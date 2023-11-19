"""
    External packages/modules

        Name            Homepage link                                               Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.widgets.LUTWidgets import TransferWidget
from Sisyphe.core.sisypheVolume import SisypheVolume

"""
    Class 

        DialogTransferSettings
"""

class DialogTransferSettings(QDialog):
    """
        DialogTransferSettings class

        Inheritance

            QDialog -> DialogTransferSettings

        Private attributes

            _lutwidget  LutWidget

        Public methods

            setVolume(SisypheVolume)

            inherited QDialog
    """

    def __init__(self, volume=None, transfer=None, gradient=True, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Transfer Settings')
        # self.setFixedWidth(256)
        # self.setFixedHeight(288)
        self._transferwidget = TransferWidget(volume=volume, transfer=transfer, gradient=gradient, size=size)
        self._transferwidget.setContentsMargins(5, 5, 5, 5)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        load = QPushButton('Load')
        load.setFixedWidth(75)
        save = QPushButton('Save')
        save.setFixedWidth(75)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(save)
        layout.addWidget(load)
        layout.addStretch()

        self._layout.addWidget(self._transferwidget)
        self._layout.addLayout(layout)

        ok.clicked.connect(self.accept)
        load.clicked.connect(self._transferwidget.load)
        save.clicked.connect(self._transferwidget.save)

    def setVolume(self, v):
        if isinstance(v, SisypheVolume):
            self._transferwidget.setVolume(v)
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
    main = DialogTransferSettings(volume=img)
    main.show()
    main.activateWindow()
    print(main.width(), main.height())
    app.exec_()
    exit()
