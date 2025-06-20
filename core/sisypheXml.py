"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - Numpy, scientific computing, https://numpy.org/
"""

from os.path import exists
from os.path import splitext
from os.path import basename

from datetime import date
from datetime import datetime

from xml.dom import minidom
from xml.dom.minicompat import NodeList

from PyQt5.QtGui import QColor

from numpy import array
from numpy import ndarray

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTracts import SisypheStreamlines

__all__ = ['AbstractXml',
           'XmlVolume',
           'XmlROI',
           'XmlStreamlines']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> AbstractXml
             -> AbstractXml -> XmlVolume
                            -> XmlROI
                            -> XmlStreamlines
"""

class AbstractXml(object):
    """
    Description
    ~~~~~~~~~~~

    Abstract ancestor class of XmlVolume, XmlRoi and XmlStreamlines classes. These classes provide direct access to
    the xml fields in PySisyphe Volume (.xvol), Roi (.xroi) and Streamlines (.xtracts) files.

    Inheritance
    ~~~~~~~~~~~

    object -> AbstractXml

    Creation: 08/09/2022
    Last revision: 16/12/2023
    """
    __slots__ = ['_doc', '_filename']

    # Class method

    @classmethod
    def getXmlEnd(cls) -> str:
        raise NotImplemented

    # Special methods

    """
    Private attributes

    _doc        minidom.Document
    _filename   str
    """

    def __init__(self, filename: str) -> None:
        """
        AbstractXml instance constructor.

        Parameters
        ----------
        filename : str
            xml file name to load
        """
        super().__init__()
        if exists(filename):
            self._filename = filename
            # self._doc = minidom.parse(filename)
            with open(filename, 'rb') as f:
                line = ''
                strdoc = ''
                end = self.getXmlEnd()
                while line != end:
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
            self._doc = minidom.parseString(strdoc)
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            AbstractXml instance representation
        """
        return 'AbstractXml instance at <{}>\n'.format(str(id(self)))

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of  AbstractXml instance to str
         """
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

    def __getitem__(self, keyword: str) -> str | list[str]:
        """
        Special overloaded container getter method. Get field value(s) in the current AbstractXml instance.

        Parameters
        ----------
        keyword : str
            field name

        Returns
        -------
        str | list[str]
            field value(s)
        """
        if isinstance(keyword, str): return self.getFieldValues(keyword)
        else: raise TypeError('key type {} is not str.'.format(type(keyword)))

    def __contains__(self, keyword: str) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a field is in
        the current AbstractXml instance.

        Parameters
        ----------
        keyword : str
            field name

        Returns
        -------
        bool
            True if keyword is defined
        """
        if isinstance(keyword, str): return self.hasField(keyword)
        else: raise TypeError('key type {} is not str.'.format(type(keyword)))

    # Public methods

    def getFieldList(self) -> list[str]:
        """
        Get field list in the current AbstractXml instance.

        Returns
        -------
        list[str]
            list of field names
        """
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
        """
        Check whether a field is in the current AbstractXml instance.

        Parameters
        ----------
        field : str
            field name

        Returns
        -------
        bool
            True if field is defined
        """
        nodes = self._doc.getElementsByTagName(field)
        return nodes.length > 0

    def getFieldNodes(self, field: str) -> NodeList:
        """
        Get field nodes in the current AbstractXml instance.

        Parameters
        ----------
        field : str
            field name

        Returns
        -------
        xml.dom.minicompat.NodeList
            list of nodes
        """
        nodes = self._doc.getElementsByTagName(field)
        return nodes

    def getFieldValues(self, field: str) -> str | list[str] | None:
        """
        Get field value(s) in the current AbstractXml instance.

        Parameters
        ----------
        field : str
            field name

        Returns
        -------
        str | list[str]
            field value(s)
        """
        nodes = self.getFieldNodes(field)
        if nodes.length > 0:
            for node in nodes:
                if node.hasChildNodes():
                    child = node.firstChild
                    return child.data
        return None


class XmlVolume(AbstractXml):
    """
    Description
    ~~~~~~~~~~~

    Class for accessing the xml fields of the PySisyphe volume (.xvol).

    Inheritance
    ~~~~~~~~~~~

    object -> AbstractXml -> XmlVolume

    Creation: 08/09/2022
    Last revision: 16/12/2023
    """

    # Class method

    @classmethod
    def getXmlEnd(cls) -> str:
        return '</xvol>\n'

    # Special methods

    def __init__(self, filename: str) -> None:
        """
        XmlVolume instance constructor.

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name to load (.xvol)
        """
        if splitext(filename)[1] == SisypheVolume.getFileExt():
            super().__init__(filename)
        else: raise IOError('{} is not a SisypheVolume file.'.format(basename(filename)))

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            XmlVolume instance representation
        """
        return 'XmlVolume instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def getID(self) -> str:
        """
        Get ID attribute of the current XmlVolume instance.

        Returns
        -------
        str
            Volume ID (space ID)
        """
        return self.getFieldValues('ID')

    def getSize(self) -> list[int]:
        """
        Get image size attribute of the current XmlVolume instance.

        Returns
        -------
        list[int]
            volume size in x, y and z axes
        """
        r = self.getFieldValues('size').split(' ')
        return [int(v) for v in r]

    def getComponents(self) -> int:
        """
        Get number of components attribute of the current XmlVolume instance.

        Returns
        -------
        int
            number of components (1 for 3D volume, > 1 for 4D multi-components volume)
        """
        return int(self.getFieldValues('components'))

    getNumberOfComponentsPerPixel = getComponents

    def getSpacing(self) -> list[float]:
        """
        Get image spacing (i.e. voxel size in each dimension) attribute of the current XmlVolume instance.

        Returns
        -------
        list[float]
            volume spacing in x, y and z axes
        """
        r = self.getFieldValues('spacing').split(' ')
        return [float(v) for v in r]

    def getFOV(self) -> list[float]:
        """
        Get field of view attribute of the current XmlVolume instance.

        Returns
        -------
        list[float]
            volume FOV in x, y and z axes
        """
        spacing = self.getSpacing()
        size = self.getSize()
        return [spacing[i] * size[i] for i in range(3)]

    def getOrigin(self) -> list[float]:
        """
        Get origin coordinates (world reference) attribute of the current XmlVolume instance.

        Returns
        -------
        list[float]
            origin coordinates of the volume
        """
        r = self.getFieldValues('origin').split(' ')
        return [float(v) for v in r]

    def getOrientation(self) -> str:
        """
        Get orientation attribute of the current XmlVolume instance.

        Returns
        -------
        str
            'axial', 'coronal', 'sagittal'
        """
        return self.getFieldValues('orientation')

    def getDatatype(self) -> str:
        """
        Get datatype attribute of the current XmlVolume instance.

        Returns
        -------
        str
            numpy datatype format
        """
        return self.getFieldValues('datatype')

    def getDirections(self) -> list[float]:
        """
        Get directions attribute of the current XmlVolume instance.
        Direction vectors of image axes in RAS+ coordinates system.

        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats

            - First vector, x-axis image direction, [1.0, 0.0, 0.0]
            - Second vector, y-axis image direction, [0.0, 1.0, 0.0]
            - Third vector, z-axis image direction, [0.0, 0.0, 1.0]

        Returns
        -------
        list[float]
            volume directions
        """
        r = self.getFieldValues('directions').split(' ')
        return [float(v) for v in r]

    def getSlope(self) -> float:
        """
        Get slope attribute of the current XmlVolume instance. Used for linear transformation of scalar values
        displayed in the PySisyphe interface. displayed value = slope x scalar value + intercept

        Returns
        -------
        float
            slope attribute
        """
        return float(self.getFieldValues('slope'))

    def getIntercept(self) -> float:
        """
        Get intercept attribute of the current XmlVolume instance. Used for linear transformation of scalar values
        displayed in the PySisyphe interface. displayed value = slope x scalar value + intercept

        Returns
        -------
        float
            intercept attribute
        """
        return float(self.getFieldValues('intercept'))

    def getLastname(self) -> str:
        """
        Get patient lastname attribute of the current XmlVolume instance.

        Returns
        -------
        str
            patient lastname
        """
        return self.getFieldValues('lastname')

    def getFirstname(self) -> str:
        """
        Get patient firstname of the current XmlVolume instance.

        Returns
        -------
        str
            patient firstname
        """
        return self.getFieldValues('firstname')

    def getDateOfBirthdayAsString(self) -> str:
        """
        Get patient's date of birth attribute of the current XmlVolume instance.

        Returns
        -------
        str
            patient's birthdate
        """
        return self.getFieldValues('dateofbirthday')

    def getDateOfBirthdayAsDate(self) -> date:
        """
        Get patient's date of birth attribute of the current XmlVolume instance.

        Returns
        -------
        datetime.date
            patient's birthdate
        """
        d = self.getDateOfBirthdayAsString()
        return datetime.strptime(d, '%Y-%m-%d').date()

    def getGender(self) -> str:
        """
        Get patient gender attribute of the current XmlVolume instance.

        Returns
        -------
        str
            patient gender ('Male', 'Female', 'Unknown')
        """
        return self.getFieldValues('gender')

    def getModality(self) -> str:
        """
        Get modality attribute of the current XmlVolume instance.

        Returns
        -------
        str
            modality
        """
        return self.getFieldValues('modality')

    def getSequence(self) -> str:
        """
        Get sequence attribute of the current XmlVolume instance.

        Returns
        -------
        str
            sequence
        """
        return self.getFieldValues('sequence')

    def getFrame(self) -> int:
        """
        Get frame attribute of the current XmlVolume instance.

        Returns
        -------
        str
            frame ('UNKNOWN', 'NO FRAME', 'LEKSELL')
        """
        return int(self.getFieldValues('frame'))

    def getUnit(self) -> str:
        """
        Get unit attribute of the current XmlVolume instance.

        Returns
        -------
        str
            unit
        """
        return self.getFieldValues('unit')

    def getDateOfScanAsString(self) -> str:
        """
        Get date of scan attribute of the current XmlVolume instance.

        Returns
        -------
        str
            date of scan
        """
        return self.getFieldValues('dateofscan')

    def getDateOfScanAsDate(self) -> date:
        """
        Get date of scan attribute of the current XmlVolume instance.

        Returns
        -------
        datetime.date
            date of scan
        """
        d = self.getDateOfScanAsString()
        return datetime.strptime(d, '%Y-%m-%d').date()

    def getRangeMin(self) -> float:
        """
        Get minimum scalar value in the image array of the current XmlVolume instance.

        Returns
        -------
        float
            minimum scalar value in the image array
        """
        return float(self.getFieldValues('rangemin'))

    def getRangeMax(self) -> float:
        """
        Get maximum scalar value in the image array of the current XmlVolume instance.

        Returns
        -------
        float
            maximum scalar value in the image array
        """
        return float(self.getFieldValues('rangemax'))

    def getRange(self) -> tuple[float, float]:
        """
        Get minimum and maximum scalar values in the image array of the current XmlVolume instance.

        Returns
        -------
        tuple[float, float]
            minimum and maximum scalar values in the image array
        """
        return self.getRangeMin(), self.getRangeMax()

    def getWindowMin(self) -> float:
        """
        Get minimum windowing value of the current XmlVolume instance.

        Returns
        -------
        float
            minimum windowing value
        """
        return float(self.getFieldValues('windowmin'))

    def getWindowMax(self) -> float:
        """
        Get maximum windowing value of the current XmlVolume instance.

        Returns
        -------
        float
            maximum windowing value
        """
        return float(self.getFieldValues('windowmax'))

    def getWindow(self) -> tuple[float, float]:
        """
        Get minimum and maximum windowing values of the current XmlVolume instance.

        Returns
        -------
        tuple[float, float]
            minimum and maximum windowing values
        """
        return self.getWindowMin(), self.getWindowMax()

    def getRawName(self) -> str:
        """
        Get array field value of the current XmlVolume instance.

        Returns
        -------
        str
            'self' if array image is saved in a binary part of the xvol file (single format) or file name with raw
            extension if image array is saved in a separate file
        """
        return self.getFieldValues('array')


