"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QPushButton

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition

"""
    Class hierarchy

        QDialog -> DialogVolumeAttributes
"""


class DialogVolumeAttributes(QDialog):
    """
        DialogVolumeAttributes class

        Description

            Dialog box to edit volume attributes.

        Inheritance

            QWidget -> QDialog -> DialogFontProperties

        Private attributes

            _volume     SisypheVolume

        Public methods

            setVolume(SisypheVolume)

            inherited QDialog methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, parent=None, vol=None):
        super().__init__(parent)

        self.setWindowTitle('Edit volume attributes')
        self.setFixedWidth(420)
        self.setFixedHeight(800)

        # Init Attributes widgets
        # Lastname
        self._lastname = QLineEdit()
        self._lastname.setFixedWidth(200)
        # Firstname
        self._firstname = QLineEdit()
        self._firstname.setFixedWidth(200)
        # Gender
        self._gender = QComboBox()
        self._gender.setFixedWidth(200)
        self._gender.setEditable(False)
        self._gender.addItem('Unknown')
        self._gender.addItem('Male')
        self._gender.addItem('Female')
        # Date of Birthday
        self._dob = QDateEdit()
        self._dob.setFixedWidth(200)
        self._dob.setCalendarPopup(True)
        # Modality
        self._modality = QComboBox()
        self._modality.setFixedWidth(200)
        self._modality.setEditable(False)
        items = SisypheAcquisition.getCodeToModalityDict().values()
        for item in items:
            self._modality.addItem(item)
        self._modality.currentIndexChanged.connect(self._setSequencesFromModality)
        # Sequence
        self._sequence = QComboBox()
        self._sequence.setFixedWidth(200)
        self._sequence.setEditable(True)
        self._setSequencesFromModality()
        self._sequence.currentIndexChanged.connect(self._setUnitFromSequence)
        # Unit
        self._unit = QComboBox()
        self._unit.setFixedWidth(200)
        self._unit.setEditable(True)
        for item in SisypheAcquisition.getUnitList():
            self._unit.addItem(item)
        self._unit.setCurrentIndex(0)
        # Frame
        self._frame = QComboBox()
        self._frame.setFixedWidth(200)
        items = SisypheAcquisition.getFrameList()
        for item in items:
            self._frame.addItem(item)
        # Date of scan
        self._dos = QDateEdit()
        self._dos.setFixedWidth(200)
        self._dos.setCalendarPopup(True)
        # Array ID
        self._aID = QLineEdit()
        self._aID.setFixedWidth(280)
        self._aID.setReadOnly(True)
        self._aID.setAlignment(Qt.AlignCenter)
        self._alID = QHBoxLayout()
        self._alID.addStretch()
        self._alID.addWidget(QLabel('Array ID'))
        self._alID.addWidget(self._aID)
        # ID
        self._ID = QLineEdit()
        self._ID.setFixedWidth(280)
        self._ID.setAlignment(Qt.AlignCenter)
        self._lID = QHBoxLayout()
        self._lID.addStretch()
        self._lID.addWidget(QLabel('Trfrm ID'))
        self._lID.addWidget(self._ID)
        # Size
        self._size = QLineEdit()
        self._size.setFixedWidth(200)
        self._size.setReadOnly(True)
        # Spacing
        self._spacingx = QDoubleSpinBox()
        self._spacingx.setFixedWidth(80)
        self._spacingx.setSingleStep(0.01)
        self._spacingx.setMinimum(0.1)
        self._spacingx.setMaximum(20.0)
        self._spacingx.setSuffix(' mm')
        self._spacingx.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._spacingx.setAlignment(Qt.AlignCenter)
        self._spacingy = QDoubleSpinBox()
        self._spacingy.setFixedWidth(80)
        self._spacingy.setSingleStep(0.01)
        self._spacingy.setMinimum(0.1)
        self._spacingy.setMaximum(20.0)
        self._spacingy.setSuffix(' mm')
        self._spacingy.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._spacingy.setAlignment(Qt.AlignCenter)
        self._spacingz = QDoubleSpinBox()
        self._spacingz.setFixedWidth(80)
        self._spacingz.setSingleStep(0.01)
        self._spacingz.setMinimum(0.1)
        self._spacingz.setMaximum(20.0)
        self._spacingz.setSuffix(' mm')
        self._spacingz.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._spacingz.setAlignment(Qt.AlignCenter)
        self._lspacing = QHBoxLayout()
        self._lspacing.setSpacing(0)
        self._lspacing.addWidget(self._spacingx)
        self._lspacing.addWidget(self._spacingy)
        self._lspacing.addWidget(self._spacingz)
        # Origin
        self._originx = QDoubleSpinBox()
        self._originx.setFixedWidth(80)
        self._originx.setSingleStep(0.1)
        self._originx.setMinimum(0.0)
        self._originx.setMaximum(512.0)
        self._originx.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._originx.setSuffix(' mm')
        self._originx.setAlignment(Qt.AlignCenter)
        self._originy = QDoubleSpinBox()
        self._originy.setFixedWidth(80)
        self._originy.setSingleStep(0.1)
        self._originy.setMinimum(0.0)
        self._originy.setMaximum(512.0)
        self._originy.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._originy.setSuffix(' mm')
        self._originy.setAlignment(Qt.AlignCenter)
        self._originz = QDoubleSpinBox()
        self._originz.setFixedWidth(80)
        self._originz.setSingleStep(0.1)
        self._originz.setMinimum(0.0)
        self._originz.setMaximum(512.0)
        self._originz.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._originz.setSuffix(' mm')
        self._originz.setAlignment(Qt.AlignCenter)
        self._lorigin = QHBoxLayout()
        self._lorigin.setSpacing(0)
        self._lorigin.addWidget(self._originx)
        self._lorigin.addWidget(self._originy)
        self._lorigin.addWidget(self._originz)
        # Datatype
        self._datatype = QLineEdit()
        self._datatype.setFixedWidth(200)
        self._datatype.setReadOnly(True)
        # Orientation
        self._orient = QComboBox()
        self._orient.setFixedWidth(200)
        self._orient.addItem('Unknown')
        self._orient.addItem('Axial')
        self._orient.addItem('Coronal')
        self._orient.addItem('Sagittal')
        # Slope
        self._slope = QDoubleSpinBox()
        self._slope.setFixedWidth(200)
        self._slope.setSingleStep(0.1)
        self._slope.setMinimum(-1e6)
        self._slope.setMaximum(1e6)
        # Intercept
        self._inter = QDoubleSpinBox()
        self._inter.setFixedWidth(200)
        self._inter.setSingleStep(0.1)
        self._inter.setMinimum(-1e6)
        self._inter.setMaximum(1e6)
        # Directions
        self._dir1 = QDoubleSpinBox()
        self._dir1.setFixedWidth(65)
        self._dir1.setSingleStep(0.1)
        self._dir1.setMinimum(-1.0)
        self._dir1.setMaximum(1.0)
        self._dir1.setAlignment(Qt.AlignCenter)
        self._dir2 = QDoubleSpinBox()
        self._dir2.setFixedWidth(65)
        self._dir2.setSingleStep(0.1)
        self._dir2.setMinimum(-1.0)
        self._dir2.setMaximum(1.0)
        self._dir2.setAlignment(Qt.AlignCenter)
        self._dir3 = QDoubleSpinBox()
        self._dir3.setFixedWidth(65)
        self._dir3.setSingleStep(0.1)
        self._dir3.setMinimum(-1.0)
        self._dir3.setMaximum(1.0)
        self._dir3.setAlignment(Qt.AlignCenter)
        self._dir4 = QDoubleSpinBox()
        self._dir4.setFixedWidth(65)
        self._dir4.setSingleStep(0.1)
        self._dir4.setMinimum(-1.0)
        self._dir4.setMaximum(1.0)
        self._dir4.setAlignment(Qt.AlignCenter)
        self._dir5 = QDoubleSpinBox()
        self._dir5.setFixedWidth(65)
        self._dir5.setSingleStep(0.1)
        self._dir5.setMinimum(-1.0)
        self._dir5.setMaximum(1.0)
        self._dir5.setAlignment(Qt.AlignCenter)
        self._dir6 = QDoubleSpinBox()
        self._dir6.setFixedWidth(65)
        self._dir6.setSingleStep(0.1)
        self._dir6.setMinimum(-1.0)
        self._dir6.setMaximum(1.0)
        self._dir6.setAlignment(Qt.AlignCenter)
        self._dir7 = QDoubleSpinBox()
        self._dir7.setFixedWidth(65)
        self._dir7.setSingleStep(0.1)
        self._dir7.setMinimum(-1.0)
        self._dir7.setMaximum(1.0)
        self._dir7.setAlignment(Qt.AlignCenter)
        self._dir8 = QDoubleSpinBox()
        self._dir8.setFixedWidth(65)
        self._dir8.setSingleStep(0.1)
        self._dir8.setMinimum(-1.0)
        self._dir8.setMaximum(1.0)
        self._dir8.setAlignment(Qt.AlignCenter)
        self._dir9 = QDoubleSpinBox()
        self._dir9.setFixedWidth(65)
        self._dir9.setSingleStep(0.1)
        self._dir9.setMinimum(-1.0)
        self._dir9.setMaximum(1.0)
        self._dir9.setAlignment(Qt.AlignCenter)
        self._ldir1 = QHBoxLayout()
        self._ldir1.setSpacing(0)
        self._ldir1.addWidget(self._dir1)
        self._ldir1.addWidget(self._dir2)
        self._ldir1.addWidget(self._dir3)
        self._ldir2 = QHBoxLayout()
        self._ldir2.setSpacing(0)
        self._ldir2.addWidget(self._dir4)
        self._ldir2.addWidget(self._dir5)
        self._ldir2.addWidget(self._dir6)
        self._ldir3 = QHBoxLayout()
        self._ldir3.setSpacing(0)
        self._ldir3.addWidget(self._dir7)
        self._ldir3.addWidget(self._dir8)
        self._ldir3.addWidget(self._dir9)
        # Memory
        self._memory = QLineEdit()
        self._memory.setFixedWidth(200)
        self._memory.setReadOnly(True)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init QGripLayout

        layout = QGridLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        # Identity fields
        layout.addWidget(QLabel('Identity'), 0, 0, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Lastname'), 1, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._lastname, 1, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Firstname'), 2, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._firstname, 2, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Gender'), 3, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._gender, 3, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Date of birth'), 4, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._dob, 4, 1, alignment=Qt.AlignLeft)
        # Acquisition fields
        layout.addWidget(QLabel('Acquisition'), 5, 0, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Modality'), 6, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._modality, 6, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Sequence'), 7, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._sequence, 7, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Unit'), 8, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._unit, 8, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Frame'), 9, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._frame, 9, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Date of scan'), 10, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._dos, 10, 1, alignment=Qt.AlignLeft)
        # Image fields
        layout.addWidget(QLabel('Image'), 11, 0, alignment=Qt.AlignLeft)
        layout.addLayout(self._alID, 12, 0, 1, 2, alignment=Qt.AlignLeft)
        layout.addLayout(self._lID, 13, 0, 1, 2, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Size'), 14, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._size, 14, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Spacing'), 15, 0, alignment=Qt.AlignRight)
        layout.addLayout(self._lspacing, 15, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Origin'), 16, 0, alignment=Qt.AlignRight)
        layout.addLayout(self._lorigin, 16, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Data type'), 17, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._datatype, 17, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Slope'), 18, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._slope, 18, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Intercept'), 19, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._inter, 19, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Orientation'), 20, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._orient, 20, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('First vector direction'), 21, 0, alignment=Qt.AlignRight)
        layout.addLayout(self._ldir1, 21, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Second vector direction'), 22, 0, alignment=Qt.AlignRight)
        layout.addLayout(self._ldir2, 22, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Third vector direction'), 23, 0, alignment=Qt.AlignRight)
        layout.addLayout(self._ldir3, 23, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel('Memory size'), 24, 0, alignment=Qt.AlignRight)
        layout.addWidget(self._memory, 24, 1, alignment=Qt.AlignLeft)
        self._layout.addLayout(layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        reset = QPushButton('Reset')
        reset.setFixedWidth(100)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.addWidget(reset)
        self._layout.addLayout(layout)
        ok.clicked.connect(self._accept)
        cancel.clicked.connect(self.reject)
        reset.clicked.connect(self._initFields)

        if isinstance(vol, SisypheVolume): self.setVolume(vol)
        else: self._vol = None

    # Private methods

    def _initFields(self):
        if isinstance(self._vol, SisypheVolume):
            self._lastname.setText(self._vol.getIdentity().getLastname())
            self._firstname.setText(self._vol.getIdentity().getFirstname())
            self._gender.setCurrentIndex(self._vol.getIdentity().getGender(string=False))
            self._dob.setDate(self._vol.getIdentity().getDateOfBirthday(string=False))
            self._modality.setCurrentIndex(self._vol.getAcquisition().getModality(string=False))
            self._sequence.setCurrentText(self._vol.getAcquisition().getSequence())
            self._unit.setCurrentText(self._vol.getAcquisition().getUnit())
            self._frame.setCurrentIndex(self._vol.getAcquisition().getFrame())
            self._dos.setDate(self._vol.getAcquisition().getDateOfScan(string=False))
            self._ID.setText(self._vol.getID())
            self._aID.setText(self._vol.getArrayID())
            buff = self._vol.getSize()
            self._size.setText('{} {} {}'.format(buff[0], buff[1], buff[2]))
            buff = self._vol.getSpacing()
            self._spacingx.setValue(buff[0])
            self._spacingy.setValue(buff[1])
            self._spacingz.setValue(buff[2])
            buff = self._vol.getOrigin()
            self._originx.setValue(buff[0])
            self._originy.setValue(buff[1])
            self._originz.setValue(buff[2])
            self._datatype.setText(self._vol.getDatatype())
            self._orient.setCurrentIndex(self._vol.getOrientation())
            self._slope.setValue(self._vol.getSlope())
            self._inter.setValue(self._vol.getIntercept())
            buff = self._vol.getDirections()
            self._dir1.setValue(buff[0])
            self._dir2.setValue(buff[1])
            self._dir3.setValue(buff[2])
            self._dir4.setValue(buff[3])
            self._dir5.setValue(buff[4])
            self._dir6.setValue(buff[5])
            self._dir7.setValue(buff[6])
            self._dir8.setValue(buff[7])
            self._dir9.setValue(buff[8])
            self._memory.setText('{0:.2f} MB'.format(self._vol.getMemorySize('MB')))

    def _accept(self):
        self._vol.setID(self._ID.text())
        self._vol.getIdentity().setLastname(self._lastname.text())
        self._vol.getIdentity().setFirstname(self._firstname.text())
        self._vol.getIdentity().setGender(self._gender.currentIndex())
        self._vol.getIdentity().setDateOfBirthday(self._dob.date().toString(Qt.ISODate))
        self._vol.getAcquisition().setModality(self._modality.currentIndex())
        self._vol.getAcquisition().setSequence(self._sequence.currentText())
        self._vol.getAcquisition().setUnit(self._unit.currentText())
        self._vol.getAcquisition().setFrame(self._frame.currentIndex())
        self._vol.getAcquisition().setDateOfScan(self._dos.date().toString(Qt.ISODate))
        self._vol.setSpacing(self._spacingx.value(), self._spacingy.value(), self._spacingz.value())
        self._vol.setOrigin((self._originx.value(), self._originy.value(), self._originz.value()))
        self._vol.setOrientation(self._orient.currentIndex())
        self._vol.setSlope(self._slope.value())
        self._vol.setIntercept(self._inter.value())
        d = (self._dir1.value(), self._dir2.value(), self._dir3.value(),
             self._dir4.value(), self._dir5.value(), self._dir6.value(),
             self._dir7.value(), self._dir8.value(), self._dir9.value())
        self._vol.setDirections(d)
        self._vol.save()
        self.accept()

    def _setSequencesFromModality(self):
        self._sequence.clear()
        # OT
        if self._modality.currentIndex() == 0:
            items = SisypheAcquisition.getOTSequences()
        # MR
        elif self._modality.currentIndex() == 1:
            items = SisypheAcquisition.getMRSequences()
        # CT
        elif self._modality.currentIndex() == 2:
            items = SisypheAcquisition.getCTSequences()
        # PT
        elif self._modality.currentIndex() == 3:
            items = SisypheAcquisition.getPTSequences()
        # NM
        elif self._modality.currentIndex() == 4:
            items = SisypheAcquisition.getNMSequences()
        # TP
        elif self._modality.currentIndex() == 6:
            items = list(SisypheAcquisition.getOTSequences())
            items += list(SisypheAcquisition.getMRSequences())
            items += list(SisypheAcquisition.getCTSequences())
            items += list(SisypheAcquisition.getPTSequences())
            items += list(SisypheAcquisition.getNMSequences())
        else:
            items = SisypheAcquisition.getOTSequences()
        for item in items:
            self._sequence.addItem(item)
        self._setUnitFromSequence()

    def _setUnitFromSequence(self):
        if self._modality.currentText() == 'CT': self._unit.setCurrentText(SisypheAcquisition.HU)
        elif self._modality.currentText() == 'OT':
            if self._sequence.currentText() == SisypheAcquisition.TMAP:
                self._unit.setCurrentText(SisypheAcquisition.TVAL)
            elif self._sequence.currentText() == SisypheAcquisition.ZMAP:
                self._unit.setCurrentText(SisypheAcquisition.ZSCORE)
            elif self._sequence.currentText() == SisypheAcquisition.ADC:
                self._unit.setCurrentText(SisypheAcquisition.MM2S)
            elif self._sequence.currentText() == SisypheAcquisition.DOSE:
                self._unit.setCurrentText(SisypheAcquisition.GY)
            elif self._sequence.currentText() == SisypheAcquisition.THICK:
                self._unit.setCurrentText(SisypheAcquisition.MM)
            elif self._sequence.currentText() in (SisypheAcquisition.MTT, SisypheAcquisition.TTP):
                self._unit.setCurrentText(SisypheAcquisition.SEC)
            elif self._sequence.currentText() in (SisypheAcquisition.GM,
                                                  SisypheAcquisition.WM,
                                                  SisypheAcquisition.CSF,
                                                  SisypheAcquisition.FA):
                self._unit.setCurrentText(SisypheAcquisition.PERC)
        elif self._modality.currentText() in ('NM', 'PT'): self._unit.setCurrentText(SisypheAcquisition.COUNT)
        else: self._unit.setCurrentText(SisypheAcquisition.NOUNIT)

    # Public method

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            self._vol = vol
            self._initFields()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    filename = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/tests/IMAGES/img.xvol'
    img = SisypheVolume()
    img.load(filename)
    main = DialogVolumeAttributes(vol=img)
    main.activateWindow()
    main.show()
    print(main.width(), main.height())
    app.exec_()
    exit()
