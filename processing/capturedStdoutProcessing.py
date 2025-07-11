"""
External packages/modules
-------------------------

    - ANTs, image registration, https://github.com/ANTsX/ANTsPy
"""

import sys

from os import dup
from os import dup2
from os import remove
from os import close

from os.path import exists
from os.path import join
from os.path import basename
from os.path import splitext

from multiprocessing import Process

from numpy import array

from ants.core import write_transform

from dipy.core.gradients import gradient_table

from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheTracts import SisypheTracking
from Sisyphe.core.sisypheTracts import SisypheDTIModel
from Sisyphe.core.sisypheTracts import SisypheDKIModel
from Sisyphe.core.sisypheTracts import SisypheSHCSAModel
from Sisyphe.core.sisypheTracts import SisypheSHCSDModel
from Sisyphe.core.sisypheTracts import SisypheDSIModel
from Sisyphe.core.sisypheTracts import SisypheDSIDModel
from Sisyphe.core.sisypheTracts import SisypheDiffusionModel
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.processing.dipyFunctions import dwiPreprocessing

__all__ = ['CapturedStdout',
           'ProcessSkullStrip',
           'ProcessRegistration',
           'ProcessRealignment',
           'ProcessAtropos',
           'ProcessCorticalThickness',
           'ProcessDeepTumorSegmentation',
           'ProcessDeepHippocampusSegmentation',
           'ProcessDeepMedialTemporalSegmentation',
           'ProcessDeepLesionSegmentation',
           'ProcessDeepWhiteMatterHyperIntensitiesSegmentation',
           'ProcessDeepTOFVesselSegmentation',
           'ProcessDeepTissueSegmentation',
           'ProcessDiffusionPreprocessing',
           'ProcessDiffusionModel',
           'ProcessDiffusionTracking']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - CapturedStdout
    - Process -> ProcessSkullStrip
              -> ProcessRegistration
              -> ProcessRealignment
              -> ProcessAtropos
              -> ProcessCorticalThickness
              -> ProcessDeepTumorSegmentation
              -> ProcessDeepHippocampusSegmentation
              -> ProcessDeepMedialTemporalSegmentation
              -> ProcessDeepLesionSegmentation
              -> ProcessDeepWhiteMatterHyperIntensitiesSegmentation
              -> ProcessDeepTOFVesselSegmentation
              -> ProcessDeepTissueSegmentation
              -> ProcessDiffusionPreprocessing
              -> ProcessDiffusionModel
              -> ProcessDiffusionTracking

When QApplication is imported into a module, calling from_numpy method of the antspy library in this module raises an 
exception in win32 platform. Processing with stdout capture is isolated in the current module to avoid conflict with 
QApplication module.

