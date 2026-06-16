"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
    - skimage, Image processing, https://scikit-image.org/
    - vtk, Visualization, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sys import platform

from os import mkdir
from os import chdir
from os import getcwd

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext

from math import atan2
from math import degrees

from numpy import flip
from numpy import stack

from skimage.util import montage
from skimage.io import imsave

from vtk import vtkCursor3D
from vtk import vtkPolyDataMapper
from vtk import vtkProp
from vtk import vtkActor
from vtk import vtkVolume
from vtk import vtkSphereSource
from vtk import vtkImageSlice
from vtk import vtkImageSliceMapper
from vtk import vtkVolumeProperty
from vtk import vtkSmartVolumeMapper
from vtk import vtkBMPWriter
from vtk import vtkJPEGWriter
from vtk import vtkPNGWriter
from vtk import vtkTIFFWriter
from vtk import vtkWindowToImageFilter
from vtk import VTK_CURSOR_HAND
from vtk import VTK_CURSOR_ARROW
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QFileDialog

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheLUT import SisypheColorTransfer
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheMesh import SisypheMeshCollection
from Sisyphe.core.sisypheTracts import SisypheTractCollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.gui.dialogMeshProperties import DialogMeshProperties
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from vtk import vtkObject

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> AbstractViewWidget -> VolumeViewWidget
    
Description
~~~~~~~~~~~

