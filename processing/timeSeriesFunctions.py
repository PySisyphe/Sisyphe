"""
External packages/modules
-------------------------

    - Nilearn, time series multivariate analysis, https://nilearn.github.io/dev/index.html
    - Numpy, scientific computing, https://numpy.org/
    - scikit-learn, data analysis, https://scikit-learn.org/stable/
"""

from os import getcwd

from os.path import join
from os.path import exists

from shutil import rmtree

from nilearn.maskers import NiftiMasker
from nilearn.maskers import NiftiLabelsMasker
from nilearn.decomposition import CanICA
from nilearn.decomposition import DictLearning

from numpy import dot
from numpy import abs
from numpy import argmax
from numpy import arctanh
from numpy import ndarray
from numpy.random import RandomState

from sklearn.decomposition import PCA
from sklearn.decomposition import FastICA
from sklearn.covariance import GraphicalLassoCV

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['seriesPreprocessing',
           'seriesSeedToVoxel',
           'seriesPCA',
           'seriesFastICA',
           'seriesConnectivityMatrix',
           'seriesGroupICA']
"""
Functions
~~~~~~~~~

    - seriesPreprocessing
    - seriesSeedToVoxel
    - seriesPCA
    - seriesFastICA
    - seriesConnectivityMatrix
    - seriesGroupICA
    
Last revision: 12/06/2025
"""

