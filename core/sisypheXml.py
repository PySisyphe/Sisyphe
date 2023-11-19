"""
    No external package or module
"""

from os.path import exists
from os.path import splitext
from os.path import basename

from datetime import date
from datetime import datetime

from xml.dom import minidom
from xml.dom.minicompat import NodeList

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI

__all__ = ['AbstractXml',
           'XmlVolume',
           'XmlROI']

"""
    Class hierarchy

        object -> AbstractXml -> XmlVolume
                              -> XmlROI  
"""


class AbstractXml(object):
    """
        AbstractXml

        Inheritance

            object -> AbstractXml

        Private attributes

            _doc        minidom.Document
            _filename   str

        Public methods

            __getitem__(str)
            __contain__(str)
            bool = hasField(str)
            NodeList = getFieldNodes(str)
            str | list[str] = getFieldValues(str)

            inherited object methods

        Creation: 08/09/2022
        Revisions:

            29/08/2023  getFieldList() method bugfix
                        type hinting
    """
    __slots__ = ['_doc', '_filename']

    # Special methods

    def __init__(self, filename: str) -> None:
        super().__init__()

        if exists(filename):
            self._filename = filename
            # self._doc = minidom.parse(filename)
            with open(filename, 'rb') as f:
                line = ''
                strdoc = ''
                while line != '</xvol>\n':
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
            self._doc = minidom.parseString(strdoc)
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def __repr__(self) -> str:
        return 'AbstractXml instance at <{}>\n'.format(str(id(self)))

    def __getitem__(self, keyword: str) -> str | list[str]:
        if isinstance(keyword, str): return self.getFieldValues(keyword)
        else: raise TypeError('key type {} is not str.'.format(type(keyword)))

    def __contains__(self, keyword: str) -> bool:
        if isinstance(keyword, str): return self.hasField(keyword)
        else: raise TypeError('key type {} is not str.'.format(type(keyword)))

    def __str__(self) -> str:
        r = list()
        node = self._doc.documentElement.firstChild
        while node:
            child = node.firstChild
            first = True
            while child:
                child2 = child.firstChild
                while child2:
                    if child2.nodeType == minidom.Node.TEXT_NODE:
                        if child2.parentNode:
                            if child2.parentNode.nodeType == minidom.Node.ELEMENT_NODE:
                                if child2.nodeValue.isprintable():
                                    r.append('\t{}: '.format(child2.parentNode.nodeName))
                                    r.append(child2.nodeValue)
                                    r.append('\n')
                    child2 = child2.nextSibling
                if child.nodeType == minidom.Node.TEXT_NODE:
                    if child.parentNode:
                        if child.parentNode.nodeType == minidom.Node.ELEMENT_NODE:
                            if first:
                                first = False
                                r.append('{}: '.format(child.parentNode.nodeName))
                                if child.nodeValue.isprintable(): r.append(child.nodeValue)
                                r.append('\n')
                child = child.nextSibling
            node = node.nextSibling
        return ''.join(r)

    # Public methods

    def getFieldList(self) -> list[str]:
        r = list()
        node = self._doc.documentElement.firstChild
        while node:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                nochild = True
                child = node.firstChild
                while child:
                    if child.nodeType == minidom.Node.ELEMENT_NODE:
                        child2 = child.firstChild
                        if child2 is not None and child2.nodeType == minidom.Node.TEXT_NODE and child2.nodeValue != '':
                            r.append(child.nodeName)
                            nochild = False
                    child = child.nextSibling
                if nochild: r.append(node.nodeName)
            node = node.nextSibling
        return r

    def hasField(self, field: str) -> bool:
        nodes = self._doc.getElementsByTagName(field)
        return nodes.length > 0

    def getFieldNodes(self, field: str) -> NodeList:
        nodes = self._doc.getElementsByTagName(field)
        return nodes

    def getFieldValues(self, field: str) -> str | list[str]:
        nodes = self.getFieldNodes(field)
        if nodes.length > 0:
            for node in nodes:
                if node.hasChildNodes():
                    child = node.firstChild
                    return child.data


