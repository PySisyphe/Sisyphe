"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from math import atan2
from math import degrees

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheImageAttributes import SisypheACPC
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalReorientViewWidget

"""
    Class hierarchy

        QDialog -> DialogACPC
"""


class DialogACPC(QDialog):
    """
        DialogACPC

        Description

            GUI dialog for anterior and posterior commissures selection.
            Control of y rotation in coronal view. x and z rotations are
            calculated with the position of the commissures.

        Inheritance

            QDialog -> DialogACPC

        Private attributes

            _views      IconBarOrthogonalReorientViewWidget
            _acpc       SisypheACPC
            _lut        LutWidget
            _mode1      QRadioButton
            _mode2      QRadioButton
            _setac      QPushButton
            _getac      QPushButton
            _setpc      QPushButton
            _getpc      QPushButton
            _reset      QPushButton
            _resettrf   QPushButton
            _opacity    LabeledSlider
            _width      LabeledDoubleSpinBox

        Public methods

            setResliceCursorOpacity(float)
            setResliceCursorWidth(float)
            setVolume(SisypheVolume)
            SisypheVolume = getVolume()
            exit()
            ok()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('AC-PC selection')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init attributes

        self._acpc = SisypheACPC()

        # Init widgets

        self._views = IconBarOrthogonalReorientViewWidget()
        self._views().setFOVBoxVisibility(False)
        self._views().setRoundedCursorCoordinatesDisabled()
        self._layout.addWidget(self._views)

        self._lut = LutWidget(size=256, view=self._views)
        self._blut = MenuPushButton('LUT')
        self._blut.setToolTip('LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._lut)
        self._blut.getPopupMenu().addAction(action)
        self._mode1 = QRadioButton('AC-PC selection')
        self._mode1.setChecked(True)
        self._mode2 = QRadioButton('Rotations')
        self._mode2.setVisible(False)
        self._mode1.toggled.connect(self._updateMode)
        self._mode2.toggled.connect(self._updateMode)
        self._setac = QPushButton('Set AC')
        self._setac.setToolTip('Set AC at the current cursor position.')
        self._setac.pressed.connect(self._setAC)
        self._getac = QPushButton('Get AC')
        self._getac.pressed.connect(self._getAC)
        self._vac = QLineEdit()
        self._vac.setReadOnly(True)
        self._vac.setAlignment(Qt.AlignCenter)
        self._vac.setVisible(False)
        self._setpc = QPushButton('Set PC')
        self._setpc.setToolTip('Set PC at the current cursor position.')
        self._setpc.pressed.connect(self._setPC)
        self._getpc = QPushButton('Get PC')
        self._getpc.pressed.connect(self._getPC)
        self._vpc = QLineEdit()
        self._vpc.setReadOnly(True)
        self._vpc.setVisible(False)
        self._vpc.setAlignment(Qt.AlignCenter)
        self._setrot = QPushButton('Set rotations')
        self._setrot.setToolTip('Set Y rotation, update AC/PC with X and Z rotations.')
        self._setrot.pressed.connect(self._setRotation)
        self._vrot = QLineEdit()
        self._vrot.setReadOnly(True)
        self._vrot.setFixedWidth(75)
        self._vrot.setAlignment(Qt.AlignCenter)
        self._resettrf = QPushButton('Reset')
        self._resettrf.setVisible(False)
        self._resettrf.setToolTip('Reset Y rotation.')
        self._resettrf.pressed.connect(self._resetRotation)
        self._opacity = LabeledSlider(title='Reslice cursor opacity')
        self._opacity.setRange(0, 100)
        self._opacity.setFixedWidth(200)
        self._opacity.setValue(int(self._views().getFirstViewWidget().getLineOpacity() * 100))
        self._opacity.valueChanged.connect(self.setResliceCursorOpacity)
        self._width = LabeledDoubleSpinBox('Line width')
        self._width.setSingleStep(0.5)
        self._width.setRange(0.5, 5.0)
        self._width.setAlignment(Qt.AlignCenter)
        self._width.setValue(self._views().getFirstViewWidget().getLineWidth())
        self._width.valueChanged.connect(self.setResliceCursorWidth)

        lyout = QHBoxLayout()
        lyout.setSpacing(5)
        lyout.setContentsMargins(5, 5, 5, 5)
        lyout.addWidget(self._blut)
        lyout.addSpacing(10)
        lyout.addWidget(self._mode1)
        lyout.addWidget(self._setac)
        lyout.addWidget(self._getac)
        lyout.addWidget(self._vac)
        lyout.addWidget(self._setpc)
        lyout.addWidget(self._getpc)
        lyout.addWidget(self._vpc)
        lyout.addSpacing(10)
        lyout.addWidget(self._mode2)
        lyout.addWidget(self._setrot)
        lyout.addWidget(self._vrot)
        lyout.addWidget(self._resettrf)
        lyout.addStretch()
        lyout.addWidget(self._opacity)
        lyout.addWidget(self._width)
        self._layout.addLayout(lyout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        self._ok = QPushButton('OK')
        self._ok.setFixedSize(QSize(120, 32))
        self._ok.setToolTip('Save AC-PC and exit.')
        self._ok.setEnabled(False)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()
        self._layout.addLayout(layout)

        # Qt Signals

        cancel.clicked.connect(self.exit)
        self._ok.clicked.connect(self.ok)

    # Private method

    def _updateMode(self, v):
        v = self._mode1.isChecked()
        self._setac.setVisible(v)
        self._setpc.setVisible(v)
        self._getac.setVisible(v)
        self._getpc.setVisible(v)
        self._resettrf.setVisible(not v)
        if v:
            self._views().getFirstViewWidget().setRotations(0.0, 0.0, 0.0)
            self._views().translationsEnabled()
            self._views().rotationsDisabled()
            self._views().setSliceNavigationEnabled()
        else:
            self._views().translationsDisabled()
            # self._views().rotationXDisabled()
            # self._views().rotationZDisabled()
            self._views().rotationXEnabled()
            self._views().rotationZEnabled()
            self._views().rotationYEnabled()
            self._views().setSliceNavigationDisabled()
            if self._acpc.hasACPC():
                p = self._acpc.getMidACPC()
                self._views().getFirstViewWidget().setCursorWorldPosition(p[0], p[1], p[2])
                r = self._acpc.getRotations(deg=True)
                self._views().getFirstViewWidget().setRotations(r[0], r[1], r[2])

    def _setAC(self):
        p = self._views().getFirstViewWidget().getResliceCursorPosition()
        self._acpc.setAC(p)
        self._getac.setToolTip(str(self._acpc))
        self._getpc.setToolTip(str(self._acpc))
        self._vac.setVisible(True)
        self._vac.setText('{ac[0]:.1f} {ac[1]:.1f} {ac[2]:.1f}'.format(ac=p))
        v = self._acpc.hasACPC()
        self._ok.setEnabled(v)
        if v:
            self._mode2.setVisible(True)
            self._resettrf.setVisible(True)

    def _setPC(self):
        p = self._views().getFirstViewWidget().getResliceCursorPosition()
        self._acpc.setPC(p)
        self._getac.setToolTip(str(self._acpc))
        self._getpc.setToolTip(str(self._acpc))
        self._vpc.setVisible(True)
        self._vpc.setText('{pc[0]:.1f} {pc[1]:.1f} {pc[2]:.1f}'.format(pc=p))
        v = self._acpc.hasACPC()
        self._ok.setEnabled(v)
        if v:
            self._mode2.setVisible(True)
            self._resettrf.setVisible(True)

    def _getAC(self):
        if self._acpc.hasAC():
            p = self._acpc.getAC()
            self._views().getFirstViewWidget().setCursorWorldPosition(p[0], p[1], p[2])

    def _getPC(self):
        if self._acpc.hasPC():
            p = self._acpc.getPC()
            self._views().getFirstViewWidget().setCursorWorldPosition(p[0], p[1], p[2])

    def _setRotation(self):
        # Update AC and PC from reslice cursor rotations
        r1 = self._acpc.getRotations(deg=True)
        r2 = self._views().getFirstViewWidget().getRotations()
        r = [r1[0] - r2[0],
             r1[1] - r2[1],
             r1[2] - r2[2]]
        trf = SisypheTransform()
        trf.setCenter(self._acpc.getMidACPC())
        trf.setRotations(r, deg=True)
        self._acpc.setAC(trf.applyToPoint(self._acpc.getAC()))
        self._acpc.setPC(trf.applyToPoint(self._acpc.getPC()))
        self._getac.setToolTip(str(self._acpc))
        self._getpc.setToolTip(str(self._acpc))
        self._vac.setText('{ac[0]:.1f} {ac[1]:.1f} {ac[2]:.1f}'.format(ac=self._acpc.getAC()))
        self._vpc.setText('{pc[0]:.1f} {pc[1]:.1f} {pc[2]:.1f}'.format(pc=self._acpc.getPC()))
        # Set Y rotation
        r = self._views().getFirstViewWidget().getRotations()[1]
        self._acpc.setYRotation(r, deg=True)
        self._vrot.setText('{:.1f}°'.format(r))

    def _resetRotation(self):
        r = self._views().getFirstViewWidget().getRotations()
        self._acpc.setYRotation(0.0, deg=True)
        self._views().getFirstViewWidget().setRotations(r[0], 0.0, r[2])

    # Public method

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

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            self._views.setVolume(vol)
            self._lut.setVolume(vol)
            self._updateMode(True)
            # copy SisypheVolume AC
            if vol.acpc.hasAC():
                p = vol.acpc.getAC()
                self._acpc.setAC(p)
                self._vac.setVisible(True)
                self._vac.setText('{ac[0]:.1f} {ac[1]:.1f} {ac[2]:.1f}'.format(ac=p))
            # copy SisypheVolume PC
            if vol.acpc.hasPC():
                p = vol.acpc.getPC()
                self._acpc.setPC(p)
                self._vpc.setVisible(True)
                self._vpc.setText('{pc[0]:.1f} {pc[1]:.1f} {pc[2]:.1f}'.format(pc=p))
            # copy SisypheVolume Y Rotation
            r = vol.acpc.getRotations(deg=True)[1]
            self._acpc.setYRotation(r, deg=True)
            self._vrot.setText('{:.1f}°'.format(r))
            # Display
            self._mode2.setVisible(vol.acpc.hasACPC())
            self._ok.setEnabled(vol.acpc.hasACPC())
            if vol.acpc.hasACPC():
                p = vol.acpc.getMidACPC()
                self._views().getFirstViewWidget().setCursorWorldPosition(p[0], p[1], p[2])
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def getVolume(self):
        return self._views.getVolume()

    def exit(self):
        self.close()

    def ok(self):
        if self._acpc.hasACPC():
            vol = self._views.getVolume()
            vol.setACPC(self._acpc)
            vol.save()
            self.close()


"""
    Test
"""

if __name__ == '__main__':
    from sys import argv
    from os import chdir

    chdir('/Users/Jean-Albert/PycharmProjects/python310Project/TESTS/REGISTRATION')
    app = QApplication(argv)
    main = DialogACPC()
    vv = SisypheVolume()
    vv.load('FLAIR.xvol')
    main.setVolume(vv)
    main.show()
    app.exec_()
