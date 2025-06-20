"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import abspath

from numpy import mean, max

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.processing.simpleItkFilters import meanFilter
from Sisyphe.processing.simpleItkFilters import medianFilter
from Sisyphe.processing.simpleItkFilters import gaussianFilter
from Sisyphe.processing.simpleItkFilters import recursiveGaussianFilter
from Sisyphe.processing.simpleItkFilters import gradientMagnitudeFilter
from Sisyphe.processing.simpleItkFilters import gradientMagnitudeRecursiveFilter
from Sisyphe.processing.simpleItkFilters import laplacianFilter
from Sisyphe.processing.simpleItkFilters import laplacianRecursiveFilter
from Sisyphe.processing.simpleItkFilters import gradientAnisotropicDiffusionFilter
from Sisyphe.processing.simpleItkFilters import curvatureAnisotropicDiffusionFilter
from Sisyphe.processing.simpleItkFilters import minMaxCurvatureFlowFilter
from Sisyphe.processing.simpleItkFilters import curvatureFlowFilter
from Sisyphe.processing.simpleItkFilters import biasFieldCorrection
from Sisyphe.processing.simpleItkFilters import histogramIntensityMatching
from Sisyphe.processing.simpleItkFilters import regressionIntensityMatching
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['AbstractDialogFunction',
           'DialogRemoveNeckSlices',
           'DialogGaussianFilter',
           'DialogMeanFilter',
           'DialogMedianFilter',
           'DialogAnisotropicDiffusionFilter',
           'DialogGradientFilter',
           'DialogLaplacianFilter',
           'DialogBiasFieldCorrectionFilter',
           'DialogHistogramIntensityMatching',
           'DialogRegressionIntensityMatching',
           'DialogIntensityNormalization']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> AbstractDialogFunction -> DialogRemoveNeckSlices
                                        -> DialogGaussianFilter
                                        -> DialogMeanFilter
                                        -> DialogMedianFilter
                                        -> DialogAnisotropicDiffusionFilter
                                        -> DialogGradientFilter
                                        -> DialogLaplacianFilter
                                        -> DialogBiasFieldCorrectionFilter
                                        -> DialogHistogramIntensityMatching
                                        -> DialogRegressionIntensityMatching
                                        -> DialogIntensityNormalization
