"""
External packages/modules
-------------------------

    - ANTs, image registration, https://github.com/ANTsX/ANTsPy
"""

import sys

from os import dup
from os import dup2
from os import remove

from os.path import exists
from os.path import join

from multiprocessing import Process

from ants.core import from_numpy
from ants.core import write_transform
from ants.registration import registration
from ants.segmentation import kelly_kapowski

from Sisyphe.lib.ants.atropos import atropos

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
           'ProcessDeepTissueSegmentation']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - CapturedStdout
    - Process -> ProcessSkullStrip
              -> ProcessRegistration
              -> ProcessRealignment
              -> ProcessAtropos
              -> ProcessCorticalThickness

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

    Class to redirect std::cout from the C++ registration function (ants library) to a text file.
    Used to follow progress.
    """

    # Special methods

    """
    Private attributes

    prevfd      file
    prev        file
    _filename   str
    """

    def __init__(self, filename):
        self.prevfd = None
        self.prev = None
        self._filename = filename

    def __enter__(self):
        F = open(self._filename, 'w')
        # copy sys.stdout file descriptor to prevfd
        self.prevfd = dup(sys.stdout.fileno())
        # copy stdout file descriptor to file F (sys.stdout redirected to file F)
        dup2(F.fileno(), sys.stdout.fileno())
        # copy stdout to prev
        self.prev = sys.stdout
        return F

    def __exit__(self, exc_type, exc_value, traceback):
        dup2(self.prevfd, self.prev.fileno())
        sys.stdout = self.prev


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
        vol = from_numpy(self._volume, spacing=self._spacing)
        if self._mask is not None: mask = from_numpy(self._mask, spacing=self._spacing)
        else: mask = None
        if isinstance(self._init, list):
            for i in range(len(self._init)):
                self._init[i] = from_numpy(self._init[i], spacing=self._spacing)
        # noinspection PyUnusedLocal
        with CapturedStdout(self._stdout) as F:
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
