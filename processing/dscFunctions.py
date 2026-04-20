"""
External packages/modules
-------------------------

    - Cython, static compiler, https://cython.org/
    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SciPy, Scientific computing, https://scipy.org/
"""

import cython

from datetime import datetime

from math import sqrt

from numpy import e
from numpy import abs
from numpy import log
from numpy import exp
from numpy import zeros
from numpy import sort
from numpy import mean
from numpy import max
from numpy import array
from numpy import arange
from numpy import argmin
from numpy import argmax
from numpy import argsort
from numpy import where
from numpy import shape
from numpy import sum
from numpy import transpose
from numpy import power
from numpy import amax
from numpy import multiply
from numpy import divide
from numpy import trapz
from numpy import convolve
from numpy import unravel_index
from numpy import nan_to_num
from numpy import ndarray
from numpy import float64
from numpy import maximum
from numpy import zeros_like
from numpy import stack
from numpy import pad
from numpy import vstack
from numpy import hstack
from numpy import diff
from numpy import diag
from numpy import einsum
from numpy import concatenate
from numpy import cumsum
from numpy.linalg import svd

from typing import Union

from scipy.special import gamma
from scipy.linalg import svd
from scipy.linalg import toeplitz
from scipy.optimize import minimize
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.gui.dialogWait import DialogWait

from PyQt5.QtWidgets import QApplication

__all__ = ['getArterialInputVoxels',
           'gammaVariate',
           'gammaVariateFitting',
           'signalToContrastConcentration',
           'deconvolveContrastConcentration',
           'signalRecoveryMaps',
           'dscMaps',
           'gamma_variate',
           'fit_gamma_variate',
           'generate_ttp',
           'generate_leakage',
           'generate_perfusion_maps',
           'oSVD',
           'boxNLR',
           'fit_boxNLR',
           'dscMaps2',
           'cbfASLMap']

"""
functions
~~~~~~~~~

    - getArterialInputVoxels
    - gammaVariate
    - gammaVariateFitting
    - signalToContrastConcentration
    - leakageCorrection
    - deconvolveContrastConcentration
    - signalRecoveryMaps
    - dscMaps
"""


