"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        pyradiomics     https://pyradiomics.readthedocs.io/en/latest/               Radiomics features
"""

from os.path import basename

from numpy import mean

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

import radiomics
from radiomics import featureextractor

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
    Class hierarchy

        
        object -> ProgressReporter
        QDialog -> DialogTexture

    Description

        GUI dialog window for texture analysis.
"""


class SisypheProgressReporter(object):
    """
        SisypheProgressReporter

        Description

            Custom radiomics ProgressReporter class to report radiomics progression in a dialogWait instance.

        Inheritance

            object -> SisypheProgressReporter

        Public class method

            setDialogWait(DialogWait)

        Public method

            update(int)

            inherited QDialog methods
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
                self._WAIT.setProgressRange(0, total)
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
            if n == 1: 
                self._WAIT.incCurrentProgressValue()
            else:
                c = self._WAIT.getCurrentProgressValue()
                self._WAIT.setCurrentProgressValue(c + n)


class DialogTexture(QDialog):
    """
        DialogTexture

        Description

            GUI dialog window for texture analysis.
            Risk of memory exception for glcm and glrlm features

        Inheritance

            QDialog -> DialogTexture

        Private attributes

            _files      FilesSelectionWidget, files selection
            _features   QTreeWidget, texture features selection
            _radius     LabeledSpinBox, kernel radius

        Public methods

            getFeaturesDict()
            FilesSelectionWidget = getFilesSelectionWidget()
            execute()

            inherited QDialog methods
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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Texture feature maps')
        self.resize(QSize(600, 500))

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
            item.setText(0, title)
            self._features.addTopLevelItem(item)
            for f in self._FEATURES[k]:
                subitem = QTreeWidgetItem(item)
                subitem.setCheckState(0, Qt.Unchecked)
                subitem.setText(0, f)
                item.addChild(subitem)
        self._layout.addWidget(self._features)

        lyout = QHBoxLayout()
        self._radius = LabeledSpinBox()
        self._radius.setTitle('Kernel radius')
        self._radius.setMinimum(1)
        self._radius.setMaximum(10)
        self._radius.setValue(2)
        self._radius.setFixedWidth(150)
        lyout.addStretch()
        lyout.addWidget(self._radius)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Calculate texture feature maps.')
        self._execute.setAutoDefault(True)
        self._execute.setDefault(True)
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        ok.clicked.connect(self.accept)
        self._execute.clicked.connect(self.execute)

    # Private methods

    @staticmethod
    def _onFeatureCheck(item, c):
        n = item.childCount()
        if n > 0:
            state = item.checkState(0)
            for i in range(n):
                subitem = item.child(i)
                subitem.setCheckState(0, state)

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

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            if self._hasFeatureChecked():
                title = 'Texture features maps'
                wait = DialogWait(title=title, cancel=True, parent=self)
                wait.open()
                QApplication.processEvents()
                radiomics.setVerbosity(20)  # INFO
                SisypheProgressReporter.setDialogWait(wait)
                radiomics.progressReporter = SisypheProgressReporter
                extractor = featureextractor.RadiomicsFeatureExtractor()
                s = extractor.settings
                s['kernelRadius'] = self._radius.value()
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
                        QMessageBox.warning(self, title, '{}'.format(err))
                        continue
                    # Voxel batch used to avoid memory errors
                    s['voxelBatch'] = 16384  # 128 x 128 voxels
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
                                    m.setFilenamePrefix('{}_{}_'.format(l[-1][9:], subitem.text(0)))
                                    m.updateArrayID()
                                    m.save()
                                    wait.setInformationText('{}\nSave {} {} map'.format(basename(filename),
                                                                                        item.text(0),
                                                                                        subitem.text(0)))
                                except UserAbortException: break
                                except Exception as err:
                                    wait.hide()
                                    QMessageBox.warning(self, title, '{}'.format(err))
                                    continue
                wait.close()
                self._files.clearall()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    main = DialogTexture()
    main.show()
    app.exec_()
    exit()