"""


class AbstractDialogFunction(QDialog):
    """
    AbstractDialogFunction

    Description
    ~~~~~~~~~~~

    GUI dialog window, abstract base class for image filters.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction

    Creation: 10/10/2023
    Last revision: 13/02/2025
    """

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    # Special method

    """
    Private attributes

    _files      FilesSelectionWidget
    _settings   FunctionSettingsWidget
    _funcname   str, function name
    """

    def __init__(self, funcname, parent=None):
        super().__init__(parent)

        self.setWindowTitle('{} function'.format(funcname))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self._funcname = funcname

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget(parent=self)
        # < Revision 10/06/2025
        self._files.setMaximumNumberOfFiles(300)
        # Revision 10/06/2025 >
        self._files.setTextLabel('Volumes')
        self._files.filterSisypheVolume()
        self._layout.addWidget(self._files)

        self._settings = FunctionSettingsWidget(funcname, parent=self)
        self._settings.setButtonsVisibility(False)
        self._settings.setIOButtonsVisibility(False)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close')
        self._ok.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute {} function'.format(funcname))
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(self._execute)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Public methods

    def getLayout(self):
        return self._layout

    def getFilesSelectionWidget(self):
        return self._files
    
    def function(self, filename, wait):
        raise NotImplemented

    def execute(self):
        if self.getNumberOfFilenames() > 0:
            wait = DialogWait(title=self._funcname, cancel=True)
            wait.open()
            for filename in self.getFilenames():
                try:
                    self.function(filename, wait)
                    if wait.getStopped(): break
                except Exception as err:
                    if not wait.getStopped():
                        messageBox(self,
                                   title=self._funcname,
                                   text='{} error: {}\n{}.'.format(basename(filename), type(err), str(err)))
                    break
            wait.close()
            self._files.clearall()

    def getFunctionName(self):
        return self._funcname

    def getFilenames(self):
        return self._files.getFilenames()

    # < Revision 13/02/2025
    # add setFilenames method
    def setFilenames(self, filenames: str | list[str]):
        if isinstance(filenames, str): self._files.add(filenames)
        elif isinstance(filenames, list):
            for filename in filenames:
                if exists(filename): self._files.add(filename)
    # Revision 13/02/2025 >

    def getNumberOfFilenames(self):
        return self._files.filenamesCount()

    def getParametersList(self):
        return self._settings.getParametersList()

    def getParameterValue(self, parameter):
        if isinstance(parameter, str):
            if parameter in self.getParametersList():
                return self._settings.getParameterValue(parameter)
            else: raise ValueError('{} is not a valid parameter.'.format(parameter))
        else: raise TypeError('parameter type {} is not str.'.format(type(parameter)))

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


class DialogRemoveNeckSlices(AbstractDialogFunction):
    """
    DialogRemoveNeckSlices

    Description
    ~~~~~~~~~~~

    GUI dialog window class for gaussian filter.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogRemoveNeckSlices

    Creation: 10/10/2023
    Last Revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('RemoveNeckSlices', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'slices removing...'))
        img = SisypheVolume()
        img.load(filename)
        f = self.getParameterValue('ExtentFactor')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')
        rimg = img.removeNeckSlices(f)
        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogGaussianFilter(AbstractDialogFunction):
    """
    DialogGaussianFilterFunction

    Description
    ~~~~~~~~~~~

    GUI dialog window class for gaussian filter.
    Two algorithms are proposed: convolution or fast recursive.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogGaussianFilterFunction

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method
    
    def __init__(self, parent=None):
        super().__init__('GaussianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Gaussian filtering...'))

        img = SisypheVolume()
        img.load(filename)
        algo = self.getParameterValue('Algorithm')[0]
        fwhm = self.getParameterValue('Fwhm')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if algo == 'Convolve': rimg = gaussianFilter(img, fwhm, wait)
        else: rimg = recursiveGaussianFilter(img, fwhm, wait)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogMeanFilter(AbstractDialogFunction):
    """
    DialogMeanFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for mean filter.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogMeanFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('MeanImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Mean filtering...'))

        img = SisypheVolume()
        img.load(filename)
        fast = self.getParameterValue('Fast')
        radius = self.getParameterValue('KernelRadius')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        rimg = meanFilter(img, radius, fast, wait)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogMedianFilter(AbstractDialogFunction):
    """
    DialogMedianFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for median filter.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogMedianFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('MedianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Median filtering...'))

        img = SisypheVolume()
        img.load(filename)
        radius = self.getParameterValue('KernelRadius')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        rimg = medianFilter(img, radius, wait)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogAnisotropicDiffusionFilter(AbstractDialogFunction):
    """
    DialogAnisotropicDiffusionFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for anisotropic diffusion filters maintaining the image edges.
    Four algorithms are proposed: gradient anisotropic diffusion, curvature anisotropic diffusion
     minmax curvature flow and curvature flow.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogAnisotropicDiffusionFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('AnisotropicDiffusionImageFilter', parent)
        self._settings.settingsVisibilityOn()
        self._algorithmChanged()

        self._settings.getParameterWidget('Algorithm').currentTextChanged.connect(self._algorithmChanged)

    # Private method

    def _algorithmChanged(self):
        algo = self.getParameterValue('Algorithm')[0][0]
        if algo == 'G':
            self._settings.setParameterVisibility('GradientTimeStep', True)
            self._settings.setParameterVisibility('CurvatureTimeStep', False)
            self._settings.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings.setParameterVisibility('FlowTimeStep', False)
            self._settings.setParameterVisibility('Conductance', True)
            self._settings.setParameterVisibility('Radius', False)
        elif algo == 'C':
            self._settings.setParameterVisibility('GradientTimeStep', False)
            self._settings.setParameterVisibility('CurvatureTimeStep', True)
            self._settings.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings.setParameterVisibility('FlowTimeStep', False)
            self._settings.setParameterVisibility('Conductance', True)
            self._settings.setParameterVisibility('Radius', False)
        elif algo == 'M':
            self._settings.setParameterVisibility('GradientTimeStep', False)
            self._settings.setParameterVisibility('CurvatureTimeStep', False)
            self._settings.setParameterVisibility('MinMaxCurvatureTimeStep', True)
            self._settings.setParameterVisibility('FlowTimeStep', False)
            self._settings.setParameterVisibility('Conductance', False)
            self._settings.setParameterVisibility('Radius', True)
        elif algo == 'F':
            self._settings.setParameterVisibility('GradientTimeStep', False)
            self._settings.setParameterVisibility('CurvatureTimeStep', False)
            self._settings.setParameterVisibility('MinMaxCurvatureTimeStep', False)
            self._settings.setParameterVisibility('FlowTimeStep', True)
            self._settings.setParameterVisibility('Conductance', False)
            self._settings.setParameterVisibility('Radius', False)

    # Public method

    def function(self, filename, wait):
        wait.progressVisibilityOn()
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Anisotropic diffusion filtering...'))

        img = SisypheVolume()
        img.load(filename)
        algorithm = self.getParameterValue('Algorithm')[0]
        gstep = self.getParameterValue('GradientTimeStep')
        cstep = self.getParameterValue('CurvatureTimeStep')
        fstep = self.getParameterValue('FlowTimeStep')
        mstep = self.getParameterValue('MinMaxCurvatureTimeStep')
        radius = self.getParameterValue('Radius')
        conductance = self.getParameterValue('Conductance')
        niter = self.getParameterValue('NumberOfIterations')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if algorithm == 'Gradient': rimg = gradientAnisotropicDiffusionFilter(img, gstep, conductance, niter, wait)
        elif algorithm == 'Curvature': rimg = curvatureAnisotropicDiffusionFilter(img, cstep, conductance, niter, wait)
        elif algorithm == 'MinMaxCurvature': rimg = minMaxCurvatureFlowFilter(img, mstep, radius, niter, wait)
        else: rimg = curvatureFlowFilter(img, fstep, niter, wait)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogGradientFilter(AbstractDialogFunction):
    """
    DialogGradientFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for anisotropic diffusion filters maintaining the image edges.
    Three algorithms are proposed: gradient anisotropic diffusion, curvature anisotropic diffusion
    and curvature flow.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogGradientFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('GradientMagnitudeImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Gradient magnitude filtering...'))

        img = SisypheVolume()
        img.load(filename)
        algorithm = self.getParameterValue('Algorithm')[0]
        sigma = self.getParameterValue('Sigma')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if algorithm == 'Discrete': rimg = gradientMagnitudeFilter(img, wait)
        elif algorithm == 'Recursive': rimg = gradientMagnitudeRecursiveFilter(img, sigma, wait)
        else: rimg = gradientMagnitudeFilter(img)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogLaplacianFilter(AbstractDialogFunction):
    """
    DialogLaplacianFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for laplacian filter.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogLaplacianFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('LaplacianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Laplacian filtering...'))

        img = SisypheVolume()
        img.load(filename)
        algorithm = self.getParameterValue('Algorithm')[0]
        sigma = self.getParameterValue('Sigma')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if algorithm == 'Discrete': rimg = laplacianFilter(img, wait)
        else: rimg = laplacianRecursiveFilter(img, sigma, wait)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()


