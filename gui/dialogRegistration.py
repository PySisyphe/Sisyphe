"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

import sys

from os import dup
from os import dup2
from os import remove
from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import exists

from multiprocessing import Process
from multiprocessing import Queue

from numpy import mean

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from ants.core import from_numpy
from ants.core import read_transform
from ants.core import write_transform
from ants.registration import registration

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
from SimpleITK import VersorRigid3DTransform
from SimpleITK import CenteredTransformInitializerFilter
from SimpleITK import CenteredVersorTransformInitializerFilter
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.gui.dialogWait import DialogWaitRegistration
from Sisyphe.gui.dialogManualRegistration import DialogManualRegistration


"""
    Classes hierarchy

        CaptureStdout
        Process -> ProcessRegistration
        QDialog -> DialogRegistration -> DialogBatchRegistration
                                      -> DialogICBMNormalization
"""


class CapturedStdout:
    """
        CaptureStdout

        Description

            Class to redirect std::cout from the C++ registration
            function (ants library) to a text file. Used to follow progress

        Inheritance

        Private attributes

            prevfd      file
            prev        file
            _filename   str

        Public methods

            inherited Process methods
    """

    # Special methods

    def __init__(self, filename):
        self.prevfd = None
        self.prev = None
        self._filename = filename

    def __enter__(self):
        F = open(self._filename, 'w')
        self.prevfd = dup(sys.stdout.fileno())
        dup2(F.fileno(), sys.stdout.fileno())
        self.prev = sys.stdout
        # sys.stdout = fdopen(self.prevfd, "w")
        return F

    def __exit__(self, exc_type, exc_value, traceback):
        dup2(self.prevfd, self.prev.fileno())
        sys.stdout = self.prev


class ProcessRegistration(Process):
    """
        ProcessRegistration

        Description

            Multiprocessing Process class for ants registration function.

        Inheritance

            Process -> ProcessRegistration

        Private attributes

            _fixed      SisypheVolume
            _moving     SisypheVolume
            _mask       SisypheVolume
            _regtype    str
            _transform  SisypheTransform
            _verbose    bool
            _stdout     str
            _result     Queue

        Public methods

            run()       override

            inherited Process methods
    """
    # Special method

    def __init__(self, fixed, moving, mask, trf, regtype, metric, step, flow, iters, verbose, stdout, queue):
        Process.__init__(self)
        self._fixed = fixed.getNumpy(defaultshape=False).astype('float32')
        self._moving = moving.getNumpy(defaultshape=False).astype('float32')
        self._mask = mask.getNumpy(defaultshape=False)
        self._fspacing = fixed.getSpacing()
        self._mspacing = moving.getSpacing()
        self._transform = join(moving.getDirname(), 'temp.mat')
        write_transform(trf.getANTSTransform(), self._transform)
        self._regtype = regtype
        self._metric = metric
        self._step = step
        self._flow = flow
        self._iters = iters
        self._verbose = verbose
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        try:
            fixed = from_numpy(self._fixed, spacing=self._fspacing)
            moving = from_numpy(self._moving,spacing=self._mspacing)
            mask = from_numpy(self._mask, spacing=self._fspacing)
            """         
                registration return
                r = {'warpedmovout': ANTsImage,
                     'warpedfixout': ANTsImage,
                     'fwdtransforms': str,
                     'invtransforms': str} 
                fwdtransforms: transformation filename
                invtransforms: inverse transformation filename               
            """
            with CapturedStdout(self._stdout) as F:
                """
                    ants.registration(fixed, moving, type_of_transform="SyN", initial_transform=None, outprefix="",
                    mask=None, grad_step=0.2, flow_sigma=3, total_sigma=0, aff_metric="mattes", aff_sampling=32,
                    aff_random_sampling_rate=0.2, syn_metric="mattes", syn_sampling=32, reg_iterations=(40, 20, 0),
                    aff_iterations=(2100, 1200, 1200, 10), aff_shrink_factors=(6, 4, 2, 1), 
                    aff_smoothing_sigmas=(3, 2, 1, 0), write_composite_transform=False, random_seed=None,
                    verbose=False, multivariate_extras=None, restrict_transformation=None, smoothing_in_mm=False,
                    **kwargs)
                    
                    grad_step: gradient step size
                    flow_sigma: smoothing for update field
                    ( total_sigma: smoothing for total field )
                    ( aff_metric: the metric for the affine part (GC, mattes, meansquares) )
                    ( aff_sampling: the nbins or radius parameter for the syn metric )
                    ( aff_random_sampling_rate: the fraction of points used to estimate the metric )
                    syn_metric: the metric for the syn part (CC, mattes, meansquares, demons)
                    ( syn_sampling: the nbins or radius parameter for the syn metric )
                    reg_iterations : vector of iterations for syn
                    ( aff_iterations : vector of iterations for linear registration (translation, rigid, affine) )
                    ( aff_shrink_factors : vector of multi-resolution shrink factors for linear registration )
                    ( aff_smoothing_sigmas : vector of multi-resolution smoothing factors for linear registration )
                    ( smoothing_in_mm : boolean; currently only impacts low dimensional registration )
                """
                r = registration(fixed, moving, type_of_transform=self._regtype,
                                 initial_transform=self._transform, mask=mask,
                                 syn_metric=self._metric, grad_step=self._step,
                                 flow_sigma=self._flow, reg_iterations=self._iters,
                                 verbose=self._verbose)
            if exists(self._transform): remove(self._transform)
            if len(r['fwdtransforms']) == 1:
                self._result.put(r['fwdtransforms'][0])  # Affine trf
                # Remove temporary ants inverse affine transform
                if exists(r['invtransforms'][0]):
                    if r['invtransforms'][0] != r['fwdtransforms'][0]:
                        remove(r['invtransforms'][0])
            else:
                self._result.put(r['fwdtransforms'][1])  # Affine trf
                self._result.put(r['fwdtransforms'][0])  # Displacement field image
                self._result.put(r['invtransforms'][1])  # Displacement field image
                # Remove temporary ants inverse affine transform
                if exists(r['invtransforms'][0]):
                    if r['invtransforms'][0] != r['fwdtransforms'][1]:
                        remove(r['invtransforms'][0])
        except: self.terminate()


