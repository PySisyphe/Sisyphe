"""
External packages/modules
-------------------------

    - Matplotlib, Graph tool, https://matplotlib.org/
    - Numpy, Scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from os import getcwd
from os import chdir
from os import remove

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import splitext

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import zeros

from pandas import DataFrame
from pandas import concat

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.gui.dialogFromXml import DialogFromXml
from Sisyphe.widgets.basicWidgets import messageBox

__all__ = ['SheetWidget',
           'SheetStatisticsWidget',
           'SheetChartWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> SheetWidget
              -> SheetStatisticsWidget -> SheetChartWidget              
"""

class SheetWidgetEditingDelegate(QItemDelegate):

    def __init__(self, sheet=None, decimals=1, parent=None):
        super().__init__(parent)

        self._sheet = None
        self._decimals = decimals
        if isinstance(sheet, SisypheSheet): self._sheet = sheet

    def setModelData(self, editor, model, index):
        fmt = '{' + ':.{}f'.format(self._decimals) + '}'

        def floatToStr(vf):
            try: return fmt.format(vf)
            except: return vf

        if self._sheet is not None:
            r = list(self._sheet.index)[index.row()]
            c = list(self._sheet.columns)[index.column() - 1]
            try:
                v = float(editor.text())
                self._sheet.loc[r, c] = v
            except:
                v = self._sheet.loc[r, c]
            editor.setText(floatToStr(v))
        super().setModelData(editor, model, index)

    def setEditorData(self, editor, index):
        if self._sheet is not None:
            r = list(self._sheet.index)[index.row()]
            c = list(self._sheet.columns)[index.column() - 1]
            editor.setText(str(self._sheet.loc[r, c]))
        super().setEditorData(editor, index)

    def setSheet(self, sheet):
        if isinstance(sheet, SisypheSheet): self._sheet = sheet
        else: raise TypeError('parameter type {} is not SisypheSheet.'.format(type(sheet)))

    def setDecimals(self, decimals):
        if isinstance(decimals, int): self._decimals = decimals
        else: raise TypeError('parameter type {} is not int.'.format(type(decimals)))


