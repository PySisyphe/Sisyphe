"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        Scipy           https://docs.scipy.org/doc/scipy/index.html                 Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
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

from numpy import array
from numpy import stack
from numpy import column_stack
from numpy import zeros
from numpy import ones
from numpy import ndarray
from numpy import finfo
from numpy import power
from numpy import sort
from numpy import isinf
from numpy import isnan
from numpy import median
from numpy import percentile
from numpy import append
from numpy import where
from numpy import convolve
from numpy import euler_gamma
from numpy import count_nonzero
from numpy.linalg import matrix_rank
from numpy.linalg import inv
from numpy.linalg import pinv

from scipy.stats import t as student
from scipy.stats import norm
from scipy.stats import chi2
from scipy.stats import gamma as gamma2

from SimpleITK import ConnectedComponentImageFilter
from SimpleITK import RelabelComponentImageFilter
from SimpleITK import LabelStatisticsImageFilter
from SimpleITK import GetArrayViewFromImage

import Sisyphe.core as sc
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
           'ReselCount',
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
           'getDOF',
           'isRankDeficient',
           'getHRF',
           'getBoxCarModel',
           'convolveModelHRF',
           'getHighPass',
           'tTozmap',
           'conjonctionFisher',
           'conjonctionWorsley',
           'conjonctionStouffer',
           'conjonctionMudholkar',
           'conjonctionTippett',
           'autocorrelationsEstimate',
           'modelEstimate',
           'tmapContrastEstimate',
           'zmapContrastEstimate',
           'thresholdMap',
           'SisypheDesign']

"""
    Functions
    
        float = tTopvalue(float, float)
        float = zTopvalue(float)
        float = pvalueTot(float, float)
        float = pvalueToz(float, float)
        float = zTot(float, float)
        float = tToz(float, float)
        float = pCorrectedBonferroni(float, int)
        float = pUncorrectedBonferroni(float, int)
        float = qFDRToz(float, SisypheVolume, bool)
        float = qFDRTot(float, SisypheVolume, bool)
        float, float, float, float = tFieldEulerCharacteristic(float, float)
        float, float, float, float = zFieldEulerCharacteristic(float, float)
        float, float, float, float = ReselCount(SisypheVolume, float, float, float)
        float = tFieldExpectedClusters(float, float, float, float, float, float)
        float = zFieldExpectedClusters(float, float, float, float, float, float)
        float = tFieldExpectedVoxels(float, float, int)
        float = zFieldExpectedVoxels(float, int)
        float = expectedVoxelsPerCluster(float, float)
        float = extentToClusterUncorrectedpvalue(int, float, float)
        float = extentToClusterCorrectedpvalue(int, float, float)
        int = clusterUncorrectedpvalueToExtent(float, float, float)
        int = clusterCorrectedpvalueToExtent(float, float, float)
        float = voxelCorrectedpvalue(float)
        float = tToVoxelCorrectedpvalue(float, float, float, float, float, float)
        float = zToVoxelCorrectedpvalue(float, float, float, float, float, float)
        float = voxelCorrectedpvalueTot(float, float, float, float, float, float)
        float = voxelCorrectedpvalueToz(float, float, float, float, float, float)
        int = getDOF(numpy.ndarray)
        bool = isRankDeficient(numpy.ndarray)

    Creation: 29/11/2022        
    Revisions:
    
        02/09/2023  type hinting       
"""

def tTopvalue(t: float, df: int) -> float:
    # Validated
    if t == 0.0: p = 1.0
    else:
        p = 1.0 - student.cdf(t, df)
        if p == 0.0: p = finfo(float).eps
    return p

def zTopvalue(z: float) -> float:
    # Validated
    if z == 0.0: p = 1.0
    else:
        p = 1.0 - norm.cdf(z)
        if p == 0.0: p = finfo(float).eps
    return p

def pvalueTot(p: float, df: int) -> float:
    # ppf is inv CDF
    # Validated
    t = student.ppf(1.0 - p, df)
    return t

def pvalueToz(p: float) -> float:
    # ppf is inv CDF
    # Validated
    z = norm.ppf(1.0 - p)
    return z

def zTot(z: float, df: int) -> float:
    p = zTopvalue(z)
    t = pvalueTot(p, df)
    return t

def tToz(t: float, df: int) -> float:
    p = tTopvalue(t, df)
    z = pvalueToz(p)
    return z

def pCorrectedBonferroni(p: float, n: int) -> float:
    # Validated
    p = 1.0 - power((1.0 - p), n)
    return p

def pUncorrectedBonferroni(p: float, n: int) -> float:
    # Validated
    p = 1.0 - power((1.0 - p), 1.0 / n)
    return p

def qFDRToz(q: float, img: sc.sisypheVolume.SisypheVolume, independent: bool = False) -> float:
    if isinstance(img, sc.sisypheVolume.SisypheVolume):
        img = img.getNumpy().flatten()
        n = count_nonzero(img)
        if independent: c = 1.0
        else: c = log(n) + euler_gamma + 1.0 / (2.0 * n)
        img = sort(img)[::-1]
        for i in range(n):
            p = zTopvalue(img[i])
            r = (i + 1) * q / (n * c)
            if p > r: return img[i]
    else: raise TypeError('Volume parameter type {} is not SisypheVolume.'.format(type(img)))

def qFDRTot(q: float, df: int, img: sc.sisypheVolume.SisypheVolume, independent: bool = False) -> float:
    if isinstance(img, sc.sisypheVolume.SisypheVolume):
        img = img.getNumpy().flatten()
        n = count_nonzero(img)
        if independent: c = 1.0
        else: c = log(n) + euler_gamma + 1.0 / (2.0 * n)
        img = sort(img)[::-1]
        for i in range(n):
            p = tTopvalue(img[i], df)
            r = (i + 1) * q / (n * c)
            if p > r: return img[i]
    else: raise TypeError('Volume parameter type {} is not SisypheVolume.'.format(type(img)))

def tFieldEulerCharacteristic(t: float, df: int) -> tuple[float, ...]:
    b1 = 4.0 * log(2)
    b2 = 2.0 * pi
    b3 = power(1.0 + ((t ** 2) / df), -0.5 * (df - 1))
    rho0 = 1.0 - student.cdf(t, df)
    rho1 = (sqrt(b1) / b2) * b3
    rho2 = (b1 / (power(b2, 1.5) * gamma(df / 2.0) * sqrt(df / 2.0))) * b3 * t * gamma((df + 1.0) / 2.0)
    rho3 = (power(b1, 1.5) / (b2 ** 2)) * b3 * ((((df - 1.0) / df) * (t ** 2)) - 1.0)
    return rho0, rho1, rho2, rho3

def zFieldEulerCharacteristic(z: float) -> tuple[float, ...]:
    b1 = 4.0 * log(2)
    b2 = 2.0 * pi
    b3 = exp(-(z ** 2) / 2.0)
    rho0 = 1.0 - norm.cdf(z)
    rho1 = (sqrt(b1) / b2) * b3
    rho2 = (b1 / power(b2, 1.5)) * b3 * z
    rho3 = (power(b1, 1.5) / (b2 ** 2)) * b3 * ((z ** 2) - 1)
    return rho0, rho1, rho2, rho3

