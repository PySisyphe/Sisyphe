"""
External packages/modules
-------------------------

    - darkdetect, OS Dark Mode detection, https://github.com/albertosottile/darkdetect
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from typing import Any

from os import getcwd
from os import chdir

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import abspath

from datetime import date
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QDate
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

import darkdetect

from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.core.sisypheSettings import SisypheDialogsSettings
from Sisyphe.core.sisypheSettings import SisypheCustomSettings
from Sisyphe.core.sisypheSettings import SisypheTooltips
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.basicWidgets import ColorSelectPushButton
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import VisibilityLabel
from Sisyphe.widgets.basicWidgets import FontSelect
from Sisyphe.widgets.LUTWidgets import ComboBoxLut

__all__ = ['SettingsWidget',
           'FunctionSettingsWidget',
           'DialogSettingsWidget',
           'CustomSettingsWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QWidget -> SettingsWidget -> FunctionSettingsWidget
"""

# < Revision 12/06/2025
# class used to remove unnecessary decimals from QDoubleSpinBox
class QDoubleSpinBox2(QDoubleSpinBox):

    def textFromValue(self, v: float) -> str:
        """
        Convert a float value to its text representation, removing trailing zeros.

        Parameters
        ----------
        v : float
            value to convert.

        Returns
        -------
        str
            formatted string representation of the value.
        """
        # noinspection PyTypeChecker
        f = QLocale(QLocale.English, QLocale.UnitedStates)
        f.setNumberOptions(QLocale.OmitGroupSeparator)
        return f.toString(v, 'g', QLocale.FloatingPointShortest)
# Revision 12/06/2025 >

