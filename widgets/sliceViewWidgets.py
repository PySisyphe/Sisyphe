"""
    External packages/modules

        Name            Homepage link                                               Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from os import mkdir
from os import getcwd
from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext

from math import pow
from math import sqrt
from math import atan2
from math import degrees
from math import radians

from numpy import ones
from numpy import zeros

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import GradientMagnitudeRecursiveGaussian

from vtk import vtkActor
from vtk import vtkFollower
from vtk import vtkCubeSource
from vtk import vtkLineSource
from vtk import vtkRegularPolygonSource
from vtk import vtkAppendPolyData
from vtk import vtkPolyDataMapper
from vtk import vtkImageSlice
from vtk import vtkImageStack
from vtk import vtkImageSliceMapper
from vtk import vtkImageResliceMapper
from vtk import vtkImageBlend
from vtk import vtkImageMapToColors
from vtk import vtkWindowToImageFilter
from vtk import vtkTransform
from vtk import vtkBMPWriter
from vtk import vtkJPEGWriter
from vtk import vtkPNGWriter
from vtk import vtkTIFFWriter
from vtk import VTK_CURSOR_HAND
from vtk import VTK_CURSOR_ARROW
from vtk import VTK_FONT_FILE
from vtk import vtkCommand
from vtk import vtkWidgetEvent

from Sisyphe.core.sisypheStatistics import tTopvalue
from Sisyphe.core.sisypheStatistics import zTopvalue
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROIDraw
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.toolWidgets import LineWidget
from Sisyphe.widgets.toolWidgets import HandleWidget
from Sisyphe.widgets.toolWidgets import BoxWidget
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy
    
        QFrame -> AbstractViewWidget -> SliceViewWidget -> SliceReorientViewWidget
                                                        -> SliceOverlayViewWidget -> SliceROIViewWidget
                                                                                  -> SliceRegistrationViewWidget
    Description
        
        Classes to display a single slice.
"""


