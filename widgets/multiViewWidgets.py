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

from os import getcwd
from os import chdir
from os import remove

from os.path import join
from os.path import exists
from os.path import dirname

import cython

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

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheMesh import SisypheMesh
    from Sisyphe.core.sisypheROI import SisypheROICollection
    from Sisyphe.core.sisypheROI import SisypheROIDraw
    # < Revision 26/02/2026
    from Sisyphe.processing.segmentation import SegmentAnything
    # Revision 26/02/2026 >

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

Classes to display multiple synchronized slices, container of SliceViewWidget derived classes.
"""

# noinspection SpellCheckingInspection
class MultiViewWidget(QWidget):
    """
    MultiViewWidget class

    Description
    ~~~~~~~~~~~

    Base class that serves as a container for managing and displaying multiple, synchronized viewports in a grid layout.
    It provides the core infrastructure for creating complex, interactive multi-view displays by arranging instances of
    AbstractViewWidget subclasses.

    The main features are as follows:

    - Grid-based Layout: arranges child widgets in a configurable grid of up to 4x4. It dynamically manages the visibility of widgets based on the specified number of rows and columns.
    - Comprehensive widget management: provides a full API for adding, removing, retrieving, moving, and swapping widgets within the grid. Widgets can be accessed by their coordinates or through helper methods like getFirstViewWidget() and getSelectedViewWidget().
    - View synchronization and control:

        - Ensures that only one view can be selected at a time across the entire grid.
        - Offers centralized methods to propagate settings—such as line colors, font styles, and popup menu states—to all contained views simultaneously.

    - Interactive display modes:

        - Expand View: allows a single widget to be temporarily expanded to fill the entire grid area, hiding all others for focused inspection.
        - Fullscreen mode: Toggles the entire widget container between normal and fullscreen display.

    - Grid capture functionality: built-in functionality to capture all visible views as a single montage image. The resulting image can be saved to a bitmap file or copied directly to the system clipboard.
    - VTK Finalization: provides an explicit finalize() method to ensure proper cleanup of VTK resources, preventing common rendering errors upon window closure, particularly on the Windows platform.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget

    Creation: 03/04/2022
    Last revision: 05/02/2026
    """

    # Special methods

    def __init__(self, r: int = 1, c: int = 1, parent: QWidget | None = None) -> None:
        """
        MultiViewWidget instance constructor.

        Parameters
        ----------
        r : int (optional)
            number of rows in the grid layout (default 1).
        c : int (optional)
            number of columns in the grid layout (default 1).
        parent : QWidget | None, optional
            parent widget (default None).
        """
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

    """
    Private attributes

    _rows       int, number of visible rows in the grid layout
    _cols       int, number of visible columns in the grid layout
    _n          int, view index for colorbar, orientation, cursor visibility
    _views      dict[tuple[int, int], abstractViewWidget]
    """

    def __getitem__(self, key: tuple[int, int]) -> AbstractViewWidget:
        """
        Get the view widget at a specified grid coordinate.

        Parameters
        ----------
        key : tuple[int, int]
            (row, column) coordinate of the widget to retrieve.

        Returns
        -------
        AbstractViewWidget
            view widget at the specified coordinate.
        """
        # < Revision 18/03/2025
        # return self._views.get(key, None)
        return self._views[key]
        # Revision 18/03/2025 >

    def __setitem__(self, key: tuple[int, int], value: AbstractViewWidget) -> None:
        """
        Set or replace the view widget at a specified grid coordinate.

        Parameters
        ----------
        key : tuple[int, int]
            (row, column) coordinate where the widget will be placed.
        value : AbstractViewWidget
            view widget to place in the grid.
        """
        self.setViewWidget(key[0], key[1], value)

    def __delitem__(self, key: tuple[int, int]) -> None:
        """
        Remove the view widget from a specified grid coordinate.

        Parameters
        ----------
        key : tuple[int, int]
            (row, column) coordinate of the widget to remove.
        """
        self.removeViewWidgetFromCoordinate(key[0], key[1])

    def __len__(self) -> int:
        """
        Get the total number of view widgets in the container.

        Returns
        -------
        int
            number of view widgets.
        """
        return len(self._views)

    # Private method

    def _updateVisibility(self) -> None:
        """
        Updates view widgets visbility from _rows and _cols attributes.
        """
        if self.isNotEmpty():
            r = self._rows - 1
            c = self._cols - 1
            for k in self._views:
                if k[0] > r or k[1] > c: self._views[k].hide()
                else: self._views[k].show()

    # Private synchronization event method

    def _synchroniseSelection(self, obj: QWidget) -> None:
        """
        Updates widget selection to ensure that only one widget is selected.
        """
        if not self.isEmpty():
            for w in self._views.values():
                if w != obj: w.unselect()

    # Public methods

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be explicitely called before destruction
    def finalize(self) -> None:
        """
        Method to be called before MultiViewWidget instance destruction.
        It is used to avoid vtk error on Windows platform (vtkWin32OpenGLRenderWindow error: 'wglMakeCurrent failed in
        MakeCurrent()').
        """
        for w in self._views.values():
            w.finalize()
    # Revision 08/03/2025 >

    def setViewWidget(self, r: int, c: int, widget: AbstractViewWidget) -> None:
        """
        Add a view widget to the grid at a specified coordinate.
        This method also configures the widget's popup menu for grid-specific actions like capturing the entire grid.

        Parameters
        ----------
        r : int
            row index for the widget.
        c : int
            column index for the widget.
        widget : AbstractViewWidget
            view widget to add to the grid.
        """
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
            # synchronize selection
            widget.Selected.connect(self._synchroniseSelection)
            # addBundle view to layout
            widget.setParent(self)
            widget.setObjectName('{} {} {}'.format(str(type(widget)), str(r), str(c)))
            self._views[(r, c)] = widget
            self._layout.addWidget(widget, r, c)
        else: raise IndexError('row and/or column parameter is out of range.')

    def getViewWidgetAt(self, r: int, c: int) -> AbstractViewWidget | None:
        """
        Get the view widget at a specific row and column.

        Parameters
        ----------
        r : int
            row index.
        c : int
            column index.

        Returns
        -------
        AbstractViewWidget | None
            view widget at the specified coordinate, or None if no widget is present.
        """
        return self._views.get((r, c), None)

    def getFirstViewWidget(self) -> AbstractViewWidget | None:
        """
        Get the view widget at the top-left position (0, 0).

        Returns
        -------
        AbstractViewWidget | None
            view widget at coordinate (0, 0), or None if it does not exist.
        """
        return self._views.get((0, 0), None)

    def getFirstSliceViewWidget(self) -> SliceViewWidget | None:
        """
        Get the first instance of a SliceViewWidget found in the grid.

        Returns
        -------
        SliceViewWidget | None
            first SliceViewWidget instance, or None if none are present.
        """
        for w in self._views.values():
            if isinstance(w, SliceViewWidget):
                return w
        return None

    def getFirstVolumeViewWidget(self) -> VolumeViewWidget | None:
        """
        Get the first instance of a VolumeViewWidget found in the grid.

        Returns
        -------
        VolumeViewWidget | None
            first VolumeViewWidget instance, or None if none are present.
        """
        for w in self._views.values():
            if isinstance(w, VolumeViewWidget):
                return w
        return None

    def getSliceViewWidgets(self) -> list[SliceViewWidget]:
        """
        Get a list of all SliceViewWidget instances in the grid.

        Returns
        -------
        list[SliceViewWidget]
            list of all SliceViewWidget instances.
        """
        ws = list()
        for w in self._views.values():
            if isinstance(w, SliceViewWidget):
                ws.append(w)
        return ws

    def getVolumeViewWidgets(self) -> list[VolumeViewWidget]:
        """
        Get a list of all VolumeViewWidget instances in the grid.

        Returns
        -------
        list[VolumeViewWidget]
            list of all VolumeViewWidget instances.
        """
        ws = list()
        for w in self._views.values():
            if isinstance(w, VolumeViewWidget):
                ws.append(w)
        return ws

    def getViewWidgetCoordinate(self, widget: AbstractViewWidget) -> tuple[int, int] | tuple[None, None]:
        """
        Get the grid coordinate (row, column) of a specific view widget.

        Parameters
        ----------
        widget : AbstractViewWidget
            view widget to locate.

        Returns
        -------
        tuple[int, int] | tuple[None, None]
            (row, column) coordinate of the widget, or (None, None) if not found.
        """
        if isinstance(widget, AbstractViewWidget):
            v = list(self._views.values())
            if widget in v:
                i = v.index(widget)
                return list(self._views.keys())[i]
            else: return None, None
        else: raise TypeError('tool parameter type {} is not AbstractViewWidget.'.format(type(widget)))

    def getSelectedViewWidget(self) -> AbstractViewWidget | None:
        """
        Get the currently selected view widget in the grid.

        Returns
        -------
        AbstractViewWidget | None
            selected view widget, or None if no widget is selected.
        """
        if not self.isEmpty():
            for w in self._views.values():
                if w.isSelected(): return w
        return None

    def getViewWidgetCount(self) -> int:
        """
        Get the total number of view widgets in the grid.

        Returns
        -------
        int
            total count of view widgets.
        """
        return len(self._views)

    def isEmpty(self) -> bool:
        """
        Check if the grid contains any view widgets.

        Returns
        -------
        bool
            True if the grid is empty, False otherwise.
        """
        return len(self._views) == 0

    def isNotEmpty(self) -> bool:
        """
        Check if the grid contains at least one view widget.

        Returns
        -------
        bool
            True if the grid is not empty, False otherwise.
        """
        return len(self._views) > 0

    def removeViewWidgetFromCoordinate(self, r: int, c: int) -> None:
        """
        Remove a view widget from the grid at a specified coordinate.

        Parameters
        ----------
        r : int
            row index of the widget to remove.
        c : int
            column index of the widget to remove.
        """
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views:
                self._layout.removeWidget(self._views[(r, c)])
                return self._views.pop((r, c))
            else: raise IndexError('invalid row or column.')
        else: raise IndexError('row or column parameter is out of range.')

    def removeViewWidget(self, widget: AbstractViewWidget) -> None:
        """
        Remove a specific view widget instance from the grid.

        Parameters
        ----------
        widget : AbstractViewWidget
            view widget instance to remove.
        """
        r, c = self.getViewWidgetCoordinate(widget)
        if r is not None:
            self.removeViewWidgetFromCoordinate(r, c)

    def moveViewWidget(self, r1: int, c1: int, r2: int, c2: int) -> None:
        """
        Move a view widget from one grid coordinate to another.
        If the destination is occupied, the widgets are swapped.

        Parameters
        ----------
        r1 : int
            source row index.
        c1 : int
            source column index.
        r2 : int
            destination row index.
        c2 : int
            destination column index.
        """
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

    def swapViewWidgets(self, r1: int, c1:int, r2:int, c2:int) -> None:
        """
        Swap the positions of two view widgets in the grid.

        Parameters
        ----------
        r1 : int
            row index of the first widget.
        c1 : int
            column index of the first widget.
        r2 : int
            row index of the second widget.
        c2 : int
            column index of the second widget.
        """
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

    def setRows(self, r: int) -> None:
        """
        Set the number of visible rows in the grid.

        Parameters
        ----------
        r : int
            number of rows to display (0-3).
        """
        if 0 <= r < 4:
            self._rows = r
            self._updateVisibility()
        else: raise ValueError('row parameter value {} is out of range.'.format(r))

    def setCols(self, c: int) -> None:
        """
        Set the number of visible columns in the grid.

        Parameters
        ----------
        c : int
            number of columns to display (0-3).
        """
        if 0 <= c < 4:
            self._cols = c
            self._updateVisibility()
        else: raise ValueError('column parameter value {} is out of range.'.format(c))

    def setRowsAndCols(self, r: int, c: int) -> None:
        """
        Set the number of visible rows and columns in the grid.

        Parameters
        ----------
        r : int
            number of rows to display (0-3).
        c : int
            number of columns to display (0-3).
        """
        if 0 <= r < 4 and 0 <= c < 4:
            self._rows = r
            self._cols = c
            self._updateVisibility()
        else: raise ValueError('row and/or column parameter is out of range.')

    def getRows(self) -> int:
        """
        Get the number of visible rows in the grid.

        Returns
        -------
        int
            current number of visible rows.
        """
        return self._rows

    def getCols(self) -> int:
        """
        Get the number of visible columns in the grid.

        Returns
        -------
        int
            current number of visible columns.
        """
        return self._cols

    def getRowsAndCols(self) -> tuple[int, int]:
        """
        Get the number of visible rows and columns in the grid.

        Returns
        -------
        tuple[int, int]
            (rows, columns) currently visible.
        """
        return self._rows, self._cols

    def setVisibilityControlToView(self, r: int, c: int) -> None:
        """
        Set a specific view to be the master for visibility-related synchronizations (e.g., colorbar, cursor).

        Parameters
        ----------
        r : int
            row index of the master view.
        c : int
            column index of the master view.
        """
        if 0 <= r < 4 and 0 <= c < 4:
            if (r, c) in self._views: self._n = (r, c)
            else: raise ValueError('No abstractViewWidget at ({},{}) coordinate.'.format(r, c))
        else: raise IndexError('row and/or column is out of range.')

    def setVisibilityControlToAll(self) -> None:
        """
        Set visibility control to apply to all views, rather than a single master view.
        """
        self._n = None

    def getVisibilityControl(self) -> int:
        """
        Get the master view index for visibility-related synchronizations (e.g., colorbar, cursor)

        Returns
        -------
        int
            index of the master view, or None if control applies to all views.
        """
        return self._n

    def getNumberOfVisibleViews(self) -> int:
        """
        Get the number of currently visible view widgets.

        Returns
        -------
        int
            count of visible views.
        """
        n = 0
        # < Revision 06/05/2026
        # bug fix
        # for view in self._views:
        #   if views.isVisible(): n += 1
        for k in self._views:
            if self._views[k].isVisible(): n += 1
        # Revision 06/05/2026 >
        return n

    def expandViewWidget(self, widget: AbstractViewWidget) -> None:
        """
        Expand a single view widget to fill the entire grid area, hiding all others.

        Parameters
        ----------
        widget : AbstractViewWidget
            view widget to expand.
        """
        if isinstance(widget, AbstractViewWidget):
            expand = widget.getAction()['expand'].isChecked()
            i: cython.int
            j: cython.int
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
        """
        Check if any view widget is currently expanded.

        Returns
        -------
        bool
            True if a view is expanded, False otherwise.
        """
        i: cython.int
        j: cython.int
        for i in range(self._rows):
            for j in range(self._cols):
                # noinspection PyUnresolvedReferences
                if self.getViewWidgetAt(i, j).getAction()['expand'].isChecked(): return True
        return False

    def getExpandedViewWidget(self) -> AbstractViewWidget | None:
        """
        Get the currently expanded view widget.

        Returns
        -------
        AbstractViewWidget | None
            expanded view widget, or None if no view is expanded.
        """
        i: cython.int
        j: cython.int
        for i in range(self._rows):
            for j in range(self._cols):
                # noinspection PyNoneFunctionAssignment
                w = self.getViewWidgetAt(i, j)
                # noinspection PyUnresolvedReferences
                if w.getAction()['expand'].isChecked(): return w
        return None

    def setFullScreenDisplay(self) -> None:
        """
        Set the multi-view widget to fullscreen display mode.
        """
        if not self.isEmpty():
            self.showFullScreen()
            for w in self._views.values():
                w.getAction()['screen'].setChecked(True)

    def setNormalDisplay(self) -> None:
        """
        Restore the multi-view widget to its normal (non-fullscreen) display mode.
        """
        if not self.isEmpty():
            self.showNormal()
            for w in self._views.values():
                w.getAction()['screen'].setChecked(False)

    def toggleDisplay(self) -> None:
        """
        Toggle the display mode between fullscreen and normal.
        """
        # noinspection PyNoneFunctionAssignment
        w = self.getFirstViewWidget()
        # noinspection PyUnresolvedReferences
        if w.getAction()['screen'].isChecked(): self.setFullScreenDisplay()
        else: self.setNormalDisplay()

    def isFullScreenDisplay(self) -> bool:
        """
        Check if the widget is currently in fullscreen display mode.

        Returns
        -------
        bool
            True if in fullscreen mode, False otherwise.
        """
        if not self.isEmpty():
            return self._views[0, 0].getAction()['screen'].isChecked()
        else: raise AttributeError('View is empty.')

    def popupMenuEnabled(self) -> None:
        """
        Enable the popup context menu for all view widgets in the grid.
        """
        for w in self._views.values():
            w.popupMenuEnabled()

    def popupMenuDisabled(self) -> None:
        """
        Disable the popup context menu for all view widgets in the grid.
        """
        for w in self._views.values():
            w.popupMenuDisabled()

    def popupMenuActionsEnabled(self) -> None:
        """
        Enable the 'Actions' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupActionsEnabled()

    def popupMenuActionsDisabled(self) -> None:
        """
        Disable the 'Actions' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupActionsDisabled()

    def popupMenuVisibilityEnabled(self) -> None:
        """
        Enable the 'Visibility' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupVisibilityEnabled()

    def popupMenuVisibilityDisabled(self) -> None:
        """
        Disable the 'Visibility' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupVisibilityDisabled()

    def popupMenuColorbarPositionEnabled(self) -> None:
        """
        Enable the 'Colorbar position' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupColorbarPositionEnabled()

    def popupMenuColorbarPositionDisabled(self) -> None:
        """
        Disable the 'Colorbar position' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupColorbarPositionDisabled()

    def popupMenuToolsEnabled(self) -> None:
        """
        Enable the 'Tools' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupToolsEnabled()

    def popupMenuToolsDisabled(self) -> None:
        """
        Disable the 'Tools' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupToolsDisabled()

    def setActionVisibility(self, name: str, v: bool) -> None:
        """
        Set the visibility of a specific action in the popup menu for all view widgets.

        Parameters
        ----------
        name : str
            name of the action to modify.
        v : bool
            True to make the action visible, False to hide it.
        """
        if isinstance(name, str):
            if isinstance(v, bool):
                i: cython.int
                j: cython.int
                for i in range(0, self._rows):
                    for j in range(0, self._cols):
                        action = self._views[i, j].getAction()
                        if action is not None:
                            if name in action:
                                action[name].setVisible(v)
            else: raise TypeError('second parameter type {} is not bool.'.format(type(v)))
        else: raise TypeError('first parameter type {} is not str.'.format(type(name)))

    def showAction(self, name: str) -> None:
        """
        Show a specific action in the popup menu for all view widgets.

        Parameters
        ----------
        name : str
            name of the action to show.
        """
        self.setActionVisibility(name, True)

    def hideAction(self, name: str) -> None:
        """
        Hide a specific action in the popup menu for all view widgets.

        Parameters
        ----------
        name : str
            name of the action to hide.
        """
        self.setActionVisibility(name, False)

    def setRoundedCursorCoordinatesEnabled(self) -> None:
        """
        Enable rounding of cross-shaped cursor coordinates to the nearest voxel for all view widgets.
        """
        i: cython.int
        j: cython.int
        for i in range(0, self._rows):
            for j in range(0, self._cols):
                self._views[i, j].setRoundedCursorCoordinatesEnabled()

    def setRoundedCursorCoordinatesDisabled(self) -> None:
        """
        Disable rounding of cross-shaped cursor coordinates for all view widgets.
        """
        i: cython.int
        j: cython.int
        for i in range(0, self._rows):
            for j in range(0, self._cols):
                self._views[i, j].setRoundedCursorCoordinatesDisabled()

    def isRoundedCursorCoordinatesEnabled(self) -> bool:
        """
        Check if cross-shaped cursor coordinate rounding is enabled.

        Returns
        -------
        bool
            True if rounding is enabled, False otherwise.
        """
        return self._views[0, 0].isRoundedCursorCoordinatesEnabled()

    def setAlignCenters(self, v: bool) -> None:
        """
        Set the automatic center alignment policy for overlays in all applicable view widgets.

        Parameters
        ----------
        v : bool
            True to enable automatic alignment, False to disable.
        """
        if len(self._views) > 0:
            for k in self._views:
                w = self._views[k]
                if isinstance(w, SliceOverlayViewWidget):
                    w.setAlignCenters(v)

    def alignCentersOn(self) -> None:
        """
        Enable automatic center alignment for overlays in all applicable view widgets.
        """
        self.setAlignCenters(True)

    def alignCentersOff(self) -> None:
        """
        Disable automatic center alignment for overlays in all applicable view widgets.
        """
        self.setAlignCenters(False)

    def getAlignCenters(self) -> bool | None:
        """
        Get the automatic center alignment policy.

        Returns
        -------
        bool | None
            True if alignment is enabled, False if disabled, or None if no applicable views exist.
        """
        if len(self._views) > 0:
            i: cython.int
            j: cython.int
            for i in range(0, self._rows):
                for j in range(0, self._cols):
                    # noinspection PyNoneFunctionAssignment
                    w = self.getViewWidgetAt(i, j)
                    if isinstance(w, SliceOverlayViewWidget):
                        return w.getAlignCenters()
        return None

    def updateRender(self) -> None:
        """
        Trigger a render update for all view widgets in the grid.
        """
        if len(self._views) > 0:
            i: cython.int
            j: cython.int
            for i in range(0, self._rows):
                for j in range(0, self._cols):
                    # noinspection PyNoneFunctionAssignment
                    w = self.getViewWidgetAt(i, j)
                    if isinstance(w, SliceROIViewWidget): w.updateROIDisplay()
                    else:
                        # noinspection PyUnresolvedReferences
                        w.updateRender()

    # Display setting methods

    def setLineColor(self, c: list[float] | tuple[float, float, float]) -> None:
        """
        Set the line color for all view widgets.

        Parameters
        ----------
        c : list[float] | tuple[float, float, float]
            RGB color values (0.0-1.0).
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineColor(c, signal=False)

    def setLineSelectedColor(self, c: list[float] | tuple[float, float, float]) -> None:
        """
        Set the selected line color for all view widgets.

        Parameters
        ----------
        c : list[float] | tuple[float, float, float]
            RGB color values (0.0-1.0).
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineSelectedColor(c, signal=False)

    def setLineWidth(self, v: float) -> None:
        """
        Set the line width for all view widgets.

        Parameters
        ----------
        v : float
            line width in pixels.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineWidth(v, signal=False)

    def setLineOpacity(self, v: float) -> None:
        """
        Set the line opacity for all view widgets.

        Parameters
        ----------
        v : float
            opacity value (0.0-1.0).
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setLineOpacity(v, signal=False)

    def setFontFamily(self, s: str) -> None:
        """
        Set the font family for text in all view widgets.

        Parameters
        ----------
        s : str
            font family name.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontFamily(s, signal=False)

    def setFontSize(self, s: int) -> None:
        """
        Set the font size for text in all view widgets.

        Parameters
        ----------
        s : int
            font size in points.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontSize(s, signal=False)

    def setFontScale(self, s: float) -> None:
        """
        Set the font scaling factor for all view widgets.

        Parameters
        ----------
        s : float
            font scaling factor.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontScale(s)

    def setFontSizeScale(self, s: tuple[int, float]) -> None:
        """
        Set both the font size and scaling factor for all view widgets.

        Parameters
        ----------
        s : tuple[int, float]
            tuple containing the font size and scaling factor.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontSizeScale(s)

    def setFontProperties(self, s: tuple[str | None, int | None, float | None]) -> None:
        """
        Set multiple font properties (family, size, scale) for all view widgets.

        Parameters
        ----------
        s : tuple[str | None, int | None, float | None]
            tuple containing font family, size, and scale.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.setFontProperties(s)

    # < Revision 05/02/2026
    def setOverlayColorBar(self, index: int = 0):
        if self.isNotEmpty():
            for w in self._views.values():
                w.setOverlayColorbar(index, signal=False)
    # Revision 05/02/2026 >

    # Capture methods

    def saveCapture(self) -> None:
        """
        Save a montage of all visible views as a single image file.
        A file dialog is shown to select the destination and format (supported formats: BMP, JPG, PNG, TIFF).
        """
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
                        i: cython.int
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

    def copyToClipboard(self) -> None:
        """
        Copy a montage of all visible views to the system clipboard.
        """
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
                    i: cython.int
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

    Specialized subclass of the MultiViewWidget base class designed to display three synchronized orthogonal views of
    a SisypheVolume. It displays the axial, coronal, and sagittal planes side-by-side in a 1x3 grid.

    The main features are as follows:

    - Standard orthogonal layout: provides three SliceOverlayViewWidget instances, pre-configured for axial, coronal, and sagittal orientations.
    - Full synchronization: all interactions are seamlessly synchronized across the three views. Changes to the cross-shaped cursor position, zoom level, window/level settings, or any added tools in one view are reflected in the others.
    - Centralized data management: providing a single API to load a primary SisypheVolume, add and manage overlay volumes, and display SisypheMeshCollection instances across all three views at once.
    - Direct view access: offers convenient helper methods (getAxialView, getCoronalView, getSagittalView) for direct access to each individual slice view widget, allowing for fine control when needed.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget

    Creation: 03/04/2022
    Last revision: 20/10/2025
    """

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OrthogonalSliceViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | Non (optional)
            parent widget (default None).
        """
        super().__init__(1, 3, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self) -> None:
        """
        Initializes the 1x3 grid of SliceOverlayViewWidget instances.
        """
        i: cython.int
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

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        i: cython.int
        j: cython.int
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

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed in the three orthogonal view widgets.

        Parameters
        ----------
        volume : SisypheVolume
            volume to display.
        """
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
    def replaceVolume(self, volume: SisypheVolume) -> None:
        """
        Replace the currently displayed SisypheVolume with a new one in all three view widgets.
        The new volume must have the same dimensions as the old one.

        Parameters
        ----------
        volume : SisypheVolume
            new volume to display.
        """
        if self.hasVolume():
            self[0, 0].replaceVolume(volume)
            self[0, 1].replaceVolume(volume)
            self[0, 2].replaceVolume(volume)
    # Revision 18/10/2024

    def removeVolume(self) -> None:
        """
        Remove the currently displayed SisypheVolume from all three view widgets.
        """
        self[0, 0].removeVolume()
        self[0, 1].removeVolume()
        self[0, 2].removeVolume()

    def getVolume(self) -> SisypheVolume:
        """
        Get the currently displayed SisypheVolume.

        Returns
        -------
        SisypheVolume
            currently displayed volume.
        """
        return self[0, 0].getVolume()

    def hasVolume(self) -> bool:
        """
        Check if a SisypheVolume is currently displayed in the views.

        Returns
        -------
        bool
            True if a SisypheVolume is displayed, False otherwise.
        """
        return self[0, 0].hasVolume()

    def addOverlay(self, volume: SisypheVolume, alpha: float = 0.5) -> None:
        """
        Add a SisypheVolume as an overlay to all three orthogonal view widgets.

        Parameters
        ----------
        volume : SisypheVolume
            volume to add as an overlay.
        alpha : float, optional
            opacity of the overlay (0.0-1.0, default 0.5).
        """
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                self[0, 0].addOverlay(volume, alpha)
                self[0, 1].addOverlay(volume, alpha)
                self[0, 2].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self) -> int:
        """
        Get the number of overlays.

        Returns
        -------
        int
            number of overlays.
        """
        return self[0, 0].getOverlayCount()

    def hasOverlay(self) -> bool:
        """
        Check if any overlays are present.

        Returns
        -------
        bool
            True if at least one overlay exists, False otherwise.
        """
        return self[0, 0].hasOverlay()

    def getOverlayIndex(self, o: int | SisypheVolume) -> None:
        """
        Get the index of a specific overlay.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to find, by index or instance.

        Returns
        -------
        int
            index of the overlay.
        """
        return self[0, 0].hasOverlayVolume(o)

    def removeOverlay(self, o: int | SisypheVolume) -> None:
        """
        Remove a specific overlay from all three view widgets.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to remove, by index or instance.
        """
        self[0, 0].removeOverlay(o)
        self[0, 1].removeOverlay(o)
        self[0, 2].removeOverlay(o)

    def removeAllOverlays(self) -> None:
        """
        Remove all overlays from all three view widgets.
        """
        self[0, 0].removeAllOverlays()
        self[0, 1].removeAllOverlays()
        self[0, 2].removeAllOverlays()

    def getOverlayFromIndex(self, index: int) -> None:
        """
        Get an overlay by its index.

        Parameters
        ----------
        index : int
            index of the overlay to retrieve.

        Returns
        -------
        SisypheVolume
            overlay volume at the specified index.
        """
        return self[0, 0].getOverlayFromIndex(index)

    def setMeshCollection(self, meshes: SisypheMeshCollection) -> None:
        """
        Set a SisypheMeshCollection for all three views.

        Parameters
        ----------
        meshes : SisypheMeshCollection
            collection of meshes to display.
        """
        if isinstance(meshes, SisypheMeshCollection):
            self[0, 0].setMeshCollection(meshes)
            self[0, 1].setMeshCollection(meshes)
            self[0, 2].setMeshCollection(meshes)
        else: raise TypeError('parameter type {} is not SisypheMeshCollection.'.format(type(meshes)))

    def getMeshCollection(self) -> SisypheMeshCollection:
        """
        Get the current SisypheMeshCollection.

        Returns
        -------
        SisypheMeshCollection
            current collection of meshes.
        """
        # < Revision 20/10/2025
        # self[0, 0].getMeshCollection()
        return self[0, 0].getMeshCollection()
        # Revision 20/10/2025 >

    # View methods

    def getAxialView(self) -> SliceViewWidget:
        """
        Get the axial SliceViewWidget instance.

        Returns
        -------
        SliceViewWidget
            axial view widget.
        """
        return self[0, 0]

    def getCoronalView(self) -> SliceViewWidget:
        """
        Get the coronal SliceViewWidget instance.

        Returns
        -------
        SliceViewWidget
            coronal view widget.
        """
        return self[0, 1]

    def getSagittalView(self) -> SliceViewWidget:
        """
        Get the sagittal SliceViewWidget instance.

        Returns
        -------
        SliceViewWidget
            sagittal view widget.
        """
        return self[0, 2]


class OrthogonalRegistrationViewWidget(OrthogonalSliceViewWidget):
    """
    OrthogonalSliceViewWidget class

    Description
    ~~~~~~~~~~~

    Specialized subclass of the OrthogonalSliceViewWidget class designed for the visual assessment and manual
    refinement of image coregistration. It arranges three synchronized SliceRegistrationViewWidget instances in the
    standard axial, coronal, and sagittal layout, providing a comprehensive toolset for comparing a fixed and a moving
    volume.

    The main features are as follows:

    - Interactive spyglass tool: a synchronized BoxWidget provides a "spyglass" effect across all three views. The moving volume is displayed exclusively inside the box, while the fixed volume is shown outside.
    - Manual registration tools: it enables interactive rigid transformations (translation and rotation) of the moving volume, allowing users to manually adjust the alignment in real-time. The moveoverlayflag is enabled by default for this purpose.
    - Automatic edge overlay: when adding an overlay (moving) volume, the widget automatically computes a gradient (edge) map of the fixed volume. This edge map is displayed as an additional overlay, providing an additional visual guide for aligning anatomical structures.
    - Synchronization: all registration-related properties—including the spyglass position, overlay transformations, and display modes—are fully synchronized across the three orthogonal views.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalRegistrationViewWidget

    Creation: 03/04/2022
    Last revision: 20/10/2025
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OrthogonalRegistrationViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

    # Private method

    def _initViews(self) -> None:
        """
        Initializes the 1x3 grid of SliceRegistrationViewWidget instances.
        """
        i: cython.int
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

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        super()._initSynchronisationSignalConnect()
        i: cython.int
        j: cython.int
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

    def addOverlay(self, volume: SisypheVolume, alpha: float = 0.5) -> None:
        """
        Add a SisypheVolume as an overlay for registration evaluation.
        This method also computes and adds a gradient (edge) version of the SisypheVolume for display.
        Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            volume to add as an overlay.
        alpha : float, optional
            opacity of the overlay (0.0-1.0, default 0.5).
        """
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

    Specialized subclass of the OrthogonalSliceViewWidget designed for interactively reorienting and reslicing a
    SisypheVolume. It provides a synchronized three-view layout (axial, coronal, and sagittal) with a set of tools for
    applying rigid transformations and/or defining a new field of view (FOV).

    The main features are as follows:

    - Interactive reorientation: allows user to apply translations and rotations to the volume's viewing planes in real-time. The effects of these transformations are visible across all three orthogonal views.
    - Field of view (FOV) manipulation: features a synchronized BoxWidget that visually represents the Field of View. User can interactively translate and resize this box to define a new volume orientation, size, and spacing for reslicing operations.
    - Synchronized reslice cursor: a reslice cursor visually represents the current orientation and intersection of the three planes, providing a consistent frame of reference during manipulation.
    - Customizable tools: offers full control over the appearance of the reslice cursor and the FOV box, including their color, opacity, and line width.
    - Synchronization: all transformations—including translations, rotations, and changes to the FOV box—are seamlessly synchronized across the axial, coronal, and sagittal views.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceViewWidget -> OrthogonalReorientViewWidget

    Creation: 03/04/2022
    Last revision: 20/10/2025
    """

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OrthogonalReorientViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

    # Private methods

    def _initViews(self) -> None:
        """
        Initializes the 1x3 grid of SliceReorientViewWidget instances.
        """
        i: cython.int
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

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        i: cython.int
        j: cython.int
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

    def translationsEnabled(self) -> None:
        """
        Enable translation interaction mode for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].translationsEnabled()

    def translationsDisabled(self) -> None:
        """
        Disnable translation interaction mode for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].translationsDisabled()

    def rotationsEnabled(self) -> None:
        """
        Enable rotation interaction mode for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationsEnabled()

    def rotationsDisabled(self) -> None:
        """
        Disable rotation interaction mode for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationsDisabled()

    def rotationXEnabled(self) -> None:
        """
        Enable rotation around the x-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationXEnabled()

    def rotationXDisabled(self) -> None:
        """
        Disable rotation around the x-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationXDisabled()

    def rotationYEnabled(self) -> None:
        """
        Enable rotation around the y-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationYEnabled()

    def rotationYDisabled(self) -> None:
        """
        Disable rotation around the y-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationYDisabled()

    def rotationZEnabled(self) -> None:
        """
        Enable rotation around the z-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationZEnabled()

    def rotationZDisabled(self) -> None:
        """
        Disable rotation around the z-axis for all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].rotationZDisabled()

    def setFOVBoxVisibility(self, v: bool) -> None:
        """
        Set the visibility of the Field of View (FOV) box in all three reorient view widgets.

        Parameters
        ----------
        v : bool
            True to show the FOV box, False to hide it.
        """
        if isinstance(v, bool):
            i: cython.int
            for i in range(3):
                self[0, i].setFOVBoxVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFOVBoxVisibility(self) -> bool:
        """
        Get the visibility of the Field of View (FOV) box in all three reorient view widgets.

        Returns
        -------
        bool
            True if the FOV box is visible, False otherwise.
        """
        return self[0, 0].getFOVBoxVisibility()

    def setResliceCursorColor(self, rgb: list[float] | tuple[float, float, float]) -> None:
        """
        Set the color of the reslice cursor in all three reorient view widgets.

        Parameters
        ----------
        rgb : list[float] | tuple[float, float, float]
            RGB color values (0.0-1.0).
        """
        i: cython.int
        for i in range(3):
            self[0, i].setResliceCursorColor(rgb)

    def getResliceCursorColor(self) -> tuple[float, float, float]:
        """
        Get the color of the reslice cursor in all three reorient view widgets.

        Returns
        -------
        tuple[float, float, float]
            current RGB color of the reslice cursor.
        """
        return self[0, 0].getResliceCursorColor()

    def setResliceCursorOpacity(self, v: float) -> None:
        """
        Set the opacity of the reslice cursor in all three reorient view widgets.

        Parameters
        ----------
        v : float
            opacity value (0.0-1.0).
        """
        if isinstance(v, float):
            i: cython.int
            for i in range(3):
                self[0, i].setResliceCursorOpacity(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorOpacity(self) -> float:
        """
        Get the opacity of the reslice cursor in all three reorient view widgets.

        Returns
        -------
        float
            current opacity of the reslice cursor.
        """
        return self[0, 0].getResliceCursorOpacity()

    def setResliceCursorLineWidth(self, v: float) -> None:
        """
        Set the line width of the reslice cursor in all three reorient view widgets.

        Parameters
        ----------
        v : float
            line width in pixels.
        """
        if isinstance(v, float):
            i: cython.int
            for i in range(3):
                self[0, i].setResliceCursorLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getResliceCursorLineWidth(self) -> float:
        """
        Get the line width of the reslice cursor in all three reorient view widgets.

        Returns
        -------
        float
            current line width of the reslice cursor.
        """
        return self[0, 0].getResliceCursorLineWidth()

    def setFovBoxColor(self, rgb: list[float] | tuple[float, float, float]) -> None:
        """
        Set the color of the FOV box in all three reorient view widgets.

        Parameters
        ----------
        rgb : list[float] | tuple[float, float, float]
            RGB color values (0.0-1.0).
        """
        i: cython.int
        for i in range(3):
            self[0, i].setFovBoxColor(rgb)

    def getFovBoxColor(self) -> tuple[float, float, float]:
        """
        Get the color of the FOV box in all three reorient view widgets.

        Returns
        -------
        tuple[float, float, float]
            current RGB color of the FOV box.
        """
        return self[0, 0].getFovBoxColor()

    def setFovBoxOpacity(self, v: float) -> None:
        """
        Set the opacity of the FOV box in all three reorient view widgets.

        Parameters
        ----------
        v : float
            opacity value (0.0-1.0).

        Raises
        ------
        TypeError
            If the `v` parameter is not a float.
        """
        if isinstance(v, float):
            i: cython.int
            for i in range(3):
                self[0, i].setFovBoxOpacity(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxOpacity(self) -> float:
        """
        Get the opacity of the FOV box in all three reorient view widgets.

        Returns
        -------
        float
            current opacity of the FOV box.
        """
        return self[0, 0].getFovBoxOpacity()

    def setFovBoxLineWidth(self, v: float) -> None:
        """
        Set the line width of the FOV box in all three reorient view widgets.

        Parameters
        ----------
        v : float
            line width in pixels.

        Raises
        ------
        TypeError
            If the `v` parameter is not a float.
        """
        if isinstance(v, float):
            i: cython.int
            for i in range(3):
                self[0, i].setFovBoxLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getFovBoxLineWidth(self) -> float:
        """
        Get the line width of the FOV box in all three reorient view widgets.

        Returns
        -------
        float
            current line width of the FOV box.
        """
        return self[0, 0].getFovBoxLineWidth()

    def setSliceNavigationEnabled(self) -> None:
        """
        Enable slice navigation (scrolling) in all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].setSliceNavigationEnabled()

    def setSliceNavigationDisabled(self) -> None:
        """
        Disable slice navigation (scrolling) in all three reorient view widgets.
        """
        i: cython.int
        for i in range(3):
            self[0, i].setSliceNavigationDisabled()

    def isSliceNavigationEnabled(self) -> None:
        """
        Check if slice navigation is enabled.

        Returns
        -------
        bool
            True if slice navigation is enabled, False otherwise.
        """
        return self[0, 0].isSliceNavigationEnabled


