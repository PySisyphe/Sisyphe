"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, Visualization, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any

from sys import platform

from os import getcwd
from os import remove
from os.path import join
from os.path import split
from os.path import exists
from os.path import splitext

from tempfile import gettempdir

from math import sqrt

from matplotlib import font_manager

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from vtk import vtkRenderer
from vtk import vtkWindowToImageFilter
from vtk import vtkInteractorStyleUser
from vtk import vtkPolyDataMapper2D
from vtk import vtkPolyDataMapper
from vtk import vtkAnnotatedCubeActor
from vtk import vtkAxesActor
from vtk import vtkTextActor
from vtk import vtkScalarBarActor
from vtk import vtkAxisActor2D
from vtk import vtkActor2D
from vtk import vtkActor
from vtk import vtkLineSource
from vtk import vtkAppendPolyData
from vtk import vtkBMPWriter
from vtk import vtkJPEGWriter
from vtk import vtkPNGWriter
from vtk import vtkTIFFWriter
from vtk import vtkOBJReader
from vtk import vtkCoordinate
from vtk import vtkOrientationMarkerWidget
from vtk import vtkBalloonWidget
from vtk import reference as vtkReference
from vtk import vtkPointHandleRepresentation3D
from vtk import vtkLineRepresentation
from vtk import VTK_CURSOR_DEFAULT
from vtk import VTK_CURSOR_ARROW
from vtk import VTK_CURSOR_HAND
from vtk import VTK_CURSOR_CROSSHAIR
from vtk import VTK_CURSOR_SIZEALL
from vtk import VTK_FONT_FILE
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheTools import NamedWidget
from Sisyphe.core.sisypheTools import DistanceWidget
from Sisyphe.core.sisypheTools import OrthogonalDistanceWidget
from Sisyphe.core.sisypheTools import AngleWidget
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import LineWidget
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import colorDialog
from Sisyphe.widgets.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from vtk import vtkObject
    from vtk import vtkRenderWindow
    from vtk import vtkRenderWindowInteractor
    from vtk import vtkCamera
    from vtk import vtk3DWidget

