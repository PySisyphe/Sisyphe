"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
    - skimage, Image processing, https://scikit-image.org/
    - vtk, Visualization, https://vtk.org/
"""

from os import getcwd
from os import chdir
from os import remove

from os.path import join
from os.path import exists
from os.path import dirname

from platform import system

from tempfile import gettempdir

from numpy import flip
from numpy import stack

from skimage.util import montage
from skimage.io import imsave

from SimpleITK import GradientMagnitudeRecursiveGaussian

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QApplication

from vtk import vtkWindowToImageFilter
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheMesh import SisypheMeshCollection
from Sisyphe.core.sisypheTracts import SisypheTractCollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceRegistrationViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceReorientViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceROIViewWidget
from Sisyphe.widgets.volumeViewWidget import VolumeViewWidget
from Sisyphe.widgets.sliceTrajectoryViewWidget import SliceTrajectoryViewWidget

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalRegistrationViewWidget
                                                              -> OrthogonalReorientViewWidget
                                 -> OrthogonalSliceVolumeViewWidget -> OrthogonalSliceTrajectoryViewWidget
                                 -> GridViewWidget -> MultiSliceGridViewWidget
                                                   -> SynchronizedGridViewWidget
Description
~~~~~~~~~~~

Classes to display multiple synchronised slices, container of SliceViewWidget derived classes.
"""