class DialogRegistration(QDialog):
    """
        DialogRegistration

        Description

            GUI dialog for linear registration (Rigid/Affine/DisplacementField).

        Inheritance

            QDialog -> DialogRegistration

        Private attributes

            _fixedSelect        FileSelectionWidget
            _movingSelect       FileSelectionWidget
            _reg                str ('Rigid', 'Affine', 'DisplacementField')
            _stages             list(str), name of each stage
            _iters              list(list(int)), number of iter in each stage and multiresolution level
            _progbylevel        list(list(int)), progress value for each stage and multiresolution level
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

        Public methods

            FileSelectionWidget = getFixedSelectionWidget()
            FileSelectionWidget = getMovingSelectionWidget()
            FileSelectionWidget = getApplyToSelectionWidget()
            setFixed(str or SisypheVolume, editable=bool)
            setMoving(str or SisypheVolume, editable=bool)
            execute()

            inherited QDialog methods
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

    def __init__(self, transform='Affine', parent=None):
        super().__init__(parent)

        # Init window

        self._reg = transform
        self.setWindowTitle('{} Registration'.format(self._reg))
        self.setFixedWidth(500)

        # Init non-GUI attributes

        self._trf = None
        self._dialog = None
        self._stages = None
        self._iters = None
        self._progbylevel = None
        self._convergence = None
        self._forigin = None
        self._morigin = None
        self._wait = DialogWaitRegistration(title='{} Registration'.format(self._reg), parent=self)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._fixedSelect = FileSelectionWidget()
        self._fixedSelect.filterSisypheVolume()
        self._fixedSelect.setTextLabel('   Fixed volume')
        self._fixedSelect.setMinimumWidth(500)
        self._fixedSelect.setCurrentVolumeButtonVisibility(True)
        self._fixedSelect.FieldChanged.connect(self._updateFixed)

        self._movingSelect = FileSelectionWidget()
        self._movingSelect.filterSisypheVolume()
        self._movingSelect.setTextLabel('Moving volume')
        self._movingSelect.setMinimumWidth(500)
        self._movingSelect.setCurrentVolumeButtonVisibility(True)
        self._movingSelect.FieldChanged.connect(self._updateMoving)

        self._applyTo = QCheckBox('Apply transformation to')
        self._applyTo.clicked.connect(self._updateApplyToSelect)

        self._applyToSelect = FilesSelectionWidget()
        self._applyToSelect.filterSisypheVolume()
        self._applyToSelect.setCurrentVolumeButtonVisibility(True)
        self._applyToSelect.setEnabled(False)
        self._applyToSelect.setVisible(False)

        self._settings = FunctionSettingsWidget('Registration')
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.setVisible(True)
        self._settings.setSettingsButtonFunctionText()
        self._settings.setParameterVisibility('Rigid', self._reg == 'Rigid')
        self._settings.setParameterVisibility('Affine', self._reg == 'Affine')
        self._settings.setParameterVisibility('DisplacementField', self._reg == 'DisplacementField')

        w = self._settings.getParameterWidget('CustomParameters')
        w.toggled.connect(self._customToggled)
        self._customToggled(self._settings.getParameterValue('CustomParameters'))

        if self._reg == 'DisplacementField':
            self._settings.getParameterWidget('ManualRegistration').setChecked(False)
            self._settings.setParameterVisibility('ManualRegistration', False)
            self._settings.setParameterVisibility('CustomParameters', True)
        else:
            self._settings.setParameterVisibility('CustomParameters', False)
            self._settings.setParameterVisibility('Metric', False)
            self._settings.setParameterVisibility('GradientStep', False)
            self._settings.setParameterVisibility('FlowSigma', False)
            self._settings.setParameterVisibility('LowResolutionIterations', False)
            self._settings.setParameterVisibility('MediumResolutionIterations', False)
            self._settings.setParameterVisibility('HighResolutionIterations', False)

        self._resamplesettings = FunctionSettingsWidget('Resample')
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(True)
        self._resamplesettings.setSettingsButtonFunctionText()

        self._layout.addWidget(self._fixedSelect)
        self._layout.addWidget(self._movingSelect)
        self._layout.addWidget(self._applyTo)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._applyToSelect)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute {} registration'.format(self._reg))
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

    # Private methods

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateApplyToSelect(self):
        self._applyToSelect.setVisible(self._applyTo.isChecked())

    def _updateFixed(self):
        if not self._fixedSelect.isEmpty() and not self._movingSelect.isEmpty():
            self._execute.setEnabled(True)
        else:
            self._execute.setEnabled(False)

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

    def _customToggled(self, v):
        self._settings.setParameterVisibility('Metric', v)
        self._settings.setParameterVisibility('GradientStep', v)
        self._settings.setParameterVisibility('FlowSigma', v)
        self._settings.setParameterVisibility('LowResolutionIterations', v)
        self._settings.setParameterVisibility('MediumResolutionIterations', v)
        self._settings.setParameterVisibility('HighResolutionIterations', v)

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

    def execute(self):
        self._wait.open()
        """
            Load fixed (fvol) and moving (mvol) volumes
            Storing volume origins
            Set origins to (0.0, 0.0, 0.0) before registration
        """
        fvol = SisypheVolume()
        mvol = SisypheVolume()
        self._wait.setInformationText('Load fixed volume...')
        fvol.load(self._fixedSelect.getFilename())
        self._wait.setInformationText('Load moving volume...')
        mvol.load(self._movingSelect.getFilename())
        # Storing volume origins
        self._forigin = fvol.getOrigin()
        self._morigin = mvol.getOrigin()
        # Set origin to (0.0, 0.0, 0.0) before registration
        fvol.setDefaultOrigin()
        mvol.setDefaultOrigin()
        """
            Verify previous registration between volumes
        """
        if (fvol.getID() in mvol.getTransforms()) or \
                (mvol.getID() in fvol.getTransforms()):
            self._wait.hide()
            r = QMessageBox.question(self, self.windowTitle(),
                                     'These volumes have already been registered.'
                                     'Do you want to make a new registration ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.No:
                self.done(QDialog.Rejected)
                return
            else:
                self._wait.open()
                # Remove previous registration transform
                if fvol.getID() in mvol.getTransforms(): mvol.getTransforms().remove(fvol.getID())
                if mvol.getID() in fvol.getTransforms(): fvol.getTransforms().remove(mvol.getID())
        """       
            Automatic fixed mask calculation
        """
        if self._settings.getParameterValue('FixedMask'):
            self._wait.setInformationText('Calculate {} mask...'.format(fvol.getBasename()))
            mask = self.calcMask(fvol)
        else: mask = None
        """
            Estimating translations/rotations
        """
        self._trf = SisypheTransform()
        self._trf.setIdentity()
        c = self._settings.getParameterValue('Estimation')[0]
        if c[0] == 'R':
            self._wait.setInformationText('Rotations and translations estimation...')
            f = CenteredVersorTransformInitializerFilter()
            f.ComputeRotationOn()
            img1 = Cast(fvol.getSITKImage(), sitkFloat32)
            img2 = Cast(mvol.getSITKImage(), sitkFloat32)
            trf = VersorRigid3DTransform(f.Execute(img1, img2, self._trf.getSITKTransform()))
            self._trf.setSITKTransform(trf)
        elif c[0] == 'T':
            self._wait.setInformationText('Translations estimation...')
            f = CenteredTransformInitializerFilter()
            img1 = Cast(fvol.getSITKImage(), sitkFloat32)
            img2 = Cast(mvol.getSITKImage(), sitkFloat32)
            trf = AffineTransform(f.Execute(img1, img2, self._trf.getSITKTransform()))
            self._trf.setSITKTransform(trf)
        """
            Manual registration and registration area definition
        """
        if self._settings.getParameterValue('ManualRegistration') and self._reg in ('Rigid', 'Affine'):
            self._dialog = DialogManualRegistration(fvol, mvol, parent=self)
            self._dialog.setDialogToRegistration()
            trf = self._trf.getInverseTransform()
            self._dialog.setTranslations(trf.getTranslations())
            self._dialog.setRotations(trf.getRotations())
            if self._dialog.exec() == self._dialog.Accepted:
                trf.setTranslations(self._dialog.getTranslations())
                trf.setRotations(self._dialog.getRotations())
                self._trf = trf.getInverseTransform()
                # combine (intersection) automatic mask and the registration area
                area = self._dialog.getRegistrationBoxMaskArea()
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
                _proglevel      wait bar progression at the end of each multi-resolution level
                _convergence    1e-value, convergence stop criteria, one for each stage      
            """
            algo = self._settings.getParameterValue(self._reg)[0]
            self._convergence = 1e-6
            if self._reg == 'Rigid':
                self._stages = ['Rigid']
                if algo == 'Translation':
                    regtype = algo
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
                    regtype = 'antsRegistrationSyNQuick[r]'
                    self._iters = [[1000, 500, 250, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                elif algo == 'BoldRigid':
                    regtype = 'BOLDRigid'
                    self._iters = [[100, 20]]
                    self._progbylevel = [[100, 200]]
                    self._convergence = [6]
                else:  # Rigid
                    regtype = algo
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
            elif self._reg == 'Affine':
                self._stages = ['Affine']
                if algo == 'Similarity':
                    regtype = algo
                    self._stages = ['Similarity']
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'FastAffine':
                    regtype = 'AffineFast'
                    self._stages = ['Affine']
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
                    regtype = 'antsRegistrationSyNQuick[a]'
                    self._stages = ['Rigid', 'Affine']
                    self._iters = [[1000, 500, 250, 1], [1000, 500, 250, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'BoldAffine':
                    regtype = 'BOLDAffine'
                    self._iters = [100, 20]
                    self._progbylevel = [[100, 200]]
                    self._convergence = [6]
                else:  # Affine
                    regtype = algo
                    self._iters = [[2100, 1200, 1200, 10]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
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
                    regtype = 'antsRegistrationSyN[s]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsDiffeomorphic':
                    regtype = 'antsRegistrationSyN[b]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsFastSplineDiffeomorphic':
                    regtype = 'antsRegistrationSyNQuick[s]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsFastDiffeomorphic':
                    regtype = 'antsRegistrationSyNQuick[b]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 0]]
                    self._convergence = [6, 6, 6]
                elif algo == 'AntsRigidSplineDiffeomorphic':
                    regtype = 'antsRegistrationSyN[sr]'
                    self._stages = ['Rigid', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
                elif algo == 'AntsRigidDiffeomorphic':
                    regtype = 'antsRegistrationSyN[br]'
                    self._stages = ['Rigid', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                    self._convergence = [6, 6]
                elif algo == 'AntsFastRigidSplineDiffeomorphic':
                    regtype = 'antsRegistrationSyNQuick[sr]'
                    self._stages = ['Rigid', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'AntsFastRigidDiffeomorphic':
                    regtype = 'antsRegistrationSyNQuick[br]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[1000, 500, 250, 100], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 0]]
                    self._convergence = [6, 6]
                elif algo == 'AntsSplineDiffeomorphicOnly':
                    regtype = 'antsRegistrationSyN[so]'
                    self._stages = ['Diffeomorphic']
                    self._iters = [[100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsDiffeomorphicOnly':
                    regtype = 'antsRegistrationSyN[bo]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[100, 70, 50, 20]]
                    self._progbylevel = [[100, 200, 400, 800]]
                    self._convergence = [6]
                elif algo == 'AntsFastSplineDiffeomorphicOnly':
                    regtype = 'antsRegistrationSyNQuick[so]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                elif algo == 'AntsFastDiffeomorphicOnly':
                    regtype = 'antsRegistrationSyNQuick[bo]'
                    self._stages = ['Rigid', 'Affine', 'Diffeomorphic']
                    self._iters = [[100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0]]
                    self._convergence = [6]
                else:   # Diffeomorphic
                    regtype = 'SyN'
                    self._stages = ['Affine', 'Diffeomorphic']
                    self._iters = [[2100, 1200, 200, 1], [40, 20, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 0]]
                    self._convergence = [6, 7]
            else: raise ValueError('Type of registration {} is not defined.'.format(self._reg))
            self._wait.setStages(self._stages)
            self._wait.setMultiResolutionIterations(self._iters)
            self._wait.setProgressByLevel(self._progbylevel)
            self._wait.setConvergenceThreshold(self._convergence)
            """        
                Set custom parameters        
            """
            if self._reg == 'DisplacementField' and self._settings.getParameterValue('CustomParameters'):
                m = self._settings.getParameterValue('Metric')
                if m == 'CC': metric = 'CC'
                elif m == 'MS': metric = 'meansquares'
                elif m == 'DEMONS': metric = 'demons'
                else: metric = 'mattes'  # IM
                step = self._settings.getParameterValue('GradientStep')
                flow = self._settings.getParameterValue('FlowSigma')
                lr = self._settings.getParameterValue('LowResolutionIterations')
                mr = self._settings.getParameterValue('MediumResolutionIterations')
                hr = self._settings.getParameterValue('HighResolutionIterations')
                iters = (lr, mr, hr)
            else:
                metric = 'mattes'
                step = 0.2
                flow = 3
                iters = (40, 20, 0)
            """      
                Registration
            """
            self._wait.setInformationText('Registration initialization...')
            queue = Queue()
            stdout = join(fvol.getDirname(), 'stdout.log')
            reg = ProcessRegistration(fvol, mvol, mask, self._trf, regtype, metric, step, flow, iters, True, stdout, queue)
            self._wait.buttonVisibilityOn()
            try:
                reg.start()
                while reg.is_alive():
                    QApplication.processEvents()
                    if exists(stdout): self._wait.setAntsRegistrationProgress(stdout)
                    if self._wait.getStopped(): reg.terminate()
            except Exception as err:
                if reg.is_alive(): reg.terminate()
                self._wait.hide()
                QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                raise Exception
            finally:
                # Remove temporary std::cout file
                if exists(stdout): remove(stdout)
            self._wait.buttonVisibilityOff()
            self._wait.setProgressVisibility(False)
            trf = None
            if not queue.empty():
                trf = queue.get()
            """
                Displacement field processing
                1. Convert affine transformation to displacement field
                2. Add Affine and Elastic/Diffeomorphic displacement fields    
            """
            if trf is not None:
                self._trf.setAttributesFromFixedVolume(fvol)
                self._trf.setANTSTransform(read_transform(trf))
                # Remove temporary ants affine transform
                remove(trf)
                if self._reg == 'DisplacementField':
                    if not queue.empty():
                        """
                            Save displacement field
                        """
                        fld = queue.get()  # Displacement field nifti filename
                        if fld is not None:
                            self._wait.setInformationText('Save displacement field...')
                            # Open diffeomorphic displacement field
                            field = SisypheVolume()
                            field.copyPropertiesFrom(fvol)
                            field.loadFromNIFTI(fld, reorient=False)
                            field.acquisition.setSequenceToDisplacementField()
                            # Remove temporary ants displacement field
                            remove(fld)
                            # Affine to displacement field conversion -> Affine displacement field
                            self._trf.AffineToDisplacementField(inverse=False)
                            # Add to elastic/diffeomorphic displacement field
                            # Final displacement field = Affine + Diffeomorphic displacement fields
                            img = Cast(field.getSITKImage(), sitkVectorFloat64) + \
                                  self._trf.getSITKDisplacementFieldSITKImage()
                            field.setSITKImage(img)
                            field.setFilename(mvol.getFilename())
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            field.setFilenamePrefix(prefix)
                            field.setFilenameSuffix(suffix)
                            field.save()
                            self._trf.setSITKDisplacementFieldImage(field.getSITKImage())
                        """
                            Save inverse displacement field
                        """
                        fld = queue.get()  # Inverse displacement field nifti filename
                        remove(fld)
                        """
                        if fld is not None:
                            self._wait.setInformationText('Save inverse displacement field...')
                            # Open inverse diffeomorphic displacement field
                            field = SisypheVolume()
                            field.copyPropertiesFrom(mvol)
                            field.loadFromNIFTI(fld, reorient=False)
                            field.acquisition.setSequenceToDisplacementField()
                            # Remove temporary ants displacement field
                            # remove(fld)
                            # Affine to displacement field conversion -> Affine displacement field
                            trf = self._trf.getInverseTransform()
                            trf.AffineToDisplacementField()
                            # Add to elastic/diffeomorphic displacement field
                            # Final displacement field = Affine + Diffeomorphic displacement fields
                            field = field.getSITKImage() + trf.getSITKDisplacementFieldSITKImage()
                            field.setSITKImage(field)
                            field.setFilename(fvol.getFilename())
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            field.setFilenamePrefix(prefix)
                            field.setFilenameSuffix(suffix)
                            field.save()
                        """
            """
                Check registration
            """
            resampled = None
            f = SisypheApplyTransform()
            if trf is not None:
                f.setMoving(mvol)
                if self._trf.isAffineTransform(): f.setTransform(self._trf.getInverseTransform())
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
                    self._dialog = DialogManualRegistration(fvol, resampled, parent=self)
                    self._dialog.setDialogToCheck()
                    self._wait.hide()
                    if not self._dialog.exec(): trf = None
            """
                Restoring volume origins
            """
            fvol.setOrigin(self._forigin)
            mvol.setOrigin(self._morigin)
            """
                Resample moving volume
            """
            if trf is not None and resampled is not None:
                if self._settings.getParameterValue('Resample'):
                    dialog = self._resamplesettings.getParameterValue('Dialog')
                    prefix = self._resamplesettings.getParameterValue('Prefix')
                    suffix = self._resamplesettings.getParameterValue('Suffix')
                    resampled.setFilename(mvol.getFilename())
                    resampled.setFilenamePrefix(prefix)
                    resampled.setFilenameSuffix(suffix)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled volume', resampled.getFilename(),
                                                               filter='PySisyphe volume (*.xvol)')[0]
                        QApplication.processEvents()
                        if filename:
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
        self._wait.hide()
        # _movingSelect is not enabled in DialogBatchRegistration instance
        # The question of doing another registration is not asked in batch mode
        if self._fixedSelect.isEnabled() and self._movingSelect.isEnabled():
            r = QMessageBox.question(self, self.windowTitle(),
                                     'Do you want to make another registration ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes:
                self._fixedSelect.clear()
                self._movingSelect.clear()
                self._applyToSelect.clearall()
            else: self.accept()
        else: self.accept()


class DialogICBMNormalization(DialogRegistration):
    """
        DialogICBMNormalization

        Description

            GUI dialog for spatial normalization i.e. displacement field registration to template.

        Inheritance

            QDialog -> DialogRegistration -> DialogICBMNormalization

        Private attributes

        Public methods

            inherited QDialogRegistration methods
            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(transform='DisplacementField', parent=parent)

        self.setWindowTitle('ICBM Normalization')

        self._fixedSelect.setTextLabel('Template')
        self._fixedSelect.filterICBM()
        self._movingSelect.FieldChanged.connect(self._updateTemplate)

        layout = self.getLayout()
        layout.removeWidget(self._fixedSelect)
        layout.insertWidget(1, self._fixedSelect)

        lyout = QHBoxLayout()
        self._transform = LabeledComboBox()
        self._transform.setTitle('Type of registration')
        self._transform.addItem('Affine')
        self._transform.addItem('DisplacementField')
        self._transform.setCurrentIndex(1)
        self._transform.currentIndexChanged.connect(self._updateParameters)
        lyout.addStretch()
        lyout.addWidget(self._transform)
        lyout.addStretch()
        lyout.insertLayout(2, self._transform)

        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)

    # Private method

    def _updateParameters(self, index):
        if index == 0:
            self._reg = 'Affine'
            self._settings.setParameterVisibility('CustomParameters', False)
            self._settings.setParameterVisibility('Metric', False)
            self._settings.setParameterVisibility('GradientStep', False)
            self._settings.setParameterVisibility('FlowSigma', False)
            self._settings.setParameterVisibility('LowResolutionIterations', False)
            self._settings.setParameterVisibility('MediumResolutionIterations', False)
            self._settings.setParameterVisibility('HighResolutionIterations', False)
        else:
            self._reg = 'DisplacementField'
            self._settings.setParameterVisibility('CustomParameters', True)

    def _updateTemplate(self):
        filename = self._movingSelect.getFilename()
        if exists(filename):
            v = SisypheVolume()
            v.load(filename)
            sequence = v.getAcquisition().getSequence()
            settings = SisypheSettings()
            if ('Templates', sequence) in settings:
                filename = settings.getFieldValue(self, 'Templates', sequence)
                if exists(filename): self._fixedSelect.open(filename)
            else:
                QMessageBox.warning(self, 'ICBM Normalization', 'No template for {} sequence.'.format(sequence))


class DialogBatchRegistration(DialogRegistration):
    """
        DialogBatchRegistration

        Description

            GUI dialog for batch registration.

        Inheritance

            QDialog -> DialogRegistration -> DialogBatchRegistration

        Private attributes

            _batch  FilesSelectionWidget()

        Public methods

            FilesSelectionWidget = getBatchSelectionWidget()
            execute                     override

            inherited QDialogRegistration methods
            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(transform='Rigid', parent=parent)

        layout = self.getLayout()
        layout.removeWidget(self._fixedSelect)
        layout.insertWidget(1, self._fixedSelect)

        self._movingSelect.setVisible(False)

        lyout = QHBoxLayout()
        self._transform = LabeledComboBox()
        self._transform.setTitle('Type of registration')
        self._transform.addItem('Rigid')
        self._transform.addItem('Affine')
        self._transform.addItem('DisplacementField')
        self._transform.setCurrentIndex(1)
        self._transform.currentIndexChanged.connect(self._updateParameters)
        lyout.addStretch()
        lyout.addWidget(self._transform)
        lyout.addStretch()
        lyout.insertLayout(2, self._transform)

        self._batch = FilesSelectionWidget()
        self._batch.filterSisypheVolume()
        self._batch.setTextLabel('Moving volumes')
        self._batch.setCurrentVolumeButtonVisibility(True)
        layout.insertWidget(2, self._batch)

        self._settings.getParameterWidget('ManualRegistration').setChecked(False)
        self._settings.setParameterVisibility('ManualRegistration', False)
        self._settings.getParameterWidget('CheckRegistration').setChecked(False)
        self._settings.setParameterVisibility('CheckRegistration', False)

    # Private method

    def _updateParameters(self, index):
        if index in (0, 1):
            if index == 0: self._reg = 'Rigid'
            else: self._reg = 'Affine'
            self._settings.setParameterVisibility('CustomParameters', False)
            self._settings.setParameterVisibility('Metric', False)
            self._settings.setParameterVisibility('GradientStep', False)
            self._settings.setParameterVisibility('FlowSigma', False)
            self._settings.setParameterVisibility('LowResolutionIterations', False)
            self._settings.setParameterVisibility('MediumResolutionIterations', False)
            self._settings.setParameterVisibility('HighResolutionIterations', False)
        else:
            self._reg = 'DisplacementField'
            self._settings.setParameterVisibility('CustomParameters', True)

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
                super().execute()
                index += 1


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from os import chdir

    chdir('/Users/Jean-Albert/PycharmProjects/python310Project/TESTS/REGISTRATION/REG1')
    app = QApplication(argv)
    main = DialogRegistration('DisplacementField')
    main.exec()
