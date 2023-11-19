"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        pydicom         https://pydicom.github.io/pydicom/stable/                   DICOM library
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os import chdir

from os.path import dirname
from os.path import join
from os.path import exists
from os.path import split
from os.path import splitext
from os.path import abspath
from os.path import isfile
from os.path import sep
from os.path import basename

from glob import glob

from datetime import datetime

from numpy import int16
from numpy import int32
from numpy import uint16
from numpy import uint32
from numpy import iinfo

from pydicom.tag import Tag
from pydicom.tag import BaseTag
from pydicom.dicomio import read_file
from pydicom.dataset import DataElement
from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import QRegExp
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import QValidator
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.core.sisypheDicom import getDicomModalities
from Sisyphe.core.sisypheDicom import getDicomRTModalities
from Sisyphe.core.sisypheDicom import getDicomImageModalities
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.gui.dialogWait import DialogWait


"""
    Function
    
        dicomDateToStr    
"""


def dicomDateToStr(date, separator='/'):
    if date == '': return date
    else: return separator.join([date[:4], date[4:6], date[6:]])


"""
    Classes hierarchy
    
        QLineEdit -> DicomVRLineEdit
        QTreeView -> DicomHeaderTreeViewWidget
                  -> XmlDicomTreeViewWidget
        QComboBox -> DicomComboBoxWidget
        QTreeWidget -> DicomFilesTreeWidget
        QWidgets -> DicomFilesEnhancedTreeWidget
"""


class DateValidator(QValidator):

    # Special method

    def __init__(self, parent=None):
        super(DateValidator, self).__init__(parent)

    # Public method

    def validate(self, value, pos):
        try:
            datetime.strptime(value, '%Y%m%d').date()
            return 2, value, pos
        except ValueError:
            return 0, value, pos


class DateTimeValidator(QValidator):

    # Special method

    def __init__(self, parent=None):
        super(DateTimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value, pos):
        if DateValidator().validate(value[:8], 0)[0] == 2 and \
                TimeValidator().validate(value[6:], 0)[0] == 2:
            return 2, value, pos
        else:
            return 0, value, pos


class TimeValidator(QValidator):

    # Special method

    def __init__(self, parent=None):
        super(TimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value, pos):
        h = int(value[0:2])
        m = int(value[2:4])
        se = int(value[4:])
        if 0 <= h < 24 and 0 <= m < 60 and 0 <= se < 60:
            return 2, value, pos
        else:
            return 0, value, pos


class MultiIntValidator(QValidator):

    # Special method

    def __init__(self, nbmin, nbmax, n, parent=None):
        super(MultiIntValidator, self).__init__(parent)
        self._min = nbmin
        self._max = nbmax
        self._n = n

    # Public method

    def validate(self, value, pos):
        value = value.strip()
        valuelist = value.split(' ')
        r1 = len(valuelist) == self._n
        try:
            intlist = [int(i) for i in valuelist]
            r2 = True
            r3 = all([self._min <= i <= self._max for i in intlist])
        except ValueError:
            r2, r3 = False, False
        if r1 and r2 and r3:
            return 2, value, pos
        elif r1 or r2 or r3:
            return 1, value, pos
        else:
            return 0, value, pos


class MultiDoubleValidator(QValidator):

    # Special method

    def __init__(self, n, parent=None):
        super(MultiDoubleValidator, self).__init__(parent)
        self._n = n

    # Public method

    def validate(self, value, pos):
        value = value.strip()
        valuelist = value.split(' ')
        r1 = len(valuelist) == self._n
        try:
            # floatlist = [float(i) for i in valuelist]
            r2 = True
        except ValueError:
            r2 = False
        if r1 and r2:
            return 2, value, pos
        elif r1 or r2:
            return 1, value, pos
        else:
            return 0, value, pos


class LineEditDelegate(QStyledItemDelegate):

    # Special method

    def __init__(self, dataset=None, parent=None):
        super(LineEditDelegate, self).__init__(parent)
        self._dataset = dataset

    # Public methods

    def createEditor(self, parent, option, index):
        index0 = index.model().index(index.row(), 0)
        item0 = index.model().itemFromIndex(index0)
        de = self._dataset[item0.data()]
        return DicomVRLineEdit(de, parent)

    def setEditorData(self, editor, index):
        editor.setText(index.model().itemFromIndex(index).text())

    def setModelData(self, editor, model, index):
        index0 = model.index(index.row(), 0)
        item0 = model.itemFromIndex(index0)
        de = self._dataset[item0.data()]
        if de.VR in ['FL', 'FD']:
            if de.VM == 1:
                de.value = float(editor.text())
            else:
                v = editor.text().split(' ')
                de.value = [float(i) for i in v]
        elif de.VR in ['SL', 'SS', 'UL', 'US']:
            if de.VM == 1:
                de.value = int(editor.text())
            else:
                v = editor.text().split(' ')
                de.value = [int(i) for i in v]
        else:
            if de.VM == 1:
                de.value = editor.text()
            else:
                de.value = editor.text().split(' ')
        model.itemFromIndex(index).setText(editor.text())
        model.itemFromIndex(index).setData(1, 3)  # 0 not edited, 1 edited set in key.data()