class SheetWidget(QWidget):
    """
    SheetWidget class

    Description
    ~~~~~~~~~~~

    Widget to display SisypheSheet

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SheetWidget
    """

    # Custom Qt Signal

    SheetChanged = pyqtSignal()

    # Special method

    """
    Private attributes

    _sheet      SisypheSheet
    _decimals   int
    """

    def __init__(self, sheet=None, title='', parent=None):
        super().__init__(parent)

        self._decimals = 1
        self._editable = False
        self._delegate = SheetWidgetEditingDelegate()

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._tree = QTreeWidget()
        self._tree.setItemDelegate(self._delegate)
        self._layout.addWidget(self._tree)
        self._sheet = SisypheSheet()
        self._title = title

        if isinstance(sheet, SisypheSheet):
            self.setSheet(sheet)

        # Buttons

        self._load = QPushButton('Open')
        self._load.setToolTip('open datasheet in XSHEET, CSV, JSON, TXT or XLSX format')
        self._save = QPushButton('Save')
        self._save.setToolTip('save datasheet to XSHEET, CSV, JSON, LATEX, MATFILE, TXT or XLSX format')
        self._copy = QPushButton('Copy')
        self._copy.setToolTip('Copy sheet to clipboard')
        # noinspection PyUnresolvedReferences
        self._load.clicked.connect(lambda dummy: self.load())
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(lambda dummy: self.save())
        # noinspection PyUnresolvedReferences
        self._copy.clicked.connect(self.copyToClipboard)

        self._btlyout = QHBoxLayout()
        self._btlyout.setContentsMargins(0, 0, 0, 0)
        self._btlyout.setSpacing(5)
        self._btlyout.addWidget(self._load)
        self._btlyout.addWidget(self._save)
        self._btlyout.addWidget(self._copy)
        self._btlyout.addStretch()
        self._layout.addLayout(self._btlyout)

    # Private methods

    def _initTreeWidget(self):

        fmt = '{' + ':.{}f'.format(self._decimals) + '}'

        def floatToStr(v):
            try: return fmt.format(v)
            except: return v

        if not self.isEmpty() and self._sheet.size > 0:
            self._tree.clear()
            hlabels = [str(v) for v in list(self._sheet.columns)]
            hlabels.insert(0, '')
            self._tree.setHeaderLabels(hlabels)
            for j in range(self._tree.headerItem().columnCount()):
                self._tree.headerItem().setTextAlignment(j, Qt.AlignCenter)
            self._tree.header().setStretchLastSection(False)
            self._tree.header().setSectionResizeMode(QHeaderView.Stretch)
            for row in self._sheet.index:
                item = QTreeWidgetItem(self._tree)
                item.setText(0, str(row))
                item.setTextAlignment(0, Qt.AlignCenter)
                values = list(self._sheet.loc[row])
                for j in range(len(values)):
                    item.setText(j+1, floatToStr(values[j]))
                    item.setTextAlignment(j+1, Qt.AlignCenter)
                if self.isEditable(): item.setFlags(item.flags() | Qt.ItemIsEditable)
                else: item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._tree.addTopLevelItem(item)
            self._delegate.setSheet(self._sheet)
            self._delegate.setDecimals(self._decimals)
            # noinspection PyUnresolvedReferences
            self.SheetChanged.emit()

    # Public methods

    def isEmpty(self):
        return self._sheet is None

    def setDecimals(self, d=1):
        if isinstance(d, int):
            self._decimals = 1
            self._initTreeWidget()
        else: raise TypeError('parameter type {} is not str.'.format(type(d)))

    def setDict(self, data, orient):
        self._sheet.from_dict(data, orient=orient)
        self._initTreeWidget()

    def setSheet(self, sheet):
        if isinstance(sheet, SisypheSheet):
            self._sheet = sheet
            self._initTreeWidget()
        else: raise TypeError('parameter type {} is not SisypheSheet.'.format(type(sheet)))

    def newSheet(self, cols, rows, cnames=None, rnames=None):
        if cnames is not None:
            if not len(cnames) == cols: raise ValueError('incorrect number of elements in cnames parameter.')
        if rnames is not None:
            if not len(rnames) == rows: raise ValueError('incorrect number of elements in rnames parameter.')
        array = zeros(shape=(rows, cols))
        self._sheet = SisypheSheet(array, columns=cnames, index=rnames)
        self._initTreeWidget()

    def newColumn(self, name, values=None):
        if values is None: values = [0.0] * self._sheet.index
        if len(values) == len(self._sheet.index):
            self._sheet[name] = values
            self._initTreeWidget()
        else: raise ValueError('incorrect number of element in values parameter.')

    def newRow(self, name, values=None):
        if values is None: values = [0.0] * len(self._sheet.columns)
        if len(values) == len(self._sheet.columns):
            values = DataFrame(values).T
            values.index = [name]
            self._sheet = concat((self._sheet, values))
            self._initTreeWidget()
        else: raise ValueError('incorrect number of element in values parameter.')

    def removeColumn(self, name):
        del self._sheet[name]
        self._initTreeWidget()

    def removeRow(self, name):
        self._sheet.drop(name)
        self._initTreeWidget()

    def getSheet(self):
        return self._sheet

    def clearSheet(self):
        self._tree.clear()
        del self._sheet
        self._sheet = None

    def setEditable(self, v):
        if isinstance(v, bool):
            self._editable = v
            self._initTreeWidget()
            if v: self._tree.setToolTip('Double-click to edit')
            else: self._tree.setToolTip('')
        else: raise TypeError('parameter type {} is not bool'.format(v))

    def isEditable(self):
        return self._editable

    def setTitle(self, title):
        if isinstance(title, str): self._title = title
        else: raise TypeError('parameter type  is not str.'.format(type(title)))

    def getTitle(self):
        return self._title

    def load(self, filename=''):
        if isinstance(filename, str):
            if not exists(filename):
                filename = QFileDialog.getOpenFileName(self, 'Open ', filename,
                                                       filter='CSV (*.csv);;JSON (*.json);;TXT (*.txt);;'
                                                              'XLSX (*.xlsx);;XSHEET (*.xsheet)',
                                                       initialFilter='XSHEET (*.xsheet)')[0]
                QApplication.processEvents()
            if filename != '':
                chdir(dirname(filename))
                ext = splitext(filename)[1].lower()
                if ext == '.xsheet': self._sheet = self._sheet.load(filename)
                elif ext == '.csv': self._sheet = self._sheet.loadCSV(filename)
                elif ext == '.json': self._sheet = self._sheet.loadJSON(filename)
                elif ext == '.txt': self._sheet = self._sheet.loadTXT(filename)
                elif ext == '.xlsx': self._sheet = self._sheet.loadXLSX(filename)
                self._initTreeWidget()

    def save(self, filename=''):
        if not self.isEmpty():
            if isinstance(filename, str):
                if filename == '':
                    filename = QFileDialog.getSaveFileName(self, 'Save ', filename,
                                                           filter='CSV (*.csv);;JSON (*.json);;LATEX (+.tex);;'
                                                                  'MATFILE (*.mat);;TXT (*.txt);;XLSX (*.xlsx);;'
                                                                  'XSHEET (*.xsheet)',
                                                           initialFilter='XSHEET (*.xsheet)')[0]
                    QApplication.processEvents()
            if filename != '':
                chdir(dirname(filename))
                ext = splitext(filename)[1]
                if ext == '.xsheet': self._sheet.save(filename)
                elif ext == '.csv': self._sheet.saveCSV(filename)
                elif ext == '.json': self._sheet.saveJSON(filename)
                elif ext == '.mat': self._sheet.saveMATFILE(filename)
                elif ext == '.tex': self._sheet.saveLATEX(filename)
                elif ext == '.txt': self._sheet.saveTXT(filename)
                elif ext == '.xlsx': self._sheet.saveXLSX(filename)

    def setButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._load.setVisible(v)
            self._save.setVisible(v)
            self._copy.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getButtonsVisibility(self):
        return self._save.isVisible()

    def showButtons(self):
        self.setButtonsVisibility(True)

    def hideButtons(self):
        self.setButtonsVisibility(False)

    def getButtonsLayout(self):
        return self._btlyout

    def copyToClipboard(self):
        if not self.isEmpty():
            self._sheet.toClipboard()

    def getStatistics(self):
        if not self.isEmpty() and self._sheet.size > 0:
            sheet = self._sheet.describe()
            skew = DataFrame(self._sheet.skew()).T
            skew.index = ['Skewness']
            kurt = DataFrame(self._sheet.kurt()).T
            kurt.index = ['Kurtosis']
            sheet = concat((sheet, skew, kurt))
            return SisypheSheet(sheet)

    def getChart(self, axes, col=None, subplots=False, bins=10, chart='line'):
        if col is None:
            if chart == 'line': return self._sheet.plot.line(ax=axes, subplots=subplots)
            elif chart == 'bar': return self._sheet.plot.bar(ax=axes, subplots=subplots)
            elif chart == 'hbar': return self._sheet.plot.barh(ax=axes, subplots=subplots)
            elif chart == 'hist': return self._sheet.plot.hist(ax=axes, bins=bins, subplots=subplots)
            elif chart == 'box': return self._sheet.plot.box(ax=axes,)
            elif chart == 'density': return self._sheet.plot.density(ax=axes, subplots=subplots)
            else: raise ValueError('incorrect chart parameter {}.'.format(chart))
        elif isinstance(col, str):
            c = self._sheet[col]
            if chart == 'line': return c.plot.line(ax=axes, subplots=subplots)
            elif chart == 'bar': return c.plot.bar(ax=axes, subplots=subplots)
            elif chart == 'hbar': return c.plot.barh(ax=axes, subplots=subplots)
            elif chart == 'hist': return c.plot.hist(ax=axes, bins=bins, subplots=subplots)
            elif chart == 'box': return c.plot.box(ax=axes)
            elif chart == 'density': return c.plot.density(ax=axes, subplots=subplots)
            else: raise ValueError('incorrect chart parameter {}.'.format(chart))
        else: raise TypeError('parameter type {} i not str'.format(type(col)))