class OrthogonalSliceVolumeViewWidget(MultiViewWidget):
    """
    OrthogonalSliceVolumeViewWidget class

    Description
    ~~~~~~~~~~~

    Specialized subclass of the MultiViewWidget base class, which is a composite widget that provides an integrated 2D
    and 3D visualization environment. It arranges four synchronized viewports in a 2x2 grid, combining three orthogonal
    slice views (axial, coronal, and sagittal) with a full 3D volume rendering view.

    The main features are as follows:

    - Combined 2D/3D layout: displays a VolumeViewWidget alongside three SliceOverlayViewWidget instances.
    - Synchronization: all views are tightly coupled. The 3D cursor position is linked across all four views, and interactions like zooming are synchronized between the 2D slice views.
    - Unified data management: a single API for loading a primary SisypheVolume, which is simultaneously rendered in the 3D view and displayed in the three slice views. It also supports adding overlay volumes to the 2D views.
    - Integrated mesh and tractography Display: manages and displays SisypheMeshCollection (3D models) across all four views and SisypheTractCollection (streamlines) within the 3D volume view.
    - Direct view access: affers helper methods (getVolumeView, getAxialView, getCoronalView, getSagittalView) for direct access and control over each individual viewport.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget

    Creation: 03/04/2022
    Last revision: 20/10/2025
    """

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OrthogonalSliceVolumeViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(2, 2, parent)
        self._initViews()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self) -> None:
        """
        Initializes the 2x2 grid of 3 SliceTrajectoryViewWidget instances and 1 VolumeViewWidget instance.
        """
        meshes = None
        i: cython.int
        j: cython.int
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

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        i: cython.int
        j: cython.int
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

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed in all four view widgets (3 slice, 1 volume rendering).

        Parameters
        ----------
        volume : SisypheVolume
            volume to display.
        """
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
    def replaceVolume(self, volume: SisypheVolume) -> None:
        """
        Replace the currently displayed SisypheVolume with a new one in all four view widgets.
        The new volume must have the same dimensions as the old one.

        Parameters
        ----------
        volume : SisypheVolume
            new volume to display.
        """
        if self.hasVolume():
            self[0, 0].replaceVolume(volume)
            self[0, 1].replaceVolume(volume)
            self[1, 0].replaceVolume(volume)
            self[1, 1].replaceVolume(volume)
    # Revision 18/10/2024

    def removeVolume(self) -> None:
        """
        Remove the currently displayed SisypheVolume from all four view widgets.
        """
        self[0, 0].removeVolume()
        self[0, 1].removeVolume()
        self[1, 0].removeVolume()
        self[1, 1].removeVolume()

    def getVolume(self) -> SisypheVolume:
        """
        Get the currently displayed SisypheVolume.

        Returns
        -------
        SisypheVolume
            currently displayed volume.
        """
        return self[0, 0].getVolume()

    def hasVolume(self) -> bool:
        """
        Check if a volume is currently displayed.

        Returns
        -------
        bool
            True if a volume is displayed, False otherwise.
        """
        return self[0, 0].hasVolume()

    # Overlay methods

    def addOverlay(self, volume: SisypheVolume, alpha: float = 0.5) -> None:
        """
        Add a SisypheVolume as an overlay to the three slice view widgets.

        Parameters
        ----------
        volume : SisypheVolume
            volume to add as an overlay.
        alpha : float, optional
            opacity of the overlay (0.0-1.0, default 0.5).
        """
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                self[0, 1].addOverlay(volume, alpha)
                self[1, 0].addOverlay(volume, alpha)
                self[1, 1].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self) -> int:
        """
        Get the number of overlays in the slice views.

        Returns
        -------
        int
            number of overlays.
        """
        return self[0, 1].getOverlayCount()

    def hasOverlay(self) -> bool:
        """
        Check if any overlays are present in the slice views.

        Returns
        -------
        bool
            True if at least one overlay exists, False otherwise.
        """
        return self[0, 1].hasOverlay()

    def getOverlayIndex(self, o: int | SisypheVolume) -> int:
        """
        Get the index of a specific overlay.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to find, by index or instance.

        Returns
        -------
        int
            index of the overlay.
        """
        return self[0, 1].hasOverlayVolume(o)

    def removeOverlay(self, o: int | SisypheVolume) -> None:
        """
        Remove a specific overlay from the three slice view widgets.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to remove, by index or instance.
        """
        self[0, 1].removeOverlay(o)
        self[1, 0].removeOverlay(o)
        self[1, 1].removeOverlay(o)

    def removeAllOverlays(self) -> None:
        """
        Remove all overlays from the three slice view widgets.
        """
        self[0, 1].removeAllOverlays()
        self[1, 0].removeAllOverlays()
        self[1, 1].removeAllOverlays()

    def getOverlayFromIndex(self, index: int) -> SisypheVolume:
        """
        Get an overlay by its index from the slice view widgets.

        Parameters
        ----------
        index : int
            index of the overlay to retrieve.

        Returns
        -------
        SisypheVolume
            overlay volume at the specified index.
        """
        return self[0, 1].getOverlayFromIndex(index)

    # Mesh methods

    # < Revision 23/03/2025
    def removeAllMeshes(self) -> None:
        """
        Remove all SisypheMesh instances from all view widgets.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.removeAllMeshes()
    # Revision 23/03/2025 >

    # < Revision 23/03/2025
    def removeMesh(self, mesh: SisypheMesh) -> None:
        """
        Remove a specific SisypheMesh instance from all view widgets.

        Parameters
        ----------
        mesh : SisypheMesh
            mesh instance to remove.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                w.removeMesh(mesh)
    # Revision 23/03/2025 >

    # < Revision 27/03/2025
    def addMesh(self, mesh: SisypheMesh)-> None:
        """
        Add a SisypheMesh instance to all view widgets.

        Parameters
        ----------
        mesh : SisypheMesh
            mesh instance to add.
        """
        for w in self._views.values():
            w.addMesh(mesh)
    # Revision 27/03/2025 >

    # Tracts methods

    def getTractCollection(self) -> SisypheTractCollection:
        """
        Get the SisypheTractCollection instance (streamlines collection) from the 3D volume view widget.

        Returns
        -------
        SisypheTractCollection
            current streamlines collection.
        """
        return self[0, 0].getTractCollection()

    def setTractCollection(self, tracts: SisypheTractCollection) -> None:
        """
        Set the SisypheTractCollection instance (streamlines collection) for the 3D volume view widget.

        Parameters
        ----------
        tracts : SisypheTractCollection
            streamlines collection to display.
        """
        self[0, 0].setTractCollection(tracts)

    def hasTracts(self) -> bool:
        """
        Check if there are any streamlines (tracts) in the collection of the 3D volume view widget

        Returns
        -------
        bool
            True if streamlines (tracts) are present, False otherwise.
        """
        return self[0, 0].hasTracts()

    # View methods

    def getVolumeView(self) -> VolumeViewWidget:
        """
        Get the 3D volume view widget.

        Returns
        -------
        VolumeViewWidget
            3D volume view widget.
        """
        return self[0, 0]

    def getAxialView(self) -> SliceViewWidget:
        """
        Get the axial slice view widget.

        Returns
        -------
        SliceViewWidget
            axial view widget.
        """
        return self[0, 1]

    def getCoronalView(self) -> SliceViewWidget:
        """
        Get the coronal slice view widget.

        Returns
        -------
        SliceViewWidget
            coronal view widget.
        """
        return self[1, 0]

    def getSagittalView(self) -> SliceViewWidget:
        """
        Get the sagittal slice view widget.

        Returns
        -------
        SliceViewWidget
            sagittal view widget.
        """
        return self[1, 1]


class OrthogonalTrajectoryViewWidget(OrthogonalSliceVolumeViewWidget):
    """
    OrthogonalTrajectoryViewWidget class

    Description
    ~~~~~~~~~~~

    Advanced subclass of the OrthogonalSliceVolumeViewWidget class that introduces trajectory-based navigation and
    visualization.It replaces the standard 2D slice viewers with SliceTrajectoryViewWidget instances, enabling the
    display of slices oriented along arbitrary paths within the SisypheVolume.

    The main features are as follows:

    - Trajectory-based slicing: the three 2D views (axial, coronal, and sagittal) can be reoriented to display slices that are perpendicular to a user-defined trajectory, offering non-orthogonal views of the data.
    - Dynamic camera alignment: ability to align the 2D slice views with the camera's orientation in the 3D viewport. This creates a real-time "oblique slicer" that updates as the user rotates and navigates the 3D scene.
    - Multiple alignment modes, trajectories can be aligned in several ways: to the 3D view's camera, to specific anatomical landmarks (e.g. AC-PC line), to other interactive tools or vectors, to the default axial, coronal, or sagittal planes.
    - Synchronization: in addition to inheriting all synchronization from its parent (cursor position, zoom, etc.), this widget ensures that all trajectory-specific properties—such as alignment mode, slab thickness, and step size—are seamlessly synchronized across all slice views and the 3D view.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> OrthogonalSliceVolumeViewWidget -> OrthogonalTrajectoryViewWidget

    Creation: 03/04/2022
    Last Revision: 20/10/2025
    """

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        OrthogonalTrajectoryViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

    # Private methods

    def _initViews(self) -> None:
        """
        Initializes the 2x2 grid of 3 SliceTrajectoryViewWidget instances and 1 VolumeViewWidget instance.
        """
        meshes = None
        i: cython.int
        j: cython.int
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

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        super()._initSynchronisationSignalConnect()
        i: cython.int
        j: cython.int
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

    def popupAlignmentEnabled(self) -> None:
        """
        Enable the 'Alignment' submenu in the popup menu for all trajectory slice view widgets.
        """
        for w in self._views.values():
            if isinstance(w, SliceTrajectoryViewWidget):
                w.popupAlignmentEnabled()

    def popupAlignmentDisabled(self) -> None:
        """
        Disable the 'Alignment' submenu in the popup menu for all trajectory slice view widgets.
        """
        for w in self._views.values():
            if isinstance(w, SliceTrajectoryViewWidget):
                w.popupAlignmentDisabled()

    # Public synchronization event methods

    def synchroniseCameraChanged(self, obj: QWidget):
        """
        Synchronizes the trajectory alignment when the 3D view camera changes.
        This is called if any slice view widget is in camera-aligned mode.

        Parameters
        ----------
        obj : QWidget
            VolumeViewWidget that emitted the signal.
        """
        view = self.getFirstSliceViewWidget()
        if view.isCameraAligned(): self.synchroniseTrajectoryCameraAligned(obj)

    # noinspection PyUnusedLocal
    def synchroniseTrajectoryCameraAligned(self, obj: QWidget):
        """
        Align all slice view widgets to the camera of the 3D view.
        This is typically triggered when one slice view widget aligns its trajectory to the camera.

        Parameters
        ----------
        obj : QWidget
            view widget that emitted the signal.
        """
        camera = self.getFirstVolumeViewWidget().getRenderer().GetActiveCamera()
        views = self.getSliceViewWidgets()
        for view in views:
            view.setTrajectoryFromCamera(camera, signal=False)


class GridViewWidget(MultiViewWidget):
    """
    GridViewWidget class

    Description
    ~~~~~~~~~~~

    Specialized subclass of the MultiViewWidget class designed for the simultaneous display of multiple slice views,
    with a primary focus on synchronized Region of Interest (ROI) editing. It arranges up to nine SliceROIViewWidget
    instances in a configurable grid. This widget serves as the base class for more specialized
    MultiSliceGridViewWidget and SynchronisedGridViewWidget classes.

    The main features are as follows:

    - Unified volume display: the widget is designed to display a single SisypheVolume, with each view widget showing a slice from that volume. It provides a single API to set or replace the volume for all views simultaneously.
    - Integrated ROI editing: populates a 3x3 grid with SliceROIViewWidget instances that all share the same SisypheROICollection and SisypheROIDraw objects. This architecture ensures that any ROI creation, modification, or selection in one view is automatically reflected in all others.
    - Dynamic grid layout: manages a 3x3 grid internally, it provides a user-friendly popup menu to dynamically change the number of visible views. This allows user to adjust the layout to focus on a specific number of slices as needed.
    - Synchronization: it offers centralized control to set the anatomical orientation (axial, coronal, or sagittal) for all visible views at once. Standard navigation controls like zoom and cursor position are also fully synchronized across the grid.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget

    Creation: 03/04/2022
    Last revision: 26/02/2026
    """

    # Special method

    """
    Private attributes

    _menuNumberOfVisibleViews   QMenu
    """

    def __init__(self,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent: QWidget | None = None) -> None:
        """
        GridViewWidget instance constructor.

        Parameters
        ----------
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be shared among the view widgets (default None).
        draw : SisypheROIDraw | None (optional)
            drawing utility instance to be shared among the view widgets (default None).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(3, 3, parent)

        self._menuNumberOfVisibleViews = None

        self._initViews(rois, draw)
        self._initActions()
        self._initSynchronisationSignalConnect()

    # Private methods

    def _initViews(self, rois: SisypheROICollection | None, draw: SisypheROIDraw | None) -> None:
        """
        Initializes the 3x3 grid of SliceROIViewWidget instances.
        """
        i: cython.int
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

    def _initActions(self) -> None:
        """
        Initializes specific QAction instances for each view widget and connects them to their respective slots.

        - orientation ('axial', 'coronal', 'sagittal')
        - number of views ('1x1', '1x2', '1x3', '2x2', '2x3', '3x3')
        """
        i: cython.int
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
            # noinspection PyUnresolvedReferences
            menuNumberOfVisibleViews.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyUnresolvedReferences
            menuNumberOfVisibleViews.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyUnresolvedReferences
            menuNumberOfVisibleViews.setAttribute(Qt.WA_TranslucentBackground, True)
            menuNumberOfVisibleViews.addAction(action['11'])
            menuNumberOfVisibleViews.addAction(action['12'])
            menuNumberOfVisibleViews.addAction(action['13'])
            menuNumberOfVisibleViews.addAction(action['22'])
            menuNumberOfVisibleViews.addAction(action['23'])
            menuNumberOfVisibleViews.addAction(action['33'])
            popup.insertMenu(popup.actions()[2], menuNumberOfVisibleViews)
            if i == 0: self._menuNumberOfVisibleViews = menuNumberOfVisibleViews

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        i: cython.int
        j: cython.int
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

    def updateROIName(self, old: str, name: str) -> None:
        """
        Update the name of a ROI across all view widgets in the grid.

        Parameters
        ----------
        old : str
            old name of the ROI.
        name : str
            new name for the ROI.
        """
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, SliceROIViewWidget):
                    if w.hasROI(): w.updateROIName(old, name)

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the SisypheVolume for all view widgets in the grid.

        Parameters
        ----------
        volume : SisypheVolume
            volume to display.
        """
        if isinstance(volume, SisypheVolume):
            i: cython.int
            for i in range(0, 9):
                self[i // 3, i % 3].setVolume(volume)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # < Revision 14/10/2024
    # add replaceVolume method
    def replaceVolume(self, volume: SisypheVolume) -> None:
        """
        Replace the currently displayed SisypheVolume with a new one in all view widgets.
        The new volume must have the same dimensions as the old one.

        Parameters
        ----------
        volume : SisypheVolume
            new volume to display.
        """
        if self.hasVolume():
            i: cython.int
            for i in range(0, 9):
                self[i // 3, i % 3].replaceVolume(volume)
    # Revision 14/10/2024 >

    def removeVolume(self) -> None:
        """
        Remove the currently displayed SisypheVolume from all view widgets in the grid.
        """
        i: cython.int
        for i in range(0, 9):
            self[i // 3, i % 3].removeVolume()

    def getVolume(self) -> SisypheVolume:
        """
        Get the SisypheVolume displayed in the grid.

        Returns
        -------
        SisypheVolume
            currently displayed volume.
        """
        return self[0, 0].getVolume()

    def hasVolume(self) -> bool:
        """
        Check if a SisypheVolume is displayed in the grid.

        Returns
        -------
        bool
            True if a volume is displayed False otherwise.
        """
        return self[0, 0].hasVolume()

    # < Revision 26/02/2026
    # add setSamModel method
    def setSamModel(self, model: SegmentAnything) -> None:
        """
        Set the SegmentAnything pre-trained model attribute.

        Parameters
        ----------
        model : SegmentAnything
            Segment Anything (MedSAM) pre-trained model
        """
        i: cython.int
        for i in range(0, 9):
            self[i // 3, i % 3].setSamModel(model)
    # Revision 26/02/2026 >

    # < Revision 26/02/2026
    # add getSamModel method
    def getSamModel(self) -> SegmentAnything:
        """
        Get the SegmentAnything pre-trained model attribute.

        Returns
        -------
        SegmentAnything
            Segment Anything (MedSAM) pre-trained model
        """
        return self[0, 0].getSamModel()
    # Revision 26/02/2026 >

    # < Revision 26/02/2026
    # add hasSamModel method
    def hasSamModel(self) -> bool:
        """
        Check if the SegmentAnything pre-trained model attribute is defined.

        Returns
        -------
        bool
            True if the SegmentAnything pre-trained model attribute is defined False otherwise.
        """
        return self[0, 0].getSamModel() is not None
    # Revision 26/02/2026 >

    def setNumberOfVisibleViews(self, r: int, c: int) -> None:
        """
        Set the number of visible view widgets by specifying the grid arrangement (rows and columns).

        Parameters
        ----------
        r : int
            number of rows to display.
        c : int
            number of columns to display.
        """
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
        i: cython.int
        for i in range(9):
            a = i // 3
            b = i % 3
            self[a, b].getAction()[k].setChecked(True)
            if n > 0:
                # < Revision 17/11/2025
                # no synchronization if hidden view, used to speed up display
                self[a, b].setVisible(i < n)
                self[a, b].setSynchronisation(i < n)
                # Revision 17/11/2025 >
            else:
                # < Revision 17/11/2025
                # no synchronization if hidden view, used to speed up display
                self[a, b].setVisible(i in [0, 1, 3, 4])
                self[a, b].setSynchronisation(i in [0, 1, 3, 4])
                # Revision 17/11/2025 >
            self.setRows(r)
            self.setCols(c)

    def getViewsArrangement(self) -> tuple[int, int]:
        """
        Get the current grid arrangement (rows, columns) of visible view widgets.

        Returns
        -------
        tuple[int, int]
            (rows, columns) of the visible grid.
        """
        action = self.getFirstSliceViewWidget().getAction()
        if action['11'].isChecked(): r = (1, 1)
        elif action['12'].isChecked(): r = (1, 2)
        elif action['13'].isChecked(): r = (1, 3)
        elif action['22'].isChecked(): r = (2, 2)
        elif action['23'].isChecked(): r = (2, 3)
        else: r = (3, 3)
        return r

    def setAxialOrientation(self) -> None:
        """
        Set the orientation of all view widgets in the grid to axial.
        """
        self.setOrientation(0)

    def setCoronalOrientation(self) -> None:
        """
        Set the orientation of all view widgets in the grid to coronal.
        """
        self.setOrientation(1)

    def setSagittalOrientation(self) -> None:
        """
        Set the orientation of all view widgets in the grid to sagittal.
        """
        self.setOrientation(2)

    def setOrientation(self, orient: int) -> None:
        """
        Set the orientation for all view widgets in the grid.

        Parameters
        ----------
        orient : int
            orientation index (0 for axial, 1 for coronal, 2 for sagittal).
        """
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, AbstractViewWidget):
                    if w.hasVolume(): w.setOrientation(orient)

    def getOrientation(self) -> int:
        """
        Get the orientation in the view widgets in the grid.

        Returns
        -------
        int
            current orientation index.
        """
        return self._views[(0, 0)].getOrientation()

    def getOrientationAsString(self) -> str:
        """
        Get the orientation in the view widgets as a string.

        Returns
        -------
        str
            current orientation ('axial', 'coronal', or 'sagittal').
        """
        return self._views[(0, 0)].getOrientationAsString()

    def getPopupMenuNumberOfVisibleViews(self) -> QMenu:
        """
        Get the popup submenu for changing the number of visible views.

        Returns
        -------
        QMenu
            'Number of views' submenu.
        """
        return self._menuNumberOfVisibleViews

    def popupMenuOrientationEnabled(self) -> None:
        """
        Enable the 'Orientation' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupOrientationEnabled()

    def popupMenuOrientationDisabled(self) -> None:
        """
        Disable the 'Orientation' submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupOrientationDisabled()

    def popupMenuNumberOfVisibleViewsShow(self) -> None:
        """
        Show the 'Number of views' submenu in the popup menu for all view widgets.
        """
        i: cython.int
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.getPopup().actions()[2].setVisible(True)

    def popupMenuNumberOfVisibleViewsHide(self) -> None:
        """
        Hide the 'Number of views' submenu in the popup menu for all view widgets.
        """
        i: cython.int
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # noinspection PyUnresolvedReferences
            w.getPopup().actions()[2].setVisible(False)

    def popupMenuROIEnabled(self) -> None:
        """
        Enable the 'ROI' tools submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupROIEnabled()

    def popupMenuROIDisabled(self) -> None:
        """
        Disable the 'ROI' tools submenu in the popup menu for all view widgets.
        """
        for w in self._views.values():
            w.popupROIDisabled()