class DialogBiasFieldCorrectionFilter(AbstractDialogFunction):
    """
    DialogBiasFieldCorrectionFilter

    Description
    ~~~~~~~~~~~

    GUI dialog window class for N4 bias field correction filter.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogBiasFieldCorrectionFilter

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('BiasFieldCorrectionImageFilter', parent)
        self.resize(QSize(600, 800))
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Bias field correction...'))

        img = SisypheVolume()
        img.load(filename)
        automask = self.getParameterValue('UseMask')
        shrink = self.getParameterValue('ShrinkFactor')
        splineorder = self.getParameterValue('SplineOrder')
        bins = self.getParameterValue('NumberOfHistogramBins')
        levels = self.getParameterValue('NumberOfFittingLevels')
        points = self.getParameterValue('NumberOfControlPoints')
        niter = self.getParameterValue('NumberOfIteration')
        convergence = self.getParameterValue('ConvergenceThreshold')
        filternoise = self.getParameterValue('WienerFilterNoise')
        biasfwhm = self.getParameterValue('BiasFieldFullWidthAtHalfMaximum')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')
        bprefix = self.getParameterValue('BiasFieldPrefix')
        bsuffix = self.getParameterValue('BiasFieldSuffix')

        rimg, bimg = biasFieldCorrection(img, shrink, bins, biasfwhm, convergence, levels,
                                         splineorder, filternoise, points, niter, automask, wait)

        wait.buttonVisibilityOff()
        wait.progressVisibilityOff()
        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()
        bimg.setFilename(filename)
        bimg.setFilenamePrefix(bprefix)
        bimg.setFilenameSuffix(bsuffix)
        wait.setInformationText('Save {}'.format(bimg.getBasename()))
        bimg.save()


class DialogHistogramIntensityMatching(AbstractDialogFunction):
    """
    DialogHistogramMatching

    Description
    ~~~~~~~~~~~

    GUI dialog window class for histogram matching to normalize grayscale values.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogHistogramMatching

    Creation: 10/10/2023
    Last revision: 10/10/2023
    """

    # Special method

    """
    Private attributes

    _reference  FileSelectionWidget
    _results    DialogGenericResults
    """

    def __init__(self, parent=None):
        super().__init__('HistogramIntensityMatchingImageFilter', parent)
        self._settings.settingsVisibilityOn()

        files = self.getFilesSelectionWidget()
        files.setEnabled(False)

        lyout = self.getLayout()
        self._reference = FileSelectionWidget()
        self._reference.setTextLabel('Reference volume')
        self._reference.filterSisypheVolume()
        self._reference.FieldChanged.connect(self._refChanged)
        self._reference.setToolTip('Set histogram intensity matching reference volume\n'
                                   'All volumes are normalized to this reference volume.')
        lyout.insertWidget(0, self._reference)

        self._results = DialogGenericResults()
        self._results.setWindowTitle('Histogram intensity matching result(s)')
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._results, c)

    # Private method

    def _refChanged(self):
        files = self.getFilesSelectionWidget()
        if self._reference.isEmpty():
            files.clearall()
            files.setEnabled(False)
        else: files.setEnabled(True)

    # Public methods

    def setReference(self, filename: str):
        self._reference.open(filename)

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{}\n{}'.format(basename(filename), 'Histogram intensity matching...'))

        img = SisypheVolume()
        ref = SisypheVolume()
        img.load(filename)
        ref.load(self._reference.getFilename())
        threshold = self.getParameterValue('ExcludeBackground')
        points = self.getParameterValue('NumberOfMatchPoints')
        bins = self.getParameterValue('NumberOfHistogramBins')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        rimg = histogramIntensityMatching(img, ref, bins, points, threshold, wait)

        wait.buttonVisibilityOff()
        wait.progressVisibilityOff()
        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()
        idx = self._results.newTab(rimg.getBasename(), dataset=False)
        self._results.getTreeWidget(idx).setVisible(False)
        fig = self._results.getFigure(idx)
        ax = fig.add_subplot(111)
        npref = ref.getNumpy().flatten()
        s1 = mean(npref)
        s2 = max(npref)
        # noinspection PyTypeChecker
        ax.hist(npref, bins=bins, range=(s1, s2), density=True, histtype='step',
                color='blue', label='Reference image', stacked=True)
        # noinspection PyTypeChecker
        ax.hist(rimg.getNumpy().flatten(), bins=bins, range=(s1, s2), density=True, histtype='step',
                color='green', label='Normalized image', stacked=True)
        ax.legend()

    def execute(self):
        if not self._reference.isEmpty():
            self._results.clear()
            super().execute()
            if self._results.getTabCount() > 0:
                self._results.exec()


class DialogRegressionIntensityMatching(AbstractDialogFunction):
    """
    DialogRegressionIntensityMatching

    Description
    ~~~~~~~~~~~

    GUI dialog window class for regression intensity matching to normalize signal of grayscale images.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogRegressionIntensityMatching

    Creation: 23/10/2024
    Last revision: 29/11/2024
    """

    # Special method

    """
    Private attributes

    _reference  FileSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__('RegressionIntensityMatchingImageFilter', parent)
        self._settings.settingsVisibilityOn()

        files = self.getFilesSelectionWidget()
        files.setEnabled(False)

        lyout = self.getLayout()
        self._reference = FileSelectionWidget()
        self._reference.setTextLabel('Reference volume')
        self._reference.filterSisypheVolume()
        self._reference.FieldChanged.connect(self._refChanged)
        self._reference.setToolTip('Set regression intensity matching reference volume.\n'
                                   'All volumes are normalized to this reference volume.')
        lyout.insertWidget(0, self._reference)

    # Private method

    def _refChanged(self):
        files = self.getFilesSelectionWidget()
        if self._reference.isEmpty():
            files.clearall()
            files.setEnabled(False)
        else:
            files.setEnabled(True)
            fov = SisypheVolume().getVolumeAttribute(self._reference.getFilename(), 'fov')
            files.filterSameFOV(fov)

    # Public methods

    def setReference(self, filename: str):
        self._reference.open(filename)

    def function(self, filename, wait):
        wait.setInformationText('{}\n{}'.format(basename(filename), 'regression intensity matching...'))

        img = SisypheVolume()
        ref = SisypheVolume()
        img.load(filename)
        ref.load(self._reference.getFilename())
        order = self.getParameterValue('Order')
        truncate = self.getParameterValue('Truncate')
        exclude = self.getParameterValue('ExcludeBackground')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if exclude: mask = ref.getMask(fill='2D')
        else: mask = None
        rimg = regressionIntensityMatching(img, ref, mask, order, truncate)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()

    def execute(self):
        if not self._reference.isEmpty():
            super().execute()


