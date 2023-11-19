"""
    External packages/modules

        Name            Link                                                        Usage

        DIPY            https://www.dipy.org/                                       MR diffusion image processing
        Numpy           https://numpy.org/                                          Scientific computing
"""

from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext

from dipy.core.gradients import gradient_table
from dipy.core.gradients import GradientTable
from dipy.denoise.gibbs import gibbs_removal
from dipy.denoise.localpca import genpca
from dipy.denoise.localpca import localpca
from dipy.denoise.localpca import mppca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.patch2self import patch2self
from dipy.denoise.noise_estimate import piesno
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.pca_noise_estimate import pca_noise_estimate

from numpy import array
from numpy import ndarray

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheDicom import removeSuffixNumberFromFilename
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

        dwiNoiseEstimation()
        getLocalPCADict()
        getGeneralFunctionPCAParameterDict()
        getMarcenkoPasturPCAParameterDict()
        getNonLocalMeansParameterDict()
        getSelfSupervisedDenoisingParameterDict()
        getAdaptiveSoftCoefficientMatchingParameterDict()
        dwiPreprocessing()
        
    Creation: 08/11/2023
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
        vol             SisypheVolume | SisypheVolumeCollection, dwi volume(s)
        algo            str, 'Local patches' or 'Piesno', noise estimation algorithm
        rec             str, 'SENSE' (Philips) or 'GRAPPA' (GE or Siemens), MR multi-coils receiver array reconstruction
        n_coils         int, number of coils of the receiver array (0 to disable correction factor)
                             use N = 1 in case of a SENSE reconstruction (Philips)
                             or the number of coils for a GRAPPA reconstruction (Siemens or GE).
                             use N = 0 to disable the correction factor,
                             as for example if the noise is Gaussian distributed.
        n_phase_coils   int, number of phase array coils
                             if scanner does a SENSE reconstruction,
                             always use N = 1, as the noise profile is always Rician.
                             if scanner does a GRAPPA reconstruction, set N as the number of phase array coils.
        wait            DialogWait, optional progress dialog

        return          float, noise
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

