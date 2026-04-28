"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
"""

from multiprocessing import cpu_count
from multiprocessing import Pool
from multiprocessing import Manager

from numpy import pi
from numpy import exp
from numpy import angle
from numpy import arccos
from numpy import nan_to_num
from numpy import zeros
from numpy import ones
from numpy import array
from numpy import ndarray

from time import time

from Sisyphe.lib.tgvqsm.qsm_tgv_main import get_laplace_phase3
from Sisyphe.lib.tgvqsm.qsm_tgv_cython import qsm_tgv

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException


__all__ = ['B0DblEchoMap',
           'B1DblTRMap',
           'B1GEDblAngleMap',
           'B1SEDblAngleMap',
           'T1MultiTRMap',
           'T1MultiAngleMap',
           'T2MonoExpMap',
           'T2BiExpMap',
           'T2primeMap',
           'MTRMap',
           'QSMMap',
           'phaseRescaling']

"""
functions
~~~~~~~~~

    - B0DblEchoMap
    - B1DblTRMap
    - B1GEDblAngleMap
    - B1SEDblAngleMap
    - T1MultiTRMap
    - T1MultiAngleMap
    - T2MonoExpMap
    - T2BiExpMap
    - T2primeMap
    - MTRMap
    - QSMMap
    - phaseRescaling
