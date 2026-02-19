"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, Scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, Visualization, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import sys

from os import getcwd
from os import chdir
from os import remove

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import splitext

from matplotlib.figure import Figure
# noinspection PyUnresolvedReferences
from matplotlib.figure import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from numpy import array

from pandas import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheConstants import addSuffixToFilename
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
from Sisyphe.widgets.multiViewWidgets import MultiViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from matplotlib.backend_bases import PickEvent

_all__ = ['MultiComponentViewWidget',
          'IconBarMultiComponentViewWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> MultiViewWidget -> GridViewWidget -> MultiComponentViewWidget
              -> IconBarWidget -> IconBarMultiComponentViewWidget
"""


class MultiComponentViewWidget(MultiViewWidget):
    """
    MultiComponentViewWidget class

    Description
    ~~~~~~~~~~~

    This is a specialized subclass of the MultiViewWidget class, which provides an integrated environment for the
    visualization and of multi-component (e.g., 4D) Sisyphe volume. It combines a grid of 2D slice views with an
    interactive 1D signal chart, for exploring datasets like time series.

    The main features are as follows:

    - Multi-Component grid display: displays individual components of a SisypheVolume across a configurable grid (up to 3x3) of SliceViewWidget instances. User can navigate through the components, which are displayed sequentially in the grid.
    - Interactive signal chart: a Matplotlib chart located below the grid plots the signal intensity profile for the data. Key chart features include:

        - a dynamic curve that updates in real-time to show the signal from the voxel at the cross-shaped cursor's position.
        - a static curve representing the mean signal across the entire volume.
        - the ability to "pin" and persist the current voxel's curve on the chart for comparison.
        - a highlighted span indicating the range of components currently visible in the 2D grid.

    - Bidirectional interaction: the link between the grid and chart is bidirectional. Moving the cursor in a slice view updates the chart, and clicking on a saved voxel curve in the chart moves the cursor to that voxel's location.
    - Export Capabilities: offers extensive options for exporting both the visual chart and its underlying data, including:

        - saving the chart as a bitmap image file.
        - copying the chart to the system clipboard.
        - saving the data from all plotted curves to various formats.

    - Synchronization: all slice views in the grid are fully synchronized for orientation, zoom, and cursor position.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> MultiViewWidget -> GridViewWidget -> MultiComponentViewWidget

    Creation: 10/12/2024
    Last revision: 19/02/2026
    """

    # Special method

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        MultiComponentViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(4, 4, parent)
        self._rows = 3
        self._cols = 3

        self._menuNumberOfVisibleViews = None
        self._first = 0
        self._multi: SisypheVolume | None = None
        self._line: Line2D | None = None
        self._span: Rectangle | None = None
        self._menuCurves: QMenu | None = None
        self._scrshot: ScreenshotsGridWidget | None = None

        self._initViews()
        self._initActions()
        self._initSynchronisationSignalConnect()

        # Init Figure

        self._fig = Figure()
        self._axe: Axes | None = None
        self._canvas = FigureCanvas(self._fig)
        self._canvas.mpl_connect('pick_event', self._chartClicked)
        # < Revision 02/02/2026
        # self._layout.addWidget(self._canvas, 3, 0, 1, 3)
        self._layout.addWidget(self._canvas, 3, 0, 1, 3)
        self._layout.setRowStretch(0, 2)
        self._layout.setRowStretch(1, 2)
        self._layout.setRowStretch(2, 2)
        self._layout.setRowStretch(3, 3)
        # Revision 02/02/2026 >

    """
    Private attributes

    _first          int, index of the first displayed component
    _multi          SisypheVolume, multi-component volume
    _fig            Figure, chart
    _canvas         FigureCanvas
    _line           Line2D, signal curve at current cursor position
    _menuCurves     QMenu, chart management menu
    _scrshot        ScreenshotsGridWidget
    """

    # Private methods

    def _initViews(self) -> None:
        """
        Initializes the 3x3 grid of SliceViewWidget instances.
        """
        for i in range(9):
            w = SliceViewWidget(parent=self)
            w.setName('MultiComponentViewWidget view#{}'.format(i))
            self.setViewWidget(i // 3, i % 3, w)
        self.setVisibilityControlToAll()

    def _initActions(self) -> None:
        """
        Initializes specific QAction instances for each view widget and connects them to their respective slots.
        This includes actions for view arrangement, chart visibility, and curve management.
        """
        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.synchronisationOn()
            action = w.getAction()
            action['expand'].setVisible(False)
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

            action['showchart'] = QAction('Show chart', self)
            action['showchart'].setCheckable(True)
            action['showchart'].setChecked(True)
            action['showchart'].triggered.connect(self.setChartVisibility)
            # noinspection PyProtectedMember
            w._menuVisibility.insertAction(action['showall'], action['showchart'])

            action['addcurve'] = QAction('Add current curve...', self)
            action['removecurve'] = QAction('Clean chart', self)
            action['savecurve'] = QAction('Save curve values...', self)
            action['savechart'] = QAction('Save chart...', self)
            action['clipbrdchart'] = QAction('Copy chart to clipboard', self)
            action['scrnshotchart'] = QAction('Send chart to screenshot preview', self)
            action['addcurve'].triggered.connect(self.addCurrentCurveToChart)
            action['removecurve'].triggered.connect(self.cleanChart)
            action['savecurve'].triggered.connect(self.saveCurveDataset)
            action['savechart'].triggered.connect(self.saveChart)
            action['clipbrdchart'].triggered.connect(self.copyChartToClipboard)
            action['scrnshotchart'].triggered.connect(self.copyChartToScreenshot)
            menucurves = QMenu('Curves', popup)
            # noinspection PyUnresolvedReferences
            menucurves.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyUnresolvedReferences
            menucurves.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyUnresolvedReferences
            menucurves.setAttribute(Qt.WA_TranslucentBackground, True)
            menucurves.addAction(action['addcurve'])
            menucurves.addAction(action['removecurve'])
            menucurves.addSeparator()
            menucurves.addAction(action['savecurve'])
            menucurves.addAction(action['savechart'])
            menucurves.addAction(action['clipbrdchart'])
            menucurves.addAction(action['scrnshotchart'])
            # < Revision 12/12/2024
            # popup.insertMenu(popup.actions()[3], menucurves)
            popup.insertMenu(popup.actions()[11], menucurves)
            # Revision 12/12/2024 >
            if i == 0: self._menuCurves = menucurves

    def _initSynchronisationSignalConnect(self) -> None:
        """
        Initializes synchronization signal connections between view widgets.
        """
        for i in range(9):
            w1 = self.getViewWidgetAt(i // 3, i % 3)
            w1.synchronisationOn()
            w1.CursorPositionChanged.connect(self._cursorPositionChanged)
            for j in range(9):
                if j != i:
                    w2 = self.getViewWidgetAt(j // 3, j % 3)
                    w1.ZoomChanged.connect(w2.synchroniseZoomChanged)
                    w1.CameraPositionChanged.connect(w2.synchroniseCameraPositionChanged)
                    w1.CursorPositionChanged.connect(w2.synchroniseCursorPositionChanged)
                    # w1.OpacityChanged.connect(w2.synchronisedOpacityChanged)
                    w1.RenderUpdated.connect(w2.synchroniseRenderUpdated)
                    w1.ViewMethodCalled.connect(w2.synchroniseViewMethodCalled)

    def _cursorPositionChanged(self) -> None:
        """
        Callback triggered when the cross-shaped cursor position changes in any of the slice view widgets.
        Updates the 1D signal chart with the component values at the new cross-shaped cursor position.
        """
        if self._multi is not None:
            if self._axe is not None:
                p = self[0, 0].getCursorArrayPosition()
                n = self._multi.getNumberOfComponentsPerPixel()
                xdata = list(range(n))
                # noinspection PyTypeChecker
                ydata = list(self._multi[p[0], p[1], p[2]])
                if self._line is None:
                    self._line, = self._axe.plot(xdata, ydata, 'o-', label='voxel {} {} {}'.format(p[0], p[1], p[2]))
                else:
                    # noinspection PyTypeChecker
                    self._line.set_xdata(array(xdata))
                    # noinspection PyTypeChecker
                    self._line.set_ydata(array(ydata))
                    self._line.set_label('voxel {} {} {}'.format(p[0], p[1], p[2]))
                self._axe.relim()
                self._axe.autoscale_view()
                self._axe.legend()
                self._canvas.draw()

    def _chartClicked(self, event: PickEvent) -> None:
        """
        Callback for 'pick_event' on the Matplotlib chart.
        If a curve representing voxel data is clicked, it moves the cursor in the slice view widgets  to that voxel's
        location.

        Parameters
        ----------
        event : matplotlib.backend_bases.PickEvent
            pick event instance containing information about the click.
        """
        if self._multi is not None:
            artist = event.artist
            if isinstance(artist, Line2D):
                lb = artist.get_label()
                # noinspection PyUnresolvedReferences
                if lb[0] == 'v':
                    # noinspection PyUnresolvedReferences
                    r = lb.split(' ')
                    if len(r) == 4:
                        spacing = self._multi.getSpacing()
                        x = int(r[1]) * spacing[0]
                        y = int(r[2]) * spacing[1]
                        z = int(r[3]) * spacing[2]
                        self[0, 0].setCursorWorldPosition(x, y, z)

    # Public method

    def updateLut(self, lut: SisypheLut) -> None:
        """
        Update the lookup table (LUT) and window/level for all component view widgets.

        Parameters
        ----------
        lut : SisypheLut
            new lookup table to apply.
        """
        for k in self._views:
            # update colormap
            lutm = lut.getName()
            lutk = self._views[k].getVolume().display.getLUT().getName()
            if lutk != lutm:
                self._views[k].getVolume().display.getLUT().setLut(lutm)
            # update window
            w = lut.getWindowRange()
            self._views[k].getVolume().display.setWindow(w[0], w[1])

    def getPopupCurves(self) -> QMenu:
        """
        Gets the 'Curves' popup menu for chart management.

        Returns
        -------
        QMenu
            'Curves' menu.
        """
        return self._menuCurves

    def setFirstDisplayedComponent(self, first: int) -> None:
        """
        Set the first component to be displayed in the top-left viewport of the grid.
        The subsequent viewports are populated with the following components.

        Parameters
        ----------
        first : int
            index of the first component to display.
        """
        if self._multi is not None:
            n = self._multi.getNumberOfComponentsPerPixel()
            if n < 10: self._first = 0
            elif 0 <= first < n - 8: self._first = first
            else: self._first = 0
            first, last = self._first, min(self._first + 9, n)
            for i in range(first, last):
                c = i - first
                component = self._multi.copyComponent(i)
                view = self[c // 3, c % 3]
                title = 'component#{}'.format(i)
                view.setName(title)
                view.setTitle(title)
                view.replaceVolume(component)
            self.updateSpan()

    def getFirstDisplayedComponent(self) -> int:
        """
        Get the index of the first component currently displayed in the grid.

        Returns
        -------
        int
            index of the first displayed component.
        """
        return self._first

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the multi-component SisypheVolume to be displayed.
        Populates the slice view widgets with individual components and initializes the chart.

        Parameters
        ----------
        volume : SisypheVolume
            multi-component SisypheVolume to display.
        """
        n = volume.getNumberOfComponentsPerPixel()
        if n > 1:
            self._first = 0
            self._multi = volume
            if n < 10: first, last = 0, n
            else: first, last = self._first, min(self._first + 9, n)
            for i in range(first, last):
                c = i - first
                component = volume.copyComponent(i)
                view = self[c // 3, c % 3]
                title = 'component#{}'.format(i)
                view.setName(title)
                view.setTitle(title)
                view.setVolume(component)
            # update visible views
            nbv = last - first - 1
            if nbv < 3: self.setRowsAndCols(nbv // 3 + 1, nbv % 3 + 1)
            elif nbv == 3: self.setRowsAndCols(2, 2)
            elif nbv in [4, 5]: self.setRowsAndCols(2, 3)
            else: self.setRowsAndCols(3, 3)
            # update chart, add mean curve
            self.cleanChart()
        else: raise ValueError('{} is not a multi-component volume.')

    def getVolume(self) -> SisypheVolume:
        """
        Get the currently displayed multi-component SisypheVolume.

        Returns
        -------
        SisypheVolume
            current multi-component SisypheVolume.
        """
        return self._multi

    def hasVolume(self) -> bool:
        """
        Check if a multi-component SisypheVolume is currently displayed.

        Returns
        -------
        bool
            True if a SisypheVolume is displayed, False otherwise.
        """
        return self._multi is not None

    def removeVolume(self) -> None:
        """
        Remove the multi-component SisypheVolume and clears all view widgets.
        """
        for k in self._views:
            self._views[k].removeVolume()
        self._multi = None

    def setScreenshotsGridWidget(self, widget: ScreenshotsGridWidget):
        """
        Set the screenshots manager widget for exporting chart captures.

        Parameters
        ----------
        widget : ScreenshotsGridWidget
            screenshots manager widget.
        """
        self._scrshot = widget

    def getScreenshotsGridWidget(self) -> ScreenshotsGridWidget:
        """
        Get the associated screenshots manager widget.

        Returns
        -------
        ScreenshotsGridWidget
            screenshots manager widget.
        """
        return self._scrshot

    # < Revision 29/04/2025
    # add visibleChartOn method
    def visibleChartOn(self) -> None:
        """
        Make the chart visible.
        """
        self.setChartVisibility(True)
    # Revision 29/04/2025 >

    # < Revision 29/04/2025
    # add visibleChartOff method
    def visibleChartOff(self) -> None:
        """
        Hide the chart.
        """
        self.setChartVisibility(False)
    # Revision 29/04/2025 >

    # < Revision 29/04/2025
    # add setChartVisibility method
    def setChartVisibility(self, v: bool) -> None:
        """
        Set the visibility of the chart.

        Parameters
        ----------
        v : bool
            True to show the chart, False to hide it.
        """
        self._canvas.setMinimumHeight(self.height() // 3)
        self._canvas.setVisible(v)
        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.getAction()['showchart'].setChecked(v)
    # Revision 29/04/2025 >

    # < Revision 29/04/2025
    # add getChartVisibility method
    def getChartVisibility(self) -> bool:
        """
        Get the visibility state of the chart.

        Returns
        -------
        bool
            True if the chart is visible, False otherwise.
        """
        return self._canvas.visible()
    # Revision 29/04/2025 >

    def cleanChart(self) -> None:
        """
        Clear the chart, removing all plotted curves, and redraws the mean signal curve and the component span.
        """
        self._fig.clear()
        if self._axe is not None: self._axe.cla()
        self._line = None
        self._axe = self._fig.add_subplot(111)
        self._axe.spines['top'].set_visible(False)
        self._axe.spines['right'].set_visible(False)
        # Curves
        n = self._multi.getNumberOfComponentsPerPixel()
        xdata = list(range(n))
        ydata = list()
        v = self._multi.copyComponent(0)
        mask = v.getMask2()
        for i in range(n):
            ydata.append(self._multi.getMean(mask, i))
        self._axe.plot(xdata, ydata, 'o-', label='Mean signal')
        # self._canvas.draw()
        self._canvas.draw()
        self._cursorPositionChanged()
        self._axe.legend()
        # Span
        last = min(self._first + 8, n - 1)
        self._span = self._axe.axvspan(self._first, last,
                                       facecolor='yellow', edgecolor='black', linewidth=2,
                                       linestyle='--', alpha=0.2)

    def updateSpan(self) -> None:
        """
        Update the position and width of the highlighted span on the chart, which indicates the range of currently
        visible components in the grid.
        """
        if self._span is not None:
            # noinspection PyUnresolvedReferences
            self._span.xy[0][0] = self._first
            # noinspection PyUnresolvedReferences
            self._span.xy[1][0] = self._first
            # noinspection PyUnresolvedReferences
            self._span.xy[4][0] = self._first
            n = self._multi.getNumberOfComponentsPerPixel()
            last = min(self._first + 8, n - 1)
            # noinspection PyUnresolvedReferences
            self._span.xy[2][0] = last
            # noinspection PyUnresolvedReferences
            self._span.xy[3][0] = last
            self._canvas.draw()

    def addCurrentCurveToChart(self) -> None:
        """
        Add a persistent copy of the current signal curve (at the cross-shaped cursor's position) to the chart.
        """
        if self._line is not None:
            xdata = self._line.get_xdata()
            ydata = self._line.get_ydata()
            artist, = self._axe.plot(xdata, ydata, 'o-', label=self._line.get_label())
            artist.set_picker(True)
            self._axe.legend()
            self._canvas.draw()

    def saveChart(self) -> None:
        """
        Open a file dialog to save the current chart as a bitmap file (supported formats BMP, JPG, PNG, TIFF, SVG).
        """
        if self._multi is not None:
            filename = self._multi.getFilename()
            filename = addSuffixToFilename(filename, 'curves')
            filename = splitext(filename)[0] + '.jpg'
            filename = QFileDialog.getSaveFileName(self, 'Save chart', filename,
                                                   filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;'
                                                          'TIFF (*.tiff);;SVG (*.svg)',
                                                   initialFilter='JPG (*.jpg)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: self._fig.savefig(filename)
                except Exception as err:
                    messageBox(self, 'Save chart', text='{}'.format(err))

    def copyChartToClipboard(self) -> None:
        """
        Copy the current chart to the system clipboard as a bitmap image.
        """
        if self._multi is not None:
            tmp = join(getcwd(), 'tmp.png')
            try:
                self._fig.savefig(tmp)
                img = QPixmap(tmp)
                QApplication.clipboard().setPixmap(img)
            except Exception as err:
                messageBox(self, 'Copy chart to clipboard', text='error: {}'.format(err))
            finally:
                if exists(tmp): remove(tmp)

    def copyChartToScreenshot(self) -> None:
        """
        Send the current chart to the associated ScreenshotsGridWidget.
        """
        if self._multi is not None:
            if self._scrshot is not None:
                self.copyChartToClipboard()
                self._scrshot.pasteFromClipboard()

    def saveCurveDataset(self) -> None:
        """
        Open a file dialog to save the data of all curves currently plotted on the chart to a file. Supported formats
        include CSV, JSON, Latex, text, Excel XLSX, and PySisyphe Sheet (*.xsheet).
        """
        if self._multi is not None:
            filename = self._multi.getFilename()
            filename = addSuffixToFilename(filename, 'curves')
            filename = splitext(filename)[0] + '.csv'
            filename = QFileDialog.getSaveFileName(self, 'Save ', filename,
                                                   filter='CSV (*.csv);; '
                                                          'JSON (*.json);; '
                                                          'Latex (*.tex);; '
                                                          'Text (*.txt);; '  
                                                          'XLSX (*.xlsx);; '
                                                          'PySisyphe Sheet (*.xsheet)',
                                                   initialFilter='CSV (*.csv)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                n = len(self._axe.lines)
                if n > 0:
                    lines = list()
                    labels = list()
                    for i in range(n):
                        lines.append(self._axe.lines[i].get_ydata())
                        labels.append(self._axe.lines[i].get_label())
                    lines = array(lines)
                    df = DataFrame(lines.T, columns=labels).T
                    sheet = SisypheSheet(df)
                    ext = splitext(filename)[1][1:]
                    try:
                        if ext == 'csv': sheet.saveCSV(filename)
                        elif ext == 'json': sheet.saveJSON(filename)
                        elif ext == 'tex': sheet.saveLATEX(filename)
                        elif ext == 'txt': sheet.saveTXT(filename)
                        elif ext == 'xlsx':
                            try: sheet.saveXLSX(filename)
                            except:
                                # < Revision 19/02/2026
                                try:
                                    import openpyxl
                                    messageBox(self, 'Save chart dataset', text='Open xlsx error.')
                                except:
                                    if hasattr(sys, '_MEIPASS'):
                                        messageBox(self,
                                                   'XLSX IO',
                                                   'OpenPyXL module is not installed.\n'
                                                   'Please perform a complete reinstallation of the latest version '
                                                   'of PySisyphe, which can be downloaded from '
                                                   'https://github.com/PySisyphe/Sisyphe.')
                                    else:
                                        messageBox(self,
                                                   'XLSX IO',
                                                   'OpenPyXL module is not installed.\n'
                                                   'Please install it using "pip install openpyxl==3.1.5" from your venv console.')
                                # Revision 19/02/2026 >
                        elif ext == 'xsheet': sheet.save(filename)
                        else: raise ValueError('{} format is not supported.'.format(ext))
                    except Exception as err:
                        messageBox(self, 'Save chart dataset', text='error: {}'.format(err))

    def setNumberOfVisibleViews(self, r: int, c: int) -> None:
        """
        Change the layout of the view grid.

        Parameters
        ----------
        r : int
            Number of rows.
        c : int
            Number of columns.
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
        for i in range(9):
            a = i // 3
            b = i % 3
            self[a, b].getAction()[k].setChecked(True)
            if n > 0: self[a, b].setVisible(i < n)
            else: self[a, b].setVisible(i in [0, 1, 3, 4])
            self.setRows(r)
            self.setCols(c)

    def getViewsArrangement(self) -> tuple[int, int]:
        """
        Get the current grid arrangement (rows, columns).

        Returns
        -------
        tuple[int, int]
            tuple containing the number of rows and columns.
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
        Set the orientation of all slice view widgets to axial.
        """
        self.setOrientation(0)

    def setCoronalOrientation(self) -> None:
        """
         Set the orientation of all slice view widgets to coronal.
         """
        self.setOrientation(1)

    def setSagittalOrientation(self) -> None:
        """
         Set the orientation of all slice view widgets to sagittal.
         """
        self.setOrientation(2)

    def setOrientation(self, orient: int) -> None:
        """
        Set the orientation for all slice view widgets in the grid.

        Parameters
        ----------
        orient : int
            orientation to set (0 for axial, 1 for coronal, 2 for sagittal).
        """
        if self.isNotEmpty():
            for w in self._views.values():
                if isinstance(w, AbstractViewWidget):
                    if w.hasVolume(): w.setOrientation(orient)

    def getOrientation(self) -> int:
        """
        Get the current orientation of the slice view widgets.

        Returns
        -------
        int
            current orientation (0 for axial, 1 for coronal, 2 for sagittal).
        """
        return self._views[(0, 0)].getOrientation()

    def getOrientationAsString(self) -> str:
        """
        Get the current orientation of the slice view widgets as a string.

        Returns
        -------
        str
            orientation as 'axial', 'coronal', or 'sagittal'.
        """
        return self._views[(0, 0)].getOrientationAsString()

    def getPopupMenuNumberOfVisibleViews(self) -> QMenu:
        """
        Get the 'Number of views' popup menu.

        Returns
        -------
        QMenu
            'Number of views' menu.
        """
        return self._menuNumberOfVisibleViews

    def popupMenuOrientationEnabled(self) -> None:
        """
        Enable the 'Orientation' menu in all slice view popups.
        """
        for w in self._views.values():
            w.popupOrientationEnabled()

    def popupMenuOrientationDisabled(self) -> None:
        """
        Disable the 'Orientation' menu in all slice view popups.
        """
        for w in self._views.values():
            w.popupOrientationDisabled()

    def popupMenuNumberOfVisibleViewsShow(self) -> None:
        """
        Show the 'Number of views' menu in all slice view popups.
        """
        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.getPopup().actions()[2].setVisible(True)

    def popupMenuNumberOfVisibleViewsHide(self) -> None:
        """
        Hide the 'Number of views' menu in all slice view popups.
        """
        for i in range(9):
            w = self.getViewWidgetAt(i // 3, i % 3)
            w.getPopup().actions()[2].setVisible(False)


class IconBarMultiComponentViewWidget(IconBarWidget):
    """
    IconBarMultiComponentViewWidget

    Description
    -----------

    This widget encapsulates a MultiComponentViewWidget and extends it by providing a collapsible icon bar that is
    displayed on the left.

    Inheritance
    -----------

    QWidget -> IconBarWidget -> IconBarMultiComponentViewWidget

    Creation: 10/12/2024
    Last revision: 10/10/2025
    """

    # Special method

    def __init__(self,
                 widget: MultiComponentViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarMultiComponentViewWidget instance constructor

        Parameters
        ----------
        widget: MultiComponentViewWidget | None (optional)
            MultiComponentViewWidget instance to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)

        self._shcutg = QShortcut('g', self)  # Show graph shortcut

        if widget is None: widget = MultiComponentViewWidget()
        if isinstance(widget, MultiComponentViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not MultiComponentViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Public methods

    def setViewWidget(self, widget: MultiComponentViewWidget):
        """
        Set the main MultiComponentViewWidget instance and connects its actions to the icon bar buttons.
        Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        widget : MultiComponentViewWidget
            view widget to be controlled by this icon bar.
        """
        if isinstance(widget, MultiComponentViewWidget):
            self._widget = widget
            self._widget.setParent(self)
            self._layout.addWidget(widget)
            view1 = widget.getFirstSliceViewWidget()
            # noinspection PyUnresolvedReferences
            self._icons['expand'].clicked.connect(self._onExpand)
            self._connectExpandAction()
            # noinspection PyUnresolvedReferences
            self._icons['screen'].clicked.connect(lambda _: self._onFullScreen())
            # noinspection PyUnresolvedReferences
            self._icons['zoomin'].clicked.connect(view1.zoomIn)
            # noinspection PyUnresolvedReferences
            self._icons['zoomout'].clicked.connect(view1.zoomOut)
            # noinspection PyUnresolvedReferences
            self._icons['zoom1'].clicked.connect(view1.zoomDefault)
            self._icons['actions'].setMenu(view1.getPopupActions())
            self._icons['info'].setMenu(view1.getPopupInformation())
            self._icons['colorbar'].setMenu(view1.getPopupColorbarPosition())
            self._icons['ruler'].setMenu(view1.getPopupRulerPosition())
            submenu = QMenu()
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyUnresolvedReferences
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            submenu.addAction('Copy grid capture to clipboard')
            submenu.addAction('Copy selected view capture to clipboard')
            # noinspection PyUnresolvedReferences
            submenu.triggered.connect(self._onMenuCopyCapture)
            self._icons['clipboard'].setMenu(submenu)
            self._icons['compminus'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=False)
            self._icons['compplus'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=False)
            self._icons['orient'] = self._createButton('wdimz.png', 'dimz.png', checkable=False, autorepeat=False)
            self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
            self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
            self._icons['curves'] = self._createButton('wcurve.png', 'curve.png', checkable=False, autorepeat=False)
            self._icons['orient'].setMenu(view1.getPopupOrientation())
            self._icons['curves'].setMenu(widget.getPopupCurves())
            menu = view1.getPopupOrientation()
            menu.actions()[0].triggered.connect(lambda dummy, v=0: self._onMenuOrientation(v))
            menu.actions()[1].triggered.connect(lambda dummy, v=1: self._onMenuOrientation(v))
            menu.actions()[2].triggered.connect(lambda dummy, v=2: self._onMenuOrientation(v))
            # noinspection PyUnresolvedReferences
            self._shcutA.activated.connect(lambda: menu.actions()[0].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutC.activated.connect(lambda: menu.actions()[1].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutS.activated.connect(lambda: menu.actions()[2].trigger())
            # noinspection PyUnresolvedReferences
            self._icons['compplus'].clicked.connect(self.nextComponent)
            # noinspection PyUnresolvedReferences
            self._icons['compplus'].setShortcut(Qt.Key_PageDown)
            # noinspection PyUnresolvedReferences
            self._icons['compminus'].clicked.connect(self.previousComponent)
            # noinspection PyUnresolvedReferences
            self._icons['compminus'].setShortcut(Qt.Key_PageUp)
            # noinspection PyUnresolvedReferences
            self._icons['sliceminus'].clicked.connect(view1.slicePlus)
            # noinspection PyUnresolvedReferences
            self._icons['sliceplus'].clicked.connect(view1.sliceMinus)
            layout = self._bar.layout()
            layout.insertWidget(3, self._icons['sliceplus'])
            layout.insertWidget(3, self._icons['sliceminus'])
            layout.insertWidget(3, self._icons['compminus'])
            layout.insertWidget(3, self._icons['compplus'])
            layout.insertWidget(3, self._icons['orient'])
            self._icons['orient'].setToolTip('Set view orientation (axial, coronal, sagittal).\n'
                                             'A key to set axial orientation,\n'
                                             'C key to set coronal orientation,\n'
                                             'S key to set sagitall orientation.')
            self._icons['compplus'].setToolTip('Go to next component.\n'
                                               'PageDown key')
            self._icons['compminus'].setToolTip('Go to previous component.'
                                                'PageUp key')
            self._icons['sliceminus'].setToolTip('Previous slice.\n'
                                                 'Up or Left key\n'
                                                 'MouseWheel')
            self._icons['sliceplus'].setToolTip('Next slice.\n'
                                                'Down or Right key\n'
                                                'MouseWheel')
            self._icons['curves'].setToolTip('Chart management.')
            # widget.popupMenuROIDisabled()
            self._icons['grid'] = self._createButton('wgrid.png', 'grid.png', checkable=False, autorepeat=False)
            self._visibilityflags['grid'] = True
            self._icons['grid'].setToolTip('Set row and column count.\n'
                                           '1 key 1x1\n'
                                           '2 key 1x2\n'
                                           '3 key 1x3\n'
                                           '4 key 2x2\n'
                                           '6 key 2x3\n'
                                           '9 key 3x3')
            self._icons['grid'].setMenu(widget.getPopupMenuNumberOfVisibleViews())
            self._icons['grid'].setMenu(widget.getPopupMenuNumberOfVisibleViews())
            # noinspection PyUnresolvedReferences
            self._shcut1.activated.connect(lambda: self._icons['grid'].menu().actions()[0].trigger())
            # noinspection PyUnresolvedReferences
            self._shcut2.activated.connect(lambda: self._icons['grid'].menu().actions()[1].trigger())
            # noinspection PyUnresolvedReferences
            self._shcut3.activated.connect(lambda: self._icons['grid'].menu().actions()[2].trigger())
            # noinspection PyUnresolvedReferences
            self._shcut4.activated.connect(lambda: self._icons['grid'].menu().actions()[3].trigger())
            # noinspection PyUnresolvedReferences
            self._shcut6.activated.connect(lambda: self._icons['grid'].menu().actions()[4].trigger())
            # noinspection PyUnresolvedReferences
            self._shcut9.activated.connect(lambda: self._icons['grid'].menu().actions()[5].trigger())
            layout.insertWidget(3, self._icons['grid'])
            self._icons['show'].setMenu(view1.getPopupVisibility())
            self._icons['show'].setToolTip('Set visibility options.\n'
                                           'x key show/hide cursor\n'
                                           'i key show/hide information\n'
                                           'l key show/hide orientation labels\n'
                                           'm key show/hide orientation marker\n'
                                           'b key show/hide colorbar\n'
                                           'r key show/hide ruler\n'
                                           't key show/hide tooltip\n'
                                           'g key show/hide chart')
            # noinspection PyUnresolvedReferences
            self._shcutx.activated.connect(lambda: self._icons['show'].menu().actions()[0].trigger())
            # noinspection PyUnresolvedReferences
            self._shcuti.activated.connect(lambda: self._icons['show'].menu().actions()[1].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutl.activated.connect(lambda: self._icons['show'].menu().actions()[2].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutm.activated.connect(lambda: self._icons['show'].menu().actions()[3].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutb.activated.connect(lambda: self._icons['show'].menu().actions()[4].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutr.activated.connect(lambda: self._icons['show'].menu().actions()[5].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutt.activated.connect(lambda: self._icons['show'].menu().actions()[6].trigger())
            # noinspection PyUnresolvedReferences
            self._shcutg.activated.connect(lambda: self._icons['show'].menu().actions()[7].trigger())
            submenu = QMenu()
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyUnresolvedReferences
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            submenu.addAction('Save grid capture...')
            submenu.addAction('Save selected view capture...')
            submenu.addAction('Save captures from slice series...')
            submenu.addSeparator()
            action = submenu.addAction('Send selected view capture to screenshots preview')
            # noinspection PyUnresolvedReferences
            action.setShortcut(Qt.Key_Space)
            # noinspection PyUnresolvedReferences
            submenu.triggered.connect(self._onMenuSaveCapture)
            self._icons['capture'].setMenu(submenu)
            layout.insertWidget(20, self._icons['curves'])

            self._icons['iso'].setVisible(False)
            self._visibilityflags['grid'] = True
            self._visibilityflags['orient'] = True
            self._visibilityflags['sliceminus'] = True
            self._visibilityflags['sliceplus'] = True
            self._visibilityflags['curves'] = True
            self._visibilityflags['compplus'] = True
            self._visibilityflags['compminus'] = True
            self._visibilityflags['iso'] = False
        else: raise TypeError('parameter type {} is not MultiComponentViewWidget.'.format(type(widget)))

    def setVolume(self, multi: SisypheVolume) -> None:
        """
        Set the multi-component SisypeVolume for the managed view widget.

        Parameters
        ----------
        multi : SisypheVolume
            multi-component SisypheVolume to display.
        """
        n = multi.getNumberOfComponentsPerPixel()
        if n > 1:
            super().setVolume(multi)
            thumbnail = self.getThumbnail()
            if thumbnail is not None:
                mainwindow = thumbnail.getMainWindow()
                if mainwindow is not None:
                    self().setScreenshotsGridWidget(mainwindow.getScreenshots())
            # < Revision 13/12/2024
            # To solve VTK mouse move event bug
            self.timerEnabled()
            # Revision 13/12/2024 >
        else: raise ValueError('{} is a single-component volume.'.format(multi.getBasename()))

    def removeVolume(self) -> None:
        """
        Remove the SisypheVolume from the managed view widget.
        """
        if self._widget is not None:
            super().removeVolume()
            # < Revision 13/12/2024
            # To solve VTK mouse move event bug
            self.timerDisabled()
            # Revision 13/12/2024 >

    def setFirstDisplayedComponent(self, first: int) -> None:
        """
        Set the first component to be displayed in the grid view.

        Parameters
        ----------
        first : int
            Index of the first component.
        """
        self().setFirstDisplayedComponent(first)

    def getFirstDisplayedComponent(self) -> int:
        """
        Get the index of the first component currently displayed in the grid view.

        Returns
        -------
        int
            index of the first component.
        """
        return self().getFirstDisplayedComponent()

    def nextComponent(self) -> None:
        """
        Navigate to the next component in the sequence, updating the grid view.
        Wraps around to the beginning if at the end.
        """
        n = self().getVolume().getNumberOfComponentsPerPixel()
        if n > 9:
            c = self.getFirstDisplayedComponent()
            if c < n - 9: self.setFirstDisplayedComponent(c + 1)
            else: self.setFirstDisplayedComponent(0)

    def previousComponent(self) -> None:
        """
        Navigate to the previous component in the sequence, updating the grid view.
        Wraps around to the end if at the beginning.
        """
        n = self().getVolume().getNumberOfComponentsPerPixel()
        if n > 9:
            c = self.getFirstDisplayedComponent()
            if c > 0: self.setFirstDisplayedComponent(c - 1)
            else: self.setFirstDisplayedComponent(n - 9)

    # Dummy methods, not inherited from IconBarWidget

    # override addOverlay (inherited from IconBarWidget class) as dummy method, no overlay in projection
    def addOverlay(self, volume: SisypheVolume) -> None:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        pass

    # override getOverlayCount (inherited from IconBarWidget class) as dummy method, no overlay in projection, always 0
    def getOverlayCount(self) -> int:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        return 0

    # override hasOverlay (inherited from IconBarWidget class) as dummy method, no overlay in projection, always False
    def hasOverlay(self) -> bool:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        return False

    # mandatory method for compatibility with IconBarViewWidgetCollection
    def getOverlayIndex(self, o: SisypheVolume) -> int | None:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        raise NotImplementedError

    # mandatory method for compatibility with IconBarViewWidgetCollection
    def removeOverlay(self, o: int | SisypheVolume) -> None:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        pass

    # mandatory method for compatibility with IconBarViewWidgetCollection
    def removeAllOverlays(self) -> None:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        pass

    # mandatory method for compatibility with IconBarViewWidgetCollection
    def getOverlayFromIndex(self, index: int) -> None:
        """
        Dummy method, overlays are not available in this widget.
        Currently, this method overrides the superclass's implementation.
        """
        raise NotImplementedError
