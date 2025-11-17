"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any

from math import pow
from math import sqrt

from numpy import ndarray

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup

from vtk import vtkPlane
from vtk import vtkCamera
from vtk import vtkImageSlice
from vtk import vtkImageResliceMapper

from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import LineWidget

if TYPE_CHECKING:
    from vtk import vtkObject
    from vtk import vtk3DWidget
    from Sisyphe.core.sisypheVolume import SisypheVolume
    from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
    from Sisyphe.core.sisypheMesh import SisypheMeshCollection

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> SliceTrajectoryViewWidget
"""


class SliceTrajectoryViewWidget(SliceOverlayViewWidget):
    """
    SliceTrajectoryViewWidget class

    Description
    ~~~~~~~~~~~

    The SliceTrajectoryViewWidget extends SliceOverlayViewWidget by integrating advanced features for interactive
    management of 3D tools, specifically HandleWidget (targets) and LineWidget (trajectories). It provides
    functionalities for aligning the camera view with predefined anatomical landmarks (AC-PC), 3D camera vectors, or
    existing trajectory tools. This widget also introduces controls for slice thickness (slab) and step size, enhancing
    the user's ability to navigate and analyze volumetric data in a trajectory-oriented manner.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> SliceTrajectoryViewWidget

    Last revision: 20/10/2025
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

    def __init__(self,
                 overlays: SisypheVolumeCollection | None = None,
                 meshes: SisypheMeshCollection | None = None,
                 parent: QWidget | None = None) -> None:
        """
        SliceTrajectoryViewWidget instance constructor.

        Parameters
        ----------
        overlays : SisypheVolumeCollection | None (optional)
            collection of SisypheVolume displayed in the viewport as overlays (default None).
        meshes : SisypheMeshCollection | None (optional)
            collection SisypheMesh displayed in the viewport (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(overlays, meshes, parent)

        self._camera0 = None
        self._step = 1.0
        self._target = None
        self._cursorpos = [0.0, 0.0, 0.0]

        self._action['axial'].setText('First orientation')
        self._action['coronal'].setText('Second orientation')
        self._action['sagittal'].setText('Third orientation')

        self._menuAlign = QMenu('Alignment', self._popup)
        # noinspection PyTypeChecker
        self._menuAlign.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menuAlign.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menuAlign.setAttribute(Qt.WA_TranslucentBackground, True)
        self._menuAlignGroup = None
        self._popup.insertMenu(self._popup.actions()[6], self._menuAlign)
        self._updateToolMenu()

    """
    Private attributes

    _target     HandleWidget | LineWidget, current target
    """

    # Private methods

    def _addSlice(self, volume: SisypheVolume, alpha: float) -> vtkImageSlice:
        """
        Creates a new vtkImageSlice from a SisypheVolume.
        vtkImageSlice instances are internally added to a vtkImageStack.
        Currently, this method overrides superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            volume from which to extract the slice.
        alpha : float
            opacity of the slice (0.0 to 1.0).

        Returns
        -------
        vtkImageSlice
            created vtkImageSlice actor.
        """
        mapper = vtkImageResliceMapper()
        mapper.BorderOff()
        mapper.SliceAtFocalPointOn()
        mapper.SliceFacesCameraOn()
        mapper.SetInputData(volume.getVTKImage())
        slc = vtkImageSlice()
        # noinspection PyTypeChecker
        slc.SetMapper(mapper)
        prop = slc.GetProperty()
        prop.SetInterpolationTypeToLinear()
        prop.SetLookupTable(volume.display.getVTKLUT())
        prop.UseLookupTableScalarRangeOn()
        prop.SetOpacity(alpha)
        self._stack.AddImage(slc)
        return slc

    def _setCameraFocalDepth(self, p: list[float] | tuple[float, float, float] | int, signal: bool = True) -> None:
        """
        Sets the camera's focal depth, effectively moving the slice plane.
        Currently, this method overrides superclass's implementation.

        Parameters
        ----------
        p : list[float] | tuple[float, float, float] | int

            - If a list/tuple, it's the new absolute world coordinates for the focal point.
            - If an int, it's a relative step to move the focal point along the current slice normal.

        signal : bool (optional)
            If True, emits the `CursorPositionChanged` signal for synchronization (default True).
        """
        camera = self._renderer.GetActiveCamera()
        if isinstance(p, (list, tuple)):
            self._cursorpos = p
            plane = vtkPlane()
            plane.SetOrigin(p[0], p[1], p[2])  # Plane center on cursor coordinates
            # noinspection PyArgumentList
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
                # noinspection PyArgumentList
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
        # Isolines display
        if self._isoindex > -1:
            self._updateIsoLines()
        # Mesh display
        if self._meshes is not None:
            self._updateMeshes()
        # Update info
        self._updateBottomRightInfo()

    def _updateCameraClipping(self) -> None:
        """
        Updates the camera's clipping range based on the current slice step.
        This ensures that only the relevant portion of the volume around the slice is rendered.
        Currently, this method overrides superclass's implementation.
        """
        camera = self._renderer.GetActiveCamera()
        d = camera.GetDistance()
        camera.SetClippingRange(d - self._step, d + self._step)
        self.updateRender()

    def _updateCameraOrientation(self) -> None:
        """
        Overrides the parent method to update the camera's orientation and view-up vector.
        This method is crucial for aligning the slice view with the chosen orientation (axial, coronal, sagittal)
        and ensuring correct rendering of the slice. It also initializes the default zoom if not set.
        """
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

    def _updateToolMenu(self) -> None:
        """
        Update the 'Move to target' submenu in the popup menu and adds a new 'Alignment' submenu to the popup menu.
        The 'Alignment' submenu includes options for default alignment, 3D camera alignment, AC-PC alignment, and
        alignment to existing trajectory tools. Currently, this method calls superclass's implementation.
        """
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
        # noinspection PyUnresolvedReferences
        t.triggered.connect(lambda: self.setTrajectoryToDefault(signal=True))
        self._menuAlign.addAction(t)
        # 3D view Camera axis alignment
        t = QAction('3D view camera alignment', self)
        self._menuAlignGroup.addAction(t)
        t.setCheckable(True)
        t.setChecked(t.text() == checked)
        # noinspection PyUnresolvedReferences
        t.triggered.connect(lambda state, x=self: self.TrajectoryCameraAligned.emit(x))
        self._menuAlign.addAction(t)
        # AC PC alignment
        if self._volume is not None and self._volume.acpc.hasACPC():
            t = QAction('AC-PC alignment', self)
            self._menuAlignGroup.addAction(t)
            t.setCheckable(True)
            t.setChecked(t.text() == checked)
            # noinspection PyUnresolvedReferences
            t.triggered.connect(lambda state: self.setTrajectoryFromACPC(signal=True))
            self._menuAlign.addAction(t)
        # Tool alignment
        if len(self._tools) > 0:
            for tool in self._tools:
                # < Revision 10/11/2025
                # if isinstance(tool, LineWidget):
                if tool.GetObjectName() == 'LineWidget':
                    t = QAction('Tool {} alignment'.format(tool.getName()), self)
                    self._menuAlignGroup.addAction(t)
                    t.setCheckable(True)
                    t.setChecked(t.text() == checked)
                    # noinspection PyUnresolvedReferences
                    t.triggered.connect(lambda state, x=tool.getName():
                                        self.setTrajectoryFromLineWidget(x, signal=True))
                    self._menuAlign.addAction(t)
                # Revision 10/11/2025 >

    def _updateCheckedAction(self, name: str) -> None:
        """
        Updates the checked state of actions within the alignment menu group.

        Parameters
        ----------
        name : str
            text of the action to be checked.
        """
        for a in self._menuAlignGroup.actions():
            a.setChecked(a.text() == name)

    def _getInfoValuesText(self, p: list[float] | tuple[float, float, float]) -> None:
        """
        Generates additional information text, including the distance from the current slice to the active target tool.
        Currently, this method calls superclass's implementation.

        Parameters
        ----------
        p : list[float] | tuple[float, float, float]
            The world coordinates of the current cursor position.

        Returns
        -------
        str
            The formatted information text, including target distances.
        """
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

    def synchroniseTrajectoryToolAligned(self, obj: QWidget, name: str) -> None:
        """
        Synchronizes trajectory alignment to a tool between SliceTrajectoryViewWidget instances.
        This method is called by the TrajectoryToolAligned PyQt signal.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the TrajectoryToolAligned signal.
        name : str
            name of the LineWidget tool to align the trajectory with.
        """
        if self != obj:
            self.setTrajectoryFromLineWidget(name, signal=False)

    def synchroniseTrajectoryACPCAligned(self, obj: QWidget) -> None:
        """
        Synchronizes AC-PC alignment between SliceTrajectoryViewWidget instances.
        This method is called by the TrajectoryACPCAligned PyQt signal.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the TrajectoryACPCAligned signal.
        """
        if self != obj:
            self.setTrajectoryFromACPC(signal=False)
            
    def synchroniseTrajectoryVectorAligned(self, obj: QWidget, x: float, y: float, z: float) -> None:
        """
        Synchronizes trajectory alignment to a normal vector between SliceTrajectoryViewWidget instances.
        This method is called by the TrajectoryVectorAligned PyQt signal.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the TrajectoryVectorAligned signal.
        x : float
            x-component of the normal vector.
        y : float
            y-component of the normal vector.
        z : float
            z-component of the normal vector.
        """
        if self != obj:
            self.setTrajectoryFromNormalVector([x, y, z], signal=False)
            
    def synchroniseTrajectoryDefaultAligned(self, obj: QWidget) -> None:
        """
        Synchronizes default trajectory alignment between SliceTrajectoryViewWidget instances.
        This method is called by the TrajectoryDefaultAligned PyQt signal.

        Parameters
        ----------
        obj : QWidget
            The SliceTrajectoryViewWidget instance that emitted the TrajectoryDefaultAligned signal.
        """
        if self != obj:
            self.setTrajectoryToDefault(signal=False)

    def synchroniseToolMoved(self, obj: QWidget, tool:HandleWidget | LineWidget) -> None:
        """
        Synchronizes tool movement and, if the view is aligned to a tool, re-align the trajectory based on the moved
        tool. Currently, this method calls superclass's implementation.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the ToolMoved signal.
        tool : HandleWidget | LineWidget
            tool that was moved.
        """
        super().synchroniseToolMoved(obj, tool)
        name = self._menuAlignGroup.checkedAction().text()
        if name[:4] == 'Tool':
            toolname = name.split(' ')[1]
            self.setTrajectoryFromLineWidget(toolname, signal=False)

    def synchroniseSlabChanged(self, obj: QWidget, thickness: float, slabtype: str) -> None:
        """
        Synchronizes slab thickness and type changes between SliceTrajectoryViewWidget instances.
        This method is called by the SlabChanged PyQt signal.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the SlabChanged signal.
        thickness : float
            new slab thickness.
        slabtype : str
            new slab type ('Min', 'Max', 'Mean', 'Sum').
        """
        if obj != self:
            self.setSlabThickness(thickness, signal=False)
            self.setSlabType(slabtype, signal=False)

    def synchroniseStepChanged(self, obj: QWidget, step: float) -> None:
        """
        Synchronizes slice step changes between SliceTrajectoryViewWidget instances.
        This method is called by the StepChanged PyQt signal.

        Parameters
        ----------
        obj : QWidget
            SliceTrajectoryViewWidget instance that emitted the StepChanged signal.
        step : float
            new slice step value.
        """
        if obj != self:
            self.setSliceStep(step, signal=False)

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed in the widget.
        Initializes the VTK image stack and slice actor, and updates the camera orientation.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            Sisyphevolume to display.
        """
        super().setVolume(volume)
        self._updateToolMenu()

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, volume: SisypheVolume) -> None:
        """
        Replace the current displayed SisypheVolume with a new one, preserving the previous display and slab properties.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            new SisypheVolume to display.
        """
        # Copy previous display properties
        slabttype = self.getSlabType()
        slabThickness = self.getSlabThickness()
        super().replaceVolume(volume)
        # Restore display properties
        self.setSlabType(slabttype, signal=False)
        self.setSlabThickness(slabThickness, signal=False)
    # Revision 18/10/2024

    def getPopupAlignment(self) -> QMenu:
        """
        Get the popup submenu 'Alignment' of the SliceTrajectoryViewWidget instance.
        This submenu provides options for aligning the slice view.

        Returns
        -------
        QMenu
            'Alignment' submenu.
        """
        return self._menuAlign

    def popupAlignmentEnabled(self) -> None:
        """
        Enable the popup submenu 'Alignment' of the SliceTrajectoryViewWidget instance.
        """
        self._menuAlign.menuAction().setVisible(True)

    def popupAlignmentDisabled(self) -> None:
        """
        Disable the popup submenu 'Alignment' of the SliceTrajectoryViewWidget instance.
        """
        self._menuAlign.menuAction().setVisible(False)

    def setSliceStep(self, v: float, signal: bool = True) -> None:
        """
        Set the step size for moving the slice plane.

        Parameters
        ----------
        v : float
            new step size in world units (between 0.5 and 10.0).
        signal : bool (optional)
            If True, emits the `StepChanged` signal for synchronization (default True).
        """
        if isinstance(v, float):
            if 0.5 <= v <= 10.0:
                self._step = v
                if signal:
                    # noinspection PyUnresolvedReferences
                    self.StepChanged.emit(self, v)
            else: raise ValueError('parameter value {} is not between 0.5 and 10.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSliceStep(self) -> float:
        """
        Get the current step size for moving the slice plane.

        Returns
        -------
        float
            current step size in world units.
        """
        return self._step

    def hasTarget(self) -> bool:
        """
        Check if an active target (HandleWidget or LineWidget) is set for the widget.

        Returns
        -------
        bool
            True if a target is set, False otherwise.
        """
        return self._target is not None

    def getTarget(self) -> HandleWidget | LineWidget | None:
        """
        Get the currently active target (HandleWidget or LineWidget).

        Returns
        -------
        HandleWidget | LineWidget | None
            active target tool, or None if no target is set.
        """
        return self._target

    def getTargetPosition(self) -> tuple[float, float, float] | None:
        """
        Get the world coordinates of the active target.
        For a HandleWidget, it returns its position. For a LineWidget, it returns its target point (p2).

        Returns
        -------
        tuple[float, float, float] | None
            The (x, y, z) world coordinates of the target, or None if no target is set.
        """
        if self._target is not None:
            if isinstance(self._target, HandleWidget): return self._target.getPosition()
            elif isinstance(self._target, LineWidget): return self._target.getPosition2()
            else: return None
        else: raise AttributeError('_target attribute is None.')

    def setTarget(self, key: int | str | HandleWidget | LineWidget, signal: bool = True) -> None:
        """
        Set the active target tool for the widget.
        The target can be identified by its index, name, or instance.

        Parameters
        ----------
        key : int | str | HandleWidget | LineWidget
            identifier for the tool to be set as the target.
        signal : bool (optional)
            If True, emits the `ViewMethodCalled` signal for synchronization (default True).
        """
        if isinstance(key, HandleWidget | LineWidget): key = key.getName()
        if isinstance(key, (int, str)):
            if key in self._tools:
                self._target = self._tools[key]
                if signal: self.ViewMethodCalled.emit(self, 'setTarget', key)
            else: raise KeyError('invalid tool key, tool {} is not in current view.'.format(key))
        else: raise TypeError('parameter type {} is not int or str')

    def setCursorWorldPosition(self, x: float, y: float, z: float, signal: bool = True) -> None:
        """
        Set the 3D world position of the cross-shaped cursor and updates the camera's focal depth accordingly.
        Currently, this method overrides the superclass's implementation.

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
            p = [x, y, z]
            # Update camera focal
            self._setCameraFocalDepth(p, signal=False)
            # Synchronising
            if self.isSynchronised() and signal:
                x, y, z = self._cursorpos
                self.CursorPositionChanged.emit(self, x, y, z)

    def getCursorWorldPosition(self) -> list[float]:
        """
        Get the 3D world position of the cross-shaped cursor.
        Currently, this method overrides the superclass's implementation.

        Returns
        -------
        list[float]
            The (x, y, z) world coordinates of the cross-shaped cursor.
        """
        return self._cursorpos

    def setCursorFromDisplayPosition(self, x: float, y: float) -> None:
        """
        Set the cros-shaped cursor's world position from 2D display coordinates.
        The display coordinates are projected onto the current slice plane.
        Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        x : float
            2D display x-coordinate.
        y : float
            2D display y-coordinate.
        """
        p = list(self._getWorldFromDisplay(x, y))
        r = [0.0, 0.0, 0.0]
        self.getVtkPlane().ProjectPoint(p, r)
        self.setCursorWorldPosition(r[0], r[1], r[2], signal=False)

    def getDistanceFromCurrentSliceToTarget(self) -> list[float] | None:
        """
        Calculate the distance from the current slice plane to the active target tool.

        - For a HandleWidget, it returns the distance to the handle.
        - For a LineWidget, it returns distances to its entry and target points.

        Returns
        -------
        list[float] | None

            - list containing the distance(s) in mm, or None if no target is set.
            - for HandleWidget: [distance_to_handle, 0.0]
            - for LineWidget: [distance_to_target_point, distance_to_entry_point]
        """
        if self._target is not None:
            if isinstance(self._target, HandleWidget):
                return [self._target.getDistanceToPlane(self), 0.0]
            elif isinstance(self._target, LineWidget):
                d = self._target.getDistancesToPlane(self)
                return [d[1], d[0]]
            else: raise TypeError('Invalid _target attribute type {}'.format(type(self._target)))
        else: return None

    def setTrajectoryFromCamera(self, t: vtkCamera, signal: bool = True) -> None:
        """
        Align the slice view's camera with the orientation of a given 3D camera.
        This sets the view to match an external 3D perspective.

        Parameters
        ----------
        t : vtkCamera
            vtkCamera instance whose orientation will be used for alignment.
        signal : bool (optional)
            If True, emits the TrajectoryCameraAligned signal for synchronization (default True).
        """
        if isinstance(t, vtkCamera):
            camera = self._renderer.GetActiveCamera()
            camera.SetPosition(t.GetPosition())
            self._camera0 = t.GetPosition()
            self._updateCameraOrientation()
            self._updateCameraClipping()
            self._updateCheckedAction('3D view camera alignment')
            self._target = None
            if self._isoindex > -1: self._updateIsoLines()
            if self._meshes is not None: self._updateMeshes()
            if signal:
                # noinspection PyUnresolvedReferences
                self.TrajectoryCameraAligned.emit()
        else: raise TypeError('parameter type {} is not vtkCamera.'.format(type(t)))

    def setTrajectoryFromLineWidget(self, name: str, signal: bool = True) -> None:
        """
        Aligns the slice view's camera with a specified LineWidget (trajectory tool).
        The camera's focal point is set to the tool's target point (p2), and its position is set along the line defined
        by the tool, looking towards the target.

        Parameters
        ----------
        name : str
            name of the LineWidget tool to align the trajectory with.
        signal : bool (optional)
            If True, emits the TrajectoryToolAligned signal for synchronization (default True).
        """
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
            if self._isoindex > -1: self._updateIsoLines()
            if self._meshes is not None: self._updateMeshes()
            if signal:
                # noinspection PyUnresolvedReferences
                self.TrajectoryToolAligned.emit(self, name)
        else: raise TypeError('parameter type {} is not LineWidget.'.format(type(tool)))

    def setTrajectoryFromNormalVector(self, t: ndarray | list[float], signal: bool = True) -> None:
        """
        Aligns the slice view's camera such that its view plane normal matches a given vector.
        The camera's focal point is set to the volume's center.

        Parameters
        ----------
        t : ndarray | list[float]
            A 3-element list or NumPy array representing the normal vector (x, y, z).
        signal : bool (optional)
            If True, emits the TrajectoryVectorAligned signal for synchronization (default True).
        """
        if isinstance(t, ndarray): t = t.tolist()
        if isinstance(t, list):
            plane = vtkPlane()
            # noinspection PyArgumentList
            plane.SetNormal(t)
            c = self._volume.getCenter()
            # noinspection PyArgumentList
            plane.SetOrigin(c)
            camera = self._renderer.GetActiveCamera()
            camera.SetFocalPoint(c)
            p = [c[0] + t[0] * 500,
                 c[1] + t[1] * 500,
                 c[2] + t[2] * 500]
            camera.SetPosition(p)
            self._camera0 = p
            self._updateCameraOrientation()
            if self._isoindex > -1: self._updateIsoLines()
            if self._meshes is not None: self._updateMeshes()
            if signal:
                # noinspection PyUnresolvedReferences
                self.TrajectoryVectorAligned.emit(self, t[0], t[1], t[2])
        else: raise TypeError('parameter type {} is not list or numpy array.'.format(type(t)))

    def setTrajectoryFromACPC(self, signal: bool = True) -> None:
        """
        Align the slice view's camera based on the Anterior Commissure (AC) and Posterior Commissure (PC) landmarks of
        the reference SisypheVolume. The camera's focal point is set to the mid-ACPC point, and its orientation is
        adjusted according to the AC-PC alignment.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the TrajectoryACPCAligned signal for synchronization (default True).
        """
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
            if self._isoindex > -1: self._updateIsoLines()
            if self._meshes is not None: self._updateMeshes()
            self._renderwindow.Render()
            if signal:
                # noinspection PyUnresolvedReferences
                self.TrajectoryACPCAligned.emit(self)

    def setTrajectoryToDefault(self, signal: bool = True) -> None:
        """
        Reset the slice view's camera to its default orientation and position.
        This typically aligns the view with the primary anatomical axes.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the TrajectoryDefaultAligned signal for synchronization (default True).
        """
        super()._updateCameraOrientation()
        self._target = None
        self._updateCheckedAction('Default alignment')
        if self._isoindex > -1: self._updateIsoLines()
        if self._meshes is not None: self._updateMeshes()
        if signal:
            # noinspection PyUnresolvedReferences
            self.TrajectoryDefaultAligned.emit(self)

    def getTrajectory(self) -> tuple[float, float, float]:
        """
        Get the current trajectory vector, which corresponds to the camera's view plane normal.

        Returns
        -------
        tuple[float, float, float]
            (x, y, z) components of the camera's view plane normal.
        """
        camera = self._renderer.GetActiveCamera()
        return camera.GetViewPlaneNormal()

    def isCameraAligned(self) -> bool:
        """
        Check if the slice view is currently aligned with a 3D camera.

        Returns
        -------
        bool
            True if aligned with a 3D camera, False otherwise.
        """
        return self._menuAlignGroup.checkedAction().text()[0] == '3'

    def isACPCAligned(self) -> bool:
        """
        Check if the slice view is currently aligned with the AC-PC line.

        Returns
        -------
        bool
            True if aligned with AC-PC, False otherwise.
        """
        return self._menuAlignGroup.checkedAction().text()[0] == 'A'

    def isToolAligned(self) -> bool:
        """
        Check if the slice view is currently aligned with a trajectory tool (LineWidget).

        Returns
        -------
        bool
            True if aligned with a tool, False otherwise.
        """
        return self._menuAlignGroup.checkedAction().text()[0] == 'T'

    def isDefaultAligned(self) -> bool:
        """
        Check if the slice view is currently set to its default alignment.

        Returns
        -------
        bool
            True if set to default alignment, False otherwise.
        """
        return self._menuAlignGroup.checkedAction().text()[0] == 'D'

    def setSlabThickness(self, v: float = 0.0, signal: bool = True) -> None:
        """
        Set the thickness of the slab. The signal is blended into the slab thickness using one of the following
        functions: mean, maximum, minimum, cumulative sum.

        Parameters
        ----------
        v : float (optional)
            slab thickness in world units (default 0.0).
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        if isinstance(v, float):
            mapper = self._volumeslice.GetMapper()
            mapper.SetSlabThickness(v)
            mapper.SetAutoAdjustImageQuality(v > 0.0)
            self.updateRender()
            if signal:
                # noinspection PyUnresolvedReferences
                self.SlabChanged.emit(self, v, self.getSlabType())
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSlabThickness(self) -> float:
        """
        Get the current slab thickness. The signal is blended into the slab thickness using one of the following
        functions: mean, maximum, minimum, cumulative sum.

        Returns
        -------
        float
            The current slab thickness in world units.
        """
        return self._volumeslice.GetMapper().GetSlabThickness()

    def setSlabType(self, v='Sum', signal: bool = True) -> None:
        """
        Set how the signal is blended wihtin the slab thickness (e.g., Min, Max, Mean, Sum).

        Parameters
        ----------
        v : str (optional)
            blending function ('Min', 'Max', 'Mean', or 'Sum', default 'Sum').
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        if isinstance(v, str):
            if v == 'Min': self._volumeslice.GetMapper().SetSlabTypeToMin()
            elif v == 'Max': self._volumeslice.GetMapper().SetSlabTypeToMax()
            elif v == 'Mean': self._volumeslice.GetMapper().SetSlabTypeToMean()
            else: self._volumeslice.GetMapper().SetSlabTypeToSum()
            if signal:
                # noinspection PyUnresolvedReferences
                self.SlabChanged.emit(self, self.getSlabThickness(), v)

    def setSlabTypeToMin(self, signal: bool = True)-> None:
        """
        Set the slab blending fnuction to 'Min' to display the minimum intensity value across the slab.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        self._volumeslice.GetMapper().SetSlabTypeToMin()
        if signal:
            # noinspection PyUnresolvedReferences
            self.SlabChanged.emit(self, self.getSlabThickness(), 'Min')

    def setSlabTypeToMax(self, signal: bool = True)-> None:
        """
        Set the slab blending fnuction to 'Max' to display the maximum intensity value across the slab.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        self._volumeslice.GetMapper().SetSlabTypeToMax()
        if signal:
            # noinspection PyUnresolvedReferences
            self.SlabChanged.emit(self, self.getSlabThickness(), 'Max')

    def setSlabTypeToMean(self, signal: bool = True)-> None:
        """
        Set the slab blending fnuction to 'Mean' to display the mean intensity value across the slab.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        self._volumeslice.GetMapper().SetSlabTypeToMean()
        if signal:
            # noinspection PyUnresolvedReferences
            self.SlabChanged.emit(self, self.getSlabThickness(), 'Mean')

    def setSlabTypeToSum(self, signal: bool = True)-> None:
        """
        Set the slab blending fnuction to 'Sum' to display the sum of intensity values across the slab.

        Parameters
        ----------
        signal : bool (optional)
            If True, emits the SlabChanged signal for synchronization (default True).
        """
        self._volumeslice.GetMapper().SetSlabTypeToSum()
        if signal:
            # noinspection PyUnresolvedReferences
            self.SlabChanged.emit(self, self.getSlabThickness(), 'Sum')

    def getSlabType(self) -> str:
        """
        Get how the signal is blended wihtin the slab thickness (e.g., Min, Max, Mean, Sum).

        Returns
        -------
        str
            The current slab type ('Min', 'Max', 'Mean', or 'Sum').
        """
        return self._volumeslice.GetMapper().GetSlabTypeAsString()

    # Private event methods

    def _onMouseMoveEvent(self, obj: vtkObject , evt_name: str) -> None:
        """
        Handle mouse move VTK events for slice manipulation.
        This includes zooming, panning, windowing, and cursor position updates, with specific logic for
        trajectory-aligned views. Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        obj : vtkObject
            VTK object that triggered the event.
        evt_name : str
            name of the event (MouseMoveEvent).
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

    def _onTrajectoryEndInteractionEvent(self, widget: vtk3DWidget, event: Any):
        """
        Handles the end of interaction with a LineWidget (trajectory tool).
        It updates the cursor position to the tool's target point and, if the view is aligned to a tool, re-aligns the
        trajectory based on the moved tool. Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        widget : vtk3DWidget
            `LineWidget` that triggered the event.
        event : Any
            event parameter.
        """
        super()._onTrajectoryEndInteractionEvent(widget, event)
        if self.isToolAligned():
            for a in self._menuAlignGroup.actions():
                if a.isChecked():
                    name = widget.getName()
                    if name == a.text():
                        self.setTrajectoryFromLineWidget(name)
