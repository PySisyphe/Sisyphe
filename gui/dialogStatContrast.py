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
from numpy import argwhere

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheConstants import getID_ICBM152
from Sisyphe.core.sisypheConstants import addPrefixSuffixToFilename
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
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
from Sisyphe.core.sisypheStatistics import pvalueTot
from Sisyphe.core.sisypheStatistics import pvalueToz
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogRegistration import DialogRegistration
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

__all__ = ['DialogContrast',
           'DialogConjunction',
           'DialogTMapToZMap',
           'DialogLateralityIndex']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogContrast
              -> DialogConjunction
              -> DialogTMapToZMap
              -> DialogLateralityIndex
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
    Last revision: 06/02/2026
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
        # noinspection PyUnresolvedReferences
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

        # design matrix figure
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
            w.setVisible(False)
            self._flayout.addWidget(w)
            self._vector.append(w)
            """
            estimable, int:
            
            - 0 confounding variable, not estimable
            - 1 estimable, main effect
            - 2 estimable, global covariate of interest
            - 3 estimable, covariate of interest by group
            - 4 estimable, covariate of interest by subject
            - 5 estimable, covariate of interest by condition
            """
            estimable = cdesign[i][1]
            if estimable == 1:  # Main effect
                if 'Main' in self._factors: self._factors['Main'].append(i)
                else:
                    self._factors['Main'] = [i]
                    # < Revision 30/03/2026
                    # self._cfactors.addItem('Main factor')
                    self._cfactors.addItem('Main')
                    # Revision 30/03/2026 >
                # w.setVisible(True)
            else:
                name = cdesign[i][0].split(' ')[0]
                if name in self._factors: self._factors[name].append(i)
                else:
                    self._factors[name] = [i]
                    if estimable > 0: self._cfactors.addItem(name)
                # w.setVisible(False)
        # < Revision 06/02/2026
        self._cfactors.setCurrentIndex(0)
        name =  self._cfactors.currentText()
        for idx in self._factors[name]:
            self._vector[idx].setVisible(True)
        # Revision 06/02/2026 >
        self._flayout.addStretch()

        self._cfactors.setCurrentIndex(0)
        # noinspection PyUnresolvedReferences
        self._cfactors.currentIndexChanged.connect(self._factorsComboBoxChanged)

        self._layout.addWidget(canvas)
        self._layout.addLayout(lyout)
        self._layout.addLayout(self._flayout)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32' or platform == 'linux': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Close', parent=self)
        # < Revision 08/10/2005
        # cancel.setFixedWidth(100)
        # Revision 08/10/2005 >
        self._ok = QPushButton('Estimate', parent=self)
        # < Revision 08/10/2005
        # self._ok.setFixedWidth(100)
        # self._ok.setAutoDefault(True)
        # self._ok.setDefault(True)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        # Revision 08/10/2005 >
        layout.addWidget(cancel)
        layout.addWidget(self._ok)
        layout.addStretch()

        # noinspection PyUnresolvedReferences
        self._ok.pressed.connect(self.estimate)
        # noinspection PyUnresolvedReferences
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)

        # dialog resize off
        # noinspection PyUnresolvedReferences
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
    Last revision: 15/10/2025
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
        # noinspection PyUnresolvedReferences
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
        if platform == 'win32' or platform == 'linux': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Close', parent=self)
        # < Revision 08/10/2025
        # cancel.setFixedWidth(100)
        # Revision 08/10/2025 >
        self._ok = QPushButton('Execute', parent=self)
        # < Revision 08/10/2025
        # self._ok.setFixedSize(QSize(100, 32))
        # self._ok.setAutoDefault(True)
        # self._ok.setDefault(True)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        # < Revision 08/10/2025
        layout.addWidget(cancel)
        layout.addWidget(self._ok)
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
        # noinspection PyUnresolvedReferences
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

    # < Revision 15/10/2025
    # add getFilesSelectionWidget method
    def getFilesSelectionWidget(self):
        return self._files
    # Revision 15/10/2025 >


