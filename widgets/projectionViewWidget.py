"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, Visualization, https://vtk.org/
"""

from os.path import join
from os.path import exists

import typing

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QWidgetAction

from vtk import vtkImageSlice
from vtk import VTK_FONT_FILE

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheConstants import getICBM152Path
from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget
from Sisyphe.widgets.multiViewWidgets import MultiViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.gui.dialogWait import DialogWait


__all__ = ['ProjectionViewWidget',
           'MultiProjectionViewWidget',
           'IconBarMultiProjectionViewWidget']


"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QFame -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> ProjectionViewWidget
    - QWidget -> MultiViewWidget -> GridViewWidget -> MultiProjectionViewWidget
              -> IconBarWidget -> IconBarMultiProjectionViewWidget
"""


class ProjectionViewWidget(SliceOverlayViewWidget):
    """
    ProjectionViewWidget class

    Description
    ~~~~~~~~~~~

    Class used to display 2D projections of SisypheVolume instance.

    Projection directions are: left, right, mid-left, mid-right, ant, post, top, bottom.
    The projection is processed with a depth expressed in mm from the head surface (default 0.0, whole brain, no thickness).
    Operators applied to voxels on a projection line: maximum, mean, median, standard deviation, sum.
    The volume can be cut out to a specified depth (slice index) in the direction of projection.

    Inheritance
    ~~~~~~~~~~~

    QFame -> AbstractViewWidget -> SliceViewWidget -> SliceOverlayViewWidget -> ProjectionViewWidget

    Creation: 12/10/2024
    Last Revision: 21/11/2024
    """

    # Private method

    def _updateProjection(self):
        if self._ref is not None:
            opacity = self.getProjectionOpacity()
            if self._cut == 0:
                fimg = self._ref.getProjection(self._direction,
                                               self._thickness,
                                               self._operator,
                                               'native')
            else:
                fimg = self._ref.getCroppedProjection(self._cut,
                                                      self._direction,
                                                      self._thickness,
                                                      self._operator,
                                                      'native')
            super().setVolume(fimg)
            self._foreground = self._volumeslice
            if self._background is not None:
                self._stack.AddImage(self._background)
                self._foreground.GetProperty().SetLayerNumber(1)
                self._foreground.GetProperty().SetOpacity(opacity)
                self._background.GetProperty().SetLayerNumber(0)
                self._background.GetProperty().SetOpacity(1.0)
            else:
                self._foreground.GetProperty().SetLayerNumber(0)
                self._foreground.GetProperty().SetOpacity(1.0)
            self.setOrientation(0)
            camera = self._renderer.GetActiveCamera()
            p = list(camera.GetFocalPoint())
            p[2] = 0.0
            camera.SetFocalPoint(p)
            self._renderwindow.Render()

    def _initSettings(self):
        super()._initSettings()
        op = self._settings.getFieldValue('Viewport', 'ProjectionOperator')[0]
        if op == 'Max': self._operator = 'max'
        elif op == 'Mean': self._operator = 'mean'
        elif op == 'Median': self._operator = 'median'
        elif op == 'Standard deviation': self._operator = 'std'
        else: self._operator = None
        self._thickness = self._settings.getFieldValue('Viewport', 'ProjectionDepth')

    def _initOrientationLabels(self):
        if self._direction == 'left':
            if self._cut == 0:
                topinfo = '\n\nLeft hemisphere'
                leftinfo = ''
                rightinfo = ''
            else:
                topinfo = '\n\nMedial right hemisphere'
                leftinfo = ''
                rightinfo = ''
        elif self._direction == 'right':
            if self._cut == 0:
                topinfo = '\n\nRight hemisphere'
                leftinfo = ''
                rightinfo = ''
            else:
                topinfo = '\n\nMedial left hemisphere'
                leftinfo = ''
                rightinfo = ''
        elif self._direction == 'ant':
            topinfo = ''
            leftinfo = 'L'
            rightinfo = 'R'
        elif self._direction == 'post':
            topinfo = ''
            leftinfo = 'R'
            rightinfo = 'L'
        elif self._direction == 'top':
            topinfo = ''
            leftinfo = 'R'
            rightinfo = 'L'
        elif self._direction == 'bottom':
            topinfo = ''
            leftinfo = 'L'
            rightinfo = 'R'
        else:
            topinfo = ''
            leftinfo = ''
            rightinfo = ''
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
        info.SetInput(topinfo)
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
        info.SetInput(leftinfo)
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
        info.SetInput(rightinfo)
        info.SetVisibility(False)
        # Bottom
        self._info['bottomcenter'].SetInput('')

    def _updateBottomRightInfo(self):
        if self._ref is not None:
            if self._aal is not None or self._brodmann is not None:
                interactorstyle = self._window.GetInteractorStyle()
                p = interactorstyle.GetLastPos()
                p = list(self._getWorldFromDisplay(p[0], p[1]))
                txt = ''
                if self.getInfoPositionVisibility():
                    d = 2 - self._orient
                    p[d] = self._renderer.GetActiveCamera().GetFocalPoint()[d]
                    x, y = p[0], p[1]
                    xm, ym, _ = self._volume.getFieldOfView()
                    if (0 <= x < xm) and (0 <= y < ym):
                        sx, sy, _ = self._ref.getSpacing()
                        x = int(x / sx)
                        y = int(y / sy)
                        if self._aal is not None:
                            try: txt += self._aal.acquisition.getLabel(self._aal[x, y, 0])
                            except: return
                        if self._brodmann is not None:
                            if self._aal is not None: txt += '\n'
                            try: txt += self._brodmann.acquisition.getLabel(self._brodmann[x, y, 0])
                            except: return
                self.getBottomRightInfo().SetInput(txt)
                self._renderwindow.Render()

    # < Revision 17/10/2024
    # override _updateCameraOrientation method
    # info labels bugfix
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
        elif self._orient == self._DIM1:
            camera.SetViewUp(0, 0, 1)
            camera.SetPosition(p[0], 500, p[2])
        else:
            camera.SetViewUp(0, 0, 1)
            camera.SetPosition(-500, p[1], p[2])
        self._setCameraFocalDepth(p, signal=False)
        self._updateRuler(signal=False)
        self._renderwindow.Render()
    # Revision 17/10/2024 >

    # Special method

    """
    Class attributes
    
    _cut: int                   cut out depth (slice index)
    _direction: str             projection direction (left, right, ant, post, top, bottom)
    _operator: str              operator applied to voxels on a projection line (max, mean, median, std)
    _thickness: int             projection depth in mm
    _ref: SisypheVolume         volume to display (reference volume)
    _t1: SisypheVolume          projection of t1 atlas
    _aal: SisypheVolume         projection of aal atlas
    _brodmann: SisypheVolume    projection of brodmann atlas
    _foreground: vtkImageSlice  vtkImageSlice of the reference volume displayed as foreground
    _background: vtkImageSlice  vtkImageSlice of the ICBM152 T1 atlas displayed as background
    """

    def __init__(self,
                 direction: str = 'left',
                 operator: str = 'max',
                 thickness: float = 10.0,
                 cut: int = 0,
                 parent=None):
        self._cut: int = cut
        self._direction: str = direction
        self._operator: str | None = None
        self._thickness: float | None = None
        super().__init__(parent)

        if direction == 'left':
            if self._cut == 0: self.setName('Left')
            else: self.setName('Right-int')
        elif direction == 'right':
            if self._cut == 0: self.setName('Right')
            else: self.setName('Left-int')
        else: self.setName(self._direction.capitalize())

        if self._operator is None: self._operator = operator
        if self._thickness is None: self._thickness = thickness

        self._ref: SisypheVolume | None = None
        self._t1: SisypheVolume | None = None
        self._aal: SisypheVolume | None = None
        self._brodmann: SisypheVolume | None = None
        self._foreground: vtkImageSlice | None = None
        self._background: vtkImageSlice | None = None

        # Menu corrections

        self._action['synchronisation'].setVisible(False)
        self._action['followflag'].setVisible(False)
        self._action['moveoverlayflag'].setVisible(False)
        self._action['showcursor'].setVisible(False)
        self._action['showmarker'].setVisible(False)
        self._action['showruler'].setVisible(False)
        self._action['showMesh'].setVisible(False)
        self._action['showpos'].setText('Anatomy label at cursor position')
        self._action['showac'].setVisible(False)
        self._action['showpc'].setVisible(False)
        self._action['showacpc'].setVisible(False)
        self._action['showframe'].setVisible(False)
        self._action['showicbm'].setVisible(False)
        self._action['showvalue'].setVisible(False)
        self._action['target'].setVisible(False)
        self._action['trajectory'].setVisible(False)
        self._action['captureseries'].setVisible(False)

        self._popup.removeAction(self._menuOrientation.menuAction())
        self._popup.removeAction(self._menuRulerPos.menuAction())
        self._popup.removeAction(self._menuShape.menuAction())
        self._menuZoom.removeAction(self._menuMoveTarget.menuAction())
        self._menuInformation.removeAction(self._menuOverlayVoxel.menuAction())
        self._menuInformation.removeAction(self._menuShape.menuAction())

        self._action['showcursor'].setChecked(False)
        self._action['showmarker'].setChecked(False)
        # self._action['showpos'].setChecked(False)

        # Viewport tooltip

        self._tooltipstr = 'View controls:\n' \
                           '\tMouseWheel + CTRL key (CMD key MacOS) to change zoom,\n' \
                           '\tUp or Left + CTRL key (CMD key MacOS) to zoom out,\n' \
                           '\tDown or Right + CTRL key (CMD key MacOS) to zoom in,\n' \
                           '\tLeft-click to move cursor position,\n' \
                           '\tLeft-click + CTRL key (CMD key MacOS) and drag to change zoom,\n' \
                           '\tLeft-click + ALT key and drag to pan,\n' \
                           '\tLeft-click + SHIFT key and drag to change window/level,\n' \
                           '\tRight-click + CTRL key (CMD key MacOS)\n' \
                           '\tor Middle-click to display popup menu.'
        if self._action['showtooltip'].isChecked(): self.setToolTip(self._tooltipstr)
        else: self.setToolTip('')

    # Public synchronisation event methods

    def synchroniseRenderUpdated(self, obj):
        if self != obj and self.hasVolume():
            w = obj.getProjection().display.getWindow()
            self._volume.display.setWindow(w[0], w[1])
            self._renderwindow.Render()

    # Public methods

    # < Revision 21/11/2024
    # add mask parameter
    def setVolume(self,
                  foreground: SisypheVolume,
                  background: SisypheVolume | None = None,
                  mask: SisypheVolume | None = None) -> None:
        if self.hasVolume():
            super().removeAllOverlays()
            super().removeVolume()
            self._ref = None
        bimg = None
        if self._cut == 0:
            # < Revision 21/11/2024
            # add mask parameter
            fimg = foreground.getProjection(self._direction,
                                            self._thickness,
                                            self._operator,
                                            'native', mask)
            # Revision 21/11/2024 >
            if foreground.acquisition.isICBM152():
                path = join(getICBM152Path(), 'PROJECTIONS')
                if exists(path):
                    if self._direction == 'left':
                        t1 = join(path, 'projection_t1_brain_left_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_left_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_left_icbm152.xvol')
                    elif self._direction == 'right':
                        t1 = join(path, 'projection_t1_brain_right_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_right_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_right_icbm152.xvol')
                    elif self._direction == 'ant':
                        t1 = join(path, 'projection_t1_brain_ant_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_ant_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_ant_icbm152.xvol')
                    elif self._direction == 'post':
                        t1 = join(path, 'projection_t1_brain_post_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_post_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_post_icbm152.xvol')
                    elif self._direction == 'top':
                        t1 = join(path, 'projection_t1_brain_top_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_top_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_top_icbm152.xvol')
                    elif self._direction == 'bottom':
                        t1 = join(path, 'projection_t1_brain_bottom_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_bottom_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_bottom_icbm152.xvol')
                    else:  t1, aal, brd = '', '', ''
                    if self._t1 is None:
                        if exists(t1):
                            self._t1 = SisypheVolume()
                            self._t1.load(t1)
                            bimg = self._t1
                    else: bimg = self._t1
                    if self._aal is None and exists(aal):
                        self._aal = SisypheVolume()
                        self._aal.load(aal)
                    if self._brodmann is None and exists(brd):
                        self._brodmann = SisypheVolume()
                        self._brodmann.load(brd)
            else:
                self._t1 = None
                self._aal = None
                self._brodmann = None
                if background is not None:
                    bimg = background.getProjection(self._direction,
                                                    self._thickness,
                                                    self._operator,
                                                    'native', mask)
        else:
            # < Revision 21/11/2024
            # add mask parameter
            fimg = foreground.getCroppedProjection(self._cut,
                                                   self._direction,
                                                   self._thickness,
                                                   self._operator,
                                                   'native', mask)
            # Revision 21/11/2024 >
            if foreground.acquisition.isICBM152():
                path = join(getICBM152Path(), 'PROJECTIONS')
                if exists(path):
                    bimg = SisypheVolume()
                    if self._direction == 'left':
                        t1 = join(path, 'projection_t1_brain_right-int_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_right-int_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_right-int_icbm152.xvol')
                    elif self._direction == 'right':
                        t1 = join(path, 'projection_t1_brain_left-int_icbm152_asym_template.xvol')
                        aal = join(path, 'projection_anatomy_left-int_icbm152.xvol')
                        brd = join(path, 'projection_brodmann_left-int_icbm152.xvol')
                    else:  t1, aal, brd = '', '', ''
                    if self._t1 is None:
                        if exists(t1):
                            self._t1 = SisypheVolume()
                            self._t1.load(t1)
                            bimg = self._t1
                    else: bimg = self._t1
                    if self._aal is None and exists(aal):
                        self._aal = SisypheVolume()
                        self._aal.load(aal)
                    if self._brodmann is None and exists(brd):
                        self._brodmann = SisypheVolume()
                        self._brodmann.load(brd)
            else:
                self._t1 = None
                self._aal = None
                self._brodmann = None
                if background is not None:
                    bimg = background.getCroppedProjection(self._cut,
                                                           self._direction,
                                                           self._thickness,
                                                           self._operator,
                                                           'native', mask)
        self._ref = foreground
        super().setVolume(fimg)
        self._foreground = self._volumeslice
        if bimg is not None:
            super().addOverlay(bimg)
            self._foreground.GetProperty().SetLayerNumber(1)
            self._foreground.GetProperty().SetOpacity(1.0)
            self._background = self._ovlslices[0]
            self._background.GetProperty().SetLayerNumber(0)
            self._background.GetProperty().SetOpacity(1.0)
        else:
            self._foreground.GetProperty().SetLayerNumber(0)
            self._foreground.GetProperty().SetOpacity(1.0)
        self.setOrientation(0)
        camera = self._renderer.GetActiveCamera()
        p = list(camera.GetFocalPoint())
        p[2] = 0.0
        camera.SetFocalPoint(p)
        self._renderwindow.Render()
    # Revision 21/11/2024 >

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, foreground: SisypheVolume) -> None:
        if self.hasVolume():
            self._ref = foreground
    # Revision 18/10/2024

    def getProjection(self) -> SisypheVolume | None:
        return self._volume

    def getVolume(self) -> SisypheVolume | None:
        return self._ref

    def hasVolume(self) -> bool:
        return self._ref is not None

    def removeVolume(self):
        super().removeAllOverlays()
        super().removeVolume()
        self._ref = None
        self._t1 = None
        self._aal = None
        self._brodmann = None

    def setDirectionOfProjection(self, d: str = 'left') -> None:
        if d in ('left', 'right', 'ant', 'post', 'top', 'bottom'):
            self._direction = d
            self._cut = 0
        else: raise ValueError('Invalid direction parameter \'{}\'.'.format(d))

    def setDirectionOfProjectionToLeft(self) -> None:
        self.setDirectionOfProjection('left')

    def setDirectionOfProjectionToRight(self) -> None:
        self.setDirectionOfProjection('right')

    def setDirectionOfProjectionToAnterior(self) -> None:
        self.setDirectionOfProjection('ant')

    def setDirectionOfProjectionToPosterior(self) -> None:
        self.setDirectionOfProjection('post')

    def setDirectionOfProjectionToTop(self) -> None:
        self.setDirectionOfProjection('top')

    def setDirectionOfProjectionToBottom(self) -> None:
        self.setDirectionOfProjection('bottom')

    def getDirectionOfProjection(self) -> str:
        return self._direction

    def isLeftProjection(self) -> bool:
        return self._direction == 'left'

    def isRightProjection(self) -> bool:
        return self._direction == 'right'

    def isAnteriorProjection(self) -> bool:
        return self._direction == 'ant'

    def isPosteriorProjection(self) -> bool:
        return self._direction == 'post'

    def isTopProjection(self) -> bool:
        return self._direction == 'top'

    def isBottomProjection(self) -> bool:
        return self._direction == 'bottom'

    def setOperatorOfProjection(self, v: str = 'max'):
        if v in ('max', 'mean', 'median', 'std', 'sum'):
            self._operator = v
            if self._ref is not None: self._updateProjection()
        else: raise ValueError('Invalid operator parameter \'{}\'.'.format(v))

    def getOperatorOfProjection(self) -> str:
        return self._operator

    def setDepthOfProjection(self, v: float = 0.0) -> None:
        if 20.0 >= v >= 5.0:
            self._thickness = v
            if self._ref is not None: self._updateProjection()
        else: raise ValueError('Thickness parameter must be between 5.0 and 20 mm.')

    def getDepthOfProjection(self) -> float:
        return self._thickness

    def setCuttingSliceIndex(self, v: int = 0) -> None:
        self._cut = v
        if self._cut > 0:
            # self._initOrientationLabels()
            if self._direction == 'left':
                self.setName('Right-int')
                self._info['topcenter'].SetInput('\n\nMedial right hemisphere')
            elif self._direction == 'right':
                self.setName('Left-int')
                self._info['topcenter'].SetInput('\n\nMedial left hemisphere')

    def getCuttingSliceIndex(self) -> int:
        return self._cut

    def isWholeBrainProjection(self) -> bool:
        return self._cut == 0

    def setProjectionOpacity(self, alpha: float = 1.0):
        if self._foreground is not None:
            if 1.0 >= alpha >= 0.0:
                self.setVolumeOpacity(alpha, signal=False)
                self._renderwindow.Render()
            else: raise ValueError('Opacity parameter must be between 0.0 and 1.0.')

    def getProjectionOpacity(self) -> float:
        return self.getVolumeOpacity()

    def updateWindowingFromReference(self) -> None:
        if self._ref is not None:
            w = self._ref.display.getWindow()
            self._volume.display.setWindow(w[0], w[1])
            self._renderwindow.Render()

    def updateLutFromReference(self) -> None:
        if self._ref is not None:
            lut = self._ref.display.getLUT()
            # < Revision 17/10/2024
            # self._volume.display.setLut(lut
            self._volume.display.getLUT().copyFrom(lut)
            # Revision 17/10/2024 >
            self._renderwindow.Render()

    def showAll(self, signal=True):
        self.setInfoVisibilityOn(signal)
        self.setColorbarVisibilityOn(signal)
        self.setOrientationLabelsVisibilityOn(signal)
        self.setTooltipVisibilityOn(signal)

    # Private vtk event methods

    def _onWheelForwardEvent(self,  obj, evt_name) -> None:
        if self.hasVolume():
            if self._interactor.GetControlKey(): self.zoomOut()

    def _onWheelBackwardEvent(self,  obj, evt_name) -> None:
        if self.hasVolume():
            if self._interactor.GetControlKey(): self.zoomIn()

    def _onKeyPressEvent(self,  obj, evt_name):
        if self.hasVolume():
            interactorstyle = self._window.GetInteractorStyle()
            k = interactorstyle.GetKeySym()
            if self._interactor.GetControlKey():
                if k == 'Up' or k == 'Left': self.zoomIn()
                elif k == 'Down' or k == 'Right': self.zoomOut()

    def _onKeyReleaseEvent(self, obj, evt_name):
        pass

    # Qt event methods

    def showEvent(self, a0: typing.Optional[QShowEvent]) -> None:
        if self._ref is not None:
            if self._ref.acquisition.isICBM152():
                self.setProjectionOpacity(0.5)


