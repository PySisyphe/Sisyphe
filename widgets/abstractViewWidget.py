"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, Visualization, https://vtk.org/
"""

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

    Abstract class designed to provide common methods and functionalities that are shared among different types of
    display widgets. The class is responsible for handling common tasks such as displaying data, managing user
    interactions, and providing a consistent user interface. It encapsulates functionality related to displaying
    data, such as zooming, panning, and navigating through the data.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AbstractViewWidget

    Creation: 20/03/2022
    Last Revision: 02/05/2025
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

    def __init__(self, parent=None):
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
            Show informations (self._action['showinfo'])
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

    # Private methods

    def _initSettings(self):
        """
            Settings -> private attributes
            Revision 17/04/2023, addBundle devicePixelRation to manage font size
                                 self._fsize *= self.getDisplayScaleFactor()
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

    def _initInfoLabels(self):
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

    def _initColorbar(self):
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

    def _initCentralCross(self):
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

    def _getRoundedCoordinate(self, p):
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

    def _getWorldToMatrixCoordinate(self, p):
        if self._volume is not None:
            s = self._volume.getSpacing()
            r = list()
            r.append(int(round(p[0] / s[0])))
            r.append(int(round(p[1] / s[1])))
            r.append(int(round(p[2] / s[2])))
            return r
        else: raise AttributeError('Volume attribute is None.')

    def _getWorldFromDisplay(self, x, y):
        self._renderer.SetDisplayPoint(x, y, 0.0)
        # noinspection PyArgumentList
        self._renderer.DisplayToWorld()
        p = self._renderer.GetWorldPoint()
        return p[:3]

    def _getDisplayFromWorld(self, x, y, z):
        self._renderer.SetWorldPoint(x, y, z, 1.0)
        self._renderer.WorldToDisplay()
        p = self._renderer.GetDisplayPoint()
        return p[:2]

    def _getDisplayFromNormalizedViewport(self, x, y):
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

    def _getNormalizedViewportFromDisplay(self, x, y):
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

    def _getScreenFromDisplay(self, x, y):
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

    def _moveToTool(self, name):
        tool = self._tools[name]
        if tool is not None:
            if isinstance(tool, HandleWidget): p = tool.getPosition()
            elif isinstance(tool, LineWidget): p = tool.getPosition2()
            else: raise TypeError('parameter type {} is not str.'.format(type(tool)))
            self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)

    def _removePickedTool(self):
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

    def _editPickedText(self):
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

    def _textProperties(self):
        rep = self._interactor.GetPicker().GetViewProp()
        if rep.GetClassName() == 'vtkTextRepresentation':
            for widget in self._tools:
                if widget.GetRepresentation() == rep:
                    pass

    def _toolColor(self):
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

    def _textEditFinished(self):
        if self._edit.text() == '': self._dialog.reject()
        else: self._dialog.accept()

    def _updateRuler(self, signal=True):
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

    def _updateToolMenu(self):
        v = False
        if self.hasTools():
            self._menuMoveTarget.clear()
            for tool in self._tools:
                if isinstance(tool, HandleWidget):
                    t = QAction(tool.getName(), self)
                    # noinspection PyUnresolvedReferences
                    t.triggered.connect(lambda state, x=tool.getName(): self._moveToTool(x))
                    self._menuMoveTarget.addAction(t)
                    v = True
                elif isinstance(tool, LineWidget):
                    t = QAction(tool.getName(), self)
                    # noinspection PyUnresolvedReferences
                    t.triggered.connect(lambda state, x=tool.getName(): self._moveToTool(x))
                    self._menuMoveTarget.addAction(t)
                    v = True
        self._menuMoveTarget.menuAction().setVisible(v)

    # Public synchronisation event methods

    def synchroniseCursorPositionChanged(self, obj, x, y, z):
        if self != obj and self.hasVolume():
            self.setCursorWorldPosition(x, y, z, signal=False)

    def synchroniseZoomChanged(self, obj, z):
        if self != obj and self.hasVolume():
            self.setZoom(z, signal=False)

    def synchroniseToolRemoved(self, obj, tool, alltools=False):
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

    def synchroniseToolMoved(self, obj, tool):
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

    def synchroniseToolColorChanged(self, obj, tool):
        if self != obj and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    w = self._tools[tool.getName()]
                    if isinstance(w, (HandleWidget, LineWidget)):
                        w.setColor(tool.getColor())
                        self._renderwindow.Render()
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseToolAttributesChanged(self, obj, tool):
        if self != obj and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    w = self._tools[tool.getName()]
                    if isinstance(w, (HandleWidget, LineWidget)):
                        w.copyAttributesFrom(tool)
                        self._renderwindow.Render()
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseToolAdded(self, obj, tool):
        if self != obj and self.hasVolume() and self.getAcceptTools():
            if isinstance(tool, HandleWidget):
                self.addTarget(tool.getPosition(), tool.getName(), signal=False)
            elif isinstance(tool, LineWidget):
                self.addTrajectory(p1=tool.getPosition1(), p2=tool.getPosition2(), name=tool.getName(), signal=False)
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))
            # noinspection PyUnresolvedReferences
            self._tools[tool.getName()].copyAttributesFrom(tool)

    def synchroniseToolRenamed(self, obj, tool, name):
        if obj != self and self.hasVolume():
            if isinstance(tool, (HandleWidget, LineWidget)):
                if tool.getName() in self._tools:
                    self._tools[tool.getName()].setName(name)
                else: raise ValueError('tool name {} is not in SisypheToolCollection.'.format(tool.getName()))
            else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    def synchroniseViewMethodCalled(self, obj, function, param):
        if obj != self and self.hasVolume():
            if hasattr(self, function):
                f = getattr(self, function)
                if param is None: f(signal=False)
                else: f(param, signal=False)

    # Public methods

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be called before destruction
    def finalize(self):
        self._window.Finalize()
    # Revision 08/03/2025 >

    def getDisplayScaleFactor(self):
        return self.screen().devicePixelRatio()

    def displayOn(self):
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
            if self._cursor is None: self._initCursor()
            if self._cursor is not None: self._cursor.SetVisibility(self._action['showcursor'].isChecked())
            self._renderwindow.Render()

    def displayOff(self):
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
        self._cursor.SetVisibility(False)
        self._renderwindow.Render()

    def setSelectable(self, v):
        if isinstance(v, bool): self._frame = v
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def isSelectable(self):
        return self._frame

    def isSelected(self):
        return self.frameShape() > 0

    def select(self, signal=True):
        # < Revision 16/03/2025
        # noinspection PyTypeChecker
        self.setFrameShape(QFrame.Box)
        if platform == 'win32': self.setStyleSheet('border-color: #FFFFFF')
        # Revision 16/03/2025 >
        if signal:
            # noinspection PyUnresolvedReferences
            self.Selected.emit(self)

    def unselect(self):
        # < Revision 16/03/2025
        # noinspection PyTypeChecker
        self.setFrameShape(QFrame.NoFrame)
        if platform == 'win32': self.setStyleSheet('border-color: #000000')
        # Revision 16/03/2025 >

    def setName(self, name):
        if isinstance(name, str): self._name = name
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self):
        return self._name

    # < Revision 12/12/2024
    def setTitle(self, title):
        self._title = title
    # Revision 12/12/2024 >

    # < Revision 12/12/2024
    def getTitle(self):
        return self._title
    # Revision 12/12/2024 >

    def isEmpty(self):
        return self._volume is None

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self.displayOn()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeVolume(self):
        if self.hasVolume():
            self._volume = None
            self.removeAllTools(signal=False)
            self.displayOff()

    def getVolume(self):
        return self._volume

    def hasVolume(self):
        return self._volume is not None

    def getRenderWindow(self):
        return self._renderwindow

    def getRenderer(self):
        return self._renderer

    def get2DRenderer(self):
        return self._renderer2D

    def getObjectRenderer(self):
        return self._objetrenderer

    def getWindowInteractor(self):
        return self._interactor

    def getAction(self):
        return self._action

    def getPopup(self):
        return self._popup

    def getPopupVisibility(self):
        return self._menuVisibility

    def getPopupActions(self):
        return self._menuActions

    def getPopupInformation(self):
        return self._menuInformation

    def getPopupColorbarPosition(self):
        return self._menuColorbarPos

    def getPopupRulerPosition(self):
        return self._menuRulerPos

    def getPopupTools(self):
        return self._menuTools

    def popupMenuEnabled(self):
        self._menuflag = True

    def popupMenuDisabled(self):
        self._menuflag = False

    def popupVisibilityEnabled(self):
        self._menuVisibility.menuAction().setVisible(True)

    def popupVisibilityDisabled(self):
        self._menuVisibility.menuAction().setVisible(False)

    def popupActionsEnabled(self):
        self._menuActions.menuAction().setVisible(True)

    def popupActionsDisabled(self):
        self._menuActions.menuAction().setVisible(False)

    def popupColorbarPositionEnabled(self):
        self._menuColorbarPos.menuAction().setVisible(True)

    def popupColorbarPositionDisabled(self):
        self._menuColorbarPos.menuAction().setVisible(False)

    def popupToolsEnabled(self):
        self._menuTools.menuAction().setVisible(True)

    def popupToolsDisabled(self):
        self._menuTools.menuAction().setVisible(False)

    def getCamera(self):
        return self._renderer.GetActiveCamera()

    def getTools(self):
        return self._tools

    def setNoActionFlag(self, signal=True):
        self._action['noflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setNoActionFlag', None)

    def setZoomFlag(self, signal=True):
        self._action['zoomflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setZoomFlag', None)

    def getZoomFlag(self):
        return self._action['zoomflag'].isChecked()

    def setMoveFlag(self, signal=True):
        self._action['moveflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setMoveFlag', None)

    def getMoveFlag(self):
        return self._action['moveflag'].isChecked()

    def setLevelFlag(self, signal=True):
        self._action['levelflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setLevelFlag', None)

    def getLevelFlag(self):
        return self._action['levelflag'].isChecked()

    def setFollowFlag(self, signal=True):
        self._action['followflag'].setChecked(True)
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setFollowFlag', None)

    def getFollowFlag(self):
        return self._action['followflag'].isChecked()

    # < Revision 09/01/2025
    # add getCenteredCursorFlag method
    def setCenteredCursorFlag(self, signal=True):
        self._action['centeredflag'].setChecked(True)
        p = self.getCursorWorldPosition()
        self.setCursorWorldPosition(p[0], p[1], p[2])
        if signal:
            # noinspection PyUnresolvedReferences
            self.ViewMethodCalled.emit(self, 'setCenteredCursorFlag', None)
    # Revision 09/01/2025 >

    # < Revision 09/01/2025
    # add getCenteredCursorFlag method
    def getCenteredCursorFlag(self):
        return self._action['centeredflag'].isChecked()
    # Revision 09/01/2025 >

    def setSynchronisation(self, v):
        if isinstance(v, bool):
            self._action['synchronisation'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def synchronisationOn(self):
        self.setSynchronisation(True)

    def synchronisationOff(self):
        self.setSynchronisation(False)

    def getSynchronisation(self):
        return self._action['synchronisation'].isChecked()

    def isSynchronised(self):
        return self._action['synchronisation'].isChecked()

    def setInfoVisibility(self, v, signal=True):
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

    def setInfoVisibilityOn(self, signal=True):
        self.setInfoVisibility(True, signal)

    def setInfoVisibilityOff(self, signal=True):
        self.setInfoVisibility(False, signal)

    def getInfoVisibility(self):
        return self._action['showinfo'].isChecked()

    def setInfoIdentityVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showident'].setChecked(v)
            self._info['topleft'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoIdentityVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoIdentityVisibilityOn(self, signal=True):
        self.setInfoVisibility(True, signal)

    def setInfoIdentityVisibilityOff(self, signal=True):
        self.setInfoVisibility(False, signal)

    def getInfoIdentityVisibility(self):
        return self._action['showident'].isChecked()

    def setInfoVolumeVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showimg'].setChecked(v)
            self._info['topright'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoVolumeVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoVolumeVisibilityOn(self, signal=True):
        self.setInfoVisibility(True, signal)

    def setInfoVolumeVisibilityOff(self, signal=True):
        self.setInfoVisibility(False, signal)

    def getInfoVolumeVisibility(self):
        return self._action['showimg'].isChecked()

    def setInfoAcquisitionVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showacq'].setChecked(v)
            self._info['bottomleft'].SetVisibility(v and self._action['showinfo'].isChecked())
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setInfoAcquisitionVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoAcquisitionVisibilityOn(self, signal=True):
        self.setInfoVisibility(True, signal)

    def setInfoAcquisitionVisibilityOff(self, signal=True):
        self.setInfoVisibility(False, signal)

    def getInfoAcquisitionVisibility(self):
        return self._action['showacq'].isChecked()

    def setColorbarVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._colorbar.SetVisibility(v)
            self._action['showcolorbar'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setColorbarVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))
        
    def setColorbarVisibilityOn(self, signal=True):
        self.setColorbarVisibility(True, signal)
        
    def setColorbarVisibilityOff(self, signal=True):
        self.setColorbarVisibility(False, signal)

    def getColorbarVisibility(self):
        return self._action['showcolorbar'].isChecked()

    def getColorbar(self):
        return self._colorbar

    def setColorbarPosition(self, pos='Left', signal=True):
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

    def setColorbarPositionToLeft(self, signal=True):
        self.setColorbarPosition('left', signal)

    def setColorbarPositionToRight(self, signal=True):
        self.setColorbarPosition('right', signal)

    def setColorbarPositionToTop(self, signal=True):
        self.setColorbarPosition('top', signal)

    def setColorbarPositionToBottom(self, signal=True):
        self.setColorbarPosition('bottom', signal)

    def getColorbarPosition(self):
        if self._action['leftcolorbar'].isChecked(): return 'Left'
        elif self._action['rightcolorbar'].isChecked(): return 'Right'
        elif self._action['topcolorbar'].isChecked(): return 'Top'
        else: return 'Bottom'

    # < Revision 03/12/2024
    # add hasHorizontalColorbar method
    def hasHorizontalColorbar(self):
        return self._action['leftcolorbar'].isChecked() or \
            self._action['rightcolorbar'].isChecked()
    # Revision 03/12/2024 >

    # < Revision 03/12/2024
    # add hasVerticalColorbar method
    def hasVerticalColorbar(self):
        return self._action['topcolorbar'].isChecked() or \
            self._action['bottomcolorbar'].isChecked()
    # Revision 03/12/2024 >

    def setTooltipVisibility(self, v, signal=True):
        if isinstance(v, bool):
            if v is True: self.setToolTip(self._tooltipstr)
            else: self.setToolTip('')
            self._action['showtooltip'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setTooltipVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTooltipVisibilityOn(self, signal=True):
        self.setTooltipVisibility(True, signal)

    def setTooltipVisibilityOff(self, signal=True):
        self.setTooltipVisibility(False, signal)

    def getTooltipVisibility(self):
        return self._action['showtooltip'].isChecked()

    def setRulerVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._ruler.SetVisibility(v)
            self._action['showruler'].setChecked(v)
            self._renderwindow.Render()
            self.setRulerPosition(self.getRulerPosition(), False)
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setRulerVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRulerVisibilityOn(self, signal=True):
        self.setRulerVisibility(True, signal)

    def setRulerVisibilityOff(self, signal=True):
        self.setRulerVisibility(False, signal)

    def getRulerVisibility(self):
        return self._action['showruler'].isChecked()

    def getRuler(self):
        return self._ruler

    def setRulerPosition(self, pos='Left', signal=True):
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

    def setRulerPositionToLeft(self, signal=True):
        self.setRulerPosition('left', signal)

    def setRulerPositionToRight(self, signal=True):
        self.setRulerPosition('right', signal)

    def setRulerPositionToTop(self, signal=True):
        self.setRulerPosition('top', signal)

    def setRulerPositionToBottom(self, signal=True):
        self.setRulerPosition('bottom', signal)

    def getRulerPosition(self):
        if self._action['leftruler'].isChecked(): return 'Left'
        elif self._action['rightruler'].isChecked(): return 'Right'
        elif self._action['topruler'].isChecked(): return 'Top'
        else: return 'Bottom'

    def getOrientationMarker(self):
        if self._action['shapecube'].isChecked(): return 'Cube'
        elif self._action['shapehead'].isChecked(): return 'Head'
        elif self._action['shapebust'].isChecked(): return 'Bust'
        elif self._action['shapebody'].isChecked(): return 'Body'
        else: return 'Axes'

    def setOrientationMarker(self, markertype, signal=True):
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

    def setOrientationMarkerToBody(self, signal=True):
        self.setOrientationMarker('body', signal)

    def setOrientationMarkerToHead(self, signal=True):
        self.setOrientationMarker('head', signal)

    def setOrientationMarkerToBust(self, signal=True):
        self.setOrientationMarker('bust', signal)

    def setOrientationMarkerToBrain(self, signal=True):
        self.setOrientationMarker('brain', signal)

    def setOrientationMarkerToCube(self, signal=True):
        self.setOrientationMarker('cube', signal)

    def setOrientationMarkerToAxes(self, signal=True):
        self.setOrientationMarker('axes', signal)

    def setOrientationMakerVisibility(self, v, signal=True):
        if isinstance(v, bool) and self._orientmarker is not None:
            self._orientmarker.SetEnabled(v)
            self._action['showmarker'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setOrientationMakerVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setOrientationMarkerVisibilityOn(self, signal=True):
        self.setOrientationMakerVisibility(True, signal)

    def setOrientationMarkerVisibilityOff(self, signal=True):
        self.setOrientationMakerVisibility(False, signal)

    def getOrientationMarkerVisibility(self):
        return self._action['showmarker'].isChecked()

    def setCentralCrossVisibility(self, v):
        if isinstance(v, bool) and self._cross is not None:
            self._cross.SetVisibility(v)
        else: raise TypeError('parameter functype is not bool or int.')

    def setCentralCrossVisibilityOn(self):
        self.setCentralCrossVisibility(True)

    def setCentralCrossVisibilityOff(self):
        self.setCentralCrossVisibility(False)

    def getCentralCrossVisibility(self):
        return self._cross.GetVisibility() > 0

    def setCentralCrossOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._cross.GetProperty().SetOpacity(v)
            else: raise ValueError('parameter value is not between 0.0 and 1.0.')
        else: raise TypeError('parameter functype is not float.')

    def getCentralCrossOpacity(self):
        return self._cross.GetProperty().GetOpacity()

    def setCursorVisibility(self, v, signal=True):
        if isinstance(v, bool):
            if self._cursor is not None: self._cursor.SetVisibility(v)
            self._action['showcursor'].setChecked(v)
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setCursorVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCursorVisibilityOn(self, signal=True):
        self.setCursorVisibility(True, signal)

    def setCursorVisibilityOff(self, signal=True):
        self.setCursorVisibility(False, signal)

    def getCursorVisibility(self):
        return self._action['showcursor'].isChecked()

    # < Revision 19/12/2024
    # add setCursorOpacity method
    def setCursorOpacity(self, v: float, signal=True):
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
    def getCursorOpacity(self):
        # < Revision 07/01/2025
        # return self._cross.GetProperty().GetOpacity()
        return self._cursor.GetProperty().GetOpacity()
        # Revision 07/01/2025 >
    # Revision 19/12/2024 >

    # < Revision 17/03/2025
    # add getFontFamily method
    def getFontFamily(self):
        return self._ffamily
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontFamily method
    def setFontFamily(self, s, signal=True):
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
    def getFontSize(self):
        return self._fsize
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontSize method
    def setFontSize(self, s, signal=True):
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
    def setFontScale(self, s, signal=True):
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
    def getFontScale(self):
        return self._fscale
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add setFontSizeScale method
    def setFontSizeScale(self, s: tuple[int, float], signal=True):
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
    def setFontProperties(self, s: tuple[str, int, float], signal=True):
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

    def setLineOpacity(self, v, signal=True):
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

    def getLineOpacity(self):
        return self._lalpha

    def setLineWidth(self, v, signal=True):
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

    def getLineWidth(self):
        return self._lwidth

    def setLineColor(self, c, signal=True):
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

    def setLineSelectedColor(self, c, signal=True):
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

    def getLineColor(self):
        return self._lcolor

    def getLineSelectedColor(self):
        return self._slcolor

    def setCursorWorldPosition(self, x, y, z, signal=True):
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

    def getCursorWorldPosition(self):
        return self._cursor.GetPosition()

    # < Revision 12/12/2024
    # add getCursorArrayPosition method
    def getCursorArrayPosition(self):
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

    def setCursorEnabled(self):
        self._cursorenabled = True

    def setCursorDisabled(self):
        self._cursorenabled = False

    def isCursorEnabled(self):
        return self._cursorenabled is True

    def setRoundedCursorCoordinatesEnabled(self):
        self._roundedenabled = True

    def setRoundedCursorCoordinatesDisabled(self):
        self._roundedenabled = False

    def isRoundedCursorCoordinatesEnabled(self):
        return self._roundedenabled is True

    def setAxisConstraintToCursor(self, v, signal=True):
        if isinstance(v, int):
            if 0 <= v < 5:
                self._axisconstraint = v
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ViewMethodCalled.emit(self, 'setAxisConstraintToCursor', v)
            else: raise ValueError('parameter value {} is out of range (0 to 3).'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setNoAxisConstraintToCursor(self, signal=True):
        self.setAxisConstraintToCursor(0, signal)

    def setXAxisConstraintToCursor(self, signal=True):
        self.setAxisConstraintToCursor(1, signal)

    def setYAxisConstraintToCursor(self, signal=True):
        self.setAxisConstraintToCursor(2, signal)

    def setZAxisConstraintToCursor(self, signal=True):
        self.setAxisConstraintToCursor(3, signal)

    def setMouseCursor(self, shape, signal=True):
        if isinstance(shape, int):
            self._renderwindow.SetCurrentCursor(shape)
            if signal:
                # noinspection PyUnresolvedReferences
                self.ViewMethodCalled.emit(self, 'setMouseCursor', shape)
        else: raise TypeError('parameter type {} is not int'.format(type(shape)))

    def setDefaultMouseCursor(self, signal=True):
        self.setMouseCursor(VTK_CURSOR_DEFAULT, signal)

    def setArrowMouseCursor(self, signal=True):
        self.setMouseCursor(VTK_CURSOR_ARROW, signal)

    def setHandMouseCursor(self, signal=True):
        self.setMouseCursor(VTK_CURSOR_HAND, signal)

    def setCrossHairMouseCursor(self, signal=True):
        self.setMouseCursor(VTK_CURSOR_CROSSHAIR, signal)

    def setSizeAllMouseCursor(self, signal=True):
        self.setMouseCursor(VTK_CURSOR_SIZEALL, signal)

    def getMouseCursor(self):
        return self._renderwindow.GetCurrentCursor()

    def hideAll(self, signal=True):
        self.setCursorVisibilityOff(signal)
        self.setInfoVisibilityOff(signal)
        self.setColorbarVisibilityOff(signal)
        self.setRulerVisibilityOff(signal)
        self.setOrientationLabelsVisibilityOff(signal)
        self.setOrientationMarkerVisibilityOff(signal)
        self.setTooltipVisibilityOff(signal)

    def showAll(self, signal=True):
        self.setCursorVisibilityOn(signal)
        self.setInfoVisibilityOn(signal)
        self.setColorbarVisibilityOn(signal)
        self.setRulerVisibilityOn(signal)
        self.setOrientationLabelsVisibilityOn(signal)
        self.setOrientationMarkerVisibilityOn(signal)
        self.setTooltipVisibilityOn(signal)

    def getTopLeftInfo(self):
        return self._info['topleft']

    def getTopRightInfo(self):
        return self._info['topright']

    def getBottomLeftInfo(self):
        return self._info['bottomleft']

    def getBottomRightInfo(self):
        return self._info['bottomright']

    def getPixmapCapture(self):
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

    def saveCapture(self):
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

    def copyToClipboard(self):
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

    def zoomIn(self):
        if self._renderer.GetActiveCamera().GetParallelScale() > 1:
            self._renderer.GetActiveCamera().Zoom(1.1)
            self._updateRuler()
            self._renderwindow.Render()
            # noinspection PyUnresolvedReferences
            self.ZoomChanged.emit(self, self._renderer.GetActiveCamera().GetParallelScale())

    def zoomOut(self):
        if self._renderer.GetActiveCamera().GetParallelScale() < 1000:
            self._renderer.GetActiveCamera().Zoom(0.9)
            self._updateRuler()
            self._renderwindow.Render()
            # noinspection PyUnresolvedReferences
            self.ZoomChanged.emit(self, self._renderer.GetActiveCamera().GetParallelScale())

    def zoomDefault(self):
        self._renderer.GetActiveCamera().SetParallelScale(self._DEFAULTZOOM)
        self._updateRuler()
        self._renderwindow.Render()
        # noinspection PyUnresolvedReferences
        self.ZoomChanged.emit(self, self._DEFAULTZOOM)

    def setZoom(self, z, signal=True):
        if isinstance(z, float):
            self._renderer.GetActiveCamera().SetParallelScale(z)
            self._updateRuler()
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.ZoomChanged.emit(self, z)
        else: raise TypeError('parameter type {} is not float.'.format(type(z)))

    def getZoom(self):
        return self._renderer.GetActiveCamera().GetParallelScale()

    def updateRender(self):
        self._renderwindow.Render()

    # Public tools methods

    def getToolCollection(self):
        return self._tools

    # 2D Tools methods

    def setAcceptTools(self, v):
        if isinstance(v, bool):
            self._accepttools = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setAcceptToolsOn(self):
        self.setAcceptTools(True)

    def setAcceptToolsOff(self):
        self.setAcceptTools(False)

    def getAcceptTools(self):
        return self._accepttools

    def addDistanceTool(self, name=''):
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

    def addOrthogonalDistanceTool(self, name=''):
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

    def addAngleTool(self, name=''):
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

    def addBoxTool(self, p=None, name=''):
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

    def addTextTool(self, p=None):
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

    def removeAll2DTools(self, signal=True):
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

    def addTarget(self, p=None, name='', signal=True):
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

    def addTrajectory(self, p1=None, p2=None, angles=None, length: float = 50.0, name='', signal=True):
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

    def hasTools(self):
        return len(self._tools) > 0

    def getToolCount(self):
        return len(self._tools)

    def getTool(self, key):
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): return self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        if isinstance(key, str):
            if key in self._tools: return self._tools[key]
            else: raise ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        else: raise TypeError('parameter type {} is not int, str, HandleWidget or LineWidget.'.format(type(key)))

    def moveTool(self, key, target, entry=None, angles=None, length=None, signal=True):
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

    def renameTool(self, key, name, signal=True):
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

    def copyToolAttributes(self, key, tool, signal=True):
        if isinstance(key, int):
            if 0 <= key < self._tools.count(): key = self._tools[key]
            else: ValueError('tool index {} is out of range.'.format(key))
        elif isinstance(key, str):
            if key in self._tools: key = self._tools[key]
            else: ValueError('tool name {} not in SisypheToolCollection.'.format(key))
        if isinstance(key, (HandleWidget, LineWidget)):
            if key.getName() in self._tools:
                if tool is not None and isinstance(tool, (HandleWidget, LineWidget)): tool.copyAttributesFrom(key)
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.ToolAttributesChanged.emit(self, key)
            else: raise ValueError('tool {} is not in SisypheToolCollection.'.format(key.getName()))
        else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(key)))

    def removeTool(self, key, signal=True):
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

    def removeAllTools(self, signal=True):
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

    def setToolInteractive(self, key, v, signal=True):
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

    def setToolInteractiveOn(self, key, signal=True):
        self.setToolInteractive(key, True, signal)

    def setToolInteractiveOff(self, key, signal=True):
        self.setToolInteractive(key, False, signal)

    def lockTool(self, key, signal=True):
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

    def unlockTool(self, key, signal=True):
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

    def isToolLocked(self, key):
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

    def _onBoxInteractionEvent(self, widget, event):
        pass

    def _onBoxStartInteractionEvent(self, widget, event):
        pass

    def _onBoxEndInteractionEvent(self, widget, event):  # to do
        pass

    def _onTargetInteractionEvent(self, widget, event):
        pass

    def _onTargetStartInteractionEvent(self, widget, event):
        pass

    # noinspection PyUnusedLocal
    def _onTargetEndInteractionEvent(self, widget, event):
        p = widget.getPosition()
        self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)
        # noinspection PyUnresolvedReferences
        self.ToolMoved.emit(self, widget)

    def _onTrajectoryInteractionEvent(self, widget, event):
        pass

    def _onTrajectoryStartInteractionEvent(self, widget, event):
        pass

    def _onTrajectoryEndInteractionEvent(self, widget, event):
        p = widget.getPosition2()  # Target point position
        self.setCursorWorldPosition(p[0], p[1], p[2], signal=True)
        # noinspection PyUnresolvedReferences
        self.ToolMoved.emit(self, widget)

    # Abstract private method

    def _initCursor(self):
        pass

    # Private VTK event method

    def _onRightPressEvent(self, obj, evt_name):
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

    def _onLeftPressEvent(self, obj, evt_name):
        if self.isSelectable():
            if not self.isSelected(): self.select()

    # Abstract private VTK event methods

    def _onWheelForwardEvent(self, obj, evt_name):
        pass

    def _onWheelBackwardEvent(self, obj, evt_name):
        pass

    def _onLeftReleaseEvent(self, obj, evt_name):
        pass

    def _onMiddlePressEvent(self, obj, evt_name):
        pass

    def _onMouseMoveEvent(self, obj, evt_name):
        pass

    def _onKeyPressEvent(self, obj, evt_name):
        pass

    def _onKeyReleaseEvent(self, obj, evt_name):
        pass
