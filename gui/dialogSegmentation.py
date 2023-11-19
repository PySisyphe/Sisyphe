"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os import remove
from os.path import join
from os.path import exists
from os.path import basename

from math import log10
from math import isinf

from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue

from numpy import mean

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from ants.core import from_numpy
from ants.utils import denoise_image
from ants.segmentation import atropos

from SimpleITK import Cast
from SimpleITK import sitkFloat32
from SimpleITK import AffineTransform
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole
from SimpleITK import CenteredTransformInitializerFilter

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import getUserPySisyphePath
from Sisyphe.processing.simpleItkFilters import kmeans
from Sisyphe.processing.simpleItkFilters import biasFieldCorrection
from Sisyphe.processing.antsRegistration import antsRegistration
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogRegistration import CapturedStdout
from Sisyphe.gui.dialogRegistration import ProcessRegistration
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        Process -> ProcessNonLocalMeansFiler
                -> ProcessAtropos
        QDialog -> DialogUnsupervisedKMeans
                -> DialogSupervisedKMeans
                -> DialogPriorBasedSegmentation
"""


class ProcessNonLocalMeansFilter(Process):
    """
        ProcessAtropos

        Description

            Multiprocessing Process class for ants non local means denoising filter.

        Inheritance

            Process -> ProcessNonLocalMeansFilter

        Private attributes

            _stdout     str, c++ stdout redirected to _stdout file
            _result     Queue

        Public methods

            run()       override

            inherited Process methods
     """

    # Special method

    def __init__(self, volume, shrink, patchradius, searchradius, noise, stdout, queue):
        Process.__init__(self)
        self._volume = volume.getNumpy(defaultshape=False).astype('float32')
        self._spacing = volume.getSpacing()
        self._shrink = shrink
        self._patchradius = patchradius
        self._searchradius = searchradius
        self._noise = noise
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        try:
            with CapturedStdout(self._stdout) as F:
                r = denoise_image(vol, shrink_factor=self._shrink, p=self._patchradius,
                                  r=self._searchradius, noise_model=self._noise, v=1)
                self._result.put(r.getNumpy())
        except: self.terminate()


class ProcessAtropos(Process):
    """
        ProcessAtropos

        Description

            Multiprocessing Process class for ants atropos function.

        Inheritance

            Process -> ProcessUnsupervisedKMeans

        Private attributes

            _stdout     str, c++ stdout redirected to _stdout file
            _result     Queue

        Public methods

            run()       override

            inherited Process methods
     """

    # Special method

    def __init__(self, volume, mask, init, mrf, conv, weight, stdout, queue):
        Process.__init__(self)
        self._volume = volume.getNumpy(defaultshape=False).astype('float32')
        self._mask = mask.getNumpy(defaultshape=False)
        self._spacing = volume.getSpacing()
        self._init = init
        self._mrf = mrf
        self._conv = conv
        self._weight = weight
        self._stdout = stdout
        self._result = queue

    # Public methods

    def run(self):
        vol = from_numpy(self._volume, spacing=self._spacing)
        mask = from_numpy(self._mask, spacing=self._spacing)
        try:
            with CapturedStdout(self._stdout) as F:
                r = atropos(vol, mask, i=self._init, m=self._mrf, c=self._conv,
                            priorweight=self._weight, verbose=1)
                self._result.put(r['segmentation'].view())
                for i in range(len(r['probabilityimages'])):
                    self._result.put(r['probabilityimages'][i].view())
        except: self.terminate()


class DialogUnsupervisedKMeans(QDialog):
    """
        DialogUnsupervisedKMeans

        Description

            GUI dialog for unsupervised KMeans segmentation.

        Inheritance

            QDialog -> DialogUnsupervisedKMeans

        Private attributes

            _pos                int, current position in stdout file, used to follow progress in C++ stdout
            _volumeSelect       FilesSelectionWidget
            _settings           FunctionSettingsWidget

        Public methods

            execute()

            inherited QDialog methods
    """
    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Unsupervised KMeans segmentation')

        # Init non-GUI attributes

        self._pos = 0
        self._stdout = ''

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget()
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._maskSelect = FilesSelectionWidget()
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Mask(s)')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(False)

        self._mask = QCheckBox('Use mask(s)')
        self._mask.setChecked(False)
        self._mask.toggled.connect(self._maskSelect.setVisible)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._mask)
        self._layout.addWidget(self._maskSelect)

        self._settings1 = FunctionSettingsWidget('NonLocalMeansImageFilter')
        self._settings1.VisibilityToggled.connect(self._center)

        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.VisibilityToggled.connect(self._center)

        self._settings = FunctionSettingsWidget('UnsupervisedKMeans')
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('NonLocalMeansFilter').toggled.connect(self._setting1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._setting2.setVisible)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

    # Private method

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateLocalMeansFilterProgress(self, wait):
        if isinstance(wait, DialogWait):
            lock = Lock()
            with lock:
                with open(self._stdout, 'r') as f:
                    verbose = f.readlines()
            if len(verbose) > 0:
                for line in reversed(verbose):
                    if line[0] == '*': wait.setCurrentProgressValue(len(line))
        else: raise TypeError('parameter type {} is not DialogWait.'.format(type(wait)))

    # Public method

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            filemasks = self._maskSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            queue = Queue()
            wait = DialogWait(parent=self)
            for i in range(len(filenames)):
                vol.load(filenames[i])
                if i < len(filemasks):
                    mask = SisypheVolume()
                    mask.load(filemasks[i])
                    if not mask.hasSameFieldOfView(vol):
                        QMessageBox.warning(self, self.windowTitle(),
                                            '{} and {} do not have the same FOV.'.format(vol.getBasename(),
                                                                                         mask.getBasename()))
                        mask = None
                """
                    First stage - Non local means filter denoising
                """
                if self._settings.getParameterValue('NonLocalMeansFilter'):
                    wait.setInformationText('{} non locals means filter initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    self._stdout = join(vol.getDirname(), 'stdout.log')
                    wait.setProgressRange(0, 107)
                    wait.setCurrentProgressValue(0)
                    # Parameters
                    params = self._settings1.getParametersList()
                    shrink = self._settings1.getParameterValue(params[0])
                    patchradius = self._settings1.getParameterValue(params[1])
                    searchradius = self._settings1.getParameterValue(params[2])
                    noise = self._settings1.getParameterValue(params[3])[0]
                    prefix = self._settings1.getParameterValue(params[4])
                    suffix = self._settings1.getParameterValue(params[5])
                    # Process
                    flt = ProcessNonLocalMeansFilter(vol, shrink, patchradius, searchradius, noise, self._stdout, queue)
                    try:
                        wait.open()
                        flt.start()
                        wait.setInformationText('{} non locals means filter...'.format(vol.getBasename()))
                        wait.setButtonVisibility(True)
                        wait.setProgressVisibility(True)
                        while flt.is_alive():
                            QApplication.processEvents()
                            if exists(self._stdout): self._updateLocalMeansFilterProgress(wait)
                            if self._wait.getStopped(): flt.terminate()
                    except Exception as err:
                        if flt.is_alive(): flt.terminate()
                        wait.hide()
                        wait.close()
                        QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                        return
                    finally:
                        # Remove temporary std::cout file
                        if exists(self._stdout): remove(self._stdout)
                    if not queue.empty():
                        img = queue.get()
                        if img is not None:
                            fltvol = SisypheVolume()
                            fltvol.copyAttributesFrom(vol)
                            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                            fltvol.setFilename(vol.getFilename())
                            fltvol.setFilenamePrefix(prefix)
                            fltvol.setFilenameSuffix(suffix)
                            fltvol.save()
                    else:
                        wait.close()
                        return
                """
                    Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    # Parameters
                    params = self._settings2.getParametersList()
                    automask = self._settings2.getParameterValue(params[0])
                    shrink = self._settings2.getParameterValue(params[1])
                    splineorder = self._settings2.getParameterValue(params[2])
                    bins = self._settings2.getParameterValue(params[3])
                    levels = self._settings2.getParameterValue(params[4])
                    points = self._settings2.getParameterValue(params[5])
                    niter = self._settings2.getParameterValue(params[6])
                    convergence = self._settings2.getParameterValue(params[7])
                    filternoise = self._settings2.getParameterValue(params[8])
                    biasfwhm = self._settings2.getParameterValue(params[9])
                    prefix = self._settings2.getParameterValue(params[10])
                    suffix = self._settings2.getParameterValue(params[11])
                    # Process
                    fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                       splineorder, filternoise, points, niter, automask, wait)
                    if wait.getStopped():
                        wait.close()
                        return
                    del bias
                    fltvol.copyAttributesFrom(vol)
                    fltvol.setFilename(vol.getFilename())
                    fltvol.setFilenamePrefix(prefix)
                    fltvol.setFilenameSuffix(suffix)
                    fltvol.save()
                """
                    Third stage - Unsupervised KMeans segmentation
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} Segmentation initialization...'.format(vol.getBasename()))
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                # Parameters
                params = self._settings.getParametersList()
                prefix = self._settings2.getParameterValue(params[2])
                suffix = self._settings2.getParameterValue(params[3])
                # Process
                fltvol = kmeans(fltvol, mask, wait)
                if wait.getStopped():
                    wait.close()
                    return
                """
                    Save volume
                """
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                fltvol.copyAttributesFrom(vol)
                fltvol.acquisition.setModalityToLB()
                fltvol.setFilename(vol.getFilename())
                fltvol.setFilenamePrefix(prefix)
                fltvol.setFilenameSuffix(suffix)
                fltvol.save()
                wait.close()
                self._volumeSelect.clear()
                self._maskSelect.clear()


class DialogSupervisedKMeans(QDialog):
    """
        DialogSupervisedKMeans

        Description

            GUI dialog for supervised KMeans segmentation.

        Inheritance

            QDialog -> DialogSupervisedKMeans

        Private attributes

            _volumeSelect       FilesSelectionWidget
            _settings           FunctionSettingsWidget

        Public methods

            execute()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Supervised KMeans segmentation')

        # Init non-GUI attributes

        self._pos = 0
        self._stdout = ''

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget()
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._maskSelect = FilesSelectionWidget()
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Mask(s)')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(False)

        self._mask = QCheckBox('Use mask(s)')
        self._mask.setChecked(False)
        self._mask.toggled.connect(self._maskSelect.setVisible)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._mask)
        self._layout.addWidget(self._maskSelect)

        self._settings1 = FunctionSettingsWidget('NonLocalMeansImageFilter')
        self._settings1.VisibilityToggled.connect(self._center)

        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.VisibilityToggled.connect(self._center)

        self._settings = FunctionSettingsWidget('SupervisedKMeans')
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('NonLocalMeansFilter').toggled.connect(self._setting1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._setting2.setVisible)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

    # Private method

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateLocalMeansFilterProgress(self, wait):
        if isinstance(wait, DialogWait):
            lock = Lock()
            with lock:
                with open(self._stdout, 'r') as f:
                    verbose = f.readlines()
            if len(verbose) > 0:
                for line in reversed(verbose):
                    if line[0] == '*': wait.setCurrentProgressValue(len(line))
        else: raise TypeError('parameter type {} is not DialogWait.'.format(type(wait)))

    def _updateAtroposProgress(self, wait):
        if isinstance(wait, DialogWait):
            lock = Lock()
            with lock:
                with open(self._stdout, 'r') as f:
                    f.seek(self._pos)
                    verbose = f.readlines()
                    self._pos = f.tell()
            if len(verbose) > 0:
                for line in reversed(verbose):
                    line = line.lstrip()
                    if line[0] == 'I':
                        citer = int(line.split(' ')[1])
                        wait.setCurrentProgressValue(citer+1)
                    elif line[0] == 'W':
                        wait.incCurrentProgressValue()
        else: raise TypeError('parameter type {} is not DialogWait.'.format(type(wait)))

    # Public method

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            filemasks = self._maskSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            queue = Queue()
            wait = DialogWait(parent=self)
            for i in range(len(filenames)):
                vol.load(filenames[i])
                if i < len(filemasks):
                    mask = SisypheVolume()
                    mask.load(filemasks[i])
                    if not mask.hasSameFieldOfView(vol):
                        QMessageBox.warning(self, self.windowTitle(),
                                            '{} and {} do not have the same FOV.'.format(vol.getBasename(),
                                                                                         mask.getBasename()))
                        mask = None
                """
                    First stage - Non local means filter denoising
                """
                if self._settings.getParameterValue('NonLocalMeansFilter'):
                    wait.setInformationText('{} non locals means filter initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    self._stdout = join(vol.getDirname(), 'stdout.log')
                    wait.setProgressRange(0, 107)
                    wait.setCurrentProgressValue(0)
                    # Parameters
                    params = self._settings1.getParametersList()
                    shrink = self._settings1.getParameterValue(params[0])
                    patchradius = self._settings1.getParameterValue(params[1])
                    searchradius = self._settings1.getParameterValue(params[2])
                    noise = self._settings1.getParameterValue(params[3])[0]
                    prefix = self._settings1.getParameterValue(params[4])
                    suffix = self._settings1.getParameterValue(params[5])
                    # Process
                    flt = ProcessNonLocalMeansFilter(vol, shrink, patchradius, searchradius, noise, self._stdout, queue)
                    try:
                        wait.open()
                        flt.start()
                        wait.setInformationText('{} non locals means filter...'.format(vol.getBasename()))
                        wait.setButtonVisibility(True)
                        wait.setProgressVisibility(True)
                        while flt.is_alive():
                            QApplication.processEvents()
                            if exists(self._stdout): self._updateLocalMeansFilterProgress(wait)
                            if self._wait.getStopped(): flt.terminate()
                    except Exception as err:
                        if flt.is_alive(): flt.terminate()
                        wait.hide()
                        wait.close()
                        QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                        return
                    finally:
                        # Remove temporary std::cout file
                        if exists(self._stdout): remove(self._stdout)
                    if not queue.empty():
                        img = queue.get()
                        if img is not None:
                            fltvol = SisypheVolume()
                            fltvol.copyAttributesFrom(vol)
                            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                            fltvol.setFilename(vol.getFilename())
                            fltvol.setFilenamePrefix(prefix)
                            fltvol.setFilenameSuffix(suffix)
                            fltvol.save()
                    else:
                        wait.close()
                        return
                """
                    Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    # Parameters
                    params = self._settings2.getParametersList()
                    automask = self._settings2.getParameterValue(params[0])
                    shrink = self._settings2.getParameterValue(params[1])
                    splineorder = self._settings2.getParameterValue(params[2])
                    bins = self._settings2.getParameterValue(params[3])
                    levels = self._settings2.getParameterValue(params[4])
                    points = self._settings2.getParameterValue(params[5])
                    niter = self._settings2.getParameterValue(params[6])
                    convergence = self._settings2.getParameterValue(params[7])
                    filternoise = self._settings2.getParameterValue(params[8])
                    biasfwhm = self._settings2.getParameterValue(params[9])
                    prefix = self._settings2.getParameterValue(params[10])
                    suffix = self._settings2.getParameterValue(params[11])
                    # Process
                    fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                       splineorder, filternoise, points, niter, automask, wait)
                    if wait.getStopped():
                        wait.close()
                        return
                    del bias
                    fltvol.copyAttributesFrom(vol)
                    fltvol.setFilename(vol.getFilename())
                    fltvol.setFilenamePrefix(prefix)
                    fltvol.setFilenameSuffix(suffix)
                    fltvol.save()
                """
                    Third stage - Supervised KMeans segmentation
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} Segmentation initialization...'.format(vol.getBasename()))
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                # Parameters
                params = self._settings.getParametersList()
                nclass = self._settings2.getParameterValue(params[2])
                niter = self._settings2.getParameterValue(params[3])
                smooth = self._settings2.getParameterValue(params[4])
                radius = self._settings2.getParameterValue(params[5])
                segprefix = self._settings2.getParameterValue(params[6])
                segsuffix = self._settings2.getParameterValue(params[7])
                classprefix = self._settings2.getParameterValue(params[8])
                classsuffix = self._settings2.getParameterValue(params[9])
                wait.setProgressRange(0, niter+1)
                wait.setCurrentProgressValue(0)
                # Process
                conv = '[{},0]'.format(niter)
                init = 'Kmeans[{}]'.format(nclass)
                mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
                weight = 0.0
                flt = ProcessAtropos(fltvol, mask, init, mrf, conv, weight, self._stdout, queue)
                try:
                    flt.start()
                    wait.setInformationText('{} segmentation...'.format(vol.getBasename()))
                    wait.setButtonVisibility(True)
                    wait.setProgressVisibility(True)
                    while flt.is_alive():
                        QApplication.processEvents()
                        if exists(self._stdout): self._updateAtroposProgress(wait)
                        if self._wait.getStopped(): flt.terminate()
                except Exception as err:
                    if flt.is_alive(): flt.terminate()
                    wait.hide()
                    wait.close()
                    QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                    return
                finally:
                    # Remove temporary std::cout file
                    if exists(self._stdout): remove(self._stdout)
                """
                    Save volume
                """
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                if not queue.empty():
                    img = queue.get()
                    if img is not None:
                        fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                        fltvol.copyAttributesFrom(vol)
                        fltvol.acquisition.setModalityToLB()
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(segprefix)
                        fltvol.setFilenameSuffix(segsuffix)
                        wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                        fltvol.save()
                    for i in range(nclass):
                        img = queue.get()
                        if img is not None:
                            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                            fltvol.copyAttributesFrom(vol)
                            fltvol.acquisition.setModalityToOT()
                            fltvol.acquisition.setUnitToPercent()
                            fltvol.setFilename(vol.getFilename())
                            if classprefix != '':
                                if '*' in classprefix: classprefix = classprefix.replace('*', str(i))
                                elif '_' in classprefix: classprefix = classprefix.replace('_', '_'+str(i))
                                elif '-' in classprefix: classprefix = classprefix.replace('-', '-' + str(i))
                                else: classprefix += str(i)
                            if classsuffix != '':
                                if '*' in classsuffix: classsuffix = classsuffix.replace('*', str(i))
                                elif '_' in classsuffix: classsuffix = classsuffix.replace('_', '_'+str(i))
                                elif '-' in classsuffix: classsuffix = classsuffix.replace('-', '-' + str(i))
                                else: classsuffix += str(i)
                            fltvol.setFilenamePrefix(classprefix)
                            fltvol.setFilenameSuffix(classsuffix)
                            wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                            fltvol.save()
                wait.close()
                self._volumeSelect.clear()
                self._maskSelect.clear()


