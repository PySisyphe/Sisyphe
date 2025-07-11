"""
External packages/modules
-------------------------

    - ANTs, image registration, https://github.com/ANTsX/ANTsPy
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import remove
from os import chdir

from os.path import join
from os.path import split
from os.path import dirname
from os.path import abspath
from os.path import exists

from Sisyphe.processing.capturedStdoutProcessing import ProcessRegistration
from multiprocessing import Queue

from numpy import mean

from ants.core import read_transform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import sitkUInt8
from SimpleITK import sitkFloat32
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
from SimpleITK import AffineTransform
from SimpleITK import CenteredTransformInitializerFilter
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole
from SimpleITK import DisplacementFieldJacobianDeterminantFilter

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWaitRegistration
from Sisyphe.gui.dialogManualRegistration import DialogManualRegistration

__all__ = ['DialogRegistration',
           'DialogICBMNormalization',
           'DialogBatchRegistration',
           'DialogAsymmetry',
           'DialogEddyCurrentCorrection']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogRegistration -> DialogBatchRegistration
                                    -> DialogICBMNormalization
                                    -> DialogBatchRegistration
                                    -> DialogAsymmetry
                                    -> DialogEddyCurrentCorrection
"""

class DialogRegistration(QDialog):
    """
    DialogRegistration

    Description
    ~~~~~~~~~~~

    GUI dialog for linear registration (Rigid/Affine/DisplacementField).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistration

    Last revision: 22/05/2025
    """
    # Class method

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    @classmethod
    def calcMask(cls, vol, dilate=4):
        img = vol.getSITKImage()
        mask = img >= mean(vol.getNumpy().flatten())
        mask = BinaryDilate(mask, [dilate, dilate, dilate])
        mask = BinaryFillhole(mask)
        r = SisypheVolume()
        r.setSITKImage(mask)
        return r

    # Special method

    """
    Private attributes

    _fixedSelect        FileSelectionWidget
    _movingSelect       FileSelectionWidget
    _reg                str ('Rigid', 'Affine', 'DisplacementField')
    _stages             list[str], name of each stage
    _iters              list[list[int]], number of iter in each stage and multiresolution level
    _progbylevel        list[list[int]], progress value for each stage and multiresolution level
    _forigin            [float] * 3, copy of fixed volume origin
    _morigin            [float] * 3, copy of moving volume origin
    _trf                SimpleITK transform
    _dialog             DialogManualRegistration, check registration dialog
    _wait               DialogWait
    _fixedSelect        FileSelectionWidget
    _movingSelect       FileSelectionWidget
    _settings           FunctionSettingsWidget
    _resamplesettings   FunctionSettingsWidget
    _execute            QPushButton
    """

    def __init__(self, transform='Affine', parent=None):
        super().__init__(parent)

        # Init window

        self._reg = transform
        self.setWindowTitle('{} Registration'.format(self._reg))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init non-GUI attributes

        self._trf = None
        self._stages = None
        self._iters = None
        self._progbylevel = None
        self._convergence = None
        self._wait = DialogWaitRegistration(title='{} Registration'.format(self._reg))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(10, 0, 10, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._fixedSelect = FileSelectionWidget(parent=self)
        self._fixedSelect.filterSisypheVolume()
        self._fixedSelect.setTextLabel('Fixed volume')
        self._fixedSelect.setMinimumWidth(500)
        self._fixedSelect.setCurrentVolumeButtonVisibility(True)
        self._fixedSelect.FieldChanged.connect(self._updateFixed)

        self._movingSelect = FileSelectionWidget(parent=self)
        self._movingSelect.filterSisypheVolume()
        self._movingSelect.setTextLabel('Moving volume')
        self._movingSelect.alignLabels(self._fixedSelect)
        self._movingSelect.setMinimumWidth(500)
        self._movingSelect.setCurrentVolumeButtonVisibility(True)
        self._movingSelect.FieldChanged.connect(self._updateMoving)

        self._applyTo = QCheckBox('Apply transformation to')
        # noinspection PyUnresolvedReferences
        self._applyTo.clicked.connect(self._updateApplyToSelect)

        self._applyToSelect = FilesSelectionWidget(parent=self)
        self._applyToSelect.filterSisypheVolume()
        self._applyToSelect.setCurrentVolumeButtonVisibility(True)
        self._applyToSelect.setEnabled(False)
        self._applyToSelect.setVisible(False)

        self._settings = FunctionSettingsWidget('Registration', parent=self)
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.setVisible(True)
        self._settings.setSettingsButtonFunctionText()
        self._settings.setParameterVisibility('Batch', False)
        self._settings.setParameterVisibility('Rigid', self._reg == 'Rigid')
        self._settings.setParameterVisibility('Affine', self._reg == 'Affine')
        self._settings.setParameterVisibility('DisplacementField', self._reg == 'DisplacementField')
        self._settings.setParameterVisibility('Transform', self._reg == 'Transform')

        if self._reg in ('DisplacementField', 'Transform'):
            self._settings.getParameterWidget('ManualRegistration').setChecked(False)
            self._settings.setParameterVisibility('ManualRegistration', False)
        else:
            self._settings.setParameterVisibility('NonLinearMetric', False)
            self._settings.setParameterVisibility('Inverse', False)
            v = self._settings.getParameterValue('ManualRegistration')
            self._settings.getParameterWidget('ManualRegistration').setChecked(self._reg == 'Rigid' and v)
            self._settings.setParameterVisibility('ManualRegistration', self._reg == 'Rigid')

        self._resamplesettings = FunctionSettingsWidget('Resample', parent=self)
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(True)
        self._resamplesettings.setSettingsButtonFunctionText()
        self._resamplesettings.setParameterVisibility('NormalizationPrefix', False)
        self._resamplesettings.setParameterVisibility('NormalizationSuffix', False)
        self._resamplesettings.setParameterVisibility('Dialog', False)
        self._resamplesettings.getParameterWidget('Dialog').setChecked(False)

        self._layout.addWidget(self._fixedSelect)
        self._layout.addWidget(self._movingSelect)
        self._layout.addWidget(self._applyTo)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._applyToSelect)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._cancel = QPushButton('Cancel')
        # self._cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute {} registration'.format(self._reg))
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._fixedSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private methods

    def _updateWindowTitleBarColor(self, window):
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            scl = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(window, scl)
            QApplication.processEvents()

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        # self.setFixedSize(self.size())
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateApplyToSelect(self):
        self._applyToSelect.setVisible(self._applyTo.isChecked())

    def _updateFixed(self):
        if not self._fixedSelect.isEmpty() and not self._movingSelect.isEmpty(): self._execute.setEnabled(True)
        else: self._execute.setEnabled(False)

    def _updateMoving(self):
        self._applyToSelect.clearall()
        if not self._movingSelect.isEmpty():
            self._applyToSelect.setEnabled(True)
            v = SisypheVolume()
            v.load(self._movingSelect.getFilename())
            self._applyToSelect.filterSameFOV(v)
            self._execute.setEnabled(not self._fixedSelect.isEmpty())
        else:
            self._applyToSelect.setEnabled(False)
            self._execute.setEnabled(False)

    # Public methods

    def getFixedSelectionWidget(self):
        return self._fixedSelect

    def getMovingSelectionWidget(self):
        return self._movingSelect

    def getApplyToSelectionWidget(self):
        return self._applyToSelect

    def setFixed(self, v, editable=True):
        if isinstance(v, SisypheVolume): v = v.getFilename()
        if isinstance(v, str):
            if exists(v):
                self._fixedSelect.open(v)
                self._fixedSelect.setEnabled(editable)

    def setMoving(self, v, editable=True):
        if isinstance(v, SisypheVolume): v = v.getFilename()
        if isinstance(v, str):
            if exists(v):
                self._movingSelect.open(v)
                self._movingSelect.setEnabled(editable)

    def getFixed(self) -> str:
        return self._fixedSelect.getFilename()

    def getMoving(self) -> str:
        return self._movingSelect.getFilename()

    # < Revision 13/02/2025
    # add getParametersDict method
    def getParametersDict(self) -> dict:
        params = dict()
        params['registration'] = self._settings.getParametersDict()
        params['resample'] = self._resamplesettings.getParametersDict()
        return params
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add setParametersFromDict method
    def setParametersFromDict(self, params: dict):
        if 'registration' in params: self._settings.setParametersFromDict(params['registration'])
        if 'resample' in params: self._resamplesettings.setParametersFromDict(params['resample'])
    # Revision 13/02/2025 >

    def execute(self):
        if self._fixedSelect.isEnabled() and self._movingSelect.isEnabled(): self.hide()
        self._wait.open()
        """
        Load fixed (fvol) and moving (mvol) volumes
        Storing volume origins
        Set origins to default (0.0, 0.0, 0.0) before registration
        Set directions to default (1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0) before registration
        Registration algorithm used backward geometric tranform (from fixed to moving)
        with center of rotation at center of fixed image
        """
        fvol = SisypheVolume()
        mvol = SisypheVolume()
        self._wait.setInformationText('Load fixed volume...')
        fvol.load(self._fixedSelect.getFilename())
        self._wait.setInformationText('Load moving volume...')
        mvol.load(self._movingSelect.getFilename())
        # Store volume origins
        # noinspection PyUnusedLocal
        forigin = fvol.getOrigin()
        # noinspection PyUnusedLocal
        morigin = mvol.getOrigin()
        # Store volume directions
        # noinspection PyUnusedLocal
        fdirections = fvol.getDirections()
        # noinspection PyUnusedLocal
        mdirections = mvol.getDirections()
        # set volume origin to (0.0, 0.0, 0.0) before registration
        fvol.setDefaultOrigin()
        mvol.setDefaultOrigin()
        # set volume directions to default
        fvol.setDefaultDirections()
        mvol.setDefaultDirections()
        """
        Verify previous registration between volumes
        """
        if (fvol.getID() in mvol.getTransforms()) or \
                (mvol.getID() in fvol.getTransforms()):
            self._wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='These volumes have already been coregistered.'
                                'Would you like to perform another coregistration ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.No:
                self.done(QDialog.Rejected)
                return
            else:
                self._wait.open()
                # Remove previous registration transform
                if fvol.getID() in mvol.getTransforms(): mvol.getTransforms().remove(fvol.getID())
                if mvol.getID() in fvol.getTransforms(): fvol.getTransforms().remove(mvol.getID())
        """       
        Automatic fixed mask processing
        """
        if self._settings.getParameterValue('FixedMask'):
            mask = self.calcMask(fvol)
        else: mask = None
        """
        Estimating translations
        """
        self._trf = SisypheTransform()
        self._trf.setIdentity()
        c = self._settings.getParameterValue('Estimation')[0][0]
        if c == 'F':
            if not fvol.hasSameFieldOfView(mvol):
                self._wait.setInformationText('FOV center alignment...')
                f = CenteredTransformInitializerFilter()
                f.GeometryOn()
                img1 = Cast(fvol.getSITKImage(), sitkFloat32)
                img2 = Cast(mvol.getSITKImage(), sitkFloat32)
                trf = AffineTransform(f.Execute(img1, img2, self._trf.getSITKTransform()))
                self._trf.setSITKTransform(trf)
        elif c == 'C':
            self._wait.setInformationText('Center of mass alignment...')
            f = CenteredTransformInitializerFilter()
            f.MomentsOn()
            img1 = Cast(fvol.getSITKImage(), sitkFloat32)
            img2 = Cast(mvol.getSITKImage(), sitkFloat32)
            trf = AffineTransform(f.Execute(img1, img2, self._trf.getSITKTransform()))
            self._trf.setSITKTransform(trf)
        # Set center of rotation to fixed image center
        self._trf.setCenter(fvol.getCenter())
        """
        Manual registration and registration area definition
        """
        if self._settings.getParameterValue('ManualRegistration') and self._reg in ('Rigid', 'Affine'):
            dialog = DialogManualRegistration(fvol, mvol)
            if platform == 'win32':
                try: self._updateWindowTitleBarColor(dialog)
                except: pass
            dialog.setDialogToRegistration()
            trf = self._trf.getInverseTransform()
            dialog.setTranslations(trf.getTranslations())
            dialog.setRotations(trf.getRotations())
            if dialog.exec() == dialog.Accepted:
                trf.setTranslations(dialog.getTranslations())
                trf.setRotations(dialog.getRotations())
                trf.setCenter(mvol.getCenter())
                # Manual registration gives a forward geometric transform (from moving to fixed)
                # with center of rotation at center of moving image
                # 1. Invert geometric transform to backward (from fixed to moving)
                trf = trf.getInverseTransform()
                # 2. Convert tranform with center of rotation at center of fixed image
                self._trf = trf.getEquivalentTransformWithNewCenterOfRotation(fvol.getCenter())
                # intersection between automatic mask and the registration area
                area = dialog.getRegistrationBoxMaskArea()
                if area is not None:
                    if mask is None: mask = area
                    else:
                        r = Cast(area.getSITKImage() * mask.getSITKImage(), sitkUInt8)
                        mask.setSITKImage(r)
                QApplication.processEvents()
            else:
                self.done(QDialog.Rejected)
                return
        if self._trf is not None:
            """      
            Set parameters used to follow registration progression
            _stage          1 stage [linear stage] or 2 stages [linear stage, non linear stage]
            _iters          number of iterations on each multi-resolution level
            _progbylevel    wait bar progression at the end of each multi-resolution level
            _convergence    1e-value, convergence stop criteria, one for each stage
            """
            algo = self._settings.getParameterValue(self._reg)[0]
            if self._reg == 'Transform':
                if algo in ('AntsAffine', 'AntsFastAffine'): self._reg = 'Affine'
                else: self._reg = 'DisplacementField'
            self._convergence = 1e-6
            if self._reg == 'Rigid':
                self._stages = ['Rigid']
                if algo == 'Translation':
                    regtype = algo
                    self._stages = ['Translation']
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'FastRigid':
                    regtype = 'QuickRigid'
                    self._iters = [[20, 20, 1, 1]]
                    self._progbylevel = [[100, 200, 0, 0]]
                    self._convergence = [6]
                elif algo == 'DenseRigid':
                    regtype = algo
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsRigid':
                    regtype = 'antsRegistrationSyN[r]'
                    self._iters = [[1000, 500, 250, 100]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsFastRigid':
                    self._stages = ['Fast Rigid']
                    regtype = 'antsRegistrationSyNQuick[r]'
                    self._iters = [[1000, 500, 250, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                elif algo == 'BoldRigid':
                    regtype = 'BOLDRigid'
                    self._iters = [[100, 20]]
                    self._progbylevel = [[100, 200]]
                    self._convergence = [6]
                else:  # AntsFastRigid, default
                    self._stages = ['Fast Rigid']
                    regtype = 'antsRegistrationSyNQuick[r]'
                    self._iters = [[1000, 500, 250, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
            elif self._reg == 'Affine':
                self._stages = ['Affine']
                if algo == 'Similarity':
                    regtype = algo
                    self._stages = ['Similarity']
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'Affine':
                    regtype = algo
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'FastAffine':
                    regtype = 'AffineFast'
                    self._iters = [[2100, 1200, 1, 1]]
                    self._progbylevel = [[100, 200, 0, 0]]
                    self._convergence = [6]
                elif algo == 'DenseAffine':
                    regtype = 'TRSAA'
                    self._stages = ['Translation', 'Rigid', 'Similarity', 'Affine', 'Affine']
                    self._iters = [[2000, 2000, 1], [2000, 2000, 1], [2000, 2000, 1], [40, 20, 1], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 0], [100, 200, 0], [100, 200, 0], [100, 200, 0], [100, 200, 0]]
                    self._convergence = [6, 6, 6, 6, 6]
                elif algo == 'AntsAffine':
                    regtype = 'antsRegistrationSyN[a]'
                    self._stages = ['Rigid', 'Affine']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
                elif algo == 'AntsFastAffine':
                    self._stages = ['Fast Affine']
                    regtype = 'antsRegistrationSyNQuick[a]'
                    self._stages = ['Rigid', 'Affine']
                    self._iters = [[1000, 500, 250, 1], [1000, 500, 250, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'BoldAffine':
                    regtype = 'BOLDAffine'
                    self._iters = [[100, 20]]
                    self._progbylevel = [[100, 200]]
                    self._convergence = [6]
                else:  # AntsAffine, default
                    regtype = 'antsRegistrationSyN[a]'
                    self._stages = ['Rigid', 'Affine']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
            elif self._reg == 'DisplacementField':
                if algo == 'Elastic':
                    regtype = 'ElasticSyN'
                    self._stages = ['Affine', 'Elastic']
                    self._iters = [[2100, 1200, 200, 1], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 0]]
                    self._convergence = [6, 7]
                elif algo == 'DenseDiffeomorphic':
                    regtype = 'SyNAggro'
                    self._stages = ['Affine', 'Diffeomorphic']
                    self._iters = [[2100, 1200, 1200, 100], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 0]]
                    self._convergence = [6, 7]
                elif algo == 'CCDiffeomorphic':
                    regtype = 'SyNCC'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[2100, 1200, 1200, 1], [1200, 1200, 100], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400], [100, 200, 0]]
                    self._convergence = [6, 6, 7]
                elif algo == 'BoldDiffeomorphic':
                    regtype = 'SyNBold'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1200, 1200, 100], [200, 20], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200], [100, 200, 0]]
                    self._convergence = [6, 6, 7]
                elif algo == 'AntsSplineDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[s]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[b]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Affine', 'Spline Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[b]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[s]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsFastSplineDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyNQuick[s]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[b]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Affine', 'Fast Spline Diffeomorphic']
                    self._iters = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsFastDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyNQuick[b]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[s]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Affine', 'Fast Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 0]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsRigidSplineDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[sr]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[br]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Spline Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
                elif algo == 'AntsRigidDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[br]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[sr]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
                elif algo == 'AntsFastRigidSplineDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyNQuick[sr]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[br]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Fast Spline Diffeomorphic']
                    self._iters = [[1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'AntsFastRigidDiffeomorphic':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyNQuick[br]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[sr]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Fast Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'AntsSplineDiffeomorphicOnly':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[so]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[bo]'
                    # Revision 14/11/2024 >
                    self._stages = ['Spline Diffeomorphic']
                    self._iters = [[100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsDiffeomorphicOnly':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[bo]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyN[so]'
                    # Revision 14/11/2024 >
                    self._stages = ['Diffeomorphic']
                    self._iters = [[100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsFastSplineDiffeomorphicOnly':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyNQuick[so]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[bo]'
                    # Revision 14/11/2024 >
                    self._stages = ['Fast Spline Diffeomorphic']
                    self._iters = [[100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                elif algo == 'AntsFastDiffeomorphicOnly':
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[bo]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[so]'
                    # Revision 14/11/2024 >
                    self._stages = ['Fast Diffeomorphic']
                    self._iters = [[100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                else:  # Ants Fast Spline Diffeomorphic, default
                    # < Revision 14/11/2024
                    # regtype = 'antsRegistrationSyN[s]'
                    # s subtype transform is SyN, b is BSpline
                    regtype = 'antsRegistrationSyNQuick[b]'
                    # Revision 14/11/2024 >
                    self._stages = ['Rigid', 'Affine', 'Fast Spline Diffeomorphic']
                    self._iters = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6, 6]
            else: raise ValueError('Type of registration {} is not defined.'.format(self._reg))
            self._wait.setStages(self._stages)
            self._wait.setMultiResolutionIterations(self._iters)
            self._wait.setProgressByLevel(self._progbylevel)
            self._wait.setConvergenceThreshold(self._convergence)
            """
            Set custom parameters        
            """
            metric = list()
            m = self._settings.getParameterValue('LinearMetric')[0]
            if m == 'CC': metric.append('CC')
            elif m == 'MS': metric.append('meansquares')
            else: metric.append('mattes')
            m = self._settings.getParameterValue('NonLinearMetric')[0]
            if m == 'CC': metric.append('CC')
            elif m == 'MS': metric.append('meansquares')
            elif m == 'DEMONS': metric.append('demons')
            else: metric.append('mattes')
            sampling = self._settings.getParameterValue('SamplingRate')
            if sampling is None: sampling = 0.2
            """      
            Registration
            """
            self._wait.setInformationText('Registration initialization...')
            queue = Queue()
            stdout = join(fvol.getDirname(), 'stdout.log')
            reg = ProcessRegistration(fvol, mvol, mask, False, self._trf, regtype, metric, sampling, stdout, queue)
            try:
                reg.start()
                while reg.is_alive():
                    QApplication.processEvents()
                    if exists(stdout): self._wait.setAntsRegistrationProgress(stdout)
                    if self._wait.getStopped(): reg.terminate()
            except Exception as err:
                if reg.is_alive(): reg.terminate()
                if not self._wait.getStopped():
                    self._wait.hide()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Registration error: {}\n{}.'.format(type(err), str(err)))
                    self._wait.show()
            finally:
                # Remove temporary std::cout file
                if exists(stdout): remove(stdout)
            # noinspection PyUnreachableCode
            self._wait.buttonVisibilityOff()
            self._wait.progressVisibilityOff()
            trf = None
            if not queue.empty(): trf = queue.get()
            """
            Displacement field processing
            1. Convert affine transformation to displacement field
            2. Add Affine and Elastic/Diffeomorphic displacement fields
            """
            if trf is not None:
                self._trf.setAttributesFromFixedVolume(fvol)
                self._trf.setANTSTransform(read_transform(trf))
                # Set center of rotation to default (0.0, 0.0, 0.0)
                self._trf = self._trf.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                # Remove temporary ants affine transform
                if exists(trf): remove(trf)
                if self._reg == 'DisplacementField':
                    if not queue.empty():
                        """
                        Save displacement field
                        """
                        fld = queue.get()  # Displacement field nifti filename
                        if fld is not None:
                            if exists(fld):
                                self._wait.setInformationText('Save displacement field...')
                                # Open diffeomorphic displacement field
                                dfield = SisypheVolume()
                                dfield.loadFromNIFTI(fld, reorient=False)
                                dfield.acquisition.setSequenceToDisplacementField()
                                # debug:
                                #   dfield.setFilename(mvol.getFilename())
                                #   dfield.setFilenamePrefix('field_spline')
                                #   dfield.save()
                                dfield = dfield.cast('float64')
                                # Convert affine transform to affine displacement field
                                if not self._trf.isIdentity():
                                    self._trf.affineToDisplacementField(inverse=False)
                                    afield = self._trf.getDisplacementField()
                                    # debug:
                                    #   afield.setFilename(mvol.getFilename())
                                    #   afield.setFilenamePrefix('field_affine')
                                    #   afield.save()
                                    # Final displacement field = affine + diffeomorphic displacement fields
                                    field = afield + dfield
                                    field.acquisition.setSequenceToDisplacementField()
                                else: field = dfield
                                self._trf.copyFromDisplacementFieldImage(field)
                                # Save displacement field image
                                self._trf.setID(fvol)
                                self._trf.saveDisplacementField(mvol.getFilename())
                                # Remove temporary ants diffeomorphic displacement field
                                remove(fld)
                        """
                        Save inverse displacement field
                        """
                        fld = queue.get()  # Inverse displacement field nifti filename
                        if fld is not None:
                            if exists(fld):
                                if self._settings.getParameterValue('Inverse'):
                                    # Open diffeomorphic displacement field
                                    dfield = SisypheVolume()
                                    dfield.loadFromNIFTI(fld, reorient=False)
                                    dfield.acquisition.setSequenceToDisplacementField()
                                    dfield = dfield.cast('float64')
                                    # Resample diffeomorphic displacement field to moving image FOV
                                    t = SisypheTransform()
                                    t.setID(mvol)
                                    t.setIdentity()
                                    t.setAttributesFromFixedVolume(mvol)
                                    f = SisypheApplyTransform()
                                    f.setTransform(trf)
                                    f.setMoving(dfield)
                                    dfield = f.execute(dfield)
                                    # Convert affine transform to affine displacement field
                                    if not self._trf.isIdentity():
                                        t = self._trf.copy()
                                        t.setID(mvol)
                                        t.setAttributesFromFixedVolume(mvol)
                                        t.affineToDisplacementField(inverse=True)
                                        afield = trf.getDisplacementField()
                                        # Final displacement field = affine + diffeomorphic displacement fields
                                        field = afield + dfield
                                        field.acquisition.setSequenceToDisplacementField()
                                    else: field = dfield
                                    t.copyFromDisplacementFieldImage(field)
                                    # Save displacement field image
                                    t.setID(mvol)
                                    t.saveDisplacementField(fvol.getFilename())
                                # Remove temporary ants inverse diffeomorphic displacement field
                                remove(fld)
            """
            Check registration
            """
            resampled = None
            f = SisypheApplyTransform()
            if trf is not None:
                f.setMoving(mvol)
                if self._trf.isAffine():
                    # SisypheApplyTransform uses forward geometric transform
                    t = self._trf.getInverseTransform()
                    f.setTransform(t)
                else: f.setTransform(self._trf)
                interpol = self._resamplesettings.getParameterValue('Interpolator')
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
                resampled = f.execute(fixed=fvol, save=False, wait=self._wait)
                if self._settings.getParameterValue('CheckRegistration'):
                    self._wait.setInformationText('Check registration...')
                    # < Revision 22/05/2025
                    # dialog = DialogManualRegistration(fvol, resampled)
                    dialog = DialogManualRegistration(fvol, resampled, parent=self)
                    # Revision 22/05/2025 >
                    dialog.setDialogToCheck()
                    dialog.setWindowTitle('Check registration')
                    if platform == 'win32':
                        try: self._updateWindowTitleBarColor(dialog)
                        except: pass
                    self._wait.hide()
                    if dialog.exec() == QDialog.Rejected:
                        trf = None
                        mvol.getTransforms().remove(fvol)
                        fvol.getTransforms().remove(mvol)
                        mvol.saveTransforms()
                        fvol.saveTransforms()
                    dialog.close()
                    self._wait.show()
            """
            Restore volume origins/directions
            """
            # volume origin restoration
            fvol.setOrigin(forigin)
            mvol.setOrigin(morigin)
            if resampled is not None: resampled.setOrigin(forigin)
            # volume direction restoration
            fvol.setDirections(fdirections)
            mvol.setDirections(mdirections)
            if resampled is not None: resampled.setDirections(fdirections)
            """
            Resample moving volume
            """
            if trf is not None and resampled is not None:
                if self._settings.getParameterValue('Resample'):
                    dialog = self._resamplesettings.getParameterValue('Dialog')
                    if self.windowTitle()[0] == 'T':
                        prefix = self._resamplesettings.getParameterValue('NormalizationPrefix')
                        suffix = self._resamplesettings.getParameterValue('NormalizationSuffix')
                    else:
                        prefix = self._resamplesettings.getParameterValue('Prefix')
                        suffix = self._resamplesettings.getParameterValue('Suffix')
                    resampled.setFilename(mvol.getFilename())
                    resampled.setFilenamePrefix(prefix)
                    resampled.setFilenameSuffix(suffix)
                    if dialog:
                        self._wait.hide()
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled volume', resampled.getFilename(),
                                                               filter='PySisyphe volume (*.xvol)')[0]
                        QApplication.processEvents()
                        self._wait.show()
                        if filename:
                            filename = abspath(filename)
                            chdir(dirname(filename))
                            resampled.setFilename(filename)
                            self._wait.setInformationText('Save {}...'.format(resampled.getBasename()))
                            resampled.setFilename(filename)
                    resampled.save()
                    if self._applyToSelect.filenamesCount() > 0:
                        filenames = self._applyToSelect.getFilenames()
                        for filename in filenames:
                            img = SisypheVolume()
                            img.load(filename)
                            f.setMoving(img)
                            f.execute(fixed=fvol, save=True, dialog=dialog,
                                      prefix=prefix, suffix=suffix, wait=self._wait)
                else:
                    if self._applyToSelect.filenamesCount() > 0:
                        filenames = self._applyToSelect.getFilenames()
                        for filename in filenames:
                            img = SisypheVolume()
                            img.load(filename)
                            img.setID(mvol.getID())
                            f.updateVolumeTransformsFromMoving(img)
                            img.save()
                if exists(trf): remove(trf)
        """
        Exit  
        """
        self._wait.close()
        # _movingSelect is not enabled in DialogBatchRegistration instance
        # The question of doing another registration is not asked in batch mode
        if self._fixedSelect.isEnabled() and self._movingSelect.isEnabled():
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform another coregistration ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._fixedSelect.clear()
                self._movingSelect.clear()
                self._applyToSelect.clearall()
                self.show()
            else: self.accept()

    def showEvent(self, a0):
        super().showEvent(a0)
        self._center(None)


class DialogICBMNormalization(DialogRegistration):
    """
    DialogICBMNormalization

    Description
    ~~~~~~~~~~~

    GUI dialog for spatial normalization i.e. displacement field registration to template.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistration -> DialogICBMNormalization
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(transform='Transform', parent=parent)

        self.setWindowTitle('ICBM Normalization')

        self._fixedSelect.setTextLabel('Template')
        self._fixedSelect.alignLabels(self._movingSelect)
        self._fixedSelect.filterICBM()
        self._movingSelect.FieldChanged.connect(self._updateTemplate)
        self.layout().removeWidget(self._fixedSelect)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(1, self._fixedSelect)

        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)

        self._resamplesettings.setParameterVisibility('Prefix', False)
        self._resamplesettings.setParameterVisibility('Suffix', False)
        self._resamplesettings.setParameterVisibility('NormalizationPrefix', True)
        self._resamplesettings.setParameterVisibility('NormalizationSuffix', True)

    # Private method

    def _updateTemplate(self):
        filename = self._movingSelect.getFilename()
        if exists(filename):
            v = SisypheVolume()
            v.load(filename)
            sequence = v.getAcquisition().getSequence()
            if sequence in (SisypheAcquisition.HMPAO, SisypheAcquisition.ECD): sequence = SisypheAcquisition.getNMModalityTag()
            elif sequence == SisypheAcquisition.FDG: sequence = SisypheAcquisition.getPTModalityTag()
            else:
                if v.getAcquisition().isPT(): sequence = SisypheAcquisition.getPTModalityTag()
                elif v.getAcquisition().isNM(): sequence = SisypheAcquisition.getNMModalityTag()
            settings = SisypheSettings()
            if ('Templates', sequence) in settings:
                template = settings.getFieldValue('Templates', sequence)
                if template is not None and len(template) > 0:
                    if template[0] == '/': template = template[1:]
                import Sisyphe.templates
                filename = join(dirname(abspath(Sisyphe.templates.__file__)), template)
                if exists(filename): self._fixedSelect.open(filename)
                else:
                    messageBox(self,
                               'ICBM Normalization',
                               text='No default template for {} sequence.'.format(sequence))
                settings = SisypheFunctionsSettings()
                if sequence == 'T1':
                    t = settings.getFieldValue('T1Normalization', 'Transform')[0]
                    m1 = settings.getFieldValue('T1Normalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('T1Normalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('T1Normalization', 'SamplingRate')
                elif sequence == 'T2':
                    t = settings.getFieldValue('T2Normalization', 'Transform')[0]
                    m1 = settings.getFieldValue('T2Normalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('T2Normalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('T2Normalization', 'SamplingRate')
                elif sequence == 'PD':
                    t = settings.getFieldValue('PDNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('PDNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('PDNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('PDNormalization', 'SamplingRate')
                elif sequence == 'PT':
                    t = settings.getFieldValue('PTNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('PTNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('PTNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('PTNormalization', 'SamplingRate')
                elif sequence == 'NM':
                    t = settings.getFieldValue('NMNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('NMNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('NMNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('NMNormalization', 'SamplingRate')
                elif sequence == 'GM':
                    t = settings.getFieldValue('GMNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('GMNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('GMNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('GMNormalization', 'SamplingRate')
                elif sequence == 'WM':
                    t = settings.getFieldValue('WMNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('WMNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('WMNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('WMNormalization', 'SamplingRate')
                elif sequence == 'CSF':
                    t = settings.getFieldValue('CSFNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('CSFNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('CSFNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('CSFNormalization', 'SamplingRate')
                elif sequence == 'CT':
                    t = settings.getFieldValue('CTNormalization', 'Transform')[0]
                    m1 = settings.getFieldValue('CTNormalization', 'LinearMetric')[0]
                    m2 = settings.getFieldValue('CTNormalization', 'NonLinearMetric')[0]
                    r = settings.getFieldValue('CTNormalization', 'SamplingRate')
                else: raise ValueError('Invalid sequence {}.'.format(sequence))
                self._settings.getParameterWidget('Transform').setCurrentText(t)
                self._settings.getParameterWidget('LinearMetric').setCurrentText(m1)
                self._settings.getParameterWidget('NonLinearMetric').setCurrentText(m2)
                self._settings.getParameterWidget('SamplingRate').setValue(r)
            else:
                messageBox(self,
                           'ICBM Normalization',
                           text='No default template for {} sequence.'.format(sequence))


class DialogBatchRegistration(DialogRegistration):
    """
    DialogBatchRegistration

    Description
    ~~~~~~~~~~~

    GUI dialog for batch registration.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistration -> DialogBatchRegistration
    """

    # Special method

    """
    Private attributes

    _batch  FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(transform='Rigid', parent=parent)

        self.setWindowTitle('Batch registration')

        self.layout().removeWidget(self._fixedSelect)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(1, self._fixedSelect)

        self._movingSelect.setVisible(False)
        self._movingSelect.setEnabled(False)
        self._applyTo.setVisible(False)
        self._settings.setParameterVisibility('Batch', True)
        self._settings.getParameterWidget('Batch').currentIndexChanged.connect(self._updateParameters)

        self._batch = FilesSelectionWidget(parent=self)
        self._batch.filterSisypheVolume()
        self._batch.setTextLabel('Moving volumes')
        self._batch.setCurrentVolumeButtonVisibility(True)
        self._batch.FieldChanged.connect(self._updateFixed)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(2, self._batch)

        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)
        self._settings.getParameterWidget('CheckRegistration').setChecked(False)
        self._settings.setParameterVisibility('CheckRegistration', False)

    # Private method

    def _updateFixed(self):
        if not self._fixedSelect.isEmpty() and not self._batch.isEmpty(): self._execute.setEnabled(True)
        else: self._execute.setEnabled(False)

    def _updateParameters(self, index):
        if index in (0, 1):
            if index == 0:
                self._reg = 'Rigid'
                self._settings.setParameterVisibility('Rigid', True)
                self._settings.setParameterVisibility('Affine', False)
                self._settings.setParameterVisibility('DisplacementField', False)
            else:
                self._reg = 'Affine'
                self._settings.setParameterVisibility('Rigid', False)
                self._settings.setParameterVisibility('Affine', True)
                self._settings.setParameterVisibility('DisplacementField', False)
            self._settings.setParameterVisibility('NonLinearMetric', False)
        else:
            self._reg = 'DisplacementField'
            self._settings.setParameterVisibility('Rigid', False)
            self._settings.setParameterVisibility('Affine', False)
            self._settings.setParameterVisibility('DisplacementField', True)
            self._settings.setParameterVisibility('NonLinearMetric', True)

    # Public method

    def getBatchSelectionWidget(self):
        return self._batch

    def execute(self):
        if self._batch.filenamesCount() > 0:
            filenames = self._batch.getFilenames()
            index = 0
            for filename in filenames:
                self._batch.setSelectionTo(index)
                self._movingSelect.open(filename)
                try: super().execute()
                except Exception as err:
                    messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                    break
                index += 1
            self._batch.clearall()
            self._fixedSelect.clear()


class DialogAsymmetry(DialogRegistration):
    """
    DialogAsymmetry

    Description
    ~~~~~~~~~~~

    GUI dialog for asymmetry analysis.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistration -> DialogAsymmetry
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(transform='DisplacementField', parent=parent)

        self.setWindowTitle('Asymmetry analysis')

        self.layout().removeWidget(self._fixedSelect)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(1, self._fixedSelect)

        self._fixedSelect.setVisible(False)
        self._movingSelect.setVisible(False)
        self._movingSelect.setEnabled(False)
        self._applyTo.setVisible(False)
        self._settings.setParameterVisibility('Batch', False)

        self._batch = FilesSelectionWidget(parent=self)
        self._batch.setMinimumWidth(500)
        self._batch.filterSisypheVolume()
        self._batch.setTextLabel('Volumes')
        self._batch.setCurrentVolumeButtonVisibility(True)
        self._batch.FieldChanged.connect(self._updateBatch)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(2, self._batch)

        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)
        self._settings.getParameterWidget('CheckRegistration').setChecked(False)
        self._settings.setParameterVisibility('CheckRegistration', False)
        self._settings.setParameterVisibility('LinearMetric', False)
        self._settings.getParameterWidget('LinearMetric').setCurrentText('MS')
        self._settings.setParameterVisibility('NonLinearMetric', False)
        self._settings.getParameterWidget('NonLinearMetric').setCurrentText('MS')
        self._settings.setParameterVisibility('Resample', False)
        self._settings.getParameterWidget('Resample').setChecked(False)
        self._settings.setParameterVisibility('Inverse', False)
        self._settings.getParameterWidget('Inverse').setChecked(False)
        self._resamplesettings.setVisible(False)

        screen = QApplication.primaryScreen().geometry()
        self._batch.setMinimumWidth(int(screen.width() * 0.33))

    # Private method

    def _updateBatch(self):
        self._execute.setEnabled(not self._batch.isEmpty())

    # Public methods

    def getBatchSelectionWidget(self):
        return self._batch

    def execute(self):
        if self._batch.filenamesCount() > 0:
            filenames = self._batch.getFilenames()
            index = 0
            settings = FunctionSettingsWidget('DisplacementFieldJacobianDeterminant')
            for filename in filenames:
                self._batch.setSelectionTo(index)
                """
                flip fixed volume = moving volume
                """
                v = SisypheVolume()
                v.load(filename)
                self._fixedSelect.open(v.getFilename())
                v.flip([True, False, False])
                v.setFilenamePrefix('flip')
                v.save()
                self._movingSelect.open(v.getFilename())
                """
                registration
                """
                try: super().execute()
                except Exception as err:
                    messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                    continue
                """
                displacement field jacobian processing
                """
                path = split(v.getFilename())
                fieldname = join(path[0], 'field_' + path[1])
                if exists(fieldname):
                    v = SisypheVolume()
                    v.load(fieldname)
                    f = DisplacementFieldJacobianDeterminantFilter()
                    try: field = f.Execute(Cast(v.getSITKImage(), sitkVectorFloat64))
                    except Exception as err:
                        messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                        index += 1
                        continue
                    r = SisypheVolume()
                    r.setSITKImage(field)
                    r.setFilename(fieldname)
                    prefix = settings.getParameterValue('Prefix')
                    suffix = settings.getParameterValue('Suffix')
                    r.setFilenamePrefix(prefix)
                    r.setFilenameSuffix(suffix)
                    r.getAcquisition().setSequenceToAlgebraMap()
                    # noinspection PyArgumentList
                    r.setIdentity(v.getIdentity())
                    r.save()
                index += 1
            self._batch.clearall()


class DialogEddyCurrentCorrection(DialogRegistration):
    """
    DialogEddyCurrentCorrection

    Description
    ~~~~~~~~~~~

    GUI dialog for eddy current correction.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistration -> DialogEddyCurrentCorrection
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(transform='Transform', parent=parent)

        self.setWindowTitle('Eddy current correction')

        self.layout().removeWidget(self._fixedSelect)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(1, self._fixedSelect)

        self._fixedSelect.setTextLabel('B0 volume')
        self._fixedSelect.filterSameModality(SisypheAcquisition.getMRModalityTag())
        self._movingSelect.setVisible(False)
        self._movingSelect.setEnabled(False)
        self._applyTo.setVisible(False)
        self._settings.setParameterVisibility('Batch', False)

        self._batch = FilesSelectionWidget(parent=self)
        self._batch.filterSisypheVolume()
        self._batch.filterSameModality(SisypheAcquisition.getMRModalityTag())
        self._batch.filterSameSequence(SisypheAcquisition.DWI)
        self._batch.setTextLabel('Diffusion-weighted volume(s)')
        self._batch.setCurrentVolumeButtonVisibility(True)
        self._batch.setEnabled(False)
        self._batch.FieldChanged.connect(self._updateBatch)
        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(2, self._batch)

        self._eddy = SisypheFunctionsSettings()
        self._settings.getParameterWidget('Transform').clear()
        self._settings.getParameterWidget('Transform').addItems(self._eddy.getFieldValue('EddyCurrent', 'Transform'))
        self._settings.getParameterWidget('LinearMetric').setCurrentText(self._eddy.getFieldValue('EddyCurrent', 'LinearMetric')[0])
        self._settings.getParameterWidget('NonLinearMetric').setCurrentText(self._eddy.getFieldValue('EddyCurrent', 'NonLinearMetric')[0])
        self._settings.getParameterWidget('SamplingRate').setValue(self._eddy.getFieldValue('EddyCurrent', 'SamplingRate'))
        self._settings.setParameterVisibility('Estimation', False)
        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)
        self._settings.getParameterWidget('CheckRegistration').setChecked(False)
        self._settings.setParameterVisibility('CheckRegistration', False)
        self._settings.setParameterVisibility('Resample', False)
        self._settings.getParameterWidget('Resample').setChecked(True)
        self._settings.setParameterVisibility('Inverse', False)
        self._settings.getParameterWidget('Inverse').setChecked(False)
        self._resamplesettings.getParameterWidget('Prefix').setText(self._eddy.getFieldValue('EddyCurrent', 'Prefix'))
        self._resamplesettings.getParameterWidget('Suffix').setText(self._eddy.getFieldValue('EddyCurrent', 'Suffix'))

    # Private method

    def _updateFixed(self):
        self._batch.clearall()
        self._execute.setEnabled(False)
        filename = self._fixedSelect.getFilename()
        if exists(filename):
            v = SisypheVolume()
            v.load(filename)
            self._batch.filterSameFOV(v)
            self._batch.setEnabled(True)
        else:
            self._fixedSelect.clear(signal=False)
            self._batch.setEnabled(False)

    def _updateBatch(self):
        self._execute.setEnabled(not self._batch.isEmpty())

    # Public methods

    def getBatchSelectionWidget(self):
        return self._batch

    def execute(self):
        filenames = self._batch.getFilenames()
        index = 0
        for filename in filenames:
            self._batch.setSelectionTo(index)
            self._movingSelect.open(filename)
            try: super().execute()
            except Exception as err:
                messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                break
            index += 1
        self._batch.clearall()
        self._fixedSelect.clear()
