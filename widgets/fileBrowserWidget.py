"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - pandas, data analysis and manipulation tool,  https://pandas.pydata.org/
    - Pillow,  image processing, https://pillow.readthedocs.io/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import sys

from os import remove
from os import rename
from os import chdir

from os.path import join
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import abspath
from os.path import isdir
from os.path import expanduser

import cython

from datetime import date

from io import BytesIO

import subprocess

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from pandas import DataFrame

from pathlib import Path

from PIL import Image

from shutil import copy
from shutil import copytree
from shutil import move
from shutil import rmtree

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDir
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRegExp
from PyQt5.QtCore import QFileSystemWatcher
from PyQt5.QtCore import QFileInfo
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QScrollArea
# from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QFileIconProvider
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel

from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.gui.dialogWait import DialogWait

if TYPE_CHECKING:
    from pandas import Index
    from PyQt5.QtCore import QObject
    from PyQt5.QtCore import QVariant
    from PyQt5.QtCore import QModelIndex
    from PyQt5.QtCore import QAbstractItemModel
    from PyQt5.QtGui import QDropEvent
    from PyQt5.QtGui import QDragMoveEvent
    from PyQt5.QtGui import QDragEnterEvent
    from PyQt5.QtWidgets import QStyleOptionViewItem
    from Sisyphe.gui.windowSisyphe import WindowSisyphe


