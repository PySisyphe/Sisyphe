"""
External packages/modules
-------------------------

    - ANTs, Image registration, https://github.com/ANTsX/ANTsPy
    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
"""

import sys

from os import remove
from os import mkdir
from os import chdir

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath
from os.path import isabs

from Sisyphe.processing.capturedStdoutProcessing import ProcessRegistration
from Sisyphe.processing.capturedStdoutProcessing import ProcessAtropos
from Sisyphe.processing.capturedStdoutProcessing import ProcessCorticalThickness
from multiprocessing import Queue

from numpy import mean
from numpy import log
from numpy import float_power

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from ants.core import read_transform

from SimpleITK import Cast
from SimpleITK import sitkUInt8
from SimpleITK import sitkFloat32
from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor
from SimpleITK import AffineTransform
from SimpleITK import CenteredTransformInitializerFilter
from SimpleITK import BinaryDilate
from SimpleITK import BinaryFillhole

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.core.sisypheSettings import getUserPySisyphePath
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheTransforms
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheConstants import getTemplatePath
from Sisyphe.core.sisypheConstants import getATROPOSPath
from Sisyphe.core.sisypheConstants import getDISTALPath
from Sisyphe.core.sisypheConstants import getICBM152Path
from Sisyphe.core.sisypheConstants import getICBM452Path
from Sisyphe.core.sisypheConstants import getSRI24Path
from Sisyphe.core.sisypheConstants import isATROPOS
from Sisyphe.core.sisypheConstants import isDISTAL
from Sisyphe.core.sisypheConstants import isICBM152
from Sisyphe.core.sisypheConstants import isICBM452
from Sisyphe.core.sisypheConstants import isSRI24
from Sisyphe.core.sisypheConstants import addPrefixToFilename
from Sisyphe.core.sisypheConstants import addPrefixSuffixToFilename
from Sisyphe.core.sisypheConstants import removeAllPrefixesFromFilename
from Sisyphe.core.sisypheConstants import replaceDirname
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.processing.simpleItkFilters import kmeans
from Sisyphe.processing.simpleItkFilters import gradientAnisotropicDiffusionFilter
from Sisyphe.processing.simpleItkFilters import curvatureAnisotropicDiffusionFilter
from Sisyphe.processing.simpleItkFilters import minMaxCurvatureFlowFilter
from Sisyphe.processing.simpleItkFilters import curvatureFlowFilter
from Sisyphe.processing.simpleItkFilters import biasFieldCorrection
from Sisyphe.processing.simpleItkFilters import gaussianFilter
from Sisyphe.processing.segmentation import probabilityTissueMapsToLabelMap
from Sisyphe.processing.segmentation import nearestNeighborTransformLabelCorrection
from Sisyphe.processing.segmentation import brainMaskFromProbabilityTissueMaps
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.selectFileWidgets import SynchronizedFilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import DialogWaitRegistration

__all__ = ['DialogKMeansClustering',
           'DialogKMeansSegmentation',
           'DialogPriorBasedSegmentation',
           'DialogCorticalThickness',
           'DialogRegistrationBasedSegmentation']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogKMeansClustering
              -> DialogKMeansSegmentation
              -> DialogPriorBasedSegmentation
              -> DialogCorticalThickness
              -> DialogRegistrationBasedSegmentation
"""

class DialogKMeansClustering(QDialog):
    """
    DialogKMeansClustering class

    Description
    ~~~~~~~~~~~

    GUI dialog for KMeans clustering.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogKMeansClustering
    """
    # Special method

    """
    Private attributes

    _pos                int, current position in stdout file, used to follow progress in C++ stdout
    _volumeSelect       FilesSelectionWidget
    _settings           FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('KMeans clustering')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init non-GUI attributes

        self._pos = 0

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._maskSelect = FilesSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Mask(s)')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(False)

        self._mask = QCheckBox('Use mask(s)')
        self._mask.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._mask.toggled.connect(self._maskSelect.setVisible)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._mask)
        self._layout.addWidget(self._maskSelect)

        self._settings1 = FunctionSettingsWidget('AnisotropicDiffusionImageFilter')
        self._settings1.setSettingsButtonFunctionText()
        self._algorithmChanged()
        self._settings1.getParameterWidget('Algorithm').currentTextChanged.connect(self._algorithmChanged)
        self._settings1.VisibilityToggled.connect(self._center)

        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.setSettingsButtonFunctionText()
        self._settings2.VisibilityToggled.connect(self._center)

        self._settings = FunctionSettingsWidget('KMeansClustering')
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('AnisotropicDiffusionFilter').toggled.connect(self._settings1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._settings2.setVisible)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 22/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 22/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _algorithmChanged(self):
        algo = self._settings1.getParameterValue('Algorithm')[0][0]
        if algo == 'G':
            self._settings1.setParameterVisibility('GradientTimeStep', True)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'C':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', True)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'M':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', True)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', True)
        elif algo == 'F':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', True)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', False)

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            filemasks = self._maskSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            wait = DialogWait()
            wait.open()
            for i in range(len(filenames)):
                wait.setInformationText('Open {}...'.format(basename(filenames[i])))
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                vol.load(filenames[i])
                if not self._maskSelect.isEmpty():
                    if i < len(filemasks):
                        mask = SisypheVolume()
                        mask.load(filemasks[i])
                        if not mask.hasSameFieldOfView(vol):
                            wait.hide()
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} and {} do not have the same FOV.'.format(vol.getBasename(),
                                                                                         mask.getBasename()))
                            wait.show()
                            mask = None
                """
                First stage - Anisotropic diffusion filtering
                """
                if self._settings.getParameterValue('AnisotropicDiffusionFilter'):
                    wait.setInformationText('{} anisotropic diffusion filtering...'.format(vol.getBasename()))
                    wait.buttonVisibilityOn()
                    wait.progressVisibilityOn()
                    # Parameters
                    algo = self._settings1.getParameterValue('Algorithm')[0][0]
                    gstep = self._settings1.getParameterValue('GradientTimeStep')
                    cstep = self._settings1.getParameterValue('CurvatureTimeStep')
                    fstep = self._settings1.getParameterValue('FlowTimeStep')
                    mstep = self._settings1.getParameterValue('MinMaxCurvatureTimeStep')
                    radius = self._settings1.getParameterValue('Radius')
                    conductance = self._settings1.getParameterValue('Conductance')
                    niter = self._settings1.getParameterValue('NumberOfIterations')
                    prefix = self._settings1.getParameterValue('Prefix')
                    suffix = self._settings1.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(vol.getFilename(), prefix, suffix)
                    if exists(filename):
                        fltvol = SisypheVolume()
                        fltvol.load(filename)
                    else:
                        # Process
                        try:
                            if algo == 'G': fltvol = gradientAnisotropicDiffusionFilter(vol, gstep, conductance, niter, wait)
                            elif algo == 'C': fltvol = curvatureAnisotropicDiffusionFilter(vol, cstep, conductance, niter, wait)
                            elif algo == 'M': fltvol = minMaxCurvatureFlowFilter(vol, mstep, radius, niter, wait)
                            elif algo == 'F': fltvol = curvatureFlowFilter(vol, fstep, niter, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in anisotropic diffusion filter stage: '
                                                '{}\n{}.'.format(vol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        # Save filtered volume
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(prefix)
                        fltvol.setFilenameSuffix(suffix)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction...'.format(fltvol.getBasename()))
                    wait.buttonVisibilityOn()
                    wait.progressVisibilityOn()
                    # Parameters
                    automask = self._settings2.getParameterValue('UseMask')
                    shrink = self._settings2.getParameterValue('ShrinkFactor')
                    splineorder = self._settings2.getParameterValue('SplineOrder')
                    bins = self._settings2.getParameterValue('NumberOfHistogramBins')
                    levels = self._settings2.getParameterValue('NumberOfFittingLevels')
                    points = self._settings2.getParameterValue('NumberOfControlPoints')
                    niter = self._settings2.getParameterValue('NumberOfIteration')
                    convergence = self._settings2.getParameterValue('ConvergenceThreshold')
                    filternoise = self._settings2.getParameterValue('WienerFilterNoise')
                    biasfwhm = self._settings2.getParameterValue('BiasFieldFullWidthAtHalfMaximum')
                    prefix = self._settings2.getParameterValue('Prefix')
                    suffix = self._settings2.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(fltvol.getFilename(), prefix, suffix)
                    if exists(filename): fltvol.load(filename)
                    else:
                        # Process
                        try:
                            fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                               splineorder, filternoise, points, niter, automask, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in bias field correction stage: '
                                                '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        del bias
                        # Save bias field corrected volume
                        fltvol.setFilename(filename)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Third stage - KMeans clustering
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} kmeans clustering...'.format(fltvol.getBasename()))
                # Parameters
                nclass = self._settings.getParameterValue('NumberOfClasses')
                prefix = self._settings.getParameterValue('Prefix')
                suffix = self._settings.getParameterValue('Suffix')
                classroi = self._settings.getParameterValue('ClassRoi')
                roiprefix = self._settings.getParameterValue('RoiPrefix')
                roisuffix = self._settings.getParameterValue('RoiSuffix')
                # Process
                try: fltvol = kmeans(fltvol, mask, nclass, wait)
                except Exception as err:
                    if not wait.getStopped():
                        wait.hide()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} error in kmeans clustering stage: '
                                        '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                if wait.getStopped():
                    wait.close()
                    return
                """
                Save label volume/ROIs
                """
                for j in range(nclass):
                    fltvol.acquisition.setLabel(j, 'cluster {}'.format(j))
                fltvol.setFilename(vol.getFilename())
                fltvol.acquisition.setModalityToLB()
                fltvol.setFilename(vol.getFilename())
                fltvol.setFilenamePrefix(prefix)
                fltvol.setFilenameSuffix(suffix)
                wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                fltvol.save()
                if classroi:
                    for j in range(nclass):
                        if roiprefix != '':
                            if '*' in roiprefix: prefix = roiprefix.replace('*', str(j+1))
                            else: prefix = roiprefix + str(j + 1)
                        else: prefix = ''
                        if roisuffix != '':
                            if '*' in roisuffix: suffix = roisuffix.replace('*', str(j+1))
                            else: suffix = roisuffix + str(j + 1)
                        else: suffix = ''
                        if prefix == '' and suffix == '': suffix = str(j+1)
                        roi = fltvol.labelToROI(j)
                        roi.setFilename(vol.getFilename())
                        roi.setFilenamePrefix(prefix)
                        roi.setFilenameSuffix(suffix)
                        wait.setInformationText('save {}...'.format(basename(roi.getFilename())))
                        roi.save()
            """
            Exit  
            """
            wait.close()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to do\nmore clustering ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._volumeSelect.clear()
                self._maskSelect.clear()
            else: self.accept()