class DialogPriorBasedSegmentation(QDialog):
    """
        DialogPriorBasedSegmentation

        Description

            GUI dialog for prior based segmentation.

        Inheritance

            QDialog -> DialogPriorBasedSegmentation

        Private attributes

            _volumeSelect       FilesSelectionWidget
            _settings           FunctionSettingsWidget

        Public methods

            execute()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Prior based segmentation')

        # Init non-GUI attributes

        self._pos = 0
        self._cstage = 0
        self._clevel = 0
        self._citer = 0
        self._cprogress = 0
        self._conv = list()
        self._progbystage = list()
        self._progbylevel = list()
        self._stdout = ''
        self._priors = list()

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget()
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._settings1 = FunctionSettingsWidget('NonLocalMeansImageFilter')
        self._settings1.VisibilityToggled.connect(self._center)
        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.VisibilityToggled.connect(self._center)
        self._settings3 = FunctionSettingsWidget('Registration')
        self._settings3.VisibilityToggled.connect(self._center)
        self._settings = FunctionSettingsWidget('PriorBasedSegmentation')
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('NonLocalMeansFilter').toggled.connect(self._setting1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._setting2.setVisible)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)
        self._layout.addWidget(self._settings3)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

    # Private method

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _updateLocalMeansFilterProgress(self, wait):
        if isinstance(wait, DialogWait):
            lock = Lock()
            with lock:
                with open(self._stdout, 'r') as f:
                    verbose = f.readlines()
            if len(verbose) > 0:
                for line in reversed(verbose):
                    if line[0] == '*': wait.setCurrentProgressValue(len(line))
        else: raise TypeError('parameter type {} is not DialogWait.'.format(type(wait)))

    def _updateRegistrationProgress(self, wait):
        lock = Lock()
        with lock:
            with open(self._stdout, 'r') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            citer = 0
            cprogress = 0
            plevel = self._clevel
            for line in reversed(verbose):
                sub = line[:5]
                # Current iter
                if sub in (' 2DIA', ' 1DIA'):
                    # 2DIA Rigid/Affine, 1DIA Displacement Field
                    if cprogress == 0:
                        w = line.split(',')
                        if len(w) > 4:  # line contains convergence value
                            citer = int(w[1])
                            v = float(w[3])
                            if isinf(v): cprogress = 0
                            else:
                                if self._cstage == 0: cconv = self._conv[0]
                                else: cconv = self._conv[self._cstage - 1]
                                cprogress = (log10(float(w[3])) + cconv) / cconv
                            continue
                # Current level Affine/Rigid
                elif sub in ('DIAGN', 'XXDIA'):
                    # DIAGN Rigid/Affine, XXDIA Displacement Field
                    self._clevel += 1
                    continue
                # Current stage
                elif sub == 'Stage':
                    w = line.split(' ')
                    if len(w) == 2:
                        self._cstage = int(w[1]) + 1
                        wait.setProgressRange(0, self._progbystage[self._cstage - 1][-1])
                        wait.setCurrentProgressValue(0)
                        self._clevel = self._clevel - plevel
                        break
            # Update current iter and current progress
            if plevel == self._clevel:
                if citer > self._citer: self._citer = citer
                if cprogress > self._cprogress: self._cprogress = cprogress
            else:
                self._citer = citer
                self._cprogress = cprogress
            if self._cstage > 0 and self._clevel > 0:
                v = citer / self._multir[self._cstage-1][self._clevel-1]
                if v > self._cprogress: self._cprogress = v
                nb1 = self._progbystage[self._cstage - 1]
                nb2 = self._progbylevel[self._cstage - 1]
                v = int(nb1[self._clevel - 1] + nb2[self._clevel - 1] * self._cprogress)
                info = 'Registration stage {}/{} {}\nMultiresolution Level {}/{}'.format(self._cstage,
                                                                                         len(self._stages),
                                                                                         self._stages[self._cstage-1],
                                                                                         self._clevel,
                                                                                         len(self._multir[self._cstage-1]))
            else:
                v = 0
                info = 'Registration stage 1/{} {}\nMultiresolution Level 1/{}'.format(len(self._stages),
                                                                                       self._stages[0],
                                                                                       len(self._multir[0]))
            wait.setInformationText(info)
            wait.setCurrentProgressValue(v)

    def _updateAtroposProgress(self, wait):
        if isinstance(wait, DialogWait):
            if isinstance(wait, DialogWait):
                lock = Lock()
                with lock:
                    with open(self._stdout, 'r') as f:
                        f.seek(self._pos)
                        verbose = f.readlines()
                        self._pos = f.tell()
                if len(verbose) > 0:
                    for line in reversed(verbose):
                        line = line.lstrip()
                        if line[0] == 'I':
                            citer = int(line.split(' ')[1])
                            wait.setCurrentProgressValue(citer+1)
                        elif line[0] == 'W':
                            wait.incCurrentProgressValue()
        else: raise TypeError('parameter type {} is not DialogWait.'.format(type(wait)))

    # Public method

    def execute(self):  # to do
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            filemasks = self._maskSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            queue = Queue()
            wait = DialogWait(parent=self)
            for i in range(len(filenames)):
                vol.load(filenames[i])
                if i < len(filemasks):
                    mask = SisypheVolume()
                    mask.load(filemasks[i])
                    if not mask.hasSameFieldOfView(vol):
                        QMessageBox.warning(self, self.windowTitle(),
                                            '{} and {} do not have the same FOV.'.format(vol.getBasename(),
                                                                                         mask.getBasename()))
                        mask = None
                """
                    First stage - Non local means filter denoising
                """
                if self._settings.getParameterValue('NonLocalMeansFilter'):
                    wait.setInformationText('{} non locals means filter initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    self._stdout = join(vol.getDirname(), 'stdout.log')
                    wait.setProgressRange(0, 107)
                    wait.setCurrentProgressValue(0)
                    # Parameters
                    params = self._settings1.getParametersList()
                    shrink = self._settings1.getParameterValue(params[0])
                    patchradius = self._settings1.getParameterValue(params[1])
                    searchradius = self._settings1.getParameterValue(params[2])
                    noise = self._settings1.getParameterValue(params[3])[0]
                    prefix = self._settings1.getParameterValue(params[4])
                    suffix = self._settings1.getParameterValue(params[5])
                    # Process
                    flt = ProcessNonLocalMeansFilter(vol, shrink, patchradius, searchradius, noise, self._stdout, queue)
                    try:
                        wait.open()
                        flt.start()
                        wait.setInformationText('{} non locals means filter...'.format(vol.getBasename()))
                        wait.setButtonVisibility(True)
                        wait.setProgressVisibility(True)
                        while flt.is_alive():
                            QApplication.processEvents()
                            if exists(self._stdout): self._updateLocalMeansFilterProgress(wait)
                            if self._wait.getStopped(): flt.terminate()
                    except Exception as err:
                        if flt.is_alive(): flt.terminate()
                        wait.hide()
                        wait.close()
                        QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                        return
                    finally:
                        # Remove temporary std::cout file
                        if exists(self._stdout): remove(self._stdout)
                    if not queue.empty():
                        img = queue.get()
                        if img is not None:
                            fltvol = SisypheVolume()
                            fltvol.copyAttributesFrom(vol)
                            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                            fltvol.setFilename(vol.getFilename())
                            fltvol.setFilenamePrefix(prefix)
                            fltvol.setFilenameSuffix(suffix)
                            fltvol.save()
                    else:
                        wait.close()
                        return
                """
                    Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction initialization...'.format(vol.getBasename()))
                    wait.setButtonVisibility(False)
                    wait.setProgressVisibility(False)
                    # Parameters
                    params = self._settings2.getParametersList()
                    automask = self._settings2.getParameterValue(params[0])
                    shrink = self._settings2.getParameterValue(params[1])
                    splineorder = self._settings2.getParameterValue(params[2])
                    bins = self._settings2.getParameterValue(params[3])
                    levels = self._settings2.getParameterValue(params[4])
                    points = self._settings2.getParameterValue(params[5])
                    niter = self._settings2.getParameterValue(params[6])
                    convergence = self._settings2.getParameterValue(params[7])
                    filternoise = self._settings2.getParameterValue(params[8])
                    biasfwhm = self._settings2.getParameterValue(params[9])
                    prefix = self._settings2.getParameterValue(params[10])
                    suffix = self._settings2.getParameterValue(params[11])
                    # Process
                    fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                       splineorder, filternoise, points, niter, automask, wait)
                    if wait.getStopped():
                        wait.close()
                        return
                    del bias
                    fltvol.copyAttributesFrom(vol)
                    fltvol.setFilename(vol.getFilename())
                    fltvol.setFilenamePrefix(prefix)
                    fltvol.setFilenameSuffix(suffix)
                    fltvol.save()
                """
                    Third stage - Priors registration
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} registration initialization...'.format(vol.getBasename()))
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                # Priors parameters
                params = self._settings.getParametersList()
                ft1 = self._settings.getParameterValue(params[9])
                if exists(ft1):
                    fmask = self._settings.getParameterValue(params[10])
                    fcgm = self._settings.getParameterValue(params[11])
                    fscgm = self._settings.getParameterValue(params[12])
                    fwm = self._settings.getParameterValue(params[13])
                    fcsf = self._settings.getParameterValue(params[14])
                    fbstem = self._settings.getParameterValue(params[15])
                    fcereb = self._settings.getParameterValue(params[16])
                    mvol = SisypheVolume()
                    mvol.load(ft1)
                    """
                        Estimating translations
                    """
                    f = CenteredTransformInitializerFilter()
                    img1 = Cast(fltvol.getSITKImage(), sitkFloat32)
                    img2 = Cast(mvol.getSITKImage(), sitkFloat32)
                    trf = AffineTransform(f.Execute(img1, img2, self._trf.getSITKTransform()))
                    self._trf.setSITKTransform(trf)
                    del img1, img2
                    """
                        Registration mask
                    """
                    img = fltvol.getSITKImage()
                    img = img >= mean(fltvol.getNumpy().flatten())
                    img = BinaryDilate(img, [4, 4, 4])
                    img = BinaryFillhole(img)
                    regmask = SisypheVolume()
                    regmask.setSITKImage(img)
                    """
                        Registration
                    """
                    reg = ProcessRegistration(fltvol, mvol, regmask, self._trf, 'ElasticSyN', 'mattes',
                                              0.2, 3, (40, 20, 0), True, self._stdout, queue)
                    self._wait.buttonVisibilityOn()
                    self._wait.setStages(['Affine', 'Elastic'])
                    self._wait.setMultiResolutionIterations([[2100, 1200, 200, 1], [40, 20, 1]])
                    self._wait.setProgressByLevel([[100, 200, 400, 0], [100, 200, 0]])
                    self._wait.setConvergenceThreshold([6, 7])
                    try:
                        reg.start()
                        while reg.is_alive():
                            QApplication.processEvents()
                            if exists(self._stdout): self._updateRegistrationProgress(wait)
                            if self._wait.getStopped(): reg.terminate()
                    except Exception as err:
                        if reg.is_alive(): reg.terminate()
                        self._wait.hide()
                        QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                        raise Exception
                    finally:
                        # Remove temporary std::cout file
                        if exists(self._stdout): remove(self._stdout)
                    del regmask, mvol
                    self._wait.buttonVisibilityOff()
                    self._wait.setProgressVisibility(False)
                    """
                        Priors resampling
                    """
                    trf = None
                    if not queue.empty():
                        trf = queue.get()
                """
                    Fourth stage - Finite mixture modeling
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} Segmentation initialization...'.format(vol.getBasename()))
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                # Parameters
                params = self._settings.getParametersList()
                niter = self._settings.getParameterValue(params[3])
                nclass = self._settings.getParameterValue(params[4])[0]
                weight = self._settings.getParameterValue(params[5])
                smooth = self._settings.getParameterValue(params[6])
                radius = self._settings.getParameterValue(params[7])
                conv = self._settings.getParameterValue(params[8])[0]
                segprefix = self._settings.getParameterValue(params[17])
                segsuffix = self._settings.getParameterValue(params[18])
                wait.setProgressRange(0, niter + 1)
                wait.setCurrentProgressValue(0)
                # Process
                if conv[0] == 'N': conv = '[{},0]'.format(niter)
                else: conv = '[{},{}]'.format(niter, float(conv))
                mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
                flt = ProcessAtropos(fltvol, mask, self._priors, mrf, conv, weight, self._stdout, queue)
                try:
                    flt.start()
                    wait.setInformationText('{} segmentation...'.format(vol.getBasename()))
                    wait.setButtonVisibility(True)
                    wait.setProgressVisibility(True)
                    while flt.is_alive():
                        QApplication.processEvents()
                        if exists(self._stdout): self._updateAtroposProgress(wait)
                        if self._wait.getStopped(): flt.terminate()
                except Exception as err:
                    if flt.is_alive(): flt.terminate()
                    wait.hide()
                    wait.close()
                    QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                    return
                finally:
                    # Remove temporary std::cout file
                    if exists(self._stdout): remove(self._stdout)
                """
                    Save volumes
                """
                wait.setButtonVisibility(False)
                wait.setProgressVisibility(False)
                if not queue.empty():
                    img = queue.get()
                    if img is not None:
                        fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                        fltvol.copyAttributesFrom(vol)
                        fltvol.acquisition.setModalityToLB()
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(segprefix)
                        fltvol.setFilenameSuffix(segsuffix)
                        wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                        fltvol.save()
                    for i in range(nclass):
                        img = queue.get()
                        if img is not None:
                            fltvol.copyFromNumpyArray(img, vol.getSpacing(), vol.getOrigin(), defaultshape=False)
                            fltvol.copyAttributesFrom(vol)
                            fltvol.acquisition.setModalityToOT()
                            fltvol.acquisition.setUnitToPercent()
                            fltvol.setFilename(vol.getFilename())

                            fltvol.setFilenamePrefix(prefix)
                            fltvol.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                            fltvol.save()
                    if mask is not None:
                        mask.copyAttributesFrom(vol)
                        mask.acquisition.setModalityToOT()
                        mask.acquisition.setSequenceToMask()
                        mask.setFilenamePrefix('mask_')
                        wait.setInformationText('Save {}'.format(mask.getBasename()))
                        mask.save()
                wait.close()
                self._volumeSelect.clear()
                self._maskSelect.clear()


