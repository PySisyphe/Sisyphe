"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        pandas          https://pandas.pydata.org/                                  Data analysis and manipulation tool
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import exists
from os.path import basename
from os.path import splitext

from numpy import ndarray
from numpy import load
from numpy import loadtxt
from numpy import genfromtxt

from pandas import DataFrame
from pandas import read_excel

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['DialogModel',
           'DialogObs',
           'DialogfMRIObs']

"""
    Class hierarchy

        QDialog -> DialogModel
                -> DialogObs
                -> DialogfMRIObs
"""

class DialogModel(QDialog):
    """
        DialogModel class

        Description

            Dialog GUI for voxel by voxel statistical model definition and estimation.

        Inheritance

            QDialog -> DialogModel

        Private attributes

            _fmri       bool
            _size       (int, int, int)
            _spacing    (float, float, float)
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


        Public methods

            getObservationCount()
            addObservations()
            remove()
            clear()
            addGlobalVariable()
            addCovariableByGroup()
            addCovariableBySubject()
            addCovariableByCondition()
            addHighPassCovariable()
            estimate()
            saveModel()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, cnd, sbj, grp, obscnd, obsgrp, fmri, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical model definition')

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._fmri = fmri
        self._obscnd = obscnd
        self._obsgrp = obsgrp
        self._size = None
        self._spacing = None
        self._design = SisypheDesign()
        if fmri: self._design.setfMRIDesign()
        ngrp = len(grp)
        nsbj = len(sbj)
        ncnd = len(cnd)
        if ngrp > 0:
            for i in range(ngrp):
                self._design.addGroup(grp[i])
        if nsbj > 0:
            if ngrp == 0: g = 1
            else: g = ngrp
            for i in range(nsbj*g):
                self._design.addSubject(sbj[i])
        if ncnd > 0:
            for i in range(ncnd):
                self._design.addCondition(cnd[i])

        # Init widgets

        self._treeobs = QTreeWidget()
        self._treeobs.setColumnCount(2)
        header = QTreeWidgetItem()
        header.setText(0, 'Observation(s)/Covariable(s)')
        header.setText(1, 'Image count')
        self._treeobs.header().resizeSection(0, 300)
        self._treeobs.setHeaderItem(header)
        self._treeobs.itemDoubleClicked.connect(self._itemDoubleClicked)
        # Observations
        self._obsitem = QTreeWidgetItem(['Observations'])
        self._obsitem.setExpanded(True)
        self._obsitems = list()
        if ngrp > 0 and ncnd == 0:
            for i in range(ngrp):
                name = self._design.getGroupName(i)
                self._obsitems.append(QTreeWidgetItem([name, str(obsgrp[name])]))
                self._obsitems[i].setToolTip(0, 'Double-click to add image(s)')
                self._obsitem.addChild(self._obsitems[i])
        if ncnd > 0:
            childgrp = list()
            childsbj = list()
            if ngrp > 0 and nsbj > 0:
                for i in range(ngrp):
                    childgrp.append(QTreeWidgetItem([self._design.getGroupName(i), '']))
                    self._obsitem.addChild(childgrp)
                    for j in range(nsbj):
                        childsbj.append(QTreeWidgetItem([self._design.getSubjectName(j), '']))
                        childgrp[0].addChild(childsbj)
                        for k in range(ncnd):
                            name = self._design.getConditionName(k)
                            self._obsitems.append(QTreeWidgetItem([name, str(obscnd[name][0])]))
                            self._obsitems[i].setToolTip(0, 'Double-click to add image(s)')
                            childsbj[0].addChild(self._obsitems[k])
            elif ngrp == 0 and nsbj > 0:
                childgrp.append(QTreeWidgetItem(['Group', '0']))
                self._obsitem.addChild(childgrp[0])
                for i in range(nsbj):
                    childsbj.append(QTreeWidgetItem([self._design.getSubjectName(i), '']))
                    childgrp[0].addChild(childsbj)
                    for j in range(ncnd):
                        name = self._design.getConditionName(j)
                        self._obsitems.append(QTreeWidgetItem([name, str(obscnd[name][0])]))
                        self._obsitems[i].setToolTip(0, 'Double-click to add image(s)')
                        childsbj[0].addChild(self._obsitems[j])
            else:  # grp == 0 and sbj == 0
                childgrp.append(QTreeWidgetItem(['Group', '']))
                self._obsitem.addChild(childgrp[0])
                childsbj.append(QTreeWidgetItem(['Subject', '']))
                childgrp[0].addChild(childsbj[0])
                for i in range(ncnd):
                    name = self._design.getConditionName(i)
                    self._obsitems.append(QTreeWidgetItem([name, str(obscnd[name][0])]))
                    self._obsitems[i].setToolTip(0, 'Double-click to add image(s)')
                    childsbj[0].addChild(self._obsitems[i])
        # Covariables
        self._glbcovitem = QTreeWidgetItem(['Global Covariable(s)'])
        self._grpcovitem = QTreeWidgetItem(['Covariable(s) by group'])
        self._sbjcovitem = QTreeWidgetItem(['Covariable(s) by subject'])
        self._cndcovitem = QTreeWidgetItem(['Covariable(s) by condition'])
        self._glbcovitem.setToolTip(0, 'Double-click to add covariable(s)')
        self._grpcovitem.setToolTip(0, 'Double-click to add covariable(s)')
        self._sbjcovitem.setToolTip(0, 'Double-click to add covariable(s)')
        self._cndcovitem.setToolTip(0, 'Double-click to add covariable(s)')
        self._treeobs.addTopLevelItem(self._obsitem)
        self._treeobs.addTopLevelItem(self._glbcovitem)
        if ngrp > 0: self._treeobs.addTopLevelItem(self._grpcovitem)
        if nsbj > 0: self._treeobs.addTopLevelItem(self._sbjcovitem)
        if ncnd > 0: self._treeobs.addTopLevelItem(self._cndcovitem)

        self._addObs = QPushButton('Add observation(s)')
        self._addObs.pressed.connect(self.addObservations)
        self._covGlobal = QPushButton('Add global cov.')
        self._covGlobal.pressed.connect(self.addGlobalCovariable)
        self._covByGroup = QPushButton('Add cov. by Group')
        self._covByGroup.setVisible(ngrp > 0)
        self._covByGroup.pressed.connect(self.addCovariableByGroup)
        self._covBySubject = QPushButton('Add cov. by Subject')
        self._covBySubject.setVisible(nsbj > 0)
        self._covBySubject.pressed.connect(self.addCovariableBySubject)
        self._covByCondition = QPushButton('Add cov. by Condition')
        self._covByCondition.setVisible(ncnd > 0)
        self._covByCondition.pressed.connect(self.addCovariableByCondition)
        self._covHighPass = QCheckBox('High pass cov.')
        self._covHighPass.setVisible(fmri)
        self._covHighPass.toggled.connect(self.addHighPassCovariable)
        self._covRealign = QCheckBox('Realignment cov.')
        self._covRealign.setVisible(fmri)
        self._covRealign.toggled.connect(self.addRealignmentCovariable)
        self._remove = QPushButton('Remove')
        self._remove.pressed.connect(self.remove)
        self._clear = QPushButton('Remove all')
        self._clear.pressed.connect(self.clear)
        self._view = QPushButton('View design')
        self._view.setToolTip('Display design matrix.')
        self._view.pressed.connect(self._viewDesign)
        self._save = QPushButton('Save')
        self._save.setToolTip('Save statistical model.')
        self._save.pressed.connect(self.saveModel)
        lyout1 = QHBoxLayout()
        lyout1.setSpacing(10)
        lyout1.addWidget(self._addObs)
        lyout1.addWidget(self._covGlobal)
        lyout1.addWidget(self._covByGroup)
        lyout1.addWidget(self._covBySubject)
        lyout1.addWidget(self._covByCondition)
        lyout1.addWidget(self._covHighPass)
        lyout1.addWidget(self._covRealign)
        lyout1.addWidget(self._remove)
        lyout1.addWidget(self._clear)

        self._cmask = LabeledComboBox(fontsize=14)
        self._cmask.setSizeAdjustPolicy(0)
        self._cmask.setTitle('Mask')
        self._cmask.addItem('Auto')
        self._cmask.addItem('ROI')
        self._cmask.addItem('Auto & ROI')
        self._cmask.currentIndexChanged.connect(self._combBoxMaskItemChanged)
        self._maskroi = FileSelectionWidget()
        self._maskroi.setFixedWidth(400)
        self._maskroi.setTextLabel('Mask ROI')
        self._maskroi.setVisible(False)
        self._maskroi.setEnabled(False)
        self._maskroi.filterSisypheROI()
        lyout2 = QHBoxLayout()
        lyout2.setSpacing(10)
        lyout2.addWidget(self._cmask)
        lyout2.addStretch()
        lyout2.addWidget(self._maskroi)

        self._cnorm = LabeledComboBox(fontsize=14)
        self._cnorm.setSizeAdjustPolicy(0)
        self._cnorm.setTitle('Signal normalization')
        self._cnorm.addItem('No')
        self._cnorm.addItem('Mean scaling')
        self._cnorm.addItem('Median scaling')
        self._cnorm.addItem('75th perc. scaling')
        self._cnorm.addItem('ROI mean scaling')
        self._cnorm.addItem('ROI median scaling')
        self._cnorm.addItem('ROI 75th perc. scaling')
        self._cnorm.addItem('ANCOVA Mean scaling')
        self._cnorm.addItem('ANCOVA Median scaling')
        self._cnorm.addItem('ANCOVA 75th perc. scaling')
        self._cnorm.addItem('ANCOVA ROI mean scaling')
        self._cnorm.addItem('ANCOVA ROI median scaling')
        self._cnorm.addItem('ANCOVA ROI 75th perc. scaling')
        self._cnorm.currentIndexChanged.connect(self._comboBoxNormItemChanged)
        self._cancova = LabeledComboBox(fontsize=14)
        self._cancova.setSizeAdjustPolicy(0)
        self._cancova.setTitle('ANCOVA')
        self._cancova.addItem('Global')
        if ngrp > 0: self._cancova.addItem('by group')
        if nsbj > 0: self._cancova.addItem('by subject')
        if ncnd > 0: self._cancova.addItem('by condition')
        self._cancova.setVisible(False)
        self._cancova.currentIndexChanged.connect(lambda: self._comboBoxAncovaItemChanged())
        self._normroi = FileSelectionWidget()
        self._normroi.setFixedWidth(400)
        self._normroi.setTextLabel('Norm. ROI')
        self._normroi.setVisible(False)
        self._normroi.setEnabled(False)
        self._normroi.filterSisypheROI()
        lyout3 = QHBoxLayout()
        lyout3.setSpacing(10)
        lyout3.addWidget(self._cnorm)
        lyout3.addWidget(self._cancova)
        lyout3.addStretch()
        lyout3.addWidget(self._normroi)

        self._layout.addWidget(self._treeobs)
        self._layout.addLayout(lyout1)
        self._layout.addLayout(lyout2)
        self._layout.addLayout(lyout3)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._ok = QPushButton('Estimate')
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._ok.pressed.connect(self.estimate)
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

    # Private

    def _combBoxMaskItemChanged(self, index):
        self._maskroi.setVisible(index > 0)

    def _comboBoxNormItemChanged(self, index):
        self._normroi.setVisible(index in (4, 5, 6, 10, 11, 12))
        self._cancova.setVisible(index > 6)

    def _comboBoxAncovaItemChanged(self):
        if self._cancova.currentText() == 'by group': self._design.setAncovaByGroup()
        elif self._cancova.currentText() == 'by subject': self._design.setAncovaBySubject()
        elif self._cancova.currentText() == 'by condition': self._design.setAncovaByCondition()
        else: self._design.setAncovaGlobal()

    def _itemDoubleClicked(self, item, column):
        if item.columnCount() > 1:
            if item.text(1).isdigit():
                n = int(item.text(1))
                print(n)
        else:
            if item.text(0) == 'Add global cov.': self.addGlobalCovariable()
            elif item.text(0) == 'Add cov. by Group': self.addCovariableByGroup()
            elif item.text(0) == 'Add cov. by Subject': self.addCovariableBySubject()
            elif item.text(0) == 'Add cov. by Condition': self.addCovariableByCondition()

    def _calcDesign(self):
        self._design.getDesign()
        if self._fmri:
            # Add box car model
            for i in range(len(self._obscnd)):
                cond = self._obscnd[0]
                first = self._obscnd[1]
                active = self._obscnd[2]
                rest = self._obscnd[3]
                nblk = self._obscnd[4]
                iscan = self._obscnd[5]
                self._design.addHRFBoxCarModelToCondition(cond, first, active, rest, nblk, iscan)
            # Add high pass covariable
            item = self._treeobs.findItems('HighPass', Qt.MatchStartsWith, column=0)
            if len(item) > 0:
                for i in range(len(self._obscnd)):
                    cond = self._obscnd[0]
                    first = self._obscnd[1]
                    active = self._obscnd[2]
                    rest = self._obscnd[3]
                    nblk = self._obscnd[4]
                    nobs = first + (active + rest) * nblk
                    self._design.addHighPassToCondition(cond, nobs, nblk)
        # Add covariable(s) by condition
        if self._cndcovitem.childCount() > 0:
            for i in range(self._cndcovitem.childCount()):
                child = self._cndcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableByCondition(name, v, estimable=1)
        # Add covariable(s) by subject
        if self._sbjcovitem.childCount() > 0:
            for i in range(self._sbjcovitem.childCount()):
                child = self._sbjcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableBySubject(name, v, estimable=1)
        # Add covariable(s) by group
        if self._grpcovitem.childCount() > 0:
            for i in range(self._grpcovitem.childCount()):
                child = self._grpcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addCovariableByGroup(name, v, estimable=1)
        # Add global covariable(s)
        if self._glbcovitem.childCount() > 0:
            for i in range(self._glbcovitem.childCount()):
                child = self._glbcovitem.child(i)
                name = child.text(0)
                v = child.data(0, Qt.UserRole)
                self._design.addGlobalCovariable(name, v, estimable=1)

    def _viewDesign(self):
        self._calcDesign()
        dialog = DialogGenericResults(parent=self)
        dialog.setWindowTitle('Design matrix')
        dialog.newTab(title='')
        dialog.hideTree(0)
        fig = dialog.getFigure(0)
        ax = fig.add_subplot(111)
        ax.pcolormesh(self._design.getDesign())
        lbl = list()
        cdesign = self._design.getBetaInformations()
        for i in range(len(cdesign)):
            lbl.append(cdesign[i][0])
        ax.set_xlabel(lbl)
        dialog.exec()

    # Public methods

    def getObservationCount(self):
        n = 0
        if len(self._obscnd) > 0:
            for k in self._obscnd:
                n += self._obscnd[k]
        elif len(self._obsgrp) > 0:
            for k in self._obsgrp:
                n += self._obsgrp[k]
        return n

    def addObservations(self):
        item = self._treeobs.selectedItems()
        if len(item) > 0: item = item[0]
        if item.columnCount() > 1:
            if item.text(1).isdigit():
                n = int(item.text(1))
                filenames = QFileDialog.getOpenFileNames(self, 'Add observations...', getcwd(),
                                                         filter='PySisyphe (*.xvol)')[0]
                QApplication.processEvents()
                if len(filenames) == n:
                    item.takeChildren()
                    for i in range(n):
                        v = SisypheVolume()
                        v.load(filenames[i])
                        if i == 0:
                            self._size = v.getSize()
                            self._spacing = v.getSpacing()
                            self._normroi.setEnabled(True)
                            self._normroi.filterSameFOV(v)
                            self._maskroi.setEnabled(True)
                            self._maskroi.filterSameFOV(v)
                        else:
                            if v.getSize() != self._size or v.getSpacing() != self._spacing:
                                QMessageBox.warning(self, '{} FOV mismatch.'.format(v.getBasename()))
                                item.takeChildren()
                                break
                        child = QTreeWidgetItem(['Image', filenames[i]])
                        item.addChild(child)
                else:
                    QMessageBox.warning(self, 'You have selected {} PySisyphe volume(s) '
                                              'when {} are needed.'.format(len(filenames), n))

    def remove(self):
        items = self._treeobs.selectedItems()
        if len(items) > 0:
            for item in items:
                if item.text(0)[:5] == 'Image': item.setText(1, '')
                else:
                    p = item.parent()
                    if p is not None:
                        if p.text(0) == 'Global Covariable(s)': p.removeChild(item)
                        elif p.text(0) == 'Covariable(s) by group': p.removeChild(item)
                        elif p.text(0) == 'Covariable(s) by subject': p.removeChild(item)
                        elif p.text(0) == 'Covariable(s) by condition': p.removeChild(item)
        items = self._treeobs.findItems('Image', Qt.MatchStartsWith, column=0)
        if len(items) == 0:
            self._size = None
            self._spacing = None
            self._normroi.clear()
            self._normroi.setEnabled(False)
            self._maskroi.clear()
            self._maskroi.setEnabled(False)

    def clear(self):
        items = self._treeobs.findItems('Image', Qt.MatchStartsWith, column=0)
        if len(items) > 0:
            for item in items:
                item.setText(1, '')
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
            n = self.getObservationCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try: cov = loadtxt(filename, delimiter=',')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try: cov = genfromtxt(filename, delimiter=';')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try: cov = load(filename)
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try: cov = read_excel(filename, engine='openpyxl')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        QMessageBox.warning(self, 'Element count ({})'
                                                                  'differs from observation '
                                                                  'count ({}).'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    self._glbcovitem.addChild(covitem)
                # Pandas
                elif isinstance(cov, DataFrame):
                    if len(cov.columns) > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    QMessageBox.warning(self, 'Element count ({})'
                                                              'differs from observation '
                                                              'count ({}).'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem([col, ''])
                                covitem.setData(0, Qt.UserRole, v)
                                self._glbcovitem.addChild(covitem)

    def addCovariableByGroup(self):
        title = 'Add covariable(s) by group'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            n = self.getObservationCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try: cov = loadtxt(filename, delimiter=',')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try: cov = genfromtxt(filename, delimiter=';')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try: cov = load(filename)
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try: cov = read_excel(filename, engine='openpyxl')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        QMessageBox.warning(self, 'Element count ({})'
                                                                  'differs from observation '
                                                                  'count ({}).'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    self._grpcovitem.addChild(covitem)
                # Pandas
                elif isinstance(cov, DataFrame):
                    if len(cov.columns) > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    QMessageBox.warning(self, 'Element count ({})'
                                                              'differs from observation '
                                                              'count ({}).'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem([col, ''])
                                covitem.setData(0, Qt.UserRole, v)
                                self._grpcovitem.addChild(covitem)

    def addCovariableBySubject(self):
        title = 'Add covariable(s) by subject'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            n = self.getObservationCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try: cov = loadtxt(filename, delimiter=',')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try: cov = genfromtxt(filename, delimiter=';')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try: cov = load(filename)
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try: cov = read_excel(filename, engine='openpyxl')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        QMessageBox.warning(self, 'Element count ({})'
                                                                  'differs from observation '
                                                                  'count ({}).'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    self._sbjcovitem.addChild(covitem)
                # Pandas
                elif isinstance(cov, DataFrame):
                    if len(cov.columns) > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    QMessageBox.warning(self, 'Element count ({})'
                                                              'differs from observation '
                                                              'count ({}).'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem([col, ''])
                                covitem.setData(0, Qt.UserRole, v)
                                self._sbjcovitem.addChild(covitem)

    def addCovariableByCondition(self):
        title = 'Add covariable(s) by condition'
        filename = QFileDialog.getOpenFileName(self, title, getcwd(),
                                               filter='CSV (*.csv);;Excel (*.xlsx);;Numpy (*.npy);;Text (*.txt)')[0]
        if filename:
            n = self.getObservationCount()
            name = basename(filename)
            name, ext = splitext(name)
            ext = ext.lower()
            # Text file
            if ext == '.txt':
                try: cov = loadtxt(filename, delimiter=',')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # CSV file
            elif ext == '.csv':
                try: cov = genfromtxt(filename, delimiter=';')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Numpy file
            elif ext == '.npy':
                try: cov = load(filename)
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            # Excel
            else:
                try: cov = read_excel(filename, engine='openpyxl')
                except:
                    QMessageBox.warning(self, '{} loading error.'.format(basename(filename)))
                    cov = None
            if cov is not None:
                # Numpy
                if isinstance(cov, ndarray):
                    if cov.ndim == 2:
                        ch = [str(i) for i in range(cov.shape[1])]
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            for i in range(cov.shape[1]):
                                if int(r) == i or r == 'All':
                                    v = cov[:, i]
                                    if len(v) != n:
                                        QMessageBox.warning(self, 'Element count ({})'
                                                                  'differs from observation '
                                                                  'count ({}).'.format(len(v), name, n))
                                        break
                                    col = '{}#{}'.format(name, i)
                                    covitem = QTreeWidgetItem([col, ''])
                                    covitem.setData(0, Qt.UserRole, v)
                                    self._cndcovitem.addChild(covitem)
                # Pandas
                elif isinstance(cov, DataFrame):
                    if len(cov.columns) > 1:
                        ch = list(cov.columns)
                        ch.append('All')
                        r, ok = QInputDialog.getItem(self, title, 'Which column you want to import ?', items=ch)
                        if ok:
                            if r != 'All': r = list(cov.columns)
                            else: r = [r]
                            for col in r:
                                v = cov[col].to_numpy()
                                if len(v) != n:
                                    QMessageBox.warning(self, 'Element count ({})'
                                                              'differs from observation '
                                                              'count ({}).'.format(len(v), name, n))
                                    break
                                covitem = QTreeWidgetItem([col, ''])
                                covitem.setData(0, Qt.UserRole, v)
                                self._cndcovitem.addChild(covitem)

    def addHighPassCovariable(self, state):
        item = self._treeobs.findItems('HighPass', Qt.MatchStartsWith, column=0)
        if len(item) == 0:
            covitem = QTreeWidgetItem(['HighPass', ''])
            self._cndcovitem.addChild(covitem)

    def estimate(self):
        self._calcDesign()
        wait = DialogWait(title=self.windowTitle(), parent=self)
        if self._maskroi.isEmpty(): mask = None
        else:
            filename = self._maskroi.getFilename()
            if exists(filename):
                mask = SisypheROI()
                mask.load(filename)
        if self._normroi.isEmpty(): roi = None
        else:
            filename = self._maskroi.getFilename()
            if exists(filename):
                roi = SisypheROI()
                roi.load(filename)
        self._design.estimate(mask=mask, roi=roi, wait=wait)
        wait.close()
        if self._design.hasFilename(): self._design.save()
        else: self.saveModel()
        if self._design.hasFilename():
            r = QMessageBox.question(self, self.windowTitle(),
                                     'Do you want to define a contrast ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes:
                self.parent().contrast(self._design.getFilename())

    def saveModel(self, filename=''):
        if filename != '': self._design.saveAs(filename)
        else:
            filename = QFileDialog.getSaveFileName(self, 'Save statistical model', filename,
                                                   filter='Statistical model ({})'.format(self._design.geModelExt()))[0]
            QApplication.processEvents()
            if filename:
                try: self._design.save(filename)
                except:
                    QMessageBox.warning(self, '{} saving error.'.format(basename(filename)))

class DialogObs(QDialog):
    """
        DialogObs class

        Inheritance

            QDialog -> DialogObs

        Private attributes

            _grps       list of LabeledSpinBox, observation count by groups
            _cnds       list of LabeledSpinBox, condition count by conditions
            _cnd        LabeledSpinBox, condition count
            _sbj        LabeledSpinBox, subject count
            _grp        LabeledSpinBox, group count
            _treeobs    QTreeWidget

        Public methods

            int = getConditionCount()
            int = getSubjectCount()
            int = getGroupCount()
            int = getGroupsObsCount()
            int = getConditionsObsCount()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, cnd, sbj, grp, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical model definition')

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._grps = None
        self._cnds = None

        # Init widgets

        self._cnd = LabeledSpinBox()
        self._cnd.setTitle('Condition count')
        self._cnd.setRange(int(cnd), 50)
        self._cnd.setValue(int(cnd))
        self._cnd.setVisible(cnd)
        self._cnd.valueChanged.connect(lambda: self._updateTreeObs())
        self._sbj = LabeledSpinBox()
        self._sbj.setTitle('Subject count')
        self._sbj.setRange(int(sbj), 50)
        self._sbj.setValue(int(sbj))
        self._sbj.setVisible(sbj)
        self._grp = LabeledSpinBox()
        self._grp.setTitle('Subject count')
        self._grp.setRange(int(grp), 50)
        self._grp.setValue(int(grp))
        self._grp.setVisible(grp)
        self._grp.valueChanged.connect(lambda: self._updateTreeObs())

        self._treeobs = QTreeWidget()
        self._treeobs.setHeaderLabel('Observation count')
        self._updateTreeObs()
        self._treeobs.setFixedWidth(500)

        self._layout.addWidget(self._cnd)
        self._layout.addWidget(self._sbj)
        self._layout.addWidget(self._grp)
        self._layout.addWidget(self._treeobs)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._ok = QPushButton('OK')
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._ok.pressed.connect(self.accept)
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

    # Private method

    def _updateTreeObs(self):
        self._treeobs.clear()
        if self._cnd.value() > 0:
            # Group(s)
            if self._grp.value() > 0:
                grpitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
                grpitem.setText(0, 'Group(s)')
                for i in range(self._sbj.value()):
                    item = QTreeWidgetItem(grpitem)
                    item.setText(0, 'Group#{}'.format(i + 1))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setToolTip(0, 'Double-click to edit subject name')
            # Subject(s)
            if self._sbj.value() > 0:
                sbjitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
                sbjitem.setText(0, 'Subject(s)')
                for i in range(self._sbj.value()):
                    item = QTreeWidgetItem(sbjitem)
                    item.setText(0, 'Subject#{}'.format(i + 1))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setToolTip(0, 'Double-click to edit subject name')
            # Condition(s)
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
                spin.setFixedWidth(120)
                spin.setAlignment(Qt.AlignCenter)
                spin.setTitle('Image count')
                self._cnds.append(spin)
                self._treeobs.setItemWidget(item, 1, self._cnds[i])
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
                spin.setFixedWidth(120)
                spin.setAlignment(Qt.AlignCenter)
                spin.setTitle('Image count')
                self._grps.append(spin)
                self._treeobs.setItemWidget(item, 1, self._grps[i])

    # Public methods

    def getGroupNames(self):
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
        r = list()
        if self._sbj.value() > 0:
            sbjitem = self._treeobs.findItems('Subject(s)', Qt.MatchExactly, column=0)
            if len(sbjitem) > 0:
                sbjitem = sbjitem[0]
                if sbjitem.childCount() > 0:
                    for i in range(self._cnd.value()):
                        r.append(sbjitem.child(i).text(0))
                    return r
        return []

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
        return []

    def getGroupsObsCount(self):
        r = dict()
        for grp in self._grps:
            r[grp.getTitle()] = grp.value()
        return r

    def getConditionsObsCount(self):
        r = dict()
        for cnd in self._cnds:
            r[cnd.getTitle()] = [cnd.value()]
        return r


