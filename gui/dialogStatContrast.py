"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import chdir

from os.path import exists
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import zeros
from numpy import arange

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheStatistics import getDOF
from Sisyphe.core.sisypheStatistics import tmapContrastEstimate
from Sisyphe.core.sisypheStatistics import zmapContrastEstimate
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.core.sisypheStatistics import conjunctionFisher
from Sisyphe.core.sisypheStatistics import conjunctionMudholkar
from Sisyphe.core.sisypheStatistics import conjunctionStouffer
from Sisyphe.core.sisypheStatistics import conjunctionTippett
from Sisyphe.core.sisypheStatistics import conjunctionWorsley
from Sisyphe.core.sisypheStatistics import tTozmap
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogContrast',
           'DialogConjunction',
           'DialogTMapToZMap']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogContrast
              -> DialogConjunction
              -> DialogTMapToZMap
"""

class DialogContrast(QDialog):
    """
    DialogContrast class

    Description
    ~~~~~~~~~~~

    GUI class to define a statistical contrast.

    Reference:
    Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley,
    JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210. doi: 10.1002/hbm.460020402.

    Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak,
    R Turner. Neuroimage 1995 Mar;2(1):45-53. doi: 10.1006/nimg.1995.1007.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogContrast

    Creation: 29/11/2022
    Last revision: 22/11/2024
    """

    # Special method

    """
    Private attributes
    
    _design     SisypheDesign
    _factors    dict, key = factor name, value list of design matrix column indexes
    _cfactors   LabeledComboBox, factor names
    _tradio     QRadioButton, select tmap
    _zradio     QRadioButton, select zmap
    _vector     list[LabeledDoubleSpinBox]
    """

    def __init__(self, design, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical contrast')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        if isinstance(design, SisypheDesign): self._design = design
        elif isinstance(design, str) and exists(design):
            path, ext = splitext(design)
            if ext == SisypheDesign.geFileExt():
                self._design = SisypheDesign()
                self._design.load(design)
            else: raise IOError('File format {} is not statistical model.'.format(basename(design)))
        elif isinstance(design, SisypheDesign): self._design = design
        else: raise TypeError('parameter type {} is not SisypheDesign.'.format(type(design)))

        # Init widgets

        fig = Figure()
        fig.set_layout_engine('constrained')
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.pcolormesh(self._design.getDesignMatrix())
        cdesign = design.getEffectInformations()
        lbl = list()
        for i in range(len(cdesign)):
            buff = cdesign[i][0].split()
            if len(buff) > 1: buff = '\n'.join(buff)
            else: buff = buff[0]
            lbl.append(buff)
        ax.set_xticks(arange(len(lbl)) + 0.5, labels=lbl, rotation=45)
        ax.invert_yaxis()

        self._cfactors = LabeledComboBox(parent=self)
        self._tradio = QRadioButton('t-map', parent=self)
        self._zradio = QRadioButton('z-map', parent=self)
        self._tradio.setChecked(True)
        lyout = QHBoxLayout(self)
        lyout.setContentsMargins(5, 5, 5, 5)
        lyout.setSpacing(10)
        lyout.addWidget(self._cfactors)
        lyout.addWidget(self._tradio)
        lyout.addWidget(self._zradio)
        lyout.addStretch()

        self._flayout = QHBoxLayout(self)
        self._flayout.setContentsMargins(5, 5, 5, 5)
        self._flayout.setSpacing(10)
        self._flayout.addStretch()
        self._factors = dict()
        self._vector = list()
        for i in range(len(cdesign)):
            w = LabeledDoubleSpinBox(parent=self)
            w.setTitle(cdesign[i][0])
            w.setDecimals(1)
            w.setRange(-100.0, 100.0)
            w.setValue(0.0)
            self._flayout.addWidget(w)
            self._vector.append(w)
            """
            estimable, int
            
            - 0 confounding variable, not estimable
            - 1 estimable, main effect
            - 2 estimable, global covariable of interest
            - 3 estimable, covariable of interest by group
            - 4 estimable, covariable of interest by subject
            - 5 estimable, covariable of interest by condition
            """
            estimable = cdesign[i][1]
            if estimable == 1:  # Main effect
                if 'Main' in self._factors: self._factors['Main'].append(i)
                else:
                    self._factors['Main'] = [i]
                    self._cfactors.addItem('Main factor')
                w.setVisible(True)
            else:
                name = cdesign[i][0].split(' ')[0]
                if name in self._factors: self._factors[name].append(i)
                else:
                    self._factors[name] = [i]
                    if estimable > 0: self._cfactors.addItem(name)
                w.setVisible(False)
        self._flayout.addStretch()

        self._cfactors.setCurrentIndex(0)
        # noinspection PyUnresolvedReferences
        self._cfactors.currentIndexChanged.connect(self._factorsComboBoxChanged)

        self._layout.addWidget(canvas)
        self._layout.addLayout(lyout)
        self._layout.addLayout(self._flayout)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setFixedWidth(100)
        self._ok = QPushButton('Estimate', parent=self)
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.pressed.connect(self.estimate)
        # noinspection PyUnresolvedReferences
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)

        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)
        
    # Private methods

    # noinspection PyUnusedLocal
    def _factorsComboBoxChanged(self, index):
        # Add widgets to factor layout
        if self._cfactors.currentText() == 'Main factor': k = 'Main'
        else: k = self._cfactors.currentText()
        for i in range(len(self._vector)):
            if i in self._factors[k]: self._vector[i].setVisible(True)
            else: self._vector[i].setVisible(False)

    # Public methods

    def estimate(self):
        if self._design.isEstimated():
            design = self._design.getDesignMatrix()
            # Contrast vector initialization
            cdesign = self._design.getEffectInformations()
            n = len(cdesign)  # number of factors
            contrast = zeros(n)
            if self._cfactors.currentIndex() == 0: k = 'Main'
            else: k = self._cfactors.currentText()
            for i in range(len(self._vector)):
                contrast[i] = self._vector[i].value()
            try: contrast = self._design.validateContrast(contrast)
            except:
                messageBox(self, title=self.windowTitle(), text='Invalid contrast.')
                return
            # Get degrees of freedom
            df = getDOF(design)
            # Statistical map
            wait = DialogWait(title=self.windowTitle())
            wait.open()
            beta = self._design.getBeta()
            variance = self._design.getPooledVariance()
            try:
                if self._tradio.isChecked():
                    img = tmapContrastEstimate(contrast, design, beta, variance, df, wait=wait)
                    img.setFilename(self._design.getFilename())
                    img.setFilenameSuffix(k.lower() + '_tmap')
                    title = 'Save t-map...'
                else:
                    img = zmapContrastEstimate(contrast, design, beta, variance, df, wait=wait)
                    img.setFilename(self._design.getFilename())
                    img.setFilenameSuffix(k.lower() + '_zmap')
                    title = 'Save z-map...'
            except Exception as err:
                wait.close()
                messageBox(self, title=self.windowTitle(), text='{}'.format(err))
                return
            wait.hide()
            filename = QFileDialog.getSaveFileName(self, title, img.getFilename(),
                                                   filter=SisypheVolume.getFilterExt())[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                wait.show()
                wait.setInformationText('{}\n{}'.format(title, basename(filename)))
                img.saveAs(filename)
            wait.close()
            """
                Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform\nanother contrast ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._factorsComboBoxChanged(0)
                return
            else: self.accept()
        else: messageBox(self, title=self.windowTitle(), text='Statistical model is not estimated.')