class DialogRegistrationBasedSegmentation(QDialog):
    """
         DialogRegistrationBasedSegmentation

         Description

             GUI dialog for registration based segmentation.

         Inheritance

             QDialog -> DialogRegistrationBasedSegmentation

         Private attributes

             _volumeSelect       FilesSelectionWidget
             _settings           FunctionSettingsWidget

         Public methods

             execute()

             inherited QDialog methods
     """

    # Special method

    def __init__(self, filename='', parent=None):
        super().__init__(parent)

        # Init window

        if filename == '': title = 'Registration based segmentation'
        else: title = '{} registration based segmentation'.format(basename(filename))
        self.setWindowTitle(title)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget()
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._templatesSelect = SynchronizedFilesSelectionWidget(singles=('Template',), multiples=('Struct',))

        self._mask = LabeledComboBox(title='Struct mask')
        self._mask.addItem('No')
        self._mask.addItem('Cortical gray matter')
        self._mask.addItem('Sub-cortical gray matter')
        self._mask.addItem('Gray matter')
        self._mask.addItem('White matter')
        self._mask.addItem('Cerebro-spinal fluid')
        self._mask.setCurrentIndex(0)

        self._regsettings = FunctionSettingsWidget('Registration')
        self._regsettings.VisibilityToggled.connect(self._center)
        self._regsettings.setSettingsButtonFunctionText()
        self._regsettings.setParameterVisibility('Rigid', False)
        self._regsettings.setParameterVisibility('Affine', False)
        self._regsettings.setParameterVisibility('DisplacementField', self._reg == 'DisplacementField')
        self._regsettings.setParameterVisibility('ManualRegistration', False)
        self._regsettings.setParameterVisibility('CheckRegistration', False)
        self._regsettings.setParameterVisibility('Prefix', False)
        self._regsettings.setParameterVisibility('Suffix', False)
        self._regsettings.setParameterVisibility('Resample', False)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._templatesSelect)
        self._layout.addWidget(self._mask)
        self._layout.addWidget(self._regsettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        save = QPushButton('Save')
        save.setFixedWidth(100)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addWidget(save)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        save.clicked.connect(self.save)
        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

        if filename != '' and exists(filename):
            self._filename = filename
            self.load()
        else: self._filename = ''

    # Private method

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def load(self):
        if self._filename == '' or not exists(self._filename):
            filt = 'XML settings (*.xml)'
            path = join(getUserPySisyphePath(), 'segmentation')
            filename = QFileDialog.getOpenFileName(self, 'Open XML settings', path, filt)
            QApplication.processEvents()
            filename = filename[0]
        else: filename = self._filename
        if filename:
            settings = SisypheSettings(setting=filename)
            if settings.hasSection('RegistrationBasedSegmentation'):
                filenames = dict()
                filenames['Template'] = settings.getFieldValue('RegistrationBasedSegmentation', 'template')
                filenames['Struct'] = settings.getFieldValue('RegistrationBasedSegmentation', 'struct')
                self._templatesSelect['Template'].open(filenames['Template'])
                for filename in filenames['Struct']:
                    self._templatesSelect['Struct'].add(filename)
                self._templatesSelect.setFilenames(self, filenames)
                algo = settings.getFieldValue('RegistrationBasedSegmentation', 'algo')
                self._regsettings.getParameterWidget('DisplacementField').setCurrentText(algo[0])
                mask = settings.getFieldValue('RegistrationBasedSegmentation', 'mask')
                self._mask.setCurrentText(mask[0])
            else:
                QMessageBox.warning(self,
                                    'Open registration based segmentation settings...',
                                    '{} is not a registration based segmentation settings file.'.format(basename(filename)))

    def save(self):
        if self._filename == '' or not exists(self._filename):
            filt = 'XML settings (*.xml)'
            path = join(getUserPySisyphePath(), 'segmentation')
            filename = QFileDialog.getSaveFileName(self, 'Save XML settings', path, filt)
            QApplication.processEvents()
            filename = filename[0]
        else: filename = self._filename
        if filename:
            settings = SisypheSettings(setting='')
            settings.newSection('RegistrationBasedSegmentation')
            settings.newField('RegistrationBasedSegmentation', 'template', attrs={'vartype': 'vol'})
            settings.newField('RegistrationBasedSegmentation', 'struct', attrs={'vartype': 'vols'})
            settings.newField('RegistrationBasedSegmentation', 'algo', attrs={'vartype': 'lstr'})
            settings.newField('RegistrationBasedSegmentation', 'mask', attrs={'vartype': 'lstr'})
            v = self._templatesSelect['Template'].getFilename()
            settings.setFieldValue('RegistrationBasedSegmentation', 'template', v)
            v = self._templatesSelect['Struct'].getFilenames()
            settings.setFieldValue('RegistrationBasedSegmentation', 'struct', v)
            settings.setFieldValue('RegistrationBasedSegmentation', 'algo', self._regsettings.getParameterValue('DisplacementField'))
            v = [self._mask.currentText()]
            for i in range(self._mask.count()):
                if i != self._mask.currentIndex():
                    v.append(self._mask.itemText(i))
            settings.setFieldValue('RegistrationBasedSegmentation', 'mask', v)
            settings.saveAs(filename)

    def execute(self):
        if not self._volumeSelect.isEmpty() and self._templatesSelect.isReady():
            wait = DialogWait()
            algo = self._regsettings.getParameterValue('DisplacementField')
            templates = self._templatesSelect.getFilenames()
            mvol = SisypheVolume()
            mvol.load(templates['Template'][0])
            rvol = list()
            for sfilename in templates['Struct']:
                rvol.append(SisypheVolume())
                rvol[-1].load(sfilename)
            for filename in self._volumeSelect.getFilenames():
                fvol = SisypheVolume()
                fvol.load(filename)
                for i in range(len(templates['Struct'])):
                    prefix = rvol[i].getFilename()
                    rvol[i].setFilename(fvol.getFilename())
                    rvol[i].setFilenamePrefix('{}_'.format(prefix))
                svol = antsRegistration(fvol, mvol, rvol=rvol, algo=algo, interpol='linear',
                                        prefix='', suffix='', fprefix='field_', fsuffix='', wait=wait)
                maskname = ''
                c = self._mask.currentIndex()
                # Cortical gray matter mask
                if c == 1:
                    maskname = join(dirname(filename), '{}{}'.format('cortical_gm_', basename(filename)))
                    if not exists(maskname):
                        maskname = join(dirname(filename), '{}{}'.format('gm_', basename(filename)))
                # Sub-cortical gray matter mask
                elif c == 2:
                    maskname = join(dirname(filename), '{}{}'.format('subcortical_gm_', basename(filename)))
                    if not exists(maskname):
                        maskname = join(dirname(filename), '{}{}'.format('gm_', basename(filename)))
                # Gray matter
                elif c == 3:
                    maskname = join(dirname(filename), '{}{}'.format('gm_', basename(filename)))
                    if not exists(maskname):
                        m1 = join(dirname(filename), '{}{}'.format('cortical_gm_', basename(filename)))
                        m2 = join(dirname(filename), '{}{}'.format('subcortical_gm_', basename(filename)))
                        if exists(m1) and exists(m2):
                            vol1 = SisypheVolume()
                            vol2 = SisypheVolume()
                            vol1.load(m1)
                            vol2.load(m2)
                            r = vol1.getSITKImage() + vol2.getSITKImage()
                            vol1.setSITKImage(r)
                            vol1.saveAs(filename)
                # White matter mask
                elif c == 4:
                    maskname = join(dirname(filename), '{}{}'.format('wm_', basename(filename)))
                # Cerebro-spinal fluid mask
                elif c == 5:
                    maskname = join(dirname(filename), '{}{}'.format('csf_', basename(filename)))
                if exists(maskname):
                    mask = SisypheVolume()
                    mask.load(maskname)
                    mask = mask.getSITKImage() > 0.5
                    prefix = maskname.split('_')[0]
                    for vol in svol:
                        mask = mask * vol.getSITKImage()
                        vol.setSITKImage(mask)
                        vol.setFilenamePrefix(prefix)
                        vol.save()


"""
    Test
"""

if __name__ == '__main__':
    from sys import argv
    from os import chdir

    app = QApplication(argv)
    main = DialogRegistrationBasedSegmentation()
    main.show()
    app.exec_()
