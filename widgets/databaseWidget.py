"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import join
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import getctime
from os.path import getmtime
from os.path import getsize
from os.path import abspath
from os.path import splitext

from time import ctime
from time import strptime
from time import strftime

from glob import glob

import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheXml import XmlROI
from Sisyphe.core.sisypheXml import XmlVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheDatabase import SisypheDatabase
from Sisyphe.gui.dialogPatient import DialogPatient
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogVolumeAttributes import DialogVolumeAttributes
from Sisyphe.widgets.basicWidgets import messageBox

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QWidget -> DatabaseWidget
"""


class DatabaseWidget(QWidget):
    """
    DatabaseWidget

    Inheritance

    QWidget -> DatabaseWidget

    Last revision: 28/05/2025
    """

    # Class methods

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    @classmethod
    def getIdentityFromItem(cls, item):
        if isinstance(item, QTreeWidgetItem):
            identity = SisypheIdentity()
            identity.setLastname(item.text(0))
            identity.setFirstname(item.text(1))
            identity.setDateOfBirthday(item.text(2))
            return identity
        else: raise TypeError('parameter type {} is not QTreeWidgetItem'.format(type(item)))

    # Special method

    """
    Private attributes

    _db             SisypheDatabase
    _patient        QTreeWidget, patient list
    _files          QTreeWidget, file list for current patient
    _action         dict() of QAction
    _popup          QMenu, menu of the widget, displayed in menu bar
    _popuppatients  QMenu, popup menu for patient list
    _popupfiles     QMenu, popup menu for file list
    _mainwindow     QMainWindow, PySisyphe main window
    + other GUI attributes (button, edit...) not detailed
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._db = SisypheDatabase()
        self._db.setDatabasePathFromSettings()
        self._mainwindow = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._checklastname = QCheckBox()
        self._checklastname.setText('Lastname')
        self._checklastname.setChecked(False)
        self._checklastname.setToolTip('Check box to activate lastname filter edition,\n'
                                       'uncheck box to inactivate filter.')
        # noinspection PyUnresolvedReferences
        self._checklastname.stateChanged.connect(lambda: self._fltlastname.setEnabled(self._checklastname.isChecked()))
        # noinspection PyUnresolvedReferences
        self._checklastname.stateChanged.connect(lambda: self._fltlastname.setText(''))
        self._fltlastname = QLineEdit()
        self._fltlastname.setEnabled(False)
        self._fltlastname.setToolTip('Lastname filter,\n'
                                     'check box on the left to activate lastname filter edition,\n'
                                     'uncheck box on the left to inactivate filter,\n'
                                     'special characters * and ? can be used in filter.')
        # noinspection PyUnresolvedReferences
        self._fltlastname.returnPressed.connect(self._update)
        self._checkfirstname = QCheckBox()
        self._checkfirstname.setText('Firstname')
        self._checkfirstname.setChecked(False)
        self._checkfirstname.setToolTip('Check box to activate filter edition,\n'
                                        'uncheck box to inactivate filter.')
        # noinspection PyUnresolvedReferences
        self._checkfirstname.stateChanged.connect(
            lambda: self._fltfirstname.setEnabled(self._checkfirstname.isChecked()))
        # noinspection PyUnresolvedReferences
        self._checkfirstname.stateChanged.connect(lambda: self._fltfirstname.setText(''))
        self._fltfirstname = QLineEdit()
        self._fltfirstname.setEnabled(False)
        self._fltfirstname.setToolTip('Firstname filter,\n'
                                      'check box on the left to activate firstname filter edition,\n'
                                      'uncheck box on the left to inactivate filter,\n'
                                      'special characters * and ? can be used in filter.')
        # noinspection PyUnresolvedReferences
        self._fltfirstname.returnPressed.connect(self._update)
        self._checkdate = QCheckBox()
        self._checkdate.setText('Date of birthday')
        self._checkdate.setChecked(False)
        self._checkdate.setToolTip('Check box to activate date of birth filter,\n'
                                   'uncheck box to inactivate filter.')
        # noinspection PyUnresolvedReferences
        self._checkdate.stateChanged.connect(lambda: self._fltdob.setEnabled(self._checkdate.isChecked()))
        self._fltdob = QDateEdit()
        self._fltdob.setCalendarPopup(True)
        self._fltdob.setEnabled(False)
        self._fltdob.setToolTip('Date of birth filter,\n'
                                'check box on the left to activate filter edition,\n'
                                'uncheck box on the left to inactivate filter.')
        # self._search = QPushButton(QIcon(join(self.getDefaultIconDirectory(), 'zoom64.png')), 'Search')
        self._search = QPushButton('Search')
        # self._search.setFixedSize(QSize(100, 32))
        self._search.setToolTip('Search patient(s) with lastname,\nfirstname and date of birth filters.')
        # noinspection PyUnresolvedReferences
        self._search.clicked.connect(self._update)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._checklastname)
        layout.addWidget(self._fltlastname)
        layout.addWidget(self._checkfirstname)
        layout.addWidget(self._fltfirstname)
        layout.addWidget(self._checkdate)
        layout.addWidget(self._fltdob)
        layout.addWidget(self._search)
        layout.addStretch()
        self._layout.addLayout(layout)

        self._patients = QTreeWidget()
        self._files = QTreeWidget()
        # < Revision 07/03/2025
        if platform == 'darwin':
            font = self.font()
            font.setPointSize(12)
            self._patients.setFont(font)
            self._files.setFont(font)
        # Revision 07/03/2025 >
        self._patients.setMinimumWidth(300)
        self._patients.setHeaderLabels(['Lastname', 'Firstname', 'Date of birth'])
        # noinspection PyTypeChecker
        self._patients.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._patients.header().setSectionsClickable(True)
        self._patients.header().setSortIndicatorShown(True)
        self._patients.header().setStretchLastSection(False)
        # noinspection PyUnresolvedReferences
        self._patients.header().sectionClicked.connect(self._sortIdentityByColumn)
        self._patients.setAlternatingRowColors(True)
        self._patients.invisibleRootItem()
        self._patients.setSelectionMode(QAbstractItemView.SingleSelection)
        # noinspection PyUnresolvedReferences
        self._patients.itemSelectionChanged.connect(self._updateFileWidget)
        self._patients.setContextMenuPolicy(Qt.CustomContextMenu)
        # noinspection PyUnresolvedReferences
        self._patients.customContextMenuRequested.connect(self._popupItemPatient)

        self._files.setHeaderLabels(['Filename', 'ID', 'Size', 'Last modified', 'Creation'])
        # noinspection PyTypeChecker
        self._files.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._files.header().setSectionsClickable(True)
        self._files.header().setSortIndicatorShown(True)
        self._files.header().setStretchLastSection(False)
        # noinspection PyUnresolvedReferences
        self._files.header().sectionClicked.connect(self._sortFilesByColumn)
        self._files.setAlternatingRowColors(True)
        self._files.invisibleRootItem()
        self._files.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._files.setContextMenuPolicy(Qt.CustomContextMenu)
        # noinspection PyUnresolvedReferences
        self._files.customContextMenuRequested.connect(self._popupItemFile)
        # noinspection PyUnresolvedReferences
        self._files.itemDoubleClicked.connect(self._doubleClicked)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        splitter.addWidget(self._patients)
        splitter.addWidget(self._files)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        self._layout.addWidget(splitter)

        self._buttonNewPatient = QPushButton('New patient')
        self._buttonNewPatient.setToolTip('Create a new patient in database.')
        self._buttonRemovePatient = QPushButton('Remove patient')
        self._buttonRemovePatient.setToolTip('Remove selected patient from database.')
        self._buttonAddVolume = QPushButton('Add volume')
        self._buttonAddVolume.setToolTip('Add a volume to selected patient.')
        self._buttonRemoveFile = QPushButton('Remove file')
        self._buttonRemoveFile.setToolTip('Remove selected volume from database.')
        # < Revision 28/05/2025
        # add open in file manager button
        if platform == 'win32':
            self._buttonFileManager = QPushButton('File Explorer')
            self._buttonFileManager.setToolTip('Open current patient folder in File Explorer.')
        elif platform == 'darwin':
            self._buttonFileManager = QPushButton('Finder')
            self._buttonFileManager.setToolTip('Open current patient folder in Finder.')
            self._buttonFileManager.setToolTip('Remove selected volume from database.')
        # Revision 28/05/2025 >
        self._buttonBackup = QPushButton('Database backup')
        self._buttonBackup.setToolTip('Backup database to a folder.')
        # noinspection PyUnresolvedReferences
        self._buttonNewPatient.clicked.connect(lambda dummy: self._newPatient())
        # noinspection PyUnresolvedReferences
        self._buttonRemovePatient.clicked.connect(self._removePatient)
        # noinspection PyUnresolvedReferences
        self._buttonAddVolume.clicked.connect(lambda dummy: self.addFiles())
        # noinspection PyUnresolvedReferences
        self._buttonRemoveFile.clicked.connect(self._removeFiles)
        # < Revision 28/05/2025
        # noinspection PyUnresolvedReferences
        self._buttonFileManager.clicked.connect(self._openFileManager)
        # Revision 28/05/20025 >
        # noinspection PyUnresolvedReferences
        self._buttonBackup.clicked.connect(self._backup)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addStretch()
        layout.addWidget(self._buttonNewPatient)
        layout.addWidget(self._buttonRemovePatient)
        layout.addWidget(self._buttonAddVolume)
        layout.addWidget(self._buttonRemoveFile)
        layout.addWidget(self._buttonFileManager)
        layout.addWidget(self._buttonBackup)
        self._layout.addLayout(layout)

        # Popup menu

        self._popuppatients = QMenu()
        # noinspection PyTypeChecker
        self._popuppatients.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popuppatients.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popuppatients.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action = dict()
        self._action['newpat'] = QAction('New patient...', self)
        self._action['delpat'] = QAction('Remove patient', self)
        self._popuppatients.addAction(self._action['newpat'])
        self._popuppatients.addAction(self._action['delpat'])
        # noinspection PyUnresolvedReferences
        self._action['newpat'].triggered.connect(lambda dummy: self._newPatient())
        # noinspection PyUnresolvedReferences
        self._action['delpat'].triggered.connect(self._removePatient)

        self._popupfiles = QMenu()
        # noinspection PyTypeChecker
        self._popupfiles.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupfiles.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupfiles.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['open'] = QAction('Open volume', self)
        self._action['edit'] = QAction('Edit volume attributes...', self)
        self._action['delvol'] = QAction('Remove volume(s)', self)
        self._popupfiles.addAction(self._action['open'])
        self._popupfiles.addAction(self._action['edit'])
        self._popupfiles.addAction(self._action['delvol'])
        # noinspection PyUnresolvedReferences
        self._action['open'].triggered.connect(self._open)
        # noinspection PyUnresolvedReferences
        self._action['edit'].triggered.connect(lambda dummy: self._edit())
        # noinspection PyUnresolvedReferences
        self._action['delvol'].triggered.connect(self._removeFiles)

        self._action['addvol'] = QAction('Add volume...', self)
        self._action['backup'] = QAction('Backup...', self)
        # noinspection PyUnresolvedReferences
        self._action['addvol'].triggered.connect(lambda dummy: self.addFiles())
        # noinspection PyUnresolvedReferences
        self._action['backup'].triggered.connect(self._backup)

        self._popup = QMenu()
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._popup.addAction(self._action['newpat'])
        self._popup.addAction(self._action['delpat'])
        self._popup.addSeparator()
        self._popup.addAction(self._action['addvol'])
        self._popup.addAction(self._action['delvol'])
        self._popup.addAction(self._action['open'])
        self._popup.addAction(self._action['edit'])
        self._popup.addSeparator()
        self._popup.addAction(self._action['backup'])

        self._update()
        self.setAcceptDrops(True)

    # Private methods

    def _getFolderFromItem(self, item):
        if isinstance(item, QTreeWidgetItem):
            patient = self._patients.selectedItems()[0]
            return '_'.join([patient.text(0), patient.text(1), patient.text(2)])
        else: raise TypeError('parameter type {} is not QTreeWidgetItem'.format(type(item)))

    def _getFilenameFromItem(self, item):
        if isinstance(item, QTreeWidgetItem):
            folder = self._getFolderFromItem(item)
            return join(self._db.getDatabasePath(), folder, item.text(0))
        else: raise TypeError('parameter type {} is not QTreeWidgetItem'.format(type(item)))

    def _sortIdentityByColumn(self, c):
        if isinstance(c, int):
            order = self._patients.header().sortIndicatorOrder()
            self._patients.sortItems(c, order)
        else: raise TypeError('parameter type {} is not int.'.format(type(c)))

    def _sortFilesByColumn(self, c):
        if isinstance(c, int):
            order = self._files.header().sortIndicatorOrder()
            self._files.sortItems(c, order)
        else: raise TypeError('parameter type {} is not int.'.format(type(c)))

    def _popupItemPatient(self, p):
        if isinstance(p, QPoint):
            item = self._patients.itemAt(p)
            if item:
                # < Revision 27/10/2024
                # use popup instead of exec
                # self._popuppatients.exec(self._patients.mapToGlobal(p))
                self._popuppatients.popup(self._patients.mapToGlobal(p))
                # Revision 27/10/2024 >
        else: raise TypeError('parameter type {} is not QPoint.'.format(type(p)))

    def _popupItemFile(self, p):
        if isinstance(p, QPoint):
            item = self._files.itemAt(p)
            if item:
                # < Revision 27/10/2024
                # use popup instead of exec
                # self._popupfiles.exec(self._files.mapToGlobal(p))
                self._popupfiles.popup(self._files.mapToGlobal(p))
                # Revision 27/10/2024 >
        else: raise TypeError('parameter type {} is not QPoint.'.format(type(p)))

    # noinspection PyUnusedLocal
    def _doubleClicked(self, item, c):
        filename = self._getFilenameFromItem(item)
        if exists(filename):
            if splitext(filename)[1] == SisypheVolume.getFileExt():
                self._mainwindow.open(filename)

    def _update(self):
        self._updateIdentityWidget()
        self._updateFileWidget()

    def _updateIdentityWidget(self):
        if not self._checklastname.isChecked(): last = ''
        else: last = self._fltlastname.text()
        if not self._checkfirstname.isChecked(): first = ''
        else: first = self._fltfirstname.text()
        if not self._checkdate.isChecked(): dob = ''
        else:
            # noinspection PyTypeChecker
            dob = self._fltdob.date().toString(Qt.ISODate)
        patients = self._db.searchPatients(last, first, dob)
        self._patients.clear()
        for patient in patients:
            last, first, dob = basename(patient).split('_')
            item = QTreeWidgetItem(self._patients)
            item.setText(0, last)
            item.setText(1, first)
            item.setText(2, dob)
            self._patients.addTopLevelItem(item)

    def _updateFileWidget(self):  # to do Mesh, Tools
        self._files.clear()
        items = self._patients.selectedItems()
        if items:
            item = items[0]
            last = item.text(0)
            first = item.text(1)
            dob = item.text(2)
            folder = '_'.join([last, first, dob])
            folder = join(self._db.getDatabasePath(), folder)
            if exists(folder):
                flt = join(folder, '*{}'.format(SisypheVolume.getFileExt()))
                filenames = glob(flt)
                if len(filenames) > 0:
                    ID = dict()
                    # Sisyphe volumes
                    for filename in filenames:
                        xml = XmlVolume(filename)
                        QApplication.processEvents()
                        item = QTreeWidgetItem(self._files)
                        item.setToolTip(0, str(xml)[:-1])
                        # filename
                        item.setText(0, basename(filename))
                        # ID
                        volID = xml.getID()
                        item.setText(1, volID)
                        font = self.font()
                        font.setPointSize(8)
                        item.setFont(1, font)
                        # size
                        raw = xml.getRawName()
                        # < Revision 25/04/2025
                        # rawname = join(dirname(filename), xml.getRawName())
                        if raw == 'self': rawname = filename
                        else: rawname = join(dirname(filename), xml.getRawName())
                        # Revision 25/04/2025 >
                        if exists(rawname): v = getsize(rawname)
                        else: v = 0
                        mb = 1024 * 1024
                        if v < 1024: v = '{} B'.format(v)
                        elif v < mb: v = '{:.2f} KB'.format(v / 1024)
                        else: v = '{:.2f} MB'.format(v / mb)
                        item.setText(2, v)
                        item.setTextAlignment(2, Qt.AlignCenter)
                        # last modified
                        v = strftime('%Y-%m-%d %H:%M:%S', strptime(ctime(getmtime(filename))))
                        item.setText(3, v)
                        item.setTextAlignment(3, Qt.AlignCenter)
                        # creation
                        v = strftime('%Y-%m-%d %H:%M:%S', strptime(ctime(getctime(filename))))
                        item.setText(4, v)
                        item.setTextAlignment(4, Qt.AlignCenter)
                        self._files.addTopLevelItem(item)
                        ID[volID] = self._files.indexFromItem(item)
                    # Sisyphe ROI
                    flt = join(folder, '*{}'.format(SisypheROI.getFileExt))
                    filenames = glob(flt)
                    if len(filenames) > 0:
                        for filename in filenames:
                            xml = XmlROI(filename)
                            QApplication.processEvents()
                            roiID = xml.getID()
                            if roiID in ID:
                                item = self._files.itemFromIndex(ID[roiID])
                                if item:
                                    child = QTreeWidgetItem(self._files)
                                    # filename
                                    child.setText(0, basename(filename))
                                    # ID
                                    child.setText(1, 'ROI')
                                    # size
                                    v = getsize(filename)
                                    mb = 1024 * 1024
                                    if v < 1024: v = '{} B\n'.format(v)
                                    elif v < mb: v = '{:.2f} KB\n'.format(v / 1024)
                                    else: v = '{:.2f} MB\n'.format(v / mb)
                                    child.setText(2, v)
                                    # last modified
                                    v = strftime('%Y-%m-%d %H:%M:%S', strptime(ctime(getmtime(filename))))
                                    child.setText(3, v)
                                    # creation
                                    v = strftime('%Y-%m-%d %H:%M:%S', strptime(ctime(getctime(filename))))
                                    child.setText(4, v)
                                    item.addChild(child)
                    # Sisyphe Mesh
                    # Sisyphe Tools
                    # Sisyphe Streamlines

    def _open(self):
        filenames = list()
        items = self._files.selectedItems()
        if items:
            for item in items:
                filename = self._getFilenameFromItem(item)
                if exists(filename):
                    if splitext(filename)[1] == SisypheVolume.getFileExt():
                        filenames.append(filename)
            if len(filenames) > 0: self._mainwindow.open(filenames)
            else: messageBox(self, 'Database', 'No volume selected.')

    def _edit(self, item=None):
        if item is None:
            item = self._files.selectedItems()
            if len(item) > 0: item = item[0]
            else:
                messageBox(self, 'Database', 'No volume selected.')
                return
        if isinstance(item, QTreeWidgetItem):
            filename = self._getFilenameFromItem(item)
            if exists(filename):
                if splitext(filename)[1] == SisypheVolume.getFileExt():
                    vol = SisypheVolume()
                    try: vol.load(filename)
                    except:
                        messageBox(self, 'Database', text='{} read error.'.format(basename(filename)))
                        return
                    dialog = DialogVolumeAttributes(vol=vol)
                    if platform == 'win32':
                        import pywinstyles
                        cl = self.palette().base().color()
                        c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                        pywinstyles.change_header_color(dialog, c)
                    dialog.exec()
        else: raise TypeError('parameter type {} is not QTreeWidgetItem.'.format(type(item)))

    def _removeFiles(self):
        items = self._files.selectedItems()
        if items:
            if messageBox(self,
                          'Database',
                          'Do you want to remove selected files ?',
                          icon=QMessageBox.Question,
                          buttons=QMessageBox.Yes | QMessageBox.No,
                          default=QMessageBox.No) == QMessageBox.Yes:
                identity = self.getIdentityFromItem(self._patients.selectedItems()[0])
                filenames = list()
                for item in items:
                    filenames.append(self._getFilenameFromItem(item))
                n = len(filenames)
                if n > 0:
                    progress = DialogWait('Database', 'Remove volume(s) from database...', progress=True,
                                          progressmin=0, progressmax=n, progresstxt=True)
                    try:
                        progress.setProgressVisibility(n > 1)
                        progress.open()
                        for filename in filenames:
                            progress.incCurrentProgressValue()
                            progress.setInformationText('Remove {} from database...'.format(basename(filename)))
                            try: self._db.deleteFileFromPatient(filename, identity)
                            except:
                                messageBox(self,
                                           'Database',
                                           text='Remove {} from database error.'.format(basename(filename)))
                                continue
                    finally:
                        progress.close()
                        self._updateFileWidget()
                else:
                    messageBox(self, 'Database', 'No volume selected.')

    def _newPatient(self, identity=None):
        if identity is not None:
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                try: self._db.createPatient(identity)
                except: messageBox(self,
                                   'Database',
                                   text='Create patient {} {} error.'.format(identity.getLastname(),
                                                                             identity.getFirstname()))
        else:
            dialog = DialogPatient()
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(dialog, c)
            if dialog.exec():
                identity = dialog.getIdentity()
                if messageBox(self,
                              'Database',
                              text='Do you want to create patient {} {} ?'.format(identity.getLastname(),
                                                                                  identity.getFirstname()),
                              icon=QMessageBox.Question,
                              buttons=QMessageBox.Yes | QMessageBox.No,
                              default=QMessageBox.No) == QMessageBox.Yes:
                    try: self._db.createPatient(identity)
                    except: messageBox(self,
                                       'Database',
                                       text='Create patient {} {} error.'.format(identity.getLastname(),
                                                                                 identity.getFirstname()))
        self._update()

    def _removePatient(self):
        items = self._patients.selectedItems()
        if items:
            identity = self.getIdentityFromItem(items[0])
            if messageBox(self,
                          'Database',
                          text='Do you want to remove {} {} from database ?'
                               '\nAll files will be deleted.'.format(identity.getLastname(),
                                                                     identity.getFirstname()),
                          icon=QMessageBox.Question,
                          buttons=QMessageBox.Yes | QMessageBox.No,
                          default=QMessageBox.No) == QMessageBox.Yes:
                try: self._db.removePatient(identity)
                except: messageBox(self,
                                   'Database',
                                   text='Remove patient {} {} error.'.format(identity.getLastname(),
                                                                             identity.getFirstname()))
                self._update()
        else: messageBox(self, 'Database', 'No patient selected.')

    # < Revision 28/05/2025
    # add _openFileManager method
    def _openFileManager(self):
        selected = self._patients.selectedItems()
        if len(selected) > 0:
            folder = join(self._db.getDatabasePath(), self._getFolderFromItem(selected[0]))
            # if platform == 'win32': subprocess.Popen('explorer /select,"{}"'.format(folder))
            if platform == 'win32': subprocess.Popen('explorer "{}"'.format(folder))
            elif platform == 'darwin':
                folder = '~' + folder
                subprocess.call(["open", folder])
        else:
            messageBox(self,
                       'Database',
                       'No patient selected.')
    # Revision 28/05/2025 >

    def _backup(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                  getcwd(), QFileDialog.ShowDirsOnly)
        if folder:
            chdir(folder)
            progress = DialogWait()
            try: self._db.backupDatabase(folder, progress)
            finally: progress.close()

    # Public

    def getPopup(self):
        return self._popup

    def addFiles(self, filenames=None):
        if filenames is None:
            filt = 'SisypheVolume (*.xvol)'
            filenames = QFileDialog.getOpenFileNames(self, 'Select PySisyphe volume', getcwd(), filt)
            QApplication.processEvents()
            filenames = filenames[0]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            vol = SisypheVolume()
            progress = DialogWait('Database', 'Add volume(s) to database...',
                                  progress=True, progressmin=0, progressmax=n)
            try:
                if n > 1: progress.open()
                for filename in filenames:
                    progress.incCurrentProgressValue()
                    progress.setInformationText('Add {} to database...'.format(basename(filename)))
                    try: vol.load(filename)
                    except:
                        messageBox(self, 'Database', text='{} read error.'.format(basename(filename)))
                        continue
                    try: self._db.copySisypheVolume(vol)
                    except:
                        messageBox(self, 'Database', text='Add {} to database error.'.format(basename(filename)))
                        continue
            finally:
                progress.close()
                self._update()

    def addVolumes(self, vols):
        if isinstance(vols, SisypheVolume): vols = [vols]
        if isinstance(vols, list):
            n = len(vols)
            if n > 0:
                progress = DialogWait('Database', 'Add volume(s) to database...',
                                      progress=True, progressmin=0, progressmax=n)
                try:
                    if n > 1: progress.open()
                    for vol in vols:
                        progress.incCurrentProgressValue()
                        progress.setInformationText('Add {} to database...'.format(vol.getBasename()))
                        if isinstance(vol, SisypheVolume):
                            try: self._db.copySisypheVolume(vol)
                            except:
                                messageBox(self,
                                           'Database',
                                           text='Add {} to database error.'.format(vol.getBasename()))
                                continue
                        else:
                            messageBox(self,
                                       'Database',
                                       '{} is not a PySisyphe volume.'.format(vol.getBasename()))
                finally:
                    progress.close()
                    self._update()

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): self._mainwindow = w
        else: raise TypeError('parameter type {} is not WindowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None

    # QEvents

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            files = event.mimeData().text().split('\n')
            filenames = list()
            for file in files:
                if file != '':
                    filename = file.replace('file://', '')
                    if splitext(filename)[1] == SisypheVolume.getFileExt():
                        filenames.append(filename)
            if len(filenames) > 0:
                self._addVolumes(filenames)
        else: event.ignore()