class MultiProjectionViewWidget(MultiViewWidget):
    """
    MultiProjectionViewWidget class

    Description
    -----------

    Derived from GridViewWidget class. Class used to display projections (left, right, ant, post, top, bottom) in a
    multiple view widget.

    Inheritance
    -----------

    QWidget -> MultiViewWidget -> GridViewWidget -> MultiProjectionViewWidget

    Creation: 12/10/2024
    Last revision: 07/12/2024
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(2, 4, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self):
        self.setViewWidget(0, 0, ProjectionViewWidget('left'))
        self.setViewWidget(1, 0, ProjectionViewWidget('right'))
        self.setViewWidget(0, 1, ProjectionViewWidget('left'))
        self.setViewWidget(1, 1, ProjectionViewWidget('right'))
        self.setViewWidget(0, 2, ProjectionViewWidget('ant'))
        self.setViewWidget(1, 2, ProjectionViewWidget('post'))
        self.setViewWidget(0, 3, ProjectionViewWidget('top'))
        self.setViewWidget(1, 3, ProjectionViewWidget('bottom'))
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        for i in range(8):
            w1 = self.getViewWidgetAt(i // 4, i % 4)
            w1.synchronisationOn()
            for j in range(8):
                if j != i:
                    w2 = self.getViewWidgetAt(j // 4, j % 4)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                    w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                    w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)

    # Public methods

    # < Revision 21/11/2024
    # add mask parameter
    def setVolume(self,
                  foreground: SisypheVolume,
                  background: SisypheVolume | None = None,
                  mask: SisypheVolume | None = None) -> None:
        if foreground.acquisition.isICBM152(): mid = foreground.getSize()[0] // 2
        else:
            # < Revision 09/06/2025
            # try: mid = int(foreground.getCentroid()[0])
            try: mid = int(foreground.getCentroid()[0] / foreground.getSpacing()[0])
            # Revision 09/06/2025 >
            # < Revision 07/12/2024
            except: mid = foreground.getSize()[0] // 2
            # Revision 07/12/2024 >
        self._views[(0, 1)].setCuttingSliceIndex(mid + 1)
        self._views[(1, 1)].setCuttingSliceIndex(mid - 1)
        for k in self._views:
            self._views[k].setVolume(foreground, background, mask)
    # Revision 21/11/2024 >

    # < Revision 18/10/2024
    # add replaceVolume
    def replaceVolume(self, foreground: SisypheVolume) -> None:
        if self.hasVolume():
            for k in self._views:
                self._views[k].replaceVolume(foreground)
    # Revision 18/10/2024 >

    def getVolume(self) -> SisypheVolume | None:
        return self._views[(0, 0)].getVolume()

    def hasVolume(self) -> bool:
        return self._views[(0, 0)].hasVolume()

    def removeVolume(self):
        for k in self._views:
            self._views[k].removeVolume()

    def setOperatorOfProjection(self, v: str = 'max'):
        for k in self._views:
            self._views[k].setOperatorOfProjection(v)

    def getOperatorOfProjection(self) -> str:
        return self._views[(0, 0)].getOperatorOfProjection()

    def setDepthOfProjection(self, v: float = 0.0) -> None:
        for k in self._views:
            self._views[k].setDepthOfProjection(v)

    def getDepthOfProjection(self) -> float:
        return self._views[(0, 0)].getDepthOfProjection()

    def setProjectionOpacity(self, alpha: float = 1.0):
        for k in self._views:
            self._views[k].setProjectionOpacity(alpha)

    def getProjectionOpacity(self) -> float:
        return self._views[(0, 0)].getProjectionOpacity()

    def updateLutFromReference(self) -> None:
        for k in self._views:
            self._views[k].updateLutFromReference()

    def updateWindowingFromReference(self) -> None:
        for k in self._views:
            self._views[k].updateWindowingFromReference()


class IconBarMultiProjectionViewWidget(IconBarWidget):
    """
    IconBarMultiProjectionViewWidget class

    Description
    -----------

    Derived from IconBarWidget class. Class used to display multiple projections (left, right, ant, post, top, bottom)
    in iconBarWidget.

    Inheritance
    -----------

    QWidget -> IconBarWidget -> IconBarMultiProjectionViewWidget

    Creation: 13/10/2024
    Last revision: 06/12/2024
    """

    # Special method

    """
    Class attributes

    _slider: QSlider            GUI slider to set opacity of the vtkImageSlice foreground
    _depth: LabeledSpinBox      GUI spinbox to set projection depth in mm
    """

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = MultiProjectionViewWidget()
        if isinstance(widget, MultiProjectionViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not MultiProjectionViewWidget.'.format(type(widget)))
        self._hideViewWidget()

        self._icons['iso'].setVisible(False)
        self._icons['ruler'].setVisible(False)
        self._icons['show'].setMenu(widget[(0, 0)].getPopupVisibility())
        self._icons['show'].setToolTip('Set visibility options.\n'
                                       'i key show/hide information\n'
                                       'l key show/hide orientation labels\n'
                                       'b key show/hide colorbar\n'
                                       't key show/hide tooltip')
        # noinspection PyUnresolvedReferences
        self._shcuti.activated.connect(lambda: self._icons['show'].menu().actions()[1].trigger())
        # noinspection PyUnresolvedReferences
        self._shcutl.activated.connect(lambda: self._icons['show'].menu().actions()[2].trigger())
        # noinspection PyUnresolvedReferences
        self._shcutb.activated.connect(lambda: self._icons['show'].menu().actions()[5].trigger())
        # noinspection PyUnresolvedReferences
        self._shcutt.activated.connect(lambda: self._icons['show'].menu().actions()[7].trigger())

        # Capture button

        submenu = QMenu()
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        submenu.addAction('Save grid capture...')
        submenu.addAction('Save selected view capture...')
        submenu.addSeparator()
        action = submenu.addAction('Send selected view capture to screenshots preview')
        action.setShortcut(Qt.Key_Space)
        # noinspection PyUnresolvedReferences
        submenu.triggered.connect(self._onMenuSaveCapture)
        self._icons['capture'].setMenu(submenu)

        # Opacity button

        self._icons['opacity'] = self._createButton('wopacity.png', 'opacity.png', checkable=True, autorepeat=False)
        self._icons['opacity'].setToolTip('Opacity')
        self._slider = QSlider(Qt.Vertical)
        self._slider.setFixedHeight(80)
        self._slider.setTickPosition(QSlider.NoTicks)
        self._slider.setMaximum(100)
        self._slider.setMinimum(0)
        self._slider.setValue(100)
        self._slider.setInvertedAppearance(True)
        self._slider.setToolTip('Opacity {} %'.format(self._slider.value()))
        # noinspection PyUnresolvedReferences
        self._slider.valueChanged.connect(self._opacityChanged)
        submenu = QMenu()
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._slider)
        submenu.addAction(a)
        self._icons['opacity'].setMenu(submenu)
        lyout = self._bar.layout()
        lyout.insertWidget(4, self._icons['opacity'])

        # Depth button

        self._icons['depth'] = self._createButton('wdepth.png', 'depth.png', checkable=True, autorepeat=False)
        self._icons['depth'].setToolTip('Projection depth from the head surface (mm)')
        self._depth = LabeledSpinBox(title='Projection depth')
        self._depth.setRange(5, 20)
        self._depth.setValue(int(widget.getDepthOfProjection()))
        # noinspection PyUnresolvedReferences
        self._depth.editingFinished.connect(self._depthChanged)
        submenu = QMenu()
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._depth)
        submenu.addAction(a)
        self._icons['depth'].setMenu(submenu)
        lyout = self._bar.layout()
        lyout.insertWidget(4, self._icons['depth'])

        # Operator button

        self._icons['operator'] = self._createButton('wintegral.png', 'integral.png', checkable=True, autorepeat=False)
        self._icons['operator'].setToolTip('Operator applied to voxels on a projection line')
        submenu = QMenu()
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        amax = submenu.addAction('Maximum')
        amean = submenu.addAction('Mean')
        amed = submenu.addAction('Median')
        astd = submenu.addAction('Standard deviation')
        amax.setCheckable(True)
        amean.setCheckable(True)
        amed.setCheckable(True)
        astd.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(amax)
        group.addAction(amean)
        group.addAction(amed)
        group.addAction(astd)
        op = widget.getOperatorOfProjection()
        if op == 'max': amax.setChecked(True)
        elif op == 'mean': amean.setChecked(True)
        elif op == 'median': amed.setChecked(True)
        else: astd.setChecked(True)
        self._icons['operator'].setMenu(submenu)
        self._icons['operator'].menu().triggered.connect(self._operatorChanged)
        lyout = self._bar.layout()
        lyout.insertWidget(4, self._icons['operator'])

        # < Revision 06/12/2024
        self._visibilityflags['ruler'] = False
        self._visibilityflags['iso'] = False
        self._visibilityflags['opacity'] = True
        self._visibilityflags['depth'] = True
        self._visibilityflags['operator'] = True
        # Revision 06/12/2024 >

    # Private method

    def _opacityChanged(self):
        self._widget.setProjectionOpacity(self._slider.value() / 100.0)
        self._slider.setToolTip('Opacity {} %'.format(self._slider.value()))

    def _depthChanged(self):
        if self._widget is not None:
            if self._depth.value() != int(self._widget.getDepthOfProjection()):
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Update projections...')
                self._widget.setDepthOfProjection(self._depth.value())
                wait.close()

    def _operatorChanged(self, action: QAction):
        if self._widget is not None:
            op = 'mean'
            if action.text() == 'Maximum': op = 'max'
            elif action.text() == 'Mean': op = 'mean'
            elif action.text() == 'Median': op = 'median'
            elif action.text() == 'Standard deviation': op = 'std'
            if op != self._widget.getOperatorOfProjection():
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Update projections...')
                self._widget.setOperatorOfProjection(op)
                wait.close()

    # Public methods

    # < Revision 21/11/2024
    # add mask parameter
    def setVolume(self,
                  foreground: SisypheVolume,
                  background: SisypheVolume | None = None,
                  mask: SisypheVolume | None = None) -> None:
        if self._widget is not None:
            self._hideViewWidget()
            self._widget.setVolume(foreground, background, mask)
            self._showViewWidget()
            if foreground is not None:
                self._slider.setValue(50)
                self._opacityChanged()
            # < Revision 08/11/2024
            # To solve VTK mouse move event bug
            self.timerEnabled()
            # Revision 08/11/2024 >
    # Revision 21/11/2024 >

    def removeVolume(self) -> None:
        if self._widget is not None:
            super().removeVolume()
            # < Revision 08/11/2024
            # To solve VTK mouse move event bug
            self.timerDisabled()
            # Revision 08/11/2024 >

    # Dummy methods, not inherited from IconBarWidget

    # < Revision 15/10/2024
    # override addOverlay (inherited from IconBarWidget class) as dummy method, no overlay in projection
    def addOverlay(self, volume: SisypheVolume) -> None:
        pass
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override getOverlayCount (inherited from IconBarWidget class) as dummy method, no overlay in projection, always 0
    def getOverlayCount(self) -> int:
        return 0
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override hasOverlay (inherited from IconBarWidget class) as dummy method, no overlay in projection, always False
    # mandatory method for compatibility with IconBarViewWidgetCollection
    def hasOverlay(self) -> bool:
        return False
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override getOverlayIndex (inherited from IconBarWidget class) as dummy method, no overlay in projection
    # mandatory method for compatibility with IconBarViewWidgetCollection
    def getOverlayIndex(self, o) -> int | None:
        raise NotImplementedError
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override removeOverlay (inherited from IconBarWidget class) as dummy method, no overlay in projection
    # mandatory method for compatibility with IconBarViewWidgetCollection
    def removeOverlay(self, o) -> None:
        pass
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override removeAllOverlays (inherited from IconBarWidget class) as dummy method, no overlay in projection
    # mandatory method for compatibility with IconBarViewWidgetCollection
    def removeAllOverlays(self) -> None:
        pass
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # override getOverlayFromIndex (inherited from IconBarWidget class) as dummy method, no overlay in projection
    # mandatory method for compatibility with IconBarViewWidgetCollection
    def getOverlayFromIndex(self, index: int) -> None:
        raise NotImplementedError
    # Revision 15/10/2024 >
