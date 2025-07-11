"""
External packages/modules
-------------------------

    - Cython, static compiler, https://cython.org/
    - Numpy, scientific computing, https://numpy.org/
    - Scipy, scientific computing, https://docs.scipy.org/doc/scipy/index.html
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import splitext

from xml.dom import minidom

from math import log
from math import pi
from math import exp
from math import cos
from math import sqrt
from math import gamma
from math import isnan
from math import isinf

import cython

from numpy import array
from numpy import any
from numpy import all
from numpy import arange
from numpy import stack
from numpy import column_stack
from numpy import zeros
from numpy import ones
from numpy import ndarray
from numpy import finfo
from numpy import power
from numpy import sort
from numpy import median
from numpy import percentile
from numpy import corrcoef
from numpy import append
from numpy import insert
from numpy import where
from numpy import convolve
from numpy import euler_gamma
from numpy import count_nonzero
from numpy import argmax
from numpy import bincount
from numpy import unravel_index
from numpy.linalg import matrix_rank
from numpy.linalg import inv
from numpy.linalg import pinv

from scipy.stats import t as student
from scipy.stats import norm
from scipy.stats import chi2
from scipy.stats import gamma as gamma2
from scipy.linalg import toeplitz

from SimpleITK import ConnectedComponentImageFilter
from SimpleITK import RelabelComponentImageFilter
from SimpleITK import LabelStatisticsImageFilter
from SimpleITK import GetArrayViewFromImage
from SimpleITK import Cast

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheConstants import addSuffixToFilename
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['tTopvalue',
           'zTopvalue',
           'pvalueTot',
           'pvalueToz',
           'zTot',
           'tToz',
           'pCorrectedBonferroni',
           'pUncorrectedBonferroni',
           'qFDRToz',
           'qFDRTot',
           'tFieldEulerCharacteristic',
           'zFieldEulerCharacteristic',
           'reselCount',
           'tFieldExpectedClusters',
           'zFieldExpectedClusters',
           'tFieldExpectedVoxels',
           'zFieldExpectedVoxels',
           'expectedVoxelsPerCluster',
           'extentToClusterUncorrectedpvalue',
           'extentToClusterCorrectedpvalue',
           'clusterUncorrectedpvalueToExtent',
           'clusterCorrectedpvalueToExtent',
           'voxelCorrectedpvalueTot',
           'voxelCorrectedpvalueToz',
           'tToVoxelCorrectedpvalue',
           'zToVoxelCorrectedpvalue',
           'getDOF',
           'isRankDeficient',
           'getHRF',
           'getBoxCarModel',
           'convolveModelHRF',
           'getHighPass',
           'tTozmap',
           'conjunctionFisher',
           'conjunctionWorsley',
           'conjunctionStouffer',
           'conjunctionMudholkar',
           'conjunctionTippett',
           'autocorrelationsEstimate',
           'modelEstimate',
           'tmapContrastEstimate',
           'zmapContrastEstimate',
           'thresholdMap',
           'SisypheDesign']

"""
Functions
~~~~~~~~~

    - tTopvalue(float, float) -> float
    - zTopvalue(float) -> float
    - pvalueTot(float, float) -> float
    - pvalueToz(float, float) -> float
    - zTot(float, float) -> float
    - tToz(float, float) -> float
    - pCorrectedBonferroni(float, int) -> float
    - pUncorrectedBonferroni(float, int) -> float
    - qFDRToz(float, SisypheVolume, bool) -> float
    - qFDRTot(float, SisypheVolume, bool) -> float
    - tFieldEulerCharacteristic(float, float) -> tuple[float, ...]
    - zFieldEulerCharacteristic(float, float) -> tuple[float, ...]
    - reselCount(SisypheVolume, float, float, float) -> tuple[float, ...]
    - tFieldExpectedClusters(float, float, float, float, float, float) -> float
    - zFieldExpectedClusters(float, float, float, float, float, float) -> float
    - tFieldExpectedVoxels(float, float, int) -> float
    - zFieldExpectedVoxels(float, int) -> float
    - expectedVoxelsPerCluster(float, float) -> float
    - extentToClusterUncorrectedpvalue(int, float, float) -> float
    - extentToClusterCorrectedpvalue(int, float, float) -> float
    - clusterUncorrectedpvalueToExtent(float, float, float) -> int
    - clusterCorrectedpvalueToExtent(float, float, float) -> int
    - voxelCorrectedpvalue(float) -> float
    - tToVoxelCorrectedpvalue(float, float, float, float, float, float) -> float
    - zToVoxelCorrectedpvalue(float, float, float, float, float, float) -> float
    - voxelCorrectedpvalueTot(float, float, float, float, float, float) -> float
    - voxelCorrectedpvalueToz(float, float, float, float, float, float) -> float
    - getDOF(numpy.ndarray) -> int
    - isRankDeficient(numpy.ndarray) -> bool

Creation: 29/11/2022        
Last revision: 02/09/2023
"""


def tTopvalue(t: float, df: int) -> float:
    """
    Get p-value from t-value.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom

    Returns
    -------
    float
        p-value
    """
    # Validated
    if t == 0.0:
        p = 1.0
    else:
        # noinspection PyUnresolvedReferences
        p = 1.0 - student.cdf(t, df)
        if p == 0.0: p = finfo(float).eps
    return p


def zTopvalue(z: float) -> float:
    """
    Get p-value from z-value.

    Parameters
    ----------
    z : float
        z-value

    Returns
    -------
    float
        p-value
    """
    # Validated
    if z == 0.0:
        p = 1.0
    else:
        p = 1.0 - norm.cdf(z)
        if p == 0.0: p = finfo(float).eps
    return p


def pvalueTot(p: float, df: int) -> float:
    """
    Get t-value from p-value.

    Parameters
    ----------
    p : float
        p-value
    df : int
        degrees of freedom

    Returns
    -------
    float
        t-value
    """
    # ppf is inv CDF
    # Validated
    t = student.ppf(1.0 - p, df)
    return t


def pvalueToz(p: float) -> float:
    """
    Get z-value from p-value.

    Parameters
    ----------
    p : float
        p-value

    Returns
    -------
    float
        z-value
    """
    # ppf is inv CDF
    # Validated
    z = norm.ppf(1.0 - p)
    return z


def zTot(z: float, df: int) -> float:
    """
    Get z-value from t-value.

    Parameters
    ----------
    z : float
        z-value
    df : int
        degrees of freedom

    Returns
    -------
    float
        t-value
    """
    p = zTopvalue(z)
    t = pvalueTot(p, df)
    return t


def tToz(t: float, df: int) -> float:
    """
    Get t-value from z-value.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom

    Returns
    -------
    float
        z-value
    """
    p = tTopvalue(t, df)
    z = pvalueToz(p)
    return z


def pCorrectedBonferroni(p: float, n: int) -> float:
    """
    Bonferroni multiple-comparison correction.

    Parameters
    ----------
    p : float
        uncorrected p-value
    n : int
        number of comparisons

    Returns
    -------
    float
        corrected p-value
    """
    # Validated
    p = 1.0 - power((1.0 - p), n)
    return p


def pUncorrectedBonferroni(p: float, n: int) -> float:
    """
    Get an uncorrected p-value from a Bonferroni corrected p-value.

    Parameters
    ----------
    p : float
        corrected p-value
    n : int
        number of comparisons

    Returns
    -------
    float
        uncorrected p-value
    """
    # Validated
    p = 1.0 - power((1.0 - p), 1.0 / n)
    return p


def qFDRToz(q: float, img: SisypheVolume, independent: bool = False) -> float:
    """
    Get z-value from a false discovery rate value.

    Reference:
    Controlling the false discovery rate: a practical and powerful approach to multiple testing.
    Benjamini Y, Hochberg Y. Journal of the Royal Statistical Society, Series B. 1995;57(1):289–300.
    doi:10.1111/j.2517-6161.1995.

    Parameters
    ----------
    q : float
        false discovery rate value
    img : Sisyphe.core.sisypheVolume.SisypheVolume
        statistical map
    independent : bool

    Returns
    -------
    float
       z-value
    """
    if isinstance(img, SisypheVolume):
        img = img.getNumpy().flatten()
        n = count_nonzero(img)
        if independent:
            c = 1.0
        else:
            c = log(n) + euler_gamma + 1.0 / (2.0 * n)
        img = sort(img)[::-1]
        for i in range(n):
            # noinspection PyTypeChecker
            p = zTopvalue(img[i])
            r = (i + 1) * q / (n * c)
            if p > r: return float(img[i])
        return float(img[-1])
    else: raise TypeError('Volume parameter type {} is not SisypheVolume.'.format(type(img)))


def qFDRTot(q: float, df: int, img: SisypheVolume, independent: bool = False) -> float:
    """
    Get t-value from a false discovery rate value.

    Reference:
    Controlling the false discovery rate: a practical and powerful approach to multiple testing.
    Benjamini Y, Hochberg Y. Journal of the Royal Statistical Society, Series B. 1995;57(1):289–300.
    doi:10.1111/j.2517-6161.1995.

    Parameters
    ----------
    q : float
        false discovery rate value
    df : int
        degrees of freedom
    img : Sisyphe.core.sisypheVolume.SisypheVolume
        statistical map
    independent : bool

    Returns
    -------
    float
       t-value
    """
    if isinstance(img, SisypheVolume):
        img = img.getNumpy().flatten()
        n = count_nonzero(img)
        if independent:
            c = 1.0
        else:
            c = log(n) + euler_gamma + 1.0 / (2.0 * n)
        img = sort(img)[::-1]
        for i in range(n):
            # noinspection PyTypeChecker
            p = tTopvalue(img[i], df)
            r = (i + 1) * q / (n * c)
            if p > r: return float(img[i])
        return float(img[-1])
    else: raise TypeError('Volume parameter type {} is not SisypheVolume.'.format(type(img)))


def tFieldEulerCharacteristic(t: float, df: int) -> tuple[float, ...]:
    """
    t field Euler characteristic processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom

    Returns
    -------
    tuple[float, ...]
        Euler characteristics
    """
    b1 = 4.0 * log(2)
    b2 = 2.0 * pi
    b3 = power(1.0 + ((t ** 2) / df), -0.5 * (df - 1))
    # noinspection PyUnresolvedReferences
    rho0 = 1.0 - student.cdf(t, df)
    rho1 = (sqrt(b1) / b2) * b3
    rho2 = (b1 / (power(b2, 1.5) * gamma(df / 2.0) * sqrt(df / 2.0))) * b3 * t * gamma((df + 1.0) / 2.0)
    rho3 = (power(b1, 1.5) / (b2 ** 2)) * b3 * ((((df - 1.0) / df) * (t ** 2)) - 1.0)
    return rho0, rho1, rho2, rho3


def zFieldEulerCharacteristic(z: float) -> tuple[float, ...]:
    """
    Gaussian field Euler characteristic processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    z : float
        z-value

    Returns
    -------
    tuple[float, ...]
        Euler characteristics
    """
    b1 = 4.0 * log(2)
    b2 = 2.0 * pi
    b3 = exp(-(z ** 2) / 2.0)
    rho0 = 1.0 - norm.cdf(z)
    rho1 = (sqrt(b1) / b2) * b3
    rho2 = (b1 / power(b2, 1.5)) * b3 * z
    rho3 = (power(b1, 1.5) / (b2 ** 2)) * b3 * ((z ** 2) - 1)
    return rho0, rho1, rho2, rho3


def reselCount(mask: SisypheVolume,
               autocorrx: float,
               autocorry: float,
               autocorrz: float,
               wait: DialogWait | None = None) -> tuple[float, ...]:
    """
    Resel counts processing.
    resel count 0 = Euler characteristic of the statistical map (i.e. gaussian field)
    resel count 1 = resel diameter
    resel count 2 = resel surface area
    resel count 3 = resel volume

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    mask : Sisyphe.core.sisypheVolume.SisypheVolume
        mask of analysis
    autocorrx : float
        statistical map gaussian point spread function, fwhm (mm) in x dimension
    autocorry : float
        statistical map gaussian point spread function, fwhm (mm) in y dimension
    autocorrz : float
        statistical map gaussian point spread function, fwhm (mm) in z dimension
    wait : DialogWait | None
        progress dialog (default None)

    Returns
    -------
    tuple[float, ...]
        resel counts
    """
    if isinstance(mask, SisypheVolume):
        s = mask.getSize()
        sp = mask.getSpacing()
        mask = mask.getNumpy()
        rx = sp[0] / autocorrx
        ry = sp[1] / autocorry
        rz = sp[2] / autocorrz
        lim0 = s[0] - 1
        lim1 = s[1] - 1
        lim2 = s[2] - 1
        p = ex = ey = ez = fxy = fxz = fyz = c = 0
        if wait is not None:
            wait.setInformationText('Compute resel count...')
            wait.progressVisibilityOn()
            wait.setProgressRange(0, s[2] - 1)
        for k in range(s[2]):
            if wait is not None: wait.setCurrentProgressValue(k)
            for j in range(s[1]):
                for i in range(s[0]):
                    if mask[k, j, i] > 0:
                        p += 1
                        if i < lim0:
                            if mask[k, j, i + 1] > 0: ex += 1
                            if j < lim1:
                                if mask[k, j + 1, i + 1] > 0: fxy += 1
                                if k < lim2:
                                    if mask[k + 1, j + 1, i + 1] > 0: c += 1
                            if k < lim2:
                                if mask[k + 1, j, i + 1] > 0: fxz += 1
                        if j < lim1:
                            if mask[k, j + 1, i] > 0: ey += 1
                            if k < lim2:
                                if mask[k + 1, j + 1, i] > 0: fyz += 1
                        if k < lim2:
                            if mask[k + 1, j, i] > 0: ez += 1
        rc0 = p - (ex + ey + ez) + (fxy + fxz + fyz) - c
        rc1 = ((ex - fxy - fxz + c) * rx) + ((ey - fxy - fyz + c) * ry) + ((ez - fxz - fyz + c) * rz)
        rc2 = ((fxy - c) * rx * ry) + ((fxz - c) * rx * rz) + ((fyz - c) * ry * rz)
        rc3 = c * rx * ry * rz
        if wait is not None:
            wait.progressVisibilityOff()
        return rc0, rc1, rc2, rc3
    else: raise TypeError('mask parameter type {} is not SisypheVolume.'.format(type(mask)))


def tFieldExpectedClusters(t: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    t field expected cluster processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        expected clusters
    """
    rho0, rho1, rho2, rho3 = tFieldEulerCharacteristic(t, df)
    return (rho0 * rc0) + (rho1 * rc1) + (rho2 * rc2) + (rho3 * rc3)


