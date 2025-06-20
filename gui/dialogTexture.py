"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - pyradiomics, Radiomics features, https://pyradiomics.readthedocs.io/en/latest/
"""

from sys import platform

from os.path import basename

from numpy import mean

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QApplication

import radiomics
from radiomics import featureextractor

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget

__all__ = ['SisypheProgressReporter',
           'DialogTexture']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> ProgressReporter
    - QDialog -> DialogTexture

Description
~~~~~~~~~~~

GUI dialog window for texture analysis.
"""


class SisypheProgressReporter(object):
    """
    SisypheProgressReporter

    Description
    ~~~~~~~~~~~

    Custom radiomics ProgressReporter class to report radiomics progression in a dialogWait instance
    (python 3.10, pyradiomics 3.0.1)

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheProgressReporter

    Creation: 14/10/2022
    Last revision: 12/02/2025
    """

    _WAIT = None

    # Public class method

    @classmethod
    def setDialogWait(cls, wait):
        if isinstance(wait, DialogWait):
            cls._WAIT = wait

    # Special methods

    def __init__(self, iterable=None, desc='', total=None):
        self._desc = desc
        self._iterable = iterable
        if total is not None:
            if self._WAIT is not None:
                self._WAIT.setProgressRange(0, int(total))
                self._WAIT.setCurrentProgressValueToMinimum()

    def __iter__(self):
        return self._iterable.__iter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self._WAIT is not None:
            self._WAIT.setCurrentProgressValueToMaximum()

    # Public methods

    def update(self, n=1):
        if self._WAIT is not None:
            if self._WAIT.getStopped(): raise UserAbortException
            if n == 1:  self._WAIT.incCurrentProgressValue()
            else:
                c = self._WAIT.getCurrentProgressValue()
                self._WAIT.setCurrentProgressValue(int(c + n))


