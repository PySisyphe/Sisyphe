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
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QApplication

import radiomics
from radiomics import featureextractor

from Sisyphe.core.sisypheXml import XmlROI
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget

__all__ = ['SisypheProgressReporter',
           'DialogTexture',
           'DialogROITexture']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> ProgressReporter
    - QDialog -> DialogTexture -> DialogROITexture

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
    set the featureextractor voxelBatch parameter to a low value (2048 or less) to avoid access violation.

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
                          'JointEntropy',
                          'MaximumProbability',
                          'MCC',
                          'SumAverage',
                          'SumEntropy',
                          'SumSquares',
                          'SumVariance'),
                 'gldm': ('DependenceEntropy',
                          'DependenceNonUniformity',
                          'DependenceNonUniformityNormalized',
                          'DependencePercentage',
                          'DependenceVariance',
                          'GrayLevelNonUniformity',
                          'GrayLevelNonUniformityNormalized',
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
                           'LongRunHighGrayLevelEmphasis',
                           'LongRunLowGrayLevelEmphasis',
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
            elif k == 'shape': title = 'Shape features'
            else: raise ValueError('Invalid feature')
            item.setText(0, title)
            self._features.addTopLevelItem(item)
            for f in self._FEATURES[k]:
                subitem = QTreeWidgetItem(item)
                subitem.setCheckState(0, Qt.Unchecked)
                subitem.setText(0, f)
                item.addChild(subitem)
        self._layout.addWidget(self._features)

        self._check = QPushButton('Check all')
        self._check.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._check.clicked.connect(self._onCheckAll)
        self._check.setVisible(False)
        self._uncheck = QPushButton('Uncheck all')
        self._uncheck.setCheckable(False)
        # noinspection PyUnresolvedReferences
        self._uncheck.clicked.connect(self._onUncheckAll)

        lyout = QHBoxLayout()
        lyout.addWidget(self._check)
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

    def _onCheckAll(self):
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            # noinspection PyTypeChecker
            item.setCheckState(0, Qt.Checked)
            for j in range(item.childCount()):
                subitem = item.child(j)
                # noinspection PyTypeChecker
                subitem.setCheckState(0, Qt.Checked)

    def _onUncheckAll(self):
        for i in range(self._features.topLevelItemCount()):
            item = self._features.topLevelItem(i)
            # noinspection PyTypeChecker
            item.setCheckState(0, Qt.Unchecked)
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
        # < Revision 05/08/2025
        # self._files.add(filenames)
        for filename in filenames:
            self._files.add(filename)
        # Revision 05/08/2025 >
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
                                except UserAbortException:
                                    # < Revision 04/08/2025
                                    # break
                                    wait.close()
                                    self._files.clearall()
                                    return
                                    # Revision 04/08/2025 >
                                except Exception as err:
                                    wait.hide()
                                    messageBox(self, title=title, text='{}'.format(err))
                                    continue
                wait.close()
                self._files.clearall()


class DialogROITexture(DialogTexture):
    """
    DialogROITexture

    Description
    ~~~~~~~~~~~

    GUI dialog window for ROI-based texture analysis.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogTexture -> DialogROITexture

    Creation: 04/08/2025
    Revision: 03/11/2025
    """

    @classmethod
    def _updateWindowTitleBarColor(cls, window):
        if platform == 'win32':
            import qdarktheme
            p = qdarktheme.load_palette('auto')
            cl = p.base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            import pywinstyles
            pywinstyles.change_header_color(window, c)
            QApplication.processEvents()

    @classmethod
    def _formatLabel(cls, label):
        if isinstance(label, str):
            if label.isupper(): r = label
            else:
                r = ''
                for c in label:
                    if c.isupper() or c.isdigit(): r += '\n{}'.format(c)
                    else: r += c
                r = r.lstrip().title()
                r = r.replace('\n2\nD\n', '\n2D\n')
                r = r.replace('\n3\nD\n', '\n3D\n')
                r = r.replace('1\n0\n', '10\n')
                r = r.replace('9\n0\n', '90\n')
            return r
        else: raise TypeError('parameter type {} is not str.'.format(type(label)))

    # Special method

    def __init__(self, parent=None):

        # noinspection PyTypeChecker
        DialogTexture._FEATURES['shape'] = ('MeshVolume',
                                      'VoxelVolume',
                                      'SurfaceArea',
                                      'SurfaceVolumeRatio',
                                      'Sphericity',
                                      'Compactness1',
                                      'Compactness2',
                                      'SphericalDisproportion',
                                      'Maximum3DDiameter',
                                      'Maximum2DDiameterSlice',
                                      'Maximum2DDiameterColumn',
                                      'Maximum2DDiameterRow',
                                      'MajorAxisLength',
                                      'MinorAxisLength',
                                      'LeastAxisLength',
                                      'Elongation',
                                      'Flatness')
        super().__init__(parent)

        self.setWindowTitle('ROI texture features')

        self._files.setTextLabel('Volume(s)')
        self._settings.setParameterVisibility('VoxelBatch', False)

        self._rois = FilesSelectionWidget()
        self._rois.setTextLabel('Region-Of-Interest(s)')
        self._rois.filterSisypheROI()
        self._rois.FieldChanged.connect(self._validateROI)
        self._layout.insertWidget(1, self._rois)

        self._check.setVisible(True)

    # Private methods

    def _filesChanges(self):
        if self._files.filenamesCount() > 0: self._rois.setEnabled(True)
        else:
            self._rois.setEnabled(False)
            self._rois.clearall()

    def _validateROI(self):
        # < Revision 03/11/2025
        if self._files.filenamesCount() > 0 and self._rois.filenamesCount() > 0:
            # for roi in self._rois.getFilenames():
            for index, roi in enumerate(self._rois.getFilenames()):
                r = XmlROI(roi)
                fov1 = [round(v, 2) for v in r.getFOV()]
                flag = False
                for filename in self._files.getFilenames():
                    fov2 = [round(v, 2) for v in SisypheVolume.getVolumeAttribute(filename, 'fov')]
                    flag = flag or (fov1 == fov2)
                if not flag:
                    # index = self._rois.getIndexFromItem(roi)
                    self._rois.clearItem(index, False)
            self._execute.setEnabled(self._rois.filenamesCount() > 0)
        else: self._execute.setEnabled(False)
        # Revision 03/11/2025 >

    # Public methods

    def setROIs(self, rois: str | list[str]):
        if isinstance(rois, str): rois = [rois]
        for roi in rois:
            self._rois.add(roi)

    def getROIs(self):
        return self._rois.getFilenames()

    def execute(self):
        n = self._files.filenamesCount()
        nrois = self._rois.filenamesCount()
        if n > 0 and nrois > 0:
            if self._hasFeatureChecked():
                self.hide()
                title = 'ROI texture features'
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
                # Features to process
                features = dict()
                features['first'] = list()
                features['glcm'] = list()
                features['gldm'] = list()
                features['glrlm'] = list()
                features['glszm'] = list()
                features['ngtdm'] = list()
                features['shape'] = list()
                extractor.disableAllFeatures()
                for i in range(self._features.topLevelItemCount()):
                    item = self._features.topLevelItem(i)
                    for j in range(item.childCount()):
                        subitem = item.child(j)
                        if subitem.checkState(0) == Qt.Checked:
                            idx = self._features.indexOfTopLevelItem(item)
                            if idx == 0: features['first'].append(subitem.text(0))
                            elif idx == 1: features['glcm'].append(subitem.text(0))
                            elif idx == 2: features['gldm'].append(subitem.text(0))
                            elif idx == 3: features['glrlm'].append(subitem.text(0))
                            elif idx == 4: features['glszm'].append(subitem.text(0))
                            elif idx == 5: features['ngtdm'].append(subitem.text(0))
                            elif idx == 6: features['shape'].append(subitem.text(0))
                if len(features['first']) > 0: extractor.enableFeaturesByName(firstorder=features['first'])
                if len(features['glcm']) > 0: extractor.enableFeaturesByName(glcm=features['glcm'])
                if len(features['gldm']) > 0: extractor.enableFeaturesByName(gldm=features['gldm'])
                if len(features['glrlm']) > 0: extractor.enableFeaturesByName(glrlm=features['glrlm'])
                if len(features['glszm']) > 0: extractor.enableFeaturesByName(glszm=features['glszm'])
                if len(features['ngtdm']) > 0: extractor.enableFeaturesByName(ngtdm=features['ngtdm'])
                if len(features['shape']) > 0: extractor.enableFeaturesByName(shape=features['shape'])
                # Dialog of results initialization
                dialog = DialogGenericResults()
                if platform == 'win32': self._updateWindowTitleBarColor(dialog)
                dialog.setWindowTitle('ROI texture feature results')
                # Feature extraction
                results = dict()
                results['firstorder'] = dict()
                results['glcm'] = dict()
                results['gldm'] = dict()
                results['glrlm'] = dict()
                results['glszm'] = dict()
                results['ngtdm'] = dict()
                results['shape'] = dict()
                roicolors = list()
                for filename in self._files.getFilenames():
                    wait.setInformationText(basename(filename))
                    v = SisypheVolume()
                    try:
                        v.load(filename)
                        img = v.getSITKImage()
                    except Exception as err:
                        wait.hide()
                        messageBox(self, title=title, text='{}'.format(err))
                        continue
                    for roifilename in self._rois.getFilenames():
                        roi = SisypheROI()
                        try:
                            roi.load(roifilename)
                            if not v.hasSameFieldOfView(roi, 2): continue
                            mask = roi.getSITKImage()
                            roicolors.append(roi.getQColor())
                        except Exception as err:
                            wait.hide()
                            messageBox(self, title=title, text='{}'.format(err))
                            continue
                        try:
                            wait.setInformationText('{} ROI {}'.format(basename(filename),
                                                                       basename(roifilename)))
                            wait.setProgressVisibility(False)
                            r = extractor.execute(img, mask)
                            for k in r.keys():
                                kr, k1, k2 = k.split('_')
                                if kr == 'original':
                                    if k1 in results:
                                        if 'ROI' not in results[k1]: results[k1]['ROI'] = list()
                                        name = roi.getName()
                                        if name not in results[k1]['ROI']: results[k1]['ROI'].append(name)
                                        if k2 not in results[k1]: results[k1][k2] = list()
                                        results[k1][k2].append(float(r[k]))
                        except UserAbortException: break
                        except Exception as err:
                            wait.hide()
                            messageBox(self, title=title, text='{}'.format(err))
                            continue
                if len(results['firstorder']) > 0:
                    index = dialog.newTab('First Order\nFeatures', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['firstorder'])
                if len(results['glcm']) > 0:
                    index = dialog.newTab('Gray Level Co-occurrence\nMatrix Features', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['glcm'])
                if len(results['gldm']) > 0:
                    index = dialog.newTab('Gray Level Dependence\nMatrix Features', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['gldm'])
                if len(results['glrlm']) > 0:
                    index = dialog.newTab('Gray Level Run Length\nMatrix Features', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['glrlm'])
                if len(results['glszm']) > 0:
                    index = dialog.newTab('Gray Level Size Zone\nMatrix Features', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['glszm'])
                if len(results['ngtdm']) > 0:
                    index = dialog.newTab('Neighbouring\nGray Tone Difference\nMatrix Features', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['ngtdm'])
                if len(results['shape']) > 0:
                    index = dialog.newTab('Shape\nFeatures', capture=False, clipbrd=False)
                    dialog.setTreeWidgetDict(index, results['shape'])
                for i in range(dialog.getTabCount()):
                    w = dialog.getTreeWidget(i)
                    # noinspection PyTypeChecker
                    w.setSelectionBehavior(1)
                    w.setWordWrap(True)
                    # noinspection PyProtectedMember
                    dialog._tab.tabBar().setTabButton(i, 0, QLabel('\n\n'))
                    for j in range(w.headerItem().columnCount()):
                        txt = self._formatLabel(w.headerItem().text(j))
                        w.headerItem().setText(j, txt)
                    for j in range(w.topLevelItemCount()):
                        item = w.topLevelItem(j)
                        item.setForeground(0, roicolors[j])
                wait.close()
                screen = QApplication.primaryScreen().geometry()
                dialog.setMinimumWidth(int(screen.width() * 0.33))
                dialog.exec()
                self._files.clearall()
                self._rois.clearall()
                self.accept()