class SettingsWidget(QWidget):
    """
    SettingsWidget class

    Description
    ~~~~~~~~~~~

    Widget to manage application settings from an XML file (settings.xml).
    This widget displays a list of the parameters of a function/section, i.e. first level node of the XML file.

    It has a main button that toggles the visibility of the parameters, as well as four IO buttons:

    - 'Reset': Reset the settings to their default values from a settings file.
    - 'Load': load settings from a custom XML file.
    - 'Save': save the current settings to the user's default settings file (~/.PySisyphe/settings.xml)
    - 'Save As': save the current settings to a custom XML file.

    Parameter types in the settings.xml are as follows:

    - str, represented by a QLineEdit widget
    - int, represented by a QSpinBox widget
    - float, represented by a QDoubleSpinBox2 widget
    - percent, percent parameter (0 to 100), represented by a QSlider widget
    - bool, represented by a QCheckBox widget
    - visibility, two states parameter i.e. show/hide, represented by a VisibilityLabel widget
    - lstr, list of str, represented by QComboBox widgets
    - lint, list of int, represented by multiple QSpinBox widgets
    - lfloat,list of float, represented by multiple QDoubleSpinBox widgets
    - lbool, list of bool, represented by multiple QComboBox (True/False items) widgets
    - color, represented by a ColorSelectPushButton widget
    - lut, lut name, represented by a ComboBoxLut widget
    - font, font name, represented by a FontSelect widget
    - date, date str, represented by a QDateEdit widget
    - vol, PySisyphe volume file name, represented by a FileSelectionWidget
    - roi, PySisyphe ROI file name, represented by a FileSelectionWidget
    - dcm, Dicom file name, represented by a FileSelectionWidget
    - dir, Path, represented by a FileSelectionWidget
    - vols, list of PySisyphe volume file names, represented by a FilesSelectionWidget
    - rois, list of PySisyphe ROI file names, represented by a FilesSelectionWidget
    - dcms, list of Dicom file names, represented by a FilesSelectionWidget
    - dirs, list of paths, represented by a FilesSelectionWidget
    - txt, text file name, represented by a FileSelectionWidget

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SettingsWidget -> FunctionSettingsWidget

    Creation: 11/08/2022
    Last revision: 02/12/2025
    """

    _VSIZE = 24

    classSisypheSettings = SisypheSettings

    # Custom Qt Signals

    ParameterChanged = pyqtSignal(QWidget)
    VisibilityToggled = pyqtSignal(QWidget)

    # Class methods

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Checks if the system is currently in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Checks if the system is currently in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on the current system theme (dark/light).

        Returns
        -------
        str
            absolute path to the icon directory.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    @classmethod
    def getDefaultToolbarIconDirectory(cls) -> str:
        """
        Get the path to the default toolbar icon directory based on the current system theme (dark/light).

        Returns
        -------
        str
            absolute path to the toolbar icon directory.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkicons')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lighticons')

    @classmethod
    def getDefaultIconSize(cls) -> int:
        """
        Get the default icon size based on the current display DPI.

        Returns
        -------
        int
            icon size in pixels.
        """
        dpi = QApplication.primaryScreen().logicalDotsPerInch()
        if dpi > 100: return int(cls._VSIZE * dpi / 800) * 8
        else: return cls._VSIZE

    @classmethod
    def formatLabel(cls, label: str) -> str:
        """
        Reformat a str label: split words using capital letters as separators.

        Parameters
        ----------
        label : str
            label to be formatted.

        Returns
        -------
        str
            reformatted label
        """
        if isinstance(label, str):
            if label.isupper(): r = label
            else:
                r = ''
                # < Revision 07/10/2025
                # for c in label:
                #     if c.isupper(): r += ' {}'.format(c)
                #     else: r += c
                for i in range(len(label) - 1):
                    c0 = label[i]
                    c1 = label[i + 1]
                    if c0.isupper() and c1.islower(): r += ' {}'.format(c0)
                    elif c0.islower() and c1.isupper(): r += '{} '.format(c0)
                    else: r += c0
                r += label[-1]
                r = r.replace('  ', ' ')
                # Revision 07/10/2025
                r = r.lstrip().capitalize()
            return r
        else: raise TypeError('parameter type {} is not str.'.format(type(label)))

    @classmethod
    def getNumberOfDecimals(cls, v: float) -> int:
        """
        Get the number of decimal places in a floating-point number.

        Parameters
        ----------
        v : float
            floating-point number.

        Returns
        -------
        int
            number of decimal places.
        """
        if v == 0.0: return 1
        elif abs(v) < 1e-8: return 8
        else:
            r = len('{:.8f}'.format(v).rstrip('0').split('.')[1])
            if r == 0: r = 1
            return r

    # Special method

    def __init__(self, function: str, parent: QWidget | None = None) -> None:
        """
        SettingsWidget instance constructor.

        Parameters
        ----------
        function : str
            name of the function for which to create the settings widget.
        parent : QWidget | None
            parent widget.
        """
        QWidget.__init__(self, parent)

        self._function = function
        self._iovisibility = True

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._iconup = QIcon(join(self.getDefaultIconDirectory(), 'down2.png'))
        self._icondown = QIcon(join(self.getDefaultIconDirectory(), 'up2.png'))
        self._button = QPushButton(self._icondown, 'Settings...')
        self._button.setToolTip('Show {} settings'.format(self._function))
        self._reset = QPushButton('Reset', parent=self)
        self._reset.setToolTip('Restore default {} settings'.format(self._function))
        self._reset.setVisible(False)
        self._save = QPushButton('Save', parent=self)
        self._save.setToolTip('Save to default {} settings'.format(self._function))
        self._save.setVisible(False)
        self._load = QPushButton('Load...', parent=self)
        self._load.setToolTip('Load custom {} settings'.format(self._function))
        self._load.setVisible(False)
        self._saveas = QPushButton('Save as...', parent=self)
        self._saveas.setToolTip('Save to custom {} settings'.format(self._function))
        self._saveas.setVisible(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._button, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self._reset, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self._save, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self._load, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self._saveas, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addStretch()
        self._layout.addLayout(layout)

        self._parameters = dict()
        self._settingsbox = QWidget(parent=self)
        self._settingsbox.setVisible(False)
        self._initSettingsLayout(function)
        self._layout.addWidget(self._settingsbox)
        # self._layout.addStretch()

        # < Revision 28/11/2025
        # noinspection PyUnresolvedReferences
        self._button.clicked.connect(lambda _: self.toggleSettingsVisibility(True))
        # Revision 28/11/2025 >
        # noinspection PyUnresolvedReferences
        self._reset.clicked.connect(self.resetSettings)
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.saveSettings)
        # noinspection PyUnresolvedReferences
        self._load.clicked.connect(self.loadSettings)
        # noinspection PyUnresolvedReferences
        self._saveas.clicked.connect(self.saveAsSettings)

    """
    Private attributes

    _parameters     dict[str, QWidget], keyword = name of function parameters
    _funcname       str, function name
    """

    # Private methods

    # noinspection PyUnusedLocal
    def _parameterChanged(self, value):
        """
        Slot for handling parameter changes. Emits the ParameterChanged signal.

        Parameters
        ----------
        value : Any
            new value of the parameter (unused).
        """
        # noinspection PyUnresolvedReferences
        self.ParameterChanged.emit(self)

    def _initSettingsLayout(self, function):
        """
        Initialize the settings layout based on the function's parameters from the XML settings file.

        Parameters
        ----------
        function : str
            name of the function.
        """
        # < Revision 19/03/2025
        size = self.getDefaultIconSize()
        # Revision 19/03/2025 >
        xml = self.classSisypheSettings()
        parameters = xml.getSectionFieldsList(function)
        try:
            tooltips = SisypheTooltips()
            title = tooltips.getFieldValue(self._function, 'Title')
            # < Revision 19/10/2025
            # if title is not None:
            if title is not None and len(title) > 0:
                title = title.replace('\t', '')
                # < Revision 24/03/2025
                if title[0] == '\n': title = title[1:]
                if title[-1] == '\n': title = title[:-1]
                # Revision 24/03/2025 >
                self.setToolTip(title)
            # Revision 19/10/2025 >
        except: tooltips = None
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if len(parameters) > 0:
            i = 0
            for parameter in parameters:
                if tooltips is not None:
                    tooltip = tooltips.getFieldValue(self._function, parameter)
                    # < Revision 19/10/2025
                    # if tooltip is not None:
                    if tooltip is not None and len(tooltip) > 0:
                        tooltip = tooltip.replace('\t', '')
                        # < Revision 24/03/2025
                        if tooltip[0] == '\n': tooltip = tooltip[1:]
                        if tooltip[-1] == '\n': tooltip = tooltip[:-1]
                        # Revision 24/03/2025 >
                    else: tooltip = ''
                    # Revision 19/10/2025 >
                else: tooltip = ''
                node = xml.getFieldNode(function, parameter)
                vartype = node.getAttribute('vartype')
                # label attribute
                if vartype not in ('dirs', 'vols', 'rois', 'dcms'):
                    if node.hasAttribute('label'): lb = QLabel(node.getAttribute('label'))
                    else: lb = QLabel(self.formatLabel(parameter), parent=self)
                    # noinspection PyTypeChecker
                    layout.addWidget(lb, i, 0, alignment=Qt.AlignRight)
                else:
                    if node.hasAttribute('label'): lb = node.getAttribute('label')
                    else: lb = self.formatLabel(parameter)
                if node.hasChildNodes():
                    child = node.firstChild
                    # noinspection PyUnresolvedReferences
                    data = child.data
                else: data = ''
                if vartype == 'str':
                    edit = QLineEdit(parent=self)
                    edit.setFixedWidth(300)
                    edit.setText(data)
                    # noinspection PyUnresolvedReferences
                    edit.textChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'int':
                    if node.hasAttribute('varmin'): varmin = int(node.getAttribute('varmin'))
                    else: varmin = None
                    if node.hasAttribute('varmax'): varmax = int(node.getAttribute('varmax'))
                    else: varmax = None
                    edit = QSpinBox(parent=self)
                    edit.setFixedWidth(100)
                    if node.hasAttribute('step'):
                        step = int(node.getAttribute('step'))
                        edit.setSingleStep(step)
                    if varmin is not None and varmax is not None:
                        edit.setMinimum(varmin)
                        edit.setMaximum(varmax)
                    if data == '': data = varmin  # Default
                    edit.setValue(int(data))
                    edit.setAlignment(Qt.AlignCenter)
                    # noinspection PyUnresolvedReferences
                    edit.valueChanged.connect(self._parameterChanged)
                    if tooltip is not None:
                        edit.setToolTip('{}\n\nValue range from {} to {}'.format(tooltip, varmin, varmax))
                    else: edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'float':
                    if node.hasAttribute('varmin'): varmin = float(node.getAttribute('varmin'))
                    else: varmin = None
                    if node.hasAttribute('varmax'): varmax = float(node.getAttribute('varmax'))
                    else: varmax = None
                    # edit = QDoubleSpinBox(parent=self)
                    edit = QDoubleSpinBox2(parent=self)
                    if node.hasAttribute('decimals'): n = int(node.getAttribute('decimals'))
                    # else: n = self.getNumberOfDecimals(varmin)
                    else: n = 1
                    # edit.setDecimals(n)
                    if n > 0: edit.setDecimals(n)
                    if node.hasAttribute('step'): step = float(node.getAttribute('step'))
                    else:
                        # step = 1 / (10**n)
                        if n > 0: step = 1 / (10**n)
                        else: step = 0.1
                    edit.setSingleStep(step)
                    if n > 5: edit.setFixedWidth(20*n)
                    else: edit.setFixedWidth(100)
                    if varmin is not None and varmax is not None:
                        edit.setMinimum(varmin)
                        edit.setMaximum(varmax)
                    if data == '': data = varmin  # Default
                    edit.setValue(float(data))
                    # noinspection PyTypeChecker
                    edit.setAlignment(Qt.AlignCenter)
                    # noinspection PyUnresolvedReferences
                    edit.valueChanged.connect(self._parameterChanged)
                    if tooltip is not None:
                        edit.setToolTip('{}\n\nValue range from {} to {}'.format(tooltip, varmin, varmax))
                    else: edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'percent':
                    lbl2 = QLabel('100 %', parent=self)
                    # noinspection PyTypeChecker
                    edit = QSlider(Qt.Horizontal, parent=self)
                    edit.setToolTip('100 %')
                    edit.setMinimum(0)
                    edit.setMaximum(100)
                    edit.setFixedWidth(100)
                    if data == '': data = 0.0  # Default
                    edit.setValue(int(float(data)*100))
                    # noinspection PyUnresolvedReferences
                    edit.valueChanged.connect(self._parameterChanged)
                    # noinspection PyUnresolvedReferences
                    edit.valueChanged.connect(lambda v, w=edit: w.setToolTip('{} %'.format(v)))
                    # noinspection PyUnresolvedReferences
                    edit.valueChanged.connect(lambda v, w=lbl2: w.setText('{} %'.format(v)))
                    if tooltip is not None: edit.setToolTip(tooltip)
                    lyout = QHBoxLayout()
                    lyout.setSpacing(5)
                    lyout.setContentsMargins(0, 0, 0, 0)
                    lyout.addWidget(edit)
                    lyout.addWidget(lbl2)
                    layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'bool':
                    edit = QCheckBox(parent=self)
                    edit.setTristate(False)
                    if data == '': data = 'False'  # Default
                    # < Revision 02/06/2025
                    # if data == 'True': edit.setCheckState(Qt.Checked)
                    # else: edit.setCheckState(Qt.Unchecked)
                    if data == 'True': edit.setChecked(True)
                    else: edit.setChecked(False)
                    # Revision 02/06/2025 >
                    # noinspection PyUnresolvedReferences
                    edit.stateChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'visibility':
                    if node.hasAttribute('icon'): icn = join(self.getDefaultToolbarIconDirectory(), node.getAttribute('icon'))
                    else: icn = ''
                    edit = VisibilityLabel(parent=self)
                    edit.setFixedSize(QSize(size, size))
                    if data == '': data = 'False'  # Default
                    if data == 'True': edit.setVisibilityStateIconToView()
                    else: edit.setVisibilityStateIconToHide()
                    edit.visibilityChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    lyout = QHBoxLayout()
                    lyout.setSpacing(5)
                    lyout.setContentsMargins(0, 0, 0, 0)
                    if exists(icn): lyout.addWidget(IconPushButton(icon=icn, size=size))
                    lyout.addWidget(edit)
                    layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'lstr':
                    if data != '':
                        edit = QComboBox(parent=self)
                        edit.setSizeAdjustPolicy(edit.AdjustToContents)
                        for d in data.split('|'):
                            edit.addItem(d)
                        edit.setEditable(False)
                        edit.setCurrentIndex(0)
                        # noinspection PyUnresolvedReferences
                        edit.currentIndexChanged.connect(self._parameterChanged)
                        if tooltip is not None: edit.setToolTip(tooltip)
                        # noinspection PyTypeChecker
                        layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                        self._parameters[parameter] = edit
                elif vartype == 'lint':
                    if data != '':
                        if node.hasAttribute('varmin'): varmin = int(node.getAttribute('varmin'))
                        else: varmin = None
                        if node.hasAttribute('varmax'): varmax = int(node.getAttribute('varmax'))
                        else: varmax = None
                        self._parameters[parameter] = list()
                        lyout = QHBoxLayout()
                        lyout.setContentsMargins(0, 0, 0, 0)
                        lyout.setSpacing(5)
                        if node.hasAttribute('step'): step = int(node.getAttribute('step'))
                        else: step = None
                        for d in data.split():
                            edit = QSpinBox(parent=self)
                            edit.setFixedWidth(100)
                            if step is not None: edit.setSingleStep(step)
                            if varmin is not None and varmax is not None:
                                edit.setMinimum(varmin)
                                edit.setMaximum(varmax)
                                edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                            edit.setValue(int(d))
                            edit.setAlignment(Qt.AlignCenter)
                            # noinspection PyUnresolvedReferences
                            edit.valueChanged.connect(self._parameterChanged)
                            if tooltip is not None: edit.setToolTip('{}\n\nValue range from {} to {}'.format(tooltip, varmin, varmax))
                            else: edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                            lyout.addWidget(edit, alignment=Qt.AlignLeft)
                            self._parameters[parameter].append(edit)
                        layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                elif vartype == 'lfloat':
                    if data != '':
                        if node.hasAttribute('varmin'): varmin = float(node.getAttribute('varmin'))
                        else: varmin = None
                        if node.hasAttribute('varmax'): varmax = float(node.getAttribute('varmax'))
                        else: varmax = None
                        self._parameters[parameter] = list()
                        lyout = QHBoxLayout()
                        lyout.setContentsMargins(0, 0, 0, 0)
                        lyout.setSpacing(5)
                        if node.hasAttribute('decimals'): n = int(node.getAttribute('decimals'))
                        # else: n = self.getNumberOfDecimals(varmin)
                        else: n = 1
                        if node.hasAttribute('step'): step = float(node.getAttribute('step'))
                        else:
                            # step = 1 / (10 ** n)
                            if n > 0: step = 1 / (10 ** n)
                            else: step = 0.1
                        for d in data.split():
                            # edit = QDoubleSpinBox(parent=self)
                            edit = QDoubleSpinBox2(parent=self)
                            # edit.setDecimals(n)
                            if n > 0: edit.setDecimals(n)
                            edit.setSingleStep(step)
                            if n > 5: edit.setFixedWidth(20*n)
                            else: edit.setFixedWidth(100)
                            if varmin is not None and varmax is not None:
                                edit.setMinimum(varmin)
                                edit.setMaximum(varmax)
                                edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                            edit.setValue(float(d))
                            # noinspection PyTypeChecker
                            edit.setAlignment(Qt.AlignCenter)
                            # noinspection PyUnresolvedReferences
                            edit.valueChanged.connect(self._parameterChanged)
                            if tooltip is not None: edit.setToolTip('{}\n\nValue range from {} to {}'.format(tooltip, varmin, varmax))
                            else: edit.setToolTip('Value range from {} to {}'.format(varmin, varmax))
                            lyout.addWidget(edit, alignment=Qt.AlignLeft)
                            self._parameters[parameter].append(edit)
                        layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                elif vartype == 'lbool':
                    if data != '':
                        self._parameters[parameter] = list()
                        lyout = QHBoxLayout()
                        lyout.setContentsMargins(0, 0, 0, 0)
                        lyout.setSpacing(5)
                        for d in data.split():
                            d = (d == 'True')
                            edit = QComboBox(parent=self)
                            edit.setFixedWidth(100)
                            edit.addItem('True')
                            edit.addItem('False')
                            if d == 'True': edit.setCurrentIndex(0)
                            else: edit.setCurrentIndex(1)
                            edit.setEditable(False)
                            # noinspection PyUnresolvedReferences
                            edit.currentIndexChanged.connect(self._parameterChanged)
                            if tooltip is not None: edit.setToolTip(tooltip)
                            lyout.addWidget(edit, alignment=Qt.AlignLeft)
                            self._parameters[parameter].append(edit)
                        layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                elif vartype == 'color':
                    edit = ColorSelectPushButton(parent=self)
                    edit.setFixedSize(QSize(size, size))
                    if data == '': data = '1.0 1.0 1.0'  # Default
                    data = data.split()
                    edit.setFloatColor(float(data[0]), float(data[1]), float(data[2]), False)
                    edit.colorChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'lut':
                    edit = ComboBoxLut(parent=self)
                    if data == '': data = 'gray'  # Default
                    edit.setCurrentText(data)
                    # noinspection PyUnresolvedReferences
                    edit.currentTextChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                # < Revision 15/03/2025
                elif vartype == 'font':
                    edit = FontSelect(parent=self)
                    if data == '': edit.setDefaultFont()
                    else: edit.setFont(data)
                    # noinspection PyUnresolvedReferences
                    edit.fontChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                # Revision 15/03/2025 >
                elif vartype == 'date':
                    edit = QDateEdit(parent=self)
                    edit.setFixedWidth(100)
                    edit.setAlignment(Qt.AlignCenter)
                    edit.setCalendarPopup(True)
                    try: data = datetime.strptime(data, '%Y-%m-%d').date()
                    except: data = datetime.today().date()
                    edit.setDate(data)
                    # noinspection PyUnresolvedReferences
                    edit.dateChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'vol':
                    edit = FileSelectionWidget(parent=self)
                    edit.filterSisypheVolume()
                    edit.setFixedWidth(400)
                    # < Revision 30/11/2025
                    if node.hasAttribute('path'):
                        path = node.getAttribute('path')
                        import Sisyphe
                        if path == '': base = ''
                        elif path == '.': base = abspath(dirname(Sisyphe.__file__))
                        else: base = abspath(join(dirname(Sisyphe.__file__), path))
                        data = abspath(join(base, data))
                    # Revision 30/11/2025 >
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'roi':
                    edit = FileSelectionWidget(parent=self)
                    edit.filterSisypheROI()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                # < Revision 23/12/2024
                # add 'dcm' vartype
                elif vartype == 'dcm':
                    edit = FileSelectionWidget(parent=self)
                    edit.filterDICOM()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                # Revision 23/12/2024 >
                elif vartype == 'dir':
                    edit = FileSelectionWidget(parent=self)
                    edit.filterDirectory()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'vols':
                    edit = FilesSelectionWidget(parent=self)
                    # edit.setTextLabel(lb.text())
                    edit.setTextLabel(lb)
                    edit.filterSisypheVolume()
                    edit.setMinimumWidth(400)
                    # edit.setFixedWidth(400)
                    for d in data.split('|'):
                        # < Revision 04/11/2025
                        # bug fix, replace data by d
                        # if exists(d): edit.add(data)
                        if exists(d): edit.add(d)
                        # Revision 04/11/2025 >
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    layout.addWidget(edit, i, 0, 1, 2)
                    self._parameters[parameter] = edit
                elif vartype == 'rois':
                    edit = FilesSelectionWidget(parent=self)
                    # edit.setTextLabel(lb.text())
                    edit.setTextLabel(lb)
                    edit.filterSisypheROI()
                    edit.setMinimumWidth(400)
                    # edit.setFixedWidth(400)
                    for d in data.split('|'):
                        # < Revision 04/11/2025
                        # if exists(d): edit.add(data)
                        if exists(d): edit.add(d)
                        # Revision 04/11/2025 >
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    layout.addWidget(edit, i, 0, 1, 2)
                    self._parameters[parameter] = edit
                # < Revision 23/12/2024
                # add 'dcms' vartype
                elif vartype == 'dcms':
                    edit = FilesSelectionWidget(parent=self)
                    # edit.setTextLabel(lb.text())
                    edit.setTextLabel(lb)
                    edit.filterDICOM()
                    edit.setMinimumWidth(400)
                    # edit.setFixedWidth(400)
                    for d in data.split('|'):
                        # < Revision 04/11/2025
                        # if exists(d): edit.add(data)
                        if exists(d): edit.add(d)
                        # Revision 04/11/2025 >
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    layout.addWidget(edit, i, 0, 1, 2)
                    self._parameters[parameter] = edit
                # Revision 23/12/2024 >
                elif vartype == 'dirs':
                    edit = FilesSelectionWidget(parent=self)
                    # edit.setTextLabel(lb.text())
                    edit.setTextLabel(lb)
                    edit.filterDirectory()
                    edit.setMinimumWidth(400)
                    # edit.setFixedWidth(400)
                    for d in data.split('|'):
                        # < Revision 04/11/2025
                        # if exists(d): edit.add(data)
                        if exists(d): edit.add(d)
                        # Revision 04/11/2025 >
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    layout.addWidget(edit, i, 0, 1, 2)
                    self._parameters[parameter] = edit
                elif vartype == 'txt':
                    edit = FileSelectionWidget(parent=self)
                    edit.filterExtension('.txt')
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    if tooltip is not None: edit.setToolTip(tooltip)
                    # noinspection PyTypeChecker
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                else: raise TypeError('Unknown vartype {}'.format(vartype))
                i += 1
        self._settingsbox.setLayout(layout)

    # Public methods

    def getFontSize(self) -> int:
        """
        Get the font size of the widget.

        Returns
        -------
        int
            font point size.
        """
        return self.font().pointSize()

    def setFontSize(self, v: int) -> None:
        """
        Set the font size for the widget and its children.

        Parameters
        ----------
        v : int
            font point size.
        """
        self.font().setPointSize(v)
        self._button.font().setPointSize(v)
        self._reset.font().setPointSize(v)
        self._save.font().setPointSize(v)
        self._load.font().setPointSize(v)
        self._saveas.font().setPointSize(v)
        for k in self._parameters:
            self._parameters[k].font().setPointSize(v)

    def toggleSettingsVisibility(self, signal: bool = True) -> None:
        """
        Toggle the visibility of the settings box.

        Parameters
        ----------
        signal : bool
            emit VisibilityToggled Qt signal if signal is True.
        """
        if self._settingsbox.isVisible():
            self._settingsbox.setVisible(False)
            self._button.setIcon(self._icondown)
            txt = self._button.toolTip()
            txt = txt.replace('Hide', 'Show')
            self._button.setToolTip(txt)
            self._save.setVisible(False)
            self._reset.setVisible(False)
            self._load.setVisible(False)
            self._saveas.setVisible(False)
            self.resize(self.width(), self._button.height())
        else:
            self._settingsbox.setVisible(True)
            self._button.setIcon(self._iconup)
            txt = self._button.toolTip()
            txt = txt.replace('Show', 'Hide')
            self._button.setToolTip(txt)
            if self._iovisibility:
                self._save.setVisible(True)
                self._reset.setVisible(True)
                self._load.setVisible(True)
                self._saveas.setVisible(True)
        QApplication.processEvents()
        # < Revision 28/11/2025
        # self.VisibilityToggled.emit(self)
        if signal:
            # noinspection PyUnresolvedReferences
            self.VisibilityToggled.emit(self)
        # Revision 28/11/2025 >

    def settingsVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the settings box if it is not visible.

        Parameters
        ----------
        signal : bool
            emit VisibilityToggled Qt signal if signal is True.
        """
        if not self._settingsbox.isVisible():
            # < Revision 28/11/2025
            # self.toggleSettingsVisibility()
            self.toggleSettingsVisibility(signal)
            # Revision 28/11/2025 >

    def settingsVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the settings box if it is visible.

        Parameters
        ----------
        signal : bool
            emit VisibilityToggled Qt signal if signal is True.
        """
        if self._settingsbox.isVisible():
            # < Revision 28/11/2025
            # self.toggleSettingsVisibility()
            self.toggleSettingsVisibility(signal)
            # Revision 28/11/2025 >

    def getFunctionName(self) -> str:
        """
        Get the name of the function associated with this settings widget.

        Returns
        -------
        str
            function name.
        """
        return self._function

    def getParameterWidget(self, parameter: str) -> QWidget:
        """
        Get the widget associated with a specific parameter.

        Parameters
        ----------
        parameter : str
            name of the parameter.

        Returns
        -------
        QWidget
            widget for the given parameter.
        """
        return self._parameters[parameter]

    def getParameterValue(self, parameter: str) -> Any:
        """
        Get the current value of a specific parameter.

        Parameters
        ----------
        parameter : str
            name of the parameter.

        Returns
        -------
        Any
            value of the parameter.
        """
        # noinspection PyInconsistentReturns
        if isinstance(self._parameters[parameter], QLineEdit):
            # vartype str
            return self._parameters[parameter].text()
        elif isinstance(self._parameters[parameter], QSpinBox):
            # vartype int
            return self._parameters[parameter].value()
        elif isinstance(self._parameters[parameter], QDoubleSpinBox):
            # vartype float
            return self._parameters[parameter].value()
        elif isinstance(self._parameters[parameter], QSlider):
            # vartype percent
            return self._parameters[parameter].value() / 100.0
        elif isinstance(self._parameters[parameter], QCheckBox):
            # vartype bool
            return bool(self._parameters[parameter].isChecked())
        elif isinstance(self._parameters[parameter], VisibilityLabel):
            # vartype visibility
            return bool(self._parameters[parameter].getVisibilityStateIcon())
        # < Revision 02/12/2025
        elif isinstance(self._parameters[parameter], ComboBoxLut):
            # vartype lut
            return self._parameters[parameter].currentText()
        elif isinstance(self._parameters[parameter], QComboBox):
            # vartype bool
            if self._parameters[parameter].itemText(0) == 'True':
                return bool(self._parameters[parameter].currentText())
            # vartype lstr
            else:
                d = list()
                current = self._parameters[parameter].currentIndex()
                d.append(self._parameters[parameter].currentText())
                for i in range(self._parameters[parameter].count()):
                    if i != current: d.append(self._parameters[parameter].itemText(i))
                return d
        # elif isinstance(self._parameters[parameter], ComboBoxLut):
        #    return self._parameters[parameter].currentText()
        # Revision 02/12/2025 >
        elif isinstance(self._parameters[parameter], ColorSelectPushButton):
            # vartype color
            return self._parameters[parameter].getFloatColor()
        # < Revision 15/03/2025
        elif isinstance(self._parameters[parameter], FontSelect):
            # vartype font
            return self._parameters[parameter].getFont()
        # Revision 15/03/2025 >
        elif isinstance(self._parameters[parameter], QDateEdit):
            # vartype date
            return self._parameters[parameter].date().toString(Qt.ISODate)
        elif isinstance(self._parameters[parameter], FileSelectionWidget):
            # vartype dir, vol, roi, dcm
            return self._parameters[parameter].getFilename()
        elif isinstance(self._parameters[parameter], FilesSelectionWidget):
            # vartype dirs, vols, rois, dcms
            return self._parameters[parameter].getFilenames()
        elif isinstance(self._parameters[parameter], list):
            # vartype lbool
            if isinstance(self._parameters[parameter][0], QComboBox):
                d = list()
                for p in self._parameters[parameter]: d.append(bool(p.currentText()))
                return d
            # vartype lint, lfloat
            else:
                d = list()
                for p in self._parameters[parameter]: d.append(p.value())
                return d

    # < Revision 13/02/2025
    # add setParameterValue method
    def setParameterValue(self, parameter: str, v: Any) -> None:
        """
        Set the value of a specific parameter widget.

        Parameters
        ----------
        parameter : str
            name of the parameter.
        v : Any
            new value to set.
        """
        widget = self.getParameterWidget(parameter)
        if isinstance(widget, QLineEdit): widget.setText(v)
        elif isinstance(widget, QSpinBox): widget.setValue(int(v))
        elif isinstance(widget, QDoubleSpinBox): widget.setValue(float(v))
        elif isinstance(widget, QSlider): widget.setValue(int(float(v) * 100))
        elif isinstance(widget, QCheckBox):
            if isinstance(v, str):
                if v == 'True': v = True
                else: v = False
            widget.setChecked(v)
        elif isinstance(widget, VisibilityLabel):
            if isinstance(v, str):
                if v == 'True': v = True
                else: v = False
            widget.setVisibilitySateIcon(v)
        elif isinstance(widget, QComboBox):
            if isinstance(v, str): v = v.split('|')
            if isinstance(v, list): v = v[0]
            widget.setCurrentText(v)
        elif isinstance(widget, ComboBoxLut):
            if isinstance(v, list): v = v[0]
            widget.setCurrentText(v)
        elif isinstance(widget, ColorSelectPushButton):
            if isinstance(v, str): v = [float(i) for i in v.split(' ')]
            widget.setFloatColor(v[0], v[1], v[2])
        # < Revision 15/03/2025
        elif isinstance(widget, FontSelect):
            # < Revision 16/03/2025
            # str or QFont type
            if isinstance(v, QFont): v = v.family()
            # Revision 16/03/2025 >
            widget.setFont(v)
        # Revision 15/03/2025 >
        elif isinstance(widget, QDateEdit):
            d = date.fromisoformat(v)
            widget.setDate(QDate(d.year, d.month, d.day))
        elif isinstance(widget, FileSelectionWidget): widget.open(v)
        elif isinstance(widget, FilesSelectionWidget): widget.add(v)
        elif isinstance(widget, list):
            # vartype lbool
            if isinstance(widget[0], QComboBox):
                if isinstance(v, str): v = v.split(' ')
                # noinspection PyTypeChecker
                for i in range(len(widget)):
                    widget[i].setCurrentText(v[i])
            # vartype lint, lfloat
            else:
                if isinstance(v, str):
                    if isinstance(widget[0], QSpinBox): v = [int(i) for i in v.split(' ')]
                    elif isinstance(widget[0], QDoubleSpinBox): v = [float(i) for i in v.split(' ')]
                # noinspection PyTypeChecker
                for i in range(len(widget)):
                    widget[i].setValue(v[i])
    # Revision 13/02/2025 >

    def setParameterVisibility(self, parameter: str, v: bool) -> None:
        """
        Set the visibility of a specific parameter widget and its label.

        Parameters
        ----------
        parameter : str
            name of the parameter.
        v : bool
            True to show the widget, False to hide it.
        """
        ws = self._parameters[parameter]
        if isinstance(ws, list): ws = ws[0]
        lyout = self._settingsbox.layout()
        for i in range(lyout.rowCount()):
            if lyout.itemAtPosition(i, 1).widget() == ws:
                ws = self._parameters[parameter]
                if isinstance(ws, list):
                    if len(ws) > 0:
                        for w in ws: w.setVisible(v)
                else: ws.setVisible(v)
                lyout.itemAtPosition(i, 0).widget().setVisible(v)
                break

    def getParameterVisibility(self, parameter: str) -> bool:
        """
        Get the visibility of a specific parameter widget.

        Parameters
        ----------
        parameter : str
            name of the parameter.

        Returns
        -------
        bool
            True if the widget is visible, False otherwise.
        """
        ws = self._parameters[parameter]
        if isinstance(ws, list):
            if len(ws) > 0: return ws[0].isVisible()
            else: raise AttributeError('No parameter.')
        else: return self._parameters[parameter].isVisible()

    def getParametersList(self) -> list[str]:
        """
        Get a list of all parameter names.

        Returns
        -------
        list[str]
            list containing the names of all parameters.
        """
        return list(self._parameters.keys())

    def getParametersDict(self) -> dict[str, Any]:
        """
        Get a dictionary of all parameters and their current values.

        Returns
        -------
        dict[str, Any]
            dictionary with parameter names as keys and their values.
        """
        r = dict()
        for parameter in self._parameters:
            r[parameter] = self.getParameterValue(parameter)
        return r

    # < Revision 13/02/2025
    # add setParametersFromDict method
    def setParametersFromDict(self, d: dict[str, Any]) -> None:
        """
        Set parameter values from a dictionary.

        Parameters
        ----------
        d : dict[str, Any]
            dictionary with parameter names as keys and their new values.
        """
        params = self.getParametersList()
        for k in list(d.keys()):
            if k in params:
                self.setParameterValue(k, d[k])
    # Revision 13/02/2025 >

    def resetSettings(self, filename: str = '', default: bool = False) -> None:
        """
        Reset the settings to their default values from a settings file.

        Parameters
        ----------
        filename : str (optional)
            Path to a custom settings file. If empty (default), uses the user's default settings (~/.PySisyphe/settings.xml).
        default : bool (optional)

            - If True, loads from the application's default settings file, ignoring `filename`.
            - If False (default), loads from the user's settings file (~/.PySisyphe/settings.xml) or the custom settings file.
        """
        xml = self.classSisypheSettings()
        if filename == '':
            if default: xml.loadDefaultFileSettings()
            # < Revision 04/11/2025
            else: xml.loadUserFileSettings()
            # Revision 04/11/2025 >
        else: xml.loadCustomFileSettings(filename)
        parameters = xml.getSectionFieldsList(self._function)
        if len(parameters) > 0:
            for parameter in parameters:
                node = xml.getFieldNode(self._function, parameter)
                vartype = node.getAttribute('vartype')
                if node.hasChildNodes():
                    child = node.firstChild
                    # noinspection PyUnresolvedReferences
                    data = child.data
                    if vartype == 'str':
                        self._parameters[parameter].setText(data)
                    elif vartype == 'int':
                        self._parameters[parameter].setValue(int(data))
                    elif vartype == 'float':
                        self._parameters[parameter].setValue(float(data))
                    elif vartype == 'percent':
                        self._parameters[parameter].setValue(int(float(data)*100))
                    elif vartype == 'bool':
                        if isinstance(self._parameters[parameter], QCheckBox):
                            if data == 'True': self._parameters[parameter].setCheckState(Qt.Checked)
                            else: self._parameters[parameter].setCheckState(Qt.Unchecked)
                        elif isinstance(self._parameters[parameter], QComboBox):
                            if data == 'True': self._parameters[parameter].setCurrentIndex(0)
                            else: self._parameters[parameter].setCurrentIndex(1)
                    elif vartype == 'visibility':
                        if isinstance(self._parameters[parameter], VisibilityLabel):
                            if data == 'True': self._parameters[parameter].setVisibilityStateIconToView()
                            else: self._parameters[parameter].setVisibilityStateIconToHide()
                    elif vartype == 'lstr':
                        self._parameters[parameter].setCurrentText(data.split('|')[0])
                    elif vartype == 'lint':
                        i = 0
                        for d in data.split():
                            self._parameters[parameter][i].setValue(int(d))
                            i += 1
                    elif vartype == 'lfloat':
                        i = 0
                        for d in data.split():
                            self._parameters[parameter][i].setValue(int(d))
                            i += 1
                    elif vartype == 'lbool':
                        i = 0
                        for d in data.split():
                            if d == 'True': self._parameters[parameter][i].setCurrentIndex(0)
                            else: self._parameters[parameter][i].setCurrentIndex(1)
                            i += 1
                    elif vartype == 'color':
                        data = data.split()
                        self._parameters[parameter].setFloatColor(float(data[0]), float(data[1]), float(data[2]), False)
                    elif vartype == 'date':
                        data = datetime.strptime(data, '%Y-%m-%d').date()
                        self._parameters[parameter].setDate(data)
                    elif vartype == 'vol':
                        # < Revision 30/11/2025
                        if node.hasAttribute('path'):
                            path = node.getAttribute('path')
                            import Sisyphe
                            if path == '': base = ''
                            elif path == '.': base = abspath(dirname(Sisyphe.__file__))
                            else: base = abspath(join(dirname(Sisyphe.__file__), path))
                            data = abspath(join(base, data))
                        # Revision 30/11/2025 >
                        self._parameters[parameter].open(data)
                    elif vartype == 'roi':
                        self._parameters[parameter].open(data)
                    elif vartype == 'dir':
                        self._parameters[parameter].open(data)
                    elif vartype == 'vols':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].addBundle(d)
                    elif vartype == 'rois':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].addBundle(d)
                    elif vartype == 'dirs':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].addBundle(d)
                elif vartype in ('str', 'dir', 'vol', 'roi', 'date'):
                    self._parameters[parameter].setText('')
                QApplication.processEvents()
                # self._parameters[parameter].repaint()

    def saveSettings(self) -> None:
        """
        Save the current settings to the user's default settings file (~/.PySisyphe/settings.xml).
        """
        xml = self.classSisypheSettings()
        for parameter in self._parameters.keys():
            xml.setFieldValue(self._function, parameter, self.getParameterValue(parameter))
        xml.save()

    def saveAsSettings(self) -> None:
        """
        Open a dialog to save the current settings to a custom XML file.
        """
        filename = QFileDialog().getSaveFileName(self, 'Save custom settings file', getcwd(), 'XML (*.xml)')
        filename = filename[0]
        if filename:
            chdir(dirname(filename))
            xml = self.classSisypheSettings()
            for parameter in self._parameters.keys():
                xml.setFieldValue(self._function, parameter, self.getParameterValue(parameter))
            xml.saveAs(filename)

    def loadSettings(self) -> None:
        """
        Open a dialog to load settings from a custom XML file.
        """
        filename = QFileDialog.getOpenFileName(self, 'Load custom settings file', getcwd(), 'XML (*.xml)')
        filename = filename[0]
        if filename:
            chdir(dirname(filename))
            self.resetSettings(filename)

    def setSettingsButtonText(self, txt: str) -> None:
        """
        Set the text of the settings button.
        This button is used to toggle visibility of the parameters.

        Parameters
        ----------
        txt : str
            new text for the button.
        """
        if isinstance(txt, str):
            v = self._button.toolTip()[:5]
            self._button.setToolTip('{}{}'.format(v, txt))
            if txt[-3:] != '...': txt += '...'
            self._button.setText(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def setSettingsButtonDefaultText(self) -> None:
        """
        Reset the settings button text to its default value ('Settings...').
        This button is used to toggle visibility of the parameters.
        """
        v = self._button.toolTip()[:5]
        self._button.setToolTip('{} settings'.format(v))
        self._button.setText('Settings...')

    def setSettingsButtonFunctionText(self) -> None:
        """
        Set the settings button text based on the function name.
        This button is used to toggle visibility of the parameters.
        """
        v = self._button.toolTip()[:5]
        self._button.setToolTip('{}{} settings'.format(v, self._function))
        txt = self.formatLabel(self._function) + '...'
        self._button.setText(txt)

    def setButtonsVisibility(self, v: bool) -> None:
        """
        Set the visibility of all buttons.

        Parameters
        ----------
        v : bool
            True to show the buttons, False to hide them.
        """
        if isinstance(v, bool):
            self._button.setVisible(v)
            self._reset.setVisible(v)
            self._load.setVisible(v)
            self._save.setVisible(v)
            self._saveas.setVisible(v)
            if v is False: self._settingsbox.setVisible(True)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getButtonsVisibility(self) -> bool:
        """
        Get the visibility state of all buttons.

        Returns
        -------
        bool
            True if the reset button is visible, False otherwise.
        """
        return self._reset.isVisible()

    def showButtons(self) -> None:
        """
        Show all buttons.
        """
        self.setButtonsVisibility(True)

    def hideButtons(self) -> None:
        """
        Hide all buttons.
        """
        self.setButtonsVisibility(False)

    def setIOButtonsVisibility(self, v: bool) -> None:
        """
        Set the visibility of the settings I/O buttons (Reset, Load, Save, Save As).

        Parameters
        ----------
        v : bool
            True to show the I/O buttons, False to hide them.
        """
        if isinstance(v, bool):
            self._reset.setVisible(v)
            self._load.setVisible(v)
            self._save.setVisible(v)
            self._saveas.setVisible(v)
            self._iovisibility = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getIOButtonsVisibility(self) -> bool:
        """
        Get the visibility state of the settings I/O buttons.

        Returns
        -------
        bool
            True if the reset button is visible, False otherwise.
        """
        return self._reset.isVisible()

    def showIOButtons(self) -> None:
        """
        Show the settings I/O buttons.
        """
        self.setIOButtonsVisibility(True)

    def hideIOButtons(self) -> None:
        """
        Hide the settings I/O buttons.
        """
        self.setIOButtonsVisibility(False)


class FunctionSettingsWidget(SettingsWidget):
    """
    FunctionSettingsWidget class

    Description
    ~~~~~~~~~~~

    Widget to manage function settings from an XML file (functions.xml).

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SettingsWidget -> FunctionSettingsWidget

    Creation: 11/08/2022
    """

    classSisypheSettings = SisypheFunctionsSettings


class DialogSettingsWidget(SettingsWidget):
    """
    DialogSettingsWidget class

    Description
    ~~~~~~~~~~~

    Widget to manage dialog window from an XML file (dialog.xml).

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SettingsWidget -> DialogSettingsWidget

    Creation: 11/08/2022
    """

    classSisypheSettings = SisypheDialogsSettings

# < Revision 04/11/2025
# new class CustomSettingsWidget
class CustomSettingsWidget(SettingsWidget):
    """
    CustomSettingsWidget class

    Description
    ~~~~~~~~~~~

    Widget to manage settings from a custom XML file.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SettingsWidget -> DialogSettingsWidget

    Creation: 04/11/2025
    """

    classSisypheSettings = SisypheCustomSettings

    # Special method

    def __init__(self, filename: str, function: str, parent: QWidget | None = None) -> None:
        """
        CustomSettingsWidget instance constructor.

        Parameters
        ----------
        filename : str
            custom settings xml file name
        function : str
             name of the function for which to create the settings widget.
        parent : QWidget | None
            parent widget.
        """
        SisypheCustomSettings.setClassSettings(filename)
        super().__init__(function, parent)
# Revision 04/11/2025 >