class DialogConjunction(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI class to combine statistical maps (conjunction).

    Reference:
    Combining brains: a survey of methods for statistical pooling of information. Lazar NA, Luna B, Sweeney JA,
    Eddy WF. Neuroimage 2002 Jun;16(2):538-50. doi: 10.1006/nimg.2002.1107.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogConjunction

    Creation: 19/11/2024
    Last revision: 05/12/2024
    """

    # Special method

    """
    Private attributes
    
    _files      FilesSelectionWidget
    _settings   FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical map conjunction')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget(parent=self)
        self._files.setTextLabel('Statistical maps')
        self._files.filterSisypheVolume()
        self._files.filterSameSequence([SisypheAcquisition.TMAP, SisypheAcquisition.ZMAP])
        self._layout.addWidget(self._files)

        self._settings = FunctionSettingsWidget('Conjunction', parent=self)
        self._settings.hideIOButtons()
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setFixedWidth(100)
        self._ok = QPushButton('Execute', parent=self)
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.pressed.connect(self.execute)
        # noinspection PyUnresolvedReferences
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)

        # < Revision 06/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._files.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 06/06/2025 >
        self.setModal(True)

    # Public methods

    def execute(self):
        if not self._files.isEmpty():
            wait = DialogWait(title=self.windowTitle())
            wait.setInformationText('Open statistical maps...')
            maps = list()
            filenames = self._files.getFilenames()
            for filename in filenames:
                if exists(filename):
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.load(filename)
                    maps.append(v)
            if len(maps) > 1:
                method = self._settings.getParameterValue('Method')[0][0]
                if method == 'F':
                    wait.setInformationText('Fisher conjunction...')
                    r = conjunctionFisher(maps)
                elif method == 'M':
                    wait.setInformationText('Mudholkar conjunction...')
                    r = conjunctionMudholkar(maps)
                elif method == 'S':
                    wait.setInformationText('Stouffer conjunction...')
                    r = conjunctionStouffer(maps)
                elif method == 'T':
                    wait.setInformationText('Tippett conjunction...')
                    r = conjunctionTippett(maps)
                elif method == 'W':
                    wait.setInformationText('Worsley conjunction...')
                    r = conjunctionWorsley(maps)
                else: raise ValueError('Invalid conjunction method.')
                if r is not None:
                    filename = self._settings.getParameterValue('DefaultFileName')
                    r.setFilename(filename)
                    r.setDirname(maps[0].getFilename())
                    wait.setInformationText('Save {}...'.format(r.getBasename()))
                    r.save()
                    wait.close()
                    r = messageBox(self,
                                   title=self.windowTitle(),
                                   text='Would you like to perform another conjunction ?',
                                   icon=QMessageBox.Question,
                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                   default=QMessageBox.No)
                    if r == QMessageBox.Yes: self._files.clearall()
                    else: self.accept()


