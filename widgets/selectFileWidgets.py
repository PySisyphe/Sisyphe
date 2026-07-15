"""
External packages/modules
-------------------------

    - darkdetect, OS Dark Mode detection, https://github.com/albertosottile/darkdetect
    - Numpy, Scientific computing, https://numpy.org/
    - pydicom, DICOM library, https://pydicom.github.io/pydicom/stable/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Optional

from sys import platform
from sys import maxsize
from sys import float_info

from os import chdir
from os import getcwd

from os.path import isdir
from os.path import join
from os.path import dirname
from os.path import basename
from os.path import abspath
from os.path import exists
from os.path import split
from os.path import splitext

import cython

from glob import glob

from numpy import array
from numpy import save
from numpy import savetxt
from numpy import load
from numpy import loadtxt

from pydicom.datadict import tag_for_keyword
from pydicom.datadict import get_entry
from pydicom import dcmread

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

import darkdetect

from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getDatatypes
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import LineWidget
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.core.sisypheXml import XmlVolume
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import IconLabel

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from PyQt5.QtGui import QDragEnterEvent
    from PyQt5.QtGui import QDropEvent
    from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail


__all__ = ['SelectionFilter',
           'FileSelectionWidget',
           'FilesSelectionWidget',
           'FilesSelectionWithParametersWidget',
           'MultiExtFilesSelectionWidget',
           'SynchronizedFilesSelectionWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SelectionFilter, QWidget  -> FileSelectionWidget
                                          -> FilesSelectionWidget
                                          -> FilesSelectionParametersWidget
                                          -> FilesSelectionWidget -> MultiExtFilesSelectionWidget
    - QWidget ->  SynchronizedFileSelectionWidget
              ->  SynchronizedFilesSelectionWidget
"""


class SelectionFilter(object):
    """
    SelectionFilter class

    Description
    ~~~~~~~~~~~

    Base class for file selection widgets (FileSelectionWidget, FilesSelectionWidget, MultiExtFilesSelectionWidget and
    SynchronizedFilesSelectionWidget).

    This class manages the filters used to define criteria for selecting files. The criteria are as follows: directory,
    file extension(s), DICOM, Nifti, Minc, Nrrd, Vtk, numpy, PySisyphe volume (.xvol), PySisyphe ROI (.xroi),
    PySisypheMesh (.xmesh), PySisyphe streamlines (.xtracts), identity fields, ID, template, ICBM152, FOV,
    matrtix size, modality, sequence, datatype, single component, multi component, orientation, scalar range, frame,
    filename prefix, filename suffix, filename contains a string, registered to a reference file.

    Inheritance
    ~~~~~~~~~~~

    object -> SelectionFilter

    Last Revision: 13/02/2026
    """

    # Class methods

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Checks if the system is currently in dark mode.

        Returns
        -------
        bool
            True if in dark mode, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Checks if the system is currently in light mode.

        Returns
        -------
        bool
            True if in light mode, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on the current system theme (dark/light).

        Returns
        ~~~~~~~
        str
            The absolute path to the icon directory.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self) -> None:
        """
        SelectionFilter instance constructor.
        """
        super().__init__()

        self._volume = None
        self._thumbnail = None

        self._name = ''
        self._path = ''

        self._refDir = False
        self._refExt = list()
        self._refdicom = False
        self._refxvol = False
        self._refxroi = False
        self._refxmesh = False
        self._refxtracts = False
        # < Revision 13/02/2026
        self._refxtools = False
        # Revision 13/02/2026 >
        self._refID = None
        self._refSpaceID = None
        self._refRange = None
        self._refICBM = False
        self._refField = False
        self._refidentity = None
        self._refFOV = None
        self._refSize = None
        self._refmodality = None
        self._refsequence = None
        self._refdatatype = None
        self._reforientation = None
        self._refsuffix = None
        self._refprefix = None
        self._refcontains = None
        self._refframe = False
        self._refcomponent = 0
        self._reftofirst = False
        self._refwhole = False
        self._refnotwhole = False
        self._refcentroid = False
        self._refnotcentroid = False
        # < Revision 04/01/2026
        self._reftrf = None
        # Revision 04/01/2026 >

    """
    Private attributes

    _name           str, basename of file
    _path           str, abspath of file
    _volume         SisypheVolume, reference volume
    _refExt         list[str], reference extension(s)
    _refID          str, reference ID
    _refRange       tuple[float, float], reference range
    _refICBM        bool, reference ICBM
    _refdicom       bool, reference dicom file extension
    _refxvol        bool, reference xvol file extension
    _refxroi        bool, reference xroi file extension
    _refxmesh       bool, reference xmesh file extension
    _refxtracts     bool, reference xtracts file extension
    _refxtools      bool, reference xtools file extension
    _refidentity    SisypheIdentity, reference identity
    _refFOV         tuple[float, float, float], reference FOV
    _refSize        tuple[int, int, int], reference matrix size
    _refmodality    str, reference modality
    _refsequence    str, reference sequence
    _refdatatype    str, reference datatype
    _reforientation int, reference orientation
    _refsuffix      str, filename suffix reference
    _refprefix      srr, filename prefix reference
    _refcontains    str, filename contains _refcontains substring
    _refframe       bool, reference stereotactic frame
    _refcomponent   int, reference number of components
    _reftofirst     bool, reference volume is the first
    _reftrf         str, has transform
    """

    # Public method

    def getFilename(self) -> str:
        """
        Get the full absolute path of the currently selected file or directory.

        Returns
        -------
        str
            The absolute path of the selected file or directory.
        """
        if self._refDir: return self._path
        else: return join(self._path, self._name)

    def getPath(self) -> str:
        """
        Get the full absolute directory path of the currently selected file.

        Returns
        ~~~~~~~
        str
            The absolute directory path of the selected file or directory.
        """
        return self._path

    def getBasename(self) -> str:
        """
        Get the base name (filename with extension) of the currently selected file.

        Returns
        -------
        str
            The base name of the file.
        """
        return self._name

    def setReferenceVolume(self, v: SisypheVolume) -> None:
        """
        Set a SisypheVolume instance as a reference for subsequent filtering operations.

        Parameters
        ~~~~~~~~~~
        v: SisypheVolume
            SisypheVolume instance to be used as a reference.
        """
        if isinstance(v, SisypheVolume):
            self._volume = v

    def getReferenceVolume(self) -> SisypheVolume:
        """
        Get the reference SisypheVolume.

        Returns
        -------
        SisypheVolume
            Reference SisypheVolume instance, or None if not set.
        """
        return self._volume

    def setReferenceVolumeToFirst(self) -> None:
        """
        Set a flag indicating that the first selected volume should be used as a reference for subsequent filtering.
        """
        self._reftofirst = True

    def isReferenceVolumeToFirst(self) -> bool:
        """
        Checks if the flag to use the first selected volume as a reference is set.

        Returns
        -------
        bool
            True if the first selected volume is used as a reference, False otherwise.
        """
        return self._reftofirst

    def setToolbarThumbnail(self, t: ToolBarThumbnail) -> None:
        """
        Set the ToolBarThumbnail widget for accessing volumes with the IconLabel '<' widget.

        Parameters
        ----------
        t : ToolBarThumbnail)
            ToolBarThumbnail instance.
        """
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(t, ToolBarThumbnail): self._thumbnail = t
        else: raise TypeError('parameter type {} is not toolBarThumbnail.'.format(type(t)))

    def getToolbarThumbnail(self) -> ToolBarThumbnail:
        """
        Get the associated ToolBarThumbnail widget for accessing volumes with the IconLabel '<' widget.

        Returns
        -------
        ToolBarThumbnail
            Associated ToolBarThumbnail widget, or None if not set.
        """
        return self._thumbnail

    def hasToolbarThumbnail(self) -> bool:
        """
        Check if a ToolBarThumbnail widget is defined.

        Returns
        -------
        bool
            True if a ToolBarThumbnail is set, False otherwise.
        """
        return self._thumbnail is not None

    def setFiltersToDefault(self, ext: bool = True) -> None:
        """
        Resets all filters to their default state (no filter).

        Parameters
        ----------
        ext : bool (optional)
            If True, clears extension filters as well. Defaults to True.
        """
        self._refDir = False
        self._refID = None
        self._refSpaceID = None
        self._refICBM = False
        self._refField = False
        self._refdicom = False
        self._refxvol = False
        self._refxroi = False
        self._refxmesh = False
        self._refxtracts = False
        # < Revision 13/02/2026
        self._refxtools = False
        # Revision 13/02/2026 >
        self._refidentity = None
        self._refRange = None
        self._refFOV = None
        self._refSize = None
        self._refmodality = None
        self._refsequence = None
        self._refdatatype = None
        self._reforientation = None
        self._refsuffix = None
        self._refprefix = None
        self._refcontains = None
        self._refframe = False
        self._refcomponent = 0
        if ext: self._refExt = list()

    def clearExtensionFilter(self) -> None:
        """
        Clears all currently set file extension filters.
        """
        self._refExt = list()

    def getExtensionFilter(self) -> list[str]:
        """
        Get the list of currently active file extension filters.

        Returns
        -------
        list[str]
            list of file extensions (e.g., ['.nii', '.gz']).
        """
        return self._refExt

    def filterDirectory(self) -> None:
        """
        Sets the filter to allow only directory selection.
        """
        # self.setFiltersToDefault(True)
        self._refDir = True

    def filterExtensions(self, exts: list[str] | tuple[str, ...]) -> None:
        """
        Adds multiple file extensions to the filter list.

        Parameters
       -----------
        exts : list[str] | tuple[str, ...]
            list or tuple of file extensions to add.
        """
        if isinstance(exts, (list, tuple)):
            if len(exts) > 0:
                for ext in exts:
                    self.filterExtension(ext)
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(exts)))

    def filterExtension(self, ext: str) -> None:
        """
        Add a single file extension to the filter list.
        Automatically handles Sisyphe-specific file types (.xvol, .xroi, etc.).

        Parameters
        ----------
        ext : str
            file extension to add (e.g., '.nii' or 'nii').
        """
        if isinstance(ext, str):
            if ext[0] != '.': ext = '.' + ext
            if ext == SisypheVolume.getFileExt(): self._refxvol = True
            elif ext == SisypheROI.getFileExt(): self._refxroi = True
            elif ext == SisypheMesh.getFileExt(): self._refxmesh = True
            elif ext == SisypheStreamlines.getFileExt(): self._refxtracts = True
            # < Revision 13/02/2026
            elif ext in (HandleWidget.getFileExt(),
                         LineWidget.getFileExt(),
                         ToolWidgetCollection.getFileExt()): self._refxtools = True
            # Revision 13/02/2026 >
            # self.setFiltersToDefault(False)
            # < Revision 06/02/2025
            # self._refExt.append(ext)
            if ext not in self._refExt: self._refExt.append(ext)
            # Revision 06/02/2025 >
        else: raise TypeError('parameter type {} is not str.'.format(type(ext)))

    def filterDICOM(self) -> None:
        """
        Add Dicom file extensions and Sisyphe XML DICOM extension to the filter list.
        """
        # self.setFiltersToDefault(True)
        # < Revision 23/12/2024
        # self._refExt.append('.dcm')
        # self._refExt.append('.dicm')
        # self._refExt.append('.ima')
        # self._refExt.append('.nema')
        for v in getDicomExt():
            if v not in self._refExt:
                self._refExt.append(v)
        # Revision 23/12/2024 >
        # < Revision 23/12/2024
        # add XmlDicom file extension
        v = XmlDicom.getFileExt()
        if v not in self._refExt:
            self._refExt.append(v)
        # Revision 23/12/2024 >
        self._refdicom = True

    def filterSisypheVolume(self) -> None:
        """
        Add the SisypheVolume file extension (.xvol) to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheVolume.getFileExt())
        # self._refxvol = True

    def filterSisypheROI(self) -> None:
        """
        Adds the SisypheROI file extension (.xroi) to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheROI.getFileExt())
        # self._refxroi = True

    def filterSisypheMesh(self) -> None:
        """
        Add the SisypheMesh file extension (.xmesh) to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheMesh.getFileExt())
        # self._refxmesh = True

    def filterSisypheStreamlines(self) -> None:
        """
        Add the SisypheStreamlines file extension (.xtracts) to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheStreamlines.getFileExt())
        # self._refxtracts = True

    # < Revision 13/02/2026
    def filterSisypheTools(self) -> None:
        self.filterExtension(ToolWidgetCollection.getFileExt())
    # Revision 13/02/2026 >

    def filterNifti(self) -> None:
        """
        Add common Nifti file extensions to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNiftiExt())
        # self._refExt += getNiftiExt()

    def filterMinc(self) -> None:
        """
        Add common Minc file extensions to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtensions(getMincExt())
        # self._refExt += getMincExt()

    def filterNrrd(self) -> None:
        """
        Add common Nrrd file extensions to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNrrdExt())
        # self._refExt += getNrrdExt()

    def filterVtk(self) -> None:
        """
        Add common VTK file extensions to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtensions(getVtkExt())
        # self._refExt += getVtkExt()

    def filterNumpy(self) -> None:
        """
        Add common NumPy file extensions to the filter list.
        """
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNumpyExt())
        # self._refExt += getNumpyExt()

    def filterRange(self, v: SisypheVolume | SisypheDisplay | tuple[float, float] | None = None) -> None:
        """
        Set a scalar range filter for PySisyphe volumes (.xvol). Only volumes with scalar values within the specified
        range will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheDisplay | tuple[float, float] | None (optional)
            SisypheVolume, SisypheDisplay, or a tuple (min, max) defining the range. If None, clears the range filter.
        """
        if v is None: self._refRange = None
        if isinstance(v, SisypheVolume): v = v.display
        if isinstance(v, SisypheDisplay): v = v.getRange()
        if isinstance(v, tuple):
            self._refRange = (float(v[0]), float(v[1]))

    def filterMultiComponent(self) -> None:
        """
        Set the filter to allow only multi-component PySisyphe volumes (.xvol).
        """
        self._refcomponent = 2

    def filterSingleComponent(self) -> None:
        """
        Set the filter to allow only single-component PySisyphe volumes (.xvol).
        """
        self._refcomponent = 1

    def filterSameIdentity(self, v: SisypheVolume | SisypheIdentity | None = None) -> None:
        """
        Set an identity filter. Only PySisyphe volumes (.xvol) with an identity matching the provided SisypheVolume or
        SisypheIdentity will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheIdentity | None (optional)
            SisypheVolume, SisypheIdentity, or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume): v = v.getIdentity()
        if isinstance(v, SisypheIdentity): self._refidentity = v
        elif v is None: self._refidentity = ''
        else: raise TypeError('parameter type {} is not SisypheIdentity or SisypheVolume.'.format(type(v)))

    def filterSameFOV(self, v: SisypheVolume | SisypheROI | list[float] | tuple[float, float, float] | None = None) -> None:
        """
        Set a Field of View (FOV) filter. Only PySisyphe volumes (.xvol) or ROI (.xroi) with an FOV that matches the
        provided SisypheVolume, SisypheROI, or a (x, y, z) tuple will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheROI | list[float] | tuple[float, float, float] | None (optional)
            SisypheVolume, SisypheROI, a list/tuple representing FOV (x, y, z), or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, (SisypheVolume, SisypheROI)):
            self._refFOV = v.getFieldOfView(decimals=1)
        # < Revision 29/11/2024
        # tuple/list type management
        elif isinstance(v, (tuple, list)):
            if len(v) == 3: self._refFOV = tuple([round(i, 1) for i in v])
            else: raise ValueError('parameter value {} is not valid FOV.'.format(v))
        # Revision 29/11/2024 >
        elif v is None: self._refFOV = 0
        else: raise TypeError('parameter type {} is not SisypheROI, SisypheVolume, list or tuple.'.format(type(v)))

    def filterSameSize(self, v: SisypheVolume | SisypheROI | list[int] | tuple[int, int, int] | None = None) -> None:
        """
        Set a matrix size filter. Only PySisyphe volumes (.xvol) or ROI (.xroi) with dimensions matching the provided
        SisypheVolume, SisypheROI, or a (x, y, z) tuple will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheROI | list[int] | tuple[int, int, int] | None (optional)
            SisypheVolume, SisypheROI, a list/tuple representing size (x, y, z), or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, (SisypheVolume, SisypheROI)):
            self._refSize = v.getSize()
        # < Revision 29/11/2024
        # tuple/list type management
        elif isinstance(v, (tuple, list)):
            if len(v) == 3: self._refSize = tuple(v)
            else: raise ValueError('parameter value {} is not valid FOV.'.format(v))
        # Revision 29/11/2024 >
        elif v is None: self._refSize = 0
        else: raise TypeError('parameter type {} is not SisypheROI, SisypheVolume, list or tuple.'.format(type(v)))

    def filterSameModality(self, v: SisypheVolume | str | list[str] | tuple[str, ...] |None = None) -> None:
        """
        Set a modality filter. Only PySisyphe volumes (.xvol) with a modality matching the provided SisypheVolume,
        modality name (str), or list/tuple of strings will be allowed.

        Parameters
        ----------
        v : SisypheVolume | str | list[str] | tuple[str, ...] | None (optional)
            SisypheVolume, a string representing a modality code, a list/tuple of modality codes, or None to clear the
            filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getAcquisition().getModality()
        if isinstance(v, str):
            if v in SisypheAcquisition.getModalityToCodeDict():
                # < Revision 10/10/2024
                # add multi modality filter
                # self._refmodality = v
                self._refmodality = [v]
                # Revision 10/10/2024 >
            else: raise ValueError('parameter value {} is not valid modality code.'.format(v))
        # < Revision 10/10/2024
        # add multi modality filter
        elif isinstance(v, (list, tuple)):
            # < Revision 20/10/2025
            # if all([i in SisypheAcquisition.getModalityToCodeDict() for i in v]): self._refmodality = v
            if all([i in SisypheAcquisition.getModalityToCodeDict() for i in v]): self._refmodality = list(v)
            else: raise ValueError('parameter value {} are not valid modality code.'.format(v))
            # Revision 20/10/2025 >
        # Revision 10/10/2024 >
        elif v is None:
            self._refmodality = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameSequence(self, v: SisypheVolume | str | list[str] | tuple[str, ...] | None = None) -> None:
        """
        Set a sequence filter. Only PySisyphe volumes (.xvol) with a sequence matching the provided SisypheVolume,
        sequence name (str), or list/tuple of strings will be allowed.

        Parameters
        ----------
        v : SisypheVolume | str | list[str] | tuple[str, ...] | None  (optional)
            SisypheVolume, a string representing a sequence, a list/tuple of sequences, or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getAcquisition().getSequence()
        # < Revision 10/10/2024
        # add multi sequence filter
        if isinstance(v, str):
            # self._refsequence = v
            self._refsequence = [v]
        elif isinstance(v, (list, tuple)):
            # < Revision 20/10/2025
            # self._refsequence = v
            self._refsequence = list(v)
            # Revision 20/10/2025 >
        # Revision 10/10/2024 >
        elif v is None:
            self._refsequence = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameDatatype(self, v: SisypheVolume | str | None = None) -> None:
        """
        Set a datatype filter. Only PySisyphe volumes (.xvol) with a datatype matching the provided SisypheVolume or
        datatype name (str) will be allowed.

        Parameters
        ----------
        v : SisypheVolume | str | None (optional)
            SisypheVolume, a string representing a datatype, or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getDatatype()
        if isinstance(v, str):
            if v in getDatatypes():
                self._refdatatype = v
            else: raise ValueError('{} is not valid datatype.'.format(v))
        elif v is None:
            self._refdatatype = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameOrientation(self, v: SisypheVolume | str | None = None) -> None:
        """
        Set an orientation filter. Only PySisyphe volumes (.xvol) with an orientation matching the provided
        SisypheVolume or orientation name (str; 'axial', 'coronal', 'sagittal') will be allowed.

        Parameters
        ----------
        v : SisypheVolume | str | None (optional)
            SisypheVolume, a string representing an orientation, or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getOrientationAsString().lower()
        if isinstance(v, str):
            orient = ('axial', 'coronal', 'sagittal')
            if v in orient:
                self._reforientation = v
            else: raise ValueError('parameter value {} is not {}, {} or {}.'.format(v, orient[0], orient[1], orient[2]))
        elif v is None:
            self._reforientation = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSuffix(self, suffix: str) -> None:
        """
        Set a filename suffix filter. Only files whose basename ends with the specified suffix (case-insensitive) will
        be allowed.

        Parameters
        ----------
        suffix : str
            suffix string to filter by.
        """
        if isinstance(suffix, str): self._refsuffix = suffix.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(suffix)))

    def filterPrefix(self, prefix: str) -> None:
        """
        Set a filename prefix filter. Only files whose basename starts with the specified prefix (case-insensitive)
        will be allowed.

        Parameters
        ----------
        prefix : str
            prefix string to filter by.
        """
        if isinstance(prefix, str): self._refprefix = prefix.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(prefix)))

    def filterFilenameContains(self, string: str) -> None:
        """
        Set a filename substring filter. Only files whose basename contains the specified substring (case-insensitive)
        will be allowed.

        Parameters
        ----------
        string : str
            substring to filter by.
        """
        if isinstance(string, str): self._refcontains = string.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(string)))

    def filterRegisteredToReference(self, v: SisypheVolume | SisypheROI | str | None = None) -> None:
        """
        Set a filter for files coregistered to a specific reference space/transform ID. Only PySisyphe volumes (.xvol)
        or ROI (.xroi) that have a geometric transformation to the specified ID will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheROI | str | None (optional)
            SisypheVolume, SisypheROI, a string representing the reference space/transform ID, or None to clear the
            filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheROI): v = v.getReferenceID()
        elif isinstance(v, SisypheVolume): v = v.getID()
        if isinstance(v, str): self._refID = v
        elif v is None: self._refID = ''
        else: raise TypeError('parameter type {} is not str, SisypheROI or SisypheVolume.'.format(type(v)))

    def filterSameID(self, v: SisypheVolume | SisypheROI | str | None = None) -> None:
        """
        Set a filter for files with a specific space/transform ID. Only files whose ID matches the provided
        SisypheVolume, SisypheROI, or space/transform ID (str) will be allowed.

        Parameters
        ----------
        v : SisypheVolume | SisypheROI | str | None (optional)
            SisypheVolume, SisypheROI, a string representing the ID, or None to clear the filter.
        """
        if v is None: v = self._volume
        if isinstance(v, SisypheROI): v = v.getReferenceID()
        elif isinstance(v, SisypheVolume): v = v.getID()
        if isinstance(v, str): self._refSpaceID = v
        elif v is None: self._refSpaceID = ''
        else: raise TypeError('parameter type {} is not str, SisypheROI or SisypheVolume.'.format(type(v)))

    def filterFrame(self) -> None:
        """
        Set a filter to allow only PySisyphe volumes (.xvol) that have a stereotactic frame.
        """
        self._refframe = True

    def filterICBM(self) -> None:
        """
        Set a filter to allow only PySisyphe volumes (.xvol) that are in ICBM152 space.
        """
        self._refICBM = True

    def filterDisplacementField(self) -> None:
        """
        Set a filter to allow only PySisyphe volumes (.xvol) that are displacement fields (float datatype,
        3 components, and marked as displacement field sequence).
        """
        self._refField = True

    def filterWhole(self) -> None:
        """
        Set a filter to allow only PySisyphe streamlines (.xtracts) declared as whole brain tractograms.
        """
        self._refwhole = True

    def filterNotWhole(self) -> None:
        """
        Set a filter to allow only PySisyphe streamlines (.xtracts) not declared as whole brain tractograms.
        """
        self._refnotwhole = True

    def filterCentroid(self) -> None:
        """
        Set a filter to allow only PySisyphe streamlines (.xtracts) declared as centroid streamline.
        """
        self._refcentroid = True

    def filterNotCentroid(self) -> None:
        """
        Set a filter to allow only PySisyphe streamlines (.xtracts) not declared as centroid streamline.
        """
        self._refnotcentroid = True

    # < Revision 04/01/2026
    # add filterTransform method
    def filterTransform(self, v: str | SisypheVolume):
        if isinstance(v, SisypheVolume): v = v.getID()
        self._reftrf = v
    # Revision 04/01/2026 >

    def getFOVFilter(self) -> tuple[float, float, float] | float | None:
        """
        Get the current Field of View (FOV) filter value.

        Returns
        -------
        tuple[float, float, float] | float | None
            FOV filter value, or None if not set.
        """
        return self._refFOV

    def getSizeFilter(self) -> tuple[int, int, int] | int | None:
        """
        Get the current matrix size filter value.

        Returns
        ~~~~~~~
        tuple[int, int, int] | int | None
            size filter value, or None if not set.
        """
        return self._refSize

    def getModalityFilter(self) -> list[str] | str | None:
        """
        Get the current modality filter value.

        Returns
        -------
        list[str] | str | None
            modality filter value, or None if not set.
        """
        return self._refmodality

    def getSequenceFilter(self) -> list[str] | str | None:
        """
        Get the current sequence filter value.

        Returns
        -------
        list[str] | str | None
            sequence filter value, or None if not set.
        """
        return self._refsequence

    def getDatatypeFilter(self) -> str | None:
        """
        Get the current datatype filter value.

        Returns
        -------
        str | None
            datatype filter value, or None if not set.
        """
        return self._refdatatype

    def getOrientationFilter(self) -> str | None:
        """
        Get the current orientation filter value.

        Returns
        -------
        str | None
            orientation filter value, or None if not set.
        """
        return self._reforientation

    def getSuffixFilter(self) -> str | None:
        """
        Get the current filename suffix filter value.

        Returns
        -------
        str | None
            suffix filter value, or None if not set.
        """
        return self._refsuffix

    def getPrefixFilter(self) -> str | None:
        """
        Get the current filename prefix filter value.

        Returns
        -------
        str | None
            prefix filter value, or None if not set.
        """
        return self._refprefix

    def getRangeFilter(self) -> tuple[float, float] | None:
        """
        Gets the current scalar range filter values.

        Returns
        -------
        tuple[float, float] | None
            range filter values (min, max), or None if not set.
        """
        return self._refRange

    def getIDFilter(self) -> str:
        """
        Get the current ID filter value.

        Returns
        -------
        str
            ID filter value, or an empty string if not set.
        """
        return self._refSpaceID

    def getFilenameContainsFilter(self) -> str | None:
        """
        Get the current filename contains substring filter value.

        Returns
        -------
        str | None
            substring filter value, or None if not set.
        """
        return self._refcontains

    # < Revision 04/01/2026
    # add getTransformFilter method
    def getTransformFilter(self) -> str | None:
        return self._reftrf
    # Revision 04/01/2026 >

    def clearFilters(self) -> None:
        """
        Clears all active filters and resets the internal state of the filter.
        """
        self._volume = None

        self._name = ''
        self._path = ''

        self._refDir = False
        self._refExt = list()
        self._refdicom = False
        self._refxvol = False
        self._refxroi = False
        # < Revision 13/02/2026
        self._refxmesh = False
        self._refxtracts = False
        self._refxtools = False
        # Revision 13/02/2026 >
        self._refID = None
        self._refSpaceID = None
        self._refRange = None
        self._refICBM = False
        self._refField = False
        self._refidentity = None
        self._refFOV = None
        self._refSize = None
        self._refmodality = None
        self._refsequence = None
        self._refdatatype = None
        self._reforientation = None
        self._refsuffix = None
        self._refprefix = None
        self._refcontains = None
        self._refframe = False
        self._refcomponent = 0
        self._reftofirst = False
        self._refwhole = False
        self._refnotwhole = False
        self._refcentroid = False
        self._refnotcentroid = False
        # < Revision 04/01/2026
        self._reftrf = None
        # Revision 04/01/2026 >


