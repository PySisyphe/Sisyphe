"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sys import platform

from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import exists

from glob import glob

from numpy import bincount

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import GetArrayViewFromImage

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import LineWidget
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.core.sisypheConstants import getID_ICBM152
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

if TYPE_CHECKING:
    from PyQt5.QtCore import QObject

__all__ = ['DialogAtlasLabeling']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogAtlasLabeling 
"""


class DialogAtlasLabeling(QDialog):
    """
    DialogAtlasLabeling

    Description
    ~~~~~~~~~~~

    Atlas labeling of ROI, mesh or tools.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogAtlasLabeling

    Creation: 12/02/2026
    Last revision: 14/02/2026
    """

    # Special method

    def __init__(self, title: str = 'ROI', parent: QObject | None = None):
        super().__init__(parent)

        # Init window

        if title in ('ROI', 'Mesh', 'Tools'): self._title = title
        else:  self._title = 'ROI'

        self.setWindowTitle('{} atlas labeling'.format(self._title))
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._reficbm = QCheckBox('Reference ICBM152')
        self._reficbm.setChecked(False)
        self._reficbm.stateChanged.connect(self.setICBMReference)

        self._reference = FileSelectionWidget(parent=self)
        self._reference.setTextLabel('Reference')
        self._reference.filterSisypheVolume()
        self._reference.FieldChanged.connect(self._referenceChanged)
        self._reference.FieldCleared.connect(self._cleared)

        self._filesROI = FilesSelectionWidget(parent=self)
        self._filesROI.setTextLabel('ROI(s)')
        self._filesROI.filterSisypheROI()
        self._filesROI.setVisible(self._title == 'ROI')
        self._filesROI.setMaximumHeight(300)
        self._filesROI.FieldChanged.connect(self._changed)
        self._filesROI.FieldCleared.connect(self._cleared)
        self._filesROI.setEnabled(False)

        self._filesMesh = FilesSelectionWidget(parent=self)
        self._filesMesh.setTextLabel('Mesh(es)')
        self._filesMesh.filterSisypheMesh()
        self._filesMesh.setVisible(self._title == 'Mesh')
        self._filesMesh.setMaximumHeight(300)
        self._filesMesh.FieldChanged.connect(self._changed)
        self._filesMesh.FieldCleared.connect(self._cleared)
        self._filesMesh.setEnabled(False)

        self._filesTools = FilesSelectionWidget(parent=self)
        self._filesTools.setTextLabel('Tool(s)')
        self._filesTools.filterSisypheTools()
        self._filesTools.setVisible(self._title == 'Tools')
        self._filesTools.setMaximumHeight(300)
        self._filesTools.FieldChanged.connect(self._changed)
        self._filesTools.FieldCleared.connect(self._cleared)
        self._filesTools.setEnabled(False)

        self._atlas = QTreeWidget(parent=self)
        self._atlas.setHeaderLabels(['Atlas', 'File'])
        # noinspection PyTypeChecker
        self._atlas.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._atlas.header().setSectionsClickable(False)
        self._atlas.header().setSortIndicatorShown(False)
        self._atlas.header().setStretchLastSection(True)
        self._atlas.setAlternatingRowColors(True)
        self._atlas.setMinimumHeight(400)
        import Sisyphe.templates
        folder = join(dirname(Sisyphe.templates.__file__), 'ICBM152', 'LABELLING', '*{}'.format(SisypheVolume.getFileExt()))
        filenames = glob(folder)
        if len(filenames) > 0:
            for filename in filenames:
                buff = splitext(filename)[0] + '.xlabels'
                if exists(buff):
                    title = splitext(basename(filename))[0].split('_')[-1]
                    if title == '': title = basename(filename)
                    item = QTreeWidgetItem(self._atlas)
                    item.setText(0, title)
                    item.setText(1, basename(filename))
                    # noinspection PyUnresolvedReferences
                    item.setData(0, Qt.UserRole, filename)
                    # noinspection PyUnresolvedReferences
                    item.setCheckState(0, Qt.Unchecked)
                    self._atlas.addTopLevelItem(item)

        self._threshold = LabeledSpinBox(parent=self)
        self._threshold.setTitle('Percent threshold')
        self._threshold.setRange(0, 50)
        self._threshold.setValue(1)
        self._threshold.setSuffix(' %')

        # Main

        btlyout = QHBoxLayout()
        if platform == 'win32': btlyout.setContentsMargins(10, 10, 10, 10)
        btlyout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        btlyout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close')
        self._ok.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setEnabled(False)
        btlyout.addWidget(self._ok)
        btlyout.addWidget(self._execute)
        btlyout.addStretch()
        self._execute.clicked.connect(self.execute)
        self._ok.clicked.connect(self.accept)

        self._layout.addWidget(self._reficbm)
        self._layout.addWidget(self._reference)
        self._layout.addWidget(self._filesROI)
        self._layout.addWidget(self._filesMesh)
        self._layout.addWidget(self._filesTools)
        self._layout.addWidget(self._atlas)
        self._layout.addWidget(self._threshold)
        self._layout.addLayout(btlyout)

        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        self._filesROI.setMinimumWidth(int(screen.width() * 0.33))
        self._filesMesh.setMinimumWidth(int(screen.width() * 0.33))
        self._filesTools.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)
        self._center()

    # Private methods

    def _center(self):
        self.show()
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _referenceChanged(self):
        if self._reference.isEmpty(): self._referenceCleared()
        else:
            if self._title == 'ROI' and not self._filesROI.isEmpty(): self._execute.setEnabled(True)
            elif self._title == 'Mesh' and not self._filesMesh.isEmpty(): self._execute.setEnabled(True)
            elif self._title == 'Tools' and not self._filesTools.isEmpty(): self._execute.setEnabled(True)
            else: self._execute.setEnabled(False)
            self._filesROI.clearall()
            self._filesMesh.clearall()
            self._filesTools.clearall()
            self._filesROI.setEnabled(True)
            self._filesMesh.setEnabled(True)
            self._filesTools.setEnabled(True)
            refid = SisypheVolume.getVolumeAttribute(self._reference.getFilename(), 'id')
            self._filesROI.filterSameID(refid)
            self._filesMesh.filterSameID(refid)
            self._filesTools.filterSameID(refid)

    def _referenceCleared(self):
        self._execute.setEnabled(False)
        if not self._reficbm.isChecked():
            self._filesROI.setEnabled(False)
            self._filesMesh.setEnabled(False)
            self._filesTools.setEnabled(False)

    def _changed(self):
        if not self._reference.isEmpty():
            if self._title == 'ROI': self._execute.setEnabled(not self._filesROI.isEmpty())
            elif self._title == 'Mesh': self._execute.setEnabled(not self._filesMesh.isEmpty())
            elif self._title == 'Tools': self._execute.setEnabled(not self._filesTools.isEmpty())
        else: self._execute.setEnabled(False)

    def _cleared(self):
        self._execute.setEnabled(False)

    # Public methods

    def getFilesSelectionWidgets(self):
        return self._reference, self._filesROI, self._filesMesh, self._filesTools

    def setICBMReference(self, icbm: bool):
        self._reficbm.setChecked(icbm)
        self._reference.setVisible(not icbm)
        self._filesROI.clearall()
        self._filesMesh.clearall()
        self._filesTools.clearall()
        if icbm:
            self._filesROI.filterSameID(getID_ICBM152())
            self._filesMesh.filterSameID(getID_ICBM152())
            self._filesTools.filterSameID(getID_ICBM152())

    def setReference(self,
                     vol: str | SisypheVolume,
                     hide: bool = True):
        if isinstance(vol, SisypheVolume): vol = vol.getFilename()
        if isinstance(vol, str):
            self._reference.open(vol)
            hide = not hide
            self._filesROI.setVisible(hide)
            self._filesMesh.setVisible(hide)
            self._filesTools.setVisible(hide)
            self._reference.setVisible(hide)
            self._reficbm.setVisible(hide)
            vid = SisypheVolume.getVolumeAttribute(vol, 'id')
            self._filesROI.filterSameID(vid)
            self._filesMesh.filterSameID(vid)
            self._filesTools.filterSameID(vid)
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(vol)))

    def addROI(self,
               roi: str | list[str] | SisypheROI,
               hide: bool = True) -> None:
        if isinstance(roi, SisypheROI): roi = [roi.getFilename()]
        elif isinstance(roi, str): roi = [roi]
        if isinstance(roi, list):
            self._filesROI.add(roi)
            hide = not hide
            self._filesROI.setVisible(hide)
            self._filesMesh.setVisible(hide)
            self._filesTools.setVisible(hide)
            self._reference.setVisible(hide)
            self._reficbm.setVisible(hide)
        else: raise TypeError('parameter type {} is not str, list[str] or SisypheROI.'.format(type(roi)))

    def addMesh(self,
                mesh: str | list[str] | SisypheMesh,
                hide: bool = True) -> None:
        if isinstance(mesh, SisypheMesh): mesh = [mesh.getFilename()]
        elif isinstance(mesh, str): mesh = [mesh]
        if isinstance(mesh, list):
            self._filesMesh.add(mesh)
            hide = not hide
            self._filesROI.setVisible(hide)
            self._filesMesh.setVisible(hide)
            self._filesTools.setVisible(hide)
            self._reference.setVisible(hide)
            self._reficbm.setVisible(hide)
        else: raise TypeError('parameter type {} is not str, list[str] or SisypheMesh.'.format(type(mesh)))

    def addTool(self,
                tools: str | list[str] | ToolWidgetCollection | HandleWidget | LineWidget,
                hide: bool = True) -> None:
        if isinstance(tools, (ToolWidgetCollection, HandleWidget, LineWidget)): tools = [tools.getFilename()]
        elif isinstance(tools, str): tools = [tools]
        if isinstance(tools, list):
            self._filesTools.add(tools)
            hide = not hide
            self._filesROI.setVisible(hide)
            self._filesMesh.setVisible(hide)
            self._filesTools.setVisible(hide)
            self._reference.setVisible(hide)
            self._reficbm.setVisible(hide)
        else: raise TypeError('parameter type {} is not str, list[str], '
                              'ToolWidgetCollection, HandleWidget or LineWidget.'.format(type(tools)))

    def roiLabeling(self):
        if not self._filesROI.isEmpty():
            # get atlas filenames
            labels = list()
            labels2 = list()
            for i in range(self._atlas.topLevelItemCount()):
                item = self._atlas.topLevelItem(i)
                # noinspection PyUnresolvedReferences
                if item.checkState(0) == Qt.Checked:
                    # noinspection PyUnresolvedReferences
                    labels.append(item.data(0, Qt.UserRole))
                    labels2.append(item.text(0))
            if len(labels) > 0:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('{} atlas labeling...'.format(self._title))
                wait.progressVisibilityOn()
                wait.setProgressRange(0,  self._filesROI.filenamesCount() * len(labels))
                trf = None
                if not self._reficbm.isChecked():
                    ref = SisypheVolume()
                    ref.load(self._reference.getFilename())
                    if not ref.acquisition.isICBM152():
                        if ref.hasICBMTransform():
                            trf = ref.getICBMTransform()
                            if trf.isAffine():
                                trf = trf.getInverseTransform()
                                trf.setAttributesFromFixedVolume(ref)
                            else:
                                wait.close()
                                messageBox(self,
                                           'Atlas labeling',
                                           'Reference volume {} spatial normalization is not affine.'
                                           'Please perform an affine spatial normalization before labeling.'.format(ref.getBasename()))
                                self.reject()
                        else:
                            wait.close()
                            messageBox(self,
                                       'Atlas labeling',
                                       'Reference volume {} has never been normalized in the ICBM space.'
                                       'Please perform an affine spatial normalization before labeling.'.format(ref.getBasename()))
                            self.reject()
                r = dict()
                nrows = dict()
                for k, label in enumerate(labels):
                    r[labels2[k]] = dict()
                    nrows[labels2[k]] = 0
                    atlas = SisypheVolume()
                    atlas.load(label)
                    # atlas resampling in ROI space
                    if trf:
                        f = SisypheApplyTransform()
                        f.setInterpolator('nearest')
                        f.setTransform(trf)
                        f.setMoving(atlas)
                        ratlas = f.execute(save=False, wait=wait)
                    else: ratlas = atlas
                    ratlas.setDefaultOrigin()
                    for filename in self._filesROI.getFilenames():
                        roi = SisypheROI()
                        roi.load(filename)
                        img = ratlas.getSITKImage()
                        imglbl = img * Cast(roi.getSITKImage(), img.GetPixelIDValue())
                        nplbl = GetArrayViewFromImage(imglbl).flatten()
                        counts = bincount(nplbl)
                        extent = counts[1:].sum()
                        tips = dict()
                        if len(counts) > 0:
                            for i in range(1, len(counts)):
                                if counts[i] > 0:
                                    value = counts[i] / extent
                                    if value in tips: value += 0.01
                                    tips[round(value * 100.0, 1)] = atlas.acquisition.getLabel(i)
                        if len(tips) > nrows[labels2[k]]: nrows[labels2[k]] = len(tips)
                        if len(tips) > 0:
                            tips = dict(sorted(tips.items(), reverse=True))
                        # < Revision 16/02/2026
                        # r[labels2[k]][roi.getName()] = tips
                        r[labels2[k]][roi.getName()] = ['{}% {}'.format(k, tips[k]) for k in tips if k > self._threshold.value()]
                        # Revision 16/02/2026 >
                        wait.incCurrentProgressValue()
                wait.close()
                # Display labeling result
                dialog = DialogGenericResults()
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                for label in labels2:
                    tab = dialog.newTab(label, capture=False, clipbrd=False, dataset=True)
                    for k in r[label]:
                        if len(r[label][k]) < nrows[label]:
                            r[label][k] += [''] * (nrows[label] - len(r[label][k]))
                    # noinspection PyUnresolvedReferences
                    dialog.setTreeWidgetDict(tab, r[label], align=Qt.AlignLeft)
                self.hide()
                screen = QApplication.primaryScreen().geometry()
                dialog.setMinimumWidth(int(screen.width() * 0.33))
                dialog.exec()
                return False
            else:
                messageBox(self,
                           'Atlas labeling',
                           'No atlas is selected.')
                return True
        return False

    def meshLabeling(self):
        if not self._filesMesh.isEmpty():
            # get atlas filenames
            labels = list()
            for i in range(self._atlas.topLevelItemCount()):
                item = self._atlas.topLevelItem(i)
                # noinspection PyUnresolvedReferences
                if item.checkState(0) == Qt.Checked:
                    # noinspection PyUnresolvedReferences
                    labels.append(item.data(0, Qt.UserRole))
            if len(labels) > 0:
                n = self._filesMesh.filenamesCount()
                wait = DialogWait()
                wait.open()
                wait.setInformationText('')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.setInformationText('Mesh to ROI conversion...')
                if self._reficbm.isChecked(): ref = 'icbm'
                else:
                    ref = SisypheVolume()
                    ref.load(self._reference.getFilename())
                for filename in self._filesMesh.getFilenames():
                    wait.addInformationText(basename(filename))
                    mesh = SisypheMesh()
                    mesh.load(filename)
                    roiname = splitext(filename)[0] + SisypheROI.getFileExt()
                    if exists(roiname):
                        roi = SisypheROI()
                        roi.load(roiname)
                    else:
                        roi = mesh.convertToSisypheROI(ref)
                        roi.save()
                    self._filesROI.add(roi.getFilename())
                    wait.incCurrentProgressValue()
                wait.close()
                self.roiLabeling()
                return False
            else:
                messageBox(self,
                           'Atlas labeling',
                           'No atlas is selected.')
                return True
        return False

    def toolLabeling(self):
        if not self._filesTools.isEmpty():
            labels = list()
            labels2 = list()
            for i in range(self._atlas.topLevelItemCount()):
                item = self._atlas.topLevelItem(i)
                # noinspection PyUnresolvedReferences
                if item.checkState(0) == Qt.Checked:
                    # noinspection PyUnresolvedReferences
                    labels.append(item.data(0, Qt.UserRole))
                    labels2.append(item.text(0))
            if len(labels) > 0:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('{} atlas labeling...'.format(self._title))
                wait.setProgressRange(0, self._filesTools.filenamesCount() * len(labels))
                wait.setProgressVisibility(wait.getProgressMaximum() > 1)
                if not self._reficbm.isChecked():
                    ref = SisypheVolume()
                    ref.load(self._reference.getFilename())
                    if not ref.acquisition.isICBM152():
                        if not ref.hasICBMTransform():
                            wait.close()
                            messageBox(self,
                                       'Atlas labeling',
                                       'Reference volume {} has never been normalized in the ICBM space.'
                                       'Please perform a spatial normalization before labeling.'.format(ref.getBasename()))
                            self.reject()
                r = dict()
                pos = dict()
                for filename in self._filesTools.getFilenames():
                    ext = splitext(filename)[1]
                    items = list()
                    if ext == '.xpoint':
                        tool = HandleWidget('')
                        tool.load(filename)
                        if self._reficbm.isChecked(): p = tool.getPosition()
                        else:
                            # noinspection PyUnboundLocalVariable
                            p = ref.getICBMfromWorld(tool.getPosition())
                        items.append((p, tool))
                    elif ext == '.xline':
                        tool = LineWidget('')
                        tool.load(filename)
                        if self._reficbm.isChecked(): p = tool.getPosition2()
                        else: p = ref.getICBMfromWorld(tool.getPosition2())
                        items.append((p, tool))
                    elif ext == '.xtools':
                        tools = ToolWidgetCollection()
                        tools.load(filename)
                        for tool in tools:
                            if isinstance(tool, HandleWidget):
                                if self._reficbm.isChecked(): p = tool.getPosition()
                                else: p = ref.getICBMfromWorld(tool.getPosition())
                            elif isinstance(tool, LineWidget):
                                if self._reficbm.isChecked(): p = tool.getPosition2()
                                else: p = ref.getICBMfromWorld(tool.getPosition2())
                            # noinspection PyUnboundLocalVariable
                            items.append((p, tool))
                    if len(items) > 0:
                        for item in items:
                            p = item[0]
                            tool = item[1]
                            key = '{}|{}'.format(basename(filename), tool.getName())
                            r[key] = dict()
                            for k, label in enumerate(labels):
                                atlas = SisypheVolume()
                                atlas.load(label)
                                # noinspection PyUnboundLocalVariable
                                r[key][labels2[k]] = atlas.acquisition.getLabel(atlas[int(p[0]), int(p[1]), int(p[2])])
                            pos[key] = [p[0] - 98.0, p[1] - 134.0, p[2] - 72.0]
                    wait.incCurrentProgressValue()
                wait.close()
                # Display labeling result
                dialog = DialogGenericResults()
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.newTab('Tools atlas labeling', capture=False, clipbrd=False, dataset=True)
                labels2 = ['Tool', 'ICBM X', 'ICBM Y', 'ICBM Z'] + labels2
                dialog.setTreeWidgetHeaderLabels(0, labels2)
                for k in r:
                    row = [k.split('|')[1],
                           round(pos[k][0], 1),
                           round(pos[k][1], 1),
                           round(pos[k][2], 1)]
                    for k2 in r[k]:
                        row.append(r[k][k2])
                    dialog.addTreeWidgetRow(0, row)
                self.hide()
                screen = QApplication.primaryScreen().geometry()
                dialog.setMinimumWidth(int(screen.width() * 0.33))
                dialog.exec()
                return False
            else:
                messageBox(self,
                           'Atlas labeling',
                           'No atlas is selected.')
                return True
        return False

    def execute(self):
        if self._title == 'ROI':
            if self.roiLabeling():
                self.show()
                return
        elif self._title == 'Mesh':
            if self.meshLabeling():
                self.show()
                return
        else:
            if self.toolLabeling():
                self.show()
                return
        if self._reficbm.isVisible():
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform another atlas labeling ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._filesROI.clearall()
                self._filesMesh.clearall()
                self._filesTools.clearall()
            else: self.accept()
        else: self.accept()