def zFieldExpectedClusters(z: float, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    Gaussian field expected cluster processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    z : float
        z-value
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        expected clusters
    """
    rho0, rho1, rho2, rho3 = zFieldEulerCharacteristic(z)
    return (rho0 * rc0) + (rho1 * rc1) + (rho2 * rc2) + (rho3 * rc3)


def tFieldExpectedVoxels(t: float, df: int, n: int) -> float:
    """
    t field expected voxel processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom
    n : int
        number of voxels in analysis mask

    Returns
    -------
    float
        expected voxels
    """
    return n * tTopvalue(t, df)


def zFieldExpectedVoxels(z: float, n: int) -> float:
    """
    Gaussian field expected voxel processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    z : float
        z-value
    n : int
        number of voxels in analysis mask

    Returns
    -------
    float
        expected voxels
    """
    return n * zTopvalue(z)


def expectedVoxelsPerCluster(ev: float, ec: float) -> float:
    """
    Expected voxels per cluster processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    ev : float
        expected number of voxels
    ec : float
        expected number of clusters

    Returns
    -------
    float
        expected voxels per cluster
    """
    return ev / ec


def extentToClusterUncorrectedpvalue(k: int, ev: float, ec: float) -> float:
    """
    Cluster uncorrected p-value processing from extent (number of voxels).

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    k : int
        extent, number of voxels
    ev : float
        expected number of voxels
    ec : float
        expected number of clusters

    Returns
    -------
    float
        cluster uncorrected p-value
    """
    c = 2.0 / 3.0
    beta = power(gamma(2.5) * (ec / ev), c)
    return exp(-beta * power(k, c))


def extentToClusterCorrectedpvalue(k: int, ev: float, ec: float) -> float:
    """
    Cluster corrected p-value processing from extent (number of voxels).

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    k : int
        extent, number of voxels
    ev : float
        expected number of voxels
    ec : float
        expected number of clusters

    Returns
    -------
    float
        cluster corrected p-value
    """
    puc = extentToClusterUncorrectedpvalue(k, ev, ec)
    # noinspection PyTypeChecker
    return 1 - exp(-(ec + finfo(float).eps) * puc)


def clusterUncorrectedpvalueToExtent(p: float, ev: float, ec: float) -> int:
    """
    Extent processing from cluster uncorrected p-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    p : float
        cluster uncorrected p-value
    ev : float
        expected number of voxels
    ec : float
        expected number of clusters

    Returns
    -------
    int
        extent (number of voxels)
    """
    beta = power(gamma(2.5) * (ec / ev), 2.0 / 3.0)
    return int((power(-log(p) / beta, 3.0 / 2.0)))


def clusterCorrectedpvalueToExtent(p: float, ev: float, ec: float) -> int:
    """
    Extent processing from cluster corrected p-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    p : float
        cluster uncorrected p-value
    ev : float
        expected number of voxels
    ec : float
        expected number of clusters

    Returns
    -------
    int
        extent (number of voxels)
    """
    beta = power(gamma(2.5) * (ec / ev), 2.0 / 3.0)
    return int(power(log(-ec / log(1 - p)) / beta, 3.0 / 2.0))


def voxelCorrectedpvalue(ev: float) -> float:
    """
    Voxel corrected p-value processing.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    ev : float
        expected number of voxels

    Returns
    -------
    float
        voxel corrected p-value
    """
    return 1 - exp(-ev)


def tToVoxelCorrectedpvalue(t: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    Voxel corrected p-value processing from t-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    t : float
        t-value
    df : int
        degrees of freedom
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        t-value
    """
    p = tFieldExpectedClusters(t, df, rc0, rc1, rc2, rc3)
    return 1.0 - exp(-p)


def zToVoxelCorrectedpvalue(z: float, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    Voxel corrected p-value processing from z-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    z : float
        z-value
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        z-value
    """
    p = zFieldExpectedClusters(z, rc0, rc1, rc2, rc3)
    return 1.0 - exp(-p)


def voxelCorrectedpvalueTot(u: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    t-value processing from voxel corrected p-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    u : float
        voxel corrected p-value
    df : int
        degrees of freedom
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        t-value
    """
    dt = 1e-6
    # Initial approximation
    vt = pvalueTot(u, df)
    # Iterative approximation with ec
    d = 1
    while abs(d) > dt:
        p = tFieldExpectedClusters(vt, df, rc0, rc1, rc2, rc3)
        q = tFieldExpectedClusters(vt + dt, df, rc0, rc1, rc2, rc3)
        d = (u - p) / ((q - p) / dt)
        vt += d
    # Iterative approximation with 1 - exp(-ec)
    d = 1
    while abs(d) > dt:
        p = tToVoxelCorrectedpvalue(vt, df, rc0, rc1, rc2, rc3)
        q = tToVoxelCorrectedpvalue(vt + dt, df, rc0, rc1, rc2, rc3)
        d = (u - p) / ((q - p) / dt)
        vt = vt + d
    return vt


def voxelCorrectedpvalueToz(u: float, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    """
    z-value processing from voxel corrected p-value.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Parameters
    ----------
    u : float
        voxel corrected p-value
    rc0 : float
        resel count 0, t-field Euler characteristic
    rc1 : float
        resel count 1, t-field resel diameter
    rc2 : float
        resel count 2, t-field resel surface area
    rc3 : float
        resel count 3, t-field resel volume

    Returns
    -------
    float
        z-value
    """
    dt = 1e-6
    # Initial approximation
    vt = pvalueToz(u)
    # Iterative approximation with ec
    d = 1
    while abs(d) > dt:
        p = zFieldExpectedClusters(vt, rc0, rc1, rc2, rc3)
        q = zFieldExpectedClusters(vt + dt, rc0, rc1, rc2, rc3)
        d = (u - p) / ((q - p) / dt)
        vt += d
    # Iterative approximation with 1 - exp(-ec)
    d = 1
    while abs(d) > dt:
        p = zToVoxelCorrectedpvalue(vt, rc0, rc1, rc2, rc3)
        q = zToVoxelCorrectedpvalue(vt + dt, rc0, rc1, rc2, rc3)
        d = (u - p) / ((q - p) / dt)
        vt = vt + d
    return vt


def getDOF(design: ndarray) -> int:
    """
    Get the degrees of freedom of a design matrix.

    Parameters
    ----------
    design : ndarray
        design matrix (lines = observations, columns = factors)

    Returns
    -------
    int
        The degrees of freedom
    """
    if isinstance(design, ndarray):
        # < Revision 05/12/2024
        # return design.shape[0] - matrix_rank(design)
        return int(design.shape[0] - matrix_rank(design))
        # Revision 05/12/2024 >
    else: raise TypeError('matrix parameter type {} is not numpy.ndarray.'.format(type(design)))


def isRankDeficient(X: ndarray) -> bool:
    """
    Check whether a design matrix is rank-deficient.

    Parameters
    ----------
    X : ndarray
        design matrix (lines = observations, columns = factors)

    Returns
    -------
    bool
        True if rank-deficient
    """
    if isinstance(X, ndarray):
        n = min(X.shape[0], X.shape[1])
        return matrix_rank(X) < n
    else:
        raise TypeError('parameter type {} is not numpy.ndarray.'.format(type(X)))


"""
fMRI functions
~~~~~~~~~~~~~~

    - getHRF(float, float, float, float, float, float, float) -> numpy.ndarray
    - getBoxCarModel(int, int, int, int) -> numpy.ndarray
    - convolveModelHRF(numpy.ndarray, float) -> numpy.ndarray
    - getHighPass() -> numpy.ndarray

Creation: 29/11/2022   
Last revision: 02/09/2023
"""


def getHRF(pdelay: float = 6.0,
           ndelay: float = 16.0,
           pspread: float = 1.0,
           nspread: float = 1.0,
           ratio: float = 6.0,
           dt: float = 0.1,
           iscan: float = 2.0) -> ndarray:
    """
    Hemodynamic response function.
    Vector used to convolve fMRI boxcar model.

    Reference:
    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Parameters
    ----------
    pdelay : float
        delay in s of positive response (default 6 s)
    ndelay : float
        delay in s of negative response (default 16 s)
    pspread : float
        spread in s of positive response (default 1 s)
    nspread : float
        spread in s of negative response (default 1 s)
    ratio : float
        ratio of positive to negative responses (default 6)
    dt : float
        sampling (default 0.1 seconds)
    iscan : float
        interscan interval (TR in seconds)

    Returns
    -------
    numpy.ndarray
        Hemodynamic response function
    """
    nb = int(16 / dt)  # 16 s
    buff = zeros([nb, ])
    # noinspection PyUnresolvedReferences
    i: cython.int
    for i in range(nb):
        j = i * dt * 2
        buff[i] = (gamma2.pdf(j, pdelay / pspread) - (gamma2.pdf(j, ndelay / nspread) / ratio))
    if iscan > 0:
        s = int(iscan / dt)
        nb = int(16 / iscan)
        hrf = zeros([nb, ])
        for i in range(nb):
            hrf[i] = buff[i * s]
    else:
        hrf = buff
    s = hrf.sum()
    hrf = hrf / s
    return hrf


def getBoxCarModel(first: int,
                   nactive: int,
                   nrest: int,
                   nblocks: int) -> ndarray:
    """
    fMRI boxcar model.

    Reference:
    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Parameters
    ----------
    first : int
        index of the first scan activity condition
    nactive : int
        number of scans in activation blocks
    nrest : int
        number of scans in rest blocks
    nblocks : int
        number of blocks (1 block = 1 active block + 1 rest block)

    Returns
    -------
    numpy.ndarray
        fMRI boxcar model
    """
    bstart = [0] * first
    bactive = [1] * nactive
    brest = [0] * nrest
    b = bactive + brest
    run = bstart + b * nblocks
    return array(run)


def convolveModelHRF(model: ndarray, iscan: float) -> ndarray:
    """
    Convolve the boxcar model with the Hemodynamic Response Function (HRF).

    Parameters
    ----------
    model : numpy.ndarray
        fMRI boxcar model
    iscan : float
        interscan interval (TR in seconds)

    Returns
    -------
    numpy.ndarray
        convolved boxcar model
    """
    hrf = getHRF(iscan=iscan)
    model2 = convolve(model, hrf)
    model2 = model2[:len(model)]
    return model2


def getHighPass(nscans: int, nblocks: int) -> ndarray:
    """
    High-pass vector processing.
    These vectors are added to fMRI design matrix as covariable of non-interest.

    Reference:
    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Parameters
    ----------
    nscans : int
        image count
    nblocks : int
        block count (1 block = 1 active block + 1 rest block) = order

    Returns
    -------
    numpy.ndarray
        High-pass vectors
    """
    hpass = zeros([nscans, nblocks])
    # noinspection PyUnresolvedReferences
    i: cython.int
    # noinspection PyUnresolvedReferences
    j: cython.int
    for i in range(nblocks):  # cols
        for j in range(nscans):  # rows
            hpass[j, i] = cos((i + 1) * pi * (j / (nscans - 1)))
    return hpass


def residualsCovarianceMatrix(res: ndarray) -> ndarray:
    """
    AR(1) method to estimate of the residuals covariance matrix.
    It computes only a single parameter, the lag-1 the “lag 1” autocorrelation (correlation between the data
    at timepoints i and i + 1)

    Parameters
    ----------
    res
        residuals matrix

    Returns
    -------
    ndarray
        residuals covariance matrix
    """
    res1 = insert(res[1:], 0, 0)
    phi = corrcoef(res, res1)[0, 1]
    return phi ** toeplitz(arange(res.size))


"""
Maps functions
~~~~~~~~~~~~~~

    - tTozmap(SisypheVolume) -> SisypheVolume
    - conjunctionFisher(list of SisypheVolume) -> SisypheVolume
    - conjunctionWorsley(list of SisypheVolume) -> SisypheVolume
    - conjunctionStouffer(list of SisypheVolume) -> SisypheVolume
    - conjunctionMudholkar(list of SisypheVolume) -> SisypheVolume
    - conjunctionTippett(list of SisypheVolume) -> SisypheVolume
    - autocorrelationsEstimate(ndarray, ndarray, SisypheVolume) -> tuple[float, float, float]
    - modelEstimate(list of SisypheVolume, SisypheVolume, ndarray) tuple[ndarray, ndarray, ndarray, ndarray]
    - tmapContrastEstimate(ndarray, ndarray, SisypheVolume, SisypheVolume, float, DialogWait | none) -> SisypheVolume
    - zmapContrastEstimate(ndarray, ndarray, SisypheVolume, SisypheVolume, float, DialogWait | None) -> SisypheVolume
    - thresholdMap(SisypheVolume, float, int) -> dict

Creation: 29/11/2022
Last revision: 06/12/2024
"""


def tTozmap(tmap: SisypheVolume) -> SisypheVolume:
    """
    t to z-map conversion

    Parameters
    ----------
    tmap: Sisyphe.core.sisypheVolume.SisypheVolume

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        z-map
    """
    if isinstance(tmap, SisypheVolume):
        if tmap.acquisition.isTMap():
            df = tmap.acquisition.getDegreesOfFreedom()
            zmap = tmap.copy()
            zmap.acquisition.setSequenceToZMap()
            zmap.acquisition.setDegreesOfFreedom(0)
            np = zmap.getNumpy().flatten()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(np)):
                if np[i] > 0.0:
                    # noinspection PyTypeChecker
                    p = tTopvalue(np[i], df)
                    np[i] = pvalueToz(p)
            return zmap
        else: raise AttributeError('Volume sequence {} is not t-map.'.format(tmap.acquisition.getSequence()))
    else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(tmap)))


