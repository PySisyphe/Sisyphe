"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import exists
from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import abspath

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['DialogBundleROISelection',
           'DialogStreamlinesROISelection',
           'DialogBundleAtlasSelection',
           'DialogStreamlinesAtlasSelection',
           'DialogBundleFilteringSelection',
           'DialogStreamlinesFiltering',
           'DialogStreamlinesClustering',
           'DialogBundleToDensityMap',
           'DialogBundleToPathLengthMap',
           'DialogBundleConnectivityMatrix']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogBundleROISelection 
              -> DialogStreamlinesROISelection
              -> DialogBundleAtlasSelection
              -> DialogStreamlinesAtlasSelection
              -> DialogBundleFilteringSelection
              -> DialogStreamlinesFiltering
              -> DialogStreamlinesClustering
              -> DialogBundleToDensityMap
              -> DialogBundleToPathLengthMap
              -> DialogBundleToConnectivityMatrix
"""


class DialogBundleROISelection(QDialog):
    """
    DialogBundleROISelection class

    Description
    ~~~~~~~~~~~

    GUI dialog window for bundle ROI selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogBundleROISelection

    Creation: 04/04/2024
    Last revision: 19/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Bundle ROI selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.filterWhole()
        self._filetracts.setTextLabel('Tractogram')
        self._filetracts.FieldCleared.connect(lambda _: self._process.setEnabled(False))
        self._filetracts.FieldChanged.connect(lambda _: self._newTractogram())

        self._filerois = FilesSelectionWidget(maxcount=20)
        self._filerois.filterSisypheROI()
        self._filerois.filterSameID()
        self._filerois.FieldCleared.connect(lambda _: self._process.setEnabled(False))
        self._filerois.FieldChanged.connect(lambda _: self._validate())
        self._filerois.setEnabled(False)

        self._toroisettings = FunctionSettingsWidget('BundleROISelection')
        self._toroisettings.settingsVisibilityOn()
        self._toroisettings.hideIOButtons()
        self._toroisettings.setSettingsButtonFunctionText()
        self._toroisettings.setParameterVisibility('Inplace', False)
        self._toroisettings.VisibilityToggled.connect(self._center)

        # < Revision 19/06/2025
        self._bundlename = self._toroisettings.getParameterWidget('BundleName')
        self._bundlename.textChanged.connect(lambda _: self._validate())
        # Revision 19/06/2025 >

        self._layout.addWidget(self._filetracts)
        self._layout.addWidget(self._filerois)
        self._layout.addWidget(self._toroisettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._exit = QPushButton('Close')
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        self._exit.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Bundle ROI selection processing')
        self._process.setEnabled(False)
        layout.addWidget(self._exit)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        self._filerois.setEnabled(not self._filetracts.isEmpty())
        r = self._filetracts.isEmpty() or self._filerois.isEmpty() or self._bundlename.text() == ''
        self._process.setEnabled(not r)

    def _newTractogram(self):
        if not self._filetracts.isEmpty():
            ID = SisypheStreamlines.getReferenceIDfromFile(self._filetracts.getFilename())
            self._filerois.filterSameID(ID)
            self._filerois.setEnabled(True)
        self._filerois.clearall(signal=False)
        self._process.setEnabled(False)

    # Public methods

    def setBundleName(self, bundle: str = ''):
        self._bundlename.setText(bundle)

    def getBundleName(self):
        return self._bundlename.text()

    def setTractogram(self, filename: str | SisypheStreamlines) -> None:
        if isinstance(filename, str):
            if splitext(filename)[1] == SisypheStreamlines.getFileExt() and exists(filename):
                self._filetracts.open(filename)
                ID = SisypheStreamlines.getReferenceIDfromFile(filename)
                self._filerois.filterSameID(ID)
        elif isinstance(filename, SisypheStreamlines):
            self._filerois.filterSameID(filename.getReferenceID())
        self._filerois.clearall(signal=False)
        self._process.setEnabled(False)

    def execute(self):
        # Open tractogram
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
        wait.progressVisibilityOff()
        sl = SisypheStreamlines()
        sl.load(self._filetracts.getFilename())
        # Open ROIs
        wait.setInformationText('Open ROIs...')
        rois = SisypheROICollection()
        rois.load(self._filerois.getFilenames())
        # Selection by Length
        wait.setInformationText('{} length selection...'.format(basename(self._filetracts.getFilename())))
        lgh = self._toroisettings.getParameterValue('MinimalLength')
        sl = sl.getSisypheStreamlinesLongerThan(l=lgh)
        # Selection by ROI
        wait.setInformationText('{} ROI selection...'.format(basename(self._filetracts.getFilename())))
        include = self._filerois.getCheckStateList()
        mode = self._toroisettings.getParameterValue('Mode')
        sl = sl.streamlinesRoiSelection(rois, include, mode, wait=wait)
        # Save bundle
        wait.hide()
        filename = join(dirname(self._filetracts.getFilename()),
                        self._bundlename.text() + SisypheStreamlines.getFileExt())
        filename = QFileDialog.getSaveFileName(self,
                                               'Save streamlines',
                                               filename,
                                               filter=SisypheStreamlines.getFilterExt())[0]
        QApplication.processEvents()
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            wait.show()
            wait.setInformationText('Save {}...'.format(basename(filename)))
            sl.save(filename=filename)
        wait.close()
        """
        Exit  
        """
        r = messageBox(self,
                       title=self.windowTitle(),
                       text='Would you like to do\nmore bundle ROI selection ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes:
            self._filerois.clearall()
            self._bundlename.setText('Tract')
        else: self.accept()


class DialogStreamlinesROISelection(QDialog):
    """
    DialogStreamlinesROISelection class

    Description
    ~~~~~~~~~~~

    GUI dialog window for streamlines ROI selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogStreamlinesROISelection

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Streamlines ROI selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init attribute

        self._id: str = ''
        # < Revision 08/04/2025
        # add _fov attribute
        self._fov: tuple[float, float, float] = 0.0, 0.0, 0.0
        # Revision 08/04/2025 >

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._toroisettings = FunctionSettingsWidget('BundleROISelection')
        self._toroisettings.settingsVisibilityOn()
        self._toroisettings.hideButtons()

        self._rois = QListWidget()
        self._inclrois = QListWidget()
        self._exclrois = QListWidget()
        self._rois.setDragDropMode(self._rois.DragDrop)
        self._inclrois.setDragDropMode(self._rois.DragDrop)
        self._exclrois.setDragDropMode(self._rois.DragDrop)
        self._rois.setDefaultDropAction(Qt.MoveAction)
        self._inclrois.setDefaultDropAction(Qt.MoveAction)
        self._exclrois.setDefaultDropAction(Qt.MoveAction)
        self._rois.setAcceptDrops(True)
        self._inclrois.setAcceptDrops(True)
        self._exclrois.setAcceptDrops(True)
        self._rois.setSelectionMode(self._rois.ExtendedSelection)
        self._inclrois.setSelectionMode(self._rois.ExtendedSelection)
        self._exclrois.setSelectionMode(self._rois.ExtendedSelection)
        self._rois.setToolTip('ROI(s) available for virtual dissection')
        self._inclrois.setToolTip('Inclusion list: ROI(s) used to include streamlines')
        self._exclrois.setToolTip('Exclusion list: ROI(s) used to exclude streamlines')

        self._incladd = IconPushButton('right.png', size=32)
        self._inclremove = IconPushButton('left.png', size=32)
        self._excladd = IconPushButton('right.png', size=32)
        self._exclremove = IconPushButton('left.png', size=32)
        self._incladd.setToolTip('Add selected ROI(s) to inclusion list')
        self._inclremove.setToolTip('Remove selected ROI(s) from inclusion list')
        self._excladd.setToolTip('Add selected ROI(s) to exclusion list')
        self._exclremove.setToolTip('Remove selected ROI(s) from exclusion list')
        # noinspection PyUnresolvedReferences
        self._incladd.clicked.connect(self._addInclusionROI)
        # noinspection PyUnresolvedReferences
        self._inclremove.clicked.connect(self._removeInclusionROI)
        # noinspection PyUnresolvedReferences
        self._excladd.clicked.connect(self._addExclusionROI)
        # noinspection PyUnresolvedReferences
        self._exclremove.clicked.connect(self._removeExclusionROI)

        # < Revision 03/04/2025
        self._openroi = QPushButton('Add ROI(s)')
        self._openroi.setToolTip('Add ROI(s) from disk.')
        # noinspection PyUnresolvedReferences
        self._openroi.clicked.connect(self._addROIfromDisk)
        # Revision 03/04/2025 >

        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(10)
        self._grid.addWidget(self._rois, 0, 0, 4, 1)
        self._grid.addWidget(self._incladd, 0, 1, 1, 1)
        self._grid.addWidget(self._inclremove, 1, 1, 1, 1)
        self._grid.addWidget(self._excladd, 2, 1, 1, 1)
        self._grid.addWidget(self._exclremove, 3, 1, 1, 1)
        self._grid.addWidget(self._inclrois, 0, 2, 2, 1)
        self._grid.addWidget(self._exclrois, 2, 2, 2, 1)
        # < Revision 03/04/2025
        self._grid.addWidget(self._openroi, 4, 0, 1, 1)
        # Revision 03/04/2025 >

        self._layout.addLayout(self._grid)
        self._layout.addWidget(self._toroisettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)

        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self._accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._toroisettings.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    def _addInclusionROI(self):
        if self._rois.count() > 0:
            selected = self._rois.selectedItems()
            if len(selected) > 0:
                for item in selected:
                    item = self._rois.findItems(item.text(), Qt.MatchExactly)[0]
                    item = self._rois.takeItem(self._rois.row(item))
                    # < Revision 03/04/2025
                    # self._inclrois.addItem(item.text())
                    self._inclrois.addItem(item)
                    # Revision 03/04/2025 >
                self._inclrois.sortItems()

    def _removeInclusionROI(self):
        if self._inclrois.count() > 0:
            selected = self._inclrois.selectedItems()
            if len(selected) > 0:
                for item in selected:
                    item = self._inclrois.findItems(item.text(), Qt.MatchExactly)[0]
                    item = self._inclrois.takeItem(self._inclrois.row(item))
                    # < Revision 03/04/2025
                    # self._rois.addItem(item.text())
                    self._rois.addItem(item)
                    # Revision 03/04/2025 >
                self._rois.sortItems()

    def _addExclusionROI(self):
        if self._rois.count() > 0:
            selected = self._rois.selectedItems()
            if len(selected) > 0:
                for item in selected:
                    item = self._rois.findItems(item.text(), Qt.MatchExactly)[0]
                    item = self._rois.takeItem(self._rois.row(item))
                    # < Revision 03/04/2025
                    # self._exclrois.addItem(item.text())
                    self._exclrois.addItem(item)
                    # Revision 03/04/2025 >
                self._exclrois.sortItems()

    def _removeExclusionROI(self):
        if self._exclrois.count() > 0:
            selected = self._exclrois.selectedItems()
            if len(selected) > 0:
                for item in selected:
                    item = self._exclrois.findItems(item.text(), Qt.MatchExactly)[0]
                    item = self._exclrois.takeItem(self._exclrois.row(item))
                    # < Revision 03/04/2025
                    # self._rois.addItem(item.text())
                    self._rois.addItem(item)
                    # Revision 03/04/2025 >
                self._rois.sortItems()

    def _addROIfromDisk(self):
        title = 'Open ROI(s)'
        filt = 'ROI (*{})'.format(SisypheROI.getFileExt())
        filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            for filename in filenames:
                filename = abspath(filename)
                if exists(filename):
                    chdir(dirname(filename))
                    roi = SisypheROI()
                    roi.load(filename)
                    cid = self._id
                    if roi.getReferenceID() != cid:
                        if roi.getFieldOfView(decimals=1) == self._fov:
                            if messageBox(self, title, 'Invalid ROI ID, but FOV is compatible.\n'
                                                    'Do you still want to load ROI?',
                                          icon=QMessageBox.Question,
                                          buttons=QMessageBox.Yes | QMessageBox.No,
                                          default=QMessageBox.No) == QMessageBox.Yes:
                                cid = roi.getReferenceID()
                        else:
                            messageBox(self, title, 'Invalid ROI ID {} and FOV {}\n'
                                                    '({} and {} are required).'.format(roi.getReferenceID(),
                                                                                       roi.getFieldOfView(decimals=1),
                                                                                       self._id, self._fov))
                    if roi.getReferenceID() == cid:
                        r = self._rois.findItems(roi.getName(), Qt.MatchExactly)
                        if len(r) == 0:
                            item = QListWidgetItem(roi.getName())
                            item.setData(Qt.UserRole, dirname(filename))
                            item.setToolTip('{}'.format(str(roi)[:-1]))
                            self._rois.addItem(item)
                            self._rois.sortItems()
                        else:
                            messageBox(self, title, 'ROI {} is already opened.'.format(roi.getName()))

    def _accept(self):
        if self._inclrois.count() > 0 or self._exclrois.count() > 0: self.accept()
        else: messageBox(self, self.windowTitle(), 'No ROI selected.')

    # Public methods

    # < Revision 03/04/2025
    def setReferenceID(self, refid: str | SisypheVolume | SisypheROI | SisypheStreamlines):
        if isinstance(refid, SisypheVolume): refid = refid.getID()
        elif isinstance(refid, (SisypheROI, SisypheStreamlines)): refid = refid.getReferenceID()
        if isinstance(refid, str): self._id = refid
        else: raise TypeError('Invalid type {} for reference ID.'.format(type(refid)))
    # Revision 03/04/2025 >

    # < Revision 03/04/2025
    def getReferenceID(self):
        return self._id
    # Revision 03/04/2025 >

    # < Revision 08/04/2025
    def setReferenceFOV(self, fov = tuple[float, float, float] | SisypheVolume | SisypheROI | SisypheStreamlines):
        if isinstance(fov, (SisypheVolume, SisypheROI)): fov = fov.getFieldOfView()
        elif isinstance(fov, SisypheStreamlines): fov = fov.getDWIFOV()
        if isinstance(fov, tuple): self._fov = fov[:3]
        else: raise TypeError('Invalid parameter type {}'.format(type(fov)))
    # Revision 08/04/2025 >

    # < Revision 08/04/2025
    def getReferenceFOV(self):
        return self._fov
    # Revision 08/04/2025 >

    def clear(self):
        self._rois.clear()
        self._inclrois.clear()
        self._exclrois.clear()

    def addROINames(self, names: list[str]):
        self.clear()
        # < Revision 03/04/2025
        # self._rois.addItems(names)
        for name in names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, '')
            self._rois.addItem(item)
        # Revision 03/04/2025 >
        self._rois.sortItems()

    def getInclusionROINames(self) -> list[str]:
        r = list()
        n = self._inclrois.count()
        if n > 0:
            for i in range(n):
                # < Revision 03/04/2025
                # r.append(self._inclrois.item(i).text())
                path = self._inclrois.item(i).data(Qt.UserRole)
                if path == '': r.append(self._inclrois.item(i).text())
                else:
                    path = str(join(path, self._inclrois.item(i).text() + SisypheROI.getFileExt()))
                    if exists(path): r.append(path)
                # Revision 03/04/2025 >
        return r

    def getExclusionROINames(self):
        r = list()
        n = self._exclrois.count()
        if n > 0:
            for i in range(n):
                # < Revision 03/04/2025
                # r.append(self._exclrois.item(i).text())
                path = self._exclrois.item(i).data(Qt.UserRole)
                if path == '': r.append(self._exclrois.item(i).text())
                else:
                    path = str(join(path, self._exclrois.item(i).text() + SisypheROI.getFileExt()))
                    if exists(path): r.append(path)
                # Revision 03/04/2025 >
        return r

    def getMinimalLength(self) -> float:
        return self._toroisettings.getParameterValue('MinimalLength')

    def setMinimalLength(self, v: float) -> None:
        self._toroisettings.getParameterWidget('MinimalLength').setValue(v)

    def getBundleName(self) -> str:
        return self._toroisettings.getParameterValue('BundleName')

    def setBundleName(self, name: str) -> None:
        self._toroisettings.getParameterWidget('BundleName').setText(name)

    def getSelectionMode(self):
        r = self._toroisettings.getParameterValue('Mode')[0]
        if r in ['All', 'Any']: return r.lower()
        elif r == 'End': return 'either_end'
        else: return 'any'

    def setSelectionModeToAny(self):
        self._toroisettings.getParameterWidget('Mode').setCurrentText('Any')

    def setSelectionModeToEnd(self):
        self._toroisettings.getParameterWidget('Mode').setCurrentText('End')

    def setSelectionModeToAll(self):
        self._toroisettings.getParameterWidget('Mode').setCurrentText('All')

    def getInPlace(self):
        return self._toroisettings.getParameterWidget('Inplace').isChecked()

    def setInPlace(self, v: bool):
        self._toroisettings.getParameterWidget('Inplace').setChecked(v)

    # < Revision 03/04/2025
    def setInPlaceVisibility(self, v: bool):
        self._toroisettings.setParameterVisibility('Inplace', v)
    # Revision 03/04/2025 >

    # < Revision 03/04/2025
    def inPlaceVisibilityOn(self):
        self.setInPlaceVisibility(True)
    # Revision 03/04/2025 >

    # < Revision 03/04/2025
    def inPlaceVisibilityOff(self):
        self.setInPlaceVisibility(False)
    # Revision 03/04/2025 >


class DialogBundleAtlasSelection(QDialog):
    """
    DialogBundleAtlasSelection

    Description
    ~~~~~~~~~~~

    GUI dialog window for bundle atlas selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogBundleAtlasSelection

    Creation: 21/04/2024
    Last revision: 19/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Bundle Atlas selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.filterWhole()
        self._filetracts.setTextLabel('Tractogram')
        self._filetracts.FieldChanged.connect(lambda: self._validate())
        self._filetracts.FieldCleared.connect(lambda _: self._process.setEnabled(False))

        self._atlas = QListWidget()
        self._atlas.setToolTip('Atlas bundles')
        # noinspection PyUnresolvedReferences
        self._atlas.itemClicked.connect(lambda: self._validate())
        self._initAtlas()

        # < Revision 19/06/2025
        # self._bundlename = LabeledLineEdit(label='Bundle name')
        # self._bundlename.textChanged.connect(lambda _: self._validate())
        # Revision 19/06/2025 >

        self._settings = FunctionSettingsWidget('BundleAtlasSelection')
        self._settings.settingsVisibilityOn()
        self._settings.hideIOButtons()
        self._settings.setSettingsButtonFunctionText()
        self._settings.VisibilityToggled.connect(self._center)
        self._refine = self._settings.getParameterWidget('Refine')
        self._refine.clicked.connect(self._refineChanged)

        self._layout.addWidget(self._filetracts)
        self._layout.addWidget(self._atlas)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._exit = QPushButton('Close')
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        self._exit.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Bundle atlas selection processing')
        self._process.setEnabled(False)
        layout.addWidget(self._exit)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        r = self._filetracts.isEmpty() or len(self.getAtlasBundlesChecked()) == 0
        self._process.setEnabled(not r)

    def _initAtlas(self):
        bundles = SisypheStreamlines.getAtlasBundleNames(whole=False)
        for bundle in bundles:
            item = QListWidgetItem(bundle)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self._atlas.addItem(item)

    def _refineChanged(self):
        v = self._refine.isChecked()
        self._settings.setParameterVisibility('RefineReductionThreshold', v)
        self._settings.setParameterVisibility('RefinePruningThreshold', v)
        self._center(None)

    # Public methods

    def getAtlasBundlesChecked(self) -> list[str]:
        checked = list()
        for i in range(self._atlas.count()):
            item = self._atlas.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def getMinimalLength(self) -> float:
        return self._settings.getParameterValue('MinimalLength')

    def getClusteringThreshold(self) -> float:
        return self._settings.getParameterValue('ClusteringThreshold')

    def getReductionThreshold(self) -> float:
        return self._settings.getParameterValue('ReductionThreshold')

    def getPruningThreshold(self) -> float:
        return self._settings.getParameterValue('PruningThreshold')

    def getReductionMetric(self) -> str:
        return self._settings.getParameterValue('ReductionMetric')[0][:3]

    def getPruningMetric(self) -> str:
        return self._settings.getParameterValue('PruningMetric')[0][:3]

    def getRefine(self) -> bool:
        return self._settings.getParameterValue('Refine')

    def getRefineReductionThreshold(self) -> float:
        return self._settings.getParameterValue('RefineReductionThreshold')

    def getRefinePruningThreshold(self) -> float:
        return self._settings.getParameterValue('RefinePruningThreshold')

    def execute(self):
        checked = self.getAtlasBundlesChecked()
        if len(checked) > 0:
            # Open tractogram
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
            wait.progressVisibilityOff()
            sl = SisypheStreamlines()
            sl.load(self._filetracts.getFilename())
            if not sl.isAtlas():
                # Atlas coregistration
                if not sl.isAtlasRegistered():
                    try:
                        wait.addInformationText('Atlas to {} coregistration...'.format(sl.getName()))
                        sl.atlasRegistration()
                        wait.addInformationText('Save {} tractogram...'.format(sl.getName()))
                        sl.save()
                    except Exception as err:
                        wait.close()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Atlas coregitration error\n{}'.format(err))
                        self._filetracts.clear()
                        for i in range(self._atlas.count()):
                            item = self._atlas.item(i)
                            # noinspection PyTypeChecker
                            item.setCheckState(Qt.Unchecked)
                        return
                # Selection by atlas
                wait.setInformationText('{} atlas selection...'.format(basename(self._filetracts.getFilename())))
                threshold = self._settings.getParameterValue('ClusteringThreshold')
                reduction = self._settings.getParameterValue('ReductionThreshold')
                pruning = self._settings.getParameterValue('PruningThreshold')
                # < Revision 19/06/2025
                # bug fix, incorrect reductiondist and pruningdist values
                # reductiondist = self._settings.getParameterValue('ReductionMetric')
                # pruningdist = self._settings.getParameterValue('PruningMetric')
                reductiondist = self._settings.getParameterValue('ReductionMetric')[0]
                if reductiondist is not None: reductiondist = reductiondist[:3]
                if reductiondist not in ('mdf', 'mam'): reductiondist = 'mdf'
                pruningdist = self._settings.getParameterValue('PruningMetric')[0]
                if pruningdist is not None: pruningdist = pruningdist[:3]
                if pruningdist not in ('mdf', 'mam'): pruningdist = 'mdf'
                # Revision 19/06/2025 >
                refine = self._settings.getParameterValue('Refine')
                refinereduction = self._settings.getParameterValue('RefineReductionThreshold')
                refinepruning = self._settings.getParameterValue('RefinePruningThreshold')
                minlength = self._settings.getParameterValue('MinimalLength')
                try:
                    for name in checked:
                        filename = SisypheStreamlines.getAtlasBundleFilenameFromName(name)
                        if filename is not None and exists(filename):
                            slatlas = SisypheStreamlines()
                            slatlas.load(filename)
                            wait.addInformationText('{} streamlines selection...'.format(name))
                            sl2 = sl.streamlinesFromAtlas(slatlas,
                                                          threshold=threshold,
                                                          reduction=reduction,
                                                          pruning=pruning,
                                                          reductiondist=reductiondist,
                                                          pruningdist=pruningdist,
                                                          refine=refine,
                                                          refinereduction=refinereduction,
                                                          refinepruning=refinepruning,
                                                          minlength=minlength,
                                                          wait=wait)
                            # Save bundle
                            filename = join(dirname(self._filetracts.getFilename()),
                                            splitext(basename(self._filetracts.getFilename()))[0] +
                                            '_' + name + SisypheStreamlines.getFileExt())
                            wait.hide()
                            filename = QFileDialog.getSaveFileName(self,
                                                                   'Save bundle',
                                                                   filename,
                                                                   filter=SisypheStreamlines.getFilterExt())[0]
                            QApplication.processEvents()
                            if filename:
                                filename = abspath(filename)
                                chdir(dirname(filename))
                                wait.show()
                                wait.setInformationText('Save {}...'.format(basename(filename)))
                                # noinspection PyTypeChecker
                                sl2.save(filename=filename)
                except Exception as err:
                    wait.hide()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Atlas selection error\n{}'.format(err))
                wait.close()
                """
                Exit  
                """
                r = messageBox(self,
                               title=self.windowTitle(),
                               text='Would you like to do\nmore bundle atlas selection ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._filetracts.clear()
                else: self.accept()
            else:
                messageBox(self,
                           title=self.windowTitle(),
                           text='{} is an ICBM152 atlas tractogram.')
                wait.close()
                self._filetracts.clear()
        else:
            messageBox(self,
                       title=self.windowTitle(),
                       text='No atlas bundles checked.')


class DialogStreamlinesAtlasSelection(QDialog):
    """
    DialogStreamlinesAtlasSelection

    Description
    ~~~~~~~~~~~

    GUI dialog window for streamlines atlas selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogStreamlinesAtlasSelection

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Streamlines atlas selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._settings = FunctionSettingsWidget('BundleAtlasSelection')
        self._settings.settingsVisibilityOn()
        self._settings.hideButtons()
        self._refine = self._settings.getParameterWidget('Refine')
        self._refine.clicked.connect(self._refineChanged)

        self._atlas = QListWidget()
        self._atlas.setToolTip('Atlas bundles')
        self._initAtlas()

        self._layout.addWidget(self._atlas)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)

        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._settings.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _initAtlas(self):
        bundles = SisypheStreamlines.getAtlasBundleNames(whole=False)
        for bundle in bundles:
            item = QListWidgetItem(bundle)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self._atlas.addItem(item)

    def _refineChanged(self):
        v = self._refine.isChecked()
        self._settings.setParameterVisibility('RefineReductionThreshold', v)
        self._settings.setParameterVisibility('RefinePruningThreshold', v)
        self._center(None)

    # Public methods

    def getAtlasBundlesChecked(self) -> list[str]:
        checked = list()
        for i in range(self._atlas.count()):
            item = self._atlas.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def getMinimalLength(self) -> float:
        return self._settings.getParameterValue('MinimalLength')

    def getClusteringThreshold(self) -> float:
        return self._settings.getParameterValue('ClusteringThreshold')

    def getReductionThreshold(self) -> float:
        return self._settings.getParameterValue('ReductionThreshold')

    def getPruningThreshold(self) -> float:
        return self._settings.getParameterValue('PruningThreshold')

    def getReductionMetric(self) -> str:
        return self._settings.getParameterValue('ReductionMetric')[0][:3]

    def getPruningMetric(self) -> str:
        return self._settings.getParameterValue('PruningMetric')[0][:3]

    def getRefine(self) -> bool:
        return self._settings.getParameterValue('Refine')

    def getRefineReductionThreshold(self) -> float:
        return self._settings.getParameterValue('RefineReductionThreshold')

    def getRefinePruningThreshold(self) -> float:
        return self._settings.getParameterValue('RefinePruningThreshold')


class DialogBundleFilteringSelection(QDialog):
    """
    DialogBundleFiltering

    Description
    ~~~~~~~~~~~

    GUI dialog window for bhundle filtering.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogStreamlinesFiltering

    Creation: 21/04/2024
    Last revision: 19/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Bundle filtering selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.filterNotWhole()
        self._filetracts.setTextLabel('Streamlines')
        self._filetracts.FieldChanged.connect(lambda _: self._validate())
        self._filetracts.FieldCleared.connect(lambda _: self._process.setEnabled(False))

        # < Revision 19/06/2025
        # self._bundlename = LabeledLineEdit(label='Bundle name')
        # self._bundlename.textChanged.connect(lambda _: self._validate())
        # Revision 19/06/2025 >

        self._settings = FunctionSettingsWidget('BundleFiltering')
        self._settings.settingsVisibilityOn()
        self._settings.hideIOButtons()
        self._settings.setSettingsButtonFunctionText()
        self._settings.setParameterVisibility('Inplace', False)
        self._settings.VisibilityToggled.connect(self._center)

        # < Revision 19/06/2025
        self._bundlename = self._settings.getParameterWidget('BundleName')
        self._bundlename.textChanged.connect(lambda _: self._validate())
        # Revision 19/06/2025 >

        self._layout.addWidget(self._filetracts)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._exit = QPushButton('Close')
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        self._exit.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Bundle filtering selection processing')
        self._process.setEnabled(False)
        layout.addWidget(self._exit)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        r = self._filetracts.isEmpty() or self._bundlename.text() == 0
        self._process.setEnabled(not r)

    # Public method

    def getMinimalStreamlinesLength(self) -> float:
        return self._settings.getParameterValue('Length')

    def getMaximumDistance(self) -> float:
        return self._settings.getParameterValue('MaximumDistance')

    def getClusterConfidenceThreshold(self) -> float:
        return self._settings.getParameterValue('Threshold')

    def getPower(self) -> float:
        return self._settings.getParameterValue('Power')

    def getStreamlinesSampling(self) -> int:
        return self._settings.getParameterValue('Subsampling')

    def execute(self):
        # Open tractogram
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
        wait.progressVisibilityOff()
        sl = SisypheStreamlines()
        sl.load(self._filetracts.getFilename())
        # Selection by Length
        wait.setInformationText('{} length selection...'.format(basename(self._filetracts.getFilename())))
        lgh = self._settings.getParameterValue('Length')
        sl = sl.getSisypheStreamlinesLongerThan(l=lgh)
        # Selection by filter
        wait.setInformationText('{} filtering selection...'.format(basename(self._filetracts.getFilename())))
        mdf = self._settings.getParameterValue('MaximumDistance')
        power = self._settings.getParameterValue('Power')
        ccithreshold = self._settings.getParameterValue('Threshold')
        subsample = self._settings.getParameterValue('Subsampling')
        try:
            sl = sl.streamlinesClusterConfidenceFiltering(mdf=mdf,
                                                          subsample=subsample,
                                                          power=power,
                                                          ccithreshold=ccithreshold)
        except Exception as err:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{}'.format(err))
            self._filetracts.clear()
            return
        # Save bundle
        wait.hide()
        filename = join(dirname(self._filetracts.getFilename()),
                        self._bundlename.text() + SisypheStreamlines.getFileExt())
        filename = QFileDialog.getSaveFileName(self,
                                               'Save bundle',
                                               filename,
                                               filter=SisypheStreamlines.getFilterExt())[0]
        QApplication.processEvents()
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            wait.show()
            wait.setInformationText('Save {}...'.format(basename(filename)))
            sl.save(filename=filename)
        wait.close()
        """
        Exit  
        """
        r = messageBox(self,
                       title=self.windowTitle(),
                       text='Would you like to do\nmore bundle filtering selection ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes:
            self._filetracts.clear()
            self._bundlename.setText('Tract')
        else: self.accept()


class DialogStreamlinesFiltering(QDialog):
    """
    DialogStreamlinesFiltering

    Description
    ~~~~~~~~~~~

    GUI dialog window for streamlines filtering.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogStreamlinesFiltering

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Streamlines cluster confidence filtering')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._settings = FunctionSettingsWidget('BundleFiltering')
        self._settings.settingsVisibilityOn()
        self._settings.hideButtons()

        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)

        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._settings.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)

    # Public methods

    def getMinimalStreamlinesLength(self) -> float:
        return self._settings.getParameterValue('Length')

    def getMaximumDistance(self) -> float:
        return self._settings.getParameterValue('MaximumDistance')

    def getClusterConfidenceThreshold(self) -> float:
        return self._settings.getParameterValue('Threshold')

    def getPower(self) -> float:
        return self._settings.getParameterValue('Power')

    def getStreamlinesSampling(self) -> int:
        return self._settings.getParameterValue('Subsampling')

    def getInPlace(self) -> bool:
        return self._settings.getParameterValue('Inplace')


class DialogStreamlinesClustering(QDialog):
    """
    DialogStreamlinesClustering

    Description
    ~~~~~~~~~~~

    GUI dialog window for streamlines clustering.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogStreamlinesClustering

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Streamlines clustering')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._settings = FunctionSettingsWidget('BundleClustering')
        self._settings.settingsVisibilityOn()
        self._settings.hideButtons()
        self._settings.getParameterWidget('Metric').currentTextChanged.connect(self._metricChanged)

        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)

        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._settings.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)

    # Private methods

    def _metricChanged(self, metric: str) -> None:
        c = metric[:2]
        w = self._settings.getParameterWidget('Threshold')
        # Average pointwise euclidean distance
        if c == 'Av':
            w.setRange(1.0, 50.0)
            w.setValue(10.0)
        # Center of mass euclidean distance
        elif c == 'Ce':
            w.setRange(1.0, 50.0)
            w.setValue(5.0)
        # Midpoint euclidean distance
        elif c == 'Mi':
            w.setRange(1.0, 50.0)
            w.setValue(5.0)
        # Length
        elif c == 'Le':
            pass
        # Angle between vector endpoint
        elif c == 'An':
            w.setRange(1.0, 90.0)
            w.setValue(80.0)
        else: raise ValueError('Invalid metric parameter.')

    # Public methods

    def getMinimalStreamlinesLength(self) -> float:
        return self._settings.getParameterValue('Length')

    def getMetric(self) -> str:
        c = self._settings.getParameterWidget('Metric').currentText()[:2]
        # Average pointwise euclidean distance
        if c == 'Av': return 'apd'
        # Center of mass euclidean distance
        elif c == 'Ce': return 'cmd'
        # Midpoint euclidean distance
        elif c == 'Mi': return 'mpd'
        # Length
        elif c == 'Le': return 'lgh'
        # Angle between vector endpoint
        elif c == 'An': return 'ang'
        else: raise ValueError('Invalid metric parameter.')

    def getMetricThreshold(self) -> float:
        return self._settings.getParameterValue('Threshold')

    def getStreamlinesSampling(self) -> int:
        return self._settings.getParameterValue('Subsampling')

    def getMinimalClusterSize(self) -> int:
        return self._settings.getParameterValue('ClusterSize')

    def getCentroidProcessing(self) -> bool:
        return self._settings.getParameterValue('Centroid')

    def setClusteringMode(self) -> None:
        self._settings.setParameterVisibility('Metric', True)
        self._settings.setParameterVisibility('ClusterSize', True)

    def setCentroidMode(self) -> None:
        self._settings.setParameterVisibility('Metric', False)
        self._settings.setParameterVisibility('ClusterSize', False)
        self.adjustSize()


class DialogBundleToDensityMap(QDialog):
    """
    DialogBundleToDensityMap

    Description
    ~~~~~~~~~~~

    GUI dialog window to process a density map from a bundle.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogBundleToDensityMap

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ID = None

        # Init window

        self.setWindowTitle('Density map processing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.filterNotWhole()
        self._filetracts.setTextLabel('Streamlines')
        self._filetracts.FieldChanged.connect(self._validate)
        self._filetracts.FieldCleared.connect(self._validate)

        self._layout.addWidget(self._filetracts)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Density map processing')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._filetracts.FieldCleared.connect(lambda _: self._process.setEnabled(False))
        self._filetracts.FieldChanged.connect(lambda _: self._process.setEnabled(True))

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        self._process.setEnabled(not self._filetracts.isEmpty())

    # Public methods

    def setTractogram(self, filename: str) -> None:
        if splitext(filename)[1] == SisypheStreamlines.getFileExt() and exists(filename):
            self._filetracts.open(filename)
            self._validate()

    def execute(self):
        # Open bundle
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
        wait.progressVisibilityOff()
        sl = SisypheStreamlines()
        sl.load(self._filetracts.getFilename())
        # Density map
        wait.setInformationText('{} density map processing...'.format(basename(self._filetracts.getFilename())))
        try: r = sl.streamlinesToDensityMap()
        except Exception as err:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{}'.format(err))
            self._filetracts.clear()
            return
        # Save map
        wait.hide()
        filename = splitext(self._filetracts.getFilename())[0] + SisypheVolume.getFileExt()
        r.setFilename(filename)
        r.setFilenamePrefix('density')
        filename = QFileDialog.getSaveFileName(self,
                                               'Save density map',
                                               r.getFilename(),
                                               filter=SisypheVolume.getFilterExt())[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            wait.show()
            wait.setInformationText('Save {}...'.format(basename(filename)))
            r.saveAs(filename)
        wait.close()
        """
        Exit  
        """
        r = messageBox(self,
                       title=self.windowTitle(),
                       text='Would you like to do\nmore density map ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes: self._filetracts.clear()
        else: self.accept()


class DialogBundleToPathLengthMap(QDialog):
    """
    DialogBundleToPathLengthMap

    Description
    ~~~~~~~~~~~

    GUI dialog window to process a path length map from a bundle and a reference ROI.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogBundleToPathLengthMap

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ID = None

        # Init window

        self.setWindowTitle('Path length map processing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.filterNotWhole()
        self._filetracts.setTextLabel('Streamlines')
        self._filetracts.FieldCleared.connect(lambda _: self._validate())
        self._filetracts.FieldChanged.connect(lambda _: self._validate())

        self._fileroi = FileSelectionWidget()
        self._fileroi.filterSisypheROI()
        self._fileroi.setTextLabel('Reference ROI')
        self._fileroi.alignLabels(self._filetracts)
        self._fileroi.setEnabled(False)
        self._fileroi.FieldChanged.connect(lambda _: self._validate())
        self._fileroi.setToolTip('Reference ROI for path length processing.')

        self._layout.addWidget(self._filetracts)
        self._layout.addWidget(self._fileroi)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Path length map processing')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        if self._filetracts.isEmpty():
            self._fileroi.clear(signal=False)
            self._fileroi.setEnabled(False)
            self._process.setEnabled(False)
        else:
            self._fileroi.setEnabled(True)
            ID = SisypheStreamlines.getReferenceIDfromFile(self._filetracts.getFilename())
            if ID != self._fileroi.getIDFilter(): self._fileroi.filterSameID(ID)
            self._process.setEnabled(not self._fileroi.isEmpty())

    # Public methods

    def setTractogram(self, filename: str) -> None:
        if splitext(filename)[1] == SisypheStreamlines.getFileExt() and exists(filename):
            self._filetracts.open(filename)
            self._validate()

    def execute(self):
        # Open bundle
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
        wait.progressVisibilityOff()
        sl = SisypheStreamlines()
        sl.load(self._filetracts.getFilename())
        roi = SisypheROI()
        roi.load(self._fileroi.getFilename())
        # Path length map
        wait.setInformationText('{} path length map processing...'.format(basename(self._filetracts.getFilename())))
        try: r = sl.streamlinesToPathLengthMap(roi)
        except Exception as err:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{}'.format(err))
            self._filetracts.clear()
            self._fileroi.clear()
            return
        # Save map
        wait.hide()
        filename = splitext(self._filetracts.getFilename())[0] + SisypheVolume.getFileExt()
        r.setFilename(filename)
        r.setFilenamePrefix('pathlength')
        filename = QFileDialog.getSaveFileName(self,
                                               'Save path length map',
                                               r.getFilename(),
                                               filter=SisypheVolume.getFilterExt())[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            wait.show()
            wait.setInformationText('Save {}...'.format(basename(filename)))
            r.saveAs(filename)
        wait.close()
        """
        Exit  
        """
        r = messageBox(self,
                       title=self.windowTitle(),
                       text='Would you like to do\nmore path length map ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes:
            self._filetracts.clear()
            self._fileroi.clear()
        else: self.accept()


class DialogBundleConnectivityMatrix(QDialog):
    """
    DialogBundleConnectivityMatrix

    Description
    ~~~~~~~~~~~

    GUI dialog window to process a connectivity matrix from a bundle.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogBundleConnectivityMatrix

    Creation: 04/04/2024
    Last revision: 13/06/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ID = None
        self._sshot = None

        # Init window

        self.setWindowTitle('Connectivity matrix processing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._filetracts = FileSelectionWidget()
        self._filetracts.filterSisypheStreamlines()
        self._filetracts.setTextLabel('Streamlines')
        self._filetracts.FieldCleared.connect(lambda _: self._validate())
        self._filetracts.FieldChanged.connect(lambda _: self._validate())

        self._filelabel = FileSelectionWidget()
        self._filelabel.filterSisypheVolume()
        self._filelabel.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._filelabel.setTextLabel('Label volume')
        self._filelabel.alignLabels(self._filetracts)
        self._filelabel.setEnabled(False)
        self._filelabel.FieldChanged.connect(lambda _: self._validate())
        self._filelabel.setToolTip('Label volume.')

        self._settings = FunctionSettingsWidget('BundleConnectivityMatrix')
        self._settings.settingsVisibilityOn()
        self._settings.hideIOButtons()
        self._settings.setSettingsButtonFunctionText()

        self._layout.addWidget(self._filetracts)
        self._layout.addWidget(self._filelabel)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Connectivity matrix processing')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._filetracts.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)
        # self.show()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _validate(self):
        if self._filetracts.isEmpty():
            self._filelabel.clear(signal=False)
            self._filelabel.setEnabled(False)
            self._process.setEnabled(False)
        else:
            self._filelabel.setEnabled(True)
            ID = SisypheStreamlines.getReferenceIDfromFile(self._filetracts.getFilename())
            if ID != self._filetracts.getIDFilter(): self._filelabel.filterSameID(ID)
            self._process.setEnabled(not self._filelabel.isEmpty())

    # Public methods

    def setScreenshotsWidget(self, widget: ScreenshotsGridWidget) -> None:
        if isinstance(widget, ScreenshotsGridWidget): self._sshot = widget
        else: raise TypeError('parameter type {} is not ScreenshotsGridWidget.'.format(type(widget)))

    def setTractogram(self, filename: str) -> None:
        if splitext(filename)[1] == SisypheStreamlines.getFileExt() and exists(filename):
            self._filetracts.open(filename)
            self._validate()

    def execute(self):
        # Open bundle
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Open {}...'.format(basename(self._filetracts.getFilename())))
        wait.progressVisibilityOff()
        sl = SisypheStreamlines()
        sl.load(self._filetracts.getFilename())
        vol = SisypheVolume()
        vol.load(self._filelabel.getFilename())
        length = self._settings.getParameterValue('BundleLength')
        if length is None: length = 10.0
        v = self._settings.getParameterValue('Values')[0][0]
        # Connectivity matrix
        try:
            wait.setInformationText('{} select streamlines longer than 10 mm...'.format(basename(self._filetracts.getFilename())))
            sl = sl.getSisypheStreamlinesLongerThan(l=length)
            wait.setInformationText('{} connectivity matrix processing...'.format(basename(self._filetracts.getFilename())))
            r = sl.streamlinesToConnectivityMatrix(vol)
        except Exception as err:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{}'.format(err))
            self._filetracts.clear()
            self._filelabel.clear()
            return
        # Display connectivity matrix
        dlg = DialogGenericResults()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(dlg, c)
        npr = r.to_numpy()[1:, 1:]
        if v != 'A':
            mat = np.zeros(npr.shape, dtype='float32')
            for i in range(mat.shape[0]):
                if npr[i, i] > 0.0:
                    mat[i, i:-1] = npr[i, i:-1] / npr[i, i]
            npr = mat + mat.T  + np.diag(np.ones(mat.shape[0]))
            npr[npr > 1.0] = 1.0
        labels = list(vol.acquisition.getLabels().values())
        title1 = 'Connectivity matrix'.format(sl.getBundle(0).getName())
        title2 = 'Connectivity table'.format(sl.getBundle(0).getName())
        tab1 = dlg.newTab(title1, capture=True, clipbrd=True, scrshot=self._sshot, dataset=False)
        tab2 = dlg.newTab(title2, capture=False, clipbrd=False, scrshot=None, dataset=True)
        dlg.setTreeWidgetHeaderLabels(index=tab2, labels=labels)
        labels = labels[1:]
        dlg.setTreeWidgetArray(index=tab2, arr=npr, d=3, rows=labels)
        # dlg.showTree(0)
        # dlg.showFigure(0)
        dlg._getDataFrame = lambda _, x=r: x
        fig = dlg.getFigure(tab1)
        fig.set_layout_engine('constrained')
        fig.clear()
        ax = fig.add_subplot(111, anchor='C')
        # noinspection PyTypeChecker
        cax = ax.inset_axes([1.05, 0.0, 0.05, 1.0])
        im = ax.imshow(npr, cmap='jet')
        cbar = fig.colorbar(im, cax=cax, cmap='jet')
        cbar.ax.set_ylabel('Streamlines count', rotation=-90, va="bottom")
        n = len(labels)
        if n < 17:
            ax.set_xticks(np.arange(n), labels=labels)
            ax.set_yticks(np.arange(n), labels=labels)
        else:
            ax.set_xticks(np.arange(1, n+1))
            ax.set_yticks(np.arange(1, n+1))
        ax.tick_params(axis='x', labelrotation=90)
        wait.close()
        dlg.exec()
        """
        Exit  
        """
        r = messageBox(self,
                       title=self.windowTitle(),
                       text='Would you like to do\nmore connectivity matrix ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes:
            self._filetracts.clear()
            self._filelabel.clear()
        else: self.accept()
