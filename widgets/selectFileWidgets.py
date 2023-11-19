"""
    External packages/modules

        Name            Link                                                        Usage

        darkdetect      https://github.com/albertosottile/darkdetect                OS Dark Mode detection
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

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
from Sisyphe.core.sisypheXml import XmlVolume
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SelectionFilter',
           'FileSelectionWidget',
           'FilesSelectionWidget',
           'SynchronizedFilesSelectionWidget']

"""
    Class hierarchy

        object -> SelectionFilter, QWidget  -> FileSelectionWidget
                                            -> FilesSelectionWidget
        QWidget ->  SynchronizedFileSelectionWidget
                ->  SynchronizedFilesSelectionWidget
"""


class SelectionFilter(object):
    """
        SelectionFilter class

        Description

            Base class for file selection widgets (FileSelectionWidget & FilesSelectionWidget).
            Filter management (Directory, file extension, DICOM, SisypheVolume, SisypheROI, identity fields, FOV
            size, modality, sequence, datatype, orientation, frame, registered to reference file)

        Inheritance

            object -> SelectionFilter

        Private attributes

            _name           str, basename of file
            _path           str, abspath of file
            _volume         SisypheVolume, reference volume
            _refExt         str, reference extension
            _refID          str, reference ID
            _refRange       tuple[float, float], reference range
            _refICBM        bool, reference ICBM
            _refdicom       bool, reference dicom file extension
            _refxvol        bool, reference xvol file extension
            _refxroi        bool, reference xroi file extension
            _refidentity    SisypheIdentity, reference identity
            _refFOV         (float, float, float), reference FOV
            _refSize        (int, int, int), reference matrix size
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

        Public methods

            str = getFilename()
            str = getPath()
            str = getBasename()
            setReferenceVolume()
            getReferenceVolume()
            setReferenceVolumeToFirst()
            bool = isReferenceVolumeToFirst()
            setToolBarThumbnail(ToolBarThumbnail)
            ToolBarThumbnail = getToolBarThumbnail()
            bool = hasToolBarThumbnail
            setFiltersToDefault(bool)   if True, clear extension list filter
            clearExtensionFilter()
            str = getExtensionFilter()
            list(float, float, float) = getFOVFilter()
            list(int, int, int) = getSizeFilter()
            str = getModalityFilter()
            str = getSequenceFilter()
            str = getDatatypeFilter()
            int = getOrientationFilter()
            filterDirectory()
            filterExtension(str)
            filterDICOM()
            filterSisypheVolume()
            filterSisypheROI()
            filterNifti()
            filterMinc()
            filterNrrd()
            filterVtk()
            filterNumpy()
            filterRange(tuple or SisypheDisplay or SisypheVolume)
            filterMultiComponent()
            filterSingleComponent()
            filterSameIdentity(SisypheIdentity or SisypheVolume)
            filterSameFOV(SisypheVolume)
            filterSameSize(SisypheVolume)
            filterSameModality(SisypheAcquisition or SisypheVolume)
            filterSameSequence(SisypheAcquisition or SisypheVolume)
            filterSameDatatype(str or SisypheVolume)
            filterSameOrientation(int or SisypheVolume)
            filterRegisteredToReference(str or SisypheVolume)
            filterSameID(str or SisypheVolume)
            filterPrefix(str)
            filterSuffix(str)
            filterFilenameContains(str)
            filterFrame()
            filterICBM()
            filterDisplacementField()
            [float, float, float] = getFOVFilter()
            [int, int, int] = getSizeFilter()
            str = getModalityFilter()
            str = getSequenceFilter()
            str = getDatatypeFilter()
            str = getOrientationFilter()
            str = getPrefixFilter()
            str = getSuffixFilter()
            (float, float) = getRangeFilter()
            str = getFilenameContainsFilter()

            inherited object methods

        Revisions:
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
        self._refID = None
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
        self.setFiltersToDefault(True)
        self._refDir = True

    def filterExtension(self, ext):
        if isinstance(ext, str):
            if ext[0] != '.': ext = '.' + ext
            if ext[0] == SisypheVolume.getFileExt(): self.filterSisypheVolume()
            if ext[0] == SisypheROI.getFileExt(): self.filterSisypheROI()
            self.setFiltersToDefault(False)
            self._refExt.append(ext)
        else:
            raise TypeError('parameter type {} is not str.'.format(type(ext)))

    def filterDICOM(self):
        self.setFiltersToDefault(True)
        self._refExt.append('.dcm')
        self._refExt.append('.dicm')
        self._refExt.append('.ima')
        self._refExt.append('.nema')
        self._refdicom = True

    def filterSisypheVolume(self):
        self.setFiltersToDefault(True)
        self.filterExtension(SisypheVolume.getFileExt())
        self._refxvol = True

    def filterSisypheROI(self):
        self.setFiltersToDefault(True)
        self.filterExtension(SisypheROI.getFileExt())
        self._refxroi = True

    def filterNifti(self):
        self.setFiltersToDefault(True)
        self._refExt += getNiftiExt()

    def filterMinc(self):
        self.setFiltersToDefault(True)
        self._refExt += getMincExt()

    def filterNrrd(self):
        self.setFiltersToDefault(True)
        self._refExt += getNrrdExt()

    def filterVtk(self):
        self.setFiltersToDefault(True)
        self._refExt += getVtkExt()

    def filterNumpy(self):
        self.setFiltersToDefault(True)
        self._refExt += getNumpyExt()

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
        if isinstance(v, (SisypheVolume, SisypheROI)): self._refFOV = v.getFieldOfView()
        elif v is None: self._refFOV = 0
        else: raise TypeError('parameter type {} is not SisypheROI or SisypheVolume.'.format(type(v)))

    def filterSameSize(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, (SisypheVolume, SisypheROI)): self._refSize = v.getSize()
        elif v is None: self._refSize = 0
        else: raise TypeError('parameter type {} is not SisypheROI or SisypheVolume.'.format(type(v)))

    def filterSameModality(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getAcquisition().getModality()
        if isinstance(v, str):
            if v in SisypheAcquisition.getModalityToCodeDict():
                self._refmodality = v
            else: raise ValueError('parameter value {} is not valid modality code.'.format(v))
        elif v is None:
            self._refmodality = ''
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(v)))

    def filterSameSequence(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheVolume):
            v = v.getAcquisition().getSequence()
        if isinstance(v, str):
            self._refsequence = v
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
        if isinstance(prefix, str): self._refcontains = string.lower()
        else: raise TypeError('parameter type {} is not str.'.format(type(string)))

    def filterRegisteredToReference(self, v=None):
        if v is None: v = self._volume
        if isinstance(v, SisypheROI): v = v.getReferenceID()
        elif isinstance(v, SisypheVolume): v = v.getID()
        if isinstance(v, str): self._refID = v
        elif v is None: self._refID = ''
        else: raise TypeError('parameter type {} is not str, SisypheROI or SisypheVolume.'.format(type(v)))

    filterSameID = filterRegisteredToReference

    def filterFrame(self):
        self._refframe = True

    def filterICBM(self):
        self._refICBM = True

    def filterDisplacementField(self):
        self._refField = True

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

    def getFilenameContainsFilter(self):
        return self._refcontains


