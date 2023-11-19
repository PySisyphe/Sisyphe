"""
    External packages/modules

        Name            Link                                                        Usage

        darkdetect      https://github.com/albertosottile/darkdetect                OS Dark Mode detection
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import join
from os.path import exists
from os.path import abspath
from os.path import dirname
from os.path import splitext

import darkdetect

from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication

__all__ = ['RoundedButton',
           'ColorSelectPushButton',
           'LabeledLineEdit',
           'LabeledSpinBox',
           'LabeledDoubleSpinBox',
           'LabeledSlider',
           'LabeledComboBox',
           'IconLabel',
           'IconPushButton',
           'MenuPushButton',
           'VisibilityLabel',
           'LockLabel',
           'OpacityPushButton']

"""
    Class hierarchy
    
        QPushButton -> RoundedButton
                    -> ColorSelectPushButton
                    -> IconPushButton
                    -> MenuPushButton
        QWidget -> LabeledLineEdit
                -> LabeledSlider
        QSpinBox -> LabeledSpinBox
        QDoubleSpinBox -> LabeledDoubleSpinBox 
        QComboBox -> LabeledComboBox
        QLabel -> IconLabel
               -> VisibilityLabel
               -> LockLabel
               -> OpacityPushButton
"""


class RoundedButton(QPushButton):
    """
        RoundedButton

        Description

            Rounded QPushButton

        Inheritance

            QPushButton -> RoundedButton

        Private attributes

            _bgcolor    str, background color
            _bcolor     str, border color
            _cbgcolor   str, checked state background color
            _cbcolor    str, checked state border color
            _bwidth     int, border width
            _bradius    int, border radius
            _icn        QIcon, button icon
            _icn0       str, normal state icon filename (png)
            _icn1       str, checked state icon filename (png)
            _size       int, button size (icon size = button size - 16)

        Public methods

            setSize(int)
            int = getSize()
            setBorderRadius(int)
            setBorderWidth(int)
            setBackgroundColor(int, int, int)
            setBackgroundColorToWhite()
            setBackgroundColorToBlack()
            setBorderColor(int, int, int)
            setBorderColorToWhite()
            setBorderColorToBlack()
            setCheckedBorderRadius(int)
            setCheckedBorderWidth(int)
            setCheckedBackgroundColor(int, int, int)
            setCheckedBackgroundColorToWhite()
            setCheckedBackgroundColorToBlack()
            setCheckedBorderColor(int, int, int)
            setCheckedBorderColorToWhite()
            setCheckedBorderColorToBlack()
            int = getBorderRadius()
            int = getBorderWidth()
            setNormalIcon(str)
            setCheckedIcon(str)

            inherited QPushButton methods
    """

    # Special method

    def __init__(self, size=64, parent=None):
        super().__init__(parent)

        self._bgcolor = 'black'
        self._bcolor = 'black'
        self._bwidth = 8
        self._bradius = 20
        self._cbgcolor = 'white'
        self._cbcolor = 'white'
        self._icn = None
        self._icn0 = ''
        self._icn1 = ''
        self._size = size

        self.setFlat(True)
        self.setObjectName('RoundedButton')

    # Private method

    def _updateProperties(self):
        self.setFixedSize(self._size, self._size)
        # Stylesheet

        buttonstyle = 'QPushButton:closed [background-color: {}; border-color: {}; ' \
                      'border-style: solid; border-width: {}px; border-radius: {}px;]'.format(self._bgcolor,
                                                                                              self._bcolor,
                                                                                              self._bwidth,
                                                                                              self._bradius)

        buttonstyle += ' QPushButton:pressed [background-color: {}; border-color: {}; ' \
                       'border-style: solid; border-width: {}px; border-radius: {}px;]'.format(self._bgcolor,
                                                                                               self._cbcolor,
                                                                                               self._bwidth,
                                                                                               self._bradius)

        buttonstyle += ' QPushButton:checked [background-color: {}; border-color: {}; ' \
                       'border-style: solid; border-width: {}px; border-radius: {}px;]'.format(self._cbgcolor,
                                                                                               self._cbcolor,
                                                                                               self._bwidth,
                                                                                               self._bradius)
        buttonstyle += ' QPushButton::menu-indicator [image: none;]'
        buttonstyle = buttonstyle.replace('[', '{')
        buttonstyle = buttonstyle.replace(']', '}')
        self.setStyleSheet(buttonstyle)

        # Icons

        self._icn = QIcon()
        if self._icn0 != '' and exists(self._icn0): self._icn.addPixmap(QPixmap(self._icn0),
                                                                        mode=QIcon.Normal,
                                                                        state=QIcon.Off)
        if self._icn1 != '' and exists(self._icn1): self._icn.addPixmap(QPixmap(self._icn1),
                                                                        mode=QIcon.Normal,
                                                                        state=QIcon.On)
        self.setIcon(self._icn)
        size = self._size - 16
        self.setIconSize(QSize(size, size))

    # Public methods

    def setSize(self, size):
        if isinstance(size, int):
            self._size = size
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getSize(self):
        return self._size

    def setBorderRadius(self, v):
        if isinstance(v, int):
            self._bradius = v
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setBorderWidth(self, v):
        if isinstance(v, int):
            self._bwidth = v
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setBackgroundColor(self, r, g, b):
        self._bgcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setBackgroundColorToWhite(self):
        self._bgcolor = 'white'
        self._updateProperties()

    def setBackgroundColorToBlack(self):
        self._bgcolor = 'black'
        self._updateProperties()

    def setBorderColor(self, r, g, b):
        self._bcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setBorderColorToWhite(self):
        self._bcolor = 'white'
        self._updateProperties()

    def setBorderColorToBlack(self):
        self._bgcolor = 'black'
        self._updateProperties()

    def setCheckedBackgroundColor(self, r, g, b):
        self._cbgcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setCheckedBackgroundColorToWhite(self):
        self._cbgcolor = 'white'
        self._updateProperties()

    def setCheckedBackgroundColorToBlack(self):
        self._cbgcolor = 'black'
        self._updateProperties()

    def setCheckedBorderColor(self, r, g, b):
        self._cbcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setCheckedBorderColorToWhite(self):
        self._cbcolor = 'white'
        self._updateProperties()

    def setCheckedBorderColorToBlack(self):
        self._cbcolor = 'black'
        self._updateProperties()

    def setNormalIcon(self, filename):
        if exists(filename):
            if splitext(filename)[1] == '.png':
                self._icn0 = filename
                self._updateProperties()

    def setCheckedIcon(self, filename):
        if exists(filename):
            if splitext(filename)[1] == '.png':
                self._icn1 = filename
                self._updateProperties()

    def getBorderRadius(self):
        return self._bradius

    def getBorderWidth(self, v):
        return self._bwidth


class ColorSelectPushButton(QPushButton):
    """
        ColorPushButton

        Description

            Color selection button

        Inheritance

            QPushButton -> ColorSelectPushButton

        Private attributes

            _color  QColor

        Custom Qt signal

            colorChanged.emit(QWidget)

        Public methods

            int, int, int = getColor()
            float, float, float = getFloatColor()
            QColor = getQColor()
            setColor(int, int, int)
            setQColor(QColor)

            inherited QPushButton methods
    """

    # Custom Qt signal

    colorChanged = pyqtSignal(QWidget)

    # Special method

    def __init__(self, c=QColor('red'), parent=None):
        super().__init__(parent)

        self.setObjectName('colorPushButton')
        self._updateWidgetColor(c)
        self.clicked.connect(self._clicked)

    # Private methods

    def _clicked(self):
        c = QColorDialog().getColor(parent=self, title='Select color', options=QColorDialog.DontUseNativeDialog)
        if c.isValid(): self.setQColor(c)

    def _updateWidgetColor(self, c):
        rgb = 'rgb({}, {}, {})'.format(c.red(),
                                       c.green(),
                                       c.blue())

        self.setStyleSheet("QPushButton#colorPushButton {background-color: " + rgb +
                           "; border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

        """
        self.setStyleSheet("background-color: " + rgb +
                           "; border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;")
        """

        self.setToolTip('Color: {:.2f} {:.2f} {:.2f}\n'
                        'Click to set a new color.'.format(c.redF(),
                                                           c.greenF(),
                                                           c.blueF()))

    # Public methods

    def getColor(self):
        sheet = self.styleSheet()
        c = sheet[sheet.index('(') + 1:sheet.index(')')].split(', ')
        return tuple([int(i) for i in c])

    def getFloatColor(self):
        c = self.getColor()
        return tuple([i/255.0 for i in c])

    def getQColor(self):
        c = self.getColor()
        r = QColor()
        r.setRed(c[0])
        r.setGreen(c[1])
        r.setBlue(c[2])
        return r

    def setColor(self, r, g, b, signal=True):
        if all([isinstance(v, int) for v in (r, g, b)]):
            if all([0 <= v < 256 for v in (r, g, b)]):
                c = QColor()
                c.setRed(r)
                c.setGreen(g)
                c.setBlue(b)
                self._updateWidgetColor(c)
                if signal: self.colorChanged.emit(self)
            else: raise ValueError('parameters are not between 0 and 255.')
        else: raise TypeError('parameters type {} are not all int.')

    def setFloatColor(self, r, g, b, signal=True):
        if all([isinstance(v, float) for v in (r, g, b)]):
            if all([0.0 <= v <= 1.0 for v in (r, g, b)]):
                c = QColor()
                c.setRedF(r)
                c.setGreenF(g)
                c.setBlueF(b)
                self._updateWidgetColor(c)
                if signal: self.colorChanged.emit(self)
            else: raise ValueError('parameters are not between 0.0 and 1.0.')
        else: raise TypeError('parameters type {} are not all int.')

    def setQColor(self, c, signal=True):
        if isinstance(c, QColor):
            self._updateWidgetColor(c)
            if signal: self.colorChanged.emit(self)
        else: raise TypeError('parameter type {} is not QColor'.format(type(c)))


class MenuPushButton(QPushButton):
    """
         MenuPushButton

         Description

             PushButton with popup menu

         Inheritance

             QPushButton -> MenuPushButton

         Private attributes

            _menu       Popupmenu
            _actions    list of QAction

         Public methods

            QAction = addSection(str)
            QAction = insertSection(QAction, str)
            clearPopupMenu()
            QMenu = getPopupMenu()

            inherited QPushButton methods

        Revision:

            27/07/2023  addAction() and insertAction() bugfix, return QAction
     """

    # Special method

    def __init__(self, txt='', parent=None):
        super().__init__(txt, parent)

        self._menu = QMenu(self)
        self._menu.aboutToHide.connect(self._onMenuHide)
        self._actions = list()
        self.pressed.connect(self._onClick)

    # Private method

    def _onClick(self):
        p = self.mapToGlobal(QPoint(0, self.height()))
        self._menu.popup(p)

    def _onMenuHide(self):
        self.setDown(False)

    # Public methods

    def addAction(self, txt: str) -> QAction:
        if isinstance(txt, str):
            action = QAction(txt, self)
            self._menu.addAction(action)
            return action
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def insertAction(self, before: QAction, txt: str) -> QAction:
        if isinstance(before, QAction):
            if isinstance(txt, str):
                action = QAction(txt, self)
                self._menu.insertAction(before, action)
                return action
            else: raise TypeError('parameter type {} is not str.'.format(type(txt)))
        else: raise TypeError('parameter type {} is not QAction.'.format(type(txt)))

    def clearPopupMenu(self) -> None:
        self._menu.clear()

    def getPopupMenu(self) -> QMenu:
        return self._menu


class LabeledLineEdit(QWidget):
    """
        LabeledLineEdit

        Description

            QLineEdit with label and checkbox

        Inheritance

            QWidget -> LabeledLineEdit

        Private attributes

            _edit   QLineEdit
            _label  QLabel
            _check  QCheckBox

        Custom Qt signal

            pressed.emit()

        Public methods

            QLineEdit = getQLineEdit()
            setEditText(str)
            str = getEditText()
            setLabelText(str)
            str = getLabelText()
            setLabelWidth(int)
            int = getLabelWidth()
            setCheckVisibility(bool)
            checkVisibilityOn()
            checkVisibilityOff()
            bool = isChecked()
            setCheckState(bool)

            inherited QWidget methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
                        add eventFilter to redirect child widget mousePressEvent to parent
    """

    # Custom Qt signal

    pressed = pyqtSignal()

    # Special method

    def __init__(self, label='', default='', fontsize=12, parent=None):
        super().__init__(parent)

        # Init widgets

        self._edit = QLineEdit()
        self._edit.setText(default)
        self._edit.setEnabled(True)
        self._label = QLabel()
        self._label.setText(label)
        self._label.setVisible(label != '')
        self._check = QCheckBox()
        self._check.setChecked(True)
        self._check.setVisible(False)
        self._check.stateChanged.connect(lambda: self._edit.setEnabled(self._check.isChecked()))

        # install event filter to redirect child widget mousePressEvent to self

        self._edit.installEventFilter(self)
        self._label.installEventFilter(self)
        self._check.installEventFilter(self)

        font = QFont('Arial', fontsize)
        self._edit.setFont(font)
        self._label.setFont(font)

        # Init layout

        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._check)
        lyout.addWidget(self._label)
        lyout.addWidget(self._edit)
        self.setLayout(lyout)

    # Public methods

    def getQLineEdit(self):
        return self._edit

    def setEditText(self, txt):
        if isinstance(txt, str):
            self._edit.setText(txt)
        else:
            raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def getEditText(self):
        return self._edit.text()

    def setLabelText(self, txt):
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(txt != '')
        else:
            raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def getLabelText(self):
        return self._label.text()

    def setCheckVisibility(self, v):
        if isinstance(v, bool):
            self._check.setVisible(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def checkVisibilityOn(self):
        self.setCheckVisibility(True)

    def checkVisibilityOff(self):
        self.setCheckVisibility(False)

    def getCheckVisibility(self):
        return self._check.isVisible()

    def isChecked(self):
        return self._check.isChecked()

    def setCheckState(self, v):
        if isinstance(v, bool):
            self._check.setChecked(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    # Overriden Qt event

    def mousePressEvent(self, event):
        self.pressed.emit()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonPress:
            # Redirect child press event to self
            self.mousePressEvent(event)
            return True
        else: return False


class LabeledSpinBox(QSpinBox):
    """
        LabeledLineEdit

        Description

            QSpinBox with label

        Inheritance

            QSpinBox -> LabeledSpinBox

        Private attributes

            _label   QLabel

        Custom Qt signal

            pressed.emit()

        Public methods

            str = getTitle()
            setTitle(str)
            setFontSize(int)
            int = getFontSize()

            inherited QSpinBox methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
    """

    # Custom Qt signal

    pressed = pyqtSignal()

    # Special method

    def __init__(self, title='', fontsize=12, titlewidth=0, parent=None):
        super().__init__(parent)

        self._label = QLabel(parent=self)
        self._label.setText(title)
        font = QFont('Arial', fontsize)
        self._label.setFont(font)
        if title != '':
            if titlewidth == 0:
                fm = QFontMetrics(font)
                w = fm.horizontalAdvance(title) + 10
            else: w = titlewidth
            self._label.move(-w, 2)
            style = 'padding-left: {}px;'.format(w)
            self.setStyleSheet(style)
        self.setFont(font)

    # Public methods

    def getTitle(self):
        return self._label.text()

    def setTitle(self, title):
        if isinstance(title, str):
            self._label.setText(title)
            fm = QFontMetrics(self._label.font())
            w = fm.horizontalAdvance(title) + 10
            h = (20 - fm.height()) // 2
            self._label.move(-w, h)
            style = 'padding: 0px 0px 0px {}px'.format(w)
            self.setStyleSheet(style)
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def setFontSize(self, v):
        if isinstance(v, int):
            self._label.font().setPointSize(v)
            self.font().setPointSize(v)
            self.setTitle(self.getTitle())
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getFontSize(self):
        return self.font().pointSize()

    # Overriden Qt event

    def mousePressEvent(self, event):
        self.pressed.emit()
        super().mousePressEvent(event)


class LabeledDoubleSpinBox(QDoubleSpinBox):
    """
         LabeledLineEdit

         Description

             QDoubleSpinBox with label

         Inheritance

             QDoubleSpinBox -> LabeledDoubleSpinBox

         Private attributes

             _label   QLabel

        Custom Qt signal

            pressed.emit()

         Public methods

             str = getTitle()
             setTitle(str)
             setFontSize(int)
             int = getFontSize()

             inherited QDoubleSpinBox methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
     """

    # Custom Qt signal

    pressed = pyqtSignal()

    # Special method

    def __init__(self, title='', fontsize=12, titlewidth=0, parent=None):
        super().__init__(parent)

        self._label = QLabel(parent=self)
        self._label.setText(title)
        font = QFont('Arial', fontsize)
        self._label.setFont(font)
        if title != '':
            if titlewidth == 0:
                fm = QFontMetrics(font)
                w = fm.horizontalAdvance(title) + 10
            else: w = titlewidth
            self._label.move(-w, 2)
            style = 'padding-left: {}px;'.format(w)
            self.setStyleSheet(style)
        self.setFont(font)

    # Public methods

    def getTitle(self):
        return self._label.text()

    def setTitle(self, title):
        if isinstance(title, str):
            self._label.setText(title)
            fm = QFontMetrics(self._label.font())
            w = fm.horizontalAdvance(title) + 10
            h = (20 - fm.height()) // 2
            self._label.move(-w, h)
            style = 'padding: 0px 0px 0px {}px'.format(w)
            self.setStyleSheet(style)
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def setFontSize(self, v):
        if isinstance(v, int):
            self._label.font().setPointSize(v)
            self.font().setPointSize(v)
            self.setTitle(self.getTitle())
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getFontSize(self):
        return self.font().pointSize()

    # Overriden Qt event

    def mousePressEvent(self, event):
        self.pressed.emit()
        super().mousePressEvent(event)


class LabeledSlider(QWidget):
    """
         LabeledLineEdit

         Description

             QSlider with label

         Inheritance

             QQWidget -> LabeledSlider

         Private attributes

             _label   QLabel
             _caption bool, display value ?
             _percent bool, display percent value

         Public methods

             str = getTitle()
             setTitle(str)
             setFontSize(int)
             int = getFontSize()
             setLegendInPercent(bool)
             bool = getLegendInPercent()
             setMinimum(int)
             int = minimum()
             setMaximum(int)
             int = maximum()
             setRange(int, int)
             setValue(int)

             inherited QDoubleSpinBox methods
     """

    # Custom Qt signals

    valueChanged = pyqtSignal(int)
    sliderMoved = pyqtSignal(int)
    sliderReleased = pyqtSignal()
    sliderPressed = pyqtSignal()

    # Special method

    def __init__(self, orient=Qt.Horizontal, title='', fontsize=12, caption=True, percent=False, parent=None):
        super().__init__(parent)

        self._caption = caption
        self._percent = percent

        font = QFont('Arial', fontsize)
        self._title = QLabel()
        self._title.setText(title)
        self._title.setFont(font)
        self._title.setVisible(title != '')

        self._slider = QSlider(orient)
        self._slider.valueChanged.connect(self._valueChanged)
        self._slider.sliderMoved.connect(self._sliderMoved)
        self._slider.sliderReleased.connect(self._sliderReleased)
        self._slider.sliderPressed.connect(self._sliderPressed)
        self._slider.setMinimum(0)
        self._slider.setMaximum(100)
        self._slider.setValue(0)

        self._legend = QLabel()
        self._legend.setText('0')
        self._legend.setFont(font)
        self._legend.setVisible(caption)
        if self._percent: s = '100%'
        else: s = str(self._slider.maximum())
        fm = QFontMetrics(self._title.font())
        w = fm.horizontalAdvance(s)
        self._legend.setFixedWidth(w)
        self._legend.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        if orient == Qt.Horizontal:
            lyout = QHBoxLayout()
            lyout.setContentsMargins(5, 0, 5, 0)
            lyout.setSpacing(5)
            lyout.addWidget(self._title)
            lyout.addWidget(self._legend)
            lyout.addWidget(self._slider)
        else:
            lyout = QVBoxLayout()
            lyout.setContentsMargins(5, 0, 5, 0)
            lyout.setSpacing(5)
            lyout.addWidget(self._title)
            lyout.addWidget(self._legend)
            lyout.addWidget(self._slider)

        self.setLayout(lyout)

    # Private methods

    def _valueChanged(self, v):
        self.valueChanged.emit(v)
        if self._percent:
            d = self._slider.maximum() - self._slider.minimum()
            if d > 0: v = (v - self._slider.minimum()) / d
            else: v = 0
            v = '{}%'.format(int(v * 100))
        else: v = str(v)
        self._legend.setText(v)
        self._slider.setToolTip(v)

    def _sliderMoved(self, v):
        self.sliderMoved.emit(v)

    def _sliderPressed(self):
        self.sliderPressed.emit()

    def _sliderReleased(self):
        self.sliderReleased.emit()

    # Public methods

    def getTitle(self):
        return self._title.text()

    def setTitle(self, title):
        if isinstance(title, str):
            self._title.setText(title)
            self._title.setVisible(title != '')
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def setFontSize(self, v):
        if isinstance(v, int):
            self._title.font().setPointSize(v)
            self._legend.font().setPointSize(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getFontSize(self):
        return self._title.font().pointSize()

    def setLegendInPercent(self, v):
        if isinstance(v, bool): self._percent = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getLegendInPercent(self):
        return self._percent

    def setMaximum(self, v):
        if isinstance(v, int):
            self._slider.setMaximum(v)
            if not self._percent:
                fm = QFontMetrics(self._title.font())
                w = fm.horizontalAdvance(str(self._slider.maximum()))
                self._legend.setFixedWidth(w)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def maximum(self):
        return self._slider.maximum()

    def setMinimum(self, v):
        if isinstance(v, int): self._slider.setMinimum(v)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def minimum(self):
        return self._slider.minimum()

    def setRange(self, vmin, vmax):
        self._slider.setRange(vmin, vmax)
        if not self._percent:
            fm = QFontMetrics(self._title.font())
            w = fm.horizontalAdvance(str(self._slider.maximum()))
            self._legend.setFixedWidth(w)

    def setValue(self, v):
        if isinstance(v, int): self._slider.setValue(v)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def value(self):
        return self._slider.value()


class LabeledComboBox(QComboBox):
    """
         LabeledComboBox

         Description

             QComboBox with label

         Inheritance

             QComboBox -> LabeledComboBox

         Private attributes

             _label   QLabel

        Custom Qt signal

            pressed.emit()

         Public methods

             str = getTitle()
             setTitle(str)
             setFontSize(int)
             int = getFontSize()

             inherited QComboBox methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
     """

    # Custom Qt signal

    pressed = pyqtSignal()

    # Special method

    def __init__(self, title='', fontsize=12, titlewidth=0, parent=None):
        super().__init__(parent)

        self._label = QLabel(parent=self)
        self._label.setText(title)
        font = QFont('Arial', fontsize)
        self._label.setFont(font)
        if title != '':
            if titlewidth == 0:
                fm = QFontMetrics(font)
                w = fm.horizontalAdvance(title) + 5
            else: w = titlewidth
            self._label.move(5, 2)
            style = 'QComboBox [margin-left: {}px; padding-left: 10px]'.format(w)
            style = style.replace('[', '{')
            style = style.replace(']', '}')
            self.setStyleSheet(style)
        self.setFont(font)

    # Public methods

    def getTitle(self):
        return self._label.text()

    def setTitle(self, title):
        if isinstance(title, str):
            self._label.setText(title)
            fm = QFontMetrics(self._label.font())
            w = fm.horizontalAdvance(title) + 5
            h = (20 - fm.height()) // 2
            self._label.move(0, 2)
            style = 'QComboBox [margin-left: {}px; padding-left: 10px]'.format(w, w)
            style = style.replace('[', '{')
            style = style.replace(']', '}')
            self.setStyleSheet(style)
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def setFontSize(self, v):
        if isinstance(v, int):
            self._label.font().setPointSize(v)
            self.font().setPointSize(v)
            self.setTitle(self.getTitle())
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getFontSize(self):
        return self.font().pointSize()

    # Overriden Qt event

    def mousePressEvent(self, event):
        self.pressed.emit()
        super().mousePressEvent(event)


class IconLabel(QLabel):
    """
         IconLabel

         Description

             Flat button with icon

         Inheritance

             QLabel -> IconLabel

        Custom Qt signal

            clicked.emit(QWidget)

         Public methods

             inherited QLabel methods
     """

    # Custom Qt signal

    clicked = pyqtSignal(QWidget)

    # Private class method

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, icon=None, parent=None):
        super().__init__(parent)

        if icon is not None:
            filename = join(self._getDefaultIconDirectory(), icon)
            if exists(filename):
                self._icon = QPixmap(filename)
                self.setPixmap(self._icon)
                self.setMargin(2)
                self.setScaledContents(True)
            else: raise AttributeError('No such file {}.'.format(filename))

        self.setObjectName('iconButton')
        self.setStyleSheet("QLabel#iconButton {border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

    # Overriden Qt event

    def mousePressEvent(self, event):
        self.clicked.emit(self)
        super().mousePressEvent(event)


class IconPushButton(QPushButton):
    """
         IconPushButton

         Description

             Flat button with icon

         Inheritance

             QPushButton -> IconPushButton

        Custom Qt signal

            clicked.emit(QWidget)

         Public methods

             inherited QPushButton methods
     """

    # Private class method

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, icon=None, size=24, parent=None):
        super().__init__(parent)

        if icon is not None:
            filename = join(self._getDefaultIconDirectory(), icon)
            if exists(filename):
                self.setIcon(QIcon(QPixmap(filename)))
            else: raise AttributeError('No such file {}.'.format(filename))

        self.setObjectName('iconPushButton')
        # Stylesheet

        buttonstyle = 'QPushButton#iconPushButton:closed {border-color: rgb(176, 176, 176); ' \
                      'border-style: solid; border-width: 0.5px; border-radius: 5px;}'

        buttonstyle += ' QPushButton#iconPushButton:pressed {border-color: rgb(176, 176, 176); ' \
                       'border-style: solid; border-width: 2px; border-radius: 5px;}'

        buttonstyle += ' QPushButton#iconPushButton:checked {border-color: rgb(0, 125, 255); ' \
                       'border-style: solid; border-width: 5px; border-radius: 3px;}'

        buttonstyle += ' QPushButton#iconPushButton::menu-indicator {image: none;}'
        self.setStyleSheet(buttonstyle)

        self.setIconSize(QSize(size - 8, size - 8))
        self.setFixedSize(size, size)


class VisibilityLabel(QLabel):
    """
        VisibilityLabel

        Description

            Flat button with open/close eye icon

        Inheritance

            QLabel -> VisibilityLabel

        Private attributes

            _visible    bool
            _iconon     QPixmap, icon show state
            _iconoff    QPixmap, icon hide state

        Custom Qt signal

            visibilityChanged.emit(QWidget)
            pressed.emit()

        Public methods

            setVisibilityStateIcon(bool)
            setVisibilityStateIconToView()
            setVisibilityStateIconToHide()
            bool = getVisibilityStateIcon()

            inherited QPushButton methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
    """

    # Custom Qt signal

    visibilityChanged = pyqtSignal(QWidget)
    pressed = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._iconon = QPixmap(join(self._getDefaultIconDirectory(), 'view.png'))
        self._iconoff = QPixmap(join(self._getDefaultIconDirectory(), 'hide.png'))
        self._visible = True
        self.setToolTip('Click to hide.')
        self.setPixmap(self._iconon)
        self.setScaledContents(True)

        self.setObjectName('visibilityButton')
        self.setStyleSheet("QLabel#visibilityButton {border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

    # Public methods

    def setVisibilitySateIcon(self, v):
        if isinstance(v, bool):
            self._visible = v
            if v is True:
                self.setPixmap(self._iconon)
                self.setToolTip('Click to hide.')
            else:
                self.setPixmap(self._iconoff)
                self.setToolTip('Click to show.')
            self.visibilityChanged.emit(self)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVisibilityStateIconToView(self):
        self.setVisibilitySateIcon(True)

    def setVisibilityStateIconToHide(self):
        self.setVisibilitySateIcon(False)

    def getVisibilityStateIcon(self):
        return self._visible

    # Overriden Qt event

    def mousePressEvent(self, event):
        self._visible = not self._visible
        if self._visible:
            self.setPixmap(self._iconon)
            self.setToolTip('Click to hide.')
        else:
            self.setPixmap(self._iconoff)
            self.setToolTip('Click to show.')
        self.pressed.emit()
        self.visibilityChanged.emit(self)
        super().mousePressEvent(event)


class LockLabel(QLabel):
    """
        LockLabel

        Description

            Flat button with lock/unlock icon

        Inheritance

            QLabel -> LockLabel

        Private attributes

            _locked     bool
            _lock       QPixmap, icon lock state
            _unlock     QPixmap, icon unlock state

        Custom Qt signal

            lockChanged.emit(QWidget)
            pressed.emit()

        Public methods

            setLockStateIcon(bool)
            setStateIconToLocked()
            setStateIconToUnlocked()
            bool = getLockStateIcon()

            inherited QPushButton methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
    """

    # Custom Qt signal

    lockChanged = pyqtSignal(QWidget)
    pressed = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._lock = QPixmap(join(self._getDefaultIconDirectory(), 'lock.png'))
        self._unlock = QPixmap(join(self._getDefaultIconDirectory(), 'unlock.png'))
        self._locked = False
        self.setToolTip('Click to lock.')
        self.setPixmap(self._unlock)
        self.setScaledContents(True)

        self.setObjectName('lockButton')
        self.setStyleSheet("QLabel#lockButton {border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

    # Public methods

    def setLockStateIcon(self, v):
        if isinstance(v, bool):
            self._locked = v
            if v is True:
                self.setPixmap(self._lock)
                self.setToolTip('Click to unlock.')
            else:
                self.setPixmap(self._unlock)
                self.setToolTip('Click to lock.')
            self.lockChanged.emit(self)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setStateIconToLocked(self):
        self.setLockStateIcon(True)

    def setStateIconToUnlocked(self):
        self.setLockStateIcon(False)

    def getLockStateIcon(self):
        return self._locked

    # Overriden Qt event

    def mousePressEvent(self, event):
        self._locked = not self._locked
        if self._locked:
            self.setPixmap(self._lock)
            self.setToolTip('Click to unlock.')
        else:
            self.setPixmap(self._unlock)
            self.setToolTip('Click to lock.')
        self.pressed.emit()
        self.lockChanged.emit(self)
        super().mousePressEvent(event)


class OpacityPushButton(QLabel):
    """
        OpacityPushButton

        Description

            Opacity selection button

        Inheritance

            QPushButton -> OpacityPushButton

        Private attributes

            _slider     QSlider

        Custom Qt signal

            opacityChanged.emit(QWidget)
            pressed.emit()

        Public methods

            float = getOpacity()
            setOpacity(float)

            inherited QPushButton methods

        Revisions:

            06/09/2023  add pressed custom Qt signal, update mousePressEvent() method to emit this signal
    """

    # Custom Qt signal

    opacityChanged = pyqtSignal(QWidget)
    pressed = pyqtSignal()

    # Class method

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._label = QLabel()
        font = QFont('Arial', 10)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignHCenter)

        self._slider = QSlider(Qt.Vertical)
        self._slider.setFixedHeight(80)
        self._slider.setTickPosition(QSlider.NoTicks)
        self._slider.setMaximum(100)
        self._slider.setMinimum(0)
        self._slider.setValue(50)
        self._slider.setInvertedAppearance(True)
        self._slider.setToolTip('Opacity {} %'.format(self._slider.value()))
        self._slider.valueChanged.connect(self._opacityChanged)

        self._popup = QMenu(self)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._label)
        self._popup.addAction(a)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._slider)
        self._popup.addAction(a)

        self.setPixmap(QPixmap(join(self._getDefaultIconDirectory(), 'opacity.png')))
        self.setScaledContents(True)

        self.setObjectName('opacityButton')
        self.setStyleSheet("QLabel#opacityButton {border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

        self.setToolTip('Opacity: {} %\nClick to set opacity.'.format(self._slider.value()))

    # Private method

    def _opacityChanged(self, value):
        self._label.setText('{} %'.format(self._slider.value()))
        self._slider.setToolTip('Opacity {} %'.format(self._slider.value()))
        self.setToolTip('Opacity: {} %\nClick to set opacity.'.format(self._slider.value()))
        self.opacityChanged.emit(self)

    # Public method

    def setOpacity(self, v):
        self._slider.setValue(int(v * 100))

    def getOpacity(self):
        return self._slider.value() / 100

    # Qt Event

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.pressed.emit()
        if event.button() == Qt.LeftButton:
            self._popup.exec(event.globalPos())


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    test = 6
    app = QApplication(argv)
    layout = QHBoxLayout()
    layout.setContentsMargins(10, 10, 10, 10)
    if test == 1:
        button = ColorSelectPushButton()
        button.setFixedWidth(32)
        button.setFixedHeight(32)
        print(button.objectName())
        layout.addWidget(button)
    elif test == 2:
        edit = LabeledLineEdit('Lastname', 'Unknown')
        edit.checkVisibilityOn()
        layout.addWidget(edit)
    elif test == 3:
        button = RoundedButton()
        button.setCheckable(True)
        button.setSize(48)
        button.setBorderWidth(5)
        button.setBorderRadius(10)
        button.setBorderColorToWhite()
        button.setBackgroundColorToBlack()
        button.setCheckedBorderColorToBlack()
        button.setCheckedBackgroundColorToWhite()
        button.setNormalIcon('/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/gui/baricons/whand.png')
        button.setCheckedIcon('/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/gui/baricons/hand.png')
        print(button.objectName())
        layout.addWidget(button)
    elif test == 4:
        slider = LabeledSlider(orient=Qt.Horizontal, title='Try', fontsize=10, caption=True, percent=False)
        slider.setRange(0, 200)
        slider.setValue(100)
        layout.addWidget(slider)
        layout.setContentsMargins(0, 0, 0, 0)
    elif test == 5:
        spin = LabeledSpinBox(title='Try', fontsize=10)
        spin.setRange(1, 20)
        spin.setValue(1)
        layout.addWidget(spin)
        layout.setContentsMargins(0, 0, 0, 0)
    elif test == 6:
        button = MenuPushButton('Try')
        button.setFixedWidth(150)
        button.addAction('submenu1')
        button.addAction('submenu2')
        layout.addStretch()
        layout.addWidget(button)
        layout.addStretch()
    else:
        slider = LabeledSlider(orient=Qt.Horizontal, title='Try', fontsize=12, caption=True, percent=False)
        slider.setRange(0, 200)
        slider.setValue(100)
        spin = LabeledSpinBox(title='An example', fontsize=12)
        spin.setRange(1, 20)
        spin.setValue(1)
        layout.addWidget(spin)
        combo = LabeledComboBox(title='An example', fontsize=12)
        combo.addItem('Un')
        combo.addItem('Deux')
        combo.addItem('Trois')
        layout.addWidget(combo)
        layout.addWidget(spin)
        layout.addWidget(slider)
        layout.setContentsMargins(0, 0, 0, 0)
    main = QWidget()
    main.setLayout(layout)
    main.show()
    app.exec_()
