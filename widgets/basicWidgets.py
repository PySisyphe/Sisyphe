"""
External packages/modules
-------------------------

    - darkdetect, OS dark Mode detection, https://github.com/albertosottile/darkdetect
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

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
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QEvent
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
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QFontDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

# noinspection PyCompatibility
import __main__

__all__ = ['messageBox',
           'findFontPath',
           'colorDialog',
           'fontDialog',
           'RoundedButton',
           'ColorSelectPushButton',
           'FontSelect',
           'LabeledLineEdit',
           'LabeledSpinBox',
           'QDoubleSpinBox2',
           'LabeledDoubleSpinBox',
           'LabeledSlider',
           'LabeledComboBox',
           'IconLabel',
           'IconPushButton',
           'MenuPushButton',
           'VisibilityLabel',
           'LockLabel',
           'OpacityPushButton',
           'WidthPushButton']

FONTPATHS: dict[str, str] = dict()

"""
function
~~~~~~~~

    - messageBox
    - colorDialog
    - fontDialog
    - findFontPath
"""


def messageBox(parent: QWidget | None = None,
               title: str = '',
               text: str = '',
               icon: int | QMessageBox.Icon = QMessageBox.Warning,
               buttons: QMessageBox.StandardButtons = QMessageBox.Ok,
               default: QMessageBox.StandardButton = QMessageBox.Ok) -> int:
    """
    Description
    ~~~~~~~~~~~

    QMessageBox with custom title bar.
    win32 bug fix, title bar color in dark mode.

    Parameters
    ~~~~~~~~~~~
    parent: QWidget | None
    title: str (optional)
        default ''
    text: str (optional)
        default ''
    icon: int | QMessageBox.Icon (optional)
        QMessageBox.NoIcon (0), QMessageBox.Information (1), QMessageBox.Warning (2), QMessageBox.Critical (3),
        QMessageBox.Question (4) (default QMessageBox.Warning)
    buttons: QMessageBox.StandardButtons (optional)
        QMessageBox.Ok | QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Close | QMessageBox.Discard |
        QMessageBox.Apply | QMessageBox.Reset | QMessageBox.RestoreDefaults | QMessageBox.Help | QMessageBox.SaveAll |
        QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No | QMessageBox.NoToAll | QMessageBox.Abort |
        QMessageBox.Retry | QMessageBox.Ignore | QMessageBox.NoButton (default QMessageBox.Ok)
    default: QMessageBox.StandardButton (optional)
        QMessageBox.Ok | QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Close | QMessageBox.Discard |
        QMessageBox.Apply | QMessageBox.Reset | QMessageBox.RestoreDefaults | QMessageBox.Help | QMessageBox.SaveAll |
        QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No | QMessageBox.NoToAll | QMessageBox.Abort |
        QMessageBox.Retry | QMessageBox.Ignore | QMessageBox.NoButton (default QMessageBox.Ok)

    Returns
    ~~~~~~~
    int
    """
    # < Revision 30/06/2026
    # msgbox = QMessageBox(parent)
    # msgbox.setWindowTitle(title)
    # msgbox.setIcon(icon)
    # msgbox.setText(text)
    if isinstance(icon, int): icon = QMessageBox.Icon(icon)
    msgbox = QMessageBox(icon, title, text, parent=parent)
    # Revision 30/06/2026 >
    msgbox.setStandardButtons(buttons)
    msgbox.setDefaultButton(default)
    if platform == 'win32':
        try: __main__.updateWindowTitleBarColor(msgbox)
        except: pass
    return msgbox.exec()

def colorDialog(parent: QWidget | None = None,
                title: str = '',
                color: QColor | None = None) -> QColor | None:
    """
    Description
    ~~~~~~~~~~~

    QColorDialog with custom title bar.
    win32 bug fix, title bar color in dark mode.

    Parameters
    ~~~~~~~~~~~
    parent: QWidget | None
    title: str
    color: QColor | None
        initial color

    Returns
    ~~~~~~~
    QColor | None

    Creation: 18/03/2025
    """
    dialog = QColorDialog(parent=parent)
    if color is not None: dialog.setCurrentColor(color)
    dialog.setWindowTitle(title)
    if platform == 'win32':
        dialog.setOption(QColorDialog.DontUseNativeDialog)
        try: __main__.updateWindowTitleBarColor(dialog)
        except: pass
    dialog.move(QApplication.primaryScreen().availableGeometry().center() - dialog.rect().center())
    if dialog.exec() > 0: return dialog.currentColor()
    else: return None

def fontDialog(parent: QWidget | None = None,
               title: str = '',
               font: QFont | None = None) -> QFont | None:
    """
    Description
    ~~~~~~~~~~~

    QFontDialog with custom title bar.
    win32 bug fix, title bar color in dark mode.

    Parameters
    ~~~~~~~~~~~
    parent: QWidget | None
    title: str
    font: QFont | None
        initial font

    Returns
    ~~~~~~~
    QFont | None

    Creation: 18/03/2025
    """
    dialog = QFontDialog(parent=parent)
    if font is not None: dialog.setCurrentFont(font)
    dialog.setWindowTitle(title)
    if platform == 'win32':
        dialog.setOption(QFontDialog.DontUseNativeDialog)
        try: __main__.updateWindowTitleBarColor(dialog)
        except: pass
    dialog.move(QApplication.primaryScreen().availableGeometry().center() - dialog.rect().center())
    if dialog.exec() > 0: return dialog.currentFont()
    else: return None

# < Revision 03/05/2026
# add findFontPath function
def findFontPath(name: str) -> str:
    """
    Description
    ~~~~~~~~~~~

    Get font path from font family name.

    Parameters
    ~~~~~~~~~~~
    name: str
        font family name

    Returns
    ~~~~~~~
    str
        font path

    Creation: 03/05/2026
    """
    if len(FONTPATHS) == 0:
        from matplotlib.font_manager import findSystemFonts
        from matplotlib.font_manager import FontProperties
        try:
            fontpaths = findSystemFonts(fontext='ttf')
            if len(fontpaths) > 0:
                for path in fontpaths:
                    fontname = FontProperties(fname=path)
                    FONTPATHS[fontname.get_name()] = path
        except: return 'Arial'
    if name in FONTPATHS:
        return FONTPATHS[name]
    else: return 'Arial'
# Revision 03/05/2026 >

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QPushButton -> RoundedButton
                  -> IconPushButton
                  -> MenuPushButton
    - QWidget -> LabeledLineEdit
              -> LabeledSlider
              -> FontSelect
              -> LabeledSpinBox
              -> LabeledDoubleSpinBox
              -> LabeledComboBox
    - QDoubleSpinBox -> QDoubleSpinBox2
    - QLabel -> IconLabel
             -> ColorSelectPushButton
             -> VisibilityLabel
             -> LockLabel
             -> OpacityPushButton
             -> WidthPushButton
"""


