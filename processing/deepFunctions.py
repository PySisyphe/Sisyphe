"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            http://stnava.github.io/ANTs/                               Image registration
        ANTsPyNet       https://github.com/ANTsX/ANTsPyNet                          Deep learning
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

import sys

from os import remove
from os.path import join
from os.path import exists
from os.path import dirname
from os.path import abspath

from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue

from ants.core import from_numpy

from antspynet.utilities import brain_extraction
from antspynet.utilities import deep_atropos
from antspynet.utilities import hippmapp3r_segmentation
from antspynet.utilities import sysu_media_wmh_segmentation

from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume

__all__ = ['deepBrainExtraction',
           'deepAtropos',
           'deepHippocampusSegmentation',
           'deepWhiteMatterHyperintensitiesSegmentation']

"""
    Class hierarchy

        Process -> DeepProcess  -> ProcessDeepBrainExtraction
                                -> ProcessDeepAtropos
                                -> ProcessDeepHippocampusSegmentation
                                -> ProcessDeepWhiteMatterHyperintensitiesSegmentation
                                -> ProcessDeepTumorSegmentation
"""


class ProcessDeep(Process):
    """
        ProcessDeep

        Description

            Abstract multiprocessing Process class for antspynet functions.

        Inheritance

            Process -> ProcessDeep

        Private attributes

            _volume     SisypheVolume
            _spacing    list[float], _volume spacing
            _stdout     str, stdout
            _out        str, stdout redirected to _out file
            _dir        str, antspynet cache directory
            _result     Queue

        Public methods

            run()       override

            inherited Process methods
     """

    # Special method

    def __init__(self, volume, stdout, queue):
        Process.__init__(self)
        self._volume = volume.getNumpy(defaultshape=False).astype('float32')
        self._spacing = volume.getSpacing()
        self._out = stdout
        self._stdout = sys.stdout
        import Sisyphe
        self._dir = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        self._result = queue

    def __enter__(self):
        sys.stdout = self._out

    def __exit__(self):
        sys.stdout = self._stdout
        self._out.close()

    # Public methods

    def run(self):
        raise NotImplemented


class ProcessDeepBrainExtraction(ProcessDeep):
    """
        ProcessDeepBrainExtraction

        Description

            Abstract multiprocessing Process class for antspynet brain_extraction.

        Inheritance

            Process -> ProcessDeep -> ProcessDeepBrainExtraction

        Private attributes

            _modality   str, _volume modality: 't1', 't1nobrainer', 't1combined', 't2', 'flair', 'bold'

        Public methods

            run()       override

            inherited Process methods
     """
    # Special method

    def __init__(self, volume, modality, stdout, queue):
        super().__init__(volume, stdout, queue)
        self._modality = modality

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        d = vol.direction
        # PySisyphe volume LPI orientation
        d[0, 0] = -1
        d[1, 1] = -1
        vol.set_direction(d)
        try:
            r = brain_extraction(vol, self._modality, antsxnet_cache_directory=self._dir, verbose=True)
            self._result.put(r.getNumpy())
        except: self.terminate()


class ProcessDeepAtropos(ProcessDeep):
    """
        ProcessDeepAtropos

        Description

            Abstract multiprocessing Process class for antspynet deep_atropos.

        Inheritance

            Process -> ProcessDeep -> ProcessDeepAtropos

        Private attributes

        Public methods

            run()       override

            inherited Process methods
     """
    # Special method

    def __init__(self, volume, stdout, queue):
        super().__init__(volume, stdout, queue)

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        d = vol.direction
        # PySisyphe volume LPI orientation
        d[0, 0] = -1
        d[1, 1] = -1
        vol.set_direction(d)
        try:
            r = deep_atropos(vol, antsxnet_cache_directory=self._dir, verbose=True)
            self._result.put(r['segmentation_image'].getNumpy())
            self._result.put(r['probability_images'][0].getNumpy())  # Mask
            self._result.put(r['probability_images'][1].getNumpy())  # Cerebro-spinal fluid map
            self._result.put(r['probability_images'][2].getNumpy())  # Cortical gray matter map
            self._result.put(r['probability_images'][3].getNumpy())  # White matter map
            self._result.put(r['probability_images'][4].getNumpy())  # Subcortical gray matter
            self._result.put(r['probability_images'][5].getNumpy())  # Brainstem
            self._result.put(r['probability_images'][6].getNumpy())  # Cerebellum
        except: self.terminate()


