"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import exists
from os.path import splitext
from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheTracts import SisypheDiffusionModel
from Sisyphe.core.sisypheTracts import SisypheTracking
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDiffusionTracking']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDiffusionTracking
"""


class DialogDiffusionTracking(QDialog):
    """
    DialogDiffusionTracking

    Description
    ~~~~~~~~~~~

    GUI dialog window for fiber tracking processing.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDiffusionTracking
    """

    # Special method

    def __init__(self, parent=None):

        super().__init__(parent)
        self._ID = None

        # Init window

        self.setWindowTitle('Diffusion tracking')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._model = FileSelectionWidget()
        self._model.filterExtension(SisypheDiffusionModel.getFileExt())
        self._model.setTextLabel('Diffusion model')
        self._model.FieldChanged.connect(self._modelChanged)

        self._track = FunctionSettingsWidget('Tracking')
        self._track.settingsVisibilityOn()
        self._track.hideIOButtons()
        self._track.setSettingsButtonFunctionText()
        self._track.VisibilityToggled.connect(self._center)
        self._combo1 = self._track.getParameterWidget('TrackingAlgorithm')
        self._combo2 = self._track.getParameterWidget('SeedMethod')
        self._combo3 = self._track.getParameterWidget('StoppingCriterion')
        self._combo4 = self._track.getParameterWidget('DeterministicAlgorithm')
        self._combo1.currentIndexChanged.connect(lambda: self._algoChanged())
        self._combo2.currentIndexChanged.connect(lambda: self._seedChanged())
        self._combo3.currentIndexChanged.connect(lambda: self._stoppingChanged())
        self._combo4.currentIndexChanged.connect(lambda: self._deterministicChanged())

        self._layout.addWidget(self._model)
        self._layout.addWidget(self._track)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Fiber tracking processing')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)
        self._model.FieldChanged.connect(self._validate)
        self._track.getParameterWidget('SeedROI').FieldChanged.connect(self._validate)
        self._track.getParameterWidget('StoppingROI').FieldChanged.connect(self._validate)
        self._track.getParameterWidget('StoppingGM').FieldChanged.connect(self._validate)
        self._track.getParameterWidget('StoppingWM').FieldChanged.connect(self._validate)
        self._track.getParameterWidget('StoppingCSF').FieldChanged.connect(self._validate)

        self.show()

        self._algoChanged()
        self._seedChanged()
        self._stoppingChanged()

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self._track.adjustSize()
        QApplication.processEvents()
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _modelChanged(self):
        if self._model.isEmpty(): self._model.setToolTip('')
        else:
            filename = self._model.getFilename()
            if exists(filename):
                m = SisypheDiffusionModel.openModel(filename, False,False)
                self._model.setToolTip(str(m)[:-1])
            else: self._model.clear(False)

    def _algoChanged(self):
        v = self._combo1.currentText() == 'Deterministic'
        self._track.setParameterVisibility('DeterministicAlgorithm', v)
        if v: self._deterministicChanged()
        v = self._combo1.currentText() == 'Probabilistic'
        self._track.setParameterVisibility('ProbabilisticAlgorithm', v)
        self._track.setParameterVisibility('RelativePeakThreshold', False)
        self._track.setParameterVisibility('MinSeparationAngle', False)
        self._track.setParameterVisibility('NPeaks', False)
        self._center(None)

    def _seedChanged(self):
        self._track.setParameterVisibility('SeedFAThreshold', self._combo2.currentText() == 'FA/GFA')
        self._track.setParameterVisibility('SeedROI', self._combo2.currentText() == 'ROI')
        self._center(None)
        self._validate()

    def _stoppingChanged(self):
        self._track.setParameterVisibility('StoppingFAThreshold', self._combo3.currentText() == 'FA/GFA')
        self._track.setParameterVisibility('StoppingROI', self._combo3.currentText() == 'ROI')
        v = self._combo3.currentText() == 'MAPS'
        self._track.setParameterVisibility('StoppingGM', v)
        self._track.setParameterVisibility('StoppingWM', v)
        self._track.setParameterVisibility('StoppingCSF', v)
        self._center(None)
        self._validate()

    def _deterministicChanged(self):
        if self._combo4.currentText() == 'Euler EuDX':
            self._track.setParameterVisibility('RelativePeakThreshold', True)
            self._track.setParameterVisibility('MinSeparationAngle', True)
            self._track.setParameterVisibility('NPeaks', True)
        else:
            self._track.setParameterVisibility('RelativePeakThreshold', False)
            self._track.setParameterVisibility('MinSeparationAngle', False)
            self._track.setParameterVisibility('NPeaks', False)
        self._center(None)

    def _validate(self):
        v = True
        v &= not self._model.isEmpty()
        if self._combo2.currentText() == 'ROI':
            v &= not self._track.getParameterWidget('SeedROI').isEmpty()
        if self._combo3.currentText() == 'ROI':
            v &= not self._track.getParameterWidget('StoppingROI').isEmpty()
        elif self._combo3.currentText() == 'GM/WM/CSF':
            v &= not self._track.getParameterWidget('StoppingGM').isEmpty()
            v &= not self._track.getParameterWidget('StoppingWM').isEmpty()
            v &= not self._track.getParameterWidget('StoppingCSF').isEmpty()
        self._process.setEnabled(v)

    def _clear(self):
        self._model.clear()
        self._track.getParameterWidget('SeedROI').clear()
        self._track.getParameterWidget('StoppingROI').clear()
        self._track.getParameterWidget('StoppingGM').clear()
        self._track.getParameterWidget('StoppingWM').clear()
        self._track.getParameterWidget('StoppingCSF').clear()
        self._process.setEnabled(False)

    # Public method

    def execute(self):
        if not self._model.isEmpty() and exists(self._model.getFilename()):
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Open model...')
            wait.progressVisibilityOff()
            model = SisypheDiffusionModel.openModel(self._model.getFilename(), True, wait)
            track = SisypheTracking(model)
            track.setBundleName(self._track.getParameterValue('BundleName'))
            track.setSeedCountPerVoxel(self._track.getParameterValue('SeedCount'))
            track.setStepSize(self._track.getParameterValue('StepSize'))
            track.setNumberOfPeaks(self._track.getParameterValue('NPeaks'))
            track.setRelativeThresholdOfPeaks(self._track.getParameterValue('RelativePeakThreshold'))
            track.setMinSeparationAngleOfPeaks(self._track.getParameterValue('MinSeparationAngle'))
            track.setMinLength(self._track.getParameterValue('MinimalLength'))
            # Algorithm
            if self._combo1.currentText() == 'Deterministic':
                ch = self._track.getParameterWidget('DeterministicAlgorithm').currentText()
                if ch == 'Euler EuDX':
                    track.setTrackingAlgorithmToDeterministicEulerIntegration()
                elif ch == 'Fiber orientation distribution':
                    track.setTrackingAlgorithmToDeterministicFiberOrientationDistribution()
                elif ch == 'Parallel transport':
                    track.setTrackingAlgorithmToDeterministicParallelTransport()
                elif ch == 'Closest peak direction':
                    track.setTrackingAlgorithmToDeterministicClosestPeakDirection()
                else: raise ValueError('Invalid deterministic tracking algorithm {}.'.format(ch))
            else:
                ch = self._track.getParameterWidget('ProbabilisticAlgorithm').currentText()
                if ch == 'Bootstrap direction':
                    track.setTrackingAlgorithmToProbabilisticBootstrapDirection()
                elif ch == 'Fiber orientation distribution':
                    track.setTrackingAlgorithmToProbabilisticFiberOrientationDistribution()
                else: raise ValueError('Invalid probabilistic tracking algorithm {}.'.format(ch))
            # Seed
            if self._combo2.currentText() == 'FA/GFA':
                v = self._track.getParameterValue('SeedFAThreshold')
                if v is None: v = 0.2
                track.setSeedsFromFAThreshold(v)
                track.setBundleName('tractogram')
            elif self._combo2.currentText() == 'ROI':
                filenames = self._track.getParameterWidget('SeedROI').getFilenames()
                for f in filenames:
                    if not exists(f):
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('SeedROI').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='No such file {}.'.format(basename(f)))
                        return
                rois = SisypheROICollection()
                wait.setInformationText('Load seed ROI(s)...')
                rois.load(filenames)
                if rois[0].hasSameSize(model.getDWI().shape[:3]):
                    track.setSeedsFromRoi(rois.union())
                else:
                    wait.close()
                    self._process.setEnabled(False)
                    self._track.getParameterWidget('SeedROI').clear()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Invalid ROI size {}.'.format(rois[0].getSize()))
                    return
            # Stopping criterion
            if self._combo3.currentText() == 'FA/GFA':
                v = self._track.getParameterValue('StoppingFAThreshold')
                if v is None: v = 0.1
                track.setStoppingCriterionToFAThreshold(v)
            elif self._combo3.currentText() == 'ROI':
                filename = self._track.getParameterWidget('StoppingROI').getFilename()
                if exists(filename):
                    roi = SisypheROI()
                    wait.setInformationText('Load stopping ROI...')
                    roi.load(filename)
                    if roi.hasSameSize(model.getDWI().shape[:3]):
                        track.setStoppingCriterionToROI(roi)
                    else:
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingROI').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Invalid ROI size {}.'.format(roi.getSize()))
                        return
                else:
                    wait.close()
                    self._process.setEnabled(False)
                    self._track.getParameterWidget('StoppingROI').clear()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='No such file {}.'.format(basename(filename)))
                    return
                track.setStoppingCriterionToROI(roi)
            elif self._combo3.currentText() == 'GM/WM/CSF':
                # Gray matter
                filename = self._track.getParameterWidget('StoppingGM').getFilename()
                if exists(filename):
                    gm = SisypheVolume()
                    wait.setInformationText('Load Gray matter map...')
                    gm.load(filename)
                    if not gm.acquisition.isGreyMatterMap():
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingGM').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} sequence is not gray matter map.'.format(basename(filename)))
                        return
                    if not gm.hasSameSize(model.getDWI().shape[:3]):
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingGM').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Invalid gray matter size.')
                        return
                else:
                    wait.close()
                    self._process.setEnabled(False)
                    self._track.getParameterWidget('StoppingGM').clear()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='No such file {}.'.format(basename(filename)))
                    return
                # White matter
                filename = self._track.getParameterWidget('StoppingWM').getFilename()
                if exists(filename):
                    wm = SisypheVolume()
                    wait.setInformationText('Load white matter map...')
                    wm.load(filename)
                    if not wm.acquisition.isWhiteMatterMap():
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingWM').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} sequence is not white matter map.'.format(basename(filename)))
                        return
                    if not wm.hasSameSize(model.getDWI().shape[:3]):
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingWM').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Invalid white matter size.')
                        return
                else:
                    wait.close()
                    self._process.setEnabled(False)
                    self._track.getParameterWidget('StoppingWM').clear()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='No such file {}.'.format(basename(filename)))
                    return
                # Cerebro-spinal fluid
                filename = self._track.getParameterWidget('StoppingCSF').getFilename()
                if exists(filename):
                    csf = SisypheVolume()
                    wait.setInformationText('Load cerebro-spinal fluid map...')
                    csf.load(filename)
                    if not csf.acquisition.isCerebroSpinalFluidMap():
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingCSF').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} sequence is not cerebro-spinal fluid map.'.format(basename(filename)))
                        return
                    if not wm.hasSameSize(model.getDWI().shape[:3]):
                        wait.close()
                        self._process.setEnabled(False)
                        self._track.getParameterWidget('StoppingCSF').clear()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Invalid cerebro-spinal fluid size.')
                        return
                else:
                    wait.close()
                    self._process.setEnabled(False)
                    self._track.getParameterWidget('StoppingCSF').clear()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='No such file {}.'.format(basename(filename)))
                    return
                track.setStoppingCriterionToMaps(gm, wm, csf)
            # Tracking
            wait.setInformationText('Compute tracking...')
            try: sl = track.computeTracking(wait)
            except Exception as err:
                wait.close()
                messageBox(self, self.windowTitle(), '{}'.format(err))
                return
            # Save streamlines
            filename = splitext(self._model.getFilename())[0] + '_' + track.getBundleName() + SisypheStreamlines.getFileExt()
            wait.setInformationText('save {} streamlines...'.format(track.getBundleName()))
            sl.save(bundle='all', filename=filename)
            wait.close()
            if sl.getName() == 'tractogram':
                messageBox(self,
                           self.windowTitle(),
                           'Tractogram of {} streamlines.'.format(sl.count()),
                           icon=QMessageBox.Information)
            else:
                messageBox(self,
                           self.windowTitle(),
                           '{} tractogram of {} streamlines.'.format(sl.getName(), sl.count()),
                           icon=QMessageBox.Information)
            self._clear()
