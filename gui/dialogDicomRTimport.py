"""
    External packages/modules

        Name            Link                                                        Usage

        pydicom         https://pydicom.github.io/pydicom/stable/                   DICOM library
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext

from glob import glob

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from pydicom import read_file
from pydicom.misc import is_dicom

from SimpleITK import sitkLinear
from SimpleITK import Euler3DTransform
from SimpleITK import ResampleImageFilter

from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheDicom import DicomToXmlDicom
from Sisyphe.core.sisypheDicom import getDicomImageModalities
from Sisyphe.core.sisypheDicom import getIdentityFromDicom
from Sisyphe.core.sisypheDicom import getAcquisitionFromDicom
from Sisyphe.core.sisypheImageIO import readFromDicomSeries
from Sisyphe.core.sisypheImageIO import convertImageToAxialOrientation
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QDialog -> DialogRTimport
"""


class DialogRTimport(QDialog):
    """
        DialogRTimport

        Inheritance

            QDialog -> DialogRTimport

        Private attributes

            _size       list of int, matrix size of reference volume
            _spacing    list of float, voxel spacing of reference volume
            _origin     list of float, origin of reference volume
            _direction  list of float, direction of reference volume

        Public methods

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM RT import')
        self.resize(QSize(1000, 500))

        self._size = None
        self._spacing = None
        self._origin = None
        self._direction = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._series = QTreeWidget()
        self._series.setAlternatingRowColors(True)
        self._series.setSelectionMode(3)
        self._series.setSelectionBehavior(1)
        self._series.setHeaderLabel('Dicom RT series')
        self._series.itemChanged.connect(self._toggleCheckbox)

        self._filter = QComboBox()
        self._filter.addItem('*')
        for ext in getDicomExt():
            self._filter.addItem('*{}'.format(ext))

        self._dir = FileSelectionWidget()
        self._dir.filterDirectory()
        self._dir.setTextLabel('DICOM directory')
        self._dir.FieldChanged.connect(self._newdir)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Import directory')
        self._savedir.setContentsMargins(10, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel('Filter'))
        layout.addWidget(self._filter)
        layout.addWidget(self._dir)
        self._layout.addLayout(layout)
        self._layout.addWidget(self._series)

        self._check = QPushButton(QIcon(join(self._dir.getDefaultIconDirectory(), 'check.png')), 'Check')
        self._uncheck = QPushButton(QIcon(join(self._dir.getDefaultIconDirectory(), 'uncheck.png')), 'Uncheck')
        self._remove = QPushButton(QIcon(join(self._dir.getDefaultIconDirectory(), 'cross.png')), 'Remove')
        self._removeall = QPushButton(QIcon(join(self._dir.getDefaultIconDirectory(), 'delete.png')), 'Clear')
        self._convert = QPushButton(QIcon(join(self._dir.getDefaultIconDirectory(), 'import.png')), 'Convert')
        self._check.setFixedSize(QSize(100, 32))
        self._uncheck.setFixedSize(QSize(100, 32))
        self._remove.setFixedSize(QSize(100, 32))
        self._removeall.setFixedSize(QSize(100, 32))
        self._convert.setFixedSize(QSize(100, 32))
        self._check.setToolTip('Check selected DICOM files.')
        self._uncheck.setToolTip('Uncheck selected DICOM files.')
        self._remove.setToolTip('Remove selected series.')
        self._removeall.setToolTip('Remove all series.')
        self._convert.setToolTip('Import checked DICOM RT series.')
        self._check.clicked.connect(self._checkSelectedRows)
        self._uncheck.clicked.connect(self._uncheckSelectedRows)
        self._remove.clicked.connect(self._removeSelectedSeries)
        self._removeall.clicked.connect(self._series.clear)

        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.addWidget(self._check)
        layout.addWidget(self._uncheck)
        layout.addWidget(self._remove)
        layout.addWidget(self._removeall)
        layout.addWidget(self._convert)
        layout.addWidget(self._savedir)
        self._layout.addLayout(layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addStretch()

        self._layout.addLayout(layout)

        ok.clicked.connect(self.accept)

    # Private methods

    def _toggleCheckbox(self, item, c):
        if item.childCount() > 0:
            for i in range(item.childCount()):
                child1 = item.child(i)
                child1.setCheckState(0, item.checkState(0))
                if child1.childCount() > 0:
                    for j in range(child1.childCount()):
                        child2 = child1.child(j)
                        child2.setCheckState(0, item.checkState(0))

    def _checkSelectedRows(self):
        items = self._series.selectedItems()
        if items:
            for item in items:
                item.setCheckState(0, Qt.Checked)

    def _uncheckSelectedRows(self):
        items = self._series.selectedItems()
        if items:
            for item in items:
                item.setCheckState(0, Qt.Unchecked)

    def _removeSelectedSeries(self):
        root = self._series.invisibleRootItem()
        items = self._series.selectedItems()
        if items:
            for item in items:
                (item.parent() or root).removeChild(item)

    def _suffixDigitDataSort(self, filename):
        basename = splitext(filename)[0]
        r = basename.split('.')[-1]
        if r.isdigit(): return int(r)
        r = basename.split('-')[-1]
        if r.isdigit(): return int(r)
        r = basename.split('-')[-1]
        if r.isdigit(): return int(r)
        r = basename.split('#')[-1]
        if r.isdigit(): return int(r)
        return filename

    def _updateSeries(self, images):
        if isinstance(images, dict):
            if len(images) > 0:
                for keyref in images:
                    itemref = QTreeWidgetItem(self._series)
                    itemref.setText(0, 'Frame of Reference UID: {}'.format(keyref))
                    itemref.setData(0, Qt.UserRole, self._dir.getPath())
                    itemref.setFlags(itemref.flags() | Qt.ItemIsUserCheckable)
                    itemref.setCheckState(0, Qt.Checked)
                    self._series.addTopLevelItem(itemref)
                    for keyseries in images[keyref]:
                        itemseries = QTreeWidgetItem(itemref)
                        itemseries.setFlags(itemseries.flags() | Qt.ItemIsUserCheckable)
                        itemseries.setCheckState(0, Qt.Checked)
                        if keyseries == 'rtstruct':
                            itemseries.setText(0, 'RTStruct')
                            itemseries.setData(0, Qt.UserRole, 'RTStruct')
                        elif keyseries == 'rtdose':
                            itemseries.setText(0, 'RTDose')
                            itemseries.setData(0, Qt.UserRole, 'RTDose')
                        else:
                            itemseries.setText(0, 'Series UID: {}'.format(keyseries))
                            itemseries.setData(0, Qt.UserRole, 'Series')
                        itemref.addChild(itemseries)
                        for filename in images[keyref][keyseries]:
                            itemfile = QTreeWidgetItem(itemseries)
                            if keyseries in ('rtstruct', 'rtdose'):
                                itemfile.setFlags(itemfile.flags() | Qt.ItemIsUserCheckable)
                                itemfile.setCheckState(0, Qt.Checked)
                            itemfile.setText(0, basename(filename))
                            itemseries.addChild(itemfile)
                        # itemseries.sortChildren(0, Qt.AscendingOrder)
        else:
            raise TypeError('parameter type {} is not dict.'.format(type(images)))

    def _newdir(self):
        folder = self._dir.getPath()
        folder = join(folder, self._filter.currentText())
        filenames = glob(folder)
        images = dict()
        if filenames:
            n = len(filenames)
            if n > 0:
                # Set ProgressBar
                progress = DialogWait(parent=self)
                progress.setProgressRange(0, n)
                progress.setCurrentProgressValue(0)
                progress.buttonVisibilityOff()
                progress.progressTextVisibilityOn()
                progress.setProgressVisibility(n > 1)
                progress.setInformationText('Dicom RT series analysis...')
                progress.open()
                try:
                    for filename in filenames:
                        if is_dicom(filename):
                            progress.setInformationText(basename(filename))
                            ds = read_file(filename, stop_before_pixels=True)
                            modality = ds['Modality'].value
                            series = ds['SeriesInstanceUID'].value
                            if 'FrameOfReferenceUID' in ds: frameref = ds['FrameOfReferenceUID'].value
                            elif (0x3006, 0x0010) in ds:
                                if 'FrameOfReferenceUID' in ds[0x3006, 0x0010][0]:
                                    frameref = ds[0x3006, 0x0010][0]['FrameOfReferenceUID'].value
                            else: continue
                            QApplication.processEvents()
                            if modality == 'RTSTRUCT':
                                if frameref not in images: images[frameref] = dict()
                                if 'rtstruct' not in images[frameref]: images[frameref]['rtstruct'] = list()
                                images[frameref]['rtstruct'].append(filename)
                            elif modality == 'RTDOSE':
                                if frameref not in images: images[frameref] = dict()
                                if 'rtdose' not in images[frameref]: images[frameref]['rtdose'] = list()
                                images[frameref]['rtdose'].append(filename)
                            elif modality in getDicomImageModalities():
                                if frameref not in images: images[frameref] = dict()
                                if series not in images[frameref]: images[frameref][series] = list()
                                images[frameref][series].append(filename)
                            progress.incCurrentProgressValue()
                finally:
                    progress.hide()
        # Keep series with dicom reference volume + rtstruct and/or rtdose
        if len(images) > 0:
            for key in images:
                tag = 0
                if 'rtstruct' in images[key]: tag += 1
                if 'rtdose' in images[key]: tag += 1
                if tag == 0 or len(images[key]) == tag: del images[key]
                # sort filenames by numeric suffix if available
                for key2 in images[key]:
                    images[key][key2].sort(key=lambda v: self._suffixDigitDataSort(v))
        # Update QTreeWidget
        if len(images) > 0: self._updateSeries(images)
        self._dir.clear()

    def _convertRTStruct(self, filename, dcmfiles):
        if isinstance(filename, str):
            if exists(filename):
                pass
            else:
                raise FileNotFoundError('no such file {}.'.format(filename))
        else:
            raise TypeError('parameter type {} is not str'.format(type(filename)))

    def _convertRTDose(self, filename):
        if isinstance(filename, str):
            if exists(filename):
                # Dicom read
                try: img = readFromDicomSeries([filename])
                except: QMessageBox.warning(self, 'DICOM RT import', 'DICOM RTDose read error.')
                # Resample to reference volume space
                if img.GetDimension() == 4: img = img[:, :, :, 0]
                if self._size and self._spacing:
                    if self._size != img.GetSize() or self._spacing != img.GetSpacing():
                        img.SetOrigin((0, 0, 0))
                        r = ResampleImageFilter()
                        r.SetSize(self._size)
                        r.SetOutputSpacing(self._spacing)
                        r.SetOutputOrigin(self._origin)
                        r.SetOutputDirection(self._direction)
                        r.SetInterpolator(sitkLinear)
                        t = Euler3DTransform()
                        t.SetIdentity()
                        r.SetTransform(t)
                        img = r.Execute(img)
                else:
                    QMessageBox.warning(self, 'DICOM RT import', 'Reference FOV is not defined.')
                    return
                # Sisyphe conversion
                img = flipImageToVTKDirectionConvention(img)
                img = convertImageToAxialOrientation(img)[0]
                img.SetDirection(getRegularDirections())
                vol = SisypheVolume()
                # Attributes
                identity = getIdentityFromDicom(filename)
                acq = getAcquisitionFromDicom(filename)
                vol.setIdentity(identity)
                vol.setAcquisition(acq)
                vol.setSITKImage(img)
                vol.setOrigin()
                # Sisyphe write
                savename = '_'.join(identity.getLastname(),
                                    identity.getFirstname(),
                                    identity.getDateOfBirthday(),
                                    acq.getModality(),
                                    acq.getDateOfScan(),
                                    acq.getSequence()) + vol.getFileExt()
                if self._savedir.getPath() != '': savename = join(self._savedir.getPath(), savename)
                else: savename = join(dirname(filename), savename)
                try: vol.save(savename)
                except: QMessageBox.warning(self, 'DICOM RT import', 'SisypheVolume write error.')
            else:
                raise FileNotFoundError('no such file {}.'.format(filename))
        else:
            raise TypeError('parameter type {} is not str'.format(type(filename)))

    def _convertDicom(self, filenames):
        if isinstance(filenames, list):
            # Dicom read
            try: img = readFromDicomSeries(filenames)
            except: QMessageBox.warning(self, 'DICOM RT import', 'DICOM read error.')
            self._size = img.GetSize()
            self._spacing = img.GetSapcing()
            self._origin = img.GetOrigin()
            self._direction = img.GetDirection()
            # Sisyphe conversion
            img = flipImageToVTKDirectionConvention(img)
            img = convertImageToAxialOrientation(img)[0]
            img.SetDirection(getRegularDirections())
            vol = SisypheVolume()
            # Attributes
            identity = getIdentityFromDicom(filenames[0])
            acq = getAcquisitionFromDicom(filenames[0])
            vol.setIdentity(identity)
            vol.setAcquisition(acq)
            vol.setSITKImage(img)
            vol.setOrigin()
            # Sisyphe write
            savename = '_'.join(identity.getLastname(),
                                identity.getFirstname(),
                                identity.getDateOfBirthday(),
                                acq.getModality(),
                                acq.getDateOfScan(),
                                acq.getSequence()) + vol.getFileExt()
            if self._savedir.getPath() != '': savename = join(self._savedir.getPath(), savename)
            else: savename = join(dirname(filenames[0]), savename)
            try: vol.save(savename)
            except: QMessageBox.warning(self, 'DICOM RT import', 'SisypheVolume write error.')
            # Write XmlDicom
            xml = DicomToXmlDicom()
            xml.setDicomSeriesFilenames(filenames)
            if self._savedir.getPath() != '': xml.setBackupXmlDicomDirectory(dirname(savename))
            try: xml.execute()
            except: QMessageBox.warning(self, 'DICOM RT import', 'XML dicom conversion error.')
        else:
            raise TypeError('parameter type {} is not list'.format(type(filenames)))

    def _convert(self):
        n1 = self._series.topLevelItemCount()
        if n1 > 0:
            dcmfiles = list()
            rtdosefiles = list()
            rtsructfiles = list()
            for i in range(n1):
                item = self._series.topLevelItem(i)
                folder = item.data(0, Qt.UserRole)
                if exists(folder):
                    n2 = item.childCount()
                    if n2 > 0:
                        for j in range(n2):
                            child = item.child(j)
                            # convert RTStruct
                            if child.data(0, Qt.UserRole) == 'RTStruct':
                                n3 = child.childCount()
                                if n3 > 0:
                                    for k in range(n3):
                                        child2 = child.child(k)
                                        rtsructfiles.append(join(folder, child2.text(0)))
                            # convert RTDose
                            elif child.data(0, Qt.UserRole) == 'RTDose':
                                n3 = child.childCount()
                                if n3 > 0:
                                    for k in range(n3):
                                        child2 = child.child(k)
                                        rtdosefiles.append(join(folder, child2.text(0)))
                            # convert DICOM reference series
                            else:
                                n3 = child.childCount()
                                if n3 > 0:
                                    for k in range(n3):
                                        child2 = child.child(k)
                                        dcmfiles.append(join(folder, child2.text(0)))
            # Convert
            if len(dcmfiles) > 0:
                n = len(rtdosefiles) + len(rtsructfiles) + 1
                progress = DialogWait(parent=self)
                progress.setProgressRange(0, n)
                progress.setCurrentProgressValue(0)
                progress.buttonVisibilityOff()
                progress.progressTextVisibilityOn()
                progress.setProgressVisibility(n > 1)
                progress.setInformationText('Import Dicom reference volume...')
                progress.open()
                try:
                    self._convertDicom(dcmfiles)
                    progress.incCurrentProgressValue()
                    if len(rtdosefiles) > 0:
                        for rtdosefile in rtdosefiles:
                            progress.setInformationText('Import {} RTDose...'.format(basename(rtdosefile)))
                            self._convertRTDose(rtdosefile)
                            progress.incCurrentProgressValue()
                    if len(rtsructfiles) > 0:
                        for rtstructfile in rtsructfiles:
                            progress.setInformationText('Import {} RTStruct...'.format(basename(rtstructfile)))
                            self._convertRTStruct(rtstructfile, dcmfiles)
                            progress.incCurrentProgressValue()
                finally:
                    progress.hide()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogRTimport()
    main.show()
    app.exec_()
