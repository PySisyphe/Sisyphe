"""
External packages/modules
-------------------------

    - ANTs, image registration, http://stnava.github.io/ANTs/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from SimpleITK import AffineTransform
from SimpleITK import CenteredTransformInitializerFilter

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidgetAction

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalRegistrationViewWidget2

__all__ = ['DialogManualRegistration']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogManualRegistration
"""


class DialogManualRegistration(QDialog):
    """
    DialogManualRegistration

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogManualRegistration

    Last revision: 08/03/2025
    """

    # Special method

    """
    Private attributes

    _widget     IconBarOrthogonalRegistrationViewWidget2
    _fixed      SisypheVolume, fixed volume
    _moving     SisypheVolume, moving volume
    _fixlut     LutWidget for fixed volume
    _ovllut     LutWidget for moving volume
    _fix        MenuPushButton, to display _fixedlut
    _ovl        MenuPushButton, to display _ovllut
    _opacity    LabeledSlider, to control overlay opacity
    _step       QDoubleSpinBox, translation and rotation step
    _crop       QCheckBox, visibility of the crop box
    _edge       QComboBox, type of volume display (native +/- gradient magnitude)
    _ok         QPushButton, automatic registration/exit button
    _cancel     QPushButton, cancel button
    """

    def __init__(self, fixed, moving, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Manual registration')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)
        size = self.screen().availableSize()
        self.resize(int(size.width() * 0.8), int(size.height() * 0.8))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._widget = IconBarOrthogonalRegistrationViewWidget2(parent=self)
        if isinstance(fixed, SisypheVolume):
            self._widget.setVolume(fixed)
            self._fixed = fixed
            self._fixed.setDefaultOrigin()
        else: raise TypeError('fixed image type {} is not SisypheVolume.'.format(type(fixed)))
        if isinstance(moving, SisypheVolume):
            self._widget.addOverlay(moving)
            self._moving = moving
            self._moving.setDefaultOrigin()
        else: raise TypeError('moving image type {} is not SisypheVolume.'.format(type(moving)))
        self._widget().getFirstSliceViewWidget().setOverlayOpacity(0, 0.5)
        self._widget().popupMenuDisabled()
        self._layout.addWidget(self._widget)

        self._fixlut = LutWidget(size=256, view=self._widget)
        self._fixlut.setVolume(fixed)
        self._ovllut = LutWidget(size=256, view=self._widget)
        self._ovllut.setVolume(moving)

        # Init default dialog buttons

        self._ok = QPushButton('Resample')
        self._cancel = QPushButton('Exit')
        self._cancel.setAutoDefault(True)
        self._cancel.setDefault(True)
        self._interpolator = QComboBox(parent=self)
        settings = SisypheFunctionsSettings()
        items = settings.getFieldValue('Resample', 'Interpolator')
        self._interpolator.setToolTip('Interpolator used to resample moving volume')
        self._interpolator.addItems(items)
        self._fix = MenuPushButton('Fixed', parent=self)
        self._fix.setToolTip('Fixed volume LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._fixlut)
        self._fix.getPopupMenu().addAction(action)
        self._ovl = MenuPushButton('Moving', parent=self)
        self._ovl.setToolTip('Moving volume LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._ovllut)
        self._ovl.getPopupMenu().addAction(action)
        self._opacity = LabeledSlider(percent=True, parent=self)
        self._opacity.setTitle('Opacity')
        self._opacity.setRange(0, 100)
        self._opacity.setValue(50)
        # self._opacity.setFixedWidth(200)
        self._opacity.setToolTip('Moving volume opacity')
        self._opacity.valueChanged.connect(self._opacityChanged)
        self._label = QLabel('Step', parent=self)
        self._step = QDoubleSpinBox(parent=self)
        self._step.setDecimals(1)
        self._step.setRange(0.1, 5.0)
        self._step.setSingleStep(0.1)
        self._step.setValue(0.5)
        self._step.setSuffix(' mm')
        # noinspection PyUnresolvedReferences
        self._step.valueChanged.connect(self._stepChanged)
        self._step.setToolTip('Translation and rotation steps of the moving volume after button click')
        self._crop = QCheckBox('Crop box', parent=self)
        self._crop.setChecked(False)
        self._crop.setToolTip('Display crop box, fixed volume inside and moving volume outside')
        # noinspection PyUnresolvedReferences
        self._crop.stateChanged.connect(self._cropBoxChanged)
        self._reg = QCheckBox('Registration area box', parent=self)
        self._reg.setChecked(False)
        self._reg.setToolTip('Display registration area box')
        # noinspection PyUnresolvedReferences
        self._reg.stateChanged.connect(self._regBoxChanged)
        self._edge = QComboBox(parent=self)
        # self._edge.setFixedSize(QSize(100, 32))
        self._edge.addItem('Native')
        self._edge.addItem('Edge')
        self._edge.addItem('Edge and Native')
        self._edge.setToolTip('Display fixed volume edges')
        # noinspection PyUnresolvedReferences
        self._edge.currentIndexChanged.connect(self._edgeSelectionChanged)
        self._auto = QPushButton('Auto', parent=self)
        # noinspection PyUnresolvedReferences
        self._auto.clicked.connect(self._estimate)
        self._auto.setToolTip('Automatic translation estimation')
        self._zero = QPushButton('Reset', parent=self)
        # noinspection PyUnresolvedReferences
        self._zero.clicked.connect(self._reset)
        self._zero.setToolTip('Reset translations and rotations')
        self._tooltip = QCheckBox('Tooltip off')
        self._tooltip.setToolTip('Disable tooltips in slice view')
        # noinspection PyUnresolvedReferences
        self._tooltip.pressed.connect(self._tooltipChanged)

        self._menuestimate = QMenu(self)
        # noinspection PyTypeChecker
        self._menuestimate.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menuestimate.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menuestimate.setAttribute(Qt.WA_TranslucentBackground, True)
        self._menuestimate.addAction('FOV center alignment')
        self._menuestimate.addAction('Center of mass alignment')
        # noinspection PyUnresolvedReferences
        self._menuestimate.triggered.connect(self._estimate)
        self._auto.setMenu(self._menuestimate)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(self._edge)
        layout.addWidget(self._crop)
        layout.addWidget(self._reg)
        layout.addWidget(self._label)
        layout.addWidget(self._step)
        layout.addWidget(self._opacity)
        layout.addWidget(self._fix)
        layout.addWidget(self._ovl)
        layout.addWidget(self._interpolator)
        layout.addWidget(self._auto)
        layout.addWidget(self._zero)
        layout.addWidget(self._tooltip)
        layout.addStretch()
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self._resample)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        self._widget.setMoveOverlayOn()

    # Private method

    def _edgeSelectionChanged(self, index):
        if index == 0: self._widget().getFirstSliceViewWidget().displayNative()
        elif index == 1: self._widget().getFirstSliceViewWidget().displayEdge()
        else: self._widget().getFirstSliceViewWidget().displayEdgeAndNative()

    def _stepChanged(self, step):
        self._widget.setMoveStep(step)

    # noinspection PyUnusedLocal
    def _opacityChanged(self, v):
        self._widget().getFirstSliceViewWidget().setOverlayOpacity(0, self._opacity.value() / 100)

    def _cropBoxChanged(self, state):
        if state == Qt.Unchecked:
            self._widget().getFirstSliceViewWidget().cropOff()
            self._widget().getFirstSliceViewWidget().setOverlayOpacity(0, self._opacity.value() / 100)
        else: self._widget().getFirstSliceViewWidget().cropOn()

    def _regBoxChanged(self, state):
        if state == Qt.Unchecked: self._widget().getFirstSliceViewWidget().registrationBoxOff()
        else: self._widget().getFirstSliceViewWidget().registrationBoxOn()

    def _tooltipChanged(self):
        self._widget().getFirstSliceViewWidget().setTooltipVisibility(self._tooltip.isChecked())

    def _resample(self):
        f = SisypheApplyTransform()
        interpol = self._interpolator.currentText()
        if interpol == 'Nearest Neighbor': f.setInterpolator(0)
        elif interpol == 'Linear': f.setInterpolator(1)
        elif interpol == 'Bspline': f.setInterpolator(2)
        elif interpol == 'Gaussian': f.setInterpolator(3)
        elif interpol == 'Hamming Sinc': f.setInterpolator(4)
        elif interpol == 'Cosine Sinc': f.setInterpolator(5)
        elif interpol == 'Welch Sinc': f.setInterpolator(6)
        elif interpol == 'Lanczos Sinc': f.setInterpolator(7)
        elif interpol == 'Blackman Sinc': f.setInterpolator(8)
        else: f.setInterpolator(1)
        trf = SisypheTransform()
        trf.setRotations(self.getRotations(), deg=True)
        trf.setTranslations(self.getTranslations())
        trf.setAttributesFromFixedVolume(self._fixed)
        trf.setCenterFromSisypheVolume(self._moving)
        trf = trf.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
        f.setMoving(self._moving)
        f.setTransform(trf)
        f.execute(fixed=self._fixed, dialog=True)

    def _estimate(self, action):
        ch = action.text()[0]
        # Translations estimation, FOV center alignment
        if ch == 'F':
            f = CenteredTransformInitializerFilter()
            f.GeometryOn()
            t = AffineTransform(f.Execute(self._moving.getSITKImage(), self._fixed.getSITKImage(), AffineTransform(3)))
            self._widget().getFirstSliceViewWidget().setTranslations(t.GetTranslation(), index=0)
        # Translations estimation, center of mass alignment
        elif ch == 'C':
            f = CenteredTransformInitializerFilter()
            f.MomentsOn()
            t = AffineTransform(f.Execute(self._moving.getSITKImage(), self._fixed.getSITKImage(), AffineTransform(3)))
            self._widget().getFirstSliceViewWidget().setTranslations(t.GetTranslation(), index=0)

    def _reset(self):
        self._widget().getFirstSliceViewWidget().setTranslations((0.0, 0.0, 0.0), index=0)
        self._widget().getFirstSliceViewWidget().setRotations((0.0, 0.0, 0.0), index=0)

    # Public methods

    def showDialogButtons(self):
        self._ok.setVisible(True)
        self._cancel.setVisible(True)
        self._label.setVisible(True)
        self._step.setVisible(True)
        self._crop.setVisible(True)
        self._edge.setVisible(True)
        self._opacity.setVisible(True)
        self._fix.setVisible(True)
        self._ovl.setVisible(True)
        self._interpolator.setVisible(True)

    def hideDialogButtons(self):
        self._label.setVisible(False)
        self._step.setVisible(False)
        self._crop.setVisible(False)
        self._edge.setVisible(False)
        self._opacity.setVisible(False)
        self._fix.setVisible(False)
        self._ovl.setVisible(False)
        self._interpolator.setVisible(False)

    def enableView(self):
        self._widget.setEnabled(True)

    def disableView(self):
        self._widget.setEnabled(False)

    def getTranslations(self):
        return self._widget().getFirstViewWidget().getTranslations(index=0)

    def getRotations(self):
        return self._widget().getFirstViewWidget().getRotations(index=0)

    def setTranslations(self, t):
        self._widget().getFirstViewWidget().setTranslations(t, index=0)

    def setRotations(self, r):
        self._widget().getFirstViewWidget().setRotations(r, index=0)

    def setAcceptTextButton(self, txt):
        if isinstance(txt, str): self._ok.setText(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def setDialogToResample(self):
        if self._ok.text() != 'Resample':
            # noinspection PyUnresolvedReferences
            self._ok.clicked.disconnect(self.accept)
            # noinspection PyUnresolvedReferences
            self._ok.clicked.connect(self._resample)
            self._ok.setText('Resample')
            self._interpolator.setVisible(True)
            self._widget.setMoveOverlayOn()
            self._widget.setMoveButtonsVisibility(True)
            self._widget.setRegistrationBoxVisibility(False)
            self._reg.setVisible(False)
            self._reg.setChecked(False)
            self._crop.setVisible(True)
            self._crop.setChecked(False)
            self._widget.cropOff()
            self._auto.setVisible(True)
            self._zero.setVisible(True)
            self._label.setVisible(True)
            self._step.setVisible(True)

    def setDialogToRegistration(self):
        if self._ok.text() != 'Registration':
            if self._ok.text() == 'Resample':
                # noinspection PyUnresolvedReferences
                self._ok.clicked.disconnect(self._resample)
                # noinspection PyUnresolvedReferences
                self._ok.clicked.connect(self.accept)
            self._ok.setText('Registration')
            self._interpolator.setVisible(False)
            self._widget.setMoveOverlayOn()
            self._widget.setMoveButtonsVisibility(True)
            self._widget.setRegistrationBoxVisibility(False)
            self._reg.setVisible(True)
            self._reg.setChecked(False)
            self._crop.setVisible(False)
            self._crop.setChecked(False)
            self._widget.cropOff()
            self._auto.setVisible(True)
            self._zero.setVisible(True)
            self._label.setVisible(True)
            self._step.setVisible(True)

    def setDialogToCheck(self):
        if self._ok.text() != 'OK':
            if self._ok.text() == 'Resample':
                # noinspection PyUnresolvedReferences
                self._ok.clicked.disconnect(self._resample)
                # noinspection PyUnresolvedReferences
                self._ok.clicked.connect(self.accept)
            self._ok.setText('OK')
            self._cancel.setText('Cancel')
            self._interpolator.setVisible(False)
            self._widget.setMoveOverlayOff()
            self._widget.setMoveButtonsVisibility(False)
            self._widget.setRegistrationBoxVisibility(False)
            self._reg.setVisible(False)
            self._reg.setChecked(False)
            self._crop.setVisible(True)
            self._crop.setChecked(False)
            self._widget.cropOff()
            self._auto.setVisible(False)
            self._zero.setVisible(False)
            self._label.setVisible(False)
            self._step.setVisible(False)

    def getRegistrationBoxMaskArea(self):
        return self._widget().getFirstViewWidget().getRegistrationBoxMaskArea()

    # Qt events

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            self._widget.finalize()
        # Revision 10/03/2025 >
