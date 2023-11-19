"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        Requests        https://requests.readthedocs.io/en/latest/                  Simple HTTP library
"""

import os

from os.path import join
from os.path import dirname
from os.path import basename
from os.path import exists
from os.path import splitext
from os.path import abspath

from xml.dom import minidom

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QMessageBox

import requests as rq

from Sisyphe.core.sisypheDownload import downloadFromHost
from Sisyphe.core.sisypheDownload import downloadFromMediaFireHost
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDownload']

"""
    Class hierarchy

        QDialog -> DialogDownload

"""

class DialogDownload(QDialog):
    """
         DialogDownload

         Description

             GUI dialog window to manage download of PySisyphe components (fonts, templates, plugins).

         Inheritance

             QDialog -> DialogDownload

         Public methods

            inherited QDialog methods
     """

    # Class constants

    _URL = 'https://www.mediafire.com/file/u23q25zgpt0076i/host.xml/file'

    # class method

    @classmethod
    def getSisypheFolder(cls) -> str:
        import Sisyphe
        return dirname(abspath(Sisyphe.__file__))

    @classmethod
    def getSettingsFolder(cls) -> str:
        import Sisyphe.settings
        return dirname(abspath(Sisyphe.settings.__file__))

    # Special method

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle('Download')

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

        self._checkall = QPushButton('Check all')
        self._uncheckall = QPushButton('Uncheck all')
        self._download = QPushButton('Download')
        self._checkall.adjustSize()
        self._uncheckall.adjustSize()
        self._download.adjustSize()
        self._checkall.setToolTip('Check all items.')
        self._uncheckall.setToolTip('Uncheck all items.')
        self._download.setToolTip('Download checked items.')
        self._checkall.clicked.connect(lambda: self.checkAll())
        self._uncheckall.clicked.connect(lambda: self.uncheckAll())
        self._download.clicked.connect(lambda: self.download())

        # Init default dialog button

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addStretch()
        layout.addWidget(self._checkall)
        layout.addWidget(self._uncheckall)
        layout.addWidget(self._download)
        self._layout.addLayout(layout)
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        self._ok.clicked.connect(self.accept)

    # Private method

    def _updateSection(self, folder: str):
        if len(self._urls[folder]) > 0:
            for item in self._urls[folder].values():
                if exists(item[0]):
                    item[2].setVisible(False)

    def _initSections(self):
        wait = DialogWait(progress=False, parent=self)
        wait.setInformationText('Host connection...')
        wait.open()
        filename = downloadFromMediaFireHost(self._URL, self.getSettingsFolder(), wait)
        wait.close()
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
                                if buff[0] == os.sep: buff = buff[1:]
                                path = join(self.getSisypheFolder(), buff)
                                if not exists(path):
                                    url = node.getAttribute('url')
                                    if node.firstChild:
                                        name = node.firstChild.data
                                        cb = QCheckBox(name)
                                        cb.setChecked(False)
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
                self._sections.currentItemChanged.connect(self._currentSelectedChanged)
                self._sections.header().setStretchLastSection(False)
                self._sections.resizeColumnToContents(0)
                self._sections.setMaximumWidth(int(self._sections.columnWidth(0) * 1.5))
                self._sections.setMinimumWidth(self._sections.columnWidth(0))
                self._sections.header().setStretchLastSection(True)
            else: raise IOError('XML format is not supported.')
        else: self.accept()

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
        folder = self._sections.selectedItems()[0].text(0)
        if len(self._urls[folder]) > 0:
            wait = DialogWait(progress=False, parent=self)
            wait.setInformationText('Downloading...')
            wait.open()
            for k, item in self._urls[folder].items():
                if item[2].isChecked():
                    path = item[0]
                    url = item[1]
                    wait.setInformationText('{} downloading...'.format(basename(path)))
                    try: downloadFromHost(url, dirname(path), wait)
                    except:
                        QMessageBox.warning(self, 'Download',
                                            '{} download failed.'.format(k))
                        return None
                    finally:
                        wait.close()
                    self._updateSection(folder)


"""
    Test
"""

if __name__ == '__main__':
    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogDownload()
    main.show()
    app.exec_()
