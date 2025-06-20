"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from sys import platform

from vtk import vtkProperty

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QPushButton

from Sisyphe.widgets.basicWidgets import colorDialog

__all__ = ['DialogMeshProperties']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QDialog -> DialogMeshProperties
"""


class DialogMeshProperties(QDialog):
    """
    DialogMeshProperties class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> QDialog -> DialogMeshProperties

    Last revision: 18/03/2025
    """

    # Custom Qt Signal

    UpdateRender = pyqtSignal()

    # Special method

    """
    Private attributes

    _properties             vtkProperty, properties to edit
    _previousproperties     vtkProperty, copy of properties before edition
    """

    def __init__(self, parent=None, properties=None):
        super().__init__(parent)

        self.setWindowTitle('Mesh properties')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)

        self._previousproperties = vtkProperty()
        if properties: self.setProperties(properties)
        else: self._properties = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Opacity

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Opacity')
        self._opacitySlider = QSlider(self)
        self._opacitySlider.setMinimum(0)
        self._opacitySlider.setMaximum(100)
        self._opacitySlider.setValue(100)
        self._opacitySlider.setFixedWidth(200)
        self._opacitySlider.setOrientation(Qt.Horizontal)
        self._opacityEdit = QDoubleSpinBox(self)
        self._opacityEdit.setMinimum(0.0)
        self._opacityEdit.setMaximum(1.0)
        self._opacityEdit.setValue(1.0)
        self._opacityEdit.setDecimals(2)
        self._opacityEdit.setSingleStep(0.1)
        # self._opacityEdit.setFixedWidth(50)
        self._opacityEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._opacityEdit.valueChanged.connect(lambda: self._opacitySlider.setValue(int(self._opacityEdit.value()*100)))
        # noinspection PyUnresolvedReferences
        self._opacityEdit.valueChanged.connect(lambda: self._properties.SetOpacity(self._opacityEdit.value()))
        # noinspection PyUnresolvedReferences
        self._opacityEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._opacitySlider.valueChanged.connect(lambda: self._opacityEdit.setValue(self._opacitySlider.value()/100))
        layout.addWidget(label)
        layout.addWidget(self._opacitySlider)
        layout.addWidget(self._opacityEdit)
        self._layout.addLayout(layout)

        # Ambient

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Ambient')
        self._ambientSlider = QSlider(self)
        self._ambientSlider.setMinimum(0)
        self._ambientSlider.setMaximum(100)
        self._ambientSlider.setValue(100)
        self._ambientSlider.setFixedWidth(200)
        self._ambientSlider.setOrientation(Qt.Horizontal)
        self._ambientEdit = QDoubleSpinBox(self)
        self._ambientEdit.setMinimum(0.0)
        self._ambientEdit.setMaximum(1.0)
        self._ambientEdit.setValue(1.0)
        self._ambientEdit.setDecimals(2)
        self._ambientEdit.setSingleStep(0.1)
        # self._ambientEdit.setFixedWidth(50)
        self._ambientEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._ambientEdit.valueChanged.connect(lambda: self._ambientSlider.setValue(int(self._ambientEdit.value() * 100)))
        # noinspection PyUnresolvedReferences
        self._ambientEdit.valueChanged.connect(lambda: self._properties.SetAmbient(self._ambientEdit.value()))
        # noinspection PyUnresolvedReferences
        self._ambientEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._ambientSlider.valueChanged.connect(lambda: self._ambientEdit.setValue(self._ambientSlider.value() / 100))
        layout.addWidget(label)
        layout.addWidget(self._ambientSlider)
        layout.addWidget(self._ambientEdit)
        self._layout.addLayout(layout)

        # Diffuse

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Diffuse')
        self._diffuseSlider = QSlider(self)
        self._diffuseSlider.setMinimum(0)
        self._diffuseSlider.setMaximum(100)
        self._diffuseSlider.setValue(100)
        self._diffuseSlider.setFixedWidth(200)
        self._diffuseSlider.setOrientation(Qt.Horizontal)
        self._diffuseEdit = QDoubleSpinBox(self)
        self._diffuseEdit.setMinimum(0.0)
        self._diffuseEdit.setMaximum(1.0)
        self._diffuseEdit.setValue(1.0)
        self._diffuseEdit.setDecimals(2)
        self._diffuseEdit.setSingleStep(0.1)
        # self._diffuseEdit.setFixedWidth(50)
        self._diffuseEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._diffuseEdit.valueChanged.connect(lambda: self._diffuseSlider.setValue(int(self._diffuseEdit.value()*100)))
        # noinspection PyUnresolvedReferences
        self._diffuseEdit.valueChanged.connect(lambda: self._properties.SetDiffuse(self._diffuseEdit.value()))
        # noinspection PyUnresolvedReferences
        self._diffuseEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._diffuseSlider.valueChanged.connect(lambda: self._diffuseEdit.setValue(self._diffuseSlider.value()/100))
        layout.addWidget(label)
        layout.addWidget(self._diffuseSlider)
        layout.addWidget(self._diffuseEdit)
        self._layout.addLayout(layout)

        # Specular

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Specular')
        self._speculSlider = QSlider(self)
        self._speculSlider.setMinimum(0)
        self._speculSlider.setMaximum(100)
        self._speculSlider.setValue(100)
        self._speculSlider.setFixedWidth(200)
        self._speculSlider.setOrientation(Qt.Horizontal)
        self._speculEdit = QDoubleSpinBox(self)
        self._speculEdit.setMinimum(0.0)
        self._speculEdit.setMaximum(1.0)
        self._speculEdit.setValue(1.0)
        self._speculEdit.setDecimals(2)
        self._speculEdit.setSingleStep(0.1)
        # self._speculEdit.setFixedWidth(50)
        self._speculEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._speculEdit.valueChanged.connect(lambda: self._speculSlider.setValue(int(self._speculEdit.value() * 100)))
        # noinspection PyUnresolvedReferences
        self._speculEdit.valueChanged.connect(lambda: self._properties.SetSpecular(self._speculEdit.value()))
        # noinspection PyUnresolvedReferences
        self._speculEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._speculSlider.valueChanged.connect(lambda: self._speculEdit.setValue(self._speculSlider.value() / 100))
        layout.addWidget(label)
        layout.addWidget(self._speculSlider)
        layout.addWidget(self._speculEdit)
        self._layout.addLayout(layout)

        # SpecularPower

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Specular power')
        self._powerSlider = QSlider(self)
        self._powerSlider.setMinimum(0)
        self._powerSlider.setMaximum(5000)
        self._powerSlider.setValue(100)
        self._powerSlider.setFixedWidth(200)
        self._powerSlider.setOrientation(Qt.Horizontal)
        self._powerEdit = QDoubleSpinBox(self)
        self._powerEdit.setMinimum(0.0)
        self._powerEdit.setMaximum(50.0)
        self._powerEdit.setValue(1.0)
        self._powerEdit.setDecimals(2)
        self._powerEdit.setSingleStep(0.1)
        # self._powerEdit.setFixedWidth(50)
        self._powerEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._powerEdit.valueChanged.connect(lambda: self._powerSlider.setValue(int(self._powerEdit.value() * 100)))
        # noinspection PyUnresolvedReferences
        self._powerEdit.valueChanged.connect(lambda: self._properties.SetSpecularPower(self._powerEdit.value()))
        # noinspection PyUnresolvedReferences
        self._powerEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._powerSlider.valueChanged.connect(lambda: self._powerEdit.setValue(self._powerSlider.value() / 100))
        layout.addWidget(label)
        layout.addWidget(self._powerSlider)
        layout.addWidget(self._powerEdit)
        self._layout.addLayout(layout)

        # Metallic

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Metallic')
        self._metalSlider = QSlider(self)
        self._metalSlider.setMinimum(0)
        self._metalSlider.setMaximum(100)
        self._metalSlider.setValue(100)
        self._metalSlider.setFixedWidth(200)
        self._metalSlider.setOrientation(Qt.Horizontal)
        self._metalEdit = QDoubleSpinBox(self)
        self._metalEdit.setMinimum(0.0)
        self._metalEdit.setMaximum(1.0)
        self._metalEdit.setValue(1.0)
        self._metalEdit.setDecimals(2)
        self._metalEdit.setSingleStep(0.1)
        # self._metalEdit.setFixedWidth(50)
        self._metalEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._metalEdit.valueChanged.connect(lambda: self._metalSlider.setValue(int(self._metalEdit.value() * 100)))
        # noinspection PyUnresolvedReferences
        self._metalEdit.valueChanged.connect(lambda: self._properties.SetMetallic(self._metalEdit.value()))
        # noinspection PyUnresolvedReferences
        self._metalEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._metalSlider.valueChanged.connect(lambda: self._metalEdit.setValue(self._metalSlider.value() / 100))
        layout.addWidget(label)
        layout.addWidget(self._metalSlider)
        layout.addWidget(self._metalEdit)
        self._layout.addLayout(layout)

        # Roughness

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Roughness')
        self._roughSlider = QSlider(self)
        self._roughSlider.setMinimum(0)
        self._roughSlider.setMaximum(100)
        self._roughSlider.setValue(100)
        self._roughSlider.setFixedWidth(200)
        self._roughSlider.setOrientation(Qt.Horizontal)
        self._roughEdit = QDoubleSpinBox(self)
        self._roughEdit.setMinimum(0.0)
        self._roughEdit.setMaximum(1.0)
        self._roughEdit.setValue(1.0)
        self._roughEdit.setDecimals(2)
        self._roughEdit.setSingleStep(0.1)
        # self._roughEdit.setFixedWidth(50)
        self._roughEdit.setAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._roughEdit.valueChanged.connect(lambda: self._roughSlider.setValue(int(self._roughEdit.value() * 100)))
        # noinspection PyUnresolvedReferences
        self._roughEdit.valueChanged.connect(lambda: self._properties.SetRoughness(self._roughEdit.value()))
        # noinspection PyUnresolvedReferences
        self._roughEdit.valueChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._roughSlider.valueChanged.connect(lambda: self._roughEdit.setValue(self._roughSlider.value() / 100))
        layout.addWidget(label)
        layout.addWidget(self._roughSlider)
        layout.addWidget(self._roughEdit)
        self._layout.addLayout(layout)

        # Rendering algorithm and Mesh color

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        label = QLabel('Rendering algorithm')
        self._algo = QComboBox(self)
        self._algo.setEditable(False)
        self._algo.setFixedWidth(150)
        self._algo.addItem('Flat')
        self._algo.addItem('Gouraud')
        self._algo.addItem('Phong')
        self._algo.addItem('PBR')
        self._algo.setCurrentIndex(1)
        self._algo.adjustSize()
        layout.addWidget(label)
        layout.addWidget(self._algo)
        label = QLabel('Mesh color')
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._color = QPushButton(self)
        self._color.setFixedWidth(self._color.height())
        self._color.setAutoFillBackground(True)
        self._color.setStyleSheet('background-color: rgb(255, 0, 0)')
        layout.addWidget(label)
        layout.addWidget(self._color)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        self._color.clicked.connect(self._changeColor)
        # noinspection PyUnresolvedReferences
        self._algo.currentIndexChanged.connect(lambda: self._properties.SetInterpolation(self._algo.currentIndex()))
        # noinspection PyUnresolvedReferences
        self._algo.currentIndexChanged.connect(lambda: self.UpdateRender.emit())

        # PointsAsSpheres and Pointsize

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        self._sphere = QCheckBox('Points as spheres')
        label = QLabel('Point size')
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._psize = QSpinBox(self)
        self._psize.setMinimum(1)
        self._psize.setMaximum(50)
        self._psize.setValue(10)
        # self._psize.setFixedWidth(50)
        self._psize.setAlignment(Qt.AlignCenter)
        self._psize.setEnabled(False)
        layout.addWidget(self._sphere)
        layout.addWidget(label)
        layout.addWidget(self._psize)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        self._sphere.stateChanged.connect(lambda: self._properties.SetRenderPointsAsSpheres(self._sphere.checkState() == 2))
        # noinspection PyUnresolvedReferences
        self._sphere.stateChanged.connect(lambda: self._psize.setEnabled(self._sphere.checkState()))
        # noinspection PyUnresolvedReferences
        self._sphere.stateChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._psize.valueChanged.connect(lambda: self._properties.SetPointSize(self._psize.value()))
        # noinspection PyUnresolvedReferences
        self._psize.valueChanged.connect(lambda: self.UpdateRender.emit())

        # LinesAsTubes and Line width

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        self._tube = QCheckBox('Lines as tubes')
        label = QLabel('Line width')
        label.setAlignment(Qt.AlignRight)
        self._lsize = QSpinBox(self)
        self._lsize.setMinimum(1)
        self._lsize.setMaximum(50)
        self._lsize.setValue(10)
        # self._lsize.setFixedWidth(50)
        self._lsize.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._lsize.setEnabled(False)
        layout.addWidget(self._tube)
        layout.addWidget(label)
        layout.addWidget(self._lsize)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        self._tube.stateChanged.connect(lambda: self._properties.SetRenderLinesAsTubes(self._tube.checkState() == 2))
        # noinspection PyUnresolvedReferences
        self._tube.stateChanged.connect(lambda: self._lsize.setEnabled(self._tube.checkState()))
        # noinspection PyUnresolvedReferences
        self._tube.stateChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._lsize.valueChanged.connect(lambda: self._properties.SetLineWidth(self._lsize.value()))
        # noinspection PyUnresolvedReferences
        self._lsize.valueChanged.connect(lambda: self.UpdateRender.emit())

        # Vertex color and visibility

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        self._vertex = QCheckBox('Vertex visibility')
        label = QLabel('Vertex color')
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._vertexcolor = QPushButton(self)
        self._vertexcolor.setFixedWidth(self._vertexcolor.height())
        self._vertexcolor.setAutoFillBackground(True)
        self._vertexcolor.setStyleSheet('background-color: rgb(255, 0, 0)')
        self._vertexcolor.setEnabled(False)
        layout.addWidget(self._vertex)
        layout.addWidget(label)
        layout.addWidget(self._vertexcolor)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        self._vertex.stateChanged.connect(lambda: self._vertexcolor.setEnabled(self._vertex.checkState()))
        # noinspection PyUnresolvedReferences
        self._vertex.stateChanged.connect(lambda: self._properties.SetVertexVisibility(self._vertex.checkState() == 2))
        # noinspection PyUnresolvedReferences
        self._vertex.stateChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._vertexcolor.clicked.connect(self._changeVertexColor)

        # Edge color and visibility

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        self._edge = QCheckBox('Edge visibility')
        label = QLabel('Edge color')
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._edgecolor = QPushButton(self)
        self._edgecolor.setFixedWidth(self._edgecolor.height())
        self._edgecolor.setAutoFillBackground(True)
        self._edgecolor.setStyleSheet('background-color: rgb(255, 0, 0)')
        self._edgecolor.setEnabled(False)
        layout.addWidget(self._edge)
        layout.addWidget(label)
        layout.addWidget(self._edgecolor)
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        self._edge.stateChanged.connect(lambda: self._edgecolor.setEnabled(self._edge.checkState()))
        # noinspection PyUnresolvedReferences
        self._edge.stateChanged.connect(lambda: self._properties.SetEdgeVisibility(self._edge.checkState() == 2))
        # noinspection PyUnresolvedReferences
        self._edge.stateChanged.connect(lambda: self.UpdateRender.emit())
        # noinspection PyUnresolvedReferences
        self._edgecolor.clicked.connect(self._changeEdgeColor)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32':
            layout.setContentsMargins(10, 10, 10, 10)
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
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        reset.clicked.connect(self._reset)
        # noinspection PyUnresolvedReferences
        self.rejected.connect(self._rejected)

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
                self._color.setStyleSheet(buff)
                self._properties.SetColor(c.red() / 255, c.green() / 255, c.blue() / 255)
                # noinspection PyUnresolvedReferences
                self.UpdateRender.emit()
        # Revision 18/03/2025 >

    def _changeVertexColor(self):
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Vertex color', options=QColorDialog.DontUseNativeDialog)
        c = self.getVertexColor()
        c = [int(i * 255) for i in c]
        c = colorDialog(title='Vertex color', color=QColor(c[0], c[1], c[2]))
        if c is not None:
            if c.isValid():
                buff = 'background-color: rgb({}, {}, {})'.format(c.red(), c.green(), c.blue())
                self._vertexcolor.setStyleSheet(buff)
                self._properties.SetVertexColor(c.red() / 255, c.green() / 255, c.blue() / 255)
                # noinspection PyUnresolvedReferences
                self.UpdateRender.emit()
        # Revision 18/03/2025 >

    def _changeEdgeColor(self):
        # < Revision 18/03/2025
        # c = QColorDialog().getColor(parent=self, title='Edge color', options=QColorDialog.DontUseNativeDialog)
        c = self.getEdgeColor()
        c = [int(i * 255) for i in c]
        c = colorDialog(title='Edge color', color=QColor(c[0], c[1], c[2]))
        if c is not None:
            if c.isValid():
                buff = 'background-color: rgb({}, {}, {})'.format(c.red(), c.green(), c.blue())
                self._edgecolor.setStyleSheet(buff)
                self._properties.SetEdgeColor(c.red() / 255, c.green() / 255, c.blue() / 255)
                # noinspection PyUnresolvedReferences
                self.UpdateRender.emit()
        # Revision 18/03/2025 >

    def _rejected(self):
        self._properties.SetColor(self._previousproperties.GetColor())
        self._properties.SetOpacity(self._previousproperties.GetOpacity())
        self._properties.SetInterpolation(self._previousproperties.GetInterpolation())
        self._properties.SetAmbient(self._previousproperties.GetAmbient())
        self._properties.SetDiffuse(self._previousproperties.GetDiffuse())
        self._properties.SetSpecular(self._previousproperties.GetSpecular())
        self._properties.SetSpecularPower(self._previousproperties.GetSpecularPower())
        self._properties.SetMetallic(self._previousproperties.GetMetallic())
        self._properties.SetRoughness(self._previousproperties.GetRoughness())
        self._properties.SetEdgeVisibility(self._previousproperties.GetEdgeVisibility())
        self._properties.SetEdgeColor(self._previousproperties.GetEdgeColor())
        self._properties.SetVertexVisibility(self._previousproperties.GetVertexVisibility())
        self._properties.SetVertexColor(self._previousproperties.GetVertexColor())
        self._properties.SetPointSize(self._previousproperties.GetPointSize())
        self._properties.SetLineWidth(self._previousproperties.GetLineWidth())
        self._properties.SetRenderLinesAsTubes(self._previousproperties.GetRenderLinesAsTubes())
        self._properties.SetRenderPointsAsSpheres(self._previousproperties.GetRenderPointsAsSpheres())

    def _reset(self):
        self._rejected()
        self.setProperties(self._properties)

    # Public methods

    def setProperties(self, p):
        if isinstance(p, vtkProperty):
            self._properties = p
            self._previousproperties.DeepCopy(p)
            c = p.GetColor()
            self.setColor(c[0], c[1], c[2])
            self.setOpacity(p.GetOpacity())
            self.setAlgorithm(p.GetInterpolation())
            self.setAmbient(p.GetAmbient())
            self.setDiffuse(p.GetDiffuse())
            self.setSpecular(p.GetSpecular())
            self.setSpecularPower(p.GetSpecularPower())
            self.setMetallic(p.GetMetallic())
            self.setRoughness(p.GetRoughness())
            self.setEdgeVisibility(p.GetEdgeVisibility() == 1)
            c = p.GetEdgeColor()
            self.setEdgeColor(c[0], c[1], c[2])
            self.setVertexVisibility(p.GetVertexVisibility() == 1)
            c = p.GetVertexColor()
            self.setVertexColor(c[0], c[1], c[2])
            self.setPointSize(p.GetPointSize())
            self.setLineWidth(p.GetLineWidth())
            self.setLinesAsTubes(p.GetRenderLinesAsTubes() == 1)
            self.setPointsAsSpheres(p.GetRenderPointsAsSpheres() == 1)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(p)))

    def getProperties(self):
        return self._properties

    def getOpacity(self):
        return self._opacityEdit.value()

    def getAmbient(self):
        return self._ambientEdit.value()

    def getDiffuse(self):
        return self._diffuseEdit.value()

    def getSpecular(self):
        return self._speculEdit.value()

    def getSpecularPower(self):
        return self._powerEdit.value()

    def getMetallic(self):
        return self._metalEdit.value()

    def getRoughness(self):
        return self._roughEdit.value()

    def getAlgorithm(self):
        return self._algo.currentIndex()

    def getColor(self):
        c = self._color.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def getPointsAsSpheres(self):
        return self._sphere.checkState() == 2

    def getPointSize(self):
        return self._psize.value()

    def getLinesAsTubes(self):
        return self._tube.checkState() == 2

    def getLineWidth(self):
        return self._lsize.value()

    def getVertexVisibility(self):
        return self._vertex.checkState() == 2

    def getVertexColor(self):
        c = self._vertexcolor.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def getEdgeVisibility(self):
        return self._edge.checkState() == 2

    def getEdgeColor(self):
        c = self._edgecolor.styleSheet()
        c = c[c.index('(') + 1:c.index(')')].split(', ')
        return int(c[0]) / 255, int(c[1]) / 255, int(c[2]) / 255

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacityEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setAmbient(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._ambientEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setDiffuse(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._diffuseEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecular(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._speculEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecularPower(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 50.0:
                self._powerEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setMetallic(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._metalEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setRoughness(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._roughEdit.setValue(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setAlgorithm(self, v):
        if isinstance(v, int):
            if 0 <= v < 4:
                self._algo.setCurrentIndex(v)
            else: raise ValueError('parameter value {} is not between 0 and 3.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._color.setStyleSheet(buff)

    def setPointsAsSpheres(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._sphere.setCheckState(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setPointSize(self, v):
        if isinstance(v, (int, float)):
            if 0.0 < v <= 50.0:
                self._psize.setValue(int(v))
            else: raise ValueError('parameter value {} is not between 0 and 50.'.format(v))
        else: raise TypeError('parameter type {} is not int'.format(type(v)))

    def setLinesAsTubes(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._tube.setCheckState(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setLineWidth(self, v):
        if isinstance(v, (int, float)):
            if 0.0 < v <= 50.0:
                self._lsize.setValue(int(v))
            else: raise ValueError('parameter value {} is not between 0 and 50.'.format(v))
        else: raise TypeError('parameter type {} is not int'.format(type(v)))

    def setVertexVisibility(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._vertex.setCheckState(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVertexColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._vertexcolor.setStyleSheet(buff)

    def setEdgeVisibility(self, v):
        if isinstance(v, bool):
            if v: v = 2
            else: v = 0
            self._edge.setCheckState(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setEdgeColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        buff = 'background-color: rgb({}, {}, {})'.format(r, g, b)
        self._edgecolor.setStyleSheet(buff)
