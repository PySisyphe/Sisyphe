"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from sys import platform

from vtk import vtkTextProperty

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QGraphicsView

from Sisyphe.widgets.basicWidgets import colorDialog

__all__ = ['DialogFontProperties']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogFontProperties
"""


class DialogFontProperties(QDialog):
    """
    DialogFontProperties class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> QDialog -> DialogFontProperties

    Last revision: 18/03/2025
    """

    # Special method

    """
    Private attributes

    _properties             vtkTextProperty, properties to edit
    _previousproperties     vtkTextProperty, copy of properties before edition
    """

    def __init__(self, parent=None, properties=None):
        super().__init__(parent)

        self.setWindowTitle('Font properties')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Text color and opacity

        self._tcolor = QPushButton(self)
        self._tcolor.setFixedWidth(self._tcolor.height())
        self._tcolor.setAutoFillBackground(True)
        self._tcolor.setStyleSheet('background-color: rgb(255, 0, 0)')
        # noinspection PyUnresolvedReferences
        self._tcolor.clicked.connect(self._changeColor)

        self._topacity = QDoubleSpinBox(self)
        self._topacity.setMinimum(0.0)
        self._topacity.setMaximum(1.0)
        self._topacity.setValue(1.0)
        self._topacity.setDecimals(2)
        self._topacity.setSingleStep(0.1)
        self._topacity.adjustSize()
        # self._topacity.setFixedWidth(50)
        self._topacity.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._topacity.valueChanged.connect(self._propertyChange)

        # Background color and opacity

        self._bcolor = QPushButton(self)
        self._bcolor.setFixedWidth(self._bcolor.height())
        self._bcolor.setAutoFillBackground(True)
        self._bcolor.setStyleSheet('background-color: rgb(255, 0, 0)')
        # noinspection PyUnresolvedReferences
        self._bcolor.clicked.connect(self._changeBackgroundColor)

        self._bopacity = QDoubleSpinBox(self)
        self._bopacity.setMinimum(0.0)
        self._bopacity.setMaximum(1.0)
        self._bopacity.setValue(1.0)
        self._bopacity.setDecimals(2)
        self._bopacity.setSingleStep(0.01)
        self._bopacity.adjustSize()
        # self._bopacity.setFixedWidth(50)
        self._bopacity.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._bopacity.valueChanged.connect(self._propertyChange)

        # Frame color

        self._frame = QCheckBox('Frame')
        # noinspection PyUnresolvedReferences
        self._frame.stateChanged.connect(self._propertyChange)

        self._fcolor = QPushButton(self)
        self._fcolor.setFixedWidth(self._fcolor.height())
        self._fcolor.setAutoFillBackground(True)
        self._fcolor.setStyleSheet('background-color: rgb(255, 0, 0)')
        # noinspection PyUnresolvedReferences
        self._fcolor.clicked.connect(self._changeFrameColor)

        # Font family, size, bold, italic

        self._fontname = QComboBox(self)
        self._fontname.setEditable(False)
        # self._fontname.setFixedWidth(80)
        self._fontname.addItem('Arial')
        self._fontname.addItem('Courier')
        self._fontname.addItem('Times')
        self._fontname.adjustSize()
        # noinspection PyUnresolvedReferences
        self._fontname.currentIndexChanged.connect(self._propertyChange)

        self._fontsize = QSpinBox(self)
        self._fontsize.setMinimum(8)
        self._fontsize.setMaximum(80)
        self._fontsize.setValue(12)
        self._fontsize.adjustSize()
        # self._fontsize.setFixedWidth(50)
        # noinspection PyUnresolvedReferences
        self._fontsize.valueChanged.connect(self._propertyChange)

        self._bold = QCheckBox('Bold')
        # noinspection PyUnresolvedReferences
        self._bold.stateChanged.connect(self._propertyChange)

        self._italic = QCheckBox('Italic')
        # noinspection PyUnresolvedReferences
        self._italic.stateChanged.connect(self._propertyChange)

        # Horizontal and vertical justification

        self._hjustfy = QComboBox(self)
        self._hjustfy.setEditable(False)
        # self._hjustfy.setFixedWidth(80)
        self._hjustfy.addItem('Left')
        self._hjustfy.addItem('Center')
        self._hjustfy.addItem('Right')
        self._hjustfy.adjustSize()

        self._vjustfy = QComboBox(self)
        self._vjustfy.setEditable(False)
        # self._vjustfy.setFixedWidth(80)
        self._vjustfy.addItem('Top')
        self._vjustfy.addItem('Center')
        self._vjustfy.addItem('Bottom')
        self._vjustfy.adjustSize()

        # Demonstration scene

        if properties: self.setProperties(properties)
        else: self._properties = properties

        scene = QGraphicsScene()
        self._demo = QGraphicsView(scene)
        scene.setBackgroundBrush(QColor(0, 0, 0))
        self._font = QFont()
        self._font.setBold(self.getBold())
        self._font.setItalic(self.getItalic())
        self._font.setFamily(self._fontname.currentText())
        self._font.setPointSize(self.getFontSize())
        self._text = scene.addSimpleText('Example', font=self._font)
        self._rect = scene.addRect(self._text.boundingRect())
        self._text.setZValue(1.0)
        self._rect.setZValue(0.0)
        self._pos = self._text.pos()
        self._propertyChange()

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init widgets position

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(QLabel('Font'), alignment=Qt.AlignRight)
        layout.addWidget(self._fontname)
        layout.addWidget(QLabel('Size'), alignment=Qt.AlignRight)
        layout.addWidget(self._fontsize)
        layout.addStretch()
        self._layout.addLayout(layout)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        layout.addStretch()
        layout.addWidget(QLabel('Text'), alignment=Qt.AlignRight)
        layout.addWidget(self._tcolor)
        layout.addWidget(QLabel('Frame'), alignment=Qt.AlignRight)
        layout.addWidget(self._fcolor)
        layout.addWidget(QLabel('Back'), alignment=Qt.AlignRight)
        layout.addWidget(self._bcolor)
        layout.addStretch()
        self._layout.addLayout(layout)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        layout.addWidget(QLabel('Text opacity'), alignment=Qt.AlignRight)
        layout.addWidget(self._topacity)
        layout.addWidget(QLabel('Back opacity'), alignment=Qt.AlignRight)
        layout.addWidget(self._bopacity)
        self._layout.addLayout(layout)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        layout.addWidget(QLabel('Horizontal'), alignment=Qt.AlignRight)
        layout.addWidget(self._hjustfy)
        layout.addWidget(QLabel('Vertical'), alignment=Qt.AlignRight)
        layout.addWidget(self._vjustfy)
        self._layout.addLayout(layout)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        layout.addWidget(self._frame, alignment=Qt.AlignCenter)
        layout.addWidget(self._bold, alignment=Qt.AlignCenter)
        layout.addWidget(self._italic, alignment=Qt.AlignCenter)
        self._layout.addLayout(layout)
        self._layout.addWidget(self._demo)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        else: layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        reset = QPushButton('Reset')
        reset.setFixedWidth(100)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.addWidget(reset)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self._accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        reset.clicked.connect(self._reset)

        self.adjustSize()
        self.setFixedSize(self.size())

    # Private methods

    def _changeColor(self):
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Mesh color', options=QColorDialog.DontUseNativeDialog)
        c = self.getColor()
        c = [int(i * 255) for i in c]
        c = colorDialog(title='Mesh color', color=QColor(c[0], c[1], c[2]))
        if c is not None:
            if c.isValid():
                buff = 'background-color: rgb({}, {}, {})'.format(c.red(), c.green(), c.blue())
                self._tcolor.setStyleSheet(buff)
                self._propertyChange()
        # Revision 18/03/2025 >

    def _changeBackgroundColor(self):
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Vertex color', options=QColorDialog.DontUseNativeDialog)
        c = self.getBackgroundColor()
        c = [int(i * 255) for i in c]
        c = colorDialog(title='Vertex color', color=QColor(c[0], c[1], c[2]))
        if c is not None:
            if c.isValid():
                buff = 'background-color: rgb({}, {}, {})'.format(c.red(), c.green(), c.blue())
                self._bcolor.setStyleSheet(buff)
                self._propertyChange()
        # Revision 18/03/2025 >

    def _changeFrameColor(self):
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Edge color', options=QColorDialog.DontUseNativeDialog)
        c = self.getFrameColor()
        c = [int(i * 255) for i in c]
        c = colorDialog(title='Edge color', color=QColor(c[0], c[1], c[2]))
        if c is not None:
            if c.isValid():
                buff = 'background-color: rgb({}, {}, {})'.format(c.red(), c.green(), c.blue())
                self._fcolor.setStyleSheet(buff)
                self._propertyChange()

    def _propertyChange(self):
        self._font.setBold(self.getBold())
        self._font.setItalic(self.getItalic())
        self._font.setFamily(self._fontname.currentText())
        self._font.setPointSize(self.getFontSize())

        r, g, b = self.getColor()
        self._text.setBrush(QColor(int(r * 255), int(g * 255), int(b * 255)))
        self._text.setFont(self._font)
        self._text.setOpacity(self.getOpacity())

        r1, g1, b1 = self.getFrameColor()
        r2, g2, b2 = self.getBackgroundColor()
        self._rect.setPen(QColor(int(r1 * 255), int(g1 * 255), int(b1 * 255)))
        self._rect.setBrush(QColor(int(r2 * 255), int(g2 * 255), int(b2 * 255)))
        self._rect.setRect(self._text.boundingRect())
        self._rect.setVisible(self.getFrame())

        self._demo.centerOn(self._text)

    def _accept(self):
        c = self.getColor()
        self._properties.SetColor(c[0], c[1], c[2])
        self._properties.SetOpacity(self.getOpacity())
        c = self.getBackgroundColor()
        self._properties.SetBackgroundColor(c[0], c[1], c[2])
        self._properties.SetBackgroundOpacity(self.getBackgroundOpacity())
        self._properties.SetFrame(self.getFrame())
        c = self.getFrameColor()
        self._properties.SetFrameColor(c[0], c[1], c[2])
        self._properties.SetFontFamily(self.getFontFamily())
        self._properties.SetFontSize(self.getFontSize())
        self._properties.SetBold(self.getBold())
        self._properties.SetItalic(self.getItalic())
        self._properties.SetJustification(self.getJustification())
        self._properties.SetVerticalJustification(self.getVerticalJustification())
        self.accept()

    def _reset(self):
        self.setProperties(self._properties)

    # Public methods

    def setProperties(self, p):
        if isinstance(p, vtkTextProperty):
            self._properties = p
            c = p.GetColor()
            self.setColor(c[0], c[1], c[2])
            self.setOpacity(p.GetOpacity())
            c = p.GetBackgroundColor()
            self.setBackgroundColor(c[0], c[1], c[2])
            self.setBackgroundOpacity(p.GetBackgroundOpacity())
            self.setFrame(p.GetFrame() == 1)
            c = p.GetFrameColor()
            self.setFrameColor(c[0], c[1], c[2])
            self.setFontFamily(p.GetFontFamily())
            self.setFontSize(p.GetFontSize())
            self.setBold(p.GetBold() == 1)
            self.setItalic(p.GetItalic() == 1)
            self.setJustification(p.GetJustification())
            self.setVerticalJustification(p.GetVerticalJustification())
            self._propertyChange()
        else:
            raise TypeError('parameter type {} is not vtkTextProperty.'.format(type(p)))

    def getProperties(self):
        return self._properties

    def setColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._tcolor.setStyleSheet(buff)

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._topacity.setValue(v)
            else:
                raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else:
            raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setBackgroundColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._bcolor.setStyleSheet(buff)

    def setBackgroundOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._bopacity.setValue(v)
            else:
                raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else:
            raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setFrame(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._frame.setCheckState(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setFrameColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._fcolor.setStyleSheet(buff)

    def setFontFamily(self, v):
        if isinstance(v, int):
            if 0 <= v < 3:
                self._fontname.setCurrentIndex(v)
            else:
                raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setFontSize(self, v):
        if isinstance(v, int):
            if 7 < v <= 80:
                self._fontsize.setValue(v)
            else:
                raise ValueError('parameter value {} is not between 8 and 80.'.format(v))
        else:
            raise TypeError('parameter type {} is not int'.format(type(v)))

    def setBold(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._bold.setCheckState(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setItalic(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._italic.setCheckState(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setJustification(self, v):
        if isinstance(v, int):
            if 0 <= v < 2:
                self._hjustfy.setCurrentIndex(v)
            else:
                raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setVerticalJustification(self, v):
        if isinstance(v, int):
            if 0 <= v < 2:
                self._vjustfy.setCurrentIndex(v)
            else:
                raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getColor(self):
        c = self._tcolor.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def getOpacity(self):
        return self._topacity.value()

    def getBackgroundColor(self):
        c = self._bcolor.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def getBackgroundOpacity(self):
        return self._bopacity.value()

    def getFrame(self):
        return self._frame.checkState() == 2

    def getFrameColor(self):
        c = self._fcolor.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def getFontFamily(self):
        return self._fontname.currentIndex()

    def getFontSize(self):
        return self._fontsize.value()

    def getBold(self):
        return self._bold.checkState() == 2

    def getItalic(self):
        return self._italic.checkState() == 2

    def getJustification(self):
        return self._hjustfy.currentIndex()

    def getVerticalJustification(self):
        return self._vjustfy.currentIndex()
