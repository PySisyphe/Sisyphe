"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            https://github.com/ANTsX/ANTsPy                             Image registration
        Matplotlib      https://matplotlib.org/                                     Plotting library
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os import remove
from os.path import join
from os.path import exists

from multiprocessing import Process
from multiprocessing import Queue

from matplotlib.ticker import MultipleLocator

from numpy import ndarray
from numpy import mean
from numpy import median

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
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

"""
    Class hierarchy

        Process -> ProcessRegistration
        QDialog -> DialogSeriesRealignment
        
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
        r = registration(fixed, moving, type_of_transform='BOLDRigid',
                         initial_transform=self._transform, mask=mask, verbose=False)
        if self._transform is not None:
            if exists(self._transform): remove(self._transform)
        if len(r['fwdtransforms']) == 1:
            self._result.put(r['fwdtransforms'][0])  # Affine trf
            # Remove temporary ants inverse affine transform
            # bug temporary forward transform = inverse transform
            # if exists(r['invtransforms'][0]): remove(r['invtransforms'][0])

    def terminate(self):
        if exists(self._transform): remove(self._transform)
        super().terminate()


class DialogSeriesRealignment(QDialog):
    """
        DialogSeriesRealignment

        Description

            GUI dialog for time series realignment.

        Inheritance

            QDialog -> DialogSeriesRealignment

        Private attributes

            _trfs               list of SisypheTransform
            _select             FilesSelectionWidget
            _wait               DialogWait
            _ref                LabeledComboBox
            _resamplesettings   FunctionSettingsWidget
            _execute            QPushButton

        Public methods

            FileSelectionWidget = getSelectionWidget()
            execute()

            inherited QDialog methods
    """

    # Class method

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

        self.setWindowTitle('Time series realignment')
        self.setFixedWidth(500)

        # Registration class

        self._trfs = list()
        self._wait = DialogWait(title=self.windowTitle(), parent=self)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._select = FilesSelectionWidget()
        self._select.filterSisypheVolume()
        self._select.setReferenceVolumeToFirst()
        self._select.filterSameFOV()
        self._select.setTextLabel('Time series volumes')
        self._select.setMinimumWidth(500)
        self._select.setCurrentVolumeButtonVisibility(True)
        self._select.FilesSelectionChanged.connect(self._updateFixed)
        self._select.FilesSelectionWidgetCleared.connect(self._updateFixed)

        settings = SisypheFunctionsSettings()
        n = settings.getFieldValue('Realignment', 'Reference')
        if n is None: n = 0
        else:
            ch = n[0][:3]
            if ch == 'Fir': n = 0
            elif ch == 'Mid': n = 1
            elif ch == 'Mea': n = 2
            elif ch == 'Med': n = 3
            else: n = 0

        lyout = QHBoxLayout()
        self._ref = LabeledComboBox()
        self._ref.setTitle('Resample to')
        self._ref.addItem('First volume')
        self._ref.addItem('Middle volume')
        self._ref.addItem('Mean transformation')
        self._ref.addItem('Median transformation')
        self._ref.setCurrentIndex(n)
        lyout.addStretch()
        lyout.addWidget(self._ref)
        lyout.addStretch()

        self._resamplesettings = FunctionSettingsWidget('Resample')
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(True)
        self._resamplesettings.setSettingsButtonFunctionText()

        self._layout.addWidget(self._select)
        self._layout.addLayout(lyout)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedSize(QSize(120, 32))
        self._execute.setToolTip('Execute time series realignment.')
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

    def _updateFixed(self, widget):
        self._execute.setEnabled(self._select.filenamesCount() > 0)

    def _registration(self, fixed, moving, mask, trf):
        queue = Queue()
        reg = ProcessRegistration(fixed, moving, mask, trf, queue)
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

    # Public method

    def getSelectionWidget(self):
        return self._select

    def execute(self):
        if self._select.filenamesCount() > 1:
            filenames = self._select.getFilenames()
            fixed = SisypheVolume()
            fixed.load(filenames[0])
            filenames.pop(0)
            mask = self.calcMask(fixed)
            trfs = list()
            n = len(filenames)
            self._wait.setProgressRange(0, n)
            self._wait.setCurrentProgressValue(0)
            self._wait.buttonVisibilityOn()
            self._wait.open()
            """
            
                Registration
            
            """
            trf = None
            for filename in filenames:
                self._wait.incCurrentProgressValue()
                self._wait.setInformationText('Time series realignment, '
                                              'volume #{}/{}'.format(self._wait.getCurrentProgressValue(), n))
                moving = SisypheVolume()
                moving.load(filename)
                trf = self._registration(fixed, moving, mask, trf)
                if trf is not None: trfs.append(trf)
                if self._wait.getStopped(): break
            """
            
                Reference transformation:
                    Transformation of the middle volume of the series to the first
                    Mean transformation of the series
                    Median transformation of the series
            
            """
            if not self._wait.getStopped():
                ref = self._ref.currentIndex()
                reftrf = None
                if ref == 1:  # Middle volume
                    reftrf = trfs[n // 2].copy()
                elif ref in (2, 3):
                    l = ndarray(shape=(6, n), dtype=float)
                    for i in range(n):
                        l[0:3, i] = trfs[i].getTranslations()
                        l[3:6, i] = trfs[i].getRotationsFromMatrix()
                    reftrf = SisypheTransform()
                    reftrf.setAttributesFromFixedVolume(fixed)
                    # Mean transformation
                    if ref == 2:
                        p = mean(l, axis=1)
                        reftrf.setTranslations(p[0:3])
                        reftrf.setRotations(p[3:6])
                    # Median transformation
                    else:
                        p = median(l, axis=1)
                        reftrf.setTranslations(p[0:3])
                        reftrf.setRotations(p[3:6])
                if reftrf is not None:
                    reftrf = reftrf.getInverseTransform()
                    # Pre-multiply each trf with reference reftrf
                    # Pre-multiply = order of transformations 1. trfs[i] then 2. reftrf
                    for i in range(n):
                        trfs[i].preMultiply(reftrf, homogeneous=True)
                    trfs.insert(0, reftrf)
                else:
                    trf = SisypheTransform()
                    trf.setIdentity()
                    trf.setAttributesFromFixedVolume(fixed)
                    trfs.insert(0, trf)
            """
            
                Resample
                
            """
            if not self._wait.getStopped():
                self._wait.setCurrentProgressValue(1)
                filenames = self._select.getFilenames()
                n = len(filenames)
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
                self._wait.setCurrentProgressValue(0)
                for i in range(n):
                    self._wait.setInformationText('Resample time series, '
                                                  'volume #{}/{}'.format(i+1, n))
                    self._wait.incCurrentProgressValue()
                    if self._wait.getStopped(): break
                    filename = filenames[i]
                    vol = SisypheVolume()
                    vol.load(filename)
                    if not trfs[i].isIdentity():
                        f.SetTransform(trfs[i].getSITKTransform())
                        img = f.Execute(vol.getSITKImage())
                        vol.setSITKImage(img)
                    vol.setFilenamePrefix(prefix)
                    vol.setFilenameSuffix(suffix)
                    vol.save()
            """
            
                Display result
            
            """
            self._wait.hide()
            if not self._wait.getStopped():
                dialog = DialogGenericResults(parent=self)
                dialog.setWindowTitle('Realignment result')
                dialog.newTab(title='Rigid parameters')
                dialog.setTreeWidgetHeaderLabels(0, ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz'])
                l = ndarray(shape=(6, n), dtype=float)
                for i in range(n):
                    l[0:3, i] = trfs[i].getTranslations()
                    l[3:6, i] = trfs[i].getRotationsFromMatrix(deg=True)
                for i in range(n):
                    v = l[:, i]
                    dialog.addTreeWidgetRow(0, row=v, d=2)
                fig = dialog.getFigure(0)
                ax = fig.add_subplot(111)
                ax.plot(l[0, :], label='Tx (mm)')
                ax.plot(l[1, :], label='Ty (mm')
                ax.plot(l[2, :], label='Tz (mm)')
                ax.plot(l[3, :], label='Rx (°)')
                ax.plot(l[4, :], label='Ry (°)')
                ax.plot(l[5, :], label='Rz (°)')
                ax.set_xlabel('Series volumes')
                ax.set_ylabel('mm / degrees')
                ax.xaxis.set_major_locator(MultipleLocator(1))
                ax.legend()
                dialog.exec()
            """
    
                Exit
    
            """
            if not self._wait.getStopped():
                r = QMessageBox.question(self, self.windowTitle(),
                                         'Do you want to make another realignment ?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r == QMessageBox.Yes: self._select.clearall()
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
    main = DialogSeriesRealignment()
    main.exec()
