"""
External packages/modules
-------------------------

    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - Numpy, scientific computing, https://numpy.org/
"""

from os.path import basename

from dipy.core.gradients import GradientTable
from dipy.denoise.gibbs import gibbs_removal
# < Revision 18/06/2025
# from dipy.denoise.localpca import genpca
# from dipy.denoise.localpca import localpca
# from dipy.denoise.localpca import mppca
# from dipy.denoise.nlmeans import nlmeans
# from dipy.denoise.non_local_means import non_local_means
# Revision 18/06/2025 >
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.patch2self import patch2self
from dipy.denoise.noise_estimate import piesno
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.pca_noise_estimate import pca_noise_estimate

from datetime import datetime

from numpy import array
from numpy import ndarray

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheDicom import removeSuffixNumberFromFilename
# < Revision 18/06/2025
from Sisyphe.lib.dipy.localpca import genpca
from Sisyphe.lib.dipy.localpca import localpca
from Sisyphe.lib.dipy.localpca import mppca
from Sisyphe.lib.dipy.non_local_means import non_local_means
# Revision 18/06/2025 >
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['dwiNoiseEstimation',
           'getLocalPCAParameterDict',
           'getGeneralFunctionPCAParameterDict',
           'getMarcenkoPasturPCAParameterDict',
           'getNonLocalMeansParameterDict',
           'getSelfSupervisedDenoisingParameterDict',
           'getAdaptiveSoftCoefficientMatchingParameterDict',
           'dwiPreprocessing']

"""
functions
~~~~~~~~~

    - dwiNoiseEstimation()
    - getLocalPCADict()
    - getGeneralFunctionPCAParameterDict()
    - getMarcenkoPasturPCAParameterDict()
    - getNonLocalMeansParameterDict()
    - getSelfSupervisedDenoisingParameterDict()
    - getAdaptiveSoftCoefficientMatchingParameterDict()
    - dwiPreprocessing()
        
Creation: 08/11/2023
Last revision: 17/06/2025
"""

_NOISE = ('Local patches', 'Piesno')

_DENOISE = ('Local PCA',
            'General function PCA',
            'Marcenko-Pastur PCA',
            'Non-local means',
            'Self-Supervised Denoising',
            'Adaptive soft coefficient matching')

def dwiNoiseEstimation(vol: SisypheVolume | SisypheVolumeCollection,
                       algo: str = 'Local patches',
                       rec: str = '',
                       n_coils: int = 0,
                       n_phase_coils: int = 1,
                       wait: DialogWait | None = None) -> float | ndarray:
    """
    Parameters
    ----------
    vol : SisypheVolume | SisypheVolumeCollection
        dwi volume(s)
    algo : str
        'Local patches' or 'Piesno', noise estimation algorithm
    rec : str
        'SENSE' (Philips) or 'GRAPPA' (GE or Siemens), MR multi-coils receiver array reconstruction
    n_coils : int
        number of coils of the receiver array (0 to disable correction factor)
        use N = 1 in case of a SENSE reconstruction (Philips)
        or the number of coils for a GRAPPA reconstruction (Siemens or GE).
        use N = 0 to disable the correction factor,
        as for example if the noise is Gaussian distributed.
    n_phase_coils : int
        number of phase array coils
        if scanner does a SENSE reconstruction,
        always use N = 1, as the noise profile is always Rician.
        if scanner does a GRAPPA reconstruction, set N as the number of phase array coils.
    wait : DialogWait
        optional progress dialog

    Returns
    -------
    float
        noise
    """
    if algo not in _NOISE: algo = _NOISE[0]
    if rec.lower() == 'sense':
        n_coils = 1
        n_phase_coils = 1
    if algo == _NOISE[0]:
        """
            Number of coils of the receiver array. 
            Use N = 1 in case of a SENSE reconstruction (Philips) 
            or the number of coils for a GRAPPA reconstruction (Siemens or GE).
            Use 0 to disable the correction factor, as for example if the noise is Gaussian distributed.
        """
        if isinstance(vol, SisypheVolume):
            if wait is not None: wait.setInformationText('{}\n'
                                                         '{} noise estimation...'.format(vol.getBasename(), algo))
            img = vol.copyToNumpyArray(defaultshape=False)
            sigma = estimate_sigma(img, N=n_coils)
        elif isinstance(vol, SisypheVolumeCollection):
            l = list()
            for v in vol:
                if wait is not None: wait.setInformationText('{}\n'
                                                             '{} noise estimation...'.format(v.getBasename(), algo))
                img = v.copyToNumpyArray(defaultshape=False)
                s = estimate_sigma(img, N=n_coils)
                l.append(s)
            sigma = array(l)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheVolumeCollection.')
    else:
        """
            Number of phase array coils of the MRI scanner. 
            If scanner does a SENSE reconstruction, always use N = 1, as the noise profile is always Rician. 
            If scanner does a GRAPPA reconstruction, set N as the number of phase array coils.
        """
        if isinstance(vol, SisypheVolume):
            if wait is not None: wait.setInformationText('{}\n'
                                                         '{} noise estimation...'.format(vol.getBasename(), algo))
            img = vol.copyToNumpyArray(defaultshape=False)
            sigma = piesno(img, N=n_phase_coils)
        elif isinstance(vol, SisypheVolumeCollection):
            l = list()
            for v in vol:
                if wait is not None: wait.setInformationText('{}\n'
                                                             '{} noise estimation...'.format(v.getBasename(), algo))
                img = v.copyToNumpyArray(defaultshape=False)
                s = piesno(img, N=n_phase_coils)
                l.append(s)
            sigma = array(l)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheVolumeCollection.')
    return sigma