class RoundedButton(QPushButton):
    """
    RoundedButton class

    Description
    ~~~~~~~~~~~

    The RoundedButton class is a custom widget that extends the QPushButton class from PyQt5. It provides a button
    with customizable rounded corners and additional styling options. This class allows you to set various properties
    such as background color, border color, border width, border radius, and icons for different button states
    (normal and checked).

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> RoundedButton

    Last revision: 07/12/2024
    """

    # Special method

    """
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
    """

    def __init__(self, size: int = 64, parent: QWidget | None = None) -> None:
        """
        RoundedButton instance constructor.

        Parameters
        ----------
        size : int (optional)
            square dimensions of the button (default 64).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._bgcolor: str = 'black'
        self._bcolor: str = 'black'
        self._bwidth: int = 8
        self._bradius: int = 20
        self._cbgcolor: str = 'white'
        self._cbcolor: str = 'white'
        self._icn: QIcon | None = None
        self._icn0: str = ''
        self._icn1: str = ''
        self._size: int = size

        self.setFlat(True)
        # < Revision 07/12/2024
        # do not change checkstate with return key
        self.setDefault(False)
        self.setAutoDefault(False)
        # Revision 07/12/2024 >
        self.setObjectName('RoundedButton')

    # Private method

    def _updateProperties(self) -> None:
        """
        Internal method to update the widget properties, including style sheet, size, and icons.
        """
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
        if self._icn0 != '' and exists(self._icn0):
            # noinspection PyUnresolvedReferences
            self._icn.addPixmap(QPixmap(self._icn0), mode=QIcon.Normal, state=QIcon.Off)
        if self._icn1 != '' and exists(self._icn1):
            # noinspection PyUnresolvedReferences
            self._icn.addPixmap(QPixmap(self._icn1), mode=QIcon.Normal, state=QIcon.On)
        self.setIcon(self._icn)
        size = self._size - 16
        self.setIconSize(QSize(size, size))

    # Public methods

    def setSize(self, size: int) -> None:
        """
        Set the size of the button.

        Parameters
        ----------
        size : int
            side length of the square button.
        """
        if isinstance(size, int):
            self._size = size
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getSize(self) -> int:
        """
        Get the current size of the button.

        Returns
        -------
        int
            side length of the square button.
        """
        return self._size

    def setBorderRadius(self, v: int) -> None:
        """
        Set the border radius of the button.

        Parameters
        ----------
        v : int
            radius value in pixels.
        """
        if isinstance(v, int):
            self._bradius = v
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setBorderWidth(self, v: int) -> None:
        """
        Set the border width of the button.

        Parameters
        ----------
        v : int
            thickness of the border in pixels.
        """
        if isinstance(v, int):
            self._bwidth = v
            self._updateProperties()
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setBackgroundColor(self, r: int, g: int, b: int) -> None:
        """
        Set the background color of the button using RGB values.

        Parameters
        ----------
        r : int
            red component (0-255).
        g : int
            green component (0-255).
        b : int
            blue component (0-255).
        """
        self._bgcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setBackgroundColorToWhite(self) -> None:
        """
        Set the background color of the button to white.
        """
        self._bgcolor = 'white'
        self._updateProperties()

    def setBackgroundColorToBlack(self) -> None:
        """
        Set the background color of the button to black.
        """
        self._bgcolor = 'black'
        self._updateProperties()

    def setBorderColor(self, r: int, g: int, b: int) -> None:
        """
        Set the border color of the button using RGB values.

        Parameters
        ----------
        r : int
            red component (0-255).
        g : int
            green component (0-255).
        b : int
            blue component (0-255).
        """
        self._bcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setBorderColorToWhite(self) -> None:
        """
        Set the border color of the button to white.
        """
        self._bcolor = 'white'
        self._updateProperties()

    def setBorderColorToBlack(self) -> None:
        """
        Set the border color of the button to black.
        """
        self._bgcolor = 'black'
        self._updateProperties()

    def setCheckedBackgroundColor(self, r: int, g: int, b: int) -> None:
        """
        Set the background color for the checked state using RGB values.

        Parameters
        ----------
        r : int
            red component (0-255).
        g : int
            green component (0-255).
        b : int
            blue component (0-255).
        """
        self._cbgcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setCheckedBackgroundColorToWhite(self) -> None:
        """
        Set the background color for the checked state to white.
        """
        self._cbgcolor = 'white'
        self._updateProperties()

    def setCheckedBackgroundColorToBlack(self) -> None:
        """
        Set the background color for the checked state to black.
        """
        self._cbgcolor = 'black'
        self._updateProperties()

    def setCheckedBorderColor(self, r: int, g: int, b: int) -> None:
        """
        Set the border color for the checked state using RGB values.

        Parameters
        ----------
        r : int
            red component (0-255).
        g : int
            green component (0-255).
        b : int
            blue component (0-255).
        """
        self._cbcolor = 'rgb({}, {}, {})'.format(r, g, b)
        self._updateProperties()

    def setCheckedBorderColorToWhite(self) -> None:
        """
        Set the border color for the checked state to white.
        """
        self._cbcolor = 'white'
        self._updateProperties()

    def setCheckedBorderColorToBlack(self) -> None:
        """
        Set the border color for the checked state to black.
        """
        self._cbcolor = 'black'
        self._updateProperties()

    def setNormalIcon(self, filename: str) -> None:
        """
        Set the icon used in the normal (unchecked) state.

        Parameters
        ----------
        filename : str
            path to the .png image file.
        """
        if exists(filename):
            if splitext(filename)[1] == '.png':
                self._icn0 = filename
                self._updateProperties()
        else: raise IOError('no such file {}'.format(filename))

    def setCheckedIcon(self, filename: str) -> None:
        """
        Set the icon used in the checked state.

        Parameters
        ----------
        filename : str
            path to the .png image file.
        """
        if exists(filename):
            if splitext(filename)[1] == '.png':
                self._icn1 = filename
                self._updateProperties()
        else: raise IOError('no such file {}'.format(filename))

    def getBorderRadius(self) -> int:
        """
        Get the border radius of the button.

        Returns
        -------
        int
           current border radius value in pixels.
        """
        return self._bradius

    # noinspection PyUnusedLocal
    def getBorderWidth(self) -> int:
        """
        Get the border width of the button.

        Returns
        -------
        int
            current border width in pixels.
        """
        return self._bwidth


# < Revision 30/03/2025
# replace ancestor class QPushButton with QLabel
# class ColorSelectPushButton(QPushButton):
# Revision 30/03/2025 >
class ColorSelectPushButton(QLabel):
    """
    ColorPushButton class

    Description
    ~~~~~~~~~~~

    The ColorSelectPushButton class is a custom widget that extends the QPushButton class from PyQt5widget. It provides
    a color selection button and a color preview label. The color selection button opens a color dialog when clicked,
    and the color preview label displays the selected color.

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> ColorSelectPushButton

    Last revision: 30/03/2025
    """

    # Custom Qt signal

    colorChanged: pyqtSignal = pyqtSignal(QWidget)

    # Class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, c: QColor = QColor('red'), parent: QWidget | None = None) -> None:
        """
        ColorSelectPushButton instance constructor.

        Parameters
        ----------
        c : QColor (optional)
            initial color of the button (default QColor('red')).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self.setObjectName('colorPushButton')
        self._icon: QPixmap = QPixmap(join(self._getDefaultIconDirectory(), 'palette.png'))
        self.setPixmap(self._icon)
        self.setMargin(2)
        self.setScaledContents(True)
        self._updateWidgetColor(c)

    # Private methods

    def _clicked(self) -> None:
        """
        Internal method to handle the click event and open a color dialog.
        """
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Select color', options=QColorDialog.DontUseNativeDialog)
        # if c.isValid(): self.setQColor(c)
        # noinspection PyTypeChecker
        r = colorDialog(title='Select color', color=self.getQColor())
        if r is not None:
            if r.isValid(): self.setQColor(r)
        # Revision 18/03/2025 >

    def _updateWidgetColor(self, c: QColor) -> None:
        """
        Internal method to update the widget's style sheet and tooltip based on the provided color.

        Parameters
        ----------
        c : QColor
            color to apply to the widget.
        """
        rgb = 'rgb({}, {}, {})'.format(c.red(),
                                       c.green(),
                                       c.blue())

        self.setStyleSheet("QLabel#colorPushButton {background-color: " + rgb +
                           "; border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

        self.setToolTip('Color: {:.2f} {:.2f} {:.2f}\n'
                        'Click to set a new color.'.format(c.redF(),
                                                           c.greenF(),
                                                           c.blueF()))

    # Public methods

    def getColor(self) -> tuple[int, ...]:
        """
        Get the color as a tuple of integers.

        Returns
        -------
        tuple[int, ...]
            tuple containing (Red, Green, Blue) values.
        """
        sheet = self.styleSheet()
        c = sheet[sheet.index('(') + 1:sheet.index(')')].split(', ')
        return tuple([int(i) for i in c])

    def getFloatColor(self) -> tuple[float, ...]:
        """
        Get the color as a tuple of floats.

        Returns
        -------
        tuple[float, ...]
            tuple containing (Red, Green, Blue) values scaled between 0.0 and 1.0.
        """
        c = self.getColor()
        return tuple([i/255.0 for i in c])

    def getQColor(self) -> QColor:
        """
        Get the color as a PyQt QColor object.

        Returns
        -------
        QColor
            QColor representation of the current button color.
        """
        c = self.getColor()
        r = QColor()
        r.setRed(c[0])
        r.setGreen(c[1])
        r.setBlue(c[2])
        return r

    def setColor(self, r: int, g: int, b: int, signal: bool = True) -> None:
        """
        Set the button's color using integer RGB values.

        Parameters
        ----------
        r : int
            red component (0-255).
        g : int
            green component (0-255).
        b : int
            blue component (0-255).
        signal : bool
            whether to emit the colorChanged signal.
        """
        if all([isinstance(v, int) for v in (r, g, b)]):
            if all([0 <= v < 256 for v in (r, g, b)]):
                c = QColor()
                c.setRed(r)
                c.setGreen(g)
                c.setBlue(b)
                self._updateWidgetColor(c)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.colorChanged.emit(self)
            else: raise ValueError('parameters are not between 0 and 255.')
        else: raise TypeError('parameters type {} are not all int.')

    def setFloatColor(self, r: float, g: float, b: float, signal: bool = True) -> None:
        """
        Set the button's color using floating-point RGB values.

        Parameters
        ----------
        r : float
            red component (0.0-1.0).
        g : float
            green component (0.0-1.0).
        b : float
            Blue component (0.0-1.0).
        signal : bool
            whether to emit the colorChanged signal.
        """
        if all([isinstance(v, float) for v in (r, g, b)]):
            if all([0.0 <= v <= 1.0 for v in (r, g, b)]):
                c = QColor()
                c.setRedF(r)
                c.setGreenF(g)
                c.setBlueF(b)
                self._updateWidgetColor(c)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.colorChanged.emit(self)
            else: raise ValueError('parameters are not between 0.0 and 1.0.')
        else: raise TypeError('not all parameter types are float.')

    def setQColor(self, c: QColor, signal: bool = True) -> None:
        """
        Set the button's color using a PyQt QColor object.

        Parameters
        ----------
        c : QColor
            QColor to apply.
        signal : bool
            whether to emit the colorChanged signal.
        """
        if isinstance(c, QColor):
            self._updateWidgetColor(c)
            if signal:
                # noinspection PyUnresolvedReferences
                self.colorChanged.emit(self)
        else: raise TypeError('parameter type {} is not QColor'.format(type(c)))

    # Overridden Qt event

    # < Revision 30/03/2025
    # add mousePressEvent method
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event to trigger color selection.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        # self.clicked.emit()
        super().mousePressEvent(event)
        self._clicked()
    # Revision 30/03/2025 >


class FontSelect(QWidget):
    """
    FontSelect class

    Description
    ~~~~~~~~~~~

    The FontSelect class is a custom widget to select font.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> FontSelect

    Creation: 15/03/2025
    Last revision: 18/03/2025
    """

    # Custom Qt signal

    fontChanged: pyqtSignal = pyqtSignal(QWidget, str)

    # Special method

    """
    Private attributes

    _field          QLineEdit
    _open           QPushbutton
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        FontSelect instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)
        self.setObjectName('FontSelect')

        # Init QLayout

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._field = QLineEdit()
        self._field.setText(self.font().family())
        self._field.setReadOnly(True)
        self._open = QPushButton('Aa')
        self._open.setToolTip('Font selection dialog.')
        # noinspection PyUnresolvedReferences
        self._open.clicked.connect(self._openFontDialog)
        self._default = QPushButton('X')
        self._default.setToolTip('Set default font..')
        # noinspection PyUnresolvedReferences
        self._default.clicked.connect(lambda _: self.setDefaultFont(True))

        self._layout.addWidget(self._field)
        self._layout.addWidget(self._open)
        self._layout.addWidget(self._default)

    # Private methods

    def _openFontDialog(self) -> None:
        """
        Internal method to open a font selection dialog and update the display field.
        """
        if self._field.text() == '': font = self.font()
        else: font = QFont(self._field.text())
        # < Revision 18/03/2025
        # r = QFontDialog.getFont(font, caption='Font selection', parent=self)
        # if r[1]:
        #    self._field.setText(r[0].family())
        #    # noinspection PyUnresolvedReferences
        #    self.fontChanged.emit(self, r[0].family())
        # noinspection PyTypeChecker
        r = fontDialog(title='Font selection', font=font)
        if r is not None:
            self._field.setText(r.family())
            # noinspection PyUnresolvedReferences
            self.fontChanged.emit(self, r.family())
        # Revision 18/03/2025 >

    # Public methods

    def isEmpty(self) -> bool:
        """
        Check if the font name field is empty.

        Returns
        -------
        bool
            True if the field is empty, False otherwise.
        """
        return self._field.text() == ''

    def getFontFamily(self) -> str:
        """
        Get the current font family string from the display field.

        Returns
        -------
        str
            name of the current font family.
        """
        return self._field.text()

    def getFont(self) -> QFont:
        """
        Get the QFont object based on the current selection.

        Returns
        -------
        QFont
            current font object.
        """
        if self._field.text() != '': return QFont(self._field.text(), self.font().pointSize())
        else: return self.font()

    # < Revision 03/05/2026
    # add getFontPath method
    def getFontPath(self) -> str:
        """
        Get the system path of the current font.

        Returns
        -------
        str
            file path of the current font.
        """
        font = self.getFont()
        return findFontPath(font.family())
    # Revision 03/05/2026 >

    def setFont(self, name: str | QFont, signal: bool = False) -> None:
        """
        Set a new font based on its name or a QFont object.

        Parameters
        ----------
        name : str | QFont
            name of the font family or QFont object.
        signal : bool
            if True, emits the fontChanged signal.
        """
        # < Revision 16/03/2025
        if isinstance(name, QFont): name = name.family()
        # Revision 16/03/2025 >
        if name in QFontDatabase().families():
            self._field.setText(name)
            if signal:
                # noinspection PyUnresolvedReferences
                self.fontChanged.emit(self, name)
        else: raise ValueError('{} invalid font family.'.format(name))

    def setDefaultFont(self, signal: bool = False):
        """
        Reset the field to the system's default font family.

        Parameters
        ----------
        signal : bool
            if True, emits the fontChanged signal.
        """
        name = self.font().defaultFamily()
        self._field.setText(name)
        if signal:
            # noinspection PyUnresolvedReferences
            self.fontChanged.emit(self, name)


class MenuPushButton(QPushButton):
    """
    MenuPushButton class

    Description
    ~~~~~~~~~~~

    The MenuPushButton class is a custom widget that extends the QPushButton class from PyQt5. It provides a button
    with a popup menu. The popup menu can be customized with various actions. It includes methods to add, remove, and
    modify actions in the popup menu.

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> MenuPushButton

    Last revision: 27/07/2023
    """

    # Special method

    """
    Private attributes

    _menu       QMenu, popupmenu
    _actions    list[QAction]
    """

    def __init__(self, txt: str = '', parent: QWidget | None = None) -> None:
        """
        MenuPushButton instance constructor.

        Parameters
        ----------
        txt : str (optional)
            text to display on the button (default '').
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(txt, parent)

        self._menu = QMenu(self)
        # noinspection PyUnresolvedReferences
        self._menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._menu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._menu.setAttribute(Qt.WA_TranslucentBackground, True)

        # noinspection PyUnresolvedReferences
        self._menu.aboutToHide.connect(self._onMenuHide)
        self._actions = list()
        # noinspection PyUnresolvedReferences
        self.pressed.connect(self._onClick)

    # Private method

    def _onClick(self) -> None:
        """
        Internal method to calculate the position and show the popup menu when clicked.
        """
        p = self.mapToGlobal(QPoint(0, self.height()))
        self._menu.popup(p)

    def _onMenuHide(self) -> None:
        """
        Internal method to update state when the menu is hidden.
        """
        self.setDown(False)

    # Public methods

    def addAction(self, txt: str) -> QAction:
        """
        Add a new action to the popup menu using its text description.

        Parameters
        ----------
        txt : str
            label for the action.

        Returns
        -------
        QAction
            created action object.
        """
        if isinstance(txt, str):
            action = QAction(txt, self)
            self._menu.addAction(action)
            return action
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def insertAction(self, before: QAction, txt: str) -> QAction:
        """
        Insert a new action into the popup menu before a specific existing action.

        Parameters
        ----------
        before : QAction
            action to insert before.
        txt : str
            label for the new action.

        Returns
        -------
        QAction
            created action object.
        """
        if isinstance(before, QAction):
            if isinstance(txt, str):
                action = QAction(txt, self)
                self._menu.insertAction(before, action)
                return action
            else: raise TypeError('parameter type {} is not str.'.format(type(txt)))
        else: raise TypeError('parameter type {} is not QAction.'.format(type(txt)))

    def clearPopupMenu(self) -> None:
        """
        Clear all actions from the popup menu.
        """
        self._menu.clear()

    def getPopupMenu(self) -> QMenu:
        """
        Get the underlying popup menu object.

        Returns
        -------
        QMenu
            popup menu.
        """
        return self._menu

    def setPopupMenu(self, popup: QMenu) -> None:
        """
        Set a custom popup menu for the button.

        Parameters
        ----------
        popup : QMenu
            replacement menu object.
        """
        self._menu = popup


class LabeledLineEdit(QWidget):
    """
    LabeledLineEdit class

    Description
    ~~~~~~~~~~~

    The LabeledLineEdit class is a custom widget that extends the QLineEdit class from PyQt5. It provides a line edit
    widget with a label and an optional checkbox. The line edit widget can be used to input and display text, while the
    label provides context for the input field. It provides functionality to set and get the label text, adjust font
    size and check box visibility.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> LabeledLineEdit

    Last revision: 07/03/2025
    """

    # Custom Qt signal

    pressed: pyqtSignal = pyqtSignal()
    returnPressed: pyqtSignal = pyqtSignal()
    textChanged: pyqtSignal = pyqtSignal()

    # Special method

    """
    Private attributes

    _edit   QLineEdit
    _label  QLabel
    _check  QCheckBox
    """

    def __init__(self,
                 label: str = '',
                 default: str = '',
                 fontsize: int = 12,
                 parent: QWidget | None = None) -> None:
        """
        LabeledLineEdit instance constructor.

        Parameters
        ----------
        label : str (optional)
            text to display in the label (default '').
        default : str (optional)
            initial value for the line edit field (default '').
        fontsize : int (optional)
            font size for both label and input (default 12).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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
        # noinspection PyUnresolvedReferences
        self._check.stateChanged.connect(lambda: self._edit.setEnabled(self._check.isChecked()))
        # noinspection PyUnresolvedReferences
        self._edit.textChanged.connect(lambda: self.textChanged.emit())
        # noinspection PyUnresolvedReferences
        self._edit.returnPressed.connect(lambda: self.returnPressed.emit())

        # install event filter to redirect child widget mousePressEvent to self

        self._edit.installEventFilter(self)
        self._label.installEventFilter(self)
        self._check.installEventFilter(self)

        # < Revision 07/03/2024
        if platform == 'darwin':
            font = QFont('Arial', fontsize)
            self._edit.setFont(font)
            self._label.setFont(font)
        # Revision 07/03/2024 >

        # Init layout

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(5, 5, 5, 5)
        else: lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._check)
        lyout.addWidget(self._label)
        lyout.addWidget(self._edit)
        self.setLayout(lyout)

    # Public methods

    def getQLineEdit(self) -> QLineEdit:
        """
        Get the underlying QLineEdit object.

        Returns
        -------
        QLineEdit
            line edit widget.
        """
        return self._edit

    def setEditText(self, txt: str) -> None:
        """
        Set the text content of the line edit field.

        Parameters
        ----------
        txt : str
            new string to display.
        """
        if isinstance(txt, str): self._edit.setText(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def getEditText(self) -> str:
        """
        Get the text content of the line edit field.

        Returns
        -------
        str
            current value in the line edit.
        """
        return self._edit.text()

    def setLabelText(self, txt: str) -> None:
        """
        Set and manage the visibility of the accompanying label.

        Parameters
        ----------
        txt : str
            text to display in the label.
        """
        if isinstance(txt, str):
            self._label.setText(txt)
            self._label.setVisible(txt != '')
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def getLabelText(self) -> str:
        """
        Get the text of the label widget.

        Returns
        -------
        str
            current label text.
        """
        return self._label.text()

    def setCheckVisibility(self, v: bool) -> None:
        """
        Set whether the checkbox is visible or not.

        Parameters
        ----------
        v : bool
            True to show, False to hide.
        """
        if isinstance(v, bool): self._check.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def checkVisibilityOn(self) -> None:
        """
        Show the checkbox.
        """
        self.setCheckVisibility(True)

    def checkVisibilityOff(self) -> None:
        """
        Hide the checkbox.
        """
        self.setCheckVisibility(False)

    def getCheckVisibility(self) -> bool:
        """
        Get the visibility status of the checkbox.

        Returns
        -------
        bool
            True if visible, False otherwise.
        """
        return self._check.isVisible()

    def isChecked(self) -> bool:
        """
        Check if the internal checkbox is checked.

        Returns
        -------
        bool
            current state of the checkbox.
        """
        return self._check.isChecked()

    def setCheckState(self, v: bool) -> None:
        """
        Set the checked or unchecked state of the internal checkbox.

        Parameters
        ----------
        v : bool
            True for checked, False for unchecked.
        """
        if isinstance(v, bool): self._check.setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isEmpty(self) -> bool:
        """
        Check if the line edit field is empty.

        Returns
        -------
        bool
            True if no text exists, False otherwise.
        """
        return self._edit.text() == ''

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """
        Handle mouse press events and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        super().mousePressEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Intercept events from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        if event.type() == QEvent.MouseButtonPress:
            # Redirect child press event to self
            # noinspection PyTypeChecker
            self.mousePressEvent(event)
            return True
        else: return False


class LabeledSpinBox(QWidget):
    """
    LabeledSpinBox class

    Description
    ~~~~~~~~~~~

    The LabeledSpinBox class is a custom widget that extends the QSpinBox class from PyQt5. It provides a spinbox
    widget with a label.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> LabeledSpinBox

    Creation: 13/03/2025
    """

    # Custom Qt signal

    pressed: pyqtSignal = pyqtSignal()
    textChanged: pyqtSignal = pyqtSignal(str)
    valueChanged: pyqtSignal = pyqtSignal(int)

    # Special method

    """
    Private attribute

    _label  QLabel
    _spin   QSpinBox
    """

    def __init__(self,
                 title: str = '',
                 fontsize: int = 12,
                 parent: QWidget | None = None) -> None:
        """
        LabeledSpinBox instance constructor.

        Parameters
        ----------
        title : str (optional)
            label text to display inf front of the spinbox (default '').
        fontsize : int (optional)
            font size for both the label and the spinbox (default 12).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._label: QLabel = QLabel(parent=self)
        self._label.setText(title)
        self._spin: QSpinBox = QSpinBox(parent=self)
        # noinspection PyUnresolvedReferences
        self._spin.textChanged.connect(lambda v: self.textChanged.emit(v))
        # noinspection PyUnresolvedReferences
        self._spin.valueChanged.connect(lambda v: self.valueChanged.emit(v))
        self.setFontSize(fontsize)

        # Init layout

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(5, 5, 5, 5)
        else: lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._label)
        lyout.addWidget(self._spin)
        self.setLayout(lyout)

    def __getattr__(self, attr):
        """
        Allow access to attributes of the internal spinbox.
        """
        if hasattr(self._spin, attr): return getattr(self._spin, attr)
        else: raise AttributeError(self.__class__.__name__ + ' has no attribute named ' + attr)

    # Public methods

    def getTitle(self) -> str:
        """
        Get the label text of the widget.

        Returns
        -------
        str
            title associated with the spinbox.
        """
        return self._label.text()

    def setTitle(self, title: str) -> None:
        """
        Set the label text of the widget.

        Parameters
        ----------
        title : str
            new text for the title associated with the spinbox.
        """
        self._label.setText(title)

    def setFontSize(self, v: int) -> None:
        """
        Set the font size for both the title and the spinbox.

        Parameters
        ----------
        v : int
            font size in points.
        """
        self._label.font().setPointSize(v)
        self._spin.font().setPointSize(v)

    def getFontSize(self) -> int:
        """
        Get the current font size of the widget elements.

        Returns
        -------
        int
            font size in points.
        """
        return self.font().pointSize()

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        super().mousePressEvent(event)


class QDoubleSpinBox2(QDoubleSpinBox):
    """
    QDoubleSpinBox2 class

    Description
    ~~~~~~~~~~~

    The QDoubleSpinBox2 class is a custom widget that extends the QDoubleSpinBox class from PyQt5.
    It provides a spinbox widget with value formatting.

    Inheritance
    ~~~~~~~~~~~

    QDoubleSpinBox -> QDoubleSpinBox2

    Creation: 07/12/2024
    """

    def textFromValue(self, v: float) -> str:
        """
        Convert a floating point value into a string representation with automatic formatting.

        Parameters
        ----------
        v : float
            numeric value to format.

        Returns
        -------
        str
            formatted string representation of the value.
        """
        v2 = abs(v)
        if v.is_integer(): f = '{}'
        else:
            if 0.0 <= v2 < 1.0:
                if v2 >= 10 ** -self.decimals():
                    try:
                        d = int('{:e}'.format(v2).split('-')[1])
                        # noinspection PyUnusedLocal
                        f = '{:.' + str(d) + 'f}'
                    except:
                        f = '{:g}'
                elif v2 < 1e-10: f = '< 1e-10'
                else: f = '{:.1e}'
            else: f = '{:.1f}'
        return f.format(v)


class LabeledDoubleSpinBox(QWidget):
    """
    LabeledDoubleSpinBox class

    Description
    ~~~~~~~~~~~

    The LabeledDoubleSpinBox class is a custom widget that extends the QDoubleSpinBox class from PyQt5. It provides a
    spinbox widget with a label.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> LabeledDoubleSpinBox

    Creation: 13/03/2025
    """

    # Custom Qt signal

    pressed: pyqtSignal = pyqtSignal()
    textChanged: pyqtSignal = pyqtSignal(str)
    valueChanged: pyqtSignal = pyqtSignal(float)

    # Special method

    """
    Private attribute

    _label  QLabel
    _spin   QSpinBox
    """

    def __init__(self,
                 title: str = '',
                 fontsize: int = 12,
                 parent: QWidget | None = None) -> None:
        """
        LabeledDoubleSpinBox instance constructor.

        Parameters
        ----------
        title : str (optional)
            label text to display in front of the double spinbox (default '').
        fontsize : int (optional)
            font size for both the label and the spinbox (default 12).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._label: QLabel = QLabel(parent=self)
        self._label.setText(title)
        self._spin: QDoubleSpinBox2 = QDoubleSpinBox2(parent=self)
        # noinspection PyUnresolvedReferences
        self._spin.textChanged.connect(lambda v: self.textChanged.emit(v))
        # noinspection PyUnresolvedReferences
        self._spin.valueChanged.connect(lambda v: self.valueChanged.emit(v))
        self.setFontSize(fontsize)

        # Init layout

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(5, 5, 5, 5)
        else: lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._label)
        lyout.addWidget(self._spin)
        self.setLayout(lyout)

    def __getattr__(self, attr):
        """
        Allow access to attributes of the internal double spinbox.
        """
        if hasattr(self._spin, attr): return getattr(self._spin, attr)
        else: raise AttributeError(self.__class__.__name__ + ' has no attribute named ' + attr)

    # Public methods

    def getTitle(self) -> str:
        """
        Get the label text of the widget.

        Returns
        -------
        str
            title associated with the spinbox.
        """
        return self._label.text()

    def setTitle(self, title: str) -> None:
        """
        Set the label text of the widget.

        Parameters
        ----------
        title : str
            new text for the title associated with the spinbox.
        """
        self._label.setText(title)

    def setFontSize(self, v: int) -> None:
        """
        Set the font size for both the title and the spinbox.

        Parameters
        ----------
        v : int
            font size in points.
        """
        self._label.font().setPointSize(v)
        self._spin.font().setPointSize(v)

    def getFontSize(self) -> int:
        """
        Get the current font size of the widget elements.

        Returns
        -------
        int
            font size in points.
        """
        return self.font().pointSize()

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        super().mousePressEvent(event)


