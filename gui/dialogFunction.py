"""
    External packages/modules

        Name            Homepage link                                               Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import join
from os.path import split
from os.path import splitext
from os.path import dirname
from os.path import basename
from os.path import abspath

from numpy import mean, max

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
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
from Sisyphe.processing.simpleItkFilters import curvatureFlowFilter
from Sisyphe.processing.simpleItkFilters import biasFieldCorrection
from Sisyphe.processing.simpleItkFilters import histogramMatching
from Sisyphe.processing.antsFilters import antsNonLocalMeansFilter
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException
from Sisyphe.gui.dialogGenericResults import DialogGenericResults


"""
    Class hierarchy

        QDialog -> AbstractDialogFunction -> DialogGaussianFilter
                                          -> DialogMeanFilter
                                          -> DialogMedianFilter
                                          -> DialogAnisotropicDiffusionFilter
                                          -> DialogNonLocalMeansFilter
                                          -> DialogGradientFilter
                                          -> DialogLaplacianFilter
                                          -> DialogBiasFieldCorrectionFilter
                                          -> DialogHistogramMatching

"""


class AbstractDialogFunction(QDialog):
    """
        AbstractDialogFunction

        Description

            GUI dialog window, abstract base class for image filters.

        Inheritance

            QDialog -> AbstractDialogFunction

        Private attributes

            _files      FilesSelectionWidget
            _settings   FunctionSettingsWidget
            _funcname   str, function name

        Public methods

            QVBoxLayout = getLayout()
            FilesSelectionWidget = getFilesSelectionWidget()
            str = getFunctionName()
            execute()
            function(str)               Abstract method
            str = getFunctionName()
            list = getFilenames()
            int = getNumberOfFilenames()
            list = getParametersList()
            str or int or float or date or list = getParameterValue(str)

            inherited QDialog methods
    """

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    # Special method

    def __init__(self, funcname, parent=None):
        super().__init__(parent)

        self.setWindowTitle('{} function'.format(funcname))
        self.resize(QSize(600, 500))
        self._funcname = funcname

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._layout.addWidget(self._files)

        self._settings = FunctionSettingsWidget(funcname)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute {} function'.format(funcname))
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(self._execute)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        ok.clicked.connect(self.accept)
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
            wait = DialogWait(title=self._funcname, cancel=True, parent=self)
            wait.open()
            for filename in self.getFilenames():
                try:
                    self.function(filename, wait)
                    if wait.getStopped():
                        wait.resetStopped()
                        break
                except UserAbortException: break
                except Exception as err:
                    QMessageBox.warning(self, self._funcname, '{} error: {}.'.format(basename(filename), type(err)))
                    break
            wait.close()
            self._files.clearall()

    def getFunctionName(self):
        return self._funcname

    def getFilenames(self):
        return self._files.getFilenames()

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


class DialogGaussianFilter(AbstractDialogFunction):
    """
        DialogGaussianFilterFunction

        Description

            GUI dialog window class for gaussian filter.
            Two algorithms are proposed: convolution or fast recursive.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogGaussianFilterFunction

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method
    
    def __init__(self, parent=None):
        super().__init__('GaussianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Gaussian filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        algo = self.getParameterValue(params[0])[0]
        fwhm = self.getParameterValue(params[1])
        prefix = self.getParameterValue(params[2])
        suffix = self.getParameterValue(params[3])

        try:
            if algo == 'Convolve': rimg = gaussianFilter(img, fwhm, wait)
            else: rimg = recursiveGaussianFilter(img, fwhm, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogMeanFilter(AbstractDialogFunction):
    """
        DialogMeanFilter

        Description

            GUI dialog window class for mean filter.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogMeanFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('MeanImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Mean filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        fast = self.getParameterValue(params[0])
        radius = self.getParameterValue(params[1])
        prefix = self.getParameterValue(params[2])
        suffix = self.getParameterValue(params[3])

        try: rimg = meanFilter(img, radius, fast, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogMedianFilter(AbstractDialogFunction):
    """
        DialogMedianFilter

        Description

            GUI dialog window class for median filter.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogMedianFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('MedianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Median filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        radius = self.getParameterValue(params[0])
        prefix = self.getParameterValue(params[1])
        suffix = self.getParameterValue(params[2])

        try: rimg = medianFilter(img, radius, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogAnisotropicDiffusionFilter(AbstractDialogFunction):
    """
        DialogAnisotropicDiffusionFilter

        Description

            GUI dialog window class for anisotropic diffusion filters maintaining the image edges.
            Three algorithms are proposed: gradient anisotropic diffusion, curvature anisotropic diffusion
            and curvature flow.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogAnisotropicDiffusionFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('AnisotropicDiffusionImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Anisotropic diffusion filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        algorithm = self.getParameterValue(params[0])[0]
        gstep = self.getParameterValue(params[1])
        cstep = self.getParameterValue(params[2])
        fstep = self.getParameterValue(params[3])
        conductance = self.getParameterValue(params[4])
        niter = self.getParameterValue(params[5])
        prefix = self.getParameterValue(params[6])
        suffix = self.getParameterValue(params[7])

        try:
            if algorithm == 'Gradient': rimg = gradientAnisotropicDiffusionFilter(img, gstep, conductance, niter, wait)
            elif algorithm == 'Curvature': rimg = curvatureAnisotropicDiffusionFilter(img, cstep, conductance, niter, wait)
            else: rimg = curvatureFlowFilter(img, fstep, niter, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogNonLocalMeansFilter(AbstractDialogFunction):
    """
        DialogNonLocalMeansFilter

        Description

            GUI dialog window class for non local means denoising filter.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogNonLocalMeansFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('NonLocalMeansImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Non local means filtering'))
        wait.setProgressVisibility(False)
        wait.setButtonVisibility(False)

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        shrink = self.getParameterValue(params[0])
        patchradius = self.getParameterValue(params[1])
        searchradius = self.getParameterValue(params[2])
        noise = self.getParameterValue(params[3])[0]
        prefix = self.getParameterValue(params[4])
        suffix = self.getParameterValue(params[5])

        try:
            rimg = antsNonLocalMeansFilter(img, shrink, patchradius, searchradius, noise, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogGradientFilter(AbstractDialogFunction):
    """
        DialogGradientFilter

        Description

            GUI dialog window class for anisotropic diffusion filters maintaining the image edges.
            Three algorithms are proposed: gradient anisotropic diffusion, curvature anisotropic diffusion
            and curvature flow.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogGradientFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('GradientMagnitudeImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Gradient magnitude filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        algorithm = self.getParameterValue(params[0])[0]
        sigma = self.getParameterValue(params[1])
        prefix = self.getParameterValue(params[2])
        suffix = self.getParameterValue(params[3])

        try:
            if algorithm == 'Discrete': rimg = gradientMagnitudeFilter(img, wait)
            elif algorithm == 'Recursive': rimg = gradientMagnitudeRecursiveFilter(img, sigma, wait)
            else: rimg = gradientMagnitudeFilter(img)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogLaplacianFilter(AbstractDialogFunction):
    """
        DialogLaplacianFilter

        Description

            GUI dialog window class for anisotropic diffusion filters maintaining the image edges.
            Three algorithms are proposed: gradient anisotropic diffusion, curvature anisotropic diffusion
            and curvature flow.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogLaplacianFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('LaplacianImageFilter', parent)
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Laplacian filtering'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        algorithm = self.getParameterValue(params[0])[0]
        sigma = self.getParameterValue(params[1])
        prefix = self.getParameterValue(params[2])
        suffix = self.getParameterValue(params[3])

        try:
            if algorithm == 'Discrete': rimg = laplacianFilter(img, wait)
            elif algorithm == 'Recursive': rimg = laplacianRecursiveFilter(img, sigma, wait)
            else: rimg = gradientMagnitudeFilter(img, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)


class DialogBiasFieldCorrectionFilter(AbstractDialogFunction):
    """
        DialogBiasFieldCorrectionFilter

        Description

            GUI dialog window class for N4 bias field correction filter.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogBiasFieldCorrectionFilter

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('BiasFieldCorrectionImageFilter', parent)
        self.resize(QSize(600, 800))
        self._settings.settingsVisibilityOn()

    # Public method

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Bias field correction'))

        img = SisypheVolume()
        img.load(filename)
        params = self.getParametersList()
        automask = self.getParameterValue(params[0])
        shrink = self.getParameterValue(params[1])
        splineorder = self.getParameterValue(params[2])
        bins = self.getParameterValue(params[3])
        levels = self.getParameterValue(params[4])
        points = self.getParameterValue(params[5])
        niter = self.getParameterValue(params[6])
        convergence = self.getParameterValue(params[7])
        filternoise = self.getParameterValue(params[8])
        biasfwhm = self.getParameterValue(params[9])
        prefix = self.getParameterValue(params[10])
        suffix = self.getParameterValue(params[11])
        bprefix = self.getParameterValue(params[12])
        bsuffix = self.getParameterValue(params[13])

        try:
            rimg, bimg = biasFieldCorrection(img, shrink, bins, biasfwhm, convergence, levels,
                                             splineorder, filternoise, points, niter, automask, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            wait.setProgressVisibility(False)
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            wait.setInformationText('Save {}'.format(basename(filename)))
            rimg.save(filename)
            filename = join(path, bprefix + name + bsuffix + ext)
            wait.setInformationText('Save {}'.format(basename(filename)))
            bimg.save(filename)


class DialogHistogramMatching(AbstractDialogFunction):
    """
        DialogHistogramMatching

        Description

            GUI dialog window class for histogram matching to normalize grayscale values.

        Inheritance

            QDialog -> AbstractDialogFunction -> DialogHistogramMatching

        Private attributes

            _reference  FileSelectionWidget
            _results    DialogGenericResults

        Public methods

            str = getFunctionName()
            function()              override AbstractDialogFunction class
            execute()               override AbstractDialogFunction class

            inherited QDialog methods
            inherited AbstractDialogFunction
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('HistogramMatchingImageFilter', parent)
        self._settings.settingsVisibilityOn()

        files = self.getFilesSelectionWidget()
        files.setEnabled(False)

        lyout = self.getLayout()
        self._reference = FileSelectionWidget()
        self._reference.setTextLabel('Reference volume')
        self._reference.filterSisypheVolume()
        self._reference.FieldChanged.connect(self._refChanged)
        self._reference.setToolTip('Set histogram matching reference volume.')
        lyout.insertWidget(0, self._reference)

        self._results = DialogGenericResults(self)
        self._results.setWindowTitle('Histogram matching result(s)')

    # Private method

    def _refChanged(self):
        files = self.getFilesSelectionWidget()
        if self._reference.isEmpty():
            files.clearall()
            files.setEnabled(False)
        else: files.setEnabled(True)

    # Public methods

    def function(self, filename, wait):
        wait.setProgressVisibility(True)
        wait.setInformationText('{} {}'.format(basename(filename), 'Histogram matching'))

        img = SisypheVolume()
        ref = SisypheVolume()
        img.load(filename)
        ref.load(self._reference.getFilename())
        params = self.getParametersList()
        threshold = self.getParameterValue(params[0])
        points = self.getParameterValue(params[1])
        bins = self.getParameterValue(params[2])
        prefix = self.getParameterValue(params[3])
        suffix = self.getParameterValue(params[4])

        try: rimg = histogramMatching(img, ref, bins, points, threshold, wait)
        except RuntimeError: raise UserAbortException()

        if not wait.getStopped():
            path, name = split(filename)
            name, ext = splitext(name)
            filename = join(path, prefix + name + suffix + ext)
            rimg.save(filename)
            idx = self._results.newTab(name, dataset=False)
            self._results.getTreeWidget(idx).setVisible(False)
            fig = self._results.getFigure(idx)
            ax = fig.add_subplot(111)
            npref = ref.getNumpy().flatten()
            s1 = mean(npref)
            s2 = max(npref)
            ax.hist(npref, bins=bins, range=(s1, s2), density=True, histtype='step',
                    color='blue', label='Reference image', stacked=True)
            ax.hist(rimg.getNumpy().flatten(), bins=bins, range=(s1, s2), density=True, histtype='step',
                    color='green', label='Normalized image', stacked=True)
            ax.legend()

    def execute(self):
        if not self._reference.isEmpty():
            self._results.clear()
            super().execute()
            if self._results.getTabCount() > 0:
                self._results.exec()
