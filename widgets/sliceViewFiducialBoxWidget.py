"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget

__all__ = ['SliceViewFiducialBoxWidget',
           'IconBarSliceViewFiducialBoxWidget']

"""
    Class hierarchy

        QFrame -> AbstractViewWidget -> SliceViewWidget -> SliceViewFiducialBoxWidget
        QWidget -> IconBarWidget -> IconBarSliceViewWidget -> IconBarSliceViewFiducialBoxWidget

    Description

        Class to display single slice with fiducial markers.   
"""


class SliceViewFiducialBoxWidget(SliceViewWidget):
    """
        SliceViewFiducialBoxWidget class

        Description

            SliceViewWidget with fiducial markers management.

        Inheritance

            QWidget -> AbstractViewWidget -> SliceViewWidget -> SliceViewFiducialBoxWidget

        Private attributes

            _fid    SisypheFiducialBox

        Public methods

            setVolume(SisypheVolume)    override
            sliceMinus()                override
            slicePlus()                 override
            zoomOnMarker(int)
            zoomDefault()               override
            calcTransform()
            addTransformToVolume()
            dict = getFiducialBoxDict()

            inherited SliceViewWidget methods
            inherited AbstractViewWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self._fid = None
        self._dz = 0.0
        self._dialog = None
        for i in range(10):
            self.addTarget(p=[0, 0, 0], name='', signal=False)
            tool = self.getTool(i)
            tool.setText('#{}'.format(i), prefix=False)
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
                    if errors is not None: tool.setText('#{}\n{:.2f}'.format(i, errors[z][i]), prefix=False)
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

    def setVolume(self, volume):
        super().setVolume(volume)
        self._dz = - 0.6 * volume.getSpacing()[2]
        wait = DialogWait(title='Stereotactic frame detection', progress=True, parent=self)
        self._fid = SisypheFiducialBox()
        self._fid.ProgressTextChanged.connect(wait.setInformationText)
        self._fid.ProgressRangeChanged.connect(wait.setProgressRange)
        self._fid.ProgressValueChanged.connect(wait.setCurrentProgressValue)
        filename = volume.getFilename()
        if self._fid.hasXML(filename): self._fid.loadFromXML(filename)
        wait.open()
        try:
            if self._fid.isEmpty(): self._fid.markersSearch(volume)
            else: self._fid.setVolume(volume)
            wait.progressVisibilityOff()
            wait.setInformationText('Geometric transformation calculation...')
            self.calcTransform()
        except Exception as err:
            QMessageBox.warning(self, 'Stereotactic frame detection', 'error: {}'.format(err))
            errors = self._fid.getErrors()
            if errors is not None: errors.clear()
        finally:
            wait.close()
            QApplication.processEvents()
        self.showErrorStatistics()
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

    def showErrorStatistics(self):
        if self._fid.hasErrors():
            self._dialog = DialogGenericResults(self)
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
            ax.set_ylabel('Error values')
            stats = self._fid.getErrorStatistics()
            for k in stats:
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
            for i in range(self._fid.getMarkersCount()):
                ax.plot(xdata, data[i], label='Marker#{}'.format(i))
            ax.legend()
            self._dialog.setTreeWidgetDict(1, data)
            self._dialog.show()

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

            SliceViewFiducialBoxWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarSliceViewFiducialBoxWidget

        Private Attributes

        Public methods

            setVolume(SisypheVolume)    override
            removeVolume()              override
            calcTransform()             inherited SliceViewFiducialBoxWidget
            addTransformToVolume()      inherited SliceViewFiducialBoxWidget
            showErrorStatistics()       inherited SliceViewFiducialBoxWidget
            removeCurrentSliceMarkers() inherited SliceViewFiducialBoxWidget

            inherited IconBarWidget
            inherited QWidget methods
    """

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)

        self._markermenu = QMenu()

        if widget is None: widget = SliceViewFiducialBoxWidget(parent=self)
        if isinstance(widget, SliceViewFiducialBoxWidget): self._setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SliceViewFiducialBoxWidget.'.format(type(widget)))

        # Inherited methods from SliceViewFiducialBoxWidget class

        setattr(self, 'calcTransform', self._widget.calcTransform)
        setattr(self, 'addTransformToVolume', self._widget.addTransformToVolume)
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


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
    from Sisyphe.core.sisypheVolume import SisypheVolume

    app = QApplication(argv)
    main = QWidget()
    layout = QHBoxLayout(main)

    vlm = SisypheVolume()
    vlm.load('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/STEREO/CTLEKSELL9.xvol')
    view = IconBarSliceViewFiducialBoxWidget()
    view.setVolume(vlm)

    layout.addWidget(view)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    exit(app.exec_())