class FileSelectionWidget(QWidget, SelectionFilter):
    """
    FileSelectionWid/get class

    Description
    ~~~~~~~~~~~

    Widget that manages single file selection.

    This widget consists of the following elements, which are displayed from left to right.

    - QLabel widget, descriptive text label
    - QLineEdit widget, selected file name
    - IconLabel widget with '<' icon, to select a PySisypheVolume from the thumbnail bar (optional widget)
    - IconLabel widget with folder icon, to select a file from a dialog
    - IconLabel widget with 'X' icon, to clear the selected file name

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FileSelectionWidget

    Last revision: 09/07/2026
    """

    # Custom Qt Signal

    FieldChanged: pyqtSignal = pyqtSignal(QWidget, str)
    FieldCleared: pyqtSignal = pyqtSignal(QWidget)

    # Special method

    def __init__(self, parent: QWidget | None = None)  -> None:
        """
        FileSelectionWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget.
        """
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self.setAcceptDrops(True)

        # Init QLayout

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)
        # < Revision 12/12/2024
        # select only single-component volumes
        self.filterSingleComponent()
        # < Revision 12/12/2024

        # Init QWidgets

        self._label = QLabel()
        self._label.setVisible(False)
        self._label.setContentsMargins(0, 0, 5, 0)
        self._field = QLineEdit()
        self._field.setReadOnly(True)
        # < Revision 04/04/2025
        # replace QPushButton by IconLabel
        # self._current = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'left.png')), '')
        # self._open = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'open.png')), '')
        # self._clear = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'cross.png')), '')
        self._current = IconLabel(join(self.getDefaultIconDirectory(), 'left.png'))
        self._open = IconLabel(join(self.getDefaultIconDirectory(), 'open.png'))
        self._clear = IconLabel(join(self.getDefaultIconDirectory(), 'cross.png'))
        # Revision 04/04/2025 >

        # < Revision 09/07/2026
        # if platform == 'win32':
        if platform == 'win32' or platform == 'linux':
            self._current.setFixedSize(QSize(32, 32))
            self._open.setFixedSize(QSize(32, 32))
            self._clear.setFixedSize(QSize(32, 32))
        # Revision 09/07/2026 >
        elif platform == 'darwin':
            self._current.setFixedSize(QSize(24, 24))
            self._open.setFixedSize(QSize(24, 24))
            self._clear.setFixedSize(QSize(24, 24))
        self._current.setToolTip('Add thumbnail volume to the field.')
        self._open.setToolTip('Add file to the field.')
        self._clear.setToolTip('Clear field.')

        self._menuThumbnail = QMenu(self._current)
        # noinspection PyUnresolvedReferences
        self._menuThumbnail.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._menuThumbnail.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._menuThumbnail.setAttribute(Qt.WA_TranslucentBackground, True)
        # noinspection PyUnresolvedReferences
        self._menuThumbnail.triggered.connect(self._onMenuThumbnailSelect)

        # noinspection PyUnresolvedReferences
        self._current.clicked.connect(self._onMenuThumbnailShow)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._field)
        self._layout.addWidget(self._current)
        self._layout.addWidget(self._open)
        self._layout.addWidget(self._clear)

        self._current.setVisible(False)

        # noinspection PyUnresolvedReferences
        self._open.clicked.connect(lambda: self.open())
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(lambda: self.clear())

    """
    Private attributes

    _label          QLabel
    _field          QLineEdit
    _current        QPushbutton
    _open           QPushbutton
    _clear          QPushbutton
    """

    # Private methods

    def _onMenuThumbnailShow(self):
        """
        Displays the context menu for selecting volumes from the thumbnail toolbar.
        If only one volume is available, it is directly opened. If multiple, a popup menu is shown.
        """
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.open(v.getFilename())
            elif n > 1:
                self._menuThumbnail.clear()
                i: cython.int
                for i in range(n):
                    v = self._thumbnail.getVolumeFromIndex(i)
                    action = self._menuThumbnail.addAction(v.getBasename())
                    action.setData(v.getFilename())
                # < Revision 27/10/2024
                # use popup instead of exec
                # menu.exec(self._current.mapToGlobal(QPoint(0, self._current.height())))
                self._menuThumbnail.popup(self._current.mapToGlobal(QPoint(0, self._current.height())))
                # Revision 27/10/2024 >

    def _onMenuThumbnailSelect(self, action):
        """
        Handles the selection of a volume from the thumbnail menu.

        Parameters
        ----------
        action : QAction
            QAction that was triggered, containing the filename.
        """
        self.open(str(action.data()))

    # Public methods

    def setToolbarThumbnail(self, t: ToolBarThumbnail) -> None:
        """
        Set the ToolBarThumbnail widget for accessing volumes and makes the current volume '<' button visible if a
        thumbnail toolbar is provided.

        Parameters
        ----------
        t : ToolBarThumbnail
            ToolBarThumbnail instance.
        """
        super().setToolbarThumbnail(t)
        self._current.setVisible(True)

    def setCurrentVolumeButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the button that allows adding the current thumbnail volume to the field.

        Parameters
        ----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool):
            v = v and self.hasToolbarThumbnail()
            self._current.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def getCurrentVolumeButtonVisibility(self) -> bool:
        """
        Get the visibility state of the current volume '<' button.

        Returns
        -------
        bool
            True if the button is visible, False otherwise.
        """
        return self._current.isVisible()

    def setClearButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the clear button.

        Parameters
        ----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def getClearButtonVisibility(self) -> bool:
        """
        Get the visibility state of the clear button.

        Returns
        -------
        bool
            True if the button is visible, False otherwise.
        """
        return self._clear.isVisible()

    def setLabelVisibility(self, v: bool) -> None:
        """
        Set the visibility of the descriptive label.

        Parameters
        ----------
        v : bool
            True to show the label, False to hide it.
        """
        if isinstance(v, bool): self._label.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showLabel(self) -> None:
        """
        Show the descriptive label.
        """
        self._label.setVisible(True)

    def hideLabel(self) -> None:
        """
        Hide the descriptive label.
        """
        self._label.setVisible(False)

    def getLabelVisibility(self) -> bool:
        """
        Get the visibility state of the descriptive label.

        Returns
        -------
        bool
            True if the label is visible, False otherwise.
        """
        return self._label.isVisible()

    def setTextLabel(self, txt: str) -> None:
        """
        Set the text of the descriptive label and makes it visible.

        Parameters
        ----------
        txt : str
            text to set for the label.
        """
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(True)
        else:
            raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getTextLabel(self) -> str:
        """
        Get the current text of the descriptive label.

        Returns
        -------
        str
            text of the label.
        """
        return self._label.text()

    def getLabel(self) -> QLabel:
        """
        Get the QLabel widget used as the descriptive label.

        Returns
        -------
        QLabel
            QLabel instance.
        """
        return self._label

    def alignLabels(self, w: QWidget) -> None:
        """
        Align the labels of this widget and another FileSelectionWidget to ensure consistent width and right alignment.

        Parameters
       -----------
        w : QWidget
            another FileSelectionWidget instance to align with.
        """
        if isinstance(w, FileSelectionWidget):
            fm = QFontMetrics(self._label.font())
            w1 = fm.horizontalAdvance(self._label.text())
            # noinspection PyProtectedMember
            w2 = fm.horizontalAdvance(w._label.text())
            w1 = max(w1, w2)
            # noinspection PyUnresolvedReferences
            self._label.setAlignment(Qt.AlignRight)
            # noinspection PyUnresolvedReferences
            w.getLabel().setAlignment(Qt.AlignRight)
            self._label.setFixedWidth(w1 + 20)
            w.getLabel().setFixedWidth(w1 + 20)
        else: raise TypeError('Parameter type {} is not FileSelectionWidget.'.format(type(w)))

    def setButtonsVisibility(self, v: bool) -> None:
        """
        Sets the visibility of all control buttons (open, clear, current volume).

        Parameters
        ----------
        v : bool
            True to show buttons, False to hide them.
        """
        if isinstance(v, bool):
            self._open.setVisible(v)
            self._clear.setVisible(v)
            self.setCurrentVolumeButtonVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showButtons(self) -> None:
        """
        Show all control buttons (open, clear, current volume).
        """
        self.setButtonsVisibility(True)

    def hideButtons(self) -> None:
        """
        Hide all control buttons (open, clear, current volume).
        """
        self.setButtonsVisibility(False)

    def getButtonsVisibility(self) -> bool:
        """
        Get the visibility state of control buttons.

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._open.isVisible()

    # < Revision 23/12/2024
    # add setFieldVisibility method
    def setFieldVisibility(self, v: bool) -> None:
        """
        Set the visibility of the QLineEdit field where the selected filename is displayed.

        Parameters
        ----------
        v : bool
            True to show the field, False to hide it.
        """
        if isinstance(v, bool):
            self._field.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add showField method
    def showField(self) -> None:
        """
        Show the QLineEdit field where the selected filename is displayed.
        """
        self.setFieldVisibility(True)
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add hideField method
    def hideField(self) -> None:
        """
        Hide the QLineEdit field where the selected filename is displayed.
        """
        self.setFieldVisibility(False)
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add getFieldVisibility method
    def getFieldVisibility(self) -> bool:
        """
        Get the visibility state of the QLineEdit field where the selected filename is displayed.

        Returns
        -------
        bool
            True if the field is visible, False otherwise.
        """
        return self._field.isVisible()
    # Revision 23/12/2024 >

    def setRemoveButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the remove button (alias for clear button).

        Parameters
       -----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveButton(self) -> None:
        """
        Show the remove button (alias for clear button).
        """
        self._clear.setVisible(True)

    def hideRemoveButton(self) -> None:
        """
        Hide the remove button (alias for clear button).
        """
        self._clear.setVisible(False)

    def getRemoveButtonVisibility(self) -> bool:
        """
        Get the visibility state of the remove button (alias for clear button).

        Returns
        -------
        bool
            True if the field is visible, False otherwise.
        """
        return self._clear.isVisible()

    def filterSisypheVolume(self) -> None:
        """
        Set the filter to allow only PySisyphe volume files (.xvol) and updates the visibility of the 'current volume'
        button based on the presence of a thumbnail toolbar.
        """
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def clear(self, signal: bool = True) -> None:
        """
        Clear the selected file from the QLineEdit field and resets internal state.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits FieldChanged and FieldCleared signals. Defaults to True.
        """
        self._field.setText('')
        self._field.setToolTip('')
        self._name = ''
        self._path = ''
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldChanged.emit(self, '')
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self)

    # noinspection PyInconsistentReturns
    def open(self, filename: str = '', signal: bool = True) -> None:
        """
        Open a file dialog to select a file or directory, applying configured filters. If a filename is provided, it
        attempts to open that file directly. Performs various checks (component, identity, FOV, size, modality, etc.)
        based on active filters before accepting the file.

        Parameters
        ~~~~~~~~~~
        filename : str (optional)
            pre-selected filename to open directly. Defaults to an empty string.
        signal : bool (optional)
            If True, emits FieldChanged signal upon successful selection. Defaults to True.
        """
        # < Revision 30/11/2025
        if self._path != '' and exists(self._path): folder = self._path
        else: folder = getcwd()
        # Revision 30/11/2025 >
        # Extract filepath, filename and ext of parameter if exists
        param = filename != '' and exists(filename)
        if param: paramext = splitext(filename)[1].lower()
        else: paramext = ''
        # Apply filters
        if self._refDir:
            if param:
                if isdir(filename): directory = filename
                else: directory = dirname(filename)
            else:
                # < Revision 30/11/2025
                # directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                #                                             getcwd(), QFileDialog.ShowDirsOnly)
                directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                             folder, QFileDialog.ShowDirsOnly)
                # Revision 30/11/2025 >
                QApplication.processEvents()
                self.activateWindow()
            if directory:
                directory = abspath(directory)
                chdir(directory)
                self._name = ''
                self._path = directory
                self._field.setText(directory)
                self._field.setToolTip(directory)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.FieldChanged.emit(self, directory)
        elif len(self._refExt) > 0:
            # SisypheVolume
            if self._refxvol:
                if not param or paramext != SisypheVolume.getFileExt():
                    filt = 'PySisyphe Volume (*.xvol)'
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe volume', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe volume', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    img = SisypheVolume()
                    # < Revision 17/11/2024
                    # load only XML part (attributes)
                    # fast volume loading
                    # try: img.load(filename)
                    try: img.load(filename, binary=False)
                    # Revision 17/11/2024 >
                    except:
                        messageBox(self,
                                   'PySisyphe volume file selector',
                                   text='{} is not a valid Sisyphe volume file.'.format(basename(filename)))
                        return None
                    # Component verification
                    if self._refcomponent == 1:
                        c = img.getNumberOfComponentsPerPixel()
                        if c > 1:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is a multi component image.'.format(basename(filename)))
                            return None
                    elif self._refcomponent > 1:
                        c = img.getNumberOfComponentsPerPixel()
                        if c == 1:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is a single component image.'.format(basename(filename)))
                            return None
                    # Identity verification
                    if self._refidentity:
                        if img.getIdentity().isNotEqual(self._refidentity):
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image identity is not allowed.'.format(basename(filename)))
                            return None
                    # FOV verification
                    if self._refFOV:
                        # < Revision 19/09/2024
                        # if img.getFieldOfView() != self._refFOV:
                        # Revision 19/09/2024 >
                        if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                            txt = '{0} image field of view {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                  'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text=txt.format(basename(filename), img.getFieldOfView(), self._refFOV))
                            return None
                    # Size verification
                    if self._refSize:
                        if img.getSize() != self._refSize:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image size {} does not match reference {}.'.format(
                                           basename(filename),
                                           img.getSize(),
                                           self._refSize))
                            return None
                    # ICBM verification
                    if self._refICBM:
                        if not img.acquisition.isICBM152():
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image is not in ICBM space.'.format(basename(filename)))
                            return None
                    # Displacement field verification
                    if self._refField:
                        if not (img.isFloatDatatype() and
                                img.getNumberOfComponentsPerPixel() == 3
                                and img.getAcquisition().isDisplacementField()):
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image is not displacement field.'.format(basename(filename)))
                            return None
                    # Modality verification
                    if self._refmodality:
                        # < Revision 10/10/2024
                        # multiple modality management
                        # self._refmodality is list and not str as before
                        # if img.getAcquisition().getModality() != self._refmodality:
                        # Revision 10/10/2024 >
                        if img.getAcquisition().getModality() not in self._refmodality:
                            # < Revision 17/11/2024
                            # modality list to str conversion
                            if len(self._refmodality) == 1: refmodality = self._refmodality[0]
                            else: refmodality = ', '.join(str(m) for m in self._refmodality)
                            # Revision 17/11/2024 >
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} modality {} is not allowed ({} required).'.format(
                                           basename(filename),
                                           img.getAcquisition().getModality(),
                                           refmodality))
                            return None
                    # Sequence verification
                    if self._refsequence:
                        # < Revision 10/10/2024
                        # multiple sequence management
                        # self._refsequence is list and not str as before
                        # if img.getAcquisition().getSequence() != self._refsequence:
                        # Revision 10/10/2024 >
                        if img.getAcquisition().getSequence() not in self._refsequence:
                            # < Revision 17/11/2024
                            # sequence list to str conversion
                            if len(self._refsequence) == 1: refsequence = self._refsequence[0]
                            else: refsequence = ', '.join(str(s) for s in self._refsequence)
                            # Revision 17/11/2024 >
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} sequence {} is not allowed ({} required).'.format(
                                           basename(filename),
                                           img.getAcquisition().getSequence(),
                                           refsequence))
                            return None
                    # Datatype verification
                    if self._refdatatype:
                        if img.getDatatype() != self._refdatatype:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image datatype {} is not allowed ({} required).'.format(
                                           basename(filename),
                                           img.getDatatype(),
                                           self._refdatatype))
                            return None
                    # Orientation verification
                    if self._reforientation:
                        if img.getOrientationAsString().lower() != self._reforientation:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image orientation {} is not allowed ({} required).'.format(
                                           basename(filename),
                                           img.getOrientationAsString(),
                                           self._reforientation))
                            return None
                    # Same ID verification
                    if self._refSpaceID:
                        if img.getID() != self._refSpaceID:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image ID is not allowed.'.format(basename(filename)))
                            return None
                    # Registered verification
                    if self._refID:
                        if img.getID() != self._refID:
                            if self._refID not in img.getTransforms():
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image not registered to reference.'.format(basename(filename)))
                                return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                 self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    # Frame verification
                    if self._refframe:
                        if not img.getAcquisition().getFrame():
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image has no frame.'.format(basename(filename)))
                            return None
                    # Range verification
                    if self._refRange:
                        r = img.display.getRange()
                        if r[0] < self._refRange[0] or r[1] > self._refRange[1]:
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} image range is not between {} and {} .'.format(
                                           basename(filename),
                                           self._refRange[0],
                                           self._refRange[1]))
                            return None
                    # Transform verification
                    # < Revision 04/01/2026
                    if self._reftrf:
                        if not img.hasTransform(self._reftrf):
                            if self._reftrf == 'LEKSELL':
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image has no geometric transformation to the '
                                                'Leksell\'s stereotactic space.'.format(basename(filename)))
                            else:
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image has no transform to {}.'.format(
                                               basename(filename), self._reftrf))
                            return None
                    # Revision 04/01/2026 >
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(img))
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
            # SisypheROI
            elif self._refxroi:
                if not param or paramext != SisypheROI.getFileExt():
                    filt = 'PySisyphe ROI (*.xroi)'
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select Sisyphe ROI', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select Sisyphe ROI', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    img = SisypheROI()
                    try: img.load(filename)
                    except:
                        messageBox(self,
                                   'File selector',
                                   text='{} is not a valid Sisyphe ROI file.'.format(basename(filename)))
                        return None
                    # Size verification
                    if self._refSize:
                        if img.getSize() != self._refSize:
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} ROI size {} does not match reference {}.'.format(
                                           basename(filename),
                                           img.getSize(),
                                           self._refSize))
                            return None
                    # FOV verification
                    if self._refFOV:
                        # < Revision 19/09/2024
                        # if img.getFieldOfView() != self._refFOV:
                        # Revision 19/09/2024 >
                        if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} ROI FOV {} does not match reference {}.'.format(
                                           basename(filename),
                                           img.getFieldOfView(),
                                           self._refFOV))
                            return None
                    # Registered verification
                    if self._refID:
                        if img.getReferenceID() != self._refID:
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} ROI is not registered to reference.'.format(basename(filename)))
                            return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                 self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(img))
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
            # SisypheMesh
            elif self._refxmesh:
                if not param or paramext != SisypheMesh.getFileExt():
                    filt = SisypheMesh.getFilterExt()
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    mesh = SisypheMesh()
                    try: mesh.load(filename)
                    except:
                        messageBox(self,
                                   'PySisyphe mesh file selector',
                                   text='{} is not a valid Sisyphe mesh file.'.format(basename(filename)))
                        return None
                    # ID verification
                    if self._refSpaceID:
                        if mesh.getReferenceID() != self._refSpaceID:
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} mesh ID is not allowed.'.format(basename(filename)))
                            return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                 self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(mesh))
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
            # SisypheStreamlines
            elif self._refxtracts:
                if not param or paramext != SisypheStreamlines.getFileExt():
                    filt = SisypheStreamlines.getFilterExt()
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    sl = SisypheStreamlines()
                    try: sl.load(filename)
                    except:
                        messageBox(self,
                                   'PySisyphe streamlines file selector',
                                   text='{} is not a valid Sisyphe streamlines file.'.format(basename(filename)))
                        return None
                    # ID verification
                    if self._refSpaceID:
                        if sl.getReferenceID() != self._refSpaceID:
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} streamlines ID is not allowed.'.format(basename(filename)))
                            return None
                    # FOV verification
                    if self._refFOV:
                        # < Revision 19/09/2024
                        # if img.getFieldOfView() != self._refFOV:
                        # Revision 19/09/2024 >
                        if not sl.getDWIFOV(decimals=1) != self._refFOV:
                            txt = '{0} streamlines field of view {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                  'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text=txt.format(basename(filename), sl.getDWIFOV, self._refFOV))
                            return None
                    # Size verification
                    if self._refSize:
                        if sl.getDWIShape() != self._refSize:
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} size {} does not match reference {}.'.format(
                                           basename(filename),
                                           sl.getDWIShape(),
                                           self._refSize))
                            return None
                    # Whole brain tractogram verification
                    if self._refwhole:
                        if not sl.isWholeBrainTractogram():
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is not a whole brain tractogram.'.format(basename(filename)))
                            return None
                    # Not whole brain tractogram verification
                    if self._refnotwhole:
                        if sl.isWholeBrainTractogram():
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is a whole brain tractogram.'.format(basename(filename)))
                            return None
                    # Centroid verification
                    if self._refcentroid:
                        if not sl.isCentroid():
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is not a centroid streamline.'.format(basename(filename)))
                            return None
                    # Not centroid vérification
                    if self._refnotcentroid:
                        if sl.isCentroid():
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is a centroid streamline.'.format(basename(filename)))
                            return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                 self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(sl))
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
            # Tools, HandleWidget, LineWidget, ToolCollectionWidget
            # < Revision 13/02/2026
            elif self._refxtools:
                if not param or paramext not in (HandleWidget.getFileExt(),
                                                 LineWidget.getFileExt(),
                                                 ToolWidgetCollection.getFileExt()):
                    # < Revision 24/02/2026
                    filt = ';;'.join([ToolWidgetCollection.getFilterExt(),
                                      HandleWidget.getFilterExt(),
                                      LineWidget.getFilterExt()])
                    # Revision 24/02/2026 >
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe tools', folder, filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    ext = splitext(filename)[1]
                    try:
                        if ext == HandleWidget.getFileExt():
                            tool = HandleWidget('')
                            tool.load(filename)
                        elif ext == LineWidget.getFileExt():
                            tool = LineWidget('')
                            tool.load(filename)
                        elif ext == ToolWidgetCollection.getFileExt():
                            tool = ToolWidgetCollection()
                            tool.load(filename)
                        else: return None
                    except:
                        messageBox(self,
                                   'PySisyphe tools file selector',
                                   text='{} is not a valid Sisyphe tools file.'.format(basename(filename)))
                        return None
                    # ID verification
                    if self._refSpaceID:
                        if isinstance(tool, ToolWidgetCollection):
                            if tool.getReferenceID() != self._refSpaceID:
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} tools ID is not allowed.'.format(basename(filename)))
                                return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                 self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(tool))
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
            # Revision 13/02/2026 >
            # DICOM
            elif self._refdicom:
                # < Revision 13/02/2026
                # if not param or paramext not in getDicomExt().append(''):
                if not param or paramext not in getDicomExt():
                # Revision 13/02/2026 >
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select DICOM file', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select DICOM file', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    if isDicom(filename):
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                return None
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                return None
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                return None
                        self._path, self._name = split(filename)
                        self._field.setText(self._name)
                        if signal:
                            # noinspection PyUnresolvedReferences
                            self.FieldChanged.emit(self, filename)
                    else:
                        messageBox(self, 'File selector', text='{} is not a valid dicom file.'.format(self._name))
            # Other file
            else:
                if not param or paramext not in self._refExt:
                    filt = 'Files ('
                    for ext in self._refExt:
                        filt += '*{} '.format(ext)
                    filt = filt.rstrip() + ')'
                    # < Revision 30/11/2025
                    # filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
                    filename = QFileDialog.getOpenFileName(self, 'Select file', folder, filt)
                    # Revision 30/11/2025 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            messageBox(self,
                                       'File selector',
                                       text='{} does not have {} prefix.'.format(basename(filename),
                                                                                 self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            messageBox(self,
                                       'File selector',
                                       text='{} does not have {} suffix.'.format(basename(filename),
                                                                                self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            messageBox(self,
                                       'File selector',
                                       text='{} does not contains {} string.'.format(basename(filename),
                                                                                     self._refcontains))
                            return None
                    chdir(dirname(filename))
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    if signal:
                        # noinspection PyUnresolvedReferences
                        self.FieldChanged.emit(self, filename)
        else:
            if not param:
                filt = 'All files (*.*)'
                # < Revision 30/11/2025
                # filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
                filename = QFileDialog.getOpenFileName(self, 'Select file', folder, filt)
                # Revision 30/11/2025 >
                QApplication.processEvents()
                self.activateWindow()
                filename = filename[0]
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                # Prefix verification
                if self._refprefix:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if not bname[:len(self._refprefix)] == self._refprefix:
                        messageBox(self,
                                   'File selector',
                                   text='{} does not have {} prefix.'.format(basename(filename),
                                                                             self._refprefix))
                        return None
                # Suffix verification
                if self._refsuffix:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if not bname[-len(self._refsuffix):] == self._refsuffix:
                        messageBox(self,
                                   'File selector',
                                   text='{} does not have {} suffix.'.format(basename(filename),
                                                                             self._refsuffix))
                        return None
                # Filename contains verification
                if self._refcontains:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if bname.find(self._refcontains) > -1:
                        messageBox(self,
                                   'File selector',
                                   text='{} does not contains {} string.'.format(basename(filename),
                                                                                 self._refcontains))
                        return None
                chdir(dirname(filename))
                self._path, self._name = split(filename)
                self._field.setText(self._name)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.FieldChanged.emit(self, filename)

    def isEmpty(self) -> bool:
        """
        Checks if the file selection field is empty.

        Returns
        -------
        bool
            True if no file is selected, False otherwise.
        """
        return self._path == ''

    def getVolume(self) -> SisypheVolume:
        """
        Load the selected file as a SisypheVolume. This method is intended for use when a SisypheVolume is expected.

        Returns
        -------
        SisypheVolume
            loaded SisypheVolume object.
        """
        if not self.isEmpty():
            v = SisypheVolume()
            v.load(self.getFilename())
            return v
        else: raise AttributeError('No volume.')

    # Qt Drop events

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
        """
        Handles drag enter events, accepting drops if the mime data contains text (e.g., file paths).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event : QDragEnterEvent
            Qt drag enter event.
        """
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """
        Handles drop events, attempting to open the dropped file(s).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event ! QDropEvent
            Qt drop event.
        """
        if event.mimeData().hasText():
            event.accept()
            self.open(event.mimeData().text()[7:])


class FilesSelectionWidget(QWidget, SelectionFilter):
    """
    FilesSelectionWidget class

    Description
    ~~~~~~~~~~~

    Widget that manages files selection.

    This widget consists of the following elements, which are displayed from left to right.

    - QLabel widget, descriptive text label
    - QListWidget widget, displays a list of selected files
    - IconLabel widget with '<' icon, to add a PySisypheVolume from the thumbnail bar (optional widget)
    - QPushButton 'add', to add a file from a dialog
    - QPushButton 'remove', to remove the selected file(s) from the list
    - QPushButton 'remove all', to remove all the files from the list

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FilesSelectionWidget

    Last revision: 26/03/2026
    """

    # Custom Qt Signals

    FieldChanged: pyqtSignal = pyqtSignal(QWidget, str)
    FieldCleared: pyqtSignal = pyqtSignal(QWidget, list)
    FilesSelectionChanged: pyqtSignal = pyqtSignal(QWidget)
    FilesSelectionWidgetSelectionChanged: pyqtSignal = pyqtSignal(QWidget, str)
    FilesSelectionWidgetCleared: pyqtSignal = pyqtSignal(QWidget)
    FilesSelectionWidgetDoubleClicked: pyqtSignal = pyqtSignal(QListWidgetItem)

    # Special method

    def __init__(self, maxcount: int = 100, checkbox: bool = False, parent: QWidget | None = None)  -> None:
        """
        FilesSelectionWidget instance constructor.

        Parameters
        ----------
        maxcount : int
            maximum number of files allowed in the list.
        checkbox : bool
            display or not a QCheckbox widget before each file name in the list.
        parent : QWidget | None (optional)
            parent widget.
        """
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self._refCount = maxcount
        self._countWarning = True
        self._checkbox = checkbox
        self._stop = False
        self.setAcceptDrops(True)
        # < Revision 12/12/2024
        # select only single-component volumes
        self.filterSingleComponent()
        # < Revision 12/12/2024

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._label = QLabel()
        self._label.setVisible(False)
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        # noinspection PyUnresolvedReferences
        self._list.itemSelectionChanged.connect(self._selectionChanged)
        # noinspection PyTypeChecker
        self._list.setSelectionMode(3)  # Extended selection
        # noinspection PyUnresolvedReferences
        self._list.itemDoubleClicked.connect(self._onDoubleClicked)
        self._current = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'left.png')), '')
        self._add = QPushButton('Add')
        self._clear = QPushButton('Remove')
        self._clearall = QPushButton('Remove all')
        # self._current.setFixedSize(QSize(50, 32))
        self._current.setToolTip('Add thumbnail volume to the list.')
        self._add.setToolTip('Add file(s) to the list.')
        self._clear.setToolTip('Remove selected file(s) from the list.')
        self._clearall.setToolTip('Remove all files from the list.')

        # noinspection PyUnresolvedReferences
        self._current.clicked.connect(self._onMenuThumbnailShow)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._list)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._current)
        layout.addWidget(self._add)
        layout.addWidget(self._clear)
        layout.addWidget(self._clearall)
        layout.addStretch()
        self._layout.addLayout(layout)

        self._current.setVisible(False)

        # noinspection PyUnresolvedReferences
        self._add.clicked.connect(lambda: self.add())
        # < Revision 19/06/2025
        # self._clear.clicked.connect(self.clear)
        # self._clearall.clicked.connect(self.clearall)
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(lambda: self.clear())
        # noinspection PyUnresolvedReferences
        self._clearall.clicked.connect(lambda: self.clearall())
        # Revision 19/06/2025 >

    """
    Private attributes

    _label          QLabel
    _list           QListWidget
    _current        QPushButton
    _add            QPushButton
    _clear          QPushButton
    _clearall       QPushButton
    _stop           bool, break files check after failure
    _refCount       int, maximum number of files
    _countWarning   bool, display or not warning when the maximum number of files is reached
    """

    # Private method

    def _selectionChanged(self):
        """
        Slot connected to the itemSelectionChanged signal of the QListWidget.
        Emits FilesSelectionWidgetSelectionChanged signal with the filename of the first selected item.
        """
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetSelectionChanged.emit(self, selecteditems[0].data(256))

    def _onMenuThumbnailShow(self):
        """
        Displays the context menu for selecting PySisyphe (.xvol) volumes from the thumbnail toolbar.
        If only one volume is available, it's directly added. If multiple, a popup menu is shown.
        Includes an 'All' option for adding all volumes from the toolbar.
        """
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.add(v.getFilename())
            if n > 1:
                menu = QMenu(self._current)
                # noinspection PyUnresolvedReferences
                menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                menu.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                menu.setAttribute(Qt.WA_TranslucentBackground, True)
                i: cython.int
                for i in range(n):
                    v = self._thumbnail.getVolumeFromIndex(i)
                    action = menu.addAction(v.getBasename())
                    action.setData(v.getFilename())
                # < Revision 08/11/2024
                if n > 1:
                    menu.addSeparator()
                    menu.addAction('All')
                # Revision 08/11/2024 >
                # noinspection PyUnresolvedReferences
                menu.triggered.connect(self._onMenuThumbnailSelect)
                menu.exec(self._current.mapToGlobal(QPoint(0, self._current.height())))

    def _onMenuThumbnailSelect(self, action):
        """
        Handles the selection of a PySisyphe volume (.xvol) from the thumbnail menu.
        If 'All' is selected, it adds all PySisyphe volumes (.xvol) from the thumbnail toolbar.

        Parameters
        ----------
        action : QAction
            QAction that was triggered, containing the filename or 'All'.
        """
        # < Revision 08/11/2024
        if action.text() == 'All':
            n = self._thumbnail.getWidgetsCount()
            wait = DialogWait(progress=True, progressmin=0, progressmax=n, cancel=True)
            wait.open()
            i: cython.int
            for i in range(n):
                filename = self._thumbnail.getVolumeFromIndex(i).getFilename()
                wait.incCurrentProgressValue()
                wait.setInformationText('Add {}...'.format(basename(filename)))
                self.add(filename)
                if wait.getStopped(): break
            wait.close()
        # Revision 08/11/2024 >
        else: self.add(str(action.data()))

    def _onDoubleClicked(self, item):
        """
        Slot connected to the itemDoubleClicked signal of the QListWidget.
        Emits FilesSelectionWidgetDoubleClicked signal with the double-clicked item.

        Parameters
        ----------
        item : QListWidgetItem
            QListWidgetItem that was double-clicked.
        """
        if item is not None:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetDoubleClicked.emit(item)

    # Public methods

    def fileCountWarningOn(self):
        self._countWarning = True

    def fileCountWarningOff(self):
        self._countWarning = False

    def setFileCountWarning(self, v: bool = True):
        self._countWarning = v

    def getFileCountWaring(self) -> bool:
        return self._countWarning

    def setStopCheckAfterFailure(self, stop: bool) -> None:
        """
        Set whether the file checking process should stop after the first file fails a filter check during an 'add' operation.

        Parameters
        ----------
        stop : bool
            True to stop on first failure, False to continue checking other files.
        """
        if isinstance(stop, bool): self._stop = stop
        else: raise TypeError('parameter type {} is not bool.'.format(type(stop)))

    def getStopCheckAfterFailure(self) -> bool:
        """
        Get the current setting for stopping file checks after a failure.

        Returns
        -------
        bool
            True if checks stop on first failure, False otherwise.
        """
        return self._stop

    def setMaximumNumberOfFiles(self, n: int)  -> None:
        """
        Set the maximum number of files allowed in the list.

        Parameters
        ----------
        n : int
            maximum number of files.
        """
        if isinstance(n, int): self._refCount = n
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def getMaximumNumberOfFiles(self) -> int:
        """
        Get the maximum number of files allowed in the list.

        Returns
        -------
        int
            maximum number of files.
        """
        return self._refCount

    def setToolbarThumbnail(self, t: ToolBarThumbnail) -> None:
        """
        Set the ToolBarThumbnail widget for accessing volumes and makes the 'current volume' button visible if a
        thumbnail toolbar is provided.

        Parameters
        ----------
        t : ToolBarThumbnail
            ToolBarThumbnail instance.
        """
        super().setToolbarThumbnail(t)
        self._current.setVisible(True)

    def setCurrentVolumeButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the button that allows adding the current thumbnail volume to the list.

        Parameters
        ----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool):
            v = v and self.hasToolbarThumbnail()
            self._current.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showCurrentVolumeButton(self) -> None:
        """
        Show the 'current volume' button.
        """
        self.setCurrentVolumeButtonVisibility(True)

    def hideCurrentVolumeButton(self) -> None:
        """
        Hide the 'current volume' button.
        """
        self.setCurrentVolumeButtonVisibility(False)

    def getCurrentVolumeButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'current volume' button.

        Returns
        -------
        bool
            True if the button is visible, False otherwise.
        """
        return self._current.isVisible()

    def setLabelVisibility(self, v: bool) -> None:
        """
        Set the visibility of the descriptive label for the widget.

        Parameters
        ----------
        v : bool
            True to show the label, False to hide it.
        """
        if isinstance(v, bool): self._label.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showLabel(self) -> None:
        """
        Show the descriptive label.
        """
        self._label.setVisible(True)

    def hideLabel(self) -> None:
        """
        Hide the descriptive label.
        """
        self._label.setVisible(False)

    def getLabelVisibility(self) -> bool:
        """
        Get the visibility state of the descriptive label.

        Returns
        -------
        bool
            True if the label is visible, False otherwise.
        """
        return self._label.isVisible()

    def setTextLabel(self, txt: str) -> None:
        """
        Set the text of the descriptive label and makes it visible.

        Parameters
        ----------
        txt : str
            text to set for the label.
        """
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(True)
        else: raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getTextLabel(self) -> str:
        """
        Get the current text of the descriptive label.

        Returns
        -------
        str
            text of the label.
        """
        return self._label.text()

    def getLabel(self) -> QLabel:
        """
        Get the QLabel widget used as the descriptive label.

        Returns
        -------
        QLabel
            QLabel instance.
        """
        return self._label

    def setButtonsVisibility(self, v: bool) -> None:
        """
        Set the visibility of all control buttons (add, remove, remove all, current volume).

        Parameters
        ----------
        v : bool
            True to show buttons, False to hide them.
        """
        if isinstance(v, bool):
            self._add.setVisible(v)
            self._clear.setVisible(v)
            self._clearall.setVisible(v)
            self.setCurrentVolumeButtonVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showButtons(self) -> None:
        """
        Show all control buttons (add, remove, remove all, current volume).
        """
        self.setButtonsVisibility(True)

    def hideButtons(self) -> None:
        """
        Hide all control buttons (add, remove, remove all, current volume).
        """
        self.setButtonsVisibility(False)

    def getButtonsVisibility(self) -> bool:
        """
        Get the visibility state of control buttons (add, remove, remove all, current volume).

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._add.isVisible()

    def setRemoveButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the 'Remove' button.

        Parameters
        ~~~~~~~~~~
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveButton(self) -> None:
        """
        Show 'remove' button.
        """
        self._clear.setVisible(True)

    def hideRemoveButton(self) -> None:
        """
        Hide 'remove' button.
        """
        self._clear.setVisible(False)

    def getRemoveButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'remove' button.

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._clear.isVisible()

    def setRemoveAllButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the 'remove all' button.

        Parameters
        ~~~~~~~~~~
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clearall.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveAllButton(self) -> None:
        """
        Show 'remove all' button.
        """
        self._clearall.setVisible(True)

    def hideRemoveAllButton(self) -> None:
        """
        Hide 'remove all' button.
        """
        self._clearall.setVisible(False)

    def getRemoveAllButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'remove all' button.

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._clearall.isVisible()

    def getCheckBoxVisibility(self) -> bool:
        """
        Check whether checkboxes are displayed before each file name in the list.

        Returns
        -------
        bool
            True if checkboxes are visible, False otherwise.
        """
        return self._checkbox

    def setSelectionTo(self, index: str | int) -> None:
        """
        Select a file in the list by its index or by matching its text.

        Parameters
        ----------
        index : str | int
            index (int) or text (str) of the item to select.
        """
        if not self.isEmpty():
            if isinstance(index, str):
                # noinspection PyTypeChecker
                index = self._list.findItems(index, 0)
                if len(index) > 0: index = index[0]
            if isinstance(index, int):
                if index < self._list.count():
                    item = self._list.item(index)
                    item.setSelected(True)
            else: raise TypeError('parameter type {} is not int or str.'.format(type(index)))

    def copySelectionFrom(self, widget: QWidget) -> None:
        """
        Copy the selection state from another FilesSelectionWidget to this widget.

        Parameters
        ----------
        widget : QWidget
            source FilesSelectionWidget to copy selection from
        """
        if isinstance(widget, FilesSelectionWidget):
            items = widget.selectedItems()
            for item in items:
                # < Revision 26/03/2026
                # replace widget by widget._list
                row = widget._list.row(item)
                if row < self._list.count():
                    self._list.item(row).setSelected(True)
                # Revision 26/03/2026 >
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def copySelectionTo(self, widget: QWidget) -> None:
        """
        Copy the selection state from this widget to another FilesSelectionWidget.

        Parameters
        ----------
        widget : QWidget
            target FilesSelectionWidget to copy selection to
        """
        if isinstance(widget, FilesSelectionWidget):
            items = self._list.selectedItems()
            for item in items:
                # < Revision 26/03/2026
                # replace widget by widget._list
                row = self._list.row(item)
                if row < widget._list.count():
                    widget._list.item(row).setSelected(True)
                # Revision 26/03/2026 >
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def clearSelection(self) -> None:
        """
        Clear the current selection in the list widget.
        """
        self._list.clearSelection()

    def hasSelection(self) -> bool:
        """
        Checks if any file is currently selected in the list.

        Returns
        -------
        bool
            True if at least one item is selected, False otherwise.
        """
        return len(self._list.selectedItems()) > 0

    def setSelectionMode(self, v: int) -> None:
        """
        Set the selection mode of the internal QListWidget.

        Parameters
        ----------
        v : int
            QAbstractItemView.selection mode (e.g., QAbstractItemView.SingleSelection,
            QAbstractItemView.ExtendedSelection).
        """
        if isinstance(v, int):
            if 0 <= v < 5:
                # noinspection PyTypeChecker
                self._list.setSelectionMode(v)
            else: raise ValueError('parameter value {} is not between 0 and 4.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setSelectionModeToSingle(self) -> None:
        """
        Set the selection mode of the list widget to single item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(1)

    def setSelectionModeToContiguous(self) -> None:
        """
        Set the selection mode of the list widget to contiguous item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(4)

    def setSelectionModeToExtended(self) -> None:
        """
        Set the selection mode of the list widget to extended item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(3)

    def getSelectionMode(self) -> int:
        """
        Get the current selection mode of the list widget.

        Returns
        -------
        int
            current selection mode.
        """
        return self._list.selectionMode()

    def getFilenames(self) -> list[str]:
        """
        Get a list of all filenames currently in the widget's list.

        Returns
        -------
        list[str]
            list of absolute file paths, or None if the list is empty.
        """
        filenames = None
        n = self._list.count()
        if n > 0:
            filenames = list()
            i: cython.int
            for i in range(n):
                filenames.append(self._list.item(i).data(256))
        return filenames

    def getSelectedFilenames(self) -> list[str]:
        """
        Get a list of filenames for all currently selected items in the list.

        Returns
        -------
        list[str]
            list of absolute file paths for selected items, or None if no items are selected.
        """
        items = self._list.selectedItems()
        filenames = None
        if len(items) > 0:
            filenames = list()
            for item in items:
                filenames.append(item.data(256))
        return filenames

    def getCheckedFilenames(self) -> list[str]:
        """
        Get a list of filenames for all checked items in the list. If checkboxes are not enabled, it returns all
        filenames.

        Returns
        -------
        list[str]
            list of absolute file paths for checked items.
        """
        if not self._checkbox: return self.getFilenames()
        else:
            r = list()
            i: cython.int
            for i in range(self._list.count()):
                if self._list.item(i).checkState() > 0: r.append(self._list.item(i).data(256))
            return r

    def getCheckedIndexes(self) -> list[int]:
        """
        Get a list of indexes for all checked items in the list. If checkboxes are not enabled, it returns indexes for
        all items.

        Returns
        -------
        list[int]
            list of integer indexes for checked items.
        """
        if not self._checkbox: return list(range(self._list.count()))
        else:
            r = list()
            i: cython.int
            for i in range(self._list.count()):
                if self._list.item(i).checkState() > 0: r.append(i)
            return r

    def getCheckStateList(self) -> list[bool]:
        """
        Get a list of boolean check states for all items in the list. If checkboxes are not enabled, it returns a list
        of True for all items.

        Returns
        -------
        list[bool]
            list where True indicates a checked item, False an unchecked item.
        """
        if not self._checkbox: return [True] * self._list.count()
        else:
            r = list()
            i: cython.int
            for i in range(self._list.count()):
                r.append(self._list.item(i).checkState() > 0)
            return r

    def filterSisypheVolume(self) -> None:
        """
        Set the filter to allow only PySisyphe volume files (.xvol) and updates the visibility of the 'current volume'
        button based on the presence of a thumbnail toolbar.
        """
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def containsItem(self, v: QListWidgetItem) -> bool:
        """
        Check if a QListWidgetItem with the same text and data (filename) is already present in the list.

        Parameters
        ----------
        v : QListWidgetItem
            QListWidgetItem to check for

        Returns
        -------
        bool
            True if the item is found, False otherwise.
        """
        if isinstance(v, QListWidgetItem):
            # noinspection PyUnresolvedReferences
            items = self._list.findItems(v.text(), Qt.MatchExactly)
            if len(items) > 0:
                for item in items:
                    if v.data(256) == item.data(256):
                        return True
            return False
        else: raise TypeError('parameter type {} is not QListWidgetItem.'.format(type(v)))

    def getIndexFromItem(self, v: QListWidgetItem) -> int:
        """
        Get the row index of a given QListWidgetItem in the list.

        Parameters
        ----------
        v : QListWidgetItem
            QListWidgetItem to find the index for.

        Returns
        -------
        int
            row index of the item.
        """
        if isinstance(v, QListWidgetItem):
            return self._list.row(v)
        else: raise TypeError('parameter type {} is not QListWidgetItem.'.format(type(v)))

    # < Revision 03/11/2025
    def getItemFromIndex(self, i: int) -> QListWidgetItem:
        """
        Get the QListWidgetItem item at a given row index.

        Parameters
        ----------
        i : int
            row index

        Returns
        -------
        QListWidgetItem
            item at row index i.
        """
        if isinstance(i, int):
            # return self._list.item(i).data(256)
            return self._list.item(i)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))
    # Revision 03/11/2025 >

    def getFilenameFromIndex(self, i: int) -> str:
        """
        Get the filename at a given index.

        Parameters
        ----------
        i : int
            element index

        Returns
        -------
        str
            filename at index i.
        """
        if isinstance(i, int):
            return self._list.item(i).data(256)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    # noinspection PyUnboundLocalVariable
    def add(self,
            filenames: str | list[str] = '',
            label: str = '',
            signal: bool = True,
            wait: DialogWait | None = None) -> None:
        """
        Open a file dialog to select one or more files/directories and adds them to the list. Applies all configured
        filters and performs checks (component, identity, FOV, size, modality, etc.) before adding each file. Displays
        a progress dialog for multiple file additions.

        Parameters
        ----------
        filenames : str | list[str] (optional)
            pre-selected filename or directory to add directly. Defaults to an empty string.
        label : str (optional)
            an optional label for the file dialog title. Defaults to an empty string.
        signal : bool (optional)
            If True, emits FieldChanged and FilesSelectionChanged signals upon successful addition. Defaults to True.
        wait : DialogWait | None (optional)
            an optional DialogWait instance to use for progress reporting. If None, a new one is created for multiple
            files. Defaults to None.
        """
        dtag = wait is None
        if label != '': label += ' '
        # < Revision 30/11/2025
        # param = filenames != '' and exists(filenames)
        #    if param:
        #        buff, paramext = splitext(filenames)
        #        paramext = paramext.lower()
        #        filenames = [filenames]
        #    else: paramext = ''
        if isinstance(filenames, str):
            # Extract filepath, filename and ext of parameter if exists
            param = filenames != '' and exists(filenames)
            if param:
                buff, paramext = splitext(filenames)
                paramext = paramext.lower()
                filenames = [filenames]
            else: paramext = ''
        elif isinstance(filenames, list):
            if len(filenames) > 0:
                buff, paramext = splitext(filenames[0])
                paramext = paramext.lower()
                buff = list()
                for filename in filenames:
                    if exists(filename): buff.append(filename)
                filenames = buff
                param = len(filenames) > 0
            else:
                param = False
                paramext = ''
        # Revision 30/11/2025 >
        # Apply filters
        if self._refDir:
            if param:
                # noinspection PyTypeChecker
                directory = split(filenames)[0]
            else:
                directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                             getcwd(), QFileDialog.ShowDirsOnly)
                QApplication.processEvents()
                self.activateWindow()
            if directory:
                directory = abspath(directory)
                chdir(directory)
                directories = [directory]
                sub = glob(join(directory, '**'))
                i: cython.int
                for i in range(len(sub)-1, -1, -1):
                    if not isdir(sub[i]): del sub[i]
                if len(sub) > 0:
                    if messageBox(self,
                                  'Select directory',
                                  'Add subdirectories ?',
                                  icon=QMessageBox.Question,
                                  buttons=QMessageBox.Yes | QMessageBox.No,
                                  default=QMessageBox.No) == QMessageBox.Yes:
                        directories += sub
                for directory in directories:
                    item = QListWidgetItem(directory)
                    item.setData(256, directory)
                    if self._checkbox:
                        # noinspection PyUnresolvedReferences
                        item.setCheckState(Qt.Checked)
                    if self.containsItem(item):
                        messageBox(self,
                                   'Select directory',
                                   text='{} is already in the list.'.format(item.text()))
                    else:
                        self._list.addItem(item)
                        if signal:
                            # noinspection PyUnresolvedReferences
                            self.FieldChanged.emit(self, directory)
                            # noinspection PyUnresolvedReferences
                            self.FilesSelectionChanged.emit(self)
        elif len(self._refExt) > 0:
            # SisypheVolume
            if self._refxvol:
                if not param or paramext != SisypheVolume.getFileExt():
                    filt = 'PySisyphe Volume (*.xvol)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe volume(s)'.format(label),
                                                             getcwd(), filt)
                    QApplication.processEvents()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.open()
                        wait.setInformationText('Add PySisyphe Volumes...')
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheVolume()
                        # < Revision 17/11/2024
                        # load only XML part (attributes)
                        # fast volume loading
                        # try: img.load(filename)
                        try: img.load(filename, binary=False)
                        # Revision 17/11/2024 >
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is not a valid Sisyphe volume file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # First volume is reference
                        if self._list.count() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    self._refID = self._volume.getID()
                                if self._refSpaceID is not None:
                                    self._refSpaceID = self._volume.getID()
                                if self._refidentity is not None:
                                    self._refidentity = self._volume.getIdentity()
                                if self._refFOV is not None:
                                    self._refFOV = self._volume.getFieldOfView()
                                if self._refSize is not None:
                                    self._refSize = self._volume.getSize()
                                if self._refmodality is not None:
                                    self._refmodality = self._volume.getAcquisition().getModality()
                                if self._refsequence is not None:
                                    self._refsequence = self._volume.getAcquisition().getSequence()
                                if self._refdatatype is not None:
                                    self._refdatatype = self._volume.getDatatype()
                                if self._reforientation is not None:
                                    self._reforientation = self._volume.getOrientationAsString().lower()
                        # Component verification, is single component ?
                        if self._refcomponent == 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c > 1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} is a multi component image.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Component verification, is multi-component ?
                        elif self._refcomponent > 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c == 1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} is a single component image.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same Identity verification
                        if self._refidentity:
                            if img.getIdentity().isNotEqual(self._refidentity):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image identity is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                                wait.hide()
                                txt = '{0} image FOV {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                      'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text=txt.format(basename(filename),
                                                           img.getFieldOfView(),
                                                           self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image size {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getSize(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ICBM verification
                        if self._refICBM:
                            if not img.acquisition.isICBM152():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image is not in ICBM space.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Displacement field verification
                        if self._refField:
                            if not (img.isFloatDatatype() and
                                    img.getNumberOfComponentsPerPixel() == 3
                                    and img.getAcquisition().isDisplacementField()):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image is not displacement field.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Modality verification
                        if self._refmodality:
                            # < Revision 10/10/2024
                            # multiple modality management
                            # self._refmodality is list and not str as before
                            # if img.getAcquisition().getModality() != self._refmodality:
                            # Revision 10/10/2024 >
                            if img.getAcquisition().getModality() not in self._refmodality:
                                # < Revision 17/11/2024
                                # modality list to str conversion
                                if len(self._refmodality) == 1: refmodality = self._refmodality[0]
                                else: refmodality = ', '.join(str(m) for m in self._refmodality)
                                # Revision 17/11/2024 >
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image modality {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getAcquisition().getModality(),
                                               refmodality))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Sequence verification
                        if self._refsequence:
                            # < Revision 10/10/2024
                            # multiple sequence management
                            # self._refsequence is list and not str as before
                            # if img.getAcquisition().getSequence() != self._refsequence:
                            # Revision 10/10/2024 >
                            if img.getAcquisition().getSequence() not in self._refsequence:
                                # < Revision 17/11/2024
                                # sequence list to str conversion
                                if len(self._refsequence) == 1: refsequence = self._refsequence[0]
                                else: refsequence = ', '.join(str(s) for s in self._refsequence)
                                # Revision 17/11/2024 >
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image sequence {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getAcquisition().getSequence(),
                                               refsequence))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Datatype verification
                        if self._refdatatype:
                            if img.getDatatype() != self._refdatatype:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image datatype {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getDatatype(),
                                               self._refdatatype))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Orientation verification
                        if self._reforientation:
                            if img.getOrientationAsString().lower() != self._reforientation:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image orientation {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getOrientationAsString(),
                                               self._reforientation))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ID verification
                        if self._refSpaceID:
                            if img.getID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Registered verification
                        if self._refID:
                            if img.getID() != self._refID:
                                if self._refID not in img.getTransforms():
                                    wait.hide()
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image is not registered to reference.'.format(
                                                   basename(filename)))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Frame verification
                        if self._refframe:
                            if not img.getAcquisition().getFrame():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image has no frame.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Range verification
                        if self._refRange:
                            r = img.display.getRange()
                            if r[0] < self._refRange[0] or r[1] > self._refRange[1]:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image range is not between {} and {} .'.format(
                                               basename(filename),
                                               self._refRange[0],
                                               self._refRange[1]))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Transform verification
                        # < Revision 04/01/2026
                        if self._reftrf:
                            if not img.hasTransform(self._reftrf):
                                wait.hide()
                                if self._reftrf == 'LEKSELL':
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image has no geometric transformation to the '
                                                    'Leksell\'s stereotactic space.'.format(basename(filename)))
                                else:
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image has no transform to {} .'.format(
                                                   basename(filename), self._reftrf))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Revision 04/01/2026 >
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe volume index {}\n{}'.format(idx, str(img)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheROI
            elif self._refxroi:
                if not param or paramext != SisypheROI.getFileExt():
                    filt = 'PySisyphe ROI (*.xroi)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe ROI(s)'.format(label),
                                                             getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.open()
                        wait.setInformationText('Add PySisyphe ROIs...')
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheROI()
                        try: img.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is not a valid PySisyphe ROI file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # First volume is reference
                        if self._list.count() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    # noinspection PyUnresolvedReferences
                                    self._refID = self._volume.getReferenceID()
                                if self._refSpaceID is not None:
                                    # noinspection PyUnresolvedReferences
                                    self._refSpaceID = self._volume.getReferenceID()
                                if self._refFOV is not None:
                                    self._refFOV = self._volume.getFieldOfView()
                                if self._refSize is not None:
                                    self._refSize = self._volume.getSize()
                        # Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI size {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getSize(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI FOV {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getFieldOfView(),
                                               self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ID verification
                        if self._refSpaceID:
                            if img.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI ID does not match reference.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Registered verification
                        if self._refID:
                            if img.getReferenceID() != self._refID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI is not registered to reference.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe ROI index {}\n{}'.format(idx, str(img)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheMesh
            elif self._refxmesh:
                if not param or paramext != SisypheMesh.getFileExt():
                    filt = SisypheMesh.getFilterExt()
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe mesh'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe mesh(es)...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        mesh = SisypheMesh()
                        try: mesh.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} is not a valid Sisyphe mesh file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if mesh.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} mesh ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe mesh index {}\n{}'.format(idx, str(mesh)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheStreamlines
            elif self._refxtracts:
                if not param or paramext != SisypheStreamlines.getFileExt():
                    filt = SisypheStreamlines.getFilterExt()
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe streamlines'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe streamlines...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        sl = SisypheStreamlines()
                        try: sl.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is not a valid Sisyphe streamlines file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if sl.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} streamlines ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not sl.getDWIFOV(decimals=1) != self._refFOV:
                                wait.hide()
                                txt = '{0} streamlines field of view {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                      'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text=txt.format(basename(filename), sl.getDWIFOV, self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Size verification
                        if self._refSize:
                            if sl.getDWIShape() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} size {} does not match reference {}.'.format(
                                               basename(filename),
                                               sl.getDWIShape(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Whole brain tractogram verification
                        if self._refwhole:
                            if not sl.isWholeBrainTractogram():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is not a whole brain tractogram.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Not whole brain tractogram verification
                        if self._refnotwhole:
                            if sl.isWholeBrainTractogram():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is a whole brain tractogram.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Centroid verification
                        if self._refcentroid:
                            if not sl.isCentroid():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is not a centroid streamline.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Not centroid vérification
                        if self._refnotcentroid:
                            if sl.isCentroid():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is a centroid streamline.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe streamlines index {}\n{}'.format(idx, str(sl)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Tools, HandleWidget, LineWidget, ToolCollectionWidget
            # < Revision 13/02/2026
            elif self._refxtools:
                if not param or paramext not in (HandleWidget.getFileExt(),
                                                 LineWidget.getFileExt(),
                                                 ToolWidgetCollection.getFileExt()):
                    # < Revision 20/02/2026
                    filt = ';;'.join([ToolWidgetCollection.getFilterExt(),
                                      HandleWidget.getFilterExt(),
                                      LineWidget.getFilterExt()])
                    # Revision 20/02/2026 >
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe tools', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe tools'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe tools...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        ext = splitext(filename)[1]
                        try:
                            if ext == HandleWidget.getFileExt():
                                tool = HandleWidget('')
                                tool.load(filename)
                            elif ext == LineWidget.getFileExt():
                                tool = LineWidget('')
                                tool.load(filename)
                            elif ext == ToolWidgetCollection.getFileExt():
                                tool = ToolWidgetCollection()
                                tool.load(filename)
                            else:
                                if self._stop: break
                                else: continue
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} is not a valid Sisyphe tools file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if isinstance(tool, ToolWidgetCollection):
                                if tool.getReferenceID() != self._refSpaceID:
                                    wait.hide()
                                    messageBox(self,
                                               'PySisyphe tools file selector',
                                               text='{} tools ID is not allowed.'.format(basename(filename)))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe tools index {}\n{}'.format(idx, str(tool)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Revision 13/02/2026 >
            # DICOM
            elif self._refdicom:
                # < Revision 13/02/2026
                #if not param or paramext not in getDicomExt().append(''):
                # if not param or paramext not in getDicomExt():
                if not param:
                # Revision 13/02/2026 >
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select DICOM file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add DICOM files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        if isDicom(filename):
                            # Prefix verification
                            if self._refprefix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[:len(self._refprefix)] == self._refprefix:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not have {} prefix.'.format(basename(filename),
                                                                                         self._refprefix))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            # Suffix verification
                            if self._refsuffix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[-len(self._refsuffix):] == self._refsuffix:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not have {} suffix.'.format(basename(filename),
                                                                                         self._refsuffix))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            # Filename contains verification
                            if self._refcontains:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if bname.find(self._refcontains) > -1:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not contains {} string.'.format(basename(filename),
                                                                                             self._refcontains))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            path, name = split(filename)
                            item = QListWidgetItem(name)
                            item.setData(256, filename)
                            if self._checkbox:
                                # noinspection PyUnresolvedReferences
                                item.setCheckState(Qt.Checked)
                            if self.containsItem(item):
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} is already in the list.'.format(item.text()))
                                wait.show()
                            else:
                                self._list.addItem(item)
                                if signal:
                                    # noinspection PyUnresolvedReferences
                                    self.FieldChanged.emit(self, filename)
                                    # noinspection PyUnresolvedReferences
                                    self.FilesSelectionChanged.emit(self)
                        else:
                            wait.hide()
                            messageBox(self,
                                       'DICOM file selector',
                                       text='{} is not a valid dicom file.'.format(self._name))
                            wait.show()
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'DICOM file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Other file
            else:
                if not param or paramext not in self._refExt:
                    filt = 'Files ('
                    for ext in self._refExt:
                        filt += '*{} '.format(ext)
                    filt = filt.rstrip() + ')'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        else:
                            self._list.addItem(item)
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'File selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
        else:
            if not param:
                filt = 'All files (*.*)'
                filenames = QFileDialog.getOpenFileNames(self, 'Select file', getcwd(), filt)
                QApplication.processEvents()
                self.activateWindow()
                filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is already in the list.'.format(item.text()))
                            wait.show()
                        else:
                            self._list.addItem(item)
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'File selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()

    def clearItem(self, i: int, signal: bool = True) -> None:
        """
        Remove a file from the list at the specified index.

        Parameters
        ----------
        i : int
            index of the item to remove
        signal : bool (optional)
            If True, emits FieldCleared signal. Defaults to True.
        """
        if isinstance(i, int):
            if i < self._list.count():
                self._list.takeItem(i)
                self._add.setEnabled(True)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.FieldCleared.emit(self, [i])
            else: raise ValueError('parameter index is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    def clearLastItem(self, signal: bool = True) -> None:
        """
        Remove the last file from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared signal. Defaults to True.
        """
        n = self._list.count()
        if n > 0: self._list.takeItem(n - 1)
        self._add.setEnabled(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, [n-1])

    def clear(self, signal: bool = True) -> None:
        """
        Remove all currently selected files from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared and FilesSelectionWidgetCleared signals. Defaults to True.
        """
        rows = list()
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            for item in selecteditems:
                row = self._list.row(item)
                rows.append(row)
                self._list.takeItem(row)
            self._add.setEnabled(True)
        if self._list.count() == 0:
            if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, rows)
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetCleared.emit(self)

    def clearall(self, signal: bool = True) -> None:
        """
        Remove all files from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared and FilesSelectionWidgetCleared signals. Defaults to True.
        """
        rows = list(range(self._list.count()))
        self._list.clear()
        self._add.setEnabled(True)
        if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, rows)
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetCleared.emit(self)

    def isEmpty(self) -> bool:
        """
        Check if the list of files is empty.

        Returns
        -------
        bool
            True if the list contains no files, False otherwise.
        """
        return self._list.count() == 0

    def filenamesCount(self) -> int:
        """
        Get the number of files currently in the list.

        Returns
        -------
        int
            count of files.
        """
        return self._list.count()

    # Qt Drop events

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
        """
        Handles drag enter events, accepting drops if the mime data contains text (e.g., file paths).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event : QDragEnterEvent
            Qt drag enter event.
        """
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """
        Handles drop events, attempting to open the dropped file(s).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event ! QDropEvent
            Qt drop event.
        """
        if event.mimeData().hasText():
            event.accept()
            files = event.mimeData().text().split('\n')
            for file in files:
                if file != '': self.add(file[7:])


