"""
    External packages/modules

        Name            Homepage link                                               Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.widgets.LUTWidgets import LutEditWidget

"""
    Class 
    
        DialogLutEdit
"""


class DialogLutEdit(QDialog):
    """
        DialogLutEdit class

        Inheritance

            QDialog -> DialogLutEdit

        Private attributes

            _lutwidget  LutEditWidget

        Public methods

            SisypheLut = getLut()

            inherited QDialog
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Edit Lut')
        self.setFixedWidth(512)
        self.setFixedHeight(96)

        self._lutwidget = LutEditWidget()
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
        layout.addWidget(save)
        layout.addStretch()

        self._layout.addWidget(self._lutwidget)
        self._layout.addLayout(layout)

        ok.clicked.connect(self.accept)
        save.clicked.connect(self._lutwidget.save)

    def getLut(self):
        return self._lutwidget.getSisypheLut()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogLutEdit()
    main.show()
    main.activateWindow()
    print(main.width(), main.height())
    app.exec_()
    exit()