class SliceViewWidget(AbstractViewWidget):
    """
        SliceViewWidget class

        Description

            Base class to display a slice.

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget

        Private attributes

            _volumeslice    vtkImageSlice instance, slice actor of the volume
            _stack          vtkImageStack instance, stack of reference (layer 0) and overlays (layer > 0) volumes
            _scale          float, default zoom factor
            _lineh          vtkLineSource, horizontal line of the cursor
            _linev          vtkLineSource, vertical line of the cursor
            _lines          vtkPolyData, cursor
            _slicenav       bool, slice navigation enable flag
            _scale0         float, zoom factor before event start
            _mousepos0      (float, float, float), mouse coordinate before event start
            _campos0        (float, float, float), camera coordinate before event start
            _camfocal0      float, focal depth before event start
            _cursor0        bool, cursor visibility before event start
            _win0           (float, float), mouse position of previous event
            _orient         int, plane orientation (0 axial, 1 coronal, 2 sagittal)
            _offset         int, current slice index = first slice index + offset in multiview tool
            _clipfactor     float, clipping before and after slice plane (distance = slice thickness x _clipfactor)

        Custom Qt signals

            TransformApplied.emit(QWidget, float, float, float, float, float, float)
            CameraPositionChanged.emit(QWidget, float, float, float)
            RenderUpdated.emit(QWidget)
            VisibilityChanged.emit(QWidget, bool)
            OpacityChanged.emit(QWidget, float)

        Public Qt event synchronisation methods

            synchroniseTransformApplied(QWidget, float, float, float, float, float, float)
            synchroniseCameraPositionChanged(QWidget, float, float, float)
            synchroniseRenderUpdated(QWidget)
            synchronisedOpacityChanged(QWidget, bool)
            synchronisedVisibilityChanged(QWidget, float)

        Public methods

            setClippingFactor(float)
            float = getClippingFactor()
            QMenu = getPopupOrientation()
            popupOrientationEnabled()
            popupOrientationDisabled()
            setVolumeOpacity(float)
            float = getVolumeOpacity()
            setVolumeVisibility(bool)
            setVolumeVisibilityOn()
            setVolumeVisibilityOff()
            bool = getVolumeVisibility()
            applyTransformToVolume(float, float, float, float, float, float)
            setAxialOrientation()
            setCoronalOrientation()
            setSagittalOrientation()
            setDim0Orientation()
            setDim1Orientation()
            setDim2Orientation()
            setOrientation(int)
            int = getOrientation()
            str = getOrientationAsString()
            bool = isCurrentOrientationIsotropic(float)
            setCameraPlanePosition(list, bool)
            setDefaultCursorPosition()
            setCursorFromDisplayPosition(int, int)
            updateCursorDepthFromFocal()
            setCursorVisibility(bool)
            setOrientationLabelsVisibility(bool)
            setOrientationLabelsVisibilityOn()
            setOrientationLabelsVisibilityOff()
            bool = getOrientationLabelsVisibility()
            setInfoValueVisibility(bool)
            setInfoValueVisibilityOn()
            setInfoValueVisibilityOff()
            bool = getInfoPositionVisibility()
            setRelativeACCoordinatesVisibility(bool)
            setRelativeACCoordinatesVisibilityOn()
            setRelativeACCoordinatesVisibilityOff()
            bool = getRelativeACCoordinatesVisibility()
            setRelativePCCoordinatesVisibility(bool)
            setRelativePCCoordinatesVisibilityOn()
            setRelativePCCoordinatesVisibilityOff()
            bool = getRelativePCCoordinatesVisibility()
            setRelativeACPCCoordinatesVisibility(bool)
            setRelativeACPCCoordinatesVisibilityOn()
            setRelativeACPCCoordinatesVisibilityOff()
            bool = getRelativeACPCCoordinatesVisibility()
            setFrameCoordinatesVisibility(bool)
            setFrameCoordinatesVisibilityOn()
            setFrameCoordinatesVisibilityOff()
            bool = getFrameCoordinatesVisibility()
            setICBMCoordinatesVisibility(bool)
            setICBMCoordinatesVisibilityOn()
            setICBMCoordinatesVisibilityOff()
            bool = getICBMCoordinatesVisibility()
            setOffset(float)
            float = getOffset()
            setSliceNavigationEnabled()
            setSliceNavigationDisabled()
            bool = isSliceNavigationEnabled()
            vtkImageSlice = getVtkImageSliceVolume()
            vtkPlane = getVtkPlane()
            float = getDistanceFromSliceToPoint([float, float, float])
            float = getDistanceFromSliceToTool(int | str | HandleWidget | LineWidget)
            saveSeriesCaptures(int)

            inherited AbstractViewWidget methods
            inherited QWidget methods

        Revisions:

            27/04/2023  _getInfoValuesText() method,
                        t-value and pvalue display for t-map
                        z-score and pvalue display for z-map
                        value x 100 for percent unit
                        label name display for LB modality
            10/09/2023  _updateCameraClipping() method bugfix
            15/09/2023  zoom bugfix for tool size update in zoomIn(), zoomOut(), zoomDefault(), setZoom() methods
    """

    # Class constants

    _ABSOLUTEDEPTH, _RELATIVEDEPTH = 0, 1
    _DIM0, _DIM1, _DIM2 = 0, 1, 2
    _AXIAL, _CORONAL, _SAGITTAL, = 1, 2, 3

    # Synchronisation signals

    TransformApplied = pyqtSignal(QWidget, float, float, float, float, float, float)
    CameraPositionChanged = pyqtSignal(QWidget, float, float, float)
    RenderUpdated = pyqtSignal(QWidget)
    VisibilityChanged = pyqtSignal(QWidget, bool)
    OpacityChanged = pyqtSignal(QWidget, float)

    # Special method

    def __init__(self, parent=None):
        self._orient = self._DIM0

        super().__init__(parent)

        self._volumeslice = None
        self._stack = None
        self._lineh = None
        self._linev = None
        self._lines = None
        self._slicenav = True
        self._clipfactor = 2.0

        # Interaction attributes

        self._scale0 = None     # scale before event start
        self._mousepos0 = None  # mouse position before event start
        self._campos0 = None    # camera position before event start
        self._camfocal0 = None  # camera focal point before event start
        self._cursor0 = None    # cursor position before event start
        self._win0 = None       # mouse position of previous event

        # Multiview attribute

        self._offset = 0        # current slice index = first slice index + offset in multiview tool

        # Init popup menu

        self._action['showorientation'] = QAction('Show orientation labels', self)
        self._action['showpos'] = QAction('Cursor world coordinates', self)
        self._action['showac'] = QAction('Coordinates relative to AC', self)
        self._action['showpc'] = QAction('Coordinates relative to PC', self)
        self._action['showacpc'] = QAction('Coordinates relative to mid AC-PC', self)
        self._action['showframe'] = QAction('Frame coordinates', self)
        self._action['showicbm'] = QAction('ICBM coordinates', self)
        self._action['showvalue'] = QAction('Voxel value at mouse position', self)

        self._action['showorientation'].setCheckable(True)
        self._action['showpos'].setCheckable(True)
        self._action['showac'].setCheckable(True)
        self._action['showpc'].setCheckable(True)
        self._action['showacpc'].setCheckable(True)
        self._action['showframe'].setCheckable(True)
        self._action['showicbm'].setCheckable(True)
        self._action['showvalue'].setCheckable(True)

        self._action['showorientation'].triggered.connect(
            lambda: self.setOrientationLabelsVisibility(self._action['showorientation'].isChecked()))
        self._action['showpos'].triggered.connect(
            lambda: self.setInfoPositionVisibility(self._action['showpos'].isChecked()))
        self._action['showac'].triggered.connect(
            lambda: self.setRelativeACCoordinatesVisibility(self._action['showac'].isChecked()))
        self._action['showpc'].triggered.connect(
            lambda: self.setRelativePCCoordinatesVisibility(self._action['showpc'].isChecked()))
        self._action['showacpc'].triggered.connect(
            lambda: self.setRelativeACPCCoordinatesVisibility(self._action['showacpc'].isChecked()))
        self._action['showframe'].triggered.connect(
            lambda: self.setFrameCoordinatesVisibility(self._action['showframe'].isChecked()))
        self._action['showicbm'].triggered.connect(
            lambda: self.setICBMCoordinatesVisibility(self._action['showicbm'].isChecked()))
        self._action['showvalue'].triggered.connect(
            lambda: self.setInfoValueVisibility(self._action['showvalue'].isChecked()))

        self._menuVisibility.insertAction(self._action['showmarker'], self._action['showorientation'])

        action = self._menuShape.menuAction()
        self._menuInformation.insertAction(action, self._action['showpos'])
        self._menuInformation.insertAction(action, self._action['showac'])
        self._menuInformation.insertAction(action, self._action['showpc'])
        self._menuInformation.insertAction(action, self._action['showacpc'])
        self._menuInformation.insertAction(action, self._action['showframe'])
        self._menuInformation.insertAction(action, self._action['showicbm'])
        self._menuInformation.insertAction(action, self._action['showvalue'])

        self._action['axial'] = QAction('Axial', self)
        self._action['coronal'] = QAction('Coronal', self)
        self._action['sagittal'] = QAction('Sagittal', self)
        self._action['axial'].setCheckable(True)
        self._action['coronal'].setCheckable(True)
        self._action['sagittal'].setCheckable(True)
        self._action['axial'].triggered.connect(self.setAxialOrientation)
        self._action['coronal'].triggered.connect(self.setCoronalOrientation)
        self._action['sagittal'].triggered.connect(self.setSagittalOrientation)
        self._group_orient = QActionGroup(self)
        self._group_orient.setExclusive(True)
        self._group_orient.addAction(self._action['axial'])
        self._group_orient.addAction(self._action['coronal'])
        self._group_orient.addAction(self._action['sagittal'])
        self._action['axial'].setChecked(True)
        self._menuOrientation = QMenu('Orientation', self._popup)
        self._menuOrientation.addAction(self._action['axial'])
        self._menuOrientation.addAction(self._action['coronal'])
        self._menuOrientation.addAction(self._action['sagittal'])
        self._popup.insertMenu(self._popup.actions()[1], self._menuOrientation)

        self._action['captureseries'] = QAction('Save captures from slice series...', self)
        self._action['captureseries'].triggered.connect(lambda dummy: self.saveSeriesCaptures())
        self._popup.addAction(self._action['captureseries'])

        self._initOrientationLabels()
        self._initSliceSettings()

        # Viewport tooltip

        self._tooltipstr = 'View controls:\n' \
                           '\tMouseWheel slices through image,\n' \
                           '\tUp or Left key to previous slice,\n' \
                           '\tDown or Right key to next slice,\n' \
                           '\tMouseWheel + Ctrl Key (Cmd Key mac os) to change zoom,\n' \
                           '\tUp or Left + Ctrl Key (Cmd Key mac os) to zoom out,\n' \
                           '\tDown or Right + Ctrl Key (Cmd Key mac os) to zoom in,\n' \
                           '\tLeft click to move cursor position,\n' \
                           '\tLeft click + Ctrl Key (Cmd Key mac os) and drag to change zoom,\n' \
                           '\tLeft click + Alt Key and drag to pan,\n' \
                           '\tLeft click + Shift Key and drag to change window/level,\n' \
                           '\tRight click + Ctrl Key (Cmd Key mac os) ' \
                           'or Middle click to display popup menu.'
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

    # Private methods

    def _initCursor(self):
        self._lineh = vtkLineSource()
        self._linev = vtkLineSource()
        self._lineh.SetPoint1(-500, 0, 1)
        self._lineh.SetPoint2(500, 0, 1)
        self._linev.SetPoint1(0, -500, 1)
        self._linev.SetPoint2(0, 500, 1)
        self._lines = vtkAppendPolyData()
        self._lines.AddInputConnection(self._lineh.GetOutputPort())
        self._lines.AddInputConnection(self._linev.GetOutputPort())
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(self._lines.GetOutputPort())
        self._cursor = vtkFollower()
        self._cursor.SetCamera(self._renderer.GetActiveCamera())
        self._cursor.SetMapper(mapper)
        self._cursor.GetProperty().SetLineWidth(self._lwidth)
        self._cursor.GetProperty().SetColor(self._lcolor[0], self._lcolor[1], self._lcolor[2])
        self._cursor.GetProperty().SetOpacity(self._lalpha)
        self._cursor.SetVisibility(False)
        self._renderer.AddActor(self._cursor)

    def _addSlice(self, volume, alpha):
        mapper = vtkImageResliceMapper()
        mapper.BorderOff()
        mapper.SliceAtFocalPointOn()
        mapper.SliceFacesCameraOn()
        mapper.SetInputData(volume.getVTKImage())
        slc = vtkImageSlice()
        slc.SetMapper(mapper)
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._stack.AddImage(slc)
        return slc

    def _updateCameraOrientation(self):
        p = self._getRoundedCoordinate(self._stack.GetMapper().GetCenter())
        p = self._getRoundedCoordinate(p)
        camera = self._renderer.GetActiveCamera()
        if self._scale is None:
            self._renderer.ResetCamera()
            self.zoomDefault()
            self._scale = camera.GetParallelScale()
            self.setCursorWorldPosition(p[0], p[1], p[2])
        if self._orient == self._DIM0:
            camera.SetViewUp(0, 1, 0)
            camera.SetPosition(p[0], p[1], -500)
            self._info['topcenter'].SetInput('\n\nA')
            self._info['bottomcenter'].SetInput('P\n\n')
            self._info['leftcenter'].SetInput('L')
            self._info['rightcenter'].SetInput('R')
        elif self._orient == self._DIM1:
            camera.SetViewUp(0, 0, 1)
            camera.SetPosition(p[0], 500, p[2])
            self._info['topcenter'].SetInput('\n\nT')
            self._info['bottomcenter'].SetInput('B\n\n')
            self._info['leftcenter'].SetInput('L')
            self._info['rightcenter'].SetInput('R')
        else:
            camera.SetViewUp(0, 0, 1)
            camera.SetPosition(-500, p[1], p[2])
            self._info['topcenter'].SetInput('\n\nT')
            self._info['bottomcenter'].SetInput('B\n\n')
            self._info['leftcenter'].SetInput('P')
            self._info['rightcenter'].SetInput('A')
        self._setCameraFocalDepth(p, signal=False)
        self._updateRuler(signal=False)
        self._renderwindow.Render()

    def _setCameraFocalDepth(self, p, signal=True):
        camera = self._renderer.GetActiveCamera()
        d = 2 - self._orient
        s = self._volume.getSpacing()[d]
        offset = s * self._offset
        if isinstance(p, (list, tuple)):
            # p = (x, y, z) absolute world coordinate of the vtkCamera focal point
            # no synchronisation because call from initialisation step or synchronisation event
            p = list(p)
            if self._roundedenabled:
                # p[d] = round(p[d] / s) * s + offset
                p[d] = int(p[d] / s) * s + offset
            else: p[d] = p[d] + offset
            camera.SetFocalPoint(p)
            self.updateCursorDepthFromFocal()
        elif isinstance(p, int):
            f = list(camera.GetFocalPoint())
            cmax = self._volume.getSize()[d] * s + offset
            cmin = - offset
            # relative step = p * slice thickness
            f[d] += p * s
            if f[d] < cmin: f[d] = cmin
            elif f[d] > cmax: f[d] = cmax
            camera.SetFocalPoint(f)
            self.updateCursorDepthFromFocal()
            # synchronisation
            if self.isSynchronised() and signal:
                p = self.getCursorWorldPosition()
                self.CursorPositionChanged.emit(self, p[0], p[1], p[2])
        else: raise TypeError('parameter type {} is not list, tuple or int.'.format(type(p)))
        self._updateCameraClipping()
        # Tools display
        if self._tools.count() > 0:
            for tool in self._tools:
                if isinstance(tool, (HandleWidget, LineWidget)):
                    tool.updateContourActor(self._volumeslice.GetMapper().GetSlicePlane())
        self._updateBottomRightInfo()

    def _updateCameraClipping(self):
        # clipping distance
        # near = slice distance to camera - (slice thickness * _clipfactor)
        # far = slice distance to camera + (slice thickness * _clipfactor)
        camera = self._renderer.GetActiveCamera()
        d = camera.GetDistance()
        n = self._clipfactor * self.getVolume().getSpacing()[2 - self._orient]
        camera.SetClippingRange(d - n, d + n)

    def _initSliceSettings(self):
        """
            Settings -> actions
        """
        # Voxel value
        v = self._settings.getFieldValue('Viewport', 'VoxelValueVisibility')
        if v is None: v = False
        self._action['showvalue'].setChecked(v)
        # World coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorWorldVisibility')
        if v is None: v = True
        self._action['showpos'].setChecked(v)
        # AC relative coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorACVisibility')
        if v is None: v = False
        self._action['showac'].setChecked(v)
        # PC relative coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorPCVisibility')
        if v is None: v = False
        self._action['showpc'].setChecked(v)
        # Mid AC-PC coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorACPCVisibility')
        if v is None: v = False
        self._action['showacpc'].setChecked(v)
        # Stereotactic frame coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorFrameVisibility')
        if v is None: v = False
        self._action['showframe'].setChecked(v)
        # ICBM coordinates
        v = self._settings.getFieldValue('Viewport', 'CoorICBMVisibility')
        if v is None: v = False
        self._action['showicbm'].setChecked(v)
        # Orientation labels
        v = self._settings.getFieldValue('Viewport', 'OrientationLabelsVisibility')
        if v is None: v = False
        self._action['showorientation'].setChecked(v)

    def _initOrientationLabels(self):
        # Top
        info = self._info['topcenter']
        prop = info.GetTextProperty()
        if self._ffamily in ('Arial', 'Courier', 'Times'):
            prop.SetFontFamilyAsString(self._ffamily)
        else:
            prop.SetFontFamily(VTK_FONT_FILE)
            prop.SetFontFile(self._ffamily)
        prop.SetFontSize(self._fsize)
        prop.SetColor(self._lcolor)
        prop.SetOpacity(self._lalpha)
        prop.SetJustificationToCentered()
        prop.SetVerticalJustificationToTop()
        info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        info.SetPosition(0.5, 0.99)
        info.SetInput('\n\nA')
        info.SetVisibility(False)
        # Bottom
        info = self._info['bottomcenter']
        prop = info.GetTextProperty()
        if self._ffamily in ('Arial', 'Courier', 'Times'):
            prop.SetFontFamilyAsString(self._ffamily)
        else:
            prop.SetFontFamily(VTK_FONT_FILE)
            prop.SetFontFile(self._ffamily)
        prop.SetFontSize(self._fsize)
        prop.SetColor(self._lcolor)
        prop.SetOpacity(self._lalpha)
        prop.SetJustificationToCentered()
        prop.SetVerticalJustificationToBottom()
        info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        info.SetPosition(0.5, 0.01)
        info.SetInput('P\n\n')
        info.SetVisibility(False)
        # Left
        info = self._info['leftcenter']
        prop = info.GetTextProperty()
        if self._ffamily in ('Arial', 'Courier', 'Times'):
            prop.SetFontFamilyAsString(self._ffamily)
        else:
            prop.SetFontFamily(VTK_FONT_FILE)
            prop.SetFontFile(self._ffamily)
        prop.SetFontSize(self._fsize)
        prop.SetColor(self._lcolor)
        prop.SetOpacity(self._lalpha)
        prop.SetJustificationToRight()
        prop.SetVerticalJustificationToCentered()
        info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        info.SetPosition(0.95, 0.5)
        info.SetInput('L')
        info.SetVisibility(False)
        # Right
        info = self._info['rightcenter']
        prop = info.GetTextProperty()
        if self._ffamily in ('Arial', 'Courier', 'Times'):
            prop.SetFontFamilyAsString(self._ffamily)
        else:
            prop.SetFontFamily(VTK_FONT_FILE)
            prop.SetFontFile(self._ffamily)
        prop.SetFontSize(self._fsize)
        prop.SetColor(self._lcolor)
        prop.SetOpacity(self._lalpha)
        prop.SetJustificationToLeft()
        prop.SetVerticalJustificationToCentered()
        info.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        info.SetPosition(0.05, 0.5)
        info.SetInput('R')
        info.SetVisibility(False)

    def _getInfoValuesText(self, p):
        txt = ''
        if self.getInfoValueVisibility():
            x, y, z = p[0], p[1], p[2]
            s = self._volume.getSize()
            v = self._volume.getSpacing()
            x = int(x / v[0])
            y = int(y / v[1])
            z = int(z / v[2])
            if not (0 <= x < s[0]): return txt
            if not (0 <= y < s[1]): return txt
            if not (0 <= z < s[2]): return txt
            u = self._volume.getAcquisition().getUnit()
            acq = self._volume.getAcquisition()
            if u == 'No': u = ''
            if u == '%':
                val = 'Value: {:.1f} {} '.format(self._volume[x, y, z] * 100.0, u)
            elif acq.isOT():
                if acq.isTMap():
                    if u == 't-statistic':
                        v = self._volume[x, y, z]
                        f = acq.getDegreesOfFreedom()
                        p = tTopvalue(v, f)
                        val = 't-value: {:.1f} p-value: {:.2g} '.format(v, p)
                elif acq.isZMap():
                    if u == 'z-score':
                        v = self._volume[x, y, z]
                        p = zTopvalue(v)
                        val = 'z-score: {:.2g} p-value: {:.2g} '.format(v, p)
                else: val = 'Value: {} {} '.format(self._volume[x, y, z], u)
            elif acq.isLB():
                v = self._volume[x, y, z]
                label = self._volume.getAcquisition().getLabel(v)
                val = 'Value: {} Label: {} '.format(v, label)
            elif self._volume.isIntegerDatatype():
                val = 'Value: {} {} '.format(self._volume[x, y, z], u)
            else:
                m = abs(self._volume.getDisplay().getRangeMax())
                if m > 10: val = 'Value: {:.1f} {} '.format(self._volume[x, y, z], u)
                elif m > 1: val = 'Value: {:.2f} {} '.format(self._volume[x, y, z], u)
                else: val = 'Value: {:.2g} {} '.format(self._volume[x, y, z], u)
            txt = '\n{} voxel {} x {} x {}'.format(val, x, y, z)
        acpc = self._volume.getACPC()
        if self.getRelativeACCoordinatesVisibility():
            p2 = acpc.getRelativeDistanceFromAC(p)
            txt += '\nAC reference LAT {:.1f} AP {:.1f} H {:.1f}'.format(p2[0], p2[1], p2[2])
        if self.getRelativePCCoordinatesVisibility():
            p2 = acpc.getACPC().getRelativeDistanceFromPC(p)
            txt += '\nPC reference LAT {:.1f} AP {:.1f} H {:.1f}'.format(p2[0], p2[1], p2[2])
        if self.getRelativeACPCCoordinatesVisibility():
            p2 = acpc.getRelativeDistanceFromACPC(p)
            txt += '\nMid AC-PC reference LAT {:.1f} AP {:.1f} H {:.1f}'.format(p2[0], p2[1], p2[2])
        if self.getFrameCoordinatesVisibility():
            p2 = self._volume.getLEKSELLfromWorld(p)
            txt += '\nLeksell {:.1f} x {:.1f} x {:.1f}'.format(p2[0], p2[1], p2[2])
        if self.getICBMCoordinatesVisibility():
            p2 = self._volume.getICBMfromWorld(p)
            txt += '\nICBM {:.1f} x {:.1f} x {:.1f}'.format(p2[0], p2[1], p2[2])
        return txt

    def _updateBottomRightInfo(self):
        interactorstyle = self._window.GetInteractorStyle()
        p = interactorstyle.GetLastPos()
        p = list(self._getWorldFromDisplay(p[0], p[1]))
        txt = ''
        if self.getInfoPositionVisibility():
            d = 2 - self._orient
            p[d] = self._renderer.GetActiveCamera().GetFocalPoint()[d]
            x, y, z = p[0], p[1], p[2]
            xm, ym, zm = self._volume.getFieldOfView()
            if (0 <= x <= xm) and (0 <= y <= ym) and (0 <= z <= zm):
                o = self._volume.getOrigin()
                x -= o[0]
                y -= o[1]
                z -= o[2]
                txt = '{:.1f} x {:.1f} x {:.1f} mm'.format(x, y, z)
        txt = txt + self._getInfoValuesText(p)
        self.getBottomRightInfo().SetInput(txt)
        self._renderwindow.Render()

    # Public synchronisation event methods

    def synchroniseTransformApplied(self, obj, tx, ty, tz, rx, ry, rz):
        if self != obj and self.hasVolume():
            self.applyTransform(tx, ty, tz, rx, ry, rz, signal=False)

    def synchroniseCameraPositionChanged(self, obj, x, y, z):
        if self != obj and self.hasVolume():
            if self.getOrientation() == obj.getOrientation():
                self.setCameraPlanePosition([x, y, z], signal=False)

    def synchroniseRenderUpdated(self, obj):
        if self != obj and self.hasVolume():
            self._renderwindow.Render()

    def synchronisedOpacityChanged(self, obj, alpha):
        if self != obj and self.hasVolume():
            self.setVolumeOpacity(alpha, signal=False)

    def synchronisedVisibilityChanged(self, obj, v):
        if self != obj and self.hasVolume():
            self.setVolumeVisibility(v, signal=False)

    # Public methods

    def setClippingFactor(self, v: float = 2.0):
        if isinstance(v, float):
            self._clipfactor = v
            self._updateCameraClipping()
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getClippingFactor(self) -> float:
        return self._clipfactor

    def displayOn(self):
        if self._volume is not None:
            # Info
            self._info['bottomright'].SetVisibility(
                self._action['showinfo'].isChecked() and self._action['showpos'].isChecked())
            v = self._volume.getACPC().hasACPC()
            self._action['showac'].setVisible(v)
            self._action['showpc'].setVisible(v)
            self._action['showacpc'].setVisible(v)
            self._action['showicbm'].setVisible(self._volume.hasICBMTransform())
            self._action['showframe'].setVisible(self._volume.hasLEKSELLTransform())
            # Orientation labels
            self._info['topcenter'].SetVisibility(self._action['showorientation'].isChecked())
            self._info['leftcenter'].SetVisibility(self._action['showorientation'].isChecked())
            self._info['rightcenter'].SetVisibility(self._action['showorientation'].isChecked())
            self._info['bottomcenter'].SetVisibility(self._action['showorientation'].isChecked())
            super().displayOn()

    def displayOff(self):
        self._action['showac'].setVisible(False)
        self._action['showpc'].setVisible(False)
        self._action['showacpc'].setVisible(False)
        self._action['showicbm'].setVisible(False)
        self._action['showframe'].setVisible(False)
        # Orientation labels
        self._info['topcenter'].SetVisibility(False)
        self._info['leftcenter'].SetVisibility(False)
        self._info['rightcenter'].SetVisibility(False)
        self._info['bottomcenter'].SetVisibility(False)
        # Ruler
        self._ruler.SetVisibility(False)
        super().displayOff()

    def getPopupOrientation(self):
        return self._menuOrientation

    def popupOrientationEnabled(self):
        self._menuOrientation.menuAction().setVisible(True)

    def popupOrientationDisabled(self):
        self._menuOrientation.menuAction().setVisible(False)

    def setVolume(self, volume):
        super().setVolume(volume)
        if self._stack is not None:
            self._renderer.RemoveActor(self._stack)
            del self._stack
            del self._volumeslice
            self._scale = None
            self._volumeslice = None
        self._stack = vtkImageStack()
        self._stack.SetActiveLayer(0)
        self._volumeslice = self._addSlice(volume, 1.0)
        self._volumeslice.GetProperty().SetLayerNumber(0)
        self._renderer.AddViewProp(self._stack)
        self._stack.VisibilityOn()
        self._updateCameraOrientation()
        p = self._renderer.GetActiveCamera().GetFocalPoint()
        self.setCursorWorldPosition(p[0], p[1], p[2])
        self._renderwindow.Render()

    def removeVolume(self):
        if self.hasVolume():
            if self._stack is not None:
                self._renderer.RemoveActor(self._stack)
                del self._stack
                del self._volumeslice
                self._stack = None
                self._volumeslice = None
        super().removeVolume()

    def setVolumeOpacity(self, alpha, signal=True):
        if isinstance(alpha, float):
            if self.hasVolume():
                self._volumeslice.GetProperty().SetOpacity(alpha)
                if signal: self.OpacityChanged.emit(self, alpha)
            else: raise AttributeError('No volume')
        else: raise TypeError('parameter type {} is not float.'.format(type(alpha)))

    def getVolumeOpacity(self):
        if self.hasVolume(): self._volumeslice.GetProperty().GetOpacity()
        else: raise AttributeError('No volume')

    def setVolumeVisibility(self, v, signal=True):
        if isinstance(v, bool):
            if self.hasVolume():
                self._volumeslice.SetVisibility(v)
                if signal: self.VisibilityChanged.emit(self, v)
            else: raise AttributeError('No volume')
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVolumeVisibilityOn(self):
        self.setVolumeVisibility(True)

    def setVolumeVisibilityOff(self):
        self.setVolumeVisibility(False)

    def getVolumeVisibility(self):
        if self.hasVolume(): self._volumeslice.GetProperty().GetVisibility()
        else: raise AttributeError('No volume')

    def applyTransformToVolume(self, tx, ty, tz, rx, ry, rz, signal=True):
        if self.hasVolume():
            self._volumeslice.SetOrigin(self._volume.getCenter())
            self._volumeslice.SetPosition(tx, ty, tz)
            self._volumeslice.SetOrientation(rx, ry, rz)
            self._volume.getVTKImage().Modified()
            self._renderwindow.Render()
            if signal: self.TransformApplied.emit(self, tx, ty, tz, rx, ry, rz)

    def setAxialOrientation(self):
        if self._volume.getOrientation() == self._AXIAL: self.setDim0Orientation()
        elif self._volume.getOrientation() == self._CORONAL: self.setDim1Orientation()
        else: self.setDim2Orientation()
        self._action['axial'].setChecked(True)

    def setCoronalOrientation(self):
        if self._volume.getOrientation() == self._AXIAL: self.setDim1Orientation()
        elif self._volume.getOrientation() == self._CORONAL: self.setDim0Orientation()
        else: self.setDim2Orientation()
        self._action['coronal'].setChecked(True)

    def setSagittalOrientation(self):
        if self._volume.getOrientation() == self._AXIAL: self.setDim2Orientation()
        elif self._volume.getOrientation() == self._CORONAL: self.setDim1Orientation()
        else: self.setDim0Orientation()
        self._action['sagittal'].setChecked(True)

    def setDim0Orientation(self):
        self._orient = self._DIM0
        self._updateCameraOrientation()

    def setDim1Orientation(self):
        self._orient = self._DIM1
        self._updateCameraOrientation()

    def setDim2Orientation(self):
        self._orient = self._DIM2
        self._updateCameraOrientation()

    def setOrientation(self, orient):
        if isinstance(orient, int):
            if 0 <= orient < 3:
                self._orient = orient
                if orient == 0: self._action['axial'].setChecked(True)
                elif orient == 1: self._action['coronal'].setChecked(True)
                else: self._action['sagittal'].setChecked(True)
                self._updateCameraOrientation()
            else: raise ValueError('parameter value is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(orient)))

    def getOrientation(self):
        return self._orient

    def getOrientationAsString(self):
        if self._volume.getOrientation() == self._AXIAL:
            if self._orient == self._DIM0: return 'axial'
            elif self._orient == self._DIM1: return 'coronal'
            else: return 'sagittal'
        elif self._volume.getOrientation() == self._CORONAL:
            if self._orient == self._DIM0: return 'coronal'
            elif self._orient == self._DIM1: return 'axial'
            else: return 'sagittal'
        else:
            if self._orient == self._DIM0: return 'sagittal'
            elif self._orient == self._DIM1: return 'axial'
            else: return 'coronal'

    def isCurrentOrientationIsotropic(self, tol=0.25):
        if isinstance(tol, float):
            tolsup = 1 + tol
            tolinf = 1 - tol
            s = self._volume.getSpacing()
            if self._orient == self._DIM0:
                return tolinf <= (s[1] / s[0]) <= tolsup
            elif self._orient == self._DIM1:
                return tolinf <= (s[2] / s[0]) <= tolsup
            else:
                return tolinf <= (s[1] / s[2]) <= tolsup
        else:
            raise TypeError('parameter functype is not float.')

    def setCameraPlanePosition(self, p, signal=True):
        if isinstance(p, (list, tuple)):
            camera = self._renderer.GetActiveCamera()
            s = self._volume.getSpacing()
            c = list(camera.GetPosition())
            f = list(camera.GetFocalPoint())
            if self._orient == self._DIM0:
                # c[0] = f[0] = round(p[0] / s[0]) * s[0]
                # c[1] = f[1] = round(p[1] / s[1]) * s[1]
                c[0] = f[0] = int(p[0] / s[0]) * s[0]
                c[1] = f[1] = int(p[1] / s[1]) * s[1]
            elif self._orient == self._DIM1:
                # c[0] = f[0] = round(p[0] / s[0]) * s[0]
                # c[2] = f[2] = round(p[2] / s[2]) * s[2]
                c[0] = f[0] = int(p[0] / s[0]) * s[0]
                c[2] = f[2] = int(p[2] / s[2]) * s[2]
            else:
                # c[1] = f[1] = round(p[1] / s[1]) * s[1]
                # c[2] = f[2] = round(p[2] / s[2]) * s[2]
                c[1] = f[1] = int(p[1] / s[1]) * s[1]
                c[2] = f[2] = int(p[2] / s[2]) * s[2]
            camera.SetPosition(c)
            camera.SetFocalPoint(f)
            self._updateBottomRightInfo()
            # synchronisation
            if self.isSynchronised() and signal:
                self.CameraPositionChanged.emit(self, p[0], p[1], p[2])
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def setDefaultCursorPosition(self):
        p = self._renderer.GetActiveCamera().GetFocalPoint()
        self.setCursorWorldPosition(p[0], p[1], p[2])

    def setCursorFromDisplayPosition(self, x, y):
        p = list(self._getWorldFromDisplay(x, y))
        f = self._renderer.GetActiveCamera().GetFocalPoint()
        d = 2 - self._orient
        s = self._volume.getSpacing()[d]
        offset = self._offset * s
        p[d] = f[d] - offset
        p = self._getRoundedCoordinate(p)
        # cursor depth = focal depth - offset
        self.setCursorWorldPosition(p[0], p[1], p[2], signal=False)
        # self._cursor.SetPosition(p)
        self._renderwindow.Render()

    def setCursorWorldPosition(self, x, y, z, signal=True):
        if self._volume is not None:
            super().setCursorWorldPosition(x, y, z, signal)
            p = self.getCursorWorldPosition()  # Rounded coordinates
            f = list(self._renderer.GetActiveCamera().GetFocalPoint())
            d = 2 - self._orient
            f[d] = p[d]
            self._setCameraFocalDepth(f, signal=False)

    def updateCursorDepthFromFocal(self):
        p = list(self._cursor.GetPosition())
        f = self._renderer.GetActiveCamera().GetFocalPoint()
        d = 2 - self._orient
        s = self._volume.getSpacing()[d]
        offset = self._offset * s
        p[d] = f[d] - offset
        self._cursor.SetPosition(p)  # cursor depth = focal depth - offset

    def setCursorVisibility(self, v, signal=True):
        if self._offset > 0: v = False
        super().setCursorVisibility(v, signal)

    def setOrientationLabelsVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._info['topcenter'].SetVisibility(v)
            self._info['leftcenter'].SetVisibility(v)
            self._info['rightcenter'].SetVisibility(v)
            self._info['bottomcenter'].SetVisibility(v)
            self._action['showorientation'].setChecked(v)
            self._renderwindow.Render()
            if signal: self.ViewMethodCalled.emit(self, 'setOrientationLabelsVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setOrientationLabelsVisibilityOn(self, signal=True):
        self.setOrientationLabelsVisibility(True, signal)

    def setOrientationLabelsVisibilityOff(self, signal=True):
        self.setOrientationLabelsVisibility(False, signal)

    def getOrientationLabelsVisibility(self):
        return self._action['showorientation'].isChecked()

    def setInfoValueVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showvalue'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setInfoValueVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoValueVisibilityOn(self, signal=True):
        self.setInfoValueVisibility(True, signal)

    def setInfoValueVisibilityOff(self, signal=True):
        self.setInfoValueVisibility(False, signal)

    def getInfoValueVisibility(self):
        return self._action['showvalue'].isChecked()

    def setInfoPositionVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showpos'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setInfoPositionVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoPositionVisibilityOn(self, signal=True):
        self.setInfoVisibility(True, signal)

    def setInfoPositionVisibilityOff(self, signal=True):
        self.setInfoVisibility(False, signal)

    def getInfoPositionVisibility(self):
        return self._action['showpos'].isChecked()

    def setRelativeACCoordinatesVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showac'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setRelativeACCoordinatesVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRelativeACCoordinatesVisibilityOn(self, signal=True):
        self.setRelativeACCoordinatesVisibility(True, signal)

    def setRelativeACCoordinatesVisibilityOff(self, signal=True):
        self.setRelativeACCoordinatesVisibility(False, signal)

    def getRelativeACCoordinatesVisibility(self):
        return self._action['showac'].isChecked()

    def setRelativePCCoordinatesVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showpc'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setRelativePCCoordinatesVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRelativePCCoordinatesVisibilityOn(self, signal=True):
        self.setRelativePCCoordinatesVisibility(True, signal)

    def setRelativePCCoordinatesVisibilityOff(self, signal=True):
        self.setRelativePCCoordinatesVisibility(False, signal)

    def getRelativePCCoordinatesVisibility(self):
        return self._action['showpc'].isChecked()

    def setRelativeACPCCoordinatesVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showacpc'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setRelativeACPCCoordinatesVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRelativeACPCCoordinatesVisibilityOn(self, signal=True):
        self.setRelativeACPCCoordinatesVisibility(True, signal)

    def setRelativeACPCCoordinatesVisibilityOff(self, signal=True):
        self.setRelativeACPCCoordinatesVisibility(False, signal)

    def getRelativeACPCCoordinatesVisibility(self):
        return self._action['showacpc'].isChecked()

    def setFrameCoordinatesVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showframe'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setFrameCoordinatesVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setFrameCoordinatesVisibilityOn(self, signal=True):
        self.setFrameCoordinatesVisibility(True, signal)

    def setFrameCoordinatesVisibilityOff(self, signal=True):
        self.setFrameCoordinatesVisibility(False, signal)

    def getFrameCoordinatesVisibility(self):
        return self._action['showframe'].isChecked()

    def setICBMCoordinatesVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['showicbm'].setChecked(v)
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setICBMCoordinatesVisibility', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setICBMCoordinatesVisibilityOn(self, signal=True):
        self.setICBMCoordinatesVisibility(True, signal)

    def setICBMCoordinatesVisibilityOff(self, signal=True):
        self.setICBMCoordinatesVisibility(False, signal)

    def getICBMCoordinatesVisibility(self):
        return self._action['showicbm'].isChecked()

    def setOffset(self, v=0):
        if isinstance(v, int):
            self._offset = v
            if self._offset != 0:
                self.setCursorVisibilityOff()
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getOffset(self):
        return self._offset

    def sliceMinus(self):
        if self._slicenav: self._setCameraFocalDepth(-1)

    def slicePlus(self):
        if self._slicenav: self._setCameraFocalDepth(1)

    def setSliceNavigationEnabled(self):
        self._slicenav = True

    def setSliceNavigationDisabled(self):
        self._slicenav = False

    def isSliceNavigationEnabled(self):
        return self._slicenav is True

    def getVtkImageSliceVolume(self):
        return self._volumeslice

    def getVtkPlane(self):
        return self._volumeslice.GetMapper().GetSlicePlane()

    def getDistanceFromSliceToPoint(self, p):
        if isinstance(p, (list, tuple)):
            if len(p) == 3 and all([isinstance(i, float) for i in p]):
                plane = self.getVtkPlane()
                return plane.DistanceToPlane(p)
            else: raise TypeError('invalid list/tuple item count or item type is not float.')
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getDistanceFromSliceToTool(self, key):
        r = list()
        if isinstance(key, (int, str)):
            if key in self._tools:
                key = self._tools[key]
        if isinstance(key, (HandleWidget, LineWidget)):
            plane = self.getVtkPlane()
            if isinstance(key, HandleWidget):
                r.append(plane.DistanceToPlane(key.getPosition()))
            elif isinstance(key, LineWidget):
                r.append(plane.DistanceToPlane(key.getPosition1()))
                r.append(plane.DistanceToPlane(key.getPosition2()))
        return r

    def saveSeriesCaptures(self, step=2):
        if self.hasVolume():
            title = 'Save all slices capture'
            name = QFileDialog.getSaveFileName(self, caption=title, directory=getcwd(),
                                               filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                               initialFilter='JPG (*.jpg)')[0]
            if name != '':
                # Create directory
                path, ext = splitext(name)
                mkdir(path)
                # Number of slices to capture
                d = 2 - self._orient
                step = step * self._volume.getSpacing()[d]
                offset = self._offset * self._volume.getSpacing()[d]
                fov = self._volume.getFieldOfView()
                n = int(fov[d] // step)
                name = basename(path)
                w = {'.bmp': vtkBMPWriter(), '.jpg': vtkJPEGWriter(),
                     '.png': vtkPNGWriter(), '.tiff': vtkTIFFWriter()}
                w = w[ext]
                wait = DialogWait(title, title, progress=True, progressmin=0, progressmax=n, parent=self)
                wait.open()
                try:
                    camera = self._renderer.GetActiveCamera()
                    f0 = list(camera.GetFocalPoint())
                    for i in range(0, n-1):
                        # Display current slice
                        f = list(camera.GetFocalPoint())
                        f[d] = - offset + i * step
                        self._setCameraFocalDepth(f)
                        # Get current slice capture
                        suffix = '00{}'.format(i)[-3:]
                        slicename = join(path, '{}_{}{}'.format(name, suffix, ext))
                        wait.setInformationText('Save {} capture.'.format(basename(slicename)))
                        wait.incCurrentProgressValue()
                        c = vtkWindowToImageFilter()
                        c.SetInput(self._renderwindow)
                        # Save current slice capture
                        w.SetInputConnection(c.GetOutputPort())
                        w.SetFileName(slicename)
                        w.Write()
                except Exception as err:
                    QMessageBox.warning(self, title, '{}'.format(err))
                finally:
                    wait.close()
                    self._setCameraFocalDepth(f0)

    # Private vtk event methods

    def _onWheelForwardEvent(self,  obj, evt_name):
        super()._onWheelForwardEvent(obj, evt_name)
        if self.hasVolume():
            # if interactorstyle.GetKeySym() == 'Control_L': self.zoomOut()
            if self._interactor.GetControlKey(): self.zoomOut()
            else: self.sliceMinus()

    def _onWheelBackwardEvent(self,  obj, evt_name):
        super()._onWheelBackwardEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            # if interactorstyle.GetKeySym() == 'Control_L': self.zoomIn()
            if self._interactor.GetControlKey(): self.zoomIn()
            else: self.slicePlus()

    def _onLeftPressEvent(self,  obj, evt_name):
        super()._onLeftPressEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            self._mousepos0 = interactorstyle.GetLastPos()
            # k = interactorstyle.GetKeySym()
            # Zoom, Control Key (Cmd key on mac)
            # if k == 'Control_L' or self.getZoomFlag() is True:
            if self._interactor.GetControlKey() or self.getZoomFlag() is True:
                self._scale0 = self._renderer.GetActiveCamera().GetParallelScale()
            # Pan, Alt Key
            # elif k == 'Alt_L' or self.getMoveFlag() is True:
            elif self._interactor.GetKeySym() == 'Alt_L' or self.getMoveFlag() is True:
                self._camfocal0 = self._renderer.GetActiveCamera().GetFocalPoint()
                self._campos0 = self._renderer.GetActiveCamera().GetPosition()
                self.setCentralCrossVisibilityOn()
                self._cursor0 = self.getCursorVisibility()
                self.setCursorVisibilityOff()
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_HAND)
            # Windowing, Shift Key
            # elif k == 'Shift_L' or self.getLevelFlag() is True:
            elif self._interactor.GetShiftKey() or self.getLevelFlag() is True:
                self._cursor0 = self.getCursorVisibility()
                self.setCursorVisibilityOff()
                self._win0 = interactorstyle.GetLastPos()
            else:
                # Update cursor position
                self.setCursorFromDisplayPosition(self._mousepos0[0], self._mousepos0[1])
                p = self.getCursorWorldPosition()
                self.CursorPositionChanged.emit(self, p[0], p[1], p[2])  # 3D position corrected by offset
            # Display information
            self._updateBottomRightInfo()

    def _onMiddlePressEvent(self, obj, evt_name):
        super()._onMiddlePressEvent(obj, evt_name)

    def _onMouseMoveEvent(self,  obj, evt_name):
        super()._onMouseMoveEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            last = interactorstyle.GetLastPos()
            # k = interactorstyle.GetKeySym()
            # Zoom, Control Key (Cmd key on mac)
            # if k == 'Control_L' or self.getZoomFlag() is True:
            if self._interactor.GetControlKey() or self.getZoomFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Zoom
                    dx = (last[1] - self._mousepos0[1]) / 10
                    if dx < 0: self.zoomIn()
                    else: self.zoomOut()
            # Pan, Alt Key
            # elif k == 'Alt_L' or self.getMoveFlag() is True:
            elif self._interactor.GetKeySym() == 'Alt_L' or self.getMoveFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Camera and focal position
                    pfirst = self._getWorldFromDisplay(self._mousepos0[0],  self._mousepos0[1])
                    plast = self._getWorldFromDisplay(last[0], last[1])
                    p = [self._campos0[0] + pfirst[0] - plast[0],
                         self._campos0[1] + pfirst[1] - plast[1],
                         self._campos0[2] + pfirst[2] - plast[2]]
                    self.setCameraPlanePosition(p)
            # Windowing, Shift Key
            # elif k == 'Shift_L' or self.getLevelFlag() is True:
            elif self._interactor.GetShiftKey() or self.getLevelFlag() is True:
                if interactorstyle.GetButton() == 1:
                    wmin, wmax = self._volume.display.getWindow()
                    rmin, rmax = self._volume.display.getRange()
                    dx = self._win0[0] - last[0]
                    dy = last[1] - self._win0[1]
                    r = (rmax - rmin) / 100
                    if dx != 0: wmin = wmin + (dx / abs(dx)) * r
                    if dy != 0: wmax = wmax + (dy / abs(dy)) * r
                    self._volume.display.setWindow(wmin, wmax)
                    self._renderwindow.Render()
                    self.RenderUpdated.emit(self)
                    self._win0 = last
            elif self.getFollowFlag() is True:
                # Update cursor position information and display
                self.setCursorFromDisplayPosition(last[0], last[1])
                p = self.getCursorWorldPosition()
                self.CursorPositionChanged.emit(self, p[0], p[1], p[2])  # 3D position corrected by offset
            else:
                if interactorstyle.GetButton() == 1 and self.isCursorEnabled():
                    # Update cursor position information and display
                    self.setCursorFromDisplayPosition(last[0], last[1])
                    p = self.getCursorWorldPosition()
                    self.CursorPositionChanged.emit(self, p[0], p[1], p[2])  # 3D position corrected by offset
            self._updateBottomRightInfo()

    def _onLeftReleaseEvent(self,  obj, evt_name):
        super()._onLeftReleaseEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            # k = interactorstyle.GetKeySym()
            # if k == 'Alt_L' or self.getMoveFlag() is True:
            if self._interactor.GetKeySym() == 'Alt_L' or self.getMoveFlag() is True:
                self._interactor.SetKeySym('')
                self.setCentralCrossVisibilityOff()
                self.setCursorVisibility(self._cursor0)
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)
                self._renderwindow.Render()
            # elif k == 'Shift_L' or self.getLevelFlag() is True:
            elif self._interactor.GetShiftKey() or self.getLevelFlag() is True:
                if self._cursor0 is not None:
                    self.setCursorVisibility(self._cursor0)
                    self._renderwindow.Render()

    def _onKeyPressEvent(self,  obj, evt_name):
        super()._onKeyPressEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            k = interactorstyle.GetKeySym()
            if self._interactor.GetControlKey():
                if k == 'Up' or k == 'Left': self.zoomIn()
                elif k == 'Down' or k == 'Right': self.zoomOut()
            else:
                if k == 'Up' or k == 'Left': self.sliceMinus()
                elif k == 'Down' or k == 'Right': self.slicePlus()

    def _onKeyReleaseEvent(self, obj, evt_name):
        super()._onKeyReleaseEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            if interactorstyle.GetButton() == 1:
                self.setCentralCrossVisibilityOff()
                if self._cursor0 is not None: self.setCursorVisibility(self._cursor0)
                self._renderwindow.SetCurrentCursor(VTK_CURSOR_ARROW)
                self._renderwindow.Render()


class SliceReorientViewWidget(SliceViewWidget):
    """
         SliceOverlayViewWidget class

         Description

            Derived from SliceViewWidget base class. Adds capacity to apply rigid transformation and
            displays a box widget to show and manipulate field of view.

         Inheritance

             QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceReorientViewWidget

         Private attributes

            _cursorpos0             float, float, float
            _rotations0             float, float, float
            _rotations              float, float, float
            _moveResliceCursorFlag  bool
            _rotationsFlag          bool
            _rotationxFlag          bool
            _rotationyFlag          bool
            _rotationzFlag          bool
            _translationsFlag       bool
            _size                   int, int, int
            _spacing                float, float, float
            _resliceCursor          vtkResliceCursor
            _resliceCursorActor     vtkActor
            _boxFov                 vtkBox
            _boxFovActor            vtkActor

         Custom Qt signals

            ResliceCursorChanged.emit(QWidget, float, float, float, float, float, float)
            SpacingChanged.emit(QWidget, float, float, float)
            SizeChanged.emit(QWidget, int, int, int)
            TranslationsChanged.emit(QWidget, float, float, float)
            RotationsChanged.emit(QWidget, float, float, float)

         Public Qt event synchronisation methods

            synchroniseResliceCursorChanged(QWidget, float, float, float, float, float, float, bool)
            synchroniseSpacingChanged(QWidget, float, float, float)
            synchroniseSizeChanged(QWidget, int, int, int))
            synchroniseTranslationsChanged(QWidget, float, float, float)
            synchroniseRotationsChanged(QWidget, float, float, float)

        Public methods

            reset()
            float, float, float = getTranslations()
            float, float, float = getRotations()
            SisypheTransform = getTransform()
            setTranslations(float, float, float)
            setRotations(float, float, float)
            float, float, float = getFOV()
            [float, float, float] = getSpacing()
            setSpacing([float, float, float])
            [int, int, int] = getSize()
            setSize([int, int, int])
            setDefaultFOV()
            setFOVBoxVisibility(bool)
            bool = getFOVBoxVisibility()
            translationEnabled()
            translationsDisabled()
            rotationsEnabled()
            rotationsDisabled()
            rotationXEnabled()
            rotationXDisabled()
            rotationYEnabled()
            rotationYDisabled()
            rotationZEnabled()
            rotationZDisabled()
            setResliceCursorPosition((float, float, float))
            (float, float, float) = getResliceCursorPosition()
            setResliceCursorColor([float, float, float])
            [float, float, float] = getResliceCursorColor()
            setResliceCursorOpacity(float)
            float = getResliceCursorOpacity()
            setResliceCursorLineWidth(float)
            float = getResliceCursorLineWidth()
            setBoxFovColor([float, float, float])
            [float, float, float] = getBoxFovColor()
            setBoxFovOpacity(float)
            float = getBoxFovOpacity()
            setBoxFovLineWidth(float)
            float = getBoxFovLineWidth()
            setLineOpacity(float)

            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods

        Revision 15/04/2023, add tooltip with transformation text (translations and rotations)
                             bug correction for rotations, replacement of atan by atan2
     """

    # Custom Qt signals

    ResliceCursorChanged = pyqtSignal(QWidget, float, float, float, float, float, float)
    SpacingChanged = pyqtSignal(QWidget, float, float, float)
    SizeChanged = pyqtSignal(QWidget, int, int, int)
    TranslationsChanged = pyqtSignal(QWidget, float, float, float)
    RotationsChanged = pyqtSignal(QWidget, float, float, float)

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._rotations0 = None
        self._rotations = [0.0, 0.0, 0.0]
        self._moveResliceCursorFlag = None
        self._translationsFlag = True
        self._rotationsFlag = True
        self._rotationxFlag = True
        self._rotationyFlag = True
        self._rotationzFlag = True
        self._size = None
        self._spacing = None

        self._resliceCursor = None
        self._initResliceCursor()

        self._boxFov = vtkCubeSource()
        self._fovmapper = vtkPolyDataMapper()
        self._fovmapper.SetInputConnection(self._boxFov.GetOutputPort())
        self._boxFovActor = vtkActor()
        self._boxFovActor.SetMapper(self._fovmapper)
        self._boxFovActor.SetVisibility(True)
        prop = self._boxFovActor.GetProperty()
        prop.SetColor(self._lcolor)
        prop.SetOpacity(self._lalpha)
        prop.EdgeVisibilityOn()
        prop.SetLineWidth(self._lwidth)
        prop.RenderLinesAsTubesOn()
        prop.SetRepresentationToWireframe()

        self._action['showcursor'].setVisible(False)
        self._action['followflag'].setVisible(False)

        self._action['resliceflag'] = QAction('Move reslice cursor')
        self._action['resliceflag'].setCheckable(True)
        self._group_flag.addAction(self._action['resliceflag'])
        self._menuActions.addAction(self._action['resliceflag'])
        self._action['resliceflag'].setChecked(True)

        self._tooltipstr = 'Reorient controls:\n' \
                           '\tPress left mouse button on reslicing cursor and move mouse,\n' \
                           '\tIf the mouse is close to center of the reslicing cursor,\n' \
                           '\ttranslations are applied by dragging, otherwise rotations\n' \
                           '\tare applied.\n' + self._tooltipstr
        self._trftooltip = 'Translations:\tX {:.1f} mm Y {:.1f} mm Z {:.1f} mm\n' \
                           'Rotations:\tX {:.1f}° Y {:.1f}° Z {:.1f}°\n\n' + self._tooltipstr
        self._tooltipstr = self._trftooltip.format(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

    # Public synchronisation event methods

    def synchroniseResliceCursorChanged(self, obj, x, y, z, rx, ry, rz):
        if self != obj and self.hasVolume():
            self._rotations = [rx, ry, rz]
            self._updateResliceCursor(x, y, z, rx, ry, rz, signal=False)

    def synchroniseSpacingChanged(self, obj, sx, sy, sz):
        if self != obj and self.hasVolume():
            self.setSpacing([sx, sy, sz], signal=False)

    def synchroniseSizeChanged(self, obj, sx, sy, sz):
        if self != obj and self.hasVolume():
            self.setSize([sx, sy, sz], signal=False)

    def synchroniseTranslationsChanged(self, obj, tx, ty, tz):
        if self != obj and self.hasVolume():
            self.setTranslations(tx, ty, tz, signal=False)

    def synchroniseRotationsChanged(self, obj, rx, ry, rz):
        if self != obj and self.hasVolume():
            self.setRotations(rx, ry, rz, signal=False)

    # Private method

    def _updateCameraClipping(self):
        pass

    def _applyTransform(self):
        if self.hasVolume():
            r = self._rotations
            p = self.getCursorWorldPosition()
            # Center of rotation at the cursor position
            self._volumeslice.SetOrigin(p)
            if self._orient == 0: self._volumeslice.SetOrientation(r[0], r[1], 0.0)
            elif self._orient == 1: self._volumeslice.SetOrientation(r[0], 0.0, r[2])
            else: self._volumeslice.SetOrientation(0.0, r[1], r[2])
            self._volume.getVTKImage().Modified()

    def _initResliceCursor(self):
        hline = vtkLineSource()
        vline = vtkLineSource()
        hline.SetPoint1(-500, 0, 1)
        hline.SetPoint2(500, 0, 1)
        vline.SetPoint1(0, -500, 1)
        vline.SetPoint2(0, 500, 1)
        lines = vtkAppendPolyData()
        lines.AddInputConnection(hline.GetOutputPort())
        lines.AddInputConnection(vline.GetOutputPort())
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(lines.GetOutputPort())
        # Reslice cursor
        self._resliceCursor = vtkFollower()
        self._resliceCursor.SetCamera(self._renderer.GetActiveCamera())
        self._resliceCursor.SetMapper(mapper)
        self._resliceCursor.GetProperty().SetLineWidth(self._lwidth)
        self._resliceCursor.GetProperty().SetColor(self._lcolor)
        self._resliceCursor.GetProperty().SetOpacity(self._lalpha)
        self._resliceCursor.SetVisibility(False)
        self._renderer.AddActor(self._resliceCursor)

    def _updateResliceCursor(self, x, y, z, rx, ry, rz, signal=True):
        """
            Translations
            SetOrigin() for boxFovActor, set coordinates of vtkActor barycenter
        """
        self._resliceCursor.SetPosition(x, y, z)
        self._boxFov.SetCenter(x, y, z)
        self._boxFov.Update()
        self._boxFovActor.SetOrigin(x, y, z)
        """
            Rotation direction of cursor is opposite to the geometric transformation
            3D boxFovActor -> -rx, -ry, -rz
            More complex for resliceCursor with vtkFollower -> rz, -ry, rx
        """
        if self._orient == 0:
            self._resliceCursor.SetOrientation(0.0, 0.0, rz)
            self._boxFovActor.SetOrientation(0.0, 0.0, -rz)
        elif self._orient == 1:
            self._resliceCursor.SetOrientation(0.0, 0.0, -ry)
            self._boxFovActor.SetOrientation(0.0, -ry, 0.0)
        else:
            self._resliceCursor.SetOrientation(0.0, 0.0, rx)
            self._boxFovActor.SetOrientation(-rx, 0.0, 0.0)
        self._applyTransform()
        self._renderwindow.Render()
        # Update tooltip
        tr = self.getTranslations()
        self._tooltipstr = self._trftooltip.format(tr[0], tr[1], tr[2], rx, ry, rz)
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')
        # Synchronise
        if signal: self.ResliceCursorChanged.emit(self, x, y, z, rx, ry, rz)

    def _setCameraFocalDepth(self, f, signal=True):
        super()._setCameraFocalDepth(f, signal)
        p = self.getCursorWorldPosition()
        self._updateResliceCursor(p[0], p[1], p[2],
                                  self._rotations[0],
                                  self._rotations[1],
                                  self._rotations[2], signal=False)

    # Public method

    def setVolume(self, volume):
        self._size = volume.getSize()
        self._spacing = volume.getSpacing()
        # Add reslice cursor actor
        c = volume.getCenter()
        self._resliceCursor.SetPosition(c[0], c[1], c[2])
        # Add box FOV actor
        fov = volume.getFieldOfView()
        self._boxFov.SetXLength(fov[0])
        self._boxFov.SetYLength(fov[1])
        self._boxFov.SetZLength(fov[2])
        self._boxFov.SetCenter(c[0], c[1], c[2])
        self._boxFov.Update()
        self._boxFovActor.SetOrigin(c[0], c[1], c[2])
        self._renderer.AddActor(self._boxFovActor)
        super().setVolume(volume)
        self._resliceCursor.SetVisibility(True)
        self._volumeslice.SetOrigin(volume.getCenter())
        self._renderer.GetActiveCamera().SetClippingRange(0.1, 1000)
        self._renderer.GetActiveCamera().SetFocalPoint(c)

    def reset(self):
        c = self._volume.getCenter()
        self._rotations = [0.0, 0.0, 0.0]
        self._updateResliceCursor(c[0], c[1], c[2], 0.0, 0.0, 0.0)

    def getTranslations(self):
        if self.hasVolume():
            c0 = self._volume.getCenter()
            c1 = self._resliceCursor.GetCenter()
            return c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2]

    def getRotations(self):
        if self.hasVolume():
            return self._rotations

    def setTranslations(self, tx, ty, tz, signal=True):
        c0 = self._volume.getCenter()
        self.setCursorWorldPosition(c0[0] + tx,
                                    c0[1] + ty,
                                    c0[2] + tz,
                                    signal)

    def setRotations(self, rx, ry, rz, signal=True):
        c = self.getCursorWorldPosition()
        self._rotations[0] = rx
        self._rotations[1] = ry
        self._rotations[2] = rz
        self._updateResliceCursor(c[0],
                                  c[1],
                                  c[2],
                                  self._rotations[0],
                                  self._rotations[1],
                                  self._rotations[2],
                                  signal)
        self._applyTransform()

    def getTransform(self):
        """
            Forward centered transform (center of rotation = volume center)
            Widget center of rotation is at the cursor position, not always in the volume center
            1. apply translations to move center of rotation (cursor position -> volume center) before rotation
            2. apply rotations
            It's not classic roto-translation matrix that has an inverse order (1. rotations 2. translations)
            Correct transformation is pre-multiply of the translation matrix by the rotation matrix
            Bugfix 02/04/2023, roto-translation matrix replacement by composite pre-multiplication matrix (T x R)
        """
        t = self.getTranslations()
        trf = SisypheTransform()
        trf.setAttributesFromFixedVolume(self._volume)
        trf.setTranslations([-t[0], -t[1], -t[2]])
        trf2 = SisypheTransform()
        trf2.setRotations(self.getRotations(), deg=True)
        trf.preMultiply(trf2, homogeneous=True)
        return trf

    def getFOV(self):
        if self.hasVolume():
            return (self._size[0] * self._spacing[0],
                    self._size[1] * self._spacing[1],
                    self._size[2] * self._spacing[2])

    def getSpacing(self):
        return self._spacing

    def setSpacing(self, spacing, signal=True):
        if self.hasVolume():
            self._spacing = spacing
            fov = self.getFOV()
            c = self._boxFov.GetCenter()
            self._boxFov.SetXLength(fov[0])
            self._boxFov.SetYLength(fov[1])
            self._boxFov.SetZLength(fov[2])
            self._boxFov.SetCenter(c[0], c[1], c[2])
            self._boxFov.Update()
            self._boxFovActor.SetOrigin(c[0], c[1], c[2])
            self._renderwindow.Render()
            if signal: self.SpacingChanged.emit(self, self._spacing[0], self._spacing[1], self._spacing[2])

    def getSize(self):
        return self._size

    def setSize(self, size, signal=True):
        if self.hasVolume():
            self._size = size
            fov = self.getFOV()
            c = self._boxFov.GetCenter()
            self._boxFov.SetXLength(fov[0])
            self._boxFov.SetYLength(fov[1])
            self._boxFov.SetZLength(fov[2])
            self._boxFov.SetCenter(c[0], c[1], c[2])
            self._boxFov.Update()
            self._boxFovActor.SetOrigin(c[0], c[1], c[2])
            self._renderwindow.Render()
            if signal: self.SizeChanged.emit(self, self._size[0], self._size[1], self._size[2])

    def setDefaultFOV(self, signal=True):
        if self.hasVolume():
            self._size = self._volume.getSize()
            self._spacing = self._volume.getSpacing()
            fov = self.getFOV()
            c = self._boxFov.GetCenter()
            self._boxFov.SetXLength(fov[0])
            self._boxFov.SetYLength(fov[1])
            self._boxFov.SetZLength(fov[2])
            self._boxFov.SetCenter(c[0], c[1], c[2])
            self._boxFov.Update()
            self._boxFovActor.SetOrigin(c[0], c[1], c[2])
            self._renderwindow.Render()
            if signal: self.SizeChanged.emit(self, self._size[0], self._size[1], self._size[2])
            if signal: self.SpacingChanged.emit(self, self._spacing[0], self._spacing[1], self._spacing[2])

    def setFOVBoxVisibility(self, v):
        if isinstance(v, bool): self._boxFovActor.SetVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFOVBoxVisibility(self):
        return self._boxFovActor.GetVisibility()

    def setResliceCursorPosition(self, p):
        r = self.getRotations()
        self._updateResliceCursor(p[0], p[1], p[2], r[0], r[1], r[2])

    def getResliceCursorPosition(self):
        return self._resliceCursor.GetPosition()

    def translationsEnabled(self):
        self._translationsFlag = True

    def translationsDisabled(self):
        self._translationsFlag = False

    def rotationsEnabled(self):
        self._rotationsFlag = True

    def rotationsDisabled(self):
        self._rotationsFlag = False

    def rotationXEnabled(self):
        self._rotationsFlag = True
        self._rotationxFlag = True

    def rotationXDisabled(self):
        self._rotationxFlag = False

    def rotationYEnabled(self):
        self._rotationsFlag = True
        self._rotationyFlag = True

    def rotationYDisabled(self):
        self._rotationzFlag = False

    def rotationZEnabled(self):
        self._rotationsFlag = True
        self._rotationzFlag = True

    def rotationZDisabled(self):
        self._rotationzFlag = False

    def setResliceCursorColor(self, rgb):
        self._resliceCursor.GetProperty().SetColor(rgb[0], rgb[1], rgb[2])
        self._renderwindow.Render()

    def getResliceCursorColor(self):
        return self._resliceCursor.GetProperty().GetColor()

    def setResliceCursorOpacity(self, v):
        if isinstance(v, float):
            self._resliceCursor.GetProperty().SetOpacity(v)
            self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorOpacity(self):
        return self._resliceCursor.GetProperty().GetOpacity()

    def setResliceCursorLineWidth(self, v):
        if isinstance(v, float):
            self._resliceCursor.GetProperty().SetLineWidth(v)
            self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorLineWidth(self):
        return self._resliceCursor.GetProperty().GetLineWidth()

    def setFovBoxColor(self, rgb):
        self._boxFovActor.GetProperty().SetColor(rgb[0], rgb[1], rgb[2])
        self._renderwindow.Render()

    def getFovBoxColor(self):
        return self._boxFovActor.GetProperty().GetColor()

    def setFovBoxOpacity(self, v):
        if isinstance(v, float):
            self._boxFovActor.GetProperty().SetOpacity(v)
            self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxOpacity(self):
        return self._boxFovActor.GetProperty().GetOpacity()

    def setFovBoxLineWidth(self, v):
        if isinstance(v, float):
            self._boxFovActor.GetProperty().SetLineWidth(v)
            self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxLineWidth(self):
        return self._boxFovActor.GetProperty().GetLineWidth()

    def setLineOpacity(self, v, signal=True):
        super().setLineOpacity(v, signal)
        self._resliceCursor.GetProperty().SetOpacity(v)

    # Private vtk event methods

    def _onLeftPressEvent(self, obj, evt_name):
        if self.hasVolume():
            if self._action['resliceflag'].isChecked():
                interactorstyle = self._window.GetInteractorStyle()
                self._mousepos0 = interactorstyle.GetLastPos()
                self._rotations0 = self._rotations
                c = self._resliceCursor.GetCenter()
                # Set type of movement
                d1 = self._volume.getFieldOfView()[1] / 4
                p = list(self._getWorldFromDisplay(self._mousepos0[0], self._mousepos0[1]))
                d = 2 - self._orient
                p[d] = c[d]
                d2 = sqrt(pow(p[0] - c[0], 2) +
                          pow(p[1] - c[1], 2) +
                          pow(p[2] - c[2], 2))
                # rotFlag adds global and single rotation permissions
                if self._orient == 0: rotFlag = self._rotationsFlag and self._rotationzFlag
                elif self._orient == 1: rotFlag = self._rotationsFlag and self._rotationyFlag
                else: rotFlag = self._rotationsFlag and self._rotationxFlag
                if self._translationsFlag and rotFlag:
                    if d2 < d1:
                        self._moveResliceCursorFlag = 1  # Translate, if mouse click close to image center
                    else:
                        self._moveResliceCursorFlag = 2  # Rotate, if mouse click close to image edge
                        self.setCursorDisabled()
                elif self._translationsFlag:
                    self._moveResliceCursorFlag = 1
                elif rotFlag:
                    self._moveResliceCursorFlag = 2
                    self.setCursorDisabled()
                else:
                    self._moveResliceCursorFlag = 0
                    self.setCursorDisabled()

    def _onMouseMoveEvent(self, obj, evt_name):
        super()._onMouseMoveEvent(obj, evt_name)
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            if self._action['resliceflag'].isChecked() and interactorstyle.GetButton() == 1:
                p = self.getCursorWorldPosition()
                # Translate
                if self._moveResliceCursorFlag == 1:
                    self._updateResliceCursor(p[0], p[1], p[2],
                                              self._rotations[0],
                                              self._rotations[1],
                                              self._rotations[2])
                # Rotate
                elif self._moveResliceCursorFlag == 2:
                    c = self._getDisplayFromWorld(p[0], p[1], p[2])
                    last = interactorstyle.GetLastPos()
                    # Old version, bug if the mouse move is close to horizontal line
                    #  r = atan((last[0] - c[0]) / (last[1] - c[1])) - \
                    #      atan((self._mousepos0[0] - c[0]) / (self._mousepos0[1] - c[1]))
                    # Revision 15/04/2023, bug correction for rotations, replacement of atan by atan2
                    a1 = last[0] - c[0]
                    o1 = last[1] - c[1]
                    a2 = self._mousepos0[0] - c[0]
                    o2 = self._mousepos0[1] - c[1]
                    alpha1 = degrees(atan2(o1, a1))
                    alpha2 = degrees(atan2(o2, a2))
                    # Atan2 gives negative angle for negative opposite segment (o1 and o2)
                    # Conversion to always keep a positive angle between 0.0 and 360.0 °
                    if alpha1 < 0: alpha1 += 360.0
                    if alpha2 < 0: alpha2 += 360.0
                    r = alpha2 - alpha1
                    if self._orient in (0, 2): r = -r
                    self._rotations = list(self._rotations0)
                    # self._rotations[2 - self._orient] += degrees(r)
                    self._rotations[2 - self._orient] += r
                    self._updateResliceCursor(p[0], p[1], p[2],
                                              self._rotations[0],
                                              self._rotations[1],
                                              self._rotations[2])

    def _onLeftReleaseEvent(self, obj, evt_name):
        super()._onLeftReleaseEvent(obj, evt_name)
        if self.hasVolume():
            if self._action['resliceflag'].isChecked():
                self._mousepos0 = None
                self._rotations0 = None
                self.setCursorEnabled()


class SliceOverlayViewWidget(SliceViewWidget):
    """
        SliceOverlayViewWidget class

        Description

            Derived from base class SliceViewWidget. Adds ability to display overlays.

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget

        Private attributes (Non-GUI)

            _ovl                SisypheVolumeCollection
            _ovlslices          list() of vtkImageSlice
            _ovlvalue           SisypheVolume, overlay for which voxel value is displayed
            _ovlvaluetrf        SisypheTransform, applied to overlay for which voxel value is displayed
            _aligncenters       bool, align centers of reference volume and overlays
            _moveOverlayFlag    int

        Custom Qt signals

            OverlayListChanged.emit()
            TranslationsChanged.emit(QWidget, tuple, int)
            RotationsCHanged.emit(QWidget, tuple, int)
            ViewOverlayMethodCalled.emit(QWidget, str, object, object)

        Public Qt event synchronisation methods

            synchroniseViewOverlayMethodCalled()
            synchroniseTranslationsChanged(QWidget, tuple, int)
            synchroniseRotationsChanged(QWidget, tuple, int)

        Public methods

            setAlignCenters(bool)
            alignCentersOn()
            alignCentersOff()
            bool = getAlignCenters()
            addOverlay(SisypheVolume)
            int = getOverlayCount()
            bool = hasOverlay()
            int = getOverlayIndex(SisypheVolume)
            removeOverlay(int or SisypheVolume)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)
            vtkImageSlice = getVtkImageSliceOverlay(int)
            bool = hasVtkImageSliceOverlay(vtkImageSlice)
            SisypheVolumeCollection = getOverlayCollection()
            setOverlayOpacity(float)
            float = getOverlayOpacity()
            setOverlayVisibility(float)
            setOverlayVisibilityOn()
            setOverlayVisibilityOff()
            float = getOverlayVisibility()
            setInfoOverlayValueVisibility(int, bool)
            setInfoOverlayValueVisibilityOff(bool)
            int = getInfoOverlayValueVisibility()
            setOverlayColorbar(int)
            setVolumeColorbar()
            setTransform(SisypheTransform, int)
            SisypheTransform = getTransform(int)
            setVTKTransform(vtkTransform, int)
            vtkTransform = getVTKTransform(int)
            setTranslations([float, float, float], int, bool, bool)
            (float, float, float) = getTranslations(int, bool)
            setRotations([float, float, float], int, bool, bool)
            (float, float, float) = getRotations(int, bool)
            setMoveOverlayFlag()
            setMoveOverlayToTranslate()
            setMoveOverlayToRotate()
            setMoveOverlayOff()
            bool = getMoveOverlayFlag()

            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods

        Revision 15/04/2023, method _addReslice: alignment of origins, alignment of image centers
                             bug correction for rotations, replacement of atan by atan2
    """

    # Custom Qt signals

    OverlayListChanged = pyqtSignal()
    TranslationsChanged = pyqtSignal(QWidget, tuple, int)  # tuple translation, int overlay index
    RotationsChanged = pyqtSignal(QWidget, tuple, int)  # tuple translation, int overlay index
    ViewOverlayMethodCalled = pyqtSignal(QWidget, str, object, object)  # str method name, object parameter

    # Special method

    def __init__(self, overlays=None, parent=None):
        super().__init__(parent)

        if overlays is not None and isinstance(overlays, SisypheVolumeCollection): self._ovl = overlays
        else: self._ovl = SisypheVolumeCollection()

        self._ovlslices = list()  # list of overlay vtkImageSlice
        self._ovlvalue = None
        self._ovlvaluetrf = None
        self._aligncenters = True

        self._rotations0 = None
        self._translations0 = None
        self._moveOverlayFlag = 0

        # Init popup menu

        self._menuOverlayVoxel = QMenu('Overlay voxel value at mouse position', self._popup)
        self._menuOverlayVoxel.triggered.connect(self._menuOverlayVoxelTriggered)
        action = self._menuShape.menuAction()
        self._menuInformation.insertMenu(action, self._menuOverlayVoxel)
        self._menuOverlayVoxel.setVisible(False)
        self._group_menuOverlayVoxel = QActionGroup(self)
        self._group_menuOverlayVoxel.setExclusive(True)
        action = QAction('No')
        action.setCheckable(True)
        action.setChecked(True)
        self._group_menuOverlayVoxel.addAction(action)
        self._menuOverlayVoxel.addAction(action)

        self._action['moveoverlayflag'] = QAction('Move overlay', self)
        self._action['moveoverlayflag'].setCheckable(True)
        self._action['moveoverlayflag'].triggered.connect(lambda: self.setMoveOverlayFlag(True))
        self._group_flag.addAction(self._action['moveoverlayflag'])
        self._menuActions.addAction(self._action['moveoverlayflag'])

    # Private method

    def _addReslice(self, volume, alpha):
        mapper = vtkImageResliceMapper()
        mapper.BorderOff()
        mapper.SliceAtFocalPointOn()
        mapper.SliceFacesCameraOn()
        mapper.SetInputData(volume.getVTKImage())
        slc = vtkImageSlice()
        slc.SetMapper(mapper)
        slc.SetOrigin(volume.getCenter())
        """
            Apply centered transform if exists, center of rotation = center of volume (SisypheVolume.getCenter())
            or align origins, if origins are not (0.0, 0.0, 0.0)
            or align centers of images
        """
        # Apply co-registration transform if exists
        if volume.hasTransform(self._volume.getID()):
            trf = volume.getTransformFromID(self._volume.getID())
            if not trf.isIdentity():
                # Affine forward transform
                slc.SetUserMatrix(trf.getVTKMatrix4x4())
        else:
            # Revision 15/04/2023
            # Apply translations to align origins
            if not (self._volume.isDefaultOrigin() or volume.isDefaultOrigin()):
                trf = SisypheTransform()
                vo = self._volume.getOrigin()
                oo = volume.getOrigin()
                trf.setTranslations((vo[0] - oo[0], vo[1] - oo[1], vo[2] - oo[2]))
                slc.SetUserMatrix(trf.getVTKMatrix4x4())
            elif not volume.hasSameFieldOfView(self._volume):
                # Revision 15/04/2023
                # Apply translations to align centers of images
                if self._aligncenters:
                    cv = self._volume.getCenter()
                    co = volume.getCenter()
                    trf = SisypheTransform()
                    trf.setTranslations((cv[0]-co[0], cv[1]-co[1], cv[2]-co[2]))
                    slc.SetUserMatrix(trf.getVTKMatrix4x4())
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._stack.AddImage(slc)
        return slc

    def _removeSlice(self, volume):
        vtkv = volume.getVTKImage()
        for slc in self._ovlslices:
            vtks = slc.GetMapper().GetInput()
            if vtkv == vtks:
                if self._stack.HasImage(slc): self._stack.RemoveImage(slc)
                self._ovlslices.remove(slc)
                del slc
                break

    def _getInfoValuesText(self, p):
        txt = super()._getInfoValuesText(p)
        if self._ovlvalue is not None:
            if self._ovlvaluetrf is not None: p = self._ovlvaluetrf.applyToPoint(p)
            if p is None: return txt
            x, y, z = p[0], p[1], p[2]
            s = self._ovlvalue.getSize()
            v = self._ovlvalue.getSpacing()
            x = int(x / v[0])
            y = int(y / v[1])
            z = int(z / v[2])
            if not (0 <= x < s[0]): return txt
            if not (0 <= y < s[1]): return txt
            if not (0 <= z < s[2]): return txt
            u = self._ovlvalue.getAcquisition().getUnit()
            if u == 'No': u = ''
            if self._ovlvalue.getAcquisition().isLB():
                v = self._ovlvalue[x, y, z]
                label = self._ovlvalue.getAcquisition().getLabel(v)
                val = '{} value: {} label: {} '.format(self._ovlvalue.getName(), v, label)
            elif self._ovlvalue.isIntegerDatatype():
                val = '{} value: {} {} '.format(self._ovlvalue.getName(), self._ovlvalue[x, y, z], u)
            else:
                m = abs(self._ovlvalue.getDisplay().getRangeMax())
                if m > 10: val = 'Overlay#{} value: {:.1f} {} '.format(self._ovlvalue.getName(), self._ovlvalue[x, y, z], u)
                elif m > 1: val = 'Overlay#{} Value: {:.2f} {} '.format(self._ovlvalue.getName(), self._ovlvalue[x, y, z], u)
                else: val = 'Overlay#{} Value: {:.6g} {} '.format(self._ovlvalue.getName(), self._ovlvalue[x, y, z], u)
            txt = txt + '\n{} voxel {} x {} x {}'.format(val, x, y, z)
        return txt

    def _addToMenuVoxelOverlayValue(self, volume):
        if isinstance(volume, SisypheVolume):
            self._ovlvalue = volume
            self._ovlvaluetrf = self._volume.getTransformFromID(volume.getID())
            action = QAction(volume.getName())
            action.setCheckable(True)
            self._group_menuOverlayVoxel.addAction(action)
            self._menuOverlayVoxel.addAction(action)
            # self._menuOverlayVoxel.setVisible(True)

    def _removeFromMenuVoxelOverlayValue(self, volume):
        if isinstance(volume, SisypheVolume):
            actions = self._group_menuOverlayVoxel.actions()
            n = len(actions)
            if n > 1:
                name = volume.getName()
                for action in actions:
                    if action.text() == name:
                        if action.isChecked():
                            actions[0].setChecked(True)
                        self._ovlvalue = None
                        self._ovlvaluetrf = None
                        self._group_menuOverlayVoxel.removeAction(action)
                        self._menuOverlayVoxel.removeAction(action)
                        del action
                        n -= 1
                        break
            self._menuOverlayVoxel.setVisible(n > 1)

    def _clearMenuVoxelOverlayValue(self):
        actions = self._group_menuOverlayVoxel.actions()
        n = len(actions)
        if n > 1:
            for action in actions:
                if action.text() != 'No':
                    self._group_menuOverlayVoxel.removeAction(action)
                    self._menuOverlayVoxel.removeAction(action)
                    del action
        actions[0].setChecked(True)
        self._ovlvalue = None
        self._ovlvaluetrf = None
        self._menuOverlayVoxel.setVisible(False)

    def _menuOverlayVoxelTriggered(self, action):
        self.setInfoOverlayValueVisibility(action.text())

    def _updateTooltip(self):
        pass

    # Public synchronisation event methods

    def synchroniseViewOverlayMethodCalled(self, obj, function, param1, param2):
        if obj != self and self.hasVolume():
            f = getattr(self, function)
            if param1 is None and param2 is None: f(signal=False)
            elif param2 is None: f(param1, signal=False)
            else: f(param1, param2, signal=False)

    def synchroniseTranslationsChanged(self, obj, t, index):
        if obj != self and self.hasVolume():
            self.setTranslations(t, index, signal=False)

    def synchroniseRotationsChanged(self, obj, r, index):
        if obj != self and self.hasVolume():
            self.setRotations(r, index, deg=True, signal=False)

    # Public methods

    def displayOff(self):
        super().displayOff()
        self._clearMenuVoxelOverlayValue()

    def setAlignCenters(self, v):
        if isinstance(v, bool): self._aligncenters = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def alignCentersOn(self):
        self.setAlignCenters(True)

    def alignCentersOff(self):
        self.setAlignCenters(False)

    def getAlignCenters(self):
        return self._aligncenters

    def removeVolume(self):
        self.removeAllOverlays()
        super().removeVolume()

    def addOverlay(self, volume, alpha=0.5):
        if self._volume is not None:
            if volume not in self._ovl:
                self._ovl.append(volume)
                ovlslice = self._addReslice(volume, alpha)
                ovlslice.GetProperty().SetLayerNumber(len(self._ovlslices) + 1)
                self._ovlslices.append(ovlslice)
                self._addToMenuVoxelOverlayValue(volume)
                self._renderwindow.Render()
                self.OverlayListChanged.emit()
        else: raise ValueError('reference volume must be set before overlay.')

    def getOverlayCount(self):
        return len(self._ovl)

    def hasOverlay(self):
        return len(self._ovl) > 0

    def removeOverlay(self, o):
        if self.hasOverlay():
            if isinstance(o, int):
                if 0 <= o < len(self._ovl):
                    o = self._ovl[o]
            if isinstance(o, SisypheVolume):
                if o in self._ovl:
                    self._ovl.remove(o)
                    self._removeSlice(o)
                    self._removeFromMenuVoxelOverlayValue(o)
                    self._renderwindow.Render()
                    self.OverlayListChanged.emit()

    def removeAllOverlays(self):
        if self.hasOverlay():
            self._ovl.clear()
            for slc in self._ovlslices:
                if self._stack.HasImage(slc): self._stack.RemoveImage(slc)
                self._ovlslices.remove(slc)
                del slc
            self._renderwindow.Render()
            self.OverlayListChanged.emit()
            self._clearMenuVoxelOverlayValue()

    def getOverlayIndex(self, o):
        if self.hasOverlay():
            if isinstance(o, SisypheVolume):
                if o in self._ovl: return self._ovl.index(o)
                else: return None
        else: raise AttributeError('No overlay')

    def getOverlayFromIndex(self, index):
        if self.hasOverlay():
            if 0 <= index < len(self._ovl):
                return self._ovl[index]
        else: raise AttributeError('No overlay')

    def getVtkImageSliceOverlay(self, index):
        if self.hasOverlay():
            if 0 <= index < len(self._ovlslices):
                return self._ovlslices[index]
        else: raise AttributeError('No overlay')

    def hasVtkImageSliceOverlay(self, o):
        if isinstance(o, vtkImageSlice):
            if o in self._ovlslices: return self._ovlslices.index(o)
            else: return None

    def getOverlayCollection(self):
        return self._ovl

    def setOverlayOpacity(self, o, alpha, signal=True):
        if isinstance(alpha, float):
            if self.hasOverlay():
                if isinstance(o, SisypheVolume):
                    if o in self._ovl: o = self._ovl.index(o)
                if isinstance(o, int):
                    self._ovlslices[o].GetProperty().SetOpacity(alpha)
                    self._renderwindow.Render()
                else: raise TypeError('first parameter type {} is not int or SisypheVolume.'.format(type(o)))
                if signal: self.ViewOverlayMethodCalled.emit(self, 'setOverlayOpacity', o, alpha)
        else: raise TypeError('second parameter type {} is not float.'.format(type(alpha)))

    def getOverlayOpacity(self, o):
        if self.hasOverlay():
            if isinstance(o, int):
                if 0 <= o < len(self._ovl):
                    o = self._ovl[o]
            if isinstance(o, SisypheVolume):
                if o in self._ovl:
                    index = self._ovl.index(o)
                    self._ovlslices[index].GetProperty().GetOpacity()
        else: raise AttributeError('No overlay')

    def setOverlayVisibility(self, o, v, signal=True):
        if isinstance(v, bool):
            if self.hasOverlay():
                if isinstance(o, SisypheVolume):
                    if o in self._ovl: o = self._ovl.index(o)
                if isinstance(o, int):
                    self._ovlslices[o].SetVisibility(v)
                    self._renderwindow.Render()
                else: raise TypeError('first parameter type {} is not int or SisypheVolume.'.format(type(o)))
                if signal: self.ViewOverlayMethodCalled.emit(self, 'setOverlayVisibility', o, v)
        else: raise TypeError('second parameter type {} is not bool.'.format(type(v)))

    def setOverlayVisibilityOn(self, o):
        self.setOverlayVisibility(o, True)

    def setOverlayVisibilityOff(self, o):
        self.setOverlayVisibility(o, False)

    def getOverlayVisibility(self, o):
        if self.hasOverlay():
            if isinstance(o, int):
                if 0 <= o < len(self._ovl):
                    o = self._ovl[o]
            if isinstance(o, SisypheVolume):
                if o in self._ovl:
                    index = self._ovl.index(o)
                    return self._ovlslices[index].GetVisibility()
        else: raise AttributeError('No overlay')

    def setInfoOverlayValueVisibility(self, name, signal=True):
        if isinstance(name, str):
            self._ovlvalue = None
            self._ovlvaluetrf = None
            # Update checked item in menu
            actions = self._group_menuOverlayVoxel.actions()
            for action in actions:
                if action.text() == name:
                    action.setChecked(True)
                    break
            # Update overlay
            for ovl in self._ovl:
                if ovl.getName() == name:
                    self._ovlvalue = ovl
                    trf = ovl.getTransformFromID(self._volume.getID())
                    if trf is not None and not trf.isIdentity():
                        self._ovlvaluetrf = trf
            self._updateBottomRightInfo()
            if signal: self.ViewMethodCalled.emit(self, 'setInfoOverlayValueVisibility', name)
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def setInfoOverlayValueVisibilityOff(self, signal=True):
        self.setInfoOverlayValueVisibility('No', signal)

    def getInfoOverlayValueVisibility(self):
        return self._group_menuOverlayVoxel.checkedAction().text()

    def setOverlayColorbar(self, i=0):
        n = self.getOverlayCount()
        if n > 0 and 0 <= i < n:
            ovl = self._ovl[i]
            self._colorbar.SetLookupTable(ovl.display.getVTKLUT())
            if ovl.isIntegerDatatype(): self._colorbar.SetLabelFormat('%5.0f')
            else: self._colorbar.SetLabelFormat('%5.2f')

    def setVolumeColorbar(self):
        if self.hasVolume():
            self._colorbar.SetLookupTable(self._volume.display.getVTKLUT())
            if self._volume.isIntegerDatatype(): self._colorbar.SetLabelFormat('%5.0f')
            else: self._colorbar.SetLabelFormat('%5.2f')

    def setTransform(self, trf, index=0):
        if self.getOverlayCount() > index:
            if isinstance(trf, SisypheTransform):
                t = trf.getTranslations()
                self.setTranslations(t, index)
                r = trf.getRotations(deg=True)
                self.setRotations(r, index, deg=True)
            else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(trf)))
        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def getTransform(self, index=0):
        if self.getOverlayCount() > index:
            trf = SisypheTransform()
            img = self._ovl[index]
            trf.setAttributesFromFixedVolume(img)
            t = self.getTranslations(index)
            trf.setTranslations(t[0], t[1], t[2])
            r = self.getRotations(index, deg=True)
            trf.setRotations(r[0], r[1], r[2], deg=True)
            return trf
        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def setVTKTransform(self, trf, index=0):
        if self.getOverlayCount() > index:
            if isinstance(trf, vtkTransform):
                t = trf.GetPosition()
                self.setTranslations(t, index)
                r = trf.GetOrientation()
                self.setRotations(r, index, deg=True)
            else: raise TypeError('parameter type {} is not vtkTransform.'.format(type(trf)))
        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def getVTKTransform(self, index=0):
        if self.getOverlayCount() > index:
            trf = vtkTransform()
            t = self.getTranslations(index)
            trf.SetPosition(t[0], t[1], t[2])
            r = self.getRotations(index, deg=True)
            trf.SetOrientation(r[0], r[1], r[2])
            return trf

        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def setTranslations(self, t, index=0, signal=True):
        if isinstance(t, (list, tuple)):
            if index < 0:
                for i in range(self.getOverlayCount()):
                    if self._ovl[i].hasSameFieldOfView(self._ovl[0]):
                        self._ovlslices[i].SetPosition(t[0], t[1], t[2])
                        self._ovl[i].getVTKImage().Modified()
            else:
                if self.getOverlayCount() > index:
                    self._ovlslices[index].SetPosition(t[0], t[1], t[2])
                    self._ovl[index].getVTKImage().Modified()
                else: raise IndexError('index parameter value {} is out of range.'.format(index))
            self._renderwindow.Render()
            self._updateTooltip()
            if signal: self.TranslationsChanged.emit(self, t, index)
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(t)))

    def getTranslations(self, index=0):
        if self.getOverlayCount() > index:
            return self._ovlslices[index].GetPosition()
        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def setRotations(self, r, index=0, deg=True, signal=True):
        if isinstance(r, (list, tuple)):
            if index < 0:
                if not deg: r = (degrees(r[0]), degrees(r[1]), degrees(r[2]))
                for i in range(self.getOverlayCount()):
                    if self._ovl[i].hasSameFieldOfView(self._ovl[0]):
                        self._ovlslices[i].SetOrientation(r[0], r[1], r[2])
                        self._ovl[i].getVTKImage().Modified()
            else:
                if self.getOverlayCount() > index:
                    self._ovlslices[index].SetOrientation(r[0], r[1], r[2])
                    self._ovl[index].getVTKImage().Modified()
                else: raise IndexError('index parameter value {} is out of range.'.format(index))
            self._renderwindow.Render()
            self._updateTooltip()
            if signal: self.RotationsChanged.emit(self, r, index)
        else: raise TypeError('parameter type {} is not list or tuple.'.format(type(r)))

    def getRotations(self, index=0, deg=True):
        if self.getOverlayCount() > index:
            if deg: return self._ovlslices[0].GetOrientation()
            else:
                rx, ry, rz = self._ovlslices[0].GetOrientation()
                return radians(rx), radians(ry), radians(rz)
        else: raise IndexError('index parameter value {} is out of range.'.format(index))

    def setMoveOverlayFlag(self, signal=True):
        if self.hasOverlay():
            self._action['moveoverlayflag'].setChecked(True)
            if signal: self.ViewOverlayMethodCalled.emit(self, 'setMoveOverlayFlag', None, None)
        else: raise AttributeError('No overlay')

    def setMoveOverlayToTranslate(self, signal=True):
        self._moveOverlayFlag = 1
        self._action['moveoverlayflag'].setChecked(True)
        if signal: self.ViewOverlayMethodCalled.emit(self, 'setMoveOverlayToTranslate', None, None)

    def setMoveOverlayToRotate(self, signal=True):
        self._moveOverlayFlag = 2
        self._action['moveoverlayflag'].setChecked(True)
        if signal: self.ViewOverlayMethodCalled.emit(self, 'setMoveOverlayToRotate', None, None)

    def setMoveOverlayOff(self, signal=True):
        self.setNoActionFlag(signal)

    def getMoveOverlayFlag(self):
        return self._action['moveoverlayflag'].isChecked()

    # Private vtk event methods

    def _onLeftPressEvent(self, obj, evt_name):
        if self.hasOverlay() and self.getMoveOverlayFlag():
            interactorstyle = self._window.GetInteractorStyle()
            self._mousepos0 = interactorstyle.GetLastPos()
            self._rotations0 = self.getRotations(deg=True)
            self._translations0 = self.getTranslations()
            # Set type of movement
            d1 = self._ovl[0].getFieldOfView()[1] / 4
            p = list(self._getWorldFromDisplay(self._mousepos0[0], self._mousepos0[1]))
            f = self._ovlslices[0].GetCenter()
            d = 2 - self._orient
            p[d] = f[d]
            d2 = sqrt(pow(p[0] - f[0], 2) +
                      pow(p[1] - f[1], 2) +
                      pow(p[2] - f[2], 2))
            if d2 < d1:
                self._moveOverlayFlag = 1   # Translate, if click close to image center
                super()._onLeftPressEvent(obj, evt_name)
            else: self._moveOverlayFlag = 2         # Rotate, if click close to image edge
        else: super()._onLeftPressEvent(obj, evt_name)

    def _onMouseMoveEvent(self, obj, evt_name):
        if self.hasOverlay() and self.getMoveOverlayFlag() and self._mousepos0 is not None:
            interactorstyle = self._window.GetInteractorStyle()
            if interactorstyle.GetButton() == 1:
                last = interactorstyle.GetLastPos()
                # Translate
                if self._moveOverlayFlag == 1:
                    plast = list(self._getWorldFromDisplay(last[0], last[1]))
                    pfirst = list(self._getWorldFromDisplay(self._mousepos0[0],  self._mousepos0[1]))
                    f = self._renderer.GetActiveCamera().GetFocalPoint()
                    d = 2 - self._orient
                    plast[d] = f[d]
                    pfirst[d] = f[d]
                    self.setTranslations((self._translations0[0] + plast[0] - pfirst[0],
                                          self._translations0[1] + plast[1] - pfirst[1],
                                          self._translations0[2] + plast[2] - pfirst[2]), index=-1)
                # Rotate
                elif self._moveOverlayFlag == 2:
                    c = self._ovlslices[0].GetCenter()
                    c = self._getDisplayFromWorld(c[0], c[1], c[2])
                    # Old version, bug if the mouse move is close to horizontal line
                    #  r = atan((last[0] - c[0]) / (last[1] - c[1])) - \
                    #      atan((self._mousepos0[0] - c[0]) / (self._mousepos0[1] - c[1]))
                    # Revision 15/04/2023, bug correction for rotations, replacement of atan by atan2
                    a1 = last[0] - c[0]
                    o1 = last[1] - c[1]
                    a2 = self._mousepos0[0] - c[0]
                    o2 = self._mousepos0[1] - c[1]
                    alpha1 = degrees(atan2(o1, a1))
                    alpha2 = degrees(atan2(o2, a2))
                    # Atan2 gives negative angle for negative opposite segment (o1 and o2)
                    # Conversion to always keep a positive angle between 0.0 and 360.0 °
                    if alpha1 < 0: alpha1 += 360.0
                    if alpha2 < 0: alpha2 += 360.0
                    r = alpha2 - alpha1
                    if self._orient == 1: r = -r
                    r2 = list(self._rotations0)
                    # r2[2 - self._orient] += degrees(r)
                    r2[2 - self._orient] += r
                    self.setRotations(tuple(r2), deg=True, index=-1)
            else: super()._onMouseMoveEvent(obj, evt_name)
        else: super()._onMouseMoveEvent(obj, evt_name)

    def _onLeftReleaseEvent(self, obj, evt_name):
        super()._onLeftReleaseEvent(obj, evt_name)
        if self.hasOverlay() and self.getMoveOverlayFlag():
            self._mousepos0 = None
            self._rotations0 = None
            self._translations0 = None
            self._moveOverlayFlag = 0