class DialogTMapToZMap(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI class to combine statistical maps (conjunction).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogTMapToZMap

    Creation: 08/10/2025
    Last revision: 15/10/2025
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
        # noinspection PyUnresolvedReferences
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
        if platform == 'win32' or platform == 'linux': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        # < Revision 08/10/2025
        # cancel.setFixedWidth(100)
        # Revision 08/10/2025 >
        self._ok = QPushButton('Execute', parent=self)
        # < Revision 08/10/2025
        # self._ok.setFixedSize(QSize(100, 32))
        # self._ok.setAutoDefault(True)
        # self._ok.setDefault(True)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
        # Revision 08/10/2025 >
        layout.addWidget(cancel)
        layout.addWidget(self._ok)
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
        # noinspection PyUnresolvedReferences
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

    # < Revision 15/10/2025
    # add getFilesSelectionWidget method
    def getFilesSelectionWidget(self):
        return self._files
    # Revision 15/10/2025 >


class DialogLateralityIndex(QDialog):
    """
    Description
    ~~~~~~~~~~~

    GUI class used to calculate the laterality index of a statistical map.

    Ref: Implementation of clinically relevant and robust fMRI-based language lateralization: Choosing the laterality
    index calculation method. Brumer I, De Vita E, Ashmore J, Jarosz J, Borri M. PLoS One. 2020 Mar 12;15(3):e0230129.
    doi: 10.1371/journal.pone.0230129. eCollection 2020.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogLateralityIndex

    Creation: 14/10/2025
    Last revision: 15/10/2025
    """
    # Special method

    """
    Private attributes
    
    _map                FileSelectionWidget
    _anat               FileSelectionWidget
    _regsettings        FunctionSettingsWidget
    _resamplesettings   FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Laterality index')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._sshot = None

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._map = FileSelectionWidget(parent=self)
        self._map.setTextLabel('Statistical map')
        self._map.filterSisypheVolume()
        self._map.filterSameSequence([SisypheAcquisition.TMAP, SisypheAcquisition.ZMAP])
        self._map.FieldChanged.connect(self._mapAdded)
        self._layout.addWidget(self._map)

        self._anat = FileSelectionWidget(parent=self)
        self._anat.setTextLabel('fMRI volume')
        self._anat.alignLabels(self._map)
        self._anat.filterSisypheVolume()
        self._anat.setEnabled(False)
        self._anat.setVisible(False)
        self._anat.FieldChanged.connect(self._anatAdded)
        self._layout.addWidget(self._anat)

        self._template = FileSelectionWidget(parent=self)
        self._template.setTextLabel('Template')
        self._template.filterSisypheVolume()
        self._template.filterICBM()
        self._template.filterSameModality(SisypheAcquisition.getTPModalityTag())
        self._template.alignLabels(self._map)
        # < Revision 15/10/2025
        self._template.FieldChanged.connect(self._okEnabled)
        # Revision 15/10/2025 >
        self._layout.addWidget(self._template)

        self._lmask = FileSelectionWidget(parent=self)
        self._lmask.setTextLabel('Left mask')
        self._lmask.alignLabels(self._map)
        self._lmask.filterSisypheVolume()
        self._lmask.filterICBM()
        # < Revision 15/10/2025
        self._lmask.FieldChanged.connect(self._okEnabled)
        # Revision 15/10/2025 >
        self._layout.addWidget(self._lmask)

        self._rmask = FileSelectionWidget(parent=self)
        self._rmask.setTextLabel('Right mask')
        self._rmask.alignLabels(self._map)
        self._rmask.filterSisypheVolume()
        self._rmask.filterICBM()
        # < Revision 15/10/2025
        self._rmask.FieldChanged.connect(self._okEnabled)
        # Revision 15/10/2025 >
        self._layout.addWidget(self._rmask)

        self._settings = FunctionSettingsWidget('LateralityIndex', parent=self)
        self._settings.setSettingsButtonFunctionText()
        self._settings.VisibilityToggled.connect(self._center)
        self._settings.getParameterWidget('MaskType').currentIndexChanged.connect(self._maskTypeChanged)
        filename = self._settings.getParameterValue('LeftMask')
        if filename != '' and exists(filename): self._lmask.open(filename)
        filename = self._settings.getParameterValue('RightMask')
        if filename != '' and exists(filename): self._rmask.open(filename)
        filename = self._settings.getParameterValue('Template')
        if filename != '' and exists(filename): self._template.open(filename)
        widget = self._settings.getParameterWidget('LeftMask')
        widget.filterSisypheVolume()
        widget.filterICBM()
        widget.FieldChanged.connect(self._settingsAdded)
        widget = self._settings.getParameterWidget('RightMask')
        widget.filterSisypheVolume()
        widget.filterICBM()
        widget.FieldChanged.connect(self._settingsAdded)
        widget = self._settings.getParameterWidget('Template')
        widget.filterSisypheVolume()
        widget.filterICBM()
        widget.filterSameModality(SisypheAcquisition.getTPModalityTag())
        widget.FieldChanged.connect(self._settingsAdded)
        self._layout.addWidget(self._settings)

        self._regsettings = FunctionSettingsWidget('Registration', parent=self)
        self._regsettings.VisibilityToggled.connect(self._center)
        self._regsettings.setVisible(False)
        self._regsettings.setSettingsButtonFunctionText()
        self._regsettings.setParameterVisibility('Batch', False)
        self._regsettings.setParameterVisibility('Rigid', False)
        self._regsettings.setParameterVisibility('Affine', False)
        self._regsettings.setParameterVisibility('DisplacementField', False)
        self._regsettings.setParameterVisibility('Transform', True)
        self._regsettings.setParameterVisibility('ManualRegistration', False)
        self._regsettings.setParameterVisibility('Inverse', False)
        self._regsettings.setParameterVisibility('CheckRegistration', False)
        self._regsettings.setParameterVisibility('Resample', False)
        self._regsettings.setParameterValue('ManualRegistration', False)
        self._regsettings.setParameterValue('Inverse', False)
        self._regsettings.setParameterValue('CheckRegistration', False)
        self._regsettings.setParameterValue('Resample', True)
        self._layout.addWidget(self._regsettings)

        self._resamplesettings = FunctionSettingsWidget('Resample', parent=self)
        self._resamplesettings.VisibilityToggled.connect(self._center)
        self._resamplesettings.setVisible(False)
        self._resamplesettings.setSettingsButtonFunctionText()
        self._resamplesettings.setParameterVisibility('Prefix', False)
        self._resamplesettings.setParameterVisibility('Suffix', False)
        self._resamplesettings.setParameterVisibility('NormalizationPrefix', True)
        self._resamplesettings.setParameterVisibility('NormalizationSuffix', True)
        self._resamplesettings.setParameterVisibility('Dialog', False)
        self._resamplesettings.getParameterWidget('Dialog').setChecked(False)
        self._layout.addWidget(self._resamplesettings)

        # Init default dialog buttons

        layout = QHBoxLayout(self)
        if platform == 'win32' or platform == 'linux': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel', parent=self)
        self._ok = QPushButton('OK', parent=self)
        self._ok.setFixedWidth(100)
        self._ok.setEnabled(False)
        cancel.setAutoDefault(True)
        cancel.setDefault(True)
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
        self._map.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 06/06/2025 >
        self.setModal(True)

    # Private method

    def _mapAdded(self):
        if self._map.isEmpty():
            self._anat.setEnabled(False)
            self._anat.clear()
            self._anat.setEnabled(False)
            self._anat.setVisible(False)
        else:
            smap = SisypheVolume()
            filename = self._map.getFilename()
            smap.load(filename)
            if smap.hasSameID(getID_ICBM152()):
                self._anat.setEnabled(False)
                self._anat.setVisible(False)
                self._template.setVisible(False)
                self._regsettings.setVisible(False)
                self._resamplesettings.setVisible(False)
                if not self._lmask.isEmpty() and not self._rmask.isEmpty(): self._ok.setEnabled(True)
                else: self._ok.setEnabled(False)
            else:
                self._anat.setEnabled(True)
                self._anat.setVisible(True)
                self._anat.filterSameID(smap.getID())
                self._template.setVisible(True)
                smap.setFilenameSuffix('mean')
                if exists(smap.getFilename()):
                    self._anat.open(smap.getFilename())
        self._center(None)

    def _anatAdded(self):
        if self._anat.isEmpty():
            self._regsettings.setVisible(False)
            self._resamplesettings.setVisible(False)
            self._ok.setEnabled(False)
        else:
            anat = SisypheVolume()
            anat.load(self._anat.getFilename())
            if anat.hasTransform(getID_ICBM152()):
                self._template.setVisible(False)
                self._regsettings.setVisible(False)
                self._resamplesettings.setVisible(True)
                if (not self._lmask.isEmpty() and
                        not self._rmask.isEmpty() and
                        not self._map.isEmpty()): self._ok.setEnabled(True)
                else: self._ok.setEnabled(False)
            else:
                self._template.setVisible(True)
                self._regsettings.setVisible(True)
                self._resamplesettings.setVisible(True)
                if (not self._lmask.isEmpty() and
                        not self._rmask.isEmpty() and
                        not self._map.isEmpty() and
                        not self._anat.isEmpty()): self._ok.setEnabled(True)
                else: self._ok.setEnabled(False)
        self._center(None)

    # < Revision 15/10/2025
    # add _okEnabled method
    def _okEnabled(self):
        r =  (not self._lmask.isEmpty() and not self._rmask.isEmpty() and not self._map.isEmpty())
        if self._anat.isVisible(): r = r and not self._anat.isEmpty()
        if self._template.isVisible(): r = r and not self._template.isEmpty()
        self._ok.setEnabled(r)
    # Revision 15/10/2025 >

    def _settingsAdded(self, widget):
        if widget.getTextLabel() == 'Left mask':
            if not widget.isEmpty():
                filename = widget.getFilename()
                if exists(filename): self._lmask.open(filename)
        elif widget.getTextLabel() == 'Right mask':
            if not widget.isEmpty():
                filename = widget.getFilename()
                if exists(filename): self._rmask.open(filename)
        elif widget.getTextLabel() == 'Template':
            if not widget.isEmpty():
                filename = widget.getFilename()
                if exists(filename): self._template.open(filename)

    def _maskTypeChanged(self):
        self._lmask.clear()
        self._rmask.clear()
        self._ok.setEnabled(False)
        if self._settings.getParameterWidget('MaskType').currentText() == 'PySisyphe volume':
            self._lmask.filterSisypheVolume()
            self._rmask.filterSisypheVolume()
        else:
            self._lmask.filterSisypheROI()
            self._rmask.filterSisypheROI()

    def _registration(self):
        dialog = DialogRegistration()
        if not self._template.isEmpty(): dialog.setFixed(self._template.getFilename(), editable=False)
        else: return None
        if not self._anat.isEmpty(): dialog.setMoving(self._anat.getFilename(), editable=False)
        else: return None
        if not self._map.isEmpty():
            # noinspection PyProtectedMember
            dialog._applyToSelect.add(self._map.getFilename())
        else: return None
        settings = dict()
        settings['registration'] = self._regsettings.getParametersDict()
        settings['resample'] = self._resamplesettings.getParametersDict()
        settings['resample']['Prefix'] = settings['resample']['NormalizationPrefix']
        settings['resample']['Suffix'] = settings['resample']['NormalizationSuffix']
        dialog.setParametersFromDict(settings)
        dialog.execute()
        filename = addPrefixSuffixToFilename(self._map.getFilename(),
                                             settings['resample']['NormalizationPrefix'],
                                             settings['resample']['NormalizationSuffix'])

        if exists(filename):
            rmap = SisypheVolume()
            rmap.load(filename)
            return rmap
        else: return None

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def setScreenshotsWidget(self, widget):
        self._sshot = widget

    def getScreenshotsWidget(self):
        return self._sshot

    def hasScreenshotsWidget(self):
        return self._sshot is not None

    def execute(self):
        rmap = None
        if not self._map.isEmpty() and not self._lmask.isEmpty() and not self._rmask.isEmpty():
            smap = SisypheVolume()
            filename = self._map.getFilename()
            smap.load(filename)
            rfilename = addPrefixSuffixToFilename(filename,
                                                  self._resamplesettings.getParameterValue('NormalizationPrefix'),
                                                  self._resamplesettings.getParameterValue('NormalizationSuffix'))
            if smap.acquisition.isICBM152(): rmap = smap
            elif exists(rfilename):
                rmap = SisypheVolume()
                rmap.load(rfilename)
            elif smap.hasTransform(getID_ICBM152()):
                f = SisypheApplyTransform()
                interpol = self._resamplesettings.getParameterValue('Interpolator')[0]
                if interpol == 'NearestNeighbor': f.setInterpolator('nearest')
                elif interpol == 'Linear': f.setInterpolator('linear')
                elif interpol == 'Bspline': f.setInterpolator('bspline')
                elif interpol == 'Gaussian': f.setInterpolator('gaussian')
                elif interpol == 'HammingSinc': f.setInterpolator('hammingsinc')
                elif interpol == 'CosineSinc': f.setInterpolator('cosinesinc')
                elif interpol == 'WelchSinc': f.setInterpolator('welchsinc')
                elif interpol == 'LanczosSinc': f.setInterpolator('lanczossinc')
                elif interpol == 'BlackmanSinc': f.setInterpolator('blackmansinc')
                else: f.setInterpolator('linear')
                f.setInterpolator(interpol)
                f.setTransform(smap.getTransformFromID(getID_ICBM152()))
                f.setMoving(smap)
                rmap = f.resampleMoving(prefix=self._resamplesettings.getParameterValue('NormalizationPrefix'),
                                        suffix=self._resamplesettings.getParameterValue('NormalizationSuffix'))
            else:
                if not self._anat.isEmpty() and not self._template.isEmpty():
                    # noinspection PyNoneFunctionAssignment
                    rmap = self._registration()
                else:
                    self._ok.setEnabled(False)
                    if self._anat.isEmpty(): messageBox(self, title=self.windowTitle(), text='No fMRI EPI image.')
                    elif self._template.isEmpty(): messageBox(self, title=self.windowTitle(),
                                                              text='No ICBM152 template\nSee in laterality index settings.')
        else:
            self._ok.setEnabled(False)
            if self._map.isEmpty(): messageBox(self, title=self.windowTitle(), text='No statistical map.')
            elif self._lmask.isEmpty(): messageBox(self, title=self.windowTitle(), text='No left mask.')
            elif self._rmask.isEmpty(): messageBox(self, title=self.windowTitle(), text='No right mask.')
        if rmap is not None:
            if self._settings.getParameterValue('MaskType')[0] == 'volume (.xvol)':
                v = SisypheVolume()
                v.load(self._lmask.getFilename())
                lmask = v.getNumpy().flatten() > 0
                v = SisypheVolume()
                v.load(self._rmask.getFilename())
                rmask = v.getNumpy().flatten() > 0
            else:
                v = SisypheROI()
                v.load(self._lmask.getFilename())
                lmask = v.getNumpy().flatten() > 0
                v = SisypheROI()
                v.load(self._rmask.getFilename())
                rmask = v.getNumpy().flatten() > 0
            # < Revision 28/04/2026
            if self._settings.getParameterValue('ApplyMask'):
                masked = lmask + rmask
                masked = masked * rmap.getNumpy().flatten()
                v = SisypheVolume()
                v.copyFromNumpyArray(masked.reshape(rmap.getSize()[::-1]),
                                     spacing=rmap.getSpacing(),
                                     origin=rmap.getOrigin(),
                                     direction=rmap.getDirections())
                v.copyAttributesFrom(rmap)
                v.setFilename(rmap.getFilename())
                v.setFilenameSuffix('masked')
                v.save()
            # Revision 28/04/2026 >
            dlg = DialogGenericResults()
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(dlg, c)
                # noinspection PyUnresolvedReferences
                dlg.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
            title = 'Lateraly index'.format(rmap.getBasename())
            tab1 = dlg.newTab(title, capture=True, clipbrd=True, scrshot=self._sshot, dataset=True)
            # Chart
            fig = dlg.getFigure(tab1)
            fig.set_layout_engine('constrained')
            fig.clear()
            img = rmap.getNumpy().flatten()
            limg = img[lmask]
            rimg = img[rmask]
            vmax = max(limg.max(), rimg.max())
            bins = self._settings.getParameterValue('HistogramBins')
            ax = fig.add_subplot(111, anchor='C')
            hl, bl, _ = ax.hist(limg, bins=bins, range=(0.0, vmax), density=False,
                               histtype='step', cumulative=-1, label='Left mask', color='r', lw=2.0)
            hr, br, _ = ax.hist(rimg, bins=bins, range=(0.0, vmax), density=False,
                               histtype='step', cumulative=-1, label='Right mask', color='b', lw=2.0)
            # AUC LI
            al = hl.cumsum()[-1]
            ar = hr.cumsum()[-1]
            li = round(float((al - ar) / (al + ar)), 2)
            # Average LI
            li2 = (hl - hr) / (hl + hr)
            ali = round(float(li2.mean()), 2)
            # LI p = 0.05 / 0.01 / 0.001
            v3 = v4 = v5 = ''
            li3 = li4 = li5 = None
            if rmap.acquisition.isZMap():
                ax.set_xlabel('z-value')
                v = pvalueToz(0.05)
                v3 = ' (z = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li3 = li2[index]
                v = pvalueToz(0.01)
                v4 = ' (z = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li4 = li2[index]
                v = pvalueToz(0.001)
                v5 = ' (z = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li5 = li2[index]
            elif rmap.acquisition.isTMap():
                ax.set_xlabel('t-value')
                dof = rmap.acquisition.getDegreesOfFreedom()
                v = pvalueTot(0.05, dof)
                v3 = ' (t = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li3 = li2[index]
                v = pvalueTot(0.01, dof)
                v4 = ' (t = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li4 = li2[index]
                v = pvalueTot(0.001, dof)
                v5 = ' (t = {})'.format(round(v, 2))
                n = argwhere(bl > v)
                if len(n) > 0:
                    index = n[0][0]
                    if index > 1: index -= 1
                    li5 = li2[index]
            ax.legend()
            # ax.set_ylabel('Number of voxels', rotation=-90, va="bottom")
            ax.set_ylabel('Number of voxels')
            fig.suptitle('AUC Laterality index {}'.format(li))
            # Table
            dlg.setTreeWidgetHeaderLabels(index=tab1, labels=['Criteria', 'Values'])
            dlg.addTreeWidgetRow(0, ['AUC left mask', int(al)])
            dlg.addTreeWidgetRow(0, ['AUC right mask', int(ar)])
            if li3 is not None: dlg.addTreeWidgetRow(0, ['LI p = 0.05{}'.format(v3), li3], d=2)
            if li4 is not None: dlg.addTreeWidgetRow(0, ['LI p = 0.01{}'.format(v4), li4], d=2)
            if li5 is not None: dlg.addTreeWidgetRow(0, ['LI p = 0.001{}'.format(v5), li5], d=2)
            dlg.addTreeWidgetRow(0, ['Average LI', ali], d=2)
            dlg.addTreeWidgetRow(0, ['AUC LI', li], d=2)
            dlg.exec()
            # Exit
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to calculate\nanother laterality index ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._map.clear()
                self._ok.setEnabled(False)
            else: self.accept()

    # < Revision 15/10/2025
    # add getFilesSelectionWidget method
    def getFilesSelectionWidget(self):
        widgets = dict()
        widgets['map'] = self._map
        widgets['anat'] = self._anat
        widgets['template'] = self._template
        widgets['lmask'] = self._lmask
        widgets['rmask'] = self._rmask
        return widgets
    # Revision 15/10/2025 >