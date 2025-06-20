"""
External packages/modules
-------------------------

    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import remove
from os import chdir

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath

from numpy import array
from numpy import ndarray

from matplotlib.figure import Figure
# noinspection PyUnresolvedReferences
from matplotlib.figure import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.lines import Line2D

from pandas import DataFrame

# < Revision 07/03/2025
# from pydicom import read_file
from pydicom import dcmread as read_file

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheConstants import addSuffixToFilename
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.processing.dscFunctions import getArterialInputVoxels
from Sisyphe.processing.dscFunctions import dscMaps
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.iconBarViewWidgets import IconBarSliceViewWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.gui.dialogFunction import AbstractDialogFunction

__all__ = ['DialogPerfusion',
           'DialogArterialInputFunction']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> AbstractDialogFunction -> DialogPerfusion
              -> DialogArterialInputFunction
"""

class DialogPerfusion(AbstractDialogFunction):
    """
    DialogPerfusion class

    Description
    ~~~~~~~~~~~

    Dialog to process MR perfusion maps.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> AbstractDialogFunction -> DialogPerfusion

    Creation: 23/12/2024
    Last revision:
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__('Perfusion', parent)
        self._settings.settingsVisibilityOn()

        # Init window

        self.setWindowTitle('DSC-MR perfusion analysis')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._files.filterMultiComponent()
        self._files.filterSameSequence(SisypheAcquisition.PWI)
        self._files.FieldChanged.connect(self._filesChanged)
        self._files.setTextLabel('DSC-MR multi-component volume(s)')
        self._settings.setButtonsVisibility(False)
        self._settings.getParameterWidget('DCM').hideRemoveButton()
        self._settings.getParameterWidget('DCM').FieldChanged.connect(self._getFromDicom)
        self._settings.getParameterWidget('DSC').clicked.connect(self._dscChanged)
        self._settings.getParameterWidget('Fitting').clicked.connect(self._dscChanged)
        self._dscChanged()

        self._dialogChecked = self._settings.getParameterWidget('Dialog').checkState()

        # < Revision 14/06/2025
        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._files.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        # Revision 14/06/2025 >
        self.setModal(True)

    # Private method

    def _getFromDicom(self):
        widget = self._settings.getParameterWidget('DCM')
        if widget is not None:
            filename = widget.getFilename()
            if exists(filename):
                ext = splitext(filename)[1]
                dcmext = getDicomExt()
                dcmext.append('')
                if ext in dcmext:
                    try: ds = read_file(filename, stop_before_pixels=True)
                    except:
                        messageBox(self, 'Dicom read', 'Invalid dicom file.')
                        return
                    if 'EchoTime' in ds:
                        te = float(ds['EchoTime'].value)
                        widget = self._settings.getParameterWidget('TE')
                        if widget is not None: widget.setValue(te)
                    if 'RepetitionTime' in ds:
                        tr = float(ds['RepetitionTime'].value)
                        widget = self._settings.getParameterWidget('TR')
                        if widget is not None: widget.setValue(tr)
                elif ext == XmlDicom.getFileExt():
                    ds = XmlDicom()
                    try: ds.loadXmlDicomFilename(filename)
                    except:
                        messageBox(self, 'XmlDicom read', 'Invalid XmlDicom file.')
                        return
                    if ds.hasKeyword('EchoTime'):
                        te = float(ds.getDataElementValue('EchoTime'))
                        widget = self._settings.getParameterWidget('TE')
                        if widget is not None: widget.setValue(te)
                    if ds.hasKeyword('RepetitionTime'):
                        tr = float(ds.getDataElementValue('RepetitionTime'))
                        widget = self._settings.getParameterWidget('TR')
                        if widget is not None: widget.setValue(tr)

    def _filesChanged(self):
        if len(self._files.getFilenames()) > 1:
            self._settings.getParameterWidget('Dialog').setCheckState(Qt.Unchecked)
            self._settings.setParameterVisibility('Dialog', False)
        else:
            self._settings.getParameterWidget('Dialog').setCheckState(self._dialogChecked)
            self._settings.setParameterVisibility('Dialog', True)

    def _dscChanged(self):
        c = self._settings.getParameterValue('DSC')
        self._settings.setParameterVisibility('Fitting', c)
        self._settings.setParameterVisibility('Deconvolution', c)
        self._settings.setParameterVisibility('Leakage', c)
        c = self._settings.getParameterValue('Fitting')
        self._settings.setParameterVisibility('Leakage', c)
        if not c:  self._settings.setParameterValue('Leakage', False)
        self._center(None)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def function(self, filename, wait):
        if exists(filename):
            wait.buttonVisibilityOff()
            wait.setInformationText(self.windowTitle() + '...\n{}'.format(basename(filename)))
            n = self._settings.getParameterValue('VoxelCount')
            # TR in s (TR in ms / 1000.0)
            delt = self._settings.getParameterValue('TR') / 1000.0
            # TE in s (TE in ms / 1000.0)
            te = self._settings.getParameterValue('TE') / 1000.0
            masking = self._settings.getParameterValue('Masking')[0]
            baseline = tuple(self._settings.getParameterValue('Baseline'))
            smooth = self._settings.getParameterValue('Smoothing')
            recovery = self._settings.getParameterValue('Recovery')
            dsc = self._settings.getParameterValue('DSC')
            fit = self._settings.getParameterValue('Fitting')
            deconvolve = self._settings.getParameterValue('Deconvolution')
            leakage = self._settings.getParameterValue('Leakage')
            vols = SisypheVolume()
            vols.load(filename)
            mask = vols.getMask(algo=masking, kernel=2, morpho='open', fill='2d', c=0)
            if self._settings.getParameterWidget('Dialog').checkState() == Qt.Checked:
                dialog = DialogArterialInputFunction(parent=self)
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.setVolume(vols, mask, n)
                wait.hide()
                if dialog.exec() == QDialog.Accepted:
                    wait.show()
                    aif = dialog.getArterialInputFunction()
                    # noinspection PyTypeChecker
                    r = dscMaps(vols, mask, aif, delt, te, baseline=baseline, recovery=recovery, dsc=dsc,
                                smooth=smooth, fit=fit, deconvolve=deconvolve, leakage=leakage, wait=wait)
                else: return
                dialog.close()
            else:
                roi = getArterialInputVoxels(vols, mask, n)[0].getROI()
                aif = array(vols.getMean(roi, c=None))
                try:
                    # noinspection PyTypeChecker
                    r = dscMaps(vols, mask, aif, delt, te, baseline=baseline, recovery=recovery, dsc=dsc,
                                smooth=smooth, fit=fit, deconvolve=deconvolve, leakage=leakage, wait=wait)
                except Exception as err:
                    wait.close()
                    messageBox(self,
                               title=self.windowTitle(),
                               text='{} error: '
                                    '{}\n{}.'.format(self.windowTitle(), type(err), str(err)))
                    self._files.clear()
                    return
            for k in r:
                wait.setInformationText('Save {}...'.format(r[k].getBasename()))
                r[k].save()
            """
            Exit  
            """
            wait.close()
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to do\nmore DSC-MR perfusion analysis ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._files.clear()
            else: self.accept()


class DialogArterialInputFunction(QDialog):
    """
    DialogArterialInputFunction class

    Description
    ~~~~~~~~~~~

    Dialog to process arterial input function from time series of perfusion weighted images.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogArterialInputFunction

    Creation: 17/12/2024
    Last revision: 08/03/2025
    """

    # Special method

    """
    Private attributes
    
    _fig        Figure
    _canvas     FigureCanvas
    _lines      list[Line2D]
    _aifvx      SisypheVolume, aif voxels labeled by sorting rank
    _roi        SisypheROI, aif ROI
    _volume     SisypheVolume, time series of perfusion weighted images
    _view       IconBarSliceViewWidget
    _scrshot    ScreenshotsGridWidget
    _ok         QPushButton 
    save       QPushButton
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Arterial input function')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        screen = QApplication.primaryScreen().geometry()
        w = int(screen.width() * 0.75)
        self.setMinimumSize(w, int(screen.height() * 0.50))

        # Init non-GUI attributes

        self._volume: SisypheVolume | None = None
        self._aifvx: SisypheVolume | None = None
        self._roi: SisypheROI | None = None
        self._lines: dict[str, Line2D] | None = dict()
        self._scrshot: ScreenshotsGridWidget | None = None

        # Init QLayout

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._view = IconBarSliceViewWidget(parent=self)
        self._view.setMinimumWidth(w // 2)
        self._view.setActionButtonAvailability(False)
        self._view.setColorbarButtonAvailability(False)
        self._view.setInfoButtonAvailability(False)
        self._view.setIsoButtonAvailability(False)
        self._view.setOrientButtonAvailability(False)
        self._view.setRulerButtonAvailability(False)
        self._view.setShowButtonAvailability(False)
        self._view.setToolButtonAvailability(False)
        self._view().synchronisationOn()
        self._view().setCenteredCursorFlag()
        self._view().setCursorVisibility(True)
        self._view().setCursorOpacity(0.25)
        self._view().CursorPositionChanged.connect(self._cursorPositionChanged)

        self._fig = Figure()
        self._axe: Axes | None = None
        self._canvas = FigureCanvas(self._fig)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('pick_event', self._chartClicked)
        widget = QWidget(parent=self)
        widget.setToolTip('Click on the grey curve of the graph to move the slice view\n'
                          'cursor to the voxel associated with that signal variation.')
        lyout = QVBoxLayout()
        lyout.addWidget(self._canvas)
        hlyout = QHBoxLayout()
        hlyout.setSpacing(5)
        button1 = QPushButton('Add')
        button2 = QPushButton('Remove')
        button3 = QPushButton('Clear')
        button4 = QPushButton('Save bitmap')
        button5 = QPushButton('Clipboard')
        button6 = QPushButton('Screenshots')
        button7 = QPushButton('Save ROI')
        button8 = QPushButton('Save Dataset')
        button1.setToolTip('Add current voxel to aif ROI.\n'
                           'The current voxel is the one under the cursor in the slice view.\n'
                           'Its signal variation curve is shown in green in the chart on the right.')
        button2.setToolTip('Remove current voxel from aif ROI.\n'
                           'The current voxel is the one under the cursor in the slice view.\n'
                           'Its signal variation curve is shown in green in the chart on the right.')
        button3.setToolTip('Clear aif ROI.')
        button4.setToolTip('Save chart to bitmap.')
        button5.setToolTip('Copy chart to clipboard.')
        button6.setToolTip('Copy chart to screenshots.')
        button7.setToolTip('Save aif ROI.')
        button8.setToolTip('Save aif dataset.')
        # noinspection PyUnresolvedReferences
        button1.clicked.connect(self._addVoxel)
        # noinspection PyUnresolvedReferences
        button2.clicked.connect(self._removeVoxel)
        # noinspection PyUnresolvedReferences
        button3.clicked.connect(self._clear)
        # noinspection PyUnresolvedReferences
        button4.clicked.connect(self.saveBitmap)
        # noinspection PyUnresolvedReferences
        button5.clicked.connect(self.copyClipboard)
        # noinspection PyUnresolvedReferences
        button6.clicked.connect(self.copyScreenshot)
        # noinspection PyUnresolvedReferences
        button7.clicked.connect(self.saveROI)
        # noinspection PyUnresolvedReferences
        button8.clicked.connect(self.saveDataset)
        hlyout.addWidget(button1)
        hlyout.addWidget(button2)
        hlyout.addWidget(button3)
        hlyout.addWidget(button4)
        hlyout.addWidget(button5)
        hlyout.addWidget(button6)
        hlyout.addWidget(button7)
        hlyout.addWidget(button8)
        hlyout.addStretch()
        lyout.addLayout(hlyout)
        widget.setLayout(lyout)

        spl = QSplitter(self)
        spl.addWidget(self._view)
        spl.addWidget(widget)
        self._layout.addWidget(spl)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        self._cancel = QPushButton('Cancel')
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)
        lyout.addWidget(self._ok)
        lyout.addWidget(self._cancel)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        self.setModal(True)

    # Private methods

    def _chartClicked(self, event) -> None:
        artist = event.artist
        if isinstance(artist, Line2D):
            lb = artist.get_label()
            # noinspection PyUnresolvedReferences
            if lb[0] == 'v':
                # noinspection PyUnresolvedReferences
                r = lb.split(' ')
                if len(r) == 4:
                    spacing = self._volume.getSpacing()
                    x = int(r[1]) * spacing[0]
                    y = int(r[2]) * spacing[1]
                    z = int(r[3]) * spacing[2]
                    self._view().setCursorWorldPosition(x, y, z)

    def _cursorPositionChanged(self):
        if self._axe is not None:
            p = self._view().getCursorArrayPosition()
            ydata = list(self._volume[p[0], p[1], p[2]])
            if 'cursor' in self._lines:
                # noinspection PyTypeChecker
                self._lines['cursor'].set_ydata(ydata)
            else:
                xdata = list(range(len(ydata)))
                self._lines['cursor'], = self._axe.plot(xdata, ydata, 'o-',
                                                        color='g', linewidth=3.0, label='cursor')
            self._axe.legend(handles=[self._lines['mean'], self._lines['aif'], self._lines['cursor']])
            self._canvas.draw()

    def _addVoxel(self):
        p = self._view().getCursorArrayPosition()
        self._roi[p[0], p[1], p[2]] = 1
        self._view().updateRender()
        # add Line2D
        n = self._volume.getNumberOfComponentsPerPixel()
        xdata = list(range(n))
        ydata = self._volume.getNumpy()[:, p[2], p[1], p[0]]
        key = ' '.join([str(v) for v in p])
        self._lines[key], = self._axe.plot(xdata, ydata, 'o-', linewidth=1.0, markersize=0.5,
                                           color='silver', picker=True, pickradius=5,
                                           label='voxel# {}'.format(key))
        self._lines[key].set_visible(True)
        # update aif curve
        curve = self._volume.getMean(self._roi, c=None)
        self._lines['aif'].set_ydata(curve)
        self._lines['aif'].set_visible(True)
        self._canvas.draw()

    def _removeVoxel(self):
        p = self._view().getCursorArrayPosition()
        self._roi[p[0], p[1], p[2]] = 0
        self._view().updateRender()
        # remove Line2D
        key = ' '.join([str(v) for v in p])
        if key in self._lines:
            self._lines[key].remove()
            del self._lines[key]
        # update aif curve
        if not self._roi.isEmptyArray():
            curve = self._volume.getMean(self._roi, c=None)
            self._lines['aif'].set_ydata(curve)
        else: self._lines['aif'].set_visible(False)
        self._canvas.draw()

    def _clear(self):
        # clear aif roi
        self._view().roiClear()
        # clear aif voxel curves
        keys = list(self._lines.keys())
        for k in keys:
            if k not in ('aif', 'mean', 'cursor'):
                self._lines[k].remove()
                del self._lines[k]
        # hide aif curve
        self._lines['aif'].set_visible(False)
        self._canvas.draw()

    # Public methods

    def setScreenshotsGridWidget(self, widget: ScreenshotsGridWidget):
        self._scrshot = widget

    def getScreenshotsGridWidget(self) -> ScreenshotsGridWidget:
        return self._scrshot

    def setVolume(self,
                  vol: SisypheVolume,
                  mask: SisypheVolume | None = None,
                  nv: int = 10) -> None:
        if vol.acquisition.getSequence() == SisypheAcquisition.PWI:
            n = vol.getNumberOfComponentsPerPixel()
            if n > 1:
                if mask is None:
                    mask = vol.getMask(kernel=2, morpho='open', fill='2d', c=0)
                # View update
                self._volume = vol
                self._view.setVolume(self._volume.copyComponent())
                self._view().addOverlay(mask)
                self._aifvx, meancurve = getArterialInputVoxels(self._volume, mask)
                self._roi = self._aifvx.getROI(nv + 1, '0<')
                self._view().addROI(self._roi)
                self._view().updateROIAttributes(signal=True)
                # Figure update
                self._fig.clear()
                self._axe = self._fig.add_subplot(111)
                self._axe.spines['top'].set_visible(False)
                self._axe.spines['right'].set_visible(False)
                xdata = list(range(n))
                # mean curve
                self._lines['mean'], = self._axe.plot(xdata, meancurve, 'o-', linewidth=3.0,
                                                      color='b', label='mean brain curve')
                # aif curve
                aifcurve = self._volume.getMean(self._roi, c=None)
                self._lines['aif'], = self._axe.plot(xdata, aifcurve, '-', linewidth=3.0,
                                                     color='r', label='aif curve')
                self._lines['aif'].set_linewidth(3)
                # cursor position curve
                self._cursorPositionChanged()
                # aif voxel curves
                c = self._roi.toIndexes()
                for ci in c:
                    ydata = self._volume.getNumpy()[:, ci[2], ci[1], ci[0]]
                    key = ' '.join([str(v) for v in ci])
                    self._lines[key], = self._axe.plot(xdata, ydata, 'o-', linewidth=1.0, markersize=0.5,
                                                       color='silver', picker=True, pickradius=5,
                                                       label='voxel# {}'.format(key))
                    # self._lines[key].set_visible(ci == c[0])
                    self._lines[key].set_visible(True)
                self._axe.legend(handles=[self._lines['mean'], self._lines['aif'], self._lines['cursor']])
                self._canvas.draw()
            else: raise ValueError('Single-component volume.')
        else: raise ValueError('Not PWI sequence ({}).'.format(self._volume.acquisition.getSequence()))

    def getArterialInputFunction(self) -> ndarray:
        return array(self._lines['aif'].get_ydata())

    def saveBitmap(self) -> None:
        filename = self._volume.getFilename()
        filename = addSuffixToFilename(filename, 'aif')
        filename = splitext(filename)[0] + '.jpg'
        filename = QFileDialog.getSaveFileName(self, 'Save chart', filename,
                                               filter='BMP (*.bmp);;JPG (*.jpg);;PNG (*.png);;'
                                                      'TIFF (*.tiff);;SVG (*.svg)',
                                               initialFilter='JPG (*.jpg)')[0]
        QApplication.processEvents()
        if filename:
            filename = abspath(filename)
            chdir(dirname(filename))
            try: self._fig.savefig(filename)
            except Exception as err:
                messageBox(self, 'Save chart', text='{}'.format(err))

    def copyClipboard(self) -> None:
        tmp = join(getcwd(), 'tmp.png')
        try:
            self._fig.savefig(tmp)
            img = QPixmap(tmp)
            QApplication.clipboard().setPixmap(img)
        except Exception as err:
            messageBox(self, 'Copy chart to clipboard', text='error: {}'.format(err))
        finally:
            if exists(tmp): remove(tmp)

    def copyScreenshot(self) -> None:
        if self._scrshot is not None:
            self.copyToClipboard()
            self._scrshot.pasteFromClipboard()

    def saveDataset(self):
        n = len(self._lines)
        if n > 0:
            filename = self._volume.getFilename()
            filename = addSuffixToFilename(filename, 'aif')
            filename = splitext(filename)[0] + '.csv'
            filename = QFileDialog.getSaveFileName(self, 'Save ', filename,
                                                   filter='CSV (*.csv);; '
                                                          'JSON (*.json);; '
                                                          'Latex (*.tex);; '
                                                          'Text (*.txt);; '  
                                                          'XLSX (*.xlsx);; '
                                                          'PySisyphe Sheet (*.xsheet)',
                                                   initialFilter='CSV (*.csv)')[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                labels = list()
                lines = list()
                for k in self._lines:
                    labels.append(self._lines[k].get_label())
                    lines.append(self._lines[k].get_ydata())
                lines = array(lines)
                df = DataFrame(lines.T, columns=labels).T
                sheet = SisypheSheet(df)
                ext = splitext(filename)[1][1:]
                try:
                    if ext == 'csv': sheet.saveCSV(filename)
                    elif ext == 'json': sheet.saveJSON(filename)
                    elif ext == 'tex': sheet.saveLATEX(filename)
                    elif ext == 'txt': sheet.saveTXT(filename)
                    elif ext == 'xlsx': sheet.saveXLSX(filename)
                    elif ext == 'xsheet': sheet.save(filename)
                    else: raise ValueError('{} format is not supported.'.format(ext))
                except Exception as err:
                    messageBox(self, 'Save chart dataset', text='error: {}'.format(err))

    def saveROI(self) -> None:
        if self._roi is not None:
            filename = self._volume.getFilename()
            filename = addSuffixToFilename(filename, 'aif')
            filename = splitext(filename)[0] + SisypheROI.getFileExt()
            filename = QFileDialog.getSaveFileName(self, 'Save aif ROI', filename,
                                                   filter=SisypheROI.getFilterExt())[0]
            QApplication.processEvents()
            if filename:
                filename = abspath(filename)
                chdir(dirname(filename))
                try: self._roi.save(filename)
                except Exception as err:
                    messageBox(self, 'Save aif ROI', text='{}'.format(err))

    # Qt events

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            self._view.finalize()
        # Revision 10/03/2025 >