class FileSelectionWidget(QWidget, SelectionFilter):
    """
        FileSelectionWidget class

        Description

            Widget for single file selection

        Inheritance

            QWidget, SelectionFilter -> FileSelectionWidget

        Private attributes

            _label          QLabel
            _field          QLineEdit
            _current        QPushbutton
            _open           QPushbutton
            _clear          QPushbutton

        Custom Qt Signal

            FieldChanged.emit(QWidget, str)

        Public methods

            setToolbarThumbnail(ToolBarThumbnail)   override SelectionFilter method
            setCurrentVolumeButtonVisibility(bool)
            bool = getCurrentVolumeButtonVisibility()
            setClearButtonVisibility(bool)
            bool = getClearButtonVisibility()
            setLabelVisibility(bool)
            showLabel()
            hideLabel()
            bool = getLabelVisibility()
            setTextLabel(str)
            str = getTextLabel()
            QLabel = getLabel()
            setFiltersToDefault(bool)   if True, clear extension list filter
            clearExtensionFilter()
            getExtensionFilter()
            filterSisypheVolume()       override SelectionFilter method
            clear()
            open()
            show()                      override
            bool = isEmpty()
            SisypheVolume = getVolume()
            dragEnterEvent(QEvent)
            dropEvent(QEvent)

            inherited SelectionFilter methods
            inherited QWidget methods

        Revisions:

            14/09/2023  _onMenuThumbnailShow() method,
                        if there is only one volume in thumbnail, add volume filename without displaying menu
            09/11/2023  open() method bugfix, replace elif by if for filter tests
    """

    # Custom Qt Signal

    FieldChanged = pyqtSignal(QWidget, str)
    FieldCleared = pyqtSignal(QWidget)

    # Special method

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self.setAcceptDrops(True)

        # Init QLayout

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._label = QLabel()
        self._label.setVisible(False)
        self._label.setContentsMargins(0, 0, 5, 0)
        self._field = QLineEdit()
        self._field.setReadOnly(True)
        self._current = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'left.png')), '')
        self._open = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'open.png')), '')
        self._clear = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'cross.png')), '')
        self._current.setFixedSize(QSize(32, 32))
        self._open.setFixedSize(QSize(32, 32))
        self._clear.setFixedSize(QSize(32, 32))
        self._current.setToolTip('Add thumbnail volume to the field.')
        self._open.setToolTip('Add file to the field.')
        self._clear.setToolTip('Clear field.')

        self._current.clicked.connect(self._onMenuThumbnailShow)

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._field)
        self._layout.addWidget(self._current)
        self._layout.addWidget(self._open)
        self._layout.addWidget(self._clear)

        self._current.setVisible(False)

        self._open.clicked.connect(lambda: self.open())
        self._clear.clicked.connect(lambda: self.clear())

    # Private methods

    def _onMenuThumbnailShow(self):
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.open(v.getFilename())
            elif n > 1:
                menu = QMenu(self._current)
                for i in range(n):
                    v = self._thumbnail.getVolumeFromIndex(i)
                    action = menu.addAction(v.getBasename())
                    action.setData(v.getFilename())
                menu.triggered.connect(self._onMenuThumbnailSelect)
                menu.exec(self._current.mapToGlobal(QPoint(0, self._current.height())))

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

    def filterSisypheVolume(self):
        SelectionFilter.filterSisypheVolume(self)
        self._current.setVisible(self.hasToolbarThumbnail())

    def clear(self, signal=True):
        self._field.setText('')
        self._field.setToolTip('')
        self._name = ''
        self._path = ''
        if signal:
            self.FieldChanged.emit(self, '')
            self.FieldCleared.emit(self)

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
            if directory:
                chdir(directory)
                self._name = ''
                self._path = directory
                self._field.setText(directory)
                self._field.setToolTip(directory)
                if signal: self.FieldChanged.emit(self, directory)
        elif len(self._refExt) > 0:
            # SisypheVolume
            if self._refxvol:
                if not param or paramext != SisypheVolume.getFileExt():
                    filt = 'PySisyphe Volume (*.xvol)'
                    filename = QFileDialog.getOpenFileName(self, 'Select PySisyphe volume', getcwd(), filt)
                    QApplication.processEvents()
                    filename = filename[0]
                if filename:
                    chdir(dirname(filename))
                    img = SisypheVolume()
                    try: img.load(filename)
                    except:
                        QMessageBox.warning(self, 'PySisyphe volume file selector',
                                            '{} is not a valid Sisyphe volume file.'.format(self._name))
                        return None
                    # Component verification
                    if self._refcomponent == 1:
                        c = img.getNumberOfComponentsPerPixel()
                        if c > 1:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} is a multi component image.'.format(basename(filename[0])))
                            return None
                    elif self._refcomponent > 1:
                        c = img.getNumberOfComponentsPerPixel()
                        if c == 1:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} is a single component image.'.format(basename(filename[0])))
                            return None
                    # Identity verification
                    if self._refidentity:
                        if img.getIdentity().isNotEqual(self._refidentity):
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image identity is different from reference.'.format(
                                                    basename(filename[0])))
                            return None
                    # FOV verification
                    if self._refFOV:
                        if img.getFieldOfView() != self._refFOV:
                            txt = '{0} image field of view {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                  'is different from reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                            QMessageBox.warning(self,
                                                'PySisyphe volume file selector',
                                                txt.format(basename(filename[0]),
                                                           img.getFieldOfView(),
                                                           self._refFOV))
                            return None
                    # Size verification
                    if self._refSize:
                        if img.getSize() != self._refSize:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image size {} is different from reference {}.'.format(basename(
                                                    filename[0]),
                                                    img.getSize(),
                                                    self._refSize))
                            return None
                    # ICBM verification
                    if self._refICBM:
                        if not img.acquisition.isICBM152():
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image is not in ICBM space.'.format(basename(filename[0])))
                            return None
                    # Displacement field verification
                    if self._refField:
                        if not (img.isFloatDatatype() and
                                img.getNumberOfComponentsPerPixel() == 3
                                and img.getAcquisition().isDisplacementField()):
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image is not displacement field.'.format(basename(filename[0])))
                            return None
                    # Modality verification
                    if self._refmodality:
                        if img.getAcquisition().getModality() != self._refmodality:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image modality {} is different from reference ({}).'.format(
                                                    basename(filename[0]),
                                                    img.getAcquisition().getModality(),
                                                    self._refmodality))
                            return None
                    # Sequence verification
                    if self._refsequence:
                        if img.getAcquisition().getSequence() != self._refsequence:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image sequence {} is different from reference ({}).'.format(
                                                    basename(filename[0]),
                                                    img.getAcquisition().getSequence(),
                                                    self._refsequence))
                            return None
                    # Datatype verification
                    if self._refdatatype:
                        if img.getDatatype() != self._refdatatype:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image datatype {} is different from reference ({}).'.format(
                                                    basename(filename[0]),
                                                    img.getDatatype(),
                                                    self._refdatatype))
                            return None
                    # Orientation verification
                    if self._reforientation:
                        if img.getOrientationAsString().lower() != self._reforientation:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image orientation {} is different from reference ({}).'.format(
                                                    basename(filename[0]),
                                                    img.getOrientationAsString(),
                                                    self._reforientation))
                            return None
                    # Registered verification
                    if self._refID:
                        if img.getTransforms().hasReferenceID(self._refID):
                            trf = img.getTransformFromID(self._refID)
                            if not trf.isIdentity():
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image not registered to reference.'.format(
                                                        basename(filename[0])))
                                return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} does not have {} prefix.'.format(
                                                    basename(filename[0]), self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} does not have {} suffix.'.format(
                                                    basename(filename[0]), self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} does not contains {} string.'.format(
                                                    basename(filename[0]), self._refcontains))
                            return None
                    # Frame verification
                    if self._refframe:
                        if not img.getAcquisition().getFrame():
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image has no frame.'.format(basename(filename[0])))
                            return None
                    # Range verification
                    if self._refRange:
                        r = img.display.getRange()
                        if r[0] < self._refRange[0] or r[1] > self._refRange[1]:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} image range is not between {} and {} .'.format(basename(filename[0]),
                                                                                                   self._refRange[0],
                                                                                                   self._refRange[1]))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(img))
                    if signal: self.FieldChanged.emit(self, filename)
            # SisypheROI
            elif self._refxroi:
                if not param or paramext != SisypheROI.getFileExt():
                    filt = 'PySisyphe ROI (*.xroi)'
                    filename = QFileDialog.getOpenFileName(self, 'Select Sisyphe ROI', getcwd(), filt)
                    QApplication.processEvents()
                    filename = filename[0]
                if filename:
                    chdir(dirname(filename))
                    img = SisypheROI()
                    try: img.load(filename)
                    except:
                        QMessageBox.warning(self, 'File selector',
                                            '{} is not a valid Sisyphe ROI file.'.format(basename(filename[0])))
                        return None
                    # Size verification
                    if self._refSize:
                        if img.getSize() != self._refSize:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} ROI size {} is different from reference {}.'.format(
                                                    basename(filename[0]),
                                                    img.getSize(),
                                                    self._refSize))
                            return None
                    # FOV verification
                    if self._refFOV:
                        if img.getFieldOfView() != self._refFOV:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} ROI FOV {} is different from reference {}.'.format(
                                                    basename(filename[0]),
                                                    img.getFieldOfView(),
                                                    self._refFOV))
                            return None
                    # Registered verification
                    if self._refID:
                        if img.getReferenceID() != self._refID:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} ROI is not registered to reference.'.format(basename(filename[0])))
                            return None
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} does not have {} prefix.'.format(
                                                    basename(filename[0]), self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} does not have {} suffix.'.format(
                                                    basename(filename[0]), self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} does not contains {} string.'.format(
                                                    basename(filename[0]), self._refcontains))
                            return None
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    self._field.setToolTip(str(img))
                    if signal: self.FieldChanged.emit(self, filename)
            # DICOM
            elif self._refdicom:
                if not param or paramext not in getDicomExt().append(''):
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    filename = QFileDialog.getOpenFileName(self, 'Select DICOM file', getcwd(), filt)
                    QApplication.processEvents()
                    filename = filename[0]
                if filename:
                    if isDicom(filename):
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not have {} prefix.'.format(
                                                        basename(filename[0]), self._refprefix))
                                return None
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not have {} suffix.'.format(
                                                        basename(filename[0]), self._refsuffix))
                                return None
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not contains {} string.'.format(
                                                        basename(filename[0]), self._refcontains))
                                return None
                        self._path, self._name = split(filename)
                        self._field.setText(self._name)
                        if signal: self.FieldChanged.emit(self, filename)
                    else:
                        QMessageBox.warning(self, 'File selector', '{} is not a valid dicom file.'.format(self._name))
            # Other file
            else:
                if not param or paramext not in self._refExt:
                    filt = 'Files ('
                    for ext in self._refExt:
                        filt += '*{} '.format(ext)
                    filt = filt.rstrip() + ')'
                    filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
                    QApplication.processEvents()
                    filename = filename[0]
                if filename:
                    # Prefix verification
                    if self._refprefix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[:len(self._refprefix)] == self._refprefix:
                            QMessageBox.warning(self, 'File selector',
                                                '{} does not have {} prefix.'.format(
                                                    basename(filename[0]), self._refprefix))
                            return None
                    # Suffix verification
                    if self._refsuffix:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if not bname[-len(self._refsuffix):] == self._refsuffix:
                            QMessageBox.warning(self, 'File selector',
                                                '{} does not have {} suffix.'.format(
                                                    basename(filename[0]), self._refsuffix))
                            return None
                    # Filename contains verification
                    if self._refcontains:
                        bname = splitext(basename(filename))[0]
                        bname = bname.lower()
                        if bname.find(self._refcontains) > -1:
                            QMessageBox.warning(self, 'File selector',
                                                '{} does not contains {} string.'.format(
                                                    basename(filename[0]), self._refcontains))
                            return None
                    chdir(dirname(filename))
                    self._path, self._name = split(filename)
                    self._field.setText(self._name)
                    if signal: self.FieldChanged.emit(self, filename)
        else:
            if not param:
                filt = 'All files (*.*)'
                filename = QFileDialog.getOpenFileName(self, 'Select file', getcwd(), filt)
                QApplication.processEvents()
                filename = filename[0]
            if filename:
                # Prefix verification
                if self._refprefix:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if not bname[:len(self._refprefix)] == self._refprefix:
                        QMessageBox.warning(self, 'File selector',
                                            '{} does not have {} prefix.'.format(
                                                basename(filename[0]), self._refprefix))
                        return None
                # Suffix verification
                if self._refsuffix:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if not bname[-len(self._refsuffix):] == self._refsuffix:
                        QMessageBox.warning(self, 'File selector',
                                            '{} does not have {} suffix.'.format(
                                                basename(filename[0]), self._refsuffix))
                        return None
                # Filename contains verification
                if self._refcontains:
                    bname = splitext(basename(filename))[0]
                    bname = bname.lower()
                    if bname.find(self._refcontains) > -1:
                        QMessageBox.warning(self, 'File selector',
                                            '{} does not contains {} string.'.format(
                                                basename(filename[0]), self._refcontains))
                        return None
                chdir(dirname(filename))
                self._path, self._name = split(filename)
                self._field.setText(self._name)
                if signal: self.FieldChanged.emit(self, filename)

    def isEmpty(self):
        return self._path == ''

    def getVolume(self):
        if not self.isEmpty():
            v = SisypheVolume()
            v.load(self.getFilename())
            return v

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

            Widget for files selection

        Inheritance

            QWidget, SelectionFilter -> FilesSelectionWidget

        Private attributes

            _label      QLabel
            _list       QListWidget
            _current    QPushButton
            _add        QPushButton
            _clear      QPushButton
            _clearall   QPushButton
            _stop       bool, break files check after failure
            _refCount   maximum number of files

        Custom Qt Signals

            FilesSelectionWidgetSelectionChanged.emit(QWidget, str)
            FilesSelectionWidgetCleared.emit(QWidget)

        Public methods

            setStopCheckAfterFailure(bool)
            bool = getStopCheckAfterFailure()
            setMaximumNumberOfFiles(int)
            int = getMaximumNumberOfFiles()
            setToolbarThumbnail(ToolBarThumbnail)   override SelectionFilter method
            setCurrentVolumeButtonVisibility(bool)
            hideCurrentVolumeButtonVisibility()
            showCurrentVolumeButtonVisibility()
            bool = getCurrentVolumeButtonVisibility()
            setLabelVisibility(bool)
            showLabel()
            hideLabel()
            bool = getLabelVisibility()
            setButtonsVisibility(bool)
            showButtons()
            hideButtons()
            getButtonsVisibility()
            setRemoveButtonVisibility(bool)
            showRemoveButton()
            hideRemoveButton()
            getRemoveButtonVisibility()
            setRemoveAllButtonVisibility(bool)
            showRemoveAllButton()
            hideRemoveAllButton()
            getRemoveAllButtonVisibility()
            setTextLabel(str)
            str = getTextLabel()
            QLabel = getLabel()
            setSelectionTo(str or int)              int = index in list; str = filename
            copySelectionFrom(FilesSelectionWidget)
            copySelectionTo(FilesSelectionWidget)
            clearSelection()
            setSelectionMode(int)
            setSelectionModeToSingle()
            setSelectionModeToContiguous()
            setSelectionModeToExtended()
            int = getSelectionMode()
            list = getFilenames()
            list = getSelectedFilenames()
            filterSisypheVolume()
            containsItem(str)
            int = getIndexFromItem(QListWidgetItem)
            QListWidgetItem = getItemFromIndex(int)
            str = getFilenameFromIndex(int)
            add()
            clear()
            clearItem()
            clearLatsItem()
            clearall()
            bool = isEmpty()
            int = filenamesCount()
            show()                          override
            dragEnterEvent(QEvent)
            dropEvent(QEvent)

            inherited SelectionFilter methods
            inherited QWidget methods

        Revisions:

            14/09/2023  _onMenuThumbnailShow() method,
                        if there is only one volume in thumbnail, add volume filename without displaying menu
            09/11/2023  add() method bugfix, replace elif by if for filter tests
                              display DialogWait progress bar if several files are added
    """

    # Custom Qt Signals

    FieldChanged = pyqtSignal(QWidget, str)
    FieldCleared = pyqtSignal(QWidget, list)
    FilesSelectionChanged = pyqtSignal(QWidget)
    FilesSelectionWidgetSelectionChanged = pyqtSignal(QWidget, str)
    FilesSelectionWidgetCleared = pyqtSignal(QWidget)
    FilesSelectionWidgetDoubleClicked = pyqtSignal(QListWidgetItem)

    # Special method

    def __init__(self, maxcount=100, parent=None):
        QWidget.__init__(self, parent)
        SelectionFilter.__init__(self)

        self._refCount = maxcount
        self._stop = False
        self.setAcceptDrops(True)

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
        self._list.itemSelectionChanged.connect(self._selectionChanged)
        self._list.setSelectionMode(3)  # Extended selection
        self._list.itemDoubleClicked.connect(self._onDoubleClicked)
        self._current = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'left.png')), '')
        self._add = QPushButton('Add')
        self._clear = QPushButton('Remove')
        self._clearall = QPushButton('Remove all')
        self._current.setFixedSize(QSize(50, 32))
        self._current.setToolTip('Add thumbnail volume to the list.')
        self._add.setToolTip('Add file(s) to the list.')
        self._clear.setToolTip('Remove selected file(s) from the list.')
        self._clearall.setToolTip('Remove all files from the list.')

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

        self._add.clicked.connect(lambda: self.add())
        self._clear.clicked.connect(self.clear)
        self._clearall.clicked.connect(self.clearall)

    # Private method

    def _selectionChanged(self):
        selecteditems = self._list.selectedItems()
        if len(selecteditems) > 0:
            self.FilesSelectionWidgetSelectionChanged.emit(self, selecteditems[0].data(256))

    def _onMenuThumbnailShow(self):
        if self.hasToolbarThumbnail():
            n = self._thumbnail.getWidgetsCount()
            if n == 1:
                v = self._thumbnail.getVolumeFromIndex(0)
                self.add(v.getFilename())
            if n > 1:
                menu = QMenu(self._current)
                for i in range(n):
                    v = self._thumbnail.getVolumeFromIndex(i)
                    action = menu.addAction(v.getBasename())
                    action.setData(v.getFilename())
                menu.triggered.connect(self._onMenuThumbnailSelect)
                menu.exec(self._current.mapToGlobal(QPoint(0, self._current.height())))

    def _onMenuThumbnailSelect(self, action):
        self.add(str(action.data()))

    def _onDoubleClicked(self, item):
        if item is not None:
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

    def add(self, filenames='', label='', signal=True):
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
            if param: directory = split(filenames)[0]
            else:
                directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                             getcwd(), QFileDialog.ShowDirsOnly)
                QApplication.processEvents()
            if directory:
                chdir(directory)
                directories = [directory]
                sub = glob(join(directory, '**'))
                for i in range(len(sub)-1, -1, -1):
                    if not isdir(sub[i]): del sub[i]
                if len(sub) > 0:
                    if QMessageBox.question(self, 'Select directory', 'Add subdirectories ?') == QMessageBox.Yes:
                        directories += sub
                for directory in directories:
                    item = QListWidgetItem(directory)
                    item.setData(256, directory)
                    if self.containsItem(item):
                        QMessageBox.warning(self, 'Select directory',
                                            '{} is already in the list.'.format(item.text()))
                    else:
                        self._list.addItem(item)
                        if signal:
                            self.FieldChanged.emit(self, directory)
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
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True,
                                      parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe Volumes...')
                        wait.open()
                    for filename in filenames:
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheVolume()
                        try: img.load(filename)
                        except:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} is not a valid Sisyphe volume file.'.format(self._name))
                            if self._stop: break
                            else: continue
                        # First volume is reference
                        if self._list.count() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    self._refID = self._volume.getID()
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
                        # Component verification
                        if self._refcomponent == 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c > 1:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} is a multi component image.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        elif self._refcomponent > 1:
                            c = img.getNumberOfComponentsPerPixel()
                            if c == 1:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} is a single component image.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        # Same Identity verification
                        if self._refidentity:
                            if img.getIdentity().isNotEqual(self._refidentity):
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image identity is different from reference.'.format(
                                                        basename(filename)))
                                if self._stop: break
                                else: continue
                        # Same FOV verification
                        if self._refFOV:
                            if img.getFieldOfView() != self._refFOV:
                                txt = '{0} image FOV {1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm ' \
                                      'is different from reference {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm.'
                                QMessageBox.warning(self,
                                                    'PySisyphe volume file selector',
                                                    txt.format(basename(filename),
                                                                        img.getFieldOfView(),
                                                                        self._refFOV))
                                if self._stop: break
                                else: continue
                        # Same Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image size {} is different from reference {}.'.format(basename(
                                                        filename),
                                                        img.getSize(),
                                                        self._refSize))
                                if self._stop: break
                                else: continue
                        # ICBM verification
                        if self._refICBM:
                            if not img.acquisition.isICBM152():
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image is not in ICBM space.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        # Displacement field verification
                        if self._refField:
                            if not (img.isFloatDatatype() and
                                    img.getNumberOfComponentsPerPixel() == 3
                                    and img.getAcquisition().isDisplacementField()):
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image is not displacement field.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        # Same Modality verification
                        if self._refmodality:
                            if img.getAcquisition().getModality() != self._refmodality:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image modality {} is different from reference ({}).'.format(
                                                        basename(filename),
                                                        img.getAcquisition().getModality(),
                                                        self._refmodality))
                                if self._stop: break
                                else: continue
                        # Same Sequence verification
                        if self._refsequence:
                            if img.getAcquisition().getSequence() != self._refsequence:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image sequence {} is different from reference ({}).'.format(
                                                        basename(filename),
                                                        img.getAcquisition().getSequence(),
                                                        self._refsequence))
                                if self._stop: break
                                else: continue
                        # Same Datatype verification
                        if self._refdatatype:
                            if img.getDatatype() != self._refdatatype:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image datatype {} is different from reference ({}).'.format(
                                                        basename(filename),
                                                        img.getDatatype(),
                                                        self._refdatatype))
                                if self._stop: break
                                else: continue
                        # Same Orientation verification
                        if self._reforientation:
                            if img.getOrientationAsString().lower() != self._reforientation:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image orientation {} is different from reference ({}).'.format(
                                                        basename(filename),
                                                        img.getOrientationAsString(),
                                                        self._reforientation))
                                if self._stop: break
                                else: continue
                        # Registered verification
                        if self._refID:
                            if img.getTransforms().hasReferenceID(self._refID):
                                trf = img.getTransformFromID(self._refID)
                                if not trf.hasIdentity():
                                    QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                        '{} image not registered to reference.'.format(
                                                            basename(filename)))
                                    if self._stop: return None
                                    else: continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} does not have {} prefix.'.format(
                                                        basename(filename), self._refprefix))
                                if self._stop: break
                                else: continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} does not have {} suffix.'.format(
                                                        basename(filename), self._refsuffix))
                                if self._stop: break
                                else: continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} does not contains {} string.'.format(
                                                        basename(filename), self._refcontains))
                                if self._stop: break
                                else: continue
                        # Frame verification
                        if self._refframe:
                            if not img.getAcquisition().getFrame():
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image has no frame.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        # Range verification
                        if self._refRange:
                            r = img.display.getRange()
                            if r[0] < self._refRange[0] or r[1] > self._refRange[1]:
                                QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                    '{} image range is not between {} and {} .'.format(
                                                        basename(filename[0]),
                                                        self._refRange[0],
                                                        self._refRange[1]))
                                if self._stop: break
                                else: continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self.containsItem(item):
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                '{} is already in the list.'.format(item.text()))
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe volume index {}\n{}'.format(idx, str(img)))
                            if signal:
                                self.FieldChanged.emit(self, filename)
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            QMessageBox.warning(self, 'PySisyphe volume file selector',
                                                'Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    wait.close()
            # SisypheROI
            elif self._refxroi:
                if not param or paramext != SisypheROI.getFileExt():
                    filt = 'PySisyphe ROI (*.xroi)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select {}PySisyphe ROI(s)'.format(label),
                                                             getcwd(), filt)
                    QApplication.processEvents()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True,
                                      parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add PySisyphe ROIs...')
                        wait.open()
                    for filename in filenames:
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        img = SisypheROI()
                        try: img.load(filename)
                        except:
                            QMessageBox.warning(self, 'File selector',
                                                '{} is not a valid PySisyphe ROI file.'.format(basename(filename)))
                            if self._stop: break
                            else: continue
                        # First volume is reference
                        if self._list.count() == 0:
                            if self._reftofirst: self._volume = img
                            if self._volume is not None:
                                if self._refID is not None:
                                    self._refID = self._volume.getReferenceID()
                                if self._refFOV is not None:
                                    self._refFOV = self._volume.getFieldOfView()
                                if self._refSize is not None:
                                    self._refSize = self._volume.getSize()
                        # Size verification
                        if self._refSize:
                            if img.getSize() != self._refSize:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} ROI size {} is different from reference {}.'.format(
                                                        basename(filename),
                                                        img.getSize(),
                                                        self._refSize))
                                if self._stop: break
                                else: continue
                        # FOV verification
                        if self._refFOV:
                            if img.getFieldOfView() != self._refFOV:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} ROI FOV {} is different from reference {}.'.format(
                                                        basename(filename),
                                                        img.getFieldOfView(),
                                                        self._refFOV))
                                if self._stop: break
                                else: continue
                        # Registered verification
                        if self._refID:
                            if img.getReferenceID() != self._refID:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} ROI is not registered to reference.'.format(basename(filename)))
                                if self._stop: break
                                else: continue
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} does not have {} prefix.'.format(
                                                        basename(filename), self._refprefix))
                                if self._stop: break
                                else: continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} does not have {} suffix.'.format(
                                                        basename(filename), self._refsuffix))
                                if self._stop: break
                                else: continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                    '{} does not contains {} string.'.format(
                                                        basename(filename), self._refcontains))
                                if self._stop: break
                                else: continue
                        # Item already in list ?
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self.containsItem(item):
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                '{} is already in the list.'.format(item.text()))
                        # Add item
                        else:
                            self._list.addItem(item)
                            idx = self._list.row(item)
                            item.setToolTip('PySisyphe ROI index {}\n{}'.format(idx, str(img)))
                            if signal:
                                self.FieldChanged.emit(self, filename)
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            QMessageBox.warning(self, 'PySisyphe ROI file selector',
                                                'Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    wait.close()
            # DICOM
            elif self._refdicom:
                if not param or paramext not in getDicomExt().append(''):
                    filt = 'DICOM (*.dcm *.dicom *.ima *.nema *)'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select DICOM file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True,
                                      parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add DICOM files...')
                        wait.open()
                    for filename in filenames:
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        if isDicom(filename):
                            # Prefix verification
                            if self._refprefix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[:len(self._refprefix)] == self._refprefix:
                                    QMessageBox.warning(self, 'DICOM file selector',
                                                        '{} does not have {} prefix.'.format(
                                                            basename(filename), self._refprefix))
                                    if self._stop: break
                                    else: continue
                            # Suffix verification
                            if self._refsuffix:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if not bname[-len(self._refsuffix):] == self._refsuffix:
                                    QMessageBox.warning(self, 'DICOM file selector',
                                                        '{} does not have {} suffix.'.format(
                                                            basename(filename), self._refsuffix))
                                    if self._stop: break
                                    else: continue
                            # Filename contains verification
                            if self._refcontains:
                                bname = splitext(basename(filename))[0]
                                bname = bname.lower()
                                if bname.find(self._refcontains) > -1:
                                    QMessageBox.warning(self, 'DICOM file selector',
                                                        '{} does not contains {} string.'.format(
                                                            basename(filename), self._refcontains))
                                    if self._stop: break
                                    else: continue
                            path, name = split(filename)
                            item = QListWidgetItem(name)
                            item.setData(256, filename)
                            if self.containsItem(item):
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} is already in the list.'.format(item.text()))
                            else:
                                self._list.addItem(item)
                                if signal:
                                    self.FieldChanged.emit(self, filename)
                                    self.FilesSelectionChanged.emit(self)
                        else:
                            QMessageBox.warning(self, 'DICOM file selector',
                                                '{} is not a valid dicom file.'.format(self._name))
                        if self._list.count() == self._refCount:
                            QMessageBox.warning(self, 'DICOM file selector',
                                                'Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    wait.close()
            # Other file
            else:
                if not param or paramext not in self._refExt:
                    filt = 'Files ('
                    for ext in self._refExt:
                        filt += '*{} '.format(ext)
                    filt = filt.rstrip() + ')'
                    filenames = QFileDialog.getOpenFileNames(self, 'Select file(s)', getcwd(), filt)
                    QApplication.processEvents()
                    filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True,
                                      parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                QMessageBox.warning(self, 'File selector',
                                                    '{} does not have {} prefix.'.format(
                                                        basename(filename), self._refprefix))
                                if self._stop: break
                                else: continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                QMessageBox.warning(self, 'File selector',
                                                    '{} does not have {} suffix.'.format(
                                                        basename(filename), self._refsuffix))
                                if self._stop: break
                                else: continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                QMessageBox.warning(self, 'File selector',
                                                    '{} does not contains {} string.'.format(
                                                        basename(filename), self._refcontains))
                                if self._stop: break
                                else: continue
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self.containsItem(item):
                            QMessageBox.warning(self, 'File selector',
                                                '{} is already in the list.'.format(item.text()))
                        else:
                            self._list.addItem(item)
                            if signal:
                                self.FieldChanged.emit(self, filename)
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            QMessageBox.warning(self, 'File selector',
                                                'Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    wait.close()
        else:
            if not param:
                filt = 'All files (*.*)'
                filenames = QFileDialog.getOpenFileNames(self, 'Select file', getcwd(), filt)
                QApplication.processEvents()
                filenames = filenames[0]
                if len(filenames) > 0 and self._list.count() < self._refCount:
                    chdir(dirname(filenames[0]))
                    wait = DialogWait(progress=True,
                                      progressmin=0,
                                      progressmax=len(filenames),
                                      cancel=True,
                                      parent=self)
                    if len(filenames) > 1:
                        wait.setInformationText('Add files...')
                        wait.open()
                    for filename in filenames:
                        wait.incCurrentProgressValue()
                        wait.setInformationText('Add {}...'.format(basename(filename)))
                        # Prefix verification
                        if self._refprefix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[:len(self._refprefix)] == self._refprefix:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not have {} prefix.'.format(
                                                        basename(filename), self._refprefix))
                                if self._stop: break
                                else: continue
                        # Suffix verification
                        if self._refsuffix:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if not bname[-len(self._refsuffix):] == self._refsuffix:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not have {} suffix.'.format(
                                                        basename(filename), self._refsuffix))
                                if self._stop: break
                                else: continue
                        # Filename contains verification
                        if self._refcontains:
                            bname = splitext(basename(filename))[0]
                            bname = bname.lower()
                            if bname.find(self._refcontains) > -1:
                                QMessageBox.warning(self, 'DICOM file selector',
                                                    '{} does not contains {} string.'.format(
                                                        basename(filename), self._refcontains))
                                if self._stop: break
                                else: continue
                        path, name = split(filename)
                        item = QListWidgetItem(name)
                        item.setData(256, filename)
                        if self.containsItem(item):
                            QMessageBox.warning(self, 'File selector',
                                                '{} is already in the list.'.format(item.text()))
                        else:
                            self._list.addItem(item)
                            if signal:
                                self.FieldChanged.emit(self, filename)
                                self.FilesSelectionChanged.emit(self)
                        if self._list.count() == self._refCount:
                            QMessageBox.warning(self, 'File selector',
                                                'Maximum number of files is reached ({}).\n'
                                                'Remove file from the list if you want to\n'
                                                'add a new one.'.format(self._refCount))
                            self._add.setEnabled(False)
                            break
                    wait.close()

    def clearItem(self, i, signal=True):
        if isinstance(i, int):
            if i < self._list.count():
                self._list.takeItem(i)
                self._add.setEnabled(True)
                if signal:
                    self.FieldCleared.emit(self, [i])
            else: raise ValueError('parameter index is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(i)))

    def clearLastItem(self, signal=True):
        n = self._list.count()
        if n > 0: self._list.takeItem(n - 1)
        self._add.setEnabled(True)
        if signal:
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
            self.FieldCleared.emit(self, rows)
            self.FilesSelectionWidgetCleared.emit(self)

    def clearall(self, signal=True):
        rows = list(range(self._list.count()))
        self._list.clear()
        self._add.setEnabled(True)
        if self.isReferenceVolumeToFirst(): self._volume = None
        if signal:
            self.FieldCleared.emit(self, rows)
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


class SynchronizedFilesSelectionWidget(QWidget):
    """
        SynchronizedFileSelectionWidget class

        Description

            Multiple synchronized widgets for single file selection

        Inheritance

            QWidget -> SynchronizedFileSelectionWidget

        Private attributes

            _lists      list[FileSelectionWidget]

        Custom Qt Signals

        Public methods

            int = getGetNumberOfLists()
            dict[list[str]] = getTitles()
            list[str] = getSingleListTitles()
            list[str] = getMultipleListTitles()
            setSequenceFilters(dict[list[str]])
            dict[list[str]] = getSequenceFilters()
            setModalityFilters(dict[list[str]])
            dict[list[str]] = getModalityFilters()
            setSuffixFilters(dict[list[str]])
            dict[list[str]] = getSuffixFilters()
            setPrefixFilters(dict[list[str]])
            dict[list[str]] = setPrefixFilters()
            setContainsStringFilters(dict[list[str]])
            dict[list[str]] = getContainsStringFilters()
            dict[str] = getFilenames()
            setFilenames(dict[str])
            bool = isReady()

            inherited QWidget methods
    """

    # Special method

    def __init__(self, singles=tuple('Default'), multiples=tuple(), maxcount=100, parent=None):
        super().__init__(parent)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._singles = dict()
        for label in singles:
            flist = FileSelectionWidget(parent=parent)
            flist.filterSisypheVolume()
            flist.setTextLabel(label)
            flist.setLabelVisibility(True)
            flist.FieldCleared.connect(self._ListCleared)
            flist.FieldChanged.connect(self._ListChanged)
            self._singles[label] = flist
            self._layout.addWidget(flist)
        self._multiples = dict()
        for label in multiples:
            flist = FilesSelectionWidget(parent=parent)
            flist.setMaximumNumberOfFiles(maxcount)
            flist.filterSisypheVolume()
            flist.filterSameFOV()
            flist.setTextLabel(label)
            flist.setLabelVisibility(True)
            flist.FieldCleared.connect(self._ListCleared)
            flist.FieldChanged.connect(self._ListChanged)
            self._multiples[label] = flist
            self._layout.addWidget(flist)

        self._FOV = None

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in self._singles: return self._singles[key]
            if key in self._multiples: return self._multiples[key]
        else: raise TypeError('key type {} is not str.'.format(type(key)))

    # Private method

    def _ListChanged(self, widget, filename):
        if filename != '':
            if self._FOV is None:
                name = ''
                if isinstance(widget, FileSelectionWidget): name = widget.getFilename()
                elif isinstance(widget, FilesSelectionWidget): name = widget.getFilenames()[0]
                if exists(name): self._FOV = XmlVolume(name).getFOV()
            else:
                fov = XmlVolume(filename).getFOV()
                if fov != self._FOV:
                    QMessageBox.warning(self, 'PySisyphe volume file selector',
                                        '{} does not have the same FOV as reference.'.format(basename(filename)))
                    widget.clearLastItem(signal=False)

    def _ListCleared(self, widget):
        if self.isEmpty(): self._FOV = None

    # Public methods

    def getGetNumberOfLists(self):
        return len(self._singles) + len(self._muliples)

    def getTitles(self):
        r = dict()
        r['singles'] = list(self._singles.keys())
        r['multiples'] = list(self._multiples.keys())
        return r

    def getSingleListTitles(self):
        return list(self._singles.keys())

    def getMultipleListTitles(self):
        return list(self._multiples.keys())

    def setSequenceFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._singles) > 0:
                if 'singles' in filters:
                    flt = filters['singles']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._singles):
                            for i, (_, flist) in enumerate(self._singles.items()):
                                flist.filterSameSequence(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiples) > 0:
                if 'multiples' in filters:
                    flt = filters['multiples']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiples):
                            for i, (_, flist) in enumerate(self._multiples.items()):
                                flist.filterSameSequence(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getSequenceFilters(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                r1[flist.flist.getLabel()] = flist.getSequenceFilter()
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                r2[flist.flist.getLabel()] = flist.getSequenceFilter()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def setModalityFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._singles) > 0:
                if 'singles' in filters:
                    flt = filters['singles']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._singles):
                            for i, (_, flist) in enumerate(self._singles.items()):
                                flist.filterSameModality(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiples) > 0:
                if 'multiples' in filters:
                    flt = filters['multiples']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiples):
                            for i, (_, flist) in enumerate(self._multiples.items()):
                                flist.filterSameModality(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getModalityFilters(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                r1[flist.getLabel()] = flist.getModalityFilter()
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                r2[flist.getLabel()] = flist.getModalityFilter()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def setSuffixFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._singles) > 0:
                if 'singles' in filters:
                    flt = filters['singles']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._singles):
                            for i, (_, flist) in enumerate(self._singles.items()):
                                flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiples) > 0:
                if 'multiples' in filters:
                    flt = filters['multiples']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiples):
                            for i, (_, flist) in enumerate(self._multiples.items()):
                                flist.filterSuffix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getSuffixFilters(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                r1[self._singles[k].getLabel()] = flist.getSuffixFilter()
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                r2[self._singles[k].getLabel()] = flist.getSuffixFilter()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def setPrefixFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._singles) > 0:
                if 'singles' in filters:
                    flt = filters['singles']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._singles):
                            for i, (_, flist) in enumerate(self._singles.items()):
                                flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiples) > 0:
                if 'multiples' in filters:
                    flt = filters['multiples']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiples):
                            for i, (_, flist) in enumerate(self._multiples.items()):
                                flist.filterPrefix(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getPrefixFilters(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                r1[flist.getLabel()] = flist.getPrefixFilter()
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                r2[flist.getLabel()] = flist.getPrefixFilter()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def setContainsStringFilters(self, filters):
        if isinstance(filters, dict):
            if len(self._singles) > 0:
                if 'singles' in filters:
                    flt = filters['singles']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._singles):
                            for i, (_, flist) in enumerate(self._singles.items()):
                                flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))
            if len(self._multiples) > 0:
                if 'multiples' in filters:
                    flt = filters['multiples']
                    if isinstance(flt, (list, tuple)):
                        if len(flt) == len(self._multiples):
                            for i, (_, flist) in enumerate(self._multiples.items()):
                                flist.filterFilenameContains(flt[i])
                        else: ValueError('wrong number of elements in multiple file selection {}'.format(type(flt)))
                    else: raise TypeError('parameter type {} is not list or tuple.'.format(type(flt)))

    def getContainsStringFilters(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                r1[flist.getLabel()] = flist.getFilenameContainsFilter()
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                r2[flist.getLabel()] = flist.getFilenameContainsFilter()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def getFilenames(self):
        r = dict()
        r1 = dict()
        r2 = dict()
        if len(self._singles) > 0:
            for label, flist in self._singles.items():
                r1[label] = [flist.getFilename()]
        if len(self._multiples) > 0:
            for label, flist in self._multiples.items():
                r2[label] = flist.getFilenames()
        r['singles'] = r1
        r['multiples'] = r2
        return r

    def setFilenames(self, filenames):
        if isinstance(filenames, dict):
            if 'singles' in filenames:
                for label, filename in filenames['singles']:
                    if isinstance(filename, list): filename = filename[0]
                    self._singles[label].open(filename)
            if 'multiples' in filenames:
                for label, filename in filenames['singles']:
                    for file in filename: self._multiples[label].add(file)
        else: raise TypeError('parameter type {} is not dict.'.format(type(filenames)))

    def isReady(self):
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                if flist.isEmpty(): return False
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                if flist.isEmpty(): return False
        return True

    def isEmpty(self):
        return self.isSinglesEmpy() and self.isMultiplesEmpty()

    def isSinglesEmpy(self):
        if len(self._singles) > 0:
            for _, flist in self._singles.items():
                if not flist.isEmpty(): return False
        return True

    def isMultiplesEmpty(self):
        if len(self._multiples) > 0:
            for _, flist in self._multiples.items():
                if not flist.isEmpty(): return False
        return True


if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    lbl1 = ('template',)
    lbl2 = ('structs',)
    main = SynchronizedFilesSelectionWidget(singles=lbl1, multiples=lbl2)
    suffix = {'multiples': ['_gm']}
    main.setSuffixFilters(filters=suffix)
    main.activateWindow()
    main.show()
    app.exec_()
    exit()