# < Revision 26/03/2026
# add FilesSelectionWithParametersWidget class
class FilesSelectionWithParametersWidget(QWidget, SelectionFilter):
    """
    FilesSelectionWithParametersWidget class

    Description
    ~~~~~~~~~~~

    Widget that manages files selection and associated parameters.

    This widget consists of the following elements, which are displayed from left to right.

    - QTreeWidget widget, displays a list of selected files and parameters
    - IconLabel widget with '<' icon, to add a PySisypheVolume from the thumbnail bar (optional widget)
    - QPushButton 'add', to add a file from a dialog
    - QPushButton 'remove', to remove the selected file(s) from the list
    - QPushButton 'remove all', to remove all the files from the list
    - QPushButton 'load', to load parmater values
    - QPushButton 'save', to save parmater values

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FilesSelectionWithParametersWidget

    Creation: 26/03/2026
    Last revision: 27/04/2026
    """

    # Custom Qt Signals

    FieldChanged: pyqtSignal = pyqtSignal(QWidget, str)
    FieldCleared: pyqtSignal = pyqtSignal(QWidget, list)
    FilesSelectionChanged: pyqtSignal = pyqtSignal(QWidget)
    FilesSelectionWidgetSelectionChanged: pyqtSignal = pyqtSignal(QWidget, str)
    FilesSelectionWidgetCleared: pyqtSignal = pyqtSignal(QWidget)
    FilesSelectionWidgetDoubleClicked: pyqtSignal = pyqtSignal(QTreeWidgetItem)

    # Special method

    def __init__(self, maxcount: int = 100, checkbox: bool = False, parent: QWidget | None = None)  -> None:
        """
        FilesSelectionWidget instance constructor.

        Parameters
        ----------
        maxcount : int
            maximum number of files allowed in the list.
        checkbox : bool
            display or not a QCheckbox widget before each file name in the list.
        parent : QWidget | None (optional)
            parent widget.
        """
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self._refCount = maxcount
        self._countWarning = True
        self._checkbox = checkbox
        self._stop = False
        self.setAcceptDrops(True)
        # < Revision 12/12/2024
        # select only single-component volumes
        self.filterSingleComponent()
        # < Revision 12/12/2024
        self._parameters = dict()

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._label = QLabel()
        self._label.setVisible(False)
        self._list = QTreeWidget()
        self._list.setAlternatingRowColors(True)
        # < Revision 09/04/2026
        self._list.header().hide()
        # Revision 09/04/2026 >
        # noinspection PyUnresolvedReferences
        self._list.itemSelectionChanged.connect(self._selectionChanged)
        # noinspection PyTypeChecker
        self._list.setSelectionMode(3)  # Extended selection
        # noinspection PyUnresolvedReferences
        self._list.itemDoubleClicked.connect(self._onDoubleClicked)
        self._current = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'left.png')), '')
        self._add = QPushButton('Add')
        self._clear = QPushButton('Remove')
        self._clearall = QPushButton('Remove all')
        self._load = QPushButton('Load parameter')
        self._save = QPushButton('Save parameter')
        self._load.setVisible(False)
        self._save.setVisible(False)
        # self._current.setFixedSize(QSize(50, 32))
        self._current.setToolTip('Add thumbnail volume to the list.')
        self._add.setToolTip('Add file(s) to the list.')
        self._clear.setToolTip('Remove selected file(s) from the list.')
        self._clearall.setToolTip('Remove all files from the list.')
        self._load.setToolTip('Load parameter values from a file.')
        self._save.setToolTip('Save parameter values to a file.')

        # noinspection PyUnresolvedReferences
        self._current.clicked.connect(self._onMenuThumbnailShow)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._list)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._current)
        layout.addWidget(self._add)
        layout.addWidget(self._clear)
        layout.addWidget(self._clearall)
        layout.addWidget(self._load)
        layout.addWidget(self._save)
        layout.addStretch()
        self._layout.addLayout(layout)

        self._current.setVisible(False)

        # noinspection PyUnresolvedReferences
        self._add.clicked.connect(lambda: self.add())
        # < Revision 19/06/2025
        # self._clear.clicked.connect(self.clear)
        # self._clearall.clicked.connect(self.clearall)
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(lambda: self.clear())
        # noinspection PyUnresolvedReferences
        self._clearall.clicked.connect(lambda: self.clearall())
        # Revision 19/06/2025 >

    """
    Private attributes

    _label      QLabel
    _list       QTreeWidget
    _current    QPushButton
    _add        QPushButton
    _clear      QPushButton
    _clearall   QPushButton
    _stop       bool, break files check after failure
    _refCount   int, maximum number of files
    """

    # Private method

    def _selectionChanged(self):
        """
        Slot connected to the itemSelectionChanged signal of the QListWidget.
        Emits FilesSelectionWidgetSelectionChanged signal with the filename of the first selected item.
        """
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetSelectionChanged.emit(self, selecteditems[0].data(0, 256))

    def _onMenuThumbnailShow(self):
        """
        Displays the context menu for selecting PySisyphe (.xvol) volumes from the thumbnail toolbar.
        If only one volume is available, it's directly added. If multiple, a popup menu is shown.
        Includes an 'All' option for adding all volumes from the toolbar.
        """
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.add(v.getFilename())
            if n > 1:
                menu = QMenu(self._current)
                # noinspection PyUnresolvedReferences
                menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                menu.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                menu.setAttribute(Qt.WA_TranslucentBackground, True)
                i: cython.int
                for i in range(n):
                    v = self._thumbnail.getVolumeFromIndex(i)
                    action = menu.addAction(v.getBasename())
                    action.setData(v.getFilename())
                # < Revision 08/11/2024
                if n > 1:
                    menu.addSeparator()
                    menu.addAction('All')
                # Revision 08/11/2024 >
                # noinspection PyUnresolvedReferences
                menu.triggered.connect(self._onMenuThumbnailSelect)
                menu.exec(self._current.mapToGlobal(QPoint(0, self._current.height())))

    def _onMenuThumbnailSelect(self, action: QAction):
        """
        Handles the selection of a PySisyphe volume (.xvol) from the thumbnail menu.
        If 'All' is selected, it adds all PySisyphe volumes (.xvol) from the thumbnail toolbar.

        Parameters
        ----------
        action : QAction
            QAction that was triggered, containing the filename or 'All'.
        """
        # < Revision 08/11/2024
        if action.text() == 'All':
            n = self._thumbnail.getWidgetsCount()
            wait = DialogWait(progress=True, progressmin=0, progressmax=n, cancel=True)
            wait.open()
            i: cython.int
            for i in range(n):
                filename = self._thumbnail.getVolumeFromIndex(i).getFilename()
                wait.incCurrentProgressValue()
                wait.setInformationText('Add {}...'.format(basename(filename)))
                self.add(filename)
                if wait.getStopped(): break
            wait.close()
        # Revision 08/11/2024 >
        else: self.add(str(action.data()))

    def _onDoubleClicked(self, item: QTreeWidgetItem):
        """
        Slot connected to the itemDoubleClicked signal of the QListWidget.
        Emits FilesSelectionWidgetDoubleClicked signal with the double-clicked item.

        Parameters
        ----------
        item : QTreeWidgetItem
            QTreeWidgetItem that was double-clicked.
        """
        if item is not None:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetDoubleClicked.emit(item)

    def _initItemParameterWidgets(self, item: QTreeWidgetItem) -> None:
        if len(self._parameters) > 0:
            i: cython.int
            for i, name in enumerate(self._parameters):
                param = self._parameters[name]
                if param['dtype'] == 'int':
                    widget = QSpinBox(self)
                    if 'vmin' in param: widget.setMinimum(int(param['vmin']))
                    else: widget.setMinimum(0)
                    if 'vmax' in param: widget.setMaximum(int(param['vmax']))
                    else: widget.setMaximum(maxsize)
                elif param['dtype'] == 'float':
                    widget = QDoubleSpinBox(self)
                    if 'vmin' in param: widget.setMinimum(float(param['vmin']))
                    else: widget.setMinimum(0.0)
                    if 'vmax' in param: widget.setMaximum(float(param['vmax']))
                    else: widget.setMaximum(float_info.max)
                    if 'decimals' in param:
                        d = int(param['decimals'])
                        widget.setDecimals(d)
                        widget.setSingleStep(1 / (10 * d))
                    else:
                        widget.setDecimals(1)
                        widget.setSingleStep(0.1)
                elif param['dtype'] == 'str':
                    widget = QLineEdit(self)
                elif param['dtype'] == 'lstr':
                    widget = QComboBox(self)
                    if len(param['values']) > 0:
                        for v in param['values']:
                            widget.addItem(v)
                        widget.setCurrentIndex(0)
                else: raise AttributeError('parameter data type {} is not defined.'.format(param['dtype']))
                widget.setMinimumWidth(100)
                if 'width' in param: widget.setFixedWidth(int(param['width']))
                else: widget.adjustSize()
                container = QWidget()
                lyout = QHBoxLayout()
                lyout.setContentsMargins(0, 0, 0, 0)
                lyout.setAlignment(widget, Qt.AlignmentFlag.AlignHCenter)
                lyout.addWidget(widget)
                container.setLayout(lyout)
                self._list.setItemWidget(item, i + 1, container)
                self._list.setColumnWidth(i + 1, widget.sizeHint().width() + 20)
                if param['dcm']:
                    value = None
                    filename = item.data(0, 256)
                    if exists(filename):
                        bname, ext = splitext(filename)
                        if ext == '.dcm':
                            ds = dcmread(filename, stop_before_pixels=True)
                            if name in ds: value = ds[name].value
                        elif ext == '.xvol':
                            ext = XmlDicom.getFileExt()
                            filename = bname + ext
                            if not exists(filename): continue
                        if ext == XmlDicom.getFileExt():
                            dcm = XmlDicom()
                            dcm.loadXmlDicomFilename(filename)
                            if name in dcm: value = dcm.getDataElementValue(name)
                    if value:
                        dtype = param['dtype']
                        if dtype == 'int': widget.setValue(int(value))
                        elif dtype == 'float': widget.setValue(float(value))
                        elif dtype == 'str': widget.setText(str(value))
                        elif dtype == 'lstr':
                            c = widget.findText(str(value), Qt.MatchFlag.MatchContains)
                            if c > -1: widget.setCurrentIndex(c)

    def _loadParameters(self, action: QAction) -> None:
        if self._list.topLevelItemCount() > 0:
            name = action.text()
            if name in self._parameters:
                filt = 'Text file (*.txt);;CSV file (*.csv);;Numpy file (*.npy)'
                filename = QFileDialog.getOpenFileName(self,
                                                       'Load the {} values'.format(name),
                                                       getcwd(),
                                                       filt)[0]
                QApplication.processEvents()
                if filename:
                    ext = splitext(filename)[1]
                    try:
                        if ext == '.txt':
                            with open(filename) as f:
                                buff = f.read()
                                if ',' in buff: values = loadtxt(filename, delimiter=',')
                                elif ';' in buff: values = loadtxt(filename, delimiter=';')
                                elif '|' in buff: values = loadtxt(filename, delimiter='|')
                                elif ' ' in buff: values = loadtxt(filename, delimiter=' ')
                                # < Revision 27/04/2026
                                else: values = loadtxt(filename)
                                if values.size == 1: values = values.flatten()
                                # Revision 27/04/2026 >
                        elif ext == '.csv': values = loadtxt(filename, delimiter=',')
                        elif ext == '.npy': values = load(filename)
                    except:
                        messageBox(self,
                                   'Load values'.format(name),
                                   text='Error loading {} values.'.format(basename(filename)))
                        return
                    dtype = self._parameters[name]['dtype']
                    idx = list(self._parameters.keys()).index(name) + 1
                    if values.ndim > 1: values = values[0, ...]
                    i: cython.int
                    for i in range(self._list.topLevelItemCount()):
                        if i < values.shape[0]:
                            w = self._list.itemWidget(self._list.topLevelItem(i), idx)
                            widget = w.layout().itemAt(0).widget()
                            if widget is not None:
                                try:
                                    if dtype == 'int': widget.setValue(int(values[i]))
                                    elif dtype == 'float': widget.setValue(float(values[i]))
                                    elif dtype == 'str': widget.setText(str(values[i]))
                                    elif dtype == 'lstr':
                                        c = widget.findText(str(values[i]), Qt.MatchFlag.MatchContains)
                                        if c > -1: widget.setCurrentIndex(c)
                                except: pass

    def _saveParameters(self, action: QAction) -> None:
        if self._list.topLevelItemCount() > 0:
            name = action.text()
            if name in self._parameters:
                filt = 'Text file (*.txt);;CSV file (*.csv);;Numpy file (*.npy)'
                filename = QFileDialog.getSaveFileName(self,
                                                       'Save the {} values'.format(name),
                                                       getcwd(),
                                                       filt)[0]
                QApplication.processEvents()
                if filename:
                    ext = splitext(filename)[1]
                    values = array(self.getParameterValues(name))
                    try:
                        if ext == '.txt': savetxt(filename, values, delimiter=',')
                        elif ext == '.csv': savetxt(filename, values, delimiter=',')
                        elif ext == '.npy': save(filename, values)
                    except:
                        messageBox(self,
                                   'Save values'.format(name),
                                   text='Error saving {} values.'.format(basename(filename)))

    # Public methods

    def addParameter(self,
                     name: str,
                     dtype: str,
                     vmin: int | float | None = None,
                     vmax: int |float | None = None,
                     decimals: int = 1,
                     values: list[str] | None = None,
                     width: int = 0) -> None:
        """
        Add a parameter.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Parameters
        ----------
        name : str
            parameter name
        dtype : str
            parameter type 'int', 'float', 'str', 'lstr'
        vmin : int | float | None
            minimum value parameter defined for the 'int' and 'float' data types
        vmax : int | float | None
            maximum value parameter defined for the 'int' and 'float' data types
        decimals : int
            number of decimals for float data type
        values : list[str] | None
            ComboBox items
        width : int (optional)
            fixed width of the parameter widget (default 0, no fixed width)
        """
        if dtype in ('int', 'float', 'str', 'lstr'):
            param = dict()
            param['dtype'] = dtype
            if vmin is not None:
                if dtype == 'int': param['vmin'] = int(vmin)
                elif dtype == 'float': param['vmin'] = float(vmin)
            if vmax is not None:
                if dtype == 'int': param['vmax'] = int(vmax)
                elif dtype == 'float': param['vmax'] = float(vmax)
            if decimals is not None and dtype == 'float': param['decimals'] = decimals
            if values is not None and dtype == 'lstr': param['values'] = values
            param['width'] = 100
            if width is not None and width > 0: param['width'] = width
            param['dcm'] = False
            self._parameters[name] = param
            hdr = [self._label.text()] + list(self._parameters.keys())
            self._list.setHeaderLabels(hdr)
            self._list.header().setStretchLastSection(False)
            self._list.header().setSectionResizeMode(0, QHeaderView.Stretch)
            # < Revision 09/04/2026
            self._list.header().show()
            # Revision 09/04/2026 >
            i: cython.int
            for i in range(1, len(hdr)):
                self._list.header().setSectionResizeMode(i, QHeaderView.Interactive)
            if self._load.menu() is not None: self._load.menu().clear()
            if self._save.menu() is not None: self._save.menu().clear()
            menu_load = QMenu(self._load)
            menu_save = QMenu(self._save)
            for key in self._parameters:
                menu_load.addAction(key)
                menu_save.addAction(key)
            menu_load.triggered.connect(self._loadParameters)
            menu_save.triggered.connect(self._saveParameters)
            self._load.setMenu(menu_load)
            self._save.setMenu(menu_save)
            self._load.setVisible(True)
            self._save.setVisible(True)
        else: raise ValueError('dtype parameter {} is not valid.'.format(dtype))

    def addDicomParameter(self,
                          name: str,
                          vmin: int | float | None = None,
                          vmax: int | float | None = None,
                          decimals: int = 1,
                          width: int = 0):
        """
        Add a dicom field parameter. The value of this parameter is automatically retrieved from a DICOM file or an
        .xvol file (searched in the associated XmlDicom .xml file) added by the user in the widget. The parameter name
        is used as a Dicom field keyword.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Parameters
        ----------
        name : str
            dicom field name
        vmin : int | float | None
            minimum value parameter defined for the 'int' and 'float' data types
        vmax : int | float | None
            maximum value parameter defined for the 'int' and 'float' data types
        decimals : int
            number of decimals for float data type
        width : int (optional)
            fixed width of the parameter widget (default 0, no fixed width)
        """
        tag = tag_for_keyword(name)
        if tag is not None:
            param = dict()
            VR = get_entry(tag)[0]
            if VR in ('AE', 'AS', 'CS', 'DA', 'DT', 'LO', 'PN', 'SH', 'ST', 'TM', 'UI'): param['dtype'] = 'str'
            elif VR in ('DS', 'FL', 'FD'): param['dtype'] = 'float'
            elif VR in ('IS', 'SL', 'SS', 'US'): param['dtype'] = 'int'
            else: raise ValueError('unsupported VR {} from {} parameter.'.format(VR, name))
            if vmin is not None:
                if param['dtype'] == 'int': param['vmin'] = int(vmin)
                elif param['dtype'] == 'float': param['vmin'] = float(vmin)
            if vmax is not None:
                if param['dtype'] == 'int': param['vmax'] = int(vmax)
                elif param['dtype'] == 'float': param['vmax'] = float(vmax)
            if decimals is not None and param['dtype'] == 'float': param['decimals'] = decimals
            param['dcm'] = True
            param['width'] = 100
            if width is not None and width > 0: param['width'] = width
            self._parameters[name] = param
            hdr = [self._label.text()] + list(self._parameters.keys())
            self._list.setHeaderLabels(hdr)
            self._list.header().setStretchLastSection(False)
            self._list.header().setSectionResizeMode(0, QHeaderView.Stretch)
            # < Revision 09/04/2026
            self._list.header().show()
            # Revision 09/04/2026 >
            i: cython.int
            for i in range(1, len(hdr)):
                self._list.header().setSectionResizeMode(i, QHeaderView.Interactive)
            if self._load.menu() is not None: self._load.menu().clear()
            if self._save.menu() is not None: self._save.menu().clear()
            menu_load = QMenu(self._load)
            menu_save = QMenu(self._save)
            for key in self._parameters:
                menu_load.addAction(key)
                menu_save.addAction(key)
            menu_load.triggered.connect(self._loadParameters)
            menu_save.triggered.connect(self._saveParameters)
            self._load.setMenu(menu_load)
            self._save.setMenu(menu_save)
            self._load.setVisible(True)
            self._save.setVisible(True)
        else: raise ValueError('Dicom parameter {} is not valid.'.format(name))

    def hasParameter(self, name: str) -> bool:
        """
        Check if the parameter name is defined.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Parameters
        ----------
        name : str
            parameter name

        Returns
        -------
        bool
        """
        return name in self._parameters

    def setParameterDict(self, params: dict[str, dict[str, str | int | float | list[str]]]) -> None:
        """
        Set the parameters attribute.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Parameters
        ----------
        params : dict[str, dict[str, str | int | float | list[str]]]
            parameters dict
        """
        self._parameters = params

    def getParameterDict(self) -> dict[str, dict[str, str | int | float | list[str]]]:
        """
        Get the parameters attribute.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Returns
        -------
        dict[str, dict[str, str | int | float | list[str]]]
            parameters dict
        """
        return self._parameters

    def getParameterValues(self, name: str) -> list:
        """
        Get the values of a parameter.

        The parameters are displayed to the right of the file name.
        Four parameter types are defined as 'dtype' keys:
            - 'int', displayed as a QSpinBox
            - 'float', displayed as a QDoubleSpinBox
            - 'str', displayed as a QLineEdit
            - 'lstr', displayed as a QComboBox
        The 'vmin' and 'vmax' keys are used to set the range of "int" or "float" parameters.
        The 'decimals' key is used to set the number of decimals for the float data type.
        The 'values' key is used to set the ComboBox items.
        The 'width' key is used to set the fixed width of the widget.
        The 'dcm' key indicates if this parameter is a DICOM field.

        Parameters
        ----------
        name : str
            parameter name

        Returns
        -------
        list
            parameter values
        """
        if name in self._parameters:
            idx = list(self._parameters.keys()).index(name) + 1
            r = list()
            i: cython.int
            for i in range(self._list.topLevelItemCount()):
                w = self._list.itemWidget(self._list.topLevelItem(i), idx)
                widget = w.layout().itemAt(0).widget()
                if widget is not None:
                    dtype = self._parameters[name]['dtype']
                    if dtype == 'int': r.append(widget.value())
                    elif dtype == 'float': r.append(widget.value())
                    elif dtype == 'str': r.append(widget.text())
                    elif dtype == 'lstr': r.append(widget.currentText())
            return r
        else: raise ValueError('No parameter {}.'.format(name))

    def fileCountWarningOn(self):
        self._countWarning = True

    def fileCountWarningOff(self):
        self._countWarning = False

    def setFileCountWarning(self, v: bool = True):
        self._countWarning = v

    def getFileCountWaring(self) -> bool:
        return self._countWarning

    def setStopCheckAfterFailure(self, stop: bool) -> None:
        """
        Set whether the file checking process should stop after the first file fails a filter check during an 'add' operation.

        Parameters
        ----------
        stop : bool
            True to stop on first failure, False to continue checking other files.
        """
        if isinstance(stop, bool): self._stop = stop
        else: raise TypeError('parameter type {} is not bool.'.format(type(stop)))

    def getStopCheckAfterFailure(self) -> bool:
        """
        Get the current setting for stopping file checks after a failure.

        Returns
        -------
        bool
            True if checks stop on first failure, False otherwise.
        """
        return self._stop

    def setMaximumNumberOfFiles(self, n: int)  -> None:
        """
        Set the maximum number of files allowed in the list.

        Parameters
        ----------
        n : int
            maximum number of files.
        """
        if isinstance(n, int): self._refCount = n
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def getMaximumNumberOfFiles(self) -> int:
        """
        Get the maximum number of files allowed in the list.

        Returns
        -------
        int
            maximum number of files.
        """
        return self._refCount

    def setToolbarThumbnail(self, t: ToolBarThumbnail) -> None:
        """
        Set the ToolBarThumbnail widget for accessing volumes and makes the 'current volume' button visible if a
        thumbnail toolbar is provided.

        Parameters
        ----------
        t : ToolBarThumbnail
            ToolBarThumbnail instance.
        """
        super().setToolbarThumbnail(t)
        self._current.setVisible(True)

    def setLabelVisibility(self, v: bool) -> None:
        """
        Set the visibility of the descriptive label for the widget.

        Parameters
        ----------
        v : bool
            True to show the label, False to hide it.
        """
        if isinstance(v, bool): self._label.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showLabel(self) -> None:
        """
        Show the descriptive label.
        """
        self._label.setVisible(True)

    def hideLabel(self) -> None:
        """
        Hide the descriptive label.
        """
        self._label.setVisible(False)

    def getLabelVisibility(self) -> bool:
        """
        Get the visibility state of the descriptive label.

        Returns
        -------
        bool
            True if the label is visible, False otherwise.
        """
        return self._label.isVisible()

    def setTextLabel(self, txt: str) -> None:
        """
        Set the text of the descriptive label and makes it visible.

        Parameters
        ----------
        txt : str
            text to set for the label.
        """
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(True)
        else: raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getTextLabel(self) -> str:
        """
        Get the current text of the descriptive label.

        Returns
        -------
        str
            text of the label.
        """
        return self._label.text()

    def getLabel(self) -> QLabel:
        """
        Get the QLabel widget used as the descriptive label.

        Returns
        -------
        QLabel
            QLabel instance.
        """
        return self._label

    def setCurrentVolumeButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the button that allows adding the current thumbnail volume to the list.

        Parameters
        ----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool):
            v = v and self.hasToolbarThumbnail()
            self._current.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showCurrentVolumeButton(self) -> None:
        """
        Show the 'current volume' button.
        """
        self.setCurrentVolumeButtonVisibility(True)

    def hideCurrentVolumeButton(self) -> None:
        """
        Hide the 'current volume' button.
        """
        self.setCurrentVolumeButtonVisibility(False)

    def getCurrentVolumeButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'current volume' button.

        Returns
        -------
        bool
            True if the button is visible, False otherwise.
        """
        return self._current.isVisible()

    def setButtonsVisibility(self, v: bool) -> None:
        """
        Set the visibility of all control buttons (add, remove, remove all, current volume).

        Parameters
        ----------
        v : bool
            True to show buttons, False to hide them.
        """
        if isinstance(v, bool):
            self._add.setVisible(v)
            self._clear.setVisible(v)
            self._clearall.setVisible(v)
            self.setCurrentVolumeButtonVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showButtons(self) -> None:
        """
        Show all control buttons (add, remove, remove all, current volume).
        """
        self.setButtonsVisibility(True)

    def hideButtons(self) -> None:
        """
        Hide all control buttons (add, remove, remove all, current volume).
        """
        self.setButtonsVisibility(False)

    def getButtonsVisibility(self) -> bool:
        """
        Get the visibility state of control buttons (add, remove, remove all, current volume).

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._add.isVisible()

    def setRemoveButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the 'Remove' button.

        Parameters
        ~~~~~~~~~~
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveButton(self) -> None:
        """
        Show 'remove' button.
        """
        self._clear.setVisible(True)

    def hideRemoveButton(self) -> None:
        """
        Hide 'remove' button.
        """
        self._clear.setVisible(False)

    def getRemoveButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'remove' button.

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._clear.isVisible()

    def setRemoveAllButtonVisibility(self, v: bool) -> None:
        """
        Set the visibility of the 'remove all' button.

        Parameters
        ~~~~~~~~~~
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool): self._clearall.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveAllButton(self) -> None:
        """
        Show 'remove all' button.
        """
        self._clearall.setVisible(True)

    def hideRemoveAllButton(self) -> None:
        """
        Hide 'remove all' button.
        """
        self._clearall.setVisible(False)

    def getRemoveAllButtonVisibility(self) -> bool:
        """
        Get the visibility state of the 'remove all' button.

        Returns
        -------
        bool
            True if buttons are visible, False otherwise.
        """
        return self._clearall.isVisible()

    def getCheckBoxVisibility(self) -> bool:
        """
        Check whether checkboxes are displayed before each file name in the list.

        Returns
        -------
        bool
            True if checkboxes are visible, False otherwise.
        """
        return self._checkbox

    def setSelectionTo(self, index: str | int) -> None:
        """
        Select a file in the list by its index or by matching its text.

        Parameters
        ----------
        index : str | int
            index (int) or text (str) of the item to select.
        """
        if not self.isEmpty():
            if isinstance(index, str):
                # noinspection PyTypeChecker
                index = self._list.findItems(index, 0)
                if len(index) > 0: index = index[0]
            if isinstance(index, int):
                if index < self._list.topLevelItemCount():
                    item = self._list.topLevelItem(index)
                    item.setSelected(True)
            else: raise TypeError('parameter type {} is not int or str.'.format(type(index)))

    def copySelectionFrom(self, widget: QWidget) -> None:
        """
        Copy the selection state from another FilesSelectionWidget to this widget.

        Parameters
        ----------
        widget : QWidget
            source FilesSelectionWidget to copy selection from
        """
        if isinstance(widget, FilesSelectionWidget):
            items = widget.selectedItems()
            for item in items:
                # noinspection PyProtectedMember
                row = widget._list.indexOfTopLevelItem(item)
                if row < self._list.topLevelItemCount():
                    self._list.topLevelItem(row).setSelected(True)
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def copySelectionTo(self, widget: QWidget) -> None:
        """
        Copy the selection state from this widget to another FilesSelectionWidget.

        Parameters
        ----------
        widget : QWidget
            target FilesSelectionWidget to copy selection to
        """
        if isinstance(widget, FilesSelectionWidget):
            items = self._list.selectedItems()
            for item in items:
                row = self._list.indexOfTopLevelItem(item)
                # noinspection PyProtectedMember
                if row <  widget._list.topLevelItemCount():
                    # noinspection PyProtectedMember
                    widget._list.topLevelItem(row).setSelected(True)
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def clearSelection(self) -> None:
        """
        Clear the current selection in the list widget.
        """
        self._list.clearSelection()

    def hasSelection(self) -> bool:
        """
        Checks if any file is currently selected in the list.

        Returns
        -------
        bool
            True if at least one item is selected, False otherwise.
        """
        return len(self._list.selectedItems()) > 0

    def setSelectionMode(self, v: int) -> None:
        """
        Set the selection mode of the internal QListWidget.

        Parameters
        ----------
        v : int
            QAbstractItemView.selection mode (e.g., QAbstractItemView.SingleSelection,
            QAbstractItemView.ExtendedSelection).
        """
        if isinstance(v, int):
            if 0 <= v < 5:
                # noinspection PyTypeChecker
                self._list.setSelectionMode(v)
            else: raise ValueError('parameter value {} is not between 0 and 4.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setSelectionModeToSingle(self) -> None:
        """
        Set the selection mode of the list widget to single item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(1)

    def setSelectionModeToContiguous(self) -> None:
        """
        Set the selection mode of the list widget to contiguous item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(4)

    def setSelectionModeToExtended(self) -> None:
        """
        Set the selection mode of the list widget to extended item selection.
        """
        # noinspection PyTypeChecker
        self._list.setSelectionMode(3)

    def getSelectionMode(self) -> int:
        """
        Get the current selection mode of the list widget.

        Returns
        -------
        int
            current selection mode.
        """
        return self._list.selectionMode()

    def getFilenames(self) -> list[str]:
        """
        Get a list of all filenames currently in the widget's list.

        Returns
        -------
        list[str]
            list of absolute file paths, or None if the list is empty.
        """
        filenames = None
        n = self._list.topLevelItemCount()
        if n > 0:
            filenames = list()
            i: cython.int
            for i in range(n):
                filenames.append(self._list.topLevelItem(i).data(0, 256))
        return filenames

    def getSelectedFilenames(self) -> list[str]:
        """
        Get a list of filenames for all currently selected items in the list.

        Returns
        -------
        list[str]
            list of absolute file paths for selected items, or None if no items are selected.
        """
        items = self._list.selectedItems()
        filenames = None
        if len(items) > 0:
            filenames = list()
            for item in items:
                filenames.append(item.data(0, 256))
        return filenames

    def getCheckedFilenames(self) -> list[str]:
        """
        Get a list of filenames for all checked items in the list. If checkboxes are not enabled, it returns all
        filenames.

        Returns
        -------
        list[str]
            list of absolute file paths for checked items.
        """
        if not self._checkbox: return self.getFilenames()
        else:
            r = list()
            i: cython.int
            for i in range(self._list.topLevelItemCount()):
                if self._list.topLevelItem(i).checkState(0) > 0:
                    r.append(self._list.topLevelItem(i).data(0, 256))
            return r

    def getCheckedIndexes(self) -> list[int]:
        """
        Get a list of indexes for all checked items in the list. If checkboxes are not enabled, it returns indexes for
        all items.

        Returns
        -------
        list[int]
            list of integer indexes for checked items.
        """
        if not self._checkbox: return list(range(self._list.topLevelItemCount()))
        else:
            r = list()
            i: cython.int
            for i in range(self._list.topLevelItemCount()):
                if self._list.topLevelItem(i).checkState(0) > 0: r.append(i)
            return r

    def getCheckStateList(self) -> list[bool]:
        """
        Get a list of boolean check states for all items in the list. If checkboxes are not enabled, it returns a list
        of True for all items.

        Returns
        -------
        list[bool]
            list where True indicates a checked item, False an unchecked item.
        """
        if not self._checkbox: return [True] * self._list.topLevelItemCount()
        else:
            r = list()
            i: cython.int
            for i in range(self._list.topLevelItemCount()):
                r.append(self._list.topLevelItem(i).checkState(0) > 0)
            return r

    def filterSisypheVolume(self) -> None:
        """
        Set the filter to allow only PySisyphe volume files (.xvol) and updates the visibility of the 'current volume'
        button based on the presence of a thumbnail toolbar.
        """
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def containsItem(self, v: QTreeWidgetItem) -> bool:
        """
        Check if a QTreeWidgetItem with the same text and data (filename) is already present in the list.

        Parameters
        ----------
        v : QTreeWidgetItem
            QTreeWidgetItem to check for

        Returns
        -------
        bool
            True if the item is found, False otherwise.
        """
        if isinstance(v, QTreeWidgetItem):
            # noinspection PyUnresolvedReferences
            items = self._list.findItems(v.text(0), Qt.MatchExactly, 0)
            if len(items) > 0:
                for item in items:
                    if v.data(0, 256) == item.data(0, 256):
                        return True
            return False
        else: raise TypeError('parameter type {} is not QTreeWidgetItem.'.format(type(v)))

    def getIndexFromItem(self, v: QTreeWidgetItem) -> int:
        """
        Get the row index of a given QTreeWidgetItem in the list.

        Parameters
        ----------
        v : QTreeWidgetItem
            QTreeWidgetItem to find the index for.

        Returns
        -------
        int
            row index of the item.
        """
        if isinstance(v, QTreeWidgetItem):
            return self._list.indexOfTopLevelItem(v)
        else: raise TypeError('parameter type {} is not QTreeWidgetItem.'.format(type(v)))

    # < Revision 03/11/2025
    def getItemFromIndex(self, i: int) -> QTreeWidgetItem:
        """
        Get the QTreeWidgetItem item at a given row index.

        Parameters
        ----------
        i : int
            row index

        Returns
        -------
        QTreeWidgetItem
            item at row index i.
        """
        if isinstance(i, int):
            # return self._list.item(i).data(256)
            return self._list.topLevelItem(i)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))
    # Revision 03/11/2025 >

    def getFilenameFromIndex(self, i: int) -> str:
        """
        Get the filename at a given index.

        Parameters
        ----------
        i : int
            element index

        Returns
        -------
        str
            filename at index i.
        """
        if isinstance(i, int):
            return self._list.topLevelItem(i).data(0, 256)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    # noinspection PyUnboundLocalVariable
    def add(self,
            filenames: str | list[str] = '',
            label: str = '',
            signal: bool = True,
            wait: DialogWait | None = None) -> None:
        """
        Open a file dialog to select one or more files/directories and adds them to the list. Applies all configured
        filters and performs checks (component, identity, FOV, size, modality, etc.) before adding each file. Displays
        a progress dialog for multiple file additions.

        Parameters
        ----------
        filenames : str | list[str] (optional)
            pre-selected filename or directory to add directly. Defaults to an empty string.
        label : str (optional)
            an optional label for the file dialog title. Defaults to an empty string.
        signal : bool (optional)
            If True, emits FieldChanged and FilesSelectionChanged signals upon successful addition. Defaults to True.
        wait : DialogWait | None (optional)
            an optional DialogWait instance to use for progress reporting. If None, a new one is created for multiple
            files. Defaults to None.
        """
        dtag = wait is None
        if label != '': label += ' '
        # < Revision 30/11/2025
        # param = filenames != '' and exists(filenames)
        #    if param:
        #        buff, paramext = splitext(filenames)
        #        paramext = paramext.lower()
        #        filenames = [filenames]
        #    else: paramext = ''
        if isinstance(filenames, str):
            # Extract filepath, filename and ext of parameter if exists
            param = filenames != '' and exists(filenames)
            if param:
                buff, paramext = splitext(filenames)
                paramext = paramext.lower()
                filenames = [filenames]
            else: paramext = ''
        elif isinstance(filenames, list):
            if len(filenames) > 0:
                buff, paramext = splitext(filenames[0])
                paramext = paramext.lower()
                buff = list()
                for filename in filenames:
                    if exists(filename): buff.append(filename)
                filenames = buff
                param = len(filenames) > 0
            else:
                param = False
                paramext = ''
        # Revision 30/11/2025 >
        # Apply filters
        if self._refDir:
            if param:
                # noinspection PyTypeChecker
                directory = split(filenames)[0]
            else:
                directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                             getcwd(), QFileDialog.ShowDirsOnly)
                QApplication.processEvents()
                self.activateWindow()
            if directory:
                directory = abspath(directory)
                chdir(directory)
                directories = [directory]
                sub = glob(join(directory, '**'))
                i: cython.int
                for i in range(len(sub)-1, -1, -1):
                    if not isdir(sub[i]): del sub[i]
                if len(sub) > 0:
                    if messageBox(self,
                                  'Select directory',
                                  'Add subdirectories ?',
                                  icon=QMessageBox.Question,
                                  buttons=QMessageBox.Yes | QMessageBox.No,
                                  default=QMessageBox.No) == QMessageBox.Yes:
                        directories += sub
                for directory in directories:
                    item = QTreeWidgetItem()
                    item.setText(0, directory)
                    item.setData(0, 256, directory)
                    if self._checkbox:
                        # noinspection PyUnresolvedReferences
                        item.setCheckState(0, Qt.Checked)
                    if self.containsItem(item):
                        messageBox(self,
                                   'Select directory',
                                   text='{} is already in the list.'.format(item.text(0)))
                    else:
                        self._list.addTopLevelItem(item)
                        self._initItemParameterWidgets(item)
                        if signal:
                            # noinspection PyUnresolvedReferences
                            self.FieldChanged.emit(self, directory)
                            # noinspection PyUnresolvedReferences
                            self.FilesSelectionChanged.emit(self)
        elif len(self._refExt) > 0:
            # SisypheVolume
            if self._refxvol:
                if not param or paramext != SisypheVolume.getFileExt():
                    filt = 'PySisyphe Volume (*.xvol)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe volume(s)'.format(label),
                                                             getcwd(), filt)
                    QApplication.processEvents()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.open()
                        wait.setInformationText('Add PySisyphe Volumes...')
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheVolume()
                        # < Revision 17/11/2024
                        # load only XML part (attributes)
                        # fast volume loading
                        # try: img.load(filename)
                        try: img.load(filename, binary=False)
                        # Revision 17/11/2024 >
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is not a valid Sisyphe volume file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # First volume is reference
                        if self._list.topLevelItemCount() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    self._refID = self._volume.getID()
                                if self._refSpaceID is not None:
                                    self._refSpaceID = self._volume.getID()
                                if self._refidentity is not None:
                                    self._refidentity = self._volume.getIdentity()
                                if self._refFOV is not None:
                                    self._refFOV = self._volume.getFieldOfView()
                                if self._refSize is not None:
                                    self._refSize = self._volume.getSize()
                                if self._refmodality is not None:
                                    self._refmodality = self._volume.getAcquisition().getModality()
                                if self._refsequence is not None:
                                    self._refsequence = self._volume.getAcquisition().getSequence()
                                if self._refdatatype is not None:
                                    self._refdatatype = self._volume.getDatatype()
                                if self._reforientation is not None:
                                    self._reforientation = self._volume.getOrientationAsString().lower()
                        # Component verification, is single component ?
                        if self._refcomponent == 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c > 1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} is a multi component image.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Component verification, is multi-component ?
                        elif self._refcomponent > 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c == 1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} is a single component image.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same Identity verification
                        if self._refidentity:
                            if img.getIdentity().isNotEqual(self._refidentity):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image identity is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                                wait.hide()
                                txt = '{0} image FOV {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                      'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text=txt.format(basename(filename),
                                                           img.getFieldOfView(),
                                                           self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Same Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image size {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getSize(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ICBM verification
                        if self._refICBM:
                            if not img.acquisition.isICBM152():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image is not in ICBM space.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Displacement field verification
                        if self._refField:
                            if not (img.isFloatDatatype() and
                                    img.getNumberOfComponentsPerPixel() == 3
                                    and img.getAcquisition().isDisplacementField()):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image is not displacement field.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Modality verification
                        if self._refmodality:
                            # < Revision 10/10/2024
                            # multiple modality management
                            # self._refmodality is list and not str as before
                            # if img.getAcquisition().getModality() != self._refmodality:
                            # Revision 10/10/2024 >
                            if img.getAcquisition().getModality() not in self._refmodality:
                                # < Revision 17/11/2024
                                # modality list to str conversion
                                if len(self._refmodality) == 1: refmodality = self._refmodality[0]
                                else: refmodality = ', '.join(str(m) for m in self._refmodality)
                                # Revision 17/11/2024 >
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image modality {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getAcquisition().getModality(),
                                               refmodality))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Sequence verification
                        if self._refsequence:
                            # < Revision 10/10/2024
                            # multiple sequence management
                            # self._refsequence is list and not str as before
                            # if img.getAcquisition().getSequence() != self._refsequence:
                            # Revision 10/10/2024 >
                            if img.getAcquisition().getSequence() not in self._refsequence:
                                # < Revision 17/11/2024
                                # sequence list to str conversion
                                if len(self._refsequence) == 1: refsequence = self._refsequence[0]
                                else: refsequence = ', '.join(str(s) for s in self._refsequence)
                                # Revision 17/11/2024 >
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image sequence {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getAcquisition().getSequence(),
                                               refsequence))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Datatype verification
                        if self._refdatatype:
                            if img.getDatatype() != self._refdatatype:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image datatype {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getDatatype(),
                                               self._refdatatype))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Orientation verification
                        if self._reforientation:
                            if img.getOrientationAsString().lower() != self._reforientation:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image orientation {} is not allowed ({} required).'.format(
                                               basename(filename),
                                               img.getOrientationAsString(),
                                               self._reforientation))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ID verification
                        if self._refSpaceID:
                            if img.getID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Registered verification
                        if self._refID:
                            if img.getID() != self._refID:
                                if self._refID not in img.getTransforms():
                                    wait.hide()
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image is not registered to reference.'.format(
                                                   basename(filename)))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Frame verification
                        if self._refframe:
                            if not img.getAcquisition().getFrame():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image has no frame.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Range verification
                        if self._refRange:
                            r = img.display.getRange()
                            if r[0] < self._refRange[0] or r[1] > self._refRange[1]:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='{} image range is not between {} and {} .'.format(
                                               basename(filename),
                                               self._refRange[0],
                                               self._refRange[1]))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Transform verification
                        # < Revision 04/01/2026
                        if self._reftrf:
                            if not img.hasTransform(self._reftrf):
                                wait.hide()
                                if self._reftrf == 'LEKSELL':
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image has no geometric transformation to the '
                                                    'Leksell\'s stereotactic space.'.format(basename(filename)))
                                else:
                                    messageBox(self,
                                               'PySisyphe volume file selector',
                                               text='{} image has no transform to {} .'.format(
                                                   basename(filename), self._reftrf))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Revision 04/01/2026 >
                        # Item already in list ?
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe volume file selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        # Add item
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            idx = self._list.indexOfTopLevelItem(item)
                            item.setToolTip(0, 'PySisyphe volume index {}\n{}'.format(idx, str(img)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe volume file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheROI
            elif self._refxroi:
                if not param or paramext != SisypheROI.getFileExt():
                    filt = 'PySisyphe ROI (*.xroi)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe ROI(s)'.format(label),
                                                             getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.open()
                        wait.setInformationText('Add PySisyphe ROIs...')
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheROI()
                        try: img.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is not a valid PySisyphe ROI file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # First volume is reference
                        if self._list.topLevelItemCount() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    # noinspection PyUnresolvedReferences
                                    self._refID = self._volume.getReferenceID()
                                if self._refSpaceID is not None:
                                    # noinspection PyUnresolvedReferences
                                    self._refSpaceID = self._volume.getReferenceID()
                                if self._refFOV is not None:
                                    self._refFOV = self._volume.getFieldOfView()
                                if self._refSize is not None:
                                    self._refSize = self._volume.getSize()
                        # Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI size {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getSize(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not img.hasSameFieldOfView(self._refFOV, decimals=1):
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI FOV {} does not match reference {}.'.format(
                                               basename(filename),
                                               img.getFieldOfView(),
                                               self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # ID verification
                        if self._refSpaceID:
                            if img.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI ID does not match reference.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Registered verification
                        if self._refID:
                            if img.getReferenceID() != self._refID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} ROI is not registered to reference.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe ROI file selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        # Add item
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            idx = self._list.indexOfTopLevelItem(item)
                            item.setToolTip(0, 'PySisyphe ROI index {}\n{}'.format(idx, str(img)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe ROI file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheMesh
            elif self._refxmesh:
                if not param or paramext != SisypheMesh.getFileExt():
                    filt = SisypheMesh.getFilterExt()
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe mesh'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe mesh(es)...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        mesh = SisypheMesh()
                        try: mesh.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} is not a valid Sisyphe mesh file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if mesh.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} mesh ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe mesh file selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        # Add item
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            idx = self._list.indexOfTopLevelItem(item)
                            item.setToolTip(0, 'PySisyphe mesh index {}\n{}'.format(idx, str(mesh)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe mesh file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # SisypheStreamlines
            elif self._refxtracts:
                if not param or paramext != SisypheStreamlines.getFileExt():
                    filt = SisypheStreamlines.getFilterExt()
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe streamlines'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe streamlines...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        sl = SisypheStreamlines()
                        try: sl.load(filename)
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is not a valid Sisyphe streamlines file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if sl.getReferenceID() != self._refSpaceID:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} streamlines ID is not allowed.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # FOV verification
                        if self._refFOV:
                            # < Revision 19/09/2024
                            # if img.getFieldOfView() != self._refFOV:
                            # Revision 19/09/2024 >
                            if not sl.getDWIFOV(decimals=1) != self._refFOV:
                                wait.hide()
                                txt = '{0} streamlines field of view {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                      'does not match reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text=txt.format(basename(filename), sl.getDWIFOV, self._refFOV))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Size verification
                        if self._refSize:
                            if sl.getDWIShape() != self._refSize:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} size {} does not match reference {}.'.format(
                                               basename(filename),
                                               sl.getDWIShape(),
                                               self._refSize))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Whole brain tractogram verification
                        if self._refwhole:
                            if not sl.isWholeBrainTractogram():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is not a whole brain tractogram.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Not whole brain tractogram verification
                        if self._refnotwhole:
                            if sl.isWholeBrainTractogram():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is a whole brain tractogram.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Centroid verification
                        if self._refcentroid:
                            if not sl.isCentroid():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is not a centroid streamline.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Not centroid vérification
                        if self._refnotcentroid:
                            if sl.isCentroid():
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} is a centroid streamline.'.format(basename(filename)))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        # Add item
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            idx = self._list.indexOfTopLevelItem(item)
                            item.setToolTip(0, 'PySisyphe streamlines index {}\n{}'.format(idx, str(sl)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe streamlines file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Tools, HandleWidget, LineWidget, ToolCollectionWidget
            # < Revision 13/02/2026
            elif self._refxtools:
                if not param or paramext not in (HandleWidget.getFileExt(),
                                                 LineWidget.getFileExt(),
                                                 ToolWidgetCollection.getFileExt()):
                    # < Revision 20/02/2026
                    filt = ';;'.join([ToolWidgetCollection.getFilterExt(),
                                      HandleWidget.getFilterExt(),
                                      LineWidget.getFilterExt()])
                    # Revision 20/02/2026 >
                    # < Revision 17/02/2026
                    # filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe tools', getcwd(), filt)
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe tools'.format(label),
                                                             getcwd(), filt)
                    # Revision 17/02/2026 >
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe tools...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        ext = splitext(filename)[1]
                        try:
                            if ext == HandleWidget.getFileExt():
                                tool = HandleWidget('')
                                tool.load(filename)
                            elif ext == LineWidget.getFileExt():
                                tool = LineWidget('')
                                tool.load(filename)
                            elif ext == ToolWidgetCollection.getFileExt():
                                tool = ToolWidgetCollection()
                                tool.load(filename)
                            else:
                                if self._stop: break
                                else: continue
                        except:
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} is not a valid Sisyphe tools file.'.format(basename(filename)))
                            if self._stop: break
                            else:
                                wait.show()
                                continue
                        # ID verification
                        if self._refSpaceID:
                            if isinstance(tool, ToolWidgetCollection):
                                if tool.getReferenceID() != self._refSpaceID:
                                    wait.hide()
                                    messageBox(self,
                                               'PySisyphe tools file selector',
                                               text='{} tools ID is not allowed.'.format(basename(filename)))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'PySisyphe tools file selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        # Add item
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            idx = self._list.indexOfTopLevelItem(item)
                            item.setToolTip(0, 'PySisyphe tools index {}\n{}'.format(idx, str(tool)))
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'PySisyphe tools file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Revision 13/02/2026 >
            # DICOM
            elif self._refdicom:
                # < Revision 13/02/2026
                #if not param or paramext not in getDicomExt().append(''):
                if not param or paramext not in getDicomExt():
                # Revision 13/02/2026 >
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select DICOM file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add DICOM files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        if isDicom(filename):
                            # Prefix verification
                            if self._refprefix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[:len(self._refprefix)] == self._refprefix:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not have {} prefix.'.format(basename(filename),
                                                                                         self._refprefix))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            # Suffix verification
                            if self._refsuffix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[-len(self._refsuffix):] == self._refsuffix:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not have {} suffix.'.format(basename(filename),
                                                                                         self._refsuffix))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            # Filename contains verification
                            if self._refcontains:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if bname.find(self._refcontains) > -1:
                                    wait.hide()
                                    messageBox(self,
                                               'DICOM file selector',
                                               text='{} does not contains {} string.'.format(basename(filename),
                                                                                             self._refcontains))
                                    if self._stop: break
                                    else:
                                        wait.show()
                                        continue
                            path, name = split(filename)
                            item = QTreeWidgetItem()
                            item.setText(0, name)
                            item.setData(0,256, filename)
                            if self._checkbox:
                                # noinspection PyUnresolvedReferences
                                item.setCheckState(0, Qt.Checked)
                            if self.containsItem(item):
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} is already in the list.'.format(item.text(0)))
                                wait.show()
                            else:
                                self._list.addTopLevelItem(item)
                                self._initItemParameterWidgets(item)
                                if signal:
                                    # noinspection PyUnresolvedReferences
                                    self.FieldChanged.emit(self, filename)
                                    # noinspection PyUnresolvedReferences
                                    self.FilesSelectionChanged.emit(self)
                        else:
                            wait.hide()
                            messageBox(self,
                                       'DICOM file selector',
                                       text='{} is not a valid dicom file.'.format(self._name))
                            wait.show()
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'DICOM file selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # Other file
            else:
                if not param or paramext not in self._refExt:
                    filt = 'Files ('
                    for ext in self._refExt:
                        filt += '*{} '.format(ext)
                    filt = filt.rstrip() + ')'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'File selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'File selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
        else:
            if not param:
                filt = 'All files (*.*)'
                filenames = QFileDialog.getOpenFileNames(self, 'Select file', getcwd(), filt)
                QApplication.processEvents()
                self.activateWindow()
                filenames = filenames[0]
                if len(filenames) > 0 and self._list.topLevelItemCount() < self._refCount:
                    chdir(dirname(filenames[0]))
                    if wait is None:
                        wait = DialogWait(progress=True,
                                          progressmin=0,
                                          progressmax=len(filenames),
                                          cancel=True,
                                          parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        filename = abspath(filename)
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} prefix.'.format(basename(filename),
                                                                                     self._refprefix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not have {} suffix.'.format(basename(filename),
                                                                                     self._refsuffix))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                wait.hide()
                                messageBox(self,
                                           'DICOM file selector',
                                           text='{} does not contains {} string.'.format(basename(filename),
                                                                                         self._refcontains))
                                if self._stop: break
                                else:
                                    wait.show()
                                    continue
                        path, name = split(filename)
                        item = QTreeWidgetItem()
                        item.setText(0, name)
                        item.setData(0,256, filename)
                        if self._checkbox:
                            # noinspection PyUnresolvedReferences
                            item.setCheckState(0, Qt.Checked)
                        if self.containsItem(item):
                            wait.hide()
                            messageBox(self,
                                       'File selector',
                                       text='{} is already in the list.'.format(item.text(0)))
                            wait.show()
                        else:
                            self._list.addTopLevelItem(item)
                            self._initItemParameterWidgets(item)
                            if signal:
                                # noinspection PyUnresolvedReferences
                                self.FieldChanged.emit(self, filename)
                                # noinspection PyUnresolvedReferences
                                self.FilesSelectionChanged.emit(self)
                        if self._list.topLevelItemCount() == self._refCount:
                            wait.hide()
                            if self._countWarning:
                                messageBox(self,
                                           'File selector',
                                           text='Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()

    def clearItem(self, i: int, signal: bool = True) -> None:
        """
        Remove a file from the list at the specified index.

        Parameters
        ----------
        i : int
            index of the item to remove
        signal : bool (optional)
            If True, emits FieldCleared signal. Defaults to True.
        """
        if isinstance(i, int):
            if i < self._list.topLevelItemCount():
                self._list.takeTopLevelItem(i)
                self._add.setEnabled(True)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.FieldCleared.emit(self, [i])
            else: raise ValueError('parameter index is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    def clearLastItem(self, signal: bool = True) -> None:
        """
        Remove the last file from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared signal. Defaults to True.
        """
        n = self._list.topLevelItemCount()
        if n > 0: self._list.takeTopLevelItem(n - 1)
        self._add.setEnabled(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, [n-1])

    def clear(self, signal: bool = True) -> None:
        """
        Remove all currently selected files from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared and FilesSelectionWidgetCleared signals. Defaults to True.
        """
        rows = list()
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            for item in selecteditems:
                row = self._list.indexOfTopLevelItem(item)
                rows.append(row)
                self._list.takeTopLevelItem(row)
            self._add.setEnabled(True)
        if self._list.topLevelItemCount() == 0:
            if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, rows)
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetCleared.emit(self)

    def clearall(self, signal: bool = True) -> None:
        """
        Remove all files from the list.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits FieldCleared and FilesSelectionWidgetCleared signals. Defaults to True.
        """
        rows = list(range(self._list.topLevelItemCount()))
        self._list.clear()
        self._add.setEnabled(True)
        if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, rows)
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetCleared.emit(self)

    def isEmpty(self) -> bool:
        """
        Check if the list of files is empty.

        Returns
        -------
        bool
            True if the list contains no files, False otherwise.
        """
        return self._list.topLevelItemCount() == 0

    def filenamesCount(self) -> int:
        """
        Get the number of files currently in the list.

        Returns
        -------
        int
            count of files.
        """
        return self._list.topLevelItemCount()

    # Qt Drop events

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
        """
        Handles drag enter events, accepting drops if the mime data contains text (e.g., file paths).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event : QDragEnterEvent
            Qt drag enter event.
        """
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """
        Handles drop events, attempting to open the dropped file(s).
        This is the method used to manage the drag-and-drop of files from Finder on the macOS platform or File Explorer
        on the Windows platform.

        Parameters
        ----------
        event ! QDropEvent
            Qt drop event.
        """
        if event.mimeData().hasText():
            event.accept()
            files = event.mimeData().text().split('\n')
            for file in files:
                if file != '': self.add(file[7:])
# Revision 26/03/2026 >


class MultiExtFilesSelectionWidget(FilesSelectionWidget):
    """
    MultiExtFilesSelectionWidget class

    Description
    ~~~~~~~~~~~

    FilesSelectionWidget to select multiple file types.

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FilesSelectionWidget -> MultiExtFilesSelectionWidget

    Last revision: 20/10/2025
    """

    # Public methods

    def add(self,
            filenames: str = '',
            label: str = '',
            signal: str = True,
            wait: DialogWait | None = None):
        """
        Opens a file dialog to select one or more files, specifically designed for multiple Sisyphe-specific file types
        (e.g., .xvol, .xroi, .xmesh, .xtracts). It dynamically constructs the file filter based on the active
        Sisyphe-specific extension filters.

        Parameters
        ~~~~~~~~~~
        filenames : str (optional)
            pre-selected filename to add directly. Defaults to an empty string.
        label : str (optional)
            Aan optional label for the file dialog title. Defaults to an empty string.
        signal : bool (optional)
            if True, emits FieldChanged and FilesSelectionChanged signals upon successful addition. Defaults to True.
        wait : DialogWait | None (optional)
            an optional DialogWait instance to use for progress reporting. If None, a new one is created for multiple
            files. Defaults to None.
        """
        exts = list()
        if self._refxvol: exts.append('*' + SisypheVolume.getFileExt())
        if self._refxroi: exts.append('*' + SisypheROI.getFileExt())
        if self._refxmesh: exts.append('*' + SisypheMesh.getFileExt())
        if self._refxtracts: exts.append('*' + SisypheStreamlines.getFileExt())
        if len(exts) > 0:
            filt = 'PySisyphe files ({})'.format(' '.join(exts))
            filenames = QFileDialog.getOpenFileNames(self, 'Select PySisyphe file(s)',
                                                     getcwd(), filt)
            QApplication.processEvents()
            filenames = filenames[0]
            if len(filenames) > 0 and self._list.count() < self._refCount:
                chdir(dirname(filenames[0]))
                if wait is None:
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True)
                if len(filenames) > 1:
                    wait.setInformationText('Add file(s)...')
                    wait.open()
                for filename in filenames:
                    filename = abspath(filename)
                    ext = splitext(filename)[1]
                    wait.incCurrentProgressValue()
                    wait.setInformationText('Add {}...'.format(basename(filename)))
                    rxvol = self._refxvol
                    rxroi = self._refxroi
                    rxmesh = self._refxmesh
                    rxtracts = self._refxtracts
                    rdir = self._refDir
                    rdicom = self._refdicom
                    if self._refxvol and ext == SisypheVolume.getFileExt():
                        self._refxroi = self._refxmesh = self._refxtracts = self._refdicom = self._refDir = False
                        super().add(filename, wait=wait)
                    elif self._refxroi and ext == SisypheROI.getFileExt():
                        self._refxvol = self._refxmesh = self._refxtracts = self._refdicom = self._refDir = False
                        super().add(filename, wait=wait)
                    elif self._refxmesh and ext == SisypheMesh.getFileExt():
                        self._refxvol = self._refxroi = self._refxtracts = self._refdicom = self._refDir = False
                        super().add(filename, wait=wait)
                    elif self._refxtracts and ext == SisypheStreamlines.getFileExt():
                        self._refxvol = self._refxroi = self._refxmesh = self._refdicom = self._refDir = False
                        super().add(filename, wait=wait)
                    elif self._refdicom:
                        self._refxvol = self._refxroi = self._refxmesh = self._refxtracts = self._refDir = False
                        super().add(filename, wait=wait)
                    elif self._refDir:
                        self._refxvol = self._refxroi = self._refxmesh = self._refxtracts = self._refdicom = False
                        super().add(filename, wait=wait)
                    self._refxvol = rxvol
                    self._refxroi = rxroi
                    self._refxmesh = rxmesh
                    self._refxtracts = rxtracts
                    self._refDir = rdir
                    self._refdicom = rdicom
                    if wait.getStopped():
                        wait.close()
                        return


class SynchronizedFilesSelectionWidget(QWidget):
    """
    SynchronizedFileSelectionWidget class

    Description
    ~~~~~~~~~~~

    A composite widget that manages multiple synchronized FileSelectionWidget and/or FilesSelectionWidget widgets.
    It ensures consistency across linked widgets, for example, by checking if selected volumes have matching
    Field of View (FOV).

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SynchronizedFileSelectionWidget

    Last revision: 09/04/2026
    """

    # Special method

    def __init__(self,
                 single: list[str] | tuple[str, ...] | None,
                 multiple: list[str] | tuple[str, ...] | None,
                 maxcount: int = 100,
                 params: bool = False,
                 parent: QWidget | None = None) -> None:
        """
        SynchronizedFilesSelectionWidget instance constructor.

        Parameters
        ----------
        single : list[str] | tuple[str, ...] | None
            titles of single file selection widgets.
        multiple : list[str] | tuple[str, ...] | None
            titles of multiple file selection widgets.
        maxcount : int (optional)
            maximum number of files allowed in the list (default 100).
        params : bool (optional)
            If false, multiple widgets are FileSelectionWidget or FilesSelectionWithParametersWidget, otherwise.
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._single = dict()
        self._multiple = dict()
        self._FOV = list()
        if single is not None and len(single) > 0:
            for label in single:
                flist = FileSelectionWidget(parent=parent)
                flist.filterSisypheVolume()
                flist.setTextLabel(label)
                flist.setLabelVisibility(True)
                # noinspection PyUnresolvedReferences
                flist.FieldCleared.connect(self._ListCleared)
                # noinspection PyUnresolvedReferences
                flist.FieldChanged.connect(self._ListChanged)
                self._single[label] = flist
                self._layout.addWidget(flist)
        elif multiple is not None and len(multiple) > 0:
            for label in multiple:
                # < Revision 09/04/2026
                # flist = FilesSelectionWidget(parent=parent)
                if params: flist = FilesSelectionWithParametersWidget(parent=parent)
                else: flist = FilesSelectionWidget(parent=parent)
                # Revision 09/04/2026 >
                flist.setMaximumNumberOfFiles(maxcount)
                flist.hideRemoveAllButton()
                flist.filterSisypheVolume()
                flist.setTextLabel(label)
                flist.setLabelVisibility(True)
                # noinspection PyUnresolvedReferences
                flist.FieldCleared.connect(self._ListCleared)
                # noinspection PyUnresolvedReferences
                flist.FieldChanged.connect(self._ListChanged)
                self._multiple[label] = flist
                self._layout.addWidget(flist)

    """
    Private attributes

    _lists      list[FileSelectionWidget]
    """

    def __getitem__(self, key: str) -> QWidget:
        if isinstance(key, str):
            if key in self._single: return self._single[key]
            if key in self._multiple: return self._multiple[key]
            raise ValueError('Invalid key parameter.')
        else: raise TypeError('key type {} is not str.'.format(type(key)))

    # Private method

    def _ListChanged(self, widget: QWidget, filename: str) -> None:
        """
        Slot connected to the FieldChanged signal of contained file selection widgets.
        It checks for Field of View (FOV) consistency among selected volumes.
        If a discrepancy is found, the newly added file is cleared.

        Parameters
        ----------
        widget : QWidget:
            file selection widget that emitted the signal.
        filename : str
            filename that was added/changed.
        """
        if filename != '':
            fov = list(XmlVolume(filename).getFOV())
            if isinstance(widget, FileSelectionWidget):
                if len(self._FOV) == 0:
                    self._FOV = [fov]
                else:
                    if self._FOV[0] != fov:
                        widget.clear(signal=False)
                        messageBox(self,
                                   'PySisyphe volume file selector',
                                   'FOV discrepancy between file selectors.')
            else:
                n = widget.filenamesCount()
                if n - len(self._FOV) == 1:
                    self._FOV.append(fov)
                elif n == len(self._FOV):
                    if self._FOV[n-1] != fov:
                        widget.clearLastItem(signal=False)
                        messageBox(self,
                                   'PySisyphe volume file selector',
                                   'FOV discrepancy between file selectors.')

    # noinspection PyUnusedLocal
    def _ListCleared(self, widget: QWidget) -> None:
        """
        Slot connected to the FieldCleared signal of contained file selection widgets.
        If all widgets are empty, it clears the stored FOV reference.

        Parameters
        ----------
        widget : QWidget
            file selection widget that emitted the signal.
        """
        if self.isEmpty(): self._FOV = list()

    # Public methods

    # < Revision 09/10/2024
    # add setToolbarThumbnail method
    def setToolbarThumbnail(self, t: ToolBarThumbnail) -> None:
        """
        Set the ToolBarThumbnail widget for accessing volumes and makes the 'current volume' button visible if a
        thumbnail toolbar is provided.

        Parameters
        ----------
        t : ToolBarThumbnail
            ToolBarThumbnail instance.
        """
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(t, ToolBarThumbnail):
            if self._single is not None:
                for k in self._single:
                    self._single[k].setToolbarThumbnail(t)
            if self._multiple is not None:
                for k in self._multiple:
                    self._multiple[k].setToolbarThumbnail(t)
        else: raise TypeError('parameter type {} is not toolBarThumbnail.'.format(type(t)))
    # Revision 09/10/2024 >

    # < Revision 09/10/2024
    # add getToolbarThumbnail method
    def getToolbarThumbnail(self) -> ToolBarThumbnail:
        """
        Get the associated ToolBarThumbnail widget for accessing volumes with the 'current volume' button.

        Returns
        -------
        ToolBarThumbnail
            Associated ToolBarThumbnail widget, or None if not set.
        """
        if self._single is not None:
            k0 = list(self._single.keys())[0]
            return self._single[k0].getToolbarThumbnail()
        if self._multiple is not None:
            k0 = list(self._multiple.keys())[0]
            return self._multiple[k0].getToolbarThumbnail()
        raise AttributeError('No single or multiple file selection widget.')
    # Revision 09/10/2024 >

    # < Revision 09/10/2024
    # add hasToolbarThumbnail method
    def hasToolbarThumbnail(self) -> bool:
        """
        Check if a ToolBarThumbnail widget is defined.

        Returns
        -------
        bool
            True if a ToolBarThumbnail is set, False otherwise.
        """
        if self._single is not None:
            k0 = list(self._single.keys())[0]
            return self._single[k0].hasToolbarThumbnail()
        if self._multiple is not None:
            k0 = list(self._multiple.keys())[0]
            return self._multiple[k0].hasToolbarThumbnail()
        raise AttributeError('No single or multiple file selection widget.')
    # Revision 09/10/2024 >

    def getGetNumberOfLists(self) -> int:
        """
        Get the total number of single (FileSelectionWidget) and multiple file selection widgets (FilesSelectionWidget)
        that are managed by this synchronized widget.

        Returns
        -------
        int
            total count of file selection widgets.
        """
        return len(self._single) + len(self._muliple)

    def getTitles(self) -> dict[str, list[str]]:
        """
        Get a dictionary containing lists of titles for both single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Returns
        -------
        dict[str, list[str]]
            dictionary with 'single' and 'multiple' keys, each mapping to a list of widget titles.
        """
        r = dict()
        r['single'] = list(self._single.keys())
        r['multiple'] = list(self._multiple.keys())
        return r

    def getSingleListTitles(self) -> list[str]:
        """
        Get a list of titles for all single file selection widgets (FileSelectionWidget).

        Returns
        -------
        list[str]
            list of titles.
        """
        return list(self._single.keys())

    def getMultipleListTitles(self) -> list[str]:
        """
        Get a list of titles for all multiple file selection widgets (FilesSelectionWidget).

        Returns
        -------
        list[str]
            list of titles.
        """
        return list(self._multiple.keys())

    def setSisypheVolumeFilters(self, filters: dict[str, list[bool] | None]) -> None:
        """
        Set PySisyphe volume (.xvol) filters to the contained single and multiple file selection widgets based on the
        provided filter configuration.

        Parameters
        ----------
        filters : dict[str, dict[str, list[bool] | None]

            - dictionary specifying which widgets should filter for SisypheVolumes.
            - expected format: {'single': list[bool] | None, 'multiple': list[bool] | None}
        """
        i: cython.int
        if len(self._single) > 0:
            if 'single' in filters:
                flt = filters['single']
                if isinstance(flt, (list, tuple)):
                    if len(flt) == len(self._single):
                        for i, (_, flist) in enumerate(self._single.items()):
                            if flt[i]: flist.filterSisypheVolume()
                    else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
        if len(self._multiple) > 0:
            if 'multiple' in filters:
                flt = filters['multiple']
                if isinstance(flt, (list, tuple)):
                    if len(flt) == len(self._multiple):
                        for i, (_, flist) in enumerate(self._multiple.items()):
                            if flt[i]: flist.filterSisypheVolume()
                    else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def setSequenceFilters(self, filters: dict[str, list[str] | None]) -> None:
        """
        Set sequence filters to the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        filters : dict[str, dict[str, list[str] | str | None]

            - dictionary specifying sequence filters for single and multiple widgets.
            - expected format: {'single': list[str] | None, 'multiple': list[str] | None}
        """
        i: cython.int
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                if flt[i] is not None: flist.filterSameSequence(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                if flt[i] is not None: flist.filterSameSequence(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getSequenceFilters(self) -> dict[str, dict[str, list[str] | str | None]]:
        """
        Get the sequence filters currently applied to the contained widgets.

        Returns
        -------
        dict[str, dict[str, list[str] | str | None]]
            dictionary containing sequence filters for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for _, flist in self._single.items():
                r1[flist.flist.getLabel()] = flist.getSequenceFilter()
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                r2[flist.flist.getLabel()] = flist.getSequenceFilter()
        r['single'] = r1
        r['multiple'] = r2
        return r

    def setModalityFilters(self, filters: dict[str, list[str] | None]) -> None:
        """
        Set modality filters to the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        filters : dict[str, list[str] | None]

            - dictionary specifying sequence filters for single and multiple widgets.
            - expected format: {'single': list[str] | None, 'multiple': list[str] | None}
        """
        i: cython.int
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                if flt[i] is not None: flist.filterSameModality(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                if flt[i] is not None: flist.filterSameModality(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getModalityFilters(self) -> dict[str, dict[str, list[str] | str | None]]:
        """
        Get the modality filters currently applied to the contained widgets.

        Returns
        -------
        dict[str, dict[str, list[str] | str | None]]
            dictionary containing modality filters for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for _, flist in self._single.items():
                r1[flist.getLabel()] = flist.getModalityFilter()
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                r2[flist.getLabel()] = flist.getModalityFilter()
        r['single'] = r1
        r['multiple'] = r2
        return r

    def setSuffixFilters(self, filters: dict[str, list[str] | None]) -> None:
        """
        Set suffix filters to the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        filters : dict[str, list[str] | None]

            - dictionary specifying suffix filters for single and multiple widgets.
            - expected format: {'single': list[str] | None, 'multiple': list[str] | None}
        """
        i: cython.int
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                if flt[i] is not None: flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                if flt[i] is not None: flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getSuffixFilters(self) -> dict[str, dict[str, str | None]]:
        """
        Get the suffix filters currently applied to the contained widgets.

        Returns
        -------
        dict[str, dict[str, list[str] | str | None]]
            dictionary containing suffix filters for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for _, flist in self._single.items():
                r1[flist.getLabel()] = flist.getSuffixFilter()
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                r2[flist.getLabel()] = flist.getSuffixFilter()
        r['single'] = r1
        r['multiple'] = r2
        return r

    def setPrefixFilters(self, filters: dict[str, list[str] | None]) -> None:
        """
        Set prefix filters to the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        filters : dict[str, list[str] | None]

            - dictionary specifying prefix filters for single and multiple widgets.
            - expected format: {'single': list[str], 'multiple': list[str] | None}
        """
        i: cython.int
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                if flt[i] is not None: flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                if flt[i] is not None: flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getPrefixFilters(self) -> dict[str, dict[str, str | None]]:
        """
        Get the prefix filters currently applied to the contained widgets.

        Returns
        -------
        dict[str, dict[str, list[str] | str | None]]
            dictionary containing prefix filters for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for _, flist in self._single.items():
                r1[flist.getLabel()] = flist.getPrefixFilter()
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                r2[flist.getLabel()] = flist.getPrefixFilter()
        r['single'] = r1
        r['multiple'] = r2
        return r

    def setContainsStringFilters(self, filters: dict[str, list[str] | None]) -> None:
        """
        Set filename substring filters to the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        filters : dict[str, list[str] | None]

            - dictionary specifying filename substring filters for single and multiple widgets.
            - expected format: {'single': list[str] | None, 'multiple': list[str] | None}
        """
        i: cython.int
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                if flt[i] is not None: flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                if flt[i] is not None: flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getContainsStringFilters(self) -> dict[str, dict[str, str | None]]:
        """
        Get the filename substring filters currently applied to the contained widgets.

        Returns
        -------
        dict[str, dict[str, list[str] | str | None]]
            dictionary containing filename substring filters for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for _, flist in self._single.items():
                r1[flist.getLabel()] = flist.getFilenameContainsFilter()
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                r2[flist.getLabel()] = flist.getFilenameContainsFilter()
        r['single'] = r1
        r['multiple'] = r2
        return r

    # < Revision 10/10/2024
    # add getSelectionWidget method
    def getSelectionWidget(self, label: str) -> QWidget:
        """
        Get a specific FileSelectionWidget or FilesSelectionWidget instance by its label.

        Parameters
        ----------
        label : str
            label of the desired file selection widget.

        Returns
        -------
        QWidget
            FileSelectionWidget or FilesSelectionWidget instance.
        """
        if self._single is not None:
            if label in self._single: return self._single[label]
        if self._multiple is not None:
            if label in self._multiple: return self._multiple[label]
        raise AttributeError('No single or multiple file selection widget.')
    # Revision 10/10/2024 >

    # < Revision 23/10/2024
    # add getSelectionWidget method
    def getSelectionWidgets(self) -> tuple[QWidget, ...]:
        """
        Get a tuple of all contained FileSelectionWidget and FilesSelectionWidget instances.

        Returns
        -------
        tuple[QWidget, ...]
            tuple containing all managed file selection widgets.
        """
        r = list()
        if self._single is not None:
            for label in self._single:
                r.append(self._single[label])
        if self._multiple is not None:
            for label in self._multiple:
                r.append(self._multiple[label])
        return tuple(r)
    # Revision 23/10/2024 >

    def getFilenames(self) -> dict[str, dict[str, str | list[str]]]:
        """
        Get a dictionary of all selected filenames from single (FileSelectionWidget) and multiple selection
        (FilesSelectionWidget) widgets, organized by their labels.

        Returns
        -------
        dict[str, dict[str, str | list[str]]]
            dictionary with 'single' and 'multiple' keys, each mapping to a dictionary of widget labels and their
            filenames.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for label, flist in self._single.items():
                r1[label] = [flist.getFilename()]
        if len(self._multiple) > 0:
            for label, flist in self._multiple.items():
                r2[label] = flist.getFilenames()
        r['single'] = r1
        r['multiple'] = r2
        return r

    def setFilenames(self, filenames: dict[str, dict[str, str | list[str]]]) -> None:
        """
        Set the filenames for the contained single (FileSelectionWidget) and multiple selection (FilesSelectionWidget)
        widgets.

        Parameters
        ----------
        filenames : dict[str, dict[str, str | list[str]]]

            - dictionary specifying filenames to set.
            - expected format: {'single': {label: filename_str}, 'multiple': {label: filename_str | list[filename_str]}}
        """
        if isinstance(filenames, dict):
            if 'single' in filenames:
                for label, filename in filenames['single'].items():
                    if isinstance(filename, list): filename = filename[0]
                    self._single[label].open(filename)
            if 'multiple' in filenames:
                for label, filename in filenames['multiple'].items():
                    if isinstance(filename, str): filename = [filename]
                    for file in filename: self._multiple[label].add(file)
        else: raise TypeError('parameter type {} is not dict.'.format(type(filenames)))

    # < Revision 22/10/2024
    # add setAvailability method
    def setAvailability(self, flags: dict[str, dict[str, bool]]) -> None:
        """
        Set the visibility (availability) of the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        flags : dict[str, dict[str, bool]]:

            - dictionary specifying visibility flags for widgets.
            - expected format: {'single': {label: bool}, 'multiple': {label: bool}}
        """
        if 'single' in flags:
            if len(flags['single']) > 0:
                for label, flag in flags['single'].items():
                    self._single[label].setVisible(flag)
        if 'multiple' in flags:
            if len(flags['multiple']) > 0:
                for label, flag in flags['multiple'].items():
                    self._multiple[label].setVisible(flag)
    # Revision 22/10/2024 >

    # < Revision 22/10/2024
    # add getAvailability method
    def getAvailability(self) -> dict[str, dict[str, bool]]:
        """
        Get the visibility (availability) state of the contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Returns
        -------
        dict[str, dict[str, bool]]
            dictionary containing visibility states for single and multiple widgets, mapped by their labels.
        """
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._single) > 0:
            for label in self._single:
                r1[label] = self._single[label].isVisible()
        if len(self._multiple) > 0:
            for label in self._multiple:
                r2[label] = self._multiple[label].isVisible()
        r['single'] = r1
        r['multiple'] = r2
        return r
    # Revision 22/10/2024 >

    def isReady(self) -> bool:
        """
        Check if the synchronized file selection widget is in a "ready" state. This means all *visible* single
        selection widgets (FileSelectionWidget) are not empty, and all *visible* multiple selection widgets
        (FileSelectionWidgets) have the same number of files.

        Returns
        -------
        bool
            True if the widget is ready, False otherwise.
        """
        if self.isEmpty(): return False
        else:
            if len(self._single) > 0:
                for _, flist in self._single.items():
                    # < revision 20/10/2024
                    # add visibility testing
                    # if not visible, widget is unavailable and not tested
                    # Returns ready if all available widgets are not empty
                    if flist.isVisible():
                        if flist.isEmpty(): return False
                    # revision 20/10/2024 >
            if len(self._multiple) > 0:
                n = 0
                for _, flist in self._multiple.items():
                    if n == 0: n = flist.filenamesCount()
                    else:
                        # < revision 20/10/2024
                        # add visibility testing
                        # if not visible, widget is unavailable and not tested
                        # Returns ready if all available widgets have the same number of files
                        if flist.isVisible():
                            if flist.filenamesCount() != n:
                                return False
                        # revision 20/10/2024 >
        return True

    def isEmpty(self) -> bool:
        """
        Check if all contained file selection widgets (both single and multiple) are empty.

        Returns
        -------
        bool
            True if all widgets are empty, False otherwise.
        """
        return self.isSingleEmpy() and self.isMultipleEmpty()

    def isSingleEmpy(self) -> bool:
        """
        Check if all single file selection widgets (FileSelectionWidget) are empty.

        Returns
        -------
        bool
            True if all single selection widgets are empty, False otherwise.
        """
        if len(self._single) > 0:
            for _, flist in self._single.items():
                if not flist.isEmpty(): return False
        return True

    def isMultipleEmpty(self) -> bool:
        """
        Check if all multiple file selection widgets (FilesSelectionWidget) are empty.

        Returns
        -------
        bool
            True if all multiple selection widgets are empty, False otherwise.
        """
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                if not flist.isEmpty(): return False
        return True

    # < Revision 09/10/2024
    # add hasToolbarThumbnail method
    def clearall(self, signal: bool = True) -> None:
        """
        Clear all files from all contained single (FileSelectionWidget) and multiple file selection
        (FilesSelectionWidget) widgets.

        Parameters
        ----------
        signal : bool (optional)
            if True, emits clear signals from the child widgets. Defaults to True.
        """
        if self._single is not None:
            for k in self._single:
                self._single[k].clear(signal)
        if self._multiple is not None:
            for k in self._multiple:
                self._multiple[k].clearall(signal)
    # Revision 09/10/2024 >