Creation: 17/04/2025
"""

class CapturedStdout:
    """
    CaptureStdout

    Description
    ~~~~~~~~~~~

    Class to redirect low-level stdout (file descriptor 1) used by C++ libraries, to a text file. This version is
    designed to work reliably in environments where sys.stdout may not be a valid stream (e.g. frozen application
    with PyInstaller)

    Last revision: 25/06/2025
    """

    # Special methods

    """
    Private attributes

    prevfd      file
    prev        file
    _filename   str
    """

    def __init__(self, filename, lowlevel=True):
        """
        old:
        self.prevfd = None
        self.prev = None
        self._filename = filename
        """
        self._filename = filename
        self._original_stdout_fd = -1  # dummy file descriptor
        self._new_stdout_file = None   # dummy file
        if not lowlevel:
            try: sys.stdout.fileno()
            except: lowlevel = True
        self._lowlevel = lowlevel

    def __enter__(self):
        """
        dst = open('stdout.log', 'a')
        dst_fd = dst.fileno()
        stdout_fd = sys.stdout.fileno()
        os.close(stdout_fd)
        os.dup2(dst_fd, stdout_fd)

        old:
        F = open(self._filename, 'w')
        # copy sys.stdout file descriptor to prevfd
        self.prevfd = dup(sys.stdout.fileno())
        # copy stdout file descriptor to file F (sys.stdout redirected to file F)
        dup2(F.fileno(), sys.stdout.fileno())
        # copy stdout to prev
        self.prev = sys.stdout
        return F
        """
        # open file to capture stdout
        self._new_stdout_file = open(self._filename, 'w')
        # file descriptor of file used to capture stdout
        new_fd = self._new_stdout_file.fileno()
        try:
            # copy original stdout file descriptor
            if self._lowlevel: self._original_stdout_fd = dup(1)
            else: self._original_stdout_fd = dup(sys.stdout.fileno())
        except OSError:
            # no stdout, dummy file descriptor
            self._original_stdout_fd = -1
        # capture original stdout
        if self._lowlevel: dup2(new_fd, 1)
        else: dup2(new_fd, sys.stdout.fileno())
        # return file used to capture stdout
        return self._new_stdout_file

    def __exit__(self, exc_type, exc_value, traceback):
        """
        old:
        dup2(self.prevfd, self.prev.fileno())
        sys.stdout = self.prev
        """
        if self._new_stdout_file:
            # close stdout file
            self._new_stdout_file.flush()
            self._new_stdout_file.close()
        if self._original_stdout_fd != -1:
            # restore original stdout if not dummy
            if self._lowlevel: dup2(self._original_stdout_fd, 1)
            else: dup2(self._original_stdout_fd, sys.stdout.fileno())
            close(self._original_stdout_fd)


class ProcessSkullStrip(Process):
    """
    ProcessSkullStrip

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for ants skull strip function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessSkullStrip
    """
    # Special method

    """
    Private attributes

    _img        numpy.ndarray
    _modality   str
    _cache      str
    """

    def __init__(self, img, modality, cache, queue):
        Process.__init__(self)
        self._img = img.getNumpy(defaultshape=False).astype('float32')
        self._modality = modality
        self._cache = cache
        self._spacing = img.getSpacing()
        self._result = queue

    # Public methods

    def run(self):
        from ants.core import from_numpy
        img = from_numpy(self._img, spacing=self._spacing)
        from antspynet.utilities import brain_extraction
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        r = brain_extraction(img, self._modality)
        self._result.put(r.numpy())


class ProcessRegistration(Process):
    """
    ProcessRegistration

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for ants registration function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessRegistration
    """
    # Special method

    """
    Private attributes

    _fixed      numpy.ndarray
    _moving     numpy.ndarray
    _mask       numpy.ndarray
    _fspacing   tuple[float, float, float], fixed volume spacing
    _mspacing   tuple[float, float, float], moving volume spacing
    _regtype    str
    _transform  str, ANTsTransform filename
    _metric     tuple[str, str]
    _sampling   float
    _verbose    bool
    _stdout     str
    _result     Queue
    """

    def __init__(self, fixed, moving, mask, maskallstages, trf, regtype, metric, sampling, stdout, queue):
        Process.__init__(self)
        self._fixed = fixed.getNumpy(defaultshape=False).astype('float32')
        self._moving = moving.getNumpy(defaultshape=False).astype('float32')
        if mask is not None: self._mask = mask.getNumpy(defaultshape=False)
        else: self._mask = None
        self._maskallstages = maskallstages
        self._fspacing = fixed.getSpacing()
        self._mspacing = moving.getSpacing()
        self._transform = join(moving.getDirname(), 'temp.mat')
        write_transform(trf.getANTSTransform(), self._transform)
        self._regtype = regtype
        self._metric = metric
        self._sampling = sampling
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        fixed = from_numpy(self._fixed, spacing=self._fspacing)
        moving = from_numpy(self._moving, spacing=self._mspacing)
        if self._mask is not None: mask = from_numpy(self._mask, spacing=self._fspacing)
        else: mask = None
        """         
            registration return
            r = {'warpedmovout': ANTsImage,
                 'warpedfixout': ANTsImage,
                 'fwdtransforms': str,
                 'invtransforms': str} 
            fwdtransforms: transformation filename
            invtransforms: inverse transformation filename               
        """
        # noinspection PyUnusedLocal
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
            total_sigma: smoothing for total field
            aff_metric: the metric for the affine part (GC, mattes, meansquares)
            aff_sampling: the nbins or radius parameter for the syn metric
            aff_random_sampling_rate: the fraction of points used to estimate the metric
            syn_metric: the metric for the syn part (CC, mattes, meansquares, demons)
            syn_sampling: the nbins or radius parameter for the syn metric
            reg_iterations : vector of iterations for syn
            aff_iterations : vector of iterations for linear registration (translation, rigid, affine)
            aff_shrink_factors : vector of multi-resolution shrink factors for linear registration
            aff_smoothing_sigmas : vector of multi-resolution smoothing factors for linear registration
            smoothing_in_mm : boolean; currently only impacts low dimensional registration
            """
            from ants.registration import registration
            r = registration(fixed, moving, type_of_transform=self._regtype,
                             initial_transform=self._transform, mask=mask, mask_all_stages=self._maskallstages,
                             aff_metric=self._metric[0], syn_metric=self._metric[1],
                             aff_random_sampling_rate=self._sampling, verbose=True)
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
            self._result.put(r['invtransforms'][1])  # Inverse displacement field image
            # Remove temporary ants inverse affine transform
            if exists(r['invtransforms'][0]):
                if r['invtransforms'][0] != r['fwdtransforms'][1]:
                    remove(r['invtransforms'][0])


