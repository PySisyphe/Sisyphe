"""
External packages/modules
-------------------------

    - ANTs, image registration, https://github.com/ANTsX/ANTsPy
    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import remove
from os.path import exists

from Sisyphe.processing.capturedStdoutProcessing import ProcessRealignment
from multiprocessing import Value
from multiprocessing import Queue

from matplotlib.ticker import MultipleLocator

from numpy import ndarray
from numpy import mean
from numpy import median

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from ants.core import read_transform

from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['DialogSeriesRealignment']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogSeriesRealignment
        
"""

class DialogSeriesRealignment(QDialog):
    """
    DialogSeriesRealignment

    Description
    ~~~~~~~~~~~

    GUI dialog for time series realignment.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesRealignment
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

    """
    Private attributes

    _trfs               list of SisypheTransform
    _select             FilesSelectionWidget
    _wait               DialogWait
    _ref                LabeledComboBox
    _resamplesettings   FunctionSettingsWidget
    _execute            QPushButton
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Time series realignment')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Registration class

        self._trfs = list()
        self._wait = DialogWait()

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
        self._select.setCurrentVolumeButtonVisibility(True)
        self._select.FilesSelectionChanged.connect(self._updateFixed)
        self._select.FilesSelectionWidgetCleared.connect(self._updateFixed)

        self._settings = FunctionSettingsWidget('Realignment')
        self._settings.VisibilityToggled.connect(self._center)

        self._resamplesettings = FunctionSettingsWidget('Resample')
        self._resamplesettings.hideIOButtons()
        self._resamplesettings.setParameterVisibility('Dialog', False)
        self._resamplesettings.getParameterWidget('Dialog').setCheckState(Qt.Unchecked)
        self._resamplesettings.setParameterVisibility('NormalizationPrefix', False)
        self._resamplesettings.setParameterVisibility('NormalizationSuffix', False)
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(True)
        self._resamplesettings.setSettingsButtonFunctionText()

        self._layout.addWidget(self._select)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Start series realignment.')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # noinspection PyUnusedLocal
    def _updateFixed(self, widget):
        self._execute.setEnabled(self._select.filenamesCount() > 0)

    def _registration(self, vols, mask):
        queue = Queue()
        previous = 0
        progress = Value('i', 0)
        v = self._settings.getParameterValue('Metric')[0]
        if v == 'MS': metric = 'meansquares'
        elif v == 'IM': metric = 'mattes'
        elif v == 'CC': metric = v
        else: raise ValueError('Invalid metric parameter {}.'.format(v))
        sampling = self._settings.getParameterValue('SamplingRate')
        self._wait.buttonVisibilityOff()
        self._wait.setInformationText('Registration initialization...')
        reg = ProcessRealignment(vols, mask, metric, sampling, progress, queue)
        try:
            reg.start()
            self._wait.setInformationText('Time series realignment...')
            self._wait.setProgressRange(0, vols.count() - 1)
            self._wait.progressVisibilityOn()
            self._wait.buttonVisibilityOn()
            while reg.is_alive():
                QApplication.processEvents()
                if progress.value != previous:
                    self._wait.setCurrentProgressValue(progress.value)
                    previous = progress.value
                if self._wait.getStopped():
                    reg.terminate()
                    self._wait.hide()
                    messageBox(self, title=self.windowTitle(), text='Realignment interrupted.')
                    return None
        except Exception as err:
            if reg.is_alive(): reg.terminate()
            self._wait.hide()
            messageBox(self,title=self.windowTitle(), text='{}'.format(err))
            return None
        trfs = list()
        if not queue.empty():
            i = 0
            while not queue.empty():
                i += 1
                trf = SisypheTransform()
                trf.setAttributesFromFixedVolume(vols[0])
                name = queue.get()
                if name is not None:
                    trf.setANTSTransform(read_transform(name))
                    trf = trf.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                    trfs.append(trf)
                    remove(name)
        return trfs

    # Public methods

    def getSelectionWidget(self):
        return self._select

    def execute(self):
        if self._select.filenamesCount() > 1:
            self._wait.open()
            """
            Open series volumes
            """
            filenames = self._select.getFilenames()
            self._wait.setInformationText('Open series volumes...')
            self._wait.buttonVisibilityOn()
            vols = SisypheVolumeCollection()
            for filename in filenames:
                if exists(filename):
                    vols.load(filename)
                    if self._wait.getStopped():
                        self._wait.hide()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Realignment interrupted.',
                                   icon=QMessageBox.Information)
                        return
            """
            Mask
            """
            self._wait.setInformationText('Calc mask...')
            mask = self.calcMask(vols[0])
            if self._wait.getStopped():
                self._wait.hide()
                messageBox(self,
                           title=self.windowTitle(),
                           text='Realignment interrupted.',
                           icon=QMessageBox.Information)
                return
            """
            Registration  
            """
            trfs = self._registration(vols, mask)
            if trfs is not None and len(trfs) != vols.count() - 1:
                self._wait.hide()
                messageBox(self, title=self.windowTitle(), text='Invalid registration count.')
                self._select.clearall()
                return
            """      
            Reference volume:
            - first volume
            - middle volume
            - mean transformation
            - median transformation  
            """
            if trfs is not None and len(trfs) > 0:
                ref = self._settings.getParameterValue('Reference')[0]
                reftrf = None
                if ref == 'Middle':  # Middle volume
                    reftrf = trfs[len(trfs) // 2].copy()
                elif ref in (2, 3):
                    l = ndarray(shape=(6, len(trfs)), dtype=float)
                    for i in range(len(trfs)):
                        l[0:3, i] = trfs[i].getTranslations()
                        l[3:6, i] = trfs[i].getRotationsFromMatrix()
                    reftrf = SisypheTransform()
                    reftrf.setAttributesFromFixedVolume(vols[0])
                    # Mean transformation
                    if ref == 'Mean':
                        p = mean(l, axis=1)
                        reftrf.setTranslations(p[0:3])
                        reftrf.setRotations(p[3:6])
                    # Median transformation
                    elif ref == 'Median':
                        p = median(l, axis=1)
                        reftrf.setTranslations(p[0:3])
                        reftrf.setRotations(p[3:6])
                    else: raise ValueError('Invalid reference {}.'.format(ref))
                if reftrf is not None:
                    reftrf = reftrf.getInverseTransform()
                    # Pre-multiply each trf with reference reftrf
                    # Pre-multiply, order of transformations: 1. trfs[i] then 2. reftrf
                    for i in range(len(trfs)):
                        trfs[i].preMultiply(reftrf, homogeneous=True)
                    trfs.insert(0, reftrf)
                else:
                    trf = SisypheTransform()
                    trf.setIdentity()
                    trf.setAttributesFromFixedVolume(vols[0])
                    trfs.insert(0, trf)
            """
            Resample        
            """
            if trfs is not None and len(trfs) > 0:
                self._wait.buttonVisibilityOn()
                self._wait.setProgressRange(0, len(trfs))
                self._wait.setCurrentProgressValue(0)
                f = SisypheApplyTransform()
                interpol = self._resamplesettings.getParameterValue('Interpolator')
                if interpol == 'Nearest Neighbor': f.setInterpolator(sitkNearestNeighbor)
                elif interpol == 'Linear': f.setInterpolator(sitkLinear)
                elif interpol == 'Bspline': f.setInterpolator(sitkBSpline)
                elif interpol == 'Gaussian': f.setInterpolator(sitkGaussian)
                elif interpol == 'Hamming Sinc': f.setInterpolator(sitkHammingWindowedSinc)
                elif interpol == 'Cosine Sinc': f.setInterpolator(sitkCosineWindowedSinc)
                elif interpol == 'Welch Sinc': f.setInterpolator(sitkWelchWindowedSinc)
                elif interpol == 'Lanczos Sinc': f.setInterpolator(sitkLanczosWindowedSinc)
                elif interpol == 'Blackman Sinc': f.setInterpolator(sitkBlackmanWindowedSinc)
                else: f.setInterpolator(sitkLinear)
                prefix = self._resamplesettings.getParameterValue('Prefix')
                suffix = self._resamplesettings.getParameterValue('Suffix')
                refid = None
                for i in range(len(trfs)):
                    self._wait.setInformationText('Resample time series...')
                    self._wait.incCurrentProgressValue()
                    if self._wait.getStopped():
                        self._wait.hide()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Realignment interrupted.',
                                   icon=QMessageBox.Information)
                        return
                    if not trfs[i].isIdentity():
                        t = trfs[i].getInverseTransform()
                        if i == 0: t.setID(vols[i])
                        elif refid is not None: t.setID(refid)
                        f.setTransform(t)
                        f.setMoving(vols[i])
                        v = f.execute(fixed=None, save=False, wait=None)
                        v.copyFilenameFrom(vols[i])
                        if refid is not None: v.setID(refid)
                    else: v = vols[i]
                    if i == 0: refid = v.getArrayID()
                    v.setFilenamePrefix(prefix)
                    v.setFilenameSuffix(suffix)
                    v.save()
                    vols[i] = v
            """
            Mean volume
            """
            if self._settings.getParameterValue('Mean'):
                self._wait.setInformationText('Compute mean volume...')
                self._wait.buttonVisibilityOff()
                v = vols.getMeanVolume()
                v.setFilename(vols[0].getFilename())
                v.removeSuffixNumber()
                v.setFilenamePrefix('mean')
                v.save()
            """    
            Display result
            """
            self._wait.hide()
            if trfs is not None and len(trfs) > 0:
                dialog = DialogGenericResults(parent=self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.setWindowTitle('Realignment')
                dialog.newTab(title='Rigid parameters')
                dialog.setTreeWidgetHeaderLabels(0, ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz'])
                l = ndarray(shape=(6, len(trfs)), dtype=float)
                for i in range(len(trfs)):
                    l[0:3, i] = trfs[i].getTranslations()
                    l[3:6, i] = trfs[i].getRotationsFromMatrix(deg=True)
                for i in range(len(trfs)):
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
            if trfs is not None and len(trfs) > 0:
                r = messageBox(self,
                               title=self.windowTitle(),
                               text='Would you like to perform\nanother realignment ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes: self._select.clearall()
                else: self.accept()
            else: self._select.clearall()