class DialogTMapToZMap(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI class to combine statistical maps (conjunction).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogTMapToZMap

    Creation: 30/01/2025
    """

    # Special method

    """
    Private attributes

    _files      FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('t to z-map conversion')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget(parent=self)
        self._files.setTextLabel('t maps')
        self._files.filterSisypheVolume()
        self._files.filterSameSequence([SisypheAcquisition.TMAP])
        self._layout.addWidget(self._files)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        cancel.setFixedWidth(100)
        self._ok = QPushButton('Execute', parent=self)
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.pressed.connect(self.execute)
        # noinspection PyUnresolvedReferences
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)

        # < Revision 06/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._files.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 06/06/2025 >
        self.setModal(True)

    # Public methods

    def execute(self):
        if not self._files.isEmpty():
            filenames = self._files.getFilenames()
            wait = DialogWait(title=self.windowTitle())
            wait.setInformationText('Open t-maps...')
            if len(filenames) > 1:
                wait.buttonVisibilityOn()
                wait.progressVisibilityOn()
                wait.setProgressRange(0, len(filenames))
            for filename in filenames:
                if exists(filename):
                    if wait.getStopped():
                        wait.close()
                        self._files.clearall()
                        return
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.load(filename)
                    wait.setInformationText('{} z-map conversion...'.format(basename(filename)))
                    z = tTozmap(v)
                    z.setFilename(v.getFilename())
                    z.removeAllSuffixes()
                    z.setFilenameSuffix('zmap')
                    wait.setInformationText('save {}...'.format(z.getBasename()))
                    z.save()
                    wait.incCurrentProgressValue()
            wait.close()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform another conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._files.clearall()
            else: self.accept()
