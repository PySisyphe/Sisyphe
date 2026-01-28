"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - pydicom, DICOM library, https://pydicom.github.io/pydicom/stable/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any

from os import getcwd
from os import chdir

from os.path import dirname
from os.path import join
from os.path import exists
from os.path import isfile
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
# < Revision 07/03/2025
# from pydicom.dicomio import read_file
# Revision 07/03/2025 >
from pydicom import dcmread as read_file
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
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.core.sisypheDicom import getDicomModalities
from Sisyphe.core.sisypheDicom import getDicomRTModalities
from Sisyphe.core.sisypheDicom import getDicomImageModalities
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from PyQt5.QtCore import QObject
    from PyQt5.QtCore import QModelIndex
    from PyQt5.QtCore import QAbstractItemModel
    from PyQt5.QtWidgets import QStyleOptionViewItem

"""
Function
~~~~~~~~
    
    - dicomDateToStr 

Classes hierarchy
~~~~~~~~~~~~~~~~~
    
    - QLineEdit -> DicomVRLineEdit
    - QTreeView -> DicomHeaderTreeViewWidget
                -> XmlDicomTreeViewWidget
    - QComboBox -> DicomComboBoxWidget
    - QTreeWidget -> DicomFilesTreeWidget
    - QWidgets -> DicomFilesEnhancedTreeWidget
"""


def dicomDateToStr(date: str, separator: str = '/') -> str:
    if date == '': return date
    else: return separator.join([date[:4], date[4:6], date[6:]])