class XmlVolume(AbstractXml):
    """
        XmlVolume

        Inheritance

            object -> AbstractXml -> XmlVolume

        Private attributes

        Public methods

            str = getID()
            int, int, int = getSize()
            int = getComponents()
            float, float, float = getSpacing()
            float, float, float = getOrigin()
            str = getOrientation()
            str = getDatatype()
            float * 6 = getDirections()
            float = getSlope()
            float = getIntercept()
            str = getLastname()
            str = getFirstname()
            str = getDateOfBirthdayAsString()
            date = getDateOfBirthdayAsDate()
            str = getGender()
            str = getModality()
            str = getSequence()
            str = getFrame()
            str = getUnit()
            str = getDateOfScanAsString()
            date = getDateOfScanAsDate()
            float = getRangeMin()
            float = getRangeMax()
            float = getWindowMin()
            float = getWindowMax()

            inherited object methods
            inherited AbstractXml methods

        Creation: 08/09/2022
        Revisions:

            29/08/2023  getFrame() method, return int and not str
                        type hinting
    """

    # Special methods

    def __init__(self, filename: str) -> None:
        if splitext(filename)[1] == SisypheVolume.getFileExt():
            super().__init__(filename)
        else: raise IOError('{} is not a SisypheVolume file.'.format(basename(filename)))

    def __repr__(self) -> str:
        return 'XmlVolume instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def getID(self) -> str:
        return self.getFieldValues('ID')

    def getSize(self) -> list[int]:
        r = self.getFieldValues('size').split(' ')
        return [int(v) for v in r]

    def getComponents(self) -> int:
        return int(self.getFieldValues('components'))

    def getSpacing(self) -> list[float]:
        r = self.getFieldValues('spacing').split(' ')
        return [float(v) for v in r]

    def getFOV(self) -> list[float]:
        spacing = self.getSpacing()
        size = self.getSize()
        return [spacing[i] * size[i] for i in range(3)]

    def getOrigin(self) -> list[float]:
        r = self.getFieldValues('origin').split(' ')
        return [float(v) for v in r]

    def getOrientation(self) -> str:
        return self.getFieldValues('orientation')

    def getDatatype(self) -> str:
        return self.getFieldValues('datatype')

    def getDirections(self) -> list[float]:
        r = self.getFieldValues('directions').split(' ')
        return [float(v) for v in r]

    def getSlope(self) -> float:
        return float(self.getFieldValues('slope'))

    def getIntercept(self) -> float:
        return float(self.getFieldValues('intercept'))

    def getLastname(self) -> str:
        return self.getFieldValues('lastname')

    def getFirstname(self) -> str:
        return self.getFieldValues('firstname')

    def getDateOfBirthdayAsString(self) -> str:
        return self.getFieldValues('dateofbirthday')

    def getDateOfBirthdayAsDate(self) -> date:
        d = self.getDateOfBirthdayAsString()
        return datetime.strptime(d, '%Y-%m-%d').date()

    def getGender(self) -> str:
        return self.getFieldValues('gender')

    def getModality(self) -> str:
        return self.getFieldValues('modality')

    def getSequence(self) -> str:
        return self.getFieldValues('sequence')

    def getFrame(self) -> int:
        return int(self.getFieldValues('frame'))

    def getUnit(self) -> str:
        return self.getFieldValues('unit')

    def getDateOfScanAsString(self) -> str:
        return self.getFieldValues('dateofscan')

    def getDateOfScanAsDate(self) -> date:
        d = self.getDateOfScanAsString()
        return datetime.strptime(d, '%Y-%m-%d').date()

    def getRangeMin(self) -> float:
        return float(self.getFieldValues('rangemin'))

    def getRangeMax(self) -> float:
        return float(self.getFieldValues('rangemax'))

    def getRange(self) -> tuple[float, float]:
        return self.getRangeMin(), self.getRangeMax()

    def getWindowMin(self) -> float:
        return float(self.getFieldValues('windowmin'))

    def getWindowMax(self) -> float:
        return float(self.getFieldValues('windowmax'))

    def getWindow(self) -> tuple[float, float]:
        return self.getWindowMin(), self.getWindowMax()

    def getRawName(self) -> str:
        return self.getFieldValues('array')


class XmlROI(AbstractXml):
    """
        XmlROI

        Inheritance

            object -> AbstractXml -> XmlROI

        Private attributes

        Public methods

            str = getID()
            str = getName()
            float, float, float = getColor()
            float = getAlpha()
            int, int, int = getSize()
            float, float, float = getSpacing()

            inherited object methods
            inherited AbstractXml methods

        Creation: 08/09/2022
        Revisions:

            29/08/2023  type hinting
    """

    # Special methods

    def __init__(self, filename: str) -> None:
        if splitext(filename)[1] == SisypheROI.getFileExt():
            super().__init__(filename)
        else: raise IOError('{} is not a SisypheROI file.'.format(basename(filename)))

    def __repr__(self) -> str:
        return 'XmlROI instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def getID(self) -> str:
        return self.getFieldValues('referenceID')

    def getName(self) -> str:
        return self.getFieldValues('name')

    def getColor(self) -> list[int, int, int]:
        r = self.getFloatColor()
        return [int(v * 255) for v in r]

    def getFloatColor(self) -> list[float, float, float]:
        r = self.getFieldValues('color').split(' ')
        return [float(v) for v in r]

    def getAlpha(self) -> int:
        return int(self.getFloatAlpha() * 255)

    def getFloatAlpha(self) -> float:
        return float(self.getFieldValues('alpha'))

    def getSize(self) -> list[float, float, float]:
        r = self.getFieldValues('size').split(' ')
        return [int(v) for v in r]

    def getSpacing(self) -> list[float, float, float]:
        r = self.getFieldValues('spacing').split(' ')
        return [float(v) for v in r]

    def getFOV(self) -> list[float, float, float]:
        spacing = self.getSpacing()
        size = self.getSize()
        return [spacing[i] * size[i] for i in range(3)]