class ProcessRealignment(Process):
    """
    ProcessRealignment

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for temporal series realignment function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessRealignmentn
    """

    # Special method

    """
    Private attributes

    _vols       numpy.ndarray
    _mask       numpy.ndarray
    _metric     str, 'CC', 'mattes' or 'meansquares'
    _sampling   float
    _progress   Value
    _result     Queue
    """

    def __init__(self, vols, mask, metric, sampling, progress, queue):
        Process.__init__(self)
        self._vols = vols.copyToNumpyArray(defaultshape=False)
        self._mask = mask.copyToNumpyArray(defaultshape=False)
        self._spacing = vols[0].getSpacing()
        self._metric = metric
        self._sampling = sampling
        self._progress = progress
        self._result = queue

    # Public method

    def run(self):
        from ants.core.ants_image_io import from_numpy
        fixed = from_numpy(self._vols[:, :, :, 0].astype('float32'), spacing=self._spacing)
        if self._mask is None: mask = self._mask
        else: mask = from_numpy(self._mask, spacing=self._spacing)
        transform = None
        for i in range(1, self._vols.shape[3]):
            moving = from_numpy(self._vols[:, :, :, i].astype('float32'), spacing=self._spacing)
            """"
                registration return
                r = {'warpedmovout': ANTsImage,
                     'warpedfixout': ANTsImage,
                     'fwdtransforms': str,
                     'invtransforms': str}
            """
            from ants.registration import registration
            r = registration(fixed, moving, type_of_transform='BOLDRigid', initial_transform=transform, mask=mask,
                             aff_metric=self._metric, aff_random_sampling_rate=self._sampling, verbose=False)
            if len(r['fwdtransforms']) == 1:
                transform = r['fwdtransforms'][0]
                self._result.put(transform)  # Affine trf
                if exists(r['invtransforms'][0]):
                    if r['invtransforms'][0] != r['fwdtransforms'][0]:
                        remove(r['invtransforms'][0])
            with self._progress.get_lock():
                self._progress.value += 1


class ProcessAtropos(Process):
    """
    ProcessAtropos class

    Description
    ~~~~~~~~~~~

    Multiprocessing class for ants atropos function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessAtropos
    """

    # Special method

    """
    Private attributes

    _stdout     str, c++ stdout redirected to _stdout file
    _result     Queue
    """

    def __init__(self, volume, mask, init, mrf, conv, weight, stdout, queue):
        Process.__init__(self)
        self._volume = volume.getNumpy(defaultshape=False).astype('float32')
        if mask is not None: self._mask = mask.getNumpy(defaultshape=False)
        else: self._mask = None
        self._spacing = volume.getSpacing()
        if isinstance(init, str): self._init = init
        elif isinstance(init, list):
            self._init = list()
            for i in range(len(init)):
                self._init.append(init[i].getNumpy(defaultshape=False).astype('float32'))
        self._mrf = mrf
        self._conv = conv
        self._weight = weight
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        vol = from_numpy(self._volume, spacing=self._spacing)
        if self._mask is not None: mask = from_numpy(self._mask, spacing=self._spacing)
        else: mask = None
        if isinstance(self._init, list):
            for i in range(len(self._init)):
                self._init[i] = from_numpy(self._init[i], spacing=self._spacing)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            from Sisyphe.lib.ants.atropos import atropos
            # noinspection PyTypeChecker
            r = atropos(vol, x=mask, i=self._init, m=self._mrf, c=self._conv, priorweight=self._weight, verbose=1)
        for i in range(len(r)):
            self._result.put(r[i])


class ProcessCorticalThickness(Process):
    """
    ProcessCorticalThickness class

    Description
    ~~~~~~~~~~~

    Multiprocessing class for ants cortical thickness function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessAtropos
    """

    # Special method

    """
    Private attributes

    _stdout     str, c++ stdout redirected to _stdout file
    _result     Queue
    """

    def __init__(self, seg, gm, wm, iters, grdstep, grdsmooth, stdout, queue):
        Process.__init__(self)
        self._seg = seg.getNumpy(defaultshape=False).astype('float32')
        self._gm = gm.getNumpy(defaultshape=False).astype('float32')
        self._wm = wm.getNumpy(defaultshape=False).astype('float32')
        self._spacing = seg.getSpacing()
        self._iters = iters
        self._grdstep = grdstep
        self._grdsmooth = grdsmooth
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        seg = from_numpy(self._seg, spacing=self._spacing)
        gm = from_numpy(self._gm, spacing=self._spacing)
        wm = from_numpy(self._wm, spacing=self._spacing)
        # Set direction to LPI
        d = seg.direction
        d[0, 0] = -1
        d[1, 1] = -1
        seg.set_direction(d)
        gm.set_direction(d)
        wm.set_direction(d)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            from ants.segmentation import kelly_kapowski
            r = kelly_kapowski(s=seg, g=gm, w=wm, its=self._iters, r=self._grdstep, m=self._grdsmooth, verbose=1)
        self._result.put(r.numpy())


