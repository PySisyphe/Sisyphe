"""
External packages/modules
-------------------------

    - ANTsPyNet, Deep learning, https://github.com/ANTsX/ANTsPyNet
    - deepbrain, Deep learning skull stripping, https://pypi.org/project/deepbrain/
    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from Sisyphe.processing.capturedStdoutProcessing import ProcessSkullStrip
from multiprocessing import Queue

from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import basename

from numpy import uint8
from numpy import dtype

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheConstants import addPrefixSuffixToFilename
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogFunction import AbstractDialogFunction
from Sisyphe.widgets.basicWidgets import messageBox

__all__ = ['DialogSkullStripping']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QDialog -> AbstractDialogFunction -> DialogSkullStripping
"""

class DialogSkullStripping(AbstractDialogFunction):
    """
    DialogSkullStripping

    Description
    ~~~~~~~~~~~

    GUI dialog window class for skull stripping.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogSkullStripping

    Last revision: 11/10/2024
    """

    # Class method

    @classmethod
    def _getAntspynetCacheDirectory(cls) -> str:
        import Sisyphe
        path = join(dirname(abspath(Sisyphe.__file__)), 'templates', 'ANTSPYNET')
        return path

    # Special method

    def __init__(self, parent=None):
        super().__init__('SkullStripping', parent)
        self._settings.settingsVisibilityOn()

        self._modality = 't1'
        self._extractor = None

        data = self._settings.getParameterWidget('TrainingData')
        data.currentTextChanged.connect(self._dataChanged)

        model = self._settings.getParameterWidget('Model')
        self._modelChanged()
        model.currentTextChanged.connect(self._modelChanged)

    # Private method

    def _dataChanged(self):
        data = self._settings.getParameterValue('TrainingData')[0]
        if data == 'T1':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.T1)
            if data == 'T1 FreeSurfer': self._modality = 't1nobrainer'
            elif data == 'T1 ANTs/FreeSurfer': self._modality = 't1combined'
            else: self._modality = 't1'
        elif data == 'T2':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.T2)
            self._modality = 't2'
        elif data == 'FLAIR':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.FLAIR)
            self._modality = 'flair'
        elif data == 'T2*':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.T2S)
            self._modality = 't2star'
        elif data == 'EPI':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.EPI)
            self._modality = 'bold'
        elif data == 'FA':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.FA)
            self._modality = 'fa'
        elif data == 'TOF':
            if not self._files.isEmpty(): self._files.clearall()
            self._files.filterSameSequence(SisypheAcquisition.TOF)
            self._modality = 'mra'
        else: raise ValueError('Invalid TrainingData parameter {}.'.format(data))

    def _modelChanged(self):
        model = self._settings.getParameterValue('Model')[0][0]
        if model == 'D':
            self._settings.setParameterVisibility('TrainingData', False)
            self._settings.getParameterWidget('TrainingData').setCurrentText('T1 ANTs')
        else:
            self._settings.setParameterVisibility('TrainingData', True)
        if not self._files.isEmpty(): self._files.clearall()

    # Public method

    def execute(self):
        if self.getNumberOfFilenames() > 0:
            wait = DialogWait(title=self._funcname)
            wait.open()
            model = self.getParameterValue('Model')[0]
            if model[0] == 'D':
                wait.setInformationText('TensorFlow initialization...')
                from Sisyphe.lib.db.extractor import Extractor
                self._extractor = Extractor()
            for filename in self.getFilenames():
                try:
                    self.function(filename, wait)
                except Exception as err:
                    messageBox(self,
                               title=self._funcname,
                               text='{} error in skull stripping: '
                                    '{}\n{}.'.format(basename(filename), type(err), str(err)))
                    break
            wait.close()
            self._files.clearall()

    def function(self, filename, wait):
        rimg = None
        img = SisypheVolume()
        img.load(filename)
        model = self.getParameterValue('Model')[0]
        savemask = self.getParameterValue('Mask')
        roimask = self.getParameterValue('ROIMask')
        maskprefix = self.getParameterValue('MaskPrefix')
        masksuffix = self.getParameterValue('MaskSuffix')
        probmask = self.getParameterValue('ProbMask')
        probprefix = self.getParameterValue('ProbPrefix')
        probsuffix = self.getParameterValue('ProbSuffix')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')
        # ANTs U-net
        if model[0] == 'A':
            wait.setInformationText('{} {}'.format(basename(filename), 'ANTs U-net {} Skull stripping...'))
            wait.setButtonVisibility(True)
            queue = Queue()
            extractor = ProcessSkullStrip(img, self._modality, self._getAntspynetCacheDirectory(), queue)
            extractor.start()
            while extractor.is_alive():
                if not queue.empty():
                    rimg = queue.get()
                    extractor.terminate()
                if wait.getStopped(): extractor.terminate()
            wait.setButtonVisibility(False)
        # DeepBrain U-net
        else:
            wait.setInformationText('{} {}'.format(basename(filename), 'DeepBrain U-net Skull stripping...'))
            # shape x, y, z after transpose
            try: rimg = self._extractor.run(img.getNumpy()).T
            except: pass
        if rimg is not None:
            mask = rimg > 0.5
            mask = mask.astype(uint8)
            # Save probability mask
            s = img.getSpacing()
            v = SisypheVolume()
            if probmask:
                filename2 = addPrefixSuffixToFilename(filename, probprefix, probsuffix)
                v.copyFromNumpyArray(rimg, spacing=s)
                v.copyAttributesFrom(img, display=False, slope=False)
                v.acquisition.setModalityToOT()
                v.acquisition.setSequenceToDensityMap()
                v.acquisition.setNoUnit()
                wait.setInformationText('Save {}...'.format(basename(filename2)))
                v.saveAs(filename2)
            # Save mask
            if savemask:
                filename2 = addPrefixSuffixToFilename(filename, maskprefix, masksuffix)
                v.copyFromNumpyArray(mask, spacing=s)
                v.setID(img)
                v.acquisition.setSequenceToMask()
                wait.setInformationText('Save {}...'.format(basename(filename2)))
                v.saveAs(filename2)
            # Save mask as ROI
            if roimask:
                roi = SisypheROI()
                roi.copyFromNumpyArray(mask)
                roi.setName('Cerebrum')
                roi.setReferenceID(img)
                roi.saveAs(filename)
            # Save brain extracted volume
            filename2 = addPrefixSuffixToFilename(filename, prefix, suffix)
            # shape x, y, z
            rimg = img.getNumpy(defaultshape=False) * mask
            rimg = rimg.astype(dtype(img.getDatatype()))
            v.copyFromNumpyArray(rimg, spacing=s, defaultshape=False)
            v.copyAttributesFrom(img)
            wait.setInformationText('Save {}...'.format(basename(filename2)))
            v.save(filename2)
