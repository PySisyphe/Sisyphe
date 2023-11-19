"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.core.sisypheVolume import SisypheVolume

"""
    Class 

        DialogLutSettings
"""


class DialogLutSettings(QDialog):
    """
        DialogLutSettings class

        Inheritance

            QDialog -> DialogLutSettings

        Private attributes

            _lutwidget  LutWidget

        Public methods

            setVolume(SisypheVolume)

            inherited QDialog
    """

    def __init__(self, volume=None, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Lut Settings')
        self.setFixedWidth(256)
        self.setFixedHeight(288)
        self._lutwidget = LutWidget(volume=volume, size=size)
        self._lutwidget.setContentsMargins(5, 5, 5, 5)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        save = QPushButton('Save')
        save.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addStretch()

        self._layout.addWidget(self._lutwidget)
        self._layout.addLayout(layout)

        ok.clicked.connect(self.accept)

    def setVolume(self, v):
        if isinstance(v, SisypheVolume):
            self._lutwidget.setVolume(v)
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    filename = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/tests/IMAGES/img.xvol'
    img = SisypheVolume()
    img.load(filename)
    main = DialogLutSettings()
    main.setVolume(img)
    main.show()
    main.activateWindow()
    print(main.width(), main.height())
    app.exec_()
    exit()
