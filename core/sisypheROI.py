"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        pandas          https://pandas.pydata.org/                                  Data analysis and manipulation tool
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        radiomics       https://pyradiomics.readthedocs.io/en/latest/               Radiomics features
        scipy           https://scipy.org/                                          Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        skimage         https://scikit-image.org/                                   Image processing
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os import getcwd
from os.path import exists
from os.path import join
from os.path import split
from os.path import splitext
from os.path import basename
from os.path import dirname

from math import sqrt

from xml.dom import minidom

from zlib import compress
from zlib import decompress

from collections import deque

from numpy import uint8
from numpy import array
from numpy import zeros
from numpy import frombuffer
from numpy import histogram
from numpy import median
from numpy import percentile
from numpy import bitwise_and
from numpy import bitwise_or
from numpy import logical_not
from numpy import invert
from numpy import ndarray as np_ndarray

from scipy import sparse
from scipy.stats import describe

from pandas import DataFrame

from skimage.draw import line
from skimage.draw import disk
from skimage.draw import ellipse
from skimage.draw import rectangle
from skimage.draw import polygon
from skimage.draw import ellipsoid
from skimage.morphology import flood

from PyQt5.QtGui import QColor
from PyQt5.QtCore import QRegExp
from PyQt5.QtWidgets import QApplication

from SimpleITK import sitkUInt8
from SimpleITK import sitkFloat32
from SimpleITK import Paste
from SimpleITK import Cast as sitkCast
from SimpleITK import Image as sitkImage
from SimpleITK import Flip as sitkFlip
from SimpleITK import sitkBall, sitkBox, sitkCross, sitkAnnulus
from SimpleITK import CyclicShift as sitkShift
from SimpleITK import BinaryThreshold as sitkThreshold
from SimpleITK import ConnectedThreshold as sitkConnectedThreshold
from SimpleITK import ConfidenceConnected as itkConfidenceConnected
from SimpleITK import GetArrayFromImage as sitkGetArrayFromImage
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage
from SimpleITK import GetImageFromArray as sitkGetImageFromArray
from SimpleITK import BinaryDilate as sitkBinaryDilate
from SimpleITK import BinaryErode as sitkBinaryErode
from SimpleITK import BinaryFillhole as sitkBinaryFillHole
from SimpleITK import BinaryFillholeImageFilter
from SimpleITK import BinaryMorphologicalOpening as sitkBinaryOpening
from SimpleITK import BinaryMorphologicalClosing as sitkBinaryClosing
from SimpleITK import BinaryNot as sitkBinaryNot
from SimpleITK import OtsuThreshold as sitkOtsu
from SimpleITK import OtsuThresholdImageFilter as sitkOtsuThresholdImageFilter
from SimpleITK import HuangThreshold as sitkHuang
from SimpleITK import RenyiEntropyThreshold as sitkRenyi
from SimpleITK import YenThreshold as sitkYen
from SimpleITK import LiThreshold as sitkLi
from SimpleITK import ShanbhagThreshold as sitkShanbhag
from SimpleITK import TriangleThreshold as sitkTriangle
from SimpleITK import IntermodesThreshold as sitkIntermodes
from SimpleITK import MaximumEntropyThreshold as sitkMaximumEntropy
from SimpleITK import KittlerIllingworthThreshold as sitkKittler
from SimpleITK import IsoDataThreshold as sitkIsoData
from SimpleITK import MomentsThreshold as sitkMoments
from SimpleITK import ConnectedComponent as sitkConnectedComponent
from SimpleITK import RelabelComponent as sitkRelabelComponent
from SimpleITK import LabelShapeStatisticsImageFilter as sitkLabelShapeStatisticsImageFilter
from SimpleITK import LabelStatisticsImageFilter as sitkLabelStatisticsImageFilter
from SimpleITK import ApproximateSignedDistanceMap as sitkDistanceMap
from SimpleITK import SignedMaurerDistanceMap as sitkSignedMaurerDistanceMap
from SimpleITK import BoundedReciprocal as sitkBoundedReciprocal
from SimpleITK import GradientMagnitudeRecursiveGaussian as sitkGradientMagnitude
from SimpleITK import GeodesicActiveContourLevelSetImageFilter as sitkGeodesicActiveContourLevelSetImageFilter
from SimpleITK import ShapeDetectionLevelSetImageFilter as sitkShapeDetectionLevelSetImageFilter
from SimpleITK import ThresholdSegmentationLevelSetImageFilter as sitkThresholdSegmentationLevelSetImageFilter
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage

from vtk import vtkLookupTable
from vtk import vtkImageCast
from vtk import vtkContourFilter
from vtk import vtkMarchingCubes
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper
from vtk import vtkActor

from radiomics.firstorder import RadiomicsFirstOrder
from radiomics.shape import RadiomicsShape
from radiomics.glcm import RadiomicsGLCM
from radiomics.glszm import RadiomicsGLSZM
from radiomics.glrlm import RadiomicsGLRLM
from radiomics.ngtdm import RadiomicsNGTDM
from radiomics.gldm import RadiomicsGLDM

import Sisyphe.core as sc
from Sisyphe.lib.bv.voi import read_voi
from Sisyphe.lib.bv.vmr import read_vmr
from Sisyphe.core.sisypheConstants import getSisypheROIExt
from Sisyphe.core.sisypheConstants import getBrainVoyagerVMRExt
from Sisyphe.core.sisypheConstants import getBrainVoyagerVOIExt
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageIO import readFromSisypheROI
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImage import SisypheBinaryImage
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheROI',
           'SisypheROICollection',
           'SisypheROIDraw',
           'SisypheROIFeatures',
           'SisypheROIHistogram']

"""
    Class hierarchy
    
        object -> SisypheImage -> SisypheBinaryImage -> SisypheROI
               -> SisypheROICollection
               -> SisypheROIDraw
               -> SisypheROIFeatures
               -> SisypheROIHistogram
"""

imageType = sitkImage | np_ndarray | SisypheImage
vectorInt2Type = list[int, int] | tuple[int, int]
vectorInt3Type = list[int, int, int] | tuple[int, int, int]
vectorFloat3Type = list[float, float, float] | tuple[float, float, float]

