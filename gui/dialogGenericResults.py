"""
    External packages/modules

        Name            Link                                                        Usage

        Matplotlib      https://matplotlib.org/                                     Plotting library
        Numpy           https://numpy.org/                                          Scientific computing
        pandas          https://pandas.pydata.org/                                  Data analysis and manipulation tool
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os import remove
from os.path import join
from os.path import exists
from os.path import splitext

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import ndarray
from numpy import sum

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

from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget

__all__ = ['DialogGenericResults']

"""
    Class hierarchy

        QDialog -> DialogGenericResults
"""


class DialogGenericResults(QDialog):
    """
         DialogGenericResults class

         Description

             Generic dialog box to display statistical results.

         Inheritance

             QDialog -> DialogGenericResults

         Private attributes

            _plotlist   list of matplotlib Figure
            _treelist   list of TreeViewWidget

         Public methods

            autoSize(index=int)
            int = newTab(title=str, capture=bool, clipbrd=bool, scrshot=ScreenshotsGridWidget, dataset=bool)
            int = getTabCount()
            QTreeWidget = getTreeWidget(index=int or str)           int = tab index or str = tab text
            hideTree(index=int | str)                               int = tab index or str = tab text
            showTree(index=int | str)                               int = tab index or str = tab text
            bool = isTreeVisible(index=int | str)
            Figure = getFigure(index=int or str)                    int = tab index or str = tab text
            hideFigure(index=int | str)                             int = tab index or str = tab text
            showFigure(index=int | str)                             int = tab index or str = tab text
            bool = isFigureVisible(index=int | str)
            setTreeWidgetHeaderLabels(index=int, labels=list[str], units=list[str], charts=list[str])
            addTreeWidgetRow(index=int, row=list or tuple or ndarray, d=int)
            setTreeWidgetArray(index=int, arr=ndarray, d=int)
            setTreeWidgetDict(index=int, arr=dict, d=int)
            setColumnChart(index=int, col=int, chart=str)
            setColumnUnit(index=int, col=int, unit=str)
            clearColumnCharts(index=int)
            clearColumnUnits(index=int)
            chartBarFromTreeWidgetColumn(index=int, col=int)
            chartPlotFromTreeWidgetColumn(index=int, col=int)
            chartBoxplotFromTreeWidgetColumn(index=int, col=int)
            chartPieFromTreeWidgetColumn(index=int, col=int)
            clear()

            inherited QDialog methods

        Revisions:

            24/09/2023  clear() method bugfix
     """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._plotlist = list()
        self._treelist = list()
        self._scrshot = list()

        self._tab = QTabWidget()

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        lyout.addWidget(ok)
        lyout.addStretch()

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
                try: fig.savefig(filename)
                except Exception as err: QMessageBox.warning(self, 'Save capture', '{}'.format(err))

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
                    QMessageBox.warning(self, 'Copy capture to clipboard', 'error: {}'.format(err))
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
                    QMessageBox.warning(self, 'Save Dataset', 'error: {}'.format(err))

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
                        df[hdrs[j]].append(float(item.text(j)))
                return DataFrame(df)
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

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
            scrshot     ScreenshotsGridWidget, to display copy to screenshots button if true
            dataset     bool, to display save dataset button if true

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
            # Init TreeViewWidget
            tree = QTreeWidget()
            tree.setSelectionBehavior(QTreeWidget.SelectColumns)
            tree.itemClicked.connect(self._onSelectionChanged)
            self._treelist.append(tree)
            # Init Buttons
            btlyout = QHBoxLayout()
            btlyout.setSpacing(10)
            btlyout.setContentsMargins(0, 0, 0, 0)
            cap = QPushButton('Save bitmap')
            cap.clicked.connect(self._onSaveBitmap)
            clip = QPushButton('Copy to clipboard')
            clip.clicked.connect(self._onCopyClipboard)
            screen = QPushButton('Copy to screenshots')
            screen.clicked.connect(self._onCopyScreenshots)
            self._scrshot.append(scrshot)
            data = QPushButton('Save Dataset')
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
            lyout.addWidget(canvas)
            lyout.addWidget(tree)
            lyout.addLayout(btlyout)
            widget = QWidget()
            widget.setLayout(lyout)
            self._tab.addTab(widget, title)
            return self._tab.count() - 1
        else: raise TypeError('parameter type {} is not str.'.format(type(title)))

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

    def addTreeWidgetRow(self, index: int, row: list | tuple | ndarray, d: int = 2) -> None:
        """
            index   int, tab number
            row     list | tuple | ndarray, row values
            d       int, floating values precision
        """
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(row, (list, tuple, ndarray)):
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
                        ax.set_xlabel('Meshes')
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
                            ax.set_xlabel('Meshes')
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
                    ax.set_xlabel('Meshes')
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

        def func(pct, v):
            absolute = pct / 100. * sum(v)
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

    def setTreeWidgetArray(self, index, arr, d=1):
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(arr, ndarray):
                    if arr.ndim == 2:
                        tree = self._treelist[index]
                        n = tree.headerItem().columnCount()
                        if arr.shape[1] < n: n = arr.shape[1]
                        f = '{:.' + str(d) + 'f}'
                        for i in range(arr.shape[0]):
                            item = QTreeWidgetItem(tree)
                            for j in range(n):
                                if isinstance(arr[i, j], float):
                                    if d == 0: item.setText(i, int(arr[i, j]))
                                    else: item.setText(i, f.format(arr[i, j]))
                                elif isinstance(arr[i, j], str): item.setText(i, arr[i, j])
                                elif isinstance(arr[i, j], (list, tuple)):
                                    buff = list()
                                    for r in arr[i, j]:
                                        if isinstance(r, float): buff.append(f.format(r))
                                        else: buff.append(r)
                                    item.setText(i, ' '.join(buff))
                                else: item.setText(i, str(arr[i, j]))
                                item.setTextAlignment(j, Qt.AlignCenter)
                            tree.addTopLevelItem(item)
                else: raise TypeError('array parameter type {} is not ndarray.'.format(type(arr)))
            else: raise ValueError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def setTreeWidgetDict(self, index, arr, d=1):
        if isinstance(index, int):
            if 0 <= index < self._tab.count():
                if isinstance(arr, dict):
                    tree = self._treelist[index]
                    hdr = list(arr.keys())
                    c = len(hdr)
                    r = len(arr[hdr[0]])
                    self.setTreeWidgetHeaderLabels(index, hdr)
                    f = '{:.' + str(d) + 'f}'
                    for i in range(r):
                        item = QTreeWidgetItem(tree)
                        for j in range(c):
                            if isinstance(arr[hdr[j]][i], float):
                                if d == 0: item.setText(i, int(arr[hdr[j]][i]))
                                else: item.setText(i, f.format(arr[hdr[j]][i]))
                            elif isinstance(arr[hdr[j]][i], str): item.setText(i, arr[hdr[j]][i])
                            elif isinstance(arr[hdr[j]][i], (list, tuple)):
                                buff = list()
                                for r in arr[hdr[j]][i]:
                                    if isinstance(r, float): buff.append(f.format(r))
                                    else: buff.append(r)
                                item.setText(i, ' '.join(buff))
                            else: item.setText(i, str(arr[hdr[j]][i]))
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


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    main = DialogGenericResults()
    main.newTab('Test1')
    main.newTab('Test2')
    main.show()
    app.exec_()
    exit()
