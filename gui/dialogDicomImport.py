"""
    External packages/modules

        Name            Homepage link                                               Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os.path import join
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import splitext

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import GetArrayViewFromImage
from SimpleITK import GetImageFromArray

from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheDicom import DicomToXmlDicom
from Sisyphe.core.sisypheDicom import getIdentityFromDicom
from Sisyphe.core.sisypheDicom import getAcquisitionFromDicom
from Sisyphe.core.sisypheDicom import getDiffusionParametersFromDicom
from Sisyphe.core.sisypheDicom import mosaicImageToVolume
from Sisyphe.core.sisypheDicom import saveBVal
from Sisyphe.core.sisypheDicom import saveBVec
from Sisyphe.core.sisypheImageIO import writeToNIFTI
from Sisyphe.core.sisypheImageIO import writeToMINC
from Sisyphe.core.sisypheImageIO import writeToNRRD
from Sisyphe.core.sisypheImageIO import writeToVTK
from Sisyphe.core.sisypheImageIO import writeToNumpy
from Sisyphe.core.sisypheImageIO import readFromDicomFilenames
from Sisyphe.core.sisypheImageIO import convertImageToAxialOrientation
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.dicomWidgets import DicomFilesEnhancedTreeWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy
    
        QDialog -> DialogDicomImport
"""