class ProcessDeepHippocampusSegmentation(ProcessDeep):
    """
        ProcessHippocampusSegmentation

        Description

            Abstract multiprocessing Process class for antspynet hippmapp3r_segmentation.

        Inheritance

            Process -> ProcessDeep -> ProcessHippocampusSegmentation

        Private attributes

        Public methods

            run()       override

            inherited Process methods
     """
    # Special method

    def __init__(self, volume, stdout, queue):
        super().__init__(volume, stdout, queue)

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        d = vol.direction
        # PySisyphe volume LPI orientation
        d[0, 0] = -1
        d[1, 1] = -1
        vol.set_direction(d)
        try:
            r = hippmapp3r_segmentation(vol, antsxnet_cache_directory=self._dir, verbose=True)
            self._result.put(r.getNumpy())
        except: self.terminate()


class ProcessDeepWhiteMatterHyperintensitiesSegmentation(ProcessDeep):
    """
        ProcessDeepWhiteMatterHyperintensitiesSegmentation

        Description

            Abstract multiprocessing Process class for antspynet sysu_media_wmh_segmentation.

        Inheritance

            Process -> ProcessDeep -> ProcessDeepWhiteMatterHyperintensitiesSegmentation

        Private attributes

            _t1     SisypheVolume

        Public methods

            run()       override

            inherited Process methods
     """
    # Special method

    def __init__(self, volume, t1, stdout, queue):
        super().__init__(volume, stdout, queue)
        if t1 is None: self._t1 = t1
        else: self._t1 = t1.getNumpy(defaultshape=False).astype('float32')

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        d = vol.direction
        # PySisyphe volume LPI orientation
        d[0, 0] = -1
        d[1, 1] = -1
        vol.set_direction(d)
        if self._t1 is None: t1 = None
        else:
            t1 = from_numpy(self._t1, spacing=self._spacing)
            t1.set_direction(d)
        try:
            r = sysu_media_wmh_segmentation(flair=vol, t1=t1, antsxnet_cache_directory=self._dir, verbose=True)
            self._result.put(r.getNumpy())
        except: self.terminate()


"""
    Functions
       
        deepBrainExtraction
        deepAtropos
        deepHippocampusSegmentation
        deepWhiteMatterHyperintensitiesSegmentation
        deepTumorSegmentation  
"""


def deepBrainExtraction(vol, modality='t1c', save=False,
                        prefix='brain_', suffix='',
                        maskprefix='mask_', masksuffix='', wait=None):
    """
        vol         SisypheVolume
        modality    str, 't1', 't1b', 't1c', 't2', 'flair', 'bold'
        save        bool, save volumes
        wait        DialogWait

        return     list[SisypheVolume], probability mask, skull stripped
    """

    def progress():
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                verbose = f.readlines()
        n = len(verbose)
        if n == 3: wait.setInformationText('Template registration...')
        else: wait.setInformationText('Model prediction...')

    if not isinstance(vol, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(vol)))

    if wait is not None:
        wait.setInformationText('Brain extraction initialization...')
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # Parameters initialization
    queue = Queue()
    stdout = join(vol.getDirname(), 'stdout.log')
    if modality == 't1b': modality = 't1nobrainer'
    elif modality == 't1c': modality = 't1combined'
    # Process
    flt = ProcessDeepBrainExtraction(vol, modality, stdout, queue)
    try:
        if wait is not None:
            wait.setButtonVisibility(True)
            wait.open()
        flt.start()
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): progress()
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise Exception
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    # Save
    r = list()
    if not queue.empty():
        img = queue.get()
        if img is not None:
            mask = SisypheVolume()
            mask.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
            mask.copyAttributesFrom(vol)
            mask.acquisition.setModalityToOT()
            mask.acquisition.setSequenceToMask()
            r.append(mask)
            img = (mask.getSITKImage() > 0.5) * vol.getSITKImage()
            brain = SisypheVolume()
            brain.setSITKImage(img)
            brain.cast(vol.getDatatype())
            brain.copyAttributesFrom(vol)
            r.append(brain)
            if save:
                mask.setFilename(vol.getFilename())
                mask.setFilenamePrefix(maskprefix)
                mask.setFilenameSuffix(masksuffix)
                wait.setInformationText('Save {}'.format(mask.getBasename()))
                mask.save()
                brain.setFilename(vol.getFilename())
                brain.setFilenamePrefix(prefix)
                brain.setFilenameSuffix(suffix)
                wait.setInformationText('Save {}'.format(brain.getBasename()))
                brain.save()
    if wait is not None: wait.hide()
    return r