# noinspection SpellCheckingInspection
class MultiViewWidget(QWidget):
    """
    MultiViewWidget class

    Description
    ~~~~~~~~~~~

    Base class to display and interact with multiple slices.

    It serves as a container for multiple instances of SliceViewWidget derived classes, allowing for the display of
    synchronised slices. This class provides methods for managing and interacting with the displayed slices. It also
    includes methods for controlling the layout and appearance of the displayed slices

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget

    Creation: 03/04/2022
    Last revision: 18/03/2025
    """

    # Special methods

    """
    Private attributes

    _rows       int, number of visible rows in the grid layout
    _cols       int, number of visible columns in the grid layout
    _n          int, view index for colorbar, orientation, cursor visibility
    _views      dict[tuple[int, int], abstractViewWidget]
    """

    def __init__(self, r=1, c=1, parent=None):
        super().__init__(parent)

        if r > 4: r = 4
        elif r < 1: r = 1
        if c > 4: c = 4
        elif c < 1: c = 1
        self._rows = r
        self._cols = c
        self._n = None
        self._views = dict()

        # Init QLayout

        self._layout = QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

    def __getitem__(self, key):
        # < Revision 18/03/2025
        # return self._views.get(key, None)
        return self._views[key]
        # Revision 18/03/2025 >

    def __setitem__(self, key, value):
        self.setViewWidget(key[0], key[1], value)

    def __delitem__(self, key):
        self.removeViewWidgetFromCoordinate(key[0], key[1])

    def __len__(self):
        return len(self._views)

    # Private method

    def _updateVisibility(self):
        if self.isNotEmpty():
            r = self._rows - 1
            c = self._cols - 1
            for k in self._views:
                if k[0] > r or k[1] > c: self._views[k].hide()
                else: self._views[k].show()

    # Private synchronisation event method

    def _synchroniseSelection(self, obj):
        if not self.isEmpty():
            for w in self._views.values():
                if w != obj: w.unselect()

    # Public methods

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be explicitely called before destruction
    def finalize(self):
        for w in self._views.values():
            w.finalize()
    # Revision 08/03/2025 >

    def setViewWidget(self, r, c, widget):
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views: self.removeViewWidgetFromCoordinate(r, c)
            action = widget.getAction()
            action['box'].setVisible(False)
            action['text'].setVisible(False)
            action['capture'].setText('Save current view capture...')
            action['clipboard'].setText('Copy current view capture to clipboard')
            action['capturegrid'] = QAction('Save grid capture...', widget)
            action['clipboardgrid'] = QAction('Copy grid capture to clipboard', widget)
            action['capturegrid'].triggered.connect(self.saveCapture)
            action['clipboardgrid'].triggered.connect(self.copyToClipboard)
            widget.getPopup().removeAction(action['capture'])
            widget.getPopup().removeAction(action['clipboard'])
            widget.getPopup().removeAction(action['captureseries'])
            submenu = widget.getPopup().addMenu('Save view capture')
            submenu.addAction(action['capturegrid'])
            submenu.addAction(action['capture'])
            submenu.addAction(action['captureseries'])
            if 'captureseries2' in action:
                widget.getPopup().removeAction(action['captureseries2'])
                submenu.addAction(action['captureseries2'])
            submenu = widget.getPopup().addMenu('Copy view capture to clipboard')
            submenu.addAction(action['clipboardgrid'])
            submenu.addAction(action['clipboard'])
            # addBundle fullscreen display action
            if system() == 'Windows':
                # action['screen'] = QAction('Fullscreen display', self)
                action['screen'] = QAction('Fullscreen display', widget)
                action['screen'].setCheckable(True)
                action['screen'].triggered.connect(self.toggleDisplay)
                widget.getPopup().insertAction(action['synchronisation'], action['screen'])
            # addBundle expand display action
            # action['expand'] = QAction('Expand display', self)
            action['expand'] = QAction('Expand display', widget)
            action['expand'].setCheckable(True)
            action['expand'].triggered.connect(lambda: self.expandViewWidget(widget))
            widget.getPopup().insertAction(action['synchronisation'], action['expand'])
            action['synchronisation'].setVisible(False)
            # synchronise selection
            widget.Selected.connect(self._synchroniseSelection)
            # addBundle view to layout
            widget.setParent(self)
            widget.setObjectName('{} {} {}'.format(str(type(widget)), str(r), str(c)))
            self._views[(r, c)] = widget
            self._layout.addWidget(widget, r, c)
        else: raise IndexError('row and/or column parameter is out of range.')

    def getViewWidgetAt(self, r, c):
        return self._views.get((r, c), None)

    def getFirstViewWidget(self):
        return self._views.get((0, 0), None)

    def getFirstSliceViewWidget(self):
        for w in self._views.values():
            if isinstance(w, SliceViewWidget):
                return w
        return None

    def getFirstVolumeViewWidget(self):
        for w in self._views.values():
            if isinstance(w, VolumeViewWidget):
                return w
        return None

    def getSliceViewWidgets(self):
        ws = list()
        for w in self._views.values():
            if isinstance(w, SliceViewWidget):
                ws.append(w)
        return ws

    def getVolumeViewWidgets(self):
        ws = list()
        for w in self._views.values():
            if isinstance(w, VolumeViewWidget):
                ws.append(w)
        return ws

    def getViewWidgetCoordinate(self, widget):
        if isinstance(widget, AbstractViewWidget):
            v = list(self._views.values())
            if widget in v:
                i = v.index(widget)
                return list(self._views.keys())[i]
            else: return None, None
        else: raise TypeError('tool parameter type {} is not AbstractViewWidget.'.format(type(widget)))

    def getSelectedViewWidget(self):
        if not self.isEmpty():
            for w in self._views.values():
                if w.isSelected(): return w
        return None

    def getViewWidgetCount(self):
        return len(self._views)

    def isEmpty(self):
        return len(self._views) == 0

    def isNotEmpty(self):
        return len(self._views) > 0

    def removeViewWidgetFromCoordinate(self, r, c):
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views:
                self._layout.removeWidget(self._views[(r, c)])
                return self._views.pop((r, c))
            else: raise IndexError('invalid row or column.')
        else: raise IndexError('row or column parameter is out of range.')

    def removeViewWidget(self, widget):
        r, c = self.getViewWidgetCoordinate(widget)
        if r is not None:
            self.removeViewWidgetFromCoordinate(r, c)

    def moveViewWidget(self, r1, c1, r2, c2):
        if 0 <= r1 < 4 and 0 <= c1 < 4 and 0 <= r2 < 4 and 0 <= c2 < 4:
            if (r1, c1) in self._views and (r2, c2) in self._views:
                self.swapViewWidgets(r1, c1, r2, c2)
            elif (r1, c1) in self._views and (r2, c2) not in self._views:
                # remove view from (r1, c1)
                widget = self.removeWidgetFromCoordinate(self._views[(r1, c1)])
                # addBundle view to (r2, c2)
                self._views[(r2, c2)] = widget
                self._layout.addWidget(widget, r2, c2)
                self._updateVisibility()
        else: raise IndexError('row or column parameter is out of range.')

    def swapViewWidgets(self, r1, c1, r2, c2):
        if 0 <= r1 < 4 and 0 <= c1 < 4 and 0 <= r2 < 4 and 0 <= c2 < 4:
            if (r1, c1) in self._views and (r2, c2) in self._views:
                v1 = self._views[(r1, c1)]
                v2 = self._views[(r2, c2)]
                self._views[(r1, c1)] = v2
                self._views[(r2, c2)] = v1
                self._layout.removeWidget(v1)
                self._layout.removeWidget(v2)
                self._layout.addWidget(v1, r2, c2)
                self._layout.addWidget(v2, r1, c1)
            elif (r1, c1) in self._views and (r2, c2) not in self._views:
                self.moveViewWidget(r1, c1, r2, c2)
            elif (r2, c2) in self._views and (r1, c1) not in self._views:
                self.moveViewWidget(r2, c2, r1, c1)
        else: raise IndexError('row or column parameter is out of range.')

    def setRows(self, r):
        if 0 <= r < 4:
            self._rows = r
            self._updateVisibility()
        else: raise ValueError('row parameter value {} is out of range.'.format(r))

    def setCols(self, c):
        if 0 <= c < 4:
            self._cols = c
            self._updateVisibility()
        else: raise ValueError('column parameter value {} is out of range.'.format(c))

    def setRowsAndCols(self, r, c):
        if 0 <= r < 4 and 0 <= c < 4:
            self._rows = r
            self._cols = c
            self._updateVisibility()
        else: raise ValueError('row and/or column parameter is out of range.')

    def getRows(self):
        return self._rows

    def getCols(self):
        return self._cols

    def getRowsAndCols(self):
        return self._rows, self._cols

    def setVisibilityControlToView(self, r, c):
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views: self._n = (r, c)
            else: raise ValueError('No abstractViewWidget at ({},{}) coordinate.'.format(r, c))
        else: raise IndexError('row and/or column is out of range.')

    def setVisibilityControlToAll(self):
        self._n = None

    def getVisibilityControl(self):
        return self._n

    def getNumberOfVisibleViews(self):
        n = 0
        for view in self._views:
            if view.isVisible(): n += 1
        return n

    def expandViewWidget(self, widget):
        if isinstance(widget, AbstractViewWidget):
            expand = widget.getAction()['expand'].isChecked()
            for i in range(self._rows):
                for j in range(self._cols):
                    # noinspection PyNoneFunctionAssignment
                    w = self.getViewWidgetAt(i, j)
                    if expand:
                        # noinspection PyUnresolvedReferences
                        w.setVisible(widget == w)
                    else:
                        # noinspection PyUnresolvedReferences
                        w.setVisible(True)
        else: raise TypeError('parameter type {} is not AbstractViewWidget.'.format(type(widget)))

    def isExpanded(self) -> bool:
        for i in range(self._rows):
            for j in range(self._cols):
                # noinspection PyUnresolvedReferences
                if self.getViewWidgetAt(i, j).getAction()['expand'].isChecked(): return True
        return False

    def getExpandedViewWidget(self) -> AbstractViewWidget | None:
        for i in range(self._rows):
            for j in range(self._cols):
                # noinspection PyNoneFunctionAssignment
                w = self.getViewWidgetAt(i, j)
                # noinspection PyUnresolvedReferences
                if w.getAction()['expand'].isChecked(): return w
        return None

    def setFullScreenDisplay(self) -> None:
        if not self.isEmpty():
            self.showFullScreen()
            for w in self._views.values():
                w.getAction()['screen'].setChecked(True)

    def setNormalDisplay(self) -> None:
        if not self.isEmpty():
            self.showNormal()
            for w in self._views.values():
                w.getAction()['screen'].setChecked(False)

    def toggleDisplay(self) -> None:
        # noinspection PyNoneFunctionAssignment
        w = self.getFirstViewWidget()
        # noinspection PyUnresolvedReferences
        if w.getAction()['screen'].isChecked(): self.setFullScreenDisplay()
        else: self.setNormalDisplay()

    def isFullScreenDisplay(self) -> bool:
        if not self.isEmpty():
            return self._views[0, 0].getAction()['screen'].isChecked()
        else: raise AttributeError('View is empty.')

    def popupMenuEnabled(self):
        for w in self._views.values():
            w.popupMenuEnabled()

    def popupMenuDisabled(self):
        for w in self._views.values():
            w.popupMenuDisabled()

    def popupMenuActionsEnabled(self):
        for w in self._views.values():
            w.popupActionsEnabled()

    def popupMenuActionsDisabled(self):
        for w in self._views.values():
            w.popupActionsDisabled()

    def popupMenuVisibilityEnabled(self):
        for w in self._views.values():
            w.popupVisibilityEnabled()

    def popupMenuVisibilityDisabled(self):
        for w in self._views.values():
            w.popupVisibilityDisabled()

    def popupMenuColorbarPositionEnabled(self):
        for w in self._views.values():
            w.popupColorbarPositionEnabled()

    def popupMenuColorbarPositionDisabled(self):
        for w in self._views.values():
            w.popupColorbarPositionDisabled()

    def popupMenuToolsEnabled(self):
        for w in self._views.values():
            w.popupToolsEnabled()

    def popupMenuToolsDisabled(self):
        for w in self._views.values():
            w.popupToolsDisabled()

    def setActionVisibility(self, name, v):
        if isinstance(name, str):
            if isinstance(v, bool):
                for i in range(0, self._rows):
                    for j in range(0, self._cols):
                        action = self._views[i, j].getAction()
                        if action is not None:
                            if name in action:
                                action[name].setVisible(v)
            else: raise TypeError('second parameter type {} is not bool.'.format(type(v)))
        else: raise TypeError('first parameter type {} is not str.'.format(type(name)))

    def showAction(self, name):
        self.setActionVisibility(name, True)

    def hideAction(self, name):
        self.setActionVisibility(name, False)

    def setRoundedCursorCoordinatesEnabled(self):
        for i in range(0, self._rows):
            for j in range(0, self._cols):
                self._views[i, j].setRoundedCursorCoordinatesEnabled()

    def setRoundedCursorCoordinatesDisabled(self):
        for i in range(0, self._rows):
            for j in range(0, self._cols):
                self._views[i, j].setRoundedCursorCoordinatesDisabled()

    def isRoundedCursorCoordinatesEnabled(self):
        return self._views[0, 0].isRoundedCursorCoordinatesEnabled()

    def setAlignCenters(self, v: bool):
        if len(self._views) > 0:
            for k in self._views:
                w = self._views[k]
                if isinstance(w, SliceOverlayViewWidget):
                    w.setAlignCenters(v)

    def alignCentersOn(self):
        self.setAlignCenters(True)

    def alignCentersOff(self):
        self.setAlignCenters(False)

    def getAlignCenters(self):
        if len(self._views) > 0:
            for i in range(0, self._rows):
                for j in range(0, self._cols):
                    # noinspection PyNoneFunctionAssignment
                    w = self.getViewWidgetAt(i, j)
                    if isinstance(w, SliceOverlayViewWidget):
                        return w.getAlignCenters()
        return None

    def updateRender(self):
        if len(self._views) > 0:
            for i in range(0, self._rows):
                for j in range(0, self._cols):
                    # noinspection PyNoneFunctionAssignment
                    w = self.getViewWidgetAt(i, j)
                    if isinstance(w, SliceROIViewWidget): w.updateROIDisplay()
                    else:
                        # noinspection PyUnresolvedReferences
                        w.updateRender()

    # Display setting methods

    def setLineColor(self, c: tuple[float, float, float]):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineColor(c, signal=False)

    def setLineSelectedColor(self, c: tuple[float, float, float]):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineSelectedColor(c, signal=False)

    def setLineWidth(self, v):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineWidth(v, signal=False)

    def setLineOpacity(self, v):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineOpacity(v, signal=False)

    def setFontFamily(self, s):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontFamily(s, signal=False)

    def setFontSize(self, s):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontSize(s, signal=False)

    def setFontScale(self, s):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontScale(s)

    def setFontSizeScale(self, s: tuple[int, float]):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontSizeScale(s)

    def setFontProperties(self, s: tuple[str, int, float]):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontProperties(s)

    # Capture methods

    def saveCapture(self):
        if self.isNotEmpty():
            # noinspection PyUnresolvedReferences
            if self.getFirstViewWidget().hasVolume():
                name = QFileDialog.getSaveFileName(self, caption='Save grid capture', directory=getcwd(),
                                                   filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                                   initialFilter='JPG (*.jpg)')
                name = name[0]
                if name != '':
                    chdir(dirname(name))
                    imglist = list()
                    c = vtkWindowToImageFilter()
                    for view in self._views:
                        if self._views[view].isVisible():
                            c.SetInput(self._views[view].getRenderWindow())
                            r = vtkImageExportToArray()
                            # noinspection PyArgumentList
                            r.SetInputConnection(c.GetOutputPort())
                            img = r.GetArray()
                            img = flip(img.reshape(img.shape[1:]), axis=0)
                            imglist.append(img)
                    n = len(imglist)
                    if n > 0:
                        # Shape correction
                        s = list(imglist[0].shape)
                        for i in range(1, n):
                            s2 = imglist[i].shape
                            if s2[0] < s[0]: s[0] = s2[0]
                            if s2[1] < s[1]: s[1] = s2[1]
                            if s2[2] < s[2]: s[2] = s2[2]
                        for i in range(n):
                            # noinspection PyUnresolvedReferences
                            imglist[i] = imglist[i][:s[0], :s[1], :s[2]]
                        # Layout
                        if n == 1: img = imglist[0]
                        else:
                            if n == 2: shape = (1, 2)
                            elif n == 3: shape = (1, 3)
                            elif n == 4: shape = (2, 2)
                            elif n == 6: shape = (2, 3)
                            elif n == 8: shape = (2, 4)
                            elif n == 9: shape = (3, 3)
                            elif n == 12: shape = (3, 4)
                            elif n == 16: shape = (4, 4)
                            else: raise ValueError('Invalid shape count.')
                            img = montage(stack(imglist), grid_shape=shape, channel_axis=3)
                        try: imsave(name, img)
                        except Exception as err:
                            messageBox(self,
                                       'Save grid capture error: ',
                                       text='{}\n{}.'.format(type(err), str(err)))

    def copyToClipboard(self):
        if self.isNotEmpty():
            # noinspection PyUnresolvedReferences
            if self.getFirstViewWidget().hasVolume():
                imglist = list()
                c = vtkWindowToImageFilter()
                for view in self._views:
                    if self._views[view].isVisible():
                        c.SetInput(self._views[view].getRenderWindow())
                        r = vtkImageExportToArray()
                        # noinspection PyArgumentList
                        r.SetInputConnection(c.GetOutputPort())
                        img = r.GetArray()
                        img = flip(img.reshape(img.shape[1:]), axis=0)
                        imglist.append(img)
                n = len(imglist)
                if n > 0:
                    # Shape correction
                    s = list(imglist[0].shape)
                    for i in range(1, n):
                        s2 = imglist[i].shape
                        if s2[0] < s[0]: s[0] = s2[0]
                        if s2[1] < s[1]: s[1] = s2[1]
                        if s2[2] < s[2]: s[2] = s2[2]
                    for i in range(n):
                        # noinspection PyUnresolvedReferences
                        imglist[i] = imglist[i][:s[0], :s[1], :s[2]]
                    # Layout
                    if n == 1: img = imglist[0]
                    else:
                        if n == 2: shape = (1, 2)
                        elif n == 3: shape = (1, 3)
                        elif n == 4: shape = (2, 2)
                        elif n == 6: shape = (2, 3)
                        elif n == 8: shape = (2, 4)
                        elif n == 9: shape = (3, 3)
                        elif n == 12: shape = (3, 4)
                        elif n == 16: shape = (4, 4)
                        else: raise ValueError('Invalid shape count.')
                        img = montage(stack(imglist), grid_shape=shape, channel_axis=3)
                    temp = join(gettempdir(), 'tmp.bmp')
                    try:
                        imsave(temp, img)
                        p = QPixmap(temp)
                        QApplication.clipboard().setPixmap(p)
                    except Exception as err:
                        messageBox(self,
                                   'Copy grid capture to clipboard error: ',
                                   text='{}\n{}.'.format(type(err), str(err)))
                    finally:
                        if exists(temp): remove(temp)


