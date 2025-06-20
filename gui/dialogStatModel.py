"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import join
from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import dirname
from os.path import abspath
from os.path import expanduser

from numpy import ndarray
from numpy import arange
from numpy import load
from numpy import loadtxt
from numpy import genfromtxt

from pandas import DataFrame
from pandas import read_excel

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.functionsSettingsWidget import DialogSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['DialogModel',
           'DialogObs',
           'DialogfMRIObs']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogModel
              -> DialogObs
              -> DialogfMRIObs
"""

class DialogModel(QDialog):
    """
    DialogModel class

    Description
    ~~~~~~~~~~~

    GUI dialog for voxel by voxel statistical model definition and estimation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogModel

    Creation: 29/11/2022
    Last revision: 29/11/2024
    """

    # Special method

    """
    Private attributes

    _size       tuple[int, int, int]
    _spacing    tuple[float, float, float]
    _fmri       bool
    _design     SisypheDesign
    _obscnd
    _obsgrp
    _treeobs    QTreeWidget
    _obsitem    QTreeWidgetItem
    _bcaritem   QTreeWidgetItem
    _glbcovitem QTreeWidgetItem
    _grpcovitem QTreeWidgetItem
    _sbjcovitem QTreeWidgetItem
    _cndcovitem QTreeWidgetItem
    """

    def __init__(self, title, treeobs, fmri, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle(title)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._size = None
        self._spacing = None
        if isinstance(treeobs, SisypheDesign):
            self._design = treeobs
            self._fmri = self._design.isfMRIDesign()
        else:
            self._design = SisypheDesign()
            self._fmri = fmri
            if fmri: self._design.setfMRIDesign()
            self._design.setDictDesign(treeobs)
        ngrp = self._design.getGroupCount()
        nsbj = self._design.getSubjectCount()
        ncnd = self._design.getConditionCount()

        # Init widgets

        self._treeobs = QTreeWidget(parent=self)
        self._treeobs.setMinimumHeight(self.screen().availableGeometry().height() // 2)
        self._treeobs.setColumnCount(2)
        header = QTreeWidgetItem()
        header.setText(0, 'Observation(s)/Covariable(s)')
        header.setText(1, 'Image count / filenames')
        self._treeobs.header().resizeSection(0, 300)
        self._treeobs.setHeaderItem(header)
        self._treeobs.setEditTriggers(QTreeWidget.DoubleClicked)
        # noinspection PyUnresolvedReferences
        self._treeobs.itemChanged.connect(self._itemRenamed)
        # noinspection PyUnresolvedReferences
        self._treeobs.itemDoubleClicked.connect(self._itemDoubleClicked)
        # Observations
        self._obsitem = QTreeWidgetItem(['Observations', ''])
        self._obsitem.setExpanded(True)
        obs = self._design.getObservationsDict()
        fobs = self._design.getFileObsDict()
        for k in obs:
            name = ' '.join(k)
            item = QTreeWidgetItem([name, '0 / {}'.format(obs[k][0])])
            # < Revision 05/06/2025
            # copy key to QTreeWidgetItem data
            item.setData(0, Qt.UserRole, k)
            # Revision 05/06/2025 >
            item.setToolTip(0, 'Double-click to add image(s)')
            # < Revision 03/12/2024
            # add observations
            n = len(fobs[k])
            if n > 0:
                c = 0
                for i in range(n):
                    filename = fobs[k][i]
                    if exists(filename):
                        child = QTreeWidgetItem(['', basename(filename)])
                        child.setData(1, Qt.UserRole, filename)
                        item.addChild(child)
                        c += 1
                item.setExpanded(True)
                item.setText(1, '{} / {}'.format(c, n))
            # Revision 03/12/2024 >
            self._obsitem.addChild(item)
        # Covariables
        self._glbcovitem = QTreeWidgetItem(['Global Covariable(s)', ''])
        self._grpcovitem = QTreeWidgetItem(['Covariable(s) by group', ''])
        self._sbjcovitem = QTreeWidgetItem(['Covariable(s) by subject', ''])
        self._cndcovitem = QTreeWidgetItem(['Covariable(s) by condition', ''])
        self._glbcovitem.setToolTip(0, 'Double-click to add global covariable(s)')
        self._grpcovitem.setToolTip(0, 'Double-click to add covariable(s) by group')
        self._sbjcovitem.setToolTip(0, 'Double-click to add covariable(s) by subject')
        self._cndcovitem.setToolTip(0, 'Double-click to add covariable(s) by condition')
        self._treeobs.addTopLevelItem(self._obsitem)
        self._treeobs.addTopLevelItem(self._glbcovitem)
        if ngrp > 0: self._treeobs.addTopLevelItem(self._grpcovitem)
        if nsbj > 0: self._treeobs.addTopLevelItem(self._sbjcovitem)
        if ncnd > 0: self._treeobs.addTopLevelItem(self._cndcovitem)
        self._treeobs.expandAll()

        self._addObs = QPushButton('Add observation(s)', parent=self)
        self._addObs.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._addObs.clicked.connect(self.addObservations)
        self._covGlobal = QPushButton('Add global cov.', parent=self)
        self._covGlobal.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._covGlobal.clicked.connect(self.addGlobalCovariable)
        self._covByGroup = QPushButton('Add cov. by group', parent=self)
        self._covByGroup.setCheckable(False)
        self._covByGroup.setVisible(ngrp > 0)
        # noinspection PyUnresolvedReferences
        self._covByGroup.clicked.connect(self.addCovariableByGroup)
        self._covBySubject = QPushButton('Add cov. by subject', parent=self)
        self._covBySubject.setCheckable(False)
        self._covBySubject.setVisible(nsbj > 0)
        # noinspection PyUnresolvedReferences
        self._covBySubject.clicked.connect(self.addCovariableBySubject)
        self._covByCondition = QPushButton('Add cov. by condition', parent=self)
        self._covByCondition.setCheckable(False)
        self._covByCondition.setVisible(ncnd > 0)
        # noinspection PyUnresolvedReferences
        self._covByCondition.clicked.connect(self.addCovariableByCondition)
        self._remove = QPushButton('Remove', parent=self)
        self._remove.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self.remove)
        self._clear = QPushButton('Remove all', parent=self)
        self._clear.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._clear.pressed.connect(self.clear)
        self._view = QPushButton('View design', parent=self)
        self._view.setCheckable(False)
        self._view.setToolTip('Display design matrix.')
        # noinspection PyUnresolvedReferences
        self._view.clicked.connect(self._viewDesign)
        self._save = QPushButton('Save', parent=self)
        self._save.setCheckable(False)
        self._save.setToolTip('Save statistical model.')
        # < Revision 05/06/2025
        # self._save.clicked.connect(self.saveModel)
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(lambda _: self.saveModel())
        # Revision 05/06/2025
        lyout1 = QHBoxLayout(self)
        lyout1.setSpacing(10)
        lyout1.addWidget(self._addObs)
        lyout1.addWidget(self._covGlobal)
        lyout1.addWidget(self._covByGroup)
        lyout1.addWidget(self._covBySubject)
        lyout1.addWidget(self._covByCondition)
        lyout1.addWidget(self._remove)
        lyout1.addWidget(self._clear)
        lyout1.addWidget(self._view)
        lyout1.addWidget(self._save)

        self._params = DialogSettingsWidget('StatisticalModel', parent=self)
        self._params.hideButtons()
        self._params.hideIOButtons()
        self._params.settingsVisibilityOn()
        self._cnorm = self._params.getParameterWidget('Norm')
        self._normroi = self._params.getParameterWidget('Roi1')
        self._cancova = self._params.getParameterWidget('Ancova')
        self._cmask = self._params.getParameterWidget('Mask')
        self._maskroi = self._params.getParameterWidget('Roi2')
        self._age = self._params.getParameterWidget('Age')

        self._params.setParameterVisibility('Roi1', False)
        self._params.setParameterVisibility('Roi2', False)
        self._params.setParameterVisibility('Ancova', False)

        self._cnorm.clear()
        self._cnorm.addItem('no')
        self._cnorm.addItem('mean scaling')
        self._cnorm.addItem('median scaling')
        self._cnorm.addItem('75th perc. scaling')
        self._cnorm.addItem('ROI mean scaling')
        self._cnorm.addItem('ROI median scaling')
        self._cnorm.addItem('ROI 75th perc. scaling')
        self._cnorm.addItem('ANCOVA mean')
        self._cnorm.addItem('ANCOVA median')
        self._cnorm.addItem('ANCOVA 75th perc.')
        self._cnorm.addItem('ANCOVA ROI mean')
        self._cnorm.addItem('ANCOVA ROI median')
        self._cnorm.addItem('ANCOVA ROI 75th perc.')
        self._cnorm.setCurrentIndex(self._design.getSignalNormalization())

        self._cancova.clear()
        self._cancova.addItem('global')
        if ngrp > 0: self._cancova.addItem('by group')
        if nsbj > 0: self._cancova.addItem('by subject')
        if ncnd > 0: self._cancova.addItem('by condition')
        self._cancova.setCurrentText(self._design.getSignalCovariableAsString())

        self._age.clear()
        self._age.addItem('no')
        self._age.addItem('global')
        if ngrp > 0: self._age.addItem('by group')
        if nsbj > 0: self._age.addItem('by subject')
        if ncnd > 0: self._age.addItem('by condition')
        self._age.setCurrentText(self._design.getAgeCovariableAsString())

        # noinspection PyUnresolvedReferences
        self._cmask.currentIndexChanged.connect(self._combBoxMaskItemChanged)
        # noinspection PyUnresolvedReferences
        self._cnorm.currentIndexChanged.connect(self._comboBoxNormItemChanged)
        # noinspection PyUnresolvedReferences
        self._cancova.currentIndexChanged.connect(lambda: self._comboBoxAncovaItemChanged())

        self._layout.addWidget(self._treeobs)
        self._layout.addLayout(lyout1)
        self._layout.addWidget(self._params)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setCheckable(False)
        cancel.setFixedWidth(100)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        self._ok = QPushButton('Estimate', parent=self)
        self._ok.setCheckable(False)
        self._ok.setEnabled(False)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.estimate)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        self._layout.addLayout(layout)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._treeobs.setMinimumWidth(int(screen.width() * 0.40))
        # dialog resize off
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private

    def _combBoxMaskItemChanged(self, index):
        c = index > 0
        self._params.setParameterVisibility('Roi2', c)
        if not c: self._maskroi.clear()

    def _comboBoxNormItemChanged(self, index):
        c = index in (4, 5, 6, 10, 11, 12)
        self._params.setParameterVisibility('Roi1', c)
        if not c: self._normroi.clear()
        self._params.setParameterVisibility('Ancova', index > 6)

    def _comboBoxAncovaItemChanged(self):
        if self._cancova.currentText() == 'by group': self._design.setSignalCovariableByGroup()
        elif self._cancova.currentText() == 'by subject': self._design.setSignalCovariableBySubject()
        elif self._cancova.currentText() == 'by condition': self._design.setSignalCovariableByCondition()
        else: self._design.setSignalGlobalCovariable()

    def _newName(self, name, cov: int = 0) -> str | None:
        if cov == 1:
            # covariable by group
            for i in range(self._grpcovitem.childCount()):
                if name == self._grpcovitem.child(i).text(0):
                    buff = name.split('#')
                    if len(buff) > 1:
                        # noinspection PyUnresolvedReferences
                        name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                    else: name = '{}#1'.format(buff[0])
                    name = self._newName(name, cov)
        elif cov == 2:
            # covariable by subject
            for i in range(self._sbjcovitem.childCount()):
                if name == self._sbjcovitem.child(i).text(0):
                    buff = name.split('#')
                    if len(buff) > 1:
                        # noinspection PyUnresolvedReferences
                        name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                    else: name = '{}#1'.format(buff[0])
                    name = self._newName(name, cov)
        elif cov == 3:
            # covariable by condition
            for i in range(self._cndcovitem.childCount()):
                if name == self._cndcovitem.child(i).text(0):
                    buff = name.split('#')
                    if len(buff) > 1:
                        # noinspection PyUnresolvedReferences
                        name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                    else: name = '{}#1'.format(buff[0])
                    name = self._newName(name, cov)
        else:
            # global covariable
            for i in range(self._glbcovitem.childCount()):
                if name == self._glbcovitem.child(i).text(0):
                    buff = name.split('#')
                    if len(buff) > 1: name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                    else: name = '{}#1'.format(buff[0])
                    name = self._newName(name, cov)
        return name

    # noinspection PyUnusedLocal
    def _itemDoubleClicked(self, item, column):
        parent = item.parent()
        if parent is not None:
            if parent.text(0) == 'Observations':
                self._treeobs.clearSelection()
                item.setSelected(True)
                self.addObservations()
            if parent.text(0) == 'Global Covariable(s)': self._treeobs.editItem(item, 0)
            elif parent.text(0) == 'Covariable(s) by group': self._treeobs.editItem(item, 0)
            elif parent.text(0) == 'Covariable(s) by subject': self._treeobs.editItem(item, 0)
            elif parent.text(0) == 'Covariable(s) by condition': self._treeobs.editItem(item, 0)
        else:
            if item.text(0) == 'Global Covariable(s)': self.addGlobalCovariable()
            elif item.text(0) == 'Covariable(s) by group': self.addCovariableByGroup()
            elif item.text(0) == 'Covariable(s) by subject': self.addCovariableBySubject()
            elif item.text(0) == 'Covariable(s) by condition': self.addCovariableByCondition()

    def _itemRenamed(self, item, column):
        if column == 0:
            parent = item.parent()
            if parent.text(0) == 'Global Covariable(s)':
                for i in range(self._glbcovitem.childCount()):
                    if item != parent.child(i):
                        if item.text(0) == parent.child(i).text(0):
                            buff = item.text(0).split('#')
                            if len(buff) > 1: name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                            else: name = '{}#1'.format(buff[0])
                            item.setText(0, name)
                            self._itemRenamed(item, column)
            elif parent.text(0) == 'Covariable(s) by group':
                for i in range(self._grpcovitem.childCount()):
                    if item != parent.child(i):
                        if item.text(0) == parent.child(i).text(0):
                            buff = item.text(0).split('#')
                            if len(buff) > 1: name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                            else: name = '{}#1'.format(buff[0])
                            item.setText(0, name)
                            self._itemRenamed(item, column)
            elif parent.text(0) == 'Covariable(s) by subject':
                for i in range(self._sbjcovitem.childCount()):
                    if item != parent.child(i):
                        if item.text(0) == parent.child(i).text(0):
                            buff = item.text(0).split('#')
                            if len(buff) > 1: name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                            else: name = '{}#1'.format(buff[0])
                            item.setText(0, name)
                            self._itemRenamed(item, column)
            elif parent.text(0) == 'Covariable(s) by condition':
                for i in range(self._cndcovitem.childCount()):
                    if item != parent.child(i):
                        if item.text(0) == parent.child(i).text(0):
                            buff = item.text(0).split('#')
                            if len(buff) > 1: name = '{}#{}'.format('#'.join(buff[:-1]), int(buff[-1]) + 1)
                            else: name = '{}#1'.format(buff[0])
                            item.setText(0, name)
                            self._itemRenamed(item, column)

    def _makeDesign(self):
        self._design.getDesignMatrix(recalc=True)
        # Add covariable(s) by condition
        if self._cndcovitem.childCount() > 0:
            for i in range(self._cndcovitem.childCount()):
                child = self._cndcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableByCondition(name, v, estimable=True)
        # Add covariable(s) by subject
        if self._sbjcovitem.childCount() > 0:
            for i in range(self._sbjcovitem.childCount()):
                child = self._sbjcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableBySubject(name, v, estimable=True)
        # Add covariable(s) by group
        if self._grpcovitem.childCount() > 0:
            for i in range(self._grpcovitem.childCount()):
                child = self._grpcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableByGroup(name, v, estimable=True)
        # Add global covariable(s)
        if self._glbcovitem.childCount() > 0:
            for i in range(self._glbcovitem.childCount()):
                child = self._glbcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addGlobalCovariable(name, v, estimable=True)

    def _viewDesign(self):
        self._makeDesign()
        dialog = DialogGenericResults()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(dialog, c)
        dialog.setWindowTitle('Design matrix')
        dialog.newTab(title='Design matrix')
        dialog.hideTree(0)
        fig = dialog.getFigure(0)
        fig.set_layout_engine('constrained')
        fig.clear()
        ax = fig.add_subplot(111)
        ax.pcolormesh(self._design.getDesignMatrix())
        # x labels, effects name
        xlbl = list()
        cdesign = self._design.getEffectInformations()
        for i in range(len(cdesign)):
            buff = cdesign[i][0].split()
            if len(buff) > 1: buff = '\n'.join(buff)
            else: buff = buff[0]
            xlbl.append(buff)
        # y labels, observations name (filenames)
        ylbl = list()
        root = self._treeobs.topLevelItem(0)
        # noinspection PyUnresolvedReferences
        if root.text(0) == 'Observations':
            for i in range(root.childCount()):
                item = root.child(i)
                n = int(item.childCount())
                if n > 0:
                    for j in range(n):
                        ylbl.append(item.child(j).text(1))
                else:
                    # noinspection PyUnresolvedReferences
                    n = int(item.text(1).split()[-1])
                    ylbl += [''] * n
        ax.set_xticks(arange(len(xlbl)) + 0.5, labels=xlbl, rotation=45)
        ax.set_yticks(arange(len(ylbl)) + 0.5, labels=ylbl)
        ax.invert_yaxis()
        dialog.exec()

    def _isFull(self):
        root = self._treeobs.topLevelItem(0)
        # noinspection PyInconsistentReturns
        if root.text(0) == 'Observations':
            # < Revision 29/11/2024
            # add return value
            for i in range(root.childCount()):
                item = root.child(i)
                n1 = int(item.text(1).split()[-1])
                n2 = int(item.childCount())
                if n1 != n2:
                    self._ok.setEnabled(False)
                    return False
            self._ok.setEnabled(True)
            return True
        # Revision 29/11/2024 >

    def _isEmpty(self):
        n = 0
        root = self._treeobs.topLevelItem(0)
        if root.text(0) == 'Observations':
            for i in range(root.childCount()):
                item = root.child(i)
                n += int(item.childCount())
        return n == 0

    # Public methods

    def addObservations(self):
        items = self._treeobs.selectedItems()
        if len(items) > 0:
            for item in items:
                parent = item.parent()
                if parent is not None:
                    if parent.text(0) == 'Observations':
                        n = int(item.text(1).split()[-1])
                        filenames = QFileDialog.getOpenFileNames(self, 'Add observations...', getcwd(),
                                                                 filter=SisypheVolume.getFilterExt())[0]
                        QApplication.processEvents()
                        if len(filenames) > 0:
                            chdir(dirname(filenames[0]))
                            if len(filenames) == n:
                                item.takeChildren()
                                for i in range(n):
                                    filenames[i] = abspath(filenames[i])
                                    v = SisypheVolume()
                                    v.load(filenames[i])
                                    if i == 0:
                                        self._size = v.getSize()
                                        self._spacing = v.getSpacing()
                                        self._normroi.filterSameFOV(v)
                                        self._maskroi.filterSameFOV(v)
                                    else:
                                        if v.getSize() != self._size or v.getSpacing() != self._spacing:
                                            messageBox(self,
                                                       'Add observations',
                                                       text='{} FOV mismatch.'.format(v.getBasename()))
                                            item.takeChildren()
                                            break
                                    child = QTreeWidgetItem(['', basename(filenames[i])])
                                    child.setData(1, Qt.UserRole, filenames[i])
                                    child.setToolTip(1, str(v))
                                    item.addChild(child)
                                item.setExpanded(True)
                                item.setText(1, '{} / {}'.format(n, n))
                                self._isFull()
                            else:
                                if n == 1: buff = 'is'
                                else: buff = 'are'
                                messageBox(self,
                                           'Add observations',
                                           text='You have selected {} PySisyphe volume(s) '
                                                'but {} {} required.'.format(len(filenames), buff, n))

    def remove(self):
        items = self._treeobs.selectedItems()
        if len(items) > 0:
            pp = None
            for item in items:
                p = item.parent()
                if p is not None:
                    if p.text(0) == 'Global Covariable(s)': p.removeChild(item)
                    elif p.text(0) == 'Covariable(s) by group': p.removeChild(item)
                    elif p.text(0) == 'Covariable(s) by subject': p.removeChild(item)
                    elif p.text(0) == 'Covariable(s) by condition': p.removeChild(item)
                    elif p.text(0) == 'Observations': item.takeChildren()
                    elif item.text(0) == '' and p != pp:
                        item.takeChildren()
                        pp = p
        if self._isEmpty():
            self._size = None
            self._spacing = None
            self._normroi.clear()
            self._normroi.setEnabled(False)
            self._maskroi.clear()
            self._maskroi.setEnabled(False)

    def clear(self):
        root = self._treeobs.topLevelItem(0)
        if root.text(0) == 'Observations':
            for i in range(root.childCount()):
                item = root.child(i)
                item.takeChildren()
                buff = item.text(1).split()
                buff[0] = '0'
                item.setText(1, ' '.join(buff))
        self._glbcovitem.takeChildren()
        self._grpcovitem.takeChildren()
        self._sbjcovitem.takeChildren()
        self._cndcovitem.takeChildren()
        self._size = None
        self._spacing = None
        self._normroi.clear()
        self._normroi.setEnabled(False)
        self._maskroi.clear()
        self._maskroi.setEnabled(False)

    def addGlobalCovariable(self):
        title = 'Add global covariable(s)'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            n = self._design.getTotalObsCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try:
                    # noinspection PyUnusedLocal
                    cov = loadtxt(filename, delimiter=',')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try:
                    # noinspection PyUnusedLocal
                    cov = genfromtxt(filename, delimiter=';')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try:
                    # noinspection PyUnusedLocal
                    cov = load(filename)
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try:
                    cov = read_excel(filename, engine='openpyxl')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            name = self._newName(name, 0)
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 1:
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, cov)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(cov))
                        self._glbcovitem.addChild(covitem)
                        self._glbcovitem.setExpanded(True)
                    elif cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        messageBox(self,
                                                   title=title,
                                                   text='{} array elements but {} are required.'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                    covitem.setToolTip(0, str(v))
                                    self._glbcovitem.addChild(covitem)
                                    self._glbcovitem.setExpanded(True)
                # Pandas
                elif isinstance(cov, DataFrame):
                    n = len(cov.columns)
                    if n == 1:
                        v = cov[0].to_numpy()
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, v)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(v))
                        self._glbcovitem.addChild(covitem)
                        self._glbcovitem.setExpanded(True)
                    elif n > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    messageBox(self,
                                               title=title,
                                               text='{} array elements but {} are required.'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem(['{}#{}'.format(name, col), ''])
                                covitem.setData(0, Qt.UserRole, v)
                                covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                covitem.setToolTip(0, str(v))
                                self._glbcovitem.addChild(covitem)
                                self._glbcovitem.setExpanded(True)

    def addCovariableByGroup(self):
        title = 'Add covariable(s) by group'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            n = self._design.getTotalObsCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try:
                    # noinspection PyUnusedLocal
                    cov = loadtxt(filename, delimiter=',')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try:
                    # noinspection PyUnusedLocal
                    cov = genfromtxt(filename, delimiter=';')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try:
                    # noinspection PyUnusedLocal
                    cov = load(filename)
                except:
                    messageBox(self, title=title,text= '{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try: cov = read_excel(filename, engine='openpyxl')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            name = self._newName(name, 1)
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 1:
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, cov)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(cov))
                        self._grpcovitem.addChild(covitem)
                        self._grpcovitem.setExpanded(True)
                    elif cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        messageBox(self,
                                                   title=title,
                                                   text='{} array elements but {} are required.'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                    covitem.setToolTip(0, str(v))
                                    self._grpcovitem.addChild(covitem)
                                    self._grpcovitem.setExpanded(True)
                # Pandas
                elif isinstance(cov, DataFrame):
                    n = len(cov.columns)
                    if n == 1:
                        v = cov[0].to_numpy()
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, v)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(v))
                        self._grpcovitem.addChild(covitem)
                        self._grpcovitem.setExpanded(True)
                    elif n > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    messageBox(self,
                                               title=title,
                                               text='{} array elements but {} are required.'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem(['{}#{}'.format(name, col), ''])
                                covitem.setData(0, Qt.UserRole, v)
                                covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                covitem.setToolTip(0, str(v))
                                self._grpcovitem.addChild(covitem)
                                self._grpcovitem.setExpanded(True)

    def addCovariableBySubject(self):
        title = 'Add covariable(s) by subject'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            n = self._design.getTotalObsCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try:
                    # noinspection PyUnusedLocal
                    cov = loadtxt(filename, delimiter=',')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try:
                    # noinspection PyUnusedLocal
                    cov = genfromtxt(filename, delimiter=';')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try:
                    # noinspection PyUnusedLocal
                    cov = load(filename)
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try:
                    cov = read_excel(filename, engine='openpyxl')
                except:
                    messageBox(self, title=title, text='{} loading error.'.format(basename(filename)))
                    cov = None
            name = self._newName(name, 2)
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 1:
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, cov)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(cov))
                        self._sbjcovitem.addChild(covitem)
                        self._sbjcovitem.setExpanded(True)
                    elif cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        messageBox(self,
                                                   title=title,
                                                   text='{} array elements but {} are required.'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                    covitem.setToolTip(0, str(v))
                                    self._sbjcovitem.addChild(covitem)
                                    self._sbjcovitem.setExpanded(True)
                # Pandas
                elif isinstance(cov, DataFrame):
                    n = len(cov.columns)
                    if n == 1:
                        v = cov[0].to_numpy()
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, v)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(v))
                        self._sbjcovitem.addChild(covitem)
                        self._sbjcovitem.setExpanded(True)
                    if n > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    messageBox(self,
                                               title=title,
                                               text='{} array elements but {} are required.'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem(['{}#{}'.format(name, col), ''])
                                covitem.setData(0, Qt.UserRole, v)
                                covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                covitem.setToolTip(0, str(v))
                                self._sbjcovitem.addChild(covitem)
                                self._sbjcovitem.setExpanded(True)

    def addCovariableByCondition(self):
        title = 'Add covariable(s) by condition'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            n = self._design.getTotalObsCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try:
                    # noinspection PyUnusedLocal
                    cov = loadtxt(filename, delimiter=',')
                except:
                    messageBox(self,
                               title=title,
                               text='{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try:
                    # noinspection PyUnusedLocal
                    cov = genfromtxt(filename, delimiter=';')
                except:
                    messageBox(self,
                               title=title,
                               text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try:
                    # noinspection PyUnusedLocal
                    cov = load(filename)
                except:
                    messageBox(self,
                               title=title,
                               text='{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try:
                    cov = read_excel(filename, engine='openpyxl')
                except:
                    messageBox(self,
                               title=title,
                               text='{} loading error.'.format(basename(filename)))
                    cov = None
            name = self._newName(name, 3)
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 1:
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, cov)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(cov))
                        self._cndcovitem.addChild(covitem)
                        self._cndcovitem.setExpanded(True)
                    elif cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        messageBox(self,
                                                   title=title,
                                                   text='{} array elements but {} are required.'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                    covitem.setToolTip(0, str(v))
                                    self._cndcovitem.addChild(covitem)
                                    self._cndcovitem.setExpanded(True)
                # Pandas
                elif isinstance(cov, DataFrame):
                    n = len(cov.columns)
                    if n == 1:
                        v = cov[0].to_numpy()
                        covitem = QTreeWidgetItem([name, ''])
                        covitem.setData(0, Qt.UserRole, v)
                        covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                        covitem.setToolTip(0, str(v))
                        self._cndcovitem.addChild(covitem)
                        self._cndcovitem.setExpanded(True)
                    if n > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column do you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    messageBox(self,
                                               title=title,
                                               text='{} array elements but {} are required.'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem(['{}#{}'.format(name, col), ''])
                                covitem.setData(0, Qt.UserRole, v)
                                covitem.setFlags(covitem.flags() | Qt.ItemIsEditable)
                                covitem.setToolTip(0, str(v))
                                self._cndcovitem.addChild(covitem)
                                self._cndcovitem.setExpanded(True)

    def estimate(self):
        if self._isFull():
            # add observations
            for i in range(self._obsitem.childCount()):
                item = self._obsitem.child(i)
                n = item.childCount()
                if n > 0:
                    filenames = list()
                    # < Revision 05/06/2025
                    # get key from QTreeWidgetItem data, not from text
                    # key = item.text(0).split(' ')
                    key = item.data(0, Qt.UserRole)
                    # Revision 05/06/2025 >
                    for j in range(n):
                        filenames.append(item.child(j).data(1, Qt.UserRole))
                    self._design.setFileObsTo(filenames, key[0], key[1], key[2])
            # design matrix processing
            self._makeDesign()
            # mask processing
            wait = DialogWait()
            wait.open()
            mask = None
            if not self._maskroi.isEmpty():
                filename = self._maskroi.getFilename()
                if exists(filename):
                    wait.setInformationText('Open mask of analysis\n{}...'.format(basename(filename)))
                    mask = SisypheROI()
                    mask.load(filename)
            roi = None
            # open ROI
            if not self._normroi.isEmpty():
                filename = self._normroi.getFilename()
                if exists(filename):
                    wait.setInformationText('Open signal normalization mask\n{}...'.format(basename(filename)))
                    roi = SisypheROI()
                    roi.load(filename)
            # Signal normalization
            self._design.setSignalNormalization(self._cnorm.currentIndex())
            # Signal ANCOVA
            c = self._cancova.currentText()
            if c == 'global': self._design.setSignalGlobalCovariable()
            elif c == 'by group': self._design.setSignalCovariableByGroup()
            elif c == 'by subject': self._design.setSignalCovariableBySubject()
            elif c == 'by condition': self._design.setSignalCovariableByCondition()
            # Age covariable
            c = self._age.currentText()
            if c == 'no': self._design.setNoAgeCovariable()
            elif c == 'global': self._design.setAgeGlobalCovariable()
            elif c == 'by group': self._design.setAgeCovariableByGroup()
            elif c == 'by subject': self._design.setAgeCovariableBySubject()
            elif c == 'by condition': self._design.setAgeCovariableByCondition()
            # estimate
            self._design.estimate(mask=mask, roi=roi, wait=wait)
            wait.close()
            # save model
            self.saveModel()
            self.accept()
        else: messageBox(self, 'Model estimation', 'Missing observation(s).')

    def saveModel(self, filename=''):
        if filename != '': self._design.saveAs(filename)
        else:
            if self._design.hasFilename(): path = self._design.getFilename()
            else:
                path = join(expanduser('~'), '.PySisyphe', 'models')
                if not exists(path): path = ''
            filename = QFileDialog.getSaveFileName(self, 'Save statistical model', path,
                                                   filter=self._design.getFilterExt())[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                if not self._design.isEstimated():
                    # < Revision 03/12/2024
                    # update signal normalization, ANCOVA and age attributes
                    # Signal normalization
                    self._design.setSignalNormalization(self._cnorm.currentIndex())
                    # Signal ANCOVA
                    c = self._cancova.currentText()
                    if c == 'global': self._design.setSignalGlobalCovariable()
                    elif c == 'by group': self._design.setSignalCovariableByGroup()
                    elif c == 'by subject': self._design.setSignalCovariableBySubject()
                    elif c == 'by condition': self._design.setSignalCovariableByCondition()
                    # Age covariable
                    c = self._age.currentText()
                    if c == 'no': self._design.setNoAgeCovariable()
                    elif c == 'global': self._design.setAgeGlobalCovariable()
                    elif c == 'by group': self._design.setAgeCovariableByGroup()
                    elif c == 'by subject': self._design.setAgeCovariableBySubject()
                    elif c == 'by condition': self._design.setAgeCovariableByCondition()
                    # Revision 03/12/2024 >
                    # < Revision 29/11/2024
                    # add observations
                    for i in range(self._obsitem.childCount()):
                        item = self._obsitem.child(i)
                        # < Revision 05/06/2025
                        # get key from QTreeWidgetItem data, not from text
                        # key = item.text(0).split(' ')
                        key = item.data(0, Qt.UserRole)
                        # Revision 05/06/2025 >
                        self._design.clearFileObsFrom(key[0], key[1], key[2])
                        n = item.childCount()
                        if n > 0:
                            filenames = list()
                            for j in range(n):
                                filenames.append(item.child(j).data(1, Qt.UserRole))
                            self._design.appendFileObsTo(filenames, key[0], key[1], key[2])
                    # Revision 29/11/2024 >
                self._design.setFilename(filename)
                wait = DialogWait(title=self.windowTitle())
                wait.open()
                try: self._design.save(wait)
                except: messageBox(self, title='Save model', text='{} IO error.'.format(basename(filename)))
                finally: wait.close()

    def getModel(self):
        return self._design


class DialogObs(QDialog):
    """
    DialogObs class

    Description
    ~~~~~~~~~~~

    GUI dialog to add observations to statistical model.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogObs

    Creation: 29/11/2022
    Last revision: 19/11/2024
    """

    # Special method

    """
    Private attributes

    _grps       list[LabeledSpinBox], observation count by groups
    _cnds       list[LabeledSpinBox], condition count by conditions
    _cnd        LabeledSpinBox, condition count
    _sbj        LabeledSpinBox, subject count
    _grp        LabeledSpinBox, group count
    _treeobs    QTreeWidget
    """

    def __init__(self,
                 title: str = 'Model design',
                 cnd: int | None = 0,
                 sbj: int | None = 0,
                 grp: int | None = 0,
                 parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle(title)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._grps = None
        self._sbjs = None
        self._cnds = None

        # Init widgets

        self._cnd = LabeledSpinBox(title='Condition count', fontsize=14, parent=self)
        self._cnd.setRange(0, 50)
        self._cnd.setVisible(cnd == 0)
        if cnd is None: cnd = 0
        self._cnd.setValue(cnd)
        # noinspection PyUnresolvedReferences
        self._cnd.valueChanged.connect(lambda: self._updateTreeObs())
        self._sbj = LabeledSpinBox(title='  Subject count', fontsize=14, parent=self)
        self._sbj.setRange(0, 50)
        self._sbj.setVisible(sbj == 0)
        if sbj is None: sbj = 0
        self._sbj.setValue(sbj)
        # noinspection PyUnresolvedReferences
        self._sbj.valueChanged.connect(lambda: self._updateTreeObs())
        self._grp = LabeledSpinBox(title='    Group count', fontsize=14, parent=self)
        self._grp.setRange(0, 50)
        self._grp.setVisible(grp == 0)
        if grp is None: grp = 0
        self._grp.setValue(grp)
        # noinspection PyUnresolvedReferences
        self._grp.valueChanged.connect(lambda: self._updateTreeObs())

        self._treeobs = QTreeWidget(parent=self)
        self._treeobs.setHeaderLabel('Model design')
        header = QTreeWidgetItem()
        header.setText(0, 'Group design')
        header.setText(1, 'Observations')
        header.setText(2, '')
        self._treeobs.setHeaderItem(header)
        # noinspection PyTypeChecker
        self._treeobs.header().setSectionResizeMode(QHeaderView.Stretch)
        # noinspection PyTypeChecker
        self._treeobs.header().setDefaultAlignment(Qt.AlignCenter)
        self._treeobs.header().setStretchLastSection(False)
        self._updateTreeObs()
        # self._treeobs.setFixedWidth(500)

        self._layout.addWidget(self._cnd, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._sbj, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._grp, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._treeobs)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setCheckable(False)
        cancel.setFixedWidth(100)
        self._ok = QPushButton('OK', parent=self)
        self._ok.setCheckable(False)
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        self._layout.addLayout(layout)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._treeobs.setMinimumWidth(int(screen.width() * 0.40))
        # dialog resize off
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    def _updateTreeObs(self):
        self._treeobs.clear()
        if self._sbj.value() > 0:
            # Group(s)
            if self._grp.value() > 0:
                grpitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
                grpitem.setText(0, 'Group(s)')
                for i in range(self._grp.value()):
                    item = QTreeWidgetItem(grpitem)
                    item.setText(0, 'Group#{}'.format(i + 1))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setToolTip(0, 'Double-click to edit group name')
            # Subject(s)
            if self._sbj.value() > 0:
                self._sbjs = list()
                sbjitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
                sbjitem.setText(0, 'Subject(s)')
                for i in range(self._sbj.value()):
                    item = QTreeWidgetItem(sbjitem)
                    item.setText(0, 'Subject#{}'.format(i + 1))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setToolTip(0, 'Double-click to edit subject name')
                    combo = LabeledComboBox(fontsize=10)
                    if self._grp.value() > 0:
                        for j in range(self._grp.value()):
                            combo.addItem('Group#{}'.format(j + 1))
                    else:
                        combo.addItem('Group#1')
                        combo.setVisible(False)
                    combo.setCurrentIndex(0)
                    self._treeobs.setItemWidget(item, 1, combo)
                    if self._cnd.value() == 0:
                        spin = LabeledSpinBox()
                        spin.setRange(1, 500)
                        spin.setValue(1)
                        spin.setAlignment(Qt.AlignCenter)
                        spin.setTitle('Image count')
                        self._sbjs.append(item)
                        self._treeobs.setItemWidget(item, 2, spin)
            # Condition(s)
            if self._cnd.value() > 0:
                self._cnds = list()
                cnditem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
                cnditem.setText(0, 'Condition(s)')
                cnditem.setExpanded(True)
                for i in range(self._cnd.value()):
                    item = QTreeWidgetItem(cnditem)
                    item.setText(0, 'Condition#{}'.format(i+1))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setToolTip(0, 'Double-click to edit condition name')
                    spin = LabeledSpinBox()
                    spin.setRange(1, 500)
                    spin.setValue(1)
                    spin.setAlignment(Qt.AlignCenter)
                    spin.setTitle('Image count')
                    self._cnds.append(item)
                    self._treeobs.setItemWidget(item, 1, spin)
        else:
            # Group(s)
            self._grps = list()
            grpitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
            grpitem.setText(0, 'Group(s)')
            grpitem.setExpanded(True)
            for i in range(self._grp.value()):
                item = QTreeWidgetItem(grpitem)
                item.setText(0, 'Group#{}'.format(i+1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit group name')
                spin = LabeledSpinBox()
                spin.setRange(1, 500)
                spin.setValue(1)
                spin.setAlignment(Qt.AlignCenter)
                spin.setTitle('Image count')
                self._grps.append(item)
                self._treeobs.setItemWidget(item, 1, spin)

    # Public methods

    def getConditionCount(self):
        return self._cnd.value()

    def getSubjectCount(self):
        return self._sbj.value()

    def getGroupCount(self):
        return self._grp.value()

    def setConditionCount(self, n: int):
        self._cnd.setValue(n)

    def setSubjectCount(self, n: int):
        self._sbj.setValue(n)

    def setGroupCount(self, n: int):
        return self._grp.setValue(n)

    def getGroupNames(self):
        r = list()
        if self._grp.value() > 0:
            grpitem = self._treeobs.findItems('Group(s)', Qt.MatchExactly, column=0)
            if len(grpitem) > 0:
                grpitem = grpitem[0]
                if grpitem.childCount() > 0:
                    for i in range(self._grp.value()):
                        r.append(grpitem.child(i).text(0))
        return r

    def getSubjectNames(self):
        r = list()
        if self._sbj.value() > 0:
            sbjitem = self._treeobs.findItems('Subject(s)', Qt.MatchExactly, column=0)
            if len(sbjitem) > 0:
                sbjitem = sbjitem[0]
                if sbjitem.childCount() > 0:
                    if self._grp.value() == 0:
                        for i in range(self._sbj.value()):
                            r.append(sbjitem.child(i).text(0))
                    else:
                        grpitem = self._treeobs.findItems('Group(s)', Qt.MatchExactly, column=0)
                        for i in range(self._sbj.value()):
                            item = sbjitem.child(i)
                            c = self._treeobs.itemWidget(item, 1).currentIndex()
                            r.append(item.text(0) + ' ' + grpitem[0].child(c).text(0))
        return r

    def getConditionNames(self):
        r = list()
        if self._cnd.value() > 0:
            cnditem = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)
            if len(cnditem) > 0:
                cnditem = cnditem[0]
                if cnditem.childCount() > 0:
                    for i in range(self._cnd.value()):
                        r.append(cnditem.child(i).text(0))
        return r

    def getTreeObsCount(self):
        r = dict()
        grpitems = self._treeobs.findItems('Group(s)', Qt.MatchExactly, column=0)
        if len(grpitems) > 0: grpitems = grpitems[0]
        if self._grp.value() > 0:
            for i in range(grpitems.childCount()):
                item = grpitems.child(i)
                r[(item.text(0), 0)] = dict()
        if self._sbj.value() > 0:
            sbjitems = self._treeobs.findItems('Subject(s)', Qt.MatchExactly, column=0)[0]
            if self._cnd.value() > 0:
                cnditems = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)[0]
                for i in range(sbjitems.childCount()):
                    item = sbjitems.child(i)
                    if self._grp.value() > 0:
                        grp = grpitems.child(self._treeobs.itemWidget(item, 1).currentIndex()).text(0)
                        r[(grp, 0)][(item.text(0), 1)] = dict()
                        for j in range(cnditems.childCount()):
                            item2 = cnditems.child(j)
                            cnd = item2.text(0)
                            r[(grp, 0)][(item.text(0), 1)][(cnd, 2)] = [self._treeobs.itemWidget(item2, 1).value()]
                    else:
                        r[(item.text(0), 1)] = dict()
                        for j in range(cnditems.childCount()):
                            item2 = cnditems.child(j)
                            cnd = item2.text(0)
                            r[(item.text(0), 1)][(cnd, 2)] = [self._treeobs.itemWidget(item2, 1).value()]
            else:
                for i in range(sbjitems.childCount()):
                    item = sbjitems.child(i)
                    if self._grp.value() > 0:
                        grp = grpitems.child(self._treeobs.itemWidget(item, 1).currentIndex()).text(0)
                        r[(grp, 0)][(item.text(0), 1)] = [self._treeobs.itemWidget(item, 2).value()]
                    else: r[(item.text(0), 1)] = [self._treeobs.itemWidget(item, 2).value()]
        else:
            if self._grp.value() > 0:
                for i in range(grpitems.childCount()):
                    item = grpitems.child(i)
                    r[(item.text(0), 0)] = [self._treeobs.itemWidget(item, 1).value()]
            elif self._cnd.value() > 0:
                cnditems = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)[0]
                for i in range(cnditems.childCount()):
                    item = cnditems.child(i)
                    r[(item.text(0), 2)] = [self._treeobs.itemWidget(item, 1).value()]
        return r


class DialogfMRIObs(QDialog):
    """
    DialogfMRIObs class

    Description
    ~~~~~~~~~~~

    GUI dialog to add observations to fMRI statistical model.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogObs

    Creation: 29/11/2022
    Last revision: 19/11/2024
    """

    # Special method

    """
    Private attributes

    _cnds       list[LabeledSpinBox], condition count by conditions
    _cnd        LabeledSpinBox, condition count
    _sbj        LabeledSpinBox, subject count
    _grp        LabeledSpinBox, group count
    _treeobs    QTreeWidget
    """

    def __init__(self,
                 title: str = 'fMRI model design',
                 cnd: int | None = 0,
                 sbj: int | None = 0,
                 grp: int | None = 0,
                 parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle(title)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout



        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._cnds = None

        # Init widgets

        self._cnd = LabeledSpinBox(title='Condition count', fontsize=14, parent=self)
        # self._cnd.setFixedWidth(200)
        self._cnd.setRange(0, 50)
        self._cnd.setVisible(cnd == 0)
        if cnd is None: cnd = 0
        self._cnd.setValue(cnd)
        # noinspection PyUnresolvedReferences
        self._cnd.valueChanged.connect(lambda: self._updateTreeObs())
        self._sbj = LabeledSpinBox(title='  Subject count', fontsize=14, parent=self)
        # self._sbj.setFixedWidth(200)
        self._sbj.setRange(0, 50)
        self._sbj.setVisible(sbj == 0)
        if sbj is None: sbj = 0
        self._sbj.setValue(sbj)
        # noinspection PyUnresolvedReferences
        self._sbj.valueChanged.connect(lambda: self._updateTreeObs())
        self._grp = LabeledSpinBox(title='    Group count', fontsize=14, parent=self)
        # self._grp.setFixedWidth(200)
        self._grp.setRange(0, 50)
        self._grp.setVisible(grp == 0)
        if grp is None: grp = 0
        self._grp.setValue(grp)
        # noinspection PyUnresolvedReferences
        self._grp.valueChanged.connect(lambda: self._updateTreeObs())

        self._treeobs = QTreeWidget(parent=self)
        self._treeobs.setHeaderLabel('Box car fMRI model')
        self._treeobs.setColumnCount(6)
        header = QTreeWidgetItem()
        header.setText(0, 'Condition')
        header.setText(1, 'First')
        header.setText(2, 'Active')
        header.setText(3, 'Rest')
        header.setText(4, 'Blocks')
        header.setText(5, 'Inter-scan')
        self._treeobs.setHeaderItem(header)
        # noinspection PyTypeChecker
        self._treeobs.header().setSectionResizeMode(QHeaderView.Stretch)
        # noinspection PyTypeChecker
        self._treeobs.header().setDefaultAlignment(Qt.AlignCenter)
        self._treeobs.header().setStretchLastSection(False)
        self._updateTreeObs()

        self._layout.addWidget(self._cnd, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._sbj, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._grp, alignment=Qt.AlignCenter)
        self._layout.addWidget(self._treeobs)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setCheckable(False)
        cancel.setFixedWidth(100)
        self._ok = QPushButton('OK', parent=self)
        self._ok.setCheckable(False)
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

        self._layout.addLayout(layout)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._treeobs.setMinimumWidth(int(screen.width() * 0.40))
        # dialog resize off
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    def _updateTreeObs(self):
        self._treeobs.clear()
        # Group(s)
        if self._grp.value() > 0:
            grpitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
            grpitem.setText(0, 'Group(s)')
            for i in range(self._grp.value()):
                item = QTreeWidgetItem(grpitem)
                item.setText(0, 'Group#{}'.format(i + 1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit group name')
        # Subject(s)
        if self._sbj.value() > 0:
            sbjitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
            sbjitem.setText(0, 'Subject(s)')
            for i in range(self._sbj.value()):
                item = QTreeWidgetItem(sbjitem)
                item.setText(0, 'Subject#{}'.format(i + 1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit subject name')
                combo = LabeledComboBox(fontsize=10)
                if self._grp.value() > 0:
                    for j in range(self._grp.value()):
                        combo.addItem('Group#{}'.format(j + 1))
                else:
                    combo.addItem('Group#1')
                    combo.setVisible(False)
                combo.setCurrentIndex(0)
                self._treeobs.setItemWidget(item, 1, combo)
        # Conditions
        cnditem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
        cnditem.setText(0, 'Condition(s)')
        cnditem.setExpanded(True)
        if self._cnd.value() > 0:
            self._cnds = list()
            for i in range(self._cnd.value()):
                item = QTreeWidgetItem(cnditem)
                item.setText(0, 'Condition#{}'.format(i+1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit condition name')
                sfirst = LabeledSpinBox()
                sfirst.setRange(1, 50)
                sfirst.setValue(10)
                sfirst.setAlignment(Qt.AlignCenter)
                sfirst.setToolTip('Number of images before first active block.')
                sact = LabeledSpinBox()
                sact.setRange(1, 50)
                sact.setValue(10)
                sact.setAlignment(Qt.AlignCenter)
                sact.setToolTip('Number of images in active blocks.')
                srst = LabeledSpinBox()
                srst.setRange(1, 50)
                srst.setValue(10)
                srst.setAlignment(Qt.AlignCenter)
                srst.setToolTip('Number of images in rest blocks.')
                sblk = LabeledSpinBox()
                sblk.setRange(1, 50)
                sblk.setValue(5)
                sblk.setAlignment(Qt.AlignCenter)
                sblk.setToolTip('Number of blocks, one block alternates between rest and activity.')
                iscn = LabeledDoubleSpinBox()
                iscn.setRange(1.0, 4.0)
                iscn.setValue(2.0)
                iscn.setAlignment(Qt.AlignCenter)
                iscn.setToolTip('Inter-scan interval (s), TR echo-planar time series.')
                self._cnds.append([sfirst, sact, srst, sblk, iscn])
                self._treeobs.setItemWidget(item, 1, sfirst)
                self._treeobs.setItemWidget(item, 2, sact)
                self._treeobs.setItemWidget(item, 3, srst)
                self._treeobs.setItemWidget(item, 4, sblk)
                self._treeobs.setItemWidget(item, 5, iscn)

    # Public methods

    def getConditionCount(self):
        return self._cnd.value()

    def getSubjectCount(self):
        return self._sbj.value()

    def getGroupCount(self):
        return self._grp.value()

    def getGroupNames(self):
        """
            return list of str, group name
        """
        r = list()
        if self._grp.value() > 0:
            grpitem = self._treeobs.findItems('Group(s)', Qt.MatchExactly, column=0)
            if len(grpitem) > 0:
                grpitem = grpitem[0]
                if grpitem.childCount() > 0:
                    for i in range(self._cnd.value()):
                        r.append(grpitem.child(i).text(0))
                    return r
        return []

    def getSubjectNames(self):
        """
            return list of str, subject name
        """
        r = list()
        if self._sbj.value() > 0:
            sbjitem = self._treeobs.findItems('Subject(s)', Qt.MatchExactly, column=0)
            if len(sbjitem) > 0:
                sbjitem = sbjitem[0]
                if sbjitem.childCount() > 0:
                    for i in range(self._cnd.value()):
                        # noinspection PyUnresolvedReferences
                        r.append(sbjitem.child(i).text(0))
                    return r
        return []

    def getConditionNames(self):
        """
            return list of str, condition name
        """
        r = list()
        if self._cnd.value() > 0:
            cnditem = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)
            if len(cnditem) > 0:
                cnditem = cnditem[0]
                if cnditem.childCount() > 0:
                    for i in range(self._cnd.value()):
                        r.append(cnditem.child(i).text(0))
                    return r
        return []

    def getTreeObsCount(self):
        r = dict()
        grpitems = self._treeobs.findItems('Group(s)', Qt.MatchExactly, column=0)
        if len(grpitems) > 0: grpitems = grpitems[0]
        if self._grp.value() > 0:
            for i in range(grpitems.childCount()):
                item = grpitems.child(i)
                r[(item.text(0), 0)] = dict()
        if self._sbj.value() > 0:
            sbjitems = self._treeobs.findItems('Subject(s)', Qt.MatchExactly, column=0)[0]
            if self._cnd.value() > 0:
                cnditems = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)[0]
                for i in range(sbjitems.childCount()):
                    item = sbjitems.child(i)
                    if self._grp.value() > 0:
                        grp = grpitems.child(self._treeobs.itemWidget(item, 1).currentIndex()).text(0)
                        r[(grp, 0)][(item.text(0), 1)] = dict()
                        for j in range(cnditems.childCount()):
                            item2 = cnditems.child(j)
                            first = self._treeobs.itemWidget(item2, 1).value()
                            act = self._treeobs.itemWidget(item2, 2).value()
                            rst = self._treeobs.itemWidget(item2, 3).value()
                            blk = self._treeobs.itemWidget(item2, 4).value()
                            iscn = self._treeobs.itemWidget(item2, 5).value()
                            n = first + (act + rst) * blk
                            cnd = item2.text(0)
                            r[(grp, 0)][(item.text(0), 1)][(cnd, 2)] = [n, first, act, rst, blk, iscn]
                    else:
                        r[(item.text(0), 1)] = dict()
                        for j in range(cnditems.childCount()):
                            item2 = cnditems.child(j)
                            first = self._treeobs.itemWidget(item2, 1).value()
                            act = self._treeobs.itemWidget(item2, 2).value()
                            rst = self._treeobs.itemWidget(item2, 3).value()
                            blk = self._treeobs.itemWidget(item2, 4).value()
                            iscn = self._treeobs.itemWidget(item2, 5).value()
                            n = first + (act + rst) * blk
                            cnd = item2.text(0)
                            r[(item.text(0), 1)][(cnd, 2)] = [n, first, act, rst, blk, iscn]
        else:
            if self._cnd.value() > 0:
                cnditems = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)[0]
                for i in range(cnditems.childCount()):
                    item = cnditems.child(i)
                    first = self._treeobs.itemWidget(item, 1).value()
                    act = self._treeobs.itemWidget(item, 2).value()
                    rst = self._treeobs.itemWidget(item, 3).value()
                    blk = self._treeobs.itemWidget(item, 4).value()
                    iscn = self._treeobs.itemWidget(item, 5).value()
                    n = first + (act + rst) * blk
                    r[(item.text(0), 2)] = [n, first, act, rst, blk, iscn]
        return r
