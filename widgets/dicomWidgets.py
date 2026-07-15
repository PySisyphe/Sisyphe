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

import sys

from os import getcwd
from os import chdir

from os.path import dirname
from os.path import join
from os.path import exists
from os.path import isfile
from os.path import basename

import cython

from glob import glob

from datetime import datetime

from math import sqrt

from numpy import int16
from numpy import int32
from numpy import uint16
from numpy import uint32
from numpy import iinfo
from numpy import array
from numpy import argmax

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
    """
    Convert a DICOM date string (YYYYMMDD) to a formatted date string.

    Parameters
    ----------
    date : str
        DICOM date string in YYYYMMDD format.
    separator : str (optional)
        separator to use between year, month, and day (default '/').

    Returns
    -------
    str
        formatted date string, or the original empty string if the input is empty.
    """
    if date == '': return date
    else: return separator.join([date[:4], date[4:6], date[6:]])


class DateValidator(QValidator):
    """
    DateValidator

    Description
    ~~~~~~~~~~~

    Validator for DICOM Date (DA) format (YYYYMMDD).

    Inheritance
    ~~~~~~~~~~~

    QValidator -> DateValidator

    Last revision: 10/06/2026
    """

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        """
        DateValidator instance constructor.

        Parameters
        ----------
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(DateValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        """
        Validate the input string as a DICOM date.

        Parameters
        ----------
        value : str
            string to validate.
        pos : int
             cursor position.

        Returns
        -------
        tuple[int, str, int]
            validation state, string, and position.
        """
        try:
            datetime.strptime(value, '%Y%m%d').date()
            return 2, value, pos
        except ValueError:
            return 0, value, pos


class DateTimeValidator(QValidator):
    """
    DateTimeValidator

    Description
    ~~~~~~~~~~~

    Validator for DICOM Date Time (DT) format.

    Inheritance
    ~~~~~~~~~~~

    QValidator -> DateTimeValidator

    Last revision: 10/06/2026
    """

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        """
        DateTimeValidator instance constructor.

        Parameters
        ----------
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(DateTimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        """
        Validate the input string as a DICOM date-time.

        Parameters
        ----------
        value : str
           string to validate.
        pos : int
            cursor position.

        Returns
        -------
        tuple[int, str, int]
            validation state, string, and position.
        """
        if DateValidator().validate(value[:8], 0)[0] == 2 and \
                TimeValidator().validate(value[6:], 0)[0] == 2:
            return 2, value, pos
        else:
            return 0, value, pos


class TimeValidator(QValidator):
    """
    TimeValidator

    Description
    ~~~~~~~~~~~

    Validator for DICOM Time (TM) format (HHMMSS).

    Inheritance
    ~~~~~~~~~~~

    QValidator -> TimeValidator

    Last revision: 10/06/2026
    """

    # Special method

    def __init__(self, parent: QObject | None = None) -> None:
        """
        TimeValidator instance constructor.

        Parameters
        ----------
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(TimeValidator, self).__init__(parent)

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        """
        Validate the input string as a DICOM time.

        Parameters
        ----------
        value : str
            string to validate.
        pos : int
            cursor position.

        Returns
        -------
        tuple[int, str, int]
            validation state, string, and position.
        """
        h = int(value[0:2])
        m = int(value[2:4])
        se = int(value[4:])
        if 0 <= h < 24 and 0 <= m < 60 and 0 <= se < 60:
            return 2, value, pos
        else:
            return 0, value, pos


class MultiIntValidator(QValidator):
    """
    MultiIntValidator

    Description
    ~~~~~~~~~~~

    Validator for multiple integer values separated by spaces.

    Inheritance
    ~~~~~~~~~~~

    QValidator -> MultiIntValidator

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _min    int, minimum value allowed for each integer.
    _max    int, maximum value allowed for each integer.
    _n      int, required number of integers.
    """

    def __init__(self,
                 nbmin: int,
                 nbmax: int,
                 n: int,
                 parent: QObject | None = None) -> None:
        """
        MultiIntValidator instance constructor.

        Parameters
        ----------
        nbmin : int
            minimum value.
        nbmax : int
            maximum value.
        n : int
            required count.
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(MultiIntValidator, self).__init__(parent)
        self._min = nbmin
        self._max = nbmax
        self._n = n

    # public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        """
        Validate the input string containing multiple integers.

        Parameters
        ----------
        value : str
            string to validate.
        pos : int
            cursor position.

        Returns
        -------
        tuple[int, str, int]
            validation state, string, and position.
        """
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
    """
    MultiDoubleValidator

    Description
    ~~~~~~~~~~~

    Validator for multiple double/float values separated by spaces.

    Inheritance
    ~~~~~~~~~~~

    QValidator -> MultiDoubleValidator

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _n      int, required number of double values.
    """

    def __init__(self,
                 n: int,
                 parent: QObject | None = None) -> None:
        """
        MultiDoubleValidator instance constructor.

        Parameters
        ----------
        n : int
            required count.
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(MultiDoubleValidator, self).__init__(parent)
        self._n = n

    # Public method

    def validate(self, value: str, pos: int) -> tuple[int, str, int]:
        """
        Validate the input string containing multiple doubles.

        Parameters
        ----------
        value : str
            string to validate.
        pos : int
            cursor position.

        Returns
        -------
        tuple[int, str, int]
            validation state, string, and position.
        """
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
    """
    LineEditDelegate

    Description
    ~~~~~~~~~~~

    Custom item delegate using DicomVRLineEdit for editing DICOM values in a view.

    Inheritance
    ~~~~~~~~~~~

    QStyledItemDelegate -> LineEditDelegate

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _dataset    Dataset | None, the DICOM dataset associated with the data being edited.
    """

    def __init__(self,
                 dataset: Dataset | None = None,
                 parent: QObject | None = None) -> None:
        """
        LineEditDelegate instance constructor.

        Parameters
        ----------
        dataset : Dataset | None (optional)
            DICOM dataset (default None).
        parent : QObject | None (optional)
            parent object (default None).
        """
        super(LineEditDelegate, self).__init__(parent)
        self._dataset = dataset

    # Public methods

    def createEditor(self, parent: QWidget | None, option:  QStyleOptionViewItem | None, index: QModelIndex) -> QLineEdit:
        """
        Create the DicomVRLineEdit editor for the given index.

        Parameters
        ----------
        parent : QWidget | None
            parent widget.
        option : QStyleOptionViewItem | None
            style option.
        index : QModelIndex

        Returns
        -------
        QLineEdit
        """
        index0 = index.model().index(index.row(), 0)
        # noinspection PyUnresolvedReferences
        item0 = index.model().itemFromIndex(index0)
        de = self._dataset[item0.data()]
        return DicomVRLineEdit(de, parent)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """
        Set the editor's text from the model's data for the given index.

        Parameters
        ----------
        editor : QWidget
            DicomVRLineEdit editor
        index: QModelIndex
        """
        # noinspection PyUnresolvedReferences
        editor.setText(index.model().itemFromIndex(index).text())

    def setModelData(self, editor: QWidget, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        """
        Set the model's data from the editor's text for the given index.

        Parameters
        ----------
        editor : QWidget
            DicomVRLineEdit editor
        model : QAbstractItemModel | None
        index : QModelIndex
        """
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

    A custom QLineEdit widget designed to handle various DICOM Value Representation (VR) types.

    Inheritance
    ~~~~~~~~~~~

    QLineEdit -> DicomVRLineEdit

    Last revision: 25/01/2026
    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _de     DataElement, the DICOM data element being edited.
    """

    def __init__(self,
                 de: DataElement | None = None,
                 parent: QWidget | None = None) -> None:
        """
        DicomVRLineEdit instance constructor.

        Parameters
        ----------
        de : DataElement | None
            DICOM Data Element.
        parent : QWidget | None
            Parent widget.
        """
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
        """
        Initialize the widget for the Application Entity (AE) DICOM data type.
        """
        self.setMaxLength(16)

    def _initAS(self):
        """
        Initialize the widget for the Age String (AS) DICOM data type.
        """
        self.setMaxLength(4)
        self.setInputMask('>00DA')
        self.setValidator(QRegExpValidator(QRegExp('^[0-9]{1,3}[DWMY]$')))

    def _initCS(self):
        """
        Initialize the widget for the Code String (CS) DICOM data type.
        """
        self.setMaxLength(16)

    def _initDA(self):
        """
        Initialize the widget for the Date (DA) DICOM data type.
        """
        self.setMaxLength(8)
        self.setInputMask('99999999')
        self.setValidator(DateValidator())

    def _initDS(self):
        """
        Initialize the widget for the Decimal String (DS) DICOM data type.
        """
        if self._de.VM == 1:
            self.setMaxLength(16)
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initDT(self):
        """
        Initialize the widget for the Date/Time (DT) DICOM data type.
        """
        self.setMaxLength(26)
        self.setInputMask('99999999999999')
        self.setValidator(DateTimeValidator())

    def _initFD(self):
        """
        Initialize the widget for the Floating point Double (FD) DICOM data type.
        """
        if self._de.VM == 1:
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initFL(self):
        """
        Initialize the widget for the Floating point Single (FL) DICOM data type.
        """
        if self._de.VM == 1:
            validator = QDoubleValidator()
            validator.setLocale(QLocale(QLocale.English))
            self.setValidator(validator)
        else:
            self.setValidator(MultiDoubleValidator(self._de.VM))

    def _initIS(self):
        """
        Initialize the widget for the Integer String (IS) DICOM data type.
        """
        if self._de.VM == 1:
            self.setMaxLength(12)
            self.setValidator(QIntValidator(iinfo(int32).min, iinfo(int32).max))
        else:
            self.setValidator(MultiIntValidator(iinfo(int32).min, iinfo(int32).max, self._de.VM))

    def _initLO(self):
        """
        Initialize the widget for the Long String (LO) DICOM data type.
        """
        self.setMaxLength(64)

    def _initLT(self):
        """
        Initialize the widget for the Long Text (LT) DICOM data type.
        """
        self.setMaxLength(10240)

    def _initPN(self):
        """
        Initialize the widget for the Person Name (PN) DICOM data type.
        """
        self.setMaxLength(64)
        # < Revision 25/01/2026
        # self.setValidator(QRegExpValidator(QRegExp('[A-Za-z\-\s]+\^[A-Za-z\-\s]+')))
        self.setValidator(QRegExpValidator(QRegExp(r'[A-Za-z\-\s]+\^[A-Za-z\-\s]+')))
        # Revision 25/01/2026 >

    def _initSH(self):
        """
        Initialize the widget for the Short String (SH) DICOM data type.
        """
        self.setMaxLength(16)

    def _initSL(self):
        """
        Initialize the widget for the Signed Long (SL) DICOM data type.
        """
        if self._de.VM == 1: self.setValidator(QIntValidator(iinfo(int32).min, iinfo(int32).max))
        else: self.setValidator(MultiIntValidator(iinfo(int32).min, iinfo(int32).max, self._de.VM))

    def _initSS(self):
        """
        Initialize the widget for the Signed Short (SS) DICOM data type.
        """
        if self._de.VM == 1: self.setValidator(QIntValidator(iinfo(int16).min, iinfo(int16).max))
        else: self.setValidator(MultiIntValidator(iinfo(int16).min, iinfo(int16).max, self._de.VM))

    def _initST(self):
        """
        Initialize the widget for the Short Text (ST) DICOM data type.
        """
        self.setMaxLength(16)

    def _initTM(self):
        """
        Initialize the widget for the Time (TM) DICOM data type.
        """
        self.setMaxLength(6)
        self.setInputMask('999999')
        self.setValidator(TimeValidator())

    def _initUI(self):
        """
        Initialize the widget for the Unique Identifier (UI) DICOM data type.
        """
        self.setMaxLength(64)
        # < Revision 25/01/2026
        # self.setValidator(QRegExpValidator(QRegExp('^[0-9][0-9\.]+[0-9]$')))
        self.setValidator(QRegExpValidator(QRegExp(r'^[0-9][0-9\.]+[0-9]$')))
        # Revision 25/01/2026 >

    def _initUL(self):
        """
        Initialize the widget for the Unsigned Long (UL) DICOM data type.
        """
        if self._de.VM == 1: self.setValidator(QIntValidator(0, iinfo(uint32).max))
        else: self.setValidator(MultiIntValidator(0, iinfo(uint32).max, self._de.VM))

    def _initUS(self):
        """
        Initialize the widget for the Unsigned Short (US) DICOM data type.
        """
        if self._de.VM == 1: self.setValidator(QIntValidator(0, iinfo(uint16).max))
        else: self.setValidator(MultiIntValidator(0, iinfo(uint16).max, self._de.VM))

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
    A specialized QTreeView designed to display and edit DICOM header information (tags, VR, VM, values).

    Inheritance
    ~~~~~~~~~~~
    QTreeView -> DicomHeaderTreeViewWidget

    Last revision: 10/06/2026
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

    _tag        bool, visibility of the tag column.
    _name       bool, visibility of the tag name column.
    _vr         bool, visibility of the VR column.
    _vm         bool, visibility of the VM column.
    _value      bool, visibility of the value column.
    _private    bool, visibility of private DICOM fields.
    _dataset    Dataset, current DICOM dataset.
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
        """
        DicomHeaderTreeViewWidget instance constructor.

        Parameters
        ----------
        dataset : Dataset | None (optional)
            initial dataset to display (default None).
        private : bool (optional)
            display private tags (default True).
        tag : bool (optional)
            display tag column (default True).
        name : bool (optional)
            display name column (default True).
        vr : bool (optional)
            display VR column (default True).
        vm : bool (optional)
            display VM column (default True).
        value : bool (optional)
            display value column (default True).
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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
        """
        Recursively populate the model with DICOM data elements.

        Parameters
        ----------
        dataset : Dataset
            DICOM dataset to iterate through.
        parent : QStandardItem
            parent item in the model.
        """
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
        """
        Clear and rebuild the model based on the current dataset and visibility settings.
        """
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

    def _setSectionVisibility(self, section: int = 0, v: bool = True) -> None:
        """
        Helper method to show or hide a header section.

        Parameters
        ----------
        section : int (optional)
            index of the section to modify (default 0).
        v : bool (optional)
            True to show the section, False to hide it (default True).
        """
        if v: self.header().showSection(section)
        else: self.header().hideSection(section)

    # Public methods

    def setDicomDataset(self, dataset: Dataset) -> None:
        """
        Set the DICOM dataset and refresh the view.

        Parameters
        ----------
        dataset : Dataset
            pydicom dataset.
        """
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            # noinspection PyUnresolvedReferences
            self.model().clear()
            self._dataset = dataset
            self.setItemDelegate(LineEditDelegate(self._dataset, self))
            self._updateModel()
        else: raise TypeError('parameter type {} is not pydicom.FileDataset.'.format(dataset))

    def getDicomDataset(self) -> Dataset:
        """
        Get current DICOM dataset.

        Returns
        -------
        Dataset
            current pydicom dataset.
        """
        return self._dataset

    def setDicomFile(self, filename: str) -> None:
        """
        Load a DICOM file and display its DICOM dataset.

        Parameters
        ----------
        filename : str
            DICOM filename
        """
        if exists(filename):
            if isDicom(filename):
                dataset = read_file(filename)
                self.setDicomDataset(dataset)
            else: raise IOError('{} is not a valid DICOM file.'.format(basename(filename)))
        else: raise IOError('{} no such file.'.format(basename(filename)))

    def setPrivateTagVisibility(self, v: bool) -> None:
        """
        Toggle visibility of private DICOM tags.
        """
        self._private = v
        self._updateModel()

    def setTagCodeVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the Tag code column.

        Parameters
        ----------
        v : bool
        """
        self._setSectionVisibility(0, v)

    def setTagNameVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the Tag name column.

        Parameters
        ----------
        v : bool
        """
        self._setSectionVisibility(1, v)

    def setVRVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the Value Representation (VR) column.

        Parameters
        ----------
        v : bool
        """
        self._setSectionVisibility(2, v)

    def setVMVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the Value Multiplicity (VM) column.

        Parameters
        ----------
        v : bool
        """
        self._setSectionVisibility(3, v)

    def setValueVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the value column.

        Parameters
        ----------
        v : bool
        """
        self._setSectionVisibility(4, v)

    def getSelectedDicomDataElements(self) -> list[DataElement]:
        """
        Return the list of selected DICOM Data Elements.

        Returns
        -------
        list[DataElement]
        """
        indexes = self.selectionModel().selectedRows(0)
        de = []
        if len(indexes) > 0:
            for index in indexes:
                # noinspection PyUnresolvedReferences
                item = self.model().itemFromIndex(index)
                if isinstance(item, QStandardItem):
                    de.append(self._dataset[item.data()])  # get DICOM Tag in key.data()
        return de

    def getSelectedDicomTags(self) -> list[BaseTag]:
        """
        Return the list of tags for selected rows.

        Returns
        -------
        list[BaseTag]
        """
        de = self.getSelectedDicomDataElements()
        taglist = []
        if len(de) > 0:
            for d in de:
                taglist.append(d.tag)
        return taglist

    def getSelectedDicomNames(self) -> list[str]:
        """
        Return the list of keywords for selected rows.

        Returns
        -------
        list[str]
        """
        de = self.getSelectedDicomDataElements()
        namelist = []
        if len(de) > 0:
            for d in de:
                namelist.append(d.name)
        return namelist

    def getSelectedDicomValues(self) -> list[str]:
        """
        Return the list of values for selected rows.

        Returns
        -------
        list[str]
        """
        de = self.getSelectedDicomDataElements()
        valuelist = []
        if len(de) > 0:
            for d in de:
                valuelist.append(str(d.value))
        return valuelist

    def getCheckedDicomNames(self) -> list[str] | None:
        """
        Return keywords of data elements with checked boxes.

        Returns
        -------
        list[str] | None
        """
        n = self.model().rowCount()
        if n > 0:
            r = list()
            i: cython.int
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
        """
        Return keywords of data elements that have been modified by the user.

        Returns
        -------
        list[str] | None
        """
        n = self.model().rowCount()
        if n > 0:
            r = list()
            i: cython.int
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
        """
        Scroll the view to a specific Data Element.

        Parameters
        ----------
        de : DataElement
        """
        if isinstance(de, DataElement):
            self.scrollToDicomTag(de.tag)

    def scrollToDicomTag(self, tag: int | str | tuple[int, int] | BaseTag) -> None:
        """
        Scroll the view to a specific DICOM tag.

        Parameters
        ----------
        tag : int | str | tuple[int, int] | BaseTag
            DICOM tag
        """
        if isinstance(tag, BaseTag):
            # noinspection PyUnresolvedReferences
            items = self.model().findItems(str(tag), Qt.MatchExactly, 0)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                # noinspection PyTypeChecker
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def scrollToDicomName(self, name: str) -> None:
        """
        Scroll the view to a specific DICOM keyword/name.

        Parameters
        ----------
        name : str
            DICOM keyword/name
        """
        if isinstance(name, str):
            # noinspection PyUnresolvedReferences
            items = self.model().findItems(name, Qt.MatchExactly, 1)
            if len(items) > 0:
                self.scrollTo(items[0].index())
                # noinspection PyTypeChecker
                self.selectionModel().select(items[0].index(), self._SELECTROWS)

    def checkSelectedRows(self) -> None:
        """
        Check the boxes for all currently selected rows.
        """
        indexlist = self.selectedIndexes()
        if len(indexlist) > 0:
            for index in indexlist:
                # noinspection PyUnresolvedReferences
                item = self.model().itemFromIndex(index)
                if item.isCheckable():
                    # noinspection PyUnresolvedReferences
                    item.setCheckState(Qt.Checked)

    def uncheckSelectedRows(self) -> None:
        """
        Uncheck the boxes for all currently selected rows.
        """
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
    DicomComboBoxWidget

    Description
    ~~~~~~~~~~~
    A QComboBox widget used to select DICOM tags from a loaded dataset.

    Inheritance
    ~~~~~~~~~~~
    QComboBox -> DicomComboBoxWidget

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _private    bool, visibility of private DICOM tags.
    _dataset    Dataset, the DICOM dataset.
    """

    def __init__(self,
                 dataset: Dataset | None = None,
                 private: bool = True,
                 parent: QWidget | None = None) -> None:
        """
        DicomComboBoxWidget instance constructor.

        Parameters
        ----------
        dataset : Dataset | None (optional)
            initial dataset (default None).
        private : bool (optional)
            include private tags (default True).
        parent : QWidget | None (optional)
            Parent widget (default None).
        """
        super(DicomComboBoxWidget, self).__init__(parent)
        self.setEditable(True)
        self._private = private
        self._dataset = dataset
        self._updateTagList()

    # Private method

    def _updateTagList(self) -> None:
        """
        Refresh the combobox items based on the current DICOM dataset.
        """
        if self._dataset is not None:
            self.clear()
            if not self._private:
                self._dataset.remove_private_tags()
            for k in self._dataset:
                if k.tag != (0x7fe0, 0x0010) and k.VR != 'SQ':  # extract pixel data and sequence
                    self.addItem(k.name, k.tag)

    # Public methods

    def setDicomDataset(self, dataset: Dataset, private: bool = True) -> None:
        """
        Load a new DICOM dataset into the combo box.

        Parameters
        ----------
        dataset: Dataset
            pydicom dataset
        private : bool (optional)
            include private tags if True, otherwise remove them (default True).
        """
        if isinstance(dataset, FileDataset) or isinstance(dataset, Dataset):
            self.clear()
            self._dataset = dataset
            self._private = private
            self._updateTagList()

    def getDicomDataset(self) -> Dataset:
        """
        Return current DICOM dataset.

        Returns
        -------
        Dataset
        """
        return self._dataset

    def setPrivateTagVisibility(self, v: bool) -> None:
        """
        Toggle visibility of private tags in the dropdown.

        Parameters
        ----------
        v : bool
        """
        self._private = v
        self._updateTagList()

    def getCurrentDicomDataElement(self) -> DataElement | None:
        """
        Get the currently selected Data Element.

        Returns
        -------
        DataElement
        """
        c = self.currentData()
        if c:
            de = self._dataset[c]
            if isinstance(de, DataElement):
                return de
        return None

    def getCurrentDicomTag(self) -> BaseTag | None:
        """
        Get the currently selected DICOM tag.

        Returns
        -------
        BaseTag | None
        """
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.tag
        return None

    def getCurrentDicomName(self) -> str | None:
        """
        Get the currently selected DICOM keyword/name.

        Returns
        -------
        str | None
        """
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.name
        return None

    def getCurrentDicomValue(self) -> Any | None:
        """
        Get the currently selected value.

        Returns
        -------
        Any | None
            Dicom value
        """
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.value
        return None

    def getCurrentDicomVR(self) -> str | None:
        """
        Get the currently selected Value Representation.

        Returns
        -------
        str | None
        """
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VR
        return None

    def getCurrentDicomVM(self) -> int | None:
        """
        Get the currently selected Value Multiplicity.

        Returns
        -------
        int | None
        """
        de = self.getCurrentDicomDataElement()
        if de:
            if isinstance(de, DataElement):
                return de.VM
        return None


class DicomFilesTreeWidget(QTreeWidget):
    """
    DicomFilesTreeWidget

    Description
    ~~~~~~~~~~~
    A QTreeWidget used to display DICOM files organized by series.

    Inheritance
    ~~~~~~~~~~~
    QTreeWidget -> DicomFilesTreeWidget

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _dict           dict, structured metadata mapping Series UID to acquisitions and files.
                    Keys include modality, name, birthdate, acqdate, protocol, mosaic, and 'acq'.
                    'acq' sub-dictionary maps acquisition tuples to:
                           'index': list[int] instance numbers,
                           'files': list[str] file paths,
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
        """
        DicomFilesTreeWidget instance constructor.

        Parameters
        ----------
        path : str | None (optional)
            path used to search for DICOM files (default None).
        filter : str (optional)
            filter extension to search dicom files (default '.*').
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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

    def _onToggleCheckbox(self, item: QTreeWidgetItem):
        """
        Recursively update the check state of children when a parent item is toggled.

        Parameters
        ----------
        item : QTreeWidgetItem
            item whose check state has changed.
        """
        if isinstance(item, QTreeWidgetItem):
            checkstate = item.checkState(0)
            if item.childCount() > 0:
                i: cython.int
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, checkstate)
                    if item.childCount() > 0: self._onToggleCheckbox(item.child(i))

    def _pathToDict(self):
        """
        Scan search paths and parse DICOM files into the internal metadata dictionary.
        """
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
                        if v > 1:
                            # < Revision 01/04/2026
                            # mosaic = ((v // 8) + 1) * 8
                            mosaic = (int(sqrt(v)) + 1) ** 2
                            # Revision 01/04/2026 >
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
                        # < Revision 30/06/2026
                        # cython crashes when using i, which is declared later in the source code as cython.int
                        # item['index'] = [i[0] for i in r]
                        # item['files'] = [i[1] for i in r]
                        # item['loc'] = [i[2] for i in r]
                        item['index'] = [v[0] for v in r]
                        item['files'] = [v[1] for v in r]
                        item['loc'] = [v[2] for v in r]
                        # Revision 30/06/2026 >
                        # < Revision 01/07/2025
                        # Subseries extraction
                        if item['loc'][0] is not None:
                            r = len(item['loc']) / len(set(item['loc']))
                            # Duplicate slice location in acquisition number if r > 1
                            if r > 1.0:
                                i: cython.int
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
        """
        Clear the tree widget and rebuild it from the internal metadata dictionary.
        """
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
                    j: cython.int
                    k: cython.int
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
                        # < Revision 24/02/2026
                        self._dict[series]['acq'][acq[j]]['files'] = self._verifySliceOrder(self._dict[series]['acq'][acq[j]]['files'])
                        # Revision 24/02/2026 >
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
        """
        Rescan the file system and refresh the widget content.
        """
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

    # < Revision 24/02/2026
    @staticmethod
    def _verifySliceOrder(filenames: list[str]) -> list[str]:
        """
        Analyze the slice positions of the files and reverse the order if necessary.

        Parameters
        ----------
        filenames : list[str]
            List of file paths to check.

        Returns
        -------
        list[str]
            potentially reordered list of filenames.
        """
        try:
            # Extract ImagePositionPatient
            dsfirst = read_file(filenames[0], stop_before_pixels=True, specific_tags=[Tag(0x0020, 0x0032)])
            dslast = read_file(filenames[-1], stop_before_pixels=True, specific_tags=[Tag(0x0020, 0x0032)])
            pfirst = dsfirst[0x0020, 0x0032].value
            plast = dslast[0x0020, 0x0032].value
            i = argmax(abs(array(plast) - array(pfirst)))
            if pfirst[i] > plast[i]:
                filenames = filenames[::-1]
        except: pass
        return filenames
    # Revision 24/02/2026 >

    # Public methods

    def treeUpdate(self) -> None:
        """
        Update the tree display based on the internal DICOM metadata dictionary.
        """
        self._dictToWidget()

    def getDict(self) -> dict:
        """
        Get the internal structured DICOM metadata dictionary.

        Returns
        -------
        dict
        """
        return self._dict

    def isMosaic(self, series: str) -> bool | None:
        """
        Check if a series contains Siemens mosaic data.

        Parameters
        ----------
        series : str
            Series UID.

        Returns
        -------
        bool | None
        """
        # noinspection PyInconsistentReturns
        if series in self._dict:
            return self._dict[series]['mosaic'] != 1

    def getMosaic(self, series: str) -> int | None:
        """
        Get the mosaic image count for a series.

        Parameters
        ----------
        series : str
            Series UID.

        Returns
        -------
        int | None
        """
        # noinspection PyInconsistentReturns
        if series in self._dict:
            return self._dict[series]['mosaic']

    def getSelectedSeriesCount(self) -> int:
        """
        Return count of checked series items.

        Returns
        -------
        int
        """
        c = 0
        n = self.topLevelItemCount()
        i: cython.int
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            if item.checkState(0) == Qt.Checked: c += 1
        return c

    def getSelectedAcquisitionsCount(self) -> int:
        """
        Return count of checked acquisition items.

        Returns
        -------
        int
        """
        c = 0
        ns = self.topLevelItemCount()
        i: cython.int
        j: cython.int
        for i in range(ns):
            sitem = self.topLevelItem(i)
            na = sitem.childCount()
            for j in range(na):
                aitem = sitem.child(j)
                # noinspection PyUnresolvedReferences
                if aitem.checkState(0) == Qt.Checked: c += 1
        return c

    def getModalityFilter(self) -> list[str]:
        """
        Get current modality filters.

        Returns
        -------
        list[str]
        """
        return self._modalityfilter

    def clearModalityFiler(self) -> None:
        """
        Clear all modality filters.
        """
        self._modalityfilter = list()

    def setModalityFilterToImages(self) -> None:
        """
        Set filter to common image modalities.
        """
        self._modalityfilter = getDicomImageModalities()

    def setModalityFilterToRT(self) -> None:
        """
        Set filter to Radiotherapy modalities.
        """
        self._modalityfilter = getDicomRTModalities()

    def setModalityFilterToAll(self) -> None:
        """
        Include all modalities in the filter.
        """
        self._modalityfilter = getDicomModalities()

    def addCTtoModalityFilter(self) -> None:
        """
        Include CT in the filter.
        """
        if 'CT' not in self._modalityfilter:
            self._modalityfilter.append('CT')

    def addMRtoModalityFilter(self) -> None:
        """
        Include MR in the filter.
        """
        if 'MR' not in self._modalityfilter:
            self._modalityfilter.append('MR')

    def addPTtoModalityFilter(self) -> None:
        """
        Include PT in the filter.
        """
        if 'PT' not in self._modalityfilter:
            self._modalityfilter.append('PT')

    def addNMtoModalityFilter(self) -> None:
        """
        Include NM in the filter.
        """
        if 'NM' not in self._modalityfilter:
            self._modalityfilter.append('NM')

    def addOTtoModalityFilter(self) -> None:
        """
        Include Other (OT) in the filter.
        """
        if 'OT' not in self._modalityfilter:
            self._modalityfilter.append('OT')

    def addRTStructToModalityFilter(self) -> None:
        """
        Include RTSTRUCT in the filter.
        """
        if 'RTSTRUCT' not in self._modalityfilter:
            self._modalityfilter.append('RTSTRUCT')

    def addRTDoseToModalityFilter(self) -> None:
        """
        Include RTDOSE in the filter.
        """
        if 'RTDOSE' not in self._modalityfilter:
            self._modalityfilter.append('RTDOSE')

    def setDefaultFilter(self) -> None:
        """
        Reset filter to default (all extensions).
        """
        self.setFilter('.*')

    def setFilter(self, v: str) -> None:
        """
        Set the file extension filter.

        Parameters
        ----------
        v : str
        """
        if isinstance(v, str):
            flt = ['.*'] + getDicomExt()
            if v in flt:
                self._filter = v[v.find('.'):]
                path = self._path
                self._path = list()
                i: cython.int
                for i in range(len(path)):
                    if i == 0: self.setPath(path[i])
                    else: self.addPath(path[i])
            else: messageBox(self,
                             'Set DICOM file extension',
                             text='{} is not a DICOM file extension.'.format(v))
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def getFilter(self) -> str:
        """
        Get the current file extension filter.

        Returns
        -------
        str
        """
        return self._filter

    def setPath(self, path: str) -> None:
        """
        Set a single search path and update.

        Parameters
        ----------
        path : str
        """
        if path not in self._path:
            self._path = [path]
            self.clear()
            self._dict = dict()
            self._updateWidget()

    def addPath(self, path: str) -> None:
        """
        Add an additional search path and update.

        Parameters
        ----------
        path : str
        """

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
        """
        Get the list of current search paths.

        Returns
        -------
        list[str]
        """
        return self._path

    def hasPath(self) -> bool:
        """
        Check if any paths are set.

        Returns
        -------
        bool
        """
        return len(self._path) > 0

    def extractDataElements(self, tag: int | str | tuple[int, int] | BaseTag, series: str) -> dict:
        """
        Extract values for a specific tag across a series.

        Parameters
        ----------
        tag: int | str | tuple[int, int] | BaseTag
            DICOM tag.
        series: str
            Series UID.

        Returns
        -------
        dict
        """
        r = dict()
        j: cython.int
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
        """
        Check all items in the tree.
        """
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Checked)
            self._onToggleCheckbox(item)

    def uncheckAll(self) -> None:
        """
        Uncheck all items in the tree.
        """
        i: cython.int
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Unchecked)
            self._onToggleCheckbox(item)

    def checkSelected(self) -> None:
        """
        Check currently selected rows.
        """
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Checked)
                self._onToggleCheckbox(item)

    def uncheckSelected(self) -> None:
        """
        Uncheck currently selected rows.
        """
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Unchecked)
                self._onToggleCheckbox(item)