class DialogDicomImport(QDialog):
    """
        DialogDicomImport

        Inheritance

            QDialog -> DialogDicomImport

        Private attributes

            _series     DicomFilesTreeViewWidget

        Public methods

            convert()           convert to Nifti, Minc, Nrrd, Vtk or Numpy

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init QMenu

        self._format = LabeledComboBox()
        self._format.setEditable(False)
        self._format.setFixedWidth(200)
        self._format.setToolTip('Import format.')
        self._format.setTitle('Format')
        self._format.addItem('PySisyphe')
        self._format.addItem('Minc')
        self._format.addItem('Nifti')
        self._format.addItem('Nrrd')
        self._format.addItem('Numpy')
        self._format.addItem('VTK')

        # Init widgets

        self._series = DicomFilesEnhancedTreeWidget()
        self._series.setModalityFilterToImages()

        self._origin = QCheckBox('Keep Dicom origin')
        self._origin.setCheckState(Qt.Checked)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Import directory')
        self._savedir.setToolTip('Directory where files are saved.')

        self._convert = QPushButton('Import')
        self._convert.setToolTip('Import checked DICOM files.')
        self._convert.clicked.connect(self.convert)

        self._layout.addWidget(self._series)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self._savedir)
        layout.addWidget(self._format)
        layout.addWidget(self._origin)
        layout.addWidget(self._convert)
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

        # Window

        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.50))

        self.setWindowTitle('DICOM import')
        self.setModal(True)

    # Public methods

    def convert(self):
        fmt = self._format.currentIndex()
        tree = self._series.getTreeWidget()
        wait = DialogWait(info='DICOM import...',
                          progress=True,
                          progressmin=0,
                          progressmax=self._series.getSelectedAcquisitionsCount(),
                          progresstxt=True,
                          cancel=True,
                          parent=self)
        wait.setCurrentProgressValue(0)
        wait.open()
        QApplication.processEvents()
        # Series
        nseries = tree.topLevelItemCount()
        for i in range(nseries):
            seriesitem = tree.topLevelItem(i)
            if seriesitem.checkState(0) == Qt.Checked:
                btag = False
                bval = dict()
                bvec = dict()
                series = seriesitem.text(0)
                wait.setInformationText('Import series {}'.format(seriesitem.text(2)))
                nacq = seriesitem.childCount()
                # Acquisitions
                for j in range(nacq):
                    acqitem = seriesitem.child(j)
                    if acqitem.checkState(0) == Qt.Checked:
                        if wait.getStopped():
                            tree.treeUpdate()
                            return
                        nfiles = acqitem.childCount()
                        filenames = list()
                        # Get DICOM filenames of the current acquisition
                        for k in range(nfiles):
                            fileitem = acqitem.child(k)
                            if fileitem.checkState(0) == Qt.Checked:
                                filename = fileitem.toolTip(0)
                                filenames.append(filename)
                        if len(filenames) > 0:
                            idt = getIdentityFromDicom(filenames[0])
                            acq = getAcquisitionFromDicom(filenames[0])
                            acq3D = acq.getType()
                            if acq3D == '2D' or acq3D in acq.getSequence(): acq3D = ''
                            acqdate = acq.getDateOfScan(True)
                            birthdate = idt.getDateOfBirthday(True)
                            save = [idt.getLastname(),
                                    idt.getFirstname(),
                                    birthdate.replace('/', '-'),
                                    acq.getModality(),
                                    acqdate.replace('/', '-'),
                                    acq3D+acq.getSequence()]
                            savename = '_'.join(save)
                            if nacq > 1:
                                f = f'_\x7b:0>{len(str(nacq))}d\x7d'
                                savename += f.format(j)
                            if fmt == 0: savename += SisypheVolume.getFileExt()
                            elif fmt == 1: savename += getMincExt()[0]   # Minc
                            elif fmt == 2: savename += getNiftiExt()[0]  # Nifti
                            elif fmt == 3: savename += getNrrdExt()[0]   # Nrrd
                            elif fmt == 4: savename += getNumpyExt()[0]  # Numpy
                            else: savename += getVtkExt()[0]  # VTK
                            if self._savedir.getPath() != '': savename = join(self._savedir.getPath(), savename)
                            else: savename = join(dirname(filenames[0]), savename)
                            # DICOM filenames conversion to SimpleITK image
                            try: img = readFromDicomFilenames(filenames)
                            except:
                                QMessageBox.warning(self,
                                                    'DICOM import',
                                                    'DICOM read error.')
                                continue
                            # Siemens mosaic conversion
                            if tree.isMosaic(series):
                                spacing = img.GetSpacing()
                                nimg = tree.getMosaic(series)
                                array = mosaicImageToVolume(GetArrayViewFromImage(img), nimg)
                                img = GetImageFromArray(array)
                                img.SetSpacing(spacing)
                            # Sisyphe (VTK) direction convention
                            img = flipImageToVTKDirectionConvention(img)
                            # Axial orientation conversion
                            img = convertImageToAxialOrientation(img)[0]
                            if not self._origin.isChecked():
                                img.SetOrigin((0.0, 0.0, 0.0))
                                img.SetDirection(getRegularDirections())
                            # Save
                            try:
                                if fmt == 0:  # SisypheVolume
                                    vol = SisypheVolume()
                                    vol.identity = idt
                                    vol.acquisition = acq
                                    vol.setSITKImage(img)
                                    vol.save(savename)
                                elif fmt == 1: writeToMINC(img, savename)   # Minc
                                elif fmt == 2: writeToNIFTI(img, savename)  # Nifti
                                elif fmt == 3: writeToNRRD(img, savename)   # Nrrd
                                elif fmt == 4: writeToNumpy(img, savename)  # Numpy
                                else: writeToVTK(img, savename)  # VTK
                            except:
                                QMessageBox.warning(self,
                                                    'DICOM import',
                                                    '{} write error.'.format(basename(savename)))
                                continue
                            # Save XmlDicom
                            xml = DicomToXmlDicom()
                            xml.setDicomSeriesFilenames(filenames)
                            xml.setXmlDicomFilename(basename(savename))
                            if self._savedir.getPath() != '': xml.setBackupXmlDicomDirectory(dirname(savename))
                            try: xml.execute()
                            except:
                                QMessageBox.warning(self,
                                                    'DICOM import',
                                                    '{} XML dicom conversion error.'.format(xml.getXmlDicomFilename()))
                                continue
                            if nacq > 1:
                                r = getDiffusionParametersFromDicom(filenames[0])
                                bval[savename] = r['bval']
                                bvec[savename] = r['bvec']
                                if r['bval'] != 0.0: btag = True
                        wait.incCurrentProgressValue()
                # Save diffusion bvalue and bvec
                if btag:
                    bname = list(bval.keys())[0]
                    bdirname = dirname(bname)
                    bsavename = splitext(basename(bname))[0]
                    buff = bsavename.split('_')
                    if buff[-1].isdigit(): buff = buff[:-1]
                    bsavename = '_'.join(buff) + '.bval'
                    bsavename = join(bdirname, bsavename)
                    saveBVal(bsavename, bval, format='txt')
                    bsavename = '_'.join(buff) + '.bvec'
                    bsavename = join(bdirname, bsavename)
                    saveBVec(bsavename, bvec, format='txt')
                    bsavename = '_'.join(buff) + '.xbval'
                    bsavename = join(bdirname, bsavename)
                    saveBVal(bsavename, bval, format='xml')
                    bsavename = '_'.join(buff) + '.xbvec'
                    bsavename = join(bdirname, bsavename)
                    saveBVec(bsavename, bvec, format='xml')
                del tree.getDict()[series]
        tree.treeUpdate()
        wait.close()

"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogDicomImport()
    main.open()
    app.exec_()