def seriesPreprocessing(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
                        confmat: ndarray | None = None,
                        fwhm: float | None = None,
                        detrend: bool = True,
                        std: bool = False,
                        stdconfounds: bool = True,
                        highvarconfounds: bool = False,
                        lowpass: float | None = 0.1,
                        highpass: float | None = 0.01,
                        tr: float = 2.0,
                        wait: DialogWait | None = None) -> SisypheVolume:
    """
    Time series preprocessing:
    - extract confound regressor variables
    (example of confound variables: motion correction parameters, global signal, wm signal, csf signal)
    - gaussian spatial smoothing
    - detrend
    - standardize signal (z-scored i.e. timeseries are shifted to zero mean and scaled to unit variance)
    - standardize confound regressor variables (z-scored)
    - high variance confounds computation
    - low pass filter
    - high pass filter

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
        time series
    confmat : numpy.ndarray | None
        confound regressor matrix, one column vector for each confound regressor variable
    fwhm : float | None
        gaussian smoothing fwhm in mm (default None, no smoothing)
    detrend : bool
        whether to detrend signals or not (default True)
    std : bool
        signal is z-scored. Timeseries are shifted to zero mean and scaled to unit variance (default False)
    stdconfounds : bool
        the confounds are z-scored: their mean is put to 0 and their variance to 1 in the time dimension (default True)
    highvarconfounds : bool
        if True, high variance confounds are computed on provided image (default False)
    lowpass : float | None
        low pass filter cutoff frequency in Hertz (default 0.1)
    highpass : float | None
        high pass filter cutoff frequency in Hertz (default 0.01)
    tr : float
        repetition time in s (default 2.0 s)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        cleaned time series
    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if wait is not None:
                wait.setInformationText('{}\nPerform time series preprocessing...'.format(vols.getBasename()))
            masker = NiftiMasker(smoothing_fwhm=fwhm,
                                 standardize=std,
                                 standardize_confounds=stdconfounds,
                                 high_variance_confounds=highvarconfounds,
                                 detrend=detrend,
                                 low_pass=lowpass,
                                 high_pass=highpass,
                                 t_r=tr,
                                 mask_strategy='epi',
                                 memory="nilearn_cache",
                                 memory_level=1)
            series = masker.fit_transform(vols.copyToNibabelImage(), confounds=confmat)
            # < Revision 12/06/2025
            # img = masker.inverse_transform(series.T)
            img = masker.inverse_transform(series)
            r = SisypheVolume()
            # r.copyFromNumpyArray(img,
            #                      spacing=vols.getSpacing(),
            #                      origin=vols.getOrigin(),
            #                      direction=vols.getDirections())
            r.copyFromNumpyArray(img.get_fdata(),
                                 spacing=vols.getSpacing(),
                                 origin=vols.getOrigin(),
                                 direction=vols.getDirections(),
                                 defaultshape=False)
            # Revision 12/06/2025 >
            r.copyAttributesFrom(vols, display=False, slope=False)
            # < Revision 12/06/2025
            # remove nilearn cache
            cache = join(getcwd(), 'nilearn_cache')
            if exists(cache): rmtree(cache)
            # Revision 12/06/2025 >
            return r
        else: raise AttributeError('Parameter is not a multi-component image.')
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


def seriesSeedToVoxel(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
                      roi: SisypheROI | None = None,
                      confmat: ndarray | None = None,
                      fwhm: float | None = None,
                      detrend: bool = True,
                      std: bool = False,
                      stdconfounds: bool = True,
                      highvarconfounds: bool = False,
                      lowpass: float | None = 0.1,
                      highpass: float | None = 0.01,
                      tr: float = 2.0,
                      wait: DialogWait | None = None) -> dict[str, SisypheVolume]:
    """
    Seed to voxel correlation map processing.
    This map depicts the temporal correlation of a seed region with the rest of the brain.

    Reference: https://nilearn.github.io/dev/auto_examples/03_connectivity/plot_seed_to_voxel_correlation.html

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
        time series
    roi : Sisyphe.core.sisypheROI.SisypheROI | None
        seed ROI (default None, no seed ROI)
    confmat : numpy.ndarray | None
        confound regressor matrix, one column vector for each confound regressor variable
    fwhm : float | None
        gaussian smoothing fwhm in mm (default None, no smoothing)
    detrend : bool
        whether to detrend signals or not (default True)
    std : bool
        signal is z-scored. Timeseries are shifted to zero mean and scaled to unit variance (default False)
    stdconfounds : bool
        the confounds are z-scored: their mean is put to 0 and their variance to 1 in the time dimension (default True)
    highvarconfounds : bool
        if True, high variance confounds are computed on provided image (default False)
    lowpass : float | None
        low pass filter cutoff frequency in Hertz (default 0.1)
    highpass : float | None
        high pass filter cutoff frequency in Hertz (default 0.01)
    tr : float
        repetition time in s (default 2.0 s)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    dict[str, SisypheVolume]
        keys: 'cc': correlation coeff. map, 'z': z-map
    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if wait is not None:
                wait.setInformationText('{}\nPreprocessing...'.format(vols.getBasename()))
            masker = NiftiMasker(smoothing_fwhm=fwhm,
                                 standardize=std,
                                 standardize_confounds=stdconfounds,
                                 high_variance_confounds=highvarconfounds,
                                 detrend=detrend,
                                 low_pass=lowpass,
                                 high_pass=highpass,
                                 t_r=tr,
                                 mask_strategy='epi',
                                 memory="nilearn_cache",
                                 memory_level=1)
            series = masker.fit_transform(vols.copyToNibabelImage(), confounds=confmat)
            if wait is not None:
                wait.setInformationText('{}\nSeed signal extraction...'.format(vols.getBasename()))
            smasker = NiftiLabelsMasker(labels_img=roi.copyToNibabelImage(),
                                        standardize=std,
                                        standardize_confounds=stdconfounds,
                                        high_variance_confounds=highvarconfounds,
                                        detrend=detrend,
                                        low_pass=lowpass,
                                        high_pass=highpass,
                                        t_r=tr,
                                        memory="nilearn_cache",
                                        memory_level=1)
            seed = smasker.fit_transform(vols.copyToNibabelImage(), confounds=confmat)
            if wait is not None:
                wait.setInformationText('{}\nCorrelation processing...'.format(vols.getBasename()))
            cc = dot(series.T, seed) / seed.shape[0]
            img = masker.inverse_transform(cc.T)
            r = dict()
            r['cc'] = SisypheVolume()
            r['cc'].copyFromNumpyArray(img.get_fdata(),
                                       spacing=vols.getSpacing(),
                                       origin=vols.getOrigin(),
                                       direction=vols.getDirections(),
                                       defaultshape=False)
            r['cc'].copyAttributesFrom(vols, display=False, slope=False)
            r['cc'].display.getLUT().setLut('flow')
            r['cc'].display.updateVTKLUT()
            r['cc'].display.setSymmetricWindow()
            r['cc'].acquisition.setSequenceToCMap()
            r['cc'].setFilename(vols.getFilename())
            r['cc'].setFilenameSuffix('seed_cmap')
            z = arctanh(cc)
            img = masker.inverse_transform(z.T)
            r['z'] = SisypheVolume()
            r['z'].copyFromNumpyArray(img.get_fdata(),
                                      spacing=vols.getSpacing(),
                                      origin=vols.getOrigin(),
                                      direction=vols.getDirections(),
                                      defaultshape=False)
            r['z'].copyAttributesFrom(vols, display=False, slope=False)
            r['z'].display.getLUT().setLut('flow')
            r['z'].display.updateVTKLUT()
            r['z'].display.setSymmetricWindow()
            r['z'].acquisition.setSequenceToZMap()
            r['z'].acquisition.setAutoCorrelations([fwhm, fwhm, fwhm])
            r['z'].setFilename(vols.getFilename())
            r['z'].setFilenameSuffix('seed_zmap')
            # < Revision 12/06/2025
            # remove nilearn cache
            cache = join(getcwd(), 'nilearn_cache')
            if exists(cache): rmtree(cache)
            # Revision 12/06/2025 >
            return r
        else: raise AttributeError('Parameter is not a multi-component image.')
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