def deepAtropos(vol, save=False, wait=None):
    """
        vol         SisypheVolume
        save        bool, save volumes
        wait        DialogWait

        return      dict[SisypheVolume],
                    'seg', segmentation label modality
                    'mask', brain mask probability map
                    'csf', cerebro-spinal fluid probability map
                    'cgm', cortical gray matter probability map
                    'wm', white matter probability map
                    'scgm', subcortical gray matter probability map
                    'brainstem', brainstem probability map
                    'cerebellum', cerebellum probability map
    """
    def progress():
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                verbose = f.readlines()
        for line in reversed(verbose):
            line = line.lstrip()
            stp = line.split('  ')
            if len(stp) == 1:
                c = stp[0][:2]
                if c == 'Pr':
                    wait.setInformationText('Model prediction...')
                    wait.setCurrentProgressValue(7)
                    break
            if len(stp) > 1:
                c = stp[1][:2]
                if c == 'tr':
                    wait.setInformationText('Truncate intensities...')
                    wait.setCurrentProgressValue(1)
                    break
                elif c == 'br':
                    wait.setInformationText('Brain extraction...')
                    wait.setCurrentProgressValue(2)
                    break
                elif c == 'te':
                    wait.setInformationText('Template registration...')
                    wait.setCurrentProgressValue(3)
                    break
                elif c == 'bi':
                    wait.setInformationText('Bias correction...')
                    wait.setCurrentProgressValue(4)
                    break
                elif c == 'de':
                    wait.setInformationText('Denoising...')
                    wait.setCurrentProgressValue(5)
                    break
                elif c == 're':
                    wait.setInformationText('Open model weights...')
                    wait.setCurrentProgressValue(6)
                    break

    if not isinstance(vol, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(vol)))

    if wait is not None:
        wait.setInformationText('Segmentation initialization...')
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # Parameters initialization
    queue = Queue()
    stdout = join(vol.getDirname(), 'stdout.log')
    # Process
    flt = ProcessDeepAtropos(vol, stdout, queue)
    try:
        if wait is not None:
            wait.setButtonVisibility(True)
            wait.setProgressVisibility(True)
            wait.setProgressRange(0, 7)
            wait.open()
        flt.start()
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): progress()
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise Exception
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    # Save
    r = dict()
    if not queue.empty():
        # Segmentation label modality
        img = queue.get()
        if img is not None:
            v = SisypheVolume()
            v.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
            v.copyAttributesFrom(vol)
            v.acquisition.setModalityToLB()
            r['seg'] = v
            if save:
                v.setFilename(vol.getFilename())
                v.setFilenamePrefix('seg_')
                if wait is not None: wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()
        # Brain mask probability map
        for i in range(7):
            img = queue.get()
            if img is not None:
                v = SisypheVolume()
                v.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                v.copyAttributesFrom(vol)
                v.acquisition.setModalityToOT()
                v.setFilename(vol.getFilename())
                if i == 0:
                    r['seg'] = v
                    v.acquisition.setSequenceToMask()
                    v.setFilenamePrefix('mask_')
                elif i == 1:
                    r['csf'] = v
                    v.acquisition.setSequenceToCerebroSpinalFluidMap()
                    v.setFilenamePrefix('csf_')
                elif i == 2:
                    r['cgm'] = v
                    v.acquisition.setSequenceToGrayMatterMap()
                    v.setFilenamePrefix('cgm_')
                elif i == 3:
                    r['wm'] = v
                    v.acquisition.setSequenceToWhiteMatterMap()
                    v.setFilenamePrefix('wm_')
                elif i == 4:
                    r['scgm'] = v
                    v.acquisition.setSequenceToGrayMatterMap()
                    v.setFilenamePrefix('scgm_')
                elif i == 5:
                    r['brainstem'] = v
                    v.acquisition.setSequence('BRAINSTEM MAP')
                    v.setFilenamePrefix('brainstem_')
                elif i == 6:
                    r['cerebellum'] = v
                    v.acquisition.setSequence('CEREBELLUM MAP')
                    v.setFilenamePrefix('cerebellum_')
                if save:
                    if wait is not None: wait.setInformationText('Save {}'.format(v.getBasename()))
                    v.save()
    if wait is not None: wait.hide()
    return r

