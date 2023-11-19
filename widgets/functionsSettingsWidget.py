"""
    External packages/modules

        Name            Homepage link                                               Usage

        darkdetect      https://github.com/albertosottile/darkdetect                OS Dark Mode detection
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import join
from os.path import exists
from os.path import dirname
from os.path import abspath

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
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
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.basicWidgets import ColorSelectPushButton
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import VisibilityLabel

__all__ = ['SettingsWidget',
           'FunctionSettingsWidget',
           'DialogSettingsWidget']

"""
    Class hierarchy
    
        QWidget -> SettingsWidget -> FunctionSettingsWidget
"""


class SettingsWidget(QWidget):
    """
        SettingsWidget class

        Description

            Widget to manage application settings from XML file (settings.xml).

        Inheritance

            QWidget -> SettingsWidget -> FunctionSettingsWidget

        Private attributes

            _parameters     dict of QWidget, keyword = name of function parameters
            _funcname       str, function name

        Qt Signals

            ParameterChanged.emit(QWidget)
            VisibilityToggled.emit(QWidget)

        Public methods

            toggleSettingsVisibility()
            settingsVisibilityOn()
            settingsVisibilityOff()
            str = getFunctionName()
            QWidget = getParameterWidget(str)
            str or int or float or date or list = getParameterValue(str)
            list = getParametersList()
            dict = getParameterDict()
            setParameterVisibility(str, bool)
            bool = getParameterVisibility(str)
            resetSettings()
            saveSettings()
            setSettingsButtonText(str)
            setSettingsButtonDefaultText()
            setSettingsButtonFunctionText()
            setButtonsVisibility(bool)
            bool = getButtonsVisibility()
            showButtons()
            hideButtons()
            setIOButtonsVisibility(bool)
            bool = getIOButtonsVisibility()
            showIOButtons()
            hideIOButtons()

            inherited QWidget methods

        Revision:

            11/08/2022  _initSettingsLayout() method, add QLabel after QSlider for percent vartype
    """

    classSisypheSettings = SisypheSettings

    # Custom Qt Signals

    ParameterChanged = pyqtSignal(QWidget)
    VisibilityToggled = pyqtSignal(QWidget)

    # Class methods

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    @classmethod
    def getDefaultToolbarIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkicons')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lighticons')

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

    @classmethod
    def getNumberOfDecimals(cls, v):
        if v == 0.0: return 1
        elif abs(v) < 1e-8: return 8
        else:
            r = len('{:.8f}'.format(v).rstrip('0').split('.')[1])
            if r == 0: r = 1
            return r

    # Special method

    def __init__(self, function, parent=None):
        QWidget.__init__(self, parent)

        self._function = function
        self._font = QFont()
        self.setFont(self._font)
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
        self._reset = QPushButton('Reset')
        self._reset.setToolTip('Restore default {} settings'.format(self._function))
        self._reset.setVisible(False)
        self._save = QPushButton('Save')
        self._save.setToolTip('Save to default {} settings'.format(self._function))
        self._save.setVisible(False)
        self._load = QPushButton('Load...')
        self._load.setToolTip('Load custom {} settings'.format(self._function))
        self._load.setVisible(False)
        self._saveas = QPushButton('Save as...')
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
        self._settingsbox = QWidget()
        self._settingsbox.setVisible(False)
        self._initSettingsLayout(function)
        self._layout.addWidget(self._settingsbox)
        # self._layout.addStretch()

        self._button.clicked.connect(self.toggleSettingsVisibility)
        self._reset.clicked.connect(self.resetSettings)
        self._save.clicked.connect(self.saveSettings)
        self._load.clicked.connect(self.loadSettings)
        self._saveas.clicked.connect(self.saveAsSettings)

    # Private methods

    def _parameterChanged(self, value):
        self.ParameterChanged.emit(self)

    def _initSettingsLayout(self, function):
        xml = self.classSisypheSettings()
        parameters = xml.getSectionFieldsList(function)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if len(parameters) > 0:
            i = 0
            for parameter in parameters:
                node = xml.getFieldNode(function, parameter)
                vartype = node.getAttribute('vartype')
                # label attribute
                if node.hasAttribute('label'): lb = QLabel(node.getAttribute('label'))
                else: lb = QLabel(self.formatLabel(parameter))
                if vartype not in ('dirs', 'vols', 'rois'):
                    layout.addWidget(lb, i, 0, alignment=Qt.AlignRight)
                if node.hasChildNodes():
                    child = node.firstChild
                    data = child.data
                else: data = ''
                if vartype == 'str':
                    edit = QLineEdit()
                    edit.setFixedWidth(300)
                    edit.setText(data)
                    edit.textChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'int':
                    if node.hasAttribute('varmin'): varmin = int(node.getAttribute('varmin'))
                    else: varmin = None
                    if node.hasAttribute('varmax'): varmax = int(node.getAttribute('varmax'))
                    else: varmax = None
                    edit = QSpinBox()
                    edit.setFixedWidth(75)
                    if node.hasAttribute('step'):
                        step = int(node.getAttribute('step'))
                        edit.setSingleStep(step)
                    if varmin is not None and varmax is not None:
                        edit.setMinimum(varmin)
                        edit.setMaximum(varmax)
                        edit.setToolTip('value range from {} to {}'.format(varmin, varmax))
                    if data == '': data = varmin  # Default
                    edit.setValue(int(data))
                    edit.setAlignment(Qt.AlignCenter)
                    edit.valueChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'float':
                    if node.hasAttribute('varmin'): varmin = float(node.getAttribute('varmin'))
                    else: varmin = None
                    if node.hasAttribute('varmax'): varmax = float(node.getAttribute('varmax'))
                    else: varmax = None
                    edit = QDoubleSpinBox()
                    if node.hasAttribute('decimals'): n = int(node.getAttribute('decimals'))
                    else: n = self.getNumberOfDecimals(varmin)
                    edit.setDecimals(n)
                    if node.hasAttribute('step'): step = float(node.getAttribute('step'))
                    else: step = 1 / (10**n)
                    edit.setSingleStep(step)
                    if n > 5: edit.setFixedWidth(15*n)
                    else: edit.setFixedWidth(75)
                    if varmin is not None and varmax is not None:
                        edit.setMinimum(varmin)
                        edit.setMaximum(varmax)
                        edit.setToolTip('value range from {} to {}'.format(varmin, varmax))
                    if data == '': data = varmin  # Default
                    edit.setValue(float(data))
                    edit.setAlignment(Qt.AlignCenter)
                    edit.valueChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'percent':
                    lbl2 = QLabel('100 %')
                    edit = QSlider(Qt.Horizontal)
                    edit.setToolTip('100 %')
                    edit.setMinimum(0)
                    edit.setMaximum(100)
                    edit.setFixedWidth(75)
                    if data == '': data = 0.0  # Default
                    edit.setValue(int(float(data)*100))
                    edit.valueChanged.connect(self._parameterChanged)
                    edit.valueChanged.connect(lambda v, w=edit: w.setToolTip('{} %'.format(v)))
                    edit.valueChanged.connect(lambda v, w=lbl2: w.setText('{} %'.format(v)))
                    lyout = QHBoxLayout()
                    lyout.setSpacing(5)
                    lyout.setContentsMargins(0, 0, 0, 0)
                    lyout.addWidget(edit)
                    lyout.addWidget(lbl2)
                    layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'bool':
                    edit = QCheckBox()
                    edit.setTristate(False)
                    if data == '': data = 'False'  # Default
                    if data == 'True': edit.setCheckState(Qt.Checked)
                    else: edit.setCheckState(Qt.Unchecked)
                    edit.stateChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'visibility':
                    if node.hasAttribute('icon'): icn = join(self.getDefaultToolbarIconDirectory(), node.getAttribute('icon'))
                    else: icn = ''
                    edit = VisibilityLabel()
                    edit.setFixedSize(QSize(24, 24))
                    if data == '': data = 'False'  # Default
                    if data == 'True': edit.setVisibilityStateIconToView()
                    else: edit.setVisibilityStateIconToHide()
                    edit.visibilityChanged.connect(self._parameterChanged)
                    lyout = QHBoxLayout()
                    lyout.setSpacing(5)
                    lyout.setContentsMargins(0, 0, 0, 0)
                    if exists(icn): lyout.addWidget(IconPushButton(icon=icn))
                    lyout.addWidget(edit)
                    layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'lstr':
                    if data != '':
                        edit = QComboBox()
                        edit.setSizeAdjustPolicy(edit.AdjustToContents)
                        for d in data.split('|'):
                            edit.addItem(d)
                        edit.setEditable(False)
                        edit.setCurrentIndex(0)
                        edit.currentIndexChanged.connect(self._parameterChanged)
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
                            edit = QSpinBox()
                            edit.setFixedWidth(75)
                            if step is not None: edit.setSingleStep(step)
                            if varmin is not None and varmax is not None:
                                edit.setMinimum(varmin)
                                edit.setMaximum(varmax)
                                edit.setToolTip('value range from {} to {}'.format(varmin, varmax))
                            edit.setValue(int(d))
                            edit.setAlignment(Qt.AlignCenter)
                            edit.valueChanged.connect(self._parameterChanged)
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
                        else: n = self.getNumberOfDecimals(varmin)
                        if node.hasAttribute('step'): step = float(node.getAttribute('step'))
                        else: step = 1 / (10 ** n)
                        for d in data.split():
                            edit = QDoubleSpinBox()
                            edit.setDecimals(n)
                            edit.setSingleStep(step)
                            if n > 5: edit.setFixedWidth(15*n)
                            else: edit.setFixedWidth(75)
                            if varmin is not None and varmax is not None:
                                edit.setMinimum(varmin)
                                edit.setMaximum(varmax)
                                edit.setToolTip('value range from {} to {}'.format(varmin, varmax))
                            edit.setValue(float(d))
                            edit.setAlignment(Qt.AlignCenter)
                            edit.valueChanged.connect(self._parameterChanged)
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
                            edit = QComboBox()
                            edit.setFixedWidth(75)
                            edit.addItem('True')
                            edit.addItem('False')
                            if d == 'True': edit.setCurrentIndex(0)
                            else: edit.setCurrentIndex(1)
                            edit.setEditable(False)
                            edit.currentIndexChanged.connect(self._parameterChanged)
                            lyout.addWidget(edit, alignment=Qt.AlignLeft)
                            self._parameters[parameter].append(edit)
                        layout.addLayout(lyout, i, 1, alignment=Qt.AlignLeft)
                elif vartype == 'color':
                    edit = ColorSelectPushButton()
                    if data == '': data = '1.0 1.0 1.0'  # Default
                    data = data.split()
                    edit.setFloatColor(float(data[0]), float(data[1]), float(data[2]), False)
                    edit.colorChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'date':
                    edit = QDateEdit()
                    edit.setFixedWidth(100)
                    edit.setAlignment(Qt.AlignCenter)
                    edit.setCalendarPopup(True)
                    try: data = datetime.strptime(data, '%Y-%m-%d').date()
                    except: data = datetime.today().date()
                    edit.setDate(data)
                    edit.dateChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'vol':
                    edit = FileSelectionWidget()
                    edit.filterSisypheVolume()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'roi':
                    edit = FileSelectionWidget()
                    edit.filterSisypheROI()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'dir':
                    edit = FileSelectionWidget()
                    edit.filterDirectory()
                    edit.setFixedWidth(400)
                    if exists(data): edit.open(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 1, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'vols':
                    edit = FilesSelectionWidget()
                    edit.setTextLabel(lb.text())
                    edit.filterSisypheVolume()
                    edit.setFixedWidth(400)
                    for d in data.split('|'):
                        if exists(d): edit.add(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 0, 1, 2, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'rois':
                    edit = FilesSelectionWidget()
                    edit.setTextLabel(lb.text())
                    edit.filterSisypheROI()
                    edit.setFixedWidth(400)
                    for d in data.split('|'):
                        if exists(d): edit.add(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 0, 1, 2, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                elif vartype == 'dirs':
                    edit = FilesSelectionWidget()
                    edit.setTextLabel(lb.text())
                    edit.filterDirectory()
                    edit.setFixedWidth(400)
                    for d in data.split('|'):
                        if exists(d): edit.add(data)
                    edit.FieldChanged.connect(self._parameterChanged)
                    layout.addWidget(edit, i, 0, 1, 2, alignment=Qt.AlignLeft)
                    self._parameters[parameter] = edit
                else: raise TypeError('Unknown vartype {}'.format(vartype))
                i += 1
        self._settingsbox.setLayout(layout)

    # Public methods

    def getFontSize(self):
        return self._font.pointSize()

    def setFontSize(self, v):
        self._font.setPointSize(v)
        self.setFont(self._font)

    def toggleSettingsVisibility(self):
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
        self.VisibilityToggled.emit(self)

    def settingsVisibilityOn(self):
        if not self._settingsbox.isVisible():
            self.toggleSettingsVisibility()

    def settingsVisibilityOff(self):
        if self._settingsbox.isVisible():
            self.toggleSettingsVisibility()

    def getFunctionName(self):
        return self._function

    def getParameterWidget(self, parameter):
        return self._parameters[parameter]

    def getParameterValue(self, parameter):
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
        elif isinstance(self._parameters[parameter], ColorSelectPushButton):
            # vartype color
            return self._parameters[parameter].getFloatColor()
        elif isinstance(self._parameters[parameter], QDateEdit):
            # vartype date
            return self._parameters[parameter].date().toString(Qt.ISODate)
        elif isinstance(self._parameters[parameter], FileSelectionWidget):
            # vartype dir, vol, roi
            return self._parameters[parameter].getFilename()
        elif isinstance(self._parameters[parameter], FilesSelectionWidget):
            # vartype dirs, vols, rois
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

    def setParameterVisibility(self, parameter, v):
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

    def getParameterVisibility(self, parameter):
        ws = self._parameters[parameter]
        if isinstance(ws, list):
            if len(ws) > 0: return ws[0].isVisible()
        else: return self._parameters[parameter].isVisible()

    def getParametersList(self):
        return list(self._parameters.keys())

    def getParametersDict(self):
        r = dict()
        for parameter in self._parameters:
            r[parameter] = self.getParameterValue(parameter)
        return r

    def resetSettings(self, filename='', default=False):
        """
            default=False, xml user settings
            default=True, xml default settings
        """
        xml = self.classSisypheSettings()
        if filename == '':
            if default: xml.loadDefaultFileSettings()
        else: xml.loadCustomFileSettings(filename)
        parameters = xml.getSectionFieldsList(self._function)
        if len(parameters) > 0:
            for parameter in parameters:
                node = xml.getFieldNode(self._function, parameter)
                vartype = node.getAttribute('vartype')
                if node.hasChildNodes():
                    child = node.firstChild
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
                        self._parameters[parameter].open(data)
                    elif vartype == 'roi':
                        self._parameters[parameter].open(data)
                    elif vartype == 'dir':
                        self._parameters[parameter].open(data)
                    elif vartype == 'vols':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].add(d)
                    elif vartype == 'rois':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].add(d)
                    elif vartype == 'dirs':
                        self._parameters[parameter].clear()
                        for d in data.split('|'):
                            if exists(d): self._parameters[parameter].add(d)
                elif vartype in ('str', 'dir', 'vol', 'roi', 'date'):
                    self._parameters[parameter].setText('')
                QApplication.processEvents()
                #self._parameters[parameter].repaint()

    def saveSettings(self):
        xml = self.classSisypheSettings()
        for parameter in self._parameters.keys():
            xml.setFieldValue(self._function, parameter, self.getParameterValue(parameter))
        xml.save()

    def saveAsSettings(self):
        filename = QFileDialog().getSaveFileName(self, 'Save custom settings file', getcwd(), 'XML (*.xml)')
        filename = filename[0]
        if filename:
            xml = self.classSisypheSettings()
            for parameter in self._parameters.keys():
                xml.setFieldValue(self._function, parameter, self.getParameterValue(parameter))
            xml.saveAs(filename)

    def loadSettings(self):
        filename = QFileDialog.getOpenFileName(self, 'Load custom settings file', getcwd(), 'XML (*.xml)')
        filename = filename[0]
        if filename: self.resetSettings(filename)

    def setSettingsButtonText(self, txt):
        if isinstance(txt, str):
            v = self._button.toolTip()[:5]
            self._button.setToolTip('{}{}'.format(v, txt))
            if txt[-3:] != '...': txt += '...'
            self._button.setText(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def setSettingsButtonDefaultText(self):
        v = self._button.toolTip()[:5]
        self._button.setToolTip('{} settings'.format(v))
        self._button.setText('Settings...')

    def setSettingsButtonFunctionText(self):
        v = self._button.toolTip()[:5]
        self._button.setToolTip('{}{} settings'.format(v, self._function))
        txt = self.formatLabel(self._function) + '...'
        self._button.setText(txt)

    def setButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._button.setVisible(v)
            self._reset.setVisible(v)
            self._load.setVisible(v)
            self._save.setVisible(v)
            self._saveas.setVisible(v)
            if v is False: self._settingsbox.setVisible(True)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getButtonsVisibility(self):
        return self._reset.isVisible()

    def showButtons(self):
        self.setButtonsVisibility(True)

    def hideButtons(self):
        self.setButtonsVisibility(False)

    def setIOButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._reset.setVisible(v)
            self._load.setVisible(v)
            self._save.setVisible(v)
            self._saveas.setVisible(v)
            self._iovisibility = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getIOButtonsVisibility(self):
        return self._reset.isVisible()

    def showIOButtons(self):
        self.setIOButtonsVisibility(True)

    def hideIOButtons(self):
        self.setIOButtonsVisibility(False)


class FunctionSettingsWidget(SettingsWidget):
    """
        FunctionSettingsWidget class

        Description

            Widget to manage application function settings from XML file (functions.xml).

        Inheritance

            QWidget -> SettingsWidget -> FunctionSettingsWidget

        Private attributes

        Qt Signals

            ParameterChanged.emit(QWidget)
            VisibilityToggled.emit(QWidget)

        Public methods

            inherited SettingsWidget
            inherited QWidget methods
    """

    classSisypheSettings = SisypheFunctionsSettings


class DialogSettingsWidget(SettingsWidget):
    """
        DialogSettingsWidget class

        Description

            Widget to manage dialog window from XML file (functions.xml).

        Inheritance

            QWidget -> SettingsWidget -> DialogSettingsWidget

        Private attributes

        Qt Signals

            ParameterChanged.emit(QWidget)
            VisibilityToggled.emit(QWidget)

        Public methods

            inherited SettingsWidget
            inherited QWidget methods
    """

    classSisypheSettings = SisypheDialogsSettings


if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    main = FunctionSettingsWidget('N4BiasFieldCorrectionImageFilter')
    main.setSettingsButtonFunctionText()
    main.activateWindow()
    main.show()
    app.exec_()
    exit()