class ProcessDeepTumorSegmentation(Process):
    """
    ProcessDeepTumorSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning tumor segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepTumorSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, flair, t1, t1ce, t2, cache, stdout, queue):
        Process.__init__(self)
        self._flair = flair.getNumpy(defaultshape=False).astype('float32')
        self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        self._t1ce = t1ce.getNumpy(defaultshape=False).astype('float32')
        self._t2 = t2.getNumpy(defaultshape=False).astype('float32')
        self._cache = cache
        self._spacing = flair.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        flair = from_numpy(self._flair, spacing=self._spacing)
        t1 = from_numpy(self._t1, spacing=self._spacing)
        t1ce = from_numpy(self._t1ce, spacing=self._spacing)
        t2 = from_numpy(self._t2, spacing=self._spacing)
        # Set direction to LPI
        d = flair.direction
        d[0, 0] = -1
        d[1, 1] = -1
        flair.set_direction(d)
        t1.set_direction(d)
        t1ce.set_direction(d)
        t2.set_direction(d)
        from antspynet.utilities import brain_tumor_segmentation
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = brain_tumor_segmentation(flair, t1, t1ce, t2, verbose=True)
        r2 = dict()
        r2['lbl'] = r['segmentation_image'].numpy()
        n = len(r['probability_images'])
        r2['prb'] = list()
        for i in range(n):
            r2['prb'].append(r['probability_images'][i].numpy())
        self._result.put(r2)


class ProcessDeepHippocampusSegmentation(Process):
    """
    ProcessDeepHippocampusSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning hippocampus segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepHippocampusSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, t1, cache, stdout, queue):
        Process.__init__(self)
        self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        self._cache = cache
        self._spacing = t1.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        t1 = from_numpy(self._t1, spacing=self._spacing)
        # Set direction to LPI
        d = t1.direction
        d[0, 0] = -1
        d[1, 1] = -1
        t1.set_direction(d)
        from antspynet.utilities import hippmapp3r_segmentation
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = hippmapp3r_segmentation(t1, verbose=True)
        self._result.put(r.numpy())


class ProcessDeepMedialTemporalSegmentation(Process):
    """
    ProcessDeepMedialTemporalSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning medial temporal segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepMedialTemporalSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, t1, t2, model, cache, stdout, queue):
        Process.__init__(self)
        self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        if t2 is not None: self._t2 = t2.getNumpy(defaultshape=False).astype('float32')
        else: self._t2 = None
        self._model = model
        self._cache = cache
        self._spacing = t1.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        t1 = from_numpy(self._t1, spacing=self._spacing)
        if self._t2 is not None: t2 = from_numpy(self._t2, spacing=self._spacing)
        else: t2 = None
        # Set direction to LPI
        d = t1.direction
        d[0, 0] = -1
        d[1, 1] = -1
        t1.set_direction(d)
        if t2 is not None: t2.set_direction(d)
        from antspynet.utilities import deep_flash
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = deep_flash(t1, t2, which_parcellation=self._model, verbose=True)
        r2 = dict()
        r2['lbl'] = r['segmentation_image'].numpy()
        n = len(r['probability_images'])
        r2['prb'] = list()
        for i in range(n):
            r2['prb'].append(r['probability_images'][i].numpy())
        if self._model == 'yassa':
            r2['med'] = r['medial_temporal_lobe_probability_image'].numpy()
            r2['hip'] = r['hippocampal_probability_image'].numpy()
        elif self._model == 'wip':
            r2['amg'] = r['amygdala_probability_image'].numpy()
            r2['hip'] = r['hippocampal_probability_image'].numpy()
        self._result.put(r2)


class ProcessDeepLesionSegmentation(Process):
    """
    ProcessDeepLesionSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning lesion segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepLesionSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, t1, cache, stdout, queue):
        Process.__init__(self)
        self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        self._cache = cache
        self._spacing = t1.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core import from_numpy
        t1 = from_numpy(self._t1, spacing=self._spacing)
        # Set direction to LPI
        d = t1.direction
        d[0, 0] = -1
        d[1, 1] = -1
        t1.set_direction(d)
        from antspynet.utilities import lesion_segmentation
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = lesion_segmentation(t1, verbose=True)
        self._result.put(r.numpy())