def ReselCount(mask: sc.sisypheVolume.SisypheVolume,
               autocorrx: float,
               autocorry: float,
               autocorrz: float) -> tuple[float, ...]:
    if isinstance(mask, sc.sisypheVolume.SisypheVolume):
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
        for k in range(s[2]):
            for j in range(s[1]):
                for i in range(s[0]):
                    if mask[k, j, i] > 0:
                        p += 1
                        if i < lim0:
                            if mask[k, j, i+1] > 0: ex += 1
                            if j < lim1:
                                if mask[k, j+1, i+1] > 0: fxy += 1
                                if k < lim2:
                                    if mask[k+1, j+1, i+1] > 0: c += 1
                            if k < lim2:
                                if mask[k+1, j, i+1] > 0: fxz += 1
                        if j < lim1:
                            if mask[k, j+1, i] > 0: ey += 1
                            if k < lim2:
                                if mask[k+1, j+1, i] > 0: fyz += 1
                        if k < lim2:
                            if mask[k+1, j, i] > 0: ez += 1
        rc0 = p - (ex + ey + ez) + (fxy + fxz + fyz) - c
        rc1 = ((ex - fxy - fxz + c) * rx) + ((ey - fxy - fyz + c) * ry) + ((ez - fxz - fyz + c) * rz)
        rc2 = ((fxy - c) * rx * ry) + ((fxz - c) * rx * rz) + ((fyz - c) * ry * rz)
        rc3 = c * rx * ry * rz
        return rc0, rc1, rc2, rc3

