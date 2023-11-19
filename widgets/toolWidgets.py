"""
    External packages/modules

        Name            Homepage link                                               Usage

        DIPY            https://www.dipy.org/                                       MR diffusion image processing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os.path import exists
from os.path import basename
from os.path import splitext

from xml.dom import minidom

from math import pi
from math import sqrt
from math import atan2
from math import acos
from math import degrees

from dipy.tracking.distances import lee_perpendicular_distance

from PyQt5.QtCore import pyqtSignal

from vtk import vtkActor
from vtk import vtkPoints
from vtk import vtkLine
from vtk import vtkPlane
from vtk import vtkPolyData
from vtk import vtkDataSetMapper
from vtk import vtkImageSlice
from vtk import vtkOBBTree
from vtk import vtkProperty
from vtk import vtkDistanceWidget
from vtk import vtkBiDimensionalWidget
from vtk import vtkAngleWidget
from vtk import vtkHandleWidget
from vtk import vtkLineWidget2
from vtk import vtkBorderWidget
from vtk import vtkTextWidget
from vtk import vtkImageSlice
from vtk import vtkTubeFilter
from vtk import vtkSphereSource
from vtk import vtkCutter
from vtk import vtkPolyDataMapper
from vtk import vtkDistanceRepresentation2D
from vtk import vtkBiDimensionalRepresentation2D
from vtk import vtkAngleRepresentation2D
from vtk import vtkPointHandleRepresentation3D
from vtk import vtkOrientedPolygonalHandleRepresentation3D
from vtk import vtkLineRepresentation
from vtk import vtkBillboardTextActor3D
from vtk import vtkRenderWindowInteractor
from vtk import VTK_FONT_FILE
from vtk import vtkTextProperty
from vtk import mutable as vtkmutable

from vtk import vtkLineSource
from vtk import vtkAppendPolyData

import Sisyphe.widgets as sw
import Sisyphe.core as sc

__all__ = ['ToolWidgetCollection',
           'NamedWidget',
           'DistanceWidget',
           'OrthogonalDistanceWidget',
           'AngleWidget',
           'BoxWidget',
           'TextWidget',
           'HandleWidget',
           'LineWidget']

"""
    Class hierarchy

        object -> ToolWidgetCollection
        object                -> NamedWidget
            vtkDistanceWidget  & NamedWidget -> DistanceWidget
        vtkBiDimensionalWidget & NamedWidget -> OrthogonalDistanceWidget
                vtkAngleWidget & NamedWidget -> AngleWidget  
               vtkBorderWidget & NamedWidget -> BoxWidget
                 vtkTextWidget & NamedWidget -> TextWidget
               vtkHandleWidget & NamedWidget -> HandleWidget
                vtkLineWidget2 & NamedWidget -> LineWidget
