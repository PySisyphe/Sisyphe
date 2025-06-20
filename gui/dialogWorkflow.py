"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import rename
from os import chdir

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import splitext
from os.path import join
from os.path import abspath

from shutil import copyfile

from xml.dom import minidom

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import getUserPySisyphePath
from Sisyphe.core.sisypheConstants import addPrefixToFilename
from Sisyphe.core.sisypheConstants import addSuffixToFilename
from Sisyphe.core.sisypheConstants import addPrefixSuffixToFilename
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['WorkflowItem',
           'DialogWorkflow']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogWorkflow
"""

class WorkflowItem(QWidget):
    """
    WorkflowItem

    Inheritance
    ~~~~~~~~~~~

    QWidget -> WorkflowItem

    Creation: 13/02/2025
    Last revision: 17/02/2025
    """

    # Special method

    def __init__(self, name: str, last: int = 0, parent=None):
        super().__init__(parent)

        self._dialog = None
        self._last: int = 0
        self._old: str = ''

        self._process = QLabel(self)
        self._process.setText(name)
        self._input1 = QSpinBox(self)
        self._input1.setFixedWidth(60)
        self._input1.setAlignment(Qt.AlignCenter)
        self._input1.setPrefix('img')
        self._input1.setWrapping(True)
        self._input1.setMinimum(0)
        self._input1.setVisible(False)
        self._input2 = QSpinBox(self)
        self._input2.setFixedWidth(60)
        self._input2.setAlignment(Qt.AlignCenter)
        self._input2.setPrefix('img')
        self._input2.setWrapping(True)
        self._input2.setMinimum(0)
        self._input2.setVisible(False)
        self._edit = QLineEdit(self)
        self._edit.setReadOnly(True)
        self._outputs = QLabel(self)
        self.init(last)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 5, 5, 5)
        lyout.setSpacing(5)
        lyout.addWidget(self._process)
        lyout.addWidget(self._input1)
        lyout.addWidget(self._input2)
        lyout.addWidget(self._edit)
        lyout.addWidget(self._outputs)
        self.setLayout(lyout)

    # Public methods

    def init(self, last: int | None = None):
        if last is None: last = self._last
        else: self._last = last
        self._input1.setMaximum(last)
        self._input2.setMaximum(last)
        name = self.getName()
        if name == 'load':
            self._input1.setVisible(False)
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} loaded'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFileSelection import DialogFileSelection
                self._dialog = DialogFileSelection(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                self._dialog.setTextLabel('Volume')
                self._dialog.filterSisypheVolume()
            self._edit.setText(basename(self._dialog.getFilename()))
        elif name == 'flip':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} axes flipped'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFlipAxes import DialogFlipAxes
                self._dialog = DialogFlipAxes(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._ok.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'swap':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} axes swapped'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogSwapAxes import DialogSwapAxes
                self._dialog = DialogSwapAxes(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._ok.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'remove':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} neck removed'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogRemoveNeckSlices
                self._dialog = DialogRemoveNeckSlices(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'texture':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            if self._dialog is None:
                from Sisyphe.gui.dialogTexture import DialogTexture
                self._dialog = DialogTexture(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            if len(params) > 0:
                c = 0
                buff1 = ''
                buff2 = ''
                for k1 in params:
                    if k1 != 'Radius':
                        for k2 in params[k1]:
                            c += 1
                            buff1 += 'img{} '.format(last + c)
                            buff2 += 'img{} {} {}\n'.format(last + c, k1, k2)
                self._outputs.setText(buff1)
                self._outputs.setToolTip('Output(s):\n{}'.format(buff2))
            else: self._outputs.setText('No output')
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'mean':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} mean filtered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogMeanFilter
                self._dialog = DialogMeanFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'median':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} median filtered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogMedianFilter
                self._dialog = DialogMedianFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'gaussian':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} smoothed'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogGaussianFilter
                self._dialog = DialogGaussianFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'gradient':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} gradient'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogGradientFilter
                self._dialog = DialogGradientFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'laplacian':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} laplacian'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogLaplacianFilter
                self._dialog = DialogLaplacianFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'anisotropic':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} anisotropic diffusion filtered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogAnisotropicDiffusionFilter
                self._dialog = DialogAnisotropicDiffusionFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'bias':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{} img{}'.format(last + 1, last + 2))
            self._outputs.setToolTip('Outputs:\nimg{} bias field corrected\n'
                                     'img{} bias field'.format(last + 1, last + 2))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogBiasFieldCorrectionFilter
                self._dialog = DialogBiasFieldCorrectionFilter(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'histogram':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Reference input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} intensity corrected'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogHistogramIntensityMatching
                self._dialog = DialogHistogramIntensityMatching(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._reference.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'regression':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Reference input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} intensity corrected'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogRegressionIntensityMatching
                self._dialog = DialogRegressionIntensityMatching(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._reference.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'signal':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} intensity normalized'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogFunction import DialogIntensityNormalization
                self._dialog = DialogIntensityNormalization(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'rigid':
            self._input1.setVisible(True)
            self._input1.setToolTip('Moving input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Fixed input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} registered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogRegistration import DialogRegistration
                self._dialog = DialogRegistration(transform='Rigid', parent=self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._fixedSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._movingSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.settingsVisibilityOn()
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._applyTo.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            buff = ['{}: {}'.format(k, str(v)) for k, v in params['registration'].items()]
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['resample'].items()])
            self._edit.setText(' '.join(buff))
            self._edit.setToolTip('\n'.join(buff))
        elif name == 'affine':
            self._input1.setVisible(True)
            self._input1.setToolTip('Moving input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Fixed input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} registered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogRegistration import DialogRegistration
                self._dialog = DialogRegistration(transform='Affine', parent=self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._fixedSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._movingSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.settingsVisibilityOn()
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._applyTo.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            buff = ['{}: {}'.format(k, str(v)) for k, v in params['registration'].items()]
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['resample'].items()])
            self._edit.setText(' '.join(buff))
            self._edit.setToolTip('\n'.join(buff))
        elif name == 'displacement':
            self._input1.setVisible(True)
            self._input1.setToolTip('Moving input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Fixed input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} registered'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogRegistration import DialogRegistration
                self._dialog = DialogRegistration(transform='DisplacementField', parent=self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._fixedSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._movingSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.settingsVisibilityOn()
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._applyTo.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            buff = ['{}: {}'.format(k, str(v)) for k, v in params['registration'].items()]
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['resample'].items()])
            self._edit.setText(' '.join(buff))
            self._edit.setToolTip('\n'.join(buff))
        elif name == 'spatial':
            self._input1.setVisible(True)
            self._input1.setToolTip('Moving input: img{}'.format(self._input1.value()))
            self._input2.setVisible(True)
            self._input2.setToolTip('Fixed input: img{}'.format(self._input2.value()))
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} spatial normalized'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogRegistration import DialogICBMNormalization
                self._dialog = DialogICBMNormalization(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._fixedSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._movingSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.settingsVisibilityOn()
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._applyTo.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            buff = ['{}: {}'.format(k, str(v)) for k, v in params['registration'].items()]
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['resample'].items()])
            self._edit.setText(' '.join(buff))
            self._edit.setToolTip('\n'.join(buff))
        elif name == 'skull':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} skull stripped'.format(last + 1))
            if self._dialog is None:
                from Sisyphe.gui.dialogSkullStripping import DialogSkullStripping
                self._dialog = DialogSkullStripping(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._files.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._ok.setText('OK')
                self._dialog.adjustSize()
            params = self._dialog.getParametersDict()
            self._edit.setText(' '.join(['{}: {}'.format(k, str(v))
                                         for k, v in params.items()]))
            self._edit.setToolTip('\n'.join(['{}: {}'.format(k, str(v))
                                             for k, v in params.items()]))
        elif name == 'prior':
            self._input1.setVisible(True)
            self._input1.setToolTip('Input: img{}'.format(self._input1.value()))
            self._input2.setVisible(False)
            if self._dialog is None:
                from Sisyphe.gui.dialogSegmentation import DialogPriorBasedSegmentation
                self._dialog = DialogPriorBasedSegmentation(self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(self._dialog, c)
                # noinspection PyProtectedMember
                self._dialog._volumeSelect.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._settings.settingsVisibilityOn()
                # noinspection PyProtectedMember
                self._dialog._settings.setButtonsVisibility(False)
                # noinspection PyProtectedMember
                self._dialog._execute.setVisible(False)
                # noinspection PyProtectedMember
                self._dialog._cancel.setText('OK')
            params = self._dialog.getParametersDict()
            n = int(params['segmentation']['NumberOfPriors'][0])
            if n not in [3, 4, 6]: n = 3
            if n == 3:
                names = ['gray matter map',
                         'white matter map',
                         'cerebro-spinal map',
                         'label map']
            elif n == 4:
                names = ['gray matter map',
                         'sub-cortical gray matter map',
                         'white matter map',
                         'cerebro-spinal map',
                         'label map']
            else:
                names = ['gray matter map',
                         'sub-cortical gray matter map',
                         'white matter map',
                         'cerebro-spinal map',
                         'brainstem map',
                         'cerebellum map',
                         'label map']
            buff1 = ''
            buff2 = ''
            for i in range(n):
                buff1 += 'img{} '.format(last + i + 1)
                buff2 += 'img{} {}\n'.format(last + i + 1, names[i])
            self._outputs.setText(buff1)
            self._outputs.setToolTip('Outputs:\n{}'.format(buff2))
            buff = ['{}: {}'.format(k, str(v)) for k, v in params['segmentation'].items()]
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['filter'].items()])
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['biasfield'].items()])
            buff.extend(['{}: {}'.format(k, str(v)) for k, v in params['resample'].items()])
            self._edit.setText(' '.join(buff))
            self._edit.setToolTip('\n'.join(buff))
        elif name == 'algebra':
            self._input1.setVisible(False)
            self._input2.setVisible(False)
            self._edit.setReadOnly(False)
            self._edit.setToolTip('All functions and operators of the Numpy library can be used in formula.\n'
                                  'All Numpy functions must be prefixed with \'np.\' (numpy is imported with the alias np)\n'
                                  'Volume number i is inserted into the formula using a list variable named img: img[i].')
            self._outputs.setText('img{}'.format(last + 1))
            self._outputs.setToolTip('Output:\nimg{} algebra result map'.format(last + 1))
        self._input1.setReadOnly(last == 0)
        self._input2.setReadOnly(last == 0)

    def getName(self) -> str:
        return self._process.text().lower().split(' ')[0]

    def getLongName(self) -> str:
        return self._process.text()

    def editParameters(self):
        if self._dialog is not None:
            self._dialog.exec()
            self.init()

    def getEdit(self):
        return self._edit.text()

    def setEdit(self, text: str):
        self._edit.setText(text)

    def getInputCount(self) -> int:
        r = 0
        if self._input1.isVisible(): r += 1
        if self._input2.isVisible(): r += 2
        return r

    def getInput1Index(self) -> int:
        return self._input1.value()

    def getInput2Index(self) -> int:
        return self._input2.value()

    def setInput1Index(self, index: int):
        self._input1.setValue(index)

    def setInput2Index(self, index: int):
        self._input2.setValue(index)

    def getDialog(self):
        return self._dialog

    def getOutputCount(self) -> int:
        if self._outputs.text() == '': return 0
        else: return len(self._outputs.text().split(' '))

    def getOutputFilenames(self) -> list[str]:
        r = list()
        name = self.getName()
        params = self._dialog.getParametersDict()
        if name == 'load':
            r.append(self._dialog.getFilename())
        elif name in ['flip', 'swap']:
            # old = self._dialog.getFilenames()[0]
            prefix = params['Prefix']
            r.append(addPrefixToFilename(self._old, prefix))
        elif name == 'bias':
            # old = self._dialog.getFilenames()[0]
            prefix = params['Prefix']
            suffix = params['Suffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
            prefix = params['BiasFieldPrefix']
            suffix = params['BiasFieldSuffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
        elif name == 'spatial':
            # old = self._dialog.getMoving()
            prefix = params['resample']['NormalizationPrefix']
            suffix = params['resample']['NormalizationSuffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
        elif name in ['rigid', 'affine', 'displacement']:
            # old = self._dialog.getMoving()
            prefix = params['resample']['Prefix']
            suffix = params['resample']['Suffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
        elif name == 'prior':
            # old = self._dialog.getFilenames()[0]
            n = int(params['segmentation']['NumberOfPriors'][0])
            if n == 3:
                r.append(addPrefixToFilename(self._old, 'gm'))
                r.append(addPrefixToFilename(self._old, 'wm'))
                r.append(addPrefixToFilename(self._old, 'csf'))
            elif n > 3:
                r.append(addPrefixToFilename(self._old, 'gm'))
                r.append(addPrefixToFilename(self._old, 'scgm'))
                r.append(addPrefixToFilename(self._old, 'wm'))
                r.append(addPrefixToFilename(self._old, 'csf'))
                if n == 6:
                    r.append(addPrefixToFilename(self._old, 'bstem'))
                    r.append(addPrefixToFilename(self._old, 'crbl'))
            prefix = params['SegPrefix']
            suffix = params['SegSuffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
        elif name == 'texture':
            # old = self._dialog.getFilenames()[0]
            for k in list(params.keys()):
                prefix = '{}_{}'.format(k[0], k[1])
                r.append(addPrefixToFilename(self._old, prefix))
        else:
            # old = self._dialog.getFilenames()[0]
            prefix = params['Prefix']
            suffix = params['Suffix']
            r.append(addPrefixSuffixToFilename(self._old, prefix, suffix))
        return r

    def setFilenames(self, input1: str, input2: str | None):
        name = self.getName()
        if name in ['histogram', 'regression']:
            self._dialog.setFilenames(input1)
            self._dialog.setReference(input2)
        elif name in ['rigid', 'affine', 'displacement', 'spatial']:
            self._dialog.setMoving(input1)
            self._dialog.setFixed(input2)
        else:
            self._dialog.setFilenames(input1)
        self._old = input1


class DialogWorkflow(QDialog):
    """
    DialogWorkflow

    Description
    ~~~~~~~~~~~

    GUI dialog window for automating a processing workflow.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogWorkflow

    Creation: 13/02/2025
    Last revision: 19/06/2025
    """

    # Class constants

    _PROC = ('Load',
             'Flip axes',
             'Swap axes',
             'Remove neck',
             'Texture feature',
             'Mean filter',
             'Median filter',
             'Gaussian filter',
             'Gradient filter',
             'Laplacian filter',
             'Anisotropic diffusion filter',
             'Bias field correction',
             'Histogram intensity matching',
             'Regression intensity matching',
             'Signal normalization',
             'Rigid registration',
             'Affine registration',
             'Displacement field registration',
             'Spatial normalization',
             'Skull striping',
             'Prior based segmentation',
             'Algebra')

    _FILEEXT = '.xwflow'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe workflow (*{})'.format(cls._FILEEXT)

    # Special method

    """
    Private attributes

    _name       str, current workflow name
    _files      FilesSelectionWidget
    _worklist   QListWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Workflow processing')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._name = 'workflow'

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget(parent=self)
        self._files.setTextLabel('Volume(s) as img0')
        self._files.filterSisypheVolume()
        self._layout.addWidget(self._files)

        self._worklist = QListWidget(self)
        self._worklist.setAlternatingRowColors(True)
        self._worklist.setSelectionMode(1)  # single selection
        # noinspection PyUnresolvedReferences
        self._worklist.itemDoubleClicked.connect(self._editParameters)
        self._layout.addWidget(self._worklist)

        lyout = QHBoxLayout(self)
        lyout.setSpacing(5)
        self._process = QComboBox(self)
        for item in self._PROC:
            self._process.addItem(item.capitalize())
        self._add = QPushButton('Add')
        self._add.setToolTip('Add a processing to the workflow.')
        # noinspection PyUnresolvedReferences
        self._add.clicked.connect(self._addProcessing)
        self._insert = QPushButton('Insert')
        self._insert.setToolTip('Insert a processing to the workflow before selected stage.')
        # noinspection PyUnresolvedReferences
        self._insert.clicked.connect(self._insertProcessing)
        self._remove = QPushButton('Remove')
        self._remove.setToolTip('Remove selected processing from the workflow.')
        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self._removeProcessing)
        self._clear = QPushButton('Clear')
        self._clear.setToolTip('Clear workflow.')
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(lambda: self._worklist.clear())
        self._params = QPushButton('Edit')
        self._params.setToolTip('Edit parameters of the selected processing.')
        # noinspection PyUnresolvedReferences
        self._params.clicked.connect(lambda _: self._editParameters())
        self._save = QPushButton('Save')
        self._save.setToolTip('Save workflow.')
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.save)
        self._open = QPushButton('Open')
        self._open.setToolTip('Open workflow.')
        # noinspection PyUnresolvedReferences
        self._open.clicked.connect(lambda: self.load())
        lyout.addWidget(self._process)
        lyout.addWidget(self._add)
        lyout.addWidget(self._insert)
        lyout.addWidget(self._params)
        lyout.addWidget(self._remove)
        lyout.addWidget(self._clear)
        lyout.addWidget(self._open)
        lyout.addWidget(self._save)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute workflow.')
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()

        self._layout.addLayout(lyout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        # < Revision 13/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._files.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 13/06/2025 >
        self.setModal(True)

    # Private methods

    def _updateIndices(self):
        n = self._worklist.count()
        if n > 0:
            last = 0
            for i in range(n):
                w = self._worklist.itemWidget(self._worklist.item(i))
                w.init(last)
                last += w.getOutputCount()

    def _editParameters(self, item: QListWidgetItem | None = None):
        if item is None:
            item = self._worklist.selectedItems()
            if len(item) > 0: item = item[0]
            else: item = None
        if item is not None:
            w = self._worklist.itemWidget(item)
            w.editParameters()

    def _addProcessing(self):
        last = self._getVolumeCount()
        w = WorkflowItem(self._process.currentText(), last)
        item = QListWidgetItem()
        item.setSizeHint(w.sizeHint())
        self._worklist.addItem(item)
        self._worklist.setItemWidget(item, w)

    def _insertProcessing(self):
        pitem = self._worklist.selectedItems()
        if len(pitem) > 0:
            pitem = pitem[0]
            row = self._worklist.row(pitem)
            last = self._getVolumeCount(row)
            w = WorkflowItem(self._process.currentText(), last)
            item = QListWidgetItem()
            item.setSizeHint(w.sizeHint())
            self._worklist.insertItem(row, item)
            self._worklist.setItemWidget(item, w)
            self._updateIndices()

    def _removeProcessing(self):
        item = self._worklist.selectedItems()
        if len(item) > 0:
            item = item[0]
            self._worklist.removeItemWidget(item)
            self._worklist.takeItem(self._worklist.row(item))
            self._updateIndices()

    def _getVolumeCount(self, row: int | None = None) -> int:
        r = 0
        n = self._worklist.count()
        if row is None: row = n
        else:
            if row > n: row = n
            elif row < 0: row = 0
        if row > 0:
            for i in range(row):
                w = self._worklist.itemWidget(self._worklist.item(i))
                r += w.getOutputCount()
        return r

    # Public methods

    def save(self):
        if self._worklist.count() > 0:
            path = join(getUserPySisyphePath(), 'workflows')
            filename = QFileDialog.getSaveFileName(self, 'Save workflow', path,
                                                   filter=self.getFilterExt())[0]
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                self._name = splitext(basename(filename))[0]
                doc = minidom.Document()
                root = doc.createElement(self._FILEEXT[1:])
                root.setAttribute('version', '1.0')
                doc.appendChild(root)
                for i in range(self._worklist.count()):
                    w = self._worklist.itemWidget(self._worklist.item(i))
                    procname = w.getName()
                    node = doc.createElement(procname)
                    root.appendChild(node)
                    if procname in ['load', 'algebra']:
                        txt = doc.createTextNode(w.getEdit())
                        node.appendChild(txt)
                    else:
                        # write input attributes
                        input1 = str(w.getInput1Index())
                        attr = doc.createAttribute('input1')
                        node.setAttributeNode(attr)
                        node.setAttribute('input1', input1)
                        input2 = str(w.getInput2Index())
                        attr = doc.createAttribute('input2')
                        node.setAttributeNode(attr)
                        node.setAttribute('input2', input2)
                        procdict = w.getDialog().getParametersDict()
                        # write parameter subnodes
                        for k in procdict.keys():
                            subnode = doc.createElement(k)
                            node.appendChild(subnode)
                            if isinstance(procdict[k], dict):
                                for k2 in procdict[k].keys():
                                    subnode2 = doc.createElement(k2)
                                    subnode.appendChild(subnode2)
                                    if isinstance(procdict[k][k2], list): buff = str(procdict[k][k2][0])
                                    else: buff = str(procdict[k][k2])
                                    txt = doc.createTextNode(buff)
                                    subnode2.appendChild(txt)
                            else:
                                if isinstance(procdict[k], list): buff = str(procdict[k][0])
                                else: buff = str(procdict[k])
                                txt = doc.createTextNode(buff)
                                subnode.appendChild(txt)
                buffxml = doc.toprettyxml()
                with open(filename, 'w') as f:
                    f.write(buffxml)
        else: messageBox(self,
                         title=self.windowTitle(),
                         text='Workflow is empty.',
                         icon=QMessageBox.Information)

    def load(self, filename: str = ''):
        if filename == '':
            path = join(getUserPySisyphePath(), 'workflows')
            filename = QFileDialog.getOpenFileName(self, 'Open workflow...', path,
                                                   filter=self.getFilterExt())[0]
        else: filename = splitext(filename)[0] + self._FILEEXT
        if filename and exists(filename):
            filename = abspath(filename)
            chdir(dirname(filename))
            self._worklist.clear()
            self._name = splitext(basename(filename))[0]
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                flow = doc.getElementsByTagName('xwflow')[0]
                for node in flow.childNodes:
                    if node.nodeType == node.ELEMENT_NODE:
                        # add processing
                        last = self._getVolumeCount()
                        w = WorkflowItem(node.nodeName)
                        item = QListWidgetItem()
                        item.setSizeHint(w.sizeHint())
                        self._worklist.addItem(item)
                        self._worklist.setItemWidget(item, w)
                        # read processing parameters
                        if node.nodeName in ['load', 'algebra']:
                            w.setEdit(node.firstChild.data)
                        else:
                            # read parameter subnodes
                            params = dict()
                            childnode = node.firstChild
                            while childnode:
                                if childnode.hasChildNodes():
                                    if len(childnode.childNodes) > 1:
                                        params[childnode.nodeName] = dict()
                                        childnode2 = childnode.firstChild
                                        while childnode2:
                                            if childnode2.nodeType == node.ELEMENT_NODE:
                                                if childnode2.hasChildNodes():
                                                    if childnode2.firstChild.nodeType == node.TEXT_NODE:
                                                        params[childnode.nodeName][childnode2.nodeName] = childnode2.firstChild.data
                                            childnode2 = childnode2.nextSibling
                                    else:
                                        if childnode.firstChild.nodeType == node.TEXT_NODE:
                                            params[childnode.nodeName] = childnode.firstChild.data
                                childnode = childnode.nextSibling
                            w.getDialog().setParametersFromDict(params)
                            w.init(last)
                            # read input attributes
                            if node.hasAttributes():
                                input1 = node.getAttribute('input1')
                                input2 = node.getAttribute('input2')
                                w.setInput1Index(int(input1))
                                w.setInput2Index(int(input2))
            else: messageBox(self, title=self.windowTitle(), text='XML file format is not supported.')

    def execute(self):
        n = self._worklist.count()
        if not self._files.isEmpty() and n > 0:
            for filename in self._files.getFilenames():
                nv = 0
                for i in range(n):
                    w = self._worklist.itemWidget(self._worklist.item(i))
                    dialog = w.getDialog()
                    # < Revision 19/06/2025
                    # bug fix
                    # name = self.getName()
                    name = w.getName()
                    # Revision 19/06/2025 >
                    if name == 'load':
                        wait = DialogWait()
                        wait.setInformationText('Load {}...'.format(basename(dialog.getFilename())))
                        nv += 1
                        try:
                            copyfile(dialog.getFilename(), dirname(filename))
                            src = join(dirname(filename), dialog.getFilename())
                            dst = addSuffixToFilename(filename, '#{}'.format(nv))
                            rename(src, dst)
                        except Exception as err:
                            wait.close()
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='Load stage#{} error.\n{}'.format(i, err))
                            self._files.clear()
                            return
                        wait.close()
                    elif name == 'algebra':
                        f = w.getEdit()
                        if f != '':
                            wait = DialogWait()
                            wait.setInformationText('Algebra processing...')
                            # Open input(s)
                            img = dict()
                            f2 = f.translate({91: None, 93: 32})
                            f2 = f2.split(' ')
                            for sub in f2:
                                n = sub.find('img')
                                if n > -1:
                                    vi = int(sub[n:])
                                    v = SisypheVolume()
                                    if vi == 0: input1 = filename
                                    else: input1 = addSuffixToFilename(filename, '#{}'.format(vi))
                                    if exists(input1): v.load(input1)
                                    else:
                                        wait.close()
                                        messageBox(self,
                                                   title=self.windowTitle(),
                                                   text='Algebra stage#{} input error.\n'
                                                        '{} does not exist.'.format(i, input1))
                                        self._files.clear()
                                        return
                                    img[vi] = v.copyToNumpyArray()
                            if len(img) > 0:
                                # Processing
                                f = 'import numpy as np\nr = ' + f
                                try: exec(f)
                                except Exception as err:
                                    wait.close()
                                    messageBox(self,
                                               title=self.windowTitle(),
                                               text='Algebra stage#{} formula error.\n{}'.format(i, err))
                                    self._files.clear()
                                    return
                                result = locals()['r']
                                v = SisypheVolume()
                                # noinspection PyUnboundLocalVariable
                                v.copyFromNumpyArray(result, spacing=v.getSpacing())
                                v.copyAttributesFrom(v, display=False)
                                nv += 1
                                dst = addSuffixToFilename(filename, '#{}'.format(nv))
                                v.setFilename(dst)
                                v.save()
                            else:
                                wait.close()
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Algebra stage#{} formula error.\n'
                                                'No img in formula.'.format(i))
                                self._files.clear()
                                return
                    else:
                        # Set input(s)
                        n1 = w.getInput1Index()
                        n2 = w.getInput2Index()
                        if n1 == 0: input1 = filename
                        else: input1 = addSuffixToFilename(filename, '#{}'.format(n1))
                        if not exists(input1):
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} stage#{} input error.\n'
                                            '{} does not exist.'.format(w.getLongName(), i, input1))
                            self._files.clear()
                            return
                        if n2 == 0: input2 = filename
                        else: input2 = addSuffixToFilename(filename, '#{}'.format(n2))
                        if not exists(input2):
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} stage#{} input error.\n'
                                            '{} does not exist.'.format(w.getLongName(), i, input2))
                            self._files.clear()
                            return
                        if name in ['histogram', 'regression']:
                            # dialog.setFilenames(input1)
                            # dialog.setReference(input2)
                            w.setFilenames(input1, input2)
                        elif name in ['rigid', 'affine', 'displacement', 'spatial']:
                            # dialog.setMoving(input1)
                            # dialog.setFixed(input2)
                            w.setFilenames(input1, input2)
                        else:
                            # dialog.setFilenames(input1)
                            w.setFilenames(input1, None)
                        # Processing
                        try: dialog.execute()
                        except Exception as err:
                            messageBox(self,
                                       title=self.windowTitle(),
                                       text='{} stage#{} error.\n{}'.format(w.getLongName(), i, err))
                            self._files.clear()
                            return
                        # Rename output(s)
                        output = w.getOutputFilenames()
                        no = len(output)
                        if no > 0:
                            try:
                                for j in range(no):
                                    nv += 1
                                    if i == n - 1 and j == 0: dst = addPrefixToFilename(filename, self._name)
                                    else: dst = addSuffixToFilename(filename, '#{}'.format(nv))
                                    rename(output[j], dst)
                            except Exception as err:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Save output(s) stage#{} error.\n{}'.format(i, err))
                                self._files.clear()
                                return
            """
            Exit  
            """
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Would you like to continue\nwith the workflow processing ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._files.clear()
            else: self.accept()