Class for displaying 3D rendering of SisypheVolume instances.
Supports texture, mesh, and three orthogonal slices.
Interactive management of target and trajectory widgets.
"""


class VolumeViewWidget(AbstractViewWidget):
    """
    Specialized subclass of the AbstractViewWidget class that provides a comprehensive 3D visualization component
    designed for the interactive rendering of a SisypheVolume instance.

    The main features are as follows:

    - Multi-modal visualization:

        - Volume rendering: a texture-based 3D rendering of the SisypheVolume, with support for multiple blend modes such as composite, minimum intensity projection (MIP), and isosurface.
        - Orthogonal slices: three vtkImageSlice actors representing the axial, coronal, and sagittal planes. The position of each slice is interactively linked to the 3D cursor.
        - Mesh and tractography overlays: displays SisypheMeshCollection (3D models) and SisypheTractCollection (streamlines) within the same scene.

    - Interactive navigation and tools:

        - Full 3D camera control: mouse-driven rotation, panning, and zooming. Predefined camera positions (top, bottom, front, back, left, right) allow standardized views.
        - 3D cursor: A cross-shaped cursor, with an optional spherical marker, indicates the current 3D focal point. Its position can be set interactively and drives the location of the orthogonal slices.
        - Streamline navigation: allows user to select a streamline and move through its points using the mouse wheel, updating the cursor position accordingly.

    - Rendering control:

        - Transfer function management: manages SisypheColorTransfer instances to control the color and opacity mapping of the volume rendering. Functions can be loaded from and saved to files.
        - Interactive cropping: provides tools to dynamically crop the volume rendering, enabling focused inspection of specific regions.
        - Outer surface generation: can compute and display an outer surface mesh of the SisypheVolume.

    - Data and scene Export:

        - Image capture: captures the current viewport to bitmap image formats.
        - Series capture: generate and save a series of captures from multiple standard camera angles, either as individual files or as a single montage image.

    - Context-Sensitive Interaction: right-click context popup menus provide quick access to settings specific to the picked object, such as volume rendering properties, mesh appearance, or tool options.

    Description
    ~~~~~~~~~~~

    Class for displaying volume rendering.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AbstractViewWidget -> VolumeViewWidget

    Last revision: 08/06/2026
    """

    _CODETOBLEND: dict[int, str] = {0: 'composite', 1: 'MaximumIntensity', 2: 'MinimumIntensity',
                                    3: 'AverageIntensity', 4: 'Additive', 5: 'IsoSurface'}

    _BLENDTOCODE: dict[str, int] = {'composite': 0, 'MaximumIntensity': 1, 'MinimumIntensity': 2,
                                    'AverageIntensity': 3, 'Additive': 4, 'IsoSurface': 5}

    # Custom Qt signals

    CameraChanged: pyqtSignal = pyqtSignal(QWidget)
    MeshOnSliceVisibilityChanged: pyqtSignal = pyqtSignal(QWidget, bool)

    # Public class methods

    @classmethod
    def getBlendAsString(cls, k: int) -> str:
        """
        Convert a blend mode integer code to its string representation.

        Parameters
        ----------
        k : int
            integer code for the blend mode.

        Returns
        -------
        str
            string representation of the blend mode.
        """
        if isinstance(k, int): return cls._CODETOBLEND[k]
        else: raise TypeError('parameter type {} is not int.'.format(type(k)))

    @classmethod
    def getBlendFromString(cls, k: str) -> int:
        """
        Convert a blend mode string representation to its integer code.

        Parameters
        ----------
        k : str
            string representation of the blend mode.

        Returns
        -------
        int
            integer code for the blend mode.
        """
        if isinstance(k, str): return cls._BLENDTOCODE[k]
        else: raise TypeError('parameter type {} is not str.'.format(type(k)))

            # Private methods

    # Special method

    def __init__(self, parent: QWidget | None = None):
        """
        VolumeViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None, optional
            Parent widget (default is None).
        """

        self._sph = None            # vtkSphereSource, sphere centered on cursor
        self._cursorsph = None      # vtkActor, sphere actor centered on cursor

        super().__init__(parent)

        self._slice0 = None         # vtkImageSlice, axial
        self._slice1 = None         # vtkImageSlice, coronal
        self._slice2 = None         # vtkImageSlice, sagittal
        self._texture = None        # vtkVolume, volume rendering

        self._mesh = SisypheMeshCollection()
        self._tract = SisypheTractCollection()
        self._tract.setRenderer(self.getRenderer())
        self._transfer = SisypheColorTransfer()
        self._croptag = 0x361B

        self._scale0 = None                     # scale before event start
        self._mousepos0 = None                  # mouse position before event start
        self._campos0 = None                    # camera position before event start
        self._camfocal0 = None                  # camera focal point before event start
        self._selectedSlice = 0                 # number of the selected slice
        self._slprop: vtkProp | None = None     # selected streamline
        self._slid: int = 0                     # current point of the selected streamline

        # Init popup menu

        self._action['top'] = QAction('Top', self)
        self._action['bottom'] = QAction('Bottom', self)
        self._action['left'] = QAction('Left', self)
        self._action['right'] = QAction('Right', self)
        self._action['front'] = QAction('Front', self)
        self._action['back'] = QAction('Back', self)
        self._action['top'].triggered.connect(self.setCameraToTop)
        self._action['bottom'].triggered.connect(self.setCameraToBottom)
        self._action['left'].triggered.connect(self.setCameraToLeft)
        self._action['right'].triggered.connect(self.setCameraToRight)
        self._action['front'].triggered.connect(self.setCameraToFront)
        self._action['back'].triggered.connect(self.setCameraToBack)
        self._action['showmesh'] = QAction('Show mesh(es) on slices', self)
        self._action['showslice0'] = QAction('Show 3D axial slice', self)
        self._action['showslice1'] = QAction('Show 3D coronal slice', self)
        self._action['showslice2'] = QAction('Show 3D sagittal slice', self)
        self._action['showslices'] = QAction('Show all 3D slices', self)
        self._action['hideslices'] = QAction('Hide all 3D slices', self)
        self._action['showtexture'] = QAction('Show texture volume rendering', self)
        # self._action['showsurface'] = QAction('Show outer mesh isosurface', self)
        self._group_orient = QActionGroup(self)
        self._group_orient.setExclusive(True)
        self._group_orient.addAction(self._action['top'])
        self._group_orient.addAction(self._action['bottom'])
        self._group_orient.addAction(self._action['left'])
        self._group_orient.addAction(self._action['right'])
        self._group_orient.addAction(self._action['front'])
        self._group_orient.addAction(self._action['back'])
        self._action['left'].setChecked(True)
        self._action['showmesh'].setCheckable(True)
        self._action['showslice0'].setCheckable(True)
        self._action['showslice1'].setCheckable(True)
        self._action['showslice2'].setCheckable(True)
        self._action['showtexture'].setCheckable(True)
        # self._action['showsurface'].setCheckable(True)
        self._action['showmesh'].setChecked(False)
        self._action['showslice0'].setChecked(True)
        self._action['showslice1'].setChecked(True)
        self._action['showslice2'].setChecked(True)
        self._action['showtexture'].setChecked(False)
        # self._action['showsurface'].setChecked(False)
        self._action['showmesh'].triggered.connect(
            lambda: self.setMeshOnSliceVisibility(self._action['showmesh'].isChecked()))
        self._action['showslice0'].triggered.connect(
            lambda: self.setSlice0Visibility(self._action['showslice0'].isChecked()))
        self._action['showslice1'].triggered.connect(
            lambda: self.setSlice1Visibility(self._action['showslice1'].isChecked()))
        self._action['showslice2'].triggered.connect(
            lambda: self.setSlice2Visibility(self._action['showslice2'].isChecked()))
        self._action['showtexture'].triggered.connect(
            lambda: self.setTextureVisibility(self._action['showtexture'].isChecked()))
        # self._action['showsurface'].triggered.connect(
        #     lambda: self.setSurfaceVisibility(self._action['showsurface'].isChecked()))
        self._action['showslices'].triggered.connect(self.showAllSlices)
        self._action['hideslices'].triggered.connect(self.hideAllSlices)
        self._menuPosition = QMenu('Position', self._popup)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._menuPosition.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._menuPosition.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._menuPosition.setAttribute(Qt.WA_TranslucentBackground, True)
        self._menuPosition.addAction(self._action['top'])
        self._menuPosition.addAction(self._action['bottom'])
        self._menuPosition.addAction(self._action['left'])
        self._menuPosition.addAction(self._action['right'])
        self._menuPosition.addAction(self._action['front'])
        self._menuPosition.addAction(self._action['back'])
        self._popup.insertMenu(self._popup.actions()[2], self._menuPosition)
        self._menuVisibility.insertSeparator(self._action['hideall'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showmesh'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice0'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice1'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice2'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslices'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showtexture'])
        # self._menuVisibility.insertAction(self._action['hideall'], self._action['showsurface'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['hideslices'])

        self._action['orthodistance'].setVisible(False)
        self._action['box'].setVisible(False)
        self._action['text'].setVisible(False)
        self._action['target'].setVisible(False)
        self._action['trajectory'].setVisible(False)
        self._action['edittext'].setVisible(False)
        self._action['textprop'].setVisible(False)
        self._action['followflag'].setVisible(False)
        self._action['showmesh'].setVisible(False)
        # self._action['showorientation'].setVisible(False)

        self._action['captureseries'] = QAction('Save captures from multiple camera positions...', self)
        self._action['captureseries2'] = QAction('Save single capture from multiple camera positions...', self)
        self._action['captureseries'].triggered.connect(lambda dummy: self.saveSeriesCaptures())
        self._action['captureseries2'].triggered.connect(lambda dummy: self.saveSeriesCapture())
        self._popup.addAction(self._action['captureseries'])
        self._popup.addAction(self._action['captureseries2'])

        # Init texture popup menu

        self._texturepopup = QMenu()
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._texturepopup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._texturepopup.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._texturepopup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['crop'] = QAction('Crop picked region', self)
        self._action['uncrop'] = QAction('Uncrop volume rendering', self)
        self._action['loadtransfer'] = QAction('Load transfer function', self)
        self._action['savetransfer'] = QAction('Save transfer function', self)
        self._action['composite'] = QAction('Composite', self)
        self._action['maxintensity'] = QAction('Maximum intensity', self)
        self._action['minintensity'] = QAction('Minimum Intensity', self)
        self._action['averageintensity'] = QAction('Average Intensity', self)
        self._action['additive'] = QAction('Additive', self)
        self._action['isosurface'] = QAction('Isosurface', self)
        self._action['composite'].setCheckable(True)
        self._action['maxintensity'].setCheckable(True)
        self._action['minintensity'].setCheckable(True)
        self._action['averageintensity'].setCheckable(True)
        self._action['additive'].setCheckable(True)
        self._action['isosurface'].setCheckable(True)
        self._action['composite'].setChecked(True)
        self._action['crop'].triggered.connect(self.cropTexture)
        self._action['uncrop'].triggered.connect(self.uncropTexture)
        self._action['loadtransfer'].triggered.connect(self.loadTransfer)
        self._action['savetransfer'].triggered.connect(self.saveTransfer)
        self._action['composite'].triggered.connect(self.setBlendModeToComposite)
        self._action['maxintensity'].triggered.connect(self.setBlendModeToMaximumIntensity)
        self._action['minintensity'].triggered.connect(self.setBlendModeToMinimumIntensity)
        self._action['averageintensity'].triggered.connect(self.setBlendModeToAverageIntensity)
        self._action['additive'].triggered.connect(self.setBlendModeToAdditive)
        self._action['isosurface'].triggered.connect(self.setBlendModeToIsoSurface)

        self._texturepopup.addAction(self._action['crop'])
        self._texturepopup.addAction(self._action['uncrop'])
        self._group_blend = QActionGroup(self)
        self._group_blend.setExclusive(True)
        self._group_blend.addAction(self._action['composite'])
        self._group_blend.addAction(self._action['maxintensity'])
        self._group_blend.addAction(self._action['minintensity'])
        self._group_blend.addAction(self._action['averageintensity'])
        self._group_blend.addAction(self._action['additive'])
        self._group_blend.addAction(self._action['isosurface'])
        submenu = QMenu('Blend mode', self._texturepopup)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        submenu.addAction(self._action['composite'])
        submenu.addAction(self._action['maxintensity'])
        submenu.addAction(self._action['minintensity'])
        submenu.addAction(self._action['averageintensity'])
        submenu.addAction(self._action['additive'])
        submenu.addAction(self._action['isosurface'])
        self._texturepopup.addMenu(submenu)
        submenu = QMenu('Transfer function', self._texturepopup)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        submenu.addAction(self._action['loadtransfer'])
        submenu.addAction(self._action['savetransfer'])
        self._texturepopup.addMenu(submenu)

        # Init mesh popup menu

        self._meshpopup = QMenu()
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._meshpopup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self._meshpopup.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._meshpopup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['meshprop'] = QAction('Edit properties...', self)
        self._action['meshprop'].triggered.connect(self.editActorProperties)
        self._meshpopup.addAction(self._action['meshprop'])

        # Viewport tooltip

        self._tooltipstr = 'View control:\n' \
                           '\tMouseWheel slices through selected orientation,\n' \
                           '\tUp or Left key to previous slice in selected orientation,\n' \
                           '\tDown or Right key to next slice in selected orientation,\n' \
                           '\tMouseWheel + CTRL key (CMD key MacOS) to change zoom,\n' \
                           '\tUp or Left + CTRL Key (CMD key MacOS) to zoom out,\n' \
                           '\tDown or Right + CTRL key (CMD key MacOS) to zoom in,\n' \
                           '\tLeft-click to select slice,\n' \
                           '\tLeft-click to select a streamline,\n'\
                           '\tand then use mousewheel to move cursor position along the streamline,\n' \
                           '\tLeft-click + CTRL key to move cursor position,\n' \
                           '\tLeft-click and drag to rotate view,\n' \
                           '\tLeft-click + CTRL key (CMD key MacOS) and drag to change zoom,\n' \
                           '\tLeft-click + ALT key and drag to pan,\n' \
                           '\tLeft-click + SHIFT key and drag to change window/level,\n' \
                           '\tRight-click to display popup menu.'
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

        self._renderer.GetLights().GetItemAsObject(0).SetAmbientColor(1.0, 1.0, 1.0)

    """
    Private attributes

    _slice0         vtkImageSlice, axial slice
    _slice1         vtkImageSlice, coronal slice
    _slice2         vtkImageSlice, sagittal slice
    _sph            vtkSphereSource, sphere centered on cursor
    _cursorsph      vtkActor, sphere actor centered on cursor
    _planewidget    vtkImplicitPlaneWidget
    _texture        vtkVolume
    _mesh           SisypheMeshCollection
    _tract          SisypheTractCollection
    _transfer       SisypheColorTransfer
    _croptag        int, crop direction code
    _scale0         float, zoom factor before event start, interactive zoom management
    _mousepos0      (float, float, float), mouse position before event start
    _campos0        (float, float, float), camera position before event start
    _camfocal0      float, focal depth before event start
    _selectedslice  int, number of the selected slice
    _slprop         vtkProp, selected streamline
    _slid           int, current point of the selected streamline
    _action         QAction
    _popup          QMenu, popup menu
    _menuVisibility QMenu, popup submenu for actors visibility (slices, texture, mesh)
    _menuPosition   QMenu, popup submenu for predefined camera position
    _texturepopup   QMenu, popup submenu for texture settings
    _meshpopup      QMenu, popup menu for mesh settings
    """

    # Private methods

    def _addSlice(self, orient: int, alpha: float) -> vtkImageSlice:
        """
        Creates and adds a vtkImageSlice to the renderer for a given orientation.

        Parameters
        ----------
        orient : int
            orientation of the slice (0 for sagittal, 1 for coronal, 2 for axial).
        alpha : float
            opacity of the slice.

        Returns
        -------
        vtkImageSlice
            created vtkImageSlice actor.
        """
        mapper = vtkImageSliceMapper()
        mapper.BorderOn()
        mapper.SetInputData(self._volume.getVTKImage())
        mapper.SetOrientation(orient)
        mapper.SliceFacesCameraOff()
        mapper.SliceAtFocalPointOff()
        slc = vtkImageSlice()
        slc.SetObjectName('slice')
        slc.SetMapper(mapper)
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(self._volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._renderer.AddViewProp(slc)
        return slc

    def _addTexture(self) -> None:
        """
        Creates and adds the texture rendering of the vtkVolume actor to the scene.
        """
        self._texture = vtkVolume()
        mapper = vtkSmartVolumeMapper()
        mapper.SetInputData(self._volume.getVTKImage())
        mapper.SetBlendModeToComposite()
        mapper.CroppingOff()
        prop = vtkVolumeProperty()
        # noinspection PyArgumentList
        prop.ShadeOff()
        self.loadTransfer()
        # noinspection PyArgumentList
        prop.DisableGradientOpacityOff()
        # noinspection PyArgumentList
        prop.SetColor(self._transfer.getColorTransfer())
        # noinspection PyArgumentList
        prop.SetScalarOpacity(self._transfer.getAlphaTransfer())
        # noinspection PyArgumentList
        prop.SetGradientOpacity(self._transfer.getGradientTransfer())
        prop.SetInterpolationTypeToLinear()
        self._texture.SetMapper(mapper)
        self._texture.SetProperty(prop)
        self._renderer.AddViewProp(self._texture)

    def _addOuterSurfaceMesh(self) -> None:
        """
        Generates and adds an outer surface mesh of the SisypheVolume to the scene.
        """
        # < Revision 20/06/2025
        """
        f = StatisticsImageFilter()
        f.Execute(self._volume.getSITKImage())
        threshold = f.GetMean()
        mask = self._volume.getSITKImage() > threshold
        # Fill mask
        f = BinaryFillholeImageFilter()
        # noinspection PyUnresolvedReferences
        for i in range(mask.GetSize()[2]):
            slc = mask[:, :, i]
            slc = f.Execute(slc)
            mask[:, :, i] = slc
        # Convert to float
        mask = Cast(mask, sitkFloat32)
        # Smoothing
        mask *= 100
        mask = SmoothingRecursiveGaussian(mask, [1.0, 1.0, 1.0])
        mask = simpleITKToVTK(mask)
        # Calc polydata
        f = vtkFlyingEdges3D()
        f.SetInputData(mask)
        f.ComputeNormalsOn()
        f.SetValue(0, 50.0)
        # noinspection PyArgumentList
        f.Update()
        """
        # Revision 20/06/2025 >
        # Mesh attributes
        wait = DialogWait()
        wait.open()
        wait.setInformationText('Outer surface mesh processing...')
        mesh = SisypheMesh()
        mesh.createOuterSurface(self._volume)
        mesh.setName('OuterSurface')
        mesh.setScalarColorVisibilityOff()
        mesh.setColor(1.0, 0.0, 0.0)
        mesh.setVisibilityOff()
        mesh.shadingOn()
        mesh.setPhongRendering()
        self._mesh.append(mesh)
        self._renderer.AddViewProp(mesh.getActor())
        wait.close()

    def _initCursor(self) -> None:
        """
        Initializes the 3D cross-shaped cursor and its spherical representation.
        Currently, this method overrides superclass's implementation.
        """
        if self._cursor is None:
            # Cursor
            cursor = vtkCursor3D()
            cursor.AxesOn()
            cursor.OutlineOff()
            cursor.XShadowsOff()
            cursor.YShadowsOff()
            cursor.ZShadowsOff()
            cursor.WrapOff()
            # fx, fy, fz = self._volume.getFieldOfView()
            # fx /= 2
            # fy /= 2
            # fz /= 2
            # cursor.SetModelBounds(-fx, fx, -fy, fy, -fz, fz)
            cursor.SetModelBounds(-500, 500, -500, 500, -500, 500)
            cursor.Update()
            mapper = vtkPolyDataMapper()
            # noinspection PyArgumentList
            mapper.SetInputConnection(cursor.GetOutputPort())
            self._cursor = vtkActor()
            self._cursor.SetMapper(mapper)
            self._cursor.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
            self._cursor.SetVisibility(False)
            self._renderer.AddActor(self._cursor)
            # Sphere centered on cursor
            self._sph = vtkSphereSource()
            self._sph.SetRadius(0.0)
            self._sph.SetCenter(0.0, 0.0, 0.0)
            self._sph.SetThetaResolution(30)
            self._sph.SetPhiResolution(30)
            # noinspection PyArgumentList
            self._sph.Update()
            mapper = vtkPolyDataMapper()
            # noinspection PyArgumentList
            mapper.SetInputConnection(self._sph.GetOutputPort())
            self._cursorsph = vtkActor()
            self._cursorsph.SetMapper(mapper)
            self._cursorsph.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
            self._cursorsph.SetVisibility(False)
            self._cursorsph.GetProperty().SetOpacity(0.5)
            self._renderer.AddActor(self._cursorsph)

    def _getPickedSlice(self) -> vtkImageSlice | None:
        """
        Picks the vtkImageSlice at the current mouse position.

        Returns
        -------
        vtkImageSlice | None
            picked vtkImageSlice actor, or None if no slice was picked.
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() != 'vtkImageSlice': prop = None
            return prop
        else: return None

    def _getPickedActor(self) -> vtkActor | None:
        """
        Picks the vtkActor at the current mouse position.

        Returns
        -------
        vtkActor | None
            picked vtkActor, or None if no actor was picked.
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() != 'vtkOpenGLActor': prop = None
            return prop
        else: return None

    def _getPickedTool(self) -> vtkProp | None:
        """
        Picks a tool representation (e.g., distance or angle widget) at the current mouse position.

        Returns
        -------
        vtkProp | None
            picked tool's vtkProp, or None if no tool was picked.
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() not in ('vtkDistanceRepresentation3D',
                                           'vtkAngleRepresentation3D'): prop = None
            return prop
        else: return None

    def _updateTextureTransfer(self) -> None:
        """
        Updates the volume rendering's transfer functions from the internal SisypheColorTransfer instance.
        """
        prop = self._texture.GetProperty()
        prop.SetColor(self._transfer.getColorTransfer())
        prop.SetScalarOpacity(self._transfer.getAlphaTransfer())
        prop.SetGradientOpacity(self._transfer.getGradientTransfer())
        self.updateRender()

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed in the widget.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            Sisyphevolume to display.
        """
        if isinstance(volume, SisypheVolume):
            if self.hasVolume(): self.removeVolume()
            super().setVolume(volume)
            self._slice0 = self._addSlice(2, 1.0)  # axial
            self._slice1 = self._addSlice(1, 1.0)  # coronal
            self._slice2 = self._addSlice(0, 1.0)  # sagittal
            self._addTexture()
            # < Revision 18/10/2024
            self.setSlice0Visibility(self._action['showslice0'].isChecked())
            self.setSlice1Visibility(self._action['showslice1'].isChecked())
            self.setSlice2Visibility(self._action['showslice2'].isChecked())
            self.setTextureVisibility(self._action['showtexture'].isChecked())
            if self._action['composite'].isChecked(): self.setBlendModeToComposite()
            elif self._action['maxintensity'].isChecked(): self.setBlendModeToMaximumIntensity()
            elif self._action['minintensity'].isChecked(): self.setBlendModeToMinimumIntensity()
            elif self._action['averageintensity'].isChecked(): self.setBlendModeToAverageIntensity()
            elif self._action['additive'].isChecked(): self.setBlendModeToAdditive()
            elif self._action['isosurface'].isChecked(): self.setBlendModeToIsoSurface()
            self._updateTextureTransfer()
            # Revision 18/10/2024 >
            # < Revision 24/07/2025
            # _initCursor() already called by abstractViewWidget.__init__() ancestor
            # self._initCursor()
            # x, y, z = self._slice0.GetCenter()
            x, y, z = volume.getCenter()
            # Revision 24/07/2025 >
            self.setCursorWorldPosition(x, y, z, False)
            self._renderer.GetActiveCamera().SetFocalPoint(x, y, z)
            self.setCameraToLeft()
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(volume)))

    # < Revision 18/10/2024
    # add replaceVolume method
    # noinspection PyUnusedLocal
    def replaceVolume(self, volume: SisypheVolume) -> None:
        """
        Replace the current displayed SisypheVolume with a new one.

        Parameters
        ----------
        volume : SisypheVolume
            new SisypheVolume to display.
        """
        if self.hasVolume():
            self._renderer.RemoveViewProp(self._slice0)
            self._renderer.RemoveViewProp(self._slice1)
            self._renderer.RemoveViewProp(self._slice2)
            self._renderer.RemoveViewProp(self._texture)
            self._slice0 = self._addSlice(2, 1.0)  # axial
            self._slice1 = self._addSlice(1, 1.0)  # coronal
            self._slice2 = self._addSlice(0, 1.0)  # sagittal
            self._addTexture()
            # Restore display properties
            self.setSlice0Visibility(self._action['showslice0'].isChecked())
            self.setSlice1Visibility(self._action['showslice1'].isChecked())
            self.setSlice2Visibility(self._action['showslice2'].isChecked())
            self.setTextureVisibility(self._action['showtexture'].isChecked())
            if self._action['composite'].isChecked(): self.setBlendModeToComposite()
            elif self._action['maxintensity'].isChecked(): self.setBlendModeToMaximumIntensity()
            elif self._action['minintensity'].isChecked(): self.setBlendModeToMinimumIntensity()
            elif self._action['averageintensity'].isChecked(): self.setBlendModeToAverageIntensity()
            elif self._action['additive'].isChecked(): self.setBlendModeToAdditive()
            elif self._action['isosurface'].isChecked(): self.setBlendModeToIsoSurface()
            # < Revision 08/06/2026
            self._initInfoLabels()
            if self._action['showinfo'].isChecked():
                self._info['topleft'].SetVisibility(True)
                self._info['topright'].SetVisibility(True)
                self._info['bottomleft'].SetVisibility(True)
                self._info['bottomright'].SetVisibility(True)
            # Revision 08/06/2026 >
            self._updateTextureTransfer()
            self._renderwindow.Render()
    # Revision 18/10/2024 >

    def removeVolume(self) -> None:
        """
        Remove the currently displayed SisypheVolume from the widget.
        Currently, this method calls the superclass's implementation.
        """
        if self.hasVolume():
            self._renderer.RemoveViewProp(self._slice0)
            self._renderer.RemoveViewProp(self._slice1)
            self._renderer.RemoveViewProp(self._slice2)
            self._renderer.RemoveViewProp(self._texture)
            for mesh in self._mesh:
                self._renderer.RemoveViewProp(mesh.getActor())
            del self._slice0
            del self._slice1
            del self._slice2
            del self._texture
            self._slice0 = None
            self._slice1 = None
            self._slice2 = None
            self._texture = None
            self._mesh.clear()
            self._transfer.clear()
        super().removeVolume()

    def getPopupCameraPosition(self) -> QMenu:
        """
        Get the 'Position' submenu from the popup menu.

        Returns
        -------
        QMenu
            'Position' submenu.
        """
        return self._menuPosition

    def getPopupTextureActor(self) -> QMenu:
        """
        Get the popup menu for texture (volume rendering) settings.

        Returns
        -------
        QMenu
            texture settings popup menu.
        """
        return self._texturepopup

    def setCameraToTop(self) -> None:
        """
        Set the camera to a top-down view.
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 1, 0)
        camera.SetPosition(f[0], f[1], 500)
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraToBottom(self) -> None:
        """
        Set the camera to a bottom-up view.
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 1, 0)
        camera.SetPosition(f[0], f[1], -500)
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraToLeft(self) -> None:
        """
        Set the camera to a view from the left.
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(-500, f[1], f[2])
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraToRight(self) -> None:
        """
        Set the camera to a view from the right.
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(500, f[1], f[2])
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraToFront(self) -> None:
        """
        Set the camera to a view from the front (anterior).
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(f[0], 500, f[2])
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraToBack(self) -> None:
        """
        Set the camera to a view from the back (posterior).
        """
        camera = self._renderer.GetActiveCamera()
        f = camera.GetFocalPoint()
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(f[0], -500, f[2])
        s = camera.GetParallelScale()
        fov = self._volume.getFieldOfView()
        self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
        if self._scale is None:
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
        else: camera.SetParallelScale(s)
        self._renderwindow.Render()

    def setCameraPosition(self, pos: str) -> None:
        """
        Set the camera to a predefined position.

        Parameters
        ----------
        pos : str
            The desired position ('top', 'bottom', 'front', 'back', 'left', 'right').
        """
        if pos == 'top': self.setCameraToTop()
        elif pos == 'bottom': self.setCameraToBottom()
        elif pos == 'front': self.setCameraToFront()
        elif pos == 'back': self.setCameraToBack()
        elif pos == 'left': self.setCameraToLeft()
        else: self.setCameraToRight()

    def hideAll(self, signal: bool = True) -> None:
        """
        Hide all the 3D VTK objects (3 vtkImageSlice, vtkVolume).
        Currently, this method overrides superclass's implementation.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits ViewMethodCalled signals for synchronization (default True).
        """
        super().hideAll(signal)
        self.setSlice0Visibility(False)
        self.setSlice1Visibility(False)
        self.setSlice2Visibility(False)
        self.setTextureVisibility(False)

    def showAll(self, signal: bool = True) -> None:
        """
        Show all the 3D VTK objects (3 vtkImageSlice, vtkVolume).
        Currently, this method overrides superclass's implementation.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits ViewMethodCalled signals for synchronization (default True).
        """
        super().showAll(signal)
        self.setSlice0Visibility(True)
        self.setSlice1Visibility(True)
        self.setSlice2Visibility(True)
        self.setTextureVisibility(True)

    def getSeriesPixmapCaptures(self) -> list[QPixmap]:
        """
        Capture bitmap images from the six standard camera positions and returns them as a list of QPixmaps.

        Returns
        -------
        list[QPixmap]
            list of six QPixmap objects, one for each camera position.
        """
        caps = list()
        campos = ['top', 'bottom', 'front', 'back', 'left', 'right']
        for pos in campos:
            # Display current camera position capture
            self.setCameraPosition(pos)
            # Get current camera position capture
            c = vtkWindowToImageFilter()
            c.SetInput(self._renderwindow)
            r = vtkImageExportToArray()
            # noinspection PyArgumentList
            r.SetInputConnection(c.GetOutputPort())
            cap = r.GetArray()
            d, h, w, ch = cap.shape
            cap = QImage(cap.data, w, h, 3 * w, QImage.Format_RGB888)
            cap = cap.mirrored(False, True)
            caps.append(QPixmap.fromImage(cap))
        return caps

    def saveSeriesCapture(self) -> None:
        """
        Captures bitmap images from six standard camera positions, montages them into a single image, and saves it to
        a file (supported formats BMP, JPG, PNG, TIFF).
        """
        title = 'Save capture from multiple camera positions'
        name = QFileDialog.getSaveFileName(self, caption=title, directory=getcwd(),
                                           filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                           initialFilter='JPG (*.jpg)')[0]
        if name != '':
            chdir(dirname(name))
            campos = ['front', 'left', 'top', 'back', 'right', 'bottom']
            wait = DialogWait(title, title, progress=False)
            wait.open()
            imglist = list()
            for pos in campos:
                # Display current camera position capture
                self.setCameraPosition(pos)
                # Get current camera position capture
                wait.setInformationText('Add {} camera position capture.'.format(basename(pos.capitalize())))
                c = vtkWindowToImageFilter()
                c.SetInput(self._renderwindow)
                r = vtkImageExportToArray()
                # noinspection PyArgumentList
                r.SetInputConnection(c.GetOutputPort())
                cap = r.GetArray()
                cap = flip(cap.reshape(cap.shape[1:]), axis=0)
                imglist.append(cap)
            # New capture (2 x 3) grid
            cap = montage(stack(imglist), grid_shape=(2, 3), multichannel=True)
            # Save capture
            wait.setInformationText('Save {} capture.'.format(basename(name)))
            try: imsave(name, cap)
            except Exception as err:
                messageBox(self, title=title, text='{}'.format(err))
            finally:
                wait.close()

    def saveSeriesCaptures(self)  -> None:
        """
        Captures bitmap images from six standard camera positions, and saves them to six files (supported formats BMP,
        JPG, PNG, TIFF) suffixed with 'top', 'bottom', 'front', 'back', 'left', 'right'.
        """
        if self.hasVolume():
            title = 'Save captures from multiple camera positions'
            name = QFileDialog.getSaveFileName(self, caption=title, directory=getcwd(),
                                               filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                               initialFilter='JPG (*.jpg)')[0]
            if name != '':
                # Create directory
                path, ext = splitext(name)
                mkdir(path)
                name = basename(path)
                w = {'.bmp': vtkBMPWriter(), '.jpg': vtkJPEGWriter(),
                     '.png': vtkPNGWriter(), '.tiff': vtkTIFFWriter()}
                w = w[ext]
                campos = ['top', 'bottom', 'front', 'back', 'left', 'right']
                wait = DialogWait(title, title, progress=False)
                wait.open()
                try:
                    for pos in campos:
                        # Display current camera position capture
                        self.setCameraPosition(pos)
                        # Get current camera position capture
                        suffix = '_{}'.format(pos.capitalize())
                        slicename = join(path, '{}_{}{}'.format(name, suffix, ext))
                        wait.setInformationText('Save {} capture.'.format(basename(slicename)))
                        c = vtkWindowToImageFilter()
                        c.SetInput(self._renderwindow)
                        # Save current camera position capture
                        # noinspection PyArgumentList
                        w.SetInputConnection(c.GetOutputPort())
                        w.SetFileName(slicename)
                        w.Write()
                except Exception as err:
                    messageBox(self, title=title, text='{}'.format(err))
                finally:
                    wait.close()

    # Public mesh methods

    def getMeshCollection(self) -> SisypheMeshCollection:
        """
        Get the SisypheMeshCollection (collections of meshes) displayed in the widget.

        Returns
        -------
        SisypheMeshCollection
            collection of meshes.
        """
        return self._mesh

    def setMeshCollection(self, mesh: SisypheMeshCollection)  -> None:
        """
        Get the SisypheMeshCollection (collections of meshes) displayed in the widget.

        Returns
        -------
        SisypheMeshCollection
            collection of meshes.
        """
        if isinstance(mesh, SisypheMeshCollection): self._mesh = mesh
        else: raise TypeError('parameter type {} is not SisypheMeshCollection'.format(type(mesh)))

    def hasMesh(self) -> bool:
        """
        Check if there are any SisypheMesh instance in the collection.

        Returns
        -------
        bool
            True if meshes are present, False otherwise.
        """
        return not self._mesh.isEmpty()

    def getNumberOfMeshes(self) -> int:
        """
        Get the number of SisypheMesh instance in the collection.

        Returns
        -------
        int
            total number of SisypheMesh instances.
        """
        return len(self._mesh)

    def addMesh(self, mesh: SisypheMesh) -> None:
        """
        Add a SisypheMesh instance to the widget.

        Parameters
        ----------
        mesh : SisypheMesh
            SisypheMesh instance to add.
        """
        if isinstance(mesh, SisypheMesh):
            if mesh.getReferenceID() == self._volume.getID():
                if mesh not in self._mesh:
                    self._action['showmesh'].setVisible(True)
                    self._renderer.AddViewProp(mesh.getActor())
                    self._renderwindow.Render()
            else: raise ValueError('mesh ID {} is different from the volume ID'.format(mesh.getReferenceID()))
        else: raise TypeError('parameter type {} is not SisypheMesh'.format(type(mesh)))

    def removeMesh(self, mesh: SisypheMesh) -> None:
        """
        Remove a SisypheMesh instance from the widget.

        Parameters
        ----------
        mesh : SisypheMesh
            SisypheMesh instance to remove.
        """
        if isinstance(mesh, SisypheMesh):
            if mesh in self._mesh:
                # self._mesh.remove(mesh)
                self._renderer.RemoveActor(mesh.getActor())
                self._action['showmesh'].setVisible(not mesh.isEmpty())
                self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not SisypheMesh'.format(type(mesh)))

    def removeAllMeshes(self) -> None:
        """
        Remove all SisypheMesh instances from the widget.
        """
        if self._mesh.count() > 0:
            for mesh in self._mesh:
                self._renderer.RemoveActor(mesh.getActor())
                self._action['showmesh'].setVisible(False)
            self._renderwindow.Render()

    def setMeshOnSliceVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the meshes.

        Parameters
        ----------
        v : bool
            True to show meshes, False to hide it.
        signal : bool (optional)
            If True, emits the MeshOnSliceVisibilityChanged signal for synchronization (default True).
        """
        self._action['showmesh'].setChecked(v)
        if signal:
            # noinspection PyUnresolvedReferences
            self.MeshOnSliceVisibilityChanged.emit(self, v)

    def getMeshOnSliceVisibility(self) -> bool:
        """
        Get the visibility of the meshes.

        Returns
        -------
        bool
            True if meshes are visible, False otherwise.
        """
        return self._action['showmesh'].isChecked()

    # Public cursor methods

    def getSphereCursorRadius(self) -> int:
        """
        Get the radius, in mm, of the spherical part of the cross-shaped cursor.

        Returns
        -------
        int
            radius in mm of the sphere.
        """
        # < Revision 03/04/2025
        # self._sph.GetRadius()
        return self._sph.GetRadius()
        # Revision 03/04/2025 >

    def setSphereCursorRadius(self, r: int = 0) -> None:
        """
        Sets the radius of the spherical part of the cross-shaped cursor.

        Parameters
        ----------
        r : int (optional)
            new radius in mm for the sphere (default 0).
        """
        self._sph.SetRadius(r)
        self._sph.Update()
        self._cursorsph.GetMapper().Update()
        if r == 0: self._cursorsph.SetVisibility(False)
        else: self._cursorsph.SetVisibility(self._cursor.GetVisibility())
        self.updateRender()

    def getSphereCursorOpacity(self) -> int:
        """
        Get the opacity of the spherical part of the cross-shaped cursor.

        Returns
        -------
        int
            opacity value (0-100).
        """
        return int(self._cursorsph.GetProperty().GetOpacity() * 100)

    def setSphereCursorOpacity(self, r: int = 0) -> None:
        """
        Set the opacity of the spherical part of the cross-shaped cursor.

        Parameters
        ----------
        r : int (optional)
            The new opacity value (0-100, default 0).
        """
        self._cursorsph.GetProperty().SetOpacity(r/100)
        self.updateRender()

    def setCursorWorldPosition(self, x: float, y: float, z: float, signal: bool = True) -> None:
        """
        Set the 3D world position of the cross-shaped cursor.
        Currently, this method overrides superclass's implementation.

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
        x, y, z = self._getRoundedCoordinate([x, y, z])
        self._cursor.SetPosition(x, y, z)
        self._cursorsph.SetPosition(x, y, z)
        sx, sy, sz = self._volume.getSpacing()
        # Update slice position
        self._slice0.GetMapper().SetSliceNumber(int(z / sz))
        self._slice1.GetMapper().SetSliceNumber(int(y / sy))
        self._slice2.GetMapper().SetSliceNumber(int(x / sx))
        # Update cropping planes
        fx, fy, fz = self._volume.getFieldOfView()
        mapper = self._texture.GetMapper()
        mapper.SetCroppingRegionPlanes(x, fx, y, fy, z, fz)
        self._renderwindow.Render()
        if self.isSynchronised() and signal: self.CursorPositionChanged.emit(self, x, y, z)

    def setCursorVisibility(self, v: bool, signal: bool = True) -> None:
        """
        Set the visibility of the cross-shaped cursor.
        Currently, this method calls superclass's implementation.

        Parameters
        ----------
        v : bool
            True to show the cursor, False to hide it.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if self._cursorsph is not None:
            self._cursorsph.SetVisibility(v and (self._sph.GetRadius() > 0.0))
        super().setCursorVisibility(v, signal)

    def setLineColor(self, c: list[float] | tuple[float, float, float], signal: bool = True) -> None:
        """
        Set the color of the cross-shaped cursor.
        Currently, this method calls superclass's implementation.

        Parameters
        ----------
        c : list[float] | tuple[float, float, float]
            color as an (r, g, b) tuple with values from 0.0 to 1.0.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if self._cursorsph is not None:
            self._cursorsph.GetProperty().SetColor(c[0], c[1], c[2])
        super().setLineColor(c, signal)

    def setLineWidth(self, v: float, signal=True) -> None:
        """
        Set the line width of the cross-shaped cursor.
        Currently, this method calls superclass's implementation.

        Parameters
        ----------
        v : float
            The line width in pixels.
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if self._cursorsph is not None:
            self._cursorsph.GetProperty().SetLineWidth(v)
        super().setLineWidth(v, signal)

    def setLineOpacity(self, v: float, signal=True) -> None:
        """
        Set the line opacity of the cross-shaped cursor.
        Currently, this method calls superclass's implementation.

        Parameters
        ----------
        v : float
            Opacity value between 0.0 (transparent) and 1.0 (opaque).
        signal : bool (optional)
            If True, emits the ViewMethodCalled signal for synchronization (default True).
        """
        if v > 0.5: v2 = 0.5
        else: v2 = v
        if self._cursorsph is not None:
            self._cursorsph.GetProperty().SetOpacity(v2)
        super().setLineOpacity(v, signal)

    # Public slices methods

    def sliceMinus(self) -> None:
        """
        Move to the previous slice along the currently selected orientation.
        """
        d = self._volume.getSpacing()
        x, y, z = self.getCursorWorldPosition()
        if self._selectedSlice == 1:
            m = self._slice0.GetMapper().GetSliceNumberMinValue()
            if z > m: z -= d[2]
        elif self._selectedSlice == 2:
            m = self._slice1.GetMapper().GetSliceNumberMinValue()
            if y > m: y -= d[1]
        else:
            m = self._slice2.GetMapper().GetSliceNumberMinValue()
            if x > m: x -= d[0]
        self.setCursorWorldPosition(x, y, z, True)

    def slicePlus(self) -> None:
        """
        Move to the next slice along the currently selected orientation.
        """
        d = self._volume.getSpacing()
        x, y, z = self.getCursorWorldPosition()
        if self._selectedSlice == 1:
            m = self._slice0.GetMapper().GetSliceNumberMaxValue()
            if z < m: z += d[2]
        elif self._selectedSlice == 2:
            m = self._slice1.GetMapper().GetSliceNumberMaxValue()
            if y < m: y += d[1]
        else:
            m = self._slice2.GetMapper().GetSliceNumberMaxValue()
            if x < m: x += d[0]
        self.setCursorWorldPosition(x, y, z, True)

    def hideAllSlices(self) -> None:
        """
        Hide all three orthogonal vtkImageSlice actors.
        """
        self.setSlice0Visibility(False)
        self.setSlice1Visibility(False)
        self.setSlice2Visibility(False)

    def showAllSlices(self) -> None:
        """
        Show all three orthogonal vtkImageSlice actors.
        """
        self.setSlice0Visibility(True)
        self.setSlice1Visibility(True)
        self.setSlice2Visibility(True)

    def setSlice0Visibility(self, v: bool) -> None:
        """
        Set the visibility of the axial vtkImageSlice actor (slice 0).

        Parameters
        ----------
        v : bool
            True to show the slice, False to hide it.
        """
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice0.SetVisibility(v)
                self._action['showslice0'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setSlice1Visibility(self, v: bool) -> None:
        """
        Set the visibility of the coronal vtkImageSlice actor (slice 1).

        Parameters
        ----------
        v : bool
            True to show the slice, False to hide it.
        """
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice1.SetVisibility(v)
                self._action['showslice1'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setSlice2Visibility(self, v: bool) -> None:
        """
        Set the visibility of the sagittal vtkImageSlice actor (slice 2).

        Parameters
        ----------
        v : bool
            True to show the slice, False to hide it.
        """
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice2.SetVisibility(v)
                self._action['showslice2'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSlice0Visibility(self) -> bool:
        """
        Get the visibility of the axial vtkImageSlice actor (slice 0).

        Returns
        -------
        bool
            True if the slice is visible, False otherwise.
        """
        # < Revision 20/10/2025
        # self._slice0.GetVisibility()
        return self._slice0.GetVisibility()
        # Revision 20/10/2025 >

    def getSlice1Visibility(self) -> bool:
        """
        Get the visibility of the coronal vtkImageSlice actor (slice 1).

        Returns
        -------
        bool
            True if the slice is visible, False otherwise.
        """
        # < Revision 20/10/2025
        # self._slice1.GetVisibility()
        return self._slice1.GetVisibility()
        # Revision 20/10/2025 >

    def getSlice2Visibility(self) -> bool:
        """
        Gets the visibility of the sagittal vtkImageSlice actor (slice 2).

        Returns
        -------
        bool
            True if the slice is visible, False otherwise.
        """
        # < Revision 20/10/2025
        # self._slice2.GetVisibility()
        return self._slice2.GetVisibility()
        # Revision 20/10/2025 >

    # Public texture methods

    def loadTransfer(self) -> None:
        """
        Load a SisypheColorTransfer instance from a file (.xtfer).
        """
        if self.hasVolume():
            self._transfer.setDefault(self._volume)
            if self._volume.hasFilename():
                name, ext = splitext(self._volume.getFilename())
                name += self._transfer.getFileExt()
                if exists(name):
                    self._transfer.loadFromXML(name)

    def saveTransfer(self) -> None:
        """
        Save the current SisypheColorTransfer instance to a file (.xtfer).
        """
        if self.hasVolume():
            self._transfer.setID(self._volume.getArrayID())
            self._transfer.saveToXML(self._volume.getFilename())

    def getTransfer(self) -> SisypheColorTransfer:
        """
        Get the current SisypheColorTransfer instance.

        Returns
        -------
        SisypheColorTransfer
            current color transfer function instance.
        """
        return self._transfer

    def setTransfer(self, transfer: SisypheColorTransfer) -> None:
        """
        Set the SisypheColorTransfer instance for volume rendering.

        Parameters
        ----------
        transfer : SisypheColorTransfer
            new transfer function instance to apply.
        """
        if isinstance(transfer, SisypheColorTransfer):
            self._transfer = transfer
            self._updateTextureTransfer()
        else: raise TypeError('parameter type {} is not SisypheColorTransfer.'.format(type(transfer)))

    def setGradientOpacity(self, v: bool) -> None:
        """
        Enable or disable the gradient opacity for volume rendering.
        Use a gradient transfer function in addition to the color transfer function for volume rendering.

        Parameters
        ----------
        v : bool
            True to enable gradient opacity, False to disable it.
        """
        prop = self._texture.GetProperty()
        prop.SetDisableGradientOpacity(int(not v))
        self._renderwindow.Render()

    def gradientOpacityOn(self) -> None:
        """
        Enable gradient opacity for volume rendering.
        """
        prop = self._texture.GetProperty()
        prop.DisableGradientOpacityOff()
        self._renderwindow.Render()

    def gradientOpacityOff(self) -> None:
        """
        Disable gradient opacity for volume rendering.
        """
        prop = self._texture.GetProperty()
        prop.DisableGradientOpacityOn()
        self._renderwindow.Render()

    def getGradientOpacity(self) -> bool:
        """
        Get the state of the gradient opacity.

        Returns
        -------
        bool
            True if gradient opacity is enabled, False otherwise.
        """
        prop = self._texture.GetProperty()
        return not bool(prop.GetDisableGradientOpacity())

    def setTextureVisibility(self, v: bool) -> None:
        """
        Set the visibility of the texture rendering of the vtkVolume actor.

        Parameters
        ----------
        v : bool
            True to show the texture rendering, False to hide it.
        """
        if isinstance(v, bool):
            if self.hasVolume():
                self._texture.SetVisibility(v)
                self._action['showtexture'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextureVisibility(self) -> bool:
        """
        Get the visibility of the texture rendering of the vtkVolume actor.

        Returns
        -------
        bool
            True if the texture rendering is visible, False otherwise.
        """
        # < Revision 20/10/2025
        # self._texture.GetVisibility()
        return self._texture.GetVisibility()
        # Revision 20/10/2025 >

    def getBlendMode(self) -> int:
        """
        Get the current blend mode used for the rendering as an integer code.

        Returns
        -------
        int
            integer code of the current blend mode.
        """
        return self._texture.GetMapper().GetBlendMode()

    def getBlendModeAsString(self) -> str:
        """
        Get the current blend mode used for the rendering as a string.

        Returns
        -------
        str
            string representation of the current blend mode.
        """
        return self._CODETOBLEND[self._texture.GetMapper().GetBlendMode()]

    def setBlendMode(self, k: int | str) -> None:
        """
        Set the blend mode used for the rendering .

        Parameters
        ----------
        k : int | str
            The blend mode to set, either as an integer code or a string.
        """
        if isinstance(k, str):
            k = self._BLENDTOCODE[k]
        if isinstance(k, int):
            self._texture.GetMapper().SetBlendMode(k)
            self._texture.Update()
            self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not int or str'.format(type(k)))

    def setBlendModeToComposite(self) -> None:
        """
        Sets the blend mode for the rendering to 'Composite'.
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToComposite()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToMaximumIntensity(self) -> None:
        """
        Set the blend mode for the rendering to 'Maximum Intensity Projection' (MIP).
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToMaximumIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToMinimumIntensity(self) -> None:
        """
        Set the blend mode for the rendering to 'Minimum Intensity Projection'.
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToMinimumIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToAverageIntensity(self) -> None:
        """
        Set the blend mode for the rendering to 'Average Intensity Projection'.
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToAverageIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToAdditive(self) -> None:
        """
        Set the blend mode for the rendering to 'Additive'.
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToAdditive()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToIsoSurface(self) -> None:
        """
        Sets the blend mode for the rendering to 'IsoSurface'.
        """
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToIsoSurface()
            self._texture.Update()
            self._renderwindow.Render()

    def getCropping(self) -> bool:
        """
        Get the cropping state of the volume rendering.

        Returns
        -------
        bool
            True if cropping is enabled, False otherwise.
        """
        return self._texture.GetMapper().GetCropping()

    def setCropping(self, v: bool) -> None:
        """
        Enable or disable cropping for the volume rendering.

        Parameters
        ----------
        v : bool
            True to enable cropping, False to disable it.
        """
        if isinstance(v, bool):
            self._texture.GetMapper().SetCropping(v)
            self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCroppingOn(self) -> None:
        """
        Enable cropping for the volume rendering.
        """
        self._texture.GetMapper().CroppingOn()
        self._renderwindow.Render()

    def setCroppingOff(self) -> None:
        """
        Disable cropping for the volume rendering.
        """
        self._texture.GetMapper().CroppingOff()
        self._renderwindow.Render()

    def cropTexture(self) -> None:
        """
        Crop the volume rendering based on the picked region relative to the cursor position.
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            cname = prop.GetClassName()
            if cname == 'vtkVolume':
                self.setCroppingOn()
                x, y, z = picker.GetPickPosition()
                xv, yv, zv = self._renderer.GetActiveCamera().GetPosition()
                xc, yc, zc = self.getCursorWorldPosition()
                region = 0
                d = zv - zc
                if abs(d) > 200:
                    if d > 0: region += 9
                elif z > zc:
                    region += 9
                d = yv - yc
                if abs(d) > 200:
                    if d > 0: region += 3
                elif y > yc:
                    region += 3
                d = xv - xc
                if abs(d) > 200:
                    if d > 0: region += 1
                elif x > xc:
                    region += 1
                region = pow(2, region)
                self._croptag -= region
                self._texture.GetMapper().SetCroppingRegionFlags(self._croptag)
                self._renderwindow.Render()

    def uncropTexture(self) -> None:
        """
        Reset the volume rendering cropping to show the full volume.
        """
        self._croptag = 0x361B
        self._texture.GetMapper().SetCroppingRegionFlags(self._croptag)
        self.setCroppingOff()

    # Public tract methods

    def getTractCollection(self) -> SisypheTractCollection:
        """
        Get the SisypheTractCollection (collections of streamlines) displayed in the widget.

        Returns
        -------
        SisypheTractCollection
            collection of streamlines.
        """
        return self._tract

    def setTractCollection(self, tracts: SisypheTractCollection) -> None:
        """
        Set the SisypheTractCollection (collections of streamlines) to be displayed in the widget.

        Parameters
        ----------
        tracts : SisypheTractCollection
            collection of streamlines.
        """
        self._tract = tracts
        self._tract.setRenderer(self._renderer)

    def hasTracts(self) -> bool:
        """
        Check if there are any streamlines (tracts) in the collection.

        Returns
        -------
        bool
            True if streamlines (tracts) are present, False otherwise.
        """
        return not self._tract.isEmpty()

    # Public openGL actor methods

    def hasSurfaceMesh(self) -> bool:
        """
        Check if an outer surface SisypheMesh instance has been generated and is available.

        Returns
        -------
        bool
            True if the outer surface SisypheMesh instance exists, False otherwise.
        """
        return 'OuterSurface' in self._mesh.keys()

    def setSurfaceVisibility(self, v: bool) -> None:
        """
        Set the visibility of the outer surface SisypheMesh instance. If the mesh doesn't exist, it is created first.

        Parameters
        ----------
        v : bool
            True to show the outer surface SisypheMesh instance, False to hide it.
        """
        if isinstance(v, bool):
            if self.hasVolume():
                if not self.hasSurfaceMesh() and v: self._addOuterSurfaceMesh()
                if self.hasSurfaceMesh():
                    self._mesh['OuterSurface'].setVisibility(v)
                    self._action['showsurface'].setChecked(v)
                    self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSurfaceVisibility(self) -> bool:
        """
        Gets the visibility of the outer surface SisypheMesh instance.

        Returns
        -------
        bool
            True if the outer surface SisypheMesh instance is visible, False otherwise.
        """
        # < Revision 20/10/2025
        # self._mesh['OuterSurface'].getVisibility()
        return self._mesh['OuterSurface'].getVisibility()
        # Revision 20/10/2025 >

    def editActorProperties(self) -> None:
        """
        Open a dialog to edit the properties of the picked vtkActor.
        """
        prop = self._getPickedActor()
        if prop:
            dialog = DialogMeshProperties()
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(dialog, c)
            dialog.setProperties(prop.GetProperty())
            dialog.UpdateRender.connect(self._renderwindow.Render)
            dialog.show()
            dialog.activateWindow()

    # Private vtk events methods

    def _onRightPressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Handles the right mouse button press VTK event to show a context-sensitive popup menu.
        Currently, this method overrides superclass's implementation.
        """
        x, y = self._window.GetInteractorStyle().GetLastPos()
        p = self._getScreenFromDisplay(x, y)
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        menu = self._popup
        if n:
            prop = picker.GetViewProp()
            cname = prop.GetClassName()
            # if cname == 'vtkImageSlice': menu = self._slicespopup
            if cname == 'vtkVolume': menu = self._texturepopup
            elif cname == 'vtkOpenGLActor': menu = self._meshpopup
            elif cname in ('vtkDistanceRepresentation3D', 'vtkAngleRepresentation3D'): menu = self._toolpopup
            # < Revision 13/03/2025
            # tools menu management
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
                menu = self._toolpopup
            # Revision 13/03/2025 >
        menu.popup(p)

    def _onWheelForwardEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles the mouse wheel forward VTK event for zooming, slicing, or navigating streamlines.
        Currently, this method overrides superclass's implementation.
        """
        if self.hasVolume():
            if self._interactor.GetKeySym() == 'Control_L':
                self.zoomOut()
            elif self._selectedSlice:
                self.slicePlus()
            elif self._slprop is not None:
                # noinspection PyUnresolvedReferences
                n = self._slprop.GetMapper().GetInput().GetPoints().GetNumberOfPoints()
                self._slid += 2
                if self._slid > n - 1: self._slid = 0
                # noinspection PyUnresolvedReferences
                p = self._slprop.GetMapper().GetInput().GetPoints().GetPoint(self._slid)
                self.setCursorWorldPosition(p[0], p[1], p[2], True)

    def _onWheelBackwardEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles the mouse wheel backward VTK event for zooming, slicing, or navigating streamlines.
        Currently, this method overrides superclass's implementation.
        """
        if self.hasVolume():
            if self._interactor.GetKeySym() == 'Control_L':
                self.zoomIn()
            elif self._selectedSlice:
                self.sliceMinus()
            elif self._slprop is not None:
                self._slid -= 2
                if self._slid < 0:
                    # noinspection PyUnresolvedReferences
                    n = self._slprop.GetMapper().GetInput().GetPoints().GetNumberOfPoints()
                    self._slid = n - 1
                # noinspection PyUnresolvedReferences
                p = self._slprop.GetMapper().GetInput().GetPoints().GetPoint(self._slid)
                self.setCursorWorldPosition(p[0], p[1], p[2], True)

    def _onLeftPressEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles the left mouse button press VTK event for interaction modes like zoom, pan, rotate, and picking.
        Currently, this method calls superclass's implementation.
        """
        super()._onLeftPressEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            self._mousepos0 = interactorstyle.GetLastPos()
            k = self._interactor.GetKeySym()
            # Zoom, Control Key (Cmd key on Mac)
            if k == 'Control_L' or self.getZoomFlag() is True:
                self._scale0 = self._renderer.GetActiveCamera().GetParallelScale()
            # Pan, Alt Key
            elif k == 'Alt_L' or self.getMoveFlag() is True:
                self._camfocal0 = self._renderer.GetActiveCamera().GetFocalPoint()
                self.setCentralCrossVisibilityOn()
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_HAND)
            # Windowing, Shift Key
            elif k == 'Shift_L' or self.getLevelFlag() is True:
                self._win0 = interactorstyle.GetLastPos()
            # Camera movement
            else:
                self._campos0 = self._renderer.GetActiveCamera().GetPosition()
            # Always test slice selection
            x, y = self._window.GetInteractorStyle().GetLastPos()
            picker = self._interactor.GetPicker()
            n = picker.Pick(x, y, 0, self._renderer)
            self._selectedSlice = 0
            self._slprop = None
            if n:
                prop = picker.GetViewProp()
                # cname = prop.GetClassName()
                cname = prop.GetObjectName()
                if cname == 'slice':  # 'vtkImageSlice':
                    if prop == self._slice0: self._selectedSlice = 1
                    elif prop == self._slice1: self._selectedSlice = 2
                    else: self._selectedSlice = 3
                    if k == 'Control_L':
                        x, y, z = picker.GetPickPosition()
                        self.setCursorWorldPosition(x, y, z, True)
                elif cname == 'streamline':
                    self._slid = 0
                    self._slprop = prop
                    p = prop.GetMapper().GetInput().GetPoints().GetPoint(0)
                    self.setCursorWorldPosition(p[0], p[1], p[2], True)

    def _onLeftReleaseEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles the left mouse button release VTK event to reset interaction states.
        Currently, this method overrides superclass's implementation.
        """
        if self.hasVolume():
            k = self._interactor.GetKeySym()
            if k == 'Alt_L' or self.getMoveFlag() is True:
                self._interactor.SetKeySym('')
                self.setCentralCrossVisibilityOff()
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)
                self._renderwindow.Render()
            elif k == 'Shift_L' or self.getLevelFlag() is True:
                self._interactor.SetKeySym('')

    def _onMiddlePressEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Handles the middle mouse button press event, which does nothing.
        Currently, this method overrides superclass's implementation.
        """
        pass

    def _onMouseMoveEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles the mouse move event for interactions like zoom, pan, window/level, and camera rotation.
        Currently, this method overrides superclass's implementation.
        """
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            last = interactorstyle.GetLastPos()
            k = self._interactor.GetKeySym()
            # Zoom, Control Key (Cmd key on Mac)
            if k == 'Control_L' or self.getZoomFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Zoom
                    dx = (last[1] - self._mousepos0[1]) / 10
                    if dx < 0:
                        base = 1.1
                    else:
                        base = 0.9
                    z = pow(base, abs(dx))
                    if self._scale0:
                        self._renderer.GetActiveCamera().SetParallelScale(self._scale0 * z)
                    self._renderwindow.Render()
            # Pan, Alt Key
            elif k == 'Alt_L' or self.getMoveFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Camera and focal position
                    camera = self._renderer.GetActiveCamera()
                    camera.SetFocalPoint(self._camfocal0)
                    pfirst = self._getWorldFromDisplay(self._mousepos0[0],  self._mousepos0[1])
                    plast = self._getWorldFromDisplay(last[0], last[1])
                    p = [self._camfocal0[0] + pfirst[0] - plast[0],
                         self._camfocal0[1] + pfirst[1] - plast[1],
                         self._camfocal0[2] + pfirst[2] - plast[2]]
                    camera.SetFocalPoint(p)
                    self._renderwindow.Render()
            # Windowing, Shift Key
            elif k == 'Shift_L' or self.getLevelFlag() is True:
                if interactorstyle.GetButton() == 1:
                    wmin, wmax = self._volume.display.getWindow()
                    rmin, rmax = self._volume.display.getRange()
                    dx = self._win0[0] - last[0]
                    dy = last[1] - self._win0[1]
                    r = (rmax - rmin) / 100
                    if dx != 0:
                        wmin = wmin + (dx / abs(dx)) * r
                    if dy != 0:
                        wmax = wmax + (dy / abs(dy)) * r
                    self._volume.display.setWindow(wmin, wmax)
                    self._renderwindow.Render()
                    self._win0 = last
            # Camera movement
            else:
                if interactorstyle.GetButton() == 1:
                    camera = self._renderer.GetActiveCamera()
                    camera.SetPosition(self._campos0)
                    dx = self._mousepos0[0] - last[0]
                    dy = self._mousepos0[1] - last[1]
                    d = camera.GetDistance()
                    # < Revision 13/03/2025
                    # anglex = degrees(atan(dx / d)) * 5
                    # angley = degrees(atan(dy / d)) * 5
                    anglex = degrees(atan2(dx, d)) * 5
                    angley = degrees(atan2(dy, d)) * 5
                    # Revision 13/03/2025 >
                    camera.Azimuth(anglex)
                    camera.Elevation(angley)
                    self._renderwindow.Render()
                    # noinspection PyUnresolvedReferences
                    self.CameraChanged.emit(self)

    def _onKeyPressEvent(self,  obj: vtkObject, evt_name: str) -> None:
        """
        Handles key press events for zooming and slicing.
        Currently, this method overrides superclass's implementation.
        """
        if self.hasVolume():
            k = self._interactor.GetKeySym()
            if self._interactor.GetControlKey():
                if k == 'Up' or k == 'Right':
                    self.zoomIn()
                elif k == 'Down' or k == 'Left':
                    self.zoomOut()
            elif self._selectedSlice:
                if k == 'Up' or k == 'Right':
                    self.sliceMinus()
                elif k == 'Down' or k == 'Left':
                    self.slicePlus()

    def _onKeyReleaseEvent(self, obj: vtkObject, evt_name: str) -> None:
        """
        Handles key release events to reset interaction states.
        Currently, this method overrides superclass's implementation.
        """
        self._interactor.SetKeySym('')
        interactorstyle = self._window.GetInteractorStyle()
        if interactorstyle.GetButton() == 1:
            self.setCentralCrossVisibilityOff()
            self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)
