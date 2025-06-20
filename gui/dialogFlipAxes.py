"""
External packages/modules
-------------------------

    - SimpleITK, Medical image processing, https://simpleitk.org/
"""

from os.path import exists
from os.path import basename

from PyQt5.QtWidgets import QApplication

from SimpleITK import Flip as sitkFlip

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogFromXml import DialogFromXml

__all__ = ['DialogFlipAxes']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogFromXml -> DialogFlipAxes
"""

class DialogFlipAxes(DialogFromXml):
    """
    DialogSwapAxes class

    Description
    ~~~~~~~~~~~

    GUI dialog window to flip volume axes.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogFromXml -> DialogFlipAxes

    Last revision: 13/02/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('Flip axes', 'FlipAxes', parent)

        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        widget = self.getFieldsWidget(0)
        self._files = widget.getParameterWidget('Volumes')
        self._flipx = widget.getParameterWidget('FlipX')
        self._flipy = widget.getParameterWidget('FlipY')
        self._flipz = widget.getParameterWidget('FlipZ')
        self._prefix = widget.getParameterWidget('Prefix')

    # Public method

    # < Revision 13/02/2025
    def setFilenames(self, filenames: str | list[str]):
        if isinstance(filenames, str): filenames = [filenames]
        self._files.add(filenames)
    # Revision 13/02/2025 >

    def getFilenames(self) -> list[str]:
        return self._files.getFilenames()

    # < Revision 13/02/2025
    def getParametersDict(self) -> dict:
        params = dict()
        params['FlipX'] = self._flipx.isChecked()
        params['FlipY'] = self._flipy.isChecked()
        params['FlipZ'] = self._flipz.isChecked()
        params['Prefix'] = self._prefix.text()
        return params
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    def setParametersFromDict(self, params: dict):
        if len(params) > 0:
            p = ['FlipX', 'FlipY', 'FlipZ', 'Prefix']
            widget = self.getFieldsWidget(0)
            for k in list(params.keys()):
                if k in p: widget.setParameterValue(k, params[k])
    # Revision 13/02/2025 >

    def accept(self):
        axes = [self._flipx.isChecked(),
                self._flipy.isChecked(),
                self._flipz.isChecked()]
        files = self._files.getFilenames()
        n = len(files)
        if files is not None and n > 0:
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Flip axes', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            for file in files:
                if exists(file):
                    wait.setInformationText('Flip {} axes...'.format(basename(file)))
                    v = SisypheVolume()
                    v.load(file)
                    img = sitkFlip(v.getSITKImage(), axes)
                    v.setSITKImage(img)
                    v.setFilenamePrefix(self._prefix.text())
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
        super().accept()