def getLocalPCAParameterDict() -> dict[str]:
    return {'algo': 'Local PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getGeneralFunctionPCAParameterDict() -> dict[str]:
    return {'algo': 'General function PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getMarcenkoPasturPCAParameterDict() -> dict[str]:
    return {'algo': 'Marcenko-Pastur PCA', 'smooth': 2, 'radius': 2, 'method': 'eig'}

def getNonLocalMeansParameterDict() -> dict[str]:
    return {'algo': 'Non-local means', 'ncoils': 0, 'patchradius': 1, 'blockradius': 5}

def getSelfSupervisedDenoisingParameterDict() -> dict[str]:
    return {'algo': 'Self-Supervised Denoising', 'radius': 0, 'solver': 'ols'}

def getAdaptiveSoftCoefficientMatchingParameterDict() -> dict[str]:
    return {'algo': 'Adaptive soft coefficient matching', 'ncoils': 0}

def dwiPreprocessing(vols: SisypheVolumeCollection,
                     prefix: str = 'f',
                     suffix: str = '',
                     gtab: GradientTable | None = None,
                     brainseg: dict[str] | None = None,
                     gibbs: dict[str] | None = None,
                     denoise: dict[str] | None = None,
                     save: bool = False,
                     wait: DialogWait | None = None) -> tuple[SisypheVolumeCollection, SisypheROI | None]:
    """
        vols        SisypheVolumeCollection, dwi volumes
        prefix      str, prefix filename for filtered dwi volumes
        suffix      str, suffix filename for filtered dwi volumes
        gtab        GradientTable | None, required for PCA, Non-local means and Self-Supervised denoising algorithms
        brainseg    dict, {'algo': str = 'huang', 'size': int = 1, 'niter': int = 2}
        gibbs       dict, {'neighbour': int = 3}
        denoise     dict, {'algo': 'Local PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
                          {'algo': 'General function PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
                          {'algo': 'Marcenko-Pastur PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
                          {'algo': 'Non-local means', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int, 'patchradius': int = 1, 'blockradius': int = 5}
                          {'algo': 'Self-Supervised Denoising', 'radius': int = 0, 'solver': str = 'ols'}
                          {'algo': 'Adaptive soft coefficient matching', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int}
        save        bool, save if true
        wait        DialogWait, optional progress dialog

        return      SisypheVolumeCollection,  SisypheROI | None
    """
    mask = None
    img = vols.getNumpy(defaultshape=False)
    # Brain segmentation
    if brainseg is not None:
        if len(brainseg) == 0: brainseg = {'algo': 'huang', 'size':  1, 'niter': 2}
        if wait is not None: wait.setInformationText('Brain extraction...')
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
        mvol = SisypheVolume(img.mean(axis=3), spacing=vols[0].getSpacing())
        mask = mvol.getMask2(algo, niter, size).getNumpy(defaultshape=False)
    # Gibbs suppression
    if gibbs is not None:
        if len(gibbs) == 0: gibbs = {'neighbour': 3}
        if wait is not None: wait.setInformationText('Gibbs suppression...')
        """
            neighbour int, number of neighbour points to access local TV (default 3)
        """
        gibbs_removal(img, n_points=gibbs['neighbour'])
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
            sigma = pca_noise_estimate(img, gtab, smooth=smooth)
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
            img = localpca(img, sigma, mask, patch_radius=radius, pca_method=method, tau_factor=2.3)
        # General function PCA denoising
        elif denoise['algo'] == _DENOISE[1]:
            if 'smooth' in denoise: smooth = denoise['smooth']
            else: smooth = 2
            if wait is not None: wait.setInformationText('Noise estimation...')
            sigma = pca_noise_estimate(img, gtab, smooth=smooth)
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
            img = genpca(img, sigma, mask, patch_radius=radius, pca_method=method, tau_factor=2.3)
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
            img = mppca(img, mask, patch_radius=radius, pca_method=method)
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
                if denoise['rec'].lower() == 'sense':
                    ncoils = 1
                    nphase = 1
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
            img = nlmeans(img, sigma, mask, patch_radius=patchradius, block_radius=blockradius, rician=True)
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
            img = patch2self(img, gtab.bvals, model=method, patch_radius=patchradius)
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
                if denoise['rec'].lower() == 'sense':
                    ncoils = 1
                    nphase = 1
            sigma = dwiNoiseEstimation(vols, noisealgo, rec, ncoils, nphase, wait)
            if wait is not None: wait.setInformationText('Adaptive soft coefficient matching denoising...')
            """
                patch_radius    int, radius of the local patch to be taken around each voxel (default 1)
                                     patch size = patch_radius x 2 + 1 (ex: 2 gives 5x5x5 patches)
                block_radius    int, radius of the local patch to be taken around each voxel  (default 5)
                                     block size = block_radius x 2 + 1 (ex: 2 gives 5x5x5 blocks)
                rician      boolean, if True the noise is estimated as Rician, otherwise Gaussian noise is assumed
            """
            img_small = non_local_means(img, sigma, mask, patch_radius=1, block_radius=1, rician=True)
            img_large = non_local_means(img, sigma, mask, patch_radius=2, block_radius=1, rician=True)
            img = adaptive_soft_matching(img, img_small, img_large, sigma[0])
    # Return preprocessed
    rvol = SisypheVolumeCollection()
    for i in range(vols.count()):
        v = SisypheVolume()
        v.copyPropertiesFrom(vols[i])
        data = img[:, :, :, i]
        v.copyFromNumpyArray(data,
                             spacing=vols[i].getSpacing(),
                             origin=vols[i].getOrigin(),
                             direction=vols[i].getDirections(),
                             defaultshape=False)
        v.setFilename(vols[i].getFilename())
        v.setFilenamePrefix(prefix)
        v.setFilenameSuffix(suffix)
        if save:
            if wait is not None: wait.setInformationText('Save {}...'.format(v.getBasename()))
            v.save()
        rvol.append(v)
    if mask is not None:
        rmask = SisypheROI()
        rmask.copyFromNumpyArray(mask,
                                 spacing=vols[0].getSpacing(),
                                 origin=vols[0].getOrigin(),
                                 direction=vols[0].getDirections(),
                                 defaultshape=False)
        mask = rmask
        filename = removeSuffixNumberFromFilename(rvol[0].getFilename())
        filename.replace(SisypheVolume.getFileExt(), SisypheROI.getFileExt())
        filename = join(dirname(filename), 'mask_' + basename(filename))
        mask.setName('dwi brain mask')
        mask.setFilename(filename)
        if save:
            if wait is not None: wait.setInformationText('Save {}...'.format(basename(mask.getFilename())))
            mask.save()
    return rvol, mask
