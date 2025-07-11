"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import abspath

import logging

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

from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTracts import SisypheBundle
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import LineWidget
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.core.sisypheDicom import ExportToRTStruct
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import IconLabel
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import LockLabel
from Sisyphe.widgets.basicWidgets import VisibilityLabel
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import ColorSelectPushButton
from Sisyphe.widgets.basicWidgets import OpacityPushButton
from Sisyphe.widgets.basicWidgets import WidthPushButton
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.widgets.multiComponentViewWidget import IconBarMultiComponentViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarSynchronisedGridViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.gui.dialogMeshProperties import DialogMeshProperties
from Sisyphe.gui.dialogFromXml import DialogFromXml
from Sisyphe.gui.dialogSettings import DialogSetting
from Sisyphe.gui.dialogTarget import DialogTarget
from Sisyphe.gui.dialogThreshold import DialogThreshold
from Sisyphe.gui.dialogGenericResults import DialogGenericResults
from Sisyphe.gui.dialogFileSelection import DialogFileSelection
from Sisyphe.gui.dialogDiffusionBundle import DialogStreamlinesROISelection
from Sisyphe.gui.dialogDiffusionBundle import DialogStreamlinesFiltering
from Sisyphe.gui.dialogDiffusionBundle import DialogStreamlinesClustering
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['ItemAttributesWidget',
           'ItemOverlayAttributesWidget',
           'ItemROIAttributesWidget',
           'ItemMeshAttributesWidget',
           'ItemToolAttributesWidget',
           'ItemBundleAttributesWidget',
           'ListAttributesWidget',
           'ListROIAttributesWidget',
           'ListMeshAttributesWidget',
           'ListToolAttributesWidget',
           'ListBundleAttributesWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QFrame -> ItemAttributesWidget -> ItemOverlayAttributesWidget
                                     -> ItemROIAttributesWidget
                                     -> ItemMeshAttributesWidget
                                     -> ItemToolAttributesWidget
                                     -> ItemBundleAttributesWidget
    - QWidget -> ListAttributesWidget -> ListROIAttributesWidget
                                      -> ListMeshAttributesWidget
                                      -> ListToolAttributesWidget
                                      -> ListBundleAttributesWidget
"""


class ItemAttributesWidget(QFrame):
    """
    Description
    ~~~~~~~~~~~

    ItemAttributesWidget, base class to specialized ItemAttributesWidget classes.
    Collection of ItemAttributesWidget are displayed in ListAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QFrame -> ItemAttributesWidget

    Last revision: 19/03/2025
    """

    _VSIZE = 24
    _HSIZE = 300 + (_VSIZE + 10) * 10

    # Class methods

    # < Revision 19/03/2025
    @classmethod
    def getDefaultIconSize(cls) -> int:
        dpi = QApplication.primaryScreen().logicalDotsPerInch()
        if dpi > 100: return int(cls._VSIZE * dpi / 800) * 8
        else: return cls._VSIZE
    # Revision 19/03/2025 >

    @classmethod
    def getDefaultMinimumWidth(cls) -> int:
        if platform == 'win32': return 300 + (cls.getDefaultIconSize() + 10) * 10
        elif platform == 'darwin': return 150 + (cls.getDefaultIconSize() + 10) * 10
        else: return cls._HSIZE

    # Special method

    """
    Private Attributes
        
    _item       type is fixed in specialized ItemAttributesWidget classes
    _views      IconBarViewWidgetCollection, to update visualization widgets with attributes
    _listattr   ListAttributesWidget
    _size       int, icon size 
    """

    def __init__(self, item=None, views=None, listattr=None, minwidth=None, parent=None):
        super().__init__(parent)
        # < Revision 06/07/2025
        self._logger = logging.getLogger(__name__)
        # Revision 06/07/2025 >

        # < Revision 19/03/2024
        self._size = self.getDefaultIconSize()
        # Revision 19/03/2024 >
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
        self._save.setFixedSize(self._size, self._size)
        self._save.clicked.connect(lambda: self.save())
        self._save.setToolTip('Save')
        self._save.setVisible(False)

        self._remove = IconLabel('cross.png')
        self._remove.setFixedSize(self._size, self._size)
        self._remove.clicked.connect(self.remove)
        self._remove.setToolTip('Remove')
        self._remove.setVisible(False)

        lyout = QHBoxLayout()
        lyout.setAlignment(Qt.AlignVCenter)
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addWidget(self._check)
        lyout.addWidget(self._save)
        lyout.addWidget(self._remove)
        self.setLayout(lyout)

        if minwidth is None: minwidth = self.getDefaultMinimumWidth()
        self.setMinimumWidth(minwidth)

    # Private method

    def _updateViews(self):
        raise NotImplemented

    def _updateSettingsFromItem(self):
        raise NotImplemented

    # Public methods

    def setIconSize(self, size=_VSIZE):
        self._size = size
        self.setFixedHeight(self._size + 8)
        self._save.setFixedSize(self._size, self._size)
        self._remove.setFixedSize(self._size, self._size)

    def getIconSize(self):
        return self._size

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
    Description
    ~~~~~~~~~~~

    Specialized ItemAttributesWidget to manage overlays.
    overlay settings : visibility, opacity

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ItemAttributesWidget -> ItemOverlayAttributesWidget

    Last revision: 19/03/2025
    """

    # Custom Qt signals

    visibilityChanged = pyqtSignal()

    # Special method

    """
    Private Attributes

    _visibility     VisibilityLabel, set visibility
    _opacity        QSlider, set opacity
    """

    def __init__(self, overlay=None, views=None, listattr=None, minwidth=192, parent=None):

        if overlay is not None:
            if not isinstance(overlay, SisypheVolume):
                raise TypeError('overlay parameter type {} is not SisypheVolume.'.format(type(overlay)))

        super().__init__(overlay, views, listattr, minwidth, parent)

        # Visibility button

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set overlay visibility')
        self._visibility.setFixedSize(self._size, self._size)
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
        # noinspection PyUnresolvedReferences
        self._opacity.valueChanged.connect(self._opacityChanged)

        self.checkBoxVisibilityOff()

        # Widget layout

        lyout = self.layout()
        lyout.addWidget(self._opacity)
        lyout.addWidget(self._label)
        lyout.addWidget(self._visibility)

    # Private methods

    # noinspection PyUnusedLocal
    def _visibilityChanged(self, obj):
        if self.hasViewCollection() and self.hasItem():
            v = self._visibility.getVisibilityStateIcon()
            for view in self._views:
                # < Revision 17/12/2024
                # if not isinstance(view, IconBarSynchronisedGridViewWidget):
                if not isinstance(view, (IconBarSynchronisedGridViewWidget, IconBarMultiComponentViewWidget)):
                    try:
                        view().getFirstSliceViewWidget().setOverlayVisibility(self._item, v)
                        view.updateRender()
                    except: pass
                # Revision 17/12/2024 >
            # noinspection PyUnresolvedReferences
            self.visibilityChanged.emit()

    def _opacityChanged(self, value):
        self._label.setText('{} %'.format(self._opacity.value()))
        self._opacity.setToolTip('Opacity {} %'.format(value))
        if self.hasViewCollection() and self.hasItem():
            for view in self._views:
                # < Revision 17/12/2024
                # if not isinstance(view, IconBarSynchronisedGridViewWidget):
                if not isinstance(view, (IconBarSynchronisedGridViewWidget, IconBarMultiComponentViewWidget)):
                    try:
                        view().getFirstSliceViewWidget().setOverlayOpacity(self._item, value / 100)
                        view.updateRender()
                    except: pass
                # Revision 17/12/2024 >

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
            self._logger.info('Set visibility {} overlay {}'.format(v, self._item.getBasename()))
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setOpacity(self, v):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                v = int(v * 100)
                self._opacity.setValue(v)
                self._opacityChanged(v)
                self._logger.info('Set opacity {} overlay {}'.format(v, self._item.getBasename()))
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
    Description
    ~~~~~~~~~~~

    ItemAttributesWidget class to manage ROI settings.
    ItemROIAttributesWidget are displayed in ListROIAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QFrame -> ItemAttributesWidget -> ItemROIAttributesWidget

    Last revision: 19/03/2025
    """

    # Special method

    """
    Private attributes

    _visibility     VisibilityLabel, eye button to set visibility
    _name           LabeledLineEdit, widget to edit name
    _color          ColorSelectPushButton, widget to set color
    _opacity        OpacityPushButton, widget to set opacity    
    """

    def __init__(self, roi=None, views=None, listattr=None, parent=None):

        if roi is not None:
            if not isinstance(roi, SisypheROI):
                raise TypeError('roi parameter type {} is not SisypheROI.'.format(type(roi)))

        super().__init__(roi, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set ROI visibility.')
        self._visibility.setFixedSize(self._size, self._size)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        # self._name.setFixedHeight(self._size)
        self._name.setToolTip('Set ROI name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, comma, space.')
        # noinspection PyUnresolvedReferences
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._size, self._size)
        self._color.colorChanged.connect(self._colorChanged)

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._size, self._size)
        self._opacity.setToolTip('Set ROI opacity.')
        # < Revision 24/10/2024
        # self._opacity.opacityChanged.connect(self._opacityChanged)
        self._opacity.popupHide.connect(self._opacityChanged)
        # Revision 24/10/2024 >

        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Widget layout

        lyout = self.layout()
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._color)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._opacity)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._visibility)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._name)
        # noinspection PyUnresolvedReferences
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
                    messageBox(self, 'Rename error', text='The ROI name {} is already in use.'.format(name))
                    self._name.setEditText(self._item.getName())
                else:
                    old = self._item.getName()
                    name = self._name.getEditText()
                    self._item.setName(name)
                    self._views.updateROIName(old, name)

    def _updateSettingsFromItem(self):
        if self._item is not None:
            self._name.setEditText(self._item.getName())
            c = self._item.getColor()
            self._color.setFloatColor(c[0], c[1], c[2])
            self._opacity.setOpacity(self._item.getAlpha())
            # Update tooltip
            self.setToolTip(str(self._item)[:-1])
            self._name.setToolTip('Set ROI name,\n'
                                  'Accepted characters A...Z, a...z, 0...9, -, _, comma, space.'
                                  '\n\n{}'.format(str(self._item)[:-1]))
            self.setToolTip(str(self._item)[:-1])

    def _updateViews(self):
        if self.hasViewCollection() and self.hasItem():
            self._views.updateROIAttributes()

    # Public methods

    def setIconSize(self, size=ItemAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._visibility.setFixedSize(self._size, self._size)
        self._color.setFixedSize(self._size, self._size)
        self._color.setFixedSize(self._size, self._size)
        self._opacity.setFixedSize(self._size, self._size)
        self.setMinimumWidth(300 + (self._size + 10) * 5)

    def setColor(self, r, g, b):
        self._color.setFloatColor(r, g, b)
        self._colorChanged()
        self._logger.info('Set color {} ROI {}'.format((r, g, b), self._item.getName()))

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
                self._logger.info('Set opacity {} ROI {}'.format(v, self._item.getName()))
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setVisibility(self, v):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            self._visibilityChanged()
            self._logger.info('Set visbility {} ROI {}'.format(v, self._item.getName()))
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setROI(self, roi):
        if isinstance(roi, SisypheROI):
            super().setItem(roi)
            # self._updateSettingsFromItem()
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def save(self, wait: DialogWait | None = None):
        if wait is None:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Save {}'.format(self._item.getName()))
        QApplication.processEvents()
        try:
            if self._item.hasFilename(): self._item.setDefaultFilename()
            self._item.save()
            self._logger.info('Save ROI {}'.format(self._item.getFilename()))
            if self.hasViewCollection(): self._views.clearUndo()
        except Exception as err:
            messageBox(self, 'Save ROI', text='{}'.format(err))
        wait.close()

    # Method aliases

    getROI = ItemAttributesWidget.getItem
    hasROI = ItemAttributesWidget.hasItem


class ItemMeshAttributesWidget(ItemAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    ItemAttributesWidget class to manage mesh settings.
    ItemMeshAttributesWidget are displayed in ListMeshAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QFrame -> ItemAttributesWidget -> ItemMeshAttributesWidget

    Last revision 19/03/2025
    """

    # Special method

    """
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
    """

    def __init__(self, mesh=None, views=None, listattr=None, parent=None):

        if mesh is not None:
            if not isinstance(mesh, SisypheMesh):
                raise TypeError('mesh parameter type {} is not SisypheMesh.'.format(type(mesh)))

        super().__init__(mesh, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set mesh visibility.')
        self._visibility.setFixedSize(self._size, self._size)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        self._name.setToolTip('Set mesh name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.')

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._size, self._size)

        # Lut

        self._lut = IconPushButton('lut.png', size=self._size)
        self._lut.setVisible(False)
        self._lutwidget = None

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._size, self._size)
        self._opacity.setToolTip('Set mesh opacity.')
        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Properties

        # < Revision 25/03/2025
        # self._properties = IconPushButton('meshsetting.png', self._size)
        self._properties = IconLabel('meshsetting.png')
        self._properties.setFixedSize(self._size, self._size)
        # Revision 25/03/2025 >
        self._properties.setToolTip('Set mesh properties.')
        # noinspection PyUnresolvedReferences
        self._properties.clicked.connect(lambda dummy: self.settings())
        self._dialogprop = DialogMeshProperties()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogprop, c)
        self._dialogprop.UpdateRender.connect(self._updateViews)

        self._updateSettingsFromItem()
        self._visibility.visibilityChanged.connect(self._visibilityChanged)
        # noinspection PyUnresolvedReferences
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)
        self._color.colorChanged.connect(self._colorChanged)
        self._opacity.opacityChanged.connect(self._opacityChanged)

        # Transform

        self._trf = IconPushButton('rotate.png', self._size)
        self._trf.setToolTip('Apply rigid transformation to mesh.')
        # noinspection PyUnresolvedReferences
        self._trf.clicked.connect(lambda dummy: self.transform())
        trf = QMenu()
        # noinspection PyTypeChecker
        trf.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        trf.setWindowFlag(Qt.FramelessWindowHint, True)
        trf.setAttribute(Qt.WA_TranslucentBackground, True)
        self._tx = LabeledDoubleSpinBox(title='Tx', fontsize=12)
        self._tx.setDecimals(1)
        self._tx.setSingleStep(1.0)
        self._tx.setRange(-256.0, 256.0)
        self._tx.setValue(0.0)
        self._tx.setSuffix(' mm')
        # noinspection PyUnresolvedReferences
        self._tx.valueChanged.connect(self._move)
        self._ty = LabeledDoubleSpinBox(title='Ty', fontsize=12)
        self._ty.setDecimals(1)
        self._ty.setSingleStep(1.0)
        self._ty.setRange(-256.0, 256.0)
        self._ty.setValue(0.0)
        self._ty.setSuffix(' mm')
        # noinspection PyUnresolvedReferences
        self._ty.valueChanged.connect(self._move)
        self._tz = LabeledDoubleSpinBox(title='Tz', fontsize=12)
        self._tz.setDecimals(1)
        self._tz.setSingleStep(1.0)
        self._tz.setRange(-256.0, 256.0)
        self._tz.setValue(0.0)
        self._tz.setSuffix(' mm')
        # noinspection PyUnresolvedReferences
        self._tz.valueChanged.connect(self._move)
        self._rx = LabeledDoubleSpinBox(title='Rx', fontsize=12)
        self._rx.setDecimals(1)
        self._rx.setSingleStep(1.0)
        self._rx.setRange(-180.0, 180.0)
        self._rx.setValue(0.0)
        self._rx.setSuffix(' °')
        # noinspection PyUnresolvedReferences
        self._rx.valueChanged.connect(self._move)
        self._ry = LabeledDoubleSpinBox(title='Ry', fontsize=12)
        self._ry.setDecimals(1)
        self._ry.setSingleStep(1.0)
        self._ry.setRange(-180.0, 180.0)
        self._ry.setValue(0.0)
        self._ry.setSuffix(' °')
        # noinspection PyUnresolvedReferences
        self._ry.valueChanged.connect(self._move)
        self._rz = LabeledDoubleSpinBox(title='Rz', fontsize=12)
        self._rz.setDecimals(1)
        self._rz.setSingleStep(1.0)
        self._rz.setRange(-180.0, 180.0)
        self._rz.setValue(0.0)
        self._rz.setSuffix(' °')
        # noinspection PyUnresolvedReferences
        self._rz.valueChanged.connect(self._move)
        font = QFont('Arial', 10)
        clear = QPushButton('Clear')
        clear.setFont(font)
        # noinspection PyUnresolvedReferences
        clear.clicked.connect(self._clearTransform)
        cursor = QPushButton('Align mesh center to cursor')
        cursor.setFont(font)
        # noinspection PyUnresolvedReferences
        cursor.clicked.connect(self._goToCursorTransform)
        apply = QPushButton('Resample mesh')
        apply.setFont(font)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._trf)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._properties)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._color)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._lut)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._opacity)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._visibility)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._name)
        # noinspection PyUnresolvedReferences
        lyout.insertSpacing(1, 5)

        # Redirect child mouse double click event to self

        self._name.installEventFilter(self)
        self._visibility.installEventFilter(self)
        self._opacity.installEventFilter(self)
        self._color.installEventFilter(self)
        self._properties.installEventFilter(self)
        self._trf.installEventFilter(self)

    # Private methods

    def _clearTransform(self):
        self._tx.setValue(0.0)
        self._ty.setValue(0.0)
        self._tz.setValue(0.0)
        self._rx.setValue(0.0)
        self._ry.setValue(0.0)
        self._rz.setValue(0.0)
        self._item.setDefaultOrigin()
        self._name.setToolTip('Set mesh name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                              '\n\n{}'.format(str(self._item)[:-1]))
        self.setToolTip(str(self._item)[:-1])

    def _move(self):
        if self._item.isDefaultOrigin(): self._item.setOriginToCenter()
        self._item.setPosition(self._tx.value(), self._ty.value(), self._tz.value())
        self._item.setRotation(self._rx.value(), self._ry.value(), self._rz.value())
        self._name.setToolTip('Set mesh name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                              '\n\n{}'.format(str(self._item)[:-1]))
        self.setToolTip('{}'.format(str(self._item)[:-1]))
        if self.hasViewCollection():
            view = self.getViewCollection()
            view.getVolumeView().updateRender()

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
            self._name.setToolTip('Set mesh name,\n'
                                  'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                                  '\n\n{}'.format(str(self._item)[:-1]))
            self.setToolTip(str(self._item)[:-1])
            self._updateViews()

    def _opacityChanged(self):
        self._item.setOpacity(self._opacity.getOpacity())
        self._name.setToolTip('Set mesh name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                              '\n\n{}'.format(str(self._item)[:-1]))
        self.setToolTip(str(self._item)[:-1])
        self._updateViews()

    def _nameChanged(self):
        if self.hasViewCollection():
            meshes = self._views.getMeshCollection()
            name = self._name.getEditText()
            if name != self._item.getName():
                if name in meshes:
                    messageBox(self, 'Rename error', text='The mesh name {} is already in use.'.format(name))
                    self._name.setEditText(self._item.getName())
                else: self._item.setName(self._name.getEditText())
                self._name.setToolTip('Set mesh name,\n'
                                      'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                                      '\n\n{}'.format(str(self._item)[:-1]))
                self.setToolTip(str(self._item)[:-1])

    def _updateViews(self):
        if self.hasViewCollection() and self.hasItem():
            volview = self._views.getVolumeView()
            if volview is not None:
                volview.updateRender()
                volview.MeshOnSliceVisibilityChanged.emit(volview, volview.getMeshOnSliceVisibility())

    def _updateSettingsFromItem(self):
        if self._item is not None:
            self._name.setEditText(self._item.getName())
            c = self._item.getColor()
            self._color.setFloatColor(c[0], c[1], c[2])
            self._opacity.setOpacity(self._item.getOpacity())
            # Update tooltip
            self.setToolTip(str(self._item)[:-1])
            self._name.setToolTip('Set mesh name,\n'
                                  'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                                  '\n\n{}'.format(str(self._item)[:-1]))

    def _updateLut(self):
        if self._lutwidget is not None:
            r = self._lutwidget.getWindow()
            self._item.setLUTScalarRange(r[0], r[1])

    # Public methods

    def setIconSize(self, size=ItemAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._visibility.setFixedSize(self._size, self._size)
        self._color.setFixedSize(self._size, self._size)
        self._opacity.setFixedSize(self._size, self._size)
        self._properties.setFixedSize(self._size, self._size)
        self._trf.setFixedSize(self._size, self._size)
        self._trf.setIconSize(QSize(self._size - 8, self._size - 8))
        if self._lut is not None:
            self._lut.setFixedSize(self._size, self._size)
            self._lut.setIconSize(QSize(self._size - 8, self._size - 8))
        self.setMinimumWidth(300 + (self._size + 10) * 8)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if views is not None:
            view = self._views.getVolumeView()
            if view is not None:
                self._dialogprop.UpdateRender.connect(view.updateRender)

    def settings(self):
        self._dialogprop.setProperties(self._item.getActor().GetProperty())
        self._logger.info('Dialog exec [gui.dialogMeshProperties.DialogMeshProperties]')
        self._dialogprop.exec()
        c = self._item.getActor().GetProperty().GetColor()
        self._color.setFloatColor(c[0], c[1], c[2])
        self._logger.info('Change Properties ROI {}'.format(self._item.getName()))

    def transform(self):
        if self._tx.value() != 0.0 or self._ty.value() != 0.0 or self._tz.value() != 0.0 or \
                self._rx.value() != 0.0 or self._ry.value() != 0.0 or self._rz.value() != 0.0:
            trf = SisypheTransform()
            trf.setTranslations([self._tx.value(), self._ty.value(), self._tz.value()])
            trf.setRotations([self._rx.value(), self._ry.value(), self._rz.value()], deg=True)
            self._item.setPosition(0.0, 0.0, 0.0)
            self._item.setRotation(0.0, 0.0, 0.0)
            if self._item.isDefaultOrigin(): self._item.setOriginToCenter()
            self._item.applyTransform(trf)
            self._clearTransform()
            self._updateViews()
            self._logger.info('Set geometric transform Mesh {}\n{}'.format(self._item.getName(), str(trf)))

    def setColor(self, r, g, b):
        self._color.setFloatColor(r, g, b)
        self._colorChanged()
        self._logger.info('Set color {} Mesh {}'.format((r, g, b), self._item.getName()))

    def getColor(self):
        return self._color.getFloatColor()

    def setLut(self, vol):
        if isinstance(vol, SisypheVolume):
            self._lutwidget = LutWidget(view=self._views.getVolumeView(), size=256)
            self._lutwidget.lutWindowChanged.connect(self._updateLut)
            self._lutwidget.setVolume(vol)
            self._lut.setVisible(True)
            self._color.setVisible(False)
            self._properties.setVisible(False)
            popup = QMenu()
            # noinspection PyTypeChecker
            popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            popup.setWindowFlag(Qt.FramelessWindowHint, True)
            popup.setAttribute(Qt.WA_TranslucentBackground, True)
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
                self._logger.info('Set opacity {} Mesh {}'.format(v, self._item.getName()))
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setVisibility(self, v):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            self._visibilityChanged()
            self._logger.info('Set visibility {} Mesh {}'.format(v, self._item.getName()))
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getVisibility(self):
        return self._visibility.getVisibilityStateIcon()

    def setTranslations(self, t):
        self._tx.setValue(t[0])
        self._ty.setValue(t[1])
        self._tz.setValue(t[2])
        self._logger.info('Set translations {} Mesh {}'.format(t, self._item.getName()))

    def setRotations(self, r):
        self._rx.setValue(r[0])
        self._ry.setValue(r[1])
        self._rz.setValue(r[2])
        self._logger.info('Set rotations {} Mesh {}'.format(r, self._item.getName()))

    def setMesh(self, mesh):
        if isinstance(mesh, SisypheMesh):
            super().setItem(mesh)
            # _updateSettingsFromItem() is already called by super().setItem()
            # self._updateSettingsFromItem()
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def save(self, wait: DialogWait | None = None):
        if wait is None:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Save {}...'.format(self._item.getName()))
            QApplication.processEvents()
        try:
            if not self._item.hasFilename():
                self._item.setFilename(join(self._views.getVolume().getDirname(),
                                            self._item.getName() + self._item.getFileExt()))
            self._logger.info('Save {}'.format(self._item.getFilename()))
            self._item.save()
        except Exception as err:
            messageBox(self, 'Save Mesh', text='{}'.format(err))

    # Method aliases

    getMesh = ItemAttributesWidget.getItem
    hasMash = ItemAttributesWidget.hasItem

    # Qt event

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonDblClick:
            # Redirect child mouse double click event to self
            self.mouseDoubleClickEvent(event)
        return False

    def mouseDoubleClickEvent(self, event):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None:
                p = self._item.getCenterOfMass()
                if p is not None:
                    view.setCursorWorldPosition(p[0], p[1], p[2])


class ItemToolAttributesWidget(ItemAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    ItemAttributesWidget class to manage tool settings.
    ItemToolAttributesWidget are displayed in ListToolAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QFrame -> ItemAttributesWidget -> ItemToolAttributesWidget

    Last revision: 19/03/2025
    """

    # Special method

    """
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
    """

    def __init__(self, tool=None, views=None, listattr=None, parent=None):
        super().__init__(tool, views, listattr, parent=parent)

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set tool visibility.')
        self._visibility.setFixedSize(self._size, self._size)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Move to target

        # < Revision 30/03/2025
        # self._toTarget = IconPushButton('ftarget.png', self._size)
        self._toTarget = IconLabel('ftarget.png')
        self._toTarget.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        self._toTarget.setToolTip('Move cursor to target.')
        # noinspection PyUnresolvedReferences
        self._toTarget.clicked.connect(lambda dummy: self.focusTarget())

        # Move to entry

        # < Revision 30/03/2025
        # self._toEntry = IconPushButton('fentry.png', self._size)
        self._toEntry = IconLabel('fentry.png')
        self._toEntry.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        self._toEntry.setToolTip('Move cursor to entry.')
        # noinspection PyUnresolvedReferences
        self._toEntry.clicked.connect(lambda dummy: self.focusEntry())

        # Lock

        self._lock = LockLabel()
        self._lock.setToolTip('Lock/unlock tool movement.')
        self._lock.setFixedSize(self._size, self._size)
        self._lock.lockChanged.connect(self._lockChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        # self._name.setFixedHeight(self._size)
        self._name.setToolTip('Set tool name,\nAccepted characters A...Z, a...z, 0...9, -, _, comma, space.')
        # noinspection PyUnresolvedReferences
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = ColorSelectPushButton()
        self._color.setFixedSize(self._size, self._size)
        self._color.colorChanged.connect(self._colorChanged)

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._size, self._size)
        self._opacity.setToolTip('Set tool opacity.')
        self._opacity.opacityChanged.connect(self._opacityChanged)

        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Properties

        # < Revision 30/03/2025
        # self._properties = IconPushButton('settings.png', self._size)
        self._properties = IconLabel('settings.png')
        self._properties.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        self._properties.setToolTip('Set tool properties.')
        # noinspection PyUnresolvedReferences
        self._properties.clicked.connect(lambda dummy: self.properties())

        self._dialogprop = DialogSetting('Tools')
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogprop, c)
        self._dialogprop.getSettingsWidget().setParameterVisibility('MaxCount', False)

        # Position

        # < Revision 30/03/2025
        # self._target = IconPushButton('target.png', self._size)
        self._target = IconLabel('target.png')
        self._target.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        self._target.setToolTip('Set point position.')
        # noinspection PyUnresolvedReferences
        self._target.clicked.connect(lambda dummy: self.target())

        self._dialogtarget = DialogTarget(tool, views)
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogtarget, c)

        # Length

        # < Revision 30/03/2025
        # self._length = IconPushButton('length.png', self._size)
        self._length = IconLabel('length.png')
        self._length.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        self._length.setToolTip('Set trajectory length.')
        # noinspection PyUnresolvedReferences
        self._length.clicked.connect(lambda dummy: self.length())

        self._dialoglength = DialogFromXml('Trajectory length', ['TrajectoryLength'])
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialoglength, c)

        # Move

        # < Revision 30/03/2025
        # self._move = IconPushButton('move.png', self._size)
        self._move = IconLabel('move.png')
        self._move.setFixedSize(self._size, self._size)
        # Revision 30/03/2025 >
        if tool is not None and isinstance(tool, HandleWidget): self._move.setToolTip('Move point.')
        else: self._move.setToolTip('Move trajectory.')

        # noinspection PyUnresolvedReferences
        self._move.clicked.connect(lambda dummy: self.moving())

        self._dialogmove = DialogFromXml('Move point/trajectory', ['DuplicateTool'])
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogmove, c)

        # Widget layout

        lyout = self.layout()
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._properties)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._move)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._length)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._target)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._color)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._opacity)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._lock)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._toEntry)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._toTarget)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._visibility)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._name)
        # noinspection PyUnresolvedReferences
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
            if w is not None:
                # noinspection PyUnresolvedReferences
                w.setFloatColor(r, g, b, signal=False)
            self._item.setColor((r, g, b))
            self.setToolTip(str(self._item))
            view = self._views.getVolumeView()
            if view is not None: view.copyToolAttributes(self._item, None, signal=True)

    def _opacityChanged(self):
        if self.hasViewCollection():
            v = self._opacity.getOpacity()
            self._item.setOpacity(v)
            w = self._dialogprop.getSettingsWidget().getParameterWidget('Opacity')
            if w is not None:
                # noinspection PyUnresolvedReferences
                w.setValue(v)
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
                    messageBox(self, 'Rename error', text='The tool name {} is already in use.')
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
            self.setToolTip(str(self._item)[:-1])

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

    def setIconSize(self, size=ItemAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._visibility.setFixedSize(self._size, self._size)
        self._lock.setFixedSize(self._size, self._size)
        self._color.setFixedSize(self._size, self._size)
        self._opacity.setFixedSize(self._size, self._size)
        self._properties.setFixedSize(self._size, self._size)
        self._target.setFixedSize(self._size, self._size)
        self._length.setFixedSize(self._size, self._size)
        self._move.setFixedSize(self._size, self._size)
        self.setMinimumWidth(300 + (self._size + 10) * 10)

    def setColor(self, r, g, b, signal=True):
        self._color.setFloatColor(r, g, b)
        if signal: self._colorChanged()
        self._logger.info('Set color {} Tool {}'.format((r, g, b), self._item.getName()))

    def getColor(self):
        return self._color.getFloatColor()

    def setOpacity(self, v, signal=True):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacity.setOpacity(v)
                if signal: self._opacityChanged()
                self._logger.info('Set opacity {} Tool {}'.format(v, self._item.getName()))
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setLock(self, v):
        if isinstance(v, bool):
            self._lock.setLockStateIcon(v)
            if not v:
                self._item.setStatic()
                self._logger.info('Lock Tool {}'.format(self._item.getName()))
            else: self._logger.info('Unlock Tool {}'.format(self._item.getName()))
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
            self._logger.info('Set visibility {} Tool {}'.format(v, self._item.getName()))
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
            self._logger.info('Dialog exec [gui.dialogSettings.DialogSetting - Tool properties]')
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
                self._logger.info('Change propertiers Tool {}'.format(self._item.getName()))

    def target(self):
        if self.hasViewCollection():
            self._dialogtarget.setTrajectoryFieldsVisibility(isinstance(self._item, LineWidget))
            self._logger.info('Dialog exec [gui.dialogTarget.DialogTarget]')
            if self._dialogtarget.exec() == QDialog.Accepted:
                r = self._dialogtarget.getAttributes()
                self._views.getVolumeView().moveTool(self._item, target=r['target'], entry=r['entry'])
                self.setLock(self._item.isDynamic())
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
                self._logger.info('Dialog exec [gui.dialogFromXml.DialogFromXml - Tool length]')
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
                                    messageBox(self, 'Extend entry', text=msg)
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
                                    messageBox(self, 'Extend entry', text=msg)
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
                                wp.addItem('{} X direction'.format(mesh.getName()))
                                wp.addItem('{} Y direction'.format(mesh.getName()))
                                wp.addItem('{} Z direction'.format(mesh.getName()))
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
            if vol is not None:
                w = settings.getParameterWidget('Orientation')
                w.clear()
                w.addItem('Native')
                w.addItem('Camera')
                if vol.getACPC().hasACPC(): w.addItem('ACPC')
                # settings.getParameterWidget().setVisible(vol.getACPC().hasACPC())
            self._logger.info('Dialog exec [gui.dialogFromXml.DialogFromXml - Tool moving]')
            if self._dialogmove.exec() == QDialog.Accepted:
                c = wp.currentIndex()
                if c == 0:
                    # AP, L, H relative shift
                    lat = settings.getParameterValue('Laterality')
                    if lat is None: lat = 0.0
                    ap = settings.getParameterValue('Antero-posterior')
                    if ap is None: ap = 0.0
                    h = settings.getParameterValue('Height')
                    if h is None: h = 0.0
                    o = settings.getParameterValue('Orientation')[0]
                    if o is None: o = 'Native'
                    if o == 'Native':
                        # Shift in native orientation
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
                        # Shift in ACPC orientation
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
                        # Shift in camera orientation
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
                    # Move to current axial plane
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c == 2:
                    # Move to current coronal plane
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c == 3:
                    # Move to current sagittal plane
                    plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane()
                    self._item.planeProjection(plane)
                    self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                elif c > 3:
                    # Move to mesh surface
                    if self.hasViewCollection():
                        inter = 0
                        name, d, _ = wp.currentText().split(' ')
                        mesh = self._views.getMeshCollection()[name]
                        if d == 'Z':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        elif d == 'Y':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        elif d == 'X':
                            plane = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane()
                            inter = self._item.meshSurfaceProjection(plane, mesh)
                        if inter == 0:
                            msg = 'No intersection between {} and {} mesh in {} direction.'.format(self._item.getName(), name, d)
                            messageBox(self, 'Point projection', text=msg)
                        else: self._views.getVolumeView().moveTool(self._item, target=self._item.getPosition())
                self.focusTarget()
                self.unlock()
                self._item.setStatic()
                self.setToolTip(str(self._item))

    def save(self, wait: DialogWait | None = None):
        if wait is None:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Save {}...'.format(self._item.getName()))
            QApplication.processEvents()
        try:
            filename = join(self._views.getVolume().getDirname(),
                            self._item.getName() + self._item.getFileExt())
            self._item.saveAs(filename)
            self._logger.info('Save {}'.format(filename))
        except Exception as err: messageBox(self, 'Save tool', text='{}'.format(err))

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


class ItemBundleAttributesWidget(ItemAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    ItemAttributesWidget class to manage bundle settings.
    ItemBundleAttributesWidget are displayed in ListBundleAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QFrame -> ItemAttributesWidget -> ItemStreamlineAttributesWidget

    Last revision: 19/03/2025
    """

    # Class constant

    _MAXCOUNT: int = 10000

    # Special method

    """
    Private attributes
    
    _sl         SisypheStreamlines
    _visibility VisibilityLabel
    _name       LabeledLineEdit
    _color      IconPushButton
    _opacity    OpacityPushButton
    _width      WidthPushButton
    """

    def __init__(self, bundle=None, views=None, listattr=None, parent=None):
        super().__init__(bundle, views, listattr, parent=parent)

        self._sl = None

        # Visibility

        self._visibility = VisibilityLabel()
        self._visibility.setToolTip('Set streamlines visibility.')
        self._visibility.setFixedSize(self._size, self._size)
        self._visibility.visibilityChanged.connect(self._visibilityChanged)

        # Name

        regexp = QRegExp(SisypheROI.getRegExp())
        validator = QRegExpValidator(regexp)
        self._name = LabeledLineEdit()
        self._name.getQLineEdit().setValidator(validator)
        self._name.setToolTip('Set streamlines name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.')
        # noinspection PyUnresolvedReferences
        self._name.getQLineEdit().editingFinished.connect(self._nameChanged)

        # Color

        self._color = IconPushButton('palette.png', self._size)
        self._color.setToolTip('Set streamlines color representation.')
        # noinspection PyUnresolvedReferences
        self._color.clicked.connect(lambda dummy: self._editColor())

        self._dialogcolor = DialogFromXml('Streamlines color', ['TractColor'])
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogcolor, c)

        # Opacity

        self._opacity = OpacityPushButton()
        self._opacity.setFixedSize(self._size, self._size)
        self._opacity.setToolTip('Set streamlines opacity.')
        self._opacity.opacityChanged.connect(self._opacityChanged)

        # Width

        self._width = WidthPushButton(prefix='Streamlines width', vmin=0.5, vmax=10.0, step=0.5)
        self._width.setFixedSize(self._size, self._size)
        # noinspection PyUnresolvedReferences
        self._width.popupHide.connect(self._widthChanged)

        self._save.setVisible(True)
        self._remove.setVisible(True)

        # Widget layout

        lyout = self.layout()
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._width)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._color)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._opacity)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._visibility)
        # noinspection PyUnresolvedReferences
        lyout.insertWidget(1, self._name)
        # noinspection PyUnresolvedReferences
        lyout.insertSpacing(1, 5)

    # Private methods

    def _getTractCollection(self):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            return view.getTractCollection()
        else: raise AttributeError('_views attribute is None.')

    def _visibilityChanged(self):
        v = self._visibility.getVisibilityStateIcon()
        self._getTractCollection().setVisibility(v, self.getBundle())
        self._updateViews()

    def _opacityChanged(self):
        v = self._opacity.getOpacity()
        self._getTractCollection().setOpacity(v, self.getBundle())
        self._updateViews()

    def _nameChanged(self):
        self._getTractCollection().renameBundle(old=self.getBundle(), new=self._name.getEditText())
        self._item = self._name.getEditText()
        self._sl.setName(self._name.getEditText())
        # < Revision 20/02/2025
        # add tooltip update
        self.setToolTip(str(self._sl)[:-1])
        self._name.setToolTip('Set streamlines name,\n'
                              'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                              '\n\n{}'.format(str(self._sl)[:-1]))
        # Revision 20/02/2025 >

    def _widthChanged(self):
        v = self._width.getWidth()
        self._getTractCollection().setLineWidth(v, self.getBundle())
        self._updateViews()

    def _editColor(self):
        tracts = self._getTractCollection()
        bundle = self.getBundle()
        c = tracts.getFloatColor(bundle)
        cm = tracts.getColorRepresentationAsString(bundle)
        if cm == 'color': cm = 'Solid'
        elif cm == 'scalars': cm = 'Scalars'
        else: cm = 'RGB Direction'
        lut = tracts.getLut(bundle).getName()
        settings = self._dialogcolor.getFieldsWidget(0)
        settings.getParameterWidget('ColorMode').setCurrentText(cm)
        settings.getParameterWidget('SolidColor').setFloatColor(r=c[0], g=c[1], b=c[2], signal=False)
        settings.getParameterWidget('ScalarsVolume')
        settings.getParameterWidget('ScalarsLut').setCurrentText(lut)
        if self._dialogcolor.exec() == QDialog.Accepted:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Update {} color...'.format(tracts.getBundleNames()[0]))
            QApplication.processEvents()
            cm2 = settings.getParameterWidget('ColorMode').currentText()
            if cm2 == 'Solid':
                c2 = settings.getParameterWidget('SolidColor').getFloatColor()
                if c2 != c: tracts.setFloatColor(c2, bundle)
            elif cm2 == 'Scalars':
                lut2 = settings.getParameterWidget('ScalarsLut').currentText()
                if settings.getParameterWidget('ScalarsVolume').isEmpty():
                    if tracts.hasScalars(bundle):
                        if lut2 != lut: tracts.setLut(lut2, bundle)
                        tracts.setColorRepresentation(1, bundle)
                else:
                    vol = settings.getParameterWidget('ScalarsVolume').getVolume()
                    # < Revision 03/04/2025
                    vol.setDefaultOrigin()
                    vol.setDirections()
                    # Revision 03/04/2025 >
                    tracts.setScalarsFromVolume(vol, bundle, wait)
                    if lut2 != lut: tracts.setLut(lut2, bundle)
                    tracts.setColorRepresentation(1, bundle)
            else:
                if cm2 != cm:
                    tracts.setColorRepresentation(0, self.getBundle())
            self._updateViews()
            wait.close()

    def _updateViews(self):
        if self.hasViewCollection() and self.hasItem():
            view = self._views.getVolumeView()
            if view is not None: view.updateRender()

    def _updateSettingsFromItem(self):
        if self._item is not None:
            # Update widget from item properties
            bundle = self.getBundle()
            self._name.setEditText(bundle)
            self._opacity.setOpacity(self._sl.getOpacity(), signal=False)
            self._width.setWidth(self._sl.getLineWidth(), signal=False)
            # Update tooltip
            self.setToolTip(str(self._sl)[:-1])
            self._name.setToolTip('Set streamlines name,\n'
                                  'Accepted characters A...Z, a...z, 0...9, -, _, #, comma, space.'
                                  '\n\n{}'.format(str(self._sl)[:-1]))

    # Public methods

    def setStreamlines(self,
                       sl: SisypheStreamlines,
                       wait: DialogWait | None = None) -> None:

        tracts = self._views.getTractCollection()
        n = sl.count()
        # < Revision 20/02/2025
        if n > self._MAXCOUNT:
            select = SisypheBundle(s=(0, self._MAXCOUNT))
            original = sl.getName()
            name = 'truncated {}'.format(original)
            select.setName(name)
            sl.getBundles().append(select)
            sl = sl.getSisypheStreamlinesFromBundle(name)
            sl.setName(original)
        # Revision 20/02/2025 >
        self._sl = sl
        if tracts is not None:
            if wait is not None:
                wait.setProgressRange(0, 100)
                wait.setProgressVisibility(True)
            tracts.appendBundle(sl, self.getBundle(), wait)
            if wait is not None:
                wait.setCurrentProgressValuePercent(100, None)
        self._updateSettingsFromItem()

    def updateStreamlines(self,
                          select: SisypheBundle) -> None:
        tracts = self._views.getTractCollection()
        if tracts is not None:
            self._sl = tracts.updateBundle(self._sl, select)
        self._updateSettingsFromItem()

    def duplicateStreamlines(self,
                             sl: SisypheStreamlines,
                             select: SisypheBundle | None) -> None:
        tracts = self._views.getTractCollection()
        if tracts is not None:
            self._sl = tracts.duplicateBundle(sl, select)
            self._logger.info('Duplicate Bundle {} to {}'.format(sl.getName(), self._sl.getName()))
        self._updateSettingsFromItem()

    def unionStreamlines(self,
                         sl: list[SisypheStreamlines],
                         wait: DialogWait | None = None) -> None:
        tracts = self._views.getTractCollection()
        if tracts is not None:
            self._sl = tracts.unionBundle(self.getBundle(), sl, wait)
            self._logger.info('Union {}'.format(self._sl.getName()))
            self._updateSettingsFromItem()

    def getStreamlines(self) -> SisypheStreamlines:
        return self._sl

    def setIconSize(self, size=ItemAttributesWidget._VSIZE):
        super().setIconSize(size)
        self._visibility.setFixedSize(self._size, self._size)
        self._color.setFixedSize(self._size, self._size)
        self._opacity.setFixedSize(self._size, self._size)
        self._width.setFixedSize(self._size, self._size)
        self.setMinimumWidth(300 + (self._size + 10) * 6)

    def setWidth(self, v, signal=True):
        if isinstance(v, float):
            if 0.1 <= v <= 10.0:
                self._width.setWidth(v)
                if signal: self._widthChanged()
                self._logger.info('Set width {} bundle {}'.format(v, self._sl.getName()))
            else: raise ValueError('parameter value {} is not between 0.1 and 10.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getWidth(self):
        return self._width.getWidth()

    def setOpacity(self, v, signal=True):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._opacity.setOpacity(v)
                if signal: self._opacityChanged()
                self._logger.info('Set opacity {} bundle {}'.format(v, self._sl.getName()))
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getOpacity(self):
        return self._opacity.getOpacity()

    def setVisibility(self, v, signal=True):
        if isinstance(v, bool):
            self._visibility.setVisibilitySateIcon(v)
            if signal: self._visibilityChanged()
            self._logger.info('Set visibility {} bundle {}'.format(v, self._sl.getName()))
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

    def save(self, wait: DialogWait | None = None):
        if wait is None:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Save {}...'.format(self._item))
            QApplication.processEvents()
        bundle = self.getBundle()
        try:
            tracts = self._getTractCollection()
            self._sl.setFloatColor(tracts.getFloatColor(bundle))
            self._sl.setLut(tracts.getLut(bundle))
            self._sl.setColorRepresentation(tracts.getColorRepresentation(bundle))
            self._sl.setOpacity(tracts.getOpacity(bundle))
            self._sl.setLineWidth(tracts.getLineWidth(bundle))
            self._sl.save()
            self._logger.info('Save {}'.format(self._sl.getFilename()))
        except Exception as err: messageBox(self, 'Save streamlines', text='{}'.format(err))

    # Method aliases

    getBundle = ItemAttributesWidget.getItem
    hasBundle = ItemAttributesWidget.hasItem


class ListAttributesWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    Abstract base class to manage a list of ItemAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ListAttributesWidget

    Last revision: 02/11/2024
    """
    _VSIZE = 32

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(parent)
        # < Revision 06/07/2025
        self._logger = logging.getLogger(__name__)
        # Revision 06/07/2025 >

        self._collection = None
        self._scrsht = None
        # < Revision 02/11/2024
        # add self._maxcount attribute
        self._maxcount = 20
        # Revision 02/11/2024 >

        self._views = views
        if views is not None:
            if views is not isinstance(views, IconBarViewWidgetCollection):
                raise TypeError('views parameter type {} is not IconBarViewWidgetCollection'.format(type(views)))

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SingleSelection)
        # noinspection PyUnresolvedReferences
        self._list.itemSelectionChanged.connect(self._selectionChanged)

        self._new = IconPushButton('add.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._new.clicked.connect(lambda dummy: self.new())
        self._open = IconPushButton('open.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._open.clicked.connect(self.open)
        self._saveall = IconPushButton('save.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._saveall.clicked.connect(self.saveAll)
        self._removeall = IconPushButton('delete2.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._removeall.clicked.connect(self.removeAll)
        self._checkall = IconPushButton('check.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._checkall.clicked.connect(self.checkAll)
        self._uncheckall = IconPushButton('uncheck.png', size=self._VSIZE)
        # noinspection PyUnresolvedReferences
        self._uncheckall.clicked.connect(self.uncheckAll)

        self._new.setToolTip('New')
        self._open.setToolTip('Open')
        self._saveall.setToolTip('Save all')
        self._removeall.setToolTip('Remove all')
        self._checkall.setToolTip('Check all')
        self._uncheckall.setToolTip('Uncheck all')

        self._btlayout1 = QHBoxLayout()
        self._btlayout1.setContentsMargins(0, 0, 0, 0)
        self._btlayout1.setSpacing(5)
        self._btlayout1.addStretch()
        self._btlayout1.addWidget(self._open)
        self._btlayout1.addWidget(self._new)
        self._btlayout1.addWidget(self._saveall)
        self._btlayout1.addWidget(self._removeall)
        self._btlayout1.addStretch()

        self._btlayout2 = QHBoxLayout()
        self._btlayout2.setContentsMargins(0, 0, 0, 0)
        self._btlayout2.setSpacing(5)
        self._btlayout2.addStretch()
        self._btlayout2.addWidget(self._checkall)
        self._btlayout2.addWidget(self._uncheckall)
        self._btlayout2.addStretch()

        lyout = QVBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
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
                             margins2.left() + margins2.right() + 20)

    # Private methods

    def _createWidget(self, item) -> ItemAttributesWidget:
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
        else:
            # noinspection PyInconsistentReturns
            messageBox(self, 'Add', text='{} is already open.'.format(item))

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
        # noinspection PyInconsistentReturns
        while parent is not None:
            if isinstance(parent, WindowSisyphe): return parent
            else: parent = parent.parent()

    def _getStatusBar(self):
        mainwindow = self.getMainWindow()
        if mainwindow is not None: return mainwindow.getStatusBar()
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

    # < Revision 02/11/2024
    # add setMaxCount method
    def setMaxCount(self, v):
        self._maxcount = v
    # Revision 02/11/2024 >

    # < Revision 02/11/2024
    # add getMaxCount method
    def getMaxCount(self):
        return self._maxcount
    # Revision 02/11/2024 >

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
                self.setEnabled(False)
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
                self.setEnabled(True)

    def removeItem(self, w):
        n = self._list.count()
        if n > 0:
            self.setEnabled(False)
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
            # < Revision 24/10/2024
            # add self._updateViews()
            self._updateViews()
            # Revision 24/10/2024 >
            self.setEnabled(True)

    def removeAll(self):
        if self._list.count() > 0: self._list.clear()
        if self.hasViewCollection() and self.hasCollection(): self._collection.clear()
        self._updateViews()

    def saveAll(self):
        if self.hasCollection():
            n = self._list.count()
            if n > 0 and self.hasCollection():
                wait = DialogWait()
                wait.setInformationText('Save all...')
                if n > 1:
                    wait.setProgressRange(0, n)
                    wait.setProgressVisibility(True)
                    for i in range(0, n):
                        attritem = self._list.item(i)
                        witem = self._list.itemWidget(attritem)
                        wait.setCurrentProgressValue(i)
                        witem.save(wait)
                wait.close()

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
    Description
    ~~~~~~~~~~~

    Class to manage a list of ItemROIAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ListAttributesWidget -> ListROIAttributesWidget

    Last revision: 22/07/2024
    """

    # Special method

    def __init__(self, views=None, parent=None):

        super().__init__(views, parent)

        self._listmeshwidget = None

        self._remove = IconPushButton('cross.png', size=ListAttributesWidget._VSIZE)
        self._duplicate = IconPushButton('duplicate.png', size=ListAttributesWidget._VSIZE)
        self._export = IconPushButton('export.png', size=ListAttributesWidget._VSIZE)
        self._mesh = IconPushButton('roi2mesh.png', size=ListAttributesWidget._VSIZE)
        self._dist = IconPushButton('map.png', size=ListAttributesWidget._VSIZE)

        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self.remove)
        # noinspection PyUnresolvedReferences
        self._duplicate.clicked.connect(self.duplicate)
        # noinspection PyUnresolvedReferences
        self._export.clicked.connect(self._exportMenu)
        # noinspection PyUnresolvedReferences
        self._mesh.clicked.connect(self.toMesh)
        # noinspection PyUnresolvedReferences
        self._dist.clicked.connect(self.toDistance)

        self._remove.setToolTip('Remove checked ROI(s)')
        self._duplicate.setToolTip('Duplicate selected ROI')
        self._export.setToolTip('Export checked ROI(s)')
        self._mesh.setToolTip('Conversion of checked ROI(s) to mesh(es)')
        self._dist.setToolTip('Distance map processing from checked ROI(s)')

        self._btlayout1.insertWidget(5, self._export)
        self._btlayout1.insertWidget(5, self._remove)
        self._btlayout2.insertWidget(3, self._mesh)
        self._btlayout2.insertWidget(3, self._dist)
        self._btlayout2.insertWidget(3, self._duplicate)

        self._popup = QMenu()
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action = dict()
        self._action['xvol'] = QAction('Export to PySisyphe format')
        self._action['nii'] = QAction('Export to Nifti format')
        self._action['nrrd'] = QAction('Export to Nrrd format')
        self._action['minc'] = QAction('Export to Minc format')
        self._action['numpy'] = QAction('Export to Numpy format')
        self._action['vtk'] = QAction('Export to VTK format')
        self._action['dcm'] = QAction('Export to DICOM RT format')
        # noinspection PyUnresolvedReferences
        self._action['xvol'].triggered.connect(self.saveSisyphe)
        # noinspection PyUnresolvedReferences
        self._action['nii'].triggered.connect(self.saveNifti)
        # noinspection PyUnresolvedReferences
        self._action['nrrd'].triggered.connect(self.saveNRRD)
        # noinspection PyUnresolvedReferences
        self._action['minc'].triggered.connect(self.saveMinc)
        # noinspection PyUnresolvedReferences
        self._action['numpy'].triggered.connect(self.saveNumpy)
        # noinspection PyUnresolvedReferences
        self._action['vtk'].triggered.connect(self.saveVTK)
        # noinspection PyUnresolvedReferences
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

    def _getNewName(self, name: str) -> str:
        while name in self._collection:
            parts = name.split('#')
            suffix = parts[-1]
            if suffix.isdigit():
                suffix = int(suffix) + 1
                # noinspection PyTypeChecker
                parts[-1] = str(suffix)
            else: parts.append('1')
            name = '#'.join(parts)
        return name

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
        self._dist.setIconSize(QSize(size - 8, size - 8))
        self._dist.setFixedSize(size, size)

    def getCheckedROI(self):
        rois = list()
        for i in range(0, self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget.isChecked():
                rois.append(widget.getROI())
        return rois

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
        if isinstance(parent, TabROIListWidget): return parent
        else: raise TypeError('parent type {} is not TabROIListWidget..'.format(type(parent)))

    def hasTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabROIListWidget
        return isinstance(parent, TabROIListWidget)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection): self._collection = views.getROICollection()
        else: self._collection = None

    def new(self, name=''):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    wait = DialogWait()
                    wait.open()
                    wait.setInformationText('Add new ROI...')
                    vol = self._views.getVolume()
                    roi = SisypheROI(vol, copy=False)
                    roi.setReferenceID(self._collection.getReferenceID())
                    roi.setAlpha(1.0)
                    if name == '':
                        # < Revision 22/07/2024
                        # roi.setName('ROI' + str(len(self._collection) + 1))
                        name = self._getNewName('ROI#1')
                        roi.setName(name)
                        # Revision 22/07/2024 >
                    else: roi.setName(name)
                    self._addItem(roi)
                    self._views.setActiveROI(roi.getName())
                    self._views.setROIVisibility(True)
                    # Set undo enabled
                    draw = self._views.getROIDraw()
                    if draw is not None: draw.setUndoOn()
                    self._logger.info('New ROI {}'.format(roi.getName()))
                    # Set ROI tools enabled
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setROIToolsEnabled(True)
                        mainwindow.setStatusBarMessage('New ROI {} added.'.format(name))
                    wait.close()
                else:
                    messageBox(self,
                               'New ROI',
                               'Maximum number of ROIs reached.\n'
                               'Close a ROI to add a new one.',
                               icon=QMessageBox.Information)

    def add(self, roi):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
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
                                self._logger.info('Add ROI {}'.format(roi.getName()))
                                # Set ROI tools enabled
                                mainwindow = self._getMainWindow()
                                if mainwindow is not None:
                                    mainwindow.setROIToolsEnabled(True)
                                    mainwindow.setStatusBarMessage('ROI {} added.'.format(roi.getName()))
                            else: messageBox(self, title=title, text='ROI {} is already open.'.format(roi.getName()))
                        else: messageBox(self, title=title,
                                         text='{} ROI does not belong to {} volume (ID mismatch).'.format(
                                             roi.getName(), vol.getBasename()))
                    else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))
                else:
                    messageBox(self,
                               'Add ROI',
                                text='Maximum number of ROIs reached.\n'
                                     'Close a ROI to add a new one.',
                               icon=QMessageBox.Information)

    def duplicate(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    widget = self._getSelectedWidget()
                    if widget is not None:
                        wait = DialogWait(info='Duplicate selected ROI...')
                        wait.open()
                        roi = widget.getItem()
                        roi2 = roi.copy()
                        roi2.setAlpha(0.5)
                        # < Revision 22/07/2024
                        # roi2.setName(roi.getName() + str(len(self._collection) + 1))
                        name = self._getNewName(roi.getName())
                        roi2.setName(name)
                        # Revision 22/07/2024 >
                        self.add(roi2)
                        wait.close()
                        self._logger.info('Duplicate ROI {} to {}'.format(roi.getName(), roi.getName()))
                        mainwindow = self._getMainWindow()
                        if mainwindow is not None:
                            mainwindow.setStatusBarMessage('ROI {} duplicated.'.format(roi.getName()))
                else:
                    messageBox(self,
                               'Duplicate ROI',
                               'Maximum number of ROIs reached.\n'
                               'Close a ROI to add a new one.',
                               icon=QMessageBox.Information)

    def open(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    title = 'Open ROI(s)'
                    filt = 'ROI (*{})'.format(SisypheROI.getFileExt())
                    filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
                    QApplication.processEvents()
                    if filenames:
                        chdir(dirname(filenames[0]))
                        n = len(filenames)
                        wait = DialogWait()
                        wait.setInformationText('Open ROI')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        chdir(dirname(filenames[0]))
                        for filename in filenames:
                            filename = abspath(filename)
                            if self.count() < self.getMaxCount():
                                roi = SisypheROI()
                                try:
                                    wait.setInformationText('Open {}'.format(basename(filename)))
                                    wait.incCurrentProgressValue()
                                    roi.load(filename)
                                    self.add(roi)
                                except Exception as err:
                                    wait.hide()
                                    messageBox(self, title=title, text='{}'.format(err))
                            else:
                                wait.hide()
                                messageBox(self,
                                           'Open ROI',
                                           text='Maximum number of ROIs reached.\n'
                                                'Close a ROI to add a new one.',
                                           icon=QMessageBox.Information)
                        wait.close()
                else:
                    messageBox(self,
                               'Open ROI',
                               text='Maximum number of ROIs reached.\n'
                                    'Close a ROI to add a new one.',
                               icon=QMessageBox.Information)

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
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Checked ROI(s) removed.')
            else: messageBox(self, 'Remove ROI', 'No ROI checked.')

    def removeItem(self, w):
        if self.hasViewCollection() and self.hasCollection():
            roi = w.getROI()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} ROI removed.'.format(roi.getName()))
            super().removeItem(w)
            self._logger.info('Remove ROI {}'.format(roi.getName()))
            if self._collection.count() == 0:
                self._views.setROIVisibility(False)
                self._views.clearUndo()
                if mainwindow is not None:
                    mainwindow.setROIToolsEnabled(False)

    def removeAll(self):
        super().removeAll()
        self._views.setROIVisibility(False)
        self._views.clearUndo()
        # Set ROI tools disabled
        self._logger.info('All ROIs removed')
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setROIToolsEnabled(False)
            mainwindow.setStatusBarMessage('All ROI(s) removed.')

    def saveAll(self):
        super().saveAll()
        self._views.clearUndo()
        self._logger.info('Save all ROIs')
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setStatusBarMessage('All ROI(s) saved.')

    def saveSisyphe(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Sisyphe volume...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            ref = self.getViewCollection().getVolume()
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename(): filename = join(ref.getFilename(), roi.getName() + ref.getFileExt())
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                vol = SisypheVolume(roi)
                ref.copyAttributesTo(vol)
                vol.saveAs(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to PySisyphe format.')
        else: messageBox(self, 'Export to PySisyphe format', 'No ROI checked.')

    def saveNifti(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Nifti...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNiftiExt()[0])
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                roi.saveToNIFTI(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Nifti format.')
        else: messageBox(self, 'Export to Nifti format', 'No ROI checked.')

    def saveNRRD(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Nrrd...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNrrdExt()[0])
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                roi.saveToNRRD(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Nrrd format.')
        else: messageBox(self, 'Export to Nrrd format', 'No ROI checked.')

    def saveMinc(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Minc...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getMincExt()[0])
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                roi.saveToMINC(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Minc format.')
        else: messageBox(self, 'Export to Minc format', 'No ROI checked.')

    def saveNumpy(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Numpy...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getNumpyExt()[0])
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                roi.saveToNumpy(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to Numpy format.')
        else: messageBox(self, 'Export to Numpy format', 'No ROI checked.')

    def saveVTK(self):
        rois = self.getCheckedROI()
        n = len(rois)
        if n > 0:
            wait = DialogWait()
            wait.setInformationText('Save as Vtk...')
            wait.setProgressRange(0, n)
            wait.setProgressVisibility(n > 1)
            for roi in rois:
                item = roi.getItem()
                if not item.hasFilename():
                    path = self.getViewCollection().getVolume().getFilename()
                    filename = join(path, roi.getName() + getVtkExt()[0])
                else: filename = item.getFilename()
                wait.setInformationText('save {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                roi.saveToVTK(filename)
                self._logger.info('Save ROI {} to {}'.format(roi.getName(), filename))
            wait.close()
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Checked ROI(s) exported to VTK format.')
        else: messageBox(self, 'Export to VTK format', 'No ROI checked.')

    # < Revision 06/11/2024
    # method implemented
    def saveDicomRT(self):
        items = self.getCheckedROI()
        if len(items) > 0:
            view = self.getViewCollection()
            if view is not None:
                ref = view.getVolume()
                if ref is not None:
                    path = QFileDialog.getExistingDirectory(self,
                                                            'Select DICOM export directory', getcwd(),
                                                            options=QFileDialog.ShowDirsOnly)
                    if path:
                        path = abspath(path)
                        chdir(path)
                        wait = DialogWait()
                        wait.setInformationText('Convert ROI(s) to Dicom RTStruct...')
                        wait.open()
                        QApplication.processEvents()
                        f = ExportToRTStruct()
                        f.setReferenceVolume(ref)
                        f.setExportFolder(path)
                        for roi in items:
                            f.addROI(roi)
                        try: f.execute(wait)
                        except Exception as err:
                            wait.hide()
                            messageBox(self,
                                       'Convert ROI(s) to Dicom RTStruct....',
                                       text='RTSTRUCT conversion error: {}\n{}.'.format(type(err), str(err)))
                            return
                        wait.close()
                        mainwindow = self._getMainWindow()
                        if mainwindow is not None:
                            mainwindow.setStatusBarMessage('Checked ROI(s) converted to Dicom RTSTRUCT.')
        else: messageBox(self, 'Export to Dicom RT format', 'No ROI checked.')
    # Revision 06/11/2024 >

    def toMesh(self):
        if self.hasViewCollection() and self._listmeshwidget is not None:
            rois = self.getCheckedROI()
            n = len(rois)
            if n > 0:
                ref = self.getViewCollection().getVolume()
                wait = DialogWait(info='ROI to Mesh processing...')
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for roi in rois:
                    wait.setInformationText('{} to Mesh processing...'.format(roi.getName()))
                    wait.incCurrentProgressValue()
                    mesh = SisypheMesh()
                    mesh.createFromROI(roi, fill=False)
                    if self._listmeshwidget.isEnabled(): self._listmeshwidget.add(mesh)
                    if ref is not None:
                        wait.setInformationText('Save {}...'.format(basename(mesh.getFilename())))
                        mesh.save()
                    self._logger.info('ROI {} to Mesh {}'.format(roi.getName(), mesh.getFilename()))
                wait.close()
            else: messageBox(self, 'ROI to Mesh processing', 'No ROI checked.')
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('ROI(s) converted to mesh(es).')

    # < Revision 25/10/2024
    # add toDistance method
    def toDistance(self):
        if self.hasViewCollection():
            rois = self.getCheckedROI()
            filenames = list()
            n = len(rois)
            if n > 0:
                wait = DialogWait(info='Save distance map...')
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for roi in rois:
                    r = roi.getDistanceMap()
                    if not roi.hasFilename():
                        wait.hide()
                        filename = QFileDialog.getSaveFileName(self,
                                                               'Save distance map',
                                                               roi.getName(),
                                                               SisypheROI.getFilterExt())[0]
                        wait.show()
                        if filename:
                            filename = abspath(filename)
                            chdir(filename)
                            r.setFilename(filename)
                        else: continue
                    else:
                        r.setFilename(roi.getFilename())
                        r.setFilenamePrefix('distance')
                    wait.setInformationText('Save {}'.format(r.getBasename()))
                    wait.incCurrentProgressValue()
                    r.save()
                    self._logger.info('ROI {} to distance map {}'.format(roi.getName(), r.getFilename()))
                    filenames.append(r.getFilename())
                wait.close()
                main = self._getMainWindow()
                if main is not None:
                    # noinspection PyArgumentList
                    main.open(filenames)
            else: messageBox(self, 'Distance map from ROI(s)', 'No ROI checked.')
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Distance map processed from ROI(s).')
    # Revision 25/10/2024 >

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
                                    messageBox(self,
                                               title=title,
                                               text='ROI {} is not in same space as reference '
                                                    'volume.'.format(basename(roi.getFilename())))
                            except Exception as err:
                                messageBox(self, title=title, text='{}'.format(err))
            else: event.ignore()

    # Method aliases

    getROI = ListAttributesWidget.getItem


class ListMeshAttributesWidget(ListAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    Class to manage a list of ItemMeshAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ListAttributesWidget -> ListMeshAttributesWidget

    Last revision: 20/02/2025
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

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

        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self.remove)
        # noinspection PyUnresolvedReferences
        self._out.clicked.connect(self.addOuterSurface)
        # noinspection PyUnresolvedReferences
        self._iso.clicked.connect(self.addIsosurface)
        # noinspection PyUnresolvedReferences
        self._roi.clicked.connect(self._roiMenu)
        # noinspection PyUnresolvedReferences
        self._duplicate.clicked.connect(self.duplicate)
        # noinspection PyUnresolvedReferences
        self._overlay.clicked.connect(self._overlayMenu)
        # noinspection PyUnresolvedReferences
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

        self._new.setVisible(False)
        self._btlayout1.insertWidget(5, self._export)
        self._btlayout1.insertWidget(5, self._remove)
        self._btlayout1.insertWidget(2, self._cube)
        self._btlayout1.insertWidget(2, self._sphere)
        self._btlayout1.insertWidget(2, self._out)
        self._btlayout2.insertWidget(3, self._2roi)
        self._btlayout2.insertWidget(3, self._roi)
        self._btlayout2.insertWidget(3, self._iso)
        self._btlayout2.insertWidget(3, self._overlay)
        self._btlayout2.insertWidget(3, self._duplicate)

        self._popupExport = QMenu()
        # noinspection PyTypeChecker
        self._popupExport.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupExport.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupExport.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action = dict()
        self._action['obj'] = QAction('Export to OBJ format')
        self._action['stl'] = QAction('Export to STL format')
        self._action['vtk'] = QAction('Export to VTK format')
        self._action['xvtk'] = QAction('Export to XMLVTK format')
        # noinspection PyUnresolvedReferences
        self._action['obj'].triggered.connect(self.saveOBJ)
        # noinspection PyUnresolvedReferences
        self._action['stl'].triggered.connect(self.saveSTL)
        # noinspection PyUnresolvedReferences
        self._action['vtk'].triggered.connect(self.saveVTK)
        # noinspection PyUnresolvedReferences
        self._action['xvtk'].triggered.connect(self.saveXMLVTK)
        self._popupExport.addAction(self._action['obj'])
        self._popupExport.addAction(self._action['stl'])
        self._popupExport.addAction(self._action['vtk'])
        self._popupExport.addAction(self._action['xvtk'])
        self._export.setMenu(self._popupExport)

        self._popupCube = QMenu()
        # noinspection PyTypeChecker
        self._popupCube.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupCube.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupCube.setAttribute(Qt.WA_TranslucentBackground, True)
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
        # noinspection PyUnresolvedReferences
        self._action['cube'].triggered.connect(self.addCube)
        self._popupCube.addAction(self._action['cube'])
        self._cube.setMenu(self._popupCube)

        self._popupSphere = QMenu()
        # noinspection PyTypeChecker
        self._popupSphere.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupSphere.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupSphere.setAttribute(Qt.WA_TranslucentBackground, True)
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
        # noinspection PyUnresolvedReferences
        self._action['sphere'].triggered.connect(self.addSphere)
        self._popupSphere.addAction(self._action['sphere'])
        self._sphere.setMenu(self._popupSphere)

        self._ractions = list()
        self._popupRoi = QMenu()
        # noinspection PyTypeChecker
        self._popupRoi.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupRoi.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupRoi.setAttribute(Qt.WA_TranslucentBackground, True)
        # noinspection PyUnresolvedReferences
        self._popupRoi.aboutToShow.connect(self._roiMenu)
        self._roi.setMenu(self._popupRoi)

        self._oactions: list[QAction] = list()
        self._popupOverlay = QMenu()
        # noinspection PyTypeChecker
        self._popupOverlay.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupOverlay.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupOverlay.setAttribute(Qt.WA_TranslucentBackground, True)
        # noinspection PyUnresolvedReferences
        self._popupOverlay.aboutToShow.connect(self._overlayMenu)
        self._overlay.setMenu(self._popupOverlay)

        self._depth = LabeledSpinBox('Depth', parent=self._popupOverlay)
        self._depth.setAlignment(Qt.AlignCenter)
        self._depth.setSuffix(' mm')
        self._depth.setRange(0, 10)
        self._depth.setValue(0)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._depth)
        self._popupOverlay.addAction(action)
        self._oactions.append(action)

        self._feature = LabeledComboBox('Feature', parent=self._popupOverlay)
        self._feature.addItem('Mean')
        self._feature.addItem('Median')
        self._feature.addItem('Min')
        self._feature.addItem('Max')
        self._feature.addItem('Sum')
        self._feature.setCurrentIndex(0)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._feature)
        self._popupOverlay.addAction(action)
        self._oactions.append(action)

        self._open.setToolTip('{} Mesh(es)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} Mesh(es)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} Mesh(es)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} Mesh(es)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} Mesh(es)'.format(self._uncheckall.toolTip()))

        self._dialog = DialogThreshold(size=384)
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialog, c)

    # Private methods

    def _createWidget(self, item):
        return ItemMeshAttributesWidget(item, views=self._views, listattr=self)

    def _updateViews(self):
        if self.hasViewCollection():
            volview = self._views.getVolumeView()
            if volview is not None: volview.updateRender()

    def _roiMenu(self):
        self._ractions.clear()
        self._popupRoi.clear()
        if self.hasListROIAttributeWidget() and self._listroiwidget.isEnabled():
            rois = self._listroiwidget.getCollection()
            if len(rois) > 0:
                for roi in rois:
                    action = QAction(roi.getName())
                    # noinspection PyUnresolvedReferences
                    action.triggered.connect(lambda _, param=roi: self.addRoi([param]))
                    self._popupRoi.addAction(action)
                    self._ractions.append(action)
                action = QAction('Add all ROI(s)')
                # noinspection PyUnresolvedReferences
                action.triggered.connect(lambda _, param=rois: self.addRoi(param.getList()))
                self._popupRoi.addAction(action)
                self._ractions.append(action)
                self._popupRoi.addSeparator()
        action = QAction('Add ROI(s) from disk')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda _: self.addRoi([]))
        self._popupRoi.addAction(action)
        self._ractions.append(action)

    def _overlayMenu(self):
        self._oactions = self._oactions[:2]
        self._popupOverlay.clear()
        self._popupOverlay.addAction(self._oactions[0])
        self._popupOverlay.addAction(self._oactions[1])
        self._popupOverlay.addSeparator()
        view = self._views.getOrthogonalSliceTrajectoryViewWidget()
        if view is not None:
            action = QAction(view.getVolume().getName())
            # noinspection PyUnresolvedReferences
            action.triggered.connect(lambda dummy, v=view.getVolume(): self.addOverlay(v))
            self._popupOverlay.addAction(action)
            self._oactions.append(action)
            n = view.getOverlayCount()
            if n > 0:
                for i in range(n):
                    ovl = view.getOverlayFromIndex(i)
                    action = QAction(ovl.getName())
                    # noinspection PyUnresolvedReferences
                    action.triggered.connect(lambda dummy, v=ovl: self.addOverlay(v))
                    self._popupOverlay.addAction(action)
                    self._oactions.append(action)
            self._popupOverlay.addSeparator()
        action = QAction('Add overlay from disk')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v='': self.addOverlay(v))
        self._popupOverlay.addAction(action)
        self._oactions.append(action)

    def _getNewName(self, name: str) -> str:
        while name in self._collection:
            parts = name.split('#')
            suffix = parts[-1]
            if suffix.isdigit():
                suffix = int(suffix) + 1
                # noinspection PyTypeChecker
                parts[-1] = str(suffix)
            else: parts.append('1')
            name = '#'.join(parts)
        return name

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
        if isinstance(parent, TabMeshListWidget): return parent
        else: raise TypeError('parent type {} is not TabMeshListWidget.'.format(type(parent)))

    def hasTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabMeshListWidget
        return isinstance(parent, TabMeshListWidget)

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection): self._collection = views.getMeshCollection()
        else: self._collection = None

    def add(self, mesh):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    if isinstance(mesh, SisypheMesh):
                        title = 'Add Mesh'
                        vol = self._views.getVolume()
                        if mesh.getReferenceID() == vol.getID():
                            if mesh.getName() not in self._collection:
                                # < Revision 23/03/2025
                                # view = self._views.getVolumeView()
                                # if view is not None:
                                #    view.updateMeshes()
                                #    widget = self._addItem(mesh)
                                #    return widget
                                view = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                # < Revision 28/03/2025
                                # if view is not None: view.updateMeshes()
                                if view is not None: view.addMesh(mesh)
                                # Revision 28/03/2025 >
                                mainwindow = self._getMainWindow()
                                if mainwindow is not None:
                                    mainwindow.setStatusBarMessage('Mesh {} added.'.format(mesh.getName()))
                                widget = self._addItem(mesh)
                                self._logger.info('Add Mesh {}'.format(mesh.getFilename()))
                                return widget
                                # Revision 23/03/2025 >
                            else:
                                # noinspection PyInconsistentReturns
                                messageBox(self,
                                           title=title,
                                           text='{} mesh is already open.'.format(mesh.getName()))
                        else:
                            # noinspection PyInconsistentReturns
                            messageBox(self,
                                       title=title,
                                       text='{} mesh does not belong to {} volume (ID mismatch).'.format(
                                           mesh.getName(),
                                           vol.getBasename()))
                    else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))
                else:
                    # noinspection PyInconsistentReturns
                    messageBox(self,
                               'Add mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)
            else: raise AttributeError('_views attribute is None.')
        else: raise AttributeError('self is not enabled.')

    def addOuterSurface(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    vol = self._views.getVolume()
                    if vol is not None:
                        mesh = SisypheMesh()
                        wait = DialogWait()
                        wait.open()
                        wait.setInformationText('Outer surface mesh processing...')
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
                        self._logger.info('Add outer surface Mesh {}'.format(mesh.getName()))
                        wait.close()
                else:
                    messageBox(self,
                               'Add outer surface mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def addIsosurface(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    vol = self._views.getVolume()
                    if vol is not None:
                        self._dialog.setVolume(vol)
                        self._dialog.setThresholdFlagToMinimum()
                        self._dialog.setThresholdFlagButtonsVisibility(False)
                        if self._dialog.exec() == QDialog.Accepted:
                            value = self._dialog.getThreshold()
                            wait = DialogWait()
                            wait.setInformationText('Isosurface mesh processing...')
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
                            self._logger.info('Add isosurface {} Mesh {}'.format(value, mesh.getName()))
                            wait.close()
                else:
                    messageBox(self,
                               'Add isosurface mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def addRoi(self, rois):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                title = 'Mesh(es) from ROI(s)'
                if self.count() < self.getMaxCount():
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
                                wait = DialogWait()
                                wait.setInformationText('Open ROI(s)...')
                                wait.setProgressRange(0, n)
                                wait.setProgressVisibility(n > 1)
                                chdir(dirname(filenames[0]))
                                rois = list()
                                for filename in filenames:
                                    filename = abspath(filename)
                                    wait.setInformationText('Open {}'.format(basename(filename)))
                                    wait.incCurrentProgressValue()
                                    roi = SisypheROI()
                                    roi.load(filename)
                                    if roi.getReferenceID() == vol.getID(): rois.append(roi)
                                    else:
                                        wait.hide()
                                        messageBox(self,
                                                   title=title,
                                                   text='{} ROI does not belong to {} volume (ID mismatch).'.format(
                                                       roi.getName(), vol.getBasename()))
                                        break
                        n = len(rois)
                        if n > 0 and all([isinstance(roi, SisypheROI) for roi in rois]):
                            wait = DialogWait()
                            wait.setInformationText('Mesh(es) from ROI(s)...')
                            wait.setProgressRange(0, n)
                            wait.setProgressVisibility(n > 1)
                            wait.open()
                            for roi in rois:
                                if self.count() < self.getMaxCount():
                                    wait.setInformationText('{} mesh processing'.format(roi.getName()))
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
                                        self._logger.info('Add Mesh {} from ROI {}'.format(mesh.getName(), roi.getFilename()))
                                        if wait.getStopped(): break
                                    else:
                                        wait.hide()
                                        messageBox(self,
                                                   title=title,
                                                   text='{} ROI does not belong to {} volume (ID mismatch).'.format(
                                                       roi.getName(), vol.getBasename()))
                                        break
                                else:
                                    wait.hide()
                                    messageBox(self,
                                               title=title,
                                               text='Maximum number of Meshes reached.\n'
                                                    'Close a Mesh to add a new one.',
                                               icon=QMessageBox.Information)
                                    break
                            wait.close()
                else:
                    messageBox(self,
                               title=title,
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def addCube(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    vol = self._views.getVolume()
                    if vol is not None:
                        p = self._views.getVolumeView().getCursorWorldPosition()
                        mesh = SisypheMesh()
                        mesh.createCube(self._cubex.value(), self._cubey.value(), self._cubez.value(), p)
                        mesh.setReferenceID(vol.getID())
                        # < Revision 22/07/2024
                        # mesh.setName('Cube#{}'.format(len(self.getCollection()) + 1))
                        name = self._getNewName('Cube#1')
                        mesh.setName(name)
                        # Revision 22/07/2024 >
                        # noinspection PyTypeChecker
                        mesh.setFilename(join(vol.getDirname(), mesh.getName() + mesh.getFileExt()))
                        self.add(mesh)
                        self._logger.info('Add cube Mesh {}'.format(mesh.getName()))
                else:
                    messageBox(self,
                               'Add cube mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def addSphere(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    vol = self._views.getVolume()
                    if vol is not None:
                        p = self._views.getVolumeView().getCursorWorldPosition()
                        mesh = SisypheMesh()
                        mesh.createSphere(self._spherer.value(), p)
                        mesh.setReferenceID(vol.getID())
                        # < Revision 22/07/2024
                        # mesh.setName('Sphere#{}'.format(len(self.getCollection()) + 1))
                        name = self._getNewName('Sphere#1')
                        mesh.setName(name)
                        # Revision 22/07/2024 >
                        # noinspection PyTypeChecker
                        mesh.setFilename(join(vol.getDirname(), mesh.getName() + mesh.getFileExt()))
                        self.add(mesh)
                        self._logger.info('Add sphere Mesh {}'.format(mesh.getName()))
                else:
                    messageBox(self,
                               'Add sphere mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def duplicate(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 0:
                        wait = DialogWait(info='Duplicate checked mesh(es)...')
                        wait.setProgressRange(0, n)
                        wait.setCurrentProgressValue(0)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for mesh in meshes:
                            if self.count() < self.getMaxCount():
                                wait.setInformationText('Duplicate {} mesh...'.format(mesh.getName()))
                                wait.incCurrentProgressValue()
                                mesh2 = SisypheMesh()
                                mesh2.copyFrom(mesh)
                                # < Revision 22/07/2024
                                # mesh2.setName(mesh.getName() + str(len(self._collection) + 1))
                                name = self._getNewName(mesh.getName())
                                mesh.setName(name)
                                # Revision 22/07/2024 >
                                # noinspection PyTypeChecker
                                mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh.getFileExt()))
                                self.add(mesh2)
                                self._logger.info('Duplicate Mesh {} to {}'.format(mesh.getName(), mesh2.getName()))
                            else:
                                wait.close()
                                messageBox(self,
                                           'Duplicate checked mesh(es)',
                                           text='Maximum number of Meshes reached.\n'
                                                'Close a Mesh to add a new one.',
                                           icon=QMessageBox.Information)
                                return
                        wait.close()
                    else: messageBox(self, 'Duplicate checked mesh(es)', 'No selected mesh.')
                else:
                    messageBox(self,
                               'Duplicate checked mesh(es)',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def addOverlay(self, vol):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 0:
                        if isinstance(vol, str):
                            filename = vol
                            if filename == '' or not exists(filename):
                                dialog = DialogFileSelection()
                                if platform == 'win32':
                                    import pywinstyles
                                    cl = self.palette().base().color()
                                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                                    pywinstyles.change_header_color(dialog, c)
                                dialog.setWindowTitle('Display mesh overlay')
                                dialog.filterSisypheVolume()
                                if dialog.exec():
                                    filename = dialog.getFilename()
                            if filename != '' and exists(filename):
                                vol = SisypheVolume()
                                vol.load(filename)
                            else: vol = None
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
                            wait = DialogWait(info='Display mesh overlay...')
                            wait.setProgressRange(0, len(meshes))
                            wait.setCurrentProgressValue(0)
                            wait.setProgressVisibility(n > 1)
                            wait.open()
                            for mesh in meshes:
                                if self.count() < self.getMaxCount():
                                    wait.setInformationText('Display {} as {} mesh overlay...'.format(vol.getName(), mesh.getName()))
                                    wait.incCurrentProgressValue()
                                    mesh2 = SisypheMesh()
                                    mesh2.copyFrom(mesh)
                                    mesh2.setPointScalarColorFromVolume(vol,
                                                                        depth=self._depth.value(),
                                                                        feature=self._feature.currentText().lower(),
                                                                        wait=wait)
                                    mesh2.setName(vol.getName() + ' ' + mesh.getName())
                                    # noinspection PyTypeChecker
                                    mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                                    widget = self.add(mesh2)
                                    self._logger.info('Add overlay Mesh {}'.format(mesh2.getName()))
                                    if widget is not None: widget.setLut(vol)
                                else:
                                    wait.close()
                                    messageBox(self,
                                               'mesh(es) overlay',
                                               text='Maximum number of Meshes reached.\n'
                                                    'Close a Mesh to add a new one.',
                                               icon=QMessageBox.Information)
                                    return
                            wait.close()
                    else: messageBox(self, 'mesh(es) overlay', 'No selected mesh.')
                else:
                    messageBox(self,
                               'mesh(es) overlay',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def filter(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
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
                            wait = DialogWait(info='Filter checked mesh(es)...')
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
                                # noinspection PyTypeChecker
                                mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                                if self.count() < self.getMaxCount():
                                    self.add(mesh2)
                                    self._logger.info('Filter Mesh {}'.format(mesh.getName()))
                                else:
                                    wait.close()
                                    messageBox(self,
                                               'Filter checked mesh(es)',
                                               text='Maximum number of Meshes reached.\n'
                                                    'Close a Mesh to add a new one.',
                                               icon=QMessageBox.Information)
                                    return
                                wait.incCurrentProgressValue()
                            wait.close()
                    else: messageBox(self, 'Filter checked mesh(es)', 'No checked mesh.')
                else:
                    messageBox(self,
                               'Filter checked mesh(es)',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def dilate(self, mm=1.0):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 0:
                        wait = DialogWait(info='Checked mesh(es) dilatation...')
                        wait.setProgressRange(0, n)
                        wait.setCurrentProgressValue(0)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for mesh in meshes:
                            wait.setInformationText('{} mesh dilatation...'.format(mesh.getName()))
                            wait.incCurrentProgressValue()
                            mesh2 = SisypheMesh()
                            mesh2.copyFrom(mesh)
                            mesh2.dilate(mm)
                            if not mesh2.isEmpty():
                                # noinspection PyTypeChecker
                                mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                                self.add(mesh2)
                                self._logger.info('Dilate Mesh {}'.format(mesh.getName()))
                            else: messageBox(self, 'Checked mesh(es) dilatation', 'Empy mesh.')
                        wait.close()
                    else: messageBox(self, 'Checked mesh(es) dilatation', 'No checked mesh.')
                else:
                    messageBox(self,
                               'Checked mesh(es) dilatation',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def erode(self, mm=1.0):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 0:
                        wait = DialogWait(info='Checked mesh(es) shrinking...')
                        wait.setProgressRange(0, n)
                        wait.setCurrentProgressValue(0)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for mesh in meshes:
                            wait.setInformationText('{} mesh shrinking...'.format(mesh.getName()))
                            wait.incCurrentProgressValue()
                            mesh2 = SisypheMesh()
                            mesh2.copyFrom(mesh)
                            mesh2.erode(mm)
                            if not mesh2.isEmpty():
                                # noinspection PyTypeChecker
                                mesh2.setFilename(join(mesh.getDirname(), mesh2.getName() + mesh2.getFileExt()))
                                self.add(mesh2)
                                self._logger.info('Erode Mesh {}'.format(mesh.getName()))
                            else: messageBox(self, 'Checked mesh(es) shrinking', 'Empy mesh.')
                        wait.close()
                    else: messageBox(self, 'Checked mesh(es) shrinking', 'No checked mesh.')
                else:
                    messageBox(self,
                               'Checked mesh(es) shrinking',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def union(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 1:
                        wait = DialogWait()
                        wait.setInformationText('Checked mesh(es) union...')
                        wait.open()
                        mesh2 = SisypheMesh()
                        mesh2.copyFrom(meshes[0])
                        meshes = meshes[1:]
                        mesh2.union(meshes)
                        wait.close()
                        if not mesh2.isEmpty():
                            # noinspection PyTypeChecker
                            mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                            self.add(mesh2)
                            self._logger.info('Union Mesh {}'.format(mesh2.getName()))
                        else: messageBox(self, 'Checked mesh(es) union', 'Mesh intersection is empty.')
                    else: messageBox(self, 'Checked mesh(es) union', 'Less than two meshes checked.')
                else:
                    messageBox(self,
                               'Checked mesh(es) union',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def intersection(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    meshes = self.getCheckedMesh()
                    n = len(meshes)
                    if n > 1:
                        wait = DialogWait()
                        wait.setInformationText('Checked mesh(es) intersection...')
                        wait.open()
                        mesh2 = SisypheMesh()
                        mesh2.copyFrom(meshes[0])
                        meshes = meshes[1:]
                        mesh2.intersection(meshes)
                        wait.close()
                        if not mesh2.isEmpty():
                            # noinspection PyTypeChecker
                            mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                            self.add(mesh2)
                            self._logger.info('Intersection Mesh {}'.format(mesh2.getName()))
                        else: messageBox(self, 'Checked mesh(es) intersection', 'Mesh intersection is empty.')
                    else: messageBox(self, 'Checked mesh(es) intersection', 'Less than two meshes checked.')
                else:
                    messageBox(self,
                               'Checked mesh(es) intersection',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def difference(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    s = self.getSelectedMesh()
                    if s is not None:
                        mesh2 = SisypheMesh()
                        mesh2.copyFrom(s)
                        meshes = self.getCheckedMesh()
                        n = len(meshes)
                        if n > 0:
                            wait = DialogWait()
                            wait.setInformationText('Mesh(es) difference...')
                            wait.open()
                            mesh2.difference(meshes)
                            wait.close()
                            if not mesh2.isEmpty():
                                # noinspection PyTypeChecker
                                mesh2.setFilename(join(meshes[0].getDirname(), mesh2.getName() + mesh2.getFileExt()))
                                self.add(mesh2)
                                self._logger.info('Difference Mesh {}'.format(mesh2.getName()))
                            else: messageBox(self, 'Mesh(es) difference', 'Mesh difference is empty')
                        else: messageBox(self, 'Mesh(es) difference', 'No checked mesh.')
                    else: messageBox(self, 'Mesh(es) difference', 'No selected mesh.')
                else:
                    messageBox(self,
                               'Mesh(es) difference',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def features(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                meshes = self.getCheckedMesh()
                n = len(meshes)
                if n > 0:
                    dialog = DialogGenericResults()
                    if platform == 'win32':
                        import pywinstyles
                        cl = self.palette().base().color()
                        c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                        pywinstyles.change_header_color(dialog, c)
                    dialog.newTab('Mesh features', capture=False, clipbrd=False, scrshot=None, dataset=True)
                    dialog.newTab('Mesh surface to surface distances', capture=False, clipbrd=False, scrshot=None, dataset=True)
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
                    wait = DialogWait()
                    wait.setInformationText('Checked mesh(es) features...')
                    wait.setProgressRange(0, n)
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
                        dialog.addTreeWidgetRow(0, row, 1)
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
                        dialog.addTreeWidgetRow(1, row, 1)
                    dialog.autoSize(0)
                    wait.close()
                    self._logger.info('Dialog exec [gui.dialogGenericResults import DialogGenericResults - Mesh features]')
                    dialog.exec()
                else: messageBox(self, 'Mesh features', 'No checked mesh.')

    def saveOBJ(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait(info='Export checked mesh(es) to OBJ format...')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to OBJ format...'.format(item.getName()))
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToOBJ(join(path, mesh.getName()))
                    item.saveToOBJ(item.getFilename())
                    self._logger.info('Save Mesh {} to OBJ format'.format(mesh.getName()))
                    wait.incCurrentProgressValue()
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to OBJ format.')
            else: messageBox(self, 'Export to OBJ format', 'No checked mesh.')

    def saveSTL(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait()
                wait.setInformationText('Export checked mesh(es) to STL format...')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to STL format...'.format(item.getName()))
                    wait.incCurrentProgressValue()
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToSTL(join(path, mesh.getName()))
                        self._logger.info('Save Mesh {} to STL format'.format(mesh.getName()))
                    item.saveToSTL(item.getFilename())
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to STL format.')
            else: messageBox(self, 'Export to STL format', 'No checked mesh.')

    def saveVTK(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if len(meshes) > 0:
                wait = DialogWait()
                wait.setInformationText('Export checked mesh(es) to VTK format...')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to VTK format...'.format(item.getName()))
                    wait.incCurrentProgressValue()
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToVTK(join(path, mesh.getName()))
                    item.saveToVTK(item.getFilename())
                    self._logger.info('Save Mesh {} to VTK format'.format(mesh.getName()))
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to VTK format.')
            else: messageBox(self, 'Export to VTK format', 'No checked mesh.')

    def saveXMLVTK(self):
        if self.hasViewCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                wait = DialogWait()
                wait.setInformationText('Export checked mesh(es) to XMLVTK format...')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.open()
                for mesh in meshes:
                    item = mesh.getItem()
                    wait.setInformationText('Export {} mesh to XMLVTK format...'.format(item.getName()))
                    wait.incCurrentProgressValue()
                    if not item.hasFilename():
                        path = self.getViewCollection().getVolume().getFilename()
                        item.saveToXMMLVTK(join(path, mesh.getName()))
                    item.saveToXMLVTK(item.getFilename())
                    self._logger.info('Save Mesh {} to XMLVTK format'.format(mesh.getName()))
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Export checked mesh(es) to XMLVTK format.')
            else: messageBox(self, 'Export to XMLVTK format', 'No checked mesh.')

    def open(self):
        if self.isEnabled():
            if self.hasViewCollection() and self.hasCollection():
                if self.count() < self.getMaxCount():
                    title = 'Open mesh(es)'
                    filt = 'Mesh (*{})'.format(SisypheMesh.getFileExt())
                    filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
                    QApplication.processEvents()
                    if filenames:
                        n = len(filenames)
                        chdir(dirname(filenames[0]))
                        wait = DialogWait()
                        wait.setInformationText('Open mesh(es)...')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for filename in filenames:
                            filename = abspath(filename)
                            mesh = SisypheMesh()
                            try:
                                wait.setInformationText('Open {}...'.format(basename(filename)))
                                wait.incCurrentProgressValue()
                                mesh.load(filename)
                                self.add(mesh)
                            except Exception as err:
                                wait.hide()
                                messageBox(self, title=title, text='{}'.format(err))
                                wait.show()
                        wait.close()
                else:
                    messageBox(self,
                               'Open Mesh',
                               text='Maximum number of Meshes reached.\n'
                                    'Close a Mesh to add a new one.',
                               icon=QMessageBox.Information)

    def remove(self):
        if self.hasViewCollection() and self.hasCollection():
            meshes = self.getCheckedMesh()
            n = len(meshes)
            if n > 0:
                view = self._views.getOrthogonalSliceTrajectoryViewWidget()
                if view is not None:
                    for mesh in meshes:
                        view.removeMesh(mesh)
                        self._logger.info('Remove Mesh {}'.format(mesh.getName()))
                super().remove()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Checked mesh(es) removed.')

    def removeItem(self, w):
        if self.hasViewCollection() and self.hasCollection():
            mesh = w.getMesh()
            view = self._views.getOrthogonalSliceTrajectoryViewWidget()
            if view is not None: view.removeMesh(mesh)
            super().removeItem(w)
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} mesh removed.'.format(mesh.getName()))

    def removeAll(self):
        if self._views is not None:
            view = self._views.getOrthogonalSliceTrajectoryViewWidget()
            if view is not None: view.removeAllMeshes()
        super().removeAll()
        self._logger.info('Remove all meshes')
        mainwindow = self._getMainWindow()
        if mainwindow is not None:
            mainwindow.setStatusBarMessage('All Mesh(es) removed.')

    def toRoi(self):
        if self.isEnabled():
            if self.hasViewCollection() and self._listroiwidget is not None:
                meshes = self.getCheckedMesh()
                n = len(meshes)
                if n > 0:
                    ref = self.getViewCollection().getVolume()
                    wait = DialogWait()
                    wait.setInformationText('Mesh to ROI processing...')
                    wait.setProgressRange(0, n)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    for mesh in meshes:
                        wait.setInformationText('{} to ROI processing...'.format(mesh.getName()))
                        wait.incCurrentProgressValue()
                        roi = mesh.convertToSisypheROI(ref)
                        if self._listroiwidget.isEnabled(): self._listroiwidget.add(roi)
                        if ref is not None:
                            wait.setInformationText('Save {}...'.format(basename(roi.getFilename())))
                            roi.save()
                            self._logger.info('Mesh {} to ROI {}'.format(mesh.getName(), roi.getFilename()))
                    wait.close()
                else: messageBox(self, 'Mesh to ROI processing', 'No checked mesh.')
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
                                messageBox(self, title=title, text='{}'.format(err))
            else: event.ignore()

    # Method aliases

    getMesh = ListAttributesWidget.getItem


class ListToolAttributesWidget(ListAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    Class to manage a list of ItemToolAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ListAttributesWidget -> ListToolAttributesWidget

    Last revision: 02/11/2024
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._filename: str = ''
        self._connected: bool = False

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

        # noinspection PyUnresolvedReferences
        self._target.clicked.connect(self.newHandle)
        # noinspection PyUnresolvedReferences
        self._trajectory.clicked.connect(self.newLine)
        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self.remove)
        # noinspection PyUnresolvedReferences
        self._duplicate.clicked.connect(self.duplicate)
        # noinspection PyUnresolvedReferences
        self._features.clicked.connect(self.features)
        # noinspection PyUnresolvedReferences
        self._features2.clicked.connect(self.features2)

        self._target.setToolTip('Add new target tool')
        self._trajectory.setToolTip('Add new trajectory tool')
        self._remove.setToolTip('Remove checked tool(s)')
        self._duplicate.setToolTip('Duplicate selected tool')
        self._features.setToolTip('Tool features')
        self._features2.setToolTip('Tool and mesh relationships')

        self._new.setVisible(False)
        self._btlayout1.insertWidget(5, self._remove)
        self._btlayout1.insertWidget(2, self._trajectory)
        self._btlayout1.insertWidget(2, self._target)
        self._btlayout2.insertWidget(3, self._features2)
        self._btlayout2.insertWidget(3, self._features)
        self._btlayout2.insertWidget(3, self._duplicate)

        self._open.setToolTip('{} tool(s)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} tool(s)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} tool(s)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} tool(s)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} tool(s)'.format(self._uncheckall.toolTip()))

        self._dialogtarget = DialogTarget()
        self._dialogduplicate = DialogFromXml('Duplicate tool', ['DuplicateTool'])
        self._dialogfeatures = DialogGenericResults()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._dialogtarget, c)
            pywinstyles.change_header_color(self._dialogduplicate, c)
            pywinstyles.change_header_color(self._dialogfeatures, c)

    # Private methods

    # noinspection PyUnusedLocal
    def _synchroniseToolColorChanged(self, widget, tool):
        if not self.isEmpty():
            for i in range(self.count()):
                if self.getTool(i).getName() == tool.getName():
                    w = self.getWidget(i)
                    c = tool.getColor()
                    if w.getColor() != c:
                        w.setColor(c[0], c[1], c[2], signal=False)

    # noinspection PyUnusedLocal
    def _synchroniseToolRemoved(self, widget, tool, removeall):
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

    # noinspection PyUnusedLocal
    def _updateTargets(self, widget, tool):
        if self.hasViewCollection():
            if len(self._collection) > 0:
                for i in range(len(self._list)):
                    w = self.getWidget(i)
                    itool = w.getTool()
                    if itool != tool:
                        if itool.isDynamic():
                            dlg = w.getDialogTarget()
                            dlg.initPoints()
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
        return tools

    def getSelectedTool(self):
        return self._getSelectedWidget().getTool()

    def getTabToolsWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabTargetListWidget
        # noinspection PyInconsistentReturns
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
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    self._dialogtarget.hideTrajectoryFields()
                    self._dialogtarget.clear()
                    self._dialogtarget.setDefaultPosition()
                    self._logger.info('Dialog exec [gui.dialogTarget.DialogTarget - New target]')
                    if self._dialogtarget.exec() == QDialog.Accepted:
                        view = self._views.getVolumeView()
                        if view is not None:
                            p = self._dialogtarget.getTargetPosition()
                            item = view.addTarget(p)
                            if self._dialogtarget.isRelativeOrWeightedPosition(): item.setDynamic()
                            widget = self._addItem(item)
                            widget.setLock(item.isDynamic())
                            widget.getDialogTarget().copyFieldsFrom(self._dialogtarget)
                            widget.setDefaultAttributesFromSettings()
                            widget.focusTarget()
                            if not self._connected:
                                # to update relative tools position
                                view.ToolMoved.connect(self._updateTargets)
                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                if slcviews is not None:
                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                            self._logger.info('New target tool {}'.format(item.getName()))
                            mainwindow = self._getMainWindow()
                            if mainwindow is not None:
                                mainwindow.setStatusBarMessage('Add new point {}.'.format(item.getName()))
                else:
                    messageBox(self,
                               'Add new target',
                               text='Maximum number of tools reached.\n'
                                    'Close a tool to add a new one.',
                               icon=QMessageBox.Information)

    def newLine(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    self._dialogtarget.showTrajectoryFields()
                    self._dialogtarget.clear()
                    self._dialogtarget.setDefaultPosition()
                    self._logger.info('Dialog exec [gui.dialogTarget.DialogTarget - New trajectory]')
                    if self._dialogtarget.exec() == QDialog.Accepted:
                        view = self._views.getVolumeView()
                        if view is not None:
                            r = self._dialogtarget.getAttributes()
                            item = view.addTrajectory(p1=r['entry'], p2=r['target'])
                            if self._dialogtarget.isRelativeOrWeightedPosition(): item.setDynamic()
                            widget = self._addItem(item)
                            widget.setLock(item.isDynamic())
                            widget.getDialogTarget().copyFieldsFrom(self._dialogtarget)
                            widget.setDefaultAttributesFromSettings()
                            widget.focusTarget()
                            if not self._connected:
                                # to update relative tools position
                                view.ToolMoved.connect(self._updateTargets)
                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                if slcviews is not None:
                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                            self._logger.info('New trajectory tool {}'.format(item.getName()))
                            mainwindow = self._getMainWindow()
                            if mainwindow is not None:
                                mainwindow.setStatusBarMessage('Add new trajectory {}.'.format(item.getName()))
                else:
                    messageBox(self,
                               'Add new trajectory',
                               text='Maximum number of tools reached.\n'
                                    'Close a tool to add a new one.',
                               icon=QMessageBox.Information)

    def open(self):
        if self.isEnabled():
            if self.hasViewCollection():
                title = 'Open tool(s)'
                if self.count() < self.getMaxCount():
                    filt = '{};;{};;{}'.format(ToolWidgetCollection.getFilterExt(),
                                               HandleWidget.getFilterExt(),
                                               LineWidget.getFilterExt())
                    filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
                    QApplication.processEvents()
                    if filenames:
                        n = len(filenames)
                        chdir(dirname(filenames[0]))
                        wait = DialogWait()
                        wait.setInformationText('Open tool(s)...')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for filename in filenames:
                            wait.setInformationText('Open {}...'.format(basename(filename)))
                            wait.incCurrentProgressValue()
                            ext = splitext(filename)[1]
                            view = self._views.getVolumeView()
                            if view is not None:
                                if ext == ToolWidgetCollection.getFileExt():
                                    tools = ToolWidgetCollection()
                                    try: tools.load(filename)
                                    except Exception as err:
                                        messageBox(self, 'open tools', text='{}'.format(err))
                                        tools = None
                                    vol = self._views.getVolume()
                                    if tools is not None and vol is not None:
                                        if tools.hasSameID(vol):
                                            for tool in tools:
                                                if self.count() < self.getMaxCount():
                                                    if isinstance(tool, HandleWidget):
                                                        p = tool.getPosition()
                                                        item = view.addTarget(p, tool.getName())
                                                        tool.copyAttributesTo(item)
                                                        widget = self._addItem(item)
                                                        widget.getDialogTarget().setAbsolutePosition(p)
                                                        widget.updateSettingsFromAttributes()
                                                        if not self._connected:
                                                            # to update relative tools position
                                                            view.ToolMoved.connect(self._updateTargets)
                                                            slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                                            if slcviews is not None:
                                                                slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                                slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                                slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                                        self._logger.info('Add target {}'.format(item.getName()))
                                                    elif isinstance(tool, LineWidget):
                                                        p = tool.getPosition2()
                                                        item = view.addTrajectory(p1=tool.getPosition1(),
                                                                                  p2=p,
                                                                                  name=tool.getName())
                                                        tool.copyAttributesTo(item)
                                                        widget = self._addItem(item)
                                                        widget.getDialogTarget().setAbsolutePosition(p)
                                                        widget.updateSettingsFromAttributes()
                                                        if not self._connected:
                                                            # to update relative tools position
                                                            view.ToolMoved.connect(self._updateTargets)
                                                            slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                                            if slcviews is not None:
                                                                slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                                slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                                slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                                        self._logger.info('Add trajectory {}'.format(item.getName()))
                                                else:
                                                    wait.close()
                                                    messageBox(self,
                                                               title=title,
                                                               text='Maximum number of tools reached.\n'
                                                                    'Close a tool to add a new one.',
                                                               icon=QMessageBox.Information)
                                                    return
                                        else:
                                            messageBox(self,
                                                       'Open tools',
                                                       text='{} tools does not belong to {} volume (ID mismatch).'.format(
                                                           basename(filename), vol.getBasename()))
                                elif ext == HandleWidget.getFileExt():
                                    if self.count() < self.getMaxCount():
                                        tool = HandleWidget('')
                                        try: tool.load(filename)
                                        except Exception as err:
                                            messageBox(self, 'open tools', text='{}'.format(err))
                                            tool = None
                                        if tool is not None:
                                            p = tool.getPosition()
                                            item = view.addTarget(p, tool.getName())
                                            tool.copyAttributesTo(item)
                                            widget = self._addItem(item)
                                            widget.getDialogTarget().setAbsolutePosition(p)
                                            widget.focusTarget()
                                            widget.updateSettingsFromAttributes()
                                            if not self._connected:
                                                # to update relative tools position
                                                view.ToolMoved.connect(self._updateTargets)
                                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                                if slcviews is not None:
                                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                            self._logger.info('Add target {}'.format(item.getName()))
                                    else:
                                        wait.close()
                                        messageBox(self,
                                                   title=title,
                                                   text='Maximum number of tools reached.\n'
                                                        'Close a tool to add a new one.',
                                                   icon=QMessageBox.Information)
                                        return
                                elif ext == LineWidget.getFileExt():
                                    if self.count() < self.getMaxCount():
                                        tool = LineWidget('')
                                        try: tool.load(filename)
                                        except Exception as err:
                                            messageBox(self, 'open tools', text='{}'.format(err))
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
                                            if not self._connected:
                                                # to update relative tools position
                                                view.ToolMoved.connect(self._updateTargets)
                                                slcviews = self._views.getOrthogonalSliceTrajectoryViewWidget()
                                                if slcviews is not None:
                                                    slcviews[0, 1].ToolMoved.connect(self._updateTargets)
                                                    slcviews[1, 0].ToolMoved.connect(self._updateTargets)
                                                    slcviews[1, 1].ToolMoved.connect(self._updateTargets)
                                            self._logger.info('Add trajectory {}'.format(item.getName()))
                                    else:
                                        wait.close()
                                        messageBox(self,
                                                   title=title,
                                                   text='Maximum number of tools reached.\n'
                                                        'Close a tool to add a new one.',
                                                   icon=QMessageBox.Information)
                                        return
                            mainwindow = self._getMainWindow()
                            if mainwindow is not None:
                                mainwindow.setStatusBarMessage('open tool(s).')
                        wait.close()
                else:
                    messageBox(self,
                               title=title,
                               text='Maximum number of tools reached.\n'
                                    'Close a tool to add a new one.',
                               icon=QMessageBox.Information)

    def duplicate(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    tool = self.getSelectedTool()
                    if tool is not None:
                        settings = self._dialogduplicate.getFieldsWidget(0)
                        vol = self._views.getVolume()
                        if vol is not None: settings.getParameterWidget('Orientation').setVisible(vol.getACPC().hasACPC())
                        self._logger.info('Dialog exec [gui.dialogFromXml.DialogFromXml - Tool duplicate]')
                        if self._dialogduplicate.exec() == QDialog.Accepted:
                            lat = settings.getParameterValue('Laterality')
                            if lat is None: lat = 0.0
                            ap = settings.getParameterValue('Antero-posterior')
                            if ap is None: ap = 0.0
                            h = settings.getParameterValue('Height')
                            if h is None: h = 0.0
                            o = settings.getParameterValue('Orientation')[0]
                            if o is None: o = 'Native'
                            from Sisyphe.core.sisypheTools import HandleWidget, LineWidget
                            if o == 'Native':
                                if isinstance(tool, HandleWidget):
                                    p = list(tool.getPosition())
                                    p[0] += lat
                                    p[1] += ap
                                    p[2] += h
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTarget(p, name)
                                    item.setStatic()
                                    tool.copyAttributesTo(item)
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                                elif isinstance(tool, LineWidget):
                                    p1 = list(tool.getPosition1())
                                    p2 = list(tool.getPosition2())
                                    p1[0] += lat
                                    p1[1] += ap
                                    p1[2] += h
                                    p2[0] += lat
                                    p2[1] += ap
                                    p2[2] += h
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTrajectory(p1, p2, name)
                                    item.setStatic()
                                    tool.copyAttributesTo(item)
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                            elif o == 'Camera':
                                v0 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 1].getVtkPlane().GetNormal()
                                v1 = self._views.getOrthogonalSliceTrajectoryViewWidget()[1, 0].getVtkPlane().GetNormal()
                                v2 = self._views.getOrthogonalSliceTrajectoryViewWidget()[0, 1].getVtkPlane().GetNormal()
                                if isinstance(self._item, HandleWidget):
                                    p = list(self._item.getPosition())
                                    p[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                                    p[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                                    p[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTarget(p, name)
                                    item.setStatic()
                                    tool.copyAttributesTo(item)
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                                elif isinstance(self._item, LineWidget):
                                    p1 = list(self._item.getPosition1())
                                    p2 = list(self._item.getPosition2())
                                    p1[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                                    p1[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                                    p1[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                                    p2[0] += v0[0] * lat + v1[0] * ap + v2[0] * h
                                    p2[1] += v0[1] * lat + v1[1] * ap + v2[1] * h
                                    p2[2] += v0[2] * lat + v1[2] * ap + v2[2] * h
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTrajectory(p1, p2, name)
                                    item.setStatic()
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                            else:
                                if isinstance(tool, HandleWidget):
                                    p = list(tool.getPosition())
                                    p = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p)
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTarget(p, name)
                                    item.setStatic()
                                    tool.copyAttributesTo(item)
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                                elif isinstance(tool, LineWidget):
                                    p1 = list(tool.getPosition1())
                                    p2 = list(tool.getPosition2())
                                    p1 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p1)
                                    p2 = vol.getACPC().getPointFromRelativeDistanceToReferencePoint((lat, ap, h), p2)
                                    if lat == ap == h == 0.0: name = '{} copy'.format(tool.getName())
                                    else: name = '{} #{:.1f} #{:.1f} #{:.1f}'.format(tool.getName(), ap, lat, h)
                                    item = self._views.getVolumeView().addTrajectory(p1, p2, name)
                                    item.setStatic()
                                    tool.copyAttributesTo(item)
                                    widget = self._addItem(item)
                                    widget.focusTarget()
                                    widget.updateSettingsFromAttributes()
                            mainwindow = self._getMainWindow()
                            if mainwindow is not None:
                                mainwindow.setStatusBarMessage('Selected tools duplicated.')
                else:
                    messageBox(self,
                               'Duplicate tool',
                               text='Maximum number of tools reached.\n'
                                    'Close a tool to add a new one.',
                               icon=QMessageBox.Information)

    def features(self):

        def toStr(v):
            return '{:.1f} {:.1f} {:.1f}'.format(v[0], v[1], v[2])

        if self.isEnabled():
            if self.hasViewCollection():
                if len(self._collection) > 0:
                    wait = DialogWait()
                    wait.setInformationText('Compute coordinates and distances...')
                    wait.open()
                    self._dialogfeatures.clear()
                    from Sisyphe.core.sisypheTools import HandleWidget
                    from Sisyphe.core.sisypheTools import LineWidget
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
                                                    if subj == 0:
                                                        # noinspection PyTypeChecker
                                                        r.append(toolr.getDistanceToPoint(toolc.getPosition2()))
                                                    # toolc entry, toolr point
                                                    elif subj == 1:
                                                        # noinspection PyTypeChecker
                                                        r.append(toolr.getDistanceToPoint(toolc.getPosition1()))
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
                    wait.close()
                    self._dialogfeatures.autoSize(0)
                    self._logger.info('Dialog exec [gui.dialogGenericResults.DialogGenericResults - Tool features]')
                    self._dialogfeatures.exec()
                else:
                    messageBox(self,
                               'Compute coordinates and distances...',
                               'No target or trajectory.')

    def features2(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if len(self._collection) > 0:
                    self._dialogfeatures.clear()
                    meshes = self._views.getMeshCollection()
                    if meshes is not None and len(meshes) > 0:
                        wait = DialogWait()
                        wait.setInformationText('Compute tool and mesh distances...')
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
                        from Sisyphe.core.sisypheTools import HandleWidget
                        from Sisyphe.core.sisypheTools import LineWidget
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
                        self._logger.info('Dialog exec [gui.dialogGenericResults.DialogGenericResults - Tool features (mesh distances)]')
                        self._dialogfeatures.exec()
                    else:
                        messageBox(self,
                                   'Compute tool and mesh distances...',
                                   'No mesh.')
                else:
                    messageBox(self,
                               'Compute tool and mesh distances...',
                               'No target or trajectory.')

    def remove(self):
        if self.hasViewCollection():
            tools = self.getCheckedTool()
            if tools is not None and len(tools) > 0:
                for tool in tools:
                    view = self._views.getVolumeView()
                    if view is not None: view.removeTool(tool.getName())
                    super().remove()
                    self._logger.info('Remove tool {}'.format(tool.getName()))
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('Tool(s) removed.')

    def removeItem(self, w):
        if self.hasViewCollection():
            tool = w.getTool()
            view = self._views.getVolumeView()
            if view is not None: view.removeTool(tool.getName())
            mainwindow = self._getMainWindow()
            if mainwindow is not None:
                mainwindow.setStatusBarMessage('{} tool removed.'.format(tool.getName()))
            super().removeItem(w)

    def removeAll(self):
        if self.hasViewCollection():
            self._views.getVolumeView().removeAllTools()
        super().removeAll()
        self._logger.info('Remove all tools')
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
                    wait = DialogWait()
                    wait.setInformationText('Save {}...'.format(basename(filename)))
                    wait.open()
                    self._collection.setReferenceID(vol)
                    self._collection.saveAs(filename)
                    self._filename = filename
                    wait.close()
                    self._logger.info('Save tools {}'.format(filename))
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('{} tools saved.'.format(basename(filename)))

    # Qt event

    def dropEvent(self, event):
        if self.hasViewCollection():
            if event.mimeData().hasText():
                event.acceptProposedAction()
                files = event.mimeData().text().split('\n')
                for file in files:
                    if file != '':
                        filename = file.replace('file://', '')
                        from Sisyphe.core.sisypheTools import HandleWidget
                        from Sisyphe.core.sisypheTools import LineWidget
                        from Sisyphe.core.sisypheTools import ToolWidgetCollection
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


class ListBundleAttributesWidget(ListAttributesWidget):
    """
    Description
    ~~~~~~~~~~~

    Class to manage a list of ItemBundleAttributesWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ListAttributesWidget -> ListBundleAttributesWidget

    Last revision: 11/04/2025
    """

    # Class constant

    _MAXSTREAMLINES: int = 10000

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._ID = ''
        self._collection: list[str] = list()
        self._listroiwidget = None
        self._listmeshwidget = None

        self._dissection = IconPushButton('tracking.png', size=ListAttributesWidget._VSIZE)
        self._interactive = IconPushButton('3daxis.png', size=ListAttributesWidget._VSIZE)
        self._remove = IconPushButton('cross.png', size=ListAttributesWidget._VSIZE)
        self._filter = IconPushButton('filter.png', size=ListAttributesWidget._VSIZE)
        self._cluster = IconPushButton('cluster.png', size=ListAttributesWidget._VSIZE)
        self._centroid = IconPushButton('centroid.png', size=ListAttributesWidget._VSIZE)
        self._tomap = IconPushButton('map.png', size=ListAttributesWidget._VSIZE)
        self._toroi = IconPushButton('roi.png', size=ListAttributesWidget._VSIZE)
        self._tomesh = IconPushButton('mesh.png', size=ListAttributesWidget._VSIZE)
        self._stat = IconPushButton('statistics.png', size=ListAttributesWidget._VSIZE)
        self._duplicate = IconPushButton('duplicate.png', size=ListAttributesWidget._VSIZE)
        self._union = IconPushButton('attach.png', size=ListAttributesWidget._VSIZE)

        self._treshroi = LabeledSpinBox(title='Count threshold', fontsize=12)
        self._treshroi.setRange(1, 1000)
        self._treshroi.setValue(10)
        self._treshroi.setToolTip('Number of streamlines per voxel threshold.')

        self._treshmesh = LabeledSpinBox(title='Count threshold', fontsize=12)
        self._treshmesh.setRange(1, 1000)
        self._treshmesh.setValue(10)
        self._treshmesh.setToolTip('Number of streamlines per voxel threshold.')

        self._action = dict()

        self._popupInteractive = QMenu()
        # noinspection PyTypeChecker
        self._popupInteractive.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupInteractive.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupInteractive.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['excl0'] = QAction('Exclude streamlines that cross cursor sphere')
        # noinspection PyUnresolvedReferences
        self._action['excl0'].triggered.connect(lambda _: self.interactive(0))
        self._popupInteractive.addAction(self._action['excl0'])
        self._action['excl1'] = QAction('Exclude streamlines that do not cross cursor sphere')
        # noinspection PyUnresolvedReferences
        self._action['excl1'].triggered.connect(lambda _: self.interactive(1))
        self._popupInteractive.addAction(self._action['excl1'])
        self._action['excl2'] = QAction('Exclude streamlines that cross axial slice')
        # noinspection PyUnresolvedReferences
        self._action['excl2'].triggered.connect(lambda _: self.interactive(2))
        self._popupInteractive.addAction(self._action['excl2'])
        self._action['excl3'] = QAction('Exclude streamlines that do not cross axial slice')
        # noinspection PyUnresolvedReferences
        self._action['excl3'].triggered.connect(lambda _: self.interactive(3))
        self._popupInteractive.addAction(self._action['excl3'])
        self._action['excl4'] = QAction('Exclude streamlines that cross coronal slice')
        # noinspection PyUnresolvedReferences
        self._action['excl4'].triggered.connect(lambda _: self.interactive(4))
        self._popupInteractive.addAction(self._action['excl4'])
        self._action['excl5'] = QAction('Exclude streamlines that do not cross coronal slice')
        # noinspection PyUnresolvedReferences
        self._action['excl5'].triggered.connect(lambda _: self.interactive(5))
        self._popupInteractive.addAction(self._action['excl5'])
        self._action['excl6'] = QAction('Exclude streamlines that cross sagittal slice')
        # noinspection PyUnresolvedReferences
        self._action['excl6'].triggered.connect(lambda _: self.interactive(6))
        self._popupInteractive.addAction(self._action['excl6'])
        self._action['excl7'] = QAction('Exclude streamlines that do not cross sagittal slice')
        # noinspection PyUnresolvedReferences
        self._action['excl7'].triggered.connect(lambda _: self.interactive(7))
        self._popupInteractive.addAction(self._action['excl7'])
        self._popupInteractive.addSeparator()
        self._interactive.setMenu(self._popupInteractive)

        self._popupToROI = QMenu()
        # noinspection PyTypeChecker
        self._popupToROI.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupToROI.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupToROI.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._treshroi)
        self._popupToROI.addAction(a)
        self._action['toroi'] = QAction('Convert to ROI(s)...')
        # noinspection PyUnresolvedReferences
        self._action['toroi'].triggered.connect(self.toROI)
        self._popupToROI.addAction(self._action['toroi'])
        self._toroi.setMenu(self._popupToROI)

        self._popupToMesh = QMenu()
        # noinspection PyTypeChecker
        self._popupToMesh.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupToMesh.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupToMesh.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._treshmesh)
        self._popupToMesh.addAction(a)
        self._action['tomesh'] = QAction('Convert to Mesh(es)...')
        # noinspection PyUnresolvedReferences
        self._action['tomesh'].triggered.connect(self.toMesh)
        self._popupToMesh.addAction(self._action['tomesh'])
        self._tomesh.setMenu(self._popupToMesh)

        self._popupDuplicate = QMenu()
        # noinspection PyTypeChecker
        self._popupDuplicate.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupDuplicate.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupDuplicate.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['dup1'] = QAction('with original step...')
        # noinspection PyUnresolvedReferences
        self._action['dup1'].triggered.connect(lambda _: self.duplicate(0))
        self._popupDuplicate.addAction(self._action['dup1'])
        self._action['dup2'] = QAction('with 0.5 mm regular step...')
        # noinspection PyUnresolvedReferences
        self._action['dup2'].triggered.connect(lambda _: self.duplicate(1))
        self._popupDuplicate.addAction(self._action['dup2'])
        self._action['dup3'] = QAction('with 1.0 mm regular step...')
        # noinspection PyUnresolvedReferences
        self._action['dup3'].triggered.connect(lambda _: self.duplicate(2))
        self._popupDuplicate.addAction(self._action['dup3'])
        self._action['dup4'] = QAction('with 2.0 mm regular step...')
        # noinspection PyUnresolvedReferences
        self._action['dup4'].triggered.connect(lambda _: self.duplicate(3))
        self._popupDuplicate.addAction(self._action['dup4'])
        self._action['dup5'] = QAction('compressed with non-regular step...')
        # noinspection PyUnresolvedReferences
        self._action['dup5'].triggered.connect(lambda _: self.duplicate(4))
        self._popupDuplicate.addAction(self._action['dup5'])
        self._duplicate.setMenu(self._popupDuplicate)

        self._popupStatistics = QMenu()
        # noinspection PyTypeChecker
        self._popupStatistics.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupStatistics.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupStatistics.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['stat1'] = QAction('Cluster confidence statistics...')
        # noinspection PyUnresolvedReferences
        self._action['stat1'].triggered.connect(lambda _: self.statistics(0))
        self._popupStatistics.addAction(self._action['stat1'])
        self._action['stat2'] = QAction('Length statistics...')
        # noinspection PyUnresolvedReferences
        self._action['stat2'].triggered.connect(lambda _: self.statistics(1))
        self._popupStatistics.addAction(self._action['stat2'])
        self._action['stat3'] = QAction('Mean curvature statistics...')
        # noinspection PyUnresolvedReferences
        self._action['stat3'].triggered.connect(lambda _: self.statistics(2))
        self._popupStatistics.addAction(self._action['stat3'])
        self._action['stat4'] = QAction('Cosine distance between end vectors statistics...')
        # noinspection PyUnresolvedReferences
        self._action['stat4'].triggered.connect(lambda _: self.statistics(3))
        self._popupStatistics.addAction(self._action['stat4'])
        self._action['stat5'] = QAction('Euclidean distance between end points statistics...')
        # noinspection PyUnresolvedReferences
        self._action['stat5'].triggered.connect(lambda _: self.statistics(4))
        self._popupStatistics.addAction(self._action['stat5'])

        self._stat.setMenu(self._popupStatistics)

        # noinspection PyUnresolvedReferences
        self._dissection.clicked.connect(self.dissection)
        # noinspection PyUnresolvedReferences
        self._filter.clicked.connect(self.filter)
        # noinspection PyUnresolvedReferences
        self._cluster.clicked.connect(self.cluster)
        # noinspection PyUnresolvedReferences
        self._centroid.clicked.connect(self.centroid)
        # noinspection PyUnresolvedReferences
        self._remove.clicked.connect(self.remove)
        # noinspection PyUnresolvedReferences
        self._tomap.clicked.connect(self.toMap)
        # noinspection PyUnresolvedReferences
        self._union.clicked.connect(self.union)

        self._remove.setToolTip('Remove checked bundle(s)')
        self._filter.setToolTip('Checked bundle(s) filtering')
        self._cluster.setToolTip('Checked bundle(s) clustering')
        self._centroid.setToolTip('Generate centroid streamline(s) of the checked bundle(s)')
        self._tomap.setToolTip('Generate density map of the checked bundle(s)')
        self._toroi.setToolTip('Generate ROI from checked bundle(s)')
        self._tomesh.setToolTip('Generate mesh from checked bundle(s)')
        self._stat.setToolTip('Checked bundle(s) statistics')
        self._dissection.setToolTip('Checked bundle(s) streamlines selection by ROI')
        self._interactive.setToolTip('Checked bundle(s) interactive streamlines selection')
        self._duplicate.setToolTip('Duplicate checked bundle(s)')
        self._union.setToolTip('Checked bundle(s) union')
        self._open.setToolTip('{} bundle(s)'.format(self._open.toolTip()))
        self._saveall.setToolTip('{} bundle(s)'.format(self._saveall.toolTip()))
        self._removeall.setToolTip('{} bundle(s)'.format(self._removeall.toolTip()))
        self._checkall.setToolTip('{} bundle(s)'.format(self._checkall.toolTip()))
        self._uncheckall.setToolTip('{} bundle(s)'.format(self._uncheckall.toolTip()))

        self._new.setVisible(False)
        self._btlayout1.insertWidget(5, self._tomesh)
        self._btlayout1.insertWidget(5, self._toroi)
        self._btlayout1.insertWidget(5, self._tomap)
        self._btlayout1.insertWidget(5, self._duplicate)
        self._btlayout1.insertWidget(5, self._union)
        self._btlayout1.insertWidget(5, self._remove)
        self._btlayout2.insertWidget(3, self._stat)
        self._btlayout2.insertWidget(3, self._centroid)
        self._btlayout2.insertWidget(3, self._cluster)
        self._btlayout2.insertWidget(3, self._filter)
        self._btlayout2.insertWidget(3, self._interactive)
        self._btlayout2.insertWidget(3, self._dissection)

        self._roidialog = DialogStreamlinesROISelection()
        self._fltdialog = DialogStreamlinesFiltering()
        self._cltdialog = DialogStreamlinesClustering()
        self._statdialog = DialogGenericResults()
        self._statdialog.setWindowTitle('Bundle statistics')
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._roidialog, c)
            pywinstyles.change_header_color(self._fltdialog, c)
            pywinstyles.change_header_color(self._cltdialog, c)
            pywinstyles.change_header_color(self._statdialog, c)

    # Private methods

    def _createWidget(self, item):
        if self.hasViewCollection():
            return ItemBundleAttributesWidget(item, views=self._views, listattr=self)
        else: raise AttributeError('_views attribute is None.')

    def _updateViews(self):
        if self.hasViewCollection():
            view = self._views.getVolumeView()
            if view is not None: view.updateRender()

    def _notAlreadyInList(self, item):
        return not (item in self._collection)

    def _getNewName(self, name: str) -> str:
        if name in ('', 'all', 'tractogram'): name = 'bundle#1'
        while name in self._collection:
            parts = name.split('#')
            # noinspection PyUnresolvedReferences
            suffix = parts[-1]
            if suffix.isdigit():
                suffix = int(suffix) + 1
                parts[-1] = str(suffix)
            else: parts.append('1')
            name = '#'.join(parts)
        return name

    # Public methods

    def setIconSize(self, size=ListAttributesWidget._VSIZE) -> None:
        super().setIconSize(size)
        self._dissection.setIconSize(QSize(size - 8, size - 8))
        self._dissection.setFixedSize(size, size)
        self._interactive.setIconSize(QSize(size - 8, size - 8))
        self._interactive.setFixedSize(size, size)
        self._remove.setIconSize(QSize(size - 8, size - 8))
        self._remove.setFixedSize(size, size)
        self._filter.setIconSize(QSize(size - 8, size - 8))
        self._filter.setFixedSize(size, size)
        self._cluster.setIconSize(QSize(size - 8, size - 8))
        self._cluster.setFixedSize(size, size)
        self._centroid.setIconSize(QSize(size - 8, size - 8))
        self._centroid.setFixedSize(size, size)
        self._tomap.setIconSize(QSize(size - 8, size - 8))
        self._tomap.setFixedSize(size, size)
        self._toroi.setIconSize(QSize(size - 8, size - 8))
        self._toroi.setFixedSize(size, size)
        self._tomesh.setIconSize(QSize(size - 8, size - 8))
        self._tomesh.setFixedSize(size, size)
        self._stat.setIconSize(QSize(size - 8, size - 8))
        self._stat.setFixedSize(size, size)
        self._duplicate.setIconSize(QSize(size - 8, size - 8))
        self._duplicate.setFixedSize(size, size)
        self._union.setIconSize(QSize(size - 8, size - 8))
        self._union.setFixedSize(size, size)

    def getTabTrackingWidget(self):
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabTrackingWidget
        if isinstance(parent, TabTrackingWidget): return parent
        else: raise TypeError('parent type {} is not TabTrackingWidget.'.format(type(parent)))

    def hasTabTrackingWidget(self) -> bool:
        r = False
        parent = self.parent()
        from Sisyphe.widgets.tabToolsWidgets import TabTrackingWidget
        if isinstance(parent, TabTrackingWidget): r = True
        return r

    def setListROIAttributeWidget(self, widget):
        if isinstance(widget, ListROIAttributesWidget): self._listroiwidget = widget
        else: raise TypeError('parameter type {} is not ListROIAttributesWidget.'.format(type(widget)))

    def getListROIAttributeWidget(self):
        return self._listroiwidget

    def hasListROIAttributeWidget(self):
        return self._listroiwidget is not None

    def setListMeshAttributeWidget(self, widget):
        if isinstance(widget, ListMeshAttributesWidget): self._listmeshwidget = widget
        else: raise TypeError('parameter type {} is not ListMeshAttributesWidget.'.format(type(widget)))

    def getListMeshAttributeWidget(self):
        return self._listmeshwidget

    def hasListMeshAttributeWidget(self):
        return self._listmeshwidget is not None

    def setReferenceID(self, rid: str):
        if self._ID != '' and not self.isEmpty(): self.removeAll()
        self._ID = rid

    def getReferenceID(self) -> str:
        return self._ID

    def hasReferenceID(self) -> bool:
        return self._ID != ''

    def getCheckedBundle(self):
        bundles = list()
        for i in range(0, self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if widget.isChecked():
                bundles.append(widget.getBundle())
        return bundles

    def setNewButtonVisibility(self, v: bool):
        self._new.setVisible(v)

    def getNewButtonVisibility(self) -> bool:
        return self._new.isVisible()

    def newButtonVisibilityOn(self):
        self._new.setVisible(True)

    def newButtonVisibilityOff(self):
        self._new.setVisible(False)

    def addBundle(self,
                  sl: SisypheStreamlines,
                  wait: DialogWait | None = None):
        if self.isEnabled():
            if self.count() < self.getMaxCount():
                if self._ID == '': self._ID = sl.getReferenceID()
                if self._ID == sl.getReferenceID():
                    name = self._getNewName(sl.getName())
                    sl.setName(name)
                    widget = self._addItem(name)
                    widget.setStreamlines(sl, wait)
                    self._logger.info('Add Bundle {}'.format(sl.getFilename()))
                else: messageBox(self, 'Add streamlines', 'Invalid streamlines ID.')
            else:
                messageBox(self,
                           'Add bundle',
                           text='Maximum number of bundles reached.\n'
                                'Close a bundle to add a new one.',
                           icon=QMessageBox.Information)

    def duplicateBundle(self,
                        widget: ItemBundleAttributesWidget,
                        select: SisypheBundle | None,
                        wait: DialogWait | None = None):
        if self.isEnabled():
            if self.count() < self.getMaxCount():
                sl = widget.getStreamlines()
                # < Revision 21/02/2025
                # if select.getName() == '':
                #   name = self._getNewName(sl.getName())
                #   select.setName(name)
                if select is None:
                    select = SisypheBundle(sl.count())
                if select.getName() == '':
                    name = self._getNewName(sl.getName())
                    select.setName(name)
                # Revision 21/02/2025 >
                if wait is not None:
                    wait.setInformationText('Add {} bundle.'.format(select.getName()))
                widget = self._addItem(select.getName())
                widget.duplicateStreamlines(sl, select)
                self._logger.info('Duplicate Bundle {} to {}'.format(sl.getName(), select.getName()))
            else:
                messageBox(self,
                           'Duplicate bundle',
                           text='Maximum number of bundles reached.\n'
                                'Close a bundle to add a new one.',
                           icon=QMessageBox.Information)

    def unionBundle(self, widgets: list[ItemBundleAttributesWidget],
                    wait: DialogWait | None = None):
        if self.isEnabled():
            if self.count() < self.getMaxCount():
                sl = list()
                for i in range(len(widgets)):
                    sl.append(widgets[i].getStreamlines())
                widget = self._addItem(self._getNewName('union#1'))
                widget.unionStreamlines(sl, wait)
            else:
                messageBox(self,
                           'Bundles union',
                           text='Maximum number of bundles reached.\n'
                                'Close a bundle to add a new one.',
                           icon=QMessageBox.Information)

    @staticmethod
    def updateBundle(widget: ItemBundleAttributesWidget,
                     select: SisypheBundle,
                     wait: DialogWait | None = None):
        sl = widget.getStreamlines()
        if wait is not None:
            wait.setInformationText('Update {} bundle.'.format(sl.getName()))
        widget.updateStreamlines(select)

    def open(self):
        if self.isEnabled():
            if self.hasViewCollection():
                title = 'Open streamlines'
                if self.count() < self.getMaxCount():
                    filt = SisypheStreamlines.getFilterExt()
                    filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), filt)[0]
                    QApplication.processEvents()
                    if filenames:
                        n = len(filenames)
                        chdir(dirname(filenames[0]))
                        wait = DialogWait()
                        wait.setInformationText('Open streamlines...')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        QApplication.processEvents()
                        for filename in filenames:
                            if self.count() < self.getMaxCount():
                                sl = SisypheStreamlines()
                                bundle = basename(filename)
                                wait.setInformationText('Open {}...'.format(bundle))
                                wait.incCurrentProgressValue()
                                sl.load(filename)
                                n = sl.count()
                                # < Revision 20/02/2025
                                if n > self._MAXSTREAMLINES:
                                    wait.hide()
                                    r = messageBox(self,
                                                   'Add bundle',
                                                   text='More than {} streamlines in {} bundle.'
                                                        'Would you like to open a sub-sample?'.format(self._MAXSTREAMLINES, sl.getName()),
                                                   icon=QMessageBox.Question,
                                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                                   default=QMessageBox.No)
                                    wait.show()
                                    if r == QMessageBox.Yes:
                                        step = (n // self._MAXSTREAMLINES) + 1
                                        select = SisypheBundle(s=(0, n, step))
                                        name = '{} subsample'.format(sl.getName())
                                        select.setName(name)
                                        sl.getBundles().append(select)
                                        sl = sl.getSisypheStreamlinesFromBundle(name)
                                    else: sl = None
                                # Revision 20/02/2025 >
                                if sl is not None:
                                    wait.setInformationText('Add {} streamlines...'.format(bundle))
                                    self.addBundle(sl, wait)
                            else:
                                wait.close()
                                messageBox(self,
                                           title=title,
                                           text='Maximum number of bundles reached.\n'
                                                'Close a bundle to add a new one.',
                                           icon=QMessageBox.Information)
                                return
                        wait.close()
                else:
                    messageBox(self,
                               title=title,
                               text='Maximum number of bundles reached.\n'
                                    'Close a bundle to add a new one.',
                               icon=QMessageBox.Information)

    def remove(self):
        if self.hasViewCollection() and self.hasCollection():
            if not self.isEmpty():
                bundles = self.getCheckedBundle()
                n = len(bundles)
                if n > 0:
                    wait = DialogWait()
                    wait.setInformationText('Remove bundle(s)...')
                    wait.open()
                    QApplication.processEvents()
                    tracts = self._views.getTractCollection()
                    if tracts is not None:
                        for bundle in bundles:
                            wait.setInformationText('Remove {} bundle...'.format(bundle))
                            tracts.removeBundle(bundle)
                            self._logger.info('Remove Bundle {}'.format(bundle))
                            QApplication.processEvents()
                    super().remove()
                    if self.isEmpty():
                        if self.hasTabTrackingWidget():
                            if not self.getTabTrackingWidget().hasTractogram(): self.setReferenceID('')
                    wait.close()
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('Checked bundle(s) removed.')

    def removeItem(self, w):
        if self.hasViewCollection() and self.hasCollection():
            if not self.isEmpty():
                wait = DialogWait()
                wait.setInformationText('Remove {} bundle...'.format(w.getName()))
                wait.open()
                QApplication.processEvents()
                tracts = self._views.getTractCollection()
                if tracts is not None:
                    tracts.removeBundle(w.getName())
                    QApplication.processEvents()
                super().removeItem(w)
                if self.isEmpty():
                    if self.hasTabTrackingWidget():
                        if not self.getTabTrackingWidget().hasTractogram(): self.setReferenceID('')
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('{} bundle removed.'.format(w.getName()))

    def removeAll(self):
        if self.hasViewCollection() and self.hasCollection():
            if not self.isEmpty():
                wait = DialogWait()
                wait.setInformationText('Remove all bundles...')
                wait.open()
                QApplication.processEvents()
                tracts = self._views.getTractCollection()
                if tracts is not None:
                    tracts.removeAllBundles()
                    self._logger.info('Remove all bundles')
                super().removeAll()
                if self.hasTabTrackingWidget():
                    if not self.getTabTrackingWidget().hasTractogram(): self.setReferenceID('')
                wait.close()
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('All bundle(s) removed.')

    def saveAll(self):
        if self.hasCollection():
            if not self.isEmpty():
                n = self.count()
                wait = DialogWait()
                wait.setInformationText('Save all bundles...')
                wait.setProgressRange(0, n)
                wait.setProgressVisibility(n > 1)
                wait.open()
                QApplication.processEvents()
                for i in range(self.count()):
                    w = self.getWidget(i)
                    sl = w.getStreamlines()
                    path = sl.getDirname()
                    if path == '': path = getcwd()
                    filename = join(path, w.getName() + sl.getFileExt())
                    wait.setInformationText('Save {}'.format(basename(filename)))
                    wait.incCurrentProgressValue()
                    sl.save(filename)
                    self._logger.info('Save Bundle {}'.format(filename))
                    mainwindow = self._getMainWindow()
                    if mainwindow is not None:
                        mainwindow.setStatusBarMessage('{} bundle saved.'.format(basename(filename)))
                wait.close()

    def dissection(self):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    rois = None
                    refid = wchk[0].getStreamlines().getReferenceID()
                    if self.hasListROIAttributeWidget():
                        rois = self.getListROIAttributeWidget().getCollection()
                        if rois.count() > 0:
                            if rois.getReferenceID() == refid:
                                names = rois.getName()
                                self._roidialog.addROINames(names)
                    self._roidialog.setReferenceID(refid)
                    self._roidialog.setReferenceFOV(wchk[0].getStreamlines().getDWIFOV(decimals=1))
                    self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesROISelection]')
                    if self._roidialog.exec() == QDialog.Accepted:
                        wait = DialogWait()
                        wait.setInformationText('Bundle streamlines selection by ROI...')
                        wait.open()
                        QApplication.processEvents()
                        l = self._roidialog.getMinimalLength()
                        incl = self._roidialog.getInclusionROINames()
                        excl = self._roidialog.getExclusionROINames()
                        include = list()
                        rois2 = SisypheROICollection()
                        if len(incl) > 0:
                            for name in incl:
                                if rois is not None and name in rois:
                                    rois2.append(rois[name])
                                    include.append(True)
                                elif exists(name):
                                    roi = SisypheROI()
                                    roi.load(name)
                                    rois2.append(roi)
                                    include.append(True)
                        if len(excl) > 0:
                            for name in excl:
                                if rois is not None and name in rois:
                                    rois2.append(rois[name])
                                    include.append(False)
                                elif exists(name):
                                    roi = SisypheROI()
                                    roi.load(name)
                                    rois2.append(roi)
                                    include.append(False)
                        if len(rois2) > 0:
                            for w in wchk:
                                select = None
                                sl = w.getStreamlines()
                                # Minimal streamline length selection
                                if l > 0.0:
                                    wait.setInformationText('{} length filtering...'.format(sl.getName()))
                                    select = sl.bundleStreamlinesLongerThan(l=l)
                                # virtual dissection
                                wait.setInformationText('{} streamlines selection by ROI...'.format(sl.getName()))
                                select2 = sl.bundleRoiSelection(rois2, include, self._roidialog.getSelectionMode())
                                if select is not None:
                                    unselect = sl.getBundle(0) - select
                                    select = select2 - unselect
                                else: select = select2
                                if select is not None:
                                    if select.count() == 0:
                                        messageBox(self,
                                                   'Bundle streamlines selection by ROI',
                                                   'All streamlines removed.')
                                        continue
                                    elif select.count() == sl.count():
                                        messageBox(self,
                                                   'Bundle streamlines selection by ROI',
                                                   'No streamline removed.')
                                        continue
                                    else:
                                        if self._roidialog.getInPlace():
                                            wait.setInformationText('Update {}...'.format(sl.getName()))
                                            self.updateBundle(w, select, wait)
                                        else:
                                            if self.count() < self.getMaxCount():
                                                select.setName(self._getNewName(sl.getName()))
                                                wait.setInformationText('Add {}...'.format(sl.getName()))
                                                self.duplicateBundle(w, select, wait)
                                            else:
                                                wait.close()
                                                messageBox(self,
                                                           'Dissection',
                                                           text='Maximum number of bundles reached.\n'
                                                                'Close a bundle to add a new one.',
                                                           icon=QMessageBox.Information)
                                                return
                                        self._logger.info('Dissection Bundle {}'.format(sl.getName()))
                        else:
                            messageBox(self,
                                       'Bundle streamlines selection by ROI',
                                       'No ROI with valid ID (same as bundle ID.')
                        wait.close()
                else: messageBox(self, 'Bundle streamlines selection by ROI', 'No checked bundle.')

    def interactive(self, mode: int = 0):
        if self.isEnabled():
            if self.hasViewCollection():
                view = self.getViewCollection().getVolumeView()
                if view is not None:
                    p = view.getCursorWorldPosition()
                    radius = view.getSphereCursorRadius()
                    wchk = self.getChecked()
                    n = len(wchk)
                    if n > 0:
                        wait = DialogWait()
                        wait.setInformationText('Interactive streamlines selection...')
                        wait.setProgressVisibility(n > 1)
                        wait.setProgressRange(0, n)
                        wait.open()
                        QApplication.processEvents()
                        for w in wchk:
                            sl = w.getStreamlines()
                            # Exclude streamlines that cross cursor sphere
                            if mode == 0:
                                wait.setInformationText(
                                    'Exclude {} streamlines that cross cursor sphere...'.format(sl.getName()))
                                wait.incCurrentProgressValue()
                                select = sl.bundleIntersectSphere(p, radius, include=False)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are excluded.\n'
                                                    'All streamlines cross cursor sphere.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamline excluded.\n'
                                                    'No streamline crosses cursor sphere.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Exclude streamlines that cross cursor sphere Bundle {}'.format(sl.getName()))
                            # Include streamlines that cross cursor sphere
                            elif mode == 1:
                                wait.setInformationText(
                                    'Exclude {} streamlines that do not cross cursor sphere...'.format(sl.getName()))
                                select = sl.bundleIntersectSphere(p, radius, include=True)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamline included.\n'
                                                    'No streamline crosses cursor sphere.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are included.\n'
                                                    'All streamlines crosse cursor sphere.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Include streamlines that cross cursor sphere Bundle {}'.format(sl.getName()))
                            # Exclude streamlines that cross axial slice
                            elif mode == 2:
                                wait.setInformationText(
                                    'Exclude {} streamlines that cross axial slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [False, False, True], include=False)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are excluded.\n'
                                                    'All streamlines cross axial slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamline excluded.\n'
                                                    'No streamline crosses axial slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Exclude streamlines that cross axial slice Bundle {}'.format(sl.getName()))
                            # Include streamlines that cross axial slice
                            elif mode == 3:
                                wait.setInformationText(
                                    'Exclude {} streamlines that do not cross axial slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [False, False, True], include=True)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamlines included.\n'
                                                    'No streamline crosses axial slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are included.\n'
                                                    'All streamlines cross axial slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Include streamlines that cross axial slice Bundle {}'.format(sl.getName()))
                            # Exclude streamlines that cross coronal slice
                            elif mode == 4:
                                wait.setInformationText(
                                    'Exclude {} streamlines that cross coronal slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [False, True, False], include=False)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are excluded.\n'
                                                    'All streamlines cross coronal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamline excluded.\n'
                                                    'No streamline crosses coronal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Exclude streamlines that cross coronal slice Bundle {}'.format(sl.getName()))
                            # Include streamlines that cross coronal slice
                            elif mode == 5:
                                wait.setInformationText(
                                    'Exclude {} streamlines that do not cross coronal slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [False, True, False], include=True)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamlines included.\n'
                                                    'No streamline crosses coronal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are included.\n'
                                                    'All streamlines cross coronal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Include streamlines that cross coronal slice Bundle {}'.format(sl.getName()))
                            # Exclude streamlines that cross sagittal slice
                            elif mode == 6:
                                wait.setInformationText(
                                    'Exclude {} streamlines that cross sagittal slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [True, False, False], include=False)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are excluded.\n'
                                                    'All streamlines cross sagittal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamline excluded.\n'
                                                    'No streamline crosses sagittal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Exclude streamlines that cross sagittal slice Bundle {}'.format(sl.getName()))
                            # Include streamlines that cross sagittal slice
                            elif mode == 7:
                                wait.setInformationText(
                                    'Exclude {} streamlines that do not cross sagittal slice...'.format(sl.getName()))
                                select = sl.bundleIntersectPlane(p, [True, False, False], include=True)
                                if select.count() == 0:
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='No streamlines included.\n'
                                                    'No streamline crosses sagittal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                elif select.count() == sl.count():
                                    wait.close()
                                    messageBox(self,
                                               'Interactive streamlines selection',
                                               text='All streamlines are included.\n'
                                                    'All streamlines cross sagittal slice.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Include streamlines that cross sagittal slice Bundle {}'.format(sl.getName()))
                            else: raise ValueError('Invalid interactive mode.')
                            wait.setInformationText('Update {}...'.format(sl.getName()))
                            self.updateBundle(w, select, wait)
                        wait.close()
                    else: messageBox(self, 'Interactive streamlines selection', 'No bundle checked.')

    def filter(self):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesFiltering]')
                    if self._fltdialog.exec() == QDialog.Accepted:
                        wait = DialogWait()
                        wait.setInformationText('Bundle filtering...')
                        wait.setProgressVisibility(n > 1)
                        wait.setProgressRange(0, n)
                        wait.open()
                        QApplication.processEvents()
                        for w in wchk:
                            select = None
                            sl = w.getStreamlines()
                            wait.incCurrentProgressValue()
                            # Length filtering
                            if self._fltdialog.getMinimalStreamlinesLength() > 0.0:
                                wait.setInformationText('{} length filtering...'.format(sl.getName()))
                                select = sl.bundleStreamlinesLongerThan(l=self._fltdialog.getMinimalStreamlinesLength())
                            if self._fltdialog.getMaximumDistance() > 0.0:
                                wait.setInformationText('{} cluster confidence filtering...'.format(sl.getName()))
                                # < Revision 11/04/2025
                                select2, _ = sl.bundleClusterConfidenceFiltering(mdf=self._fltdialog.getMaximumDistance(),
                                                                                 subsample=self._fltdialog.getStreamlinesSampling(),
                                                                                 power=self._fltdialog.getPower(),
                                                                                 ccithreshold=self._fltdialog.getClusterConfidenceThreshold())
                                if select is not None:
                                    select1 = sl.getBundle(0) - select
                                    select = select2 - select1
                                else: select = select2
                                # Revision 11/04/2025 >
                            if select is not None:
                                if select.count() == 0:
                                    wait.hide()
                                    messageBox(self,
                                               'Cluster confidence filtering',
                                               'All streamlines removed.')
                                    wait.show()
                                    continue
                                elif select.count() == sl.count():
                                    wait.hide()
                                    messageBox(self,
                                               'Cluster confidence filtering',
                                               'No streamline removed.')
                                    wait.show()
                                    continue
                                else:
                                    if self._fltdialog.getInPlace():
                                        wait.setInformationText('Update {}...'.format(sl.getName()))
                                        self.updateBundle(w, select, wait)
                                    else:
                                        if self.count() < self.getMaxCount():
                                            select.setName(self._getNewName(sl.getName()))
                                            wait.setInformationText('Add {}...'.format(sl.getName()))
                                            self.duplicateBundle(w, select, wait)
                                        else:
                                            wait.close()
                                            messageBox(self,
                                                       'Filter',
                                                       text='Maximum number of bundles reached.\n'
                                                            'Close a bundle to add a new one.',
                                                       icon=QMessageBox.Information)
                                            return
                                    self._logger.info('Streamlines filtering Bundle {}'.format(sl.getName()))
                            else: continue
                        wait.close()
                else: messageBox(self,
                                 'Bundle filtering',
                                 'No checked bundle.')

    def cluster(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    wchk = self.getChecked()
                    n = len(wchk)
                    if n > 0:
                        self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesClustering]')
                        if self._cltdialog.exec() == QDialog.Accepted:
                            wait = DialogWait()
                            wait.setInformationText('Bundle clustering...')
                            wait.setProgressVisibility(n > 1)
                            wait.setProgressRange(0, n)
                            wait.open()
                            for w in wchk:
                                # Clustering
                                sl = w.getStreamlines()
                                wait.setInformationText('{} clustering...'.format(sl.getName()))
                                wait.incCurrentProgressValue()
                                bdls, centroids = sl.bundleClustering(metric=self._cltdialog.getMetric(),
                                                                      threshold=self._cltdialog.getMetricThreshold(),
                                                                      nbp=self._cltdialog.getStreamlinesSampling(),
                                                                      minclustersize=self._cltdialog.getMinimalClusterSize())
                                n = len(bdls)
                                if n > 0:
                                    if n == 1 and bdls[0].count() == sl.count():
                                        wait.hide()
                                        messageBox(self,
                                                   'Bundle clustering',
                                                   text='Clustering has failed, there is only one '
                                                        'cluster which is the same as the processed bundle.')
                                    else:
                                        for i in range(n):
                                            if self.count() < self.getMaxCount():
                                                self.duplicateBundle(w, bdls[i], wait)
                                            else:
                                                wait.close()
                                                messageBox(self,
                                                           'Bundle clustering',
                                                           text='Maximum number of bundles reached.\n'
                                                                'Close a bundle to add a new one.',
                                                           icon=QMessageBox.Information)
                                                return
                                        if self._cltdialog.getCentroidProcessing():
                                            for i in range(len(centroids)):
                                                if self.count() < self.getMaxCount():
                                                    wait.setInformationText('Add {}...'.format(centroids[i].getName()))
                                                    self.addBundle(centroids[i])
                                                else:
                                                    wait.close()
                                                    messageBox(self,
                                                               'Bundle clustering',
                                                               text='Maximum number of bundles reached.\n'
                                                                    'Close a bundle to add a new one.',
                                                               icon=QMessageBox.Information)
                                                    return
                                        self._logger.info('Streamlines clustering Bundle {}'.format(sl.getName()))
                                else:
                                    wait.hide()
                                    messageBox(self, 'Bundle clustering', 'No cluster.')
                                    wait.show()
                            wait.close()
                    else: messageBox(self, 'Bundle clustering', 'No checked bundle.')
                else:
                    messageBox(self,
                               'Bundle clustering',
                               text='Maximum number of bundles reached.\n'
                                    'Close a bundle to add a new one.',
                               icon=QMessageBox.Information)

    def centroid(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    wchk = self.getChecked()
                    n = len(wchk)
                    if n > 0:
                        self._cltdialog.setCentroidMode()
                        self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesClustering - Centroid]')
                        if self._cltdialog.exec() == QDialog.Accepted:
                            wait = DialogWait()
                            wait.setInformationText('Bundle centroid...')
                            wait.setProgressRange(0, n)
                            wait.setProgressVisibility(n > 1)
                            wait.open()
                            for w in wchk:
                                if self.count() < self.getMaxCount():
                                    slt = w.getStreamlines()
                                    wait.setInformationText('{} centroid...'.format(slt.getName()))
                                    wait.incCurrentProgressValue()
                                    sl = slt.streamlinesMajorCentroid(threshold=self._cltdialog.getMetricThreshold(),
                                                                      subsample=self._cltdialog.getStreamlinesSampling())
                                    if sl is not None and sl.count() > 0:
                                        wait.setInformationText('Add {}...'.format(sl.getName()))
                                        self.addBundle(sl)
                                else:
                                    wait.close()
                                    messageBox(self,
                                               'Bundle centroid(s)',
                                               text='Maximum number of bundles reached.\n'
                                                    'Close a bundle to add a new one.',
                                               icon=QMessageBox.Information)
                                    return
                                self._logger.info('Streamlines centroid Bundle {}'.format(slt.getName()))
                            wait.close()
                        self._cltdialog.setClusteringMode()
                    else: messageBox(self, 'Bundle centroid(s)', 'No checked bundle.')
                else:
                    messageBox(self,
                               'Bundle centroid(s)',
                               text='Maximum number of bundles reached.\n'
                                    'Close a bundle to add a new one.',
                               icon=QMessageBox.Information)

    def toMap(self):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    wait = DialogWait()
                    wait.setInformationText('Bundle density map processing...')
                    wait.setProgressRange(0, n)
                    wait.setCurrentProgressValue(0)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    for w in wchk:
                        wait.setInformationText('{} density map processing...'.format(w.getName()))
                        wait.incCurrentProgressValue()
                        sl = w.getStreamlines()
                        vol = sl.streamlinesToDensityMap()
                        filename = sl.getName() + vol.getFileExt()
                        wait.hide()
                        filename = QFileDialog.getSaveFileName(self,
                                                               'Save density map',
                                                               filename,
                                                               vol.getFilterExt())[0]
                        wait.show()
                        if filename:
                            wait.setInformationText('save {}...'.format(basename(filename)))
                            vol.saveAs(filename)
                            self._logger.info('Bundle {} to density map {}'.format(sl.getName(), filename))
                    wait.close()
                else: messageBox(self, 'Bundle density map processing', 'No bundle checked.')
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Bundle(s) converted to Map(s).')

    def toROI(self):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    wait = DialogWait()
                    wait.setInformationText('Bundle ROI processing...')
                    wait.setProgressRange(0, n)
                    wait.setCurrentProgressValue(0)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    for w in wchk:
                        wait.setInformationText('{} ROI processing...'.format(w.getName()))
                        wait.incCurrentProgressValue()
                        sl = w.getStreamlines()
                        roi = sl.bundleToRoi(self._treshroi.value(), perc=False)
                        if roi.isEmptyArray():
                            wait.hide()
                            messageBox(self,
                                       'Bundle ROI conversion',
                                       text='{} ROI is empty with a threshold of {} streamlines.'.format(
                                           w.getName(), self._treshroi.value()))
                            wait.show()
                            continue
                        else:
                            filename = sl.getName() + roi.getFileExt()
                            wait.hide()
                            filename = QFileDialog.getSaveFileName(self,
                                                                   'Save bundle ROI',
                                                                   filename,
                                                                   roi.getFilterExt())[0]
                            wait.show()
                            if filename:
                                wait.setInformationText('save {}...'.format(basename(filename)))
                                roi.saveAs(filename)
                                self._logger.info('Bundle {} to ROI {}'.format(sl.getName(), filename))
                            if self.hasListROIAttributeWidget():
                                widget = self.getListROIAttributeWidget()
                                if widget.isEnabled():
                                    wait.hide()
                                    r = messageBox(self,
                                                   'Bundle ROI conversion',
                                                   text='Do you want to open {}?'.format(basename(filename)),
                                                   icon=QMessageBox.Question,
                                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                                   default=QMessageBox.No)
                                    wait.show()
                                    if r == QMessageBox.Yes:
                                        self.getListROIAttributeWidget().add(roi)
                    wait.close()
                else: messageBox(self, 'Bundle ROI conversion', 'No bundle checked.')
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Bundle(s) converted to ROI(s).')

    def toMesh(self):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    wait = DialogWait()
                    wait.setInformationText('Bundle Mesh processing...')
                    wait.setProgressRange(0, n)
                    wait.setCurrentProgressValue(0)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    for w in wchk:
                        wait.setInformationText('{} Mesh processing...'.format(w.getName()))
                        wait.incCurrentProgressValue()
                        sl = w.getStreamlines()
                        mesh = sl.bundleToMesh(self._treshmesh.value(), perc=False)
                        if mesh.isEmpty():
                            wait.hide()
                            messageBox(self,
                                       'Bundle Mesh conversion',
                                       text='{} Mesh is empty with a threshold of {} streamlines.'.format(
                                           w.getName(), self._treshmesh.value()))
                            wait.show()
                            pass
                        else:
                            filename = sl.getName() + mesh.getFileExt()
                            wait.hide()
                            filename = QFileDialog.getSaveFileName(self,
                                                                   'Save bundle Mesh',
                                                                   filename,
                                                                   mesh.getFilterExt())[0]
                            wait.show()
                            if filename:
                                wait.setInformationText('save {}...'.format(basename(filename)))
                                mesh.saveAs(filename)
                                self._logger.info('Bundle {} to Mesh {}'.format(sl.getName(), filename))
                            if self.hasListMeshAttributeWidget():
                                widget = self.getListMeshAttributeWidget()
                                if widget.isEnabled():
                                    wait.hide()
                                    r = messageBox(self,
                                                   'Bundle Mesh conversion',
                                                   text='Do you want to open {}?'.format(basename(filename)),
                                                   icon=QMessageBox.Question,
                                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                                   default=QMessageBox.No)
                                    wait.show()
                                    if r == QMessageBox.Yes:
                                        self.getListMeshAttributeWidget().add(mesh)
                    wait.close()
                else: messageBox(self, 'Bundle Mesh conversion', 'No bundle checked.')
                mainwindow = self._getMainWindow()
                if mainwindow is not None:
                    mainwindow.setStatusBarMessage('Bundle(s) converted to Mesh(es).')

    def statistics(self, mode: int = 1):
        if self.isEnabled():
            if self.hasViewCollection():
                wchk = self.getChecked()
                n = len(wchk)
                if n > 0:
                    wait = DialogWait()
                    wait.setInformationText('Compute bundle statistics...')
                    wait.setProgressRange(0, n)
                    wait.setProgressVisibility(n > 1)
                    wait.open()
                    QApplication.processEvents()
                    self._statdialog.clear()
                    data = list()
                    labels = list()
                    for w in wchk:
                        slt = w.getStreamlines()
                        labels.append(slt.getName())
                        # Cluster confidence statistics
                        if mode == 0:
                            wait.addInformationText('Cluster confidence processing')
                            data.append(slt.bundleClusterConfidence())
                        # Length statistics
                        elif mode == 1:
                            wait.addInformationText('Length processing')
                            data.append(slt.bundleLengths())
                        # Mean curvature statistics
                        elif mode == 2:
                            wait.addInformationText('Mean curvature processing')
                            data.append(slt.bundleMeanCurvatures())
                        # Cosine distance between end vectors statistics
                        elif mode == 3:
                            wait.addInformationText('Cosine distance between end vectors')
                            data.append(slt.bundleCosineDistanceBetweenEndVectors())
                        # Euclidean distance between end vectors statistics
                        elif mode == 4:
                            wait.addInformationText('Euclidean distance between end points')
                            data.append(slt.bundleEuclideanDistanceBetweenEndPoints())
                        else: raise ValueError('Invalid statistics mode.')
                    if mode == 0:
                        title = 'Cluster confidence'
                        unit = ''
                    elif mode == 1:
                        title = 'Length'
                        unit = 'mm'
                    elif mode == 2:
                        title = 'Mean curvature'
                        unit = ''
                    elif mode == 3:
                        title = 'Cosine distance between end vectors'
                        unit = ''
                    elif mode == 4:
                        title = 'Euclidean distance between end points'
                        unit = ''
                    else: raise ValueError('Invalid statistics mode')
                    self._statdialog.newDescriptiveStatisticsTab(labels, data, title, scrshot=self._scrsht, units=unit)
                    for i in range(len(labels)):
                        self._statdialog.newHistogramTab(data[i], label='{} {}'.format(labels[i], title), scrshot=self._scrsht, units=unit)
                    wait.close()
                    self._logger.info('Dialog exec [gui.dialogGenericResults.DialogGenericResults - Streamlines {}]'.format(title))
                    self._statdialog.exec()
                else: messageBox(self, 'Bundle statistics', 'No bundle checked.')

    def duplicate(self, mode: int = 0):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    wchk = self.getChecked()
                    n = len(wchk)
                    if n > 0:
                        wait = DialogWait()
                        wait.setInformationText('Duplicate bundle...')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        for w in wchk:
                            if self.count() < self.getMaxCount():
                                wait.incCurrentProgressValue()
                                sl = w.getStreamlines()
                                if mode == 0:
                                    # self.duplicateBundle(w, sl.getBundle(0), wait)
                                    self.duplicateBundle(w, None, wait)
                                elif mode == 1:
                                    wait.setInformationText('Duplicate {} bundle with 0.5 mm step size...'.format(sl.getName()))
                                    sl = sl.changeStreamlinesStepSize(step=0.5, inplace=False)
                                    sl.setName(self._getNewName(sl.getName()))
                                    self.addBundle(sl)
                                elif mode == 2:
                                    wait.setInformationText('Duplicate {} bundle with 1.0 mm step size...'.format(sl.getName()))
                                    sl = sl.changeStreamlinesStepSize(step=1.0, inplace=False)
                                    sl.setName(self._getNewName(sl.getName()))
                                    self.addBundle(sl)
                                elif mode == 3:
                                    wait.setInformationText('Duplicate {} bundle with 2.0 mm step size...'.format(sl.getName()))
                                    sl = sl.changeStreamlinesStepSize(step=2.0, inplace=False)
                                    sl.setName(self._getNewName(sl.getName()))
                                    self.addBundle(sl)
                                elif mode == 4:
                                    wait.setInformationText('Duplicate {} bundle with compression...'.format(sl.getName()))
                                    sl = sl.compressStreamlines(inplace=False)
                                    sl.setName(self._getNewName(sl.getName()))
                                    self.addBundle(sl)
                                else: raise ValueError('Invalid duplicate mode')
                            else:
                                wait.close()
                                messageBox(self,
                                           'Duplicate bundle(s)',
                                           text='Maximum number of bundles reached.\n'
                                                'Close a bundle to add a new one.',
                                           icon=QMessageBox.Information)
                                return
                            self._logger.info('Duplicate Bundle {}'.format(sl.getName()))
                        wait.close()
                    else: messageBox(self, 'Duplicate bundle', 'No bundle checked.')
                else:
                    messageBox(self,
                               'Duplicate bundle(s)',
                               text='Maximum number of bundles reached.\n'
                                    'Close a bundle to add a new one.',
                               icon=QMessageBox.Information)

    def union(self):
        if self.isEnabled():
            if self.hasViewCollection():
                if self.count() < self.getMaxCount():
                    wchk = self.getChecked()
                    n = len(wchk)
                    if n > 1:
                        wait = DialogWait()
                        wait.setInformationText('Bundles union...')
                        wait.open()
                        self.unionBundle(wchk, wait)
                        wait.close()
                    else: messageBox(self,
                                     'Bundle union',
                                     text='At least two bundles must be checked.')
                else:
                    messageBox(self,
                               'Bundles union',
                               text='Maximum number of bundles reached.\n'
                                    'Close a bundle to add a new one.',
                               icon=QMessageBox.Information)

    # Qt event

    def dropEvent(self, event):
        if self.hasViewCollection():
            if event.mimeData().hasText():
                event.acceptProposedAction()
                files = event.mimeData().text().split('\n')
                title = 'Open streamlines'
                for file in files:
                    if file != '':
                        filename = file.replace('file://', '')
                        bundle, ext = splitext(filename)
                        if ext == SisypheStreamlines.getFileExt():
                            wait = DialogWait(info='Open {}...'.format(basename(filename)))
                            wait.open()
                            sl = SisypheStreamlines()
                            try:
                                sl.load(filename)
                                self.addBundle(sl)
                            except Exception as err:
                                messageBox(self, title, text='{}'.format(err))
                            wait.close()
                        mainwindow = self._getMainWindow()
                        if mainwindow is not None:
                            mainwindow.setStatusBarMessage('open {}.'.format(basename(filename)))
            else: event.ignore()

    # Method alias

    getBundle = ListAttributesWidget.getItem
