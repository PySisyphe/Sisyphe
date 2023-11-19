"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        skimage         https://scikit-image.org/                                   Image processing
        vtk             https://vtk.org/                                            Visualization
"""

from os import getcwd
from os import remove
from os.path import join
from os.path import exists

from platform import system

from tempfile import gettempdir

from numpy import flip
from numpy import stack

from skimage.util import montage
from skimage.io import imsave

from SimpleITK import GradientMagnitude
from SimpleITK import GradientMagnitudeRecursiveGaussian

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QApplication

from vtk import vtkWindowToImageFilter
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray

from Sisyphe.core.sisypheVolume import SisypheVolume
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
        
        QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalRegistrationViewWidget
                                                                -> OrthogonalReorientViewWidget
                                   -> OrthogonalSliceVolumeViewWidget -> OrthogonalSliceTrajectoryViewWidget
                                   -> GridViewWidget -> MultiSliceGridViewWidget
                                                     -> SynchronisedGridViewWidget
    Description
    
        Classes to display multiple synchronised slices, container of SliceViewWidget derived classes.
"""


class MultiViewWidget(QWidget):
    """
        MultiViewWidget class

        Description

            base class to display multiple slices.

        Inheritance

            QWidget -> MultiViewWidget

        Private attributes

            _rows       int, number of rows in the grid layout
            _cols       int, number of columns in the grid layout
            _n          int, view index for colorbar, orientation, cursor visibility
            _views      dict of abstractViewWidget instances

        Public methods

            __getitem__()
            __setitem__()
            __delitem__()
            __len__()
            setViewWidget(int, int, AbstractViewWidget)
            AbstractViewWidget = getViewWidgetAt(int, int)
            AbstractViewWidget = getFirstViewWidget()
            SliceViewWidget = getFirstSliceViewWidget()
            VolumeViewWidget = getFirstVolumeViewWidget()
            list = getSliceViewWidgets()
            list = getVolumeViewWidgets()
            int, int = getViewWidgetCoordinate(AbstractViewWidget)
            int = getViewWidgetCount()
            bool = isEmpty()
            bool = isNotEmpty()
            removeViewWidgetFromCoordinate(int, int)                row, column
            removeViewWidget(AbstractViewWidget)
            moveViewWidget(int, int, int, int)                      row, column of old and new positions
            swapViewWidgets(int, int, int, int)                     rows, columns of widgets to swap
            setRows(int)
            setCols(int)
            setRowsAndCols(int, int)
            int = getRows()
            int = getCols()
            int, int = getRowsAndCols()
            setVisibilityControlToView(int, int)
            setVisibilityControlToAll()
            int, int = getVisibilityControl()
            setFontColor(int)
            int = getFontColor()
            saveCapture()
            copyToClipboard()
            popupMenuEnabled()
            popupMenuDisabled()
            setActionVisibility(str, bool)
            showAction(str)
            hideAction(str)
            setRoundedCursorCoordinatesEnabled()
            setRoundedCursorCoordinatesDisabled()
            bool = isRoundedCursorCoordinatesEnabled()
            updateRender()                                          to update volume display

            inherited QWidget methods
    """

    # Special methods

    def __init__(self, r=1, c=1, parent=None):
        super().__init__(parent)

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
        return self._views.get(key, None)

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
            # add fullscreen display action
            if system() == 'Windows':
                action['screen'] = QAction('Fullscreen display', self)
                action['screen'].setCheckable(True)
                action['screen'].triggered.connect(self.toggleDisplay)
                widget.getPopup().insertAction(action['synchronisation'], action['screen'])
            # add expand display action
            action['expand'] = QAction('Expand display', self)
            action['expand'].setCheckable(True)
            action['expand'].triggered.connect(lambda: self.expandViewWidget(widget))
            widget.getPopup().insertAction(action['synchronisation'], action['expand'])
            action['synchronisation'].setVisible(False)
            # synchronise selection
            widget.Selected.connect(self._synchroniseSelection)
            # add view to layout
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

    def getFirstVolumeViewWidget(self):
        for w in self._views.values():
            if isinstance(w, VolumeViewWidget):
                return w

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
        else: raise IndexError('row or column parameter is out of range.')

    def removeViewWidget(self, widget):
        r, c = self.getViewWidgetCoordinate(widget)
        if r is not None:
            self.removeViewWidgetFromCoordinate(r, c)

    def moveViewWidget(self, r1, c1, r2, c2):
        if 0 <= r1 < 4 and 0 <= c1 < 4 and 0 <= r2 < 4 and 0 <= c2 < 4:
            if (r1, c1) in self._views:
                # remove tool from (r1, c1)
                widget = self.removeWidgetFromCoordinate(self._views[(r1, c1)])
                # add tool to (r2, c2)
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
        else:
            raise ValueError('row and/or column parameter is out of range.')

    def getRows(self):
        return self._rows

    def getCols(self):
        return self._cols

    def getRowsAndCols(self):
        return self._rows, self._cols

    def setVisibilityControlToView(self, r, c):
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views:
                self._n = (r, c)
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
                    w = self.getViewWidgetAt(i, j)
                    if expand: w.setVisible(widget == w)
                    else:  w.setVisible(True)
        else: raise TypeError('parameter type {} is not AbstractViewWidget.'.format(type(widget)))

    def isExpanded(self) -> bool:
        for i in range(self._rows):
            for j in range(self._cols):
                if self.getViewWidgetAt(i, j).getAction()['expand'].isChecked(): return True
        return False

    def getExpandedViewWidget(self) -> AbstractViewWidget | None:
        for i in range(self._rows):
            for j in range(self._cols):
                w = self.getViewWidgetAt(i, j)
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
        w = self.getFirstViewWidget()
        if w.getAction()['screen'].isChecked(): self.setFullScreenDisplay()
        else: self.setNormalDisplay()

    def isFullScreenDisplay(self) -> bool:
        if not self.isEmpty():
            return self._views[0, 0].getAction()['screen'].isChecked()

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

    def updateRender(self):
        for i in range(0, self._rows):
            for j in range(0, self._cols):
                w = self.getViewWidgetAt(i, j)
                if isinstance(w, SliceROIViewWidget): w.updateROIDisplay()
                else: w.updateRender()

    # AbstractView public methods

    def getFontColor(self):
        if self.isNotEmpty():
            return self._views[(0, 0)].getFontColor()

    def setFontColor(self, r, g, b):
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, AbstractViewWidget):
                    w.setFontColor(r, g, b)
                    w.updateRender()

    def saveCapture(self):
        if self.hasVolume():
            name = QFileDialog.getSaveFileName(self, caption='Save grid capture', directory=getcwd(),
                                               filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;TIFF (*.tiff)',
                                               initialFilter='JPG (*.jpg)')
            name = name[0]
            if name != '':
                imglist = list()
                c = vtkWindowToImageFilter()
                for view in self._views:
                    if self._views[view].isVisible():
                        c.SetInput(self._views[view].getRenderWindow())
                        r = vtkImageExportToArray()
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
                        imglist[i] = imglist[i][:s[0], :s[1], :s[2]]
                    # Layout
                    if n == 1: img = imglist[0]
                    else:
                        if n == 2: shape = (1, 2)
                        elif n == 3: shape = (1, 3)
                        elif n == 4: shape = (2, 2)
                        elif n == 6: shape = (2, 3)
                        elif n == 9: shape = (3, 3)
                        img = montage(stack(imglist), grid_shape=shape, multichannel=True)
                    try: imsave(name, img)
                    except Exception as err:
                        QMessageBox.warning(self, 'Save grid capture', 'error : {}'.format(err))

    def copyToClipboard(self):
        if self.hasVolume():
            imglist = list()
            c = vtkWindowToImageFilter()
            for view in self._views:
                if self._views[view].isVisible():
                    c.SetInput(self._views[view].getRenderWindow())
                    r = vtkImageExportToArray()
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
                    imglist[i] = imglist[i][:s[0], :s[1], :s[2]]
                # Layout
                if n == 1: img = imglist[0]
                else:
                    if n == 2: shape = (1, 2)
                    elif n == 3: shape = (1, 3)
                    elif n == 4: shape = (2, 2)
                    elif n == 6: shape = (2, 3)
                    elif n == 9: shape = (3, 3)
                    img = montage(stack(imglist), grid_shape=shape, multichannel=True)
                temp = join(gettempdir(), 'tmp.bmp')
                try:
                    imsave(temp, img)
                    p = QPixmap(temp)
                    QApplication.clipboard().setPixmap(p)
                except Exception as err:
                    QMessageBox.warning(self, 'Copy grid capture to clipboard', '{}'.format(err))
                finally:
                    if exists(temp): remove(temp)