class LabeledSlider(QWidget):
    """
    LabeledSlider class

    Description
    ~~~~~~~~~~~

    The LabeledSlider class is a custom widget that extends the QSlider class from PyQt5. It combines a QSlider with a
    label and value display. It supports both horizontal and vertical orientations, and can display values as
    percentages or absolute numbers.

    Inheritance
    ~~~~~~~~~~~

    QQWidget -> LabeledSlider

    Last revision: 28/03/2025
    """

    # Custom Qt signals

    valueChanged: pyqtSignal = pyqtSignal(int)
    sliderMoved: pyqtSignal = pyqtSignal(int)
    sliderReleased: pyqtSignal = pyqtSignal()
    sliderPressed: pyqtSignal = pyqtSignal()

    # Special method

    """
    Private attributes

    _title      QLabel
    _legend     QLabel
    _caption    bool, display value ?
    _percent    bool, display percent value
    """

    # noinspection PyUnresolvedReferences
    def __init__(self,
                 orient: Qt.Orientations = Qt.Horizontal,
                 title: str = '',
                 fontsize: int = 12,
                 caption: bool = True,
                 percent: bool = False,
                 parent: QWidget | None = None) -> None:
        """
        LabeledSlider instance constructor.

        Parameters
        ----------
        orient : Qt.Orientations (optional)
            orientation of the slider (Horizontal or Vertical, default Qt.Horizontal).
        title : str (optional)
            title to display above the slider (default '').
        fontsize : int (optional)
            font size for the labels (default 12).
        caption : bool (optional)
            whether to show a numeric label next to the slider (default True).
        percent : bool (optional)
            if True, displays values as percentages (0-100%, default False).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._caption: bool = caption
        self._percent: bool = percent

        self._title = QLabel(self)
        self._title.setText(title)
        self._title.setVisible(title != '')
        self._legend: QLabel = QLabel(self)
        self._legend.setText('0')
        self._legend.setVisible(caption)
        # noinspection PyTypeChecker
        self._legend.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFontSize(fontsize)

        self._slider = QSlider(orientation=orient, parent=self)
        # < Revision 28/03/2025
        self._slider.setStyleSheet('background-color: transparent;')
        # Revision 28/03/2025 >
        self._slider.setMinimumWidth(50)
        self._slider.valueChanged.connect(self._valueChanged)
        self._slider.sliderMoved.connect(self._sliderMoved)
        self._slider.sliderReleased.connect(self._sliderReleased)
        self._slider.sliderPressed.connect(self._sliderPressed)
        self._slider.setMinimum(0)
        self._slider.setMaximum(100)
        self._slider.setValue(0)

        if orient == Qt.Horizontal: lyout = QHBoxLayout()
        else: lyout = QVBoxLayout()
        if platform == 'win32':
            lyout.setContentsMargins(5, 5, 5, 5)
            self._title.setStyleSheet('QLabel { margin: 0px } ')
            self._legend.setStyleSheet('QLabel { margin: 0px } ')
        else: lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)

        lyout.addWidget(self._title)
        lyout.addWidget(self._legend)
        lyout.addWidget(self._slider)

        self.setLayout(lyout)

    def __call__(self, *args, **kwargs) -> QSlider:
        """
        Return the internal QSlider object for direct access.

        Returns
        -------
        QSlider
            internal slider widget.
        """
        return self._slider

    # Private methods

    def _valueChanged(self, v: int) -> None:
        """
        Internal method to update labels and tooltips when the slider value changes.
        """
        # < Revision 28/03/2025
        if self._percent:
            d = self._slider.maximum() - self._slider.minimum()
            if d > 0: v = (v - self._slider.minimum()) / d
            else: v = 0
            # v = '{}%'.format(int(v * 100))
            v2 = '{}%'.format(int(v * 100))
        else:
            # v = str(v)
            v2 = str(v)
        # self._legend.setText(v)
        # self._slider.setToolTip(v)
        self._legend.setText(v2)
        self._slider.setToolTip(v2)
        # Revision 28/03/2025 >
        # noinspection PyUnresolvedReferences
        self.valueChanged.emit(v)

    def _sliderMoved(self, v: int) -> None:
        """
        Internal method triggered when the slider is moved by user interaction.
        """
        # noinspection PyUnresolvedReferences
        self.sliderMoved.emit(v)

    def _sliderPressed(self) -> None:
        """
        Internal method triggered when the slider is pressed by user interaction.
        """
        # noinspection PyUnresolvedReferences
        self.sliderPressed.emit()

    def _sliderReleased(self) -> None:
        """
        Internal method triggered when the slider is released by user interaction.
        """
        # noinspection PyUnresolvedReferences
        self.sliderReleased.emit()

    # Public methods

    def getTitle(self) -> str:
        """
        Get the label text of the widget.

        Returns
        -------
        str
            title associated with the slider.
        """
        return self._title.text()

    def setTitle(self, title: str) -> None:
        """
        Set the label text of the widget.

        Parameters
        ----------
        title : str
            new text for the title associated with the slider.
        """
        if isinstance(title, str):
            self._title.setText(title)
            self._title.setVisible(title != '')
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def setFontSize(self, v: int) -> None:
        """
        Set the font size for all label elements of the slider.

        Parameters
        ----------
        v : int
            font size in points.
        """
        if isinstance(v, int):
            self._title.font().setPointSize(v)
            self._legend.font().setPointSize(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getFontSize(self) -> int:
        """
        Get the current font size of the slider labels.

        Returns
        -------
        int
            font size in points.
        """
        return self._title.font().pointSize()

    def setLegendInPercent(self, v: bool) -> None:
        """
        Toggle whether the legend value is displayed as a percentage.

        Parameters
        ----------
        v : bool
            True to use percentages, False for absolute values.
        """
        if isinstance(v, bool): self._percent = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getLegendInPercent(self) -> bool:
        """
        Get the current mode of the legend display.

        Returns
        -------
        bool
            True if percent mode is active, False otherwise.
        """
        return self._percent

    def setMaximum(self, v: int) -> None:
        """
        Set the maximum value of the slider.

        Parameters
        ----------
        v : int
            maximum value.
        """
        if isinstance(v, int): self._slider.setMaximum(v)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def maximum(self) -> int:
        """
        Get the current maximum value of the slider.

        Returns
        -------
        int
            maximum value.
        """
        return self._slider.maximum()

    def setMinimum(self, v: int) -> None:
        """
        Set the minimum value of the slider.

        Parameters
        ----------
        v : int
            minimum value.
        """
        if isinstance(v, int): self._slider.setMinimum(v)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def minimum(self) -> int:
        """
        Get the current minimum value of the slider.

        Returns
        -------
        int
            minimum value.
        """
        return self._slider.minimum()

    def setRange(self, vmin: int, vmax: int) -> None:
        """
        Set the range of values for the slider.

        Parameters
        ----------
        vmin : int
            minimum value.
        vmax : int
            maximum value.
        """
        self._slider.setRange(vmin, vmax)

    def setValue(self, v: int) -> None:
        """
        Set the current value of the slider.

        Parameters
        ----------
        v : int
            current value of the slider.
        """
        if isinstance(v, int): self._slider.setValue(v)
        else: raise TypeError('parameter type {} is not int.'.format(v))

    def value(self) -> int:
        """
        Get the current value of the slider.

        Returns
        -------
        int
            current value of the slider.
        """
        return self._slider.value()

    # Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and trigger a slider SliderSingleStep action.
        """
        self._slider.triggerAction(QSlider.SliderAction.SliderSingleStepAdd)


