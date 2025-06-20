"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join

from xml.dom import minidom

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheSettings import getUserPySisyphePath
from Sisyphe.core.sisypheDownload import downloadFromHost
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDownload']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDownload
"""

class DialogDownload(QDialog):
    """
    DialogDownload

    Description
    ~~~~~~~~~~~

    GUI dialog window to manage download of PySisyphe components (fonts, templates, plugins).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDownload

    Last revision: 30/10/2024
    """

    # class method

    @classmethod
    def getSisypheFolder(cls) -> str:
        import Sisyphe
        return dirname(abspath(Sisyphe.__file__))

    @classmethod
    def getSettingsFolder(cls) -> str:
        import Sisyphe.settings
        return dirname(abspath(Sisyphe.settings.__file__))

    @classmethod
    def getUserFolder(cls) -> str:
        return getUserPySisyphePath()

    # Special method

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle('Download manager')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._urls = dict()
        self._splitter = QSplitter()
        self._stack = QStackedWidget()
        self._sections = QTreeWidget()
        self._sections.setColumnCount(1)
        self._sections.header().setVisible(False)
        self._sections.setSelectionMode(QTreeWidget.SingleSelection)
        self._splitter.addWidget(self._sections)
        self._splitter.addWidget(self._stack)
        self._layout.addWidget(self._splitter)
        self._initSections()

        # Init buttons

        self._uncheckall = QPushButton('Uncheck all')
        self._download = QPushButton('Download')
        self._uncheckall.adjustSize()
        self._download.adjustSize()
        self._uncheckall.setToolTip('Uncheck all items.')
        self._download.setToolTip('Download checked items.')
        # noinspection PyUnresolvedReferences
        self._uncheckall.clicked.connect(lambda: self.uncheckAll())
        # noinspection PyUnresolvedReferences
        self._download.clicked.connect(lambda: self.download())

        # Init default dialog button

        layout = QHBoxLayout()
        if platform == 'win32':
            layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(self._download)
        layout.addStretch()
        layout.addWidget(self._uncheckall)
        self._layout.addLayout(layout)
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)

    # Private method

    def _updateSection(self, folder: str):
        if len(self._urls[folder]) > 0:
            for item in self._urls[folder].values():
                path = join(item[0], item[2].text())
                if exists(path):
                    item[2].setEnabled(False)

    def _initSections(self):
        filename = join(self.getSettingsFolder(), 'host.xml')
        if exists(filename):
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == 'host' and root.getAttribute('version') == '1.0':
                sections = doc.getElementsByTagName('folder')
                for section in sections:
                    folder = section.getAttribute('name')
                    lyout = QVBoxLayout()
                    lyout.setAlignment(Qt.AlignLeft)
                    widget = QWidget()
                    widget.setLayout(lyout)
                    self._urls[folder] = dict()
                    if section.hasChildNodes():
                        for node in section.childNodes:
                            if node.nodeName == 'file':
                                buff = node.getAttribute('path')
                                if buff[0] == '/': buff = buff[1:]
                                if platform == 'win32':
                                    buff = buff.replace('/', '\\')
                                dst = node.getAttribute('dst')
                                if dst == 'main': path = join(self.getSisypheFolder(), buff)
                                elif dst == 'user': path = join(self.getUserFolder(), buff)
                                else: continue
                                url = node.getAttribute('url')
                                if node.firstChild:
                                    name = node.firstChild.data
                                    cb = QCheckBox(name)
                                    cb.setChecked(False)
                                    path2 = join(path, name)
                                    cb.setEnabled(not exists(path2))
                                    if cb.isEnabled(): cb.setToolTip('Destination: {}'.format(path2))
                                    lyout.addWidget(cb)
                                    self._urls[folder][name] = (path, url, cb)
                        scroll = QScrollArea()
                        scroll.setWidget(widget)
                        scroll.setFrameShape(QScrollArea.NoFrame)
                        scroll.setAlignment(Qt.AlignLeft)
                        self._stack.addWidget(scroll)
                        item = QTreeWidgetItem()
                        item.setText(0, folder)
                        item.setData(0, Qt.UserRole, self._stack.count() - 1)
                        self._sections.addTopLevelItem(item)
                        if self._sections.topLevelItemCount() == 1: item.setSelected(True)
                # noinspection PyUnresolvedReferences
                self._sections.currentItemChanged.connect(self._currentSelectedChanged)
                self._sections.header().setStretchLastSection(False)
                self._sections.resizeColumnToContents(0)
                self._sections.setMaximumWidth(int(self._sections.columnWidth(0) * 1.5))
                self._sections.setMinimumWidth(self._sections.columnWidth(0))
                self._sections.header().setStretchLastSection(True)
            else:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Unable to decode host.xml file.')
                self.accept()
        else:
            messageBox(self,
                       title=self.windowTitle(),
                       text='host.xml file not found.')
            self.accept()

    # noinspection PyUnusedLocal
    def _currentSelectedChanged(self, current, previous):
        index = current.data(0, Qt.UserRole)
        if index >= 0: self._stack.setCurrentIndex(index)

    # Public methods

    def checkAll(self):
        folder = self._sections.selectedItems()[0].text(0)
        for item in self._urls[folder].values():
            item[2].setChecked(True)

    def uncheckAll(self):
        folder = self._sections.selectedItems()[0].text(0)
        for item in self._urls[folder].values():
            item[2].setChecked(False)

    def download(self):
        wait = None
        for i in range(self._sections.topLevelItemCount()):
            folder = self._sections.topLevelItem(i).text(0)
            if len(self._urls[folder]) > 0:
                for k, item in self._urls[folder].items():
                    if item[2].isChecked():
                        if wait is None:
                            wait = DialogWait()
                            wait.open()
                            wait.progressVisibilityOff()
                            wait.setInformationText('Downloading...')
                        path = item[0]
                        url = item[1]
                        try: downloadFromHost(url, path, info=k, wait=wait)
                        except:
                            if wait is not None: wait.close()
                            messageBox(self,
                                       title='Download manager',
                                       text='{} download failed.'.format(k))
                            self.uncheckAll()
                            return
                        item[2].setChecked(False)
                        item[2].setEnabled(False)
        if wait is not None: wait.close()
