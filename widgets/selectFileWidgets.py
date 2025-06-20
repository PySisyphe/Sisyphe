"""
External packages/modules
-------------------------

    - darkdetect, OS Dark Mode detection, https://github.com/albertosottile/darkdetect
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

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

from glob import glob

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
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
from Sisyphe.core.sisypheXml import XmlVolume
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import IconLabel

__all__ = ['SelectionFilter',
           'FileSelectionWidget',
           'FilesSelectionWidget',
           'MultiExtFilesSelectionWidget',
           'SynchronizedFilesSelectionWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SelectionFilter, QWidget  -> FileSelectionWidget
                                          -> FilesSelectionWidget
                                          -> FilesSelectionWidget -> MultiExtFilesSelectionWidget
    - QWidget ->  SynchronizedFileSelectionWidget
              ->  SynchronizedFilesSelectionWidget
"""


class SelectionFilter(object):
    """
    SelectionFilter class

    Description
    ~~~~~~~~~~~

    Base class for file selection widgets (FileSelectionWidget & FilesSelectionWidget).
    Filter management (directory, file extension, DICOM, Nifti, Minc, Nrrd, Vtk, numpy, SisypheVolume, SisypheROI,
    identity fields, ID, template ICBM152, FOV, size, modality, sequence, datatype, single component, multi component,
    orientation, scalar range, frame, filename prefix, filename suffix, str in filename, registered to a reference file)

    Inheritance
    ~~~~~~~~~~~

    object -> SelectionFilter

    Last Revision: 15/04/2025
    """

    # Class methods

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

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
    """

    def __init__(self):
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

    # Public method

    def getFilename(self):
        if self._refDir: return self._path
        else: return join(self._path, self._name)

    def getPath(self):
        return self._path

    def getBasename(self):
        return self._name

    def setReferenceVolume(self, v):
        if isinstance(v, SisypheVolume):
            self._volume = v

    def getReferenceVolume(self):
        return self._volume

    def setReferenceVolumeToFirst(self):
        self._reftofirst = True

    def isReferenceVolumeToFirst(self):
        return self._reftofirst

    def setToolbarThumbnail(self, t):
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(t, ToolBarThumbnail): self._thumbnail = t
        else: raise TypeError('parameter type {} is not toolBarThumbnail.'.format(type(t)))

    def getToolbarThumbnail(self):
        return self._thumbnail

    def hasToolbarThumbnail(self):
        return self._thumbnail is not None

    def setFiltersToDefault(self, ext=True):
        self._refDir = False
        self._refID = None
        self._refICBM = False
        self._refField = False
        self._refdicom = False
        self._refxvol = False
        self._refxroi = False
        self._refxmesh = False
        self._refxtracts = False
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

    def clearExtensionFilter(self):
        self._refExt = list()

    def getExtensionFilter(self):
        return self._refExt

    def filterDirectory(self):
        # self.setFiltersToDefault(True)
        self._refDir = True

    def filterExtensions(self, exts):
        if isinstance(exts, (list, tuple)):
            if len(exts) > 0:
                for ext in exts:
                    self.filterExtension(ext)
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(exts)))

    def filterExtension(self, ext):
        if isinstance(ext, str):
            if ext[0] != '.': ext = '.' + ext
            if ext == SisypheVolume.getFileExt(): self._refxvol = True
            elif ext == SisypheROI.getFileExt(): self._refxroi = True
            elif ext == SisypheMesh.getFileExt(): self._refxmesh = True
            elif ext == SisypheStreamlines.getFileExt(): self._refxtracts = True
            # self.setFiltersToDefault(False)
            # < Revision 06/02/2025
            # self._refExt.append(ext)
            if ext not in self._refExt: self._refExt.append(ext)
            # Revision 06/02/2025 >
        else: raise TypeError('parameter type {} is not str.'.format(type(ext)))

    def filterDICOM(self):
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

    def filterSisypheVolume(self):
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheVolume.getFileExt())
        # self._refxvol = True

    def filterSisypheROI(self):
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheROI.getFileExt())
        # self._refxroi = True

    def filterSisypheMesh(self):
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheMesh.getFileExt())
        # self._refxmesh = True

    def filterSisypheStreamlines(self):
        # self.setFiltersToDefault(True)
        self.filterExtension(SisypheStreamlines.getFileExt())
        # self._refxtracts = True

    def filterNifti(self):
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNiftiExt())
        # self._refExt += getNiftiExt()

    def filterMinc(self):
        # self.setFiltersToDefault(True)
        self.filterExtensions(getMincExt())
        # self._refExt += getMincExt()

    def filterNrrd(self):
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNrrdExt())
        # self._refExt += getNrrdExt()

    def filterVtk(self):
        # self.setFiltersToDefault(True)
        self.filterExtensions(getVtkExt())
        # self._refExt += getVtkExt()

    def filterNumpy(self):
        # self.setFiltersToDefault(True)
        self.filterExtensions(getNumpyExt())
        # self._refExt += getNumpyExt()

    def filterRange(self, v=None):
        if v is None: self._refRange = None
        if isinstance(v, SisypheVolume): v = v.display
        if isinstance(v, SisypheDisplay): v = v.getRange()
        if isinstance(v, tuple):
            self._refRange = (float(v[0]), float(v[1]))

    def filterMultiComponent(self):
        self._refcomponent = 2

    def filterSingleComponent(self):
        self._refcomponent = 1

    def filterSameIdentity(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume): v = v.getIdentity()
        if isinstance(v, SisypheIdentity): self._refidentity = v
        elif v is None: self._refidentity = ''
        else: raise TypeError('parameter type {} is not SisypheIdentity or SisypheVolume.'.format(type(v)))

    def filterSameFOV(self, v=None):
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

    def filterSameSize(self, v=None):
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

    def filterSameModality(self, v=None):
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
            if all([i in SisypheAcquisition.getModalityToCodeDict() for i in v]): self._refmodality = v
            else: raise ValueError('parameter value {} are not valid modality code.'.format(v))
        # Revision 10/10/2024 >
        elif v is None:
            self._refmodality = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameSequence(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getAcquisition().getSequence()
        # < Revision 10/10/2024
        # add multi sequence filter
        if isinstance(v, str):
            # self._refsequence = v
            self._refsequence = [v]
        elif isinstance(v, (list, tuple)):
            self._refsequence = v
        # Revision 10/10/2024 >
        elif v is None:
            self._refsequence = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameDatatype(self, v=None):
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

    def filterSameOrientation(self, v=None):
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

    def filterSuffix(self, suffix):
        if isinstance(suffix, str): self._refsuffix = suffix.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(suffix)))

    def filterPrefix(self, prefix):
        if isinstance(prefix, str): self._refprefix = prefix.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(prefix)))

    def filterFilenameContains(self, string):
        if isinstance(string, str): self._refcontains = string.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(string)))

    def filterRegisteredToReference(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheROI): v = v.getReferenceID()
        elif isinstance(v, SisypheVolume): v = v.getID()
        if isinstance(v, str): self._refID = v
        elif v is None: self._refID = ''
        else: raise TypeError('parameter type {} is not str, SisypheROI or SisypheVolume.'.format(type(v)))

    def filterSameID(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheROI): v = v.getReferenceID()
        elif isinstance(v, SisypheVolume): v = v.getID()
        if isinstance(v, str): self._refSpaceID = v
        elif v is None: self._refSpaceID = ''
        else: raise TypeError('parameter type {} is not str, SisypheROI or SisypheVolume.'.format(type(v)))

    def filterFrame(self):
        self._refframe = True

    def filterICBM(self):
        self._refICBM = True

    def filterDisplacementField(self):
        self._refField = True

    def filterWhole(self):
        self._refwhole = True

    def filterNotWhole(self):
        self._refnotwhole = True

    def filterCentroid(self):
        self._refcentroid = True

    def filterNotCentroid(self):
        self._refnotcentroid = True

    def getFOVFilter(self):
        return self._refFOV

    def getSizeFilter(self):
        return self._refSize

    def getModalityFilter(self):
        return self._refmodality

    def getSequenceFilter(self):
        return self._refsequence

    def getDatatypeFilter(self):
        return self._refdatatype

    def getOrientationFilter(self):
        return self._reforientation

    def getSuffixFilter(self):
        return self._refsuffix

    def getPrefixFilter(self):
        return self._refprefix

    def getRangeFilter(self):
        return self._refRange

    def getIDFilter(self):
        return self._refSpaceID

    def getFilenameContainsFilter(self):
        return self._refcontains

    def clearFilters(self):
        self._volume = None

        self._name = ''
        self._path = ''

        self._refDir = False
        self._refExt = list()
        self._refdicom = False
        self._refxvol = False
        self._refxroi = False
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


class FileSelectionWidget(QWidget, SelectionFilter):
    """
    FileSelectionWidget class

    Description
    ~~~~~~~~~~~

    Widget that manages single file selection and filtering.
    Available filters: directory, file extension, DICOM, Nifti, Minc, Nrrd, Vtk, numpy, SisypheVolume, SisypheROI,
    identity fields, ID, template ICBM152, FOV, size, modality, sequence, datatype, single component, multi component,
    orientation, scalar range, frame, filename prefix, filename suffix, str in filename, registered to a reference file

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FileSelectionWidget

    Last revision: 15/04/2025
    """

    # Custom Qt Signal

    FieldChanged = pyqtSignal(QWidget, str)
    FieldCleared = pyqtSignal(QWidget)

    # Special method

    """
    Private attributes

    _label          QLabel
    _field          QLineEdit
    _current        QPushbutton
    _open           QPushbutton
    _clear          QPushbutton
    """

    def __init__(self, parent=None):
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

        if platform == 'win32':
            self._current.setFixedSize(QSize(32, 32))
            self._open.setFixedSize(QSize(32, 32))
            self._clear.setFixedSize(QSize(32, 32))
        elif platform == 'darwin':
            self._current.setFixedSize(QSize(24, 24))
            self._open.setFixedSize(QSize(24, 24))
            self._clear.setFixedSize(QSize(24, 24))
        self._current.setToolTip('Add thumbnail volume to the field.')
        self._open.setToolTip('Add file to the field.')
        self._clear.setToolTip('Clear field.')

        self._menuThumbnail = QMenu(self._current)
        # noinspection PyTypeChecker
        self._menuThumbnail.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menuThumbnail.setWindowFlag(Qt.FramelessWindowHint, True)
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

    # Private methods

    def _onMenuThumbnailShow(self):
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.open(v.getFilename())
            elif n > 1:
                self._menuThumbnail.clear()
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
        self.open(str(action.data()))

    # Public methods

    def setToolbarThumbnail(self, t):
        super().setToolbarThumbnail(t)
        self._current.setVisible(True)

    def setCurrentVolumeButtonVisibility(self, v):
        if isinstance(v, bool):
            v = v and self.hasToolbarThumbnail()
            self._current.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def getCurrentVolumeButtonVisibility(self):
        return self._current.isVisible()

    def setClearButtonVisibility(self, v):
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def getClearButtonVisibility(self):
        return self._clear.isVisible()

    def setLabelVisibility(self, v):
        if isinstance(v, bool): self._label.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showLabel(self):
        self._label.setVisible(True)

    def hideLabel(self):
        self._label.setVisible(False)

    def getLabelVisibility(self):
        return self._label.isVisible()

    def setTextLabel(self, txt):
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(True)
        else:
            raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getTextLabel(self):
        return self._label.text()

    def getLabel(self):
        return self._label

    def alignLabels(self, w):
        if isinstance(w, FileSelectionWidget):
            fm = QFontMetrics(self._label.font())
            w1 = fm.horizontalAdvance(self._label.text())
            w2 = fm.horizontalAdvance(w._label.text())
            w1 = max(w1, w2)
            self._label.setAlignment(Qt.AlignRight)
            w.getLabel().setAlignment(Qt.AlignRight)
            self._label.setFixedWidth(w1 + 20)
            w.getLabel().setFixedWidth(w1 + 20)
        else: raise TypeError('Parameter type {} is not FileSelectionWidget.'.format(type(w)))

    def setButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._open.setVisible(v)
            self._clear.setVisible(v)
            self.setCurrentVolumeButtonVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showButtons(self):
        self.setButtonsVisibility(True)

    def hideButtons(self):
        self.setButtonsVisibility(False)

    def getButtonsVisibility(self):
        return self._open.isVisible()

    # < Revision 23/12/2024
    # add setFieldVisibility method
    def setFieldVisibility(self, v):
        if isinstance(v, bool):
            self._field.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add showField method
    def showField(self):
        self.setFieldVisibility(True)
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add hideField method
    def hideField(self):
        self.setFieldVisibility(False)
    # Revision 23/12/2024 >

    # < Revision 23/12/2024
    # add getFieldVisibility method
    def getFieldVisibility(self):
        return self._field.isVisible()
    # Revision 23/12/2024 >

    def setRemoveButtonVisibility(self, v):
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveButton(self):
        self._clear.setVisible(True)

    def hideRemoveButton(self):
        self._clear.setVisible(False)

    def getRemoveButtonVisibility(self):
        return self._clear.isVisible()

    def filterSisypheVolume(self):
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def clear(self, signal=True):
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
    def open(self, filename='', signal=True):
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
                directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                             getcwd(), QFileDialog.ShowDirsOnly)
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
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe volume', getcwd(), filt)
                    QApplication.processEvents()
                    self.activateWindow()
                    filename = filename[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    img = SisypheVolume()
                    # < Revision 17/11/2024
                    # load only xml part (attributes)
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
                    filename = QFileDialog.getOpenFileName(self, 'Select Sisyphe ROI', getcwd(), filt)
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
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', getcwd(), filt)
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
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', getcwd(), filt)
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
            # DICOM
            elif self._refdicom:
                if not param or paramext not in getDicomExt().append(''):
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    filename = QFileDialog.getOpenFileName(self, 'Select DICOM file', getcwd(), filt)
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
                    filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
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
                filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
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

    def isEmpty(self):
        return self._path == ''

    def getVolume(self):
        if not self.isEmpty():
            v = SisypheVolume()
            v.load(self.getFilename())
            return v
        else: raise AttributeError('No volume.')

    # Qt Drop events

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            self.open(event.mimeData().text()[7:])


class FilesSelectionWidget(QWidget, SelectionFilter):
    """
    FilesSelectionWidget class

    Description
    ~~~~~~~~~~~

    Widget that manages files selection and filtering.
    Available filters: directory, file extension, DICOM, Nifti, Minc, Nrrd, Vtk, numpy, SisypheVolume, SisypheROI,
    identity fields, ID, template ICBM152, FOV, size, modality, sequence, datatype, single component, multi component,
    orientation, scalar range, frame, filename prefix, filename suffix, str in filename, registered to a reference file

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FilesSelectionWidget

    Last revision: 19/06/2025
    """

    # Custom Qt Signals

    FieldChanged = pyqtSignal(QWidget, str)
    FieldCleared = pyqtSignal(QWidget, list)
    FilesSelectionChanged = pyqtSignal(QWidget)
    FilesSelectionWidgetSelectionChanged = pyqtSignal(QWidget, str)
    FilesSelectionWidgetCleared = pyqtSignal(QWidget)
    FilesSelectionWidgetDoubleClicked = pyqtSignal(QListWidgetItem)

    # Special method

    """
    Private attributes

    _label      QLabel
    _list       QListWidget
    _current    QPushButton
    _add        QPushButton
    _clear      QPushButton
    _clearall   QPushButton
    _stop       bool, break files check after failure
    _refCount   int, maximum number of files
    """

    def __init__(self, maxcount=100, checkbox=False, parent=None):
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self._refCount = maxcount
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

    # Private method

    def _selectionChanged(self):
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetSelectionChanged.emit(self, selecteditems[0].data(256))

    def _onMenuThumbnailShow(self):
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.add(v.getFilename())
            if n > 1:
                menu = QMenu(self._current)
                # noinspection PyTypeChecker
                menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyTypeChecker
                menu.setWindowFlag(Qt.FramelessWindowHint, True)
                menu.setAttribute(Qt.WA_TranslucentBackground, True)
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
        # < Revision 08/11/2024
        if action.text() == 'All':
            n = self._thumbnail.getWidgetsCount()
            wait = DialogWait(progress=True, progressmin=0, progressmax=n, cancel=True)
            wait.open()
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
        if item is not None:
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetDoubleClicked.emit(item)

    # Public methods

    def setStopCheckAfterFailure(self, stop):
        if isinstance(stop, bool): self._stop = stop
        else: raise TypeError('parameter type {} is not bool.'.format(type(stop)))

    def getStopCheckAfterFailure(self):
        return self._stop

    def setMaximumNumberOfFiles(self, n):
        if isinstance(n, int): self._refCount = n
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def getMaximumNumberOfFiles(self):
        return self._refCount

    def setToolbarThumbnail(self, t):
        super().setToolbarThumbnail(t)
        self._current.setVisible(True)

    def setCurrentVolumeButtonVisibility(self, v):
        if isinstance(v, bool):
            v = v and self.hasToolbarThumbnail()
            self._current.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showCurrentVolumeButton(self):
        self.setCurrentVolumeButtonVisibility(True)

    def hideCurrentVolumeButton(self):
        self.setCurrentVolumeButtonVisibility(False)

    def getCurrentVolumeButtonVisibility(self):
        return self._current.isVisible()

    def setLabelVisibility(self, v):
        if isinstance(v, bool): self._label.setVisible(v)
        else: raise TypeError('parameter {} is not bool.'.format(type(v)))

    def showLabel(self):
        self._label.setVisible(True)

    def hideLabel(self):
        self._label.setVisible(False)

    def getLabelVisibility(self):
        return self._label.isVisible()

    def setTextLabel(self, txt):
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(True)
        else: raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getTextLabel(self):
        return self._label.text()

    def getLabel(self):
        return self._label

    def setButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._add.setVisible(v)
            self._clear.setVisible(v)
            self._clearall.setVisible(v)
            self.setCurrentVolumeButtonVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showButtons(self):
        self.setButtonsVisibility(True)

    def hideButtons(self):
        self.setButtonsVisibility(False)

    def getButtonsVisibility(self):
        return self._add.isVisible()

    def setRemoveButtonVisibility(self, v):
        if isinstance(v, bool): self._clear.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveButton(self):
        self._clear.setVisible(True)

    def hideRemoveButton(self):
        self._clear.setVisible(False)

    def getRemoveButtonVisibility(self):
        return self._clear.isVisible()

    def setRemoveAllButtonVisibility(self, v):
        if isinstance(v, bool): self._clearall.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def showRemoveAllButton(self):
        self._clearall.setVisible(True)

    def hideRemoveAllButton(self):
        self._clearall.setVisible(False)

    def getRemoveAllButtonVisibility(self):
        return self._clearall.isVisible()

    def getCheckBoxVisibility(self):
        return self._checkbox

    def setSelectionTo(self, index):
        if not self.isEmpty():
            if isinstance(index, str):
                index = self._list.findItems(index, 0)
                if len(index) > 0: index = index[0]
            if isinstance(index, int):
                if index < self._list.count():
                    item = self._list.item(index)
                    item.setSelected(True)
            else: raise TypeError('parameter type {} is not int or str.'.format(type(index)))

    def copySelectionFrom(self, widget):
        if isinstance(widget, FilesSelectionWidget):
            items = widget.selectedItems()
            for item in items:
                row = widget.row(item)
                self._list.item(row).setSelected(True)
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def copySelectionTo(self, widget):
        if isinstance(widget, FilesSelectionWidget):
            items = self._list.selectedItems()
            for item in items:
                row = self._list.row(item)
                widget.item(row).setSelected(True)
        else: raise TypeError('parameter type {} is not FilesSelectionWidget.'.format(type(widget)))

    def clearSelection(self):
        self._list.clearSelection()

    def hasSelection(self):
        return len(self._list.selectedItems()) > 0

    def setSelectionMode(self, v):
        if isinstance(v, int):
            if 0 <= v < 5:
                self._list.setSelectionMode(v)
            else: raise ValueError('parameter value {} is not between 0 and 4.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setSelectionModeToSingle(self):
        self._list.setSelectionMode(1)

    def setSelectionModeToContiguous(self):
        self._list.setSelectionMode(4)

    def setSelectionModeToExtended(self):
        self._list.setSelectionMode(3)

    def getSelectionMode(self):
        return self._list.selectionMode()

    def getFilenames(self):
        filenames = None
        n = self._list.count()
        if n > 0:
            filenames = list()
            for i in range(n):
                filenames.append(self._list.item(i).data(256))
        return filenames

    def getSelectedFilenames(self):
        items = self._list.selectedItems()
        filenames = None
        if len(items) > 0:
            filenames = list()
            for item in items:
                filenames.append(item.data(256))
        return filenames

    def getCheckedFilenames(self):
        if not self._checkbox: return self.getFilenames()
        else:
            r = list()
            for i in range(self._list.count()):
                if self._list.item(i).checkState() > 0: r.append(self._list.item(i).data(256))
            return r

    def getCheckedIndexes(self):
        if not self._checkbox: return list(range(self._list.count()))
        else:
            r = list()
            for i in range(self._list.count()):
                if self._list.item(i).checkState() > 0: r.append(i)
            return r

    def getCheckStateList(self):
        if not self._checkbox: return [True] * self._list.count()
        else:
            r = list()
            for i in range(self._list.count()):
                r.append(self._list.item(i).checkState() > 0)
            return r

    def filterSisypheVolume(self):
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def containsItem(self, v):
        if isinstance(v, QListWidgetItem):
            items = self._list.findItems(v.text(), Qt.MatchExactly)
            if len(items) > 0:
                for item in items:
                    if v.data(256) == item.data(256):
                        return True
            return False
        else: raise TypeError('parameter type {} is not QListWidgetItem.'.format(type(v)))

    def getIndexFromItem(self, v):
        if isinstance(v, QListWidgetItem):
            return self._list.row(v)
        else: raise TypeError('parameter type {} is not QListWidgetItem.'.format(type(v)))

    def getItemFromIndex(self, i):
        if isinstance(i, int):
            return self._list.item(i).data(256)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    def getFilenameFromIndex(self, i):
        if isinstance(i, int):
            return self._list.item(i).data(256)
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    # noinspection PyUnboundLocalVariable
    def add(self, filenames='', label='', signal=True, wait: DialogWait | None = None):
        dtag = wait is None
        if label != '': label += ' '
        # Extract filepath, filename and ext of parameter if exists
        param = filenames != '' and exists(filenames)
        if param:
            buff, paramext = splitext(filenames)
            paramext = paramext.lower()
            filenames = [filenames]
        else: paramext = ''
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
                    if self._checkbox: item.setCheckState(Qt.Checked)
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
                        # load only xml part (attributes)
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
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                                    self._refID = self._volume.getReferenceID()
                                if self._refSpaceID is not None:
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
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                    filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe mesh', getcwd(), filt)
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
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                    filenames = QFileDialog.getOpenFileName(self, 'Select PySisyphe streamlines', getcwd(), filt)
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
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                            messageBox(self,
                                       'PySisyphe streamlines file selector',
                                       text='Maximum number of files is reached ({}).\n'
                                            'Remove file from the list if you want to\n'
                                            'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()
            # DICOM
            elif self._refdicom:
                if not param or paramext not in getDicomExt().append(''):
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
                            if self._checkbox: item.setCheckState(Qt.Checked)
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
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                        if self._checkbox: item.setCheckState(Qt.Checked)
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
                            messageBox(self,
                                       'File selector',
                                       text='Maximum number of files is reached ({}).\n'
                                            'Remove file from the list if you want to\n'
                                            'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    if dtag: wait.close()

    def clearItem(self, i, signal=True):
        if isinstance(i, int):
            if i < self._list.count():
                self._list.takeItem(i)
                self._add.setEnabled(True)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.FieldCleared.emit(self, [i])
            else: raise ValueError('parameter index is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    def clearLastItem(self, signal=True):
        n = self._list.count()
        if n > 0: self._list.takeItem(n - 1)
        self._add.setEnabled(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, [n-1])

    def clear(self, signal=True):
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

    def clearall(self, signal=True):
        rows = list(range(self._list.count()))
        self._list.clear()
        self._add.setEnabled(True)
        if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            # noinspection PyUnresolvedReferences
            self.FieldCleared.emit(self, rows)
            # noinspection PyUnresolvedReferences
            self.FilesSelectionWidgetCleared.emit(self)

    def isEmpty(self):
        return self._list.count() == 0

    def filenamesCount(self):
        return self._list.count()

    # Qt Drop events

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            files = event.mimeData().text().split('\n')
            for file in files:
                if file != '': self.add(file[7:])


class MultiExtFilesSelectionWidget(FilesSelectionWidget):
    """
    MultiExtFilesSelectionWidget class

    Description
    ~~~~~~~~~~~

    FilesSelectionWidget to select multiple file types.

    Inheritance
    ~~~~~~~~~~~

    QWidget, SelectionFilter -> FilesSelectionWidget -> MultiExtFilesSelectionWidget

    Last revision: 15/04/2025
    """

    # Public methods

    def add(self, filenames='', label='', signal=True, wait: DialogWait | None = None):
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

    Multiple synchronized widgets for file selection.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SynchronizedFileSelectionWidget

    Last revision: 22/10/2024
    """

    # Special method

    """
    Private attributes

    _lists      list[FileSelectionWidget]
    """

    def __init__(self, single, multiple, maxcount=100, parent=None):
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
                flist = FilesSelectionWidget(parent=parent)
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

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in self._single: return self._single[key]
            if key in self._multiple: return self._multiple[key]
            raise ValueError('Invalid key parameter.')
        else: raise TypeError('key type {} is not str.'.format(type(key)))

    # Private method

    def _ListChanged(self, widget, filename):
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
    def _ListCleared(self, widget):
        if self.isEmpty(): self._FOV = list()

    # Public methods

    # < Revision 09/10/2024
    # add setToolbarThumbnail method
    def setToolbarThumbnail(self, t):
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
    def getToolbarThumbnail(self):
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
    def hasToolbarThumbnail(self):
        if self._single is not None:
            k0 = list(self._single.keys())[0]
            return self._single[k0].hasToolbarThumbnail()
        if self._multiple is not None:
            k0 = list(self._multiple.keys())[0]
            return self._multiple[k0].hasToolbarThumbnail()
        raise AttributeError('No single or multiple file selection widget.')
    # Revision 09/10/2024 >

    def getGetNumberOfLists(self):
        return len(self._single) + len(self._muliple)

    def getTitles(self):
        r = dict()
        r['single'] = list(self._single.keys())
        r['multiple'] = list(self._multiple.keys())
        return r

    def getSingleListTitles(self):
        return list(self._single.keys())

    def getMultipleListTitles(self):
        return list(self._multiple.keys())

    def setSisypheVolumeFilters(self, filters):
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

    def setSequenceFilters(self, filters):
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

    def getSequenceFilters(self):
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

    def setModalityFilters(self, filters):
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

    def getModalityFilters(self):
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

    def setSuffixFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getSuffixFilters(self):
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

    def setPrefixFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getPrefixFilters(self):
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

    def setContainsStringFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._single) > 0:
                if 'single' in filters:
                    flt = filters['single']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._single):
                            for i, (_, flist) in enumerate(self._single.items()):
                                flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiple) > 0:
                if 'multiple' in filters:
                    flt = filters['multiple']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiple):
                            for i, (_, flist) in enumerate(self._multiple.items()):
                                flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getContainsStringFilters(self):
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
    def getSelectionWidget(self, label):
        if self._single is not None:
            if label in self._single: return self._single[label]
        if self._multiple is not None:
            if label in self._multiple: return self._multiple[label]
        raise AttributeError('No single or multiple file selection widget.')
    # Revision 10/10/2024 >

    # < Revision 23/10/2024
    # add getSelectionWidget method
    def getSelectionWidgets(self):
        r = list()
        if self._single is not None:
            for label in self._single:
                r.append(self._single[label])
        if self._multiple is not None:
            for label in self._multiple:
                r.append(self._multiple[label])
        return tuple(r)
    # Revision 23/10/2024 >

    def getFilenames(self):
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

    def setFilenames(self, filenames):
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
    def setAvailability(self, flags):
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
    def getAvailability(self):
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

    def isReady(self):
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

    def isEmpty(self):
        return self.isSingleEmpy() and self.isMultipleEmpty()

    def isSingleEmpy(self):
        if len(self._single) > 0:
            for _, flist in self._single.items():
                if not flist.isEmpty(): return False
        return True

    def isMultipleEmpty(self):
        if len(self._multiple) > 0:
            for _, flist in self._multiple.items():
                if not flist.isEmpty(): return False
        return True

    # < Revision 09/10/2024
    # add hasToolbarThumbnail method
    def clearall(self, signal=True):
        if self._single is not None:
            for k in self._single:
                self._single[k].clear(signal)
        if self._multiple is not None:
            for k in self._multiple:
                self._multiple[k].clearall(signal)
    # Revision 09/10/2024 >