class DicomVRLineEdit(QLineEdit):
    """
        DicomVRLineEdit
        QLineEdit to edit DICOM DataElement value

        Inheritance

            QLineEdit -> DicomVRLineEdit

        Private attributes

            _de     pydicom.DataElement

        Public methods

            inherited QLineEdit methods
    """

    # Special method

    def __init__(self, de=None, parent=None):
        super(DicomVRLineEdit, self).__init__(parent)
        if isinstance(de, DataElement):
            if de.VR in self._INITVR:
                self._de = de
                self._INITVR[self._de.VR](self)
            self.setText(str(de.value))
        else:
            self.setText('')
        self.setClearButtonEnabled(True)

    # Private methods

    def _initAE(self):
        self.setMaxLength(16)

    def _initAS(self):
        self.setMaxLength(4)
        self.setInputMask('>00DA')
        self.setValidator(QRegExpValidator(QRegExp('^[0-9]{1,3}[DWMY]$')))

    def _initCS(self):
        self.setMaxLength(16)

    def _initDA(self):
        self.setMaxLength(8)
        self.setInputMask('99999999')
        self.setValidator(DateValidator())

    def _initDS(self):
        if self._de.VM == 1:
            self.setMaxLength(16)
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initDT(self):
        self.setMaxLength(26)
        self.setInputMask('99999999999999')
        self.setValidator(DateTimeValidator())

    def _initFD(self):
        if self._de.VM == 1:
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initFL(self):
        if self._de.VM == 1:
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initIS(self):
        if self._de.VM == 1:
            self.setMaxLength(12)
            self.setValidator(QIntValidator(iinfo(int32).min, iinfo(int32).max))
        else:
            self.setValidator(MultiIntValidator(iinfo(int32).min, iinfo(int32).max, self._de.VM))

    def _initLO(self):
        self.setMaxLength(64)

    def _initLT(self):
        self.setMaxLength(10240)

    def _initPN(self):
        self.setMaxLength(64)
        self.setValidator(QRegExpValidator(QRegExp('[A-Za-z\-\s]+\^[A-Za-z\-\s]+')))

    def _initSH(self):
        self.setMaxLength(16)

    def _initSL(self):
        if self._de.VM == 1:
            self.setValidator(QIntValidator(iinfo(int32).min, iinfo(int32).max))
        else:
            self.setValidator(MultiIntValidator(iinfo(int32).min, iinfo(int32).max, self._de.VM))

    def _initSS(self):
        if self._de.VM == 1:
            self.setValidator(QIntValidator(iinfo(int16).min, iinfo(int16).max))
        else:
            self.setValidator(MultiIntValidator(iinfo(int16).min, iinfo(int16).max, self._de.VM))

    def _initST(self):
        self.setMaxLength(16)

    def _initTM(self):
        self.setMaxLength(6)
        self.setInputMask('999999')
        self.setValidator(TimeValidator())

    def _initUI(self):
        self.setMaxLength(64)
        self.setValidator(QRegExpValidator(QRegExp('^[0-9][0-9\.]+[0-9]$')))

    def _initUL(self):
        if self._de.VM == 1:
            self.setValidator(QIntValidator(0, iinfo(uint32).max))
        else:
            self.setValidator(MultiIntValidator(0, iinfo(uint32).max, self._de.VM))

    def _initUS(self):
        if self._de.VM == 1:
            self.setValidator(QIntValidator(0, iinfo(uint16).max))
        else:
            self.setValidator(MultiIntValidator(0, iinfo(uint16).max, self._de.VM))

    _INITVR = {'AE': _initAE,
               'AS': _initAS,
               'CS': _initCS,
               'DA': _initDA,
               'DS': _initDS,
               'DT': _initDT,
               'FD': _initFD,
               'FL': _initFL,
               'IS': _initIS,
               'LO': _initLO,
               'LT': _initLT,
               'PN': _initPN,
               'SH': _initSH,
               'SL': _initSL,
               'SS': _initSS,
               'ST': _initST,
               'TM': _initTM,
               'UI': _initUI,
               'UL': _initUL,
               'US': _initUS}


