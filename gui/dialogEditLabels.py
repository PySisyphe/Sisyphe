"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import join
from os.path import exists
from os.path import splitext

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.iconBarViewWidgets import IconBarSliceViewWidget

_all__ = ['DialogEditLabels']

"""
    Class hierarchy

        QDialog -> DialogEditLabels

"""


class DialogEditLabels(QDialog):
    """
        DialogEditLabels class

        Inheritance

            QWidget -> QDialog -> DialogEditLabels

        Private attributes

            _volume     SisypheVolume

        Public methods

            setVolume(SisypheVolume)

            inherited QDialog methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Edit labels')
        self.setMinimumSize(1000, 400)

        self._volume = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init widgets

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        self._view = IconBarSliceViewWidget()

        self._tree = QTreeWidget()
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.setHeaderLabels(['Values', 'Labels'])
        for i in range(256):
            item = QTreeWidgetItem(self._tree)
            item.setText(0, str(i))
            item.setTextAlignment(0, Qt.AlignCenter)
            self._tree.addTopLevelItem(item)
            edit = QLineEdit()
            self._tree.setItemWidget(item, 1, edit)
        self._tree.topLevelItem(0).setSelected(True)
        self._tree.itemSelectionChanged.connect(self._selectionChanged)

        layout.addWidget(self._view)
        layout.addWidget(self._tree)
        self._layout.addLayout(layout)

        self._sep = LabeledLineEdit(label='Separator', default=',', fontsize=10)
        self._labelpos = LabeledSpinBox(title='Label position', fontsize=10)
        self._indexpos = LabeledSpinBox(title='Index position', fontsize=10)
        self._indexpos.setRange(0, 100)
        self._indexpos.setValue(0)
        self._labelpos.setRange(0, 100)
        self._labelpos.setValue(1)

        io = MenuPushButton('Import/export')
        io.setFixedWidth(150)
        io.setToolTip('Import list of labels from a text file (*.txt)')
        menu = io.getPopupMenu()
        self._asep = QWidgetAction(self)
        self._asep.setDefaultWidget(self._sep)
        self._aindexpos = QWidgetAction(self)
        self._aindexpos.setDefaultWidget(self._indexpos)
        self._alabelpos = QWidgetAction(self)
        self._alabelpos.setDefaultWidget(self._labelpos)
        menu.addAction(self._asep)
        menu.addAction(self._aindexpos)
        menu.addAction(self._alabelpos)
        menu.addSeparator()
        load = menu.addAction('Load labels from text file...')
        save = menu.addAction('Save labels to text file...')
        load.triggered.connect(self._load)
        save.triggered.connect(self._save)

        clear = QPushButton('Clear labels')
        clear.setFixedWidth(100)
        clear.clicked.connect(self._clear)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)

        layout.addWidget(ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.addWidget(clear)
        layout.addWidget(io)
        self._layout.addLayout(layout)
        ok.clicked.connect(self._saveLabels)
        cancel.clicked.connect(self.reject)

    # Private method

    def _saveLabels(self):
        if self._volume is not None:
            acq = self._volume.getAcquisition()
            acq.getLabels().clear()
            for i in range(256):
                item = self._tree.topLevelItem(i)
                edit = self._tree.itemWidget(item, 1)
                if edit.text() != '': acq.setLabel(i, edit.text())
            acq.saveLabels()
            self.accept()

    def _selectionChanged(self):
        item = self._tree.selectedItems()
        if item is not None: item = item[0]
        n = int(item.text(0))
        self._view().getDrawInstance().extractingValue(n, mask=False, replace=True)
        self._view().updateRender()

    def _load(self):
        if self._volume is not None:
            filename = QFileDialog.getOpenFileName(self, 'Load labels from text file...', getcwd(), filter='text file (*.txt)')[0]
            if filename and exists(filename):
                with open(filename, 'r') as f:
                    lines = f.readlines()
                idxint = self._indexpos.value()
                idxlbl = self._labelpos.value()
                sep = self._sep.getEditText()
                for line in lines:
                    r = line.split(sep)
                    idx = int(r[idxint])
                    lbl = str(r[idxlbl])
                    if 0 <= idx < 256:
                        item = self._tree.topLevelItem(idx)
                        edit = self._tree.itemWidget(item, 1)
                        edit.setText(lbl)

    def _save(self):
        if self._volume is not None:
            filename = splitext(self._volume.getFilename())[0] + '.txt'
            filename = QFileDialog.getSaveFileName(self, 'Save labels to text file...', filename, filter='text file (*.txt)')[0]
            if filename:
                sep = self._sep.getEditText()
                with open(filename, 'w') as f:
                    for i in range(256):
                        item = self._tree.topLevelItem(i)
                        edit = self._tree.itemWidget(item, 1)
                        txt = edit.text()
                        if txt != '':
                            line = '{}{}{}\n'.format(i, sep, txt)
                            f.write(line)

    def _clear(self):
        for i in range(256):
            item = self._tree.topLevelItem(i)
            edit = self._tree.itemWidget(item, 1)
            edit.setText('')

    # Public method

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            self._volume = vol
            self._view.setVolume(self._volume)
            self._view().newROI()
            self._view().setInfoVisibilityOn()
            self._view().setInfoValueVisibilityOn()
            self._selectionChanged()
            labels = self._volume.getAcquisition().getLabels()
            if labels is not None and len(labels) > 0:
                for i in range(256):
                    if i in labels:
                        item = self._tree.topLevelItem(i)
                        edit = self._tree.itemWidget(item, 1)
                        edit.setText(labels[i])

    def getVolume(self):
        return self._volume


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = DialogEditLabels()
    v = SisypheVolume()
    v.load('/Users/jean-albert/PycharmProjects/python310Project/TESTS/LABELS/ICBM_LABELS_181x197x181.xvol')
    main.setVolume(v)
    main.show()
    app.exec_()