"""

vectorFloat2 = list[float, float] | tuple[float, float]
vectorFloat3 = list[float, float, float] | tuple[float, float, float]

_TOL = 20
_HSIZE = 20.0
_HLWIDTH = 2.0
_PSIZE = 2.0
_LWIDTH = 5.0
_ALPHA = 1.0
_FSIZE = 12
_FFAMILY = 'Arial'
_DEFAULTCOLOR = (1.0, 1.0, 1.0)   # White
_DEFAULTSCOLOR = (1.0, 1.0, 1.0)  # Red


class NamedWidget(object):
    """
        NamedWidget

        Inheritance

            object -> NamedObject

        Private attribute

            _name   str, name of the vtkWidget
            _3D     bool, display type (True: VolumeViewWidget, False: SliceViewWidget and derived classes)
                    used to control sphere and tube actor visibility for HandleWidget and LineWidget

        Public methods

            str = getName()
            setName(str)
            bool = hasName()
            setSliceDisplay()
            setVolumeDisplay()
            bool = isVolumeDisplay()
            bool = isSliceDisplay()

            inherited object methods
    """

    # Special method

    def __init__(self, name: str = '') -> None:
        self._name = name
        self._3D = False
        self._alpha = 1.0

    # Public methods

    def getName(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        if isinstance(name, str): self._name = name
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def hasName(self) -> bool:
        return self._name != ''

    def setSliceDisplay(self) -> None:
        self._3D = False

    def setVolumeDisplay(self) -> None:
        self._3D = True

    def isVolumeDisplay(self) -> bool:
        return self._3D

    def isSliceDisplay(self) -> bool:
        return not self._3D


class DistanceWidget(vtkDistanceWidget, NamedWidget):
    """
        DistanceWidget

        Inheritance

            (vtkDistanceWidget, NamedWidget) -> DistanceWidget

        Public method

            setVisibility(bool)
            bool = getVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setSelectedColor((float, float, float))
            float, float, float = getSelectedColor()
            setTolerance(float)
            float = getTolerance()
            setOpacity(float)
            float = getOpacity()
            float = getLinewidth()
            setLineWidth(float)
            float = getHandleSize()
            setHandleSize(float)
            str, int, bool, bool = getTextProperty()
            setTextProperty(bool, bool, int, str)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkDistanceWidget methods
    """

    # Special method

    def __init__(self, name: str) -> None:
        vtkDistanceWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetDistanceRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetDistanceRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetAxisProperty().SetColor(c[0], c[1], c[2])
        r.GetAxis().GetTitleTextProperty().SetColor(c[0], c[1], c[2])
        r.GetAxis().GetLabelTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        r = self.GetDistanceRepresentation()
        return r.GetPoint1Representation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        r = self.GetDistanceRepresentation()
        return r.GetPoint1Representation().GetSelectedProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint1Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetAxisProperty().SetOpacity(alpha)
        r.GetAxis().GetTitleTextProperty().SetOpacity(alpha)
        r.GetAxis().GetLabelTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        return self.GetDistanceRepresentation().GetAxisProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetLineWidth(width)
        r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetAxisProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        return self.GetDistanceRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r = self.GetDistanceRepresentation().GetAxis()
        r1 = r.GetTitleTextProperty()
        r1.SetBold(bold)
        r1.SetItalic(italic)
        r1.ShadowOff()
        r2 = r.GetLabelTextProperty()
        r2.SetBold(bold)
        r2.SetItalic(italic)
        r2.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r1.SetFontFamilyAsString(fontname)
            r2.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r1.SetFontFamily(VTK_FONT_FILE)
                r2.SetFontFamily(VTK_FONT_FILE)
                r1.SetFontFile(fontname)
                r2.SetFontFile(fontname)
            else:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> vtkTextProperty:
        r = self.GetDistanceRepresentation().GetAxis().GetTitleTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        self.GetDistanceRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        return self.GetDistanceRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        r = self.GetDistanceRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        return self.GetDistanceRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        r = vtkDistanceRepresentation2D()
        r.InstantiateHandleRepresentation()
        r.RulerModeOff()
        # r.SetRulerDistance(10.0)
        r.GetAxis().SetTickLength(0)
        r.GetAxis().SetNumberOfMinorTicks(0)
        r.GetAxis().SetMinorTickLength(0)
        self.SetRepresentation(r)
        self.setLineWidth(_HLWIDTH)
        self.setHandleSize(_HSIZE)
        self.setTolerance(_TOL)
        self.setColor(_DEFAULTCOLOR)
        self.setSelectedColor(_DEFAULTSCOLOR)
        self.setTextProperty(_FFAMILY)
        self.setOpacity(_ALPHA)


class OrthogonalDistanceWidget(vtkBiDimensionalWidget, NamedWidget):
    """
        OrthogonalDistanceWidget

        Inheritance

            (vtkDistanceWidget, NamedWidget) -> OrthogonalDistanceWidget

        Public method

            setVisibility(bool)
            bool = getVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setSelectedColor((float, float, float))
            float, float, float = getSelectedColor()
            setTolerance(float)
            float = getTolerance()
            setOpacity(float)
            float = getOpacity()
            float = getLinewidth()
            setLineWidth(float)
            float = getHandleSize()
            setHandleSize(float)
            str, int, bool, bool = getTextProperty()
            setTextProperty(bool, bool, int, str)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkBiDimensionalWidget methods
    """

    # Special method

    def __init__(self, name: str) -> None:
        vtkBiDimensionalWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetBiDimensionalRepresentation().SetVisibility(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetBiDimensionalRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint3Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint4Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetLineProperty().SetColor(c[0], c[1], c[2])
        r.GetTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        r = self.GetBiDimensionalRepresentation()
        return r.GetLineProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint3Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint4Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetSelectedLineProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        r = self.GetBiDimensionalRepresentation()
        return r.GetSelectedLineProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint3Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint4Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint1Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetPoint3Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetPoint4Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetLineProperty().SetOpacity(alpha)
        r.GetSelectedLineProperty().SetOpacity(alpha)
        r.GetTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        return self.GetBiDimensionalRepresentation().GetLineProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetProperty().SetLineWidth(width)
        r.GetPoint3Representation().GetProperty().SetLineWidth(width)
        r.GetPoint4Representation().GetProperty().SetLineWidth(width)
        r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint3Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint4Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetLineProperty().SetLineWidth(width)
        r.GetSelectedLineProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        return self.GetBiDimensionalRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r = self.GetBiDimensionalRepresentation().GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            else:
                r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> vtkTextProperty:
        r = self.GetBiDimensionalRepresentation().GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        self.GetBiDimensionalRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        return self.GetBiDimensionalRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        r = self.GetBiDimensionalRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)
        r.GetPoint3Representation().SetHandleSize(size)
        r.GetPoint4Representation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        return self.GetBiDimensionalRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        r = vtkBiDimensionalRepresentation2D()
        r.InstantiateHandleRepresentation()
        self.SetRepresentation(r)
        self.setLineWidth(_HLWIDTH)
        self.setHandleSize(_HSIZE)
        self.setTolerance(_TOL)
        self.setColor(_DEFAULTCOLOR)
        self.setSelectedColor(_DEFAULTSCOLOR)
        self.setTextProperty(_FFAMILY)
        self.setOpacity(_ALPHA)


class AngleWidget(vtkAngleWidget, NamedWidget):
    """
        AngleWidget

        Inheritance

            (vtkDistanceWidget, NamedWidget) -> AngleWidget

        Public method

            setVisibility(bool)
            bool = getVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setSelectedColor((float, float, float))
            (float, float, float) = getSelectedColor()
            setTolerance(float)
            float = getTolerance()
            setOpacity(float)
            float = getOpacity()
            setTextProperty(float, str, bool, bool)
            (float, str, bool, bool) = getTextProperty()
            float = getLinewidth()
            setLineWidth(float)
            float = getHandleSize()
            setHandleSize(float)
            str, int, bool, bool = getTextProperty()
            setTextProperty(bool, bool, int, str)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkAngleWidget methods
    """

    # Special method

    def __init__(self, name: str) -> None:
        vtkAngleWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetAngleRepresentation().SetVisibility(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetAngleRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        r = self.GetAngleRepresentation()
        r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetCenterRepresentation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetArc().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetRay1().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetRay2().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetArc().GetLabelTextProperty().SetColor(c[0], c[1], c[2])
        r.GetRay1().GetLabelTextProperty().SetColor(c[0], c[1], c[2])
        r.GetRay2().GetLabelTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        r = self.GetAngleRepresentation()
        return r.GetPoint1Representation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        r = self.GetAngleRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetCenterRepresentation().GetSelectedProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        r = self.GetAngleRepresentation()
        return r.GetPoint1Representation().GetSelectedProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        r = self.GetAngleRepresentation()
        r.GetPoint1Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetProperty().SetOpacity(alpha)
        r.GetCenterRepresentation().GetProperty().SetOpacity(alpha)
        r.GetArc().GetProperty().SetOpacity(alpha)
        r.GetRay1().GetProperty().SetOpacity(alpha)
        r.GetRay2().GetProperty().SetOpacity(alpha)
        r.GetArc().GetLabelTextProperty().SetOpacity(alpha)
        r.GetRay1().GetLabelTextProperty().SetOpacity(alpha)
        r.GetRay1().GetLabelTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        return self.GetAngleRepresentation().GetArc().GetProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        r = self.GetAngleRepresentation()
        r.GetPoint1Representation().GetProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetProperty().SetLineWidth(width)
        r.GetCenterRepresentation().GetProperty().SetLineWidth(width)
        r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetCenterRepresentation().GetSelectedProperty().SetLineWidth(width)
        r.GetArc().GetProperty().SetLineWidth(width)
        r.GetRay1().GetProperty().SetLineWidth(width)
        r.GetRay2().GetProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        return self.GetAngleRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r = self.GetAngleRepresentation().GetArc().GetLabelTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            else:
                r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> vtkTextProperty:
        r = self.GetAngleRepresentation().GetArc().GetLabelTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        self.GetAngleRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        return self.GetAngleRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        r = self.GetAngleRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)
        r.GetCenterRepresentation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        return self.GetAngleRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        r = vtkAngleRepresentation2D()
        r.InstantiateHandleRepresentation()
        self.SetRepresentation(r)
        self.setLineWidth(_HLWIDTH)
        self.setHandleSize(_HSIZE)
        self.setTolerance(_TOL)
        self.setColor(_DEFAULTCOLOR)
        self.setSelectedColor(_DEFAULTSCOLOR)
        self.setTextProperty(_FFAMILY)
        self.setOpacity(_ALPHA)


class BoxWidget(vtkBorderWidget, NamedWidget):
    """
        BoxWidget

        Inheritance

            (vtkDistanceWidget,NamedWidget) -> BoxWidget

        Public method

            setVisibility(bool)
            bool = getVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setTolerance(float)
            float = getTolerance()
            setOpacity(float)
            bool = getProportionalResize()
            setProportionalResize(bool)
            float = getOpacity()
            float = getLinewidth()
            setLineWidth(float)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkBorderWidget methods
    """

    # Special method

    def __init__(self, name: str) -> None:
        vtkBorderWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetBorderRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetBorderRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        r = self.GetBorderRepresentation()
        r.GetBorderProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        r = self.GetBorderRepresentation()
        return r.GetBorderProperty().GetColor()

    def setTolerance(self, tol: int) -> None:
        self.GetBorderRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        return self.GetBorderRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        self.GetBorderRepresentation().GetBorderProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        return self.GetBorderRepresentation().GetBorderProperty().GetOpacity()

    def setProportionalResize(self, v: bool) -> None:
        if isinstance(v, bool): self.GetRepresentation().SetProportionalResize(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getProportionalResize(self) -> bool:
        return self.GetRepresentation().GetProportionalResize()

    def setPosition(self, x: float, y: float) -> None:
        self.GetBorderRepresentation().SetPosition(x, y)

    def getPosition(self) -> vectorFloat2:
        return self.GetBorderRepresentation().GetPosition()

    def setSize(self, w: float, h: float) -> None:
        self.GetBorderRepresentation().SetPosition2(w, h)

    def getSize(self) -> vectorFloat2:
        return self.GetBorderRepresentation().GetPosition2()

    def setLineWidth(self, width: float) -> None:
        self.GetBorderRepresentation().GetBorderProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        return self.GetBorderRepresentation().GetBorderProperty().GetLineWidth()

    def setDefaultRepresentation(self) -> None:
        self.CreateDefaultRepresentation()
        r = self.GetBorderRepresentation()
        r.SetMinimumSize(_TOL, _TOL)
        r.SetTolerance(_TOL)
        r.VisibilityOn()
        r.SetShowBorderToOn()
        r.ProportionalResizeOn()
        r.GetBorderProperty().SetColor(_DEFAULTCOLOR[0], _DEFAULTCOLOR[1], _DEFAULTCOLOR[2])
        r.GetBorderProperty().SetOpacity(_ALPHA)
        r.GetBorderProperty().SetLineWidth(_HLWIDTH)
        self.SelectableOn()
        self.ResizableOn()


class TextWidget(vtkTextWidget, NamedWidget):
    """
        TextWidget

        Inheritance

            (vtkDistanceWidget, NamedObject) -> TextWidget

        Public method

            setVisibility(bool)
            bool = getVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setTolerance(float)
            float = getTolerance()
            setOpacity(float)
            float = getOpacity()
            float = getLinewidth()
            setLineWidth(float)
            float, str, bool, bool = getTextProperty()
            setTextProperty(float, str, bool, bool)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkTextWidget methods
    """

    # Special method

    def __init__(self, name: str) -> None:
        vtkTextWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetRepresentation().SetVisibility(v)
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        self.GetTextActor().GetTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        return self.GetTextActor().GetTextProperty().GetColor()

    def setTolerance(self, tol: int) -> None:
        self.GetBorderRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        return self.GetBorderRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        self.GetRepresentation().GetBorderProperty().SetOpacity(alpha)
        self.GetTextActor().GetTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        return self.GetTextActor().GetTextProperty().GetOpacity()

    def setPosition(self, x: float, y: float) -> None:
        self.GetRepresentation().SetPosition(x, y)

    def getPosition(self) -> vectorFloat2:
        return self.GetRepresentation().GetPosition()

    def setWidth(self, x: float, y: float) -> None:
        self.GetRepresentation().SetPosition2(x, y)

    def getWidth(self) -> vectorFloat2:
        return self.GetRepresentation().GetPosition2()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r = self.GetTextActor().GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            else:
                r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> vtkTextProperty:
        r = self.GetTextActor().GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setText(self, txt: str) -> None:
        if isinstance(txt, str):
            self.GetRepresentation().SetText(txt)
        else:
            raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getText(self) -> str:
        return self.GetRepresentation().GetText()

    def setDefaultRepresentation(self) -> None:
        self.CreateDefaultRepresentation()
        r = self.GetRepresentation()
        r.SetShowBorderToOff()
        r.GetBorderProperty().SetLineWidth(_HLWIDTH)
        self.GetTextActor().SetTextScaleModeToNone()
        pr = self.GetTextActor().GetTextProperty()
        pr.SetFontSize(_FSIZE * 2)
        pr.FrameOff()
        pr.SetColor(_DEFAULTCOLOR[0], _DEFAULTCOLOR[1], _DEFAULTCOLOR[2])
        pr.SetOpacity(_ALPHA)
        pr.SetFontFamilyAsString(_FFAMILY)
        pr.SetJustificationToCentered()
        pr.SetVerticalJustificationToCentered()
        self.SelectableOn()
        self.setOpacity(_ALPHA)


class HandleWidget(vtkHandleWidget, NamedWidget):
    """
        HandleWidget

        Inheritance

            (vtkDistanceWidget, NamedWidget) -> HandleWidget

        Class methods

            str = getFileExt()
            str = getFilterExt()

        Public methods

            updateContourActor()
            setName(str)
            setPrefix(str)
            str = getPrefix()
            setSuffix(str)
            str = getSuffix()
            setLegend(str)
            str = getLegend()
            str = getText()
            setOverlayEdgeVisibility(bool)
            bool = getVisibility()
            setFontSize(float)
            float = getFontSize()
            setFontBold(bool)
            bool = getFontBold()
            setFontItalic(bool)
            bool = getFontItalic()
            setTextProperty(float, str, bool, bool)
            (float, str, bool, bool) = getTextProperty()
            setTextVisibility(bool)
            bool = getTextVisibility()
            setSphereVisibility(bool)
            bool = getSphereVisibility()
            setSphereRadius(float)
            float = getSphereRadius()
            setColor((float, float, float))
            float, float, float = getColor()
            setSelectedColor((float, float, float))
            float, float, float = getSelectedColor()
            setPosition((float, float, float))
            float, float, float = getPosition()
            planeProjection(vtkPlane | vtkImageSlice | SliceViewWidget)
            int = meshSurfaceProjection(vtkPlane | vtkImageSlice | SliceViewWidget)
            setLineWidth(float)
            float = getLineWidth()
            setHandleSize(float)
            float = getHandleSize()
            setTolerance(int)
            int = getTolerance()
            setOpacity(float)
            float = getOpacity()
            setSphereProperties(vtkProperty)
            vtkProperty = getSphereProperties()
            setMetallic(float)
            float = getMetallic()
            setRoughness(float)
            float = getRoughness()
            setAmbient(float)
            float = getAmbient()
            setSpecular(float)
            float = getSpecular()
            setSpecularPower(float)
            float = getSpecularPower()
            HandleWidget = deepCopy()
            copyAttributesTo(HandleWidget)
            copyAttributesFrom(HandleWidget)
            float = getDistanceToPoint()
            float = getDistanceToHandleWidget()
            float = getDistanceToLine()
            float = getDistanceToLineWidget()
            float = getDistanceToPlane()
            createXML(minidom.Document, minidom.Element)
            parseXMLNode(minidom.Element)
            parseXML(minidom.Document)
            saveAs(str)
            load(str)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkHandleWidget methods

        Revisions:

            07/09/2023  __init__() method bugfix, call setDefaultRepresentation() after vtkActor declaration
            08/09/2023  add setPrefix(), getPrefix(), setSuffix(), getSuffix(), getText() methods
                        add setFontFamily(), getFontFamily() methods
                        add font family update to copyAttributesTo() and copyAttributesFrom() methods
            10/09/2023  type hinting
            15/09/2023  vtk SetHandleSize bugfix in setHandleSize() and getHandleSize() methods
            21/09/2023  setDefaultRepresentation() method,
                        replace vtkPointHandleRepresentation3D with vtkOrientedPolygonalHandleRepresentation3D
            28/09/2023  parseXMLNode() method bugfix
            08/10/2023  add moveToPlane() method
    """

    _FILEEXT = '.xpoint'
    _DEFAULTSPHERERADIUS = 2
    _DEFAULTSPHERERESOLUTION = 32

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Target (*{})'.format(cls._FILEEXT)

    # Special method

    def __init__(self, name: str, legend: str = 'Target') -> None:
        vtkHandleWidget.__init__(self)
        NamedWidget.__init__(self, name)

        self.AddObserver('InteractionEvent', self._onInteractionEvent)
        self.AddObserver('EndInteractionEvent', self._onEndInteractionEvent)
        self.AddObserver('EnableEvent', self._onEnableEvent)
        self.AddObserver('DisableEvent', self._onDisableEvent)

        self._legend = legend
        self._prefix = ''
        self._suffix = ''
        self._hsize = _HSIZE

        self._targetText = vtkBillboardTextActor3D()
        self._sphere = vtkSphereSource()
        self._sphereActor = vtkActor()
        self._cutter = vtkCutter()
        self._contourActor = vtkActor()
        self.setDefaultRepresentation()

        self._targetText.SetInput('{}\n{}'.format(legend, self.getName()))
        self._targetText.SetDisplayOffset(40, 0)
        self._targetText.GetTextProperty().SetFontFamilyAsString(_FFAMILY)
        self._targetText.GetTextProperty().FrameOff()
        self._targetText.GetTextProperty().ShadowOff()
        self._targetText.GetTextProperty().SetFontSize(_FSIZE)
        self._targetText.GetTextProperty().SetVerticalJustificationToCentered()
        self._targetText.GetTextProperty().SetBackgroundOpacity(0.0)

        self._sphere.SetThetaResolution(self._DEFAULTSPHERERESOLUTION)
        self._sphere.SetPhiResolution(self._DEFAULTSPHERERESOLUTION)
        self._sphere.SetRadius(self._DEFAULTSPHERERADIUS)

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(self._sphere.GetOutputPort())
        self._sphereActor.SetMapper(mapper)
        self._sphereActor.GetProperty().SetInterpolationToPhong()
        self._sphereActor.GetProperty().SetRepresentationToSurface()
        self._sphereActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self._sphereActor.GetProperty().SetOpacity(0.5 * _ALPHA)

        self._cutter.SetInputConnection(self._sphere.GetOutputPort())

        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(self._cutter.GetOutputPort())
        mapper.ScalarVisibilityOff()
        self._contourActor.SetMapper(mapper)
        r = self._contourActor.GetProperty()
        r.SetColor(1.0, 1.0, 1.0)
        r.SetEdgeColor(1.0, 1.0, 1.0)
        r.SetVertexColor(1.0, 1.0, 1.0)
        r.SetOpacity(_ALPHA)
        r.SetLineWidth(_HLWIDTH)
        r.EdgeVisibilityOff()
        r.VertexVisibilityOff()
        r.RenderLinesAsTubesOn()
        r.SetInterpolationToFlat()
        r.SetRepresentationToSurface()

    def __str__(self) -> str:
        buff = '{}:\n'.format(self.getName())
        p = self.getPosition()
        buff += 'Position: {:.1f} {:.1f} {:.1f}\n'.format(p[0], p[1], p[2])
        buff += 'Prefix: {}\n'.format(self.getPrefix())
        buff += 'Suffix: {}\n'.format(self.getSuffix())
        buff += 'Legend: {}\n'.format(self.getLegend())
        buff += 'Color: {}\n'.format(self.getColor())
        buff += 'Selected Color: {}\n'.format(self.getColor())
        buff += 'Opacity: {}\n'.format(self.getOpacity())
        buff += 'Tolerance: {}\n'.format(self.getTolerance())
        buff += 'Handle Line width: {}\n'.format(self.getLineWidth())
        buff += 'Handle size: {}\n'.format(self.getHandleSize())
        buff += 'Font:\n'
        buff += '\tFamily: {}\n'.format(self.getFontFamily())
        buff += '\tSize: {}\n'.format(self.getFontSize())
        buff += '\tBold: {}\n'.format(self.getFontBold())
        buff += '\tItalic: {}\n'.format(self.getFontItalic())
        buff += '\tVisibility: {}\n'.format(self.getTextVisibility())
        buff += '\tOffset: {}\n'.format(self.getTextOffset())
        buff += 'Safety:\n'
        buff += '\tRadius: {}\n'.format(self.getSphereRadius())
        buff += '\tVisibility: {}\n'.format(self.getSphereVisibility())
        return buff

    # Private VTK event methods

    def _onInteractionEvent(self, widget, event) -> None:
        p = self.GetHandleRepresentation().GetWorldPosition()
        self._targetText.SetPosition(p)
        self._sphere.SetCenter(p)
        self._sphere.Update()
        self._cutter.Update()

    def _onEndInteractionEvent(self, widget, event) -> None:
        pass

    def _onEnableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        renderer.AddActor(self._targetText)
        renderer.AddActor(self._sphereActor)
        renderer.AddActor(self._contourActor)
        self._targetText.SetVisibility(True)
        self.setVisibility(True)
        p = self.GetHandleRepresentation().GetWorldPosition()
        self._targetText.SetPosition(p)
        self._sphere.SetCenter(p)
        self._sphere.Update()
        # Update contour actor
        props = renderer.GetViewProps()
        for i in range(props.GetNumberOfItems()):
            prop = props.GetItemAsObject(i)
            if isinstance(prop, vtkImageSlice):
                # self._cutter.SetCutFunction(prop.GetMapper().GetSlicePlane())
                self.updateContourActor(prop.GetMapper().GetSlicePlane())
                break

    def _onDisableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        renderer.RemoveActor(self._targetText)
        renderer.RemoveActor(self._sphereActor)
        renderer.RemoveActor(self._contourActor)
        del self._targetText
        del self._sphereActor
        del self._contourActor

    # Private method

    def _setText(self, txt: str) -> None:
        self._targetText.SetInput(txt)

    # Public methods

    def updateContourActor(self, plane: vtkPlane) -> None:
        if isinstance(plane, vtkPlane):
            plane2 = vtkPlane()
            plane2.SetNormal(plane.GetNormal())
            plane2.SetOrigin(plane.GetOrigin())
            plane2.Push(0.5)
            self._cutter.SetCutFunction(plane2)
            self._cutter.Update()
        else: raise TypeError('parameter type {} is not vtkPlane.'.format(type(plane)))

    def setName(self, name: str) -> None:
        super().setName(name)
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def setPrefix(self, txt: str = '') -> None:
        if txt != '':
            if txt[-1] != ' ': txt += ' '
        self._prefix = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getPrefix(self) -> str:
        return self._prefix

    def setSuffix(self, txt: str = '') -> None:
        if txt != '':
            if txt[0] != ' ': txt = ' ' + txt
        self._suffix = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getSuffix(self) -> str:
        return self._suffix

    def setLegend(self, txt: str = 'Target') -> None:
        self._legend = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getLegend(self) -> str:
        return self._legend

    def getText(self) -> str:
        return self._targetText.GetInput()

    def setFontSize(self, size: int) -> None:
        if isinstance(size, int): self._targetText.GetTextProperty().SetFontSize(size)
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getFontSize(self) -> int:
        return self._targetText.GetTextProperty().GetFontSize()

    def setFontBold(self, v: bool) -> None:
        if isinstance(v, bool): self._targetText.GetTextProperty().SetBold(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontBold(self) -> bool:
        return self._targetText.GetTextProperty().GetBold() > 0

    def setFontItalic(self, v: bool) -> None:
        if isinstance(v, bool): self._targetText.GetTextProperty().SetItalic(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontItalic(self) -> bool:
        return self._targetText.GetTextProperty().GetItalic() > 0

    def setFontFamily(self, fontname: str = _FFAMILY) -> None:
        r = self._targetText.GetTextProperty()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            else:
                r.SetFontFamilyAsString('Arial')

    def getFontFamily(self) -> str:
        return self._targetText.GetTextProperty().GetFontFamilyAsString()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r = self._targetText.GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            else:
                r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> vtkTextProperty:
        r = self._targetText.GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTextOffset(self, r: tuple[int, int] | list[int, int]) -> None:
        self._targetText.SetDisplayOffset(r[0], r[1])

    def getTextOffset(self) -> tuple[int, int]:
        return self._targetText.GetDisplayOffset()

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            if not v:
                self._alpha = self.GetHandleRepresentation().GetProperty().GetOpacity()
                self.GetHandleRepresentation().GetProperty().SetOpacity(0.0)
            else:
                self.GetHandleRepresentation().GetProperty().SetOpacity(self._alpha)
            self._targetText.SetVisibility(v)
            if self.isVolumeDisplay():
                self._sphereActor.SetVisibility(v)
                self._contourActor.SetVisibility(False)
            else:
                self._sphereActor.SetVisibility(False)
                self._contourActor.SetVisibility(v)
            r = self.GetCurrentRenderer()
            if r is not None:
                r = r.GetRenderWindow()
                if r is not None: r.Render()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self.GetHandleRepresentation().GetProperty().GetOpacity() > 0

    def setTextVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._targetText.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextVisibility(self) -> bool:
        return self._targetText.GetVisibility() > 0

    def setSphereVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            if self.isVolumeDisplay():
                self._sphereActor.SetVisibility(v)
                self._contourActor.SetVisibility(False)
            else:
                self._sphereActor.SetVisibility(False)
                self._contourActor.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSphereVisibility(self) -> bool:
        return self._sphereActor.GetVisibility() > 0 or \
            self._contourActor.GetVisibility() > 0

    def setSphereRadius(self, radius: float) -> None:
        if isinstance(radius, float):
            self._sphere.SetRadius(radius)
            self._sphere.Update()
        else: raise TypeError('parameter type {} is not float.'.format(type(radius)))

    def getSphereRadius(self) -> float:
        return self._sphere.GetRadius()

    def setColor(self, c: vectorFloat3) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                if all([0.0 <= i <= 1.0 for i in c]):
                    self.GetHandleRepresentation().GetProperty().SetColor(c[0], c[1], c[2])
                    self._targetText.GetTextProperty().SetColor(c[0], c[1], c[2])
                    self._sphereActor.GetProperty().SetColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetEdgeColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetVertexColor(c[0], c[1], c[2])
                else: raise ValueError('parameter value is not between 0.0 and 1.0.')
            else: raise ValueError('list length {} is not 3.'.format(len(c)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getColor(self) -> vectorFloat3:
        return self.GetRepresentation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                if all([0.0 <= i <= 1.0 for i in c]):
                    self.GetHandleRepresentation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
                else: raise ValueError('parameter value is not between 0.0 and 1.0.')
            else: raise ValueError('list length {} is not 3.'.format(len(c)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getSelectedColor(self) -> vectorFloat3:
        return self.GetHandleRepresentation().GetSelectedProperty().GetColor()

    def setPosition(self, p: vectorFloat3) -> None:
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, float) for i in p]):
                    self.GetHandleRepresentation().SetWorldPosition(p)
                    self._targetText.SetPosition(p)
                    self._sphere.SetCenter(p)
                    self._sphere.Update()
                    # Update contour actor
                    renderer = self.GetCurrentRenderer()
                    if renderer is not None:
                        props = renderer.GetViewProps()
                        for i in range(props.GetNumberOfItems()):
                            prop = props.GetItemAsObject(i)
                            if isinstance(prop, vtkImageSlice):
                                self.updateContourActor(prop.GetMapper().GetSlicePlane())
                                break
                else: raise TypeError('parameter type is not float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition(self) -> vectorFloat3:
        return self.GetHandleRepresentation().GetWorldPosition()

    def planeProjection(self, plane: vtkPlane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget) -> None:
        """
            Move Handle position to intersection of normal line and plane
            plane   SliceViewWidget | vtkImageSlice | vtkPlane
        """
        if isinstance(plane, sw.sliceViewWidgets.SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            t = vtkmutable(0.0)
            p = [0.0, 0.0, 0.0]
            p2 = list(self.getPosition())
            v2 = plane.GetNormal()
            p2[0] += (v2[0] * 10.0)
            p2[1] += (v2[1] * 10.0)
            p2[2] += (v2[2] * 10.0)
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            plane.IntersectWithLine(self.getPosition(), p2, t, p)
            self.setPosition(p)

    def meshSurfaceProjection(self,
                              plane: vtkPlane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget,
                              mesh: sc.sisypheMesh.SisypheMesh) -> int:
        """
            Move Handle position to intersection of normal line and mesh surface
            plane   SliceViewWidget | vtkImageSlice | vtkPlane
            mesh    SisypheMesh
        """
        if isinstance(plane, sw.sliceViewWidgets.SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            v = list(plane.GetNormal())
            v[0] *= 200.0
            v[1] *= 200.0
            v[2] *= 200.0
        else: return 0
        if isinstance(mesh, sc.sisypheMesh.SisypheMesh):
            f = vtkOBBTree()
            f.SetDataSet(mesh.getPolyData())
            f.BuildLocator()
            ps = vtkPoints()
            p = self.GetHandleRepresentation().GetWorldPosition()
            p1 = [p[0] + v[0],
                  p[1] + v[1],
                  p[2] + v[2]]
            p2 = [p[0] - v[0],
                  p[1] - v[1],
                  p[2] - v[2]]
            inter = f.IntersectWithLine(p1, p2, ps, None)
            if inter != 0:
                n = ps.GetNumberOfPoints()
                print(n)
                if n > 0:
                    d = list()
                    for i in range(n):
                        pr = ps.GetPoint(i)
                        d.append(sqrt((p[0] - pr[0])**2 + (p[1] - pr[1])**2 + (p[2] - pr[2])**2))
                    self.setPosition(ps.GetPoint(d.index(min(d))))
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def setLineWidth(self, width: float) -> None:
        if isinstance(width, float):
            self.GetHandleRepresentation().GetProperty().SetLineWidth(width)
            self.GetHandleRepresentation().GetSelectedProperty().SetLineWidth(width)
            self._contourActor.GetProperty().SetLineWidth(width)
        else: raise TypeError('parameter functype {} is not float'.format(type(width)))

    def getLineWidth(self) -> float:
        return self.GetHandleRepresentation().GetProperty().GetLineWidth()

    def setHandleSize(self, size: float) -> None:
        if isinstance(size, float):
            self._hsize = size
            lineh = vtkLineSource()
            linev = vtkLineSource()
            lineh.SetPoint1(-self._hsize / 2, 0.0, 0.0)
            lineh.SetPoint2(self._hsize / 2, 0.0, 0.0)
            linev.SetPoint1(0.0, -self._hsize / 2, 0)
            linev.SetPoint2(0.0, self._hsize / 2, 0)
            cross = vtkAppendPolyData()
            cross.AddInputConnection(lineh.GetOutputPort())
            cross.AddInputConnection(linev.GetOutputPort())
            cross.Update()
            self.GetHandleRepresentation().SetHandle(cross.GetOutput())
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getHandleSize(self) -> float:
        return self._hsize

    def setTolerance(self, tol: int) -> None:
        if isinstance(tol, int):
            self.GetHandleRepresentation().SetTolerance(tol)
        else: raise TypeError('parameter type {} is not int'.format(type(tol)))

    def getTolerance(self) -> int:
        return self.GetHandleRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        if isinstance(alpha, float):
            if 0.0 <= alpha <= 1.0:
                self.GetHandleRepresentation().GetProperty().SetOpacity(alpha)
                self.GetHandleRepresentation().GetSelectedProperty().SetOpacity(alpha)
                self._targetText.GetTextProperty().SetOpacity(alpha)
                self._contourActor.GetProperty().SetOpacity(alpha)
                self._sphereActor.GetProperty().SetOpacity(0.5 * alpha)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(alpha))
        else: raise TypeError('parameter type {} is not float'.format(type(alpha)))

    def getOpacity(self) -> float:
        return self.GetHandleRepresentation().GetProperty().GetOpacity()

    def setInterpolation(self, inter: int) -> None:
        if isinstance(inter, int):
            self._sphereActor.GetProperty().SetInterpolation(inter)
        else: raise TypeError('parameter functype {} is not int.'.format(type(inter)))

    def getInterpolation(self) -> int:
        return self._sphereActor.GetProperty().GetInterpolation()

    def setMetallic(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetMetallic(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getMetallic(self) -> float:
        return self._sphereActor.GetProperty().GetMetallic()

    def setRoughness(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetRoughness(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getRoughness(self) -> float:
        return self._sphereActor.GetProperty().GetRoughness()

    def setAmbient(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetAmbient(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getAmbient(self) -> float:
        return self._sphereActor.GetProperty().GetAmbient()

    def setSpecular(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetSpecular(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecular(self) -> float:
        return self._sphereActor.GetProperty().GetSpecular()

    def setSpecularPower(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetSpecularPower(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecularPower(self) -> float:
        return self._sphereActor.GetProperty().GetSpecularPower()

    def setSphereProperties(self, p: vtkProperty) -> None:
        if isinstance(p, vtkProperty): self._sphereActor.SetProperty(p)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(p)))

    def getSphereProperties(self) -> vtkProperty:
        return self._sphereActor.GetProperty()

    def deepCopy(self) -> HandleWidget:
        r = vtkPointHandleRepresentation3D()
        r.DeepCopy(self.GetHandleRepresentation())
        widget = HandleWidget(self.getName())
        widget.SetRepresentation(r)
        widget.copyAttributesFrom(self)
        return widget

    def copyAttributesTo(self, tool) -> None:
        if isinstance(tool, HandleWidget):
            tool._setText(self.getText())
            tool.setFontSize(self.getFontSize())
            tool.setFontBold(self.getFontBold())
            tool.setFontItalic(self.getFontItalic())
            tool.setFontFamily(self.getFontFamily())
            tool.setVisibility(self.getVisibility())
            tool.setTextVisibility(self.getTextVisibility())
            tool.setTextOffset(self.getTextOffset())
            tool.setColor(self.getColor())
            tool.setSelectedColor(self.getSelectedColor())
            tool.setLineWidth(self.getLineWidth())
            tool.setHandleSize(self.getHandleSize())
            tool.setTolerance(self.getTolerance())
            tool.setOpacity(self.getOpacity())
            tool.setInterpolation(self.getInterpolation())
            tool.setSphereRadius(self.getSphereRadius())
            tool.setSphereVisibility(self.getSphereVisibility())
            tool.setMetallic(self.getMetallic())
            tool.setRoughness(self.getRoughness())
            tool.setAmbient(self.getAmbient())
            tool.setSpecular(self.getSpecular())
            tool.setSpecularPower(self.getSpecularPower())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(tool)))

    def copyAttributesFrom(self, tool) -> None:
        if isinstance(tool, HandleWidget):
            self._setText(tool.getText())
            self.setFontSize(tool.getFontSize())
            self.setFontBold(tool.getFontBold())
            self.setFontItalic(tool.getFontItalic())
            self.setFontFamily(tool.getFontFamily())
            self.setVisibility(tool.getVisibility())
            self.setTextVisibility(tool.getTextVisibility())
            self.setTextOffset(tool.getTextOffset())
            self.setColor(tool.getColor())
            self.setSelectedColor(tool.getSelectedColor())
            self.setLineWidth(tool.getLineWidth())
            self.setHandleSize(tool.getHandleSize())
            self.setTolerance(tool.getTolerance())
            self.setOpacity(tool.getOpacity())
            self.setInterpolation(tool.getInterpolation())
            self.setSphereRadius(tool.getSphereRadius())
            self.setSphereVisibility(tool.getSphereVisibility())
            self.setMetallic(tool.getMetallic())
            self.setRoughness(tool.getRoughness())
            self.setAmbient(tool.getAmbient())
            self.setSpecular(tool.getSpecular())
            self.setSpecularPower(tool.getSpecularPower())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(tool)))

    def setDefaultRepresentation(self) -> None:
        # Handle representation
        r = vtkOrientedPolygonalHandleRepresentation3D()
        lineh = vtkLineSource()
        linev = vtkLineSource()
        lineh.SetPoint1(-_HSIZE / 2, 0.0, 0.0)
        lineh.SetPoint2(_HSIZE / 2, 0.0, 0.0)
        linev.SetPoint1(0.0, -_HSIZE / 2, 0)
        linev.SetPoint2(0.0, _HSIZE / 2, 0)    
        cross = vtkAppendPolyData()
        cross.AddInputConnection(lineh.GetOutputPort())
        cross.AddInputConnection(linev.GetOutputPort())
        cross.Update()
        r.SetHandle(cross.GetOutput())
        r.HandleVisibilityOn()
        # widget
        self.AllowHandleResizeOff()
        self.SetRepresentation(r)
        self.setTextProperty(_FFAMILY)
        self.setLineWidth(_HLWIDTH)
        self.setColor(_DEFAULTCOLOR)
        self.setSelectedColor(_DEFAULTSCOLOR)
        self.setTolerance(_TOL)
        self.setOpacity(_ALPHA)

    # Various distance methods

    def getDistanceToPoint(self, p: vectorFloat3) -> float:
        """
            p       [float, float, float]
            return  float, distance between parameter point and self HandleWidget position
        """
        p0 = self.getPosition()
        return sqrt((p0[0] - p[0])**2 + (p0[1] - p[1])**2 + (p0[2] - p[2])**2)

    def getDistanceToHandleWidget(self, hw: HandleWidget) -> float:
        """
            hw      HandleWidget
            return  float, distance between parameter HandleWidget position and self HandleWidgets
        """
        if isinstance(hw, HandleWidget): return self.getDistanceToPoint(hw.getPosition())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(hw)))

    def getDistanceToLine(self, p1: vectorFloat3, p2: vectorFloat3) -> list[float, vectorFloat3]:
        """
            p1, p2  [float, float, float], 2 points to define line equation
            return  [float, [float, float, float]]
                    float, distance between line parameter and self HandleWidgets
                    [float, float, float], coordinates of the closest point on line parameter
        """
        r = list()
        line = vtkLine()
        t = vtkmutable(0.0)
        cp = [0.0, 0.0, 0.0]
        r.append(sqrt(line.DistanceToLine(self.getPosition(), p1, p2, t, cp)))
        r.append(cp)
        return r

    def getDistanceToLineWidget(self, lw: HandleWidget) -> list[float, vectorFloat3]:
        """
            lw      LineWidget
            return  float, distance between LineWidget line parameter and self HandleWidgets position
        """
        if isinstance(lw, LineWidget): return self.getDistanceToLine(lw.getPosition1(), lw.getPosition2())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(lw)))

    def getDistanceToPlane(self, p: vtkPlane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget) -> float:
        """
            p       SliceViewWidget | vtkImageSlice | vtkPlane
            return  float, distance between plane parameter and self HandleWidgets position
        """
        if isinstance(p, sw.sliceViewWidgets.SliceViewWidget): p = p.getVtkImageSliceVolume()
        if isinstance(p, vtkImageSlice): p = p.GetMapper().GetSlicePlane()
        if isinstance(p, vtkPlane):
            return p.DistanceToPlane(self.getPosition())
        else: raise TypeError('parameter type {} is not SliceViewWidget, vtkImageSlice or vtkPlane.'.format(type(p)))

    # IO methods

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                tool = doc.createElement('point')
                currentnode.appendChild(tool)
                # name
                node = doc.createElement('name')
                tool.appendChild(node)
                txt = doc.createTextNode(self.getName())
                node.appendChild(txt)
                # prefix
                node = doc.createElement('prefix')
                tool.appendChild(node)
                txt = doc.createTextNode(self.getPrefix())
                node.appendChild(txt)
                # suffix
                node = doc.createElement('suffix')
                tool.appendChild(node)
                txt = doc.createTextNode(self.getSuffix())
                node.appendChild(txt)
                # legend
                node = doc.createElement('legend')
                tool.appendChild(node)
                txt = doc.createTextNode(self.getLegend())
                node.appendChild(txt)
                # position
                node = doc.createElement('position')
                tool.appendChild(node)
                buff = [str(v) for v in self.getPosition()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # font size
                node = doc.createElement('fontsize')
                tool.appendChild(node)
                buff = self.getFontSize()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font bold
                node = doc.createElement('fontbold')
                tool.appendChild(node)
                buff = self.getFontBold()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font italic
                node = doc.createElement('fontitalic')
                tool.appendChild(node)
                buff = self.getFontItalic()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font family
                node = doc.createElement('fontfamily')
                tool.appendChild(node)
                buff = self.getFontFamily()
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # text offset
                node = doc.createElement('textoffset')
                tool.appendChild(node)
                buff = [str(v) for v in self.getTextOffset()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # text visibility
                node = doc.createElement('textvisibility')
                tool.appendChild(node)
                buff = self.getTextVisibility()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # color
                node = doc.createElement('color')
                tool.appendChild(node)
                buff = [str(v) for v in self.getColor()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # selectedcolor
                node = doc.createElement('selectedcolor')
                tool.appendChild(node)
                buff = [str(v) for v in self.getSelectedColor()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # opacity
                node = doc.createElement('opacity')
                tool.appendChild(node)
                buff = self.getOpacity()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # linewidth
                node = doc.createElement('linewidth')
                tool.appendChild(node)
                buff = self.getLineWidth()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # handlesize
                node = doc.createElement('handlesize')
                tool.appendChild(node)
                buff = self.getHandleSize()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # tolerance
                node = doc.createElement('tolerance')
                tool.appendChild(node)
                buff = self.getTolerance()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # sphereradius
                node = doc.createElement('sphereradius')
                tool.appendChild(node)
                buff = self.getSphereRadius()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # sphere visibility
                node = doc.createElement('spherevisibility')
                tool.appendChild(node)
                buff = self.getSphereVisibility()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # interpolation
                node = doc.createElement('interpolation')
                tool.appendChild(node)
                buff = self.getInterpolation()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # metallic
                node = doc.createElement('metallic')
                tool.appendChild(node)
                buff = self.getMetallic()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # roughness
                node = doc.createElement('roughness')
                tool.appendChild(node)
                buff = self.getRoughness()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # ambient
                node = doc.createElement('ambient')
                tool.appendChild(node)
                buff = self.getAmbient()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # specular
                node = doc.createElement('specular')
                tool.appendChild(node)
                buff = self.getSpecular()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # specularpower
                node = doc.createElement('specularpower')
                tool.appendChild(node)
                buff = self.getSpecularPower()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXMLNode(self, currentnode: minidom.Element) -> None:
        if currentnode.nodeName == 'point':
            for node in currentnode.childNodes:
                if node.hasChildNodes():
                    buff = node.firstChild.data
                    if buff is not None:
                        # name
                        if node.nodeName == 'name': self.setName(buff)
                        # prefix
                        if node.nodeName == 'prefix': self.setPrefix(buff)
                        # suffix
                        if node.nodeName == 'suffix': self.setSuffix(buff)
                        # legend
                        if node.nodeName == 'legend': self.setLegend(buff)
                        # position
                        if node.nodeName == 'position':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setPosition(buff)
                        # font size
                        elif node.nodeName == 'fontsize': self.setFontSize(int(buff))
                        # font bold
                        elif node.nodeName == 'fontbold': self.setFontBold(bool(buff == 'True'))
                        # font italic
                        elif node.nodeName == 'fontitalic': self.setFontItalic(bool(buff == 'True'))
                        # font family
                        elif node.nodeName == 'fontfamily': self.setFontFamily(buff)
                        # text offset
                        elif node.nodeName == 'textoffset':
                            buff = buff.split(' ')
                            buff = [int(i) for i in buff]
                            self.setTextOffset(buff)
                        # text visibility
                        elif node.nodeName == 'textvisibility': self.setTextVisibility(bool(buff == 'True'))
                        # color
                        elif node.nodeName == 'color':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setColor(buff)
                        # selectedcolor
                        elif node.nodeName == 'selectedcolor':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setSelectedColor(buff)
                        # opacity
                        elif node.nodeName == 'opacity': self.setOpacity(float(buff))
                        # linewidth
                        elif node.nodeName == 'linewidth': self.setLineWidth(float(buff))
                        # handlesize
                        elif node.nodeName == 'handlesize': self.setHandleSize(float(buff))
                        # handlelinewidth
                        elif node.nodeName == 'handlelinewidth': self.setHandleLineWidth(float(buff))
                        # tolerance
                        elif node.nodeName == 'tolerance': self.setTolerance(int(buff))
                        # sphereradius
                        elif node.nodeName == 'sphereradius': self.setSphereRadius(float(buff))
                        # sphere visibility
                        elif node.nodeName == 'spherevisibility': self.setSphereVisibility(bool(buff == 'True'))
                        # interpolation
                        elif node.nodeName == 'interpolation': self.setInterpolation(int(buff))
                        # metallic
                        elif node.nodeName == 'metallic': self.setMetallic(float(buff))
                        # roughness
                        elif node.nodeName == 'roughness': self.setRoughness(float(buff))
                        # ambient
                        elif node.nodeName == 'ambient': self.setAmbient(float(buff))
                        # specular
                        elif node.nodeName == 'specular': self.setSpecular(float(buff))
                        # specularpower
                        elif node.nodeName == 'specularpower': self.setSpecularPower(float(buff))
        else: raise ValueError('Node name is not \'point\'.')

    def parseXML(self, doc: minidom.Document):
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                tool = doc.getElementsByTagName('point')
                if tool is not None: self.parseXMLNode(tool[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()

    def load(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
        else:
            raise IOError('no such file : {}'.format(filename))


class LineWidget(vtkLineWidget2, NamedWidget):
    """
        LineWidget

        Inheritance

            (vtkDistanceWidget, NamedWidget) -> LineWidget

        Class method

            str = getFileExt()
            str = getFilterExt()

        Public method

            updateContourActor()
            setName(str)
            setPrefix([str, str])
            [str, str] = getPrefix()
            setSuffix([str, str])
            [str, str] = getSuffix()
            setLegend([str, str])
            [str, str] = getLegend()
            [str, str] = getText()
            setOverlayEdgeVisibility(bool)
            bool = getVisibility()
            setTextVisibility(bool)
            setFontSize(float)
            float = getFontSize()
            setFontBold(bool)
            bool = getFontBold()
            setFontItalic(bool)
            bool = getFontItalic()
            setTextProperty(float, str, bool, bool)
            (float, str, bool, bool) = getTextProperty()
            bool = getTextVisibility()
            setTubeVisibility(bool)
            bool = getTubeVisibility()
            setColor((float, float, float))
            float, float, float = getColor()
            setSelectedColor((float, float, float))
            float, float, float = getSelectedColor()
            setPosition1((float, float, float))
            float, float, float = getPosition1()
            setPosition2((float, float, float))
            float, float, float = getPosition2()
            float, float, float = getVector(float)
            extendPosition1(float)
            extendPosition2(float)
            extendPosition1ToPlane(SliceViewWidget | vtkImageSlice | vtkPlane)
            extendPosition2ToPlane(SliceViewWidget | vtkImageSlice | vtkPlane)
            extendPosition1ToMeshSurface(SisypheMesh)
            extendPosition2ToMeshSurface(SisypheMesh)
            extendPosition1ToMeshCenterOfMass(SisypheMesh)
            extendPosition2ToMeshCenterOfMass(SisypheMesh)
            extendPosition1ToMeshCenter(SisypheMesh)
            extendPosition2ToMeshCenter(SisypheMesh)
            setTolerance(float)
            float = getTolerance()
            setHandleLineWidth(float)
            float = getHandleLineWidth()
            setLineWidth(float)
            float = getLineWidth()
            setHandleSize(float)
            float = getHandleSize()
            setPointSize(float)
            float = getPointSize()
            setTolerance(int)
            int = getTolerance()
            setOpacity(float)
            float = getOpacity()
            setRenderLineAsTube(bool)
            bool = getRenderLineAsTube()
            setInterpolation(int)
            int = getInterpolation()
            setTubeRadius(float)
            float = getTubeRadius()
            setTubeProperties(vtkProperty)
            vtkProperty = getTubeProperties()
            setMetallic(float)
            float = getMetallic()
            setRoughness(float)
            float = getRoughness()
            setAmbient(float)
            float = getAmbient()
            setSpecular(float)
            float = getSpecular()
            setSpecularPower(float)
            float = getSpecularPower()
            copyAttributesTo(LineWidget)
            copyAttributesFrom(LineWidget)
            LineWidget = deepCopy()
            float = getLength()
            [float, float, float] = getDistancesToPoint()
            [float, float, float] = getDistancesToHandleWidget()
            [float, , float, float, [float, float, float], [float, float, float]] = getDistancesToLine()
            [float, , float, float, [float, float, float], [float, float, float]] = getDistancesToLineWidget()
            [float, float, [float, float, float]] = getDistancesToPlane()
            createXML(minidom.Document, minidom.Element)
            parseXMLNode(minidom.Element)
            parseXML(minidom.Document)
            saveAs(str)
            load(str)
            setDefaultRepresentation()

            inherited NamedWidget methods
            inherited vtkLineWidget2 methods

        Revisions:

            07/09/2023  __init__() method bugfix, call setDefaultRepresentation() after vtkActor declaration
            08/09/2023  add setPrefix(), getPrefix(), setSuffix(), getSuffix(), getText() methods
                        add setFontFamily(), getFontFamily() methods
                        add font family update to copyAttributesTo() and copyAttributesFrom() methods
            10/09/2023  type hinting
            23/09/2023  setDefaultRepresentation() method,
                        replace vtkPointHandleRepresentation3D with vtkOrientedPolygonalHandleRepresentation3D
            28/09/2023  parseXMLNode() method bugfix
            03/10/2023  getDistancesToHandleWidget() method bugfix
                        getDistancesToLineWidget() method bugfix
            09/10/2023  setTrajectoryAngles() method bugfix
                        getTrajectoryAngles() method bugfix
                        extendPosition1ToMeshSurface() method bugfix
                        extendPosition2ToMeshSurface() method bugfix
    """

    _FILEEXT = '.xline'
    _DEFAULTTUBERADIUS = 2
    _DEFAULTTUBESIDES = 32

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Trajectory (*{})'.format(cls._FILEEXT)

    # Special methods

    def __init__(self, name: str, legend: list[str, str] | tuple[str, str] = ('Target', 'Entry')) -> None:
        vtkLineWidget2.__init__(self)
        NamedWidget.__init__(self, name)

        self.AddObserver('InteractionEvent', self._onInteractionEvent)
        self.AddObserver('EndInteractionEvent', self._onEndInteractionEvent)
        self.AddObserver('EnableEvent', self._onEnableEvent)
        self.AddObserver('DisableEvent', self._onDisableEvent)

        self._legend = list(legend)
        self._prefix = ['', '']
        self._suffix = ['', '']

        self._targetText = vtkBillboardTextActor3D()
        self._entryText = vtkBillboardTextActor3D()
        self._tube = vtkTubeFilter()
        self._tubeActor = vtkActor()
        self._cutter = vtkCutter()
        self._contourActor = vtkActor()
        self.setDefaultRepresentation()

        self._targetText.SetInput('{}\n{}'.format(legend[0], self.getName()))
        self._targetText.SetDisplayOffset(40, 0)
        self._targetText.GetTextProperty().SetFontFamilyAsString(_FFAMILY)
        self._targetText.GetTextProperty().FrameOff()
        self._targetText.GetTextProperty().ShadowOff()
        self._targetText.GetTextProperty().SetFontSize(_FSIZE)
        self._targetText.GetTextProperty().SetVerticalJustificationToCentered()
        self._targetText.GetTextProperty().SetBackgroundOpacity(0.0)

        self._entryText.SetInput('{}\n{}'.format(legend[1], self.getName()))
        self._entryText.GetTextProperty().SetFontFamilyAsString(_FFAMILY)
        self._entryText.SetDisplayOffset(40, 0)
        self._entryText.GetTextProperty().FrameOff()
        self._entryText.GetTextProperty().ShadowOff()
        self._entryText.GetTextProperty().SetFontSize(_FSIZE)
        self._entryText.GetTextProperty().SetVerticalJustificationToCentered()
        self._entryText.GetTextProperty().SetBackgroundOpacity(0.0)

        self._tube.SetRadius(self._DEFAULTTUBERADIUS)
        self._tube.SetNumberOfSides(self._DEFAULTTUBESIDES)
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(self._tube.GetOutputPort())

        self._tubeActor.SetMapper(mapper)
        self._tubeActor.GetProperty().SetInterpolationToPhong()
        self._tubeActor.GetProperty().SetRepresentationToSurface()
        self._tubeActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        self._tubeActor.GetProperty().SetOpacity(0.5 * _ALPHA)

        self._cutter = vtkCutter()
        self._cutter.SetInputConnection(self._tube.GetOutputPort())

        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(self._cutter.GetOutputPort())
        mapper.ScalarVisibilityOff()
        self._contourActor.SetMapper(mapper)
        r = self._contourActor.GetProperty()
        r.SetColor(1.0, 1.0, 1.0)
        r.SetEdgeColor(1.0, 1.0, 1.0)
        r.SetVertexColor(1.0, 1.0, 1.0)
        r.SetOpacity(_ALPHA)
        r.SetLineWidth(_HLWIDTH)
        r.EdgeVisibilityOff()
        r.VertexVisibilityOff()
        r.RenderLinesAsTubesOn()
        r.SetInterpolationToFlat()
        r.SetRepresentationToSurface()

    def __str__(self) -> str:
        buff = '{}:\n'.format(self.getName())
        p1 = self.getPosition1()
        p2 = self.getPosition2()
        buff += 'Position1: {:.1f} {:.1f} {:.1f}\n'.format(p1[0], p1[1], p1[2])
        buff += 'Position2: {:.1f} {:.1f} {:.1f}\n'.format(p2[0], p2[1], p2[2])
        buff += 'Length: {:.1f} mm\n'.format(self.getLength())
        r = self.getTrajectoryAngles()
        buff += 'Angles: X {:.1f}° Y {:.1f}° \n'.format(r[0], r[1])
        buff += 'Prefix: {}\n'.format(self.getPrefix())
        buff += 'Suffix: {}\n'.format(self.getSuffix())
        buff += 'Legend: {}\n'.format(self.getLegend())
        buff += 'Color: {}\n'.format(self.getColor())
        buff += 'Selected Color: {}\n'.format(self.getColor())
        buff += 'Opacity: {:.2f}\n'.format(self.getOpacity())
        buff += 'Tolerance: {}\n'.format(self.getTolerance())
        buff += 'Point size: {}\n'.format(self.getPointSize())
        buff += 'Line width: {}\n'.format(self.getLineWidth())
        buff += 'Handle size: {}\n'.format(self.getHandleSize())
        buff += 'Handle line width: {}\n'.format(self.getHandleLineWidth())
        buff += 'Font:\n'
        buff += '\tFamily: {}\n'.format(self.getFontFamily())
        buff += '\tSize: {}\n'.format(self.getFontSize())
        buff += '\tBold: {}\n'.format(self.getFontBold())
        buff += '\tItalic: {}\n'.format(self.getFontItalic())
        buff += '\tVisibility: {}\n'.format(self.getTextVisibility())
        buff += '\tOffset: {}\n'.format(self.getTextOffset())
        buff += 'Safety:\n'
        buff += '\tRadius: {}\n'.format(self.getTubeRadius())
        buff += '\tVisibility: {}\n'.format(self.getTubeVisibility())
        return buff

    # Private event methods

    def _onInteractionEvent(self, widget, event) -> None:
        p1 = self.GetLineRepresentation().GetPoint1WorldPosition()
        p2 = self.GetLineRepresentation().GetPoint2WorldPosition()
        self._entryText.SetPosition(p1)
        self._targetText.SetPosition(p2)
        data = vtkPolyData()
        self.GetLineRepresentation().GetPolyData(data)
        self._tube.SetInputData(data)
        self._tube.Update()

    def _onEndInteractionEvent(self, widget, event) -> None:
        pass

    def _onEnableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        props = renderer.GetViewProps()
        for i in range(props.GetNumberOfItems()):
            prop = props.GetItemAsObject(i)
            if isinstance(prop, vtkImageSlice):
                self._cutter.SetCutFunction(prop.GetMapper().GetSlicePlane())
                break
        renderer.AddActor(self._targetText)
        renderer.AddActor(self._entryText)
        renderer.AddActor(self._tubeActor)
        renderer.AddActor(self._contourActor)
        self._targetText.SetVisibility(True)
        self._entryText.SetVisibility(True)
        self._contourActor.SetVisibility(True)
        self._tubeActor.SetVisibility(False)
        p1 = self.GetLineRepresentation().GetPoint1WorldPosition()
        p2 = self.GetLineRepresentation().GetPoint2WorldPosition()
        self._entryText.SetPosition(p1)
        self._targetText.SetPosition(p2)
        data = vtkPolyData()
        self.GetLineRepresentation().GetPolyData(data)
        self._tube.SetInputData(data)
        self._tube.Update()
        self._cutter.Update()

    def _onDisableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        renderer.RemoveActor(self._targetText)
        renderer.RemoveActor(self._entryText)
        renderer.RemoveActor(self._tubeActor)
        renderer.RemoveActor(self._contourActor)
        del self._targetText
        del self._entryText
        del self._tubeActor
        del self._contourActor

    def _setText(self, txt: list[str, str]) -> None:
        self._entryText.SetInput(txt[0])
        self._targetText.SetInput(txt[1])

    # Public methods

    def updateContourActor(self, plane: vtkPlane) -> None:
        if isinstance(plane, vtkPlane):
            plane2 = vtkPlane()
            plane2.SetNormal(plane.GetNormal())
            plane2.SetOrigin(plane.GetOrigin())
            plane2.Push(0.5)
            self._cutter.SetCutFunction(plane2)
            self._cutter.Update()
        else: raise TypeError('parameter type {} is not vtkPlane.'.format(type(plane)))

    def setName(self, name: str) -> None:
        super().setName(name)
        txt = '{}\n{}{}{}'.format(self._legend[0],
                                  self._prefix[0],
                                  self.getName(),
                                  self._suffix[0])
        self._targetText.SetInput(txt)
        txt = '{}\n{}{}{}'.format(self._legend[1],
                                  self._prefix[1],
                                  self.getName(),
                                  self._suffix[1])
        self._entryText.SetInput(txt)

    def setPrefix(self, txt: list[str, str] = ('', '')) -> None:
        target = txt[0]
        entry = txt[1]
        if target != '':
            if target[-1] != ' ': target += ' '
        if entry != '':
            if entry[-1] != ' ': entry += ' '
        self._prefix = [target, entry]
        txt = '{}\n{}{}{}'.format(self._legend[0],
                                  self._prefix[0],
                                  self.getName(),
                                  self._suffix[0])
        self._targetText.SetInput(txt)
        txt = '{}\n{}{}{}'.format(self._legend[1],
                                  self._prefix[1],
                                  self.getName(),
                                  self._suffix[1])
        self._entryText.SetInput(txt)

    def getPrefix(self) -> list[str, str]:
        return self._prefix

    def setSuffix(self, txt: list[str, str] = ('', '')) -> None:
        target = txt[0]
        entry = txt[1]
        if target != '':
            if target[-1] != ' ': target += ' '
        if entry != '':
            if entry[-1] != ' ': entry += ' '
        self._suffix = [target, entry]
        txt = '{}\n{}{}{}'.format(self._legend[0],
                                  self._prefix[0],
                                  self.getName(),
                                  self._suffix[0])
        self._targetText.SetInput(txt)
        txt = '{}\n{}{}{}'.format(self._legend[1],
                                  self._prefix[1],
                                  self.getName(),
                                  self._suffix[1])
        self._entryText.SetInput(txt)

    def getSuffix(self) -> list[str, str]:
        return self._suffix

    def setLegend(self, txt: list[str, str] = ('', '')) -> None:
        self._legend = txt
        txt = '{}\n{}{}{}'.format(self._legend[0],
                                  self._prefix[0],
                                  self.getName(),
                                  self._suffix[0])
        self._targetText.SetInput(txt)
        txt = '{}\n{}{}{}'.format(self._legend[1],
                                  self._prefix[1],
                                  self.getName(),
                                  self._suffix[1])
        self._entryText.SetInput(txt)

    def getLegend(self) -> list[str, str]:
        return self._legend

    def getText(self) -> list[str, str]:
        return [self._entryText.GetInput(),
                self._targetText.GetInput()]

    def setFontSize(self, size: int) -> None:
        if isinstance(size, int):
            self._targetText.GetTextProperty().SetFontSize(size)
            self._entryText.GetTextProperty().SetFontSize(size)
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getFontSize(self) -> int:
        return self._targetText.GetTextProperty().GetFontSize()

    def setFontBold(self, v: bool) -> None:
        if isinstance(v, bool):
            self._targetText.GetTextProperty().SetBold(v)
            self._entryText.GetTextProperty().SetBold(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontBold(self) -> bool:
        return self._targetText.GetTextProperty().GetBold() > 0

    def setFontItalic(self, v: bool) -> None:
        if isinstance(v, bool):
            self._targetText.GetTextProperty().SetItalic(v)
            self._entryText.GetTextProperty().SetItalic(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontItalic(self) -> bool:
        return self._targetText.GetTextProperty().GetItalic() > 0

    def setFontFamily(self, fontname: str = _FFAMILY) -> None:
        r1 = self._targetText.GetTextProperty()
        r2 = self._entryText.GetTextProperty()
        if fontname in ('Arial', 'Courier', 'Times'):
            r1.SetFontFamilyAsString(fontname)
            r2.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r1.SetFontFamily(VTK_FONT_FILE)
                r2.SetFontFamily(VTK_FONT_FILE)
                r1.SetFontFile(fontname)
                r2.SetFontFile(fontname)
            else:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')

    def getFontFamily(self) -> str:
        return self._targetText.GetTextProperty().GetFontFamilyAsString()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        r1 = self._targetText.GetTextProperty()
        r2 = self._entryText.GetTextProperty()
        r1.SetBold(bold)
        r2.SetBold(bold)
        r1.SetItalic(italic)
        r2.SetItalic(italic)
        r1.ShadowOff()
        r2.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r1.SetFontFamilyAsString(fontname)
            r2.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname):
                r1.SetFontFamily(VTK_FONT_FILE)
                r2.SetFontFamily(VTK_FONT_FILE)
                r1.SetFontFile(fontname)
                r2.SetFontFile(fontname)
            else:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        r = self._targetText.GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            r = self.GetLineRepresentation()
            if not v:
                self._alpha = r.GetLineProperty().GetOpacity()
                r.GetEndPointProperty().SetOpacity(0.0)
                r.GetSelectedEndPointProperty().SetOpacity(0.0)
                r.GetEndPoint2Property().SetOpacity(0.0)
                r.GetSelectedEndPoint2Property().SetOpacity(0.0)
                r.GetLineProperty().SetOpacity(0.0)
                r.GetSelectedLineProperty().SetOpacity(0.0)
            else:
                r.GetEndPointProperty().SetOpacity(self._alpha)
                r.GetSelectedEndPointProperty().SetOpacity(self._alpha)
                r.GetEndPoint2Property().SetOpacity(self._alpha)
                r.GetSelectedEndPoint2Property().SetOpacity(self._alpha)
                r.GetLineProperty().SetOpacity(self._alpha)
                r.GetSelectedLineProperty().SetOpacity(self._alpha)
            self._targetText.SetVisibility(v)
            self._entryText.SetVisibility(v)
            if self.isVolumeDisplay():
                self._tubeActor.SetVisibility(v)
                self._contourActor.SetVisibility(False)
            else:
                self._tubeActor.SetVisibility(False)
                self._contourActor.SetVisibility(v)
            r = self.GetCurrentRenderer()
            if r is not None:
                r = r.GetRenderWindow()
                if r is not None: r.Render()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        return self._targetText.GetVisibility() > 0

    def setTextOffset(self, r: tuple[int, int] | list[int, int]) -> None:
        self._targetText.SetDisplayOffset(r[0], r[1])
        self._entryText.SetDisplayOffset(r[0], r[1])

    def getTextOffset(self) -> tuple[int, int]:
        return self._targetText.GetDisplayOffset()

    def setTextVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._targetText.SetVisibility(v)
            self._entryText.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextVisibility(self) -> bool:
        return self._targetText.GetVisibility() > 0

    def setTubeVisibility(self, v: bool):
        if isinstance(v, bool):
            if self.isVolumeDisplay(): self._tubeActor.SetVisibility(v)
            else:  self._tubeActor.SetVisibility(False)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTubeVisibility(self) -> bool:
        return self._tubeActor.GetVisibility() > 0 or \
            self._contourActor.GetVisibility() > 0

    def setColor(self, c: vectorFloat3) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                if all([0.0 <= i <= 1.0 for i in c]):
                    r = self.GetLineRepresentation()
                    r.GetLineProperty().SetColor(c[0], c[1], c[2])
                    r.GetEndPointProperty().SetColor(c[0], c[1], c[2])
                    r.GetEndPoint2Property().SetColor(c[0], c[1], c[2])
                    r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
                    r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
                    r.GetLineHandleRepresentation().GetProperty().SetColor(c[0], c[1], c[2])
                    self._targetText.GetTextProperty().SetColor(c[0], c[1], c[2])
                    self._entryText.GetTextProperty().SetColor(c[0], c[1], c[2])
                    self._tubeActor.GetProperty().SetColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetEdgeColor(c[0], c[1], c[2])
                    self._contourActor.GetProperty().SetVertexColor(c[0], c[1], c[2])
                else: raise ValueError('parameter value is not between 0.0 and 1.0.')
            else: raise ValueError('list length {} is not 3.'.format(len(c)))
        else: raise TypeError('parameter functype {} is not list or tuple.'.format(type(c)))

    def getColor(self) -> vectorFloat3:
        return self.GetLineRepresentation().GetLineProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                if all([0.0 <= i <= 1.0 for i in c]):
                    r = self.GetLineRepresentation()
                    r.GetSelectedLineProperty().SetColor(c[0], c[1], c[2])
                    r.GetSelectedEndPointProperty().SetColor(c[0], c[1], c[2])
                    r.GetSelectedEndPoint2Property().SetColor(c[0], c[1], c[2])
                    r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
                    r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
                    r.GetLineHandleRepresentation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
                else: raise ValueError('parameter value is not between 0.0 and 1.0.')
            else: raise ValueError('list length {} is not 3.'.format(len(c)))
        else: raise TypeError('parameter functype {} is not list or tuple.'.format(type(c)))

    def getSelectedColor(self) -> vectorFloat3:
        return self.GetLineRepresentation().GetSelectedLineProperty().GetColor()

    def setPosition1(self, p: vectorFloat3) -> None:
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, float) for i in p]):
                    r = self.GetLineRepresentation()
                    r.SetPoint1WorldPosition(p)
                    self._entryText.SetPosition(p)
                    data = vtkPolyData()
                    r.GetPolyData(data)
                    self._tube.SetInputData(data)
                    self._tube.Update()
                else: raise TypeError('parameter type is not float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition1(self) -> vectorFloat3:
        return self.GetLineRepresentation().GetPoint1WorldPosition()

    def setPosition2(self, p: vectorFloat3) -> None:
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, float) for i in p]):
                    r = self.GetLineRepresentation()
                    r.SetPoint2WorldPosition(p)
                    self._targetText.SetPosition(p)
                    data = vtkPolyData()
                    r.GetPolyData(data)
                    self._tube.SetInputData(data)
                    self._tube.Update()
                else: raise TypeError('parameter type is not float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition2(self) -> vectorFloat3:
        return self.GetLineRepresentation().GetPoint2WorldPosition()

    def getVector(self, length: float = 1.0) -> vectorFloat3:
        r = self.GetLineRepresentation()
        p1 = r.GetPoint1WorldPosition()
        p2 = r.GetPoint2WorldPosition()
        v = list()
        v.append((p1[0] - p2[0]) * length)
        v.append((p1[1] - p2[1]) * length)
        v.append((p1[2] - p2[2]) * length)
        return v

    def setTrajectoryAngles(self, r: vectorFloat2, length: float = 50.0, deg: bool = True) -> None:
        trf = sc.sisypheTransform.SisypheTransform()
        trf.setCenter((0.0, 0.0, 0.0))
        trf.setTranslations((0.0, 0.0, 0.0))
        trf.setRotations((r[0], r[1], 0.0), deg=deg)
        entry = list(trf.applyToPoint([0.0, 0.0, length]))
        target = self.getPosition2()
        entry[0] += target[0]
        entry[1] += target[1]
        entry[2] += target[2]
        self.setPosition1(entry)

    def getTrajectoryAngles(self, deg: bool = True) -> vectorFloat2:
        r = [0.0, 0.0]
        entry = self.getPosition1()
        target = self.getPosition2()
        length = self.getLength()
        """
            Sagittal angle, x rotation
            -180.0 to +180.0
        """
        o = entry[1] - target[1]  # ∆y
        a = entry[2] - target[2]  # ∆z
        r[0] = -atan2(o, a)
        if deg: r[0] = degrees(r[0])
        """
            Coronal angle, y rotation
            -90.0 to +90.0
        """
        o = entry[0] - target[0]  # ∆x
        r[1] = (pi / 2) - acos(o / length)
        if deg: r[1] = degrees(r[1])
        return r

    def extendPosition1(self, mm: float) -> None:
        """
            Extend/reduce LineWidget length on the point1 side
            mm  float, - reduce and + extend in mm
        """
        if isinstance(mm, float):
            r = self.GetLineRepresentation()
            p1 = r.GetPoint1WorldPosition()
            p2 = r.GetPoint2WorldPosition()
            n = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
            v = [(p1[i] - p2[i]) / n for i in range(3)]
            p = [p1[i] + v[i] * mm for i in range(3)]
            self.setPosition1(p)
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def extendPosition2(self, mm: float) -> None:
        """
            Extend/reduce LineWidget length on the point2 side
            mm  float, - reduce and + extend in mm
        """
        if isinstance(mm, float):
            r = self.GetLineRepresentation()
            p1 = r.GetPoint1WorldPosition()
            p2 = r.GetPoint2WorldPosition()
            n = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
            v = [(p2[i] - p1[i]) / n for i in range(3)]
            p = [p2[i] + v[i] * mm for i in range(3)]
            self.setPosition2(p)
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def extendPosition1ToPlane(self, plane: vtkPlane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget) -> None:
        """
            Move LineWidget position1 to intersection of line and plane
            plane   SliceViewWidget | vtkImageSlice | vtkPlane
        """
        if isinstance(plane, sw.sliceViewWidgets.SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            t = vtkmutable(0.0)
            p = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            plane.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, p)
            self.setPosition1(p)

    def extendPosition2ToPlane(self, plane: vtkPlane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget) -> None:
        """
            Move LineWidget position2 to intersection of line and plane
            plane   SliceViewWidget | vtkImageSlice | vtkPlane
        """
        if isinstance(plane, sw.sliceViewWidgets.SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            t = vtkmutable(0.0)
            p = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            plane.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, p)
            self.setPosition2(p)

    def extendPosition1ToMeshSurface(self, mesh: sc.sisypheMesh.SisypheMesh) -> int:
        if isinstance(mesh, sc.sisypheMesh.SisypheMesh):
            f = vtkOBBTree()
            f.SetDataSet(mesh.getPolyData())
            f.BuildLocator()
            ps = vtkPoints()
            r = self.GetLineRepresentation()
            p = r.GetPoint1WorldPosition()
            v = self.getVector(200.0)
            p1 = [p[0] + v[0],
                  p[1] + v[1],
                  p[2] + v[2]]
            p2 = [p[0] - v[0],
                  p[1] - v[1],
                  p[2] - v[2]]
            inter = f.IntersectWithLine(p1, p2, ps, None)
            print(inter)
            if inter != 0:
                n = ps.GetNumberOfPoints()
                print(n)
                if n > 0:
                    d = list()
                    for i in range(n):
                        pr = ps.GetPoint(i)
                        d.append(sqrt((p[0] - pr[0])**2 + (p[1] - pr[1])**2 + (p[2] - pr[2])**2))
                    self.setPosition1(ps.GetPoint(d.index(min(d))))
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshSurface(self, mesh: sc.sisypheMesh.SisypheMesh) -> int:
        if isinstance(mesh, sc.sisypheMesh.SisypheMesh):
            f = vtkOBBTree()
            f.SetDataSet(mesh.getPolyData())
            f.BuildLocator()
            ps = vtkPoints()
            r = self.GetLineRepresentation()
            p = r.GetPoint2WorldPosition()
            v = self.getVector(200.0)
            p1 = [p[0] + v[0],
                  p[1] + v[1],
                  p[2] + v[2]]
            p2 = [p[0] - v[0],
                  p[1] - v[1],
                  p[2] - v[2]]
            inter = f.IntersectWithLine(p1, p2, ps, None)
            if inter != 0:
                n = ps.GetNumberOfPoints()
                if n > 0:
                    d = list()
                    for i in range(n):
                        pr = ps.GetPoint(i)
                        d.append(sqrt((p[0] - pr[0])**2 + (p[1] - pr[1])**2 + (p[2] - pr[2])**2))
                    self.setPosition2(ps.getPoint(d.index(min(d))))
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition1ToMeshCenterOfMass(self, mesh: sc.sisypheMesh.SisypheMesh) -> None:
        if isinstance(mesh,  sc.sisypheMesh.SisypheMesh):
            p = mesh.getCenterOfMass()
            self.setPosition1(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshCenterOfMass(self, mesh: sc.sisypheMesh.SisypheMesh) -> None:
        if isinstance(mesh,  sc.sisypheMesh.SisypheMesh):
            p = mesh.getCenterOfMass()
            self.setPosition2(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition1ToMeshCenter(self, mesh: sc.sisypheMesh.SisypheMesh) -> None:
        if isinstance(mesh,  sc.sisypheMesh.SisypheMesh):
            p = mesh.getActor().GetCenter()
            self.setPosition1(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshCenter(self, mesh: sc.sisypheMesh.SisypheMesh) -> None:
        if isinstance(mesh,  sc.sisypheMesh.SisypheMesh):
            p = mesh.getActor().GetCenter()
            self.setPosition2(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def setLineWidth(self, width: float) -> None:
        if isinstance(width, float):
            r = self.GetLineRepresentation()
            r.GetLineProperty().SetLineWidth(width)
            r.GetSelectedLineProperty().SetLineWidth(width)
        else: raise TypeError('parameter type {} is not float'.format(type(width)))

    def getLineWidth(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetLineWidth()

    def setPointSize(self, size: float) -> None:
        if isinstance(size, float):
            r = self.GetLineRepresentation()
            r.GetEndPointProperty().SetPointSize(size)
            r.GetEndPoint2Property().SetPointSize(size)
            r.GetSelectedEndPointProperty().SetPointSize(size)
            r.GetSelectedEndPoint2Property().SetPointSize(size)
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getPointSize(self) -> float:
        return self.GetLineRepresentation().GetEndPointProperty().GetPointSize()

    def setHandleSize(self, size: float) -> None:
        if isinstance(size, float):
            r = self.GetLineRepresentation()
            r.GetPoint1Representation().SetHandleSize(size)
            r.GetPoint2Representation().SetHandleSize(size)
            r.GetLineHandleRepresentation().SetHandleSize(size)
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getHandleSize(self) -> float:
        return self.GetLineRepresentation().GetLineHandleRepresentation().GetHandleSize()

    def setHandleLineWidth(self, size: float) -> None:
        if isinstance(size, float):
            r = self.GetLineRepresentation()
            r.GetPoint1Representation().GetProperty().SetLineWidth(size)
            r.GetPoint2Representation().GetProperty().SetLineWidth(size)
            r.GetLineHandleRepresentation().GetProperty().SetLineWidth(size)
            r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(size)
            r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(size)
            r.GetLineHandleRepresentation().GetSelectedProperty().SetLineWidth(size)
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getHandleLineWidth(self) -> float:
        return self.GetLineRepresentation().GetLineHandleRepresentation().GetProperty().GetLineWidth()

    def setOpacity(self, alpha: float) -> None:
        if isinstance(alpha, float):
            if 0.0 <= alpha <= 1.0:
                r = self.GetLineRepresentation()
                r.GetEndPointProperty().SetOpacity(alpha)
                r.GetSelectedEndPointProperty().SetOpacity(alpha)
                r.GetEndPoint2Property().SetOpacity(alpha)
                r.GetSelectedEndPoint2Property().SetOpacity(alpha)
                r.GetLineProperty().SetOpacity(alpha)
                r.GetSelectedLineProperty().SetOpacity(alpha)
                self._targetText.GetTextProperty().SetOpacity(alpha)
                self._entryText.GetTextProperty().SetOpacity(alpha)
                self._contourActor.GetProperty().SetOpacity(alpha)
                self._tubeActor.GetProperty().SetOpacity(0.5 * alpha)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(alpha))
        else: raise TypeError('parameter type {} is not float'.format(type(alpha)))

    def getOpacity(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetOpacity()

    def setTolerance(self, tol: int) -> None:
        if isinstance(tol, int):
            self.GetLineRepresentation().SetTolerance(tol)
        else: raise TypeError('parameter type {} is not int'.format(type(tol)))

    def getTolerance(self) -> int:
        return self.GetLineRepresentation().GetTolerance()

    def setRenderLineAsTube(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetLineRepresentation().GetLineProperty().SetRenderLinesAsTubes(v)
            self.GetLineRepresentation().GetSelectedLineProperty().SetRenderLinesAsTubes(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(render)))

    def getRenderLineAsTube(self) -> bool:
        return self.GetLineRepresentation().GetLineProperty().GetRenderLinesAsTubes() > 0

    def setRenderPointsAsSpheres(self, v: bool) -> None:
        if isinstance(v, bool):
            self.GetLineRepresentation().GetEndPointProperty().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetSelectedEndPointProperty().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetEndPoint2Property().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetSelectedEndPoint2Property().SetRenderPointsAsSpheres(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(render)))

    def getRenderPointsAsSpheres(self) -> bool:
        return self.GetLineRepresentation().GetEndPointProperty().GetRenderPointsAsSpheres() > 0

    def setInterpolation(self, inter: int) -> None:
        if isinstance(inter, int):
            r = self.GetLineRepresentation()
            r.GetLineProperty().SetInterpolation(inter)
            r.GetEndPointProperty().SetInterpolation(inter)
            r.GetEndPoint2Property().SetInterpolation(inter)
            r.GetSelectedEndPointProperty().SetInterpolation(inter)
            r.GetSelectedEndPoint2Property().SetInterpolation(inter)
            r.GetSelectedLineProperty().SetInterpolation(inter)
            self._tubeActor.GetProperty().SetInterpolation(inter)
        else: raise TypeError('parameter functype {} is not int.'.format(type(inter)))

    def getInterpolation(self) -> int:
        return self.GetLineRepresentation().GetLineProperty().GetInterpolation()

    def setTubeRadius(self, radius: float) -> None:
        if isinstance(radius, float):
            self._tube.SetRadius(radius)
            self._tube.Update()
        else: raise TypeError('parameter type {} is not float.'.format(type(radius)))

    def getTubeRadius(self) -> float:
        return self._tube.GetRadius()

    def setMetallic(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                r = self.GetLineRepresentation()
                r.GetLineProperty().SetMetallic(v)
                r.GetEndPointProperty().SetMetallic(v)
                r.GetEndPoint2Property().SetMetallic(v)
                r.GetSelectedEndPointProperty().SetMetallic(v)
                r.GetSelectedEndPoint2Property().SetMetallic(v)
                r.GetSelectedLineProperty().SetMetallic(v)
                self._tubeActor.GetProperty().SetMetallic(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getMetallic(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetMetallic()

    def setRoughness(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                r = self.GetLineRepresentation()
                r.GetLineProperty().SetRoughness(v)
                r.GetEndPointProperty().SetRoughness(v)
                r.GetEndPoint2Property().SetRoughness(v)
                r.GetSelectedEndPointProperty().SetRoughness(v)
                r.GetSelectedEndPoint2Property().SetRoughness(v)
                r.GetSelectedLineProperty().SetRoughness(v)
                self._tubeActor.GetProperty().SetRoughness(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getRoughness(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetRoughness()

    def setAmbient(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                r = self.GetLineRepresentation()
                r.GetLineProperty().SetAmbient(v)
                r.GetEndPointProperty().SetAmbient(v)
                r.GetEndPoint2Property().SetAmbient(v)
                r.GetSelectedEndPointProperty().SetAmbient(v)
                r.GetSelectedEndPoint2Property().SetAmbient(v)
                r.GetSelectedLineProperty().SetAmbient(v)
                self._tubeActor.GetProperty().SetAmbient(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getAmbient(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetAmbient()

    def setSpecular(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                r = self.GetLineRepresentation()
                r.GetLineProperty().SetSpecular(v)
                r.GetEndPointProperty().SetSpecular(v)
                r.GetEndPoint2Property().SetSpecular(v)
                r.GetSelectedEndPointProperty().SetSpecular(v)
                r.GetSelectedEndPoint2Property().SetSpecular(v)
                r.GetSelectedLineProperty().SetSpecular(v)
                self._tubeActor.GetProperty().SetSpecular(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecular(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetSpecular()

    def setSpecularPower(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                r = self.GetLineRepresentation()
                r.GetLineProperty().SetSpecularPower(v)
                r.GetEndPointProperty().SetSpecularPower(v)
                r.GetEndPoint2Property().SetSpecularPower(v)
                r.GetSelectedEndPointProperty().SetSpecularPower(v)
                r.GetSelectedEndPoint2Property().SetSpecularPower(v)
                r.GetSelectedLineProperty().SetSpecularPower(v)
                self._tubeActor.GetProperty().SetSpecularPower(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecularPower(self) -> float:
        return self.GetLineRepresentation().GetLineProperty().GetSpecularPower()

    def setTubeProperties(self, p: vtkProperty) -> None:
        if isinstance(p, vtkProperty): self._tubeActor.SetProperty(p)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(p)))

    def getTubeProperties(self) -> vtkProperty:
        return self._tubeActor.GetProperty()

    def deepCopy(self) -> LineWidget:
        r = vtkLineRepresentation()
        r.GetPoint1Representation().DeepCopy(self.GetLineRepresentation().GetPoint1Representation())
        r.GetPoint2Representation().DeepCopy(self.GetLineRepresentation().GetPoint2Representation())
        r.GetLineHandleRepresentation().DeepCopy(self.GetLineRepresentation().GetLineHandleRepresentation())
        r.GetEndPointProperty().DeepCopy(self.GetLineRepresentation().GetEndPointProperty())
        r.GetSelectedEndPointProperty().DeepCopy(self.GetLineRepresentation().GetSelectedEndPointProperty())
        r.GetEndPoint2Property().DeepCopy(self.GetLineRepresentation().GetEndPoint2Property())
        r.GetSelectedEndPoint2Property().DeepCopy(self.GetLineRepresentation().GetSelectedEndPoint2Property())
        r.GetLineProperty().DeepCopy(self.GetLineRepresentation().GetLineProperty())
        r.GetSelectedLineProperty().DeepCopy(self.GetLineRepresentation().GetSelectedLineProperty())
        r.SetTolerance(self.GetLineRepresentation().GetTolerance())
        r.SetLineColor(self.GetLineRepresentation().GetLineColor())
        r.SetPoint1WorldPosition(self.GetLineRepresentation().GetPoint1WorldPosition())
        r.SetPoint2WorldPosition(self.GetLineRepresentation().GetPoint2WorldPosition())
        widget = LineWidget(self.getName())
        widget.SetRepresentation(r)
        widget.copyAttributesFrom(self)
        return widget

    def copyAttributesTo(self, tool: LineWidget) -> None:
        if isinstance(tool, LineWidget):
            tool._setText(self.getText())
            tool.setFontSize(self.getFontSize())
            tool.setFontBold(self.getFontBold())
            tool.setFontItalic(self.getFontItalic())
            tool.setFontFamily(self.getFontFamily())
            tool.setVisibility(self.getVisibility())
            tool.setTextVisibility(self.getTextVisibility())
            tool.setTextOffset(self.getTextOffset())
            tool.setColor(self.getColor())
            tool.setSelectedColor(self.getSelectedColor())
            tool.setOpacity(self.getOpacity())
            tool.setPointSize(self.getPointSize())
            tool.setLineWidth(self.getLineWidth())
            tool.setHandleSize(self.getHandleSize())
            tool.setRenderPointsAsSpheres(self.getRenderPointsAsSpheres())
            tool.setRenderLineAsTube(self.getRenderLineAsTube())
            tool.setInterpolation(self.getInterpolation())
            tool.setTubeRadius(self.getTubeRadius())
            tool.setTubeVisibility(self.getTubeVisibility())
            tool.setMetallic(self.getMetallic())
            tool.setRoughness(self.getRoughness())
            tool.setAmbient(self.getAmbient())
            tool.setSpecular(self.getSpecular())
            tool.setSpecularPower(self.getSpecularPower())
            tool.setTolerance(self.getTolerance())
        else: raise TypeError('parameter type {} is not LineWidget.'.format(type(tool)))

    def copyAttributesFrom(self, tool: LineWidget) -> None:
        if isinstance(tool, LineWidget):
            self._setText(tool.getText())
            self.setFontSize(tool.getFontSize())
            self.setFontBold(tool.getFontBold())
            self.setFontItalic(tool.getFontItalic())
            self.setFontFamily(tool.getFontFamily())
            self.setVisibility(tool.getVisibility())
            self.setTextVisibility(tool.getTextVisibility())
            self.setTextOffset(tool.getTextOffset())
            self.setColor(tool.getColor())
            self.setSelectedColor(tool.getSelectedColor())
            self.setOpacity(tool.getOpacity())
            self.setPointSize(tool.getPointSize())
            self.setLineWidth(tool.getLineWidth())
            self.setHandleSize(tool.getHandleSize())
            self.setRenderPointsAsSpheres(tool.getRenderPointsAsSpheres())
            self.setRenderLineAsTube(tool.getRenderLineAsTube())
            self.setInterpolation(tool.getInterpolation())
            self.setTubeRadius(tool.getTubeRadius())
            self.setTubeVisibility(tool.getTubeVisibility())
            self.setMetallic(tool.getMetallic())
            self.setRoughness(tool.getRoughness())
            self.setAmbient(tool.getAmbient())
            self.setSpecular(tool.getSpecular())
            self.setSpecularPower(tool.getSpecularPower())
            self.setTolerance(tool.getTolerance())
        else: raise TypeError('parameter type {} is not LineWidget.'.format(type(tool)))

    def setDefaultRepresentation(self) -> None:
        self.CreateDefaultRepresentation()
        r = self.GetLineRepresentation()
        # Point1
        p = r.GetEndPointProperty()
        p.RenderPointsAsSpheresOn()
        p.SetInterpolationToPhong()
        p = r.GetSelectedEndPointProperty()
        p.RenderPointsAsSpheresOn()
        p.SetInterpolationToFlat()
        # Point2
        p = r.GetEndPoint2Property()
        p.RenderPointsAsSpheresOn()
        p.SetInterpolationToPhong()
        p = r.GetSelectedEndPoint2Property()
        p.RenderPointsAsSpheresOn()
        p.SetInterpolationToFlat()
        # Line
        p = r.GetLineProperty()
        p.RenderLinesAsTubesOn()
        p.SetInterpolationToPhong()
        p = r.GetSelectedLineProperty()
        p.RenderLinesAsTubesOn()
        p.SetInterpolationToFlat()
        # Widget
        self.setTextProperty(_FFAMILY)
        self.setPointSize(_PSIZE)
        self.setLineWidth(_LWIDTH)
        self.setHandleSize(_HSIZE)
        self.setHandleLineWidth(_HLWIDTH)
        self.setColor(_DEFAULTCOLOR)
        self.setSelectedColor(_DEFAULTSCOLOR)
        self.setTolerance(_TOL)
        self.setOpacity(_ALPHA)

    # Various distance methods

    def getLength(self) -> float:
        p1 = self.GetLineRepresentation().GetPoint1WorldPosition()
        p2 = self.GetLineRepresentation().GetPoint2WorldPosition()
        return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

    def getDistancesToPoint(self, p: vectorFloat3) -> vectorFloat3:
        """
            p       [float, float, float]
            return  [float, float, float]
                    float, distance between parameter point and self LineWidget point1
                    float, distance between parameter point and self LineWidget point2
                    float, distance between parameter point and self LineWidget line
        """
        r = list()
        p1 = self.getPosition1()
        p2 = self.getPosition2()
        r.append(sqrt((p1[0] - p[0])**2 + (p1[1] - p[1])**2 + (p1[2] - p[2])**2))
        r.append(sqrt((p2[0] - p[0])**2 + (p2[1] - p[1])**2 + (p2[2] - p[2])**2))
        line = vtkLine()
        r.append(sqrt(line.DistanceToLine(p, p1, p2)))
        return r

    def getDistancesToHandleWidget(self, hw: HandleWidget) -> vectorFloat3:
        """
            hw       HandleWidget
            return  [float, , float, float]
                    float, distance between parameter HandleWidget position and self LineWidget point1
                    float, distance between parameter HandleWidget position and self LineWidget point2
                    float, distance between parameter HandleWidget position and self LineWidget line
        """
        if isinstance(hw, HandleWidget):
            return self.getDistancesToPoint(hw.getPosition())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(hw)))

    def getLineToLineDistance(self, p1: vectorFloat3, p2: vectorFloat3) -> float:
        """
            p1, p2  [float, float, float], 2 points to define line segment
            return  float, perpendicular distance metric between two line segments
        """
        sp1 = self.getPosition1()
        sp2 = self.getPosition2()
        return lee_perpendicular_distance(sp1, sp2, p1, p2)

    def getDistancesToLine(self, p1: vectorFloat3, p2: vectorFloat3) -> list[float, float, float, float, float, float, float, vectorFloat3, vectorFloat3]:
        """
            p1, p2  [float, float, float], 2 points to define line equation
            return  [float, , float, float, [float, float, float], [float, float, float]]
                    float, distance between line parameter and self LineWidget point1
                    float, distance between line parameter and self LineWidget point2
                    float, distance between line parameter and self LineWidget line
                    float, distance between point1 parameter and self LineWidget point1
                    float, distance between point1 parameter and self LineWidget point2
                    float, distance between point2 parameter and self LineWidget point1
                    float, distance between point2 parameter and self LineWidget point2
                    [float, float, float], coordinates of the closest point on line parameter
                    [float, float, float], closest point coordinate on self LineWidget line
        """
        r = list()
        line = vtkLine()
        sp1 = self.getPosition1()
        sp2 = self.getPosition2()
        # r[0], distance between line parameter and self LineWidget point1
        r.append(sqrt(line.DistanceToLine(sp1, p1, p2)))
        # r[1], distance between line parameter and self LineWidget point2
        r.append(sqrt(line.DistanceToLine(sp2, p1, p2)))
        cp1 = [0.0, 0.0, 0.0]
        cp2 = [0.0, 0.0, 0.0]
        t1 = vtkmutable(0.0)
        t2 = vtkmutable(0.0)
        # r[2], distance between line parameter and self LineWidget line
        r.append(sqrt(line.DistanceBetweenLines(self.getPosition1(), self.getPosition2(), p1, p2, cp1, cp2, t1, t2)))
        # r[3], distance between point1 parameter and self LineWidget point1
        r.append(sqrt((p1[0] - sp1[0])**2 + (p1[1] - sp1[1])**2 + (p1[2] - sp1[2])**2))
        # r[4], distance between point1 parameter and self LineWidget point2
        r.append(sqrt((p1[0] - sp2[0])**2 + (p1[1] - sp2[1])**2 + (p1[2] - sp2[2])**2))
        # r[5], distance between point2 parameter and self LineWidget point1
        r.append(sqrt((p2[0] - sp1[0]) ** 2 + (p2[1] - sp1[1]) ** 2 + (p2[2] - sp1[2]) ** 2))
        # r[6], distance between point2 parameter and self LineWidget point1
        r.append(sqrt((p2[0] - sp2[0]) ** 2 + (p2[1] - sp2[1]) ** 2 + (p2[2] - sp2[2]) ** 2))
        # r[7], closest point on line parameter
        r.append(cp1)
        # r[8], closest point on self LineWidget line
        r.append(cp2)
        return r

    def getDistancesToLineWidget(self, lw: LineWidget) -> list[float, float, float, float, float, float, float, vectorFloat3, vectorFloat3]:
        """
            lw      LineWidget
            return  [float, , float, float, [float, float, float], [float, float, float]]
                    float, distance between LineWidget parameter and self LineWidget point1
                    float, distance between LineWidget parameter and self LineWidget point2
                    float, distance between LineWidget parameter and self LineWidget line
                    float, distance between point1 LineWidget parameter and self LineWidget point1
                    float, distance between point1 LineWidget parameter and self LineWidget point2
                    float, distance between point2 LineWidget parameter and self LineWidget point1
                    float, distance between point2 LineWidget parameter and self LineWidget point2
                    [float, float, float], coordinates of the closest point on LineWidget parameter
                    [float, float, float], coordinates of the closest point coordinate on self LineWidget line
        """
        if isinstance(lw, LineWidget):
            return self.getDistancesToLine(lw.getPosition1(), lw.getPosition2())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(lw)))

    def getDistancesToPlane(self, p: vtkPLane | vtkImageSlice | sw.sliceViewWidgets.SliceViewWidget) -> list[float, float, vectorFloat3]:
        """
            p       SliceViewWidget | vtkImageSlice | vtkPlane
            return  [float, float, [float, float, float]]
                    float, distance between plane parameter and self LineWidget position1
                    float, distance between plane parameter and self LineWidget position2
                    [float, float, float], coordinates of the projection of the line on the plane
        """
        if isinstance(p, sw.sliceViewWidgets.SliceViewWidget): p = p.getVtkImageSliceVolume()
        if isinstance(p, vtkImageSlice): p = p.GetMapper().GetSlicePlane()
        if isinstance(p, vtkPlane):
            r = list()
            r.append(p.DistanceToPlane(self.getPosition1()))
            r.append(p.DistanceToPlane(self.getPosition2()))
            t = vtkmutable(0.0)
            pp = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            p.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, pp)
            r.append(pp)
            return r
        else: raise TypeError('parameter type {} is not SliceViewWidget, vtkImageSlice or vtkPlane.'.format(type(p)))

    # IO methods

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                tool = doc.createElement('line')
                currentnode.appendChild(tool)
                # name
                node = doc.createElement('name')
                tool.appendChild(node)
                txt = doc.createTextNode(self.getName())
                node.appendChild(txt)
                # prefix
                node = doc.createElement('prefix')
                tool.appendChild(node)
                buff = ' '.join(self.getPrefix())
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # suffix
                node = doc.createElement('suffix')
                tool.appendChild(node)
                buff = ' '.join(self.getSuffix())
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # legend
                node = doc.createElement('legend')
                tool.appendChild(node)
                buff = ' '.join(self.getLegend())
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # position1
                node = doc.createElement('position1')
                tool.appendChild(node)
                buff = [str(v) for v in self.getPosition1()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # position1
                node = doc.createElement('position2')
                tool.appendChild(node)
                buff = [str(v) for v in self.getPosition2()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # font size
                node = doc.createElement('fontsize')
                tool.appendChild(node)
                buff = self.getFontSize()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font bold
                node = doc.createElement('fontbold')
                tool.appendChild(node)
                buff = self.getFontBold()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font italic
                node = doc.createElement('fontitalic')
                tool.appendChild(node)
                buff = self.getFontItalic()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # font family
                node = doc.createElement('fontfamily')
                tool.appendChild(node)
                buff = self.getFontFamily()
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # text offset
                node = doc.createElement('textoffset')
                tool.appendChild(node)
                buff = [str(v) for v in self.getTextOffset()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # text visibility
                node = doc.createElement('textvisibility')
                tool.appendChild(node)
                buff = self.getTextVisibility()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # color
                node = doc.createElement('color')
                tool.appendChild(node)
                buff = [str(v) for v in self.getColor()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # selected color
                node = doc.createElement('selectedcolor')
                tool.appendChild(node)
                buff = [str(v) for v in self.getSelectedColor()]
                txt = doc.createTextNode(' '.join(buff))
                node.appendChild(txt)
                # opacity
                node = doc.createElement('opacity')
                tool.appendChild(node)
                buff = self.getOpacity()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # point size
                node = doc.createElement('pointsize')
                tool.appendChild(node)
                buff = self.getPointSize()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # line width
                node = doc.createElement('linewidth')
                tool.appendChild(node)
                buff = self.getLineWidth()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # handle size
                node = doc.createElement('handlesize')
                tool.appendChild(node)
                buff = self.getHandleSize()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # handle line width
                node = doc.createElement('handlelinewidth')
                tool.appendChild(node)
                buff = self.getHandleLineWidth()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # render point as sphere
                node = doc.createElement('renderpointsphere')
                tool.appendChild(node)
                buff = self.getRenderPointsAsSpheres()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # render line as tube
                node = doc.createElement('renderlinetube')
                tool.appendChild(node)
                buff = self.getRenderLineAsTube()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # tube radius
                node = doc.createElement('tuberadius')
                tool.appendChild(node)
                buff = self.getTubeRadius()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # tube visibility
                node = doc.createElement('tubevisibility')
                tool.appendChild(node)
                buff = self.getTubeVisibility()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # interpolation
                node = doc.createElement('interpolation')
                tool.appendChild(node)
                buff = self.getInterpolation()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # metallic
                node = doc.createElement('metallic')
                tool.appendChild(node)
                buff = self.getMetallic()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # roughness
                node = doc.createElement('roughness')
                tool.appendChild(node)
                buff = self.getRoughness()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # ambient
                node = doc.createElement('ambient')
                tool.appendChild(node)
                buff = self.getAmbient()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # specular
                node = doc.createElement('specular')
                tool.appendChild(node)
                buff = self.getSpecular()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # specular power
                node = doc.createElement('specularpower')
                tool.appendChild(node)
                buff = self.getSpecularPower()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
                # tolerance
                node = doc.createElement('tolerance')
                tool.appendChild(node)
                buff = self.getTolerance()
                txt = doc.createTextNode(str(buff))
                node.appendChild(txt)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXMLNode(self, currentnode: minidom.Element) -> None:
        if currentnode.nodeName == 'line':
            for node in currentnode.childNodes:
                if node.hasChildNodes():
                    buff = node.firstChild.data
                    if buff is not None:
                        # name
                        if node.nodeName == 'name': self.setName(buff)
                        # prefix
                        if node.nodeName == 'prefix': self.setPrefix(buff.split(' '))
                        # suffix
                        if node.nodeName == 'suffix': self.setSuffix(buff.split(' '))
                        # legend
                        if node.nodeName == 'legend': self.setLegend(buff.split(' '))
                        # position1
                        if node.nodeName == 'position1':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setPosition1(buff)
                        # position2
                        if node.nodeName == 'position2':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setPosition2(buff)
                        # font size
                        elif node.nodeName == 'fontsize': self.setFontSize(int(buff))
                        # font bold
                        elif node.nodeName == 'fontbold': self.setFontBold(bool(buff == 'True'))
                        # font italic
                        elif node.nodeName == 'fontitalic': self.setFontItalic(bool(buff == 'True'))
                        # font family
                        elif node.nodeName == 'fontfamily': self.setFontFamily(buff)
                        # text offset
                        elif node.nodeName == 'textoffset':
                            buff = buff.split(' ')
                            buff = [int(i) for i in buff]
                            self.setTextOffset(buff)
                        # text visibility
                        elif node.nodeName == 'textvisibility': self.setTextVisibility(bool(buff == 'True'))
                        # color
                        elif node.nodeName == 'color':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setColor(buff)
                        # selectedcolor
                        elif node.nodeName == 'selectedcolor':
                            buff = buff.split(' ')
                            buff = [float(i) for i in buff]
                            self.setSelectedColor(buff)
                        # opacity
                        elif node.nodeName == 'opacity': self.setOpacity(float(buff))
                        # point size
                        elif node.nodeName == 'pointsize': self.setPointSize(float(buff))
                        # line width
                        elif node.nodeName == 'linewidth': self.setLineWidth(float(buff))
                        # handle size
                        elif node.nodeName == 'handlesize': self.setHandleSize(float(buff))
                        # handle line width
                        elif node.nodeName == 'handlelinewidth': self.setHandleLineWidth(float(buff))
                        # render point as sphere
                        elif node.nodeName == 'renderpointsphere': self.setRenderPointsAsSpheres(bool(buff == 'True'))
                        # render line as tube
                        elif node.nodeName == 'renderlinetube': self.setRenderLineAsTube(bool(buff == 'True'))
                        # tube radius
                        elif node.nodeName == 'tuberadius': self.setTubeRadius(float(buff))
                        # tube visibility
                        elif node.nodeName == 'tubevisibility': self.setTubeVisibility(bool(buff == 'True'))
                        # interpolation
                        elif node.nodeName == 'interpolation': self.setInterpolation(int(buff))
                        # metallic
                        elif node.nodeName == 'metallic': self.setMetallic(float(buff))
                        # roughness
                        elif node.nodeName == 'roughness': self.setRoughness(float(buff))
                        # ambient
                        elif node.nodeName == 'ambient': self.setAmbient(float(buff))
                        # specular
                        elif node.nodeName == 'specular': self.setSpecular(float(buff))
                        # specularpower
                        elif node.nodeName == 'specularpower': self.setSpecularPower(float(buff))
                        # tolerance
                        elif node.nodeName == 'tolerance': self.setTolerance(int(buff))
        else: raise ValueError('Node name is not \'trajectory\'.')

    def parseXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                tool = doc.getElementsByTagName('line')
                if tool is not None: self.parseXMLNode(tool[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()

    def load(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
        else:
            raise IOError('no such file : {}'.format(filename))


class ToolWidgetCollection(object):
    """
        ToolWidgetCollection

        Inheritance

            object -> ToolWidgetCollection

        Private attributes

            _tools  list of NamedWidget
            _index  Iterator index

        Class method

            str = getFileExt()
            str = getFilterExt()

        Public methods

            __getitem__(int)
            __setitem__(NamedWidget)
            __delitem__(int)
            __len__()
            __contains__(str or NamedWidget)
            __iter__()
            __next__()
            __str__()
            __repr__()
            bool = isEmpty()
            int = count()
            list() = keys()
            remove(int, str or NamedWidget)
            int = index(str or NamedWidget)
            reverse()
            append(NamedWidget)
            insert(str or int, NamedWidget)
            clear()
            sort()
            ToolWidgetCollection = copy()
            list = copyToList()
            list = getList()
            setColor(float, float, float)
            float, float, float = getColor()
            setSelectedColor(float, float, float)
            float, float, float = getSelectedColor()
            newDistanceWidget()
            newBiDimensionalWidget()
            newAngleWidget()
            newHandleWidget()
            newLineWidget()
            newBorderWidget()
            newTextWidget()
            select(str or int, NamedWidget)
            createXML(minidom.Document.documentElement)
            parseXML(minidom.Document, minidom.Document.documentElement)
            parseXMLNode(minidom.Document.documentElement)
            saveAs()
            save()
            load()

        Major revisions
            16/03/2023 Changed items type in _tools list, tuple(Str Name, NamedWidget) replaced by NamedWidget
            16/03/2023 Added pop method, removes NamedWidget from list and returns it
            16/03/2023 Added __getattr__ method, gives access to setter and getter methods of NamedWidget
    """

    __slots__ = ['_referenceID', '_filename', '_tools', '_index', '_color',
                 '_scolor', '_lwidth', '_alpha', '_ffamily', '_fsize', '_interactor']

    _FILEEXT = '.xtools'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe tool collection (*{})'.format(cls._FILEEXT)

    # Special method

    def __init__(self,
                 volume: sc.sisypheVolume.SisypheVolume | None = None,
                 interactor: vtkRenderWindowInteractor | None = None) -> None:
        self._tools = list()
        self._index = 0
        self._color = _DEFAULTCOLOR
        self._scolor = _DEFAULTSCOLOR
        self._lwidth = _LWIDTH
        self._alpha = _ALPHA
        self._fsize = _FSIZE
        self._ffamily = _FFAMILY
        self._interactor = interactor
        # reference SisypheVolume ID
        if isinstance(volume, sc.sisypheVolume.SisypheVolume):
            self._referenceID = volume.getID()
            if volume.hasFilename():
                filename, ext = splitext(volume.getFilename())
                filename += self._FILEEXT
        else:
            self._referenceID = None
            self._filename = ''

    # Container special methods

    def __getitem__(self, key: int | str) -> NamedWidget:
        # key is Name str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._tools):
                return self._tools[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int, value: NamedWidget):
        if isinstance(value, NamedWidget):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._tools):
                    if value.getName() in self: key = self.index(value)
                    self._tools[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not NamedWidget.'.format(type(value)))

    def __delitem__(self, key: int | str | NamedWidget) -> None:
        # key is Name str or NamedWidget
        if isinstance(key, (str, NamedWidget)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._tools):
                del self._tools[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, value: str | NamedWidget) -> bool:
        keys = [k.getName() for k in self._tools]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is NamedWidget
        elif isinstance(value, NamedWidget):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or NamedWidget.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> NamedWidget:
        if self._index < len(self._tools):
            n = self._index
            self._index += 1
            return self._tools[n]
        else: raise StopIteration

    # Private method

    def _KeyToIndex(self, key: str) -> int:
        keys = [k[0] for k in self._tools]
        return keys.index(key)

    # Container public methods

    def isEmpty(self) -> bool:
        return len(self._tools) == 0

    def count(self) -> int:
        return len(self._tools)

    def keys(self) -> list[str]:
        # return list of keys (widget name)
        return [k.getName() for k in self._tools]

    def remove(self, value: NamedWidget) -> None:
        # value is NamedWidget
        if isinstance(value, NamedWidget):
            self._tools.remove(value)
        # value is NamedWidget, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or NamedWidget.'.format(type(value)))

    def pop(self, key: int | str | NamedWidget | None = None):
        if key is None: return self._tools.pop()
        # key is Name str or NamedWidget
        if isinstance(key, (str, NamedWidget)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._tools.pop(key)
        else: raise TypeError('parameter type {} is not int, str or NamedWidget.'.format(type(key)))

    def index(self, value: str | NamedWidget):
        keys = [k.getName() for k in self._tools]
        # value is NamedWidget
        if isinstance(value, NamedWidget):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or NamedWidget.'.format(type(value)))

    def reverse(self) -> None:
        self._tools.reverse()

    def append(self, value: NamedWidget):
        if isinstance(value, NamedWidget):
            if value.getName() not in self: self._tools.append(value)
            else: self._tools[self.index(value)] = value
        else: raise TypeError('parameter type {} is not NamedWidget.'.format(type(value)))

    def insert(self, key: int | str | NamedWidget, value: NamedWidget):
        if isinstance(value, NamedWidget):
            # value is Name str or NamedWidget
            if isinstance(key, (str, NamedWidget)):
                key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._tools):
                    if value.getName() not in self: self._tools.insert(key, value)
                    else: self._tools[self.index(value)] = value
                else: IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not NamedWidget.'.format(type(value)))

    def clear(self) -> None:
        self._tools.clear()

    def sort(self, reverse: bool = False) -> None:
        def _getName(item):
            return item.getName()

        self._tools.sort(reverse=reverse, key=_getName)

    def copy(self) -> ToolWidgetCollection:
        tools = ToolWidgetCollection()
        for tool in self._tools:
            tools.append(tool)
        return tools

    def copyToList(self) -> list[NamedWidget]:
        tools = self._tools.copy()
        return tools

    def getList(self) -> list[NamedWidget]:
        return self._tools

    # Public methods

    def getReferenceID(self) -> str:
        return self._referenceID

    def setReferenceID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(ID, str): self._referenceID = ID
        elif isinstance(ID, sc.sisypheVolume.SisypheVolume): self._referenceID = ID.getID()
        else: self._referenceID = None

    def hasReferenceID(self) -> bool:
        return self._referenceID is not None

    def hasSameID(self, ID: str | sc.sisypheVolume.SisypheVolume):
        if isinstance(ID, sc.sisypheVolume.SisypheVolume): ID = ID.getID()
        if isinstance(ID, str): return ID == self._referenceID
        else: raise TypeError('parameter type {} is not str or SisypheVolume'.format(type(ID)))

    def hasFilename(self) -> bool:
        if self._filename != '':
            if exists(self._filename):
                return True
            else:
                self._filename = ''
        return False

    def getFilename(self) -> str:
        return self._filename

    def setFilenameFromVolume(self, img: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(img, sc.sisypheVolume.SisypheVolume):
            if img.hasFilename():
                path, ext = splitext(img.getFilename())
                path += self._FILEEXT
                self._filename = path
            else: self._filename = ''
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(img)))

    def setColor(self, c: vectorFloat3) -> None:
        if isinstance(c, (list, tuple)):
            if all([0.0 <= i <= 1.0 for i in c]):
                self._color = c
                if self.count() > 0:
                    for tool in self._tools:
                        tool.setColor(c)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(c))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getColor(self) -> vectorFloat3:
        return self._color

    def setSelectedColor(self, c: vectorFloat3):
        if isinstance(c, (list, tuple)):
            if all([0.0 <= i <= 1.0 for i in c]):
                self._scolor = c
                for tool in self._tools:
                    tool.setSelectedColor(c)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(c))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getSelectedColor(self) -> vectorFloat3:
        return self._scolor

    def setOpacity(self, v: float) -> None:
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._alpha = v
                if self.count() > 0:
                    for tool in self._tools:
                        tool.setOpacity(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self) -> float:
        return self._alpha

    def setLineWidth(self, v: float) -> None:
        if isinstance(v, float):
            self._lwidth = v
            if self.count() > 0:
                for tool in self._tools:
                    tool.setLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getLineWidth(self) -> float:
        return self._lwidth

    def setFontFamily(self, v: str = _FFAMILY) -> None:
        if isinstance(v, str):
            self._ffamily = v
            if self.count() > 0:
                for tool in self._tools:
                    if not isinstance(tool, BoxWidget):
                        tool.setTextProperty(fontname=self._ffamily)
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def getFontFamily(self) -> str:
        return self._ffamily

    def setInteractor(self, interactor: vtkRenderWindowInteractor) -> None:
        if isinstance(interactor, vtkRenderWindowInteractor):
            self._interactor = interactor
        else: raise TypeError('parameter type {} is not vtkRenderWindowInteractor.'.format(type(interactor)))

    def hasInteractor(self) -> bool:
        return self._interactor is not None

    def newDistanceWidget(self, name: str = '') -> DistanceWidget:
        if self.hasInteractor():
            r = vtkDistanceRepresentation2D()
            r.InstantiateHandleRepresentation()
            r1 = r.GetPoint1Representation()
            r1.SetHandleSize(_HSIZE)
            r1.GetProperty().SetLineWidth(self._lwidth)
            r1.GetProperty().SetOpacity(self._alpha)
            r1.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r1.GetSelectedProperty().SetLineWidth(self._lwidth)
            r1.GetSelectedProperty().SetOpacity(self._alpha)
            r1.GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r2 = r.GetPoint2Representation()
            r2.SetHandleSize(_HSIZE)
            r2.GetProperty().SetLineWidth(self._lwidth)
            r2.GetProperty().SetOpacity(self._alpha)
            r2.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r2.GetSelectedProperty().SetLineWidth(self._lwidth)
            r2.GetSelectedProperty().SetOpacity(self._alpha)
            r2.GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.SetHandleSize(_HSIZE)
            r.RulerModeOff()
            # r.SetRulerDistance(10.0)
            r.SetTolerance(_TOL)
            r.GetAxisProperty().SetLineWidth(self._lwidth)
            r.GetAxisProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetAxisProperty().SetOpacity(self._alpha)
            r.GetAxis().SetTickLength(0)
            r.GetAxis().SetNumberOfMinorTicks(0)
            r.GetAxis().SetMinorTickLength(0)
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                r.GetAxis().GetTitleTextProperty().SetFontFamilyAsString(self._ffamily)
                r.GetAxis().GetLabelTextProperty().SetFontFamilyAsString(self._ffamily)
            else:
                r.GetAxis().GetTitleTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetAxis().GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetAxis().GetTitleTextProperty().SetFontFile(self._ffamily)
                r.GetAxis().GetLabelTextProperty().SetFontFile(self._ffamily)
            r.GetAxis().GetTitleTextProperty().SetFontSize(self._fsize)
            r.GetAxis().GetTitleTextProperty().BoldOff()
            r.GetAxis().GetTitleTextProperty().ItalicOff()
            r.GetAxis().GetLabelTextProperty().SetFontSize(self._fsize)
            r.GetAxis().GetLabelTextProperty().BoldOff()
            r.GetAxis().GetLabelTextProperty().ItalicOff()
            r.GetAxis().SizeFontRelativeToAxisOff()
            r.GetAxis().GetTitleTextProperty().SetOpacity(self._alpha)
            r.GetAxis().GetLabelTextProperty().SetOpacity(self._alpha)
            r.GetAxis().GetTitleTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetAxis().GetLabelTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            if name == '': name = 'Distance#' + str(len(self._tools) + 1)
            widget = DistanceWidget(name)
            widget.SetInteractor(self._interactor)
            widget.SetRepresentation(r)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newOrthogonalDistanceWidget(self, name: str = '') -> OrthogonalDistanceWidget:
        if self.hasInteractor():
            r = vtkBiDimensionalRepresentation2D()
            r.InstantiateHandleRepresentation()
            r.GetPoint1Representation().SetHandleSize(_HSIZE)
            r.GetPoint1Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint1Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint1Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint1Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint1Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetPoint2Representation().SetHandleSize(_HSIZE)
            r.GetPoint2Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint2Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint2Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint2Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint2Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetPoint3Representation().SetHandleSize(_HSIZE)
            r.GetPoint3Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint3Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint3Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint3Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint3Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint3Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetPoint4Representation().SetHandleSize(_HSIZE)
            r.GetPoint4Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint4Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint4Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint4Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint4Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint4Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.SetHandleSize(_HSIZE)
            r.SetTolerance(_TOL)
            r.GetLineProperty().SetLineWidth(self._lwidth)
            r.GetLineProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetLineProperty().SetOpacity(self._alpha)
            r.GetSelectedLineProperty().SetLineWidth(self._lwidth)
            r.GetSelectedLineProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetSelectedLineProperty().SetOpacity(self._alpha)
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                r.GetTextProperty().SetFontFamilyAsString(self._ffamily)
            else:
                r.GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetTextProperty().SetFontFile(self._ffamily)
            r.GetTextProperty().SetFontSize(self._fsize)
            r.GetTextProperty().BoldOff()
            r.GetTextProperty().ItalicOff()
            r.GetTextProperty().SetOpacity(self._alpha)
            r.GetTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            if name == '': name = 'OrthoDistance#' + str(len(self._tools) + 1)
            widget = OrthogonalDistanceWidget(name)
            widget.SetInteractor(self._interactor)
            widget.SetRepresentation(r)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newAngleWidget(self, name: str = '') -> AngleWidget:
        if self.hasInteractor():
            r = vtkAngleRepresentation2D()
            r.InstantiateHandleRepresentation()
            r.GetPoint1Representation().SetHandleSize(_HSIZE)
            r.GetPoint1Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint1Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint1Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint1Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint1Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetPoint2Representation().SetHandleSize(_HSIZE)
            r.GetPoint2Representation().GetProperty().SetLineWidth(self._lwidth)
            r.GetPoint2Representation().GetProperty().SetOpacity(self._alpha)
            r.GetPoint2Representation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetPoint2Representation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetPoint2Representation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.GetCenterRepresentation().SetHandleSize(_HSIZE)
            r.GetCenterRepresentation().GetProperty().SetLineWidth(self._lwidth)
            r.GetCenterRepresentation().GetProperty().SetOpacity(self._alpha)
            r.GetCenterRepresentation().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetCenterRepresentation().GetSelectedProperty().SetLineWidth(self._lwidth)
            r.GetCenterRepresentation().GetSelectedProperty().SetOpacity(self._alpha)
            r.GetCenterRepresentation().GetSelectedProperty().SetColor(self._scolor[0], self._scolor[1], self._scolor[2])
            r.SetHandleSize(_HSIZE)
            r.SetTolerance(_TOL)
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                r.GetArc().GetLabelTextProperty().SetFontFamilyAsString(self._ffamily)
                r.GetRay1().GetLabelTextProperty().SetFontFamilyAsString(self._ffamily)
                r.GetRay2().GetLabelTextProperty().SetFontFamilyAsString(self._ffamily)
            else:
                r.GetArc().GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetRay1().GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetRay2().GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
                r.GetArc().GetLabelTextProperty().SetFontFile(self._ffamily)
                r.GetRay1().GetLabelTextProperty().SetFontFile(self._ffamily)
                r.GetRay2().GetLabelTextProperty().SetFontFile(self._ffamily)
            r.GetArc().GetLabelTextProperty().SetFontSize(self._fsize)
            r.GetArc().GetLabelTextProperty().BoldOff()
            r.GetArc().GetLabelTextProperty().ItalicOff()
            r.GetArc().GetLabelTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetArc().GetLabelTextProperty().SetOpacity(self._alpha)
            r.GetArc().GetProperty().SetLineWidth(self._lwidth)
            r.GetArc().GetProperty().SetOpacity(self._alpha)
            r.GetArc().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetRay1().GetLabelTextProperty().SetFontSize(self._fsize)
            r.GetRay1().GetLabelTextProperty().BoldOff()
            r.GetRay1().GetLabelTextProperty().ItalicOff()
            r.GetRay1().GetLabelTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetRay1().GetLabelTextProperty().SetOpacity(self._alpha)
            r.GetRay1().GetProperty().SetLineWidth(self._lwidth)
            r.GetRay1().GetProperty().SetOpacity(self._alpha)
            r.GetRay1().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetRay2().GetLabelTextProperty().SetFontSize(self._fsize)
            r.GetRay2().GetLabelTextProperty().BoldOff()
            r.GetRay2().GetLabelTextProperty().ItalicOff()
            r.GetRay2().GetLabelTextProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetRay2().GetLabelTextProperty().SetOpacity(self._alpha)
            r.GetRay2().GetProperty().SetLineWidth(self._lwidth)
            r.GetRay2().GetProperty().SetOpacity(self._alpha)
            r.GetRay2().GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
            if name == '': name = 'Angle#' + str(len(self._tools) + 1)
            widget = AngleWidget(name)
            widget.SetInteractor(self._interactor)
            widget.SetRepresentation(r)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newBoxWidget(self, p: vectorFloat2, name: str = '') -> BoxWidget:
        if self.hasInteractor():
            if name == '': name = 'Box#' + str(len(self._tools) + 1)
            widget = BoxWidget(name)
            widget.CreateDefaultRepresentation()
            r = widget.GetBorderRepresentation()
            r.SetPosition(p[0] - 0.1, p[1] - 0.1)
            r.SetPosition2(0.2, 0.2)
            r.SetMinimumSize(10, 10)
            r.SetTolerance(_TOL)
            r.VisibilityOn()
            r.SetShowBorderToOn()
            r.ProportionalResizeOn()
            r.GetBorderProperty().SetColor(self._color[0], self._color[1], self._color[2])
            r.GetBorderProperty().SetOpacity(self._alpha)
            r.GetBorderProperty().SetLineWidth(self._lwidth)
            widget.SelectableOn()
            widget.ResizableOn()
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newTextWidget(self, p: vectorFloat2, text: str, name: str = '') -> TextWidget:
        if self.hasInteractor():
            if name == '': name = 'Text#' + str(len(self._tools) + 1)
            widget = TextWidget(name)
            widget.CreateDefaultRepresentation()
            r = widget.GetRepresentation()
            r.SetText(text)
            r.SetShowBorderToOff()
            r.GetBorderProperty().SetLineWidth(self._lwidth)
            r.GetBorderProperty().SetOpacity(self._alpha)
            widget.GetTextActor().SetTextScaleModeToNone()
            pr = widget.GetTextActor().GetTextProperty()
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                pr.SetFontFamilyAsString(self._ffamily)
            else:
                pr.SetFontFamily(VTK_FONT_FILE)
                pr.SetFontFile(self._ffamily)
            pr.SetFontSize(self._fsize)
            pr.FrameOff()
            pr.SetColor(self._color[0], self._color[1], self._color[2])
            pr.SetOpacity(self._alpha)
            pr.SetFontFamilyToArial()
            pr.SetJustificationToCentered()
            pr.SetVerticalJustificationToCentered()
            widget.SelectableOn()
            widget.setPosition(p[0], p[1])
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newHandleWidget(self, p: vectorFloat3, name: str = '') -> HandleWidget:
        if self.hasInteractor():
            if name == '': name = 'Target#' + str(len(self._tools) + 1)
            widget = HandleWidget(name)
            widget.setPosition(p)
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newLineWidget(self, p1: vectorFloat3, p2: vectorFloat3, name: str = '') -> LineWidget:
        if self.hasInteractor():
            if name == '': name = 'Trajectory#' + str(len(self._tools) + 1)
            widget = LineWidget(name)
            widget.setPosition1(p1)
            widget.setPosition2(p2)
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def select(self, key: str | int) -> None:
        if isinstance(key, NamedWidget):
            key = key.getName()
        if isinstance(key, str):
            key = self.index(key)
        if isinstance(key, int):
            if 0 <= key < len(self._tools):
                for i in range(len(self._tools)):
                    if i != key: c = self._color
                    else: c = self._scolor
                    widget = self._tools[i]
                    widget.setColor(c)
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('referenceID')
            root.appendChild(node)
            txt = doc.createTextNode(str(self.getReferenceID()))
            node.appendChild(txt)
            # NamedWidgets nodes
            for tool in self._tools:
                # save only HandWidget and LineWidget instances
                if isinstance(tool, (HandleWidget, LineWidget)):
                    tool.createXML(doc, root)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.clear()
                node = root.firstChild
                while node:
                    # ID
                    if node.nodeName == 'referenceID':
                        self.setReferenceID(node.firstChild.data)
                    elif node.nodeName == 'point':
                        tool = HandleWidget('')
                        tool.parseXMLNode(node)
                        self.append(tool)
                    elif node.nodeName == 'line':
                        tool = LineWidget('')
                        tool.parseXMLNode(node)
                        self.append(tool)
                    node = node.nextSibling
        else: raise TypeError('parameter type is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        if not self.isEmpty():
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
            doc = minidom.Document()
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            self.createXML(doc)
            buff = doc.toprettyxml()
            f = open(filename, 'w')
            try: f.write(buff)
            except IOError: raise IOError('{} XML file write error.'.format(basename(filename)))
            finally: f.close()
            self._filename = filename
        else: raise AttributeError('ToolWidgetCollection instance is empty.')

    def save(self, filename: str = '') -> None:
        if not self.isEmpty():
            if self.hasFilename():
                filename = self._filename
            if filename != '':
                self.saveAs(filename)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('ToolWidgetCollection instance is empty.')

    def load(self, filename: str = '') -> None:
        if self.hasFilename() and exists(self._filename):
            filename = self._filename
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
            self._filename = filename
        else: raise IOError('No such file : {}'.format(basename(filename)))
