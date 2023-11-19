"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os.path import basename

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import DisplacementFieldJacobianDeterminantFilter

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QDialog -> DialogJacobian

"""


class DialogJacobian(QDialog):
    """
        DialogJacobian

        Description

            GUI dialog to calculate determinant
            of the Jacobian of a deformation field.

        Inheritance

            QDialog -> DialogJacobian

        Private attributes
        
            _fields     FilesSelectionWidget
            _settings

        Public methods

            execute()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Jacobian determinant of displacement field')

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self.setLayout(self._layout)

        # Init widgets
        
        self._fields = FilesSelectionWidget()
        self._fields.filterSisypheVolume()
        self._fields.filterDisplacementField()
        self._fields.setTextLabel('Displacement field(s)')
        self._fields.setCurrentVolumeButtonVisibility(True)
        self._fields.setMinimumWidth(500)
        self._layout.addWidget(self._fields)

        self._settings = FunctionSettingsWidget('DisplacementFieldJacobianDeterminant')
        self._settings.VisibilityToggled.connect(self._center)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Jacobian determinant calculation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)

        # Qt Signals

        cancel.clicked.connect(self.reject)
        self._execute.clicked.connect(self.execute)

    # Private method

    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()
        
    # Public methods

    def getSelectionWidget(self):
        return self._fields
    
    def execute(self):
        n = self._fields.filenamesCount()
        if n > 0:
            wait = DialogWait(title=self.windowTitle(), progressmin=0, progressmax=n, cancel=True, parent=None)
            if n > 1: wait.open()
            for filename in self._fields.getFilenames():
                wait.setInformationText('{} Jacobian determinant calculation...'.format(basename(filename)))
                wait.incCurrentProgressValue()
                v = SisypheVolume()
                v.load(filename)
                f = DisplacementFieldJacobianDeterminantFilter()
                img = None
                try:
                    img = f.Execute(v.getSITKImage())
                except Exception as err:
                    QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
                if wait.getStopped(): break
                if img is not None:
                    r = SisypheVolume()
                    r.setSITKImage(img)
                    r.setFilename(v.getFilename())
                    prefix = self._settings.getParameterValue('Prefix')
                    suffix = self._settings.getParameterValue('Suffix')
                    r.setFilenamePrefix(prefix)
                    r.setFilenameSuffix(suffix)
                    r.getAcquisition().setSequenceToAlgebraMap()  
                    r.setIdentity(v.getIdentity())
                    wait.setInformationText('Save {}'.format(r.getBasename()))
                    r.save()
                if wait.getStopped(): break
            wait.close()
            self._fields.clear()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from os import chdir

    chdir('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/REGISTRATION/REG2')
    app = QApplication(argv)
    main = DialogJacobian()
    main.exec()