class LabeledComboBox(QWidget):
    """
    LabeledComboBox class

    Description
    ~~~~~~~~~~~

    The LabeledComboBox class is a custom widget that extends the QComboBox class from PyQt5. It provides a
    combobox widget with a label.

    Inheritance
    ~~~~~~~~~~~

    QWidget ->  LabeledComboBox

    Creation: 13/03/2025
    """

    # Custom Qt signal

    pressed: pyqtSignal = pyqtSignal()
    activated: pyqtSignal = pyqtSignal(int)
    currentIndexChanged: pyqtSignal = pyqtSignal(int)
    currentTextChanged: pyqtSignal = pyqtSignal(str)
    editTextChanged: pyqtSignal = pyqtSignal(str)
    highlighted: pyqtSignal = pyqtSignal(int)
    textActivated: pyqtSignal = pyqtSignal(str)
    textHighlighted: pyqtSignal = pyqtSignal(str)

    # Special method

    """
    Private attributes

    _label  QLabel
    _spin   QSpinBox
    """

    def __init__(self,
                 title: str = '',
                 fontsize: int = 12,
                 parent: QWidget | None = None) -> None:
        """
        LabeledComboBox instance constructor.

        Parameters
        ----------
        title : str (optional)
            label text to display in front of the combobox (default '').
        fontsize : int (optional)
            font size for both the label and the combobox (default 12).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._label: QLabel = QLabel(parent=self)
        self._label.setText(title)
        self._combo: QComboBox = QComboBox(parent=self)
        # noinspection PyUnresolvedReferences
        self._combo.activated.connect(lambda v: self.activated.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.currentIndexChanged.connect(lambda v: self.currentIndexChanged.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.currentTextChanged.connect(lambda v: self.currentTextChanged.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.editTextChanged.connect(lambda v: self.editTextChanged.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.highlighted.connect(lambda v: self.highlighted.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.textActivated.connect(lambda v: self.textActivated.emit(v))
        # noinspection PyUnresolvedReferences
        self._combo.textHighlighted.connect(lambda v: self.textHighlighted.emit(v))
        self.setFontSize(fontsize)

        # Init layout

        lyout = QHBoxLayout()
        if platform == 'win32':  lyout.setContentsMargins(5, 5, 5, 5)
        else: lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._label)
        lyout.addWidget(self._combo)
        self.setLayout(lyout)

    def __getattr__(self, attr):
        """
        Allow access to attributes of the internal combobox.
        """
        if hasattr(self._combo, attr): return getattr(self._combo, attr)
        else: raise AttributeError(self.__class__.__name__ + ' has no attribute named ' + attr)

    # Public methods

    def getTitle(self) -> str:
        """
        Get the label text of the widget.

        Returns
        -------
        str
            title associated with the combobox.
        """
        return self._label.text()

    def setTitle(self, title: str) -> None:
        """
        Set the label text of the widget.

        Parameters
        ----------
        title : str
            new text for the title associated with the combobox.
        """
        self._label.setText(title)

    def setFontSize(self, v: int) -> None:
        """
        Set the font size for all label elements of the widget.

        Parameters
        ----------
        v : int
            font size in points.
        """
        self._label.font().setPointSize(v)
        self._combo.font().setPointSize(v)

    def getFontSize(self) -> int:
        """
        Get the current font size of the widget.

        Returns
        -------
        int
            font size in points.
        """
        return self.font().pointSize()

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        super().mousePressEvent(event)


class IconLabel(QLabel):
    """
    IconLabel class

    Description
    ~~~~~~~~~~~

    A custom flat button widget that displays an icon and emits a clicked signal.
    It allows to customize the appearance of the icons according to light or dark mode.

    Inheritance
    ~~~~~~~~~~~

    QLabel -> IconLabel

    Last revision 18/03/2025
    """

    # Custom Qt signal

    clicked: pyqtSignal = pyqtSignal(QWidget)

    # Private class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, icon: str | None = None, parent: QWidget | None = None) -> None:
        """
        IconLabel instance constructor.

        Parameters
        ----------
        icon : str | None (optional)
            icon filename in the PySisyphe icon folder (./Sisyphe/gui/darkroi or ./Sisyphe/gui/lightroi).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        # noinspection PyUnresolvedReferences
        self.clicked.emit(self)
        super().mousePressEvent(event)