def tFieldExpectedClusters(t: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    rho0, rho1, rho2, rho3 = tFieldEulerCharacteristic(t, df)
    return (rho0 * rc0) + (rho1 * rc1) + (rho2 * rc2) + (rho3 * rc3)

def zFieldExpectedClusters(z: float, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    rho0, rho1, rho2, rho3 = zFieldEulerCharacteristic(z)
    return (rho0 * rc0) + (rho1 * rc1) + (rho2 * rc2) + (rho3 * rc3)

def tFieldExpectedVoxels(t: float, df: int, n: int) -> float:
    return n * tTopvalue(t, df)

def zFieldExpectedVoxels(z: float, n: int) -> float:
    return n * zTopvalue(z)

def expectedVoxelsPerCluster(ev: float, ec: float) -> float:
    """
        ec expected number of clusters
        ev expected number of voxels
    """
    return ev / ec

def extentToClusterUncorrectedpvalue(k: int, ev: float, ec: float) -> float:
    """
        k extent, number of voxels
        ec expected number of clusters
        ev expected number of voxels
    """
    c = 2.0 / 3.0
    beta = power(gamma(2.5) * (ec / ev), c)
    return exp(-beta * power(k, c))

def extentToClusterCorrectedpvalue(k: int, ev: float, ec: float) -> float:
    """
        k extent, number of voxels
        ec expected number of clusters
        ev expected number of voxels
    """
    puc = extentToClusterUncorrectedpvalue(k, ev, ec)
    return 1 - exp(-(ec + finfo(float).eps) * puc)

def clusterUncorrectedpvalueToExtent(p: float, ev: float, ec: float) -> int:
    """
        p value cluster uncorrected
        ec expected number of clusters
        ev expected number of voxels
        Validated
    """
    beta = power(gamma(2.5) * (ec / ev), 2.0 / 3.0)
    return int((power(-log(p) / beta, 3.0 / 2.0)))

def clusterCorrectedpvalueToExtent(p: float, ev: float, ec: float) -> int:
    """
        p value cluster corrected
        ec expected number of clusters
        ev expected number of voxels
        Validated
    """
    beta = power(gamma(2.5) * (ec / ev), 2.0 / 3.0)
    return int(power(log(-ec / log(1 - p)) / beta, 3.0 / 2.0))

def voxelCorrectedpvalue(ev: float) -> float:
    return 1 - exp(-ev)

def tToVoxelCorrectedpvalue(t: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    p = tFieldExpectedClusters(t, df, rc0, rc1, rc2, rc3)
    return 1.0 - exp(-p)

def zToVoxelCorrectedpvalue(z: float, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
    p = zFieldExpectedClusters(z, rc0, rc1, rc2, rc3)
    return 1.0 - exp(-p)

def voxelCorrectedpvalueTot(u: float, df: int, rc0: float, rc1: float, rc2: float, rc3: float) -> float:
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
    if isinstance(design, ndarray):
        return design.shape[0] - matrix_rank(design)
    else: raise TypeError('matrix parameter type {} is not numpy.ndarray.'.format(type(design)))

def isRankDeficient(X: ndarray) -> bool:
    if isinstance(X, ndarray):
        n = min(X.shape[0], X.shape[1])
        return matrix_rank(X) < n
    else: raise TypeError('parameter type {} is not numpy.ndarray.'.format(type(X)))

"""
    fMRI functions
    
        numpy.ndarray = getHRF(float, float, float, float, float, float, float)
        numpy.ndarray = getBoxCarModel(int, int, int, int)
        numpy.ndarray = convolveModelHRF(numpy.ndarray, float)
        numpy.ndarray = getHighPass()

    Creation: 29/11/2022   
    Revisions:

        02/09/2023  type hinting        
"""

def getHRF(pdelay: float = 6.0,
           ndelay: float = 16.0,
           pspread: float = 1.0,
           nspread: float = 1.0,
           ratio: float = 6.0,
           dt: float = 0.1,
           iscan: float = 2.0) -> ndarray:
    """
        Hemodynamic response function

        pdelay      float, delay in s of positive response (default 6 s)
        ndelay      float, delay in s of negative response (default 16 s)
        pspread     float, spread in s of positive response (default 1 s)
        nspread     float, spread in s of negative response (default 1 s)
        ratio       float, ratio of positive to negative responses (default 6)
        dt          float, sampling (default 0.1 s)
        iscan       float, interscan interval (TR)
    """
    nb = int(16 / dt)  # 16 s
    buff = zeros([nb, ])
    for i in range(nb):
        j = i * dt * 2
        buff[i] = (gamma2.pdf(j, pdelay / pspread) - (gamma2.pdf(j, ndelay / nspread) / ratio))
    if iscan > 0:
        s = int(iscan / dt)
        nb = int(16 / iscan)
        hrf = zeros([nb, ])
        for i in range(nb):
            hrf[i] = buff[i * s]
    else: hrf = buff
    s = hrf.sum()
    hrf = hrf / s
    return hrf

def getBoxCarModel(first: int,
                   nactive: int,
                   nrest: int,
                   nblocks: int) -> ndarray:
    """
        first   int, index of the first scan activity condition
        nactive int, number of scans in activation blocks
        nrest   int, number of scans in rest blocks
        nblocks int, number of blocks (1 block = 1 active block + 1 rest block)
    """
    bstart = [0] * first
    bactive = [1] * nactive
    brest = [0] * nrest
    b = bactive + brest
    run = bstart + b * nblocks
    return array(run)

def convolveModelHRF(model: ndarray, iscan: float) -> ndarray:
    """
        model   numpy.ndarray, boxcar model
        iscan   float, interscan interval (TR)
    """
    hrf = getHRF(iscan=iscan)
    model2 = convolve(model, hrf)
    model2 = model2[:len(model)]
    return model2

def getHighPass(nscans: int, nblocks: int) -> ndarray:
    """
        nscans      int, image count
        nblocks     int, block count (1 block = 1 active block + 1 rest block) = order
    """
    hpass = zeros([nscans, nblocks])
    for i in range(nblocks - 1):  # cols
        for j in range(nscans):   # rows
            hpass[j, i] = cos((i + 1) * pi * (j / (nscans - 1)))
    return hpass

"""
    Maps functions
    
        SisypheVolume = tTozmap(SisypheVolume)
        SisypheVolume = conjonctionFisher(list of SisypheVolume)
        SisypheVolume = conjonctionWorsley(list of SisypheVolume)
        SisypheVolume = conjonctionStouffer(list of SisypheVolume)
        SisypheVolume = conjonctionMudholkar(list of SisypheVolume)
        SisypheVolume = conjonctionTippett(list of SisypheVolume)
        autocorrelationsEstimate(ndarray, ndarray, SisypheVolume)
        modelEstimate(list of SisypheVolume, SisypheVolume, ndarray)
        tmapContrastEstimate(ndarray, ndarray, ndarray, ndarray, float, SisypheVolume)
        zmapContrastEstimate(ndarray, ndarray, ndarray, ndarray, float, SisypheVolume)
        thresholdMap(SisypheVolume, float, int)

    Creation: 29/11/2022
    Revisions:
    
        02/09/2023  type hinting
"""

def tTozmap(tmap: sc.sisypheVolume.SisypheVolume) -> sc.sisypheVolume.SisypheVolume:
    if isinstance(tmap, sc.sisypheVolume.SisypheVolume):
        if tmap.acquisition.isTMap():
            df = tmap.acquisition.getDegreesOfFreedom()
            zmap = tmap.copy()
            zmap.acquisition.setSequenceToZMap()
            zmap.acquisition.setDegreesOfFreedom(0)
            np = zmap.getNumpy().flatten()
            for i in range(len(np)):
                if np[i] > 0:
                    p = tTopvalue(np[i], df)
                    np[i] = pvalueToz(p)
            return zmap
        else: raise AttributeError('Volume parameter sequence {} is not t map.'.format(tmap.acquisition.getSequence()))
    else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(tmap)))

# to do
def conjonctionFisher(maps: list[sc.sisypheVolume.SisypheVolume]
                            | sc.sisypheVolume.SisypheVolumeCollection) -> sc.sisypheVolume.SisypheVolume:
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i])
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    for m in maps:
        npmaps.append(m.getNumpy().flatten())
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        for i in range(nb):
            # Fisher = -2 * sum(log(Pi))
            s = 0
            for npmap in npmaps:
                s += log(1.0 - norm.cdf(npmap[i]))
            s *= -2.0
            p = 1.0 - chi2.cdf(s, 2 * n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        for i in range(nb):
            # Fisher = -2 * sum(log(Pi))
            s = 0
            for npmap in npmaps:
                s += log(1.0 - student.cdf(npmap[i], df[i]))
            s *= -2.0
            p = 1.0 - chi2.cdf(s, 2 * n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r

# to do
def conjonctionWorsley(maps: list[sc.sisypheVolume.SisypheVolume]
                             | sc.sisypheVolume.SisypheVolumeCollection) -> sc.sisypheVolume.SisypheVolume:
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    for m in maps:
        npmaps.append(m.getNumpy().flatten())
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - norm.cdf(npmap[i])
                if b > s: s = b  # search max pvalue
            p = power(s, n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - student.cdf(npmap[i], df[i])
                if b > s: s = b  # search max pvalue
            p = power(s, n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r

# to do
def conjonctionStouffer(maps: list[sc.sisypheVolume.SisypheVolume]
                              | sc.sisypheVolume.SisypheVolumeCollection) -> sc.sisypheVolume.SisypheVolume:
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    for m in maps:
        npmaps.append(m.getNumpy().flatten())
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        # Stouffer = sum(NormalCDFInv(1 - Pi)) / sqrt(n)
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - norm.cdf(npmap[i])
                s += norm.sf(1.0 - b)
            r = s / sqrt(n)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        # Stouffer = sum(NormalCDFInv(1 - Pi)) / sqrt(n)
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - student.cdf(npmap[i], df[i])
                s += norm.sf(1.0 - b)
            r = s / sqrt(n)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r

# to do
def conjonctionMudholkar(maps: list[sc.sisypheVolume.SisypheVolume]
                               | sc.sisypheVolume.SisypheVolumeCollection) -> sc.sisypheVolume.SisypheVolume:
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    for m in maps:
        npmaps.append(m.getNumpy().flatten())
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    c1 = (5 * n) + 2
    c2 = c1 + 2
    # z maps
    if zflag:
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - norm.cdf(npmap[i])
                s += log(b / (1.0 - b))
            p = s * -sqrt(3 * c2 / (n * (pi ** 2) * c1))
            p = 1.0 - student.cdf(p, c2)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - norm.cdf(npmap[i])
                s += log(b / (1.0 - b))
            p = s * -sqrt(3 * c2 / (n * (pi ** 2) * c1))
            p = 1.0 - student.cdf(p, c2)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r

# to do
def conjonctionTippett(maps: list[sc.sisypheVolume.SisypheVolume]
                             | sc.sisypheVolume.SisypheVolumeCollection) -> sc.sisypheVolume.SisypheVolume:
    zflag = False
    # z map in list ?
    for m in maps:
        if m.acquisition.isZMap():
            zflag = True
            break
    # if z map, conversion of t maps
    if zflag:
        for i in range(len(maps)):
            if maps[i].acquisition.isTMap():
                maps[i] = tTozmap(maps[i], )
    # Largest autocorrelations
    if not zflag:
        autocorrx, autocorry, autocorrz = maps[0].acquisition.getAutoCorrelations()
        for i in range(1, len(maps)):
            bautocorrx, bautocorry, bautocorrz = maps[0].acquisition.getAutoCorrelations()
            if bautocorrx > autocorrx: autocorrx = bautocorrx
            if bautocorry > autocorry: autocorry = bautocorry
            if bautocorrz > autocorrz: autocorrz = bautocorrz
    # Numpy conversion of maps
    npmaps = list()
    for m in maps:
        npmaps.append(m.getNumpy().flatten())
    nb = len(npmaps[0])
    conj = zeros([nb, ])
    n = len(npmaps)
    # z maps
    if zflag:
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - norm.cdf(npmap[i])
                if s == 0: s = b
                if b < s: s = b  # search min pvalue
            p = 1.0 - power(1.0 - s, n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r
    # t maps
    else:
        df = list()
        for m in maps:
            df.append(m.acquisition.getDegreesOfFreedom())
        for i in range(nb):
            s = 0
            for npmap in npmaps:
                b = 1.0 - student.cdf(npmap[i], df[i])
                if s == 0: s = b
                if b < s: s = b  # search min pvalue
            p = 1.0 - power(1.0 - s, n)
            r = norm.sf(1.0 - p)
            if isnan(r) or isinf(r): r = 0.0
            conj[i] = r

def autocorrelationsEstimate(error: ndarray,
                             design: ndarray,
                             mask: sc.sisypheVolume.SisypheVolume) -> tuple[float, float, float]:
    """
        error   ndarray, model error vector / standard deviation of error
                         computed in modelEstimate function
        design  ndarray, design matrix X
        mask    SisypheVolume
    """
    buffx = buffy = buffz = 0
    vx, vy, vz = mask.getSpacing()
    sx, sy, sz = mask.getSize()
    slc = sx * sy
    npmask = mask.getNumpy().flatten()
    nb = len(npmask)
    nbv = 0
    for i in range(slc, nb):
        if npmask[i] > 0 and npmask[i-1] > 0 and npmask[i-sx] > 0 and npmask[i-slc] > 0:
            verrorx = error[:, i] - error[:, i-1]
            verrory = error[:, i] - error[:, i-sx]
            verrorz = error[:, i] - error[:, i-slc]
            verrorx = (verrorx / vx) ** 2
            verrory = (verrory / vy) ** 2
            verrorz = (verrorz / vz) ** 2
            buffx = buffx + verrorx.sum()
            buffy = buffy + verrory.sum()
            buffz = buffz + verrorz.sum()
            nbv += 1
    df = getDOF(design)
    f1 = (df - 2) / ((df - 1) * nbv)
    f2 = 4.0 * log(2.0)
    autocorrx = sqrt(f2 / (buffx * f1))
    autocorry = sqrt(f2 / (buffy * f1))
    autocorrz = sqrt(f2 / (buffz * f1))
    return autocorrx, autocorry, autocorrz

def modelEstimate(obs: list[sc.sisypheVolume.SisypheVolume],
                  design: ndarray,
                  mask: sc.sisypheROI.SisypheROI,
                  scale: float | None = None,
                  wait: DialogWait | None = None) -> tuple[ndarray, ndarray, ndarray]:
    """
        obs     list of SisypheVolume
        mask    SisypheROI, mask
        design  ndarray, design matrix X
        scale   float, signal normalization value
        wait    DialogWait
    """
    n = len(obs)
    if design.shape[0] == n:
        # ndarray conversion
        lobs = list()
        for o in obs:
            lobs.append(o.getNumpy().flatten())
        npobs = stack(lobs)
        npmask = mask.getNumpy().flatten()
        nb = len(npmask)
        # Main loop
        beta = zeros([nb, design.shape[1]])
        error = zeros([nb, design.shape[1]])
        variance = zeros([nb, ])
        idesign = pinv(design)
        if wait is not None:
            wait.setInformationText('Model estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        for i in range(nb):
            if wait is not None: wait.incCurrentProgressValue()
            if npmask[i] > 0:
                # Y vector (vobs) of observations at current voxel i
                if scale is not None: vobs = npobs[:, i] / scale
                else: vobs = npobs[:, i]
                vbeta = idesign @ vobs  # beta = pinv(X) Y
                beta[i, :] = vbeta
                vobsm = design @ vbeta  # Y' = X beta
                verror = vobs - vobsm   # E = Y - Y'
                verror2 = verror ** 2
                variance[i] = verror2.sum()  # Variance = sum of squared errors
                error[i, :] = verror / sqrt(variance[i])
        if wait is not None: wait.progressVisibilityOff()
        return beta, variance, error
    else: raise ValueError('Row count {} of the design matrix is not the same '
                           'as observations count {}.'.format(design.shape[0], n))

def tmapContrastEstimate(contrast: ndarray,
                         design: ndarray,
                         beta: sc.sisypheVolume.SisypheVolume,
                         variance: sc.sisypheVolume.SisypheVolume,
                         df: int,
                         wait: DialogWait | None = None) -> ndarray:
    """
        contrast    ndarray, contrast vector
        design      ndarray, design matrix
        beta        SisypheVolume, beta
        variance    SisypheVolume, pooled variance
        df          int, DOF
        wait        DialogWait
    """
    if len(contrast) == design.shape[1]:
        variance = variance.getNumpy().flatten()
        nb = len(variance)
        beta = beta.getNumpy().reshape(nb, len(contrast))
        # Compute Ct (XtX)-1 C
        designt = design.T          # Xt
        buff = designt @ design     # XtX
        if isRankDeficient(buff):
            # Rank deficient
            buff = pinv(buff)       # (XtX)-1
        else:
            # Full rank
            buff = inv(buff)        # (XtX)-1
        buff = contrast @ buff
        d = float(buff @ contrast)
        tmap = zeros(nb)
        if wait is not None:
            wait.setInformationText('Contrast estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        # t test main loop
        # s2 pooled variance of current voxel
        for i in range(nb):
            if wait is not None: wait.incCurrentProgressValue()
            if variance[i] > 0:
                s2 = variance[i] / df
                vbeta = beta[:, i]
                n = float(contrast @ vbeta)
                tmap[i] = n / sqrt(s2 * d)
            else: tmap[i] = 0.0
        if wait is not None: wait.progressVisibilityOff()
        return tmap
    else: raise ValueError('Column count {} of the design matrix is not the same as '
                           'number of elements in the contrast vector {}.'.format(design.shape[1], len(contrast)))

def zmapContrastEstimate(contrast: ndarray,
                         beta: sc.sisypheVolume.SisypheVolume,
                         variance: sc.sisypheVolume.SisypheVolume,
                         df: int,
                         wait: DialogWait | None = None) -> ndarray:
    """
        contrast    ndarray, contrast vector
        beta        SisypheVolume, beta
        variance    SisypheVolume, pooled variance
        df          int, DOF
        wait        DialogWait
    """
    if len(contrast) == beta.shape[1]:
        variance = variance.getNumpy().flatten()
        nb = len(variance)
        beta = beta.getNumpy().reshape(nb, len(contrast))
        zmap = zeros([nb, ])
        if wait is not None:
            wait.setInformationText('Contrast estimation...')
            wait.setProgressRange(0, nb)
            wait.progressVisibilityOn()
        # z test main loop
        # s standard deviation of current voxel
        for i in range(nb):
            if variance[i] > 0:
                s = sqrt(variance[i] / df)
                vbeta = beta[:, i]
                n = float(contrast @ vbeta)
                zmap[i] = n / s
            else: zmap[i] = 0.0
        if wait is not None: wait.progressVisibilityOff()
        return zmap
    else: raise ValueError('Column count {} of the design matrix is not the same as '
                           'number of elements in the contrast vector {}.'.format(beta.shape[1], len(contrast)))

def thresholdMap(statmap: sc.sisypheVolume.SisypheVolume,
                 stat: float, ext: int) -> sc.sisypheVolume.SisypheVolume:
    """
        statmap SisypheVolume, tmap or zmap
        stat    float, t or z threshold
        ext     int, number of voxels extension
    """
    from Sisyphe.core.sisypheVolume import SisypheVolume
    if isinstance(statmap, sc.sisypheVolume.SisypheVolume):
        if statmap.acquisition.isTMap() or statmap.acquisition.isZMap():
            img = statmap.getSITKImage()
            mask = img >= stat
            f = ConnectedComponentImageFilter()
            label = f.Execute(mask)
            f = RelabelComponentImageFilter()
            f.SortByObjectSizeOn()
            f.SetMinimumObjectSize(ext)
            label = f.Execute(label)
            mask = label > 0
            img = img * mask
            f = LabelStatisticsImageFilter()
            f.Execute(img, label)
            r = dict()
            r['extent'] = list()
            r['max'] = list()
            for i in range(f.GetNumberOfLabels()):
                r['extent'].append(f.GetCount(i))
                r['max'].append(f.GetMaximum(i))
            vol = sc.sisypheVolume.SisypheVolume()
            vol.copyPropertiesFrom(statmap)
            vol.setSITKImage(img)
            return vol, r
        else: raise AttributeError('Image parameter is not a statistical map.')
    else: raise TypeError('Image parameter type {} is not SisypheVolume.'.format(type(statmap)))


"""

    Class hierarchy
    
        object -> SisypheDesign

"""


class SisypheDesign(object):
    """
        SisypheDesign class

        Description

            Model definition class for voxel by voxel statistical mapping analysis

        Inheritance

            object -> SisypheDesign

        Private attributes

            _obs        dict, Key (group, subj, cond), list of str filenames
            _group      list of str, Group names
            _subj       list of str, Subject names
            _cond       list of str, Condition names
            _design     numpy.ndarray, design matrix
            _cdesign    list of (name str, estimable int 0, 1=estimable or 2=Main effect),
                        column name of the design matrix
            _ancova     int, 1 ANCOVA global, 2 by group, 3 by subject, 4 by condition
            _norm       int, 0 no, 1 scaling mean, 2 scaling median, 3 scale 75th percentile
                             4 roi mean, 5 roi median, 6 roi 75th percentile,
                             7 ancova mean, 8 ancova median, 9 ancova 75th percentile,
                             10 ancova roi mean, 11 ancova roi median, 12 roi 75th percentile
            _fmri       bool, fMRI model
            _beta       numpy.ndarray, beta of the model estimation
            _variance   numpy.ndarray, pooled variance of the model estimation

        Public methods

            bool = hasFilename()
            str = getFilename()
            str = getDirname()
            str = getBasename()
            setFilename(str)
            setfMRIDesign()
            bool = isfMRIDesign()
            addGroup(str)
            addSubject(str)
            addCondition(str)
            setGroupName(int, str)
            setSubjectName(int, str)
            setConditionName(int, str)
            str = getGroupName(int)
            str = getSubjectName(int)
            str = getConditionName(int)
            bool = hasGroup()
            bool = hasSubject()
            bool = hasCondition()
            int = getGroupCount()
            int = getSubjectCount()
            int = getConditionCount()
            int = getObsCount(group=str, subj=str, cond=str)
            int = getTotalObsCount()
            addObsTo(list of str, group=str, subj=str, cond=str)
            addDummyObsTo(int, group=str, subj=str, cond=str)
            addHRFBoxCarModelToCondition(str, int, int, int, int, float)
            addHighPassToCondition(str, int, int)
            addGlobalCovariable(str, numpy.ndarray, int)
            addCovariableByGroup(str, numpy.ndarray, int)
            addCovariableBySubject(str, numpy.ndarray, int)
            addCovariableByCondition(str, numpy.ndarray, int)
            setAncovaGlobal()
            setAncovaByGroup()
            setAncovaBySubject()
            setAncovaByCondition()
            numpy.ndarray = getDesign()
            estimate()
            SisypheVolume = getBeta()
            SisypheVolume = getVariance()
            bool = isEstimated()
            parseXML(minidom.Document)
            createXML(minidom.Document)
            load(str)
            save()
            saveAs(str)

        Creation: 29/11/2022
        Revisions:

            02/09/2023  type hinting
    """
    __slots__ = ['_obs', '_group', '_subj', '_cond', '_design', '_cdesign', '_ancova',
                 '_norm', '_fmri', '_beta', '_variance', '_autocorr', '_filename']

    # Class constants

    _FILELEXT = '.xmodel'

    # Class method

    @classmethod
    def geFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Geometric transformation (*{})'.format(cls._FILEEXT)

    @classmethod
    def calcMask(cls, obs: sc.sisypheVolume.SisypheVolume) -> sc.sisypheVolume.SisypheVolume:
        img = obs[0].getSITKImage() + obs[1].getSITKImage()
        for i in range(2, len(obs)):
            img = img + obs[i].getSITKImage()
        np = GetArrayViewFromImage(img)
        s = np.flatten().mean()
        img = img > s
        mask = sc.sisypheVolume.SisypheVolume()
        mask.setSITKImage(img)
        return mask

    # Special method

    def __init__(self) -> None:
        self._obs = dict()      # (Key (group, subj, cond), list of filenames)
        self._group = list()    # Group names
        self._subj = list()     # Subject names
        self._cond = list()     # Condition names
        self._design = None     # numpy.ndarray, design matrix
        self._cdesign = None    # (name, estimable 0/1) of design matrix columns
        self._ancova = 0        # 0 ANCOVA global, 1 by group, 2 by subject, 3 by condition
        self._norm = 0          # 0 no, 1 proportional scaling, 2 roi, 3 ancova
        self._fmri = False
        self._beta = None       # SisypheVolume
        self._variance = None   # SisypheVolume
        self._autocorr = None   # (float, float, float)
        self._filename = ''

    def __str__(self) -> str:
        buff = ''
        if self._fmri: buff += 'fMRI design\n'
        buff += 'Signal normalization: {}\n'.format(['No', 'Mean Scaling', 'ANCOVA'][self._norm])
        if self.hasGroup(): buff += 'Groups (n={}): {}\n'.format(len(self._group), ' '.join(self._group))
        if self.hasSubject(): buff += 'Subjects (n={}): {}\n'.format(len(self._subj), ' '.join(self._subj))
        if self.hasCondition(): buff += 'Conditions (n={}): {}\n'.format(len(self._cond), ' '.join(self._cond))
        buff += 'Observations ({} scans):\n'.format(self.getTotalObsCount())
        for key in self._obs:
            if key[0] == 0: group = ''
            else: group = self._group[key[0]]
            if key[1] == 0: subj = ''
            else: subj = self._subj[key[1]]
            if key[2] == 0: cond = ''
            else: cond = self._cond[key[2]]
            k = ' '.join([s for s in (group, subj, cond) if s != ''])
            buff += '  {}:\n'.format(k)
            for filename in self._obs[key]:
                buff += '    {}'.format(basename(filename))
        buff += 'Design matrix:'
        if self._design is None: buff += '  Empty'
        else:
            for i in range(self._design.shape[0]):
                l = ''
                for j in range(self._design.shape[1]):
                    l += '{:4.1f}'.format(self._design[i, j])
                buff += l + '\n'
        return buff

    def __repr__(self) -> str:
        return 'SisypheDesign instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Private method

    def _calcDesign(self) -> None:
        r = self.getTotalObsCount()
        columns = list()
        self._cdesign = list()
        # Model Groups, Subjects, Conditions
        if self.hasGroup() and self.hasSubject() and self.hasCondition():
            t = 0
            group = [0] * len(self._group)
            subj = [0] * len(self._subj)
            for i in range(len(self._group)):
                for j in range(len(self._subj)):
                    for k in range(len(self._cond)):
                        if (i, j, k) in self._obs:
                            c = len(self._obs[(i, j, k)])
                            column = zeros((r, 1))
                            column[t:t + c] = ones((c, 1))
                            columns.append(column)
                            t += c
                            group[i] += c
                            subj[j] += c
                            self._cdesign.append([self._cond[k], 2])
            if self._fmri:
                # Copy dummy columns for boxcar model
                for i in range(len(columns)):
                    c = columns[i].copy()
                    columns.append(c)
                    self._cdesign.append([self._cond[i], 0])
            t = 0
            for i in range(len(subj)):
                c = subj[i]
                column = zeros((r, 1))
                column[t:t + c] = ones((c, 1))
                columns.append(column)
                t += c
                self._cdesign.append([self._subj[i], 0])
            t = 0
            for i in range(len(group)):
                c = group[i]
                column = zeros((r, 1))
                column[t:t + c] = ones((c, 1))
                columns.append(column)
                t += c
                self._cdesign.append([self._group[i], 0])
        # Model Subjects, Conditions
        elif not self.hasGroup() and self.hasSubject() and self.hasCondition():
            t = 0
            subj = [0] * len(self._subj)
            for j in range(len(self._subj)):
                for k in range(len(self._cond)):
                    if (0, j, k) in self._obs:
                        c = len(self._obs[(0, j, k)])
                        column = zeros((r, 1))
                        column[t:t + c] = ones((c, 1))
                        columns.append(column)
                        t += c
                        subj[j] += c
                        self._cdesign.append([self._cond[k], 2])
            if self._fmri:
                # Copy dummy columns for boxcar model
                for i in range(len(columns)):
                    c = columns[i].copy()
                    columns.append(c)
                    self._cdesign.append([self._cond[i], 0])
            t = 0
            for i in range(len(subj)):
                c = subj[i]
                column = zeros((r, 1))
                column[t:t + c] = ones((c, 1))
                columns.append(column)
                t += c
                self._cdesign.append([self._subj[i], 0])
        # Model Conditions
        elif not self.hasGroup() and not self.hasSubject() and self.hasCondition():
            t = 0
            for k in range(len(self._cond)):
                if (0, 0, k) in self._obs:
                    c = len(self._obs[(0, 0, k)])
                    column = zeros((r, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append([self._cond[k], 2])
            if self._fmri:
                # Copy dummy columns for boxcar model
                for i in range(len(columns)):
                    c = columns[i].copy()
                    columns.append(c)
                    self._cdesign.append([self._cond[i], 0])
        # model Groups
        elif self.hasGroup() and not self.hasSubject() and not self.hasCondition():
            t = 0
            for i in range(len(self._group)):
                if (i, 0, 0) in self._obs:
                    c = len(self._obs[(i, 0, 0)])
                    column = zeros((r, 1))
                    column[t:t + c] = ones((c, 1))
                    columns.append(column)
                    t += c
                    self._cdesign.append([self._group[i], 2])
        elif not self.hasGroup() and not self.hasSubject() and not self.hasCondition():
            column = ones((r, 1))
            columns.append(column)
            self._cdesign.append(['Global', 0])
        self._design = column_stack(columns)

    def _signalNormalization(self,
                             obs: list[sc.sisypheVolume.SisypheVolume],
                             mask: sc.sisypheVolume.SisypheVolume,
                             roi: sc.sisypheROI.SisypheROI,
                             wait: DialogWait | None = None):
        if self._norm > 0:
            if wait is not None:
                wait.setInformationText('Signal normalization...')
                wait.setProgressRange(0, len(obs))
                wait.progressVisibilityOn()
            ancova = list()
            npmask = mask.getNumpy().flatten()
            if self._norm in (1, 2, 3, 7, 8, 9):
                for img in obs:
                    if wait is not None: wait.incCurrentProgressValue()
                    np = img.getNumpy().flatten()
                    if self._norm in (1, 7): ancova.append(np[npmask > 0].mean())
                    elif self._norm in (2, 8): ancova.append(median(np[npmask > 0]))
                    elif self._norm in (3, 9): ancova.append(percentile(np[npmask > 0], 75))
            elif self._norm in (4, 5, 6, 10, 11, 12):
                nproi = roi.getNumpy().flatten()
                nproi = nproi * npmask
                for img in obs:
                    if wait is not None: wait.incCurrentProgressValue()
                    np = img.getNumpy().flatten()
                    if self._norm in (1, 7): ancova.append(np[nproi > 0].mean())
                    elif self._norm in (2, 8): ancova.append(median(np[nproi > 0]))
                    elif self._norm in (3, 9): ancova.append(percentile(np[nproi > 0], 75))
            ancova = array(ancova)
            if self._norm in range(7):
                # vector of proportional scaling normalization
                ancova = 100 / ancova
            if wait is not None: wait.progressVisibilityOff()
            return ancova

    # Public methods

    def hasFilename(self) -> bool:
        return self._filename != ''

    def getFilename(self) -> str:
        path, ext = splitext(self._filename)
        self._filename = path + self._MODELEXT
        return self._filename

    def getDirname(self) -> str:
        return dirname(self._filename)

    def getBasename(self) -> str:
        return basename(self._filename)

    def setFilename(self, filename: str) -> None:
        path, ext = splitext(filename)
        filename = path + self._MODELEXT
        self._filename = filename

    def setfMRIDesign(self) -> None:
        self._fmri = True

    def isfMRIDesign(self) -> bool:
        return self._fmri

    def addGroup(self, name: str | None = None) -> None:
        if name is None: name = 'Group{:d}'.format(len(self._group) + 1)
        if name not in self._group: self._group.append(name)

    def addSubject(self, name: str | None = None) -> None:
        if name is None: name = 'Subject{:d}'.format(len(self._subj) + 1)
        if name not in self._subj:  self._subj.append(name)

    def addCondition(self, name: str | None = None) -> None:
        if name is None: name = 'Condition{:d}'.format(len(self._cond) + 1)
        if name not in self._cond:  self._cond.append(name)

    def setGroupName(self, index: int, name: str) -> None:
        if isinstance(index, int):
            if 0 <= index < len(self._group): self._group[index] = name
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._group)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setSubjectName(self, index: int, name: str) -> None:
        if isinstance(index, int):
            if 0 <= index < len(self._subj): self._subj[index] = name
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._subj)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setConditionName(self, index: int, name: str) -> None:
        if isinstance(index, int):
            if 0 <= index < len(self._cond): self._cond[index] = name
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._cond)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getGroupName(self, index: int) -> str:
        if isinstance(index, int):
            if 0 <= index < len(self._group): return self._group[index]
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._group)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getSubjectName(self, index: int) -> str:
        if isinstance(index, int):
            if 0 <= index < len(self._subj): return self._subj[index]
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._subj)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def getConditionName(self, index: int) -> str:
        if isinstance(index, int):
            if 0 <= index < len(self._cond): return self._cond[index]
            else: raise ValueError('index parameter value {} is out of range [0...{}]'.format(index, len(self._cond)-1))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def hasGroup(self) -> bool:
        return len(self._group) > 0

    def hasSubject(self) -> bool:
        return len(self._subj) > 0

    def hasCondition(self) -> bool:
        return len(self._cond) > 0

    def getGroupCount(self) -> int:
        return len(self._group)

    def getSubjectCount(self) -> int:
        return len(self._subj)

    def getConditionCount(self) -> int:
        return len(self._cond)

    def getObsCount(self,
                    group: str | None = None,
                    subj: str | None = None,
                    cond: str | None = None) -> int:
        if group is None: g = 0
        else: g = self._group.index(group)
        if subj is None: s = 0
        else: s = self._subj.index(subj)
        if cond is None: c = 0
        else: c = self._cond.index(cond)
        return len(self._obs[(g, s, c)])

    def getTotalObsCount(self) -> int:
        c = 0
        for k in self._obs:
            c = c + len(self._obs[k])
        return c

    def getBetaInformations(self) -> list[list[str, int]]:
        return self._cdesign

    def addObsTo(self,
                 obs: list[str],
                 group: str | None = None,
                 subj: str | None = None,
                 cond: str | None = None) -> None:
        if group is None: g = 0
        else: g = self._group.index(group)
        if subj is None: s = 0
        else: s = self._subj.index(subj)
        if cond is None: c = 0
        else: c = self._cond.index(cond)
        key = (g, s, c)
        if key not in self._obs: self._obs[key] = list()
        for o in obs: self._obs[key].append(o)

    def addDummyObsTo(self,
                      n: int,
                      group: str | None = None,
                      subj: str | None = None,
                      cond: str | None = None) -> None:
        if group is None: g = 0
        else: g = self._group.index(group)
        if subj is None: s = 0
        else: s = self._subj.index(subj)
        if cond is None: c = 0
        else: c = self._cond.index(cond)
        key = (g, s, c)
        if key not in self._obs: self._obs[key] = list()
        for i in range(n): self._obs[key].append('dummy')

    def addHRFBoxCarModelToCondition(self,
                                     cond: str,
                                     first: int,
                                     nactive: int,
                                     nrest: int,
                                     nblocks: int,
                                     iscan: float) -> None:
        # cond = condition name (must be in self._cond)
        if self._design is None: self._calcDesign()
        if self.hasCondition():
            model = getBoxCarModel(first, nactive, nrest, nblocks)
            model = convolveModelHRF(model, iscan)
            for i in range(len(self._cdesign)):
                if self._cdesign[i][1] == 0 and self._cdesign[i][0] == cond:
                    n = self._design[:, i].sum()
                    if n == len(model):
                        v = self._design[:, i]
                        idx = int(where(v == 1)[0])
                        vmodel = zeros([n, ])
                        vmodel[idx:idx + n] = model
                        self._design[:, i] = vmodel
                    else: raise ValueError('model element count {} '
                                           'is not the same as observation count {}.'.format(len(model), n))

    def addHighPassToCondition(self,
                               cond: str,
                               nscans: int,
                               nblocks: int) -> None:
        """
            cond    str, condition name (must be in self._cond)
            nscans  int, image count in condition
            nblocks int, block count (1 block = 1 active block + 1 rest block)
        """
        if self._design is None: self._calcDesign()
        if self.hasCondition():
            hpass = getHighPass(nscans, nblocks)
            for i in range(len(self._cdesign)):
                if self._cdesign[i][0] == cond:
                    n = self._design[:, i].sum()
                    if n == len(hpass):
                        v = self._design[:, i]
                        n = len(v)
                        idx = int(where(v == 1)[0])
                        vhpass = zeros([n, ])
                        vhpass[idx:idx + n] = hpass
                        vhpass = vhpass.reshape(n, 1)
                        self._design = append(self._design, vhpass, axis=1)
                        cname = '{} {}'.format('Highpass', self._cdesign[i][0])
                        self._cdesign.append((cname, 0))
                    else: raise ValueError('High pass element count {}'
                                           ' is not the same as observation count {}.'.format(len(hpass), n))

    def addGlobalCovariable(self,
                            name: str,
                            cov: ndarray,
                            estimable: int = 0) -> None:
        if self._design is None: self._calcDesign()
        n = self.getTotalObsCount()
        if len(cov) == n:
            cov = cov.reshape(n, 1)
            self._design = append(self._design, cov, axis=1)
            self._cdesign.append((name, estimable))

    def addCovariableByGroup(self,
                             name: str,
                             cov: ndarray,
                             estimable: int = 0) -> None:
        if self._design is None: self._calcDesign()
        if self.hasGroup():
            n = self.getTotalObsCount()
            if len(cov) == n:
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._group:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape(n, 1)
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        self._cdesign.append((cname, estimable))
            else: raise ValueError('element count in covariable {} is not same '
                                   'as observation count {}.'.format(len(cov), n))
        else: raise ValueError('No group in model.')

    def addCovariableBySubject(self,
                               name: str,
                               cov: ndarray,
                               estimable: int = 0) -> None:
        if self._design is None: self._calcDesign()
        if self.hasSubject():
            n = self.getTotalObsCount()
            if len(cov) == n:
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._subj:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape(n, 1)
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        self._cdesign.append((cname, estimable))
            else: raise ValueError('element count in covariable {} is not same '
                                   'as observation count {}.'.format(len(cov), n))
        else: raise ValueError('No subject in model.')

    def addCovariableByCondition(self,
                                 name: str,
                                 cov: ndarray,
                                 estimable: int = 0) -> None:
        if self._design is None: self._calcDesign()
        if self.hasCondition():
            n = self.getTotalObsCount()
            if len(cov) == n:
                for i in range(len(self._cdesign)):
                    if self._cdesign[i][0] in self._cond:
                        cov2 = self._design[:, i] * cov
                        cov2 = cov2.reshape(n, 1)
                        self._design = append(self._design, cov2, axis=1)
                        cname = '{} {}'.format(name, self._cdesign[i][0])
                        self._cdesign.append((cname, estimable))
            else: raise ValueError('element count in covariable {} is not same '
                                   'as observation count {}.'.format(len(cov), n))
        else: raise ValueError('No subject in model.')

    def setAncovaGlobal(self) -> None:
        self._ancova = 0

    def setAncovaByGroup(self) -> None:
        if self.hasGroup(): self._ancova = 1
        else: self._ancova = 0

    def setAncovaBySubject(self) -> None:
        if self.hasSubject(): self._ancova = 2
        else: self._ancova = 0

    def setAncovaByCondition(self) -> None:
        if self.hasCondition(): self._ancova = 3
        else: self._ancova = 0

    def getDesign(self) -> ndarray:
        if self._design is None: self._calcDesign()
        return self._design

    def estimate(self,
                 mask: sc.sisypheVolume.SisypheVolume | None = None,
                 roi: sc.sisypheROI.SisypheROI | None = None,
                 wait: DialogWait | None = None) -> None:
        if self._design is not None:
            if wait is not None:
                wait.setInformationText('Open volumes')
            # Open volumes
            obs = list()
            for key in self._obs:
                for filename in self._obs[key]:
                    if wait is not None: wait.setInformationText('Open {}'.format(basename(filename)))
                    if exists(filename):
                        v = sc.sisypheVolume.SisypheVolume()
                        v.load(filename)
                        obs.append(filename)
                    else: raise IOError('No such file {}'.format(filename))
            # Calc mask
            if mask is None:
                if wait is not None: wait.setInformationText('Calc mask...')
                mask = self.calcMask(obs)
            # Signal normalization ANCOVA
            ancova = None
            if self._norm > 0:
                if roi is None and self._norm in (4, 5, 6, 10, 11, 12): self._norm -= 3
                ancova = self._signalNormalization(obs, mask, roi, wait=wait)
                # ANCOVA normalization
                if self._norm in range(7, 13):
                    if self._ancova == 1: self.addCovariableByGroup('Ancova', ancova, estimable=0)
                    elif self._ancova == 2: self.addCovariableBySubject('Ancova', ancova, estimable=0)
                    elif self._ancova == 3: self.addCovariableByCondition('Ancova', ancova, estimable=0)
                    else: self.addGlobalCovariable('Ancova', ancova, estimable=0)
            # Model estimation
            beta, variance, error = modelEstimate(obs, self._design, mask, scale=ancova, wait=wait)
            # Autocorrelations estimation
            if wait is not None: wait.setInformationText('Estimation of spatial autocorrelations...')
            self._autocorr = autocorrelationsEstimate(error, self._design, mask)
            # beta numpy.ndarray to SisypheVolume
            if wait is not None: wait.setInformationText('Save beta volume...')
            spacing = obs[0].getSpacing()
            size = obs[0].getSize()
            beta = beta.reshape((size[2], size[1], size[0], beta.shape[1]))
            variance = variance.reshape((size[2], size[1], size[0]))
            self._beta = sc.sisypheVolume.SisypheVolume()
            self._beta.copyFromNumpyArray(beta, spacing=spacing)
            self._beta.acquisition.setAutoCorrelations(self._autocorr)
            self._beta.acquisition.setModalityToOT()
            self._beta.acquisition.setSequence('Beta')
            # variance numpy.ndarray to SisypheVolume
            if wait is not None: wait.setInformationText('Save pooled variance volume...')
            self._variance = sc.sisypheVolume.SisypheVolume()
            self._variance.copyFromNumpyArray(variance, spacing=spacing)
            self._variance.acquisition.setAutoCorrelations(self._autocorr)
            self._variance.acquisition.setModalityToOT()
            self._variance.acquisition.setSequence('Pooled variance')

    def getBeta(self) -> sc.sisypheVolume.SisypheVolume | None:
        if self.isEstimated():
            return self._beta

    def getPooledVariance(self) -> sc.sisypheVolume.SisypheVolume | None:
        if self.isEstimated():
            return self._variance

    def isEstimated(self) -> bool:
        return self._beta is not None and \
               self._variance is not None and \
               self._autocorr is not None

    def parseXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                # Parse observations
                elements = root.GetElementsByTagName('obs')
                n = len(elements)
                if n > 0:
                    for element in elements:
                        k = element.getAttribute('key')
                        key = k.split()
                        if element.firstChild:
                            self._obs[key] = element.firstChild.data
                # Parse group names
                element = root.GetElementsByTagName('groups')
                if element.firstChild:
                    v = element.firstChild.data
                    if v != '': self._group = v.split(' ')
                    else: self._group = list()
                # Parse subject names
                element = root.GetElementsByTagName('subjects')
                if element.firstChild:
                    v = element.firstChild.data
                    if v != '': self._subj = v.split(' ')
                    else: self._subj = list()
                # Parse condition names
                element = root.GetElementsByTagName('conditions')
                if element.firstChild:
                    v = element.firstChild.data
                    if v != '': self._cond = v.split(' ')
                    else: self._cond = list()
                # Parse beta information
                elements = root.GetElementsByTagName('beta')
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
                elements = root.GetElementsByTagName('row')
                n = len(elements)
                if n > 0:
                    buff = [[]] * n
                    for element in elements:
                        i = int(element.getAttribute('index'))
                        if element.firstChild:
                            v = element.firstChild.data
                            v = v.split(' ')
                            v = array([float(j) for j in v])
                            buff[i] = v
                    self._design = stack(buff)
            else: raise IOError('XML file format is not supported.')

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            # Observations
            obs = doc.createElement('observations')
            root.appendChild(obs)
            for key in self._obs:
                node = doc.createElement('obs')
                node.setAttribute('key', ' '.join(key))
                txt = doc.createTextNode(obs[key])
                node.appendChild(txt)
                obs.appendChild(node)
            # Groups
            item = doc.createElement('groups')
            root.appendChild(item)
            if len(self._group) > 0: buff = ' '.join(self._group)
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Subjects
            item = doc.createElement('subjects')
            root.appendChild(item)
            if len(self._subj) > 0: buff = ' '.join(self._subj)
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Conditions
            item = doc.createElement('conditions')
            root.appendChild(item)
            if len(self._cond) > 0: buff = ' '.join(self._cond)
            else: buff = ''
            txt = doc.createTextNode(buff)
            item.appendChild(txt)
            # Beta information
            beta = doc.createElement('betas')
            root.appendChild(beta)
            for i in range(len(self._cdesign)):
                node = doc.createElement('beta')
                name, estim = self._cdesign[i]
                node.setAttribute('column', str(i))
                node.setAttribute('name', name)
                node.setAttribute('estim', str(estim))
                beta.appendChild(node)
            # Design matrix
            design = doc.createElement('design')
            root.appendChild(design)
            for i in range(self._design.shape[0]):  # rows
                node = doc.createElement('row')
                node.setAttribute('index', str(i))
                v = list(self._design[i, :])
                v = ' '.join([str(i) for i in v])
                txt = doc.createTextNode(v)
                node.appendChild(txt)
                design.appendChild(node)

    def load(self, filename: str) -> None:
        path, ext = splitext(filename)
        filename = path + self._FILELEXT
        if exists(filename):
            # Load XML
            doc = minidom.parse(filename)
            self.parseXML(doc)
            # Load beta
            from Sisyphe.core.sisypheVolume import SisypheVolume
            self._beta = SisypheVolume()
            self._beta.setFilename(filename)
            self._beta.setFilenamePrefix('beta_')
            self._beta.load()
            # Load variance
            self._variance = SisypheVolume()
            self._variance.setFilename(filename)
            self._variance.setFilenamePrefix('sig2_')
            self._variance.load()
        else: raise IOError('No such file {}'.format(filename))

    def save(self) -> None:
        if self.hasFilename():
            filename = self.getFilename()
            # Save beta
            if self._beta is not None:
                self._beta.setFilename(filename)
                self._beta.setFilenamePrefix('beta_')
                self._beta.save()
            # Save variance
            if self._variance is not None:
                self._variance.setFilename(filename)
                self._variance.setFilenamePrefix('sig2_')
                self._variance.save()
            # Save xml
            doc = minidom.Document()
            self.createXML(doc)
            buff = doc.toprettyxml()
            f = open(filename, 'w')
            try: f.write(buff)
            except IOError: raise IOError('XML file write error.')
            finally: f.close()
        else: raise AttributeError('No model filename.')

    def saveAs(self, filename: str) -> None:
        self.setFilename(filename)
        self.save()


"""
    Test
"""

if __name__ == '__main__':
    fb = SisypheDesign()
    fb.addGroup('Groupe1')
    fb.addGroup('Groupe2')
    fb.addSubject('Sujet1')
    fb.addSubject('Sujet2')
    fb.addSubject('Sujet3')
    fb.addSubject('Sujet4')
    fb.addSubject('Sujet5')
    fb.addSubject('Sujet6')
    fb.addCondition('Activation')
    fb.addCondition('Repos')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet1', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet2', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet3', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet4', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet5', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet6', 'Activation')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet1', 'Repos')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet2', 'Repos')
    fb.addObsTo([0] * 2, 'Groupe1', 'Sujet3', 'Repos')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet4', 'Repos')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet5', 'Repos')
    fb.addObsTo([0] * 2, 'Groupe2', 'Sujet6', 'Repos')
    print(fb.getDesign())