def getArterialInputVoxels(vols: list[SisypheVolume] | SisypheVolumeCollection | SisypheVolume,
                           mask: SisypheVolume | None = None,
                           n: int = 100) -> tuple[SisypheVolume, list[float]]:
    """
    Extracts voxels used to process arterial input function from the time series of perfusion-weighted images.
    Arterial voxels have high range and low argmin (early negative peak, before tissue and veins)

    - (1) negative peak height of each voxel (i.e. time series range of each voxel)
    - (2) relative time to peak delay: mean time to peak tissue - time to peak of each voxel (arteries have positive
    values, veins have negative values)
    - thresholding parameter = (1) * (2)

    Parameters
    ----------
        vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection | Sisyphe.core.sisypheVolume.SisypheVolume
            time series of perfusion weighted images
        mask : SisypheVolume | None
            voxels used for aif processing. A mask is automatically computed if there is none (default).
        n : int
            max number of extracted voxels (default 100, minimum 10)

    Returns
    -------
        tuple[SisypheVolume, list[float]]
            - SisypheVolume: aif voxels, each voxel is labeled according to its sorting rank
            - list[float]: mean curve
    """
    if isinstance(vols, list):
        v = SisypheVolumeCollection()
        v.copyFromList(vols)
        vols = v
    if isinstance(vols, SisypheVolumeCollection):
        vols = vols.copyToMultiComponentSisypheVolume()
    if isinstance(vols, SisypheVolume):
        if vols.getNumberOfComponentsPerPixel() > 1:
            if mask is None: mask = vols.getMask()
            mcurve = vols.getMean(mask, c=None)
            mmin = argmin(mcurve)
            vargmin = vols.getComponentArgmin()
            mask = mask.cast('float32')
            # noinspection PyTypeChecker
            mask2 = (vargmin > (mmin // 2)).cast('float32')
            # noinspection PyTypeChecker
            vargmin = (mmin - vargmin).cast('float32')
            vrange = vols.getComponentMean(slice(3)).cast('float32') - vols.getComponentMin().cast('float32')
            vparam = vrange * vargmin * mask * mask2
            if n < 10: n = 10
            # Select voxels according to vparam
            threshold = sort(vparam.getNumpy().flatten())[-n]
            vrange = vrange * (vparam >= threshold).cast('float32')
            # Sort aif voxels according to vrange
            # Each voxel is labeled according to its sorting rank.
            vrange2 = vrange.getNumpy()
            idx = unravel_index(argsort(vrange2, axis=None)[::-1], shape=vrange2.shape)
            aifv = zeros(vrange2.shape)
            aifv[idx[0][0:n], idx[1][0:n], idx[2][0:n]] = range(1, n + 1)
            r = SisypheVolume()
            r.copyFromNumpyArray(aifv, spacing=vols.getSpacing())
            r.copyAttributesFrom(vols)
            return r, mcurve
        else: raise AttributeError('Parameter is not a multi-component image.')
    else: raise TypeError('Parameter type {} is not supported'.format(type(vols)))


def gammaVariate(params: ndarray, t: ndarray) -> ndarray:
    """
    Gamma-variate function.

    Gamma variate(t) = k (t - t0) ** a * exp(- (t - t0) / b)
    - t0, bolus arrival time
    - k, scale factor (> 0.0)
    - a and b, arbitrary parameters (>= 1.0)

    Parameters
    ----------
    params : numpy.ndarray
        gamma variate parameters
        - params[0], t0 bolus appearance time
        - params[1], c0 constant scale factor
        - params[2], arbitrary parameter alpha
        - params[3], arbitrary parameter beta
    t : numpy.ndarray
        time points

    Returns
    -------
    numpy.ndarray
        gamma variate contrast concentration time series
    """
    # noinspection PyTypeChecker
    t0: float = params[0]
    # noinspection PyTypeChecker
    c0: float = params[1]
    # noinspection PyTypeChecker
    alpha: float = params[2]
    # noinspection PyTypeChecker
    beta: float = params[3]
    tr = t - t0
    tr = where(tr > 0.0, tr, 0.0)
    y = c0 * (tr ** alpha) * exp((-tr) / beta)
    return y


def gammaVariateFitting(cc: ndarray,
                        leakage: bool = False,
                        optim: str = 'L-BFGS-B') -> dict[str, Union[ndarray, tuple, float]] | None:
    """
    Fitting a gamma-variate function to a voxel contrast concentration time series.

    Gamma variate(t) = k (t - t0) ** a * exp(- (t - t0) / b)

    Optimized parameters:
    - t0, bolus arrival time
    - k, scale factor (> 0.0)
    - a and b, arbitrary parameters (>= 1.0)

    Gamma variate analytical solutions:
    - integral = k * (b ** (a + 1)) * gamma(a + 1)
    - mean transit time = t0 + b * (a + 1)
    - peak time = t0 + (a * b)
    - peak concentration = k ((a * b) / e) ** a

    Reference:
    H.K. Thompson Jr, C.F. Starmer, R.E. Whalen, H.D. Mcintosh.  Indicator Transit Time Considered as a Gamma Variate.
    Circ Res 1964 Jun;14:502-15.

    Parameters
    ----------
    cc : numpy.ndarray
        voxel contrast concentration time series
    leakage : bool
        return residue integral
    optim : str
        optimization method: 'Nelder-Mead', 'Powell', 'L-BFGS-B' (default), 'SLSQP'

    Returns
    -------
    dict[str, numpy.ndarray | tuple | float] | None
        dict keys: values or None if optimization failure
        - 'cc': ndarray, gamma variate fitted contrast concentration
        - 'ccintgrl': float, gamma variate integral
        - 'rintgrl': float, residue integral (leakage)
        - 'ttp': float, gamma variate index of peak
        - 'mtt': float, gamma variate mean transit time
        - 'cp': float, gamma variate peak concentration
        - 'params': tuple[float, ...], bolus arrival time, scale factor, alpha and beta arbitrary parameters
    """

    def func(params: ndarray,
             inputs: list[ndarray]) -> float:
        """
        Gamma variate loss function to optimize.
        Mean square of gamma variate fitting residuals.

        Parameters
        ----------
        params : numpy.ndarray
            gamma variate parameters
            - params[0], t0 bolus appearance time
            - params[1], c0 constant scale factor
            - params[2], alpha arbitrary parameter
            - params[3], beta arbitrary parameter
        inputs : list[ndarray, ndarray]
            - inputs[0], time series indices
            - inputs[1], voxel contrast concentration time series

        Returns
        -------
        float
            mean square of residuals
        """
        # noinspection PyTypeChecker
        t0: float = params[0]
        # noinspection PyTypeChecker
        c0: float = params[1]
        # noinspection PyTypeChecker
        alpha: float = params[2]
        # noinspection PyTypeChecker
        beta: float = params[3]
        t = inputs[0]
        y = inputs[1]
        # Gamma variate function
        tr = t - t0
        tr = where(tr > 0.0, tr, 0.0)
        ye = c0 * (tr ** alpha) * exp((-tr) / beta)
        # Mean square of residuals
        v = (abs(ye - y) ** 2).mean()
        return v

    # noinspection PyUnresolvedReferences
    n: cython.int = cc.shape[0]
    x = arange(n)
    peak = argmax(cc)
    # noinspection PyTypeChecker
    p0 = array([peak / 2, 1.0, 1.0, 1.0])
    # noinspection PyTypeChecker
    bnd = ((peak / 2, peak), (0.0, None), (1.0, 100.0), (1.0, 100.0))
    # noinspection PyTypeChecker
    optim = minimize(func, p0,
                     args=[x, cc],
                     method=optim,
                     bounds=bnd,
                     tol=1e-6)
    if optim.success:
        r = dict()
        x0: float = optim.x[0]
        k: float = optim.x[1]
        a: float = optim.x[2]
        b: float = optim.x[3]
        r['cc'] = gammaVariate(optim.x, x)
        r['ccintgrl'] = k * (b ** (a + 1)) * gamma(a + 1)
        r['ttp'] = x0 + (a * b)
        r['mtt'] = x0 + b * (a + 1)
        r['cp'] = k * ((a * b) / e) ** a
        r['params'] = optim.x
        if leakage: r['rintgrl'] = trapz(cc - r['cc'])
        else: r['rintgrl'] = 0.0
    else: r = None
    return r


def signalToContrastConcentration(vols: SisypheVolume,
                                  mask: SisypheVolume,
                                  te: float,
                                  baseline: tuple[int, int] = (0, 4)) -> SisypheVolume:
    """
    Signal to contrast concentration (∆R2*).
    ∆R2*(t) = -1/te log(s(t) / s(0))

    Parameters
    ----------
    vols : Sisyphe.core.sisypheVolume.SisypheVolume
        time series of perfusion weighted images
    mask : Sisyphe.core.sisypheVolume.SisypheVolume
        brain mask
    te : float
        echo time (TE) in s
    baseline : tuple[int, int]
        range (start, end) of volume indices used as baseline signal
        (default first 4 volumes, start=0, end=4)

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        ∆R2* contrast concentration maps
    """
    s0 = vols.getComponentMean(slice(baseline[0], baseline[1], 1)).getNumpy(defaultshape=False)
    st = vols.getNumpy(defaultshape=False).astype(s0.dtype)
    m = mask.getNumpy(defaultshape=False).astype(s0.dtype)
    # noinspection PyUnresolvedReferences
    i: cython.int
    for i in range(st.shape[3]):
        st[:, :, :, i] = (-1/te) * (log(st[:, :, :, i] / s0)) * m
    st = where(st <= 0.0, 0.0, st)
    st = nan_to_num(st, nan=0.0, posinf=0.0, neginf=0.0)
    r = SisypheVolume()
    r.copyFromNumpyArray(st, spacing=vols.getSpacing(), defaultshape=False)
    r.copyAttributesFrom(vols)
    return r


def deconvolveContrastConcentration(aif: ndarray, cc: ndarray, tr: float) -> ndarray:
    """
    Deconvolution of voxel contrast concentration time series with arterial input function.

    Contrast concentration deconvolution is an ill-posed problem, which requires some form of regularization in order
    to extract a physically acceptable solution. Deconvolution algorithm is based on truncated singular value
    decomposition with L-curve criterion (LCC) regularization.

    Reference:
    S. Sourbron, M. Dujardin, S. Makkat and R. Luypaert. Pixel-by-pixel deconvolution of bolus-tracking data:
    optimization and implementation. Phys Med Biol 2007 Jan 21;52(2):429-47.

    Parameters
    ----------
    aif : numpy.ndarray
        arterial input function (as signal, not contrast concentration)
    cc : numpy.ndarray
        voxel contrast concentration time series
    tr : float
        repetition time (TR) in s

    Returns
    -------
    numpy.ndarray
        impulse response function
    """
    # Discretize AIF
    # noinspection PyUnresolvedReferences
    nt: cython.int = shape(cc)[0]
    amtx = zeros([nt, nt])
    # noinspection PyUnresolvedReferences
    i: cython.int
    # noinspection PyUnresolvedReferences
    j: cython.int
    for i in range(nt):
        for j in range(nt):
            if j == 0 and i != 0: amtx[i, j] = (2 * aif[i] + aif[i - 1]) / 6.0
            elif i == j: amtx[i, j] = (2 * aif[0] + aif[1]) / 6.0
            elif 0 < j < i:
                amtx[i, j] = ((2 * aif[i - j] + aif[i - j - 1]) / 6.0) + \
                             ((2 * aif[i - j] + aif[i - j + 1]) / 6.0)
            else: amtx[i, j] = 0.0
    # SVD without regularization
    amtx = tr * amtx
    B0 = cc
    U, S, V = svd(amtx)
    # S_d = diag(S)
    B = transpose(U) @ B0
    # L-curve regularization
    # noinspection PyUnresolvedReferences
    umax: cython.double = 10.0
    # noinspection PyUnresolvedReferences
    umin: cython.double = 10e-10
    # noinspection PyUnresolvedReferences
    nu: cython.int = 400
    k = arange(nu)
    # noinspection PyTypeChecker
    u = amax(S) * umin * power((umax / umin), ((k - 1) / (nu - 1)))
    l0 = zeros([nu, amtx[:, 0].size])
    l1 = zeros([nu, amtx[:, 0].size])
    l2 = zeros([nu, amtx[:, 0].size])
    L = zeros([nu, amtx[:, 0].size, 3])
    # noinspection PyUnresolvedReferences
    x: cython.int
    # noinspection PyUnresolvedReferences
    y: cython.int
    for x in range(nu):
        for y in range(amtx[:, 0].size):
            l0[x, y] = power((power(u[x], 2) / (power(S[y], 2) + power(u[x], 2))), 2)
            l1[x, y] = power((S[y] / (power(S[y], 2) + power(u[x], 2))), 2)
            l2[x, y] = ((-4) * u[x] * power(S[y], 2)) / power((power(S[y], 2) + power(u[x], 2)), 3)
    L[:, :, 0] = l0
    L[:, :, 1] = l1
    L[:, :, 2] = l2
    # Optimize
    k = (nu - 1) - 1
    m = zeros([nu, 3])
    product = zeros(amtx[:, 0].size)
    lcurve = zeros(nu)
    # noinspection PyUnresolvedReferences
    x: cython.int
    for x in range(amtx[:, 0].size):
        Ui = U[:, x]
        product[x] = power((transpose(Ui) @ B), 2)
    # noinspection PyUnresolvedReferences
    x: cython.int
    for x in range(3):
        ltmp = L[:, :, x]
        # noinspection PyTypeChecker
        m[:, x] = sum(ltmp, axis=1) * sum(product)
    # noinspection PyUnresolvedReferences
    x: cython.int
    for x in range(nu):
        lcurve[x] = 2 * (m[x, 1] * m[x, 0] / m[x, 2]) * \
                    ((power(u[x], 2) * m[x, 2] * m[x, 0] + 2 * u[x] * m[x, 1] * m[x, 0] +
                      power(u[x], 4) * m[x, 1] * m[x, 2]) /
                     power((power(u[x], 4) * power(m[x, 1], 2) + power(m[x, 0], 2)), (3 / 2)))
    # noinspection PyUnresolvedReferences
    Lm1: cython.double = lcurve[k - 2]
    # noinspection PyUnresolvedReferences
    L0: cython.double = lcurve[k - 1]
    # noinspection PyUnresolvedReferences
    L1: cython.double = lcurve[k]
    # noinspection PyUnresolvedReferences
    mu: cython.double = u[k - 1]
    while L0 >= Lm1 or L0 >= L1:
        k -= 1
        L1 = L0
        L0 = Lm1
        Lm1 = lcurve[k - 1]
        mu = u[k - 1]
    Bpi = multiply(B, divide(S, (power(S, 2) + power(mu, 2))))
    Rf = transpose(V) @ Bpi
    # return Rf, mu, B, S
    return Rf


def signalRecoveryMaps(vols: SisypheVolume,
                       mask: SisypheVolume,
                       t0: float, tr: float,
                       baseline: tuple[int, int] = (0, 4),
                       wait: DialogWait | None = None) -> dict[str, SisypheVolume]:
    """
    Signal recovery (SR) and percentage signal recovery (PSR) maps processing.

    SR is defined as the difference between the signal intensity immediately after the first pass (Spost) of the
    contrast agent (in humans usually 60 s after bolus arrival) and the pre-contrast (Spre) signal intensity, while
    PSR is given by the difference of Spost to the minimum of the signal intensity-curve (Smin) divided by the
    difference between pre-contrast (Spre) and minimum (Smin) signal intensity.

    SR = (Spost - Spre) / (Spre * 100)
    PSR = (Spost - Smin) / ((Spre - Smin) * 100)

    Reference:
    M. Huhndorf, A. Moussavil, N. Kramann, O. Will, K. Hattermann, C. Stadelmann, O. Jansen, S. Boretius.
    Alterations of the Blood-Brain Barrier and Regional Perfusion in Tumor Development: MRI Insights from a Rat C6
    Glioma Model.  PLoS One 2016 Dec 22;11(12)

    Parameters
    ----------
    vols : Sisyphe.core.sisypheVolume.SisypheVolume
        time series of perfusion weighted images
    mask : Sisyphe.core.sisypheVolume.SisypheVolume
        brain mask
    t0 : float
        bolus arrival time index
    tr : float
        repetition time (TR) in s
    baseline : tuple[int, int]
        range (start, end) of volume indices used as baseline signal
        (default first 4 volumes, start=0, end=4)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    dict[str, SisypheVolume]
        SR and PSR maps
    """
    if wait is not None:
        wait.setInformationText('Recovery maps processing...')
        wait.setProgressVisibility(False)
        wait.buttonVisibilityOff()
    n = baseline[1] - baseline[0] + 1
    tpost = int(t0 + (60.0 / tr))
    if tpost + n > vols.getNumberOfComponentsPerPixel():
        # < Revision 13/06/2025
        # tpost = vols.getNumberOfComponentsPerPixel() - n
        tpost = vols.getNumberOfComponentsPerPixel() - n
        # Revision 13/06/2025 >
    vpre = vols.getComponentMean(slice(baseline[0], baseline[1], 1))
    vpre2 = vpre.getNumpy(defaultshape=False)
    vpost = vols.getComponentMean(slice(tpost, tpost + n, 1))
    vpost2 = vpost.getNumpy(defaultshape=False)
    vmin = vols.getComponentMin()
    vmin2 = vmin.getNumpy(defaultshape=False)
    m = mask.getNumpy(defaultshape=False)
    r = dict()
    # signal recovery map (SR)
    sr = ((vpost2 - vpre2) / vpre2) * 100.0 * m
    sr = nan_to_num(sr, nan=0.0, posinf=0.0, neginf=0.0)
    r['sr'] = SisypheVolume()
    r['sr'].copyFromNumpyArray(sr,
                               spacing=vols.getSpacing(),
                               origin=vols.getOrigin(),
                               direction=vols.getDirections(),
                               defaultshape=False)
    r['sr'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
    r['sr'].acquisition.setModalityToOT()
    r['sr'].acquisition.setSequence('SR')
    r['sr'].acquisition.setUnitToRatio()
    r['sr'].display.getLUT().setLut('inserm')
    r['sr'].setFilename(vols.getFilename())
    r['sr'].setFilenameSuffix('sr')
    # percentage signal recovery map (PSR)
    psr = ((vpost2 - vmin2) / (vpre2 - vmin2)) * 100.0 * m
    psr = nan_to_num(psr, nan=0.0, posinf=0.0, neginf=0.0)
    r['psr'] = SisypheVolume()
    r['psr'].copyFromNumpyArray(psr,
                                spacing=vols.getSpacing(),
                                origin=vols.getOrigin(),
                                direction=vols.getDirections(),
                                defaultshape=False)
    r['psr'].replaceNanInfValues()
    r['psr'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
    r['psr'].acquisition.setModalityToOT()
    r['psr'].acquisition.setSequence('PSR')
    r['psr'].acquisition.setUnitToRatio()
    r['psr'].display.getLUT().setLut('inserm')
    r['psr'].setFilename(vols.getFilename())
    r['psr'].setFilenameSuffix('psr')
    return r


def dscMaps(vols: SisypheVolume,
            mask: SisypheVolume,
            aif: ndarray,
            tr: float, te: float,
            baseline: tuple[int, int] = (0, 4),
            smooth: bool = False,
            recovery: bool = True,
            dsc: bool = True,
            fit: bool = True,
            deconvolve: bool = True,
            leakage: bool = True,
            wait: DialogWait | None = None) -> dict[str, SisypheVolume]:
    """
    Dynamic susceptibility contrast MR perfusion maps processing:
    - cerebral blood flow (CBF), in ml / min / 100g
    - cerebral blood volume (CBV), in ml / 100g
    - mean transit time (MTT), in s
    - leakage volume (LKV), in ml / 100g
    - time to pic (TTP), in s
    - signal recovery (SR)
    - percentage signal recovery (PSR)
    
    Parameters
    ----------
    vols : Sisyphe.core.sisypheVolume.SisypheVolume
        time series of perfusion weighted images
    mask : Sisyphe.core.sisypheVolume.SisypheVolume
        brain mask
    aif : ndarray
        arterial input function (as signal, not contrast concentration)
    tr : float
        repetition time (TR) in s
    te : float
        echo time (TE) in s
    baseline : tuple[int, int]
        range (start, end) of volume indices used as baseline signal
        (default first 4 volumes, start=0, end=4)
    smooth : bool
        contrast concentration time series smoothing if true (default False)
    recovery : bool
        Signal recovery maps processing if True
    dsc : bool
        DSC maps processing if True
    fit : bool
        Gamma variate fitting of contrast concentration time series if True (default). In this case, integration is
        performed using the analytical solution of the gamma variate function. Otherwise, a numerical integration is
        performed using the composite trapezoidal rule.
    deconvolve : bool
        CBF and CBV are processed using a deconvolution algorithm (default True). If False, fast approximations of
        CBF and MTT are calculated directly from the contrast concentration time series.
    leakage : bool
        Leakage correction of contrast concentration maps if True (default)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    dict[str, SisypheVolume]
        perfusion maps, dict keys: 'cbf', 'cbv', 'mtt', 'lkv', 'ttp', 'tmax', 'sr', 'psr'
    """
    r: dict[str, SisypheVolume] = dict()
    # signal to contrast concentration
    if wait is not None:
        wait.setInformationText('Signal to concentration processing...')
    cc_vols = signalToContrastConcentration(vols, mask, te, baseline)
    cc_vols.setFilename(vols.getFilename())
    cc_vols.setFilenameSuffix('cc')
    cc_vols.save()
    # arterial input function processing
    if wait is not None:
        wait.setInformationText('Arterial input function processing...')
    s0 = mean(aif[baseline[0]:baseline[1]])
    aif = (-1/te) * (log(aif / s0))
    aif = where(aif <= 0.0, 0.0, aif)
    p = gammaVariateFitting(aif)
    aif = p['cc']
    aif_intgrl = p['ccintgrl']
    """
    Constant krho needed to obtain absolute measurements:
    
    - tissue-to-artery concentration scale factor ratio = 0.1369
    - x 1 / brain density rho, rho = 0.104 g / ml, rho = 0.0104 100 g / ml
    - x (1 - Ha) / (1 - Ht) = 0.55 / 0.75 = 0.73
    - hematocrit in large arterial Ha = 0.45, plasma in large arterial (1 - Ha) = 0.55
    - hematocrit in the tissue capillary bed Ht = 0.25, plasma in tissue capillary bed (1 - Ht) = 0.75
    - x 60, s to min conversion
    
    DSC in ml / min / 100 g
    CBV, LKV in ml / 100 g
    MTT, TTP, TTB in s
    SR, PSR no unit, ratio
    """
    # krho: cython.double = (((0.55 / 0.75) * 0.1369) / 0.0104)
    if recovery:
        # SR/PSR maps processing
        t0 = where(aif.cumsum() == 0.0)[0]
        if len(t0) > 0: t0 = t0[-1]
        else: t0 = 0
        v = signalRecoveryMaps(vols, mask, t0, tr, baseline, wait)
        r['sr'] = v['sr']
        r['psr'] = v['psr']
    if dsc:
        # DSC maps processing
        cc = cc_vols.getNumpy(defaultshape=False)
        # noinspection PyUnresolvedReferences
        i: cython.int
        # noinspection PyUnresolvedReferences
        j: cython.int
        # noinspection PyUnresolvedReferences
        k: cython.int
        cbf = zeros(shape=cc.shape[:3])
        cbv = zeros(shape=cc.shape[:3])
        mtt = zeros(shape=cc.shape[:3])
        ttp = zeros(shape=cc.shape[:3])
        lkv = zeros(shape=cc.shape[:3])
        if wait is not None:
            wait.setInformationText('DSC maps processing...')
            wait.setProgressVisibility(True)
            wait.setProgressRange(0, cc.shape[2])
            wait.buttonVisibilityOn()
        t = datetime.now()
        for k in range(cc.shape[2]):
            if wait is not None: wait.setCurrentProgressValue(k)
            if k > 0:
                now = datetime.now()
                delta = now - t
                t = now
                delta *= cc.shape[2] - k
                m = delta.seconds // 60
                s = delta.seconds - (m * 60)
                if m == 0:
                    wait.setInformationText('DSC maps processing...\n'
                                            'Estimated time remaining {} s.'.format(s))
                else:
                    wait.setInformationText('DSC maps processing...\n'
                                            'Estimated time remaining {} min {} s.'.format(m, s))
            for j in range(cc.shape[1]):
                for i in range(cc.shape[0]):
                    QApplication.processEvents()
                    if wait is not None and wait.getStopped(): return r
                    if mask[i, j, k] > 0:
                        if smooth:
                            cc[i, j, k, :] = convolve(cc[i, j, k, :], [0.25, 0.5, 0.25])
                        if fit:
                            p = gammaVariateFitting(cc[i, j, k, :], leakage=leakage)
                            if p is not None:
                                ccc = p['cc']
                                # cerebral blood volume in ml / 100 g (* 100, g to 100 g)
                                cbv[i, j, k] = (p['ccintgrl'] / aif_intgrl) * 100.0
                                if cbv[i, j, k] > 100.0: cbv[i, j, k] = 100.0
                                # mean transit time in s (* tr, index to s)
                                mtt[i, j, k] = p['mtt'] * tr
                                # time to pic in s (* tr, index to s)
                                ttp[i, j, k] = p['ttp'] * tr
                                if leakage:
                                    # leakage in ml / 100 g (* 100, g to 100 g)
                                    lkv[i, j, k] = (p['rintgrl'] / aif_intgrl) * 100.0
                            else: continue
                        else: ccc = cc[i, j, k, :]
                        if deconvolve:
                            rf = deconvolveContrastConcentration(aif, ccc, tr)
                            # cerebral blood flow in ml / min / 100 g (* 100, g to 100 g)
                            cbf[i, j, k] = max(rf) * 100.0 * (60.0 / tr)
                            # cerebral blood volume in ml / 100 g (* 100, g to 100 g)
                            if cbv[i, j, k] == 0.0: cbv[i, j, k] = trapz(rf) * 100
                            # mean transit time in s (* 60, min to s)
                            mtt[i, j, k] = (cbv[i, j, k] / cbf[i, j, k]) * 60.0
                        else:
                            if cbv[i, j, k] == 0.0:
                                # cerebral blood flow in ml / min / 100 g (* 100, g to 100 g)
                                cbv[i, j, k] = (trapz(ccc) / aif_intgrl) * 100.0
                                if cbv[i, j, k] > 100.0: cbv[i, j, k] = 100.0
                            if mtt[i, j, k] != 0.0:
                                # cerebral blood flow in ml / min / 100 g, * 60 (s to min)
                                cbf[i, j, k] = (cbv[i, j, k] / mtt[i, j, k]) * 60.0
                        if ttp[i, j, k] == 0.0:
                            # noinspection PyTypeChecker
                            ttp[i, j, k] = ccc.argmax() * tr
        wait.setCurrentProgressValue(cc.shape[2])
        cbv = nan_to_num(cbv, nan=0.0, posinf=0.0, neginf=0.0)
        cbf = nan_to_num(cbf, nan=0.0, posinf=0.0, neginf=0.0)
        mtt = nan_to_num(mtt, nan=0.0, posinf=0.0, neginf=0.0)
        ttp = nan_to_num(ttp, nan=0.0, posinf=0.0, neginf=0.0)
        wmax = cc.shape[3] * tr
        mtt = (mtt <= wmax) * mtt
        ttp = (ttp <= wmax) * ttp
        # CBV, Cerebral Blood Volume
        r['cbv'] = SisypheVolume()
        r['cbv'].copyFromNumpyArray(cbv,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=False)
        r['cbv'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['cbv'].acquisition.setSequenceToCerebralBloodVolumeMap()
        if deconvolve: r['cbv'].acquisition.setUnit('ml / 100g')
        else: r['cbv'].acquisition.setNoUnit()
        r['cbv'].display.getLUT().setLut('inserm')
        r['cbv'].setFilename(vols.getFilename())
        r['cbv'].setFilenameSuffix('cbv')
        # TTP, Time To Pic
        r['ttp'] = SisypheVolume()
        r['ttp'].copyFromNumpyArray(ttp,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=False)
        r['ttp'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['ttp'].acquisition.setSequenceToTimeToPicMap()
        r['ttp'].acquisition.setUnit('s')
        r['ttp'].display.getLUT().setLut('inserm')
        r['ttp'].setFilename(vols.getFilename())
        r['ttp'].setFilenameSuffix('ttp')
        if fit or deconvolve:
            # CBF, Cerebral Blood Flow
            r['cbf'] = SisypheVolume()
            r['cbf'].copyFromNumpyArray(cbf,
                                        spacing=mask.getSpacing(),
                                        origin=vols.getOrigin(),
                                        direction=vols.getDirections(),
                                        defaultshape=False)
            r['cbf'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
            r['cbf'].acquisition.setSequenceToCerebralBloodFlowMap()
            if deconvolve: r['cbf'].acquisition.setUnit('ml / min / 100g')
            else: r['cbf'].acquisition.setNoUnit()
            r['cbf'].display.getLUT().setLut('inserm')
            r['cbf'].setFilename(vols.getFilename())
            r['cbf'].setFilenameSuffix('cbf')
            # MTT, Mean Transit Time
            r['mtt'] = SisypheVolume()
            r['mtt'].copyFromNumpyArray(mtt,
                                        spacing=mask.getSpacing(),
                                        origin=vols.getOrigin(),
                                        direction=vols.getDirections(),
                                        defaultshape=False)
            r['mtt'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
            r['mtt'].acquisition.setSequenceToMeanTransitTimeMap()
            r['mtt'].acquisition.setUnit('s')
            r['mtt'].display.getLUT().setLut('inserm')
            r['mtt'].setFilename(vols.getFilename())
            r['mtt'].setFilenameSuffix('mtt')
        # LKV, LeaKage Volume
        if leakage:
            if fit:
                lkv = nan_to_num(lkv, nan=0.0, posinf=0.0, neginf=0.0)
                r['lkv'] = SisypheVolume()
                r['lkv'].copyFromNumpyArray(lkv,
                                            spacing=mask.getSpacing(),
                                            origin=vols.getOrigin(),
                                            direction=vols.getDirections(),
                                            defaultshape=False)
            r['lkv'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
            r['lkv'].acquisition.setModalityToOT()
            r['lkv'].acquisition.setSequence('LKV')
            if deconvolve: r['lkv'].acquisition.setUnit('ml / 100g')
            else: r['lkv'].acquisition.setNoUnit()
            r['lkv'].display.getLUT().setLut('inserm')
            r['lkv'].setFilename(vols.getFilename())
            r['lkv'].setFilenameSuffix('lkv')
    return r


"""
Dynamic susceptibility contrast
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

functions
~~~~~~~~~

    - gamma_variate
    - fit_gamma_variate
    - generate_ttp
    - generate_leakage
    - generate_perfusion_maps
    - oSVD
    - boxNLR
    - fit_boxNLR
    - dscMaps2

The code was adapted from the PyPeT Python Perfusion Tool.
https://github.com/Marijn311/CT-and-MR-Perfusion-Tool

reference: PyPeT: A Python Perfusion Tool for Automated Quantitative Brain CT and MR Perfusion Analysis. Borghouts M. 
& Su R. arXiv:2511.13310v1 [eess.IV] 17 Nov 2025.
"""


def gamma_variate(t: ndarray | list[float],
                  t0: float,
                  alpha: float,
                  beta: float,
                  k: float = 1.0) -> ndarray:
    """
    Gamma variate function for modeling arterial input function.
    Standard gamma variate: k * (t-t0)^alpha * exp(-(t-t0)/beta) for t > t0

    Parameters
    ----------
    t : ndarray
        1D time array, same length as the contrast curve. Contains a time value for each time point.
    t0 : float
        time delay/onset time.
    alpha : float
        shape parameter.
    beta : float
        time constant.
    k : float
        peak amplitude scaling factor.

    Returns
    -------
        ndarray
            1D array of modeled arterial input function
    """
    t = array(t)
    t_shifted = maximum(0, t - t0)
    r = zeros_like(t_shifted)
    mask = t > t0
    r[mask] = k * (t_shifted[mask] ** alpha) * exp(-t_shifted[mask] / beta)
    return r


def fit_gamma_variate(time_index: ndarray,
                      curve: ndarray,
                      sigma: ndarray | None = None) -> ndarray:
    """
    Fit a gamma variate function to the given contrast curve using non-linear least squares optimization.

    Parameters
    ----------
    time_index : ndarray
        1D array of time points corresponding to the contrast curve.
    curve : ndarray
        1D array of contrast values to fit the gamma variate to.
    sigma : ndarray | None (optional)
        1D array of standard deviations for each point in the curve, used as weights in fitting (default None)

    Returns
    -------
    ndarray
        1D array containing the optimized parameters [t0, alpha, beta, k] for the fitted gamma variate function.
    """
    # Parameter search bounds
    # Minimum: t0 = 0.0, alpha = 0.1, beta = 0.1, k = 0.0
    # Maximum: t0 = 20.0, alpha = 8, beta = 8, k = max(curve) * 2
    r, _ = curve_fit(gamma_variate,
                     time_index,
                     curve,
                     bounds=([0, 0.1, 0.1, 0], [20, 8, 8, max(curve) * 2]),
                     sigma=sigma)
    return r


def generate_ttp(ctc: ndarray | list[ndarray],
                 time_index: list[float] | ndarray,
                 s0_index: int,
                 mask: ndarray,
                 outside_value: float = 0.0,
                 wait: DialogWait | None = None) -> ndarray:
    """
    Generate the Time to Peak (TTP) map from contrast time curves (ctc). TTP is the time at which the CTC reaches its
    maximum value.

    Parameters
    ----------
    ctc : ndarray | list[ndarray]
        4D ndarray (shape=[n,z,y,x]) or list of 3D ndarray (shape=[z,y,x]) representing contrast time curves.
    time_index : list | ndarray
        list of time indexes corresponding to each timepoint in ctc.
    s0_index : int
        Starting index for analysis. Time points before this index are excluded from TTP calculation (e.g., baseline measurements).
    mask : ndarray
        Binary 3D ndarray (shape=[z,y,x]) of the brain mask.
    outside_value : float (optional)
        Value assigned to voxels outside the brain mask (default 0.0).
    wait : DialogWait | None
        progress bar dialog (default None).

    Returns
    -------
    ndarray
        3D ndarray (shape=[z,y,x]) of time to peak map.
    """
    if wait is not None:
        wait.setInformationText('Time to peak map processing...')
    if isinstance(ctc, list): ctc = stack(ctc, axis=0)
    if isinstance(time_index, list): time_index = array(time_index)
    time_index = time_index[s0_index:] - time_index[s0_index]
    ctc = ctc[s0_index:, :, :, :]
    ttp = time_index[ctc.argmax(axis=0)]
    ttp[mask == 0] = outside_value
    return ttp


def generate_leakage(ctc: ndarray | list[ndarray],
                     time_index: list[float] | ndarray,
                     mask: ndarray,
                     outside_value: float = 0.0,
                     wait: DialogWait | None = None) -> ndarray:
    """
    Generate leakage map from contrast time curves (CTC).

    Parameters
    ----------
    ctc : ndarray | list[ndarray]
        4D ndarray (shape=[n,z,y,x]) or list of 3D ndarray (shape=[z,y,x]) representing contrast time curves.
    time_index : list[float] | ndarray
        list of time indexes corresponding to the ctc.
    mask : ndarray
        Binary 3D ndarray (shape=[z,y,x]) of the brain mask.
    outside_value : float (optional)
        Value assigned to voxels outside the brain mask (default 0.0).
    wait : DialogWait | None
        progress bar dialog (default None).

    Returns
    -------
    ndarray
        3D ndarray (shape=[z,y,x]) leakage map.
    """
    if wait is not None:
        wait.setInformationText('Leakage map processing...')
        wait.setProgressRange(0, mask.shape[0])
        wait.setCurrentProgressValue(0)
        wait.setProgressVisibility(True)
    r = zeros(shape=mask.shape)
    # noinspection PyUnresolvedReferences
    zi: cython.int
    # noinspection PyUnresolvedReferences
    yi: cython.int
    # noinspection PyUnresolvedReferences
    xi: cython.int
    for zi in range(ctc.shape[0]):
        for yi in range(ctc.shape[1]):
            for xi in range(ctc.shape[2]):
                if mask[zi, yi, xi] != 0.0:
                    cc = ctc[zi, yi, xi, :]
                    p = fit_gamma_variate(time_index, cc)
                    gcc = gamma_variate(time_index, *p)
                    r[zi, yi, xi] = trapz(cc - gcc)
                else: r[zi, yi, xi] = outside_value
        if wait is not None:
            wait.incCurrentProgressValue()
    if wait is not None: wait.setProgressVisibility(False)
    return r


def generate_perfusion_maps(ctc: ndarray | list[ndarray],
                            time_index: list[float] | ndarray,
                            mask: ndarray,
                            aif_properties: ndarray,
                            method: str = 'bcSVD1',
                            SVD_truncation_threshold: float = 0.1,
                            oSVD_OI_threshold: float = 0.035,
                            outside_value: float = 0.0,
                            rho: float = 1.05,
                            hcf: float = 0.73,
                            wait: DialogWait | None = None) -> tuple[ndarray, ndarray, ndarray, ndarray]:
    """
    Generate perfusion maps (MTT, CBV, CBF, TMAX) from contrast time curves (CTC) via deconvolution with the arterial
    input function (AIF). This function supports multiple SVD-based deconvolution methods. Additionally, there is the
    option to use the box-shaped model with non-linear regression optimization, as described in Bennink et al.
    
    Reference: Bennink E., Oosterbroek J., Kudo K., Viergever M.A., Velthuis B.K., de Jong H.W.A.M., Fast nonlinear 
    regression method for CT brain perfusion analysis, J. Med. Imag. 3(2),026003 (2016)

    Parameters
    ----------
    ctc : ndarray | list[ndarray]
        4D ndarray (shape=[n,z,y,x]) or list of 3D ndarray (shape=[z,y,x]) representing contrast time curves.
    time_index : list[float] | ndarray 
        list of time indexes corresponding to the ctc.
    mask : ndarray
        Binary 3D ndarray (shape=[z,y,x]) of the brain mask.
    aif_properties : ndarray
        1D array with 4 elements [t0, alpha, beta, k] representing the parameters of the fitted gamma variate function for the AIF.
    method : str (optional)
        Deconvolution method to use, either 'bcSVD1' (default), 'bcSVD2', 'SVD', 'oSVD', or 'boxNLR'.
    SVD_truncation_threshold : float (optional)
        Threshold for SVD regularization as fraction of maximum singular value (default 0.1).
    oSVD_OI_threshold : float (optional)
        Threshold for oscillation index in oSVD method (default 0.035).
    outside_value : float (optional)
        Value assigned to voxels outside the brain mask (default 0.0)
    rho : float (optional)
        Tissue density in g/ml (default 1.05)
    hcf : float (optional)
        Hematocrit correction factor (default 0.73)
    wait : DialogWait | None
        progress bar dialog (default None).

    Returns
    -------
    tuple[ndarray, ndarray, ndarray, ndarray]
    
        - mtt, 3D ndarray (shape=[z,y,x]) containing the Mean Transit Time in seconds.
        - cbv, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Volume in ml/100g.
        - cbf, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Flow in ml/100g/min.
        - tmax, 3D ndarray (shape=[z,y,x]) containing the Time to maximum of residue function in seconds.
    """
    if wait is not None:
        wait.setInformationText('CBF, CBV, MTT, TMAX maps processing...')
    aif = gamma_variate(time_index, *aif_properties)
    # Calculate time step for numerical integration
    deltaT = mean(diff(time_index))
    # Get number of time points
    nr_timepoints = len(time_index)
    # Construct convolution matrix G based on selected deconvolution method
    if method == 'SVD':
        # Original SVD method using standard Toeplitz matrix
        G = toeplitz(aif, zeros(nr_timepoints))
        ctc_pad = ctc
    elif method == 'bcSVD1':
        # Block-circulant SVD method 1 with Simpson's rule integration
        colG = zeros(2 * nr_timepoints)
        colG[0] = aif[0]
        # Apply Simpson's rule for numerical integration at boundaries
        colG[nr_timepoints - 1] = (aif[nr_timepoints - 2] + 4 * aif[nr_timepoints - 1]) / 6
        colG[nr_timepoints] = aif[nr_timepoints - 1] / 6
        # Apply Simpson's rule for interior points
        for k in range(1, nr_timepoints - 1):
            colG[k] = (aif[k - 1] + 4 * aif[k] + aif[k + 1]) / 6
        # Construct row vector for circulant matrix
        rowG = zeros(2 * nr_timepoints)
        rowG[0] = colG[0]
        for k in range(1, 2 * nr_timepoints):
            rowG[k] = colG[2 * nr_timepoints - k]
        # Create block-circulant matrix
        G = toeplitz(colG, rowG)
        # Pad contrast data by doubling temporal dimension
        # noinspection PyTypeChecker
        ctc_pad = pad(ctc, [(0, len(ctc)), ] + [(0, 0)] * 3)
    elif method == 'bcSVD2':
        # Block-circulant SVD method 2 with manual matrix construction
        cmat = zeros([nr_timepoints, nr_timepoints])
        B = zeros([nr_timepoints, nr_timepoints])
        # Build circulant and anti-circulant blocks
        for i in range(nr_timepoints):
            for j in range(nr_timepoints):
                if i == j: cmat[i, j] = aif[0]
                elif i > j: cmat[i, j] = aif[(i - j)]
                else: B[i, j] = aif[nr_timepoints - (j - i)]
        # Construct 2x2 block matrix
        G = vstack([hstack([cmat, B]), hstack([B, cmat])])
        # Pad contrast data by doubling temporal dimension
        # noinspection PyTypeChecker
        ctc_pad = pad(ctc, [(0, len(ctc)), ] + [(0, 0)] * 3)
    elif method == 'oSVD':
        # Oscillation index SVD method with adaptive regularization
        # Uses block-circulant matrix construction similar to bcSVD1
        colG = zeros(2 * nr_timepoints)
        colG[0] = aif[0]
        # Apply Simpson's rule for numerical integration at boundaries
        colG[nr_timepoints - 1] = (aif[nr_timepoints - 2] + 4 * aif[nr_timepoints - 1]) / 6
        colG[nr_timepoints] = aif[nr_timepoints - 1] / 6
        # Apply Simpson's rule for interior points
        for k in range(1, nr_timepoints - 1):
            colG[k] = (aif[k - 1] + 4 * aif[k] + aif[k + 1]) / 6
        # Construct row vector for circulant matrix
        rowG = zeros(2 * nr_timepoints)
        rowG[0] = colG[0]
        for k in range(1, 2 * nr_timepoints):
            rowG[k] = colG[2 * nr_timepoints - k]
        # Create block-circulant matrix
        G = toeplitz(colG, rowG)
        # Pad contrast data by doubling temporal dimension
        # noinspection PyTypeChecker
        ctc_volumes_pad = pad(ctc, [(0, len(ctc)), ] + [(0, 0)] * 3)
        # Use oSVD-specific processing instead of standard SVD approach
        # noinspection PyTypeChecker
        mtt, cbv, cbf, tmax = oSVD(ctc_volumes_pad, G, deltaT, mask, oSVD_OI_threshold, nr_timepoints, outside_value,
                                   rho, hcf, time_index, wait=wait)
        return mtt, cbv, cbf, tmax
    elif method == 'boxNLR':
        # noinspection PyTypeChecker
        mtt, cbv, cbf, tmax = boxNLR(ctc, aif, deltaT, mask, outside_value=-1, wait=wait)
        return mtt, cbv, cbf, tmax
    # Perform SVD decomposition on scaled convolution matrix
    # noinspection PyUnboundLocalVariable
    U, S, V = svd(G * deltaT)
    # Apply threshold-based regularization to singular values
    thres = SVD_truncation_threshold * max(S)
    filteredS = 1 / (S + 1e-5)  # Add small epsilon to avoid division by zero
    filteredS[S < thres] = 0  # Zero out small singular values below threshold
    # Reconstruct pseudo-inverse matrix using filtered singular values
    Ginv = V.T @ diag(filteredS) @ U.T
    # Perform deconvolution to obtain residue function R
    # noinspection PyUnboundLocalVariable
    R = abs(einsum('ab, bcde->acde', Ginv, ctc_pad))
    # Truncate residue function to original temporal length
    R = R[:nr_timepoints]
    # Calculate perfusion parameters from residue function
    # tissue-to-artery concentration scale factor ratio = 0.1369
    # CBF Maximum of residue function scaled by physiological constants (ml/100g/min)
    cbf = hcf / rho * R.max(axis=0) * 60 * 100 * 0.1369
    # CBV Area under residue function scaled by physiological constants (ml/100g)
    cbv = hcf / rho * R.sum(axis=0) * 100 * 0.1369
    # MTT Mean transit time calculated as CBV/CBF ratio (seconds)
    mtt = divide(cbv, cbf, out=zeros_like(cbv), where=cbf != 0) * 60
    # Calculate time to maximum of residue function (tmax)
    time_index = array(time_index, dtype=int)
    tmax = time_index[R.argmax(axis=0)]
    tmax = tmax.astype(float64)
    # Apply brain mask to set outside values for all perfusion maps
    tmax[mask == 0] = outside_value
    cbv[mask == 0] = outside_value
    cbf[mask == 0] = outside_value
    mtt[mask == 0] = outside_value
    return mtt, cbv, cbf, tmax


def oSVD(ctc_pad: ndarray,
         G: ndarray,
         deltaT: float,
         mask: ndarray,
         oSVD_OI_threshold : float,
         nr_timepoints: int,
         outside_value: float,
         rho: float,
         hcf: float,
         time_index: list[float] | ndarray,
         wait: DialogWait | None = None) -> tuple[ndarray, ndarray, ndarray, ndarray]:
    """
    This function implements the oscillation index SVD method which adaptively selects the optimal SVD truncation
    threshold for each voxel based on minimizing oscillations in the residue function.

    Parameters
    ----------
    ctc_pad : ndarray
        4D array of padded contrast time curves.
    G : ndarray)
        Block-circulant convolution matrix.
    deltaT : float
        Time step for numerical integration.
    mask : ndarray
        Binary 3D ndarray (shape=[z,y,x]) of the brain mask.
    oSVD_OI_threshold : float
        Oscillation index threshold.
    nr_timepoints : int
        Number of original timepoints.
    outside_value : float
        Value for voxels outside mask.
    rho : float
        Tissue density
    hcf : float
        Hematocrit correction factor
    time_index : list[float] | ndarray
        Time indices
    wait : DialogWait | None
        progress bar dialog (default None).

    Returns
    -------
    tuple[ndarray, ndarray, ndarray, ndarray]

        - mtt, 3D ndarray (shape=[z,y,x]) containing the Mean Transit Time in seconds.
        - cbv, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Volume in ml/100g.
        - cbf, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Flow in ml/100g/min.
        - tmax, 3D ndarray (shape=[z,y,x]) containing the Time to maximum of residue function in seconds.
    """
    # Perform SVD decomposition on scaled convolution matrix
    U, S, V = svd(G * deltaT)
    # Initialize output arrays
    z, y, x = mask.shape
    cbf = zeros((z, y, x))
    cbv = zeros((z, y, x))
    mtt = zeros((z, y, x))
    tmax = zeros((z, y, x))
    # Process each voxel individually for adaptive threshold selection
    if wait is not None:
        wait.addInformationText('Oscillation index SVD method, '
                                'this process may take longer than traditional SVD methods.')
        wait.setProgressRange(0, mask.shape[0])
        wait.setCurrentProgressValue(0)
        wait.setProgressVisibility(True)
    # noinspection PyUnresolvedReferences
    zi: cython.int
    # noinspection PyUnresolvedReferences
    yi: cython.int
    # noinspection PyUnresolvedReferences
    xi: cython.int
    for zi in range(z):
        for yi in range(y):
            for xi in range(x):
                if mask[zi, yi, xi]:
                    # Extract concentration time curve for current voxel
                    vett_conc = ctc_pad[:, zi, yi, xi]
                    # Find optimal threshold using oscillation index
                    best_residue = None
                    # Test thresholds from 5% to 95% of maximum singular value
                    for threshold_percent in range(5, 100, 5):
                        threshold = (threshold_percent / 100.0) * S[0]
                        # Create filtered inverse matrix
                        filtered_S = 1.0 / (S + 1e-5)
                        filtered_S[S < threshold] = 0
                        G_inv = V.T @ diag(filtered_S) @ U.T
                        # Calculate residue function
                        residue = G_inv @ vett_conc
                        residue = abs(residue)
                        # Calculate oscillation index
                        oscillation = 0.0
                        L = len(residue)
                        for j in range(2, L):
                            oscillation += abs(residue[j] - 2 * residue[j - 1] + residue[j - 2])
                        max_residue = max(residue)
                        if max_residue > 0: OI = (1.0 / L) * (1.0 / max_residue) * oscillation
                        else: OI = float('inf')
                        # Use this threshold if oscillation index is below threshold
                        if OI < oSVD_OI_threshold:
                            best_residue = residue
                            break
                    # If no threshold met criteria, use the most restrictive one
                    if best_residue is None:
                        threshold = 0.95 * S[0]
                        filtered_S = 1.0 / (S + 1e-5)
                        filtered_S[S < threshold] = 0
                        G_inv = V.T @ diag(filtered_S) @ U.T
                        best_residue = abs(G_inv @ vett_conc)
                    # Truncate residue function to original temporal length
                    residue_truncated = best_residue[:nr_timepoints]
                    # Calculate perfusion parameters for this voxel
                    cbf[zi, yi, xi] = hcf / rho * max(residue_truncated) * 60 * 100
                    cbv[zi, yi, xi] = hcf / rho * sum(residue_truncated) * 100
                    if cbf[zi, yi, xi] != 0:
                        mtt[zi, yi, xi] = (cbv[zi, yi, xi] / cbf[zi, yi, xi]) * 60
                    # Calculate time to maximum
                    time_index_array = array(time_index[:nr_timepoints], dtype=int)
                    tmax[zi, yi, xi] = float(time_index_array[argmax(residue_truncated)])
        if wait is not None:
            wait.incCurrentProgressValue()
    if wait is not None: wait.setProgressVisibility(False)
    # Apply brain mask to set outside values
    tmax[mask == 0] = outside_value
    cbv[mask == 0] = outside_value
    cbf[mask == 0] = outside_value
    mtt[mask == 0] = outside_value
    return mtt, cbv, cbf, tmax


def boxNLR(ctc: ndarray | list[ndarray],
           aif: ndarray,
           dt: float,
           mask: ndarray,
           outside_value: float = 0.0,
           wait: DialogWait | None = None):
    """
    This is the main function which generates perfusion maps using the boxNLR (box Non-Linear Regression) approach by
    bennink et al.

    Reference: Bennink E., Oosterbroek J., Kudo K., Viergever M.A., Velthuis B.K., de Jong H.W.A.M., Fast nonlinear
    regression method for CT brain perfusion analysis, J. Med. Imag. 3(2),026003 (2016)

    Be aware that this is just my attempt at implementing the method, this approach is very slow, and I am not sure it
    is implemented correctly. So please use with caution and verify results carefully.

    Parameters
    ----------
    ctc :  ndarray | list[ndarray]
        4D ndarray (shape=[n,z,y,x]) or list of 3D ndarray (shape=[z,y,x]) representing contrast time curves.
    aif : ndarray
        1D array containing the AIF signal.
    dt : float
        Time step (sampling interval) in seconds.
    mask : ndarray
        Binary 3D ndarray (shape=[z,y,x]) of the brain mask.
    outside_value : float (optional)
        Value to assign to voxels outside the brain mask in the output maps.
    wait : DialogWait | None
        progress bar dialog (default None).

    Returns
    -------
    tuple[ndarray, ndarray, ndarray, ndarray]

        - mtt, 3D ndarray (shape=[z,y,x]) containing the Mean Transit Time in seconds.
        - cbv, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Volume in ml/100g.
        - cbf, 3D ndarray (shape=[z,y,x]) containing the Cerebral Blood Flow in ml/100g/min.
        - tmax, 3D ndarray (shape=[z,y,x]) containing the Time to maximum of residue function in seconds.
    """

    # Non-linear regression method using boxNLR model
    if wait is not None:
        wait.addInformationText('Using box non linear regression method, '
                                'this process may take much longer than SVD methods.')
        wait.setProgressRange(0, mask.shape[0])
        wait.setCurrentProgressValue(0)
        wait.setProgressVisibility(True)
    # Convert list of 3D volumes to a 4D array (t, z, y, x)
    if isinstance(ctc, list): ctc = stack(ctc, axis=0)
    # Initialize output arrays
    cbf =zeros(ctc.shape[1:])
    cbv = zeros(ctc.shape[1:])
    mtt = zeros(ctc.shape[1:])
    tmax = zeros(ctc.shape[1:])
    # Get brain voxel coordinates
    brain_coords = where(mask == 1)
    total_voxels = len(brain_coords[0])
    # Process each brain voxel
    # noinspection PyUnresolvedReferences
    z: cython.int
    # noinspection PyUnresolvedReferences
    y: cython.int
    # noinspection PyUnresolvedReferences
    x: cython.int
    # noinspection PyUnresolvedReferences
    idx: cython.int
    for idx, (z, y, x) in enumerate(zip(*brain_coords)):
        if idx % 1000 == 0 and wait is not None:
            wait.setCurrentProgressValuePercent(int(100 * idx / total_voxels), idx)
        # Extract tissue curve for this voxel
        ctc = ctc[:, z, y, x]
        # Fit NLR model
        fit_result = fit_boxNLR(aif, ctc, dt)
        # Store results
        cbf[z, y, x] = fit_result['cbf']
        cbv[z, y, x] = fit_result['cbv']
        mtt[z, y, x] = fit_result['mtt']
        tmax[z, y, x] = fit_result['tmax']
    # Apply brain mask to set outside values for all perfusion maps
    cbf[mask == 0] = outside_value
    cbv[mask == 0] = outside_value
    mtt[mask == 0] = outside_value
    tmax[mask == 0] = outside_value
    if wait is not None: wait.setProgressVisibility(False)
    return mtt, cbv, cbf, tmax


def fit_boxNLR(aif: ndarray,
               ctc: ndarray,
               dt: float) -> dict[str, float]:
    """
    Optimize (fit) the box-shaped residue function such that it explains the measured CTC with the given AIF. The
    box-shaped residue function is defined by three parameter: CBV, MTT, and delay. The function returns the optimal
    values for these parameters. Hence by fitting the box-shaped residue function, we obtain perfusion parameters
    directly.

    Parameters
    ----------
    aif : ndarray
        1D array containing the arterial input function.
    ctc : ndarray
        1D array containing the contrast time curve for a single voxel.
    dt : float
        Sample interval (time step).

    Returns
    -------
    dict
        Dictionary containing the optimized perfusion parameters ['cbf', 'mtt', 'cbv', 'tmax'].
    """

    def objective(p):
        pcbf, pmtt, pdelay = p
        n = len(auc)
        # Create interpolation indices with half sample shift correction
        indices = arange(1, n + 1) - 0.5 - pdelay
        indices_shifted = arange(1, n + 1) - 0.5 - pdelay - pmtt
        # Create interpolation function for AUC
        # noinspection PyDeprecation
        auc_interp = interp1d(arange(len(auc)), auc, kind='linear', bounds_error=False, fill_value=0)
        # Interpolate at shifted indices
        a = auc_interp(indices)
        b = auc_interp(indices_shifted)
        # Handle NaN values (set to 0)
        a = nan_to_num(a, nan=0.0)
        b = nan_to_num(b, nan=0.0)
        # Calculate TAC as difference of shifted integrands
        ctc_estimated = pcbf * (a - b)
        sse = sum((ctc_estimated - ctc_band_limited) ** 2)
        return sse

    # Initial estimates for CBV, MTT, and delay, respectively.
    # Divide MTT and delay by dt seconds to convert to unitless values.
    params = array([0.05, 4 / dt, 1 / dt])
    # Create a 3-point bandlimiting kernel with a FWHM of 2 samples.
    kernel = array([0.25, 0.5, 0.25])
    # Extend arrays with nearest neighbor extrapolation, such that convolution does not reduce length
    # noinspection PyTypeChecker
    aif_extended = concatenate([[aif[0]], aif, [aif[-1]]])
    # noinspection PyTypeChecker
    ctc_extended = concatenate([[ctc[0]], ctc, [ctc[-1]]])
    # Convolve the AIF and measured CTC with the kernel to obtain bandlimited versions
    aif_band_limited = convolve(aif_extended, kernel, mode='valid')
    ctc_band_limited = convolve(ctc_extended, kernel, mode='valid')
    # Calculate the numerical integrand of the bandlimited AIF.
    # Note that this cumulative sum introduces a half sample shift.
    auc = cumsum(aif_band_limited)
    # Use scipy minimize with Nelder-Mead method to find the optimal parameters for the box-shaped residue function.
    # Optimal is defined as the box-model parameters that minimize the sum of squared errors between the measured CTC and the estimated CTC.
    # The estimated CTC is generated from the AIF (auc) and the box-shaped residue function.
    optimal_params = minimize(objective, params, method='Nelder-Mead').x
    # Multiply MTT and delay by dt seconds to convert from unitless values.
    optimal_params = array([optimal_params[0], optimal_params[1] * dt, optimal_params[2] * dt])
    cbv, mtt, delay = optimal_params
    cbf = cbv / (mtt / 60) if mtt > 0 else 0  # Convert MTT from seconds to minutes for CBF calculation
    # Calculate tmax as delay + mtt/2 (center of box function)
    tmax = delay + mtt / 2
    r = {'cbf': cbf * 60,  # Convert to ml/100g/min
         'mtt': mtt,  # Already in seconds
         'cbv': cbv * 100,  # Convert to ml/100g
         'tmax': tmax}
    return r


def dscMaps2(vols: SisypheVolume,
             mask: SisypheVolume,
             aif: ndarray,
             tr: float, te: float,
             baseline: tuple[int, int] = (0, 4),
             smooth: float = 0.0,
             recovery: bool = True,
             dsc: bool = True,
             leakage: bool = True,
             method: str = 'bcSVD1',
             svdtuncation: float = 0.1,
             osvdoi : float = 0.035,
             outsidev : float = 0.0,
             wait: DialogWait | None = None) -> dict[str, SisypheVolume]:
    """
    Dynamic susceptibility contrast MR perfusion maps processing:
    - cerebral blood flow (CBF), in ml / min / 100g
    - cerebral blood volume (CBV), in ml / 100g
    - mean transit time (MTT), in s
    - leakage volume (LKV), in ml / 100g
    - time to pic (TTP), in s
    - time to maximum (TMAX), in s
    - signal recovery (SR)
    - percentage signal recovery (PSR)

    PyPeT Python Perfusion Tool implementation
    https://github.com/Marijn311/CT-and-MR-Perfusion-Tool

    Reference: PyPeT: A Python Perfusion Tool for Automated Quantitative Brain CT and MR Perfusion Analysis.
    Borghouts M. & Su R. arXiv:2511.13310v1 [eess.IV] 17 Nov 2025.

    Parameters
    ----------
    vols : Sisyphe.core.sisypheVolume.SisypheVolume
        time series of perfusion weighted images
    mask : Sisyphe.core.sisypheVolume.SisypheVolume
        brain mask
    aif : ndarray
        arterial input function (as signal, not contrast concentration)
    tr : float
        repetition time (TR) in s
    te : float
        echo time (TE) in s
    baseline : tuple[int, int]
        range (start, end) of volume indices used as baseline signal
        (default first 4 volumes, start=0, end=4)
    smooth : float (optional)
        time series fwhm smoothing if true (default 0.0, no smoothing)
    recovery : bool
        Signal recovery maps processing if True
    dsc : bool
        CBF, CBV, MTT, TMAX, TTP maps processing if True
    leakage : bool
        Leakage correction of contrast concentration maps if True (default)
    method : str (optional)
        Deconvolution method to use, either 'bcSVD1' (default), 'bcSVD2', 'SVD', 'oSVD', or 'boxNLR'.
    svdtuncation : float (optional)
        Threshold for SVD regularization as fraction of maximum singular value (default 0.1).
    osvdoi : float (optional)
        Threshold for oscillation index in oSVD method (default 0.035).
    outsidev : float (optional)
        Value assigned to voxels outside the brain mask (default 0.0).
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress bar dialog (default None)

    Returns
    -------
    dict[str, SisypheVolume]
        dsc maps, dict keys: 'cbf', 'cbv', 'mtt', 'ttp', 'tmax', 'lkv', 'sr', 'psr'
    """
    r: dict[str, SisypheVolume] = dict()
    # smooth
    if smooth > 0.0:
        if wait is not None:
            wait.setInformationText('Smoothing...')
            wait.setProgressRange(0, vols.getNumberOfComponentsPerPixel())
            wait.setCurrentProgressValue(0)
            wait.setProgressVisibility(True)
        c = 2 * sqrt(2 * log(2))
        sigma = smooth / c
        v = vols.copyToNumpyArray(defaultshape=True)
        tag = mask.isIsotropic()
        for i in range(v.shape[0]):
            slc = v[i, :, :, :]
            if tag: v[i, :, :, :] = gaussian_filter(slc, sigma)  # 3D smoothing if isotropic
            else: v[i, :, :, :] = gaussian_filter(slc, sigma, axes=(0, 1, 1))  # 2D smoothing if anostropic
            if wait is not None: wait.incCurrentProgressValue()
        vols.copyFromNumpyArray(v, defaultshape=True)
        if wait is not None: wait.setProgressVisibility(False)
    # signal to contrast concentration
    if wait is not None:
        wait.setInformationText('Signal to concentration processing...')
    ctc_vols = signalToContrastConcentration(vols, mask, te, baseline)
    ctc_vols.setFilename(vols.getFilename())
    ctc_vols.setFilenameSuffix('cc')
    ctc_vols.save()
    # arterial input function processing
    if wait is not None:
        wait.setInformationText('Arterial input function processing...')
    time_index = array([i * tr for i in range(ctc_vols.getNumberOfComponentsPerPixel())])
    s0 = mean(aif[baseline[0]:baseline[1]])
    aif = (-1 / te) * (log(aif / s0))
    aif = where(aif <= 0.0, 0.0, aif)
    aif_properties = fit_gamma_variate(time_index, aif)
    if recovery:
        # SR/PSR maps processing
        t0 = where(aif.cumsum() == 0.0)[0]
        if len(t0) > 0: t0 = t0[-1]
        else: t0 = 0
        v = signalRecoveryMaps(vols, mask, t0, tr, baseline, wait)
        r['sr'] = v['sr']
        r['psr'] = v['psr']
    if dsc:
        ttp = generate_ttp(ctc_vols.getNumpy(defaultshape=True),
                           time_index,
                           baseline[1],
                           mask.getNumpy(defaultshape=True),
                           outsidev,
                           wait)
        mtt, cbv, cbf, tmax = generate_perfusion_maps(ctc_vols.getNumpy(defaultshape=True),
                                                      time_index,
                                                      mask.getNumpy(defaultshape=True),
                                                      aif_properties,
                                                      method,
                                                      svdtuncation,
                                                      osvdoi,
                                                      outsidev)
        # TTP, Time to Peak
        r['ttp'] = SisypheVolume()
        r['ttp'].copyFromNumpyArray(ttp,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=True)
        r['ttp'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['ttp'].acquisition.setSequenceToMeanTransitTimeMap()
        r['ttp'].acquisition.setUnit('s')
        r['ttp'].display.getLUT().setLut('inserm')
        r['ttp'].setFilename(vols.getFilename())
        r['ttp'].setFilenameSuffix('ttp')
        # CBV, Cerebral Blood Volume
        r['cbv'] = SisypheVolume()
        r['cbv'].copyFromNumpyArray(cbv,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=True)
        r['cbv'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['cbv'].acquisition.setSequenceToCerebralBloodVolumeMap()
        r['cbv'].acquisition.setUnit('ml / 100g')
        r['cbv'].display.getLUT().setLut('inserm')
        r['cbv'].setFilename(vols.getFilename())
        r['cbv'].setFilenameSuffix('cbv')
        # CBF, Cerebral Blood Flow
        r['cbf'] = SisypheVolume()
        r['cbf'].copyFromNumpyArray(cbf,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=True)
        r['cbf'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['cbf'].acquisition.setSequenceToCerebralBloodFlowMap()
        r['cbf'].acquisition.setUnit('ml / min / 100g')
        r['cbf'].display.getLUT().setLut('inserm')
        r['cbf'].setFilename(vols.getFilename())
        r['cbf'].setFilenameSuffix('cbf')
        # MTT, Mean Transit Time
        r['mtt'] = SisypheVolume()
        r['mtt'].copyFromNumpyArray(mtt,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=True)
        r['mtt'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['mtt'].acquisition.setSequenceToMeanTransitTimeMap()
        r['mtt'].acquisition.setUnit('s')
        r['mtt'].display.getLUT().setLut('inserm')
        r['mtt'].setFilename(vols.getFilename())
        r['mtt'].setFilenameSuffix('mtt')
        # TMAX, Mean Transit Time
        r['tmax'] = SisypheVolume()
        r['tmax'].copyFromNumpyArray(tmax,
                                     spacing=mask.getSpacing(),
                                     origin=vols.getOrigin(),
                                     direction=vols.getDirections(),
                                     defaultshape=True)
        r['tmax'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['tmax'].acquisition.setSequenceToMeanTransitTimeMap()
        r['tmax'].acquisition.setUnit('s')
        r['tmax'].display.getLUT().setLut('inserm')
        r['tmax'].setFilename(vols.getFilename())
        r['tmax'].setFilenameSuffix('tmax')
    if leakage:
        lkv = generate_leakage(ctc_vols.getNumpy(defaultshape=True),
                               time_index,
                               mask.getNumpy(),
                               outsidev,
                               wait)
        lkv = nan_to_num(lkv, nan=0.0, posinf=0.0, neginf=0.0)
        r['lkv'] = SisypheVolume()
        r['lkv'].copyFromNumpyArray(lkv,
                                    spacing=mask.getSpacing(),
                                    origin=vols.getOrigin(),
                                    direction=vols.getDirections(),
                                    defaultshape=True)
        r['lkv'].copyAttributesFrom(vols, display=False, slope=False, acquisition=False)
        r['lkv'].acquisition.setModalityToOT()
        r['lkv'].acquisition.setSequence('LKV')
        r['lkv'].acquisition.setUnit('ml / 100g')
        r['lkv'].display.getLUT().setLut('inserm')
        r['lkv'].setFilename(vols.getFilename())
        r['lkv'].setFilenameSuffix('lkv')
    return r

"""
Arterial Spin Labeling (ASL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

function
~~~~~~~~

The code was adapted from:
 
    - erwin qMRI toolbox, https://github.com/lamyj/erwin
    - https://github.com/SaraDupont/ASL_processing
    
    - cbfASLMap

references: 

Comparison of quantitative perfusion imaging using arterial spin labeling at 1.5 and 4.0 Tesla. Wang J, Alsop DC, Li L, 
Listerud J., Gonzalez-At J.B., Schnall M.D., Detre J.A. Magn Reson Med. 2002 Aug;48(2):242-54.

Correcting for the echo-time effect after measuring the cerebral blood flow by arterial spin labeling.
Foucher J.R., Roquet D., Marrer C., Pham B.T., Gounot D. J Magn Reson Imaging. 2011 Oct;34(4):785-90.

A Beginner's Guide to Arterial Spin Labeling (ASL) Image Processing. Clement P., Petr J., Dijsselhof M.B.J., Padrela B., 
Pasternak M., Dolui S., Jarutyte L., Pinter N., Hernandez-Garcia L., Jahn A., Kuijer J.P.A., Barkhof F., 
Mutsaerts H.J.M., Keil V.C. Front Radiol. 2022 Jun 14:2:929533.

In vivo blood T1 measurements at 1.5 T, 3 T, and 7 T. Zhang X., Petersen E.T., Ghariq E., De Vis J.B., Webb A.G., 
Teeuwisse W.M., Hendrikse J. van Osch M.J.P. Magn Reson Med. 2013 70:1082–1086.
"""


def cbfASLMap(m0: SisypheVolume,
              asl: list[SisypheVolume] | SisypheVolumeCollection,
              mask: SisypheVolume | None,
              sequence: str,
              ti1: float,
              ti2: float,
              te: float | None = None,
              tr: float | None = None,
              lmbda: float = 0.9,
              alpha: float = 0.98,
              t1blood: float = 1640.0) -> SisypheVolume:
    """
    CBF processing from Arterial Spin Labeling (ASL) series.
    Cerebral blood flow (CBF) in ml / min / 100g

    Code adpated from https://github.com/SaraDupont/ASL_processing & https://github.com/lamyj/erwin

    Parameters
    ----------
    m0 : SisypheVolume
        M0 control proton density weighted volume, acquired without blood spin tagging
    asl : list[SisypheVolume] | SisypheVolumeCollection
        ASL volumes, acquired after blood spin tagging
    mask : SisypheVolume
        mask of analyzis, voxels outisde mask are set to 0.0
    sequence : str
        type of ASL sequence 'pasl' (pulsed ASL) or 'pcasl' (pseudo-continuous ASL)
    ti1 : float
        label duration (LD) in ms (typically 700-900 ms in pasl, 1800-2000 ms in pcasl)
    ti2 : float
        post labeling delay (PLD) in ms (typically 1600-2000 ms in pasl, 1800-2000 ms in pcasl)
    te : float | None (optional)
        echo time in ms, used for magnetization correction. No correction if None (default None, no correction)
    tr : float | None (optional)
        repetition time in ms, used to correct intensity of proton density weighted volume if the repetition time is too short (default None, no correction)
    lmbda : float (optional)
        lambda paramter, blood brain partition coefficient in mL/g eq. L/Kg (default 0.9)

            - 0.9 mL/g in Wang et al. and Foucher et al. (global)
            - 0.98 mL/g in Foucher (gray matter)
            - 0.81 mL/g in Foucher (white matter)
    alpha : float
        alpha parameter, labeling efficiency (default 0.98; 0.95 in Wang et al. and Foucher et al.)
    t1blood : float
        T1 relaxation time of blood in ms (default 1650)

            - ~1200–1350 ms 1.5T, Zhang et al.
            - ~1600–1700 ms 3.0T, Zhang et al.
            - ~2100–2300 ms 7.0T, Zhang et al.

    Returns
    -------
    SisypheVolume
        CBF map
    """
    if isinstance(asl, list):
        buff = SisypheVolumeCollection()
        buff.copyFromList(asl)
        asl = buff
    asl = asl.getMeanVolume()
    filename = m0.getFilename()
    filename = filename.replace('_M0', '')
    asl.setFilename(filename)
    asl.setFilenameSuffix('MEAN_TAG')
    asl.save()
    ti1 /= 1000.0
    ti2 /= 1000.0
    t1blood /= 1000.0
    if te is not None: te /= 1000.0
    corrtr = 1.0
    if tr is not None:
        tr /= 1000.0
        if tr > 0.0:
            # correct intensity of proton density weighted volume if the repetition time is too short
            t1gm = 1.82
            corrtr = 1.0 - exp(- tr / t1gm)
    if corrtr != 1.0: sub = (m0.getNumpy() / corrtr) - asl.getNumpy()
    else: sub = m0.getNumpy() - asl.getNumpy()
    v = SisypheVolume()
    v.copyFromNumpyArray(sub,
                         spacing=m0.getSpacing(),
                         origin=m0.getOrigin(),
                         direction=m0.getDirections())
    v.copyAttributesFrom(m0, display=False, slope=False, acquisition=False)
    v.acquisition.setSequenceToCerebralBloodFlowMap()
    v.setFilename(filename)
    v.setFilenameSuffix('SUB')
    v.save()
    # Difference in the apparent transverse relaxation rates between
    # labeled water in capillaries and nonlabeled water in the tissue, in Hz
    deltar2 = 20.0
    if te is None or te == 0.0: corrte = 1.0
    else: corrte = exp(deltar2 * te)
    if sequence == 'pasl':
        cbf = ((60.0 * lmbda * sub * corrte * exp(ti2 / t1blood)) /
               (2 * alpha * ti1 * m0.getNumpy()))
    elif sequence == 'pcasl':
        cbf = ((60.0 * lmbda * sub * corrte * exp(ti2 / t1blood)) /
               (2 * alpha * t1blood * m0.getNumpy() * (1 - exp(-ti1 / t1blood))))
    else: raise ValueError('{} invalid sequence, pasl or pcasl')
    cbf = nan_to_num(cbf, nan = 0.0, posinf = 0.0, neginf = 0.0)
    if mask is not None: cbf = cbf * mask.getNumpy()
    cbf[cbf < 0.0] = 0.0
    cbf[cbf > 1000.0] = 1000.0
    r = SisypheVolume()
    r.copyFromNumpyArray(cbf,
                         spacing=m0.getSpacing(),
                         origin=m0.getOrigin(),
                         direction=m0.getDirections())
    r.copyAttributesFrom(m0, display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToCerebralBloodFlowMap()
    r.acquisition.setUnit('ml / min / 100g')
    r.display.getLUT().setLut('inserm')
    r.setFilename(filename)
    r.setFilenameSuffix(r.acquisition.CBF)
    return r
