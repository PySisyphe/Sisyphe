"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - scipy, scientific computing, https://scipy.org/
"""

from sys import platform

from os import getcwd
from os import remove
from os import chdir

from os.path import join
from os.path import exists
from os.path import splitext
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
from PyQt5.QtWidgets import QApplication

from scipy.stats import describe

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget

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

    Generic dialog o display statistical results.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogGenericResults

    Creation: 25/11/2022
    Last revision: 12/06/2025
    """

    # Special method

    """
     Private attributes

    _plotlist   list[Figure]
    _treelist   list[TreeViewWidget]
    _scrshot    list[ScreenshotsGridWidget]
    _tab        QTabWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._plotlist = list()
        self._treelist = list()
        self._scrshot = list()

        self._tab = QTabWidget()

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
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

    # Private methods

    def _onSaveBitmap(self):
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

    def _onSaveDataset(self):
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
                    elif ext == 'xlsx': sheet.saveXLSX(filename)
                    elif ext == 'xsheet': sheet.save(filename)
                    else: raise ValueError('{} format is not supported.'.format(ext))
                except Exception as err:
                    messageBox(self, 'Save Dataset', text='error: {}'.format(err))

    def _onSelectionChanged(self, item):
        index = self._tab.currentIndex()
        if self.isFigureVisible(index):
            c = item.treeWidget().currentIndex().column()
            if c > 0:
                data = self._treelist[index].headerItem().data(c, Qt.UserRole)['chart']
                if data == 'bar': self.chartBarFromTreeWidgetColumn(index, c)
                elif data == 'plot': self.chartPlotFromTreeWidgetColumn(index, c)
                elif data == 'boxplot': self.chartBoxplotFromTreeWidgetColumn(index, c)
                elif data == 'pie': self.chartPieFromTreeWidgetColumn(index, c)

    def _getDataFrame(self, index):
        if isinstance(index, int):
            df = dict()
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                hdrs = list()
                for i in range(tree.columnCount()):  # cols
                    hdr = tree.headerItem().text(i)
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

    def autoSize(self, index: int) -> None:
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
            title       str, title of the tab
            capture     bool, to display save bitmap button if true
            clipbrd     bool, to display copy to clipboard button if true
            scrshot     ScreenshotsGridWidget, to display copy to screenshots
            dataset     bool, to display dataset TreeView/save dataset button if true

            return      int, index of the new tab
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
            cap.setObjectName('cap')
            # noinspection PyUnresolvedReferences
            cap.clicked.connect(self._onSaveBitmap)
            clip = QPushButton('Copy to clipboard', parent=self)
            clip.setObjectName('clip')
            # noinspection PyUnresolvedReferences
            clip.clicked.connect(self._onCopyClipboard)
            screen = QPushButton('Copy to screenshots',parent=self)
            screen.setObjectName('screen')
            # noinspection PyUnresolvedReferences
            screen.clicked.connect(self._onCopyScreenshots)
            self._scrshot.append(scrshot)
            data = QPushButton('Save Dataset', parent=self)
            data.setObjectName('data')
            # noinspection PyUnresolvedReferences
            data.clicked.connect(self._onSaveDataset)
            btlyout.addWidget(cap)
            btlyout.addWidget(clip)
            btlyout.addWidget(screen)
            btlyout.addWidget(data)
            btlyout.addStretch()
            cap.setVisible(capture)
            clip.setVisible(clipbrd)
            screen.setVisible(scrshot is not None)
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
        return self._tab.count()

    def getTreeWidget(self, index: str | int) -> QTreeWidget:
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
            index   int, tab index
            labels  list[str], list of columns labels displayed in TreeWidget header
            units   list[str], list of columns units
            charts  list[str], list of columns chart type (in ['bar', 'plot', 'boxplot', 'pie', ''])
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
                        tree.headerItem().setData(i, Qt.UserRole, {'unit': units[i], 'chart': charts[i]})
                        tree.headerItem().setTextAlignment(i, Qt.AlignCenter)
                    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
                    tree.header().setSectionsClickable(False)
                    tree.header().setSortIndicatorShown(False)
                    tree.header().setStretchLastSection(False)
                    tree.setAlternatingRowColors(True)
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def addTreeWidgetRow(self, index: int, row: list | tuple | ndarray, d: int | None = None) -> None:
        """
            index   int, tab number
            row     list | tuple | ndarray, row values
            d       int, floating values precision
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
                            if d == 0: item.setText(i, int(row[i]))
                            else: item.setText(i, f.format(row[i]))
                        elif isinstance(row[i], str): item.setText(i, row[i])
                        elif isinstance(row[i], (list, tuple)):
                            buff = list()
                            for r in row[i]:
                                if isinstance(r, float): buff.append(f.format(r))
                                else: buff.append(r)
                            item.setText(i, ' '.join(buff))
                        else: item.setText(i, str(row[i]))
                        item.setTextAlignment(i, Qt.AlignCenter)
                    tree.addTopLevelItem(item)
                else: raise TypeError('row parameter type {} is not list, tuple or ndarray.'.format(type(row)))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setColumnChart(self, index: int, col: int, chart: str = '') -> None:
        """
            chart   str, type of chart used to display values in a column
                         chart types are 'bar', 'plot', 'boxplot', 'pie'
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    data = tree.headerItem().data(col, Qt.UserRole)
                    data['chart'] = chart
                    tree.headerItem().setData(col, Qt.UserRole, data)
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setColumnUnit(self, index: int, col: int, unit: str = '') -> None:
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                if 0 < col < n:
                    data = tree.headerItem().data(col, Qt.UserRole)
                    data['unit'] = unit
                    tree.headerItem().setData(col, Qt.UserRole, data)
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def clearColumnCharts(self, index: int) -> None:
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                for i in range(n):
                    data = tree.headerItem().data(i, Qt.UserRole)
                    data['chart'] = ''
                    tree.headerItem().setData(i, Qt.UserRole, data)
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def clearColumnUnits(self, index: int) -> None:
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                tree = self._treelist[index]
                n = tree.headerItem().columnCount()
                for i in range(n):
                    data = tree.headerItem().data(i, Qt.UserRole)
                    data['unit'] = ''
                    tree.headerItem().setData(i, Qt.UserRole, data)
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartBarFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
            index   int, tab number
            col     int, column number
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
                    self._plotlist[index].draw()
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartPlotFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
            index   int, tab number
            col     int, column number
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
                    unit = tree.headerItem().data(col, Qt.UserRole)['unit']
                    ylabel = tree.headerItem().text(col)
                    if unit != '': ylabel += ' ({})'.format(unit)
                    ax.set_ylabel(ylabel)
                    ax.legend()
                    self._plotlist[index].draw()
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartBoxplotFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
            index   int, tab number
            col     int, column number
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
                    self._plotlist[index].draw()
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def chartPieFromTreeWidgetColumn(self, index: int, col: int) -> None:
        """
            index   int, tab number
            col     int, column number
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
                    self._plotlist[index].draw()
                else: raise ValueError('col parameter value {} is out of range.'.format(col))
            else: raise ValueError('index parameter value {} is out of range.'.format(index))
        else: raise TypeError('index parameter type {} is not int.'.format(type(index)))

    def setTreeWidgetArray(self,
                           index: int,
                           arr: ndarray | DataFrame,
                           d: int | None = None,
                           rows: list[str] | None = None) -> None:
        """
            index   int, tab number
            arr     ndarray, data
            d       int, decimals
            rows    list[str], row labels (default None)
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
                                item.setTextAlignment(j, Qt.AlignCenter)
                            tree.addTopLevelItem(item)
                else: raise TypeError('array parameter type {} is not ndarray.'.format(type(arr)))
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def setTreeWidgetDict(self, index: int, arr: dict, d: int | None = None):
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
                            item.setTextAlignment(j, Qt.AlignCenter)
                        tree.addTopLevelItem(item)
                else: raise TypeError('array parameter type {} is not dict.'.format(type(arr)))
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def clear(self) -> None:
        self._tab.clear()
        self._plotlist = list()
        self._treelist = list()
        self._scrshot = list()
