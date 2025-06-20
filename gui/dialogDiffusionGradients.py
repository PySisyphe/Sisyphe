"""
External packages/modules
-------------------------

    - PyQt5,Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import basename
from os.path import splitext

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheDicom import saveBVal
from Sisyphe.core.sisypheDicom import saveBVec
from Sisyphe.core.sisypheDicom import removeSuffixNumberFromFilename
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

__all__ = ['DialogDiffusionGradients']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDiffusionGradients
"""

class DialogDiffusionGradients(QDialog):
    """
    DialogDiffusionPreprocessing

    Description
    ~~~~~~~~~~~

    GUI dialog window, association of diffusion dwi files with diffusion gradients saved in xbval and xbvec files.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDiffusionGradients

    Last revision: 17/06/2025
    """

    # Special method

    """
    Private attributes

    _layout         QVBoxLayout, main QLayout of the dialog
    _dwiSelect      FilesSelectionWidget, dwi files
    _bvals          FileSelectionWidget, bval file
    _bvecs          FileSelectionWidget, bvec file
    _save           QPushButton
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Diffusion gradients')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._dwiSelect = FilesSelectionWidget()
        self._dwiSelect.filterSisypheVolume()
        self._dwiSelect.setReferenceVolumeToFirst()
        self._dwiSelect.filterSameModality()
        self._dwiSelect.filterSameSequence()
        self._dwiSelect.filterSameFOV()
        self._dwiSelect.filterSameDatatype()
        self._dwiSelect.filterSameIdentity()
        self._dwiSelect.setTextLabel('Diffusion weighted volumes')
        self._dwiSelect.setMinimumWidth(500)
        self._dwiSelect.setCurrentVolumeButtonVisibility(False)
        self._dwiSelect.FieldChanged.connect(self._updateDwi)
        self._dwiSelect.FieldCleared.connect(self._updateDwi)

        self._bvals = FileSelectionWidget()
        self._bvals.setTextLabel('Associated B-values')
        self._bvals.filterExtension('.bval')
        self._bvals.setEnabled(False)
        self._bvals.FieldChanged.connect(self._updateBVals)

        self._bvecs = FileSelectionWidget()
        self._bvecs.setTextLabel('Associated gradient directions')
        self._bvecs.alignLabels(self._bvals)
        self._bvecs.filterExtension('.bvec')
        self._bvecs.setEnabled(False)
        self._bvecs.FieldChanged.connect(self._updateBVecs)

        self._layout.addWidget(self._dwiSelect)
        self._layout.addWidget(self._bvals)
        self._layout.addWidget(self._bvecs)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._exit = QPushButton('Close')
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        self._exit.setFixedWidth(100)
        self._save = QPushButton('Save')
        self._save.setFixedWidth(100)
        self._save.setToolTip('save xbvals and xbvecs files')
        self._save.setEnabled(False)
        layout.addWidget(self._exit)
        layout.addWidget(self._save)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.save)

        # < Revision 17/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._dwiSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 17/06/2025 >
        self.setModal(True)

    # Private methods

    def _updateDwi(self):
        self._bvals.clear(signal=False)
        self._bvecs.clear(signal=False)
        self._bvals.setToolTip('')
        self._bvecs.setToolTip('')
        self._bvals.setEnabled(not self._dwiSelect.isEmpty())
        self._bvecs.setEnabled(not self._dwiSelect.isEmpty())

    def _updateBVals(self):
        try: v = loadBVal(self._bvals.getFilename())
        except:
            messageBox(self,
                       'Diffusion gradients',
                       text='{} file format is invalid.'.format(basename(self._bvals.getFilename())))
            self._bvals.clear(signal=False)
            self._bvecs.clear(signal=False)
            self._bvals.setToolTip('')
            self._bvecs.setToolTip('')
            self._save.setEnabled(False)
            return None
        if len(v) != self._dwiSelect.filenamesCount():
            self._bvals.clear(signal=False)
            self._bvals.setToolTip('')
            messageBox(self,
                       'Diffusion gradients',
                       'There are not as many B values as there are dwi files.')
            # noinspection PyInconsistentReturns
            self._save.setEnabled(False)
        else:
            dwinames = self._dwiSelect.getFilenames()
            if len(v) > 1:
                v = list(v.values())
                buff = '{}: {}'.format(basename(dwinames[0]), str(v[0]))
                for i in range(1, len(v)):
                    buff += '\n{}: {}'.format(basename(dwinames[i]), str(v[i]))
                self._bvals.setToolTip(buff)
            # noinspection PyInconsistentReturns
            self._save.setEnabled(not self._bvecs.isEmpty())

    def _updateBVecs(self):
        try: v = loadBVec(self._bvecs.getFilename(), format='txtbydim')
        except:
            try: v = loadBVec(self._bvecs.getFilename(), format='txtbyvec')
            except:
                messageBox(self,
                           'Diffusion gradients',
                           text='{} file format is invalid.'.format(basename(self._bvecs.getFilename())))
                self._bvals.clear(signal=False)
                self._bvecs.clear(signal=False)
                self._bvals.setToolTip('')
                self._bvecs.setToolTip('')
                self._save.setEnabled(False)
                return None
        if len(v) != self._dwiSelect.filenamesCount():
            self._bvecs.clear(signal=False)
            self._bvecs.setToolTip('')
            messageBox(self, 'Diffusion gradients', 'There are not as many gradients directions as there are dwi files.')
            # noinspection PyInconsistentReturns
            self._save.setEnabled(False)
        else:
            v = list(v.values())
            if len(v) > 1:
                dwinames = self._dwiSelect.getFilenames()
                buff = '{}: {}'.format(basename(dwinames[0]), ' '.join([str(j) for j in v[0]]))
                for i in range(1, len(v)):
                    buff += '\n{}: {}'.format(basename(dwinames[i]), ' '.join([str(j) for j in v[i]]))
                self._bvecs.setToolTip(buff)
            # noinspection PyInconsistentReturns
            self._save.setEnabled(not self._bvecs.isEmpty())

    # Public method

    def save(self):
        if not (self._dwiSelect.isEmpty() or self._bvals.isEmpty() or self._bvecs.isEmpty()):
            dwinames = self._dwiSelect.getFilenames()
            # Load bvals
            try: bvals = loadBVal(self._bvals.getFilename())
            except:
                messageBox(self,
                           'Diffusion gradients',
                           text='{} file format is invalid.'.format(basename(self._bvals.getFilename())))
                self._bvals.clear(signal=False)
                self._bvecs.clear(signal=False)
                self._bvals.setToolTip('')
                self._bvecs.setToolTip('')
                self._save.setEnabled(False)
                return None
            # Load bvecs
            try: bvecs = loadBVec(self._bvecs.getFilename(), format='txtbydim')
            except:
                try: bvecs = loadBVec(self._bvecs.getFilename(), format='txtbyvec')
                except:
                    messageBox(self,
                               'Diffusion gradients',
                               text='{} file format is invalid.'.format(basename(self._bvecs.getFilename())))
                    self._bvals.clear(signal=False)
                    self._bvecs.clear(signal=False)
                    self._bvals.setToolTip('')
                    self._bvecs.setToolTip('')
                    self._save.setEnabled(False)
                    return None
            bvals2 = dict()
            bvecs2 = dict()
            for i in range(len(bvals)):
                bvals2[dwinames[i]] = bvals[str(i)]
                bvecs2[dwinames[i]] = bvecs[str(i)]
            base = splitext(removeSuffixNumberFromFilename(dwinames[0]))[0]
            bvalname = base + '.xbval'
            bvecname = base + '.xbvec'
            saveBVal(bvalname, bvals2, format='xml')
            saveBVec(bvecname, bvecs2, format='xml')
            messageBox(self,
                       'Diffusion gradients',
                       text='files {} and {} are saved.'.format(basename(bvalname), basename(bvecname)))
            self._dwiSelect.clearall()
            self._bvals.clear(signal=False)
            self._bvecs.clear(signal=False)
            self._bvals.setToolTip('')
            self._bvecs.setToolTip('')
            self._bvals.setEnabled(False)
            self._bvecs.setEnabled(False)
            # noinspection PyInconsistentReturns
            self._save.setEnabled(False)
        else: raise AttributeError('No DWI volume or b-values or b-vectors.')