class SisypheROI(SisypheBinaryImage):
    """
        SisypheROI class

        Description

            ROI image class.

        Inheritance

            object -> SisypheImage -> SisypheBinaryImage -> SisypheROI

        Private attributes

            _color          list(double double double)
            _alpha          float
            _name           str
            _path           str
            _reference_ID   str
            _compressed     bool
            _filename       str
            _lut            SisypheLut instance

        Class method

            str = getFileExt()
            str = getFilterExt()

        Public methods

            SisypheROI = copy()
            copyAttributesTo(SisypheROI)
            copyAttributesFrom(SisypheROI)
            setName(str)
            setDefaultName()
            str = getName()
            setFilename(str)
            setDefaultFilename()
            setPathFromVolume(SisypheVolume)
            str = getFilename()
            str = getDirname()
            bool = hasFilename()
            float, float, float = getColor()
            QColor = getQColor()
            setColor(float, float, float)
            setQColor(QColor)
            float = getAlpha()
            setAlpha(float)
            setOverlayEdgeVisibility(bool)
            setVisibilityOn()
            setVisibilityOff()
            bool = getVisibility()
            str = getReferenceID()
            setReferenceID(str)
            setCompression(bool)
            setCompressionToOn()
            setCompressionToOff()
            bool = getCompression()
            parseXML(minidom.Document)
            createXML(minidom.Document, minidom.Document.documentElement)
            save()
            saveAs(str)
            load()
            loadFromSisyphe(str, index=int)
            loadFromBrainVoyagerVOI(str, index=int)
            flip()
            shift()
            morphoDilate(radius=int, struct=sitkBall | sitkBox | sitkCross | sitkAnnulus)
            morphoErode(radius=int, struct=sitkBall | sitkBox | sitkCross | sitkAnnulus)
            morphoOpening(radius=int, struct=sitkBall | sitkBox | sitkCross | sitkAnnulus)
            morphoClosing(radius=int, struct=sitkBall | sitkBox | sitkCross | sitkAnnulus)
            fillHoles()
            SisypheROI = getFlip()
            SisypheROI = getShift()
            SisypheROI = getMorphoDilate()
            SisypheROI = getMorphoErode()
            SisypheROI = getMorphoClosing()
            SisypheROI = getMorphoOpening()
            SisypheROI = getFillHoles()
            SisypheROI = getMajorBlob()
            SisypheROI = getBlobLargerThan(n=int)
            int = getBlobCount()
            clear()
            drawLine(p0=[int]*3, p1=[int]*3, orient=int)
            drawDisk(p=[int]*3, radius=int, orient=int)
            drawEllipse(p=[int]*3, radius=int, rot=float, orient=int)
            drawSquare(p=[int]*3, extent=int, orient=int)
            drawRectangle(p=[int]*3, extent=[int]*2, orient=int)
            drawPolygon(p=[int]*3, orient=int)
            drawCube(p=[int]*3, extent=int)
            drawParallelepiped(p=[int]*3, extent=[int]*3)
            drawSphere(p=[int]*3, radius=int)
            vtkPolyData = getVtkContourPolyData()
            vtkPolyData = getVtkMarchingCubeContourPolyData()
            vtkActor = getVtkContourActor()
            vtkActor = getVtkMarchingCubeContourActor()

            inherited SisypheImage class
            inherited SisypheBinaryImage class

        Creation: 08/09/2022
        Revisions:

            08/05/2022  new IO methods for single file *.xroi format
            20/07/2023  add loadFromBrainVoyagerVOI IO method, open brainvoyager voi
            20/07/2023  loadFromSisyphe method bugfix
            20/07/2023  add clear method, fill with 0
            03/08/2023  add '#' char to _REGEXP
            01/09/2023  type hinting
            31/10/2023  add openROI() class method
    """

    __slots__ = ['_filename', '_referenceID', '_compression', '_name', '_color', '_alpha', '_visibility', '_lut']
    _counter = int(0)

    # Class constants

    _FILEEXT = '.xroi'
    _REGEXP = '^[_A-Za-z0-9#\-\_\s+,]+$'

    # Class methods

    @classmethod
    def getInstancesCount(cls) -> int:
        return cls._counter

    @classmethod
    def addInstance(cls) -> None:
        cls._counter += 1

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe ROI (*{})'.format(cls._FILEEXT)

    @classmethod
    def getRegExp(cls) -> str:
        return cls._REGEXP

    @classmethod
    def openROI(cls, filename: str) -> SisypheROI:
        if exists(filename):
            filename = basename(filename) + cls.getFileExt()
            roi = SisypheROI()
            roi.load(filename)
            return roi

    # Special methods

    def __init__(self, image=None, copy=True, **kargs):
        self.addInstance()
        self._referenceID = ''
        # Copy SisypheVolume ID to reference ID
        if isinstance(image, SisypheVolume):
            self.setReferenceID(image.getID())
        # Copy SisypheROI reference ID
        elif isinstance(image, SisypheROI):
            self.setReferenceID(image.getReferenceID())
            image = image._sitk_image
        super().__init__(image, copy, **kargs)
        self._name = ''
        self._filename = ''
        self._compression = False
        self._color = [1.0, 0.0, 0.0]   # default = red
        self._alpha = 1.0               # default = opaque
        self._visibility = True
        self._lut = SisypheLut()
        self._initLut()
        self.setDefaultOrigin()
        self.setDirections()
        self.setDefaultFilename()

    def __str__(self) -> str:
        buff = 'ReferenceID: {}\n' \
               'Name: {}\n'.format(self.getReferenceID(), self._name)
        buff += super().__str__()
        buff += 'Color: r={0[0]:.2f} g={0[1]:.2f} b={0[2]:.2f}\n' \
                'Alpha: {1:.2f}\n'.format(self._color, self._alpha)
        return buff

    def __repr__(self) -> str:
        return 'SisypheROI instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Difference

    def __sub__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        img = self._sitk_image.__sub__(other) == 1
        return SisypheROI(sitkCast(img, getLibraryDataType('uint8', 'sitk')))

    def __rsub__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        img = self._sitk_image.__rsub__(other) == 1
        return SisypheROI(sitkCast(img, getLibraryDataType('uint8', 'sitk')))

    # Logic operators

    def __and__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__and__(other))

    def __rand__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__rand__(other))

    def __or__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__or__(other))

    def __ror__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__ror__(other))

    def __xor__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__xor__(other))

    def __rxor__(self, other: imageType | SisypheROI | int | float) -> SisypheROI:
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheROI(self._sitk_image.__rxor__(other))

    def __invert__(self) -> SisypheROI:
        return SisypheROI(sitkBinaryNot(self._sitk_image))

    # Private method

    def _toSimpleITK(self, img: sitkImage | int | float) -> sitkImage | int | float:
        img = super()._toSimpleITK(img)
        if isinstance(img, sitkImage):
            img = sitkCast(img > 0, getLibraryDataType('uint8', 'sitk'))
            img.SetOrigin(self.getOrigin())
            img.SetDirection(self.getDirections())
        if isinstance(img, (int, float)):
            if int(img) > 0: img = 1
            else: img = 0
        return img

    def _initLut(self) -> None:
        self._lut.setColor(0, 0.0, 0.0, 0.0, 0.0)
        for i in range(1, 256):
            self._lut.setColor(i,
                               self._color[0],
                               self._color[1],
                               self._color[2],
                               self._alpha)

    # Public methods

    def copy(self) -> SisypheROI:
        if not self.isEmpty():
            roi = SisypheROI(self.getSITKImage())
            self.copyAttributesTo(roi)
            return roi
        else: raise ValueError('SisypheROI is empty.')

    def copyAttributesTo(self, roi: SisypheROI) -> None:
        if isinstance(roi, SisypheROI):
            roi.setReferenceID(self)
            roi.setName(self.getName())
            roi.setFilename(self.getFilename())
            roi.setColor(rgb=self.getColor())
            roi.setAlpha(self.getAlpha())
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def copyAttributesFrom(self, roi: SisypheROI) -> None:
        if isinstance(roi, SisypheROI):
            self.setReferenceID(roi)
            self.setName(roi.getName())
            self.setFilename(roi.getFilename())
            self.setColor(rgb=roi.getColor())
            self.setAlpha(roi.getAlpha())
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def setName(self, name: str) -> None:
        if isinstance(name, str):
            re = QRegExp(self._REGEXP)
            if re.exactMatch(name):
                self._name = name
            else: raise ValueError('Invalid char in name parameter.')
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self) -> str:
        return self._name

    def setDefaultName(self) -> None:
        idx = '00{}'.format(self.getInstancesCount())[-3:]
        self.setName('ROI{}'.format(idx))

    def setFilename(self, filename: str) -> None:
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
            self._filename = filename
            if self._name == '':
                self._name = splitext(basename(filename))[0]
        else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    def setDefaultFilename(self) -> None:
        if self._name == '': self.setDefaultName()
        self._filename = join(getcwd(), '{}{}'.format(self._name, self._FILEEXT))

    def setPathFromVolume(self, volume: SisypheVolume) -> None:
        if isinstance(volume, SisypheVolume):
            path = dirname(volume.getFilename())
            if path != '': self._filename = join(path, basename(self._filename))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getDirname(self) -> str:
        return dirname(self._filename)

    def getFilename(self) -> str:
        return self._filename

    def hasFilename(self) -> bool:
        return self._filename != ''

    def getColor(self) -> vectorFloat3Type:
        return self._color

    def getQColor(self) -> QColor:
        c = QColor()
        c.setRgbF(self._color[0], self._color[1], self._color[2])
        return c

    def setColor(self,
                 r: float | int | None = None,
                 g: float | int | None = None,
                 b: float | int | None = None,
                 rgb: vectorFloat3Type | vectorInt3Type | None = None):
        if rgb is None:
            rgb = [r, g, b]
        for i in range(0, 3):
            if isinstance(rgb[i], float):
                if rgb[i] < 0.0 or rgb[i] > 1.0:
                    raise ValueError('float color value {} is not between 0.0 and 1.0.'.format(rgb[i]))
            elif isinstance(rgb[i], int):
                if 0 <= rgb[i] <= 255:
                    rgb[i] = float(rgb[i]) / 255
                else: raise ValueError('int color value {} is not be between 0 and 255.'.format(rgb[i]))
            else: raise TypeError('parameter type {} is not int or float.'.format(type(rgb[i])))
        self._color = rgb
        self._initLut()

    def setQColor(self, c: QColor) -> None:
        if isinstance(c, QColor):
            self._color = list(c.getRgbF())[:3]
            self._initLut()
        else: raise TypeError('parameter type {} is not QColor.'.format(type(c)))

    def getAlpha(self) -> float:
        return self._alpha

    def setAlpha(self, a: int | float) -> None:
        if isinstance(a, float):
            if 0.0 <= a <= 1.0: self._alpha = a
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(a))
        elif isinstance(a, int):
            if 0 <= a <= 255: self._alpha = a / 255
            else: raise ValueError('parameter value {} is not between 0 and 255.'.format(a))
        else: raise TypeError('parameter type {} is not int or float.'.format(type(a)))
        self._initLut()

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._visibility = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVisibilityOn(self) -> None:
        self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        self.setVisibility(False)

    def getVisibility(self) -> bool:
        return self._visibility

    def getLut(self) -> SisypheLut:
        return self._lut

    def getvtkLookupTable(self) -> vtkLookupTable:
        return self._lut.getvtkLookupTable()

    def getReferenceID(self) -> str:
        if self._referenceID is None:
            return 'None'
        else:
            return self._referenceID

    def setReferenceID(self, ID: SisypheROI | SisypheVolume | str) -> None:
        if isinstance(ID, SisypheROI):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, (SisypheImage, SisypheVolume)):
            self._referenceID = ID.getID()
        elif isinstance(ID, str):
            self._referenceID = ID
        else: raise TypeError('parameter type {} is not SisypheImage, SisypheVolume or str'.format(type(ID)))

    def hasReferenceID(self) -> bool:
        return self._referenceID != ''

    def setCompression(self, v: bool) -> None:
        if isinstance(v, bool):
            self._compression = v

    def setCompressionOn(self) -> None:
        self._compression = True

    def setCompressionOff(self) -> None:
        self._compression = False

    def getCompression(self) -> bool:
        return self._compression

    # Processing

    def flip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> None:
        self.setSITKImage(sitkFlip(self.getSITKImage(), [fx, fy, fz]))

    def shift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> None:
        self.setSITKImage(sitkShift(self.getSITKImage(), [sx, sy, sz]))

    def morphoDilate(self, radius: int = 1, struct: int = sitkBall) -> None:
        self.setSITKImage(sitkBinaryDilate(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoErode(self, radius: int = 1, struct: int = sitkBall) -> None:
        self.setSITKImage(sitkBinaryErode(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoOpening(self, radius: int = 1, struct: int = sitkBall) -> None:
        self.setSITKImage(sitkBinaryOpening(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoClosing(self, radius: int = 1, struct: int = sitkBall) -> None:
        self.setSITKImage(sitkBinaryClosing(self.getSITKImage(), [radius, radius, radius], struct))

    def fillHoles(self) -> None:
        self.setSITKImage(sitkBinaryFillHole(self.getSITKImage()))

    def getFlip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> SisypheROI:
        return SisypheROI(sitkFlip(self.getSITKImage(), [fx, fy, fz]))

    def getShift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> SisypheROI:
        return SisypheROI(sitkShift(self.getSITKImage(), [sx, sy, sz]))

    def getMorphoDilate(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        return SisypheROI(sitkBinaryDilate(self.getSITKImage(), [radius, radius, radius], struct))

    def getMorphoErode(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        return SisypheROI(sitkBinaryErode(self.getSITKImage(), [radius, radius, radius], struct))

    def getMorphoOpening(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        return SisypheROI(sitkBinaryOpening(self.getSITKImage(), [radius, radius, radius], struct))

    def getMorphoClosing(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        return SisypheROI(sitkBinaryClosing(self.getSITKImage(), [radius, radius, radius], struct))

    def getFillHoles(self) -> SisypheROI:
        return SisypheROI(sitkBinaryFillHole(self.getSITKImage()))

    def getMajorBlob(self) -> SisypheROI:
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                img = sitkRelabelComponent(img)
                img = (img == 1)
                return SisypheROI(img)
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')

    def getBlobLargerThan(self, n: int) -> SisypheROI:
        img = sitkConnectedComponent(self.getSITKImage())
        img = sitkRelabelComponent(img, minimumObjectSize=n)
        return SisypheROI(img > 0)

    def getBlobCount(self) -> int:
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                return sitkGetArrayViewFromImage(img).max()
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')

    def clear(self) -> None:
        self.getNumpy().fill(0)

    # Draw methods

    def drawLine(self, p0: vectorInt3Type, p1: vectorInt3Type, orient: int = 0) -> None:
        """
            p0      [int]*3 | (int, )*3, x, y, z coordinates of first point
            p1      [int]*3 | (int, )*3, x, y, z coordinates of second point
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        img = self.getNumpy()
        if orient == 0:
            slc = img[p0[2], :, :]
            r, c = line(p0[1], p0[0], p1[1], p1[0])
            slc[r, c] = 1
            img[p0[2], :, :] = slc
        elif orient == 1:
            slc = img[:, p0[1], :]
            r, c = line(p0[2], p0[0], p1[2], p1[0])
            slc[r, c] = 1
            img[:, p0[1], :] = slc
        else:
            slc = img[:, :, p0[0]]
            r, c = line(p0[2], p0[1], p1[2], p1[1])
            slc[r, c] = 1
            img[:, :, p0[0]] = slc

    def drawDisk(self, p: vectorInt3Type, radius: int, orient: int = 0) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z coordinates of center point
            radius  int
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        img = self.getNumpy()
        if orient == 0:
            slc = img[p[2], :, :]
            r, c = disk(center=(p[1], p[0]), radius=radius)
            slc[r, c] = 1
            img[p[2], :, :] = slc
        elif orient == 1:
            slc = img[:, p[1], :]
            r, c = disk(center=(p[2], p[0]), radius=radius)
            slc[r, c] = 1
            img[:, p[1], :] = slc
        else:
            slc = img[:, :, p[0]]
            r, c = disk(center=(p[2], p[1]), radius=radius)
            slc[r, c] = 1
            img[:, :, p[0]] = slc

    def drawEllipse(self, p: vectorInt3Type, radius: vectorInt2Type, rot: float = 0.0, orient: int = 0) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z coordinates of center point
            radius  [int]*2, x, y, radius
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        img = self.getNumpy()
        if orient == 0:
            slc = img[p[2], :, :]
            r, c = ellipse(p[1], p[0], radius[1], radius[0], rotation=rot)
            slc[r, c] = 1
            img[p[2], :, :] = slc
        elif orient == 1:
            slc = img[:, p[1], :]
            r, c = ellipse(p[2], p[0], radius[1], radius[0], rotation=rot)
            slc[r, c] = 1
            img[:, p[1], :] = slc
        else:
            slc = img[:, :, p[0]]
            r, c = ellipse(p[2], p[1], radius[1], radius[0], rotation=rot)
            slc[r, c] = 1
            img[:, :, p[0]] = slc

    def drawSquare(self, p: vectorInt3Type, extent: int, orient: int = 0) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z origin coordinates
            extent  int
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        extent = (extent, ) * 2
        img = self.getNumpy()
        if orient == 0:
            slc = img[p[2], :, :]
            r, c = rectangle(start=(p[1], p[0]), extent=extent)
            slc[r, c] = 1
            img[p[2], :, :] = slc
        elif orient == 1:
            slc = img[:, p[1], :]
            r, c = rectangle(start=(p[2], p[0]), extent=extent)
            slc[r, c] = 1
            img[:, p[1], :] = slc
        else:
            slc = img[:, :, p[0]]
            r, c = rectangle(start=(p[2], p[1]), extent=extent)
            slc[r, c] = 1
            img[:, :, p[0]] = slc

    def drawRectangle(self, p: vectorInt3Type, extent: vectorInt2Type, orient: int = 0) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z origin coordinates
            extent  [int]*2, x, y extent
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        extent = extent[:, :, -1]
        img = self.getNumpy()
        if orient == 0:
            slc = img[p[2], :, :]
            r, c = rectangle(start=(p[1], p[0]), extent=extent)
            slc[r, c] = 1
            img[p[2], :, :] = slc
        elif orient == 1:
            slc = img[:, p[1], :]
            r, c = rectangle(start=(p[2], p[0]), extent=extent)
            slc[r, c] = 1
            img[:, p[1], :] = slc
        else:
            slc = img[:, :, p[0]]
            r, c = rectangle(start=(p[2], p[1]), extent=extent)
            slc[r, c] = 1
            img[:, :, p[0]] = slc

    def drawPolygon(self, p: vectorInt3Type, orient: int = 0) -> None:
        """
            p       list([int]*3 | (int, )*3)
            orient  int, 0 axial, 1 coronal, 2 sagittal
        """
        px = p[0][0]
        py = p[0][1]
        pz = p[0][2]
        p = array(p)
        img = self.getNumpy()
        if orient == 0:
            slc = img[pz, :, :]
            r, c = polygon(p[:, 1], p[:, 0])
        elif orient == 1:
            slc = img[:, py, :]
            r, c = polygon(p[:, 2], p[:, 0])
        else:
            slc = img[:, :, px]
            r, c = polygon(p[:, 2], p[:, 1])
        slc[r, c] = 1
        if orient == 0: img[pz, :, :] = slc
        elif orient == 1: img[:, py, :] = slc
        else:  img[:, :, px] = slc

    def drawCube(self, p: vectorInt3Type, extent: int) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z origin coordinates
            extent  int, length
        """
        extent = (extent,) * 3
        img = self.getNumpy()
        z, y, x = rectangle(start=(p[2], p[1], p[0]), extent=extent)
        img[z, y, x] = 1

    def drawParallelepiped(self, p: vectorInt3Type, extent: vectorInt3Type) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z origin coordinates
            extent  [int]*3, x, y, z extents
        """
        img = self.getNumpy()
        z, y, x = rectangle(start=(p[2], p[1], p[0]), extent=(extent[2], extent[1], extent[0]))
        img[z, y, x] = 1

    def drawSphere(self, p: vectorInt3Type, radius: int) -> None:
        """
            p       [int]*3 | (int, )*3, x, y, z origin coordinates
            radius  int
        """
        sph = ellipsoid(radius, radius, radius,
                        spacing=self.getSpacing()).astype('uint8')
        sph = sph[2:-2, 2:-2, 2:-2]
        x, y, z = p
        xmax, ymax, zmax = self.getSize()
        if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
            idx1 = radius - 1 - x
            idy1 = radius - 1 - y
            idz1 = radius - 1 - z
            idx2 = xmax - x - radius
            idy2 = ymax - y - radius
            idz2 = zmax - z - radius
            if idx1 < 0: x, idx1 = -idx1, 0
            else: x = 0
            if idy1 < 0: y, idy1 = -idy1, 0
            else: y = 0
            if idz1 < 0: z, idz1 = -idz1, 0
            else: z = 0
            m = 2 * radius - 1
            if idx2 > -1: idx2 = m
            if idy2 > -1: idy2 = m
            if idz2 > -1: idz2 = m
            sph = sph[idz1:idz2, idy1:idy2, idx1:idx2]
            dz, dy, dx = sph.shape
            x2 = x + dx
            y2 = y + dy
            z2 = z + dz
            back = self.getNumpy()[z:z2, y:y2, x:x2]
            self.getNumpy()[z:z2, y:y2, x:x2] = bitwise_or(back, sph)

    # Mesh conversion

    def getVtkContourPolyData(self) -> vtkPolyData:
        filtr = vtkImageCast()
        filtr.SetInputData(self.getVTKImage())
        filtr.SetOutputScalarTypeToFloat()
        filtr.Update()
        mask = filtr.GetOutput()
        filtr = vtkContourFilter()
        filtr.SetInputData(mask)
        filtr.ComputeNormalsOn()
        filtr.SetValue(0, 0.5)
        filtr.Update()
        return filtr.GetOutput()

    def getVtkMarchingCubeContourPolyData(self) -> vtkPolyData:
        filtr = vtkImageCast()
        filtr.SetInputData(self.getVTKImage())
        filtr.SetOutputScalarTypeToFloat()
        filtr.Update()
        mask = filtr.GetOutput()
        filtr = vtkMarchingCubes()
        filtr.SetInputData(mask)
        filtr.ComputeNormalsOn()
        filtr.SetValue(0, 0.5)
        filtr.Update()
        return filtr.GetOutput()

    def getVtkContourActor(self) -> vtkActor:
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(self.getVtkContourPolyData())
        mapper.ScalarVisibilityOff()
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
        return actor

    def getVtkMarchingCubeContourActor(self) -> vtkActor:
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(self.getVtkMarchingCubeContourPolyData())
        mapper.ScalarVisibilityOff()
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
        return actor

    # IO old version 1.0, deprecated methods

    def createXMLOld(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Reference ID node
            node = doc.createElement('referenceID')
            root.appendChild(node)
            txt = doc.createTextNode(self.getReferenceID())
            node.appendChild(txt)
            # Compressed node
            node = doc.createElement('compressed')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._compression))
            node.appendChild(txt)
            # Name node
            node = doc.createElement('name')
            root.appendChild(node)
            txt = doc.createTextNode(self._name)
            node.appendChild(txt)
            # Color node
            node = doc.createElement('color')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self._color)]))
            node.appendChild(txt)
            # Alpha node
            node = doc.createElement('alpha')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._alpha))
            node.appendChild(txt)
            # Size node
            node = doc.createElement('size')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSize())]))
            node.appendChild(txt)
            # Spacing node
            node = doc.createElement('spacing')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSpacing())]))
            node.appendChild(txt)
            # Array node
            node = doc.createElement('array')
            root.appendChild(node)
            path, ext = splitext(self._filename)
            filename = path + '.raw'
            txt = doc.createTextNode(filename)
            node.appendChild(txt)
            # Save raw data
            buff = self.getNumpy().tobytes()
            if self._compression: buff = compress(buff)
            with open(filename, 'wb') as f:
                f.write(buff)

    def parseXMLOld(self, doc: minidom.Document) -> None:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
            size = None
            spacing = None
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'referenceID':
                    self._referenceID = node.firstChild.data
                    if self._referenceID == 'None': self._referenceID = None
                # Compressed
                elif node.nodeName == 'compressed':
                    self._compression = node.firstChild.data == 'True'
                elif node.nodeName == 'name':
                    self._name = node.firstChild.data
                elif node.nodeName == 'color':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    self._color = [float(i) for i in buff]
                elif node.nodeName == 'alpha':
                    self._alpha = float(node.firstChild.data)
                elif node.nodeName == 'size':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    size = [int(i) for i in buff]
                elif node.nodeName == 'spacing':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    spacing = [float(i) for i in buff]
                elif node.nodeName == 'array':
                    if not self.isEmpty():
                        filename, ext = splitext(self._filename)
                        filename += '.raw'
                        if not exists(filename):
                            path = split(filename)
                            buff = node.firstChild.data
                            filename = join(path[0], buff)
                            if not exists(filename):
                                raise IOError('No such file or directory: {}'.format(filename))
                        # Load raw data
                        with open(filename, 'rb') as f:
                            buff = f.read()
                        if self._compression: buff = decompress(buff)
                        img = frombuffer(buff, dtype='uint8')
                        img = img.reshape((size[2], size[1], size[0]))
                        self.copyFromNumpyArray(img, spacing=spacing, defaultshape=True)
                node = node.nextSibling
            self._initLut()

    def saveAsOld(self, filename: str) -> None:
        if not self.isEmpty():
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
            doc = minidom.Document()
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            self.setFilename(filename)
            self.createXMLOld(doc)
            buff = doc.toprettyxml()
            with open(filename, 'w') as f:
                f.write(buff)
        else: raise ValueError('Array image is empty.')

    def loadOld(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            # XML part
            self._filename = filename
            self.parseXMLOld(doc)
        else: raise IOError('no such file : {}'.format(filename))

    # IO new version 1.1

    def save(self, filename: str = '') -> None:
        if not self.isEmpty():
            if filename != '': self.saveAs(filename)
            elif self.hasFilename(): self.saveAs(self._filename)
            else: raise IOError('parameter and filename attribute are empty.')
        else: raise ValueError('Voxel data array is empty.')

    def createXML(self, doc: minidom.Document, single: bool = True) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Reference ID node
            node = doc.createElement('referenceID')
            root.appendChild(node)
            txt = doc.createTextNode(self.getReferenceID())
            node.appendChild(txt)
            # Compressed node
            node = doc.createElement('compressed')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._compression))
            node.appendChild(txt)
            # Name node
            node = doc.createElement('name')
            root.appendChild(node)
            txt = doc.createTextNode(self._name)
            node.appendChild(txt)
            # Color node
            node = doc.createElement('color')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self._color)]))
            node.appendChild(txt)
            # Alpha node
            node = doc.createElement('alpha')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._alpha))
            node.appendChild(txt)
            # Size node
            node = doc.createElement('size')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSize())]))
            node.appendChild(txt)
            # Spacing node
            node = doc.createElement('spacing')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSpacing())]))
            node.appendChild(txt)
            # Array node
            node = doc.createElement('array')
            root.appendChild(node)
            if single is True: txt = doc.createTextNode('self')
            else:
                filename = '{}.raw'.format(splitext(self._filename)[0])
                txt = doc.createTextNode(basename(filename))
            node.appendChild(txt)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(doc))

    def saveAs(self, filename: str, single: bool = True) -> None:
        # single = True, write single hybrid file with XML part followed by binary array part
        # if False, write two files *.xvol for XML part and *.raw for binary array part
        if not self.isEmpty():
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
            doc = minidom.Document()
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.1')
            doc.appendChild(root)
            self.setFilename(filename)
            self.createXML(doc, single)
            buffxml = doc.toprettyxml().encode()  # Convert utf-8 to binary
            buffarray = self.getNumpy().tobytes()
            if self._compression: buffarray = compress(buffarray)
            with open(filename, 'wb') as f:
                # Save XML part
                f.write(buffxml)
                # Binary array part
                if single is True:
                    # Write in same file after XML part
                    f.write(buffarray)
                else:
                    # Write in other file *.raw
                    afilename = '{}.raw'.format(path)
                    with open(afilename, 'wb') as fa:
                        fa.write(buffarray)
        else: raise AttributeError('Data Array is empty.')

    def parseXML(self, doc: documentElement) -> dict:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.1':
            attr = dict()
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'referenceID':
                    self._referenceID = node.firstChild.data
                    if self._referenceID == 'None': self._referenceID = None
                # Compressed
                elif node.nodeName == 'compressed':
                    self._compression = node.firstChild.data == 'True'
                elif node.nodeName == 'name':
                    self._name = node.firstChild.data
                elif node.nodeName == 'color':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    self._color = [float(i) for i in buff]
                elif node.nodeName == 'alpha':
                    self._alpha = float(node.firstChild.data)
                elif node.nodeName == 'size':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    attr['size'] = [int(i) for i in buff]
                elif node.nodeName == 'spacing':
                    buff = node.firstChild.data
                    buff = buff.split(' ')
                    attr['spacing'] = [float(i) for i in buff]
                elif node.nodeName == 'array':
                    attr['array'] = node.firstChild.data
                node = node.nextSibling
            self._initLut()
            return attr
        else: raise IOError('XML file format is not supported.')

    def load(self, filename: str) -> None:
        # Check extension xroi
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
        if exists(filename):
            # Read XML part
            with open(filename, 'rb') as f:
                line = ''
                strdoc = ''
                while line != '</xroi>\n':
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                self._filename = filename
                doc = minidom.parseString(strdoc)
                attr = self.parseXML(doc)
            # Read binary array part
                buff = None
                rawname = attr['array']
                if rawname == 'self':
                    buff = f.read()
                else:
                    rawname = join(dirname(filename), basename(rawname))
                    rawname = '{}.raw'.format(splitext(rawname)[0])
                    if exists(rawname):
                        with open(rawname, 'rb') as fa:
                            buff = fa.read()
            if buff is not None:
                if self._compression: buff = decompress(buff)
                img = frombuffer(buff, dtype='uint8')
                size = attr['size']
                img = img.reshape((size[2], size[1], size[0]))
                self.copyFromNumpyArray(img, spacing=attr['spacing'], defaultshape=True)
            else: raise IOError('no such file : {}.'.format(rawname))
        else: raise IOError('no such file : {}'.format(filename))

    # IO other format

    def loadFromSisyphe(self, filename: str, index: int = 0) -> None:
        if exists(filename):
            path, ext = splitext(filename)
            ext = ext.lower()
            if ext == getSisypheROIExt()[0]:
                img, hdr = readFromSisypheROI(filename)
                if index < len(img):
                    img = flipImageToVTKDirectionConvention(img[index])
                    self.setName(splitext(basename(filename))[0])
                    self.setColor(hdr['Red'], hdr['Blue'], hdr['Green'])
                    self.setAlpha(hdr['Alpha'])
                    self.setSITKImage(img)
                    self.setOrigin()
                    self.setDirections(getRegularDirections())
                else: raise IndexError('Index {} is out of range (max={})'.format(index, len(img)-1))
            else: raise IOError('{} is not a Sisyphe ROI file extension.'.format(ext))
        else: raise IOError('no such file {}.'.format(filename))

    def loadFromBrainVoyagerVOI(self, vmr: str, voi: str, index: int = 0) -> None:
        if exists(vmr):
            path, ext = splitext(vmr)
            ext = ext.lower()
            if ext == getBrainVoyagerVMRExt()[0]:
                hdr, data = read_vmr(vmr)
                vx = hdr['VoxelSizeY']
                vy = hdr['VoxelSizeX']
                vz = hdr['VoxelSizeZ']
                buff = zeros(shape=data.shape, dtype='uint8')
            else: raise IOError('{} is not a BrainVoyager VMR file extension.'.format(ext))
        else: raise IOError('no such file {}.'.format(vmr))
        if exists(voi):
            path, ext = splitext(filename)
            ext = ext.lower()
            if ext == getBrainVoyagerVOIExt()[0]:
                voi = read_voi(voi)
                n = voi[0]['NrOfVOIs']
                if index < n:
                    voi = voi[1][index]
                    r = voi['Coordinates'][:, 0]
                    c = voi['Coordinates'][:, 1]
                    buff[r, c] = 1
                    img = sitkGetImageFromArray(buff.T)
                    img.SetSpacing((vx, vy, vz))
                    self.setSITKImage(img)
                    self.setColor(rgb=voi[ColorOfVOI])
                    self.setName(voi['NameOfVOI'])
                    self.setOrigin()
                    self.setDirections(getRegularDirections())
            else: raise IOError('{} is not a BrainVoyager VOI file extension.'.format(ext))
        else: raise IOError('no such file {}.'.format(vmr))


class SisypheROICollection(object):
    """
        SisypheROICollection

        Description

            Container for SisypheROI instances.

        Inheritance

            object -> SisypheROICollection

        Private attributes

            _rois           list of SisypheROI
            _index          index for Iterator
            _referenceID    str

        Public methods

            __getitem__(str | int)
            __setitem__(int, SisypheROI)
            __delitem__(SisypheROI | str | int)
            __len__()
            __contains__(str | SisypheROI)
            __iter__()
            __next__()
            __str__()
            __repr__()
            setReferenceID(SisypheROI or SisypheVolume or str)
            str = getReferenceID()
            bool = isEmpty()
            int = count()
            remove(SisypheROI | str | int)
            SisypheTransform = pop(SisypheROI | str | int)
            list = keys()
            int = index(SisypheROI | str)
            reverse()
            append(SisypheROI)
            insert(SisypheROI | str | int, SisypheROI)
            clear()
            sort()
            SisypheROICollection = copy()
            list = copyToList()
            list = getList()
            resample(SisypheTransform, save=bool, dialog=bool, prefix=str, suffix=str, wait=dialogWait)
            SisypheVolume = toLabelVolume()
            fromLabelVolume(SisypheVolume)
            load(list)
            loadFromSisyphe(list)
            loadFromBrainVoyagerVOI(vmr=str, filenames=list(str))
            save()

        Creation: 08/09/2022
        Revisions:

            16/03/2023  changed items type in _rois list, tuple(Str Name, SisypheROI) replaced by SisypheROI
            16/03/2023  add pop method, removes SisypheROI from list and returns it
            16/03/2023  add __getattr__ method, gives access to setter and getter methods of SisypheROI
            16/05/2023  add item ID control
            15/06/2023  add SisypheVolume label conversion methods (toLabel and fromLabel)
            15/06/2023  add save method
            20/07/2023  add loadFromBrainVoyagerVOI IO method, open brainvoyager voi
            20/07/2023  loadFromSisyphe() bugfix
            01/09/2023  type hinting
    """

    __slots__ = ['_rois', '_index', '_referenceID']

    # Private method

    def _verifyID(self, roi: SisypheROI) -> None:
        if isinstance(roi, SisypheROI):
            if self.isEmpty(): self.setReferenceID(roi.getReferenceID())
            if self.hasReferenceID():
                if roi.getReferenceID() != self._referenceID:
                    if roi.getSize() == self.rois[0].getSize():
                        roi.setReferenceID(self._referenceID)
                    else:
                        raise ValueError('ROI reference ID ({}) is not '
                                         'compatible with collection reference ID ({}).'.format(roi.getReferenceID(),
                                                                                                self._referenceID))
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    # Special methods

    def __init__(self) -> None:
        super().__init__()
        self._rois = list()
        self._index = 0
        self._referenceID = ''

    def __str__(self) -> str:
        index = 0
        buff = 'SisypheROI count #{}\n'.format(len(self._rois))
        for roi in self._rois:
            index += 1
            buff += 'SisypheROI #{}\n'.format(index)
            buff += '{}\n'.format(str(roi))
        return buff

    def __repr__(self) -> str:
        return 'SisypheROICollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, key: str | int):
        # key is Name str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._rois):
                return self._rois[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheROI) -> None:
        if isinstance(value, SisypheROI):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._rois):
                    self._verifyID(value)
                    if value.getName() in self: key = self.index(value)
                    self._rois[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(value)))

    def __delitem__(self, key: str | int | SisypheROI) -> None:
        # key is Name str or SisypheROI
        if isinstance(key, (str, SisypheROI)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._rois):
                del self._rois[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        return len(self._rois)

    def __contains__(self, value: str | SisypheROI) -> bool:
        keys = [k.getName() for k in self._rois]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is SisypheROI
        elif isinstance(value, SisypheROI):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or SisypheROI.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> SisypheROI:
        if self._index < len(self._rois):
            n = self._index
            self._index += 1
            return self._rois[n]
        else:
            raise StopIteration

    def __getattr__(self, name: str):
        """
            When attribute does not exist in the class,
            try calling the setter or getter method of sisypheROI instances in collection.
            Getter methods return a list of the same size as the collection.
        """
        prefix = name[:3]
        if prefix in ('set', 'get'):
            def func(*args):
                # SisypheROI get methods or set methods without argument
                if len(args) == 0:
                    if prefix in ('get', 'set'):
                        if name in SisypheROI.__dict__:
                            if prefix == 'get': return [roi.__getattribute__(name)() for roi in self]
                            else:
                                for roi in self: roi.__getattribute__(name)()
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                # SisypheROI set methods with argument
                elif prefix == 'set':
                    p = args[0]
                    # SisypheROI set method argument is list
                    if isinstance(p, (list, tuple)):
                        n = len(p)
                        if n == self.count():
                            if name in SisypheROI.__dict__:
                                for i in range(n): self[i].__getattribute__(name)(p[i])
                            else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                        else: raise ValueError('Number of items in list ({}) '
                                               'does not match with {} ({}).'.format(p, self.__class__, self.count()))
                    # SisypheROI set method argument is a single value (int, float, str, bool)
                    else:
                        if name in SisypheROI.__dict__:
                            for roi in self: roi.__getattribute__(name)(p)
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
            return func
        raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Public methods

    def setReferenceID(self, ID: SisypheROI | SisypheImage | SisypheVolume | str) -> None:
        if isinstance(ID, SisypheROI):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, (SisypheImage, SisypheVolume)):
            self._referenceID = ID.getID()
        elif isinstance(ID, str):
            self._referenceID = ID
            if not self.isEmpty():
                for roi in self:
                    roi.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not SisypheROI or str'.format(type(ID)))

    def getReferenceID(self) -> str:
        return self._referenceID

    def hasReferenceID(self) -> bool:
        return self._referenceID != ''

    def isEmpty(self) -> bool:
        return len(self._rois) == 0

    def count(self) -> int:
        return len(self._rois)

    def keys(self) -> list[str]:
        return [k.getName() for k in self._rois]

    def remove(self, value: str | int | SisypheROI) -> None:
        # value is SisypheROI
        if isinstance(value, SisypheROI):
            self._rois.remove(value)
        # value is SisypheROI, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or SisypheROI.'.format(type(value)))

    def pop(self, key: str | int | SisypheROI | None = None) -> SisypheROI:
        if key is None: return self._rois.pop()
        # key is Name str or SisypheROI
        if isinstance(key, (str, SisypheROI)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._rois.pop(key)
        else: raise TypeError('parameter type {} is not int, str or SisypheROI.'.format(type(key)))

    def index(self, value: str | SisypheROI) -> int:
        keys = [k.getName() for k in self._rois]
        # value is SisypheROI
        if isinstance(value, SisypheROI):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheROI.'.format(type(value)))

    def reverse(self) -> None:
        self._rois.reverse()

    def append(self, value: SisypheROI) -> None:
        if isinstance(value, SisypheROI):
            self._verifyID(value)
            if value.getName() not in self: self._rois.append(value)
            else: self._rois[self.index(value)] = value
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(value)))

    def insert(self, key: str | int | SisypheROI, value: SisypheROI):
        if isinstance(value, SisypheROI):
            # value is Name str or SisypheROI
            if isinstance(key, (str, SisypheROI)):
                key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._rois):
                    self._verifyID(value)
                    if value.getName() not in self: self._rois.insert(key, value)
                    else: self._rois[self.index(value)] = value
                else: IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(value)))

    def clear(self) -> None:
        self._rois.clear()

    def sort(self, reverse=False):
        def _getName(item):
            return item.getName()

        self._rois.sort(reverse=reverse, key=_getName)

    def copy(self) -> SisypheROICollection:
        rois = SisypheROICollection()
        for roi in self._rois:
            rois.append(roi)
        return rois

    def copyToList(self) -> list[SisypheROI]:
        rois = self._rois.copy()
        return rois

    def getList(self) -> list[SisypheROI]:
        return self._rois

    def resample(self,
                 trf: sc.sisypheTransform.SisypheTransform,
                 save: bool = True,
                 dialog: bool = False,
                 prefix: str | None = None,
                 suffix: str | None = None,
                 wait: DialogWait | None = None):
        if not self.isEmpty():
            if isinstance(trf, sc.sisypheTransform.SisypheTransform):
                f = sc.sisypheTransform.SisypheApplyTransform()
                f.setTransform(trf)
                c = SisypheROICollection()
                for roi in self:
                    f.setMovingROI(roi)
                    c.append(f.resampleROI(save, dialog, prefix, suffix, wait))
                return c
            else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(trf)))
        else: raise ValueError('ROI collection is empty.')

    def toLabelVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            self.sort()
            roi = self[0].getSITKImage()
            for i in range(1, self.count()):
                roi = roi + self[i].getSITKImage() * i
            roi = sitkCast(roi, getLibraryDataType('uint8', 'sitk'))
            rvol = SisypheVolume()
            rvol.setSITKImage(roi)
            rvol.acquisition.setModalityToLB()
            rvol.setID(self[0].getReferenceID())
            for i in range(self.count()):
                name = self[i].getName()
                if name == '': name = 'ROI#{}'.format(i + 1)
                rvol.acquisition.setLabel(i+1, name)
            return rvol

    def fromLabelVolume(self, v: SisypheVolume) -> None:
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self.clear()
                img = v.getSITKImage()
                for i in range(1, 256):
                    r = (img == i)
                    if sitkGetArrayViewFromImage(r).sum() > 0:
                        roi = SisypheROI(r)
                        name = v.acquisition.getLabel(i)
                        if name == '': name = 'ROI#{}'.format(i)
                        roi.setName(name)
                        roi.setReferenceID(v.getID())
                        roi.setFilename(join(v.getDirname(), name + roi.getFileExt()))
                        self.append(roi)
            else: raise ValueError('SisypheVolume {} parameter is not label.'.format(v.getBasename()))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    # IO Public methods

    def load(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        roi = SisypheROI()
                        roi.load(filename)
                        if roi.getName() not in self:
                            self.append(roi)
                            QApplication.processEvents()
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromSisyphe(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        path, ext = splitext(filename)
                        ext = ext.lower()
                        if ext == getSisypheROIExt()[0]:
                            imgs, hdr = readFromSisypheROI(filename)
                            for i in range(len(imgs)):
                                img = flipImageToVTKDirectionConvention(imgs[i])
                                roi = SisypheROI()
                                roi.setName(splitext(basename(filename))[0])
                                roi.setColor(hdr['Red'], hdr['Blue'], hdr['Green'])
                                roi.setAlpha(hdr['Alpha'])
                                roi.setSITKImage(img)
                                roi.setOrigin()
                                roi.setDirections(getRegularDirections())
                                if roi.getName() not in self:
                                    self.append(roi)
                                    QApplication.processEvents()
                        else: raise IOError('{} is not a Sisyphe ROI file extension.'.format(ext))
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromBrainVoyagerVOI(self, vmr: str, filenames: str | list[str]) -> None:
        if exists(vmr):
            path, ext = splitext(vmr)
            ext = ext.lower()
            if ext == getBrainVoyagerVMRExt()[0]:
                hdr, data = read_vmr(vmr)
                vx = hdr['VoxelSizeY']
                vy = hdr['VoxelSizeX']
                vz = hdr['VoxelSizeZ']
                buff = zeros(shape=data.shape, dtype='uint8')
            else: raise IOError('{} is not a BrainVoyager VMR file extension.'.format(ext))
        else: raise IOError('no such file {}.'.format(vmr))
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        path, ext = splitext(filename)
                        ext = ext.lower()
                        if ext == getBrainVoyagerVOIExt()[0]:
                            voi = read_voi(filename)
                            n = voi[0]['NrOfVOIs']
                            for i in range(n):
                                voi = voi[1][i]
                                r = voi['Coordinates'][:, 0]
                                c = voi['Coordinates'][:, 1]
                                buff[r, c] = 1
                                img = sitkGetImageFromArray(buff.T)
                                img.SetSpacing((vx, vy, vz))
                                roi = SisypheROI()
                                roi.setSITKImage(img)
                                roi.setColor(rgb=voi[ColorOfVOI])
                                roi.setName(voi['NameOfVOI'])
                                roi.setOrigin()
                                roi.setDirections(getRegularDirections())
                                if roi.getName() not in self:
                                    self.append(roi)
                                    QApplication.processEvents()
                        else: raise IOError('{} is not a BrainVoyager VOI file extension.'.format(ext))
                    else: raise IOError('no such file {}.'.format(vmr))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def save(self) -> None:
        if not self.isEmpty():
            for roi in self:
                if roi.hasFilename(): roi.save()


class SisypheROIDraw(object):
    """
        SisypheROIDraw class

        Description

            Processing class for SisypheROI instances with undo/redo management
            2D/3D morphology operators, thresholding, region growing, flip/shift, active contour

        Inheritance

            object -> SisypheROIDraw

        Private attributes

            _volume         SisypheVolume
            _gradient       sitkImage
            _mask
            _roi            SisypheROI
            _brush          numpy array, disk brush
            _vbrush         numpy array, ball brush
            _undo           bool
            _undolifo       deque
            _redolifo       deque
            _radius         int         Brush radius (pixel unit)
            _brushtype      int         Brush shape
            _morphradius                Structuring element radius (pixel unit)
            _struct         int         Structuring element shape (ball, box, cross, annulus)
            _thickness      float       Default expand/shrink thickness (mm)
            _thresholdmin   float
            _thresholdmax   float
            _clipboard      sitkImage

        Public methods

            setVolume(SisypheVolume)
            SisypheVolume = getVolume()
            bool = hasVolume()
            setROI(SisypheROI)
            SisypheROI = getROI()
            bool = hasROI()
            str = getBrushType()                    str = 'solid' or 'threshold' or 'gradient'
            setBrushType(str)                       str = 'solid' or 'threshold' or 'gradient'
            getBrushRadius(int)
            int = setBrushRadius()
            setStructElement(str)
            str = getStructElement()
            setMorphologyRadius(int)
            int = getMorphologyRadius()
            setThickness(float)
            float = getThickness()
            float = getThresholdMin()
            setThresholdMin(float)
            float = getThresholdMax()
            setThresholdMax(float)
            float, float = getThresholds()
            setThresholds(float, float)
            bool = hasThresholds()
            setFullRangeThreshold()
            setOtsuThreshold()
            setMeanThreshold()
            clearClipboard()
            setUndoOn()
            setUndoOff()
            setUndo(bool)
            bool = getUndo()
            appendZSliceToLIFO(int, int)            slice number, pile functype (default 0 = UNDO or 1 = REDO)
            appendYSliceToLIFO(int)                 slice number, pile functype (default 0 = UNDO or 1 = REDO)
            appendXSliceToLIFO(int)                 slice number, pile functype (default 0 = UNDO or 1 = REDO)
            appendSliceToLIFO(int, int)             slice number, slice dimension (0, 1 or 2),
                                                    pile functype (default 0 = UNDO or 1 = REDO)
            appendVolumeToLIFO(int)                 pile functype (0 = UNDO, 1 = REDO)
            popUndoLIFO()
            popRedoLIFO()
            clearLIFO()
            brush(int, int, int ,int)               apply brush to coordinate x, y, z, slice dimension (0, 1 or 2)
            erase(int, int, int, int)               apply brush to coordinate x, y, z, slice dimension (0, 1 or 2)
            solidBrush(int, int, int, int)          apply brush to coordinate x, y, z, slice dimension (0, 1 or 2)
            thresholdBrush(int, int, int, int)      apply brush to coordinate x, y, z, slice dimension (0, 1 or 2)
            flipSlice(int, int, bool, bool)         slice number, slice orientation (0, 1 or 2), flip x and y ? (bool)
            moveSlice(int, int, int, int)           slice number, slice orientation (0, 1 or 2), move x and y
            morphoSliceDilate(int, int, int)        slice number, slice orientation (0, 1 or 2), radius (nb of pixels)
            morphoSliceErode(int, int, int)         slice number, slice orientation (0, 1 or 2), radius (nb of pixels)
            morphoSliceOpening(int, int, int)       slice number, slice orientation (0, 1 or 2), radius (nb of pixels)
            morphoSliceClosing(int, int, int)       slice number, slice orientation (0, 1 or 2), radius (nb of pixels)
            morphoSliceBlobDilate(int, int, int, int, int, int)
            morphoSliceBlobErode(int, int, int, int, int, int)
            morphoSliceBlobOpening(int, int, int, int, int, int)
            morphoSliceBlobClosing(int, int, int, int, int, int)
            fillHolesSlice(int, int)                slice number, slice orientation (0, 1 or 2)
            fillHolesAllSlices(int)                 slice orientation (0, 1 or 2)
            backgroundSegmentSlice(int, int, str)   slice number, slice orientation (0, 1 or 2), algorithm name
            blobFilterExtentSlice(int, int, int)    slice number, slice orientation (0, 1 or 2), extent (nb of pixels)
            blobSelectSlice(int, int, int, int, int)slice number, slice orientation (0, 1 or 2), coordinate x, y, z
            blobRemoveSlice(int, int, int, int, int)slice number, slice orientation (0, 1 or 2), coordinate x, y, z
            copyBlobSlice(int, int, int, int, int)  slice number, slice orientation (0, 1 or 2), coordinate x, y, z
            cutBlobSlice(int, int, int, int, int)   slice number, slice orientation (0, 1 or 2), coordinate x, y, z
            pasteBlobSlice(int, int, int, int, int) slice number, slice orientation (0, 1 or 2), coordinate x, y, z
            interpolateEmptySlices(int, int)
            interpolateBetweenSlices(int, int, int) slice number inf. and sup., slice orientation (0, 1 or 2)
            extractingValueSlice(int, int, int | float, bool)
            extractingValueBlobSlice(idem, int, int, int)
            thresholdingSlice(int, int, bool)       slice number, slice orientation (0, 1 or 2),
                                                    mask result with previous r (True, False)
            thresholdingBlobSlice(idem, int, int, int)  coordinate x, y, z
            regionGrowingSlice(int, int, int, int, int, bool)
                                                    slice number, slice orientation (0, 1 or 2),
                                                    seed coordinate x, y, z, mask result with previous r (True, False)
            regionGrowingBlobSlice(int, int, int, int, int) idem
            regionGrowingConfidenceSlice()
            regionGrowingConfidenceBlobSlice()
            flip(bool, bool, bool)                  flip x, y and z ? (bool)
            shift(int, int, int)                    shift x, y, and z
            euclideanDilate(float)
            euclideanErode(float)
            morphoDilate(int)                       radius (nb of pixels)
            morphoErode(int)                        radius (nb of pixels)
            morphoOpening(int)                      radius (nb of pixels)
            morphoClosing(int)                      radius (nb of pixels)
            morphoBlobDilate(int, int, int, int)
            morphoBlobErode(int, int, int, int)
            morphoBlobOpening(int, int, int, int)
            morphoBlobClosing(int, int, int, int)
            binaryAND(list)                         list() of SisypheROI
            binaryOR(list)                          list() of SisypheROI
            binaryXOR(list)                         list() of SisypheROI
            binaryNOT()
            binaryNAND(list)                        list() of SisypheROI
            fillHoles()
            backgroundSegment(str)                  algorithm name
            blobFilterExtent(int)                   extent (nb of pixels)
            blobSelect(int, int, int)               coordinate x, y, z
            blobRemove(int, int, int)               coordinate x, y, z
            copyBlob(int, int, int)                 coordinate x, y, z
            cutBlob(int, int, int)                  coordinate x, y, z
            pasteBlob(int, int, int)                coordinate x, y, z
            extractingValue(int | float, bool)      mask result with previous r (True, False)
            extractingValueBlob(int | float, int, int, int)      coordinate x, y, z
            thresholding(bool)                      mask result with previous r (True, False)
            thresholdingBlob(int, int, int)         coordinate x, y, z
            regionGrowing(int, int, int, bool)      coordinate x, y, z, mask result with previous r (True, False)
            regionGrowingBlob(int, int, int)
            regionGrowingConfidence(int, int, int, int, float, bool)
                                                    coordinate x, y, z, niter=4, multi=4.5, radius (nb of pixels),
                                                    mask result with previous r (True, False)
            regionGrowingConfidenceBlob(int, int, int, int, float)
            activeContour()
            getIntensityStatistics()
            getSliceIntensityStatistics()           slice number, slice orientation (0, 1 or 2)
            getShapeStatistics()

        Creation: 08/09/2022
        Revisions:

            22/04/2023  ActiveContour() method bugfix
            01/09/2023  type hinting
            06/09/2023  interpolateBetweenSlices() method bugfix
                        _updateRoiFromSITKImage(), _updateSliceFromSITKImage(),
                        _updateRoiFromNumpy(), _updateSliceFromNumpy() methods, add replace parameter
            11/11/2023  add majorBlobSelect() and majorBlobSelectSlice() methods
                        add maskSegment() and maskSegment2() methods
    """

    __slots__ = {'_volume', '_gradient', '_mask', '_brush', '_vbrush', '_roi', '_undo', '_undolifo', '_redolifo',
                 '_radius', '_morphradius', '_thickness', '_brushtype', '_struct', '_thresholdmin', '_thresholdmax',
                 '_clipboard'}

    # Class constants

    _DV, _DSZ, _DSY, _DSX = 0, 1, 2, 3
    _UNDO, _REDO = 0, 1
    _BRUSHTYPECODE = {'solid': 0, 'threshold': 1, 'solid3': 2, 'threshold3': 3}
    _BRUSHTYPENAME = {0: 'solid', 1: 'threshold', 2: 'solid3', 3: 'threshold3'}
    _MAXRADIUS = 50
    _DEFAULTRADIUS = 2
    _DEFAULTMORPHRADIUS = 1
    _MAXUNDO = 20

    # Special methods

    def __init__(self) -> None:
        self._volume = None
        self._mask = None
        self._brush = None
        self._vbrush = None
        self._roi = None
        self._undo = False
        self._undolifo = deque(maxlen=self._MAXUNDO)
        self._redolifo = deque(maxlen=self._MAXUNDO)
        self._radius = self._DEFAULTRADIUS
        self._brushtype = self._BRUSHTYPECODE['solid']
        self._morphradius = self._DEFAULTMORPHRADIUS
        self._thickness = 0.0
        self._struct = sitkBall
        self._thresholdmin = 0
        self._thresholdmax = 0
        self._clipboard = None
        self._calcBrush()

    def __str__(self) -> str:
        if self.hasVolume():
            buff = 'Volume ID: {}\n'.format(self._volume.getID())
        else: buff = 'Volume: empty\n'
        if self.hasROI():
            buff += 'ROI name: {}\n'.format(self._roi.getName())
        else: buff += 'ROI: empty\n'
        buff += 'Brush functype: {}\n'.format(self._BRUSHTYPENAME[self._brushtype])
        buff += 'Brush radius: {}\n'.format(self._radius)
        buff += 'Threshold inf.: {}\n'.format(self._thresholdmin)
        buff += 'Threshold sup.: {}\n'.format(self._thresholdmax)
        buff += 'Undo flag: {}\n'.format(self._undo)
        buff += 'Undo LIFO elements: {}\n'.format(len(self._undolifo))
        buff += 'Redo LIFO elements: {}\n'.format(len(self._redolifo))
        mem = self.__sizeof__()
        if mem <= 1024: buff += 'Memory Size: {} Bytes\n'.format(mem)
        elif mem <= 1024: buff += 'Memory Size: {:.2f} KB\n'.format(mem/1024)
        else: buff += 'Memory Size: {:.2f} MB\n'.format(mem/1048576)
        return buff

    def __repr__(self) -> str:
        return 'SisypheROIDraw instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Private methods

    def _calcMask(self) -> None:
        # img = self._volume.getNumpy()
        # self._mask = bitwise_and(img > self._thresholdmin,  img < self._thresholdmax).astype('uint8')
        img = sitkThreshold(self._volume.getSITKImage(),
                            lowerThreshold=float(self._thresholdmin),
                            upperThreshold=float(self._thresholdmax))
        self._mask = sitkGetArrayFromImage(img)

    def _calcBrush(self) -> None:
        if self._radius > 1:
            # 2D brush
            s = self._radius * 2 - 1
            shape = (s, s)
            self._brush = zeros(shape, dtype='uint8')
            rr, cc = disk((self._radius - 1, self._radius - 1), self._radius, shape=shape)
            self._brush[rr, cc] = 1
            # 3D brush
            self._vbrush = ellipsoid(self._radius, self._radius, self._radius, (1.0, 1.0, 1.0), False).astype('uint8')
            self._vbrush = self._vbrush[2:-2, 2:-2, 2:-2]
        else:
            self._brush = None
            self._vbrush = None

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self.setFullRangeThreshold()
            if self.hasROI():
                if self._roi.getReferenceID() != self._volume.getID(): self._roi = None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        return self._volume

    def hasVolume(self) -> bool:
        return self._volume is not None

    def setROI(self, roi: SisypheROI) -> None:
        if isinstance(roi, SisypheROI):
            if self.hasVolume:
                if roi.getReferenceID() == self._volume.getID():
                    self._roi = roi
                    self._roi.setOrigin(self._volume.getOrigin())
                    self._roi.setDirections(self._volume.getDirections())
                    if self._undo: self.clearLIFO()
                else: raise ValueError('SisypheROI ID conflicting with SisypheVolume ID.')
            else: raise ValueError('SisypheVolume attribute is empty.')
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def getROI(self) -> SisypheROI:
        return self._roi

    def hasROI(self) -> bool:
        return self._roi is not None

    def removeROI(self) -> None:
        self._roi = None
        self.clearLIFO()

    def getBrushType(self) -> str:
        return self._BRUSHTYPENAME[self._brushtype]

    def setBrushType(self, brushtype: int | str) -> None:
        # brush type = 'solid', 'threshold', 'solid3', 'threshold3'
        if isinstance(brushtype, str):
            if brushtype in self._BRUSHTYPECODE: self._brushtype = self._BRUSHTYPECODE[brushtype]
            else: self._brushtype = self._BRUSHTYPECODE['solid']
        elif isinstance(brushtype, int):
            if 0 <= brushtype < 3: self._brushtype = brushtype
            else: self._brushtype = self._BRUSHTYPECODE['solid']

    def setBrushRadius(self, radius: int) -> None:
        if isinstance(radius, int):
            self._radius = radius
            if self._radius < 0: self._radius = 0
            if self._radius > self._MAXRADIUS: self._radius = self._MAXRADIUS
            self._calcBrush()
        else:
            raise TypeError('parameter type {} is not int.'.format(type(radius)))

    def getBrushRadius(self) -> int:
        return self._radius

    def setStructElement(self, struct: str) -> None:
        if isinstance(struct, str):
            if struct in ('ball', 'box', 'cross', 'annulus'):
                if struct == 'ball': self._struct = sitkBall
                elif struct == 'box': self._struct = sitkBox
                elif struct == 'cross': self._struct = sitkCross
                else: self._struct = sitkAnnulus
            else: raise ValueError('parameter value {} is not valid.'.format(struct))
        else: raise TypeError('parameter type {} is not str.'.format(type(struct)))

    def getStructElement(self) -> str:
        if self._struct == sitkBall: return 'ball'
        elif self._struct == sitkBox: return 'box'
        elif self._struct == sitkCross: return 'cross'
        else: return 'annulus'

    def setMorphologyRadius(self, radius: float) -> None:
        if isinstance(radius, (int, float)):
            if radius <= 0.0: radius = 1.0
            if radius > 20.0: radius = 20.0
            self._morphradius = radius
        else: raise TypeError('parameter type {} is not int or float.'.format(type(radius)))

    def getMorphologyRadius(self) -> float:
        return self._morphradius

    def getThickness(self) -> float:
        return self._thickness

    def setThickness(self, mm: float) -> None:
        if isinstance(mm, float):
            if 0.0 < mm <= 50.0: self._thickness = mm
            else: raise ValueError('parameter value {} is out of range (0.0 to 50.0 mm).'.format(mm))
        else: raise TypeError('parameter type {} is not float.'.format(mm))

    def getThresholdMin(self) -> float:
        return self._thresholdmin

    def getThresholdMax(self) -> float:
        return self._thresholdmax

    def getThresholds(self) -> tuple[float, float]:
        return self._thresholdmin, self._thresholdmax

    def setThresholdMin(self, vmin: float) -> None:
        if isinstance(vmin, (int, float)):
            self._thresholdmin = vmin
            if self._thresholdmin > self._thresholdmax:
                self._thresholdmax = self._thresholdmin
            self._calcMask()
        else: raise TypeError('parameter type {} is not int or float.'.format(type(vmin)))

    def setThresholdMax(self, vmax: float) -> None:
        if isinstance(vmax, (int, float)):
            self._thresholdmax = vmax
            if self._thresholdmax < self._thresholdmin:
                self._thresholdmin = self._thresholdmax
            self._calcMask()
        else: raise TypeError('parameter type {} is not int or float.'.format(type(vmax)))

    def setThresholds(self, vmin: float, vmax: float) -> None:
        if isinstance(vmax, (int, float)) and isinstance(vmin, (int, float)):
            if vmin > vmax: vmin, vmax = vmax, vmin
            self._thresholdmin = vmin
            self._thresholdmax = vmax
            self._calcMask()

    def hasThresholds(self) -> bool:
        return self._thresholdmax > 0

    def setFullRangeThreshold(self) -> None:
        self._thresholdmin = self._volume.getDisplay().getRangeMin()
        self._thresholdmax = self._volume.getDisplay().getRangeMax()

    def setOtsuThreshold(self, background: bool = False) -> None:
        simg = self._volume.getSITKImage()
        otsu = sitkOtsuThresholdImageFilter()
        otsu.SetInsideValue(0)
        otsu.SetOutsideValue(1)
        self._mask = otsu.Execute(simg)
        if background:
            self._thresholdmin = self._volume.getDisplay().getRangeMin()
            self._thresholdmax = otsu.GetThreshold()
        else:
            self._thresholdmin = otsu.GetThreshold()
            self._thresholdmax = self._volume.getDisplay().getRangeMax()

    def setMeanThreshold(self, background: bool = False) -> None:
        mean = int(self._volume.getNumpy().mean())
        if background:
            self._thresholdmin = self._volume.getDisplay().getRangeMin()
            self._thresholdmax = mean
        else:
            self._thresholdmin = mean
            self._thresholdmax = self._volume.getDisplay().getRangeMax()
        self._calcMask()

    def clearClipboard(self) -> None:
        if self._clipboard is not None:
            del self._clipboard
            self._clipboard = None

    # Undo/redo

    def setUndoOn(self) -> None:
        self.setUndo(True)

    def setUndoOff(self) -> None:
        self.setUndo(False)

    def setUndo(self, v: bool) -> None:
        if isinstance(v, bool):
            self._undo = v
            self.clearLIFO()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getUndo(self) -> bool:
        return self._undo

    def appendZSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        if 0 <= i < self._roi.getSize()[2]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[i, :, :].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSZ, i, buff))
            else: self._redolifo.append((self._DSZ, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendYSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        if 0 <= i < self._roi.getSize()[1]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[:, i, :].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSY, i, buff))
            else: self._redolifo.append((self._DSY, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendXSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        if 0 <= i < self._roi.getSize()[0]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[:, :, i].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSX, i, buff))
            else: self._redolifo.append((self._DSY, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendSliceToLIFO(self, i: int, dim, pile: int = _UNDO) -> None:
        if self._undo:
            if dim == 0: self.appendZSliceToLIFO(i, pile)
            elif dim == 1: self.appendYSliceToLIFO(i, pile)
            else: self.appendXSliceToLIFO(i, pile)

    def appendVolumeToLIFO(self, pile: int = _UNDO) -> None:
        if self._undo and self.hasROI():
            buff = sparse.csr_matrix(self._roi.getNumpy().copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DV, None, buff))
            else: self._redolifo.append((self._DV, None, buff))

    def popUndoLIFO(self) -> None:
        if len(self._undolifo) > 0:
            if len(self._undolifo) > 1: self._undolifo.pop()
            item = self._undolifo[len(self._undolifo) - 1]
            sx, sy, sz = self._roi.getSize()
            if item[0] == self._DV:
                self.appendVolumeToLIFO(pile=self._REDO)
                buff = item[2].toarray().reshape(sz, sy, sx)
                self._roi.getNumpy()[:, :, :] = buff
            elif item[0] == self._DSZ:
                self.appendZSliceToLIFO(item[1], pile=self._REDO)
                buff = item[2].toarray().reshape(sy, sx)
                self._roi.getNumpy()[item[1], :, :] = buff
            elif item[0] == self._DSY:
                self.appendYSliceToLIFO(item[1], pile=self._REDO)
                buff = item[2].toarray().reshape(sz, sx)
                self._roi.getNumpy()[:, item[1], :] = buff
            elif item[0] == self._DSX:
                self.appendXSliceToLIFO(item[1], pile=self._REDO)
                buff = item[2].toarray().reshape(sz, sy)
                self._roi.getNumpy()[:, :, item[1]] = buff

    def popRedoLIFO(self) -> None:
        if len(self._redolifo) > 0:
            item = self._redolifo.pop()
            sx, sy, sz = self._roi.getSize()
            if item[0] == self._DV:
                self.appendVolumeToLIFO(pile=self._UNDO)
                buff = item[2].toarray().reshape(sz, sy, sx)
                self._roi.getNumpy()[:, :, :] = buff
            elif item[0] == self._DSZ:
                self.appendZSliceToLIFO(item[1], pile=self._UNDO)
                buff = item[2].toarray().reshape(sy, sx)
                self._roi.getNumpy()[item[1], :, :] = buff
            elif item[0] == self._DSY:
                self.appendYSliceToLIFO(item[1], pile=self._UNDO)
                buff = item[2].toarray().reshape(sz, sx)
                self._roi.getNumpy()[:, item[1], :] = buff
            elif item[0] == self._DSX:
                self.appendXSliceToLIFO(item[1], pile=self._UNDO)
                buff = item[2].toarray().reshape(sz, sy)
                self._roi.getNumpy[:, :, item[1]] = buff

    def clearLIFO(self) -> None:
        self._undolifo.clear()
        self.appendVolumeToLIFO()
        self._redolifo.clear()

    # Brush

    def brush(self, x: int, y: int, z: int, dim: int) -> None:
        if self.hasROI():
            if self._brushtype == self._BRUSHTYPECODE['solid']: self.solidBrush(x, y, z, 1, dim)
            elif self._brushtype == self._BRUSHTYPECODE['threshold']: self.thresholdBrush(x, y, z, dim)
            elif self._brushtype == self._BRUSHTYPECODE['solid3']: self.solid3DBrush(x, y, z)
            else: self.threshold3DBrush(x, y, z)

    def erase(self, x: int, y: int, z: int, dim: int) -> None:
        if self.hasROI():
            if self._brushtype < self._BRUSHTYPECODE['solid3']: self.solidBrush(x, y, z, 0, dim)
            else: self.solid3DBrush(x, y, z, 0)

    def solidBrush(self, x: int, y: int, z: int, c: int, dim: int) -> None:
        if self._radius in (0, 1):
            self._roi.getSITKImage()[x, y, z] = c
        else:
            xmax, ymax, zmax = self._roi.getSize()
            if dim == 0:
                if 0 <= x < xmax and 0 <= y < ymax:
                    idx1 = self._radius - 1 - x
                    idy1 = self._radius - 1 - y
                    idx2 = xmax - x - self._radius
                    idy2 = ymax - y - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    m = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    brush = self._brush[idy1:idy2, idx1:idx2]
                    dy, dx = brush.shape
                    x2 = x + dx
                    y2 = y + dy
                    back = self._roi.getNumpy()[z, y:y2, x:x2]
                    if c == 1: self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_and(back, invert(brush))
            elif dim == 1:
                if 0 <= x < xmax and 0 <= z < zmax:
                    idx1 = self._radius - 1 - x
                    idz1 = self._radius - 1 - z
                    idx2 = xmax - x - self._radius
                    idz2 = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    m = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idx1:idx2]
                    dz, dx = brush.shape
                    x2 = x + dx
                    z2 = z + dz
                    back = self._roi.getNumpy()[z:z2, y, x:x2]
                    if c == 1: self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_and(back, invert(brush))
            else:
                if 0 <= y < ymax and 0 <= z < zmax:
                    idy1 = self._radius - 1 - y
                    idz1 = self._radius - 1 - z
                    idy2 = ymax - y - self._radius
                    idz2 = zmax - z - self._radius
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    m = 2 * self._radius - 1
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idy1:idy2]
                    dz, dy = brush.shape
                    y2 = y + dy
                    z2 = z + dz
                    back = self._roi.getNumpy()[z:z2, y:y2, x]
                    if c == 1: self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_and(back, invert(brush))

    def thresholdBrush(self, x: int, y: int, z: int, dim: int) -> None:
        if not self.hasThresholds(): self.solidBrush(x, y, z, 1, dim)
        else:
            if self._radius in (0, 1):
                if self._thresholdmin <= self._volume.getSITKImage()[x, y, z] <= self._thresholdmax:
                    self._roi.getSITKImage()[x, y, z] = 1
            else:
                xmax, ymax, zmax = self._roi.getSize()
                if dim == 0:
                    idx1 = self._radius - 1 - x
                    idy1 = self._radius - 1 - y
                    idx2 = xmax - x - self._radius
                    idy2 = ymax - y - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    m = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    brush = self._brush[idy1:idy2, idx1:idx2]
                    dy, dx = brush.shape
                    x2 = x + dx
                    y2 = y + dy
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z, y:y2, x:x2], brush)
                    back = self._roi.getNumpy()[z, y:y2, x:x2]
                    self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_or(back, brush)
                elif dim == 1:
                    idx1 = self._radius - 1 - x
                    idz1 = self._radius - 1 - z
                    idx2 = xmax - x - self._radius
                    idz2 = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    m = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idx1:idx2]
                    dz, dx = brush.shape
                    x2 = x + dx
                    z2 = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y, x:x2], brush)
                    back = self._roi.getNumpy()[z:z2, y, x:x2]
                    self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_or(back, brush)
                else:
                    idy1 = self._radius - 1 - y
                    idz1 = self._radius - 1 - z
                    idy2 = ymax - y - self._radius
                    idz2 = zmax - z - self._radius
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    m = 2 * self._radius - 1
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idy1:idy2]
                    dz, dy = brush.shape
                    y2 = y + dy
                    z2 = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y:y2, x], brush)
                    back = self._roi.getNumpy()[z:z2, y:y2, x]
                    self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_or(back, brush)

    def solid3DBrush(self, x: int, y: int, z: int, c: int = 1) -> None:
        if self._radius in (0, 1):
            self._roi.getSITKImage()[x, y, z] = c
        else:
            xmax, ymax, zmax = self._roi.getSize()
            if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
                idx1 = self._radius - 1 - x
                idy1 = self._radius - 1 - y
                idz1 = self._radius - 1 - z
                idx2 = xmax - x - self._radius
                idy2 = ymax - y - self._radius
                idz2 = zmax - z - self._radius
                if idx1 < 0: x, idx1 = -idx1, 0
                else: x = 0
                if idy1 < 0: y, idy1 = -idy1, 0
                else: y = 0
                if idz1 < 0: z, idz1 = -idz1, 0
                else: z = 0
                m = 2 * self._radius - 1
                if idx2 > -1: idx2 = m
                if idy2 > -1: idy2 = m
                if idz2 > -1: idz2 = m
                brush = self._vbrush[idz1:idz2, idy1:idy2, idx1:idx2]
                dz, dy, dx = brush.shape
                x2 = x + dx
                y2 = y + dy
                z2 = z + dz
                back = self._roi.getNumpy()[z:z2, y:y2, x:x2]
                if c == 1: self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_or(back, brush)
                else: self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_and(back, invert(brush))

    def threshold3DBrush(self, x: int, y: int, z: int) -> None:
        if not self.hasThresholds(): self.solid3DBrush(x, y, z, 1)
        else:
            if self._radius in (0, 1):
                if self._thresholdmin <= self._volume.getSITKImage()[x, y, z] <= self._thresholdmax:
                    self._roi.getSITKImage()[x, y, z] = 1
            else:
                xmax, ymax, zmax = self._roi.getSize()
                if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
                    idx1 = self._radius - 1 - x
                    idy1 = self._radius - 1 - y
                    idz1 = self._radius - 1 - z
                    idx2 = xmax - x - self._radius
                    idy2 = ymax - y - self._radius
                    idz2 = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    m = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._vbrush[idz1:idz2, idy1:idy2, idx1:idx2]
                    dz, dy, dx = brush.shape
                    x2 = x + dx
                    y2 = y + dy
                    z2 = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y:y2, x:x2], brush)
                    back = self._roi.getNumpy()[z:z2, y:y2, x:x2]
                    self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_or(back, brush)

    # Update and extract slices from volume

    def _updateRoiFromSITKImage(self, img: sitkImage, replace: bool = True) -> None:
        npimg = sitkGetArrayViewFromImage(img)
        self._updateRoiFromNumpy(npimg, replace)

    def _updateSliceFromSITKImage(self, img: sitkImage, sindex: int, dim: int, replace: bool = True) -> None:
        npimg = sitkGetArrayViewFromImage(img)
        self._updateSliceFromNumpy(npimg, sindex, dim, replace)

    def _updateRoiFromNumpy(self, img: np_ndarray, replace: bool = True) -> None:
        if not replace: img = self._roi.getNumpy() | img
        self._roi.getNumpy()[:] = img[:]

    def _updateSliceFromNumpy(self, img: np_ndarray, sindex: int, dim: int, replace: bool = True):
        dz, dy, dx = self._roi.getNumpy().shape
        if dim == 0:
            if 0 <= sindex < dz:
                if not replace: img = self._roi.getNumpy()[sindex, :, :] | img
                self._roi.getNumpy()[sindex, :, :] = img[:]  # numpy z, y, x
            else: raise IndexError('slice index is out of range.')
        elif dim == 1:
            if 0 <= sindex < dy:
                if not replace: img = self._roi.getNumpy()[:, sindex, :] | img
                self._roi.getNumpy()[:, sindex, :] = img[:]  # numpy z, y, x
            else: raise IndexError('slice index is out of range.')
        else:
            if 0 <= sindex < dx:
                if not replace: img = self._roi.getNumpy()[:, :, sindex] | img
                self._roi.getNumpy()[:, :, sindex] = img[:]  # numpy z, y, x
            else: raise IndexError('slice index is out of range.')

    def _extractSITKSlice(self, sindex: int, dim: int, roi: bool = True) -> sitkImage:
        dz, dy, dx = self._roi.getNumpy().shape
        if dim == 0:
            if 0 <= sindex < dz:
                if roi: return self._roi.getSITKImage()[:, :, sindex]
                else: return self._volume.getSITKImage()[:, :, sindex]
            else: raise IndexError('slice index is out of range.')
        elif dim == 1:
            if 0 <= sindex < dy:
                if roi: return self._roi.getSITKImage()[:, sindex, :]
                else: return self._volume.getSITKImage()[:, sindex, :]
            else: raise IndexError('slice index is out of range.')
        else:
            if 0 <= sindex < dx:
                if roi: return self._roi.getSITKImage()[sindex, :, :]
                else: return self._volume.getSITKImage()[sindex, :, :]
            else: raise IndexError('slice index is out of range.')

    # Slice processing

    def flipSlice(self, sindex: int, dim: int, flipx: bool, flipy: bool) -> None:
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkFlip(img, [flipx, flipy])
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def shiftSlice(self, sindex: int, dim: int, movex: int, movey: int) -> None:
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkShift(img, [movex, movey])
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def copySlice(self, sindex: int, dim: int) -> None:
        self._clipboard = self._extractSITKSlice(sindex, dim)

    def cutSlice(self, sindex: int, dim: int) -> None:
        self._clipboard = self._extractSITKSlice(sindex, dim)
        self.clearSlice(sindex, dim)
        if self._undo: self.appendSliceToLIFO(sindex, dim)

    def pasteSlice(self, sindex: int, dim: int) -> None:
        if self._clipboard is not None and self._clipboard.GetDimension() == 2:
            self._updateSliceFromSITKImage(self._clipboard, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceDilate(self,
                          sindex: int,
                          dim: int,
                          radius: int | None = None,
                          struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryDilate(img, [radius, radius], struct)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceErode(self,
                         sindex: int,
                         dim: int,
                         radius: int | None = None,
                         struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryErode(img, [radius, radius], struct)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceOpening(self,
                           sindex: int,
                           dim: int,
                           radius: int | None = None,
                           struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryOpening(img, [radius, radius], struct)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceClosing(self,
                           sindex: int,
                           dim: int,
                           radius: int | None = None,
                           struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryClosing(img, [radius, radius], struct)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceBlobDilate(self,
                              sindex: int,
                              dim: int,
                              x: int, y: int, z: int,
                              radius: int | None = None,
                              struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                img = self._extractSITKSlice(sindex, dim)
                cc = sitkConnectedComponent(img)
                if dim == 0: c = cc[x, y]
                elif dim == 1: c = cc[x, z]
                else: c = cc[y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ img
                    img = sitkBinaryDilate(img1, [radius, radius], struct) | img2
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceBlobErode(self,
                             sindex: int,
                             dim: int,
                             x: int, y: int, z: int,
                             radius: int | None = None,
                             struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                img = self._extractSITKSlice(sindex, dim)
                cc = sitkConnectedComponent(img)
                if dim == 0: c = cc[x, y]
                elif dim == 1: c = cc[x, z]
                else: c = cc[y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ img
                    img = sitkBinaryErode(img1, [radius, radius], struct) | img2
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceBlobOpening(self,
                               sindex: int,
                               dim: int,
                               x: int, y: int, z: int,
                               radius: int | None = None,
                               struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                img = self._extractSITKSlice(sindex, dim)
                cc = sitkConnectedComponent(img)
                if dim == 0: c = cc[x, y]
                elif dim == 1: c = cc[x, z]
                else: c = cc[y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ img
                    img = sitkBinaryOpening(img1, [radius, radius], struct) | img2
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceBlobClosing(self,
                               sindex: int,
                               dim: int,
                               x: int, y: int, z: int,
                               radius: int | None = None,
                               struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                img = self._extractSITKSlice(sindex, dim)
                cc = sitkConnectedComponent(img)
                if dim == 0: c = cc[x, y]
                elif dim == 1: c = cc[x, z]
                else: c = cc[y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ img
                    img = sitkBinaryClosing(img1, [radius, radius], struct) | img2
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def fillHolesSlice(self, sindex: int, dim: int, undo: bool | None = None):
        if self.hasROI():
            if undo is None: undo = self._undo
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryFillHole(img)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if undo: self.appendSliceToLIFO(sindex, dim)

    def fillHolesAllSlices(self, dim: int) -> None:
        if self.hasROI():
            dz, dy, dx = self._roi.getNumpy().shape
            if dim == 0: d = dz
            elif dim == 1: d = dy
            else: d = dx
            for i in range(0, d):
                self.fillHolesSlice(i, dim, False)
            if self._undo: self.appendVolumeToLIFO()

    def seedFillSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] == 0:
                if dim == 0: xs, ys = x, y
                elif dim == 1: xs, ys = x, z
                else:  xs, ys = y, z
                img = self._extractSITKSlice(sindex, dim)
                np = sitkGetArrayViewFromImage(img)
                np = flood(np, (ys, xs)).astype('uint8')
                fill = sitkGetImageFromArray(np)
                fill.SetOrigin(img.GetOrigin())
                fill.SetDirection(img.GetDirection())
                img = img | fill
                self._updateSliceFromSITKImage(img, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    def seedFill(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] == 0:
                np = self._roi.getNumpy()
                np = flood(np, (z, y, x)).astype('uint8')
                fill = sitkGetImageFromArray(np)
                fill.SetOrigin(self._roi.getSITKImage().GetOrigin())
                fill.SetDirection(self._roi.getSITKImage().GetDirection())
                img = self._roi.getSITKImage() | fill
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def clearSlice(self, sindex: int, dim: int) -> None:
        img = self._extractSITKSlice(sindex, dim)
        img = sitkImage(img.GetSize(), sitkUInt8)
        self._updateSliceFromSITKImage(img, sindex, dim)
        if self._undo: self.appendSliceToLIFO(sindex, dim)

    def binaryNotSlice(self, sindex: int, dim: int) -> None:
        if self.hasROI():
            img = sitkBinaryNot(self._extractSITKSlice(sindex, dim))
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def objectSegmentSlice(self, sindex: int, dim: int, algo: str = 'otsu') -> None:
        if self.hasVolume() and self.hasROI():
            img = self._extractSITKSlice(sindex, dim, roi=False)
            if algo == 'otsu': img = sitkOtsu(img)
            elif algo == 'huang': img = sitkHuang(img)
            elif algo == 'renyi': img = sitkRenyi(img)
            elif algo == 'yen': img = sitkYen(img)
            elif algo == 'li': img = sitkLi(img)
            elif algo == 'shanbhag': img = sitkShanbhag(img)
            elif algo == 'triangle': img = sitkTriangle(img)
            elif algo == 'intermodes': img = sitkIntermodes(img)
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(img)
            elif algo == 'kittler': img = sitkKittler(img)
            elif algo == 'isodata': img = sitkIsoData(img)
            elif algo == 'moments': img = sitkMoments(img)
            elif algo == 'mean':
                v = sitkGetArrayViewFromImage(img).mean()
                img = (img <= v)
            else: raise ValueError('unknown algorithm parameter.')
            img = sitkBinaryNot(img)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def backgroundSegmentSlice(self, sindex: int, dim: int, algo: str = 'otsu') -> None:
        if self.hasVolume() and self.hasROI():
            img = self._extractSITKSlice(sindex, dim, roi=False)
            if algo == 'otsu': img = sitkOtsu(img)
            elif algo == 'huang': img = sitkHuang(img)
            elif algo == 'renyi': img = sitkRenyi(img)
            elif algo == 'yen': img = sitkYen(img)
            elif algo == 'li': img = sitkLi(img)
            elif algo == 'shanbhag': img = sitkShanbhag(img)
            elif algo == 'triangle': img = sitkTriangle(img)
            elif algo == 'intermodes': img = sitkIntermodes(img)
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(img)
            elif algo == 'kittler': img = sitkKittler(img)
            elif algo == 'isodata': img = sitkIsoData(img)
            elif algo == 'moments': img = sitkMoments(img)
            elif algo == 'mean':
                v = sitkGetArrayViewFromImage(img).mean()
                img = (img <= v)
            else: raise ValueError('unknown algorithm parameter.')
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def blobFilterExtentSlice(self, sindex: int, dim: int, n: int) -> None:
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkConnectedComponent(img)
            img = sitkRelabelComponent(img, minimumObjectSize=n)
            img = (img > 0)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def majorBlobSelectSlice(self, sindex: int, dim: int):
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkConnectedComponent(img)
            img = sitkRelabelComponent(img, sortByObjectSize=True)
            img = (img == 1)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def blobSelectSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._extractSITKSlice(sindex, dim)
                cimg = sitkConnectedComponent(img)
                if dim == 0: c = cimg[x, y]
                elif dim == 1: c = cimg[x, z]
                else: c = cimg[y, z]
                if c > 0:
                    img = (cimg == c)
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def blobRemoveSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._extractSITKSlice(sindex, dim)
                cimg = sitkConnectedComponent(img)
                if dim == 0: c = cimg[x, y]
                elif dim == 1: c = cimg[x, z]
                else: c = cimg[y, z]
                if c > 0:
                    img = (cimg != c) & img
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def copyBlobSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._extractSITKSlice(sindex, dim)
                cimg = sitkConnectedComponent(img)
                if dim == 0: c = cimg[x, y]
                elif dim == 1: c = cimg[x, z]
                else: c = cimg[y, z]
                if c > 0:
                    img = (cimg == c)
                    filtr = sitkLabelShapeStatisticsImageFilter()
                    filtr.Execute(img)
                    if filtr.GetNumberOfLabels() > 0:
                        x0, y0, dx, dy = filtr.GetBoundingBox(1)
                        self._clipboard = img[x0:x0+dx, y0:y0+dy]

    def cutBlobSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._extractSITKSlice(sindex, dim)
                cimg = sitkConnectedComponent(img)
                if dim == 0: c = cimg[x, y]
                elif dim == 1: c = cimg[x, z]
                else: c = cimg[y, z]
                if c > 0:
                    img = (cimg == c)
                    filtr = sitkLabelShapeStatisticsImageFilter()
                    filtr.Execute(img)
                    if filtr.GetNumberOfLabels() > 0:
                        x0, y0, dx, dy = filtr.GetBoundingBox(1)
                        self._clipboard = img[x0:x0+dx, y0:y0+dy]
                        img = self._extractSITKSlice(sindex, dim) - img
                        self._updateSliceFromSITKImage(img, sindex, dim)
                        if self._undo: self.appendSliceToLIFO(sindex, dim)

    def pasteBlobSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self._clipboard is not None:
            if self.hasROI():
                if self._clipboard is not None and self._clipboard.GetDimension() == 2:
                    img = self._extractSITKSlice(sindex, dim)
                    if dim == 0:
                        img = Paste(img,
                                    self._clipboard,
                                    self._clipboard.GetSize(),
                                    (0, 0), (x, y))
                    elif dim == 1:
                        img = Paste(img,
                                    self._clipboard,
                                    self._clipboard.GetSize(),
                                    (0, 0), (x, z))
                    else:
                        img = Paste(img,
                                    self._clipboard,
                                    self._clipboard.GetSize(),
                                    (0, 0), (y, z))
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def interpolateEmptySlices(self, sindex: int, dim: int) -> None:
        if self.hasROI():
            size = self._roi.getSize()[2 - dim]
            tindex = sindex
            bindex = sindex
            index = sindex + 1
            # Search first non-empty slice above reference slice
            while index < size:
                if dim == 0: csum = self._roi.getNumpy()[index, :, :].sum()
                elif dim == 1: csum = self._roi.getNumpy()[:, index, :].sum()
                else: csum = self._roi.getNumpy()[:, :, index].sum()
                if csum > 0:
                    tindex = index - 1
                    break
                index += 1
            index = sindex - 1
            # Search first non-empty slice below reference slice
            while index >= 0:
                if dim == 0: csum = self._roi.getNumpy()[index, :, :].sum()
                elif dim == 1: csum = self._roi.getNumpy()[:, index, :].sum()
                else: csum = self._roi.getNumpy()[:, :, index].sum()
                if csum > 0:
                    bindex = index + 1
                    break
                index -= 1
            # Interpolate above
            if tindex > sindex: self.interpolateBetweenSlices(sindex, tindex, dim)
            # Interpolate below
            if bindex < sindex: self.interpolateBetweenSlices(bindex, sindex, dim)

    def interpolateBetweenSlices(self, sindex1: int, sindex2: int, dim: int, replace=False) -> None:
        if self.hasROI():
            if sindex1 > sindex2: sindex1, sindex2 = sindex2, sindex1
            n = sindex2 - sindex1
            if n > 1:
                if not self._roi.sliceIsEmpty((sindex1, sindex2), dim):
                    # Extract slices
                    img1 = self._extractSITKSlice(sindex1, dim)
                    img2 = self._extractSITKSlice(sindex2, dim)
                    # Chamfer distance
                    img1 = sitkDistanceMap(img1)
                    img2 = sitkDistanceMap(img2)
                    # Linear interpolation between img1 and img2
                    step = (img2 - img1) / n
                    for i in range(1, n):
                        img1 = img1 + sitkCast(step * i, sitkFloat32)
                        img = img1 <= 0
                        self._updateSliceFromSITKImage(img, sindex1 + i, dim, replace=False)
                    if self._undo: self.appendVolumeToLIFO()

    def extractingValueSlice(self,
                             sindex: int,
                             dim: int,
                             value: float,
                             mask: bool = False,
                             replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            roi = img == value
            if mask: roi = roi & self._extractSITKSlice(sindex, dim)
            if not replace: roi = roi | roi1
            self._updateSliceFromSITKImage(roi, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def extractingValueBlobSlice(self, sindex: int, dim: int, value: float, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._extractSITKSlice(sindex, dim, roi=True)
                img = self._extractSITKSlice(sindex, dim, roi=False)
                cc = sitkConnectedComponent(roi1)
                if dim == 0: mask = (cc == cc[x, y])
                elif dim == 1: mask = (cc == cc[x, z])
                else: mask = (cc == cc[y, z])
                roi1 = roi1 ^ mask
                roi = img == value
                roi = (roi & mask) | roi1
                self._updateSliceFromSITKImage(roi, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    def thresholdingSlice(self, sindex: int, dim: int, mask: bool = False, replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            roi = sitkThreshold(img,
                                lowerThreshold=float(self._thresholdmin),
                                upperThreshold=float(self._thresholdmax))
            if mask: roi = roi & self._extractSITKSlice(sindex, dim)
            if not replace: roi = roi | roi1
            self._updateSliceFromSITKImage(roi, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def thresholdingBlobSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._extractSITKSlice(sindex, dim, roi=True)
                img = self._extractSITKSlice(sindex, dim, roi=False)
                cc = sitkConnectedComponent(roi1)
                if dim == 0: mask = (cc == cc[x, y])
                elif dim == 1: mask = (cc == cc[x, z])
                else: mask = (cc == cc[y, z])
                roi1 = roi1 ^ mask
                roi = sitkThreshold(img,
                                    lowerThreshold=float(self._thresholdmin),
                                    upperThreshold=float(self._thresholdmax))
                roi = (roi & mask) | roi1
                self._updateSliceFromSITKImage(roi, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    def regionGrowingSlice(self,
                           sindex: int,
                           dim: int,
                           x: int, y: int, z: int,
                           mask: bool = False,
                           replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            if dim == 0:
                roi = sitkConnectedThreshold(img, [(x, y)],
                                             lower=self._thresholdmin,
                                             upper=self._thresholdmax)
            elif dim == 1:
                roi = sitkConnectedThreshold(img, [(x, z)],
                                             lower=self._thresholdmin,
                                             upper=self._thresholdmax)
            else:
                roi = sitkConnectedThreshold(img, [(y, z)],
                                             lower=self._thresholdmin,
                                             upper=self._thresholdmax)
            if mask: roi = roi & self._extractSITKSlice(sindex, dim)
            if not replace: roi = roi | roi1
            self._updateSliceFromSITKImage(roi, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def regionGrowingBlobSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._extractSITKSlice(sindex, dim, roi=True)
                img = self._extractSITKSlice(sindex, dim, roi=False)
                cc = sitkConnectedComponent(roi1)
                if dim == 0:
                    mask = (cc == cc[x, y])
                    roi = sitkConnectedThreshold(img, [(x, y)],
                                                 lower=self._thresholdmin,
                                                 upper=self._thresholdmax)
                elif dim == 1:
                    mask = (cc == cc[x, z])
                    roi = sitkConnectedThreshold(img, [(x, z)],
                                                 lower=self._thresholdmin,
                                                 upper=self._thresholdmax)
                else:
                    mask = (cc == cc[y, z])
                    roi = sitkConnectedThreshold(img, [(y, z)],
                                                 lower=self._thresholdmin,
                                                 upper=self._thresholdmax)
                roi1 = roi1 ^ mask
                roi = (roi & mask) | roi1
                self._updateSliceFromSITKImage(roi, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    def regionGrowingConfidenceSlice(self,
                                     sindex: int,
                                     dim: int,
                                     x: int, y: int, z: int,
                                     niter: int = 4,
                                     multi: float = 2.5,
                                     radius: int | None = None,
                                     mask: bool = False,
                                     replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            if radius is None: radius = self._radius
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            if dim == 0:
                roi = itkConfidenceConnected(img, [(x, y)],
                                             numberOfIterations=niter, multiplier=multi,
                                             initialNeighborhoodRadius=radius)
            elif dim == 1:
                roi = itkConfidenceConnected(img, [(x, z)],
                                             numberOfIterations=niter, multiplier=multi,
                                             initialNeighborhoodRadius=radius)
            else:
                roi = itkConfidenceConnected(img, [(y, z)],
                                             numberOfIterations=niter, multiplier=multi,
                                             initialNeighborhoodRadius=radius)
            if mask: roi = roi & self._extractSITKSlice(sindex, dim)
            if not replace: roi = roi | roi1
            self._updateSliceFromSITKImage(roi, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def regionGrowingConfidenceBlobSlice(self,
                                         sindex: int,
                                         dim: int,
                                         x: int, y: int, z: int,
                                         niter: int = 4,
                                         multi: float = 2.5,
                                         radius: int | None = None) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._radius
                roi1 = self._extractSITKSlice(sindex, dim, roi=True)
                img = self._extractSITKSlice(sindex, dim, roi=False)
                cc = sitkConnectedComponent(roi1)
                if dim == 0:
                    mask = (cc == cc[x, y])
                    roi = itkConfidenceConnected(img, [(x, y)],
                                                 numberOfIterations=niter, multiplier=multi,
                                                 initialNeighborhoodRadius=radius)
                elif dim == 1:
                    mask = (cc == cc[x, y])
                    roi = itkConfidenceConnected(img, [(x, z)],
                                                 numberOfIterations=niter, multiplier=multi,
                                                 initialNeighborhoodRadius=radius)
                else:
                    mask = (cc == cc[x, y])
                    roi = itkConfidenceConnected(img, [(y, z)],
                                                 numberOfIterations=niter, multiplier=multi,
                                                 initialNeighborhoodRadius=radius)
                roi1 = roi1 ^ mask
                roi = (roi & mask) | roi1
                self._updateSliceFromSITKImage(roi, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    # Volume processing

    def flip(self, flipx: bool, flipy: bool, flipz: bool) -> None:
        if self.hasROI():
            img = sitkFlip(self._roi.getSITKImage(), [flipx, flipy, flipz])
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def shift(self, movex: int, movey: int, movez: int) -> None:
        if self.hasROI():
            img = sitkShift(self._roi.getSITKImage(), [movex, movey, movez])
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def euclideanDilate(self, mm: float = 0.0) -> None:
        if self.hasROI():
            if mm == 0.0: mm = self._thickness
            if mm > 0.0:
                dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                img = (dmap <= mm)
                img = sitkCast(img, sitkUInt8)
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def euclideanErode(self, mm: float = 0.0) -> None:
        if self.hasROI():
            if mm == 0.0: mm = self._thickness
            if mm > 0.0:
                dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                img = (dmap <= -mm)
                img = sitkCast(img, sitkUInt8)
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def morphoDilate(self, radius: int | None = None, struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryDilate(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoErode(self, radius: int | None = None, struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryErode(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoOpening(self, radius: int | None = None, struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryOpening(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoClosing(self, radius: int | None = None, struct: int | None = None) -> None:
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryClosing(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def euclideanBlobDilate(self, x: int, y: int, z: int, mm: float = 0.0) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if mm == 0.0: mm = self._thickness
                if mm > 0.0:
                    cc = sitkConnectedComponent(self._roi.getSITKImage())
                    c = cc[x, y, z]
                    if c > 0:
                        dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                        img = (dmap <= mm)
                        img = sitkCast(img, sitkUInt8)
                        img1 = (cc == c)
                        img2 = img1 ^ self._roi.getSITKImage()
                        img = img | img2
                        self._updateRoiFromSITKImage(img)
                        if self._undo: self.appendVolumeToLIFO()

    def euclideanBlobErode(self, x: int, y: int, z: int, mm: float = 0.0) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if mm == 0.0: mm = self._thickness
                if mm > 0.0:
                    cc = sitkConnectedComponent(self._roi.getSITKImage())
                    c = cc[x, y, z]
                    if c > 0:
                        dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                        img = (dmap <= -mm)
                        img = sitkCast(img, sitkUInt8)
                        img1 = (cc == c)
                        img2 = img1 ^ self._roi.getSITKImage()
                        img = img | img2
                        self._updateRoiFromSITKImage(img)
                        if self._undo: self.appendVolumeToLIFO()

    def morphoBlobDilate(self,
                         x: int, y: int, z: int,
                         radius: int | None = None,
                         struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                cc = sitkConnectedComponent(self._roi.getSITKImage())
                c = cc[x, y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ self._roi.getSITKImage()
                    img = sitkBinaryDilate(img1, [radius, radius, radius], struct) | img2
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def morphoBlobErode(self,
                        x: int, y: int, z: int,
                        radius: int | None = None,
                        struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                cc = sitkConnectedComponent(self._roi.getSITKImage())
                c = cc[x, y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ self._roi.getSITKImage()
                    img = sitkBinaryErode(img1, [radius, radius, radius], struct) | img2
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def morphoBlobOpening(self,
                          x: int, y: int, z: int,
                          radius: int | None = None,
                          struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                cc = sitkConnectedComponent(self._roi.getSITKImage())
                c = cc[x, y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ self._roi.getSITKImage()
                    img = sitkBinaryOpening(img1, [radius, radius, radius], struct) | img2
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def morphoBlobClosing(self,
                          x: int, y: int, z: int,
                          radius: int | None = None,
                          struct: int | None = None) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._morphradius
                if struct is None: struct = self._struct
                cc = sitkConnectedComponent(self._roi.getSITKImage())
                c = cc[x, y, z]
                if c > 0:
                    img1 = (cc == c)
                    img2 = img1 ^ self._roi.getSITKImage()
                    img = sitkBinaryClosing(img1, [radius, radius, radius], struct) | img2
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def binaryAND(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                for i in range(1, n):
                    temp = temp & rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryOR(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                for i in range(1, n):
                    temp = temp | rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryXOR(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                for i in range(1, n):
                    temp = temp ^ rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryNAND(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        if self.hasROI():
            n = len(rois)
            if n > 0:
                temp1 = rois[0].getNumpy()
                temp2 = rois[1].getNumpy()
                for i in range(2, n): temp2 = temp2 & rois[i].getNumpy()
                temp1 = temp1 & logical_not(temp2).astype(uint8)
                self._updateRoiFromNumpy(temp1)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter is empty.')

    def binaryNOT(self) -> None:
        if self.hasROI():
            img = sitkBinaryNot(self._roi.getSITKImage())
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def fillHoles(self) -> None:
        if self.hasROI():
            img = sitkBinaryFillHole(self._roi.getSITKImage())
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def clear(self) -> None:
        img = sitkImage(self._roi.getSITKImage().GetSize(), sitkUInt8)
        self._updateRoiFromSITKImage(img)
        if self._undo: self.appendVolumeToLIFO()

    def objectSegment(self, algo: str = 'otsu') -> None:
        if self.hasVolume():
            if algo == 'otsu': img = sitkOtsu(self._volume.getSITKImage())
            elif algo == 'huang': img = sitkHuang(self._volume.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(self._volume.getSITKImage())
            elif algo == 'yen': img = sitkYen(self._volume.getSITKImage())
            elif algo == 'li': img = sitkLi(self._volume.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(self._volume.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(self._volume.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(self._volume.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(self._volume.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(self._volume.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(self._volume.getSITKImage())
            elif algo == 'moments': img = sitkMoments(self._volume.getSITKImage())
            elif algo == 'mean':
                v = self._volume.getNumpy().mean()
                img = (self._volume.getSITKImage() <= v)
            else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
            img = sitkBinaryNot(img)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def backgroundSegment(self, algo: str = 'otsu') -> None:
        if self.hasVolume():
            if algo == 'otsu': img = sitkOtsu(self._volume.getSITKImage())
            elif algo == 'huang': img = sitkHuang(self._volume.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(self._volume.getSITKImage())
            elif algo == 'yen': img = sitkYen(self._volume.getSITKImage())
            elif algo == 'li': img = sitkLi(self._volume.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(self._volume.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(self._volume.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(self._volume.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(self._volume.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(self._volume.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(self._volume.getSITKImage())
            elif algo == 'moments': img = sitkMoments(self._volume.getSITKImage())
            elif algo == 'mean':
                v = self._volume.getNumpy().mean()
                img = (self._volume.getSITKImage() <= v)
            else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def maskSegment(self,
                    algo: str = 'mean',
                    morpho: str = '',
                    niter: int = 1,
                    kernel: int = 0,
                    fill: str = ''):
        if self.hasVolume():
            # Segment background
            algo = algo.lower()
            if algo == 'mean':
                v = self._volume.getNumpy().mean()
                img = (self._volume.getSITKImage() <= v)
            elif algo == 'otsu': img = sitkOtsu(self._volume.getSITKImage())
            elif algo == 'huang': img = sitkHuang(self._volume.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(self._volume.getSITKImage())
            elif algo == 'yen': img = sitkYen(self._volume.getSITKImage())
            elif algo == 'li': img = sitkLi(self._volume.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(self._volume.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(self._volume.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(self._volume.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(self._volume.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(self._volume.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(self._volume.getSITKImage())
            elif algo == 'moments': img = sitkMoments(self._volume.getSITKImage())
            else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
            QApplication.processEvents()
            # mask = not( background )
            img = sitkBinaryNot(img)
            # Morphology operator
            if isinstance(kernel, int):
                if kernel > 0 and morpho in ('dilate', 'erode', 'open', 'close'):
                    morpho = morpho.lower()
                    for i in range(niter):
                        if morpho == 'dilate': img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        elif morpho == 'erode': img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        elif morpho == 'open':
                            img = sitkBinaryOpening(img, [kernel, kernel, kernel])
                            break
                        elif morpho == 'close':
                            img = sitkBinaryClosing(img, [kernel, kernel, kernel])
                            break
                        QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            # Filling
            if fill == '2d':
                f = BinaryFillholeImageFilter()
                for i in range(img.GetSize()[2]):
                    slc = img[:, :, i]
                    slc = f.Execute(slc)
                    img[:, :, i] = slc
                    QApplication.processEvents()
            elif fill == '3d':
                img = sitkBinaryFillHole(img)
                QApplication.processEvents()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def maskSegment2(self,
                     algo: str = 'mean',
                     morphoiter: int = 2,
                     kernel: int = 0):
        if self.hasVolume():
            # Segment background
            algo = algo.lower()
            if algo == 'mean':
                v = self._volume.getNumpy().mean()
                img = (self._volume.getSITKImage() <= v)
            elif algo == 'otsu': img = sitkOtsu(self._volume.getSITKImage())
            elif algo == 'huang': img = sitkHuang(self._volume.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(self._volume.getSITKImage())
            elif algo == 'yen': img = sitkYen(self._volume.getSITKImage())
            elif algo == 'li': img = sitkLi(self._volume.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(self._volume.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(self._volume.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(self._volume.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(self._volume.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(self._volume.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(self._volume.getSITKImage())
            elif algo == 'moments': img = sitkMoments(self._volume.getSITKImage())
            else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
            QApplication.processEvents()
            # Background processing
            if isinstance(kernel, int):
                if kernel == 0:
                    if max(self._volume.getSpacing()) < 1.5: kernel = 2
                    else: kernel = 1
                # Erode
                if morphoiter > 0:
                    for i in range(morphoiter):
                        img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        QApplication.processEvents()
                # keep major blob (remove blobs in head/brain)
                blobs = sitkConnectedComponent(img)
                QApplication.processEvents()
                blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
                QApplication.processEvents()
                img = blobs == 1
                # Dilate
                if morphoiter > 0:
                    for i in range(morphoiter):
                        img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            # Object = not( background )
            img = sitkBinaryNot(img)
            # Object processing
            if isinstance(kernel, int):
                # Erode
                if morphoiter > 0:
                    for i in range(morphoiter):
                        img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        QApplication.processEvents()
                # keep major blob (remove blobs in head/brain)
                blobs = sitkConnectedComponent(img)
                QApplication.processEvents()
                blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
                QApplication.processEvents()
                img = blobs == 1
                # Dilate
                if morphoiter > 0:
                    for i in range(morphoiter):
                        img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def notMaskSegment2(self,
                        algo: str = 'mean',
                        morphoiter: int = 2,
                        kernel: int = 0):
        self.maskSegment2(algo, morphoiter, kernel)
        self.binaryNOT()

    def blobFilterExtent(self, n: int) -> None:
        if self.hasROI():
            img = sitkConnectedComponent(self._roi.getSITKImage())
            img = sitkRelabelComponent(img, minimumObjectSize=n)
            img = (img > 0)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def majorBlobSelect(self) -> None:
        if self.hasROI():
            img = sitkConnectedComponent(self._roi.getSITKImage())
            img = sitkRelabelComponent(img, sortByObjectSize=True)
            img = (img == 1)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def blobSelect(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                cimg = sitkConnectedComponent(self._roi.getSITKImage())
                c = cimg[x, y, z]
                if c > 0:
                    img = (cimg == c)
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def blobRemove(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._roi.getSITKImage()
                cimg = sitkConnectedComponent(img)
                c = cimg[x, y, z]
                if c > 0:
                    img = (cimg != c) & img
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def copyBlob(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = sitkConnectedComponent(self._roi.getSITKImage())
                c = img[x, y, z]
                if c > 0:
                    img = (img == c)
                    filtr = sitkLabelShapeStatisticsImageFilter()
                    filtr.Execute(img)
                    if filtr.GetNumberOfLabels() > 0:
                        x0, y0, z0, dx, dy, dz = filtr.GetBoundingBox(1)
                        self._clipboard = img[x0:x0+dx, y0:y0+dy, z0:z0+dz]

    def cutBlob(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = sitkConnectedComponent(self._roi.getSITKImage())
                c = img[x, y, z]
                if c > 0:
                    img = (img == c)
                    filtr = sitkLabelShapeStatisticsImageFilter()
                    filtr.Execute(img)
                    if filtr.GetNumberOfLabels() > 0:
                        x0, y0, z0, dx, dy, dz = filtr.GetBoundingBox(1)
                        self._clipboard = img[x0:x0+dx, y0:y0+dy, z0:z0+dz]
                        img = self._roi.getSITKImage() - img
                        self._updateRoiFromSITKImage(img)
                        if self._undo: self.appendVolumeToLIFO()

    def pasteBlob(self, x: int, y: int, z: int) -> None:
        if self.hasROI():
            if self._clipboard is not None:
                img = Paste(self._roi.getSITKImage(),
                            self._clipboard,
                            self._clipboard.GetSize(),
                            (0, 0, 0), (x, y, z))
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def extractingValue(self, value: float, mask: bool = False, replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            img = self._volume.getSITKImage() == value
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def extractingValueBlob(self, value: float, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._roi.getSITKImage()
                cc = sitkConnectedComponent(roi1)
                mask = (cc == cc[x, y, z])
                img = self._volume.getSITKImage() == value
                roi1 = roi1 ^ mask
                img = (img & mask) | roi1
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def thresholding(self, mask: bool = False, replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            img = sitkThreshold(self._volume.getSITKImage(),
                                lowerThreshold=float(self._thresholdmin),
                                upperThreshold=float(self._thresholdmax))
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def thresholdingBlob(self, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._roi.getSITKImage()
                cc = sitkConnectedComponent(roi1)
                mask = (cc == cc[x, y, z])
                img = sitkThreshold(self._volume.getSITKImage(),
                                    lowerThreshold=float(self._thresholdmin),
                                    upperThreshold=float(self._thresholdmax))
                roi1 = roi1 ^ mask
                img = (img & mask) | roi1
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def regionGrowing(self, x: int, y: int, z: int, mask: bool = False, replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            img = sitkConnectedThreshold(self._volume.getSITKImage(), [(x, y, z)],
                                         lower=self._thresholdmin, upper=self._thresholdmax)
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def regionGrowingBlob(self, x: int, y: int, z: int) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                roi1 = self._roi.getSITKImage()
                cc = sitkConnectedComponent(roi1)
                mask = (cc == cc[x, y, z])
                img = sitkConnectedThreshold(self._volume.getSITKImage(), [(x, y, z)],
                                             lower=self._thresholdmin, upper=self._thresholdmax)
                roi1 = roi1 ^ mask
                img = (img & mask) | roi1
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def regionGrowingConfidence(self,
                                x: int, y: int, z: int,
                                niter: int = 4,
                                multi: float = 2.5,
                                radius: int | None = None,
                                mask: bool = False,
                                replace: bool = False) -> None:
        if self.hasVolume() and self.hasROI():
            if radius is None: radius = self._radius
            img = itkConfidenceConnected(self._volume.getSITKImage(), [(x, y, z)],
                                         numberOfIterations=niter, multiplier=multi,
                                         initialNeighborhoodRadius=radius)
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def regionGrowingConfidenceBlob(self,
                                    x: int, y: int, z: int,
                                    niter: int = 4,
                                    multi: float = 2.5,
                                    radius: int | None = None) -> None:
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if radius is None: radius = self._radius
                roi1 = self._roi.getSITKImage()
                cc = sitkConnectedComponent(roi1)
                mask = (cc == cc[x, y, z])
                img = itkConfidenceConnected(self._volume.getSITKImage(), [(x, y, z)],
                                             numberOfIterations=niter, multiplier=multi,
                                             initialNeighborhoodRadius=radius)
                roi1 = roi1 ^ mask
                img = (img & mask) | roi1
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def activeContour(self,
                      x: int, y: int, z: int,
                      seedradius: int = 3,
                      sigma: float = 1.0,
                      rms: float = 0.01,
                      advec: float = 1.0,
                      curv: float = 1.0,
                      propag: float = 1.0,
                      niter: int = 1000,
                      algo: str = 'default',
                      replace: bool = False) -> None:
        """
            seedradius: radius en mm of the seed sphere centered on x, y, z
            propagation scaling: propagation speed, default 1.0, > 0 propagation outwards, < 0 propagating inwards
            curvature: default 1.0, larger -> smoother resulting contour
            advection: default 1.0
            rms: 0.0 < rms < 1.0, default 0.01, convergence threshold
            niter, maximum number of iterations
            algo: algorithm default 'GeodesicActiveContourLevelSetImageFilter'
            or 'shape' ShapeDetectionLevelSetImageFilter
        """
        seedradius = seedradius ** 2 + 1
        img = sitkCast(self._volume.getSITKImage(), sitkFloat32)
        speed = sitkBoundedReciprocal(sitkGradientMagnitude(img, sigma))
        seed = sitkImage(self._volume.GetSize()[0], self._volume.GetSize()[1], self._volume.GetSize()[2], sitkUInt8)
        seed.SetSpacing(self._volume.GetSpacing())
        seed[x, y, z] = 1
        seed = sitkSignedMaurerDistanceMap(seed, insideIsPositive=False, useImageSpacing=True)
        seed = sitkCast(sitkThreshold(seed, -1000, seedradius), speed.GetPixelID()) * -1 + 0.5
        if algo == 'shape': flt = sitkShapeDetectionLevelSetImageFilter()
        else: flt = sitkGeodesicActiveContourLevelSetImageFilter()
        flt.SetMaximumRMSError(rms)
        flt.SetNumberOfIterations(niter)
        flt.SetAdvectionScaling(advec)
        flt.SetCurvatureScaling(curv)
        flt.SetPropagationScaling(propag)
        roi = self._roi.copyToSITKImage()
        img = sitkThreshold(flt.Execute(seed, speed), -1000, 0)
        if not replace: img = img | roi
        self._updateRoiFromSITKImage(img)
        if self._undo: self.appendVolumeToLIFO()

    def activeThresholdContour(self,
                               x: int, y: int, z: int,
                               seedradius: int = 3,
                               factor: float = 3.5,
                               rms: float = 0.01,
                               curv: float = 1.0,
                               propag: float = 1.0,
                               niter: int = 1000,
                               replace: bool = False) -> None:
        """
            seedradius: radius en mm of the seed sphere centered on x, y, z
            factor: factor x standard deviation of signal in seed sphere to estimate lower and upper thresholds
            propagation scaling: propagation speed, default 1.0, > 0 propagation outwards, < 0 propagating inwards
            curvature: default 1.0, larger -> smoother resulting contour
            rms: 0.0 < rms < 1.0, default 0.01, convergence threshold
            niter, maximum number of iterations
        """
        seedradius = seedradius ** 2 + 1
        img = sitkCast(self._volume.getSITKImage(), sitkFloat32)
        seed = sitkImage(self._volume.GetSize()[0], self._volume.GetSize()[1], self._volume.GetSize()[2], sitkUInt8)
        seed.SetSpacing(self._volume.GetSpacing())
        seed[x, y, z] = 1
        seed = sitkSignedMaurerDistanceMap(seed, insideIsPositive=False, useImageSpacing=True)
        seed = sitkThreshold(seed, -1000, seedradius)
        stats = sitkLabelStatisticsImageFilter()
        stats.Execute(img, seed)
        lower_threshold = stats.GetMean(1) - factor * stats.GetSigma(1)
        upper_threshold = stats.GetMean(1) + factor * stats.GetSigma(1)
        seed = sitkCast(seed, sitkFloat32) * -1 + 0.5
        flt = sitkThresholdSegmentationLevelSetImageFilter()
        flt.SetLowerThreshold(lower_threshold)
        flt.SetUpperThreshold(upper_threshold)
        flt.SetMaximumRMSError(rms)
        flt.SetNumberOfIterations(niter)
        flt.SetCurvatureScaling(curv)
        flt.SetPropagationScaling(propag)
        roi = self._roi.copyToSITKImage()
        img = sitkThreshold(flt.Execute(seed, img), -1000, 0)
        if not replace: img = img | roi
        self._updateRoiFromSITKImage(img)
        if self._undo: self.appendVolumeToLIFO()

    binaryUNION = binaryOR
    binaryINTERSECTION = binaryAND

    # Statistics

    def getIntensityStatistics(self) -> dict[str, float]:
        stats = dict()
        if self.hasVolume() and self.hasROI():
            mask = self._roi.getNumpy().flatten() > 0
            img = self._volume.getNumpy().flatten()[mask]
            r = describe(img)
            stats['count'] = r.nobs
            stats['mean'] = r.mean
            stats['median'] = median(img)
            stats['min'] = r.minmax[0]
            stats['max'] = r.minmax[1]
            stats['range'] = r.minmax[1] - r.minmax[0]
            stats['perc25'] = percentile(img, 25)
            stats['perc75'] = percentile(img, 75)
            stats['var'] = r.variance
            stats['std'] = sqrt(r.variance)
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
        return stats

    def getSliceIntensityStatistics(self, sindex: int, dim: int) -> dict[str, float]:
        stats = dict()
        if self.hasVolume() and self.hasROI():
            roi = (self._extractSITKSlice(sindex, dim) > 0)
            slc = self._extractSITKSlice(sindex, dim, roi=False)
            mask = sitkGetArrayViewFromImage(roi).flatten() > 0
            img = sitkGetArrayViewFromImage(slc).flatten()[mask]
            r = describe(img)
            stats['count'] = r.nobs
            stats['mean'] = r.mean
            stats['median'] = median(img)
            stats['min'] = r.minmax[0]
            stats['max'] = r.minmax[1]
            stats['range'] = r.minmax[1] - r.minmax[0]
            stats['perc25'] = percentile(img, 25)
            stats['perc75'] = percentile(img, 75)
            stats['var'] = r.variance
            stats['std'] = sqrt(r.variance)
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
        return stats

    def getShapeStatistics(self) -> list[dict[str, float]]:
        stats = []
        if self.hasVolume() and self.hasROI():
            filtr = sitkLabelShapeStatisticsImageFilter()
            filtr.SetComputeFeretDiameter(True)
            filtr.SetComputePerimeter(True)
            img = sitkConnectedComponent(self._roi.getSITKImage())
            filtr.Execute(img)
            if filtr.GetNumberOfLabels() > 0:
                for i in range(0, filtr.GetNumberOfLabels()-1):
                    statslabel = dict()
                    statslabel['count'] = filtr.GetNumberOfPixels(i + 1)
                    statslabel['boundingbox'] = filtr.GetBoundingBox(i + 1)
                    statslabel['centroid'] = filtr.GetCentroid(i + 1)
                    statslabel['elongation'] = filtr.GetElongation(i + 1)
                    statslabel['flatness'] = filtr.GetFlatness(i + 1)
                    statslabel['roudness'] = filtr.GetRoundness(i + 1)
                    statslabel['principalaxes'] = filtr.GetPrincipalAxes(i + 1)
                    statslabel['principalmoments'] = filtr.GetPrincipalMoments((i + 1))
                    statslabel['perimeter'] = filtr.GetPerimeter(i + 1)
                    statslabel['physicalsize'] = filtr.GetPhysicalSize(i + 1)
                    statslabel['feretdiameter'] = filtr.GetFeretDiameter(i + 1)
                    statslabel['ellipsoiddiameter'] = filtr.GetEquivalentEllipsoidDiameter(i + 1)
                    statslabel['sphericalperimeter'] = filtr.GetEquivalentSphericalPerimeter(i + 1)
                    statslabel['sphericalradius'] = filtr.GetEquivalentSphericalRadius(i + 1)
                    stats.append(statslabel)
        return stats


class SisypheROIFeatures(object):
    """
        SisypheROIFeatures

        Description

            Extract features (descriptive statistics, shape, texture) from SisypheROI
            and SisypheVolume instance(s).

        Inheritance

            object -> SisypheROIFeatures

        Private attributes

            _volume     SisypheVolume
            _rois       SisypheROICollection

        Public methods

            setVolume(SisypheVolume)
            SisypheVolume = getVolume()
            bool = hasVolume()
            setROICollectionFromLabelVolume(SisypheVolume)
            setROICollection(SisypheROICollection)
            SisypheROICollection = getROICollection()
            bool = hasROICollection()
            DataFrame = getDataFrame()
            setFirstOrderTag(bool)
            bool = getFirstOrderTag()
            setShapeTag(bool)
            bool = getShapeTag()
            setGrayLevelCooccurrenceMatrixTag(bool)
            bool = getGrayLevelCooccurrenceMatrixTag()
            setGrayLevelSizeZoneMatrixTag(bool)
            bool = getGrayLevelSizeZoneMatrixTag()
            setGrayLevelRunLengthMatrixTag(bool)
            bool =  getGrayLevelRunLengthMatrixTag()
            setNeighbouringGrayToneDifferenceMatrixTag(bool)
            bool = getNeighbouringGrayToneDifferenceMatrixTag()
            setGrayLevelDependenceMatrixTag(bool)
            bool = getGrayLevelDependenceMatrixTag()
            setAllTagsOn()
            execute()
            saveToCSV(str)
            saveToXLSX(str)

            inherited object methods

        Creation: 08/09/2022
        Revision:

            15/07/2023  add setROICollectionFromLabelVolume() method
            01/09/2023  type hinting
    """

    __slots__ = ['_volume', '_rois', '_foTag', '_shTag', '_glcmTag',
                 '_glszmTag', '_glrlmTag', '_ngtdmTag', '_gldmTag', '_df']

    # Special method

    def __init__(self,
                 vol: SisypheVolume | None = None,
                 rois: SisypheROICollection | None = None) -> None:
        super().__init__()

        if vol is not None: self.setVolume(vol)
        else: self._volume = None

        if rois is not None: self.setROICollection(rois)
        else: self._rois = None

        self._foTag = False
        self._shTag = False
        self._glcmTag = False
        self._glszmTag = False
        self._glrlmTag = False
        self._ngtdmTag = False
        self._gldmTag = False

        self._df = None

    def __str__(self) -> str:
        if self._volume is not None: v = 'SisypheVolume instance at <{}>'.format(id(self._volume))
        else: v = 'None'
        if self._rois is not None: r = 'SisypheROICollection instance at <{}>'.format(id(self._rois))
        else: r = 'None'
        buff = 'Volume: {}\n'.format(v)
        buff += 'ROICollection: {}\nFeatures calculation:\n'.format(r)
        buff += '  Shape: {}\n'.format(str(self._shTag))
        buff += '  First-order: {}\n'.format(str(self._foTag))
        buff += '  Gray level co-occurrence matrix: {}\n'.format(str(self._glcmTag))
        buff += '  Gray level Size zone matrix: {}\n'.format(str(self._glszmTag))
        buff += '  Gray level run length matrix: {}\n'.format(str(self._glrlmTag))
        buff += '  Neighbouring gray tone difference matrix: {}\n'.format(str(self._ngtdmTag))
        buff += '  Gray level dependence matrix: {}\n'.format(str(self._gldmTag))
        return buff

    def __repr__(self) -> str:
        return 'SisypheROIFeatures instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            if self.hasROICollection() and len(self._rois) > 0:
                if self._rois[0].getReferenceID() != self._volume.getID(): self._rois = None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        return self._volume

    def hasVolume(self) -> bool:
        return self._volume is not None

    def setROICollectionFromLabelVolume(self, v: SisypheVolume) -> None:
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self._rois = SisypheROICollection()
                self._rois.fromLabelVolume(v)
            else: raise ValueError('volume modality {} is not LB.'.format(v.acquisition.getModality()))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setROICollection(self, rois: SisypheROICollection) -> None:
        if isinstance(rois, SisypheROICollection):
            if self.hasVolume:
                if len(rois) > 0:
                    for roi in rois:
                        if roi.getReferenceID() != self._volume.getID():
                            raise AttributeError('ROI {} ID is not same as reference volume.'.format(roi.getName()))
                        if roi.getNumpy().sum() == 0:
                            raise AttributeError('ROI {} is empty.'.format(roi.getName()))
                    self._rois = rois
                else: raise AttributeError('SisypheROICollection is empty.')
            else: raise AttributeError('SisypheVolume attribute is empty.')
        else: raise TypeError('parameter type {} is not SisypheROICollection.'.format(type(rois)))

    def getROICollection(self) -> SisypheROICollection:
        return self._rois

    def hasROICollection(self) -> bool:
        return self._rois is not None

    def getDataFrame(self) -> DataFrame:
        return self._df

    def setFirstOrderTag(self, v: bool) -> None:
        if isinstance(v, bool): self._foTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getFirstOrderTag(self) -> bool:
        return self._foTag

    def setShapeTag(self, v: bool) -> None:
        if isinstance(v, bool): self._shTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getShapeTag(self) -> bool:
        return self._shTag

    def setGrayLevelCooccurrenceMatrixTag(self, v: bool) -> None:
        if isinstance(v, bool): self._glcmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelCooccurrenceMatrixTag(self) -> bool:
        return self._glcmTag

    def setGrayLevelSizeZoneMatrixTag(self, v: bool) -> None:
        if isinstance(v, bool): self._glszmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelSizeZoneMatrixTag(self) -> bool:
        return self._glszmTag

    def setGrayLevelRunLengthMatrixTag(self, v: bool) -> None:
        if isinstance(v, bool): self._glrlmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelRunLengthMatrixTag(self) -> bool:
        return self._glrlmTag

    def setNeighbouringGrayToneDifferenceMatrixTag(self, v: bool) -> None:
        if isinstance(v, bool): self._ngtdmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getNeighbouringGrayToneDifferenceMatrixTag(self) -> bool:
        return self._ngtdmTag

    def setGrayLevelDependenceMatrixTag(self, v: bool) -> None:
        if isinstance(v, bool): self._gldmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelDependenceMatrixTag(self) -> bool:
        return self._gldmTag

    def setAllTagsOn(self) -> None:
        self._foTag = True
        self._shTag = True
        self._glcmTag = True
        self._glszmTag = True
        self._glrlmTag = True
        self._ngtdmTag = True
        self._gldmTag = True

    def execute(self, progress: DialogWait | None = None) -> None:
        if self.hasVolume() and self.hasROICollection():
            from Sisyphe.gui.dialogWait import DialogWait
            if not isinstance(progress, DialogWait): progress = None
            n = len(self._rois)
            if n > 0:
                img = self._volume.getSITKImage()
                rows = self._rois.keys()
                cols = list()
                df = list()
                for i in range(n):
                    item = list()
                    mask = self._rois[i].getSITKImage()
                    name = self._rois[i].getName()
                    # First-order features
                    if self._foTag:
                        if progress is not None:
                            progress.setInformationText('{} first-order statistics.'.format(name))
                        flt = RadiomicsFirstOrder(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Shape features of main connected component
                    if self._shTag:
                        if progress is not None:
                            progress.setInformationText('{} shape statistics.'.format(name))
                        mask2 = sitkConnectedComponent(mask)
                        if sitkGetArrayViewFromImage(mask2).max() > 1:
                            mask2 = sitkRelabelComponent(mask2)
                            mask2 = (mask2 == 1)
                        else: mask2 = mask
                        flt = RadiomicsShape(img, mask2)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Gray level co-occurrence matrix features
                    if self._glcmTag:
                        if progress is not None:
                            progress.setInformationText('{} gray level co-occurrence matrix features.'.format(name))
                        flt = RadiomicsGLCM(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Gray level Size zone matrix features
                    if self._glszmTag:
                        if progress is not None:
                            progress.setInformationText('{} gray level Size zone matrix features.'.format(name))
                        flt = RadiomicsGLSZM(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Gray level run length matrix features
                    if self._glrlmTag:
                        if progress is not None:
                            progress.setInformationText('{} gray level run length matrix features.'.format(name))
                        flt = RadiomicsGLRLM(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Neighbouring gray tone difference matrix features
                    if self._ngtdmTag:
                        if progress is not None:
                            progress.setInformationText('{} neighbouring gray tone difference matrix features.'
                                                        .format(name))
                        flt = RadiomicsNGTDM(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    # Gray level dependence matrix matrix features
                    if self._gldmTag:
                        if progress is not None:
                            progress.setInformationText('{} gray level dependence matrix features.'.format(name))
                        flt = RadiomicsGLDM(img, mask)
                        r = flt.execute()
                        if i == 0: cols += r.keys()
                        item += r.values()
                    df.append(item)
                self._df = DataFrame(df, index=rows, columns=cols)
            else: raise AttributeError('ROI collection is empty.')
        else: raise AttributeError('Undefined volume or ROICollection.')

    def saveToCSV(self, filename: str) -> None:
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.csv'
                self._df.to_csv(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')

    def saveToXLSX(self, filename: str) -> None:
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.xlsx'
                self._df.to_excel(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')


class SisypheROIHistogram(object):
    """
        SisypheROIHistogram

        Inheritance

            object -> SisypheROIHistogram

        Private attributes

            _volume     SisypheVolume
            _rois       SisypheROICollection

        Public methods

            setVolume(SisypheVolume)
            SisypheVolume = getVolume()
            bool = hasVolume()
            setROICollectionFromLabelVolume(SisypheVolume)
            setROICollection(SisypheROICollection)
            SisypheROICollection = getROICollection()
            bool = hasROICollection()
            setBins(int)
            int = getBins()
            DataFrame = getDataFrame()
            (DataFrame, DataFrame) = getHistograms(SisypheROICollection, bool)
            execute()
            saveToCSV(str)
            saveToXLSX(str)

            inherited object methods

        Creation: 08/09/2022
        Revision:

            15/07/2023  add setROICollectionFromLabelVolume() method
            01/09/2023  type hinting
    """

    __slots__ = ['_volume', '_rois', '_bins', '_df']

    # Special method

    def __init__(self,
                 vol: SisypheVolume | None = None,
                 rois: SisypheROICollection | None = None) -> None:
        super().__init__()

        if vol is not None: self.setVolume(vol)
        else: self._volume = None

        if rois is not None: self.setROICollection(rois)
        else: self._rois = None

        self._bins = 100
        self._df = None

    def __str__(self) -> str:
        if self._volume is not None: v = 'SisypheVolume instance at <{}>'.format(id(self._volume))
        else: v = 'None'
        if self._rois is not None: r = 'SisypheROICollection instance at <{}>'.format(id(self._rois))
        else: r = 'None'
        buff = 'Volume: {}\n'.format(v)
        buff += 'ROICollection: {}\n'.format(r)
        buff += '  Bins: {}\n'.format(self._bins)
        return buff

    def __repr__(self) -> str:
        return 'SisypheROIHistogram instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            if self.hasROICollection() and len(self._rois) > 0:
                if self._rois[0].getReferenceID() != self._volume.getID(): self._rois = None
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        return self._volume

    def hasVolume(self) -> bool:
        return self._volume is not None

    def setROICollectionFromLabelVolume(self, v: SisypheVolume) -> None:
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self._rois = SisypheROICollection()
                self._rois.fromLabelVolume(v)
            else: raise ValueError('volume modality {} is not LB.'.format(v.acquisition.getModality()))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setROICollection(self, rois: SisypheROICollection) -> None:
        if isinstance(rois, SisypheROICollection):
            if self.hasVolume:
                if len(rois) > 0:
                    for roi in rois:
                        if roi.getReferenceID() != self._volume.getID():
                            raise AttributeError('ROI {} ID is not same as reference volume.'.format(roi.getName()))
                        if roi.getNumpy().sum() == 0:
                            raise AttributeError('ROI {} is empty.'.format(roi.getName()))
                    self._rois = rois
                else: raise AttributeError('SisypheROI ID conflicting with SisypheVolume ID.')
            else: raise AttributeError('SisypheVolume attribute is empty.')
        else: raise TypeError('parameter type {} is not SisypheROICollection.'.format(type(rois)))

    def getROICollection(self) -> SisypheROICollection:
        return self._rois

    def hasROICollection(self) -> bool:
        return self._rois is not None

    def setBins(self, v: int) -> None:
        if isinstance(v, int):
            if 2 <= v <= 256: self._bins = v
            else: raise ValueError('parameter value {} is not between 2 and 256.'.format(v))

    def getBins(self) -> int:
        return self._bins

    def getDataFrame(self) -> DataFrame:
        return self._df

    def getHistograms(self, roi: SisypheROI, norm: bool = False) -> tuple[DataFrame, DataFrame]:
        if isinstance(roi, SisypheROI):
            if roi.getNumpy().sum() > 0:
                mask = roi.getNumpy().flatten() > 0
                img = self._volume.getNumpy().flatten()
                img = img[mask]
                # Histogram
                h, c = histogram(img, bins=self._bins)
                c2 = list()
                for i in range(len(c) - 1):
                    c2.append((c[i] + c[i + 1]) / 2)
                s = h.sum()
                if norm: h2 = h / s
                else: h2 = h
                df1 = DataFrame([h2], columns=c2)
                # Cumulative histogram
                h = h[::-1].cumsum()[::-1]
                if norm: h2 = h / s
                else: h2 = h
                df2 = DataFrame([h2], columns=c2)
                return df1, df2
            else: raise ValueError('SisypheROI array is empty.')
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def execute(self, progress: DialogWait | None = None) -> None:
        if self.hasVolume() and self.hasROICollection():
            from Sisyphe.gui.dialogWait import DialogWait
            if not isinstance(progress, DialogWait): progress = None
            n = len(self._rois)
            if n > 0:
                df = list()
                rows = self._rois.keys()
                img = self._volume.getNumpy().flatten()
                for i in range(n):
                    name = self._rois[i].getName()
                    if progress is not None: progress.setInformationText('{} histogram.'.format(name))
                    mask = self._rois[i].getNumpy().flatten() > 0
                    roi = img[mask]
                    h, c = histogram(roi, bins=self._bins)
                    c2 = list()
                    for j in range(len(c) - 1):
                        c2.append((c[j] + c[j + 1]) / 2)
                    df.append(h)
                self._df = DataFrame(df, index=rows, columns=c2)
            else: raise AttributeError('ROI collection is empty.')
        else: raise AttributeError('Undefined volume or ROICollection.')

    def saveToCSV(self, filename: str) -> None:
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.csv'
                self._df.to_csv(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')

    def saveToXLSX(self, filename: str) -> None:
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.xlsx'
                self._df.to_excel(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    test = 1
    app = QApplication(argv)
    vol1 = SisypheVolume()
    mr = SisypheROI()
    rs = SisypheROICollection()
    fe = SisypheROIFeatures()
    vol1.loadFromSisyphe('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/SISYPHE/t1mni.vol')
    mr.loadFromSisyphe('/Users/Jean-Albert/PycharmProjects/untitled/TESTS/SISYPHE/test.roi')
    mr.setReferenceID(vol1.getID())
    rs.append(mr)
    rs.append(mr)
    fe.setVolume(vol1)
    fe.setROICollection(rs)
    fe.setAllTagsOn()
    fe.execute()
    exit(app.exec_())
