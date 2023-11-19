"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        vtk             https://vtk.org/                                            Visualization
"""

from math import pow
from math import sqrt

from numpy import ndarray

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QApplication

from vtk import vtkPlane
from vtk import vtkCamera
from vtk import vtkImageSlice
from vtk import vtkImageResliceMapper

from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.toolWidgets import HandleWidget
from Sisyphe.widgets.toolWidgets import LineWidget
from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget

"""
    Class hierarchy

        QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> SliceTrajectoryViewWidget
        
    Description
    
        Derived from SliceOverlayViewWidget. Adds interactive management of target and trajectory widgets. 
"""


class SliceTrajectoryViewWidget(SliceOverlayViewWidget):
    """
        SliceTrajectoryViewWidget class

        Description

            Add target management and camera trajectory alignment

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceTrajectoryViewWidget

        Private attributes

            _target     [float, float, float], current target

        Custom Qt signals

            TrajectoryCameraAligned.emit(QWidget)
            TrajectoryToolAligned.emit(QWidget, str)
            TrajectoryVectorAligned.emit(QWidget, float, float, float)
            TrajectoryDefaultAligned.emit(QWidget)
            SlabChanged.emit(QWidget, float, str)
            StepChanged.emit(QWidget, float)

        Public Qt event synchronisation methods

            synchroniseTrajectoryToolAligned(QWidget, str)
            synchroniseTrajectoryVectorAligned(QWidget, float, float, float)
            synchroniseTrajectoryDefaultAligned(QWidget)
            synchroniseToolMoved(QWidget, NamedWidget)
            synchroniseSlabChanged(QWidget, float, str)
            synchroniseStepChanged(QWidget, float)

        Public methods

            QMenu = getPopupAlignment()
            popupAlignmentEnabled()
            popupAlignmentDisabled()
            setSliceStep(float)
            float = getSliceStep()
            bool = hasTarget()
            HandleWidget | LineWidget = getTarget()
            [float, float, float] = getTargetPosition()
            setTarget(int | str | HandleWidget | LineWidget)
            float = getDistanceFromCurrentSliceToTarget()
            setTrajectoryFromCamera(vtkCamera)
            setTrajectoryFromLineWidget(LineWidget)
            setTrajectoryFromNormalVector(list or numpy array)
            setTrajectoryToDefault()
            [float, float, float] = getTrajectory()
            setCursorFromDisplayPosition(int, int)
            bool = isCameraAligned()
            bool = isToolAligned()
            bool = isDefaultAligned()
            setSlabThickness(float)
            float = getSlabThickness()
            setSlabType(str)
            setSlabTypeToMin()
            setSlabTypeToMax()
            setSlabTypeToMean()
            setSlabTypeToSum()
            str = getSlabType()

            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods

        Revisions:

            20/09/2023  _setCameraFocalDepth() method, tool and cursor display bugfix
            23/09/2023  _updateCameraOrientation() method, camera orientation bugfix
            02/10/2023  add slab management methods
            10/10/2023  _updateCameraOrientation() method bugfix, set opposite azimuth and elevation angles
            11/10/2023  add setTrajectoryFromACPC() method
                        add synchroniseTrajectoryACPCAligned() method
    """
    # Custom Qt signals

    TrajectoryCameraAligned = pyqtSignal(QWidget)
    TrajectoryACPCAligned = pyqtSignal(QWidget)
    TrajectoryToolAligned = pyqtSignal(QWidget, str)  # str tool name
    TrajectoryVectorAligned = pyqtSignal(QWidget, float, float, float)  # float normal
    TrajectoryDefaultAligned = pyqtSignal(QWidget)
    SlabChanged = pyqtSignal(QWidget, float, str)  # float slab thickness, str slab type
    StepChanged = pyqtSignal(QWidget, float)  # float slice step

    # Special method

    def __init__(self, overlays=None, parent=None):
        super().__init__(overlays, parent)

        self._camera0 = None
        self._step = 1.0
        self._target = None
        self._cursorpos = [0.0, 0.0, 0.0]

        self._action['axial'].setText('First orientation')
        self._action['coronal'].setText('Second orientation')
        self._action['sagittal'].setText('Third orientation')

        self._menuAlign = QMenu('Alignment', self._popup)
        self._menuAlignGroup = None
        self._popup.insertMenu(self._popup.actions()[6], self._menuAlign)
        self._updateToolMenu()

    # Private methods

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

    def _setCameraFocalDepth(self, p, signal=True):
        camera = self._renderer.GetActiveCamera()
        if isinstance(p, (list, tuple)):
            self._cursorpos = p
            plane = vtkPlane()
            plane.SetOrigin(p[0], p[1], p[2])  # Plane center on cursor coordinates
            plane.SetNormal(self.getVtkPlane().GetNormal())  # Plane normal from camera
            plane.Push(-0.1)
            r = [0, 0, 0]
            f = camera.GetFocalPoint()
            plane.ProjectPoint(f, r)
            camera.SetFocalPoint(r)
            plane.ProjectPoint(p, r)
            self._cursor.SetPosition(r)
        elif isinstance(p, int):
            step = p * self._step
            v = list(camera.GetDirectionOfProjection())
            v[0] *= step
            v[1] *= step
            v[2] *= step
            f = list(camera.GetFocalPoint())
            f[0] += v[0]
            f[1] += v[1]
            f[2] += v[2]
            xmax, ymax, zmax = self._volume.getFieldOfView()
            if (0 <= f[0] <= xmax) and (0 <= f[1] <= ymax) and (0 <= f[2] <= zmax):
                camera.SetFocalPoint(f)
                p = self.getCursorWorldPosition()
                plane = vtkPlane()
                plane.SetOrigin(f[0], f[1], f[2])
                plane.SetNormal(camera.GetViewPlaneNormal())
                r = [0, 0, 0]
                plane.ProjectPoint(p, r)
                self._cursor.SetPosition(r)
                self._cursorpos = r
                # synchronisation
                if self.isSynchronised() and signal:
                    self.CursorPositionChanged.emit(self, r[0], r[1], r[2])
        else: raise TypeError('parameter type {} is not int.'.format(type(p)))
        self._updateCameraClipping()
        # Tools display
        if self._tools.count() > 0:
            for tool in self._tools:
                if isinstance(tool, (HandleWidget, LineWidget)):
                    tool.updateContourActor(self.getVtkPlane())
        self._updateBottomRightInfo()

    def _updateCameraClipping(self):
        camera = self._renderer.GetActiveCamera()
        d = camera.GetDistance()
        camera.SetClippingRange(d - self._step, d + self._step)
        self.updateRender()

    def _updateCameraOrientation(self):
        if self._camera0 is not None:
            camera = self._renderer.GetActiveCamera()
            camera.SetPosition(self._camera0)
            v = [abs(i) for i in camera.GetDirectionOfProjection()]
            orient = 2 - v.index(max(v))
            if orient in (self._DIM1, self._DIM2): camera.SetViewUp(0.0, 0.0, 1.0)
            else: camera.SetViewUp(0.0, 1.0, 0.0)
            camera.OrthogonalizeViewUp()
            # row 0, column 1
            if self._orient == self._DIM0:
                camera.Azimuth(-90)
                camera.Elevation(-90)
            # row 1, column 0
            elif self._orient == self._DIM1:
                camera.Azimuth(-90)
            # update view up vector
            if self._orient != self._DIM2:
                v = [abs(i) for i in camera.GetDirectionOfProjection()]
                orient = 2 - v.index(max(v))
                if orient in (self._DIM1, self._DIM2): camera.SetViewUp(0.0, 0.0, 1.0)
                else: camera.SetViewUp(0.0, 1.0, 0.0)
                camera.OrthogonalizeViewUp()
            # init default zoom if not defined
            camera.UpdateViewport(self._renderer)
            self._stack.GetMapper().UpdateInformation()
            if self._scale is None:
                fov = self._volume.getFieldOfView()
                self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
                self._scale = camera.GetParallelScale()
                p = list(camera.GetFocalPoint())
                self._cursor.SetPosition(p)
            self._renderwindow.Render()

    def _updateToolMenu(self):
        super()._updateToolMenu()
        # search checked action
        checked = None
        if self._menuAlignGroup is not None:
            a = self._menuAlignGroup.checkedAction()
            if a is not None: checked = a.text()
        # update menu
        self._menuAlign.clear()
        self._menuAlignGroup = QActionGroup(self._popup)
        self._menuAlignGroup.setExclusive(True)
        # Default alignment
        t = QAction('Default alignment', self)
        self._menuAlignGroup.addAction(t)
        t.setCheckable(True)
        if checked is None: t.setChecked(True)
        else: t.setChecked(t.text() == checked)
        t.triggered.connect(lambda: self.setTrajectoryToDefault(signal=True))
        self._menuAlign.addAction(t)
        # 3D view Camera axis alignment
        t = QAction('3D view camera alignment', self)
        self._menuAlignGroup.addAction(t)
        t.setCheckable(True)
        t.setChecked(t.text() == checked)
        t.triggered.connect(lambda state, x=self: self.TrajectoryCameraAligned.emit(x))
        self._menuAlign.addAction(t)
        # AC PC alignment
        if self._volume is not None and self._volume.acpc.hasACPC():
            t = QAction('AC-PC alignment', self)
            self._menuAlignGroup.addAction(t)
            t.setCheckable(True)
            t.setChecked(t.text() == checked)
            t.triggered.connect(lambda state: self.setTrajectoryFromACPC(signal=True))
            self._menuAlign.addAction(t)
        # Tool alignment
        if len(self._tools) > 0:
            for tool in self._tools:
                if isinstance(tool, LineWidget):
                    t = QAction('Tool {} alignment'.format(tool.getName()), self)
                    self._menuAlignGroup.addAction(t)
                    t.setCheckable(True)
                    t.setChecked(t.text() == checked)
                    t.triggered.connect(lambda state, x=tool.getName():
                                        self.setTrajectoryFromLineWidget(x, signal=True))
                    self._menuAlign.addAction(t)

    def _updateCheckedAction(self, name):
        for a in self._menuAlignGroup.actions():
            a.setChecked(a.text() == name)

    def _getInfoValuesText(self, p):
        txt = ''
        if self.getInfoVisibility():
            if self._target is not None:
                d = self.getDistanceFromCurrentSliceToTarget()
                if d[0] < self._step: d[0] = 0.0
                if d[1] < self._step: d[1] = 0.0
                legend = self._target.getLegend()
                for i in range(2):
                    txt += '\nDistance from slice to {} {} {:.1f} mm'.format(self._target.getName(),
                                                                             legend[i], d[i])
        return txt + super()._getInfoValuesText(p)

    # Public synchronisation event methods

    def synchroniseTrajectoryToolAligned(self, obj, name):
        if self != obj:
            self.setTrajectoryFromLineWidget(name, signal=False)

    def synchroniseTrajectoryACPCAligned(self, obj):
        if self != obj:
            self.setTrajectoryFromACPC(signal=False)
            
    def synchroniseTrajectoryVectorAligned(self, obj, x, y, z):
        if self != obj:
            self.setTrajectoryFromNormalVector([x, y, z], signal=False)
            
    def synchroniseTrajectoryDefaultAligned(self, obj):
        if self != obj:
            self.setTrajectoryToDefault(signal=False)

    def synchroniseToolMoved(self, obj, tool):
        super().synchroniseToolMoved(obj, tool)
        name = self._menuAlignGroup.checkedAction().text()
        if name not in ('Default axis alignment', 'Camera axis alignment'):
            self.setTrajectoryFromLineWidget(name, signal=False)

    def synchroniseSlabChanged(self, obj, thickness, slabtype):
        if obj != self:
            self.setSlabThickness(thickness, signal=False)
            self.setSlabType(slabtype, signal=False)

    def synchroniseStepChanged(self, obj, step):
        if obj != self:
            self.setSliceStep(step, signal=False)

    # Public methods

    def setVolume(self, volume):
        super().setVolume(volume)
        self._updateToolMenu()

    def getPopupAlignment(self):
        return self._menuAlign

    def popupAlignmentEnabled(self):
        self._menuAlign.menuAction().setVisible(True)

    def popupAlignmentDisabled(self):
        self._menuAlign.menuAction().setVisible(False)

    def setSliceStep(self, v, signal=True):
        if isinstance(v, float):
            if 0.5 <= v <= 10.0:
                self._step = v
                if signal: self.StepChanged.emit(self, v)
            else: raise ValueError('parameter value {} is not between 0.5 and 10.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSliceStep(self):
        return self._step

    def hasTarget(self):
        return self._target is not None

    def getTarget(self):
        return self._target

    def getTargetPosition(self):
        if self._target is not None:
            if isinstance(self._target, HandleWidget): return self._target.getPosition()
            elif isinstance(self._target, LineWidget): return self._target.getPosition2()
            else: return None

    def setTarget(self, key, signal=True):
        if isinstance(key, HandleWidget | LineWidget): key = key.getName()
        if isinstance(key, (int, str)):
            if key in self._tools:
                self._target = self._tools[key]
                if signal: self.ViewMethodCalled.emit(self, 'setTarget', key)
            else: raise KeyError('invalid tool key, tool {} is not in current view.'.format(key))
        else: raise TypeError('parameter type {} is not int or str')

    def setCursorWorldPosition(self, x, y, z, signal=True):
        if self._volume is not None:
            p = [x, y, z]
            # Update camera focal
            self._setCameraFocalDepth(p, signal=False)
            # Synchronising
            if self.isSynchronised() and signal:
                x, y, z = self._cursorpos
                self.CursorPositionChanged.emit(self, x, y, z)

    def getCursorWorldPosition(self):
        return self._cursorpos

    def setCursorFromDisplayPosition(self, x, y):
        p = list(self._getWorldFromDisplay(x, y))
        r = [0.0, 0.0, 0.0]
        self.getVtkPlane().ProjectPoint(p, r)
        self.setCursorWorldPosition(r[0], r[1], r[2], signal=False)

    def getDistanceFromCurrentSliceToTarget(self):
        if self._target is not None:
            if isinstance(self._target, HandleWidget):
                return [self._target.getDistanceToPlane(self), 0.0]
            elif isinstance(self._target, LineWidget):
                d = self._target.getDistancesToPlane(self)
                return [d[1], d[0]]
        else: return None

    def setTrajectoryFromCamera(self, t, signal=True):
        if isinstance(t, vtkCamera):
            camera = self._renderer.GetActiveCamera()
            camera.SetPosition(t.GetPosition())
            self._camera0 = t.GetPosition()
            self._updateCameraOrientation()
            self._updateCameraClipping()
            self._updateCheckedAction('3D view camera alignment')
            self._target = None
            if signal: self.TrajectoryCameraAligned.emit()
        else: raise TypeError('parameter type {} is not vtkCamera.'.format(type(t)))

    def setTrajectoryFromLineWidget(self, name, signal=True):
        tool = None
        for t in self._tools:
            if t.getName() == name:
                tool = t
                break
        if tool is not None and isinstance(tool, LineWidget):
            camera = self._renderer.GetActiveCamera()
            p1 = tool.getPosition1()  # Entry
            p2 = tool.getPosition2()  # Target
            d = sqrt(pow(p2[0] - p1[0], 2) +
                     pow(p2[1] - p1[1], 2) +
                     pow(p2[2] - p1[2], 2))
            # Normal unit vector
            n = [(p1[0] - p2[0]) / d,
                 (p1[1] - p2[1]) / d,
                 (p1[2] - p2[2]) / d]
            # Set focal point
            camera.SetFocalPoint(p2)
            # Set camera position
            p = [p2[0] + (n[0] * 500),
                 p2[1] + (n[1] * 500),
                 p2[2] + (n[2] * 500)]
            camera.SetPosition(p)
            self._camera0 = p
            self._updateCameraOrientation()
            self.setCursorWorldPosition(p2[0], p2[1], p2[2], signal=False)
            self._target = tool
            self._updateCheckedAction('Tool {} alignment'.format(name))
            if signal: self.TrajectoryToolAligned.emit(self, name)
        else: raise TypeError('parameter type {} is not LineWidget.'.format(type(tool)))

    def setTrajectoryFromNormalVector(self, t, signal=True):
        if isinstance(t, ndarray): t = t.tolist()
        if isinstance(t, list):
            plane = vtkPlane()
            plane.SetNormal(t)
            c = self._volume.getCenter()
            plane.SetOrigin(c)
            camera = self._renderer.GetActiveCamera()
            camera.SetFocalPoint(c)
            p = [c[0] + t[0] * 500,
                 c[1] + t[1] * 500,
                 c[2] + t[2] * 500]
            camera.SetPosition(p)
            self._camera0 = p
            self._updateCameraOrientation()
            if signal: self.TrajectoryVectorAligned.emit(self, t[0], t[1], t[2])
        else: raise TypeError('parameter type {} is not list or numpy array.'.format(type(t)))

    def setTrajectoryFromACPC(self, signal=True):
        if self._volume.acpc.hasACPC():
            camera = self._renderer.GetActiveCamera()
            # Set focal point
            p = self._volume.acpc.getMidACPC()
            camera.SetFocalPoint(p)
            # Set camera rotations
            r = self._volume.acpc.getRotations(deg=True)
            r = [-r[0], -r[1], -r[2]]
            trf = SisypheTransform()
            trf.setCenter(p)
            trf.setRotations(r, deg=True)
            # Axial
            if self._orient == self._DIM0:
                pr = [p[0], p[1], -500]
                pr = trf.applyToPoint(pr)
                camera.SetPosition(pr[0], pr[1], pr[2])
                camera.SetViewUp(0, 1, 0)
                camera.Roll(r[2])
                # camera.SetPosition(p[0], p[1], -500)
                # camera.Elevation(r[0])
                # camera.Azimuth(r[1])
                # camera.Roll(r[2])
            # Coronal
            elif self._orient == self._DIM1:
                pr = [p[0], 500, p[2]]
                pr = trf.applyToPoint(pr)
                camera.SetPosition(pr[0], pr[1], pr[2])
                camera.SetViewUp(0, 0, 1)
                camera.Roll(-r[1])
                # camera.SetPosition(p[0], 500, p[2])
                # camera.Elevation(r[0])
                # camera.Azimuth(r[2])
                # camera.Roll(-r[1])
            # Sagittal
            elif self._orient == self._DIM2:
                pr = [-500, p[1], p[2]]
                pr = trf.applyToPoint(pr)
                camera.SetPosition(pr[0], pr[1], pr[2])
                camera.SetViewUp(0, 0, 1)
                camera.Roll(r[0])
                # camera.SetPosition([-500, p[1], p[2]])
                # camera.Elevation(r[1])
                # camera.Azimuth(r[2])
                # camera.Roll(r[0])
            self.setCursorWorldPosition(p[0], p[1], p[2], signal=False)
            self._target = None
            self._updateCheckedAction('AC-PC alignment')
            # init default zoom if not defined
            camera.UpdateViewport(self._renderer)
            self._stack.GetMapper().UpdateInformation()
            if self._scale is None:
                fov = self._volume.getFieldOfView()
                self._renderer.ResetCamera(0.0, fov[0], 0.0, fov[1], 0.0, fov[2])
                self._scale = camera.GetParallelScale()
                p = list(camera.GetFocalPoint())
                self._cursor.SetPosition(p)
            self._renderwindow.Render()
            if signal: self.TrajectoryACPCAligned.emit(self)

    def setTrajectoryToDefault(self, signal=True):
        super()._updateCameraOrientation()
        self._target = None
        self._updateCheckedAction('Default alignment')
        if signal: self.TrajectoryDefaultAligned.emit(self)

    def getTrajectory(self):
        camera = self._renderer.GetActiveCamera()
        return camera.GetViewPlaneNormal()

    def isCameraAligned(self):
        return self._menuAlignGroup.checkedAction().text()[0] == '3'

    def isACPCAligned(self):
        return self._menuAlignGroup.checkedAction().text()[0] == 'A'

    def isToolAligned(self):
        return self._menuAlignGroup.checkedAction().text()[0] == 'T'

    def isDefaultAligned(self):
        return self._menuAlignGroup.checkedAction().text()[0] == 'D'

    def setSlabThickness(self, v=0.0, signal=True):
        if isinstance(v, float):
            mapper = self._volumeslice.GetMapper()
            mapper.SetSlabThickness(v)
            mapper.SetAutoAdjustImageQuality(v > 0.0)
            self.updateRender()
            if signal: self.SlabChanged.emit(self, v, self.getSlabType())
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSlabThickness(self):
        return self._volumeslice.GetMapper().GetSlabThickness()

    def setSlabType(self, v='Sum', signal=True):
        if isinstance(v, str):
            if v == 'Min': self._volumeslice.GetMapper().SetSlabTypeToMin()
            elif v == 'Max': self._volumeslice.GetMapper().SetSlabTypeToMax()
            elif v == 'Mean': self._volumeslice.GetMapper().SetSlabTypeToMean()
            else: self._volumeslice.GetMapper().SetSlabTypeToSum()
            if signal: self.SlabChanged.emit(self, self.getSlabThickness(), v)

    def setSlabTypeToMin(self, signal=True):
        self._volumeslice.GetMapper().SetSlabTypeToMin()
        if signal: self.SlabChanged.emit(self, self.getSlabThickness(), 'Min')

    def setSlabTypeToMax(self, signal=True):
        self._volumeslice.GetMapper().SetSlabTypeToMax()
        if signal: self.SlabChanged.emit(self, self.getSlabThickness(), 'Max')

    def setSlabTypeToMean(self, signal=True):
        self._volumeslice.GetMapper().SetSlabTypeToMean()
        if signal: self.SlabChanged.emit(self, self.getSlabThickness(), 'Mean')

    def setSlabTypeToSum(self, signal=True):
        self._volumeslice.GetMapper().SetSlabTypeToSum()
        if signal: self.SlabChanged.emit(self, self.getSlabThickness(), 'Sum')

    def getSlabType(self):
        return self._volumeslice.GetMapper().GetSlabTypeAsString()

    # Private event methods

    def _onMouseMoveEvent(self, obj, evt_name):
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            last = interactorstyle.GetLastPos()
            k = self._interactor.GetKeySym()
            # Zoom, Control Key (Cmd key on mac)
            if k == 'Control_L' or self.getZoomFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Zoom
                    dx = (last[1] - self._mousepos0[1]) / 10
                    if dx < 0: base = 1.1
                    else: base = 0.9
                    z = pow(base, abs(dx))
                    if self._scale0:
                        self._renderer.GetActiveCamera().SetParallelScale(self._scale0 * z)
                    self._renderwindow.Render()
            # Pan, Alt Key
            elif k == 'Alt_L' or self.getMoveFlag() is True:
                if interactorstyle.GetButton() == 1:
                    # Camera and focal position
                    camera = self._renderer.GetActiveCamera()
                    camera.SetPosition(self._campos0)
                    camera.SetFocalPoint(self._camfocal0)
                    plane = self._volumeslice.GetMapper().GetSlicePlane()
                    p = self._getWorldFromDisplay(self._mousepos0[0],  self._mousepos0[1])
                    pfirst = [0, 0, 0]
                    plane.ProjectPoint(p, pfirst)
                    p = self._getWorldFromDisplay(last[0], last[1])
                    plast = [0, 0, 0]
                    plane.ProjectPoint(p, plast)
                    p = [self._campos0[0] + pfirst[0] - plast[0],
                         self._campos0[1] + pfirst[1] - plast[1],
                         self._campos0[2] + pfirst[2] - plast[2]]
                    camera.SetPosition(p)
                    p = [self._camfocal0[0] + pfirst[0] - plast[0],
                         self._camfocal0[1] + pfirst[1] - plast[1],
                         self._camfocal0[2] + pfirst[2] - plast[2]]
                    camera.SetFocalPoint(p)
                    self._updateBottomRightInfo()
            # Windowing, Shift Key
            elif k == 'Shift_L' or self.getLevelFlag() is True:
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
                    self._win0 = last
            elif self.getFollowFlag() is True:
                # Update cursor position information and display
                self.setCursorFromDisplayPosition(last[0], last[1])
                p = self.getCursorWorldPosition()
                self.CursorPositionChanged.emit(self, p[0], p[1], p[2])
            else:
                if interactorstyle.GetButton() == 1:
                    # Update cursor position information and display
                    self.setCursorFromDisplayPosition(last[0], last[1])
                    p = self.getCursorWorldPosition()
                    self.CursorPositionChanged.emit(self, p[0], p[1], p[2])
            self._updateBottomRightInfo()

    # tool VTK event methods

    def _onTrajectoryEndInteractionEvent(self, widget, event):
        super()._onTrajectoryEndInteractionEvent(widget, event)
        if self.isToolAligned():
            for a in self._menuAlignGroup.actions():
                if a.isChecked():
                    name = widget.getName()
                    if name == a.text():
                        self.setTrajectoryFromLineWidget(name)

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
    from Sisyphe.core.sisypheVolume import SisypheVolume

    app = QApplication(argv)
    main = QWidget()
    layout = QHBoxLayout(main)
    # SliceTrajectoryViewWidget
    print('Test SliceTrajectoryViewWidget')
    file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.xvol'
    file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.xvol'
    img1 = SisypheVolume()
    img2 = SisypheVolume()
    img1.load(file1)
    img2.load(file2)
    img2.display.getLUT().setLutToRainbow()
    img2.display.getLUT().setDisplayBelowRangeColorOn()
    view = SliceTrajectoryViewWidget()
    view.setVolume(img1)
    view.synchronisationOn()
    view.addOverlay(img2)
    view.setOverlayOpacity(0, 0.25)
    view.setTrajectoryFromNormalVector([0, 0.4472135954999579, 0.8944271909999159])
    view.setCentralCrossOpacity(0.5)
    view.setOrientationMarker('cube')
    view.setOrientationMarkerVisibilityOn()
    view.setCursorVisibilityOff()
    view.setColorbarPosition('left')
    view.setColorbarVisibilityOff()
    view.setInfoVisibilityOn()
    layout.addWidget(view)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    main.activateWindow()
    exit(app.exec_())
