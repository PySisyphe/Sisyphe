"""
    External packages/modules

        Name            Homepage link                                               Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        skimage         https://scikit-image.org/                                   Image processing
        vtk             https://vtk.org/                                            Visualization
"""

from os import mkdir
from os import getcwd
from os.path import join
from os.path import exists
from os.path import basename
from os.path import splitext

from math import atan
from math import degrees

from numpy import flip
from numpy import stack

from skimage.util import montage
from skimage.io import imsave

from vtk import vtkCursor3D
from vtk import vtkPolyDataMapper
from vtk import vtkActor
from vtk import vtkVolume
from vtk import vtkImageSlice
from vtk import vtkImageSliceMapper
from vtk import vtkVolumeProperty
from vtk import vtkSmartVolumeMapper
from vtk import vtkFlyingEdges3D
from vtk import vtkBMPWriter
from vtk import vtkJPEGWriter
from vtk import vtkPNGWriter
from vtk import vtkTIFFWriter
from vtk import vtkWindowToImageFilter
from vtk import VTK_CURSOR_HAND
from vtk import VTK_CURSOR_ARROW
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray

from SimpleITK import sitkFloat32
from SimpleITK import Cast
from SimpleITK import StatisticsImageFilter
from SimpleITK import BinaryFillholeImageFilter
from SimpleITK import SmoothingRecursiveGaussian

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

from Sisyphe.core.sisypheImage import simpleITKToVTK
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheLUT import SisypheColorTransfer
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheMesh import SisypheMeshCollection
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.gui.dialogMeshProperties import DialogMeshProperties
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy
    
        QWidget -> AbstractViewWidget -> VolumeViewWidget
        
    Description
    
         Class to display 3D render of SisypheVolume instances.
         Supports texture, mesh, and three orthogonal slices.
         Interactive management of target and trajectory widgets.
