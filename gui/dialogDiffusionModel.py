"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - scikit-image, image processing, https://scikit-image.org/
"""

from sys import platform

from os.path import exists
from os.path import basename
from os.path import splitext

from multiprocessing import Queue
from multiprocessing import Manager

from numpy import zeros
from numpy import median

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from skimage.morphology import isotropic_dilation

from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheConstants import addPrefixToFilename
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.selectFileWidgets import SynchronizedFilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.processing.capturedStdoutProcessing import ProcessDiffusionModel
from Sisyphe.gui.dialogRegistration import DialogRegistration
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDiffusionModel',
           'DialogALPS']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDiffusionModel
    - QDialog -> DialogALPS
"""

class DialogDiffusionModel(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog window for defining the diffusion model, model parameters and diffusion-derived maps to be processed.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDiffusionModel

    Last revision: 14/04/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Diffusion model')
        # noinspection PyUnresolvedReferences
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

        self._model = FunctionSettingsWidget('DiffusionModel')
        self._model.settingsVisibilityOn()
        self._model.hideIOButtons()
        self._model.setSettingsButtonFunctionText()
        self._model.VisibilityToggled.connect(self._center)
        self._combo = self._model.getParameterWidget('Model')
        self._combo.currentIndexChanged.connect(lambda: self._modelChanged())
        self._DTI = FunctionSettingsWidget('DTIModel')
        self._DKI = FunctionSettingsWidget('DKIModel')
        self._SHCSA = FunctionSettingsWidget('SHCSAModel')
        self._SHCSD = FunctionSettingsWidget('SHCSDModel')
        # < Revision 24/03/2026
        self._FWDTI = FunctionSettingsWidget('FWDTIModel')
        self._RUMBA = FunctionSettingsWidget('RUMBAModel')
        # Revision 24/03/2026 >
        # < Revision 21/06/2025
        # self._DSI = FunctionSettingsWidget('DSI Model')
        # self._DSID = FunctionSettingsWidget('DSID Model')
        self._DSI = FunctionSettingsWidget('DSIModel')
        self._DSID = FunctionSettingsWidget('DSIDModel')
        # < Revision 21/06/2025
        self._DTI.setSettingsButtonText('DTI Model')
        self._DKI.setSettingsButtonText('DKI Model')
        self._SHCSA.setSettingsButtonText('SHCSA Model')
        self._SHCSD.setSettingsButtonText('SHCSD Model')
        self._DSI.setSettingsButtonText('DSI Model')
        self._DSID.setSettingsButtonText('DSID Model')
        # < Revision 24/03/2026
        self._FWDTI.setSettingsButtonText('FW DTI Model')
        self._RUMBA.setSettingsButtonText('RUMBA Model')
        # Revision 24/03/2026 >
        self._DTI.settingsVisibilityOn()
        self._DKI.settingsVisibilityOn()
        self._SHCSA.settingsVisibilityOn()
        self._SHCSD.settingsVisibilityOn()
        self._DSI.settingsVisibilityOn()
        self._DSID.settingsVisibilityOn()
        # < Revision 24/03/2026
        self._FWDTI.settingsVisibilityOn()
        self._RUMBA.settingsVisibilityOn()
        # Revision 24/03/2026 >
        self._DTI.hideIOButtons()
        self._DKI.hideIOButtons()
        self._SHCSA.hideIOButtons()
        self._SHCSD.hideIOButtons()
        self._DSI.hideIOButtons()
        self._DSID.hideIOButtons()
        # < Revision 24/03/2026
        self._FWDTI.hideIOButtons()
        self._RUMBA.hideIOButtons()
        # Revision 24/03/2026 >
        self._modelChanged()
        self._DTI.VisibilityToggled.connect(self._center)
        self._DKI.VisibilityToggled.connect(self._center)
        self._SHCSA.VisibilityToggled.connect(self._center)
        self._SHCSD.VisibilityToggled.connect(self._center)
        self._DSI.VisibilityToggled.connect(self._center)
        self._DSID.VisibilityToggled.connect(self._center)
        # < Revision 24/03/2026
        self._FWDTI.VisibilityToggled.connect(self._center)
        self._RUMBA.VisibilityToggled.connect(self._center)
        # Revision 24/03/2026 >

        # < Revision 24/03/2026
        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)
        self._layout.addWidget(self._model)
        self._layout.addWidget(self._DTI)
        self._layout.addWidget(self._FWDTI)
        self._layout.addWidget(self._DKI)
        self._layout.addWidget(self._RUMBA)
        self._layout.addWidget(self._SHCSA)
        self._layout.addWidget(self._SHCSD)
        # Revision 24/03/2026 >

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._save = QPushButton('Execute')
        self._save.setFixedWidth(100)
        self._save.setToolTip('Diffusion model processing')
        self._save.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._save)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # < Revision 11/07/2025
        # noinspection PyUnresolvedReferences
        # self._save.clicked.connect(self.save)
        self._save.clicked.connect(self.multiExecute)
        # Revision 11/07/2025 >

        # < Revision 17/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._bvals.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 17/06/2025 >
        self.setModal(True)

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _bvalsCleared(self):
        self._save.setEnabled(False)
        self._bvals.setToolTip('')

    def _bvecsCleared(self):
        self._save.setEnabled(False)
        self._bvecs.setToolTip('')

    def _updateBVals(self):
        try: v1 = loadBVal(self._bvals.getFilename(), format='xml')
        except:
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvals.getFilename())))
            self._bvals.clear(signal=False)
            self._bvals.setToolTip('')
            self._save.setEnabled(False)
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
                self._save.setEnabled(not (self._bvals.isEmpty() and self._bvecs.isEmpty()))
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
        else: raise IOError('No such file {}.'.format(filename))

    def _updateBVecs(self):
        try: v1 = loadBVec(self._bvecs.getFilename(), format='xml')
        except:
            messageBox(self,
                       title=self.windowTitle(),
                       text='{} format is invalid.'.format(basename(self._bvecs.getFilename())))
            self._bvecs.clear(signal=False)
            self._bvecs.setToolTip('')
            self._save.setEnabled(False)
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
                self._save.setEnabled(not (self._bvals.isEmpty() and self._bvecs.isEmpty()))
                v = list(v2.values())
                if len(v) > 1:
                    dwi = list(v2.keys())
                    buff = '{}: {}'.format(basename(dwi[0]), str(v[0]))
                    for i in range(1, len(v)):
                        buff += '\n{}: {}'.format(basename(dwi[i]), str(v[i]))
                    # noinspection PyInconsistentReturns
                    self._bvals.setToolTip(buff)
                else: raise ValueError('b-vectors and b-values count <= 1.')
            else: raise ValueError('b-vectors and b-values mismatch.')
        else: raise IOError('No such file {}.'.format(filename))

    def _modelChanged(self):
        self._DTI.setVisible(self._combo.currentText() == 'DTI')
        self._DKI.setVisible(self._combo.currentText() == 'DKI')
        self._SHCSA.setVisible(self._combo.currentText() == 'SHCSA')
        self._SHCSD.setVisible(self._combo.currentText() == 'SHCSD')
        # < Revision 24/03/2026
        self._FWDTI.setVisible(self._combo.currentText() == 'FWDTI')
        self._RUMBA.setVisible(self._combo.currentText() == 'RUMBA')
        # Revision 24/03/2026 >
        self._center(None)

    # Public method

    def multiExecute(self):
        wait = DialogWait()
        wait.setInformationText('Diffusion model intialization...')
        wait.buttonVisibilityOn()
        wait.open()
        # Parameters
        order = None
        method = None
        maps = dict()
        if self._combo.currentText() == 'DTI':
            method = self._DTI.getParameterValue('Method')[0]
            maps['fa'] = self._DTI.getParameterValue('FA')
            maps['ga'] = self._DTI.getParameterValue('GA')
            maps['md'] = self._DTI.getParameterValue('MD')
            maps['tr'] = self._DTI.getParameterValue('Trace')
            maps['ad'] = self._DTI.getParameterValue('AD')
            maps['rd'] = self._DTI.getParameterValue('RD')
            # < Revision 23/03/2026
            maps['li'] = self._DTI.getParameterValue('Linearity')
            maps['pl'] = self._DTI.getParameterValue('Planarity')
            maps['sp'] = self._DTI.getParameterValue('Sphericity')
            maps['ts'] = self._DTI.getParameterValue('Tensor')
            maps['ts2'] = self._DTI.getParameterValue('Tensor2')
            maps['mj'] = self._DTI.getParameterValue('Major')
            maps['evl'] = self._DTI.getParameterValue('Eval')
            maps['evc'] = self._DTI.getParameterValue('Evec')
            # Revision 23/03/2026 >
        # < Revision 23/03/2026
        elif self._combo.currentText() == 'FWDTI':
            method = self._FWDTI.getParameterValue('Method')[0]
            maps['fa'] = self._FWDTI.getParameterValue('FA')
            maps['ga'] = self._FWDTI.getParameterValue('GA')
            maps['md'] = self._FWDTI.getParameterValue('MD')
            maps['tr'] = self._FWDTI.getParameterValue('Trace')
            maps['ad'] = self._FWDTI.getParameterValue('AD')
            maps['rd'] = self._FWDTI.getParameterValue('RD')
            maps['li'] = self._FWDTI.getParameterValue('Linearity')
            maps['pl'] = self._FWDTI.getParameterValue('Planarity')
            maps['sp'] = self._FWDTI.getParameterValue('Sphericity')
            maps['fw'] = self._FWDTI.getParameterValue('FW')
        # Revision 23/03/2026 >
        elif self._combo.currentText() == 'DKI':
            method = self._DKI.getParameterValue('Method')[0]
            maps['fa'] = self._DKI.getParameterValue('FA')
            maps['ga'] = self._DKI.getParameterValue('GA')
            maps['md'] = self._DKI.getParameterValue('MD')
            maps['tr'] = self._DKI.getParameterValue('Trace')
            maps['ad'] = self._DKI.getParameterValue('AD')
            maps['rd'] = self._DKI.getParameterValue('RD')
            # < Revision 23/03/2026
            maps['li'] = self._DTI.getParameterValue('Linearity')
            maps['pl'] = self._DTI.getParameterValue('Planarity')
            maps['sp'] = self._DTI.getParameterValue('Sphericity')
            # Revision 23/03/2026 >
        # < Revision 23/03/2026
        elif self._combo.currentText() == 'RUMBA':
            method = self._RUMBA.getParameterValue('Method')[0]
            maps['fcsf'] = self._RUMBA.getParameterValue('FCSF')
            maps['fgm'] = self._RUMBA.getParameterValue('FGM')
            maps['fwm'] = self._RUMBA.getParameterValue('FWM')
            maps['fiso'] = self._RUMBA.getParameterValue('FISO')
        # Revision 23/03/2026 >
        elif self._combo.currentText() == 'SHCSA':
            order = self._SHCSA.getParameterValue('Order')
            maps['gfa'] = self._SHCSA.getParameterValue('GFA')
        elif self._combo.currentText() == 'SHCSD':
            order = self._SHCSD.getParameterValue('Order')
            maps['gfa'] = self._SHCSD.getParameterValue('GFA')
        elif self._combo.currentText() == 'DSI':
            maps['gfa'] = self._DSI.getParameterValue('GFA')
        elif self._combo.currentText() == 'DSID':
            maps['gfa'] = self._DSID.getParameterValue('GFA')
        corr = self._model.getParameterValue('Orientation')
        algo = self._model.getParameterValue('Algo')[0]
        niter = self._model.getParameterValue('Iter')
        size = self._model.getParameterValue('Size')
        if corr is None: corr = False
        # Preprocessing loop
        r = None
        with Manager() as manager:
            mng = manager.dict()
            queue = Queue()
            try:
                process = ProcessDiffusionModel(self._bvals.getFilename(),
                                                self._bvecs.getFilename(),
                                                self._combo.currentText(),
                                                method, order, maps, corr, algo, niter, size,True, mng, queue)
                process.start()
                while process.is_alive():
                    # noinspection PyTypeChecker
                    wait.messageFromDictProxyManager(mng)
                    if not queue.empty():
                        # noinspection PyUnusedLocal
                        r = queue.get()
                        if process.is_alive(): process.terminate()
                    if wait.getStopped(): process.terminate()
            except Exception as err:
                wait.hide()
                if process.is_alive(): process.terminate()
                r = 'Diffusion model error: {}\n{}.'.format(type(err), str(err))
        wait.close()
        if r is not None:
            if r == 'terminate':
                # Exit
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to estimate\nmore diffusion model ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._bvals.clear(signal=False)
                    self._bvecs.clear(signal=False)
                    self._save.setEnabled(False)
                else:
                    # noinspection PyInconsistentReturns
                    self.accept()
            else:
                # Show process exception dialog
                # noinspection PyTypeChecker
                messageBox(self,
                           title=self.windowTitle(),
                           text=r)

    def showEvent(self, a0):
        super().showEvent(a0)
        self.move(self.screen().availableGeometry().center() - self.rect().center())


