"""
    External packages/modules

        Name            Link                                                        Usage

        pydicom         https://pydicom.github.io/pydicom/stable/                   DICOM library
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename

from csv import writer
from csv import QUOTE_NONNUMERIC

from pydicom import read_file
from pydicom.multival import MultiValue

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.dicomWidgets import DicomHeaderTreeViewWidget
from Sisyphe.widgets.dicomWidgets import DicomComboBoxWidget

"""
    Class hierarchy

       QDialog ->  DialogDicomDataset
"""


class DialogDicomDataset(QDialog):
    """
        DialogDicomDataset

        Inheritance

            QDialog -> DialogDicomDataset

        Private attributes

            _dataset    DicomHeaderTreeViewWidget
            _searchtag  DicomComboBoxWidget

        Public methods

            setDicomSeriesFilesVisibility(bool)
            bool = getDicomSeriesFilesVisibility()

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

        # Init save menu

        self._savemenu = QMenu()
        self._action = dict()
        self._action['dcm'] = QAction('Save DICOM file', self)
        self._action['csv'] = QAction('Save checked DataElements to CSV file', self)
        self._action['txt'] = QAction('Save checked DataElements to text file', self)
        self._action['dcm'].triggered.connect(self._saveDCM)
        self._action['csv'].triggered.connect(self._saveCSV)
        self._action['txt'].triggered.connect(self._saveTXT)
        self._savemenu.addAction(self._action['dcm'])
        self._savemenu.addAction(self._action['csv'])
        self._savemenu.addAction(self._action['txt'])

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.setSelectionModeToSingle()
        self._files.filterDICOM()
        self._files.FilesSelectionWidgetSelectionChanged.connect(self._initDataset)
        self._files.FilesSelectionWidgetCleared.connect(self._fileSelectionCleared)
        self._files.setTextLabel('Dicom series files')
        self._dataset = DicomHeaderTreeViewWidget()
        self._dataset.setPrivateTagVisibility(False)

        self._searchtag = DicomComboBoxWidget()
        self._searchtag.setPrivateTagVisibility(False)
        self._searchtag.setEditable(True)
        self._searchtag.setFixedWidth(200)
        self._searchtag.currentIndexChanged.connect(self._searchChanged)

        self._private = QCheckBox('Remove private DataElements')
        self._private.setCheckState(2)
        self._private.stateChanged.connect(self._privateTagChanged)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(QLabel('Search DataElement'))
        hlayout.addWidget(self._searchtag)
        hlayout.addStretch()
        hlayout.addWidget(self._private)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(hlayout)
        layout.addWidget(self._dataset)
        widget = QWidget()
        widget.setLayout(layout)

        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Vertical)
        self._splitter.addWidget(self._files)
        self._splitter.addWidget(widget)
        self._layout.addWidget(self._splitter)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 5)

        self._check = QPushButton(QIcon(join(self._files.getDefaultIconDirectory(), 'check.png')), '')
        self._uncheck = QPushButton(QIcon(join(self._files.getDefaultIconDirectory(), 'uncheck.png')), '')
        self._save = QPushButton(QIcon(join(self._files.getDefaultIconDirectory(), 'save.png')), '')
        self._save.setMenu(self._savemenu)
        self._save.setFixedWidth(60)
        self._check.setFixedSize(QSize(32, 32))
        self._uncheck.setFixedSize(QSize(32, 32))
        self._check.setToolTip('Check selected DICOM DataElements.')
        self._uncheck.setToolTip('Uncheck selected DICOM DataElements.')
        self._save.setToolTip('Save DataElements selection.')
        self._check.clicked.connect(self._dataset.checkSelectedRows)
        self._uncheck.clicked.connect(self._dataset.uncheckSelectedRows)

        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.addWidget(self._check)
        layout.addWidget(self._uncheck)
        layout.addWidget(self._save)
        layout.addStretch()
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
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        self.setWindowTitle('DICOM dataset')
        self.setModal(True)

    # Private methods

    def _initDataset(self, obj, filename):
        if obj == self._files:
            if exists(filename):
                if isDicom(filename):
                    self._dataset.setDicomFile(filename)
                    self._searchtag.setDicomDataset(self._dataset.getDicomDataset(), self._private.checkState() < 2)
                else:
                    raise IOError('{} is not a valid DICOM file.'.format(basename(filename)))
            else:
                raise IOError('{} no such file.'.format(basename(filename)))

    def _fileSelectionCleared(self, obj):
        if obj == self._files:
            self._dataset.model().clear()

    def _privateTagChanged(self):
        self._dataset.setPrivateTagVisibility(self._private.checkState() < 2)
        filename = self._files.getSelectedFilenames()
        if filename: self._initDataset(self._files, filename[0])

    def _searchChanged(self):
        self._dataset.scrollToDicomName(self._searchtag.getCurrentDicomName())

    def _checkedToDict(self):
        dcmnames = self._dataset.getCheckedDicomNames()
        if dcmnames and len(dcmnames) > 0:
            dedict = dict()
            filenames = self._files.getFilenames()
            for i in range(len(filenames)):
                ds = read_file(filenames[i], stop_before_pixels=True)
                for dcmname in dcmnames:
                    if i == 0: dedict[dcmname] = list()
                    if dcmname in ds.dir(): dedict[dcmname].append(ds[dcmname].value)
                    else: dedict[dcmname].append('')
            return dedict
        else: return None

    def _saveCSV(self):
        dedict = self._checkedToDict()
        if dedict:
            filename = QFileDialog.getSaveFileName(self, 'Save CSV file', getcwd(), 'CSV file (*.csv)')
            QApplication.processEvents()
            filename = filename[0]
            if filename:
                with open(filename, mode='tool') as csvfile:
                    try:
                        csvwriter = writer(csvfile, delimiter=',', quotechar='"', quoting=QUOTE_NONNUMERIC)
                        # First row
                        row = ['filename']
                        for de in dedict:
                            if isinstance(dedict[de][0], MultiValue):
                                for i in range(len(dedict[de][0])):
                                    row.append('{}{}'.format(de, i))
                            else: row.append(de)
                        csvwriter.writerow(row)
                        # Data rows
                        files = self._files.getFilenames()
                        i = 0
                        for file in files:
                            row = [basename(file)]
                            for de in dedict:
                                if isinstance(dedict[de][i], MultiValue):
                                    for j in range(len(dedict[de][i])):
                                        row.append(str(dedict[de][i][j]))
                                else: row.append(str(dedict[de][i]))
                            csvwriter.writerow(row)
                            i += 1
                    except: QMessageBox.warning(self, 'Save CSV file', 'CSV write error.')

    def _saveTXT(self):
        dedict = self._checkedToDict()
        if dedict:
            filename = QFileDialog.getSaveFileName(self, 'Save text file', getcwd(), 'Text file (*.txt)')
            QApplication.processEvents()
            filename = filename[0]
            if filename:
                with open(filename, mode='tool') as txtfile:
                    try:
                        # First row
                        row = ['filename']
                        for de in dedict:
                            if isinstance(dedict[de][0], MultiValue):
                                for i in range(len(dedict[de][0])):
                                    row.append('{}{}'.format(de, i))
                            else: row.append(de)
                        txtfile.write('\t'.join(row) + '\n')
                        # Data rows
                        files = self._files.getFilenames()
                        i = 0
                        for file in files:
                            row = [basename(file)]
                            for de in dedict:
                                if isinstance(dedict[de][i], MultiValue):
                                    for j in range(len(dedict[de][i])):
                                        row.append(str(dedict[de][i][j]))
                                else: row.append(str(dedict[de][i]))
                            txtfile.write('\t'.join(row) + '\n')
                            i += 1
                    except: QMessageBox.warning(self, 'Save txt file', 'txt write error.')

    def _saveDCM(self):
        # list of edited DataElements
        edited = self._dataset.getEditedDataElements()
        if edited and len(edited) > 0:
            dialog = QMessageBox()
            dialog.setText('Dicom Dataset')
            dialog.setInformativeText('Do you want to overwrite the dicom file ?')
            dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dialog.setIcon(QMessageBox.Question)
            r = dialog.exec()
            if len(edited) == 1:
                if r == QMessageBox.Yes:
                    try: self._dataset.getDicomDataset().save_as(self._dataset.getDicomDataset().filename)
                    except: QMessageBox.warning(self, 'Dicom Dataset', 'DICOM write error.')
                else:
                    filename = QFileDialog.getSaveFileName(self, 'Save DICOM file', getcwd(), 'Dicom file (*.dcm)')
                    filename = filename[0]
                    if filename:
                        # write DICOM
                        try: self._dataset.getDicomDataset().save_as(filename)
                        except: QMessageBox.warning(self, 'Dicom Dataset', 'DICOM write error.')
            else:
                filenames = self._files.getFilenames()
                # constant DataElement value in series files, to remove from save
                ds1 = read_file(filenames[0], stop_before_pixels=True)
                ds2 = read_file(filenames[1], stop_before_pixels=True)
                for de in edited:
                    if ds1[de] != ds2[de]:
                        QMessageBox.information(self, 'Dicom Dataset',
                                                '{} is not a constant DataElement, removed from save.'.format(de))
                        del de
                # write DICOM
                if r == QMessageBox.No:
                    base = QFileDialog.getSaveFileName(self, 'Save DICOM file', getcwd(), 'Dicom file (*.dcm)')
                    base = base[0]
                    if not base:
                        QMessageBox.information(self, 'Dicom Dataset', 'Save canceled.')
                        return
                if len(edited) > 0:
                    for filename in filenames:
                        ds = read_file(filename)
                        for de in edited:
                            ds[de] = self._dataset.getDicomDataset()[de]
                            if r == QMessageBox.No:
                                buff, ext = splitext(base)
                                suffix = '00000{}'.format(edited.index(de))[-5:]
                                savename = '{}{}{}'.format(buff, suffix, ext)
                                try: ds.save_as(savename)
                                except: QMessageBox.warning(self, 'Dicom Dataset', 'DICOM write error.')
                            else:
                                try: ds.save_as(filename)
                                except: QMessageBox.warning(self, 'Dicom Dataset', 'DICOM write error.')
                else:
                    QMessageBox.information(self, 'Dicom Dataset', 'Save canceled.')
        else:
            QMessageBox.information(self, 'Dicom Dataset', 'No DataElement has been edited.')

    def _savePreference(self):
        pass

    # Public methods

    def setDicomSeriesFilesVisibility(self, v):
        if isinstance(v, bool):
            self._files.setVisible(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getDicomSeriesFilesVisibility(self):
        return self._files.isVisible()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogDicomDataset()
    main.show()
    app.exec_()
