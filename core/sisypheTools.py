"""
External packages/modules
-------------------------

    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

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

from vtk import vtkActor
from vtk import vtkPoints
from vtk import vtkLine
from vtk import vtkPlane
from vtk import vtkPolyData
from vtk import vtkDataSetMapper
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
from vtk import mutable as vtkmutable
from vtk import vtkLineSource
from vtk import vtkAppendPolyData

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTransform import SisypheTransform

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget


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
~~~~~~~~~~~~~~~

    - object -> NamedWidget
             -> (vtk.vtkDistanceWidget, NamedWidget) -> DistanceWidget
             -> (vtk.vtkBiDimensionalWidget, NamedWidget) -> OrthogonalDistanceWidget
             -> (vtk.vtkAngleWidget, NamedWidget) -> AngleWidget
             -> (vtk.vtkBorderWidget, NamedWidget) -> BoxWidget
             -> (vtk.vtkTextWidget, NamedWidget) -> TextWidget
             -> (vtk.vtkHandleWidget, NamedWidget) -> HandleWidget
             -> (vtk.vtkLineWidget2, NamedWidget) -> LineWidget
             > ToolWidgetCollection
"""

vectorFloat2 = list[float] | tuple[float, float]
vectorFloat3 = list[float] | tuple[float, float, float]

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
    Description
    ~~~~~~~~~~~

    Ancestor class for all tool classes.

    Getter/setter methods:
        - tool name
        - type of tool, 2D or 3D

    Inheritance
    ~~~~~~~~~~~

    object -> NamedObject

    Creation: 05/04/2022
    Last revision: 18/12/2023
    """

    # Special method

    """
    Private attribute

    _name   str, name of the vtkWidget
    _3D     bool, display type (True: VolumeViewWidget, False: SliceViewWidget and derived classes)
            used to control sphere and tube actor visibility for HandleWidget and LineWidget
    """

    def __init__(self, name: str = '') -> None:
        """
        NamedWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        self._name = name
        self._3D = False
        self._alpha = 1.0

    # Public methods

    def getName(self) -> str:
        """
        Get the name attribute of the current NamedWidget instance.

        Returns
        -------
        str
            tool name
        """
        return self._name

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current NamedWidget instance.

        Parameters
        ----------
        name : str
            tool name
        """
        if isinstance(name, str): self._name = name
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def hasName(self) -> bool:
        """
        Check whether the name attribute of the current NamedWidget instance is defined.

        Returns
        -------
        bool
            True if tool name is defined
        """
        return self._name != ''

    def setSliceDisplay(self) -> None:
        """
        Set the type attribute of the NamedWidget instance constructor to 2D.
        """
        self._3D = False

    def setVolumeDisplay(self) -> None:
        """
        Set the type attribute of the NamedWidget instance constructor to 3D.
        """
        self._3D = True

    def isVolumeDisplay(self) -> bool:
        """
        Check whether the type attribute of the current NamedWidget instance is 3D.

        Returns
        -------
        bool
            True if tool type is 3D
        """
        return self._3D

    def isSliceDisplay(self) -> bool:
        """
        Check whether the type attribute of the current NamedWidget instance is 2D.

        Returns
        -------
        bool
            True if tool type is 2D
        """
        return not self._3D


class DistanceWidget(vtkDistanceWidget, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Distance tool class. Distance-measuring 2D widget.
    It consists of a line ruler between two handles at opposite end points.

    Getter/setter methods:

        - visibility
        - opacity
        - color and selected color
        - font name, bold/italic
        - line width
        - handle size

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedWidget) -> DistanceWidget

    Creation: 05/04/2022
    Last revision: 18/12/2023
    """

    # Special method

    def __init__(self, name: str) -> None:
        """
        DistanceWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        vtkDistanceWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current DistanceWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            self.GetDistanceRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current DistanceWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetDistanceRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current DistanceWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetAxisProperty().SetColor(c[0], c[1], c[2])
        r.GetAxis().GetTitleTextProperty().SetColor(c[0], c[1], c[2])
        r.GetAxis().GetLabelTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        """
        Get the color attribute of the current DistanceWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetDistanceRepresentation()
        return r.GetPoint1Representation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        """
        Set the selected color attribute of the current DistanceWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        """
        Get the selected color attribute of the current DistanceWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetDistanceRepresentation()
        return r.GetPoint1Representation().GetSelectedProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current DistanceWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetProperty().SetOpacity(alpha)
        r.GetPoint1Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetPoint2Representation().GetSelectedProperty().SetOpacity(alpha)
        r.GetAxisProperty().SetOpacity(alpha)
        r.GetAxis().GetTitleTextProperty().SetOpacity(alpha)
        r.GetAxis().GetLabelTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        """
        Get the opacity attribute of the current DistanceWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetDistanceRepresentation().GetAxisProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current DistanceWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
        r = self.GetDistanceRepresentation()
        r.GetPoint1Representation().GetProperty().SetLineWidth(width)
        r.GetPoint1Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetProperty().SetLineWidth(width)
        r.GetPoint2Representation().GetSelectedProperty().SetLineWidth(width)
        r.GetAxisProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current DistanceWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetDistanceRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
        Set the text property attribute of the current DistanceWidget instance.

        Parameters
        ----------
        fontname : str
            font name, 'Arial' (default), 'Courier', 'Times' or filename
        bold : bool
            text in bold (default False)
        italic : bool
            text in italic (default False)
        """
        r = self.GetDistanceRepresentation().GetAxis()
        r1 = r.GetTitleTextProperty()
        r1.SetBold(bold)
        r1.SetItalic(italic)
        r1.ShadowOff()
        r2 = r.GetLabelTextProperty()
        r2.SetBold(bold)
        r2.SetItalic(italic)
        r2.ShadowOff()
        if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
            try:
                r1.SetFontFamily(VTK_FONT_FILE)
                r2.SetFontFamily(VTK_FONT_FILE)
                r1.SetFontFile(fontname)
                r2.SetFontFile(fontname)
            except:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')
        else:
            r1.SetFontFamilyAsString('Arial')
            r2.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Get the text property attribute of the current DistanceWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - str, fontname
            - first bool, is bold ?
            - second bool, is italic ?
        """
        r = self.GetDistanceRepresentation().GetAxis().GetTitleTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current DistanceWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        self.GetDistanceRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current DistanceWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetDistanceRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        """
        Set the handle size attribute of the current DistanceWidget instance.

        Parameters
        ----------
        size : float
            handle size
        """
        r = self.GetDistanceRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        """
        Get the handle size attribute of the current DistanceWidget instance.

        Returns
        -------
        float
            handle size
        """
        return self.GetDistanceRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        """
        Set default representation (size, color, font, opacity...) of the current DistanceWidget instance.
        """
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

    def getDistance(self) -> float:
        """
        Get the distance value of the current DistanceWidget instance.

        Returns
        -------
        float
            distance in mm
        """
        return self.GetDistanceRepresentation().GetDistance()


class OrthogonalDistanceWidget(vtkBiDimensionalWidget, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Orthogonal distance tool class (two orthogonal rulers).
    It consists of two orthogonal line rulers with handles at the end points.

    Getter/setter methods:

        - visibility
        - opacity
        - color and selected color
        - font name, bold/italic
        - line width
        - handle size

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedWidget) -> OrthogonalDistanceWidget

    Creation: 05/04/2022
    Last revision: 18/12/2023
    """

    # Special method

    def __init__(self, name: str) -> None:
        """
        OrthogonalDistanceWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        vtkBiDimensionalWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            self.GetBiDimensionalRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetBiDimensionalRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint3Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint4Representation().GetProperty().SetColor(c[0], c[1], c[2])
        r.GetLineProperty().SetColor(c[0], c[1], c[2])
        r.GetTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        """
        Get the color attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBiDimensionalRepresentation()
        return r.GetLineProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        """
        Set the selected color attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBiDimensionalRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint3Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint4Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetSelectedLineProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        """
        Get the selected color attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBiDimensionalRepresentation()
        return r.GetSelectedLineProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
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
        """
        Get the opacity attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetBiDimensionalRepresentation().GetLineProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
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
        """
        Get the line width attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetBiDimensionalRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
        Set the text property attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        fontname : str
            font name, 'Arial' (default), 'Courier', 'Times' or filename
        bold : bool
            text in bold (default False)
        italic : bool
            text in italic (default False)
        """
        r = self.GetBiDimensionalRepresentation().GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
            try:
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            except: r.SetFontFamilyAsString('Arial')
        else: r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Get the text property attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - str, fontname
            - first bool, is bold ?
            - second bool, is italic ?
        """
        r = self.GetBiDimensionalRepresentation().GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current OrthogonalDistanceWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        self.GetBiDimensionalRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current OrthogonalDistanceWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetBiDimensionalRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        """
        Set the handle size attribute of the current OrthogonalDistanceWidget instance.

        Parameters
        ----------
        size : float
            handle size
        """
        r = self.GetBiDimensionalRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)
        r.GetPoint3Representation().SetHandleSize(size)
        r.GetPoint4Representation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        """
        Get the handle size attribute of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        float
            handle size
        """
        return self.GetBiDimensionalRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        """
        Set default representation (size, color, font, opacity...) of the current OrthogonalDistanceWidget instance.
        """
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

    def getDistances(self) -> tuple[float, float]:
        """
        Get the distance values of the current OrthogonalDistanceWidget instance.

        Returns
        -------
        tuple[float, float]
            distances in mm
        """
        r = self.GetDistanceRepresentation()
        return r.GetLength1(), r.GetLength2()


