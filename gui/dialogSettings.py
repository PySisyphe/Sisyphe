"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.functionsSettingsWidget import SettingsWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget

__all__ = ['DialogSetting',
           'DialogFunctionSetting',
           'DialogSettings']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogSetting
              -> DialogSetting -> DialogFunctionSetting
              -> DialogSettings
"""


class DialogSetting(QDialog):
    """
    DialogSetting

    Description
    ~~~~~~~~~~~

    GUI dialog window to manage one section of application settings (settings.xml).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSetting

    Last revision: 30/03/2025
    """

    # Class method

    @classmethod
    def formatLabel(cls, label):
        if isinstance(label, str):
            if label.isupper(): r = label
            else:
                r = ''
                for c in label:
                    if c.isupper(): r += ' {}'.format(c)
                    else: r += c
                r = r.lstrip().capitalize()
            return r
        else: raise TypeError('parameter type {} is not str.'.format(type(label)))

    # Special method

    def __init__(self, section='', parent=None):
        super().__init__(parent)

        self.setWindowTitle(self.formatLabel(section))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widget

        if section != '':
            self._widget = SettingsWidget(section)
            self._widget.setButtonsVisibility(False)
            self._layout.addWidget(self._widget)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)
        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()
        self._layout.addLayout(layout)
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

        # < Revision 30/03/2025
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())
        # Revision 30/03/2025 >

    # Public method

    def getSettingsWidget(self):
        return self._widget


class DialogFunctionSetting(DialogSetting):
    """
    DialogFunctionSetting

    Description
    ~~~~~~~~~~~

    GUI dialog window to manage one section of function settings (functions.xml).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSetting -> DialogFunctionSetting
    """

    # Special method

    def __init__(self, section='', parent=None):
        super().__init__('', parent)

        if section != '':
            self._widget = FunctionSettingsWidget(section)
            self._widget.setButtonsVisibility(False)
            self._layout.insertWidget(0, self._widget)


class DialogSettings(QDialog):
    """
    DialogSettings

    Description
    ~~~~~~~~~~~

    GUI dialog window to manage PySisyphe preferences.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSettings

    Last revision: 30/03/2025
    """

    # Class method

    @classmethod
    def formatLabel(cls, label):
        if isinstance(label, str):
            if label.isupper(): r = label
            else:
                r = ''
                for c in label:
                    if c.isupper(): r += ' {}'.format(c)
                    else: r += c
                r = r.lstrip().capitalize()
            return r
        else: raise TypeError('parameter type {} is not str.'.format(type(label)))

    # Special method

    """
     Private attributes

    _splitter       QSplitter
    _sections       QTreeWidget
    _stack          QStackedWidget
    _mainwindow     windowSisyphe, PySisyphe main window
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Preferences')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.5))
        self.setMinimumHeight(int(screen.height() * 0.5))
        self._mainwindow = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._splitter = QSplitter()
        self._sections = QTreeWidget()
        self._sections.header().setVisible(False)
        self._sections.setSelectionMode(QTreeWidget.SingleSelection)
        self._sections.adjustSize()
        self._stack = QStackedWidget()
        self._splitter.addWidget(self._sections)
        self._splitter.addWidget(self._stack)
        self._layout.addWidget(self._splitter)
        self._initSettings()

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._cancel = QPushButton('Cancel')
        self._cancel.setFixedWidth(100)
        self._cancel.setAutoDefault(True)
        self._cancel.setDefault(True)
        self._apply = QPushButton('Apply')
        self._apply.setFixedWidth(100)
        self._apply.setEnabled(False)
        self._default = QPushButton('Default')
        self._default.setFixedWidth(100)
        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addWidget(self._apply)
        layout.addWidget(self._default)
        layout.addStretch()
        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._apply.clicked.connect(self.apply)
        # noinspection PyUnresolvedReferences
        self._default.clicked.connect(self.default)

        # < Revision 30/03/2025
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())
        # Revision 30/03/2025 >

    # Private methods

    def _initSettings(self):
        fitems = dict()
        # Settings
        fitems['General'] = QTreeWidgetItem()
        settings = SisypheSettings()
        sections = settings.getSectionsList()
        for section in sections:
            widget = SettingsWidget(section)
            widget.setObjectName(section)
            widget.settingsVisibilityOn()
            widget.setSettingsButtonFunctionText()
            widget.hideButtons()
            widget.ParameterChanged.connect(lambda dummy: self._apply.setEnabled(True))
            scroll = QScrollArea()
            scroll.setWidget(widget)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setAlignment(Qt.AlignHCenter)
            self._stack.addWidget(scroll)
            item = QTreeWidgetItem()
            item.setText(0, self.formatLabel(section))
            item.setData(0, Qt.UserRole, self._stack.count() - 1)
            fitems['General'].addChild(item)
            self._sections.addTopLevelItem(fitems['General'])
        # Functions
        fitems['Filters'] = QTreeWidgetItem()
        fitems['Segmentation'] = QTreeWidgetItem()
        fitems['Registration'] = QTreeWidgetItem()
        # < Revision 18/02/2025
        # add mapping settings
        fitems['Mapping'] = QTreeWidgetItem()
        # Revision 18/02/2025 >
        fitems['Diffusion'] = QTreeWidgetItem()
        for k in fitems:
            fitems[k].setText(0, k)
            fitems[k].setData(0, Qt.UserRole, -1)
            self._sections.addTopLevelItem(fitems[k])
        settings = SisypheFunctionsSettings()
        functions = settings.getSectionsList()
        for function in functions:
            widget = FunctionSettingsWidget(function)
            widget.settingsVisibilityOn()
            widget.setSettingsButtonFunctionText()
            widget.hideButtons()
            scroll = QScrollArea()
            scroll.setWidget(widget)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setAlignment(Qt.AlignHCenter)
            self._stack.addWidget(scroll)
            item = QTreeWidgetItem()
            item.setText(0, self.formatLabel(function))
            item.setData(0, Qt.UserRole, self._stack.count() - 1)
            if function in ('RemoveNeckSlices',
                            'MeanImageFilter',
                            'MedianImageFilter',
                            'GaussianImageFilter',
                            'GradientMagnitudeImageFilter',
                            'LaplacianImageFilter',
                            'AnisotropicDiffusionImageFilter',
                            'RegressionIntensityMatchingImageFilter',
                            'HistogramIntensityMatchingImageFilter',
                            'IntensityNormalizationImageFilter',
                            'BiasFieldCorrectionImageFilter'):
                fitems['Filters'].addChild(item)
            elif function in ('SkullStripping',
                              'KMeansClustering',
                              'KMeansSegmentation',
                              'PriorBasedSegmentation',
                              'CorticalThickness',
                              'RegistrationBasedSegmentation',
                              'UnetHippocampusSegmentation',
                              'UnetMedialTemporalSegmentation',
                              'UnetLesionSegmentation',
                              'UnetWMHSegmentation'):
                if function == 'KMeansClustering': item.setText(0, 'KMeans clustering')
                elif function == 'KMeansSegmentation': item.setText(0, 'KMeans segmentation')
                elif function == 'UnetWMHSegmentation': item.setText(0, 'Unet WMH segmentation')
                fitems['Segmentation'].addChild(item)
            elif function in ('Registration',
                              'T1Normalization',
                              'T2Normalization',
                              'PDNormalization',
                              'PTNormalization',
                              'NMNormalization',
                              'GMNormalization',
                              'WMNormalization',
                              'CSFNormalization',
                              'EddyCurrent',
                              'Realignment',
                              'Resample',
                              'DisplacementFieldJacobianDeterminant'):
                if function == 'PDNormalization': item.setText(0, 'PD normalization')
                elif function == 'PTNormalization': item.setText(0, 'PET normalization')
                elif function == 'NMNormalization': item.setText(0, 'SPECT normalization')
                elif function == 'GMNormalization': item.setText(0, 'GM map normalization')
                elif function == 'WMNormalization': item.setText(0, 'WM map normalization')
                elif function == 'CSFNormalization': item.setText(0, 'CSF map normalization')
                fitems['Registration'].addChild(item)
            # < Revision 18/02/2025
            # add mapping settings
            elif function in ('Conjunction',
                              'TimeSeriesPreprocessing',
                              'TimeSeriesFastICA',
                              'TimeSeriesGroupICA',
                              'TimeSeriesSeedToVoxel',
                              'TimeSeriesConnectivityMatrix',
                              'Perfusion'):
                if function == 'TimeSeriesPreprocessing':
                    item.setText(0, 'Clean time series')
                    widget.setParameterVisibility('TissueMap', False)
                    widget.setParameterVisibility('DCM', False)
                elif function == 'TimeSeriesFastICA': item.setText(0, 'Single-subject time series ICA')
                elif function == 'TimeSeriesGroupICA': item.setText(0, 'Multi-subject time series ICA')
                elif function == 'TimeSeriesSeedToVoxel':
                    item.setText(0, 'Seed-to-voxel time series correlation')
                    widget.setParameterVisibility('Seed', False)
                elif function == 'TimeSeriesConnectivityMatrix':
                    item.setText(0, 'Time series correlation matrix')
                    widget.setParameterVisibility('Label', False)
                elif function == 'Perfusion':
                    item.setText(0, 'Dynamic susceptibility contrast')
                    widget.setParameterVisibility('DCM', False)
                fitems['Mapping'].addChild(item)
            # Revision 18/02/2025 >
            elif function in ('DiffusionPreprocessing',
                              'PCADenoise',
                              'NLMeansDenoise',
                              'SelfSupervisedDenoise',
                              'DiffusionModel',
                              'DTIModel',
                              'DKIModel',
                              'SHCSAModel',
                              'SHCSDModel',
                              'Tracking',
                              'BundleROISelection',
                              'BundleAtlasSelection',
                              'BundleToROI',
                              'BundleFiltering',
                              'BundleClustering'):
                if function == 'PCADenoise': item.setText(0, 'PCA denoise')
                elif function == 'NLMeansDenoise': item.setText(0, 'NLMeans denoise')
                elif function == 'DTIModel': item.setText(0, 'DTI model')
                elif function == 'DKIModel': item.setText(0, 'DKI model')
                elif function == 'SHCSAModel': item.setText(0, 'SHCSA model')
                elif function == 'SHCSDModel': item.setText(0, 'SHCSD model')
                elif function == 'BundleROISelection': item.setText(0, 'Bundle ROI selection')
                elif function == 'BundleToROI': item.setText(0, 'Bundle to ROI')
                elif function == 'Tracking':
                    widget.setParameterVisibility('SeedROI', False)
                    widget.setParameterVisibility('StoppingROI', False)
                    widget.setParameterVisibility('StoppingGM', False)
                    widget.setParameterVisibility('StoppingWM', False)
                    widget.setParameterVisibility('StoppingCSF', False)
                fitems['Diffusion'].addChild(item)
        self._sections.setCurrentItem(self._sections.topLevelItem(0))
        # noinspection PyUnresolvedReferences
        self._sections.currentItemChanged.connect(self._currentSelectedChanged)

    # noinspection PyUnusedLocal
    def _currentSelectedChanged(self, current, previous):
        index = current.data(0, Qt.UserRole)
        if index >= 0: self._stack.setCurrentIndex(index)

    # Public method

    def default(self):
        c = self._sections.currentItem().data(0, Qt.UserRole)
        widget = self._stack.widget(c).widget()
        widget.resetSettings(default=True)

    def save(self):
        for i in range(self._stack.count()):
            widget = self._stack.widget(i).widget()
            widget.saveSettings()

    def apply(self):
        if self.hasMainWindow():
            window = self.getMainWindow()
            # < Revision 18/02/2025
            #  c = self._sections.currentItem().data(0, Qt.UserRole)
            widget = self._stack.currentWidget().widget()
            if widget is not None:
                c = widget.objectName()
                # Revision 18/02/2025 >
                if c == 'GUI':
                    v = widget.getParameterValue('ToolbarSize')
                    if v is not None: window.setToolbarSize(v)
                    v = widget.getParameterValue('ThumbnailSize')
                    if v is not None: window.setThumbnailSize(v)
                    v = widget.getParameterValue('IconSize')
                    if v is not None: window.setDockIconSize(v)
                    v = widget.getParameterValue('ToolbarVisibility')
                    if v is not None: window.setToolbarVisibility(v)
                    # < Revision 15/03/2025
                    # font and help zoom factor management
                    v1 = widget.getParameterValue('FontFamily')
                    if v1 is None: v1 = self.font().family()
                    v2 = widget.getParameterValue('FontSize')
                    if v2 is None: v2 = 12
                    window.setApplicationFont(v1.family(), v2)
                    v = widget.getParameterValue('ZoomFactor')
                    if v is not None: window.setHelpZoomFactor(v)
                    # Revision 15/03/2025 >
                elif c == 'ToolbarIcons':
                    actions = window.getActions()
                    toolbar = window.getToolbar()
                    toolbar.clear()
                    params = widget.getParametersList()
                    for p in params:
                        if widget.getParameterValue(p):
                            toolbar.addAction(actions[p])
                        if p == 'dcmimport':
                            if len(toolbar.actions()) > 0: toolbar.addSeparator()
                        elif p == 'lutedit':
                            n = len(toolbar.actions())
                            if n > 0 and not toolbar.actions()[n - 1].isSeparator(): toolbar.addSeparator()
                    n = len(toolbar.actions())
                    if n > 0 and toolbar.actions()[n - 1].isSeparator(): toolbar.removeAction(toolbar.actions()[n - 1])
                    if n == 0: toolbar.setVisible(False)
                elif c == 'Viewport':
                    # < Revision 17/03/2025
                    # add icon size and font size scale management
                    v = widget.getParameterValue('IconSize')
                    if v is not None: window.setIconBarSize(v)
                    v = widget.getParameterValue('FontSizeScale')
                    if v is not None:  window.setViewportsFontScale(v)
                    # Revision 17/03/2025 >
                    v = widget.getParameterValue('LineWidth')
                    if v is not None: window.setViewportsLineWidth(v)
                    v = widget.getParameterValue('LineOpacity')
                    if v is not None: window.setViewportsLineOpacity(v)
                    v = widget.getParameterValue('LineColor')
                    if v is not None: window.setViewportsLineColor(v)
                    v = widget.getParameterValue('LineSelectedColor')
                    if v is not None: window.setViewportsLineSelectedColor(v)
                    v = widget.getParameterValue('CursorVisibility')
                    if v is not None: window.setViewportsCursorVisibility(v)
                    v = widget.getParameterValue('AttributesVisibility')
                    if v is not None: window.setViewportsAttributesVisibility(v)
                    v = widget.getParameterValue('IdentityAttributesVisibility')
                    if v is not None: window.setViewportsInfoIdentityVisibility(v)
                    v = widget.getParameterValue('VolumeAttributesVisibility')
                    if v is not None: window.setViewportsInfoVolumeVisibility(v)
                    v = widget.getParameterValue('AcquisitionAttributesVisibility')
                    if v is not None: window.setViewportsInfoAcquisitionVisibility(v)
                    v = widget.getParameterValue('VoxelValueVisibility')
                    if v is not None: window.setViewportsInfoValueVisibility(v)
                    v = widget.getParameterValue('CoorWorldVisibility')
                    if v is not None: window.setViewportsInfoPositionVisibility(v)
                    v = widget.getParameterValue('CoorACVisibility')
                    if v is not None: window.setViewportsRelativeACCoordinatesVisibility(v)
                    v = widget.getParameterValue('CoorPCVisibility')
                    if v is not None: window.setViewportsRelativePCCoordinatesVisibility(v)
                    v = widget.getParameterValue('CoorACPCVisibility')
                    if v is not None: window.setViewportsRelativeACPCCoordinatesVisibility(v)
                    v = widget.getParameterValue('CoorFrameVisibility')
                    if v is not None: window.setViewportsFrameCoordinatesVisibility(v)
                    v = widget.getParameterValue('CoorICBMVisibility')
                    if v is not None: window.setViewportsICBMCoordinatesVisibility(v)
                    v = widget.getParameterValue('ColorbarPosition')
                    if v is not None: window.setViewportsColorbarPosition(v[0])
                    v = widget.getParameterValue('ColorbarVisibility')
                    if v is not None: window.setViewportsColorbarVisibility(v)
                    v = widget.getParameterValue('RulerPosition')
                    if v is not None: window.setViewportsRulerPosition(v[0])
                    v = widget.getParameterValue('RulerVisibility')
                    if v is not None: window.setViewportsRulerVisibility(v)
                    v = widget.getParameterValue('TooltipVisibility')
                    if v is not None: window.setViewportsTooltipVisibility(v)
                    v = widget.getParameterValue('OrientationLabelsVisibility')
                    if v is not None: window.setViewportsOrientationLabelsVisibility(v)
                    v = widget.getParameterValue('OrientationMarkerShape')
                    if v is not None: window.setViewportsOrientationMarkerShape(v[0])
                    v = widget.getParameterValue('OrientationMarkerVisibility')
                    if v is not None: window.setViewportsOrientationMarkerVisibility(v)
                    v = widget.getParameterValue('Align')
                    if v is not None: window.setViewportsAlign(v)
        self._apply.setEnabled(False)

    def accept(self):
        self.save()
        super().accept()

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe):
            self._mainwindow = w
        else: raise TypeError('parameter type {} is not windowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None