class SheetStatisticsWidget(QWidget):
    """
    SheetStatisticsWidget class

    Description
    ~~~~~~~~~~~

    Widget to display SisypheSheet, gives descriptive statistics of the sheet

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SheetStatisticsWidget
    """

    # Special method

    """
    Private attributes

    _sheet      SheetWidget
    _stats      SheetWidget
    """

    def __init__(self, sheet=None, title='Datasheet', parent=None):
        super().__init__(parent)

        self._sheet = SheetWidget(title=title)
        # noinspection PyUnresolvedReferences
        self._sheet.SheetChanged.connect(self._updateStatistics)
        self._stats = SheetWidget(title='Statistics')

        if isinstance(sheet, SisypheSheet): self.setSheet(sheet)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QWidgets

        self._tab = QTabWidget()
        self._tab.addTab(self._sheet, self._sheet.getTitle())
        self._tab.addTab(self._stats, self._stats.getTitle())
        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Vertical)
        self._splitter.addWidget(self._tab)
        self._layout.addWidget(self._splitter)

    def __getattr__(self, name):
        # When attribute does not exist in the class, try calling SheetWidget method
        if name in SheetWidget.__dict__: return self._sheet.__getattribute__(name)
        else: raise AttributeError('No attribute {} in SheetStatisticsWidget class.'.format(name))

    # Private method

    def _updateStatistics(self):
        self._stats.setSheet(self._sheet.getStatistics())

    # Public methods

    def setSheet(self, sheet):
        if isinstance(sheet, SisypheSheet):
            self._sheet.setSheet(sheet)
            self._stats.setSheet(sheet.getStatistics())

    def clearSheet(self):
        self._sheet.clearSheet()
        self._stats.clearSheet()


