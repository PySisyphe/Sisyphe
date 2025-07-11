"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import exists
from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext

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

from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheTracts import SisypheDTIModel
from Sisyphe.core.sisypheTracts import SisypheDKIModel
from Sisyphe.core.sisypheTracts import SisypheSHCSAModel
from Sisyphe.core.sisypheTracts import SisypheSHCSDModel
from Sisyphe.core.sisypheTracts import SisypheDSIModel
from Sisyphe.core.sisypheTracts import SisypheDSIDModel
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.processing.capturedStdoutProcessing import ProcessDiffusionModel
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogDiffusionModel']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDiffusionModel
"""

class DialogDiffusionModel(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI dialog window for defining the diffusion model, model parameters and diffusion-derived maps to be processed.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDiffusionModel

    Last revision: 11/07/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Diffusion model')
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
        self._DTI.settingsVisibilityOn()
        self._DKI.settingsVisibilityOn()
        self._SHCSA.settingsVisibilityOn()
        self._SHCSD.settingsVisibilityOn()
        self._DSI.settingsVisibilityOn()
        self._DSID.settingsVisibilityOn()
        self._DTI.hideIOButtons()
        self._DKI.hideIOButtons()
        self._SHCSA.hideIOButtons()
        self._SHCSD.hideIOButtons()
        self._DSI.hideIOButtons()
        self._DSID.hideIOButtons()
        self._modelChanged()
        self._DTI.VisibilityToggled.connect(self._center)
        self._DKI.VisibilityToggled.connect(self._center)
        self._SHCSA.VisibilityToggled.connect(self._center)
        self._SHCSD.VisibilityToggled.connect(self._center)
        self._DSI.VisibilityToggled.connect(self._center)
        self._DSID.VisibilityToggled.connect(self._center)

        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)
        self._layout.addWidget(self._model)
        self._layout.addWidget(self._DTI)
        self._layout.addWidget(self._DKI)
        self._layout.addWidget(self._SHCSA)
        self._layout.addWidget(self._SHCSD)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
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
        self._center(None)

    # Public method

    def save(self):
        if not (self._bvals.isEmpty() or self._bvecs.isEmpty()):
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Model definition...')
            wait.progressVisibilityOff()
            filename = splitext(self._bvals.getFilename())[0] + SisypheDTIModel.getFileExt()
            fa = ga = gfa = md = tr = ad = rd = False
            if self._combo.currentText() == 'DTI':
                wait.setInformationText('DTI Model definition...')
                model = SisypheDTIModel()
                method = self._DTI.getParameterValue('Method')[0]
                model.setFitAlgorithm(method)
                fa = self._DTI.getParameterValue('FA')
                ga = self._DTI.getParameterValue('GA')
                md = self._DTI.getParameterValue('MD')
                tr = self._DTI.getParameterValue('Trace')
                ad = self._DTI.getParameterValue('AD')
                rd = self._DTI.getParameterValue('RD')
                tag = fa or ga or md or tr or ad or rd
                ndmin = 6
            elif self._combo.currentText() == 'DKI':
                wait.setInformationText('DKI Model definition...')
                model = SisypheDKIModel()
                method = self._DKI.getParameterValue('Method')[0]
                model.setFitAlgorithm(method)
                fa = self._DKI.getParameterValue('FA')
                ga = self._DKI.getParameterValue('GA')
                md = self._DKI.getParameterValue('MD')
                tr = self._DKI.getParameterValue('Trace')
                ad = self._DKI.getParameterValue('AD')
                rd = self._DKI.getParameterValue('RD')
                tag = fa or ga or md or tr or ad or rd
                ndmin = 15
            elif self._combo.currentText() == 'SHCSA':
                wait.setInformationText('SHCSA Model definition...')
                model = SisypheSHCSAModel()
                order = self._SHCSA.getParameterValue('Order')
                model.setOrder(order)
                gfa = self._SHCSA.getParameterValue('GFA')
                tag = gfa
                ndmin = 100
            elif self._combo.currentText() == 'SHCSD':
                wait.setInformationText('SHCSD Model definition...')
                model = SisypheSHCSDModel()
                order = self._SHCSD.getParameterValue('Order')
                model.setOrder(order)
                gfa = self._SHCSD.getParameterValue('GFA')
                tag = gfa
                ndmin = 20
            elif self._combo.currentText() == 'DSI':
                wait.setInformationText('DSI Model definition...')
                gfa = self._DSI.getParameterValue('GFA')
                model = SisypheDSIModel()
                tag = gfa
                ndmin = 100
            elif self._combo.currentText() == 'DSID':
                wait.setInformationText('DSID Model definition...')
                gfa = self._DSID.getParameterValue('GFA')
                model = SisypheDSIDModel()
                tag = gfa
                ndmin = 100
            else: raise ValueError('Invalid model name ({}).'.format(self._combo.currentText()))
            # Load bvecs and bvals
            wait.setInformationText('Load gradient B values...')
            bvals = loadBVal(self._bvals.getFilename(), format='xml')
            dwinames = list(bvals.keys())
            bvals = array(list(bvals.values()))
            wait.setInformationText('Load gradient directions...')
            bvecs = loadBVec(self._bvecs.getFilename(), format='xml', numpy=True)
            # < Revision 08/04/2025
            # LPS+ to RAS+ orientation conversion
            conv = self._model.getParameterValue('Orientation')
            if conv is None: conv = False
            model.setGradients(bvals, bvecs, lpstoras=conv)
            # Revision 08/04/2025 >
            # < Revision 04/04/2025
            # verification of consistency between model and acquisition (DWI count)
            nd = len(bvals)
            nb0 = 0  # B0 count
            for i in range(nd):
                if bvals[i] == 0: nb0 += 1
            nd -= nb0  # DWI count
            # Acqusition validation
            if nd < ndmin:
                wait.close()
                messageBox(self, self.windowTitle(), 'Number of DWI images is not consistent '
                                                     'with the {} model.'.format(self._combo.currentText()))
                return
            # Revision 04/04/2025 >
            # Load dwi volumes
            vols = SisypheVolumeCollection()
            wait.setInformationText('Load diffusion weighted volumes...')
            wait.setProgressRange(0, len(dwinames)-1)
            wait.progressVisibilityOn()
            for dwiname in dwinames:
                # < Revision 03/07/2025
                dwiname= join(dirname(filename), dwiname)
                # Revision 03/07/2025 >
                if exists(dwiname):
                    wait.setInformationText('Load {}...'.format(basename(dwiname)))
                    wait.incCurrentProgressValue()
                    vol = SisypheVolume()
                    # noinspection PyTypeChecker
                    vol.load(dwiname)
                    vols.append(vol)
                else:
                    wait.close()
                    messageBox(self, self.windowTitle(), 'No such file {}'.format(dwiname))
                    return
            model.setDWI(vols)
            # Mask processing
            wait.setInformationText('Mask processing...')
            wait.progressVisibilityOff()
            QApplication.processEvents()
            algo = self._model.getParameterValue('Algo')[0]
            niter = self._model.getParameterValue('Iter')
            size = self._model.getParameterValue('Size')
            model.calcMask(algo, niter, size)
            # Model fitting
            filename = splitext(filename)[0] + model.getFileExt()
            wait.setInformationText('Model fitting...')
            try: model.computeFitting()
            except Exception as err:
                messageBox(self, self.windowTitle(), '{}'.format(err))
            # Save model
            if self._model.getParameterValue('Save'):
                wait.setInformationText('Save model...')
                QApplication.processEvents()
                model.saveModel(filename, wait)
            # Save maps
            if tag:
                # Revision 04/04/2025 >
                if fa:
                    wait.setInformationText('Save Fractional anisotropy map...')
                    v = model.getFA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('FA')
                    v.acquisition.setSequenceToFractionalAnisotropyMap()
                    v.setID(model.getReferenceID())
                    v.save()
                if ga:
                    wait.setInformationText('Save Geodesic anisotropy map...')
                    v = model.getGA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('GA')
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence('GA')
                    v.setID(model.getReferenceID())
                    v.save()
                if gfa:
                    wait.setInformationText('Save Generalized fractional anisotropy map...')
                    v = model.getGFA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('GFA')
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence('GFA')
                    v.setID(model.getReferenceID())
                    v.save()
                if md:
                    wait.setInformationText('Save Mean diffusivity map...')
                    v = model.getMD()
                    v.setFilename(filename)
                    v.setFilenameSuffix('MD')
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence('MD')
                    v.setID(model.getReferenceID())
                    v.save()
                if tr:
                    wait.setInformationText('Save Trace map...')
                    v = model.getTrace()
                    v.setFilename(filename)
                    v.setFilenameSuffix('TR')
                    v.acquisition.setSequenceToApparentDiffusionMap()
                    v.setID(model.getReferenceID())
                    v.save()
                if ad:
                    wait.setInformationText('Save Axial diffusivity map...')
                    v = model.getAxialDiffusivity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('AD')
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence('AD')
                    v.setID(model.getReferenceID())
                    v.save()
                if rd:
                    wait.setInformationText('Save Radial diffusivity map...')
                    v = model.getRadialDiffusivity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('RD')
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence('RD')
                    v.setID(model.getReferenceID())
                    v.save()
            wait.close()
            self._bvals.clear(signal=False)
            self._bvecs.clear(signal=False)
            self._save.setEnabled(False)

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
        elif self._combo.currentText() == 'DKI':
            method = self._DKI.getParameterValue('Method')[0]
            maps['fa'] = self._DKI.getParameterValue('FA')
            maps['ga'] = self._DKI.getParameterValue('GA')
            maps['md'] = self._DKI.getParameterValue('MD')
            maps['tr'] = self._DKI.getParameterValue('Trace')
            maps['ad'] = self._DKI.getParameterValue('AD')
            maps['rd'] = self._DKI.getParameterValue('RD')
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
