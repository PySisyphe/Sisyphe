"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        vtk             https://vtk.org/                                            Visualization engine
"""

from os import getcwd
from os import chdir
from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext

from math import cos
from math import sin
from math import radians

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRegExp
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from vtk import vtkCutter
from vtk import vtkActor
from vtk import vtkPolyDataMapper
from vtk import vtkTransform
from vtk import vtkPlane

from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.widgets.basicWidgets import IconLabel
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import LockLabel
from Sisyphe.widgets.basicWidgets import VisibilityLabel
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import ColorSelectPushButton
from Sisyphe.widgets.basicWidgets import OpacityPushButton
from Sisyphe.widgets.toolWidgets import HandleWidget
from Sisyphe.widgets.toolWidgets import LineWidget
from Sisyphe.widgets.toolWidgets import ToolWidgetCollection
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.gui.dialogMeshProperties import DialogMeshProperties
from Sisyphe.gui.dialogFromXml import DialogFromXml
from Sisyphe.gui.dialogSettings import DialogSetting
from Sisyphe.gui.dialogTarget import DialogTarget
from Sisyphe.gui.dialogThreshold import DialogThreshold
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.gui.dialogFileSelection import DialogFileSelection
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['ItemAttributesWidget',
           'ItemOverlayAttributesWidget',
           'ItemROIAttributesWidget',
           'ItemMeshAttributesWidget',
           'ItemToolAttributesWidget',
           'ListAttributesWidget',
           'ListROIAttributesWidget',
           'ListMeshAttributesWidget',
           'ListToolAttributesWidget']

"""
    Class hierarchy
    
        QFrame -> ItemAttributesWidget -> ItemOverlayAttributesWidget
                                       -> ItemROIAttributesWidget
                                       -> ItemMeshAttributesWidget
                                       -> ItemToolAttributesWidget
        QWidget -> ListAttributesWidget -> ListROIAttributesWidget
                                        -> ListMeshAttributesWidget
                                        -> ListToolAttributesWidget
