"""
    External packages/modules

        Name            Link                                                        Usage

        deepbrain       https://pypi.org/project/deepbrain/                         Deep learning skull stripping
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import join
from os.path import split
from os.path import splitext
from os.path import basename

from numpy import uint8
from numpy import dtype

from PyQt5.QtWidgets import QMessageBox

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogFunction import AbstractDialogFunction

"""
    Class hierarchy
    
        QDialog -> AbstractDialogFunction -> DialogSkullStripping
"""

class DialogSkullStripping(AbstractDialogFunction):
    """
        DialogSkullStripping

        Description

            GUI dialog window class for skull stripping.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogSkullStripping

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('SkullStripping', parent)
        self._settings.settingsVisibilityOn()
        self._extractor = None

    # Public method

    def execute(self):
        if self.getNumberOfFilenames() > 0:
            wait = DialogWait(title=self._funcname, cancel=True, parent=self)
            wait.open()
            wait.buttonVisibilityOff()
            wait.setInformationText('Load deep learning model...')
            from deepbrain import Extractor
            wait.buttonVisibilityOn()
            self._extractor = Extractor()
            for filename in self.getFilenames():
                try:
                    self.function(filename, wait)
                    if wait.getStopped():
                        wait.resetStopped()
                        break
                except Exception as err:
                    QMessageBox.warning(self, self._funcname, '{} error: {}.'.format(basename(filename), type(err)))
                    break
            wait.close()
            self._files.clearall()

    def function(self, filename, wait):
        wait.setProgressVisibility(False)
        wait.setInformationText('{} {}'.format(basename(filename), 'Skull stripping'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        model = self.getParameterValue(params[0])[0]
        savemask = self.getParameterValue(params[1])
        roimask = self.getParameterValue(params[2])
        maskprefix = self.getParameterValue(params[3])
        saveprob = self.getParameterValue(params[4])
        probprefix = self.getParameterValue(params[5])
        prefix = self.getParameterValue(params[6])
        suffix = self.getParameterValue(params[7])

        # if model[0] == 'D':  # DeepBrain U-net
        rimg = self._extractor.run(img.getNumpy())
        mask = rimg > 0.5
        mask = mask.astype(uint8)
        # else:  # ANTs U-net
        #    pass

        # Save probability
        s = img.getSpacing()
        path, name = split(filename)
        name, ext = splitext(name)
        v = SisypheVolume()
        if saveprob:
            filename = join(path, probprefix + name + ext)
            v.copyFromNumpyArray(rimg, spacing=s)
            v.copyAttributesFrom(img, display=False, slope=False)
            v.acquisition.setModalityToOT()
            v.acquisition.setSequenceToDensityMap()
            v.acquisition.setNoUnit()
            v.saveAs(filename)
        # Save mask
        if savemask:
            filename = join(path, maskprefix + name + ext)
            v.copyFromNumpyArray(mask, spacing=s)
            v.setID(img)
            v.acquisition.setSequenceToMask()
            v.saveAs(filename)
        # Save mask as ROI
        if roimask:
            roi = SisypheROI()
            roi.copyFromNumpyArray(mask)
            roi.setName('Brain')
            roi.setReferenceID(img)
            roi.saveAs(filename)
        # Save brain extracted volume
        filename = join(path, prefix + name + suffix + ext)
        rimg = img.getNumpy() * mask
        rimg = rimg.astype(dtype(img.getDatatype()))
        v.copyFromNumpyArray(rimg, spacing=s)
        v.copyAttributesFrom(img)
        v.save(filename)