def seriesPCA(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
              whiten: bool = False,
              threshold: float = 0.9,
              wait: DialogWait | None = None) -> SisypheVolume:
    """
    Apply PCA to timeseries data using scikit-learn PCA algorithm.

    Principal Component Analysis (PCA) is a statistical procedure that uses an orthogonal transformation to convert a
    set of observations of possibly correlated variables into a set of values of linearly uncorrelated variables called
    principal components.

    Reference: https://scikit-learn.org/stable/modules/decomposition.html#pca

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
        time series
    whiten : bool
        whitening will remove some information from the transformed signal (the relative variance scales of the
        components) but can sometime improve the predictive accuracy of the downstream estimators by making their data
        respect some hard-wired assumptions.
    threshold : float
        explained variance ratio threshold (default 0.9)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        cleaned time series

    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if wait is not None:
                wait.setInformationText('{}\nPCA preprocessing...'.format(vols.getBasename()))
            masker = NiftiMasker(memory='nilearn_cache',
                                 memory_level=1,
                                 mask_strategy='epi',
                                 standardize='zscore_sample')
            series = masker.fit_transform(vols.copyToNibabelImage())
            if wait is not None:
                wait.setInformationText('{}\nPCA processing...'.format(vols.getBasename()))
            rng = RandomState(42)
            pca = PCA(svd_solver='full', whiten=whiten, random_state=rng)
            comp = pca.fit_transform(series.T).T
            # noinspection PyTypeChecker
            idx = argmax(comp.explained_variance_ratio_.cumsum() >= threshold) + 1
            if idx < comp.shape[1] - 1: comp[idx:] = 0
            img = pca.inverse_transform(comp)
            img = masker.inverse_transform(img)
            r = SisypheVolume()
            # < Revision 12/06/2025
            # r.copyFromNumpyArray(img.get_fdata(),
            #                      spacing=vols.getSpacing(),
            #                      origin=vols.getOrigin(),
            #                      direction=vols.getDirections())
            r.copyFromNumpyArray(img.get_fdata(),
                                 spacing=vols.getSpacing(),
                                 origin=vols.getOrigin(),
                                 direction=vols.getDirections(),
                                 defaultshape=False)
            # Revision 12/06/2025 >
            r.copyAttributesFrom(vols, display=False, slope=False)
            # < Revision 12/06/2025
            # remove nilearn cache
            cache = join(getcwd(), 'nilearn_cache')
            if exists(cache): rmtree(cache)
            # Revision 12/06/2025 >
            return r
        else: raise AttributeError('Parameter is not a multi-component image.')
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


def seriesFastICA(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
                  ncomp: int = 10,
                  threshold: float = 0.8,
                  confmat: ndarray | None = None,
                  fwhm: float | None = None,
                  detrend: bool = True,
                  stdconfounds: bool = True,
                  highvarconfounds: bool = False,
                  lowpass: float | None = 0.1,
                  highpass: float | None = 0.01,
                  tr: float = 2.0,
                  wait: DialogWait | None = None) -> SisypheVolume:
    """
    Apply ICA to a single-subject timeseries data using scikit-learn Fast ICA algorithm.

    Independent component analysis (ICA) separates a multivariate signal into additive subcomponents that are maximally
    independent. Typically, ICA is not used for reducing dimensionality but for separating superimposed signals.

    Reference: https://scikit-learn.org/1.5/modules/decomposition.html#ica

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
        time series
    ncomp : int
        number of components (default 10)
    threshold : float
        components threshold
    confmat : numpy.ndarray | None
        confound regressor matrix, one column vector for each confound regressor variable
    fwhm : float | None
        gaussian smoothing fwhm in mm (default None, no smoothing)
    detrend : bool
        whether to detrend signals or not (default True)
    stdconfounds : bool
        the confounds are z-scored: their mean is put to 0 and their variance to 1 in the time dimension (default True)
    highvarconfounds : bool
        if True, high variance confounds are computed on provided image (default False)
    lowpass : float | None
        low pass filter cutoff frequency in Hertz (default 0.1)
    highpass : float | None
        high pass filter cutoff frequency in Hertz (default 0.01)
    tr : float
        repetition time in s (default 2.0 s)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        ICA components
    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if wait is not None:
                wait.setInformationText('{}\nPreprocessing...'.format(vols.getBasename()))
            if fwhm == 0: fwhm = None
            masker = NiftiMasker(smoothing_fwhm=fwhm,
                                 standardize='zscore_sample',
                                 standardize_confounds=stdconfounds,
                                 high_variance_confounds=highvarconfounds,
                                 detrend=detrend,
                                 low_pass=lowpass,
                                 high_pass=highpass,
                                 t_r=tr,
                                 mask_strategy='epi',
                                 memory="nilearn_cache",
                                 memory_level=1)
            series = masker.fit_transform(vols.copyToNibabelImage(), confounds=confmat)
            if wait is not None:
                wait.setInformationText('{}\nSingle-subject ICA processing...'.format(vols.getBasename()))
            rng = RandomState(42)
            ica = FastICA(n_components=ncomp, random_state=rng)
            comp = ica.fit_transform(series.T).T
            comp -= comp.mean(axis=0)
            comp /= comp.std(axis=0)
            comp[abs(comp) < threshold] = 0
            compimg = masker.inverse_transform(comp)
            r = SisypheVolume()
            r.copyFromNumpyArray(compimg.get_fdata(),
                                 spacing=vols.getSpacing(),
                                 origin=vols.getOrigin(),
                                 direction=vols.getDirections(),
                                 defaultshape=False)
            r.copyAttributesFrom(vols, display=False, slope=False)
            r.display.getLUT().setLut('flow')
            r.display.updateVTKLUT()
            r.acquisition.setSequenceToZMap()
            r.acquisition.setAutoCorrelations([fwhm, fwhm, fwhm])
            r.setFilename(vols.getFilename())
            r.setFilenameSuffix('ica')
            # < Revision 12/06/2025
            # remove nilearn cache
            cache = join(getcwd(), 'nilearn_cache')
            if exists(cache): rmtree(cache)
            # Revision 12/06/2025 >
            return r
        else: raise AttributeError('Parameter is not a multi-component image.')
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