class AngleWidget(vtkAngleWidget, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Angle tool class. Angle-measuring 2D widget.
    It consists of two lines with handles at the ends.

    Getter/setter methods:

        - visibility
        - opacity
        - color and selected color
        - font name, bold/italic
        - line width
        - handle size

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedWidget) -> AngleWidget

    Creation: 05/04/2022
    Last revision: 18/12/2023
    """

    # Special method

    def __init__(self, name: str) -> None:
        """
        AngleWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        vtkAngleWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current AngleWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            self.GetAngleRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current AngleWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetAngleRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current AngleWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
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
        """
        Get the color attribute of the current AngleWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetAngleRepresentation()
        return r.GetPoint1Representation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        """
        Set the selected color attribute of the current AngleWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetAngleRepresentation()
        r.GetPoint1Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetPoint2Representation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
        r.GetCenterRepresentation().GetSelectedProperty().SetColor(c[0], c[1], c[2])

    def getSelectedColor(self) -> vectorFloat3:
        """
        Get the selected color attribute of the current AngleWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetAngleRepresentation()
        return r.GetPoint1Representation().GetSelectedProperty().GetColor()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current AngleWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
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
        """
        Get the opacity attribute of the current AngleWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetAngleRepresentation().GetArc().GetProperty().GetOpacity()

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current AngleWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
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
        """
        Get the line width attribute of the current AngleWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetAngleRepresentation().GetPoint1Representation().GetProperty().GetLineWidth()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
        Set the text property attribute of the current AngleWidget instance.

        Parameters
        ----------
        fontname : str
            font name, 'Arial' (default), 'Courier', 'Times' or filename
        bold : bool
            text in bold (default False)
        italic : bool
            text in italic (default False)
        """
        r = self.GetAngleRepresentation().GetArc().GetLabelTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
            try:
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            except: r.SetFontFamilyAsString('Arial')
        else: r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Get the text property attribute of the current AngleWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - str, fontname
            - first bool, is bold ?
            - second bool, is italic ?
        """
        r = self.GetAngleRepresentation().GetArc().GetLabelTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current AngleWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        self.GetAngleRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current AngleWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetAngleRepresentation().GetTolerance()

    def setHandleSize(self, size: float) -> None:
        """
        Set the handle size attribute of the current AngleWidget instance.

        Parameters
        ----------
        size : float
            handle size
        """
        r = self.GetAngleRepresentation()
        r.SetHandleSize(size)
        r.GetPoint1Representation().SetHandleSize(size)
        r.GetPoint2Representation().SetHandleSize(size)
        r.GetCenterRepresentation().SetHandleSize(size)

    def getHandleSize(self) -> float:
        """
        Get the handle size attribute of the current AngleWidget instance.

        Returns
        -------
        float
            handle size
        """
        return self.GetAngleRepresentation().GetHandleSize()

    def setDefaultRepresentation(self) -> None:
        """
        Set default representation (size, color, font, opacity...) of the current AngleWidget instance.
        """
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

    def getAngle(self) -> float:
        """
        Get the angle value of the current AngleWidget instance.

        Returns
        -------
        float
            angle in degrees
        """
        return self.GetDistanceRepresentation().GetAngle()


class BoxWidget(vtkBorderWidget, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Box tool class. It is a rectangle 2D widget.

    Getter/setter methods:

        - visibility
        - opacity
        - color
        - line width
        - size

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget,NamedWidget) -> BoxWidget

    Creation: 05/04/2022
    Last revision: 18/04/2025
    """

    # Special method

    def __init__(self, name: str) -> None:
        """
        BoxWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        vtkBorderWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current BoxWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            self.GetBorderRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current BoxWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetBorderRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current BoxWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBorderRepresentation()
        r.GetBorderProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        """
        Get the color attribute of the current BoxWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        r = self.GetBorderRepresentation()
        return r.GetBorderProperty().GetColor()

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current BoxWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        self.GetBorderRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current BoxWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetBorderRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current BoxWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        self.GetBorderRepresentation().GetBorderProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        """
        Get the opacity attribute of the current BoxWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetBorderRepresentation().GetBorderProperty().GetOpacity()

    def setProportionalResize(self, v: bool) -> None:
        """
        Set the resize behavior attribute of the current BoxWidget instance.
        Indicate whether resizing operations should keep the x-y directions proportional to one another.

        Parameters
        ----------
        v : bool
            keep proportions if True
        """
        if isinstance(v, bool):
            # < Revision 18/04/2025
            # self.GetRepresentation().SetProportionalResize(v)
            self.GetRepresentation().SetProportionalResize(int(v))
            # Revision 18/04/2025 >
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getProportionalResize(self) -> bool:
        """
        Get the resize behavior attribute of the current BoxWidget instance.
        Indicate whether resizing operations should keep the x-y directions proportional to one another.

        Returns
        -------
        bool
            keep proportions if True
        """
        # < Revision 18/04/2025
        # return self.GetRepresentation().GetProportionalResize()
        return self.GetRepresentation().GetProportionalResize() > 0
        # Revision 18/04/2025 >

    def setPosition(self, x: float, y: float) -> None:
        """
        Set the position (upper left corner) of the current BoxWidget instance.

        Parameters
        ----------
        x : float
            x-axis coordinate
        y : float
            y-axis coordinate
        """
        self.GetBorderRepresentation().SetPosition(x, y)

    def getPosition(self) -> tuple[float, float]:
        """
        Set the position (upper left corner) of the current BoxWidget instance.

        Returns
        -------
        tuple[float, float]
            x-axis and y-axis coordinates
        """
        return self.GetBorderRepresentation().GetPosition()

    def setSize(self, w: float, h: float) -> None:
        """
        Set the sizes (width and height) of the current BoxWidget instance.

        Parameters
        ----------
        w : float
            width
        h : float
            height
        """
        self.GetBorderRepresentation().SetPosition2(w, h)

    def getSize(self) -> tuple[float, float]:
        """
        Get the sizes (width and height) of the current BoxWidget instance.

        Returns
        -------
        tuple[float, float]
            width and height
        """
        return self.GetBorderRepresentation().GetPosition2()

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current BoxWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
        self.GetBorderRepresentation().GetBorderProperty().SetLineWidth(width)

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current BoxWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetBorderRepresentation().GetBorderProperty().GetLineWidth()

    def setDefaultRepresentation(self) -> None:
        """
        Set default representation (size, color, font, opacity...) of the current BoxWidget instance.
        """
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
        # < Revision 18/04/2025
        # self.SelectableOn()
        # Revision 18/04/2025 >
        self.ResizableOn()
        self.ManagesCursorOn()

class TextWidget(vtkTextWidget, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Text tool class. It is a text 2D widget.

    Getter/setter methods:

        - visibility
        - opacity
        - color and selected color
        - font name, bold/italic
        - text displayed

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedObject) -> TextWidget

    Creation: 05/04/2022
    Last revision: 18/12/2023
    """

    # Special method

    def __init__(self, name: str) -> None:
        """
        TextWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        """
        vtkTextWidget.__init__(self)
        NamedWidget.__init__(self, name)
        self.setDefaultRepresentation()

    # Public methods

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current TextWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            self.GetRepresentation().SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current TextWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetRepresentation().GetVisibility()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current TextWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        self.GetTextActor().GetTextProperty().SetColor(c[0], c[1], c[2])

    def getColor(self) -> vectorFloat3:
        """
        Get the color attribute of the current TextWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self.GetTextActor().GetTextProperty().GetColor()

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current TextWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        self.GetBorderRepresentation().SetTolerance(tol)

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current TextWidget instance.
        Distance tolerance (in pixels) between tool and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetBorderRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current TextWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        self.GetRepresentation().GetBorderProperty().SetOpacity(alpha)
        self.GetTextActor().GetTextProperty().SetOpacity(alpha)

    def getOpacity(self) -> float:
        """
        Get the opacity attribute of the current TextWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetTextActor().GetTextProperty().GetOpacity()

    def setPosition(self, x: float, y: float) -> None:
        """
        Set the position (upper left corner) of the current TextWidget instance.

        Parameters
        ----------
        x : float
            x-axis coordinate
        y : float
            y-axis coordinate
        """
        self.GetRepresentation().SetPosition(x, y)

    def getPosition(self) -> vectorFloat2:
        """
        Set the position (upper left corner) of the current TextWidget instance.

        Returns
        -------
        tuple[float, float]
            x-axis and y-axis coordinates
        """
        return self.GetRepresentation().GetPosition()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
        Set the text property attribute of the current TextWidget instance.

        Parameters
        ----------
        fontname : str
            font name, 'Arial' (default), 'Courier', 'Times' or filename
        bold : bool
            text in bold (default False)
        italic : bool
            text in italic (default False)
        """
        r = self.GetTextActor().GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
            try:
                r.SetFontFamily(VTK_FONT_FILE)
                r.SetFontFile(fontname)
            except: r.SetFontFamilyAsString('Arial')
        else: r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Get the text property attribute of the current TextWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - str, fontname
            - first bool, is bold ?
            - second bool, is italic ?
        """
        r = self.GetTextActor().GetTextProperty()
        bold = r.GetBold()
        italic = r.GetItalic()
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setText(self, txt: str) -> None:
        """
        Set the text of the current TextWidget instance.

        Parameters
        ----------
        txt : str
            widget text
        """
        if isinstance(txt, str):
            self.GetRepresentation().SetText(txt)
        else: raise TypeError('parameter type {} is not str'.format(type(txt)))

    def getText(self) -> str:
        """
        Get the text of the current TextWidget instance.

        Returns
        -------
        str
            widget text
        """
        return self.GetRepresentation().GetText()

    def setDefaultRepresentation(self) -> None:
        """
        Set default representation (size, color, font, opacity...) of the current TextWidget instance.
        """
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
    Description
    ~~~~~~~~~~~

    Target tool class.

    This is a 3D widget that includes:

        - a cross-shaped handle widget
        - a text widget displaying a prefix, a name, a suffix and a legend
        - a sphere widget as safety zone

    Scope of methods:

        - getter/setter methods

            - prefix, text, suffix and legend displayed
            - font (name, size, bold, italic)
            - visibility
            - opacity
            - color and selected color
            - line width
            - handle size
            - tolerance
            - surface rendering properties

        - plane projection
        - projection on mesh surface
        - various distances
        - IO methods

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedWidget) -> HandleWidget

    Creation: 05/04/2022
    Last revision: 21/05/2025
    """

    _FILEEXT = '.xpoint'
    _DEFAULTSPHERERADIUS = 2
    _DEFAULTSPHERERESOLUTION = 32

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get HandleWidget file extension.

        Returns
        -------
        str
            '.xpoint'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get HandleWidget filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Target tool (.xpoint)'
        """
        return 'PySisyphe Target (*{})'.format(cls._FILEEXT)

    # Special method

    def __init__(self, name: str, legend: str = 'Target') -> None:
        """
        HandleWidget instance constructor.

        Parameters
        ----------
        name : str
            tool name
        legend : str
            legend (displayed under the tool name, default 'Target')
        """
        vtkHandleWidget.__init__(self)
        NamedWidget.__init__(self, name)

        # noinspection PyTypeChecker
        self.AddObserver('InteractionEvent', self._onInteractionEvent)
        # noinspection PyTypeChecker
        self.AddObserver('EndInteractionEvent', self._onEndInteractionEvent)
        # noinspection PyTypeChecker
        self.AddObserver('EnableEvent', self._onEnableEvent)
        # noinspection PyTypeChecker
        self.AddObserver('DisableEvent', self._onDisableEvent)

        self._legend = legend
        self._prefix = ''
        self._suffix = ''
        self._hsize = _HSIZE
        # 0 = static (absolute position), 1 = dynamic (relative or weighted position)
        self._postype = 0

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
        # noinspection PyArgumentList
        mapper.SetInputConnection(self._sphere.GetOutputPort())
        self._sphereActor.SetMapper(mapper)
        self._sphereActor.GetProperty().SetInterpolationToPhong()
        self._sphereActor.GetProperty().SetRepresentationToSurface()
        self._sphereActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self._sphereActor.GetProperty().SetOpacity(0.5 * _ALPHA)

        # noinspection PyArgumentList
        self._cutter.SetInputConnection(self._sphere.GetOutputPort())

        mapper = vtkDataSetMapper()
        # noinspection PyArgumentList
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
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of HandleWidget instance to str
        """
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

    # noinspection PyUnusedLocal
    def _onInteractionEvent(self, widget, event) -> None:
        p = self.GetHandleRepresentation().GetWorldPosition()
        # noinspection PyArgumentList,PyTypeChecker
        self._targetText.SetPosition(p)
        # noinspection PyArgumentList
        self._sphere.SetCenter(p)
        # noinspection PyArgumentList
        self._sphere.Update()
        # noinspection PyArgumentList
        self._cutter.Update()

    def _onEndInteractionEvent(self, widget, event) -> None:
        pass

    # noinspection PyUnusedLocal
    def _onEnableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        renderer.AddActor(self._targetText)
        renderer.AddActor(self._sphereActor)
        renderer.AddActor(self._contourActor)
        self._targetText.SetVisibility(True)
        self.setVisibility(True)
        p = self.GetHandleRepresentation().GetWorldPosition()
        # noinspection PyArgumentList,PyTypeChecker
        self._targetText.SetPosition(p)
        # noinspection PyArgumentList
        self._sphere.SetCenter(p)
        # noinspection PyArgumentList
        self._sphere.Update()
        # Update contour actor
        props = renderer.GetViewProps()
        for i in range(props.GetNumberOfItems()):
            prop = props.GetItemAsObject(i)
            if isinstance(prop, vtkImageSlice):
                # self._cutter.SetCutFunction(prop.GetMapper().GetSlicePlane())
                self.updateContourActor(prop.GetMapper().GetSlicePlane())
                break

    # noinspection PyUnusedLocal
    def _onDisableEvent(self, widget, event) -> None:
        renderer = self.GetCurrentRenderer()
        renderer.RemoveActor(self._targetText)
        renderer.RemoveActor(self._sphereActor)
        renderer.RemoveActor(self._contourActor)
        del self._targetText
        del self._sphereActor
        del self._contourActor

    # Private method

    # def _setText(self, txt: str) -> None:

    # Public methods

    def updateContourActor(self, plane: vtkPlane) -> None:
        """
        Update sphere rendering on a 2D cutting plane. This method is called by private VTK events methods.

        Parameters
        ----------
        plane : vtkPlane
            cutting plane
        """
        if isinstance(plane, vtkPlane):
            plane2 = vtkPlane()
            # noinspection PyArgumentList
            plane2.SetNormal(plane.GetNormal())
            # noinspection PyArgumentList
            plane2.SetOrigin(plane.GetOrigin())
            plane2.Push(0.5)
            self._cutter.SetCutFunction(plane2)
            # noinspection PyArgumentList
            self._cutter.Update()
        else: raise TypeError('parameter type {} is not vtkPlane.'.format(type(plane)))

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        name : str
            tool text name
        """
        super().setName(name)
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def setPrefix(self, txt: str = '') -> None:
        """
        Set the prefix attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        txt : str
            tool text prefix
        """
        if txt != '':
            if txt[-1] != ' ': txt += ' '
        self._prefix = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getPrefix(self) -> str:
        """
        Get the prefix attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        str
            tool text prefix
        """
        return self._prefix

    def setSuffix(self, txt: str = '') -> None:
        """
        Set the suffix attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        txt : str
            tool text suffix
        """
        if txt != '':
            if txt[0] != ' ': txt = ' ' + txt
        self._suffix = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getSuffix(self) -> str:
        """
        Get the suffix attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        str
            tool text suffix
        """
        return self._suffix

    def setLegend(self, txt: str = 'Target') -> None:
        """
        Set the legend attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        txt : str
            tool text legend
        """
        self._legend = txt
        txt = '{}\n{}{}{}'.format(self._legend,
                                  self._prefix,
                                  self.getName(),
                                  self._suffix)
        self._targetText.SetInput(txt)

    def getLegend(self) -> str:
        """
        Get the legend attribute of the current HandleWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        str
            tool text legend
        """
        return self._legend

    def setText(self, txt: str) -> None:
        """
        Set the text of the current HandleWidget instance. The text widget displays a prefix, a name, a suffix and
        a legend.

        Parameters
        ----------
        txt : str
            tool text
        """
        self._targetText.SetInput(txt)

    def getText(self) -> str:
        """
        Get the text of the current HandleWidget instance. The text widget displays a prefix, a name, a suffix and
        a legend.

        Returns
        -------
        str
            tool text
        """
        return self._targetText.GetInput()

    def setFontSize(self, size: int) -> None:
        """
        Set the font size used to display the text of the current HandleWidget instance.

        Parameters
        ----------
        size : int
            font size
        """
        if isinstance(size, int): self._targetText.GetTextProperty().SetFontSize(size)
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getFontSize(self) -> int:
        """
        Get the font size used to display the text of the current HandleWidget instance.

        Returns
        -------
        int
            font size
        """
        return self._targetText.GetTextProperty().GetFontSize()

    def setFontBold(self, v: bool) -> None:
        """
        Display the text of the current HandleWidget instance in bold.

        Parameters
        ----------
        v : bool
            displays in bold if True
        """
        if isinstance(v, bool): self._targetText.GetTextProperty().SetBold(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontBold(self) -> bool:
        """
        Check whether the text of the current HandleWidget instance is displayed in bold.

        Returns
        -------
        bool
            True if text displayed in bold
        """
        return self._targetText.GetTextProperty().GetBold() > 0

    def setFontItalic(self, v: bool) -> None:
        """
        Display the text of the current HandleWidget instance in italic.

        Parameters
        ----------
        v : bool
            displays in italic if True
        """
        if isinstance(v, bool): self._targetText.GetTextProperty().SetItalic(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontItalic(self) -> bool:
        """
        Check whether the text of the current HandleWidget instance is displayed in italic.

        Returns
        -------
        bool
            True if text displayed in italic
        """
        return self._targetText.GetTextProperty().GetItalic() > 0

    def setFontFamily(self, fontname: str = _FFAMILY) -> None:
        """
        Set the font used to display the text of the current HandleWidget instance.

        Parameters
        ----------
        fontname : str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        """
        r = self._targetText.GetTextProperty()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
                try:
                    r.SetFontFamily(VTK_FONT_FILE)
                    r.SetFontFile(fontname)
                except: r.SetFontFamilyAsString('Arial')
            else: r.SetFontFamilyAsString('Arial')

    def getFontFamily(self) -> str:
        """
        Get the font used to display the text of the current HandleWidget instance.

        Returns
        -------
        str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        """
        return self._targetText.GetTextProperty().GetFontFamilyAsString()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
        Set the font properties used to display the text of the current HandleWidget instance.

        Parameters
        ----------
        fontname : str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        bold : bool
            True to display in bold (default False)
        italic : bool
            True to display in italic (default False)
        """
        r = self._targetText.GetTextProperty()
        r.SetBold(bold)
        r.SetItalic(italic)
        r.ShadowOff()
        if fontname in ('Arial', 'Courier', 'Times'):
            r.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
                try:
                    r.SetFontFamily(VTK_FONT_FILE)
                    r.SetFontFile(fontname)
                except: r.SetFontFamilyAsString('Arial')
            else: r.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Set the font properties used to display the text of the current HandleWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - str, fontname
            - first bool, is bold ?
            - second bool, is italic ?
        """
        r = self._targetText.GetTextProperty()
        bold = r.GetBold() > 0
        italic = r.GetItalic() > 0
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setTextOffset(self, r: tuple[int, int] | list[int]) -> None:
        """
        Set the relative position of text in relation to handle in the current HandleWidget instance.

        Parameters
        ----------
        r : tuple[int, int] | list[int]
            - first value, x-axis relative position in pixel unit (+ right, - left)
            - second value, y-axis relative position in pixel unit (+ bottom, - top)
        """
        self._targetText.SetDisplayOffset(r[0], r[1])

    def getTextOffset(self) -> tuple[int, int]:
        """
        Get the relative position of text in relation to handle in the current HandleWidget instance.

        Parameters
        ----------
        tuple[int, int]
            - first value, x-axis relative position in pixel unit (+ right, - left)
            - second value, y-axis relative position in pixel unit (+ bottom, - top)
        """
        return self._targetText.GetDisplayOffset()

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current HandleWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            if not v:
                # < Revision 21/05/2025
                # self._alpha = self.GetHandleRepresentation().GetProperty().GetOpacity()
                alpha = self.GetHandleRepresentation().GetProperty().GetOpacity()
                if alpha != 0.0: self._alpha = alpha
                # Revision 21/05/2025 >
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
        """
        Get the visibility attribute of the current HandleWidget instance.

        Returns
        -------
        bool
            True if visible
        """
        return self.GetHandleRepresentation().GetProperty().GetOpacity() > 0

    def setTextVisibility(self, v: bool) -> None:
        """
        Show/hide the text of the current HandleWidget instance.

        Parameters
        ----------
        v : bool
            True to show text
        """
        if isinstance(v, bool): self._targetText.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextVisibility(self) -> bool:
        """
        Get the text visibility of the current HandleWidget instance.

        Returns
        -------
        bool
            True if text is visible
        """
        return self._targetText.GetVisibility() > 0

    def setSphereVisibility(self, v: bool) -> None:
        """
        Show/hide safety zone (sphere widget) of the current HandleWidget instance.

        Parameters
        ----------
        v : bool
            True to show text
        """
        if isinstance(v, bool):
            if self.isVolumeDisplay():
                self._sphereActor.SetVisibility(v)
                self._contourActor.SetVisibility(False)
            else:
                self._sphereActor.SetVisibility(False)
                self._contourActor.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSphereVisibility(self) -> bool:
        """
        Get the safety zone (sphere widget) visibility of the current HandleWidget instance.

        Returns
        -------
        bool
            True if text is visible
        """
        return self._sphereActor.GetVisibility() > 0 or \
            self._contourActor.GetVisibility() > 0

    def setSphereRadius(self, radius: float) -> None:
        """
        Set the safety zone radius (sphere widget) of the current HandleWidget instance.

        Parameters
        ----------
        radius : float
            safety zone radius in mm
        """
        if isinstance(radius, float):
            self._sphere.SetRadius(radius)
            # noinspection PyArgumentList
            self._sphere.Update()
        else: raise TypeError('parameter type {} is not float.'.format(type(radius)))

    def getSphereRadius(self) -> float:
        """
        Get the safety zone radius (sphere widget) of the current HandleWidget instance.

        Returns
        -------
        float
            safety zone radius in mm
        """
        return self._sphere.GetRadius()

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current HandleWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
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
        """
        Get the color attribute of the current HandleWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self.GetRepresentation().GetProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        """
        Set the selected color attribute of the current HandleWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                if all([0.0 <= i <= 1.0 for i in c]):
                    self.GetHandleRepresentation().GetSelectedProperty().SetColor(c[0], c[1], c[2])
                else: raise ValueError('parameter value is not between 0.0 and 1.0.')
            else: raise ValueError('list length {} is not 3.'.format(len(c)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getSelectedColor(self) -> vectorFloat3:
        """
        Get the selected color attribute of the current HandleWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self.GetHandleRepresentation().GetSelectedProperty().GetColor()

    def setPosition(self, p: vectorFloat3) -> None:
        """
        Set the position of the current HandleWidget instance.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float]
            position in world coordinates
        """
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, (int, float)) for i in p]):
                    self.GetHandleRepresentation().SetWorldPosition(p)
                    # noinspection PyArgumentList
                    self._targetText.SetPosition(p)
                    # noinspection PyArgumentList
                    self._sphere.SetCenter(p)
                    # noinspection PyArgumentList
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
                else: raise TypeError('parameter type is not int or float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition(self) -> vectorFloat3:
        """
        Get the position of the current HandleWidget instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            position in world coordinates
        """
        return self.GetHandleRepresentation().GetWorldPosition()

    def planeProjection(self, plane: vtkPlane | vtkImageSlice | SliceViewWidget) -> None:
        """
        Projecting the current HandleWidget instance onto a plane along its normal direction.

        Parameters
        ----------
        plane : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            projection plane
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(plane, SliceViewWidget): plane = plane.getVtkImageSliceVolume()
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
            # noinspection PyTypeChecker
            plane.IntersectWithLine(self.getPosition(), p2, t, p)
            self.setPosition(p)

    def meshSurfaceProjection(self,
                              plane: vtkPlane | vtkImageSlice | SliceViewWidget,
                              mesh: SisypheMesh) -> int:
        """
        Projects the current instance of the HandleWidget onto the surface of a mesh along the normal direction of a
        plane.

        Parameters
        ----------
        plane : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            plane used to define normal direction
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            projection mesh
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(plane, SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            v = list(plane.GetNormal())
            v[0] *= 200.0
            v[1] *= 200.0
            v[2] *= 200.0
        else: return 0
        if isinstance(mesh, SisypheMesh):
            f = vtkOBBTree()
            # noinspection PyTypeChecker
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
                if n > 0:
                    d = list()
                    for i in range(n):
                        pr = ps.GetPoint(i)
                        d.append(sqrt((p[0] - pr[0])**2 + (p[1] - pr[1])**2 + (p[2] - pr[2])**2))
                    self.setPosition(ps.GetPoint(d.index(min(d))))
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current HandleWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
        if isinstance(width, float):
            self.GetHandleRepresentation().GetProperty().SetLineWidth(width)
            self.GetHandleRepresentation().GetSelectedProperty().SetLineWidth(width)
            self._contourActor.GetProperty().SetLineWidth(width)
        else: raise TypeError('parameter functype {} is not float'.format(type(width)))

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current HandleWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetHandleRepresentation().GetProperty().GetLineWidth()

    def setHandleSize(self, size: float) -> None:
        """
        Set the handle size attribute of the current HandleWidget instance.

        Parameters
        ----------
        size : float
            handle size
        """
        if isinstance(size, float):
            self._hsize = size
            lineh = vtkLineSource()
            linev = vtkLineSource()
            lineh.SetPoint1(-self._hsize / 2, 0.0, 0.0)
            lineh.SetPoint2(self._hsize / 2, 0.0, 0.0)
            linev.SetPoint1(0.0, -self._hsize / 2, 0)
            linev.SetPoint2(0.0, self._hsize / 2, 0)
            cross = vtkAppendPolyData()
            # noinspection PyArgumentList
            cross.AddInputConnection(lineh.GetOutputPort())
            # noinspection PyArgumentList
            cross.AddInputConnection(linev.GetOutputPort())
            # noinspection PyArgumentList
            cross.Update()
            self.GetHandleRepresentation().SetHandle(cross.GetOutput())
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getHandleSize(self) -> float:
        """
        Get the handle size attribute of the current HandleWidget instance.

        Returns
        -------
        float
            handle size
        """
        return self._hsize

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current HandleWidget instance. Distance tolerance (in pixels) between tool
        and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        if isinstance(tol, int):
            self.GetHandleRepresentation().SetTolerance(tol)
        else: raise TypeError('parameter type {} is not int'.format(type(tol)))

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current HandleWidget instance. Distance tolerance (in pixels) between tool
        and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetHandleRepresentation().GetTolerance()

    def setOpacity(self, alpha: float) -> None:
        """
        Set the opacity attribute of the current HandleWidget instance.

        Parameters
        ----------
        alpha : float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
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
        """
        Get the opacity attribute of the current HandleWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetHandleRepresentation().GetProperty().GetOpacity()

    def setInterpolation(self, inter: int) -> None:
        """
        Set the shading interpolation method of the current HandleWidget instance, as int code.

        Parameters
        ----------
        inter : int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
        if isinstance(inter, int):
            self._sphereActor.GetProperty().SetInterpolation(inter)
        else: raise TypeError('parameter functype {} is not int.'.format(type(inter)))

    def getInterpolation(self) -> int:
        """
        Get the shading interpolation method (as int code) of the current HandleWidget instance.

        Returns
        -------
        int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
        return self._sphereActor.GetProperty().GetInterpolation()

    def setMetallic(self, v: float) -> None:
        """
        Set the metallic coefficient of the current HandleWidget instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Parameters
        ----------
        v : float
            metallic coefficient
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetMetallic(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getMetallic(self) -> float:
        """
        Get the metallic coefficient of the current HandleWidget instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Returns
        -------
        float
            metallic coefficient
        """
        return self._sphereActor.GetProperty().GetMetallic()

    def setRoughness(self, v: float) -> None:
        """
        Set the roughness coefficient of the current HandleWidget instance. This value has to be between 0.0 (glossy)
        and 1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Parameters
        ----------
        v : float
            between 0.0 (glossy) and 1.0 (rough)
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetRoughness(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getRoughness(self) -> float:
        """
        Get the roughness coefficient of the current HandleWidget instance. This value has to be between 0.0 (glossy)
        and 1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Returns
        -------
        float
            between 0.0 (glossy) and 1.0 (rough)
        """
        return self._sphereActor.GetProperty().GetRoughness()

    def setAmbient(self, v: float) -> None:
        """
        Set the ambient lighting coefficient of the current HandleWidget instance.

        Parameters
        ----------
        v : float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetAmbient(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getAmbient(self) -> float:
        """
        Get the ambient lighting coefficient of the current HandleWidget instance.

        Returns
        -------
        float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
        return self._sphereActor.GetProperty().GetAmbient()

    def setSpecular(self, v: float) -> None:
        """
        Set the specular lighting coefficient of the current HandleWidget instance.

        Parameters
        ----------
        v : float
            specular lighting coefficient (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetSpecular(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecular(self) -> float:
        """
        Get the specular lighting coefficient of the current HandleWidget instance.

        Returns
        -------
        float
            specular lighting coefficient (between 0.0 and 1.0)
        """
        return self._sphereActor.GetProperty().GetSpecular()

    def setSpecularPower(self, v: float) -> None:
        """
        Set the specular power of the current HandleWidget instance.

        Parameters
        ----------
        v : float
            specular power (between 0.0 and 50.0)
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._sphereActor.GetProperty().SetSpecularPower(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecularPower(self) -> float:
        """
        Get the specular power of the current HandleWidget instance.

        Returns
        -------
        float
            specular power (between 0.0 and 50.0)
        """
        return self._sphereActor.GetProperty().GetSpecularPower()

    def setSphereProperties(self, p: vtkProperty) -> None:
        """
        Set the safety zone sphere properties of the current HandleWidget instance.

        Parameters
        ----------
        p : vtkProperty
            sphere properties
        """
        if isinstance(p, vtkProperty): self._sphereActor.SetProperty(p)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(p)))

    def getSphereProperties(self) -> vtkProperty:
        """
        Get the safety zone sphere properties of the current HandleWidget instance.

        Returns
        -------
        vtkProperty
            sphere properties
        """
        return self._sphereActor.GetProperty()

    def deepCopy(self) -> HandleWidget:
        """
        Deep copy of the current HandleWidget instance.

        Returns
        -------
        HandleWidget
            widget copy
        """
        r = vtkPointHandleRepresentation3D()
        r.DeepCopy(self.GetHandleRepresentation())
        widget = HandleWidget(self.getName())
        widget.SetRepresentation(r)
        widget.copyAttributesFrom(self)
        return widget

    def copyAttributesTo(self, tool: HandleWidget) -> None:
        """
        Copy the current HandleWidget instance attributes to another HandleWidget.

        Parameters
        ----------
        tool : HandleWidget
            copy attributes to this widget
        """
        if isinstance(tool, HandleWidget):
            tool.setText(self.getText())
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

    def copyAttributesFrom(self, tool: HandleWidget) -> None:
        """
        Set the current HandleWidget instance attributes from another HandleWidget.

        Parameters
        ----------
        tool : HandleWidget
            copy attributes from this widget
        """
        if isinstance(tool, HandleWidget):
            self.setText(tool.getText())
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
        """
        Set default representation (size, color, font, opacity...) of the current HandleWidget instance.
        """
        # Handle representation
        r = vtkOrientedPolygonalHandleRepresentation3D()
        lineh = vtkLineSource()
        linev = vtkLineSource()
        lineh.SetPoint1(-_HSIZE / 2, 0.0, 0.0)
        lineh.SetPoint2(_HSIZE / 2, 0.0, 0.0)
        linev.SetPoint1(0.0, -_HSIZE / 2, 0)
        linev.SetPoint2(0.0, _HSIZE / 2, 0)    
        cross = vtkAppendPolyData()
        # noinspection PyArgumentList
        cross.AddInputConnection(lineh.GetOutputPort())
        # noinspection PyArgumentList
        cross.AddInputConnection(linev.GetOutputPort())
        # noinspection PyArgumentList
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

    def isStatic(self):
        """
        Check whether the current LineWidget instance is static i.e. absolute position

        Returns
        -------
        bool
            True if static
        """
        return self._postype == 0

    def isDynamic(self):
        """
        Check whether the current LineWidget instance is dynamic i.e. position processed from other tools (relative or
        weighted position)

        Returns
        -------
        bool
            True if dynamic
        """
        return self._postype == 1

    def setStatic(self):
        """
        Set the current LineWidget instance as static i.e. absolute position.
        """
        self._postype = 0

    def setDynamic(self):
        """
        Set the current LineWidget instance as dynamic i.e. position processed from other tools (relative or weighted
        position).
        """
        self._postype = 1

    # Various distance methods

    def getDistanceToPoint(self, p: vectorFloat3) -> float:
        """
        Get the distance between the current HandleWidget instance and a point.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float]

        Returns
        -------
        float
            distance in mm
        """
        p0 = self.getPosition()
        return sqrt((p0[0] - p[0])**2 + (p0[1] - p[1])**2 + (p0[2] - p[2])**2)

    def getDistanceToHandleWidget(self, hw: HandleWidget) -> float:
        """
        Get the distance between the current HandleWidget instance and another HandleWidget.

        Parameters
        ----------
        hw : HandleWidget

        Returns
        -------
        float
            distance in mm
        """
        if isinstance(hw, HandleWidget): return self.getDistanceToPoint(hw.getPosition())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(hw)))

    def getDistanceToLine(self, p1: vectorFloat3, p2: vectorFloat3) -> list[float | vectorFloat3]:
        """
        Get the minimum distance between the current HandleWidget instance and a line.

        Parameters
        ----------
        p1 : tuple[float, float, float] | list[float]
            p1, first point to define line equation
        p2 : tuple[float, float, float] | list[float]
            p2, second point to define line equation

        Returns
        -------
        list[float | list[float | tuple[float, float]]
            - first element: minimum distance in mm
            - second element: coordinates of the closest point in the line
        """
        r = list()
        line = vtkLine()
        t = vtkmutable(0.0)
        cp = [0.0, 0.0, 0.0]
        # noinspection PyTypeChecker
        r.append(sqrt(line.DistanceToLine(self.getPosition(), p1, p2, t, cp)))
        r.append(cp)
        return r

    def getDistanceToLineWidget(self, lw: LineWidget) -> list[float | vectorFloat3]:
        """
        Get the minimum distance between the current HandleWidget instance and a LineWidget.

        Parameters
        ----------
        lw : LineWidget

        Returns
        -------
        list[float | tuple[float, float, float] | list[float]]
            - first element: minimum distance in mm
            - second element: coordinates of the closest point in the line
        """
        if isinstance(lw, LineWidget): return self.getDistanceToLine(lw.getPosition1(), lw.getPosition2())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(lw)))

    def getDistanceToPlane(self, p: vtkPlane | vtkImageSlice | SliceViewWidget) -> float:
        """
        Get the distance between the current HandleWidget instance and a plane along its normal direction.

        Parameters
        ----------
        p : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            plane

        Returns
        -------
        float
            distance in mm
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(p, SliceViewWidget): p = p.getVtkImageSliceVolume()
        if isinstance(p, vtkImageSlice): p = p.GetMapper().GetSlicePlane()
        if isinstance(p, vtkPlane):
            return p.DistanceToPlane(self.getPosition())
        else: raise TypeError('parameter type {} is not SliceViewWidget, vtkImageSlice or vtkPlane.'.format(type(p)))

    # IO methods

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
        Write the current HandleWidget instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        currentnode : minidom.Element
            xml root node
        """
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
        """
        Read the current HandleWidget instance attributes from xml document instance.

        Parameters
        ----------
        currentnode : minidom.Element
            xml root node
        """
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
        """
        Read the current HandleWidget instance attributes from xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                tool = doc.getElementsByTagName('point')
                if tool is not None: self.parseXMLNode(tool[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        """
        Save the current HandleWidget instance to a PySisyphe Target tool (.xpoint) file.

        Parameters
        ----------
        filename : str
            PySisyphe Target tool file name
        """
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
        """
        Load the current HandleWidget instance from a PySisyphe Target tool (.xpoint) file.

        Parameters
        ----------
        filename : str
            PySisyphe Target tool file name
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
        else: raise IOError('no such file : {}'.format(filename))


class LineWidget(vtkLineWidget2, NamedWidget):
    """
    Description
    ~~~~~~~~~~~

    Trajectory tool class.

    This is a 3D widget that includes:

        - three cross-shaped handle widgets, two at the extremities (target and entry points) and one at the middle
        - two text widgets displaying a prefix, a name, a suffix and a legend at the extremities
        - a tube widget as safety zone

   Scope of methods:

        - getter/setter methods

            - prefix, text, suffix and legend displayed
            - font (name, size, bold, italic)
            - visibility
            - opacity
            - color and selected color
            - line width
            - handle size
            - tolerance
            - surface rendering properties

        - plane projection
        - projection on mesh surface
        - various distances
        - IO methods

    Inheritance
    ~~~~~~~~~~~

    (vtkDistanceWidget, NamedWidget) -> LineWidget

    Creation: 05/04/2022
    Last revision: 21/05/2025
    """

    _FILEEXT = '.xline'
    _DEFAULTTUBERADIUS = 2
    _DEFAULTTUBESIDES = 32

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get LineWidget file extension.

        Returns
        -------
        str
            '.xline'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get LineWidget filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Trajectory tool (.xline)'
        """
        return 'PySisyphe Trajectory (*{})'.format(cls._FILEEXT)

    # Special methods

    def __init__(self, name: str, legend: list[str] | tuple[str, str] = ('Target', 'Entry')) -> None:
        """
         LineWidget instance constructor.

         Parameters
         ----------
         name : str
             tool name
         legend : list[str] | tuple[str, str]
             legend (displayed under the tool name, default 'Target' and 'Entry')
         """
        vtkLineWidget2.__init__(self)
        NamedWidget.__init__(self, name)

        # noinspection PyTypeChecker
        self.AddObserver('InteractionEvent', self._onInteractionEvent)
        # noinspection PyTypeChecker
        self.AddObserver('EndInteractionEvent', self._onEndInteractionEvent)
        # noinspection PyTypeChecker
        self.AddObserver('EnableEvent', self._onEnableEvent)
        # noinspection PyTypeChecker
        self.AddObserver('DisableEvent', self._onDisableEvent)

        self._legend = list(legend)
        self._prefix = ['', '']
        self._suffix = ['', '']
        # 0 = static (absolute position), 1 = dynamic (relative or weighted position)
        self._postype = 0

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
        # noinspection PyArgumentList
        mapper.SetInputConnection(self._tube.GetOutputPort())

        self._tubeActor.SetMapper(mapper)
        self._tubeActor.GetProperty().SetInterpolationToPhong()
        self._tubeActor.GetProperty().SetRepresentationToSurface()
        self._tubeActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        self._tubeActor.GetProperty().SetOpacity(0.5 * _ALPHA)

        self._cutter = vtkCutter()
        # noinspection PyArgumentList
        self._cutter.SetInputConnection(self._tube.GetOutputPort())

        mapper = vtkDataSetMapper()
        # noinspection PyArgumentList
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
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of LineWidget instance to str
        """
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

    # noinspection PyUnusedLocal
    def _onInteractionEvent(self, widget, event) -> None:
        p1 = self.GetLineRepresentation().GetPoint1WorldPosition()
        p2 = self.GetLineRepresentation().GetPoint2WorldPosition()
        # noinspection PyArgumentList,PyTypeChecker
        self._entryText.SetPosition(p1)
        # noinspection PyArgumentList,PyTypeChecker
        self._targetText.SetPosition(p2)
        data = vtkPolyData()
        self.GetLineRepresentation().GetPolyData(data)
        self._tube.SetInputData(data)
        # noinspection PyArgumentList
        self._tube.Update()

    def _onEndInteractionEvent(self, widget, event) -> None:
        pass

    # noinspection PyUnusedLocal
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
        # noinspection PyArgumentList,PyTypeChecker
        self._entryText.SetPosition(p1)
        # noinspection PyArgumentList,PyTypeChecker
        self._targetText.SetPosition(p2)
        data = vtkPolyData()
        self.GetLineRepresentation().GetPolyData(data)
        self._tube.SetInputData(data)
        # noinspection PyArgumentList
        self._tube.Update()
        # noinspection PyArgumentList
        self._cutter.Update()

    # noinspection PyUnusedLocal
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

    # Public methods

    def updateContourActor(self, plane: vtkPlane) -> None:
        """
        Update tube rendering on a 2D cutting plane. This method is called by private VTK events methods.

        Parameters
        ----------
        plane : vtkPlane
            cutting plane
        """
        if isinstance(plane, vtkPlane):
            plane2 = vtkPlane()
            # noinspection PyArgumentList
            plane2.SetNormal(plane.GetNormal())
            # noinspection PyArgumentList
            plane2.SetOrigin(plane.GetOrigin())
            plane2.Push(0.5)
            self._cutter.SetCutFunction(plane2)
            # noinspection PyArgumentList
            self._cutter.Update()
        else: raise TypeError('parameter type {} is not vtkPlane.'.format(type(plane)))

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current LineWidget instance. The text widget displays a prefix, a name, a suffix
        and a legend.

        Parameters
        ----------
        name : str
            tool text name
        """
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

    def setPrefix(self, txt: tuple[str, str] | list[str] = ('', '')) -> None:
        """
        Set the prefix attribute of the current LineWidget instance. The text widget displays a prefix, a name, a
        suffix and a legend.

        Parameters
        ----------
        txt : tuple[str, str] | list[str]
            - first element, target text prefix (default empty str)
            - second element, entry text prefix (default empty str)
        """
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

    def getPrefix(self) -> list[str]:
        """
        Get the prefix attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        list[str]
            - first element, target text prefix
            - second element, entry text prefix
        """
        return self._prefix

    def setSuffix(self, txt: tuple[str, str] | list[str] = ('', '')) -> None:
        """
        Set the suffix attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        txt : tuple[str, str] | list[str]
            - first element, target text suffix (default empty str)
            - second element, entry text suffix (default empty str)
        """
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

    def getSuffix(self) -> list[str]:
        """
        Get the suffix attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        list[str]
            - first element, target text suffix
            - second element, entry text suffix
        """
        return self._suffix

    def setLegend(self, txt: tuple[str, str] | list[str] = ('', '')) -> None:
        """
        Set the legend attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Parameters
        ----------
        txt : tuple[str, str] | list[str]
            - first element, target text legend (default empty str)
            - second element, entry text legend (default empty str)
        """
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

    def getLegend(self) -> list[str]:
        """
        Get the legend attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        list[str]
            - first element, target text legend
            - second element, entry text legend
        """
        return self._legend

    def setText(self, txt: list[str]) -> None:
        """
        Set the text of the current LineWidget instance. The text widget displays a prefix, a name, a suffix and
        a legend.

        Parameters
        ----------
        list[str]
            - first element, target text
            - second element, entry text
        """
        self._entryText.SetInput(txt[0])
        self._targetText.SetInput(txt[1])

    def getText(self) -> list[str]:
        """
        Get the text attribute of the current LineWidget instance. The text widget displays a prefix, a name,
        a suffix and a legend.

        Returns
        -------
        list[str]
            - first element, target text
            - second element, entry text
        """
        return [self._entryText.GetInput(),
                self._targetText.GetInput()]

    def setFontSize(self, size: int) -> None:
        """
        Set the font size used to display the text of the current LineWidget instance.

        Parameters
        ----------
        size : int
            font size
        """
        if isinstance(size, int):
            self._targetText.GetTextProperty().SetFontSize(size)
            self._entryText.GetTextProperty().SetFontSize(size)
        else: raise TypeError('parameter type {} is not int.'.format(type(size)))

    def getFontSize(self) -> int:
        """
         Get the font size used to display the text of the currentLineWidget instance.

         Returns
         -------
         int
             font size
         """
        return self._targetText.GetTextProperty().GetFontSize()

    def setFontBold(self, v: bool) -> None:
        """
        Display the text of the current LineWidget instance in bold.

        Parameters
        ----------
        v : bool
            displays in bold if True
        """
        if isinstance(v, bool):
            self._targetText.GetTextProperty().SetBold(v)
            self._entryText.GetTextProperty().SetBold(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontBold(self) -> bool:
        """
        Check whether the text of the current LineWidget instance is displayed in bold.

        Returns
        -------
        bool
            True if text displayed in bold
        """
        return self._targetText.GetTextProperty().GetBold() > 0

    def setFontItalic(self, v: bool) -> None:
        """
        Display the text of the current LineWidget instance in italic.

        Parameters
        ----------
        v : bool
            displays in italic if True
        """
        if isinstance(v, bool):
            self._targetText.GetTextProperty().SetItalic(v)
            self._entryText.GetTextProperty().SetItalic(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFontItalic(self) -> bool:
        """
        Check whether the text of the current LineWidget instance is displayed in italic.

        Returns
        -------
        bool
            True if text displayed in italic
        """
        return self._targetText.GetTextProperty().GetItalic() > 0

    def setFontFamily(self, fontname: str = _FFAMILY) -> None:
        """
        Set the font used to display the text of the current LineWidget instance.

        Parameters
        ----------
        fontname : str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        """
        r1 = self._targetText.GetTextProperty()
        r2 = self._entryText.GetTextProperty()
        if fontname in ('Arial', 'Courier', 'Times'):
            r1.SetFontFamilyAsString(fontname)
            r2.SetFontFamilyAsString(fontname)
        else:
            if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
                try:
                    r1.SetFontFamily(VTK_FONT_FILE)
                    r2.SetFontFamily(VTK_FONT_FILE)
                    r1.SetFontFile(fontname)
                    r2.SetFontFile(fontname)
                except:
                    r1.SetFontFamilyAsString('Arial')
                    r2.SetFontFamilyAsString('Arial')
            else:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')

    def getFontFamily(self) -> str:
        """
        Get the font used to display the text of the current LineWidget instance.

        Returns
        -------
        str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        """
        return self._targetText.GetTextProperty().GetFontFamilyAsString()

    def setTextProperty(self, fontname: str = _FFAMILY, bold: bool = False, italic: bool = False) -> None:
        """
         Set the font properties used to display the text of the current LineWidget instance.

         Parameters
         ----------
         fontname : str
             font name 'Arial' (default), 'Courier', 'Times' or font file name
         bold : bool
             True to display in bold (default False)
         italic : bool
             True to display in italic (default False)
         """
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
            if exists(fontname) and splitext(fontname)[1] in ('.ttf', '.otf'):
                try:
                    r1.SetFontFamily(VTK_FONT_FILE)
                    r2.SetFontFamily(VTK_FONT_FILE)
                    r1.SetFontFile(fontname)
                    r2.SetFontFile(fontname)
                except:
                    r1.SetFontFamilyAsString('Arial')
                    r2.SetFontFamilyAsString('Arial')
            else:
                r1.SetFontFamilyAsString('Arial')
                r2.SetFontFamilyAsString('Arial')

    def getTextProperty(self) -> tuple[str, bool, bool]:
        """
        Set the font properties used to display the text of the current HandleWidget instance.

        Returns
        -------
        tuple[str, bool, bool]
            - first element, font name 'Arial' (default), 'Courier', 'Times' or font file name
            - second element, bold ?
            - third element, italic ?
        """
        r = self._targetText.GetTextProperty()
        bold = r.GetBold() > 0
        italic = r.GetItalic() > 0
        fontname = r.GetFontFamilyAsString()
        return fontname, bold, italic

    def setVisibility(self, v: bool) -> None:
        """
        Show/hide the current LineWidget instance.

        Parameters
        ----------
        v : bool
            True to show
        """
        if isinstance(v, bool):
            r = self.GetLineRepresentation()
            if not v:
                # < Revision 21/05/2025
                # self._alpha = r.GetLineProperty().GetOpacity()
                alpha = r.GetLineProperty().GetOpacity()
                if alpha != 0.0: self._alpha = alpha
                # Revision 21/05/2025 >
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
        """
         Get the visibility attribute of the current LineWidget instance.

         Returns
         -------
         bool
             True if visible
         """
        return self._targetText.GetVisibility() > 0

    def setTextOffset(self, r: tuple[int, int] | list[int]) -> None:
        """
        Set the relative position of text in relation to handle in the current LineWidget instance.

        Parameters
        ----------
        r : tuple[int, int] | list[int]
            - first value, x-axis relative position in pixel unit (+ right, - left)
            - second value, y-axis relative position in pixel unit (+ bottom, - top)
        """
        self._targetText.SetDisplayOffset(r[0], r[1])
        self._entryText.SetDisplayOffset(r[0], r[1])

    def getTextOffset(self) -> tuple[int, int]:
        """
         Get the relative position of text in relation to handle in the current LineWidget instance.

         Parameters
         ----------
         tuple[int, int]
             - first value, x-axis relative position in pixel unit (+ right, - left)
             - second value, y-axis relative position in pixel unit (+ bottom, - top)
         """
        return self._targetText.GetDisplayOffset()

    def setTextVisibility(self, v: bool) -> None:
        """
        Show/hide the text of the current LineWidget instance.

        Parameters
        ----------
        v : bool
            True to show text
        """
        if isinstance(v, bool):
            self._targetText.SetVisibility(v)
            self._entryText.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextVisibility(self) -> bool:
        """
        Get the text visibility of the current LineWidget instance.

        Returns
        -------
        bool
            True if text is visible
        """
        return self._targetText.GetVisibility() > 0

    def setTubeVisibility(self, v: bool):
        """
        Show/hide safety zone (tube widget) of the current LineWidget instance.

        Parameters
        ----------
        v : bool
            True to show text
        """
        if isinstance(v, bool):
            if self.isVolumeDisplay(): self._tubeActor.SetVisibility(v)
            else:  self._tubeActor.SetVisibility(False)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTubeVisibility(self) -> bool:
        """
        Get the safety zone (tube widget) visibility of the current LineWidget instance.

        Returns
        -------
        bool
            True if text is visible
        """
        return self._tubeActor.GetVisibility() > 0 or \
            self._contourActor.GetVisibility() > 0

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the color attribute of the current LineWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
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
        """
        Get the color attribute of the current LineWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self.GetLineRepresentation().GetLineProperty().GetColor()

    def setSelectedColor(self, c: vectorFloat3) -> None:
        """
        Set the selected color attribute of the current LineWidget instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
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
        """
        Get the selected color attribute of the current LineWidget instance.

        Returns
        -------
        tuple[float, float, float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self.GetLineRepresentation().GetSelectedLineProperty().GetColor()

    def setPosition1(self, p: vectorFloat3) -> None:
        """
        Set the target point position of the current LineWidget instance.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float]
            target point position in world coordinates
        """
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, float) for i in p]):
                    r = self.GetLineRepresentation()
                    r.SetPoint1WorldPosition(p)
                    # noinspection PyArgumentList
                    self._entryText.SetPosition(p)
                    data = vtkPolyData()
                    r.GetPolyData(data)
                    self._tube.SetInputData(data)
                    # noinspection PyArgumentList
                    self._tube.Update()
                else: raise TypeError('parameter type is not float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition1(self) -> vectorFloat3:
        """
        Get the target point position of the current LineWidget instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            target point position in world coordinates
        """
        return self.GetLineRepresentation().GetPoint1WorldPosition()

    def setPosition2(self, p: vectorFloat3) -> None:
        """
        Set the entry point position of the current LineWidget instance.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float]
            entry point position in world coordinates
        """
        if isinstance(p, (list, tuple)):
            if len(p) == 3:
                if all([isinstance(i, float) for i in p]):
                    r = self.GetLineRepresentation()
                    r.SetPoint2WorldPosition(p)
                    # noinspection PyArgumentList
                    self._targetText.SetPosition(p)
                    data = vtkPolyData()
                    r.GetPolyData(data)
                    self._tube.SetInputData(data)
                    # noinspection PyArgumentList
                    self._tube.Update()
                else: raise TypeError('parameter type is not float.')
            else: raise ValueError('list length {} is not 3.'.format(len(p)))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getPosition2(self) -> vectorFloat3:
        """
        Get the entry point position of the current LineWidget instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            entry point position in world coordinates
        """
        return self.GetLineRepresentation().GetPoint2WorldPosition()

    def getVector(self, length: float = 1.0) -> vectorFloat3:
        """
        Get the direction vector of the current LineWidget instance.

        Parameters
        ----------
        length : float
            vector norm in mm (unit vector, default 1.0)

        Returns
        -------
        list[float]
            direction vector
        """
        r = self.GetLineRepresentation()
        p1 = r.GetPoint1WorldPosition()
        p2 = r.GetPoint2WorldPosition()
        v = list()
        v.append((p1[0] - p2[0]) * length)
        v.append((p1[1] - p2[1]) * length)
        v.append((p1[2] - p2[2]) * length)
        return v

    def setTrajectoryAngles(self, r: vectorFloat2, length: float = 50.0, deg: bool = True) -> None:
        """
        Set the trajectory angles  of the current LineWidget instance.

        There are two angles:

            - sagittal (rotation around x-axis, -180.0° to +180.0°)
            - coronal (rotation around y-axis, -90.0° to +90.0°)

        Parameters
        ----------
        r : tuple[float, float] | list[float]
            - first element, sagittal angle (rotation around x-axis, -180.0° to +180.0°)
            - second element, coronal angle (rotation around y-axis, -90.0° to +90.0°)
        length :  float
            trajectory length in mm (default 50.0)
        deg : bool
            angles in degrees if True (default), in radians otherwise
        """
        trf = SisypheTransform()
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
        """
        Get the trajectory angles  of the current LineWidget instance.

        There are two angles:

            - sagittal (rotation around x-axis, -180.0° to +180.0°)
            - coronal (rotation around y-axis, -90.0° to +90.0°)

        Parameters
        ----------
        deg : bool
            angles in degrees if True (default), in radians otherwise

        Returns
        -------
        list[float]
            - first element, sagittal angle
            - second element, coronal angle
        """
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
        Extend/reduce LineWidget length on the target side.

        Parameters
        ----------
        mm : float
            - reduce or + extend in mm
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
        Extend/reduce LineWidget length on the entry side.

        Parameters
        ----------
        mm : float
            - reduce or + extend in mm
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

    def extendPosition1ToPlane(self, plane: vtkPlane | vtkImageSlice | SliceViewWidget) -> None:
        """
        Projecting the target point of the current LineWidget instance onto a plane along the trajectory direction.

        Parameters
        ----------
        plane : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            projection plane
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(plane, SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            t = vtkmutable(0.0)
            p = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            # noinspection PyTypeChecker
            plane.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, p)
            self.setPosition1(p)

    def extendPosition2ToPlane(self, plane: vtkPlane | vtkImageSlice | SliceViewWidget) -> None:
        """
        Projecting the entry point of the current LineWidget instance onto a plane along the trajectory direction.

        Parameters
        ----------
        plane : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            projection plane
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(plane, SliceViewWidget): plane = plane.getVtkImageSliceVolume()
        if isinstance(plane, vtkImageSlice): plane = plane.GetMapper().GetSlicePlane()
        if isinstance(plane, vtkPlane):
            t = vtkmutable(0.0)
            p = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            # noinspection PyTypeChecker
            plane.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, p)
            self.setPosition2(p)

    def extendPosition1ToMeshSurface(self, mesh: SisypheMesh) -> int:
        """
        Projecting the target point of the current LineWidget instance onto a mesh surface along the trajectory direction.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            projection mesh

        Returns
        -------
        int
            number of intersections (0 if no intersection)
        """
        if isinstance(mesh, SisypheMesh):
            f = vtkOBBTree()
            # noinspection PyTypeChecker
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
            if inter != 0:
                n = ps.GetNumberOfPoints()
                if n > 0:
                    d = list()
                    for i in range(n):
                        pr = ps.GetPoint(i)
                        d.append(sqrt((p[0] - pr[0])**2 + (p[1] - pr[1])**2 + (p[2] - pr[2])**2))
                    self.setPosition1(ps.GetPoint(d.index(min(d))))
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshSurface(self, mesh: SisypheMesh) -> int:
        """
        Projecting the entry point of the current LineWidget instance onto a mesh surface
        along the trajectory direction.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            projection mesh

        Returns
        -------
        int
            number of intersections (0 if no intersection)
        """
        if isinstance(mesh, SisypheMesh):
            f = vtkOBBTree()
            # noinspection PyTypeChecker
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
                    # < Revision 07/03/2025
                    # self.setPosition2(ps.getPoint(d.index(min(d))))
                    self.setPosition2(ps.GetPoint(d.index(min(d))))
                    # Revision 07/03/2025
            return inter
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition1ToMeshCenterOfMass(self, mesh: SisypheMesh) -> None:
        """
        Move the target point of the current LineWidget instance to the center of mass of a mesh.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to use
        """
        if isinstance(mesh, SisypheMesh):
            p = mesh.getCenterOfMass()
            self.setPosition1(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshCenterOfMass(self, mesh: SisypheMesh) -> None:
        """
        Move the entry point of the current LineWidget instance to the center of mass of a mesh.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to use
        """
        if isinstance(mesh, SisypheMesh):
            p = mesh.getCenterOfMass()
            self.setPosition2(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition1ToMeshCenter(self, mesh: SisypheMesh) -> None:
        """
        Move the target point of the current LineWidget instance to the center of a mesh (vtk.vtkActor center).

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to use
        """
        if isinstance(mesh, SisypheMesh):
            p = mesh.getActor().GetCenter()
            self.setPosition1(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def extendPosition2ToMeshCenter(self, mesh: SisypheMesh) -> None:
        """
        Move the entry point of the current LineWidget instance to the center of a mesh (vtk.vtkActor center).

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to use
        """
        if isinstance(mesh,  SisypheMesh):
            p = mesh.getActor().GetCenter()
            self.setPosition2(p)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def setLineWidth(self, width: float) -> None:
        """
        Set the line width attribute of the current LineWidget instance.

        Parameters
        ----------
        width : float
            line width
        """
        if isinstance(width, float):
            r = self.GetLineRepresentation()
            r.GetLineProperty().SetLineWidth(width)
            r.GetSelectedLineProperty().SetLineWidth(width)
        else: raise TypeError('parameter type {} is not float'.format(type(width)))

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current LineWidget instance.

        Returns
        -------
        float
            line width
        """
        return self.GetLineRepresentation().GetLineProperty().GetLineWidth()

    def setPointSize(self, size: float) -> None:
        """
        Set the size of the target and entry points of the current LineWidget instance.

        Parameters
        ----------
        size : float
            target and entry points size in mm
        """
        if isinstance(size, float):
            r = self.GetLineRepresentation()
            r.GetEndPointProperty().SetPointSize(size)
            r.GetEndPoint2Property().SetPointSize(size)
            r.GetSelectedEndPointProperty().SetPointSize(size)
            r.GetSelectedEndPoint2Property().SetPointSize(size)
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getPointSize(self) -> float:
        """
        Set the size of the target and entry points of the current LineWidget instance.

        Returns
        -------
        float
            target and entry points size in mm
        """
        return self.GetLineRepresentation().GetEndPointProperty().GetPointSize()

    def setHandleSize(self, size: float) -> None:
        """
        Set the handle size attribute of the current LineWidget instance.

        Parameters
        ----------
        size : float
            handle size
        """
        if isinstance(size, float):
            r = self.GetLineRepresentation()
            r.GetPoint1Representation().SetHandleSize(size)
            r.GetPoint2Representation().SetHandleSize(size)
            r.GetLineHandleRepresentation().SetHandleSize(size)
        else: raise TypeError('parameter type {} is not float'.format(type(size)))

    def getHandleSize(self) -> float:
        """
        Get the handle size attribute of the current LineWidget instance.

        Returns
        -------
        float
            handle size
        """
        return self.GetLineRepresentation().GetLineHandleRepresentation().GetHandleSize()

    def setHandleLineWidth(self, size: float) -> None:
        """
         Set the handle line width attribute of the current LineWidget instance.

         Parameters
         ----------
         size : float
             handle line width
         """
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
        """
        Get the handle line width attribute of the current LineWidget instance.

        Returns
        -------
        float
            handle line width
        """
        return self.GetLineRepresentation().GetLineHandleRepresentation().GetProperty().GetLineWidth()

    def setOpacity(self, alpha: float) -> None:
        """
         Set the opacity attribute of the current LineWidget instance.

         Parameters
         ----------
         alpha : float
             opacity between 0.0 (transparent) to 1.0 (opaque)
         """
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
        """
        Get the opacity attribute of the current LineWidget instance.

        Returns
        -------
        float
            opacity between 0.0 (transparent) to 1.0 (opaque)
        """
        return self.GetLineRepresentation().GetLineProperty().GetOpacity()

    def setTolerance(self, tol: int) -> None:
        """
        Set the tolerance attribute of the current LineWidget instance. Distance tolerance (in pixels) between tool
        and mouse cursor for interaction.

        Parameters
        ----------
        tol : int
            tolerance in pixels
        """
        if isinstance(tol, int):
            self.GetLineRepresentation().SetTolerance(tol)
        else: raise TypeError('parameter type {} is not int'.format(type(tol)))

    def getTolerance(self) -> int:
        """
        Get the tolerance attribute of the current LineWidget instance. Distance tolerance (in pixels) between tool
        and mouse cursor for interaction.

        Returns
        -------
        int
            tolerance in pixels
        """
        return self.GetLineRepresentation().GetTolerance()

    def setRenderLineAsTube(self, v: bool) -> None:
        """
        Enable/disable rendering line of the current LineWidget instance as tube.

        Parameters
        ----------
        v : bool
            render line as tube if True
        """
        if isinstance(v, bool):
            self.GetLineRepresentation().GetLineProperty().SetRenderLinesAsTubes(v)
            self.GetLineRepresentation().GetSelectedLineProperty().SetRenderLinesAsTubes(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getRenderLineAsTube(self) -> bool:
        """
        Check whether the line of the current LineWidget instance is rendered as tube.

        Returns
        -------
        bool
            True if render line as tube
        """
        return self.GetLineRepresentation().GetLineProperty().GetRenderLinesAsTubes() > 0

    def setRenderPointsAsSpheres(self, v: bool) -> None:
        """
        Enable/disable rendering points (target/entry) of the current LineWidget instance as sphere.

        Parameters
        ----------
        v : bool
            render point as sphere if True
        """
        if isinstance(v, bool):
            self.GetLineRepresentation().GetEndPointProperty().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetSelectedEndPointProperty().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetEndPoint2Property().SetRenderPointsAsSpheres(v)
            self.GetLineRepresentation().GetSelectedEndPoint2Property().SetRenderPointsAsSpheres(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getRenderPointsAsSpheres(self) -> bool:
        """
        Check whether the points (target/entry) of the current LineWidget instance are rendered as spheres.

        Returns
        -------
        bool
            True if render point as sphere
        """
        return self.GetLineRepresentation().GetEndPointProperty().GetRenderPointsAsSpheres() > 0

    def setInterpolation(self, inter: int) -> None:
        """
        Set the shading interpolation method of the current LineWidget instance, as int code.

        Parameters
        ----------
        inter : int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
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
        """
        Get the shading interpolation method (as int code) of the current LineWidget instance.

        Returns
        -------
        int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
        return self.GetLineRepresentation().GetLineProperty().GetInterpolation()

    def setTubeRadius(self, radius: float) -> None:
        """
        Set the safety zone radius (tube widget) of the current LineWidget instance.

        Parameters
        ----------
        radius : float
            safety zone radius in mm
        """
        if isinstance(radius, float):
            self._tube.SetRadius(radius)
            # noinspection PyArgumentList
            self._tube.Update()
        else: raise TypeError('parameter type {} is not float.'.format(type(radius)))

    def getTubeRadius(self) -> float:
        """
        Get the safety zone radius (tube widget) of the current LineWidget instance.

        Returns
        -------
        float
            safety zone radius in mm
        """
        return self._tube.GetRadius()

    def setMetallic(self, v: float) -> None:
        """
        Set the metallic coefficient of the current LineWidget instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Parameters
        ----------
        v : float
        """
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
        """
        Get the metallic coefficient of the current LineWidget instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Returns
        -------
        float
        """
        return self.GetLineRepresentation().GetLineProperty().GetMetallic()

    def setRoughness(self, v: float) -> None:
        """
        Set the roughness coefficient of the current LineWidget instance. This value has to be between 0.0 (glossy) and
        1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Parameters
        ----------
        v : float
            between 0.0 (glossy) and 1.0 (rough)
        """
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
        """
        Get the roughness coefficient of the current LineWidget instance. This value has to be between 0.0 (glossy) and
        1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Returns
        -------
        float
            between 0.0 (glossy) and 1.0 (rough)
        """
        return self.GetLineRepresentation().GetLineProperty().GetRoughness()

    def setAmbient(self, v: float) -> None:
        """
        Set the ambient lighting coefficient of the current LineWidget instance.

        Parameters
        ----------
        v : float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
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
        """
        Get the ambient lighting coefficient of the current LineWidget instance.

        Returns
        -------
        float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
        return self.GetLineRepresentation().GetLineProperty().GetAmbient()

    def setSpecular(self, v: float) -> None:
        """
        Set the specular lighting coefficient of the current LineWidget instance.

        Parameters
        ----------
        v : float
            specular lighting coefficient (between 0.0 and 1.0)
        """
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
        """
        Get the specular lighting coefficient of the current LineWidget instance.

        Returns
        -------
        float
            specular lighting coefficient (between 0.0 and 1.0)
        """
        return self.GetLineRepresentation().GetLineProperty().GetSpecular()

    def setSpecularPower(self, v: float) -> None:
        """
        Set the specular power of the current LineWidget instance.

        Parameters
        ----------
        v : float
            specular power (between 0.0 and 50.0)
        """
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
        """
        Get the specular power of the current LineWidget instance.

        Returns
        -------
        float
            specular power (between 0.0 and 50.0)
        """
        return self.GetLineRepresentation().GetLineProperty().GetSpecularPower()

    def setTubeProperties(self, p: vtkProperty) -> None:
        """
        Set the safety zone (tube widget) properties of the current LineWidget instance.

        Parameters
        ----------
        p : vtkProperty
            tube properties
        """
        if isinstance(p, vtkProperty): self._tubeActor.SetProperty(p)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(p)))

    def getTubeProperties(self) -> vtkProperty:
        """
        Get the safety zone (tube widget) properties of the current HandleWidget instance.

        Returns
        -------
        vtkProperty
            tube properties
        """
        return self._tubeActor.GetProperty()

    def deepCopy(self) -> LineWidget:
        """
        Deep copy of the current LineWidget instance.

        Returns
        -------
        LineWidget
            line copy
        """
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
        # noinspection PyArgumentList
        r.SetLineColor(self.GetLineRepresentation().GetLineColor())
        # noinspection PyTypeChecker
        r.SetPoint1WorldPosition(self.GetLineRepresentation().GetPoint1WorldPosition())
        # noinspection PyTypeChecker
        r.SetPoint2WorldPosition(self.GetLineRepresentation().GetPoint2WorldPosition())
        widget = LineWidget(self.getName())
        widget.SetRepresentation(r)
        widget.copyAttributesFrom(self)
        return widget

    def copyAttributesTo(self, tool: LineWidget) -> None:
        """
        Copy the current LineWidget instance attributes to another LineWidget.

        Parameters
        ----------
        tool : LineWidget
            copy attributes to this widget
        """
        if isinstance(tool, LineWidget):
            tool.setText(self.getText())
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
        """
        Set the current LineWidget instance attributes from another LineWidget.

        Parameters
        ----------
        tool : LineWidget
            copy attributes from this widget
        """
        if isinstance(tool, LineWidget):
            self.setText(tool.getText())
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
        """
        Set default representation (size, color, font, opacity...) of the current LineWidget instance.
        """
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

    def isStatic(self) -> bool:
        """
        Check whether the current HandleWidget instance is static i.e. absolute position

        Returns
        -------
        bool
            True if static
        """
        return self._postype == 0

    def isDynamic(self) -> bool:
        """
        Check whether the current HandleWidget instance is dynamic i.e. position processed from other tools (relative or
        weighted position)

        Returns
        -------
        bool
            True if dynamic
        """
        return self._postype == 1

    def setStatic(self) -> None:
        """
        Set the current HandleWidget instance as static i.e. absolute position.
        """
        self._postype = 0

    def setDynamic(self) -> None:
        """
        Set the current HandleWidget instance as dynamic i.e. position processed from other tools (relative or weighted
        position).
        """
        self._postype = 1

    # Various distance methods

    def getLength(self) -> float:
        """
        Get the trajectory length of the current LineWidget instance.

        Returns
        -------
        float
            trajectory length in mm
        """
        p1 = self.GetLineRepresentation().GetPoint1WorldPosition()
        p2 = self.GetLineRepresentation().GetPoint2WorldPosition()
        return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

    def getDistancesToPoint(self, p: vectorFloat3) -> list[float]:
        """
        Get some distances between a point and the current LineWidget instance.

        Parameters
        ----------
        p  : tuple[float, float, float] | list[float]
            point cooridnates

        Returns
        -------
        list[float]
            - first element, distance between parameter point and target point
            - second element, distance between parameter point and entry point
            - third element, minimum distance between parameter point and line
        """
        r = list()
        p1 = self.getPosition1()
        p2 = self.getPosition2()
        r.append(sqrt((p1[0] - p[0])**2 + (p1[1] - p[1])**2 + (p1[2] - p[2])**2))
        r.append(sqrt((p2[0] - p[0])**2 + (p2[1] - p[1])**2 + (p2[2] - p[2])**2))
        line = vtkLine()
        r.append(sqrt(line.DistanceToLine(p, p1, p2)))
        return r

    def getDistancesToHandleWidget(self, hw: HandleWidget) -> list[float]:
        """
        Get some distances between a HandleWidget and the current LineWidget instance.

        Parameters
        ----------
        hw : HandleWidget
            point coordinates

        Returns
        -------
        list[float]
            - first element, distance between handle parameter and target point
            - second element, distance between handle parameter and entry point
            - third element, minimum distance between handle parameter and line
        """
        if isinstance(hw, HandleWidget):
            return self.getDistancesToPoint(hw.getPosition())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(hw)))

    def getLineToLineDistance(self, p1: vectorFloat3, p2: vectorFloat3) -> float:
        """
        Get the distance between a line and the current LineWidget instance.

        Parameters
        ----------
        p1 : tuple[float, float, float] | float[float, float, float]
            point coordinates
        p2 : tuple[float, float, float] | float[float, float, float]
            point coordinates, these two points define the line

        Returns
        -------
        float
            minimal perpendicular distance metric between two line segments
        """
        sp1 = self.getPosition1()
        sp2 = self.getPosition2()
        return lee_perpendicular_distance(sp1, sp2, p1, p2)

    def getDistancesToLine(self, p1: vectorFloat3, p2: vectorFloat3) -> list[float | vectorFloat3]:
        """
        Get some distances between a line and the current LineWidget instance.

        Parameters
        ----------
        p1 : tuple[float, float, float] | float[float, float, float]
            point coordinates
        p2 : tuple[float, float, float] | float[float, float, float]
            point coordinates, these two points define the line

        Returns
        -------
        list[float | list[float]]
            - first element, distance between line parameter and target point
            - second element, distance between line parameter and entry point
            - third element, distance between line parameter and LineWidget line
            - fourth element, distance between p1 parameter and target point
            - fifth element, distance between p1 parameter and entry point
            - sixth element, distance between p2 parameter and target point
            - seventh element, distance between p2 parameter and entry point
            - ninth element, coordinates of the closest point on line parameter
            - tenth element, coordinates of the closest point on LineWidget line
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
        # noinspection PyTypeChecker
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

    def getDistancesToLineWidget(self, lw: LineWidget) -> list[float | vectorFloat3]:
        """
        Get some distances between a LineWidget and the current LineWidget instance.

        Parameters
        ----------
        lw : LineWidget
            line

        Returns
        -------
        list[float | list[float]]
            - first element, distance between LineWidget parameter and current target point
            - second element, distance between LineWidget parameter and current entry point
            - third element, distance between LineWidget parameter and current LineWidget line
            - fourth element, distance between LineWidget target parameter and current target point
            - fifth element, distance between LineWidget target parameter and current entry point
            - sixth element, distance between LineWidget entry parameter and current target point
            - seventh element, distance between LineWidget entry parameter and current entry point
            - ninth element, coordinates of the closest point on LineWidget parameter
            - tenth element, coordinates of the closest point on current LineWidget line
        """
        if isinstance(lw, LineWidget):
            return self.getDistancesToLine(lw.getPosition1(), lw.getPosition2())
        else: raise TypeError('parameter type {} is not HandleWidget.'.format(type(lw)))

    def getDistancesToPlane(self, p: vtkPlane | vtkImageSlice | SliceViewWidget) -> list[float | vectorFloat3]:
        """
        Get some distances between a plane and the current LineWidget instance.

        Parameters
        ----------
        p : vtk.vtkPlane | vtk.vtkImageSlice | Sisyphe.widgets.sliceViewWidgets.SliceViewWidget
            plane

        Returns
        -------
        list[float | list[float]]
            - first element, distance between plane parameter and target point
            - second element, distance between plane parameter and entry point
            - third element, coordinates of the line projection on the plane
        """
        from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
        if isinstance(p, SliceViewWidget): p = p.getVtkImageSliceVolume()
        if isinstance(p, vtkImageSlice): p = p.GetMapper().GetSlicePlane()
        if isinstance(p, vtkPlane):
            r = list()
            r.append(p.DistanceToPlane(self.getPosition1()))
            r.append(p.DistanceToPlane(self.getPosition2()))
            t = vtkmutable(0.0)
            pp = [0.0, 0.0, 0.0]
            # alternative syntax (point1, point2, normal, origin, float, [0.0, 0.0, 0.0])
            # noinspection PyTypeChecker
            p.IntersectWithLine(self.getPosition1(), self.getPosition2(), t, pp)
            r.append(pp)
            return r
        else: raise TypeError('parameter type {} is not SliceViewWidget, vtkImageSlice or vtkPlane.'.format(type(p)))

    # IO methods

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
        Write the current LineWidget instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        currentnode : minidom.Element
            xml root node
        """
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
        """
        Read the current LineWidget instance attributes from xml document instance.

        Parameters
        ----------
        currentnode : minidom.Element
            xml root node
        """
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
        """
        Read the current LineWidget instance attributes from xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                tool = doc.getElementsByTagName('line')
                if tool is not None: self.parseXMLNode(tool[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        """
        Save the current LineWidget instance to a PySisyphe Trajectory tool (.xline) file.

        Parameters
        ----------
        filename : str
            PySisyphe Trajectory tool file name
        """
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
        """
        Load the current LineWidget instance from a PySisyphe Trajectory tool (.xline) file.

        Parameters
        ----------
        filename : str
            PySisyphe Trajectory tool file name
        """
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
    Description
    ~~~~~~~~~~~

    Named list container of tool instances. Container key to address elements can be an int index or a str name.

    Scope of methods:

        - getter/setter methods

            - reference ID, all tools in the container are defined in the space of a reference SisypheVolume whose ID is the reference ID.
            - file name

        - container methods
        - display properties of the tool elements
        - tool element creation
        - IO methods

    Inheritance
    ~~~~~~~~~~~

    object -> ToolWidgetCollection

    Creation: 05/04/2022
    Last revision: 19/12/2023
    """

    __slots__ = ['_referenceID', '_filename', '_tools', '_index', '_color',
                 '_scolor', '_lwidth', '_alpha', '_ffamily', '_fsize', '_interactor']

    _FILEEXT = '.xtools'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get ToolWidgetCollection file extension.

        Returns
        -------
        str
            '.xtools'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get ToolWidgetCollection filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe tool collection (.xtools)'
        """
        return 'PySisyphe tool collection (*{})'.format(cls._FILEEXT)

    # Special method

    def __init__(self,
                 volume: SisypheVolume | None = None,
                 interactor: vtkRenderWindowInteractor | None = None) -> None:
        """
        ToolWidgetCollection instance constructor.

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume | None
            reference volume (default None)
        interactor : vtk.vtkRenderWindowInteractor | None
            vtkRenderWindowInteractor of the tool widgets in the container (default None)
        """
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
        if isinstance(volume, SisypheVolume):
            self._referenceID = volume.getID()
            if volume.hasFilename():
                filename, ext = splitext(volume.getFilename())
                filename += self._FILEEXT
        else:
            self._referenceID = None
            self._filename = ''

    # Container special methods

    def __getitem__(self, key: int | str) -> NamedWidget:
        """
        Special overloaded container getter method. Get a tool element from container, key which can be an int index or
        a name attribute.

        Parameters
        ----------
        key : int | str
            - int, index
            - str, tool name

        Returns
        -------
        NamedWidget
            tool widget
        """
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
        """
        Special overloaded container setter method. Set a tool element in the container.

        Parameters
        ----------
        key : int
            index
        value : NamedWidget
            tool widget to be placed at key position
        """
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
        """
        Special overloaded method called by the built-in del() python function. Delete a tool element in the container.

        Parameters
        ----------
        key : int | str |  NamedWidget,
            - int, index
            - str, tool name
            - NamedWidget, tool name attribute of the NamedWidget
        """
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
        """
        Special overloaded method called by the built-in len() python function. Returns the number of tool elements in
        the container.

        Returns
        -------
        int
            number of tool elements
        """
        return len(self._tools)

    def __contains__(self, value: str | NamedWidget) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a tool is in
        the container.

        Parameters
        ----------
        value : str | NamedWidget
            - str, tool name
            - SisypheMesh, tool name attribute of the NamedWidget

        Returns
        -------
        bool
            True if value is in the container.
        """
        keys = [k.getName() for k in self._tools]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is NamedWidget
        elif isinstance(value, NamedWidget):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or NamedWidget.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> NamedWidget:
        """
        Special overloaded container called by the built-in 'next()' python iterator method. Returns the next value for
        the iterable.
        """
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
        """
        Checks if ToolWidgetCollection instance container is empty.

        Returns
        -------
        bool
            True if empty
        """
        return len(self._tools) == 0

    def count(self) -> int:
        """
        Get the number of tool elements in the
        current ToolWidgetCollection instance container.

        Returns
        -------
        int
            number of tool elements
        """
        return len(self._tools)

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current ToolWidgetCollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        # return list of keys (widget name)
        return [k.getName() for k in self._tools]

    def remove(self, value: NamedWidget) -> None:
        """
        Remove a tool element from the current ToolWidgetCollection instance container.

        Parameters
        ----------
        value : int | str | NamedWidget
            - int, index of the tool to remove
            - str, tool name of the NamedWidget to remove
            - NamedWidget to remove
        """
        # value is NamedWidget
        if isinstance(value, NamedWidget):
            self._tools.remove(value)
        # value is NamedWidget, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or NamedWidget.'.format(type(value)))

    def pop(self, key: int | str | NamedWidget | None = None):
        """
        Remove a tool element from the current ToolWidgetCollection instance container and return it. If key is None,
        removes and returns the last element.

        Parameters
        ----------
        key : int | str | NamedWidget | None
            - int, index of the tool to remove
            - str, tool name of the NamedWidget to remove
            - NamedWidget to remove
            - None, remove the last element

        Returns
        -------
        NamedWidget
            element removed from the container
        """
        if key is None: return self._tools.pop()
        # key is Name str or NamedWidget
        if isinstance(key, (str, NamedWidget)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._tools.pop(key)
        else: raise TypeError('parameter type {} is not int, str or NamedWidget.'.format(type(key)))

    def index(self, value: str | NamedWidget):
        """
        Index of a tool element in the current ToolWidgetCollection instance container.

        Parameters
        ----------
        value : str | NamedWidget
            tool name or NamedWidget

        Returns
        -------
        int
            index
        """
        keys = [k.getName() for k in self._tools]
        # value is NamedWidget
        if isinstance(value, NamedWidget):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or NamedWidget.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current ToolWidgetCollection instance container.
        """
        self._tools.reverse()

    def append(self, value: NamedWidget):
        """
        Append a tool element in the current ToolWidgetCollection instance container.

        Parameters
        ----------
        value : NamedWidget
            tool to append
        """
        if isinstance(value, NamedWidget):
            if value.getName() not in self: self._tools.append(value)
            else: self._tools[self.index(value)] = value
        else: raise TypeError('parameter type {} is not NamedWidget.'.format(type(value)))

    def insert(self, key: int | str | NamedWidget, value: NamedWidget):
        """
        Insert a tool element at the position given by the key in the current ToolWidgetCollection instance container.

        Parameters
        ----------
        key : int | str | NamedWidget
            - int, index
            - str, tool name index
            - NamedWidget, tool index
        value : NamedWidget
            tool to insert
        """
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
        """
        Remove all elements from the current ToolWidgetCollection instance container (empty).
        """
        self._tools.clear()

    def sort(self, reverse: bool = False) -> None:
        """
        Sort elements of the current ToolWidgetCollection instance container. Sorting is based on the name attribute of
        the tool elements, in the ascending order.

        Parameters
        ----------
        reverse : bool
            sorting in reverse order
        """
        def _getName(item):
            return item.getName()

        self._tools.sort(reverse=reverse, key=_getName)

    def copy(self) -> ToolWidgetCollection:
        """
        Copy the current ToolWidgetCollection instance container (Shallow copy of elements).

        Returns
        -------
        ToolWidgetCollection
            shallow copy collection
        """
        tools = ToolWidgetCollection()
        for tool in self._tools:
            tools.append(tool)
        return tools

    def copyToList(self) -> list[NamedWidget]:
        """
        Copy the current ToolWidgetCollection instance container to a list (Shallow copy of elements).

        Returns
        -------
        list[NamedWidget]
            shallow copy collection
        """
        tools = self._tools.copy()
        return tools

    def getList(self) -> list[NamedWidget]:
        """
        Get the list attribute of the current ToolWidgetCollection instance container (Shallow copy of the elements).

        Returns
        -------
        list[NamedWidget]
            shallow copy collection
        """
        return self._tools

    # Public methods

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current ToolWidgetCollection instance. All tools in the container are defined
        in the space of a reference SisypheVolume whose ID is the reference ID.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def setReferenceID(self, ID: str | SisypheVolume) -> None:
        """
        Set reference ID attribute of the current ToolWidgetCollection instance. All tools in the container are defined
        in the space of a reference SisypheVolume whose ID is the reference ID.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            - str, ID
            - Sisyphe.core.sisypheVolume.SisypheVolume, ID attribute of the SisypheVolume
        """
        if isinstance(ID, str): self._referenceID = ID
        elif isinstance(ID, SisypheVolume): self._referenceID = ID.getID()
        else: self._referenceID = None

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID attribute of the current ToolWidgetCollection instance is defined (not empty str).

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID is not None

    def hasSameID(self, ID: str | SisypheVolume):
        """
        Check that the ID parameter is identical to the ID attribute of the current ToolWidgetCollection instance.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume

        Returns
        -------
        bool
            True if IDs are identical
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str): return ID == self._referenceID
        else: raise TypeError('parameter type {} is not str or SisypheVolume'.format(type(ID)))

    def hasFilename(self) -> bool:
        """
        Check if the file name attribute of the current ToolWidgetCollection instance is defined (not empty str).

        Returns
        -------
        bool
            True if file name is defined
        """
        if self._filename != '':
            if exists(self._filename):
                return True
            else:
                self._filename = ''
        return False

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current ToolWidgetCollection instance.

        Returns
        -------
        str
            file name
        """
        return self._filename

    def setFilenameFromVolume(self, img: SisypheVolume) -> None:
        """
        Set the file name attribute of the current ToolWidgetCollection instance from a volume.

        Parameters
        ----------
        img : Sisyphe.core.sisypheVolume.SisypheVolume
        """
        if isinstance(img, SisypheVolume):
            if img.hasFilename():
                path, ext = splitext(img.getFilename())
                path += self._FILEEXT
                self._filename = path
            else: self._filename = ''
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(img)))

    def setColor(self, c: vectorFloat3) -> None:
        """
        Set the tool elements color of the current ToolWidgetCollection instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        if isinstance(c, (list, tuple)):
            if all([0.0 <= i <= 1.0 for i in c]):
                self._color = c
                if self.count() > 0:
                    for tool in self._tools:
                        tool.setColor(c)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(c))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getColor(self) -> vectorFloat3:
        """
        Get the tool elements color of the current ToolWidgetCollection instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self._color

    def setSelectedColor(self, c: vectorFloat3):
        """
        Set the tool elements selected color of the current ToolWidgetCollection instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        if isinstance(c, (list, tuple)):
            if all([0.0 <= i <= 1.0 for i in c]):
                self._scolor = c
                for tool in self._tools:
                    tool.setSelectedColor(c)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(c))
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(c)))

    def getSelectedColor(self) -> vectorFloat3:
        """
        Get the tool elements selected color of the current ToolWidgetCollection instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            color, red, green, blue components (between 0.0 and 1.0)
        """
        return self._scolor

    def setOpacity(self, v: float) -> None:
        """
        Set the tool elements opacity of the current ToolWidgetCollection instance.

        Parameters
        ----------
        v : float
            opacity (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._alpha = v
                if self.count() > 0:
                    for tool in self._tools:
                        tool.setOpacity(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self) -> float:
        """
        Get the tool elements opacity of the current ToolWidgetCollection instance.

        Returns
        -------
        float
            opacity (between 0.0 and 1.0)
        """
        return self._alpha

    def setLineWidth(self, v: float) -> None:
        """
        Set the tool elements line width of the current ToolWidgetCollection instance.

        Parameters
        ----------
        v : float
            line width
        """
        if isinstance(v, float):
            self._lwidth = v
            if self.count() > 0:
                for tool in self._tools:
                    tool.setLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getLineWidth(self) -> float:
        """
        Get the tool elements line width of the current ToolWidgetCollection instance.

        Returns
        ----------
        float
            line width
        """
        return self._lwidth

    def setFontFamily(self, v: str = _FFAMILY) -> None:
        """
        Set the font used to display the tool elements text of the current ToolWidgetCollection instance.

        Parameters
        ----------
        v : str
            font name 'Arial' (default), 'Courier', 'Times' or ttf font file name (*.ttf)
        """
        if isinstance(v, str):
            self._ffamily = v
            if self.count() > 0:
                for tool in self._tools:
                    if not isinstance(tool, BoxWidget):
                        tool.setTextProperty(fontname=self._ffamily)
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def getFontFamily(self) -> str:
        """
        Get the font used to display the tool elements text of the current ToolWidgetCollection instance.

        Returns
        -------
        str
            font name 'Arial' (default), 'Courier', 'Times' or font file name
        """
        return self._ffamily

    def setInteractor(self, interactor: vtkRenderWindowInteractor) -> None:
        """
        Set the interactor attribute of the current ToolWidgetCollection instance. vtk.vtkRenderWindowInteractor manage
        vtk events of the tool widgets.

        Parameters
        ----------
        interactor : vtk.vtkRenderWindowInteractor
            interactor to copy
        """
        if isinstance(interactor, vtkRenderWindowInteractor):
            self._interactor = interactor
        else: raise TypeError('parameter type {} is not vtkRenderWindowInteractor.'.format(type(interactor)))

    def hasInteractor(self) -> bool:
        """
        Check whether the interactor attribute of the current ToolWidgetCollection instance is defined (not None).
        vtk.vtkRenderWindowInteractor manage vtk events of the tool widgets.

        Returns
        -------
        bool
            True if interactor is defined
        """
        return self._interactor is not None

    def newDistanceWidget(self, name: str = '') -> DistanceWidget:
        """
        Create a new DistanceWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        name : str
            tool name (default empty str)

        Returns
        -------
        DistanceWidget
            new widget
        """
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
        """
        Create a new OrthogonalDistanceWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        name : str
            tool name (default empty str)

        Returns
        -------
        OrthogonalDistanceWidget
            new widget
        """
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
        """
        Create a new AngleWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        name : str
            tool name (default empty str)

        Returns
        -------
        AngleWidget
            new widget
        """
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
        """
        Create a new BoxWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        p : tuple[float, float] | list[float]
            widget position, top/left corner, vtk display 2D coordinates
        name : str
            tool name (default empty str)

        Returns
        -------
        BoxWidget
            new widget
        """
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
        """
        Create a new TextWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        p : tuple[float, float] | list[float]
            widget position, vtk display 2D coordinates
        text : str
            widget text attribute
        name : str
            tool name (default empty str)

        Returns
        -------
        TextWidget
            new widget
        """
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
        """
        Create a new HandleWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float]
            widget position, world coordinates
        name : str
            tool name (default empty str)

        Returns
        -------
        HandleWidget
            new widget
        """
        if self.hasInteractor():
            if name == '': name = 'Target#' + str(len(self._tools) + 1)
            widget = HandleWidget(name)
            widget.setPosition(p)
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def newLineWidget(self, p1: vectorFloat3, p2: vectorFloat3, name: str = '') -> LineWidget:
        """
        Create a new LineWidget instance and addBundle it to the current ToolWidgetCollection.

        Parameters
        ----------
        p1 : tuple[float, float, float] | list[float]
            target point position, world coordinates
        p2 : tuple[float, float, float] | list[float]
            entry point position, world coordinates
        name : str
            tool name (default empty str)

        Returns
        -------
        LineWidget
            new widget
        """
        if self.hasInteractor():
            if name == '': name = 'Trajectory#' + str(len(self._tools) + 1)
            widget = LineWidget(name)
            widget.setPosition1(p1)
            widget.setPosition2(p2)
            widget.SetInteractor(self._interactor)
            self.append(widget)
            return widget
        else: raise AttributeError('interactor attribute is not defined.')

    def select(self, key: int | str) -> None:
        """
        Select a tool element of the current ToolWidgetCollection. This tool is displayed with the selected color.

        Parameters
        ----------
        key : int | str
            - int, index
            - str, tool name
        """
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

    # IO Public methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current ToolWidgetCollection instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
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
        """
        Read the current oolWidgetCollection instance attributes from xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
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
        """
        Save the current ToolWidgetCollection instance to a PySisyphe tool collection (.xtools) file.

        Parameters
        ----------
        filename : str
            PySisyphe tool collection file name
        """
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
        """
        Save the current ToolWidgetCollection instance to a PySisyphe tool collection (.xtools) file. If the filename
        parameter is empty (default), the file name attribute of the current ToolWidgetCollection instance is used.

        Parameters
        ----------
        filename : str
            PySisyphe tool collection file name
        """
        if not self.isEmpty():
            if self.hasFilename():
                filename = self._filename
            if filename != '':
                self.saveAs(filename)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('ToolWidgetCollection instance is empty.')

    def load(self, filename: str = '') -> None:
        """
        Load the current ToolWidgetCollection instance from a PySisyphe tool collection (.xtools) file. If the filename
        parameter is empty (default), the file name attribute of the current ToolWidgetCollection instance is used.

        Parameters
        ----------
        filename : str
            PySisyphe tool collection file name.
        """
        if filename == '' and self.hasFilename() and exists(self._filename):
            filename = self._filename
        if filename != '':
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
            if exists(filename):
                doc = minidom.parse(filename)
                self.parseXML(doc)
                self._filename = filename
            else: raise IOError('No such file : {}'.format(basename(filename)))