class DicomHeaderTreeViewWidget(QTreeView):
    """
        DicomHeaderTreeViewWidget class
        QTreeView to display tags and values of a DICOM file.

        Inheritance

            QTreeView -> DicomHeaderTreeViewWidget

        Private attributes

            _tag        bool, display tag column
            _name       bool, display tag name column
            _vr         bool, display VR column
            _vm         bool, display VM column
            _value      bool, display value column
            _private    bool, display private dicom fields
            _dataset    pydicom.dataset, dataset of the dicom file

        Public methods

            setDicomDataset(pydicom.dataset)
            setPrivateTagVisibility(bool)
            setTagCodeVisibility(bool)
            setTagNameVisibility(bool)
            setVRVisibility(bool)
            setVMVisibility(bool)
            setValueVisibility(bool)
            pydicom.dataset = getDataDicomDataset()
            list = getSelectedDicomDataElements()
            list = getSelectedDicomTags()
            list = getSelectedDicomNames()
            list = getSelectedDicomValues()
            list = getCheckedDicomNames()
            list = getEditedDataElements()
            scrollToDicomDataElement(pydicom.DataElement)
            scrollToDicomTag(pydicom.tag)
            scrollToDicomName(str)
            checkSelectedRows()
            uncheckSelectedRows()

            inherited QTreeView methods
    """

    _EDITFLAG = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
    _NOEDITFLAG = Qt.ItemIsEnabled | Qt.ItemIsSelectable
    _SELECTROWS = QItemSelectionModel.Select | QItemSelectionModel.Rows

    # Special method

    def __init__(self, dataset=None, private=True, tag=True, name=True, vr=True, vm=True, value=True, parent=None):
        super(DicomHeaderTreeViewWidget, self).__init__(parent)
        self._tag = tag
        self._name = name
        self._vr = vr
        self._vm = vm
        self._value = value
        self._private = private
        self._dataset = dataset

        # Init TreeView
        self.setSelectionMode(3)      # ExtendedSelection mode
        self.setSelectionBehavior(1)  # Select only rows
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setItemDelegate(LineEditDelegate(self._dataset, self))
        self.setAlternatingRowColors(True)
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        # Init Model
        self.setModel(QStandardItemModel())
        self._updateModel()

    # Private method

    def _datasetToModel(self, dataset, parent):
        for k in dataset:
            if k.tag != (0x7fe0, 0x0010):  # extract pixel data
                if k.VR == 'SQ':
                    item = QStandardItem(str(k.tag))
                    item.setData(k.tag, 3)
                    item.setFlags(self._NOEDITFLAG)
                    parent.appendRow([item, QStandardItem(k.name), QStandardItem(k.VR)])
                    for k2 in k.value:
                        self._datasetToModel(k2, item)
                else:
                    items = []
                    # items[0]
                    if self._tag:
                        item = QStandardItem(str(k.tag))
                        item.setFlags(self._NOEDITFLAG | Qt.ItemIsUserCheckable)
                        item.setCheckable(True)
                        item.setCheckState(Qt.Unchecked)
                        item.setData(k.tag)  # DICOM Tag set in key.data()
                        items.append(item)
                    # items[1]
                    if self._name:
                        item = QStandardItem(k.name)
                        item.setData(k.keyword, 3)  # DICOM keyword set in key.data()
                        item.setFlags(self._NOEDITFLAG)
                        items.append(item)
                    # items[2]
                    if self._vr:
                        item = QStandardItem(k.VR)
                        item.setFlags(self._NOEDITFLAG)
                        items.append(item)
                    # items[3]
                    if self._vm:
                        item = QStandardItem(str(k.VM))
                        item.setFlags(self._NOEDITFLAG)
                        items.append(item)
                    # items[4]
                    if self._value:
                        if k.VM == 1: buff = str(k.value)
                        elif k.VM == 0: buff = ''
                        else:
                            buff = [str(i) for i in k.value]
                            buff = ' '.join(buff)
                        item = QStandardItem(buff)
                        item.setData(0, 3)  # 0 not edited, 1 edited set in key.data()
                        item.setFlags(self._EDITFLAG)
                        items.append(item)
                    parent.appendRow(items)

    def _updateModel(self):
        if self._dataset is not None:
            if not self._private:
                self._dataset.remove_private_tags()

            # Init Header items
            hdr = []
            if self._tag: hdr.append('Tag')
            if self._name: hdr.append('Name')
            if self._vr: hdr.append('VR')
            if self._vm: hdr.append('VM')
            if self._value: hdr.append('Value')
            self.model().clear()
            self.model().setHorizontalHeaderLabels(hdr)

            # Init Model
            self._datasetToModel(self._dataset, self.model().invisibleRootItem())
            self.expandAll()

    def _setSectionVisibility(self, section=0, v=True):
        if v:
            self.header().showSection(section)
        else:
            self.header().hideSection(section)

    # Public methods

    def setDicomDataset(self, dataset):
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            self.model().clear()
            self._dataset = dataset
            self.setItemDelegate(LineEditDelegate(self._dataset, self))
            self._updateModel()
        else: raise TypeError('parameter type {} is not pydicom.FileDataset.'.format(dataset))

    def getDicomDataset(self):
        return self._dataset

    def setDicomFile(self, filename):
        if exists(filename):
            if isDicom(filename):
                dataset = read_file(filename)
                self.setDicomDataset(dataset)
            else: raise IOError('{} is not a valid DICOM file.'.format(basename(filename)))
        else: raise IOError('{} no such file.'.format(basename(filename)))

    def setPrivateTagVisibility(self, v):
        self._private = v
        self._updateModel()

    def setTagCodeVisibility(self, v):
        self._setSectionVisibility(0, v)

    def setTagNameVisibility(self, v):
        self._setSectionVisibility(1, v)

    def setVRVisibility(self, v):
        self._setSectionVisibility(2, v)

    def setVMVisibility(self, v):
        self._setSectionVisibility(3, v)

    def setValueVisibility(self, v):
        self._setSectionVisibility(4, v)

    def getSelectedDicomDataElements(self):
        # return list of selected dicom DataElement
        indexes = self.selectionModel().selectedRows(0)
        de = []
        if len(indexes) > 0:
            for index in indexes:
                item = self.model().itemFromIndex(index)
                if isinstance(item, QStandardItem):
                    de.append(self._dataset[item.data()])  # get DICOM Tag in key.data()
        return de

    def getSelectedDicomTags(self):
        # return list of selected dicom tags
        de = self.getSelectedDicomDataElements()
        taglist = []
        if len(de) > 0:
            for d in de:
                taglist.append(d.tag)
        return taglist

    def getSelectedDicomNames(self):
        # return list of selected dicom tags (names)
        de = self.getSelectedDicomDataElements()
        namelist = []
        if len(de) > 0:
            for d in de:
                namelist.append(d.name)
        return namelist

    def getSelectedDicomValues(self):
        # return list of selected dicom values
        de = self.getSelectedDicomDataElements()
        valuelist = []
        if len(de) > 0:
            for d in de:
                valuelist.append(str(d.value))
        return valuelist

    def getCheckedDicomNames(self):
        n = self.model().rowCount()
        if n > 0:
            r = list()
            for i in range(n):
                items = self.model().item(i)
                if items.checkState() == 2:
                    r.append(self.model().item(i, 1).data(3))
            return r
        else:
            return None

    def getEditedDataElements(self):
        n = self.model().rowCount()
        if n > 0:
            r = list()
            for i in range(n):
                if self.model().item(i, 4):
                    if self.model().item(i, 4).data(3) == 1:
                        r.append(self.model().item(i, 1).data(3))
            return r
        else:
            return None

    def scrollToDicomDataElement(self, de):
        if isinstance(de, DataElement):
            self.scrollToDicomTag(de.tag)

    def scrollToDicomTag(self, tag):
        if isinstance(tag, BaseTag):
            items = self.model().findItems(str(tag), Qt.MatchExactly, 0)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def scrollToDicomName(self, name):
        if isinstance(name, str):
            items = self.model().findItems(name, Qt.MatchExactly, 1)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def checkSelectedRows(self):
        indexlist = self.selectedIndexes()
        if len(indexlist) > 0:
            for index in indexlist:
                item = self.model().itemFromIndex(index)
                if item.isCheckable():
                    item.setCheckState(Qt.Checked)

    def uncheckSelectedRows(self):
        indexlist = self.selectedIndexes()
        if len(indexlist) > 0:
            for index in indexlist:
                item = self.model().itemFromIndex(index)
                if item.isCheckable():
                    item.setCheckState(Qt.Unchecked)