"""


class ItemAttributesWidget(QFrame):
    """
        ItemAttributesWidget class

        Description

            ItemAttributesWidget, base class to specialized ItemAttributesWidget classes.
            Collection of ItemAttributesWidget are displayed in ListAttributesWidget.

        Inheritance

            QFrame -> ItemAttributesWidget

        Private Attributes

            _item       type is fixed in specialized ItemAttributesWidget classes
            _views      IconBarViewWidgetCollection, to update visualization widgets with attributes
            _listattr   ListAttributesWidget

        Public methods

            setIconSize(int)
            int = getIconSize()
            bool = isChecked()
            setChecked(bool)
            setCheckBoxVisibility(bool)
            checkBoxVisibilityOn()
            checkBoxVisibilityOff()
            bool = getCheckBoxVisibility()
            dynamic type = getItem()
            setItem(dynamic type)
            bool = hasItem()
            setViewsCollection(IconBarViewWidgetCollection)
            IconBarViewWidgetCollection = getViewsCollection()
            bool = hasViewsCollection()
            setListAttributesWidget(ListAttributesWidget)
            ListAttributesWidget = getListAttributesWidget()
            bool = hasListAttributesWidget()

            inherited QFrame methods

        Revision:

            11/08/2023  remove() method bugfix
    """

    _VSIZE = 24
    _HSIZE = 320

    # Special method

    def __init__(self, item=None, views=None, listattr=None, minwidth=_HSIZE, parent=None):
        super().__init__(parent)

        self._item = item

        if views is not None:
            if not isinstance(views, IconBarViewWidgetCollection):
                raise TypeError('views parameter type {} is not IconBarViewWidgetCollection.'.format(type(views)))

        if listattr is not None:
            if not isinstance(listattr, ListAttributesWidget):
                raise TypeError('listattr parameter type {} is not ListAttributesWidget.'.format(type(listattr)))

        self._views = views
        self._listattr = listattr

        self._check = QCheckBox(self)

        self._save = IconLabel('save.png')
        self._remove = IconLabel('cross.png')

        self._save.setFixedSize(self._VSIZE, self._VSIZE)
        self._remove.setFixedSize(self._VSIZE, self._VSIZE)

        self._save.clicked.connect(self.save)
        self._remove.clicked.connect(self.remove)

        self._save.setToolTip('Save')
        self._remove.setToolTip('Remove')

        self._save.setVisible(False)
        self._remove.setVisible(False)

        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._check)
        lyout.addWidget(self._save)
        lyout.addWidget(self._remove)
        self.setLayout(lyout)

        self.setFixedHeight(self._VSIZE + 8)
        self.setMinimumWidth(minwidth)

    # Class method

    @classmethod
    def getDefaultMinimumWidth(cls):
        return cls._HSIZE

    # Private method

    def _updateViews(self):
        raise NotImplemented

    def _updateSettingsFromItem(self):
        raise NotImplemented

    # Public methods

    def setIconSize(self, size=_VSIZE + 8):
        self.setFixedHeight(size)
        size -= 8
        self._save.setFixedSize(size, size)
        self._remove.setFixedSize(size, size)

    def getIconSize(self):
        return self._save.width() + 8

    def isChecked(self):
        return self._check.isChecked()

    def setChecked(self, v):
        if isinstance(v, bool):
            self._check.setChecked(v)

    def setCheckBoxVisibility(self, v):
        if isinstance(v, bool):
            self._check.setVisible(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def checkBoxVisibilityOn(self):
        self._check.setVisible(True)

    def checkBoxVisibilityOff(self):
        self._check.setVisible(False)

    def getCheckBoxVisibility(self):
        return self._check.isVisible()

    def getItem(self):
        return self._item

    def setItem(self, item):
        self._item = item
        self._updateSettingsFromItem()

    def hasItem(self):
        return self._item is not None

    def setViewCollection(self, views):
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: raise TypeError('parameter type {} is not IconBarViewWidgetCollection.'.format(type(views)))

    def getViewCollection(self):
        return self._views

    def hasViewCollection(self):
        return self._views is not None

    def setListAttributesWidget(self, listattr):
        if isinstance(listattr, ListAttributesWidget): self._listattr = listattr
        else: raise TypeError('parameter type {} is not ListAttributesWidget.'.format(type(listattr)))

    def getListAttributesWidget(self):
        return self._listattr

    def hasListAttributesWidget(self):
        return self._listattr is not None

    def save(self):
        pass

    def remove(self):
        if self._listattr is not None:
            self._listattr.removeItem(self)


class ItemOverlayAttributesWidget(ItemAttributesWidget):
    """
        ItemOverlayAttributesWidget class

        Description

            Specialized ItemAttributesWidget to manage overlay.
            overlay settings : visibility, opacity

        Inheritance

            QWidget -> ItemAttributesWidget -> ItemOverlayAttributesWidget

        Private Attributes

            _visibility     VisibilityLabel, set visibility
            _opacity        QSlider, set opacity

        Custom Qt signal

            visibilityChanged.emit()    Emitted after visibility button click

        Public methods

            setOverlay(SisypheVolume)
            SisypheVolume = getOverlay()
            bool = hasOverlay()
            setVisibility(bool)
            bool = getVisibility()
            setOpacity(float)
            float = getOpacity()

            inherited QWidget methods
    """

    # Custom Qt signals

    visibilityChanged = pyqtSignal()

    # Special method

    def __init__(self, overlay=None, views=None, listattr=None, minwidth=192, parent=None):

        if overlay is not None:
            if not isinstance(overlay, SisypheVolume):
                raise TypeError('overlay parameter type {} is not SisypheVolume.'.format(type(overlay)))

        super().__init__(overlay, views, listattr, minwidth, parent)

        # Visibility button

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set overlay visibility')
        self._visibility.setFixedSize(self._VSIZE, self._VSIZE)
        self._visibility.setVisibilityStateIconToView()
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Slider

        self._label = QLabel()
        font = QFont('Arial', 10)
        self._label.setFont(font)

        self._opacity = QSlider(Qt.Horizontal)
        self._opacity.setTickPosition(QSlider.NoTicks)
        self._opacity.setMaximum(100)
        self._opacity.setMinimum(0)
        self._opacity.setValue(50)
        self._opacity.setToolTip('Opacity {} %'.format(self._opacity.value()))
        self._opacity.valueChanged.connect(self._opacityChanged)

        self.checkBoxVisibilityOff()

        # Widget layout

        lyout = self.layout()
        lyout.addWidget(self._opacity)
        lyout.addWidget(self._label)
        lyout.addWidget(self._visibility)

    # Private methods

    def _visibilityChanged(self, obj):
        if self.hasViewCollection() and self.hasItem():
            v = self._visibility.getVisibilityStateIcon()
            for view in self._views:
                view().getFirstSliceViewWidget().setOverlayVisibility(self._item, v)
                view.updateRender()
            self.visibilityChanged.emit()

    def _opacityChanged(self, value):
        self._label.setText('{} %'.format(self._opacity.value()))
        self._opacity.setToolTip('Opacity {} %'.format(value))
        if self.hasViewCollection() and self.hasItem():
            for view in self._views:
                view().getFirstSliceViewWidget().setOverlayOpacity(self._item, value / 100)
                view.updateRender()

    def _updateSettingsFromItem(self):
        if self.hasViewCollection() and self.hasItem():
            view = self._views[0]().getFirstSliceViewWidget()
            v = view.getOverlayVisibility(self._item)
            o = view.getOverlayOpacity(self._item)
            self._visibility.setVisibilitySateIcon(v)
            self._opacity.setValue(int(o * 100))

    # Public methods

    def setVisibility(self, v):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            self._visibilityChanged(self)
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                v = int(v * 100)
                self._opacity.setValue(v)
                self._opacityChanged(v)
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.value() / 100

    def setOverlay(self, vol):
        if isinstance(vol, SisypheVolume):
            super().setItem(vol)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def getOverlay(self):
        super().GetItem()

    def hasOverlay(self):
        super().hasItem()


class ItemROIAttributesWidget(ItemAttributesWidget):
    """
        ItemROIAttributesWidget

        Description

            ItemAttributesWidget class for management of ROI settings.
            ItemROIAttributesWidget are displayed in ListROIAttributesWidget.

        Inheritance

            QFrame -> ItemAttributesWidget -> ItemROIAttributesWidget

        Private attributes

            _visibility     VisibilityLabel, eye button to set visibility
            _name           LabeledLineEdit, widget to edit name
            _color          ColorSelectPushButton, widget to set color
            _opacity        OpacityPushButton, widget to set opacity

        Public methods

            setColor(float, float, float)
            float, float, float = getColor()
            setName(str)
            str = getName()
            setOpacity(float)
            float = getOpacity()
            setVisibility(bool)
            bool = getVisibility()
            setROI(SisypheROI)
            SisypheROI = getROI()
            bool = hasROI()
            save()

            inherited ItemAttributesWidget methods
            inherited QFrame methods
    """

    # Special method

    def __init__(self, roi=None, views=None, listattr=None, parent=None):

        if roi is not None:
            if not isinstance(roi, SisypheROI):
                raise TypeError('roi parameter type {} is not SisypheROI.'.format(type(roi)))

        super().__init__(roi, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set ROI visibility.')
        self._visibility.setFixedSize(self._VSIZE, self._VSIZE)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        self._name.setFixedHeight(self._VSIZE)
        self._name.setToolTip('Set ROI name,\nAccepted characters A...Z, a...z, 0...9, -, _, comma, space.')
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._VSIZE, self._VSIZE)
        self._color.colorChanged.connect(self._colorChanged)

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._VSIZE, self._VSIZE)
        self._opacity.setToolTip('Set ROI opacity.')
        self._opacity.opacityChanged.connect(self._opacityChanged)

        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Widget layout

        lyout = self.layout()
        lyout.insertWidget(1, self._color)
        lyout.insertWidget(1, self._opacity)
        lyout.insertWidget(1, self._visibility)
        lyout.insertWidget(1, self._name)
        lyout.insertSpacing(1, 5)

        self._updateSettingsFromItem()

    # Private methods

    def _visibilityChanged(self):
        self._item.setVisibility(self._visibility.getVisibilityStateIcon())
        self._updateViews()

    def _colorChanged(self):
        r, g, b = self._color.getColor()
        self._item.setColor(r, g, b)
        self._updateViews()

    def _opacityChanged(self):
        self._item.setAlpha(self._opacity.getOpacity())
        self._updateViews()

    def _nameChanged(self):
        if self.hasViewCollection():
            rois = self._views.getROICollection()
            name = self._name.getEditText()
            if name != self._item.getName():
                if name in rois:
                    QMessageBox.warning(self, 'Rename error', 'The ROI name {} is already in use.'.format(name))
                    self._name.setEditText(self._item.getName())
                else: self._item.setName(self._name.getEditText())

    def _updateSettingsFromItem(self):
        if self._item is not None:
            self._name.setEditText(self._item.getName())
            c = self._item.getColor()
            self._color.setFloatColor(c[0], c[1], c[2])
            self._opacity.setOpacity(self._item.getAlpha())
            self.setToolTip(str(self._item)[:-1])

    def _updateViews(self):
        if self.hasViewCollection() and self.hasItem():
            self._views.updateROIAttributes()

    # Public methods

    def setIconSize(self, size=ItemAttributesWidget._VSIZE + 8):
        super().setIconSize(size)
        size -= 8
        self._visibility.setFixedSize(size, size)
        self._color.setFixedSize(size, size)
        self._opacity.setFixedSize(size, size)

    def setColor(self, r, g, b):
        self._color.setFloatColor(r, g, b)
        self._colorChanged()

    def getColor(self):
        return self._color.getFloatColor()

    def setName(self, name):
        if isinstance(name, str):
            self._name.setEditText(name)
            self._nameChanged()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self):
        return self._name.getEditText()

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacity.setOpacity(v)
                self._opacityChanged()
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setVisibility(self, v):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            self._visibilityChanged()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setROI(self, roi):
        if isinstance(roi, SisypheROI):
            super().setItem(roi)
            # self._updateSettingsFromItem()
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def save(self):
        if self._item.hasFilename(): self._item.setDefaultFilename()
        try:
            self._item.save()
            if self.hasViewCollection(): self._views.clearUndo()
        except Exception as err:
            QMessageBox.warning(self, 'Save ROI', '{}'.format(err))

    # Method aliases

    getROI = ItemAttributesWidget.getItem
    hasROI = ItemAttributesWidget.hasItem


class ItemMeshAttributesWidget(ItemAttributesWidget):
    """
        ItemMeshAttributesWidget

        Description

            ItemAttributesWidget class for management of mesh settings.
            ItemMeshAttributesWidget are displayed in ListMeshAttributesWidget.

        Inheritance

            QFrame -> ItemAttributesWidget -> ItemMeshAttributesWidget

        Private attributes

            _visibility     VisibilityLabel, eye button to set visibility
            _name           LabeledLineEdit, widget to edit name
            _color          ColorSelectPushButton, widget to set color
            _lut            LutWidget
            _opacity        OpacityPushButton, widget to set opacity
            _properties     IconPushButton, rendering properties
            _trf            IconPushButton, geometric transformation
            _dialogtrf      DialogFromXml, dialog window to edit mesh geometric transformation
            _dialogprop     DialogMeshProperties, dialog window to edit mesh properties

        Public methods

            settings()
            transform()
            setColor(float, float, float)
            float, float, float = getColor()
            setLut(SisypheVolume)
            setName(str)
            str = getName()
            setOpacity(float)
            float = getOpacity()
            setVisibility(bool)
            bool = getVisibility()
            setRotations([float, float, float])
            setTranslations([float, float, float])
            setMesh(SisypheMesh)
            SisypheMesh = getMesh()
            bool = hasMesh()
            save()

            inherited ItemAttributesWidget methods
            inherited QFrame methods

        Revision:

            24/08/2023  settings() method, _color button update
    """

    # Special method

    def __init__(self, mesh=None, views=None, listattr=None, parent=None):

        if mesh is not None:
            if not isinstance(mesh, SisypheMesh):
                raise TypeError('mesh parameter type {} is not SisypheMesh.'.format(type(mesh)))

        super().__init__(mesh, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set mesh visibility.')
        self._visibility.setFixedSize(self._VSIZE, self._VSIZE)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        self._name.setFixedHeight(self._VSIZE)
        self._name.setToolTip('Set mesh name,\nAccepted characters A...Z, a...z, 0...9, -, _, #, comma, space.')
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._VSIZE, self._VSIZE)
        self._color.colorChanged.connect(self._colorChanged)

        # Lut

        self._lut = IconPushButton('lut.png', size=self._VSIZE)
        self._lut.setVisible(False)
        self._lutwidget = None

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._VSIZE, self._VSIZE)
        self._opacity.setToolTip('Set mesh opacity.')
        self._opacity.opacityChanged.connect(self._opacityChanged)
        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Properties

        self._properties = IconPushButton('meshsetting.png', self._VSIZE)
        self._properties.setToolTip('Mesh properties.')
        self._properties.clicked.connect(lambda dummy: self.settings())
        self._dialogprop = DialogMeshProperties()
        self._dialogprop.UpdateRender.connect(self._updateViews)

        # Transform

        self._trf = IconPushButton('rotate.png', self._VSIZE)
        self._trf.setToolTip('Apply rigid transformation to mesh.')
        self._trf.clicked.connect(lambda dummy: self.transform())
        trf = QMenu()
        self._tx = LabeledDoubleSpinBox(title='Tx', fontsize=10)
        self._tx.setDecimals(1)
        self._tx.setSingleStep(1.0)
        self._tx.setRange(-256.0, 256.0)
        self._tx.setValue(0.0)
        self._tx.setSuffix(' mm')
        self._ty = LabeledDoubleSpinBox(title='Ty', fontsize=10)
        self._ty.setDecimals(1)
        self._ty.setSingleStep(1.0)
        self._ty.setRange(-256.0, 256.0)
        self._ty.setValue(0.0)
        self._ty.setSuffix(' mm')
        self._tz = LabeledDoubleSpinBox(title='Tz', fontsize=10)
        self._tz.setDecimals(1)
        self._tz.setSingleStep(1.0)
        self._tz.setRange(-256.0, 256.0)
        self._tz.setValue(0.0)
        self._tz.setSuffix(' mm')
        self._rx = LabeledDoubleSpinBox(title='Rx', fontsize=10)
        self._rx.setDecimals(1)
        self._rx.setSingleStep(1.0)
        self._rx.setRange(-180.0, 180.0)
        self._rx.setValue(0.0)
        self._rx.setSuffix(' °')
        self._ry = LabeledDoubleSpinBox(title='Ry', fontsize=10)
        self._ry.setDecimals(1)
        self._ry.setSingleStep(1.0)
        self._ry.setRange(-180.0, 180.0)
        self._ry.setValue(0.0)
        self._ry.setSuffix(' °')
        self._rz = LabeledDoubleSpinBox(title='Rz', fontsize=10)
        self._rz.setDecimals(1)
        self._rz.setSingleStep(1.0)
        self._rz.setRange(-180.0, 180.0)
        self._rz.setValue(0.0)
        self._rz.setSuffix(' °')
        font = QFont('Arial', 10)
        clear = QPushButton('Clear')
        clear.setFont(font)
        clear.clicked.connect(self._clearTransform)
        cursor = QPushButton('To cursor')
        cursor.setFont(font)
        cursor.clicked.connect(self._goToCursorTransform)
        apply = QPushButton('Apply')
        apply.setFont(font)
        apply.clicked.connect(self.transform)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._tx)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._ty)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._tz)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._rx)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._ry)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(self._rz)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(clear)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(cursor)
        trf.addAction(a)
        a = QWidgetAction(trf)
        a.setDefaultWidget(apply)
        trf.addAction(a)
        self._trf.setMenu(trf)

        # Widget layout

        lyout = self.layout()
        lyout.insertWidget(1, self._trf)
        lyout.insertWidget(1, self._properties)
        lyout.insertWidget(1, self._color)
        lyout.insertWidget(1, self._lut)
        lyout.insertWidget(1, self._opacity)
        lyout.insertWidget(1, self._visibility)
        lyout.insertWidget(1, self._name)
        lyout.insertSpacing(1, 5)

        # Redirect child mouse double click event to self

        self._name.installEventFilter(self)
        self._visibility.installEventFilter(self)
        self._opacity.installEventFilter(self)
        self._color.installEventFilter(self)
        self._properties.installEventFilter(self)
        self._trf.installEventFilter(self)

        self._updateSettingsFromItem()

    # Private methods

    def _clearTransform(self):
        self._tx.setValue(0.0)
        self._ty.setValue(0.0)
        self._tz.setValue(0.0)
        self._rx.setValue(0.0)
        self._ry.setValue(0.0)
        self._rz.setValue(0.0)

    def _goToCursorTransform(self):
        if self._views is not None:
            pc = self._views.getVolumeView().getCursorWorldPosition()
            pm = self._item.getCenter()
            self._tx.setValue(pc[0] - pm[0])
            self._ty.setValue(pc[1] - pm[1])
            self._tz.setValue(pc[2] - pm[2])
            self._rx.setValue(0.0)
            self._ry.setValue(0.0)
            self._rz.setValue(0.0)

    def _visibilityChanged(self):
        self._item.setVisibility(self._visibility.getVisibilityStateIcon())
        self._updateViews()

    def _colorChanged(self):
        if self._item.getScalarColorVisibility() == 0:
            r, g, b = self._color.getFloatColor()
            self._item.setColor(r, g, b)
            self.setToolTip(str(self._item)[:-1])
            self._updateViews()

    def _opacityChanged(self):
        self._item.setOpacity(self._opacity.getOpacity())
        self.setToolTip(str(self._item)[:-1])
        self._updateViews()

    def _nameChanged(self):
        if self.hasViewCollection():
            meshes = self._views.getMeshCollection()
            name = self._name.getEditText()
            if name != self._item.getName():
                if name in meshes:
                    QMessageBox.warning(self, 'Rename error', 'The mesh name {} is already in use.'.format(name))
                    self._name.setEditText(self._item.getName())
                else: self._item.setName(self._name.getEditText())
                self.setToolTip(str(self._item)[:-1])

    def _updateViews(self):
        if self.hasViewCollection() and self.hasItem():
            volview = self._views.getVolumeView()
            if volview is not None: volview.updateRender()

    def _updateSettingsFromItem(self):
        if self._item is not None:
            self._name.setEditText(self._item.getName())
            c = self._item.getColor()
            self._color.setFloatColor(c[0], c[1], c[2])
            self._opacity.setOpacity(self._item.getOpacity())
            self.setToolTip(str(self._item)[:-1])

    # Public methods

    def setIconSize(self, size=ItemAttributesWidget._VSIZE + 8):
        super().setIconSize(size)
        size -= 8
        self._visibility.setFixedSize(size, size)
        self._color.setFixedSize(size, size)
        self._opacity.setFixedSize(size, size)
        self._properties.setIconSize(QSize(size - 8, size - 8))
        self._properties.setFixedSize(size, size)
        self._trf.setIconSize(QSize(size - 8, size - 8))
        self._trf.setFixedSize(size, size)
        if self._lut is not None:
            self._lut.setIconSize(QSize(size - 8, size - 8))
            self._lut.setFixedSize(size, size)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if views is not None:
            view = self._views.getVolumeView()
            if view is not None:
                self._dialogprop.UpdateRender.connect(view.updateRender)

    def settings(self):
        self._dialogprop.setProperties(self._item.getActor().GetProperty())
        self._dialogprop.exec()
        c = self._item.getActor().GetProperty().GetColor()
        self._color.setFloatColor(c[0], c[1], c[2])

    def transform(self):
        if self._tx.value() != 0.0 or self._ty.value() != 0.0 or self._tz.value() != 0.0 or \
                self._rx.value() != 0.0 or self._ry.value() != 0.0 or self._rz.value() != 0.0:
            trf = vtkTransform()
            t = (self._tx.value(), self._ty.value(), self._tz.value())
            if t != (0.0, 0.0, 0.0): trf.Translate(t)
            if self._rx.value() != 0.0: trf.RotateX(self._rx.value())
            if self._ry.value() != 0.0: trf.RotateY(self._ry.value())
            if self._rz.value() != 0.0: trf.RotateX(self._rz.value())
            self._item.applyTransform(trf)
            self._updateViews()

    def setColor(self, r, g, b):
        self._color.setFloatColor(r, g, b)
        self._colorChanged()

    def getColor(self):
        return self._color.getFloatColor()

    def setLut(self, vol):
        if isinstance(vol, SisypheVolume):
            self._lutwidget = LutWidget(view=self._views.getVolumeView(), size=256)
            self._lutwidget.lutWindowChanged.connect(lambda: self._item.update())
            self._lutwidget.setVolume(vol)
            self._lut.setVisible(True)
            self._color.setVisible(False)
            self._properties.setVisible(False)
            popup = QMenu()
            action = QWidgetAction(self)
            action.setDefaultWidget(self._lutwidget)
            popup.addAction(action)
            self._lut.setMenu(popup)

    def setName(self, name):
        if isinstance(name, str):
            self._name.setEditText(name)
            self._nameChanged()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self):
        return self._name.getEditText()

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacity.setOpacity(v)
                self._opacityChanged()
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setVisibility(self, v):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            self._visibilityChanged()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setTranslations(self, t):
        self._tx.setValue(t[0])
        self._ty.setValue(t[1])
        self._tz.setValue(t[2])

    def setRotations(self, r):
        self._rx.setValue(r[0])
        self._ry.setValue(r[1])
        self._rz.setValue(r[2])

    def setMesh(self, mesh):
        if isinstance(mesh, SisypheMesh):
            super().setItem(mesh)
            # _updateSettingsFromItem() is already called by super().setItem()
            # self._updateSettingsFromItem()
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def save(self):
        if not self._item.hasFilename():
            self._item.setFilename(join(self._views.getVolume().getDirname(),
                                        self._item.getName() + self._item.getFileExt()))
        wait = DialogWait(info='Save {} mesh...'.format(self._item.getName()), parent=self)
        wait.open()
        try: self._item.save()
        except Exception as err: QMessageBox.warning(self, 'Save Mesh', '{}'.format(err))
        wait.close()

    # Method aliases

    getMesh = ItemAttributesWidget.getItem
    hasMash = ItemAttributesWidget.hasItem

    # Qt event

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonDblClick:
            # Redirect child mouse double click event to self
            self.mouseDoubleClickEvent(event)
            return True
        else: return False

    def mouseDoubleClickEvent(self, event):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None:
                p = self._item.getCenterOfMass()
                if p is not None:
                    view.setCursorWorldPosition(p[0], p[1], p[2])


class ItemToolAttributesWidget(ItemAttributesWidget):
    """
        ItemToolAttributesWidget

        Description

            ItemAttributesWidget class for management of tool settings.
            ItemToolAttributesWidget are displayed in ListToolAttributesWidget.

        Inheritance

            QFrame -> ItemAttributesWidget -> ItemToolAttributesWidget

        Private attributes

            _visibility     VisibilityLabel, eye button to set visibility
            _name           LabeledLineEdit, widget to edit name
            _color          ColorSelectPushButton, widget to set color
            _opacity        OpacityPushButton, widget to set opacity
            _properties     IconPushButton, rendering properties
            _target         IconPushButton, target position
            _dialogprop     DialogMeshProperties, dialog window to edit tool properties
            _dialogtarget   DialogTarget, dialog window to set target position
            _dialoglength   DialogFromXml, dialog window to set trajectory length

        Public methods

            DialogTarget = getDialogTarget()
            setIconSize(int)
            setColor(float, float, float)
            [float, float, float] = getColor()
            setOpacity(float)
            float = getOpacity()
            setLock(bool)
            lock()
            unlock()
            bool = isLocked()
            setVisibility(bool)
            bool = getVisibility()
            setName(str)
            getName(str)
            focusTarget()
            focusEntry()
            properties()
            target()
            length()
            moving()
            save()
            getTool()
            bool = hasTool()
            setTool(HandleWidget | LineWidget)

            inherited ItemAttributesWidget methods
            inherited QFrame methods

        Revisions:

            07/09/2023  _colorChanged() method bugfix, replace self._color.getColor() with self._color.getFloatColor()
                        _updateSettingsFromItem() method bugfix, replace self._item.getAlpha() with self._item.getOpacity()
                        bugfix in all methods, replace self._views.getFirstSliceView() with self._views.getVolumeView()
                        properties() method bugfix
    """

    # Special method

    def __init__(self, tool=None, views=None, listattr=None, parent=None):
        super().__init__(tool, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set tool visibility.')
        self._visibility.setFixedSize(self._VSIZE, self._VSIZE)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Move to target

        self._toTarget = IconPushButton('ftarget.png', self._VSIZE)
        self._toTarget.setToolTip('Move cursor to target.')
        self._toTarget.clicked.connect(lambda dummy: self.focusTarget())

        # Move to entry

        self._toEntry = IconPushButton('fentry.png', self._VSIZE)
        self._toEntry.setToolTip('Move cursor to entry.')
        self._toEntry.clicked.connect(lambda dummy: self.focusEntry())

        # Lock

        self._lock = LockLabel()
        self._lock.setToolTip('Lock/unlock tool movement.')
        self._lock.setFixedSize(self._VSIZE, self._VSIZE)
        self._lock.lockChanged.connect(self._lockChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        self._name.setFixedHeight(self._VSIZE)
        self._name.setToolTip('Set tool name,\nAccepted characters A...Z, a...z, 0...9, -, _, comma, space.')
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._VSIZE, self._VSIZE)
        self._color.colorChanged.connect(self._colorChanged)

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._VSIZE, self._VSIZE)
        self._opacity.setToolTip('Set tool opacity.')
        self._opacity.opacityChanged.connect(self._opacityChanged)

        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Properties

        self._properties = IconPushButton('settings.png', self._VSIZE)
        self._properties.setToolTip('Set tool properties.')
        self._properties.clicked.connect(lambda dummy: self.properties())

        self._dialogprop = DialogSetting('Tools')

        # Position

        self._target = IconPushButton('target.png', self._VSIZE)
        self._target.setToolTip('Set point position.')
        self._target.clicked.connect(lambda dummy: self.target())

        self._dialogtarget = DialogTarget(tool, views)

        # Length

        self._length = IconPushButton('length.png', self._VSIZE)
        self._length.setToolTip('Set trajectory length.')
        self._length.clicked.connect(lambda dummy: self.length())

        self._dialoglength = DialogFromXml('Trajectory length', ['TrajectoryLength'])

        # Move

        self._move = IconPushButton('move.png', self._VSIZE)
        if tool is not None and isinstance(tool, HandleWidget): self._move.setToolTip('Move point.')
        else: self._move.setToolTip('Move trajectory.')

        self._move.clicked.connect(lambda dummy: self.moving())

        self._dialogmove = DialogFromXml('Move point/trajectory', ['DuplicateTool'])

        # Widget layout

        lyout = self.layout()
        lyout.insertWidget(1, self._properties)
        lyout.insertWidget(1, self._move)
        lyout.insertWidget(1, self._length)
        lyout.insertWidget(1, self._target)
        lyout.insertWidget(1, self._color)
        lyout.insertWidget(1, self._opacity)
        lyout.insertWidget(1, self._lock)
        lyout.insertWidget(1, self._toEntry)
        lyout.insertWidget(1, self._toTarget)
        lyout.insertWidget(1, self._visibility)
        lyout.insertWidget(1, self._name)
        lyout.insertSpacing(1, 5)

        # Redirect child mouse double click event to self

        self._name.installEventFilter(self)
        self._visibility.installEventFilter(self)
        self._toTarget.installEventFilter(self)
        self._toEntry.installEventFilter(self)
        self._lock.installEventFilter(self)
        self._opacity.installEventFilter(self)
        self._color.installEventFilter(self)
        self._target.installEventFilter(self)
        self._length.installEventFilter(self)
        self._move.installEventFilter(self)
        self._properties.installEventFilter(self)

        self._updateSettingsFromItem()

    # Private methods

    def _visibilityChanged(self):
        if self.hasViewCollection():
            self._item.setVisibility(self._visibility.getVisibilityStateIcon())
            view = self._views.getVolumeView()
            if view is not None: view.copyToolAttributes(self._item, None, signal=True)

    def _lockChanged(self):
        view = self._views.getVolumeView()
        if view is not None:
            if self._lock.getLockStateIcon(): view.lockTool(self._item, signal=True)
            else: view.unlockTool(self._item, signal=True)

    def _colorChanged(self):
        if self.hasViewCollection():
            r, g, b = self._color.getFloatColor()
            w = self._dialogprop.getSettingsWidget().getParameterWidget('Color')
            if w is not None: w.setFloatColor(r, g, b, signal=False)
            self._item.setColor((r, g, b))
            self.setToolTip(str(self._item))
            view = self._views.getVolumeView()
            if view is not None: view.copyToolAttributes(self._item, None, signal=True)

    def _opacityChanged(self):
        if self.hasViewCollection():
            v = self._opacity.getOpacity()
            self._item.setOpacity(v)
            w = self._dialogprop.getSettingsWidget().getParameterWidget('Opacity')
            if w is not None: w.setValue(v)
            self.setToolTip(str(self._item))
            view = self._views.getVolumeView()
            if view is not None:
                view.updateRender()
                view.copyToolAttributes(self._item, None, signal=True)

    def _nameChanged(self):
        if self.hasViewCollection():
            tools = self._views.getToolCollection()
            name = self._name.getEditText()
            if name != self._item.getName():
                if name in tools:
                    QMessageBox.warning(self, 'Rename error', 'The tool name {} is already in use.')
                    self._name.setEditText(self._item.getName())
                else:
                    view = self._views.getVolumeView()
                    if view is not None: view.renameTool(self._item, name, signal=True)
                    self._item.setName(self._name.getEditText())
                self.setToolTip(str(self._item))

    def _updateSettingsFromItem(self):
        if self._item is not None:
            # Update widget from item properties
            self._name.setEditText(self._item.getName())
            c = self._item.getColor()
            self._color.setFloatColor(c[0], c[1], c[2])
            self._opacity.setOpacity(self._item.getOpacity())
            self.setToolTip(str(self._item)[:-1])
            # Entry focus button visibility
            wline = isinstance(self._item, LineWidget)
            self._toEntry.setVisible(wline)
            self._length.setVisible(wline)
            self.setToolTip(str(self._item))

    # Public methods

    def updateSettingsFromAttributes(self):
        settings = self._dialogprop.getSettingsWidget()
        if isinstance(self._item, HandleWidget):
            settings.getParameterWidget('TextTarget').setText(self._item.getLegend())
            settings.getParameterWidget('HandleLineWidth').setValue(self._item.getLineWidth())
            settings.getParameterWidget('SafetyRadius').setValue(self._item.getSphereRadius())
            if self._item.getSphereVisibility() is True: v = Qt.Checked
            else: v = Qt.Unchecked
            settings.getParameterWidget('SafetyVisibility').setCheckState(v)
        elif isinstance(self._item, LineWidget):
            v = self._item.getLegend()
            settings.getParameterWidget('TextTarget').setText(v[0])
            settings.getParameterWidget('TextEntry').setText(v[1])
            settings.getParameterWidget('PointSize').setValue(self._item.getPointSize())
            settings.getParameterWidget('LineWidth').setValue(self._item.getLineWidth())
            settings.getParameterWidget('HandleLineWidth').setValue(self._item.getHandleLineWidth())
            settings.getParameterWidget('SafetyRadius').setValue(self._item.getTubeRadius())
            if self._item.getTubeVisibility() is True: v = Qt.Checked
            else: v = Qt.Unchecked
            settings.getParameterWidget('SafetyVisibility').setCheckState(v)
        settings.getParameterWidget('HandleSize').setValue(self._item.getHandleSize())
        settings.getParameterWidget('FontSize').setValue(self._item.getFontSize())
        settings.getParameterWidget('FontFamily').setCurrentText(self._item.getFontFamily())
        if self._item.getFontBold() is True: v = Qt.Checked
        else: v = Qt.Unchecked
        settings.getParameterWidget('FontBold').setCheckState(v)
        if self._item.getFontItalic() is True: v = Qt.Checked
        else: v = Qt.Unchecked
        settings.getParameterWidget('FontItalic').setCheckState(v)
        v = self._item.getTextOffset()
        settings.getParameterWidget('TextOffset')[0].setValue(v[0])
        settings.getParameterWidget('TextOffset')[1].setValue(v[1])
        if self._item.getTextVisibility() is True: v = Qt.Checked
        else: v = Qt.Unchecked
        settings.getParameterWidget('TextVisibility').setCheckState(v)
        settings.getParameterWidget('Tolerance').setValue(self._item.getTolerance())

    def setDefaultAttributesFromSettings(self):
        settings = self._dialogprop.getSettingsWidget()
        settings.resetSettings()
        # Update HandleWidget properties from settings
        if isinstance(self._item, HandleWidget):
            v = settings.getParameterValue('TextTarget')
            if v is not None: self._item.setLegend(v)
            v = settings.getParameterValue('HandleLineWidth')
            if v is not None: self._item.setLineWidth(v)
            v = settings.getParameterValue('SafetyRadius')
            if v is not None: self._item.setSphereRadius(v)
            v = settings.getParameterValue('SafetyVisibility')
            if v is not None: self._item.setSphereVisibility(v)
        # Update LineWidget properties from settings
        elif isinstance(self._item, LineWidget):
            v1 = settings.getParameterValue('TextTarget')
            v2 = settings.getParameterValue('TextEntry')
            if v1 is None and v2 is not None: self._item.setLegend([v1, v2])
            v = settings.getParameterValue('PointSize')
            if v is not None: self._item.setPointSize(v)
            v = settings.getParameterValue('LineWidth')
            if v is not None: self._item.setLineWidth(v)
            v = settings.getParameterValue('HandleLineWidth')
            if v is not None: self._item.setHandleLineWidth(v)
            v = settings.getParameterValue('SafetyRadius')
            if v is not None: self._item.setTubeRadius(v)
            v = settings.getParameterValue('SafetyVisibility')
            if v is not None: self._item.setTubeVisibility(v)
        # Update common properties from settings
        v = settings.getParameterValue('Color')
        if v is not None: self._item.setColor(v)
        v = settings.getParameterValue('SelectedColor')
        if v is not None: self._item.setSelectedColor(v)
        v = settings.getParameterValue('Opacity')
        if v is not None: self._item.setOpacity(v)
        v = settings.getParameterValue('HandleSize')
        if v is not None: self._item.setHandleSize(v)
        v = settings.getParameterValue('FontSize')
        if v is not None: self._item.setFontSize(v)
        v1 = settings.getParameterValue('FontFamily')[0]
        v2 = settings.getParameterValue('FontBold')
        v3 = settings.getParameterValue('FontItalic')
        if all([v is not None for v in (v1, v2, v2)]): self._item.setTextProperty(v1, v2, v3)
        v = settings.getParameterValue('TextOffset')
        if v is not None: self._item.setTextOffset(v)
        v = settings.getParameterValue('TextVisibility')
        if v is not None: self._item.setTextVisibility(v)
        v = settings.getParameterValue('Tolerance')
        if v is not None: self._item.setTolerance(v)
        self.setToolTip(str(self._item))
        view = self._views.getVolumeView()
        if view is not None: view.copyToolAttributes(self._item, None, signal=True)

    def getDialogTarget(self):
        return self._dialogtarget

    def setIconSize(self, size=ItemAttributesWidget._VSIZE + 8):
        super().setIconSize(size)
        size -= 8
        self._visibility.setFixedSize(size, size)
        self._lock.setFixedSize(size, size)
        self._color.setFixedSize(size, size)
        self._opacity.setFixedSize(size, size)
        self._properties.setIconSize(QSize(size - 8, size - 8))
        self._properties.setFixedSize(size, size)
        self._target.setIconSize(QSize(size - 8, size - 8))
        self._target.setFixedSize(size, size)
        self._length.setIconSize(QSize(size - 8, size - 8))
        self._length.setFixedSize(size, size)
        self._move.setIconSize(QSize(size - 8, size - 8))
        self._move.setFixedSize(size, size)

    def setColor(self, r, g, b, signal=True):
        self._color.setFloatColor(r, g, b)
        if signal: self._colorChanged()

    def getColor(self):
        return self._color.getFloatColor()

    def setOpacity(self, v, signal=True):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacity.setOpacity(v)
                if signal: self._opacityChanged()
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setLock(self, v):
        if isinstance(v, bool): self._lock.setLockStateIcon(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def lock(self):
        self.setLock(True)

    def unlock(self):
        self.setLock(False)

    def isLocked(self):
        return self._lock.getLockStateIcon()

    def setVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            if signal: self._visibilityChanged()
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setName(self, name, signal=True):
        if isinstance(name, str):
            self._name.setEditText(name)
            if signal: self._nameChanged()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self):
        return self._name.getEditText()

    def focusTarget(self):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None:
                if isinstance(self._item, HandleWidget): p = self._item.getPosition()
                elif isinstance(self._item, LineWidget): p = self._item.getPosition2()
                else: p = None
                if p is not None:
                    view.setCursorWorldPosition(p[0], p[1], p[2])
                    self._views.updateRender()

    def focusEntry(self):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None:
                if isinstance(self._item, LineWidget):
                    p = self._item.getPosition1()
                    if p is not None: view.setCursorWorldPosition(p[0], p[1], p[2])
                    self._views.updateRender()

    def properties(self):
        if self.hasViewCollection():
            settings = self._dialogprop.getSettingsWidget()
            wline = isinstance(self._item, LineWidget)
            settings.setParameterVisibility('TextEntry', wline)
            settings.setParameterVisibility('PointSize', wline)
            settings.setParameterVisibility('LineWidth', wline)
            if self._dialogprop.exec() == QDialog.Accepted:
                txt = settings.getParameterValue('TextTarget')
                if txt is None: txt = 'Target'
                if wline:
                    v = settings.getParameterValue('TextEntry')
                    if v is None: v = 'Entry'
                    txt = [txt, v]
                self._item.setLegend(txt)
                v = settings.getParameterValue('FontSize')
                if v is None: v = 12
                self._item.setFontSize(v)
                v1 = settings.getParameterValue('FontFamily')[0]
                if v1 is None: v1 = 'Arial'
                v2 = settings.getParameterValue('FontBold')
                if v2 is None: v2 = False
                v3 = settings.getParameterValue('FontItalic')
                if v3 is None: v3 = False
                self._item.setTextProperty(v1, v2, v3)
                v = settings.getParameterValue('TextOffset')
                if v is None: v = [40, 0]
                self._item.setTextOffset(v)
                v = settings.getParameterValue('TextVisibility')
                if v is None: v = True
                self._item.setTextVisibility(v)
                v = settings.getParameterValue('Color')
                if v is None: v = [1.0, 1.0, 1.0]
                self._item.setColor(v)
                self._color.setFloatColor(v[0], v[1], v[2])
                v = settings.getParameterValue('SelectedColor')
                if v is None: v = [1.0, 1.0, 1.0]
                self._item.setSelectedColor(v)
                v = settings.getParameterValue('Opacity')
                if v is None: v = 1.0
                self._item.setOpacity(v)
                self._opacity.setOpacity(v)
                if wline:
                    v = settings.getParameterValue('PointSize')
                    if v is None: v = 5.0
                    self._item.setPointSize(v)
                    v = settings.getParameterValue('LineWidth')
                    if v is None: v = 5.0
                    self._item.setLineWidth(v)
                v = settings.getParameterValue('HandleSize')
                if v is None: v = 10.0
                self._item.setHandleSize(v)
                v = settings.getParameterValue('HandleLineWidth')
                if v is None: v = 2.0
                if wline: self._item.setHandleLineWidth(v)
                else: self._item.setLineWidth(v)
                v = settings.getParameterValue('SafetyRadius')
                if v is None: v = 10.0
                if wline: self._item.setTubeRadius(v)
                else: self._item.setSphereRadius(v)
                v = settings.getParameterValue('SafetyVisibility')
                if v is None: v = True
                if wline: self._item.setTubeVisibility(v)
                else: self._item.setSphereVisibility(v)
                self.setToolTip(str(self._item))
                view = self._views.getVolumeView()
                if view is not None: view.copyToolAttributes(self._item, None, signal=True)

    def target(self):
        if self.hasViewCollection():
            self._dialogtarget.setTrajectoryFieldsVisibility(isinstance(self._item, LineWidget))
            if self._dialogtarget.exec() == QDialog.Accepted:
                r = self._dialogtarget.getAttributes()
                self._views.getVolumeView().moveTool(self._item, target=r['target'], entry=r['entry'])
                self.setLock(self._dialogtarget.isRelativeOrWeightedPosition())
                self.setToolTip(str(self._item))

    def length(self):
        if self.hasViewCollection():
            if isinstance(self._item, LineWidget):
                settings = self._dialoglength.getFieldsWidget(0)
                widget1 = settings.getParameterWidget('ExtendEntryToMesh')
                widget2 = settings.getParameterWidget('ExtendTargetToMesh')
                widget1.clear()
                widget2.clear()
                widget1.addItem('No')
                widget2.addItem('No')
                widget1.addItem('Current axial slice')
                widget2.addItem('Current axial slice')
                widget1.addItem('Current coronal slice')
                widget2.addItem('Current coronal slice')
                widget1.addItem('Current sagittal slice')
                widget2.addItem('Current sagittal slice')
                meshes = self._views.getMeshCollection()
                if meshes is not None:
                    n = meshes.count()
                    if n > 0:
                        for mesh in meshes:
                            widget1.addItem(mesh.getName())
                            widget2.addItem(mesh.getName())
                widget1.setCurrentIndex(0)
                widget2.setCurrentIndex(0)
                settings.getParameterWidget('ExtendEntry').setValue(0.0)
                settings.getParameterWidget('ExtendTarget').setValue(0.0)
                if self._dialoglength.exec() == QDialog.Accepted:
                    view = self._views.getOrthogonalSliceTrajectoryViewWidget()
                    e1 = settings.getParameterValue('ExtendEntry')
                    e2 = settings.getParameterValue('ExtendTarget')
                    if e1 is None: e1 = 0.0
                    else: e1 = float(e1)
                    if e2 is None: e2 = 0.0
                    else: e2 = float(e2)
                    c = widget1.currentIndex()
                    if view is not None:
                        if c == 1: self._item.extendPosition1ToPlane(view[0, 1].getVtkPlane())
                        elif c == 2: self._item.extendPosition1ToPlane(view[1, 0].getVtkPlane())
                        elif c == 3: self._item.extendPosition1ToPlane(view[1, 1].getVtkPlane())
                        elif c > 3:
                            mesh = self._views.getMeshCollection()[widget1.currentText()]
                            if mesh is not None:
                                if self._item.extendPosition1ToMeshSurface(mesh) == 0:
                                    msg = 'No intersection between {} and {} mesh'.format(self._item.getName(),
                                                                                          mesh.getName())
                                    QMessageBox.warning(self, 'Extend entry', msg)
                    c = widget2.currentIndex()
                    if view is not None:
                        if c == 1: self._item.extendPosition2ToPlane(view[0, 1].getVtkPlane())
                        elif c == 2: self._item.extendPosition2ToPlane(view[1, 0].getVtkPlane())
                        elif c == 3: self._item.extendPosition2ToPlane(view[1, 1].getVtkPlane())
                        elif c > 3:
                            mesh = self._views.getMeshCollection()[widget2.currentText()]
                            if mesh is not None:
                                if self._item.extendPosition2ToMeshSurface(mesh) == 0:
                                    msg = 'No intersection between {} and {} mesh'.format(self._item.getName(),
                                                                                          mesh.getName())
                                    QMessageBox.warning(self, 'Extend entry', msg)
                    self._item.extendPosition1(e1)
                    self._item.extendPosition2(e2)
                    self._views.getVolumeView().moveTool(self._item,
                                                         target=self._item.getPosition2(),
                                                         entry=self._item.getPosition1())
                    if e1 != 0 and e2 == 0: self.focusEntry()
                    elif e2 != 0: self.focusTarget()
                    self.setToolTip(str(self._item))

    def moving(self):
        if self.hasViewCollection():
            settings = self._dialogmove.getFieldsWidget(0)
            wp = settings.getParameterWidget('Projection')
            if isinstance(self._item, HandleWidget):
                settings.setParameterVisibility('Projection', True)
                wp.clear()
                wp.addItem('No')
                wp.addItem('Current axial slice')
                wp.addItem('Current coronal slice')
                wp.addItem('Current sagittal slice')
                if self.hasViewCollection():
                    meshes = self._views.getMeshCollection()
                    if meshes is not None:
                        n = meshes.count()
                        if n > 0:
                            for mesh in meshes:
                                wp.addItem('{} axial direction'.format(mesh.getName()))
                                wp.addItem('{} coronal direction'.format(mesh.getName()))
                                wp.addItem('{} sagittal direction'.format(mesh.getName()))
                wp.setCurrentIndex(0)
            else: settings.setParameterVisibility('Projection', False)
            w = settings.getParameterWidget('Laterality')
            w.setValue(0.0)
            w.setToolTip('Move + right, - left\n{}'.format(w.toolTip()))
            w = settings.getParameterWidget('Antero-posterior')
            w.setValue(0.0)
            w.setToolTip('Move + forward, - backward\n{}'.format(w.toolTip()))
            w = settings.getParameterWidget('Height')
            w.setValue(0.0)
            w.setToolTip('Move + top, - bottom\n{}'.format(w.toolTip()))
            vol = self._views.getVolume()
            if vol is not None: settings.getParameterWidget('Orientation').setVisible(vol.getACPC().hasACPC())
            if self._dialogmove.exec() == QDialog.Accepted:
                c = wp.currentIndex()
                if c == 0:
                    lat = settings.getParameterValue('Laterality')
                    if lat is None: lat = 0.0
                    ap = settings.getParameterValue('Antero-posterior')
                    if ap is None: ap = 0.0
                    h = settings.getParameterValue('Height')
                    if h is None: h = 0.0
                    o = settings.getParameterValue('Orientation')[0]
                    if o is None: o = 'Native'
                    if o == 'Native':
                        if isinstance(self._item, HandleWidget):
                            p = list(self._item.getPosition())
                            p[0] += lat
                            p[1] += ap
                            p[2] += h
                            self._views.getVolumeView().moveTool(self._item, target=p)
                        elif isinstance(self._item, LineWidget):
                            p1 = list(self._item.getPosition1())
                            p2 = list(self._item.getPosition2())
                            p1[0] += lat
                            p1[1] += ap
                            p1[2] += h
                            p2[0] += lat
                            p2[1] += ap
                            p2[2] += h
                            self._views.getVolumeView().moveTool(self._item, target=p2, entry=p1)
                    elif o == 'ACPC':
                        if isinstance(self._item, HandleWidget):
                            p = list(self._item.getPosition())
                            r = [lat, ap, h]
                            p = vol.getACPC().getPointFromRelativeDistanceToReferencePoint(r, p)
                            self._views.getVolumeView().moveTool(self._item, target=p)
                        elif isinstance(self._item, LineWidget):
                            p1 = list(self._item.getPosition1())
                            p2 = list(self._item.getPosition2())
                            r = [lat, ap, h]
                            p1 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint(r, p1)
                            p2 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint(r, p2)
                            self._views.getVolumeView().moveTool(self._item, target=p2, entry=p1)
                    elif o == 'Camera':
                        v0 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane().GetNormal()
                        v1 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane().GetNormal()
                        v2 = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane().GetNormal()
                        if isinstance(self._item, HandleWidget):
                            p = list(self._item.getPosition())
                            p[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            self._views.getVolumeView().moveTool(self._item, target=p)
                        elif isinstance(self._item, LineWidget):
                            p1 = list(self._item.getPosition1())
                            p2 = list(self._item.getPosition2())
                            p1[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p1[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p1[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            p2[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p2[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p2[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            self._views.getVolumeView().moveTool(self._item, target=p2, entry=p1)
                elif c == 1:
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c == 2:
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c == 3:
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c > 3:
                    if self.hasViewCollection():
                        inter = 0
                        name, d, _ = wp.currentText().split(' ')
                        mesh = self._views.getMeshCollection()[name]
                        if d == 'axial':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        elif d == 'coronal':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        elif d == 'sagittal':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        if inter == 0:
                            msg = 'No intersection between {} and {} mesh in {} direction.'.format(self._item.getName(), name, d)
                            QMessageBox.warning(self, 'Point projection', msg)
                        else: self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                self.focusTarget()
                self.setToolTip(str(self._item))

    def save(self):
        filename = join(self._views.getVolume().getDirname(),
                        self._item.getName() + self._item.getFileExt())
        wait = DialogWait(info='Save {} tool...'.format(self._item.getName()), parent=self)
        wait.open()
        try: self._item.saveAs(filename)
        except Exception as err: QMessageBox.warning(self, 'Save tool', '{}'.format(err))
        wait.close()

    def setTool(self, tool):
        if isinstance(tool, (HandleWidget, LineWidget)):
            super().setItem(tool)
            if tool is not None and isinstance(tool, HandleWidget):  self._move.setToolTip('Move point.')
            else: self._move.setToolTip('Move trajectory.')
        else: raise TypeError('parameter type {} is not HandleWidget or LineWidget.'.format(type(tool)))

    # Method aliases

    getTool = ItemAttributesWidget.getItem
    hasTool = ItemAttributesWidget.hasItem

    # Qt events

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonDblClick:
            # Redirect child mouse double click event to self
            self.mouseDoubleClickEvent(event)
            return True
        else: return False

    def mouseDoubleClickEvent(self, event):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None:
                if isinstance(self._item, HandleWidget): p = self._item.getPosition()
                elif isinstance(self._item, LineWidget): p = self._item.getPosition2()
                else: p = None
                if p is not None:
                    view.setCursorWorldPosition(p[0], p[1], p[2])
                    self._views.updateRender()


class ListAttributesWidget(QWidget):
    """
        ListAttributesWidget

        Description

            Abstract base class to manage a list of ItemAttributesWidget.

        Inheritance

            QWidget -> ListAttributesWidget

        Private attributes

            _collection     Collection, type is specified in specialized classes
            _list           QListWidget
            _new            QPushButton
            _open           QPushButton
            _saveall        QPushButton
            _removeall      QPushButton
            _btlayout       QHBoxLayout, layout of buttons bar

        Public methods

            setIconSize(int)
            int = getIconSize()
            setViewCollection(IconBarViewWidgetCollection)
            IconBarViewWidgetCollection = getViewCollection()
            hasViewCollection()
            setCollection(dynamic type)
            dynamic type = getCollection()
            bool = hasCollection()
            new()
            load()
            remove()
            removeAll()
            save()
            saveAll()
            clear()

            inherited QWidget methods

        Revision:

            07/08/2023  remove() method bugfix
            11/08/2023  add removeItem() method
            06/09/2023  add _getItemFromWidget() method
                        add selectWidget() method
            21/09/2023  getItem() and getWidget() methods bugfix, index must be >= 0 (and not > 0)
    """
    _VSIZE = 32

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(parent)

        self._collection = None
        self._scrsht = None

        self._views = views
        if views is not None:
            if views is not isinstance(views, IconBarViewWidgetCollection):
                raise TypeError('views parameter type {} is not IconBarViewWidgetCollection'.format(type(views)))

        self._list = QListWidget()
        self._list.setMinimumWidth(ItemAttributesWidget.getDefaultMinimumWidth())
        self._list.setSelectionMode(QListWidget.SingleSelection)
        self._list.itemSelectionChanged.connect(self._selectionChanged)

        self._new = IconPushButton('add.png', self._VSIZE)
        self._new.clicked.connect(lambda dummy: self.new())
        self._open = IconPushButton('open.png', self._VSIZE)
        self._open.clicked.connect(self.open)
        self._saveall = IconPushButton('save.png', self._VSIZE)
        self._saveall.clicked.connect(self.saveAll)
        self._removeall = IconPushButton('delete2.png', self._VSIZE)
        self._removeall.clicked.connect(self.removeAll)
        self._checkall = IconPushButton('check.png', self._VSIZE)
        self._checkall.clicked.connect(self.checkAll)
        self._uncheckall = IconPushButton('uncheck.png', self._VSIZE)
        self._uncheckall.clicked.connect(self.uncheckAll)

        self._new.setToolTip('New')
        self._open.setToolTip('Open')
        self._saveall.setToolTip('Save all')
        self._removeall.setToolTip('Remove all')
        self._checkall.setToolTip('Check all')
        self._uncheckall.setToolTip('Uncheck all')

        self._btlayout1 = QHBoxLayout()
        self._btlayout1.setContentsMargins(5, 0, 5, 0)
        self._btlayout1.setSpacing(5)
        self._btlayout1.addStretch()
        self._btlayout1.addWidget(self._open)
        self._btlayout1.addWidget(self._saveall)
        self._btlayout1.addWidget(self._removeall)
        self._btlayout1.addWidget(self._checkall)
        self._btlayout1.addWidget(self._uncheckall)
        self._btlayout1.addStretch()

        self._btlayout2 = QHBoxLayout()
        self._btlayout2.setContentsMargins(5, 0, 5, 0)
        self._btlayout2.setSpacing(5)
        self._btlayout2.addStretch()
        self._btlayout2.addWidget(self._new)
        self._btlayout2.addStretch()

        lyout = QVBoxLayout()
        lyout.setContentsMargins(5, 5, 5, 5)
        lyout.setSpacing(5)
        lyout.addWidget(self._list)
        lyout.addLayout(self._btlayout1)
        lyout.addLayout(self._btlayout2)

        self.setLayout(lyout)

        self._updateList()
        self.setAcceptDrops(True)
        margins1 = self.contentsMargins()
        margins2 = lyout.contentsMargins()
        self.setMinimumWidth(ItemAttributesWidget.getDefaultMinimumWidth() +
                             margins1.left() + margins1.right() +
                             margins2.left() + margins2.right())

    # Private methods

    def _createWidget(self, item: ItemAttributesWidget) -> ItemAttributesWidget:
        pass

    def _selectionChanged(self):
        select = self._getSelectedWidget()
        if select is not None:
            self._updateViews()

    def _getSelectedItem(self):
        s = self._list.selectedItems()
        if len(s) > 0: return s[0]
        else: return None

    def _getSelectedWidget(self):
        return self._list.itemWidget(self._getSelectedItem())

    def _getItemFromWidget(self, widget):
        n = self._list.count()
        if n > 0:
            for i in range(n):
                item = self._list.item(i)
                w = self._list.itemWidget(item)
                if w == widget: return item
        return None

    def _notAlreadyInList(self, item):
        n = self._list.count()
        if n > 0:
            for i in range(0, n):
                listitem = self._list.item(i)
                citem = self._list.itemWidget(listitem).getItem()
                if citem.getName() == item.getName(): return False
        return True

    def _addItem(self, item):
        if self._notAlreadyInList(item):
            widget = self._createWidget(item)
            listitem = QListWidgetItem()
            listitem.setSizeHint(widget.sizeHint())
            self._list.addItem(listitem)
            self._list.setItemWidget(listitem, widget)
            self._collection.append(item)
            listitem.setSelected(True)
            self._updateViews()
            return widget
        else: QMessageBox.warning(self, 'Add', '{} is already open.'.format(item.getName()))

    def _updateList(self):
        self._list.clear()
        if self.hasCollection():
            self._collection.sort()
            if len(self._collection) > 0:
                for item in self._collection:
                    widget = self._createWidget(item)
                    listitem = QListWidgetItem()
                    listitem.setSizeHint(widget.sizeHint())
                    self._list.addItem(listitem)
                    self._list.setItemWidget(listitem, widget)
                self._list.item(0).setSelected(True)
                self._updateViews()

    def _updateViews(self):
        raise NotImplemented

    def _getMainWindow(self):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, WindowSisyphe): return parent
            else: parent = parent.parent()

    def _getStatusBar(self):
        mainwindow = self.getMainWindow()
        if main is not None: return mainwindow.getStatusBar()
        else: return None

    # Public methods

    def setIconSize(self, size=_VSIZE):
        self._new.setIconSize(QSize(size - 8, size - 8))
        self._new.setFixedSize(size, size)
        self._open.setIconSize(QSize(size - 8, size - 8))
        self._open.setFixedSize(size, size)
        self._saveall.setIconSize(QSize(size - 8, size - 8))
        self._saveall.setFixedSize(size, size)
        self._removeall.setIconSize(QSize(size - 8, size - 8))
        self._removeall.setFixedSize(size, size)
        self._checkall.setIconSize(QSize(size - 8, size - 8))
        self._checkall.setFixedSize(size, size)
        self._uncheckall.setIconSize(QSize(size - 8, size - 8))
        self._uncheckall.setFixedSize(size, size)

    def getIconSize(self):
        return self._new.width()

    def setViewCollection(self, views):
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: self._views = None

    def getViewCollection(self):
        return self._views

    def hasViewCollection(self):
        return self._views is not None

    def setScreenshotsWidget(self, w):
        if isinstance(w, ScreenshotsGridWidget): self._scrsht = w
        else: self._scrsht = None

    def getScreenshotsWidget(self):
        return self._scrsht

    def hasScreenshotsWidget(self):
        return self._scrsht is not None

    def getCollection(self):
        return self._collection

    def hasCollection(self):
        return self._collection is not None

    def checkAll(self):
        for i in range(0, self._list.count()):
            item = self._list.item(i)
            widget = self._list.itemWidget(item)
            widget.setChecked(True)

    def uncheckAll(self):
        for i in range(0, self._list.count()):
            item = self._list.item(i)
            widget = self._list.itemWidget(item)
            widget.setChecked(False)

    def getChecked(self):
        widgets = list()
        for i in range(0, self._list.count()):
            item = self._list.item(i)
            widget = self._list.itemWidget(item)
            if widget.isChecked(): widgets.append(widget)
        return widgets

    def remove(self):
        if self.hasViewCollection() and self.hasCollection():
            n = self._list.count()
            if n > 0:
                for i in range(n-1, -1, -1):
                    listitem = self._list.item(i)
                    widget = self._list.itemWidget(listitem)
                    if widget.isChecked():
                        item = widget.getItem()
                        if listitem.isSelected() and i != 0: self._list.item(0).setSelected(True)
                        if item in self._collection: self._collection.remove(item)
                        self._list.removeItemWidget(listitem)
                        self._list.takeItem(i)
                        del widget
                if self._list.count() == 0: self._list.clear()
                self._updateViews()

    def removeItem(self, w):
        n = self._list.count()
        if n > 0:
            for i in range(n - 1, -1, -1):
                listitem = self._list.item(i)
                widget = self._list.itemWidget(listitem)
                if w == widget:
                    item = widget.getItem()
                    if listitem.isSelected() and i != 0: self._list.item(0).setSelected(True)
                    if item in self._collection: self._collection.remove(item)
                    self._list.removeItemWidget(listitem)
                    self._list.takeItem(i)
                    del widget
                    break
            if self._list.count() == 0: self._list.clear()

    def removeAll(self):
        if self._list.count() > 0: self._list.clear()
        if self.hasViewCollection() and self.hasCollection(): self._collection.clear()
        self._updateViews()

    def saveAll(self):
        if self.hasCollection():
            n = self._list.count()
            if n > 0 and self.hasCollection():
                for i in range(0, n):
                    attritem = self._list.item(i)
                    witem = self._list.itemWidget(attritem)
                    witem.save()

    def clear(self):
        self._list.clear()

    def count(self):
        return self._list.count()

    def isEmpty(self):
        return self._list.count() == 0

    def getWidget(self, index):
        if isinstance(index, int):
            if 0 <= index < self._list.count():
                return self._list.itemWidget(self._list.item(index))
            else: raise ValueError('parameter is out of range.')
        else: raise ValueError('parameter type {} is not int.'.format(type(index)))

    def getItem(self, index):
        if isinstance(index, int):
            if 0 <= index < self._list.count():
                return self._list.itemWidget(self._list.item(index)).getItem()
            else: raise ValueError('parameter is out of range.')
        else: raise ValueError('parameter type {} is not int.'.format(type(index)))

    def selectWidget(self, widget):
        item = self._getItemFromWidget(widget)
        if item is not None: item.setSelected(True)

    # Public abstract methods

    def new(self):
        raise NotImplemented

    def open(self):
        raise NotImplemented

    # Qt event

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()


class ListROIAttributesWidget(ListAttributesWidget):
    """
        ListROIAttributesWidget

        Description

            Class to manage a list of ItemROIAttributesWidget.

        Inheritance

            QWidget -> ListAttributesWidget -> ListROIAttributesWidget

        Private attributes

            _collection     SisypheROICollection
            _listmeshwidget ListMeshAttributesWidget

        Public methods

            getCheckedROI()
            getSelectedROI()
            setListMeshAttributeWidget(ListMeshAttributeWidget)
            ListMeshAttributeWidget = getListMeshAttributeWidget()
            bool = hasListMeshAttributeWidget()
            getTabToolsWidget()
            bool = hasTabToolsWidget()
            new(str)
            add(SisypheROI)
            duplicate()
            open()
            remove()
            removeAll()
            saveAll()
            saveSisyphe()
            saveNifti()
            saveNRRD()
            saveMinc()
            saveNumpy()
            saveVTK()
            saveDicomRT()
            toMesh()

            inherited ListAttributesWidget
            inherited QWidget methods
    """

    # Special method

    def __init__(self, views=None, parent=None):

        super().__init__(views, parent)

        self._listmeshwidget = None

        self._remove = IconPushButton('cross.png', size=ListAttributesWidget._VSIZE)
        self._duplicate = IconPushButton('duplicate.png', size=ListAttributesWidget._VSIZE)
        self._export = IconPushButton('export.png', size=ListAttributesWidget._VSIZE)
        self._mesh = IconPushButton('roi2mesh.png', size=ListAttributesWidget._VSIZE)

        self._remove.clicked.connect(self.remove)
        self._duplicate.clicked.connect(self.duplicate)
        self._export.clicked.connect(self._exportMenu)
        self._mesh.clicked.connect(self.toMesh)

        self._remove.setToolTip('Remove checked ROI(s)')
        self._duplicate.setToolTip('Duplicate selected ROI')
        self._export.setToolTip('Export checked ROI(s)')
        self._mesh.setToolTip('Conversion of checked ROI(s) to mesh(es)')

        self._btlayout1.insertWidget(4, self._remove)
        self._btlayout1.insertWidget(4, self._export)
        self._btlayout2.insertWidget(2, self._mesh)
        self._btlayout2.insertWidget(2, self._duplicate)

        self._popup = QMenu()
        self._action = dict()
        self._action['xvol'] = QAction('Export to PySisyphe format')
        self._action['nii'] = QAction('Export to Nifti format')
        self._action['nrrd'] = QAction('Export to Nrrd format')
        self._action['minc'] = QAction('Export to Minc format')
        self._action['numpy'] = QAction('Export to Numpy format')
        self._action['vtk'] = QAction('Export to VTK format')
        self._action['dcm'] = QAction('Export to DICOM RT format')
        self._action['xvol'].triggered.connect(self.saveSisyphe)
        self._action['nii'].triggered.connect(self.saveNifti)
        self._action['nrrd'].triggered.connect(self.saveNRRD)
        self._action['minc'].triggered.connect(self.saveMinc)
        self._action['numpy'].triggered.connect(self.saveNumpy)
        self._action['vtk'].triggered.connect(self.saveVTK)
        self._action['dcm'].triggered.connect(self.saveDicomRT)
        self._popup.addAction(self._action['xvol'])
        self._popup.addAction(self._action['nii'])
        self._popup.addAction(self._action['nrrd'])
        self._popup.addAction(self._action['minc'])
        self._popup.addAction(self._action['numpy'])
        self._popup.addAction(self._action['vtk'])
        self._popup.addAction(self._action['dcm'])

        self._new.setToolTip('{} ROI'.format(self._new.toolTip()))
        self._open.setToolTip('{} ROI(s)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} ROI(s)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} ROI(s)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} ROI(s)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} ROI(s)'.format(self._uncheckall.toolTip()))

    # Private methods

    def _createWidget(self, item):
        return ItemROIAttributesWidget(item, views=self._views, listattr=self)

    def _selectionChanged(self):
        QApplication.processEvents()
        select = self._getSelectedWidget()
        if select is not None:
            self._views.setActiveROI(select.getROI().getName())
            self._views.clearUndo()

    def _updateViews(self):
        if self.hasViewCollection():
            self._views.updateROIAttributes()

    def _getListMesh(self):
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            meshlist = mainwindow.getMeshListWidget()
            if meshlist is not None: return meshlist.getMeshListWidget()
        return None

    def _exportMenu(self):
        p = self.mapToGlobal(QPoint(0, self.height()))
        self._popup.popup(p)

    # Public methods

    def setIconSize(self, size=ListAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._remove.setIconSize(QSize(size - 8, size - 8))
        self._remove.setFixedSize(size, size)
        self._duplicate.setIconSize(QSize(size - 8, size - 8))
        self._duplicate.setFixedSize(size, size)
        self._export.setIconSize(QSize(size - 8, size - 8))
        self._export.setFixedSize(size, size)
        self._mesh.setIconSize(QSize(size - 8, size - 8))
        self._mesh.setFixedSize(size, size)

    def getCheckedROI(self):
        rois = list()
        for i in range(0, self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget.isChecked():
                rois.append(widget.getROI())
        if len(rois) > 0: return rois
        else: return None

    def getSelectedROI(self):
        return self._getSelectedWidget().getROI()

    def setListMeshAttributeWidget(self, widget):
        if isinstance(widget, ListMeshAttributesWidget): self._listmeshwidget = widget
        else: raise TypeError('parameter type {} is not ListMeshAttributesWidget.'.format(type(widget)))

    def getListMeshAttributeWidget(self):
        return self._listmeshwidget

    def hasListMeshAttributeWidget(self):
        return self._listmeshwidget is not None

    def getTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabROIListWidget
        if isinstance(parent, TabROIListWidget):
            return parent

    def hasTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabROIListWidget
        return isinstance(parent, TabROIListWidget)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection): self._collection = views.getROICollection()
        else: self._collection = None

    def new(self, name=''):
        if self.hasViewCollection() and self.hasCollection():
            wait = DialogWait(info='Add new ROI...', parent=self)
            wait.open()
            vol = self._views.getVolume()
            roi = SisypheROI(vol)
            roi.setReferenceID(self._collection.getReferenceID())
            roi.setAlpha(0.5)
            if name == '': roi.setName('ROI' + str(len(self._collection) + 1))
            else: roi.setName(name)
            self._addItem(roi)
            self._views.setActiveROI(roi.getName())
            self._views.setROIVisibility(True)
            # Set undo enabled
            draw = self._views.getROIDraw()
            if draw is not None: draw.setUndoOn()
            # Set ROI tools enabled
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setROIToolsEnabled(True)
                mainwindow.setROIToolsVisibility(True)
                mainwindow.setStatusBarMessage('New ROI {} added.'.format(name))
            wait.close()

    def add(self, roi):
        if self.hasViewCollection() and self.hasCollection():
            if isinstance(roi, SisypheROI):
                title = 'Add ROI'
                vol = self._views.getVolume()
                if roi.getReferenceID() == vol.getID():
                    if roi.getName() not in self._collection:
                        roi.setOrigin(vol.getOrigin())
                        self._addItem(roi)
                        self._views.setActiveROI(roi.getName())
                        self._views.setROIVisibility(True)
                        # Set undo enabled
                        draw = self._views.getROIDraw()
                        if draw is not None: draw.setUndoOn()
                        # Set ROI tools enabled
                        mainwindow = self._getMainWindow()
                        if mainwindow is not None:
                            mainwindow.setROIToolsEnabled(True)
                            mainwindow.setROIToolsVisibility(True)
                            mainwindow.setStatusBarMessage('ROI {} added.'.format(roi.getName()))
                    else: QMessageBox.warning(self, title, 'ROI {} is already open.'.format(roi.getName()))
                else: QMessageBox.warning(self, title,
                                          '{} ROI does not belong to {} volume (ID mismatch).'.format(
                                              roi.getName(),
                                              vol.getBasename()))
            else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def duplicate(self):
        if self.hasViewCollection() and self.hasCollection():
            widget = self._getSelectedWidget()
            if widget is not None:
                wait = DialogWait(info='Duplicate selected ROI...', parent=self)
                wait.open()
                roi = widget.getItem()
                roi2 = roi.copy()
                roi2.setAlpha(0.5)
                roi2.setName(roi.getName() + str(len(self._collection) + 1))
                self.add(roi2)
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('ROI {} duplicated.'.format(roi.getName()))

    def open(self):
        if self.hasViewCollection() and self.hasCollection():
            title = 'Open ROI(s)'
            filt = 'ROI (*{})'.format(SisypheROI.getFileExt())
            filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
            QApplication.processEvents()
            if filenames:
                chdir(dirname(filenames[0]))
                for filename in filenames:
                    roi = SisypheROI()
                    try:
                        roi.load(filename)
                        self.add(roi)
                    except Exception as err:
                        QMessageBox.warning(self, title, '{}'.format(err))

    def remove(self):
        if self.hasViewCollection() and self.hasCollection():
            rois = self.getCheckedROI()
            n = len(rois)
            if n > 0:
                super().remove()
                mainwindow = self._getMainWindow()
                if self._collection.count() == 0:
                    self._views.setROIVisibility(False)
                    self._views.clearUndo()
                    if mainwindow is not None:
                        mainwindow.setROIToolsEnabled(False)
                        mainwindow.setROIToolsVisibility(False)
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Checked ROI(s) removed.')

    def removeItem(self, w):
        if self.hasViewCollection() and self.hasCollection():
            roi = w.getROI()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} ROI removed.'.format(roi.getName()))
            super().removeItem(w)
            if self._collection.count() == 0:
                self._views.setROIVisibility(False)
                self._views.clearUndo()
                if mainwindow is not None:
                    mainwindow.setROIToolsEnabled(False)
                    mainwindow.setROIToolsVisibility(False)

    def removeAll(self):
        super().removeAll()
        self._views.setROIVisibility(False)
        self._views.clearUndo()
        # Set ROI tools disabled
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setROIToolsEnabled(False)
            mainwindow.setROIToolsVisibility(False)
            mainwindow.setStatusBarMessage('All ROI(s) removed.')

    def saveAll(self):
        super().saveAll()
        self._views.clearUndo()
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setStatusBarMessage('All ROI(s) saved.')

    def saveSisyphe(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            ref = self.getViewCollection().getVolume()
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename(): filename = join(ref.getFilename(), roi.getName() + ref.getFileExt())
                else: filename = item.getFilename()
                vol = SisypheVolume(roi)
                ref.copyAttributesTo(vol)
                vol.saveAs(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to PySisyphe format.')
        else: QMessageBox.warning(self, 'Export to PySisyphe format', 'No ROI checked.')

    def saveNifti(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNiftiExt()[0])
                else: filename = item.getFilename()
                roi.saveToNIFTI(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Nifti format.')
        else: QMessageBox.warning(self, 'Export to Nifti format', 'No ROI checked.')

    def saveNRRD(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNrrdExt()[0])
                else: filename = item.getFilename()
                roi.saveToNRRD(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Nrrd format.')
        else: QMessageBox.warning(self, 'Export to Nrrd format', 'No ROI checked.')

    def saveMinc(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getMincExt()[0])
                else: filename = item.getFilename()
                roi.saveToMINC(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Minc format.')
        else: QMessageBox.warning(self, 'Export to Minc format', 'No ROI checked.')

    def saveNumpy(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNumpyExt()[0])
                else: filename = item.getFilename()
                roi.saveToNumpy(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Numpy format.')
        else: QMessageBox.warning(self, 'Export to Numpy format', 'No ROI checked.')

    def saveVTK(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getVtkExt()[0])
                else: filename = item.getFilename()
                roi.saveToVTK(filename)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to VTK format.')
        else: QMessageBox.warning(self, 'Export to VTK format', 'No ROI checked.')

    # to do
    def saveDicomRT(self):
        rois = self.getCheckedROI()
        if len(rois) > 0:
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName())
                else: filename = item.getFilename()
                # to do
                pass
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Export checked ROI(s) to Dicom RT format.')
        else: QMessageBox.warning(self, 'Export to Dicom RT format', 'No ROI checked.')

    def toMesh(self):
        if self.hasViewCollection():
            rois = self.getCheckedROI()
            if len(rois) > 0:
                for roi in rois:
                    mesh = SisypheMesh()
                    mesh.createFromROI(roi, fill=False)
                    self._listmeshwidget.add(mesh)
            else: QMessageBox.warning(self, 'Mesh(es) from ROI(s)', 'No ROI checked.')
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('ROI(s) converted to mesh(es).')

    # Qt event

    def dropEvent(self, event):
        if self.hasViewCollection():
            if event.mimeData().hasText():
                event.acceptProposedAction()
                files = event.mimeData().text().split('\n')
                for file in files:
                    if file != '':
                        filename = file.replace('file://', '')
                        if splitext(filename)[1] == SisypheROI.getFileExt():
                            title = 'Open PySisyphe ROI'
                            roi = SisypheROI()
                            try:
                                roi.load(filename)
                                if roi.getReferenceID() == self._collection.getReferenceID(): self._addItem(roi)
                                else:
                                    QMessageBox.warning(self, title, 'ROI {} is not in same space as reference '
                                                                     'volume.'.format(basename(roi.getFilename())))
                            except Exception as err:
                                QMessageBox.warning(self, title, '{}'.format(err))
            else: event.ignore()

    # Method aliases

    getROI = ListAttributesWidget.getItem


class ListMeshAttributesWidget(ListAttributesWidget):
    """
        ListMeshAttributesWidget

        Description

            Class to manage a list of ItemMeshAttributesWidget.

        Inheritance

            QWidget -> ListAttributesWidget -> ListMeshAttributesWidget

        Private attributes

            _listroiwidget  ListROIAttributesWidget
            _dialog         DialogThreshold

        Public methods

            getCheckedMesh()
            getSelectedMesh()
            setListROIAttributeWidget(ListROIAttributeWidget)
            ListROIAttributeWidget = getListROIAttributeWidget()
            bool = hasListROIAttributeWidget()
            getTabToolsWidget()
            bool = hasTabToolsWidget()
            add(SisypheMesh)
            addOuterSurface()
            addIsosurface()
            addRoi(SisypheROI)
            addCube()
            addSphere()
            duplicate()
            filter()
            dilate(float)
            erode(float)
            union()
            intersection()
            difference()
            features()
            open()
            remove()
            removeAll()
            saveAll()
            saveOBJ()
            saveSTL()
            saveVTK()
            saveXMLVTK()
            toRoi()

            inherited ListAttributesWidget
            inherited QWidget methods

        Revisions:

            07/08/2023  remove() method bugfix
            07/08/2023  union(), intersection(), difference() bugfix
            11/08/2023  add removeItem() method
            24/08/2023  addOverlay() method bugfix
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._new.setVisible(False)
        self._listroiwidget = None

        self._remove = IconPushButton('cross.png', size=ListAttributesWidget._VSIZE)
        self._out = IconPushButton('head.png', size=ListAttributesWidget._VSIZE)
        self._iso = IconPushButton('vol2mesh.png', size=ListAttributesWidget._VSIZE)
        self._roi = IconPushButton('roi2mesh.png', size=ListAttributesWidget._VSIZE)
        self._cube = IconPushButton('cube.png', size=ListAttributesWidget._VSIZE)
        self._sphere = IconPushButton('sphere.png', size=ListAttributesWidget._VSIZE)
        self._duplicate = IconPushButton('duplicate.png', size=ListAttributesWidget._VSIZE)
        self._overlay = IconPushButton('overlay.png', size=ListAttributesWidget._VSIZE)
        self._export = IconPushButton('export.png', size=ListAttributesWidget._VSIZE)
        self._2roi = IconPushButton('mesh2roi.png', size=ListAttributesWidget._VSIZE)

        self._remove.clicked.connect(self.remove)
        self._out.clicked.connect(self.addOuterSurface)
        self._iso.clicked.connect(self.addIsosurface)
        # self._roi.clicked.connect(self._roiMenu)
        self._duplicate.clicked.connect(self.duplicate)
        # self._overlay.clicked.connect(self._overlayMenu)
        self._2roi.clicked.connect(self.toRoi)

        self._remove.setToolTip('Remove checked mesh(es)')
        self._out.setToolTip('Add outer surface mesh')
        self._iso.setToolTip('Add isosurface mesh')
        self._roi.setToolTip('Add mesh from roi')
        self._cube.setToolTip('Add cube mesh at the cursor position')
        self._sphere.setToolTip('Add sphere mesh at the cursor position')
        self._duplicate.setToolTip('Duplicate checked mesh(es)')
        self._overlay.setToolTip('Paint checked mesh(es) with overlay')
        self._export.setToolTip('Export checked mesh(es)')
        self._2roi.setToolTip('Conversion of checked mesh(es) to ROI(s)')

        self._btlayout1.insertWidget(4, self._remove)
        self._btlayout1.insertWidget(4, self._export)
        self._btlayout2.insertWidget(2, self._2roi)
        self._btlayout2.insertWidget(2, self._overlay)
        self._btlayout2.insertWidget(2, self._duplicate)
        self._btlayout2.insertWidget(2, self._cube)
        self._btlayout2.insertWidget(2, self._sphere)
        self._btlayout2.insertWidget(2, self._roi)
        self._btlayout2.insertWidget(2, self._iso)
        self._btlayout2.insertWidget(2, self._out)

        self._popupExport = QMenu()
        self._action = dict()
        self._action['obj'] = QAction('Export to OBJ format')
        self._action['stl'] = QAction('Export to STL format')
        self._action['vtk'] = QAction('Export to VTK format')
        self._action['xvtk'] = QAction('Export to XMLVTK format')
        self._action['obj'].triggered.connect(self.saveOBJ)
        self._action['stl'].triggered.connect(self.saveSTL)
        self._action['vtk'].triggered.connect(self.saveVTK)
        self._action['xvtk'].triggered.connect(self.saveXMLVTK)
        self._popupExport.addAction(self._action['obj'])
        self._popupExport.addAction(self._action['stl'])
        self._popupExport.addAction(self._action['vtk'])
        self._popupExport.addAction(self._action['xvtk'])
        self._export.setMenu(self._popupExport)

        self._popupCube = QMenu()
        self._cubex = LabeledDoubleSpinBox()
        self._cubex.setTitle('Size x')
        self._cubex.setFontSize(10)
        self._cubex.setValue(10.0)
        self._cubex.setDecimals(1)
        self._cubex.setSingleStep(1.0)
        self._cubex.setSuffix(' mm')
        self._cubex.setRange(1.0, 256.0)
        self._cubey = LabeledDoubleSpinBox()
        self._cubey.setTitle('Size y')
        self._cubey.setFontSize(10)
        self._cubey.setValue(10.0)
        self._cubey.setDecimals(1)
        self._cubey.setSingleStep(1.0)
        self._cubey.setSuffix(' mm')
        self._cubey.setRange(1.0, 256.0)
        self._cubez = LabeledDoubleSpinBox()
        self._cubez.setTitle('Size z')
        self._cubez.setFontSize(10)
        self._cubez.setValue(10.0)
        self._cubez.setDecimals(1)
        self._cubez.setSingleStep(1.0)
        self._cubez.setSuffix(' mm')
        self._cubez.setRange(1.0, 256.0)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._cubex)
        self._popupCube.addAction(action)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._cubey)
        self._popupCube.addAction(action)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._cubez)
        self._popupCube.addAction(action)
        self._popupCube.addSeparator()
        self._action['cube'] = QAction('Add parallelepiped mesh')
        self._action['cube'].triggered.connect(self.addCube)
        self._popupCube.addAction(self._action['cube'])
        self._cube.setMenu(self._popupCube)

        self._popupSphere = QMenu()
        self._spherer = LabeledDoubleSpinBox()
        self._spherer.setTitle('Radius')
        self._spherer.setFontSize(10)
        self._spherer.setValue(10.0)
        self._spherer.setDecimals(1)
        self._spherer.setSingleStep(1.0)
        self._spherer.setSuffix(' mm')
        self._spherer.setRange(1.0, 256.0)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._spherer)
        self._popupSphere.addAction(action)
        self._popupSphere.addSeparator()
        self._action['sphere'] = QAction('Add sphere mesh')
        self._action['sphere'].triggered.connect(self.addSphere)
        self._popupSphere.addAction(self._action['sphere'])
        self._sphere.setMenu(self._popupSphere)

        self._ractions = list()
        self._popupRoi = QMenu()
        self._popupRoi.aboutToShow.connect(self._roiMenu)
        self._roi.setMenu(self._popupRoi)
        self._oactions = list()
        self._popupOverlay = QMenu()
        self._popupOverlay.aboutToShow.connect(self._overlayMenu)
        self._overlay.setMenu(self._popupOverlay)

        self._open.setToolTip('{} Mesh(es)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} Mesh(es)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} Mesh(es)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} Mesh(es)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} Mesh(es)'.format(self._uncheckall.toolTip()))

        self._dialog = DialogThreshold(size=384)

    # Private methods

    def _createWidget(self, item):
        return ItemMeshAttributesWidget(item, views=self._views, listattr=self)

    def _updateViews(self):
        if self.hasViewCollection():
            volview = self._views.getVolumeView()
            if volview is not None: volview.updateRender()

    def _roiMenu(self):
        if self.hasListROIAttributeWidget():
            self._ractions.clear()
            self._popupRoi.clear()
            rois = self.getListROIAttributeWidget().getCollection()
            if len(rois) > 0:
                for roi in rois:
                    action = QAction(roi.getName())
                    action.triggered.connect(lambda dummy: self.addRoi([roi]))
                    self._popupRoi.addAction(action)
                    self._ractions.append(action)
                action = QAction('Add all ROI(s)')
                action.triggered.connect(lambda dummy: self.addRoi(rois.getList()))
                self._popupRoi.addAction(action)
                self._ractions.append(action)
                self._popupRoi.addSeparator()
            action = QAction('Add ROI(s) from disk')
            action.triggered.connect(lambda dummy: self.addRoi([]))
            self._popupRoi.addAction(action)
            self._ractions.append(action)

    def _overlayMenu(self):
        self._oactions.clear()
        self._popupOverlay.clear()
        view = self._views.getFirstSliceView()
        if view is not None:
            action = QAction(view.getVolume().getName())
            action.triggered.connect(lambda dummy: self.addOverlay(view.getVolume()))
            self._popupOverlay.addAction(action)
            from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget
            if isinstance(view, SliceOverlayViewWidget):
                n = view.getOverlayCount()
                if n > 0:
                    for ovl in view.getOverlayCollection():
                        action = QAction(ovl.getName())
                        action.triggered.connect(lambda dummy, v=ovl: self.addOverlay(v))
                        self._popupOverlay.addAction(action)
                        self._oactions.append(action)
            self._popupOverlay.addSeparator()
        action = QAction('Add overlay from disk')
        action.triggered.connect(lambda dummy: self.addOverlay(''))
        self._popupOverlay.addAction(action)
        self._oactions.append(action)

    # Public methods

    def setIconSize(self, size=ListAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._remove.setIconSize(QSize(size - 8, size - 8))
        self._remove.setFixedSize(size, size)
        self._out.setIconSize(QSize(size - 8, size - 8))
        self._out.setFixedSize(size, size)
        self._iso.setIconSize(QSize(size - 8, size - 8))
        self._iso.setFixedSize(size, size)
        self._roi.setIconSize(QSize(size - 8, size - 8))
        self._roi.setFixedSize(size, size)
        self._cube.setIconSize(QSize(size - 8, size - 8))
        self._cube.setFixedSize(size, size)
        self._sphere.setIconSize(QSize(size - 8, size - 8))
        self._sphere.setFixedSize(size, size)
        self._duplicate.setIconSize(QSize(size - 8, size - 8))
        self._duplicate.setFixedSize(size, size)
        self._overlay.setIconSize(QSize(size - 8, size - 8))
        self._overlay.setFixedSize(size, size)
        self._export.setIconSize(QSize(size - 8, size - 8))
        self._export.setFixedSize(size, size)
        self._2roi.setIconSize(QSize(size - 8, size - 8))
        self._2roi.setFixedSize(size, size)

    def getCheckedMesh(self):
        meshes = list()
        for i in range(0, self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget.isChecked():
                meshes.append(widget.getMesh())
        return meshes

    def getSelectedMesh(self):
        return self._getSelectedWidget().getMesh()

    def setListROIAttributeWidget(self, widget):
        if isinstance(widget, ListROIAttributesWidget): self._listroiwidget = widget
        else: raise TypeError('parameter type {} is not ListROIAttributesWidget.'.format(type(widget)))

    def getListROIAttributeWidget(self):
        return self._listroiwidget

    def hasListROIAttributeWidget(self):
        return self._listroiwidget is not None

    def getTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabMeshListWidget
        if isinstance(parent, TabMeshListWidget):
            return parent

    def hasTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabMeshListWidget
        return isinstance(parent, TabMeshListWidget)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection): self._collection = views.getMeshCollection()
        else: self._collection = None

    def add(self, mesh):
        if self.hasViewCollection() and self.hasCollection():
            if isinstance(mesh, SisypheMesh):
                title = 'Add Mesh'
                vol = self._views.getVolume()
                if mesh.getReferenceID() == vol.getID():
                    if mesh.getName() not in self._collection:
                        view = self._views.getVolumeView()
                        if view is not None:
                            widget = self._addItem(mesh)
                            view.updateMeshes()
                            # bugfix 28/07/23
                            # view.addMesh(mesh)
                            return widget
                        mainwindow = self._getMainWindow()
                        if mainwindow is not None:
                            mainwindow.setStatusBarMessage('Mesh {} added.'.format(mesh.getName()))
                    else: QMessageBox.warning(self, title, '{} mesh is already open.'.format(mesh.getName()))
                else: QMessageBox.warning(self, title,
                                          '{} mesh does not belong to {} volume (ID mismatch).'.format(
                                              mesh.getName(),
                                              vol.getBasename()))
            else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def addOuterSurface(self):
        if self.hasViewCollection() and self.hasCollection():
            vol = self._views.getVolume()
            if vol is not None:
                mesh = SisypheMesh()
                wait = DialogWait(info='Outer surface mesh processing...', parent=self)
                wait.open()
                if self.hasTabToolsWidget():
                    settings = self.getTabToolsWidget().getSettingsWidget()
                    if settings.getParameterValue('Decimate') is False: decimate = 1.0
                    else: decimate = settings.getParameterValue('DecimatePercent')
                    if decimate is None: decimate = 1.0
                    if settings.getParameterValue('FillHoles') is False: fill = 0.0
                    else: fill = settings.getParameterValue('FillHolesSize')
                    if fill is None: fill = 0.0
                    clean = settings.getParameterValue('Clean')
                    if clean is None: clean = True
                    if settings.getParameterValue('Smooth') is False: smooth = ''
                    else: smooth = settings.getParameterValue('SmoothAlgorithm')
                    if smooth is None: smooth = ''
                    if smooth == 'Sinc': factor = settings.getParameterValue('SmoothPassBand')
                    else: factor = settings.getParameterValue('SmoothRelaxationFactor')
                    if factor is None: factor = 0.1
                    niter = settings.getParameterValue('SmoothIterations')
                    if niter is None: niter = 10
                    algo = settings.getParameterValue('IsosurfaceAlgorithm')[0]
                    if algo is None: algo = 'contour'
                    seg = settings.getParameterValue('SegmentationAlgorithm')[0]
                    if seg is None: seg = 'otsu'
                    mesh.createOuterSurface(vol, seg, fill, decimate, clean, smooth, niter, factor, algo)
                else: mesh.createOuterSurface(vol)
                self.add(mesh)
                wait.close()

    def addIsosurface(self):
        if self.hasViewCollection() and self.hasCollection():
            vol = self._views.getVolume()
            if vol is not None:
                self._dialog.setVolume(vol)
                self._dialog.setThresholdFlagToMinimum()
                if self._dialog.exec() == QDialog.Accepted:
                    value = self._dialog.getThreshold()
                    wait = DialogWait(info='Isosurface mesh processing...', parent=self)
                    wait.open()
                    mesh = SisypheMesh()
                    if self.hasTabToolsWidget():
                        settings = self.getTabToolsWidget().getSettingsWidget()
                        if settings.getParameterValue('Decimate') is False: decimate = 1.0
                        else: decimate = settings.getParameterValue('DecimatePercent')
                        if decimate is None: decimate = 1.0
                        if settings.getParameterValue('FillHoles') is False: fill = 0.0
                        else: fill = settings.getParameterValue('FillHolesSize')
                        if fill is None: fill = 0.0
                        clean = settings.getParameterValue('Clean')
                        if clean is None: clean = True
                        if settings.getParameterValue('Smooth') is False: smooth = ''
                        else: smooth = settings.getParameterValue('SmoothAlgorithm')
                        if smooth is None: smooth = ''
                        if smooth == 'Sinc': factor = settings.getParameterValue('SmoothPassBand')
                        else: factor = settings.getParameterValue('SmoothRelaxationFactor')
                        if factor is None: factor = 0.1
                        niter = settings.getParameterValue('SmoothIterations')
                        if niter is None: niter = 10
                        algo = settings.getParameterValue('IsosurfaceAlgorithm')[0]
                        if algo is None: algo = 'contour'
                        mesh.createIsosurface(vol, value, fill, decimate, clean, smooth, niter, factor, algo)
                    else: mesh.createIsosurface(vol, value)
                    self.add(mesh)
                    wait.close()

    def addRoi(self, rois):
        if self.hasViewCollection() and self.hasCollection():
            title = 'Mesh(es) from ROI(s)'
            vol = self._views.getVolume()
            if isinstance(rois, (list, tuple)):
                if len(rois) == 0:
                    # from disk
                    filenames = QFileDialog.getOpenFileNames(self, 'Open ROI(s)...', getcwd(),
                                                             filter='SisypheROI (*{})'.format(SisypheROI.getFileExt()))[0]
                    QApplication.processEvents()
                    n = len(filenames)
                    if n > 0:
                        chdir(dirname(filenames[0]))
                        rois = list()
                        for filename in filenames:
                            roi = SisypheROI()
                            roi.load(filename)
                            if roi.getReferenceID() == vol.getID(): rois.append(roi)
                            else:
                                QMessageBox.warning(self, title,
                                                    '{} ROI does not belong to {} volume (ID mismatch).'.format(
                                                        roi.getName(),
                                                        vol.getBasename()))
                if all([isinstance(roi, SisypheROI) for roi in rois]):
                    # from list
                    n = len(rois)
                    wait = DialogWait(info='Mesh(es) from ROI(s)...',
                                      progressmin=0, progressmax=n, cancel=True, parent=self)
                    wait.setProgressVisibility(n > 1)
                    wait.setButtonVisibility(n > 1)
                    wait.open()
                    for roi in rois:
                        wait.setInformationText('{} mesh processing...'.format(roi.getName()))
                        wait.incCurrentProgressValue()
                        if roi.getReferenceID() == vol.getID():
                            mesh = SisypheMesh()
                            if self.hasTabToolsWidget():
                                settings = self.getTabToolsWidget().getSettingsWidget()
                                if settings.getParameterValue('Decimate') is False: decimate = 1.0
                                else: decimate = settings.getParameterValue('DecimatePercent')
                                if decimate is None: decimate = 1.0
                                if settings.getParameterValue('FillHoles') is False: fill = 0.0
                                else: fill = settings.getParameterValue('FillHolesSize')
                                if fill is None: fill = 0.0
                                clean = settings.getParameterValue('Clean')
                                if clean is None: clean = True
                                if settings.getParameterValue('Smooth') is False: smooth = ''
                                else: smooth = settings.getParameterValue('SmoothAlgorithm')
                                if smooth is None: smooth = ''
                                if smooth == 'Sinc': factor = settings.getParameterValue('SmoothPassBand')
                                else: factor = settings.getParameterValue('SmoothRelaxationFactor')
                                if factor is None: factor = 0.1
                                niter = settings.getParameterValue('SmoothIterations')
                                if niter is None: niter = 10
                                algo = settings.getParameterValue('IsosurfaceAlgorithm')[0]
                                if algo is None: algo = 'contour'
                                mesh.createFromROI(roi, fill, decimate, clean, smooth, niter, factor, algo)
                            else: mesh.createFromROI(roi)
                            self.add(mesh)
                            if wait.getStopped(): break
                        else:
                            QMessageBox.warning(self, title,
                                                '{} ROI does not belong to {} volume (ID mismatch).'.format(
                                                    roi.getName(),
                                                    vol.getBasename()))
                    wait.close()
                else: raise TypeError('parameter type is not list of SisypheROI.')

    def addCube(self):
        if self.hasViewCollection() and self.hasCollection():
            vol = self._views.getVolume()
            if vol is not None:
                p = self._views.getVolumeView().getCursorWorldPosition()
                mesh = SisypheMesh()
                mesh.createCube(self._cubex.value(), self._cubey.value(), self._cubez.value(), p)
                # mesh.createCube(self._cubex.value(), self._cubey.value(), self._cubez.value())
                mesh.setReferenceID(vol.getID())
                # mesh.setPosition(p[0], p[1], p[2])
                mesh.setName('Cube#{}'.format(len(self.getCollection()) + 1))
                mesh.setFilename(join(vol.getDirname(), mesh.getName() + mesh.getFileExt()))
                self.add(mesh)

    def addSphere(self):
        if self.hasViewCollection() and self.hasCollection():
            vol = self._views.getVolume()
            if vol is not None:
                p = self._views.getVolumeView().getCursorWorldPosition()
                mesh = SisypheMesh()
                mesh.createSphere(self._spherer.value(), p)
                # mesh.createSphere(self._spherer.value())
                mesh.setReferenceID(vol.getID())
                # mesh.setPosition(p[0], p[1], p[2])
                mesh.setName('Sphere#{}'.format(len(self.getCollection()) + 1))
                mesh.setFilename(join(vol.getDirname(), mesh.getName() + mesh.getFileExt()))
                self.add(mesh)

    def duplicate(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Duplicate checked mesh(es)...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    wait.setInformationText('Duplicate {} mesh...'.format(mesh.getName()))
                    mesh2 = SisypheMesh()
                    mesh2.copyFrom(mesh)
                    mesh2.setName(mesh.getName() + str(len(self._collection) + 1))
                    mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh.getFileExt()))
                    self.add(mesh2)
                    wait.incCurrentProgressValue()
                wait.close()
            else: QMessageBox.warning(self, 'Duplicate checked mesh(es)', 'No selected mesh.')

    def addOverlay(self, vol):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                if isinstance(vol, str):
                    filename = vol
                    if filename == '' or not exists(filename):
                        dialog = DialogFileSelection(parent=self)
                        dialog.setWindowTitle('Display mesh overlay')
                        dialog.filterSisypheVolume()
                        if dialog.exec():
                            filename = dialog.getFilename()
                    if filename != '' and exists(filename):
                        vol = SisypheVolume()
                        vol.load(filename)
                elif isinstance(vol, SisypheVolume): vol = vol.copy()
                if vol is not None and isinstance(vol, SisypheVolume):
                    # Resample to reference volume
                    ref = self._views.getVolume()
                    if not vol.hasSameID(ref):
                        if ref.getID() in vol.getTransforms():
                            trf = vol.getTransformFromID(ref.getID())
                            from Sisyphe.core.sisypheTransform import SisypheApplyTransform
                            f = SisypheApplyTransform()
                            f.setTransform(trf)
                            f.setMoving(vol)
                            vol = f.execute(fixed=None, save=False)
                    # Apply overlay to mesh
                    wait = DialogWait(info='Display mesh overlay...', parent=self)
                    wait.setProgressVisibility(False)
                    wait.open()
                    for mesh in meshes:
                        wait.setInformationText('Display {} as {} mesh overlay...'.format(vol.getName(), mesh.getName()))
                        mesh2 = SisypheMesh()
                        mesh2.copyFrom(mesh)
                        mesh2.setPointScalarColorFromVolume(vol, wait=wait)
                        mesh2.setName('Overlay' + vol.getName() + mesh.getName())
                        mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                        widget = self.add(mesh2)
                        if widget is not None: widget.setLut(vol)
                    wait.close()
            else: QMessageBox.warning(self, 'Paint mesh(es) with overlay', 'No selected mesh.')

    def filter(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                if self.hasTabToolsWidget():
                    settings = self.getTabToolsWidget().getSettingsWidget()
                    if settings.getParameterValue('Decimate') is False: decimate = 1.0
                    else: decimate = settings.getParameterValue('DecimatePercent')
                    if decimate is None: decimate = 1.0
                    if settings.getParameterValue('FillHoles') is False: fill = 0.0
                    else: fill = settings.getParameterValue('FillHolesSize')
                    if fill is None: fill = 0.0
                    clean = settings.getParameterValue('Clean')
                    if clean is None: clean = True
                    if settings.getParameterValue('Smooth') is False: smooth = ''
                    else: smooth = settings.getParameterValue('SmoothAlgorithm')
                    if smooth is None: smooth = ''
                    if smooth == 'Sinc': factor = settings.getParameterValue('SmoothPassBand')
                    else: factor = settings.getParameterValue('SmoothRelaxationFactor')
                    if factor is None: factor = 0.1
                    niter = settings.getParameterValue('SmoothIterations')
                    if niter is None: niter = 10
                    wait = DialogWait(info='Filter checked mesh(es)...', parent=self)
                    wait.setProgressRange(0, n)
                    wait.setCurrentProgressValue(0)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    for mesh in meshes:
                        wait.setInformationText('Filter {} mesh...'.format(mesh.getName()))
                        mesh2 = SisypheMesh()
                        mesh2.copyFrom(mesh)
                        mesh2.filter(fill, decimate, clean, smooth, niter, factor)
                        mesh2.setName('Filter {}'.format(mesh.getName()))
                        mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                        self.add(mesh2)
                        wait.incCurrentProgressValue()
                    wait.close()
            else: QMessageBox.warning(self, 'Filter checked mesh(es)', 'No checked mesh.')

    def dilate(self, mm=1.0):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Dilate checked mesh(es)...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    wait.setInformationText('Dilate {} mesh...'.format(mesh.getName()))
                    mesh2 = SisypheMesh()
                    mesh2.copyFrom(mesh)
                    mesh2.dilate(mm)
                    mesh2.setName('Dilate#{} {}'.format(mm, mesh.getName()))
                    mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                    self.add(mesh2)
                    wait.incCurrentProgressValue()
                wait.close()
            else: QMessageBox.warning(self, 'Dilate checked mesh(es)', 'No checked mesh.')

    def erode(self, mm=1.0):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Erode checked mesh(es)...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    wait.setInformationText('Erode {} mesh...'.format(mesh.getName()))
                    mesh2 = SisypheMesh()
                    mesh2.copyFrom(mesh)
                    mesh2.erode(mm)
                    mesh2.setName('Erode#{} {}'.format(mm, mesh.getName()))
                    mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                    self.add(mesh2)
                    wait.incCurrentProgressValue()
                wait.close()
            else: QMessageBox.warning(self, 'Erode checked mesh(es)', 'No checked mesh.')

    def union(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 1:
                wait = DialogWait(info='Checked mesh(es) union...', parent=self)
                wait.open()
                mesh2 = SisypheMesh()
                mesh2.copyFrom(meshes[0])
                meshes = meshes[1:]
                mesh2.union(meshes)
                wait.close()
                if not mesh2.isEmpty():
                    mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                    self.add(mesh2)
                else: QMessageBox.warning(self, 'Checked mesh(es) intersection', 'Mesh intersection is empty.')
            else: QMessageBox.warning(self, 'Checked mesh(es) union', 'Less than two meshes checked.')

    def intersection(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 1:
                wait = DialogWait(info='Checked mesh(es) intersection...', parent=self)
                wait.open()
                mesh2 = SisypheMesh()
                mesh2.copyFrom(meshes[0])
                meshes = meshes[1:]
                mesh2.intersection(meshes)
                wait.close()
                if not mesh2.isEmpty():
                    mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                    self.add(mesh2)
                else: QMessageBox.warning(self, 'Checked mesh(es) intersection', 'Mesh intersection is empty.')
            else: QMessageBox.warning(self, 'Checked mesh(es) intersection', 'Less than two meshes checked.')

    def difference(self):
        if self.hasViewCollection() and self.hasCollection():
            s = self.getSelectedMesh()
            if s is not None:
                mesh2 = SisypheMesh()
                mesh2.copyFrom(s)
                meshes = self.getCheckedMesh()
                n = len(meshes)
                if n > 0:
                    wait = DialogWait(info='Mesh(es) difference...', parent=self)
                    wait.open()
                    mesh2.difference(meshes)
                    wait.close()
                    if not mesh2.isEmpty():
                        mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                        self.add(mesh2)
                    else: QMessageBox.warning(self, 'Mesh(es) difference', 'Mesh difference is empty')
                else: QMessageBox.warning(self, 'Mesh(es) difference', 'No checked mesh.')
            else: QMessageBox.warning(self, 'Mesh(es) difference', 'No selected mesh.')

    def features(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                dialog = DialogGenericResults()
                dialog.newTab('Mesh features', capture=False, clipbrd=False, scrshot=False, dataset=True)
                dialog.newTab('Mesh surface to surface distances', capture=False, clipbrd=False, scrshot=False, dataset=True)
                dialog.hideFigure(0)
                dialog.hideFigure(1)
                dialog.setTreeWidgetHeaderLabels(0, ['Mesh', 'Volume', 'Surface', 'Bounds', 'Center of mass',
                                                     'Major axis', 'Mid axis', 'Minor axis', 'Sizes'],
                                                 units=['', 'mm3', 'mm2', 'mm', 'mm', '', '', '', 'mm'],
                                                 charts=['', 'bar', 'bar', 'plot', 'plot', 'plot', 'plot', 'plot', 'bar'])
                h = ['Mesh']
                for mesh in meshes:
                    h.append(mesh.getName())
                dialog.setTreeWidgetHeaderLabels(1, h)
                wait = DialogWait(info='Checked mesh(es) features...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    wait.setInformationText('{} features processing...'.format(mesh.getName()))
                    wait.incCurrentProgressValue()
                    row = list()
                    row.append(mesh.getName())
                    row.append(mesh.getMeshVolume())
                    row.append(mesh.getMeshSurface())
                    row.append(mesh.getBounds())
                    row.append(mesh.getCenterOfMass())
                    pca = mesh.getPrincipalAxis()
                    row.append(pca[1])  # Major axis
                    row.append(pca[2])  # Mid axis
                    row.append(pca[3])  # Minor axis
                    row.append(pca[4])  # Sizes
                    dialog.addTreeWidgetRow(0, row)
                    row = list()
                    h.append(mesh.getName())
                    row.append(mesh.getName())
                    for mesh2 in meshes:
                        if mesh2 != mesh:
                            wait.setInformationText('Minimal distance between {} and {}...'.format(mesh.getName(),
                                                                                                   mesh2.getName()))
                            vmin, vmax = mesh.getDistanceFromSurfaceToSurface(mesh2)
                            row.append(vmin)
                        else: row.append(0)
                    dialog.addTreeWidgetRow(1, row)
                dialog.autoSize(0)
                wait.close()
                dialog.exec()
            else: QMessageBox.warning(self, 'Mesh features', 'No checked mesh.')

    def saveOBJ(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Export checked mesh(es) to OBJ format...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to OBJ format...'.format(item.getName()))
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToOBJ(join(path, mesh.getName()))
                    item.saveToOBJ(item.getFilename())
                    wait.incCurrentProgressValue()
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to OBJ format.')
            else: QMessageBox.warning(self, 'Export to OBJ format', 'No checked mesh.')

    def saveSTL(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Export checked mesh(es) to STL format...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to STL format...'.format(item.getName()))
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToSTL(join(path, mesh.getName()))
                    item.saveToSTL(item.getFilename())
                    wait.incCurrentProgressValue()
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to STL format.')
            else: QMessageBox.warning(self, 'Export to STL format', 'No checked mesh.')

    def saveVTK(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if len(meshes) > 0:
                wait = DialogWait(info='Export checked mesh(es) to VTK format...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to VTK format...'.format(item.getName()))
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToVTK(join(path, mesh.getName()))
                    item.saveToVTK(item.getFilename())
                    wait.incCurrentProgressValue()
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to VTK format.')
            else: QMessageBox.warning(self, 'Export to VTK format', 'No checked mesh.')

    def saveXMLVTK(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Export checked mesh(es) to XMLVTK format...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to XMLVTK format...'.format(item.getName()))
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToXMMLVTK(join(path, mesh.getName()))
                    item.saveToXMLVTK(item.getFilename())
                    wait.incCurrentProgressValue()
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to XMLVTK format.')
            else: QMessageBox.warning(self, 'Export to XMLVTK format', 'No checked mesh.')

    def open(self):
        if self.hasViewCollection() and self.hasCollection():
            title = 'Open mesh(es)'
            filt = 'Mesh (*{})'.format(SisypheMesh.getFileExt())
            filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
            QApplication.processEvents()
            if filenames:
                n = len(filenames)
                chdir(dirname(filenames[0]))
                wait = DialogWait(info='Open mesh(es)...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for filename in filenames:
                    mesh = SisypheMesh()
                    try:
                        wait.setInformationText('Open {}...'.format(basename(filename)))
                        mesh.load(filename)
                        self.add(mesh)
                    except Exception as err:
                        QMessageBox.warning(self, title, '{}'.format(err))
                    wait.incCurrentProgressValue()
                wait.close()

    def remove(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                view = self._views.getVolumeView()
                if view is not None:
                    for mesh in meshes:
                        view.removeMesh(mesh)
                super().remove()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Checked mesh(es) removed.')

    def removeItem(self, w):
        if self.hasViewCollection() and self.hasCollection():
            mesh = w.getMesh()
            view = self._views.getVolumeView()
            if view is not None:
                view.removeMesh(mesh)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} mesh removed.'.format(mesh.getName()))
            super().removeItem(w)

    def removeAll(self):
        if self._views is not None:
            view = self._views.getVolumeView()
            if view is not None: view.removeAllMeshes()
        super().removeAll()
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setStatusBarMessage('All Mesh(es) removed.')

    def toRoi(self):
        if self.hasViewCollection() and self._listroiwidget is not None:
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                ref = self.getViewCollection().getVolume()
                wait = DialogWait(info='Mesh to ROI processing...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    wait.setInformationText('{} to ROI processing...'.format(mesh.getName()))
                    roi = mesh.convertToSisypheROI(ref)
                    self._listroiwidget.add(roi)
                    wait.incCurrentProgressValue()
                wait.close()
            else: QMessageBox.warning(self, 'Mesh to ROI conversion', 'No checked mesh.')
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Mesh(es) converted to ROI(s).')

    # Qt event

    def dropEvent(self, event):
        if self.hasViewCollection():
            if event.mimeData().hasText():
                event.acceptProposedAction()
                files = event.mimeData().text().split('\n')
                for file in files:
                    if file != '':
                        filename = file.replace('file://', '')
                        if splitext(filename)[1] == SisypheMesh.getFileExt():
                            title = 'Open mesh'
                            mesh = SisypheMesh()
                            try:
                                mesh.load(filename)
                                self.add(mesh)
                            except Exception as err:
                                QMessageBox.warning(self, title, '{}'.format(err))
            else: event.ignore()

    # Method aliases

    getMesh = ListAttributesWidget.getItem


class ListToolAttributesWidget(ListAttributesWidget):
    """
        ListToolAttributesWidget

        Description

            Class to manage a list of ItemToolAttributesWidget.

        Inheritance

            QWidget -> ListAttributesWidget -> ListToolAttributesWidget

        Private attributes

        Public methods

            getCheckedTool()
            getSelectedTool()
            getTabToolsWidget()
            bool = hasTabToolsWidget()
            newHandle()
            newLine()
            add(HandleWidget | LineWidget)
            open()
            remove()
            removeAll()
            save()

            inherited ListAttributesWidget
            inherited QWidget methods

        Revision:

            11/08/2023  add removeItem() method
            06/09/2023  remove() method bugfix
            24/09/2023  features() method bugfix
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._filename = ''

        if self._views is not None:
            view = self._views.getVolumeView()
            view.ToolColorChanged.connect(self._synchroniseToolColorChanged)
            # view.ToolRemoved.connect(self._synchroniseToolRemoved)

        self._target = IconPushButton('target.png', size=ListAttributesWidget._VSIZE)
        self._trajectory = IconPushButton('line.png', size=ListAttributesWidget._VSIZE)
        self._remove = IconPushButton('cross.png', size=ListAttributesWidget._VSIZE)
        self._duplicate = IconPushButton('duplicate.png', size=ListAttributesWidget._VSIZE)
        self._features = IconPushButton('toolfeature.png', size=ListAttributesWidget._VSIZE)
        self._features2 = IconPushButton('toolfeature2.png', size=ListAttributesWidget._VSIZE)

        self._target.clicked.connect(self.newHandle)
        self._trajectory.clicked.connect(self.newLine)
        self._remove.clicked.connect(self.remove)
        self._duplicate.clicked.connect(self.duplicate)
        self._features.clicked.connect(self.features)
        self._features2.clicked.connect(self.features2)

        self._target.setToolTip('Add new target tool')
        self._trajectory.setToolTip('Add new trajectory tool')
        self._remove.setToolTip('Remove checked tool(s)')
        self._duplicate.setToolTip('Duplicate selected tool')
        self._features.setToolTip('Tool features')
        self._features2.setToolTip('Tool and mesh relationships')

        self._new.setVisible(False)
        self._btlayout1.insertWidget(4, self._remove)
        self._btlayout2.insertWidget(2, self._features2)
        self._btlayout2.insertWidget(2, self._features)
        self._btlayout2.insertWidget(2, self._duplicate)
        self._btlayout2.insertWidget(2, self._trajectory)
        self._btlayout2.insertWidget(2, self._target)

        self._open.setToolTip('{} tool(s)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} tool(s)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} tool(s)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} tool(s)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} tool(s)'.format(self._uncheckall.toolTip()))

        self._dialogtarget = DialogTarget()
        self._dialogduplicate = DialogFromXml('Duplicate tool', ['DuplicateTool'])

        self._dialogfeatures = DialogGenericResults()

    # Private methods

    def _synchroniseToolColorChanged(self, widget, tool):
        if not self.isEmpty():
            for i in range(self.count()):
                if self.getTool(i).getName() == tool.getName():
                    w = self.getWidget(i)
                    c = tool.getColor()
                    if w.getColor() != c:
                        w.setColor(c[0], c[1], c[2], signal=False)

    def _synchroniseToolRemoved(self, widget, tool, all):
        if not self.isEmpty() and tool is not None:
            for i in range(self.count()):
                if self.getTool(i).getName() == tool.getName():
                    w = self.getWidget(i)
                    ListAttributesWidget.removeItem(self, w)

    def _createWidget(self, item):
        return ItemToolAttributesWidget(item, views=self._views, listattr=self)

    def _updateViews(self):
        if self.hasViewCollection():
            self._views.updateRender()

    def _updateTargets(self, widget, tool):
        if self.hasViewCollection():
            if len(self._collection) > 0:
                for i in range(len(self._list)):
                    w = self.getWidget(i)
                    itool = w.getTool()
                    if itool != tool:
                        dlg = w.getDialogTarget()
                        if dlg.isRelativeOrWeightedPosition():
                            if dlg.isWeightedPosition(): dlg._initPoints()
                            r = dlg.getAttributes()
                            if isinstance(itool, HandleWidget):
                                self._views.getVolumeView().moveTool(itool, target=r['target'])
                            elif isinstance(itool, LineWidget):
                                self._views.getVolumeView().moveTool(itool, target=r['target'], entry=r['entry'])

    # Public methods

    def setIconSize(self, size=ListAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._target.setIconSize(QSize(size - 8, size - 8))
        self._target.setFixedSize(size, size)
        self._trajectory.setIconSize(QSize(size - 8, size - 8))
        self._trajectory.setFixedSize(size, size)
        self._remove.setIconSize(QSize(size - 8, size - 8))
        self._remove.setFixedSize(size, size)
        self._duplicate.setIconSize(QSize(size - 8, size - 8))
        self._duplicate.setFixedSize(size, size)
        self._features.setIconSize(QSize(size - 8, size - 8))
        self._features.setFixedSize(size, size)
        self._features2.setIconSize(QSize(size - 8, size - 8))
        self._features2.setFixedSize(size, size)

    def getCheckedTool(self):
        tools = list()
        for i in range(0, self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget.isChecked():
                tools.append(widget.getTool())
        if len(tools) > 0: return tools
        else: return None

    def getSelectedTool(self):
        return self._getSelectedWidget().getTool()

    def getTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabTargetListWidget
        if isinstance(parent, TabTargetListWidget):
            return parent

    def hasTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabTargetListWidget
        return isinstance(parent, TabTargetListWidget)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection):
            self._collection = views.getToolCollection()
            self._dialogtarget.setViewCollection(views)
            view = self._views.getVolumeView()
            view.ToolColorChanged.connect(self._synchroniseToolColorChanged)
            # view.ToolRemoved.connect(self._synchroniseToolRemoved)
        else: self._collection = None

    def newHandle(self):
        if self.hasViewCollection():
            self._dialogtarget.hideTrajectoryFields()
            self._dialogtarget.clear()
            self._dialogtarget.setDefaultPosition()
            if self._dialogtarget.exec() == QDialog.Accepted:
                view = self._views.getVolumeView()
                if view is not None:
                    p = self._dialogtarget.getTargetPosition()
                    item = view.addTarget(p)
                    widget = self._addItem(item)
                    widget.setLock(self._dialogtarget.isRelativeOrWeightedPosition())
                    widget.getDialogTarget().copyFieldsFrom(self._dialogtarget)
                    widget.setDefaultAttributesFromSettings()
                    widget.focusTarget()
                    # to update relative tools position
                    view.ToolMoved.connect(self._updateTargets)
                    slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                    if slcviews is not None:
                        slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                        slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                        slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('Add new point {}.'.format(item.getName()))

    def newLine(self):
        if self.hasViewCollection():
            self._dialogtarget.showTrajectoryFields()
            self._dialogtarget.clear()
            self._dialogtarget.setDefaultPosition()
            if self._dialogtarget.exec() == QDialog.Accepted:
                view = self._views.getVolumeView()
                if view is not None:
                    r = self._dialogtarget.getAttributes()
                    item = view.addTrajectory(p1=r['entry'], p2=r['target'])
                    widget = self._addItem(item)
                    widget.setLock(self._dialogtarget.isRelativeOrWeightedPosition())
                    widget.getDialogTarget().copyFieldsFrom(self._dialogtarget)
                    widget.setDefaultAttributesFromSettings()
                    widget.focusTarget()
                    # to update relative tools position
                    view.ToolMoved.connect(self._updateTargets)
                    slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                    if slcviews is not None:
                        slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                        slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                        slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('Add new trajectory {}.'.format(item.getName()))

    def open(self):
        if self.hasViewCollection():
            title = 'Open tool(s)'
            filt = '{};;{};;{}'.format(ToolWidgetCollection.getFilterExt(),
                                       HandleWidget.getFilterExt(),
                                       LineWidget.getFilterExt())
            filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
            QApplication.processEvents()
            if filenames:
                n = len(filenames)
                chdir(dirname(filenames[0]))
                wait = DialogWait(info='Open tool(s)...', parent=self)
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    ext = splitext(filename)[1]
                    view = self._views.getVolumeView()
                    if view is not None:
                        if ext == ToolWidgetCollection.getFileExt():
                            tools = ToolWidgetCollection()
                            try: tools.load(filename)
                            except Exception as err:
                                QMessageBox.warning(self, 'open tools', '{}'.format(err))
                                tools = None
                            vol = self._views.getVolume()
                            if tools is not None and vol is not None:
                                if tools.hasSameID(vol):
                                    for tool in tools:
                                        if isinstance(tool, HandleWidget):
                                            p = tool.getPosition()
                                            item = view.addTarget(p, tool.getName())
                                            tool.copyAttributesTo(item)
                                            widget = self._addItem(item)
                                            widget.getDialogTarget().setAbsolutePosition(p)
                                            widget.updateSettingsFromAttributes()
                                            # to update relative tools position
                                            view.ToolMoved.connect(self._updateTargets)
                                            slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                            if slcviews is not None:
                                                slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                        elif isinstance(tool, LineWidget):
                                            p = tool.getPosition2()
                                            item = view.addTrajectory(p1=tool.getPosition1(),
                                                                      p2=p,
                                                                      name=tool.getName())
                                            tool.copyAttributesTo(item)
                                            widget = self._addItem(item)
                                            widget.getDialogTarget().setAbsolutePosition(p)
                                            widget.updateSettingsFromAttributes()
                                            # to update relative tools position
                                            view.ToolMoved.connect(self._updateTargets)
                                            slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                            if slcviews is not None:
                                                slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                else:
                                    QMessageBox.warning(self, 'Open tools',
                                                        '{} tools does not belong to {} volume (ID mismatch).'.format(
                                                            basename(filename),
                                                            vol.getBasename()))
                        elif ext == HandleWidget.getFileExt():
                            tool = HandleWidget('')
                            try: tool.load(filename)
                            except Exception as err:
                                QMessageBox.warning(self, 'open tools', '{}'.format(err))
                                tool = None
                            if tool is not None:
                                p = tool.getPosition()
                                item = view.addTarget(p, tool.getName())
                                tool.copyAttributesTo(item)
                                widget = self._addItem(item)
                                widget.getDialogTarget().setAbsolutePosition(p)
                                widget.focusTarget()
                                widget.updateSettingsFromAttributes()
                                # to update relative tools position
                                view.ToolMoved.connect(self._updateTargets)
                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                if slcviews is not None:
                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                        elif ext == LineWidget.getFileExt():
                            tool = LineWidget('')
                            try: tool.load(filename)
                            except Exception as err:
                                QMessageBox.warning(self, 'open tools', '{}'.format(err))
                                tool = None
                            if tool is not None:
                                p = tool.getPosition2()
                                item = view.addTrajectory(p1=tool.getPosition1(),
                                                          p2=p,
                                                          name=tool.getName())
                                tool.copyAttributesTo(item)
                                widget = self._addItem(item)
                                widget.getDialogTarget().setAbsolutePosition(p)
                                widget.focusTarget()
                                widget.updateSettingsFromAttributes()
                                # to update relative tools position
                                view.ToolMoved.connect(self._updateTargets)
                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                if slcviews is not None:
                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                    wait.incCurrentProgressValue()
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('open tool(s).')
                wait.close()

    def duplicate(self):
        if self.hasViewCollection():
            tool = self.getSelectedTool()
            if tool is not None:
                settings = self._dialogduplicate.getFieldsWidget(0)
                vol = self._views.getVolume()
                if vol is not None: settings.getParameterWidget('Orientation').setVisible(vol.getACPC().hasACPC())
                if self._dialogduplicate.exec() == QDialog.Accepted:
                    lat = settings.getParameterValue('Laterality')
                    if lat is None: lat = 0.0
                    ap = settings.getParameterValue('Antero-posterior')
                    if ap is None: ap = 0.0
                    h = settings.getParameterValue('Height')
                    if h is None: h = 0.0
                    o = settings.getParameterValue('Orientation')[0]
                    if o is None: o = 'Native'
                    from Sisyphe.widgets.toolWidgets import HandleWidget
                    from Sisyphe.widgets.toolWidgets import LineWidget
                    if o == 'Native':
                        if isinstance(tool, HandleWidget):
                            p = list(tool.getPosition())
                            p[0] += lat
                            p[1] += ap
                            p[2] += h
                            item = self._views.getVolumeView().addTarget(p)
                            if lat == ap == h == 0.0: item.setName('{} copy'.format(tool.getName()))
                            else: item.setName('{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h))
                            self._addItem(item)
                        elif isinstance(tool, LineWidget):
                            p1 = list(tool.getPosition1())
                            p2 = list(tool.getPosition2())
                            p1[0] += lat
                            p1[1] += ap
                            p1[2] += h
                            p2[0] += lat
                            p2[1] += ap
                            p2[2] += h
                            item = self._views.getVolumeView().addTrajectory(p1, p2)
                            if lat == ap == h == 0.0: item.setName('{} copy'.format(tool.getName()))
                            else: item.setName('{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h))
                            self._addItem(item)
                    elif o == 'Camera':
                        v0 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane().GetNormal()
                        v1 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane().GetNormal()
                        v2 = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane().GetNormal()
                        if isinstance(self._item, HandleWidget):
                            p = list(self._item.getPosition())
                            p[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            item = self._views.getVolumeView().addTarget(p)
                            self._addItem(item)
                        elif isinstance(self._item, LineWidget):
                            p1 = list(self._item.getPosition1())
                            p2 = list(self._item.getPosition2())
                            p1[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p1[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p1[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            p2[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                            p2[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                            p2[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                            item = self._views.getVolumeView().addTrajectory(p1, p2)
                            self._addItem(item)
                    else:
                        if isinstance(tool, HandleWidget):
                            p = list(tool.getPosition())
                            p = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p)
                            item = self._views.getVolumeView().addTarget(p)
                            if lat == ap == h == 0.0: item.setName('{} copy'.format(tool.getName()))
                            else: item.setName('{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h))
                            self._addItem(item)
                        elif isinstance(tool, LineWidget):
                            p1 = list(tool.getPosition1())
                            p2 = list(tool.getPosition2())
                            p1 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p1)
                            p2 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p2)
                            item = self._views.getVolumeView().addTrajectory(p1, p2)
                            if lat == ap == h == 0.0: item.setName('{} copy'.format(tool.getName()))
                            else: item.setName('{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h))
                            self._addItem(item)
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('Duplicate tool.')

    def features(self):

        def toStr(v):
            return '{:.1f} {:.1f} {:.1f}'.format(v[0], v[1], v[2])

        if self.hasViewCollection():
            if len(self._collection) > 0:
                self._dialogfeatures.clear()
                from Sisyphe.widgets.toolWidgets import HandleWidget
                from Sisyphe.widgets.toolWidgets import LineWidget
                vol = self._views.getVolume()
                """      
                    Coordinates, page #0           
                """
                self._dialogfeatures.newTab('Coordinates',
                                            capture=False, clipbrd=False,
                                            scrshot=self._scrsht, dataset=True)
                self._dialogfeatures.hideFigure(0)
                h = ['Tools', 'World', 'Image', 'Leksell', 'AC', 'PC', 'Mid AC-PC', 'Length', 'Sagittal angle', 'Coronal angle']
                self._dialogfeatures.setTreeWidgetHeaderLabels(0, labels=h)
                for tool in self._collection:
                    if isinstance(tool, (LineWidget, HandleWidget)):
                        if isinstance(tool, HandleWidget): n = 1
                        else:  n = 2
                        for i in range(n):
                            r = list()
                            # Name column
                            if n == 1: r.append(tool.getName())
                            else: r.append('{} {}'.format(tool.getName(), tool.getLegend()[i]))
                            # World coordinate column
                            if n == 1: p = tool.getPosition()
                            else:
                                if i == 0: p = tool.getPosition2()
                                else: p = tool.getPosition1()
                            r.append(toStr(p))
                            # Image coordinate column
                            s = vol.getSpacing()
                            p2 = list(p)
                            p2[0] /= s[0]
                            p2[1] /= s[1]
                            p2[2] /= s[2]
                            r.append(toStr(p2))
                            # Leksell coordinate column
                            if vol.hasLEKSELLTransform():
                                p2 = vol.getLEKSELLfromWorld(p)
                                r.append(toStr(p2))
                            else: r.append('NA')
                            # AC reference column
                            acpc = vol.getACPC()
                            if acpc.hasACPC():
                                p2 = acpc.getRelativeDistanceFromAC(p)
                                r.append(toStr(p2))
                            else: r.append('NA')
                            # PC reference column
                            if acpc.hasACPC():
                                p2 = acpc.getRelativeDistanceFromPC(p)
                                r.append(toStr(p2))
                            else: r.append('NA')
                            # Mid AC-PC column
                            if acpc.hasACPC():
                                p2 = acpc.getRelativeDistanceFromMidACPC(p)
                                r.append(toStr(p2))
                            else: r.append('NA')
                            # Length, sagittal angle, coronal angle
                            if n == 2:
                                r.append(tool.getLength())
                                a = tool.getTrajectoryAngles()
                                r.append(a[0])
                                r.append(a[1])
                            else: r += ['NA'] * 3
                            self._dialogfeatures.addTreeWidgetRow(0, r, d=1)
                """           
                    Distances, page #1         
                """
                self._dialogfeatures.newTab('Distances',
                                            capture=False, clipbrd=False,
                                            scrshot=self._scrsht, dataset=True)
                self._dialogfeatures.hideFigure(1)
                h = ['Tools']
                for tool in self._collection:
                    if isinstance(tool, HandleWidget): h.append(tool.getName())
                    elif isinstance(tool, LineWidget):
                        legend = tool.getLegend()
                        h.append('{} {}'.format(tool.getName(), legend[0]))
                        h.append('{} {}'.format(tool.getName(), legend[1]))
                        h.append('{} Line'.format(tool.getName()))
                self._dialogfeatures.setTreeWidgetHeaderLabels(1, h)
                n = self._collection.count()
                for i in range(n):
                    toolr = self._collection[i]
                    if isinstance(toolr, (LineWidget, HandleWidget)):
                        dr = None
                        if isinstance(toolr, HandleWidget): nr = 1
                        elif isinstance(toolr, LineWidget): nr = 3
                        else: nr = 0
                        for subi in range(nr):
                            if nr == 1: r = [toolr.getName()]
                            else:
                                if subi == 0: r = ['{} {}'.format(toolr.getName(), toolr.getLegend()[0])]
                                elif subi == 1: r = ['{} {}'.format(toolr.getName(), toolr.getLegend()[1])]
                                else: r = ['{} {}'.format(toolr.getName(), 'Line')]
                            for j in range(n):
                                toolc = self._collection[j]
                                if isinstance(toolc, (LineWidget, HandleWidget)):
                                    dc = None
                                    if isinstance(toolc, HandleWidget): nc = 1
                                    elif isinstance(toolc, LineWidget): nc = 3
                                    else: nc = 0
                                    for subj in range(nc):
                                        if toolc == toolr: r.append('')
                                        else:
                                            # column toolc HandleWidget, row toolr HandleWidget
                                            if nc == 1 and nr == 1: r.append(toolc.getDistanceToHandleWidget(toolr))
                                            # column toolc HandleWidget, row toolr LineWidget
                                            elif nc == 1 and nr == 3:
                                                # toolr target, toolc point
                                                if subi == 0: r.append(toolc.getDistanceToPoint(toolr.getPosition2()))
                                                # toolr entry, toolc point
                                                elif subi == 1: r.append(toolc.getDistanceToPoint(toolr.getPosition1()))
                                                # toolr line, toolc point
                                                else: r.append(toolc.getDistanceToLineWidget(toolr)[0])
                                            # column toolc LineWidget, row toolr HandleWidget
                                            elif nc == 3 and nr == 1:
                                                # toolc target, toolr point
                                                if subj == 0: r.append(toolr.getDistanceToPoint(toolc.getPosition2()))
                                                # toolc entry, toolr point
                                                elif subj == 1: r.append(toolr.getDistanceToPoint(toolc.getPosition1()))
                                                # toolc line, toolr point
                                                else: r.append(toolr.getDistanceToLineWidget(toolc)[0])
                                            # column toolc LineWidget, row toolr LineWidget
                                            elif nc == 3 and nr == 3:
                                                if dr is None: dr = toolr.getDistancesToLineWidget(toolc)
                                                if dc is None: dc = toolc.getDistancesToLineWidget(toolr)
                                                """
                                                    dr[0], distance between toolc line and toolr entry
                                                    dr[1], distance between toolc line and toolr target
                                                    dr[2], distance between toolc line and toolr line
                                                    dr[3], distance between toolc entry and toolr entry
                                                    dr[4], distance between toolc entry and toolr target
                                                    dr[5], distance between toolc target and toolr entry
                                                    dr[6], distance between toolc target and toolr target

                                                    dc[0], distance between toolr line and toolc entry
                                                    dc[1], distance between toolr line and toolc target
                                                    dc[2], distance between toolr line and toolc line
                                                """
                                                # toolr target
                                                if subi == 0:
                                                    # toolr target, toolc target
                                                    if subj == 0: r.append(dr[6])
                                                    # toolr target, toolc entry
                                                    elif subj == 1: r.append(dr[4])
                                                    # toolr target,  toolc line
                                                    else: r.append(dr[1])
                                                # toolr entry
                                                elif subi == 1:
                                                    # toolr entry, toolc target
                                                    if subj == 0: r.append(dr[5])
                                                    # toolr entry, toolc entry
                                                    elif subj == 1: r.append(dr[3])
                                                    # toolr entry, toolc line
                                                    else: r.append(dr[0])
                                                # toolr line
                                                elif subi == 2:
                                                    # toolr line, toolc target
                                                    if subj == 0: r.append(dc[1])
                                                    # toolr line, toolc entry
                                                    elif subj == 1: r.append(dc[0])
                                                    # toolr line, toolc line
                                                    else: r.append(dr[2])
                            self._dialogfeatures.addTreeWidgetRow(1, r, d=1)
                """                  
                    Display dialog                    
                """
                self._dialogfeatures.autoSize(0)
                self._dialogfeatures.exec()

    def features2(self):
        if self.hasViewCollection():
            if len(self._collection) > 0:
                self._dialogfeatures.clear()
                meshes = self._views.getMeshCollection()
                if meshes is not None and len(meshes) > 0:
                    wait = DialogWait(info='Tool and mesh relationships estimation...', parent=self)
                    wait.open()
                    h = list()
                    h.append('Tools')
                    for mesh in meshes:
                        h.append(mesh.getName())
                    """
                        Inside, page #0
                        Distance to surface, page #1
                        Distance to center of mass, page #2
                    """
                    self._dialogfeatures.newTab('Inside mesh',
                                                capture=False, clipbrd=False,
                                                scrshot=self._scrsht, dataset=True)
                    self._dialogfeatures.newTab('Distance to mesh surface',
                                                capture=False, clipbrd=False,
                                                scrshot=self._scrsht, dataset=True)
                    self._dialogfeatures.newTab('Distance to mesh center of mass',
                                                capture=False, clipbrd=False,
                                                scrshot=self._scrsht, dataset=True)
                    self._dialogfeatures.hideFigure(0)
                    self._dialogfeatures.hideFigure(1)
                    self._dialogfeatures.hideFigure(2)
                    self._dialogfeatures.setTreeWidgetHeaderLabels(0, h)
                    self._dialogfeatures.setTreeWidgetHeaderLabels(1, h)
                    self._dialogfeatures.setTreeWidgetHeaderLabels(2, h)
                    from Sisyphe.widgets.toolWidgets import HandleWidget
                    from Sisyphe.widgets.toolWidgets import LineWidget
                    for tool in self._collection:
                        if isinstance(tool, (HandleWidget, LineWidget)):
                            r0 = list()
                            r1 = list()
                            r2 = list()
                            r0.append(tool.getName())
                            r1.append(tool.getName())
                            r2.append(tool.getName())
                            for mesh in meshes:
                                if isinstance(tool, HandleWidget): p = tool.getPosition()
                                else: p = tool.getPosition2()
                                r0.append(str(mesh.isPointInside(p)))
                                r1.append(mesh.getDistanceFromSurfaceToPoint(p)[0])
                                p = mesh.getCenterOfMass()
                                if isinstance(tool, HandleWidget): r2.append(tool.getDistanceToPoint(p))
                                else: r2.append(tool.getDistancesToPoint(p)[1])
                            self._dialogfeatures.addTreeWidgetRow(0, r0, d=0)
                            self._dialogfeatures.addTreeWidgetRow(1, r1, d=1)
                            self._dialogfeatures.addTreeWidgetRow(2, r2, d=1)
                    """
                        Display dialog
                    """
                    wait.close()
                    self._dialogfeatures.autoSize(0)
                    self._dialogfeatures.exec()

    def remove(self):
        if self.hasViewCollection():
            tools = self.getCheckedTool()
            if tools is not None and len(tools) > 0:
                for tool in tools:
                    self._views.getFirstSliceView().removeTool(tool.getName())
                    super().remove()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Tool(s) removed.')

    def removeItem(self, w):
        if self.hasViewCollection():
            tool = w.getTool()
            self._views.getVolumeView().removeTool(tool.getName())
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} tool removed.'.format(tool.getName()))
            super().removeItem(w)

    def removeAll(self):
        if self.hasViewCollection():
            self._views.getVolumeView().removeAllTools()
        super().removeAll()
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setStatusBarMessage('All tool(s) removed.')

    def saveAll(self):
        if self.hasViewCollection():
            vol = self._views.getVolume()
            if vol is not None:
                if self._filename != '': filename = self._filename
                else: filename = vol.getFilename().replace(vol.getFileExt(), self._collection.getFileExt())
                filename = QFileDialog.getSaveFileName(self, 'Save tools', filename, ToolWidgetCollection.getFilterExt())[0]
                if filename:
                    wait = DialogWait(info='Save {}...'.format(basename(filename)), parent=self)
                    wait.open()
                    self._collection.setReferenceID(vol)
                    self._collection.saveAs(filename)
                    self._filename = filename
                    wait.close()
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('Tools {} saved.'.format(basename(filename)))

    # Qt event

    def dropEvent(self, event):
        if self.hasViewCollection():
            if event.mimeData().hasText():
                event.acceptProposedAction()
                files = event.mimeData().text().split('\n')
                for file in files:
                    if file != '':
                        filename = file.replace('file://', '')
                        from Sisyphe.widgets.toolWidgets import HandleWidget
                        from Sisyphe.widgets.toolWidgets import LineWidget
                        from Sisyphe.widgets.toolWidgets import ToolWidgetCollection
                        ext = splitext(filename)[1]
                        if ext == HandleWidget.getFileExt():
                            tool = HandleWidget('')
                            tool.load(filename)
                            item = self._views.getFirstSliceView().addTarget(tool.getPosition(), tool.getName())
                            tool.copyAttributesTo(item)
                            self._addItem(item)
                        elif ext == LineWidget.getFileExt():
                            tool = LineWidget('')
                            tool.load(filename)
                            item = self._views.getFirstSliceView().addTarget(tool.getPosition1(),
                                                                             tool.getPosition2(),
                                                                             tool.getName())
                            tool.copyAttributesTo(item)
                            self._addItem(item)
                        elif ext == ToolWidgetCollection.getFileExt():
                            tools = ToolWidgetCollection()
                            tools.load(filename)
                            for tool in tools:
                                if isinstance(tool, HandleWidget):
                                    item = self._views.getFirstSliceView().addTarget(tool.getPosition(), tool.getName())
                                    tool.copyAttributesTo(item)
                                    self._addItem(item)
                                elif isinstance(tool, LineWidget):
                                    item = self._views.getFirstSliceView().addTarget(tool.getPosition1(),
                                                                                     tool.getPosition2(),
                                                                                     tool.getName())
                                    tool.copyAttributesTo(item)
                                    self._addItem(item)
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('open tool(s).')
            else: event.ignore()

    # Method alias

    getTool = ListAttributesWidget.getItem

