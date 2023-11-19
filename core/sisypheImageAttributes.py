"""
    External packages/modules

        Name            Link                                                        Usage

        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import splitext

from math import sqrt
from math import atan2
from math import degrees

from datetime import date
from datetime import datetime

from xml.dom import minidom

from copy import deepcopy

from vtk import vtkLookupTable

import Sisyphe.core as sc
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheTransform import SisypheTransform

__all__ = ['SisypheIdentity',
           'SisypheAcquisition',
           'SisypheDisplay',
           'SisypheACPC']

"""
    Classes hierarchy
    
        object -> SisypheIdentity
                  SisypheAcquisition
                  SisypheDisplay
                  SisypheACPC  
"""

listFloat3 = list[float, float, float]
tupleFloat3 = tuple[float, float, float]


class SisypheIdentity(object):
    """
        SisypheIdentity class

            Class to manage patient identity attributes.

        Inheritance

            object -> SisypheIdentity

        Private attributes

            _lastname           str
            _firstname          str
            _gender             int
            _dateofbirthday     date
            _parent             parent instance

        Class method

            getFileExt() -> str
            getFilterExt() -> str
            getDefaultDate() -> datetime.date

        Public methods

            __init__(firstname: str = '',
                     lastname: str = '',
                     gender: int = 0,
                     dob: date,
                     parent: Sisyphe.sisypheVolume.SisypheVolume | None = None)
            __repr__() -> str
            __str__() -> str
            __contains__(buff: str | int | date) -> bool
            __lt__(other: SisypheIdentity) -> bool
            __le__(other: SisypheIdentity) -> bool
            __eq__(other: SisypheIdentity) -> bool
            __ne__(other: SisypheIdentity) -> bool
            __gt__(other: SisypheIdentity) -> bool
            __ge__(other: SisypheIdentity) -> bool
            hasParent() -> bool
            setParent(parent: Sisyphe.sisypheVolume.SisypheVolume)
            getParent() -> Sisyphe.sisypheVolume.SisypheVolume
            getFirstname() -> str
            setFirstname(buff: str)
            getLastname() -> str
            getLastname(buff: str)
            getDateOfBirthday(string: bool = True, f: str = '%Y-%m-%d') -> str | datetime.date
            setDateOfBirthday(buff: str | datetime.date | None = None, f: str = '%Y-%m-%d')
            getGender(string: bool = True) -> int | str
            setGender(v: int | str)
            setGenderToMale()
            setGenderToFemale()
            setGenderToUnknown()
            anonymize()
            isAnonymized() -> bool
            isEqual(buff: SisypheIdentity) -> bool
            isNotEqual(buff: SisypheIdentity) -> bool
            copyFrom(buff: SisypheIdentity | Sisyphe.sisypheVolume.SisypheVolume)
            copy() -> SisypheIdentity
            getAge() -> int
            getAgeOn(d: date) -> int
            isYounger(buff: SisypheIdentity | date | int | float) -> bool
            isOlder(buff: SisypheIdentity | date | int | float) -> bool
            isMale() -> bool
            isFemale() -> bool
            saveToTxt(filename: str)
            loadFromTxt(filename: str)
            parseXML(minidom.Document)
            createXML(doc: minidom.Document, currentnode: minidom.Element)
            saveToXML(filename: str)
            loadFromXML(filename: str)

        Creation: 17/01/2020
        Revision:

            29/08/2023  type hinting
            17/11/2023  docstrings
    """
    __slots__ = ['_firstname', '_lastname', '_gender', '_dateofbirthday', '_parent']

    # Class constants

    _DEFAULTDATE = date(2000, 1, 1)
    _GENDERTOCODE = {'Unknown': 0, 'Male': 1, 'Female': 2}
    _CODETOGENDER = {0: 'Unknown', 1: 'Male', 2: 'Female'}
    _FILEEXT = '.xidentity'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
            Get SisypheIdentity file extension.

            return  str, '.xidentity'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
            Get SisypheIdentity filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

            return  str, 'PySisyphe Identity (*.xidentity)'
        """
        return 'PySisyphe Identity (*{})'.format(cls._FILEEXT)

    @classmethod
    def getDefaultDate(cls) -> date:
        """
            Get default date 01/01/2000

            return  datetime.date, datetime.date(1, 1, 2000)
        """
        return cls._DEFAULTDATE

    # Special methods

    def __init__(self,
                 firstname: str = '',
                 lastname: str = '',
                 gender: int = 0,
                 dob: date = _DEFAULTDATE,
                 parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        """
            SisypheIdentity instance constructor

            Parameters

                firstname   str, patient firstname
                lastname    str, patient lastname
                gender      int, patient gender code (0 unknown, 1 male, 2 female)
                dob         datetime.date, patient birthdate
                parent      Sisyphe.sisypheVolume.SisypheVolume | None
        """
        self._firstname = firstname.title()
        self._lastname = lastname.title()
        self._gender = gender
        self._dateofbirthday = dob
        self._parent = parent

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheIdentity instance to str
         """
        return 'Identity:\n' \
               '\tLastname: {}\n' \
               '\tFirstname: {}\n' \
               '\tDate of birthday: {}\n' \
               '\tGender: {}\n'.format(self._lastname, self._firstname,
                                       self.getDateOfBirthday(True), self.getGender(True))

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheIdentity instance representation
        """
        return '{} class instance at <{}>\n'.format(self.__class__.__name__,
                                                    str(id(self)))

    def __contains__(self, buff: str | int | date) -> bool:
        """
            Special overloaded container method called by the built-in 'in' python operator.
            Checks whether buff parameter is in SisypheIdentity instance.

            Parameter

                key     str,    firstname, lastname
                        | int,  gender
                        | date, birthdate

            return  bool, True if buff parameter is in SisypheIdentity instance
        """
        return self._firstname == buff or self._lastname == buff or \
               self._gender == buff or self._dateofbirthday == buff

    # Relational operators

    def __lt__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator <.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self < other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        if isinstance(other, SisypheIdentity):
            strself = self._lastname + self._firstname + str(self._dateofbirthday) + self.getGender(True)
            strbuff = other._lastname + other._firstname + str(other._dateofbirthday) + other.getGender(True)
            return strself < strbuff
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    def __le__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator <=.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self <= other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        if isinstance(other, SisypheIdentity):
            strself = self._lastname + self._firstname + str(self._dateofbirthday) + self.getGender(True)
            strbuff = other._lastname + other._firstname + str(other._dateofbirthday) + other.getGender(True)
            return strself <= strbuff
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    def __eq__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator ==.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self == other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        return self.isEqual(other)

    def __ne__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator !=.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self != other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        return not self.isEqual(other)

    def __gt__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator >.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self > other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        if isinstance(other, SisypheIdentity):
            strself = self._lastname + self._firstname + str(self._dateofbirthday) + self.getGender(True)
            strbuff = other._lastname + other._firstname + str(other._dateofbirthday) + other.getGender(True)
            return strself > strbuff
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    def __ge__(self, other: SisypheIdentity) -> bool:
        """
            Special overloaded relational operator >=.
            Attribute comparison order: lastname, firstname, birthdate, gender
            self >=other -> bool

            Parameter

                other   SisypheIdentity

            return  bool
        """
        if isinstance(other, SisypheIdentity):
            strself = self._lastname + self._firstname + str(self._dateofbirthday) + self.getGender(True)
            strbuff = other._lastname + other._firstname + str(other._dateofbirthday) + other.getGender(True)
            return strself >= strbuff
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    # Public methods

    def hasParent(self) -> bool:
        """
            Check whether current SisypheIdentity instance has a parent,
            i.e. parent attribute is not None.

            return  bool, True if current SisypheIdentity is defined (not None)
        """
        return self._parent is not None

    def setParent(self, parent: sc.sisypheVolume.SisypheVolume) -> None:
        """
            Set parent of the current SisypheIdentity instance.

            Parameter

                parent  Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(parent, sc.sisypheVolume.SisypheVolume): self._parent = parent
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(parent)))

    def getParent(self) -> sc.sisypheVolume.SisypheVolume:
        """
            Get parent of the current SisypheIdentity instance.

            return  Sisyphe.sisypheVolume.SisypheVolume
        """
        return self._parent

    def getFirstname(self) -> str:
        """
            Get firstname attribute of the current SisypheIdentity instance.

            return  str, patient firstname
        """
        return self._firstname

    def setFirstname(self, buff: str) -> None:
        """
            Set firstname attribute of the current SisypheIdentity instance.

            parameter

                buff    str, patient firstname
        """
        self._firstname = buff.title()

    def getLastname(self) -> str:
        """
            Get lastname attribute of the current SisypheIdentity instance.

            return  str, patient lastname
        """
        return self._lastname

    def setLastname(self, buff: str) -> None:
        """
            Set lastname attribute of the current SisypheIdentity instance.

            parameter

                buff    str, patient lastname
        """
        self._lastname = buff.title()

    def getDateOfBirthday(self, string: bool = True, f: str = '%Y-%m-%d') -> str | date:
        """
            Get birthdate attribute of the current SisypheIdentity instance.

            parameters

                string  bool, if True return patient birthdate as str
                              if False return patient birthdate as datetime.date
                f       str, format used to convert date to str (default '%Y-%m-%d')

            return  str,                patient birthdate as str
                    | datetime.date,    patient birthdate as datetime.date
        """
        if string: return self._dateofbirthday.strftime(f)
        else: return self._dateofbirthday

    def setDateOfBirthday(self, buff: str | date | None = None, f: str = '%Y-%m-%d') -> None:
        """
            Set birthdate attribute of the current SisypheIdentity instance.

            parameters

                buff  str,                patient birthdate as str
                      | datetime.date,    patient birthdate as datetime.date
                f     str, format used to convert date to str (default '%Y-%m-%d')
        """
        if isinstance(buff, str): self._dateofbirthday = datetime.strptime(buff, f).date()
        elif isinstance(buff, date): self._dateofbirthday = buff
        else: self._dateofbirthday = SisypheIdentity._DEFAULTDATE

    def getGender(self, string: bool = True) -> int | str:
        """
            Get gender attribute of the current SisypheIdentity instance.

            parameter

                string  bool, if True return gender as str ('Unknown', 'Male', 'Female')
                              if False return gender as int code (0 Unknown, 1 Male, 2 Female)

            return  str,    patient gender ('Unknown', 'Male', 'Female')
                    | int,  patient gender code (0 Unknown, 1 Male, 2 Female)
        """
        if string: return SisypheIdentity._CODETOGENDER[self._gender]
        else: return self._gender

    def setGender(self, v: int | str) -> None:
        """
            Set gender attribute of the current SisypheIdentity instance.

            parameter

                v  str,    patient gender str ('Unknown', 'Male', 'Female')
                   | int,  patient gender code (0 Unknown, 1 Male, 2 Female)
        """
        if isinstance(v, str):
            if v in self._GENDERTOCODE:
                self._gender = self._GENDERTOCODE[v]
            else: raise ValueError('parameter value {} is not a correct gender'.format(v))
        elif isinstance(v, int):
            if 0 <= v < 3:
                self._gender = v
            else: raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else: raise TypeError('parameter type {} is not str or int.'.format(type(v)))

    def setGenderToMale(self) -> None:
        """
            Set gender attribute of the current SisypheIdentity instance to male.
        """
        self._gender = self._GENDERTOCODE['Male']

    def setGenderToFemale(self) -> None:
        """
            Set gender attribute of the current SisypheIdentity instance to female.
        """
        self._gender = self._GENDERTOCODE['Female']

    def setGenderToUnknown(self) -> None:
        """
            Set gender attribute of the current SisypheIdentity instance to unknown.
        """
        self._gender = self._GENDERTOCODE['Unknown']

    def anonymize(self) -> None:
        """
            Anonymize identity attributes of the current SisypheIdentity instance.
            Set lastname and firstname to empty str ('')
            Set gender code to 0
            Set birthdate to default date i.e. datetime.date(1, 1, 2000)
        """
        self._firstname = ''
        self._lastname = ''
        self._gender = 0
        self._dateofbirthday = SisypheIdentity._DEFAULTDATE

    def isAnonymized(self) -> bool:
        """
            Check whether identity attributes of the
            current SisypheIdentity instance are anonymized.

            return  bool, True if identity attributes are anonymized
        """
        return self._firstname == '' and self._lastname == '' and \
               self._gender == 0 and self._dateofbirthday == SisypheIdentity._DEFAULTDATE

    def isEqual(self, buff: SisypheIdentity) -> bool:
        """
            Check that the attributes of the SisypheIdentity parameter are equal
            to those of the current SisypheIdentity instance.
            Attribute comparison order: lastname, firstname, birthdate, gender

            Parameter

                buff    SisypheIdentity

            return  bool
        """
        if isinstance(buff, SisypheIdentity):
            return self._firstname == buff._firstname and self._lastname == buff._lastname and \
                   self._gender == buff._gender and self._dateofbirthday == buff._dateofbirthday
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    def isNotEqual(self, buff: SisypheIdentity) -> bool:
        """
            Check that the attributes of the SisypheIdentity parameter are not equal
            to those of the current SisypheIdentity instance.
            Attribute comparison order: lastname, firstname, birthdate, gender

            Parameter

                buff    SisypheIdentity

            return  bool
        """
        return not self.isEqual(buff)

    def copyFrom(self, buff: SisypheIdentity | sc.sisypheVolume.SisypheVolume) -> None:
        """
            Copy attributes of the identity parameter to
            the current SisypheIdentity instance (deep copy).

            Parameter

                buff    SisypheIdentity | Sisyphe.sisypheVolume.SisypheVolume
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(buff, SisypheVolume):
            buff = buff.identity
        if isinstance(buff, SisypheIdentity):
            self._firstname = buff._firstname
            self._lastname = buff._lastname
            self._gender = buff._gender
            self._dateofbirthday = buff._dateofbirthday
        else: raise TypeError('parameter type {} is not {} or SisypheVolume.'.format(type(buff), self.__class__.__name__))

    def copy(self) -> SisypheIdentity:
        """
            Copy the current SisypheIdentity instance (deep copy).

            return   SisypheIdentity
        """
        return deepcopy(self)

    def getAge(self) -> int:
        """
            Get age as of today's date

            return  int, patient age
        """
        delta = date.today() - self._dateofbirthday
        return int(delta.days / 365)

    def getAgeOn(self, d: date) -> int:
        """
            Get age on a given date.

            Parameter

                d   datetime.date

            return  int, patient age
        """
        delta = d - self._dateofbirthday
        return int(delta.days / 365)

    def isYounger(self, buff: SisypheIdentity | date | int | float) -> bool:
        """
            Check whether current SisypheIdentity instance
            age calculated from birthdate attribute is younger
            than age calculated from parameter.

            Parameter

                buff    SisypheIdentity
                        | datetime.date, birthdate
                        | int, age in years
                        | float, age in years

            return  bool, True if younger
        """
        if isinstance(buff, SisypheIdentity): return self._dateofbirthday > buff._dateofbirthday
        elif isinstance(buff, date): return self._dateofbirthday > buff
        elif isinstance(buff, (int, float)): return self.getAge() < buff
        else: raise TypeError('parameter functype is not {}, date, int or float.'.format(self.__class__.__name__))

    def isOlder(self, buff: SisypheIdentity | date | int | float) -> bool:
        """
            Check whether current SisypheIdentity instance
            age calculated from birthdate attribute is older
            than age calculated from parameter.

            Parameter

                buff    SisypheIdentity
                        | datetime.date, birthdate
                        | int, age in years
                        | float, age in years

            return  bool, True if older
        """
        if isinstance(buff, SisypheIdentity): return self._dateofbirthday < buff._dateofbirthday
        elif isinstance(buff, date): return self._dateofbirthday < buff
        elif isinstance(buff, (int, float)): return self.getAge() > buff
        else: raise TypeError('parameter functype is not {}, date, int or float.'.format(self.__class__.__name__))

    def isMale(self) -> bool:
        """
            Check whether current SisypheIdentity instance gender attribute is male.

            return  bool, True if patient is male
        """
        return self._gender == SisypheIdentity._GENDERTOCODE['Male']

    def isFemale(self) -> bool:
        """
            Check whether current SisypheIdentity instance gender attribute is female.

            return  bool, True if patient is female
        """
        return self._gender == SisypheIdentity._GENDERTOCODE['Female']

    def saveToTxt(self, filename: str) -> None:
        """
            Save current SisypheIdentity instance to text file (*.txt).

            Parameter

                filename    str, text file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.txt':
            filename = path + '.txt'
        f = open(filename, 'w')
        try:
            f.write(self.__str__())
        except IOError:
            raise IOError('write error.')
        finally:
            f.close()

    def loadFromTxt(self, filename: str) -> None:
        """
            Load current SisypheIdentity instance attributes from text file (*.txt).

            Parameter

                filename    str, text file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.txt':
            filename = path + '.txt'
        if exists(filename):
            f = open(filename, 'r')
            try:
                buff = f.read()
                buff = buff.split('\n')
                self.setLastname(buff[0])
                self.setFirstname(buff[1])
                self.setDateOfBirthday(buff[2])
                self._gender = self._GENDERTOCODE[buff[3]]
            except IOError:
                raise IOError('read error.')
            finally:
                f.close()
        else: raise IOError('no such file : {}'.format(filename))

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
            Write current SisypheIdentity instance attributes to xml instance.

            Parameter

                doc             minidom.Document, xml document
                currentnode     minidom.Element, xml root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                ident = doc.createElement('identity')
                currentnode.appendChild(ident)
                # lastname
                node = doc.createElement('lastname')
                ident.appendChild(node)
                txt = doc.createTextNode(self._lastname)
                node.appendChild(txt)
                # firstname
                node = doc.createElement('firstname')
                ident.appendChild(node)
                txt = doc.createTextNode(self._firstname)
                node.appendChild(txt)
                # dateofbirthday
                node = doc.createElement('dateofbirthday')
                ident.appendChild(node)
                txt = doc.createTextNode(self.getDateOfBirthday(True))
                node.appendChild(txt)
                # gender
                node = doc.createElement('gender')
                ident.appendChild(node)
                txt = doc.createTextNode(self.getGender(True))
                node.appendChild(txt)
            else: raise TypeError('parameter type {} is not xml.dom.minidom.Element.'.format(type(currentnode)))
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXML(self, doc: minidom.Document) -> None:
        """
            Read current SisypheIdentity instance attributes from xml instance.

            Parameter

                doc             minidom.Document, xml document
        """
        if isinstance(doc, minidom.Document):
            ident = doc.getElementsByTagName('identity')
            for node in ident[0].childNodes:
                if node.nodeName == 'lastname':
                    if node.firstChild: self.setLastname(node.firstChild.data)
                    else: self._lastname = ''
                elif node.nodeName == 'firstname':
                    if node.firstChild: self.setFirstname(node.firstChild.data)
                    else: self._firstname = ''
                elif node.nodeName == 'dateofbirthday':
                    if node.firstChild: self.setDateOfBirthday(node.firstChild.data)
                    else: self._dateofbirthday = self._DEFAULTDATE
                elif node.nodeName == 'gender':
                    if node.firstChild: self._gender = self._GENDERTOCODE[node.firstChild.data]
                    else: self._gender = 0
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveToXML(self, filename: str) -> None:
        """
            Save current SisypheIdentity instance attributes to xml file (*.xidentity).

            Parameter

                filename    str, xml file name (*.xidentity)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try:
            f.write(buff)
        except IOError:
            raise IOError('XML file write error.')
        finally:
            f.close()

    def loadFromXML(self, filename: str) -> None:
        """
            Load current SisypheIdentity instance attributes from xml file (*.xidentity).

            Parameter

                filename    str, xml file name (*.xidentity)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.parseXML(doc)
            else: raise IOError('XML file format is not supported.')
        else: raise IOError('no such file : {}'.format(filename))


class SisypheAcquisition(object):
    """
        SisypheAcquisition class

        Description

            Class to manage acquisition attributes of images : modality, sequence, date of scan, frame,
            units of scalar values, labels for LB modality, degrees of freedom and autocorrelation for
            statistical map sequences.

        Inheritance

            object -> SisypheIdentity

        Private attributes

            _modality       int, modality code
            _sequence       str, sequence description
            _dateofscan     date, acquisition date
            _frame          int, stereotactic frame code
            _unit           str, signal unit
            _labels         dict(), dict of labels for LB modality
            _df             int, degrees of freedom (tmap and zmap)
            _autocorrx      float, spatial autocorrelations, x-axis (mm)
            _autocorry      float, spatial autocorrelations, y-axis (mm)
            _autocorrz      float, spatial autocorrelations, z-axis (mm)
            _parent         parent instance

        Class method

            sgetFileExt() -> str
            getFilterExt() -> str
            getLabelsFileExt() -> str
            getLabelsFilterExt() -> str
            getCodeToModalityDict() -> dict
            getModalityToCode() -> dict
            getOTModalityTag() -> str
            getMRModalityTag() -> str
            getCTModalityTag() -> str
            getPTModalityTag() -> str
            getNMModalityTag() -> str
            getLBModalityTag() -> str
            getTPModalityTag() -> str
            getOTSequences() -> tuple[str, ...]
            getPTSequences() -> tuple[str, ...]
            getMRSequences() -> tuple[str, ...]
            getCTSequences() -> tuple[str, ...]
            getNMSequences() -> tuple[str, ...]
            getFrameList() -> tuple[str, ...]
            getUnitList() -> tuple[str, ...]
            getTemplatesList() -> tuple[str, ...]

        Public methods

            __init__(modality: int = 0,
                     sequence: str = '',
                     d: date = date.today(),
                     unit: str = 'No',
                     parent: Sisyphe.sisypheVolume.SisypheVolume | None = None)
            __repr__() -> str
            __str__() -> str
            __contains__(buff: str) -> bool
            __eq__(other: SisypheAcquisition) -> bool
            __ne__(other: SisypheAcquisition) -> bool
            hasParent() -> bool
            setParent(Sisyphe.sisypheVolume.SisypheVolume)
            getParent() -> Sisyphe.sisypheVolume.SisypheVolume
            is3D() -> bool
            is2D() -> bool
            set2D()
            set3D()
            setType(v: str)
            getType() -> str
            getModality(string: bool = True) -> str | int
            setModality(buff: int | str)
            setModalityToMR()
            setModalityToCT()
            setModalityToPT()
            setModalityToNM()
            setModalityToOT()
            setModalityToLB()
            selLabel(index: int, value: str)
            getLabel(index: float | int) -> str
            hasLabels() -> bool
            getLabels() -> dict[int, str]
            loadLabels()
            saveLabels()
            isMR() -> bool
            isCT() -> bool
            isPT() -> bool
            isNM() -> bool
            isOT() -> bool
            isLB() -> bool
            isTP() -> bool
            setDegreesOfFreedom(v: int)
            getDegreesOfFreedom() -> int
            setAutoCorrelations(v: listFloat3 | tupleFloat3)
            getAutoCorrelations() -> tupleFloat3
            setSequenceToTMap()
            setSequenceToZMap()
            setSequenceToGrayMatterMap()
            setSequenceToWhiteMatterMap()
            setSequenceToCerebroSpinalFluidMap()
            setSequenceToCorticalThicknessMap()
            setSequenceToCerebralBloodFlowMap()
            setSequenceToCerebralBloodVolumeMap()
            setSequenceToMeanTransitTimeMap()
            setSequenceToTimeToPicMap()
            setSequenceToDoseMap()
            setSequenceToFractionalAnisotropyMap()
            setSequenceToApparentDiffusionMap()
            setSequenceToDensityMap()
            setSequenceToBiasFieldMap()
            setSequenceToMeanMap()
            setSequenceToMedianMap()
            setSequenceToMinimumMap()
            setSequenceToMaximumMap()
            setSequenceToStandardDeviationMap()
            setSequenceToAlgebraMap()
            setSequenceToMask()
            setSequenceToDisplacementField()
            setSequenceToLabels()
            setSequenceToProbabilityMap()
            setSequenceToT1Weighted()
            setSequenceToT2Weighted()
            setSequenceToT2Star()
            setSequenceToProtonDensityWeighted()
            setSequenceToFLAIR()
            setSequenceToContrastEnhancedT1()
            setSequenceToContrastEnhancedT2()
            setSequenceToContrastEnhancedFLAIR()
            setSequenceToEchoPlanar()
            setSequenceToDiffusionWeighted()
            setSequenceToPerfusionWeighted()
            setSequenceToSusceptibilityWeighted()
            setSequenceToTimeOfFlight()
            setSequenceToContrastEnhancedCT()
            setSequenceToFDG()
            setSequenceToHMPAO()
            setSequenceToECD()
            setSequenceToFPCIT()
            isStandardSequence() -> bool
            isCustomSequence() -> bool
            isDisplacementField() -> bool
            isContrastEnhanced() -> bool
            isTMap() -> bool
            isZMap() -> bool
            isStatisticalMap() -> bool
            getSequence() -> str
            setSequence(buff: str)
            setNoUnit()
            setUnitToPercent()
            setUnitToRatio()
            setUnitToSecond()
            setUnitToMillimeter()
            setUnitToCount()
            setUnitToBq()
            setUnitToBqMl()
            setUnitToSUV()
            setUnitToADCunit()
            setUnitToHounsfield()
            setUnitToGy()
            setUnitToTValue()
            setUnitToZScore()
            setUnitToPValue()
            setUnit(unit: str)
            getUnit(self) -> str
            hasUnit() -> bool
            isStandardUnit() -> bool
            isCustomUnit() -> bool
            getDateOfScan(string: bool = True, f: str = '%Y-%m-%d') -> str | date
            setDateOfScan(buff: str | date = datetime.today(), f: str = '%Y-%m-%d')
            getFrame() -> int
            getFrameAsString() -> str
            setFrame(v: int)
            setFrameAsString(v: str)
            setFrameToUnknown()
            setFrameToNo()
            setFrameToLeksell()
            isCustomSequence() -> bool
            copyFrom(buff: SisypheAcquisition | sc.sisypheVolume.SisypheVolume)
            copy() -> SisypheAcquisition
            isICBM152() -> bool
            isICBM452() -> bool
            isATROPOS() -> bool
            isSRI24() -> bool
            isEqual(buff: SisypheAcquisition) -> bool
            isNotEqual(buff: SisypheAcquisition) -> bool
            getAgeAtScanDate(dateofbirthday: str | SisypheIdentity | date, f: str = '%Y-%m-%d') -> int
            parseXML(doc: minidom.Document)
            createXML(doc:  minidom.Document, currentnode: minidom.Element)
            saveToXML(filename: str)
            loadFromXML(filename: str)

        Creation: 16/03/2021
        Revisions:

            02/10/2022  add LB (i.e. label) modality and methods
            16/04/2023  add TP (i.e. template) modality and methods
            29/08/2023  type hinting
            19/10/2023  add type attribute ('2D' or '3D')
            20/10/2023  add sequence and unit class constants
            18/11/2023  docstrings
    """
    __slots__ = ['_modality', '_sequence', '_type', '_dateofscan', '_frame', '_unit',
                 '_labels', '_df', '_autocorrx', '_autocorry', '_autocorrz', '_parent']

    # Class constants

    UK = 'UNKNOWN'
    CECT = 'CE'
    FDG = 'FDG'
    HMPAO, ECD, FPCIT = 'HMPAO', 'ECD', 'FPCIT'
    PMAP, TMAP, ZMAP, GM, WM, CSF, = 'P MAP', 'T MAP', 'Z MAP', 'GM', 'WM', 'CSF'
    CBF, CBV, MTT, TTP, DOSE, THICK = 'CBF', 'CBV', 'MTT', 'TTP', 'DOSE', 'CORTICAL THICKNESS'
    FA, ADC, DENSITY, BIAS = 'FA', 'MD', 'DENSITY', 'BIAS FIELD'
    MEDIAN, MEAN, MIN, MAX, STD, ALGEBRA = 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'STD', 'ALGEBRA'
    MASK, FIELD, JAC, LABELS, = 'MASK', 'DISPLACEMENT FIELD', 'JACOBIAN', 'LABELS'
    T1, T2, T2S, PD, FLAIR, CET1, CET2 = 'T1', 'T2', 'T2*', 'PD', 'FLAIR', 'CE T1', 'CE T2'
    CEFLAIR, EPI, DWI, PWI, ASL, SWI, TOF = 'CE FLAIR', 'EPI', 'DWI', 'PWI', 'ASL', 'SWI', 'TOF'
    NOFRAME, LEKSELL = 'NO FRAME', 'LEKSELL'
    NOUNIT, PERC, RATIO, SEC, MM = 'No unit', '%', 'ratio', 's', 'mm'
    COUNT, BQ, BQML, SUV, MM2S, HU, GY = 'Count', 'Bq', 'Bq/ml', 'SUV', 'mm2/s', 'HU', 'Gy'
    TVAL, ZSCORE, PVAL = 't-value', 'z-score', 'p-value'

    _MODALITYTOCODE = {'OT': 0, 'MR': 1, 'CT': 2, 'PT': 3, 'NM': 4, 'LB': 5, 'TP': 6}
    _CODETOMODALITY = {0: 'OT', 1: 'MR', 2: 'CT', 3: 'PT', 4: 'NM', 5: 'LB', 6: 'TP'}
    _OTSEQUENCE = (UK, PMAP, TMAP, ZMAP, GM, WM, CSF, THICK, CBF, CBV,
                   MTT, TTP, DOSE, FA, ADC, DENSITY, BIAS, MEDIAN, MEAN,
                   MIN, MAX, STD, ALGEBRA, MASK, LABELS)
    _MRSEQUENCE = (UK, T1, T2, T2S, PD, FLAIR, CET1, CET2, CEFLAIR, EPI,
                   DWI, PWI, ASL, SWI, TOF)
    _CTSEQUENCE = (UK, CECT)
    _PTSEQUENCE = (UK, FDG)
    _NMSEQUENCE = (UK, HMPAO, ECD, FPCIT)
    _TYPE = ('2D', '3D')
    _FRAME = (UK, NOFRAME, LEKSELL)
    _UNIT = (NOUNIT, PERC, RATIO, SEC, MM, COUNT, BQ, BQML, SUV, MM2S, HU,
             GY, TVAL, ZSCORE, PVAL)
    _TEMPLATES = ('ICBM152', 'ICBM452', 'ATROPOS', 'SRI24')
    _FILEEXT = '.xacq'
    _LABELSEXT = '.xlabels'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
            Get SisypheAcquisition file extension.

            return  str, '.xacq'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
            Get SisypheAcquisition filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

            return  str, 'PySisyphe Acquisition (*.xacq)'
        """
        return 'PySisyphe Acquisition (*{})'.format(cls._FILEEXT)

    @classmethod
    def getLabelsFileExt(cls) -> str:
        """
            Get XML labels file extension.

            return  str, '.xlabels'
        """
        return cls._LABELSEXT

    @classmethod
    def getLabelsFilterExt(cls) -> str:
        """
            Get XML labels filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

            return  str, 'PySisyphe Labels (*.xlabels)'
        """
        return 'PySisyphe Labels (*{})'.format(cls._LABELSEXT)

    @classmethod
    def getCodeToModalityDict(cls) -> dict[int, str]:
        """
            Get dict with modality code as key and modality name as value.

            return  dict[int, str], {0: 'OT', 1: 'MR', 2: 'CT', 3: 'PT', 4: 'NM', 5: 'LB', 6: 'TP'}
        """
        return cls._CODETOMODALITY

    @classmethod
    def getModalityToCodeDict(cls) -> dict[str, int]:
        """
            Get dict with modality name as key and modality code as value.

            return  dict[str, int], {'OT': 0, 'MR': 1, 'CT': 2, 'PT': 3, 'NM': 4, 'LB': 5, 'TP': 6}
        """
        return cls._MODALITYTOCODE

    @classmethod
    def getOTModalityTag(cls) -> str:
        """
            Get OT modality str

            return  str, OT modality str
        """
        return cls._CODETOMODALITY[0]

    @classmethod
    def getMRModalityTag(cls) -> str:
        """
            Get MRI modality str

            return  str, MRI modality str
        """
        return cls._CODETOMODALITY[1]

    @classmethod
    def getCTModalityTag(cls) -> str:
        """
            Get CT-scan modality str

            return  str, CT-scan modality str
        """
        return cls._CODETOMODALITY[2]

    @classmethod
    def getPTModalityTag(cls) -> str:
        """
            Get PET-scan modality str

            return  str, PET-scan modality str
        """
        return cls._CODETOMODALITY[3]

    @classmethod
    def getNMModalityTag(cls) -> str:
        """
            Get Nuclear Medicine modality str

            return  str, Nuclear Medicine modality str
        """
        return cls._CODETOMODALITY[4]

    @classmethod
    def getLBModalityTag(cls) -> str:
        """
            Get Label modality str

            return  str, Label modality str
        """
        return cls._CODETOMODALITY[5]

    @classmethod
    def getTPModalityTag(cls) -> str:
        """
            Get Template modality str

            return  str, Template modality str
        """
        return cls._CODETOMODALITY[6]

    @classmethod
    def getOTSequences(cls) -> tuple[str, ...]:
        """
            Get tuple of OT sequence names

            return  tuple[str, ...], tuple of OT sequence names
        """
        return cls._OTSEQUENCE

    @classmethod
    def getMRSequences(cls) -> tuple[str, ...]:
        """
            Get tuple of MRI sequence names

            return  tuple[str, ...], tuple of OT sequence names
        """
        return cls._MRSEQUENCE

    @classmethod
    def getCTSequences(cls) -> tuple[str, ...]:
        """
            Get tuple of CT-scan sequence names

            return  tuple[str, ...], tuple of CT-scan sequence names
        """
        return cls._CTSEQUENCE

    @classmethod
    def getPTSequences(cls) -> tuple[str, ...]:
        """
            Get tuple of PET radiopharmaceutical names

            return  tuple[str, ...], tuple of PET radiopharmaceutical names
        """
        return cls._PTSEQUENCE

    @classmethod
    def getNMSequences(cls) -> tuple[str, ...]:
        """
            Get tuple of Nuclear Medicine radiopharmaceutical names

            return  tuple[str, ...], tuple of Nuclear Medicine radiopharmaceutical names
        """
        return cls._NMSEQUENCE

    @classmethod
    def getFrameList(cls) -> tuple[str, ...]:
        """
            Get tuple of frame names

            return  tuple[str, ...], tuple frame names
        """
        return cls._FRAME

    @classmethod
    def getUnitList(cls) -> tuple[str, ...]:
        """
            Get tuple of units names

            return  tuple[str, ...], tuple units names
        """
        return cls._UNIT

    @classmethod
    def getTemplatesList(cls) -> tuple[str, ...]:
        """
            Get tuple of template names

            return  tuple[str, ...], tuple template names
        """
        return cls._TEMPLATES

    # Special methods

    def __init__(self,
                 modality: int = 0,
                 sequence: str = '',
                 d: date = date.today(),
                 unit: str = 'No',
                 parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        """
            SisypheAcquisition instance constructor

            Parameters

                modality    int, modality code (0 'OT', 1 'MR', 2 'CT', 3 'PT', 4 'NM', 5 'LB', 6 'TP')
                sequence    str, sequence name (default '')
                d           datetime.date, acquisition date (default datetime.today())
                unit        str, unit name (default 'No')
                parent      Sisyphe.sisypheVolume.SisypheVolume | None (default None)
        """
        self._modality = modality
        self._type = '2D'
        self._sequence = sequence
        self._dateofscan = d
        self._frame = 0
        self._unit = unit
        self._labels = dict()
        self._df = 0
        self._autocorrx = 0.0
        self._autocorry = 0.0
        self._autocorrz = 0.0
        self._parent = parent

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheAcquisition instance to str
         """
        txt = 'Acquisition:\n' \
              '\tModality: {}\n' \
              '\tType: {}\n' \
              '\tSequence: {}\n' \
              '\tFrame: {}\n' \
              '\tUnit: {}\n' \
              '\tDate of scan: {}\n'.format(self.getModality(True), self._type, self._sequence,
                                            self.getFrameAsString(), self._unit, self.getDateOfScan(True))
        if self.isStatisticalMap():
            txt += '\tDegrees of freedom: {}\n' \
                   '\tAutocorrelations: {:.1f} x {:.1f} x {:.1f} mm\n'.format(self._df,
                                                                              self._autocorrx,
                                                                              self._autocorry,
                                                                              self._autocorrz)

        return txt

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheAcquisition instance representation
        """
        return '{} class instance at <{}>\n'.format(self.__class__.__name__, str(id(self)))

    def __contains__(self, buff: str) -> bool:
        """
            Special overloaded container method called by the built-in 'in' python operator.
            Check whether buff parameter is the modality or the sequence attribute of the
            current SisypheAcquisition instance

            Parameter

                buff    str

            return  bool, True if buff parameter is in SisypheAcquisition instance
        """
        return self.getModality(True) == buff or self._sequence == buff

    def __eq__(self, other: SisypheAcquisition) -> bool:
        """
            Special overloaded relational operator ==.
            Check whether parameter instance and current SisypheAcquisition instance
            have the same modality, sequence and date of scan attributes
            self == other -> bool

            Parameter

                other   SisypheAcquisition

            return  bool
        """
        return self.isEqual(other)

    def __ne__(self, other: SisypheAcquisition) -> bool:
        """
            Special overloaded relational operator !=.
            Check whether parameter instance and current SisypheAcquisition instance
            have not the same modality, sequence or date of scan attributes
            self != other -> bool

            Parameter

                other   SisypheAcquisition

            return  bool
        """
        return not self.isNotEqual(other)

    # Public methods

    def hasParent(self) -> bool:
        """
            Check whether current SisypheAcquisition instance has a parent,
            i.e. parent attribute is not None.

            return  bool, True if current SisypheAcquisition is defined (not None)
        """
        return self._parent is not None

    def setParent(self, parent: sc.sisypheVolume.SisypheVolume):
        """
            Set parent of the current SisypheAcquisition instance.

            Parameter

                parent  Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(parent, sc.sisypheVolume.SisypheVolume):
            self._parent = parent
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(parent)))

    def getParent(self) -> sc.sisypheVolume.SisypheVolume:
        """
            Get parent of the current SisypheAcquisition instance.

            return  Sisyphe.sisypheVolume.SisypheVolume
        """
        return self._parent

    def is2D(self) -> bool:
        """
            Check whether type attribute of the current
            SisypheAcquisition instance is 2D

            return  bool, True if 2D acquisition
        """
        return self._type == self._TYPE[0]

    def is3D(self) -> bool:
        """
            Check whether type attribute of the current
            SisypheAcquisition instance is 3D

            return  bool, True if 3D acquisition
        """
        return self._type == self._TYPE[1]

    def set2D(self) -> None:
        """
            Set type attribute of the current
            SisypheAcquisition instance to 2D
        """
        self._type = self._TYPE[0]

    def set3D(self) -> None:
        """
            Set type attribute of the current
            SisypheAcquisition instance to 3D
        """
        self._type = self._TYPE[1]

    def setType(self, v: str) -> None:
        """
            Set type attribute ('2D', '3D') of the current
            SisypheAcquisition instance

            Parameter

                v   str, acquisition type ('2D', '3D')
        """
        if v in self._TYPE: self._type = v
        else: self._type = '2D'

    def getType(self) -> str:
        """
            Get type attribute ('2D', '3D') of the current
            SisypheAcquisition instance

            return  str, acquisition type ('2D', '3D')
        """
        return self._type

    def getModality(self, string: bool = True) -> str | int:
        """
            Get modality attribute of the current
            SisypheAcquisition instance

            Parameter

                string  bool,   return modality str if True
                                return modality int code if False

            return  str,    modality str
                    | int,  modality int code
        """
        if string: return SisypheAcquisition._CODETOMODALITY[self._modality]
        else: return self._modality

    def setModality(self, buff: int | str) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance

            Parameter

                buff  str,    modality str
                      | int,  modality int code
        """
        if isinstance(buff, int):
            if buff in range(7): self._modality = buff
            else: self._modality = 0
        elif isinstance(buff, str):
            buff = buff.upper()
            self._modality = SisypheAcquisition._MODALITYTOCODE[buff]
        else: raise TypeError('parameter type {} is not int, str.'.format(type(buff)))

    def setModalityToMR(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to MRI.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['MR']

    def setModalityToCT(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to CT-scan.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['CT']
        self.setUnitToHounsfield()

    def setModalityToPT(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to PET.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['PT']

    def setModalityToNM(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to Nuclear Medicine.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['NM']
        self.setUnitToCount()

    def setModalityToOT(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to OT.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['OT']

    def setModalityToLB(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to Label.
        """
        if self._parent is not None:
            from Sisyphe.core.sisypheVolume import SisypheVolume
            if isinstance(self._parent, SisypheVolume):
                if self._parent.isUInt8Datatype():
                    self._modality = SisypheAcquisition._MODALITYTOCODE['LB']
                    self._sequence = self.LABELS
                    self.setNoUnit()
                    self.loadLabels()
                else: raise TypeError('Image datatype {} is incompatible '
                                      'with LB modality, must be uint8.'.format(self._parent.getDatatype()))

    def setModalityToTP(self) -> None:
        """
            Set modality attribute of the current
            SisypheAcquisition instance to Template.
        """
        self._modality = SisypheAcquisition._MODALITYTOCODE['TP']

    def getLabel(self, index: float | int) -> str:
        """
            Get label name from index value.

            Parameter

                index   float | int, index

            return  str, label name
        """
        if self.isLB():
            if isinstance(index, float): index = int(index)
            if isinstance(index, int):
                if 0 <= index < 256:
                    if index in self._labels: return self._labels[index]
                    else: return ''
            else: raise TypeError('parameter type {} is not int.'.format(type(index)))
        else: raise ValueError('modality {} is not LB.'.format(self.getModality(True)))

    def setLabel(self, index: int, value: str) -> None:
        """
            Set label name for an index value.

            Parameter

                index   float | int,    index
                value   str,            label name
        """
        if self.isLB():
            if isinstance(index, int):
                if isinstance(value, str):
                    if 0 <= index < 256: self._labels[index] = value
                    else: raise KeyError('index parameter {} is out of range [1..256].'.format(index))
                else: raise TypeError('value parameter type {} is not str.'.format(type(index)))
            else: raise TypeError('index parameter type {} is not int.'.format(type(index)))
        else: raise ValueError('modality {} is not LB.'.format(self.getModality(True)))

    def hasLabels(self) -> bool:
        """
            Check that label table is not empty.

            return  bool, True if label table is not empty
        """
        return len(self._labels) > 0

    def getLabels(self) -> dict:
        """
            Get label table

            return  dict[key, value]
                    key     int, index
                    value   str, label name
        """
        if self.isLB(): return self._labels
        else: raise ValueError('modality {} is not LB.'.format(self.getModality(True)))

    def loadLabels(self) -> None:
        """
            Load label table from XML file (*.xlabels).
        """
        if self.isLB() and self.hasParent():
            path, ext = splitext(self._parent.getFilename())
            filename = path + self.getLabelsFileExt()
            if exists(filename):
                doc = minidom.parse(filename)
                root = doc.documentElement
                if root.nodeName == self.getLabelsFileExt()[1:] and root.getAttribute('version') == '1.0':
                    nodes = doc.getElementsByTagName('label')
                    for node in nodes:
                        index = int(node.getAttribute('value'))
                        if node.nodeName == 'label':
                            if node.firstChild:
                                self._labels[index] = node.firstChild.data

    def saveLabels(self) -> None:
        """
            Save label table from XML file (*.xlabels).
        """
        if self.isLB() and self.hasLabels() and self.hasParent():
            doc = minidom.Document()
            root = doc.createElement(self.getLabelsFileExt()[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            for i in range(256):
                if i in self._labels:
                    node = doc.createElement('label')
                    node.setAttribute('value', str(i))
                    root.appendChild(node)
                    txt = doc.createTextNode(self._labels[i])
                    node.appendChild(txt)
            path, ext = splitext(self._parent.getFilename())
            filename = path + self.getLabelsFileExt()
            buffxml = doc.toprettyxml()
            with open(filename, 'w') as f: f.write(buffxml)

    def setDegreesOfFreedom(self, v) -> None:
        """
            Set degrees of freedom attribute of the current SisypheAcquisition instance.
            This attribute is only defined for some statistical maps (i.e. 't-value', 'p-value').

            Parameter

                v   int, degrees of freedom
        """
        if isinstance(v, int): self._df = v
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getDegreesOfFreedom(self) -> int:
        """
            Get degrees of freedom attribute of the current SisypheAcquisition instance.
            This attribute is only defined for some statistical maps (i.e. 't-value', 'p-value').

            return   int, degrees of freedom
        """
        return self._df

    def setAutoCorrelations(self, v: listFloat3 | tupleFloat3) -> None:
        """
            Set autocorrelations attribute of the current SisypheAcquisition instance.
            This attribute is only defined for statistical maps.

            Parameter

                v   listFloat3 | tupleFloat3, autocorrelations
        """
        if isinstance(v, list):
            if len(v) == 3:
                if all([isinstance(i, float) for i in v]):
                    self._autocorrx = v[0]
                    self._autocorry = v[1]
                    self._autocorrz = v[2]
                else: raise TypeError('type of elements in the list {} is not float.'.format(type(v[0])))
            else: raise ValueError('list parameter does not have 3 elements ({}).'.format(len(v)))
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def getAutoCorrelations(self) -> tupleFloat3:
        """
            Get autocorrelations attribute of the current SisypheAcquisition instance.
            This attribute is only defined for statistical maps.

            return  tupleFloat3, autocorrelations
        """
        return self._autocorrx, self._autocorry, self._autocorrz

    def setSequenceToTMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to t map.
        """
        self.setModalityToOT()
        self._sequence = self.TMAP
        self.setUnitToTValue()

    def setSequenceToZMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to Z map.
        """
        self.setModalityToOT()
        self._sequence = self.ZMAP
        self.setUnitToZScore()

    def setSequenceToGrayMatterMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to gray matter map.
        """
        self.setModalityToOT()
        self._sequence = self.GM
        self.setUnitToRatio()

    def setSequenceToWhiteMatterMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to white matter map.
        """
        self.setModalityToOT()
        self._sequence = self.WM
        self.setUnitToRatio()

    def setSequenceToCerebroSpinalFluidMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to cerebro-spinal fluid map.
        """
        self.setModalityToOT()
        self._sequence = self.CSF
        self.setUnitToRatio()

    def setSequenceToCorticalThicknessMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to cortical thickness map.
        """
        self.setModalityToOT()
        self._sequence = self.THICK
        self.setUnitToMillimeter()

    def setSequenceToCerebralBloodFlowMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to cerebral blood flow map.
        """
        self.setModalityToOT()
        self._sequence = self.CBF
        self.setNoUnit()

    def setSequenceToCerebralBloodVolumeMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to cerebral blood volume map.
        """
        self.setModalityToOT()
        self._sequence = self.CBV
        self.setNoUnit()

    def setSequenceToMeanTransitTimeMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to mean transit time map.
        """
        self.setModalityToOT()
        self._sequence = self.MTT
        self.setUnitToSecond()

    def setSequenceToTimeToPicMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to time to pic map.
        """
        self.setModalityToOT()
        self._sequence = self.TTP
        self.setUnitToSecond()

    def setSequenceToDoseMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to dose map.
        """
        self.setModalityToOT()
        self._sequence = self.DOSE
        self.setUnitToGy()

    def setSequenceToFractionalAnisotropyMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to fractional anisotropy map.
        """
        self.setModalityToOT()
        self._sequence = self.FA
        self.setUnitToRatio()

    def setSequenceToApparentDiffusionMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to apparent diffusion map.
        """
        self.setModalityToOT()
        self._sequence = self.ADC
        self.setUnitToADCunit()

    def setSequenceToDensityMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to density map.
        """
        self.setModalityToOT()
        self._sequence = self.DENSITY
        self.setNoUnit()

    def setSequenceToBiasFieldMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to bias field map.
        """
        self.setModalityToOT()
        self._sequence = self.BIAS
        self.setNoUnit()

    def setSequenceToMeanMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to mean map.
        """
        self.setModalityToOT()
        self._sequence = self.MEAN
        self.setNoUnit()

    def setSequenceToMedianMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to median map.
        """
        self.setModalityToOT()
        self._sequence = self.MEDIAN
        self.setNoUnit()

    def setSequenceToMinimumMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to minimum map.
        """
        self.setModalityToOT()
        self._sequence = self.MIN
        self.setNoUnit()

    def setSequenceToMaximumMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to maximum map.
        """
        self.setModalityToOT()
        self._sequence = self.MAX
        self.setNoUnit()

    def setSequenceToStandardDeviationMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to standard deviation map.
        """
        self.setModalityToOT()
        self._sequence = self.STD
        self.setNoUnit()

    def setSequenceToAlgebraMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to algebra map.
        """
        self.setModalityToOT()
        self._sequence = self.ALGEBRA
        self.setNoUnit()

    def setSequenceToMask(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to mask.
        """
        self.setModalityToOT()
        self._sequence = self.MASK
        self.setNoUnit()

    def setSequenceToDisplacementField(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to displacement field.
        """
        if self.hasParent():
            parent = self.getParent()
            if parent.isFloatDatatype():
                if parent.getNumberOfComponentsPerPixel() == 3:
                    self.setModalityToOT()
                    self._sequence = self.FIELD
                    self.setUnitToMillimeter()
                else: raise ValueError('Volume has {} components,\n3 components required '
                                       'to be a displacement field.'.format(parent.getNumberOfComponentsPerPixel()))
            else: raise TypeError('Volume datatype is {}.\nIt must be Float32 or 64 to be a '
                                  'displacement field.'.format(parent.isFloat64Datatype()))
        else: raise ValueError('No SisypheVolume parent.')

    def setSequenceToLabels(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to labels.
        """
        self.setModalityToLB()
        self._sequence = self.LABELS

    def setSequenceToProbabilityMap(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to probability map.
        """
        self.setModalityToOT()
        self._sequence = self.PMAP

    def setSequenceToT1Weighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to T1 weighted.
        """
        self.setModalityToMR()
        self._sequence = self.T1
        self.setNoUnit()

    def setSequenceToT2Weighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to T2 weighted.
        """
        self.setModalityToMR()
        self._sequence = self.T2
        self.setNoUnit()

    def setSequenceToT2Star(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to T2 star.
        """
        self.setModalityToMR()
        self._sequence = self.T2S
        self.setNoUnit()

    def setSequenceToProtonDensityWeighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to proton density weighted.
        """
        self.setModalityToMR()
        self._sequence = self.PD
        self.setNoUnit()

    def setSequenceToFLAIR(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to FLAIR.
        """
        self.setModalityToMR()
        self._sequence = self.FLAIR
        self.setNoUnit()

    def setSequenceToContrastEnhancedT1(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to contrast enhanced T1 weighted.
        """
        self.setModalityToMR()
        self._sequence = self.CET1
        self.setNoUnit()

    def setSequenceToContrastEnhancedT2(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to contrast enhanced T2 weighted.
        """
        self.setModalityToMR()
        self._sequence = self.CET2
        self.setNoUnit()

    def setSequenceToContrastEnhancedFLAIR(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to contrast enhanced FLAIR.
        """
        self.setModalityToMR()
        self._sequence = self.CEFLAIR
        self.setNoUnit()

    def setSequenceToEchoPlanar(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to echo-planar.
        """
        self.setModalityToMR()
        self._sequence = self.EPI
        self.setNoUnit()

    def setSequenceToDiffusionWeighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to diffusion weighted.
        """
        self.setModalityToMR()
        self._sequence = self.DWI
        self.setNoUnit()

    def setSequenceToPerfusionWeighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to perfusion weighted.
        """
        self.setModalityToMR()
        self._sequence = self.PWI
        self.setNoUnit()

    def setSequenceToSusceptibilityWeighted(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to susceptibility weighted.
        """
        self.setModalityToMR()
        self._sequence = self.SWI
        self.setNoUnit()

    def setSequenceToTimeOfFlight(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to time of flight.
        """
        self.setModalityToMR()
        self._sequence = self.TOF
        self.setNoUnit()

    def setSequenceToContrastEnhancedCT(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance
            to contrast enhanced CT-scan.
        """
        self.setModalityToCT()
        self._sequence = self.CECT

    def setSequenceToFDG(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to FDG.
        """
        self.setModalityToPT()
        self._sequence = self.FDG

    def setSequenceToHMPAO(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to HMPAO.
        """
        self.setModalityToNM()
        self._sequence = self.HMPAO

    def setSequenceToECD(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to ECD.
        """
        self.setModalityToNM()
        self._sequence = self.ECD

    def setSequenceToFPCIT(self) -> None:
        """
            Set sequence attribute of the current SisypheAcquisition instance to FPCIT.
        """
        self.setModalityToNM()
        self._sequence = self.FPCIT

    def isStandardSequence(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is standard.
            A standard sequence has a predefined str value in SisypheAcquisition instance.

            return  bool, True if sequence is standard
        """
        if self.isOT(): return self._sequence in self._OTSEQUENCE
        elif self.isMR(): return self._sequence in self._MRSEQUENCE
        elif self.isCT(): return self._sequence in self._CTSEQUENCE
        elif self.isNM(): return self._sequence in self._NMSEQUENCE
        elif self.isPT(): return self._sequence in self._PTSEQUENCE
        else: return False

    def isDisplacementField(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is a displacement field.

            return  bool, True if sequence is a displacement field
        """
        return self.getSequence() == self.FIELD

    def setNoUnit(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to no unit.
        """
        self._unit = self.NOUNIT

    def setUnitToPercent(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to percent.
        """
        self._unit = self.PERC

    def setUnitToRatio(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to ratio.
        """
        self._unit = self.RATIO

    def setUnitToSecond(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to second.
        """
        self._unit = self.SEC

    def setUnitToMillimeter(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to millimeter.
        """
        self._unit = self.MM

    def setUnitToCount(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to count.
        """
        self._unit = self.COUNT

    def setUnitToBq(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to Bq.
        """
        self._unit = self.BQ

    def setUnitToBqMl(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to Bq/ml.
        """
        self._unit = self.BQML

    def setUnitToSUV(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to SUV.
        """
        self._unit = self.SUV

    def setUnitToADCunit(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to mm2/s.
        """
        self._unit = self.MM2S

    def setUnitToHounsfield(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to Hounsfield.
        """
        self._unit = self.HU

    def setUnitToGy(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to Gy.
        """
        self._unit = self.GY

    def setUnitToTValue(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to t-value.
        """
        self._unit = self.TVAL

    def setUnitToZScore(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to Z-score.
        """
        self._unit = self.ZSCORE

    def setUnitToPValue(self) -> None:
        """
            Set the unit attribute of the current SisypheAcquisition instance to p-value.
        """
        self._unit = self.PVAL

    def isStandardUnit(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance unit attribute is standard.
            A standard unit has a predefined str value in SisypheAcquisition instance.

            return  bool, True if unit is standard
        """
        return self._unit in self._UNIT

    def isContrastEnhanced(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is contrast enhanced.

            return  bool, True if sequence is contrast enhanced
        """
        return self._sequence[:2] == 'CE'

    def isTMap(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is a t-map.

            return  bool, True if sequence is a t-map
        """
        return self._sequence == self.TMAP

    def isZMap(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is a z-map.

            return  bool, True if sequence is a z-map
        """
        return self._sequence == self.ZMAP

    def isStatisticalMap(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute
            is a t-map or a z-map.

            return  bool, True if sequence is a t-map or a z-map
        """
        return self.isTMap() or self.isZMap()

    def getSequence(self) -> str:
        """
            Get current SisypheAcquisition instance sequence attribute.

            return  str, sequence attribute
        """
        return self._sequence

    def setSequence(self, buff: str) -> None:
        """
            Set the current SisypheAcquisition instance sequence attribute.

            Parameter

                buff    str, sequence attribute
        """
        self._sequence = buff

    def getDateOfScan(self, string: bool = True, f: str = '%Y-%m-%d') -> str | date:
        """
            Get date of scan attribute of the current SisypheAcquisition instance.

            parameters

                string  bool, if True return date of scan as str
                              if False return date of scan as datetime.date
                f       str, format used to convert date to str (default '%Y-%m-%d')

            return  str,                date of scan as str
                    | datetime.date,    date of scan as datetime.date
        """
        if string: return self._dateofscan.strftime(f)
        else: return self._dateofscan

    def setDateOfScan(self, buff: str | date = datetime.today(), f: str = '%Y-%m-%d') -> None:
        """
            Set the date of scan attribute of the current SisypheAcquisition instance.

            parameters

                buff    str,                date of scan as str
                        | datetime.date,    date of scan as datetime.date
                        (default datetime.today())
                f       str, format used to convert date to str (default '%Y-%m-%d')
        """
        if isinstance(buff, str):
            self._dateofscan = datetime.strptime(buff, f).date()
        elif isinstance(buff, date):
            self._dateofscan = buff
        else:
            raise TypeError('parameter functype is not date or str.')

    def getFrame(self) -> int:
        """
            Get current SisypheAcquisition instance frame code attribute.
            (0 unknown, 1 no frame, 2 Leksell frame)

            return  str, frame code attribute
        """
        return self._frame

    def getFrameAsString(self) -> str:
        """
            Get current SisypheAcquisition instance frame str attribute.
            ('UNKNOWN', 'NO FRAME', 'LEKSELL')

            return  str, frame str attribute
        """
        return self._FRAME[self._frame]

    def setFrame(self, v: int) -> None:
        """
            Set the current SisypheAcquisition instance frame code attribute.
            (0 unknown, 1 no frame, 2 Leksell frame)

            Parameter

                v   str, frame code attribute
        """
        if isinstance(v, int):
            if 0 <= v < 3:
                self._frame = v
            else: raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setFrameAsString(self, v: str) -> None:
        """
            Set the current SisypheAcquisition instance frame str attribute.
            ('UNKNOWN', 'NO FRAME', 'LEKSELL')

            Parameter

                v   str, frame str attribute
        """
        if isinstance(v, str):
            if v in self._FRAME:
                self._frame = self._FRAME.index(v)
            else: raise ValueError('parameter is not a valid frame str.')
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    def setFrameToUnknown(self) -> None:
        """
            Set the current SisypheAcquisition instance frame attribute to unknown.
        """
        self._frame = 0

    def setFrameToNo(self) -> None:
        """
            Set the current SisypheAcquisition instance frame attribute to no frame.
        """
        self._frame = 1

    def setFrameToLeksell(self) -> None:
        """
            Set the current SisypheAcquisition instance frame attribute to Leksell.
        """
        self._frame = 2

    def setUnit(self, unit: str) -> None:
        """
            Set the current SisypheAcquisition instance unit attribute.

            Parameter

                v   str, unit attribute
        """
        if isinstance(unit, str): self._unit = unit
        else: raise TypeError('parameter type {} is not str'.format(type(unit)))

    def getUnit(self) -> str:
        """
            Get current SisypheAcquisition instance unit attribute.

            return  str, unit attribute
        """
        return self._unit

    def hasUnit(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance unit attribute is defined.

            return  bool, True if the unit attribute is defined
        """
        return self._unit != self.NOUNIT

    def isCustomSequence(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance sequence attribute is not standard.
            A standard sequence has a predefined str value in SisypheAcquisition instance.

            return  bool, True if sequence is not standard
        """
        return not self.isStandardSequence()

    def isCustomUnit(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance unit attribute is not standard.
            A standard unit has a predefined str value in SisypheAcquisition instance.

            return  bool, True if unit is not standard
        """
        return not self.isStandardUnit()

    def copyFrom(self, buff: SisypheAcquisition | sc.sisypheVolume.SisypheVolume) -> None:
        """
            Copy attributes of the acquisition parameter to
            the current SisypheAcquisition instance (deep copy).

            Parameter

                buff    SisypheAcquisition | Sisyphe.sisypheVolume.SisypheVolume
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(buff, sc.sisypheVolume.SisypheVolume):
            buff = buff.acquisition
        if isinstance(buff, SisypheAcquisition):
            self._modality = buff._modality
            self._sequence = buff._sequence
            self._dateofscan = buff._dateofscan
            self._frame = buff._frame
            self._unit = buff._unit
            self._labels = buff._labels
            self._df = buff._df
            self._autocorrx = buff._autocorrx
            self._autocorry = buff._autocorry
            self._autocorrz = buff._autocorrz
        else: raise TypeError('parameter type {} is not {} or SisypheVolume.'.format(type(buff), self.__class__.__name__))

    def copy(self) -> SisypheAcquisition:
        """
            Copy the current SisypheAcquisition instance (deep copy).

            return   SisypheAcquisition
        """
        return deepcopy(self)

    def isMR(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is MRI.

            return  bool, True if MRI modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['MR']

    def isCT(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is CT-scan.

            return  bool, True if CT-scan modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['CT']

    def isPT(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is TEP.

            return  bool, True if TEP modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['PT']

    def isNM(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is Nuclear Medicine.

            return  bool, True if Nuclear Medicine modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['NM']

    def isOT(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is OT.

            return  bool, True if OT modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['OT']

    def isLB(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is Label.

            return  bool, True if Label modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['LB']

    def isTP(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance modality attribute is Template.

            return  bool, True if Template modality
        """
        return self._modality == SisypheAcquisition._MODALITYTOCODE['TP']

    def isICBM152(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance attributes
            are Template modality and ICBM152 sequence.

            return  bool, True if Template modality and ICBM152 sequence
        """
        return self.isTP() and self._sequence == self._TEMPLATES[0]

    def isICBM452(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance attributes
            are Template modality and ICBM452 sequence.

            return  bool, True if Template modality and ICBM452 sequence
        """
        return self.isTP() and self._sequence == self._TEMPLATES[1]

    def isATROPOS(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance attributes
            are Template modality and ATROPOS sequence.

            return  bool, True if Template modality and ATROPOS sequence
        """
        return self.isTP() and self._sequence == self._TEMPLATES[2]

    def isSRI24(self) -> bool:
        """
            Check whether the current SisypheAcquisition instance attributes
            are Template modality and SRI24 sequence.

            return  bool, True if Template modality and SRI24 sequence
        """
        return self.isTP() and self._sequence == self._TEMPLATES[3]

    def isEqual(self, buff: SisypheAcquisition) -> bool:
        """
            Check whether parameter instance and current SisypheAcquisition instance
            have the same modality, sequence and date of scan attributes
            self == other -> bool

            Parameter

                other   SisypheAcquisition

            return  bool
        """
        if isinstance(buff, SisypheAcquisition):
            return buff._modality == self._modality and \
                   buff._sequence == self._sequence and \
                   buff._dateofscan == self._dateofscan
        else: raise TypeError('parameter type is not {}.'.format(self.__class__.__name__))

    def isNotEqual(self, buff: SisypheAcquisition) -> bool:
        """
            Check whether parameter instance and current SisypheAcquisition instance
            have not the same modality, sequence or date of scan attributes
            self != other -> bool

            Parameter

                other   SisypheAcquisition

            return  bool
        """
        return not self.isEqual(buff)

    def getAgeAtScanDate(self, dateofbirthday: str | SisypheIdentity | date, f: str = '%Y-%m-%d') -> int:
        """
            Get the patient's age supplied as parameter on the scan date.

            Parameters

                dateofbirthday  str,                birthdate as str
                                | SisypheIdentity   birthdate attribute of the SisypheIdentity instance
                                | datetime.date     birthdate as datetime.date
                f               str, format used to convert date to str (default '%Y-%m-%d')

            return  int, patient age
        """
        if isinstance(dateofbirthday, str):
            dateofbirthday = datetime.strptime(dateofbirthday, f).date()
        elif isinstance(dateofbirthday, SisypheIdentity):
            dateofbirthday = dateofbirthday.getDateOfBirthday(False)
        # elif isinstance(dateofbirthday, Volume):
        #    dateofbirthday = dateofbirthday.getIdentity().getDateOfBirthday()
        if isinstance(dateofbirthday, date):
            delta = self._dateofscan - dateofbirthday
            return int(delta.days / 365)
        else:
            raise TypeError('parameter functype is not str, date, SisypheIdentity or SisypheVolume.')

    def createXML(self, doc:  minidom.Document, currentnode: minidom.Element) -> None:
        """
            Write current SisypheAcquisition instance attributes to xml instance.

            Parameter

                doc             minidom.Document, xml document
                currentnode     minidom.Element, xml root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                attr = doc.createElement('acquisition')
                currentnode.appendChild(attr)
                # modality
                node = doc.createElement('modality')
                attr.appendChild(node)
                txt = doc.createTextNode(self.getModality(True))
                node.appendChild(txt)
                # type
                node = doc.createElement('type')
                attr.appendChild(node)
                txt = doc.createTextNode(self._type)
                node.appendChild(txt)
                # sequence
                node = doc.createElement('sequence')
                attr.appendChild(node)
                txt = doc.createTextNode(self._sequence)
                node.appendChild(txt)
                # unit
                node = doc.createElement('unit')
                attr.appendChild(node)
                txt = doc.createTextNode(self._unit)
                node.appendChild(txt)
                # frame
                node = doc.createElement('frame')
                attr.appendChild(node)
                txt = doc.createTextNode(str(self._frame))
                node.appendChild(txt)
                # dateofscan
                node = doc.createElement('dateofscan')
                attr.appendChild(node)
                txt = doc.createTextNode(self.getDateOfScan(True))
                node.appendChild(txt)
                # degree of freedom
                node = doc.createElement('dof')
                attr.appendChild(node)
                txt = doc.createTextNode(str(self.getDegreesOfFreedom()))
                node.appendChild(txt)
                # autocorrelations
                node = doc.createElement('autocorrelations')
                attr.appendChild(node)
                buff = self.getAutoCorrelations()
                buff = ' '.join([str(i) for i in buff])
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
            else: raise TypeError('parameter functype is not xml.dom.minidom.Element.')
        else: raise TypeError('parameter functype is not xml.dom.minidom.Document.')

    def parseXML(self, doc: minidom.Document) -> None:
        """
            Read current SisypheAcquisition instance attributes from xml instance.

            Parameter

                doc             minidom.Document, xml document
        """
        if isinstance(doc, minidom.Document):
            attr = doc.getElementsByTagName('acquisition')
            for node in attr[0].childNodes:
                if node.nodeName == 'modality':
                    if node.firstChild: self.setModality(node.firstChild.data)
                    else: self.setModalityToOT()
                if node.nodeName == 'type':
                    if node.firstChild: self.setType(node.firstChild.data)
                    else: self.setModalityToOT()
                elif node.nodeName == 'sequence':
                    if node.firstChild: self.setSequence(node.firstChild.data)
                    else: self._sequence = ''
                elif node.nodeName == 'unit':
                    if node.firstChild: self.setUnit(node.firstChild.data)
                    else: self._unit = self.NOUNIT
                elif node.nodeName == 'frame':
                    if node.firstChild: self.setFrame(int(node.firstChild.data))
                    else: self._frame = 0
                elif node.nodeName == 'dateofscan':
                    if node.firstChild: self.setDateOfScan(node.firstChild.data)
                    else: self._dateofscan = date.today()
                elif node.nodeName == 'dof':
                    if node.firstChild: self.setDegreesOfFreedom(int(node.firstChild.data))
                elif node.nodeName == 'autocorrelations':
                    if node.firstChild:
                        buff = node.firstChild.data
                        buff = buff.split(' ')
                        self.setAutoCorrelations([float(buff[0]), float(buff[1]), float(buff[2])])
        else: raise TypeError('parameter functype is not xml.dom.minidom.Document.')

    def saveToXML(self, filename: str) -> None:
        """
            Save current SisypheAcquisition instance attributes to xml file (*.xacq).

            Parameter

                filename    str, xml file name (*.xacq)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()
        if self.isLB() and self.hasLabels(): self.saveLabels()

    def loadFromXML(self, filename: str) -> None:
        """
            Load current SisypheAcquisition instance attributes from xml file (*.xacq).

            Parameter

                filename    str, xml file name (*.xacq)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.parseXML(doc)
            else: raise IOError('XML file format is not supported.')
            if self.isLB(): self.loadLabels()
        else: raise IOError('No such file {}'.format(filename))

    isTemplate = isTP


class SisypheDisplay(object):
    """
        SisypheDisplay class

        Description

            Class to manage LUT attribute of images.

        Inheritance

            object -> SisypheIdentity

        Private attributes

            _rangemin   float
            _rangemax   float
            _windowmin  float
            _windowmax  float
            _lut        SisypheLut instance
            _parent     parent instance

        Class method

            getFileExt() -> str
            getFilterExt() -> str

        Public methods

            __init__(rangemin: float = 0.0,
                     rangemax: float = 0.0,
                     windowmin: float | None = None,
                     windowmax: float | None = None,
                     lut: Sisyphe.sisypheLUT.SisypheLut | None = None,
                     parent: Sisyphe.sisypheVolume.SisypheVolume | None = None)
            __str__() -> str
            __repr__() -> str
            hasParent() -> str
            setParent(self, parent: Sisyphe.sisypheVolume.SisypheVolume)
            getParent() -> Sisyphe.sisypheVolume.SisypheVolume
            copyFrom(self, buff: SisypheDisplay | Sisyphe.sisypheVolume.SisypheVolume)
            copy() -> SisypheDisplay
            updateVTKLUT()
            getLUT() -> Sisyphe.sisypheLUT.SisypheLut
            getVTKLUT() -> vtk.vtkLookupTable
            setLUT(lut: SisypheLut)
            getWindow() -> Tuple[float, float]
            getWindowMin() -> float
            getWindowMax() -> float
            getRange() -> Tuple[float, float]
            getRangeMin() -> float
            getRangeMax() -> float
            setDefaultWindowMin()
            setDefaultWindowMax()
            setWindow(vmin: float, vmax: float)
            setWindowMin(v: float)
            setWindowMax(v: float)
            setRangeMin(v: float)
            setRangeMax(v: float)
            setRange(vmin: float, vmax: float)
            setDefaultLut()
            hasZeroOneRange() -> bool
            hasNegativeValues() -> bool
            convertRangeWindowToInt()
            setDefaultWindow()
            isDefaultWindow() -> bool
            setDefaultLut()
            parseXML(doc: minidom.Document)
            createXML(doc: minidom.Document, currentnode: minidom.Element)
            saveToXML(filename: str)
            loadFromXML(filename: str)

        Creation: 18/03/2021
        Revisions:

            24/08/2023  copy() and copyFrom() methods bugfix
            29/08/2023  type hinting
            18/11/2023  docstrings
    """
    __slots__ = ['_rangemin', '_rangemax', '_windowmin', '_windowmax', '_lut', '_parent']

    # Class constant

    _FILEEXT = '.xdisplay'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
            Get SisypheDisplay file extension.

            return  str, '.xdisplay'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
            Get SisypheAcquisition filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

            return  str, 'PySisyphe Display (*.xdisplay)'
        """
        return 'PySisyphe Display (*{})'.format(cls._FILEEXT)

    # Special methods

    def __init__(self,
                 rangemin: float = 0.0,
                 rangemax: float = 0.0,
                 windowmin: float | None = None,
                 windowmax: float | None = None,
                 lut: SisypheLut | None = None,
                 parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        """
            SisypheDisplay instance constructor

            Parameters

                rangemin    float, minimum scalar value in the image (default 0.0)
                rangemax    float, maximum scalar value in the image (default 0.0)
                windowmin   float | None, minimum value of the lut windowing (default None)
                windowmax   float | None, maximum value of the lut windowing (default None)
                lut         sisyphe.sisypheLUT.SisypheLut | None = None, look-up table colormap (default None)
                parent      Sisyphe.sisypheVolume.SisypheVolume | None (default None)
        """
        # Init range and window
        self._rangemin = rangemin
        self._rangemax = rangemax
        if windowmin is not None: self._windowmin = windowmin
        else: self._windowmin = rangemin
        if windowmax is not None: self._windowmax = windowmax
        else: self._windowmax = rangemax
        # Init SisypheLut
        if isinstance(lut, str): self._lut = SisypheLut(lut)
        elif isinstance(lut, SisypheLut): self._lut = lut
        else: self._lut = SisypheLut()
        self.updateVTKLUT()
        self._parent = parent

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheDisplay instance to str
         """
        if self.hasParent():
            v = self.getParent()
            if v.isIntegerDatatype():
                txt = 'Display:\n\tRange: {} to {}\n\tWindow: {} to {}\n\tLut: {}\n\tName: {}\n'
                return txt.format(int(self._rangemin), int(self._rangemax),
                                  int(self._windowmin), int(self._windowmax),
                                  self._lut.getLUTType(True), self._lut.getName())
        txt = 'Display:\n\tRange: {:.2f} to {:.2f}\n\tWindow: {:.2f} to {:.2f}\n\tLut: {}\n\tName: {}\n'
        return txt.format(self._rangemin, self._rangemax,
                          self._windowmin, self._windowmax,
                          self._lut.getLUTType(True), self._lut.getName())

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheDisplay instance representation
        """
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    # Public methods

    def hasParent(self) -> bool:
        """
            Check whether current SisypheDisplay instance has a parent,
            i.e. parent attribute is not None.

            return  bool, True if current SisypheDisplay is defined (not None)
        """
        return self._parent is not None

    def setParent(self, parent: sc.sisypheVolume.SisypheVolume) -> None:
        """
            Set parent of the current SisypheDisplay instance.

            Parameter

                parent  Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(parent, sc.sisypheVolume.SisypheVolume):
            self._parent = parent
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(parent)))

    def getParent(self) -> sc.sisypheVolume.SisypheVolume:
        """
            Get parent of the current SisypheDisplay instance.

            return  Sisyphe.sisypheVolume.SisypheVolume
        """
        return self._parent

    def copyFrom(self, buff: SisypheDisplay | sc.sisypheVolume.SisypheVolume) -> None:
        """
            Copy attributes of the display parameter to
            the current SisypheDisplay instance (deep copy).

            Parameter

                buff    SisypheDisplay | Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(buff, sc.sisypheVolume.SisypheVolume):
            buff = buff.display
        if isinstance(buff, SisypheDisplay):
            self._rangemin = buff._rangemin
            self._rangemax = buff._rangemax
            self._windowmin = buff._windowmin
            self._windowmax = buff._windowmax
            self._lut = buff._lut.copy()
        else: raise TypeError('parameter type {} is not {} or SisypheVolume.'.format(type(buff), self.__class__.__name__))

    def copy(self) -> SisypheDisplay:
        """
            Copy the current SisypheDisplay instance (deep copy).

            return   SisypheDisplay
        """
        buff = SisypheDisplay()
        buff._rangemin = self._rangemin
        buff._rangemax = self._rangemax
        buff._windowmin = self._windowmin
        buff._windowmax = self._windowmax
        buff._lut = self._lut.copy()
        return buff

    def updateVTKLUT(self) -> None:
        """
            Apply windowing attributes to current SisypheDisplay instance.
        """
        self._lut.setWindowRange(self._windowmin, self._windowmax)

    def getLUT(self) -> SisypheLut:
        """
            Get Lut attribute of the current SisypheDisplay instance.

            return  Sisyphe.sisypheLUT.SisypheLut, PySisyphe Look-up-table colormap instance
        """
        return self._lut

    def getVTKLUT(self) -> vtkLookupTable:
        """
            Get Lut attribute of the current SisypheDisplay instance.

            return  vtk.vtkLookupTable, VTK Look-up-table colormap instance
        """
        return self._lut.getvtkLookupTable()

    def setLUT(self, lut: SisypheLut) -> None:
        """
            Set Lut attribute of the current SisypheDisplay instance.

            Parameter

                lut     Sisyphe.sisypheLUT.SisypheLut, PySisyphe Look-up-table colormap instance
        """
        if isinstance(lut, SisypheLut): self._lut = lut
        else: raise TypeError('parameter type {} is not SisypheLut.'.format(type(lut)))

    def getWindow(self) -> tuple[float, float] | tuple[int, int]:
        """
            Get lut windowing attributes of the current SisypheDisplay instance.

            return  tuple[float, float] | tuple[int, int], minimum and maximum windowing values
        """
        return self._windowmin, self._windowmax

    def getWindowMin(self) -> float | int:
        """
            Get minimum lut windowing attribute of the current SisypheDisplay instance.

            return  float | int, minimum windowing value
        """
        return self._windowmin

    def getWindowMax(self) -> float | int:
        """
            Get maximum lut windowing attribute of the current SisypheDisplay instance.

            return  float | int, maximum windowing value
        """
        return self._windowmax

    def getRange(self) -> tuple[float, float] | tuple[int, int]:
        """
            Get scalar values range attributes of the current SisypheDisplay instance.

            return  tuple[float, float] | tuple[int, int], minimum and maximum scalar values
        """
        return self._rangemin, self._rangemax

    def getRangeMin(self) -> float | int:
        """
            Get minimum scalar value attribute of the current SisypheDisplay instance.

            return  float | int, minimum scalar value
        """
        return self._rangemin

    def getRangeMax(self) -> float | int:
        """
            Get maximum scalar value attribute of the current SisypheDisplay instance.

            return  float | int, maximum scalar value
        """
        return self._rangemax

    def setDefaultWindowMin(self) -> None:
        """
            Set minimum windowing value of the current SisypheDisplay instance to
            minimum scalar value of the image array.
        """
        self._windowmin = self._rangemin
        self.updateVTKLUT()

    def setWindowMin(self, v: float) -> None:
        """
            Set minimum windowing value of the current SisypheDisplay instance.

            Parameter

                v   float, minimum windowing value
        """
        if v < self._rangemin: self._windowmin = self._rangemin
        else: self._windowmin = v
        self.updateVTKLUT()

    def setDefaultWindowMax(self) -> None:
        """
            Set maximum windowing value of the current SisypheDisplay instance to
            maximum scalar value of the image array.
        """
        self._windowmax = self._rangemax
        self.updateVTKLUT()

    def setWindowMax(self, v: float) -> None:
        """
            Set maximum windowing value of the current SisypheDisplay instance.

            Parameter

                v   float, maximum windowing value
        """
        if v > self._rangemax: self._windowmax = self._rangemax
        else: self._windowmax = v
        self.updateVTKLUT()

    def setRangeMin(self, v: float) -> None:
        """
            Set minimum scalar value of the current SisypheDisplay instance.

            Parameter

                v   float, minimum scalar value
        """
        self._rangemin = v
        if self._windowmin < v: self._windowmin = v
        self.updateVTKLUT()

    def setRangeMax(self, v: float) -> None:
        """
            Set maximum scalar value of the current SisypheDisplay instance.

            Parameter

                v   float, maximum scalar value
        """
        self._rangemax = v
        if self._windowmax > v: self._windowmax = v
        self.updateVTKLUT()

    def setWindow(self, vmin: float, vmax: float) -> None:
        """
            Set windowing lut attributes of the current SisypheDisplay instance.

            Parameters

                vmin    float, minimum windowing value
                vmax    float, maximum windowing value
        """
        if vmax >= vmin:
            if vmin < self._rangemin: vmin = self._rangemin
            if vmax > self._rangemax: vmax = self._rangemax
            self._windowmin = vmin
            self._windowmax = vmax
            self.updateVTKLUT()
        else: raise ValueError('second parameter {} is not greater than first parameter {}.'.format(vmax, vmin))

    def setRange(self, vmin: float, vmax: float) -> None:
        """
            Set scalar range attributes of the current SisypheDisplay instance.

            Parameters

                vmin    float, minimum scalar value
                vmax    float, maximum scalar value
        """
        if vmax >= vmin:
            self._rangemin = vmin
            self._rangemax = vmax
            self._windowmin = vmin
            self._windowmax = vmax
            self.updateVTKLUT()
        else: raise ValueError('second parameter {} is not greater than first parameter {}.'.format(vmax, vmin))

    def hasZeroOneRange(self) -> bool:
        """
            Check whether scalar values range of the current SisypheDisplay instance is (0.0, 1.0).

            return  bool, True if scalar values range is (0.0, 1.0)
        """
        return self._rangemin >= 0.0 and self._rangemax <= 1.0

    def hasNegativeValues(self) -> bool:
        """
            Check whether minimum scalar value of the current SisypheDisplay instance is negative.

            return  bool, True if minimum scalar value is negative
        """
        return self._rangemin < 0.0

    def convertRangeWindowToInt(self) -> None:
        """
            Conversion of windowing and scalar values attributes of the current SisypheDisplay instance to integers.
        """
        self._rangemin = int(self._rangemin)
        self._rangemax = int(self._rangemax)
        self._windowmin = int(self._windowmin)
        self._windowmax = int(self._windowmax)

    def setDefaultWindow(self) -> None:
        """
            Set minimum windowing value to minimum scalar value of the image array.
            Set maximum windowing value to maximum scalar value of the image array.
        """
        self._windowmin = self._rangemin
        self._windowmax = self._rangemax
        self.updateVTKLUT()

    def isDefaultWindow(self) -> bool:
        """
            Check whether minimum windowing value = minimum scalar value and
            maximum windowing value = maximum scalar value (no lut windowing)

            return  bool, True if no lut windowing
        """
        return self._windowmin == self._rangemin and \
               self._windowmax == self._rangemax

    def setDefaultLut(self) -> None:
        """
            Set Lut attribute of the current SisypheDisplay instance
            to default (grayscale colormap).
        """
        self._lut.setDefaultLut()

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
            Write current SisypheDisplay instance attributes to xml instance.

            Parameter

                doc             minidom.Document, xml document
                currentnode     minidom.Element, xml root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                display = doc.createElement('display')
                currentnode.appendChild(display)
                # rangemin
                node = doc.createElement('rangemin')
                display.appendChild(node)
                txt = doc.createTextNode(str(self._rangemin))
                node.appendChild(txt)
                # rangemax
                node = doc.createElement('rangemax')
                display.appendChild(node)
                txt = doc.createTextNode(str(self._rangemax))
                node.appendChild(txt)
                # windowmin
                node = doc.createElement('windowmin')
                display.appendChild(node)
                txt = doc.createTextNode(str(self._windowmin))
                node.appendChild(txt)
                # windowmax
                node = doc.createElement('windowmax')
                display.appendChild(node)
                txt = doc.createTextNode(str(self._windowmax))
                node.appendChild(txt)
                # luttype
                node = doc.createElement('luttype')
                display.appendChild(node)
                txt = doc.createTextNode(self.getLUT().getLUTType(True))
                node.appendChild(txt)
                # lutname
                node = doc.createElement('lutname')
                display.appendChild(node)
                txt = doc.createTextNode(self.getLUT().getName())
                node.appendChild(txt)
            else: raise TypeError('parameter functype is not xml.dom.minidom.Element.')
        else: raise TypeError('parameter functype is not xml.dom.minidom.Document.')

    def parseXML(self, doc: minidom.Document) -> None:
        """
            Read current SisypheDisplay instance attributes from xml instance.

            Parameter

                doc             minidom.Document, xml document
        """
        if isinstance(doc, minidom.Document):
            display = doc.getElementsByTagName('display')
            luttype = 'default'
            lutname = 'gray'
            for node in display[0].childNodes:
                if node.nodeName == 'rangemin': self._rangemin = float(node.firstChild.data)
                if node.nodeName == 'rangemax': self._rangemax = float(node.firstChild.data)
                if node.nodeName == 'windowmin': self._windowmin = float(node.firstChild.data)
                if node.nodeName == 'windowmax': self._windowmax = float(node.firstChild.data)
                if node.nodeName == 'luttype': luttype = node.firstChild.data
                if node.nodeName == 'lutname': lutname = node.firstChild.data
            if luttype == 'internal': self._lut.setInternalLut(lutname)
            elif luttype == 'file':
                if dirname(lutname) == '': lutname = join(self._lut.getDefaultLutDirectory(), lutname)
                path, ext = splitext(lutname)
                if ext not in ('.lut', '.txt', self._lut.getFileExt()): ext = self._lut.getFileExt()
                lutname = path + ext
                if exists(lutname):
                    if ext.lower() == '.lut': self._lut.load(lutname)
                    if ext.lower() == '.txt': self._lut.loadFromTxt(lutname)
                    if ext.lower() == self._lut.getFileExt(): self._lut.loadFromXML(lutname)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveToXML(self, filename: str) -> None:
        """
            Save current SisypheDislpay instance attributes to xml file (*.xdisplay).

            Parameter

                filename    str, xml file name (*.xdisplay)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try:
            f.write(buff)
        except IOError:
            raise IOError('XML file write error.')
        finally:
            f.close()

    def loadFromXML(self, filename: str) -> None:
        """
            Load current SisypheDisplay instance attributes from xml file (*.xdisplay).

            Parameter

                filename    str, xml file name (*.xdisplay)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.parseXML(doc)
            else: raise IOError('XML file format is not supported.')
        else: raise IOError('No such file : {}'.format(filename))


class SisypheACPC(object):
    """
        SisypheACPC class

            Class to manage anterior (AC) and posterior (PC) commissure attributes of images.
            Generate rigid geometric transformation, x and z rotations calculated from AC-PC,
            i.e. geometric transformation to reference with axes aligned on the AC-PC line,
            with midACPC point as center of rotation.

        Inheritance

            object -> SisypheACPC

        Private attributes

            _ac     (float, float, float)
            _pc     (float, float, float)
            _trf    SisypheTransform
            _parent object

        Class methods

            getFileExt() -> str
            getFilterExt() -> str

        Public methods

            __init__(parent: Sisyphe.sisypheVolume.SisypheVolume | None = None)
            _str__() -> str
            __repr__() -> str
            getAC() -> tupleFloat3
            getPC() -> tupleFloat3
            getMidACPC() -> tupleFloat3
            setAC(v: tupleFloat3 | listFloat3)
            setPC(v: tupleFloat3 | listFloat3)
            hasAC() -> bool
            hasPC() -> bool
            hasACPC() -> bool
            hasTransform() -> bool
            setTransform(trf: Sisyphe.sisypheTransform.SisypheTransform)
            getTransform() -> Sisyphe.sisypheTransform.SisypheTransform
            getEquivalentVolumeCenteredTransform() -> Sisyphe.sisypheTransform.SisypheTransform
            setYRotation(r: float, deg: bool = False)
            getRotations(deg: bool = False) -> tupleFloat3
            getACPCDistance() -> float
            getEuclideanDistanceFromAC(p: tupleFloat3 | listFloat3) -> float
            getEuclideanDistanceFromPC(p: tupleFloat3 | listFloat3) -> float
            getEuclideanDistanceFromMidACPC(p: tupleFloat3 | listFloat3) -> float
            getRelativeDistanceFromAC(p: tupleFloat3 | listFloat3) -> tupleFloat3
            getRelativeDistanceFromPC(p: tupleFloat3 | listFloat3) -> tupleFloat3
            getRelativeDistanceFromMidACPC(p: tupleFloat3 | listFloat3) -> tupleFloat3
            getRelativeDistanceFromReferencePoint(p: tupleFloat3 | listFloat3,
                                                  ref: tupleFloat3 | listFloat3) -> tupleFloat3
            getPointFromRelativeDistanceToAC(r: tupleFloat3 | listFloat3) -> tupleFloat3
            getPointFromRelativeDistanceToPC(r: tupleFloat3 | listFloat3) -> tupleFloat3
            getPointFromRelativeDistanceToMidACPC(r: tupleFloat3 | listFloat3) -> tupleFloat3
            getPointFromRelativeDistanceToReferencePoint(r: tupleFloat3 | listFloat3,
                                                         ref: tupleFloat3 | listFloat3) -> tupleFloat3
            copyFrom(buff: SisypheACPC | Sisyphe.sisypheVolume.SisypheVolume)
            copy() -> SisypheACPC
            parseXML(doc: minidom.Document)
            createXML(doc: minidom.Document, currentnode: minidom.Element)
            saveToXML(str)
            loadFromXML(str)

        Creation: 12/04/2023
        Revisions:

            24/08/2023  copy() and copyFrom() methods bugfix
            29/08/2023  type hinting
            12/10/2023  add getEquivalentVolumeCenteredTransform2() method
            19/11/2023  docstrings
    """
    __slots__ = ['_ac', '_pc', '_trf', '_parent']

    # Class constant

    _FILEEXT = '.xacpc'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
            Get SisypheACPC file extension.

            return  str, '.xacpc'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
            Get SisypheACPC filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

            return  str, 'PySisyphe ACPC (*.xacpc)'
        """
        return 'PySisyphe ACPC (*{})'.format(cls._FILEEXT)

    # Special methods

    def __init__(self, parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        """
            SisypheACPC instance constructor

            Parameter

                parent      Sisyphe.sisypheVolume.SisypheVolume | None (default None)
        """
        self._ac = (0.0, 0.0, 0.0)
        self._pc = (0.0, 0.0, 0.0)
        self._trf = SisypheTransform()
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(parent, SisypheVolume): self._parent = parent
        else: self._parent = None

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheACPC instance to str
         """
        r = 'ACPC:\n' \
            '\tAC: {ac[0]:.1f} {ac[1]:.1f} {ac[2]:.1f}\n' \
            '\tPC: {pc[0]:.1f} {pc[1]:.1f} {pc[2]:.1f}\n' \
            '\tAC-PC distance (mm): {d:.1f}\n'.format(ac=self._ac, pc=self._pc, d=self.getACPCDistance())
        r += '\tRotations: {rot[0]:.1f} {rot[1]:.1f} {rot[2]:.1f}\n'.format(rot=self._trf.getRotations(deg=True))
        return r

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheACPC instance representation
        """
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    # Private method

    def _updateTransform(self) -> None:
        # Revision 02/04/2023, replace atan by atan2
        if self.hasACPC():
            a = self._ac[1] - self._pc[1]
            o = self._ac[0] - self._pc[0]
            rz = degrees(atan2(o, a))
            o = self._pc[2] - self._ac[2]
            rx = degrees(atan2(o, a))
        else: rx, rz = 0.0, 0.0
        ry = self._trf.getRotations(deg=True)[1]
        self._trf.setRotations((rx, ry, rz), deg=True)
        self._trf.setCenter(self.getMidACPC())

    # Public methods

    def hasParent(self) -> bool:
        """
            Check whether current SisypheACPC instance has a parent,
            i.e. parent attribute is not None.

            return  bool, True if current SisypheACPC is defined (not None)
        """
        return self._parent is not None

    def setParent(self, parent: sc.sisypheVolume.SisypheVolume) -> None:
        """
            Set parent of the current SisypheACPC instance.

            Parameter

                parent  Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(parent, sc.sisypheVolume.SisypheVolume):
            self._parent = parent
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(parent)))

    def getParent(self) -> sc.sisypheVolume.SisypheVolume:
        """
            Get parent of the current SisypheACPC instance.

            return  Sisyphe.sisypheVolume.SisypheVolume
        """
        return self._parent

    def getAC(self) -> tupleFloat3:
        """
            Get AC coordinates attribute of the current SisypheACPC instance.

            return   tupleFloat3, AC coordinates
        """
        return self._ac

    def getPC(self) -> tupleFloat3:
        """
            Get PC coordinates attribute of the current SisypheACPC instance.

            return   tupleFloat3, PC coordinates
        """
        return self._pc

    def getMidACPC(self) -> tupleFloat3:
        """
            Get midACPC coordinates of the current SisypheACPC instance.

            return   tupleFloat3, midACPC coordinates
        """
        if self.hasPC() and not self.hasAC(): return self._pc
        else:
            return (self._ac[0] + (self._pc[0] - self._ac[0]) / 2,
                    self._ac[1] + (self._pc[1] - self._ac[1]) / 2,
                    self._ac[2] + (self._pc[2] - self._ac[2]) / 2)

    def setAC(self, v: tupleFloat3 | listFloat3) -> None:
        """
            Set AC coordinates attribute of the current SisypheACPC instance.

            Parameter

                v   tupleFloat3, AC coordinates
        """
        if isinstance(v, (tuple, list)) and len(v) == 3:
            if all([isinstance(i, (float, int)) for i in v]):
                self._ac = tuple(v)
                self._updateTransform()
            else: raise TypeError('parameter element type of the list/tuple is not int or float.')
        else: raise TypeError('parameter type is not tuple/list of 3 elements.')

    def setPC(self, v: tupleFloat3 | listFloat3) -> None:
        """
            Set PC coordinates attribute of the current SisypheACPC instance.

            Parameter

                v   tupleFloat3, PC coordinates
        """
        if isinstance(v, (tuple, list)) and len(v) == 3:
            if all([isinstance(i, (float, int)) for i in v]):
                self._pc = tuple(v)
                self._updateTransform()
            else: raise TypeError('parameter element type of the list/tuple is not int or float.')
        else: raise TypeError('parameter type is not tuple/list of 3 elements.')

    def hasAC(self) -> bool:
        """
            Check whether AC attribute of the current SisypheACPC instance is defined
            (not coordinates 0.0, 0.0 0.0).

            return  bool, True if AC is defined (not coordinates 0.0, 0.0 0.0)
        """
        return self._ac != (0.0, 0.0, 0.0)

    def hasPC(self) -> bool:
        """
            Check whether PC attribute of the current SisypheACPC instance is defined
            (not coordinates 0.0, 0.0 0.0).

            return  bool, True if AC is defined (not coordinates 0.0, 0.0 0.0)
        """
        return self._pc != (0.0, 0.0, 0.0)

    def hasACPC(self) -> bool:
        """
            Check whether AC and PC attributes of the current SisypheACPC instance is defined
            (not coordinates 0.0, 0.0 0.0).

            return  bool, True if AC is defined (not coordinates 0.0, 0.0 0.0)
        """
        return self._ac != (0.0, 0.0, 0.0) and \
               self._pc != (0.0, 0.0, 0.0)

    def hasTransform(self) -> bool:
        """
            Check whether geometric transformation attribute of the
            current SisypheAPC instance is not identity.

            return  bool, True if geometric transformation is not identity
        """
        return not self._trf.isIdentity()

    def setTransform(self, trf: SisypheTransform) -> None:
        """
            Set geometric transformation attribute of the current SisypheACPC instance.
            Geometric transformation to reference frame with axes aligned on the AC-PC line,
            with midACPC point as center of rotation.

            Parameter

                trf   Sisyphe.sisypheTransform.SisypheTransform, geometric transformation
        """
        if isinstance(trf, SisypheTransform):
            self._trf = trf

    def getTransform(self) -> SisypheTransform:
        """
            Get geometric transformation attribute of the current SisypheACPC instance.
            Geometric transformation to reference frame with axes aligned on the AC-PC line,
            with midACPC point as center of rotation.

            return  Sisyphe.sisypheTransform.SisypheTransform, geometric transformation
        """
        return self._trf

    def getEquivalentVolumeCenteredTransform(self) -> SisypheTransform:
        """
            Get geometric transformation attribute of the current SisypheACPC instance.
            Conversion of the geometric transformation, changing the center of rotation
            from midACPC to the center of the volume.

            1. Apply forward translation, mid CA-CP to volume center (translation = volume center - mid CA-CP)
            2. Apply rotation, after forward translation, center of rotation is volume center
            3. Apply backward translation, volume center to mid CA-CP

            return Sisyphe.sisypheTransform.SisypheTransform, geometric transformation
        """
        if self.hasParent() and self.hasACPC():
            c = list(self._parent.getCenter())
            m = list(self.getMidACPC())
            c[0] -= m[0]
            c[1] -= m[1]
            c[2] -= m[2]
            """
                t1 = forward translation transformation matrix
                forward translation of the center of rotation from mid CA-CP to volume center
                translation = volume center (c) - mid CA-CP (m)
            """
            t1 = SisypheTransform()
            t1.setTranslations(c)
            """
                rt2 = roto-translation matrix = backward translation transformation x rotation transformation
                backward translation from volume center to mid CA-CP
                backward translation = - forward translation
                Order of transformations is 1. rotation -> 2. backward translation
            """
            rt2 = SisypheTransform()
            rt2.setRotations(self._trf.getRotations())
            rt2.setTranslations((-c[0], -c[1], -c[2]))
            """
                final transformation = t1 x rt2
                Order of transformations (inverse of the matrix product order) is
                1. forward translation -> 2. rotation -> 3. backward translation
            """
            t1.preMultiply(rt2, homogeneous=True)
            t1.setID('ACPC')
            if self._parent is not None:
                t1.setCenter(self._parent.getCenter())
                t1.setSize(self._parent.getSize())
                t1.setSpacing(self._parent.getSpacing())
            return t1

    def getEquivalentVolumeCenteredTransform2(self) -> SisypheTransform:
        """
            Get geometric transformation attribute of the current SisypheACPC instance.
            Conversion of the geometric transformation, changing the center of rotation
            from midACPC to the center of the volume.

            Forward centered transform (center of rotation = volume center)
            Widget center of rotation is at the cursor position, not always in the volume center
            1. apply translations to move center of rotation (cursor position -> volume center) before rotation
            2. apply rotations
            It's not classic roto-translation matrix that has an inverse order (1. rotations 2. translations)
            Correct transformation is pre-multiply of the translation matrix by the rotation matrix

            return Sisyphe.sisypheTransform.SisypheTransform, geometric transformation
        """
        t = self.getMidACPC()
        trf = SisypheTransform()
        trf.setID('ACPC')
        if self._parent is not None: trf.setAttributesFromFixedVolume(self._parent)
        trf.setTranslations([-t[0], -t[1], -t[2]])
        trf2 = SisypheTransform()
        trf2.setRotations(self.getRotations(), deg=True)
        trf.preMultiply(trf2, homogeneous=True)
        return trf

    def setYRotation(self, r: float, deg: bool = False) -> None:
        """
            Set rotation around Y axis with update of geometric transformation attribute
            of the current SisypheACPC instance.

            Parameter

                r       float, Y rotation
                deg     bool, degrees if True, radians otherwise
        """
        if isinstance(r, float):
            rot = list(self._trf.getRotations(deg=deg))
            rot[1] = r
            self._trf.setRotations(rot, deg=deg)
        else: raise TypeError('parameter type {} is not float.'.format(type(r)))

    def getRotations(self, deg: bool = False) -> tupleFloat3:
        """
            Get rotation around Y axis with update of geometric transformation attribute
            of the current SisypheACPC instance.

            Parameter

                r       tupleFloat3, rotations around x, y and z axes
                deg     bool, degrees if True, radians otherwise
        """
        return self._trf.getRotations(deg=deg)

    def getACPCDistance(self) -> float:
        """
            Get euclidean distance between AC and PC points.

            return  float, euclidean distance in mm between AC and PC
        """
        if self.hasACPC():
            return sqrt((self._ac[0] - self._pc[0]) ** 2 +
                        (self._ac[1] - self._pc[1]) ** 2 +
                        (self._ac[2] - self._pc[2]) ** 2)
        else: return 0.0

    def getEuclideanDistanceFromAC(self, p: tupleFloat3 | listFloat3) -> float:
        """
            Get euclidean distance between AC and parameter point.

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  float, euclidean distance in mm between AC and p
        """
        if self.hasAC():
            return sqrt((self._ac[0] - p[0]) ** 2 +
                        (self._ac[1] - p[1]) ** 2 +
                        (self._ac[2] - p[2]) ** 2)
        else: return 0.0

    def getEuclideanDistanceFromPC(self, p: tupleFloat3 | listFloat3) -> float:
        """
            Get euclidean distance between PC and parameter point.

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  float, euclidean distance in mm between PC and p
        """
        if self.hasAC():
            return sqrt((self._pc[0] - p[0]) ** 2 +
                        (self._pc[1] - p[1]) ** 2 +
                        (self._pc[2] - p[2]) ** 2)
        else: return 0.0

    def getEuclideanDistanceFromMidACPC(self, p: tupleFloat3 | listFloat3) -> float:
        """
            Get euclidean distance between midACPC and parameter point.

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  float, euclidean distance in mm between midACPC and p
        """
        if self.hasAC():
            p0 = self.getMidACPC()
            return sqrt((p0[0] - p[0]) ** 2 +
                        (p0[1] - p[1]) ** 2 +
                        (p0[2] - p[2]) ** 2)
        else: return 0.0

    def getRelativeDistanceFromAC(self, p: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get relative distance between a point and AC in each axis x (lat), y (ap) and z (h)
            in the geometric reference frame with axes aligned on the AC-PC line.

            Apply inverse transformation to AC -> AC in AC-PC space (AC-PC line aligned to axes in this space)
            Apply inverse transformation to p point -> p point in AC-PC space
            Return relative distance between AC and p point in AC-PC space

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  tupleFloat3, lat, ap and h, relative distance in mm between p and AC
                                 in the reference frame with axes aligned on the AC-PC line
        """
        if self.hasAC():
            p = self._trf.applyInverseToPoint(p)
            ref = self._trf.applyInverseToPoint(self.getAC())
            return p[0] - ref[0], p[1] - ref[1], p[2] - ref[2]
        else: return 0.0, 0.0, 0.0

    def getRelativeDistanceFromPC(self, p: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get relative distance between a point and PC in each axis x (lat), y (ap) and z (h)
            in the geometric reference frame with axes aligned on the AC-PC line.

            Apply inverse transformation to PC -> PC in AC-PC space (AC-PC line aligned to axes in this space)
            Apply inverse transformation to p point -> p point in AC-PC space
            Return relative distance between PC and p point in AC-PC space

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  tupleFloat3, lat, ap and h, relative distance in mm between p and PC
                                 in the reference frame with axes aligned on the AC-PC line
        """
        if self.hasPC():
            p = self._trf.applyInverseToPoint(p)
            ref = self._trf.applyInverseToPoint(self.getPC())
            return p[0] - ref[0], p[1] - ref[1], p[2] - ref[2]
        else: return 0.0, 0.0, 0.0

    def getRelativeDistanceFromMidACPC(self, p: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get relative distance between a point and midACPC in each axis x (lat), y (ap) and z (h)
            in the geometric reference frame with axes aligned on the AC-PC line.

            Apply inverse transformation to p point -> p point in AC-PC space
            Mid AC-PC is already in AC-PC space (Mid AC-PC is the center of rotation, invariant to transformation)
            Return relative distance between mid AC-PC and p point in AC-PC space

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates

            return  tupleFloat3, lat, ap and h, relative distance in mm between p and midACPC
                                 in the reference frame with axes aligned on the AC-PC line
        """
        if self.hasACPC():
            p = self._trf.applyInverseToPoint(p)
            ref = self.getMidACPC()
            return p[0] - ref[0], p[1] - ref[1], p[2] - ref[2]
        else: return 0.0, 0.0, 0.0

    def getRelativeDistanceFromReferencePoint(self,
                                              p: tupleFloat3 | listFloat3,
                                              ref: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get relative distance between a point and a second reference point
            in each axis x (lat), y (ap) and z (h) in the geometric reference
            frame with axes aligned on the AC-PC line.

            Apply inverse transformation to ref point -> ref point in AC-PC space (AC-PC line aligned to axes in this space)
            Apply inverse transformation to p point -> p point in AC-PC space
            Return relative distance between ref point and p point in AC-PC space

            Parameter

                p   tupleFloat3 | listFloat3, point coordinates
                ref tupleFloat3 | listFloat3, reference point coordinates

            return  tupleFloat3, lat, ap and h, relative distance in mm between p and ref
                                 in the reference frame with axes aligned on the AC-PC line
        """
        if self.hasACPC():
            p = self._trf.applyInverseToPoint(p)
            ref = self._trf.applyInverseToPoint(ref)
            return p[0] - ref[0], p[1] - ref[1], p[2] - ref[2]
        else: return 0.0, 0.0, 0.0

    def getPointFromRelativeDistanceToAC(self, r: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get coordinates of a point giving relative distances from AC point
            in each axis x (lat), y (ap) and z (h), in the geometric reference
            frame with axes aligned on the AC-PC line.

            Apply inverse transformation to AC -> AC in AC-PC space (AC-PC line aligned to axes in this space)
            New point = add relative distances r to AC in AC-PC space
            Apply transformation to new point -> new point in native space

            Parameter

                r   tupleFloat3 | listFloat3, relative distances in each axis x (lat), y (ap) and z (h)

            return  tupleFloat3, point coordinates
        """
        if self.hasACPC():
            p = list(self._trf.applyInverseToPoint(self.getAC()))
            p[0] += r[0]  # lat
            p[1] += r[1]  # ap
            p[2] += r[2]  # h
            return self._trf.applyToPoint(p)
        else: return 0.0, 0.0, 0.0

    def getPointFromRelativeDistanceToPC(self, r: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get coordinates of a point giving relative distances from PC point
            in each axis x (lat), y (ap) and z (h), in the geometric reference
            frame with axes aligned on the AC-PC line.

            Apply inverse transformation to PC -> PC in AC-PC space (AC-PC line aligned to axes in this space)
            New point = add relative distances r to PC in AC-PC space
            Apply transformation to new point -> new point in native space

            Parameter

                r   tupleFloat3 | listFloat3, relative distances in each axis x (lat), y (ap) and z (h)

            return  tupleFloat3, point coordinates
        """
        if self.hasACPC():
            p = list(self._trf.applyInverseToPoint(self.getPC()))
            p[0] += r[0]  # lat
            p[1] += r[1]  # ap
            p[2] += r[2]  # h
            return self._trf.applyToPoint(p)
        else: return 0.0, 0.0, 0.0

    def getPointFromRelativeDistanceToMidACPC(self, r: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get coordinates of a point giving relative distances from midACPC point
            in each axis x (lat), y (ap) and z (h), in the geometric reference
            frame with axes aligned on the AC-PC line.

            midACPC is already in AC-PC space (midACPC is the center of rotation, invariant to transformation)
            New point = add relative distances r to midACPC
            Apply transformation to new point -> new point in native space

            Parameter

                r   tupleFloat3 | listFloat3, relative distances in each axis x (lat), y (ap) and z (h)

            return  tupleFloat3, point coordinates
        """
        if self.hasACPC():
            p = list(self.getMidACPC())
            p[0] += r[0]  # lat
            p[1] += r[1]  # ap
            p[2] += r[2]  # h
            return self._trf.applyToPoint(p)
        else: return 0.0, 0.0, 0.0

    def getPointFromRelativeDistanceToReferencePoint(self,
                                                     r: tupleFloat3 | listFloat3,
                                                     ref: tupleFloat3 | listFloat3) -> tupleFloat3:
        """
            Get coordinates of a point giving relative distances from a second
            reference point in each axis x (lat), y (ap) and z (h), in the geometric
            reference frame with axes aligned on the AC-PC line.

            Apply inverse transformation to ref point -> ref point in AC-PC space (AC-PC line aligned to axes)
            New point = add relative distances r to ref point in AC-PC space
            Apply transformation to new point -> new point in native space

            Parameter

                r   tupleFloat3 | listFloat3, relative distances in each axis x (lat), y (ap) and z (h)
                ref tupleFloat3 | listFloat3, reference point coordinates

            return  tupleFloat3, point coordinates
        """
        if self.hasACPC():
            p = list(self._trf.applyInverseToPoint(ref))
            p[0] += r[0]  # lat
            p[1] += r[1]  # ap
            p[2] += r[2]  # h
            return self._trf.applyToPoint(p)
        else: return 0.0, 0.0, 0.0

    def copyFrom(self, buff: SisypheACPC | sc.sisypheVolume.SisypheVolume) -> None:
        """
            Copy attributes of the ACPC parameter to
            the current SisypheACPC instance (deep copy).

            Parameter

                buff    SisypheACPC | Sisyphe.sisypheVolume.SisypheVolume
        """
        if isinstance(buff, sc.sisypheVolume.SisypheVolume):
            buff = buff.acpc
        if isinstance(buff, SisypheACPC):
            self._ac = buff._ac
            self._pc = buff._pc
            self._trf = buff._trf.copy()
        else: raise TypeError('parameter type {} is not {} or SisypheVolume.'.format(type(buff), self.__class__.__name__))

    def copy(self) -> SisypheACPC:
        """
            Copy the current SisypheACPC instance (deep copy).

            return   SisypheACPC
        """
        buff = SisypheACPC()
        buff._ac = self._ac
        buff._pc = self._pc
        buff._trf = self._trf.copy()
        return buff

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
            Write current SisypheACPC instance attributes to xml instance.

            Parameter

                doc             minidom.Document, xml document
                currentnode     minidom.Element, xml root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                item = doc.createElement('ACPC')
                currentnode.appendChild(item)
                # AC
                node = doc.createElement('AC')
                item.appendChild(node)
                ac = '{} {} {}'.format(self._ac[0], self._ac[1], self._ac[2])
                txt = doc.createTextNode(ac)
                node.appendChild(txt)
                # PC
                node = doc.createElement('PC')
                item.appendChild(node)
                pc = '{} {} {}'.format(self._pc[0], self._pc[1], self._pc[2])
                txt = doc.createTextNode(pc)
                node.appendChild(txt)
                # Rotation
                node = doc.createElement('Rotation')
                item.appendChild(node)
                r = str(self._trf.getRotations(deg=True)[1])
                txt = doc.createTextNode(r)
                node.appendChild(txt)
            else: raise TypeError('parameter functype is not xml.dom.minidom.Element.')
        else: raise TypeError('parameter functype is not xml.dom.minidom.Document.')

    def parseXML(self, doc: minidom.Document) -> None:
        """
            Read current SisypheACPC instance attributes from xml instance.

            Parameter

                doc             minidom.Document, xml document
        """
        if isinstance(doc, minidom.Document):
            item = doc.getElementsByTagName('ACPC')
            if len(item) > 0:
                for node in item[0].childNodes:
                    # AC
                    if node.nodeName == 'AC':
                        r = node.firstChild.data.split(' ')
                        self._ac = (float(r[0]), float(r[1]), float(r[2]))
                    # PC
                    elif node.nodeName == 'PC':
                        r = node.firstChild.data.split(' ')
                        self._pc = (float(r[0]), float(r[1]), float(r[2]))
                    # Rotation
                    elif node.nodeName == 'Rotation':
                        if node.firstChild.data is not None: r = float(node.firstChild.data)
                        else: r = 0.0
                        self.setYRotation(r, deg=True)
                        self._updateTransform()
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveToXML(self, filename: str) -> None:
        """
            Save current SisypheACPC instance attributes to xml file (*.xacpc).

            Parameter

                filename    str, xml file name (*.xacpc)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()

    def loadFromXML(self, filename: str) -> None:
        """
            Load current SisypheACPC instance attributes from xml file (*.xacpc).

            Parameter

                filename    str, xml file name (*.xacpc)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.parseXML(doc)
            else: raise IOError('XML file format is not supported.')
        else: raise IOError('No such file : {}'.format(filename))

