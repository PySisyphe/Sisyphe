"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QStackedWidget

from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.functionsSettingsWidget import SettingsWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget

__all__ = ['DialogSetting',
           'DialogSettings']

"""
    Class hierarchy

        QDialog -> DialogSetting
                -> DialogSettings

"""


class DialogSetting(QDialog):
    """
         DialogSetting

         Description

             GUI dialog window to manage one section preferences.

         Inheritance

             QDialog -> DialogSetting

         Public methods

            SettingsWidget = getSettingWidget()

            inherited QDialog methods
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

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widget

        self._widget = SettingsWidget(section)
        self._widget.setButtonsVisibility(False)
        self._layout.addWidget(self._widget)

        # Init default dialog buttons

        layout = QHBoxLayout()
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
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Qt Signals

        self._ok.clicked.connect(self.accept)
        self._cancel.clicked.connect(self.reject)

    # Public method

    def getSettingsWidget(self):
        return self._widget


class DialogSettings(QDialog):
    """
         DialogSettings

         Description

             GUI dialog window to manage PySisyphe preferences.

         Inheritance

             QDialog -> DialogSettings

         Private attributes

            _mainwindow     windowSisyphe, PySisyphe main window

         Public methods

            accept()
            setMainWindow(windowSisyphe)
            windowSisyphe = getMainWindow()
            bool = hasMainWindow()

            inherited QDialog methods
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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Preferences')
        self.resize(QSize(800, 400))
        self.setFixedHeight(400)
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
        self._stack = QStackedWidget()
        self._splitter.addWidget(self._sections)
        self._splitter.addWidget(self._stack)
        self._layout.addWidget(self._splitter)
        self._initSettings()

        # Init default dialog buttons

        layout = QHBoxLayout()
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

        self._ok.clicked.connect(self.accept)
        self._cancel.clicked.connect(self.reject)
        self._apply.clicked.connect(self.apply)
        self._default.clicked.connect(self.default)

    # Private methods

    def _initSettings(self):
        # Settings
        settings = SisypheSettings()
        sections = settings.getSectionsList()
        for section in sections:
            widget = SettingsWidget(section)
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
            self._sections.addTopLevelItem(item)
        # Functions
        fitems = dict()
        fitems['Filters'] = QTreeWidgetItem()
        fitems['Segmentation'] = QTreeWidgetItem()
        fitems['Registration'] = QTreeWidgetItem()
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
            if function in ('MeanImageFilter',
                            'MedianImageFilter',
                            'GaussianImageFilter',
                            'GradientMagnitudeImageFilter',
                            'LaplacianImageFilter',
                            'AnisotropicDiffusionImageFilter',
                            'HistogramMatchingImageFilter',
                            'BiasFieldCorrectionImageFilter'):
                fitems['Filters'].addChild(item)
            elif function in ('UnsupervisedKMeans',
                              'SupervisedKMeans',
                              'FiniteMixtureModel'):
                fitems['Segmentation'].addChild(item)
            elif function in ('Registration',
                              'Realignment',
                              'Resample',
                              'DisplacementFieldJacobianDeterminant'):
                fitems['Registration'].addChild(item)
        self._sections.setCurrentItem(self._sections.topLevelItem(0))
        self._sections.currentItemChanged.connect(self._currentSelectedChanged)

    def _currentSelectedChanged(self, current, previous):
        index = current.data(0, Qt.UserRole)
        if index >= 0: self._stack.setCurrentIndex(index)

    # Public method

    def default(self):
        c = self._sections.currentItem().data(0, Qt.UserRole)
        widget = self._stack.widget(c).widget()
        widget.resetSettings(default=True)

    def save(self):
        self.apply()
        for i in range(self._stack.count()):
            widget = self._stack.widget(i).widget()
            widget.saveSettings()

    def apply(self):
        if self.hasMainWindow():
            window = self.getMainWindow()
            c = self._sections.currentItem().data(0, Qt.UserRole)
            widget = self._stack.widget(c).widget()
            if c == 0:  # GUI
                v = widget.getParameterValue('ToolbarSize')
                if v is not None: window.setToolbarSize(v)
                v = widget.getParameterValue('ThumbnailSize')
                if v is not None: window.setThumbnailSize(v)
                v = widget.getParameterValue('IconSize')
                if v is not None: window.setDockIconSize(v)
                v = widget.getParameterValue('ToolbarVisibility')
                if v is not None: window.setToolbarVisibility(v)
            elif c == 1:  # ToolbarIcons
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
            elif c == 2:  # Viewport
                v = widget.getParameterValue('FontSize')
                if v is not None: window.setViewportsFontSize(v)
                v = widget.getParameterValue('FontFamily')
                if v is not None: window.setViewportsFontFamily(v[0])
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
        self._apply.setEnabled(False)

    def accept(self):
        self.save()
        self.close()

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe):
            self._mainwindow = w
        else: raise TypeError('parameter type {} is not windowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogSettings()
    main.show()
    app.exec_()