class DicomComboBoxWidget(QComboBox):
    """
        DicomComboBoxWidget class
        QComboBox tool to select DICOM tag of a DICOM file.

        Inheritance

            QComboBox -> DicomComboBoxWidget

        Private attributes

            _private    bool, display private dicom fields
            _dataset    pydicom.dataset, DICOM dataset

        Public methods

            setDicomDataset(pydicom.dataset, bool)
            pydicom.dataset = getDicomDataset()
            pydicom.DataElement = getCurrentDicomDataElement()
            pydicom.tag = getCurrentDicomTag()
            getCurrentDicomName()
            str or int or float or list = getCurrentDicomValue()
            str = getCurrentDicomVR()
            int = getCurrentDicomVM()

            inherited QComboBox methods
    """

    # Special method

    def __init__(self, dataset=None, private=True, parent=None):
        super(DicomComboBoxWidget, self).__init__(parent)
        self.setEditable(True)
        self._private = private
        self._dataset = dataset
        self._updateTagList()

    # Private method

    def _updateTagList(self):
        if self._dataset is not None:
            self.clear()
            if not self._private:
                self._dataset.remove_private_tags()
            for k in self._dataset:
                if k.tag != (0x7fe0, 0x0010) and k.VR != 'SQ':  # extract pixel data and sequence
                    self.addItem(k.name, k.tag)

    # Public methods

    def setDicomDataset(self, dataset, private=True):
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            self.clear()
            self._dataset = dataset
            self._private = private
            self._updateTagList()

    def getDicomDataset(self):
        return self.dataset

    def setPrivateTagVisibility(self, v):
        self._private = v
        self._updateTagList()

    def getCurrentDicomDataElement(self):
        c = self.currentData()
        if c:
            de = self._dataset[c]
            if isinstance(de, DataElement):
                return de
        return None

    def getCurrentDicomTag(self):
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.tag
        return None

    def getCurrentDicomName(self):
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.name
        return None

    def getCurrentDicomValue(self):
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.value
        return None

    def getCurrentDicomVR(self):
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VR
        return None

    def getCurrentDicomVM(self):
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VM
        return None