class DialogKMeansSegmentation(QDialog):
    """
    DialogKMeansSegmentation class

    Description
    ~~~~~~~~~~~

    GUI dialog for KMeans segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSupervisedKMeans

    Last revision: 04/06/2025
    """

    # Special method

    """
    Private attributes

    _volumeSelect       FilesSelectionWidget
    _settings           FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('KMeans segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._maskSelect = FilesSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Mask(s)')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(False)

        self._mask = QCheckBox('Use mask(s)')
        self._mask.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._mask.toggled.connect(self._maskSelect.setVisible)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._mask)
        self._layout.addWidget(self._maskSelect)

        self._settings1 = FunctionSettingsWidget('AnisotropicDiffusionImageFilter')
        self._settings1.setSettingsButtonFunctionText()
        self._algorithmChanged()
        self._settings1.getParameterWidget('Algorithm').currentTextChanged.connect(self._algorithmChanged)
        self._settings1.VisibilityToggled.connect(self._center)

        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.setSettingsButtonFunctionText()
        self._settings2.VisibilityToggled.connect(self._center)

        self._settings = FunctionSettingsWidget('KMeansSegmentation')
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('AnisotropicDiffusionFilter').toggled.connect(self._settings1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._settings2.setVisible)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 22/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 22/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _algorithmChanged(self):
        algo = self._settings1.getParameterValue('Algorithm')[0][0]
        if algo == 'G':
            self._settings1.setParameterVisibility('GradientTimeStep', True)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'C':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', True)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'M':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', True)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', True)
        elif algo == 'F':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', True)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', False)

    # Public method

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            filemasks = self._maskSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            queue = Queue()
            for i in range(len(filenames)):
                wait = DialogWaitRegistration()
                wait.open()
                # < Revision 04/06/2025
                self._volumeSelect.clearSelection()
                self._volumeSelect.setSelectionTo(i)
                # Revision 04/06/2025 >
                wait.setInformationText('Open {}...'.format(basename(filenames[i])))
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                vol.load(filenames[i])
                if not self._maskSelect.isEmpty():
                    if i < len(filemasks):
                        mask = SisypheVolume()
                        mask.load(filemasks[i])
                        if not mask.hasSameFieldOfView(vol):
                            wait.hide()
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} and {} do not have the same FOV.'.format(vol.getBasename(),
                                                                                         mask.getBasename()))
                            wait.show()
                            mask = None
                """
                First stage - Anisotropic diffusion filtering
                """
                if self._settings.getParameterValue('AnisotropicDiffusionFilter'):
                    wait.setInformationText('{} anisotropic diffusion filtering...'.format(vol.getBasename()))
                    # Parameters
                    algo = self._settings1.getParameterValue('Algorithm')[0][0]
                    gstep = self._settings1.getParameterValue('GradientTimeStep')
                    cstep = self._settings1.getParameterValue('CurvatureTimeStep')
                    fstep = self._settings1.getParameterValue('FlowTimeStep')
                    mstep = self._settings1.getParameterValue('MinMaxCurvatureTimeStep')
                    radius = self._settings1.getParameterValue('Radius')
                    conductance = self._settings1.getParameterValue('Conductance')
                    niter = self._settings1.getParameterValue('NumberOfIterations')
                    prefix = self._settings1.getParameterValue('Prefix')
                    suffix = self._settings1.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(vol.getFilename(), prefix, suffix)
                    if exists(filename):
                        fltvol = SisypheVolume()
                        fltvol.load(filename)
                    else:
                        wait.buttonVisibilityOn()
                        wait.progressVisibilityOn()
                        # Process
                        try:
                            if algo == 'G': fltvol = gradientAnisotropicDiffusionFilter(vol, gstep, conductance, niter, wait)
                            elif algo == 'C': fltvol = curvatureAnisotropicDiffusionFilter(vol, cstep, conductance, niter, wait)
                            elif algo == 'M': fltvol = minMaxCurvatureFlowFilter(vol, mstep, radius, niter, wait)
                            elif algo == 'F': fltvol = curvatureFlowFilter(vol, fstep, niter, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in anisotropic diffusion filter stage: '
                                                '{}\n{}.'.format(vol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        # Save filtered volume
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(prefix)
                        fltvol.setFilenameSuffix(suffix)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction...'.format(fltvol.getBasename()))
                    # Parameters
                    automask = self._settings2.getParameterValue('UseMask')
                    shrink = self._settings2.getParameterValue('ShrinkFactor')
                    splineorder = self._settings2.getParameterValue('SplineOrder')
                    bins = self._settings2.getParameterValue('NumberOfHistogramBins')
                    levels = self._settings2.getParameterValue('NumberOfFittingLevels')
                    points = self._settings2.getParameterValue('NumberOfControlPoints')
                    niter = self._settings2.getParameterValue('NumberOfIteration')
                    convergence = self._settings2.getParameterValue('ConvergenceThreshold')
                    filternoise = self._settings2.getParameterValue('WienerFilterNoise')
                    biasfwhm = self._settings2.getParameterValue('BiasFieldFullWidthAtHalfMaximum')
                    prefix = self._settings2.getParameterValue('Prefix')
                    suffix = self._settings2.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(fltvol.getFilename(), prefix, suffix)
                    if exists(filename): fltvol.load(filename)
                    else:
                        wait.buttonVisibilityOn()
                        wait.progressVisibilityOn()
                        # Process
                        try:
                            fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                               splineorder, filternoise, points, niter, automask, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self, title=self.windowTitle(),
                                           text='{} error in bias field correction stage: '
                                                '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        del bias
                        # Save bias field corrected volume
                        fltvol.setFilename(filename)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Third stage - KMeans segmentation
                """
                if fltvol is None: fltvol = vol
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                # Parameters
                nclass = self._settings.getParameterValue('NumberOfClasses')
                niter = self._settings.getParameterValue('NumberOfIterations')
                smooth = self._settings.getParameterValue('Smoothing')
                radius = self._settings.getParameterValue('Radius')
                # noinspection PyUnusedLocal
                segprefix = self._settings.getParameterValue('SegPrefix')
                # noinspection PyUnusedLocal
                segsuffix = self._settings.getParameterValue('SegSuffix')
                # noinspection PyUnusedLocal
                classprefix = self._settings.getParameterValue('Prefix')
                # noinspection PyUnusedLocal
                classsuffix = self._settings.getParameterValue('Suffix')
                wait.setProgressRange(0, niter)
                stdout = join(vol.getDirname(), 'stdout.log')
                # Process
                conv = '[{},0]'.format(niter)
                init = 'Kmeans[{}]'.format(nclass)
                mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
                weight = 0.0
                wait.setInformationText('{} kmeans initialization...'.format(vol.getBasename()))
                if mask is None:
                    wait.addInformationText('{} mask processing...'.format(vol.getBasename()))
                    mask = fltvol.getMask()
                wait.addInformationText('')
                wait.setNumberOfIterations(niter)
                flt = ProcessAtropos(fltvol, mask, init, mrf, conv, weight, stdout, queue)
                try:
                    flt.start()
                    wait.setInformationText('{} kmeans segmentation...'.format(vol.getBasename()))
                    wait.buttonVisibilityOn()
                    wait.progressVisibilityOn()
                    while flt.is_alive():
                        QApplication.processEvents()
                        if exists(stdout): wait.setAntsAtroposProgress(stdout)
                        if wait.getStopped(): flt.terminate()
                except Exception as err:
                    if flt.is_alive(): flt.terminate()
                    if not wait.getStopped():
                        wait.hide()
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} error in kmeans segmentation stage: '
                                        '{}\n{}.'.format(vol.getBasename(), type(err), str(err)))
                finally:
                    # Remove temporary std::cout file
                    if exists(stdout): remove(stdout)
                # noinspection PyUnreachableCode
                if wait.getStopped():
                    wait.close()
                    return
                """
                Save volumes
                """
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                if not queue.empty():
                    vols = list()
                    for j in range(nclass):
                        filename = queue.get()
                        if exists(filename):
                            fltvol = SisypheVolume()
                            fltvol.loadFromNIFTI(filename, reorient=False)
                            fltvol.copyAttributesFrom(vol)
                            fltvol.acquisition.setModalityToOT()
                            fltvol.acquisition.setSequence('TISSUE CLASS {}'.format(j+1))
                            fltvol.acquisition.setUnitToPercent()
                            if classprefix != '':
                                if '*' in classprefix: prefix = classprefix.replace('*', str(j+1))
                                else: prefix = classprefix + str(j+1)
                            else: prefix = ''
                            if classsuffix != '':
                                if '*' in classsuffix: suffix = classsuffix.replace('*', str(j+1))
                                else: suffix = classsuffix + str(j+1)
                            else: suffix = ''
                            if prefix == '' and suffix == '': suffix = str(j+1)
                            fltvol.setFilename(vol.getFilename())
                            fltvol.setFilenamePrefix(prefix)
                            fltvol.setFilenameSuffix(suffix)
                            wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                            fltvol.save()
                            vols.append(fltvol)
                            if exists(filename): remove(filename)
                    if len(vols) > 0:
                        fltvol = probabilityTissueMapsToLabelMap(vols)
                        fltvol.copyAttributesFrom(vol)
                        fltvol.acquisition.setModalityToLB()
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(segprefix)
                        fltvol.setFilenameSuffix(segsuffix)
                        wait.setInformationText('Save {}'.format(fltvol.getBasename()))
                        fltvol.save()
                wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to do\nmore segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._volumeSelect.clear()
                self._maskSelect.clear()
            else: self.accept()


