"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - fpdf2, pdf document generation, https://py-pdf.github.io/fpdf2/index.html
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import remove
from os import chdir

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import dirname
from os.path import basename
from os.path import abspath

from glob import glob

from math import sqrt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import array
from numpy import arange
from numpy import count_nonzero
from numpy import corrcoef
from numpy import polyfit

from pandas import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from fpdf import FPDF

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.core.sisypheConstants import getICBM152Path
from Sisyphe.core.sisypheConstants import getID_ICBM152
from Sisyphe.core.sisypheConstants import getOrigin_ICBM152
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.core.sisypheStatistics import zTot
from Sisyphe.core.sisypheStatistics import tToz
from Sisyphe.core.sisypheStatistics import pvalueToz
from Sisyphe.core.sisypheStatistics import qFDRToz
from Sisyphe.core.sisypheStatistics import tTopvalue
from Sisyphe.core.sisypheStatistics import zTopvalue
from Sisyphe.core.sisypheStatistics import pCorrectedBonferroni
from Sisyphe.core.sisypheStatistics import tToVoxelCorrectedpvalue
from Sisyphe.core.sisypheStatistics import zToVoxelCorrectedpvalue
from Sisyphe.core.sisypheStatistics import extentToClusterUncorrectedpvalue
from Sisyphe.core.sisypheStatistics import extentToClusterCorrectedpvalue
from Sisyphe.core.sisypheStatistics import pUncorrectedBonferroni
from Sisyphe.core.sisypheStatistics import reselCount
from Sisyphe.core.sisypheStatistics import voxelCorrectedpvalueToz
from Sisyphe.core.sisypheStatistics import tFieldExpectedVoxels
from Sisyphe.core.sisypheStatistics import zFieldExpectedVoxels
from Sisyphe.core.sisypheStatistics import tFieldExpectedClusters
from Sisyphe.core.sisypheStatistics import zFieldExpectedClusters
from Sisyphe.core.sisypheStatistics import clusterUncorrectedpvalueToExtent
from Sisyphe.core.sisypheStatistics import clusterCorrectedpvalueToExtent
from Sisyphe.core.sisypheStatistics import thresholdMap
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import QDoubleSpinBox2
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalSliceViewWidget
from Sisyphe.widgets.projectionViewWidget import IconBarMultiProjectionViewWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogResult']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogResult
"""

class DialogResult(QDialog):
    """
    DialogResult class

    Description
    ~~~~~~~~~~~

    GUI window to display a statistical map.

    reference:
    A unified statistical approach for determining significant signals in images of cerebral activation.
    KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73.
    doi: 10.1002/(SICI)1097-0193(1996)4:1<58::AID-HBM4>3.0.CO;2-O.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogResult

    Creation: 18/11/2024
    Last revision: 10/06/2025
    """

    # class method

    @classmethod
    def _getFormattedValue(cls, v: int | float, threshold: float = 1e-6) -> str:
        if isinstance(v, float):
            v2 = abs(v)
            if 0.0 <= v2 < 1.0:
                if v2 >= threshold:
                    try:
                        d = int('{:e}'.format(v2).split('-')[1])
                        # noinspection PyUnusedLocal
                        f = '{:.' + str(d) + 'f}'
                    except:
                        f = '{:g}'
                elif v2 < 1e-10: f = '< 1e-10'
                else: f = '{:.1e}'
            else: f = '{:.1f}'
        else: f = '{}'
        return f.format(v)

    # Special method

    """
    Private attributes
    
    _stats          QTreeWidget, list of local maximums for clusters
    _cbthreshold    LabeledComboBox, type of statistical threshold: t-value, z-value, uncorrected p-value, 
                    Bonferroni corrected p-value, gaussian-field corrected p-value, q-value FDR
    _sbthreshold    QDoubleSpinBox, statistical threshold value
    _cbextent       LabeledComboBox, cluster size threshold: voxel count, volume (mm3), uncorrected p-value, 
                    gaussian-field corrected p-value
    _sbextent       QDoubleSpinBox, cluster size threshold value
    _scrshot        ScreenshotsGridWidget
    _map            SisypheVolume, statistical map (t-map or zmap)
    _mask           SisypheVolume, mask of analysis (i.e. non-zero voxels of the statistical map)
    _anat           SisypheVolume, background anatomical volume
    _brodmann       SisypheVolume, ICBM152 Brodmann label image
    _anatomy        SisypheVolume, ICBM152 Anatomy label image
    _design         SisypheDesign, model design
    _cursor         tuple[int, int, int], current voxel coordinates
    _nb             int, number of non-zero voxels
    _rc             tuple[float, float, float, float], resel counts
    _ev             float, expected voxels
    _ec             float, expected clusters
    _res            float, resel volume (in voxels)
    _zscore         float, z-value threshold
    _extent         float, number of voxels extent
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical results')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        # Init non-GUI attributes

        self._map: SisypheVolume | None = None
        self._mask: SisypheVolume | None = None
        self._anat: SisypheVolume | None = None
        self._brodmann: SisypheVolume | None = None
        self._anatomy: SisypheVolume | None = None
        self._design: SisypheDesign | None = None
        self._scrshot: ScreenshotsGridWidget | None = None
        self._cursor: tuple[int, int, int] = (0, 0, 0)
        self._nb: int = 0
        self._rc: tuple[float, float, float, float] | None = None
        self._ec: float = 0.0
        self._ev: float = 0.0
        self._res: float = 0.0

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._views = QTabWidget()
        # noinspection PyUnresolvedReferences
        self._views.currentChanged.connect(self._updateChart)
        self._sliceView = IconBarOrthogonalSliceViewWidget()
        self._projectionView = IconBarMultiProjectionViewWidget()

        self._widget1 = QWidget()
        hlyout1 = QHBoxLayout()
        button1 = QPushButton('Save bitmap')
        button2 = QPushButton('Copy to clipboard')
        button3 = QPushButton('Copy to screenshots')
        # noinspection PyUnresolvedReferences
        button1.clicked.connect(self._saveBitmap)
        # noinspection PyUnresolvedReferences
        button2.clicked.connect(self._copyClipboard)
        # noinspection PyUnresolvedReferences
        button3.clicked.connect(self._copyScreenshot)
        hlyout1.addWidget(button1)
        hlyout1.addWidget(button2)
        hlyout1.addWidget(button3)
        hlyout1.addStretch()

        self._fig1 = Figure()
        self._fig1.set_layout_engine('constrained')
        self._canvas1 = FigureCanvas(self._fig1)

        lyoutf1 = QVBoxLayout()
        lyoutf1.addWidget(self._canvas1)
        lyoutf1.addLayout(hlyout1)
        self._widget1.setLayout(lyoutf1)

        self._widget2 = QWidget()
        hlyout2 = QHBoxLayout()
        button1 = QPushButton('Save bitmap')
        button2 = QPushButton('Copy to clipboard')
        button3 = QPushButton('Copy to screenshots')
        # noinspection PyUnresolvedReferences
        button1.clicked.connect(self._saveBitmap)
        # noinspection PyUnresolvedReferences
        button2.clicked.connect(self._copyClipboard)
        # noinspection PyUnresolvedReferences
        button3.clicked.connect(self._copyScreenshot)
        hlyout2.addWidget(button1)
        hlyout2.addWidget(button2)
        hlyout2.addWidget(button3)
        hlyout2.addStretch()

        self._fig2 = Figure()
        self._fig2.set_layout_engine('constrained')
        self._canvas2 = FigureCanvas(self._fig2)

        lyoutf2 = QVBoxLayout()
        lyoutf2.addWidget(self._canvas2)
        lyoutf2.addLayout(hlyout2)
        self._widget2.setLayout(lyoutf2)

        self._widget3 = QWidget()
        hlyout3 = QHBoxLayout()
        button1 = QPushButton('Save bitmap')
        button2 = QPushButton('Copy to clipboard')
        button3 = QPushButton('Copy to screenshots')
        # noinspection PyUnresolvedReferences
        button1.clicked.connect(self._saveBitmap)
        # noinspection PyUnresolvedReferences
        button2.clicked.connect(self._copyClipboard)
        # noinspection PyUnresolvedReferences
        button3.clicked.connect(self._copyScreenshot)
        hlyout3.addWidget(button1)
        hlyout3.addWidget(button2)
        hlyout3.addWidget(button3)
        hlyout3.addStretch()

        self._fig3 = Figure()
        self._fig3.set_layout_engine('constrained')
        self._canvas3 = FigureCanvas(self._fig3)

        lyoutf3 = QVBoxLayout()
        lyoutf3.addWidget(self._canvas3)
        lyoutf3.addLayout(hlyout3)
        self._widget3.setLayout(lyoutf3)

        self._views.addTab(self._sliceView, 'Slices')
        self._views.addTab(self._projectionView, 'Projections')
        self._views.addTab(self._widget1, 'Beta chart')
        self._views.addTab(self._widget2, 'Time series chart')
        self._views.addTab(self._widget3, 'Regression chart')
        self._views.setTabVisible(2, False)
        self._views.setTabVisible(3, False)
        self._views.setTabVisible(4, False)

        self._cbthreshold = LabeledComboBox(title='Voxel threshold')
        self._cbthreshold.addItem('t-value')
        self._cbthreshold.addItem('z-score')
        self._cbthreshold.addItem('uncorrected p-value')
        self._cbthreshold.addItem('Bonferroni corrected p-value')
        self._cbthreshold.addItem('Gaussian-field corrected p-value')
        self._cbthreshold.addItem('q FDR')
        self._cbthreshold.setCurrentIndex(2)
        # noinspection PyUnresolvedReferences
        self._cbthreshold.currentIndexChanged.connect(self._cbThresholdChanged)

        self._sbthreshold = QDoubleSpinBox2()
        self._sbthreshold.setFixedWidth(200)
        # < Revision 07/12/2024
        # no keyboard tracking
        self._sbthreshold.setKeyboardTracking(False)
        # Revision 07/12/2024 >
        self._sbthreshold.setDecimals(6)
        self._sbthreshold.setRange(0.0, 1.0)
        self._sbthreshold.setSingleStep(0.01)
        self._sbthreshold.setValue(0.05)
        # < Revision 07/12/2024
        # self._sbthreshold.editingFinished.connect(self._sbThresholdValueChanged)
        # noinspection PyUnresolvedReferences
        self._sbthreshold.valueChanged.connect(self._sbThresholdValueChanged)
        # Revision 07/12/2024 >
        self._zscore: float = pvalueToz(0.05)

        self._cbextent = LabeledComboBox(title='Cluster extent threshold')
        self._cbextent.addItem('number of voxels')
        self._cbextent.addItem('number of resels')
        self._cbextent.addItem('volume (mm3)')
        self._cbextent.addItem('uncorrected p-value')
        self._cbextent.addItem('Gaussian-field corrected p-value')
        self._cbextent.setCurrentIndex(0)
        # noinspection PyUnresolvedReferences
        self._cbextent.currentIndexChanged.connect(self._cbExtentChanged)
        self._extent: int = 100

        self._sbextent = QDoubleSpinBox2()
        self._sbextent.setFixedWidth(200)
        # < Revision 07/12/2024
        # no keyboard tracking
        self._sbextent.setKeyboardTracking(False)
        # Revision 07/12/2024 >
        self._sbextent.setRange(0.0, 10000.0)
        self._sbextent.setValue(100)
        self._sbextent.setDecimals(0)
        # < Revision 07/12/2024
        # self._sbextent.editingFinished.connect(self._sbExtentValueChanged)
        # noinspection PyUnresolvedReferences
        self._sbextent.valueChanged.connect(self._sbExtentValueChanged)
        # Revision 07/12/2024 >

        lyoutbt = QHBoxLayout()
        lyoutbt.setSpacing(10)
        lyoutbt.setDirection(QHBoxLayout.LeftToRight)
        lyoutbt.addWidget(self._cbthreshold)
        lyoutbt.addWidget(self._sbthreshold)
        lyoutbt.addWidget(self._cbextent)
        lyoutbt.addWidget(self._sbextent)
        lyoutbt.addStretch()

        font = QFont('Arial', 8)
        self._group1 = QGroupBox(' General ')
        self._group1.setFont(font)
        self._lbdof = QLabel('Degrees of freedom')
        self._lbauto = QLabel('Autocorrelations fwhm')
        self._lvresel = QLabel('Resel volume')
        self._lbvan = QLabel('Analysis volume')
        self._lbdof.setFont(font)
        self._lbvan.setFont(font)
        self._lbauto.setFont(font)
        self._lvresel.setFont(font)

        lyout1 = QVBoxLayout()
        lyout1.addStretch()
        lyout1.addWidget(self._lbdof)
        lyout1.addWidget(self._lbauto)
        lyout1.addWidget(self._lvresel)
        lyout1.addWidget(self._lbvan)
        lyout1.addStretch()
        self._group1.setLayout(lyout1)

        group2 = QGroupBox(' Expected ')
        group2.setFont(font)
        self._lbexpv = QLabel('Voxels')
        self._lbexpc = QLabel('Clusters')
        self._lbexvc = QLabel('Voxels per cluster')
        self._lbexpv.setFont(font)
        self._lbexpc.setFont(font)
        self._lbexvc.setFont(font)

        lyout2 = QVBoxLayout()
        lyout2.addStretch()
        lyout2.addWidget(self._lbexpv)
        lyout2.addWidget(self._lbexpc)
        lyout2.addWidget(self._lbexvc)
        lyout2.addStretch()
        group2.setLayout(lyout2)

        group3 = QGroupBox(' Observed ')
        group3.setFont(font)
        self._lbobsv = QLabel('Voxels')
        self._lbobsc = QLabel('Clusters')
        self._lbobsvc = QLabel('Voxels per cluster')
        self._lbobsv.setFont(font)
        self._lbobsc.setFont(font)
        self._lbobsvc.setFont(font)

        lyout3 = QVBoxLayout()
        lyout3.addStretch()
        lyout3.addWidget(self._lbobsv)
        lyout3.addWidget(self._lbobsc)
        lyout3.addWidget(self._lbobsvc)
        lyout3.addStretch()
        group3.setLayout(lyout3)

        group4 = QGroupBox(' Voxel threshold ')
        group4.setFont(font)
        self._lbt = QLabel('t-value')
        self._lbz = QLabel('z-score')
        self._lbq = QLabel('q FDR')
        self._lbp = QLabel('uncorrected p-value')
        self._lbbcp = QLabel('Bonferroni corrected p-value')
        self._lbgcp = QLabel('Gaussian-field corrected p-value')
        self._lbt.setFont(font)
        self._lbz.setFont(font)
        self._lbq.setFont(font)
        self._lbp.setFont(font)
        self._lbbcp.setFont(font)
        self._lbgcp.setFont(font)

        lyout4 = QVBoxLayout()
        lyout4.addWidget(self._lbt)
        lyout4.addWidget(self._lbz)
        lyout4.addWidget(self._lbq)
        lyout4.addWidget(self._lbp)
        lyout4.addWidget(self._lbbcp)
        lyout4.addWidget(self._lbgcp)
        group4.setLayout(lyout4)

        group5 = QGroupBox(' Cluster extent threshold ')
        group5.setFont(font)
        self._lbvox = QLabel('voxel(s)')
        self._lbres = QLabel('resel(s)')
        self._lbvol = QLabel('mm3')
        self._lbcup = QLabel('uncorrected p-value')
        self._lbccp = QLabel('corrected p-value')
        self._lbvox.setFont(font)
        self._lbres.setFont(font)
        self._lbvol.setFont(font)
        self._lbcup.setFont(font)
        self._lbccp.setFont(font)

        lyout5 = QVBoxLayout()
        lyout5.addWidget(self._lbvox)
        lyout5.addWidget(self._lbres)
        lyout5.addWidget(self._lbvol)
        lyout5.addWidget(self._lbcup)
        lyout5.addWidget(self._lbccp)
        group5.setLayout(lyout5)

        self._group6 = QGroupBox(' Cursor position ')
        self._group6.setFont(font)
        self._lbcurt = QLabel('t-value')
        self._lbcurz = QLabel('z-score')
        self._lbcurp = QLabel('uncorrected p-value')
        self._lbcurbcp = QLabel('Bonferroni corrected p-value')
        self._lbcurgcp = QLabel('Gaussian-field corrected p-value')
        self._lbcurt.setFont(font)
        self._lbcurz.setFont(font)
        self._lbcurp.setFont(font)
        self._lbcurbcp.setFont(font)
        self._lbcurgcp.setFont(font)

        lyout6 = QVBoxLayout()
        lyout6.addWidget(self._lbcurt)
        lyout6.addWidget(self._lbcurz)
        lyout6.addWidget(self._lbcurp)
        lyout6.addWidget(self._lbcurbcp)
        lyout6.addWidget(self._lbcurgcp)
        self._group6.setLayout(lyout6)
        self._group6.adjustSize()
        self._group6.setFixedWidth(self._group6.width())

        lyoutif = QHBoxLayout()
        # lyoutif.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        lyoutif.setSpacing(10)
        lyoutif.setContentsMargins(5, 5, 5, 5)
        lyoutif.addWidget(self._group1)
        lyoutif.addWidget(group2)
        lyoutif.addWidget(group3)
        lyoutif.addWidget(group4)
        lyoutif.addWidget(group5)
        lyoutif.addWidget(self._group6)

        self._clusters = QTreeView()
        self._model = QStandardItemModel()
        self._model.setSortRole(Qt.UserRole)
        self._clusters.setModel(self._model)
        self._clusters.setMinimumHeight(400)
        self._labels = ['x', 'y', 'z',
                        'world\nx',
                        'world\ny',
                        'world\nz',
                        't-value',
                        'z-score',
                        'p-value',
                        'Bonferroni\ncorrected\np-value',
                        'Gaussian-field\ncorrected\np-value',
                        'Voxels',
                        'Resels',
                        'Volume',
                        'Cluster\nuncorrected\np-value',
                        'Cluster\ncorrected\np-value',
                        'Brodmann\narea(s)',
                        'Anatomical\nlocation']
        self._model.setHorizontalHeaderLabels(self._labels)
        self._clusters.setAlternatingRowColors(True)
        # noinspection PyTypeChecker
        self._clusters.header().setSectionResizeMode(QHeaderView.Stretch)
        self._clusters.header().setSectionsClickable(True)
        self._clusters.header().setSortIndicatorShown(True)
        self._clusters.header().setStretchLastSection(False)
        # noinspection PyTypeChecker
        self._clusters.header().setDefaultAlignment(Qt.AlignCenter)
        # noinspection PyUnresolvedReferences
        self._clusters.header().sectionClicked.connect(self._sortColumn)
        # noinspection PyUnresolvedReferences
        self._clusters.doubleClicked.connect(self._doubleClicked)

        # Init default dialog buttons

        btwidget = QWidget()
        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close', parent=self)
        self._ok.setAutoDefault(False)
        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        self._report = QPushButton('Save report', parent=self)
        self._report.setAutoDefault(False)
        self._report.setToolTip('Save a pdf report.')
        # noinspection PyUnresolvedReferences
        self._report.clicked.connect(self.report)
        self._save = QPushButton('Save map', parent=self)
        self._save.setAutoDefault(False)
        self._save.setToolTip('Save thresholded statistical map.')
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.saveMap)
        self._save2 = QPushButton('Save table', parent=self)
        self._save2.setAutoDefault(False)
        self._save2.setToolTip('Save table dataset.')
        # noinspection PyUnresolvedReferences
        self._save2.clicked.connect(self.saveDataset)
        lyout.addWidget(self._ok)
        lyout.addWidget(self._save)
        lyout.addWidget(self._save2)
        lyout.addWidget(self._report)
        lyout.addStretch()
        btwidget.setLayout(lyout)

        self._layout.addWidget(self._views)
        self._layout.addLayout(lyoutbt)
        self._layout.addLayout(lyoutif)
        self._layout.addWidget(self._clusters)
        self._layout.addWidget(btwidget)

    # Private methods

    def _sortColumn(self, column: int) -> None:
        if 6 < column < 11: column = 6
        elif column in (14, 15): column = 11
        self._model.sort(column, self._clusters.header().sortIndicatorOrder())

    def _initResults(self):
        # General results
        self._lbdof.setText('{} degrees of freedom'.format(self._map.acquisition.getDegreesOfFreedom()))
        ac = self._map.acquisition.getAutoCorrelations()
        self._lbauto.setText('Autocorrelations fwhm {:.1f} x {:.1f} x {:.1f} mm'.format(ac[0], ac[1], ac[2]))
        self._lvresel.setText('Resel volume {:.1f} voxels, '
                              '{:.1f} mm3'.format(self._res, self._res * self._map.getVoxelVolume()))
        self._lbvan.setText('Analysis volume {:.1f} resels, {} voxels, '
                            '{:.1f} mm3'.format(self._nb / self._res, self._nb, self._nb * self._map.getVoxelVolume()))
        if self._map.acquisition.isTMap():
            self._group1.setTitle('t-map results')
            self._lbdof.show()
        else:
            self._group1.setTitle('z-map results')
            self._lbdof.hide()
        # Expected
        ev = zFieldExpectedVoxels(self._zscore, self._nb)
        ec = zFieldExpectedClusters(self._zscore, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
        self._lbexpv.setText('{:.1f} voxels'.format(ev))
        self._lbexpc.setText('{:.1f} clusters'.format(ec))
        self._lbexvc.setText('{:.1f} voxels per cluster'.format(ev / ec))

    def _cbThresholdChanged(self, index: int) -> None:
        if self._map is not None:
            df = self._map.acquisition.getDegreesOfFreedom()
            if index == 0:
                # t-value
                self._sbthreshold.setRange(0.0, 100.0)
                self._sbthreshold.setDecimals(2)
                self._sbthreshold.setValue(zTot(1.96, df))
            elif index == 1:
                # z-score
                self._sbthreshold.setRange(0.0, 100.0)
                self._sbthreshold.setDecimals(2)
                self._sbthreshold.setValue(1.96)
            else:
                # p-value / q FDR
                self._sbthreshold.setRange(0.0, 1.0)
                self._sbthreshold.setDecimals(10)
                self._sbthreshold.setValue(0.05)

    def _sbThresholdValueChanged(self) -> None:
        if self._map is not None:
            v = self._sbthreshold.value()
            df = self._map.acquisition.getDegreesOfFreedom()
            index = self._cbthreshold.currentIndex()
            # t-value
            if index == 0: v = tToz(v, df)
            # uncorrected p-value
            elif index == 2: v = pvalueToz(v)
            # Bonferroni corrected p-value
            elif index == 3:
                p = pUncorrectedBonferroni(v, self._nb)
                v = pvalueToz(p)
            # Gaussian-field corrected p-value
            elif index == 4:
                v = voxelCorrectedpvalueToz(v, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
            # q FDR
            elif index == 5:
                v = qFDRToz(v, self._map)
            self._zscore = v
            self._update()

    def _cbExtentChanged(self, index: int) -> None:
        if self._map is not None:
            # number of voxels
            if index == 0:
                self._sbextent.setRange(0, self._nb)
                self._sbextent.setDecimals(0)
                self._sbextent.setValue(self._res)
            # number of resels
            elif index == 1:
                self._sbextent.setRange(0.0, self._nb / self._res)
                self._sbextent.setDecimals(1)
                self._sbextent.setValue(1.0)
            # volume (mm3)
            elif index == 2:
                self._sbextent.setRange(0, int(self._nb * self._map.getVoxelVolume()))
                self._sbextent.setDecimals(1)
                self._sbextent.setValue(int(self._res * self._map.getVoxelVolume()))
            # cluster p-value
            else:
                self._sbextent.setRange(0.0, 1.0)
                self._sbextent.setDecimals(10)
                self._sbextent.setValue(0.05)

    def _sbExtentValueChanged(self) -> None:
        if self._map is not None:
            v = self._sbextent.value()
            index = self._cbextent.currentIndex()
            # number of resels
            if index == 1:
                v = v * self._res
            # volume (mm3)
            elif index == 2:
                v = v * self._map.getVoxelVolume()
            # uncorrected p-value
            elif index == 3:
                if self._map.acquisition.isTMap():
                    t = self.getVoxelThreshold()
                    df = self._map.acquisition.getDegreesOfFreedom()
                    ev = tFieldExpectedVoxels(t, df, self._nb)
                    ec = tFieldExpectedClusters(t, df, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    v = clusterUncorrectedpvalueToExtent(v, ev, ec)
                else:
                    z = self.getVoxelThreshold()
                    ev = zFieldExpectedVoxels(z, self._nb)
                    ec = zFieldExpectedClusters(z, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    v = clusterUncorrectedpvalueToExtent(v, ev, ec)
            # Gaussian-field corrected p-value
            elif index == 4:
                if self._map.acquisition.isTMap():
                    t = self.getVoxelThreshold()
                    df = self._map.acquisition.getDegreesOfFreedom()
                    ev = tFieldExpectedVoxels(t, df, self._nb)
                    ec = tFieldExpectedClusters(t, df, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    v = clusterCorrectedpvalueToExtent(v, ev, ec)
                else:
                    z = self.getVoxelThreshold()
                    ev = zFieldExpectedVoxels(z, self._nb)
                    ec = zFieldExpectedClusters(z, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    v = clusterCorrectedpvalueToExtent(v, ev, ec)
            self._extent = int(v)
            self._update()

    def _updateVoxelThresholdBox(self):
        if self._map.acquisition.isTMap():
            self._lbt.show()
            df = self._map.acquisition.getDegreesOfFreedom()
            t = zTot(self._zscore, df)
            self._lbt.setText('t-value {:.2f}'.format(t))
        else: self._lbt.hide()
        self._lbz.setText('z-score {:.2f}'.format(self._zscore))
        if self._cbthreshold.currentIndex() == 5:
            self._lbq.show()
            self._lbq.setText('q FDR {}'.format(self._getFormattedValue(self._sbthreshold.value())))
        else: self._lbq.hide()
        p = zTopvalue(self._zscore)
        self._lbp.setText('uncorrected p-value {}'.format(self._getFormattedValue(p)))
        p = pCorrectedBonferroni(p, self._nb)
        self._lbbcp.setText('Bonferroni corrected p-value {}'.format(self._getFormattedValue(p)))
        p = zToVoxelCorrectedpvalue(self._zscore, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
        self._lbgcp.setText('Gaussian-field corrected p-value {}'.format(self._getFormattedValue(p)))

    def _updateClusterExtentBox(self):
        self._lbvox.setText('{} voxel(s)'.format(self._extent))
        self._lbres.setText('{:.1f} resel(s)'.format(self._extent / self._res))
        self._lbvol.setText('{:.1f} mm3'.format(self._extent * self._map.getVoxelVolume()))
        ev = zFieldExpectedVoxels(self._zscore, self._nb)
        ec = zFieldExpectedClusters(self._zscore, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
        p = extentToClusterUncorrectedpvalue(self._extent, ev, ec)
        self._lbcup.setText('uncorrected p-value {}'.format(self._getFormattedValue(p)))
        p = extentToClusterCorrectedpvalue(self._extent, ev, ec)
        self._lbccp.setText('corrected p-value {}'.format(self._getFormattedValue(p)))

    def _update(self):
        if self._map is not None:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Update statistics')
            df = self._map.acquisition.getDegreesOfFreedom()
            if self._map.acquisition.isTMap(): v = zTot(self._zscore, df)
            else: v = self._zscore
            vlabels = list()
            if self._brodmann is not None: vlabels.append(self._brodmann)
            if self._anatomy is not None: vlabels.append(self._anatomy)
            r = thresholdMap(v, self._extent, self._map, vlabels)
            # update _views
            self._sliceView.removeAllOverlays()
            self._sliceView.addOverlay(r['map'])
            if self._anat is None: self._projectionView.setVolume(r['map'], self._mask, mask=self._mask)
            else: self._projectionView.setVolume(r['map'], self._anat, mask=self._mask)
            # update QTreeView
            # self._clusters.clear()
            self._model.invisibleRootItem().removeRows(0, self._model.rowCount())
            nclusters = len(r['max'])
            if nclusters > 0:
                for i in range(nclusters):
                    # x, y, z local maximum coordinates
                    x = int(r['c'][i][0])
                    y = int(r['c'][i][1])
                    z = int(r['c'][i][2])
                    # x
                    item = QStandardItem()
                    item.setData(x, Qt.UserRole)
                    item.setText(str(x))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 0, item)
                    # y
                    item = QStandardItem()
                    item.setData(y, Qt.UserRole)
                    item.setText(str(y))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 1, item)
                    # z
                    item = QStandardItem()
                    item.setData(z, Qt.UserRole)
                    item.setText(str(z))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 2, item)
                    # x, y, z local maximum world coordinates
                    spacing = self._map.getSpacing()
                    origin = self._map.getOrigin()
                    x2 = (float(x) * spacing[0]) - origin[0]
                    y2 = (float(y) * spacing[1]) - origin[1]
                    z2 = (float(z) * spacing[2]) - origin[2]
                    # x world coordinate
                    item = QStandardItem()
                    item.setData(x2, Qt.UserRole)
                    item.setText('{:.1f}'.format(x2))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 3, item)
                    # y world coordinate
                    item = QStandardItem()
                    item.setData(y2, Qt.UserRole)
                    item.setText('{:.1f}'.format(y2))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 4, item)
                    # z world coordinate
                    item = QStandardItem()
                    item.setData(z2, Qt.UserRole)
                    item.setText('{:.1f}'.format(z2))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 5, item)
                    if self._map.acquisition.isTMap():
                        # t-value
                        t = r['max'][i]
                        item = QStandardItem()
                        item.setData(t, Qt.UserRole)
                        item.setText('{:.2f}'.format(t))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 6, item)
                        # z-score
                        zs = tToz(t, df)
                        item = QStandardItem()
                        item.setData(zs, Qt.UserRole)
                        item.setText('{:.2f}'.format(zs))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 7, item)
                        # uncorrected p-value
                        puc = tTopvalue(t, df)
                        item = QStandardItem()
                        item.setData(puc, Qt.UserRole)
                        item.setText(self._getFormattedValue(puc))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 8, item)
                        # Bonferroni corrected p-value
                        pb = pCorrectedBonferroni(puc, self._nb)
                        item = QStandardItem()
                        item.setData(pb, Qt.UserRole)
                        item.setText(self._getFormattedValue(pb))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 9, item)
                        # gaussian-field corrected p-value
                        pg = tToVoxelCorrectedpvalue(t, df, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                        item = QStandardItem()
                        item.setData(pg, Qt.UserRole)
                        item.setText(self._getFormattedValue(pg))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 10, item)
                        ev = tFieldExpectedVoxels(t, df, self._nb)
                        ec = tFieldExpectedClusters(t, df, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    else:
                        # t-value
                        t = 'na'
                        item = QStandardItem()
                        item.setData(0.0, Qt.UserRole)
                        item.setText(t)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 6, item)
                        self._clusters.header().hideSection(6)
                        # z-score
                        zs = self._map[x, y, z]
                        item = QStandardItem()
                        item.setData(zs, Qt.UserRole)
                        item.setText('{:.2f}'.format(zs))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 7, item)
                        # uncorrected p-value
                        puc = zTopvalue(z)
                        item = QStandardItem()
                        item.setData(puc, Qt.UserRole)
                        item.setText(self._getFormattedValue(puc))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 8, item)
                        # Bonferroni corrected p-value
                        pb = pCorrectedBonferroni(puc, self._nb)
                        item = QStandardItem()
                        item.setData(pb, Qt.UserRole)
                        item.setText(self._getFormattedValue(pb))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 9, item)
                        # gaussian-field corrected p-value
                        pg = zToVoxelCorrectedpvalue(zs, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                        item = QStandardItem()
                        item.setData(pg, Qt.UserRole)
                        item.setText(self._getFormattedValue(pg))
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                        self._model.setItem(i, 10, item)
                        ev = zFieldExpectedVoxels(z, self._nb)
                        ec = zFieldExpectedClusters(z, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                    # cluster, nb. of voxels
                    nbv = r['extent'][i]
                    item = QStandardItem()
                    item.setData(nbv, Qt.UserRole)
                    item.setText(str(nbv))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 11, item)
                    # cluster, nb. of resels
                    v = nbv / self._res
                    item = QStandardItem()
                    item.setData(v, Qt.UserRole)
                    item.setText('{:.1f}'.format(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 12, item)
                    # cluster, volume (mm3)
                    v = nbv * self._map.getVoxelVolume()
                    item = QStandardItem()
                    item.setData(v, Qt.UserRole)
                    item.setText('{:.1f}'.format(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 13, item)
                    # cluster uncorrected p-value
                    p = extentToClusterUncorrectedpvalue(nbv, ev, ec)
                    item = QStandardItem()
                    item.setData(p, Qt.UserRole)
                    item.setText(self._getFormattedValue(p))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 14, item)
                    # cluster corrected p-value
                    p = extentToClusterCorrectedpvalue(nbv, ev, ec)
                    item = QStandardItem()
                    item.setData(p, Qt.UserRole)
                    item.setText(self._getFormattedValue(p))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    self._model.setItem(i, 15, item)
                    # Brodmann area
                    if self._brodmann is not None:
                        # Brodmann label of voxel
                        lb = self._brodmann[x, y, z]
                        item = QStandardItem()
                        item.setData(0.0, Qt.UserRole)
                        item.setText(self._brodmann.acquisition.getLabel(lb))
                        item.setEditable(False)
                        self._model.setItem(i, 16, item)
                        tip = 'Voxel Brodmann area:\n{}'.format(item.text())
                        # Brodmann label proportions in cluster
                        label = self._brodmann.getBasename()
                        tips = dict()
                        if label in r:
                            nlb = len(r[label][i])
                            if nlb > 0:
                                tip += '\n\nCluster Brodmann areas:'
                                keys = list(r[label][i].keys())
                                for k in keys:
                                    name = self._brodmann.acquisition.getLabel(k)
                                    value = r[label][i][k] * 100.0
                                    if value > 1.0:
                                        if value in tips: value += 0.01
                                        tips[value] = '\n{} {:.1f} %'.format(name, value)
                        if len(tips) > 0:
                            keys = list(tips.keys())
                            keys.sort(reverse=True)
                            for k in keys:
                                tip += tips[k]
                        item.setToolTip(tip)
                    else: self._clusters.header().hideSection(16)
                    # Anatomy
                    if self._anatomy is not None:
                        # anatomy label of voxel
                        lb = self._anatomy[x, y, z]
                        item = QStandardItem()
                        item.setData(0.0, Qt.UserRole)
                        item.setText(self._anatomy.acquisition.getLabel(lb))
                        item.setEditable(False)
                        self._model.setItem(i, 17, item)
                        tip = 'Voxel anatomy area:\n{}'.format(item.text())
                        # anatomy label proportions in cluster
                        tips = dict()
                        label = self._anatomy.getBasename()
                        if label in r:
                            tip += '\n\nCluster anatomy areas:'
                            nlb = len(r[label][i])
                            if nlb > 0:
                                keys = list(r[label][i].keys())
                                for k in keys:
                                    name = self._anatomy.acquisition.getLabel(k)
                                    value = r[label][i][k] * 100.0
                                    if value > 1.0:
                                        if value in tips: value += 0.01
                                        tips[value] = '\n{} {:.1f} %'.format(name, value)
                        if len(tips) > 0:
                            keys = list(tips.keys())
                            keys.sort(reverse=True)
                            for k in keys:
                                tip += tips[k]
                        item.setToolTip(tip)
                    else: self._clusters.header().hideSection(17)
                    # self._clusters.addTopLevelItem(item)
            self._updateVoxelThresholdBox()
            self._updateClusterExtentBox()
            # Observed
            nvoxels = 0
            if nclusters > 0:
                for i in range(nclusters):
                    nvoxels += r['extent'][i]
            self._lbobsv.setText('{} voxels'.format(nvoxels))
            self._lbobsc.setText('{} clusters'.format(nclusters))
            if nclusters > 0:
                self._lbobsvc.setText('{:.1f} voxels per cluster'.format(nvoxels / nclusters))
            wait.close()

    def _updateChart(self, index: int) -> None:
        if index == 2: self._updateBetaChart()
        elif index == 3: self._updateTimeSeriesChart()
        elif index == 4: self._updateRegressionChart()

    def _updateBetaChart(self):
        if self._views.isTabVisible(2):
            if self._design is not None and self._map.acquisition.hasContrast():
                contrast = self._map.acquisition.getContrast()
                beta = self._design.getBeta()
                factors = self._design.getEffectInformations()
                pooled = self._design.getPooledVariance()
                if beta is not None and factors is not None and contrast is not None and pooled is not None:
                    wait = DialogWait()
                    wait.open()
                    wait.setInformationText('Beta chart update...')
                    try:
                        x, y, z = self._getCurrentVoxelPosition()
                        self._fig1.clear()
                        ax = self._fig1.add_subplot(111)
                        ax.set_title('Beta {} {}'.format(splitext(self._design.getBasename())[0], (x, y, z)))
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        v = dict()
                        for i in range(len(contrast)):
                            # < Revision 10/06/2025
                            # remove global factor if fMRI design
                            # v[factors[i][0]] = beta[x, y, z][i]
                            factor = factors[i][0]
                            if self._design.isfMRIDesign() and factor not in self._design.getConditionNames():
                                v[factor] = beta[x, y, z][i]
                            # Revision 10/06/2025 >
                        if len(v) > 0:
                            errors = [sqrt(pooled[x, y, z])] * len(v)
                            rects = ax.bar(list(v.keys()), list(v.values()), yerr=errors)
                            ax.bar_label(rects, fmt='%.2f', padding=3)
                        lbls = ['\n'.join(lb.split()) for lb in list(v.keys())]
                        ax.set_xticks(arange(len(v)), labels=lbls)
                        ax.tick_params(axis='x', labelrotation=45)
                        self._fig1.canvas.draw()
                        wait.close()
                        return
                    except: wait.close()
            self._views.setTabVisible(2, False)

    def _updateTimeSeriesChart(self):
        if self._views.isTabVisible(3):
            if self._design is not None:
                if self._design.isfMRIDesign() and self._map.acquisition.hasContrast():
                    obs = self._design.getObservations()
                    beta = self._design.getBeta()
                    mtx = self._design.getDesignMatrix()
                    if obs is not None and beta is not None and mtx is not None:
                        wait = DialogWait()
                        wait.open()
                        wait.setInformationText('Time series chart update...')
                        try:
                            x, y, z = self._getCurrentVoxelPosition()
                            self._fig2.clear()
                            ax = self._fig2.add_subplot(111)
                            ax.set_title('Time series {} {}'.format(splitext(self._design.getBasename())[0],
                                                                    (x, y, z)))
                            vobs = array(obs[x, y, z])
                            vmodel = mtx @ array(beta[x, y, z])
                            vx = arange(len(vobs))
                            ax.plot(vx, vobs, 'o-', label='Observations')
                            ax.plot(vx, vmodel, 'o-', label='fitted model')
                            self._fig2.canvas.draw()
                            wait.close()
                            return
                        except: wait.close()
            self._views.setTabVisible(3, False)

    def _updateRegressionChart(self):
        if self._views.isTabVisible(4):
            if self._design is not None and self._map.acquisition.hasContrast():
                obs = self._design.getObservations()
                beta = self._design.getBeta()
                mtx = self._design.getDesignMatrix()
                factors = self._design.getEffectInformations()
                contrast = self._map.acquisition.getContrast()
                n = count_nonzero(contrast)
                if obs is not None and beta is not None and factors is not None and contrast is not None:
                    wait = DialogWait()
                    wait.open()
                    wait.setInformationText('Regression chart update...')
                    try:
                        x, y, z = self._getCurrentVoxelPosition()
                        self._fig3.clear()
                        c = 1
                        for i in range(len(contrast)):
                            if contrast[i] != 0:
                                ax = self._fig3.add_subplot(1, n, c)
                                # noinspection PyArgumentList
                                vx = mtx[:, i] * array(beta[x, y, z][i])
                                vy = array(obs[x, y, z])
                                vy = vy - vy.mean()
                                # noinspection PyArgumentList
                                x0 = vx.min()
                                # noinspection PyArgumentList
                                x1 = vx.max()
                                r = polyfit(vx, vy, deg=1)
                                y0 = r[0] * x0 + r[1]
                                y1 = r[0] * x1 + r[1]
                                ax.scatter(vx, vy, label=factors[i][0])
                                ax.plot([x0, x1], [y0, y1])
                                ax.set_title('Regression {} {}'
                                             '\nbeta={:.2f}, '
                                             'Pearson correlation coeff.={:.2f}'.format(factors[i][0],
                                                                                               (x, y, z),
                                                                                               beta[x, y, z][i],
                                                                                               corrcoef(array([vx, vy]))[0, 1]))
                                ax.set_xlabel('model x beta')
                                ax.set_ylabel('mean-centered observations')
                                c += 1
                        self._fig3.canvas.draw()
                        wait.close()
                        return
                    except: wait.close()
            self._views.setTabVisible(4, False)

    def _getCurrentWorldPosition(self) -> tuple[float, float, float]:
        if self._map is not None: return self._sliceView().getAxialView().getCursorWorldPosition()
        else: return 0.0, 0.0, 0.0

    def _getCurrentVoxelPosition(self) -> tuple[int, int, int]:
        if self._map is not None:
            p = list(self._sliceView().getAxialView().getCursorWorldPosition())
            spacing = self._map.getSpacing()
            size = list(self._map.getSize())
            size[0] -= 1
            size[1] -= 1
            size[2] -= 1
            x = int(p[0] // spacing[0])
            y = int(p[1] // spacing[1])
            z = int(p[2] // spacing[2])
            if x < 0: x = 0
            elif x > size[0]: x = size[0]
            if y < 0: y = 0
            elif y > size[1]: y = size[1]
            if z < 0: z = 0
            elif z > size[2]: z = size[2]
            return x, y, z
        else: return 0, 0, 0

    def _updatePosition(self):
        if self._map is not None:
            p = list(self._sliceView().getAxialView().getCursorWorldPosition())
            spacing = self._map.getSpacing()
            size = list(self._map.getSize())
            size[0] -= 1
            size[1] -= 1
            size[2] -= 1
            x = int(p[0] // spacing[0])
            y = int(p[1] // spacing[1])
            z = int(p[2] // spacing[2])
            if x < 0: x = 0
            elif x > size[0]: x = size[0]
            if y < 0: y = 0
            elif y > size[1]: y = size[1]
            if z < 0: z = 0
            elif z > size[2]: z = size[2]
            if not self._map.isDefaultOrigin():
                origin = self._map.getOrigin()
                p[0] -= origin[0]
                p[1] -= origin[1]
                p[2] -= origin[2]
            # Coordinates
            self._cursor = (x, y, z)
            self._group6.setTitle('Cursor position {} {} {}'.format(x, y, z))
            if self._map.acquisition.isTMap():
                # t-value
                t = self._map[x, y, z]
                self._lbcurt.show()
                self._lbcurt.setText('t-value {:.2f}'.format(t))
                # z-value
                df = self._map.acquisition.getDegreesOfFreedom()
                z = tToz(t, df)
                self._lbcurz.setText('z-score {:.2f}'.format(z))
                # uncorrected p-value
                p = tTopvalue(t, df)
                self._lbcurp.setText('uncorrected p-value {}'.format(self._getFormattedValue(p)))
                # Bonferroni corrected p-value
                p = pCorrectedBonferroni(p, self._nb)
                self._lbcurbcp.setText('Bonferroni corrected p-value {}'.format(self._getFormattedValue(p)))
                # Gaussian-field corrected p-value
                p = tToVoxelCorrectedpvalue(t, df, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                self._lbcurgcp.setText('Gaussian-field corrected p-value {}'.format(self._getFormattedValue(p)))
            else:
                # t-value
                self._lbcurt.hide()
                # z-value
                self._lbcurz.setText('z-score {:.2f}'.format(self._map[x, y, z]))
                # uncorrected p-value
                p = zTopvalue(z)
                self._lbcurp.setText('uncorrected p-value {}'.format(self._getFormattedValue(p)))
                # Bonferroni corrected p-value
                p = pCorrectedBonferroni(p, self._nb)
                self._lbcurbcp.setText('Bonferroni corrected p-value {}'.format(self._getFormattedValue(p)))
                # Gaussian-field corrected p-value
                p = zToVoxelCorrectedpvalue(z, self._rc[0], self._rc[1], self._rc[2], self._rc[3])
                self._lbcurgcp.setText('Gaussian-field corrected p-value {}'.format(self._getFormattedValue(p)))
            if self._design is not None:
                i = self._views.currentIndex()
                if i == 2: self._updateBetaChart()
                elif i == 3: self._updateTimeSeriesChart()
                elif i == 4: self._updateRegressionChart()

    def _saveBitmap(self):
        if self._map is not None:
            i = self._views.currentIndex()
            if i > 1:
                if i == 2: title, fig = 'Save beta chart capture', self._fig1
                elif i == 3: title, fig = 'Save time series chart capture', self._fig2
                elif i ==4: title, fig = 'Save regression chart capture', self._fig3
                else: return
                filename = join(self._map.getDirname(), self._views.tabText(i) + '.jpg')
                filename = QFileDialog.getSaveFileName(self, title, filename,
                                                       filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;'
                                                              'TIFF (*.tiff);;SVG (*.svg)',
                                                       initialFilter='JPG (*.jpg)')[0]
                QApplication.processEvents()
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    try: fig.savefig(filename)
                    except Exception as err: messageBox(self, 'Save capture error', text='{}'.format(err))

    def _copyClipboard(self):
        if self._map is not None:
            i = self._views.currentIndex()
            if i > 1:
                if i == 2: title, fig = 'Copy beta chart capture to clipboard', self._fig1
                elif i == 3: title, fig = 'Copy time series chart capture to clipboard', self._fig2
                elif i == 4: title, fig = 'Copy regression chart capture to clipboard', self._fig3
                else: return
                tmp = join(getcwd(), 'tmp.png')
                try:
                    fig.savefig(tmp)
                    img = QPixmap(tmp)
                    QApplication.clipboard().setPixmap(img)
                except Exception as err:
                    messageBox(self, title=title, text='error: {}'.format(err))
                finally:
                    if exists(tmp): remove(tmp)

    def _copyScreenshot(self):
        if self._map is not None:
            if self._scrshot is not None:
                self._copyClipboard()
                self._scrshot.pasteFromClipboard()

    def _doubleClicked(self, modelindex):
        if self._map is not None:
            r = modelindex.row()
            spacing = self._map.getSpacing()
            x = self._model.item(r, 0).data(Qt.UserRole) * spacing[0]
            y = self._model.item(r, 1).data(Qt.UserRole) * spacing[1]
            z = self._model.item(r, 2).data(Qt.UserRole) * spacing[2]
            self._sliceView().getAxialView().setCursorWorldPosition(x, y, z, signal=True)
            self._updatePosition()

    # Public methods

    def setMap(self, v: SisypheVolume, wait: DialogWait | None = None) -> None:
        if v.acquisition.isStatisticalMap():
            self._map = v
            if self._map.acquisition.hasContrast():
                c = array(self._map.acquisition.getContrast()).sum()
                if c > 0.0: self._map.display.getLUT().setLutToHot()
                else: self._map.display.getLUT().setLutToWinter()
            else: self._map.display.getLUT().setLutToHot()
            self._mask = self._map.getNonZeroMask()
            self._nb = self._map.getNumberOfNonZero()
            ac = self._map.acquisition.getAutoCorrelations()
            self._res = ac[0] * ac[1] * ac[2] / self._map.getVoxelVolume()
            self._rc = reselCount(self._mask, ac[0], ac[1], ac[2], wait)
            if self._map.acquisition.isICBM152():
                self.setBrodmannLabel(wait=wait)
                self.setAnatomyLabel(wait=wait)
                self.setBackgroundVolume(wait=wait)
            # load design
            path = join(dirname(self._map.getFilename()), '*' + SisypheDesign.geFileExt())
            filenames = glob(path)
            if len(filenames) > 0:
                for filename in filenames:
                    if exists(filename):
                        wait.setInformationText('Load design {}...'.format(basename(filename)))
                        design = SisypheDesign()
                        design.load(filename, wait)
                        anat = design.getMeanObservations()
                        if anat.getID() == self._map.getID():
                            self._anat = anat
                            self._design = design
            if self._anat is not None:
                if not self._map.acquisition.isICBM152():
                    if self._anat.hasTransform(getID_ICBM152()):
                        trf = self._anat.getTransformFromID(getID_ICBM152())
                        wait.hide()
                        r = messageBox(self,
                                       title=self.windowTitle(),
                                       text='Would you like to normalize statistical map in ICBM152 space ?',
                                       icon=QMessageBox.Question,
                                       buttons=QMessageBox.Yes | QMessageBox.No,
                                       default=QMessageBox.No)
                        wait.show()
                        if r == QMessageBox.Yes:
                            filename = self._map.getFilename()
                            wait.setInformationText('{} spatial normalization...'.format(basename(filename)))
                            f = SisypheApplyTransform()
                            f.setTransform(trf)
                            f.setInterpolator('linear')
                            f.setMoving(self._map)
                            self._map = f.resampleMoving(save=False)
                            settings = SisypheFunctionsSettings()
                            prefix = settings.getFieldValue('Resample', 'NormalizationPrefix')
                            suffix = settings.getFieldValue('Resample', 'NormalizationSuffix')
                            if prefix is None: prefix = 'ICBM152'
                            if suffix is None: suffix = ''
                            self._map.setFilename(filename)
                            self._map.setFilenamePrefix(prefix)
                            self._map.setFilenameSuffix(suffix)
                            self._map.setOrigin(getOrigin_ICBM152())
                            self._map.setIDtoICBM152()
                            wait.setInformationText('Save {}...'.format(basename(filename)))
                            self._map.save()
                            self.setBrodmannLabel(wait)
                            self.setAnatomyLabel(wait)
                            self.setBackgroundVolume(wait)
                            self._design = None
                        else:
                            trf = trf.getInverseTransform()
                            trf.setID(self._map)
                            trf.setSize(self._map.getSize())
                            trf.setSpacing(self._map.getSpacing())
                            f = SisypheApplyTransform()
                            f.setTransform(trf)
                            filename = join(getICBM152Path(), 'icbm152_asym_template_t1_brain.xvol')
                            if exists(filename):
                                wait.setInformationText('Open ICBM152 T1 brain...')
                                v = SisypheVolume()
                                v.load(filename)
                                f.setInterpolator('linear')
                                f.setMoving(v)
                                self._anat = f.resampleMoving(save=False)
                                self._anat.setOrigin(self._map.getOrigin())
                                self._anat.setID(self._map.getID())
                            filename = join(getICBM152Path(), 'LABELLING', 'icbm152_brodmann.xvol')
                            if exists(filename):
                                wait.setInformationText('Open ICBM152 Brodmann labels...')
                                v = SisypheVolume()
                                v.load(filename)
                                f.setInterpolator('nearest')
                                f.setMoving(v)
                                self._brodmann = f.resampleMoving(save=False)
                                self._brodmann.setOrigin(self._map.getOrigin())
                                self._brodmann.setID(self._map.getID())
                                self._brodmann.acquisition.setLabels(v)
                                self._brodmann.setFilename(filename)
                                self._brodmann.setFilenameSuffix('brodmann')
                            filename = join(getICBM152Path(), 'LABELLING', 'icbm152_harvard_oxford.xvol')
                            if exists(filename):
                                wait.setInformationText('Open ICBM152 Anatomy labels...')
                                v = SisypheVolume()
                                v.load(filename)
                                f.setInterpolator('nearest')
                                f.setMoving(v)
                                self._anatomy = f.resampleMoving(save=False)
                                self._anatomy.setOrigin(self._map.getOrigin())
                                self._anatomy.setID(self._map.getID())
                                self._anatomy.acquisition.setLabels(v)
                                self._anatomy.setFilename(filename)
                                self._anatomy.setFilenameSuffix('anatomy')
            # init views
            if self._anat is not None: self._sliceView.setVolume(self._anat)
            else: self._sliceView.setVolume(self._mask)
            self._sliceView().getAxialView().setCursorVisibilityOn()
            self._sliceView().setCursorOpacity(0.25)
            self._sliceView().getAxialView().CursorPositionChanged.connect(self._updatePosition)
            self._sliceView().getCoronalView().CursorPositionChanged.connect(self._updatePosition)
            self._sliceView().getSagittalView().CursorPositionChanged.connect(self._updatePosition)
            if self._design is not None:
                self._views.setTabVisible(2, True)
                self._views.setTabVisible(3, True)
                self._views.setTabVisible(4, True)
            wait.hide()
            self._update()
            wait.show()
            wait.setInformationText('Window initialization...')
            self._initResults()
            self._updatePosition()
        else: raise AttributeError('{} is not a statistical map.'.format(v.getBasename()))

    def getMap(self) -> SisypheVolume | None:
        return self._map

    def hasMap(self) -> bool:
        return self._map is not None

    def hasDesign(self) -> bool:
        return self._design is not None

    def getDesign(self) -> SisypheDesign | None:
        return self._design

    def setBrodmannLabel(self,
                         v: SisypheVolume | None = None,
                         wait: DialogWait | None = None) -> None:
        self._brodmann = None
        if self._map is not None:
            if self._map.acquisition.isICBM152() and v is None:
                filename = join(getICBM152Path(), 'LABELLING', 'icbm152_brodmann.xvol')
                if exists(filename):
                    if wait is not None: wait.setInformationText('Load {}'.format(basename(filename)))
                    self._brodmann = SisypheVolume()
                    self._brodmann.load(filename)
            elif v is not None:
                if v.hasSameFieldOfView(self._map): self._brodmann = v

    def getBrodmannLabel(self) -> SisypheVolume | None:
        return self._brodmann

    def hasBrodmannLabel(self) -> bool:
        return self._brodmann is not None

    def setAnatomyLabel(self,
                        v: SisypheVolume | None = None,
                        wait: DialogWait | None = None) -> None:
        self._anatomy = None
        if self._map is not None:
            if self._map.acquisition.isICBM152() and v is None:
                filename = join(getICBM152Path(), 'LABELLING', 'icbm152_harvard_oxford.xvol')
                if exists(filename):
                    if wait is not None: wait.setInformationText('Load {}'.format(basename(filename)))
                    self._anatomy = SisypheVolume()
                    self._anatomy.load(filename)
            elif v is not None:
                if v.hasSameFieldOfView(self._map): self._anatomy = v

    def getAnatomyLabel(self) -> SisypheVolume | None:
        return self._anatomy

    def hasAnatomyLabel(self) -> bool:
        return self._anatomy is not None

    def setBackgroundVolume(self,
                            v: SisypheVolume | None = None,
                            wait: DialogWait | None = None):
        self._anat = None
        if self._map is not None:
            if self._map.acquisition.isICBM152() and v is None:
                filename = join(getICBM152Path(), 'icbm152_asym_template_t1_brain.xvol')
                if exists(filename):
                    if wait is not None: wait.setInformationText('Load {}'.format(basename(filename)))
                    self._anat = SisypheVolume()
                    self._anat.load(filename)
            elif v is not None:
                if v.hasSameFieldOfView(self._map): self._anat = v

    def getBackgroundVolume(self) -> SisypheVolume | None:
        return self._anat

    def hasBackgroundVolume(self) -> bool:
        return self._anat is not None

    def setScreenshotsGridWidget(self, widget: ScreenshotsGridWidget):
        self._scrshot = widget

    def getScreenshotsGridWidget(self) -> ScreenshotsGridWidget:
        return self._scrshot

    def report(self) -> None:
        if self._map is not None:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=12)
            pdf.cell(200, 10, 'Statistical map: {}'.format(self._map.getBasename()), border='B')
            pdf.ln(12)
            pdf.set_font("helvetica", size=10)
            if not self._map.identity.isAnonymized():
                pdf.cell(100, 10, '{}\t{}\t{} ({} years)'.format(self._map.identity.getLastname(),
                                                                 self._map.identity.getFirstname(),
                                                                 self._map.identity.getDateOfBirthday(),
                                                                 self._map.identity.getAge()),
                         markdown=True,
                         new_x='LMARGIN')
                pdf.ln(5)
            pdf.cell(100, 10, 'Acquisition date {}'.format(self._map.acquisition.getDateOfScan()))
            pdf.ln(24)
            pdf.set_font("helvetica", size=6)
            with pdf.table(borders_layout='SINGLE_TOP_LINE',
                           markdown=True) as table:
                row = table.row()
                row.cell(self._group1.title())
                row.cell('Voxel threshold')
                row.cell('Cluster extent threshold')
                row.cell('Expected')
                row.cell('Observed')
                row = table.row()
                row.cell('{}\n\t{}\n\t{}\n\t{}'.format(self._lbdof.text(),
                                                       self._lbvan.text(),
                                                       self._lbauto.text(),
                                                       self._lvresel.text()), v_align='T')
                row.cell('{}\n\t{}\n\t{}\n\t{}\n\t{}\n\t{}'.format(self._lbt.text(),
                                                                   self._lbz.text(),
                                                                   self._lbq.text(),
                                                                   self._lbp.text(),
                                                                   self._lbbcp.text(),
                                                                   self._lbgcp.text()), v_align='T')
                row.cell('{}\n\t{}\n\t{}\n\t{}\n\t{}'.format(self._lbvox.text(),
                                                             self._lbres.text(),
                                                             self._lbvol.text(),
                                                             self._lbcup.text(),
                                                             self._lbccp.text()), v_align='T')
                row.cell('{}\n\t{}\n\t{}'.format(self._lbexpv.text(),
                                                              self._lbexpc.text(),
                                                              self._lbexvc.text()), v_align='T')
                row.cell('{}\n\t{}\n\t{}'.format(self._lbobsv.text(),
                                                              self._lbobsc.text(),
                                                              self._lbobsvc.text()), v_align='T')
            pdf.ln(24)
            pdf.set_font("helvetica", size=6)
            labels = {'x': 5,
                      'y': 5,
                      'z': 5,
                      'world x': 7,
                      'world y': 7,
                      'world z': 7,
                      't-value': 8,
                      'z-score': 8,
                      'p-value': 14,
                      'Bonf. p-value': 10,
                      'Gaus. p-value': 10,
                      'Voxels': 10,
                      'Resels': 10,
                      'Volume': 12,
                      'cluster p-value': 15,
                      'cluster corr. p-value': 15,
                      'Brodmann': 20,
                      'Anatomy': 20}
            if self._brodmann is None: labels.pop('Brodmann')
            if self._anatomy is None: labels.pop('Anatomy')
            # noinspection PyTypeChecker
            with pdf.table(width=190,
                           align='CENTER',
                           col_widths=list(labels.values()),
                           borders_layout='SINGLE_TOP_LINE',
                           markdown=True) as table:
                row = table.row()
                for l in labels:
                    row.cell(l, align='C', v_align='T')
                n = self._model.rowCount()
                for i in range(n):
                    row = table.row()
                    for j in range(len(labels)):
                        item = self._model.item(i, j)
                        if item is None: buff = ''
                        else: buff = item.text()
                        row.cell(buff, align='C')
            # Save
            filename = splitext(self._map.getFilename())[0] + '.pdf'
            filename = QFileDialog.getSaveFileName(self, 'Save report', filename,
                                                   filter='Pdf document',
                                                   initialFilter='*.pdf')[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                try: pdf.output(filename)
                except Exception as err: messageBox(self, 'Save report error', text='{}'.format(err))

    def saveMap(self) -> None:
        df = self._map.acquisition.getDegreesOfFreedom()
        if self._map.acquisition.isTMap(): v = zTot(self._zscore, df)
        else: v = self._zscore
        r = thresholdMap(v, self._extent, self._map, )
        vol = r['map']
        vol.copyFilenameFrom(self._map)
        vol.setFilenamePrefix('thresholded')
        filename = QFileDialog.getSaveFileName(self, 'Save thresholded statistical map', vol.getFilename(),
                                               filter=SisypheVolume.getFilterExt())[0]
        QApplication.processEvents()
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            vol.saveAs(filename)

    def saveDataset(self) -> None:
        filename = splitext(self._map.getFilename())[0] + '.csv'
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
            # Pandas dataset
            d = dict()
            hdrs = list()
            for i in range(self._model.columnCount()):
                hdr = self._labels[i]
                hdr = hdr.replace('\n', ' ')
                hdrs.append(hdr)
                d[hdr] = list()
            for i in range(self._model.rowCount()):
                for j in range(self._model.columnCount()):
                    item = self._model.item(i, j)
                    if item is not None:
                        try:
                            # noinspection PyUnusedLocal
                            buff = float(item.text())
                        except: buff = item.text()
                    else: buff = ''
                    d[hdrs[j]].append(buff)
            df = DataFrame(d)
            # Save dataset
            sheet = SisypheSheet(df)
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
               messageBox(self, 'Save table dataset', text='error: {}'.format(err))