class OrthogonalSliceViewWidget(MultiViewWidget):
    """
    OrthogonalSliceViewWidget class

    Description
    ~~~~~~~~~~~

    Class designed to display synchronised axial, coronal, and sagittal slices from the same 3D volume.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget

    Creation: 03/04/2022
    Last revision: 18/10/2024
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(1, 3, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self):
        for i in range(3):
            widget = SliceOverlayViewWidget()
            self.setViewWidget(0, i, widget)
            widget.synchronisationOn()
            widget.getPopup().actions()[2].setVisible(False)  # Orientation menu off
            widget.getAction()['moveoverlayflag'].setVisible(False)
        self[0, 0].setName('Axial view')
        self[0, 1].setName('Coronal view')
        self[0, 2].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        for i in range(3):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(0, j)
                    # noinspection PyUnresolvedReferences
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    # noinspection PyUnresolvedReferences
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolMoved.connect(w2.synchroniseToolMoved)
                    # noinspection PyUnresolvedReferences
                    w1.ToolRemoved.connect(w2.synchroniseToolRemoved)
                    # noinspection PyUnresolvedReferences
                    w1.ToolColorChanged.connect(w2.synchroniseToolColorChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolAttributesChanged.connect(w2.synchroniseToolAttributesChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolRenamed.connect(w2.synchroniseToolRenamed)
                    # noinspection PyUnresolvedReferences
                    w1.ToolAdded.connect(w2.synchroniseToolAdded)
                    # noinspection PyUnresolvedReferences
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)
                    if isinstance(w1, SliceViewWidget) and isinstance(w2, SliceViewWidget):
                        w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                        w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                        w1.TransformApplied.connect(w2.synchroniseTransformApplied)
                        w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                        w1.VisibilityChanged.connect(w2.synchronisedVisibilityChanged)
                    if isinstance(w1, SliceOverlayViewWidget) and isinstance(w2, SliceOverlayViewWidget):
                        w1.ViewOverlayMethodCalled.connect(w2.synchroniseViewOverlayMethodCalled)
                        w1.TranslationsChanged.connect(w2.synchroniseTranslationsChanged)
                        w1.RotationsChanged.connect(w2.synchroniseRotationsChanged)
                        w1.IsoIndexChanged.connect(w2.synchroniseIsoIndexChanged)
                        w1.IsoValuesChanged.connect(w2.synchroniseIsoValuesChanged)
                        w1.IsoLinesColorChanged.connect(w2.synchroniseIsoLinesColorChanged)
                        w1.IsoLinesOpacityChanged.connect(w2.synchroniseIsoLinesOpacityChanged)

    # Public methods

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self[0, 0].setVolume(volume)
            self[0, 0].setDim0Orientation()
            self[0, 1].setVolume(volume)
            self[0, 1].setDim1Orientation()
            self[0, 2].setVolume(volume)
            self[0, 2].setDim2Orientation()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, volume):
        if self.hasVolume():
            self[0, 0].replaceVolume(volume)
            self[0, 1].replaceVolume(volume)
            self[0, 2].replaceVolume(volume)
    # Revision 18/10/2024

    def removeVolume(self):
        """
        self.removeAllOverlays() not called
        already deleted by self.removeVolume()
        """
        self[0, 0].removeVolume()
        self[0, 1].removeVolume()
        self[0, 2].removeVolume()

    def getVolume(self):
        return self[0, 0].getVolume()

    def hasVolume(self):
        return self[0, 0].hasVolume()

    def addOverlay(self, volume, alpha=0.5):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                self[0, 0].addOverlay(volume, alpha)
                self[0, 1].addOverlay(volume, alpha)
                self[0, 2].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self):
        return self[0, 0].getOverlayCount()

    def hasOverlay(self):
        return self[0, 0].hasOverlay()

    def getOverlayIndex(self, o):
        return self[0, 0].hasOverlayVolume(o)

    def removeOverlay(self, o):
        self[0, 0].removeOverlay(o)
        self[0, 1].removeOverlay(o)
        self[0, 2].removeOverlay(o)

    def removeAllOverlays(self):
        self[0, 0].removeAllOverlays()
        self[0, 1].removeAllOverlays()
        self[0, 2].removeAllOverlays()

    def getOverlayFromIndex(self, index):
        return self[0, 0].getOverlayFromIndex(index)

    def setMeshCollection(self, meshes):
        if isinstance(meshes, SisypheMeshCollection):
            self[0, 0].setMeshCollection(meshes)
            self[0, 1].setMeshCollection(meshes)
            self[0, 2].setMeshCollection(meshes)
        else: raise TypeError('parameter type {} is not SisypheMeshCollection.'.format(type(meshes)))

    def getMeshCollection(self):
        self[0, 0].getMeshCollection()

    # View methods

    def getAxialView(self):
        return self[0, 0]

    def getCoronalView(self):
        return self[0, 1]

    def getSagittalView(self):
        return self[0, 2]


class OrthogonalRegistrationViewWidget(OrthogonalSliceViewWidget):
    """
    OrthogonalSliceViewWidget class

    Description
    ~~~~~~~~~~~

    Subclass of the OrthogonalSliceViewWidget class.

    It is designed to provide functionalities for evaluating registration quality between two volumes. The class allows
    users to apply rigid transformations to the volume being viewed. It also includes a synchronised box widget that
    can be used to crop the overlays in the three orientations.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalRegistrationViewWidget

    Creation: 03/04/2022
    Last revision:
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    # Private method

    def _initViews(self):
        for i in range(3):
            widget = SliceRegistrationViewWidget()
            self.setViewWidget(0, i, widget)
            widget.synchronisationOn()
            # < Revision 05/09/2024
            widget.alignCentersOff()
            # Revision 05/09/2024 >
            widget.getPopup().actions()[3].setVisible(False)  # Orientation menu off
            widget.getAction()['moveoverlayflag'].setVisible(True)
        self[0, 0].setName('Axial view')
        self[0, 1].setName('Coronal view')
        self[0, 2].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        super()._initSynchronisationSignalConnect()
        for i in range(3):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(0, j)
                    if isinstance(w1, SliceRegistrationViewWidget) and isinstance(w2, SliceRegistrationViewWidget):
                        w1.CropChanged.connect(w2.synchroniseCropChanged)

    # Public method

    def addOverlay(self, volume, alpha=0.5):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                img = GradientMagnitudeRecursiveGaussian(self.getVolume().getSITKImage())
                gradient = SisypheVolume(img)
                gradient.getDisplay().getLUT().setLutToHot()
                rmin, rmax = gradient.getDisplay().getRange()
                w = (rmax - rmin) / 10
                wmin = rmin + w
                wmax = rmax - (2 * w)
                gradient.getDisplay().setWindow(wmin, wmax)
                gradient.getDisplay().getLUT().setDisplayBelowRangeColorOn()
                self[0, 0].addOverlay(volume, gradient, alpha)
                self[0, 1].addOverlay(volume, gradient, alpha)
                self[0, 2].addOverlay(volume, gradient, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))


