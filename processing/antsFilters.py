"""
External packages/modules
-------------------------

    - ANTs, image registration, http://stnava.github.io/ANTs/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

import sys

from os import dup
from os import dup2
from os import remove
from os.path import join
from os.path import exists

from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue

from ants.core import from_numpy
from ants.segmentation import atropos
from ants.segmentation import kelly_kapowski

from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume

__all__ = ['CapturedStdout',
           'ProcessAtropos',
           'ProcessThickness',
           'antsKMeansSegmentation',
           'antsPriorBasedSegmentation',
           'antsCorticalThickness']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - CaptureStdout
    - Process -> ProcessAtropos
              -> ProcessThickness
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
        self.prevfd = dup(sys.stdout.fileno())
        dup2(F.fileno(), sys.stdout.fileno())
        self.prev = sys.stdout
        # sys.stdout = fdopen(self.prevfd, "w")
        return F

    def __exit__(self, exc_type, exc_value, traceback):
        dup2(self.prevfd, self.prev.fileno())
        sys.stdout = self.prev


class ProcessAtropos(Process):
    """
    ProcessAtropos

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for ants atropos function.

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
        self._mask = mask.getNumpy(defaultshape=False)
        self._spacing = volume.getSpacing()
        if isinstance(init, list):
            self._init = list()
            for i in range(len(init)):
                self._init.append(init[i].getNumpy(defaultshape=False).astype('float32'))
        elif isinstance(init, str): self._init = init
        else: self._init = 'Kmeans[3]'
        self._mrf = mrf
        self._conv = conv
        self._weight = weight
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        # d = vol.direction
        # PySisyphe volume LPI orientation
        # d[0, 0] = -1
        # d[1, 1] = -1
        mask = from_numpy(self._mask, spacing=self._spacing)
        # vol.set_direction(d)
        # mask.set_direction(d)
        if isinstance(self._init, list):
            init = list()
            for i in range(len(self._init)):
                init.append(from_numpy(self._init[i], spacing=self._spacing))
        else: init = self._init
        try:
            # with CapturedStdout(self._stdout) as F:
            with CapturedStdout(self._stdout):
                r = atropos(vol, mask, i=init, m=self._mrf, c=self._conv,
                            priorweight=self._weight, verbose=1)
                self._result.put(r['segmentation'].view())
                for i in range(len(r['probabilityimages'])):
                    self._result.put(r['probabilityimages'][i].view())
        except: self.terminate()


class ProcessThickness(Process):
    """
    ProcessThickness

    Description
    ~~~~~~~~~~~

    Multiprocessing Process class for ants kelly_kapowski function.

    Inheritance
    ~~~~~~~~~~~

    Process -> ProcessThickness
     """

    # Special method

    """
    Private attributes

    _stdout     str, c++ stdout redirected to _stdout file
    _result     Queue
    """

    def __init__(self, seg, gm, wm, niter, grdstep, grdsmooth, stdout, queue):
        Process.__init__(self)
        self._seg = seg.getNumpy(defaultshape=False).astype('float32')
        self._gm = gm.getNumpy(defaultshape=False).astype('float32')
        self._wm = wm.getNumpy(defaultshape=False).astype('float32')
        self._spacing = seg.getSpacing()
        self._niter = niter
        self._grdstep = grdstep
        self._grdsmooth = grdsmooth
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        seg = from_numpy(self._seg, spacing=self._spacing)
        # d = seg.direction
        # PySisyphe volume LPI orientation
        # d[0, 0] = -1
        # d[1, 1] = -1
        gm = from_numpy(self._gm, spacing=self._spacing)
        wm = from_numpy(self._wm, spacing=self._spacing)
        # seg.set_direction(d)
        # gm.set_direction(d)
        # wm.set_direction(d)
        try:
            # with CapturedStdout(self._stdout) as F:
            with CapturedStdout(self._stdout):
                r = kelly_kapowski(s=seg, g=gm, w=wm, its=self._niter, r=self._grdstep, m=self._grdsmooth, verbose=1)
                self._result.put(r.view())
        except: self.terminate()