class DialogIntensityNormalization(AbstractDialogFunction):
    """
    DialogIntensityNormalization

    Description
    ~~~~~~~~~~~

    GUI dialog window class to normalize grayscale values.
    Two normalizations: z-score or [Ø, 1] range

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogIntensityNormalization

    Creation: 27/10/2024
    Last revision: 27/10/2024
    """

    # Special method

    """
    Private attributes

    _reference  FileSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__('IntensityNormalizationImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public methods

    def function(self, filename, wait):
        wait.setInformationText('{}\n{}'.format(basename(filename), 'intensity normalization...'))

        img = SisypheVolume()
        img.load(filename)
        method = self.getParameterValue('Method')[0]
        truncate = self.getParameterValue('Truncate')
        prefix = self.getParameterValue('Prefix')
        suffix = self.getParameterValue('Suffix')

        if truncate != 0: rimg = img.getTruncateIntensity(truncate)
        else: rimg = img
        if method[0] == 'z': method = 'norm'
        elif method[0] == 'r': method = 'rescale'
        rimg = rimg.getStandardizeIntensity(method)

        rimg.setFilename(filename)
        rimg.setFilenamePrefix(prefix)
        rimg.setFilenameSuffix(suffix)
        wait.setInformationText('Save {}'.format(rimg.getBasename()))
        rimg.save()

    def execute(self):
        files = self.getFilesSelectionWidget()
        if not files.isEmpty():
            super().execute()
