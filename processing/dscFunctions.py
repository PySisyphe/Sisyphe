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
from numpy.linalg import svd

from typing import Union

from scipy.special import gamma
from scipy.optimize import minimize

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
           'dscMaps']

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
            - SisypheVolume: aif voxels, each voxel is labelled according to its sorting rank
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
            vargmin = (mmin - vargmin).cast('float32')
            vrange = vols.getComponentMean(slice(3)).cast('float32') - vols.getComponentMin().cast('float32')
            vparam = vrange * vargmin * mask * mask2
            if n < 10: n = 10
            # Select voxels according to vparam
            threshold = sort(vparam.getNumpy().flatten())[-n]
            vrange = vrange * (vparam >= threshold).cast('float32')
            # Sort aif voxels according to vrange
            # Each voxel is labelled according to its sorting rank.
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
        wait.setInformationText('SR/PSR maps processing...')
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
        perfusion maps, dict keys: 'cbf', 'cbv', 'mtt', 'lkv', 'ttp', 'ttb', 'sr', 'psr'
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
    - x (1 - Ha) / (1 - Ht) = 0.55 / 0.75
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