class MultiSliceGridViewWidget(GridViewWidget):
    """
    MultiSliceGridViewWidget class

    Description
    ~~~~~~~~~~~

    Specialized subclass of the GridViewWidget class designed for the simultaneous visualization of multiple,
    consecutive slices from a single SisypheVolume. It arranges up to nine SliceROIViewWidget instances in a grid,
    where each view automatically displays a slice adjacent to its neighbors.

    The main features are as follows:

    - Consecutive slice display: each view in the grid is automatically assigned an offset, allowing the widget to display a sequence of adjacent slices. This provides a "filmstrip" style view, ideal for inspecting a region of interest across several slices at once.
    - Full ROI integration: inheriting from GridViewWidget, it offers fully synchronized ROI editing capabilities. All views share the same ROI collection, enabling users to draw and modify a single 3D ROI across multiple 2D slices seamlessly.
    - Overlay functionality: supports the addition of one or more overlay volumes, which are displayed consistently across all slice views.
    - Synchronization: all navigation controls, including zoom, pan, and cursor position, are synchronized across all visible views. The cursor is typically shown only on the first view to provide a clear reference point.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget -> MultiSliceGridViewWidget

    Creation: 03/04/2022
    Last revision: 20/10/2025
    """

    # Special method

    def __init__(self,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent: QWidget | None = None) -> None:
        """
        MultiSliceGridViewWidget instance constructor.

        Parameters
        ----------
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be shared among the view widgets (default None).
        draw : SisypheROIDraw | Noneb(optional)
            drawing utility instance to be shared among the view widgets (default None).
        parent : QWidget | None (optional)
            parent widget (default None).
        """

        super().__init__(rois, draw, parent)
        i: cython.int
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

    def getFirstVisibleView(self) -> AbstractViewWidget | None:
        """
        Get the first visible view widget in the grid.

        Returns
        -------
        AbstractViewWidget | None
            first visible view widget, or None if no views are visible.
        """
        i: cython.int
        for i in range(9):
            r = i // 3
            c = i % 3
            view = self[r, c]
            if view.isVisible():
                return view
        return None

    def getLastVisibleView(self) -> AbstractViewWidget | None:
        """
        Get the last visible view widget in the grid.

        Returns
        -------
        AbstractViewWidget | None
            last visible view widget, or None if no views are visible.
        """
        i: cython.int
        for i in range(8, -1, -1):
            r = i // 3
            c = i % 3
            view = self[r, c]
            if view.isVisible():
                return view
        return None

    def getFirstVisibleSliceIndex(self) -> int | None:
        """
        Get the slice index of the first visible view widget.

        Returns
        -------
        int | None
            slice index, or None if no view widget is visible.
        """
        view = self.getFirstVisibleView()
        if isinstance(view, SliceROIViewWidget): return view.getSliceIndex()
        else: return None

    def getLastVisibleSliceIndex(self) -> int | None:
        """
        Get the slice index of the last visible view.

        Returns
        -------
        int | None
            slice index, or None if no view widget is visible.
        """
        view = self.getLastVisibleView()
        if isinstance(view, SliceROIViewWidget): return view.getSliceIndex()
        else: return None

    def addOverlay(self, volume: SisypheVolume, alpha: float = 0.5) -> None:
        """
        Add a SisypheVolume as an overlay to all view widgets in the grid.

        Parameters
        ----------
        volume : SisypheVolume
            volume to add as an overlay.
        alpha : float (optional)
            opacity of the overlay (0.0-1.0, default 0.5).
        """
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                i: cython.int
                for i in range(0, 9):
                    self[i // 3, i % 3].addOverlay(volume, alpha)
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getOverlayCount(self) -> int:
        """
        Get the number of overlays.

        Returns
        -------
        int
            number of overlays.
        """
        return self[0, 0].getOverlayCount()()

    def hasOverlay(self) -> bool:
        """
        Check if any overlays are present.

        Returns
        -------
        bool
            True if at least one overlay exists, False otherwise.
        """
        return self[0, 0].hasOverlay()

    def getOverlayIndex(self, o: int | SisypheVolume) -> int:
        """
        Get the index of a specific overlay.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to find, by index or instance.

        Returns
        -------
        int
            index of the overlay.
        """
        return self[0, 0].getOverlayIndex(o)

    def removeOverlay(self, o:  int | SisypheVolume) -> None:
        """
        Remove a specific overlay from all view widgets.

        Parameters
        ----------
        o : int | SisypheVolume
            overlay to remove, by index or instance.
        """
        i: cython.int
        for i in range(0, 9):
            self[i // 3, i % 3].removeOverlay(o)

    def removeAllOverlays(self) -> None:
        """
        Remove all overlays from all view widgets.
        """
        i: cython.int
        for i in range(0, 9):
            self[i // 3, i % 3].removeAllOverlays()

    def getOverlayFromIndex(self, index: int) -> SisypheVolume:
        """
        Get an overlay by its index.

        Parameters
        ----------
        index : int
            index of the overlay to retrieve.

        Returns
        -------
        SisypheVolume
            overlay volume at the specified index.
        """
        return self[0, 0].getOverlayFromIndex(index)


class SynchronisedGridViewWidget(GridViewWidget):
    """
    SynchronisedGridViewWidget class

    Description
    ~~~~~~~~~~~

    Specialized subclass of the GridViewWidget class designed for the side-by-side comparison of multiple, distinct
    SisypheVolume instances within a single, synchronized environment.

    The main features are as follows:

    - Multi-Volume comparison: it operates on a reference-plus-synchronized model. A primary reference volume is set, and each additional SisypheVolume is added as a "synchronized" volume, displayed in its own dedicated view within the grid. This allows for direct visual comparison of corresponding slices from different datasets.
    - Dynamic grid layout: the number of visible views and the grid's dimensions automatically adapt as synchronized volumes are added or removed, ensuring an optimal layout for comparison.
    - Unified ROI editing: as a GridViewWidget subclass, it provides fully integrated and synchronized ROI tools. Any ROI created or modified in one view is instantly updated across all other views, allowing for consistent analysis across different volumes.
    - Synchronization: all interactions, including cursor movement, zoom/pan, and slice/orientation changes, are mirrored across all views.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget -> SynchronisedGridViewWidget

    Creation: 03/04/2022
    Last revision: 10/03/2026
    """

    # Special method

    """
    Private attributes

    _nbv    int, volume count
    """

    def __init__(self,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent: QWidget | None = None) -> None:
        """
        SynchronisedGridViewWidget instance constructor.

        Parameters
        ----------
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be shared among the view widgets (default None).
        draw : SisypheROIDraw | None (optional)
            drawing utility instance to be shared among the view widgets (default None).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(rois, draw, parent)
        i: cython.int
        for i in range(9):
            # noinspection PyNoneFunctionAssignment
            w = self.getViewWidgetAt(i // 3, i % 3)
            # < Revision 10/03/2026
            w.setOverlayColorbarAvailability(False, signal=False)
            # Revision 10/03/2026 >
            # noinspection PyUnresolvedReferences
            action = w.getAction()
            action['expand'].setVisible(True)

        self.popupMenuNumberOfVisibleViewsHide()

    # Private methods

    def _updateVisibleViews(self) -> None:
        """
        Updates grid geometry based on the number of visible view widgets.

        - 1 visible view widget: grid 1 x 1
        - 2 visible view widgets: grid 1 x 2
        - 3 visible view widgets: grid 1 x 3
        - 4 visible view widgets: grid 2 x 2
        - 5, 6 visible view widgets: grid 2 x 3
        - > 6 visible view widgets: grid 3 x 3
        """
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
            i: cython.int
            r: cython.int
            c: cython.int
            for i in range(nbv):
                for r in range(self.getRows()):
                    for c in range(self.getCols()):
                        n = r * self.getCols() + c
                        view = self[r, c]
                        if n <= nbv:
                            view.setVisible(True)
                            if n > 0: view.setOverlayColorbar(n - 1, signal=False)
                            view.setOverlayVisibility(i, i == n - 1, signal=False)
                        elif n > nbv: view.setVisible(False)
        # Revision 27/05/2025 >

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the reference SisypheVolume for the grid.
        This volume is displayed in the first view widget, and other views are configured to show synchronized volumes.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            reference SisypheVolume to display.
        """
        super().setVolume(volume)
        i: cython.int
        for i in range(9):
            r = i // 3
            c = i % 3
            self[r, c].setVolumeVisibility(i == 0, signal=False)
        # Reference volume is in the first view
        self._updateVisibleViews()

    def addSynchronisedVolume(self, volume: SisypheVolume) -> None:
        """
        Add a synchronized SisypheVolume to the grid.
        Each synchronized volume is displayed in a separate view widget, overlaid on the reference volume.

        Parameters
        ----------
        volume : SisypheVolume
            volume to add for synchronized display.
        """
        if isinstance(volume, SisypheVolume):
            if self.hasVolume():
                i: cython.int
                for i in range(0, 9):
                    self[i // 3, i % 3].addOverlay(volume, 1.0)
                self._updateVisibleViews()
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeSynchronisedVolume(self, v: SisypheVolume) -> None:
        """
        Remove a synchronized SisypheVolume from the grid.

        Parameters
        ----------
        v : SisypheVolume
            synchronized volume to remove.
        """
        if isinstance(v, SisypheVolume):
            if self.hasVolume():
                i: cython.int
                for i in range(0, 9):
                    self[i // 3, i % 3].removeOverlay(v)
                self._updateVisibleViews()
            else: raise ValueError('reference volume must be set before overlay.')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def removeAllSynchronisedVolumes(self) -> None:
        """
        Remove all synchronized SisypheVolume instance from the grid, leaving only the reference volume.
        """
        if self.hasVolume():
            if self.hasOverlay():
                i: cython.int
                for i in range(0, 9):
                    self[i // 3, i % 3].removeAllOverlays()
                self._updateVisibleViews()

    def getSynchronisedVolumeCount(self) -> int:
        """
        Get the number of synchronized volumes.

        Returns
        -------
        int
            number of synchronized volumes.
        """
        return self[0, 0].getOverlayCount()()

    def hasSynchronisedVolume(self) -> bool:
        """
        Check if any synchronized volumes are present.

        Returns
        -------
        bool
            True if at least one synchronized volume exists, False otherwise.
        """
        return self[0, 0].hasOverlay()

    def getSynchronisedVolumeIndex(self, o: int | SisypheVolume):
        """
        Get the index of a specific synchronized volume.

        Parameters
        ----------
        o : int | SisypheVolume
            synchronized volume to find, by index or instance.

        Returns
        -------
        int
            index of the synchronized volume.
        """
        return self[0, 0].getOverlayIndex(o)

    def getSynchronisedVolumeFromIndex(self, index: int) -> SisypheVolume:
        """
        Get a synchronized volume by its index.

        Parameters
        ----------
        index : int
            index of the synchronized volume to retrieve.

        Returns
        -------
        SisypheVolume
            synchronized volume at the specified index.
        """
        return self[0, 0].getOverlayFromIndex(index)

    #  Public method aliases

    addOverlay = addSynchronisedVolume
    removeOverlay = removeSynchronisedVolume
    removeAllOverlays = removeAllSynchronisedVolumes
    hasOverlay = hasSynchronisedVolume
    getOverlayIndex = getSynchronisedVolumeIndex
    getOverlayFromIndex = getSynchronisedVolumeFromIndex