"""
Functions
~~~~~~~~~

    - antsSupervisedKMeansSegmentation
    - antsPriorBasedSegmentation
    - antsCorticalThickness
"""


def antsKMeansSegmentation(vol, mask=None, nclass=3, niter=3, smooth=0.3, radius=1,
                           save=False, segprefix='seg_', segsuffix='',
                           classprefix='', classsuffix='class*_', wait=None):
    """
    Parameters
    ----------
    vol : SisypheVolume
    mask : SisypheVolume | SisypheROI | SisypheImage
    nclass : int
        number of classes, default 1
    niter : int
        number of iterations, default 3
    smooth : float
        mrf parameter
    radius : int
        mrf parameter
    save : bool
        save segmentation result if True (default False)
    segprefix : str
        prefix for label segmentation result filename
    segsuffix : str
        suffix for label segmentation result filename
    classprefix : str
        prefix for probability segmentation result filename
    classsuffix : str
        suffix for probability segmentation result filename
    wait : DialogWait

    Returns
    -------
    list[SisypheVolume]
    """

    def progress(p):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(p)
                verbose = f.readlines()
                p = f.tell()
        if len(verbose) > 0:
            for line in reversed(verbose):
                line = line.lstrip()
                if line[0] == 'I':
                    citer = line.split(' ')
                    if len(citer) >= 2:
                        citer = int(citer[1])
                        if citer > wait.getCurrentProgressValue():
                            wait.setCurrentProgressValue(citer)
                            break
        return p

    if not isinstance(vol, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(vol)))

    if wait is not None:
        wait.setInformationText('{} segmentation initialization...'.format(vol.getBasename()))
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
        wait.setProgressRange(0, niter)
        wait.setCurrentProgressValue(0)
    # Parameters initialization
    queue = Queue()
    stdout = join(vol.getDirname(), 'stdout.log')
    conv = '[{},0]'.format(niter)
    init = 'Kmeans[{}]'.format(nclass)
    mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
    weight = 0.0
    if mask is None: mask = vol.getMask(algo='mean', fill='2d')
    # Process
    flt = ProcessAtropos(vol, mask, init, mrf, conv, weight, stdout, queue)
    try:
        if wait is not None:
            wait.setInformationText('{} segmentation...'.format(vol.getBasename()))
            wait.setButtonVisibility(True)
            wait.setProgressVisibility(True)
            wait.open()
        flt.start()
        pos = 0
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): pos = progress(pos)
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise err
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    if wait is not None:
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # Save
    r = list()
    if not queue.empty():
        img = queue.get()
        if img is not None:
            fltvol = SisypheVolume()
            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
            fltvol.copyAttributesFrom(vol)
            fltvol.acquisition.setModalityToLB()
            if save:
                fltvol.setFilename(vol.getFilename())
                fltvol.setFilenamePrefix(segprefix)
                fltvol.setFilenameSuffix(segsuffix)
                wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                fltvol.save()
            r.append(fltvol)
        for i in range(nclass):
            img = queue.get()
            if img is not None:
                fltvol = SisypheVolume()
                fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                fltvol.copyAttributesFrom(vol)
                fltvol.acquisition.setModalityToOT()
                fltvol.acquisition.setUnitToPercent()
                if save:
                    fltvol.setFilename(vol.getFilename())
                    if classprefix != '':
                        if '*' in classprefix: classprefix = classprefix.replace('*', str(i))
                        elif '_' in classprefix: classprefix = classprefix.replace('_', '_' + str(i))
                        elif '-' in classprefix: classprefix = classprefix.replace('-', '-' + str(i))
                        else: classprefix += str(i)
                    if classsuffix != '':
                        if '*' in classsuffix: classsuffix = classsuffix.replace('*', str(i))
                        elif '_' in classsuffix: classsuffix = classsuffix.replace('_', '_' + str(i))
                        elif '-' in classsuffix: classsuffix = classsuffix.replace('-', '-' + str(i))
                        else: classsuffix += str(i)
                    fltvol.setFilenamePrefix(classprefix)
                    fltvol.setFilenameSuffix(classsuffix)
                    wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                    fltvol.save()
                r.append(fltvol)
    if wait is not None: wait.hide()
    return r