class DialogPriorBasedSegmentation(QDialog):
    """
    DialogPriorBasedSegmentation class

    Description
    ~~~~~~~~~~~

    GUI dialog for prior based segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogPriorBasedSegmentation

    Last revision: 04/06/2025
    """

    # Special method

    """
    Private attributes

    _volumeSelect       FilesSelectionWidget
    _settings           FunctionSettingsWidget
    _settings1          FunctionSettingsWidget
    _settings2          FunctionSettingsWidget
    _settings3          FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Tissue segmentation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init non-GUI attributes

        self._pos = 0
        self._nstages = 0
        self._clevel = None
        self._cstage = None
        self._progbylevel = None
        self._multir = None
        self._stages = None
        self._conv = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._volumeSelect = FilesSelectionWidget(parent=self)
        self._volumeSelect.filterSisypheVolume()
        self._volumeSelect.setCurrentVolumeButtonVisibility(True)
        self._volumeSelect.setTextLabel('Volume(s)')
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setVisible(True)

        self._settings1 = FunctionSettingsWidget('AnisotropicDiffusionImageFilter')
        self._settings1.setSettingsButtonFunctionText()
        self._algorithmChanged()
        self._settings1.getParameterWidget('Algorithm').currentTextChanged.connect(self._algorithmChanged)
        self._settings1.VisibilityToggled.connect(self._center)

        self._settings2 = FunctionSettingsWidget('BiasFieldCorrectionImageFilter')
        self._settings2.setSettingsButtonFunctionText()
        self._settings2.VisibilityToggled.connect(self._center)

        self._settings3 = FunctionSettingsWidget('Resample')
        self._settings3.setSettingsButtonFunctionText()
        self._settings3.getParameterWidget('Dialog').setCheckState(Qt.Checked)
        self._settings3.setParameterVisibility('Dialog', False)
        self._settings3.VisibilityToggled.connect(self._center)

        self._settings = FunctionSettingsWidget('PriorBasedSegmentation')
        self._settings.getParameterWidget('AnisotropicDiffusionFilter').toggled.connect(self._settings1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._settings2.setVisible)
        self._settings.setSettingsButtonFunctionText()
        self._settings.settingsVisibilityOn()
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('Priors').currentIndexChanged.connect(self._priorsChanged)
        self._settings.getParameterWidget('NumberOfPriors').currentIndexChanged.connect(self._priorsChanged)
        self._settings.getParameterWidget('AnisotropicDiffusionFilter').toggled.connect(self._settings1.setVisible)
        self._settings.getParameterWidget('BiasFieldCorrection').toggled.connect(self._settings2.setVisible)
        self._priorsChanged(0)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._settings)
        self._layout.addWidget(self._settings1)
        self._layout.addWidget(self._settings2)
        self._layout.addWidget(self._settings3)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 22/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 22/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # noinspection PyUnusedLocal
    def _priorsChanged(self, index: int):
        v1 = self._settings.getParameterValue('Priors')[0]
        v2 = v1 == 'Custom'
        v3 = int(self._settings.getParameterValue('NumberOfPriors')[0])
        self._settings.setParameterVisibility('T1', v2)
        self._settings.setParameterVisibility('Mask', v2)
        self._settings.setParameterVisibility('GMPrior', v2 and v3 < 4)
        self._settings.setParameterVisibility('CGMPrior', v2 and v3 > 3)
        self._settings.setParameterVisibility('SCGMPrior', v2 and v3 > 3)
        self._settings.setParameterVisibility('WMPrior', v2)
        self._settings.setParameterVisibility('CSFPrior', v2)
        self._settings.setParameterVisibility('BrainstemPrior', v2 and v3 == 6)
        self._settings.setParameterVisibility('CerebellumPrior', v2 and v3 == 6)
        self._settings.setParameterVisibility('PriorSmoothing', v1 != 'KMEANS')
        self._settings3.setVisible(v1 != 'KMEANS')

    def _algorithmChanged(self):
        algo = self._settings1.getParameterValue('Algorithm')[0][0]
        if algo == 'G':
            self._settings1.setParameterVisibility('GradientTimeStep', True)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'C':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', True)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', True)
            self._settings1.setParameterVisibility('Radius', False)
        elif algo == 'M':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', True)
            self._settings1.setParameterVisibility('FlowTimeStep', False)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', True)
        elif algo == 'F':
            self._settings1.setParameterVisibility('GradientTimeStep', False)
            self._settings1.setParameterVisibility('CurvatureTimeStep', False)
            self._settings1.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings1.setParameterVisibility('FlowTimeStep', True)
            self._settings1.setParameterVisibility('Conductance', False)
            self._settings1.setParameterVisibility('Radius', False)

    # Public method

    # < Revision 13/02/2025
    # add setFilenames method
    def setFilenames(self, filenames: str | list[str]):
        if isinstance(filenames, str): filenames = [filenames]
        self._volumeSelect.add(filenames)
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add getFilenames method
    def getFilenames(self) -> list[str]:
        return self._volumeSelect.getFilenames()
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add getParametersDict method
    def getParametersDict(self) -> dict:
        params = dict()
        params['segmentation'] = self._settings.getParametersDict()
        params['filter'] = self._settings1.getParametersDict()
        params['biasfield'] = self._settings2.getParametersDict()
        params['resample'] = self._settings3.getParametersDict()
        return params
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add setParametersFromDict method
    def setParametersFromDict(self, params: dict):
        if 'segmentation' in params: self._settings.setParametersFromDict(params['segmentation'])
        if 'filter' in params: self._settings1.setParametersFromDict(params['filter'])
        if 'biasfield' in params: self._settings2.setParametersFromDict(params['biasfield'])
        if 'resample' in params: self._settings3.setParametersFromDict(params['resample'])
    # Revision 13/02/2025 >

    def getSelectionWidget(self):
        return self._volumeSelect

    def execute(self):
        if not self._volumeSelect.isEmpty():
            filenames = self._volumeSelect.getFilenames()
            vol = SisypheVolume()
            mask = None
            fltvol = None
            queue = Queue()
            for i in range(len(filenames)):
                wait = DialogWaitRegistration()
                wait.open()
                # < Revision 04/06/2025
                self._volumeSelect.clearSelection()
                self._volumeSelect.setSelectionTo(i)
                # Revision 04/06/2025 >
                wait.setInformationText('Open {}...'.format(filenames[i]))
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                vol.load(filenames[i])
                """
                First stage - Anisotropic diffusion filtering
                """
                if self._settings.getParameterValue('AnisotropicDiffusionFilter'):
                    wait.setInformationText('{} anisotropic diffusion filtering...'.format(vol.getBasename()))
                    # Parameters
                    algo = self._settings1.getParameterValue('Algorithm')[0][0]
                    gstep = self._settings1.getParameterValue('GradientTimeStep')
                    cstep = self._settings1.getParameterValue('CurvatureTimeStep')
                    fstep = self._settings1.getParameterValue('FlowTimeStep')
                    mstep = self._settings1.getParameterValue('MinMaxCurvatureTimeStep')
                    radius = self._settings1.getParameterValue('Radius')
                    conductance = self._settings1.getParameterValue('Conductance')
                    niter = self._settings1.getParameterValue('NumberOfIterations')
                    prefix = self._settings1.getParameterValue('Prefix')
                    suffix = self._settings1.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(vol.getFilename(), prefix, suffix)
                    if exists(filename):
                        fltvol = SisypheVolume()
                        fltvol.load(filename)
                    else:
                        wait.buttonVisibilityOn()
                        wait.progressVisibilityOn()
                        # Process
                        try:
                            if algo == 'G': fltvol = gradientAnisotropicDiffusionFilter(vol, gstep, conductance, niter, wait)
                            elif algo == 'C': fltvol = curvatureAnisotropicDiffusionFilter(vol, cstep, conductance, niter, wait)
                            elif algo == 'M': fltvol = minMaxCurvatureFlowFilter(vol, mstep, radius, niter, wait)
                            elif algo == 'F': fltvol = curvatureFlowFilter(vol, fstep, niter, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in anisotropic diffusion filter stage: '
                                                '{}\n{}.'.format(vol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        # Save filtered volume
                        fltvol.setFilename(vol.getFilename())
                        fltvol.setFilenamePrefix(prefix)
                        fltvol.setFilenameSuffix(suffix)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Second stage - Bias field correction
                """
                if fltvol is None: fltvol = vol
                if self._settings.getParameterValue('BiasFieldCorrection'):
                    wait.setInformationText('{} bias field correction...'.format(fltvol.getBasename()))
                    # Parameters
                    automask = self._settings2.getParameterValue('UseMask')
                    shrink = self._settings2.getParameterValue('ShrinkFactor')
                    splineorder = self._settings2.getParameterValue('SplineOrder')
                    bins = self._settings2.getParameterValue('NumberOfHistogramBins')
                    levels = self._settings2.getParameterValue('NumberOfFittingLevels')
                    points = self._settings2.getParameterValue('NumberOfControlPoints')
                    niter = self._settings2.getParameterValue('NumberOfIteration')
                    convergence = self._settings2.getParameterValue('ConvergenceThreshold')
                    filternoise = self._settings2.getParameterValue('WienerFilterNoise')
                    biasfwhm = self._settings2.getParameterValue('BiasFieldFullWidthAtHalfMaximum')
                    prefix = self._settings2.getParameterValue('Prefix')
                    suffix = self._settings2.getParameterValue('Suffix')
                    filename = addPrefixSuffixToFilename(fltvol.getFilename(), prefix, suffix)
                    if exists(filename): fltvol.load(filename)
                    else:
                        wait.buttonVisibilityOn()
                        wait.progressVisibilityOn()
                        # Process
                        try:
                            fltvol, bias = biasFieldCorrection(fltvol, shrink, bins, biasfwhm, convergence, levels,
                                                               splineorder, filternoise, points, niter, automask, wait)
                        except Exception as err:
                            if not wait.getStopped():
                                wait.hide()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in bias field correction stage: '
                                                '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                        if wait.getStopped():
                            wait.close()
                            return
                        del bias
                        # Save bias field corrected volume
                        fltvol.setFilename(filename)
                        wait.setInformationText('save {}...'.format(fltvol.getBasename()))
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        fltvol.save()
                """
                Third stage - Priors registration
                """
                if fltvol is None: fltvol = vol
                # Priors parameters
                transform = self._settings.getParameterValue('PriorsRegistration')[0][0]
                if transform == 'A':
                    # Affine
                    trftype = 'antsRegistrationSyN[a]'
                    self._stages = ['Rigid', 'Affine']
                    self._multir = [[1000, 500, 250, 100], [1000, 500, 250, 100]]
                    self._progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                    self._conv = [6, 6]
                else:
                    # Diffeomorphic
                    trftype = 'antsRegistrationSyNQuick[s]'
                    self._stages = ['Rigid', 'Affine', 'Spline diffeomorphic']
                    self._multir = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
                    self._progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
                    self._conv = [6, 6, 6]
                stdout = join(vol.getDirname(), 'stdout.log')
                priors = self._settings.getParameterValue('Priors')[0]
                if priors == 'ICBM152':
                    ft1 = join(getICBM152Path(), 'icbm152_sym_template_t1.xvol')
                    wait.setInformationText('T1 ICBM152 registration...')
                elif priors == 'ATROPOS':
                    ft1 = join(getATROPOSPath(), 'atropos_template_t1.xvol')
                    wait.setInformationText('T1 ATROPOS registration...')
                elif priors == 'CUSTOM':
                    ft1 = self._settings.getParameterValue('T1')
                    wait.setInformationText('{} registration...'.format(ft1))
                else: ft1 = ''
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                if exists(ft1):
                    rtrf = None
                    mvol = SisypheVolume()
                    mvol.load(ft1)
                    fltvol.setDefaultOrigin()
                    fltvol.setDefaultDirections()
                    mvol.setDefaultOrigin()
                    mvol.setDefaultDirections()
                    if vol.hasTransform(mvol):
                        rtrf = vol.getTransforms()[mvol].copy()
                        # rtrf is a forward transform (fixed -> moving, vol -> mvol)
                        # as registration processing that calculates a forward transform
                        if rtrf.isAffine: rtrf.setAttributesFromFixedVolume(vol)
                        else: rtrf = None
                    if rtrf is None:
                        """
                        Estimating translations
                        """
                        trf = SisypheTransform()
                        trf.setIdentity()
                        c = self._settings.getParameterValue('PriorsRegistrationEstimation')[0][0]
                        if c == 'F':
                            if not fltvol.hasSameFieldOfView(mvol):
                                # print('FOV center alignment')
                                wait.addInformationText('FOV center alignment...')
                                f = CenteredTransformInitializerFilter()
                                f.GeometryOn()
                                img1 = Cast(fltvol.getSITKImage(), sitkFloat32)
                                img2 = Cast(mvol.getSITKImage(), sitkFloat32)
                                t = AffineTransform(f.Execute(img1, img2, trf.getSITKTransform()))
                                trf.setSITKTransform(t)
                        elif c == 'C':
                            # print('Center of mass alignment')
                            wait.addInformationText('Center of mass alignment...')
                            f = CenteredTransformInitializerFilter()
                            f.MomentsOn()
                            img1 = Cast(fltvol.getSITKImage(), sitkFloat32)
                            img2 = Cast(mvol.getSITKImage(), sitkFloat32)
                            t = AffineTransform(f.Execute(img1, img2, trf.getSITKTransform()))
                            trf.setSITKTransform(t)
                        # Set center of rotation to fixed image center
                        trf.setCenter(fltvol.getCenter())
                        """
                        Registration mask
                        """
                        wait.addInformationText('Mask processing...')
                        regmask = fltvol.getMask(morpho='dilate', kernel=4)
                        """
                        Registration
                        """
                        wait.addInformationText('Initialization...')
                        reg = ProcessRegistration(fltvol, mvol, regmask, False, trf, trftype,
                                                  ['mattes', 'mattes'], 0.5, stdout, queue)
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        wait.setStages(self._stages)
                        wait.setMultiResolutionIterations(self._multir)
                        wait.setProgressByLevel(self._progbylevel)
                        wait.setConvergenceThreshold(self._conv)
                        try:
                            reg.start()
                            wait.addInformationText('')
                            while reg.is_alive():
                                QApplication.processEvents()
                                if exists(stdout): wait.setAntsRegistrationProgress(stdout)
                                if wait.getStopped(): reg.terminate()
                        except Exception as err:
                            if reg.is_alive(): reg.terminate()
                            wait.hide()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='{} error in registration stage: '
                                                '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                                return
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        del regmask
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                    """
                    Priors resampling
                    """
                    if not queue.empty():
                        trf = queue.get()
                        rtrf = SisypheTransform()
                        rtrf.setANTSTransform(read_transform(trf))
                        rtrf.setAttributesFromFixedVolume(fltvol)
                        rtrf = rtrf.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                    if rtrf is not None:
                        wait.setInformationText('Priors resampling...')
                        f = SisypheApplyTransform()
                        f.setTransform(rtrf.getInverseTransform())
                        interpol = self._settings3.getParameterValue('Interpolator')[0].lower()
                        prefix = self._settings3.getParameterValue('Prefix')
                        suffix = self._settings3.getParameterValue('Suffix')
                        if interpol == 'nearestneighbor': interpol = 'nearest'
                        f.setInterpolator(interpol)
                        priorsmooth = self._settings.getParameterValue('PriorSmoothing')
                        nclass = int(self._settings.getParameterValue('NumberOfPriors')[0])
                        if priors == 'ICBM152':
                            path = getICBM152Path()
                            fmask = join(path, 'icbm152_sym_template_mask.xvol')
                            fgm = join(path, 'icbm152_sym_template_gm.xvol')
                            fcgm = join(path, 'icbm152_sym_template_cortical_gm.xvol')
                            fscgm = join(path, 'icbm152_sym_template_subcortical_gm.xvol')
                            fwm = join(path, 'icbm152_sym_template_wm.xvol')
                            fcsf = join(path, 'icbm152_sym_template_csf.xvol')
                            fbstem = join(path, 'icbm152_sym_template_brainstem.xvol')
                            fcereb = join(path, 'icbm152_sym_template_cerebellum.xvol')
                        elif priors == 'ATROPOS':
                            path = getATROPOSPath()
                            fmask = join(path, 'atropos_template_brain_mask.xvol')
                            fgm = join(path, 'atropos_template_prior_gm.xvol')
                            fcgm = join(path, 'atropos_template_prior_cortical_gm.xvol')
                            fscgm = join(path, 'atropos_template_prior_subcortical_gm.xvol')
                            fwm = join(path, 'atropos_template_prior_wm.xvol')
                            fcsf = join(path, 'atropos_template_prior_csf.xvol')
                            fbstem = join(path, 'atropos_template_prior_brainstem.xvol')
                            fcereb = join(path, 'atropos_template_prior_cerebellum.xvol')
                        elif priors == 'CUSTOM':
                            fmask = self._settings.getParameterValue('Mask')
                            fgm = self._settings.getParameterValue('GMPrior')
                            fcgm = self._settings.getParameterValue('CGMPrior')
                            fscgm = self._settings.getParameterValue('SCGMPrior')
                            fwm = self._settings.getParameterValue('WMPrior')
                            fcsf = self._settings.getParameterValue('CSFPrior')
                            fbstem = self._settings.getParameterValue('BrainstemPrior')
                            fcereb = self._settings.getParameterValue('CerebellumPrior')
                        else:
                            # KMEANS
                            fmask = ''
                            fgm = ''
                            fcgm = ''
                            fscgm = ''
                            fwm = ''
                            fcsf = ''
                            fbstem = ''
                            fcereb = ''
                        priors = list()
                        # 3 classes: cerebro-spinal fluid, grey matter, white matter,
                        if nclass >= 3:
                            if nclass > 4: fgm = fcgm
                            if fcsf is not None and exists(fcsf): priors.append(fcsf)
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='cerebro-spinal fluid prior is missing.')
                                priors.clear()
                            if fgm is not None and exists(fgm): priors.append(fgm)
                            else:
                                if nclass == 3: messageBox(self,
                                                           title=self.windowTitle(),
                                                           text='Grey matter prior is missing.')
                                else: messageBox(self,
                                                 title=self.windowTitle(),
                                                 text='Cortical grey matter prior is missing.')
                                priors.clear()
                            if fwm is not None and exists(fwm): priors.append(fwm)
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='White matter prior is missing.')
                                priors.clear()
                        # 4 classes: cortical grey matter , subcortical grey matter, white matter, cerebro-spinal fluid
                        if nclass >= 4:
                            if fscgm is not None and exists(fscgm): priors.append(fscgm)
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Subcortical grey matter prior is missing.')
                                priors.clear()
                        # 6 classes: cortical grey matter , subcortical Grey matter, white matter, cerebro-spinal fluid, brainstem, cerebellum
                        if nclass == 6:
                            if fbstem is not None and exists(fbstem): priors.append(fbstem)
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Brainstem prior is missing.')
                                priors.clear()
                            if fcereb is not None and exists(fcereb): priors.append(fcereb)
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Cerebellum prior is missing.')
                                priors.clear()
                        """
                        Save resampled T1 template, priors, mask
                        """
                        if len(priors) == nclass:
                            if mvol is not None:
                                filename = addPrefixSuffixToFilename(ft1,
                                                                     self._settings3.getParameterValue('Prefix'),
                                                                     self._settings3.getParameterValue('Suffix'))
                                filename = replaceDirname(filename, vol.getDirname())
                                if not exists(filename):
                                    f.setMoving(mvol)
                                    r = f.execute(fixed=vol, save=False)
                                    r.setFilename(mvol.getFilename())
                                    r.setDirname(vol.getDirname())
                                    r.setFilenamePrefix(prefix)
                                    r.setFilenameSuffix(suffix)
                                    wait.setInformationText('Save {}...'.format(r.getBasename()))
                                    r.save()
                            for j in range(len(priors)):
                                filename = addPrefixSuffixToFilename(priors[j],
                                                                     self._settings3.getParameterValue('Prefix'),
                                                                     self._settings3.getParameterValue('Suffix'))
                                filename = replaceDirname(filename, vol.getDirname())
                                r = None
                                if exists(filename):
                                    wait.setInformationText('Open {}...'.format(basename(filename)))
                                    v = SisypheVolume()
                                    v.load(filename)
                                    if v.hasSameID(vol): r = v
                                if r is None:
                                    v = SisypheVolume()
                                    v.load(priors[j])
                                    f.setMoving(v)
                                    r = f.execute(save=False)
                                    if priorsmooth > 0.0:
                                        wait.setInformationText('Smooth {}...'.format(v.getBasename()))
                                        r = gaussianFilter(r, priorsmooth, None)
                                    r.copyPropertiesFrom(v, acpc=False)
                                    r.copyAttributesFrom(vol, id=True, identity=False, acquisition=False,
                                                         display=False, transform=True, acpc=True, slope=False)
                                    r.getTransformFromID(v).setName(v.getBasename())
                                    r.setOrigin(vol.getOrigin())
                                    r.setFilename(v.getFilename())
                                    r.setDirname(vol.getDirname())
                                    r.setFilenamePrefix(prefix)
                                    r.setFilenameSuffix(suffix)
                                    wait.setInformationText('Save {}...'.format(r.getBasename()))
                                    r.save()
                                priors[j] = r
                            if fmask != '' and exists(fmask):
                                filename = addPrefixSuffixToFilename(fmask,
                                                                     self._settings3.getParameterValue('Prefix'),
                                                                     self._settings3.getParameterValue('Suffix'))
                                filename = replaceDirname(filename, vol.getDirname())
                                if exists(filename):
                                    wait.setInformationText('Open {}...'.format(basename(filename)))
                                    v = SisypheVolume()
                                    v.load(filename)
                                    if v.hasSameID(vol): mask = v
                                if mask is None:
                                    v = SisypheVolume()
                                    v.load(fmask)
                                    f.setMoving(v)
                                    mask = f.execute(save=False)
                                    mask.copyPropertiesFrom(v, acpc=False)
                                    mask.copyAttributesFrom(vol, id=True, identity=False, acquisition=False,
                                                            display=False, transform=True, acpc=True, slope=False)
                                    mask.getTransformFromID(v).setName(v.getBasename())
                                    mask.setOrigin(vol.getOrigin())
                                    mask.setFilename(v.getFilename())
                                    mask.setDirname(vol.getDirname())
                                    mask.setFilenamePrefix(prefix)
                                    mask.setFilenameSuffix(suffix)
                                    wait.setInformationText('Save {}...'.format(mask.getBasename()))
                                    mask.save()
                        else: priors = 'Kmeans[3]'
                else: priors = 'Kmeans[3]'
                """
                Fourth stage - Finite mixture modeling
                """
                if fltvol is None: fltvol = vol
                wait.setInformationText('{} prior based segmentation initialization...'.format(vol.getBasename()))
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                if mask is None:
                    wait.addInformationText('{} mask processing...'.format(vol.getBasename()))
                    if isinstance(priors, list): mask = (priors[1] + priors[2]) > 0.5
                    else: mask = fltvol.getMask()
                radius = self._settings.getParameterValue('PriorMaskRadius')
                if radius is None: radius = 0
                if radius > 0:
                    img = Cast(mask.getSITKImage() >= 1, sitkUInt8)
                    img = BinaryDilate(img, kernelRadius=[radius] * 3)
                    mask.setSITKImage(img)
                wait.addInformationText('')
                # Parameters
                niter = self._settings.getParameterValue('NumberOfIterations')
                # noinspection PyUnusedLocal
                nclass = int(self._settings.getParameterValue('NumberOfPriors')[0])
                weight = self._settings.getParameterValue('PriorWeight')
                smooth = self._settings.getParameterValue('Smoothing')
                radius = self._settings.getParameterValue('Radius')
                conv = self._settings.getParameterValue('Convergence')[0]
                # noinspection PyUnusedLocal
                strip = self._settings.getParameterValue('SkullStrip')
                # noinspection PyUnusedLocal
                segprefix = self._settings.getParameterValue('SegPrefix')
                # noinspection PyUnusedLocal
                segsuffix = self._settings.getParameterValue('SegSuffix')
                wait.setNumberOfIterations(niter)
                stdout = join(vol.getDirname(), 'stdout.log')
                # Process
                if conv[0] == 'N': conv = '[{},0]'.format(niter)
                else: conv = '[{},{}]'.format(niter, float(conv))
                mrf = '[{},{}x{}x{}]'.format(smooth, radius, radius, radius)
                flt = ProcessAtropos(fltvol, mask, priors, mrf, conv, weight, stdout, queue)
                try:
                    flt.start()
                    wait.setInformationText('{} prior based segmentation...'.format(vol.getBasename()))
                    wait.buttonVisibilityOn()
                    wait.progressVisibilityOn()
                    while flt.is_alive():
                        QApplication.processEvents()
                        if exists(stdout): wait.setAntsAtroposProgress(stdout)
                        if wait.getStopped(): flt.terminate()
                except Exception as err:
                    if flt.is_alive(): flt.terminate()
                    wait.hide()
                    if not wait.getStopped():
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} error prior based segmentation stage: '
                                        '{}\n{}.'.format(fltvol.getBasename(), type(err), str(err)))
                        return
                finally:
                    # Remove temporary std::cout file
                    if exists(stdout): remove(stdout)
                # noinspection PyUnreachableCode
                if wait.getStopped():
                    wait.close()
                    return
                """
                Save volumes
                """
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                radius = self._settings.getParameterValue('BrainMaskRadius')
                if radius is None: radius = 0
                if not queue.empty():
                    vols = list()
                    for j in range(nclass):
                        filename = queue.get()
                        if exists(filename):
                            v = SisypheVolume()
                            v.loadFromNIFTI(filename, reorient=False)
                            v.copyAttributesFrom(vol)
                            v.acquisition.setModalityToOT()
                            if isinstance(priors, str):
                                v.acquisition.setSequence('TISSUE CLASS {}'.format(j + 1))
                                classprefix = 'class' + str(j + 1)
                            else:
                                acq = priors[j].acquisition
                                if acq.isGreyMatterMap(): classprefix = 'gm'
                                elif acq.isSubCorticalGreyMatterMap(): classprefix = 'scgm'
                                elif acq.isWhiteMatterMap(): classprefix = 'wm'
                                elif acq.isCerebroSpinalFluidMap(): classprefix = 'csf'
                                elif acq.isBrainstemMap(): classprefix = 'bstem'
                                elif acq.isCerebellumMap(): classprefix = 'crbl'
                                else: classprefix = 'class' + str(j + 1)
                                v.acquisition.setSequence(acq.getSequence())
                            v.acquisition.setUnitToPercent()
                            v.setFilename(vol.getFilename())
                            v.setFilenamePrefix(classprefix)
                            vols.append(v)
                    if radius > 0:
                        wait.setInformationText('Brain mask processing...')
                        try:
                            mask = brainMaskFromProbabilityTissueMaps(vols, radius)
                            mask = mask.cast('float32')
                        except: radius = 0
                    # Save tissue probability maps
                    for j in range(len(vols)):
                        v = vols[j]
                        if radius > 0 and not v.acquisition.isCerebroSpinalFluidMap():
                            v = v * mask
                            v.acquisition.setSequence(vols[j].acquisition.getSequence())
                            v.acquisition.setUnitToPercent()
                            v.setFilename(vols[j].getFilename())
                            vols[j] = v
                        wait.setInformationText('Save {}'.format(v.getBasename()))
                        v.save()
                    # Save label tissue map
                    if len(vols) > 0:
                        v = probabilityTissueMapsToLabelMap(vols)
                        v.copyAttributesFrom(vol)
                        v.acquisition.setModalityToLB()
                        v.setFilename(vol.getFilename())
                        v.setFilenamePrefix(segprefix)
                        v.setFilenameSuffix(segsuffix)
                        wait.setInformationText('Save {}'.format(v.getBasename()))
                        v.save()
                        if len(vols) > 3:
                            if self._settings.getParameterValue('SegSGM') is True:
                                # add subcortical gray matter to white matter map
                                vols[2] = vols[2] + vols[3]
                                if isinstance(priors, list):
                                    seq = priors[2].acquisition.getSequence()
                                    vols[2].acquisition.setSequence(seq)
                                vols = vols[0:3]
                                v = probabilityTissueMapsToLabelMap(vols)
                                v.copyAttributesFrom(vol)
                                v.acquisition.setModalityToLB()
                                v.setFilename(vol.getFilename())
                                if segprefix != '': segprefix = segprefix + '3'
                                if segsuffix != '': segsuffix = segsuffix + '3'
                                v.setFilenamePrefix(segprefix)
                                v.setFilenameSuffix(segsuffix)
                                wait.setInformationText('Save {}'.format(v.getBasename()))
                                v.save()
                    # Save skull strip volume
                    if radius > 0 and strip:
                        settings = SisypheFunctionsSettings()
                        prefix = settings.getFieldValue('SkullStripping', 'Prefix')
                        suffix = settings.getFieldValue('SkullStripping', 'Suffix')
                        v = vol.cast('float32') * mask
                        v.copyAttributesFrom(vol)
                        v.setFilename(vol.getFilename())
                        v.setFilenamePrefix(prefix)
                        v.setFilenameSuffix(suffix)
                        wait.setInformationText('Save {}'.format(v.getBasename()))
                        v.save()
                    # Save brain mask
                    if radius > 0:
                        mask.copyAttributesFrom(vol)
                        mask.setFilename(vol.getFilename())
                        mask.setFilenameSuffix('mask')
                        mask.acquisition.setModalityToOT()
                        mask.acquisition.setSequence(SisypheAcquisition.MASK)
                        wait.setInformationText('Save {}'.format(mask.getBasename()))
                        mask.save()
                wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to do\nmore segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._volumeSelect.clear()
                self._maskSelect.clear()
            else: self.accept()


