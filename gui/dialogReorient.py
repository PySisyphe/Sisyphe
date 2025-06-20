"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor
from SimpleITK import LabelShapeStatisticsImageFilter

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalReorientViewWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogReorient']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QDialog -> DialogReorient
"""


class DialogReorient(QDialog):
    """
    DialogReorient

    Description
    ~~~~~~~~~~~

    GUI dialog for volume reorientation.
    Control of rotations, translations, center of rotation and FOV.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogReorient

    Last revision: 08/03/2025
    """

    # Special method

    """
    Private attributes

    _views      IconBarOrthogonalReorientViewWidget
    _lut        LutWidget
    _settings   FunctionSettingsWidget
    _box        QCheckBox
    _sizex      QSpinBox
    _sizey      QSpinBox
    _sizez      QSpinBox
    _spacex     QDoubleSpinBox
    _spacey     QDoubleSpinBox
    _spacez     QDoubleSpinBox
    _resetfov   QPushButton
    _resettrf   QPushButton
    _opacity    LabeledSlider
    _width      LabeledDoubleSpinBox
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Volume reorientation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._views = IconBarOrthogonalReorientViewWidget()
        self._layout.addWidget(self._views)

        self._lut = LutWidget(size=256, view=self._views)
        self._blut = MenuPushButton('LUT')
        self._blut.setToolTip('LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._lut)
        self._blut.getPopupMenu().addAction(action)
        self._box = QCheckBox('Field of view Box')
        # noinspection PyUnresolvedReferences
        self._box.toggled.connect(self.setBoxVisibility)
        self._label1 = QLabel('Size')
        self._sizex = QSpinBox()
        self._sizey = QSpinBox()
        self._sizez = QSpinBox()
        self._sizex.setAlignment(Qt.AlignCenter)
        self._sizey.setAlignment(Qt.AlignCenter)
        self._sizez.setAlignment(Qt.AlignCenter)
        # self._sizex.setFixedWidth(60)
        # self._sizey.setFixedWidth(60)
        # self._sizez.setFixedWidth(60)
        self._sizex.setRange(10, 1024)
        self._sizey.setRange(10, 1024)
        self._sizez.setRange(10, 1024)
        self._sizex.setValue(256)
        self._sizey.setValue(256)
        self._sizez.setValue(256)
        self._label2 = QLabel('Spacing')
        self._spacex = QDoubleSpinBox()
        self._spacey = QDoubleSpinBox()
        self._spacez = QDoubleSpinBox()
        self._spacex.setAlignment(Qt.AlignCenter)
        self._spacey.setAlignment(Qt.AlignCenter)
        self._spacez.setAlignment(Qt.AlignCenter)
        # self._spacex.setFixedWidth(60)
        # self._spacey.setFixedWidth(60)
        # self._spacez.setFixedWidth(60)
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
        self._resetfov = QPushButton('Reset FOV')
        # noinspection PyUnresolvedReferences
        self._resetfov.pressed.connect(self.resetFOV)
        self._resettrf = QPushButton('Reset Transform')
        # noinspection PyUnresolvedReferences
        self._resettrf.pressed.connect(self.resetTransform)
        self._auto = QPushButton('Auto')
        # noinspection PyUnresolvedReferences
        self._auto.pressed.connect(self.autoTransform)
        self._auto.setToolTip('Automatic reorientation on principal axes.')
        self._opacity = LabeledSlider(title='Reslice cursor opacity')
        self._opacity.setRange(0, 100)
        self._opacity.setFixedWidth(200)
        self._opacity.setValue(int(self._views().getFirstViewWidget().getLineOpacity() * 100))
        self._opacity.valueChanged.connect(self.setResliceCursorOpacity)
        self._width = LabeledDoubleSpinBox('Reslice cursor width')
        self._width.setSingleStep(0.5)
        self._width.setRange(0.5, 5.0)
        self._width.setAlignment(Qt.AlignCenter)
        self._width.setValue(self._views().getFirstViewWidget().getLineWidth())
        # noinspection PyUnresolvedReferences
        self._width.valueChanged.connect(self.setResliceCursorWidth)

        lyout = QHBoxLayout()
        lyout.setSpacing(5)
        lyout.setContentsMargins(5, 5, 5, 5)
        lyout.addWidget(self._blut)
        lyout.addSpacing(10)
        lyout.addWidget(self._label1)
        lyout.addWidget(self._sizex)
        lyout.addWidget(self._sizey)
        lyout.addWidget(self._sizez)
        lyout.addSpacing(10)
        lyout.addWidget(self._label2)
        lyout.addWidget(self._spacex)
        lyout.addWidget(self._spacey)
        lyout.addWidget(self._spacez)
        lyout.addSpacing(10)
        lyout.addWidget(self._resetfov)
        lyout.addWidget(self._resettrf)
        lyout.addWidget(self._auto)
        lyout.addStretch()
        lyout.addWidget(self._opacity)
        lyout.addSpacing(10)
        lyout.addWidget(self._width)
        self._layout.addLayout(lyout)

        self._settings = FunctionSettingsWidget('Resample')

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Exit')
        cancel.setFixedWidth(100)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        self._execute = QPushButton('Resample')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Apply reorientation to volume.')
        self._execute.setEnabled(False)
        layout.addWidget(cancel)
        layout.addWidget(self._execute)
        layout.addStretch()
        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.exit)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Private method

    def _updateFovValues(self):
        size = [self._sizex.value(), self._sizey.value(), self._sizez.value()]
        spacing = [self._spacex.value(), self._spacey.value(), self._spacez.value()]
        self._views().getFirstViewWidget().setSize(size)
        self._views().getFirstViewWidget().setSpacing(spacing)

    # Public method

    def setBoxVisibility(self, v):
        if isinstance(v, bool):
            self._views().setFOVBoxVisibility(v)
            self._sizex.setVisible(v)
            self._sizey.setVisible(v)
            self._sizez.setVisible(v)
            self._spacex.setVisible(v)
            self._spacey.setVisible(v)
            self._spacez.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setResliceCursorOpacity(self, v):
        if isinstance(v, int):
            v = v / 100
            self._views().setResliceCursorOpacity(v)
            self._views().setFovBoxOpacity(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setResliceCursorWidth(self, v):
        if isinstance(v, (int, float)):
            self._views().setResliceCursorLineWidth(float(v))
            self._views().setFovBoxLineWidth(float(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def resetFOV(self):
        vol = self.getVolume()
        size = vol.getSize()
        spacing = vol.getSpacing()
        self._sizex.setValue(size[0])
        self._sizey.setValue(size[1])
        self._sizez.setValue(size[2])
        self._spacex.setValue(spacing[0])
        self._spacey.setValue(spacing[1])
        self._spacez.setValue(spacing[2])

    def getSize(self):
        return self._sizex.value(), self._sizey.value(), self._sizez.value()

    def getSpacing(self):
        return self._spacex.value(), self._spacey.value(), self._spacez.value()

    def getFOV(self):
        return (self._spacex.value() * self._sizex.value(),
                self._spacey.value() * self._sizey.value(),
                self._spacez.value() * self._sizez.value())

    def isDefaultFOV(self):
        return self.getFOV() == self._views.getVolume().getFieldOfView()

    def resetTransform(self):
        self._views().getFirstSliceViewWidget().reset()

    def autoTransform(self):
        m = self.getVolume().getNumpy().flatten().mean()
        mask = self.getVolume().getSITKImage() > m
        f = LabelShapeStatisticsImageFilter()
        f.Execute(mask)
        # Translations
        c = f.GetCentroid(1)
        cv = self.getVolume().getCenter()
        self._views().getFirstViewWidget().setTranslations(c[0] - cv[0],
                                                           c[1] - cv[1],
                                                           c[2] - cv[2])
        r = f.GetPrincipalAxes(1)
        v = dict()
        # Sort x, y, z axis
        vi = [abs(i) for i in r[:3]]
        v[vi.index(max(vi))] = r[:3]
        vi = [abs(i) for i in r[3:6]]
        v[vi.index(max(vi))] = r[3:6]
        vi = [abs(i) for i in r[6:]]
        v[vi.index(max(vi))] = r[6:]
        v = v[0] + v[1] + v[2]
        trf = SisypheTransform()
        trf.setIdentity()
        trf.setFlattenMatrix(v, bycolumn=True)
        trf = trf.getInverseTransform()
        # < Revision 04/09/2024
        # use only z rotation
        r = trf.getRotations(deg=True)
        ry = r[1]
        rz = r[2]
        ary = abs(ry)
        arz = abs(rz)
        if ary > 90.0 and arz > 90.0:
            if ry > 0: ry = ry - 180.0
            else: ry = 180.0 + ry
            if rz > 0: rz = rz - 180.0
            else: rz = 180.0 + rz
        elif ary > 90.0 >= arz:
            if ry > 0: ry = ry - 180.0
            else: ry = 180.0 + ry
            rz = -rz
        elif ary <= 90.0 < arz:
            if rz > 0: rz = rz - 180.0
            else: rz = 180.0 + rz
            ry = -ry
        # self._views().getFirstViewWidget().setRotations(r[0], r[1], r[2])
        self._views().getFirstViewWidget().setRotations(0.0, ry, rz)
        # Revision 04/09/2024 >

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if self._views.getVolume() is not None:
                # noinspection PyUnresolvedReferences
                self._sizex.valueChanged.disconnect()
                # noinspection PyUnresolvedReferences
                self._sizey.valueChanged.disconnect()
                # noinspection PyUnresolvedReferences
                self._sizez.valueChanged.disconnect()
                # noinspection PyUnresolvedReferences
                self._spacex.valueChanged.disconnect()
                # noinspection PyUnresolvedReferences
                self._spacey.valueChanged.disconnect()
                # noinspection PyUnresolvedReferences
                self._spacez.valueChanged.disconnect()
            self._views.setVolume(vol)
            size = vol.getSize()
            spacing = vol.getSpacing()
            self._sizex.setValue(size[0])
            self._sizey.setValue(size[1])
            self._sizez.setValue(size[2])
            self._spacex.setValue(spacing[0])
            self._spacey.setValue(spacing[1])
            self._spacez.setValue(spacing[2])
            # noinspection PyUnresolvedReferences
            self._sizex.valueChanged.connect(self._updateFovValues)
            # noinspection PyUnresolvedReferences
            self._sizey.valueChanged.connect(self._updateFovValues)
            # noinspection PyUnresolvedReferences
            self._sizez.valueChanged.connect(self._updateFovValues)
            # noinspection PyUnresolvedReferences
            self._spacex.valueChanged.connect(self._updateFovValues)
            # noinspection PyUnresolvedReferences
            self._spacey.valueChanged.connect(self._updateFovValues)
            # noinspection PyUnresolvedReferences
            self._spacez.valueChanged.connect(self._updateFovValues)
            self._execute.setEnabled(True)
            self._lut.setVolume(vol)

    def getVolume(self):
        return self._views.getVolume()

    def exit(self):
        self.close()

    def execute(self):
        # Get forward transform from widget
        trf = self._views().getFirstViewWidget().getTransform().copy()
        trf.setID('')
        trf.setSpacing([self._spacex.value(), self._spacey.value(), self._spacez.value()])
        trf.setSize([self._sizex.value(), self._sizey.value(), self._sizez.value()])
        # < Revision 27/08/2024
        trf = trf.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
        # Revision 27/08/2024 >
        f = SisypheApplyTransform()
        f.setMoving(self.getVolume())
        f.setTransform(trf)
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
        prefix = self._settings.getParameterValue('Prefix')
        suffix = self._settings.getParameterValue('Suffix')
        wait = DialogWait(title='Resample')
        wait.open()
        wait.setInformationText('Resample {} ...'.format(self.getVolume().getBasename()))
        try:
            f.execute(fixed=None, save=True, dialog=True, prefix=prefix, suffix=suffix, wait=wait)
        except Exception as err:
            messageBox(self, title=self.windowTitle(), text='{}'.format(err))
        wait.close()

    # Qt events

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            self._views.finalize()
        # Revision 10/03/2025 >