class XmlROI(AbstractXml):
    """
    Description
    ~~~~~~~~~~~

    Class for accessing the xml fields of the PySisyphe ROI (.xroi).

    Inheritance
    ~~~~~~~~~~~

    object -> AbstractXml -> XmlROI

    Creation: 08/09/2022
    Last revision: 16/12/2023
    """

    # Class method

    @classmethod
    def getXmlEnd(cls) -> str:
        return '</xroi>\n'

    # Special methods

    def __init__(self, filename: str) -> None:
        """
        XmlROI instance constructor

        Parameters
        ----------
        filename : str
            PySisyphe Roi file name to load (.xroi)
        """
        if splitext(filename)[1] == SisypheROI.getFileExt():
            super().__init__(filename)
        else: raise IOError('{} is not a SisypheROI file.'.format(basename(filename)))

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            XmlROI instance representation
        """
        return 'XmlROI instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def getID(self) -> str:
        """
        Get reference ID attribute of the current XmlROI instance.

        Returns
        -------
        str
            Roi ID
        """
        return self.getFieldValues('referenceID')

    def getName(self) -> str:
        """
        Get name attribute of the current XmlROI instance.

        Returns
        -------
        str
            Roi name
        """
        return self.getFieldValues('name')

    def getColor(self) -> list[int]:
        """
        Get int format color attribute of the current XmlROI instance.

        Returns
        -------
        list[int]
            Roi color, red, green, blue components between 0 and 255
        """
        r = self.getFloatColor()
        return [int(v * 255) for v in r]

    def getFloatColor(self) -> list[float]:
        """
        Get float format color attribute of the current XmlROI instance.

        Returns
        -------
        list[float]
            Roi color, red, green, blue components between 0.0 and 1.0
        """
        r = self.getFieldValues('color').split(' ')
        return [float(v) for v in r]

    def getQColor(self) -> QColor:
        """
        Get QColor attribute of the current XmlROI instance.

        Returns
        -------
        PyQt5.QtGui.QColor
            Roi color
        """
        buff = self.getFloatColor()
        alpha = self.getFloatAlpha()
        r = QColor()
        r.setRgbF(buff[0], buff[1], buff[2], alpha)
        return r

    def getAlpha(self) -> int:
        """
        Get int format opacity attribute of the current XmlROI instance.

        Returns
        -------
        int
            Roi opacity, between 0 and 255
        """
        return int(self.getFloatAlpha() * 255)

    def getFloatAlpha(self) -> float:
        """
        Get float format opacity attribute of the current XmlROI instance.

        Returns
        -------
        float
            Roi opacity between 0.0 and 1.0
        """
        return float(self.getFieldValues('alpha'))

    def getSize(self) -> list[int]:
        """
        Get image size attribute of the current XmlROI instance.

        Returns
        -------
        list[int]
            Roi size in x, y and z axes
        """
        r = self.getFieldValues('size').split(' ')
        return [int(v) for v in r]

    def getSpacing(self) -> list[float]:
        """
        Get image spacing (i.e. voxel size in each dimension) attribute of the current XmlROI instance.

        Returns
        -------
        list[float]
            Roi spacing in x, y and z axes
        """
        r = self.getFieldValues('spacing').split(' ')
        return [float(v) for v in r]

    def getFOV(self) -> list[float]:
        """
        Get field of view attribute of the current XmlROI instance.

        Returns
        -------
        list[float]
            Roi FOV in x, y and z axes
        """
        spacing = self.getSpacing()
        size = self.getSize()
        return [spacing[i] * size[i] for i in range(3)]


class XmlStreamlines(AbstractXml):
    """
    Description
    ~~~~~~~~~~~

    Class for accessing the xml fields of the PySisyphe Streamlines (.xtracts).

    Inheritance
    ~~~~~~~~~~~

    object -> AbstractXml -> XmlStreamlines

    Creation: 29/08/2024
    """

    # Class method

    @classmethod
    def getXmlEnd(cls) -> str:
        return '</xtracts>\n'

    # Special methods

    def __init__(self, filename: str) -> None:
        """
        XmlStreamlines instance constructor

        Parameters
        ----------
        filename : str
            PySisyphe Roi file name to load (.xtracts)
        """
        if splitext(filename)[1] == SisypheStreamlines.getFileExt():
            super().__init__(filename)
        else: raise IOError('{} is not a SisypheStreamlines file.'.format(basename(filename)))

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            XmlStreamlines instance representation
        """
        return 'XmlStreamlines instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def getID(self) -> str:
        """
        Get reference ID attribute of the current XmlStreamlines instance.

        Returns
        -------
        str
            Streamlines ID
        """
        return self.getFieldValues('id')

    def getName(self) -> str:
        """
        Get name attribute of the current XmlStreamlines instance.

        Returns
        -------
        str
            Streamlines name
        """
        return self.getFieldValues('name')

    def getColor(self) -> list[int]:
        """
        Get int format color attribute of the current XmlStreamlines instance.

        Returns
        -------
        list[int]
            Streamlines color, red, green, blue components between 0 and 255
        """
        r = self.getFloatColor()
        return [int(v * 255) for v in r]

    def getFloatColor(self) -> list[float]:
        """
        Get float format color attribute of the current XmlStreamlines instance.

        Returns
        -------
        list[float]
            Streamlines color, red, green, blue components between 0.0 and 1.0
        """
        r = self.getFieldValues('color').split(' ')
        return [float(v) for v in r]

    def getQColor(self) -> QColor:
        """
        Get QColor attribute of the current XmlStreamlines instance.

        Returns
        -------
        PyQt5.QtGui.QColor
            Streamlines color
        """
        buff = self.getFloatColor()
        alpha = self.getFloatAlpha()
        r = QColor()
        r.setRgbF(buff[0], buff[1], buff[2], alpha)
        return r

    def getAlpha(self) -> int:
        """
        Get int format opacity attribute of the current XmlStreamlines instance.

        Returns
        -------
        int
            Streamlines opacity, between 0 and 255
        """
        return int(self.getFloatAlpha() * 255)

    def getFloatAlpha(self) -> float:
        """
        Get float format opacity attribute of the current XmlStreamlines instance.

        Returns
        -------
        float
            Streamlines opacity between 0.0 and 1.0
        """
        return float(self.getFieldValues('opacity'))

    def getLineWidth(self) -> float:
        """
        Get line width attribute of the current XmlStreamlines instance.

        Returns
        -------
        float
            Streamlines line width in mm
        """
        return float(self.getFieldValues('linewidth'))

    def getLut(self) -> str:
        """
        Get lut name attribute of the current XmlStreamlines instance.

        Returns
        -------
        str
            Streamlines lut name
        """
        return self.getFieldValues('lut')

    def getSize(self) -> list[int]:
        """
        Get image size attribute of the current XmlStreamlines instance.

        Returns
        -------
        list[int]
            Streamlines size in x, y and z axes
        """
        r = self.getFieldValues('shape').split(' ')
        return [int(v) for v in r]

    def getSpacing(self) -> list[float]:
        """
        Get image spacing (i.e. voxel size in each dimension)
        attribute of the current XmlStreamlines instance.

        Returns
        -------
        list[float]
            Streamlines spacing in x, y and z axes
        """
        r = self.getFieldValues('spacing').split(' ')
        return [float(v) for v in r]

    def getFOV(self) -> list[float]:
        """
        Get field of view attribute of the current XmlStreamlines instance.

        Returns
        -------
        list[float]
            Streamlines FOV in x, y and z axes
        """
        spacing = self.getSpacing()
        size = self.getSize()
        return [spacing[i] * size[i] for i in range(3)]

    def getAffineTransform(self) -> ndarray:
        """
        Get affine transform attribute of the current XmlStreamlines instance.

        Returns
        -------
        numpy.ndarray
            Affine transform
        """
        buff = self.getFieldValues('affine')
        affine = [float(v) for v in buff.split(' ')]
        return array(affine).reshape(4, 4)

    def isWhole(self) -> bool:
        """
        Check whether streamlines of the current SisypheStreamlines instance have been generated from whole brain seeds.

        Returns
        -------
        bool
            True if whole brain streamlines
        """
        return bool(self.getFieldValues('whole') == 'True')

    def isCentroid(self) -> bool:
        """
        Check whether the current SisypheStreamlines instance is a centroid streamline.

        Returns
        -------
        bool
            True if centroid streamline
        """
        return bool(self.getFieldValues('centroid') == 'True')

    def isAtlas(self) -> bool:
        """
        Check whether streamlines of the current SisypheStreamlines instance are atlas streamlines.

        Returns
        -------
        bool
            True if atlas streamlines
        """
        return bool(self.getFieldValues('atlas') == 'True')

    def isRegularStep(self) -> bool:
        """
        Check whether the streamlines of the current SisypheStreamlines instance are compressed.

        By default, streamlines are uncompressed, with a regular step between points. Compression can be applied to
        streamlines i.e. a reduction in the number of points with non-uniform steps between points. The compression
        consists in merging consecutive segments that are nearly collinear. The merging is achieved by removing the
        point the two segments have in common. The linearization process ensures that every point being removed are
        within a certain margin of the resulting streamline.

        Returns
        -------
        bool
            True, if not compressed with regular step between points.
        """
        return bool(self.getFieldValues('regularstep') == 'True')
