"""
    External packages/modules

        Name            Homepage link                                               Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import exists
from os.path import basename
from os.path import splitext

from numpy import array

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
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QDialog -> DialogDiffusionModel
"""

class DialogDiffusionModel(QDialog):
    """
        DialogDiffusionPreprocessing

        Description

            GUI dialog window for defining the diffusion model, model parameters
            and diffusion-derived maps to be processed.

        Inheritance

            QDialog -> DialogDiffusionPreprocessing

        Public methods

            save()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Diffusion gradients')
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
        self._DTI.setSettingsButtonText('DTI Model')
        self._DKI.setSettingsButtonText('DKI Model')
        self._SHCSA.setSettingsButtonText('SHCSA Model')
        self._SHCSD.setSettingsButtonText('SHCSD Model')
        self._DTI.settingsVisibilityOn()
        self._DKI.settingsVisibilityOn()
        self._SHCSA.settingsVisibilityOn()
        self._SHCSD.settingsVisibilityOn()
        self._DTI.hideIOButtons()
        self._DKI.hideIOButtons()
        self._SHCSA.hideIOButtons()
        self._SHCSD.hideIOButtons()
        self._modelChanged()
        self._DTI.VisibilityToggled.connect(self._center)
        self._DKI.VisibilityToggled.connect(self._center)
        self._SHCSA.VisibilityToggled.connect(self._center)
        self._SHCSD.VisibilityToggled.connect(self._center)

        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)
        self._layout.addWidget(self._model)
        self._layout.addWidget(self._DTI)
        self._layout.addWidget(self._DKI)
        self._layout.addWidget(self._SHCSA)
        self._layout.addWidget(self._SHCSD)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exit = QPushButton('Close')
        exit.setAutoDefault(True)
        exit.setDefault(True)
        exit.setFixedWidth(100)
        self._save = QPushButton('Save')
        self._save.setFixedWidth(100)
        self._save.setToolTip('save diffusion model')
        self._save.setEnabled(False)
        layout.addWidget(exit)
        layout.addWidget(self._save)
        layout.addStretch()

        self._layout.addLayout(layout)
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        exit.clicked.connect(self.accept)
        self._save.clicked.connect(self.save)

    # Private methods

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
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvals.getFilename())))
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
                QMessageBox.warning(self,
                                    self.windowTitle(),
                                    '{} format is invalid.'.format(basename(filename)))
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
                    self._bvecs.setToolTip(buff)

    def _updateBVecs(self):
        try: v1 = loadBVec(self._bvecs.getFilename(), format='xml')
        except:
            QMessageBox.warning(self,
                                self.windowTitle(),
                                '{} format is invalid.'.format(basename(self._bvecs.getFilename())))
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
                QMessageBox.warning(self,
                                    self.windowTitle(),
                                    '{} format is invalid.'.format(basename(filename)))
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
                    self._bvals.setToolTip(buff)

    def _modelChanged(self):
        self._DTI.setVisible(self._combo.currentText() == 'DTI')
        self._DKI.setVisible(self._combo.currentText() == 'DKI')
        self._SHCSA.setVisible(self._combo.currentText() == 'SHCSA')
        self._SHCSD.setVisible(self._combo.currentText() == 'SHCSD')
        self._center(None)

    # Public methods

    def save(self):
        if not (self._bvals.isEmpty() or self._bvecs.isEmpty()):
            wait = DialogWait(parent=self)
            wait.setInformationText('Model definition...')
            wait.progressVisibilityOff()
            wait.open()
            filename = splitext(self._bvals.getFilename())[0] + SisypheDTIModel.getFileExt()
            fa = kfa = ga = gfa = md = ly = py = sy = tr = ad = rd = ic = dc = False
            if self._combo.currentText() == 'DTI':
                wait.setInformationText('DTI Model definition...')
                model = SisypheDTIModel()
                method = self._DTI.getParameterValue('Method')
                model.setFitAlgorithm(method)
                fa = self._DTI.getParameterValue('FA')
                ga = self._DTI.getParameterValue('GA')
                md = self._DTI.getParameterValue('MD')
                ly = self._DTI.getParameterValue('Linearity')
                py = self._DTI.getParameterValue('Planarity')
                sy = self._DTI.getParameterValue('Sphericity')
                tr = self._DTI.getParameterValue('Trace')
                ad = self._DTI.getParameterValue('AD')
                rd = self._DTI.getParameterValue('RD')
                ic = self._DTI.getParameterValue('Isotropic')
                dc = self._DTI.getParameterValue('Deviatropic')
                tag = fa or ga or md or ly or py or sy or tr or ad or rd or ic or dc
            elif self._combo.currentText() == 'DKI':
                wait.setInformationText('DKI Model definition...')
                model = SisypheDKIModel()
                method = self._DTI.getParameterValue('Method')
                model.setFitAlgorithm(method)
                fa = self._DKI.getParameterValue('FA')
                kfa = self._DKI.getParameterValue('KFA')
                ga = self._DKI.getParameterValue('GA')
                md = self._DKI.getParameterValue('MD')
                ly = self._DKI.getParameterValue('Linearity')
                py = self._DKI.getParameterValue('Planarity')
                sy = self._DKI.getParameterValue('Sphericity')
                tr = self._DKI.getParameterValue('Trace')
                ad = self._DKI.getParameterValue('AD')
                rd = self._DKI.getParameterValue('PD')
                tag = fa or kfa or ga or md or ly or py or sy or tr or ad or rd
            elif self._combo.currentText() == 'SHCSA':
                wait.setInformationText('SHCSA Model definition...')
                model = SisypheSHCSAModel()
                order = self._DTI.getParameterValue('Order')
                model.setOrder(order)
                gfa = self._SHCSA.getParameterValue('GFA')
                tag = gfa
            elif self._combo.currentText() == 'SHCSD':
                wait.setInformationText('SHCSD Model definition...')
                model = SisypheSHCSDModel()
                order = self._DTI.getParameterValue('Order')
                model.setOrder(order)
                gfa = self._SHCSD.getParameterValue('GFA')
                tag = gfa
            elif self._combo.currentText() == 'DSI':
                wait.setInformationText('DSI Model definition...')
                model = SisypheDSIModel()
                tag = False
            else:
                wait.setInformationText('DSID Model definition...')
                model = SisypheDSIDModel()
                tag = False
            # Load bvecs and bvals
            wait.setInformationText('Load gradient B values...')
            bvals = loadBVal(self._bvals.getFilename(), format='xml')
            dwinames = list(bvals.keys())
            bvals = array(list(bvals.values()))
            wait.setInformationText('Load gradient directions...')
            bvecs = loadBVec(self._bvecs.getFilename(), format='xml', numpy=True)
            model.setGradients(bvals, bvecs)
            # Load dwi volumes
            vols = SisypheVolumeCollection()
            wait.setInformationText('Load diffusion weighted volumes...')
            wait.setProgressRange(0, len(dwinames)-1)
            wait.progressVisibilityOn()
            for dwiname in dwinames:
                wait.setInformationText('Load {}...'.format(dwiname))
                wait.incCurrentProgressValue()
                vol = SisypheVolume()
                vol.load(dwiname)
                vols.append(vol)
            # Mask processing
            wait.setInformationText('Mask processing...')
            wait.progressVisibilityOff()
            QApplication.processEvents()
            algo = self._model.getParameterValue('Algo')
            niter = self._model.getParameterValue('Iter')
            size = self._model.getParameterValue('Size')
            model.setDWI(vols, algo, niter, size)
            # Save model
            wait.setInformationText('Save model...')
            QApplication.processEvents()
            model.saveModel(filename, wait)
            # Maps processing
            if tag:
                filename = splitext(filename)[0] + SisypheVolume.getFileExt()
                wait.setInformationText('Model fitting...')
                model.computeFitting()
                if fa:
                    wait.setInformationText('FA map processing...')
                    v = model.getFA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('FA')
                    v.save()
                if kfa:
                    wait.setInformationText('KFA map processing...')
                    v = model.getKFA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('KFA')
                    v.save()
                if ga:
                    wait.setInformationText('GA map processing...')
                    v = model.getGA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('GA')
                    v.save()
                if gfa:
                    wait.setInformationText('GFA map processing...')
                    v = model.getGFA()
                    v.setFilename(filename)
                    v.setFilenameSuffix('GFA')
                    v.save()
                if md:
                    wait.setInformationText('MD map processing...')
                    v = model.getMD()
                    v.setFilename(filename)
                    v.setFilenameSuffix('MD')
                    v.save()
                if ly:
                    wait.setInformationText('Linearity map processing...')
                    v = model.getLinearity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('Linearity')
                    v.save()
                if py:
                    wait.setInformationText('Planarity map processing...')
                    v = model.getPlanarity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('Planarity')
                    v.save()
                if sy:
                    wait.setInformationText('Sphericity map processing...')
                    v = model.getSphericity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('Sphericity')
                    v.save()
                if tr:
                    wait.setInformationText('Trace map processing...')
                    v = model.getTrace()
                    v.setFilename(filename)
                    v.setFilenameSuffix('TR')
                    v.save()
                if ad:
                    wait.setInformationText('Axial diffusivity map processing...')
                    v = model.getAxialDiffusivity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('AD')
                    v.save()
                if rd:
                    wait.setInformationText('Radial diffusivity map processing...')
                    v = model.getRadialDiffusivity()
                    v.setFilename(filename)
                    v.setFilenameSuffix('RD')
                    v.save()
                if ic:
                    wait.setInformationText('Isotropic diffusivity map processing...')
                    v = model.getIsotropic()
                    v.setFilename(filename)
                    v.setFilenameSuffix('Isotropic')
                    v.save()
                if dc:
                    wait.setInformationText('Deviatropic diffusivity map processing...')
                    v = model.getDeviatropic()
                    v.setFilename(filename)
                    v.setFilenameSuffix('Deviatropic')
                    v.save()
            wait.close()
            self._bvals.clear(signal=False)
            self._bvecs.clear(signal=False)
            self._save.setEnabled(False)

"""
    Test
"""

if __name__ == '__main__':
    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogDiffusionModel()
    main.show()
    app.exec_()