def antsPriorBasedSegmentation(vol, priors, mask=None, weight=0.5, niter=10, smooth=0.3, radius=1, conv=None,
                               save=False, segprefix='seg_', segsuffix='', wait=None):
    """
    Parameters
    ----------
    vol : SisypheVolume
    priors : list[SisypheVolume]
        prior probability images registered to vol
    mask : SisypheVolume | SisypheROI | SisypheImage
    weight : float
        prior weight (0.0 to 1.0, default 0.5)
    niter : int
        number of iterations, default 3
    smooth : float
        mrf parameter, default 0.3
    radius : int
        mrf parameter, default 1
    conv : float
        convergence threshold, usual value 1e-6
    save : bool
        save segmentation result if True (default False)
    segprefix : str
        prefix for label segmentation result filename
    segsuffix : str
        suffix for label segmentation result filename
    wait : DialogWait

    Returns
    -------
    list[SisypheVolume]

    Last revision: 23/07/2024
    """

    def progress(p):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(p)
                verbose = f.readlines()
                p = f.tell()
        if len(verbose) > 0:
            for line in reversed(verbose):
                line = line.lstrip()
                if line[0] == 'I':
                    citer = line.split(' ')
                    if len(citer) >= 2:
                        citer = int(citer[1])
                        if citer > wait.getCurrentProgressValue():
                            wait.setCurrentProgressValue(citer)
                            break
        return p

    if not isinstance(vol, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(vol)))

    if not isinstance(priors, list): priors = 'Kmeans[3]'

    if wait is not None:
        wait.setInformationText('{} segmentation initialization...'.format(vol.getBasename()))
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
        wait.setProgressRange(0, niter)
        wait.setCurrentProgressValue(0)
    # Parameters initialization
    queue = Queue()
    stdout = join(vol.getDirname(), 'stdout.log')
    # Process
    if isinstance(conv, float): conv = '[{},{}]'.format(niter, conv)
    else: conv = '[{},0]'.format(niter)
    mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
    if mask is None: mask = vol.getMask(algo='mean', fill='2d')
    flt = ProcessAtropos(vol, mask, priors, mrf, conv, weight, stdout, queue)
    try:
        if wait is not None:
            wait.setInformationText('{} segmentation...'.format(vol.getBasename()))
            wait.setButtonVisibility(True)
            wait.setProgressVisibility(True)
            wait.open()
        flt.start()
        pos = 0
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): pos = progress(pos)
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise err
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    if wait is not None:
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # save
    r = list()
    if not queue.empty():
        img = queue.get()
        if img is not None:
            fltvol = SisypheVolume()
            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
            fltvol.copyAttributesFrom(vol)
            fltvol.acquisition.setModalityToLB()
            if save:
                fltvol.setFilename(vol.getFilename())
                fltvol.setFilenamePrefix(segprefix)
                fltvol.setFilenameSuffix(segsuffix)
                if wait is not None: wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                fltvol.save()
            r.append(fltvol)
        for i in range(len(priors)):
            img = queue.get()
            if img is not None:
                fltvol = SisypheVolume()
                fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                fltvol.copyAttributesFrom(vol)
                fltvol.acquisition.setModalityToOT()
                fltvol.acquisition.setUnitToPercent()
                fltvol.acquisition.setSequence(priors[i].acquisition.getSequence())
                if save:
                    fltvol.setFilename(vol.getFilename())
                    prior = priors[i].getFilename()
                    if 'brainstem' in prior: prefix = 'brainstem_'
                    elif 'cerebellum' in prior: prefix = 'cerebellum_'
                    elif 'csf' in prior: prefix = 'csf_'
                    elif 'gm' in prior: prefix = 'gm_'
                    elif 'wm' in prior: prefix = 'wm_'
                    elif 'cortical' in prior: prefix = 'cortical_gm_'
                    elif 'subcortical' in prior: prefix = 'subcortical_gm_'
                    else: prefix = 'class_{}_'.format(i)
                    fltvol.setFilenamePrefix(prefix)
                    if wait is not None: wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                    fltvol.save()
                r.append(fltvol)
    if wait is not None: wait.hide()
    return r


