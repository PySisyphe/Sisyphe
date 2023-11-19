"""
    External packages/modules

        Name            Homepage link                                               Usage

        DIPY            https://www.dipy.org/                                       MR diffusion image processing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from dipy.core.gradients import gradient_table

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.processing.dipyFunctions import dwiPreprocessing
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QDialog -> DialogDiffusionPreprocessing
"""

class DialogDiffusionPreprocessing(QDialog):
    """
        DialogDiffusionPreprocessing

        Description

            GUI dialog window for diffusion-weighted images preprocessing
            (Brain extraction, Gibbs suppression, denoising).

        Inheritance

            QDialog -> DialogDiffusionPreprocessing

        Public methods

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Diffusion preprocessing')
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        # self.setMinimumSize(int(screen.width() * 0.25), int(screen.height() * 0.25))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._bvals = FileSelectionWidget()
        self._bvals.filterExtension('.xbval')
        self._bvals.setTextLabel('B values')
        self._bvals.FieldChanged.connect(self._updateBVals)
        self._bvals.FieldCleared.connect(self._bvalsCleared)

        self._bvecs = FileSelectionWidget()
        self._bvecs.filterExtension('.xbvec')
        self._bvecs.setTextLabel('Gradient directions')
        self._bvecs.FieldChanged.connect(self._updateBVecs)
        self._bvecs.FieldCleared.connect(self._bvecsCleared)

        self._preproc = FunctionSettingsWidget('DiffusionPreprocessing')
        self._preproc.settingsVisibilityOn()
        self._preproc.hideIOButtons()
        self._preproc.setSettingsButtonFunctionText()
        self._preproc.VisibilityToggled.connect(self._center)

        self._combo = self._preproc.getParameterWidget('Denoise')
        self._combo.currentIndexChanged.connect(lambda: self._denoiseChanged())

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

        self._denoiseChanged()
        self._reconstructionChanged()
        self._noiseEstimationChanged()

        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)
        self._layout.addWidget(self._preproc)
        self._layout.addWidget(self._pca)
        self._layout.addWidget(self._nlmeans)
        self._layout.addWidget(self._supervised)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exit = QPushButton('Close')
        exit.setAutoDefault(True)
        exit.setDefault(True)
        exit.setFixedWidth(100)
        self._exec = QPushButton('Execute')
        self._exec.setFixedWidth(100)
        self._exec.setToolTip('Run diffusion preprocessing.')
        self._exec.setEnabled(False)
        layout.addWidget(exit)
        layout.addWidget(self._exec)
        layout.addStretch()

        self._layout.addLayout(layout)
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        exit.clicked.connect(self.accept)
        self._exec.clicked.connect(self.execute)

    # Private methods

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
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvals.getFilename())))
            self._bvals.clear(signal=False)
            self._bvals.setToolTip('')
            self._exec.setEnabled(False)
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
                QMessageBox.warning(self,
                                    self.windowTitle(),
                                    '{} format is invalid.'.format(basename(filename)))
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
                    self._bvecs.setToolTip(buff)

    def _updateBVecs(self):
        try: v1 = loadBVec(self._bvecs.getFilename(), format='xml')
        except:
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvecs.getFilename())))
            self._bvecs.clear(signal=False)
            self._bvecs.setToolTip('')
            self._exec.setEnabled(False)
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
                QMessageBox.warning(self,
                                    self.windowTitle(),
                                    '{} format is invalid.'.format(basename(filename)))
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
                    self._bvals.setToolTip(buff)

    def _denoiseChanged(self):
        self._pca.setVisible(self._combo.currentText() in ('Local PCA', 'General function PCA', 'Marcenko-Pastur PCA'))
        self._nlmeans.setVisible(self._combo.currentText() == 'Non-local means')
        self._supervised.setVisible(self._combo.currentText() == 'Self-Supervised Denoising')
        tag = self._combo.currentText() != 'No' and self._combo.currentText()[0] in ('N', 'A')
        self._preproc.setParameterVisibility('NoiseEstimation', tag)
        self._preproc.setParameterVisibility('MRReconstruction', tag)
        self._preproc.setParameterVisibility('ReceiverArray', (self._noise.currentText()[0][0] == 'L' and tag))
        self._preproc.setParameterVisibility('PhaseArray', (self._noise.currentText()[0][0] == 'P' and tag))
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
        wait = DialogWait(parent=self)
        wait.progressVisibilityOff()
        # Load bvals
        wait.setInformationText('Load gradient B values...')
        try: bvals = loadBVal(self._bvals.getFilename(), format='xml')
        except:
            wait.close()
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvals.getFilename())))
            return None
        dwinames = list(bvals.keys())
        # Load bvecs
        wait.setInformationText('Load gradient directions...')
        try: bvecs = loadBVec(self._bvecs.getFilename(), format='xml')
        except:
            wait.close()
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvals.getFilename())))
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
        # Preprocessing
        gtable = gradient_table(self._bvals, self._bvecs)
        prefix = self._preproc.getParameterValue('Prefix')
        suffix = self._preproc.getParameterValue('Suffix')
        """
            brainseg    dict, {'algo': str = 'huang', 'size': int = 1, 'niter': int = 1}
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
            gibbs       dict, {'neighbour': int = 3}
        """
        if self._preproc.getParameterValue('GibbsSuppression'):
            gibbs = dict()
            gibbs['neighbour'] = self._preproc.getParameterValue('GibbsNeighbour')
        else: gibbs = None
        """
            denoise     dict, {'algo': 'Local PCA', 'smooth': int = 2, 'radius': int = 2, 'method': str = 'eig'}
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
                denoise['radius'] = self._pca.getParameterValue('Radius')
                denoise['method'] = self._pca.getParameterValue('PCAMethod')[0]
            elif denoise['algo'] == 'Non-local means':
                denoise['noisealgo'] = self._preproc.getParameterValue('Algo')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
                denoise['patchradius'] = self._nlmeans.getParameterValue('PatchRadius')
                denoise['blockradius'] = self._nlmeans.getParameterValue('BlockRadius')
            elif denoise['algo'] == 'Self-Supervised Denoising':
                denoise['radius'] = self._supervised.getParameterValue('PatchRadius')
                denoise['solver'] = self._supervised.getParameterValue('Solver')[0]
            elif denoise['algo'] == 'Adaptive soft coefficient matching':
                denoise['noisealgo'] = self._preproc.getParameterValue('Algo')
                denoise['rec'] = self._preproc.getParameterValue('MRReconstruction')
                denoise['ncoils'] = self._preproc.getParameterValue('ReceiverArray')
                denoise['nphase'] = self._preproc.getParameterValue('PhaseArray')
        else: denoise = None
        try: dwiPreprocessing(vols, prefix, suffix, gtable, brainseg, gibbs, denoise, save=True, wait=wait)
        except:
            QMessageBox.warning(self,
                                self.windowTitle(),
                                'Diffusion preprocessing failed.')
        self._bvals.clear()
        self._bvecs.clear()
        wait.close()

"""
    Test
"""

if __name__ == '__main__':
    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogDiffusionPreprocessing()
    main.show()
    app.exec_()
