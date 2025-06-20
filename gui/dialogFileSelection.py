"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import exists

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

__all__ = ['DialogFileSelection',
           'DialogMultiFileSelection',
           'DialogFilesSelection']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogFileSelection
              -> DialogMultiFileSelection
              -> DialogFilesSelection
"""


class DialogFileSelection(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog for single file selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogFileSelection

    Creation: 15/11/2022
    Last revision: 19/11/2024
    """

    # Special method

    """
    Private attributes

    _widget    FileSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('File selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        self._widget = FileSelectionWidget()

        # Inherited methods from SelectionFilter class

        setattr(self, 'getFilename', self._widget.getFilename)
        setattr(self, 'getPath', self._widget.getPath)
        setattr(self, 'getBasename', self._widget.getBasename)
        setattr(self, 'setReferenceVolume', self._widget.setReferenceVolume)
        setattr(self, 'getReferenceVolume', self._widget.getReferenceVolume)
        setattr(self, 'setToolBarThumbnail', self._widget.setToolbarThumbnail)
        setattr(self, 'getToolBarThumbnail', self._widget.getToolbarThumbnail)
        setattr(self, 'hasToolBarThumbnail', self._widget.hasToolbarThumbnail)
        setattr(self, 'setFiltersToDefault', self._widget.setFiltersToDefault)
        setattr(self, 'clearExtensionFilter', self._widget.clearExtensionFilter)
        setattr(self, 'getExtensionFilter', self._widget.getExtensionFilter)
        setattr(self, 'filterDirectory', self._widget.filterDirectory)
        setattr(self, 'filterExtension', self._widget.filterExtension)
        setattr(self, 'filterDICOM', self._widget.filterDICOM)
        setattr(self, 'filterSisypheVolume', self._widget.filterSisypheVolume)
        setattr(self, 'filterSisypheROI', self._widget.filterSisypheROI)
        setattr(self, 'filterSisypheMesh', self._widget.filterSisypheMesh)
        setattr(self, 'filterSisypheStreamlines', self._widget.filterSisypheStreamlines)
        setattr(self, 'filterMultiComponent', self._widget.filterMultiComponent)
        setattr(self, 'filterSingleComponent', self._widget.filterSingleComponent)
        setattr(self, 'filterSameIdentity', self._widget.filterSameIdentity)
        setattr(self, 'filterSameSize', self._widget.filterSameSize)
        setattr(self, 'filterSameModality', self._widget.filterSameModality)
        setattr(self, 'filterSameSequence', self._widget.filterSameSequence)
        setattr(self, 'filterSameDatatype', self._widget.filterSameDatatype)
        setattr(self, 'filterSameOrientation', self._widget.filterSameOrientation)
        setattr(self, 'filterRegisteredToReference', self._widget.filterRegisteredToReference)
        setattr(self, 'filterFrame', self._widget.filterFrame)

        # Inherited methods from FileSelectionWidget class

        setattr(self, 'setCurrentVolumeButtonVisibility', self._widget.setCurrentVolumeButtonVisibility)
        setattr(self, 'getCurrentVolumeButtonVisibility', self._widget.getCurrentVolumeButtonVisibility)
        setattr(self, 'setClearButtonVisibility', self._widget.setClearButtonVisibility)
        setattr(self, 'getClearButtonVisibility', self._widget.getClearButtonVisibility)
        setattr(self, 'setLabelVisibility', self._widget.setLabelVisibility)
        setattr(self, 'getLabelVisibility', self._widget.getLabelVisibility)
        setattr(self, 'setTextLabel', self._widget.setTextLabel)
        setattr(self, 'getTextLabel', self._widget.getTextLabel)
        setattr(self, 'getLabel', self._widget.getTextLabel)
        setattr(self, 'isEmpty', self._widget.isEmpty)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        lyout.addWidget(ok)
        lyout.addWidget(cancel)
        lyout.addStretch()

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self._accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.addWidget(self._widget)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

        # < Revision 20/05/2025
        # no resize
        self.adjustSize()
        self.setFixedSize(self.size())
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    def _accept(self):
        if self.getFilename() != '': self.accept()


class DialogMultiFileSelection(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog for multiple file selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogMultipleFileSelection

    Creation: 15/11/2022
    Last revision: 22/05/2025
    """

    # Special methods

    """
    Private attributes

    _widget    dict[str, FileSelectionWidget]
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Files selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        self._widgets = dict()
        self._current = 0

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        else: lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        lyout.addWidget(ok)
        lyout.addWidget(cancel)
        lyout.addStretch()

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self._accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

        self.setModal(True)

    # Container Public methods

    def __getitem__(self, key):
        return self._widgets[key]

    def __len__(self):
        return len(self._widgets)

    def __contains__(self, key):
        return key in self._widgets

    def __iter__(self):
        self._current = 0
        return self

    def __next__(self):
        keys = list(self._widgets.keys())
        if self._current < len(self._widgets):
            index = self._current
            self._current += 1
            return self._wdigets[keys[index]]
        else: raise StopIteration

    # Private method

    def _accept(self):
        filenames = self.getFilenames()
        if len(filenames) == len(self._widgets): self.accept()
        else: messageBox(self,
                         title='File selection',
                         text='All files are not selected.')

    # Public methods

    def createFileSelectionWidget(self, label, toolbar=None, current=False, clear=True, sfilter=True):
        widget = FileSelectionWidget()
        widget.setTextLabel(label)
        if toolbar is not None: widget.setToolbarThumbnail(toolbar)
        widget.setCurrentVolumeButtonVisibility(current)
        widget.setClearButtonVisibility(clear)
        if sfilter: widget.filterSisypheVolume()
        self._widgets[label] = widget
        # < Revision 22/05/2025
        # align labels
        if len(self._widgets) > 1:
            wref = self._widgets[list(self._widgets.keys())[0]]
            widget.alignLabels(wref)
        # Revision 22/05/2025 >
        # Remove previous fixed height
        self.setMinimumHeight(0)
        screen = QApplication.primaryScreen().geometry()
        self.setMaximumHeight(screen.height())
        # Add widget
        self._layout.insertWidget(self._layout.count() - 1, widget)
        # Add new fixed height
        self.setFixedHeight(self.sizeHint().height())
        return widget

    def count(self):
        return len(self._widgets)

    def isEmpty(self):
        return len(self._widgets) == 0

    def getFilename(self, key):
        if len(self._widgets) > 0:
            filename = self._widgets[key].getFilename()
            if exists(filename): return filename
            else: self._widgets[key].clear()
        return None

    def getFilenames(self):
        if len(self._widgets) > 0:
            r = dict()
            keys = list(self._widgets.keys())
            for key in keys:
                filename = self._widgets[key].getFilename()
                if exists(filename): r[key] = filename
                else: self._widgets[key].clear()
            if len(r) > 0: return r
        return None


class DialogFilesSelection(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog for list of file selection.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogFilesSelection

    Creation: 15/11/2022
    Last revision: 19/11/2024
    """

    # Special method

    """
    Private attributes

    _widget    FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Files selection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        self._widget = FilesSelectionWidget()

        # Inherited methods from SelectionFilter class

        setattr(self, 'setReferenceVolume', self._widget.setReferenceVolume)
        setattr(self, 'getReferenceVolume', self._widget.getReferenceVolume)
        setattr(self, 'setToolBarThumbnail', self._widget.setToolbarThumbnail)
        setattr(self, 'getToolBarThumbnail', self._widget.getToolbarThumbnail)
        setattr(self, 'hasToolBarThumbnail', self._widget.hasToolbarThumbnail)
        setattr(self, 'setFiltersToDefault', self._widget.setFiltersToDefault)
        setattr(self, 'clearExtensionFilter', self._widget.clearExtensionFilter)
        setattr(self, 'getExtensionFilter', self._widget.getExtensionFilter)
        setattr(self, 'filterDirectory', self._widget.filterDirectory)
        setattr(self, 'filterExtension', self._widget.filterExtension)
        setattr(self, 'filterDICOM', self._widget.filterDICOM)
        setattr(self, 'filterSisypheVolume', self._widget.filterSisypheVolume)
        setattr(self, 'filterSisypheROI', self._widget.filterSisypheROI)
        setattr(self, 'filterSisypheMesh', self._widget.filterSisypheMesh)
        setattr(self, 'filterSisypheStreamlines', self._widget.filterSisypheStreamlines)
        setattr(self, 'filterMultiComponent', self._widget.filterMultiComponent)
        setattr(self, 'filterSingleComponent', self._widget.filterSingleComponent)
        setattr(self, 'filterSameIdentity', self._widget.filterSameIdentity)
        setattr(self, 'filterSameSize', self._widget.filterSameSize)
        setattr(self, 'filterSameModality', self._widget.filterSameModality)
        setattr(self, 'filterSameSequence', self._widget.filterSameSequence)
        setattr(self, 'filterSameDatatype', self._widget.filterSameDatatype)
        setattr(self, 'filterSameOrientation', self._widget.filterSameOrientation)
        setattr(self, 'filterRegisteredToReference', self._widget.filterRegisteredToReference)
        setattr(self, 'filterFrame', self._widget.filterFrame)

        # Inherited methods from FilesSelectionWidget class

        # < Revision 10/06/2025
        setattr(self, 'setMaximumNumberOfFiles', self._widget.setMaximumNumberOfFiles)
        setattr(self, 'getMaximumNumberOfFiles', self._widget.getMaximumNumberOfFiles)
        # Revision 10/06/2025 >
        setattr(self, 'setCurrentVolumeButtonVisibility', self._widget.setCurrentVolumeButtonVisibility)
        setattr(self, 'getCurrentVolumeButtonVisibility', self._widget.getCurrentVolumeButtonVisibility)
        setattr(self, 'setLabelVisibility', self._widget.setLabelVisibility)
        setattr(self, 'getLabelVisibility', self._widget.getLabelVisibility)
        setattr(self, 'setTextLabel', self._widget.setTextLabel)
        setattr(self, 'getTextLabel', self._widget.getTextLabel)
        setattr(self, 'getLabel', self._widget.getTextLabel)
        setattr(self, 'setSelectionMode', self._widget.setSelectionMode)
        setattr(self, 'setSelectionModeToSingle', self._widget.setSelectionModeToSingle)
        setattr(self, 'setSelectionModeToContiguous', self._widget.setSelectionModeToContiguous)
        setattr(self, 'setSelectionModeToExtended', self._widget.setSelectionModeToExtended)
        setattr(self, 'getSelectionMode', self._widget.getSelectionMode)
        setattr(self, 'getFilenames', self._widget.getFilenames)
        setattr(self, 'getSelectedFilenames', self._widget.getSelectedFilenames)
        setattr(self, 'isEmpty', self._widget.isEmpty)
        setattr(self, 'filenamesCount', self._widget.filenamesCount)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        else: lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        lyout.addWidget(ok)
        lyout.addWidget(cancel)
        lyout.addStretch()

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self._accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.addWidget(self._widget)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

        self.setModal(True)

    # Private method

    def _accept(self):
        if self.filenamesCount() > 0: self.accept()
