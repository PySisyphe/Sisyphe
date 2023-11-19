"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.sliceViewFiducialBoxWidget import IconBarSliceViewFiducialBoxWidget

__all__ = ['DialogFiducialBox']

"""
    Class hierarchy

        QDialog -> DialogFiducialBox
"""


class DialogFiducialBox(QDialog):
    """
         DialogFiducialBox class

         Description

             Generic dialog box to display statistical results.

         Inheritance

             QDialog -> DialogFiducialBox

         Private attributes

            _view       IconBarSliceViewFiducialBoxWidget

         Public methods

            setVolume(SisypheVolume)    inherited from IconBarSliceViewFiducialBoxWidget

            inherited QDialog methods
     """

    # Special method

    def __init__(self, parent=None):

        super().__init__(parent)

        self._view = IconBarSliceViewFiducialBoxWidget(parent=self)

        # Inherited methods from SisypheFiducialBox class

        setattr(self, 'setVolume', self._view.setVolume)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        trf = QPushButton('Calc geometric transform')
        dlt = QPushButton('Remove current slice markers')
        dlt2 = QPushButton('Remove front plate markers')
        lyout.addWidget(ok)
        lyout.addWidget(cancel)
        lyout.addStretch()
        lyout.addWidget(trf)
        lyout.addWidget(dlt2)
        lyout.addWidget(dlt)

        trf.clicked.connect(self._calcTransform)
        dlt.clicked.connect(self._removeCurrentSliceMarkers)
        dlt2.clicked.connect(self._removeFrontPlateMarkers)
        ok.clicked.connect(self._accept)
        cancel.clicked.connect(self.reject)

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(5, 0, 0, 0)
        self._layout.addWidget(self._view)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

        # Window

        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        self.setWindowTitle('Stereotactic frame detection')
        self.setModal(True)

    # Private method

    def _accept(self):
        self._view.addTransformToVolume()
        self.accept()

    def _calcTransform(self):
        self._view.calcTransform()
        self._view.showErrorStatistics()

    def _removeCurrentSliceMarkers(self):
        self._view.removeCurrentSliceMarkers()
        self._calcTransform()

    def _removeFrontPlateMarkers(self):
        self._view.removeFrontPlateMarkers()
        self._calcTransform()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from Sisyphe.core.sisypheVolume import SisypheVolume

    app = QApplication(argv)
    vlm = SisypheVolume()
    vlm.load('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/STEREO/CTLEKSELL9.xvol')
    main = DialogFiducialBox()
    main.open()
    main.setVolume(vlm)
    exit(app.exec_())
