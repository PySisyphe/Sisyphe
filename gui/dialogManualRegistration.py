"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from SimpleITK import VersorRigid3DTransform
from SimpleITK import CenteredVersorTransformInitializerFilter

from ants.registration import get_center_of_mass

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
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
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalRegistrationViewWidget2

"""
    Class hierarchy
    
        QDialog -> DialogManualRegistration
"""


class DialogManualRegistration(QDialog):
    """
        DialogManualRegistration

        Inheritance

            QDialog -> DialogManualRegistration

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

        Public methods

            showDialogButtons()
            hideDialogButtons()
            enableView()
            disableView()
            [float, float, float] = getTranslations()
            [float, float, float] = getRotations()
            setTranslations([float, float, float])
            setRotations([float, float, float])
            setAcceptTextButton(str)
            setDialogToResample()
            setDialogToRegistration()
            setDialogToCheck()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, fixed, moving, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Manual registration')
        size = self.screen().availableSize()
        self.resize(int(size.width() * 0.8), int(size.height() * 0.8))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._widget = IconBarOrthogonalRegistrationViewWidget2()
        if isinstance(fixed, SisypheVolume):
            self._widget.setVolume(fixed)
            self._fixed = fixed
        else: raise TypeError('fixed image type {} is not SisypheVolume.'.format(type(fixed)))
        if isinstance(moving, SisypheVolume):
            self._widget.addOverlay(moving)
            self._moving = moving
        else: raise TypeError('moving image type {} is not SisypheVolume.'.format(type(moving)))
        self._widget().getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
        self._widget().popupMenuDisabled()
        self._layout.addWidget(self._widget)

        self._fixlut = LutWidget(size=256, view=self._widget)
        self._fixlut.setVolume(fixed)
        self._ovllut = LutWidget(size=256, view=self._widget)
        self._ovllut.setVolume(moving)

        # Init default dialog buttons

        self._ok = QPushButton('Resample')
        self._ok.setFixedWidth(120)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedSize(QSize(120, 32))
        self._interpolator = QComboBox()
        settings = SisypheFunctionsSettings()
        items = settings.getFieldValue('Resample', 'Interpolator')
        self._interpolator.setToolTip('Interpolator used to resample moving volume')
        self._interpolator.addItems(items)
        self._fix = MenuPushButton('Fixed')
        self._fix.setToolTip('Fixed volume LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._fixlut)
        self._fix.getPopupMenu().addAction(action)
        self._ovl = MenuPushButton('Moving')
        self._ovl.setToolTip('Moving volume LUT and windowing settings')
        action = QWidgetAction(self)
        action.setDefaultWidget(self._ovllut)
        self._ovl.getPopupMenu().addAction(action)
        self._opacity = LabeledSlider(percent=True)
        self._opacity.setTitle('Opacity')
        self._opacity.setRange(0, 100)
        self._opacity.setValue(20)
        self._opacity.setFixedWidth(150)
        self._opacity.setToolTip('Moving volume opacity')
        self._opacity.valueChanged.connect(self._opacityChanged)
        self._label = QLabel('Step')
        self._step = QDoubleSpinBox()
        self._step.setDecimals(1)
        self._step.setRange(0.1, 5.0)
        self._step.setSingleStep(0.1)
        self._step.setValue(0.5)
        self._step.setSuffix(' mm')
        self._step.valueChanged.connect(self._stepChanged)
        self._step.setToolTip('Translation and rotation steps of the moving volume after button click')
        self._crop = QCheckBox('Crop box')
        self._crop.setChecked(False)
        self._crop.setToolTip('Display crop box, fixed volume inside and moving volume outside')
        self._crop.stateChanged.connect(self._cropBoxChanged)
        self._reg = QCheckBox('Registration area box')
        self._reg.setChecked(False)
        self._reg.setToolTip('Display registration area box')
        self._reg.stateChanged.connect(self._regBoxChanged)
        self._edge = QComboBox()
        # self._edge.setFixedSize(QSize(100, 32))
        self._edge.addItem('Native')
        self._edge.addItem('Edge')
        self._edge.addItem('Edge and Native')
        self._edge.setToolTip('Display fixed volume edges')
        self._edge.currentIndexChanged.connect(self._edgeSelectionChanged)
        self._auto = QPushButton('Auto')
        self._auto.clicked.connect(self._estimate)
        self._auto.setToolTip('Automatic translation estimation')
        self._zero = QPushButton('Reset')
        self._zero.clicked.connect(self._reset)
        self._zero.setToolTip('Reset translations and rotations')

        self._menuestimate = QMenu(self)
        self._menuestimate.addAction('Translations - centers of mass alignment')
        self._menuestimate.addAction('Rotations - second order moments')
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
        layout.addStretch()
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(self._cancel)
        layout.addWidget(self._ok)
        self._layout.addLayout(layout)

        # Qt Signals

        self._ok.clicked.connect(self._resample)
        self._cancel.clicked.connect(self.reject)
        self._widget.setMoveOverlayOn()

    # Private method

    def _edgeSelectionChanged(self, index):
        if index == 0: self._widget().getFirstSliceViewWidget().displayNative()
        elif index == 1: self._widget().getFirstSliceViewWidget().displayEdge()
        else: self._widget().getFirstSliceViewWidget().displayEdgeAndNative()

    def _stepChanged(self, step):
        self._widget.setMoveStep(step)

    def _opacityChanged(self, v):
        self._widget().getFirstSliceViewWidget().setOverlayOpacity(0, v / 100)

    def _cropBoxChanged(self, state):
        if state == Qt.Unchecked: self._widget().getFirstSliceViewWidget().cropOff()
        else: self._widget().getFirstSliceViewWidget().cropOn()

    def _regBoxChanged(self, state):
        if state == Qt.Unchecked: self._widget().getFirstSliceViewWidget().registrationBoxOff()
        else: self._widget().getFirstSliceViewWidget().registrationBoxOn()

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
        trf.setRotations(self.getRotations())
        trf.setTranslations(self.getTranslations())
        trf.setAttributesFromFixedVolume(self._fixed)
        f.setMoving(self._moving)
        f.setTransform(trf)
        f.execute(fixed=self._fixed, dialog=True)
        self.accept()

    def _estimate(self, action):
        ch = action.text()[0]
        # Translations estimation, centers of mass alignment
        if ch == 'T':
            cf = get_center_of_mass(self._fixed.copyToANTSImage())
            cm = get_center_of_mass(self._moving.copyToANTSImage())
            c = tuple([cf[i] - cm[i] for i in range(3)])
            self._widget().getFirstSliceViewWidget().setTranslations(c, index=0)
        # Translations + rotations estimations, second order moments
        elif ch == 'R':
            f = CenteredVersorTransformInitializerFilter()
            f.ComputeRotationOn()
            t = VersorRigid3DTransform()
            t.SetIdentity()
            t = VersorRigid3DTransform(f.Execute(self._fixed.getSITKImage(), self._moving.getSITKImage(), t))
            t = VersorRigid3DTransform(t.GetInverse())
            trf = SisypheTransform()
            trf.setSITKTransform(t)
            self._widget().getFirstSliceViewWidget().setTranslations(trf.getTranslations(), index=0)
            self._widget().getFirstSliceViewWidget().setRotations(trf.getRotations(), index=0)

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
        return self._widget().getFirstViewWidget().getTranslations()

    def getRotations(self):
        return self._widget().getFirstViewWidget().getRotations()

    def setTranslations(self, t):
        self._widget().getFirstViewWidget().setTranslations(t)

    def setRotations(self, r):
        self._widget().getFirstViewWidget().setRotations(r)

    def setAcceptTextButton(self, txt):
        if isinstance(txt, str): self._ok.setText(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def setDialogToResample(self):
        if self._ok.text() != 'Resample':
            self._ok.clicked.disconnect(self.accept)
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
            self._step.setVisible(True)

    def setDialogToRegistration(self):
        if self._ok.text() != 'Registration':
            if self._ok.text() == 'Resample':
                self._ok.clicked.disconnect(self._resample)
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
            self._step.setVisible(True)

    def setDialogToCheck(self):
        if self._ok.text() != 'OK':
            if self._ok.text() == 'Resample':
                self._ok.clicked.disconnect(self._resample)
                self._ok.clicked.connect(self.accept)
            self._ok.setText('OK')
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
            self._step.setVisible(False)

    def getRegistrationBoxMaskArea(self):
        return self._widget().getFirstViewWidget().getRegistrationBoxMaskArea()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    print('Test DialogManualRegistration')
    file1 = '/Users/Jean-Albert/PycharmProjects/python310Project/TESTS/REGISTRATION/IRM.xvol'
    file2 = '/Users/Jean-Albert/PycharmProjects/python310Project/TESTS/REGISTRATION/TEP.xvol'
    img1 = SisypheVolume()
    img2 = SisypheVolume()
    img1.load(file1)
    img2.load(file2)
    img2.display.getLUT().setLutToRainbow()
    img2.display.getLUT().setDisplayBelowRangeColorOn()
    main = DialogManualRegistration(img1, img2)
    main.setDialogToRegistration()
    main.show()
    app.exec_()
