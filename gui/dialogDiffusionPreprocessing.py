"""
External packages/modules
-------------------------

    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import basename
from os.path import splitext
from os.path import exists

from dipy.core.gradients import gradient_table

from multiprocessing import Queue
from multiprocessing import Manager

from numpy import array

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.processing.dipyFunctions import dwiPreprocessing
from Sisyphe.processing.capturedStdoutProcessing import ProcessDiffusionPreprocessing
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDiffusionPreprocessing']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDiffusionPreprocessing
"""

class DialogDiffusionPreprocessing(QDialog):
    """
    DialogDiffusionPreprocessing

    Description
    ~~~~~~~~~~~

    GUI dialog window for diffusion-weighted images preprocessing.
    (Brain extraction, Gibbs suppression, denoising)

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDiffusionPreprocessing

    Last revision: 11/07/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Diffusion preprocessing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._bvals = FileSelectionWidget()
        self._bvals.filterExtension('.xbval')
        self._bvals.setTextLabel('B-values')
        self._bvals.FieldChanged.connect(self._updateBVals)
        self._bvals.FieldCleared.connect(self._bvalsCleared)

        self._bvecs = FileSelectionWidget()
        self._bvecs.filterExtension('.xbvec')
        self._bvecs.setTextLabel('Gradient directions')
        self._bvecs.alignLabels(self._bvals)
        self._bvecs.FieldChanged.connect(self._updateBVecs)
        self._bvecs.FieldCleared.connect(self._bvecsCleared)

        self._preproc = FunctionSettingsWidget('DiffusionPreprocessing')
        self._preproc.settingsVisibilityOn()
        self._preproc.hideIOButtons()
        self._preproc.setSettingsButtonFunctionText()
        self._preproc.VisibilityToggled.connect(self._center)

        self._combo = self._preproc.getParameterWidget('Denoise')
        self._combo.currentIndexChanged.connect(lambda: self._denoiseChanged())

        self._check = self._preproc.getParameterWidget('GibbsSuppression')
        self._check.clicked.connect(lambda: self._denoiseChanged())

        self._rec = self._preproc.getParameterWidget('MRReconstruction')
        self._rec.currentIndexChanged.connect(lambda: self._reconstructionChanged())

        self._noise = self._preproc.getParameterWidget('NoiseEstimation')
        self._noise.currentIndexChanged.connect(lambda: self._noiseEstimationChanged())

        self._pca = FunctionSettingsWidget('PCADenoise')
        self._pca.settingsVisibilityOn()
        self._pca.hideIOButtons()
        self._pca.setSettingsButtonText('PCA Denoising')
        self._pca.VisibilityToggled.connect(self._center)
        self._pca.setVisible(False)

        self._nlmeans = FunctionSettingsWidget('NLMeansDenoise')
        self._nlmeans.settingsVisibilityOn()
        self._nlmeans.hideIOButtons()
        self._nlmeans.setSettingsButtonText('Non-Local Means Denoising')
        self._nlmeans.VisibilityToggled.connect(self._center)
        self._nlmeans.setVisible(False)

        self._supervised = FunctionSettingsWidget('SelfSupervisedDenoise')
        self._supervised.settingsVisibilityOn()
        self._supervised.hideIOButtons()
        self._nlmeans.setSettingsButtonText('Self Supervised Denoising')
        self._supervised.VisibilityToggled.connect(self._center)
        self._supervised.setVisible(False)

        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)
        self._layout.addWidget(self._preproc)
        self._layout.addWidget(self._pca)
        self._layout.addWidget(self._nlmeans)
        self._layout.addWidget(self._supervised)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._exit = QPushButton('Close')
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        self._exit.setFixedWidth(100)
        self._exec = QPushButton('Execute')
        self._exec.setFixedWidth(100)
        self._exec.setToolTip('Run diffusion preprocessing.')
        self._exec.setEnabled(False)
        layout.addWidget(self._exit)
        layout.addWidget(self._exec)
        layout.addStretch()

        self._layout.addLayout(layout)

        self._denoiseChanged()
        self._reconstructionChanged()
        self._noiseEstimationChanged()

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self.accept)
        # < Revision 11/07/2025
        # noinspection PyUnresolvedReferences
        # self._exec.clicked.connect(self.execute)
        self._exec.clicked.connect(self.multiExecute)
        # Revision 11/07/2025 >

        # < Revision 17/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._bvals.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 17/06/2025 >
        self.setModal(True)

        self._center(None)

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _bvalsCleared(self):
        self._exec.setEnabled(False)
        self._bvals.setToolTip('')

    def _bvecsCleared(self):
        self._exec.setEnabled(False)
        self._bvecs.setToolTip('')

    def _updateBVals(self):
        try: v1 = loadBVal(self._bvals.getFilename(), format='xml')
        except:
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvals.getFilename())))
            self._bvals.clear(signal=False)
            self._bvals.setToolTip('')
            # < Revision 18/06/2025
            # self._exec.setEnabled(False)
            self._denoiseChanged()
            # Revision 18/06/2025 >
            return None
        v = list(v1.values())
        if len(v) > 1:
            dwi = list(v1.keys())
            buff = '{}: {}'.format(basename(dwi[0]), str(v[0]))
            for i in range(1, len(v)):
                buff += '\n{}: {}'.format(basename(dwi[i]), str(v[i]))
            self._bvals.setToolTip(buff)
        filename = splitext(self._bvals.getFilename())[0] + '.xbvec'
        if exists(filename):
            try: v2 = loadBVec(filename, format='xml')
            except:
                messageBox(self,
                           title=self.windowTitle(),
                           text='{} format is invalid.'.format(basename(filename)))
                return None
            if list(v1.keys()) == list(v2.keys()):
                self._bvecs.open(filename, signal=False)
                self._exec.setEnabled(not (self._bvals.isEmpty() and self._bvecs.isEmpty()))
                v = list(v2.values())
                if len(v) > 1:
                    dwi = list(v2.keys())
                    buff = '{}: {}'.format(basename(dwi[0]), ' '.join([str(j) for j in v[0]]))
                    for i in range(1, len(v)):
                        buff += '\n{}: {}'.format(basename(dwi[i]), ' '.join([str(j) for j in v[i]]))
                    # noinspection PyInconsistentReturns
                    self._bvecs.setToolTip(buff)
                else: raise ValueError('b-vectors and b-values count <= 1.')
            else: raise ValueError('b-vectors and b-values mismatch.')
        else: raise IOError('No such file {}'.format(filename))

    def _updateBVecs(self):
        try: v1 = loadBVec(self._bvecs.getFilename(), format='xml')
        except:
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvecs.getFilename())))
            self._bvecs.clear(signal=False)
            self._bvecs.setToolTip('')
            # < Revision 18/06/2025
            # self._exec.setEnabled(False)
            self._denoiseChanged()
            # Revision 18/06/2025 >
            return None
        v = list(v1.values())
        if len(v) > 1:
            dwi = list(v1.keys())
            buff = '{}: {}'.format(basename(dwi[0]), ' '.join([str(j) for j in v[0]]))
            for i in range(1, len(v)):
                buff += '\n{}: {}'.format(basename(dwi[i]), ' '.join([str(j) for j in v[i]]))
            self._bvecs.setToolTip(buff)
        filename = splitext(self._bvecs.getFilename())[0] + '.xbval'
        if exists(filename):
            try: v2 = loadBVal(filename, format='xml')
            except:
                messageBox(self,
                           title=self.windowTitle(),
                           text='{} format is invalid.'.format(basename(filename)))
                return None
            if list(v1.keys()) == list(v2.keys()):
                self._bvals.open(filename, signal=False)
                self._exec.setEnabled(not (self._bvals.isEmpty() and self._bvecs.isEmpty()))
                v = list(v2.values())
                if len(v) > 1:
                    dwi = list(v2.keys())
                    buff = '{}: {}'.format(basename(dwi[0]), str(v[0]))
                    for i in range(1, len(v)):
                        buff += '\n{}: {}'.format(basename(dwi[i]), str(v[i]))
                    # noinspection PyInconsistentReturns
                    self._bvals.setToolTip(buff)
                else: raise ValueError('b-vectors and b-values count <= 1.')
            else: raise ValueError('b-vectors and b-values count <= 1.')
        else: raise IOError('No such file {}'.format(filename))

    def _denoiseChanged(self):
        self._pca.setVisible(self._combo.currentText() in ('Local PCA', 'General function PCA', 'Marcenko-Pastur PCA'))
        self._nlmeans.setVisible(self._combo.currentText() == 'Non-local means')
        self._supervised.setVisible(self._combo.currentText() == 'Self-Supervised Denoising')
        tag = self._combo.currentText() != 'No' and self._combo.currentText()[0] in ('N', 'A')
        self._preproc.setParameterVisibility('NoiseEstimation', tag)
        self._preproc.setParameterVisibility('MRReconstruction', tag)
        self._preproc.setParameterVisibility('ReceiverArray', (self._noise.currentText()[0][0] == 'L' and tag))
        self._preproc.setParameterVisibility('PhaseArray', (self._noise.currentText()[0][0] == 'P' and tag))
        # < Revision 18/06/2025
        self._exec.setEnabled(False)
        if not self._bvals.isEmpty():
            if self._combo.currentIndex() > 0 or self._check.isChecked():
                self._exec.setEnabled(True)
        # Revision 18/06/2025 >
        self._center(None)

    def _reconstructionChanged(self):
        if self._rec.currentText()[0] == 'S':  # SENSE (Philips)
            self._preproc.getParameterWidget('ReceiverArray').setValue(1)
            self._preproc.getParameterWidget('PhaseArray').setValue(1)
            self._preproc.getParameterWidget('ReceiverArray').setEnabled(False)
            self._preproc.getParameterWidget('PhaseArray').setEnabled(False)
        else:
            self._preproc.getParameterWidget('ReceiverArray').setEnabled(True)
            self._preproc.getParameterWidget('PhaseArray').setEnabled(True)

    def _noiseEstimationChanged(self):
        tag = self._combo.currentText() != 'No' and self._combo.currentText()[0] in ('N', 'A')
        self._preproc.setParameterVisibility('ReceiverArray', (self._noise.currentText()[0][0] == 'L' and tag))
        self._preproc.setParameterVisibility('PhaseArray', (self._noise.currentText()[0][0] == 'P' and tag))
        self._center(None)

    # Public methods

    def execute(self):
        wait = DialogWait()
        # < Revision 17/06/2025
        # bug fix, open() to display wait dialog
        wait.open()
        # Revision 17/06/2025 >
        wait.progressVisibilityOff()
        # Load bvals
        wait.setInformationText('Load gradient B values...')
        try:
            bvals = loadBVal(self._bvals.getFilename(), format='xml')
            dwinames = list(bvals.keys())
            bvals = array(list(bvals.values()))
        except:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvals.getFilename())))
            return None
        # Load bvecs
        wait.setInformationText('Load gradient directions...')
        try:
            # < Revision 17/06/2025
            # bvecs = loadBVec(self._bvecs.getFilename(), format='xml')
            # bug fix, numpy=True to return a numpy array instead of a dict
            bvecs = loadBVec(self._bvecs.getFilename(), format='xml', numpy=True)
            # Revision 17/06/2025 >
        except:
            wait.close()
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvals.getFilename())))
            return None
        # Load dwi volumes
        vols = SisypheVolumeCollection()
        wait.setInformationText('Load diffusion weighted volumes...')
        wait.setProgressRange(0, len(dwinames) - 1)
        wait.progressVisibilityOn()
        for dwiname in dwinames:
            wait.setInformationText('Load {}...'.format(dwiname))
            wait.incCurrentProgressValue()
            vol = SisypheVolume()
            vol.load(dwiname)
            vols.append(vol)
        wait.progressTextVisibilityOff()
        # Preprocessing
        # < Revision 17/06/2025
        # bug fix, replace self._bvals by bvals and self._bvecs by bvecs
        # gtable = gradient_table(self._bvals, self._bvecs)
        gtable = gradient_table(bvals=bvals, bvecs=bvecs)
        # Revision 17/06/2025 >
        prefix = self._preproc.getParameterValue('Prefix')
        suffix = self._preproc.getParameterValue('Suffix')
        """
        brainseg    
        dict, {'algo': str = 'huang', 'size': int = 1, 'niter': int = 1}
        """
        if self._preproc.getParameterValue('Mask'):
            brainseg = dict()
            algo = self._preproc.getParameterValue('Algo')[0]
            algo = algo.lower()
            algo = algo.replace(' ', '')
            brainseg['algo'] = algo
            brainseg['size'] = self._preproc.getParameterValue('Size')
            brainseg['niter'] = self._preproc.getParameterValue('Iter')
        else: brainseg = None
        """
        gibbs       
        dict, {'neighbour': int = 3}
        """
        if self._preproc.getParameterValue('GibbsSuppression'):
            gibbs = dict()
            gibbs['neighbour'] = self._preproc.getParameterValue('GibbsNeighbour')
        else: gibbs = None
        """
        denoise     
        dict, {'algo': 'Local PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'General function PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'Marcenko-Pastur PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'Non-local means', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int, 'patchradius': int = 1, 'blockradius': int = 5}
              {'algo': 'Self-Supervised Denoising', 'radius': int = 0, 'solver': str = 'ols'}
              {'algo': 'Adaptive soft coefficient matching', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int}
        """
        denoise = dict()
        denoise['algo'] = self._preproc.getParameterValue('Denoise')[0]
        if denoise['algo'] != 'No':
            if denoise['algo'][-3:] == 'PCA':
                denoise['smooth'] = self._pca.getParameterValue('Smooth')
                denoise['PatchRadius'] = self._pca.getParameterValue('PatchRadius')
                denoise['PCAMethod'] = self._pca.getParameterValue('PCAMethod')[0]
            elif denoise['algo'] == 'Non-local means':
                denoise['noisealgo'] = self._preproc.getParameterValue('NoiseEstimation')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
                denoise['patchradius'] = self._nlmeans.getParameterValue('PatchRadius')
                denoise['blockradius'] = self._nlmeans.getParameterValue('BlockRadius')
            elif denoise['algo'] == 'Self-Supervised Denoising':
                denoise['patchradius'] = self._supervised.getParameterValue('PatchRadius')
                denoise['solver'] = self._supervised.getParameterValue('Solver')[0]
            elif denoise['algo'] == 'Adaptive soft coefficient matching':
                denoise['noisealgo'] = self._preproc.getParameterValue('NoiseEstimation')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
        else: denoise = None
        try: dwiPreprocessing(vols, prefix, suffix, gtable, brainseg, gibbs, denoise, save=True, wait=wait)
        except Exception as err:
            wait.hide()
            messageBox(self,
                       title=self.windowTitle(),
                       text='Diffusion preprocessing failed.\n'
                       '{}\n{}.'.format(type(err), str(err)))
        """
        Exit  
        """
        wait.close()
        r = messageBox(self,
                       self.windowTitle(),
                       'Would you like to do\nmore diffusion preprocessing ?',
                       icon=QMessageBox.Question,
                       buttons=QMessageBox.Yes | QMessageBox.No,
                       default=QMessageBox.No)
        if r == QMessageBox.Yes:
            self._bvals.clear()
            # noinspection PyInconsistentReturns
            self._bvecs.clear()
        else:
            # noinspection PyInconsistentReturns
            self.accept()

    def multiExecute(self):
        wait = DialogWait()
        wait.setInformationText('Diffusion preprocessing intialization...')
        wait.buttonVisibilityOn()
        wait.open()
        # Parameters
        prefix = self._preproc.getParameterValue('Prefix')
        suffix = self._preproc.getParameterValue('Suffix')
        """
        brainseg    
        dict, {'algo': str = 'huang', 'size': int = 1, 'niter': int = 1}
        """
        if self._preproc.getParameterValue('Mask'):
            brainseg = dict()
            algo = self._preproc.getParameterValue('Algo')[0]
            algo = algo.lower()
            algo = algo.replace(' ', '')
            brainseg['algo'] = algo
            brainseg['size'] = self._preproc.getParameterValue('Size')
            brainseg['niter'] = self._preproc.getParameterValue('Iter')
        else: brainseg = None
        """
        gibbs       
        dict, {'neighbour': int = 3}
        """
        if self._preproc.getParameterValue('GibbsSuppression'):
            gibbs = dict()
            gibbs['neighbour'] = self._preproc.getParameterValue('GibbsNeighbour')
        else: gibbs = None
        """
        denoise     
        dict, {'algo': 'Local PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'General function PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'Marcenko-Pastur PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
              {'algo': 'Non-local means', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int, 'patchradius': int = 1, 'blockradius': int = 5}
              {'algo': 'Self-Supervised Denoising', 'radius': int = 0, 'solver': str = 'ols'}
              {'algo': 'Adaptive soft coefficient matching', 'noisealgo': str, 'rec': str, 'ncoils': int, 'nphase': int}
        """
        denoise = dict()
        denoise['algo'] = self._preproc.getParameterValue('Denoise')[0]
        if denoise['algo'] != 'No':
            if denoise['algo'][-3:] == 'PCA':
                denoise['smooth'] = self._pca.getParameterValue('Smooth')
                denoise['PatchRadius'] = self._pca.getParameterValue('PatchRadius')
                denoise['PCAMethod'] = self._pca.getParameterValue('PCAMethod')[0]
            elif denoise['algo'] == 'Non-local means':
                denoise['noisealgo'] = self._preproc.getParameterValue('NoiseEstimation')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
                denoise['patchradius'] = self._nlmeans.getParameterValue('PatchRadius')
                denoise['blockradius'] = self._nlmeans.getParameterValue('BlockRadius')
            elif denoise['algo'] == 'Self-Supervised Denoising':
                denoise['patchradius'] = self._supervised.getParameterValue('PatchRadius')
                denoise['solver'] = self._supervised.getParameterValue('Solver')[0]
            elif denoise['algo'] == 'Adaptive soft coefficient matching':
                denoise['noisealgo'] = self._preproc.getParameterValue('NoiseEstimation')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
        else: denoise = None
        # Preprocessing loop
        r = None
        with Manager() as manager:
            mng = manager.dict()
            queue = Queue()
            process = ProcessDiffusionPreprocessing(self._bvals.getFilename(),
                                                    self._bvecs.getFilename(),
                                                    brainseg, gibbs, denoise,
                                                    prefix, suffix, mng, queue)
            try:
                process.start()
                while process.is_alive():
                    wait.messageFromDictProxyManager(mng)
                    if not queue.empty():
                        # noinspection PyUnusedLocal
                        r = queue.get()
                        if process.is_alive(): process.terminate()
                    if wait.getStopped(): process.terminate()
            except Exception as err:
                wait.hide()
                if process.is_alive(): process.terminate()
                r = 'Diffusion preprocessing error: {}\n{}.'.format(type(err), str(err))
        wait.close()
        if r is not None:
            if r == 'terminate':
                # Exit
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to do\nmore diffusion preprocessing ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._bvals.clear(signal=False)
                    self._bvecs.clear(signal=False)
                    self._exec.setEnabled(False)
                else:
                    # noinspection PyInconsistentReturns
                    self.accept()
            else:
                # Show process exception dialog
                # noinspection PyTypeChecker
                messageBox(self,
                           title=self.windowTitle(),
                           text=r)