class DateValidator(QValidator):

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        super(DateValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        try:
            datetime.strptime(value, '%Y%m%d').date()
            return 2, value, pos
        except ValueError:
            return 0, value, pos


class DateTimeValidator(QValidator):

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        super(DateTimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        if DateValidator().validate(value[:8], 0)[0] == 2 and \
                TimeValidator().validate(value[6:], 0)[0] == 2:
            return 2, value, pos
        else:
            return 0, value, pos


class TimeValidator(QValidator):

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        super(TimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        h = int(value[0:2])
        m = int(value[2:4])
        se = int(value[4:])
        if 0 <= h < 24 and 0 <= m < 60 and 0 <= se < 60:
            return 2, value, pos
        else:
            return 0, value, pos


class MultiIntValidator(QValidator):

    # Special method

    def __init__(self,
                 nbmin: int,
                 nbmax: int,
                 n: int,
                 parent: QObject | None = None) -> None:
        super(MultiIntValidator, self).__init__(parent)
        self._min = nbmin
        self._max = nbmax
        self._n = n

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
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

    def __init__(self,
                 n: int,
                 parent: QObject | None = None) -> None:
        super(MultiDoubleValidator, self).__init__(parent)
        self._n = n

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
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

    def __init__(self,
                 dataset: Dataset | None = None,
                 parent: QObject | None = None) -> None:
        super(LineEditDelegate, self).__init__(parent)
        self._dataset = dataset

    # Public methods

    def createEditor(self, parent: QWidget | None, option:  QStyleOptionViewItem | None, index: QModelIndex) -> QLineEdit:
        index0 = index.model().index(index.row(), 0)
        # noinspection PyUnresolvedReferences
        item0 = index.model().itemFromIndex(index0)
        de = self._dataset[item0.data()]
        return DicomVRLineEdit(de, parent)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        # noinspection PyUnresolvedReferences
        editor.setText(index.model().itemFromIndex(index).text())

    def setModelData(self, editor: QWidget, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        index0 = model.index(index.row(), 0)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        model.itemFromIndex(index).setText(editor.text())
        # noinspection PyUnresolvedReferences
        model.itemFromIndex(index).setData(1, 3)  # 0 not edited, 1 edited set in key.data()


class DicomVRLineEdit(QLineEdit):
    """
    DicomVRLineEdit

    Description
    ~~~~~~~~~~~

    QLineEdit to edit DICOM DataElement value.

    Inheritance
    ~~~~~~~~~~~

    QLineEdit -> DicomVRLineEdit

    Last revision: 25/01/2026
    """

    # Special method

    """
    Private attributes

    _de     pydicom.DataElement
    """

    def __init__(self,
                 de: DataElement | None = None,
                 parent: QWidget | None = None) -> None:
        super(DicomVRLineEdit, self).__init__(parent)
        if isinstance(de, DataElement):
            if de.VR in self._INITVR:
                self._de = de
                # noinspection PyArgumentList
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
        # < Revision 25/01/2026
        # self.setValidator(QRegExpValidator(QRegExp('[A-Za-z\-\s]+\^[A-Za-z\-\s]+')))
        self.setValidator(QRegExpValidator(QRegExp(r'[A-Za-z\-\s]+\^[A-Za-z\-\s]+')))
        # Revision 25/01/2026 >

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
        # < Revision 25/01/2026
        # self.setValidator(QRegExpValidator(QRegExp('^[0-9][0-9\.]+[0-9]$')))
        self.setValidator(QRegExpValidator(QRegExp(r'^[0-9][0-9\.]+[0-9]$')))
        # Revision 25/01/2026 >

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

    Description
    ~~~~~~~~~~~

    QTreeView to display tags and values of a DICOM file.

    Inheritance
    ~~~~~~~~~~~

    QTreeView -> DicomHeaderTreeViewWidget

    Last revision: 20/10/2025
    """

    # noinspection PyUnresolvedReferences
    _EDITFLAG = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
    # noinspection PyUnresolvedReferences
    _NOEDITFLAG = Qt.ItemIsEnabled | Qt.ItemIsSelectable
    # noinspection PyUnresolvedReferences
    _SELECTROWS = QItemSelectionModel.Select | QItemSelectionModel.Rows

    # Special method

    """
    Private attributes

    _tag        bool, display tag column
    _name       bool, display tag name column
    _vr         bool, display VR column
    _vm         bool, display VM column
    _value      bool, display value column
    _private    bool, display private dicom fields
    _dataset    pydicom.dataset, dataset of the dicom file
    """

    def __init__(self,
                 dataset: Dataset | None = None,
                 private: bool = True,
                 tag: bool = True,
                 name: bool = True,
                 vr: bool = True,
                 vm: bool = True,
                 value: bool = True,
                 parent: QWidget | None = None) -> None:
        super(DicomHeaderTreeViewWidget, self).__init__(parent)
        self._tag = tag
        self._name = name
        self._vr = vr
        self._vm = vm
        self._value = value
        self._private = private
        self._dataset = dataset

        # Init TreeView
        # noinspection PyTypeChecker
        self.setSelectionMode(3)      # ExtendedSelection mode
        # noinspection PyTypeChecker
        self.setSelectionBehavior(1)  # Select only rows
        # noinspection PyTypeChecker
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setItemDelegate(LineEditDelegate(self._dataset, self))
        self.setAlternatingRowColors(True)
        # < Revision 26/06/2025
        # font = self.font()
        # font.setPointSize(12)
        # self.setFont(font)
        # Revision 26/06/2025 >

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
                        # noinspection PyUnresolvedReferences
                        item.setFlags(self._NOEDITFLAG | Qt.ItemIsUserCheckable)
                        item.setCheckable(True)
                        # noinspection PyUnresolvedReferences
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
            # noinspection PyUnresolvedReferences
            self.model().clear()
            # noinspection PyUnresolvedReferences
            self.model().setHorizontalHeaderLabels(hdr)

            # Init Model
            # noinspection PyUnresolvedReferences
            self._datasetToModel(self._dataset, self.model().invisibleRootItem())
            self.expandAll()

    def _setSectionVisibility(self, section=0, v=True):
        if v:
            self.header().showSection(section)
        else:
            self.header().hideSection(section)

    # Public methods

    def setDicomDataset(self, dataset: Dataset) -> None:
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            # noinspection PyUnresolvedReferences
            self.model().clear()
            self._dataset = dataset
            self.setItemDelegate(LineEditDelegate(self._dataset, self))
            self._updateModel()
        else: raise TypeError('parameter type {} is not pydicom.FileDataset.'.format(dataset))

    def getDicomDataset(self) -> Dataset:
        return self._dataset

    def setDicomFile(self, filename: str) -> None:
        if exists(filename):
            if isDicom(filename):
                dataset = read_file(filename)
                self.setDicomDataset(dataset)
            else: raise IOError('{} is not a valid DICOM file.'.format(basename(filename)))
        else: raise IOError('{} no such file.'.format(basename(filename)))

    def setPrivateTagVisibility(self, v: bool) -> None:
        self._private = v
        self._updateModel()

    def setTagCodeVisibility(self, v: bool) -> None:
        self._setSectionVisibility(0, v)

    def setTagNameVisibility(self, v: bool) -> None:
        self._setSectionVisibility(1, v)

    def setVRVisibility(self, v: bool) -> None:
        self._setSectionVisibility(2, v)

    def setVMVisibility(self, v: bool) -> None:
        self._setSectionVisibility(3, v)

    def setValueVisibility(self, v: bool) -> None:
        self._setSectionVisibility(4, v)

    def getSelectedDicomDataElements(self):
        # return list of selected dicom DataElement
        indexes = self.selectionModel().selectedRows(0)
        de = []
        if len(indexes) > 0:
            for index in indexes:
                # noinspection PyUnresolvedReferences
                item = self.model().itemFromIndex(index)
                if isinstance(item, QStandardItem):
                    de.append(self._dataset[item.data()])  # get DICOM Tag in key.data()
        return de

    def getSelectedDicomTags(self) -> list[int | str | tuple[int, int] | BaseTag]:
        # return list of selected dicom tags
        de = self.getSelectedDicomDataElements()
        taglist = []
        if len(de) > 0:
            for d in de:
                taglist.append(d.tag)
        return taglist

    def getSelectedDicomNames(self) -> list[str]:
        # return list of selected dicom tags (names)
        de = self.getSelectedDicomDataElements()
        namelist = []
        if len(de) > 0:
            for d in de:
                namelist.append(d.name)
        return namelist

    def getSelectedDicomValues(self) -> list[str]:
        # return list of selected dicom values
        de = self.getSelectedDicomDataElements()
        valuelist = []
        if len(de) > 0:
            for d in de:
                valuelist.append(str(d.value))
        return valuelist

    def getCheckedDicomNames(self) -> list[str] | None:
        n = self.model().rowCount()
        if n > 0:
            r = list()
            for i in range(n):
                # noinspection PyUnresolvedReferences
                items = self.model().item(i)
                if items.checkState() == 2:
                    # noinspection PyUnresolvedReferences
                    r.append(self.model().item(i, 1).data(3))
            return r
        else:
            return None

    def getEditedDataElements(self) -> list[str] | None:
        n = self.model().rowCount()
        if n > 0:
            r = list()
            for i in range(n):
                # noinspection PyUnresolvedReferences
                if self.model().item(i, 4):
                    # noinspection PyUnresolvedReferences
                    if self.model().item(i, 4).data(3) == 1:
                        # noinspection PyUnresolvedReferences
                        r.append(self.model().item(i, 1).data(3))
            return r
        else: return None

    def scrollToDicomDataElement(self, de: DataElement) -> None:
        if isinstance(de, DataElement):
            self.scrollToDicomTag(de.tag)

    def scrollToDicomTag(self, tag: int | str | tuple[int, int] | BaseTag) -> None:
        if isinstance(tag, BaseTag):
            # noinspection PyUnresolvedReferences
            items = self.model().findItems(str(tag), Qt.MatchExactly, 0)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                # noinspection PyTypeChecker
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def scrollToDicomName(self, name: str) -> None:
        if isinstance(name, str):
            # noinspection PyUnresolvedReferences
            items = self.model().findItems(name, Qt.MatchExactly, 1)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                # noinspection PyTypeChecker
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def checkSelectedRows(self) -> None:
        indexlist = self.selectedIndexes()
        if len(indexlist) > 0:
            for index in indexlist:
                # noinspection PyUnresolvedReferences
                item = self.model().itemFromIndex(index)
                if item.isCheckable():
                    # noinspection PyUnresolvedReferences
                    item.setCheckState(Qt.Checked)

    def uncheckSelectedRows(self) -> None:
        indexlist = self.selectedIndexes()
        if len(indexlist) > 0:
            for index in indexlist:
                # noinspection PyUnresolvedReferences
                item = self.model().itemFromIndex(index)
                if item.isCheckable():
                    # noinspection PyUnresolvedReferences
                    item.setCheckState(Qt.Unchecked)


class DicomComboBoxWidget(QComboBox):
    """
    DicomComboBoxWidget class

    Description
    ~~~~~~~~~~~

    QComboBox tool to select DICOM tag of a DICOM file.

    Inheritance
    ~~~~~~~~~~~

    QComboBox -> DicomComboBoxWidget

    Last revision: 20/10/2025
    """

    # Special method

    """
    Private attributes

    _private    bool, display private dicom fields
    _dataset    pydicom.dataset, DICOM dataset
    """

    def __init__(self,
                 dataset: Dataset | None = None,
                 private: bool = True,
                 parent: QWidget | None = None) -> None:
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

    def setDicomDataset(self, dataset: Dataset, private: bool = True) -> None:
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            self.clear()
            self._dataset = dataset
            self._private = private
            self._updateTagList()

    def getDicomDataset(self) -> Dataset:
        return self.dataset

    def setPrivateTagVisibility(self, v: bool) -> None:
        self._private = v
        self._updateTagList()

    def getCurrentDicomDataElement(self) -> DataElement | None:
        c = self.currentData()
        if c:
            de = self._dataset[c]
            if isinstance(de, DataElement):
                return de
        return None

    def getCurrentDicomTag(self) -> int | str | tuple[int, int] | BaseTag | None:
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.tag
        return None

    def getCurrentDicomName(self) -> str | None:
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.name
        return None

    def getCurrentDicomValue(self) -> Any | None:
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.value
        return None

    def getCurrentDicomVR(self) -> str | None:
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VR
        return None

    def getCurrentDicomVM(self) -> int | None:
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VM
        return None


class DicomFilesTreeWidget(QTreeWidget):
    """
    DicomFilesTreeWidget class

    Description
    ~~~~~~~~~~~

    QTreeWidget to display DICOM files sorted by series.

    Inheritance
    ~~~~~~~~~~~

    QTreeWidget -> DicomFilesTreeWidget

    Last revision: 26/01/2026
    """

    # Special method

    """
    Private attributes

    _dict           dict, dict of dicom fields (modality, series description, acquisition date, identity, birthdate)
                    dict[str Series instance UID: dict2]
                    dict2={'modality': str, 
                           'name': str, 
                           'birthdate': str, 
                           'acqdate': str, 
                           'protocol': str, 
                           'mosaic': int,
                           'acq': dict3}
                    dict3[tuple(int: acqn, int: instn | tempn): dict4]
                    dict4={'index': list[int] instn,
                           'files': list[str] filename,
                           'loc': dict[float loc: int count of files at this loc]}
    _path           str, directory to display in the TreeView
    _filter         str, filter for dicom file extension
    _modalityfilter str, dicom modality filter ('CT', 'MR', 'PT', 'NM' ...)
    """

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 path: str | None = None,
                 filter: str = '.*',
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dict = dict()
        self._path = list()
        self._filter = filter
        self._modalityfilter = getDicomModalities()

        # Init TreeWidget

        # noinspection PyTypeChecker
        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # ExtendedSelection mode
        # noinspection PyTypeChecker
        self.setSelectionBehavior(QTreeWidget.SelectRows)     # Selecting only rows
        self.setHeaderLabels(['Series UID ➤ Acquisition ➤ Files', 'Modality', 'Description',
                              'Acq. Date', 'Lastname', 'Firstname', 'Birth Date'])
        # noinspection PyTypeChecker
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setAlternatingRowColors(True)
        # noinspection PyUnresolvedReferences
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
            # < Revision 26/01/2026
            """
            0x0008, 0x0020 Study date
            0x0008, 0x0021 Series date
            0x0008, 0x0022 Acquisition date
            0x0008, 0x0060 Modality
            0x0008, 0x1030 Study description
            0x0008, 0x103e Series description
            0x0010, 0x0010 Patient's name
            0x0010, 0x0030 Patient's birth date
            0x0019, 0x100a Number of images in mosaic
            0x0020, 0x0012 Acquisition number
            0x0020, 0x0013 Instance number
            0x0020, 0x000e Series instance UID
            0x0020, 0x0100 Temporal position identifier
            0x0020, 0x1041 Slice location
            """
            tags = [Tag(0x0008, 0x0020), Tag(0x0008, 0x0021), Tag(0x0008, 0x0022),
                    Tag(0x0008, 0x0060), Tag(0x0008, 0x1030), Tag(0x0008, 0x103e),
                    Tag(0x0010, 0x0010), Tag(0x0010, 0x0030), Tag(0x0019, 0x100a),
                    Tag(0x0020, 0x0012), Tag(0x0020, 0x0013), Tag(0x0020, 0x000e),
                    Tag(0x0020, 0x0100), Tag(0x0020, 0x1041)]
            # Revision 26/01/2026 >
            wait = DialogWait(info='',
                              progress=True,
                              progressmin=0,
                              progressmax=len(filenames),
                              progresstxt=True,
                              cancel=False)
            wait.open()
            wait.setCurrentProgressValue(0)
            wait.setInformationText('DICOM file analysis...')
            for filename in filenames:
                if not isfile(filename): continue
                if isDicom(filename):
                    try: ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                    except: continue
                    # Apply modality filter
                    # < Revision 20/06/2025
                    if Tag(0x0008, 0x0060) in ds:
                        if ds[0x0008, 0x0060].value in self._modalityfilter: series = str(ds[0x0020, 0x000e].value)
                        else: continue
                    else: continue
                    # Revision 20/06/2025 >
                    # Acquisition number
                    if Tag(0x0020, 0x0012) in ds:
                        try: acqn = int(ds[0x0020, 0x0012].value)
                        except: acqn = 1
                    else: acqn = 1
                    # Instance number
                    if Tag(0x0020, 0x0013) in ds:
                        try: instn = int(ds[0x0020, 0x0013].value)
                        except: instn = 1
                    else: instn = 1
                    # Slice location
                    if Tag(0x0020, 0x1041) in ds:
                        try: loc = round(float(ds[0x0020, 0x1041].value), 2)
                        except: loc = None
                    else: loc = None
                    # < Revision 20/09/2024
                    # Temporal position identifier
                    if Tag(0x0020, 0x0100) in ds:
                        tempn = int(ds[0x0020, 0x0100].value)
                        acqn = (acqn, tempn)
                    # < Revision 20/06/2025
                    # bug fix, acqn type must be tuple
                    if isinstance(acqn, int): acqn = (acqn, 1)
                    # Revision 20/06/2025 >
                    # Revision 20/09/2024 >
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
                        self._dict[series]['acq'][acqn]['loc'] = list()
                    self._dict[series]['acq'][acqn]['index'].append(instn)
                    self._dict[series]['acq'][acqn]['files'].append(filename)
                    # < Revision 26/01/2026
                    if loc is None: loc = instn
                    self._dict[series]['acq'][acqn]['loc'].append(loc)
                    # Revision 26/01/2026 >
                wait.incCurrentProgressValue()
            # Sort self._dict
            wait.setCurrentProgressValue(len(filenames))
            wait.progressVisibilityOff()
            wait.setInformationText('DICOM files sorting...')
            for series in list(self._dict.keys()):
                if len(self._dict[series]['acq']) == 0:
                    self._dict.pop(series)
                    continue
                for acqn in list(self._dict[series]['acq'].keys()):
                    item = self._dict[series]['acq'][acqn]
                    if len(item['index']) == 0:
                        self._dict[series]['acq'].pop(acqn)
                    elif len(item['index']) == 1:
                        if item['loc'][0] is None:
                            self._dict[series]['acq'].pop(acqn)
                    elif len(item['index']) > 1:
                        r = list(zip(item['index'], item['files'], item['loc']))
                        r.sort()
                        item['index'] = [i[0] for i in r]
                        item['files'] = [i[1] for i in r]
                        item['loc'] = [i[2] for i in r]
                        # < Revision 01/07/2025
                        # Subseries extraction
                        if item['loc'][0] is not None:
                            r = len(item['loc']) / len(set(item['loc']))
                            # Duplicate slice location in acquisition number if r > 1
                            if r > 1.0:
                                # try to extract subseries
                                if r.is_integer():
                                    wait.setInformationText('Extracting {} subseries...'.format(acqn))
                                    r = dict()
                                    for i, loc in enumerate(item['loc']):
                                        if loc not in r: r[loc] = list()
                                        r[loc].append(item['files'][i])
                                    if len(r) > 0:
                                        n = None
                                        for loc in r:
                                            if n is None: n = len(r[loc])
                                            if n != len(r[loc]): n = None
                                        if n is not None:
                                            for loc in r:
                                                for i in range(n):
                                                    k = (1000 + acqn[0], i + 1)
                                                    if k not in self._dict[series]['acq']:
                                                        self._dict[series]['acq'][k] = dict()
                                                        self._dict[series]['acq'][k]['files'] = list()
                                                    self._dict[series]['acq'][k]['files'].append(r[loc][i])
                                self._dict[series]['acq'].pop(acqn)
                        else:
                            # loc is None, not an image -> remove
                            self._dict[series]['acq'].pop(acqn)
                        # Revision 01/07/2025 >
                if len(self._dict[series]['acq']) == 0:
                    self._dict.pop(series)
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
                # < Revision 20/09/2024
                # last, first = self._dict[series]['name'].split('^')
                last = ''
                first = ''
                try: v = self._dict[series]['name'].split('^')
                except: v = None
                if isinstance(v, list):
                    n = len(v)
                    if n == 1: last = v[0]
                    elif n > 1:
                        last = v[0]
                        first = v[1]
                # Revision 20/09/2024 >
                item.setText(4, last)
                item.setText(5, first)
                item.setText(6, self._dict[series]['birthdate'])
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Checked)
                acq = list(self._dict[series]['acq'].keys())
                if len(acq) > 0:
                    # < Revision 20/06/2025
                    if isinstance(acq[0], int): acq.sort()
                    elif isinstance(acq[0], tuple): acq.sort(key=lambda vi: vi[1])
                    # Revision 20/06/2025 >
                    for j in range(len(acq)):
                        acqitem = QTreeWidgetItem(item)
                        n = len(self._dict[series]['acq'][acq[j]]['files'])
                        acqitem.setText(0, '{} ({} files)'.format(str(acq[j]), n))
                        # noinspection PyUnresolvedReferences
                        acqitem.setCheckState(0, Qt.Checked)
                        item.addChild(acqitem)
                        for k in range(n):
                            institem = QTreeWidgetItem(acqitem)
                            filename = self._dict[series]['acq'][acq[j]]['files'][k]
                            institem.setText(0, basename(filename))
                            institem.setToolTip(0, filename)
                            # noinspection PyUnresolvedReferences
                            institem.setCheckState(0, Qt.Checked)
                            acqitem.addChild(institem)
                    self.addTopLevelItem(item)

    def _updateWidget(self):
        try:
            self._pathToDict()
            self._dictToWidget()
        except:
            # < Revision 26/01/2026
            for w in QApplication.topLevelWindows():
                if w.objectName() == 'DialogWaitWindow':
                    w.close()
            # Revision 26/01/2026 >
            messageBox(self,
                       'DICOM file parsing...',
                       text='DICOM file parsing error.')

    # Public methods

    def treeUpdate(self) -> None:
        self._dictToWidget()

    def getDict(self) -> dict:
        return self._dict

    def isMosaic(self, series: str) -> bool | None:
        # noinspection PyInconsistentReturns
        if series in self._dict:
            return self._dict[series]['mosaic'] != 1

    def getMosaic(self, series: str) -> int | None:
        # noinspection PyInconsistentReturns
        if series in self._dict:
            return self._dict[series]['mosaic']

    def getSelectedSeriesCount(self) -> int:
        c = 0
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            if item.checkState(0) == Qt.Checked: c += 1
        return c

    def getSelectedAcquisitionsCount(self) -> int:
        c = 0
        ns = self.topLevelItemCount()
        for i in range(ns):
            sitem = self.topLevelItem(i)
            na = sitem.childCount()
            for j in range(na):
                aitem = sitem.child(j)
                # noinspection PyUnresolvedReferences
                if aitem.checkState(0) == Qt.Checked: c += 1
        return c

    def getModalityFilter(self) -> list[str]:
        return self._modalityfilter

    def clearModalityFiler(self) -> None:
        self._modalityfilter = list()

    def setModalityFilterToImages(self) -> None:
        self._modalityfilter = getDicomImageModalities()

    def setModalityFilterToRT(self) -> None:
        self._modalityfilter = getDicomRTModalities()

    def setModalityFilterToAll(self) -> None:
        self._modalityfilter = getDicomModalities()

    def addCTtoModalityFilter(self) -> None:
        if 'CT' not in self._modalityfilter:
            self._modalityfilter.append('CT')

    def addMRtoModalityFilter(self) -> None:
        if 'MR' not in self._modalityfilter:
            self._modalityfilter.append('MR')

    def addPTtoModalityFilter(self) -> None:
        if 'PT' not in self._modalityfilter:
            self._modalityfilter.append('PT')

    def addNMtoModalityFilter(self) -> None:
        if 'NM' not in self._modalityfilter:
            self._modalityfilter.append('NM')

    def addOTtoModalityFilter(self) -> None:
        if 'OT' not in self._modalityfilter:
            self._modalityfilter.append('OT')

    def addRTStructToModalityFilter(self) -> None:
        if 'RTSTRUCT' not in self._modalityfilter:
            self._modalityfilter.append('RTSTRUCT')

    def addRTDoseToModalityFilter(self) -> None:
        if 'RTDOSE' not in self._modalityfilter:
            self._modalityfilter.append('RTDOSE')

    def setDefaultFilter(self) -> None:
        self.setFilter('.*')

    def setFilter(self, v: str) -> None:
        if isinstance(v, str):
            flt = ['.*'] + getDicomExt()
            if v in flt:
                self._filter = v[v.find('.'):]
                path = self._path
                self._path = list()
                for i in range(len(path)):
                    if i == 0: self.setPath(path[i])
                    else: self.addPath(path[i])
            else: messageBox(self,
                             'Set DICOM file extension',
                             text='{} is not a DICOM file extension.'.format(v))
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def getFilter(self) -> str:
        return self._filter

    def setPath(self, path: str) -> None:
        if path not in self._path:
            self._path = [path]
            self.clear()
            self._dict = dict()
            self._updateWidget()

    def addPath(self, path: str) -> None:

        def isSubdir(rpath, subpath):
            d = glob(join(rpath, '**'), recursive=True)
            return subpath in d

        if path not in self._path:
            if len(self._path) > 0:
                for p in self._path:
                    if isSubdir(p, path): return
            self._path.append(path)
            self._updateWidget()

    def getPath(self) -> list[str]:
        return self._path

    def hasPath(self) -> bool:
        return len(self._path) > 0

    def extractDataElements(self, tag: int | str | tuple[int, int] | BaseTag, series: str) -> dict:
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
        return r

    def checkAll(self) -> None:
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Checked)
            self._onToggleCheckbox(item)

    def uncheckAll(self) -> None:
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Unchecked)
            self._onToggleCheckbox(item)

    def checkSelected(self) -> None:
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Checked)
                self._onToggleCheckbox(item)

    def uncheckSelected(self) -> None:
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Unchecked)
                self._onToggleCheckbox(item)


class DicomFilesEnhancedTreeWidget(QWidget):
    """
    DicomFilesEnhancedTreeWidget class

    Description
    ~~~~~~~~~~~

    DicomFilesTreeWidget with buttons to check and uncheck items.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> DicomFilesEnhancedTreeWidget

    Last revision: 20/10/2025
    """

    # Special method

    """
    Private attributes

    _tree       DicomFilesTreeWidget
    _ext        QComboBox
    _dir        MenuPushButton
    _checkall   QPushButton
    _uncheckall QPushButton
    _checksel   QPushButton
    _unchecksel QPushButton
    """

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 path: str | None = None,
                 filter: str = '.*',
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._ext = QComboBox()
        self._ext.addItem('.*')
        self._ext.addItems(getDicomExt())
        self._ext.setCurrentIndex(0)
        self._ext.adjustSize()
        self._ext.setToolTip('Select DICOM file extension.')
        # noinspection PyUnresolvedReferences
        self._ext.currentTextChanged.connect(lambda: self._extensionChanged())

        self._dir = MenuPushButton('Directory')
        self._dir.adjustSize()
        self._dir.setToolTip('Select DICOM directory.')
        self._action = dict()
        self._action['new'] = self._dir.addAction('New...')
        self._action['addBundle'] = self._dir.addAction('Add...')
        # noinspection PyUnresolvedReferences
        self._action['new'].triggered.connect(lambda: self.newDirectory())
        # noinspection PyUnresolvedReferences
        self._action['addBundle'].triggered.connect(lambda: self.addDirectory())

        self._tree = DicomFilesTreeWidget(path, filter, parent=self)

        self._checkall = QPushButton('Check all')
        self._uncheckall = QPushButton('Uncheck all')
        self._checksel = QPushButton('Check selected')
        self._unchecksel = QPushButton('Uncheck selected')
        self._removeall = QPushButton('Clear')
        self._checkall.adjustSize()
        self._uncheckall.adjustSize()
        self._checksel.adjustSize()
        self._unchecksel.adjustSize()
        # noinspection PyUnresolvedReferences
        self._checkall.clicked.connect(lambda: self._tree.checkAll())
        # noinspection PyUnresolvedReferences
        self._uncheckall.clicked.connect(lambda: self._tree.uncheckAll())
        # noinspection PyUnresolvedReferences
        self._checksel.clicked.connect(lambda: self._tree.checkSelected())
        # noinspection PyUnresolvedReferences
        self._unchecksel.clicked.connect(lambda: self._tree.uncheckSelected())
        # noinspection PyUnresolvedReferences
        self._removeall.clicked.connect(lambda: self._tree.clear())

        self._pathlayout = QHBoxLayout()
        self._pathlayout.addWidget(self._ext)
        self._pathlayout.addWidget(self._dir)
        self._pathlayout.addStretch()

        self._checklyout = QHBoxLayout()
        self._checklyout.addWidget(self._checkall)
        self._checklyout.addWidget(self._uncheckall)
        self._checklyout.addWidget(self._checksel)
        self._checklyout.addWidget(self._unchecksel)
        self._checklyout.addWidget(self._removeall)
        self._checklyout.addStretch()

        lyout = QVBoxLayout(self)
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(10)
        lyout.addLayout(self._pathlayout)
        lyout.addWidget(self._tree)
        lyout.addLayout(self._checklyout)
        self.setLayout(lyout)

    def __getattr__(self, name: str) -> Any:
        """
            When attribute does not exist in the class, try calling self._tree DicomFilesTreeWidget method
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

    def newDirectory(self) -> None:
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            chdir(path)
            self._tree.setPath(path)

    def addDirectory(self) -> None:
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            self._tree.addPath(path)

    def getTreeWidget(self) -> QTreeWidget:
        return self._tree

    # noinspection PyShadowingBuiltins
    def setFilter(self, filter: str) -> None:
        flt = ['.*'] + getDicomExt()
        if filter in flt: self._ext.setCurrentText(filter)

    def setSelectionButtonVisibility(self, v: bool) -> None:
        self._checkall.setVisible(v)
        self._uncheckall.setVisible(v)
        self._checksel.setVisible(v)
        self._unchecksel.setVisible(v)

    def getSelectionButtonVisibility(self) -> bool:
        return self._checkall.isVisible()

    def selectionButtonVisibilityOn(self) -> None:
        self.setSelectionButtonVisibility(True)

    def selectionButtonVisibilityOff(self) -> None:
        self.setSelectionButtonVisibility(False)

    def setDirectoryButtonVisibility(self, v: bool) -> None:
        self._dir.setVisible(v)

    def getDirectoryButtonVisibility(self) -> bool:
        return self._dir.isVisible()

    def directoryButtonVisibilityOn(self) -> None:
        self.setDirectoryButtonVisibility(True)

    def directoryButtonVisibilityOff(self) -> None:
        self.setDirectoryButtonVisibility(False)

    def setFilterButtonVisibility(self, v: bool) -> None:
        self._ext.setVisible(v)

    def getFilterButtonVisibility(self) -> bool:
        return self._ext.isVisible()

    def filterButtonVisibilityOn(self) -> None:
        self.setFilterButtonVisibility(True)

    def filterButtonVisibilityOff(self) -> None:
        self.setFilterButtonVisibility(False)


class XmlDicomTreeViewWidget(QTreeWidget):
    """
    XmlDicomTreeViewWidget class

    Description
    ~~~~~~~~~~~

    QTreeView to display XmlDicom data elements.

    Inheritance
    ~~~~~~~~~~~

    QTreeView -> XmlDicomTreeViewWidget

    Last revision: 20/10/2025
    """

    # Special method

    """
    Private attributes

    _dcm    XmlDicom
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dcm = XmlDicom()

        # noinspection PyTypeChecker
        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # ExtendedSelection mode
        # noinspection PyTypeChecker
        self.setSelectionBehavior(QTreeWidget.SelectRows)     # Selecting only rows
        self.setAlternatingRowColors(True)
        self.setDragEnabled(False)
        self.setHeaderLabels(['Tag', 'Name', 'VR', 'VM', 'Value'])
        # noinspection PyUnresolvedReferences
        self.header().setDefaultAlignment(Qt.AlignCenter)

    # Public methods

    def isEmpty(self) -> bool:
        return self._dcm.isEmpty()

    def getXmlDicom(self) -> XmlDicom:
        return self._dcm

    def loadXmlDicom(self, filename: str) -> None:
        if exists(filename):
            self._dcm.loadXmlDicomFilename(filename)
            keys = self._dcm.getKeywords()
            for k in keys:
                data = self._dcm.getDataElement(k)
                if not isinstance(data, list):
                    item = QTreeWidgetItem([str(data.tag), data.keyword, data.VR, str(data.VM), str(data.value)])
                    # noinspection PyUnresolvedReferences
                    item.setCheckState(0, Qt.Unchecked)
                    self.addTopLevelItem(item)
                else:
                    if len(data) > 0:
                        root = QTreeWidgetItem([str(data[0].tag), data[0].keyword])
                        # noinspection PyUnresolvedReferences
                        root.setCheckState(0, Qt.Unchecked)
                        self.addTopLevelItem(root)
                        for d in data:
                            item = QTreeWidgetItem([str(d.tag), d.keyword, d.VR, str(d.VM), str(d.value)])
                            root.addChild(item)
            for i in range(4):
                self.resizeColumnToContents(i)

    def checkAll(self) -> None:
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Checked)

    def uncheckAll(self) -> None:
        n = self.topLevelItemCount()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Unchecked)

    def checkSelected(self) -> None:
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Checked)

    def uncheckSelected(self) -> None:
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Unchecked)

    def saveCheckedDataElementsToXml(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        keys = self._dcm.getKeywords()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def saveCheckedDataElementsToTxt(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def saveCheckedDataElementsToCSV(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def saveCheckedDataElementsToMatfile(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def saveCheckedDataElementsToExcel(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def saveCheckedDataElementsToLATEX(self, filename: str = '') -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
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

    def copyCheckedDataElementsToClipboard(self) -> None:
        n = self.topLevelItemCount()
        skeys = list()
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            self._dcm.copyDataElementValuesToClipboard(skeys)