# noinspection PyTypeChecker
def seriesConnectivityMatrix(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
                             lbls: SisypheVolume,
                             confmat: ndarray | None = None,
                             fwhm: float | None = None,
                             detrend: bool = True,
                             std: bool = False,
                             stdconfounds: bool = True,
                             highvarconfounds: bool = False,
                             lowpass: float | None = 0.1,
                             highpass: float | None = 0.01,
                             tr: float = 2.0,
                             wait: DialogWait | None = None) -> ndarray:
    """
    Connectivity covariance matrix processing.

    Reference: https://nilearn.github.io/dev/auto_examples/03_connectivity/plot_inverse_covariance_connectome.html

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
        time series
    lbls : Sisyphe.core.sisypheVolume.SisypheVolume
        label image
    confmat : numpy.ndarray | None
        confound regressor matrix, one column vector for each confound regressor variable
    fwhm : int
        gaussian smoothing fwhm in mm (default None, no smoothing)
    detrend : bool
        whether to detrend signals or not (default True)
    std : bool
        signal is z-scored. Timeseries are shifted to zero mean and scaled to unit variance (default False)
    stdconfounds : bool
        the confounds are z-scored: their mean is put to 0 and their variance to 1 in the time dimension (default True)
    highvarconfounds : bool
        if True, high variance confounds are computed on provided image (default False)
    lowpass : float | None
        low pass filter cutoff frequency in Hertz (default 0.1)
    highpass : float | None
        high pass filter cutoff frequency in Hertz (default 0.01)
    tr : float
        repetition time in s (default 2.0 s)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    ndarray
        connectome covariance matrix
    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if wait is not None:
                wait.setInformationText('{}\nPreprocessing...'.format(vols.getBasename()))
            masker = NiftiLabelsMasker(labels_img=lbls.copyToNibabelImage(),
                                       smoothing_fwhm=fwhm,
                                       standardize=std,
                                       standardize_confounds=stdconfounds,
                                       high_variance_confounds=highvarconfounds,
                                       detrend=detrend,
                                       low_pass=lowpass,
                                       high_pass=highpass,
                                       t_r=tr,
                                       memory="nilearn_cache",
                                       memory_level=1)
            series = masker.fit_transform(vols.copyToNibabelImage(), confounds=confmat)
            if wait is not None:
                wait.setInformationText('{}\nConnectome processing...'.format(vols.getBasename()))
            estimator = GraphicalLassoCV()
            estimator.fit(series)
            # < Revision 12/06/2025
            # remove nilearn cache
            cache = join(getcwd(), 'nilearn_cache')
            if exists(cache): rmtree(cache)
            # Revision 12/06/2025 >
            return estimator.covariance_
        else: raise ValueError('Parameter volume is single component volume.'.format())
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


# noinspection PyTypeChecker,PyUnusedLocal
def seriesGroupICA(vols: list[SisypheVolume],
                   ncomp: int = 20,
                   algo: str = 'ica',
                   wait: DialogWait | None = None) -> SisypheVolume:
    """
    Derive spatial maps or networks from group fMRI time-series data (multi-subject) using CanICA or Dict Learning
    methods provided in the NiLearn module.

    This function extracts distributed brain regions that exhibit similar BOLD fluctuations over time.
    Decomposition methods allow for generation of many independent maps (components) simultaneously without the need
    to provide a priori information.

    Reference:
    https://nilearn.github.io/dev/auto_examples/03_connectivity/plot_compare_decomposition.html
    https://nilearn.github.io/dev/modules/generated/nilearn.decomposition.CanICA.html
    https://nilearn.github.io/dev/modules/generated/nilearn.decomposition.DictLearning.html

    Parameters
    ----------
    vols : list[Sisyphe.core.sisypheVolume.SisypheVolume]
        list of time series
    ncomp : int
        Number of components to extract.
    algo : str
        decomposition methods: 'ica' as CanICA, 'dict' as dictionary learning
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        components extracted
    """
    if len(vols) > 0:
        data = list()
        n = vols[0].getNumberOfComponentsPerPixel()
        if n > 1:
            for v in vols:
                if v.acquisition.isICBM152():
                    if v.getNumberOfComponentsPerPixel() == n:
                        data.append(v.copyToNibabelImage())
                    else: raise ValueError('Number of components mismatch '
                                           '({} expected, {} provided.'.format(n,
                                                                               v.getNumberOfComponentsPerPixel()))
                else: AttributeError('Parameter element is not in ICBM152 normalized space.')
        else: raise AttributeError('Parameter element is not a multi-component image.')
        # noinspection PyUnreachableCode
        if len(data) > 1:
            func = None
            if algo == 'ica': func = CanICA
            elif algo == 'dict': func = DictLearning
            if func is not None:
                if wait is not None:
                    if algo == 'ica': wait.setInformationText('Multi-subject ICA processing...')
                    else: wait.setInformationText('Multi-subject Dict Learning processing...')
                f = func(n_components=ncomp,
                         smoothing_fwhm=None,
                         standardize_confounds=False,
                         memory='nilearn_cache',
                         memory_level=2,
                         standardize='zscore_sample',
                         n_jobs=2)
                f.fit(data)
                comp = f.components_img_
                r = SisypheVolume()
                r.copyFromNibabelImage(comp)
                r.copyAttributesFrom(vols[0], display=False, slope=False)
                r.acquisition.setSequenceToZMap()
                r.setFilename(vols[0].getFilename())
                r.setFilenamePrefix('components')
                return r
            else: raise ValueError('Algorithm {} is not supported (must be \'ica\' or \'dict\').'.format(algo))
        else: raise ValueError('Parameter volume is single comporent.')
    else: raise TypeError('Parameter type {} is not list'.format(type(vols)))
