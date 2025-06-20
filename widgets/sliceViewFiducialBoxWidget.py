"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu

# noinspection PyCompatibility
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget

__all__ = ['SliceViewFiducialBoxWidget',
           'IconBarSliceViewFiducialBoxWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QFrame -> AbstractViewWidget -> SliceViewWidget -> SliceViewFiducialBoxWidget
    - QWidget -> IconBarWidget -> IconBarSliceViewWidget -> IconBarSliceViewFiducialBoxWidget

Description
~~~~~~~~~~~

Class to display single slice with fiducial markers.   
"""


class SliceViewFiducialBoxWidget(SliceViewWidget):
    """
    SliceViewFiducialBoxWidget class

    Description
    ~~~~~~~~~~~

    SliceViewWidget with fiducial marker management.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceViewFiducialBoxWidget

    Last revision: 21/05/2025
    """

    # Special method

    """
    Private attributes

    _fid    SisypheFiducialBox
    """

    def __init__(self, fid: SisypheFiducialBox, parent=None):
        super().__init__(parent)

        self._dz = 0.0
        if isinstance(fid, SisypheFiducialBox):
            self._fid = fid
            # self._volume = fid.getVolume()
        else: raise ValueError('No SisypheFiducialBox.')
        self._dialog = None
        for i in range(10):
            self.addTarget(p=[0, 0, 0], name='', signal=False)
            tool = self.getTool(i)
            tool.setText('#{}'.format(i))
            tool.setSphereVisibility(False)
            tool.setLineWidth(2.0)
            tool.setOpacity(0.5)

    # Private method

    def _getFocalDepth(self):
        camera = self.getCamera()
        return camera.GetFocalPoint()[2]

    def _updateDisplayedMarkers(self):
        if not self._fid.isEmpty():
            sz = self._volume.getSpacing()[2]
            z = round(self._getFocalDepth() // sz)
            errors = self._fid.getErrors()
            for i in range(self._fid.getMarkersCount()):
                tool = self.getTool(i)
                if z in self._fid:
                    p = self._fid.getMarker(z, i)
                    p = [p[0], p[1], self._getFocalDepth() + self._dz]
                    if errors is not None: tool.setText('#{}\n{:.2f}'.format(i, errors[z][i]))
                    tool.setPosition(p)
                    tool.setVisibility(True)
                else: tool.setVisibility(False)

    def _updateMarkersFromDisplay(self):
        if not self._fid.isEmpty():
            sz = self._volume.getSpacing()[2]
            z = round(self._getFocalDepth() // sz)
            if z in self._fid:
                for i in range(self._fid.getMarkersCount()):
                    tool = self.getTool(i)
                    p = tool.getPosition()
                    self._fid[z, i] = (p[0], p[1])

    # Public methods

    def frameDetection(self) -> bool | None:
        if self.hasVolume():
            wait = DialogWait(title='Stereotactic frame detection', progress=True)
            self._fid.ProgressTextChanged.connect(wait.setInformationText)
            self._fid.ProgressRangeChanged.connect(wait.setProgressRange)
            self._fid.ProgressValueChanged.connect(wait.setCurrentProgressValue)
            filename = self._volume.getFilename()
            r = False
            if self._fid.hasXML(filename):
                self._fid.loadFromXML(filename)
                r = True
            else:
                if self._fid.markersSearch(self._volume):
                    wait.setInformationText('Geometric transformation calculation...')
                    wait.progressVisibilityOff()
                    self.calcTransform()
                    wait.close()
                    self.showErrorStatistics()
                    r = True
                else:
                    wait.close()
                    messageBox(self, 'Stereotactic frame detection', 'No frame or frame detection failed.')
            self._fid.ProgressTextChanged.disconnect(wait.setInformationText)
            self._fid.ProgressRangeChanged.disconnect(wait.setProgressRange)
            self._fid.ProgressValueChanged.disconnect(wait.setCurrentProgressValue)
            return r
        else: raise AttributeError('No volume.')

    def setVolume(self, volume):
        super().setVolume(volume)
        # < Revision 21/05/2025
        # self._dz = - 0.6 * volume.getSpacing()[2]
        self._dz = - 0.1
        # Revision 21/05/2025 >
        if self._fid.getMarkersCount() == 6:
            self.getTool(6).setVisibility(False)
            self.getTool(7).setVisibility(False)
            self.getTool(8).setVisibility(False)
        else:
            self.getTool(6).setVisibility(True)
            self.getTool(7).setVisibility(True)
            self.getTool(8).setVisibility(True)
        self._updateDisplayedMarkers()

    def sliceMinus(self):
        self._updateMarkersFromDisplay()
        super().sliceMinus()
        self._updateDisplayedMarkers()

    def slicePlus(self):
        self._updateMarkersFromDisplay()
        super().slicePlus()
        self._updateDisplayedMarkers()

    def zoomOnMarker(self, n):
        if not self._fid.isEmpty():
            if n < self._fid.getMarkersCount():
                if self.getZoom() != 10.0: self._scale = self.getZoom()
                f = list(self.getCamera().GetFocalPoint())
                p = self._fid.getMarker(int(f[2]), n)
                f[0], f[1] = p[0], p[1]
                self.setCameraPlanePosition(f)
                self.setZoom(10.0)

    def zoomDefault(self):
        super().zoomDefault()
        if self.hasVolume():
            p = self._volume.getCenter()
            f = list(self.getCamera().GetFocalPoint())
            f[0], f[1] = p[0], p[1]
            self.setCameraPlanePosition(f)

    def calcTransform(self):
        if not self._fid.isEmpty():
            self._fid.calcTransform()
            self._fid.calcErrors()

    def addTransformToVolume(self):
        if not self._fid.isEmpty():
            self._fid.addTransformToVolume()

    def removeTransformFromVolume(self):
        if not self._fid.isEmpty():
            self._fid.removeTransformFromVolume()

    def showErrorStatistics(self):
        if self._fid.hasErrors():
            self._dialog = DialogGenericResults()
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(self._dialog, c)
            self._dialog.setWindowTitle('Stereotactic frame detection accuracy')
            self._dialog.newTab('Global error')
            self._dialog.newTab('Errors')
            fig0 = self._dialog.getFigure(0)
            fig1 = self._dialog.getFigure(1)
            # Global error
            data = list()
            errors = self._fid.getErrors()
            for k in errors:
                for i in range(self._fid.getMarkersCount()):
                    data.append(errors[k][i])
            ax = fig0.add_subplot(111)
            ax.boxplot(data, vert=True, patch_artist=True, showfliers=False)
            ax.yaxis.grid(True)
            ax.set_xlabel('All fiducial markers')
            ax.set_ylabel('Error values (mm)')
            stats = self._fid.getErrorStatistics().copy()
            for k in stats:
                # noinspection PyTypeChecker
                stats[k] = [stats[k]]
            self._dialog.setTreeWidgetDict(0, stats)
            # Errors
            ax = fig1.add_subplot(111)
            ax.yaxis.grid(True)
            ax.set_xlabel('Slice numbers (bottom to top)')
            ax.set_ylabel('Error values')
            data = dict()
            xdata = list()
            for i in range(self._fid.getMarkersCount()): data[i] = list()
            for k in errors:
                xdata.append(k)
                for i in range(self._fid.getMarkersCount()):
                    data[i].append(errors[k][i])
            lbls = ['left posterior',
                    'left middle',
                    'left anterior',
                    'right anterior',
                    'right middle',
                    'right posterior',
                    'anterior right',
                    'anterior middle',
                    'anterior left']
            for i in range(self._fid.getMarkersCount()):
                ax.plot(xdata, data[i], label='Marker#{} ({})'.format(i, lbls[i]))
            ax.legend()
            self._dialog.setTreeWidgetDict(1, data)
            self._dialog.exec()

    def getFiducialBoxDict(self):
        return self._fid

    def removeCurrentSliceMarkers(self):
        if not self._fid.isEmpty():
            sz = self._volume.getSpacing()[2]
            z = round(self._getFocalDepth() // sz)
            self._fid.removeSliceMarkers(z)
            self._updateDisplayedMarkers()
            self.updateRender()

    def removeFrontPlateMarkers(self):
        if not self._fid.isEmpty():
            if self._fid.getMarkersCount() == 9:
                self._fid.removeFrontPlateMarkers()
                self._updateDisplayedMarkers()
                self.updateRender()


class IconBarSliceViewFiducialBoxWidget(IconBarWidget):
    """
    IconBarSliceViewWidget

    Description
    ~~~~~~~~~~~

    SliceViewFiducialBoxWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarSliceViewFiducialBoxWidget
    """

    def __init__(self, fid: SisypheFiducialBox, parent=None):
        super().__init__(parent)

        self._markermenu = QMenu()
        # noinspection PyTypeChecker
        self._markermenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._markermenu.setWindowFlag(Qt.FramelessWindowHint, True)
        self._markermenu.setAttribute(Qt.WA_TranslucentBackground, True)

        if isinstance(fid, SisypheFiducialBox):
            widget = SliceViewFiducialBoxWidget(fid, parent=self)
            self._setViewWidget(widget)
            if fid.hasVolume(): self.setVolume(fid.getVolume())
        else: raise ValueError('No SisypheFiducialBox.')

        self.setShowButtonAvailability(False)
        self.setInfoButtonAvailability(False)
        self.setActionButtonAvailability(False)
        self.setIsoButtonAvailability(False)
        self.setColorbarButtonAvailability(False)
        self.setRulerButtonAvailability(False)
        self.setToolButtonAvailability(False)

        # Inherited methods from SliceViewFiducialBoxWidget class

        setattr(self, 'calcTransform', self._widget.calcTransform)
        setattr(self, 'addTransformToVolume', self._widget.addTransformToVolume)
        setattr(self, 'removeTransformFromVolume', self._widget.removeTransformFromVolume)
        setattr(self, 'showErrorStatistics', self._widget.showErrorStatistics)
        setattr(self, 'removeCurrentSliceMarkers', self._widget.removeCurrentSliceMarkers)
        setattr(self, 'removeFrontPlateMarkers', self._widget.removeFrontPlateMarkers)

    # Private methods

    def _onMenuTools(self, action):
        s = str(action.text())[0]
        w = self.getViewWidget()
        if w is not None:
            if s == 'D': w.addDistanceTool()
            elif s == 'O': w.addOrthogonalDistanceTool()
            else: w.addAngleTool()

    def _setViewWidget(self, widget):
        if isinstance(widget, SliceViewFiducialBoxWidget):
            self._widget = widget
            self._layout.addWidget(widget)
            widget.setSelectable(False)
            self.setExpandButtonAvailability(False)
            self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
            self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
            self._icons['sliceminus'].clicked.connect(widget.sliceMinus)
            self._icons['sliceplus'].clicked.connect(widget.slicePlus)
            self._visibilityflags['sliceminus'] = True
            self._visibilityflags['sliceplus'] = True

            self._icons['zoom'] = self._createButton('wzoomtarget.png', 'zoomtarget.png', checkable=True,
                                                     autorepeat=False)
            self._markermenu.addAction('Marker#0 Left posterior')
            self._markermenu.addAction('Marker#1 Left mid')
            self._markermenu.addAction('Marker#2 Left anterior')
            self._markermenu.addAction('Marker#3 Right anterior')
            self._markermenu.addAction('Marker#4 Right mid')
            self._markermenu.addAction('Marker#5 Right posterior')
            self._markermenu.addAction('Marker#6 Anterior right')
            self._markermenu.addAction('Marker#7 Anterior mid')
            self._markermenu.addAction('Marker#8 Anterior left')
            # noinspection PyUnresolvedReferences
            self._markermenu.triggered.connect(self._onMarkerZoom)
            self._icons['zoom'].setMenu(self._markermenu)

            lyout = self._bar.layout()
            lyout.insertWidget(5, self._icons['zoom'])
            lyout.insertWidget(2, self._icons['sliceplus'])
            lyout.insertWidget(2, self._icons['sliceminus'])

            self._icons['show'].setMenu(widget.getPopupVisibility())
            self._icons['actions'].setMenu(widget.getPopupActions())
            self._icons['colorbar'].setMenu(widget.getPopupColorbarPosition())
            self._icons['zoomin'].clicked.connect(widget.zoomIn)
            self._icons['zoomout'].clicked.connect(widget.zoomOut)
            self._icons['zoom1'].clicked.connect(widget.zoomDefault)
            self._icons['capture'].clicked.connect(widget.saveCapture)
            self._icons['clipboard'].clicked.connect(widget.copyToClipboard)

            self._visibilityflags['zoom'] = True
            self._icons['zoom'].setToolTip('Zoom on fiducial marker.')
        else: raise TypeError('parameter type {} is not SliceViewFiducialBoxWidget.'.format(type(widget)))

    def _onMarkerZoom(self, action):
        n = int(action.text()[7])
        self._widget.zoomOnMarker(n)

    # Public methods

    def setVolume(self, vol):
        super().setVolume(vol)
        self.timerEnabled()
        fid = self._widget.getFiducialBoxDict()
        if fid.getMarkersCount() == 6:
            self._markermenu.actions()[6].setVisible(False)
            self._markermenu.actions()[7].setVisible(False)
            self._markermenu.actions()[8].setVisible(False)
        else:
            self._markermenu.actions()[6].setVisible(True)
            self._markermenu.actions()[7].setVisible(True)
            self._markermenu.actions()[8].setVisible(True)

    def removeVolume(self):
        super().removeVolume()
        self.timerDisabled()

    def timerEvent(self, event):
        w = self._widget
        # Icon bar visibility management
        if not self._icons['pin'].isChecked():
            if self.getIconBarVisibility():
                if not self._bar.underMouse(): self.iconBarVisibleOff()
            else:
                p = w.cursor().pos()
                p = w.mapFromGlobal(p)
                if p.x() < self._icons['pin'].width(): self.iconBarVisibleOn()
        # Mouse move event management
        # solves VTK mouse move event bug
        interactor = w.getWindowInteractor()
        p = w.cursor().pos()
        p = w.mapFromGlobal(p)
        p.setY(w.height() - p.y() - 1)
        interactor.SetEventInformation(p.x(), p.y())
        interactor.MouseMoveEvent()