def deepHippocampusSegmentation(vol, save=False,
                                prefix='hipp_', suffix='', wait=None):
    """
        vol         SisypheVolume
        save        bool, save volumes
        wait        DialogWait

        return      SisypheVolume, hippocampus probability map
    """
    def progress():
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                verbose = f.readlines()
        for line in reversed(verbose):
            line = line.lstrip()
            stp = line.split('  ')
            if len(stp) > 1:
                c = stp[1][:2]
                if c == 'br':
                    wait.setInformationText('Brain extraction...')
                    wait.setCurrentProgressValue(1)
                    break
                elif c == 'bi':
                    wait.setInformationText('Bias correction...')
                    wait.setCurrentProgressValue(2)
                    break
                elif c == 'te':
                    wait.setInformationText('Template registration...')
                    wait.setCurrentProgressValue(3)
                    break
                elif c == 'ge':
                    if wait.getCurrentProgressValue() > 4:
                        wait.setInformationText('Open second model weights...')
                        wait.setCurrentProgressValue(6)
                        break
                    else:
                        wait.setInformationText('Open first model weights...')
                        wait.setCurrentProgressValue(4)
                        break
                elif c == 'pr':
                    wait.setInformationText('First model prediction...')
                    wait.setCurrentProgressValue(5)
                    break
                elif c == 'Mo':
                    wait.setInformationText('Second model prediction...')
                    wait.setCurrentProgressValue(7)
                    break

    if not isinstance(vol, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(vol)))

    if wait is not None:
        wait.setInformationText('Segmentation initialization...')
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # Parameters initialization
    queue = Queue()
    stdout = join(vol.getDirname(), 'stdout.log')
    # Process
    flt = ProcessDeepHippocampusSegmentation(vol, stdout, queue)
    try:
        if wait is not None:
            wait.setButtonVisibility(True)
            wait.setProgressVisibility(True)
            wait.setProgressRange(0, 7)
            wait.open()
        flt.start()
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): progress()
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise Exception
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    # Save
    v = None
    if not queue.empty():
        img = queue.get()
        if img is not None:
            v = SisypheVolume()
            v.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
            v.copyAttributesFrom(vol)
            v.acquisition.setModalityToOT()
            v.acquisition.setSequence('HIPPOCAMPUS MAP')
            if save:
                v.setFilename(vol.getFilename())
                v.setFilenamePrefix(prefix)
                v.setFilenameSuffix(suffix)
                if wait is not None: wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()
    if wait is not None: wait.hide()
    return v

def deepWhiteMatterHyperintensitiesSegmentation(flair, t1=None, save=False,
                                                prefix='wmh_', suffix='', wait=None):
    """
        flair       SisypheVolume
        t1          SisypheVolume, optional
        save        bool, save volumes
        wait        DialogWait

        return      SisypheVolume, hippocampus probability map
    """
    def progress():
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                verbose = f.readlines()
        for line in reversed(verbose):
            line = line.lstrip()
            if line[:2] == 'Pr':
                wait.setInformationText('Model prediction...')
                break

    if not isinstance(flair, SisypheVolume):
        raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(flair)))

    if t1 is not None:
        if not isinstance(t1, SisypheVolume):
            raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(flair)))

    if wait is not None:
        wait.setInformationText('Segmentation initialization...')
        wait.setButtonVisibility(False)
        wait.setProgressVisibility(False)
    # Parameters initialization
    queue = Queue()
    stdout = join(flair.getDirname(), 'stdout.log')
    # Process
    flt = ProcessDeepWhiteMatterHyperintensitiesSegmentation(flair, t1, stdout, queue)
    try:
        if wait is not None:
            wait.setButtonVisibility(True)
            wait.setProgressVisibility(False)
            wait.open()
        flt.start()
        while flt.is_alive():
            QApplication.processEvents()
            if wait is not None:
                if exists(stdout): progress()
                if wait.getStopped(): flt.terminate()
    except Exception as err:
        if flt.is_alive(): flt.terminate()
        if wait is not None: wait.hide()
        raise Exception
    finally:
        # Remove temporary std::cout file
        if exists(stdout): remove(stdout)
    # Save
    v = None
    if not queue.empty():
        img = queue.get()
        if img is not None:
            v = SisypheVolume()
            v.copyFromNumpyArray(img, flair.getSpacing(), flair.getOrigin(), defaultshape=False)
            v.copyAttributesFrom(flair)
            v.acquisition.setModalityToOT()
            v.acquisition.setSequenceToProbabilityMap()
            if save:
                v.setFilename(flair.getFilename())
                v.setFilenamePrefix(prefix)
                v.setFilenameSuffix(suffix)
                if wait is not None: wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()
    if wait is not None: wait.hide()
    return v