class DialogfMRIObs(QDialog):
    """
        DialogObs class

        Inheritance

            QDialog -> DialogObs

        Private attributes

            _cnds       list of LabeledSpinBox, condition count by conditions
            _cnd        LabeledSpinBox, condition count
            _sbj        LabeledSpinBox, subject count
            _grp        LabeledSpinBox, group count
            _treeobs    QTreeWidget

        Public methods

            int = getConditionNames()
            int = getSubjectNames()
            int = getGroupNames()
            int = getConditionsBoxCar()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, cnd, sbj, grp, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical model definition')

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        self._cnds = None

        # Init widgets

        self._cnd = LabeledSpinBox()
        self._cnd.setTitle('Condition count')
        self._cnd.setRange(1, 50)
        self._cnd.setValue(1)
        self._cnd.setVisible(cnd)
        self._cnd.valueChanged.connect(lambda: self._updateTreeObs())
        self._sbj = LabeledSpinBox()
        self._sbj.setTitle('Subject count')
        self._sbj.setRange(int(sbj), 50)
        self._sbj.setValue(int(sbj))
        self._sbj.setVisible(sbj)
        self._grp = LabeledSpinBox()
        self._grp.setTitle('Group count')
        self._grp.setRange(int(grp), 50)
        self._grp.setValue(int(grp))
        self._grp.setVisible(grp)
        self._grp.valueChanged.connect(lambda: self._updateTreeObs())

        self._treeobs = QTreeWidget()
        self._treeobs.setHeaderLabel('Box car fMRI models')
        self._treeobs.setColumnCount(6)
        header = QTreeWidgetItem()
        header.setText(0, 'Condition')
        header.setText(1, 'First')
        header.setText(2, 'Active')
        header.setText(3, 'Rest')
        header.setText(4, 'Blocks')
        header.setText(5, 'Inter-scan')
        self._treeobs.setHeaderItem(header)
        self._treeobs.header().resizeSection(0, 150)
        self._treeobs.header().resizeSection(1, 50)
        self._treeobs.header().resizeSection(2, 50)
        self._treeobs.header().resizeSection(3, 50)
        self._treeobs.header().resizeSection(4, 50)
        self._treeobs.header().resizeSection(5, 80)
        self._treeobs.header().setStretchLastSection(False)
        self._updateTreeObs()
        self._treeobs.setFixedWidth(500)

        self._layout.addWidget(self._cnd)
        self._layout.addWidget(self._sbj)
        self._layout.addWidget(self._grp)
        self._layout.addWidget(self._treeobs)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._ok = QPushButton('OK')
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._ok.pressed.connect(self.accept)
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

    # Private method

    def _updateTreeObs(self):
        self._treeobs.clear()
        # Group(s)
        if self._grp.value() > 0:
            grpitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
            grpitem.setText(0, 'Group(s)')
            for i in range(self._sbj.value()):
                item = QTreeWidgetItem(grpitem)
                item.setText(0, 'Group#{}'.format(i + 1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit subject name')
        # Subject(s)
        if self._sbj.value() > 0:
            sbjitem = QTreeWidgetItem(self._treeobs.invisibleRootItem())
            sbjitem.setText(0, 'Subject(s)')
            for i in range(self._sbj.value()):
                item = QTreeWidgetItem(sbjitem)
                item.setText(0, 'Subject#{}'.format(i + 1))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(0, 'Double-click to edit subject name')
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
                self._treeobs.setItemWidget(item, 1, self._cnds[i][0])
                self._treeobs.setItemWidget(item, 2, self._cnds[i][1])
                self._treeobs.setItemWidget(item, 3, self._cnds[i][2])
                self._treeobs.setItemWidget(item, 4, self._cnds[i][3])
                self._treeobs.setItemWidget(item, 5, self._cnds[i][4])

    # Public methods

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

    def getConditionsBoxCar(self):
        """
            return dict r[key], key str = condition name
                r[key][0] int, image count before first activation
                r[key][1] int, image count by activation block
                r[key][2] int, image count by rest block
                r[key][3] int, block count (1 block = 1 active block + 1 rest block)
                r[key][4] float, interscan interval TR (s)
        """
        r = dict()
        cnditem = self._treeobs.findItems('Condition(s)', Qt.MatchExactly, column=0)
        if len(cnditem) > 0:
            cnditem = cnditem[0]
            if cnditem.childCount() > 0:
                for i in range(self._cnd.value()):
                    name = cnditem.child(i).text(0)
                    first = self._cnds[i][0].value()
                    act = self._cnds[i][1].value()
                    rst = self._cnds[i][2].value()
                    blk = self._cnds[i][3].value()
                    n = first + (act + rst) * blk
                    r[name] = [n, first, act, rst, blk, self._cnds[i][4].value()]
                return r
        return []

"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    dlg = DialogfMRIObs(True, False, False, parent=None)
    if dlg.exec():
        cnd0 = dlg.getConditionNames()
        sbj0 = dlg.getSubjectNames()
        grp0 = dlg.getGroupNames()
        obscnd0 = dlg.getConditionsBoxCar()
        obsgrp0 = None
        # obscnd = dlg.getConditionsObsCount()
        # obsgrp = dlg.getGroupsObsCount()
        print(dlg.getConditionNames())
        print('condition(s) {} subject(s) {} group(s) {}'.format(cnd0, sbj0, grp0))
        dlg = DialogModel(cnd0, sbj0, grp0, obscnd0, obsgrp0, fmri=True, parent=None)
        dlg.exec()