class ProcessDeepWhiteMatterHyperIntensitiesSegmentation(Process):
    """
    ProcessDeepWhiteMatterHyperIntensitiesSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning white matter hyperintensities segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepWhiteMatterHyperIntensitiesSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, flair, t1, mask, model, cache, stdout, queue):
        Process.__init__(self)
        self._flair = flair.getNumpy(defaultshape=False).astype('float32')
        if t1 is not None: self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        else: self._t1 = None
        if mask is not None: self._mask = t1.getNumpy(defaultshape=False).astype('float32')
        else: self._mask = None
        self._model = model
        self._cache = cache
        self._spacing = flair.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        flair = from_numpy(self._flair, spacing=self._spacing)
        if self._t1 is not None: t1 = from_numpy(self._t1, spacing=self._spacing)
        else: t1 = None
        if self._mask is not None: mask = from_numpy(self._mask, spacing=self._spacing)
        else: mask = None
        # Set direction to LPI
        d = flair.direction
        d[0, 0] = -1
        d[1, 1] = -1
        flair.set_direction(d)
        if t1 is not None: t1.set_direction(d)
        if mask is not None: mask.set_direction(d)
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        if self._model == 'sysu':
            from antspynet.utilities.white_matter_hyperintensity_segmentation import sysu_media_wmh_segmentation
            # noinspection PyUnusedLocal
            with CapturedStdout(self._stdout) as F:
                r = sysu_media_wmh_segmentation(flair, t1, verbose=True)
        elif self._model == 'hypermapp3r':
            from antspynet.utilities.white_matter_hyperintensity_segmentation import hypermapp3r_segmentation
            # noinspection PyUnusedLocal
            with CapturedStdout(self._stdout) as F:
                r = hypermapp3r_segmentation(flair, t1, verbose=True)
        elif self._model == 'antsxnet':
            from antspynet.utilities.white_matter_hyperintensity_segmentation import wmh_segmentation
            # noinspection PyUnusedLocal
            with CapturedStdout(self._stdout) as F:
                r = wmh_segmentation(flair, t1, mask, verbose=True)
        else: raise ValueError('Invalid model.')
        self._result.put(r.numpy())


class ProcessDeepTOFVesselSegmentation(Process):
    """
    ProcessDeepTOFVesselSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning TOF vessels segmentation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepTOFVesselSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, tof, cache, stdout, queue):
        Process.__init__(self)
        self._tof = tof.getNumpy(defaultshape=False).astype('float32')
        self._cache = cache
        self._spacing = tof.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        tof = from_numpy(self._tof, spacing=self._spacing)
        # Set direction to LPI
        d = tof.direction
        d[0, 0] = -1
        d[1, 1] = -1
        tof.set_direction(d)
        from antspynet.utilities.brain_mra_vessel_segmentation import brain_mra_vessel_segmentation
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = brain_mra_vessel_segmentation(tof, verbose=True)
        self._result.put(r.numpy())


class ProcessDeepTissueSegmentation(Process):
    """
    ProcessDeepTissueSegmentation

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for deep learning tissue segmentation i.e. gray matter, white matter, cerebro-spinal
    fluid, brainstem, cerebellum.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDeepTissueSegmentation
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, t1, cache, stdout, queue):
        Process.__init__(self)
        self._t1 = t1.getNumpy(defaultshape=False).astype('float32')
        self._cache = cache
        self._spacing = t1.getSpacing()
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        from ants.core.ants_image_io import from_numpy
        t1 = from_numpy(self._t1, spacing=self._spacing)
        # Set direction to LPI
        d = t1.direction
        d[0, 0] = -1
        d[1, 1] = -1
        t1.set_direction(d)
        from antspynet.utilities.deep_atropos import deep_atropos
        from antspynet.utilities.get_antsxnet_data import set_antsxnet_cache_directory
        set_antsxnet_cache_directory(self._cache)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
            r = deep_atropos(t1, verbose=True)
        r2 = dict()
        r2['lbl'] = r['segmentation_image'].numpy()
        n = len(r['probability_images'])
        r2['prb'] = list()
        for i in range(n):
            r2['prb'].append(r['probability_images'][i].numpy())
        self._result.put(r2)


class ProcessDiffusionPreprocessing(Process):
    """
    ProcessDiffusionPreprocessing

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for diffusion preprocessing.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDiffusionPreprocessing
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, bval, bvec, bseg, gibbs, denoise, prefix, suffix, mng, queue):
        Process.__init__(self)
        self._fbval = bval
        self._fbvec = bvec
        self._brainseg = bseg
        self._gibbs = gibbs
        self._denoise = denoise
        self._prefix = prefix
        self._suffix = suffix
        self._result = queue
        self._mng = mng

    # Public methods

    def run(self):
        self._mng['msg'] = 'Load gradient B values...'
        if exists(self._fbval):
            try: bvals = loadBVal(self._fbval, format='xml')
            except:
                self._result.put('{} format is invalid.'.format(basename(self._fbval)))
                self.terminate()
        else:
            self._result.put('No such file {}.'.format(self._fbval))
            self.terminate()
        self._mng['msg'] = 'Load gradient directions...'
        if exists(self._fbvec):
            try: bvecs = loadBVec(self._fbvec, format='xml', numpy=True)
            except:
                self._result.put('{} format is invalid.'.format(basename(self._fbvec)))
                self.terminate()
        else:
            self._result.put('No such file {}.'.format(self._fbvec))
            self.terminate()
        self._mng['msg'] = 'Load diffusion weighted volumes...'
        # noinspection PyUnboundLocalVariable
        dwinames = list(bvals.keys())
        bvals = array(list(bvals.values()))
        vols = SisypheVolumeCollection()
        for dwiname in dwinames:
            if exists(dwiname):
                vol = SisypheVolume()
                vol.load(dwiname)
                vols.append(vol)
            else:
                self._result.put('Diffusion-weighted images are missing.')
                self.terminate()
        # noinspection PyUnboundLocalVariable
        gtable = gradient_table(bvals=bvals, bvecs=bvecs)
        try:
            dwiPreprocessing(vols,
                             self._prefix,
                             self._suffix,
                             gtable,
                             self._brainseg,
                             self._gibbs,
                             self._denoise,
                             save=True,
                             wait=self._mng)
        except Exception as err:
            self._result.put('Diffusion preprocessing failed.\n{}\n{}.'.format(type(err), str(err)))
            self.terminate()
        self._result.put('terminate')