class DicomFilesEnhancedTreeWidget(QWidget):
    """
    DicomFilesEnhancedTreeWidget

    Description
    ~~~~~~~~~~~
    A container widget embedding a DicomFilesTreeWidget with additional UI controls (buttons, filters)
    to manage DICOM files and selections.

    Inheritance
    ~~~~~~~~~~~
    QWidget -> DicomFilesEnhancedTreeWidget

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _tree       DicomFilesTreeWidget, the embedded tree widget.
    _ext        QComboBox, dropdown for file extension filtering.
    _dir        MenuPushButton, button to select or add directories.
    _checkall   QPushButton, button to check all items.
    _uncheckall QPushButton, button to uncheck all items.
    _checksel   QPushButton, button to check selected items.
    _unchecksel QPushButton, button to uncheck selected items.
    _removeall  QPushButton, button to clear the tree.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 path: str | None = None,
                 filter: str = '.*',
                 parent: QWidget | None = None) -> None:
        """
        DicomFilesEnhancedTreeWidget instance constructor.

        Parameters
        ----------
        path : str | None (optional)
            initial search path (None).
        filter : str (optional)
            initial file extension filter (default '.*').
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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
        When attribute does not exist in the class, try calling self._tree DicomFilesTreeWidget method.
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
        """
        Handle changes in the extension filter combobox.
        """
        ext = self._ext.currentText()
        self._tree.setFilter(ext)

    # Public methods

    def newDirectory(self) -> None:
        """
        Clear paths and select a new root directory.
        """
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            chdir(path)
            self._tree.setPath(path)

    def addDirectory(self) -> None:
        """
        Add a directory to the existing search paths.
        """
        if self._tree.hasPath(): path = self._tree.getPath()[-1]
        else: path = getcwd()
        path = QFileDialog.getExistingDirectory(self,
                                                'Select DICOM directory', path,
                                                options=QFileDialog.ShowDirsOnly)
        if path:
            self._tree.addPath(path)

    def getTreeWidget(self) -> QTreeWidget:
        """
        Return the underlying DicomFilesTreeWidget.

        Returns
        -------
        QTreeWidget
        """
        return self._tree

    # noinspection PyShadowingBuiltins
    def setFilter(self, filter: str) -> None:
        """
        Set the current extension filter.

        Parameters
        ----------
        filter : str
        """
        flt = ['.*'] + getDicomExt()
        if filter in flt: self._ext.setCurrentText(filter)

    def setSelectionButtonVisibility(self, v: bool) -> None:
        """
        Toggle visibility of check/uncheck buttons.

        Parameters
        ----------
        v : bool
        """
        self._checkall.setVisible(v)
        self._uncheckall.setVisible(v)
        self._checksel.setVisible(v)
        self._unchecksel.setVisible(v)

    def getSelectionButtonVisibility(self) -> bool:
        """
        Get the check/uncheck buttons visbility.

        Returns
        -------
        bool
        """
        return self._checkall.isVisible()

    def selectionButtonVisibilityOn(self) -> None:
        """
        Show selection control buttons.
        """
        self.setSelectionButtonVisibility(True)

    def selectionButtonVisibilityOff(self) -> None:
        """
        Hide selection control buttons.
        """
        self.setSelectionButtonVisibility(False)

    def setDirectoryButtonVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the directory selection button.

        Parameters
        ----------
        v : bool
        """
        self._dir.setVisible(v)

    def getDirectoryButtonVisibility(self) -> bool:
        """
        Get the directory selection button visbility.

        Returns
        -------
        bool
        """
        return self._dir.isVisible()

    def directoryButtonVisibilityOn(self) -> None:
        """
        Show directory button.
        """
        self.setDirectoryButtonVisibility(True)

    def directoryButtonVisibilityOff(self) -> None:
        """
        Hide directory button.
        """
        self.setDirectoryButtonVisibility(False)

    def setFilterButtonVisibility(self, v: bool) -> None:
        """
        Toggle visibility of the extension filter combobox.

        Parameters
        ----------
        v : bool
        """
        self._ext.setVisible(v)

    def getFilterButtonVisibility(self) -> bool:
        """
        Get the extension filter combobox visbility.

        Returns
        -------
        bool
        """
        return self._ext.isVisible()

    def filterButtonVisibilityOn(self) -> None:
        """
        Show extension filter combobox.
        """
        self.setFilterButtonVisibility(True)

    def filterButtonVisibilityOff(self) -> None:
        """
        Hide extension filter combobox.
        """
        self.setFilterButtonVisibility(False)


class XmlDicomTreeViewWidget(QTreeWidget):
    """
    XmlDicomTreeViewWidget

    Description
    ~~~~~~~~~~~
    A QTreeWidget specialized to display and export DICOM data elements stored in an XmlDicom container.

    Inheritance
    ~~~~~~~~~~~
    QTreeWidget -> XmlDicomTreeViewWidget

    Last revision: 10/06/2026
    """

    # Special method

    """
    Private attributes

    _dcm    XmlDicom, the data container holding DICOM elements.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        XmlDicomTreeViewWidget instance constructor.

        Parameters
        ----------
        parent : QWidget | None (optional)
            parent widget (default None).
        """
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
        """
        Check if the underlying container is empty.
        """
        return self._dcm.isEmpty()

    def getXmlDicom(self) -> XmlDicom:
        """
        Return the XmlDicom container.
        
        Returns
        -------
        XmlDicom
        """
        return self._dcm

    def loadXmlDicom(self, filename: str) -> None:
        """
        Load an XML DICOM file and populate the tree.
        """
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
            i: cython.int
            for i in range(4):
                self.resizeColumnToContents(i)

    def checkAll(self) -> None:
        """
        Check all items in the tree.
        """
        n = self.topLevelItemCount()
        i: cython.int
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Checked)

    def uncheckAll(self) -> None:
        """
        Uncheck all items in the tree.
        """
        n = self.topLevelItemCount()
        i: cython.int
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            item.setCheckState(0, Qt.Unchecked)

    def checkSelected(self) -> None:
        """
        Check currently selected rows.
        """
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Checked)

    def uncheckSelected(self) -> None:
        """
        Uncheck currently selected rows.
        """
        items = self.selectedItems()
        if len(items) > 0:
            for item in self.selectedItems():
                # noinspection PyUnresolvedReferences
                item.setCheckState(0, Qt.Unchecked)

    def saveCheckedDataElementsToXml(self, filename: str = '') -> None:
        """
        Save checked elements to a Sisyphe XML sheet.

        Parameters
        ----------
        filename : str (optional)
           XML sheet filename (default '').
        """
        n = self.topLevelItemCount()
        keys = self._dcm.getKeywords()
        skeys = list()
        i: cython.int
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
        """
        Save checked elements to a text file.

        Parameters
        ----------
        filename : str (optional)
           text filename (default '').
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
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
        """
        Save checked elements to a CSV file.

        Parameters
        ----------
        filename : str (optional)
           CSV filename (default '').
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
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
        """
        Save checked elements to a MATLAB .mat file.

        Parameters
        ----------
        filename : str (optional)
           MATLAB .mat filename (default '').
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
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
        """
        Save checked elements to an Excel .xlsx file.

        Parameters
        ----------
        filename : str (optional)
           Excel .xlsx filename (default '').
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
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
                try: self._dcm.saveDataElementValuesToExcel(skeys, filename)
                except:
                    # < Revision 19/02/2026
                    try:
                        import openpyxl
                        messageBox(self, title='Save Excel file', text='{} saving error.'.format(basename(filename)))
                    except:
                        if hasattr(sys, '_MEIPASS'):
                            messageBox(self,
                                       'XLSX IO',
                                       'OpenPyXL module is not installed.\n'
                                       'Please perform a complete reinstallation of the latest version '
                                       'of PySisyphe, which can be downloaded from '
                                       'https://github.com/PySisyphe/Sisyphe.')
                        else:
                            messageBox(self,
                                       'XLSX IO',
                                       'OpenPyXL module is not installed.\n'
                                       'Please install it using "pip install openpyxl==3.1.5" from your venv console.')
                    # Revision 19/02/2026 >

    def saveCheckedDataElementsToLATEX(self, filename: str = '') -> None:
        """
        Save checked elements to a LaTeX table format.

        Parameters
        ----------
        filename : str (optional)
           LaTeX filename (default '').
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
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
        """
        Copy checked data elements to the system clipboard.
        """
        n = self.topLevelItemCount()
        skeys = list()
        i: cython.int
        for i in range(n):
            item = self.topLevelItem(i)
            # noinspection PyUnresolvedReferences
            if item.checkState(0) == Qt.Checked:
                skeys.append(item.text(1))
        if len(skeys) > 0:
            self._dcm.copyDataElementValuesToClipboard(skeys)
