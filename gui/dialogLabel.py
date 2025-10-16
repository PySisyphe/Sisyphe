"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import chdir

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogVOLtoLabel',
           'DialogROItoLabel',
           'DialogLabeltoROI',
           'DialogLabeltoMask',
           'DialogRelabel']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogVOLtoLabel
              -> DialogROItoLabel
              -> DialogLabeltoROI
              -> DialogLabelToMask
              -> DialogRelabel
"""

class DialogVOLtoLabel(QDialog):
    """
    DialogVOLtoLabel class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert volume to label volume.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogVOLtoLabel

    Last revision: 15/10/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Probability volumes to Label volume')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('Probability volume(s)')
        self._list.filterSisypheVolume()
        self._list.filterRange(v=(0.0, 1.0))
        self._list.filterSameFOV()
        self._list.setMaximumNumberOfFiles(255)
        self._list.setReferenceVolumeToFirst()
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Window

        # < Revision 17/07/2025
        screen = QApplication.primaryScreen().geometry()
        self._list.setMinimumWidth(int(screen.width() * 0.33))
        self.adjustSize()
        # Revision 17/07/2025 >
        self.setModal(True)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            vols = SisypheVolumeCollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            wait.buttonVisibilityOff()
            wait.FigureVisibilityOff()
            for filename in self._list.getFilenames():
                wait.setInformationText('Load {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    v = SisypheVolume()
                    v.load(filename)
                    vols.append(v)
            if vols.count() > 1:
                wait.progressVisibilityOff()
                wait.setInformationText('Label volume processing...')
                lbl = vols.toLabelVolume()
                wait.hide()
                filename = QFileDialog.getSaveFileName(self,
                                                       'Save label volume...',
                                                       vols[0].getDirname(),
                                                       filter=lbl.getFilterExt())[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    lbl.saveAs(filename)
            else: wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()

    # < Revision 15/10/2025
    # add getFileSelectionWidget method
    def getFilesSelectionWidget(self):
        return  self._list
    # Revision 15/10/2025 >


class DialogROItoLabel(QDialog):
    """
    DialogROItoLabel class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert ROIs to label volume.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogROItoLabel

    Last revision: 15/10/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('ROI(s) to Label volume')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('ROI(s)')
        self._list.filterSisypheROI()
        self._list.filterSameID()
        self._list.setMaximumNumberOfFiles(255)
        self._list.setReferenceVolumeToFirst()
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Window

        # < Revision 17/07/2025
        screen = QApplication.primaryScreen().geometry()
        self._list.setMinimumWidth(int(screen.width() * 0.33))
        self.adjustSize()
        # Revision 17/07/2025 >
        self.setModal(True)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            rois = SisypheROICollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            for filename in self._list.getFilenames():
                wait.setInformationText('Load {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    roi = SisypheROI()
                    roi.load(filename)
                    rois.append(roi)
            if rois.count() > 1:
                wait.progressVisibilityOff()
                wait.setInformationText('Label volume processing...')
                lbl = rois.toLabelVolume()
                wait.hide()
                filename = QFileDialog.getSaveFileName(self,
                                                       'Save label volume...',
                                                       rois[0].getDirname(),
                                                       filter=lbl.getFilterExt())[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    lbl.saveAs(filename)
            wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()

    # < Revision 15/10/2025
    # add getFileSelectionWidget method
    def getFilesSelectionWidget(self):
        return  self._list
    # Revision 15/10/2025 >


class DialogLabeltoROI(QDialog):
    """
    DialogLabelToROI class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert label volume to ROIs.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogLabelToROI

    Last revision: 15/10/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Label volume(s) to ROI(s)')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('Label volume(s)')
        self._list.filterSisypheVolume()
        self._list.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Window

        # < Revision 17/07/2025
        screen = QApplication.primaryScreen().geometry()
        self._list.setMinimumWidth(int(screen.width() * 0.33))
        self.adjustSize()
        # Revision 17/07/2025 >
        self.setModal(True)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            v = SisypheVolume()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            for filename in self._list.getFilenames():
                wait.setInformationText('{} conversion...'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    wait.incCurrentProgressValue()
                    v.load(filename)
                    rois = SisypheROICollection()
                    rois.fromLabelVolume(v)
                    rois.save()
            wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()

    # < Revision 15/10/2025
    # add getFileSelectionWidget method
    def getFilesSelectionWidget(self):
        return  self._list
    # Revision 15/10/2025 >


class DialogLabeltoMask(QDialog):
    """
     DialogLabelToMask class

     Description
     ~~~~~~~~~~~

     GUI dialog window to create a mask as a combination of labels from a label volume.

     Inheritance
     ~~~~~~~~~~~

     QDialog -> DialogLabelToMask

     Creation: 13/10/2025
     Last revision: 15/10/2025
     """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    _labels QListWidget
    _roi    QCheckBox
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Label volume to mask')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FileSelectionWidget()
        self._list.setTextLabel('Label volume')
        self._list.filterSisypheVolume()
        self._list.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._list.FieldChanged.connect(self._updateLabels)
        self._layout.addWidget(self._list)

        self._labels = QListWidget()
        self._labels.setToolTip('Label names')
        self._labels.setMinimumHeight(300)
        # noinspection PyUnresolvedReferences
        self._labels.itemClicked.connect(self._hasChecked)
        self._layout.addWidget(self._labels)

        self._roi = QCheckBox('Save ROI')
        self._roi.setToolTip('Also save mask as ROI.')
        self._layout.addWidget(self._roi)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._ok.setEnabled(False)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Window

        # < Revision 17/07/2025
        screen = QApplication.primaryScreen().geometry()
        self._list.setMinimumWidth(int(screen.width() * 0.33))
        self.adjustSize()
        # Revision 17/07/2025 >
        self.setModal(True)

    # Private method

    def _updateLabels(self):
        self._labels.clear()
        if not self._list.isEmpty():
            v = SisypheVolume()
            v.load(self._list.getFilename())
            if v.acquisition.hasLabels():
                for k in v.acquisition.getLabels():
                    if k > 0:
                        # < Revision 15/10/2025
                        # add label index to QListWidgetItem
                        # item = QListWidgetItem(v.acquisition.getLabel(k))
                        item = QListWidgetItem('#{} {}'.format(k, v.acquisition.getLabel(k)))
                        # Revision 15/10/2025 >
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                        item.setData(Qt.UserRole, k)
                        self._labels.addItem(item)

    def _hasChecked(self):
        for i in range(self._labels.count()):
            item = self._labels.item(i)
            if item.checkState() == Qt.Checked:
                self._ok.setEnabled(True)
                return True
        self._ok.setEnabled(False)
        return False

    # < Revision 14/10/2025
    # add _uncheckAll method
    def _uncheckAll(self):
        for i in range(self._labels.count()):
            item = self._labels.item(i)
            # noinspection PyTypeChecker
            item.setCheckState(Qt.Unchecked)
    # Revision 14/10/2025 >

    # Public methods

    def convert(self):
        if not self._list.isEmpty() and self._hasChecked():
            wait = DialogWait(info=self.windowTitle())
            wait.open()
            wait.progressVisibilityOff()
            v = SisypheVolume()
            v.load(self._list.getFilename())
            cross = dict()
            for i in range(self._labels.count()):
                item = self._labels.item(i)
                if item.checkState() == Qt.Checked: cross[item.data(Qt.UserRole)] = 1
                else: cross[item.data(Qt.UserRole)] = 0
            mask = v.getRelabeled(cross)
            mask.acquisition.setModalityToOT()
            mask.acquisition.setSequenceToMask()
            mask.setFilename(v.getFilename())
            mask.setFilenameSuffix('mask')
            wait.close()
            filename = QFileDialog.getSaveFileName(self,
                                                   'Save mask volume...',
                                                   mask.getFilename(),
                                                   filter=mask.getFilterExt())[0]
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                mask.saveAs(filename)
                if self._roi.isChecked():
                    roi = mask.getROI()
                    roi.saveAs(mask.getFilename())
                r = messageBox(self,
                               title=self.windowTitle(),
                               text='Do you want to make a new mask ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes: self._uncheckAll()
                else: self.accept()
            else: self.accept()

    # < Revision 15/10/2025
    # add getFileSelectionWidget method
    def getFileSelectionWidget(self):
        return  self._list
    # Revision 15/10/2025 >


class DialogRelabel(QDialog):
    """
     DialogRelabel class

     Description
     ~~~~~~~~~~~

     GUI dialog window to remaps label indexes of a label volume.

     Inheritance
     ~~~~~~~~~~~

     QDialog -> DialogRelabel

     Creation: 15/10/2025
     """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    _labels QListWidget
    _roi    QCheckBox
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Remap label volume')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FileSelectionWidget()
        self._list.setTextLabel('Label volume')
        self._list.filterSisypheVolume()
        self._list.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._list.FieldChanged.connect(self._updateLabels)
        self._layout.addWidget(self._list)

        self._labels = QTreeWidget()
        self._labels.setHeaderLabels(['Old\nindexes', 'New\nindexes', 'Labels'])
        self._labels.setMinimumHeight(300)
        self._labels.header().setStretchLastSection(True)
        # noinspection PyTypeChecker
        self._labels.header().setDefaultAlignment(Qt.AlignCenter)
        self._labels.setColumnWidth(0, 75)
        self._labels.setColumnWidth(1, 75)
        self._layout.addWidget(self._labels)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._ok.setEnabled(False)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Window

        # < Revision 17/07/2025
        screen = QApplication.primaryScreen().geometry()
        self._list.setMinimumWidth(int(screen.width() * 0.33))
        self.adjustSize()
        # Revision 17/07/2025 >
        self.setModal(True)

    # Private method

    def _updateLabels(self):
        self._labels.clear()
        if not self._list.isEmpty():
            v = SisypheVolume()
            v.load(self._list.getFilename())
            if v.acquisition.hasLabels():
                for k in v.acquisition.getLabels():
                    if k > 0:
                        item = QTreeWidgetItem(self._labels)
                        item.setText(0, str(k))
                        item.setTextAlignment(0, Qt.AlignCenter)
                        item.setTextAlignment(1, Qt.AlignCenter)
                        item.setTextAlignment(2, Qt.AlignCenter)
                        self._labels.addTopLevelItem(item)
                        label = QLineEdit()
                        label.setText(v.acquisition.getLabel(k))
                        index = QSpinBox()
                        index.setRange(0, 255)
                        index.setValue(k)
                        self._labels.setItemWidget(item, 1, index)
                        self._labels.setItemWidget(item, 2, label)
            self._ok.setEnabled(True)
        else: self._ok.setEnabled(False)

    # Public methods

    def convert(self):
        if not self._list.isEmpty() and self._labels.topLevelItemCount() > 0:
            wait = DialogWait(info=self.windowTitle())
            wait.open()
            wait.progressVisibilityOff()
            v = SisypheVolume()
            v.load(self._list.getFilename())
            cross = dict()
            for i in range(self._labels.topLevelItemCount()):
                item = self._labels.topLevelItem(i)
                oldlbl = int(item.text(0))
                newlbl = self._labels.itemWidget(item, 1)
                cross[oldlbl] = newlbl.value()
            v2 = v.getRelabeled(cross)
            v2.acquisition.setModalityToLB()
            v2.setFilename(v.getFilename())
            v2.setFilenamePrefix('relabeled')
            v2.acquisition.clearLabels()
            for i in range(self._labels.topLevelItemCount()):
                item = self._labels.topLevelItem(i)
                index = self._labels.itemWidget(item, 1)
                if index.value() > 0:
                    name = self._labels.itemWidget(item, 2)
                    v2.acquisition.setLabel(index.value(), name.text())
            wait.close()
            filename = QFileDialog.getSaveFileName(self,
                                                   'Save relabeled volume...',
                                                   v2.getFilename(),
                                                   filter=v2.getFilterExt())[0]
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                v2.saveAs(filename)
                r = messageBox(self,
                               title=self.windowTitle(),
                               text='Do you want to relabel a new volume ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes: self._list.clear()
                else: self.accept()
            else: self.accept()

    # < Revision 15/10/2025
    # add getFileSelectionWidget method
    def getFileSelectionWidget(self):
        return  self._list
    # Revision 15/10/2025 >