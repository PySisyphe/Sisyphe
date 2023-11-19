"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os import remove
from os.path import join
from os.path import exists

from multiprocessing import Process
from multiprocessing import Queue

from numpy import mean

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from ants.core import read_transform
from ants.core import write_transform
from ants.registration import registration

from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor
from SimpleITK import ResampleImageFilter
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        Process -> ProcessRegistration
        QDialog -> DialogEddyCurrentCorrection

"""


class ProcessRegistration(Process):
    """
        ProcessRegistration

        Description

            Multiprocessing Process class for ants registration function.

        Inheritance

            Process -> ProcessRegistration

        Private attributes

            _fixed      SisypheVolume
            _moving     SisypheVolume
            _mask       SisypheVolume
            _regtype    str
            _transform  SisypheTransform
            _verbose    bool
            _stdout     str
            _result     Queue

        Public methods

            run()       override

            inherited Process methods
    """

    # Special method

    def __init__(self, fixed, moving, mask, trf, queue):
        Process.__init__(self)
        self._fixed = fixed
        self._moving = moving
        self._mask = mask
        if trf is not None:
            trf = trf.getANTSTransform()
            self._transform = join(self._moving.getDirname(), 'temp.mat')
            write_transform(trf, self._transform)
        else: self._transform = None
        self._result = queue

    # Public methods

    def run(self):
        fixed = self._fixed.copyToANTSImage('float32')
        moving = self._moving.copyToANTSImage('float32')
        mask = self._mask.copyToANTSImage()
        """

            registration return
            r = {'warpedmovout': ANTsImage,
                 'warpedfixout': ANTsImage,
                 'fwdtransforms': str,
                 'invtransforms': str}

        """
        r = registration(fixed, moving, type_of_transform='BOLDAffine',
                         initial_transform=self._transform, mask=mask, verbose=False)
        if exists(self._transform): remove(self._transform)
        if len(r['fwdtransforms']) == 1:
            self._result.put(r['fwdtransforms'][0])  # Affine trf
            # Remove temporary ants inverse affine transform
            # bug temporary forward transform = inverse transform
            # if exists(r['invtransforms'][0]): remove(r['invtransforms'][0])


class DialogEddyCurrentCorrection(QDialog):
    """
        DialogEddyCurrentCorrection

        Description

            GUI dialog for eddy current correction,
            affine registration between DTI and B0 images.

        Inheritance

            QDialog -> DialogEddyCurrentCorrection

        Private attributes

            _b0select           FilesSelectionWidget
            _dwiselect          FilesSelectionWidget
            _wait               DialogWait
            _ref                LabeledComboBox
            _resamplesettings   FunctionSettingsWidget
            _execute            QPushButton

        Public methods

            FileSelectionWidget = getB0SelectionWidget()
            FilesSelectionWidget = getDWISelectionWidget()
            execute()

            inherited QDialog methods
    """

    @classmethod
    def calcMask(cls, vol, dilate=4):
        img = vol.getSITKImage()
        mask = img >= mean(vol.getNumpy().flatten())
        mask = BinaryDilate(mask, [dilate, dilate, dilate])
        mask = BinaryFillhole(mask)
        r = SisypheVolume()
        r.setSITKImage(mask)
        return r

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Eddy current correction')
        self.setFixedWidth(500)

        # Registration class

        self._wait = DialogWait(title=self.windowTitle(), parent=self)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._b0select = FileSelectionWidget()
        self._b0select.filterSisypheVolume()
        self._b0select.setTextLabel('B0 volume')
        self._b0select.setCurrentVolumeButtonVisibility(True)
        self._b0select.FieldChanged.connect(self._updateB0)

        self._dwiselect = FilesSelectionWidget()
        self._dwiselect.filterSisypheVolume()
        self._dwiselect.filterSameFOV()
        self._dwiselect.filterSameSequence('DWI')
        self._dwiselect.setTextLabel('DWI volumes')
        self._dwiselect.setMinimumWidth(500)
        self._dwiselect.setCurrentVolumeButtonVisibility(True)
        self._dwiselect.setEnabled(False)
        self._dwiselect.FilesSelectionChanged.connect(self._updateDWI)
        self._dwiselect.FilesSelectionWidgetCleared.connect(self._updateDWI)

        self._resamplesettings = FunctionSettingsWidget('Resample')
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(True)
        self._resamplesettings.setSettingsButtonFunctionText()

        self._layout.addWidget(self._b0select)
        self._layout.addWidget(self._dwiselect)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute eddy current correction')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        self._execute.setEnabled(False)
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

    def _updateB0(self):
        if self._b0select.isEmpty():
            self._dwiselect.clearall()
            self._dwiselect.setEnabled(False)
        else:
            self._dwiselect.setEnabled(True)
            v = SisypheVolume()
            v.load(self._b0select.getFilename())
            self._dwiselect.setReferenceVolume(v)

    def _updateDWI(self, widget):
        self._execute.setEnabled(self._dwiselect.filenamesCount() > 0)

    def _registration(self, fixed, moving, mask):
        queue = Queue()
        reg = ProcessRegistration(fixed, moving, mask, None, queue)
        try:
            reg.start()
            while reg.is_alive():
                QApplication.processEvents()
                if self._wait.getStopped(): reg.terminate()
        except Exception as err:
            if reg.is_alive(): reg.terminate()
            QMessageBox.warning(self, self.windowTitle(), '{}'.format(err))
        trf = None
        if not queue.empty():
            trfname = queue.get()
            if exists(trfname):
                trf = SisypheTransform()
                trf.setAttributesFromFixedVolume(fixed)
                trf.setANTSTransform(read_transform(trfname))
                remove(trfname)
        return trf

    # Public methods

    def getB0SelectionWidget(self):
        return self._b0select

    def getDWISelectionWidget(self):
        return self._dwiselect

    def execute(self):
        if self._dwiselect.filenamesCount() > 1:
            filename = self._b0select.getFilename()
            fixed = SisypheVolume()
            fixed.load(filename)
            mask = self.calcMask(fixed)
            filenames = self._dwiselect.getFilenames()
            n = len(filenames)
            self._wait.setProgressRange(0, n * 2)
            self._wait.setCurrentProgressValue(0)
            self._wait.buttonVisibilityOn()
            self._wait.open()
            for filename in filenames:
                self._wait.incCurrentProgressValue()
                self._wait.setInformationText('Eddy current correction, registration'
                                              'volume #{}/{}'.format(self._wait.getCurrentProgressValue(), n))
                moving = SisypheVolume()
                moving.load(filename)
                """

                    Registration

                """
                trf = self._registration(fixed, moving, mask)
                if self._wait.getStopped(): break
                """
    
                    Resample
    
                """
                self._wait.incCurrentProgressValue()
                self._wait.setInformationText('Eddy current correction, resample '
                                              'volume #{}/{}'.format(self._wait.getCurrentProgressValue(), n))
                f = ResampleImageFilter()
                f.SetReferenceImage(fixed.getSITKImage())
                interpol = self._resamplesettings.getParameterValue('Interpolator')
                if interpol == 'Nearest Neighbor': f.SetInterpolator(sitkNearestNeighbor)
                elif interpol == 'Linear': f.SetInterpolator(sitkLinear)
                elif interpol == 'Bspline': f.SetInterpolator(sitkBSpline)
                elif interpol == 'Gaussian': f.SetInterpolator(sitkGaussian)
                elif interpol == 'Hamming Sinc': f.SetInterpolator(sitkHammingWindowedSinc)
                elif interpol == 'Cosine Sinc': f.SetInterpolator(sitkCosineWindowedSinc)
                elif interpol == 'Welch Sinc': f.SetInterpolator(sitkWelchWindowedSinc)
                elif interpol == 'Lanczos Sinc': f.SetInterpolator(sitkLanczosWindowedSinc)
                elif interpol == 'Blackman Sinc': f.SetInterpolator(sitkBlackmanWindowedSinc)
                else: f.SetInterpolator(sitkLinear)
                prefix = self._resamplesettings.getParameterValue('Prefix')
                suffix = self._resamplesettings.getParameterValue('Suffix')
                if self._wait.getStopped(): break
                if not trf.isIdentity():
                    f.SetTransform(trf.getSITKTransform())
                    img = f.Execute(moving.getSITKImage())
                    moving.setSITKImage(img)
                moving.setFilenamePrefix(prefix)
                moving.setFilenameSuffix(suffix)
                moving.save()
            """

                Exit

            """
            self._wait.hide()
            if not self._wait.getStopped():
                r = QMessageBox.question(self, self.windowTitle(),
                                         'Do you want to make another eddy current correction ?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._select.clearall()
                else: self.accept()
            else: self.accept()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from os import chdir

    chdir('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/REGISTRATION')
    app = QApplication(argv)
    main = DialogEddyCurrentCorrection()
    main.exec()
