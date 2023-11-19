"""
    External packages/modules

        Name            Homepage link                                               Usage

        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os.path import exists
from os.path import basename

from SimpleITK import Flip as sitkFlip

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogFromXml import DialogFromXml

__all__ = ['DialogFlipAxes']

"""
    Class hierarchy

        QDialog -> DialogFromXml -> DialogFlipAxes
"""

class DialogFlipAxes(DialogFromXml):
    """
        DialogSwapAxes class

        Description

            GUI dialog window to flip volume axes

        Inheritance

            QDialog -> DialogFromXml -> DialogFlipAxes

        Private attributes

        Public methods


            inherited DialogFromXml methods
            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('Flip axes', 'FlipAxes', parent)

        widget = self.getFieldsWidget(0)
        self._files = widget.getParameterWidget('Volumes')
        self._flipx = widget.getParameterWidget('FlipX')
        self._flipy = widget.getParameterWidget('FlipY')
        self._flipz = widget.getParameterWidget('FlipZ')
        self._prefix = widget.getParameterWidget('Prefix')

    # Public method

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
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
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


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogFlipAxes()
    main.show()
    app.exec_()