"""


class VolumeViewWidget(AbstractViewWidget):
    """
        VolumeViewWidget class

        Description

            Display volume rendering.

        Inheritance

            QWidget -> AbstractViewWidget -> VolumeViewWidget

        Private attributes

            _slice0         vtkImageSlice, axial slice
            _slice1         vtkImageSlice, coronal slice
            _slice2         vtkImageSlice, sagittal slice
            _planewidget    vtkImplicitPlaneWidget
            _texture        vtkVolume
            _mesh           SisypheMeshCollection
            _transfer       SisypheColorTransfer
            _croptag        int, crop direction code
            _scale0         float, zoom factor before event start, interactive zoom management
            _mousepos0      (float, float, float), mouse position before event start
            _campos0        (float, float, float), camera position before event start
            _camfocal0      float, focal depth before event start
            _selectedslice  int, number of the selected slice
            _action         QAction
            _popup          QMenu, popup menu
            _menuVisibility QMenu, popup submenu for actors visibility (slices, texture, mesh)
            _menuPosition   QMenu, popup submenu for predefined camera position
            _texturepopup   QMenu, popup submenu for texture settings
            _meshpopup      QMenu, popup menu for mesh settings

        Custom QtSignal

            emitted from DialogMeshProperties
            UpdateRender            ->          received by VolumeViewWidget
                                                No parameter

        Public methods

            loadTransfer()
            saveTransfer()
            setTransfer(SisypheColorTransfer)
            SisypheColorTransfer = getTransfer()
            setGradientOpacity(bool)
            bool = GetGradientOpacity()
            gradientOpacityOn()
            gradientOpacityOff()
            setVolume(sisypheVolume)
            QMenu = getPopupCameraPosition()
            QMenu = getPopupTextureActor()
            SisypheMeshCollection = getMesh()
            setMesh(SisypheMeshCollection)
            setCursorWorldPosition(float, float, float, bool)
            setCameraToTop()
            setCameraToBottom()
            setCameraToLeft()
            setCameraToRight()
            setCameraToFront()
            setCameraToBack()
            setCameraPosition(str)
            bool = hasMesh()
            addMesh(sisypheMesh)
            updateMeshes()
            removeMesh(sisypheMesh)
            removeAllMeshes()
            int = getNumberOfMeshes()
            removeMesh(str)
            removeAllMeshes()
            setSlice0Visibility(bool)
            setSlice1Visibility(bool)
            setSlice2Visibility(bool)
            setTextureVisibility(bool)
            bool = getSlice0Visibility()
            bool = getSlice1Visibility()
            bool = getSlice2Visibility()
            bool = getTextureVisibility()
            int = getBlendMode()
            str = getBlendModeAsString()
            setBlendMode(int or str)
            setBlendModeToComposite()
            setBlendModeToMaximumIntensity()
            setBlendModeToMinimumIntensity()
            setBlendModeToAverageIntensity()
            setBlendModeToAdditive()
            setBlendModeToIsoSurface()

            inherited AbstractViewWidget methods
            inherited QWidget methods
    """

    _CODETOBLEND = {0: 'composite', 1: 'MaximumIntensity', 2: 'MinimumIntensity',
                    3: 'AverageIntensity', 4: 'Additive', 5: 'IsoSurface'}

    _BLENDTOCODE = {'composite': 0, 'MaximumIntensity': 1, 'MinimumIntensity': 2,
                    'AverageIntensity': 3, 'Additive': 4, 'IsoSurface': 5}

    # Custom Qt signals

    CameraChanged = pyqtSignal(QWidget)

    # Public class methods

    @classmethod
    def getBlendAsString(cls, k):
        if isinstance(k, int):
            return cls._CODETOBLEND[k]
        else: raise TypeError('parameter type {} is not int.'.format(type(k)))

    @classmethod
    def getBlendFromString(cls, k):
        if isinstance(k, str):
            return cls._BLENDTOCODE[k]
        else: raise TypeError('parameter type {} is not str.'.format(type(k)))

            # Private methods

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._slice0 = None         # vtkImageSlice, axial
        self._slice1 = None         # vtkImageSlice, coronal
        self._slice2 = None         # vtkImageSlice, sagittal
        self._texture = None        # vtkVolume
        self._mesh = SisypheMeshCollection()
        self._transfer = SisypheColorTransfer()
        self._croptag = 0x361B

        self._scale0 = None         # scale before event start
        self._mousepos0 = None      # mouse position before event start
        self._campos0 = None        # camera position before event start
        self._camfocal0 = None      # camera focal point before event start
        self._selectedSlice = 0     # number of the selected slice

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
        self._action['showslice0'] = QAction('Show 3D axial slice', self)
        self._action['showslice1'] = QAction('Show 3D coronal slice', self)
        self._action['showslice2'] = QAction('Show 3D sagittal slice', self)
        self._action['showslices'] = QAction('Show all 3D slices', self)
        self._action['hideslices'] = QAction('Hide all 3D slices', self)
        self._action['showtexture'] = QAction('Show texture volume rendering', self)
        self._action['showsurface'] = QAction('Show outer mesh isosurface', self)
        self._group_orient = QActionGroup(self)
        self._group_orient.setExclusive(True)
        self._group_orient.addAction(self._action['top'])
        self._group_orient.addAction(self._action['bottom'])
        self._group_orient.addAction(self._action['left'])
        self._group_orient.addAction(self._action['right'])
        self._group_orient.addAction(self._action['front'])
        self._group_orient.addAction(self._action['back'])
        self._action['left'].setChecked(True)
        self._action['showslice0'].setCheckable(True)
        self._action['showslice1'].setCheckable(True)
        self._action['showslice2'].setCheckable(True)
        self._action['showtexture'].setCheckable(True)
        self._action['showsurface'].setCheckable(True)
        self._action['showslice0'].setChecked(True)
        self._action['showslice1'].setChecked(True)
        self._action['showslice2'].setChecked(True)
        self._action['showtexture'].setChecked(False)
        self._action['showsurface'].setChecked(False)
        self._action['showslice0'].triggered.connect(
            lambda: self.setSlice0Visibility(self._action['showslice0'].isChecked()))
        self._action['showslice1'].triggered.connect(
            lambda: self.setSlice1Visibility(self._action['showslice1'].isChecked()))
        self._action['showslice2'].triggered.connect(
            lambda: self.setSlice2Visibility(self._action['showslice2'].isChecked()))
        self._action['showtexture'].triggered.connect(
            lambda: self.setTextureVisibility(self._action['showtexture'].isChecked()))
        self._action['showsurface'].triggered.connect(
            lambda: self.setSurfaceVisibility(self._action['showsurface'].isChecked()))
        self._action['showslices'].triggered.connect(self.showAllSlices)
        self._action['hideslices'].triggered.connect(self.hideAllSlices)
        self._menuPosition = QMenu('Position', self._popup)
        self._menuPosition.addAction(self._action['top'])
        self._menuPosition.addAction(self._action['bottom'])
        self._menuPosition.addAction(self._action['left'])
        self._menuPosition.addAction(self._action['right'])
        self._menuPosition.addAction(self._action['front'])
        self._menuPosition.addAction(self._action['back'])
        self._popup.insertMenu(self._popup.actions()[2], self._menuPosition)
        self._menuVisibility.insertSeparator(self._action['hideall'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice0'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice1'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslice2'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showslices'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showtexture'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['showsurface'])
        self._menuVisibility.insertAction(self._action['hideall'], self._action['hideslices'])

        self._action['orthodistance'].setVisible(False)
        self._action['box'].setVisible(False)
        self._action['text'].setVisible(False)
        self._action['target'].setVisible(False)
        self._action['trajectory'].setVisible(False)
        self._action['edittext'].setVisible(False)
        self._action['textprop'].setVisible(False)
        self._action['followflag'].setVisible(False)
        # self._action['showorientation'].setVisible(False)

        self._action['captureseries'] = QAction('Save captures from multiple camera positions...', self)
        self._action['captureseries2'] = QAction('Save single capture from multiple camera positions...', self)
        self._action['captureseries'].triggered.connect(lambda dummy: self.saveSeriesCaptures())
        self._action['captureseries2'].triggered.connect(lambda dummy: self.saveSeriesCapture())
        self._popup.addAction(self._action['captureseries'])
        self._popup.addAction(self._action['captureseries2'])

        # Init texture popup menu

        self._texturepopup = QMenu()
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
        submenu.addAction(self._action['composite'])
        submenu.addAction(self._action['maxintensity'])
        submenu.addAction(self._action['minintensity'])
        submenu.addAction(self._action['averageintensity'])
        submenu.addAction(self._action['additive'])
        submenu.addAction(self._action['isosurface'])
        self._texturepopup.addMenu(submenu)
        submenu = QMenu('Transfer function', self._texturepopup)
        submenu.addAction(self._action['loadtransfer'])
        submenu.addAction(self._action['savetransfer'])
        self._texturepopup.addMenu(submenu)

        # Init mesh popup menu

        self._meshpopup = QMenu()
        self._action['meshprop'] = QAction('Edit properties...', self)
        self._action['meshprop'].triggered.connect(self.editActorProperties)
        self._meshpopup.addAction(self._action['meshprop'])

        # Viewport tooltip

        self._tooltipstr = 'View control:\n' \
                           '\tMouseWheel slices through selected orientation,\n' \
                           '\tUp or Left key to previous slice in selected orientation,\n' \
                           '\tDown or Right key to next slice in selected orientation,\n' \
                           '\tMouseWheel + Ctrl Key (Cmd Key mac os) to change zoom,\n' \
                           '\tUp or Left + Ctrl Key (Cmd Key mac os) to zoom out,\n' \
                           '\tDown or Right + Ctrl Key (Cmd Key mac os) to zoom in,\n' \
                           '\tLeft click to select slice,\n' \
                           '\tLeft click + Ctrl Key to move cursor position,\n' \
                           '\tLeft click and drag to rotate view,\n' \
                           '\tLeft click + Ctrl Key (Cmd Key mac os) and drag to change zoom,\n' \
                           '\tLeft click + Alt Key and drag to pan,\n' \
                           '\tLeft click + Shift Key and drag to change window/level,\n' \
                           '\tRight click to display popup menu.'
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

        self._renderer.GetLights().GetItemAsObject(0).SetAmbientColor(1.0, 1.0, 1.0)

    # Private methods

    def _addSlice(self, orient, alpha):
        mapper = vtkImageSliceMapper()
        mapper.BorderOn()
        mapper.SetInputData(self._volume.getVTKImage())
        mapper.SetOrientation(orient)
        mapper.SliceFacesCameraOff()
        mapper.SliceAtFocalPointOff()
        slc = vtkImageSlice()
        slc.SetMapper(mapper)
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(self._volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._renderer.AddViewProp(slc)
        return slc

    def _addTexture(self):
        self._texture = vtkVolume()
        mapper = vtkSmartVolumeMapper()
        mapper.SetInputData(self._volume.getVTKImage())
        mapper.SetBlendModeToComposite()
        mapper.CroppingOff()
        prop = vtkVolumeProperty()
        prop.ShadeOff()
        self.loadTransfer()
        prop.DisableGradientOpacityOff()
        prop.SetColor(self._transfer.getColorTransfer())
        prop.SetScalarOpacity(self._transfer.getAlphaTransfer())
        prop.SetGradientOpacity(self._transfer.getGradientTransfer())
        prop.SetInterpolationTypeToLinear()
        self._texture.SetMapper(mapper)
        self._texture.SetProperty(prop)
        self._renderer.AddViewProp(self._texture)

    def _addOuterSurfaceMesh(self):
        f = StatisticsImageFilter()
        f.Execute(self._volume.getSITKImage())
        threshold = f.GetMean()
        mask = self._volume.getSITKImage() > threshold
        # Fill mask
        f = BinaryFillholeImageFilter()
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
        f.Update()
        # Mesh attributes
        mesh = SisypheMesh()
        mesh.setPolyData(f.GetOutput())
        mesh.fillHoles(1000)
        mesh.setReferenceID(self._volume)
        mesh.setName('OuterSurface')
        mesh.setScalarColorVisibilityOff()
        mesh.setColor(1.0, 0.0, 0.0)
        mesh.setVisibilityOff()
        mesh.shadingOn()
        mesh.setPhongRendering()
        self._mesh.append(mesh)
        self._renderer.AddViewProp(mesh.getActor())

    def _initCursor(self):
        if self.hasVolume():
            cursor = vtkCursor3D()
            cursor.AxesOn()
            cursor.OutlineOff()
            cursor.XShadowsOff()
            cursor.YShadowsOff()
            cursor.ZShadowsOff()
            cursor.WrapOff()
            fx, fy, fz = self._volume.getFieldOfView()
            fx /= 2
            fy /= 2
            fz /= 2
            cursor.SetModelBounds(-fx, fx, -fy, fy, -fz, fz)
            cursor.Update()
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(cursor.GetOutputPort())
            self._cursor = vtkActor()
            self._cursor.SetMapper(mapper)
            self._cursor.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
            self._cursor.SetVisibility(False)
            self._renderer.AddActor(self._cursor)

    def _getPickedSlice(self):
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() != 'vtkImageSlice': prop = None
            return prop
        else: return None

    def _getPickedActor(self):
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() != 'vtkOpenGLActor': prop = None
            return prop
        else: return None

    def _getPickedTool(self):
        x, y = self._window.GetInteractorStyle().GetLastPos()
        picker = self._interactor.GetPicker()
        n = picker.Pick(x, y, 0, self._renderer)
        if n:
            prop = picker.GetViewProp()
            if prop.GetClassName() not in ('vtkDistanceRepresentation3D',
                                           'vtkAngleRepresentation3D'): prop = None
            return prop
        else: return None

    def _updateTextureTransfer(self):
        prop = self._texture.GetProperty()
        prop.SetColor(self._transfer.getColorTransfer())
        prop.SetScalarOpacity(self._transfer.getAlphaTransfer())
        prop.SetGradientOpacity(self._transfer.getGradientTransfer())
        self.updateRender()

    # Public methods

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume(): self.removeVolume()
            super().setVolume(volume)
            self._slice0 = self._addSlice(2, 1.0)  # axial
            self._slice1 = self._addSlice(1, 1.0)  # coronal
            self._slice2 = self._addSlice(0, 1.0)  # sagittal
            self._addTexture()
            # self._addOuterSurfaceMesh()
            self.setTextureVisibility(self._action['showtexture'].isChecked())
            self._initCursor()
            x, y, z = self._slice0.GetCenter()
            self.setCursorWorldPosition(x, y, z, False)
            self._renderer.GetActiveCamera().SetFocalPoint(x, y, z)
            self.setCameraToLeft()
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(volume)))

    def removeVolume(self):
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

    def getPopupCameraPosition(self):
        return self._menuPosition

    def getPopupTextureActor(self):
        return self._texturepopup

    def getMeshCollection(self):
        return self._mesh

    def setMeshCollection(self, mesh):
        if isinstance(mesh, SisypheMeshCollection):
            self._mesh = mesh
        else: raise TypeError('parameter type {} is not SisypheMeshCollection'.format(type(mesh)))

    def hasMesh(self):
        return not self._mesh.isEmpty()

    def getNumberOfMeshes(self):
        return len(self._mesh)

    def addMesh(self, mesh):
        if isinstance(mesh, SisypheMesh):
            if mesh.getReferenceID() == self._volume.getID():
                if mesh not in self._mesh:
                    self._mesh.append(mesh)
                    self._renderer.AddViewProp(mesh.getActor())
                    self.updateRender()
            else: raise ValueError('mesh ID {} is different from the volume ID'.format(mesh.getReferenceID()))
        else: raise TypeError('parameter type {} is not SisypheMesh'.format(type(mesh)))

    def updateMeshes(self):
        c = self._renderer.GetActors()
        for mesh in self._mesh:
            if c.IsItemPresent(mesh.getActor()) == 0:
                self._renderer.AddViewProp(mesh.getActor())
                self.updateRender()

    def removeMesh(self, mesh):
        if isinstance(mesh, SisypheMesh):
            if mesh in self._mesh:
                if mesh in self._mesh: self._mesh.remove(mesh)
                self._renderer.RemoveActor(mesh.getActor())
        else: raise TypeError('parameter type {} is not SisypheMesh'.format(type(mesh)))

    def removeAllMeshes(self):
        for mesh in self._mesh:
            self._renderer.RemoveActor(mesh.getActor())
        self._mesh.clear()

    def setCursorWorldPosition(self, x, y, z, signal=True):
        x, y, z = self._getRoundedCoordinate([x, y, z])
        self._cursor.SetPosition(x, y, z)
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

    def setCameraToTop(self):
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

    def setCameraToBottom(self):
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

    def setCameraToLeft(self):
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

    def setCameraToRight(self):
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

    def setCameraToFront(self):
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

    def setCameraToBack(self):
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

    def setCameraPosition(self, pos):
        if pos == 'top': self.setCameraToTop()
        elif pos == 'bottom': self.setCameraToBottom()
        elif pos == 'front': self.setCameraToFront()
        elif pos == 'back': self.setCameraToBack()
        elif pos == 'left': self.setCameraToLeft()
        else: self.setCameraToRight()

    def hideAll(self, signal=True):
        super().hideAll(signal)
        self.setSlice0Visibility(False)
        self.setSlice1Visibility(False)
        self.setSlice2Visibility(False)
        self.setTextureVisibility(False)

    def showAll(self, signal=True):
        super().showAll(signal)
        self.setSlice0Visibility(True)
        self.setSlice1Visibility(True)
        self.setSlice2Visibility(True)
        self.setTextureVisibility(True)

    def getSeriesPixmapCaptures(self):
        caps = list()
        campos = ['top', 'bottom', 'front', 'back', 'left', 'right']
        for pos in campos:
            # Display current camera position capture
            self.setCameraPosition(pos)
            # Get current camera position capture
            c = vtkWindowToImageFilter()
            c.SetInput(self._renderwindow)
            r = vtkImageExportToArray()
            r.SetInputConnection(c.GetOutputPort())
            cap = r.GetArray()
            d, h, w, ch = cap.shape
            cap = QImage(cap.data, w, h, 3 * w, QImage.Format_RGB888)
            cap = cap.mirrored(False, True)
            caps.append(QPixmap.fromImage(cap))
        return caps

    def saveSeriesCapture(self):
        title = 'Save capture from multiple camera positions'
        name = QFileDialog.getSaveFileName(self, caption=title, directory=getcwd(),
                                           filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                           initialFilter='JPG (*.jpg)')[0]
        if name != '':
            campos = ['front', 'left', 'top', 'back', 'right', 'bottom']
            wait = DialogWait(title, title, progress=False, parent=self)
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
                QMessageBox.warning(self, title, '{}'.format(err))
            finally:
                wait.close()

    def saveSeriesCaptures(self):
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
                wait = DialogWait(title, title, progress=False, parent=self)
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
                        w.SetInputConnection(c.GetOutputPort())
                        w.SetFileName(slicename)
                        w.Write()
                except Exception as err:
                    QMessageBox.warning(self, title, '{}'.format(err))
                finally:
                    wait.close()

    # Public slices methods

    def sliceMinus(self):
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

    def slicePlus(self):
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

    def hideAllSlices(self):
        self.setSlice0Visibility(False)
        self.setSlice1Visibility(False)
        self.setSlice2Visibility(False)

    def showAllSlices(self):
        self.setSlice0Visibility(True)
        self.setSlice1Visibility(True)
        self.setSlice2Visibility(True)

    def setSlice0Visibility(self, v):
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice0.SetVisibility(v)
                self._action['showslice0'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setSlice1Visibility(self, v):
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice1.SetVisibility(v)
                self._action['showslice1'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setSlice2Visibility(self, v):
        if isinstance(v, bool):
            if self.hasVolume():
                self._slice2.SetVisibility(v)
                self._action['showslice2'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSlice0Visibility(self):
        self._slice0.GetVisibility()

    def getSlice1Visibility(self):
        self._slice1.GetVisibility()

    def getSlice2Visibility(self):
        self._slice2.GetVisibility()

    # Public texture methods

    def loadTransfer(self):
        if self.hasVolume():
            self._transfer.setDefault(self._volume)
            if self._volume.hasFilename():
                name, ext = splitext(self._volume.getFilename())
                name += self._transfer.getFileExt()
                if exists(name):
                    self._transfer.loadFromXML(name)

    def saveTransfer(self):
        if self.hasVolume():
            self._transfer.setID(self._volume.getArrayID())
            self._transfer.saveToXML(self._volume.getFilename())

    def getTransfer(self):
        return self._transfer

    def setTransfer(self, transfer):
        if isinstance(transfer, SisypheColorTransfer):
            self._transfer = transfer
            self._updateTextureTransfer()
        else: raise TypeError('parameter type {} is not SisypheColorTransfer.'.format(type(transfer)))

    def setGradientOpacity(self, v):
        prop = self._texture.GetProperty()
        prop.SetDisableGradientOpacity(int(not v))
        self._renderwindow.Render()

    def gradientOpacityOn(self):
        prop = self._texture.GetProperty()
        prop.DisableGradientOpacityOff()
        self._renderwindow.Render()

    def gradientOpacityOff(self):
        prop = self._texture.GetProperty()
        prop.DisableGradientOpacityOn()
        self._renderwindow.Render()

    def getGradientOpacity(self):
        prop = self._texture.GetProperty()
        return not bool(prop.GetDisableGradientOpacity())

    def setTextureVisibility(self, v):
        if isinstance(v, bool):
            if self.hasVolume():
                self._texture.SetVisibility(v)
                self._action['showtexture'].setChecked(v)
                self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getTextureVisibility(self):
        self._texture.GetVisibility()

    def getBlendMode(self):
        return self._texture.GetMapper().GetBlendMode()

    def getBlendModeAsString(self):
        return self._CODETOBLEND[self._texture.GetMapper().GetBlendMode()]

    def setBlendMode(self, k):
        if isinstance(k, str):
            k = self._BLENDTOCODE[k]
        if isinstance(k, int):
            self._texture.GetMapper().SetBlendMode(k)
            self._texture.Update()
            self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not int or str'.format(type(k)))

    def setBlendModeToComposite(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToComposite()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToMaximumIntensity(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToMaximumIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToMinimumIntensity(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToMinimumIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToAverageIntensity(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToAverageIntensity()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToAdditive(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToAdditive()
            self._texture.Update()
            self._renderwindow.Render()

    def setBlendModeToIsoSurface(self):
        if self.hasVolume():
            self._texture.GetMapper().SetBlendModeToIsoSurface()
            self._texture.Update()
            self._renderwindow.Render()

    def getCropping(self):
        return self._texture.GetMapper().GetCropping()

    def setCropping(self, v):
        if isinstance(v, bool):
            self._texture.GetMapper().SetCropping(v)
            self._renderwindow.Render()
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCroppingOn(self):
        self._texture.GetMapper().CroppingOn()
        self._renderwindow.Render()

    def setCroppingOff(self):
        self._texture.GetMapper().CroppingOff()
        self._renderwindow.Render()

    def cropTexture(self):
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

    def uncropTexture(self):
        self._croptag = 0x361B
        self._texture.GetMapper().SetCroppingRegionFlags(self._croptag)
        self.setCroppingOff()

    # Public openGL actor methods

    def hasSurfaceMesh(self):
        return 'OuterSurface' in self._mesh.keys()

    def setSurfaceVisibility(self, v):
        if isinstance(v, bool):
            if self.hasVolume():
                if not self.hasSurfaceMesh() and v: self._addOuterSurfaceMesh()
                if self.hasSurfaceMesh():
                    self._mesh['OuterSurface'].setVisibility(v)
                    self._action['showsurface'].setChecked(v)
                    self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getSurfaceVisibility(self):
        self._mesh['OuterSurface'].getVisibility()

    def editActorProperties(self):
        prop = self._getPickedActor()
        if prop:
            dialog = DialogMeshProperties()
            dialog.setProperties(prop.GetProperty())
            dialog.UpdateRender.connect(self._renderwindow.Render)
            dialog.show()
            dialog.activateWindow()

    # Private vtk events methods

    def _onRightPressEvent(self, obj, evt_name):
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
        menu.popup(p)

    def _onWheelForwardEvent(self,  obj, evt_name):
        if self.hasVolume():
            if self._interactor.GetKeySym() == 'Control_L':
                self.zoomOut()
            elif self._selectedSlice:
                self.slicePlus()

    def _onWheelBackwardEvent(self,  obj, evt_name):
        if self.hasVolume():
            if self._interactor.GetKeySym() == 'Control_L':
                self.zoomIn()
            elif self._selectedSlice:
                self.sliceMinus()

    def _onLeftPressEvent(self,  obj, evt_name):
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
            if n:
                prop = picker.GetViewProp()
                cname = prop.GetClassName()
                if cname == 'vtkImageSlice':
                    if prop == self._slice0:
                        self._selectedSlice = 1
                    elif prop == self._slice1:
                        self._selectedSlice = 2
                    else:
                        self._selectedSlice = 3
                    if k == 'Control_L':
                        x, y, z = picker.GetPickPosition()
                        self.setCursorWorldPosition(x, y, z, True)

    def _onLeftReleaseEvent(self,  obj, evt_name):
        if self.hasVolume():
            k = self._interactor.GetKeySym()
            if k == 'Alt_L' or self.getMoveFlag() is True:
                self._interactor.SetKeySym('')
                self.setCentralCrossVisibilityOff()
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)
                self._renderwindow.Render()
            elif k == 'Shift_L' or self.getLevelFlag() is True:
                self._interactor.SetKeySym('')

    def _onMiddlePressEvent(self, obj, evt_name):
        pass

    def _onMouseMoveEvent(self,  obj, evt_name):
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            last = interactorstyle.GetLastPos()
            k = self._interactor.GetKeySym()
            # Zoom, Control Key (Cmd key on mac)
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
                    # to do: replace with atan2
                    # anglex = degrees(atan2(d, dx)) * 5
                    # angley = degrees(atan2(d, dy)) * 5
                    anglex = degrees(atan(dx / d)) * 5
                    angley = degrees(atan(dy / d)) * 5
                    camera.Azimuth(anglex)
                    camera.Elevation(angley)
                    self._renderwindow.Render()
                    self.CameraChanged.emit(self)

    def _onKeyPressEvent(self,  obj, evt_name):
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

    def _onKeyReleaseEvent(self, obj, evt_name):
        self._interactor.SetKeySym('')
        interactorstyle = self._window.GetInteractorStyle()
        if interactorstyle.GetButton() == 1:
            self.setCentralCrossVisibilityOff()
            self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)


if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QWidget, QHBoxLayout, QApplication

    app = QApplication(argv)
    main = QWidget()
    print('Test volumeViewWidget')
    filename = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/3D.nii'
    img = SisypheVolume()
    img.identity.setLastname('lastname')
    img.identity.setFirstname('firstname')
    img.identity.setDateOfBirthday('2000-01-01')
    img.acquisition.setSequence('3D T1')
    img.loadFromNIFTI(filename)
    view = VolumeViewWidget()
    view.setVolume(img)
    layout = QHBoxLayout(main)
    layout.addWidget(view)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    main.activateWindow()
    exit(app.exec_())