__all__ = ['FileBrowserWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QLineEdit -> BrowserLineEdit
    - QStyledItemDelegate -> LineEditDelegate
    - QStandardItemModel -> PandasTableModel
    - QTreeView -> FileDragDropTreeView
    - QWidget -> DialogFileBrowser
"""


class BrowserLineEdit(QLineEdit):

    # Special method

    def __init__(self,
                 filename: str,
                 parent: QWidget | None = None) -> None:
        super(BrowserLineEdit, self).__init__(parent)
        regex = QRegExp(r'^(?!\.{1,2}$)(?!CON$|PRN$|AUX$|NUL$|COM[1-9]$|LPT[1-9]$)'
                        r'[^\x00-\x1F\\/:*?"<>|]'
                        r'[^\x00-\x1F\\/:*?"<>|]*'
                        r'[^\x00-\x1F\\/:*?"<>| .]$')
        self.setValidator(QRegExpValidator(regex))
        self.setText(filename)
        self.setClearButtonEnabled(True)


class LineEditDelegate(QStyledItemDelegate):

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        super(LineEditDelegate, self).__init__(parent)

    # Public methods

    # noinspection unresolved-references
    def createEditor(self,
                     parent: QWidget | None,
                     option:  QStyleOptionViewItem | None,
                     index: QModelIndex) -> QLineEdit:
        model = index.model()
        return BrowserLineEdit(model.data(index, Qt.EditRole), parent)

    # noinspection method-overriding, unresolved-references
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        model = index.model()
        editor.setText(model.data(index, Qt.EditRole))

    # noinspection method-overriding, unresolved-references
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        if editor.text() != '':
            if self.parent().objectName() == 'files':
                src = model.data(index, Qt.UserRole)
                dst = abspath(join(dirname(src), editor.text()))
                if exists(src): rename(src, dst)
            elif self.parent().objectName() == 'folders':
                chdir(expanduser('~'))
                model.setData(index, editor.text(), Qt.EditRole)


# < Revision 11/05/2026
# new IconProvider class
class IconProvider(QFileIconProvider):

    def __init__(self):
        super().__init__()
        import darkdetect
        if darkdetect.isDark(): icondir = 'darkroi'
        else: icondir = 'lightroi'
        import Sisyphe.gui
        path = join(dirname(Sisyphe.gui.__file__), icondir)
        self._icn_folder = QIcon(join(path, 'folder.png'))
        self._icn_head = QIcon(join(path, 'head.png'))
        self._icn_bitmap = QIcon(join(path, 'bitmap.png'))
        self._icn_xml = QIcon(join(path, 'xml.png'))
        self._icn_json = QIcon(join(path, 'json.png'))
        self._icn_roi = QIcon(join(path, 'roi.png'))
        self._icn_mesh = QIcon(join(path, 'mesh.png'))
        self._icn_tracking = QIcon(join(path, 'tracking-atlas.png'))
        self._icn_360 = QIcon(join(path, '360.png'))
        self._icn_labels = QIcon(join(path, 'labels.png'))
        self._icn_target = QIcon(join(path, 'target.png'))
        self._icn_palette = QIcon(join(path, 'palette.png'))
        self._icn_sheet = QIcon(join(path, 'sheet.png'))
        self._icn_scan = QIcon(join(path, 'scan.png'))
        self._icn_model = QIcon(join(path, 'model.png'))
        self._icn_frame = QIcon(join(path, 'frame.png'))
        self._icn_workflow = QIcon(join(path, 'workflow.png'))
        self._icn_page = QIcon(join(path, 'page.png'))

    # noinspection method-overriding
    def icon(self, fileInfo: QFileInfo) -> QIcon:
        return self._icn_folder
# Revision 11/05/2026 >


class PandasTableModel(QStandardItemModel):

    # Special method

    def __init__(self,
                 data: DataFrame,
                 editable: bool = False,
                 parent: QObject | None = None) -> None:
        QStandardItemModel.__init__(self, parent)
        self._data: DataFrame = data
        self._editflag: bool = editable
        for col in data.columns:
            data_col = [QStandardItem("{}".format(x)) for x in data[col].values]
            self.appendColumn(data_col)
        return

    # Public methods

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._data.values)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return self._data.columns.size

    # noinspection PyMethodOverriding, PyUnresolvedReferences
    def headerData(self,
                   x: int,
                   orientation: Qt.Orientation,
                   role: Qt.DisplayRole) -> Index | str | None:
        # noinspection PyUnresolvedReferences
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[x]
        # noinspection PyUnresolvedReferences
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[x]
        return None

    def getDataFrame(self) -> DataFrame:
        return self._data

    def hasDataFrame(self) -> bool:
        return self._data is not None

    # noinspection method-overriding
    def flags(self, index: QModelIndex) -> int:
        if self._editflag:
            # noinspection PyUnresolvedReferences
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            # noinspection PyUnresolvedReferences
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # noinspection method-overriding,unresolved-references
    def setData(self,
                index: QModelIndex,
                value: QVariant,
                role: int = Qt.EditRole) -> bool | None:
        # noinspection PyInconsistentReturns
        if role == Qt.EditRole:
            self._data[self._data.columns[index.column()]][self._data.index[index.row()]] = value
            return True

    # noinspection PyUnresolvedReferences
    def data(self,
             index: QModelIndex,
             role: int = Qt.DisplayRole) -> str | None:
        # noinspection PyInconsistentReturns
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data[self._data.columns[index.column()]][self._data.index[index.row()]]
                return str(value)

    def getEditable(self) -> bool:
        return self._editflag


class FileDragDropTreeView(QTreeView):

    # Private method

    def _getParent(self) -> FileBrowserWidget | None:
        parent = self.parent()
        while parent:
            if isinstance(parent, FileBrowserWidget): return parent
            # noinspection unresolved-references
            parent = parent.parent()
        return None

    # Qt events methods

    # noinspection method-overriding
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept()

    # noinspection method-overriding
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        m = event.mimeData()
        # noinspection unresolved-references
        if m.hasUrls():
            event.accept()
            return
        event.ignore()

    # noinspection method-overriding,unresolved-references,protected-member
    def dropEvent(self, event: QDropEvent) -> None:
        accepted = False
        m = event.mimeData()
        if m.hasUrls():
            dst = ''
            p = event.pos()
            index = self.indexAt(p)
            if self.objectName() == 'folders': dst = self.model().filePath(index)
            elif self.objectName() == 'files':
                parent = self._getParent()
                if parent:
                    try:
                        index = parent._treedir.selectedIndexes()
                        if index: dst = parent._treedir.model().filePath(index[0])
                    except: accepted = False
            else: accepted = False
            # if dst == m.absoluteFilePath(): accepted = True
            if exists(dst):
                urls = [url for url in m.urls() if url.isLocalFile()]
                for url in urls:
                    path = url.toLocalFile()
                    info = QFileInfo(path)
                    src = info.absoluteFilePath()
                    if exists(src):
                        if dst == src: continue
                        else:
                            try:
                                if isdir(src): move(src, dst)
                                else: copy(src, dst)
                            except: pass
                            accepted = True
        if accepted: event.acceptProposedAction()


# < Revision 12/10/2026
# new FileItemModel class
class FileItemModel(QStandardItemModel):

    def mimeTypes(self):
        types = super().mimeTypes()
        types.append("text/uri-list")
        return types

    # noinspection unresolved-references
    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        urls = []
        for index in indexes[::3]:
            if index.isValid():
                item = self.itemFromIndex(index)
                file_path = abspath(item.data(Qt.UserRole))
                if file_path: urls.append(QUrl.fromLocalFile(file_path))
        if urls: mime_data.setUrls(urls)
        return mime_data
# Revision 12/10/2026 >


class FileBrowserWidget(QWidget):
    """
    FileBrowserWidget

    Description
    ~~~~~~~~~~~

    File browser and preview widget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> FileBrowserWidget

    Creation: 09/02/2026
    Last revision: 12/10/2026
    """

    # Special method

    # noinspection unresolved-references
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Init QLayout

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._currentfile: str = ''
        self._mainWindow: WindowSisyphe | None = None
        self._cutflag: bool = False
        self._copyflag: bool = False
        self._clipboard: list[str] | None = None
        self._filter: str = '*'

        # Init widgets

        self._iconProvider = IconProvider()
        self._watcher = QFileSystemWatcher(self)

        self._filemodel = QFileSystemModel(self)
        self._filemodel.setRootPath('')
        self._filemodel.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self._filemodel.setReadOnly(False)
        self._filemodel.setIconProvider(self._iconProvider)
        rootindex = self._filemodel.index('')

        self._treedir = FileDragDropTreeView(self)
        self._treedir.setObjectName('folders')
        self._treedir.setModel(self._filemodel)
        self._treedir.setRootIndex(rootindex)
        self._treedir.setUniformRowHeights(True)
        self._treedir.header().hide()
        # self._treedir.header().model().setHeaderData(0, Qt.Orientation.Horizontal, 'Directories')
        self._treedir.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._treedir.header().hideSection(1)
        self._treedir.header().hideSection(2)
        self._treedir.header().hideSection(3)
        self._treedir.setSelectionMode(QTreeView.SingleSelection)
        self._treedir.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._treedir.customContextMenuRequested.connect(self._popupFolder)
        self._treedir.setAcceptDrops(True)
        self._treedir.setDragEnabled(True)
        self._treedir.setDropIndicatorShown(True)
        self._treedir.setItemDelegate(LineEditDelegate(self._treedir))
        self._treedir.setEditTriggers(QTreeView.EditTrigger.SelectedClicked)
        self._treedir.setStyleSheet('QTreeView::item { border: 1px solid transparent; } '
                                    'QTreeView::item:hover { border: 1px solid #CDE8FF; }')

        self._listfiles = FileDragDropTreeView(self)
        self._listfiles.setObjectName('files')
        self._listfiles.setUniformRowHeights(True)
        self._listfiles.setRootIsDecorated(False)
        # < Revision 12/10/2026
        # model = QStandardItemModel()
        model = FileItemModel()
        # Revision 12/10/2026 >
        model.setHorizontalHeaderLabels(['Name', 'Size', 'Last modified'])
        self._listfiles.setModel(model)
        self._listfiles.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._listfiles.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._listfiles.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._listfiles.header().setStretchLastSection(False)
        self._listfiles.setSortingEnabled(True)
        self._listfiles.setSelectionMode(QTreeView.ExtendedSelection)
        self._listfiles.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._listfiles.setAcceptDrops(True)
        self._listfiles.setDragEnabled(True)
        self._listfiles.setDropIndicatorShown(True)
        self._listfiles.setItemDelegate(LineEditDelegate(self._listfiles))
        self._listfiles.setEditTriggers(QTreeView.EditTrigger.SelectedClicked)
        self._listfiles.setStyleSheet('QTreeView::item { border: 1px solid transparent; } '
                                      'QTreeView::item:hover { border: 1px solid #CDE8FF; }')

        # text preview tab

        self._tabtextpreview = QWidget()
        self._textpreview = QPlainTextEdit(self)
        self._textpreview.setReadOnly(True)
        self._btsavetext = QPushButton('Save')
        self._btsavetext.setToolTip('Save text as .txt')
        self._btsavetext.clicked.connect(self._saveText)
        # < Revision 12/02/2026
        self._btimport = QPushButton('Table import')
        self._btimport.setToolTip('Import table from text')
        menu = QMenu()
        menu.addAction('space separator')
        menu.addAction('tab separator')
        menu.addAction('"," separator')
        menu.addAction('";" separator')
        menu.addAction('"|" separator')
        self._btimport.setMenu(menu)
        self._btimport.menu().triggered.connect(self._importTable)
        # Revision 12/02/2026 >
        self._chksource = QCheckBox()
        self._chksource.setChecked(False)
        self._chksource.setText('XML source')
        self._chksource.setToolTip('Check to show XML source')
        btlyout = QHBoxLayout()
        btlyout.setContentsMargins(10, 10, 10, 10)
        btlyout.setSpacing(10)
        btlyout.addWidget(self._btsavetext)
        btlyout.addWidget(self._btimport)
        btlyout.addStretch()
        btlyout.addWidget(self._chksource)
        lyout = QVBoxLayout()
        lyout.addWidget(self._textpreview)
        lyout.addLayout(btlyout)
        self._tabtextpreview.setLayout(lyout)

        # table preview tab

        self._tabtablepreview = QWidget()
        self._tablepreview = QTableView(self)
        self._tablepreview.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)
        self._tablepreview.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._bttabletranspose = QPushButton('Transpose')
        self._bttabletranspose.setToolTip('Transpose table')
        self._bttablesave = QPushButton('Save')
        self._bttablesave.setToolTip('Save tabl.')
        self._bttablesave2 = QPushButton('Save selected')
        self._bttablesave2.setToolTip('Save selected column')
        self._bttableconsole = QPushButton('Table to console')
        self._bttableconsole.setToolTip('Copy table to console as pandas DataFrame.')
        self._btcolumnconsole = QPushButton('Copy column to console')
        self._btcolumnconsole.setToolTip('Copy selected column to console as pandas DataFrame.')
        self._bttabletranspose.clicked.connect(self._transposeTable)
        self._bttablesave.clicked.connect(self._saveTable)
        self._bttablesave2.clicked.connect(self._saveTableSelection)
        self._bttableconsole.clicked.connect(self._copyTableToConsole)
        self._btcolumnconsole.clicked.connect(self._copyColumnToConsole)
        self._bttableconsole.setVisible(False)
        self._btcolumnconsole.setVisible(False)
        btlyout = QHBoxLayout()
        btlyout.setContentsMargins(10, 10, 10, 10)
        btlyout.setSpacing(10)
        btlyout.addWidget(self._bttabletranspose)
        btlyout.addWidget(self._bttablesave)
        btlyout.addWidget(self._bttablesave2)
        btlyout.addWidget(self._bttableconsole)
        btlyout.addWidget(self._btcolumnconsole)
        btlyout.addStretch()
        lyout = QVBoxLayout()
        lyout.addWidget(self._tablepreview)
        lyout.addLayout(btlyout)
        self._tabtablepreview.setLayout(lyout)
        self._tabtablepreview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tabtablepreview.customContextMenuRequested.connect(self._popupTable)

        # image preview tab

        self._fig = Figure()
        self._fig.set_layout_engine('constrained')
        self._imagepreview = FigureCanvas(self._fig)
        self._imagepreview2 = QWidget()
        lyout = QVBoxLayout()
        lyout.addWidget(self._imagepreview)
        self._imagepreview2.setLayout(lyout)

        self._tabimagepreview = QWidget()
        self._area = QScrollArea()
        # noinspection PyUnresolvedReferences
        self._area.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._area.setWidget(self._imagepreview2)
        self._btzoomin = QPushButton('+')
        self._btzoomin.setToolTip('Zoom in')
        self._btzoomout = QPushButton('-')
        self._btzoomout.setToolTip('Zoom out')
        self._btzoomreset = QPushButton('1:1')
        self._btzoomreset.setToolTip('Reset zoom')
        self._btsaveimage = QPushButton('Save')
        self._btsaveimage.setToolTip('Save image preview')
        self._btocr = QPushButton('OCR')
        self._btocr.setToolTip('Perform OCR processing to extract text from the image.')
        self._btzoomin.clicked.connect(self._zoomin)
        self._btzoomout.clicked.connect(self._zoomout)
        self._btzoomreset.clicked.connect(self._resetzoom)
        self._btsaveimage.clicked.connect(self._saveImage)
        self._btocr.clicked.connect(self._ocr)
        btlyout = QHBoxLayout()
        btlyout.setContentsMargins(10, 10, 10, 10)
        btlyout.setSpacing(10)
        btlyout.addWidget(self._btzoomin)
        btlyout.addWidget(self._btzoomout)
        btlyout.addWidget(self._btzoomreset)
        btlyout.addWidget(self._btsaveimage)
        btlyout.addWidget(self._btocr)
        btlyout.addStretch()
        lyout = QVBoxLayout()
        lyout.addWidget(self._area)
        lyout.addLayout(btlyout)
        self._tabimagepreview.setLayout(lyout)

        # xml preview

        # < Revision 12/02/2026
        self._tabxmlpreview = QWidget()
        self._xmlpreview = QPlainTextEdit(self)
        self._xmlpreview.setReadOnly(False)
        self._btsavexml = QPushButton('Save')
        self._btsavexml.clicked.connect(self._saveXml)
        btlyout = QHBoxLayout()
        btlyout.setContentsMargins(10, 10, 10, 10)
        btlyout.setSpacing(10)
        btlyout.addWidget(self._btsavexml)
        btlyout.addStretch()
        lyout = QVBoxLayout()
        lyout.addWidget(self._xmlpreview)
        lyout.addLayout(btlyout)
        self._tabxmlpreview.setLayout(lyout)
        # Revision 12/02/2026 >

        # tab widget

        self._preview = QTabWidget(self)
        self._preview.addTab(self._tabtextpreview, 'Text')
        self._preview.addTab(self._tabtablepreview, 'Table')
        self._preview.addTab(self._tabimagepreview, 'Image')
        self._preview.addTab(self._tabxmlpreview, 'XML')
        self._preview.setTabVisible(0, False)
        self._preview.setTabVisible(1, False)
        self._preview.setTabVisible(2, False)
        self._preview.setTabVisible(3, False)
        self._splitter = QSplitter()
        self._splitter.addWidget(self._treedir)
        self._splitter.addWidget(self._listfiles)
        self._splitter.addWidget(self._preview)

        self._layout.addWidget(self._splitter)

        # popup menu actions

        self.actions = dict()
        self.actions['open'] = QAction('Open')
        if sys.platform == 'win32': self.actions['explorer'] = QAction('Open current folder in file explorer...')
        else: self.actions['explorer'] = QAction('Open current folder in finder...')
        self.actions['user'] = QAction('Go to user folder...')
        self.actions['template'] = QAction('Go to template folder...')
        self.actions['edit'] = QAction('Edit attributes...')
        self.actions['console'] = QAction('Copy to console')
        self.actions['acpc'] = QAction('AC-PC selection...')
        self.actions['frame'] = QAction('Stereotactic frame detection...')
        self.actions['reorient'] = QAction('Reorient...')
        self.actions['rename1'] = QAction('Rename')
        self.actions['rename2'] = QAction('Rename')
        self.actions['folder'] = QAction('New folder...')
        self.actions['remove'] = QAction('Remove')
        self.actions['remove'].setShortcut('Ctrl+Suppr')
        self.actions['rmdir'] = QAction('Remove folder')
        self.actions['savec'] = QAction('Save column...')
        self.actions['savet'] = QAction('Save table...')
        self.actions['copyc'] = QAction('Copy column to console...')
        self.actions['copyt'] = QAction('Copy table to console...')
        self.actions['copyf'] = QAction('Copy file')
        self.actions['copyf'].setShortcut('Ctrl+C')
        self.actions['cutf'] = QAction('Cut file')
        self.actions['cutf'].setShortcut('Ctrl+X')
        self.actions['copyd'] = QAction('Copy folder')
        self.actions['copyd'].setShortcut('Ctrl+C')
        self.actions['cutd'] = QAction('Cut folder')
        self.actions['cutd'].setShortcut('Ctrl+X')
        self.actions['paste'] = QAction('Paste')
        self.actions['paste'].setShortcut('Ctrl+V')
        self.actions['selectall'] = QAction('Select All')
        self.actions['selectall'].setShortcut('Ctrl+A')
        self.actions['open'].triggered.connect(lambda _: self._open())
        self.actions['explorer'].triggered.connect(self._openExplorer)
        self.actions['user'].triggered.connect(self._userFolder)
        self.actions['template'].triggered.connect(self._templateFolder)
        self.actions['edit'].triggered.connect(self._editAttributes)
        self.actions['console'].triggered.connect(self._console)
        self.actions['acpc'].triggered.connect(self._acpc)
        self.actions['frame'].triggered.connect(self._frame)
        self.actions['reorient'].triggered.connect(self._reorient)
        self.actions['rename1'].triggered.connect(self._renameInTreeFolders)
        self.actions['rename2'].triggered.connect(self._renameInListFiles)
        self.actions['folder'].triggered.connect(self._newFolder)
        self.actions['remove'].triggered.connect(self._removeFile)
        self.actions['rmdir'].triggered.connect(self._removeDir)
        self.actions['savet'].triggered.connect(self._saveTable)
        self.actions['savec'].triggered.connect(self._saveTableSelection)
        self.actions['copyt'].triggered.connect(self._copyTableToConsole)
        self.actions['copyc'].triggered.connect(self._copyColumnToConsole)
        self.actions['copyd'].triggered.connect(self._copyDir)
        self.actions['cutd'].triggered.connect(self._cutDir)
        self.actions['copyf'].triggered.connect(self._copyFile)
        self.actions['cutf'].triggered.connect(self._cutFile)
        self.actions['paste'].triggered.connect(self._paste)
        self.actions['selectall'].triggered.connect(self._selectAll)

        self._filters = QMenu(title='File extension filtering')
        self.actions['fall'] = QAction('No filter (*)')
        self.actions['fxvol'] = QAction('PySisyphe volume (*.xvol)')
        self.actions['fxroi'] = QAction('PySisyphe ROI (*.xroi)')
        self.actions['fnii'] = QAction('Nifti (*.nii)')
        self.actions['fniigz'] = QAction('Nifti (*.nii.gz)')
        self.actions['fall'].setData('*')
        self.actions['fxvol'].setData('*.xvol')
        self.actions['fxroi'].setData('*.xroi')
        self.actions['fnii'].setData('*.nii')
        self.actions['fniigz'].setData('*.nii.gz')
        self.actions['fall'].setCheckable(True)
        self.actions['fxvol'].setCheckable(True)
        self.actions['fxroi'].setCheckable(True)
        self.actions['fnii'].setCheckable(True)
        self.actions['fniigz'].setCheckable(True)
        self._filtergroup = QActionGroup(self._filters)
        self._filtergroup.addAction(self.actions['fall'])
        self._filtergroup.addAction(self.actions['fxvol'])
        self._filtergroup.addAction(self.actions['fxroi'])
        self._filtergroup.addAction(self.actions['fnii'])
        self._filtergroup.addAction(self.actions['fniigz'])
        self._filtergroup.setExclusionPolicy(QActionGroup.ExclusionPolicy.Exclusive)
        self._filters.addAction(self.actions['fall'])
        self._filters.addAction(self.actions['fxvol'])
        self._filters.addAction(self.actions['fxroi'])
        self._filters.addAction(self.actions['fnii'])
        self._filters.addAction(self.actions['fniigz'])
        self.actions['fall'].setChecked(True)
        self._filters.triggered.connect(self._filterUpdate)

        self._treedir.addAction(self.actions['copyd'])
        self._treedir.addAction(self.actions['cutd'])

        self._listfiles.addAction(self.actions['copyf'])
        self._listfiles.addAction(self.actions['cutf'])

        # Icons

        import darkdetect
        if darkdetect.isDark(): icondir = 'darkroi'
        else: icondir = 'lightroi'
        import Sisyphe.gui
        path = join(dirname(Sisyphe.gui.__file__), icondir)
        self._icn_folder = QIcon(join(path, 'folder.png'))
        self._icn_head = QIcon(join(path, 'head.png'))
        self._icn_bitmap = QIcon(join(path, 'bitmap.png'))
        self._icn_xml = QIcon(join(path, 'xml.png'))
        self._icn_json = QIcon(join(path, 'json.png'))
        self._icn_roi = QIcon(join(path, 'roi.png'))
        self._icn_mesh = QIcon(join(path, 'mesh.png'))
        self._icn_tracking = QIcon(join(path, 'tracking-atlas.png'))
        self._icn_360 = QIcon(join(path, '360.png'))
        self._icn_labels = QIcon(join(path, 'labels.png'))
        self._icn_target = QIcon(join(path, 'target.png'))
        self._icn_palette = QIcon(join(path, 'palette.png'))
        self._icn_sheet = QIcon(join(path, 'sheet.png'))
        self._icn_scan = QIcon(join(path, 'scan.png'))
        self._icn_model = QIcon(join(path, 'model.png'))
        self._icn_frame = QIcon(join(path, 'frame.png'))
        self._icn_workflow = QIcon(join(path, 'workflow.png'))
        self._icn_page = QIcon(join(path, 'page.png'))

        self._treedir.selectionModel().currentChanged.connect(self._currentDirChanged)
        self._listfiles.selectionModel().currentChanged.connect(self._currentFileChanged)
        self._listfiles.doubleClicked.connect(self._open)
        self._listfiles.customContextMenuRequested.connect(self._popupFiles)
        self._watcher.directoryChanged.connect(self._updateDir)

        # Select current directory (~/.PySisyphe)

        home = abspath(join(QDir.homePath(), '.PySisyphe'))
        index = self._filemodel.index(home, 0)
        self._treedir.expand(index)
        self._treedir.setCurrentIndex(index)
        self._treedir.scrollTo(index)

        self.setLayout(self._layout)

    """
    Private attributes
    
    _currentfile        str, current filename
    _preview            QTabWidget
    _layout             QHBoxLayout, widget main layout
    _filemodel          QFileSystemModel, model of the directories
    _proxymodel         FileFilterProxyModel, model of the files
    _treedir            QTreeView of directories
    _listfiles          QTreeView of files
    _fig                Figure, image preview
    _imagepreview       FigureCanvas
    _ax                 Axe
    _tabtextpreview     QWidget, text preview tab widget
    _tabtablepreview    QWidget, table preview tab widget
    _tabimagepreview    QWidget, image preview tab widget
    _tablepreview       QTableView, image preview widget
    _textpreview        QPlainTextEdit, text preview widget
    _btsavetext         QPushButton, save text
    _bttablesave        QPushButton, save table
    _bttableconsole     QPushButton, copy table to console
    _btsaveimage        QPushButton, save image
    _btocr              QPushButton, perform image ocr
    _actions            dict[str, QAction], popup menu QAction
    """

    # Private methods

    def _filterUpdate(self, action: QAction) -> None:
        self._filter = action.data()
        index = self._treedir.selectedIndexes()
        if index:
            if len(index) > 0:
                index = index[0]
                self._currentDirChanged(index, None)

    def _tabVisibility(self,
                       text: bool = False,
                       table: bool = False,
                       image: bool = False,
                       source: bool = False)  -> None:
        self._preview.setTabVisible(0, text)
        self._preview.setTabVisible(1, table)
        self._preview.setTabVisible(2, image)
        # < Revision 12/02/2026
        self._preview.setTabVisible(3, source)
        # Revision 12/02/2026 >

    def _updateDir(self, path: str) -> None:
        if exists(path):
            index = self._filemodel.index(path)
            if index == self._treedir.currentIndex():
                self._currentDirChanged(index, None)

    # noinspection unused-parameter, unresolved-references
    def _currentDirChanged(self, current: QModelIndex, previous: QModelIndex) -> None:
        path = self._filemodel.filePath(current)
        self._watcher.removePaths(self._watcher.directories())
        if exists(path):
            chdir(path)
            self._watcher.addPath(path)
            from Sisyphe.core.sisypheConstants import (getImageExt,
                                                       getBitmapExt)
            kb = 1024
            mb = 1024 ** 2
            model = self._listfiles.model()
            model.removeRows(0, model.rowCount())
            paths = list(Path(path).glob(self._filter))
            if len(paths) > 0:
                for filepath in paths:
                    if filepath.is_file():
                        ext = filepath.suffix
                        if ext == '': icn = self._icn_page
                        elif ext == '.xvol': icn =self._icn_head
                        elif ext in getImageExt(): icn = self._icn_head
                        elif ext in getBitmapExt(): icn = self._icn_bitmap
                        elif ext == '.xml': icn = self._icn_xml
                        elif ext == '.json': icn = self._icn_json
                        elif ext == '.xroi': icn = self._icn_roi
                        elif ext == '.xmesh': icn = self._icn_mesh
                        elif ext == '.xtracts': icn = self._icn_tracking
                        elif ext in ('.xtrf', '.xtrfs'): icn = self._icn_360
                        elif ext == '.xlabels': icn = self._icn_labels
                        elif ext in ('.xtools', '.xline', '.xpoint'): icn = self._icn_target
                        elif ext in ('.lut', '.xlut'): icn = self._icn_palette
                        elif ext in ('.xlsx', '.csv', '.xsheet', '.npy'): icn = self._icn_sheet
                        elif ext in ('.xdcm', '.dcm', '.dicom', '.nema'): icn = self._icn_scan
                        elif ext == '.xmodel': icn = self._icn_model
                        elif ext == '.xfid': icn = self._icn_frame
                        elif ext == '.xwflow': icn = self._icn_workflow
                        else: icn = self._icn_page
                        item = QStandardItem(icn, filepath.name)
                        item.setData(filepath, Qt.UserRole)
                        size = filepath.stat().st_size
                        if size < kb: size = '{} B'.format(size)
                        elif kb <= size < mb: size = '{:.2f} KB'.format(size / kb)
                        else: size = '{:.2f} MB'.format(size / mb)
                        last = date.fromtimestamp(filepath.stat().st_mtime).strftime('%d-%m-%Y')
                        model.appendRow(item)
                        row = item.row()
                        model.setItem(row, 1, QStandardItem(size))
                        model.setItem(row, 2, QStandardItem(last))
            self._treedir.expand(current)

    # noinspection unused-parameter, unresolved-references
    def _currentFileChanged(self, current: QModelIndex, previous: QModelIndex):
        try: filename = abspath(self._listfiles.model().data(current, Qt.UserRole))
        except: return
        self._currentfile = filename
        ext = splitext(filename)[1].lower()
        if ext in ('.xml', '.md', '.rst', '.txt', '.json', '.log', '.xlut', '.xfid', '.xtrf', '.xtrfs',
                   '.xmesh','.xtools','.xline', '.xpoint', '.xtract', '.xidentity', '.xacq', '.xdisplay',
                   '.xacpc', '.xdcm', '.xmodel', '.xwflow', '.xlabels', '.xbvec', '.xbval', '.bvec', '.bval'):
            # Text tab
            self._tabVisibility(text=True, source=self._chksource.isChecked())
            if ext == '.xlut':
                from Sisyphe.core.sisypheLUT import SisypheLut
                v = SisypheLut()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xfid':
                from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
                v = SisypheFiducialBox()
                v.loadFromXML(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xtrf':
                from Sisyphe.core.sisypheTransform import SisypheTransform
                v = SisypheTransform()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xtrfs':
                from Sisyphe.core.sisypheTransform import SisypheTransforms
                v = SisypheTransforms()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xmesh':
                from Sisyphe.core.sisypheMesh import SisypheMesh
                wait = DialogWait()
                wait.open()
                wait.setInformationText('{} preview...'.format(basename(filename)))
                v = SisypheMesh()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
                wait.close()
            elif ext == '.xtools':
                from Sisyphe.core.sisypheTools import ToolWidgetCollection
                v = ToolWidgetCollection()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xline':
                from Sisyphe.core.sisypheTools import LineWidget
                v = LineWidget('')
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xpoint':
                from Sisyphe.core.sisypheTools import HandleWidget
                v = HandleWidget('')
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xtract':
                from Sisyphe.core.sisypheTracts import SisypheStreamlines
                v = SisypheStreamlines()
                v.load(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xidentity':
                from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
                v = SisypheIdentity()
                v.loadFromXML(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xacq':
                from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
                v = SisypheAcquisition()
                v.loadFromXML(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xdisplay':
                from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
                v = SisypheDisplay()
                v.loadFromXML(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xacpc':
                from Sisyphe.core.sisypheImageAttributes import SisypheACPC
                v = SisypheACPC()
                v.loadFromXML(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xdcm':
                from Sisyphe.core.sisypheDicom import XmlDicom
                v = XmlDicom()
                v.loadXmlDicomFilename(filename)
                self._textpreview.setPlainText(str(v))
            elif ext == '.xmodel':
                from Sisyphe.core.sisypheStatistics import SisypheDesign
                v = SisypheDesign()
                # < Revision 10/09/2026
                v.load(filename, binary=False)
                # Revision 10/09/2026 >
                self._textpreview.setPlainText(str(v))
            elif ext == '.xlabels':
                v = SisypheVolume()
                v.load(filename, binary=False)
                if v.acquisition.hasLabels():
                    self._textpreview.setPlainText(v.acquisition.labelsToStr())
            # < Revision 30/09/2026
            elif ext == '.xbval':
                from Sisyphe.core.sisypheDicom import loadBVal
                r = loadBVal(filename, format='xml')
                self._textpreview.setPlainText(str(r))
            elif ext == '.xbvec':
                from Sisyphe.core.sisypheDicom import loadBVec
                r = loadBVec(filename, format='xml')
                self._textpreview.setPlainText(str(r))
            # Revision 30/09/2026 >
            # XML tab
            if ext in ('.xml', '.md', '.rst', '.txt', '.json', '.log', '.bvec', '.bval'):
                with open(filename, 'r') as f:
                    lines = f.read()
                if ext == '.xml':
                    self._tabVisibility(source=True)
                    self._preview.setCurrentIndex(3)
                    self._xmlpreview.setPlainText(lines)
                elif ext in ('.txt', '.json', '.log', '.bval', '.bvec'):
                    self._tabVisibility(text=True)
                    self._preview.setCurrentIndex(0)
                    self._textpreview.setPlainText(lines)
                elif exit in ('.rst', '.md') :
                    self._tabVisibility(text=True)
                    self._preview.setCurrentIndex(0)
                    self._textpreview.document().setMarkdown(lines)
            elif self._chksource.isChecked() and ext[1] == 'x':
                with open(filename, 'r') as f:
                    lines = f.read()
                self._xmlpreview.setPlainText(lines)
            else: self._xmlpreview.clear()
        elif ext in ('.xvol', '.xroi'):
            self._tabVisibility(text=True, source=self._chksource.isChecked())
            self._preview.setCurrentIndex(0)
            # XML tab
            if self._chksource.isChecked():
                stop = '</{}>\n'.format(ext[1:])
                with open(filename, 'rb') as f:
                    line = ''
                    lines = ''
                    while line != stop:
                        line = f.readline().decode()  # Convert binary to utf-8
                        lines += line
                    self._xmlpreview.setPlainText(lines)
            # Text tab
            v = ''
            if ext == '.xvol':
                v = SisypheVolume()
                v.load(filename, binary=False)
            elif ext == '.xroi':
                from Sisyphe.core.sisypheROI import SisypheROI
                v = SisypheROI()
                v.load(filename)
            self._textpreview.setPlainText(str(v))
        elif ext in ('.nii', '.hdr', '.img', '.nia', '.gz'):
            from Sisyphe.core.sisypheImageIO import readFromNIFTI
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromNIFTI(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext in ('.nrrd', '.nhdr'):
            from Sisyphe.core.sisypheImageIO import readFromNRRD
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromNRRD(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext in ('.mnc', '.minc'):
            from Sisyphe.core.sisypheImageIO import readFromMINC
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromMINC(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext in ('.mgh', '.mgz'):
            from Sisyphe.core.sisypheImageIO import readFromFreeSurferMGH
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromFreeSurferMGH(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext == '.vol':
            from Sisyphe.core.sisypheImageIO import readFromSisyphe
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromSisyphe(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r[1]))
            wait.close()
        elif ext == '.vmr':
            from Sisyphe.core.sisypheImageIO import readFromBrainVoyagerVMR
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromBrainVoyagerVMR(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext in ('.vtk', '.vti'):
            from Sisyphe.core.sisypheImageIO import readFromVTK
            wait = DialogWait()
            wait.open()
            wait.setInformationText('{} preview...'.format(basename(filename)))
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            try: r = readFromVTK(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
            wait.close()
        elif ext == '.xfm':
            from Sisyphe.core.sisypheTransform import SisypheTransform
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            r = SisypheTransform()
            try: r.loadFromXfmTransform(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
        elif ext == '.tfm':
            from Sisyphe.core.sisypheTransform import SisypheTransform
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            r = SisypheTransform()
            try: r.loadFromTfmTransform(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
        elif ext == '.trf':
            from Sisyphe.core.sisypheTransform import SisypheTransform
            self._tabVisibility(text=True)
            self._preview.setCurrentIndex(0)
            r = SisypheTransform()
            try: r.loadFromBrainVoyagerTransform(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(r))
        elif ext in ('.npy', '.npz'):
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import numpy as np
            # noinspection PyUnusedLocal
            try:
                r = np.load(filename, allow_pickle=True)
                df = DataFrame(r)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
        elif ext == '.csv':
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import pandas as pd
            # noinspection PyUnusedLocal
            try:
                df = pd.read_csv(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
        elif ext == '.xlsx':
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import pandas as pd
            # noinspection PyUnusedLocal
            try:
                df = pd.read_excel(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                # < Revision 19/02/2026
                try: import openpyxl
                except:
                    if hasattr(sys, '_MEIPASS'):
                        messageBox(self,
                                   'XLSX IO',
                                   'OpenPyXL module is not installed.\n'
                                   'Please perform a complete reinstallation of the latest version '
                                   'of PySisyphe, which can be downloaded from '
                                   'https://github.com/PySisyphe/Sisyphe.')
                    else:
                        messageBox(self,
                                   'XLSX IO',
                                   'OpenPyXL module is not installed.\n'
                                   'Please install it using "pip install openpyxl==3.1.5" from your venv console.')
                # Revision 19/02/2026 >
                self._tabVisibility()
                return
        elif ext == '.xsheet':
            self._tabVisibility(table=True, source=self._chksource.isChecked())
            self._preview.setCurrentIndex(1)
            from Sisyphe.core.sisypheSheet import SisypheSheet
            df = SisypheSheet()
            try:
                df.load(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
            if self._chksource.isChecked():
                with open(filename, 'r') as f:
                    lines = f.read()
                self._xmlpreview.setPlainText(lines)
        elif ext == '.sav':   # SPSS format
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import pandas as pd
            # noinspection PyUnusedLocal
            try:
                df = pd.read_spss(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
        elif ext == '.dta':  # Stata format
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import pandas as pd
            # noinspection PyUnusedLocal
            try:
                df = pd.read_stata(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
        elif ext == '.sas7bdat':  # SAS format
            self._tabVisibility(table=True)
            self._preview.setCurrentIndex(1)
            import pandas as pd
            # noinspection PyUnusedLocal
            try:
                df = pd.read_sas(filename)
                model = PandasTableModel(df)
                self._tablepreview.setModel(model)
            except:
                self._tabVisibility()
                return
        elif ext in ('.bmp', '.eps', '.jpg', '.jpeg', '.pcx', '.pfm', '.png', '.pbm',
                     '.pgm', '.ppm', '.pnm', '.tga', '.tiff', '.webp', '.xbm', '.xpm'):
            self._tabVisibility(image=True)
            self._preview.setCurrentIndex(2)
            self._btocr.setVisible(True)
            from PIL import Image
            try: img = Image.open(filename)
            except:
                self._tabVisibility()
                return
            self._imagepreview2.resize(QSize(self._area.width() - 20, self._area.height() - 20))
            self._fig.clear()
            ax = self._fig.add_subplot(111)
            ax.axis('off')
            ax.imshow(img)
            self._imagepreview.draw_idle()
        elif ext == '.pdf':
            try: import pymupdf
            except:
                # < Revision 19/02/2026
                if hasattr(sys, '_MEIPASS'):
                    messageBox(self,
                               'PDF IO',
                               'PyMuPDF module is not installed.\n'
                               'Please perform a complete reinstallation of the latest version '
                               'of PySisyphe, which can be downloaded from '
                               'https://github.com/PySisyphe/Sisyphe.')
                else:
                    messageBox(self,
                               'PDF IO',
                               'PyMuPDF module is not installed.\n'
                               'Please install it using "pip install PyMuPDF==1.26.7" from your venv console.')
                return
                # Revision 19/02/2026 >
            # as text
            # noinspection PyUnusedLocal
            self._tabVisibility(text=True, image=True)
            self._preview.setCurrentIndex(2)
            self._btocr.setVisible(False)
            try: doc = pymupdf.open(filename)
            except:
                self._tabVisibility()
                return
            lines = ''
            i: cython.int
            for i in range(doc.page_count):
                page = doc.load_page(i)
                lines += page.get_text()
            self._textpreview.setPlainText(lines)
            # as image(s)
            self._fig.clear()
            for i in range(doc.page_count):
                ax = self._fig.add_subplot(doc.page_count, 1, i+1)
                ax.axis('off')
                page = doc.load_page(i)
                pixmap = page.get_pixmap(dpi=300)
                img = pixmap.pil_image()
                ax.imshow(img)
            # noinspection PyUnboundLocalVariable
            self._imagepreview2.resize(QSize(img.width, img.height * doc.page_count))
            self._imagepreview.draw_idle()
            self._resetzoom()
        elif ext in ('.dcm', '.dicom', '.ima', '.nema') or isDicom(filename):
            self._tabVisibility(text=True, image=True)
            if self._preview.currentIndex() == 1:
                self._preview.setCurrentIndex(0)
            import pydicom as pd
            try: ds = pd.dcmread(filename)
            except:
                self._tabVisibility()
                return
            self._textpreview.setPlainText(str(ds))
            # (0x7FE0, 0x0010) Pixel Data
            if (0x7FE0, 0x0010) in ds:
                self._fig.clear()
                ax = self._fig.add_subplot(111)
                ax.axis('off')
                ax.imshow(ds.pixel_array, cmap='gray')
                self._imagepreview.draw_idle()
            else: self._tabVisibility(text=True)

    def _popupFolder(self, pos: QPoint) -> None:
        index = self._treedir.indexAt(pos)
        if index:
            popup = QMenu(self._treedir)
            if self._clipboard:
                popup.addAction(self.actions['paste'])
                popup.addSeparator()
            popup.addAction(self.actions['copyd'])
            popup.addAction(self.actions['cutd'])
            popup.addSeparator()
            popup.addAction(self.actions['rename1'])
            popup.addAction(self.actions['folder'])
            popup.addAction(self.actions['rmdir'])
            # < Revision 16/06/2026
            popup.addSeparator()
            popup.addAction(self.actions['explorer'])
            popup.addAction(self.actions['user'])
            popup.addAction(self.actions['template'])
            # Revision 16/06/2026 >
            popup.exec_(self._treedir.mapToGlobal(pos))

    # noinspection unresolved-references
    def _popupFiles(self, pos: QPoint) -> None:
        sindex = self._listfiles.selectedIndexes()
        popup = QMenu(self._listfiles)
        popup.addMenu(self._filters)
        if len(sindex) > 0:
            try: filename = abspath(self._listfiles.model().data(sindex[0], Qt.UserRole))
            except: return
            ext = splitext(filename)[1]
            if ext in ('.xlabels', '.nii', '.hdr', '.img', '.nia', '.nrrd', '.nhdr', '.mnc',
                       '.minc', '.mgh', '.mgz', '.vol', '.vmr', '.vtk', '.vti', '.xmodel',
                       '.xlabels', '.xdcm', '.xwflow'):
                popup.addAction(self.actions['open'])
                popup.addSeparator()
            elif ext == '.gz':
                if filename.split('.')[-2] in ('nii', 'img'):
                    popup.addAction(self.actions['open'])
                    popup.addSeparator()
            elif ext in ('.dcm', '.dicom', '.ima', '.nema'):
                popup.addAction(self.actions['open'])
                popup.addAction(self.actions['edit'])
                popup.addSeparator()
            elif ext == '.xvol':
                popup.addAction(self.actions['open'])
                popup.addAction(self.actions['edit'])
                popup.addAction(self.actions['console'])
                popup.addSeparator()
                popup.addAction(self.actions['acpc'])
                popup.addAction(self.actions['frame'])
                popup.addAction(self.actions['reorient'])
                popup.addSeparator()
            popup.addAction(self.actions['copyf'])
            popup.addAction(self.actions['cutf'])
            popup.addSeparator()
            popup.addAction(self.actions['rename2'])
            popup.addAction(self.actions['remove'])
        else:
            if self._clipboard:
                popup.addAction(self.actions['paste'])
                popup.addSeparator()
            popup.addAction(self.actions['selectall'])
            popup.addSeparator()
            popup.addAction(self.actions['folder'])
            popup.addSeparator()
            popup.addAction(self.actions['explorer'])
        popup.exec_(self._listfiles.mapToGlobal(pos))

    def _popupTable(self, pos: QPoint) -> None:
        popup = QMenu()
        popup.addAction(self.actions['savec'])
        popup.addAction(self.actions['savet'])
        if self.hasMainWindow():
            popup.addAction(self.actions['copyc'])
            popup.addAction(self.actions['copyt'])
        popup.exec_(self._tabtablepreview.mapToGlobal(pos))

    # noinspection unresolved-references
    def _open(self, index: QModelIndex | None = None) -> None:
        if self.hasMainWindow():
            if index is None:
                index = self._listfiles.selectedIndexes()
                if len(index) > 0: index = index[0]
                else: return
            try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
            except: return
            ext = splitext(filename)[1].lower()
            v = None
            wait = DialogWait()
            if  ext == '.xvol':
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.load(filename)
            elif ext in ('.nii', '.hdr', '.img', '.nia', '.gz'):
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromNIFTI(filename)
                v.save()
            elif ext in ('.nrrd', '.nhdr'):
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromNRRD(filename)
                v.save()
            elif ext in ('.mnc', '.minc'):
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromMINC(filename)
                v.save()
            elif ext in ('.mgh', '.mgz'):
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromFreeSurferMGH(filename)
                v.save()
            elif ext == '.vol':
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromSisyphe(filename)
                v.save()
            elif ext == '.vmr':
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromBrainVoyagerVMR(filename)
                v.save()
            elif ext in ('.vtk', '.vti'):
                wait.open()
                wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.loadFromVTK(filename)
                v.save()
            elif ext == '.xlabels':
                filename = filename.replace('.xlabels', '.xvol')
                if exists(filename):
                    self._mainWindow.editLabels(filename)
                    return
            elif ext == '.xmodel':
                action = QAction(basename(filename))
                action.setData(filename)
                # noinspection PyProtectedMember
                self._mainWindow._openModel(action)
                return
            elif ext == '.xwflow':
                action = QAction(basename(filename))
                action.setData(filename)
                # < Revision 14/05/2026
                # self._mainWindow_openWorkflow(action)
                # noinspection PyProtectedMember
                self._mainWindow._openWorkflow(action)
                # Revision 14/05/2026 >
                return
            elif ext == '.xdcm':
                # < Revision 12/05/2026
                self._mainWindow.xmlDicom(filename)
                return
                # Revision 12/05/2026 >
            elif ext in ('.dcm', '.dicom', '.nema') or isDicom(filename):
                # < Revision 12/05/2026
                self._mainWindow.datasetDicom(filename)
                return
                # Revision 12/05/2026 >
            if v:
                self._mainWindow.addVolume(v)
                wait.close()

    def _openExplorer(self) -> None:
        folder = abspath(self._filemodel.filePath(self._treedir.currentIndex()))
        if sys.platform == 'win32': subprocess.Popen('explorer "{}"'.format(folder))
        elif sys.platform == 'darwin': subprocess.call(["open", folder])

    def _userFolder(self) -> None:
        folder = abspath(join(expanduser('~'), '.PySisyphe'))
        index = self._filemodel.index(folder, 0)
        self._treedir.expand(index)
        self._treedir.scrollTo(index)
        self._treedir.setCurrentIndex(index)
        self._currentDirChanged(index, None)

    def _templateFolder(self) -> None:
        import Sisyphe
        folder = abspath(join(dirname(Sisyphe.__file__), 'templates'))
        index = self._filemodel.index(folder, 0)
        self._treedir.expand(index)
        self._treedir.scrollTo(index)
        self._treedir.setCurrentIndex(index)
        self._currentDirChanged(index, None)

    # noinspection unresolved-references
    def _editAttributes(self) -> None:
        index = self._listfiles.selectedIndexes()
        if len(index) > 0:
            index = index[0]
            try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
            except: return
            ext = splitext(filename)[1]
            if ext == '.xvol':
                v = SisypheVolume()
                v.load(filename)
                from Sisyphe.gui.dialogVolumeAttributes import DialogVolumeAttributes
                dialog = DialogVolumeAttributes(vol=v)
                if sys.platform == 'win32':
                    import pywinstyles
                    if self.hasMainWindow():
                        # noinspection unresolved-references
                        cl = self._mainWindow.palette().base().color()
                    else: cl = self.palette().base().color()
                    # noinspection string-format
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.exec()
                v.save()
            elif ext in ('.dcm', '.dicom', '.ima', '.nema'):
                if self.hasMainWindow():
                    # noinspection unresolved-references
                    self._mainWindow.datasetDicom(filename)
        else: return

    # noinspection unresolved-references
    def _console(self) -> None:
        if self.hasMainWindow():
            index = self._listfiles.selectedIndexes()
            if len(index) > 0:
                index = index[0]
                try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
                except: return
                ext = splitext(filename)[1]
                if ext == '.xvol':
                    v = SisypheVolume()
                    v.load(filename)
                    # noinspection unresolved-references
                    console = self._mainWindow.getConsole()
                    console.pushVariables({'v': v})
                    console.update()
                    messageBox(self, 'Copy volume to console',
                               text='Copy {} to console as "v".'.format(basename(filename)),
                               icon=QMessageBox.Information)

    # noinspection unresolved-references
    def _acpc(self) -> None:
        if self.hasMainWindow():
            index = self._listfiles.selectedIndexes()
            if len(index) > 0:
                index = index[0]
                try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
                except: return
                ext = splitext(filename)[1]
                if ext == '.xvol':
                    v = SisypheVolume()
                    v.load(filename)
                    # noinspection unresolved-references
                    self._mainWindow.acpcSelection(v)

    # noinspection unresolved-references
    def _frame(self) -> None:
        if self.hasMainWindow():
            index = self._listfiles.selectedIndexes()
            if len(index) > 0:
                index = index[0]
                try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
                except: return
                ext = splitext(filename)[1]
                if ext == '.xvol':
                    v = SisypheVolume()
                    v.load(filename)
                    # noinspection unresolved-references
                    self._mainWindow.frameDetection(v)

    # noinspection unresolved-references
    def _reorient(self) -> None:
        if self.hasMainWindow():
            index = self._listfiles.selectedIndexes()
            if len(index) > 0:
                index = index[0]
                try: filename = abspath(self._listfiles.model().data(index, Qt.UserRole))
                except: return
                ext = splitext(filename)[1]
                if ext == '.xvol':
                    v = SisypheVolume()
                    v.load(filename)
                    # noinspection unresolved-references
                    self._mainWindow.reorient(v)

    def _zoomin(self) -> None:
        height = int(self._imagepreview2.height() * 1.1)
        width = int(self._imagepreview2.width() * 1.1)
        self._imagepreview2.resize(QSize(width, height))

    def _zoomout(self) -> None:
        height = int(self._imagepreview2.height() * 0.9)
        width = int(self._imagepreview2.width() * 0.9)
        self._imagepreview2.resize(QSize(width, height))

    def _resetzoom(self) -> None:
        ext = splitext(self._currentfile)[1].lower()
        if ext == '.pdf':
            f = self._imagepreview2.width() / (self._area.width() - 20)
            self._imagepreview2.resize(QSize(self._area.width() - 20, int(self._imagepreview2.height() / f)))
        else: self._imagepreview2.resize(QSize(self._area.width() - 20, self._area.height() - 20))

    def _transposeTable(self) -> None:
        model = self._tablepreview.model()
        # noinspection PyUnresolvedReferences
        if model.hasDataFrame():
            # noinspection PyUnresolvedReferences
            df = model.getDataFrame()
            df = df.T
            model = PandasTableModel(df)
            self._tablepreview.setModel(model)

    # < Revision 12/02/2026
    # add _importTable method
    def _importTable(self, action: QAction) -> None:
        sep = ''
        c = action.text()
        if c == 'space separator': sep = ' '
        elif c == 'tab separator': sep = '\t'
        elif c == '"," separator': sep = ','
        elif c == '";" separator': sep = ';'
        elif c == '"|" separator': sep = '|'
        if sep != '':
            n = 0
            r = dict()
            lines = self._textpreview.toPlainText().split('\n')
            i: cython.int
            for line in lines:
                buff: list[float | str] = line.split(sep)
                nc = len(buff)
                if nc > 1:
                    if len(r) == 0:
                        n = nc
                        if isinstance(buff[0], str):
                            for i in range(n):
                                r[buff[i]] = list()
                        else:
                            for i in range(n):
                                r[i] = list()
                                r[i].append(buff[i])
                        continue
                    if n == nc:
                        for i, k in enumerate(r):
                            try: buff[i] = float(buff[i])
                            except: pass
                            r[k].append(buff[i])
                else: continue
            if len(r) > 1:
                df = DataFrame.from_dict(r)
                self._tabVisibility(text=True, table=True)
                self._preview.setCurrentIndex(1)
                model = PandasTableModel(df, editable=True)
                self._tablepreview.setModel(model)
                return
        messageBox(self, 'Table import',
                   text='There is no valid table in {}.'.format(basename(self._currentfile)),
                   icon=QMessageBox.Information)
    # Revision 12/02/2026 >

    def _saveText(self) -> None:
        if self._currentfile != '':
            path, ext = splitext(self._currentfile)
            filename = path + ext.lower()
            filename = QFileDialog.getSaveFileName(None, 'Save text',filename,
                                                   filter='Text file (*.txt)')[0]
            if filename:
                buff = self._textpreview.toPlainText()
                with open(filename, 'w') as f:
                    f.write(buff)

    def _saveXml(self) -> None:
        if self._currentfile != '':
            ext = splitext(self._currentfile)[1]
            filename = QFileDialog.getSaveFileName(None, 'Save text', self._currentfile,
                                                   filter=ext)[0]
            if filename:
                buff = self._xmlpreview.toPlainText()
                with open(filename, 'w') as f:
                    f.write(buff)

    def _saveTable(self) -> None:
        if self._currentfile != '':
            model = self._tablepreview.model()
            # noinspection PyUnresolvedReferences
            if model.hasDataFrame():
                # noinspection PyUnresolvedReferences
                df = model.getDataFrame()
                path, ext = splitext(self._currentfile)
                filename = QFileDialog.getSaveFileName(None, 'Save table', path,
                                                       filter='CSV (*.csv);; JSON (*.json);; HTML (*.html);; '
                                                              'Numpy (*.npy);; Excel (*.xlsx)')[0]
                if filename:
                    ext = splitext(filename)[1].lower()
                    if ext == '.csv': df.to_csv(filename)
                    elif ext == '.json': df.to_json(filename)
                    elif ext == '.html': df.to_html(filename)
                    elif ext == '.npy':
                        r = df.to_numpy()
                        import numpy as np
                        np.save(filename, r)
                    elif ext == '.xlsx':
                        try: df.to_excel(filename)
                        except:
                            # < Revision 19/02/2026
                            try: import openpyxl
                            except:
                                if hasattr(sys, '_MEIPASS'):
                                    messageBox(self,
                                               'XLSX IO',
                                               'OpenPyXL module is not installed.\n'
                                               'Please perform a complete reinstallation of the latest version '
                                               'of PySisyphe, which can be downloaded from '
                                               'https://github.com/PySisyphe/Sisyphe.')
                                else:
                                    messageBox(self,
                                               'XLSX IO',
                                               'OpenPyXL module is not installed.\n'
                                               'Please install it using "pip install openpyxl==3.1.5" from your venv console.')
                            # Revision 19/02/2026 >

    # noinspection unresolved-references
    def _saveTableSelection(self) -> None:
        model = self._tablepreview.model()
        if model.hasDataFrame():
            selectmodel = self._tablepreview.selectionModel()
            if selectmodel.hasSelection():
                index = selectmodel.selectedColumns(0)
                if len(index) > 0:
                    col = index[0].column()
                    df = model.getDataFrame()
                    hdr = df.columns[col]
                    if isinstance(hdr, int): hdr = 'col{}'.format(hdr)
                    elif isinstance(hdr, str):
                        if hdr.isnumeric(): hdr = 'col{}'.format(hdr)
                        else: hdr = hdr.replace(' ', '_').lower()
                    else: return
                    if hdr[:3] == 'col':
                        path = splitext(self._currentfile)[0] + '_{}'.format(hdr)
                    else: path = abspath(join(dirname(self._currentfile), hdr))
                    filename = QFileDialog.getSaveFileName(None, 'Save selected column', path,
                                                           filter='Numpy (*.npy)')[0]
                    if filename:
                        r = df.to_numpy()[:, col]
                        import numpy as np
                        np.save(filename, r)

    def _saveImage(self) -> None:
        if self._currentfile != '':
            path, ext = splitext(self._currentfile)
            filename = QFileDialog.getSaveFileName(None, 'Save bitmap', path,
                                                   filter='BMP (*.bmp);; JPEG (*.jpg);; PNG (*.png);; '
                                                          'TGA (*.tga);; TIFF (*.tiff);; WebP (*.webp)')[0]
            if filename:
                buff = BytesIO()
                self._fig.savefig(buff)
                buff.seek(0)
                img = Image.open(buff)
                img.save(filename)

    # noinspection unresolved-references
    def _copyTableToConsole(self) -> None:
        if self.hasMainWindow():
            model = self._tablepreview.model()
            if model.hasDataFrame():
                console = self._mainWindow.getConsole()
                if console is not None:
                    df = model.getDataFrame()
                    console.pushVariables({'df': df})
                    console.update()
                    messageBox(self, 'Copy table to console',
                               text='Copy table to console as pandas DataFrame "df".',
                               icon=QMessageBox.Information)

    # noinspection unresolved-references
    def _copyColumnToConsole(self) -> None:
        if self.hasMainWindow():
            model = self._tablepreview.model()
            # noinspection PyUnresolvedReferences
            if model.hasDataFrame():
                console = self._mainWindow.getConsole()
                if console is not None:
                    selectmodel = self._tablepreview.selectionModel()
                    if selectmodel.hasSelection():
                        index = selectmodel.selectedColumns(0)
                        if len(index) > 0:
                            col = index[0].column()
                            # noinspection PyUnresolvedReferences
                            df = model.getDataFrame()
                            hdr = df.columns[col]
                            if isinstance(hdr, int): hdr = 'vcol{}'.format(hdr)
                            elif isinstance(hdr, str):
                                if hdr.isnumeric(): hdr = 'vcol{}'.format(hdr)
                                else: hdr = hdr.replace(' ', '_').lower()
                            else: return
                            v = df.to_numpy()[:, col]
                            console.pushVariables({hdr: v})
                            console.update()
                            messageBox(self, 'Copy table to console',
                                       text='Copy selected column to console as numpy array "{}".'.format(hdr),
                                       icon=QMessageBox.Information)

    # noinspection unresolved-references
    def _ocr(self) -> None:
        index = self._listfiles.currentIndex()
        if index:
            try: import easyocr
            except:
                if hasattr(sys, '_MEIPASS'):
                    messageBox(self,
                               'Image OCR',
                               'Easyocr module is not installed.\n'
                               'Please perform a complete reinstallation of the latest version '
                               'of PySisyphe, which can be downloaded from '
                               'https://github.com/PySisyphe/Sisyphe.')
                else:
                    messageBox(self,
                               'Image OCR',
                               'Easyocr module is not installed.\n'
                               'Please install it using "pip install easyocr==1.7.2" from your venv console.')
                self._btocr.setVisible(False)
                return
            wait = DialogWait()
            wait.open()
            wait.setInformationText('OCR processing...')
            filename = self._proxymodel.filePath(index)
            reader = easyocr.Reader(['en'])
            png = splitext(filename)[0] + '.png'
            flag = False
            if not exists(png):
                img = Image.open(filename)
                img.save(png)
                flag = True
            ocr = reader.readtext(png)
            lines = ''
            if isinstance(ocr, list):
                n = len(ocr)
                if n > 0:
                    i: cython.int
                    for i in range(n):
                        lines += str(ocr[i][1]) + '\n'
                self._tabVisibility(text=True, image=True)
                self._preview.setCurrentIndex(0)
                self._textpreview.setPlainText(lines)
                if self.hasMainWindow():
                    self._mainWindow.getConsole().pushVariables({'ocr': ocr})
                    self._mainWindow.getConsole().update()
                    wait.hide()
                    messageBox(self, 'Image OCR',
                               text='Copy OCR result to console as list "ocr".',
                               icon=QMessageBox.Information)
            if flag: remove(png)
            wait.close()

    def _renameInTreeFolders(self) -> None:
        index =  self._treedir.selectedIndexes()[0]
        if index: self._treedir.edit(index)

    def _renameInListFiles(self) -> None:
        index =  self._listfiles.selectedIndexes()[0]
        if index: self._listfiles.edit(index)

    # noinspection unresolved-references
    def _removeFile(self) -> None:
        sindex = self._listfiles.selectedIndexes()
        if sindex:
            if len(sindex) > 0:
                r = messageBox(self,
                               'Remove File(s)',
                               'Do you want to delete selected file(s) ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No)
                if r == QMessageBox.Yes:
                    previous = ''
                    files = list()
                    for index in sindex[::3]:
                        try:
                            path = abspath(self._listfiles.model().data(index, Qt.UserRole))
                        except: break
                        if path != previous: files.append(path)
                        previous = path
                    for f in files:
                        remove(f)

    # noinspection unresolved-references
    def _removeDir(self) -> None:
        index = self._treedir.selectedIndexes()[0]
        if index:
            path = self._filemodel.filePath(index)
            r = messageBox(self,
                           'Remove directory',
                           'Do you want to delete {} and its contents ?'.format(path),
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes:
                above = self._treedir.indexAbove(index)
                if above:
                    self._treedir.selectionModel().setCurrentIndex(above, QItemSelectionModel.ClearAndSelect)
                rmtree(path)

    # noinspection unresolved-references
    def _newFolder(self) -> None:
        index = self._treedir.selectedIndexes()
        if index:
            index = index[0]
            path = abspath(join(self._filemodel.filePath(index), 'new folder'))
            i = 0
            while exists(path):
                i += 1
                path = abspath(join(self._filemodel.filePath(index), 'new folder#{}'.format(i)))
            self._treedir.expand(index)
            index = self._filemodel.mkdir(index, basename(path))
            self._treedir.scrollTo(index)
            self._treedir.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
            self._renameInTreeFolders()

    def _copyDir(self) -> None:
        index = self._treedir.selectedIndexes()
        if index:
            index = index[0]
            self._clipboard = [self._filemodel.filePath(index)]
            self._copyflag = True
            self._cutflag = False

    def _cutDir(self) -> None:
        index = self._treedir.selectedIndexes()
        if index:
            index = index[0]
            self._clipboard = [self._filemodel.filePath(index)]
            self._copyflag = False
            self._cutflag = True

    # noinspection unresolved-references
    def _copyFile(self) -> None:
        indexes = self._listfiles.selectedIndexes()
        if indexes:
            if len(indexes) > 0:
                self._clipboard = [self._listfiles.model().data(index, Qt.UserRole) for index in indexes[::3]]
                self._copyflag = True
                self._cutflag = False

    # noinspection unresolved-references
    def _cutFile(self) -> None:
        indexes = self._listfiles.selectedIndexes()
        if indexes:
            if len(indexes) > 0:
                self._clipboard = [self._listfiles.model().data(index, Qt.UserRole) for index in indexes[::3]]
                self._copyflag = False
                self._cutflag = True

    # noinspection unresolved-references
    def _paste(self) -> None:
        index = self._treedir.selectedIndexes()
        if index:
            index = index[0]
            if self._clipboard:
                dst = self._filemodel.filePath(index)
                i: cython.int
                for i in range(len(self._clipboard)):
                    src: str = self._clipboard[i]
                    if exists(src):
                        try:
                            if src != dst:
                                if self._copyflag:
                                    if isdir(src):
                                        dst = abspath(join(dst, Path(src).parts[-1]))
                                        copytree(src, dst)
                                    else: copy(src, dst)
                                elif self._cutflag: move(src, dst)
                        except: pass
                self._copyflag = False
                self._cutflag = False
                self._clipboard = None

    def _selectAll(self) -> None:
        self._listfiles.selectAll()

    # Public methods

    def initSplitterSize(self) -> None:
        width = self._splitter.size().width()
        # noinspection PyTypeChecker
        self._splitter.setSizes([int(width*(4/16)), int(width*(4/16)), width - int(width*(8/16))])

    def setMainWindow(self, window: WindowSisyphe) -> None:
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(window, WindowSisyphe):
            self._mainWindow = window
            self._bttableconsole.setVisible(True)
            self._btcolumnconsole.setVisible(True)

    def getMainWindow(self) -> WindowSisyphe | None:
        return self._mainWindow

    def hasMainWindow(self) -> bool:
        return self._mainWindow is not None
