"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os import remove
from os.path import exists
from os.path import join

from multiprocessing import Process
from multiprocessing import Queue

from ants.core import from_numpy
from ants.core import read_transform
from ants.core import write_transform
from ants.registration import registration

from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
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

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.processing.antsFilters import CapturedStdout

__all__ = ['antsRegistration']


"""
    Class hierarchy

        Process -> ProcessRegistration
"""


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
            moving = from_numpy(self._moving, spacing=self._mspacing)
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
        except:
            self.terminate()


"""
    Function

        antsRegistration
"""


def antsRegistration(fvol, mvol, rvol=(), algo='AntsRigid', interpol='linear',
                     prefix='r_', suffix='', fprefix='field_', fsuffix='', wait=None):
    """
        fvol        SisypheVolume, fixed volume
        mvol        SisypheVolume, moving volume
        rvol        tuple[SisypheVolume], volume(s) to resample
        regtype     str, type of registration:
                    'Translation', 'FastRigid', 'DenseRigid', 'AntsRigid', 'AntsFastRigid', 'BoldRigid', 'Similarity',
                    'Affine', 'FastAffine', 'DenseAffine', 'AntsAffine', 'AntsFastAffine', 'BoldAffine', 'Elastic',
                    'Diffeomorphic', 'DenseDiffeomorphic', 'CCDiffeomorphic', 'BoldDiffeomorphic',
                    'AntsSplineDiffeomorphic', 'AntsDiffeomorphic', 'AntsFastSplineDiffeomorphic',
                    'AntsRigidSplineDiffeomorphic', 'AntsRigidDiffeomorphic', 'AntsFastRigidSplineDiffeomorphic',
                    'AntsFastRigidDiffeomorphic', 'AntsSplineDiffeomorphicOnly', 'AntsFastSplineDiffeomorphicOnly',
                    'AntsFastDiffeomorphicOnly'
        interpol    str, interpolation algorithm:
                    'nearest', 'linear', 'bspline', 'gaussian', 'hamming', 'cosine', 'welch', 'lanczos', 'blackman'
        fprefix     str, prefix for displacement field filename
        fsuffix     str, suffix for displacement field filename
        wait        DialogWaitRegistration

        return      SisypheVolume,resampled moving volume
    """
    """
        Set origin to (0.0, 0.0, 0.0) before registration
    """
    fvol.setDefaultOrigin()
    mvol.setDefaultOrigin()
    # Automatic fixed mask calculation
    if wait is not None: wait.setInformationText('Registration - Mask calculation...')
    mask = fvol.getMask(algo='mean', morpho='dilate', kernel=4, fill='2d')
    """
        Estimating translations
    """
    if wait is not None: wait.setInformationText('Registration - Translations estimation...')
    f = CenteredTransformInitializerFilter()
    img1 = Cast(fvol.getSITKImage(), sitkFloat32)
    img2 = Cast(mvol.getSITKImage(), sitkFloat32)
    ttrf = AffineTransform()
    ttrf.SetIdentity()
    ttrf = AffineTransform(f.Execute(img1, img2, ttrf))
    trf = SisypheTransform()
    trf.setSITKTransform(ttrf)
    trf.setAttributesFromFixedVolume(fvol)
    """
        Registration parameters initialization
    """
    if wait is not None: wait.setInformationText('Registration initialization...')
    if algo == 'Translation':
        regtype = algo
        stages = ['Rigid']
        iters = [[2100, 1200, 1200, 10]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = False
    elif algo == 'FastRigid':
        regtype = 'QuickRigid'
        stages = ['Rigid']
        iters = [[20, 20, 1, 1]]
        progbylevel = [[100, 200, 0, 0]]
        convergence = [6]
        field = False
    elif algo == 'DenseRigid':
        regtype = algo
        stages = ['Rigid']
        iters = [[2100, 1200, 1200, 10]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = False
    elif algo == 'AntsRigid':
        regtype = 'antsRegistrationSyN[r]'
        stages = ['Rigid']
        iters = [[1000, 500, 250, 100]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = False
    elif algo == 'AntsFastRigid':
        regtype = 'antsRegistrationSyNQuick[r]'
        stages = ['Rigid']
        iters = [[1000, 500, 250, 1]]
        progbylevel = [[100, 200, 400, 0]]
        convergence = [6]
        field = False
    elif algo == 'BoldRigid':
        regtype = 'BOLDRigid'
        stages = ['Rigid']
        iters = [[100, 20]]
        progbylevel = [[100, 200]]
        convergence = [6]
        field = False
    elif algo == 'Similarity':
        regtype = algo
        stages = ['Similarity']
        iters = [[2100, 1200, 1200, 10]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = False
    elif algo == 'Affine':
        regtype = algo
        stages = ['Affine']
        iters = [[2100, 1200, 1200, 10]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = False
    elif algo == 'FastAffine':
        regtype = 'AffineFast'
        stages = ['Affine']
        iters = [[2100, 1200, 1, 1]]
        progbylevel = [[100, 200, 0, 0]]
        convergence = [6]
        field = False
    elif algo == 'DenseAffine':
        regtype = 'TRSAA'
        stages = ['Translation', 'Rigid', 'Similarity', 'Affine', 'Affine']
        iters = [[2000, 2000, 1], [2000, 2000, 1], [2000, 2000, 1], [40, 20, 1], [40, 20, 1]]
        progbylevel = [[100, 200, 0], [100, 200, 0], [100, 200, 0], [100, 200, 0], [100, 200, 0]]
        convergence = [6, 6, 6, 6, 6]
        field = False
    elif algo == 'AntsAffine':
        regtype = 'antsRegistrationSyN[a]'
        stages = ['Rigid', 'Affine']
        iters = [[1000, 500, 250, 100], [1000, 500, 250, 100]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
        convergence = [6, 6]
        field = False
    elif algo == 'AntsFastAffine':
        regtype = 'antsRegistrationSyNQuick[a]'
        stages = ['Rigid', 'Affine']
        iters = [[1000, 500, 250, 1], [1000, 500, 250, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
        convergence = [6, 6]
        field = False
    elif algo == 'BoldAffine':
        regtype = 'BOLDAffine'
        stages = ['Affine']
        iters = [100, 20]
        progbylevel = [[100, 200]]
        convergence = [6]
        field = False
    elif algo == 'Elastic':
        regtype = 'ElasticSyN'
        stages = ['Affine', 'Elastic']
        iters = [[2100, 1200, 200, 1], [40, 20, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 0]]
        convergence = [6, 7]
        field = True
    elif algo == 'Diffeomorphic':
        regtype = 'SyN'
        stages = ['Affine', 'Diffeomorphic']
        iters = [[2100, 1200, 200, 1], [40, 20, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 0]]
        convergence = [6, 7]
        field = True
    elif algo == 'DenseDiffeomorphic':
        regtype = 'SyNAggro'
        stages = ['Affine', 'Diffeomorphic']
        iters = [[2100, 1200, 1200, 100], [40, 20, 1]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 0]]
        convergence = [6, 7]
        field = True
    elif algo == 'CCDiffeomorphic':
        regtype = 'SyNCC'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[2100, 1200, 1200, 1], [1200, 1200, 100], [40, 20, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 400], [100, 200, 0]]
        convergence = [6, 6, 7]
        field = True
    elif algo == 'BoldDiffeomorphic':
        regtype = 'SyNBold'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1200, 1200, 100], [200, 20], [40, 20, 1]]
        progbylevel = [[100, 200, 400, 800], [100, 200], [100, 200, 0]]
        convergence = [6, 6, 7]
        field = True
    elif algo == 'AntsSplineDiffeomorphic':
        regtype = 'antsRegistrationSyN[s]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
        convergence = [6, 6, 6]
        field = True
    elif algo == 'AntsDiffeomorphic':
        regtype = 'antsRegistrationSyN[b]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
        convergence = [6, 6, 6]
        field = True
    elif algo == 'AntsFastSplineDiffeomorphic':
        regtype = 'antsRegistrationSyNQuick[s]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
        convergence = [6, 6, 6]
        field = True
    elif algo == 'AntsFastDiffeomorphic':
        regtype = 'antsRegistrationSyNQuick[b]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 0]]
        convergence = [6, 6, 6]
        field = True
    elif algo == 'AntsRigidSplineDiffeomorphic':
        regtype = 'antsRegistrationSyN[sr]'
        stages = ['Rigid', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
        convergence = [6, 6]
        field = True
    elif algo == 'AntsRigidDiffeomorphic':
        regtype = 'antsRegistrationSyN[br]'
        stages = ['Rigid', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
        convergence = [6, 6]
        field = True
    elif algo == 'AntsFastRigidSplineDiffeomorphic':
        regtype = 'antsRegistrationSyNQuick[sr]'
        stages = ['Rigid', 'Diffeomorphic']
        iters = [[1000, 500, 250, 1], [100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
        convergence = [6, 6]
        field = True
    elif algo == 'AntsFastRigidDiffeomorphic':
        regtype = 'antsRegistrationSyNQuick[br]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[1000, 500, 250, 100], [100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 800], [100, 200, 400, 0]]
        convergence = [6, 6]
        field = True
    elif algo == 'AntsSplineDiffeomorphicOnly':
        regtype = 'antsRegistrationSyN[so]'
        stages = ['Diffeomorphic']
        iters = [[100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = True
    elif algo == 'AntsDiffeomorphicOnly':
        regtype = 'antsRegistrationSyN[bo]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[100, 70, 50, 20]]
        progbylevel = [[100, 200, 400, 800]]
        convergence = [6]
        field = True
    elif algo == 'AntsFastSplineDiffeomorphicOnly':
        regtype = 'antsRegistrationSyNQuick[so]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 0]]
        convergence = [6]
        field = True
    elif algo == 'AntsFastDiffeomorphicOnly':
        regtype = 'antsRegistrationSyNQuick[bo]'
        stages = ['Rigid', 'Affine', 'Diffeomorphic']
        iters = [[100, 70, 50, 1]]
        progbylevel = [[100, 200, 400, 0]]
        convergence = [6]
        field = True
    else: raise ValueError('Type of registration {} is not defined.'.format(algo))
    if wait is not None:
        wait.setStages(stages)
        wait.setMultiResolutionIterations(iters)
        wait.setProgressByLevel(progbylevel)
        wait.setConvergenceThreshold(convergence)
    # Default custom parameters
    metric = 'mattes'
    step = 0.2
    flow = 3
    iters = (40, 20, 0)
    """
        Registration
    """
    queue = Queue()
    stdout = join(fvol.getDirname(), 'stdout.log')
    reg = ProcessRegistration(fvol, mvol, mask, trf, regtype, metric, step, flow, iters, True, stdout, queue)
    if wait is not None: wait.buttonVisibilityOn()
    try:
        reg.start()
        while reg.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): wait.setAntsRegistrationProgress(stdout)
                if wait.getStopped(): reg.terminate()
    except Exception as err:
        if reg.is_alive(): reg.terminate()
        if wait is not None: wait.hide()
        raise Exception
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    if wait is not None:
        wait.buttonVisibilityOff()
        wait.setProgressVisibility(False)
    if not queue.empty():
        trf.setANTSTransform(read_transform(queue.get()))
    """
         Save displacement field
    """
    if field and not queue.empty():
        fld = queue.get()  # Displacement field nifti filename
        if fld is not None:
            if wait is not None: wait.setInformationText('Save displacement field...')
            # Open diffeomorphic displacement field
            field = SisypheVolume()
            field.copyPropertiesFrom(fvol)
            field.loadFromNIFTI(fld, reorient=False)
            field.acquisition.setSequenceToDisplacementField()
            # Remove temporary ants displacement field
            remove(fld)
            # Affine to displacement field conversion -> Affine displacement field
            trf.AffineToDisplacementField(inverse=False)
            # Add to elastic/diffeomorphic displacement field
            # Final displacement field = Affine + Diffeomorphic displacement fields
            img = Cast(field.getSITKImage(), sitkVectorFloat64) + \
                  trf.getSITKDisplacementFieldSITKImage()
            field.setSITKImage(img)
            field.setFilename(mvol.getFilename())
            field.setFilenamePrefix(fprefix)
            if fsuffix != '': field.setFilenameSuffix(fsuffix)
            field.save()
            trf.setSITKDisplacementFieldImage(field.getSITKImage())
    """
        Resample volume(s)
    """
    if trf is not None and len(rvol) > 0:
        resampled = list()
        f = SisypheApplyTransform()
        if trf.isAffineTransform(): f.setTransform(trf.getInverseTransform())
        else: f.setTransform(trf)
        if interpol == 'nearest': f.setInterpolator(sitkNearestNeighbor)
        elif interpol == 'linear': f.setInterpolator(sitkLinear)
        elif interpol == 'bspline': f.setInterpolator(sitkBSpline)
        elif interpol == 'gaussian': f.setInterpolator(sitkGaussian)
        elif interpol == 'hamming': f.setInterpolator(sitkHammingWindowedSinc)
        elif interpol == 'cosine': f.setInterpolator(sitkCosineWindowedSinc)
        elif interpol == 'welch': f.setInterpolator(sitkWelchWindowedSinc)
        elif interpol == 'lanczos': f.setInterpolator(sitkLanczosWindowedSinc)
        elif interpol == 'blackman': f.setInterpolator(sitkBlackmanWindowedSinc)
        else: f.setInterpolator(sitkLinear)
        if wait is not None: wait.progressVisibilityOff()
        for vol in rvol:
            if wait is not None: wait.setInformationText('Resample {}...'.format(vol.getBasename()))
            f.setMoving(vol)
            resampled.append(f.execute(fixed=fvol, save=True, prefix=prefix, suffix=suffix, wait=wait))
        return resampled
    if wait is not None: wait.hide()