class DialogALPS(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog window for diffusion tensor image analysis along the perivascular space (DTI‑ALPS).

    ALPS-index express the influence of the water diffusion along the perivascular space which will reflect activity of
    the glymphatic system in the individual cases. When the ratio is close to 1, it means that the influence of the
    water diffusion along the perivascular space is minimal (i.e. impaired glymphatic system), and a larger ratio will
    represent larger water diffusivity along the perivascular space.

    Reference:
    Evaluation of glymphatic system activity with the diffusion MR technique: diffusion tensor image analysis along the
    perivascular space (DTI-ALPS) in Alzheimer's disease cases. T. Taoka, Y. Masutani, H. Kawai, T. Nakane, K. Matsuoka,
    F. Yasuno, T. Kishimoto, S. Naganawa. Jpn J Radiol 2017 Apr;35(4):172-178.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogALPS

    Creation: 13/04/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Diffusion analysis along perivascular space')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._files.filterMultiComponent()
        self._files.filterSameSequence('TENSOR')
        self._files.setTextLabel('Multicomponent tensor volume(s)')
        self._files.FieldChanged.connect(self._updateFiles)
        self._files.FieldCleared.connect(self._updateFiles)

        self._template = SynchronizedFilesSelectionWidget(single=('Multicomponent tensor volume reference',
                                                                  'Label volume of reference proj./assoc. areas'),
                                                          multiple=None,
                                                          parent=self)
        self._template.setSisypheVolumeFilters({'single': [True, True]})
        flt = {'single': [SisypheAcquisition.getOTModalityTag(),
                          SisypheAcquisition.getLBModalityTag()]}
        self._template.setModalityFilters(flt)
        flt = {'single': ['TENSOR',
                          SisypheAcquisition.LABELS]}
        self._template.setSequenceFilters(flt)
        self._tensor = self._template.getSelectionWidget('Multicomponent tensor volume reference')
        self._tensor.filterMultiComponent()
        self._tensor.FieldChanged.connect(self._updateFiles)
        self._tensor.FieldCleared.connect(self._updateFiles)
        self._lbl = self._template.getSelectionWidget('Label volume of reference proj./assoc. areas')
        self._lbl.FieldChanged.connect(self._updateFiles)
        self._lbl.FieldCleared.connect(self._updateFiles)
        self._tensor.alignLabels(self._lbl)

        self._settings = FunctionSettingsWidget('DiffusionALPS')
        self._settings.setSettingsButtonText('Diffusion ALPS')
        self._settings.setParameterVisibility('RefTensor', False)
        self._settings.setParameterVisibility('RefLabels', False)
        self._settings.settingsVisibilityOn()

        self._layout.addWidget(self._files)
        self._layout.addWidget(self._template)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._exec = QPushButton('Execute')
        self._exec.setFixedWidth(100)
        self._exec.setToolTip('DTI-ALPS index processing')
        self._exec.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._exec)
        layout.addStretch()

        self._layout.addLayout(layout)

        reftensor = self._settings.getParameterValue('RefTensor')
        if exists(reftensor): self._tensor.open(reftensor)
        reflabels = self._settings.getParameterValue('RefLabels')
        if exists(reflabels): self._lbl.open(reflabels)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # < Revision 11/07/2025
        # noinspection PyUnresolvedReferences
        # self._save.clicked.connect(self.save)
        self._exec.clicked.connect(self.execute)
        # Revision 11/07/2025 >

        # < Revision 17/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._files.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 17/06/2025 >
        self.setModal(True)

    # Private methods

    def _updateFiles(self):
        v = self._files.filenamesCount() > 0 and not self._tensor.isEmpty() and not self._lbl.isEmpty()
        self._exec.setEnabled(v)
        # if not self._tensor.isEmpty():
        #     self._settings.setParameterValue('RefTensor', self._tensor.getFilename())
        # if not self._lbl.isEmpty():
        #     self._settings.setParameterValue('RefLabels', self._lbl.getFilename())

    # Public method

    def getFileSelectionWidget(self):
        return [self._files,
                self._tensor,
                self._lbl]

    def execute(self):
        n = self._files.filenamesCount() > 0
        if n > 0:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Open reference tensor {}...'.format(basename(self._tensor.getFilename())))
            v = SisypheVolume()
            v.load(self._tensor.getFilename())
            template = v.copyComponent(8)  # ZZ
            template.setFilename(v.getFilename())
            template.setFilenameSuffix('ZZ', sep=' ')
            template.copyAttributesFrom(v, display=False)
            template.acquisition.setSequence('TENSOR ZZ')
            if not exists(template.getFilename()): template.save()
            wait.setInformationText('Open reference area labels {}...'.format(basename(self._lbl.getFilename())))
            areas = SisypheVolume()
            areas.load(self._lbl.getFilename())
            # Area dilatation
            radius = self._settings.getParameterValue('Dilatation')
            if radius > 0:
                lbls = zeros(shape=areas.getNumpy().shape, dtype='uint8')
                for i in range(1, 5):
                    buff = areas.getNumpy() == i
                    buff = isotropic_dilation(buff, radius)
                    buff = (buff * i).astype('uint8')
                    lbls += buff
                dareas = SisypheVolume()
                dareas.copyFromNumpyArray(lbls,
                                          spacing=areas.getSpacing(),
                                          origin=areas.getOrigin(),
                                          direction=areas.getDirections())
                dareas.copyAttributesFrom(areas)
                dareas.setFilename(areas.getFilename())
            else: dareas = areas
            lbls = dareas.getNumpy()
            dareas.setFilenamePrefix('ALPS')
            results = dict()
            hdr = ['filenames',
                   'ALPS-Mean\nLeft',
                   'ALPS-Mean\nRight',
                   'ALPS-Median\nLeft',
                   'ALPS-Median\nRight',
                   'ALPS-Max\nLeft',
                   'ALPS-Max\nRight']
            for h in hdr: results[h] = list()
            filenames = [v.getFilename()] + self._files.getFilenames()
            wait.setProgressRange(0, n + 1)
            wait.setCurrentProgressValue(0)
            wait.progressVisibilityOn()
            for i, filename in enumerate(filenames):
                self._files.setSelectionTo(i)
                wait.incCurrentProgressValue()
                if exists(filename):
                    if i == 0: results['filenames'].append('Reference')
                    else: results['filenames'].append(basename(filename))
                    v = SisypheVolume()
                    v.load(filename)
                    vxx = v.copyComponent(0)
                    vxx.setFilename(v.getFilename())
                    vxx.setFilenameSuffix('XX', sep=' ')
                    vxx.copyAttributesFrom(v, display=False)
                    vxx.acquisition.setSequence('TENSOR XX')
                    if i > 0 and not exists(vxx.getFilename()): vxx.save()
                    vyy = v.copyComponent(4)
                    vyy.setFilename(v.getFilename())
                    vyy.setFilenameSuffix('YY', sep=' ')
                    vyy.copyAttributesFrom(v, display=False)
                    vyy.acquisition.setSequence('TENSOR YY')
                    if i > 0 and not exists(vyy.getFilename()): vyy.save()
                    vzz = v.copyComponent(8)
                    vzz.setFilename(v.getFilename())
                    vzz.setFilenameSuffix('ZZ', sep=' ')
                    vzz.copyAttributesFrom(v, display=False)
                    vzz.acquisition.setSequence('TENSOR ZZ')
                    if i > 0 and not exists(vzz.getFilename()): vzz.save()
                    if i > 0:
                        """
                        Registration to reference
                        """
                        fxx = addPrefixToFilename(vxx.getFilename(), 'ALPS')
                        fyy = addPrefixToFilename(vyy.getFilename(), 'ALPS')
                        fzz = addPrefixToFilename(vzz.getFilename(), 'ALPS')
                        if not exists(fxx) or not exists(fyy) or not exists(fzz):
                            wait.hide()
                            dialog = DialogRegistration(transform='Transform')
                            dialog.setFixed(template)
                            dialog.setMoving(vzz)
                            dialog.setFilesToApply([vxx.getFilename(), vyy.getFilename()])
                            params = dialog.getParametersDict()
                            params['registration']['CheckRegistration'] = False
                            params['registration']['Transform'] = self._settings.getParameterValue('Transform')[0]
                            params['resample']['Prefix'] = 'ALPS'
                            dialog.setParametersFromDict(params)
                            dialog.getMovingSelectionWidget().setEnabled(False)
                            dialog.getFixedSelectionWidget().setEnabled(False)
                            dialog.execute()
                            wait.show()
                        wait.setInformationText('Open tensor {}...'.format(basename(filename)))
                        vxx.load(fxx)
                        vyy.load(fyy)
                        vzz.load(fzz)
                        dareas.setDirname(v.getDirname())
                        dareas.save()
                    """
                    ALPS index processing
                    ALPS-index = mean(Dxx(PArea), Dxx(AArea)) / mean(Dyy(PArea), Dzz(AArea))
                    PArea: projection area
                    AArea: association area
                    Dxx: Tensor XX
                    Dyy: Tensor YY
                    Dzz: Tensor ZZ
                    
                    label 1: Left Association Area
	                label 2: Right Association Area
	                label 3: Left Projection Area
	                label 4: Right Projection Area
                    """
                    wait.setInformationText('{} DTI-ALPS processing...'.format(basename(filename)))
                    xx = vxx.getNumpy()
                    yy = vyy.getNumpy()
                    zz = vzz.getNumpy()
                    xxa = xx[lbls == 1]
                    xxp = xx[lbls == 3]
                    yyp = yy[lbls == 3]
                    zza = zz[lbls == 1]
                    results['ALPS-Mean\nLeft'].append(((xxp.mean() + xxa.mean()) / 2) / ((yyp.mean() + zza.mean()) / 2))
                    results['ALPS-Median\nLeft'].append(((median(xxp) + median(xxa)) / 2) / ((median(yyp) + median(zza)) / 2))
                    results['ALPS-Max\nLeft'].append(((xxp.max() + xxa.max()) / 2) / ((yyp.max() + zza.max()) / 2))
                    xxa = xx[lbls == 2]
                    xxp = xx[lbls == 4]
                    yyp = yy[lbls == 4]
                    zza = zz[lbls == 2]
                    results['ALPS-Mean\nRight'].append(((xxp.mean() + xxa.mean()) / 2) / ((yyp.mean() + zza.mean()) / 2))
                    results['ALPS-Median\nRight'].append(((median(xxp) + median(xxa)) / 2) / ((median(yyp) + median(zza)) / 2))
                    results['ALPS-Max\nRight'].append(((xxp.max() + xxa.max()) / 2) / ((yyp.max() + zza.max()) / 2))
            wait.close()
            if len(results) > 0:
                dialog = DialogGenericResults()
                if platform == 'win32':
                    import pywinstyles
                    cl = self._files.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.newTab('Diffusion ALPS Index', capture=False, clipbrd=False, scrshot=False, dataset=True)
                dialog.setTreeWidgetDict(0, results, d=2)
                screen = QApplication.primaryScreen().geometry()
                dialog.setMinimumWidth(int(screen.width() * 0.40))
                dialog.exec()
            """
            Exit
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to process\nadditional DTI-ALPS ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._files.clearAll()
            else: self.accept()
