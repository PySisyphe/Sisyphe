"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import sitkVectorFloat64
from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheTransforms
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogResample']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogResample
"""


class DialogResample(QDialog):
    """
    DialogResample

    Description
    ~~~~~~~~~~~

    GUI dialog for volume resampling.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogResample
    """

    # Special method

    """
    Private attributes

    _moving         FileSelectionWidget
    _selftrf        QCheckBox
    _freetrf        QCheckBox
    _settings       FunctionSettingsWidget
    _list           QComboBox, list of geometric transformations
    _trfpreview     QTextEdit
    _trf            SisypheTransform
    _trfs           SisypheTransforms
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Resample')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._strf = None
        self._ftrf = SisypheTransform()
        self._ftrf.setSize([256, 256, 256])
        self._ftrf.setSpacing([1.0, 1.0, 1.0])
        self._trfs = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self.setLayout(self._layout)

        # Init widgets

        self._moving = FileSelectionWidget()
        self._moving.setTextLabel('Moving volume')
        self._moving.filterSisypheVolume()
        self._moving.setCurrentVolumeButtonVisibility(True)
        self._moving.FieldChanged.connect(self._updateMoving)
        self._layout.addWidget(self._moving)

        self._selftrf = QRadioButton('Self geometric transform')
        self._selftrf.setChecked(True)
        self._selftrf.setAutoExclusive(True)
        # noinspection PyUnresolvedReferences
        self._selftrf.toggled.connect(self._updateVisible)
        # noinspection PyUnresolvedReferences
        self._selftrf.toggled.connect(self._center)
        self._freetrf = QRadioButton('Free geometric transform')
        self._freetrf.setAutoExclusive(True)
        # noinspection PyUnresolvedReferences
        self._freetrf.toggled.connect(self._updateVisible)
        # noinspection PyUnresolvedReferences
        self._freetrf.toggled.connect(self._center)
        lyout = QHBoxLayout()
        lyout.addStretch()
        lyout.addWidget(self._selftrf)
        lyout.addWidget(self._freetrf)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        self._list = LabeledComboBox('Transformations', fontsize=13)
        self._list.setMinimumWidth(400)
        # noinspection PyUnresolvedReferences
        self._list.currentIndexChanged.connect(self._transformChanged)
        self._fixed = QPushButton('Get fixed volume')
        # noinspection PyUnresolvedReferences
        self._fixed.pressed.connect(self._getFixedID)
        self._layout.addWidget(self._list)
        self._layout.addWidget(self._fixed)
        self._layout.setAlignment(self._fixed, Qt.AlignCenter)

        self._sizex = QSpinBox()
        self._sizey = QSpinBox()
        self._sizez = QSpinBox()
        self._sizex.setAlignment(Qt.AlignCenter)
        self._sizey.setAlignment(Qt.AlignCenter)
        self._sizez.setAlignment(Qt.AlignCenter)
        self._sizex.setFixedWidth(100)
        self._sizey.setFixedWidth(100)
        self._sizez.setFixedWidth(100)
        self._sizex.setRange(10, 1024)
        self._sizey.setRange(10, 1024)
        self._sizez.setRange(10, 1024)
        self._sizex.setValue(256)
        self._sizey.setValue(256)
        self._sizez.setValue(256)
        # noinspection PyUnresolvedReferences
        self._sizex.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._sizey.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._sizez.valueChanged.connect(self._updateValues)
        self._label1 = QLabel('Size')
        lyout = QHBoxLayout()
        lyout.addStretch()
        lyout.addWidget(self._sizex)
        lyout.addWidget(self._sizey)
        lyout.addWidget(self._sizez)
        lyout.addStretch()
        flyout = QFormLayout()
        flyout.addRow(self._label1, lyout)

        self._spacex = QDoubleSpinBox()
        self._spacey = QDoubleSpinBox()
        self._spacez = QDoubleSpinBox()
        self._spacex.setAlignment(Qt.AlignCenter)
        self._spacey.setAlignment(Qt.AlignCenter)
        self._spacez.setAlignment(Qt.AlignCenter)
        self._spacex.setFixedWidth(100)
        self._spacey.setFixedWidth(100)
        self._spacez.setFixedWidth(100)
        self._spacex.setDecimals(2)
        self._spacey.setDecimals(2)
        self._spacez.setDecimals(2)
        self._spacex.setSingleStep(0.1)
        self._spacey.setSingleStep(0.1)
        self._spacez.setSingleStep(0.1)
        self._spacex.setRange(0.1, 10.0)
        self._spacey.setRange(0.1, 10.0)
        self._spacez.setRange(0.1, 10.0)
        self._spacex.setValue(1.0)
        self._spacey.setValue(1.0)
        self._spacez.setValue(1.0)
        # noinspection PyUnresolvedReferences
        self._spacex.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._spacey.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._spacez.valueChanged.connect(self._updateValues)
        self._label2 = QLabel('Spacing')
        lyout = QHBoxLayout()
        lyout.addStretch()
        lyout.addWidget(self._spacex)
        lyout.addWidget(self._spacey)
        lyout.addWidget(self._spacez)
        lyout.addStretch()
        flyout.addRow(self._label2, lyout)
        self._layout.addLayout(flyout)

        self._fixed2 = QPushButton('From volume')
        self._fixed2.setToolTip('Get resampling field of view from selected volume,\n'
                                'and align center of the moving volumes')
        self._fixed2.setFixedWidth(200)
        # noinspection PyUnresolvedReferences
        self._fixed2.pressed.connect(self._updateGeometryFromVolume)
        self._layout.addWidget(self._fixed2)
        self._layout.setAlignment(self._fixed2, Qt.AlignHCenter)

        self._transx = QDoubleSpinBox()
        self._transy = QDoubleSpinBox()
        self._transz = QDoubleSpinBox()
        self._transx.setAlignment(Qt.AlignCenter)
        self._transy.setAlignment(Qt.AlignCenter)
        self._transz.setAlignment(Qt.AlignCenter)
        self._transx.setDecimals(2)
        self._transy.setDecimals(2)
        self._transz.setDecimals(2)
        self._transx.setSingleStep(0.1)
        self._transy.setSingleStep(0.1)
        self._transz.setSingleStep(0.1)
        self._transx.setFixedWidth(100)
        self._transy.setFixedWidth(100)
        self._transz.setFixedWidth(100)
        self._transx.setRange(-256.0, 256.0)
        self._transy.setRange(-256.0, 256.0)
        self._transz.setRange(-256.0, 256.0)
        self._transx.setValue(0.0)
        self._transy.setValue(0.0)
        self._transz.setValue(0.0)
        # noinspection PyUnresolvedReferences
        self._transx.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._transy.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._transz.valueChanged.connect(self._updateValues)
        self._label3 = QLabel('Translations (mm)')
        lyout = QHBoxLayout()
        lyout.addStretch()
        lyout.addWidget(self._transx)
        lyout.addWidget(self._transy)
        lyout.addWidget(self._transz)
        lyout.addStretch()
        flyout = QFormLayout()
        flyout.addRow(self._label3, lyout)
        self._layout.addLayout(flyout)

        self._rotx = QDoubleSpinBox()
        self._roty = QDoubleSpinBox()
        self._rotz = QDoubleSpinBox()
        self._rotx.setAlignment(Qt.AlignCenter)
        self._roty.setAlignment(Qt.AlignCenter)
        self._rotz.setAlignment(Qt.AlignCenter)
        self._rotx.setDecimals(2)
        self._roty.setDecimals(2)
        self._rotz.setDecimals(2)
        self._rotx.setSingleStep(0.1)
        self._roty.setSingleStep(0.1)
        self._rotz.setSingleStep(0.1)
        self._rotx.setFixedWidth(100)
        self._roty.setFixedWidth(100)
        self._rotz.setFixedWidth(100)
        self._rotx.setRange(-180.0, 180.0)
        self._roty.setRange(-180.0, 180.0)
        self._rotz.setRange(-180.0, 180.0)
        self._rotx.setValue(0.0)
        self._roty.setValue(0.0)
        self._rotz.setValue(0.0)
        # noinspection PyUnresolvedReferences
        self._rotx.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._roty.valueChanged.connect(self._updateValues)
        # noinspection PyUnresolvedReferences
        self._rotz.valueChanged.connect(self._updateValues)
        self._label4 = QLabel('Rotations (°)')
        lyout = QHBoxLayout()
        lyout.addStretch()
        lyout.addWidget(self._rotx)
        lyout.addWidget(self._roty)
        lyout.addWidget(self._rotz)
        lyout.addStretch()
        flyout.addRow(self._label4, lyout)
        self._layout.addLayout(flyout)

        # < Revision 11/06/2025
        self._label3.adjustSize()
        self._label1.setMinimumWidth(self._label3.width())
        self._label2.setMinimumWidth(self._label3.width())
        # Revision 11/06/2025 >

        self._field = FileSelectionWidget()
        self._field.setTextLabel('Displacement field')
        self._field.filterDisplacementField()
        self._layout.addWidget(self._field)
        self._field.FieldChanged.connect(self._loadField)

        self._load = MenuPushButton('Load')
        self._load.setToolTip('Load a geometric transformation')
        self._load.addAction('PySisyphe transform (*.xtrf)')
        self._load.addAction('ANTs transform (*.mat)')
        self._load.addAction('ITK transform (*.tfm)')
        self._load.addAction('MINC transform (*.xfm)')
        self._load.addAction('Matlab transform (*.mat)')
        self._load.addAction('Text transform (*.txt)')
        # noinspection PyUnresolvedReferences
        self._load.getPopupMenu().triggered.connect(self._loadTransform)

        # < Revision 11/06/2025
        self._load2 = MenuPushButton('Load transforms')
        self._load2.setToolTip('Load a collection of geometric transformations\n'
                               'with the same space (same ID) as the moving volume')
        self._load2.addAction('PySisyphe transforms (*.xtrfs)')
        self._load2.addAction('PySisyphe transforms from volume (*.xvol)')
        # noinspection PyUnresolvedReferences
        self._load2.getPopupMenu().triggered.connect(self._loadTransforms)
        # Revision 11/06/2025 >

        self._save = MenuPushButton('Save')
        # self._save.setFixedWidth(60)
        self._save.setToolTip('Save geometric transformation')
        self._save.addAction('PySisyphe transform (*.xtrf)')
        self._save.addAction('ANTs transform (*.mat)')
        self._save.addAction('ITK transform (*.tfm)')
        self._save.addAction('MINC transform (*.xfm)')
        self._save.addAction('Matlab transform (*.mat)')
        self._save.addAction('Text transform (*.txt)')
        # noinspection PyUnresolvedReferences
        self._save.getPopupMenu().triggered.connect(self._saveTransform)
        self._field2 = QPushButton('Affine to displacement field')
        # noinspection PyUnresolvedReferences
        self._field2.pressed.connect(self._affineToDisplacementField)
        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.addWidget(self._load)
        lyout.addWidget(self._load2)
        lyout.addWidget(self._save)
        lyout.addWidget(self._field2)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        self._trfpreview = QTextEdit()
        self._trfpreview.setReadOnly(True)
        self._trfpreview.setMinimumHeight(280)
        self._layout.addWidget(self._trfpreview)

        self._settings = FunctionSettingsWidget('Resample')
        self._settings.setParameterVisibility('NormalizationPrefix', False)
        self._settings.setParameterVisibility('NormalizationSuffix', False)
        self._settings.VisibilityToggled.connect(self._center)
        self._layout.addWidget(self._settings)

        self._list.setEnabled(False)
        self._fixed.setEnabled(False)
        self._sizex.setEnabled(False)
        self._sizey.setEnabled(False)
        self._sizez.setEnabled(False)
        self._spacex.setEnabled(False)
        self._spacey.setEnabled(False)
        self._spacez.setEnabled(False)
        self._transx.setEnabled(False)
        self._transy.setEnabled(False)
        self._transz.setEnabled(False)
        self._rotx.setEnabled(False)
        self._roty.setEnabled(False)
        self._rotz.setEnabled(False)
        self._fixed2.setEnabled(False)
        self._field.setEnabled(False)
        self._field2.setEnabled(False)
        self._load.setEnabled(False)
        # < Revision 11/06/2025
        self._load2.setEnabled(False)
        # Revision 11/06/2025 >
        self._save.setEnabled(False)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Resample')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Resample moving volume')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        self._updateVisible(True)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 11/06/2025
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        self._moving.setMinimumWidth(int(screen.width() * 0.33))
        self.setModal(True)
        # Revision 11/06/2025 >

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateMoving(self):
        if not self._moving.isEmpty():
            filename = self._moving.getFilename()
            if self._selftrf.isChecked():
                if exists(filename):
                    v = SisypheVolume()
                    v.load(filename)
                    self._trfs = v.getTransforms()
                    # < Revision 03/09/2024
                    # add self._list.blockSignals(True)
                    self._list.blockSignals(True)
                    # Revision 03/09/2024 >
                    self._list.clear()
                    if len(self._trfs) > 0:
                        for trf in self._trfs:
                            self._list.addItem(trf.getID())
                        self._list.setCurrentIndex(0)
                        self._strf = self._trfs[0]
                    else: self._strf = None
                    self._trfpreview.clear()
                    self._trfpreview.append(str(self._strf))
                    # < Revision 03/09/2024
                    # add self._list.blockSignals(False)
                    self._list.blockSignals(False)
                    # Revision 03/09/2024 >
        v = not self._moving.isEmpty()
        self._list.setEnabled(v)
        self._fixed.setEnabled(v)
        self._sizex.setEnabled(v)
        self._sizey.setEnabled(v)
        self._sizez.setEnabled(v)
        self._spacex.setEnabled(v)
        self._spacey.setEnabled(v)
        self._spacez.setEnabled(v)
        self._transx.setEnabled(v)
        self._transy.setEnabled(v)
        self._transz.setEnabled(v)
        self._rotx.setEnabled(v)
        self._roty.setEnabled(v)
        self._rotz.setEnabled(v)
        self._fixed2.setEnabled(v)
        self._field.setEnabled(v)
        self._field2.setEnabled(v)
        self._load.setEnabled(v)
        # < Revision 114/06/2025
        self._load2.setEnabled(v)
        # Revision 114/06/2025 >
        self._save.setEnabled(v)
        self._execute.setEnabled(v)

    # noinspection PyUnusedLocal
    def _updateVisible(self, v):
        self._trfpreview.clear()
        v = self._selftrf.isChecked()
        self._list.setVisible(v)
        self._fixed.setVisible(v)
        if v:
            if self._trfs is not None:
                if len(self._trfs) > 0:
                    index = self._list.currentIndex()
                    self._strf = self._trfs[index]
                    self._trfpreview.clear()
                    self._trfpreview.append(str(self._strf))
                else: self._strf = None
        v = not v
        e = not (self._ftrf is not None and self._ftrf.isDisplacementField())
        self._sizex.setVisible(v)
        self._sizey.setVisible(v)
        self._sizez.setVisible(v)
        self._spacex.setVisible(v)
        self._spacey.setVisible(v)
        self._spacez.setVisible(v)
        self._transx.setVisible(v and e)
        self._transy.setVisible(v and e)
        self._transz.setVisible(v and e)
        self._rotx.setVisible(v and e)
        self._roty.setVisible(v and e)
        self._rotz.setVisible(v and e)
        self._label1.setVisible(v)
        self._label2.setVisible(v)
        self._label3.setVisible(v and e)
        self._label4.setVisible(v and e)
        self._fixed2.setVisible(v and e)
        self._field.setVisible(v)
        self._load.setVisible(v)
        # < Revision 11/06/2025
        self._load2.setVisible(not v)
        # Revision 11/06/2025 >

        self._sizex.setEnabled(e)
        self._sizey.setEnabled(e)
        self._sizez.setEnabled(e)
        self._spacex.setEnabled(e)
        self._spacey.setEnabled(e)
        self._spacez.setEnabled(e)
        if v:
            self._trfpreview.append(str(self._ftrf))

    def _transformChanged(self, index):
        self._strf = self._trfs[index]
        self._trfpreview.clear()
        self._trfpreview.append(str(self._strf))

    # noinspection PyUnusedLocal
    def _updateValues(self, v):
        sizex = self._sizex.value()
        sizey = self._sizey.value()
        sizez = self._sizez.value()
        spacex = self._spacex.value()
        spacey = self._spacey.value()
        spacez = self._spacez.value()
        self._ftrf.setSize([sizex, sizey, sizez])
        self._ftrf.setSpacing([spacex, spacey, spacez])
        if not self._ftrf.isDisplacementField():
            transx = self._transx.value()
            transy = self._transy.value()
            transz = self._transz.value()
            rotx = self._rotx.value()
            roty = self._roty.value()
            rotz = self._rotz.value()
            self._ftrf.setTranslations([transx, transy, transz])
            self._ftrf.setRotations([rotx, roty, rotz], deg=True)
        self._trfpreview.clear()
        self._trfpreview.append(str(self._ftrf))

    def _updateGeometryFromVolume(self):
        filename = QFileDialog.getOpenFileName(None, 'Get geometry from volume', getcwd(),
                                               filter='PySisyphe volume (*.xvol)')[0]
        QApplication.processEvents()
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            v = SisypheVolume()
            v.load(filename)
            size = v.getSize()
            spacing = v.getSpacing()
            self._sizex.setValue(size[0])
            self._sizey.setValue(size[1])
            self._sizez.setValue(size[2])
            self._spacex.setValue(spacing[0])
            self._spacey.setValue(spacing[1])
            self._spacez.setValue(spacing[2])
            self._ftrf.setID(v.getID())
            self._ftrf.setSize(size)
            self._ftrf.setSpacing(spacing)
            if not self._moving.isEmpty():
                moving = self._moving.getVolume()
                if not moving.isDefaultOrigin() and not v.isDefaultOrigin():
                    r = messageBox(self,
                                   title=self.windowTitle(),
                                   text='Do you want to align origins ?',
                                   icon=QMessageBox.Question,
                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                   default=QMessageBox.No)
                    if r == QMessageBox.Yes:
                        cv = v.getOrigin()
                        co = moving.getOrigin()
                        t = (cv[0] - co[0], cv[1] - co[1], cv[2] - co[2])
                        self._transx.setValue(t[0])
                        self._transy.setValue(t[1])
                        self._transz.setValue(t[2])
                        self._ftrf.setTranslations(t)
                else:
                    r = messageBox(self,
                                   title=self.windowTitle(),
                                   text='Do you want to align image centers ?',
                                   icon=QMessageBox.Question,
                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                   default=QMessageBox.No)
                    if r == QMessageBox.Yes:
                        cv = v.getCenter()
                        co = moving.getCenter()
                        t = (cv[0]-co[0], cv[1]-co[1], cv[2]-co[2])
                        self._transx.setValue(t[0])
                        self._transy.setValue(t[1])
                        self._transz.setValue(t[2])
                        self._ftrf.setTranslations(t)
            self._trfpreview.clear()
            self._trfpreview.append(str(self._ftrf))

    # noinspection PyUnusedLocal
    def _updateDisplacement(self, v):
        filename = self._field.getFilename()
        if exists(filename):
            v = SisypheVolume()
            v.load(filename)
            self._ftrf.setSITKDisplacementFieldImage(v.getSITKImage())
            self._trfpreview.clear()
            self._trfpreview.append(str(self._ftrfs))

    def _getFixedID(self):
        if self._strf is not None:
            filename = QFileDialog.getOpenFileName(None, 'Get volume ID', getcwd(),
                                                   filter='PySisyphe volume (*.xvol)')[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                v = SisypheVolume()
                v.load(filename)
                ID = v.getID()
                if ID in self._trfs:
                    self._list.setCurrentText(ID)
                    self._strf = self._trfs[ID]
                    self._trfpreview.clear()
                    self._trfpreview.append('Transformation of {} to {}'.format(self._moving.getBasename(),
                                                                                v.getBasename()))
                    self._trfpreview.append(str(self._strf))
                else:
                    messageBox(self,
                               title=self.windowTitle(),
                               text='{} is not registered to {}'.format(v.getBasename(),
                                                                        self._moving.getBasename()),
                               icon=QMessageBox.Information)

    def _affineToDisplacementField(self):
        if self._freetrf.isChecked():
            if self._ftrf.isAffine():
                self._ftrf.affineToDisplacementField()
                self._trfpreview.clear()
                self._trfpreview.append(str(self._ftrf))
        else:
            if self._strf is not None:
                if self._strf.isAffine():
                    self._strf.affineToDisplacementField()
                    self._trfpreview.clear()
                    self._trfpreview.append(str(self._strf))

    def _loadField(self):
        self._ftrf = SisypheTransform()
        if not self._field.isEmpty():
            field = SisypheVolume()
            field.load(self._field.getFilename())
            if (field.getNumberOfComponentsPerPixel() == 3 and
                    field.isFloatDatatype() and
                    field.getAcquisition().isDisplacementField()):
                self._ftrf.setSITKDisplacementFieldImage(Cast(field.getSITKImage(), sitkVectorFloat64))
                size = field.getSize()
                spacing = field.getSpacing()
                self._sizex.blockSignals(True)
                self._sizey.blockSignals(True)
                self._sizez.blockSignals(True)
                self._spacex.blockSignals(True)
                self._spacey.blockSignals(True)
                self._spacez.blockSignals(True)
                self._sizex.setValue(size[0])
                self._sizey.setValue(size[1])
                self._sizez.setValue(size[2])
                self._spacex.setValue(spacing[0])
                self._spacey.setValue(spacing[0])
                self._spacez.setValue(spacing[0])
                self._sizex.blockSignals(False)
                self._sizey.blockSignals(False)
                self._sizez.blockSignals(False)
                self._spacex.blockSignals(False)
                self._spacey.blockSignals(False)
                self._spacez.blockSignals(False)
        else: self._updateValues(None)
        self._updateVisible(False)

    def _loadTransform(self, action):
        flt = action.text()
        filename = QFileDialog.getOpenFileName(self, 'Load geometric transformation...', getcwd(), filter=flt)[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            self._ftrf = SisypheTransform()
            flt = flt[:2]
            try:
                if flt == 'Py': self._ftrf.load(filename)
                elif flt == 'AN': self._ftrf.loadFromANTSTransform(filename)
                elif flt == 'IT': self._ftrf.loadFromTfmTransform(filename)
                elif flt == 'MI': self._ftrf.loadFromXfmTransform(filename)
                elif flt == 'Ma': self._ftrf.loadFromMatfileTransform(filename)
                elif flt == 'Te': self._ftrf.loadFromTxtTransform(filename)
                self._sizex.blockSignals(True)
                self._sizey.blockSignals(True)
                self._sizez.blockSignals(True)
                self._spacex.blockSignals(True)
                self._spacey.blockSignals(True)
                self._spacez.blockSignals(True)
                size = self._ftrf.getSize()
                self._sizex.setValue(size[0])
                self._sizey.setValue(size[1])
                self._sizez.setValue(size[2])
                spacing = self._ftrf.getSpacing()
                self._spacex.setValue(spacing[0])
                self._spacey.setValue(spacing[0])
                self._spacez.setValue(spacing[0])
                self._sizex.blockSignals(False)
                self._sizey.blockSignals(False)
                self._sizez.blockSignals(False)
                self._spacex.blockSignals(False)
                self._spacey.blockSignals(False)
                self._spacez.blockSignals(False)
                self._updateVisible(False)
            except Exception as err:
                messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                self._trf = None

    def _saveTransform(self, action):
        if self._selftrf.isChecked(): trf = self._strf
        else: trf = self._ftrf
        if trf is not None:
            flt = action.text()
            filename = QFileDialog.getSaveFileName(self, 'Save geometric transformation...', getcwd(), filter=flt)[0]
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                flt = flt[:2]
                try:
                    if flt == 'Py': trf.saveAs(filename)
                    elif flt == 'AN': trf.saveToANTSTransform(filename)
                    elif flt == 'IT': trf.saveToTfmTransform(filename)
                    elif flt == 'MI': trf.saveToXfmTransform(filename)
                    elif flt == 'Ma': trf.saveToMatfileTransform(filename)
                    elif flt == 'Te': trf.saveToTxtTransform(filename)
                except Exception as err:
                    QMessageBox(self, title=self.windowTitle(), text='{}'.format(err))

    def _loadTransforms(self, action):
        flt = action.text()
        filename = QFileDialog.getOpenFileName(self, 'Load geometric transformations...', getcwd(), filter=flt)[0]
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            vid = SisypheVolume().getVolumeAttribute(self._moving.getFilename(), 'id')
            flt = flt.split()[-1]
            if flt == '(*.xtrfs)':
                trfs = SisypheTransforms()
                trfs.load(filename)
                if trfs.getReferenceID() != vid:
                    trfs = None
                    messageBox(self,
                               'Load geometric transformations',
                               'ID mismatch between {} and moving volume  {}.'.format(basename(filename),
                                                                                      self._moving.getBasename()))
            elif flt == '(*.xvol)':
                v = SisypheVolume()
                v.load(filename)
                trfs = v.getTransforms()
                if trfs.getReferenceID() != vid:
                    trfs = None
                    messageBox(self,
                               'Load geometric transformations',
                               'ID mismatch between {} and moving volume  {}.'.format(v.getBasename(),
                                                                                      self._moving.getBasename()))
            else: raise ValueError('Invalid action ({})'.format(action.text()))
            if trfs is not None:
                self._selftrf.setChecked(True)
                self._trfs = trfs
                self._list.blockSignals(True)
                self._list.clear()
                if len(self._trfs) > 0:
                    for trf in self._trfs:
                        self._list.addItem(trf.getID())
                    self._list.setCurrentIndex(0)
                    self._strf = self._trfs[0]
                else: self._strf = None
                self._trfpreview.clear()
                self._trfpreview.append(str(self._strf))
                self._list.blockSignals(False)

    # Public method

    def getMovingSelectionWidget(self):
        return self._moving

    def getMoving(self):
        if not self._moving.isEmpty():
            filename = self._moving.getFilename()
            if exists(filename):
                v = SisypheVolume()
                v.load(filename)
                return v
        return None

    def execute(self):
        if self._selftrf.isChecked(): trf = self._strf
        else: trf = self._ftrf
        if trf is not None and not self._moving.isEmpty():
            f = SisypheApplyTransform()
            interpol = self._settings.getParameterValue('Interpolator')
            if interpol == 'Nearest Neighbor': f.setInterpolator(sitkNearestNeighbor)
            elif interpol == 'Linear': f.setInterpolator(sitkLinear)
            elif interpol == 'Bspline': f.setInterpolator(sitkBSpline)
            elif interpol == 'Gaussian': f.setInterpolator(sitkGaussian)
            elif interpol == 'Hamming Sinc': f.setInterpolator(sitkHammingWindowedSinc)
            elif interpol == 'Cosine Sinc': f.setInterpolator(sitkCosineWindowedSinc)
            elif interpol == 'Welch Sinc': f.setInterpolator(sitkWelchWindowedSinc)
            elif interpol == 'Lanczos Sinc': f.setInterpolator(sitkLanczosWindowedSinc)
            elif interpol == 'Blackman Sinc': f.setInterpolator(sitkBlackmanWindowedSinc)
            else: f.setInterpolator(sitkLinear)
            dialog = self._settings.getParameterValue('Dialog')
            prefix = self._settings.getParameterValue('Prefix')
            suffix = self._settings.getParameterValue('Suffix')
            v = self.getMoving()
            if v is not None:
                f.setMoving(v)
                f.setTransform(trf)
                wait = DialogWait(title='Resample')
                wait.open()
                wait.setInformationText('Resample {} ...'.format(self._moving.getBasename()))
                try:
                    f.execute(fixed=None, save=True, dialog=dialog, prefix=prefix, suffix=suffix, wait=wait)
                except Exception as err:
                    messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                wait.close()
            """
            
                Exit
            
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to resample another volume ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._moving.clear()
            else: self.accept()

    def reset(self):
        self._sizex.setValue(256)
        self._sizey.setValue(256)
        self._sizez.setValue(256)
        self._spacex.setValue(1.0)
        self._spacey.setValue(1.0)
        self._spacez.setValue(1.0)
        self._transx.setValue(0.0)
        self._transy.setValue(0.0)
        self._transz.setValue(0.0)
        self._rotx.setValue(0.0)
        self._roty.setValue(0.0)
        self._rotz.setValue(0.0)
        self._ftrf = SisypheTransform()
        self._updateVisible(False)