class IconPushButton(QPushButton):
    """
    IconPushButton class

    Description
    ~~~~~~~~~~~

    The IconPushButton class is a custom widget that extends the QPushButton class from PyQt5.
    It allows to customize the appearance of the icons according to light or dark mode.

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> IconPushButton

    Last revision: 18/03/2025
    """

    # Private class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    def __init__(self, icon: str | None = None, size: int = 32, parent: QWidget | None = None) -> None:
        """
        IconPushButton instance constructor.

        Parameters
        ----------
        icon : str | None (optional)
            icon filename in the PySisyphe icon folder (./Sisyphe/gui/darkroi or ./Sisyphe/gui/lightroi).
        size : int (optional)
            button size in pixels (default 32).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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
    VisibilityLabel class

    Description
    ~~~~~~~~~~~

    The VisibilityLabel class is a custom widget that extends the QLabel class from PyQt5.
    It acts as a flat button displaying an eye icon that toggles between "view" and "hide"
    states, allowing users to control the visibility of associated elements.

    Inheritance
    ~~~~~~~~~~~

    QLabel -> VisibilityLabel

    Last revision: 10/06/2026
    """

    # Custom Qt signal

    visibilityChanged: pyqtSignal = pyqtSignal(QWidget)
    pressed: pyqtSignal = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    """
    Private attributes

    _visible    bool, current visibility state
    _iconon     QPixmap, icon representing the visible state
    _iconoff    QPixmap, icon representing the hidden state
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        VisibilityLabel instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._iconon: QPixmap = QPixmap(join(self._getDefaultIconDirectory(), 'view.png'))
        self._iconoff: QPixmap = QPixmap(join(self._getDefaultIconDirectory(), 'hide.png'))
        self._visible: bool = True
        self.setToolTip('Click to hide.')
        self.setPixmap(self._iconon)
        self.setScaledContents(True)

        self.setObjectName('visibilityButton')
        self.setStyleSheet("QLabel#visibilityButton {border-color: rgb(176, 176, 176); border-style: solid;"
                           " border-width: 0.5px; border-radius: 5px;}")

    # Public methods

    def setVisibilitySateIcon(self, v: bool) -> None:
        """
        Set the visibility state and update the displayed icon.

        Parameters
        ----------
        v : bool
            True to set the icon to the "view" state, False for the "hide" state.
        """
        if isinstance(v, bool):
            self._visible = v
            if v:
                self.setPixmap(self._iconon)
                self.setToolTip('Click to hide.')
            else:
                self.setPixmap(self._iconoff)
                self.setToolTip('Click to show.')
            # noinspection PyUnresolvedReferences
            self.visibilityChanged.emit(self)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVisibilityStateIconToView(self) -> None:
        """
        Set the visibility state icon to "view" (visible).
        """
        self.setVisibilitySateIcon(True)

    def setVisibilityStateIconToHide(self) -> None:
        """
        Set the visibility state icon to "hide" (hidden).
        """
        self.setVisibilitySateIcon(False)

    def getVisibilityStateIcon(self) -> bool:
        """
        Get the current visibility state.

        Returns
        -------
        bool
            True if the state is visible, False if hidden.
        """
        return self._visible

    # Overridden Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Toggles the internal visibility state and updates the icon.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        self._visible = not self._visible
        if self._visible:
            self.setPixmap(self._iconon)
            self.setToolTip('Click to hide.')
        else:
            self.setPixmap(self._iconoff)
            self.setToolTip('Click to show.')
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        # noinspection PyUnresolvedReferences
        self.visibilityChanged.emit(self)
        super().mousePressEvent(event)


class LockLabel(QLabel):
    """
    LockLabel

    Description
    ~~~~~~~~~~~
    The LockLabel class is a custom widget that extends the QLabel class from PyQt5.
    It functions as a flat button displaying a lock icon that toggles between "locked" and "unlocked"
    states, allowing users to control the lock status of associated elements.
    
    Inheritance
    ~~~~~~~~~~~
    QLabel -> LockLabel
    
    Last revision: 10/06/2026
    """

    # Custom Qt signal

    lockChanged: pyqtSignal = pyqtSignal(QWidget)
    pressed: pyqtSignal = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    """
    Private attributes

    _locked     bool, current lock state
    _lock       QPixmap, icon representing the locked state
    _unlock     QPixmap, icon representing the unlocked state
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        LockLabel instance constructor.
        
        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._lock: QPixmap = QPixmap(join(self._getDefaultIconDirectory(), 'lock.png'))
        self._unlock: QPixmap = QPixmap(join(self._getDefaultIconDirectory(), 'unlock.png'))
        self._locked: bool = False
        self.setToolTip('Click to lock.')
        self.setPixmap(self._unlock)
        self.setScaledContents(True)

        self.setObjectName('lockButton')
        self.setStyleSheet("QLabel#lockButton {border-color: rgb(176, 176, 176); border-style: solid"
                           "; border-width: 0.5px; border-radius: 5px;}")

    # Public methods

    def setLockStateIcon(self, v: bool) -> None:
        """
        Set the lock state and update the displayed icon.
        
        Parameters
        ----------
        v : bool
            True to set the icon to the "locked" state, False for the "unlocked" state.
        """
        if isinstance(v, bool):
            self._locked = v
            if v:
                self.setPixmap(self._lock)
                self.setToolTip('Click to unlock.')
            else:
                self.setPixmap(self._unlock)
                self.setToolTip('Click to lock.')
            # noinspection PyUnresolvedReferences
            self.lockChanged.emit(self)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setStateIconToLocked(self) -> None:
        """
        Set the lock state icon to "locked".
        """
        self.setLockStateIcon(True)

    def setStateIconToUnlocked(self) -> None:
        """
        Set the lock state icon to "unlocked".
        """
        self.setLockStateIcon(False)

    def getLockStateIcon(self) -> bool:
        """
        Get the current lock state.
        
        Returns
        -------
        bool
            True if the state is locked, False if unlocked.
        """
        return self._locked

    # Override Qt event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Toggles the lock state and update the displayed icon.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        self._locked = not self._locked
        if self._locked:
            self.setPixmap(self._lock)
            self.setToolTip('Click to unlock.')
        else:
            self.setPixmap(self._unlock)
            self.setToolTip('Click to lock.')
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        # noinspection PyUnresolvedReferences
        self.lockChanged.emit(self)
        super().mousePressEvent(event)


