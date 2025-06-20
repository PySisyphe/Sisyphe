"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool,  https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename

from shutil import rmtree

from numpy import load
from numpy import array
from numpy import save
from numpy import arange

from pandas import DataFrame

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.processing.timeSeriesFunctions import seriesPreprocessing
from Sisyphe.processing.timeSeriesFunctions import seriesFastICA
from Sisyphe.processing.timeSeriesFunctions import seriesSeedToVoxel
from Sisyphe.processing.timeSeriesFunctions import seriesConnectivityMatrix
from Sisyphe.processing.timeSeriesFunctions import seriesGroupICA
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogSeriesPreprocessing',
           'DialogSeriesFastICA',
           'DialogSeriesSeedToVoxel',
           'DialogSeriesConnectivityMatrix',
           'DialogSeriesCanICA']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogSeriesPreprocessing
    - QDialog -> DialogSeriesPreprocessing -> DialogSeriesFastICA
                                           -> DialogSeriesSeedToVoxel
                                           -> DialogSeriesConnectivityMatrix
    - QDialog -> DialogSeriesCanICA
"""


class DialogSeriesPreprocessing(QDialog):
    """
    DialogSeriesPreprocessing

    Description
    ~~~~~~~~~~~

    GUI dialog window for time series preprocessing.

    Proposed preprocessing:
    - extract confound regressor variables
    (example of confound variables: motion correction parameters, global signal, wm signal, csf signal)
    - gaussian spatial smoothing
    - detrend
    - standardize signal (z-scored i.e. timeseries are shifted to zero mean and scaled to unit variance)
    - standardize confound regressor variables (z-scored)
    - high variance confounds computation
    - low pass filter
    - high pass filter

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesPreprocessing

    Creation: 06/02/2025
    Last revision:
    """

    # Special method

    """
    Private attributes
    
    _process    QPushButton
    _series     FileSelectionWidget
    _settings   FunctionSettingsWidget
    _map        FileSelectionWidget
    _tissue     QCheckBox
    _nobs       int
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Time series preprocessing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._nobs: int = 0
        self._series = FileSelectionWidget()
        self._series.filterSisypheVolume()
        self._series.setTextLabel('Time series')
        self._series.filterMultiComponent()
        self._series.FieldChanged.connect(self._seriesChanged)
        self._layout.addWidget(self._series)

        self._confounds = FilesSelectionWidget()
        self._confounds.setTextLabel('Confound variable(s)')
        self._confounds.filterExtension('.csv')
        self._confounds.filterExtension('.xlsx')
        self._confounds.filterExtension('.xsheet')
        self._confounds.filterExtension('.npy')
        self._confounds.FieldChanged.connect(self._confoundChanged)
        self._layout.addWidget(self._confounds)

        self._settings = FunctionSettingsWidget('TimeSeriesPreprocessing')
        self._settings.settingsVisibilityOn()
        self._settings.hideIOButtons()
        self._settings.hideButtons()
        self._tissue = self._settings.getParameterWidget('TissueConfounds')
        self._tissue.clicked.connect(self._tissueClicked)
        self._settings.setParameterVisibility('TissueMap', False)
        self._map = self._settings.getParameterWidget('TissueMap')
        self._map.filterSisypheVolume()
        self._map.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Execute preprocessing.')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

        # < Revision 10/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._series.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 10/06/2025 >
        self.setModal(True)
    # Private method

    def _center(self):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _confoundChanged(self):
        if not self._confounds.isEmpty():
            n = 0
            v = ''
            filename = self._confounds.getFilenames()[-1]
            ext = splitext(filename)[1]
            ext = ext.lower()
            if ext == '.npy':
                try:
                    v = load(filename)
                    if v.ndim == 1: n = v.shape[0]
                    elif v.ndim == 2: n = v.shape[1]
                    else:
                        messageBox(self,
                                   'Open confound variable',
                                   text='{} ndim ndarray is not supported.'.format(v.ndim))
                        n = 0
                except Exception as err:
                    messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                    n = 0
            elif ext in ['.csv', '.xlsx', 'xsheet']:
                try:
                    v = SisypheSheet()
                    if ext == '.csv': v.loadCSV(filename)
                    elif ext == '.xlsx': v.loadXLSX(filename)
                    elif ext == '.xsheet': v.load(filename)
                    n = v.shape[1]
                except Exception as err:
                    messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                    n = 0
            else:
                messageBox(self,
                           'Open confound variable',
                           text='{} format is not supported.'.format(ext))
            if n > 0 and n == self._nobs:
                item = self._confounds.getItemFromIndex(self._confounds.filenamesCount() - 1)
                item.setToolTip('{}'.format(v))
            else:
                if n > 0:
                    messageBox(self,
                               'Open confound variable',
                               text='Invalid number of elements in {}.\n'
                                    '{} elements in array, {} expected.'.format(basename(filename),
                                                                                n, self._nobs))
                self._counfounds.clearLastItem(signal=False)

    def _seriesChanged(self):
        if not self._series.isEmpty():
            r = SisypheVolume.getVolumeAttributes(self._series.getFilename())
            self._map.clear()
            self._map.filterSameFOV(r['fov'])
            self._nobs = r['components']
            self._confounds.setEnabled(True)
            self._process.setEnabled(True)
        else:
            self._nobs = 0
            self._confounds.clear(signal=False)
            self._confounds.setEnabled(False)
            self._process.setEnabled(False)

    # noinspection PyUnusedLocal
    def _tissueClicked(self, checked):
        self._settings.setParameterVisibility('TissueMap', self._tissue.isChecked())
        self._center()

    # Public method

    def execute(self):
        if not self._series.isEmpty():
            fwhm = self._settings.getParameterValue('Smoothing')
            if fwhm == 0.0: fwhm = None
            detrend = self._settings.getParameterValue('Detrend')
            std = self._settings.getParameterValue('Std')
            stdconfounds = self._settings.getParameterValue('StdConfounds')
            highvarconfounds = self._settings.getParameterValue('HighConfounds')
            lowpass = self._settings.getParameterValue('LowPass')
            if lowpass == 0.0: lowpass = None
            highpass = self._settings.getParameterValue('HighPass')
            if highpass == 0.0: highpass = None
            # tr = float(self._settings.getParameterValue('TR'))
            tr = float(self._settings.getParameterValue('TR')) / 1000.0
            prefix = self._settings.getParameterValue('Prefix')
            if prefix is None: prefix = ''
            suffix = self._settings.getParameterValue('Suffix')
            if suffix is None: suffix = ''
            if prefix == '' and suffix == '': prefix = 'flt'
            wait = DialogWait()
            wait.open()
            # matrix of confounding variables
            data = dict()
            confmat = None
            # open confounding variables
            if not self._confounds.isEmpty():
                filenames = self._confounds.getFilename()
                for filename in filenames:
                    wait.setInformationText('Open {} confounding variable...'.format(basename(filename)))
                    ext = splitext(filename)[1]
                    ext = ext.lower()
                    if ext == '.npy':
                        try:
                            v = load(filename)
                            if v.ndim == 1: data[basename(filename)] = v
                            elif v.ndim == 2:
                                for i in range(v.shape[0]):
                                    data['{}#{}'.format(basename(filename), i)] = v[:, i].flatten()
                        except Exception as err:
                            messageBox(self, 'Open confounding variable', text='error: {}'.format(err))
                            continue
                    elif ext in ['.csv', '.xlsx', 'xsheet']:
                        try:
                            v = SisypheSheet()
                            if ext == '.csv': v.loadCSV(filename)
                            elif ext == '.xlsx': v.loadXLSX(filename)
                            elif ext == '.xsheet': v.load(filename)
                            hdr = v.columns
                            v = v.values
                            if v.ndim == 1: data[basename(filename)] = v
                            elif v.ndim == 2:
                                for i in range(v.shape[0]):
                                    data[hdr[i]] = v[:, i].flatten()
                        except Exception as err:
                            messageBox(self, 'Open confounding variable', text='error: {}'.format(err))
                            continue
            # add global, csf, gm, wm signal confounding variables
            tissue = self._settings.getParameterValue('TissueConfounds')
            filename = self._settings.getParameterValue('TissueMap')
            if tissue and exists(filename):
                wait.setInformationText('Open tissue label map...'.format(basename(filename)))
                lbl = SisypheVolume()
                lbl.load(filename)
                wait.setInformationText('Processing tissue confounding variables....'.format(basename(filename)))
                # global confound
                v = lbl.getMean(mask=lbl > 0)
                data['global'] = array(v)
                # csf signal confound (label 1)
                v = lbl.getMean(mask=lbl == 1)
                data['csf'] = array(v)
                # gm signal confound (label 2)
                v = lbl.getMean(mask=lbl == 2)
                data['gm'] = array(v)
                # wm signal confound (label 3)
                v = lbl.getMean(mask=lbl == 3)
                data['wm'] = array(v)
            if len(data) > 0:
                try: confmat = DataFrame(data)
                except: confmat = None
            try:
                wait.setInformationText('Open {}...'.format(basename(self._series.getFilename())))
                vols = SisypheVolume()
                vols.load(self._series.getFilename())
                r = seriesPreprocessing(vols, confmat, fwhm, detrend, std, stdconfounds,
                                        highvarconfounds, lowpass, highpass, tr, wait)
                r.setFilename(self._series.getFilename())
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                wait.setInformationText('Save {}...'.format(r.getBasename()))
                r.save()
            except Exception as err:
                wait.hide()
                messageBox(self, 'Time series preprocessing', text='error: {}'.format(err))
                # < Revision 12/06/2025
                # remove nilearn cache
                cache = join(getcwd(), 'nilearn_cache')
                if exists(cache): rmtree(cache)
                # Revision 12/06/2025 >
            wait.close()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform\nanother time series preprocessing ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._series.clear()
                self._map.clear()
            else: self.accept()


