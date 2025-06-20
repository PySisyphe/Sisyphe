"""
External packages/modules
-------------------------

    - ANTs, image registration, http://stnava.github.io/ANTs/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepTumorSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepHippocampusSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepMedialTemporalSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepLesionSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepWhiteMatterHyperIntensitiesSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepTOFVesselSegmentation
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepTissueSegmentation
from multiprocessing import Queue

from sys import platform

from os import remove

from os.path import join
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.selectFileWidgets import SynchronizedFilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWaitRegistration

_all__ = ['DialogDeepTumorSegmentation',
          'DialogDeepHippocampusSegmentation',
          'DialogDeepMedialTemporalSegmentation',
          'DialogDeepLesionSegmentation',
          'DialogDeepWhiteMatterHyperIntensitiesSegmentation',
          'DialogDeepTOFVesselSegmentation',
          'DialogDeepTissueSegmentation']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDeepTumorSegmentation
              -> DialogDeepHippocampusSegmentation
              -> DialogDeepMedialTemporalSegmentation
              -> DialogDeepLesionSegmentation
              -> DialogDeepWhiteMatterHyperIntensitiesSegmentation
              -> DialogDeepTOFVesselSegmentation
"""


class DialogDeepTumorSegmentation(QDialog):
    """
    DialogDeepTumorSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning tumor segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepTumorSegmentation

    Creation: 22/10/2024
    Last revision: 03/06/2025
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net tumor segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = SynchronizedFilesSelectionWidget(single=None,
                                                              multiple=('FLAIR',
                                                                        'T1',
                                                                        'Contrast-enhanced T1',
                                                                        'T2'),
                                                              parent=self)
        self._volumeSelect.setSisypheVolumeFilters({'multiple': [True, True, True, True]})
        flt = {'multiple': [SisypheAcquisition.FLAIR,
                            SisypheAcquisition.T1,
                            SisypheAcquisition.CET1,
                            SisypheAcquisition.T2]}
        self._volumeSelect.setSequenceFilters(flt)
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setMaximumHeight(800)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetTumorSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidgets(self):
        return self._volumeSelect.getSelectionWidgets()

    def execute(self):
        if self._volumeSelect.isReady():
            filenames = self._volumeSelect.getFilenames()
            filenames1 = filenames['multiple']['FLAIR']
            filenames2 = filenames['multiple']['T1']
            filenames3 = filenames['multiple']['Contrast-enhanced T1']
            filenames4 = filenames['multiple']['T2']
            if len(filenames1) > 0:
                for i in range(len(filenames1)):
                    wait = DialogWaitRegistration()
                    wait.open()
                    w = self._volumeSelect.getSelectionWidget('FLAIR')
                    if w is not None:
                        w.clearSelection()
                        w.setSelectionTo(i)
                    wait.setInformationText('Load {}...'.format(basename(filenames1[i])))
                    flair = SisypheVolume()
                    flair.load(filenames1[i])
                    t1 = None
                    if filenames2 is not None:
                        if i < len(filenames2):
                            wait.setInformationText('Load {}...'.format(basename(filenames2[i])))
                            t1 = SisypheVolume()
                            t1.load(filenames2[i])
                    else:
                        messageBox(self, self.windowTitle(), 'Missing T1.')
                        wait.close()
                        return
                    t1ce = None
                    if filenames3 is not None:
                        if i < len(filenames3):
                            wait.setInformationText('Load {}...'.format(basename(filenames3[i])))
                            t1ce = SisypheVolume()
                            t1ce.load(filenames3[i])
                    else:
                        messageBox(self, self.windowTitle(), 'Missing contrast-enhanced T1.')
                        wait.close()
                        return
                    t2 = None
                    if filenames4 is not None:
                        if i < len(filenames4):
                            wait.setInformationText('Load {}...'.format(basename(filenames4[i])))
                            t2 = SisypheVolume()
                            t2.load(filenames4[i])
                    else:
                        messageBox(self, self.windowTitle(), 'Missing T2.')
                        wait.close()
                        return
                    """
                    Segmentation
                    """
                    # noinspection PyUnusedLocal
                    r = None
                    wait.setInformationText('U-net tumor segmentation initialization...')
                    wait.setButtonVisibility(True)
                    queue = Queue()
                    stdout = join(flair.getDirname(), 'stdout.log')
                    extractor = ProcessDeepTumorSegmentation(flair, t1, t1ce, t2, self._getAntspynetCacheDirectory(), stdout, queue)
                    try:
                        extractor.start()
                        while extractor.is_alive():
                            if exists(stdout): wait.setAntspynetTumorProgress(stdout)
                            if not queue.empty():
                                # noinspection PyUnusedLocal
                                r = queue.get()
                                if extractor.is_alive(): extractor.terminate()
                                wait.progressVisibilityOff()
                            if wait.getStopped(): extractor.terminate()
                    except Exception as err:
                        if extractor.is_alive(): extractor.terminate()
                        wait.hide()
                        if not wait.getStopped():
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} U-net tumor segmentation error: '
                                            '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                            return
                    finally:
                        # Remove temporary std::cout file
                        if exists(stdout): remove(stdout)
                    # noinspection PyUnreachableCode
                    if wait.getStopped():
                        wait.close()
                        return
                    """
                    Save
                    """
                    wait.setButtonVisibility(False)
                    if r is not None:
                        # Label map
                        prefix = self._settings.getParameterValue('Prefix')
                        suffix = self._settings.getParameterValue('Suffix')
                        v = SisypheVolume()
                        v.copyFromNumpyArray(r['lbl'].astype('uint8'), spacing=t1ce.getSpacing(), defaultshape=False)
                        v.copyAttributesFrom(t1ce, display=False, slope=False)
                        v.acquisition.setModalityToLB()
                        v.setFilename(filenames3[i])
                        v.setFilenamePrefix(prefix)
                        v.setFilenameSuffix(suffix)
                        saveroi = self._settings.getParameterValue('SaveROI')
                        # Probability maps
                        lbls = {0: 'non-tumoral parenchyma',
                                1: 'non-enhancing/necrotic tumor core',
                                2: 'peritumoral edema',
                                3: '',
                                4: 'enhancing tumor core'}
                        for lbl in lbls:
                            v.acquisition.setLabel(i, lbls[lbl])
                            if lbl in (1, 2, 4) and saveroi:
                                roi = v.labelToROI(lbl)
                                roi.setFilename(filenames3[i])
                                if lbl == 1: roi.setFilenameSuffix('net')
                                elif lbl == 2: roi.setFilenameSuffix('ed')
                                elif lbl == 4: roi.setFilenameSuffix('et')
                                wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                roi.save()
                        wait.setInformationText('Save {}...'.format(v.getBasename()))
                        v.save()
                        for j in range(len(r['prb'])):
                            if j in (1, 2, 4):
                                v2 = SisypheVolume()
                                v2.copyFromNumpyArray(r['prb'][j], spacing=t1ce.getSpacing(), defaultshape=False)
                                v2.copyAttributesFrom(t1ce, display=False, slope=False)
                                v2.acquisition.setModalityToOT()
                                v2.acquisition.setSequenceToStructMap()
                                v2.setFilename(filenames3[i])
                                if j == 1: v2.setFilenameSuffix('net')
                                elif j == 2: v2.setFilenameSuffix('ed')
                                elif j == 4: v2.setFilenameSuffix('et')
                                wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                v2.save()
                    wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore tumor segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()


class DialogDeepHippocampusSegmentation(QDialog):
    """
    DialogDeepHippocampusSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning hippocampus segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepHippocampusSegmentation

    Creation: 22/10/2024
    Last revision: 03/06/2025
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net hippocampus segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.filterSameSequence(SisypheAcquisition.T1)
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('T1')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetHippocampusSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            if len(filenames) > 0:
                for index, filename in enumerate(filenames):
                    wait = DialogWaitRegistration()
                    wait.open()
                    self._volumeSelect.clearSelection()
                    self._volumeSelect.setSelectionTo(index)
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        t1 = SisypheVolume()
                        t1.load(filename)
                        """
                        Segmentation
                        """
                        # noinspection PyUnusedLocal
                        r = None
                        wait.setInformationText('U-net hippocampus segmentation initialization...')
                        wait.setButtonVisibility(True)
                        queue = Queue()
                        stdout = join(t1.getDirname(), 'stdout.log')
                        extractor = ProcessDeepHippocampusSegmentation(t1, self._getAntspynetCacheDirectory(), stdout, queue)
                        try:
                            extractor.start()
                            while extractor.is_alive():
                                if exists(stdout): wait.setAntspynetHippocamusProgress(stdout)
                                if not queue.empty():
                                    # noinspection PyUnusedLocal
                                    r = queue.get()
                                    if extractor.is_alive(): extractor.terminate()
                                    wait.progressVisibilityOff()
                                if wait.getStopped(): extractor.terminate()
                        except Exception as err:
                            if extractor.is_alive(): extractor.terminate()
                            wait.hide()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} U-net hippocampus segmentation error: '
                                                '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                                return
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        """
                        Save
                        """
                        wait.setButtonVisibility(False)
                        if r is not None:
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            v = SisypheVolume()
                            v.copyFromNumpyArray(r.astype('uint8'), spacing=t1.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(t1, display=False, slope=False)
                            v.acquisition.setModalityToLB()
                            v.setFilename(t1.getFilename())
                            v.setFilenamePrefix(prefix)
                            v.setFilenameSuffix(suffix)
                            saveroi = self._settings.getParameterValue('SaveROI')
                            lbls = ('background', 'right hippocampus', 'left hippocampus')
                            for j in range(len(lbls)):
                                v.acquisition.setLabel(j, lbls[j])
                                if saveroi and j > 0:
                                    roi = v.labelToROI(j)
                                    roi.setFilename(t1.getFilename())
                                    roi.setFilenameSuffix(lbls[j])
                                    wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                    roi.save()
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                    wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore hippocampus segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()


class DialogDeepMedialTemporalSegmentation(QDialog):
    """
    DialogDeepMedialTemporalSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning segmentation of medial temporal structures.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepMedialTemporalSegmentation

    Creation: 22/10/2024
    Last revision: 03/06/2025
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net medial temporal segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = SynchronizedFilesSelectionWidget(single=None,
                                                              multiple=('T1',
                                                                        'T2'),
                                                              parent=self)
        self._volumeSelect.setSisypheVolumeFilters({'multiple': [True, True]})
        flt = {'multiple': [SisypheAcquisition.T1, SisypheAcquisition.T2]}
        self._volumeSelect.setSequenceFilters(flt)
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setMaximumHeight(800)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetMedialTemporalSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._settings.getParameterWidget('UseT2').stateChanged.connect(self._useT2Changed)
        self._useT2Changed()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _useT2Changed(self):
        flag = self._settings.getParameterValue('UseT2')
        flags = self._volumeSelect.getAvailability()
        flags['multiple']['T1'] = True
        flags['multiple']['T2'] = flag
        self._volumeSelect.setAvailability(flags)

    # Public method

    def getSelectionWidgets(self):
        return self._volumeSelect.getSelectionWidgets()

    def execute(self):
        if self._volumeSelect.isReady():
            filenames = self._volumeSelect.getFilenames()
            filenames1 = filenames['multiple']['T1']
            filenames2 = filenames['multiple']['T2']
            model = self._settings.getParameterValue('Model')[0]
            if len(filenames1) > 0:
                for i in range(len(filenames1)):
                    wait = DialogWaitRegistration()
                    wait.open()
                    w = self._volumeSelect.getSelectionWidget('T1')
                    if w is not None:
                        w.clearSelection()
                        w.setSelectionTo(i)
                    wait.setInformationText('Load {}...'.format(basename(filenames1[i])))
                    t1 = SisypheVolume()
                    t1.load(filenames1[i])
                    t2 = None
                    if filenames2 is not None:
                        if i < len(filenames2):
                            wait.setInformationText('Load {}...'.format(basename(filenames2[i])))
                            t2 = SisypheVolume()
                            t2.load(filenames2[i])
                    """
                    Segmentation
                    """
                    # noinspection PyUnusedLocal
                    r = None
                    wait.setInformationText('U-net temporal segmentation initialization...')
                    wait.setButtonVisibility(True)
                    queue = Queue()
                    stdout = join(t1.getDirname(), 'stdout.log')
                    extractor = ProcessDeepMedialTemporalSegmentation(t1, t2, model, self._getAntspynetCacheDirectory(), stdout, queue)
                    try:
                        extractor.start()
                        while extractor.is_alive():
                            if exists(stdout): wait.setAntspynetTemporalProgress(stdout)
                            if not queue.empty():
                                # noinspection PyUnusedLocal
                                r = queue.get()
                                if extractor.is_alive(): extractor.terminate()
                                wait.progressVisibilityOff()
                            if wait.getStopped(): extractor.terminate()
                    except Exception as err:
                        if extractor.is_alive(): extractor.terminate()
                        wait.hide()
                        if not wait.getStopped():
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} U-net temporal segmentation error: '
                                            '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                            return
                    finally:
                        # Remove temporary std::cout file
                        if exists(stdout): remove(stdout)
                    # noinspection PyUnreachableCode
                    if wait.getStopped():
                        wait.close()
                        return
                    """
                    Save
                    """
                    wait.setButtonVisibility(False)
                    if r is not None:
                        prefix = self._settings.getParameterValue('Prefix')
                        suffix = self._settings.getParameterValue('Suffix')
                        saveroi = self._settings.getParameterValue('SaveROI')
                        saveprob = self._settings.getParameterValue('SaveProbability')
                        v = SisypheVolume()
                        if model == 'yassa':
                            v.copyFromNumpyArray(r['lbl'].astype('uint8'), spacing=t1.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(t1, display=False, slope=False)
                            v.acquisition.setModalityToLB()
                        elif model == 'wip':
                            v.copyFromNumpyArray(r['lbl'].astype('uint16'), spacing=t1.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(t1, display=False, slope=False)
                            v.acquisition.setModalityToOT()
                        v.setFilename(t1.getFilename())
                        v.setFilenamePrefix(prefix)
                        v.setFilenameSuffix(suffix)
                        # Probability
                        if model == 'yassa':
                            lbls = {0: 'background',
                                    5: 'left anterior-lateral entorhinal',
                                    6: 'right anterior-lateral entorhinal',
                                    7: 'left posterior-medial entorhinal',
                                    8: 'right posterior-medial entorhinal',
                                    9: 'left perirhinal',
                                    10: 'right perirhinal',
                                    11: 'left parahippocampal',
                                    12: 'right parahippocampal',
                                    13: 'left DG-CA2-CA3-CA4',
                                    14: 'right DG-CA2-CA3-CA4',
                                    15: 'left CA1',
                                    16: 'right CA1',
                                    17: 'left subiculum',
                                    18: 'right subiculum'}
                            for k in lbls:
                                v.acquisition.setLabel(k, lbls[k])
                                if saveroi and k > 0:
                                    roi = v.labelToROI(k)
                                    roi.setFilename(t1.getFilename())
                                    roi.setFilenamePrefix('')
                                    roi.setFilenameSuffix(lbls[k])
                                    wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                    roi.save()
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                            if saveprob:
                                for j, k in enumerate(lbls):
                                    if k > 0:
                                        v2 = SisypheVolume()
                                        v2.copyFromNumpyArray(r['prb'][j], spacing=t1.getSpacing(), defaultshape=False)
                                        v2.copyAttributesFrom(t1, display=False, slope=False)
                                        v2.acquisition.setModalityToOT()
                                        v2.acquisition.setSequenceToStructMap()
                                        v2.setFilename(t1.getFilename())
                                        v2.setFilenamePrefix('')
                                        v2.setFilenameSuffix(lbls[k])
                                        wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                        v2.save()
                                lbls = {'med': 'medial',
                                        'hip': 'hippocampus'}
                                for k in lbls:
                                    v2 = SisypheVolume()
                                    v2.copyFromNumpyArray(r[k], spacing=t1.getSpacing(), defaultshape=False)
                                    v2.copyAttributesFrom(t1, display=False, slope=False)
                                    v2.acquisition.setModalityToOT()
                                    v2.acquisition.setSequenceToStructMap()
                                    v2.setFilename(t1.getFilename())
                                    v2.setFilenamePrefix('')
                                    v2.setFilenameSuffix(lbls[k])
                                    wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                    v2.save()
                        elif model == 'wip':
                            lbls = (0, 104, 204, 105, 205, 106, 206, 108, 208, 109, 209, 110, 210, 114, 214, 115, 225,
                                    126, 226, 6001, 7001, 6003, 7003, 6008, 7008, 6009, 7009, 6010, 7010)
                            for k in lbls:
                                # v.acquisition.setLabel(k, str(k))
                                if saveroi and k > 0:
                                    roi = v.getROI(k, '==')
                                    roi.setFilename(t1.getFilename())
                                    roi.setFilenamePrefix('')
                                    roi.setFilenameSuffix(str(k))
                                    wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                    roi.save()
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                            if saveprob:
                                for j, k in enumerate(lbls):
                                    if k > 0:
                                        v2 = SisypheVolume()
                                        v2.copyFromNumpyArray(r['prb'][j], spacing=t1.getSpacing(), defaultshape=False)
                                        v2.copyAttributesFrom(t1, display=False, slope=False)
                                        v2.acquisition.setModalityToOT()
                                        v2.acquisition.setSequenceToStructMap()
                                        v2.setFilename(t1.getFilename())
                                        v2.setFilenamePrefix('')
                                        v2.setFilenameSuffix(str(k))
                                        wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                        v2.save()
                                lbls = {'hip': 'hippocampus',
                                        'amg': 'amygdala'}
                                for k in lbls:
                                    v2 = SisypheVolume()
                                    v2.copyFromNumpyArray(r[k], spacing=t1.getSpacing(), defaultshape=False)
                                    v2.copyAttributesFrom(t1, display=False, slope=False)
                                    v2.acquisition.setModalityToOT()
                                    v2.acquisition.setSequenceToStructMap()
                                    v2.setFilename(t1.getFilename())
                                    v2.setFilenamePrefix('')
                                    v2.setFilenameSuffix(lbls[k])
                                    wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                    v2.save()
                    wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore medial temporal segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()


class DialogDeepLesionSegmentation(QDialog):
    """
    DialogDeepLesionSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning T1-hypo-intensity lesion segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepLesionSegmentation

    Creation: 22/10/2024
    Last revision: 03/06/2025
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net lesion segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.filterSameSequence(SisypheAcquisition.T1)
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('T1')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetLesionSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            if len(filenames) > 0:
                for index, filename in enumerate(filenames):
                    wait = DialogWaitRegistration()
                    wait.open()
                    self._volumeSelect.clearSelection()
                    self._volumeSelect.setSelectionTo(index)
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        t1 = SisypheVolume()
                        t1.load(filename)
                        """
                        Segmentation
                        """
                        # noinspection PyUnusedLocal
                        r = None
                        wait.setInformationText('U-net lesion segmentation initialization...')
                        wait.setButtonVisibility(True)
                        queue = Queue()
                        stdout = join(t1.getDirname(), 'stdout.log')
                        extractor = ProcessDeepLesionSegmentation(t1, self._getAntspynetCacheDirectory(), stdout, queue)
                        try:
                            extractor.start()
                            while extractor.is_alive():
                                if exists(stdout): wait.setAntspynetLesionProgress(stdout)
                                if not queue.empty():
                                    # noinspection PyUnusedLocal
                                    r = queue.get()
                                    if extractor.is_alive(): extractor.terminate()
                                    wait.progressVisibilityOff()
                                if wait.getStopped(): extractor.terminate()
                        except Exception as err:
                            if extractor.is_alive(): extractor.terminate()
                            wait.hide()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} U-net lesion segmentation error: '
                                                '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                                return
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        """
                        Save
                        """
                        wait.setButtonVisibility(False)
                        if r is not None:
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            v = SisypheVolume()
                            v.copyFromNumpyArray(r, spacing=t1.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(t1, display=False, slope=False)
                            v.acquisition.setModalityToOT()
                            v.acquisition.setSequenceToMask()
                            v.setFilename(t1.getFilename())
                            v.setFilenamePrefix(prefix)
                            v.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                            saveroi = self._settings.getParameterValue('SaveROI')
                            if saveroi:
                                roi = v.getROI(0.5,'>=')
                                roi.setFilename(t1.getFilename())
                                roi.setFilenamePrefix(prefix)
                                roi.setFilenameSuffix(suffix)
                                wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                roi.save()
                    wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore lesion segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()


class DialogDeepWhiteMatterHyperIntensitiesSegmentation(QDialog):
    """
    DialogDeepWhiteMatterHyperIntensitiesSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning white matter FLAIR-hyper-intensities segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepWhiteMatterHyperIntensitiesSegmentation

    Creation: 22/10/2024
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net white matter hyper-intensities segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = SynchronizedFilesSelectionWidget(single=None,
                                                              multiple=('FLAIR',
                                                                        'T1',
                                                                        'White matter map(s)',
                                                                        'Sub-cortical gray matter map(s)'),
                                                              parent=self)
        self._volumeSelect.setSisypheVolumeFilters({'multiple': [True, True, True, True]})
        flt = {'multiple': [SisypheAcquisition.FLAIR,
                            SisypheAcquisition.T1,
                            SisypheAcquisition.WM,
                            SisypheAcquisition.SCGM]}
        self._volumeSelect.setSequenceFilters(flt)
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setMaximumHeight(800)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetWMHSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._settings.getParameterWidget('UseT1').stateChanged.connect(self._useT1Changed)
        self._settings.getParameterWidget('Model').currentIndexChanged.connect(self._modelChanged)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _useT1Changed(self):
        flag = self._settings.getParameterValue('UseT1')
        flags = self._volumeSelect.getAvailability()
        flags['multiple']['T1'] = flag
        self._volumeSelect.setAvailability(flags)

    def _modelChanged(self):
        model = self._settings.getParameterValue('Model')[0]
        flags = self._volumeSelect.getAvailability()
        flags['multiple']['White matter map(s)'] = (model == 'antsxnet')
        flags['multiple']['Sub-cortical gray matter map(s)'] = (model == 'antsxnet')
        self._volumeSelect.setAvailability(flags)

    # Public method

    def getSelectionWidgets(self):
        return self._volumeSelect.getSelectionWidgets()

    def execute(self):
        if self._volumeSelect.isReady():
            filenames = self._volumeSelect.getFilenames()
            filenames1 = filenames['multiple']['FLAIR']
            filenames2 = filenames['multiple']['T1']
            filenames3 = filenames['multiple']['White matter map(s)']
            filenames4 = filenames['multiple']['Sub-cortical gray matter map(s)']
            if len(filenames1) > 0:
                for i in range(len(filenames1)):
                    wait = DialogWaitRegistration()
                    wait.open()
                    w = self._volumeSelect.getSelectionWidget('FLAIR')
                    if w is not None:
                        w.clearSelection()
                        w.setSelectionTo(i)
                    wait.setInformationText('Load {}...'.format(basename(filenames1[i])))
                    flair = SisypheVolume()
                    flair.load(filenames1[i])
                    t1 = None
                    if filenames2 is not None:
                        if i < len(filenames2):
                            wait.setInformationText('Load {}...'.format(basename(filenames2[i])))
                            t1 = SisypheVolume()
                            t1.load(filenames2[i])
                    mask = None
                    model = self._settings.getParameterValue('Model')[0]
                    if model == 'antsxnet':
                        wm = None
                        if filenames3 is not None:
                            if i < len(filenames3):
                                wait.setInformationText('Load {}...'.format(basename(filenames3[i])))
                                wm = SisypheVolume()
                                wm.load(filenames3[i])
                        scgm = None
                        if filenames4 is not None:
                            if i < len(filenames4):
                                wait.setInformationText('Load {}...'.format(basename(filenames4[i])))
                                scgm = SisypheVolume()
                                scgm.load(filenames4[i])
                        if wm is not None and scgm is not None: mask = wm + scgm
                        else: model = 'sysu'
                    """
                    Segmentation
                    """
                    # noinspection PyUnusedLocal
                    r = None
                    wait.setInformationText('U-net white matter hyper-intensities segmentation initialization...')
                    wait.setButtonVisibility(True)
                    stdout = join(flair.getDirname(), 'stdout.log')
                    queue = Queue()
                    extractor = ProcessDeepWhiteMatterHyperIntensitiesSegmentation(flair, t1, mask, model, self._getAntspynetCacheDirectory(), stdout, queue)
                    try:
                        wait.setInformationText('U-net white matter hyper-intensities segmentation...')
                        extractor.start()
                        while extractor.is_alive():
                            if not queue.empty():
                                # noinspection PyUnusedLocal
                                r = queue.get()
                                if extractor.is_alive(): extractor.terminate()
                            if wait.getStopped(): extractor.terminate()
                    except Exception as err:
                        if extractor.is_alive(): extractor.terminate()
                        wait.hide()
                        if not wait.getStopped():
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} U-net white matter hyper-intensities segmentation error: '
                                            '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                            return
                    finally:
                        # Remove temporary std::cout file
                        if exists(stdout): remove(stdout)
                    # noinspection PyUnreachableCode
                    if wait.getStopped():
                        wait.close()
                        return
                    """
                    Save
                    """
                    wait.setButtonVisibility(False)
                    if r is not None:
                        prefix = self._settings.getParameterValue('Prefix')
                        suffix = self._settings.getParameterValue('Suffix')
                        v = SisypheVolume()
                        v.copyFromNumpyArray(r, spacing=flair.getSpacing(), defaultshape=False)
                        v.copyAttributesFrom(flair, display=False, slope=False)
                        v.acquisition.setModalityToOT()
                        v.acquisition.setSequenceToMask()
                        v.setFilename(flair.getFilename())
                        v.setFilenamePrefix(prefix)
                        v.setFilenameSuffix(suffix)
                        wait.setInformationText('Save {}...'.format(v.getBasename()))
                        v.save()
                        saveroi = self._settings.getParameterValue('SaveROI')
                        if saveroi:
                            roi = v.getROI(0.5, '>')
                            roi.setFilename(flair.getFilename())
                            roi.setFilenamePrefix(prefix)
                            roi.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                            roi.save()
                    wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore white matter hyper-intensities segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self._useT1Changed()
        self._modelChanged()
        self._center(None)


class DialogDeepTOFVesselSegmentation(QDialog):
    """
    DialogDeepTOFVesselSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep learning segmentation of TOF vessels.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepTOFVesselSegmentation

    Creation: 22/10/2024
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net TOF vessel segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.filterSameSequence(SisypheAcquisition.TOF)
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('TOF')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetTOFSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            if len(filenames) > 0:
                for index, filename in enumerate(filenames):
                    wait = DialogWaitRegistration()
                    wait.open()
                    self._volumeSelect.clearSelection()
                    self._volumeSelect.setSelectionTo(index)
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        tof = SisypheVolume()
                        tof.load(filename)
                        """
                        Segmentation
                        """
                        # noinspection PyUnusedLocal
                        r = None
                        wait.setInformationText('U-net vessel segmentation initialization...')
                        wait.setButtonVisibility(True)
                        stdout = join(tof.getDirname(), 'stdout.log')
                        queue = Queue()
                        extractor = ProcessDeepTOFVesselSegmentation(tof, self._getAntspynetCacheDirectory(), stdout, queue)
                        try:
                            extractor.start()
                            while extractor.is_alive():
                                if exists(stdout): wait.setAntspynetVesselProgress(stdout)
                                if not queue.empty():
                                    # noinspection PyUnusedLocal
                                    r = queue.get()
                                    extractor.terminate()
                                    wait.progressVisibilityOff()
                                if wait.getStopped(): extractor.terminate()
                        except Exception as err:
                            if flt.is_alive(): flt.terminate()
                            wait.hide()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} U-net vessel segmentation error: '
                                                '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                                return
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        """
                        Save
                        """
                        wait.setButtonVisibility(False)
                        if r is not None:
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            v = SisypheVolume()
                            v.copyFromNumpyArray(r, spacing=tof.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(tof, display=False, slope=False)
                            v.acquisition.setModalityToOT()
                            v.acquisition.setSequenceToMask()
                            v.setFilename(tof.getFilename())
                            v.setFilenamePrefix(prefix)
                            v.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                            saveroi = self._settings.getParameterValue('SaveROI')
                            if saveroi:
                                roi = v.getROI(0.5,'>')
                                roi.setFilename(tof.getFilename())
                                roi.setFilenamePrefix(prefix)
                                roi.setFilenameSuffix(suffix)
                                wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                roi.save()
                    wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore vessel segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()


class DialogDeepTissueSegmentation(QDialog):
    """
    DialogDeepTissueSegmentation

    Description
    ~~~~~~~~~~~

    GUI dialog for deep tissue segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDeepTissueSegmentation

    Creation: 03/06/2025
    Last revision: 03/06/2025
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('U-net tissue segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.filterSameSequence(SisypheAcquisition.T1)
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('T1')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)
        self._layout.addWidget(self._volumeSelect)

        self._settings = FunctionSettingsWidget('UnetTissueSegmentation', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        # cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        # self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 20/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 20/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            if len(filenames) > 0:
                for index, filename in enumerate(filenames):
                    wait = DialogWaitRegistration()
                    wait.open()
                    self._volumeSelect.clearSelection()
                    self._volumeSelect.setSelectionTo(index)
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        t1 = SisypheVolume()
                        t1.load(filename)
                        """
                        Segmentation
                        """
                        # noinspection PyUnusedLocal
                        r = None
                        wait.setInformationText('U-net tissue segmentation initialization...')
                        wait.setButtonVisibility(True)
                        queue = Queue()
                        stdout = join(t1.getDirname(), 'stdout.log')
                        extractor = ProcessDeepTissueSegmentation(t1, self._getAntspynetCacheDirectory(), stdout, queue)
                        try:
                            extractor.start()
                            while extractor.is_alive():
                                if exists(stdout): wait.setAntspynetTissueProgress(stdout)
                                if not queue.empty():
                                    # noinspection PyUnusedLocal
                                    r = queue.get()
                                    if extractor.is_alive(): extractor.terminate()
                                    wait.progressVisibilityOff()
                                if wait.getStopped(): extractor.terminate()
                        except Exception as err:
                            if extractor.is_alive(): extractor.terminate()
                            wait.hide()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} U-net tissue segmentation error: '
                                                '{}\n{}.'.format(flair.getBasename(), type(err), str(err)))
                                return
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        """
                        Save
                        """
                        wait.setButtonVisibility(False)
                        if r is not None:
                            prefix = self._settings.getParameterValue('Prefix')
                            suffix = self._settings.getParameterValue('Suffix')
                            if prefix == '' and suffix == '': prefix = 'tissue_labels'
                            # 6 labels image
                            v = SisypheVolume()
                            v.copyFromNumpyArray(r['lbl'].astype('uint8'), spacing=t1.getSpacing(), defaultshape=False)
                            v.copyAttributesFrom(t1, display=False, slope=False)
                            v.acquisition.setModalityToLB()
                            v.setFilename(t1.getFilename())
                            v.setFilenamePrefix(prefix)
                            v.setFilenameSuffix(suffix)
                            # label rois
                            saveroi = self._settings.getParameterValue('SaveROI')
                            lbls = ('background', 'cerebro-spinal fluid', 'gray matter', 'white matter',
                                    'deep gray matter', 'brainstem', 'cerebellum')
                            lbls2 = ('', 'csf', 'gm', 'wm', 'scgm', 'bstem', 'crbl')
                            for j in range(len(lbls)):
                                v.acquisition.setLabel(j, lbls[j])
                                if saveroi and j > 0:
                                    roi = v.labelToROI(j)
                                    roi.setFilename(t1.getFilename())
                                    roi.setFilenameSuffix(lbls2[j])
                                    wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                                    roi.save()
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.save()
                            # brain mask
                            mask = v > 1
                            mask.acquisition.setModalityToOT()
                            mask.acquisition.setSequenceToMask()
                            mask.setFilename(t1.getFilename())
                            mask.setFilenamePrefix('brainmask')
                            wait.setInformationText('Save {}...'.format(mask.getBasename()))
                            mask.save()
                            # skull stripped
                            v2 = t1 * mask.cast(t1.getDatatype())
                            v2.copyAttributesFrom(t1)
                            v2.setFilename(t1.getFilename())
                            v2.setFilenamePrefix('brain')
                            wait.setInformationText('Save {}...'.format(v2.getBasename()))
                            v2.save()
                            # 3 labels image for cortical thickness processing
                            if prefix != '': prefix += '3'
                            elif suffix != '': suffix += '3'
                            img = v.getNumpy()
                            img[img == 4] = 3
                            img[img > 4] = 1
                            v.acquisition.setModalityToLB()
                            v.setFilename(t1.getFilename())
                            v.setFilenamePrefix(prefix)
                            v.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}...'.format(v.getBasename()))
                            v.acquisition.setLabel(4, '')
                            v.acquisition.setLabel(5, '')
                            v.acquisition.setLabel(6, '')
                            v.save()
                            # probability images
                            saveprb = self._settings.getParameterValue('SaveProbability')
                            if saveprb:
                                for j in range(len(r['prb'])):
                                    if j > 0:
                                        v2 = SisypheVolume()
                                        v2.copyFromNumpyArray(r['prb'][j], spacing=t1.getSpacing(), defaultshape=False)
                                        v2.copyAttributesFrom(t1, display=False, slope=False)
                                        v2.acquisition.setModalityToOT()
                                        v2.acquisition.setSequenceToStructMap()
                                        v2.setFilename(filename)
                                        v2.setFilenameSuffix(lbls2[j])
                                        wait.setInformationText('Save {}...'.format(v2.getBasename()))
                                        v2.save()
                    wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore tissue segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._volumeSelect.clear()
            else: self.accept()