class SheetChartWidget(SheetStatisticsWidget):
    """
    SheetStatisticsWidget class

    Description
    ~~~~~~~~~~~

    SheetStatisticsWidget with chart display

    Inheritance
    ~~~~~~~~~~~

    QWidget -> SheetStatisticsWidget -> SheetChartWidget
    """

    # Special method

    def __init__(self, sheet=None, title='Datasheet', parent=None):
        super().__init__(sheet, title, parent)

        self._fig = Figure()
        self._canvas = FigureCanvas(self._fig)
        self._axes = self._fig.add_axes(rect=(0.1, 0.1, 0.8, 0.8))

        self._splitter.insertWidget(0, self._canvas)

        btlayout = self._sheet.getButtonsLayout()
        self._chart = QPushButton('Draw chart')
        self._chartmenu = QMenu()
        self._chartmenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._chartmenu.setWindowFlag(Qt.FramelessWindowHint, True)
        self._chartmenu.setAttribute(Qt.WA_TranslucentBackground, True)
        # noinspection PyUnresolvedReferences
        self._chartmenu.triggered.connect(self._drawChart)
        self._chartmenu.addAction('Lines')
        self._chartmenu.addAction('Vertical bars')
        self._chartmenu.addAction('Horizontal bars')
        self._chartmenu.addAction('Histogram')
        self._chartmenu.addAction('Box')
        self._chartmenu.addAction('Density')
        self._chart.setMenu(self._chartmenu)

        self._properties = QPushButton('Properties')
        self._properties.setToolTip('Edit chart properties')
        # noinspection PyUnresolvedReferences
        self._properties.clicked.connect(self.properties)

        self._savechart = QPushButton('Save chart')
        self._savechart.setToolTip('Save chart to BMP, JPG, PNG, TIFF or SVG format')
        # noinspection PyUnresolvedReferences
        self._savechart.clicked.connect(lambda dummy: self.saveChart())

        self._clipboardchart = QPushButton('Copy chart')
        self._clipboardchart.setToolTip('Copy chart to clipboard')
        # noinspection PyUnresolvedReferences
        self._clipboardchart.clicked.connect(self.copyChartToClipboard)

        btlayout.addWidget(self._chart)
        btlayout.addWidget(self._properties)
        btlayout.addWidget(self._savechart)
        btlayout.addWidget(self._clipboardchart)

        self._dialog = DialogFromXml('Chart properties', ['ChartProperties'])

    # private method

    def _drawChart(self, action):
        c = action.text()[:2]
        self._axes.cla()
        if c == 'Li': self._sheet.getChart(axes=self._axes, chart='line')
        elif c == 'Ve': self._sheet.getChart(axes=self._axes, chart='bar')
        elif c == 'Ho': self._sheet.getChart(axes=self._axes, chart='hbar')
        elif c == 'Hi': self._sheet.getChart(axes=self._axes, chart='hist')
        elif c == 'Bo': self._sheet.getChart(axes=self._axes, chart='box')
        elif c == 'De': self._sheet.getChart(axes=self._axes, chart='density')
        self._canvas.draw()

    # Public method

    def properties(self):
        if self._dialog.exec() == QDialog.Accepted:
            settings = self._dialog.getFieldsWidget(0)
            if settings.getParameterValue('TitleVisibility'): self._axes.set_title(self._sheet.getTitle())
            else: self._axes.set_title('')
            legend = settings.getParameterValue('Legend')[0].lower()
            if legend == 'no':
                lgd = self._axes.get_legend()
                if lgd is not None: lgd.remove()
            else: self._axes.legend(loc=legend)
            if settings.getParameterValue('FrameVisibility'): self._axes.set_frame_on(True)
            else: self._axes.set_frame_on(False)
            if settings.getParameterValue('AxisVisibility'): self._axes.set_axis_on()
            else: self._axes.set_axis_off()
            grid = settings.getParameterValue('Grid')[0]
            opacity = settings.getParameterValue('GridOpacity')
            dash = settings.getParameterValue('GridDash')[0]
            if dash == 'Solid': ds = '-'
            elif dash == 'Dashed': ds = '--'
            elif dash == 'Dash-dotted': ds = '_.'
            elif dash == 'Dotted': ds = ':'
            else: ds = '-'
            if grid == 'No': self._axes.grid(visible=False)
            elif grid == 'X': self._axes.grid(visible=True, ls=ds, alpha=opacity, axis='x')
            elif grid == 'Y': self._axes.grid(visible=True, ls=ds, alpha=opacity, axis='y')
            else: self._axes.grid(visible=True, ls=ds, alpha=opacity, axis='both')
            c = settings.getParameterValue('FigColor')
            self._fig.set_facecolor(c)
            c = settings.getParameterValue('FrameColor')
            self._axes.set_facecolor(c)
            self._canvas.draw()

    def saveChart(self, filename=''):
        if not self.isEmpty():
            if isinstance(filename, str):
                if filename == '':
                    filename = QFileDialog.getSaveFileName(self, 'Save chart', filename,
                                                           filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;'
                                                                  'TIFF (*.tiff);;SVG (*.svg)',
                                                           initialFilter='JPG (*.jpg)')[0]
                    QApplication.processEvents()
            if filename != '':
                chdir(dirname(filename))
                try: self._fig.savefig(filename)
                except Exception as err: messageBox(self, 'Save chart', text='{}'.format(err))

    def copyChartToClipboard(self):
        tmp = join(getcwd(), 'tmp.png')
        try:
            self._fig.savefig(tmp)
            img = QPixmap(tmp)
            QApplication.clipboard().setPixmap(img)
        except Exception as err:
            messageBox(self, 'Copy chart to clipboard', text='error: {}'.format(err))
        finally:
            if exists(tmp): remove(tmp)