class OrthogonalSliceViewWidget(MultiViewWidget):
    """
        OrthogonalSliceViewWidget class

        Description

            Displays synchronised axial, coronal and sagittal slices.

        Inheritance

            QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget

        Public methods

            setVolume(SisypheVolume)
            volumeCloseRequested()
            bool = hasVolume()
            addOverlay(SisypheVolume, float)
            int = getOverlayCount()
            bool = hasOverlay()
            removeOverlay(SisypheVolume)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)

            inherited MultiViewWidget methods
            inherited QWidget methods
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
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
                    w2 = self.getViewWidgetAt(0, j)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    w1.ToolMoved.connect(w2.synchroniseToolMoved)
                    w1.ToolRemoved.connect(w2.synchroniseToolRemoved)
                    w1.ToolColorChanged.connect(w2.synchroniseToolColorChanged)
                    w1.ToolAttributesChanged.connect(w2.synchroniseToolAttributesChanged)
                    w1.ToolRenamed.connect(w2.synchroniseToolRenamed)
                    w1.ToolAdded.connect(w2.synchroniseToolAdded)
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


class OrthogonalRegistrationViewWidget(OrthogonalSliceViewWidget):
    """
        OrthogonalSliceViewWidget class

        Description

            Derived from OrthogonalSliceViewWidget class. Adds capacity to apply rigid transformation and
            displays a box widget to crop overlay. Used to evaluate registration quality between two volumes.

        Inheritance

            QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalRegistrationViewWidget

        Public methods

            addOverlay(SisypheVolume, float)

            inherited OrthogonalSliceViewWidget
            inherited MultiViewWidget methods
            inherited QWidget methods
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    # Private method

    def _initViews(self):
        for i in range(3):
            widget = SliceRegistrationViewWidget()
            self.setViewWidget(0, i, widget)
            widget.synchronisationOn()
            widget.getPopup().actions()[3].setVisible(False)  # Orientation menu off
            widget.getAction()['moveoverlayflag'].setVisible(True)
        self[0, 0].setName('Axial view')
        self[0, 1].setName('Coronal view')
        self[0, 2].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        super()._initSynchronisationSignalConnect()
        for i in range(3):
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
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
                w = (rmax - rmin) / 15
                wmin = rmin + w
                wmax = rmax - 2 * w
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

            Derived from OrthogonalSliceViewWidget class. Adds capacity to apply rigid transformation and
            displays a box widget to show and manipulate field of view in the three orientations.

        Inheritance

            QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalReorientViewWidget

        Public methods

            translationsEnabled()
            translationsDisabled()
            rotationsEnabled()
            rotationsDisabled()
            setFOVBoxVisibility(bool)
            bool = getFOVBoxVisibility()
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
            setSliceNavigationEnabled()
            setSliceNavigationDisabled()
            bool = isSliceNavigationEnabled()

            inherited OrthogonalSliceViewWidget
            inherited MultiViewWidget methods
            inherited QWidget methods
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
            w1 = self.getViewWidgetAt(0, i)
            for j in range(3):
                if j != i:
                    w2 = self.getViewWidgetAt(0, j)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    w1.ResliceCursorChanged.connect(w2.synchroniseResliceCursorChanged)
                    w1.SpacingChanged.connect(w2.synchroniseSpacingChanged)
                    w1.SizeChanged.connect(w2.synchroniseSizeChanged)
                    w1.TranslationsChanged.connect(w2.synchroniseTranslationsChanged)
                    w1.RotationsChanged.connect(w2.synchroniseRotationsChanged)
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

            Displays synchronised axial, coronal and sagittal slices and volume rendering in 2 x 2 grid.

        Inheritance

            QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget

        Public methods

            setVolume(SisypheVolume)
            volumeCloseRequested()
            bool = hasVolume()
            addOverlay(SisypheVolume, float)
            int = getOverlayCount()
            bool = hasOverlay()
            removeOverlay(SisypheVolume)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)

            inherited MultiViewWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(2, 2, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self):
        for i in range(2):
            for j in range(2):
                if i == 0 and j == 0: widget = VolumeViewWidget()
                else:
                    widget = SliceOverlayViewWidget()
                    widget.getPopup().actions()[3].setVisible(False)
                    widget.getAction()['moveoverlayflag'].setVisible(False)
                    widget.synchronisationOn()
                self.setViewWidget(i, j, widget)
        self[0, 0].setName('3D view')
        self[0, 1].setName('Axial view')
        self[1, 0].setName('Coronal view')
        self[1, 1].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        for i in range(4):
            w1 = self.getViewWidgetAt(i // 2, i % 2)
            for j in range(4):
                if j != i:
                    w2 = self.getViewWidgetAt(j // 2, j % 2)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    w1.ToolMoved.connect(w2.synchroniseToolMoved)
                    w1.ToolRemoved.connect(w2.synchroniseToolRemoved)
                    w1.ToolColorChanged.connect(w2.ToolColorChanged)
                    w1.ToolAttributesChanged.connect(w2.synchroniseToolAttributesChanged)
                    w1.ToolRenamed.connect(w2.synchroniseToolRenamed)
                    w1.ToolAdded.connect(w2.synchroniseToolAdded)
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


class OrthogonalTrajectoryViewWidget(OrthogonalSliceVolumeViewWidget):
    """
        OrthogonalSliceVolumeViewWidget class

        Description

            Derived from OrthogonalSliceVolumeViewWidget class. Adds trajectory management.

        Inheritance

            QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget -> OrthogonalTrajectoryViewWidget

        Public methods

            popupAlignmentEnabled()
            popupAlignmentDisabled()

            inherited OrthogonalSliceVolumeViewWidget
            inherited MultiViewWidget methods
            inherited QWidget methods

        Revisions:

            02/10/2023  add SlabChanged event in _initSynchronisationSignalConnect() method
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

    # Private methods

    def _initViews(self):
        for i in range(2):
            for j in range(2):
                if i == 0 and j == 0:
                    widget = VolumeViewWidget()
                    widget.setRoundedCursorCoordinatesDisabled()
                    widget.synchronisationOn()
                else:
                    widget = SliceTrajectoryViewWidget()
                    widget.getPopup().actions()[3].setVisible(False)
                    widget.getAction()['moveoverlayflag'].setVisible(False)
                    widget.synchronisationOn()
                self.setViewWidget(i, j, widget)
        self[0, 0].setName('3D view')
        self[0, 1].setName('Axial view')
        self[1, 0].setName('Coronal view')
        self[1, 1].setName('Sagittal view')
        self.setVisibilityControlToAll()

    def _initSynchronisationSignalConnect(self):
        super()._initSynchronisationSignalConnect()
        for i in range(4):
            w1 = self.getViewWidgetAt(i // 2, i % 2)
            if isinstance(w1, SliceTrajectoryViewWidget):
                w1.TrajectoryCameraAligned.connect(self.synchroniseTrajectoryCameraAligned)
            elif isinstance(w1, VolumeViewWidget):
                w1.CameraChanged.connect(self.synchroniseCameraChanged)
            for j in range(4):
                if j != i:
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

    def synchroniseTrajectoryCameraAligned(self, obj):
        camera = self.getFirstVolumeViewWidget().getRenderer().GetActiveCamera()
        views = self.getSliceViewWidgets()
        for view in views:
            view.setTrajectoryFromCamera(camera, signal=False)


class GridViewWidget(MultiViewWidget):
    """
        GridViewWidget class

        Description

            Base class to display 3 x 3 grid of slices.

        Inheritance

            QWidget -> MultiViewWidget -> GridViewWidget

        Private attributes

            _menuNumberOfVisibleViews   QMenu

        Public methods

            setAxialOrientation()
            setCoronalOrientation()
            setSagittalOrientation()
            setOrientation(int)
            int = getOrientation()
            str = getOrientationAsString()
            int, int = getViewsArrangement()
            QMenu = getSubmenuNumberOfVisibleViews()
            popupMenuOrientationEnabled()
            popupMenuOrientationDisabled()
            popupMenuROIEnabled()
            popupMenuROIDisabled()

            inherited MultiViewWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, rois=None, draw=None, parent=None):
        super().__init__(3, 3, parent)

        self._menuNumberOfVisibleViews = None

        self._initViews(rois, draw)
        self._initActions()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self, rois, draw):
        # ovls = None
        # rois = None
        # draw = None
        for i in range(9):
            if i == 0:
                if rois is not None and draw is not None: w = SliceROIViewWidget(rois=rois, draw=draw)
                else:
                    w = SliceROIViewWidget()
                    # ovls = w.getOverlayCollection()
                    rois = w.getROICollection()
                    draw = w.getDrawInstance()
            # else: w = SliceROIViewWidget(overlays=ovls, rois=rois, draw=draw)
            else: w = SliceROIViewWidget(rois=rois, draw=draw)
            self.setViewWidget(i // 3, i % 3, w)
        self.setVisibilityControlToAll()

    def _initActions(self):
        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.setName('view#{}'.format(i))
            w.synchronisationOn()
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
            popup = w.getPopup()
            self._menuNumberOfVisibleViews = QMenu('Number of views', popup)
            self._menuNumberOfVisibleViews.addAction(action['11'])
            self._menuNumberOfVisibleViews.addAction(action['12'])
            self._menuNumberOfVisibleViews.addAction(action['13'])
            self._menuNumberOfVisibleViews.addAction(action['22'])
            self._menuNumberOfVisibleViews.addAction(action['23'])
            self._menuNumberOfVisibleViews.addAction(action['33'])
            popup.insertMenu(popup.actions()[2], self._menuNumberOfVisibleViews)

    def _initSynchronisationSignalConnect(self):
        for i in range(9):
            w1 = self.getViewWidgetAt(i // 3, i % 3)
            for j in range(9):
                if j != i:
                    w2 = self.getViewWidgetAt(j // 3, j % 3)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
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
                    if isinstance(w1, SliceROIViewWidget) and isinstance(w2, SliceROIViewWidget):
                        w1.ROIAttributesChanged.connect(w2.synchroniseROIAttributesChanged)
                        w1.ROISelectionChanged.connect(w2.synchroniseROISelectionChanged)
                        w1.ROIModified.connect(w2.synchroniseROIModified)
                        w1.BrushRadiusChanged.connect(w2.synchroniseBrushRadiusChanged)
                        w1.ROIFlagChanged.connect(w2.synchroniseROIFlagChanged)

    # Public methods

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            for i in range(0, 9):
                self[i // 3, i % 3].setVolume(volume)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

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

            Derived from GridViewWidget class. Displays several adjacent slices in 3 x 3 grid
            with overlays and ROI support.

        Inheritance

            QWidget -> MultiViewWidget -> GridViewWidget -> MultiSliceGridViewWidget

        Public methods

            SliceROIViewWidget = getFirstVisibleView()
            SliceROIViewWidget = getLastVisibleView()
            int = getFirstVisibleSliceIndex()
            int = getLastVisibleSliceIndex()
            addOverlay(SisypheVolume, float)
            int = getOverlayCount()
            bool = hasOverlay()
            int = getOverlayIndex(SisypheVolume)
            removeOverlay(SisypheVolume)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)

            inherited GridViewWidget methods
            inherited MultiViewWidget methods
            inherited QWidget methods

        Revision(s):

            12/08/2023  add getFirstVisibleView(), getLastVisibleView() methods
                        add getFirstVisibleSliceIndex(), getLastVisibleSliceIndex methods
    """

    # Special method

    def __init__(self, rois=None, draw=None, parent=None):
        super().__init__(rois, draw, parent)

        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.setOffset(i)  # nine consecutive slices of the same volume
            if i > 0: w.setCursorVisibilityOff()
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

    def getLastVisibleView(self):
        for i in range(8, -1, -1):
            r = i // 3
            c = i % 3
            view = self[r, c]
            if view.isVisible():
                return view

    def getFirstVisibleSliceIndex(self):
        view = self.getFirstVisibleView()
        if isinstance(view, SliceROIViewWidget):
            return view.getSliceIndex()

    def getLastVisibleSliceIndex(self):
        view = self.getLastVisibleView()
        if isinstance(view, SliceROIViewWidget):
            return view.getSliceIndex()

    def addOverlay(self, volume, alpha=0.5):
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                for i in range(0, 9):
                    self[i // 3, i % 3].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self):
        return self[0, 0].getNumberOfOverlays()

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

            Displays same slices of multiple volumes in 3 x 3 grid.

        Inheritance

            QWidget -> MultiViewWidget -> GridViewWidget -> SynchronisedGridViewWidget

        Private attributes

            _nbv    int, volumes count

        Public methods

            addSynchronisedVolume(SisypheVolume, int)
            removeSynchronisedVolume(SisypheVolume)
            removeAllSynchronisedVolumes()
            removeSynchronisedVolumeFromIndex(int)
            int = getSynchronisedVolumeCount()
            bool = hasSynchronisedVolume()

            inherited GridViewWidget methods
            inherited MultiViewWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, rois=None, draw=None, parent=None):
        super().__init__(rois, draw, parent)

        # _nbv = 1 reference volume + synchronised volumes count
        self._nbv = 0
        self._volume = None

        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            action = w.getAction()
            action['expand'].setVisible(True)

    # Private method

    def _updateVisibleViews(self):
        if self._nbv < 3: self.setNumberOfVisibleViews(1, self._nbv)
        elif self._nbv in [3, 4]: self.setNumberOfVisibleViews(2, 2)
        else: self.setNumberOfVisibleViews(self._nbv // 3 + 1, 3)

    # Public methods

    def setVolume(self, volume):
        super().setVolume(volume)
        # Reference volume is the first
        self._nbv = 1

    def addSynchronisedVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            if self._nbv < 9:
                r = self._nbv // 3
                c = self._nbv % 3
                self[r, c].addOverlay(volume, alpha=1.0)
                self[r, c].setOverlayColorbar()
                self._nbv += 1
                self._updateVisibleViews()
            else:
                self[2, 2].removeOverlay(0)
                self[2, 2].addOverlay(volume, alpha=1.0)
        else: raise TypeError('volume parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeSynchronisedVolume(self, v):
        if self.hasVolume():
            if isinstance(v, SisypheVolume):
                for i in range(0, self._nbv):
                    r = i // 3
                    c = i % 3
                    self[r, c].removeOverlay(v)
                self._nbv -= 1
                self._updateVisibleViews()
            else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def removeAllSynchronisedVolumes(self):
        if self.hasVolume():
            for i in range(0, self._nbv):
                r = i // 3
                c = i % 3
                self[r, c].removeOverlay(0)
            self._nbv = 1
            self._updateVisibleViews()

    def removeSynchronisedVolumeFromIndex(self, index):
        if self.hasVolume():
            if isinstance(index, int):
                if 0 <= index < self._nbv:
                    self[index // 3, index % 3].removeVolume()
                    self._nbv -= 1
                    self._updateVisibleViews()
                else: raise ValueError('index parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getSynchronisedVolumeCount(self):
        return self._nbv - 1

    def hasSynchronisedVolume(self):
        return self._nbv > 1

    #  Public method aliases

    addOverlay = addSynchronisedVolume
    removeOverlay = removeSynchronisedVolume
    removeAllOverlays = removeAllSynchronisedVolumes
    hasOverlay = hasSynchronisedVolume


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QWidget, QHBoxLayout

    test = 3
    app = QApplication(argv)
    main = QWidget()
    layout = QHBoxLayout(main)
    if test == 0:  # OrthogonalSliceViewWidget, OK 02/06/2021
        print('Test OrthogonalSliceViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        view1 = OrthogonalSliceViewWidget()
        view1.setVolume(img1)
        view1.addOverlay(img2)
        view1.getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
        view1.getFirstSliceViewWidget().setXAxisConstraintToCursor()
    elif test == 1:  # OrthogonalSliceVolumeViewWidget OK 03/06/2021
        print('Test OrthogonalSliceVolumeViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        view1 = OrthogonalSliceVolumeViewWidget()
        view1.setVolume(img1)
        view1.addOverlay(img2)
        view1.getViewWidgetAt(0, 1).setOverlayOpacity(0, 0.2)
    elif test == 2:  # OrthogonalTrajectoryViewWidget
        print('Test OrthogonalTrajectoryViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        view1 = OrthogonalTrajectoryViewWidget()
        view1.setVolume(img1)
        view1.addOverlay(img2)
        view1.getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
    elif test == 3:  # OrthogonalReorientViewWidget OK 15/06/2021
        print('Test OrthogonalReorientViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/OVERLAY/3D.xvol'
        img1 = SisypheVolume()
        img1.load(file1)
        view1 = OrthogonalReorientViewWidget()
        view1.setVolume(img1)
    elif test == 4:  # MultiSliceGridViewWidget OK 17/06/2021
        print('Test MultiSliceGridViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/ROI/STEREO3D.xvol'
        img1 = SisypheVolume()
        img1.load(file1)
        view1 = MultiSliceGridViewWidget()
        view1.setVolume(img1)
        view1.getFirstSliceViewWidget().loadROI('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/ROI/testroi1.xroi')
        view1.getFirstSliceViewWidget().loadROI('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/ROI/testroi2.xroi')
        view1.getFirstSliceViewWidget().loadROI('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/ROI/testroi3.xroi')
        view1.getFirstSliceViewWidget().setBrushRadius(5)
        view1.getFirstSliceViewWidget().setSolidBrushFlagOn()
        view1.getFirstSliceViewWidget().setFillHolesFlagOn()
        view1.getFirstSliceViewWidget().setUndoOn()
    elif test == 5:  # SynchronisedGridViewWidget OK 17/06/2021
        print('SynchronisedGridViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2 = SisypheVolume()
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        view1 = SynchronisedGridViewWidget()
        view1.addSynchronisedVolume(img1)
        view1.addSynchronisedVolume(img2)
    else:  # OrthogonalRegistrationViewWidget
        print('Test OrthogonalRegistrationViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        view1 = OrthogonalRegistrationViewWidget()
        view1.setVolume(img1)
        view1.addOverlay(img2)
        view1.getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
    layout.addWidget(view1)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    main.activateWindow()
    exit(app.exec_())