class SliceRegistrationViewWidget(SliceOverlayViewWidget):
    """
        SliceRegistrationViewWidget

        Description

            Derived from SliceOverlayViewWidget class. Displays a box widget to crop overlay.
            Used to evaluate registration quality between two volumes.

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> SliceRegistrationViewWidget

        Private attributes

            _cropbox        BoxWidget, overlay inside box and volume outside
            _regbox         BoxWidget, registration area (default FOV area)
            _regarea        [float] * 6, registration area oin world coordinates (x, y, z, width, height, depth)
            _crop           bool, crop _volumeslice volume vtkImageSlice with _cropbox BoxWidget
            _gradient       SisypheVolume, edge overlay

        Custom Qt signals

            CropChanged.emit(QWidget, bool)                     Crop synchronisation
            RegistrationBoxVisibilityChanged(QWidget, bool)     Registration area box visibility synchronisation
            RegistrationBoxChanged(QWidget, list)               Registration area box display synchronisation

        Public Qt event synchronisation methods

            synchroniseCropChanged(QWidget, bool)
            synchroniseRegistrationBoxVisibilityChanged(QWidget, bool)
            synchroniseRegistrationBoxChanged(QWidget, list)

        Public methods

            setCrop(bool)
            bool = getCrop()
            cropOn()
            cropOff()
            setRegistrationBoxVisibility(bool)
            bool = getRegistrationBoxVisibility()
            [float] * 6 = getRegistrationBoxWorldArea()
            [float] * 6 = getRegistrationBoxMatrixArea()
            registrationBoxOn()
            registrationBoxOff()
            setRegistrationBoxArea([float] * 6)
            popupCropEnabled()
            popupCropDisabled()
            displayEdge()
            displayNative()
            displayEdgeAndNative()

            inherited SliceOverlayViewWidget methods
            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods
    """

    # Custom Qt signals

    CropChanged = pyqtSignal(QWidget, bool)
    RegistrationBoxVisibilityChanged = pyqtSignal(QWidget, bool)
    RegistrationBoxChanged = pyqtSignal(QWidget, list)

    # Special method

    def __init__(self, overlays=None, parent=None):
        super().__init__(overlays, parent)

        self._crop = False
        self._cropbox = None
        self._regbox = None
        """
            _regarea: registration area (world coordinates)
            _regarea[0] -> x point
            _regarea[1] -> y point
            _regarea[2] -> z point
            _regarea[3] -> width
            _regarea[4] -> height
            _regarea[5] -> depth
            
        """
        self._regarea = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        self._initRegistrationBox()

        # Init popup menu

        self._action['crop'] = QAction('Box crop', self)
        self._action['crop'].setCheckable(True)
        self._action['crop'].triggered.connect(lambda: self.setCrop(self._action['crop'].isChecked()))
        self._action['crop'].setVisible(False)
        self._popup.insertAction(self._action['capture'], self._action['crop'])

        self._action['regarea'] = QAction('Registration area', self)
        self._action['regarea'].setCheckable(True)
        self._action['regarea'].triggered.connect(lambda: self.setRegistrationBoxVisibility(self._action['regarea'].isChecked()))
        self._action['regarea'].setVisible(False)
        self._popup.insertAction(self._action['capture'], self._action['regarea'])

        self._menuFloat = QMenu('Moving volume display', self._popup)
        self._menuFloatGroup = QActionGroup(self._popup)
        self._menuFloatGroup.setExclusive(True)
        self._action['displaynative'] = QAction('Native', self)
        self._action['displayedge'] = QAction('Edge', self)
        self._action['displayall'] = QAction('Edge and native', self)
        self._action['displaynative'].setCheckable(True)
        self._action['displayedge'].setCheckable(True)
        self._action['displayall'].setCheckable(True)
        self._action['displaynative'].triggered.connect(self.displayNative)
        self._action['displayedge'].triggered.connect(self.displayEdge)
        self._action['displayall'].triggered.connect(self.displayEdgeAndNative)
        self._menuFloatGroup.addAction(self._action['displaynative'])
        self._menuFloatGroup.addAction(self._action['displayedge'])
        self._menuFloatGroup.addAction(self._action['displayall'])
        self._menuFloat.addAction(self._action['displaynative'])
        self._menuFloat.addAction(self._action['displayedge'])
        self._menuFloat.addAction(self._action['displayall'])
        self._action['displaynative'].setChecked(True)
        self._popup.insertMenu(self._popup.actions()[6], self._menuFloat)

        self.popupToolsDisabled()
        self.popupVisibilityDisabled()
        self.popupOrientationDisabled()
        self.popupColorbarPositionDisabled()

        # Viewport tooltip

        self._tooltipstr = 'Coregistration controls:\n' \
                           '\tPress left mouse button and move mouse,\n' \
                           '\tIf the mouse is close to center of the image,\n' \
                           '\ttranslations are applied by dragging, otherwise\n' \
                           '\trotations are applied.\n' \
                           'Crop box and registration area controls:\n' \
                           '\tPress right mouse button inside crop box and move mouse to drag it,\n' \
                           '\tPress left mouse button on crop box edge and move mouse to change its size.\n' + self._tooltipstr
        self._trftooltip = 'Translations:\tX {:.1f} mm Y {:.1f} mm Z {:.1f} mm\n' \
                           'Rotations:\tX {:.1f}° Y {:.1f}° Z {:.1f}°\n\n' + self._tooltipstr
        self._tooltipstr = self._trftooltip.format(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

    # Private method

    def _initRegistrationBox(self):
        self._regbox = BoxWidget('RegAreaBox')
        self._regbox.CreateDefaultRepresentation()
        r = self._regbox.GetBorderRepresentation()
        r.SetPosition(0.0, 0.0)
        r.SetPosition2(1.0, 1.0)
        r.SetMinimumSize(10, 10)
        r.SetTolerance(20)
        r.VisibilityOn()
        r.SetShowBorderToOn()
        r.ProportionalResizeOn()
        r.GetBorderProperty().SetColor(self._lcolor)
        r.GetBorderProperty().SetOpacity(1.0)
        r.GetBorderProperty().SetLineWidth(self._lwidth)
        self._regbox.SelectableOn()
        self._regbox.ResizableOn()
        self._regbox.setProportionalResize(False)
        self._regbox.SetInteractor(self._interactor)
        self._regbox.AddObserver('InteractionEvent', self._regboxChanged)
        self._regbox.GetEventTranslator().SetTranslation(vtkCommand.LeftButtonPressEvent, vtkWidgetEvent.Select)
        self._regbox.GetEventTranslator().SetTranslation(vtkCommand.LeftButtonPressEvent, vtkWidgetEvent.Translate)
        self._regbox.GetEventTranslator().SetTranslation(vtkCommand.LeftButtonReleaseEvent, vtkWidgetEvent.EndSelect)
        self._regbox.SetEnabled(False)

    def _addReslice(self, volume, alpha):
        mapper = vtkImageResliceMapper()
        mapper.BorderOff()
        mapper.SliceAtFocalPointOn()
        mapper.SliceFacesCameraOn()
        mapper.SetInputData(volume.getVTKImage())
        slc = vtkImageSlice()
        slc.SetMapper(mapper)
        slc.SetOrigin(volume.getCenter())
        """
            Apply centered transform if exists, center of rotation = center of volume (SisypheVolume.getCenter())
            or align origins, if origins are not (0.0, 0.0, 0.0)
            or align centers of images
        """
        # Apply co-registration transform if exists
        if volume.hasTransform(self._volume.getID()):
            trf = volume.getTransformFromID(self._volume.getID())
            if not trf.isIdentity():
                # Affine forward transform
                t = trf.getTranslations()
                r = trf.getRotations()
                slc.SetPosition(t[0], t[1], t[2])
                if r is not None: slc.SetOrientation(r[0], r[1], r[2])
        else:
            # Revision 15/04/2023
            # Apply translations to align origins
            if not (self._volume.isDefaultOrigin() or volume.isDefaultOrigin()):
                vo = self._volume.getOrigin()
                oo = volume.getOrigin()
                slc.SetPosition((vo[0] - oo[0], vo[1] - oo[1], vo[2] - oo[2]))
            elif not volume.hasSameFieldOfView(self._volume):
                # Revision 15/04/2023
                # Apply translations to align centers of images
                if self._aligncenters:
                    cv = self._volume.getCenter()
                    co = volume.getCenter()
                    slc.SetPosition((cv[0]-co[0], cv[1]-co[1], cv[2]-co[2]))
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._stack.AddImage(slc)
        return slc

    def _updateCameraOrientation(self):
        super()._updateCameraOrientation()
        self._cropboxChanged(None, None)

    def _cropboxChanged(self, widget, event):
        if self._crop and len(self._ovlslices) > 0:
            xmax, ymax, zmax = self._volume.getFieldOfView()
            x, y = self._cropbox.getPosition()
            x, y = self._getDisplayFromNormalizedViewport(x, y)
            p = self._getWorldFromDisplay(x, y)
            x1, y1, z1 = p[0], p[1], p[2]
            if x1 < 0: x1 = 0
            elif x1 > xmax: x1 = int(xmax)
            if y1 < 0: y1 = 0
            elif y1 > ymax: y1 = int(ymax)
            if z1 < 0: z1 = 0
            elif z1 > zmax: z1 = int(zmax)
            wx, wy = self._cropbox.getSize()
            wx, wy = self._getDisplayFromNormalizedViewport(wx, wy)
            pw = self._getWorldFromDisplay(x + wx, y + wy)
            x2, y2, z2 = int(pw[0]), int(pw[1]), int(pw[2])
            x1, y1, z1 = int(x1), int(y1), int(z1)
            if x2 < 0: x2 = 0
            elif x2 > xmax: x2 = int(xmax)
            if y2 < 0: y2 = 0
            elif y2 > ymax: y2 = int(ymax)
            if z2 < 0: z2 = 0
            elif z2 > zmax: z2 = int(zmax)
            if self._orient == self._DIM0: self._volumeslice.GetMapper().SetCroppingRegion(x2, x1, y1, y2, 0, 500)
            elif self._orient == self._DIM1: self._volumeslice.GetMapper().SetCroppingRegion(x2, x1, 0, 500, z1, z2)
            else: self._volumeslice.GetMapper().SetCroppingRegion(0, 500, y2, y1, z1, z2)

    def _regboxChanged(self, widget, event):
        a1, b1 = self._regbox.GetBorderRepresentation().GetPosition()
        a2, b2 = self._regbox.GetBorderRepresentation().GetPosition2()
        """
            x2 = a1
            y1 = b1
            x1 = a2 + x2 = a1 + a2
            y2 = b2 + y1 = b1 + b2
    
            p1 = self._getDisplayFromNormalizedViewport(x1, y1)
            p1 = self._getWorldFromDisplay(p1[0], p1[1])
            p2 = self._getDisplayFromNormalizedViewport(x2, y2)
            p2 = self._getWorldFromDisplay(p2[0], p2[1])
        """
        p1 = self._getDisplayFromNormalizedViewport(a1 + a2, b1)
        p1 = self._getWorldFromDisplay(p1[0], p1[1])
        p2 = self._getDisplayFromNormalizedViewport(a1, b1 + b2)
        p2 = self._getWorldFromDisplay(p2[0], p2[1])
        if self._orient == 0:  # axial
            self._regarea[0] = p1[0]  # x
            self._regarea[1] = p1[1]  # y
            self._regarea[3] = p2[0] - p1[0]  # width
            self._regarea[4] = p2[1] - p1[1]  # height
        elif self._orient == 1:  # Coronal
            self._regarea[0] = p1[0]  # x
            self._regarea[2] = p1[2]  # z
            self._regarea[3] = p2[0] - p1[0]  # width
            self._regarea[5] = p2[2] - p1[2]  # depth
        else:  # Sagittal
            self._regarea[1] = p1[1]  # y
            self._regarea[2] = p1[2]  # z
            self._regarea[4] = p2[1] - p1[1]  # height
            self._regarea[5] = p2[2] - p1[2]  # depth
        self.RegistrationBoxChanged.emit(self, self._regarea)

    def _addSlice(self, volume, alpha):
        mapper = vtkImageSliceMapper()
        mapper.BorderOff()
        mapper.SliceAtFocalPointOn()
        mapper.SliceFacesCameraOn()
        mapper.SetInputData(volume.getVTKImage())
        slc = vtkImageSlice()
        slc.SetMapper(mapper)
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._stack.AddImage(slc)
        return slc

    def _updateTooltip(self):
        r = self.getRotations(deg=True)
        tr = self.getTranslations()
        self._tooltipstr = self._trftooltip.format(tr[0], tr[1], tr[2], r[0], r[1], r[2])
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

    # Public synchronisation event method

    def synchroniseCropChanged(self, obj, v):
        if obj != self and self.hasVolume():
            self.setCrop(v, signal=False)

    def synchroniseRegistrationBoxVisibilityChanged(self, obj, v):
        if self != obj and self.hasVolume():
            self.setRegistrationBoxVisibility(v, signal=False)

    def synchroniseRegistrationBoxChanged(self, obj, area):
        if self != obj and self.hasVolume():
            self.setRegistrationBoxArea(area, signal=False)

    # Overridden methods to update registration box area when viewport changes

    def zoomIn(self):
        super().zoomIn()
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def zoomOut(self):
        super().zoomOut()
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def zoomDefault(self):
        super().zoomDefault()
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def setZoom(self, z, signal=True):
        super().setZoom(z, signal)
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def setCameraPlanePosition(self, p, signal=True):
        super().setCameraPlanePosition(p, signal)
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def sliceMinus(self):
        super().sliceMinus()
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    def slicePlus(self):
        super().slicePlus()
        if self.getRegistrationBoxVisibility():
            self.setRegistrationBoxArea(self._regarea, signal=False)

    # Public methods

    def setVolume(self, volume):
        super().setVolume(volume)
        fov = volume.getFieldOfView()
        self._regarea = [0.0, 0.0, 0.0, fov[0], fov[1], fov[2]]

    def addOverlay(self, volume, gradient=None, alpha=0.5):
        super().addOverlay(volume, alpha)
        if gradient is None or not isinstance(gradient, SisypheVolume):
            img = GradientMagnitudeRecursiveGaussian(self._volume.getSITKImage())
            gradient = SisypheVolume(img)
            gradient.getDisplay().getLUT().setLutToHot()
            rmin, rmax = gradient.getDisplay().getRange()
            w = (rmax - rmin) / 15
            wmin = rmin + w
            wmax = rmax - 2 * w
            gradient.getDisplay().setWindow(wmin, wmax)
            gradient.getDisplay().getLUT().setDisplayBelowRangeColorOn()
        super().addOverlay(gradient, alpha)
        self._ovlslices[1].SetVisibility(False)
        self._action['crop'].setVisible(True)
        self._updateTooltip()

    def removeOverlay(self, o):
        super().removeOverlay(o)
        self._action['crop'].setVisible(len(self._ovl) > 0)

    def removeAllOverlays(self):
        super().removeAllOverlays()
        self._action['crop'].setVisible(False)

    def setCrop(self, crop, signal=True):
        if isinstance(crop, bool):
            self._crop = crop
            if crop and len(self._ovlslices) > 0:
                self._action['crop'].setChecked(True)
                self._cropbox = BoxWidget('RegCropBox')
                self._cropbox.CreateDefaultRepresentation()
                r = self._cropbox.GetBorderRepresentation()
                r.SetPosition(0.4, 0.4)
                w, h = self._getDisplayFromNormalizedViewport(0.2, 0.2)
                w, h = self._getNormalizedViewportFromDisplay(w, w)
                r.SetPosition2(w, h)
                r.SetMinimumSize(10, 10)
                r.SetTolerance(20)
                r.VisibilityOn()
                r.SetShowBorderToOn()
                r.ProportionalResizeOn()
                r.GetBorderProperty().SetColor(1.0, 1.0, 1.0)
                r.GetBorderProperty().SetOpacity(0.0)
                r.GetBorderProperty().SetLineWidth(self._lwidth)
                self._cropbox.SelectableOn()
                self._cropbox.ResizableOn()
                self._cropbox.setProportionalResize(True)
                self._cropbox.SetInteractor(self._interactor)
                self._cropbox.AddObserver('InteractionEvent', self._cropboxChanged)
                self._cropbox.GetEventTranslator().SetTranslation(vtkCommand.RightButtonPressEvent,
                                                                  vtkWidgetEvent.Select)
                self._cropbox.GetEventTranslator().SetTranslation(vtkCommand.RightButtonPressEvent,
                                                                  vtkWidgetEvent.Translate)
                self._cropbox.GetEventTranslator().SetTranslation(vtkCommand.RightButtonReleaseEvent,
                                                                  vtkWidgetEvent.EndSelect)
                self._cropboxChanged(None, None)
                self._cropbox.SetEnabled(True)
                self.registrationBoxOff()
            else:
                self._action['crop'].setChecked(False)
                if self._cropbox is not None:
                    self._cropbox.SetEnabled(0)
                    del self._cropbox
                    self._cropbox = None
            if self.hasOverlay():
                self._volumeslice.GetMapper().SetCropping(crop)
                if crop:
                    self._volumeslice.GetProperty().SetLayerNumber(100)
                    self._ovlslices[0].GetProperty().SetOpacity(1.0)
                else:
                    self._volumeslice.GetProperty().SetLayerNumber(0)
                    self._ovlslices[0].GetProperty().SetLayerNumber(1)
                    self._ovlslices[0].GetProperty().SetOpacity(0.25)
                self._renderwindow.Render()
            if signal: self.CropChanged.emit(self, crop)
        else: raise TypeError('parameter type {} is not bool'.format(type(crop)))

    def getCrop(self):
        return self._crop

    def cropOn(self, signal=True):
        self.setCrop(True, signal)

    def cropOff(self, signal=True):
        self.setCrop(False, signal)

    def setRegistrationBoxVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._action['regarea'].setChecked(True)
            if v:
                self._regbox.EnabledOn()
                self.cropOff()
            else:
                self._regbox.EnabledOff()
            self._renderwindow.Render()
            if signal: self.RegistrationBoxVisibilityChanged.emit(self, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getRegistrationBoxVisibility(self):
        return self._regbox.GetEnabled()

    def registrationBoxOn(self):
        self.setRegistrationBoxVisibility(True)

    def registrationBoxOff(self):
        self.setRegistrationBoxVisibility(False)

    def getRegistrationBoxWorldArea(self):
        return self._regarea

    def getRegistrationBoxMatrixArea(self):
        if self.hasVolume():
            fov = self._volume.getFieldOfView()
            if self._regarea != [0.0, 0.0, 0.0, fov[0], fov[1], fov[2]]:
                s = self._volume.getSize()
                sp = self._volume.getSpacing()
                x = int(self._regarea[0] / sp[0])
                y = int(self._regarea[1] / sp[1])
                z = int(self._regarea[2] / sp[2])
                w = int(self._regarea[3] / sp[0])
                h = int(self._regarea[4] / sp[1])
                d = int(self._regarea[5] / sp[2])
                if x < 0: x = 0
                if y < 0: y = 0
                if z < 0: z = 0
                sx = s[0] - 1
                sy = s[1] - 1
                sz = s[2] - 1
                if x > sx:
                    x = sx - 1
                    w = 1
                if y > sy:
                    y = sy - 1
                    h = 1
                if z > sz:
                    z = sz - 1
                    d = 1
                if x + w > sx: w = sx - x
                elif x + w == 0: w = 1
                if y + h > sy: h = sy - y
                elif y + h == 0: h = 1
                if z + d > sz: d = sz - z
                elif z + d == 0: d = 1
                return x, y, z, w, h, d
            else: return [0, 0, 0] + list(self._volume.getSize())
        else: raise ValueError('No fixed volume.')

    def getRegistrationBoxMaskArea(self):
        if self.hasVolume():
            r = self.getRegistrationBoxMatrixArea()
            default = [0, 0, 0] + list(self._volume.getSize())
            if r != default:
                s = self._volume.getSize()
                mask = zeros((s[2], s[1], s[0]), 'unit8')
                area = ones((r[5], r[4], r[3]), 'unit8')
                mask[r[2]:r[2]+r[5], r[1]:r[1]+r[4], r[0]:r[0]+r[3]] = area
                v = SisypheVolume()
                v.copyFromNumpyArray(mask, self._volume.getSpacing())
                v.copyAttributesFrom(self._volume, display=False, slope=False)
                v.setFilenamePrefix('mask_')
                return v
            else: return None
        else: raise ValueError('No fixed volume.')

    def setRegistrationBoxArea(self, area, signal=True):
        self._regarea = area
        p = self._getDisplayFromWorld(self._regarea[0],
                                      self._regarea[1],
                                      self._regarea[2])
        x1, y1 = self._getNormalizedViewportFromDisplay(p[0], p[1])
        p = self._getDisplayFromWorld(self._regarea[0] + self._regarea[3],
                                      self._regarea[1] + self._regarea[4],
                                      self._regarea[2] + self._regarea[5])
        x2, y2 = self._getNormalizedViewportFromDisplay(p[0], p[1])
        w = x1 - x2
        h = y2 - y1
        self._regbox.GetBorderRepresentation().SetPosition(x2, y1)
        self._regbox.GetBorderRepresentation().SetPosition2(w, h)
        self._renderwindow.Render()
        if signal: self.RegistrationBoxChanged.emit(self, self._regarea)

    def popupCropEnabled(self):
        self._action['crop'].setVisible(True)

    def popupCropDisabled(self):
        self._action['crop'].setVisible(False)

    def displayEdge(self):
        if self.hasVolume():
            self._action['displayedge'].setChecked(True)
            self.setVolumeVisibility(False, signal=True)             # volume OFF
            self.setOverlayVisibility(1, True, signal=True)     # Edge volume ON

    def displayNative(self):
        if self.hasVolume():
            self._action['displaynative'].setChecked(True)
            self.setVolumeVisibility(True, signal=True)              # volume ON
            self.setOverlayVisibility(1, False, signal=True)    # Edge volume OFF

    def displayEdgeAndNative(self):
        if self.hasVolume():
            self._action['displayall'].setChecked(True)
            self.setVolumeVisibility(True, signal=True)              # volume ON
            self.setOverlayVisibility(1, True, signal=True)     # Edge volume ON

    # Qt event

    def showEvent(self, event):
        super().showEvent(event)
        self.setRegistrationBoxArea(self._regarea, signal=False)

    # Private event method

    def _onRightPressEvent(self, obj, evt_name):  # Override AbstractViewWidget method
        if self._menuflag:
            interactorstyle = self._window.GetInteractorStyle()
            x, y = interactorstyle.GetLastPos()
            p = self._getScreenFromDisplay(x, y)
            self._popup.popup(p)


class SliceROIViewWidget(SliceOverlayViewWidget):
    """
        SliceROIViewWidget class

        Description

            Derived from SliceOverlayViewWidget class. Adds ROI management.

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> SliceROIViewWidget

        Private attributes

            _rois           SisypheROICollection
            _activeroi      str name of active SisypheROI
            _roimapper      vtkImageSliceMapper of the active roi vtkImageSlice instance
            _activesliceroi vtkImageSlice instance of active SisypheROI
            _slicerois      vtkImageSlice instance of inactive SisypheROI
            _draw           SisypheROIDraw instance
            _circle         vtkRegularPolygonSource, brush circle source
            _brush          vtkActor, circle brush representation
            _brushFlag      bool, brush flag (active/inactive) for mouse event

        Custom Qt signals

            ROIModified.emit(QWidget)
            ROISelectionChanged.emit(QWidget, str)
            ROIAttributesChanged.emit(QWidget)
            BrushRadiusChanged.emit(QWidget, int)
            ROIFlagChanged.emit(QWidget, str, object)
            ROINameChanged.emit(str, str)
            ROIListChanged.emit(str)

        Public Qt event synchronisation methods

            synchroniseROISelectionChanged(QWidget, str)
            synchroniseROIAttributesChanged(QWidget)
            synchroniseROIModified(QWidget)
            synchroniseBrushRadiusChanged(QWidget, int)
            synchroniseROIFlagChanged(QWidget, str, object)

        Public methods

            getSliceIndex()             Get current slice index
            addROI(SisypheROI)
            newROI()
            loadROI(str)
            int = getNumberOfROI()
            bool = hasROI()
            removeROI(str ou SisypheROI)
            removeAllROI()
            setActiveROI(str)
            SisypheROI = getActiveROI()
            setActiveROI(str | SisypheROI)
            SisypheROI = getROI(str)
            list() = getROINames()
            updateRoiName(str, str)
            SisypheROICollection = getROICollection()
            setROICollection(SisypheROICollection)
            SisypheROIDraw = getDrawInstance()
            setDrawInstance(SisypheROIDraw)
            setBrushRadius(int)
            int = getBrushRadius()
            setMorphologyRadius(int)
            int = getMorphologyRadius()
            setBrushVisibility(bool)
            bool = getBrushVisibility()
            setBrushVisibilityOn()
            setBrushVisibilityOff()
            setROIVisibility(bool)
            setROIVisibilityOn()
            setROIVisibilityOff()
            bool = getROIVisibility()
            setROIMenuVisibility(bool)
            setROIMenuVisibilityOn()
            setROIMenuVisibilityOff()
            bool = getROIMenuVisibility()
            setNoROIFlag()
            setSolidBrushFlag(bool)
            setSolidBrushFlagOn()
            setSolidBrushFlagOff()
            bool = getSolidBrushFlag()
            setSolidBrush3Flag(bool)
            setSolidBrush3FlagOn()
            setSolidBrush3FlagOff()
            bool = getSolidBrush3Flag()
            setThresholdBrushFlag(bool)
            setThresholdBrushFlagOn()
            setThresholdBrushFlagOff()
            bool = getThresholdBrushFlag()
            setThresholdBrush3Flag(bool)
            setThresholdBrush3FlagOn()
            setThresholdBrush3FlagOff()
            bool = getThresholdBrush3Flag()
            bool = getBrushFlag()
            bool = get2DBrushFlag()
            bool = get3DBrushFlag()
            setFillHolesFlag(bool)
            setFillHolesFlagOn()
            setFillHolesFlagOff()
            bool = getFillHolesFlag()
            set2DBlobDilateFlagOn()
            set2DBlobErodeFlagOn()
            set2DBlobCloseFlagOn()
            set2DBlobOpenFlagOn()
            set2DBlobCopyFlagOn()
            set2DBlobCutFlagOn()
            set2DBlobPasteFlagOn()
            set2DBlobRemoveFlagOn()
            set2DBlobKeepFlagOn()
            set2DBlobThresholdFlagOn()
            set2DFillFlagOn()
            set2DRegionGrowingFlagOn()
            set2DBlobRegionGrowingFlagOn()
            set2DRegionConfidenceFlagOn()
            set2DBlobRegionConfidenceFlagOn()
            set3DBlobDilateFlagOn()
            set3DBlobErodeFlagOn()
            set3DBlobCloseFlagOn()
            set3DBlobOpenFlagOn()
            set3DBlobCopyFlagOn()
            set3DBlobCutFlagOn()
            set3DBlobPasteFlagOn()
            set3DBlobRemoveFlagOn()
            set3DBlobKeepFlagOn()
            set3DBlobExpandFlagOn()
            set3DBlobShrinkFlagOn()
            set3DBlobThresholdFlagOn()
            set3DFillFlagOn()
            set3DRegionGrowingFlagOn()
            set3DBlobRegionGrowingFlagOn()
            set3DRegionConfidenceFlagOn()
            set3DBlobRegionConfidenceFlagOn()
            setActiveContourFlagOn()
            setUndo(bool)
            bool = getUndo()
            setUndoOn()
            setUndoOff()
            undo()
            redo()
            updateROIDisplay()
            updateROIAttributes()
            QMenu = getPopupROI()
            popupROIEnabled()
            popupROIDisabled()
            sliceFlip(bool, bool)
            sliceMove(int, int)
            sliceDilate()
            sliceErode()
            sliceOpen()
            sliceClose()
            sliceBackground()
            sliceObject()
            sliceInvert()
            sliceClear()
            roiDilate()
            roiErode()
            roiOpen()
            roiClose()
            roiBackground()
            roiObject()
            roiInvert()
            roiClear()

            inherited SliceOverlayViewWidget methods
            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods

        Revision:

            03/08/2023  Add setNoROIFlag() method
    """

    # Custom Qt signals

    ROIModified = pyqtSignal(QWidget)
    ROISelectionChanged = pyqtSignal(QWidget, str)
    ROIAttributesChanged = pyqtSignal(QWidget)
    BrushRadiusChanged = pyqtSignal(QWidget, int)
    ROIFlagChanged = pyqtSignal(QWidget, str, object)
    ROINameChanged = pyqtSignal(str, str)
    ROIListChanged = pyqtSignal(str)

    # Special method

    def __init__(self, overlays=None, rois=None, draw=None, parent=None):
        super().__init__(overlays, parent)

        # Class attributes

        # SisypheROICollection
        if rois is not None and isinstance(rois, SisypheROICollection): self._rois = rois
        else: self._rois = SisypheROICollection()

        # SisypheROIDraw, draw functions for active roi
        if draw is not None and isinstance(draw, SisypheROIDraw): self._draw = draw
        else: self._draw = SisypheROIDraw()

        self._activeroi = None                  # str, name of active roi
        self._roimapper = None                  # mapper of the active roi vtkImageSlice
        self._activesliceroi = None             # vtkImageSlice, active roi
        self._slicerois = None                  # vtkImageSlice, inactive roi
        self._circle = None                     # vtkRegularPolygonSource, brush circle polydata
        self._brush = None                      # vtkActor, circle brush representation
        self._brushFlag0 = None

        self._initBrushActor()

        # Init popup menu

        self._action['newroi'] = QAction('New...', self)
        self._action['newroi'].triggered.connect(self.newROI)
        self._action['addroi'] = QAction('Load...', self)
        self._action['addroi'].triggered.connect(self.loadROI)
        self._action['removeroi'] = QAction('Remove active', self)
        self._action['removeroi'].triggered.connect(self.removeROI)
        self._action['removeallroi'] = QAction('Remove all', self)
        self._action['removeallroi'].triggered.connect(self.removeAllROI)
        self._action['saveroi'] = QAction('Save active', self)
        self._action['saveroi'].triggered.connect(self.saveROI)
        self._action['saverois'] = QAction('Save all', self)
        self._action['saverois'].triggered.connect(self.saveAllROI)
        self._action['undo'] = QAction('Undo', self)
        self._action['undo'].setShortcut(QKeySequence('Ctrl+Z'))
        self._action['undo'].setShortcutVisibleInContextMenu(True)
        self._action['undo'].triggered.connect(self.undo)
        self._action['redo'] = QAction('Redo', self)
        self._action['redo'].setShortcut(QKeySequence('Ctrl+Y'))
        self._action['redo'].setShortcutVisibleInContextMenu(True)
        self._action['redo'].triggered.connect(self.redo)
        self._action['brushflag'] = QAction('Solid disk brush', self)
        self._action['brushflag'].setCheckable(True)
        self._action['brushflag'].triggered.connect(
            lambda: self.setSolidBrushFlag(self._action['brushflag'].isChecked()))
        self._action['brushflag3'] = QAction('Solid sphere brush', self)
        self._action['brushflag3'].setCheckable(True)
        self._action['brushflag3'].triggered.connect(
            lambda: self.setSolidBrush3Flag(self._action['brushflag3'].isChecked()))
        self._action['thresholdbrush'] = QAction('Threshold disk brush', self)
        self._action['thresholdbrush'].setCheckable(True)
        self._action['thresholdbrush'].triggered.connect(
            lambda: self.setThresholdBrushFlag(self._action['thresholdbrush'].isChecked()))
        self._action['thresholdbrush3'] = QAction('Threshold sphere brush', self)
        self._action['thresholdbrush3'].setCheckable(True)
        self._action['thresholdbrush3'].triggered.connect(
            lambda: self.setThresholdBrush3Flag(self._action['thresholdbrush3'].isChecked()))
        self._action['fillholesflag'] = QAction('Automatic hole filling', self)
        self._action['fillholesflag'].setCheckable(True)
        self._action['fillholesflag'].triggered.connect(
            lambda: self.setFillHolesFlag(self._action['fillholesflag'].isChecked()))
        # 2D ROI actions
        self._action['2derode'] = QAction('Erode', self)
        self._action['2derode'].triggered.connect(self.sliceErode)
        self._action['2ddilate'] = QAction('Dilate', self)
        self._action['2ddilate'].triggered.connect(self.sliceDilate)
        self._action['2dopen'] = QAction('Opening', self)
        self._action['2dopen'].triggered.connect(self.sliceOpen)
        self._action['2dclose'] = QAction('Closing', self)
        self._action['2dclose'].triggered.connect(self.sliceClose)
        self._action['2dblobdilate'] = QAction('Dilate selected blob', self)
        self._action['2dblobdilate'].setCheckable(True)
        self._action['2dblobdilate'].triggered.connect(self.set2DBlobDilateFlagOn)
        self._action['2dbloberode'] = QAction('Erode selected blob', self)
        self._action['2dbloberode'].setCheckable(True)
        self._action['2dbloberode'].triggered.connect(self.set2DBlobErodeFlagOn)
        self._action['2dblobopen'] = QAction('Opening selected blob', self)
        self._action['2dblobopen'].setCheckable(True)
        self._action['2dblobopen'].triggered.connect(self.set2DBlobOpenFlagOn)
        self._action['2dblobclose'] = QAction('Closing selected blob', self)
        self._action['2dblobclose'].setCheckable(True)
        self._action['2dblobclose'].triggered.connect(self.set2DBlobCloseFlagOn)
        self._action['2dblobcopy'] = QAction('Copy selected blob', self)
        self._action['2dblobcopy'].setCheckable(True)
        self._action['2dblobcopy'].triggered.connect(self.set2DBlobCopyFlagOn)
        self._action['2dblobcut'] = QAction('Cut selected blob', self)
        self._action['2dblobcut'].setCheckable(True)
        self._action['2dblobcut'].triggered.connect(self.set2DBlobCutFlagOn)
        self._action['2dblobpaste'] = QAction('Paste selected blob', self)
        self._action['2dblobpaste'].setCheckable(True)
        self._action['2dblobpaste'].triggered.connect(self.set2DBlobPasteFlagOn)
        self._action['2dblobremove'] = QAction('Remove selected blob', self)
        self._action['2dblobremove'].setCheckable(True)
        self._action['2dblobremove'].triggered.connect(self.set2DBlobRemoveFlagOn)
        self._action['2dblobkeep'] = QAction('Keep only selected blob', self)
        self._action['2dblobkeep'].setCheckable(True)
        self._action['2dblobkeep'].triggered.connect(self.set2DBlobKeepFlagOn)
        self._action['2dblobthreshold'] = QAction('Thresholding in selected blob', self)
        self._action['2dblobthreshold'].setCheckable(True)
        self._action['2dblobthreshold'].triggered.connect(self.set2DBlobThresholdFlagOn)
        self._action['2dfill'] = QAction('Fill from seed pixel', self)
        self._action['2dfill'].setCheckable(True)
        self._action['2dfill'].triggered.connect(self.set2DFillFlagOn)
        self._action['2drgrowing'] = QAction('Region growing', self)
        self._action['2drgrowing'].setCheckable(True)
        self._action['2drgrowing'].triggered.connect(self.set2DRegionGrowingFlagOn)
        self._action['2dblobrgrowing'] = QAction('Region growing in selected blob', self)
        self._action['2dblobrgrowing'].setCheckable(True)
        self._action['2dblobrgrowing'].triggered.connect(self.set2DBlobRegionGrowingFlagOn)
        self._action['2drconfidence'] = QAction('Region growing confidence', self)
        self._action['2drconfidence'].setCheckable(True)
        self._action['2drconfidence'].triggered.connect(self.set2DRegionConfidenceFlagOn)
        self._action['2dblobrconfidence'] = QAction('Region growing confidence in selected blob', self)
        self._action['2dblobrconfidence'].setCheckable(True)
        self._action['2dblobrconfidence'].triggered.connect(self.set2DBlobRegionConfidenceFlagOn)
        self._action['2dobject'] = QAction('Segment object', self)
        self._action['2dobject'].triggered.connect(self.sliceObject)
        self._action['2dback'] = QAction('Segment background', self)
        self._action['2dback'].triggered.connect(self.sliceBackground)
        self._action['2dinvert'] = QAction('Invert slice', self)
        self._action['2dinvert'].triggered.connect(self.sliceInvert)
        self._action['2dclear'] = QAction('Clear slice', self)
        self._action['2dclear'].triggered.connect(self.sliceClear)
        # 3D ROI actions
        self._action['3derode'] = QAction('Erode', self)
        self._action['3derode'].triggered.connect(self.roiErode)
        self._action['3ddilate'] = QAction('Dilate', self)
        self._action['3ddilate'].triggered.connect(self.roiDilate)
        self._action['3dopen'] = QAction('Opening', self)
        self._action['3dopen'].triggered.connect(self.roiOpen)
        self._action['3dclose'] = QAction('Closing', self)
        self._action['3dclose'].triggered.connect(self.roiClose)
        self._action['3dblobdilate'] = QAction('Dilate selected blob', self)
        self._action['3dblobdilate'].setCheckable(True)
        self._action['3dblobdilate'].triggered.connect(self.set3DBlobDilateFlagOn)
        self._action['3dbloberode'] = QAction('Erode selected blob', self)
        self._action['3dbloberode'].setCheckable(True)
        self._action['3dbloberode'].triggered.connect(self.set3DBlobErodeFlagOn)
        self._action['3dblobopen'] = QAction('Opening selected blob', self)
        self._action['3dblobopen'].setCheckable(True)
        self._action['3dblobopen'].triggered.connect(self.set3DBlobOpenFlagOn)
        self._action['3dblobclose'] = QAction('Closing selected blob', self)
        self._action['3dblobclose'].setCheckable(True)
        self._action['3dblobclose'].triggered.connect(self.set3DBlobCloseFlagOn)
        self._action['3dblobcopy'] = QAction('Copy selected blob', self)
        self._action['3dblobcopy'].setCheckable(True)
        self._action['3dblobcopy'].triggered.connect(self.set3DBlobCopyFlagOn)
        self._action['3dblobcut'] = QAction('Cut selected blob', self)
        self._action['3dblobcut'].setCheckable(True)
        self._action['3dblobcut'].triggered.connect(self.set3DBlobCutFlagOn)
        self._action['3dblobpaste'] = QAction('Paste selected blob', self)
        self._action['3dblobpaste'].setCheckable(True)
        self._action['3dblobpaste'].triggered.connect(self.set3DBlobPasteFlagOn)
        self._action['3dblobremove'] = QAction('Remove selected blob', self)
        self._action['3dblobremove'].setCheckable(True)
        self._action['3dblobremove'].triggered.connect(self.set3DBlobRemoveFlagOn)
        self._action['3dblobkeep'] = QAction('Keep only selected blob', self)
        self._action['3dblobkeep'].setCheckable(True)
        self._action['3dblobkeep'].triggered.connect(self.set3DBlobKeepFlagOn)
        self._action['3dblobexpand'] = QAction('Expand selected blob', self)
        self._action['3dblobexpand'].setCheckable(True)
        self._action['3dblobexpand'].triggered.connect(self.set3DBlobExpandFlagOn)
        self._action['3dblobshrink'] = QAction('Shrink selected blob', self)
        self._action['3dblobshrink'].setCheckable(True)
        self._action['3dblobshrink'].triggered.connect(self.set3DBlobShrinkFlagOn)
        self._action['3dblobthreshold'] = QAction('Thresholding in selected blob', self)
        self._action['3dblobthreshold'].setCheckable(True)
        self._action['3dblobthreshold'].triggered.connect(self.set3DBlobThresholdFlagOn)
        self._action['3dfill'] = QAction('Fill from seed voxel', self)
        self._action['3dfill'].setCheckable(True)
        self._action['3dfill'].triggered.connect(self.set2DFillFlagOn)
        self._action['3drgrowing'] = QAction('Region growing', self)
        self._action['3drgrowing'].setCheckable(True)
        self._action['3drgrowing'].triggered.connect(self.set3DRegionGrowingFlagOn)
        self._action['3dblobrgrowing'] = QAction('Region growing in selected blob', self)
        self._action['3dblobrgrowing'].setCheckable(True)
        self._action['3dblobrgrowing'].triggered.connect(self.set3DBlobRegionGrowingFlagOn)
        self._action['3drconfidence'] = QAction('Region growing confidence', self)
        self._action['3drconfidence'].setCheckable(True)
        self._action['3drconfidence'].triggered.connect(self.set3DRegionConfidenceFlagOn)
        self._action['3dblobrconfidence'] = QAction('Region growing confidence in selected blob', self)
        self._action['3dblobrconfidence'].setCheckable(True)
        self._action['3dblobrconfidence'].triggered.connect(self.set3DBlobRegionConfidenceFlagOn)
        self._action['activecontour'] = QAction('Active contour')
        self._action['activecontour'].setCheckable(True)
        self._action['activecontour'].triggered.connect(self.setActiveContourFlagOn)
        self._action['3dobject'] = QAction('Segment object', self)
        self._action['3dobject'].triggered.connect(self.roiObject)
        self._action['3dback'] = QAction('Segment background', self)
        self._action['3dback'].triggered.connect(self.roiBackground)
        self._action['3dinvert'] = QAction('Invert', self)
        self._action['3dinvert'].triggered.connect(self.roiInvert)
        self._action['3dclear'] = QAction('Clear', self)
        self._action['3dclear'].triggered.connect(self.roiClear)
        self._action['showROI'] = QAction('Show ROI', self)
        self._action['showROI'].setCheckable(True)
        self._action['showROI'].triggered.connect(
            lambda: self.setROIVisibility(self._action['showROI'].isChecked()))

        self._2d = QMenu('2D functions', self._popup)
        self._2d.addAction(self._action['2derode'])
        self._2d.addAction(self._action['2ddilate'])
        self._2d.addAction(self._action['2dopen'])
        self._2d.addAction(self._action['2dclose'])
        self._2d.addSeparator()
        self._2d.addAction(self._action['2dbloberode'])
        self._2d.addAction(self._action['2dblobdilate'])
        self._2d.addAction(self._action['2dblobopen'])
        self._2d.addAction(self._action['2dblobclose'])
        self._2d.addSeparator()
        self._2d.addAction(self._action['2dblobcopy'])
        self._2d.addAction(self._action['2dblobcut'])
        self._2d.addAction(self._action['2dblobpaste'])
        self._2d.addAction(self._action['2dblobremove'])
        self._2d.addAction(self._action['2dblobkeep'])
        self._2d.addSeparator()
        self._2d.addAction(self._action['2dblobthreshold'])
        self._2d.addAction(self._action['2drgrowing'])
        self._2d.addAction(self._action['2dblobrgrowing'])
        self._2d.addAction(self._action['2drconfidence'])
        self._2d.addAction(self._action['2dblobrconfidence'])
        self._2d.addSeparator()
        self._2d.addAction(self._action['2dfill'])
        self._2d.addAction(self._action['2dobject'])
        self._2d.addAction(self._action['2dback'])
        self._2d.addAction(self._action['2dinvert'])
        self._2d.addAction(self._action['2dclear'])

        self._3d = QMenu('3D functions', self._popup)
        self._3d.addAction(self._action['3derode'])
        self._3d.addAction(self._action['3ddilate'])
        self._3d.addAction(self._action['3dopen'])
        self._3d.addAction(self._action['3dclose'])
        self._3d.addSeparator()
        self._3d.addAction(self._action['3dbloberode'])
        self._3d.addAction(self._action['3dblobdilate'])
        self._3d.addAction(self._action['3dblobopen'])
        self._3d.addAction(self._action['3dblobclose'])
        self._3d.addSeparator()
        self._3d.addAction(self._action['3dblobthreshold'])
        self._3d.addAction(self._action['3drgrowing'])
        self._3d.addAction(self._action['3dblobrgrowing'])
        self._3d.addAction(self._action['3drconfidence'])
        self._3d.addAction(self._action['3dblobrconfidence'])
        self._3d.addAction(self._action['activecontour'])
        self._3d.addSeparator()
        self._3d.addAction(self._action['3dblobcopy'])
        self._3d.addAction(self._action['3dblobcut'])
        self._3d.addAction(self._action['3dblobpaste'])
        self._3d.addAction(self._action['3dblobremove'])
        self._3d.addAction(self._action['3dblobkeep'])
        self._3d.addSeparator()
        self._3d.addAction(self._action['3dblobthreshold'])
        self._3d.addAction(self._action['3drgrowing'])
        self._3d.addAction(self._action['3dblobrgrowing'])
        self._3d.addAction(self._action['3drconfidence'])
        self._3d.addAction(self._action['3dblobrconfidence'])
        self._3d.addAction(self._action['activecontour'])
        self._3d.addSeparator()
        self._3d.addAction(self._action['3dfill'])
        self._3d.addAction(self._action['3dobject'])
        self._3d.addAction(self._action['3dback'])
        self._3d.addAction(self._action['3dinvert'])
        self._3d.addAction(self._action['3dclear'])

        self._currentroi = QMenu('Set active ROI', self._popup)
        self._roigroup = None

        self._roitools = QMenu('ROI', self._popup)
        self._roitools.addAction(self._action['newroi'])
        self._roitools.addAction(self._action['addroi'])
        self._roitools.addAction(self._action['removeroi'])
        self._roitools.addAction(self._action['removeallroi'])
        self._roitools.addAction(self._action['saveroi'])
        self._roitools.addAction(self._action['saverois'])
        self._roitools.addMenu(self._currentroi)
        self._roitools.addSeparator()
        self._roitools.addAction(self._action['brushflag'])
        self._roitools.addAction(self._action['thresholdbrush'])
        self._roitools.addAction(self._action['brushflag3'])
        self._roitools.addAction(self._action['thresholdbrush3'])
        self._roitools.addAction(self._action['fillholesflag'])
        self._roitools.addSeparator()
        self._roitools.addMenu(self._2d)
        self._roitools.addMenu(self._3d)
        self._roitools.addSeparator()
        self._roitools.addAction(self._action['undo'])
        self._roitools.addAction(self._action['redo'])

        self._popup.insertMenu(self._popup.actions()[7], self._roitools)
        self._menuVisibility.insertAction(self._menuVisibility.actions()[4], self._action['showROI'])
        self.setROIMenuVisibilityOff()

        # Viewport tooltip

        self._tooltipstr += '\n\nBrush control:\n' \
                            '\tLeft click to brush, Right click to erase in draw mode,\n' \
                            '\tMouseWheel + Alt Key to change brush size.'
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

        # Timer

        self._timer = QTimer()
        self._timer.timeout.connect(self._onTimer)

    # Private methods

    def _initBrushActor(self):
        r = self._draw.getBrushRadius()  # + 0.5
        self._circle = vtkRegularPolygonSource()
        self._circle.GeneratePolygonOff()
        self._circle.SetNumberOfSides(int(10 * r))
        self._circle.SetRadius(r)
        self._circle.SetCenter(0, 0, 0)
        if self._orient == 0: self._circle.SetNormal(0.0, 0.0, 1.0)
        elif self._orient == 1: self._circle.SetNormal(0.0, 1.0, 0.0)
        elif self._orient == 2: self._circle.SetNormal(1.0, 0.0, 0.0)
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(self._circle.GetOutputPort())
        mapper.ScalarVisibilityOff()
        self._brush = vtkActor()
        self._brush.SetMapper(mapper)
        self._brush.GetProperty().EdgeVisibilityOn()
        self._brush.GetProperty().SetLineWidth(self._lwidth)
        self._brush.GetProperty().SetColor(1.0, 1.0, 1.0)
        self._renderer.AddActor(self._brush)

    def _updateActiveSliceROI(self):
        if self._activeroi is not None:
            # delete previous self._activesliceroi vtkImageSlice
            if self._activesliceroi is not None:
                if self._stack.HasImage(self._activesliceroi): self._stack.RemoveImage(self._activesliceroi)
                del self._activesliceroi
                self._activesliceroi = None
            # delete r mapper
            if self._roimapper is not None:
                del self._roimapper
                self._roimapper = None
            if self.hasROI():
                # create new self._activesliceroi vtkImageSlice and vtkImageSliceMapper
                roi = self._rois[self._activeroi]
                self._roimapper = vtkImageSliceMapper()
                self._roimapper.BorderOff()
                self._roimapper.SliceAtFocalPointOn()
                self._roimapper.SliceFacesCameraOn()
                self._roimapper.SetInputData(roi.getVTKImage())
                self._activesliceroi = vtkImageSlice()
                self._activesliceroi.SetMapper(self._roimapper)
                self._activesliceroi.SetVisibility(roi.getVisibility())
                prop = self._activesliceroi.GetProperty()
                prop.SetLayerNumber(51)
                prop.SetInterpolationTypeToNearest()
                prop.SetLookupTable(roi.getvtkLookupTable())
                prop.UseLookupTableScalarRangeOn()
                prop.SetOpacity(roi.getAlpha())
                self._stack.AddImage(self._activesliceroi)
            else: self._activeroi = None

    def _updateSliceROI(self):
        if self._slicerois is not None:
            # delete previous non active rois vtkImageSlice (self._slicerois)
            if self._stack.HasImage(self._slicerois): self._stack.RemoveImage(self._slicerois)
            del self._slicerois
            self._slicerois = None
        if self.getNumberOfROI() > 1:
            # create new non-active rois vtkImageSlice (self._slicerois)
            blend = vtkImageBlend()
            blend.SetBlendModeToCompound()
            blend.CompoundAlphaOn()
            index = 0
            for roi in self._rois:
                if roi.getName() != self._activeroi and roi.getVisibility():
                    rgb = vtkImageMapToColors()
                    rgb.SetOutputFormatToRGBA()
                    rgb.SetInputData(roi.getVTKImage())
                    rgb.SetLookupTable(roi.getvtkLookupTable())
                    rgb.Update()
                    blend.AddInputData(0, rgb.GetOutput())
                    blend.SetOpacity(index, 1.0)
                    index += 1
            if blend.GetNumberOfInputs() > 0:
                blend.Update()
                mapper = vtkImageSliceMapper()
                mapper.BorderOff()
                mapper.SliceAtFocalPointOn()
                mapper.SliceFacesCameraOn()
                mapper.SetInputData(blend.GetOutput())
                self._slicerois = vtkImageSlice()
                self._slicerois.SetMapper(mapper)
                prop = self._slicerois.GetProperty()
                prop.SetLayerNumber(50)
                prop.SetInterpolationTypeToNearest()
                prop.SetOpacity(self._rois[self._activeroi].getAlpha())
                self._stack.AddImage(self._slicerois)

    def _updateBrush(self):
        if self._volume is not None:
            r = self._draw.getBrushRadius()  # + 0.5
            self._circle.SetNumberOfSides(int(10 * r))
            self._circle.SetRadius(r * self._volume.getSpacing()[self._orient])
            if self._orient == 0: self._circle.SetNormal(0.0, 0.0, 1.0)
            elif self._orient == 1: self._circle.SetNormal(0.0, 1.0, 0.0)
            elif self._orient == 2: self._circle.SetNormal(1.0, 0.0, 0.0)
            self._circle.Update()
            if self._activeroi is not None:
                self._brush.GetProperty().SetColor(self._rois[self._activeroi].getColor())
            else: self._brush.SetVisibility(False)

    def _updateExclusiveFlags(self, flag=''):
        if isinstance(flag, str):
            flags = ['brushflag', 'thresholdbrush', 'brushflag3', 'thresholdbrush3', '2dblobdilate',
                     '2dbloberode', '2dblobopen', '2dblobclose', '2dblobcopy', '2dblobcut', '2dblobpaste',
                     '2dblobremove', '2dblobkeep', '2dblobthreshold', '2dfill', '2drgrowing', '2dblobrgrowing',
                     '2drconfidence', '2dblobrconfidence', '3dblobdilate', '3dbloberode', '3dblobopen', '3dblobclose',
                     '3dblobcopy', '3dblobcut', '3dblobpaste', '3dblobremove', '3dblobkeep', '3dblobexpand',
                     '3dblobshrink', '3dblobthreshold', '3dfill', '3drgrowing', '3dblobrgrowing', '3drconfidence',
                     '3dblobrconfidence', 'activecontour']
            if flag in flags:
                for f in flags:
                    self._action[f].setChecked(f == flag)
                if self.getBrushFlag():
                    self._brush.SetVisibility(True)
                    self.setDefaultMouseCursor()
                else:
                    self._brush.SetVisibility(False)
                    self.setCrossHairMouseCursor()
            else:
                for f in flags:
                    self._action[f].setChecked(False)
                    self._brush.SetVisibility(False)
                self.setDefaultMouseCursor()
        else: raise TypeError('parameter type {} is not str.'.format(type(flag)))

    def _updateROIMenu(self):
        self._currentroi.clear()
        if len(self._rois) > 0:
            self.setROIMenuVisibilityOn()
            self._roigroup = QActionGroup(self._popup)
            self._roigroup.setExclusive(True)
            for roi in self._rois:
                r = QAction(roi.getName(), self)
                self._roigroup.addAction(r)
                r.setCheckable(True)
                r.setChecked(self._activeroi == roi.getName())
                r.triggered.connect(lambda: self.setActiveROI(self._roigroup.checkedAction().text(), signal=True))
                self._currentroi.addAction(r)
        else: self.setROIMenuVisibilityOff()

    def _updateCameraOrientation(self):
        super()._updateCameraOrientation()
        self._updateBrush()
        if not self.isCurrentOrientationIsotropic(): self.setROIVisibilityOff()
        else: self.setROIVisibilityOn()

    def _getClickedMatrixCoordinate(self):
        last = self._window.GetInteractorStyle().GetLastPos()
        p = list(self._getWorldFromDisplay(last[0], last[1]))
        f = self._renderer.GetActiveCamera().GetFocalPoint()
        d = 2 - self._orient
        p[d] = f[d]
        p = self._getWorldToMatrixCoordinate(p)
        return p

    # Public synchronisation event methods

    def synchroniseROISelectionChanged(self, obj, r):
        if obj != self and self.hasVolume():
            self.setActiveROI(r, signal=False)

    def synchroniseROIAttributesChanged(self, obj):
        if obj != self and self.hasVolume():
            self.updateROIAttributes()

    def synchroniseROIModified(self, obj):
        if obj != self and self.hasVolume():
            self.updateROIDisplay()

    def synchroniseBrushRadiusChanged(self, obj, radius):
        if obj != self and self.hasVolume():
            self.setBrushRadius(radius, signal=False)

    def synchroniseROIFlagChanged(self, obj, function, param):
        if obj != self and self.hasVolume():
            f = getattr(self, function)
            if param is None: f(signal=False)
            else: f(param, signal=False)

    # Public methods

    def getSliceIndex(self):
        f = self._renderer.GetActiveCamera().GetFocalPoint()
        d = 2 - self._orient
        s = self._volume.getSpacing()
        return int(round(f[d] / s[d]))

    def removeVolume(self):
        self.removeAllROI()
        super().removeVolume()

    def setVolume(self, volume):
        super().setVolume(volume)
        self._draw.setVolume(volume)
        self._rois.setReferenceID(volume)
        self._updateBrush()
        self._brush.SetVisibility(False)

    def setROICollection(self, rois):
        if isinstance(rois, SisypheROICollection):
            self._rois = rois
            self.setActiveROI(self._rois[0].getName(), signal=False)
        else: raise TypeError('parameter type {} is not SisypheROICollection.'.format(type(rois)))

    def getROICollection(self):
        return self._rois

    def newROI(self):
        roi = SisypheROI(self._volume)
        roi.setAlpha(0.5)
        roi.setName('ROI' + str(len(self._rois)))
        self._rois.append(roi)
        self.setActiveROI(roi, signal=True)
        self.ROIListChanged.emit(roi.getName())
        if not self._action['showROI'].isChecked(): self._action['showROI'].setChecked(True)

    def addROI(self, roi):
        if isinstance(roi, SisypheROI):
            roi.setOrigin(self._volume.getOrigin())
            if roi.getName() == '': roi.setName('ROI' + str(len(self._rois)))
            self._rois.append(roi)
            self.setActiveROI(roi, signal=True)
            self.ROIListChanged.emit(roi.getName())
            if not self._action['showROI'].isChecked(): self._action['showROI'].setChecked(True)
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def loadROI(self, filenames=None):
        if isinstance(filenames, str): filenames = [filenames]
        if filenames is None:
            filt = 'SisypheROI (*{})'.format(SisypheROI.getFileExt())
            filenames = QFileDialog.getOpenFileNames(self, 'Load Sisyphe ROI',
                                                     dirname(self._volume.getFilename()), filt)
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        if filenames:
            for filename in filenames:
                roi = SisypheROI()
                try:
                    roi.load(filename)
                    if roi.getReferenceID() == self._volume.getID():
                        roi.setOrigin(self._volume.getOrigin())
                        self._rois.append(roi)
                        self.setActiveROI(roi, signal=True)
                        self.ROIListChanged.emit(roi.getName())
                        if not self._action['showROI'].isChecked(): self._action['showROI'].setChecked(True)
                    else: QMessageBox.warning(self, 'ROI ID is not same as reference volume.')
                except Exception as msg:
                    QMessageBox.warning(self, 'Load {} error'.format(basename(filename)),
                                        '{}'.format(msg))

    def removeROI(self):
        if self.hasROI():
            if self._activeroi in self._rois: del self._rois[self._activeroi]
            if self._rois.count() > 0:
                self.setActiveROI(self._rois[0].getName(), signal=True)
                self.ROIListChanged.emit(self._rois[0].getName())
            else:
                self.updateROIAttributes()
                self.ROIAttributesChanged.emit(self)
                if self._draw.getUndo(): self._draw.clearLIFO()
                self.ROIListChanged.emit('')

    def removeAllROI(self):
        if self.hasROI():
            self._rois.clear()
            self.updateROIAttributes()
            self.ROIAttributesChanged.emit(self)
            if self._draw.getUndo(): self._draw.clearLIFO()
            self.ROIListChanged.emit('')

    def saveROI(self):
        if self.hasROI():
            roi = self._rois[self._activeroi]
            try:
                if not roi.hasFilename():
                    filename = join(dirname(self._volume.getFilename()), roi.getName()) + roi.getFileExt()
                    roi.save(filename)
                else: roi.save()
                if self._draw.getUndo(): self._draw.clearLIFO()
            except Exception as msg:
                QMessageBox.warning(self, 'Save {} error'.format(basename(roi.getFilename())),
                                    '{}'.format(msg))

    def saveAllROI(self):
        if self.hasROI():
            for roi in self._rois:
                try:
                    if not roi.hasFilename():
                        filename = join(dirname(self._volume.getFilename()), roi.getName()) + roi.getFileExt()
                        roi.save(filename)
                    else: roi.save()
                    QApplication.processEvents()
                except Exception as msg:
                    QMessageBox.warning(self, 'Save {} error'.format(basename(roi.getFilename())),
                                        '{}'.format(msg))
                    return
            if self._draw.getUndo(): self._draw.clearLIFO()

    def getNumberOfROI(self):
        return len(self._rois)

    def hasROI(self):
        return len(self._rois) > 0

    def setActiveROI(self, r, signal=True):
        if self.hasROI():
            if isinstance(r, SisypheROI): r = r.getName()
            if isinstance(r, str):
                if r != self._activeroi:
                    if r in self._rois:
                        self._activeroi = r
                        self._draw.setROI(self._rois[r])
                        self.updateROIAttributes()
                        if signal: self.ROISelectionChanged.emit(self, r)

    def getActiveROI(self):
        if self.hasROI():
            if self._activeroi is not None: return self._rois[self._activeroi]
            else: return None

    def getROI(self, name):
        if isinstance(name, str): return self._rois[name]
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getROINames(self):
        return self._rois.keys()

    def updateRoiName(self, old, name):
        if self._activeroi == old:
            self._activeroi = name

    def getDrawInstance(self):
        return self._draw

    def setDrawInstance(self, draw):
        if isinstance(draw, SisypheROIDraw):
            self._draw = draw
        else: raise TypeError('parameter type {} is not SisypheROIDraw'.format(type(draw)))

    def setBrushRadius(self, r, signal=True):
        if isinstance(r, int):
            self._draw.setBrushRadius(r)
            self._updateBrush()
            if signal: self.BrushRadiusChanged.emit(self, r)
        else: raise TypeError('parameter type {} is not int.'.format(type(r)))

    def getBrushRadius(self):
        return self._draw.getBrushRadius()

    def setMorphologyRadius(self, r):
        if isinstance(r, (int, float)): self._draw.setMorphologyRadius(r)
        else: raise TypeError('parameter type {} is not int or float.'.format(type(r)))

    def getMorphologyRadius(self):
        return self._draw.getMorphologyRadius()

    def setBrushVisibility(self, v):
        if isinstance(v, bool):
            self._brush.SetVisibility(v)
            if v:
                f = self._renderer.GetActiveCamera().GetFocalPoint()
                self._brush.SetPosition(f)
            self._renderwindow.Render()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getBrushVisibility(self):
        return self._brush.GetVisibility()

    def setBrushVisibilityOn(self):
        self.setBrushVisibility(True)

    def setBrushVisibilityOff(self):
        self.setBrushVisibility(False)

    def setROIVisibility(self, v, signal=True):
        if self.hasROI() and self._activesliceroi is not None:
            if isinstance(v, bool):
                if self._slicerois is not None: self._slicerois.SetVisibility(v)
                if self._activesliceroi is not None: self._activesliceroi.SetVisibility(v)
                self._action['showROI'].setChecked(v)
                if not v: self.setSolidBrushFlag(v, signal=False)
                self.setROIMenuVisibility(v)
                self._renderwindow.Render()
                if signal: self.ROIFlagChanged.emit(self, 'setROIVisibility', v)
            else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setROIVisibilityOn(self, signal=True):
        self.setROIVisibility(True, signal)

    def setROIVisibilityOff(self, signal=True):
        self.setROIVisibility(False, signal)

    def getROIVisibility(self):
        if self._activesliceroi is not None: return self._activesliceroi.GetVisibility() > 0
        else: return False

    def setROIMenuVisibility(self, v):
        if isinstance(v, bool):
            self._2d.setEnabled(v)
            self._3d.setEnabled(v)
            self._currentroi.setEnabled(v)
            self._action['removeroi'].setEnabled(v)
            self._action['removeallroi'].setEnabled(v)
            self._action['saveroi'].setEnabled(v)
            self._action['saverois'].setEnabled(v)
            self._action['brushflag'].setEnabled(v)
            self._action['thresholdbrush'].setEnabled(v)
            self._action['brushflag3'].setEnabled(v)
            self._action['thresholdbrush3'].setEnabled(v)
            self._action['fillholesflag'].setEnabled(v)
            self._action['undo'].setEnabled(v and self.getUndo())
            self._action['redo'].setEnabled(v and self.getUndo())
            self._action['showROI'].setEnabled(self.hasROI())
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setROIMenuVisibilityOn(self):
        self.setROIMenuVisibility(True)

    def setROIMenuVisibilityOff(self):
        self.setROIMenuVisibility(False)

    def getROIMenuVisibility(self):
        return self._roitools.isEnabled()

    def setNoROIFlag(self, signal=True):
        self._updateExclusiveFlags()
        if signal: self.ROIFlagChanged.emit(self, 'setNoROIFlag', None)

    def setSolidBrushFlag(self, f, signal=True):
        if isinstance(f, bool):
            if self.hasROI() and self.getROIVisibility() and f:
                self._updateExclusiveFlags('brushflag')
                self._draw.setBrushType('solid')
            else: self._updateExclusiveFlags()
            if signal: self.ROIFlagChanged.emit(self, 'setSolidBrushFlag', f)
        else: raise TypeError('parameter type {} is not bool.'.format(f))

    def setSolidBrushFlagOn(self, signal=True):
        self.setSolidBrushFlag(True, signal)

    def setSolidBrushFlagOff(self, signal=True):
        self.setSolidBrushFlag(False, signal)

    def getSolidBrushFlag(self):
        return self._action['brushflag'].isChecked()

    def setSolidBrush3Flag(self, f, signal=True):
        if isinstance(f, bool):
            if self.hasROI() and self.getROIVisibility() and f:
                self._updateExclusiveFlags('brushflag3')
                self._draw.setBrushType('solid3')
            else: self._updateExclusiveFlags()
            if signal: self.ROIFlagChanged.emit(self, 'setSolidBrush3Flag', f)
        else: raise TypeError('parameter type {} is not bool.'.format(f))

    def setSolidBrush3FlagOn(self, signal=True):
        self.setSolidBrush3Flag(True, signal)

    def setSolidBrush3FlagOff(self, signal=True):
        self.setSolidBrush3Flag(False, signal)

    def getSolidBrush3Flag(self):
        return self._action['brushflag3'].isChecked()

    def setThresholdBrushFlag(self, f, signal=True):
        if isinstance(f, bool):
            if self.hasROI() and self.getROIVisibility() and f:
                self._updateExclusiveFlags('thresholdbrush')
                self._draw.setBrushType('threshold')
            else: self._updateExclusiveFlags()
            if signal: self.ROIFlagChanged.emit(self, 'setThresholdBrushFlag', f)
        else: raise TypeError('parameter type {} is not bool.'.format(f))

    def setThresholdBrushFlagOn(self, signal=True):
        self.setSolidBrushFlag(True, signal)

    def setThresholdBrushFlagOff(self, signal=True):
        self.setSolidBrushFlag(False, signal)

    def getThresholdBrushFlag(self):
        return self._action['thresholdbrush'].isChecked()

    def setThresholdBrush3Flag(self, f, signal=True):
        if isinstance(f, bool):
            if self.hasROI() and self.getROIVisibility() and f:
                self._updateExclusiveFlags('thresholdbrush3')
                self._draw.setBrushType('threshold3')
            else: self._updateExclusiveFlags()
            if signal: self.ROIFlagChanged.emit(self, 'setThresholdBrush3Flag', f)
        else: raise TypeError('parameter type {} is not bool.'.format(f))

    def setThresholdBrush3FlagOn(self, signal=True):
        self.setSolidBrush3Flag(True, signal)

    def setThresholdBrush3FlagOff(self, signal=True):
        self.setSolidBrush3Flag(False, signal)

    def getThresholdBrush3Flag(self):
        return self._action['thresholdbrush3'].isChecked()

    def getBrushFlag(self):
        if self._action['brushflag'].isChecked(): return 1
        elif self._action['thresholdbrush'].isChecked(): return 2
        elif self._action['brushflag3'].isChecked(): return 3
        elif self._action['thresholdbrush3'].isChecked(): return 4
        else: return 0

    def get2DBrushFlag(self):
        return self._action['brushflag'].isChecked() or \
               self._action['thresholdbrush'].isChecked()

    def get3DBrushFlag(self):
        return self._action['brushflag3'].isChecked() or \
               self._action['thresholdbrush3'].isChecked()

    def setFillHolesFlag(self, f, signal=True):
        if isinstance(f, bool):
            self._action['fillholesflag'].setChecked(f)
            if signal: self.ROIFlagChanged.emit(self, 'setFillHolesFlag', f)
        else: raise TypeError('parameter type {} is not bool.'.format(type(f)))

    def setFillHolesFlagOn(self, signal=True):
        self.setFillHolesFlag(True, signal)

    def setFillHolesFlagOff(self, signal=True):
        self.setFillHolesFlag(False, signal)

    def getFillHolesFlag(self):
        return self._action['fillholesflag'].isChecked()

    def set2DBlobDilateFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobdilate'].setChecked(True)
            self._updateExclusiveFlags('2dblobdilate')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobDilateFlagOn', None)

    def set2DBlobErodeFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dbloberode'].setChecked(True)
            self._updateExclusiveFlags('2dbloberode')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobErodeFlagOn', None)

    def set2DBlobCloseFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobclose'].setChecked(True)
            self._updateExclusiveFlags('2dblobclose')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobCloseFlagOn', None)

    def set2DBlobOpenFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobopen'].setChecked(True)
            self._updateExclusiveFlags('2dblobopen')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobOpenFlagOn', None)

    def set2DBlobCopyFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobcopy'].setChecked(True)
            self._updateExclusiveFlags('2dblobcopy')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobCopyFlagOn', None)

    def set2DBlobCutFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobcut'].setChecked(True)
            self._updateExclusiveFlags('2dblobcut')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobCutFlagOn', None)

    def set2DBlobPasteFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobpaste'].setChecked(True)
            self._updateExclusiveFlags('2dblobpaste')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobPasteFlagOn', None)

    def set2DBlobRemoveFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobremove'].setChecked(True)
            self._updateExclusiveFlags('2dblobremove')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobRemoveFlagOn', None)

    def set2DBlobKeepFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobkeep'].setChecked(True)
            self._updateExclusiveFlags('2dblobkeep')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobKeepFlagOn', None)

    def set2DBlobThresholdFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobthreshold'].setChecked(True)
            self._updateExclusiveFlags('2dblobthreshold')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobThresholdFlagOn', None)

    def set2DFillFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dfill'].setChecked(True)
            self._updateExclusiveFlags('2dfill')
            if signal: self.ROIFlagChanged.emit(self, 'set2DFillFlagOn', None)

    def set2DRegionGrowingFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2drgrowing'].setChecked(True)
            self._updateExclusiveFlags('2drgrowing')
            if signal: self.ROIFlagChanged.emit(self, 'set2DRegionGrowingFlagOn', None)

    def set2DBlobRegionGrowingFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobrgrowing'].setChecked(True)
            self._updateExclusiveFlags('2dblobrgrowing')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobRegionGrowingFlagOn', None)

    def set2DRegionConfidenceFlagOn(self, signal=True):
            if self.hasROI() and self.getROIVisibility():
                self._action['2drconfidence'].setChecked(True)
                self._updateExclusiveFlags('2drconfidence')
                if signal: self.ROIFlagChanged.emit(self, 'set2DRegionConfidenceFlagOn', None)

    def set2DBlobRegionConfidenceFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['2dblobrconfidence'].setChecked(True)
            self._updateExclusiveFlags('2dblobrconfidence')
            if signal: self.ROIFlagChanged.emit(self, 'set2DBlobRegionConfidenceFlagOn', None)

    def set3DBlobDilateFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobdilate'].setChecked(True)
            self._updateExclusiveFlags('3dblobdilate')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobDilateFlagOn', None)

    def set3DBlobErodeFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dbloberode'].setChecked(True)
            self._updateExclusiveFlags('3dbloberode')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobErodeFlagOn', None)

    def set3DBlobCloseFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobclose'].setChecked(True)
            self._updateExclusiveFlags('3dblobclose')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobCloseFlagOn', None)

    def set3DBlobOpenFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobopen'].setChecked(True)
            self._updateExclusiveFlags('3dblobopen')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobOpenFlagOn', None)

    def set3DBlobCopyFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobcopy'].setChecked(True)
            self._updateExclusiveFlags('3dblobcopy')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobCopyFlagOn', None)

    def set3DBlobCutFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobcut'].setChecked(True)
            self._updateExclusiveFlags('3dblobcut')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobCutFlagOn', None)

    def set3DBlobPasteFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobpaste'].setChecked(True)
            self._updateExclusiveFlags('3dblobpaste')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobPasteFlagOn', None)

    def set3DBlobRemoveFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobremove'].setChecked(True)
            self._updateExclusiveFlags('3dblobremove')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobRemoveFlagOn', None)

    def set3DBlobKeepFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobkeep'].setChecked(True)
            self._updateExclusiveFlags('3dblobkeep')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobKeepFlagOn', None)

    def set3DBlobExpandFlagOn(self, v, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobexpand'].setChecked(True)
            self._draw.setThickness(v)
            self._updateExclusiveFlags('3dblobexpand')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobExpandFlagOn', v)

    def set3DBlobShrinkFlagOn(self, v, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobshrink'].setChecked(True)
            self._draw.setThickness(v)
            self._updateExclusiveFlags('3dblobshrink')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobShrinkFlagOn', v)

    def set3DBlobThresholdFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobthreshold'].setChecked(True)
            self._updateExclusiveFlags('3dblobthreshold')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobThresholdFlagOn', None)

    def set3DFillFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dfill'].setChecked(True)
            self._updateExclusiveFlags('3dfill')
            if signal: self.ROIFlagChanged.emit(self, 'set3DFillFlagOn', None)

    def set3DRegionGrowingFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3drgrowing'].setChecked(True)
            self._updateExclusiveFlags('3drgrowing')
            if signal: self.ROIFlagChanged.emit(self, 'set3DRegionGrowingFlagOn', None)

    def set3DBlobRegionGrowingFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobrgrowing'].setChecked(True)
            self._updateExclusiveFlags('3dblobrgrowing')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobRegionGrowingFlagOn', None)

    def set3DRegionConfidenceFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3drconfidence'].setChecked(True)
            self._updateExclusiveFlags('3drconfidence')
            if signal: self.ROIFlagChanged.emit(self, 'set3DRegionConfidenceFlagOn', None)

    def set3DBlobRegionConfidenceFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['3dblobrconfidence'].setChecked(True)
            self._updateExclusiveFlags('3dblobrconfidence')
            if signal: self.ROIFlagChanged.emit(self, 'set3DBlobRegionConfidenceFlagOn', None)

    def setActiveContourFlagOn(self, signal=True):
        if self.hasROI() and self.getROIVisibility():
            self._action['activecontour'].setChecked(True)
            self._updateExclusiveFlags('activecontour')
            if signal: self.ROIFlagChanged.emit(self, 'setActiveContourFlagOn', None)

    def setUndoOn(self, signal=True):
        self.setUndo(True, signal)

    def setUndoOff(self, signal=True):
        self.setUndo(False, signal)

    def setUndo(self, v, signal=True):
        if isinstance(v, bool):
            self._draw.setUndo(v)
            self._action['undo'].setEnabled(v)
            self._action['redo'].setEnabled(v)
            if signal: self.ROIFlagChanged.emit(self, 'setUndo', v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getUndo(self):
        return self._draw.getUndo()

    def sliceMinus(self):
        super().sliceMinus()
        if self.hasROI() and self.getROIVisibility() and self.getBrushFlag() > 0:
            p = list(self._brush.GetPosition())
            f = self._renderer.GetActiveCamera().GetFocalPoint()
            d = 2 - self._orient
            p[d] = f[d] - 1.0
            self._brush.SetPosition(p)
            self._renderwindow.Render()

    def slicePlus(self):
        super().slicePlus()
        if self.hasROI() and self.getROIVisibility() and self.getBrushFlag() > 0:
            p = list(self._brush.GetPosition())
            f = self._renderer.GetActiveCamera().GetFocalPoint()
            d = 2 - self._orient
            p[d] = f[d] - 1.0
            self._brush.SetPosition(p)
            self._renderwindow.Render()

    def undo(self):
        self._draw.popUndoLIFO()
        self._roimapper.GetInput().Modified()
        self._renderwindow.Render()
        self.ROIModified.emit(self)

    def redo(self):
        self._draw.popRedoLIFO()
        self._roimapper.GetInput().Modified()
        self._renderwindow.Render()
        self.ROIModified.emit(self)

    def updateROIDisplay(self, signal=False):
        if self._roimapper is not None:  self._roimapper.GetInput().Modified()
        if signal: self.ROIModified.emit(self)
        self._renderwindow.Render()

    def updateROIAttributes(self, signal=False):
        self._updateSliceROI()
        self._updateActiveSliceROI()
        self._updateBrush()
        self._updateROIMenu()
        self._renderwindow.Render()
        if self._rois.count() == 0:
            self._draw.removeROI()
        if signal: self.ROIAttributesChanged.emit(self)

    def getPopupROI(self):
        return self._roitools

    def popupROIEnabled(self):
        self._roitools.menuAction().setVisible(True)

    def popupROIDisabled(self):
        self._roitools.menuAction().setVisible(False)

    # 2D ROI functions

    def sliceFlip(self, flipx, flipy):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.flipSlice(index, self._orient, flipx, flipy)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceMove(self, movex, movey):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.moveSlice(index, self._orient, movex, movey)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceDilate(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.morphoSliceDilate(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceErode(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.morphoSliceErode(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceOpen(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.morphoSliceOpening(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceClose(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.morphoSliceClosing(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceBackground(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.backgroundSegmentSlice(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceObject(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.objectSegmentSlice(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceInvert(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.binaryNotSlice(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def sliceClear(self):
        if self.hasROI() and self.getROIVisibility():
            index = self.getSliceIndex()
            self._draw.clearSlice(index, self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    # 3D ROI functions

    def roiDilate(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.morphoDilate()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiErode(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.morphoErode()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiOpen(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.morphoOpening()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiClose(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.morphoClosing()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiBackground(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.backgroundSegment()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiObject(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.objectSegment()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiInvert(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.binaryNOT()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def roiClear(self):
        if self.hasROI() and self.getROIVisibility():
            self._draw.clear()
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)

    def updateRender(self):
        self._roimapper.GetInput().Modified()
        super().updateRender()

    # Private event methods

    def _onWheelForwardEvent(self,  obj, evt_name):
        # interactorstyle = self._window.GetInteractorStyle()
        # k = interactorstyle.GetKeySym()
        # Brush radius Alt + Wheel
        if self.hasROI() and self.getROIVisibility() and \
                self.getBrushFlag() > 0 and self._interactor.GetKeySym() == 'Alt_L':
            # change brush radius
            r = self.getBrushRadius() - 1
            self.setBrushRadius(r)
        else: super()._onWheelForwardEvent(obj, evt_name)
        self._renderwindow.Render()

    def _onWheelBackwardEvent(self,  obj, evt_name):
        # interactorstyle = self._window.GetInteractorStyle()
        # k = interactorstyle.GetKeySym()
        # Brush radius Alt + Wheel
        if self.hasROI() and self.getROIVisibility() and \
                self.getBrushFlag() > 0 and self._interactor.GetKeySym() == 'Alt_L':
            # change brush radius
            r = self.getBrushRadius() + 1
            self.setBrushRadius(r)
        else: super()._onWheelBackwardEvent(obj, evt_name)
        self._renderwindow.Render()

    def _onMouseMoveEvent(self, obj, evt_name):
        if self.hasROI() and self.getROIVisibility() and self.getBrushFlag() > 0:
            interactorstyle = self._window.GetInteractorStyle()
            k = self._interactor.GetKeySym()
            if k in ('Control_L', 'Shift_L', 'Alt_L') or self.getZoomFlag()\
                    or self.getMoveFlag() or self.getLevelFlag():
                if self._brushFlag0 is None:
                    self._brushFlag0 = self.getBrushFlag()
                    self._brush.SetVisibility(False)
                super()._onMouseMoveEvent(obj, evt_name)
            else:
                self._brush.SetVisibility(True)
                if not self._timer.isActive(): self._timer.start()
                last = interactorstyle.GetLastPos()
                p = list(self._getWorldFromDisplay(last[0], last[1]))
                f = self._renderer.GetActiveCamera().GetFocalPoint()
                d = 2 - self._orient
                if self._orient == 1: p[d] = f[d] + 1.0
                else: p[d] = f[d] - 1.0
                self._brush.SetPosition(p)
                if interactorstyle.GetButton() != 0:
                    p[d] = f[d]
                    p = self._getWorldToMatrixCoordinate(p)
                    if self._window.GetInteractorStyle().GetButton() == 1:
                        self._draw.brush(p[0], p[1], p[2], self._orient)
                    elif self._window.GetInteractorStyle().GetButton() == 3:
                        self._draw.erase(p[0], p[1], p[2], self._orient)
                    self._roimapper.GetInput().Modified()
                    self.ROIModified.emit(self)
                self._renderwindow.Render()
        else: super()._onMouseMoveEvent(obj, evt_name)

    def _onLeftPressEvent(self, obj, evt_name):
        if self.hasROI() and self.getROIVisibility():
            k = self._interactor.GetKeySym()
            if k in ('Control_L', 'Shift_L', 'Alt_L') or self.getZoomFlag() \
                    or self.getMoveFlag() or self.getLevelFlag():
                if self._brushFlag0 is None:
                    self._brushFlag0 = self.getBrushFlag()
                    self._brush.SetVisibility(False)
                super()._onLeftPressEvent(obj, evt_name)
            else:
                if not self.isSelected(): self.select()
                p = self._getClickedMatrixCoordinate()
                # Solid brush draw
                if self.getBrushFlag() > 0:
                    self._draw.brush(p[0], p[1], p[2], self._orient)
                # 2D Dilate selected blob
                elif self._action['2dblobdilate'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.morphoSliceBlobDilate(index, self._orient, p[0], p[1], p[2])
                # 2D Erode selected blob
                elif self._action['2dbloberode'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.morphoSliceBlobErode(index, self._orient, p[0], p[1], p[2])
                # 2D Close selected blob
                elif self._action['2dblobclose'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.morphoSliceBlobClosing(index, self._orient, p[0], p[1], p[2])
                # 2D Open selected blob
                elif self._action['2dblobopen'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.morphoSliceBlobOpening(index, self._orient, p[0], p[1], p[2])
                # 2D Copy selected blob
                elif self._action['2dblobcopy'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.copyBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Cut selected blob
                elif self._action['2dblobcut'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.cutBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Paste blob
                elif self._action['2dblobpaste'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.pasteBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Remove selected blob
                elif self._action['2dblobremove'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.blobRemoveSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Keep selected blob
                elif self._action['2dblobkeep'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.blobSelectSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Thresholding in selected blob
                elif self._action['2dblobthreshold'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.thresholdingBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 2D fill
                elif self._action['2dfill'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.seedFillSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Region growing
                elif self._action['2drgrowing'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.regionGrowingSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Region growing in selected blob
                elif self._action['2dblobrgrowing'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.regionGrowingBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Region confidence
                elif self._action['2drconfidence'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.regionGrowingConfidenceSlice(index, self._orient, p[0], p[1], p[2])
                # 2D Region confidence in selected blob
                elif self._action['2dblobrconfidence'].isChecked():
                    index = self.getSliceIndex()
                    self._draw.regionGrowingConfidenceBlobSlice(index, self._orient, p[0], p[1], p[2])
                # 3D Dilate selected blob
                elif self._action['3dblobdilate'].isChecked():
                    wait = DialogWait(info='Morphology dilate of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.morphoBlobDilate(p[0], p[1], p[2])
                    wait.close()
                # 3D Erode selected blob
                elif self._action['3dbloberode'].isChecked():
                    wait = DialogWait(info='Morphology erode of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.morphoBlobErode(p[0], p[1], p[2])
                    wait.close()
                # 3D Close selected blob
                elif self._action['3dblobclose'].isChecked():
                    wait = DialogWait(info='Morphology closing of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.morphoBlobClosing(p[0], p[1], p[2])
                    wait.close()
                # 3D Open selected blob
                elif self._action['3dblobopen'].isChecked():
                    wait = DialogWait(info='Morphology opening of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.morphoBlobOpening(p[0], p[1], p[2])
                    wait.close()
                # 3D Copy selected blob
                elif self._action['3dblobcopy'].isChecked():
                    self._draw.copyBlob(p[0], p[1], p[2])
                # 3D Cut selected blob
                elif self._action['3dblobcut'].isChecked():
                    self._draw.cutBlob(p[0], p[1], p[2])
                # 3D Paste blob
                elif self._action['3dblobpaste'].isChecked():
                    self._draw.pasteBlob(p[0], p[1], p[2])
                # 3D Remove selected blob
                elif self._action['3dblobremove'].isChecked():
                    self._draw.blobRemove(p[0], p[1], p[2])
                # 3D Keep selected blob
                elif self._action['3dblobkeep'].isChecked():
                    self._draw.blobSelect(p[0], p[1], p[2])
                # 3D expand selected blob
                elif self._action['3dblobexpand'].isChecked():
                    wait = DialogWait(info='Euclidean expand of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.euclideanBlobDilate(p[0], p[1], p[2])
                    wait.close()
                # 3D shrink selected blob
                elif self._action['3dblobshrink'].isChecked():
                    wait = DialogWait(info='Euclidean shrink of selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.euclideanBlobErode(p[0], p[1], p[2])
                    wait.close()
                # 3D Thresholding in selected blob
                elif self._action['3dblobthreshold'].isChecked():
                    wait = DialogWait(info='Thresholding...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.thresholdingBlob(p[0], p[1], p[2])
                    wait.close()
                # 3D fill from seed
                    wait = DialogWait(info='Fill from seed voxel...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.seedFill(p[0], p[1], p[2])
                    wait.close()
                # 3D Region growing
                elif self._action['3drgrowing'].isChecked():
                    wait = DialogWait(info='Region growing segmentation...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.regionGrowing(p[0], p[1], p[2])
                    wait.close()
                # 3D Region growing in selected blob
                elif self._action['3dblobrgrowing'].isChecked():
                    wait = DialogWait(info='Region growing segmentation in selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.regionGrowingBlob(p[0], p[1], p[2])
                    wait.close()
                # 3D Region confidence
                elif self._action['3drconfidence'].isChecked():
                    wait = DialogWait(info='Region confidence connected segmentation...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.regionGrowingConfidence(p[0], p[1], p[2])
                    wait.close()
                # 3D Region confidence in selected blob
                elif self._action['3dblobrconfidence'].isChecked():
                    wait = DialogWait(info='Region confidence connected segmentation in selected blob...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.regionGrowingConfidenceBlob(p[0], p[1], p[2])
                    wait.close()
                # Active contour
                elif self._action['activecontour'].isChecked():
                    wait = DialogWait(info='Active contour segmentation...', parent=self)
                    wait.open()
                    # wait.moveToScreenCenter()
                    self._draw.activeContour(p[0], p[1], p[2])
                    wait.close()
                self._roimapper.GetInput().Modified()
                self._renderwindow.Render()
                self.ROIModified.emit(self)
        else: super()._onLeftPressEvent(obj, evt_name)

    def _onLeftReleaseEvent(self,  obj, evt_name):
        if self._brushFlag0 is not None:
            self._brush.SetVisibility(self._brushFlag0 > 0)
            self._brushFlag0 = None
        elif self.hasROI() and self.getROIVisibility() and self.getBrushFlag() > 0:
            if self._action['fillholesflag'].isChecked():
                index = self.getSliceIndex()
                self._draw.fillHolesSlice(index, self._orient, False)
                if self.getUndo(): self._draw.appendSliceToLIFO(index, self._orient)
                self._roimapper.GetInput().Modified()
                self._renderwindow.Render()
                self.ROIModified.emit(self)
            elif self.getUndo():
                if self.get2DBrushFlag():
                    index = self.getSliceIndex()
                    self._draw.appendSliceToLIFO(index, self._orient)
                else: self._draw.appendVolumeToLIFO()
        super()._onLeftReleaseEvent(obj, evt_name)

    def _onMiddlePressEvent(self, obj, evt_name):
        self._brush.SetVisibility(False)
        self._renderwindow.Render()
        super()._onMiddlePressEvent(obj, evt_name)

    def _onRightPressEvent(self, obj, evt_name):
        interactorstyle = self._window.GetInteractorStyle()
        if self.hasROI() and self.getROIVisibility() and self.getBrushFlag() > 0:
            last = interactorstyle.GetLastPos()
            p = list(self._getWorldFromDisplay(last[0], last[1]))
            f = self._renderer.GetActiveCamera().GetFocalPoint()
            d = 2 - self._orient
            p[d] = f[d]
            p = self._getWorldToMatrixCoordinate(p)
            self._draw.erase(p[0], p[1], p[2], self._orient)
            self._roimapper.GetInput().Modified()
            self._renderwindow.Render()
            self.ROIModified.emit(self)
        else:
            self._brush.SetVisibility(False)
            self._renderwindow.Render()
            super()._onRightPressEvent(obj, evt_name)
            self._interactor.RightButtonReleaseEvent()
            self._interactor.KeyReleaseEvent()

    def _onKeyPressEvent(self,  obj, evt_name):
        if self.hasROI():
            interactorstyle = self._window.GetInteractorStyle()
            k = interactorstyle.GetKeySym()
            if self._interactor.GetControlKey():
                if k == 'z': self.undo()
                elif k == 'y': self.redo()
        super()._onKeyPressEvent(obj, evt_name)

    def _onTimer(self):
        p = self.mapFromGlobal(QCursor.pos())
        if not self.rect().contains(p):
            self._brush.SetVisibility(False)
            self._renderwindow.Render()
            self._timer.stop()