class DialogTexture(QDialog):
    """
    DialogTexture

    Description
    ~~~~~~~~~~~

    GUI dialog window for texture analysis.
    Memory exception risk for glcm and glrlm features.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogTexture

    Error
    ~~~~~
    access violation C-error (0xC0000005) with glcm and glrlm processings

    Creation: 14/10/2022
    Last revision: 18/02/2025
    """

    _FEATURES = {'firstorder': ('10Percentile',
                                '90Percentile',
                                'Energy',
                                'Entropy',
                                'InterquartileRange',
                                'Kurtosis',
                                'Maximum',
                                'Mean',
                                'MeanAbsoluteDeviation',
                                'Median',
                                'Minimum',
                                'Range',
                                'RobustMeanAbsoluteDeviation',
                                'RootMeanSquared',
                                'Skewness',
                                'TotalEnergy',
                                'Uniformity',
                                'Variance'),
                 'glcm': ('Autocorrelation',
                          'ClusterProminence',
                          'ClusterShade',
                          'ClusterTendency',
                          'Contrast',
                          'Correlation',
                          'DifferenceAverage',
                          'DifferenceEntropy',
                          'DifferenceVariance',
                          'Dissimilarity',
                          'Homogeneity1',
                          'Homogeneity2',
                          'Id',
                          'Idn',
                          'Idm',
                          'Idmn',
                          'Imc1',
                          'Imc2',
                          'InverseVariance',
                          'JointAverage',
                          'JointEnergy',
                          'MaximumProbability',
                          'MCC',
                          'SumAverage',
                          'SumEntropy',
                          'SumSquares',
                          'SumVariance'),
                 'gldm': ('DependenceEntropy',
                          'DependenceNonUniformity',
                          'DependenceNonUniformityNormalized',
                          'DependenceVariance',
                          'GrayLevelNonUniformity',
                          'GrayLevelVariance',
                          'HighGrayLevelEmphasis',
                          'LargeDependenceEmphasis',
                          'LargeDependenceHighGrayLevelEmphasis',
                          'LargeDependenceLowGrayLevelEmphasis',
                          'LowGrayLevelEmphasis',
                          'SmallDependenceEmphasis',
                          'SmallDependenceHighGrayLevelEmphasis',
                          'SmallDependenceLowGrayLevelEmphasis'),
                 'glrlm': ('GrayLevelNonUniformity',
                           'GrayLevelNonUniformityNormalized',
                           'GrayLevelVariance',
                           'HighGrayLevelRunEmphasis',
                           'LongRunEmphasis',
                           'LongRunHighGrayLevelEmphasis'
                           'LongRunLowGrayLevelEmphasis'
                           'LowGrayLevelRunEmphasis',
                           'RunEntropy',
                           'RunLengthNonUniformity',
                           'RunLengthNonUniformityNormalized',
                           'RunPercentage',
                           'RunVariance',
                           'ShortRunEmphasis',
                           'ShortRunLowGrayLevelEmphasis',
                           'ShortRunHighGrayLevelEmphasis'),
                 'glszm': ('GrayLevelNonUniformity',
                           'GrayLevelNonUniformityNormalized',
                           'GrayLevelVariance',
                           'HighGrayLevelZoneEmphasis',
                           'LargeAreaEmphasis',
                           'LargeAreaHighGrayLevelEmphasis',
                           'LargeAreaLowGrayLevelEmphasis',
                           'LowGrayLevelZoneEmphasis',
                           'SizeZoneNonUniformity',
                           'SizeZoneNonUniformityNormalized',
                           'SmallAreaEmphasis',
                           'SmallAreaHighGrayLevelEmphasis',
                           'SmallAreaLowGrayLevelEmphasis',
                           'ZoneEntropy',
                           'ZonePercentage',
                           'ZoneVariance'),
                 'ngtdm': ('Busyness',
                           'Coarseness',
                           'Contrast',
                           'Complexity',
                           'Strength')}

    # Class method

    @classmethod
    def getFeaturesDict(cls):
        return cls._FEATURES

    # Special method

    """
    Private attributes

    _files      FilesSelectionWidget, files selection
    _features   QTreeWidget, texture features selection
    _radius     LabeledSpinBox, kernel radius
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Texture feature maps')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Files selection widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._layout.addWidget(self._files)

        # Texture features selection

        self._features = QTreeWidget()
        self._features.setHeaderLabel('Texture feature(s) selection')
        # noinspection PyUnresolvedReferences
        self._features.itemChanged.connect(self._onFeatureCheck)
        for k in self._FEATURES.keys():
            item = QTreeWidgetItem(self._features)
            item.setCheckState(0, Qt.Unchecked)
            if k == 'firstorder': title = 'First order features'
            elif k == 'glcm': title = 'Gray Level Co-occurrence Matrix features'
            elif k == 'gldm': title = 'Gray level dependence matrix features'
            elif k == 'glrlm': title = 'Gray Level Run Length Matrix features'
            elif k == 'glszm': title = 'Gray level size zone matrix features'
            elif k == 'ngtdm': title = 'Neighbouring gray tone difference matrix features'
            else: raise ValueError('Invalid feature')
            item.setText(0, title)
            self._features.addTopLevelItem(item)
            for f in self._FEATURES[k]:
                subitem = QTreeWidgetItem(item)
                subitem.setCheckState(0, Qt.Unchecked)
                subitem.setText(0, f)
                item.addChild(subitem)
        self._layout.addWidget(self._features)

        self._uncheck = QPushButton('Uncheck all')
        self._uncheck.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._uncheck.clicked.connect(self._onUncheckAll)
        lyout = QHBoxLayout()
        lyout.addWidget(self._uncheck)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        self._settings = FunctionSettingsWidget('TextureImageFilter', parent=self)
        self._settings.setButtonsVisibility(False)
        self._settings.setIOButtonsVisibility(False)
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close')
        self._ok.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Calculate texture feature maps.')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        lyout.addWidget(self._ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Private methods

    # noinspection PyUnusedLocal
    @staticmethod
    def _onFeatureCheck(item, c: int):
        n = item.childCount()
        if n > 0:
            state = item.checkState(0)
            for i in range(n):
                subitem = item.child(i)
                subitem.setCheckState(0, state)

    def _onUncheckAll(self):
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            for j in range(item.childCount()):
                subitem = item.child(j)
                # noinspection PyTypeChecker
                subitem.setCheckState(0, Qt.Unchecked)

    def _hasFeatureChecked(self):
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            for j in range(item.childCount()):
                subitem = item.child(j)
                if subitem.checkState(0) == Qt.Checked: return True
        return False

    # Public methods

    def getFilesSelectionWidget(self):
        return self._files

    # < Revision 13/02/2025
    # add setFilenames method
    def setFilenames(self, filenames: str | list[str]):
        if isinstance(filenames, str): filenames = [filenames]
        self._files.add(filenames)
    # Revision 13/02/2025 >

    def getFilenames(self) -> list[str]:
        return self._files.getFilenames()

    # < Revision 13/02/2025
    # add getParametersDict method
    def getParametersDict(self) -> dict:
        r = dict()
        r['Radius'] = self._settings.getParameterValue('KernelRadius')
        r['Batch'] = self._settings.getParameterValue('VoxelBatch')
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            for j in range(item.childCount()):
                subitem = item.child(j)
                if subitem.checkState(0) == Qt.Checked:
                    # < Revision 18/02/2025
                    k1 = item.text(0).replace(' ', '_')
                    k2 = subitem.text(0).replace(' ', '_')
                    # Revision 18/02/2025 >
                    if k1 not in r: r[k1] = dict()
                    r[k1][k2] = True
        return r
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add setParametersFromDict method
    def setParametersFromDict(self, params: dict):
        if 'Radius' in params:
            v = params['Radius']
            if isinstance(v, str): v = int(v)
            self._settings.setParameterValue('KernelRadius', v)
        if 'Batch' in params:
            v = params['Batch']
            if isinstance(v, str): v = int(v)
            self._settings.setParameterValue('VoxelBatch', v)
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            for j in range(item.childCount()):
                subitem = item.child(j)
                # < Revision 18/02/2025
                k1 = item.text(0).replace(' ', '_')
                k2 = subitem.text(0).replace(' ', '_')
                # Revision 18/02/2025 >
                if k1 in params:
                    if k2 in params[k1]:
                        v = params[k1][k2]
                        if isinstance(v, bool):
                            if v is True:
                                # noinspection PyTypeChecker
                                subitem.setCheckState(0, Qt.Checked)
                            else:
                                # noinspection PyTypeChecker
                                subitem.setCheckState(0, Qt.Unchecked)
                        if isinstance(v, str):
                            if v == 'True':
                                # noinspection PyTypeChecker
                                subitem.setCheckState(0, Qt.Checked)
                            else:
                                # noinspection PyTypeChecker
                                subitem.setCheckState(0, Qt.Unchecked)
                    else:
                        # noinspection PyTypeChecker
                        subitem.setCheckState(0, Qt.Unchecked)
                else:
                    # noinspection PyTypeChecker
                    subitem.setCheckState(0, Qt.Unchecked)
    # Revision 13/02/2025 >

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            if self._hasFeatureChecked():
                title = 'Texture features maps'
                wait = DialogWait(title=title, cancel=True)
                wait.open()
                QApplication.processEvents()
                radiomics.setVerbosity(20)  # INFO
                SisypheProgressReporter.setDialogWait(wait)
                radiomics.progressReporter = SisypheProgressReporter
                extractor = featureextractor.RadiomicsFeatureExtractor()
                s = extractor.settings
                try: s['kernelRadius'] = self._settings.getParameterValue('KernelRadius')
                except: s['kernelRadius'] = 2
                # Voxel batch used to avoid memory errors
                # s['voxelBatch'] = 16384  # 128 x 128 voxels
                try: s['voxelBatch'] = self._settings.getParameterValue('VoxelBatch')
                except: s['voxelBatch'] = 2048
                for filename in self._files.getFilenames():
                    wait.setInformationText(basename(filename))
                    v = SisypheVolume()
                    try:
                        v.load(filename)
                        img = v.getSITKImage()
                        t = mean(v.getNumpy())
                        mask = img > t
                    except Exception as err:
                        wait.hide()
                        messageBox(self, title=title, text='{}'.format(err))
                        continue
                    for i in range(self._features.topLevelItemCount()):
                        item = self._features.topLevelItem(i)
                        for j in range(item.childCount()):
                            subitem = item.child(j)
                            if subitem.checkState(0) == Qt.Checked:
                                wait.setInformationText('{}\n{} {} processing'.format(basename(filename),
                                                                                      item.text(0),
                                                                                      subitem.text(0)))
                                wait.setProgressVisibility(True)
                                extractor.disableAllFeatures()
                                idx = self._features.indexOfTopLevelItem(item)
                                if idx == 0: extractor.enableFeaturesByName(firstorder=[subitem.text(0)])
                                elif idx == 1: extractor.enableFeaturesByName(glcm=[subitem.text(0)])
                                elif idx == 2: extractor.enableFeaturesByName(gldm=[subitem.text(0)])
                                elif idx == 3: extractor.enableFeaturesByName(glrlm=[subitem.text(0)])
                                elif idx == 4: extractor.enableFeaturesByName(glszm=[subitem.text(0)])
                                else: extractor.enableFeaturesByName(ngtdm=[subitem.text(0)])
                                try:
                                    result = extractor.execute(img, mask, voxelBased=True)
                                    l = list(result.keys())
                                    rimg = result[l[-1]]
                                    m = SisypheVolume()
                                    m.copyFromSITKImage(rimg)
                                    m.copyAttributesFrom(v, display=False)
                                    m.setFilename(v.getFilename())
                                    # < Revision 13/02/2025
                                    # m.setFilenamePrefix('{}_{}'.format(l[-1][9:], subitem.text(0)))
                                    m.setFilenamePrefix('{}_{}'.format(item.text(0), subitem.text(0)))
                                    # Revision 13/02/2025 >
                                    m.updateArrayID()
                                    # < Revision 18/02/2025
                                    # add modality, sequence
                                    m.acquisition.setModalityToOT()
                                    m.acquisition.setSequence('{} {}'.format(item.text(0), subitem.text(0)))
                                    # Revision 18/02/2025 >
                                    m.save()
                                    wait.setInformationText('{}\nSave {} {} map'.format(basename(filename),
                                                                                        item.text(0),
                                                                                        subitem.text(0)))
                                except UserAbortException: break
                                except Exception as err:
                                    wait.hide()
                                    messageBox(self, title=title, text='{}'.format(err))
                                    continue
                wait.close()
                self._files.clearall()