class ProcessDiffusionModel(Process):
    """
    ProcessDiffusionModel

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for diffusion model estimation.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDiffusionModel
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, bval, bvec, model, method, order, maps, corr, algo, niter, size, save, mng, queue):
        Process.__init__(self)
        self._fbval = bval
        self._fbvec = bvec
        self._model = model
        self._method = method
        self._order = order
        self._maps = maps
        self._corr = corr
        self._save = save
        self._algo = algo
        self._niter = niter
        self._size = size
        self._mng = mng
        self._result = queue

    # Public methods

    def run(self):
        # Load gradient B values
        self._mng['msg'] = 'Load gradient B values...'
        if exists(self._fbval):
            try:
                bvals = loadBVal(self._fbval, format='xml')
            except:
                self._result.put('{} format is invalid.'.format(basename(self._fbval)))
                self.terminate()
        else:
            self._result.put('No such file {}.'.format(self._fbval))
            self.terminate()
        # Load gradient directions
        self._mng['msg'] = 'Load gradient directions...'
        if exists(self._fbvec):
            try:
                bvecs = loadBVec(self._fbvec, format='xml', numpy=True)
            except:
                self._result.put('{} format is invalid.'.format(basename(self._fbvec)))
                self.terminate()
        else:
            self._result.put('No such file {}.'.format(self._fbvec))
            self.terminate()
        # Load diffusion weighted volumes
        self._mng['msg'] = 'Load diffusion weighted volumes...'
        # noinspection PyUnboundLocalVariable
        dwinames = list(bvals.keys())
        bvals = array(list(bvals.values()))
        vols = SisypheVolumeCollection()
        for dwiname in dwinames:
            if exists(dwiname):
                vol = SisypheVolume()
                vol.load(dwiname)
                vols.append(vol)
            else:
                self._result.put('Diffusion-weighted images are missing.')
                self.terminate()
        # verification of consistency between model and acquisition (DWI count)
        nd = len(bvals)
        nb0 = 0  # B0 count
        for i in range(nd):
            if bvals[i] == 0: nb0 += 1
        nd -= nb0  # DWI count
        # set model
        tag = False
        fa = ga = gfa = md = tr = ad = rd = False
        if 'fa' in self._maps: fa = self._maps['fa']
        if 'ga' in self._maps: ga = self._maps['ga']
        if 'gfa' in self._maps: gfa = self._maps['gfa']
        if 'md' in self._maps: md = self._maps['md']
        if 'tr' in self._maps: tr = self._maps['tr']
        if 'ad' in self._maps: ad = self._maps['ad']
        if 'rd' in self._maps: rd = self._maps['rd']
        if self._model == 'DTI':
            msg = 'DTI Model fitting...'
            model = SisypheDTIModel()
            model.setFitAlgorithm(self._method)
            tag = fa or ga or md or tr or ad or rd
            ndim = 6
        elif self._model == 'DKI':
            msg = 'DKI Model fitting...'
            model = SisypheDKIModel()
            model.setFitAlgorithm(self._method)
            tag = fa or ga or md or tr or ad or rd
            ndim = 15
        elif self._model == 'SHCSA':
            msg = 'SHCSA Model fitting...'
            model = SisypheSHCSAModel()
            model.setOrder(self._order)
            tag = gfa
            ndim = 100
        elif self._model == 'SHCSD':
            msg = 'SHCSD Model fitting...'
            model = SisypheSHCSDModel()
            model.setOrder(self._order)
            tag = gfa
            ndim = 20
        elif self._model == 'DSI':
            msg = 'DSI Model fitting...'
            model = SisypheDSIModel()
            tag = gfa
            ndim = 100
        elif self._model == 'DSID':
            msg = 'DSID Model fitting...'
            model = SisypheDSIDModel()
            tag = gfa
            ndim = 100
        else:
            self._result.put('Invalid model name ({}).'.format(self._model))
            self.terminate()
        # noinspection PyUnboundLocalVariable
        if nd < ndim:
            self._result.put('Not enough diffusion-weighted images for the {} model (at least {}).'.format(self._model, ndim))
            self.terminate()
        # noinspection PyUnboundLocalVariable
        model.setGradients(bvals, bvecs, lpstoras=self._corr)
        model.setDWI(vols)
        # Mask processing
        self._mng['msg'] = 'mask processing...'
        try: model.calcMask(self._algo, self._niter, self._size)
        except Exception as err:
            self._result.put('Mask processing error.\n{}\n{}.'.format(type(err), str(err)))
            self.terminate()
        # Model fitting
        # noinspection PyUnboundLocalVariable
        self._mng['msg'] = msg
        try: model.computeFitting()
        except Exception as err:
            self._result.put('Diffusion model fitting failed.\n{}\n{}.'.format(type(err), str(err)))
            self.terminate()
        filename = splitext(self._fbval)[0] + SisypheDTIModel.getFileExt()
        if self._save:
            self._mng['msg'] = 'Save model...'
            model.saveModel(filename, self._mng)
        if tag:
            if fa:
                self._mng['msg'] = 'Save Fractional anisotropy map...'
                v = model.getFA()
                v.setFilename(filename)
                v.setFilenameSuffix('FA')
                v.acquisition.setSequenceToFractionalAnisotropyMap()
                v.setID(model.getReferenceID())
                v.save()
            if ga:
                self._mng['msg'] = 'Save Geodesic anisotropy map...'
                v = model.getGA()
                v.setFilename(filename)
                v.setFilenameSuffix('GA')
                v.acquisition.setModalityToOT()
                v.acquisition.setSequence('GA')
                v.setID(model.getReferenceID())
                v.save()
            if gfa:
                self._mng['msg'] = 'Save Generalized fractional anisotropy map...'
                v = model.getGFA()
                v.setFilename(filename)
                v.setFilenameSuffix('GFA')
                v.acquisition.setModalityToOT()
                v.acquisition.setSequence('GFA')
                v.setID(model.getReferenceID())
                v.save()
            if md:
                self._mng['msg'] = 'Save Mean diffusivity map...'
                v = model.getMD()
                v.setFilename(filename)
                v.setFilenameSuffix('MD')
                v.acquisition.setModalityToOT()
                v.acquisition.setSequence('MD')
                v.setID(model.getReferenceID())
                v.save()
            if tr:
                self._mng['msg'] = 'Save Trace map...'
                v = model.getTrace()
                v.setFilename(filename)
                v.setFilenameSuffix('TR')
                v.acquisition.setSequenceToApparentDiffusionMap()
                v.setID(model.getReferenceID())
                v.save()
            if ad:
                self._mng['msg'] = 'Save Axial diffusivity map...'
                v = model.getAxialDiffusivity()
                v.setFilename(filename)
                v.setFilenameSuffix('AD')
                v.acquisition.setModalityToOT()
                v.acquisition.setSequence('AD')
                v.setID(model.getReferenceID())
                v.save()
            if rd:
                self._mng['msg'] = 'Save Radial diffusivity map...'
                v = model.getRadialDiffusivity()
                v.setFilename(filename)
                v.setFilenameSuffix('RD')
                v.acquisition.setModalityToOT()
                v.acquisition.setSequence('RD')
                v.setID(model.getReferenceID())
                v.save()
        self._result.put('terminate')


class ProcessDiffusionTracking(Process):
    """
    ProcessDiffusionModel

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for diffusion tracking.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessDiffusionTracking
    """
    # Special method

    """
    Private attributes

    """

    def __init__(self, model, seedcount, stepsize, maxangle, npeaks, peakthreshold,
                 minangle, minlength, alg, method, seed, stopping, mng, queue):
        Process.__init__(self)
        self._model = model
        self._seedcount = seedcount
        self._stepsize = stepsize
        self._maxangle = maxangle
        self._npeaks = npeaks
        self._peakthreshold = peakthreshold
        self._minangle = minangle
        self._minlength = minlength
        self._alg = alg
        self._method = method
        self._seed = seed
        self._stopping = stopping
        self._mng = mng
        self._result = queue

    # Public methods

    def run(self):
        self._mng['msg'] = 'Open model {}...'.format(basename(self._model))
        try: model = SisypheDiffusionModel.openModel(self._model, False, True, self._mng)
        except Exception as err:
            self._result.put('{} format is invalid.\n{}\n{}.'.format(basename(self._model), type(err), str(err)))
            self.terminate()
        # noinspection PyUnboundLocalVariable
        track = SisypheTracking(model)
        track.setSeedCountPerVoxel(self._seedcount)
        track.setStepSize(self._stepsize)
        track.setMaxAngle(self._maxangle)
        track.setNumberOfPeaks(self._npeaks)
        track.setRelativeThresholdOfPeaks(self._peakthreshold)
        track.setMinSeparationAngleOfPeaks(self._minangle)
        track.setMinLength(self._minlength)
        if self._alg == 'Deterministic':
            if self._method == 'Euler EuDX':
                track.setTrackingAlgorithmToDeterministicEulerIntegration()
            elif self._method == 'Fiber orientation distribution':
                track.setTrackingAlgorithmToDeterministicFiberOrientationDistribution()
            elif self._method == 'Parallel transport':
                track.setTrackingAlgorithmToDeterministicParallelTransport()
            elif self._method == 'Closest peak direction':
                track.setTrackingAlgorithmToDeterministicClosestPeakDirection()
        elif self._alg == 'Probabilistic':
            if self._method == 'Bootstrap direction':
                track.setTrackingAlgorithmToProbabilisticBootstrapDirection()
            elif self._method == 'Fiber orientation distribution':
                track.setTrackingAlgorithmToProbabilisticFiberOrientationDistribution()
        if self._seed['algo'] == 'FA/GFA':
            if self._seed['threshold'] is None: self._seed['threshold'] = 0.2
            track.setSeedsFromFAThreshold(self._seed['threshold'])
        elif self._seed['algo'] == 'ROI':
            filenames = self._seed['rois']
            for f in filenames:
                if not exists(f):
                    self._result.put('No such file {}.'.format(basename(f)))
                    self.terminate()
            rois = SisypheROICollection()
            self._mng['msg'] = 'Load seed ROI(s)...'
            rois.load(filenames)
            if rois[0].hasSameSize(model.getDWI().shape[:3]): track.setSeedsFromRoi(rois.union())
            else:
                self._result.put('Invalid ROI size {}.'.format(rois[0].getSize()))
                self.terminate()
        if self._stopping['algo'] == 'FA/GFA':
            if self._stopping['threshold'] is None: self._stopping['threshold'] = 0.1
            track.setStoppingCriterionToFAThreshold(self._stopping['threshold'])
        elif self._stopping['algo'] == 'ROI':
            filename = self._stopping['roi']
            if not exists(filename):
                self._result.put('No such file {}.'.format(basename(filename)))
                self.terminate()
            roi = SisypheROI()
            self._mng['msg'] = 'Load stopping ROI...'
            roi.load(filename)
            if roi.hasSameSize(model.getDWI().shape[:3]): track.setStoppingCriterionToROI(roi)
            else:
                self._result.put('Invalid ROI size {}.'.format(roi.getSize()))
                self.terminate()
        elif self._stopping['algo'] == 'GM/WM/CSF':
            # Gray matter map
            filename = self._stopping['gm']
            if not exists(filename):
                self._result.put('No such file {}.'.format(basename(filename)))
                self.terminate()
            gm = SisypheVolume()
            self._mng['msg'] = 'Load gray matter map...'
            gm.load(filename)
            if not gm.acquisition.isCerebroSpinalFluidMap():
                self._result.put('{} sequence is not gray matter map.'.format(basename(filename)))
                self.terminate()
            if not gm.hasSameSize(model.getDWI().shape[:3]):
                self._result.put('Invalid gray matter map size {}.'.format(gm.getSize()))
                self.terminate()
            # White matter map
            filename = self._stopping['wm']
            if not exists(filename):
                self._result.put('No such file {}.'.format(basename(filename)))
                self.terminate()
            wm = SisypheVolume()
            self._mng['msg'] = 'Load white matter map...'
            wm.load(filename)
            if not wm.acquisition.isWhiteMatterMap():
                self._result.put('{} sequence is not white matter map.'.format(basename(filename)))
                self.terminate()
            if not wm.hasSameSize(model.getDWI().shape[:3]):
                self._result.put('Invalid white matter map size {}.'.format(gm.getSize()))
                self.terminate()
            # Cerebro-spinal fluid map
            filename = self._stopping['csf']
            if not exists(filename):
                self._result.put('No such file {}.'.format(basename(filename)))
                self.terminate()
            csf = SisypheVolume()
            self._mng['msg'] = 'Load cerebro-spinal fluid map...'
            csf.load(filename)
            if not csf.acquisition.isCerebroSpinalFluidMap():
                self._result.put('{} sequence is not cerebro-spinal fluid map.'.format(basename(filename)))
                self.terminate()
            if not csf.hasSameSize(model.getDWI().shape[:3]):
                self._result.put('Invalid cerebro-spinal fluid map size {}.'.format(gm.getSize()))
                self.terminate()
            track.setStoppingCriterionToMaps(gm, wm, csf)
        self._mng['msg'] = 'Compute tracking...'
        try: sl = track.computeTracking(self._mng)
        except Exception as err:
            self._result.put('{} tracking failed.\n{}\n{}.'.format(basename(self._model), type(err), str(err)))
            self.terminate()
        filename = splitext(self._model)[0] + '_' + track.getBundleName() + SisypheStreamlines.getFileExt()
        self._mng['msg'] = 'save {} streamlines...'.format(track.getBundleName())
        # noinspection PyUnboundLocalVariable
        sl.save(bundle='all', filename=filename)
        if sl.getName() == 'tractogram': msg = 'Tractogram of {} streamlines.'.format(sl.count())
        else: msg = '{} tractogram of {} streamlines.'.format(sl.getName(), sl.count())
        self._result.put(['terminate', msg])