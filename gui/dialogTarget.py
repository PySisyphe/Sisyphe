"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from math import pi
from math import sqrt
from math import atan2
from math import acos
from math import degrees

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem

import Sisyphe.widgets as sw
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox

__all__ = ['DialogTarget']

"""
    Class hierarchy

        QDialog -> DialogTarget
        
"""


class DialogTarget(QDialog):
    """
         DialogTarget

         Description

             GUI dialog window for targeting parameters.

         Inheritance

             QDialog -> DialogTarget

         Private attributes

            _views  IconBarViewWidgetCollection
            _tool   NamedWidget

         Public methods

            clear()
            copyFieldsFrom(DialogTarget)
            copyFieldsTo(DialogTarget)
            setDefaultPosition()
            setCursorPosition()
            setAbsolutePosition([float, float, float], bool, bool)
            setEntryPosition([float, float, float])
            updateAbsolutePosition()
            bool = getTargetPosition()
            dict = getTrajectory()
            dict = getAttributes()
            bool = isAbsolutePosition()
            bool = isRelativeOrWeightedPosition()
            bool = isRelativePosition()
            bool = isWeightedPosition()
            setTrajectoryFieldsVisibility(bool)
            bool = getTrajectoryFieldsVisibility()
            showTrajectoryFields()
            hideTrajectoryFields()
            setViewCollection(IconBarViewWidgetCollection)
            IconBarViewWidgetCollection = getViewCollection()
            bool = hasViewCollection()

            inherited QDialog methods

        Revisions:

            07/09/2023  getTargetPosition() method bugfix, replace self._views.getFirstSliceView() with self._views.getVolumeView()
            21/09/2023  isAbsolutePosition() and isRelativePosition() methods bugfix
            28/09/2023  _initPoints() method bugfix
     """

    # Special method

    def __init__(self, tool=None, views=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Target position')

        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: self._views = None

        from Sisyphe.widgets.toolWidgets import HandleWidget
        from Sisyphe.widgets.toolWidgets import LineWidget
        if isinstance(tool, (HandleWidget, LineWidget)): self._tool = tool
        else: self._tool = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init widgets

        self._poscursor = QRadioButton('Cursor position')
        self._poscursor.setChecked(True)
        self._layout.addWidget(self._poscursor)

        # Absolute position

        self._posabs = QRadioButton('Absolute position')
        self._layout.addWidget(self._posabs)

        self._posx = LabeledDoubleSpinBox(title='X', fontsize=14)
        self._posx.setAlignment(Qt.AlignCenter)
        self._posx.setFixedWidth(100)
        self._posx.setDecimals(1)
        self._posx.setSingleStep(1.0)
        self._posx.setRange(0.0, 512.0)
        self._posy = LabeledDoubleSpinBox(title='Y', fontsize=14)
        self._posy.setAlignment(Qt.AlignCenter)
        self._posy.setFixedWidth(100)
        self._posy.setDecimals(1)
        self._posy.setSingleStep(1.0)
        self._posy.setRange(0.0, 512.0)
        self._posz = LabeledDoubleSpinBox(title='Z', fontsize=14)
        self._posz.setAlignment(Qt.AlignCenter)
        self._posz.setFixedWidth(100)
        self._posz.setDecimals(1)
        self._posz.setSingleStep(1.0)
        self._posz.setRange(0.0, 512.0)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._posx)
        lyout.addWidget(self._posy)
        lyout.addWidget(self._posz)
        self._abs = QWidget()
        self._abs.setLayout(lyout)
        self._abs.setEnabled(False)
        self._layout.addWidget(self._abs)
        self._posabs.toggled.connect(self._abs.setEnabled)

        # Leksell absolute position

        self._poslabs = QRadioButton('Leksell absolute position')
        self._layout.addWidget(self._poslabs)

        self._poslx = LabeledDoubleSpinBox(title='X', fontsize=14)
        self._poslx.setAlignment(Qt.AlignCenter)
        self._poslx.setFixedWidth(100)
        self._poslx.setDecimals(1)
        self._poslx.setSingleStep(1.0)
        self._poslx.setRange(0.0, 512.0)
        self._posly = LabeledDoubleSpinBox(title='Y', fontsize=14)
        self._posly.setAlignment(Qt.AlignCenter)
        self._posly.setFixedWidth(100)
        self._posly.setDecimals(1)
        self._posly.setSingleStep(1.0)
        self._posly.setRange(0.0, 512.0)
        self._poslz = LabeledDoubleSpinBox(title='Z', fontsize=14)
        self._poslz.setAlignment(Qt.AlignCenter)
        self._poslz.setFixedWidth(100)
        self._poslz.setDecimals(1)
        self._poslz.setSingleStep(1.0)
        self._poslz.setRange(0.0, 512.0)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._poslx)
        lyout.addWidget(self._posly)
        lyout.addWidget(self._poslz)
        self._labs = QWidget()
        self._labs.setLayout(lyout)
        self._labs.setEnabled(False)
        self._layout.addWidget(self._labs)
        self._poslabs.toggled.connect(self._labs.setEnabled)

        # Mesh center of mass

        self._posmeshes = QRadioButton('Mesh center of mass')
        self._layout.addWidget(self._posmeshes)

        self._meshes = QComboBox()
        self._meshes.setEnabled(False)
        self._layout.addWidget(self._meshes)
        self._posmeshes.toggled.connect(self._meshes.setEnabled)

        # Weighted targets

        self._postargets = QRadioButton('Weighted position')
        self._layout.addWidget(self._postargets)

        self._points = QTreeWidget()
        self._points.setHeaderLabels(['Points          ', 'Relative weights', 'Absolute weights'])
        for i in range(self._points.headerItem().columnCount()):
            self._points.headerItem().setTextAlignment(i, Qt.AlignCenter)
        self._points.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._points.header().setStretchLastSection(False)
        self._points.setAlternatingRowColors(True)
        self._points.setEnabled(False)
        self._layout.addWidget(self._points)
        self._postargets.toggled.connect(self._points.setEnabled)

        # Relative position

        self._posrel = QRadioButton('Relative position')
        self._layout.addWidget(self._posrel)

        self._ref = QComboBox()
        self._ref.setFixedWidth(160)
        self._ap1 = QDoubleSpinBox()
        self._ap1.setAlignment(Qt.AlignCenter)
        self._ap1.setFixedWidth(80)
        self._ap1.setDecimals(1)
        self._ap1.setSingleStep(1.0)
        self._ap1.setValue(0.0)
        self._ap1.setRange(-256.0, 256.0)
        self._ap1.setToolTip('Anterior +, Posterior -')
        self._ap1.valueChanged.connect(self._apChanged)
        self._ap2 = QDoubleSpinBox()
        self._ap2.setAlignment(Qt.AlignCenter)
        self._ap2.setFixedWidth(80)
        self._ap2.setDecimals(2)
        self._ap2.setSingleStep(0.1)
        self._ap2.setValue(0.0)
        self._ap2.setRange(-1.0, 1.0)
        self._ap1.setToolTip('Anterior +, Posterior -')
        self._ap2.valueChanged.connect(self._apChanged)
        self._ap3 = QComboBox()
        self._ap3.currentIndexChanged.connect(self._apChanged)
        self._ap4 = QComboBox()
        self._ap4.currentIndexChanged.connect(self._apChanged)
        self._ap5 = QLineEdit()
        self._ap5.setFixedWidth(80)
        self._ap5.setText('0.0')
        self._ap5.setReadOnly(True)
        self._ap5.setAlignment(Qt.AlignCenter)
        self._lat1 = QDoubleSpinBox()
        self._lat1.setAlignment(Qt.AlignCenter)
        self._lat1.setFixedWidth(80)
        self._lat1.setDecimals(1)
        self._lat1.setSingleStep(1.0)
        self._lat1.setValue(0.0)
        self._lat1.setRange(-256.0, 256.0)
        self._lat1.setToolTip('Right +, Left -')
        self._lat1.valueChanged.connect(self._latChanged)
        self._lat2 = QDoubleSpinBox()
        self._lat2.setAlignment(Qt.AlignCenter)
        self._lat2.setFixedWidth(80)
        self._lat2.setDecimals(2)
        self._lat2.setSingleStep(0.1)
        self._lat2.setValue(0.0)
        self._lat2.setRange(-1.0, 1.0)
        self._lat2.setToolTip('Right +, Left -')
        self._lat2.valueChanged.connect(self._latChanged)
        self._lat3 = QComboBox()
        self._lat3.currentIndexChanged.connect(self._latChanged)
        self._lat4 = QComboBox()
        self._lat4.currentIndexChanged.connect(self._latChanged)
        self._lat5 = QLineEdit()
        self._lat5.setFixedWidth(80)
        self._lat5.setText('0.0')
        self._lat5.setReadOnly(True)
        self._lat5.setAlignment(Qt.AlignCenter)
        self._h1 = QDoubleSpinBox()
        self._h1.setAlignment(Qt.AlignCenter)
        self._h1.setFixedWidth(80)
        self._h1.setDecimals(1)
        self._h1.setSingleStep(1.0)
        self._h1.setValue(0.0)
        self._h1.setRange(-256.0, 256.0)
        self._h1.setToolTip('Top +, Bottom -')
        self._h1.valueChanged.connect(self._hChanged)
        self._h2 = QDoubleSpinBox()
        self._h2.setAlignment(Qt.AlignCenter)
        self._h2.setFixedWidth(80)
        self._h2.setDecimals(2)
        self._h2.setSingleStep(0.1)
        self._h2.setValue(0.0)
        self._h2.setRange(-1.0, 1.0)
        self._h1.setToolTip('Top +, Bottom -')
        self._h2.valueChanged.connect(self._hChanged)
        self._h3 = QComboBox()
        self._h3.currentIndexChanged.connect(self._hChanged)
        self._h4 = QComboBox()
        self._h4.currentIndexChanged.connect(self._hChanged)
        self._h5 = QLineEdit()
        self._h5.setFixedWidth(80)
        self._h5.setText('0.0')
        self._h5.setReadOnly(True)
        self._h5.setAlignment(Qt.AlignCenter)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._ap1)
        lyout.addWidget(QLabel('+'))
        lyout.addWidget(self._ap2)
        lyout.addWidget(QLabel('x distance('))
        lyout.addWidget(self._ap3)
        lyout.addWidget(QLabel(','))
        lyout.addWidget(self._ap4)
        lyout.addWidget(QLabel(') = '))
        lyout.addWidget(self._ap5)
        ap = QWidget()
        ap.setLayout(lyout)

        lyout = QHBoxLayout()
        lyout.setSpacing(5)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._lat1)
        lyout.addWidget(QLabel('+'))
        lyout.addWidget(self._lat2)
        lyout.addWidget(QLabel('x distance('))
        lyout.addWidget(self._lat3)
        lyout.addWidget(QLabel(','))
        lyout.addWidget(self._lat4)
        lyout.addWidget(QLabel(') = '))
        lyout.addWidget(self._lat5)
        lat = QWidget()
        lat.setLayout(lyout)

        lyout = QHBoxLayout()
        lyout.setSpacing(5)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._h1)
        lyout.addWidget(QLabel('+'))
        lyout.addWidget(self._h2)
        lyout.addWidget(QLabel('x distance('))
        lyout.addWidget(self._h3)
        lyout.addWidget(QLabel(','))
        lyout.addWidget(self._h4)
        lyout.addWidget(QLabel(') = '))
        lyout.addWidget(self._h5)
        h = QWidget()
        h.setLayout(lyout)

        lyout = QVBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._ref)
        lyout.addWidget(QLabel('Antero-posterior'))
        lyout.addWidget(ap)
        lyout.addWidget(QLabel('Laterally'))
        lyout.addWidget(lat)
        lyout.addWidget(QLabel('Height'))
        lyout.addWidget(h)
        self._rel = QWidget()
        self._rel.setLayout(lyout)
        self._rel.setEnabled(False)
        self._layout.addWidget(self._rel)
        self._posrel.toggled.connect(self._rel.setEnabled)

        # Trajectory

        self._yangle = LabeledDoubleSpinBox(title='Coronal angle (around y-axis)\n'
                                                  '+ right - left rotation',
                                            titlewidth=200,
                                            fontsize=14)
        self._yangle.setFixedWidth(300)
        self._yangle.setSuffix(' °')
        self._yangle.setDecimals(1)
        self._yangle.setSingleStep(1.0)
        self._yangle.setRange(-90.0, 90.0)
        self._yangle.setValue(0.0)
        self._yangle.valueChanged.connect(self._trajectoryChanged)
        self._xangle = LabeledDoubleSpinBox(title='Sagittal angle (around x-axis)\n'
                                                  '+ backward - forward rotation',
                                            titlewidth=200,
                                            fontsize=14)
        self._xangle.setFixedWidth(300)
        self._xangle.setSuffix(' °')
        self._xangle.setDecimals(1)
        self._xangle.setSingleStep(1.0)
        self._xangle.setRange(-180.0, 180.0)
        self._xangle.setValue(0.0)
        self._xangle.valueChanged.connect(self._trajectoryChanged)
        self._length = LabeledDoubleSpinBox(title='Length', titlewidth=200, fontsize=14)
        self._length.setFixedWidth(300)
        self._length.setSuffix(' mm')
        self._length.setDecimals(1)
        self._length.setSingleStep(1.0)
        self._length.setRange(0.0, 512.0)
        self._length.setValue(50.0)
        self._length.valueChanged.connect(self._trajectoryChanged)

        lyout = QVBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._yangle)
        lyout.addWidget(self._xangle)
        lyout.addWidget(self._length)
        self._trajectory = QWidget()
        self._trajectory.setLayout(lyout)
        self._lbtrajectory = QLabel('Trajectory')
        self._layout.addWidget(self._lbtrajectory)
        self._layout.addWidget(self._trajectory)

        self._posex = LabeledDoubleSpinBox(title='X', fontsize=14)
        self._posex.setAlignment(Qt.AlignCenter)
        self._posex.setFixedWidth(100)
        self._posex.setDecimals(1)
        self._posex.setSingleStep(1.0)
        self._posex.setRange(0.0, 512.0)
        self._posex.valueChanged.connect(self._entryChanged)
        self._posey = LabeledDoubleSpinBox(title='Y', fontsize=14)
        self._posey.setAlignment(Qt.AlignCenter)
        self._posey.setFixedWidth(100)
        self._posey.setDecimals(1)
        self._posey.setSingleStep(1.0)
        self._posey.setRange(0.0, 512.0)
        self._posey.valueChanged.connect(self._entryChanged)
        self._posez = LabeledDoubleSpinBox(title='Z', fontsize=14)
        self._posez.setAlignment(Qt.AlignCenter)
        self._posez.setFixedWidth(100)
        self._posez.setDecimals(1)
        self._posez.setSingleStep(1.0)
        self._posez.setRange(0.0, 512.0)
        self._posez.valueChanged.connect(self._entryChanged)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.setAlignment(Qt.AlignCenter)
        lyout.addWidget(self._posex)
        lyout.addWidget(self._posey)
        lyout.addWidget(self._posez)
        self._entry = QWidget()
        self._entry.setLayout(lyout)
        self._lbentry = QLabel('Absolute entry position')
        self._layout.addWidget(self._lbentry)
        self._layout.addWidget(self._entry)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        lyout.addWidget(self._ok)
        lyout.addWidget(self._cancel)
        lyout.addStretch()
        lyout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self._layout.addLayout(lyout)

        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._btgroup = QButtonGroup()
        self._btgroup.setExclusive(True)
        self._btgroup.addButton(self._poscursor)
        self._btgroup.addButton(self._posabs)
        self._btgroup.addButton(self._poslabs)
        self._btgroup.addButton(self._postargets)
        self._btgroup.addButton(self._posmeshes)
        self._btgroup.addButton(self._posrel)

        # Qt Signals

        self._ok.clicked.connect(self.accept)
        self._cancel.clicked.connect(self.reject)

        if views is not None:
            self._initPoints()
            self._initMeshes()

    # Private methods

    def _pointsToTrajectoryAngles(self):
        p1 = [self._posex.value(), self._posey.value(), self._posez.value()]
        p2 = [self._posx.value(), self._posy.value(), self._posz.value()]
        length = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
        self._xangle.blockSignals(True)
        self._yangle.blockSignals(True)
        self._length.blockSignals(True)
        # Sagittal angle, x rotation
        o = p1[1] - p2[1]  # ∆y
        a = p1[2] - p2[2]  # ∆z
        self._xangle.setValue(degrees(-atan2(o, a)))
        # Coronal angle, y rotation
        o = p1[0] - p2[0]  # ∆x
        self._yangle.setValue(degrees((pi / 2) - acos(o / length)))
        self._length.setValue(length)
        self._xangle.blockSignals(False)
        self._yangle.blockSignals(False)
        self._length.blockSignals(False)

    def _trajectoryAnglesToPoint(self):
        trf = SisypheTransform()
        trf.setCenter((0.0, 0.0, 0.0))
        trf.setTranslations((0.0, 0.0, 0.0))
        trf.setRotations((self._xangle.value(), self._yangle.value(), 0.0), deg=deg)
        p1 = list(trf.applyToPoint([0.0, 0.0, self._length.value()]))
        p2 = [self._posx.value(), self._posy.value(), self._posz.value()]
        p1[0] += p2[0]
        p1[1] += p2[1]
        p1[2] += p2[2]
        self._posex.blockSignals(True)
        self._posey.blockSignals(True)
        self._posez.blockSignals(True)
        self._posex.setValue(p1[0])
        self._posey.setValue(p1[1])
        self._posez.setValue(p1[2])
        self._posex.blockSignals(False)
        self._posey.blockSignals(False)
        self._posez.blockSignals(False)

    def _apChanged(self, d):
        d = 0.0
        if self._ap3.count() > 0 and self._ap4.count() > 0:
            p1 = self._points.topLevelItem(self._ap3.currentIndex()).data(0, Qt.UserRole)
            p2 = self._points.topLevelItem(self._ap4.currentIndex()).data(0, Qt.UserRole)
            if p1 is None or p2 is None: d = 0.0
            else: d = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
        r = self._ap1.value() + self._ap2.value() * d
        self._ap5.setText('{:.1f}'.format(r))

    def _latChanged(self, d):
        d = 0.0
        if self._lat3.count() > 0 and self._lat4.count() > 0:
            p1 = self._points.topLevelItem(self._lat3.currentIndex()).data(0, Qt.UserRole)
            p2 = self._points.topLevelItem(self._lat4.currentIndex()).data(0, Qt.UserRole)
            if p1 is None or p2 is None: d = 0.0
            else: d = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
        r = self._lat1.value() + self._lat2.value() * d
        self._lat5.setText('{:.1f}'.format(r))

    def _hChanged(self, d):
        d = 0.0
        if self._h3.count() > 0 and self._h4.count() > 0:
            p1 = self._points.topLevelItem(self._h3.currentIndex()).data(0, Qt.UserRole)
            p2 = self._points.topLevelItem(self._h4.currentIndex()).data(0, Qt.UserRole)
            if p1 is None or p2 is None: d = 0.0
            else: d = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
        r = self._h1.value() + self._h2.value() * d
        self._h5.setText('{:.1f}'.format(r))

    def _trajectoryChanged(self, d):
        if self._tool is None:
            if self._trajectory.isVisible(): self._trajectoryAnglesToPoint()
        elif isinstance(self._tool, sw.toolWidgets.LineWidget):
            r = [self._xangle.value(), self._yangle.value()]
            self._tool.setTrajectoryAngles(r, self._length.value())
            p = self._tool.getPosition1()
            self._posex.blockSignals(True)
            self._posey.blockSignals(True)
            self._posez.blockSignals(True)
            self._posex.setValue(p[0])
            self._posey.setValue(p[1])
            self._posez.setValue(p[2])
            self._posex.blockSignals(False)
            self._posey.blockSignals(False)
            self._posez.blockSignals(False)

    def _entryChanged(self, d):
        if self._tool is None:
            if self._trajectory.isVisible(): self._pointsToTrajectoryAngles()
        elif isinstance(self._tool, sw.toolWidgets.LineWidget):
            p = [self._posex.value(), self._posey.value(), self._posez.value()]
            self._tool.setPosition1(p)
            r = self._tool.getTrajectoryAngles()
            self._xangle.blockSignals(True)
            self._yangle.blockSignals(True)
            self._length.blockSignals(True)
            self._xangle.setValue(r[0])
            self._yangle.setValue(r[1])
            self._length.setValue(self._tool.getLength())
            self._xangle.blockSignals(False)
            self._yangle.blockSignals(False)
            self._length.blockSignals(False)

    def _editWeight(self, index):
        n = self._points.topLevelItemCount()
        if n > 0:
            wt = 0
            for i in range(n):
                wt += self._points.itemWidget(self._points.topLevelItem(i), 1).value()
            for i in range(n):
                w = self._points.itemWidget(self._points.topLevelItem(i), 1).value()
                if wt == 0.0: r = 0.0
                else: r = w / wt
                self._points.topLevelItem(i).setData(2, Qt.UserRole, r)
                self._points.topLevelItem(i).setText(2, '{:.2f}'.format(r))

    def _initPoints(self):
        row = 0
        weights = dict()
        n = self._points.topLevelItemCount()
        if n > 0:
            for i in range(n):
                item = self._points.topLevelItem(i)
                weights[item.text(0)] = self._points.itemWidget(item, 1).value()
        self._points.clear()
        if self._ref.count() > 0:
            ref = self._ref.currentText()
            self._ref.clear()
        else: ref = ''
        if self._ap3.count() > 0:
            ap3 = self._ap3.currentText()
            self._ap3.clear()
        else: ap3 = ''
        if self._ap4.count() > 0:
            ap4 = self._ap4.currentText()
            self._ap4.clear()
        else: ap4 = ''
        if self._lat3.count() > 0:
            lat3 = self._lat3.currentText()
            self._lat3.clear()
        else: lat3 = ''
        if self._lat4.count() > 0:
            lat4 = self._lat4.currentText()
            self._lat4.clear()
        else: lat4 = ''
        if self._h3.count() > 0:
            h3 = self._h3.currentText()
            self._h3.clear()
        else: h3 = ''
        if self._h4.count() > 0:
            h4 = self._h4.currentText()
            self._h4.clear()
        else: h4 = ''
        self._ref.addItem('No')
        if self.hasViewCollection():
            vol = self._views.getVolume()
            tools = self._views.getToolCollection()
            if vol is not None and tools is not None:
                # Add AC PC points
                if vol.acpc.hasACPC():
                    for acpc in ['AC', 'PC']:
                        item = QTreeWidgetItem(self._points)
                        item.setText(0, acpc)
                        item.setTextAlignment(0, Qt.AlignCenter)
                        if acpc == 'AC': item.setData(0, Qt.UserRole, vol.acpc.getAC())
                        else: item.setData(0, Qt.UserRole, vol.acpc.getPC())
                        edit = QSpinBox()
                        edit.setRange(0, 100)
                        if acpc in weights: edit.setValue(weights[acpc])
                        else: edit.setValue(0)
                        edit.setAlignment(Qt.AlignCenter)
                        edit.valueChanged.connect(self._editWeight)
                        item.setData(2, Qt.UserRole, 0.0)
                        item.setText(2, '0.0')
                        item.setTextAlignment(2, Qt.AlignCenter)
                        self._points.setItemWidget(item, 1, edit)
                        self._points.addTopLevelItem(item)
                        self._ref.addItem(acpc)
                        self._ap3.addItem(acpc)
                        self._ap4.addItem(acpc)
                        self._lat3.addItem(acpc)
                        self._lat4.addItem(acpc)
                        self._h3.addItem(acpc)
                        self._h4.addItem(acpc)
                        row += 1
                # Add HandleWidget and LineWidget tools
                if tools.count() > 0:
                    for tool in tools:
                        if self._tool is not None and tool.getName() == self._tool.getName(): continue
                        if isinstance(tool, (sw.toolWidgets.HandleWidget, sw.toolWidgets.LineWidget)):
                            item = QTreeWidgetItem(self._points)
                            name = tool.getName()
                            item.setText(0, name)
                            if isinstance(tool, sw.toolWidgets.HandleWidget):
                                item.setData(0, Qt.UserRole, tool.getPosition())
                            else: item.setData(0, Qt.UserRole, tool.getPosition2())
                            item.setTextAlignment(0, Qt.AlignCenter)
                            edit = QSpinBox()
                            edit.setRange(0, 100)
                            if name in weights: edit.setValue(weights[name])
                            else: edit.setValue(0)
                            edit.setAlignment(Qt.AlignCenter)
                            edit.valueChanged.connect(self._editWeight)
                            item.setData(2, Qt.UserRole, 0.0)
                            item.setText(2, '0.0')
                            item.setTextAlignment(2, Qt.AlignCenter)
                            self._points.setItemWidget(item, 1, edit)
                            self._points.addTopLevelItem(item)
                            self._ref.addItem(name)
                            self._ap3.addItem(name)
                            self._ap4.addItem(name)
                            self._lat3.addItem(name)
                            self._lat4.addItem(name)
                            self._h3.addItem(name)
                            self._h4.addItem(name)
                            row += 1
        if row > 0: self._editWeight(0)
        self._postargets.setVisible(row > 0)
        self._points.setVisible(row > 0)
        self._posrel.setVisible(row > 0)
        self._rel.setVisible(row > 0)
        self._ref.setVisible(self._ref.count() > 1)
        if ref != '' and self._ref.findText(ref) >= 0: self._ref.setCurrentText(ref)
        if ap3 != '' and self._ap3.findText(ap3) >= 0: self._ap3.setCurrentText(ap3)
        if ap4 != '' and self._ap4.findText(ap4) >= 0: self._ap4.setCurrentText(ap4)
        if lat3 != '' and self._lat3.findText(lat3) >= 0: self._lat3.setCurrentText(lat3)
        if lat4 != '' and self._lat4.findText(lat4) >= 0: self._lat4.setCurrentText(lat4)
        if h3 != '' and self._h3.findText(h3) >= 0: self._h3.setCurrentText(h3)
        if h4 != '' and self._h4.findText(h4) >= 0: self._h4.setCurrentText(h4)
        if self._posrel.isChecked():
            self._apChanged(0.0)
            self._latChanged(0.0)
            self._hChanged(0.0)

    def _initMeshes(self):
        n = 0
        self._meshes.clear()
        if self.hasViewCollection():
            meshes = self._views.getMeshCollection()
            if meshes is not None:
                n = meshes.count()
                if n > 0:
                    for mesh in meshes:
                        self._meshes.addItem(mesh.getName())
        self._meshes.setVisible(n > 0)
        self._posmeshes.setVisible(n > 0)

    # Public method

    def clear(self):
        self._posx.setValue(0.0)
        self._posy.setValue(0.0)
        self._posz.setValue(0.0)
        self._poslx.setValue(0.0)
        self._posly.setValue(0.0)
        self._poslz.setValue(0.0)
        self._posex.setValue(0.0)
        self._posey.setValue(0.0)
        self._posez.setValue(0.0)
        self._xangle.setValue(0.0)
        self._yangle.setValue(0.0)
        self._length.setValue(50.0)
        self._poscursor.setChecked(True)
        self._points.clear()

    def copyFieldsFrom(self, dialog):
        if isinstance(dialog, DialogTarget):
            if self._ref.count() > 0: self._ref.setCurrentIndex(dialog._ref.currentIndex())
            if self._meshes.count() > 0: self._meshes.setCurrentIndex(dialog._meshes.currentIndex())
            # self._posx.setValue(dialog._posx.value())
            # self._posy.setValue(dialog._posy.value())
            # self._posz.setValue(dialog._posz.value())
            # self._poslx.setValue(dialog._poslx.value())
            # self._posly.setValue(dialog._posly.value())
            # self._poslz.setValue(dialog._poslz.value())
            self._ap1.setValue(dialog._ap1.value())
            self._ap2.setValue(dialog._ap2.value())
            if self._ap3.count() > 0: self._ap3.setCurrentIndex(dialog._ap3.currentIndex())
            if self._ap4.count() > 0: self._ap4.setCurrentIndex(dialog._ap4.currentIndex())
            self._ap5.setText(dialog._ap5.text())
            self._lat1.setValue(dialog._lat1.value())
            self._lat2.setValue(dialog._lat2.value())
            if self._lat3.count() > 0: self._lat3.setCurrentIndex(dialog._lat3.currentIndex())
            if self._lat4.count() > 0: self._lat4.setCurrentIndex(dialog._lat4.currentIndex())
            self._lat5.setText(dialog._lat5.text())
            self._h1.setValue(dialog._h1.value())
            self._h2.setValue(dialog._h2.value())
            if self._h3.count() > 0: self._h3.setCurrentIndex(dialog._h3.currentIndex())
            if self._h4.count() > 0: self._h4.setCurrentIndex(dialog._h4.currentIndex())
            self._h5.setText(dialog._h5.text())
            # self._xangle.setValue(dialog._xangle.value())
            # self._yangle.setValue(dialog._yangle.value())
            # self._length.setValue(dialog._length.value())
            # self._posex.setValue(dialog._posex.value())
            # self._posey.setValue(dialog._posey.value())
            # self._posez.setValue(dialog._posez.value())
            c = self._points.topLevelItemCount()
            if c > 0:
                for i in range(c):
                    w = self._points.itemWidget(self._points.topLevelItem(i), 1)
                    wd = dialog._points.itemWidget(dialog._points.topLevelItem(i), 1)
                    if w is not None and wd is not None: w.setValue(wd.value())
                self._editWeight(0.0)
            txt = dialog._btgroup.checkedButton().text()
            for bt in self._btgroup.buttons():
                if bt.text() == txt:
                    bt.setChecked(True)
                    break

    def copyFieldsTo(self, dialog):
        if isinstance(dialog, DialogTarget):
            if dialog._ref.count() > 0: dialog._ref.setCurrentIndex(self._ref.currentIndex())
            if dialog._meshes.count() > 0: dialog._meshes.setCurrentIndex(self._meshes.currentIndex())
            # dialog._posx.setValue(self._posx.value())
            # dialog._posy.setValue(self._posy.value())
            # dialog._posz.setValue(self._posz.value())
            # dialog._poslx.setValue(self._poslx.value())
            # dialog._posly.setValue(self._posly.value())
            # dialog._poslz.setValue(self._poslz.value())
            dialog._ap1.setValue(self._ap1.value())
            dialog._ap2.setValue(self._ap2.value())
            if dialog._ap3.count() > 0: dialog._ap3.setCurrentIndex(self._ap3.currentIndex())
            if dialog._ap4.count() > 0: dialog._ap4.setCurrentIndex(self._ap4.currentIndex())
            dialog._ap5.setText(self._ap5.text())
            dialog._lat1.setValue(self._lat1.value())
            dialog._lat2.setValue(self._lat2.value())
            if dialog._lat3.count() > 0: dialog._lat3.setCurrentIndex(self._lat3.currentIndex())
            if dialog._lat4.count() > 0: dialog._lat4.setCurrentIndex(self._lat4.currentIndex())
            dialog._lat5.setText(self._lat5.text())
            dialog._h1.setValue(self._h1.value())
            dialog._h2.setValue(self._h2.value())
            if dialog._h3.count() > 0: dialog._h3.setCurrentIndex(self._h3.currentIndex())
            if dialog._h4.count() > 0: dialog._h4.setCurrentIndex(self._h4.currentIndex())
            dialog._h5.setText(self._h5.text())
            # dialog._xangle.setValue(self._xangle.value())
            # dialog._yangle.setValue(self._yangle.value())
            # dialog._length.setValue(self._length.value())
            # dialog._posex.setValue(self._posex.value())
            # dialog._posey.setValue(self._posey.value())
            # dialog._posez.setValue(self._posez.value())
            c = self._points.topLevelItemCount()
            if c > 0:
                for i in range(c):
                    w = self._points.itemWidget(self._points.topLevelItem(i), 1)
                    wd = dialog._points.itemWidget(dialog._points.topLevelItem(i), 1)
                    wd.setValue(w.value())
                dialog._editWeight(0.0)
            txt = self._btgroup.checkedButton().text()
            for bt in dialog._btgroup.buttons():
                if bt.text() == txt:
                    bt.setChecked(True)
                    break
            dialog._first = False

    def setDefaultPosition(self):
        if self.hasViewCollection():
            p = list(self._views.getVolumeView().getCursorWorldPosition())
            self.setAbsolutePosition(p, check=False)
            p[2] += 50.0
            self.setEntryPosition(p)

    def setCursorPosition(self):
        if self.hasViewCollection():
            p = self._views.getVolumeView().getCursorWorldPosition()
            self.setAbsolutePosition(p, check=False)

    def setAbsolutePosition(self, p, check=True, leksell=True):
        self._posx.setValue(p[0])
        self._posy.setValue(p[1])
        self._posz.setValue(p[2])
        self._posabs.setChecked(check)
        vol = self._views.getVolume()
        if leksell and vol.hasLEKSELLTransform():
            pl = vol.getLEKSELLfromWorld(p)
            self._poslx.setValue(pl[0])
            self._posly.setValue(pl[1])
            self._poslz.setValue(pl[2])

    def setEntryPosition(self, p):
        self._posex.blockSignals(True)
        self._posey.blockSignals(True)
        self._posez.blockSignals(True)
        self._posex.setValue(p[0])
        self._posey.setValue(p[1])
        self._posez.setValue(p[2])
        self._posex.blockSignals(False)
        self._posey.blockSignals(False)
        self._posez.blockSignals(False)
        self._entryChanged(0)

    def updateAbsolutePosition(self):
        if self._tool is not None:
            if isinstance(self._tool, sw.toolWidgets.HandleWidget):
                p = self._tool.getPosition()
                self.setAbsolutePosition(p, check=False)
            else:
                p2 = self._tool.getPosition2()
                self.setAbsolutePosition(p2, check=False)
                p1 = self._tool.getPosition1()
                self._posex.blockSignals(True)
                self._posey.blockSignals(True)
                self._posez.blockSignals(True)
                self._posex.setValue(p1[0])
                self._posey.setValue(p1[1])
                self._posez.setValue(p1[2])
                self._posex.blockSignals(False)
                self._posey.blockSignals(False)
                self._posez.blockSignals(False)
                self._entryChanged(0)

    def getTargetPosition(self):
        if self.hasViewCollection():
            # Cursor position (Default)
            p = self._views.getVolumeView().getCursorWorldPosition()
            if self._poscursor.isChecked(): self.setAbsolutePosition(p)
            elif self._posabs.isChecked():
                # World coordinates absolute position
                p = self._posx.value(), self._posy.value(), self._posz.value()
                vol = self._views.getVolume()
                if vol.hasLEKSELLTransform():
                    pl = vol.getLEKSELLfromWorld(p)
                    self._poslx.setValue(pl[0])
                    self._posly.setValue(pl[1])
                    self._poslz.setValue(pl[2])
            elif self._poslabs.isChecked():
                # Leksell coordinates absolute position
                p0 = self._poslx.value(), self._posly.value(), self._poslz.value()
                vol = self._views.getVolume()
                if vol.hasLEKSELLTransform():
                    p = vol.getWorldfromLEKSELL(p0)
                    self.setAbsolutePosition(p)
            elif self._posmeshes.isChecked():
                # Mesh center of mass
                p = self._views.getMeshCollection()[self._meshes.currentText()].getCenterOfMass()
                self.setAbsolutePosition(p)
            elif self._postargets.isChecked():
                # Weighted targets
                n = self._points.topLevelItemCount()
                if n > 0:
                    p = list(self._points.topLevelItem(0).data(0, Qt.UserRole))
                    if n > 1:
                        w = self._points.topLevelItem(0).data(2, Qt.UserRole)
                        p[0] *= w
                        p[1] *= w
                        p[2] *= w
                        for i in range(1, n):
                            p2 = self._points.topLevelItem(i).data(0, Qt.UserRole)
                            w = self._points.topLevelItem(i).data(2, Qt.UserRole)
                            p[0] += (p2[0] * w)
                            p[1] += (p2[1] * w)
                            p[2] += (p2[2] * w)
                else: p = (0.0, 0.0, 0.0)
                self.setAbsolutePosition(p, check=False)
            elif self._posrel.isChecked():
                # relative position
                vol = self._views.getVolume()
                c = self._ref.currentText()
                if c == 'AC': p = vol.acpc.getAC()
                elif c == 'PC': p = vol.acpc.getPC()
                else:
                    tools = self._views.getToolCollection()
                    if c in tools:
                        tool = tools[c]
                        if isinstance(tool, sw.toolWidgets.HandleWidget): p = list(tool.getPosition())
                        else: p = list(tool.getPosition2())
                self._apChanged(0.0)
                self._latChanged(0.0)
                self._hChanged(0.0)
                lat = float(self._lat5.text())
                ap = float(self._ap5.text())
                h = float(self._h5.text())
                if vol is not None and vol.getACPC().hasACPC():
                    # move in AC PC space if exists
                    p = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p)
                else:
                    # move in world space otherwise
                    p[0] += lat
                    p[1] += ap
                    p[2] += h
                self.setAbsolutePosition(p, check=False)
            return p

    def getTrajectory(self):
        r = dict()
        r['angles'] = [self._xangle.value(), self._yangle.value()]
        r['length'] = self._length
        r['entry'] = [self._posex.value(), self._posey.value(), self._posez.value()]
        return r

    def getAttributes(self):
        if isinstance(self._tool, sw.toolWidgets.LineWidget):
            r = self.getTrajectory()
        else:
            r = dict()
            r['angles'] = None
            r['length'] = None
            r['entry'] = None
        r['target'] = self.getTargetPosition()
        return r

    def isAbsolutePosition(self):
        return self._poscursor.isChecked() or self._posabs.isChecked() or self._poslabs.isChecked()

    def isRelativeOrWeightedPosition(self):
        return not self.isAbsolutePosition()

    def isRelativePosition(self):
        return self._posrel.isChecked()

    def isWeightedPosition(self):
        return self._postargets.isChecked()

    def setTrajectoryFieldsVisibility(self, v):
        if isinstance(v, bool):
            self._trajectory.setVisible(v)
            self._lbtrajectory.setVisible(v)
            self._entry.setVisible(v)
            self._lbentry.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getTrajectoryFieldsVisibility(self):
        return self._trajectory.isVisible()

    def showTrajectoryFields(self):
        self.setTrajectoryFieldsVisibility(True)

    def hideTrajectoryFields(self):
        self.setTrajectoryFieldsVisibility(False)

    def setViewCollection(self, views):
        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(views, IconBarViewWidgetCollection):
            self._views = views

    def getViewCollection(self):
        return self._views

    def hasViewCollection(self):
        return self._views is not None

    # Qt Event

    def showEvent(self, event):
        super().showEvent(event)
        self._initPoints()
        self._initMeshes()
        self.updateAbsolutePosition()
        vol = self._views.getVolume()
        if vol is not None:
            v = vol.hasLEKSELLTransform()
            self._poslabs.setVisible(v)
            self._labs.setVisible(v)
        self.adjustSize()

"""
    Test 
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogTarget()
    main.activateWindow()
    main.show()
    app.exec_()
    exit()