class DialogSeriesSeedToVoxel(DialogSeriesPreprocessing):
    """
    DialogSeriesSeedToVoxel

    Description
    ~~~~~~~~~~~

    GUI dialog window for seed to voxel correlation map processing.
    This map depicts the temporal correlation of a seed region with the rest of the brain.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesPreprocessing -> DialogSeriesSeedToVoxel

    Creation: 06/02/2025
    Last revision:
    """

    # Special method

    """
    Private attributes

    _settings2  FunctionSettingsWidget
    _roi        FileSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Time series seed to voxel')

        # Init widgets

        self._settings2 = FunctionSettingsWidget('TimeSeriesSeedToVoxel')
        self._settings2.settingsVisibilityOn()
        self._settings2.hideIOButtons()
        self._settings2.hideButtons()
        self._settings2.getParameterWidget('Preprocessing').clicked.connect(self._preprocessingClicked)
        idx = self._layout.indexOf(self._settings)
        self._layout.insertWidget(idx, self._settings2)

        self._roi = self._settings2.getParameterWidget('Seed')
        self._roi.filterSisypheROI()
        self._roi.FieldChanged.connect(self._roiChanged)

        self._settings.showButtons()
        self._preprocessingClicked()

        self._process.setToolTip('Execute time series seed to voxel processing.')

    # Private method

    def _center(self):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _preprocessingClicked(self):
        c = self._settings2.getParameterWidget('Preprocessing').isChecked()
        if c is True:
            self._settings.show()
            self._settings.settingsVisibilityOn()
            self._settings.setParameterVisibility('Prefix', False)
            self._settings.setParameterVisibility('Suffix', False)
            self._confounds.show()
        else:
            self._settings.hide()
            self._settings.settingsVisibilityOff()
            self._confounds.hide()
        self._center()

    def _seriesChanged(self):
        super()._seriesChanged()
        if not self._series.isEmpty():
            r = SisypheVolume.getVolumeAttributes(self._series.getFilename())
            self._roi.filterSameID(r['id'])
        self._roi.clear(signal=False)
        self._process.setEnabled(False)

    def _roiChanged(self):
        self._process.setEnabled((not self._roi.isEmpty()) and
                                 (not self._series.isEmpty()))

    # Public method

    def execute(self):
        if not self._series.isEmpty():
            wait = DialogWait()
            wait.open()
            if self._settings2.getParameterWidget('Preprocessing').isChecked():
                fwhm = self._settings.getParameterValue('Smoothing')
                if fwhm == 0.0: fwhm = None
                detrend = self._settings.getParameterValue('Detrend')
                std = self._settings.getParameterValue('Std')
                stdconfounds = self._settings.getParameterValue('StdConfounds')
                highvarconfounds = self._settings.getParameterValue('HighConfounds')
                lowpass = self._settings.getParameterValue('LowPass')
                if lowpass == 0.0: lowpass = None
                highpass = self._settings.getParameterValue('HighPass')
                if highpass == 0.0: highpass = None
                # tr = float(self._settings.getParameterValue('TR'))
                tr = float(self._settings.getParameterValue('TR')) / 1000.0
                # matrix of confounding variables
                data = dict()
                confmat = None
                # open confounding variables
                if not self._confounds.isEmpty():
                    filenames = self._confounds.getFilename()
                    for filename in filenames:
                        wait.setInformationText('Open {} confound...'.format(basename(filename)))
                        ext = splitext(filename)[1]
                        ext = ext.lower()
                        if ext == '.npy':
                            try:
                                v = load(filename)
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data['{}#{}'.format(basename(filename), i)] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                                continue
                        elif ext in ['.csv', '.xlsx', 'xsheet']:
                            try:
                                v = SisypheSheet()
                                if ext == '.csv':
                                    v.loadCSV(filename)
                                elif ext == '.xlsx':
                                    v.loadXLSX(filename)
                                elif ext == '.xsheet':
                                    v.load(filename)
                                hdr = v.columns
                                v = v.values
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data[hdr[i]] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                                continue
                # add global, csf, gm, wm signal confounding variables
                tissue = self._settings.getParameterValue('TissueConfounds')
                filename = self._settings.getParameterValue('TissueMap')
                if tissue and exists(filename):
                    wait.setInformationText('{} tissue confounding variables...'.format(basename(filename)))
                    lbl = SisypheVolume()
                    lbl.load(filename)
                    # global confound
                    v = lbl.getMean(mask=lbl > 0)
                    data['global'] = array(v)
                    # csf signal confound (label 1)
                    v = lbl.getMean(mask=lbl == 1)
                    data['csf'] = array(v)
                    # gm signal confound (label 2)
                    v = lbl.getMean(mask=lbl == 2)
                    data['gm'] = array(v)
                    # wm signal confound (label 3)
                    v = lbl.getMean(mask=lbl == 3)
                    data['wm'] = array(v)
                if len(data) > 0:
                    try:
                        # noinspection PyUnusedLocal
                        confmat = DataFrame(data)
                    except: confmat = None
            else:
                fwhm = None
                detrend = False
                std = False
                stdconfounds = False
                highvarconfounds = False
                lowpass = None
                highpass = None
                tr = 2.0
                confmat = None
            try:
                wait.setInformationText('Open {}...'.format(basename(self._series.getFilename())))
                vols = SisypheVolume()
                vols.load(self._series.getFilename())
                roi = SisypheROI()
                roi.load(self._roi.getFilename())
                wait.setInformationText('{} seed to voxel processing...'.format(basename(self._series.getFilename())))
                r = seriesSeedToVoxel(vols, roi, confmat, fwhm, detrend, std, stdconfounds,
                                      highvarconfounds, lowpass, highpass, tr, wait)
                wait.setInformationText('Save {}...'.format(r['cc'].getBasename()))
                r['cc'].save()
                wait.setInformationText('Save {}...'.format(r['z'].getBasename()))
                r['z'].save()
            except Exception as err:
                wait.hide()
                messageBox(self, 'Seed to voxel processing', text='error: {}'.format(err))
                # < Revision 12/06/2025
                # remove nilearn cache
                cache = join(getcwd(), 'nilearn_cache')
                if exists(cache): rmtree(cache)
                # Revision 12/06/2025 >
            wait.close()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform\nanother seed to voxel processing ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._series.clear()
                self._map.clear()
            else: self.accept()


class DialogSeriesFastICA(DialogSeriesPreprocessing):
    """
    DialogSeriesFastICA

    Description
    ~~~~~~~~~~~

    GUI dialog window for single-subject time series ICA processing.
    Independent component analysis (ICA) separates a multivariate signal into additive subcomponents that are maximally
    independent. Typically, ICA is not used for reducing dimensionality but for separating superimposed signals.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesPreprocessing -> DialogSeriesFastICA

    Creation: 06/02/2025
    Last revision:
    """

    # Special method

    """
    Private attributes
    
    _settings2  FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Single-subject time Series ICA')

        # Init widgets

        self._settings2 = FunctionSettingsWidget('TimeSeriesFastICA')
        self._settings2.settingsVisibilityOn()
        self._settings2.hideIOButtons()
        self._settings2.hideButtons()
        self._settings2.getParameterWidget('Preprocessing').clicked.connect(self._preprocessingClicked)
        idx = self._layout.indexOf(self._settings)
        self._layout.insertWidget(idx, self._settings2)

        self._settings.showButtons()
        self._settings.setParameterVisibility('Std', False)
        self._preprocessingClicked()

        self._process.setToolTip('Execute single-subject time series ICA processing.')

    # Private method

    def _center(self):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _preprocessingClicked(self):
        c = self._settings2.getParameterWidget('Preprocessing').isChecked()
        if c is True:
            self._settings.show()
            self._settings.settingsVisibilityOn()
            self._settings.setParameterVisibility('Std', False)
            self._settings.setParameterVisibility('Prefix', False)
            self._settings.setParameterVisibility('Suffix', False)
            self._confounds.show()
        else:
            self._settings.hide()
            self._settings.settingsVisibilityOff()
            self._confounds.hide()
        self._center()

    # Public method

    def execute(self):
        if not self._series.isEmpty():
            wait = DialogWait()
            wait.open()
            if self._settings2.getParameterWidget('Preprocessing').isChecked():
                fwhm = self._settings.getParameterValue('Smoothing')
                if fwhm == 0.0: fwhm = None
                detrend = self._settings.getParameterValue('Detrend')
                stdconfounds = self._settings.getParameterValue('StdConfounds')
                highvarconfounds = self._settings.getParameterValue('HighConfounds')
                lowpass = self._settings.getParameterValue('LowPass')
                if lowpass == 0.0: lowpass = None
                highpass = self._settings.getParameterValue('HighPass')
                if highpass == 0.0: highpass = None
                # tr = self._settings.getParameterValue('TR')
                tr = float(self._settings.getParameterValue('TR')) / 1000.0
                # matrix of confounding variables
                data = dict()
                confmat = None
                # open confounding variables
                if not self._confounds.isEmpty():
                    filenames = self._confounds.getFilename()
                    for filename in filenames:
                        wait.setInformationText('Open {} confounding variable...'.format(basename(filename)))
                        ext = splitext(filename)[1]
                        ext = ext.lower()
                        if ext == '.npy':
                            try:
                                v = load(filename)
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data['{}#{}'.format(basename(filename), i)] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confounding variable', text='error: {}'.format(err))
                                continue
                        elif ext in ['.csv', '.xlsx', 'xsheet']:
                            try:
                                v = SisypheSheet()
                                if ext == '.csv':
                                    v.loadCSV(filename)
                                elif ext == '.xlsx':
                                    v.loadXLSX(filename)
                                elif ext == '.xsheet':
                                    v.load(filename)
                                hdr = v.columns
                                v = v.values
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data[hdr[i]] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confounding variable', text='error: {}'.format(err))
                                continue
                # add global, csf, gm, wm signal confounding variables
                tissue = self._settings.getParameterValue('TissueConfounds')
                filename = self._settings.getParameterValue('TissueMap')
                if tissue and exists(filename):
                    wait.setInformationText('{} tissue confounding variables...'.format(basename(filename)))
                    lbl = SisypheVolume()
                    lbl.load(filename)
                    # global confound
                    v = lbl.getMean(mask=lbl > 0)
                    data['global'] = array(v)
                    # csf signal confound (label 1)
                    v = lbl.getMean(mask=lbl == 1)
                    data['csf'] = array(v)
                    # gm signal confound (label 2)
                    v = lbl.getMean(mask=lbl == 2)
                    data['gm'] = array(v)
                    # wm signal confound (label 3)
                    v = lbl.getMean(mask=lbl == 3)
                    data['wm'] = array(v)
                if len(data) > 0:
                    try:
                        # noinspection PyUnusedLocal
                        confmat = DataFrame(data)
                    except: confmat = None
            else:
                fwhm = None
                detrend = False
                stdconfounds = False
                highvarconfounds = False
                lowpass = None
                highpass = None
                tr = 2.0
                confmat = None
            ncomp = self._settings2.getParameterValue('NumberOfComponents')
            threshold = self._settings2.getParameterValue('Threshold')
            try:
                wait.setInformationText('Open {}...'.format(basename(self._series.getFilename())))
                vols = SisypheVolume()
                vols.load(self._series.getFilename())
                wait.setInformationText('{} ICA processing...'.format(basename(self._series.getFilename())))
                r = seriesFastICA(vols, ncomp, threshold, confmat, fwhm, detrend, stdconfounds,
                                  highvarconfounds, lowpass, highpass, tr, wait)
                wait.setInformationText('Save {}...'.format(r.getBasename()))
                r.save()
            except Exception as err:
                wait.hide()
                messageBox(self, 'Single-subject ICA processing', text='error: {}'.format(err))
            wait.close()
            r = messageBox(self, title=self.windowTitle(),
                           text='Would you like to perform\nanother ICA processing ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._series.clear()
                self._map.clear()
            else: self.accept()


class DialogSeriesConnectivityMatrix(DialogSeriesPreprocessing):
    """
    DialogSeriesConnectivityMatrix

    Description
    ~~~~~~~~~~~

    GUI dialog window for connectivity matrix processing.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesPreprocessing -> DialogSeriesConnectivityMatrix

    Creation: 06/02/2025
    Last revision:
    """

    # Special method

    """
    Private attributes
    
    _settings2  FunctionSettingsWidget
    _lbl        FileSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sshot: ScreenshotsGridWidget | None = None

        # Init window

        self.setWindowTitle('Time series connectivity matrix')

        # Init widgets

        self._settings2 = FunctionSettingsWidget('TimeSeriesConnectivityMatrix')
        self._settings2.settingsVisibilityOn()
        self._settings2.hideIOButtons()
        self._settings2.hideButtons()
        self._settings2.getParameterWidget('Preprocessing').clicked.connect(self._preprocessingClicked)
        idx = self._layout.indexOf(self._settings)
        self._layout.insertWidget(idx, self._settings2)

        self._lbl = self._settings2.getParameterWidget('Label')
        self._lbl.filterSisypheVolume()
        self._lbl.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._lbl.FieldChanged.connect(self._lblChanged)

        self._settings.showButtons()
        self._preprocessingClicked()

        self._process.setToolTip('Execute time series connectivity matrix processing.')

    # Private method

    def _center(self):
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _preprocessingClicked(self):
        c = self._settings2.getParameterWidget('Preprocessing').isChecked()
        if c is True:
            self._settings.show()
            self._settings.settingsVisibilityOn()
            self._settings.setParameterVisibility('Prefix', False)
            self._settings.setParameterVisibility('Suffix', False)
            self._confounds.show()
        else:
            self._settings.hide()
            self._settings.settingsVisibilityOff()
            self._confounds.hide()
        self._center()

    def _seriesChanged(self):
        super()._seriesChanged()
        if not self._series.isEmpty():
            r = SisypheVolume.getVolumeAttributes(self._series.getFilename())
            self._lbl.filterSameID(r['id'])
        self._lbl.clear(signal=False)
        self._process.setEnabled(False)

    def _lblChanged(self):
        self._process.setEnabled((not self._lbl.isEmpty()) and
                                 (not self._series.isEmpty()))

    # Public methods

    def setScreenshotsWidget(self, widget: ScreenshotsGridWidget):
        if isinstance(widget, ScreenshotsGridWidget): self._sshot = widget
        else: raise TypeError('parameter type {} is not ScreenshotsGridWidget.'.format(type(widget)))

    def execute(self):
        if not self._series.isEmpty():
            wait = DialogWait()
            wait.open()
            if self._settings2.getParameterWidget('Preprocessing').isChecked():
                fwhm = self._settings.getParameterValue('Smoothing')
                if fwhm == 0.0: fwhm = None
                detrend = self._settings.getParameterValue('Detrend')
                std = self._settings.getParameterValue('Std')
                stdconfounds = self._settings.getParameterValue('StdConfounds')
                highvarconfounds = self._settings.getParameterValue('HighConfounds')
                lowpass = self._settings.getParameterValue('LowPass')
                if lowpass == 0.0: lowpass = None
                highpass = self._settings.getParameterValue('HighPass')
                if highpass == 0.0: highpass = None
                # tr = self._settings.getParameterValue('TR')
                tr = float(self._settings.getParameterValue('TR')) / 1000.0
                # matrix of confounding variables
                data = dict()
                confmat = None
                # open confounding variables
                if not self._confounds.isEmpty():
                    filenames = self._confounds.getFilename()
                    for filename in filenames:
                        wait.setInformationText('Open {} confound...'.format(basename(filename)))
                        ext = splitext(filename)[1]
                        ext = ext.lower()
                        if ext == '.npy':
                            try:
                                v = load(filename)
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data['{}#{}'.format(basename(filename), i)] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                                continue
                        elif ext in ['.csv', '.xlsx', 'xsheet']:
                            try:
                                v = SisypheSheet()
                                if ext == '.csv':
                                    v.loadCSV(filename)
                                elif ext == '.xlsx':
                                    v.loadXLSX(filename)
                                elif ext == '.xsheet':
                                    v.load(filename)
                                hdr = v.columns
                                v = v.values
                                if v.ndim == 1:
                                    data[basename(filename)] = v
                                elif v.ndim == 2:
                                    for i in range(v.shape[0]):
                                        data[hdr[i]] = v[:, i].flatten()
                            except Exception as err:
                                messageBox(self, 'Open confound variable', text='error: {}'.format(err))
                                continue
                # add global, csf, gm, wm signal confounding variables
                tissue = self._settings.getParameterValue('TissueConfounds')
                filename = self._settings.getParameterValue('TissueMap')
                if tissue and exists(filename):
                    wait.setInformationText('{} tissue confounding variables...'.format(basename(filename)))
                    lbl = SisypheVolume()
                    lbl.load(filename)
                    # global confound
                    v = lbl.getMean(mask=lbl > 0)
                    data['global'] = array(v)
                    # csf signal confound (label 1)
                    v = lbl.getMean(mask=lbl == 1)
                    data['csf'] = array(v)
                    # gm signal confound (label 2)
                    v = lbl.getMean(mask=lbl == 2)
                    data['gm'] = array(v)
                    # wm signal confound (label 3)
                    v = lbl.getMean(mask=lbl == 3)
                    data['wm'] = array(v)
                if len(data) > 0:
                    try:
                        # noinspection PyUnusedLocal
                        confmat = DataFrame(data)
                    except: confmat = None
            else:
                fwhm = None
                detrend = False
                std = False
                stdconfounds = False
                highvarconfounds = False
                lowpass = None
                highpass = None
                tr = 2.0
                confmat = None
            try:
                wait.setInformationText('Open {}...'.format(basename(self._series.getFilename())))
                vols = SisypheVolume()
                vols.load(self._series.getFilename())
                lbl = SisypheVolume()
                lbl.load(self._lbl.getFilename())
                wait.setInformationText('{} connectivity matrix processing...'.format(basename(self._series.getFilename())))
                mat = seriesConnectivityMatrix(vols, lbl, confmat, fwhm, detrend, std, stdconfounds,
                                               highvarconfounds, lowpass, highpass, tr, wait)
                filename = splitext(vols.getFilename())[0] + '_connectivity.npy'
                wait.setInformationText('Save {}...'.format(basename(filename)))
                save(filename, mat)
            except Exception as err:
                wait.hide()
                messageBox(self, 'Connectivity matrix processing', text='error: {}'.format(err))
                mat = None
                lbl = None
                vols = None
            wait.close()
            # Display connectivity matrix
            if (mat is not None) and (lbl is not None) and (vols is not None):
                dlg = DialogGenericResults()
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dlg, c)
                    # noinspection PyTypeChecker
                    dlg.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
                labels = list(lbl.acquisition.getLabels().values())
                title1 = 'Connectivity matrix'.format(vols.getBasename())
                title2 = 'Connectivity table'.format(vols.getBasename())
                tab1 = dlg.newTab(title1, capture=True, clipbrd=True, scrshot=self._sshot, dataset=False)
                tab2 = dlg.newTab(title2, capture=False, clipbrd=False, scrshot=None, dataset=True)
                dlg.setTreeWidgetHeaderLabels(index=tab2, labels=labels)
                labels = labels[1:]
                dlg.setTreeWidgetArray(index=tab2, arr=mat, d=3, rows=labels)
                # dlg.showTree(0)
                # dlg.showFigure(0)
                dlg._getDataFrame = lambda _, x=DataFrame(data=mat, columns=labels): x
                fig = dlg.getFigure(tab1)
                fig.set_layout_engine('constrained')
                fig.clear()
                ax = fig.add_subplot(111, anchor='C')
                # noinspection PyTypeChecker
                cax = ax.inset_axes([1.05, 0.0, 0.05, 1.0])
                im = ax.imshow(mat, cmap='jet')
                cbar = fig.colorbar(im, cax=cax, cmap='jet')
                cbar.ax.set_ylabel('Covariance', rotation=-90, va="bottom")
                n = len(labels)
                if n < 17:
                    ax.set_xticks(arange(n), labels=labels)
                    ax.set_yticks(arange(n), labels=labels)
                else:
                    ax.set_xticks(arange(n))
                    ax.set_yticks(arange(n))
                ax.tick_params(axis='x', labelrotation=90)
                dlg.exec()
            # Exit
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to perform\nanother connectivity matrix processing ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._series.clear()
            else: self.accept()


class DialogSeriesCanICA(QDialog):
    """
    DialogSeriesCanICA

    Description
    ~~~~~~~~~~~

    GUI dialog window for multi-subject time series ICA processing.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSeriesCanICA

    Creation: 11/02/2025
    Last revision:
    """

    # Special method

    """
    Private attributes

    _process    QPushButton
    _series     FileSelectionWidget
    _settings   FunctionSettingsWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Multi-subject time Series ICA')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._series = FilesSelectionWidget()
        self._series.filterSisypheVolume()
        self._series.setTextLabel('Time series')
        self._series.filterMultiComponent()
        self._series.filterICBM()
        self._series.FieldChanged.connect(self._seriesChanged)
        self._layout.addWidget(self._series)

        self._settings = FunctionSettingsWidget('TimeSeriesGroupICA')
        self._settings.settingsVisibilityOn()
        self._settings.hideIOButtons()
        self._settings.hideButtons()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        exitb = QPushButton('Close')
        exitb.setAutoDefault(True)
        exitb.setDefault(True)
        exitb.setFixedWidth(100)
        self._process = QPushButton('Execute')
        self._process.setFixedWidth(100)
        self._process.setToolTip('Execute multi-subject time series ICA processing.')
        self._process.setEnabled(False)
        layout.addWidget(exitb)
        layout.addWidget(self._process)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        exitb.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._process.clicked.connect(self.execute)

    # Private method

    def _seriesChanged(self):
        if self._series.isEmpty(): self._process.setEnabled(False)
        else: self._process.setEnabled(len(self._series.getFilenames()) > 1)

    # Public method

    def execute(self):
        filenames = self._series.getFilenames()
        if len(filenames) > 1:
            vols = list()
            wait = DialogWait()
            for filename in filenames:
                if wait is not None: wait.setInformationText('Open {}...'.format(basename(filename)))
                v = SisypheVolume()
                v.load(filename)
                vols.append(v)
            if len(vols) > 0:
                ncomp = self._settings2.getParameterValue('NumberOfComponents')
                algo = self._settings2.getParameterValue('Algorithm')[0][0]
                if algo == 'C': algo = 'ica'
                else: algo = 'dict'
                try:
                    r = seriesGroupICA(vols, ncomp, algo, wait)
                    wait.setInformationText('Save {}...'.format(r.getBasename()))
                    r.save()
                except Exception as err:
                    messageBox(self, 'Multi-subject ICA processing', text='error: {}'.format(err))
                wait.close()
                r = messageBox(self,
                               title=self.windowTitle(),
                               text='Would you like to perform\nanother multi-subject ICA processing ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes: self._series.clearall()
                else: self.accept()