def conjunctionFisher(maps: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Fisher's method to combine t-maps (t-maps conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002 Jun;16(2):538-50.
    doi: 10.1006/nimg.2002.1107.

    Parameters
    ----------
    maps : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        combined t-map
    """
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i])
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    mask = zeros(shape=maps[0].getNumpy().flatten().shape)
    for m in maps:
        npmap = m.getNumpy().flatten()
        mask += npmap
        npmaps.append(npmap)
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                # Fisher = -2 * sum(log(Pi))
                s = 0
                for npmap in npmaps:
                    s += log(1.0 - norm.cdf(npmap[i]))
                s *= -2.0
                p = 1.0 - chi2.cdf(s, 2 * n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                # Fisher = -2 * sum(log(Pi))
                s = 0
                for npmap in npmaps:
                    s += log(1.0 - student.cdf(npmap[i], df[i]))
                s *= -2.0
                p = 1.0 - chi2.cdf(s, 2 * n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # numpy conj map to SisypheVolume
    conj = conj.reshape(maps[0].getNumpy().shape)
    rmap = SisypheVolume()
    rmap.copyFromNumpyArray(conj,
                            spacing=maps[0].getSpacing(),
                            origin=maps[0].getOrigin(),
                            direction=maps[0].getDirection())
    rmap.copyAttributesFrom(maps[0])
    rmap.acquisition.setSequenceToZMap()
    rmap.acquisition.setDegreesOfFreedom(0)
    return rmap


def conjunctionWorsley(maps: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Worsley's method to combine t-maps (t-maps conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002;Jun;16(2):538-50.
    doi: 10.1006/nimg.2002.1107.

    Parameters
    ----------
    maps : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        combined t-map
    """
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    mask = zeros(shape=maps[0].getNumpy().flatten().shape)
    for m in maps:
        npmap = m.getNumpy().flatten()
        mask += npmap
        npmaps.append(npmap)
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - norm.cdf(npmap[i])
                    if b > s: s = b  # search max pvalue
                p = power(s, n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - student.cdf(npmap[i], df[i])
                    if b > s: s = b  # search max pvalue
                p = power(s, n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # numpy conj map to SisypheVolume
    conj = conj.reshape(maps[0].getNumpy().shape)
    rmap = SisypheVolume()
    rmap.copyFromNumpyArray(conj,
                            spacing=maps[0].getSpacing(),
                            origin=maps[0].getOrigin(),
                            direction=maps[0].getDirection())
    rmap.copyAttributesFrom(maps[0])
    rmap.acquisition.setSequenceToZMap()
    rmap.acquisition.setDegreesOfFreedom(0)
    return rmap


def conjunctionStouffer(maps: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Stouffer's method to combine t-maps (t-maps conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002;Jun;16(2):538-50.
    doi: 10.1006/nimg.2002.1107.

    Parameters
    ----------
    maps : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        combined t-map
    """
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    mask = zeros(shape=maps[0].getNumpy().flatten().shape)
    for m in maps:
        npmap = m.getNumpy().flatten()
        mask += npmap
        npmaps.append(npmap)
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        # Stouffer = sum(NormalCDFInv(1 - Pi)) / sqrt(n)
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - norm.cdf(npmap[i])
                    s += norm.sf(1.0 - b)
                r = s / sqrt(n)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # Stouffer = sum(NormalCDFInv(1 - Pi)) / sqrt(n)
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - student.cdf(npmap[i], df[i])
                    s += norm.sf(1.0 - b)
                r = s / sqrt(n)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # numpy conj map to SisypheVolume
    conj = conj.reshape(maps[0].getNumpy().shape)
    rmap = SisypheVolume()
    rmap.copyFromNumpyArray(conj,
                            spacing=maps[0].getSpacing(),
                            origin=maps[0].getOrigin(),
                            direction=maps[0].getDirection())
    rmap.copyAttributesFrom(maps[0])
    rmap.acquisition.setSequenceToZMap()
    rmap.acquisition.setDegreesOfFreedom(0)
    return rmap


def conjunctionMudholkar(maps: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Mudholkar's method to combine t-maps (t-maps conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002;Jun;16(2):538-50.
    doi: 10.1006/nimg.2002.1107.

    Parameters
    ----------
    maps : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        combined t-map
    """
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    mask = zeros(shape=maps[0].getNumpy().flatten().shape)
    for m in maps:
        npmap = m.getNumpy().flatten()
        mask += npmap
        npmaps.append(npmap)
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    c1 = (5 * n) + 2
    c2 = c1 + 2
    # z maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - norm.cdf(npmap[i])
                    s += log(b / (1.0 - b))
                p = s * -sqrt(3 * c2 / (n * (pi ** 2) * c1))
                p = 1.0 - student.cdf(p, c2)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - norm.cdf(npmap[i])
                    s += log(b / (1.0 - b))
                p = s * -sqrt(3 * c2 / (n * (pi ** 2) * c1))
                p = 1.0 - student.cdf(p, c2)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # numpy conj map to SisypheVolume
    conj = conj.reshape(maps[0].getNumpy().shape)
    rmap = SisypheVolume()
    rmap.copyFromNumpyArray(conj,
                            spacing=maps[0].getSpacing(),
                            origin=maps[0].getOrigin(),
                            direction=maps[0].getDirection())
    rmap.copyAttributesFrom(maps[0])
    rmap.acquisition.setSequenceToZMap()
    rmap.acquisition.setDegreesOfFreedom(0)
    return rmap


def conjunctionTippett(maps: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Tippett's method to combine t-maps (t-maps conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002;Jun;16(2):538-50.
    doi: 10.1006/nimg.2002.1107.

    Parameters
    ----------
    maps : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        combined t-map
    """
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    mask = zeros(shape=maps[0].getNumpy().flatten().shape)
    for m in maps:
        npmap = m.getNumpy().flatten()
        mask += npmap
        npmaps.append(npmap)
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - norm.cdf(npmap[i])
                    if s == 0: s = b
                    if b < s: s = b  # search min pvalue
                p = 1.0 - power(1.0 - s, n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if mask[i] != 0.0:
                s = 0
                for npmap in npmaps:
                    b = 1.0 - student.cdf(npmap[i], df[i])
                    if s == 0: s = b
                    if b < s: s = b  # search min pvalue
                p = 1.0 - power(1.0 - s, n)
                r = norm.sf(1.0 - p)
                if isnan(r) or isinf(r): r = 0.0
                conj[i] = r
            else:
                conj[i] = 0.0
    # numpy conj map to SisypheVolume
    conj = conj.reshape(maps[0].getNumpy().shape)
    rmap = SisypheVolume()
    rmap.copyFromNumpyArray(conj,
                            spacing=maps[0].getSpacing(),
                            origin=maps[0].getOrigin(),
                            direction=maps[0].getDirection())
    rmap.copyAttributesFrom(maps[0])
    rmap.acquisition.setSequenceToZMap()
    rmap.acquisition.setDegreesOfFreedom(0)
    return rmap


def autocorrelationsEstimate(error: ndarray,
                             design: ndarray,
                             mask: SisypheROI | SisypheVolume,
                             wait: DialogWait | None = None) -> tuple[float, float, float]:
    """
    Estimating autocorrelations of residuals.

    Reference:
    Robust smoothness estimation in statistical parametric maps using standardized residuals from the general
    linear model. SJ Kiebel, JB Poline, KJ Friston, AP Holmes, KJ Worsley. Neuroimage 1999 Dec;10(6):756-66.
    doi: 10.1006/nimg.1999.0508.

    Parameters
    ----------
    error : numpy.ndarray
        residuals vector / standard deviation of residuals
    design : numpy.ndarray
        design matrix X
    mask : sisyphe.core.sisypheROI.SisypheROI | sisyphe.core.sisypheVolume.SisypheVolume
        statistical analysis mask
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar

    Returns
    -------
    tuple[float, float, float]
        autocorrelations x, y, z (fwhm in mm)
    """
    buffx = buffy = buffz = 0.0
    vx, vy, vz = mask.getSpacing()
    sx, sy, sz = mask.getSize()
    # < Revision 06/06/2025
    # bug fix, indexing of flattened numpy array
    # error and npmask shape order (x, y, z)
    # numpy is in c-order, last-index varies the fastest
    # after flatten conversion :
    # flatten array index - 1 -> non flatten array z - 1
    # flatten array index - sizez -> non flatten array y - 1
    # flatten array index - (sizey * sizez) -> non flatten array x - 1
    """
    slc = sx * sy
    """
    slc = sy * sz
    # Revision 06/06/2025 >
    npmask = mask.getNumpy(defaultshape=False).flatten()
    nb = len(npmask)
    if wait is not None:
        wait.setInformationText('Estimation of spatial autocorrelations...')
        wait.setProgressRange(0, nb)
        wait.progressVisibilityOn()
    nbv = 0
    # noinspection PyUnresolvedReferences
    i: cython.int
    # noinspection PyUnresolvedReferences
    c: cython.int = 0
    for i in range(slc, nb):
        if wait is not None:
            c += 1
            if c == 100:
                wait.setCurrentProgressValue(i + 1)
                c = 0
        # < Revision 06/06/2025
        # bug fix, indexing of flattened numpy array
        # error and npmask shape order (x, y, z)
        # numpy is in c-order, last-index varies the fastest
        # after flatten conversion :
        # flatten array index - 1 -> non flatten array z - 1
        # flatten array index - sizez -> non flatten array y - 1
        # flatten array index - (sizey * sizez) -> non flatten array x - 1
        """
        if npmask[i] > 0 and npmask[i - 1] > 0 and npmask[i - sx] > 0 and npmask[i - slc] > 0:
            verrorx = error[i, :] - error[i - 1, :]
            verrory = error[i, :] - error[i - sx, :]
            verrorz = error[i, :] - error[i - slc, :]
            verrorx = (verrorx / vx) ** 2
            verrory = (verrory / vy) ** 2
            verrorz = (verrorz / vz) ** 2
            buffx += verrorx.sum()
            buffy += verrory.sum()
            buffz += verrorz.sum()
            nbv += 1
        """
        if npmask[i] > 0 and npmask[i - 1] > 0 and npmask[i - sz] > 0 and npmask[i - slc] > 0:
            verrorz = error[i, :] - error[i - 1, :]
            verrory = error[i, :] - error[i - sz, :]
            verrorx = error[i, :] - error[i - slc, :]
            verrorx = (verrorx / vx) ** 2
            verrory = (verrory / vy) ** 2
            verrorz = (verrorz / vz) ** 2
            buffx += verrorx.sum()
            buffy += verrory.sum()
            buffz += verrorz.sum()
            nbv += 1
        # Revision 06/06/2025 >
    df = getDOF(design)
    f1 = (df - 2) / ((df - 1) * nbv)
    f2 = 4.0 * log(2.0)
    autocorrx = sqrt(f2 / (buffx * f1))
    autocorry = sqrt(f2 / (buffy * f1))
    autocorrz = sqrt(f2 / (buffz * f1))
    return autocorrx, autocorry, autocorrz


def modelEstimate(obs: list[SisypheVolume],
                  design: ndarray,
                  mask: SisypheROI | SisypheVolume,
                  scale: ndarray | None = None,
                  wait: DialogWait | None = None) -> tuple[SisypheVolume, SisypheVolume, SisypheVolume, ndarray]:
    """
    Model estimation.

    Design matrix X (lines = observations, columns = factors):
    beta = pinv(X) Y = (XtX)-1 Xt Y
    residuals i.e. model errors = Y - X beta
    pooled variance = variance(residuals)

    Reference:
    Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley,
    JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210.
    doi: 10.1002/hbm.460020402.

    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Parameters
    ----------
    obs : list[sisyphe.core.sisypheVolume.SisypheVolume]
    mask : sisyphe.core.sisypheROI.SisypheROI | sisyphe.core.sisypheVolume.SisypheVolume
        analysis mask
    design : numpy.ndarray
        design matrix X
    scale : numpy.ndarray
        signal normalization values
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar

    Returns
    -------
    tuple[sisyphe.core.sisypheVolume.SisypheVolume,sisyphe.core.sisypheVolume.SisypheVolume, sisyphe.core.sisypheVolume.SisypheVolume, ndarray]
        beta, pooled variance, residuals, autocorrelations
    """
    n = len(obs)
    if design.shape[0] == n:
        """
        ndarray conversion
        
        npobs, ndarray, matrix of observations, shape=(l, c)
            - l, lines, number of observations (number of volumes)
            - c, columns, number of voxels in observation volume (i.e. vector images)
        npmask, ndarray, analysis mask, shape(l, 1)
        """
        # < Revision 06/12/2024
        # lobs = list()
        # for o in obs:
        #    lobs.append(o.getNumpy().flatten())
        # npobs = stack(lobs)
        vobs = multiComponentSisypheVolumeFromList(obs)
        # npobs = vobs.getNumpy()
        # npmask = mask.getNumpy().flatten()
        npobs = vobs.getNumpy(defaultshape=False)
        npmask = mask.getNumpy(defaultshape=False).flatten()
        # Revision 06/12/2024 >
        """
        ndarray results
        
        beta, ndarray, shape(l, c)
        error, residuals, ndarray, shape(l, c)
        nerror, normalized residuals, ndarray, shape(l, c)
        variance, residuals variance, ndarray, shape(l, 1)
            - l, lines = number of voxels in observation volume
            - c, columns = factors
        """
        nb = len(npmask)
        npobs = npobs.reshape((nb, n))
        beta = zeros([nb, design.shape[1]])
        # < Revision 03/12/2024
        # error = zeros([nb, design.shape[1]])
        # nerror = zeros([nb, design.shape[1]])
        error = zeros([nb, n])
        nerror = zeros([nb, n])
        # Revision 03/12/2024 >
        variance = zeros([nb, ])
        idesign = pinv(design)
        # noinspection PyUnresolvedReferences
        i: cython.int
        # noinspection PyUnresolvedReferences
        c: cython.int = 0
        # Main loop
        if wait is not None:
            wait.setInformationText('Model estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        for i in range(nb):
            if wait is not None:
                c += 1
                if c == 100:
                    wait.setCurrentProgressValue(i + 1)
                    c = 0
            if npmask[i] > 0:
                # Proportional scaling if scale is not None
                # Y vector (vobs) of observations at current voxel i
                if scale is not None: vobs = npobs[i, :] * scale
                else: vobs = npobs[i, :]
                # beta = pinv(X) Y
                vbeta = idesign @ vobs
                beta[i, :] = vbeta
                # Y' = X beta
                vobsm = design @ vbeta
                # errors, residuals E = Y - Y'
                res = vobs - vobsm
                error[i, :] = res
                # Variance = sum of squared errors
                res2 = res ** 2
                variance[i] = res2.sum()
                # Normalized error E / std (i.e. sqrt(Variance))
                nerror[i, :] = res / sqrt(variance[i])
        autocorr = array(autocorrelationsEstimate(nerror, design, mask, wait))
        # < Revision 06/12/2024
        # SisypheVolume conversion
        dof = int(getDOF(design))
        size = obs[0].getSize()
        spacing = obs[0].getSpacing()
        # beta volume
        beta = beta.reshape((size[0], size[1], size[2], design.shape[1]))
        vbeta = SisypheVolume()
        vbeta.copyFromNumpyArray(beta, spacing=spacing, defaultshape=False)
        vbeta.copyAttributesFrom(obs[0], display=False)
        vbeta.acquisition.setDegreesOfFreedom(dof)
        vbeta.acquisition.setAutoCorrelations(autocorr)
        vbeta.acquisition.setModalityToOT()
        vbeta.acquisition.setSequence('Beta')
        # variance volume
        variance = variance.reshape((size[0], size[1], size[2]))
        vvariance = SisypheVolume()
        vvariance.copyFromNumpyArray(variance, spacing=spacing, defaultshape=False)
        vvariance.copyAttributesFrom(obs[0], display=False)
        vvariance.acquisition.setDegreesOfFreedom(dof)
        vvariance.acquisition.setAutoCorrelations(autocorr)
        vvariance.acquisition.setModalityToOT()
        vvariance.acquisition.setSequence('Pooled variance')
        # error volume
        error = error.reshape((size[0], size[1], size[2], n))
        verror = SisypheVolume()
        verror.copyFromNumpyArray(error, spacing=spacing, defaultshape=False)
        verror.copyAttributesFrom(obs[0], display=False)
        verror.acquisition.setDegreesOfFreedom(dof)
        verror.acquisition.setAutoCorrelations(autocorr)
        verror.acquisition.setModalityToOT()
        verror.acquisition.setSequence('Residuals')
        # Revision 06/12/2024 >
        if wait is not None: wait.progressVisibilityOff()
        return vbeta, vvariance, verror, autocorr
    else:
        raise ValueError('Row count {} of the design matrix does not match the '
                         'observation count {}.'.format(design.shape[0], n))


def tmapContrastEstimate(contrast: ndarray,
                         design: ndarray,
                         beta: SisypheVolume,
                         variance: SisypheVolume,
                         df: int,
                         wait: DialogWait | None = None) -> SisypheVolume:
    """
    t-test contrast estimation.

    Reference:
    Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley,
    JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210.
    doi: 10.1002/hbm.460020402.

    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Parameters
    ----------
    contrast : numpy.ndarray
        contrast vector
    design : numpy.ndarray
        design matrix
    beta : Sisyphe.core.sisypheVolume.SisypheVolume
        beta
    variance : Sisyphe.core.sisypheVolume.SisypheVolume
        pooled variance
    df : int
        degrees of freedom (DOF)
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        t-map
    """
    if len(contrast) == design.shape[1]:
        vr = variance.getNumpy(defaultshape=False).flatten()
        nb = len(vr)
        beta = beta.getNumpy(defaultshape=False).reshape((nb, len(contrast)))
        # Compute C (XtX)-1 Ct
        designt = design.T  # Xt
        buff = designt @ design  # XtX
        # (XtX)-1
        if isRankDeficient(buff): buff = pinv(buff)  # Rank deficient
        else: buff = inv(buff)  # Full rank
        buff = contrast @ buff
        d = float(buff @ contrast)
        tmap = zeros(nb)
        # noinspection PyUnresolvedReferences
        c: cython.int = 0
        if wait is not None:
            wait.setInformationText('Contrast estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        # t-test main loop
        # s2 pooled variance of current voxel
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if wait is not None:
                c += 1
                if c == 100:
                    wait.setCurrentProgressValue(i + 1)
                    c = 0
            if vr[i] > 0.0:
                s2 = vr[i] / df
                vbeta = beta[i, :]
                n = float(contrast @ vbeta)
                tmap[i] = n / sqrt(s2 * d)
            else: tmap[i] = 0.0
        if wait is not None: wait.progressVisibilityOff()
        tmap = tmap.reshape(variance.getSize())
        r = SisypheVolume()
        r.copyFromNumpyArray(tmap,
                             spacing=variance.getSpacing(),
                             origin=variance.getOrigin(),
                             defaultshape=False)
        r.copyAttributesFrom(variance, display=False)
        r.display.getLUT().setLutToHot()
        r.acquisition.setSequenceToTMap()
        r.acquisition.setDegreesOfFreedom(df)
        r.acquisition.setContrast(contrast)
        r.acquisition.setAutoCorrelations(variance.acquisition.getAutoCorrelations())
        return r
    else:
        raise ValueError('Column count of the design matrix ({}) does not match the number of elements '
                         'in the contrast vector ({}).'.format(design.shape[1], len(contrast)))


def zmapContrastEstimate(contrast: ndarray,
                         design: ndarray,
                         beta: SisypheVolume,
                         variance: SisypheVolume,
                         df: int,
                         wait: DialogWait | None = None) -> SisypheVolume:
    """
    Parameters
    ----------
    contrast : ndarray
        contrast vector
    design : numpy.ndarray
        design matrix
    beta : Sisyphe.core.sisypheVolume.SisypheVolume
        beta
    variance : Sisyphe.core.sisypheVolume.SisypheVolume
        pooled variance
    df : int
        degrees of freedom (DOF)
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog

    Returns
    -------
    Sisyphe.core.sisypheVolume.SisypheVolume
        z-map
    """
    if len(contrast) == design.shape[1]:
        vr = variance.getNumpy(defaultshape=False).flatten()
        nb = len(vr)
        beta = beta.getNumpy(defaultshape=False).reshape((nb, len(contrast)))
        zmap = zeros([nb, ])
        # noinspection PyUnresolvedReferences
        c: cython.int = 0
        if wait is not None:
            wait.setInformationText('Contrast estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        # z test main loop
        # s standard deviation of current voxel
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(nb):
            if wait is not None:
                c += 1
                if c == 100:
                    wait.setCurrentProgressValue(i + 1)
                    c = 0
            if vr[i] > 0:
                s = sqrt(vr[i] / df)
                vbeta = beta[i, :]
                n = float(contrast @ vbeta)
                zmap[i] = n / s
            else: zmap[i] = 0.0
        if wait is not None: wait.progressVisibilityOff()
        zmap = zmap.reshape(variance.getSize())
        r = SisypheVolume()
        r.copyFromNumpyArray(zmap,
                             spacing=variance.getSpacing(),
                             origin=variance.getOrigin(),
                             defaultshape=False)
        r.copyAttributesFrom(variance, display=False)
        r.display.getLUT().setLutToHot()
        r.acquisition.setSequenceToZMap()
        r.acquisition.setDegreesOfFreedom(df)
        r.acquisition.setContrast(contrast)
        r.acquisition.setAutoCorrelations(variance.acquisition.getAutoCorrelations())
        return r
    else:
        raise ValueError('Column count of the design matrix ({}) does not match the number of elements in the '
                         'contrast vector ({}).'.format(design.shape[1], len(contrast)))


def thresholdMap(stat: float, ext: int,
                 smap: SisypheVolume,
                 lbls: list[SisypheVolume] | None = None) -> dict:
    """
    Statistical map thresholding.

    Parameters
    ----------
    stat : float
        statistical threshold, t or z value
    ext : int
        extension threshold, number of voxels
    smap : Sisyphe.core.sisypheVolume.SisypheVolume
        statistical map (tmap or zmap)
    lbls : list[Sisyphe.core.sisypheVolume.SisypheVolume] | None
        label image(s), to process proportion of each label in clusters

    Returns
    -------
    dict
        dict keys:
        - 'map': Sisyphe.core.sisypheVolume.SisypheVolume, thresholded statistical map
        - 'c': list[tuple[float, float, float], ...], voxel coordinates of each cluster local maximum
        - 'max': list[float, ...], statistical value of each cluster local maximum
        - 'extent': list[int, ...], extent i.e. number of voxels of each cluster
        - label image filenames: list[dict[int, float]], dict: key = label index in the label image, value = proportion
        of this label in the current cluster (cluster number = list index)
    """
    if isinstance(smap, SisypheVolume):
        if smap.acquisition.isTMap() or smap.acquisition.isZMap():
            img = smap.getSITKImage()
            mask = (img >= stat)
            f = ConnectedComponentImageFilter()
            label = f.Execute(mask)
            f = RelabelComponentImageFilter()
            f.SortByObjectSizeOn()
            f.SetMinimumObjectSize(ext)
            label = f.Execute(label)
            mask = (label > 0)
            img = img * Cast(mask, img.GetPixelIDValue())
            f = LabelStatisticsImageFilter()
            f.Execute(img, label)
            r = dict()
            r['c'] = list()
            r['max'] = list()
            r['extent'] = list()
            # < Revision 05/06/2025
            # if lbls is not None:
            if lbls is not None and len(lbls) > 0:
            # Revision 05/06/2025 >
                for lbl in lbls:
                    r[lbl.getBasename()] = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            n = f.GetNumberOfLabels()
            if n > 0:
                for i in range(1, n):
                    mask = (label == i)
                    imglbl = img * Cast(mask, img.GetPixelIDValue())
                    npimglbl = GetArrayViewFromImage(imglbl)
                    extent = f.GetCount(i)
                    # < Revision 25/11/2024
                    # bugfix, replace flat index with tuple coordinates array
                    # r['c'].append(argmax(imglbl))
                    r['c'].append(unravel_index(argmax(npimglbl), shape=list(npimglbl.shape))[::-1])
                    # Revision 25/11/2024
                    r['max'].append(f.GetMaximum(i))
                    r['extent'].append(extent)
                    if lbls is not None and len(lbls) > 0:
                        for lbl in lbls:
                            imglbl2 = lbl.getSITKImage() * mask
                            # < Revision 09/06/2025
                            # bug fix, bincount parameter must be a one-dimensional array
                            # npimglbl2 = GetArrayViewFromImage(imglbl2)
                            npimglbl2 = GetArrayViewFromImage(imglbl2).flatten()
                            counts = bincount(npimglbl2)
                            extent2 = counts[1:].sum()
                            # Revision 09/06/2025 >
                            if len(counts) > 0:
                                dlbl = dict()
                                # < Revision 10/06/2025
                                # remove background (label = 0) voxels from ratio
                                # noinspection PyUnresolvedReferences
                                j: cython.int
                                for j in range(1, len(counts)):
                                    if counts[j] > 0:
                                        dlbl[j] = counts[j] / extent2
                                # Revision 10/06/2025 >
                                r[lbl.getBasename()].append(dlbl)
            vol = SisypheVolume()
            vol.setSITKImage(img)
            vol.copyAttributesFrom(smap)
            vol.display.setWindowMin(0.0)
            r['map'] = vol
            return r
        else: raise AttributeError('Volume sequence {} is not statistical map.'.format(smap.acquisition.getSequence()))
    else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(smap)))


"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - object -> SisypheDesign
"""


class SisypheDesign(object):
    """
    SisypheDesign class

    Description
    ~~~~~~~~~~~

    PySisyphe statistical design class.

    Model definition class for voxel by voxel statistical parametric mapping analysis.

    Reference:
    Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley,
    JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210.
    doi: 10.1002/hbm.460020402.

    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53.
    doi: 10.1006/nimg.1995.1007.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDesign

    Creation: 29/11/2023
    Last revision: 10/06/2025
    """
    __slots__ = ['_obs', '_cobs', '_grp', '_sbj', '_cnd', '_design', '_cdesign', '_ancova', '_norm', '_fmri',
                 '_age', '_beta', '_variance', '_vols', '_mean', '_mask', '_autocorr', '_filename']

    # Class constants

    _FILEEXT = '.xmodel'

    # Class method

    @classmethod
    def geFileExt(cls) -> str:
        """
        Get statistical design file extension.

        Returns
        -------
        str
            '.xmodel'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get statistical design filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe statistical model (*.xmodel)'
        """
        return 'PySisyphe statistical model (*{})'.format(cls._FILEEXT)

    @classmethod
    def calcMask(cls, obs: list[SisypheVolume]) -> SisypheVolume:
        """
        Analysis mask processing

        Parameters
        ----------
        obs : list[Sisyphe.core.sisypheVolume.SisypheVolume]
            observations

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            mask
        """
        # < Revision 05/06/2025
        # img = obs[0].getSITKImage() + obs[1].getSITKImage()
        # for i in range(2, len(obs)):
        #     img = img + obs[i].getSITKImage()
        # np = GetArrayViewFromImage(img)
        # s = np.flatten().mean()
        # img = img > s
        # mask = SisypheVolume()
        # mask.setSITKImage(img)
        # Revision 05/06/2025 >
        vols = SisypheVolumeCollection()
        vols.copyFromList(obs)
        v = vols.getMeanVolume()
        return v.getMask(morpho='open', fill='')

    # Special method

    """
    Private attributes

    _obs        dict[tuple[str, str, str], list[str]]
                    - key, tuple[str, str, str] as (group name, subject name, condition name)
                    - value, list[str], observation filenames
    _cobs       dict[tuple[str, str, str], list[int]]
                    - key, tuple[str, str, str] as (group name, subject name, condition name)
                    - value, int, number of observations
    _grp        list[str], group names
    _sbj        list[str], subject names
    _cnd        list[str], condition names
    _design     numpy.ndarray, design matrix X (lines = observations, columns = factor/effects/covariables)
    _cdesign    list[tuple[str, int]]
                str, column name of the design matrix (covariable/effect name) 
                int, estimable
                    - 0 not estimable
                    - 1 estimable, main effect
                    - 2 estimable, global covariable of interest
                    - 3 estimable, covariable by group
                    - 4 estimable, covariable by subject
                    - 5 estimable, covariable by condition  
    _ancova     int, 0 ANCOVA global, 1 by group, 2 by subject, 3 by condition
    _norm       int, 0 no, 1 scaling mean, 2 scaling median, 3 scaling 75th percentile
                     4 scaling roi mean, 5 scaling roi median, 6 scaling roi 75th percentile,
                     7 ancova mean, 8 ancova median, 9 ancova 75th percentile,
                     10 ancova roi mean, 11 ancova roi median, 12 ancova roi 75th percentile
    _age        int, age covariable: 0 no, 1 global, 2 by group, 3 by subject, 4 by condition
    _fmri       bool, fMRI model ?
    _beta       SisypheVolume, beta of the model (defined after estimation)
    _variance   SisypheVolume, pooled variance of the model (defined after estimation)
    _vols       SisypheVolume, observations
    _mean       SisypheVolume, mean volume of observations
    _mask       SisypheVolume, analysis mask
    _autocorr   tuple[float, float, float], auto-correlations (defined after estimation)
    """

    def __init__(self) -> None:
        """
        SisypheDesign instance constructor.
        """
        self._grp = None  # group names
        self._sbj = None  # subject names
        self._cnd = None  # condition names
        self._obs = dict()  # (Key (group, subj, cond), list of filenames)
        self._cobs = dict()  # (Key (group, subj, cond), number of filenames)
        self._cdesign = None  # list[(name: str, estimable: int)] of design matrix columns
        self._design = None  # numpy.ndarray, design matrix
        self._ancova = 0  # 0 ANCOVA global, 1 by group, 2 by subject, 3 by condition
        self._norm = 0  # 0 no, 1 proportional scaling, 2 roi, 3 ancova
        self._age = 0  # Age global covariable: 0 No, 1 global, 2 by group, by subject, by condition
        self._fmri = False  # fMRI model ?
        self._beta = None  # SisypheVolume
        self._variance = None  # SisypheVolume, pooled variance volume
        self._vols = None  # SisypheVolume, observations
        self._mean = None  # SisypheVolume, mean volume of observations
        self._mask = None  # SisypheVolume, mask of analysis volume
        self._autocorr = None  # (float, float, float)
        self._filename = ''

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDesign instance to str
         """
        buff = ''
        if self._fmri: buff += 'fMRI design\n'
        # < Revision 30/11/2024
        # add signal normalization and age covariable
        ns = ['No',
              'Mean scaling',
              'Median scaling',
              '75th perc. scaling',
              'ROI mean scaling',
              'ROI median scaling',
              'ROI 75th perc. scaling',
              'ANCOVA mean',
              'ANCOVA median',
              'ANCOVA 75th perc.',
              'ANCOVA ROI mean',
              'ANCOVA ROI median',
              'ANCOVA ROI 75th perc.']
        cov = ['global',
               'by group',
               'by subject',
               'by condition']
        if self._norm < 7: buff += 'Signal normalization: {}\n'.format(ns[self._norm])
        else: buff += 'Signal normalization: {} {}\n'.format(ns[self._norm], cov[self._ancova])
        if self._age > 0: buff += 'Age covariable {}\n'.format(cov[self._age - 1])
        # Revision 30/11/2024 >
        if self.hasGroup(): buff += 'Groups (n={}): {}\n'.format(len(self._grp), ' '.join(self._grp))
        if self.hasSubject(): buff += 'Subjects (n={}): {}\n'.format(len(self._sbj), ' '.join(self._sbj))
        if self.hasCondition(): buff += 'Conditions (n={}): {}\n'.format(len(self._cnd), ' '.join(self._cnd))
        buff += 'Observations ({} scans):\n'.format(self.getTotalObsCount())
        if self._obs is not None and len(self._obs) > 0:
            for key in self._obs:
                k = ' '.join(key)
                k = k.lstrip(' ')
                k = k.rstrip(' ')
                buff += '  {}:\n'.format(k)
                for filename in self._obs[key]:
                    buff += '    {}\n'.format(basename(filename))
        else: buff += '  Empty\n'
        # < Revision 05/12/2024
        # add factors
        if self._cdesign is not None and len(self._design) > 0:
            buff += 'Factor(s):\n'
            estimable = {0: 'confounding variable, not estimable',
                         1: 'main effect',
                         2: 'global covariable of interest',
                         3: 'covariable of interest by group',
                         4: 'covariable of interest by subject',
                         5: 'covariable of interest by condition'}
            for item in self._cdesign:
                buff += '  {} {}\n'.format(item[0], estimable[item[1]])
        else: buff += '  Empty\n'
        # Revision 05/12/2024 >
        # < Revision 05/12/2024
        # add autocorrelations
        if self._autocorr is not None:
            buff += 'Auto-correlations fwhm: {:.1f} {:.1f} {:.1f} mm\n'.format(self._autocorr[0],
                                                                               self._autocorr[1],
                                                                               self._autocorr[2])
        # Revision 05/12/2024 >
        buff += 'Design matrix:\n'
        if self._design is None: buff += '  Empty'
        else:
            for i in range(self._design.shape[0]):
                l = ''
                for j in range(self._design.shape[1]):
                    l += '{:.1f} '.format(self._design[i, j])
                buff += l + '\n'
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDesign instance representation
        """
        return 'SisypheDesign instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Private methods

    def _makeDesignMatrix(self) -> None:
        if self.hasModel():
            nbobs = self.getTotalObsCount()
            columns = list()
            self._cdesign = list()
            # Model with groups, subjects, conditions
            if self.hasGroup() and self.hasSubject() and self.hasCondition():
                # Add condition columns to design matrix
                t = 0
                for grp in self._grp:
                    for sbj in self._sbj:
                        for cnd in self._cnd:
                            k = (grp, sbj, cnd)
                            if k in self._cobs:
                                c = self._cobs[k][0]
                                column = zeros((nbobs, 1))
                                column[t:t + c] = ones((c, 1))
                                columns.append(column)
                                t += c
                                name = ' '.join(k)
                                # < Revision 05/06/2025
                                # In fmri design, the boxcar column is the main effect, not the condition column
                                # self._cdesign.append((name, 1))
                                if self._fmri: self._cdesign.append((name, 0))
                                else: self._cdesign.append((name, 1))
                                # Revision 05/06/2025 >
                if self._fmri:
                    # Copy dummy columns for boxcar model
                    for i in range(len(columns)):
                        c = columns[i].copy()
                        columns.append(c)
                        name = 'boxcar ' + self._cdesign[i][0]
                        # < Revision 05/06/2025
                        # In fmri design, the boxcar column is the main effect, not the condition column
                        # self._cdesign.append((name, 0))
                        self._cdesign.append((name, 1))
                        # Revision 05/06/2025 >
                # Add subject columns to design matrix
                c = nbobs // len(self._sbj)
                t = 0
                for sbj in self._sbj:
                    column = zeros((nbobs, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append((sbj, 0))
                # Add group columns to design matrix
                t = 0
                for grp in self._grp:
                    c = 0
                    for sbj in self._sbj:
                        for cnd in self._cnd:
                            k = (grp, sbj, cnd)
                            if k in self._cobs: c += self._cobs[k][0]
                    column = zeros((nbobs, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append((grp, 0))
            # model subjects, conditions
            elif not self.hasGroup() and self.hasSubject() and self.hasCondition():
                # Add condition columns to design matrix
                t = 0
                for sbj in self._sbj:
                    for cnd in self._cnd:
                        k = ('', sbj, cnd)
                        if k in self._cobs:
                            c = self._cobs[k][0]
                            column = zeros((nbobs, 1))
                            column[t:t + c] = ones((c, 1))
                            columns.append(column)
                            t += c
                            name = ' '.join(k)
                            # < Revision 05/06/2025
                            # In fmri design, the boxcar column is the main effect, not the condition column
                            # self._cdesign.append((name, 1))
                            if self._fmri: self._cdesign.append((name, 0))
                            else: self._cdesign.append((name, 1))
                            # Revision 05/06/2025 >
                if self._fmri:
                    # Copy dummy columns for boxcar model
                    for i in range(len(columns)):
                        c = columns[i].copy()
                        columns.append(c)
                        name = 'boxcar ' + self._cdesign[i][0]
                        # < Revision 05/06/2025
                        # In fmri design, the boxcar column is the main effect, not the condition column
                        # self._cdesign.append((name, 0))
                        self._cdesign.append((name, 1))
                        # Revision 05/06/2025 >
                # Add subject columns to design matrix
                if len(self._sbj) > 1:
                    c = nbobs // len(self._sbj)
                    t = 0
                    for sbj in self._sbj:
                        column = zeros((nbobs, 1))
                        column[t:t + c] = ones((c, 1))
                        columns.append(column)
                        t += c
                        self._cdesign.append((sbj, 0))
            # Model with conditions
            elif not self.hasGroup() and not self.hasSubject() and self.hasCondition():
                # Add condition columns to design matrix
                t = 0
                for cnd in self._cnd:
                    k = ('', '', cnd)
                    c = self._cobs[k][0]
                    column = zeros((nbobs, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    # < Revision 05/06/2025
                    # In fmri design, the boxcar column is the main effect, not the condition column
                    # self._cdesign.append((name, 1))
                    if self._fmri: self._cdesign.append((cnd, 0))
                    else: self._cdesign.append((cnd, 1))
                    # Revision 05/06/2025 >
                if self._fmri:
                    # Copy dummy columns for boxcar model
                    for i in range(len(columns)):
                        c = columns[i].copy()
                        columns.append(c)
                        name = 'boxcar ' + self._cdesign[i][0]
                        # < Revision 05/06/2025
                        # In fmri design, the boxcar column is the main effect, not the condition column
                        # self._cdesign.append((name, 0))
                        self._cdesign.append((name, 1))
                        # Revision 05/06/2025 >
            # Model with groups, subjects
            elif self.hasGroup() and self.hasSubject() and not self.hasCondition():
                # Add subject columns to design matrix
                t = 0
                for grp in self._grp:
                    for sbj in self._sbj:
                        k = (grp, sbj, '')
                        if k in self._cobs:
                            c = self._cobs[k][0]
                            column = zeros((nbobs, 1))
                            column[t:t + c] = ones((c, 1))
                            columns.append(column)
                            t += c
                            self._cdesign.append((sbj, 1))
                # Add group columns to design matrix
                t = 0
                for grp in self._grp:
                    c = 0
                    for sbj in self._sbj:
                        k = (grp, sbj, '')
                        if k in self._cobs: c += self._cobs[k][0]
                    column = zeros((nbobs, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append((grp, 0))
            # Model with groups
            elif self.hasGroup() and not self.hasSubject() and not self.hasCondition():
                # Add condition columns to design matrix
                t = 0
                for grp in self._grp:
                    k = (grp, '', '')
                    c = self._cobs[k][0]
                    column = zeros((nbobs, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append((grp, 1))
            # One sample t-test model
            elif not self.hasGroup() and not self.hasSubject() and not self.hasCondition():
                column = ones((nbobs, 1))
                columns.append(column)
                self._cdesign.append(('Global', 1))
            self._design = column_stack(columns)
            # Add fMRI columns (box car and high pass)
            if self._fmri:
                for cnd in self._cnd:
                    self.addHRFBoxCarModelToCondition(cnd)
                for cnd in self._cnd:
                    self.addHighPassToCondition(cnd)

    def _signalNormalization(self,
                             obs: list[SisypheVolume],
                             mask: SisypheROI | SisypheVolume,
                             roi: SisypheROI | SisypheVolume,
                             wait: DialogWait | None = None) -> ndarray:
        if self._norm > 0:
            if wait is not None:
                wait.setInformationText('Signal normalization...')
                wait.setProgressRange(0, len(obs))
                wait.progressVisibilityOn()
            ancova = list()
            npmask = mask.getNumpy().flatten()
            if self._norm in (1, 2, 3, 7, 8, 9):
                """
                Proportional scaling signal normalization:
                    1: proportional scaling, obs mean (voxels in mask)
                    2: proportional scaling, obs median (voxels in mask)
                    3: proportional scaling, obs 75th percentile (voxels in mask)
                    7: proportional scaling, obs mean (voxels in ROI & mask)
                    8: proportional scaling, obs median (voxels in ROI & mask)
                    9: proportional scaling, obs 75th percentile (voxels in ROI & mask)
                """
                for img in obs:
                    if wait is not None: wait.incCurrentProgressValue()
                    npimg = img.getNumpy().flatten()
                    if self._norm > 6:
                        nproi = roi.getNumpy().flatten()
                        npmask = nproi * npmask
                    if self._norm in (1, 7): ancova.append(npimg[npmask > 0].mean())
                    elif self._norm in (2, 8): ancova.append(median(npimg[npmask > 0]))
                    elif self._norm in (3, 9): ancova.append(percentile(npimg[npmask > 0], 75))
                    # vector of proportional scaling signal normalization
                ancova = array(ancova)
                ancova = 100 / ancova
            elif self._norm in (4, 5, 6, 10, 11, 12):
                """
                ANCOVA signal normalization:
                    4:  ANCOVA, obs mean (voxels in mask)
                    5:  ANCOVA, obs median (voxels in mask)
                    6:  ANCOVA, obs 75th percentile (voxels in mask)
                    10: ANCOVA, obs mean (voxels in ROI & mask)
                    11: ANCOVA, obs median (voxels in ROI & mask)
                    12: ANCOVA, obs 75th percentile (voxels in ROI & mask)
                """
                for img in obs:
                    if wait is not None: wait.incCurrentProgressValue()
                    npimg = img.getNumpy().flatten()
                    if self._norm > 6:
                        nproi = roi.getNumpy().flatten()
                        npmask = nproi * npmask
                    if self._norm in (4, 10): ancova.append(npimg[npmask > 0].mean())
                    elif self._norm in (5, 11): ancova.append(median(npimg[npmask > 0]))
                    elif self._norm in (6, 12): ancova.append(percentile(npimg[npmask > 0], 75))
                ancova = array(ancova)
            if wait is not None: wait.progressVisibilityOff()
            return ancova
        else: return ones(shape=(len(obs),))

    # Public methods

    def hasFilename(self) -> bool:
        """
        Check whether the filename attribute of the current SisypheDesign instance is defined (i.e. not '')

        Returns
        -------
        bool
            True if the filename attribute is defined, False otherwise
        """
        return self._filename != ''

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current SisypheDesign instance. The file name attribute is used to save
        the current SisypheDesign instance.

        Returns
        -------
        str
            file name
        """
        path, ext = splitext(self._filename)
        self._filename = path + self._FILEEXT
        return self._filename

    def getDirname(self) -> str:
        """
        Get the path name attribute of the current SisypheDesign instance. The file name attribute is used to save the
        current SisypheDesign instance.

        Returns
        -------
        str
            path name (path part of the file name)
        """
        return dirname(self._filename)

    def getBasename(self) -> str:
        """
        Get the base name attribute of the current SisypheDesign instance. The file name attribute is used to save the
        current SisypheDesign instance.

        Returns
        -------
        str
            base name (base part of the file name)
        """
        return basename(self._filename)

    def setFilename(self, filename: str) -> None:
        """
        Set the file name attribute of the current SisypheDesign instance. The file name attribute is used to save the
        current SisypheDesign instance.

        Parameters
        ----------
        filename : str
            file name
        """
        path, ext = splitext(filename)
        filename = path + self._FILEEXT
        self._filename = filename

    def setfMRIDesign(self) -> None:
        """
        Set the design type of the current SisypheDesign instance to fMRI. The current SisypheDesign instance is used
        to process fMRI.
        """
        self._fmri = True

    def isfMRIDesign(self) -> bool:
        """
        Check whether the design type of the current SisypheDesign instance is fMRI.

        Returns
        -------
        bool
            True if fMRI design
        """
        return self._fmri

    def setDictDesign(self, design: dict) -> None:
        """
        Set the observation dictionary of the current SisypheDesign instance.

        Parameters
        ----------
        design : dict
            Dictionary syntax with 3 levels, key tuple(str = effect name, int = tree level)
            3 possible levels: 0=first level (group), 1=second level (subject), 2=third level (condition)
        |
        |   {('Group#1', 0): {
        |       ('Subject#11', 1): {
        |           ('Condition#1', 2): [number of observations]
        |           , ... ,
        |           ('Condition#k', 2): [number of observations]}
        |       , ... ,
        |       ('Subject#1j', 1): {
        |           ('Condition#1', 2): [number of observations]
        |           , ... ,
        |           ('Condition#k', 2): [number of observations]}
        |       }
        |   , ... ,
        |   ('Group#i', 0): {
        |       ('Subject#i1', 1): {
        |           ('Condition#1', 2): [number of observations]
        |           , ... ,
        |           ('Condition#k', 2): [number of observations]}
        |       , ... ,
        |       ('Subject#ij', 1): {
        |           ('Condition#1', 2): [number of observations]
        |           , ... ,
        |           ('Condition#k', 2): [number of observations]}
        |       }
        |   }

            Type of models :

                - i groups (one-sample t-test, two-sample t-test, ANOVA), no subject, no condition
                - i conditions, no group, no subject
                - i subjects, j conditions, no group
                - i groups, j subjects, no condition
                - i groups, j subjects, k conditions
        """
        self._grp = list()
        self._sbj = list()
        self._cnd = list()
        self._obs = dict()
        self._cobs = dict()
        # first level, group or subject or condition
        for k1 in design:
            d1 = design[k1]
            if k1[1] == 0:
                self._grp.append(k1[0])
            elif k1[1] == 1:
                self._sbj.append(k1[0])
            elif k1[1] == 2:
                if k1[0] not in self._cnd: self._cnd.append(k1[0])
            else:
                raise ValueError('Invalid design dict.')
            if isinstance(d1, list):
                if k1[1] == 0:
                    k = (k1[0], '', '')
                elif k1[1] == 1:
                    k = ('', k1[0], '')
                elif k1[1] == 2:
                    k = ('', '', k1[0])
                else:
                    raise ValueError('Invalid design dict.')
                # < Revision 05/06/2025
                # init obs dict
                self._obs[k] = list()
                # Revision 05/06/2025 >
                self._cobs[k] = d1
            # Second level, subject or condition
            elif isinstance(d1, dict):
                for k2 in d1:
                    d2 = d1[k2]
                    if k2[1] == 1:
                        self._sbj.append(k2[0])
                    elif k2[1] == 2:
                        if k2[0] not in self._cnd: self._cnd.append(k2[0])
                    else:
                        raise ValueError('Invalid design dict.')
                    if isinstance(d2, list):
                        if k2[1] == 1:
                            k = (k1[0], k2[0], '')
                        elif k2[1] == 2:
                            k = ('', k1[0], k2[0])
                        else:
                            raise ValueError('Invalid design dict.')
                        # < Revision 05/06/2025
                        # init obs dict
                        self._obs[k] = list()
                        # Revision 05/06/2025 >
                        self._cobs[k] = d2
                    # Third level, condition
                    elif isinstance(d2, dict):
                        for k3 in d2:
                            d3 = d2[k3]
                            if k3[1] == 2:
                                if k3[0] not in self._cnd: self._cnd.append(k3[0])
                            if isinstance(d3, list):
                                if k3[1] == 2:
                                    k = (k1[0], k2[0], k3[0])
                                else:
                                    raise ValueError('Invalid design dict.')
                                # < Revision 05/06/2025
                                # init obs dict
                                self._obs[k] = list()
                                # Revision 05/06/2025 >
                                self._cobs[k] = d3

    def getObservationsDict(self) -> dict[tuple[str, str, str], list[int]]:
        """
        Get the observation dictionary of the current SisypheDesign instance.

        Returns
        -------
            dict[tuple[str, str, str], list[int]]
                Observation dictionary:
                    - tuple[str, str, str] key as (group name, subject name, condition name)
                    - list[int] value, first element (index 0) = number of observations
        """
        return self._cobs

    def hasModel(self) -> bool:
        """
        Check whether the model of the current SisypheDesign instance is defined.

        Returns
        -------
        bool
            True if the model is defined
        """
        return len(self._cobs) > 0

    def hasDesignMatrix(self) -> bool:
        """
        Check whether the design matrix of the current SisypheDesign instance is defined.

        Returns
        -------
        bool
            True if the design matrix is defined
        """
        return self._design is not None

    def hasAllFileObs(self) -> bool:
        """
        Check that there are no missing observation volumes in the model of the current SisypheDesign instance.

        Returns
        -------
        bool
            True if no missing observation volumes
        """
        r = False
        if self.hasModel():
            r = self.getTotalObsCount() == self.getTotalFileObsCount()
        return r

    def isEstimated(self) -> bool:
        """
        Check whether the current SisypheDesign instance is estimated.

        Returns
        -------
        bool
            True if design is estimated
        """
        # < Revision 22/11/2024
        # add self._obs
        return self._beta is not None and \
            self._variance is not None and \
            self._design is not None and \
            self._cdesign is not None
        # Revision 22/11/2024 >

    def getGroupName(self, index: int) -> str:
        """
        Get a group name from the model of the current SisypheDesign instance.

        Parameters
        ----------
        index : int
            group index

        Returns
        -------
        str
            group name
        """
        if isinstance(index, int):
            if 0 <= index < len(self._grp):
                return self._grp[index]
            else:
                raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._grp) - 1))
        else:
            raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getSubjectName(self, index: int) -> str:
        """
        Get a subject name from the model of the current SisypheDesign instance.

        Parameters
        ----------
        index : int
            subject index

        Returns
        -------
        str
            subject name
        """
        if isinstance(index, int):
            if 0 <= index < len(self._sbj):
                return self._sbj[index]
            else:
                raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._sbj) - 1))
        else:
            raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getConditionName(self, index: int) -> str:
        """
        Get a condition name from the model of the current SisypheDesign instance.

        Parameters
        ----------
        index : int
            condition index

        Returns
        -------
        str
            condition name
        """
        if isinstance(index, int):
            if 0 <= index < len(self._cnd):
                return self._cnd[index]
            else:
                raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._cnd) - 1))
        else:
            raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getGroupNames(self) -> list[str]:
        """
        Get names of model groups of the current SisypheDesign instance.

        Returns
        -------
        list[str]
            list of group names
        """
        return self._grp

    def getSubjectNames(self) -> list[str]:
        """
        Get names of model subjects of the model of the current SisypheDesign instance.

        Returns
        -------
        list[str]
            list of subject names
        """
        return self._sbj

    def getConditionNames(self) -> list[str]:
        """
        Get names of model conditions of the model of the current SisypheDesign instance.

        Returns
        -------
        list[str]
            list of condition names
        """
        return self._cnd

    def hasGroup(self) -> bool:
        """
        Check whether the model of the current SisypheDesign instance has group(s).

        Returns
        -------
        bool
            True if the model has group(s)
        """
        return self._grp is not None and len(self._grp) > 0

    def hasSubject(self) -> bool:
        """
        Check whether the model of the current SisypheDesign instance has subject(s).

        Returns
        -------
        bool
            True if the model has subject(s)
        """
        return self._sbj is not None and len(self._sbj) > 0

    def hasCondition(self) -> bool:
        """
        Check whether the model of the current SisypheDesign instance has condition(s).

        Returns
        -------
        bool
            True if the model has condition(s)
        """
        return self._cnd is not None and len(self._cnd) > 0

    def getGroupCount(self) -> int:
        """
        Get the number of groups in the model of the current SisypheDesign instance.

        Returns
        -------
        int
            number of groups
        """
        if self._grp is None:
            return 0
        else:
            return len(self._grp)

    def getSubjectCount(self) -> int:
        """
        Get the number of subjects in the model of the current SisypheDesign instance.

        Returns
        -------
        int
            number of subjects
        """
        if self._sbj is None:
            return 0
        else:
            return len(self._sbj)

    def getConditionCount(self) -> int:
        """
        Get the number of conditions in the model of the current SisypheDesign instance.

        Returns
        -------
        int
            number of conditions
        """
        if self._cnd is None:
            return 0
        else:
            return len(self._cnd)

    def getObsCount(self,
                    group: str | None = None,
                    subj: str | None = None,
                    cond: str | None = None) -> int:
        """
        Get the numer of observations (SisypheVolume) required in a given group/subject/condition of the model of the
        current SisypheDesign instance. Observations are SisypheVolume filenames.

        Parameters
        ----------
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)

        Returns
        -------
        int
            number of observations in a given group/subject/condition of the model
        """
        if group is None: group = ''
        if subj is None: subj = ''
        if cond is None: cond = ''
        return self._cobs[(group, subj, cond)][0]

    def getFileObsCount(self,
                        group: str | None = None,
                        subj: str | None = None,
                        cond: str | None = None) -> int:
        """
        Get the numer of observations (SisypheVolume) in a given group/subject/condition of the model of the current
        SisypheDesign instance.

        Parameters
        ----------
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)

        Returns
        -------
        int
            number of observations in a given group/subject/condition of the model
        """
        if group is None: group = ''
        if subj is None: subj = ''
        if cond is None: cond = ''
        return len(self._obs[(group, subj, cond)])

    def getTotalObsCount(self) -> int:
        """
        Get the number of observations (SisypheVolume) required in the model of the current SisypheDesign instance.

        Returns
        -------
        int
            total number of observations in the model
        """
        c = 0
        for k in self._cobs:
            c += self._cobs[k][0]
        return c

    def getTotalFileObsCount(self) -> int:
        """
        Get the numer of observations (SisypheVolume) in the model of the current SisypheDesign instance.

        Returns
        -------
        int
            total number of observations in the model
        """
        c = 0
        for k in self._obs:
            c += len(self._obs[k])
        return c

    def getEffectInformations(self) -> list[tuple[str, int]]:
        """
        Get the model dictionary of the current SisypheDesign instance.

        Returns
        -------
        list[tuple[str, int]]
            - str, column name of the design matrix (covariable/effect name)
            - int, covariable/effect estimability
                - 0 not estimable
                - 1 estimable, main effect
                - 2 estimable, global covariable of interest
                - 3 estimable, covariable by group
                - 4 estimable, covariable by subject
                - 5 estimable, covariable by condition
        """
        return self._cdesign

    # < Revision 03/12/2024
    # add getFileObsDict method
    def getFileObsDict(self) -> dict[tuple[str, str, str], list[str]]:
        """
        Get all model observations of the current SisypheDesign instance. Observations are SisypheVolume filenames.

        Returns
        -------
        dict[tuple[str, str, str], list[str]]
            - key, tuple[str, str, str] as (group name, subject name, condition name)
            - value, list[str], observation filenames
        """
        return self._obs
    # Revision 03/12/2024 >

    # < Revision 03/12/2024
    # add getFileObsFrom method
    def getFileObsFrom(self,
                       group: str | None = None,
                       subj: str | None = None,
                       cond: str | None = None) -> list[str]:
        """
        Get model observations of the current SisypheDesign instance. Observations are SisypheVolume filenames.

        Parameters
        ----------
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)

        Returns
        -------
        list[str]
            list of SisypheVolume filenames (observations)
        """
        if group is None: group = ''
        if subj is None: subj = ''
        if cond is None: cond = ''
        key = (group, subj, cond)
        if key in self._obs: return self._obs[key]
        else: raise KeyError('Invalid Group/Subject/Condition parameters.')
    # Revision 03/12/2024 >

    def setFileObsTo(self,
                     obs: list[str],
                     group: str | None = None,
                     subj: str | None = None,
                     cond: str | None = None) -> None:
        """
        Set observations to the model of the current SisypheDesign instance. Observations are SisypheVolume filenames.

        Parameters
        ----------
        obs: list[str]
            list of SisypheVolume filenames (observations)
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)
        """
        if self.hasModel():
            if group is None: group = ''
            if subj is None: subj = ''
            if cond is None: cond = ''
            key = (group, subj, cond)
            if key in self._cobs:
                if self._cobs[key][0] == len(obs):
                    self._obs[key] = obs
                else:
                    raise ValueError(
                        'Invalid file count ({} expected, {} provided).'.format(self._cobs[key][0], len(obs)))
            else: raise KeyError('Invalid Group/Subject/Condition parameters.')
        else: raise AttributeError('No model is defined')

    def appendFileObsTo(self,
                        obs: list[str],
                        group: str | None = None,
                        subj: str | None = None,
                        cond: str | None = None) -> None:
        """
        Append observations to the model of the current SisypheDesign instance. Observations are SisypheVolume
        filenames.

        Parameters
        ----------
        obs: list[str]
            list of SisypheVolume filenames (observations)
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)
        """
        if self.hasModel():
            if group is None: group = ''
            if subj is None: subj = ''
            if cond is None: cond = ''
            key = (group, subj, cond)
            if key in self._cobs:
                if self._cobs[key][0] <= len(obs) + len(self._obs[key]):
                    # < Revision 29/11/2024
                    # self._obs[key].append(obs)
                    self._obs[key].extend(obs)
                    # Revision 29/11/2024 >
                else:
                    raise ValueError(
                        'Invalid file count ({} expected, {} provided).'.format(self._cobs[key][0], len(obs)))
            else:
                raise KeyError('Invalid Group/Subject/Condition parameters.')
        else:
            raise AttributeError('No model is defined')

    # < Revision 29/11/2024
    # add clearFileObsFrom method
    def clearFileObsFrom(self,
                         group: str | None = None,
                         subj: str | None = None,
                         cond: str | None = None) -> None:
        """
        clear observations from the model of the current SisypheDesign instance. Observations are SisypheVolume
        filenames.

        Parameters
        ----------
        group : str | None
            group name (default None)
        subj : str | None
            subject name (default None)
        cond : str | None
            condition name (default None)
        """
        if self.hasModel():
            if group is None: group = ''
            if subj is None: subj = ''
            if cond is None: cond = ''
            key = (group, subj, cond)
            if key in self._cobs:
                self._obs[key] = list()
            else:
                raise KeyError('Invalid Group/Subject/Condition parameters.')
        else:
            raise AttributeError('No model is defined')

    # Revision 29/11/2024 >

    def addHRFBoxCarModelToCondition(self, cond: str) -> None:
        """
        Add a BoxCar (with HRF convolution) covariable to the fMRI model of the current SisypheDesign instance.

        Parameters
        ----------
        cond : str
            fMRI condition name
        """
        # cond = condition name (must be in self._cond)
        if self._design is None: self._makeDesignMatrix()
        if self.hasCondition():
            boxcar = None
            # box car vector processing
            for k in self._cobs:
                if k[2] == cond:
                    prdgm = self._cobs[k]
                    """
                    first   int, image index of first active block
                    act     int, image count in active block
                    rst     int, image count in resting block
                    blk     int, block count
                    iscn    float, interscan interval
                    """
                    first = prdgm[1]
                    act = prdgm[2]
                    rst = prdgm[3]
                    blk = prdgm[4]
                    iscn = prdgm[5]
                    boxcar = getBoxCarModel(first, act, rst, blk)
                    boxcar = convolveModelHRF(boxcar, iscn)
                    break
            # add box car vector to design matrix
            if boxcar is not None:
                for i in range(len(self._cdesign)):
                    name = self._cdesign[i][0].split()
                    if len(name) > 1 and name[0] == 'boxcar':
                        # < Revision 05/06/2025
                        # if  and name[-1] == cond:
                        if ' '.join(name[1:]) == cond:
                        # Revision 05/06/2025 >
                            n = int(self._design[:, i].sum())
                            if n == len(boxcar):
                                v = self._design[:, i]
                                idx = int(where(v == 1)[0][0])
                                # < Revision 15/11/2024
                                # vmodel = zeros([n, ])
                                vmodel = zeros([self._design.shape[0], ])
                                # Revision 15/11/2024 >
                                vmodel[idx:idx + n] = boxcar
                                self._design[:, i] = vmodel
                            else: raise ValueError('Design matrix elements {} != observations {}.'.format(len(boxcar), n))
            else: raise ValueError('Invalid condition.')

    def addHighPassToCondition(self, cond: str) -> None:
        """
        Add high pass filter covariables to the fMRI model of the current SisypheDesign instance.

        Parameters
        ----------
        cond : str
            fMRI condition name
        """
        if self._design is None: self._makeDesignMatrix()
        if self.hasCondition():
            hpass = None
            # high pass vector processing
            for k in self._cobs:
                if k[2] == cond:
                    prdgm = self._cobs[k]
                    """
                    nscans  int, image count in condition
                    nblocks int, block count (1 block = 1 active block + 1 rest block) in condition
                    """
                    nscans = prdgm[0]
                    nblocks = prdgm[4]
                    hpass = getHighPass(nscans, nblocks)
            # add high pass vector to design matrix
            if hpass is not None:
                for i in range(len(self._cdesign)):
                    name = self._cdesign[i][0].split()
                    if len(name) > 0 and name[0] != 'boxcar':
                        # < Revision 05/06/2025
                        if ' '.join(name) == cond:
                        # Revision 05/06/2025 >
                            n = int(self._design[:, i].sum())
                            if n == len(hpass):
                                v = self._design[:, i]
                                # < Revision 15/11/2024
                                # n = len(v)
                                n2 = len(v)
                                # Revision 15/11/2024 >
                                idx = int(where(v == 1)[0][0])
                                for k in range(hpass.shape[1]):
                                    # < Revision 15/11/2024
                                    # vhpass = zeros([n, ])
                                    vhpass = zeros([n2, ])
                                    vhpass[idx:idx + n] = hpass[:, k].flatten()
                                    # vhpass = vhpass.reshape(n, 1)
                                    vhpass = vhpass.reshape((n2, 1))
                                    # Revision 15/11/2024 >
                                    self._design = append(self._design, vhpass, axis=1)
                                    cname = '{} {}'.format('highpass#{}'.format(k + 1), self._cdesign[i][0])
                                    self._cdesign.append((cname, 0))
                            else:
                                raise ValueError('High pass elements {} != observations {}.'.format(len(hpass), n))
            else: raise ValueError('Invalid condition.')

    # < Revision 03/12/2024
    # add hasGlobalFactor method
    def hasGlobalFactor(self) -> bool:
        """
        Check if the current SisypheDesign instance has a global factor (column of ones in the design matrix).

        Returns
        -------
        bool
            True if design matrix has a global factor
        """
        if self._design is None: self._makeDesignMatrix()
        return any(all(self._design == 1.0, axis=0))
    # Revision 03/12/2024 >

    # < Revision 10/06/2025
    # add isGlobalFactor method
    def isGlobalFactor(self, col: int) -> bool:
        """
        Check if the design matrix column of the current SisypheDesign instance is a global factor (column of ones in
        the design matrix).

        Parameters
        ----------
        col : int
            design matrix column index

        Returns
        -------
        bool
            True if design matrix column is a global factor
        """
        if self._design is None: self._makeDesignMatrix()
        return all(self._design[:, col] == 1.0, axis=0)
    # Revision 10/06/2025 >

    # < Revision 03/12/2024
    # add getGlobalFactorIndex method
    def getGlobalFactorIndex(self) -> int | None:
        """
        Get the column index of the global factor (column of ones) in the design matrix of the current SisypheDesign
        instance.

        Returns
        -------
        int | None
            column index of the global factor, or None if no global factor in the design matrix
        """
        if self._design is None: self._makeDesignMatrix()
        r = where(all(self._design == 1.0, axis=0) > 0)
        if len(r[0]) > 0: return int(r[0][0])
        else: return None
    # Revision 03/12/2024 >

    def addGlobalCovariable(self,
                            name: str,
                            cov: ndarray,
                            estimable: bool = False,
                            zscore: bool = False,
                            logt: bool = False) -> None:
        """
        Add a global covariable to the model of the current SisypheDesign instance.

        Parameters
        ----------
        name : str
            covariable name
        cov: ndarray
            covariable vector, a value for each model observation
        estimable : bool
            covariable estimability, confound variable if False (default False)
        zscore : bool
            convert covariable values into z-score (i.e. (value - mean) / std, default False)
        logt : bool
            apply log to covariable values (default False)
        """
        # < Revision 05/06/2025
        # no space in name
        if len(name.split()) > 1: name = '_'.join(name.split())
        # Revision 05/06/2025 >
        if self._design is None: self._makeDesignMatrix()
        n = self.getTotalObsCount()
        if len(cov) == n:
            if logt: cov = log(cov)
            if zscore:
                m = cov.mean()
                sd = cov.std()
                cov = (cov - m) / sd
            cov = cov.reshape((n, 1))
            if estimable: estimable = 2
            else: estimable = 0
            self._cdesign.append((name, estimable))
            # < Revision 03/12/2024
            # add covariable column before global factor
            gi = self.getGlobalFactorIndex()
            # no global factor
            if gi is None:
                # add covariable column
                self._design = append(self._design, cov, axis=1)
                # add global factor (last column)
                glb = ones(shape=(n, 1))
                self._design = append(self._design, glb, axis=1)
                self._cdesign.append(('global', 0))
            # global factor already exists
            else:
                # insert covariable column before global factor
                self._design = insert(self._design, [gi], cov, axis=1)
            # Revision 03/12/2024 >

    def addCovariableByGroup(self,
                             name: str,
                             cov: ndarray,
                             estimable: bool = False,
                             zscore: bool = False,
                             logt: bool = False) -> None:
        """
        Add a covariable by group to the model of the current SisypheDesign instance.

        Parameters
        ----------
        name : str
            covariable name
        cov: ndarray
            covariable vector, a value for each model observation
        estimable : bool
            covariable estimability, confound variable if False (default False)
        zscore : bool
            convert covariable values into z-score (i.e. (value - mean) / std, default False)
        logt : bool
            apply log to covariable values (default False)
        """
        # < Revision 05/06/2025
        # no space in name
        if len(name.split()) > 1: name = '_'.join(name.split())
        # Revision 05/06/2025 >
        if self._design is None: self._makeDesignMatrix()
        if self.hasGroup():
            n = self.getTotalObsCount()
            if len(cov) == n:
                if logt: cov = log(cov)
                if zscore:
                    m = cov.mean()
                    sd = cov.std()
                    cov = (cov - m) / sd
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._grp:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape((n, 1))
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        if estimable: estimable = 3
                        else: estimable = 0
                        self._cdesign.append((cname, estimable))
            else:
                raise ValueError(
                    'Number of covariable elements {} and observations {} is not equal'.format(len(cov), n))
        else: raise ValueError('No group in model.')

    def addCovariableBySubject(self,
                               name: str,
                               cov: ndarray,
                               estimable: bool = False,
                               zscore: bool = False,
                               logt: bool = False) -> None:
        """
        Add a covariable by subject to the model of the current SisypheDesign instance.

        Parameters
        ----------
        name : str
            covariable name
        cov: ndarray
            covariable vector, a value for each model observation
        estimable : bool
            covariable estimability, confound variable if False (default False)
        zscore : bool
            convert covariable values into z-score (i.e. (value - mean) / std, default False)
        logt : bool
            apply log to covariable values (default False)
        """
        # < Revision 05/06/2025
        # no space in name
        if len(name.split()) > 1: name = '_'.join(name.split())
        # Revision 05/06/2025 >
        if self._design is None: self._makeDesignMatrix()
        if self.hasSubject():
            n = self.getTotalObsCount()
            if len(cov) == n:
                if logt: cov = log(cov)
                if zscore:
                    m = cov.mean()
                    sd = cov.std()
                    cov = (cov - m) / sd
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._sbj:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape((n, 1))
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        if estimable: estimable = 4
                        else: estimable = 0
                        self._cdesign.append((cname, estimable))
            else:
                raise ValueError(
                    'Number of covariable elements {} and observations {} is not equal'.format(len(cov), n))
        else: raise ValueError('No subject in model.')

    def addCovariableByCondition(self,
                                 name: str,
                                 cov: ndarray,
                                 estimable: bool = False,
                                 zscore: bool = False,
                                 logt: bool = False) -> None:
        """
        Add a covariable by condition to the model of the current SisypheDesign instance.

        Parameters
        ----------
        name : str
            covariable name
        cov: ndarray
            covariable vector, a value for each model observation
        estimable : bool
            covariable estimability, confound variable if False (default False)
        zscore : bool
            convert covariable values into z-score (i.e. (value - mean) / std, default False)
        logt : bool
            apply log to covariable values (default False)
        """
        # < Revision 05/06/2025
        # no space in name
        if len(name.split()) > 1: name = '_'.join(name.split())
        # Revision 05/06/2025 >
        if self._design is None: self._makeDesignMatrix()
        if self.hasCondition():
            n = self.getTotalObsCount()
            if len(cov) == n:
                if logt: cov = log(cov)
                if zscore:
                    m = cov.mean()
                    sd = cov.std()
                    cov = (cov - m) / sd
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._cnd:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape((n, 1))
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        if estimable: estimable = 5
                        else: estimable = 0
                        self._cdesign.append((cname, estimable))
            else:
                ValueError('Number of covariable elements {} and observations {} is not equal'.format(len(cov), n))
        else: raise ValueError('No subject in model.')

    def setNoAgeCovariable(self) -> None:
        """
        Remove age covariable from the model of the current SisypheDesign instance.
        """
        self._age = 0

    def setAgeGlobalCovariable(self) -> None:
        """
        Add age global confound covariable to the model of the current SisypheDesign instance.
        """
        self._age = 1

    def setAgeCovariableByGroup(self) -> None:
        """
        Add age confound covariable by group to the model of the current SisypheDesign instance.
        """
        if self.hasGroup(): self._age = 2
        else: self._age = 1

    def setAgeCovariableBySubject(self) -> None:
        """
        Add age confound covariable by subject to the model of the current SisypheDesign instance.
        """
        if self.hasSubject(): self._age = 3
        else: self._age = 1

    def setAgeCovariableByCondition(self) -> None:
        """
        Add age confound covariable by condition to the model of the current SisypheDesign instance.
        """
        if self.hasSubject(): self._age = 4
        else: self._age = 1

    def getAgeCovariable(self) -> int:
        """
        Get the age covariable attribute code of the current SisypheDesign instance.

        Returns
        -------
            int
                Age covariable attribute code:
                    - 0: no age covariable,
                    - 1: age global covariable,
                    - 2: age covariable by group,
                    - 3: age covariable by subject,
                    - 4: age covariable by condition.
        """
        return self._age

    def getAgeCovariableAsString(self) -> str:
        """
        Get the age covariable attribute of the current SisypheDesign instance as string.

        Returns
        -------
            int
                Age covariable attribute code:
                    - 'no', no age covariable,
                    - 'global', age global covariable,
                    - 'by group', age covariable by group,
                    - 'by subject', age covariable by subject,
                    - 'by condition', age covariable by condition.
        """
        d = {0: 'no', 1: 'global', 2: 'by group', 3: 'by subject', 4: 'by condition'}
        return d[self._age]

    def setSignalNormalization(self, v: int = 0) -> None:
        """
        Set the signal normalization attribute of the current SisypheDesign instance.

        Parameters
        ----------
        v : int
            Signal normalization code:
                - 0: No signal normalization,
                - 1: mean scaling, signal divided by the mean in the analysis mask
                - 2: Median scaling, signal divided by the median in the analysis mask
                - 3: 75th percentile scaling, signal divided by the 75th percentile in the analysis mask
                - 4: ROI mean scaling, signal divided by the mean in a reference ROI
                - 5: ROI median scaling, signal divided by the median in a reference ROI
                - 6: ROI 75th perc. scaling, scaling, signal divided by the 75th percentile in a reference ROI
                - 7: ANCOVA Mean, add covariable of the mean in the analysis mask
                - 8: ANCOVA Median, add covariable of the median in the analysis mask
                - 9: ANCOVA 75th percentile, add covariable of the 75th percentile in the analysis mask
                - 10: ANCOVA ROI mean, add covariable of the mean in a reference ROI
                - 11: ANCOVA ROI median, add covariable of the median in a reference ROI
                - 12: ANCOVA ROI 75th percentile, add covariable of the 75th percentile in a reference ROI
        """
        self._norm = v

    def getSignalNormalization(self) -> int:
        """
        Get the signal normalization attribute of the current SisypheDesign instance.

        Returns
        -------
        int
            Signal normalization code:
                - 0: No signal normalization,
                - 1: Mean scaling, signal divided by the mean in the analysis mask
                - 2: Median scaling, signal divided by the median in the analysis mask
                - 3: 75th percentile scaling, signal divided by the 75th percentile in the analysis mask
                - 4: ROI mean scaling, signal divided by the mean in a reference ROI
                - 5: ROI median scaling, signal divided by the median in a reference ROI
                - 6: ROI 75th perc. scaling, scaling, signal divided by the 75th percentile in a reference ROI
                - 7: ANCOVA Mean, add covariable of the mean in the analysis mask
                - 8: ANCOVA Median, add covariable of the median in the analysis mask
                - 9: ANCOVA 75th percentile, add covariable of the 75th percentile in the analysis mask
                - 10: ANCOVA ROI mean, add covariable of the mean in a reference ROI
                - 11: ANCOVA ROI median, add covariable of the median in a reference ROI
                - 12: ANCOVA ROI 75th percentile, add covariable of the 75th percentile in a reference ROI
        """
        return self._norm

    def getNormalizationAsString(self) -> str:
        """
        Get the signal normalization attribute of the current SisypheDesign instance as string.

        Returns
        -------
        str
            Signal normalization code:
                - 'No' signal normalization,
                - 'Mean scaling', signal divided by the mean in the analysis mask
                - 'Median scaling', signal divided by the median in the analysis mask
                - '75th perc. scaling', signal divided by the 75th percentile in the analysis mask
                - 'ROI mean scaling', signal divided by the mean in a reference ROI
                - 'ROI median scaling', signal divided by the median in a reference ROI
                - 'ROI 75th perc. scaling', scaling, signal divided by the 75th percentile in a reference ROI
                - 'ANCOVA Mean', add covariable of the mean in the analysis mask
                - 'ANCOVA Median', add covariable of the median in the analysis mask
                - 'ANCOVA 75th perc.', add covariable of the 75th percentile in the analysis mask
                - 'ANCOVA ROI mean', add covariable of the mean in a reference ROI
                - 'ANCOVA ROI median', add covariable of the median in a reference ROI
                - 'ANCOVA ROI 75th perc.', add covariable of the 75th percentile in a reference ROI
        """
        d = {0: 'No',
             1: 'Mean scaling',
             2: 'Median scaling',
             3: '75th perc. scaling',
             4: 'ROI mean scaling',
             5: 'ROI median scaling',
             6: 'ROI 75th perc. scaling',
             7: 'ANCOVA mean',
             8: 'ANCOVA median',
             9: 'ANCOVA 75th perc.',
             10: 'ANCOVA ROI mean',
             11: 'ANCOVA ROI median',
             12: 'ANCOVA ROI 75th perc.'}
        return d[self._norm]

    def setSignalGlobalCovariable(self) -> None:
        """
        Set the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance. Global
        covariable, a single column in the design matrix.
        """
        self._ancova = 0

    def setSignalCovariableByGroup(self) -> None:
        """
        Set the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance. Covariable
        by group, one column for each group in the design matrix.
        """
        if self.hasGroup():
            self._ancova = 1
        else:
            self._ancova = 0

    def setSignalCovariableBySubject(self) -> None:
        """
        Set the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance. Covariable
        by subject, one column for each subject in the design matrix.
        """
        if self.hasSubject():
            self._ancova = 2
        else:
            self._ancova = 0

    def setSignalCovariableByCondition(self) -> None:
        """
        Set the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance. Covariable
        by condition, one column for each condition in the design matrix.
        """
        if self.hasCondition():
            self._ancova = 3
        else:
            self._ancova = 0

    def getSignalCovariable(self) -> int:
        """
        Get the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance.

        Returns
        -------
        int
            type of ANCOVA covariable: 0 ANCOVA global, 1 by group, 2 by subject, 3 by condition
        """
        return self._ancova

    def getSignalCovariableAsString(self) -> str:
        """
        Get the type of ANCOVA covariable for signal normalization of the current SisypheDesign instance.

        Returns
        -------
        str
            type of ANCOVA covariable: 'Global', 'by group', 'by subject','by condition'
        """
        d = {0: 'global', 1: 'by group', 2: 'by subject', 3: 'by condition'}
        return d[self._ancova]

    def getDesignMatrix(self, recalc: bool = False) -> ndarray:
        """
        Get the design matrix of the current SisypheDesign instance.

        Returns
        -------
        ndarray
            design matrix X of the statistical model, lines = observations x columns = effects/covariables
        """
        if self._design is None or recalc: self._makeDesignMatrix()
        return self._design

    def estimate(self,
                 mask: SisypheROI | SisypheVolume | None = None,
                 roi: SisypheROI | SisypheVolume | None = None,
                 wait: DialogWait | None = None) -> None:
        """
        Model estimation of the current SisypheDesign instance. beta, pooled variance and autocorrelations are
        processed.

        Y vector of observations, X design matrix
        beta = pinv(X) Y = (XtX)-1 Xt Y
        residuals i.e. model errors = Y - X beta
        pooled variance = variance(residuals)

        Reference:
        Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley,
        JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210.
        doi: 10.1002/hbm.460020402.

        Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
        R Turner. Neuroimage 1995 Mar;2(1):45-53.
        doi: 10.1006/nimg.1995.1007.

        Parameters
        ----------
        mask : Sisyphe.core.SisypheROI.sisypheROI | Sisyphe.core.sisypheVolume.SisypheVolume
            statistical analysis mask
        roi : Sisyphe.core.SisypheROI.sisypheROI | Sisyphe.core.sisypheVolume.SisypheVolume
            mask used for signal normalization
        wait : Sisyphe.gui.dialogWait.DialogWait
            progress dialog
        """
        if self.hasDesignMatrix():
            if self.hasAllFileObs():
                age = list()
                if wait is not None:
                    wait.setInformationText('Open volumes...')
                # Open volumes
                obs = list()
                for key in self._obs:
                    for filename in self._obs[key]:
                        if wait is not None:
                            wait.setInformationText('Open volumes...\n{}'.format(basename(filename)))
                        if exists(filename):
                            v = SisypheVolume()
                            v.load(filename)
                            # < Revision 29/11/2024
                            # bug fix, obs is list[SisypheVolume], not list[str]
                            # obs.append(filename)
                            obs.append(v)
                            # Revision 29/11/2024 >
                            if self._age > 0: age.append(v.identity.getAge())
                        else: raise IOError('No such file {}'.format(filename))
                # Add age factor to the design matrix
                if self._age > 0:
                    age = array(age)
                    if self._age == 2:
                        # Age covariable by group
                        self.addCovariableByGroup('Age', age, False)
                    elif self._age == 3:
                        # Age covariable by subject
                        self.addCovariableBySubject('Age', age, False)
                    elif self._age == 4:
                        # Age covariable by condition
                        self.addCovariableByCondition('Age', age, False)
                    else:
                        # Age global covariable
                        self.addGlobalCovariable('Age', age, False)
                # Analysis mask processing
                if mask is None:
                    if wait is not None: wait.setInformationText('Analysis mask processing...')
                    mask = self.calcMask(obs)
                # < Revision 05/06/2025
                # bugfix if mask is SisypheROI, conversion to SisypheVolume
                elif isinstance(mask, SisypheROI): mask = SisypheVolume(mask.getSITKImage())
                # Revision 05/06/2025 >
                # Signal normalization ANCOVA
                if self._norm > 0:
                    """
                    Signal normalization (self._norm):
                        0: no signal normalization
                        1...3, 7...9: Proportional scaling
                            1: proportional scaling, obs mean (voxels in mask)
                            2: proportional scaling, obs median (voxels in mask)
                            3: proportional scaling, obs 75th percentile (voxels in mask)
                            7: proportional scaling, obs mean (voxels in ROI & mask)
                            8: proportional scaling, obs median (voxels in ROI & mask)
                            9: proportional scaling, obs 75th percentile (voxels in ROI & mask)
                        4...6, 10...12: ANCOVA
                            4:  ANCOVA, obs mean (voxels in mask)
                            5:  ANCOVA, obs median (voxels in mask)
                            6:  ANCOVA, obs 75th percentile (voxels in mask)
                            10: ANCOVA, obs mean (voxels in ROI & mask)
                            11: ANCOVA, obs median (voxels in ROI & mask)
                            12: ANCOVA, obs 75th percentile (voxels in ROI & mask)
                    """
                    if roi is None and self._norm in (7, 8, 9, 10, 11, 12): self._norm -= 6
                    scale = self._signalNormalization(obs, mask, roi, wait=wait)
                    # ANCOVA normalization
                    # Add signal normalization factor to the design matrix
                    if self._norm in (4, 5, 6, 10, 11, 12):
                        if self._ancova == 1: self.addCovariableByGroup('Ancova', scale, False)
                        elif self._ancova == 2: self.addCovariableBySubject('Ancova', scale, False)
                        elif self._ancova == 3: self.addCovariableByCondition('Ancova', scale, False)
                        else: self.addGlobalCovariable('Ancova', scale, False)
                        scale = None
                else: scale = None
                # Model estimation
                self._beta, self._variance, error, self._autocorr = modelEstimate(obs=obs,
                                                                                  design=self._design,
                                                                                  mask=mask,
                                                                                  scale=scale,
                                                                                  wait=wait)
                # < Revision 22/11/2024
                # set observations multicomponent volume,
                # scaled if proportional scaling signal normalization
                vols = SisypheVolumeCollection()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(len(obs)):
                    if scale is None: vols.append(obs[i])
                    else:
                        v = obs[i].cast('float32') * scale[i]
                        vols.append(v)
                self._vols = vols.copyToMultiComponentSisypheVolume()
                self._vols.copyAttributesFrom(obs[0])
                self._vols.acquisition.setModality(obs[0].acquisition.getModality())
                self._vols.acquisition.setSequence(obs[0].acquisition.getSequence())
                # Revision 22/11/2024 >
                # < Revision 24/11/2024
                # set mean volume
                vols = SisypheVolumeCollection()
                vols.setList(obs)
                self._mean = vols.getMeanVolume()
                self._mean.copyAttributesFrom(obs[0], display=False)
                # Revision 24/11/2024 >
                # < Revision 05/12/2024
                # set mask volume
                self._mask = mask
                self._mask.copyAttributesFrom(obs[0], display=False)
                self._mask.acquisition.setSequenceToMask()
                # Revision 05/12/2024 >
            else: raise AttributeError('Missing observation files.')
        else: raise AttributeError('Design matrix is empty.')

    def getBeta(self) -> SisypheVolume | None:
        """
        Get the beta volume of the current SisypheDesign instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            beta
        """
        return self._beta

    def getPooledVariance(self) -> SisypheVolume | None:
        """
        Get the pooled variance volume of the current SisypheDesign instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            pooled variance
        """
        return self._variance

    # < Revision 22/11/2024
    # add getObservations method
    def getObservations(self) -> SisypheVolume | None:
        """
        Get the observations multicomponent volume of the current SisypheDesign instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            observations multicomponent volume
        """
        return self._vols

    # Revision 22/11/2024 >

    # < Revision 24/11/2024
    # add getMeanObservations method
    def getMeanObservations(self) -> SisypheVolume | None:
        """
        Get the mean volume of observations of the current SisypheDesign instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            mean volume of observations
        """
        return self._mean

    # Revision 24/11/2024 >

    def getAutocorrelations(self) -> list[float] | None:
        """
        Get autocorrelations of the current SisypheDesign instance.

        Reference:
        Robust smoothness estimation in statistical parametric maps using standardized residuals from the general
        linear model. SJ Kiebel, JB Poline, KJ Friston, AP Holmes, KJ Worsley. Neuroimage 1999 Dec;10(6):756-66.
        doi: 10.1006/nimg.1999.0508.

        Returns
        -------
        list[float]
            autocorrelations in x, y and z directions (gaussian point spread function, fwhm in mm)
        """
        if self.isEstimated(): return self._autocorr
        else: raise ValueError('Model is not estimated.')

    # < Revision 18/11/2024
    # add getDegreesOfFreedom method
    def getDegreesOfFreedom(self) -> int:
        """
        Get the degrees of freedom of the current SisypheDesign instance.

        Returns
        -------
        list[float, float, float]
            autocorrelations in x, y and directions (mm)
        """
        if self.isEstimated(): return getDOF(self._design)
        else: raise ValueError('Model is not estimated.')

    # Revision 18/11/2024 >

    def validateContrast(self, contrast: ndarray) -> ndarray:
        """
        Check validity of the contrast vector. Adjusts the contrast vector to make the cumulative sum equal to
        0.0, +1.0, or -1.0.

        Parameters
        ----------
        contrast : ndarray
            contrast vector

        Returns
        -------
        ndarray
            contrast vector
        """
        if len(contrast) == len(self._cdesign):
            estimable = array([v[1] for v in self._cdesign])
            effect = dict()
            for v in estimable:
                if v > 0:
                    if v not in effect: effect[v] = 1
                    else: effect[v] += 1
            if len(effect) == 1:
                neg = contrast < 0.0
                pos = contrast > 0.0
                if neg.any():
                    ncontrast = contrast * neg
                    ncontrast = ncontrast / -ncontrast.sum()
                else: ncontrast = zeros(shape=contrast.shape)
                if pos.any():
                    pcontrast = contrast * pos
                    pcontrast = pcontrast / pcontrast.sum()
                else: pcontrast = zeros(shape=contrast.shape)
                return pcontrast + ncontrast
            else: raise ValueError('Invalid contrast vector.')
        else:
            raise ValueError('The number of elements in the contrast vector ({}) does not match'
                             'the number of columns in the design matrix ({}).'.format(len(contrast),
                                                                                       len(self._cdesign)))

    # IO public methods

    def parseXML(self, doc: minidom.Document) -> None:
        """
        Read the current SisypheDesign instance attributes from xml instance. This method is called by load() method,
        not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                # Parse fMRI
                element = doc.getElementsByTagName('fmri')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    self._fmri = element[0].firstChild.data == 'True'
                else: self._fmri = False
                # Parse signal normalization
                element = doc.getElementsByTagName('norm')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    self._norm = int(element[0].firstChild.data)
                else: self._norm = 0
                # Parse ANCOVA
                element = doc.getElementsByTagName('ancova')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    self._ancova = int(element[0].firstChild.data)
                else: self._ancova = 0
                # Parse age covariable
                element = doc.getElementsByTagName('age')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    self._age = int(element[0].firstChild.data)
                else: self._age = 0
                # Parse observations
                elements = doc.getElementsByTagName('obs')
                self._obs = dict()
                self._cobs = dict()
                n = len(elements)
                if n > 0:
                    for element in elements:
                        k = element.getAttribute('key')
                        # < Revision 30/11/2024
                        # fix unhashable type list exceptions
                        # key = k.split()
                        # < Revision 05/06/2025
                        # replace space separator with '|'
                        key = tuple(k.split('|'))
                        # Revision 05/06/2025 >
                        # Revision 30/11/2024 >
                        if element.hasChildNodes():
                            self._obs[key] = list()
                            # < Revision 05/06/2025
                            # replace space separator with '|'
                            # self._cobs[key] = [int(v) for v in element.firstChild.data.split('|')]
                            buff = list()
                            # noinspection PyUnresolvedReferences
                            for v in element.firstChild.data.split('|'):
                                if v.isnumeric(): v = int(v)
                                else: v = float(v)
                                buff.append(v)
                            self._cobs[key] = buff
                            # Revision 05/06/2025 >
                # Parse filenames
                elements = doc.getElementsByTagName('file')
                n = len(elements)
                if n > 0:
                    for element in elements:
                        k = element.getAttribute('key')
                        # < Revision 30/11/2024
                        # fix unhashable type list exceptions
                        # key = k.split()
                        # < Revision 05/06/2025
                        # replace space separator with '|'
                        key = tuple(k.split('|'))
                        # Revision 05/06/2025 >
                        # Revision 30/11/2024 >
                        if element.hasChildNodes():
                            # < Revision 03/12/2024
                            # check if filename exists
                            # noinspection PyUnresolvedReferences
                            filename = element.firstChild.data
                            if exists(filename): self._obs[key].append(filename)
                            # Revision 03/12/2024 >
                # Parse group names
                element = doc.getElementsByTagName('groups')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    v = element[0].firstChild.data
                    # < Revision 05/06/2025
                    # replace space separator with '|'
                    if v != '': self._grp = v.split('|')
                    # Revision 05/06/2025 >
                    else: self._grp = list()
                # Parse subject names
                element = doc.getElementsByTagName('subjects')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    v = element[0].firstChild.data
                    # < Revision 05/06/2025
                    # replace space separator with '|'
                    if v != '': self._sbj = v.split('|')
                    # Revision 05/06/2025 >
                    else: self._sbj = list()
                # Parse condition names
                element = doc.getElementsByTagName('conditions')
                if len(element) > 0 and element[0].hasChildNodes():
                    # noinspection PyUnresolvedReferences
                    v = element[0].firstChild.data
                    # < Revision 05/06/2025
                    # replace space separator with '|'
                    if v != '': self._cnd = v.split('|')
                    # Revision 05/06/2025 >
                    else: self._cnd = list()
                # Parse effects, design matrix column information
                elements = doc.getElementsByTagName('effect')
                n = len(elements)
                if n > 0:
                    cdesign = [[]] * n
                    for element in elements:
                        i = int(element.getAttribute('column'))
                        name = element.getAttribute('name')
                        estim = int(element.getAttribute('estim'))
                        cdesign[i] = [name, estim]
                    self._cdesign = cdesign
                # Parse design matrix
                elements = doc.getElementsByTagName('row')
                n = len(elements)
                if n > 0:
                    buff = [[]] * n
                    for element in elements:
                        i = int(element.getAttribute('index'))
                        if element.hasChildNodes():
                            # noinspection PyUnresolvedReferences
                            v = element.firstChild.data
                            # < Revision 05/06/2025
                            # replace space separator with '|'
                            v = v.split('|')
                            # Revision 05/06/2025 >
                            v = array([float(j) for j in v])
                            # noinspection PyTypeChecker
                            buff[i] = v
                    self._design = stack(buff)
            else: raise IOError('XML file format is not supported.')

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDesign instance attributes to xml instance. This method is called by save() and
        saveAs() methods, not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            # < Revision 29/11/2024
            # bug fix, add forgotten doc.appendChild(root)
            doc.appendChild(root)
            # Revision 29/11/2024 >
            # fMRI
            item = doc.createElement('fmri')
            txt = doc.createTextNode(str(self._fmri))
            item.appendChild(txt)
            root.appendChild(item)
            # Signal normalization
            item = doc.createElement('norm')
            txt = doc.createTextNode(str(self._norm))
            item.appendChild(txt)
            root.appendChild(item)
            # ANCOVA
            item = doc.createElement('ancova')
            txt = doc.createTextNode(str(self._ancova))
            item.appendChild(txt)
            root.appendChild(item)
            # ANCOVA
            item = doc.createElement('age')
            txt = doc.createTextNode(str(self._age))
            item.appendChild(txt)
            root.appendChild(item)
            # Observations
            item = doc.createElement('observations')
            root.appendChild(item)
            if len(self._cobs) > 0:
                for key in self._cobs:
                    node = doc.createElement('obs')
                    # < Revision 05/06/2025
                    # replace space separator with '|'
                    node.setAttribute('key', '|'.join(key))
                    buff = '|'.join([str(v) for v in self._cobs[key]])
                    # Revision 05/06/2025 >
                    txt = doc.createTextNode(buff)
                    node.appendChild(txt)
                    item.appendChild(node)
            # Filenames
            item = doc.createElement('files')
            root.appendChild(item)
            if len(self._obs) > 0:
                for key in self._obs:
                    n = len(self._obs[key])
                    if n > 0:
                        for i in range(n):
                            node = doc.createElement('file')
                            # < Revision 05/06/2025
                            # replace space separator with '|'
                            node.setAttribute('key', '|'.join(key))
                            # Revision 05/06/2025 >
                            txt = doc.createTextNode(self._obs[key][i])
                            node.appendChild(txt)
                            item.appendChild(node)
            # Groups
            item = doc.createElement('groups')
            root.appendChild(item)
            if self._grp is not None and len(self._grp) > 0:
                # < Revision 05/06/2025
                # replace space separator with '|'
                buff = '|'.join(self._grp)
                # Revision 05/06/2025 >
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Subjects
            item = doc.createElement('subjects')
            root.appendChild(item)
            if self._sbj is not None and len(self._sbj) > 0:
                # < Revision 05/06/2025
                # replace space separator with '|'
                buff = '|'.join(self._sbj)
                # Revision 05/06/2025 >
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Conditions
            item = doc.createElement('conditions')
            root.appendChild(item)
            if self._cnd is not None and len(self._cnd) > 0:
                # < Revision 05/06/2025
                # replace space separator with '|'
                buff = '|'.join(self._cnd)
                # Revision 05/06/2025 >
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Effects, design matrix column information
            if self._cdesign is not None and len(self._cdesign) > 0:
                effects = doc.createElement('effects')
                root.appendChild(effects)
                for i in range(len(self._cdesign)):
                    node = doc.createElement('effect')
                    name, estim = self._cdesign[i]
                    node.setAttribute('column', str(i))
                    node.setAttribute('name', name)
                    node.setAttribute('estim', str(estim))
                    effects.appendChild(node)
            # Design matrix
            if self._design is not None:
                design = doc.createElement('design')
                root.appendChild(design)
                for i in range(self._design.shape[0]):  # rows
                    node = doc.createElement('row')
                    node.setAttribute('index', str(i))
                    v = list(self._design[i, :])
                    # < Revision 05/06/2025
                    # replace space separator with '|'
                    v = '|'.join([str(i) for i in v])
                    # Revision 05/06/2025 >
                    txt = doc.createTextNode(v)
                    node.appendChild(txt)
                    design.appendChild(node)

    def load(self, filename: str, wait: DialogWait | None = None) -> None:
        """
        Load the current SisypheDesign instance from a PySisyphe statistical design (.xmodel) file.

        Parameters
        ----------
        filename : str
            PySisyphe statistical design file name
        wait: DialogWait | None
            progress dialog (optional)
        """
        path, ext = splitext(filename)
        filename = path + self._FILEEXT
        if exists(filename):
            # Load XML
            if wait is not None:
                wait.setInformationText('Open model...\n{}'.format(basename(filename)))
            doc = minidom.parse(filename)
            self.parseXML(doc)
            self._filename = filename
            # < Revision 05/12/2024
            # bugfix, replace extension
            filename2 = filename.replace(self._FILEEXT, SisypheVolume.getFileExt())
            # Revision 05/12/2024 >
            # Load beta
            filename = addSuffixToFilename(filename2, 'beta')
            if exists(filename):
                if wait is not None:
                    wait.setInformationText('Open beta volume...\n{}'.format(basename(filename)))
                self._beta = SisypheVolume()
                self._beta.load(filename)
                self._autocorr = self._beta.acquisition.getAutoCorrelations()
            else: self._beta = None
            # Load variance
            filename = addSuffixToFilename(filename2, 'sig2')
            if exists(filename):
                if wait is not None:
                    wait.setInformationText('Open variance volume...\n{}'.format(basename(filename)))
                self._variance = SisypheVolume()
                self._variance.load(filename)
            else: self._variance = None
            # < Revision 22/11/2024
            # load observations (multi-component volume)
            filename = addSuffixToFilename(filename2, 'obs')
            if exists(filename):
                if wait is not None:
                    wait.setInformationText('Open observation volume...\n{}'.format(basename(filename)))
                self._vols = SisypheVolume()
                self._vols.load(filename)
            else: self._vols = None
            # Revision 22/11/2024 >
            # < Revision 24/11/2024
            # load mean volume of observations
            filename = addSuffixToFilename(filename2, 'mean')
            if exists(filename):
                if wait is not None:
                    wait.setInformationText('Open mean observation volume...\n{}'.format(basename(filename)))
                self._mean = SisypheVolume()
                self._mean.load(filename)
            else: self._mean = None
            # Revision 24/11/2024 >
            # < Revision 03/12/2024
            # load mean volume of observations
            filename = addSuffixToFilename(filename2, 'mask')
            if exists(filename):
                if wait is not None:
                    wait.setInformationText('Open mask of analysis...\n{}'.format(basename(filename)))
                self._mask = SisypheVolume()
                self._mask.load(filename)
            else: self._mask = None
            # Revision 03/12/2024 >
        else: raise IOError('No such file {}'.format(filename))

    def save(self, wait: DialogWait | None = None) -> None:
        """
        Save the current SisypheDesign instance to a PySisyphe statistical design (.xmodel) file. The file name
        attribute of the current SisypheDesign instance is used.

        Parameters
        ----------
        wait: DialogWait | None
            progress dialog (optional)
        """
        if self.hasFilename():
            filename = self.getFilename()
            # Save beta
            if self._beta is not None:
                self._beta.setFilename(filename)
                self._beta.setFilenameSuffix('beta')
                if wait is not None:
                    wait.setInformationText('Save beta volume...\n{}'.format(self._beta.getBasename()))
                self._beta.save()
            # Save variance
            if self._variance is not None:
                self._variance.setFilename(filename)
                self._variance.setFilenameSuffix('sig2')
                if wait is not None:
                    wait.setInformationText('Save variance volume...\n{}'.format(self._variance.getBasename()))
                self._variance.save()
            # < Revision 22/11/2024
            # Save observations
            if self._vols is not None:
                self._vols.setFilename(filename)
                self._vols.setFilenameSuffix('obs')
                if wait is not None:
                    wait.setInformationText('Save observation volume...\n{}'.format(self._vols.getBasename()))
                self._vols.save()
            # Revision 22/11/2024 >
            # < Revision 24/11/2024
            # Save mean observations
            if self._mean is not None:
                self._mean.setFilename(filename)
                self._mean.setFilenameSuffix('mean')
                if wait is not None:
                    wait.setInformationText('Save mean observation volume...\n{}'.format(self._mean.getBasename()))
                self._mean.save()
            # Revision 24/11/2024 >
            # < Revision 03/12/2024
            # Save mean observations
            if self._mask is not None:
                self._mask.setFilename(filename)
                self._mask.setFilenameSuffix('mask')
                if wait is not None:
                    wait.setInformationText('Save mask of analysis...\n{}'.format(self._mask.getBasename()))
                self._mask.save()
            # Revision 24/11/2024 >
            # Save xml
            if wait is not None:
                wait.setInformationText('Save model...\n{}'.format(basename(filename)))
            doc = minidom.Document()
            self.createXML(doc)
            buff = doc.toprettyxml()
            f = open(filename, 'w')
            try: f.write(buff)
            except IOError: raise IOError('XML file write error.')
            finally: f.close()
        else: raise AttributeError('No model filename.')

    def saveAs(self, filename: str) -> None:
        """
        Save the current SisypheDesign instance to a PySisyphe statistical design (.xmodel) file.

        Parameters
        ----------
        filename : str
            PySisyphe statistical design file name
        """
        self.setFilename(filename)
        self.save()