"""


def B0DblEchoMap(phse: tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume],
                 mask: SisypheVolume | None,
                 te : tuple[float, float] | list[float],
                 rescaling : bool) -> SisypheVolume:
    """
    B0 main static magnetic field map (in Hz) processing using the phase difference between two echoes.

    Code adapted from https://github.com/lamyj/erwin

    Reference:
    An in vivo automated shimming method taking into account shim current constraints. Wen H. & Jaffer F.A.
    Magn Reson Med. 1995 34(6),pp.898-904.

    Parameters
    ----------
    phse : tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume]
        two phase volumes acquired with short and long echo time
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0
    te : tuple[float, float] | list[float]
        short and long echo time in ms
    rescaling : bool
        if True, rescaling phase data from -4096.4096 (Siemens) to -pi...pi

    Returns
    -------
    SisypheVolume
        B0 map
    """
    # if rescaling: phse2 = [(v.getNumpy() / 4096.0) * pi for v in phse]
    if rescaling: phse2 =[phaseRescaling(v).getNumpy() for v in phse]
    else: phse2 = [v.getNumpy() for v in phse]
    S = [exp(1j * p) for p in phse2]
    delta = S[1] * S[0].conj()
    delta = angle(delta)
    deltaTE = (te[1] - te[0]) / 1000.0 # in s
    B0 = delta / (2 * pi * deltaTE)
    B0 = nan_to_num(B0, nan=0.0, posinf=0.0, neginf=0.0)
    if mask is not None: B0 *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(B0,
                         spacing=phse[0].getSpacing(),
                         origin=phse[0].getOrigin(),
                         direction=phse[0].getDirections())
    r.copyAttributesFrom(phse[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToB0Map()
    r.setFilename(phse[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.B0MAP)
    return r


def B1DblTRMap(img: tuple[SisypheVolume, SisypheVolume],
               mask: SisypheVolume | None,
               tr : tuple[float, float] | list[float]) -> SisypheVolume:
    """
    B1 radiofrequency (RF) coil map processing from two-pulse spoiled gradient echo with short and long TR.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Actual flip-angle imaging in the pulsed steady state: a method for rapid three-dimensional mapping of the
    transmitted radiofrequency field. Yarnykh V.L. Magn Reson Med. 2007 57:192-200.

    Parameters
    ----------
    img : tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume]
        two gradient echo volumes acquired with short and long TR
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0
    tr : tuple[float, float] | list[float]
        short and long TR in ms

    Returns
    -------
    SisypheVolume
        B1 map
    """
    iratio = img[1].getNumpy() / img[0].getNumpy()
    nratio = tr[1] / tr[0]
    B1 = arccos((iratio * nratio - 1) / (nratio - iratio))
    B1 = nan_to_num(B1, nan=0.0, posinf=0.0, neginf=0.0)
    if mask is not None: B1 *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(B1,
                         spacing=img[0].getSpacing(),
                         origin=img[0].getOrigin(),
                         direction=img[0].getDirections())
    r.copyAttributesFrom(img[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToB1Map()
    r.setFilename(img[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.B1MAP)
    return r


def B1GEDblAngleMap(img: tuple[SisypheVolume, SisypheVolume],
                    mask: SisypheVolume | None,
                    theta: float) -> SisypheVolume:
    """
    B1 radiofrequency (RF) coil map processing from two gradient echo images using the double angle method (actual
    flip angle imaging AFI).

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Mapping of the radiofrequency field. Insko E.K. & Bolinger L. J Magn Reson Imaging. 1993 Series A, 103:82-85.

    Parameters
    ----------
    img : tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume]

        - first gradient echo volume acquired with flip angle theta
        - second gradient echo volume acquired with flip angle 2 x theta
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0
    theta : float
        filp angle in degrees

    Returns
    -------
    SisypheVolume
        B1 map
    """
    iratio = img[0].getNumpy() / img[1].getNumpy()
    thetam = arccos(0.5 * (1.0 / iratio))
    B1 = thetam / (pi * (theta / 180.0))
    B1 = nan_to_num(B1, nan=0.0, posinf=0.0, neginf=0.0)
    if mask is not None: B1 *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(B1,
                         spacing=img[0].getSpacing(),
                         origin=img[0].getOrigin(),
                         direction=img[0].getDirections())
    r.copyAttributesFrom(img[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToB1Map()
    r.setFilename(img[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.B1MAP)
    return r


def B1SEDblAngleMap(img: tuple[SisypheVolume, SisypheVolume],
                    mask: SisypheVolume | None,
                    theta: float,
                    sequence: str = 't180') -> SisypheVolume:
    """
    B1 radiofrequency (RF) coil map processing from two spin echo images using the double angle method (AFI).

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Mapping of the radiofrequency field. Insko E.K. & Bolinger L. J Magn Reson Imaging. 1993 Series A, 103:82-85.

    Parameters
    ----------
    img : tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume]

        - first gradient echo volume acquired with flip angle theta
        - second gradient echo volume acquired with flip angle 2 x theta
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0
    theta : float
        flip angle in degrees
    sequence : str (optional)

        type of spin echo sequence
            - 't180':   theta - TE/2 - 180 - TE/2 - acquisition (default)
            - 't2t':    theta - TE/2 - 2 theta - TE/2 - acquisition

    Returns
    -------
    SisypheVolume
        B1 map
    """
    iratio = img[0].getNumpy() / img[1].getNumpy()
    if sequence == 't180': mtheta = arccos(0.5 * (1.0 / iratio))
    else: mtheta = arccos(0.5 * ((1.0 / iratio) ** (1/3)))
    B1 = mtheta / (pi * theta / 180.0)
    B1 = nan_to_num(B1, nan=0.0, posinf=0.0, neginf=0.0)
    if mask is not None: B1 *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(B1,
                         spacing=img[0].getSpacing(),
                         origin=img[0].getOrigin(),
                         direction=img[0].getDirections())
    r.copyAttributesFrom(img[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToB1Map()
    r.setFilename(img[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.B1MAP)
    return r


def T1MultiTRMap(img: list[SisypheVolume] | SisypheVolumeCollection,
                 mask: SisypheVolume | None,
                 tr: list[float] | ndarray,
                 te: list[float] | ndarray,
                 wait: DialogWait | None = None) -> SisypheVolume:
    """
    Voxel-wise mono-exponential T1 fitting on spin echo volumes at variable TR (VTR).

    Usual brain values:

    - T1 gray matter    1516 +/- 39
    - T1 white matter   1046 +/- 29

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Parameters
    ----------
    img : list[SisypheVolume] | SisypheVolumeCollection
        spin echo volumes at variable TR
    mask : SisypheVolume | None
        analysis mask, voxels outisde mask are set to 0.0
    tr : list[float] | ndarray
        TR values in ms
    te : list[float] | ndarray
        TE values in ms
    wait : DialogWait | None (optional)
        progress dialog (default None)

    Returns
    -------
    SisypheVolume
        T1 map
    """
    if isinstance(img, list):
        mimg = SisypheVolumeCollection()
        mimg.copyFromList(img)
    elif isinstance(img, SisypheVolumeCollection):
        mimg = img
    # noinspection PyUnboundLocalVariable
    buff = mimg.copyToMultiComponentSisypheVolume()
    img = buff.getNumpy(defaultshape=False)
    if isinstance(tr, list): tr = array(tr)
    # corrected TR values = TR - TE/2
    tr = tr - te / 2.0
    ncpu = cpu_count() - 1
    t1 = zeros(img.shape[:3], 'float64')
    if mask is None: msk = ones(img.shape[:3],'float64')
    else: msk = mask.getNumpy(defaultshape=False)
    inputlist = []
    if ncpu > 1:
        if wait is not None:
            wait.setInformationText('VTR T1 map processing initialization...')
        with Manager() as manager:
            mng = manager.dict()
            # mng['acc'] = 0
            mng['acc'] = manager.list([0] * img.shape[2])
            for z in range(0, img.shape[2]):
                sliceinfo = [img[:, :, z, :], tr, msk[:, :, z], z, mng]
                inputlist.append(sliceinfo)
            fitpool = Pool(processes=ncpu)
            # noinspection PyProtectedMember, PyUnresolvedReferences
            fitpool_pids_initial = [proc.pid for proc in fitpool._pool]
            from Sisyphe.lib.myrelax.getT1VTR import TxyFitMEslice
            fitresults = fitpool.map_async(TxyFitMEslice, inputlist)
            if wait is not None:
                wait.setInformationText('VTR T1 map processing...')
                wait.setProgressRange(0, img.shape[0] * img.shape[2])
                wait.setCurrentProgressValue(0)
                wait.buttonVisibilityOn()
                wait.progressVisibilityOn()
            while not fitresults.ready():
                if wait is not None:
                    wait.messageFromDictProxyManager(mng)
                    if wait.getStopped():
                        fitpool.terminate()
                        raise UserAbortException
                # noinspection PyProtectedMember, PyUnresolvedReferences
                fitpool_pids_new = [proc.pid for proc in fitpool._pool]
                if fitpool_pids_new != fitpool_pids_initial:
                    fitpool.terminate()
                    raise RuntimeError
        if wait is not None:
            wait.setCurrentProgressValue(wait.getProgressMaximum())
            wait.buttonVisibilityOff()
        fitlist = fitresults.get()
        for k in range(0,img.shape[2]):
            fitslice = fitlist[k]
            slicepos = fitslice[4]
            t1[:, :, slicepos] = fitslice[1]
    # < Revision 03/04/2026
    t1 = nan_to_num(t1, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t1[t1 < 0.0] = 0.0
    t1[t1 > 100000.0] = 100000.0
    # Revision 03/04/2026 >
    r = SisypheVolume()
    r.copyFromNumpyArray(t1,
                         spacing=mimg[0].getSpacing(),
                         origin=mimg[0].getOrigin(),
                         direction=mimg[0].getDirections(),
                         defaultshape=False)
    r.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToT1Map()
    r.acquisition.setUnitToMillisecond()
    r.display.setWindow(0.0, 25000.0)
    r.setFilename(mimg[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.T1MAP)
    if wait is not None: wait.progressVisibilityOff()
    return r


def T1MultiAngleMap(img: list[SisypheVolume] | SisypheVolumeCollection,
                    mask: SisypheVolume | None,
                    b1: SisypheVolume | None,
                    angl: list[float] | ndarray,
                    tr : float,
                    algo : str = 'l',
                    wait: DialogWait | None = None) -> SisypheVolume:
    """
    Voxel-wise mono-exponential T1 fitting for variable flip angle (VFA) volumes.

    Usual brain values:

    - T1 gray matter    1516 +/- 39
    - T1 white matter   1046 +/- 29

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Parameters
    ----------
    img : list[SisypheVolume] | SisypheVolumeCollection
        volumes at variable flip angle
    mask : SisypheVolume | None (optional)
        mask of analysis, voxels outisde mask are set to 0.0
    b1 : SisypheVolume | None (optional)
        B1 map
    angl : list[float] | ndarray
        flip angle values in degrees
    tr : float
        TR value in ms
    algo : str (optional)
        'l' linear (default) or 'nl' non-linear
    wait : DialogWait | None (optional)
        progress dialog (default None)

    Returns
    -------
    SisypheVolume
        T1 map
    """
    if isinstance(img, list):
        mimg = SisypheVolumeCollection()
        mimg.copyFromList(img)
    elif isinstance(img, SisypheVolumeCollection):
        mimg = img
    # noinspection PyUnboundLocalVariable
    buff = mimg.copyToMultiComponentSisypheVolume()
    img = buff.getNumpy(defaultshape=False)
    if algo in ('l', 'L', 'linear', 'LINEAR'): algo = 'linear'
    elif algo in ('nl', 'NL', 'nonlinear', 'NONLINEAR'): algo = 'nonlinear'
    else: algo = 'linear'
    if isinstance(angl, list): angl = array(angl)
    tr = array(tr)
    ncpu = cpu_count() - 1
    t1 = zeros(img.shape[:3], 'float64')
    if mask is None: msk = ones(img.shape[:3],'float64')
    else: msk = mask.getNumpy(defaultshape=False)
    if b1 is None: b = ones(img.shape[:3],'float64')
    else: b = b1.getNumpy(defaultshape=False)
    inputlist = []
    if ncpu > 1:
        if wait is not None:
            wait.setInformationText('VFA T1 map processing initialization...')
        with Manager() as manager:
            mng = manager.dict()
            # mng['acc'] = 0
            mng['acc'] = manager.list([0] * img.shape[2])
            for z in range(0, img.shape[2]):
                sliceinfo = [img[:, :, z, :], angl, tr, algo, msk[:, :, z], b[:, :, z], z, mng]
                inputlist.append(sliceinfo)
            fitpool = Pool(processes=ncpu)
            # noinspection PyProtectedMember, PyUnresolvedReferences
            fitpool_pids_initial = [proc.pid for proc in fitpool._pool]
            from Sisyphe.lib.myrelax.getT1VFA import T1FitVFAslice
            fitresults = fitpool.map_async(T1FitVFAslice, inputlist)
            if wait is not None:
                wait.setInformationText('VFA T1 map processing...')
                wait.setProgressRange(0, img.shape[0] * img.shape[2])
                wait.setCurrentProgressValue(0)
                wait.buttonVisibilityOn()
                wait.progressVisibilityOn()
            while not fitresults.ready():
                if wait is not None:
                    wait.messageFromDictProxyManager(mng)
                    if wait.getStopped():
                        fitpool.terminate()
                        raise UserAbortException
                # noinspection PyProtectedMember, PyUnresolvedReferences
                fitpool_pids_new = [proc.pid for proc in fitpool._pool]
                if fitpool_pids_new != fitpool_pids_initial:
                    fitpool.terminate()
                    raise RuntimeError
        if wait is not None:
            wait.setCurrentProgressValue(wait.getProgressMaximum())
            wait.buttonVisibilityOff()
        fitlist = fitresults.get()
        for k in range(0,img.shape[2]):
            fitslice = fitlist[k]
            slicepos = fitslice[4]
            t1[:, :, slicepos] = fitslice[1]
    # < Revision 03/04/2026
    t1 = nan_to_num(t1, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t1[t1 < 0.0] = 0.0
    t1[t1 > 100000.0] = 100000.0
    # Revision 03/04/2026 >
    r = SisypheVolume()
    r.copyFromNumpyArray(t1,
                         spacing=mimg[0].getSpacing(),
                         origin=mimg[0].getOrigin(),
                         direction=mimg[0].getDirections(),
                         defaultshape=False)
    r.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToT1Map()
    r.acquisition.setUnitToMillisecond()
    r.display.setWindow(0.0, 25000.0)
    r.setFilename(mimg[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.T1MAP)
    if wait is not None: wait.progressVisibilityOff()
    return r


def T2MonoExpMap(img: list[SisypheVolume] | SisypheVolumeCollection,
                 mask: SisypheVolume | None,
                 te: list[float] | ndarray,
                 algo : str = 'l',
                 wait: DialogWait | None = None) -> SisypheVolume:
    """
    Voxel-wise mono-exponential T2/T2* fitting on volumes at variable echo times.

    signal  =  S0 * exp(-TE/T2)

    - TE, echo time
    - S0, signal for zero TE
    - T2/T2* tissue

    Usual brain values:

    - T2* gray matter   48.5 +/- 12.1
    - T2* white matter  67.6 +/- 11.0
    - T2 gray matter    96.1 +/- 9.1
    - T2 white matter   109.8 +/- 11.4

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Parameters
    ----------
    img: list[SisypheVolume] | SisypheVolumeCollection
        volumes at variable TE
    mask : SisypheVolume | None
        analysis mask, voxels outisde mask are set to 0.0
    te : list[float] | ndarray
        TE values in ms
    algo : str (optional)
        'l' linear (default) or 'nl' non-linear
    wait : DialogWait | None (optional)
        progress dialog (default None)

    Returns
    -------
    SisypheVolume
        T2/T2* map
    """
    if isinstance(img, list):
        mimg = SisypheVolumeCollection()
        mimg.copyFromList(img)
    elif isinstance(img, SisypheVolumeCollection):
        mimg = img
    # noinspection PyUnboundLocalVariable
    buff = mimg.copyToMultiComponentSisypheVolume()
    img = buff.getNumpy(defaultshape=False)
    if algo in ('l', 'L', 'linear', 'LINEAR'): algo = 'linear'
    elif algo in ('nl', 'NL', 'nonlinear', 'NONLINEAR'): algo = 'nonlinear'
    else: algo = 'linear'
    if isinstance(te, list): te = array(te)
    ncpu = cpu_count() - 1
    t2 = zeros(img.shape[:3], 'float64')
    if mask is None: msk = ones(img.shape[:3],'float64')
    else: msk = mask.getNumpy(defaultshape=False)
    inputlist = []
    if ncpu > 1:
        if wait is not None:
            wait.setInformationText('T2 map processing initialization...')
        with Manager() as manager:
            mng = manager.dict()
            # mng['acc'] = 0
            mng['acc'] = manager.list([0] * img.shape[2])
            for z in range(0, img.shape[2]):
                sliceinfo = [img[:, :, z, :], te, algo, msk[:, :, z], z, mng]
                inputlist.append(sliceinfo)
            fitpool = Pool(processes=ncpu)
            # noinspection PyProtectedMember, PyUnresolvedReferences
            fitpool_pids_initial = [proc.pid for proc in fitpool._pool]
            from Sisyphe.lib.myrelax.getT2T2star import TxyFitMEslice
            fitresults = fitpool.map_async(TxyFitMEslice, inputlist)
            if wait is not None:
                wait.setInformationText('T2 map processing...')
                wait.setProgressRange(0, img.shape[0] * img.shape[2])
                wait.setCurrentProgressValue(0)
                wait.buttonVisibilityOn()
                wait.progressVisibilityOn()
            while not fitresults.ready():
                if wait is not None:
                    wait.messageFromDictProxyManager(mng)
                    if wait.getStopped():
                        fitpool.terminate()
                        raise UserAbortException
                # noinspection PyProtectedMember, PyUnresolvedReferences
                fitpool_pids_new = [proc.pid for proc in fitpool._pool]
                if fitpool_pids_new != fitpool_pids_initial:
                    fitpool.terminate()
                    raise RuntimeError
        if wait is not None:
            wait.setCurrentProgressValue(wait.getProgressMaximum())
            wait.buttonVisibilityOff()
        fitlist = fitresults.get()
        for k in range(0,img.shape[2]):
            fitslice = fitlist[k]
            slicepos = fitslice[4]
            t2[:, :, slicepos] = fitslice[1]
    # < Revision 03/04/2026
    t2 = nan_to_num(t2, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t2[t2 < 0.0] = 0.0
    t2[t2 > 2000.0] = 2000.0
    # Revision 03/04/2026 >
    r = SisypheVolume()
    r.copyFromNumpyArray(t2,
                         spacing=mimg[0].getSpacing(),
                         origin=mimg[0].getOrigin(),
                         direction=mimg[0].getDirections(),
                         defaultshape=False)
    r.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToT2Map()
    r.acquisition.setUnitToMillisecond()
    r.display.setWindow(0.0, 250.0)
    r.setFilename(mimg[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.T2MAP)
    if wait is not None: wait.progressVisibilityOff()
    return r,


def T2BiExpMap(img: list[SisypheVolume] | SisypheVolumeCollection,
               mask: SisypheVolume | None,
               te: list[float] | ndarray,
               lreg : float = 0.0,
               wait: DialogWait | None = None) -> tuple[SisypheVolume, SisypheVolume]:
    """
    Voxel-wise bi-exponential T2/T2* fitting on volumes at variable echo times.

    signal = S0 * f * exp(-TE/T2l) + S0 * (1 - f) * exp(-TE/T2s)

    - TE, echo time
    - S0, signal for zero TE
    - T2l, T2/T2* of the slowly-decaying water
    - T2s (T2s <= T2l), T2/T2* of fast-decaying water
    - f signal fraction of the slowly-decaying water

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Parameters
    ----------
    img: list[SisypheVolume] | SisypheVolumeCollection
        volumes at variable TE
    mask : SisypheVolume | None
        analysis mask, voxels outisde mask are set to 0.0
    te : list[float] | ndarray
        TE values in ms
    lreg : float = 0.0 (optional)
        weight of Tikhonov regularization (default 0.0, i.e. no regularization)
    wait : DialogWait | None (optional)
        progress dialog (default None)

    Returns
    -------
    tuple[SisypheVolume, SisypheVolume]
        long T2/T2* map, short T2/T2* map, long T2/T2* fraction
    """
    if isinstance(img, list):
        mimg = SisypheVolumeCollection()
        mimg.copyFromList(img)
    elif isinstance(img, SisypheVolumeCollection):
        mimg = img
    # noinspection PyUnboundLocalVariable
    buff = mimg.copyToMultiComponentSisypheVolume()
    img = buff.getNumpy(defaultshape=False)
    if isinstance(te, list): te = array(te)
    ncpu = cpu_count() - 1
    t2 = zeros(img.shape[:3], 'float64')
    t2l = zeros(img.shape[:3], 'float64')
    t2s = zeros(img.shape[:3], 'float64')
    fl = zeros(img.shape[:3], 'float64')
    if mask is None: msk = ones(img.shape[:3],'float64')
    else: msk = mask.getNumpy(defaultshape=False)
    inputlist = []
    if ncpu > 1:
        if wait is not None:
            wait.setInformationText('T2 map processing initialization...')
        with Manager() as manager:
            mng = manager.dict()
            # mng['acc'] = 0
            mng['start'] = time()
            mng['acc'] = manager.list([0] * img.shape[2])
            for z in range(0, img.shape[2]):
                sliceinfo = [img[:, :, z, :], te, msk[:, :, z], z, lreg, mng]
                inputlist.append(sliceinfo)
            fitpool = Pool(processes=ncpu)
            # noinspection PyProtectedMember, PyUnresolvedReferences
            fitpool_pids_initial = [proc.pid for proc in fitpool._pool]
            from Sisyphe.lib.myrelax.getT2T2starBiexp import FitSlice
            fitresults = fitpool.map_async(FitSlice, inputlist)
            if wait is not None:
                wait.setInformationText('T2 map processing...')
                wait.setProgressRange(0, img.shape[0] * img.shape[2])
                wait.setCurrentProgressValue(0)
                wait.buttonVisibilityOn()
                wait.progressVisibilityOn()
            while not fitresults.ready():
                if wait is not None:
                    wait.messageFromDictProxyManager(mng)
                    if wait.getStopped():
                        fitpool.terminate()
                        raise UserAbortException
                # noinspection PyProtectedMember, PyUnresolvedReferences
                fitpool_pids_new = [proc.pid for proc in fitpool._pool]
                if fitpool_pids_new != fitpool_pids_initial:
                    fitpool.terminate()
                    raise RuntimeError
        if wait is not None:
            wait.setCurrentProgressValue(wait.getProgressMaximum())
            wait.buttonVisibilityOff()
        fitlist = fitresults.get()
        for k in range(0, img.shape[2]):
            fitslice = fitlist[k]
            slicepos = fitslice[7]
            t2l[:, :, slicepos] = fitslice[1]
            fl[:, :, slicepos] = fitslice[2]
            t2s[:, :, slicepos] = fitslice[3]
            t2[:, :, slicepos] = fitslice[4]
    # < Revision 03/04/2026
    t2 = nan_to_num(t2, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t2[t2 < 0.0] = 0.0
    t2[t2 > 2000.0] = 2000.0
    t2l = nan_to_num(t2l, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t2l[t2l < 0.0] = 0.0
    t2l[t2l > 2000.0] = 2000.0
    t2s = nan_to_num(t2s, nan = 0.0, posinf = 0.0, neginf = 0.0)
    t2s[t2s < 0.0] = 0.0
    t2s[t2s > 2000.0] = 2000.0
    fl = nan_to_num(fl, nan = 0.0, posinf = 0.0, neginf = 0.0)
    fl[fl < 0.0] = 0.0
    fl[fl > 1.0] = 1.0
    # Revision 03/04/2026 >
    r = SisypheVolume()
    rlong = SisypheVolume()
    rshort = SisypheVolume()
    rf = SisypheVolume()
    r.copyFromNumpyArray(t2,
                         spacing=mimg[0].getSpacing(),
                         origin=mimg[0].getOrigin(),
                         direction=mimg[0].getDirections(),
                         defaultshape=False)
    r.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToT2Map()
    r.acquisition.setUnitToMillisecond()
    r.display.setWindow(0.0, 250.0)
    r.setFilename(mimg[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.T2MAP)
    rlong.copyFromNumpyArray(t2l,
                             spacing=mimg[0].getSpacing(),
                             origin=mimg[0].getOrigin(),
                             direction=mimg[0].getDirections(),
                             defaultshape=False)
    rlong.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    rlong.acquisition.setSequenceToT2Map()
    rlong.acquisition.setUnitToMillisecond()
    rlong.display.setWindow(0.0, 250.0)
    rlong.setFilename(mimg[0].getFilename())
    rlong.setFilenameSuffix('Long_' + SisypheAcquisition.T2MAP)
    rshort.copyFromNumpyArray(t2s,
                              spacing=mimg[0].getSpacing(),
                              origin=mimg[0].getOrigin(),
                              direction=mimg[0].getDirections(),
                              defaultshape=False)
    rshort.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    rshort.acquisition.setSequenceToT2Map()
    rshort.acquisition.setUnitToMillisecond()
    rshort.display.setWindow(0.0, 250.0)
    rshort.setFilename(mimg[0].getFilename())
    rshort.setFilenameSuffix('Short_' + SisypheAcquisition.T2MAP)
    rf.copyFromNumpyArray(fl,
                          spacing=mimg[0].getSpacing(),
                          origin=mimg[0].getOrigin(),
                          direction=mimg[0].getDirections(),
                          defaultshape=False)
    rf.copyAttributesFrom(mimg[0], display=False, slope=False, acquisition=False)
    rf.acquisition.setModalityToOT()
    rf.acquisition.setSequence('Long T2 fraction map')
    rf.acquisition.setUnitToRatio()
    rf.display.setWindow(0.0, 1.0)
    rf.setFilename(mimg[0].getFilename())
    rf.setFilenameSuffix('Fraction_' + SisypheAcquisition.T2MAP)
    if wait is not None: wait.progressVisibilityOff()
    return r, rlong, rshort, rf


def T2primeMap(t2 : SisypheVolume,
               t2s : SisypheVolume,
               mask: SisypheVolume | None) -> SisypheVolume:
    """
    T2' processing from quantitative T2 and T2* maps.
    T2' = 1 / ((1 / T2*) - (1 / T2))

    Usual brain values:

    - T2' gray matter   109.9 +/- 44.9
    - T2' white matter  170.5 +/- 99.3

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Age-dependent normal values of T2* and T2' in brain parenchyma. Siemonsen  S., Finsterbusch J., Matschke J.,
    Lorenzen A., Ding X.-Q., Fiehler J. AJNR Am J Neuroradiol. 2008 May;29(5):950-955.

    Parameters
    ----------
    t2 : SisypheVolume
        T2 map volume
    t2s : SisypheVolume
        T2* map volume
    mask: SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0

    Returns
    -------
    SisypheVolume
        T2' map
    """
    T2P = 1 / ((1 / t2s.getNumpy()) - (1 / t2.getNumpy()))
    T2P = nan_to_num(T2P, nan=0.0, posinf=0.0, neginf=0.0)
    if mask is not None: T2P *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(T2P,
                         spacing=t2.getSpacing(),
                         origin=t2.getOrigin(),
                         direction=t2.getDirections())
    r.copyAttributesFrom(t2, display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToT2primeMap()
    r.acquisition.setUnitToMillisecond()
    r.setFilename(t2.getFilename())
    r.setFilenameSuffix(SisypheAcquisition.T2PMAP)
    return r


def MTRMap(img : tuple[SisypheVolume, SisypheVolume],
           mask: SisypheVolume | None) -> SisypheVolume:
    """
    Magnetization Transfer Ratio (MTR) from MT "on" and MT "off" acquisitions.
    MTR = 100.0 * (MToff - MTon) / MToff

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    T1, T2 relaxation and magnetization transfer in tissue at 3T. Stanisz G.J. Magn Reson Med. 2005 54:507-512.

    Parameters
    ----------
    img : tuple[SisypheVolume, SisypheVolume] | list[SisypheVolume]
        MT "on" and MT "off" volumes
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0

    Returns
    -------
    SisypheVolume
        MTR map
    """
    # 100.0 * (OFF - ON) / OFF
    MTR = 100.0 * (img[1].getNumpy() - img[0].getNumpy()) / img[1].getNumpy()
    MTR = nan_to_num(MTR, nan=0.0, posinf=0.0, neginf=0.0)
    # < Revision 03/04/2026
    MTR = nan_to_num(MTR, nan = 0.0, posinf = 0.0, neginf = 0.0)
    MTR[MTR < 0.0] = 0.0
    MTR[MTR > 100.0] = 100.0
    # Revision 03/04/2026 >
    if mask is not None: MTR *= mask.getNumpy()
    r = SisypheVolume()
    r.copyFromNumpyArray(MTR,
                         spacing=img[0].getSpacing(),
                         origin=img[0].getOrigin(),
                         direction=img[0].getDirections())
    r.copyAttributesFrom(img[0], display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToMTRMap()
    r.setFilename(img[0].getFilename())
    r.setFilenameSuffix(SisypheAcquisition.MTR)
    return r


def QSMMap(img : SisypheVolume,
           mask: SisypheVolume | None,
           te : float,
           field : float,
           rescaling : bool,
           iters : int = 1000,
           alpha : tuple[float, float] = (0.0015, 0.0005),
           wait: DialogWait | None = None) -> SisypheVolume:
    """
    Quantitative Susceptibility Mapping (QSM) processing using Total Generalized Variation (TGV-QSM).

    Code adapted from TGVQSM package, https://www.neuroimaging.at/pages/qsm.php

    Reference:
    Fast Quantitative Susceptibility Mapping using 3D EPI and Total Generalized Variation. Langkammer C., Bredies K.,
    Poser B.A., Barth M., Reishofer G. Fan A.P., Bilgic B., Fazekas F., Mainero C., Ropele S.
    Neuroimage. 2015 May 1;111:622-30

    Parameters
    ----------
    img : SisypheVolume
        phase volume
    mask : SisypheVolume | None
        mask of analysis, voxels outisde mask are set to 0.0
    te : float
        echo time in ms
    field : float
        field strength
    rescaling : bool
        if True, rescaling phase data from -4096.4096 (Siemens) to -pi...pi
    iters : int (optional)
        number of iterations (default 1000)
    alpha : Tuple[float, float] (optional)
        regularization parameters (default 0.0015 & 0.0005)
    wait : DialogWait | None (optional)
        progress dialog (default None)

    Returns
    -------
    SisypheVolume
        QSM map
    """
    gamma = 42.5781
    # < Revision 27/04/2026
    if rescaling:
        # phase = (phase / 4096.0) * pi
        img = phaseRescaling(img)
    phase = img.getNumpy(defaultshape=False)
    if mask is not None:
        msk = mask.getNumpy(defaultshape=False)
        msk[msk > 0] = 1
    else: msk = ones(phase.shape, 'uint8')
    # Revision 27/04/2026 >
    te /= 1000.0 # in s
    scale = (2.0 * pi * te) * (field * gamma)
    laplace_phi0 = get_laplace_phase3(phase, img.getSpacing())
    phi = qsm_tgv(laplace_phi0, msk, array(img.getSpacing()), alpha=alpha, iterations=iters, wait=wait)
    chi = phi / scale
    r = SisypheVolume()
    r.copyFromNumpyArray(chi,
                         spacing=img.getSpacing(),
                         origin=img.getOrigin(),
                         direction=img.getDirections(),
                         defaultshape=False)
    r.copyAttributesFrom(img, display=False, slope=False, acquisition=False)
    r.acquisition.setSequenceToQSMMap()
    r.setFilename(img.getFilename())
    r.setFilenameSuffix(SisypheAcquisition.QSM)
    return r


def phaseRescaling(img : SisypheVolume) -> SisypheVolume:
    """
    Phase MR image rescaling to (-pi, +pi).

    Parameters
    ----------
    img : SisypheVolume
        MR phase image

    Returns
    -------
    SisypheVolume
        Rescaled MR phase image, signal ranges from -pi to +pi
    """
    vmin, vmax = img.getRange()
    if round(vmin, 1) != -3.1 and round(vmax, 1) != 3.1:
        r = vmax - vmin
        v = img.getNumpy()
        v = (((v - vmin) / r) * 2 * pi) - pi
        r = SisypheVolume()
        r.copyFromNumpyArray(v,
                             spacing=img.getSpacing(),
                             origin=img.getOrigin(),
                             direction=img.getDirections())
        r.copyAttributesFrom(img, display=False, slope=False)
        r.display.setWindow(-3.14, 3.14)
        return r
    else: return img