class OrthogonalReorientViewWidget(OrthogonalSliceViewWidget):
    """
    OrthogonalReorientViewWidget class

    Description
    ~~~~~~~~~~~

    Subclass of the OrthogonalSliceViewWidget class.

    The class allows users to apply rigid transformations to the volume being viewed. It also includes a synchronised
    box widget to show and manipulate field of view in the three orientations.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalReorientViewWidget

    Creation: 03/04/2022
    Last revision:
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

    # Private methods

    def _initViews(self):
        for i in range(3):
            widget = SliceReorientViewWidget()
            self.setViewWidget(0, i, widget)
            widget.synchronisationOn()
            widget.getPopup().actions()[2].setVisible(False)  # Orientation menu off
            widget.getPopup().actions()[7].setVisible(False)  # Tools menu off
        self[0, 0].setName('Axial view')
        self[0, 1].setName('Coronal view')
        self[0, 2].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        for i in range(3):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(0, j)
                    # noinspection PyUnresolvedReferences
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    # noinspection PyUnresolvedReferences
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ResliceCursorChanged.connect(w2.synchroniseResliceCursorChanged)
                    # noinspection PyUnresolvedReferences
                    w1.SpacingChanged.connect(w2.synchroniseSpacingChanged)
                    # noinspection PyUnresolvedReferences
                    w1.SizeChanged.connect(w2.synchroniseSizeChanged)
                    # noinspection PyUnresolvedReferences
                    w1.TranslationsChanged.connect(w2.synchroniseTranslationsChanged)
                    # noinspection PyUnresolvedReferences
                    w1.RotationsChanged.connect(w2.synchroniseRotationsChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)
                    if isinstance(w1, SliceViewWidget) and isinstance(w2, SliceViewWidget):
                        w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                        w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                        w1.TransformApplied.connect(w2.synchroniseTransformApplied)
                        w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                        w1.VisibilityChanged.connect(w2.synchronisedVisibilityChanged)

    # Public methods

    def translationsEnabled(self):
        for i in range(3):
            self[0, i].translationsEnabled()

    def translationsDisabled(self):
        for i in range(3):
            self[0, i].translationsDisabled()

    def rotationsEnabled(self):
        for i in range(3):
            self[0, i].rotationsEnabled()

    def rotationsDisabled(self):
        for i in range(3):
            self[0, i].rotationsDisabled()

    def rotationXEnabled(self):
        for i in range(3):
            self[0, i].rotationXEnabled()

    def rotationXDisabled(self):
        for i in range(3):
            self[0, i].rotationXDisabled()

    def rotationYEnabled(self):
        for i in range(3):
            self[0, i].rotationYEnabled()

    def rotationYDisabled(self):
        for i in range(3):
            self[0, i].rotationYDisabled()

    def rotationZEnabled(self):
        for i in range(3):
            self[0, i].rotationZEnabled()

    def rotationZDisabled(self):
        for i in range(3):
            self[0, i].rotationZDisabled()

    def setFOVBoxVisibility(self, v):
        if isinstance(v, bool):
            for i in range(3):
                self[0, i].setFOVBoxVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFOVBoxVisibility(self):
        return self[0, 0].getFOVBoxVisibility()

    def setResliceCursorColor(self, rgb):
        for i in range(3):
            self[0, i].setResliceCursorColor(rgb)

    def getResliceCursorColor(self):
        return self[0, 0].getResliceCursorColor()

    def setResliceCursorOpacity(self, v):
        if isinstance(v, float):
            for i in range(3):
                self[0, i].setResliceCursorOpacity(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorOpacity(self):
        return self[0, 0].getResliceCursorOpacity()

    def setResliceCursorLineWidth(self, v):
        if isinstance(v, float):
            for i in range(3):
                self[0, i].setResliceCursorLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorLineWidth(self):
        return self[0, 0].getResliceCursorLineWidth()

    def setFovBoxColor(self, rgb):
        for i in range(3):
            self[0, i].setFovBoxColor(rgb)

    def getFovBoxColor(self):
        return self[0, 0].getFovBoxColor()

    def setFovBoxOpacity(self, v):
        if isinstance(v, float):
            for i in range(3):
                self[0, i].setFovBoxOpacity(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxOpacity(self):
        return self[0, 0].getFovBoxOpacity()

    def setFovBoxLineWidth(self, v):
        if isinstance(v, float):
            for i in range(3):
                self[0, i].setFovBoxLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxLineWidth(self):
        return self[0, 0].getFovBoxLineWidth()

    def setSliceNavigationEnabled(self):
        for i in range(3):
            self[0, i].setSliceNavigationEnabled()

    def setSliceNavigationDisabled(self):
        for i in range(3):
            self[0, i].setSliceNavigationDisabled()

    def isSliceNavigationEnabled(self):
        return self[0, 0].isSliceNavigationEnabled


class OrthogonalSliceVolumeViewWidget(MultiViewWidget):
    """
    OrthogonalSliceVolumeViewWidget class

    Description
    ~~~~~~~~~~~

    Class designed to display a 2x2 grid of axial, coronal, and sagittal slices, along with a 3D volume rendering.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget

    Creation: 03/04/2022
    Last revision: 27/03/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(2, 2, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self):
        meshes = None
        for i in range(2):
            for j in range(2):
                if i == 0 and j == 0:
                    widget = VolumeViewWidget()
                    meshes = widget.getMeshCollection()
                else:
                    widget = SliceOverlayViewWidget()
                    widget.getPopup().actions()[3].setVisible(False)
                    widget.getAction()['moveoverlayflag'].setVisible(False)
                    widget.synchronisationOn()
                    if meshes is not None: widget.setMeshCollection(meshes)
                self.setViewWidget(i, j, widget)
        self[0, 0].setName('3D view')
        self[0, 1].setName('Axial view')
        self[1, 0].setName('Coronal view')
        self[1, 1].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        for i in range(4):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(i // 2, i % 2)
            for j in range(4):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(j // 2, j % 2)
                    # noinspection PyUnresolvedReferences
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    # noinspection PyUnresolvedReferences
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolMoved.connect(w2.synchroniseToolMoved)
                    # noinspection PyUnresolvedReferences
                    w1.ToolRemoved.connect(w2.synchroniseToolRemoved)
                    # noinspection PyUnresolvedReferences
                    w1.ToolColorChanged.connect(w2.ToolColorChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolAttributesChanged.connect(w2.synchroniseToolAttributesChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ToolRenamed.connect(w2.synchroniseToolRenamed)
                    # noinspection PyUnresolvedReferences
                    w1.ToolAdded.connect(w2.synchroniseToolAdded)
                    # noinspection PyUnresolvedReferences
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)
                    if isinstance(w1, SliceViewWidget) and isinstance(w2, SliceViewWidget):
                        w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                        w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                        w1.TransformApplied.connect(w2.synchroniseTransformApplied)
                        w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                        w1.VisibilityChanged.connect(w2.synchronisedVisibilityChanged)
                    if isinstance(w1, SliceOverlayViewWidget) and isinstance(w2, SliceOverlayViewWidget):
                        w1.ViewOverlayMethodCalled.connect(w2.synchroniseViewOverlayMethodCalled)
                        w1.TranslationsChanged.connect(w2.synchroniseTranslationsChanged)
                        w1.RotationsChanged.connect(w2.synchroniseRotationsChanged)
                        w1.IsoIndexChanged.connect(w2.synchroniseIsoIndexChanged)
                        w1.IsoValuesChanged.connect(w2.synchroniseIsoValuesChanged)
                        w1.IsoLinesColorChanged.connect(w2.synchroniseIsoLinesColorChanged)
                        w1.IsoLinesOpacityChanged.connect(w2.synchroniseIsoLinesOpacityChanged)
                        w1.MeshVisibilityChanged.connect(w2.synchroniseMeshVisibilityChanged)
                    if isinstance(w1, VolumeViewWidget) and isinstance(w2, SliceOverlayViewWidget):
                        w1.MeshOnSliceVisibilityChanged.connect(w2.synchroniseMeshVisibilityChanged)

    # Public methods

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self[0, 0].setVolume(volume)
            self[0, 0].setCameraToLeft()
            self[0, 1].setVolume(volume)
            self[0, 1].setDim0Orientation()
            self[1, 0].setVolume(volume)
            self[1, 0].setDim1Orientation()
            self[1, 1].setVolume(volume)
            self[1, 1].setDim2Orientation()
            self[0, 1].setTrajectoryToDefault(signal=True)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, volume):
        if self.hasVolume():
            self[0, 0].replaceVolume(volume)
            self[0, 1].replaceVolume(volume)
            self[1, 0].replaceVolume(volume)
            self[1, 1].replaceVolume(volume)
    # Revision 18/10/2024

    def removeVolume(self):
        """
            self.removeAllOverlays()
            already deleted by self.removeVolume()
        """
        self[0, 0].removeVolume()
        self[0, 1].removeVolume()
        self[1, 0].removeVolume()
        self[1, 1].removeVolume()

    def getVolume(self):
        return self[0, 0].getVolume()

    def hasVolume(self):
        return self[0, 0].hasVolume()

    # Overlay methods

    def addOverlay(self, volume, alpha=0.5):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                self[0, 1].addOverlay(volume, alpha)
                self[1, 0].addOverlay(volume, alpha)
                self[1, 1].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self):
        return self[0, 1].getOverlayCount()

    def hasOverlay(self):
        return self[0, 1].hasOverlay()

    def getOverlayIndex(self, o):
        return self[0, 1].hasOverlayVolume(o)

    def removeOverlay(self, o):
        self[0, 1].removeOverlay(o)
        self[1, 0].removeOverlay(o)
        self[1, 1].removeOverlay(o)

    def removeAllOverlays(self):
        self[0, 1].removeAllOverlays()
        self[1, 0].removeAllOverlays()
        self[1, 1].removeAllOverlays()

    def getOverlayFromIndex(self, index):
        return self[0, 1].getOverlayFromIndex(index)

    # Mesh methods

    # < Revision 23/03/2025
    def removeAllMeshes(self):
        if self.isNotEmpty():
            for w in self._views.values():
                w.removeAllMeshes()
    # Revision 23/03/2025 >

    # < Revision 23/03/2025
    def removeMesh(self, mesh):
        if self.isNotEmpty():
            for w in self._views.values():
                w.removeMesh(mesh)
    # Revision 23/03/2025 >

    # < Revision 27/03/2025
    def addMesh(self, mesh):
        for w in self._views.values():
            w.addMesh(mesh)
    # Revision 27/03/2025 >

    # Tracts methods

    def getTractCollection(self) -> SisypheTractCollection:
        return self[0, 0].getTractCollection()

    def setTractCollection(self, tracts: SisypheTractCollection) -> None:
        self[0, 0].setTractCollection(tracts)

    def hasTracts(self):
        return self[0, 0].hasTracts()

    # View methods

    def getVolumeView(self):
        return self[0, 0]

    def getAxialView(self):
        return self[0, 1]

    def getCoronalView(self):
        return self[1, 0]

    def getSagittalView(self):
        return self[1, 1]


class OrthogonalTrajectoryViewWidget(OrthogonalSliceVolumeViewWidget):
    """
    OrthogonalTrajectoryViewWidget class

    Description
    ~~~~~~~~~~~

    Subclass of the OrthogonalSliceVolumeViewWidget class.

    It extends the functionality of the OrthogonalSliceVolumeViewWidget by adding trajectory management.
    It includes methods for adding, removing, and manipulating trajectories, as well as for aligning the trajectories
    with specific anatomical orientations (e.g., axial, coronal, sagittal), with the camera view or with specific
    anatomical landmarks. It also provides methods for customizing the appearance and behavior of the trajectories,
    such as changing their color, opacity, and visibility.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget -> OrthogonalTrajectoryViewWidget

    Creation: 03/04/2022
    Last Revision: 02/10/2023
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

    # Private methods

    def _initViews(self):
        meshes = None
        for i in range(2):
            for j in range(2):
                if i == 0 and j == 0:
                    widget = VolumeViewWidget()
                    widget.setRoundedCursorCoordinatesDisabled()
                    widget.synchronisationOn()
                    meshes = widget.getMeshCollection()
                else:
                    widget = SliceTrajectoryViewWidget()
                    widget.getPopup().actions()[3].setVisible(False)
                    widget.getAction()['moveoverlayflag'].setVisible(False)
                    widget.synchronisationOn()
                    if meshes is not None: widget.setMeshCollection(meshes)
                self.setViewWidget(i, j, widget)
        self[0, 0].setName('3D view')
        self[0, 1].setName('Axial view')
        self[1, 0].setName('Coronal view')
        self[1, 1].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        super()._initSynchronisationSignalConnect()
        for i in range(4):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(i // 2, i % 2)
            if isinstance(w1, SliceTrajectoryViewWidget):
                w1.TrajectoryCameraAligned.connect(self.synchroniseTrajectoryCameraAligned)
            elif isinstance(w1, VolumeViewWidget):
                w1.CameraChanged.connect(self.synchroniseCameraChanged)
            for j in range(4):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(j // 2, j % 2)
                    if isinstance(w1, SliceTrajectoryViewWidget) and isinstance(w2, SliceTrajectoryViewWidget):
                        w1.TrajectoryToolAligned.connect(w2.synchroniseTrajectoryToolAligned)
                        w1.TrajectoryACPCAligned.connect(w2.synchroniseTrajectoryACPCAligned)
                        w1.TrajectoryVectorAligned.connect(w2.synchroniseTrajectoryVectorAligned)
                        w1.TrajectoryDefaultAligned.connect(w2.synchroniseTrajectoryDefaultAligned)
                        w1.SlabChanged.connect(w2.synchroniseSlabChanged)
                        w1.StepChanged.connect(w2.synchroniseStepChanged)

    # Public methods

    def popupAlignmentEnabled(self):
        for w in self._views.values():
            if isinstance(w, SliceTrajectoryViewWidget):
                w.popupAlignmentEnabled()

    def popupAlignmentDisabled(self):
        for w in self._views.values():
            if isinstance(w, SliceTrajectoryViewWidget):
                w.popupAlignmentDisabled()

    # Public synchronisation event methods

    def synchroniseCameraChanged(self, obj):
        view = self.getFirstSliceViewWidget()
        if view.isCameraAligned(): self.synchroniseTrajectoryCameraAligned(obj)

    # noinspection PyUnusedLocal
    def synchroniseTrajectoryCameraAligned(self, obj):
        camera = self.getFirstVolumeViewWidget().getRenderer().GetActiveCamera()
        views = self.getSliceViewWidgets()
        for view in views:
            view.setTrajectoryFromCamera(camera, signal=False)


class GridViewWidget(MultiViewWidget):
    """
    GridViewWidget class

    Description
    ~~~~~~~~~~~

    Base class designed to display a 3x3 grid of slices.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget

    Creation: 03/04/2022
    Last revision: 14/10/2024
    """

    # Special method

    """
    Private attributes

    _menuNumberOfVisibleViews   QMenu
    """

    def __init__(self, rois=None, draw=None, parent=None):
        super().__init__(3, 3, parent)

        self._menuNumberOfVisibleViews = None

        self._initViews(rois, draw)
        self._initActions()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self, rois, draw):
        for i in range(9):
            if i == 0:
                if rois is not None and draw is not None: w = SliceROIViewWidget(rois=rois, draw=draw)
                else:
                    w = SliceROIViewWidget()
                    rois = w.getROICollection()
                    draw = w.getDrawInstance()
            else: w = SliceROIViewWidget(rois=rois, draw=draw)
            self.setViewWidget(i // 3, i % 3, w)
        self.setVisibilityControlToAll()

    def _initActions(self):
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.setName('view#{}'.format(i))
            # noinspection PyUnresolvedReferences
            w.synchronisationOn()
            # noinspection PyUnresolvedReferences
            action = w.getAction()
            action['expand'].setVisible(False)
            action['target'].setVisible(False)
            action['trajectory'].setVisible(False)
            action['moveoverlayflag'].setVisible(False)
            action['axial'].triggered.disconnect()
            action['coronal'].triggered.disconnect()
            action['sagittal'].triggered.disconnect()
            action['axial'].triggered.connect(self.setAxialOrientation)
            action['coronal'].triggered.connect(self.setCoronalOrientation)
            action['sagittal'].triggered.connect(self.setSagittalOrientation)
            action['11'] = QAction('1 x 1', self)
            action['12'] = QAction('1 x 2', self)
            action['13'] = QAction('1 x 3', self)
            action['22'] = QAction('2 x 2', self)
            action['23'] = QAction('2 x 3', self)
            action['33'] = QAction('3 x 3', self)
            action['11'].setCheckable(True)
            action['12'].setCheckable(True)
            action['13'].setCheckable(True)
            action['22'].setCheckable(True)
            action['23'].setCheckable(True)
            action['33'].setCheckable(True)
            action['33'].setChecked(True)
            action['11'].triggered.connect(lambda: self.setNumberOfVisibleViews(1, 1))
            action['12'].triggered.connect(lambda: self.setNumberOfVisibleViews(1, 2))
            action['13'].triggered.connect(lambda: self.setNumberOfVisibleViews(1, 3))
            action['22'].triggered.connect(lambda: self.setNumberOfVisibleViews(2, 2))
            action['23'].triggered.connect(lambda: self.setNumberOfVisibleViews(2, 3))
            action['33'].triggered.connect(lambda: self.setNumberOfVisibleViews(3, 3))
            self._group_nbviews = QActionGroup(self)
            self._group_nbviews.setExclusive(True)
            self._group_nbviews.addAction(action['11'])
            self._group_nbviews.addAction(action['12'])
            self._group_nbviews.addAction(action['13'])
            self._group_nbviews.addAction(action['22'])
            self._group_nbviews.addAction(action['23'])
            self._group_nbviews.addAction(action['33'])
            # noinspection PyUnresolvedReferences
            popup = w.getPopup()
            menuNumberOfVisibleViews = QMenu('Number of views', popup)
            # noinspection PyTypeChecker
            menuNumberOfVisibleViews.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            menuNumberOfVisibleViews.setWindowFlag(Qt.FramelessWindowHint, True)
            menuNumberOfVisibleViews.setAttribute(Qt.WA_TranslucentBackground, True)
            menuNumberOfVisibleViews.addAction(action['11'])
            menuNumberOfVisibleViews.addAction(action['12'])
            menuNumberOfVisibleViews.addAction(action['13'])
            menuNumberOfVisibleViews.addAction(action['22'])
            menuNumberOfVisibleViews.addAction(action['23'])
            menuNumberOfVisibleViews.addAction(action['33'])
            popup.insertMenu(popup.actions()[2], menuNumberOfVisibleViews)
            if i == 0: self._menuNumberOfVisibleViews = menuNumberOfVisibleViews

    def _initSynchronisationSignalConnect(self):
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w1 = self.getViewWidgetAt(i // 3, i % 3)
            for j in range(9):
                if j != i:
                    # noinspection PyNoneFunctionAssignment
                    w2 = self.getViewWidgetAt(j // 3, j % 3)
                    # noinspection PyUnresolvedReferences
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    # noinspection PyUnresolvedReferences
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    # noinspection PyUnresolvedReferences
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)
                    if isinstance(w1, SliceViewWidget) and isinstance(w2, SliceViewWidget):
                        w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                        w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                        w1.TransformApplied.connect(w2.synchroniseTransformApplied)
                        w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                        w1.VisibilityChanged.connect(w2.synchronisedVisibilityChanged)
                    if isinstance(w1, SliceOverlayViewWidget) and isinstance(w2, SliceOverlayViewWidget):
                        w1.ViewOverlayMethodCalled.connect(w2.synchroniseViewOverlayMethodCalled)
                        w1.TranslationsChanged.connect(w2.synchroniseTranslationsChanged)
                        w1.RotationsChanged.connect(w2.synchroniseRotationsChanged)
                        w1.IsoIndexChanged.connect(w2.synchroniseIsoIndexChanged)
                        w1.IsoValuesChanged.connect(w2.synchroniseIsoValuesChanged)
                        w1.IsoLinesColorChanged.connect(w2.synchroniseIsoLinesColorChanged)
                        w1.IsoLinesOpacityChanged.connect(w2.synchroniseIsoLinesOpacityChanged)
                    if isinstance(w1, SliceROIViewWidget) and isinstance(w2, SliceROIViewWidget):
                        w1.ROIAttributesChanged.connect(w2.synchroniseROIAttributesChanged)
                        w1.ROISelectionChanged.connect(w2.synchroniseROISelectionChanged)
                        w1.ROIModified.connect(w2.synchroniseROIModified)
                        w1.BrushRadiusChanged.connect(w2.synchroniseBrushRadiusChanged)
                        w1.ROIFlagChanged.connect(w2.synchroniseROIFlagChanged)

    # Public methods

    def updateROIName(self, old, name):
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, SliceROIViewWidget):
                    if w.hasROI(): w.updateROIName(old, name)

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            for i in range(0, 9):
                self[i // 3, i % 3].setVolume(volume)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # < Revision 14/10/2024
    # add replaceVolume method
    def replaceVolume(self, volume):
        if self.hasVolume():
            for i in range(0, 9):
                self[i // 3, i % 3].replaceVolume(volume)
    # Revision 14/10/2024 >

    def removeVolume(self):
        """
            self.removeAllOverlays()
            already deleted by self.removeVolume()
        """
        for i in range(0, 9):
            self[i // 3, i % 3].removeVolume()

    def getVolume(self):
        return self[0, 0].getVolume()

    def hasVolume(self):
        return self[0, 0].hasVolume()

    def setNumberOfVisibleViews(self, r, c):
        k = '{}{}'.format(r, c)
        if r == c == 2:
            n = 0
            # Swap views if 2 x 2 grid, to avoid skipping slice (lost view row 0, column 2)
            # Swap views (0,2) and (1,0)
            self.swapViewWidgets(1, 0, 0, 2)
            self.swapViewWidgets(0, 2, 1, 1)
        else:
            n = r * c
            # Swap views if 2 x 2 grid, to restore slice order
            if self.getRows() == self.getCols() == 2:
                self.swapViewWidgets(1, 1, 1, 0)
                self.swapViewWidgets(1, 1, 0, 2)
        for i in range(9):
            a = i // 3
            b = i % 3
            self[a, b].getAction()[k].setChecked(True)
            if n > 0: self[a, b].setVisible(i < n)
            else: self[a, b].setVisible(i in [0, 1, 3, 4])
            self.setRows(r)
            self.setCols(c)

    def getViewsArrangement(self):
        action = self.getFirstSliceViewWidget().getAction()
        if action['11'].isChecked(): r = (1, 1)
        elif action['12'].isChecked(): r = (1, 2)
        elif action['13'].isChecked(): r = (1, 3)
        elif action['22'].isChecked(): r = (2, 2)
        elif action['23'].isChecked(): r = (2, 3)
        else: r = (3, 3)
        return r

    def setAxialOrientation(self):
        self.setOrientation(0)

    def setCoronalOrientation(self):
        self.setOrientation(1)

    def setSagittalOrientation(self):
        self.setOrientation(2)

    def setOrientation(self, orient):
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, AbstractViewWidget):
                    if w.hasVolume(): w.setOrientation(orient)

    def getOrientation(self):
        return self._views[(0, 0)].getOrientation()

    def getOrientationAsString(self):
        return self._views[(0, 0)].getOrientationAsString()

    def getPopupMenuNumberOfVisibleViews(self):
        return self._menuNumberOfVisibleViews

    def popupMenuOrientationEnabled(self):
        for w in self._views.values():
            w.popupOrientationEnabled()

    def popupMenuOrientationDisabled(self):
        for w in self._views.values():
            w.popupOrientationDisabled()

    def popupMenuNumberOfVisibleViewsShow(self):
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.getPopup().actions()[2].setVisible(True)

    def popupMenuNumberOfVisibleViewsHide(self):
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.getPopup().actions()[2].setVisible(False)

    def popupMenuROIEnabled(self):
        for w in self._views.values():
            w.popupROIEnabled()

    def popupMenuROIDisabled(self):
        for w in self._views.values():
            w.popupROIDisabled()


class MultiSliceGridViewWidget(GridViewWidget):
    """
    MultiSliceGridViewWidget class

    Description
    ~~~~~~~~~~~

    Subclass of the GridViewWidget class.

    It is designed to display multiple adjacent slices in a 3 x 3 grid layout. This class provides additional
    functionalities such as overlay support and ROI support.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget -> MultiSliceGridViewWidget

    Creation: 03/04/2022
    Last revision: 12/08/2023
    """

    # Special method

    def __init__(self, rois=None, draw=None, parent=None):

        super().__init__(rois, draw, parent)

        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.setOffset(i)  # nine consecutive slices of the same volume
            if i > 0:
                # noinspection PyUnresolvedReferences
                w.setCursorVisibilityOff()
            # noinspection PyUnresolvedReferences
            action = w.getAction()
            action['expand'].setVisible(True)

    # Overlay public methods

    def getFirstVisibleView(self):
        for i in range(9):
            r = i // 3
            c = i % 3
            view = self[r, c]
            if view.isVisible():
                return view
        return None

    def getLastVisibleView(self):
        for i in range(8, -1, -1):
            r = i // 3
            c = i % 3
            view = self[r, c]
            if view.isVisible():
                return view
        return None

    def getFirstVisibleSliceIndex(self):
        view = self.getFirstVisibleView()
        if isinstance(view, SliceROIViewWidget): return view.getSliceIndex()
        else: return None

    def getLastVisibleSliceIndex(self):
        view = self.getLastVisibleView()
        if isinstance(view, SliceROIViewWidget): return view.getSliceIndex()
        else: return None

    def addOverlay(self, volume, alpha=0.5):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                for i in range(0, 9):
                    self[i // 3, i % 3].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self):
        return self[0, 0].getOverlayCount()()

    def hasOverlay(self):
        return self[0, 0].hasOverlay()

    def getOverlayIndex(self, o):
        return self[0, 0].getOverlayIndex(o)

    def removeOverlay(self, o):
        for i in range(0, 9):
            self[i // 3, i % 3].removeOverlay(o)

    def removeAllOverlays(self):
        for i in range(0, 9):
            self[i // 3, i % 3].removeAllOverlays()

    def getOverlayFromIndex(self, index):
        return self[0, 0].getOverlayFromIndex(index)


class SynchronisedGridViewWidget(GridViewWidget):
    """
    SynchronisedGridViewWidget class

    Description
    ~~~~~~~~~~~

    Class designed to display the same slices from multiple volumes in a 3 x 3 grid layout. It provides additional
    functionalities such as overlay support and ROI support.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget -> SynchronisedGridViewWidget

    Creation: 03/04/2022
    Last revision: 27/05/2025
    """

    # Special method

    """
    Private attributes

    _nbv    int, volume count
    """

    def __init__(self, rois=None, draw=None, parent=None):
        super().__init__(rois, draw, parent)

        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            action = w.getAction()
            action['expand'].setVisible(True)

        self.popupMenuNumberOfVisibleViewsHide()

    # Private methods

    def _updateVisibleViews(self):
        # update visible views
        nbv = self[0, 0].getOverlayCount()
        if nbv < 3: self.setRowsAndCols(nbv // 3 + 1, nbv % 3 + 1)
        elif nbv == 3: self.setRowsAndCols(2, 2)
        elif nbv in [4, 5]: self.setRowsAndCols(2, 3)
        else: self.setRowsAndCols(3, 3)
        # update overlay display in each visible view
        # < Revision 27/05/2025
        # n = 0
        # for r in range(self.getRows()):
        #     for c in range(self.getCols()):
        #         if nbv > 0:
        #             view = self[r, c]
        #             if n <= nbv:
        #                 view.setVisible(True)
        #                 if n > 0: view.setOverlayColorbar(n - 1)
        #                 for i in range(nbv):
        #                     view.setOverlayVisibility(i, i == n - 1, signal=False)
        #             else: view.setVisible(False)
        #         n += 1
        if nbv > 0:
            for i in range(nbv):
                for r in range(self.getRows()):
                    for c in range(self.getCols()):
                        n = r * self.getCols() + c
                        view = self[r, c]
                        if n <= nbv:
                            view.setVisible(True)
                            if n > 0: view.setOverlayColorbar(n - 1)
                            view.setOverlayVisibility(i, i == n - 1, signal=False)
                        elif n > nbv: view.setVisible(False)
        # Revision 27/05/2025 >

    # Public methods

    def setVolume(self, volume):
        super().setVolume(volume)
        for i in range(9):
            r = i // 3
            c = i % 3
            self[r, c].setVolumeVisibility(i == 0, signal=False)
        # Reference volume is in the first view
        self._updateVisibleViews()

    def addSynchronisedVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                for i in range(0, 9):
                    self[i // 3, i % 3].addOverlay(volume, 1.0)
                self._updateVisibleViews()
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeSynchronisedVolume(self, v):
        if isinstance(v, SisypheVolume):
            if self.hasVolume():
                for i in range(0, 9):
                    self[i // 3, i % 3].removeOverlay(v)
                self._updateVisibleViews()
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def removeAllSynchronisedVolumes(self):
        if self.hasVolume():
            if self.hasOverlay():
                for i in range(0, 9):
                    self[i // 3, i % 3].removeAllOverlays()
                self._updateVisibleViews()

    def getSynchronisedVolumeCount(self):
        return self[0, 0].getOverlayCount()()

    def hasSynchronisedVolume(self):
        return self[0, 0].hasOverlay()

    def getSynchronisedVolumeIndex(self, o):
        return self[0, 0].getOverlayIndex(o)

    def getSynchronisedVolumeFromIndex(self, index):
        return self[0, 0].getOverlayFromIndex(index)

    #  Public method aliases

    addOverlay = addSynchronisedVolume
    removeOverlay = removeSynchronisedVolume
    removeAllOverlays = removeAllSynchronisedVolumes
    hasOverlay = hasSynchronisedVolume
    getOverlayIndex = getSynchronisedVolumeIndex
    getOverlayFromIndex = getSynchronisedVolumeFromIndex