class DialogCorticalThickness(QDialog):
    """
    DialogCorticalThickness class

    Description
    ~~~~~~~~~~~

    GUI dialog for cortical thickness processing.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogCorticalThickness

    Last revision: 13/02/2025
    """

    # Special method

    """
    Private attributes

    _select     SynchronizedFilesSelectionWidget
    _settings   FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Cortical thickness')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._select = SynchronizedFilesSelectionWidget(parent=self, single=None,
                                                        multiple=('Label map(s) - Three tissue labels', 'Gray matter map(s)', 'White matter map(s)'))
        self._select.setSisypheVolumeFilters({'multiple': [True, True, True]})
        filters = dict()
        filters['multiple'] = (SisypheAcquisition.LABELS, SisypheAcquisition.GM, SisypheAcquisition.WM)
        self._select.setSequenceFilters(filters)

        self._settings = FunctionSettingsWidget('CorticalThickness')
        self._settings.settingsVisibilityOn()
        self._settings.VisibilityToggled.connect(self._center)

        self._layout.addWidget(self._select)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute cortical thickness processing')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 22/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._select.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 22/05/2025 >
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    # < Revision 13/02/2025
    # add getFilenames method
    def getFilenames(self) -> list[str]:
        return self._select.getFilenames()
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add getParametersDict method
    def getParametersDict(self) -> dict:
        return self._settings.getParametersDict()
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add setParametersFromDict method
    def setParametersFromDict(self, params: dict):
        self._settings.setParametersFromDict(params)
    # Revision 13/02/2025 >

    def getSelectionWidget(self):
        return self._select

    def execute(self):
        if self._select.isReady():
            filenames = self._select.getFilenames()['multiple']
            for i in range(len(filenames['Label map(s)'])):
                wait = DialogWaitRegistration()
                wait.open()
                # < Revision 04/06/2025
                w = self._select.getSelectionWidget('Label map(s)')
                if w is not None:
                    w.clearSelection()
                    w.setSelectionTo(i)
                # Revision 04/06/2025 >
                queue = Queue()
                seg = None
                gm = None
                wm = None
                # noinspection PyUnusedLocal
                rimg = None
                fseg = self._select.getFilenames()['multiple']['Label map(s)'][i]
                fgm = self._select.getFilenames()['multiple']['Grey matter map(s)'][i]
                fwm = self._select.getFilenames()['multiple']['White matter map(s)'][i]
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                if exists(fseg):
                    wait.setInformationText('Open {}...'.format(basename(fseg)))
                    seg = SisypheVolume()
                    seg.load(fseg)
                if exists(fgm):
                    wait.setInformationText('Open {}...'.format(basename(fgm)))
                    gm = SisypheVolume()
                    gm.load(fgm)
                if exists(fwm):
                    wait.setInformationText('Open {}...'.format(basename(fwm)))
                    wm = SisypheVolume()
                    wm.load(fwm)
                if seg is None or gm is None or wm is None:
                    wait.close()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Missing one of the required volumes.')
                    return
                """
                Cortical thickness processing
                """
                wait.setInformationText('{} cortical thickness initialization...'.format(seg.getBasename()))
                iters = self._settings.getParameterValue('NumberOfIterations')
                grdstep = self._settings.getParameterValue('GradientStep')
                grdsmooth = self._settings.getParameterValue('GradientSmoothing')
                # noinspection PyUnusedLocal
                prefix = self._settings.getParameterValue('Prefix')
                # noinspection PyUnusedLocal
                suffix = self._settings.getParameterValue('Suffix')
                stdout = join(seg.getDirname(), 'stdout.log')
                wait.setNumberOfIterations(iters)
                flt = ProcessCorticalThickness(seg, gm, wm, iters, grdstep, grdsmooth, stdout, queue)
                try:
                    flt.start()
                    wait.setInformationText('{} cortical thickness processing...'.format(seg.getBasename()))
                    wait.buttonVisibilityOn()
                    wait.progressVisibilityOn()
                    while flt.is_alive():
                        QApplication.processEvents()
                        if exists(stdout): wait.setAntsAtroposProgress(stdout)
                        if wait.getStopped(): flt.terminate()
                        if not queue.empty():
                            # noinspection PyUnusedLocal
                            rimg = queue.get()
                            if flt.is_alive(): flt.terminate()
                except Exception as err:
                    if flt.is_alive(): flt.terminate()
                    wait.hide()
                    if not wait.getStopped():
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='{} error in cortical thickness: '
                                        '{}\n{}.'.format(seg.getBasename(), type(err), str(err)))
                        return
                finally:
                    # Remove temporary std::cout file
                    if exists(stdout): remove(stdout)
                # noinspection PyUnreachableCode
                if wait.getStopped():
                    wait.close()
                    return
                """
                Save
                """
                wait.buttonVisibilityOff()
                wait.progressVisibilityOff()
                if rimg is not None:
                    v = SisypheVolume()
                    v.copyFromNumpyArray(rimg, spacing=seg.getSpacing(), defaultshape=False)
                    v.copyAttributesFrom(seg)
                    v.acquisition.setModalityToOT()
                    v.acquisition.setSequence(SisypheAcquisition.THICK)
                    filename = seg.getFilename()
                    settings = SisypheFunctionsSettings()
                    pfx = settings.getFieldValue('CorticalThickness', 'Prefix')
                    sfx = settings.getFieldValue('CorticalThickness', 'Suffix')
                    if sfx == '' and pfx == '': pfx = 'thickness'
                    segpfx = settings.getFieldValue('PriorBasedSegmentation', 'SegPrefix')
                    segsfx = settings.getFieldValue('PriorBasedSegmentation', 'SegSuffix')
                    if segpfx != '':
                        for buff in [segpfx + '3_', segpfx + '_']:
                            if buff in filename:
                                filename = filename.replace(buff, '')
                                break
                    if segsfx != '':
                        for buff in ['_' + segsfx + '3',  '_' + segsfx]:
                            if buff in filename:
                                filename = filename.replace(buff, '')
                                break
                    v.setFilename(filename)
                    if pfx !='': v.setFilenamePrefix(pfx)
                    if sfx !='': v.setFilenameSuffix(sfx)
                    wait.setInformationText('Save {}...'.format(v.getBasename()))
                    v.save()
                wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to do\nmore cortical thickness ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._select.clearall()
            else: self.accept()


class DialogRegistrationBasedSegmentation(QDialog):
    """
    DialogRegistrationBasedSegmentation class

    Description
    ~~~~~~~~~~~

    GUI dialog for registration based segmentation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRegistrationBasedSegmentation

    Last revision 04/06/2025
    """

    # Special method

    """
    Private attributes

    _volumeSelect       FilesSelectionWidget
    _settings           FunctionSettingsWidget
    """

    def __init__(self, filename='', parent=None):
        super().__init__(parent)

        # Init window

        if filename == '': title = 'Registration based segmentation'
        else: title = '{} registration based segmentation'.format(splitext(basename(filename))[0].capitalize())
        self.setWindowTitle(title)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._settings = FunctionSettingsWidget('RegistrationBasedSegmentation')
        self._settings.settingsVisibilityOn()
        self._settings.setParameterVisibility('PMAPCorrection', False)
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('RegistrationSequence').currentIndexChanged.connect(self._updateTemplateFilter)
        self._settings.getParameterWidget('RegistrationSequence').currentIndexChanged.connect(self._updateAvailability)
        self._settings.getParameterWidget('TissueCorrectionAlgorithm').currentIndexChanged.connect(self._updateAvailability)
        self._settings.getParameterWidget('LocalStage').stateChanged.connect(self._updateGlobalStageTransform)
        self._settings.setSettingsButtonFunctionText()
        self._updateGlobalStageTransform()

        self._volumeSelect = SynchronizedFilesSelectionWidget(parent=self,
                                                              single=None,
                                                              multiple=('T1',
                                                                        'Grey matter map(s)',
                                                                        'White matter map(s)',
                                                                        'CSF map(s)'))
        self._volumeSelect.setSisypheVolumeFilters({'multiple': [True, True, True, True]})
        flt = {'multiple': [SisypheAcquisition.T1,
                            SisypheAcquisition.GM,
                            SisypheAcquisition.WM,
                            SisypheAcquisition.CSF]}
        self._volumeSelect.setSequenceFilters(flt)
        self._volumeSelect.setMinimumWidth(500)
        self._volumeSelect.setMaximumHeight(800)
        self._volumeSelect.setVisible(True)
        w = self._volumeSelect.getSelectionWidget('T1')
        if w is not None: w.FieldChanged.connect(self._t1Change)
        self._structSelect = SynchronizedFilesSelectionWidget(parent=self,
                                                              single=('Structure', 'Template'),
                                                              multiple=None)
        self._structSelect.setSisypheVolumeFilters({'single': [True, True]})
        flt = {'single': [(SisypheAcquisition.getOTModalityTag(),
                           SisypheAcquisition.getLBModalityTag(),
                           SisypheAcquisition.getTPModalityTag()),
                          SisypheAcquisition.getTPModalityTag()]}
        self._structSelect.setModalityFilters(flt)
        self._structSelect.setMinimumWidth(500)
        self._structSelect.setMaximumHeight(200)
        self._structSelect.setVisible(True)
        w = self._structSelect.getSelectionWidget('Structure')
        if w is not None: w.FieldChanged.connect(self._structChange)

        self._layout.addWidget(self._volumeSelect)
        self._layout.addWidget(self._structSelect)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        save = QPushButton('Save struct settings')
        save.setToolTip('Save struct segmentation settings to xml file')
        cancel.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setFixedWidth(100)
        self._execute.setToolTip('Execute segmentation processing')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addWidget(save)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        save.clicked.connect(self.save)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        if filename != '' and exists(filename):
            self._filename = filename
            self.load()
        else: self._filename = ''

        # < Revision 22/05/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._volumeSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 22/05/2025 >
        self.setModal(True)

    # Static method

    @classmethod
    def _getT1Template(cls, ID: str):
        filename = ''
        if isATROPOS(ID): filename = join(getATROPOSPath(), 'atropos_template_brain_t1.xvol')
        elif isICBM152(ID): filename = join(getICBM152Path(), 'icbm152_asym_template_t1_brain.xvol')
        elif isICBM452(ID): filename = join(getICBM452Path(), 'icbm452_template_t1_warp.xvol')
        elif isDISTAL(ID): filename = join(getDISTALPath(), 'icbm152_template_brain_T1MPRAGE.xvol')
        elif isSRI24(ID): filename = join(getSRI24Path(), 'sri24_template_t1_brain.xvol')
        return filename

    @classmethod
    def _getGreyMatterTemplate(cls, ID: str):
        filename = ''
        if isATROPOS(ID): filename = join(getATROPOSPath(), 'atropos_template_prior_gm.xvol')
        elif isICBM152(ID): filename = join(getICBM152Path(), 'icbm152_asym_template_gm.xvol')
        elif isICBM452(ID): filename = join(getICBM452Path(), 'icbm452_template_probability_gm.xvol')
        elif isSRI24(ID): filename = join(getSRI24Path(), 'sri24_template_gm.xvol')
        return filename

    @classmethod
    def _getWhiteMatterTemplate(cls, ID: str):
        filename = ''
        if isATROPOS(ID): filename = join(getATROPOSPath(), 'atropos_template_prior_wm.xvol')
        elif isICBM152(ID): filename = join(getICBM152Path(), 'icbm152_asym_template_wm.xvol')
        elif isICBM452(ID): filename = join(getICBM452Path(), 'icbm452_template_probability_wm.xvol')
        elif isSRI24(ID): filename = join(getSRI24Path(), 'sri24_template_wm.xvol')
        return filename

    @classmethod
    def _getCerebroSpinalFluidTemplate(cls, ID: str):
        filename = ''
        if isATROPOS(ID): filename = join(getATROPOSPath(), 'atropos_template_prior_csf.xvol')
        elif isICBM152(ID): filename = join(getICBM152Path(), 'icbm152_asym_template_csf.xvol')
        elif isICBM452(ID): filename = join(getICBM452Path(), 'icbm452_template_probability_csf.xvol')
        elif isSRI24(ID): filename = join(getSRI24Path(), 'sri24_template_csf.xvol')
        return filename

    # Private method

    def _getTemplateFromStruct(self, struct: str):
        ID = SisypheVolume.getVolumeAttribute(struct, 'id')
        sequence = self._settings.getParameterValue('RegistrationSequence')[0]
        if sequence == 'T1': return self._getT1Template(ID)
        elif sequence == 'GM': return self._getGreyMatterTemplate(ID)
        elif sequence == 'WM': return self._getWhiteMatterTemplate(ID)
        elif sequence == 'CSF': return self._getCerebroSpinalFluidTemplate(ID)
        else: return ''

    def _t1Change(self):
        wt1 = self._volumeSelect.getSelectionWidget('T1')
        if wt1.filenamesCount() > 0:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Search for related tissue maps.')
            wgm = self._volumeSelect.getSelectionWidget('Grey matter map(s)')
            wwm = self._volumeSelect.getSelectionWidget('White matter map(s)')
            wcsf = self._volumeSelect.getSelectionWidget('CSF map(s)')
            filename = wt1.getFilenames()[-1]
            if wt1.filenamesCount() == wgm.filenamesCount() + 1:
                filename2 = addPrefixToFilename(filename, 'gm')
                if exists(filename2): wgm.add(filename2, signal=False)
                else:
                    wait.close()
                    return
            if wt1.filenamesCount() == wwm.filenamesCount() + 1:
                filename2 = addPrefixToFilename(filename, 'wm')
                if exists(filename2): wwm.add(filename2, signal=False)
                else:
                    wgm.clearLastItem()
                    wait.close()
                    return
            if wt1.filenamesCount() == wcsf.filenamesCount() + 1:
                filename2 = addPrefixToFilename(filename, 'csf')
                if exists(filename2): wcsf.add(filename2, signal=False)
                else:
                    wgm.clearLastItem()
                    wwm.clearLastItem()
                    wait.close()
                    return
            wait.close()

    def _structChange(self):
        if self.isVisible():
            sw = self._structSelect.getSelectionWidget('Structure')
            tw = self._structSelect.getSelectionWidget('Template')
            if not sw.isEmpty():
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Search for related template.')
                filename = self._getTemplateFromStruct(sw.getFilename())
                if exists(filename):
                    tw.open(filename, signal=False)
                    # < Revision 14/11/2024
                    # attr = SisypheVolume.getVolumeAttributes(filename)
                    attr = SisypheVolume.getVolumeAttributes(sw.getFilename())
                    # Revision 14/11/2024 >
                    if attr['modality'] == SisypheAcquisition.getLBModalityTag():
                        self._settings.setParameterVisibility('PMAPCorrection', False)
                    elif attr['modality'] in (SisypheAcquisition.getOTModalityTag(),
                                              SisypheAcquisition.getTPModalityTag()):
                        if attr['sequence'] == SisypheAcquisition.MASK:
                            self._settings.setParameterVisibility('PMAPCorrection', False)
                        elif attr['sequence'] == SisypheAcquisition.STRUCT:
                            self._settings.setParameterVisibility('PMAPCorrection', True)
                wait.close()

    def _updateAvailability(self):
        sequence = self._settings.getParameterValue('RegistrationSequence')[0]
        correction = self._settings.getParameterValue('TissueCorrectionAlgorithm')[0]
        v = not ((sequence == 'T1') and (correction == 'No'))
        flags = self._volumeSelect.getAvailability()
        flags['multiple']['T1'] = True
        flags['multiple']['Grey matter map(s)'] = v
        flags['multiple']['White matter map(s)'] = v
        flags['multiple']['CSF map(s)'] = v
        self._settings.setParameterVisibility('StructureTissue', v)
        self._volumeSelect.setAvailability(flags)
        self._center(None)

    def _updateTemplateFilter(self):
        sequence = self._settings.getParameterValue('RegistrationSequence')[0]
        if sequence == 'T1': v = SisypheAcquisition.T1
        elif sequence == 'GM': v = SisypheAcquisition.GM
        elif sequence == 'WM': v = SisypheAcquisition.WM
        else: v = SisypheAcquisition.CSF
        flt = {'multiple': [(SisypheAcquisition.MASK,
                             SisypheAcquisition.STRUCT,
                             SisypheAcquisition.LABELS), v]}
        self._structSelect.setSequenceFilters(flt)
        self._structSelect.getSelectionWidget('Template').clear(signal=False)
        self._center(None)

    def _updateGlobalStageTransform(self):
        if self._settings.getParameterValue('LocalStage'):
            self._settings.setParameterVisibility('GlobalStageTransform1', True)
            self._settings.setParameterVisibility('GlobalStageTransform2', False)
            self._settings.setParameterVisibility('LocalMargin', True)
            self._settings.setParameterVisibility('LocalStageTransform', True)
            self._settings.setParameterVisibility('SamplingRate', True)
        else:
            self._settings.setParameterVisibility('GlobalStageTransform1', False)
            self._settings.setParameterVisibility('GlobalStageTransform2', True)
            self._settings.setParameterVisibility('LocalMargin', False)
            self._settings.setParameterVisibility('LocalStageTransform', False)
            self._settings.setParameterVisibility('SamplingRate', False)
        self._center(None)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getSelectionWidgets(self):
        return self._volumeSelect, self._structSelect

    def load(self):
        if self._filename == '' or not exists(self._filename):
            filt = 'XML settings (*.xml)'
            path = join(getUserPySisyphePath(), 'segmentation')
            filename = QFileDialog.getOpenFileName(self, 'Open XML settings', path, filt)
            QApplication.processEvents()
            filename = filename[0]
        else: filename = self._filename
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            settings = SisypheSettings(setting=filename)
            if settings.hasSection('RegistrationBasedSegmentation'):
                # Add structure
                self._structSelect.clearall(signal=False)
                struct = settings.getFieldValue('RegistrationBasedSegmentation', 'Struct')
                if not isabs(struct): struct = abspath(join(getTemplatePath(), struct))
                if exists(struct):
                    self._structSelect.setFilenames({'single': {'Structure': struct}})
                    if self.isVisible(): self._structSelect.getSelectionWidget('Template').clear(signal=False)
                # Add template
                template = settings.getFieldValue('RegistrationBasedSegmentation', 'Template')
                if not isabs(template): template = abspath(join(getTemplatePath(), template))
                if exists(template):
                    self._structSelect.setFilenames({'single': {'Template': template}})
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'GlobalStageTransform1')[0]
                self._settings.getParameterWidget('GlobalStageTransform1').setCurrentText(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'GlobalStageTransform2')[0]
                self._settings.getParameterWidget('GlobalStageTransform2').setCurrentText(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'LocalStage')
                self._settings.getParameterWidget('LocalStage').setCheckState(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'LocalMargin')
                self._settings.getParameterWidget('LocalMargin').setValue(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'LocalStageTransform')[0]
                self._settings.getParameterWidget('LocalStageTransform').setCurrentText(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'StructureTissue')[0]
                self._settings.getParameterWidget('StructureTissue').setCurrentText(v)
                v = settings.getFieldValue('RegistrationBasedSegmentation', 'TissueCorrectionAlgorithm')[0]
                self._settings.getParameterWidget('TissueCorrectionAlgorithm').setCurrentText(v)
                self._structSelect.setVisible(False)
            else:
                messageBox(self,
                           'Open registration based segmentation settings...',
                           text='{} is not a registration based segmentation settings file.'.format(basename(filename)))

    def save(self):
        if self._structSelect.isReady():
            segpath = join(getUserPySisyphePath(), 'segmentation')
            if not exists(segpath): mkdir(segpath)
            struct = self._structSelect.getFilenames()['single']['Structure'][0]
            template = self._structSelect.getFilenames()['single']['Template'][0]
            filename = struct.replace(SisypheVolume.getFileExt(), '.xml')
            filename = replaceDirname(filename, segpath)
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Save {} structure settings...'.format(basename(removeAllPrefixesFromFilename(struct))))
            settings = SisypheSettings(setting='struct')
            settings.newSection('RegistrationBasedSegmentation')
            settings.newField('RegistrationBasedSegmentation', 'Struct', attrs={'vartype': 'vol'})
            settings.newField('RegistrationBasedSegmentation', 'Template', attrs={'vartype': 'str'})
            settings.newField('RegistrationBasedSegmentation', 'GlobalStageTransform1', attrs={'vartype': 'lstr'})
            settings.newField('RegistrationBasedSegmentation', 'GlobalStageTransform2', attrs={'vartype': 'lstr'})
            settings.newField('RegistrationBasedSegmentation', 'LocalStage', attrs={'vartype': 'bool'})
            settings.newField('RegistrationBasedSegmentation', 'LocalMargin', attrs={'vartype': 'int'})
            settings.newField('RegistrationBasedSegmentation', 'LocalStageTransform', attrs={'vartype': 'lstr'})
            settings.newField('RegistrationBasedSegmentation', 'StructureTissue', attrs={'vartype': 'lstr'})
            settings.newField('RegistrationBasedSegmentation', 'TissueCorrectionAlgorithm', attrs={'vartype': 'lstr'})
            settings.setFieldValue('RegistrationBasedSegmentation', 'Struct', struct)
            settings.setFieldValue('RegistrationBasedSegmentation', 'Template', template)
            settings.setFieldValue('RegistrationBasedSegmentation', 'GlobalStageTransform1', self._settings.getParameterValue('GlobalStageTransform1'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'GlobalStageTransform2', self._settings.getParameterValue('GlobalStageTransform2'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'LocalStage', self._settings.getParameterValue('LocalStage'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'LocalMargin', self._settings.getParameterValue('LocalMargin'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'LocalStageTransform', self._settings.getParameterValue('LocalStageTransform'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'StructureTissue', self._settings.getParameterValue('StructureTissue'))
            settings.setFieldValue('RegistrationBasedSegmentation', 'TissueCorrectionAlgorithm', self._settings.getParameterValue('TissueCorrectionAlgorithm'))
            settings.saveAs(filename, pretty=True)
            wait.incCurrentProgressValue()
            wait.close()

    def execute(self):
        """
            p = p(STRUCT) ^ (0.5 / p(TISSUE))
            or p = p(STRUCT) ^ (1 + log(0.5 / p(TISSUE)))
            TISSUE is GM, WM, CSF, GM+WM or GM+CSF
        """
        if self._volumeSelect.isReady() and self._structSelect.isReady():
            filenames = self._volumeSelect.getFilenames()
            filenames1 = filenames['multiple']['T1']
            filenames2 = filenames['multiple']['Grey matter map(s)']
            filenames3 = filenames['multiple']['White matter map(s)']
            filenames4 = filenames['multiple']['CSF map(s)']
            sequence = self._settings.getParameterValue('RegistrationSequence')[0]
            correction = self._settings.getParameterValue('TissueCorrectionAlgorithm')[0]
            n = len(filenames1)
            if n > 0:
                for i in range(n):
                    wait = DialogWaitRegistration()
                    wait.open()
                    # < Revision 04/06/2025
                    w = self._volumeSelect.getSelectionWidget('T1')
                    if w is not None:
                        w.clearSelection()
                        w.setSelectionTo(i)
                    # Revision 04/06/2025 >
                    """
                        Load fixed volume
                    """
                    t1 = None
                    origin = None
                    if exists(filenames1[i]):
                        wait.setInformationText('Load {}...'.format(basename(filenames1[i])))
                        t1 = SisypheVolume()
                        t1.load(filenames1[i])
                        origin = t1.getOrigin()
                        t1.setDefaultOrigin()
                        t1.setDefaultDirections()
                    gm = None
                    wm = None
                    csf = None
                    if sequence != 'T1' or correction != 'No':
                        if i < len(filenames2):
                            if exists(filenames2[i]):
                                wait.setInformationText('Load {}...'.format(basename(filenames2[i])))
                                gm = SisypheVolume()
                                gm.load(filenames2[i])
                                gm.setDefaultOrigin()
                                gm.setDefaultDirections()
                        if i < len(filenames3):
                            if exists(filenames3[i]):
                                wait.setInformationText('Load {}...'.format(basename(filenames3[i])))
                                wm = SisypheVolume()
                                wm.load(filenames3[i])
                                wm.setDefaultOrigin()
                                wm.setDefaultDirections()
                        if i < len(filenames4):
                            if exists(filenames4[i]):
                                wait.setInformationText('Load {}...'.format(basename(filenames4[i])))
                                csf = SisypheVolume()
                                csf.load(filenames4[i])
                                csf.setDefaultOrigin()
                                csf.setDefaultDirections()
                        if gm is None or wm is None or csf is None:
                            wait.close()
                            messageBox(self,
                                        title=self.windowTitle(),
                                        text='Missing gray matter, white matter or cerebro-spinal fluid maps.')
                            return
                    else:
                        if t1 is None:
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='Missing T1-weighted MR volume.')
                            wait.close()
                            return
                    if sequence == 'T1': fixed = t1
                    elif sequence == 'GM': fixed = gm
                    elif sequence == 'WM': fixed = wm
                    else: fixed = csf
                    """
                    Load template volume
                    """
                    filenames = self._structSelect.getFilenames()
                    filename = filenames['single']['Template'][0]
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        template = SisypheVolume()
                        template.load(filename)
                        template.setDefaultOrigin()
                        template.setDefaultDirections()
                    else:
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Missing template.')
                        wait.close()
                        return
                    """
                    Load structure volume
                    """
                    filenames = self._structSelect.getFilenames()
                    filename = filenames['single']['Structure'][0]
                    if exists(filename):
                        wait.setInformationText('Load {}...'.format(basename(filename)))
                        struct = SisypheVolume()
                        struct.load(filename)
                        struct.setDefaultOrigin()
                        struct.setDefaultDirections()
                    else:
                        messageBox(self,
                                   title=self.windowTitle(),
                                   text='Missing structure.')
                        wait.close()
                        return
                    """
                    First stage - global registration
                    """
                    if self._settings.getParameterValue('LocalStage'):
                        algo = self._settings.getParameterValue('GlobalStageTransform1')[0]
                    else: algo = self._settings.getParameterValue('GlobalStageTransform2')[0]
                    affine = None
                    fieldname = join(fixed.getDirname(), template.getBasename())
                    fieldname = addPrefixToFilename(fieldname, 'field')
                    if fixed.hasTransform(template) and algo in ('AntsAffine', 'AntsFastAffine'):
                        # backward transform: fixed -> template
                        # < Revision 05/11/2024
                        # affine = fixed.getTransformFromID(template)
                        affine = fixed.getTransformFromID(template).copy()
                        # Revision 05/11/2024 >
                        affine.setAttributesFromFixedVolume(fixed)
                        trf = affine
                    elif exists(fieldname) and algo not in ('AntsAffine', 'AntsFastAffine'):
                        v = SisypheVolume()
                        v.load(fieldname)
                        trf = SisypheTransform()
                        trf.copyFromDisplacementFieldImage(v)
                    else:
                        wait.setInformationText('{} global registration'.format(fixed.getBasename()))
                        """
                        Mask
                        """
                        wait.setInformationText('{} global registration\n'
                                                      'Mask processing...'.format(fixed.getBasename()))
                        img = fixed.getSITKImage()
                        img = img >= mean(fixed.getNumpy().flatten())
                        img = BinaryDilate(img, [4, 4, 4])
                        img = BinaryFillhole(img)
                        mask = SisypheVolume()
                        mask.setSITKImage(img)
                        """
                        Estimating translations
                        """
                        trf = SisypheTransform()
                        trf.setIdentity()
                        wait.setInformationText('{} global registration\n'
                                                      'FOV center alignment...'.format(fixed.getBasename()))
                        f = CenteredTransformInitializerFilter()
                        f.GeometryOn()
                        img1 = Cast(fixed.getSITKImage(), sitkFloat32)
                        img2 = Cast(template.getSITKImage(), sitkFloat32)
                        trf2 = AffineTransform(f.Execute(img1, img2, trf.getSITKTransform()))
                        trf.setSITKTransform(trf2)
                        # Set center of rotation to fixed image center
                        trf.setCenter(fixed.getCenter())
                        """
                        Registration
                        """
                        wait.setInformationText('{} global registration\n'
                                                'Initialization...'.format(fixed.getBasename()))
                        if algo == 'AntsAffine':
                            regtype = 'antsRegistrationSyN[a]'
                            stages = ['Rigid', 'Affine']
                            iters = [[1000, 500, 250, 100], [1000, 500, 250, 100]]
                            progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800]]
                            convergence = [6, 6]
                        elif algo == 'AntsFastAffine':
                            regtype = 'antsRegistrationSyNQuick[a]'
                            stages = ['Rigid', 'Affine']
                            iters = [[1000, 500, 250, 1], [1000, 500, 250, 1]]
                            progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0]]
                            convergence = [6, 6]
                        elif algo == 'AntsSplineDiffeomorphic':
                            regtype = 'antsRegistrationSyN[b]'
                            stages = ['Rigid', 'Affine', 'Spline diffeomorphic']
                            iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                            progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                            convergence = [6, 6, 6]
                        elif algo == 'AntsFastSplineDiffeomorphic':
                            regtype = 'antsRegistrationSyNQuick[b]'
                            stages = ['Rigid', 'Affine', 'Spline diffeomorphic']
                            iters = [[1000, 500, 250, 1], [1000, 500, 250, 1], [100, 70, 50, 1]]
                            progbylevel = [[100, 200, 400, 0], [100, 200, 400, 0], [100, 200, 400, 0]]
                            convergence = [6, 6, 6]
                        elif algo == 'AntsDiffeomorphic':
                            regtype = 'antsRegistrationSyN[s]'
                            stages = ['Rigid', 'Affine', 'Diffeomorphic']
                            iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
                            progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 800]]
                            convergence = [6, 6, 6]
                        elif algo == 'AntsFastDiffeomorphic':
                            regtype = 'antsRegistrationSyNQuick[s]'
                            stages = ['Rigid', 'Affine', 'Diffeomorphic']
                            iters = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 1]]
                            progbylevel = [[100, 200, 400, 800], [100, 200, 400, 800], [100, 200, 400, 0]]
                            convergence = [6, 6, 6]
                        else: raise ValueError('Invalid type of global registration ({})'.format(algo))
                        wait.setStages(stages)
                        wait.setMultiResolutionIterations(iters)
                        wait.setProgressByLevel(progbylevel)
                        wait.setConvergenceThreshold(convergence)
                        queue = Queue()
                        stdout = join(fixed.getDirname(), 'stdout.log')
                        # mask all stages = False, mask used only in the last multi-resolution stage
                        # subsampling = 0.5, 50% of the voxels in the mask are used to compute the similarity function
                        reg = ProcessRegistration(fixed, template, mask, False, trf,
                                                  regtype, ['mattes', 'mattes'], 0.5, stdout, queue)
                        try:
                            reg.start()
                            while reg.is_alive():
                                QApplication.processEvents()
                                if exists(stdout): wait.setAntsRegistrationProgress(stdout)
                                if wait.getStopped(): reg.terminate()
                        except Exception as err:
                            if reg.is_alive(): reg.terminate()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Registration error: {}\n{}.'.format(type(err), str(err)))
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        if queue.empty():
                            wait.close()
                            return
                        r = queue.get()
                        affine = SisypheTransform()
                        affine.setAttributesFromFixedVolume(fixed)
                        affine.setANTSTransform(read_transform(r))
                        # Set center of rotation to default (0.0, 0.0, 0.0)
                        affine = affine.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                        # Remove temporary ants affine transform
                        if exists(r): remove(r)
                        # Displacement field
                        trf = affine
                        if algo not in ('AntsAffine', 'AntsFastAffine'):
                            r = queue.get()  # Displacement field nifti filename
                            if r is not None and exists(r):
                                wait.setInformationText('{} global registration\nSave displacement field...')
                                # Open diffeomorphic displacement field
                                dfield = SisypheVolume()
                                dfield.loadFromNIFTI(r, reorient=False)
                                dfield.acquisition.setSequenceToDisplacementField()
                                dfield = dfield.cast('float64')
                                # Convert affine transform to affine displacement field
                                if not affine.isIdentity():
                                    affine.affineToDisplacementField(inverse=False)
                                    afield = affine.getDisplacementField()
                                    field = afield + dfield
                                    field.acquisition.setSequenceToDisplacementField()
                                else: field = dfield
                                trf = SisypheTransform()
                                trf.copyFromDisplacementFieldImage(field)
                                # Save displacement field image
                                trf.setID(fixed)
                                trf.saveDisplacementField(fieldname)
                                # Remove temporary ants diffeomorphic displacement field
                                remove(r)
                    """
                    Second stage - local registration
                    """
                    if self._settings.getParameterValue('LocalStage') and affine is not None:
                        wait.setInformationText('{} local registration'.format(fixed.getBasename()))
                        # registration mask
                        wait.setInformationText('{} local registration\n'
                                                'Registration mask processing...'.format(fixed.getBasename()))
                        margin = self._settings.getParameterValue('LocalMargin')
                        bb = struct.getBoundingBox(margin=margin)
                        mask = SisypheVolume(size=struct.getSize(), datatype='uint8', spacing=struct.getSpacing())
                        mask.getNumpy()[bb[4]:bb[5], bb[2]:bb[3], bb[0]:bb[1]] = 1
                        f = SisypheApplyTransform()
                        f.setMoving(mask)
                        f.setTransform(affine.getInverseTransform())
                        f.setInterpolator(sitkNearestNeighbor)
                        mask = f.execute(fixed=fixed, save=False)
                        # mask.save(join(fixed.getDirname(), 'mask.xvol'))
                        # Registration
                        wait.setInformationText('{} local registration\n'
                                                'Initialization...'.format(fixed.getBasename()))
                        algo = self._settings.getParameterValue('LocalStageTransform')[0]
                        sampling = self._settings.getParameterValue('SamplingRate')
                        if sampling is None: sampling = 0.5
                        if algo == 'AntsDiffeomorphic':
                            regtype = 'antsRegistrationSyN[so]'
                            stages = ['Diffeomorphic']
                            iters = [[100, 70, 50, 20]]
                            progbylevel = [[100, 200, 400, 800]]
                            convergence = [6]
                        elif algo == 'AntsFastDiffeomorphic':
                            regtype = 'antsRegistrationSyNQuick[so]'
                            stages = ['Diffeomorphic']
                            iters = [[100, 70, 50, 1]]
                            progbylevel = [[100, 200, 400, 0]]
                            convergence = [6]
                        elif algo == 'AntsSplineDiffeomorphic':
                            regtype = 'antsRegistrationSyN[bo]'
                            stages = ['Spline diffeomorphic']
                            iters = [[100, 70, 50, 20]]
                            progbylevel = [[100, 200, 400, 800]]
                            convergence = [6]
                        elif algo == 'AntsFastSplineDiffeomorphic':
                            regtype = 'antsRegistrationSyNQuick[bo]'
                            stages = ['Spline diffeomorphic']
                            iters = [[100, 70, 50, 1]]
                            progbylevel = [[100, 200, 400, 0]]
                            convergence = [6]
                        else: raise ValueError('Invalid type of local registration ({}).'.format(algo))
                        wait.setStages(stages)
                        wait.setMultiResolutionIterations(iters)
                        wait.setProgressByLevel(progbylevel)
                        wait.setConvergenceThreshold(convergence)
                        queue = Queue()
                        stdout = join(fixed.getDirname(), 'stdout.log')
                        # mask all stages = True, mask used in all multi-resolution stages
                        # No subsampling (= 1.0), all voxels in the mask used to compute the similarity function
                        reg = ProcessRegistration(fixed, template, mask, True, affine,
                                                  regtype, ['mattes', 'mattes'], sampling, stdout, queue)
                        try:
                            reg.start()
                            while reg.is_alive():
                                QApplication.processEvents()
                                if exists(stdout): wait.setAntsRegistrationProgress(stdout)
                                if wait.getStopped(): reg.terminate()
                        except Exception as err:
                            if reg.is_alive(): reg.terminate()
                            if not wait.getStopped():
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Registration error: {}\n{}.'.format(type(err), str(err)))
                        finally:
                            # Remove temporary std::cout file
                            if exists(stdout): remove(stdout)
                        # noinspection PyUnreachableCode
                        if wait.getStopped():
                            wait.close()
                            return
                        wait.buttonVisibilityOff()
                        wait.progressVisibilityOff()
                        if queue.empty():
                            wait.close()
                            return
                        # Affine trf, dummy
                        r = queue.get()
                        if exists(r): remove(r)
                        # Displacement field nifti filename
                        r = queue.get()
                        if r is not None and exists(r):
                            wait.setInformationText('{} local registration\nSave displacement field...')
                            # Open diffeomorphic displacement field
                            dfield = SisypheVolume()
                            dfield.loadFromNIFTI(r, reorient=False)
                            dfield.acquisition.setSequenceToDisplacementField()
                            dfield = dfield.cast('float64')
                            # Convert affine transform to affine displacement field
                            if not affine.isIdentity():
                                affine.affineToDisplacementField(inverse=False)
                                afield = affine.getDisplacementField()
                                field = afield + dfield
                                field.acquisition.setSequenceToDisplacementField()
                            else: field = dfield
                            trf = SisypheTransform()
                            trf.copyFromDisplacementFieldImage(field)
                            # Save displacement field image
                            trf.setID(fixed)
                            prefix = splitext(basename(removeAllPrefixesFromFilename(struct.getFilename())))[0]
                            fieldname = addPrefixToFilename(fixed.getFilename(), prefix)
                            trf.saveDisplacementField(fieldname)
                            # Remove temporary ants diffeomorphic displacement field
                            remove(r)
                    """
                    Structure resampling
                    """
                    f = SisypheApplyTransform()
                    f.setMoving(struct)
                    if trf.isAffine():
                        # SisypheApplyTransform uses forward geometric transform
                        t = trf.getInverseTransform()
                        f.setTransform(t)
                    else: f.setTransform(trf)
                    if struct.isUInt8Datatype(): f.setInterpolator(sitkNearestNeighbor)
                    else:
                        settings = SisypheFunctionsSettings()
                        interpol = settings.getFieldValue('Resample', 'Interpolator')
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
                    rstruct = f.execute(save=False, wait=wait)
                    # remove trfs file associated with struct volume
                    filename = splitext(struct.getFilename())[0] + SisypheTransforms.getFileExt()
                    if exists(filename): remove(filename)
                    """
                    Tissue correction
                    """
                    structseq = struct.acquisition.getSequence()
                    if correction != 'No':
                        wait.setInformationText('{} tissue correction...'.format(struct.getBasename()))
                        tissue = self._settings.getParameterValue('StructureTissue')[0]
                        if structseq == SisypheAcquisition.STRUCT: correction = 'Masking'
                        # Masking
                        if correction == 'Masking':
                            wait.setInformationText('{} masking...'.format(struct.getBasename()))
                            # Probability map
                            if structseq == SisypheAcquisition.STRUCT:
                                if tissue == 'GM': ref = gm
                                elif tissue == 'WM': ref = wm
                                elif tissue == 'CSF': ref = csf
                                elif tissue == 'GM+WM': ref = gm + wm
                                elif tissue == 'CSF+GM': ref = csf + gm
                                else: raise ValueError('Invalid tissue correction parameter ({}).'.format(tissue))
                                correction2 = self._settings.getParameterWidget('PMAPCorrection').currentIndex()
                                pref = ref.getNumpy()
                                pstr = rstruct.getNumpy()
                                if correction2 == 0:
                                    # p = p(STRUCT) ^ (0.5 / p(TISSUE))
                                    r = float_power(pstr, 0.5 / pref)
                                else:
                                    # p = p(STRUCT) ^ (1 + log(0.5 / p(TISSUE)))
                                    r = float_power(pstr, 1 + log(0.5 / pref))
                                rstruct.copyFromNumpyArray(r, spacing=fixed.getSpacing())
                            # Binary mask
                            else:
                                labels = probabilityTissueMapsToLabelMap([csf, gm, wm])
                                if tissue == 'CSF': mask = (labels == 1)
                                elif tissue == 'GM': mask = (labels == 2)
                                elif tissue == 'WM': mask = (labels == 3)
                                elif tissue == 'GM+WM': mask = (labels > 1)
                                elif tissue == 'CSF+GM': mask = (3 > labels > 0)
                                else: raise ValueError('Invalid tissue correction parameter ({}).'.format(tissue))
                                rstruct = rstruct * mask
                        # NearestNeighborTransform
                        else:
                            wait.setInformationText('{} nearest neighbor transform...'.format(struct.getBasename()))
                            fcsf = self._getCerebroSpinalFluidTemplate(template.getID())
                            fgm = self._getGreyMatterTemplate(template.getID())
                            fwm = self._getWhiteMatterTemplate(template.getID())
                            if exists(fcsf) and exists(fgm) and exists(fwm):
                                settings = SisypheFunctionsSettings()
                                interpol = settings.getFieldValue('Resample', 'Interpolator')
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
                                tcsf = SisypheVolume()
                                tcsf.load(fcsf)
                                f.setMoving(tcsf)
                                tcsf = f.execute(save=False, wait=wait)
                                tgm = SisypheVolume()
                                tgm.load(fgm)
                                f.setMoving(tgm)
                                tgm = f.execute(save=False, wait=wait)
                                twm = SisypheVolume()
                                twm.load(fwm)
                                f.setMoving(twm)
                                twm = f.execute(save=False, wait=wait)
                                sbjlabels = probabilityTissueMapsToLabelMap([csf, gm, wm])
                                tmplabels = probabilityTissueMapsToLabelMap([tcsf, tgm, twm])
                                margin = self._settings.getParameterValue('LocalMargin')
                                if margin is None: margin = 2
                                rstruct = nearestNeighborTransformLabelCorrection(tmplabels, sbjlabels, rstruct, margin, wait)
                    """
                    Save structure
                    """
                    rstruct.copyAttributesFrom(fixed)
                    if structseq == SisypheAcquisition.STRUCT:
                        rstruct.acquisition.setModalityToOT()
                        rstruct.acquisition.setSequenceToStructMap()
                    elif structseq == SisypheAcquisition.MASK:
                        rstruct.acquisition.setModalityToOT()
                        rstruct.acquisition.setSequenceToMask()
                    elif structseq == SisypheAcquisition.LABELS:
                        rstruct.acquisition.setSequenceToLabels()
                        rstruct.acquisition.setLabels(struct)
                    rstruct.setFilename(fixed.getFilename())
                    rstruct.removeAllPrefixes()
                    rstruct.setFilenamePrefix(struct.getName())
                    if origin is not None: rstruct.setOrigin(origin)
                    wait.setInformationText('Save {}...'.format(rstruct.getBasename()))
                    rstruct.save()
                    wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to do\nmore structure segmentation ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._volumeSelect.clear()
            else: self.accept()

    # noinspection PyUnusedLocal
    def showEvent(self, a0):
        super().showEvent(a0)
        self._updateAvailability()
        self._updateTemplateFilter()
        self._updateGlobalStageTransform()