class OpacityPushButton(QLabel):
    """
    OpacityPushButton class

    Description
    ~~~~~~~~~~~

    Opacity management button. The opacity is adjusted using a slider displayed in a popup menu.

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> OpacityPushButton

    Last revision: 11/06/2026
    """

    # Custom Qt signal

    opacityChanged: pyqtSignal = pyqtSignal(QWidget)
    popupShow: pyqtSignal = pyqtSignal()
    popupHide: pyqtSignal = pyqtSignal()
    pressed: pyqtSignal = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    """
    Private attribute

    _label      QLabel
    _slider     QSlider
    _popup      QMenu
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OpacityPushButton instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._popup: QMenu = QMenu(self)
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)

        self._label: QLabel = QLabel(self._popup)
        font = QFont('Arial', 8)
        self._label.setFont(font)
        # < Revision 20/03/2025
        self._label.setFixedWidth(60)
        # Revision 20/03/2025 >
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # noinspection PyUnresolvedReferences
        self._slider: QSlider = QSlider(Qt.Vertical, parent=self._popup)
        self._slider.setFixedHeight(80)
        # noinspection PyTypeChecker
        self._slider.setTickPosition(QSlider.NoTicks)
        self._slider.setMaximum(100)
        self._slider.setMinimum(0)
        self._slider.setValue(100)
        self._slider.setInvertedAppearance(True)
        self._slider.setToolTip('Opacity {} %'.format(self._slider.value()))
        # < Revision 23/03/2025
        self._slider.setStyleSheet('background-color: transparent;')
        # Revision 23/03/2025 >
        self._label.setText('{} %'.format(self._slider.value()))
        # noinspection PyUnresolvedReferences
        self._slider.valueChanged.connect(self._opacityChanged)

        a = QWidgetAction(self._popup)
        a.setDefaultWidget(self._label)
        self._popup.addAction(a)
        a = QWidgetAction(self._popup)
        a.setDefaultWidget(self._slider)
        self._popup.addAction(a)
        # noinspection PyUnresolvedReferences
        self._popup.aboutToShow.connect(lambda: self.popupShow.emit())
        # < Revision 11/06/2026
        # move keyboard focus to slider
        self._popup.aboutToShow.connect(lambda: self._slider.setFocus())
        # Revision 11/06/2026 >
        # noinspection PyUnresolvedReferences
        self._popup.aboutToHide.connect(lambda: self.popupHide.emit())

        self.setPixmap(QPixmap(join(self._getDefaultIconDirectory(), 'opacity.png')))
        self.setScaledContents(True)

        self.setObjectName('opacityButton')
        self.setStyleSheet("QLabel#opacityButton {border-color: rgb(176, 176, 176); border-style: solid; "
                           "border-width: 0.5px; border-radius: 5px;}")

        self.setToolTip('Opacity: {} %\nClick to set opacity.'.format(self._slider.value()))

    # Private method

    # noinspection PyUnusedLocal
    def _opacityChanged(self, value: int) -> None:
        """
        Internal method to update opacity and tooltips when the slider value changes.
        """
        # < Revision 11/06/2026
        tip = '{} %'.format(self._slider.value())
        self._label.setText(tip)
        self._slider.setToolTip('Opacity ' + tip)
        self.setToolTip('Opacity ' + tip + '\nClick to set opacity.')
        # Revision 11/06/2026 >
        # noinspection PyUnresolvedReferences
        self.opacityChanged.emit(self)

    # Public method

    def setOpacity(self, v: float, signal: bool = True) -> None:
        """
        Set the opacity value.

        Parameters
        ----------
        v : float
            opacity value.
        signal : bool (optional)
            emit valueChanged signal if True (default True).
        """
        v = int(v * 100)
        if signal: self._slider.setValue(v)
        else:
            self._slider.blockSignals(True)
            self._slider.setValue(v)
            self._slider.blockSignals(False)
            self._label.setText('{} %'.format(v))
            self._slider.setToolTip('Opacity {} %'.format(v))
            self.setToolTip('Opacity: {} %\nClick to set opacity.'.format(v))

    def getOpacity(self) -> float:
        """
        Get the opacity value.

        Returns
        -------
        float
            opacity value.
        """
        return self._slider.value() / 100

    # Qt Event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        super().mousePressEvent(event)
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        # noinspection PyUnresolvedReferences
        if event.button() == Qt.LeftButton:
            # < Revision 27/10/2024
            # use popup instead of exec
            # self._popup.exec(event.globalPos())
            self._popup.popup(event.globalPos())
            # < Revision 09/06/2026
            self._slider.setFocus()
            # Revision 09/06/2026 >
            # Revision 27/10/2024 >


class WidthPushButton(QLabel):
    """
    WidthPushButton class

    Description
    ~~~~~~~~~~~

    Width management button. The width is adjusted using a slider displayed in a popup menu.

    Inheritance
    ~~~~~~~~~~~

    QPushButton -> WidthPushButton

    Last revision: 11/06/2026
    """

    # Custom Qt signal

    widthChanged: pyqtSignal = pyqtSignal(QWidget)
    popupShow: pyqtSignal = pyqtSignal()
    popupHide: pyqtSignal = pyqtSignal()
    pressed: pyqtSignal = pyqtSignal()

    # Class method

    @classmethod
    def isDarkMode(cls) -> bool:
        """
        Check if the current OS is in dark mode.

        Returns
        -------
        bool
            True if dark mode is detected, False otherwise.
        """
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        """
        Check if the current OS is in light mode.

        Returns
        -------
        bool
            True if light mode is detected, False otherwise.
        """
        return darkdetect.isLight()

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the path to the default icon directory based on system theme.

        Returns
        -------
        str
            path to the 'darkroi' or 'lightroi' folder.
        """
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkroi')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lightroi')

    # Special method

    """
    Private attributes

    _vmin       float
    _vmax       float
    _step       float
    _prefix     str
    _label      QLabel
    _slider     QSlider
    _popup      QMenu
    """

    def __init__(self,
                 vmin: float = 1.0,
                 vmax: float = 10.0,
                 step: float = 1.0,
                 prefix: str = '',
                 parent: QWidget | None = None) -> None:
        """
        WidthPushButton instance constructor.

        Parameters
        ----------
        vmin : float (optional)
            minimum width (default 1.0).
        vmax : float (optional)
            maximum width (default 10.0).
        step : float (optional)
            slider step (default 1.0).
        prefix : str (optional)
            text displayed in the tooltip before the width value (default '').
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        if prefix == '': self._prefix = 'Width'
        else: self._prefix: str = prefix
        self._prefix = prefix
        self._vmin: float = vmin
        self._step: float = step
        n = int((vmax - vmin) // step)
        self._vmax: float = vmin + (step * n)

        self._popup: QMenu = QMenu(self)
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)

        self._label: QLabel = QLabel(self._popup)
        font = QFont('Arial', 8)
        self._label.setFont(font)
        # < Revision 20/03/2025
        self._label.setFixedWidth(60)
        # Revision 20/03/2025 >
        # noinspection PyUnresolvedReferences
        self._label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # noinspection PyUnresolvedReferences
        self._slider: QSlider = QSlider(Qt.Vertical, parent=self._popup)
        self._slider.setFixedHeight(80)
        # noinspection PyTypeChecker
        self._slider.setTickPosition(QSlider.NoTicks)
        self._slider.setMinimum(0)
        self._slider.setMaximum(n)
        self._slider.setValue(0)
        self._slider.setInvertedAppearance(True)
        # < Revision 23/03/2025
        self._slider.setStyleSheet('background-color: transparent;')
        # Revision 23/03/2025 >
        self._slider.setToolTip('{} {:.1f} mm'.format(self._prefix, vmin))
        v = self._vmin + self._slider.value() * self._step
        self._label.setText('{:.1f} mm'.format(v))
        # noinspection PyUnresolvedReferences
        self._slider.valueChanged.connect(self._widthChanged)

        a = QWidgetAction(self._popup)
        a.setDefaultWidget(self._label)
        self._popup.addAction(a)
        a = QWidgetAction(self._popup)
        a.setDefaultWidget(self._slider)
        self._popup.addAction(a)
        # noinspection PyUnresolvedReferences
        self._popup.aboutToShow.connect(lambda: self.popupShow.emit())
        # < Revision 11/06/2026
        # move keyboard focus to slider
        self._popup.aboutToShow.connect(lambda: self._slider.setFocus())
        # Revision 11/06/2026 >
        # noinspection PyUnresolvedReferences
        self._popup.aboutToHide.connect(lambda: self.popupHide.emit())

        self.setPixmap(QPixmap(join(self._getDefaultIconDirectory(), 'width.png')))
        self.setScaledContents(True)

        self.setObjectName('widthButton')
        self.setStyleSheet("QLabel#widthButton {border-color: rgb(176, 176, 176); border-style: solid; "
                           "border-width: 0.5px; border-radius: 5px;}")

        self.setToolTip('{0}: {1:.1f} mm\nClick to set {0}.'.format(self._prefix, vmin))

    # Private method

    # noinspection PyUnusedLocal
    def _widthChanged(self, value: int) -> None:
        """
        Internal method to update width and tooltips when the slider value changes.
        """
        v = self._vmin + self._slider.value() * self._step
        # < Revision 11/06/2026
        tip = '{:.1f} mm'.format(v)
        self._label.setText(tip)
        self._slider.setToolTip('{} '.format(self._prefix) + tip)
        self.setToolTip('{} '.format(self._prefix) + tip +'\nClick to set {}.'.format(self._prefix.lower()))
        QToolTip.showText(self._slider.mapToGlobal(QPoint(self._slider.width(), self._slider.height() // 2)), tip)
        # Revision 11/06/2026 >
        # noinspection PyUnresolvedReferences
        self.widthChanged.emit(self)

    # Public method

    def setRange(self,
                 vmin: float = 1.0,
                 vmax: float = 10.0,
                 step: float = 1.0) -> None:
        """
        Set the width value range.

        Parameters
        ----------
        vmin : float (optional)
            minimum width value (default 1.0).
        vmax : float (optional)
            maximum width value (default 10.0).
        step : float (optional)
            slider step (default 1.0).
        """
        self._vmin = vmin
        self._step = step
        n = int((vmax - vmin) // step)
        self._vmax = vmin + (step * n)
        self._slider.setMinimum(0)
        self._slider.setMaximum(n)
        self._slider.setValue(0)

    def setWidth(self, v: float, signal: bool = True) -> None:
        """
        Set the width value.

        Parameters
        ----------
        v : float
            width value.
        signal : bool (optional)
            emit valueChanged signal if True (default True).
        """
        if v < self._vmin: v = self._vmin
        elif v > self._vmax: v = self._vmax
        v2 = int((v - self._vmin) // self._step)
        if signal: self._slider.setValue(v2)
        else:
            self._slider.blockSignals(True)
            self._slider.setValue(v2)
            self._slider.blockSignals(False)
            v = self._vmin + (v2 * self._step)
            self._label.setText('{:.1f} mm'.format(v))
            self._slider.setToolTip('{} {:.1f} mm'.format(self._prefix, v))
            self.setToolTip('{0}: {1:.1f} mm\nClick to set {0}.'.format(self._prefix, v))

    def getWidth(self) -> float:
        """
        Get the width value.

        Returns
        -------
        float
            width value.
        """
        return self._vmin + (self._slider.value() * self._step)

    # < Revision 20/02/2025
    # add setPrefix method
    def setPrefix(self, prefix: str = '') -> None:
        """
        Set the text displayed in the tooltip before the width value.

        Parameters
        ----------
        prefix : str (optional)
            text displayed in the tooltip before the width value (default '').
        """
        if prefix == '': self._prefix = 'Width'
        else: self._prefix = prefix
        v = self.getWidth()
        # < Revision 11/06/2026
        tip = '{:.1f} mm'.format(v)
        self._label.setText(tip)
        self._slider.setToolTip('{} '.format(self._prefix) + tip)
        self.setToolTip('{} '.format(self._prefix) + tip +'\nClick to set {}.'.format(self._prefix.lower()))
        # Revision 11/06/2026 >
    # Revision 20/02/2025 >

    # < Revision 20/02/2025
    # add getPrefix method
    def getPrefix(self) -> str:
        """
        Get the text displayed in the tooltip before the width value.

        Returns
        -------
        str
            text displayed in the tooltip before the width value.
        """
        return self._prefix
    # Revision 20/02/2025 >

    # Qt Event

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle the mouse press event and emit the pressed signal.
        Intercept mouse press event from child widgets to handle them at the parent level.
        """
        super().mousePressEvent(event)
        # noinspection PyUnresolvedReferences
        self.pressed.emit()
        # noinspection PyUnresolvedReferences
        if event.button() == Qt.LeftButton:
            # < Revision 27/10/2024
            # use popup instead of exec
            # self._popup.exec(event.globalPos())
            self._popup.popup(event.globalPos())
            # < Revision 09/06/2026
            self._slider.setFocus()
            # Revision 09/06/2026 >
            # Revision 27/10/2024 >
