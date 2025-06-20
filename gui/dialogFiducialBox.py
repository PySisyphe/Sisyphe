"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
from Sisyphe.widgets.sliceViewFiducialBoxWidget import IconBarSliceViewFiducialBoxWidget

__all__ = ['DialogFiducialBox']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogFiducialBox
"""


class DialogFiducialBox(QDialog):
    """
    DialogFiducialBox class

    Description
    ~~~~~~~~~~~

    Generic dialog box to display statistical results.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogFiducialBox

    Last revision: 08/03/2025
    """

    # Special method

    """
    Private attributes

    _view       IconBarSliceViewFiducialBoxWidget
    """

    def __init__(self, fid=SisypheFiducialBox, parent=None):

        super().__init__(parent)

        self.setWindowTitle('Stereotactic frame detection')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        if isinstance(fid, SisypheFiducialBox):
            self._view = IconBarSliceViewFiducialBoxWidget(fid, parent=self)
        else: raise ValueError('No SisypheFiducialBox.')

        setattr(self, 'showErrorStatistics', self._view.showErrorStatistics)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        else: lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        error = QPushButton('Error statistics')
        trf = QPushButton('Calc geometric transform')
        dlt = QPushButton('Remove current slice markers')
        dlt2 = QPushButton('Remove front plate markers')
        lyout.addWidget(ok)
        lyout.addWidget(cancel)
        lyout.addStretch()
        lyout.addWidget(error)
        lyout.addWidget(trf)
        lyout.addWidget(dlt2)
        lyout.addWidget(dlt)

        # noinspection PyUnresolvedReferences
        error.clicked.connect(self.showErrorStatistics)
        # noinspection PyUnresolvedReferences
        trf.clicked.connect(self._calcTransform)
        # noinspection PyUnresolvedReferences
        dlt.clicked.connect(self._removeCurrentSliceMarkers)
        # noinspection PyUnresolvedReferences
        dlt2.clicked.connect(self._removeFrontPlateMarkers)
        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        self.accepted.connect(self._view.addTransformToVolume)
        self.rejected.connect(self._view.removeTransformFromVolume)

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(5, 0, 0, 0)
        self._layout.addWidget(self._view)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

        self.setModal(True)

    # Private method

    def _calcTransform(self):
        self._view.calcTransform()
        self._view.showErrorStatistics()

    def _removeCurrentSliceMarkers(self):
        self._view.removeCurrentSliceMarkers()
        self._calcTransform()

    def _removeFrontPlateMarkers(self):
        self._view.removeFrontPlateMarkers()
        self._calcTransform()

    # Qt event

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            if self._view is not None:
                self._view.finalize()
        # Revision 10/03/2025 >
