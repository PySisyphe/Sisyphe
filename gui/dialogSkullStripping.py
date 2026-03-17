"""
External packages/modules
-------------------------

    - ANTsPyNet, Deep learning, https://github.com/ANTsX/ANTsPyNet
    - deepbrain, Deep learning skull stripping, https://pypi.org/project/deepbrain/
    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from Sisyphe.processing.capturedStdoutProcessing import ProcessSkullStrip
from Sisyphe.processing.capturedStdoutProcessing import ProcessDeepAtlasParcellation
from multiprocessing import Queue
from multiprocessing import Manager

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

    Last revision: 16/03/2026
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
        if data[:2] == 'T1':
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
            self._settings.getParameterWidget('TrainingData').setCurrentText('T1')
            # < Revision 16/03/2026
            self._settings.setParameterVisibility('ProbMask', True)
            self._settings.setParameterVisibility('ProbPrefix', True)
            self._settings.setParameterVisibility('ProbSuffix', True)
            # Revision 16/03/2026 >
        elif model == 'A':
            self._settings.setParameterVisibility('TrainingData', True)
            # < Revision 16/03/2026
            self._settings.setParameterVisibility('ProbMask', True)
            self._settings.setParameterVisibility('ProbPrefix', True)
            self._settings.setParameterVisibility('ProbSuffix', True)
            # Revision 16/03/2026 >
        # < Revision 16/03/2026
        elif model == 'O':
            self._settings.setParameterVisibility('TrainingData', False)
            self._settings.getParameterWidget('TrainingData').setCurrentText('T1')
            self._settings.setParameterVisibility('ProbMask', False)
            self._settings.setParameterVisibility('ProbPrefix', False)
            self._settings.setParameterVisibility('ProbSuffix', False)
        # Revision 16/03/2026 >
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
                try: self.function(filename, wait)
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
            wait.setInformationText('{} ANTs U-net Skull stripping...'.format(basename(filename)))
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
        elif model[0] == 'D':
            wait.setInformationText('{} DeepBrain U-net Skull stripping...'.format(basename(filename)))
            # shape x, y, z after transpose
            try: rimg = self._extractor.run(img.getNumpy()).T
            except: pass
        # OpenMAP
        # < Revision 16/03/2026
        elif model[0] == 'O':
            wait.setInformationText('{} OpenMAP Skull stripping...'.format(basename(filename)))
            wait.setButtonVisibility(True)
            with Manager() as manager:
                mng = manager.dict()
                queue = Queue()
                try:
                    extractor = ProcessDeepAtlasParcellation(img, False, mng, queue)
                    extractor.start()
                    while extractor.is_alive():
                        # noinspection PyTypeChecker
                        wait.messageFromDictProxyManager(mng)
                        if not queue.empty():
                            # noinspection PyUnusedLocal
                            r = queue.get()
                            if extractor.is_alive(): extractor.terminate()
                        if wait.getStopped(): extractor.terminate()
                except Exception as err:
                    if extractor.is_alive(): extractor.terminate()
                # noinspection PyUnreachableCode
                if wait.getStopped():
                    wait.close()
                    return
                if not wait.getStopped() and r is None:
                    wait.close()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='{} OpenMAP skull striping error: '
                                    '{}\n{}.'.format(img.getBasename(), type(err), str(err)))
                    return
            wait.setButtonVisibility(False)
            if r is not None:
                v = SisypheVolume()
                v.copyFromNumpyArray(r[1], spacing=img.getSpacing(), defaultshape=False)
                v.copyAttributesFrom(img, display=False, slope=False)
                v.setFilename(img.getFilename())
                v.setFilenamePrefix(prefix)
                v.setFilenameSuffix(prefix)
                wait.setInformationText('Save {}...'.format(v.getBasename()))
                v.save()
                mask = r[1] > 0
                mask = mask.astype(uint8)
                if savemask:
                    v = SisypheVolume()
                    v.copyFromNumpyArray(mask, spacing=img.getSpacing(), defaultshape=False)
                    v.copyAttributesFrom(img, display=False, slope=False)
                    v.setFilename(img.getFilename())
                    v.setFilenamePrefix(maskprefix)
                    v.setFilenameSuffix(masksuffix)
                    wait.setInformationText('Save {}...'.format(v.getBasename()))
                    v.save()
                if roimask:
                    roi = SisypheROI()
                    roi.copyFromNumpyArray(mask, spacing=img.getSpacing(), defaultshape=False)
                    roi.setName('Cerebrum')
                    roi.setReferenceID(img)
                    filename2 = addPrefixSuffixToFilename(img.getFilename(), maskprefix, masksuffix)
                    roi.saveAs(filename2)
            wait.close()
            return
        # Revision 16/03/2026 >
        if rimg is not None:
            mask = rimg > 0.5
            mask = mask.astype(uint8)
            # Save probability mask
            s = img.getSpacing()
            v = SisypheVolume()
            if probmask:
                filename2 = addPrefixSuffixToFilename(filename, probprefix, probsuffix)
                # < Revision 13/07/2025
                # v.copyFromNumpyArray(rimg, spacing=s)
                v.copyFromNumpyArray(rimg, spacing=s, defaultshape=False)
                # Revision 13/07/2025 >
                v.copyAttributesFrom(img, display=False, slope=False)
                v.acquisition.setModalityToOT()
                v.acquisition.setSequenceToDensityMap()
                v.acquisition.setNoUnit()
                wait.setInformationText('Save {}...'.format(basename(filename2)))
                v.saveAs(filename2)
            # Save mask
            if savemask:
                filename2 = addPrefixSuffixToFilename(filename, maskprefix, masksuffix)
                # < Revision 13/07/2025
                # v.copyFromNumpyArray(mask, spacing=s)
                v.copyFromNumpyArray(mask, spacing=s, defaultshape=False)
                # Revision 13/07/2025 >
                v.setID(img)
                v.acquisition.setSequenceToMask()
                wait.setInformationText('Save {}...'.format(basename(filename2)))
                v.saveAs(filename2)
            # Save mask as ROI
            if roimask:
                # < Revision 06/11/2025
                filename2 = addPrefixSuffixToFilename(filename, maskprefix, masksuffix)
                # Revision 06/11/2025 >
                roi = SisypheROI()
                # < Revision 06/11/2025
                # roi.copyFromNumpyArray(mask)
                roi.copyFromNumpyArray(mask, spacing=s, defaultshape=False)
                # Revision 06/11/2025 >
                roi.setName('Cerebrum')
                roi.setReferenceID(img)
                # < Revision 06/11/2025
                # roi.saveAs(filename2)
                roi.saveAs(filename2)
                # Revision 06/11/2025 >
            # Save brain extracted volume
            filename2 = addPrefixSuffixToFilename(filename, prefix, suffix)
            # shape x, y, z
            rimg = img.getNumpy(defaultshape=False) * mask
            rimg = rimg.astype(dtype(img.getDatatype()))
            v.copyFromNumpyArray(rimg, spacing=s, defaultshape=False)
            v.copyAttributesFrom(img)
            wait.setInformationText('Save {}...'.format(basename(filename2)))
            v.save(filename2)