def getLocalPCAParameterDict() -> dict[str, int | str]:
    return {'algo': 'Local PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getGeneralFunctionPCAParameterDict() -> dict[str, int | str]:
    return {'algo': 'General function PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getMarcenkoPasturPCAParameterDict() -> dict[str, int | str]:
    return {'algo': 'Marcenko-Pastur PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getNonLocalMeansParameterDict() -> dict[str, int | str]:
    return {'algo': 'Non-local means', 'ncoils': 0, 'patchradius': 1, 'blockradius': 5}

def getSelfSupervisedDenoisingParameterDict() -> dict[str, int | str]:
    return {'algo': 'Self-Supervised Denoising', 'radius': 0, 'solver': 'ols'}

def getAdaptiveSoftCoefficientMatchingParameterDict() -> dict[str, int | str]:
    return {'algo': 'Adaptive soft coefficient matching', 'ncoils': 0}

def dwiPreprocessing(vols: SisypheVolumeCollection,
                     prefix: str = 'f',
                     suffix: str = '',
                     gtab: GradientTable | None = None,
                     brainseg: dict[str, int | str] | None = None,
                     gibbs: dict[str, int] | None = None,
                     denoise: dict[str, int | str] | None = None,
                     save: bool = False,
                     wait: DialogWait | None = None) -> tuple[SisypheVolumeCollection, SisypheROI | None] | None:
    """
    Parameters
    ----------
    vols : SisypheVolumeCollection
        dwi volumes
    prefix : str
        prefix filename for filtered dwi volumes
    suffix : str
        suffix filename for filtered dwi volumes
    gtab : GradientTable | None
        required for PCA, Non-local means and Self-Supervised denoising algorithms
    brainseg : dict[str, int | str]
        {'algo': str = 'huang', 'size': int = 1, 'niter': int = 2}
    gibbs : dict[str, int]
        {'neighbour': int = 3}
    denoise : dict[str, int | str]
        {'algo': 'Local PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
        {'algo': 'General function PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
        {'algo': 'Marcenko-Pastur PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
        {'algo': 'Non-local means', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int, 'patchradius': int = 1, 'blockradius': int = 5}
        {'algo': 'Self-Supervised Denoising', 'radius': int = 0, 'solver': str = 'ols'}
        {'algo': 'Adaptive soft coefficient matching', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int}
    save : bool
        save if true
    wait : DialogWait
        optional progress dialog

    Returns
    -------
    SisypheVolumeCollection : SisypheROI | None
    """
    mask = None
    # < Revision 17/06/2025
    # bug fix, img = vols.getNumpy(defaultshape=False)
    imgs = vols.copyToNumpyArray(defaultshape=False)
    # Revision 17/06/2025 >
    # Brain segmentation
    if brainseg is not None:
        if len(brainseg) == 0: brainseg = {'algo': 'huang', 'size':  1, 'niter': 2}
        if wait is not None: wait.setInformationText('Mask processing...')
        """
        algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                        'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        algorithm used for automatic object/background segmentation (default otsu)
        size    int, structuring element size of binary morphology operator (default 1)
        niter   int, number of binary morphology iterations (default 1)
        """
        if 'algo' in brainseg: algo = brainseg['algo']
        else: algo = 'otsu'
        if 'size' in brainseg: size = brainseg['size']
        else: size = 1
        if 'niter' in brainseg: niter = brainseg['niter']
        else: niter = 2
        # < Revision 17/06/2025
        # mvol = SisypheVolume(img.mean(axis=3), spacing=vols[0].getSpacing())
        mvol = vols.getMeanVolume()
        # Revision 17/06/2025 >
        buff = mvol.getMask2(algo, niter, size)
        mask = buff.getNumpy(defaultshape=False)
        if save:
            rmask = SisypheROI()
            rmask.copyFromNumpyArray(mask,
                                     spacing=vols[0].getSpacing(),
                                     origin=vols[0].getOrigin(),
                                     direction=vols[0].getDirections(),
                                     defaultshape=False)
            filename = removeSuffixNumberFromFilename(vols[0].getFilename())
            rmask.setReferenceID(vols[0].getID())
            rmask.setFilename(filename)
            rmask.setFilenameSuffix('mask')
            if wait is not None: wait.setInformationText('Save {}...'.format(basename(rmask.getFilename())))
            rmask.save()
        else: rmask = None
    # Gibbs suppression
    if gibbs is not None:
        if len(gibbs) == 0: gibbs = {'neighbour': 3}
        if wait is not None: wait.setInformationText('Gibbs correction...')
        """
        neighbour int, number of neighbour points to access local TV (default 3)
        """
        # < Revision 17/06/2025
        # bug fix, return value
        # gibbs_removal(img, n_points=gibbs['neighbour'])
        n = imgs.shape[3]
        wait.setProgressRange(0, n+1)
        wait.setCurrentProgressValue(0)
        wait.setProgressVisibility(True)
        t = datetime.now()
        for i in range(n):
            if i > 0:
                now = datetime.now()
                delta = now - t
                t = now
                delta *= n - i
                m = delta.seconds // 60
                s = delta.seconds - (m * 60)
                if m == 0:
                    wait.addInformationText('Estimated time remaining {} s.'.format(s))
                else:
                    wait.addInformationText('Estimated time remaining {} min {} s.'.format(m, s))
            img = imgs[:, :, :, i]
            img = gibbs_removal(img, n_points=gibbs['neighbour'], inplace=False)
            imgs[:, :, :, i] = img
            wait.setCurrentProgressValue(i + 1)
            # if wait.getStopped():
            #    wait.setProgressVisibility(False)
            #    return None
        wait.setProgressVisibility(False)
        # Revision 17/06/2025 >
    # Denoising
    if denoise is not None:
        if len(denoise) == 0:
            # Default denoising algorithm with parameters
            denoise = {'algo': 'Local PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}
        # Local PCA denoising
        if denoise['algo'] == _DENOISE[0]:
            if 'smooth' in denoise: smooth = denoise['smooth']
            else: smooth = 2
            if wait is not None: wait.setInformationText('Noise estimation...')
            sigma = pca_noise_estimate(imgs, gtab, smooth=smooth)
            """
            patch_radius    int, radius of the local patch to be taken around each voxel 
                                 patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
            gtab            GradientTable
            pca_method      str, ‘eig’ or ‘svd’ (default eig)
                                 eigenvalue decomposition (eig) or singular value decomposition (svd) 
                                 for principal component analysis. The default method is ‘eig’ which is faster. 
                                 However, occasionally ‘svd’ might be more accurate.
            tau_factor      float, thresholding of PCA eigenvalues is done by nulling out eigenvalues 
                                   that are smaller than tau = (tau_factor x sigma)**2 (default 2.3)
            """
            if 'radius' in denoise: radius = denoise['radius']
            else: radius = 2
            if 'method' in denoise: method = denoise['method'].lower()
            else: method = 'eig'
            if wait is not None: wait.setInformationText('Local PCA denoising...')
            imgs = localpca(imgs, sigma=sigma, mask=mask, patch_radius=radius, pca_method=method, tau_factor=2.3, wait=wait)
        # General function PCA denoising
        elif denoise['algo'] == _DENOISE[1]:
            if 'smooth' in denoise: smooth = denoise['smooth']
            else: smooth = 2
            if wait is not None: wait.setInformationText('Noise estimation...')
            sigma = pca_noise_estimate(imgs, gtab, smooth=smooth)
            """
                patch_radius    int, radius of the local patch to be taken around each voxel 
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
                pca_method      str, ‘eig’ or ‘svd’ (default eig)
                                     eigenvalue decomposition (eig) or singular value decomposition (svd) 
                                     for principal component analysis. The default method is ‘eig’ which is faster. 
                                     However, occasionally ‘svd’ might be more accurate.
                tau_factor      float, thresholding of PCA eigenvalues is done by nulling out eigenvalues 
                                       that are smaller than tau = (tau_factor x sigma)**2 (default 2.3)
            """
            if 'radius' in denoise: radius = denoise['radius']
            else: radius = 2
            if 'method' in denoise: method = denoise['method'].lower()
            else: method = 'eig'
            if wait is not None: wait.setInformationText('General function PCA denoising...')
            imgs = genpca(imgs, sigma=sigma, mask=mask, patch_radius=radius, pca_method=method, tau_factor=2.3, wait=wait)
        # Marcenko-Pastur PCA denoising
        elif denoise['algo'] == _DENOISE[2]:
            """
                patch_radius    int, radius of the local patch to be taken around each voxel 
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
                pca_method      str, ‘eig’ or ‘svd’ (default eig)
                                     eigenvalue decomposition (eig) or singular value decomposition (svd) 
                                     for principal component analysis. The default method is ‘eig’ which is faster. 
                                     However, occasionally ‘svd’ might be more accurate.
            """
            if 'radius' in denoise: radius = denoise['radius']
            else: radius = 2
            if 'method' in denoise: method = denoise['method'].lower()
            else: method = 'eig'
            if wait is not None: wait.setInformationText('Marcenko-Pastur PCA denoising...')
            imgs = mppca(imgs, mask=mask, patch_radius=radius, pca_method=method, wait=wait)
        # Non-local means denoising
        elif denoise['algo'] == _DENOISE[3]:
            if wait is not None: wait.setInformationText('Noise estimation...')
            """
                noisealgo       str, 'Local patches' or 'Piesno', noise estimation algorithm
                rec             str, 'SENSE' (Philips) or 'GRAPPA' (GE or Siemens), MR multi-coils receiver array reconstruction
                ncoils          int, number of coils of the receiver array (0 to disable correction factor)
                                     use N = 1 in case of a SENSE reconstruction (Philips)
                                     or the number of coils for a GRAPPA reconstruction (Siemens or GE).
                                     use N = 0 to disable the correction factor,
                                     as for example if the noise is Gaussian distributed.
                nphase          int, number of phase array coils
                                     if scanner does a SENSE reconstruction,
                                     always use N = 1, as the noise profile is always Rician.
                                     if scanner does a GRAPPA reconstruction, set N as the number of phase array coils.
            """
            if 'noisealgo' in denoise: noisealgo = denoise['noisealgo']
            else: noisealgo = _NOISE[0]
            if 'ncoils' in denoise: ncoils = denoise['ncoils']
            else: ncoils = 0
            if 'nphase' in denoise: nphase = denoise['nphase']
            else: nphase = 1
            if 'rec' in denoise:
                rec = denoise['rec']
                if denoise['rec'].lower() == 'sense':
                    ncoils = 1
                    nphase = 1
            else: rec = 'SENSE'
            sigma = dwiNoiseEstimation(vols, noisealgo, rec, ncoils, nphase, wait)
            """
                patch_radius    int, radius of the local patch to be taken around each voxel (default 1)
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
                block_radius    int, radius of the local patch to be taken around each voxel  (default 5)
                                     block size = block_radius x 2 + 1 (ex: 2 gives 5x5x5 blocks)
                rician      boolean, if True the noise is estimated as Rician, otherwise Gaussian noise is assumed
            """
            if 'patchradius' in denoise: patchradius = denoise['patchradius']
            else: patchradius = 1
            if 'blockradius' in denoise: blockradius = denoise['blockradius']
            else: blockradius = 5
            if wait is not None: wait.setInformationText('Non-local means denoising...')
            # imgs = nlmeans(imgs, sigma, mask, patch_radius=patchradius, block_radius=blockradius, rician=True)
            imgs = non_local_means(imgs, sigma=sigma, mask=mask, patch_radius=patchradius, block_radius=blockradius, rician=True, wait=wait)
        # Self-Supervised denoising
        elif denoise['algo'] == _DENOISE[4]:
            """
                bvals           ndarray, array of bvals from the DWI acquisition
                model           str, ‘ols’, ‘ridge’ or ‘lasso’ (default ols)
                                     algorithm used to solve the set of linear equations
                patch_radius    int, radius of the local patch to be taken around each voxel (default 0)
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
            """
            if 'patchradius' in denoise: patchradius = denoise['patchradius']
            else: patchradius = 0
            if 'method' in denoise: method = denoise['method']
            else: method = 'ols'
            if wait is not None: wait.setInformationText('Self-Supervised denoising...')
            imgs = patch2self(imgs, bvals=gtab.bvals, model=method, patch_radius=patchradius)
        # Adaptive soft coefficient matching denoising
        elif denoise['algo'] == _DENOISE[5]:
            if wait is not None: wait.setInformationText('Noise estimation...')
            """
                noisealgo       str, 'Local patches' or 'Piesno', noise estimation algorithm
                rec             str, 'SENSE' (Philips) or 'GRAPPA' (GE or Siemens), MR multi-coils receiver array reconstruction
                ncoils          int, number of coils of the receiver array (0 to disable correction factor)
                                     use N = 1 in case of a SENSE reconstruction (Philips)
                                     or the number of coils for a GRAPPA reconstruction (Siemens or GE).
                                     use N = 0 to disable the correction factor,
                                     as for example if the noise is Gaussian distributed.
                nphase          int, number of phase array coils
                                     if scanner does a SENSE reconstruction,
                                     always use N = 1, as the noise profile is always Rician.
                                     if scanner does a GRAPPA reconstruction, set N as the number of phase array coils.
            """
            if 'noisealgo' in denoise: noisealgo = denoise['noisealgo']
            else: noisealgo = _NOISE[0]
            if 'ncoils' in denoise: ncoils = denoise['ncoils']
            else: ncoils = 0
            if 'nphase' in denoise: nphase = denoise['nphase']
            else: nphase = 1
            if 'rec' in denoise:
                rec = denoise['rec']
                if denoise['rec'].lower() == 'sense':
                    ncoils = 1
                    nphase = 1
            else: rec = 'SENSE'
            sigma = dwiNoiseEstimation(vols, noisealgo, rec, ncoils, nphase, wait)
            if wait is not None: wait.setInformationText('Adaptive soft coefficient matching denoising...')
            """
                patch_radius    int, radius of the local patch to be taken around each voxel (default 1)
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
                block_radius    int, radius of the local patch to be taken around each voxel  (default 5)
                                     block size = block_radius x 2 + 1 (ex: 2 gives 5x5x5 blocks)
                rician      boolean, if True the noise is estimated as Rician, otherwise Gaussian noise is assumed
            """
            if wait is not None: wait.setInformationText('Stage 1/3 - non-local means, small patch...')
            img_small = non_local_means(imgs, sigma=sigma, mask=mask, patch_radius=1, block_radius=1, rician=True, wait=wait)
            if wait is not None: wait.setInformationText('Stage 2/3 - non-local means, large patch...')
            img_large = non_local_means(imgs, sigma=sigma, mask=mask, patch_radius=2, block_radius=1, rician=True, wait=wait)
            if wait is not None: wait.setInformationText('Stage 3/3 - adaptive soft coefficient matching...')
            imgs = adaptive_soft_matching(imgs, img_small, img_large, sigma=sigma[0])
    # Return preprocessed
    rvol = SisypheVolumeCollection()
    for i in range(vols.count()):
        v = SisypheVolume()
        data = imgs[:, :, :, i]
        v.copyFromNumpyArray(data,
                             spacing=vols[0].getSpacing(),
                             origin=vols[0].getOrigin(),
                             direction=vols[0].getDirections(),
                             defaultshape=False)
        v.copyAttributesFrom(vols[i], display=False)
        v.setFilename(vols[i].getFilename())
        v.setFilenamePrefix(prefix)
        v.setFilenameSuffix(suffix)
        if save:
            if wait is not None: wait.setInformationText('Save {}...'.format(v.getBasename()))
            v.save()
        rvol.append(v)
    # noinspection PyUnboundLocalVariable
    return rvol, rmask