__all__ = ['AbstractViewWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

QFrame -> AbstractViewWidget
"""


class AbstractViewWidget(QFrame):
    """
    AbstractViewWidget class

    Description
    ~~~~~~~~~~~

    This abstract class is designed to provide a set of common methods and functionalities for all view widgets.

    The main features are as follows:

    - Rendering Pipeline: establishes a multi-layered VTK rendering setup, separating the primary data display (i.e. SisyppheVolume display) from 2D information overlays.
    - User Interaction: implements handling for mouse and keyboard events, enabling standard viewport navigation like zooming, panning, and window/level adjustments.
    - Informational overlays: manages a set of configurable 2D VTK actors for displaying contextual information, such as a color bar, scale ruler, orientation marker, cross-shaped cursor, and detailed text attributes about the patient and image.
    - Tool management: provides a framework for adding, managing, and interacting with a variety of 2D and 3D tools, including distance, angle, target (point), and trajectory (line) widgets.
    - Context menus: features a right-click popup menu system that offers easy access to viewport actions, visibility settings, and tool-specific operations.
    - Synchronization: uses a Qt signal and slot mechanism to enable the synchronization of cursor position, zoom, and tool manipulations across multiple linked viewports.
    - Configuration and export: supports user settings (e.g. colors, fonts...) and includes functionality to save the current view to a bitmap image file or copy it to the system clipboard.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AbstractViewWidget

    Creation: 20/03/2022
    Last Revision: 04/12/2025
    """

    _DEFAULTZOOM = 128.0  # Default zoom (vtk parallel scale) = conventional FOV of head imaging / 2

    # Custom Qt signals

    Selected = pyqtSignal(QWidget)
    CursorPositionChanged = pyqtSignal(QWidget, float, float, float)    # float x, y, z coordinates
    ZoomChanged = pyqtSignal(QWidget, float)                            # float zoom factor
    ToolMoved = pyqtSignal(QWidget, NamedWidget)                        # NamedWidget
    ToolRemoved = pyqtSignal(QWidget, NamedWidget, bool)                # NamedWidget, bool remove all ?
    ToolColorChanged = pyqtSignal(QWidget, NamedWidget)                 # NamedWidget
    ToolAttributesChanged = pyqtSignal(QWidget, NamedWidget)            # NamedWidget
    ToolAdded = pyqtSignal(QWidget, NamedWidget)                        # NamedWidget
    ToolRenamed = pyqtSignal(QWidget, NamedWidget, str)                 # NamedWidget, str old and new name
    ViewMethodCalled = pyqtSignal(QWidget, str, object)                 # str method name, object parameter

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        AbstractViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None
            parent widget
        """
        super().__init__(parent)

        self._volume = None
        self._synchro = False
        self._name = None
        self._title: str = ''
        self._scale = None
        self._axisconstraint = 0
        self._cursorenabled = True
        self._roundedenabled = True
        self._selected = False
        self._frame = True
        self._menuflag = True
        self._tooltipstr = ''
        # < Revision 10/03/2025
        if platform == 'win32':
            self.setStyleSheet('border-color: #000000')
        # Revision 10/03/2025 >

        # Init VTK window and interactor

        self._window = QVTKRenderWindowInteractor(self)
        # vtkRenderWindow instance
        self._renderwindow = self._window.GetRenderWindow()
        """
            Layer 0 = Volume/image display
            Layer 1 = Text information, cross, colorbar, ruler, orientation marker
        """
        self._renderwindow.SetNumberOfLayers(3)
        # vtkRenderWindowInteractor instance
        self._interactor = self._renderwindow.GetInteractor()

        # Init renderers

        self._renderer = vtkRenderer()
        self._renderer.SetLayer(0)
        self._renderer.SetBackground(0, 0, 0)
        self._renderer.GetActiveCamera().ParallelProjectionOn()
        self._renderwindow.AddRenderer(self._renderer)

        self._renderer2D = vtkRenderer()
        self._renderer2D.SetLayer(1)
        self._renderer2D.SetViewport(0, 0, 1, 1)
        self._renderer2D.InteractiveOff()
        self._renderwindow.AddRenderer(self._renderer2D)

        # Init VTK events, mouse and keyboard events

        style = vtkInteractorStyleUser()
        # noinspection PyTypeChecker
        style.AddObserver('MouseMoveEvent', self._onMouseMoveEvent)
        # noinspection PyTypeChecker
        style.AddObserver('MouseWheelForwardEvent', self._onWheelForwardEvent)
        # noinspection PyTypeChecker
        style.AddObserver('MouseWheelBackwardEvent', self._onWheelBackwardEvent)
        # noinspection PyTypeChecker
        style.AddObserver('LeftButtonPressEvent', self._onLeftPressEvent)
        # noinspection PyTypeChecker
        style.AddObserver('LeftButtonReleaseEvent', self._onLeftReleaseEvent)
        # noinspection PyTypeChecker
        style.AddObserver('RightButtonPressEvent', self._onRightPressEvent)
        # noinspection PyTypeChecker
        style.AddObserver('MiddleButtonPressEvent', self._onMiddlePressEvent)
        # noinspection PyTypeChecker
        style.AddObserver('KeyPressEvent', self._onKeyPressEvent)
        # noinspection PyTypeChecker
        style.AddObserver('KeyReleaseEvent', self._onKeyReleaseEvent)
        style.KeyPressActivationOff()
        self._window.SetInteractorStyle(style)

        """
        Init window popup menu
        
        Synchronisation (self._action['synchronisation'])
        Zoom (self._menuZoom)
            Zoom in (self._action['zoomin'])
            Zoom out (self._action['zoomout'])
            Default zoom (self._action['defaultzoom'])
            Move to target (self._menuMoveTarget)
        Actions (self._menuActions)
            No action (self._action['noflag'])
            Move (self._action['moveflag'])
            Zoom (self._action['zoomflag'])
            Level/Window (self._action['levelflag'])
            < Removed 10/03/2025 Cursor follows mouse (self._action['followflag']) >
            Centered cursor (self._action['centeredflag'])
        Visibility (self._menuVisibility)
            Show cursor (self._action['showcursor'])
            Show information (self._action['showinfo'])
            Show orientation marker (self._action['showmarker'])
            Show colorbar (self._action['showcolorbar'])
            Show ruler (self._action['showruler')
            Show tooltip (self._action['showtooltip'])
            Show all (self._action['showall'])
            Hide all (self._action['hideall'])
        Information (self._menuInformation)
            Identity (self._action['showident'])
            Image attributes (self._action['showimg'])
            Acquisition attributes (self._action['showacq'])
            Orientation marker shape (self._menuShape)
                Cube (self._action['shapecube'])
                Head (self._action['shapehead'])
                Bust (self._action['shapebust'])
                Body (self._action['shapebody'])
                Axes (self._action['shapeaxes'])
                Brain (self._action['shapebrain'])
        Colorbar position (self._menuColorbarPos)
            Left colorbar (self._action['leftcolorbar'])
            Right colorbar (self._action['rightcolorbar'])
            Top colorbar (self._action['topcolorbar'])
            Bottom colorbar (self._action['bottomcolorbar'])
        Ruler position (self._menuRulerPos)
            Left ruler (self._action['leftruler'])
            Right ruler (self._action['rightruler'])
            Top ruler (self._action['topcolorbar'])
            Bottom ruler (self._action['bottomruler'])
        Tools (self._menuTools)
            Distance (self._action['distance'])
            Orthogonal distances (self._action['orthodistance'])
            Angle (self._action['angle'])
            Box (self._action['box'])
            Text (self._action['text'])
            Remove all (self._action['removeall'])
            Target (self._action['target'])
            Trajectory (self._action['trajectory'])
        Save capture... (self._action['capture'])
        Copy capture to clipboard (self._action['clipboard'])
        """

        self._popup = QMenu('Main menu')
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action = dict()
        self._action['noflag'] = QAction('No action', self)
        self._action['moveflag'] = QAction('Move', self)
        self._action['zoomflag'] = QAction('Zoom', self)
        self._action['levelflag'] = QAction('Level/Window', self)
        self._action['followflag'] = QAction('Cursor follows mouse', self)
        # < Revision 09/01/2025
        # add centered cursor action
        self._action['centeredflag'] = QAction('Centered cursor', self)
        # Revision 09/01/2025 >
        self._action['zoomin'] = QAction('Zoom In', self)
        self._action['zoomout'] = QAction('Zoom Out', self)
        self._action['defaultzoom'] = QAction('Default Zoom', self)
        self._action['synchronisation'] = QAction('Synchronisation', self)
        self._action['showcursor'] = QAction('Show cursor', self)
        self._action['showinfo'] = QAction('Show information', self)
        self._action['showmarker'] = QAction('Show orientation marker', self)
        self._action['showcolorbar'] = QAction('Show colorbar', self)
        self._action['showruler'] = QAction('Show ruler', self)
        self._action['showtooltip'] = QAction('Show tooltip', self)
        self._action['showall'] = QAction('Show all', self)
        self._action['hideall'] = QAction('Hide all', self)
        self._action['showident'] = QAction('Identity', self)
        self._action['showimg'] = QAction('Image attributes', self)
        self._action['showacq'] = QAction('Acquisition attributes', self)
        self._action['leftcolorbar'] = QAction('Left colorbar', self)
        self._action['rightcolorbar'] = QAction('Right colorbar', self)
        self._action['topcolorbar'] = QAction('Top colorbar', self)
        self._action['bottomcolorbar'] = QAction('Bottom colorbar', self)
        self._action['leftruler'] = QAction('Left ruler', self)
        self._action['rightruler'] = QAction('Right ruler', self)
        self._action['topruler'] = QAction('Top ruler', self)
        self._action['bottomruler'] = QAction('Bottom ruler', self)
        self._action['shapecube'] = QAction('Cube', self)
        self._action['shapehead'] = QAction('Head', self)
        self._action['shapebust'] = QAction('Bust', self)
        self._action['shapebody'] = QAction('Body', self)
        self._action['shapeaxes'] = QAction('Axes', self)
        self._action['shapebrain'] = QAction('Brain', self)
        self._action['capture'] = QAction('Save capture...', self)
        self._action['clipboard'] = QAction('Copy capture to clipboard', self)
        self._action['distance'] = QAction('Distance', self)
        self._action['orthodistance'] = QAction('Orthogonal distances', self)
        self._action['angle'] = QAction('Angle', self)
        self._action['box'] = QAction('Box', self)
        self._action['text'] = QAction('Text', self)
        self._action['removeall'] = QAction('Remove all', self)
        self._action['target'] = QAction('Target', self)
        self._action['trajectory'] = QAction('Trajectory', self)
        self._action['noflag'].setCheckable(True)
        self._action['moveflag'].setCheckable(True)
        self._action['zoomflag'].setCheckable(True)
        self._action['levelflag'].setCheckable(True)
        self._action['followflag'].setCheckable(True)
        # < Revision 09/01/2025
        # add centered cursor action
        self._action['centeredflag'].setCheckable(True)
        # Revision 09/01/2025 >
        self._action['synchronisation'].setCheckable(True)
        self._action['showcursor'].setCheckable(True)
        self._action['showinfo'].setCheckable(True)
        self._action['showmarker'].setCheckable(True)
        self._action['showcolorbar'].setCheckable(True)
        self._action['leftcolorbar'].setCheckable(True)
        self._action['rightcolorbar'].setCheckable(True)
        self._action['topcolorbar'].setCheckable(True)
        self._action['bottomcolorbar'].setCheckable(True)
        self._action['showruler'].setCheckable(True)
        self._action['showtooltip'].setCheckable(True)
        self._action['leftruler'].setCheckable(True)
        self._action['rightruler'].setCheckable(True)
        self._action['topruler'].setCheckable(True)
        self._action['bottomruler'].setCheckable(True)
        self._action['shapecube'].setCheckable(True)
        self._action['shapehead'].setCheckable(True)
        self._action['shapebust'].setCheckable(True)
        self._action['shapebody'].setCheckable(True)
        self._action['shapebrain'].setCheckable(True)
        self._action['shapeaxes'].setCheckable(True)
        self._action['showident'].setCheckable(True)
        self._action['showimg'].setCheckable(True)
        self._action['showacq'].setCheckable(True)

        # noinspection PyUnresolvedReferences
        self._action['showcursor'].triggered.connect(
            lambda: self.setCursorVisibility(self._action['showcursor'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showinfo'].triggered.connect(
            lambda: self.setInfoVisibility(self._action['showinfo'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showmarker'].triggered.connect(
            lambda: self.setOrientationMakerVisibility(self._action['showmarker'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showcolorbar'].triggered.connect(
            lambda: self.setColorbarVisibility(self._action['showcolorbar'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showruler'].triggered.connect(
            lambda: self.setRulerVisibility(self._action['showruler'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showtooltip'].triggered.connect(
            lambda: self.setTooltipVisibility(self._action['showtooltip'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showident'].triggered.connect(
            lambda: self.setInfoIdentityVisibility(self._action['showident'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showimg'].triggered.connect(
            lambda: self.setInfoVolumeVisibility(self._action['showimg'].isChecked()))
        # noinspection PyUnresolvedReferences
        self._action['showacq'].triggered.connect(
            lambda: self.setInfoAcquisitionVisibility(self._action['showacq'].isChecked()))

        # noinspection PyUnresolvedReferences
        self._action['noflag'].triggered.connect(lambda: self.setNoActionFlag(True))
        # noinspection PyUnresolvedReferences
        self._action['moveflag'].triggered.connect(lambda: self.setMoveFlag(True))
        # noinspection PyUnresolvedReferences
        self._action['zoomflag'].triggered.connect(lambda: self.setZoomFlag(True))
        # noinspection PyUnresolvedReferences
        self._action['levelflag'].triggered.connect(lambda: self.setLevelFlag(True))
        # noinspection PyUnresolvedReferences
        self._action['followflag'].triggered.connect(lambda: self.setFollowFlag(True))
        # < Revision 09/01/2025
        # add centered cursor action
        # noinspection PyUnresolvedReferences
        self._action['centeredflag'].triggered.connect(lambda: self.setCenteredCursorFlag(True))
        # Revision 09/01/2025 >
        # noinspection PyUnresolvedReferences
        self._action['hideall'].triggered.connect(lambda: self.hideAll(True))
        # noinspection PyUnresolvedReferences
        self._action['showall'].triggered.connect(lambda: self.showAll(True))
        # noinspection PyUnresolvedReferences
        self._action['zoomin'].triggered.connect(self.zoomIn)
        # noinspection PyUnresolvedReferences
        self._action['zoomout'].triggered.connect(self.zoomOut)
        # noinspection PyUnresolvedReferences
        self._action['defaultzoom'].triggered.connect(self.zoomDefault)
        # noinspection PyUnresolvedReferences
        self._action['leftcolorbar'].triggered.connect(self.setColorbarPositionToLeft)
        # noinspection PyUnresolvedReferences
        self._action['rightcolorbar'].triggered.connect(self.setColorbarPositionToRight)
        # noinspection PyUnresolvedReferences
        self._action['topcolorbar'].triggered.connect(self.setColorbarPositionToTop)
        # noinspection PyUnresolvedReferences
        self._action['bottomcolorbar'].triggered.connect(self.setColorbarPositionToBottom)
        # noinspection PyUnresolvedReferences
        self._action['leftruler'].triggered.connect(self.setRulerPositionToLeft)
        # noinspection PyUnresolvedReferences
        self._action['rightruler'].triggered.connect(self.setRulerPositionToRight)
        # noinspection PyUnresolvedReferences
        self._action['topruler'].triggered.connect(self.setRulerPositionToTop)
        # noinspection PyUnresolvedReferences
        self._action['bottomruler'].triggered.connect(self.setRulerPositionToBottom)
        # noinspection PyUnresolvedReferences
        self._action['shapecube'].triggered.connect(self.setOrientationMarkerToCube)
        # noinspection PyUnresolvedReferences
        self._action['shapehead'].triggered.connect(self.setOrientationMarkerToHead)
        # noinspection PyUnresolvedReferences
        self._action['shapebust'].triggered.connect(self.setOrientationMarkerToBust)
        # noinspection PyUnresolvedReferences
        self._action['shapebody'].triggered.connect(self.setOrientationMarkerToBody)
        # noinspection PyUnresolvedReferences
        self._action['shapeaxes'].triggered.connect(self.setOrientationMarkerToAxes)
        # noinspection PyUnresolvedReferences
        self._action['shapebrain'].triggered.connect(self.setOrientationMarkerToBrain)
        # noinspection PyUnresolvedReferences
        self._action['capture'].triggered.connect(self.saveCapture)
        # noinspection PyUnresolvedReferences
        self._action['clipboard'].triggered.connect(self.copyToClipboard)
        # noinspection PyUnresolvedReferences
        self._action['distance'].triggered.connect(lambda: self.addDistanceTool())
        # noinspection PyUnresolvedReferences
        self._action['orthodistance'].triggered.connect(lambda: self.addOrthogonalDistanceTool())
        # noinspection PyUnresolvedReferences
        self._action['angle'].triggered.connect(lambda: self.addAngleTool())
        # noinspection PyUnresolvedReferences
        self._action['removeall'].triggered.connect(lambda: self.removeAll2DTools())
        # noinspection PyUnresolvedReferences
        self._action['box'].triggered.connect(lambda: self.addBoxTool())
        # noinspection PyUnresolvedReferences
        self._action['text'].triggered.connect(lambda: self.addTextTool())
        # noinspection PyUnresolvedReferences
        self._action['target'].triggered.connect(lambda: self.addTarget(p=None, name='', signal=True))
        # noinspection PyUnresolvedReferences
        self._action['trajectory'].triggered.connect(lambda: self.addTrajectory(p1=None, p2=None, name='', signal=True))
        self._popup.addAction(self._action['synchronisation'])
        self._group_colorbar = QActionGroup(self)
        self._group_colorbar.setExclusive(True)
        self._group_colorbar.addAction(self._action['leftcolorbar'])
        self._group_colorbar.addAction(self._action['rightcolorbar'])
        self._group_colorbar.addAction(self._action['topcolorbar'])
        self._group_colorbar.addAction(self._action['bottomcolorbar'])
        self._group_ruler = QActionGroup(self)
        self._group_ruler.setExclusive(True)
        self._group_ruler.addAction(self._action['leftruler'])
        self._group_ruler.addAction(self._action['rightruler'])
        self._group_ruler.addAction(self._action['topruler'])
        self._group_ruler.addAction(self._action['bottomruler'])
        self._group_shape = QActionGroup(self)
        self._group_shape.setExclusive(True)
        self._group_shape.addAction(self._action['shapecube'])
        self._group_shape.addAction(self._action['shapehead'])
        self._group_shape.addAction(self._action['shapebust'])
        self._group_shape.addAction(self._action['shapebody'])
        self._group_shape.addAction(self._action['shapebrain'])
        self._group_shape.addAction(self._action['shapeaxes'])
        self._group_flag = QActionGroup(self)
        self._group_flag.setExclusive(True)
        self._group_flag.addAction(self._action['noflag'])
        self._group_flag.addAction(self._action['moveflag'])
        self._group_flag.addAction(self._action['zoomflag'])
        self._group_flag.addAction(self._action['levelflag'])
        self._group_flag.addAction(self._action['followflag'])
        # < Revision 09/01/2025
        # add centered cursor action
        self._group_flag.addAction(self._action['centeredflag'])
        # Revision 09/01/2025 >
        self._action['leftcolorbar'].setChecked(True)
        self._action['leftruler'].setChecked(True)
        self._action['noflag'].setChecked(True)
        self._menuZoom = self._popup.addMenu('Zoom')
        self._menuZoom.addAction(self._action['zoomin'])
        self._menuZoom.addAction(self._action['zoomout'])
        self._menuZoom.addAction(self._action['defaultzoom'])
        self._menuActions = self._popup.addMenu('Actions')
        self._menuActions.addAction(self._action['noflag'])
        self._menuActions.addAction(self._action['moveflag'])
        self._menuActions.addAction(self._action['zoomflag'])
        self._menuActions.addAction(self._action['levelflag'])
        # < Revision 10/03/2025
        # remove cursor follow mouse action
        self._menuActions.addAction(self._action['followflag'])
        # Revision 10/03/2025 >
        # < Revision 09/01/2025
        # add centered cursor action
        self._menuActions.addAction(self._action['centeredflag'])
        # Revision 09/01/2025 >
        self._menuVisibility = self._popup.addMenu('Visibility')
        self._menuVisibility.addAction(self._action['showcursor'])
        self._menuVisibility.addAction(self._action['showinfo'])
        self._menuVisibility.addAction(self._action['showmarker'])
        self._menuVisibility.addAction(self._action['showcolorbar'])
        self._menuVisibility.addAction(self._action['showruler'])
        self._menuVisibility.addAction(self._action['showtooltip'])
        self._menuVisibility.addAction(self._action['showall'])
        self._menuVisibility.addAction(self._action['hideall'])
        self._menuInformation = self._popup.addMenu('Information')
        self._menuInformation.addAction(self._action['showident'])
        self._menuInformation.addAction(self._action['showimg'])
        self._menuInformation.addAction(self._action['showacq'])
        # self._menuShape = self._popup.addMenu('Orientation marker shape')
        self._menuShape = self._menuInformation.addMenu('Orientation marker shape')
        self._menuShape.addAction(self._action['shapecube'])
        self._menuShape.addAction(self._action['shapebrain'])
        self._menuShape.addAction(self._action['shapehead'])
        self._menuShape.addAction(self._action['shapebust'])
        self._menuShape.addAction(self._action['shapebody'])
        self._menuShape.addAction(self._action['shapeaxes'])
        self._menuColorbarPos = self._popup.addMenu('Colorbar position')
        self._menuColorbarPos.addAction(self._action['leftcolorbar'])
        self._menuColorbarPos.addAction(self._action['rightcolorbar'])
        self._menuColorbarPos.addAction(self._action['topcolorbar'])
        self._menuColorbarPos.addAction(self._action['bottomcolorbar'])
        self._menuRulerPos = self._popup.addMenu('Ruler position')
        self._menuRulerPos.addAction(self._action['leftruler'])
        self._menuRulerPos.addAction(self._action['rightruler'])
        self._menuRulerPos.addAction(self._action['topruler'])
        self._menuRulerPos.addAction(self._action['bottomruler'])
        self._menuTools = self._popup.addMenu('Tools')
        self._menuTools.addAction(self._action['distance'])
        self._menuTools.addAction(self._action['orthodistance'])
        self._menuTools.addAction(self._action['angle'])
        self._menuTools.addAction(self._action['box'])
        self._menuTools.addAction(self._action['text'])
        self._menuTools.addSeparator()
        self._menuTools.addAction(self._action['removeall'])
        self._menuTools.addSeparator()
        self._menuTools.addAction(self._action['target'])
        self._menuTools.addAction(self._action['trajectory'])
        self._menuTools.addSeparator()
        self._menuMoveTarget = self._menuZoom.addMenu('Move to target')
        self._menuMoveTarget.menuAction().setVisible(False)
        self._popup.addAction(self._action['capture'])
        self._popup.addAction(self._action['clipboard'])

        # Init tool popup menu

        self._toolpopup = QMenu()
        # noinspection PyTypeChecker
        self._toolpopup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._toolpopup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._toolpopup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['toolcolor'] = QAction('Color...', self)
        self._action['textprop'] = QAction('Text properties...', self)
        self._action['edittext'] = QAction('Edit text...', self)
        self._action['tooldelete'] = QAction('Delete', self)
        # noinspection PyUnresolvedReferences
        self._action['toolcolor'].triggered.connect(self._toolColor)
        # noinspection PyUnresolvedReferences
        self._action['textprop'].triggered.connect(self._textProperties)
        # noinspection PyUnresolvedReferences
        self._action['edittext'].triggered.connect(self._editPickedText)
        # noinspection PyUnresolvedReferences
        self._action['tooldelete'].triggered.connect(self._removePickedTool)
        self._toolpopup.addAction(self._action['toolcolor'])
        self._toolpopup.addAction(self._action['textprop'])
        self._toolpopup.addAction(self._action['edittext'])
        self._toolpopup.addAction(self._action['tooldelete'])
        self._toolpopup.addSeparator()
        self._toolpopup.addMenu(self._popup)

        # Init QLineEdit, edit TextWidget text

        self._dialog = QDialog(self, flags=Qt.Dialog | Qt.FramelessWindowHint)
        self._dialog.resize(100, 20)
        self._dialog.setWindowOpacity(1.0)
        self._dialog.setVisible(False)
        self._edit = QLineEdit(self._dialog)
        # noinspection PyUnresolvedReferences
        self._edit.editingFinished.connect(self._textEditFinished)

        # User settings

        self._settings = SisypheSettings()
        self._lwidth = None
        self._lalpha = None
        self._lcolor = None
        self._slcolor = None
        self._ffamily = None
        self._fsize = None
        self._fscale = None
        self._initSettings()

        # Init text attributes actors

        self._info = dict()
        self._info['topright'] = vtkTextActor()
        self._info['topleft'] = vtkTextActor()
        self._info['bottomright'] = vtkTextActor()
        self._info['bottomleft'] = vtkTextActor()
        self._info['topcenter'] = vtkTextActor()
        self._info['leftcenter'] = vtkTextActor()
        self._info['rightcenter'] = vtkTextActor()
        self._info['bottomcenter'] = vtkTextActor()
        self._info['topright'].SetTextScaleModeToNone()
        self._info['topleft'].SetTextScaleModeToNone()
        self._info['bottomright'].SetTextScaleModeToNone()
        self._info['bottomleft'].SetTextScaleModeToNone()
        self._info['topcenter'].SetTextScaleModeToNone()
        self._info['leftcenter'].SetTextScaleModeToNone()
        self._info['rightcenter'].SetTextScaleModeToNone()
        self._info['bottomcenter'].SetTextScaleModeToNone()
        self._renderer2D.AddActor2D(self._info['topright'])
        self._renderer2D.AddActor2D(self._info['topleft'])
        self._renderer2D.AddActor2D(self._info['bottomright'])
        self._renderer2D.AddActor2D(self._info['bottomleft'])
        self._renderer2D.AddActor2D(self._info['topcenter'])
        self._renderer2D.AddActor2D(self._info['leftcenter'])
        self._renderer2D.AddActor2D(self._info['rightcenter'])
        self._renderer2D.AddActor2D(self._info['bottomcenter'])

        # Init colorbar actor

        self._colorbar = vtkScalarBarActor()
        self._colorbar.AnnotationTextScalingOff()
        self._colorbar.SetOrientationToVertical()
        self._colorbar.SetTextPositionToSucceedScalarBar()
        # noinspection PyUnresolvedReferences
        self._colorbar.GetLabelTextProperty().SetFontSize(int(self._fsize * self._fscale))
        # noinspection PyUnresolvedReferences
        self._colorbar.GetTitleTextProperty().SetFontSize(int(self._fsize * self._fscale))
        if self._ffamily in ('Arial', 'Courier', 'Times'):
            self._colorbar.GetLabelTextProperty().SetFontFamilyAsString(self._ffamily)
            self._colorbar.GetTitleTextProperty().SetFontFamilyAsString(self._ffamily)
        else:
            self._colorbar.GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
            self._colorbar.GetTitleTextProperty().SetFontFamily(VTK_FONT_FILE)
            self._colorbar.GetLabelTextProperty().SetFontFile(self._ffamily)
            self._colorbar.GetTitleTextProperty().SetFontFile(self._ffamily)
        self._colorbar.GetLabelTextProperty().BoldOff()
        self._colorbar.GetTitleTextProperty().BoldOff()
        self._colorbar.GetTitleTextProperty().SetLineOffset(5.0)
        self._colorbar.SetVerticalTitleSeparation(5)
        self._colorbar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self._colorbar.GetPositionCoordinate().SetValue(0.81, 0.25)
        self._colorbar.SetWidth(0.14)
        self._colorbar.SetHeight(0.5)
        self.setColorbarPosition(self.getColorbarPosition(), False)
        self._colorbar.SetVisibility(False)
        # noinspection PyTypeChecker
        self._renderer2D.AddActor2D(self._colorbar)

        # Init ruler actor

        self._ruler = vtkAxisActor2D()
        self._ruler.RulerModeOn()
        self._ruler.SetRulerDistance(0.1)
        self._ruler.SetTickLength(10)
        self._ruler.SetNumberOfMinorTicks(0)
        self._ruler.GetProperty().SetLineWidth(self._lwidth)
        # noinspection PyUnresolvedReferences
        self._ruler.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
        self._ruler.GetProperty().SetOpacity(self._lalpha)
        self._ruler.LabelVisibilityOff()
        self._ruler.TitleVisibilityOff()
        self._ruler.GetPoint1Coordinate().SetCoordinateSystemToNormalizedViewport()
        self._ruler.GetPoint2Coordinate().SetCoordinateSystemToNormalizedViewport()
        self._ruler.GetPoint1Coordinate().SetValue(0.01, 0.3)
        self._ruler.GetPoint2Coordinate().SetValue(0.01, 0.7)
        self.setRulerPosition(self.getRulerPosition(), False)
        self._ruler.SetVisibility(False)
        # noinspection PyTypeChecker
        self._renderer2D.AddActor2D(self._ruler)

        # Init orientation marker actor

        self._orientmarker = None
        self.setOrientationMarker(self.getOrientationMarker(), False)
        # noinspection PyUnresolvedReferences
        self._orientmarker.EnabledOff()

        # list of tools

        self._tools = ToolWidgetCollection()
        # noinspection PyTypeChecker
        self._tools.setFontFamily(self._ffamily)
        # noinspection PyTypeChecker
        self._tools.setLineWidth(self._lwidth)
        # noinspection PyTypeChecker
        self._tools.setOpacity(self._lalpha)
        # noinspection PyTypeChecker
        self._tools.setColor(self._lcolor)
        # noinspection PyTypeChecker
        self._tools.setSelectedColor(self._slcolor)
        self._tools.setInteractor(self._interactor)
        self._tooltip = vtkBalloonWidget()
        self._tooltip.CreateDefaultRepresentation()
        # noinspection PyUnresolvedReferences
        self._tooltip.GetBalloonRepresentation().GetTextProperty().SetFontSize(int(self._fsize * self._fscale))
        self._tooltip.GetBalloonRepresentation().GetTextProperty().BoldOff()
        self._tooltip.SetInteractor(self._interactor)
        self._accepttools = True

        # Init central cross actor

        self._cross = None
        self._initCentralCross()

        # Init cursor

        self._cursor = None
        self._initCursor()

        # Init frame

        # noinspection PyTypeChecker
        self.setFrameShadow(QFrame.Plain)
        # noinspection PyTypeChecker
        self.setFrameShape(QFrame.NoFrame)

        # Init QLayout

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._window)
        self.setLayout(self._layout)

        # Start interactor

        self._tooltip.EnabledOn()
        self._interactor.Initialize()
        self._interactor.Start()

    """
    Private attributes

    _window                 QVTKRenderWindowInteractor
    _renderwindow           vtkRenderWindow
    _interactor             vtkRenderWindowInteractor
    _renderer               vtkRenderer, world display
    _renderer2D             vtkRenderer, text info, cross, colorbar, ruler display
    _colorbar               vtkScalarBarActor
    _ruler                  vtkDistanceWidget
    _volume                 SisypheVolume, reference volume
    _title                  str, view title
    _name                   str, widget name
    _scale                  float, default zoom scale
    _fontsize               int
    _fontcolor              list[float, float, float]
    _info                   dict[str, vtkTextActor], volume attributes displayed on renderer2D
    _cross                  vtkActor2D, cross marker in the center of the view
    _cursor                 vtkCursor2D, two orthogonal lines
    _cursoractor            vtkActor, cursor actor
    _orientmarker           vtkOrientationMarkerWidget
    _tools                  ToolWidgetCollection
    _accepttools            bool, accept or not to display ToolWidget
    _dialog                 QDialog, text editor for TextWidget tool
    _axisconstraint         int, cursor axis constraint 0 = unconstrained, 1 = x axis, 2 = y axis, 3 = z axis
    _cursorenabled          bool, cursor enabled flag
    _roundedenabled         bool, rounded cursor coordinates enabled flag
    _selected               bool, view selection
    _frame                  bool, frame visibility if selected
    _action                 dict[str, QActions] 
    _menuflag               bool, popup menu enabled or disabled
    _popup                  QMenu, popup menu
    _menuActions            QMenu, popup submenu for actions
    _menuVisibility         QMenu, popup submenu for visibility
    _menuColorbarPos        QMenu, popup submenu for colorbar position
    _tooltip                vtkBalloonWidget, tooltip for vtkWidgets
    _tooltipstr             str, viewport tooltip text
    _lwidth                 int, default line width, default 2.0
    _lcolor                 tuple[int, int, int], font color, default white (1.0, 1.0, 1.0)
    _slcolor                tuple[int, int, int], selected color, default red (1.0, 0.0, 0.0)
    _lalpha                 float, default line opacity, default 1.0
    _fsize                  int, font size, default 12
    _ffamily                str, font family, default 'Arial'
    _fscale                 float, scale factor applied to font size (default 1.0, no scale factor)
    _fopacity               float, default font opacity, default 1.0
    """

    # Private methods

    def _initSettings(self) -> None:
        """
        Initialize widget attributes from the SisypheSettings instance.
        Loads user preferences for line styles, font styles, and default visibilities.
        """
        self._lwidth = self._settings.getFieldValue('Viewport', 'LineWidth')
        self._lcolor = self._settings.getFieldValue('Viewport', 'LineColor')
        self._slcolor = self._settings.getFieldValue('Viewport', 'LineSelectedColor')
        self._lalpha = self._settings.getFieldValue('Viewport', 'LineOpacity')
        # < Revision 17/03/2025
        # font settings management
        self._fsize = self._settings.getFieldValue('GUI', 'FontSize')
        self._ffamily = self._settings.getFieldValue('GUI', 'FontFamily')
        self._fscale = self._settings.getFieldValue('Viewport', 'FontSizeScale')
        # Revision 17/03/2025 >
        if self._lwidth is None: self._lwidth = 2
        if self._lcolor is None: self._lcolor = (1.0, 1.0, 1.0)
        if self._slcolor is None: self._slcolor = (1.0, 0.0, 0.0)
        if self._lalpha is None: self._lalpha = 1.0
        # < Revision 17/03/2025
        # font settings management
        if self._fsize is None: self._fsize = 12
        if self._ffamily is None: self._ffamily = 'Arial'
        elif self._ffamily not in ('Arial', 'Courier', 'Times'):
            try:
                path = font_manager.findfont(self._ffamily, fallback_to_default=False)
                if (not exists(path) or
                        splitext(path)[1] not in ('.ttf', '.otf')): self._ffamily = 'Arial'
                else: self._ffamily = path
            except: self._ffamily = 'Arial'
        if self._fscale is None: self._fscale = 1.0
        # Revision 17/03/2025 >

        """
            Settings -> actions        
        """
        # Cursor
        v = self._settings.getFieldValue('Viewport', 'CursorVisibility')
        if v is None: v = False
        self._action['showcursor'].setChecked(v)
        # Attributes
        v = self._settings.getFieldValue('Viewport', 'AttributesVisibility')
        if v is None: v = False
        self._action['showinfo'].setChecked(v)
        # Identity attributes
        v = self._settings.getFieldValue('Viewport', 'IdentityAttributesVisibility')
        if v is None: v = True
        self._action['showident'].setChecked(v)
        # Volume attributes
        v = self._settings.getFieldValue('Viewport', 'VolumeAttributesVisibility')
        if v is None: v = True
        self._action['showimg'].setChecked(v)
        # Acquisition attributes
        v = self._settings.getFieldValue('Viewport', 'AcquisitionAttributesVisibility')
        if v is None: v = True
        self._action['showacq'].setChecked(v)
        # Colorbar
        v = self._settings.getFieldValue('Viewport', 'ColorbarVisibility')
        if v is None: v = False
        self._action['showcolorbar'].setChecked(v)
        # Ruler
        v = self._settings.getFieldValue('Viewport', 'RulerVisibility')
        if v is None: v = False
        self._action['showruler'].setChecked(v)
        # Tooltip
        v = self._settings.getFieldValue('Viewport', 'TooltipVisibility')
        if v is None: v = False
        self._action['showtooltip'].setChecked(v)
        # Orientation marker
        v = self._settings.getFieldValue('Viewport', 'OrientationMarkerVisibility')
        if v is None: v = False
        self._action['showmarker'].setChecked(v)
        # Orientation marker shape
        v = self._settings.getFieldValue('Viewport', 'OrientationMarkerShape')
        if v is not None: v = v[0]
        else: v = 'Cube'
        if v == 'Cube': self._action['shapecube'].setChecked(True)
        elif v == 'Head': self._action['shapehead'].setChecked(True)
        elif v == 'Bust': self._action['shapebust'].setChecked(True)
        elif v == 'Body': self._action['shapebody'].setChecked(True)
        elif v == 'Brain': self._action['shapebrain'].setChecked(True)
        else: self._action['shapeaxes'].setChecked(True)
        # Colorbar position
        v = self._settings.getFieldValue('Viewport', 'ColorbarPosition')
        if v is not None: v = v[0]
        else: v = 'Left'
        if v == 'Left': self._action['leftcolorbar'].setChecked(True)
        elif v == 'Right': self._action['rightcolorbar'].setChecked(True)
        elif v == 'Top': self._action['topcolorbar'].setChecked(True)
        else: self._action['bottomcolorbar'].setChecked(True)
        # Ruler position
        v = self._settings.getFieldValue('Viewport', 'RulerPosition')
        if v is not None: v = v[0]
        else: v = 'Left'
        if v == 'Left': self._action['leftruler'].setChecked(True)
        elif v == 'Right': self._action['rightruler'].setChecked(True)
        elif v == 'Top': self._action['topruler'].setChecked(True)
        else: self._action['bottomruler'].setChecked(True)

    def _initInfoLabels(self)  -> None:
        """
        Initialize the vtkTextActor instances used to display SisypheVolume information.
        Sets up text properties, positions, and content for identity, image, and acquisition attributes.
        """
        if self.hasVolume():
            # Top Left identity attributes

            identity = self._volume.identity
            if self._volume.getID() != self._volume.getArrayID():
                txt = 'ID. {}\n{} {}\n{} ({} Y)'.format(self._volume.getID(),
                                                        identity.getLastname(),
                                                        identity.getFirstname(),
                                                        identity.getDateOfBirthday(),
                                                        identity.getAge())
            else:
                txt = '{} {}\n{} ({} Y)'.format(identity.getLastname(),
                                                identity.getFirstname(),
                                                identity.getDateOfBirthday(),
                                                identity.getAge())

            info = self._info['topleft']
            prop = info.GetTextProperty()
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                prop.SetFontFamilyAsString(self._ffamily)
            else:
                prop.SetFontFamily(VTK_FONT_FILE)
                prop.SetFontFile(self._ffamily)
            prop.SetFontSize(int(self._fsize * self._fscale))
            prop.SetColor(self._lcolor)
            prop.SetOpacity(self._lalpha)
            prop.SetJustificationToLeft()
            prop.SetVerticalJustificationToTop()
            info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            info.SetPosition(0.01, 0.99)
            if not identity.isAnonymized():
                info.SetInput(txt)
            info.SetVisibility(False)

            # Top Right image attributes

            if self._volume.isDefaultOrigin():
                txt = 'Array ID. {0}\n' \
                      '{1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm\n' \
                      '{2[0]} x {2[1]} x {2[2]} x {3}\n' \
                      '{4[0]:.2f} x {4[1]:.2f} x {4[2]:.2f} mm\n' \
                      '{5}, {6:.2f} MB'.format(self._volume.getArrayID(),
                                               self._volume.getFieldOfView(),
                                               self._volume.getSize(),
                                               self._volume.getNumberOfComponentsPerPixel(),
                                               self._volume.getSpacing(),
                                               self._volume.getDatatype(),
                                               self._volume.getMemorySize('MB'))
            else:
                txt = 'Array ID. {0}\n' \
                      '{1[0]:.1f} x {1[1]:.1f} x {1[2]:.1f} mm\n' \
                      'Origin: {2[0]:.1f} x {2[1]:.1f} x {2[2]:.1f} mm\n' \
                      '{3[0]} x {3[1]} x {3[2]} x {4}\n' \
                      '{5[0]:.2f} x {5[1]:.2f} x {5[2]:.2f} mm\n' \
                      '{6}, {7:.2f} MB'.format(self._volume.getArrayID(),
                                               self._volume.getFieldOfView(),
                                               self._volume.getOrigin(),
                                               self._volume.getSize(),
                                               self._volume.getNumberOfComponentsPerPixel(),
                                               self._volume.getSpacing(),
                                               self._volume.getDatatype(),
                                               self._volume.getMemorySize('MB'))

            info = self._info['topright']
            prop = info.GetTextProperty()
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                prop.SetFontFamilyAsString(self._ffamily)
            else:
                prop.SetFontFamily(VTK_FONT_FILE)
                prop.SetFontFile(self._ffamily)
            prop.SetFontSize(int(self._fsize * self._fscale))
            prop.SetColor(self._lcolor)
            prop.SetOpacity(self._lalpha)
            prop.SetJustificationToRight()
            prop.SetVerticalJustificationToTop()
            info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            info.SetPosition(0.99, 0.99)
            info.SetInput(txt)
            info.SetVisibility(False)

            # Bottom Left acquisition attributes

            acq = self._volume.acquisition

            txt = '{} {}\n{}\n{}'.format(self._volume.getOrientationAsString().upper(),
                                         acq.getModality(True),
                                         acq.getSequence(),
                                         acq.getDateOfScan(True))

            info = self._info['bottomleft']
            prop = info.GetTextProperty()
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                prop.SetFontFamilyAsString(self._ffamily)
            else:
                prop.SetFontFamily(VTK_FONT_FILE)
                prop.SetFontFile(self._ffamily)
            prop.SetFontSize(int(self._fsize * self._fscale))
            prop.SetColor(self._lcolor)
            prop.SetOpacity(self._lalpha)
            prop.SetJustificationToLeft()
            prop.SetVerticalJustificationToBottom()
            info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            info.SetPosition(0.01, 0.01)
            info.SetInput(txt)
            info.SetVisibility(False)

            # Bottom Right

            txt = ''
            info = self._info['bottomright']
            prop = info.GetTextProperty()
            if self._ffamily in ('Arial', 'Courier', 'Times'):
                prop.SetFontFamilyAsString(self._ffamily)
            else:
                prop.SetFontFamily(VTK_FONT_FILE)
                prop.SetFontFile(self._ffamily)
            prop.SetFontSize(int(self._fsize * self._fscale))
            prop.SetColor(self._lcolor)
            prop.SetOpacity(self._lalpha)
            prop.SetJustificationToRight()
            prop.SetVerticalJustificationToBottom()
            info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            info.SetPosition(0.99, 0.01)
            info.SetInput(txt)
            info.SetVisibility(False)

    def _initColorbar(self) -> None:
        """
        Initialize the vtkScalarBarActor.
        Sets the lookup table from the SisypheVolume, and configures font, size, and format.
        """
        if self.hasVolume():
            self._colorbar.SetLookupTable(self._volume.display.getVTKLUT())
            self._colorbar.UnconstrainedFontSizeOn()
            self._colorbar.SetMaximumWidthInPixels(150)
            prop = self._colorbar.GetLabelTextProperty()
            if self._ffamily in ['Arial', 'Courier', 'Times']:
                prop.SetFontFamilyAsString(self._ffamily)
            else:
                prop.SetFontFamily(VTK_FONT_FILE)
                prop.SetFontFile(self._ffamily)
            prop.SetFontSize(int(self._fsize * self._fscale))
            prop.SetColor(self._lcolor)
            prop.SetOpacity(self._lalpha)
            self._colorbar.SetNumberOfLabels(5)
            if self._volume.isIntegerDatatype(): self._colorbar.SetLabelFormat('%5.0f')
            else: self._colorbar.SetLabelFormat('%5.2f')
            self._colorbar.SetVisibility(False)

    def _initCentralCross(self) -> None:
        """
        Initialize the central cross vtkActor2D.
        The cross indicates the center of the viewport.
        """
        s = self._renderer.GetSize()
        t0 = 0.05
        r = 2 * s[1] / s[0]
        t1 = 0.05 * r
        lineh = vtkLineSource()
        linev = vtkLineSource()
        lineh.SetPoint1(0.5, 0.5 - t0, 0)
        lineh.SetPoint2(0.5, 0.5 + t0, 0)
        linev.SetPoint1(0.5 - t1, 0.5, 0)
        linev.SetPoint2(0.5 + t1, 0.5, 0)
        lines = vtkAppendPolyData()
        # noinspection PyArgumentList
        lines.AddInputConnection(lineh.GetOutputPort())
        # noinspection PyArgumentList
        lines.AddInputConnection(linev.GetOutputPort())
        c = vtkCoordinate()
        c.SetCoordinateSystemToNormalizedViewport()
        mapper = vtkPolyDataMapper2D()
        # noinspection PyArgumentList
        mapper.SetInputConnection(lines.GetOutputPort())
        mapper.SetTransformCoordinate(c)
        self._cross = vtkActor2D()
        self._cross.SetMapper(mapper)
        self._cross.GetProperty().SetLineWidth(self._lwidth)
        self._cross.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
        self._cross.GetProperty().SetOpacity(self._lalpha)
        self._cross.SetVisibility(False)
        self._renderer2D.AddActor2D(self._cross)

    def _getRoundedCoordinate(self, p:  list[float] | tuple[float, float, float]) -> list[float]:
        """
        Round world coordinates to the nearest voxel coordinate based on SisypheVolume spacing.

        Parameters
        ----------
        p : list[float] or tuple[float, float, float]
            world coordinates (x, y, z).

        Returns
        -------
        list[float]
            World coordinates rounded to the volume's voxel grid.
        """
        if self._volume is not None:
            if self._roundedenabled:
                s = self._volume.getSpacing()
                r = list()
                r.append(int(p[0] / s[0]) * s[0])
                r.append(int(p[1] / s[1]) * s[1])
                r.append(int(p[2] / s[2]) * s[2])
                return r
            else: return p
        else: raise AttributeError('Volume attribute is None.')

    def _getWorldToMatrixCoordinate(self, p: list[float] | tuple[float, float, float]) -> list[int]:
        """
        Convert world coordinates to matrix (voxel) coordinates.

        Parameters
        ----------
        p : list[float] or tuple[float, float, float]
            world coordinates (x, y, z).

        Returns
        -------
        list[int]
            matrix coordinates (i, j, k).
        """
        if self._volume is not None:
            s = self._volume.getSpacing()
            r = list()
            r.append(int(round(p[0] / s[0])))
            r.append(int(round(p[1] / s[1])))
            r.append(int(round(p[2] / s[2])))
            return r
        else: raise AttributeError('Volume attribute is None.')

    def _getWorldFromDisplay(self, x: float, y: float) -> tuple[float, float, float]:
        """
        Convert 2D display coordinates to 3D world coordinates.

        Parameters
        ----------
        x : int
            2D display x-coordinate.
        y : int
            2D display y-coordinate.

        Returns
        -------
        tuple[float, float, float]
            3D world coordinates (x, y, z).
        """
        self._renderer.SetDisplayPoint(x, y, 0.0)
        # noinspection PyArgumentList
        self._renderer.DisplayToWorld()
        p = self._renderer.GetWorldPoint()
        # noinspection PyTypeChecker
        return p[:3]

    def _getDisplayFromWorld(self, x: float, y: float, z: float) -> tuple[float, float]:
        """
        Convert 3D world coordinates to 2D display coordinates.

        Parameters
        ----------
        x : float
            world x-coordinate.
        y : float
            world y-coordinate.
        z : float
            world z-coordinate.

        Returns
        -------
        tuple[int, int]
            2D display coordinates (x, y).
        """
        self._renderer.SetWorldPoint(x, y, z, 1.0)
        self._renderer.WorldToDisplay()
        p = self._renderer.GetDisplayPoint()
        # noinspection PyTypeChecker
        return p[:2]

    def _getDisplayFromNormalizedViewport(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert normalized viewport coordinates to display coordinates.

        Parameters
        ----------
        x : float
            normalized viewport x-coordinate (0.0 to 1.0).
        y : float
            normalized viewport y-coordinate (0.0 to 1.0).

        Returns
        -------
        tuple[int, int]
            2D display coordinates (in pixels).
        """
        xr = vtkReference(x)
        yr = vtkReference(y)
        # noinspection PyTypeChecker
        self._renderer.NormalizedViewportToViewport(xr, yr)
        # noinspection PyTypeChecker
        self._renderer.ViewportToNormalizedDisplay(xr, yr)
        # noinspection PyTypeChecker
        self._renderer.NormalizedDisplayToDisplay(xr, yr)
        # noinspection PyTypeChecker
        return float(xr), float(yr)

    def _getNormalizedViewportFromDisplay(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert display coordinates to normalized viewport coordinates.

        Parameters
        ----------
        x : float
            2D display x-coordinate (in pixels).
        y : float
            2D display y-coordinate (in pixels).

        Returns
        -------
        tuple[float, float]
            normalized viewport coordinates (0.0 to 1.0).
        """
        xr = vtkReference(x)
        yr = vtkReference(y)
        # noinspection PyTypeChecker
        self._renderer.DisplayToNormalizedDisplay(xr, yr)
        # noinspection PyTypeChecker
        self._renderer.NormalizedDisplayToViewport(xr, yr)
        # noinspection PyTypeChecker
        self._renderer.ViewportToNormalizedViewport(xr, yr)
        # noinspection PyTypeChecker
        return float(xr), float(yr)

    def _getScreenFromDisplay(self, x: float, y: float) -> QPoint:
        """
        Convert display coordinates to global screen coordinates.
        This is used to position Qt widgets (like popup menus) over the VTK window.

        Parameters
        ----------
        x : float
            2D display x-coordinate (in pixels).
        y : float
            2D display y-coordinate (in pixels).

        Returns
        -------
        QPoint
            Global screen coordinates.
        """
        # < Revision 14/03/2025
        if platform == 'darwin':
            scale = 1.0
            xs = int(x / scale)
            ys = int((self._renderwindow.GetSize()[1] - y - 1) / scale)
            r = self.mapToGlobal(QPoint(xs, ys))
        else:
            # bug mapToGlobal in win32 platform
            px, py = self._renderwindow.GetPosition()
            scale = QApplication.primaryScreen().devicePixelRatio()
            x2 = px + int(x / scale)
            y2 = py + int((self._renderwindow.GetSize()[1] - y - 1) / scale)
            r = QPoint(x2, y2)
        return r
        # Revision 14/03/2025 >

    def _moveToTool(self, name: str) -> None:
        """
        Move the viewport's cross-sahped cursor to the position of a specified tool.

        Parameters
        ----------
        name : str
            name of the target tool (HandleWidget or LineWidget).
        """
        tool = self._tools[name]
        if tool is not None:
            if isinstance(tool, HandleWidget): p = tool.getPosition()
            elif isinstance(tool, LineWidget): p = tool.getPosition2()
            else: raise TypeError('parameter type {} is not str.'.format(type(tool)))
            self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)

    def _removePickedTool(self) -> None:
        """
        Remove the tool currently selected by the interactor's picker.
        Emits the ToolRemoved signal.
        """
        rep = self._interactor.GetPicker().GetViewProp()
        if rep.GetClassName() in ('vtkDistanceRepresentation2D',
                                  'vtkBiDimensionalRepresentation2D',
                                  'vtkAngleRepresentation2D',
                                  'vtkBorderRepresentation',
                                  'vtkTextRepresentation',
                                  'vtkOpenGLBillboardTextActor3D',
                                  'vtkPointHandleRepresentation3D',
                                  'vtkLineRepresentation'):
            if rep.GetClassName() == 'vtkOpenGLBillboardTextActor3D':
                name = ''.join(rep.GetInput().split(sep='\n')[1])
                for widget in self._tools:
                    if widget.getName() == name:
                        # noinspection PyUnresolvedReferences
                        self.ToolRemoved.emit(self, widget, False)
                        widget.SetEnabled(0)
                        del self._tools[widget.getName()]
                        self._renderwindow.Render()
                        self._updateToolMenu()
                        break
            for widget in self._tools:
                if widget.GetRepresentation() == rep:
                    if rep.GetClassName() in ('vtkPointHandleRepresentation3D',
                                              'vtkLineRepresentation'):
                        # noinspection PyUnresolvedReferences
                        self.ToolRemoved.emit(self, widget, False)
                    widget.SetEnabled(0)
                    del self._tools[widget.getName()]
                    self._renderwindow.Render()
                    self._updateToolMenu()
                    break

    def _editPickedText(self) -> None:
        """
        Open a dialog to edit the text of a picked TextWidget tool.
        """
        rep = self._interactor.GetPicker().GetViewProp()
        if rep.GetClassName() == 'vtkTextRepresentation':
            for widget in self._tools:
                if widget.GetRepresentation() == rep:
                    x, y = widget.getPosition()
                    x, y = self._getDisplayFromNormalizedViewport(x, y)
                    p = self._getScreenFromDisplay(x, y)
                    p.setY(p.y() - self._dialog.height())
                    self._dialog.move(p)
                    self._edit.setText(widget.getInformationText())
                    if self._dialog.exec():
                        widget.setInformationText(self._edit.text())
                    break

    def _textProperties(self) -> None:
        """
        Placeholder method for editing the properties of a picked TextWidget.
        """
        rep = self._interactor.GetPicker().GetViewProp()
        if rep.GetClassName() == 'vtkTextRepresentation':
            for widget in self._tools:
                if widget.GetRepresentation() == rep:
                    pass

    def _toolColor(self) -> None:
        """
        Open a color dialog to change the color and opacity of a picked tool.
        Emits the ToolColorChanged signal for 3D tools.
        """
        rep = self._interactor.GetPicker().GetViewProp()
        if rep.GetClassName() == 'vtkOpenGLBillboardTextActor3D':
            name = ''.join(rep.GetInput().split(sep='\n')[1])
            for widget in self._tools:
                if widget.getName() == name:
                    if isinstance(widget, vtkPointHandleRepresentation3D): rep = widget.GetHandleRepresentation()
                    elif isinstance(widget, vtkLineRepresentation): rep = widget.GetLineRepresentation()
        for widget in self._tools:
            if widget.GetRepresentation() == rep:
                # < Revision 18/03/2025
                # c = QColorDialog().getColor(title='Tool color', options=QColorDialog.DontUseNativeDialog)
                c = colorDialog(title='Tool color')
                # Revision 18/03/2025 >
                if c is not None:
                    if c.isValid():
                        widget.setColor((c.red() / 255, c.green() / 255, c.blue() / 255))
                        widget.setOpacity(c.alpha() / 255)
                        self._renderwindow.Render()
                        if rep.GetClassName() in ('vtkPointHandleRepresentation3D',
                                                  'vtkLineRepresentation'):
                            # self.ToolAttributesChanged.emit(self, widget)
                            # noinspection PyUnresolvedReferences
                            self.ToolColorChanged.emit(self, widget)

    def _textEditFinished(self) -> None:
        """
        Handle the editingFinished signal from the QLineEdit dialog used for TextWidget.
        Accepts or rejects the dialog based on whether text was entered.
        """
        if self._edit.text() == '': self._dialog.reject()
        else: self._dialog.accept()

    def _updateRuler(self, signal: bool = True) -> None:
        """
        Update the ruler's scale to reflect the current zoom level of the camera.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if self.getRulerVisibility():
            p1 = self._ruler.GetPoint1Coordinate().GetValue()
            p2 = self._ruler.GetPoint2Coordinate().GetValue()
            p1 = self._getDisplayFromNormalizedViewport(p1[0], p1[1])
            p1 = self._getWorldFromDisplay(p1[0], p1[1])
            p2 = self._getDisplayFromNormalizedViewport(p2[0], p2[1])
            p2 = self._getWorldFromDisplay(p2[0], p2[1])
            d = sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)
            f = 10 / d * 0.4
            self._ruler.SetRulerDistance(f)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, '_updateRuler', None)

    def _updateToolMenu(self) -> None:
        """
        Update the 'Move to target' submenu in the popup menu.
        Populates the menu with actions to move the cursor to each existing 3D tool.
        """
        v = False
        if self.hasTools():
            self._menuMoveTarget.clear()
            for tool in self._tools:
                # < Revision 10/11/2025
                # if isinstance(tool, HandleWidget):
                if tool.GetObjectName() == 'HandleWidget':
                    t = QAction(tool.getName(), self)
                    # noinspection PyUnresolvedReferences
                    t.triggered.connect(lambda state, x=tool.getName(): self._moveToTool(x))
                    self._menuMoveTarget.addAction(t)
                    v = True
                # elif isinstance(tool, LineWidget):
                elif tool.GetObjectName() == 'LineWidget':
                    t = QAction(tool.getName(), self)
                    # noinspection PyUnresolvedReferences
                    t.triggered.connect(lambda state, x=tool.getName(): self._moveToTool(x))
                    self._menuMoveTarget.addAction(t)
                    v = True
                # Revision 10/11/2025 >
        self._menuMoveTarget.menuAction().setVisible(v)

    # Public synchronisation event methods

    def synchroniseCursorPositionChanged(self, obj: QWidget, x: float, y: float, z: float) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by CursorPositionChanged PyQt signal.
        It is responsible for synchronizing the cross-shaped cursor position between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit CursorPositionChanged signal.
        x : float
            x-axis world coordinate of the cross-shaped cursor.
        y : float
            y-axis world coordinate of the cross-shaped cursor.
        z : float
            z-axis world coordinate of the cross-shaped cursor.
        """
        # < Revision 17/11/2025
        # use synchronisation flag attribute
        # if self != obj and self.hasVolume():
        if self != obj and self.hasVolume() and self.isSynchronised():
            self.setCursorWorldPosition(x, y, z, signal=False)
        # Revision 17/11/2025 >

    def synchroniseZoomChanged(self, obj: QWidget, z: float) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ZoomChanged PyQt signal.
        It is responsible for synchronizing zoom factor between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ZoomChanged signal.
        z : float
            zoom factor.
        """
        if self != obj and self.hasVolume():
            self.setZoom(z, signal=False)

    def synchroniseToolRemoved(self, obj: QWidget, tool: HandleWidget | LineWidget | None, alltools: bool = False) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolRemoved PyQt signal.
        It is responsible for synchronizing tool removal between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolRemoved signal.
        tool : HandleWidget | LineWidget | None
            tool to remove.
        alltools : bool (optional)
            remove all tools if True (default False).
        """
        if self != obj and self.hasVolume():
            # < Revision 02/05/2025
            if alltools: self.removeAllTools(signal=False)
            else:
                if isinstance(tool, HandleWidget | LineWidget | None):
                    # if alltools: self.removeAllTools(signal=False)
                    # else:
                    if len(self._tools) > 0:
                        if tool is not None and tool.getName() in self._tools:
                            self.removeTool(tool.getName(), signal=False)
                    # else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
                # else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))
            # Revision 02/05/2025 >

    def synchroniseToolMoved(self, obj: QWidget, tool: HandleWidget | LineWidget) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolMoved PyQt signal.
        It is responsible for synchronizing tool movement between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolMoved signal
        tool : HandleWidget | LineWidget
            tool to move
        """
        if self != obj and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    w = self._tools[tool.getName()]
                    # Synchronise only HandleWidget or LineWidget (not 2D Widgets)
                    if isinstance(w, HandleWidget):
                        w.setPosition(tool.getPosition())
                    elif isinstance(w, LineWidget):
                        w.setPosition1(tool.getPosition1())
                        w.setPosition2(tool.getPosition2())
                    self._renderwindow.Render()
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseToolColorChanged(self, obj: QWidget, tool: HandleWidget | LineWidget) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolColorChanged PyQt signal.
        It is responsible for synchronizing tool color between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolColorChanged signal.
        tool : HandleWidget | LineWidget
            synchronize the color of this tool.
        """
        if self != obj and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    w = self._tools[tool.getName()]
                    if isinstance(w, (HandleWidget, LineWidget)):
                        w.setColor(tool.getColor())
                        self._renderwindow.Render()
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseToolAttributesChanged(self, obj: QWidget, tool: HandleWidget | LineWidget) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolAttributesChanged PyQt signal.
        It is responsible for synchronizing tool attributes between AbstractViewWidget instances.

        Tool attributes are as follows: text, text visbility, text offset, font size, font style (bold, italic),
        font family, color, selected color, opacity, point size, line width, handle size, tolerance, rendering
        attributes (render points as spheres, render lines as tube, interpolation, tube radius, metallic, roughness,
        ambient, specular, specular power).

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolAttributesChanged signal.
        tool : HandleWidget | LineWidget
            synchronize attributes of this tool.
        """
        if self != obj and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    w = self._tools[tool.getName()]
                    if isinstance(w, (HandleWidget, LineWidget)):
                        w.copyAttributesFrom(tool)
                        self._renderwindow.Render()
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseToolAdded(self, obj: QWidget, tool: HandleWidget | LineWidget) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolAdded PyQt signal.
        It is responsible for synchronizing tool creation between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolAdded signal.
        tool : HandleWidget | LineWidget
            synchronize the creation of this tool.
        """
        if self != obj and self.hasVolume() and self.getAcceptTools():
            if isinstance(tool, HandleWidget):
                self.addTarget(tool.getPosition(), tool.getName(), signal=False)
            elif isinstance(tool, LineWidget):
                self.addTrajectory(p1=tool.getPosition1(), p2=tool.getPosition2(), name=tool.getName(), signal=False)
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))
            # noinspection PyUnresolvedReferences
            self._tools[tool.getName()].copyAttributesFrom(tool)

    def synchroniseToolRenamed(self, obj: QWidget, tool: HandleWidget | LineWidget, name: str) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ToolRenamed PyQt signal.
        It is responsible for synchronizing tool name between AbstractViewWidget instances.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ToolRenamed signal.
        tool : HandleWidget | LineWidget
            synchronize the name of this tool.
        name : str
            tool name.
        """
        if obj != self and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    self._tools[tool.getName()].setName(name)
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseViewMethodCalled(self, obj: QWidget, function: str, param: Any) -> None:
        """
        Method of synchronisation between AbstractViewWidget instances.
        This method is called by ViewMethodCalled PyQt signal.

        Parameters
        ----------
        obj : QWidget
            AbstractViewWidget instances that emit ViewMethodCalled signal.
        function : str
            name of the synchronisation function.
        param : Any
            parameter of the synchronisation function.
        """
        if obj != self and self.hasVolume():
            if hasattr(self, function):
                f = getattr(self, function)
                if param is None: f(signal=False)
                else: f(param, signal=False)

    # Public methods

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be called before destruction
    def finalize(self) -> None:
        """
        Method to be called before AbstractViewWidget instance destruction.
        It is used to avoid vtk error on windows platform (vtkWin32OpenGLRenderWindow error: 'wglMakeCurrent failed in
        MakeCurrent()')
        """
        self._window.Finalize()
    # Revision 08/03/2025 >

    def getDisplayScaleFactor(self) -> float:
        """
        Get the scale (i.e. zoom) factor applied to the display of all QWidgets.

        Returns
        -------
        float
            scale factor
        """
        return self.screen().devicePixelRatio()

    def displayOn(self) -> None:
        """
        Show the following items of the AbstractViewWidget instance:

        - information (top left, top right, bottom left, bottom right)
        - colorbar
        - orientation maker (bottom right)
        - ruler
        - cross-shaped cursor

        Items are displayed only if their individual visibility attribute is True.
        """
        if self._volume is not None:
            # Info
            self._initInfoLabels()
            v = self._action['showinfo'].isChecked()
            self._info['topleft'].SetVisibility(v and self._action['showident'].isChecked())
            self._info['topright'].SetVisibility(v and self._action['showimg'].isChecked())
            self._info['bottomleft'].SetVisibility(v and self._action['showacq'].isChecked())
            self._info['bottomright'].SetVisibility(v)
            # Colorbar
            self._initColorbar()
            self._colorbar.SetVisibility(self._action['showcolorbar'].isChecked())
            # Marker
            self._orientmarker.SetEnabled(self._action['showmarker'].isChecked())
            # Ruler
            self._ruler.SetVisibility(self._action['showruler'].isChecked())
            # Cursor
            # < Revision 24/07/2025
            # _initCursor() is always called by __init__()
            # if self._cursor is None: self._initCursor()
            # Revision 24/07/2025 >
            if self._cursor is not None: self._cursor.SetVisibility(self._action['showcursor'].isChecked())
            self._renderwindow.Render()

    def displayOff(self) -> None:
        """
        Hide the following items of the AbstractViewWidget instance:

        - information (top left, top right, bottom left, bottom right)
        - colorbar
        - orientation maker (bottom right)
        - ruler
        - cross-shaped cursor
        """
        # Info
        self._info['topright'].SetVisibility(False)
        self._info['topleft'].SetVisibility(False)
        self._info['bottomright'].SetVisibility(False)
        self._info['bottomleft'].SetVisibility(False)
        # Colorbar
        self._colorbar.SetVisibility(False)
        # Marker
        self._orientmarker.SetEnabled(False)
        # Cursor
        # < Revision 24/07/2025
        if self._cursor is not None: self._cursor.SetVisibility(False)
        # Revision 24/07/2025 >
        self._renderwindow.Render()

    def setSelectable(self, v: bool) -> None:
        """
        Choose if the AbstractViewWidget instance is selectable.
        An AbstractViewWidget instance is selected by left-click.
        Selection is indicated by a white frame.
        """
        if isinstance(v, bool): self._frame = v
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def isSelectable(self) -> bool:
        """
        Check whether the AbstractViewWidget instance is selectable.

        Returns
        -------
        bool
            True if the AbstractViewWidget instance is selectable, False otherwise
        """
        return self._frame

    def isSelected(self) -> bool:
        """
        Check whether the AbstractViewWidget instance is selected.

        Returns
        -------
        bool
            True if the AbstractViewWidget instance is selected, False otherwise
        """
        return self.frameShape() > 0

    def select(self, signal: bool = True) -> None:
        """
        Select the AbstractViewWidget instance.
        Selection is indicated by a white frame.

        Parameters
        ----------
        signal : bool (optional)
            emit a selected PyQt signal if True (default True).
        """
        # < Revision 16/03/2025
        # noinspection PyTypeChecker
        self.setFrameShape(QFrame.Box)
        if platform == 'win32': self.setStyleSheet('border-color: #FFFFFF')
        # Revision 16/03/2025 >
        if signal:
            # noinspection PyUnresolvedReferences
            self.Selected.emit(self)

    def unselect(self) -> None:
        """
        Unselect the AbstractViewWidget instance.
        """
        # < Revision 16/03/2025
        # noinspection PyTypeChecker
        self.setFrameShape(QFrame.NoFrame)
        if platform == 'win32': self.setStyleSheet('border-color: #000000')
        # Revision 16/03/2025 >

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the AbstractViewWidget instance.

        Parameters
        ----------
        name : str
            name attribute of the AbstractViewWidget instance
        """
        if isinstance(name, str): self._name = name
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self) -> str:
        """
        Get the name attribute of the AbstractViewWidget instance.

        Returns
        -------
        str
            name attribute of the AbstractViewWidget instance
        """
        return self._name

    # < Revision 12/12/2024
    def setTitle(self, title: str) -> None:
        """
        Set the title attribute of the AbstractViewWidget instance.
        This title is displayed in the middle of the top part of the view area.

        Parameters
        ----------
        title : str
            title attribute of the AbstractViewWidget instance
        """
        self._title = title
    # Revision 12/12/2024 >

    # < Revision 12/12/2024
    def getTitle(self) -> str:
        """
        Get the title attribute of the AbstractViewWidget instance.
        This title is displayed in the middle of the top part of the view area.

        Returns
        -------
        str
            title attribute of the AbstractViewWidget instance
        """
        return self._title
    # Revision 12/12/2024 >

    def isEmpty(self) -> bool:
        """
        Check whether the volume attribute of the AbstractViewWidget instance is empty.

        Returns
        -------
        bool
            True if no SisypheVolume is displayed in the AbstractViewWidget instance, False otherwise
        """
        return self._volume is None

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the volume attribute of the AbstractViewWidget instance.
        This attribute is the SisypheVolume displayed in the AbstractViewWidget instance.

        Parameters
        ----------
        volume : SisypheVolume
            SisypheVolume to display in the AbstractViewWidget instance.
        """
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self.displayOn()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeVolume(self) -> None:
        """
        Clear the volume attribute of the AbstractViewWidget instance.
        No volume is displayed in the AbstractViewWidget instance.
        """
        if self.hasVolume():
            self._volume = None
            self.removeAllTools(signal=False)
            self.displayOff()

    def getVolume(self) -> SisypheVolume:
        """
        Get the volume attribute of the AbstractViewWidget instance.
        This attribute is the SisypheVolume displayed in the AbstractViewWidget instance.

        Returns
        -------
        SisypheVolume
            SisypheVolume displayed in the AbstractViewWidget instance.
        """
        return self._volume

    def hasVolume(self) -> bool:
        """
        Check whether the volume attribute of the AbstractViewWidget instance is not empty.

        Returns
        -------
        bool
            True if a SisypheVolume is defined and displayed in the AbstractViewWidget instance, False otherwise
        """
        return self._volume is not None

    def getRenderWindow(self) -> vtkRenderWindow:
        """
        Get the vtkRenderWindow attribute of the AbstractViewWidget instance.
        Rendering window class where renderers draw their images.
        https://vtk.org/doc/nightly/html/classvtkRenderWindow.html

        Returns
        -------
        vtkRenderWindow
        """
        return self._renderwindow

    def getRenderer(self) -> vtkRenderer:
        """
        Get the vtkRenderer attribute of the AbstractViewWidget instance that manages the volume display.
        https://vtk.org/doc/nightly/html/classvtkRenderer.html

        Returns
        -------
        vtkRenderer
        """
        return self._renderer

    def get2DRenderer(self) -> vtkRenderer:
        """
        Get the vtkRenderer attribute of the AbstractViewWidget instance that manages the 2D display (information,
        colorbar, orientation maker, ruler, cross-shaped cursor) in front of the volume.
        https://vtk.org/doc/nightly/html/classvtkRenderer.html

        Returns
        -------
        vtkRenderer
        """
        return self._renderer2D

    # < Revision 20/10/2025
    # def getObjectRenderer(self):
    #    return self._objetrenderer
    # Revision 20/10/2025 >

    def getWindowInteractor(self) -> vtkRenderWindowInteractor:
        """
        Get the vtkRenderWindowInteractor attribute of the AbstractViewWidget instance.
        Platform-independent class that handle routing of mouse/key/timer messages.
        https://vtk.org/doc/nightly/html/classvtkRenderWindowInteractor.html

        Returns
        -------
        vtkRenderWindowInteractor
        """
        return self._interactor

    def getAction(self) -> dict[str, QAction]:
        """
        Get a dict of all the available QActions defined in the AbstractViewWidget instance.
        A str key is used to address each QAction.
        https://doc.qt.io/qt-6/qaction.html

        Returns
        -------
            dict[str, QAction]
                key str, QAction name
        """
        return self._action

    def getPopup(self) -> QMenu:
        """
        Get the popup menu of the AbstractViewWidget instance.
        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._popup

    def getPopupVisibility(self) -> bool:
        """
        Get the popup submenu **Visibility** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - show cursor
        - show information
        - show orientation marker
        - show colorbar
        - show ruler
        - show tooltip
        - show all
        - hide all

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuVisibility

    def getPopupActions(self) -> QMenu:
        """
        Get the popup submenu **Actions** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - no action
        - zoom: left press + drag to change image zoom
        - move: left press + drag to change image position
        - windowing level: left press + drag to change windowing level
        - cursor follows mouse: the cross-shaped cursor follows the mouse pointer
        - centered cursor: the cross-shaped cursor always remains centered in the view

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuActions

    def getPopupInformation(self) -> QMenu:
        """
        Get the popup submenu **Information** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - Identity (displayed at the top left of the view)
        - Image attributes (displayed at the top right of the view)
        - Acquisition attributes (displayed at the bottom left of the view)
        - Orientation marker shape:

            - Cube
            - Head
            - Bust
            - Body
            - Axes
            - Brain

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuInformation

    def getPopupColorbarPosition(self) -> QMenu:
        """
        Get the popup submenu **Colorbar position** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - Left colorbar
        - Right colorbar
        - Top colorbar
        - Bottom colorbar

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuColorbarPos

    def getPopupRulerPosition(self) -> QMenu:
        """
        Get the popup submenu **Ruler position** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - Left ruler
        - Right ruler
        - Top ruler
        - Bottom ruler

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuRulerPos

    def getPopupTools(self) -> QMenu:
        """
        Get the popup submenu **Tools** of the AbstractViewWidget instance.
        This submenu provides the following options:

        - Distance
        - Orthogonal distances
        - Angle
        - Box
        - Text
        - Remove all
        - Target
        - Trajectory

        https://doc.qt.io/qt-6/qmenu.html

        Returns
        -------
            QMenu
        """
        return self._menuTools

    def popupMenuEnabled(self) -> None:
        """
        Enable the popup menu of the AbstractViewWidget instance.
        """
        self._menuflag = True

    def popupMenuDisabled(self) -> None:
        """
        Disable the popup menu of the AbstractViewWidget instance.
        """
        self._menuflag = False

    def popupVisibilityEnabled(self) -> None:
        """
        Enable the popup submenu **Visibility** of the AbstractViewWidget instance.
        """
        self._menuVisibility.menuAction().setVisible(True)

    def popupVisibilityDisabled(self) -> None:
        """
        Disable the popup submenu **Visibility** of the AbstractViewWidget instance.
        """
        self._menuVisibility.menuAction().setVisible(False)

    def popupActionsEnabled(self) -> None:
        """
        Enable the popup submenu **Actions** of the AbstractViewWidget instance.
        """
        self._menuActions.menuAction().setVisible(True)

    def popupActionsDisabled(self) -> None:
        """
        Disable the popup submenu **Actions** of the AbstractViewWidget instance.
        """
        self._menuActions.menuAction().setVisible(False)

    def popupColorbarPositionEnabled(self) -> None:
        """
        Enable the popup submenu **Colorbar position** of the AbstractViewWidget instance.
        """
        self._menuColorbarPos.menuAction().setVisible(True)

    def popupColorbarPositionDisabled(self) -> None:
        """
        Disable the popup submenu **Colorbar position** of the AbstractViewWidget instance.
        """
        self._menuColorbarPos.menuAction().setVisible(False)

    def popupToolsEnabled(self) -> None:
        """
        Enable the popup submenu **Tools** of the AbstractViewWidget instance.
        """
        self._menuTools.menuAction().setVisible(True)

    def popupToolsDisabled(self) -> None:
        """
        Disable the popup submenu **Tools** of the AbstractViewWidget instance.
        """
        self._menuTools.menuAction().setVisible(False)

    def getCamera(self) -> vtkCamera:
        """
        Get the vtkCamera attribute of the AbstractViewWidget instance.
        A camera class for 3D rendering that provides methods for positioning and orienting the viewpoint and focal
        point. https://vtk.org/doc/nightly/html/classvtkCamera.html

        Returns
        -------
            vtkCamera
        """
        return self._renderer.GetActiveCamera()

    def getTools(self) -> ToolWidgetCollection:
        """
        Get the ToolWidgetCollection associated with this viewport.

        Returns
        -------
        ToolWidgetCollection
            collection managing all tool widgets.
        """
        return self._tools

    def setNoActionFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'No action'. Disables move, zoom, and level/window actions.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['noflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setNoActionFlag', None)

    def setZoomFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'Zoom'. Left-click and drag will zoom the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['zoomflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setZoomFlag', None)

    def getZoomFlag(self) -> bool:
        """
        Check if the current mouse action is 'Zoom'.

        Returns
        -------
        bool
            True if the zoom flag is set, False otherwise.
        """
        return self._action['zoomflag'].isChecked()

    def setMoveFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'Move'. Left-click and drag will pan the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['moveflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setMoveFlag', None)

    def getMoveFlag(self) -> bool:
        """
        Check if the current mouse action is 'Move'.

        Returns
        -------
        bool
            True if the move flag is set, False otherwise.
        """
        return self._action['moveflag'].isChecked()

    def setLevelFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'Level/Window'. Left-click and drag will adjust the windowing.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['levelflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setLevelFlag', None)

    def getLevelFlag(self) -> bool:
        """
        Check if the current mouse action is 'Level/Window'.

        Returns
        -------
        bool
            True if the level/window flag is set, False otherwise.
        """
        return self._action['levelflag'].isChecked()

    def setFollowFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'Cursor follows mouse'. The cross-shaped cursor will track the mouse pointer.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['followflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setFollowFlag', None)

    def getFollowFlag(self) -> bool:
        """
        Check if the 'Cursor follows mouse' action is active.

        Returns
        -------
        bool
            True if the follow flag is set, False otherwise.
        """
        return self._action['followflag'].isChecked()

    # < Revision 09/01/2025
    # add getCenteredCursorFlag method
    def setCenteredCursorFlag(self, signal: bool = True) -> None:
        """
        Set the mouse action to 'Centered cursor'. The cross-shaped cursor remains at the viewport's center.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self._action['centeredflag'].setChecked(True)
        p = self.getCursorWorldPosition()
        self.setCursorWorldPosition(p[0], p[1], p[2])
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setCenteredCursorFlag', None)
    # Revision 09/01/2025 >

    # < Revision 09/01/2025
    # add getCenteredCursorFlag method
    def getCenteredCursorFlag(self) -> bool:
        """
        Check if the 'Centered cursor' action is active. The cross-shaped cursor remains at the viewport's center.

        Returns
        -------
        bool
            True if the centered cursor flag is set, False otherwise.
        """
        return self._action['centeredflag'].isChecked()
    # Revision 09/01/2025 >

    def setSynchronisation(self, v: bool) -> None:
        """
        Set the synchronization state of the viewport.

        Parameters
        ----------
        v : bool
            True to enable synchronization with other viewports, False to disable.
        """
        if isinstance(v, bool):
            self._action['synchronisation'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def synchronisationOn(self) -> None:
        """
        Enable synchronization with other viewports.
        """
        self.setSynchronisation(True)

    def synchronisationOff(self) -> None:
        """
        Disable synchronization with other viewports.
        """
        self.setSynchronisation(False)

    def getSynchronisation(self) -> bool:
        """
        Get the current synchronization state.

        Returns
        -------
        bool
            True if synchronization is enabled, False otherwise.
        """
        return self._action['synchronisation'].isChecked()

    def isSynchronised(self) -> bool:
        """
        Check if the viewport is synchronized with other viewports.

        Returns
        -------
        bool
            True if synchronization is enabled, False otherwise.
        """
        return self._action['synchronisation'].isChecked()

    def setInfoVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the information text overlays.

        Parameters
        ----------
        v : bool
            True to show the information, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            self._info['topleft'].SetVisibility(v and self._action['showident'].isChecked())
            self._info['topright'].SetVisibility(v and self._action['showimg'].isChecked())
            self._info['bottomleft'].SetVisibility(v and self._action['showacq'].isChecked())
            self._info['bottomright'].SetVisibility(v)
            self._action['showinfo'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the information text actors.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(True, signal)

    def setInfoVisibilityOff(self, signal: bool = True) -> None:
        """
         Hide the information text actors.

         Parameters
         ----------
         signal : bool (optional)
             If True, emits the ViewMethodCalled signal for synchronization (default True).
         """
        self.setInfoVisibility(False, signal)

    def getInfoVisibility(self) -> bool:
        """
        Check if the information text overlays are visible.

        Returns
        -------
        bool
            True if information is visible, False otherwise.
        """
        return self._action['showinfo'].isChecked()

    def setInfoIdentityVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the identity information (top-left).

        Parameters
        ----------
        v : bool
            True to show the identity information, False to hide it.
        signal : bool
            If True, emits the ViewMethodCalled signal for synchronization.
        """
        if isinstance(v, bool):
            self._action['showident'].setChecked(v)
            self._info['topleft'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoIdentityVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoIdentityVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the identity information text (top-left).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(True, signal)

    def setInfoIdentityVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the identity information text (top-left).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(False, signal)

    def getInfoIdentityVisibility(self) -> bool:
        """
        Check if the identity information is visible.

        Returns
        -------
        bool
            True if identity information is visible, False otherwise.
        """
        return self._action['showident'].isChecked()

    def setInfoVolumeVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the volume attributes information (top-right).

        Parameters
        ----------
        v : bool
            True to show the volume information, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            self._action['showimg'].setChecked(v)
            self._info['topright'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoVolumeVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoVolumeVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the volume attributes information text (top-right).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(True, signal)

    def setInfoVolumeVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the volume attributes information text (top-right).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(False, signal)

    def getInfoVolumeVisibility(self) -> bool:
        """
        Check if the volume attributes information is visible.

        Returns
        -------
        bool
            True if volume information is visible, False otherwise.
        """
        return self._action['showimg'].isChecked()

    def setInfoAcquisitionVisibility(self, v: bool, signal: bool = True) -> None:
        """
         Set the visibility of the acquisition information (bottom-left).

         Parameters
         ----------
         v : bool
             True to show the acquisition information, False to hide it.
         signal : bool (optional)
             If True, emits the ViewMethodCalled signal for synchronization (default True).
         """
        if isinstance(v, bool):
            self._action['showacq'].setChecked(v)
            self._info['bottomleft'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoAcquisitionVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoAcquisitionVisibilityOn(self, signal: bool = True) -> None:
        """
         Show the acquisition information text (bottom-left).

         Parameters
         ----------
         signal : bool (optional)
             If True, emits the ViewMethodCalled signal for synchronization (default True).
         """
        self.setInfoVisibility(True, signal)

    def setInfoAcquisitionVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the acquisition information text (bottom-left).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setInfoVisibility(False, signal)

    def getInfoAcquisitionVisibility(self) -> bool:
        """
        Check if the acquisition information is visible.

        Returns
        -------
        bool
            True if acquisition information is visible, False otherwise.
        """
        return self._action['showacq'].isChecked()

    def setColorbarVisibility(self, v, signal: bool = True) -> None:
        """
        Set the visibility of the colorbar.

        Parameters
        ----------
        v : bool
            True to show the colorbar, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            self._colorbar.SetVisibility(v)
            self._action['showcolorbar'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setColorbarVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))
        
    def setColorbarVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the colorbar.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarVisibility(True, signal)
        
    def setColorbarVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the colorbar.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarVisibility(False, signal)

    def getColorbarVisibility(self) -> bool:
        """
        Check if the colorbar is visible.

        Returns
        -------
        bool
            True if the colorbar is visible, False otherwise.
        """
        return self._action['showcolorbar'].isChecked()

    def getColorbar(self) -> vtkScalarBarActor:
        """
        Get the vtkScalarBarActor instance.

        Returns
        -------
        vtkScalarBarActor
            colorbar actor.
        """
        return self._colorbar

    def setColorbarPosition(self, pos: str = 'Left', signal: bool = True) -> None:
        """
        Set the position of the colorbar in the viewport.

        Parameters
        ----------
        pos : str (optional)
            position, one of 'Left', 'Right', 'Top', 'Bottom' (default 'Left').
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        pos = pos.lower()
        if pos == 'left':
            self._colorbar.SetMaximumWidthInPixels(150)
            self._colorbar.SetMaximumHeightInPixels(self._renderwindow.GetScreenSize()[1])
            self._colorbar.SetWidth(0.14)
            self._colorbar.SetHeight(0.5)
            self._colorbar.SetOrientationToVertical()
            self._colorbar.SetTextPositionToSucceedScalarBar()
            self._colorbar.GetPositionCoordinate().SetValue(0.05, 0.25)
            self._action['leftcolorbar'].setChecked(True)
        elif pos == 'right':
            self._colorbar.SetMaximumWidthInPixels(150)
            self._colorbar.SetMaximumHeightInPixels(self._renderwindow.GetScreenSize()[1])
            self._colorbar.SetWidth(0.14)
            self._colorbar.SetHeight(0.5)
            self._colorbar.SetOrientationToVertical()
            self._colorbar.SetTextPositionToPrecedeScalarBar()
            self._colorbar.GetPositionCoordinate().SetValue(0.81, 0.25)
            self._action['rightcolorbar'].setChecked(True)
        elif pos == 'bottom':
            self._colorbar.SetMaximumHeightInPixels(150)
            self._colorbar.SetMaximumWidthInPixels(self._renderwindow.GetScreenSize()[0])
            self._colorbar.SetWidth(0.5)
            self._colorbar.SetHeight(0.14)
            self._colorbar.SetOrientationToHorizontal()
            self._colorbar.SetTextPositionToSucceedScalarBar()
            self._colorbar.GetPositionCoordinate().SetValue(0.25, 0.03)
            self._action['bottomcolorbar'].setChecked(True)
        else:
            self._colorbar.SetMaximumHeightInPixels(150)
            self._colorbar.SetMaximumWidthInPixels(self._renderwindow.GetScreenSize()[0])
            self._colorbar.SetWidth(0.5)
            self._colorbar.SetHeight(0.14)
            self._colorbar.SetOrientationToHorizontal()
            self._colorbar.SetTextPositionToPrecedeScalarBar()
            self._colorbar.GetPositionCoordinate().SetValue(0.25, 0.83)
            self._action['topcolorbar'].setChecked(True)
        self._renderwindow.Render()
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setColorbarPosition', pos)

    def setColorbarPositionToLeft(self, signal: bool = True) -> None:
        """
        Move the colorbar to the left side of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarPosition('left', signal)

    def setColorbarPositionToRight(self, signal: bool = True) -> None:
        """
        Move the colorbar to the right side of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarPosition('right', signal)

    def setColorbarPositionToTop(self, signal: bool = True) -> None:
        """
        Move the colorbar to the top of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarPosition('top', signal)

    def setColorbarPositionToBottom(self, signal: bool = True) -> None:
        """
        Move the colorbar to the bottom of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setColorbarPosition('bottom', signal)

    def getColorbarPosition(self) -> str:
        """
        Get the current position of the colorbar.

        Returns
        -------
        str
            current colorbar position ('Left', 'Right', 'Top', or 'Bottom').
        """
        if self._action['leftcolorbar'].isChecked(): return 'Left'
        elif self._action['rightcolorbar'].isChecked(): return 'Right'
        elif self._action['topcolorbar'].isChecked(): return 'Top'
        else: return 'Bottom'

    # < Revision 03/12/2024
    # add hasHorizontalColorbar method
    def hasHorizontalColorbar(self) -> bool:
        """
        Check if the colorbar has a horizontal orientation.

        Returns
        -------
        bool
            True if the colorbar is on the left or right, False otherwise.
        """
        return self._action['leftcolorbar'].isChecked() or \
            self._action['rightcolorbar'].isChecked()
    # Revision 03/12/2024 >

    # < Revision 03/12/2024
    # add hasVerticalColorbar method
    def hasVerticalColorbar(self) -> bool:
        """
        Check if the colorbar has a vertical orientation.

        Returns
        -------
        bool
            True if the colorbar is on the top or bottom, False otherwise.
        """
        return self._action['topcolorbar'].isChecked() or \
            self._action['bottomcolorbar'].isChecked()
    # Revision 03/12/2024 >

    def setTooltipVisibility(self, v, signal: bool = True) -> None:
        """
        Set the visibility of tooltips for VTK widgets.

        Parameters
        ----------
        v : bool
            True to enable tooltips, False to disable them.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            if v is True: self.setToolTip(self._tooltipstr)
            else: self.setToolTip('')
            self._action['showtooltip'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setTooltipVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTooltipVisibilityOn(self, signal: bool = True) -> None:
        """
        Enable tooltips for VTK widgets.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setTooltipVisibility(True, signal)

    def setTooltipVisibilityOff(self, signal: bool = True) -> None:
        """
        Disable tooltips for VTK widgets.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setTooltipVisibility(False, signal)

    def getTooltipVisibility(self) -> bool:
        """
        Check if tooltips are visible.

        Returns
        -------
        bool
            True if tooltips are visible, False otherwise.
        """
        return self._action['showtooltip'].isChecked()

    def setRulerVisibility(self, v, signal: bool = True) -> None:
        """
        Set the visibility of the ruler.

        Parameters
        ----------
        v : bool
            True to show the ruler, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            self._ruler.SetVisibility(v)
            self._action['showruler'].setChecked(v)
            self._renderwindow.Render()
            self.setRulerPosition(self.getRulerPosition(), False)
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setRulerVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRulerVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the ruler.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerVisibility(True, signal)

    def setRulerVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the ruler.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerVisibility(False, signal)

    def getRulerVisibility(self) -> bool:
        """
        Check if the ruler is visible.

        Returns
        -------
        bool
            True if the ruler is visible, False otherwise.
        """
        return self._action['showruler'].isChecked()

    def getRuler(self) -> vtkAxisActor2D:
        """
        Get the vtkAxisActor2D instance used as a ruler.

        Returns
        -------
        vtkAxisActor2D
            ruler actor.
        """
        return self._ruler

    def setRulerPosition(self, pos: str = 'Left', signal: bool = True) -> None:
        """
        Set the position of the ruler in the viewport.

        Parameters
        ----------
        pos : str (optional)
            position, one of 'Left', 'Right', 'Top', 'Bottom' (default 'left').
        signal : bool
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        pos = pos.lower()
        if pos == 'left':
            self._ruler.GetPoint1Coordinate().SetValue(0.01, 0.3)
            self._ruler.GetPoint2Coordinate().SetValue(0.01, 0.7)
            self._action['leftruler'].setChecked(True)
        elif pos == 'right':
            self._ruler.GetPoint1Coordinate().SetValue(0.99, 0.7)
            self._ruler.GetPoint2Coordinate().SetValue(0.99, 0.3)
            self._action['rightruler'].setChecked(True)
        elif pos == 'bottom':
            self._ruler.GetPoint2Coordinate().SetValue(0.3, 0.01)
            self._ruler.GetPoint1Coordinate().SetValue(0.7, 0.01)
            self._action['bottomruler'].setChecked(True)
        else:
            self._ruler.GetPoint2Coordinate().SetValue(0.7, 0.99)
            self._ruler.GetPoint1Coordinate().SetValue(0.3, 0.99)
            self._action['topruler'].setChecked(True)
        self._updateRuler(signal=False)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setRulerPosition', pos)

    def setRulerPositionToLeft(self, signal: bool = True) -> None:
        """
        Move the ruler to the left side of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerPosition('left', signal)

    def setRulerPositionToRight(self, signal: bool = True) -> None:
        """
        Move the ruler to the right side of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerPosition('right', signal)

    def setRulerPositionToTop(self, signal: bool = True) -> None:
        """
         Move the ruler to the top of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerPosition('top', signal)

    def setRulerPositionToBottom(self, signal: bool = True) -> None:
        """
        Move the ruler to the bottom of the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setRulerPosition('bottom', signal)

    def getRulerPosition(self) -> str:
        """
        Get the current position of the ruler.

        Returns
        -------
        str
            current ruler position ('Left', 'Right', 'Top', or 'Bottom').
        """
        if self._action['leftruler'].isChecked(): return 'Left'
        elif self._action['rightruler'].isChecked(): return 'Right'
        elif self._action['topruler'].isChecked(): return 'Top'
        else: return 'Bottom'

    def getOrientationMarker(self) -> str:
        """
        Get the current shape of the orientation marker.

        Returns
        -------
        str
            marker shape ('Cube', 'Head', 'Bust', 'Body', or 'Axes').
        """
        if self._action['shapecube'].isChecked(): return 'Cube'
        elif self._action['shapehead'].isChecked(): return 'Head'
        elif self._action['shapebust'].isChecked(): return 'Bust'
        elif self._action['shapebody'].isChecked(): return 'Body'
        else: return 'Axes'

    def setOrientationMarker(self, markertype: str, signal: bool = True) -> None:
        """
        Set the shape and actor for the orientation marker widget.

        Parameters
        ----------
        markertype : str
            shape of marker to use ('cube', 'head', 'bust', 'body', 'brain', 'axes').
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if self._orientmarker is not None:
            self._orientmarker.SetEnabled(False)
            del self._orientmarker
        self._orientmarker = vtkOrientationMarkerWidget()
        markertype = markertype.lower()
        s = 0.0
        actor = None
        if markertype in ['head', 'bust', 'body', 'brain', 'cube']:
            if markertype != 'cube':
                import Sisyphe.gui
                path = split(Sisyphe.gui.__file__)[0]
                file = '{}.obj'.format(markertype)
                objname = join(path, 'mesh', file)
                if exists(objname):
                    r = vtkOBJReader()
                    r.SetFileName(objname)
                    r.Update()
                    mapper = vtkPolyDataMapper()
                    # noinspection PyArgumentList
                    mapper.SetInputConnection(r.GetOutputPort())
                    actor = vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetColor(0.9, 0.9, 0.9)
                    if markertype == 'bust':
                        actor.SetOrientation(90.0, 0.0, 0.0)
                        self._action['shapebust'].setChecked(True)
                        s = 0.2
                    elif markertype == 'head':
                        actor.SetOrientation(90.0, 0.0, 180.0)
                        self._action['shapehead'].setChecked(True)
                        s = 0.2
                    elif markertype == 'body':
                        actor.SetOrientation(90.0, 0.0, 180.0)
                        self._action['shapebody'].setChecked(True)
                        s = 0.3
                    else:
                        actor.SetOrientation(0.0, 0.0, 0.0)
                        self._action['shapebrain'].setChecked(True)
                        s = 0.3
                else: markertype = 'cube'
        if markertype == 'cube':  # Annotated cube actor
            actor = vtkAnnotatedCubeActor()
            actor.SetXPlusFaceText('R')
            actor.SetXMinusFaceText('L')
            actor.SetYMinusFaceText('P')
            actor.SetYPlusFaceText('A')
            actor.SetZMinusFaceText('I')
            actor.SetZPlusFaceText('S')
            actor.SetZFaceTextRotation(90)
            actor.GetTextEdgesProperty().SetColor(0.2, 0.2, 0.2)
            actor.GetTextEdgesProperty().SetLineWidth(2)
            actor.GetCubeProperty().SetColor(0.9, 0.9, 0.9)
            self._action['shapecube'].setChecked(True)
            s = 0.15
        elif s == 0.0:  # axes actor
            markertype = 'axes'
            actor = vtkAxesActor()
            self._action['shapeaxes'].setChecked(True)
            s = 0.3
        self._orientmarker.SetOrientationMarker(actor)
        self._orientmarker.SetInteractor(self._interactor)
        self._orientmarker.SetViewport(1.0 - s, 0.0, 1.0, s)
        self._orientmarker.EnabledOn()
        self._orientmarker.InteractiveOff()
        self._orientmarker.SetEnabled(self._action['showmarker'].isChecked())
        self._renderwindow.Render()
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setOrientationMarker', markertype)

    def setOrientationMarkerToBody(self, signal: bool = True) -> None:
        """
        Set the orientation marker to a body shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('body', signal)

    def setOrientationMarkerToHead(self, signal: bool = True) -> None:
        """
        Set the orientation marker to a head shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('head', signal)

    def setOrientationMarkerToBust(self, signal: bool = True) -> None:
        """
        Set the orientation marker to a bust shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('bust', signal)

    def setOrientationMarkerToBrain(self, signal: bool = True) -> None:
        """
        Set the orientation marker to a brain shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('brain', signal)

    def setOrientationMarkerToCube(self, signal: bool = True) -> None:
        """
        Set the orientation marker to an annotated cube.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('cube', signal)

    def setOrientationMarkerToAxes(self, signal: bool = True) -> None:
        """
        Set the orientation marker to a 3D axes actor.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMarker('axes', signal)

    def setOrientationMakerVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the orientation marker.

        Parameters
        ----------
        v : bool
            True to show the marker, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool) and self._orientmarker is not None:
            self._orientmarker.SetEnabled(v)
            self._action['showmarker'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setOrientationMakerVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setOrientationMarkerVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the orientation marker.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMakerVisibility(True, signal)

    def setOrientationMarkerVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the orientation marker.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setOrientationMakerVisibility(False, signal)

    def getOrientationMarkerVisibility(self) -> bool:
        """
        Check if the orientation marker is visible.

        Returns
        -------
        bool
            True if the marker is visible, False otherwise.
        """
        return self._action['showmarker'].isChecked()

    def setCentralCrossVisibility(self, v: bool) -> None:
        """
        Set the visibility of the central cross.

        Parameters
        ----------
        v : bool
            True to show the cross, False to hide it.
        """
        if isinstance(v, bool) and self._cross is not None:
            self._cross.SetVisibility(v)
        else: raise TypeError('parameter functype is not bool or int.')

    def setCentralCrossVisibilityOn(self) -> None:
        """
        Show the central cross.
        """
        self.setCentralCrossVisibility(True)

    def setCentralCrossVisibilityOff(self) -> None:
        """
        Hide the central cross.
        """
        self.setCentralCrossVisibility(False)

    def getCentralCrossVisibility(self) -> bool:
        """
        Check if the central cross is visible.

        Returns
        -------
        bool
            True if the cross is visible, False otherwise.
        """
        return self._cross.GetVisibility() > 0

    def setCentralCrossOpacity(self, v: float):
        """
        Set the opacity of the central cross.

        Parameters
        ----------
        v : float
            Opacity value between 0.0 (transparent) and 1.0 (opaque).
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._cross.GetProperty().SetOpacity(v)
            else: raise ValueError('parameter value is not between 0.0 and 1.0.')
        else: raise TypeError('parameter functype is not float.')

    def getCentralCrossOpacity(self) -> float:
        """
        Get the opacity of the central cross.

        Returns
        -------
        float
            opacity value.
        """
        return self._cross.GetProperty().GetOpacity()

    def setCursorVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the cross-shaped cursor.

        Parameters
        ----------
        v : bool
            True to show the cursor, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, bool):
            if self._cursor is not None: self._cursor.SetVisibility(v)
            self._action['showcursor'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setCursorVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCursorVisibilityOn(self, signal: bool = True) -> None:
        """
        Show the cross-shaped cursor.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setCursorVisibility(True, signal)

    def setCursorVisibilityOff(self, signal: bool = True) -> None:
        """
        Hide the cross-shaped cursor.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setCursorVisibility(False, signal)

    def getCursorVisibility(self) -> bool:
        """
        Check if the cross-shaped cursor is visible.

        Returns
        -------
        bool
            True if the cursor is visible, False otherwise.
        """
        return self._action['showcursor'].isChecked()

    # < Revision 19/12/2024
    # add setCursorOpacity method
    def setCursorOpacity(self, v: float, signal: bool = True) -> None:
        """
        Set the opacity of the cross-shaped cursor.

        Parameters
        ----------
        v : float
            Opacity value between 0.0 (transparent) and 1.0 (opaque).
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                # < Revision 07/01/2025
                # self._cross.GetProperty().SetOpacity(v)
                self._cursor.GetProperty().SetOpacity(v)
                # Revision 07/01/2025 >
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setLineOpacity', v)
            else: raise ValueError('parameter value is not between 0.0 and 1.0.')
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))
    # Revision 19/12/2024 >

    # < Revision 19/12/2024
    # add getCursorOpacity method
    def getCursorOpacity(self) -> float:
        """
        Get the opacity of the cross-shaped cursor.

        Returns
        -------
        float
            opacity value.
        """
        # < Revision 07/01/2025
        # return self._cross.GetProperty().GetOpacity()
        return self._cursor.GetProperty().GetOpacity()
        # Revision 07/01/2025 >
    # Revision 19/12/2024 >

    # < Revision 17/03/2025
    # add getFontFamily method
    def getFontFamily(self) -> str:
        """
        Get the current font family used for text overlays.

        Returns
        -------
        str
            font family name or path.
        """
        return self._ffamily
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontFamily method
    def setFontFamily(self, s: str, signal: bool = True) -> None:
        """
        Set the font family for all text overlays in the viewport.

        Parameters
        ----------
        s : str
            Font family name ('Arial', 'Courier', 'Times') or path to a .ttf/.otf file.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(s, str):
            if s in ('Arial', 'Courier', 'Times'):
                self._ffamily = s
                self._info['topright'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['topleft'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['bottomright'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['bottomleft'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['topcenter'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['leftcenter'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['rightcenter'].GetTextProperty().SetFontFamilyAsString(s)
                self._info['bottomcenter'].GetTextProperty().SetFontFamilyAsString(s)
                self._colorbar.GetLabelTextProperty().SetFontFamilyAsString(s)
                self._tools.setFontFamily(s)
            else:
                if exists(s) and splitext(s)[1] in ('.ttf', '.otf'):
                    self._ffamily = s
                    self._info['topright'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['topleft'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['bottomright'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['bottomleft'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['topcenter'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['leftcenter'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['rightcenter'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['bottomcenter'].GetTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._colorbar.GetLabelTextProperty().SetFontFamily(VTK_FONT_FILE)
                    self._info['topright'].GetTextProperty().SetFontFile(s)
                    self._info['topleft'].GetTextProperty().SetFontFile(s)
                    self._info['bottomright'].GetTextProperty().SetFontFile(s)
                    self._info['bottomleft'].GetTextProperty().SetFontFile(s)
                    self._info['topcenter'].GetTextProperty().SetFontFile(s)
                    self._info['leftcenter'].GetTextProperty().SetFontFile(s)
                    self._info['rightcenter'].GetTextProperty().SetFontFile(s)
                    self._info['bottomcenter'].GetTextProperty().SetFontFile(s)
                    self._colorbar.GetLabelTextProperty().SetFontFile(s)
                    self._tools.setFontFamily(s)
                else:  # Default
                    self._ffamily = 'Arial'
                    self._info['topright'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['topleft'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['bottomright'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['bottomleft'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['topcenter'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['leftcenter'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['rightcenter'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._info['bottomcenter'].GetTextProperty().SetFontFamilyAsString('Arial')
                    self._colorbar.GetLabelTextProperty().SetFontFamilyAsString('Arial')
                    self._tools.setFontFamily('Arial')
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setFontFamily', s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add getFontSize method
    def getFontSize(self) -> int:
        """
        Get the base font size for text overlays.

        Returns
        -------
        int
            The base font size.
        """
        return self._fsize
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontSize method
    def setFontSize(self, s: int, signal: bool = True) -> None:
        """
        Set the base font size for all text overlays.
        The final size is `s * font_scale`.

        Parameters
        ----------
        s : int
            base font size.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(s, int):
            self._fsize = s
            s = int(self._fsize * self._fscale)
            # Revision 17/03/2025 >
            self._info['topright'].GetTextProperty().SetFontSize(s)
            self._info['topleft'].GetTextProperty().SetFontSize(s)
            self._info['bottomright'].GetTextProperty().SetFontSize(s)
            self._info['bottomleft'].GetTextProperty().SetFontSize(s)
            self._info['topcenter'].GetTextProperty().SetFontSize(s)
            self._info['leftcenter'].GetTextProperty().SetFontSize(s)
            self._info['rightcenter'].GetTextProperty().SetFontSize(s)
            self._info['bottomcenter'].GetTextProperty().SetFontSize(s)
            self._colorbar.GetLabelTextProperty().SetFontSize(s)
            self._tooltip.GetBalloonRepresentation().GetTextProperty().SetFontSize(s)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setFontSize', self._fsize)
        else: raise TypeError('parameter type {} is not int.'.format(type(s)))
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontScale method
    def setFontScale(self, s: float, signal: bool = True) -> None:
        """
        Set the scale factor for all text overlays.
        The final size is `font_size * s`.

        Parameters
        ----------
        s : float
            font scale factor (clamped between 0.5 and 2.0).
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(s, float):
            if s < 0.5: s = 0.5
            elif s > 2.0: s = 2.0
            self._fscale = s
            s = int(self._fsize * self._fscale)
            # Revision 17/03/2025 >
            self._info['topright'].GetTextProperty().SetFontSize(s)
            self._info['topleft'].GetTextProperty().SetFontSize(s)
            self._info['bottomright'].GetTextProperty().SetFontSize(s)
            self._info['bottomleft'].GetTextProperty().SetFontSize(s)
            self._info['topcenter'].GetTextProperty().SetFontSize(s)
            self._info['leftcenter'].GetTextProperty().SetFontSize(s)
            self._info['rightcenter'].GetTextProperty().SetFontSize(s)
            self._info['bottomcenter'].GetTextProperty().SetFontSize(s)
            self._colorbar.GetLabelTextProperty().SetFontSize(s)
            self._tooltip.GetBalloonRepresentation().GetTextProperty().SetFontSize(s)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setFontScale', self._fscale)
        else: raise TypeError('parameter type {} is not float.'.format(type(s)))
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add getFontScale method
    def getFontScale(self) -> float:
        """
        Get the current font scale factor.

        Returns
        -------
        float
            font scale factor.
        """
        return self._fscale
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontSizeScale method
    def setFontSizeScale(self, s: tuple[int, float], signal: bool = True) -> None:
        """
        Set both the base font size and scale factor simultaneously.

        Parameters
        ----------
        s : tuple[int, float]
            A tuple containing the base font size and the scale factor.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(s, tuple):
            if isinstance(s[0], int): self._fsize = s[0]
            if isinstance(s[1], float): self._fscale = s[1]
            s = int(self._fsize * self._fscale)
            # Revision 17/03/2025 >
            self._info['topright'].GetTextProperty().SetFontSize(s)
            self._info['topleft'].GetTextProperty().SetFontSize(s)
            self._info['bottomright'].GetTextProperty().SetFontSize(s)
            self._info['bottomleft'].GetTextProperty().SetFontSize(s)
            self._info['topcenter'].GetTextProperty().SetFontSize(s)
            self._info['leftcenter'].GetTextProperty().SetFontSize(s)
            self._info['rightcenter'].GetTextProperty().SetFontSize(s)
            self._info['bottomcenter'].GetTextProperty().SetFontSize(s)
            self._colorbar.GetLabelTextProperty().SetFontSize(s)
            self._tooltip.GetBalloonRepresentation().GetTextProperty().SetFontSize(s)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setFontSizeScale', (self._fsize, self._fscale))
        else: raise TypeError('parameter type {} is not tuple.'.format(type(s)))
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontProperties method
    def setFontProperties(self, s: tuple[str | None, int | None, float | None], signal: bool = True) -> None:
        """
        Set the font family, base size, and scale factor simultaneously.

        Parameters
        ----------
        s : tuple[str | None, int | None, float | None]
            A tuple containing font family, base size, and scale factor. None values are ignored.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(s, tuple):
            if isinstance(s[0], str): self._ffamily = s[0]
            if isinstance(s[1], int): self._fsize = s[1]
            if isinstance(s[2], float): self._fscale = s[2]
            # Revision 17/03/2025 >
            self.setFontSizeScale((self._fsize, self._fscale), signal=False)
            self.setFontFamily(self._ffamily, signal=False)
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setFontProperties', (self._ffamily, self._fsize, self._fscale))
        else: raise TypeError('parameter type {} is not tuple.'.format(type(s)))
    # Revision 17/03/2025 >

    def setLineOpacity(self, v: float, signal: bool = True) -> None:
        """
        Set the opacity for all line-based overlays (text, cursors, tools).

        Parameters
        ----------
        v : float
            Opacity value between 0.0 (transparent) and 1.0 (opaque).
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._lalpha = v
                self._info['topright'].GetTextProperty().SetOpacity(v)
                self._info['topleft'].GetTextProperty().SetOpacity(v)
                self._info['bottomright'].GetTextProperty().SetOpacity(v)
                self._info['bottomleft'].GetTextProperty().SetOpacity(v)
                self._info['topcenter'].GetTextProperty().SetOpacity(v)
                self._info['leftcenter'].GetTextProperty().SetOpacity(v)
                self._info['rightcenter'].GetTextProperty().SetOpacity(v)
                self._info['bottomcenter'].GetTextProperty().SetOpacity(v)
                if self._cursor is not None: self._cursor.GetProperty().SetOpacity(v)
                self._cross.GetProperty().SetOpacity(v)
                self._ruler.GetProperty().SetOpacity(v)
                self._colorbar.GetLabelTextProperty().SetOpacity(v)
                self._tools.setOpacity(v)
                self._renderwindow.Render()
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setLineOpacity', v)
            else: raise ValueError('parameter value is not between 0.0 and 1.0.')
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getLineOpacity(self) -> float:
        """
        Get the current line opacity for overlays.

        Returns
        -------
        float
            opacity value.
        """
        return self._lalpha

    def setLineWidth(self, v: float, signal: bool = True) -> None:
        """
        Set the line width for all line-based overlays (cursors, tools).

        Parameters
        ----------
        v : float
            line width in pixels.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, float):
            self._lwidth = v
            if self._cursor is not None: self._cursor.GetProperty().SetLineWidth(v)
            self._ruler.GetProperty().SetLineWidth(v)
            self._cross.GetProperty().SetLineWidth(v)
            self._tools.setLineWidth(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setLineWidth', v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getLineWidth(self) -> float:
        """
        Get the current line width for overlays.

        Returns
        -------
        float
            line width in pixels.
        """
        return self._lwidth

    def setLineColor(self, c: list[float] | tuple[float, float, float], signal: bool = True) -> None:
        """
        Set the color for all non-selected line-based overlays (text, cursors, tools).

        Parameters
        ----------
        c : list[float] | tuple[float, float, float]
            color as an (r, g, b) tuple with values from 0.0 to 1.0.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(c, (list, tuple)):
            r = c[0]
            g = c[1]
            b = c[2]
            if 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0:
                self._lcolor = (r, g, b)
                self._info['topright'].GetTextProperty().SetColor(r, g, b)
                self._info['topleft'].GetTextProperty().SetColor(r, g, b)
                self._info['bottomright'].GetTextProperty().SetColor(r, g, b)
                self._info['bottomleft'].GetTextProperty().SetColor(r, g, b)
                self._info['topcenter'].GetTextProperty().SetColor(r, g, b)
                self._info['leftcenter'].GetTextProperty().SetColor(r, g, b)
                self._info['rightcenter'].GetTextProperty().SetColor(r, g, b)
                self._info['bottomcenter'].GetTextProperty().SetColor(r, g, b)
                if self._cursor is not None: self._cursor.GetProperty().SetColor(r, g, b)
                self._cross.GetProperty().SetColor(r, g, b)
                self._ruler.GetProperty().SetColor(r, g, b)
                self._colorbar.GetLabelTextProperty().SetColor(r, g, b)
                self._tools.setColor((r, g, b))
                self._renderwindow.Render()
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setLineColor', c)
            else: self._lcolor = (1.0, 1.0, 1.0)
        else: TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def setLineSelectedColor(self, c: list[float] | tuple[float, float, float], signal: bool = True) -> None:
        """
        Set the color for selected tools.

        Parameters
        ----------
        c : list[float] | tuple[float, float, float]
            color as an (r, g, b) tuple with values from 0.0 to 1.0.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(c, (list, tuple)):
            r = c[0]
            g = c[1]
            b = c[2]
            if 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0:
                self._slcolor = (r, g, b)
                self._tools.setSelectedColor((r, g, b))
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setLineSelectedColor', c)
            else: self._lcolor = (1.0, 1.0, 1.0)
        else: TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def getLineColor(self) -> tuple[float, float, float]:
        """
        Get the current color for non-selected overlays.

        Returns
        -------
        tuple[float, float, float]
            (r, g, b) color tuple.
        """
        return self._lcolor

    def getLineSelectedColor(self) -> tuple[float, float, float]:
        """
        Get the current color for selected tools.

        Returns
        -------
        tuple[float, float, float]
            (r, g, b) color tuple.
        """
        return self._slcolor

    def setCursorWorldPosition(self, x: float, y: float, z: float, signal: bool = True) -> None:
        """
        Set the 3D world position of the cross-shaped cursor.

        Parameters
        ----------
        x : float
            world x-coordinate.
        y : float
            world y-coordinate.
        z : float
            world z-coordinate.
        signal : bool (optional)
            If True and synchronization is on, emits the CursorPositionChanged signal (default True).
        """
        if self._volume is not None:
            p = self._getRoundedCoordinate([x, y, z])
            if self._axisconstraint > 0:
                n = self._axisconstraint - 1
                p[n] = self._volume.getCenter()[n]
            self._cursor.SetPosition(p)
            # synchronisation
            if self.isSynchronised() and signal:
                # noinspection PyUnresolvedReferences
                self.CursorPositionChanged.emit(self, p[0], p[1], p[2])

    def getCursorWorldPosition(self) -> tuple[float, float, float]:
        """
        Get the 3D world position of the cross-shaped cursor.

        Returns
        -------
        tuple[float, float, float]
            (x, y, z) world coordinates of the cross-shaped cursor.
        """
        return self._cursor.GetPosition()

    # < Revision 12/12/2024
    # add getCursorArrayPosition method
    def getCursorArrayPosition(self) -> tuple[int, int, int]:

        """
        Get the cross-shaped cursor position in array (voxel) coordinates.

        Returns
        -------
        tuple[int, int, int]
            (i, j, k) array coordinates of the cursor.
        """
        p = self._cursor.GetPosition()
        size = self._volume.getSize()
        spacing = self._volume.getSpacing()
        x = int(p[0] / spacing[0])
        y = int(p[1] / spacing[1])
        z = int(p[2] / spacing[2])
        if x < 0: x = 0
        if y < 0: y = 0
        if z < 0: z = 0
        if x > size[0] - 1: x = size[0] - 1
        if y > size[1] - 1: y = size[1] - 1
        if z > size[2] - 1: z = size[2] - 1
        return x, y, z
    # Revision 12/12/2024 >

    def setCursorEnabled(self) -> None:
        """
        Enable cross-shaped cursor updates.
        """
        self._cursorenabled = True

    def setCursorDisabled(self) -> None:
        """
        Disable cross-shaped cursor updates.
        """
        self._cursorenabled = False

    def isCursorEnabled(self) -> bool:
        """
        Check if the cross-shaped cursor is enabled.

        Returns
        -------
        bool
            True if the cursor is enabled, False otherwise.
        """
        return self._cursorenabled is True

    def setRoundedCursorCoordinatesEnabled(self) -> None:
        """
        Enable rounding of cross-shaped cursor coordinates to the nearest voxel.
        """
        self._roundedenabled = True

    def setRoundedCursorCoordinatesDisabled(self) -> None:
        """
        Disable rounding of cross-shaped cursor coordinates. Coordinates will be continuous.
        """
        self._roundedenabled = False

    def isRoundedCursorCoordinatesEnabled(self) -> bool:
        """
        Check if cross-shaped cursor coordinate rounding is enabled.

        Returns
        -------
        bool
            True if rounding is enabled, False otherwise.
        """
        return self._roundedenabled is True

    def setAxisConstraintToCursor(self, v: int, signal: bool = True) -> None:
        """
        Constrain cross-shaped cursor movement to a specific axis.

        Parameters
        ----------
        v : int
            axis constraint: 0=None, 1=x-axis, 2=y-axis, 3=z-axis.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(v, int):
            if 0 <= v < 5:
                self._axisconstraint = v
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setAxisConstraintToCursor', v)
            else: raise ValueError('parameter value {} is out of range (0 to 3).'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setNoAxisConstraintToCursor(self, signal: bool = True) -> None:
        """
        Remove any axis constraint from the cross-shaped cursor movement.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setAxisConstraintToCursor(0, signal)

    def setXAxisConstraintToCursor(self, signal: bool = True) -> None:
        """
        Constrain cross-shaped cursor movement to the x-axis.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setAxisConstraintToCursor(1, signal)

    def setYAxisConstraintToCursor(self, signal: bool = True) -> None:
        """
        Constrain cross-shaped cursor movement to the y-axis.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setAxisConstraintToCursor(2, signal)

    def setZAxisConstraintToCursor(self, signal: bool = True) -> None:
        """
        Constrain cross-shaped cursor movement to the z-axis.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setAxisConstraintToCursor(3, signal)

    def setMouseCursor(self, shape: int, signal: bool = True) -> None:
        """
        Set the shape of the mouse pointer in the render window.

        Parameters
        ----------
        shape : int
            VTK mouse pointer shape constant (e.g., VTK_CURSOR_ARROW).
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(shape, int):
            self._renderwindow.SetCurrentCursor(shape)
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setMouseCursor', shape)
        else: raise TypeError('parameter type {} is not int'.format(type(shape)))

    def setDefaultMouseCursor(self, signal: bool = True) -> None:
        """
        Set the mouse pointer to the default shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setMouseCursor(VTK_CURSOR_DEFAULT, signal)

    def setArrowMouseCursor(self, signal: bool = True) -> None:
        """
        Set the mouse pointer to an arrow shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setMouseCursor(VTK_CURSOR_ARROW, signal)

    def setHandMouseCursor(self, signal: bool = True) -> None:
        """
        Set the mouse pointer to a hand shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setMouseCursor(VTK_CURSOR_HAND, signal)

    def setCrossHairMouseCursor(self, signal: bool = True) -> None:
        """
        Set the mouse pointer to a crosshair shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setMouseCursor(VTK_CURSOR_CROSSHAIR, signal)

    def setSizeAllMouseCursor(self, signal: bool = True) -> None:
        """
        Set the mouse pointer to a 'size all' shape.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setMouseCursor(VTK_CURSOR_SIZEALL, signal)

    def getMouseCursor(self) -> int:
        """
        Get the current shape of the mouse pointer.

        Returns
        -------
        int
            VTK cursor shape constant.
        """
        return self._renderwindow.GetCurrentCursor()

    def hideAll(self, signal: bool = True) -> None:
        """
        Hide all optional overlays (cursor, info, colorbar, ruler, etc.).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits ViewMethodCalled signals for synchronization (default True).
        """
        self.setCursorVisibilityOff(signal)
        self.setInfoVisibilityOff(signal)
        self.setColorbarVisibilityOff(signal)
        self.setRulerVisibilityOff(signal)
        self.setOrientationLabelsVisibilityOff(signal)
        self.setOrientationMarkerVisibilityOff(signal)
        self.setTooltipVisibilityOff(signal)

    def showAll(self, signal: bool = True) -> None:
        """
        Show all optional overlays (cursor, info, colorbar, ruler, etc.).

        Parameters
        ----------
        signal : bool (optional)
            If True, emits ViewMethodCalled signals for synchronization (default True).
        """
        self.setCursorVisibilityOn(signal)
        self.setInfoVisibilityOn(signal)
        self.setColorbarVisibilityOn(signal)
        self.setRulerVisibilityOn(signal)
        self.setOrientationLabelsVisibilityOn(signal)
        self.setOrientationMarkerVisibilityOn(signal)
        self.setTooltipVisibilityOn(signal)

    def getTopLeftInfo(self) -> vtkTextActor:
        """
        Get the text actor for the top-left information display.

        Returns
        -------
        vtkTextActor
            The top-left text actor.
        """
        return self._info['topleft']

    def getTopRightInfo(self) -> vtkTextActor:
        """
        Get the text actor for the top-right information display.

        Returns
        -------
        vtkTextActor
            The top-right text actor.
        """
        return self._info['topright']

    def getBottomLeftInfo(self) -> vtkTextActor:
        """
        Get the text actor for the bottom-left information display.

        Returns
        -------
        vtkTextActor
            The bottom-left text actor.
        """
        return self._info['bottomleft']

    def getBottomRightInfo(self) -> vtkTextActor:
        """
        Get the text actor for the bottom-right information display.

        Returns
        -------
        vtkTextActor
            The bottom-right text actor.
        """
        return self._info['bottomright']

    def getPixmapCapture(self) -> QPixmap:
        """
        Capture the current viewport content as a QPixmap.

        Returns
        -------
        QPixmap
            pixmap of the current render window content.
        """
        if self.hasVolume():
            c = vtkWindowToImageFilter()
            c.SetInput(self._renderwindow)
            r = vtkImageExportToArray()
            # noinspection PyArgumentList
            r.SetInputConnection(c.GetOutputPort())
            cap = r.GetArray()
            d, h, w, ch = cap.shape
            cap = QImage(cap.data, w, h, 3 * w, QImage.Format_RGB888)
            cap = cap.mirrored(False, True)
            return QPixmap.fromImage(cap)
        else: raise AttributeError('Volume attribute is None.')

    def saveCapture(self) -> None:
        """
        Open a file dialog to save the current viewport content to an image file.
        Supported formats are BMP, JPG, PNG, and TIFF.
        """
        if self.hasVolume():
            name = QFileDialog.getSaveFileName(self, caption='Save view capture', directory=getcwd(),
                                               filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                               initialFilter='JPG (*.jpg)')[0]
            if name != '':
                c = vtkWindowToImageFilter()
                c.SetInput(self._renderwindow)
                w = {'.bmp': vtkBMPWriter(), '.jpg': vtkJPEGWriter(),
                     '.png': vtkPNGWriter(), '.tiff': vtkTIFFWriter()}
                path, ext = splitext(name)
                w = w[ext]
                # noinspection PyArgumentList
                w.SetInputConnection(c.GetOutputPort())
                w.SetFileName(name)
                try: w.Write()
                except Exception as err:
                    messageBox(self, 'Save view capture', text='error : {}'.format(err))

    def copyToClipboard(self) -> None:
        """
        Copy the current viewport content to the system clipboard as an image.
        """
        if self.hasVolume():
            # Quick and dirty with temporary disk file
            c = vtkWindowToImageFilter()
            c.SetInput(self._renderwindow)
            w = vtkBMPWriter()
            # noinspection PyArgumentList
            w.SetInputConnection(c.GetOutputPort())
            temp = join(gettempdir(), 'tmp.bmp')
            w.SetFileName(temp)
            try:
                w.Write()
                p = QPixmap(temp)
                QApplication.clipboard().setPixmap(p)
            except Exception as err:
                messageBox(self, 'Copy view capture to clipboard', text='error : {}'.format(err))
            finally:
                if exists(temp): remove(temp)

    def zoomIn(self) -> None:
        """
        Zoom in on the viewport by a fixed factor (1.1).
        """
        if self._renderer.GetActiveCamera().GetParallelScale() > 1:
            self._renderer.GetActiveCamera().Zoom(1.1)
            self._updateRuler()
            self._renderwindow.Render()
            # noinspection PyUnresolvedReferences
            self.ZoomChanged.emit(self, self._renderer.GetActiveCamera().GetParallelScale())

    def zoomOut(self) -> None:
        """
        Zoom out of the viewport by a fixed factor (0.9).
        """
        if self._renderer.GetActiveCamera().GetParallelScale() < 1000:
            self._renderer.GetActiveCamera().Zoom(0.9)
            self._updateRuler()
            self._renderwindow.Render()
            # noinspection PyUnresolvedReferences
            self.ZoomChanged.emit(self, self._renderer.GetActiveCamera().GetParallelScale())

    def zoomDefault(self) -> None:
        """
        Reset the viewport to the default zoom level.
        """
        self._renderer.GetActiveCamera().SetParallelScale(self._DEFAULTZOOM)
        self._updateRuler()
        self._renderwindow.Render()
        # noinspection PyUnresolvedReferences
        self.ZoomChanged.emit(self, self._DEFAULTZOOM)

    def setZoom(self, z: float, signal: bool = True) -> None:
        """
        Set the zoom level of the viewport to a specific value.

        Parameters
        ----------
        z : float
            parallel scale value for the camera. Smaller values mean more zoom.
        signal : bool (optional)
            If True, emits the ZoomChanged signal for synchronization (default True).
        """
        if isinstance(z, float):
            self._renderer.GetActiveCamera().SetParallelScale(z)
            self._updateRuler()
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ZoomChanged.emit(self, z)
        else: raise TypeError('parameter type {} is not float.'.format(type(z)))

    def getZoom(self) -> float:
        """
        Get the current zoom level of the viewport.

        Returns
        -------
        float
            parallel scale value of the camera.
        """
        return self._renderer.GetActiveCamera().GetParallelScale()

    def updateRender(self) -> None:
        """
        Force a re-render of the vtkRenderWindow.
        """
        self._renderwindow.Render()

    # Public tools methods

    def getToolCollection(self) -> ToolWidgetCollection:
        """
        Get the collection of all tool widgets associated with this viewport.

        Returns
        -------
        ToolWidgetCollection
            collection managing all tool widgets.
        """
        return self._tools

    # 2D Tools methods

    def setAcceptTools(self, v: bool) -> None:
        """
        Set whether the viewport can accept new tool widgets.

        Parameters
        ----------
        v : bool
            True to allow adding new tools, False to prevent it.
        """
        if isinstance(v, bool):
            self._accepttools = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setAcceptToolsOn(self) -> None:
        """
        Allow the viewport to accept new tool widgets.
        """
        self.setAcceptTools(True)

    def setAcceptToolsOff(self) -> None:
        """
        Prevent the viewport from accepting new tool widgets.
        """
        self.setAcceptTools(False)

    def getAcceptTools(self) -> bool:
        """
        Check if the viewport is currently accepting new tool widgets.

        Returns
        -------
        bool
            True if new tools can be added, False otherwise.
        """
        return self._accepttools

    def addDistanceTool(self, name: str = '') -> None:
        """
        Add a new 2D distance measurement tool to the viewport.

        Parameters
        ----------
        name : str (optional)
            optional name for the new tool (default '').
        """
        if self._accepttools:
            widget = self._tools.newDistanceWidget(name)
            # < Revision 16/03/2025
            # add font settings
            widget.setTextProperty(self._ffamily)
            widget.setColor(self._lcolor)
            widget.setSelectedColor(self._slcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            widget.EnabledOn()

    def addOrthogonalDistanceTool(self, name: str = '') -> None:
        """
        Add a new 2D orthogonal distance (bi-dimensional) measurement tool to the viewport.

        Parameters
        ----------
        name : str (optional)
            optional name for the new tool (default '').
        """
        if self._accepttools:
            widget = self._tools.newOrthogonalDistanceWidget(name)
            # < Revision 16/03/2025
            # add font settings
            widget.setTextProperty(self._ffamily)
            widget.setColor(self._lcolor)
            widget.setSelectedColor(self._slcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            widget.EnabledOn()

    def addAngleTool(self, name: str = '') -> None:
        """
        Add a new 2D angle measurement tool to the viewport.

        Parameters
        ----------
        name : str (optional)
            optional name for the new tool (default '').
        """
        if self._accepttools:
            widget = self._tools.newAngleWidget(name)
            # < Revision 16/03/2025
            # add font settings
            widget.setTextProperty(self._ffamily)
            widget.setColor(self._lcolor)
            widget.setSelectedColor(self._slcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            widget.EnabledOn()

    def addBoxTool(self, p: list[float] | tuple[float, float, float] | None = None, name: str = '') -> None:
        """
        Add a new 2D box widget tool to the viewport.

        Parameters
        ----------
        p : list[float] | tuple[float, float, float] | None (optional)
            initial world position for the tool. If None, the cross-shaped cursor position is used.
        name : str (optional)
            optional name for the new tool (default '').
        """
        if not p: p = self.getCursorWorldPosition()
        x, y = self._getDisplayFromWorld(p[0], p[1], p[2])
        x, y = self._getNormalizedViewportFromDisplay(x, y)
        widget = self._tools.newBoxWidget((x, y), name)
        widget.setColor(self._lcolor)
        widget.setOpacity(self._lalpha)
        # noinspection PyTypeChecker
        widget.AddObserver('InteractionEvent', self._onBoxInteractionEvent)
        # noinspection PyTypeChecker
        widget.AddObserver('StartInteractionEvent', self._onBoxStartInteractionEvent)
        # noinspection PyTypeChecker
        widget.AddObserver('EndInteractionEvent', self._onBoxEndInteractionEvent)
        widget.EnabledOn()

    def addTextTool(self, p: list[float] | tuple[float, float, float] | None = None) -> None:
        """
        Add a new 2D text annotation tool to the viewport.
        Opens a dialog to enter the text.

        Parameters
        ----------
        p : list[float] | tuple[float, float, float] | None (optional)
            initial world position for the tool. If None, the cursor position is used.
        """
        if not p: p = self.getCursorWorldPosition()
        x, y = self._getDisplayFromWorld(p[0], p[1], p[2])
        p = self._getScreenFromDisplay(x, y)
        p.setY(p.y() - self._dialog.height())
        self._dialog.move(p)
        self._edit.setText('')
        if self._dialog.exec():
            # Widget creation
            x, y = self._getNormalizedViewportFromDisplay(x, y)
            widget = self._tools.newTextWidget((x, y), self._edit.text())
            # < Revision 16/03/2025
            # add font settings
            widget.setTextProperty(self._ffamily)
            widget.setColor(self._lcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            widget.EnabledOn()

    def removeAll2DTools(self, signal: bool = True) -> None:
        """
        Remove all 2D measurement tools (Distance, OrthogonalDistance, Angle) from the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        n = self._tools.count()
        if n > 0:
            for i in range(n-1, -1, -1):
                if isinstance(self._tools[i], (DistanceWidget, OrthogonalDistanceWidget, AngleWidget)):
                    # noinspection PyTypeChecker
                    self._tools.remove(i)
            self._renderwindow.Render()
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'removeAll2DTools', None)

    # 3D Tools methods

    def addTarget(self,
                  p: list[float] | tuple[float, float, float] | None = None,
                  name: str = '',
                  signal: bool = True) -> HandleWidget:
        """
        Add a 3D target (handle) widget to the viewport.

        Parameters
        ----------
        p : list[float] | tuple[float, float, float] | None (optional)
            initial world position for the target. If None, the cross-shaped cursor position is used.
        name : str (optional)
            optional name for the new target (default '').
        signal : bool (optional)
            If True, emits the ToolAdded signal for synchronization (default True).

        Returns
        -------
        HandleWidget
            The newly created handle widget.
        """
        if self._accepttools:
            from Sisyphe.widgets.volumeViewWidget import VolumeViewWidget
            if p is None: p = self.getCursorWorldPosition()
            widget = self._tools.newHandleWidget(p, name)
            # < Revision 16/03/2025
            # add font settings
            widget.setFontFamily(self._ffamily)
            widget.setFontSize(int(self._fsize * self._fscale))
            widget.setColor(self._lcolor)
            widget.setSelectedColor(self._slcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            # noinspection PyTypeChecker
            widget.AddObserver('InteractionEvent', self._onTargetInteractionEvent)
            # noinspection PyTypeChecker
            widget.AddObserver('StartInteractionEvent', self._onTargetStartInteractionEvent)
            # noinspection PyTypeChecker
            widget.AddObserver('EndInteractionEvent', self._onTargetEndInteractionEvent)
            if isinstance(self, VolumeViewWidget): widget.setVolumeDisplay()
            else: widget.setSliceDisplay()
            widget.EnabledOn()
            # noinspection PyArgumentList
            self._tooltip.AddBalloon(widget.GetHandleRepresentation(), 'Target\n{}'.format(widget.getName()))
            self._renderwindow.Render()
            self._updateToolMenu()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ToolAdded.emit(self, widget)
            return widget
        else: raise AttributeError('accepttools attribute is False.')

    def addTrajectory(self,
                      p1: list[float] | tuple[float, float, float] | None = None,
                      p2: list[float] | tuple[float, float, float] | None = None,
                      angles: list[float] | tuple[float, float] | None = None,
                      length: float = 50.0,
                      name: str = '',
                      signal: bool = True) -> LineWidget:
        """
        Add a 3D trajectory (line) widget to the viewport.

        Parameters
        ----------
        p1 : list[float] | tuple[float, float, float] | None (optional)
            world position of the entry point.
        p2 : list[float] | tuple[float, float, float] | None (optional)
            world position of the target point. If None, the cursor position is used.
        angles : list[float] | tuple[float, float] | None (optional)
            Azimuth and elevation angles to define the trajectory from the target.
        length : float (optional)
            length in mm of the trajectory (default 50.0).
        name : str (optional)
            optional name for the new trajectory (default '').
        signal : bool (optional)
            If True, emits the ToolAdded signal for synchronization (default True).

        Returns
        -------
        LineWidget
            The newly created line widget.
        """
        if self._accepttools:
            from Sisyphe.widgets.volumeViewWidget import VolumeViewWidget
            if p2 is None: p2 = self.getCursorWorldPosition()  # Target
            if p1 is None: p1 = [p2[0], p2[1], p2[2] + length]  # Entry
            widget = self._tools.newLineWidget(p1, p2, name)
            # < Revision 16/03/2025
            # add font settings
            widget.setFontFamily(self._ffamily)
            widget.setFontSize(int(self._fsize * self._fscale))
            widget.setColor(self._lcolor)
            widget.setSelectedColor(self._slcolor)
            widget.setOpacity(self._lalpha)
            # Revision 16/03/2025 >
            if angles is not None:
                widget.setTrajectoryAngles(angles, length, deg=True)
            # noinspection PyTypeChecker
            widget.AddObserver('InteractionEvent', self._onTrajectoryInteractionEvent)
            # noinspection PyTypeChecker
            widget.AddObserver('StartInteractionEvent', self._onTrajectoryStartInteractionEvent)
            # noinspection PyTypeChecker
            widget.AddObserver('EndInteractionEvent', self._onTrajectoryEndInteractionEvent)
            if isinstance(self, VolumeViewWidget): widget.setVolumeDisplay()
            else: widget.setSliceDisplay()
            widget.EnabledOn()
            # noinspection PyArgumentList
            self._tooltip.AddBalloon(widget.GetLineRepresentation(), 'Trajectory\n{}'.format(widget.getName()))
            self._renderwindow.Render()
            self._updateToolMenu()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ToolAdded.emit(self, widget)
            return widget
        else: raise AttributeError('accepttools attribute is False.')

    def hasTools(self) -> bool:
        """
        Check if the viewport contains any tool widgets.

        Returns
        -------
        bool
            True if at least one tool exists, False otherwise.
        """
        return len(self._tools) > 0

    def getToolCount(self) -> int:
        """
        Get the number of tool widgets in the viewport.

        Returns
        -------
        int
            total number of tools.
        """
        return len(self._tools)

    def getTool(self, key: int | str) -> NamedWidget | HandleWidget | LineWidget:
        """
        Get a specific tool by its index or name.

        Parameters
        ----------
        key : int | str
            index or name of the tool to retrieve.

        Returns
        -------
        NamedWidget | HandleWidget | LineWidget
            requested tool widget.
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): return self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        if isinstance(key, str):
            if key in self._tools: return self._tools[key]
            else: raise ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def moveTool(self,
                 key: int | str | HandleWidget | LineWidget,
                 target: list[float] | tuple[float, float, float],
                 entry: list[float] | tuple[float, float, float] | None = None,
                 angles: list[float] | tuple[float, float] | None = None,
                 length: float | None = None,
                 signal: bool = True) -> None:
        """
        Move a specified tool to a new position.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to move, identified by index, name, or instance.
        target : list[float] | tuple[float, float, float]
            new target world position.
        entry : list[float] | tuple[float, float, float] | None, optional
            new entry world position (for LineWidget).
        angles : list[float] | tuple[float, float] | None, optional
            new angles to define the trajectory (for LineWidget).
        length : float | None, optional
            new length in mm for the trajectory (for LineWidget).
        signal : bool (optional)
            If True, emits the ToolMoved signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                if isinstance(key, HandleWidget):
                    # noinspection PyUnresolvedReferences
                    self._tools[key.getName()].setPosition(target)
                else:
                    if entry is not None:
                        # noinspection PyUnresolvedReferences
                        self._tools[key.getName()].setPosition1(entry)
                    elif angles is not None:
                        if length is None: length = 100.0
                        # noinspection PyUnresolvedReferences
                        self._tools[key.getName()].setTrajectoryAngles(angles, length, deg=True)
                    # noinspection PyUnresolvedReferences
                    self._tools[key.getName()].setPosition2(target)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ToolMoved.emit(self, key)
            else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def renameTool(self,
                   key: int | str | HandleWidget | LineWidget,
                   name: str,
                   signal: bool = True) -> None:
        """
        Rename a specified tool.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to rename, identified by index, name, or instance.
        name : str
            new name for the tool.
        signal : bool (optional)
            If True, emits the ToolRenamed signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ToolRenamed.emit(self, key, name)
                self._tools[key.getName()].setName(name)
            else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def copyToolAttributes(self,
                           key: int | str | HandleWidget | LineWidget,
                           tool: HandleWidget | LineWidget,
                           signal: bool = True) -> None:
        """
        Copy attributes from one tool to another.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            source tool, identified by index, name, or instance.
        tool : HandleWidget | LineWidget
            destination tool.
        signal : bool (optional)
            If True, emits the ToolAttributesChanged signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                # < Revision 04/12/2025
                if tool is not None and isinstance(tool, (HandleWidget, LineWidget)): tool.copyAttributesFrom(key)
                else: self._renderwindow.Render()
                # Revision 04/12/2025 >
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ToolAttributesChanged.emit(self, key)
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(key)))

    def removeTool(self,
                   key: int | str | HandleWidget | LineWidget,
                   signal: bool = True) -> None:
        """
        Remove a specified tool from the viewport.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to remove, identified by index, name, or instance.
        signal : bool (optional)
            If True, emits the ToolRemoved signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                index = self._tools.index(key.getName())
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ToolRemoved.emit(self, self._tools[index], False)
                if isinstance(self._tools[index], HandleWidget):
                    # noinspection PyUnresolvedReferences
                    self._tooltip.RemoveBalloon(self._tools[index].GetHandleRepresentation())
                elif isinstance(self._tools[index], LineWidget):
                    # noinspection PyUnresolvedReferences
                    self._tooltip.RemoveBalloon(self._tools[index].GetLineRepresentation())
                # noinspection PyUnresolvedReferences
                self._tools[index].SetEnabled(0)
                del self._tools[index]
                self._renderwindow.Render()
                self._updateToolMenu()
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def removeAllTools(self, signal: bool = True) -> None:
        """
        Remove all tool widgets (2D and 3D) from the viewport.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits a ToolRemoved signal for each 3D tool for synchronization (default True).
        """
        if len(self._tools) > 0:
            keys = self._tools.keys()
            for k in keys:
                if signal:
                    # < Revision 02/05/2025
                    # synchronize only if HandleWidget or LineWidget
                    if isinstance(self._tools[k], (HandleWidget, LineWidget)):
                        # noinspection PyUnresolvedReferences
                        self.ToolRemoved.emit(self, self._tools[k], False)
                    # Revision 02/05/2025 >
                self.removeTool(self._tools[k].getName())
            self._tools.clear()

    def setToolInteractive(self,
                           key: int | str | HandleWidget | LineWidget,
                           v: bool,
                           signal: bool = True) -> None:
        """
        Set the interactive state of a specified tool.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to modify, identified by index, name, or instance.
        v : bool
            True to make the tool interactive, False to make it non-interactive.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                index = self._tools.index(key.getName())
                if v is True:
                    # noinspection PyUnresolvedReferences
                    self._tools[index].On()
                else:
                    # noinspection PyUnresolvedReferences
                    self._tools[index].Off()
                if signal:
                    if v:
                        # noinspection PyUnresolvedReferences
                        self.ViewMethodCalled.emit(self, 'setToolInteractiveOn', self._tools[index])
                    else:
                        # noinspection PyUnresolvedReferences
                        self.ViewMethodCalled.emit(self, 'setToolInteractiveOff', self._tools[index])
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def setToolInteractiveOn(self,
                             key: int | str | HandleWidget | LineWidget,
                             signal: bool = True) -> None:
        """
        Make a specified tool interactive.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to modify, identified by index, name, or instance.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setToolInteractive(key, True, signal)

    def setToolInteractiveOff(self,
                              key: int | str | HandleWidget | LineWidget,
                              signal: bool = True) -> None:
        """
        Make a specified tool non-interactive.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to modify, identified by index, name, or instance.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        self.setToolInteractive(key, False, signal)

    def lockTool(self,
                 key: int | str | HandleWidget | LineWidget,
                 signal: bool = True) -> None:
        """
        Lock a tool, preventing it from being moved or modified by user interaction.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to lock, identified by index, name, or instance.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                index = self._tools.index(key.getName())
                # noinspection PyUnresolvedReferences
                self._tools[index].ProcessEventsOff()
                # noinspection PyUnresolvedReferences
                self._tools[index].ManagesCursorOff()
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'lockTool', self._tools[index])
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def unlockTool(self,
                   key: int | str | HandleWidget | LineWidget,
                   signal: bool = True) -> None:
        """
        Unlock a tool, allowing it to be moved or modified by user interaction.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to unlock, identified by index, name, or instance.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                index = self._tools.index(key.getName())
                # noinspection PyUnresolvedReferences
                self._tools[index].ProcessEventsOn()
                # noinspection PyUnresolvedReferences
                self._tools[index].ManagesCursorOn()
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'unlockTool', self._tools[index])
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def isToolLocked(self, key: int | str | HandleWidget | LineWidget) -> bool:
        """
        Check if a tool is locked.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            tool to check, identified by index, name, or instance.

        Returns
        -------
        bool
            True if the tool is locked, False otherwise.
        """
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                # noinspection PyUnresolvedReferences,PyTypeChecker
                return self._tools[key].GetProcessEvents()
            else: raise ValueError('tool {} is not in collection (_.tools attribute).'.format(key.getName()))
        else: raise TypeError('key parameter type {} is not HandleWidget or LineWidget.'.format(type(key)))

    # Abstract tool VTK event methods

    def _onBoxInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for vtkBoxWidget interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onBoxStartInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for vtkBoxWidget start interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onBoxEndInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for vtkBoxWidget end interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onTargetInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for HandleWidget interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onTargetStartInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for HandleWidget start interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    # noinspection PyUnusedLocal
    def _onTargetEndInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Callback for HandleWidget end interaction VTK events.
        Updates the cursor position and emits the ToolMoved signal.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        p = widget.getPosition()
        self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)
        # noinspection PyUnresolvedReferences
        self.ToolMoved.emit(self, widget)

    def _onTrajectoryInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for LineWidget interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onTrajectoryStartInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Abstract callback for LineWidget start interaction VTK events.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        pass

    def _onTrajectoryEndInteractionEvent(self, widget: vtk3DWidget, event: Any) -> None:
        """
        Callback for LineWidget end interaction VTK events.
        Updates the cross-sahep cursor position to the target point and emits the ToolMoved signal.

        Parameters
        ----------
        widget : vtk3DWidget
            caller vtkObject.
        event : Any
            event parameter.
        """
        p = widget.getPosition2()  # Target point position
        self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)
        # noinspection PyUnresolvedReferences
        self.ToolMoved.emit(self, widget)

    # Abstract private method

    def _initCursor(self) -> None:
        """
        Abstract method for cursor initialization.
        Subclasses must implement this to create their specific cursor actor.
        """
        pass

    # Private VTK event method

    def _onRightPressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Handle the right mouse button press VTK event.
        Shows the appropriate popup menu (main or tool-specific) at the mouse pointer location.

        Parameters
        ----------
        obj : vtkObject
            VTK object that triggered the event.
        evt_name : str
            name of the event (RightButtonPressEvent).
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        p = self._getScreenFromDisplay(x, y)
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        tag = True
        if n:
            prop = picker.GetViewProp()
            cname = prop.GetClassName()
            if cname in ('vtkDistanceRepresentation2D',
                         'vtkBiDimensionalRepresentation2D',
                         'vtkAngleRepresentation2D',
                         'vtkBorderRepresentation',
                         'vtkTextRepresentation',
                         'vtkOpenGLBillboardTextActor3D',
                         'vtkPointHandleRepresentation3D',
                         'vtkLineRepresentation'):
                # Show tool popup menu
                r = (cname == 'vtkTextRepresentation')
                self._action['edittext'].setVisible(r)
                self._action['textprop'].setVisible(r)
                self._toolpopup.popup(p)
                tag = False
        if tag and self._menuflag: self._popup.popup(p)

    def _onLeftPressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Handle the left mouse button press VTK event.
        Selects the widget if it is selectable.

        Parameters
        ----------
        obj : vtkObject
            VTK object that triggered the event.
        evt_name : str
            name of the event (LeftButtonPressEvent).
        """
        if self.isSelectable():
            if not self.isSelected(): self.select()

    # Abstract private VTK event methods

    def _onWheelForwardEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for mouse wheel forward VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            VTK object that triggered the event.
        evt_name : str
            name of the event (MouseWheelForwardEvent).
        """
        pass

    def _onWheelBackwardEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for mouse wheel backward VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            VTK object that triggered the event.
        evt_name : str
            name of the event (MouseWheelBackwardEvent).
        """
        pass

    def _onLeftReleaseEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for left mouse button release VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            The VTK object that triggered the event.
        evt_name : str
            The name of the event (LeftButtonReleaseEvent).
        """
        pass

    def _onMiddlePressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for middle mouse button press VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            The VTK object that triggered the event.
        evt_name : str
            The name of the event (MiddleButtonPressEvent).
        """
        pass

    def _onMouseMoveEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for mouse move VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            The VTK object that triggered the event.
        evt_name : str
            The name of the event (MouseMoveEvent).
        """
        pass

    def _onKeyPressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for key press VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            The VTK object that triggered the event.
        evt_name : str
            The name of the event (KeyPressEvent).
        """
        pass

    def _onKeyReleaseEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Abstract callback for key release VTK events. To be implemented by subclasses.

        Parameters
        ----------
        obj : vtkObject
            The VTK object that triggered the event.
        evt_name : str
            The name of the event (KeyReleaseEvent).
        """
        pass