def antsCorticalThickness(seg, gm, wm, niter=50, grdstep=0.5, grdsmooth=1,
                          save=False, prefix='thickness_', suffix='', wait=None):
    """
    Parameters
    ----------
    seg : SisypheVolume
    gm : SisypheVolume
        grey matter map
    wm : SisypheVolume
        white matter map
    niter : int
        number of iterations, default 50
    grdstep : float
        gradient descent step, default 0.025
    grdsmooth : float
        gradient field smoothing, default 1.4
    save : bool
        save cortical thickness map if True (default False)
    prefix : str
        prefix for cortical thickness map filename
    suffix : str
        suffix for cortical thickness map filename
    wait : DialogWait

    Returns
    -------
    SisypheVolume
    """

    def progress(p):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(p)
                verbose = f.readlines()
                p = f.tell()
        if len(verbose) > 0:
            for line in reversed(verbose):
                line = line.lstrip()
                if line[0] == 'I':
                    citer = line.split(' ')
                    if len(citer) >= 2:
                        citer = int(citer[1])
                        if citer > wait.getCurrentProgressValue():
                            wait.setCurrentProgressValue(citer)
                            break
        return p

    if not isinstance(seg, SisypheVolume):
        raise TypeError('seg parameter type {} is not SisypheVolume.'.format(type(seg)))
    if not isinstance(gm, SisypheVolume):
        raise TypeError('gm parameter type {} is not SisypheVolume.'.format(type(gm)))
    if not isinstance(wm, SisypheVolume):
        raise TypeError('wm parameter type {} is not SisypheVolume.'.format(type(wm)))

    o = seg.getOrigin()
    seg.setDefaultOrigin()
    gm.setDefaultOrigin()
    wm.setDefaultOrigin()
    seg.setDefaultDirections()
    gm.setDefaultDirections()
    wm.setDefaultDirections()

    if wait is not None:
        wait.setInformationText('{} cortical thickness initialization...'.format(seg.getBasename()))
        wait.buttonVisibilityOff()
        wait.progressVisibilityOff()
        wait.setProgressRange(0, niter)
        wait.setCurrentProgressValue(0)
    # Parameters initialization
    queue = Queue()
    stdout = join(seg.getDirname(), 'stdout.log')
    # Process
    flt = ProcessThickness(seg, gm, wm, niter, grdstep, grdsmooth, stdout, queue)
    try:
        flt.start()
        if wait is not None:
            wait.setInformationText('{} cortical thickness processing...'.format(seg.getBasename()))
            wait.buttonVisibilityOn()
            wait.progressVisibilityOn()
        pos = 0
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): pos = progress(pos)
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise err
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    if wait is not None:
        wait.buttonVisibilityOff()
        wait.progressVisibilityOff()
    # Save
    fltvol = None
    if not queue.empty():
        img = queue.get()
        if img is not None:
            fltvol = SisypheVolume()
            fltvol.copyAttributesFrom(seg)
            fltvol.copyFromNumpyArray(img, seg.getSpacing(), seg.getOrigin(), defaultshape=False)
            if save:
                fltvol.setFilename(seg.getFilename())
                fltvol.setFilenamePrefix(prefix)
                fltvol.setFilenameSuffix(suffix)
                fltvol.setOrigin(o)
                if wait is not None: wait.setInformationText('Save {}...'.format(fltvol.getBasename()))
                fltvol.save()
    if wait is not None: wait.hide()
    return fltvol