class DicomFilesTreeWidget(QTreeWidget):
    """
        DicomFilesTreeWidget class

        Description

            QTreeWidget to display DICOM files sorted by series.

        Inheritance

            QTreeWidget -> DicomFilesTreeWidget

        Private attributes

            _dict           dict, dict of dicom fields
                            (modality, series description, acquisition date, identity, birthdate)
            _path           str, directory to display in the TreeView
            _filter         str, filter for dicom file extension
            _modalityfilter str, dicom modality filter ('CT', 'MR', 'PT', 'NM' ...)

        Public methods

            dict = getDict()
            str = getModalityFilter()
            clearModalityFiler()
            setModalityFilterToImages()
            setModalityFilterToRT()
            setModalityFilterToAll()
            addCTtoModalityFilter()
            addMRtoModalityFilter()
            addPTtoModalityFilter()
            addNMtoModalityFilter()
            addOTtoModalityFilter()
            addRTStructToModalityFilter()
            addRTDoseToModalityFilter()
            setDefaultFilter(
            setFilter(str)
            str = getFilter()
            setPath(str)
            str = getPath()
            extractDataElements(BaseTag, str)
            checkAll()
            uncheckAll()
            checkSelected()
            uncheckSelected()

            inherited QTreeWidget methods
    """

    # Special method

    def __init__(self, path=None, filter='.*', parent=None):
        super().__init__(parent)
        self._dict = dict()
        self._path = list()
        self._filter = filter
        self._modalityfilter = getDicomModalities()

        # Init TreeWidget

        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # ExtendedSelection mode
        self.setSelectionBehavior(QTreeWidget.SelectRows)     # Selecting only rows
        self.setHeaderLabels(['Series UID ➤ Acquisition ➤ Files', 'Modality', 'Description',
                              'Acq. Date', 'Lastname', 'Firstname', 'Birth Date'])
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setAlternatingRowColors(True)
        self.itemChanged.connect(self._onToggleCheckbox)

        if path is not None:
            if exists(path):
                path = dirname(path)
                self.setPath(path)

    # Private methods

    def _onToggleCheckbox(self, item):
        if isinstance(item, QTreeWidgetItem):
            checkstate = item.checkState(0)
            if item.childCount() > 0:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, checkstate)
                    if item.childCount() > 0: self._onToggleCheckbox(item.child(i))

    def _pathToDict(self):
        if exists(self._path[-1]):
            if self._filter == '.*': flt = '**'
            else: flt = '*{}'.format(self._filter)
            filenames = glob(join(self._path[-1], flt), recursive=True)
            """
                0x0008, 0x0060 Modality
                0x0008, 0x0022 Acquisition date
                0x0008, 0x103e Series description
                0x0010, 0x0010 Patient's name
                0x0010, 0x0030 Patient's birth date
                0x0018, 0x1310 Acquisition matrix
                0x0019, 0x100a Number of images in mosaic
                0x0020, 0x000e Series instance UID
                0x0020, 0x0012 Acquisition number
                0x0020, 0x0013 Instance number
                0x0028, 0x0010 Rows
                0x0028, 0x0011 Columns
            """
            tags = [Tag(0x0008, 0x0060), Tag(0x0008, 0x0020), Tag(0x0008, 0x0021), Tag(0x0008, 0x0022),
                    Tag(0x0008, 0x103e), Tag(0x0010, 0x0010), Tag(0x0010, 0x0030), Tag(0x0018, 0x0120),
                    Tag(0x0018, 0x1310), Tag(0x0019, 0x100a), Tag(0x0020, 0x000e), Tag(0x0020, 0x000e),
                    Tag(0x0020, 0x0012), Tag(0x0020, 0x0013), Tag(0x0028, 0x0010), Tag(0x0028, 0x0011)]
            wait = DialogWait(info='',
                              progress=True,
                              progressmin=0,
                              progressmax=len(filenames),
                              progresstxt=True,
                              cancel=False,
                              parent=self)
            wait.setCurrentProgressValue(0)
            wait.open()
            wait.setInformationText('DICOM file analysis...')
            for filename in filenames:
                if not isfile(filename): continue
                if isDicom(filename):
                    try: ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                    except: continue
                    # Apply modality filter
                    if ds[0x0008, 0x0060].value in self._modalityfilter: series = str(ds[0x0020, 0x000e].value)
                    else: continue
                    # Acquisition number
                    if Tag(0x0020, 0x0012) in ds: acqn = int(ds[0x0020, 0x0012].value)
                    else: acqn = 1
                    # Instance number
                    if Tag(0x0020, 0x0013) in ds: instn = int(ds[0x0020, 0x0013].value)
                    else: instn = 1
                    # Siemens mosaic detection
                    mosaic = 1
                    if Tag(0x0019, 0x100a) in ds:
                        v = ds[0x0019, 0x100a].value
                        if isinstance(v, bytes): v = int.from_bytes(v, byteorder='little')
                        if v > 1: mosaic = ((v // 8) + 1) * 8
                    # Add values to dict
                    if series not in self._dict: self._dict[series] = dict()
                    # Modality
                    if Tag(0x0008, 0x0060) in ds: self._dict[series]['modality'] = ds[0x0008, 0x0060].value
                    else: self._dict[series]['modality'] = 'OT'
                    # Patient name
                    if Tag(0x0010, 0x0010) in ds: self._dict[series]['name'] = str(ds[0x0010, 0x0010].value)
                    else: self._dict[series]['name'] = ' ^ '
                    # Date of birth
                    if Tag(0x0010, 0x0030) in ds: self._dict[series]['birthdate'] = dicomDateToStr(ds[0x0010, 0x0030].value)
                    else: self._dict[series]['birthdate'] = ''
                    # Acquisition date
                    if Tag(0x0008, 0x0020) in ds: self._dict[series]['acqdate'] = dicomDateToStr(ds[0x0008, 0x0020].value)
                    elif Tag(0x0008, 0x0021) in ds: self._dict[series]['acqdate'] = dicomDateToStr(ds[0x0008, 0x0021].value)
                    elif Tag(0x0008, 0x0022) in ds: self._dict[series]['acqdate'] = dicomDateToStr(ds[0x0008, 0x0022].value)
                    else: self._dict[series]['acqdate'] = ''
                    # Series description
                    if Tag(0x0008, 0x103e) in ds: self._dict[series]['protocol'] = ds[0x0008, 0x103e].value
                    elif Tag(0x0008, 0x1030) in ds: self._dict[series]['protocol'] = ds[0x0008, 0x1030].value
                    else: self._dict[series]['protocol'] = ''
                    self._dict[series]['mosaic'] = mosaic
                    if 'acq' not in self._dict[series]: self._dict[series]['acq'] = dict()
                    if acqn not in self._dict[series]['acq']:
                        self._dict[series]['acq'][acqn] = dict()
                        self._dict[series]['acq'][acqn]['files'] = list()
                        self._dict[series]['acq'][acqn]['index'] = list()
                    self._dict[series]['acq'][acqn]['index'].append(instn)
                    self._dict[series]['acq'][acqn]['files'].append(filename)
                wait.incCurrentProgressValue()
            # Sort self._dict
            wait.progressVisibilityOff()
            wait.setInformationText('DICOM files sorting...')
            for series in self._dict:
                for acqn in self._dict[series]['acq']:
                    item = self._dict[series]['acq'][acqn]
                    if len(item['index']) > 1:
                        r = list(zip(item['index'], item['files']))
                        r.sort()
                        item['index'] = [i[0] for i in r]
                        item['files'] = [i[1] for i in r]
            wait.close()

    def _dictToWidget(self):
        self.clear()
        if len(self._dict) > 0:
            for series in self._dict:
                item = QTreeWidgetItem(self)
                item.setText(0, series)
                item.setText(1, self._dict[series]['modality'])
                item.setText(2, self._dict[series]['protocol'])
                item.setText(3, self._dict[series]['acqdate'])
                last, first = self._dict[series]['name'].split('^')
                item.setText(4, last)
                item.setText(5, first)
                item.setText(6, self._dict[series]['birthdate'])
                item.setCheckState(0, Qt.Checked)
                acq = list(self._dict[series]['acq'].keys())
                acq.sort()
                for j in range(len(acq)):
                    acqitem = QTreeWidgetItem(item)
                    n = len(self._dict[series]['acq'][acq[j]]['files'])
                    acqitem.setText(0, '{} ({} files)'.format(str(acq[j]), n))
                    acqitem.setCheckState(0, Qt.Checked)
                    item.addChild(acqitem)
                    for k in range(n):
                        institem = QTreeWidgetItem(acqitem)
                        filename = self._dict[series]['acq'][acq[j]]['files'][k]
                        institem.setText(0, basename(filename))
                        institem.setToolTip(0, filename)
                        institem.setCheckState(0, Qt.Checked)
                        acqitem.addChild(institem)
                self.addTopLevelItem(item)

    def _updateWidget(self):
        self._pathToDict()
        self._dictToWidget()

    # Public methods

    def treeUpdate(self):
        self._dictToWidget()

    def getDict(self):
        return self._dict

    def isMosaic(self, series):
        if series in self._dict:
            return self._dict[series]['mosaic'] != 1

    def getMosaic(self, series):
        if series in self._dict:
            return self._dict[series]['mosaic']

    def getSelectedSeriesCount(self):
        c = 0
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked: c += 1
        return c

    def getSelectedAcquisitionsCount(self):
        c = 0
        ns = self.topLevelItemCount()
        for i in range(ns):
            sitem = self.topLevelItem(i)
            na = sitem.childCount()
            for j in range(na):
                aitem = sitem.child(j)
                if aitem.checkState(0) == Qt.Checked: c += 1
        return c

    def getModalityFilter(self):
        return self._modalityfilter

    def clearModalityFiler(self):
        self._modalityfilter = list()

    def setModalityFilterToImages(self):
        self._modalityfilter = getDicomImageModalities()

    def setModalityFilterToRT(self):
        self._modalityfilter = getDicomRTModalities()

    def setModalityFilterToAll(self):
        self._modalityfilter = getDicomModalities()

    def addCTtoModalityFilter(self):
        if 'CT' not in self._modalityfilter:
            self._modalityfilter.append('CT')

    def addMRtoModalityFilter(self):
        if 'MR' not in self._modalityfilter:
            self._modalityfilter.append('MR')

    def addPTtoModalityFilter(self):
        if 'PT' not in self._modalityfilter:
            self._modalityfilter.append('PT')

    def addNMtoModalityFilter(self):
        if 'NM' not in self._modalityfilter:
            self._modalityfilter.append('NM')

    def addOTtoModalityFilter(self):
        if 'OT' not in self._modalityfilter:
            self._modalityfilter.append('OT')

    def addRTStructToModalityFilter(self):
        if 'RTSTRUCT' not in self._modalityfilter:
            self._modalityfilter.append('RTSTRUCT')

    def addRTDoseToModalityFilter(self):
        if 'RTDOSE' not in self._modalityfilter:
            self._modalityfilter.append('RTDOSE')

    def setDefaultFilter(self):
        self.setFilter('.*')

    def setFilter(self, v):
        if isinstance(v, str):
            flt = ['.*'] + getDicomExt()
            if v in flt:
                self._filter = v[v.find('.'):]
                path = self._path
                self._path = list()
                for i in range(len(path)):
                    if i == 0: self.setPath(path[i])
                    else: self.addPath(path[i])
            else: QMessageBox.warning(self,
                                      'Set DICOM file extension',
                                      '{} is not a DICOM file extension.'.format(v))
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def getFilter(self):
        return self._filter

    def setPath(self, path):
        if path not in self._path:
            self._path = [path]
            self.clear()
            self._dict = dict()
            self._updateWidget()

    def addPath(self, path):

        def isSubdir(path, subpath):
            d = glob(join(path, '**'), recursive=True)
            return subpath in d

        if path not in self._path:
            if len(self._path) > 0:
                for p in self._path:
                    if isSubdir(p, path): return
            self._path.append(path)
            self._updateWidget()

    def getPath(self):
        return self._path

    def hasPath(self):
        return len(self._path) > 0

    def extractDataElements(self, tag, series):
        r = dict()
        if isinstance(tag, BaseTag):
            if series in self._dict:
                for i in self._dict[series]['acq']:
                    r[i] = list()
                    previous = None
                    acq = self._dict[series]['acq'][i]
                    for j in range(len(acq['files'])):
                        ds = read_file(acq['files'][j], stop_before_pixels=True, specific_tags=[tag])
                        if tag in ds:
                            v = ds[tag].value
                            if previous != v: r[i].append(v)
                            previous = v
                    if len(r[i]) == 1: r[i] = r[i][0]
            # Sort

        return r

    def checkAll(self):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)
            self._onToggleCheckbox(item)

    def uncheckAll(self):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
            self._onToggleCheckbox(item)

    def checkSelected(self):
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                item.setCheckState(0, Qt.Checked)
                self._onToggleCheckbox(item)

    def uncheckSelected(self):
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                item.setCheckState(0, Qt.Unchecked)
                self._onToggleCheckbox(item)


class DicomFilesEnhancedTreeWidget(QWidget):
    """
        DicomFilesEnhancedTreeWidget class

        Description

            DicomFilesTreeWidget with buttons to check and uncheck items.

        Inheritance

            QWidget -> DicomFilesEnhancedTreeWidget

        Private attributes

            _tree       DicomFilesTreeWidget
            _ext        QComboBox
            _dir        MenuPushButton
            _checkall   QPushButton
            _uncheckall QPushButton
            _checksel   QPushButton
            _unchecksel QPushButton

        Public method

            newDirectory()
            addDirectory()
            QTreeWidget = getTreeWidget()
            setFilter(str)
            setSelectionButtonVisibility(bool)
            bool = getSelectionButtonVisibility()
            selectionButtonVisibilityOn()
            selectionButtonVisibilityOff()
            setDirectoryButtonVisibility(bool)
            bool = getDirectoryButtonVisibility()
            directoryButtonVisibilityOn()
            directoryButtonVisibilityOff()
            setFilterButtonVisibility(bool)
            bool = getFilterButtonVisibility()
            filterButtonVisibilityOn()
            filterButtonVisibilityOff()

            DicomFilesTreeWidget methods
    """

    # Special method

    def __init__(self, path=None, filter='.*', parent=None):
        super().__init__(parent)

        self._ext = QComboBox()
        self._ext.addItem('.*')
        self._ext.addItems(getDicomExt())
        self._ext.setCurrentIndex(0)
        self._ext.adjustSize()
        self._ext.setToolTip('Select DICOM file extension.')
        self._ext.currentTextChanged.connect(lambda: self._extensionChanged())

        self._dir = MenuPushButton('Directory')
        self._dir.adjustSize()
        self._dir.setToolTip('Select DICOM directory.')
        self._action = dict()
        self._action['new'] = self._dir.addAction('New...')
        self._action['add'] = self._dir.addAction('Add...')
        self._action['new'].triggered.connect(lambda: self.newDirectory())
        self._action['add'].triggered.connect(lambda: self.addDirectory())

        self._tree = DicomFilesTreeWidget(path, filter, parent=self)

        self._checkall = QPushButton('Check all')
        self._uncheckall = QPushButton('Uncheck all')
        self._checksel = QPushButton('Check selected')
        self._unchecksel = QPushButton('Uncheck selected')
        self._checkall.adjustSize()
        self._uncheckall.adjustSize()
        self._checksel.adjustSize()
        self._unchecksel.adjustSize()
        self._checkall.clicked.connect(lambda: self._tree.checkAll())
        self._uncheckall.clicked.connect(lambda: self._tree.uncheckAll())
        self._checksel.clicked.connect(lambda: self._tree.checkSelected())
        self._unchecksel.clicked.connect(lambda: self._tree.uncheckSelected())

        self._pathlayout = QHBoxLayout()
        self._pathlayout.addWidget(self._ext)
        self._pathlayout.addWidget(self._dir)
        self._pathlayout.addStretch()

        self._checklyout = QHBoxLayout()
        self._checklyout.addWidget(self._checkall)
        self._checklyout.addWidget(self._uncheckall)
        self._checklyout.addWidget(self._checksel)
        self._checklyout.addWidget(self._unchecksel)
        self._checklyout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addLayout(self._pathlayout)
        layout.addWidget(self._tree)
        layout.addLayout(self._checklyout)
        self.setLayout(layout)

    def __getattr__(self, name: str):
        """
            When attribute does not exist in the class,
            try calling self._tree DicomFilesTreeWidget method
        """
        methods = ['treeUpdate',
                   'getDict',
                   'isMosaic',
                   'getMosaic',
                   'getSelectedSeriesCount',
                   'getSelectedAcquisitionsCount',
                   'getModalityFilter',
                   'clearModalityFiler',
                   'setModalityFilterToImages',
                   'setModalityFilterToRT',
                   'setModalityFilterToAll',
                   'addCTtoModalityFilter',
                   'addMRtoModalityFilter',
                   'addPTtoModalityFilter',
                   'addNMtoModalityFilter',
                   'addRTStructToModalityFilter',
                   'addRTDoseToModalityFilter',
                   'setDefaultFilter',
                   'getFilter',
                   'setPath',
                   'addPath',
                   'hasPath',
                   'checkAll',
                   'uncheckAll',
                   'checkSelected',
                   'uncheckSelected']
        if name in methods:
            def func(*args): return self._tree.__getattribute__(name)(*args)
            return func
        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Private methods

    def _extensionChanged(self):
        ext = self._ext.currentText()
        self._tree.setFilter(ext)

    # Public methods

    def newDirectory(self):
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            self._tree.setPath(path)

    def addDirectory(self):
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            self._tree.addPath(path)

    def getTreeWidget(self):
        return self._tree

    def setFilter(self, filter):
        flt = ['.*'] + getDicomExt()
        if filter in flt: self._ext.setCurrentText(filter)

    def setSelectionButtonVisibility(self, v):
        self._checkall.setVisible(v)
        self._uncheckall.setVisible(v)
        self._checksel.setVisible(v)
        self._unchecksel.setVisible(v)

    def getSelectionButtonVisibility(self):
        return self._checkall.isVisible()

    def selectionButtonVisibilityOn(self):
        self.setSelectionButtonVisibility(True)

    def selectionButtonVisibilityOff(self):
        self.setSelectionButtonVisibility(False)

    def setDirectoryButtonVisibility(self, v):
        self._dir.setVisible(v)

    def getDirectoryButtonVisibility(self):
        return self._dir.isVisible()

    def directoryButtonVisibilityOn(self):
        self.setDirectoryButtonVisibility(True)

    def directoryButtonVisibilityOff(self):
        self.setDirectoryButtonVisibility(False)

    def setFilterButtonVisibility(self, v):
        self._ext.setVisible(v)

    def getFilterButtonVisibility(self):
        return self._ext.isVisible()

    def filterButtonVisibilityOn(self):
        self.setFilterButtonVisibility(True)

    def filterButtonVisibilityOff(self):
        self.setFilterButtonVisibility(False)


class XmlDicomTreeViewWidget(QTreeWidget):
    """
        XmlDicomTreeViewWidget class

        Description

            QTreeView to display XmlDicom data elements.

        Inheritance

            QTreeView -> XmlDicomTreeViewWidget

        Private attributes

            _dcm    XmlDicom

        Public methods

            bool = isEmpty()
            XmlDicom = getXmlDicom()
            loadXmlDicom(filename=str)
            checkAll()
            uncheckAll()
            saveCheckedDataElementsToXml(filename=str)
            saveCheckedDataElementsToTxt
            saveCheckedDataElementsToCSV
            saveCheckedDataElementsToMatfile
            saveCheckedDataElementsToExcel
            saveCheckedDataElementsToLATEX
            copyCheckedDataElementsToClipboard

            inherited QTreeView methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dcm = XmlDicom()

        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # ExtendedSelection mode
        self.setSelectionBehavior(QTreeWidget.SelectRows)     # Selecting only rows
        self.setAlternatingRowColors(True)
        self.setDragEnabled(False)
        self.setHeaderLabels(['Tag', 'Name', 'VR', 'VM', 'Value'])
        self.header().setDefaultAlignment(Qt.AlignCenter)

    # Public methods

    def isEmpty(self):
        return self._dcm.isEmpty()

    def getXmlDicom(self):
        return self._dcm

    def loadXmlDicom(self, filename):
        if exists(filename):
            self._dcm.loadXmlDicomFilename(filename)
            keys = self._dcm.getKeywords()
            for k in keys:
                data = self._dcm.getDataElement(k)
                if not isinstance(data, list):
                    item = QTreeWidgetItem([str(data.tag), data.keyword, data.VR, str(data.VM), str(data.value)])
                    item.setCheckState(0, Qt.Unchecked)
                    self.addTopLevelItem(item)
                else:
                    if len(data) > 0:
                        root = QTreeWidgetItem([str(data[0].tag), data[0].keyword])
                        root.setCheckState(0, Qt.Unchecked)
                        self.addTopLevelItem(root)
                        for d in data:
                            item = QTreeWidgetItem([str(d.tag), d.keyword, d.VR, str(d.VM), str(d.value)])
                            root.addChild(item)
            for i in range(4):
                self.resizeColumnToContents(i)

    def checkAll(self):
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def uncheckAll(self):
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)

    def checkSelected(self):
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                item.setCheckState(0, Qt.Checked)

    def uncheckSelected(self):
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                item.setCheckState(0, Qt.Unchecked)

    def saveCheckedDataElementsToXml(self, filename=''):
        n = self.topLevelItemCount()
        keys = self._dcm.getKeywords()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(keys[i])
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save PySisyphe Sheet', getcwd(),
                                                       filter='PySisyphe Sheet (*.xsheet)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToXml(skeys, filename)

    def saveCheckedDataElementsToTxt(self, filename=''):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save Text file', getcwd(),
                                                       filter='Text file (*.txt)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToTxt(skeys, filename)

    def saveCheckedDataElementsToCSV(self, filename=''):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save CSV file', getcwd(),
                                                       filter='CSV file (*.csv)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToCSV(skeys, filename)

    def saveCheckedDataElementsToMatfile(self, filename=''):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save Matfile', getcwd(),
                                                       filter='Matfile (*.mat)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToMatfile(skeys, filename)

    def saveCheckedDataElementsToExcel(self, filename=''):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save Excel file', getcwd(),
                                                       filter='Excel file (*.xlsx)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToExcel(skeys, filename)

    def saveCheckedDataElementsToLATEX(self, filename=''):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            if filename == '':
                filename = QFileDialog.getSaveFileName(self, 'Save Latex file', getcwd(),
                                                       filter='Latex file (*.tex)')[0]
                QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                self._dcm.saveDataElementValuesToLATEX(skeys, filename)

    def copyCheckedDataElementsToClipboard(self):
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            self._dcm.copyDataElementValuesToClipboard(skeys)


if __name__ == '__main__':
    """
        Tests
    """

    from sys import argv
    from PyQt5.QtWidgets import QVBoxLayout

    app = QApplication(argv)
    w = DicomFilesEnhancedTreeWidget()
    # w.setPath('/Users/jean-albert/PycharmProjects/python310Project/TESTS/DTI/DTI/DICOM')
    main = QWidget()
    layout = QVBoxLayout(main)
    layout.addWidget(w)
    main.show()
    app.exec_()
