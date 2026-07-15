"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - scipy, scientific computing, https://scipy.org/
"""

import sys
from sys import platform

from os import getcwd
from os import remove
from os import chdir

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import array
from numpy import ndarray
from numpy import sum
from numpy import sqrt
from numpy import median
from numpy import percentile
from numpy import where

from pandas import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from scipy.stats import describe

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
# < Revision 29/11/2025
from Sisyphe.widgets.consoleWidget import ConsoleWidget
# Revision 29/11/2025 >

__all__ = ['DialogGenericResults']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogGenericResults
"""


class DialogGenericResults(QDialog):
    """
    DialogGenericResults class

    Description
    ~~~~~~~~~~~

    Generic dialog to display statistical results as table(s) and/or chart(s).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogGenericResults

    Creation: 25/11/2022
    Last revision: 19/02/2026
    """

    # Special method

    def __init__(self, parent=None):
        """
        DialogGenericResults instance constructor.

        Parameters
        ----------
        parent : QWidget, optional
            The parent widget. Defaults to None.
        """
        super().__init__(parent)

        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._plotlist = list()
        self._treelist = list()
        self._scrshot = list()
        self._console: ConsoleWidget | None = None

        self._tab = QTabWidget()

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32' or platform == 'linux': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
        # noinspection PyUnresolvedReferences
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        lyout.addWidget(ok)
        lyout.addStretch()

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(lambda: self.hide())

        # Init Layout

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(5, 0, 0, 0)
        self._layout.addWidget(self._tab)
        self._layout.addLayout(lyout)
        self.setLayout(self._layout)

    """
     Private attributes

    _plotlist   list[Figure]
    _treelist   list[TreeViewWidget]
    _scrshot    list[ScreenshotsGridWidget]
    _tab        QTabWidget
    _console    ConsoleWidget
    """

    # Private methods

    def _onSaveBitmap(self):
        """
        Slot to save the current tab's figure as a bitmap image.
        Opens a file dialog to select the output path and format.
        Supported formats: BMP, JPG, PNG, TIFF, SVG.
        """
        if self._tab.count() > 0:
            index = self._tab.currentIndex()
            fig = self._plotlist[index].figure
            filename = self._tab.tabText(index) + '_chart'
            filename = QFileDialog.getSaveFileName(self, 'Save capture', filename,
                                                   filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;'
                                                          'TIFF (*.tiff);;SVG (*.svg)',
                                                   initialFilter='JPG (*.jpg)')[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                try: fig.savefig(filename)
                except Exception as err: messageBox(self, 'Save capture', text='{}'.format(err))

    def _onCopyClipboard(self):
        """
        Slot to copy the current tab's figure to the system clipboard.
        The figure is saved to a temporary PNG file, then loaded as a QPixmap and placed on the clipboard.
        """
        if self._tab.count() > 0:
            index = self._tab.currentIndex()
            if self.isFigureVisible(index):
                fig = self._plotlist[index].figure
                tmp = join(getcwd(), 'tmp.png')
                try:
                    fig.savefig(tmp)
                    img = QPixmap(tmp)
                    QApplication.clipboard().setPixmap(img)
                except Exception as err:
                    messageBox(self, 'Copy capture to clipboard', text='error: {}'.format(err))
                finally:
                    if exists(tmp): remove(tmp)

    def _onCopyScreenshots(self):
        """
        Slot to copy the current tab's figure and/or tree widget to the associated ScreenshotsGridWidget.
        """
        if self._tab.count() > 0:
            index = self._tab.currentIndex()
            widget = self._scrshot[index]
            if widget is not None and isinstance(widget, ScreenshotsGridWidget):
                if self.isFigureVisible(index):
                    self._onCopyClipboard()
                    widget.pasteFromClipboard()
                if self.isTreeVisible(index):
                    img = self._treelist[index].grab()
                    QApplication.clipboard().setPixmap(img)
                    widget.pasteFromClipboard()

    # < Revision 29/11/2025
    # add _onCopyConsole method
    def _onCopyConsole(self):
        """
        Slot to copy the current dataset to the associated ConsoleWidget.
        """
        if self._console is not None:
            if self._tab.count() > 0:
                index = self._tab.currentIndex()
                df = self._getDataFrame(index)
                try:
                    suffix = 0
                    name = 'df'
                    while self._console.hasVariable(name):
                        suffix += 1
                        name = 'df{}'.format(suffix)
                    self._console.pushVariables({name: df.values.tolist()})
                    self._console.update()
                    messageBox(self,
                               'Copy dataset to console',
                               icon=QMessageBox.Information,
                               text='The current dataset is available in the PySisyphe console '
                                    'as a list variable called \"{}\".'.format(name))
                except:
                    messageBox(self,
                               'Copy dataset to console',
                               text='Unable to copy the current dataset to the PySisyphe console.')

    # Revision 29/11/2025 >

    def _onSaveDataset(self):
        """
        Slot to save the data from the current tab's tree widget to a file.
        Opens a file dialog to select the output path and format.
        Supported formats: CSV, JSON, LaTeX, TXT, XLSX, XSHEET.
        """
        if self._tab.count() > 0:
            index = self._tab.currentIndex()
            filename = self._tab.tabText(index) + '_data'
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
                filename = abspath(filename)
                chdir(dirname(filename))
                sheet = SisypheSheet(self._getDataFrame(index))
                ext = splitext(filename)[1][1:]
                try:
                    if ext == 'csv': sheet.saveCSV(filename)
                    elif ext == 'json': sheet.saveJSON(filename)
                    elif ext == 'tex': sheet.saveLATEX(filename)
                    elif ext == 'txt': sheet.saveTXT(filename)
                    elif ext == 'xlsx':
                        # < Revision 19/02/2026
                        try: sheet.saveXLSX(filename)
                        except:
                            try:
                                import openpyxl
                                messageBox(self,
                                           'Save Dataset',
                                           text='Save {} error.'.format(basename(filename)))
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
                    messageBox(self, 'Save Dataset', text='error: {}'.format(err))

    def _onSelectionChanged(self, item):
        """
        Slot to handle selection changes in the tree widget.
        Redraws the chart based on the selected column if a chart type is defined.

        Parameters
        ----------
        item : QTreeWidgetItem
            The clicked item in the tree widget.
        """
        index = self._tab.currentIndex()
        if self.isFigureVisible(index):
            c = item.treeWidget().currentIndex().column()
            if c > 0:
                # noinspection PyUnresolvedReferences
                data = self._treelist[index].headerItem().data(c, Qt.UserRole)['chart']
                if data == 'bar': self.chartBarFromTreeWidgetColumn(index, c)
                elif data == 'plot': self.chartPlotFromTreeWidgetColumn(index, c)
                elif data == 'boxplot': self.chartBoxplotFromTreeWidgetColumn(index, c)
                elif data == 'pie': self.chartPieFromTreeWidgetColumn(index, c)

    def _getDataFrame(self, index):
        """
        Get a pandas DataFrame from the data in a tree widget.

        Parameters
        ----------
        index : int
            The tab index.

        Returns
        -------
        DataFrame
            A pandas DataFrame containing the data from the tree widget.
        """
        if isinstance(index, int):
            df = dict()
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                hdrs = list()
                for i in range(tree.columnCount()):  # cols
                    hdr = tree.headerItem().text(i)
                    # < Revision 05/08/2025
                    hdr = hdr.replace('\n', ' ')
                    # Revision 05/08/2025 >
                    hdrs.append(hdr)
                    df[hdr] = list()
                for i in range(tree.topLevelItemCount()):  # rows
                    item = tree.topLevelItem(i)
                    for j in range(tree.columnCount()):  # cols
                        # < Revision 16/07/2024
                        # exception management of non float values
                        try: buff = float(item.text(j))
                        except: buff = item.text(j)
                        # Revision 16/07/2024 >
                        df[hdrs[j]].append(buff)
                return DataFrame(df)
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    @staticmethod
    def _getDecimals(data: tuple | list | ndarray) -> tuple[int, str]:
        """
        Determine the appropriate number of decimals for formatting a dataset.

        Parameters
        ----------
        data : tuple | list | ndarray
            The input data array.

        Returns
        -------
        tuple[int, str]
            A tuple containing the number of decimals and the format string.
        """
        if isinstance(data, tuple): data = array(list(data))
        if isinstance(data, list): data = array(data)
        if isinstance(data, ndarray):
            # <Revision 19/07/2024
            # Add exception
            try:
                # noinspection PyArgumentList
                m = data.flatten().max()
                if m < 1.0:
                    d = int('{:e}'.format(abs(m)).split('-')[1]) + 1
                    return d, '{:.' + str(d) + 'f}'
                else: return 1, '{:.1f}'
            except: return 1, '{:.1f}'
            # Revision 19/07/2024>
        else: raise TypeError('parameter type {} is not tuple, list or ndarray.'.format(type(data)))

    # Public methods

    # < Revision 29/11/2025
    # add setConsoleWidget method
    def setConsoleWidget(self, w: ConsoleWidget) -> None:
        """
        Set the console widget attribute.

        Parameters
        ----------
        w : ConsoleWidget
        """
        self._console = w
    # Revision 29/11/2025 >

    # < Revision 29/11/2025
    # add getConsoleWidget method
    def getConsoleWidget(self) -> ConsoleWidget | None:
        """
        Get the console widget attribute.

        Returns
        -------
        ConsoleWidget
        """
        return self._console
    # Revision 29/11/2025 >

    # < Revision 29/11/2025
    # add hasConsoleWidget method
    def hasConsoleWidget(self) -> bool:
        """
        Check if the console widget attribute is defined.

        Returns
        -------
        bool
            True if the console widget attribute is not None, False otherwise.
        """
        return self._console is not None
    # Revision 29/11/2025 >

    def autoSize(self, index: int) -> None:
        """
        Automatically resize the dialog width to fit the tree widget content.

        Parameters
        ----------
        index : int
            The tab index containing the tree widget to measure.
        """
        if self._tab.count() > 0:
            if isinstance(index, int):
                if 0 <= index < self._tab.count():
                    tree = self._treelist[index]
                    width = 20
                    for i in range(tree.columnCount()):
                        width += tree.columnWidth(i)
                    screen = QApplication.primaryScreen().geometry()
                    maxwidth = screen.width() * 0.75
                    if width > maxwidth: width = maxwidth
                    self.setMinimumWidth(width)
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def newTab(self,
               title: str = '',
               capture: bool = True,
               clipbrd: bool = True,
               scrshot: ScreenshotsGridWidget | None = None,
               dataset: bool = True) -> int:
        """
        Create and add a new tab to the dialog.

        Parameters
        ----------
        title : str, optional
            Title of the tab.
        capture : bool, optional
            If True, enables the figure canvas and save/copy buttons.
        clipbrd : bool, optional
            If True, enables the copy to clipboard button.
        scrshot : ScreenshotsGridWidget | None, optional
            A ScreenshotsGridWidget instance to enable copying to it.
        dataset : bool, optional
            If True, enables the tree widget and save dataset button.

        Returns
        -------
        int
            The index of the newly created tab.
        """
        if not isinstance(scrshot, ScreenshotsGridWidget): scrshot = None
        if isinstance(title, str):
            lyout = QVBoxLayout()
            lyout.setSpacing(0)
            lyout.setContentsMargins(0, 0, 0, 0)
            # Init Figure
            fig = Figure()
            canvas = FigureCanvas(fig)
            self._plotlist.append(canvas)
            # < Revision 12/06/2025
            # hide figure if capture is false
            fig.set_visible(capture)
            # Revision 12/06/2025 >
            # Init TreeViewWidget
            tree = QTreeWidget(parent=self)
            tree.setSelectionBehavior(QTreeWidget.SelectColumns)
            # noinspection PyUnresolvedReferences
            tree.itemClicked.connect(self._onSelectionChanged)
            self._treelist.append(tree)
            tree.setVisible(dataset)
            # Init Buttons
            btlyout = QHBoxLayout()
            btlyout.setSpacing(10)
            btlyout.setContentsMargins(0, 0, 0, 0)
            cap = QPushButton('Save bitmap', parent=self)
            cap.setToolTip('Save the current chart as a bitmap image.')
            cap.setObjectName('cap')
            # noinspection PyUnresolvedReferences
            cap.clicked.connect(self._onSaveBitmap)
            clip = QPushButton('Copy to clipboard', parent=self)
            clip.setToolTip('Copy the current chart to the system clipboard.')
            clip.setObjectName('clip')
            # noinspection PyUnresolvedReferences
            clip.clicked.connect(self._onCopyClipboard)
            screen = QPushButton('Copy to screenshots',parent=self)
            screen.setToolTip('Copy the current chart to the PySisyphe screenshots manager.')
            screen.setObjectName('screen')
            # noinspection PyUnresolvedReferences
            screen.clicked.connect(self._onCopyScreenshots)
            self._scrshot.append(scrshot)
            # < Revision 29/11/2025
            csle = QPushButton('Copy to console',parent=self)
            csle.setToolTip('Copy the current dataset to the PySisyphe console\n'
                            'as a pandas DataFrame variable.')
            csle.setObjectName('console')
            # noinspection PyUnresolvedReferences
            csle.clicked.connect(self._onCopyConsole)
            # Revision 29/11/2025 >
            data = QPushButton('Save Dataset', parent=self)
            data.setToolTip('Save the current dataset as a file in one of the\n'
                            'following formats: csv, json, LaTeX, txt, xlsx, PySisyphe xsheet')
            data.setObjectName('data')
            # noinspection PyUnresolvedReferences
            data.clicked.connect(self._onSaveDataset)
            btlyout.addWidget(cap)
            btlyout.addWidget(clip)
            btlyout.addWidget(screen)
            btlyout.addWidget(csle)
            btlyout.addWidget(data)
            btlyout.addStretch()
            cap.setVisible(capture)
            clip.setVisible(clipbrd)
            screen.setVisible(scrshot is not None)
            # < Revision 29/11/2025
            csle.setVisible(dataset and self._console is not None)
            # Revision 29/11/2025 >
            data.setVisible(dataset)
            # Tab
            if capture: lyout.addWidget(canvas)
            if dataset: lyout.addWidget(tree)
            lyout.addLayout(btlyout)
            widget = QWidget(parent=self)
            widget.setLayout(lyout)
            # < Revision 12/06/2025
            # self._tab.addTab(widget, title)
            # return self._tab.count() - 1
            index = self._tab.addTab(widget, title)
            return index
            # Revision 12/06/2025 >
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

    def newDescriptiveStatisticsTab(self,
                                    labels: list[str],
                                    data: list[ndarray],
                                    title: str = '',
                                    units: str = '',
                                    decimals: int | None = None,
                                    capture: bool = True,
                                    clipbrd: bool = True,
                                    scrshot: ScreenshotsGridWidget | None = None,
                                    dataset: bool = True) -> int:
        """
        Create a new tab to display descriptive statistics.
        Calculates and displays statistics (min, max, mean, std, etc.) in a tree widget and shows a corresponding
        boxplot.

        Parameters
        ----------
        labels : list[str]
            Labels for the data series.
        data : list[ndarray]
            A list of numpy arrays containing the data.
        title : str, optional
            Base title for the tab.
        units : str, optional
            Units for the data values.
        decimals : int | None, optional
            Number of decimals for display. Auto-detected if None.
        capture : bool, optional
            If True, enables the figure canvas and save/copy buttons.
        clipbrd : bool, optional
            If True, enables the copy to clipboard button.
        scrshot : ScreenshotsGridWidget | None, optional
            A ScreenshotsGridWidget instance to enable copying to it.
        dataset : bool, optional
            If True, enables the tree widget and save dataset button.

        Returns
        -------
        int
            The index of the newly created tab.
        """
        title += ' descriptive statistics'
        index = self.newTab(title, capture, clipbrd, scrshot, dataset)
        if units == '': units = None
        else: units = [units] * len(labels)
        labels = [''] + labels
        self.setTreeWidgetHeaderLabels(index, labels, units, None)
        rows = ['Minimum',
                '5th percentile',
                '25th percentile',
                'Median',
                '75th percentile',
                '95th percentile',
                'Maximum',
                'Std deviation',
                'Mean',
                'Skewness',
                'Kurtosis']
        # TreeWidget
        stats = ndarray(shape=(len(rows), len(data)))
        for i in range(len(data)):
            r = describe(data[i])
            # noinspection PyUnresolvedReferences
            stats[0, i] = r.minmax[0]
            stats[1, i] = percentile(data, 5)
            stats[2, i] = percentile(data, 25)
            stats[3, i] = median(data)
            stats[4, i] = percentile(data, 75)
            stats[5, i] = percentile(data, 95)
            # noinspection PyUnresolvedReferences
            stats[6, i] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats[7, i] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats[8, i] = r.mean
            # noinspection PyUnresolvedReferences
            stats[9, i] = r.skewness
            # noinspection PyUnresolvedReferences
            stats[10, i] = r.kurtosis
        if decimals is None: decimals = self._getDecimals(data[0])[0]
        self.setTreeWidgetArray(index, stats, decimals, rows)
        # Figure
        fig = self._plotlist[index].figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ylabel = title
        if units is not None:
            if units[0] != '': ylabel += ' ({})'.format(units[0])
        ax.set_ylabel(ylabel)
        ax.boxplot(data, labels=labels[1:], showfliers=False)
        return index

    def newHistogramTab(self,
                        data: ndarray,
                        bins: int | None = 32,
                        cumulative: bool = False,
                        label: str = '',
                        units: str = '',
                        capture: bool = True,
                        clipbrd: bool = True,
                        scrshot: ScreenshotsGridWidget | None = None,
                        dataset: bool = True) -> int:
        """
        Create a new tab to display a histogram.

        Parameters
        ----------
        data : ndarray
            The 1D data to be plotted.
        bins : int | None, optional
            Number of histogram bins. Defaults to 32.
        cumulative : bool, optional
            If True, create a cumulative histogram. Defaults to False.
        label : str, optional
            Label for the data.
        units : str, optional
            Units for the data values.
        capture : bool, optional
            If True, enables the figure canvas and save/copy buttons.
        clipbrd : bool, optional
            If True, enables the copy to clipboard button.
        scrshot : ScreenshotsGridWidget | None, optional
            A ScreenshotsGridWidget instance to enable copying to it.
        dataset : bool, optional
            If True, enables the tree widget and save dataset button.

        Returns
        -------
        int
            The index of the newly created tab.
        """
        if cumulative: title = '{} cumulative histogram'.format(label)
        else: title = '{} histogram'.format(label)
        if len(data) > 10000: dataset = False
        index = self.newTab(title, capture, clipbrd, scrshot, dataset)
        # TreeWidget
        if units == '': units = None
        else: units = [units]
        self.setTreeWidgetHeaderLabels(index, [label], units, None)
        if len(data) <= 10000: self.setTreeWidgetArray(index, data, d=0)
        # Figure
        fig = self._plotlist[index].figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        xlabel = label
        if units is not None:
            if units[0] != '': xlabel += ' ({})'.format(units[0])
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Percent')
        if bins is None: bins = 'auto'
        ax.hist(data, bins, density=True, cumulative=cumulative, histtype='stepfilled')
        return index

    def newImageHistogramTab(self,
                             vol: SisypheVolume,
                             bins: int | None = 128,
                             cumulative: bool = False,
                             capture: bool = True,
                             clipbrd: bool = True,
                             scrshot: ScreenshotsGridWidget | None = None):
        """
        Create a new tab to display a histogram of a SisypheVolume.

        Parameters
        ----------
        vol : SisypheVolume
            The volume to analyze.
        bins : int | None, optional
            Number of histogram bins. Defaults to 128.
        cumulative : bool, optional
            If True, create a cumulative histogram. Defaults to False.
        capture : bool, optional
            If True, enables the figure canvas and save/copy buttons.
        clipbrd : bool, optional
            If True, enables the copy to clipboard button.
        scrshot : ScreenshotsGridWidget | None, optional
            A ScreenshotsGridWidget instance to enable copying to it.

        Returns
        -------
        int
            The index of the newly created tab.
        """
        if cumulative: title = '{} cumulative histogram'.format(vol.getName())
        else: title = '{} histogram'.format(vol.getName())
        index = self.newTab(title, capture, clipbrd, scrshot, True)
        if vol.acquisition.hasUnit(): units = [vol.acquisition.getUnit()]
        else: units = None
        data = vol.getNumpy().flatten()
        # Figure
        fig = self._plotlist[index].figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        xlabel = vol.getName()
        if units is not None:
            if units[0] != '': xlabel += ' ({})'.format(units[0])
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Count')
        if bins is None: bins = 'auto'
        h = ax.hist(data, bins, density=False, cumulative=cumulative, histtype='stepfilled')
        # y-axis limit to take into account background values
        m = data.mean()
        idx = where(h[1] > m)[0][0]
        m = max(h[0][idx:])
        ax.set_ylim(0, int(m * 3))
        # TreeWidget
        self.setTreeWidgetHeaderLabels(index, ['Intervals', vol.getName()], units, None)
        if cumulative: hh = (h[0] * vol.getNumberOfVoxels()).astype('int32')
        else: hh = h[0]
        if vol.isIntegerDatatype(): ff = '{:.1f}'
        else: ff = self._getDecimals(data)[1]
        ff = ff + ' ' + ff
        rows = [ff.format(h[1][i], h[1][i+1]) for i in range(len(h[0]))]
        self.setTreeWidgetArray(index, hh, d=0, rows=rows)
        return index

    def getTabCount(self) -> int:
        """
        Get the number of tabs in the dialog.

        Returns
        -------
        int
            The total number of tabs.
        """
        return self._tab.count()

    def getTreeWidget(self, index: str | int) -> QTreeWidget:
        """
        Get the tree widget from a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.

        Returns
        -------
        QTreeWidget
            The tree widget from the specified tab.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                return self._treelist[index]
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def hideTree(self, index: str | int) -> None:
        """
        Hide the tree widget in a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                self._treelist[index].setVisible(False)
                # < Revision 05/06/2025
                # hide save dataset button
                button = self._tab.widget(index).findChild(QPushButton, 'data')
                if button is not None: button.setVisible(False)
                # Revision 05/06/2025 >
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def showTree(self, index: str | int) -> None:
        """
        Show the tree widget in a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                self._treelist[index].setVisible(True)
                # < Revision 05/06/2025
                # show save dataset button
                button = self._tab.widget(index).findChild(QPushButton, 'data')
                if button is not None: button.setVisible(True)
                # Revision 05/06/2025 >
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def isTreeVisible(self, index: str | int) -> bool:
        """
        Check if the tree widget in a specific tab is visible.

        Parameters
        ----------
        index : str | int
            The tab index or title.

        Returns
        -------
        bool
            True if the tree widget is visible, False otherwise.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                return self._treelist[index].isVisible()
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getFigure(self, index: str | int) -> Figure:
        """
        Get the Matplotlib figure from a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.

        Returns
        -------
        Figure
            The Matplotlib figure from the specified tab.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                return self._plotlist[index].figure
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def hideFigure(self, index:  str | int) -> None:
        """
        Hide the figure canvas in a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                self._plotlist[index].setVisible(False)
                # < Revision 05/06/2025
                # hide save bitmap, copy to screenshot manager and copy to clipboard buttons
                button = self._tab.widget(index).findChild(QPushButton, 'cap')
                if button is not None: button.setVisible(False)
                button = self._tab.widget(index).findChild(QPushButton, 'clip')
                if button is not None: button.setVisible(False)
                if self._scrshot[index] is not None:
                    button = self._tab.widget(index).findChild(QPushButton, 'screen')
                    if button is not None: button.setVisible(False)
                # Revision 05/06/2025 >
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def showFigure(self, index: str | int) -> None:
        """
        Show the figure canvas in a specific tab.

        Parameters
        ----------
        index : str | int
            The tab index or title.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                self._plotlist[index].setVisible(True)
                # < Revision 05/06/2025
                # show save bitmap and copy to clipboard buttons
                button = self._tab.widget(index).findChild(QPushButton, 'cap')
                if button is not None: button.setVisible(True)
                button = self._tab.widget(index).findChild(QPushButton, 'clip')
                if button is not None: button.setVisible(True)
                if self._scrshot[index] is not None:
                    button = self._tab.widget(index).findChild(QPushButton, 'screen')
                    if button is not None: button.setVisible(True)
                # Revision 05/06/2025 >
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def isFigureVisible(self, index: str | int) -> bool:
        """
        Check if the figure canvas in a specific tab is visible.

        Parameters
        ----------
        index : str | int
            The tab index or title.

        Returns
        -------
        bool
            True if the figure is visible, False otherwise.
        """
        if isinstance(index, str):
            for i in range(self._tab.count()):
                if self._tab.tabText(i) == index: index = i
                break
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                return self._plotlist[index].isVisible()
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def setTreeWidgetHeaderLabels(self,
                                  index: int,
                                  labels: list[str],
                                  units: list[str] | None = None,
                                  charts: list[str] | None = None) -> None:
        """
        Set the header labels, units, and chart types for a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        labels : list[str]
            List of column header labels.
        units : list[str] | None, optional
            List of units for each column.
        charts : list[str] | None, optional
            List of chart types for each column ('bar', 'plot', 'boxplot', 'pie').
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(labels, list):
                    labels = [str(v) for v in labels]
                    tree = self._treelist[index]
                    tree.setHeaderLabels(labels)
                    c = tree.headerItem().columnCount()
                    if units is None: units = [''] * c
                    if len(units) < c: units += [''] * (c - len(units))
                    if charts is None: charts = [''] * c
                    if len(charts) < c: charts += [''] * (c - len(charts))
                    for i in range(c):
                        # noinspection PyUnresolvedReferences
                        tree.headerItem().setData(i, Qt.UserRole, {'unit': units[i], 'chart': charts[i]})
                        # noinspection PyUnresolvedReferences
                        tree.headerItem().setTextAlignment(i, Qt.AlignCenter)
                    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
                    tree.header().setSectionsClickable(False)
                    tree.header().setSortIndicatorShown(False)
                    tree.header().setStretchLastSection(False)
                    tree.setAlternatingRowColors(True)
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    # noinspection PyUnresolvedReferences
    def addTreeWidgetRow(self,
                         index: int,
                         row: list | tuple | ndarray,
                         d: int | None = None,
                         align: int = Qt.AlignCenter) -> None:
        """
        Add a new row of data to a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        row : list | tuple | ndarray
            The data for the new row.
        d : int | None, optional
            Number of decimals for formatting float values. Auto-detected if None.
        align : int (optional)
            set text alignment (default center alignment, Qt.AlignCenter).
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(row, (list, tuple, ndarray)):
                    if d is None: d = self._getDecimals(row)[0]
                    tree = self._treelist[index]
                    n = tree.headerItem().columnCount()
                    if len(row) < n: n = len(row)
                    f = '{:.' + str(d) + 'f}'
                    item = QTreeWidgetItem(tree)
                    for i in range(n):
                        if isinstance(row[i], float):
                            if d == 0:
                                # noinspection PyTypeChecker
                                item.setText(i, int(row[i]))
                            else: item.setText(i, f.format(row[i]))
                        elif isinstance(row[i], str): item.setText(i, row[i])
                        elif isinstance(row[i], (list, tuple)):
                            buff = list()
                            for r in row[i]:
                                if isinstance(r, float): buff.append(f.format(r))
                                else: buff.append(r)
                            item.setText(i, ' '.join(buff))
                        else: item.setText(i, str(row[i]))
                        # < Revision 16/02/2026
                        # item.setTextAlignment(i, Qt.AlignCenter)
                        # noinspection PyUnresolvedReferences
                        item.setTextAlignment(i, align)
                        # Revision 16/02/2026 >
                    tree.addTopLevelItem(item)
                else: raise TypeError('row parameter type {} is not list, tuple or ndarray.'.format(type(row)))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setColumnChart(self, index: int, col: int, chart: str = '') -> None:
        """
        Set the chart type for a specific column in a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index.
        chart : str, optional
            The chart type ('bar', 'plot', 'boxplot', 'pie'). Defaults to ''.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    # noinspection PyUnresolvedReferences
                    data = tree.headerItem().data(col, Qt.UserRole)
                    data['chart'] = chart
                    # noinspection PyUnresolvedReferences
                    tree.headerItem().setData(col, Qt.UserRole, data)
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setColumnUnit(self, index: int, col: int, unit: str = '') -> None:
        """
        Set the unit for a specific column in a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index.
        unit : str, optional
            The unit string. Defaults to ''.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    # noinspection PyUnresolvedReferences
                    data = tree.headerItem().data(col, Qt.UserRole)
                    data['unit'] = unit
                    # noinspection PyUnresolvedReferences
                    tree.headerItem().setData(col, Qt.UserRole, data)
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def clearColumnCharts(self, index: int) -> None:
        """
        Clear the chart type for all columns in a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                for i in range(n):
                    # noinspection PyUnresolvedReferences
                    data = tree.headerItem().data(i, Qt.UserRole)
                    data['chart'] = ''
                    # noinspection PyUnresolvedReferences
                    tree.headerItem().setData(i, Qt.UserRole, data)
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def clearColumnUnits(self, index: int) -> None:
        """
        Clear the units for all columns in a tree widget.

        Parameters
        ----------
        index : int
            The tab index.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                for i in range(n):
                    # noinspection PyUnresolvedReferences
                    data = tree.headerItem().data(i, Qt.UserRole)
                    data['unit'] = ''
                    # noinspection PyUnresolvedReferences
                    tree.headerItem().setData(i, Qt.UserRole, data)
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartBarFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
        Generate and display a bar chart from a tree widget column.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index to plot.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if not self._plotlist[index].isVisible(): self._plotlist[index].setVisible(True)
                tree = self._treelist[index]
                nv = 0
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    vd = dict()
                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        v = item.text(col)
                        v = v.split(' ')
                        nv = len(v)
                        if nv == 1: vd[item.text(0)] = float(v[0])
                        elif nv > 1: vd[item.text(0)] = [float(i) for i in v]
                        else: return
                    fig = self._plotlist[index].figure
                    fig.clear()
                    # noinspection PyUnresolvedReferences
                    unit = tree.headerItem().data(col, Qt.UserRole)['unit']
                    if nv == 1:
                        ax = fig.add_subplot(111)
                        ylabel = tree.headerItem().text(col)
                        if unit != '': ylabel += ' ({})'.format(unit)
                        ax.set_ylabel(ylabel)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        rects = ax.bar(list(vd.keys()), list(vd.values()))
                        ax.bar_label(rects, padding=3)
                    elif 1 < nv < 10:
                        geo = (111, 121, 131, 221, 231, 231, 331, 331, 331)
                        for i in range(nv):
                            ax = fig.add_subplot(geo[nv-1] + i)
                            ylabel = '{}#{}'.format(tree.headerItem().text(col), i)
                            if unit != '': ylabel += ' ({})'.format(unit)
                            ax.set_ylabel(ylabel)
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)
                            values = [j[i] for j in vd.values()]
                            rects = ax.bar(list(vd.keys()), values)
                            ax.bar_label(rects, padding=3)
                    else: raise ValueError('')
                    # < Revision 23/03/2026
                    # migrate from matplotlib 3.6.3 to 3.10.8
                    # self._plotlist[index].draw()
                    self._plotlist[index].draw_idle()
                    # faster & non-blocking GUI
                    # Revision 23/03/2026 >
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartPlotFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
        Generate and display a line plot from a tree widget column.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index to plot.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if not self._plotlist[index].isVisible(): self._plotlist[index].setVisible(True)
                tree = self._treelist[index]
                nv = 0
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    vd = dict()
                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        v = item.text(col)
                        v = v.split(' ')
                        nv = len(v)
                        if nv == 1: vd[item.text(0)] = float(v[0])
                        elif nv > 1: vd[item.text(0)] = [float(i) for i in v]
                        else: return
                    fig = self._plotlist[index].figure
                    fig.clear()
                    ax = fig.add_subplot(111)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    if nv == 1:
                        ax.set_ylabel(tree.headerItem().text(col))
                        ax.plot(list(vd.keys()), list(vd.values()))
                    elif 1 < nv < 10:
                        for i in range(nv):
                            values = [j[i] for j in vd.values()]
                            ax.plot(list(vd.keys()), values, label=tree.headerItem().text(col) + '#{}'.format(i))
                    else: raise ValueError('')
                    # noinspection PyUnresolvedReferences
                    unit = tree.headerItem().data(col, Qt.UserRole)['unit']
                    ylabel = tree.headerItem().text(col)
                    if unit != '': ylabel += ' ({})'.format(unit)
                    ax.set_ylabel(ylabel)
                    ax.legend()
                    # < Revision 23/03/2026
                    # migrate from matplotlib 3.6.3 to 3.10.8
                    # self._plotlist[index].draw()
                    self._plotlist[index].draw_idle()
                    # faster & non-blocking GUI
                    # Revision 23/03/2026 >
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartBoxplotFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
        Generate and display a boxplot from a tree widget column.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index to plot.
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if not self._plotlist[index].isVisible(): self._plotlist[index].setVisible(True)
                tree = self._treelist[index]
                nv = 0
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    vd = dict()
                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        v = item.text(col)
                        v = v.split(' ')
                        nv = len(v)
                        if nv == 1: vd[item.text(0)] = float(v[0])
                        elif nv > 1: vd[item.text(0)] = [float(i) for i in v]
                        else: return
                    fig = self._plotlist[index].figure
                    fig.clear()
                    ax = fig.add_subplot(111)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    # noinspection PyUnresolvedReferences
                    unit = tree.headerItem().data(col, Qt.UserRole)['unit']
                    ylabel = tree.headerItem().text(col)
                    if unit != '': ylabel += ' ({})'.format(unit)
                    ax.set_ylabel(ylabel)
                    if nv == 1:
                        ax.boxplot(list(vd.values()), labels=[tree.headerItem().text(col)])
                    elif 1 < nv < 10:
                        values = list()
                        lb = list()
                        for i in range(nv):
                            values.append([j[i] for j in vd.values()])
                            lb.append(tree.headerItem().text(col) + '#{}'.format(i))
                        ax.boxplot(values, labels=lb)
                    else: raise ValueError('')
                    # < Revision 23/03/2026
                    # migrate from matplotlib 3.6.3 to 3.10.8
                    # self._plotlist[index].draw()
                    self._plotlist[index].draw_idle()
                    # faster & non-blocking GUI
                    # Revision 23/03/2026 >
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartPieFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
        Generate and display a pie chart from a tree widget column.

        Parameters
        ----------
        index : int
            The tab index.
        col : int
            The column index to plot.
        """

        def func(pct, vv):
            absolute = pct / 100. * sum(vv)
            return f"{pct:.1f}%\n({absolute:.1f})"

        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if not self._plotlist[index].isVisible(): self._plotlist[index].setVisible(True)
                tree = self._treelist[index]
                nv = 0
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    lb = list()
                    vd = dict()
                    for i in range(tree.topLevelItemCount()):
                        item = tree.topLevelItem(i)
                        lb.append(item.text(0))
                        v = item.text(col)
                        v = v.split(' ')
                        nv = len(v)
                        if nv == 1: vd[item.text(0)] = float(v[0])
                        elif nv > 1: vd[item.text(0)] = [float(i) for i in v]
                        else: return
                    fig = self._plotlist[index].figure
                    fig.clear()
                    if nv == 1:
                        ax = fig.add_subplot(111)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.set_title(tree.headerItem().text(col))
                        ax.pie(list(vd.values()), labels=lb, autopct=lambda pct: func(pct, list(vd.values())))
                    elif 1 < nv < 10:
                        geo = (111, 121, 131, 221, 231, 231, 331, 331, 331)
                        for i in range(nv):
                            ax = fig.add_subplot(geo[nv-1] + i)
                            ax.set_title(tree.headerItem().text(col) + '#{}'.format(i))
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)
                            values = [j[i] for j in vd.values()]
                            ax.pie(values, labels=lb, autopct=lambda pct: func(pct, values))
                    else: raise ValueError('')
                    # < Revision 23/03/2026
                    # migrate from matplotlib 3.6.3 to 3.10.8
                    # self._plotlist[index].draw()
                    self._plotlist[index].draw_idle()
                    # faster & non-blocking GUI
                    # Revision 23/03/2026 >
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    # noinspection PyUnresolvedReferences
    def setTreeWidgetArray(self,
                           index: int,
                           arr: ndarray | DataFrame,
                           d: int | None = None,
                           rows: list[str] | None = None,
                           align: int = Qt.AlignCenter) -> None:
        """
        Populate a tree widget from a NumPy array or pandas DataFrame.

        Parameters
        ----------
        index : int
            The tab index.
        arr : ndarray | DataFrame
            The data to populate the widget with.
        d : int | None, optional
            Number of decimals for formatting float values. Auto-detected if None.
        rows : list[str] | None, optional
            Labels for the rows. If provided, they are placed in the first column.
        align : int (optional)
            set text alignment (default center alignment, Qt.AlignCenter).
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(arr, DataFrame): arr = arr.to_numpy()
                if isinstance(arr, ndarray):
                    if arr.ndim == 1: arr = arr.reshape(len(arr), 1)
                    if arr.ndim == 2:
                        tree = self._treelist[index]
                        if rows is None: n = arr.shape[1]
                        else: n = arr.shape[1] + 1
                        if n != tree.headerItem().columnCount():
                            raise ValueError('Invalid header labels count.')
                        # decimals for each column
                        fd: list[str] = list()
                        for i in range(arr.shape[1]):
                            if d is None or d == 0: f = self._getDecimals(arr[:, i])[1]
                            else: f = '{:.' + str(d) + 'f}'
                            fd.append(f)
                        # TreeView filling
                        for i in range(arr.shape[0]):
                            item = QTreeWidgetItem(tree)
                            for j in range(0, n):
                                if rows is None: k = j
                                else:
                                    if j == 0:
                                        item.setText(j, rows[i])
                                        continue
                                    k = j - 1
                                if isinstance(arr[i, k], int): item.setText(j, arr[i, k])
                                elif isinstance(arr[i, k], float): item.setText(j, fd[k].format(arr[i, k]))
                                elif isinstance(arr[i, k], str): item.setText(j, arr[i, k])
                                else: item.setText(j, str(arr[i, k]))
                                # < Revision 16/02/2026
                                # item.setTextAlignment(j, Qt.AlignCenter)
                                # noinspection PyUnresolvedReferences
                                item.setTextAlignment(j, align)
                                # Revision 16/02/2026 >
                            tree.addTopLevelItem(item)
                else: raise TypeError('array parameter type {} is not ndarray.'.format(type(arr)))
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    # noinspection PyUnresolvedReferences
    def setTreeWidgetDict(self,
                          index: int,
                          arr: dict,
                          d: int | None = None,
                          align: int = Qt.AlignCenter):
        """
        Populate a tree widget from a dictionary.

        Parameters
        ----------
        index : int
            The tab index.
        arr : dict
            The data dictionary. Keys are used as headers, and values are lists of column data.
        d : int | None (optional)
            Number of decimals for formatting float values. Auto-detected if None.
        align : int (optional)
            set text alignment (default center alignment, Qt.AlignCenter).
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(arr, dict):
                    tree = self._treelist[index]
                    hdr = list(arr.keys())
                    c = len(hdr)
                    r = len(arr[hdr[0]])
                    self.setTreeWidgetHeaderLabels(index, hdr)
                    # decimals for each column
                    fd = dict()
                    for k in arr:
                        if d is None or d == 0: f = self._getDecimals(arr[k])[1]
                        else: f = '{:.' + str(d) + 'f}'
                        fd[k] = f
                    # TreeView filling
                    for i in range(r):
                        item = QTreeWidgetItem(tree)
                        for j in range(c):
                            k = hdr[j]
                            if isinstance(arr[k][i], int): item.setText(j, arr[k][i])
                            elif isinstance(arr[k][i], float): item.setText(j, fd[k].format(arr[k][i]))
                            elif isinstance(arr[k][i], str): item.setText(j, arr[k][i])
                            elif isinstance(arr[k][i], (list, tuple)):
                                buff = list()
                                for r in arr[k][i]:
                                    if isinstance(r, float): buff.append(fd[k].format(r))
                                    elif isinstance(r, int): buff.append(str(r))
                                    elif isinstance(r, str): buff.append(r)
                                    else: raise ValueError('dict element type {} is not int, float or str.'.format(type(r)))
                                item.setText(j, ' '.join(buff))
                            else: item.setText(j, str(arr[k][i]))
                            # < Revision 16/02/2026
                            # item.setTextAlignment(j, Qt.AlignCenter)
                            # noinspection PyUnresolvedReferences
                            item.setTextAlignment(j, align)
                            # Revision 16/02/2026 >
                        tree.addTopLevelItem(item)
                else: raise TypeError('array parameter type {} is not dict.'.format(type(arr)))
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def clear(self) -> None:
        """
        Clear all tabs and data from the dialog.
        """
        self._tab.clear()
        self._plotlist = list()
        self._treelist = list()
        self._scrshot = list()

    # < Revision 18/09/2025
    # add showEvent method, Adjust the size of the dialog box to fit the content
    def showEvent(self, a0):
        """
        Reimplementation of QWidget.showEvent to adjust dialog size on show.

        Parameters
        ----------
        a0 : QShowEvent
            The show event.
        """
        super().showEvent(a0)
        self.adjustSize()
    # <Revision 18/09/2025 >
