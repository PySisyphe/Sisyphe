"""
External packages/modules
-------------------------

    - cython, static compiler, https://cython.org/
    - ANTs, image registration, http://stnava.github.io/ANTs/
    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - radiomics, radiomics features and texture analysis, https://pyradiomics.readthedocs.io/en/latest/
    - scipy, scientific computing, https://scipy.org/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - scikit-image, image processing, https://scikit-image.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os import getcwd
from os.path import exists
from os.path import join
from os.path import split
from os.path import splitext
from os.path import basename
from os.path import dirname

import cython

from re import sub

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
from numpy import ndarray
from numpy import where
from numpy import max

from scipy import sparse
from scipy.stats import describe

from pandas import DataFrame

from skimage.draw import line
from skimage.draw import disk
from skimage.draw import ellipse
from skimage.draw import rectangle
from skimage.draw import polygon
from skimage.draw import ellipsoid
from skimage.measure import euler_number
from skimage.morphology import flood
from skimage.morphology import remove_objects_by_distance
from skimage.segmentation import clear_border

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

# < Revision 19/02/2025
# from Sisyphe.lib.ants.ants_image import ANTsImage
from ants.core.ants_image import ANTsImage
# Revision 19/02/2025 >

from SimpleITK import Image
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
from SimpleITK import ConfidenceConnected as sitkConfidenceConnected
from SimpleITK import GetArrayFromImage as sitkGetArrayFromImage
from SimpleITK import GetImageFromArray as sitkGetImageFromArray
from SimpleITK import BinaryDilate as sitkBinaryDilate
from SimpleITK import BinaryErode as sitkBinaryErode
from SimpleITK import BinaryFillhole as sitkBinaryFillHole
from SimpleITK import BinaryThinning as sitkBinaryThinning
from SimpleITK import BinaryPruning as sitkBinaryPruning
from SimpleITK import BinaryFillholeImageFilter
from SimpleITK import BinaryMorphologicalOpening as sitkBinaryOpening
from SimpleITK import BinaryMorphologicalClosing as sitkBinaryClosing
from SimpleITK import BinaryNot as sitkBinaryNot
from SimpleITK import OtsuThreshold as sitkOtsu
from SimpleITK import OtsuThresholdImageFilter as sitkOtsuThresholdImageFilter
from SimpleITK import HuangThreshold as sitkHuang
from SimpleITK import HuangThresholdImageFilter as sitkHuangThresholdImageFilter
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
from SimpleITK import LabelVoting as sitkLabelVoting
from SimpleITK import MultiLabelSTAPLE as sitkMultiLabelSTAPLE
from SimpleITK import ComposeImageFilter as sitkComposeImageFilter

from vtk import vtkLookupTable
from vtk import vtkImageCast
from vtk import vtkContourFilter
from vtk import vtkMarchingCubes
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper
from vtk import vtkActor
from vtk import vtkImageData

from radiomics.firstorder import RadiomicsFirstOrder
from radiomics.shape import RadiomicsShape
from radiomics.glcm import RadiomicsGLCM
from radiomics.glszm import RadiomicsGLSZM
from radiomics.glrlm import RadiomicsGLRLM
from radiomics.ngtdm import RadiomicsNGTDM
from radiomics.gldm import RadiomicsGLDM

from Sisyphe.lib.bv.voi import read_voi
from Sisyphe.lib.bv.vmr import read_vmr
# < Revision 30/07/2024
# add SisypheVolume import
from Sisyphe.core.sisypheVolume import SisypheVolume
# Revision 30/07/2024 >
from Sisyphe.core.sisypheImageIO import readFromSisypheROI
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImage import SisypheBinaryImage
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    # < Revision 30/07/2024
    # from Sisyphe.core.sisypheVolume import SisypheVolume
    # Revision 30/07/2024 >
    from Sisyphe.core.sisypheTransform import SisypheTransform
    from Sisyphe.core.sisypheTransform import SisypheApplyTransform


__all__ = ['SisypheROI',
           'SisypheROICollection',
           'SisypheROIDraw',
           'SisypheROIFeatures',
           'SisypheROIHistogram']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> Sisyphe.core.sisypheImage.SisypheImage -> Sisyphe.core.sisypheImage.SisypheBinaryImage -> SisypheROI
             -> SisypheROICollection
             -> SisypheROIDraw
             -> SisypheROIFeatures
             -> SisypheROIHistogram
"""

listImages = sitkImage | ndarray | SisypheImage
listLibImages = listImages | vtkImageData | ANTsImage
tupleInt2 = tuple[int, int]
vectorInt2 = list[int] | tuple[int, int]
tupleInt3 = tuple[int, int, int]
vectorInt3 = list[int] | tupleInt3
tupleFloat3 = tuple[float, float, float]
vectorFloat3 = list[float] | tupleFloat3


class SisypheROI(SisypheBinaryImage):
    """
    Description
    ~~~~~~~~~~~

    PySisyphe region-of-interest (ROI) binary image class.

    Scope of methods:

        - display management (color, opacity, visibility),
        - flip/shift,
        - morphology operators (dilate, erode, closing, opening),
        - fill holes,
        - blob (connected component),
        - 2D shape drawing (line, disk, ellipse, square, rectangle, polygon),
        - 3D shape drawing (cube, Parallelepiped, sphere),
        - mesh conversion,
        - IO methods (native format and BrainVoyager VOI format),
        - methods inherited from the SisypheImage class.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheImage -> SisypheBinaryImage -> SisypheROI

    Creation: 08/09/2022
    Last revision: 21/09/2024
    """

    __slots__ = ['_filename', '_referenceID', '_compression', '_name', '_color', '_alpha', '_visibility', '_lut']
    _counter: int = 0

    # Class constants

    _FILEEXT = '.xroi'
    _REGEXP = '^[_A-Za-z0-9#\-\_\s+,]+$'

    # Class methods

    @classmethod
    def getInstancesCount(cls) -> int:
        """
        Get the SisypheROI instance count.

        Returns
        -------
        int
            instance count
        """
        return cls._counter

    @classmethod
    def addInstance(cls) -> None:
        """
        Increment the SisypheROI instance count. This class method is called by the constructor.
        """
        cls._counter += 1

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheROI file extension.

        Returns
        -------
        str
            '.xroi'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheROI filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe ROI (.xroi)'
        """
        return 'PySisyphe ROI (*{})'.format(cls._FILEEXT)

    @classmethod
    def getRegExp(cls) -> str:
        """
        Get the regular expression filter applied to roi name attribute.

        Returns
        -------
        str
            regular expression filter
        """
        return cls._REGEXP

    @classmethod
    def openROI(cls, filename: str) -> SisypheROI:
        """
        Create a SisypheROI instance from a PySisyphe ROI (.xroi) file format.

        Parameters
        ----------
        filename : str
            PySisyphe ROI file name

        Returns
        -------
        SisypheROI
            loaded ROI
        """
        if exists(filename):
            filename = basename(filename) + cls.getFileExt()
            roi = SisypheROI()
            roi.load(filename)
            return roi
        else: raise ValueError('No such file {}'.format(filename))

    # Special methods

    """
    Private attributes

    _color          list[double]
    _alpha          float
    _name           str
    _path           str
    _reference_ID   str
    _compressed     bool
    _filename       str
    _lut            SisypheLut
    """

    def __init__(self,
                 image: str | listLibImages | SisypheImage | None = None,
                 copy: bool = True,
                 **kargs):
        """
        SisypheROI instance constructor

        Parameters
        ----------
        image : Sisyphe.core.sisypheImage.SisypheImage | SimpleITK.Image | vkt.vtkImageData | ants.core.ANTSImage | numpy.ndarray instance
            image to copy
        copy : bool
            - if True, copy image to SisypheROI if datatype is unit8
            - if False, create only a new SisypheROI with the same image geometry (size, spacing, origin, orientation)
        **kargs :
            - size : tuple[float, float, float] | list[float, float, float]
            - datatype : str
            - spacing : tuple[float, float, float] | list[float, float, float]
            - direction : tuple[float * 9] | list[float * 9]
        """
        self.addInstance()
        self._referenceID: str = ''
        # Copy SisypheVolume ID to reference ID
        if isinstance(image, SisypheVolume):
            self.setReferenceID(image.getID())
        # Copy SisypheROI reference ID
        elif isinstance(image, SisypheROI):
            self.setReferenceID(image.getReferenceID())
            image = image._sitk_image
        super().__init__(image, copy, **kargs)
        self._name: str = ''
        self._filename: str = ''
        self._compression: bool = False
        self._color = [1.0, 0.0, 0.0]   # default = red
        # noinspection PyUnresolvedReferences
        self._alpha: cython.double = 1.0  # default = opaque
        self._visibility: bool = True
        self._lut = SisypheLut()
        self._initLut()
        self.setDefaultOrigin()
        self.setDirections()
        self.setDefaultFilename()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheROI instance to str
        """
        buff = 'ReferenceID: {}\n' \
               'Name: {}\n'.format(self.getReferenceID(), self._name)
        buff += 'Color: r={0[0]:.2f} g={0[1]:.2f} b={0[2]:.2f}\n' \
                'Alpha: {1:.2f}\n'.format(self._color, self._alpha)
        buff += 'Non zero voxels: {}\n'.format(self.getNumberOfNonZero())
        buff += super().__str__()

        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheROI instance representation
        """
        return 'SisypheROI instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # < Revision 29/07/2024
    # add __getitem__ method
    # Revision 29/07/2024 >
    def __getitem__(self, idx):
        """
        Special overloaded container getter method. Get scalar value(s) with slicing ability.
        syntax: v = instance_name[x, y, z]

        Parameters
        ----------
        idx : list[int, int, int], tuple[int, int, int] | slice
            x, y, z int indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)

        Returns
        -------
        int | float | tuple | SisypheROI
            SisypheROI if slicing key
        """
        r = self._sitk_image.__getitem__(idx)
        if isinstance(r, sitkImage):
            r = SisypheROI(r)
            r.setColor(rgb=self.getColor())
            r.setAlpha(self.getAlpha())
        return r

    # Difference

    def __sub__(self, other: listImages | SisypheROI | int | float) -> SisypheROI:
        """
        Special overloaded arithmetic operator -. self - other -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI | int | float
            second operand of subtraction

        Returns
        -------
        SisypheROI
            roi = self - other
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        img = self._sitk_image.__sub__(other) == 1
        roi = SisypheROI(sitkCast(img, getLibraryDataType('uint8', 'sitk')))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __rsub__(self, other: listImages | SisypheROI | int | float) -> SisypheROI:
        """
        Special overloaded arithmetic operator -. other - self -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI | int | float
            second operand of subtraction

        Returns
        -------
        SisypheROI
            roi = other - self
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        img = self._sitk_image.__rsub__(other) == 1
        roi = SisypheROI(sitkCast(img, getLibraryDataType('uint8', 'sitk')))
        roi.setReferenceID(self.getReferenceID())
        return roi

    # Logic operators

    def __and__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator & (and).
        self & other -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            second operand of & operator

        Returns
        -------
        SisypheROI
            roi = self & other
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__and__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __rand__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator & (and). other & self -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            first operand of & operator

        Returns
        -------
        SisypheROI
            roi = other & self
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__rand__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __or__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator | (or). self | other -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            second operand of | operator

        Returns
        -------
        SisypheROI
            roi = self | other
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__or__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __ror__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator | (or). other | self -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            first operand of | operator

        Returns
        -------
        SisypheROI
            roi = other | self
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__ror__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __xor__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator ^ (xor). self ^ other -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            second operand of ^ operator

        Returns
        -------
        SisypheROI
            roi = self ^ other
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__xor__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __rxor__(self, other: listImages | SisypheROI) -> SisypheROI:
        """
        Special overloaded logic operator ^ (xor). other ^ self -> SisypheROI

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | SisypheROI
            first operand of ^ operator

        Returns
        -------
        SisypheROI
            roi = other ^ self
        """
        if isinstance(other, SisypheROI): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        roi = SisypheROI(self._sitk_image.__rxor__(other))
        roi.setReferenceID(self.getReferenceID())
        return roi

    def __invert__(self) -> SisypheROI:
        """
        Special overloaded logic unary operator ~ (not). ~self -> SisypheROI

        Returns
        -------
        SisypheROI
            roi = ~self
        """
        roi = SisypheROI(sitkBinaryNot(self._sitk_image))
        roi.setReferenceID(self.getReferenceID())
        return roi

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

    # < Revision 20/10/2024
    # add getSisypheVolume method
    def getSisypheVolume(self) -> SisypheVolume:
        """
        SisypheROI instance view to a SisypheVolume instance. Shallow copy of the SimpleITK image attribute. Image
        buffer is shared between SisypheROI and SisypheVolume instances.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            shallow copy of roi
        """
        r = SisypheVolume()
        r.setSITKImage(self.getSITKImage())
        return r
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add getSisypheVolume method
    def copyToSisypheVolume(self) -> SisypheVolume:
        """
        Copy fo the SisypheROI instance to a SisypheVolume instance. Deep copy of the SimpleITK image attribute. Image
        buffer is not shared between SisypheROI and SisypheVolume instances.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            deep copy of roi
        """
        r = SisypheVolume()
        r.copyFromSITKImage(self.getSITKImage())
        return r
    # Revision 20/10/2024 >

    def copy(self) -> SisypheROI:
        """
        SisypheROI copy of the current SisypheROI instance.

        Returns
        -------
        SisypheROI
            roi copy
        """
        if not self.isEmpty():
            roi = SisypheROI(self.getSITKImage())
            self.copyAttributesTo(roi)
            return roi
        else: raise ValueError('SisypheROI is empty.')

    def copyAttributesTo(self, roi: SisypheROI) -> None:
        """
        Copy the attributes (reference ID, name, file name, color, opacity) of the current SisypheROI instance to the
        parameter SisypheROI instance.

        Parameters
        ----------
        roi : SisypheROI
           roi where attributes are copied
        """
        if isinstance(roi, SisypheROI):
            roi.setReferenceID(self)
            roi.setName(self.getName())
            roi.setFilename(self.getFilename())
            roi.setColor(rgb=self.getColor())
            roi.setAlpha(self.getAlpha())
            # < Revision 30/07/2024
            # copy spacing attribute
            s = self.getSpacing()
            roi.setSpacing(s[0], s[1], s[2])
            # Revision 30/07/2024 >
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def copyAttributesFrom(self, roi: SisypheROI) -> None:
        """
        Copy the attributes (reference ID, name, file name, color, opacity) of the parameter SisypheROI instance to the
        current SisypheROI instance.

        Parameters
        ----------
        roi : SisypheROI
            roi from which attributes are copied
        """
        if isinstance(roi, SisypheROI):
            self.setReferenceID(roi)
            self.setName(roi.getName())
            self.setFilename(roi.getFilename())
            self.setColor(rgb=roi.getColor())
            self.setAlpha(roi.getAlpha())
            # < Revision 30/07/2024
            # copy spacing attribute
            s = roi.getSpacing()
            self.setSpacing(s[0], s[1], s[2])
            # Revision 30/07/2024 >
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current SisypheROI instance.

        Parameters
        ----------
        name : str
            roi name
        """
        if isinstance(name, str):
            if name != '':
                # < Revision 21/09/2024
                # re = QRegExp(self._REGEXP)
                # if re.exactMatch(name):
                #     self._name = name
                r = '[^A-Za-z0-9#\-\_\s,]'
                name = sub(r, '', name)
                if name != '':
                    self._name = name
                    # < Revision 23/03/2025
                    if self._filename is not None:
                        self._filename = join(dirname(self._filename), self._name + self._FILEEXT)
                    # Revision 23/03/2025 >
                # Revision 21/09/2024 >
                else: raise ValueError('Invalid char in name parameter.')
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheMesh instance.

        Returns
        -------
        str
            roi name
        """
        return self._name

    def setDefaultName(self) -> None:
        """
        Set default name attribute of the current SisypheROI instance. default name = 'ROI' + instance count.
        """
        idx = '00{}'.format(self.getInstancesCount())[-3:]
        self.setName('ROI{}'.format(idx))

    def setFilename(self, filename: str) -> None:
        """
        Set the file name attribute of the current SisypheROI instance. This file name is used by save() method.

        Parameters
        ----------
        filename : str
            file name
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
            self._filename = filename
            if self._name == '':
                self._name = splitext(basename(filename))[0]
        else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    # < Revision 01/08/2024
    # add setFilenamePrefix method
    def setFilenamePrefix(self, prefix: str, sep: str = '_') -> None:
        """
        Set a prefix to the file name attribute of the current SisypheROI instance.

        Parameters
        ----------
        prefix : str
            prefix to add
        sep : str
            char between prefix and base name (default '_')
        """
        if self._filename != '':
            if isinstance(prefix, str):
                if prefix != '':
                    if prefix[-1] == sep: prefix = prefix[:-1]
                    self._filename = join(dirname(self._filename), '{}{}{}'.format(prefix, sep, basename(self._filename)))
            else: raise TypeError('parameter type {} is not str.'.format(prefix))
        else: raise ValueError('Filename attribute is empty.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add getFilenamePrefix method
    def getFilenamePrefix(self, sep: str = '_') -> str:
        """
        Get prefix (if any) from the file name attribute of the current SisypheROI instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            prefix
        """
        r = self.getFilename().split(sep)
        if len(r) > 0: return r[0]
        else: return ''
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add setFilenameSuffix method
    def setFilenameSuffix(self, suffix: str, sep: str = '_') -> None:
        """
        Set a suffix to the file name attribute of the current SisypheROI instance.

        Parameters
        ----------
        suffix : str
            suffix to add
        sep : str
            char between base name and suffix (default '_')
        """
        if self._filename != '':
            if isinstance(suffix, str):
                if suffix != '':
                    if suffix[0] == sep: suffix = suffix[1:]
                    root, ext = splitext(basename(self._filename))
                    self._filename = join(dirname(self._filename), '{}{}{}{}'.format(root, sep, suffix, ext))
            else: raise TypeError('parameter type {} is not str.'.format(suffix))
        else: raise ValueError('Filename attribute is empty.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add getFilenameSuffix method
    def getFilenameSuffix(self, sep: str = '_') -> str:
        """
        Get suffix (if any) from the file name attribute of the current SisypheROI instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            suffix
        """
        r = self.getFilename().split(sep)
        if len(r) > 0: return r[-1]
        else: return ''
    # Revision 01/08/2024 >

    def setDefaultFilename(self) -> None:
        """
        Set default file name attribute of the current SisypheROI instance. This file name is used by save() method.
        Default file name = name attribute + roi file extension (.xroi)
        """
        if self._name == '': self.setDefaultName()
        self._filename = join(getcwd(), '{}{}'.format(self._name, self._FILEEXT))

    def setPathFromVolume(self, volume: SisypheVolume) -> None:
        """
        Set path part (dirname) of the file name attribute of the current SisypheROI instance from the path part of the
        file name attribute of a SisypheVolume parameter.

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to replace dirname
        """
        if isinstance(volume, SisypheVolume):
            path = dirname(volume.getFilename())
            if path != '': self._filename = join(path, basename(self._filename))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDirname(self, path: str) -> None:
        """
        Set path part (dirname) of the file name attribute of the current SisypheROI instance.

        Parameters
        ----------
        path : str
            replacement dirname
        """
        if exists(path): self._filename = join(path, basename(self._filename))
        else: raise FileExistsError('folder {} not found.'.format(path))

    def getDirname(self) -> str:
        """
        Get path part (dirname) of the file name attribute of the current SisypheROI instance.

        Returns
        -------
        str
            path part of the file name attribute
        """
        return dirname(self._filename)

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current SisypheROI instance. This file name is used by save() method.

        Returns
        -------
        str
            file name
        """
        return self._filename

    def hasFilename(self) -> bool:
        """
        Check whether the current SisypheROI instance file name attribute is defined (!= '')

        Returns
        -------
        bool
            True if file name attribute is defined
        """
        return self._filename != ''

    def getColor(self) -> vectorFloat3:
        """
        Get the roi color of the current SisypheROI instance.

        Returns
        -------
        tuple[float, float, float]
            roi color, red, green, blue (0.0 <= value <= 1.0)
        """
        return self._color

    def getQColor(self) -> QColor:
        """
        Get the mesh color (as QColor) of the current SisypheROI instance.

        Returns
        -------
        PyQt5.QtGui.QColor
            roi color
        """
        c = QColor()
        c.setRgbF(self._color[0], self._color[1], self._color[2])
        return c

    def setColor(self,
                 r: float | int | None = None,
                 g: float | int | None = None,
                 b: float | int | None = None,
                 rgb: vectorFloat3 | vectorInt3 | None = None):
        """
        Set the ROI color of the current SisypheROI instance.

        Parameters
        ----------
        r : float | None
            roi color, 0.0 <= red <= 1.0
        g : float | None
            roi color, 0.0 <= green <= 1.0
        b : float | None
            roi color, 0.0 <= blue <= 1.0
        rgb : tuple[float, float, float] | None
            roi color, red, green, blue (0.0 <= value <= 1.0)
        """
        if rgb is None:
            rgb = [r, g, b]
        # noinspection PyUnresolvedReferences
        i: cython.int
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
        """
        Set the ROI color of the current SisypheROI instance from a QColor.

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            roi color
        """
        if isinstance(c, QColor):
            self._color = list(c.getRgbF())[:3]
            self._initLut()
        else: raise TypeError('parameter type {} is not QColor.'.format(type(c)))

    def getAlpha(self) -> float:
        """
        Set the ROI opacity of the current SisypheROI instance.

        Returns
        -------
        float
            opacity, between 0.0 and 1.0
        """
        return self._alpha

    def setAlpha(self, a: int | float) -> None:
        """
        Set the ROI opacity of the current SisypheROI instance.

        Parameters
        ----------
        a : float | int
            - float, opacity, between 0.0 and 1.0
            - int, opacity, between 0 and 255
        """
        if isinstance(a, float):
            if 0.0 <= a <= 1.0: self._alpha = a
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(a))
        elif isinstance(a, int):
            if 0 <= a <= 255: self._alpha = a / 255
            else: raise ValueError('parameter value {} is not between 0 and 255.'.format(a))
        else: raise TypeError('parameter type {} is not int or float.'.format(type(a)))
        self._initLut()

    def setVisibility(self, v: bool) -> None:
        """
        Set the ROI visibility of the current SisypheROI instance.

        Parameters
        ----------
        v : bool
            visible if True
        """
        if isinstance(v, bool): self._visibility = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setVisibilityOn(self) -> None:
        """
        Show the current SisypheROI instance.
        """
        self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        """
        Hide the current SisypheROI instance.
        """
        self.setVisibility(False)

    def getVisibility(self) -> bool:
        """
        Get the ROI visibility of the current SisypheROI instance.

        Returns
        -------
        bool
            True if visible
        """
        return self._visibility

    def getLut(self) -> SisypheLut:
        """
        Get the look-up table colormap attribute of the current SisypheROI instance. The Lut attribute exists only for
        compatibility with SisypheImage ancestor class and display widgets. All lut elements have the same color,
        i.e. the color attribute of the current SisypheROI instance.

        Returns
        -------
        Sisyphe.core.sisypheLUT.SisypheLut
            roi lut
        """
        return self._lut

    def getvtkLookupTable(self) -> vtkLookupTable:
        """
        Get the look-up table colormap attribute of the current SisypheROI instance. The Lut attribute exists only for
        compatibility with SisypheImage ancestor class and display widgets. All lut elements have the same color,
        i.e. the color attribute of the current SisypheROI instance.

        Returns
        -------
        vtk.vtkLookupTable
            roi lut
        """
        return self._lut.getvtkLookupTable()

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current SisypheROI instance. A ROI is defined in the space of a reference
        SisypheVolume whose ID is the reference ID.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def setReferenceID(self, ID: SisypheROI | SisypheVolume | str) -> None:
        """
        Set the reference ID attribute of the current SisypheROI instance. A ROI is defined in the space of a reference
        SisypheVolume whose ID is the reference ID.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheROI.SisypheROI | Sisyphe.core.sisypheVolume.SisypheVolume
            - str, ID
            - SisypheROI's reference ID attribute
            - SisypheVolume's ID attribute
        """
        if isinstance(ID, SisypheROI):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, (SisypheImage, SisypheVolume)):
            self._referenceID = ID.getID()
        elif isinstance(ID, str):
            self._referenceID = ID
        else: raise TypeError('parameter type {} is not SisypheImage, SisypheVolume or str'.format(type(ID)))

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID of the current SisypheROI instance is defined (not '').

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID != ''

    def setCompression(self, v: bool) -> None:
        """
        Set the compression attribute of the current SisypheROI instance. PySisyphe ROI format (.xroi) can be
        optionally gzipped.

        Parameters
        ---------
        v : bool
            compression is enabled if True
        """
        if isinstance(v, bool):
            self._compression = v

    def setCompressionOn(self) -> None:
        """
        Enables gzip file compression of the current SisypheROI instance. PySisyphe ROI format (.xroi) can be
        optionally gzipped.
        """
        self._compression = True

    def setCompressionOff(self) -> None:
        """
        Disables gzip file compression of the current SisypheROI instance. PySisyphe ROI format (.xroi) can be
        optionally gzipped.
        """
        self._compression = False

    def getCompression(self) -> bool:
        """
        Get the gzip file compression attribute of the current SisypheROI instance. PySisyphe ROI format (.xroi) can be
        optionally gzipped.

        Returns
        -------
        bool
            True if compression is on
        """
        return self._compression

    def toIndexes(self, numpy: bool = False) -> list | ndarray:
        """
        Get a list of voxels indexes (x, y, z).

        Parameters
        ----------
        numpy : bool
            return numpy ndarray if True, list otherwise

        Returns
        -------
        list | ndarray
            list of voxels indexes
        """
        a = self.getNumpy(defaultshape=False)
        idx = array(where(a == 1)).T
        if numpy: return idx
        else: return list([list(v) for v in idx])

    def fromIndexes(self, idx: list | ndarray) -> None:
        """
        Set voxels from a list of indexes (x, y, z).

        Parameters
        ----------
        idx : list | ndarray
            list of voxels indexes
        """
        if isinstance(idx, list):
            idx = array([array(v) for v in idx])
        img = zeros(shape=self.getSize(), dtype='unit8')
        idx = idx.T
        x = idx[0]
        y = idx[1]
        z = idx[2]
        img[x, y, z] = 1
        self._sitk_image = sitkGetImageFromArray(img.T)
        self._updateImages()

    # Processing

    def flip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> None:
        """
        Flip ROI image axes of the current SisypheROI instance. The current SisypheROI instance is overwritten.

        Parameters
        ----------
        fx : bool
            flip x-axis if True (default False)
        fy : bool
            flip y-axis if True (default False)
        fz : bool
            flip z-axis if True (default False)
        """
        self.setSITKImage(sitkFlip(self.getSITKImage(), [fx, fy, fz]))

    def shift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> None:
        """
        ROI image shift of the current SisypheROI instance. The current SisypheROI instance is overwritten.

        Parameters
        ----------
        sx : int
            shift of sx voxels in x-axis (default 0)
        sy : int
            shift of sy voxels in y-axis (default 0)
        sz : int
            shift of sz voxels in z-axis (default 0)
        """
        self.setSITKImage(sitkShift(self.getSITKImage(), [sx, sy, sz]))

    def morphoDilate(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        ROI image morphological dilatation of the current SisypheROI instance. The current SisypheROI instance is
        overwritten.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        self.setSITKImage(sitkBinaryDilate(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoErode(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        ROI image morphological erosion of the current SisypheROI instance. The current SisypheROI instance is
        overwritten.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        self.setSITKImage(sitkBinaryErode(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoOpening(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        ROI image morphological opening of the current SisypheROI instance. The current SisypheROI instance is
        overwritten.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        self.setSITKImage(sitkBinaryOpening(self.getSITKImage(), [radius, radius, radius], struct))

    def morphoClosing(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        ROI image morphological closing of the current SisypheROI instance. The current SisypheROI instance is
        overwritten.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        self.setSITKImage(sitkBinaryClosing(self.getSITKImage(), [radius, radius, radius], struct))

    def fillHoles(self) -> None:
        """
        Fill holes in the ROI image of the current SisypheROI instance. The current SisypheROI instance is overwritten.
        """
        self.setSITKImage(sitkBinaryFillHole(self.getSITKImage()))

    # < Revision 30/07/2024
    # add removeBlobByDistance method
    def removeBlobByDistance(self, d: float):
        """
        Remove blobs until the remaining ones are spaced more than a given distance from one another. By default,
        smaller objects are removed first. The current SisypheROI instance is overwritten.

        Parameters
        ----------
        d : float
            minimal distance between blobs in mm
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                img = sitkRelabelComponent(img)
                np = sitkGetArrayFromImage(img).T
                rnp = remove_objects_by_distance(np, d, p_norm=2, spacing=self.getSpacing())
                self.copyFromNumpyArray(rnp.astype('uint8'), spacing=self.getSpacing())
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 30/07/2024 >

    # < Revision 01/08/2024
    # add pruning method
    def pruning(self, blob: int = 0):
        """
        Remove "spurs" of less than a certain length in the current SisypheROI instance. The current SisypheROI
        instance is overwritten.

        Parameters
        ----------
        blob : int
            blob index or 0 (whole image, default)
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                if blob > 0:
                    img = sitkConnectedComponent(self.getSITKImage())
                    img = (img == blob)
                else: img = self.getSITKImage()
                self.setSITKImage(sitkBinaryPruning(img))
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add clearBorderBlobs method
    def clearBorderBlobs(self):
        """
        Clear blob(s) connected to the border of the current SisypheROI instance. The current SisypheROI instance is
        overwritten.
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                rnp = clear_border(self.getNumpy())
                self.copyFromNumpyArray(rnp.astype('uint8'), spacing=self.getSpacing())
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 01/08/2024 >

    def getFlip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> SisypheROI:
        """
        Flip ROI image axes of a copy of the current SisypheROI instance.

        Parameters
        ----------
        fx : bool
            flip x-axis if True (default False)
        fy : bool
            flip y-axis if True (default False)
        fz : bool
            flip z-axis if True (default False)

        Returns
        -------
        SisypheROI
            flipped roi
        """
        roi = SisypheROI(sitkFlip(self.getSITKImage(), [fx, fy, fz]))
        self.copyAttributesTo(roi)
        return roi

    def getShift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> SisypheROI:
        """
        ROI image shift of a copy of the current SisypheROI instance.

        Parameters
        ----------
        sx : int
            shift of sx voxels in x-axis (default 0)
        sy : int
            shift of sy voxels in y-axis (default 0)
        sz : int
            shift of sz voxels in z-axis (default 0)

        Returns
        -------
        SisypheROI
            shifted roi
        """
        roi = SisypheROI(sitkShift(self.getSITKImage(), [sx, sy, sz]))
        self.copyAttributesTo(roi)
        return roi

    def getMorphoDilate(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        """
        ROI image morphological dilatation of a copy of the current SisypheROI instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROI
            dilated roi
        """
        roi = SisypheROI(sitkBinaryDilate(self.getSITKImage(), [radius, radius, radius], struct))
        self.copyAttributesTo(roi)
        return roi

    def getMorphoErode(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        """
        ROI image morphological erosion of a copy of the current SisypheROI instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROI
            eroded roi
        """
        roi = SisypheROI(sitkBinaryErode(self.getSITKImage(), [radius, radius, radius], struct))
        self.copyAttributesTo(roi)
        return roi

    def getMorphoOpening(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        """
        ROI image morphological opening of a copy of the current SisypheROI instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROI
            morphology opening roi
        """
        roi = SisypheROI(sitkBinaryOpening(self.getSITKImage(), [radius, radius, radius], struct))
        self.copyAttributesTo(roi)
        return roi

    def getMorphoClosing(self, radius: int = 1, struct: int = sitkBall) -> SisypheROI:
        """
        ROI image morphological closing of a copy of the current SisypheROI instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROI
            morphology closing roi
        """
        roi = SisypheROI(sitkBinaryClosing(self.getSITKImage(), [radius, radius, radius], struct))
        self.copyAttributesTo(roi)
        return roi

    def getFillHoles(self) -> SisypheROI:
        """
        Fill holes in the ROI image of a copy of the current SisypheROI instance.

        Returns
        -------
        SisypheROI
            roi without hole
        """
        roi = SisypheROI(sitkBinaryFillHole(self.getSITKImage()))
        self.copyAttributesTo(roi)
        return roi

    def getMajorBlob(self) -> SisypheROI:
        """
        Clear all blobs (connected components) except the major one (most voxels) in the ROI image of a copy of the
        current SisypheROI instance.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                img = sitkRelabelComponent(img)
                img = (img == 1)
                roi = SisypheROI(img)
                self.copyAttributesTo(roi)
                return roi
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')

    def getBlobLargerThan(self, n: int) -> SisypheROI:
        """
        Remove blobs (connected components) with less than n voxels from the ROI image of a copy of the current
        SisypheROI instance.

        Returns
        -------
        SisypheROI
            processed roi
        """
        img = sitkConnectedComponent(self.getSITKImage())
        img = sitkRelabelComponent(img, minimumObjectSize=n)
        roi = SisypheROI(img > 0)
        self.copyAttributesTo(roi)
        return roi

    # < Revision 30/07/2024
    # add getRemoveBlobByDistance method
    def getRemoveBlobByDistance(self, d: float) -> SisypheROI:
        """
        Remove blobs until the remaining ones are spaced more than a given distance from one another. By default,
        smaller objects are removed first.

        Parameters
        ----------
        d : float
            minimal distance between blobs in mm

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                img = sitkRelabelComponent(img)
                np = sitkGetArrayFromImage(img).T
                rnp = remove_objects_by_distance(np, d, p_norm=2, spacing=self.getSpacing())
                roi = SisypheROI()
                roi.copyFromNumpyArray(rnp.astype('uint8'), spacing=self.getSpacing())
                roi.copyAttributesFrom(self)
                return roi
            else: return self
        else: raise AttributeError('Image is empty.')
    # Revision 30/07/2024 >

    # < Revision 01/08/2024
    # add getSkeletonize method
    def getPruning(self, blob: int = 0) -> SisypheROI:
        """
        Remove "spurs" of less than a certain length in the current SisypheROI instance.

        Parameters
        ----------
        blob : int
            blob index or 0 (whole image, default)

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                if blob > 0:
                    img = sitkConnectedComponent(self.getSITKImage())
                    img = (img == blob)
                else: img = self.getSITKImage()
                img = sitkBinaryPruning(img)
                r = SisypheROI()
                r.copyFromSITKImage(img)
                r.copyAttributesFrom(self)
                return r
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 01/08/2024 >

    def getBlobCount(self) -> int:
        """
        Get the number of blobs (connected components) in the ROI image of the current SisypheROI instance.

        Returns
        -------
        int
            number of blobs
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                img = sitkConnectedComponent(self.getSITKImage())
                # noinspection PyArgumentList
                return sitkGetArrayViewFromImage(img).max()
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')

    # < Revision 01/08/2024
    # add getSkeletonize method
    def getClearBorderBlobs(self) -> SisypheROI:
        """
        Clear blob(s) connected to the border of the current SisypheROI instance.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                rnp = clear_border(self.getNumpy())
                r = SisypheROI()
                r.copyFromNumpyArray(rnp)
                r.copyAttributesFrom(self)
                return r
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add getSkeletonize method
    def getSkeletonize(self, blob: int = 0) -> SisypheROI:
        """
        Calculate the skeleton of the current SisypheROI instance.

        Parameters
        ----------
        blob : int
            blob index or 0 (whole image, default)

        Returns
        -------
        SisypheROI
            skeleton roi
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                if blob > 0:
                    img = sitkConnectedComponent(self.getSITKImage())
                    img = (img == blob)
                else: img = self.getSITKImage()
                img = sitkBinaryThinning(img)
                r = SisypheROI()
                r.copyFromSITKImage(img)
                r.copyAttributesFrom(self)
                return r
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 01/08/2024 >

    # < Revision 30/07/2024
    # add getRemoveBlobByDistance method
    def getDistanceMap(self, blob: int = 0, output: str = 'xvol') -> Image | ndarray | SisypheVolume:
        """
        Calculates the Euclidean distance transform of the current SisypheROI instance.

        Parameters
        ----------
        blob : int
            blob index or 0 (all image, default)
        output : str
            output image type: 'sitk', 'numpy', 'xvol'

        Returns
        -------
        SimpleITK.Image | numpy.ndarray | Sisyphe.core.sisypheVolume.SisypheVolume
            distance map
        """
        if not self.isEmpty():
            if not self.isEmptyArray():
                if blob > 0:
                    img = sitkConnectedComponent(self.getSITKImage())
                    img = (img == blob)
                else: img = self.getSITKImage()
                dmap = sitkSignedMaurerDistanceMap(img, False, False, True)
                if output == 'sitk': return dmap
                elif output == 'numpy':
                    r = sitkGetArrayFromImage(dmap).T
                    return r
                else:
                    r = SisypheVolume()
                    r.copyFromSITKImage(dmap)
                    r.acquisition.setSequenceToDistanceMap()
                    # < Revision 25/10/2024
                    r.setID(self._referenceID)
                    # Revision 25/10/2024 >
                    return r
            else: raise AttributeError('Image array is empty.')
        else: raise AttributeError('Image is not defined.')
    # Revision 31/07/2024 >

    # < Revision 30/07/2024
    # add getEulerNumber method
    def getEulerNumber(self, connectivity: int = 26) -> int:
        """
        Calculate the Euler characteristic of the current SisypheROI instance.
        The Euler number is obtained as the number of blobs plus the number of holes, minus the number of tunnels, or loops.

        Parameters
        ----------
        connectivity : int
            6 or 26

        Returns
        -------
        int
            Euler number
        """
        if connectivity in (6, 26):
            if connectivity == 6: connectivity = 1
            else: connectivity = 3
            return euler_number(self.getNumpy(defaultshape=False), connectivity)
        else: raise ValueError('Invalid connectivity ({}), must be 6 or 26.'.format(connectivity))
    # Revision 30/07/2024 >

    def clear(self) -> None:
        """
        Clear the ROI image of the current SisypheROI instance (Filling roi with 0).
        """
        self.getNumpy().fill(0)

    # Draw methods

    def drawLine(self, p0: vectorInt3, p1: vectorInt3, orient: int = 0) -> None:
        """
        Draw a line in the ROI image of the current SisypheROI instance. Line is drawn in a single slice (points p0
        and p1 must be within the same slice)

        Parameters
        ----------
        p0 : tuple[int, int, int] | list[int, int, int]
            x, y, z first point coordinates
        p1 : tuple[int, int, int] | list[int, int, int]
            x, y, z second point coordinates
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
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

    def drawDisk(self, p: vectorInt3, radius: int, orient: int = 0) -> None:
        """
        Draw a disk in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center point coordinates
        radius : int
            disk radius (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
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

    def drawEllipse(self, p: vectorInt3, radius: vectorInt2, rot: float = 0.0, orient: int = 0) -> None:
        """
        Draw an ellipse in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center point coordinates
        radius : tuple[int, int] | list[int, int]
            radius in x and y axes (in voxels)
        rot : float
            set the ellipse rotation in radians (between -pi and pi, default 0.0)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
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

    def drawSquare(self, p: vectorInt3, extent: int, orient: int = 0) -> None:
        """
        Draw a square in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : int
            length of square sides (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
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

    def drawRectangle(self, p: vectorInt3, extent: vectorInt2, orient: int = 0) -> None:
        """
        Draw a rectangle in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : tuple[int, int] | list[int, int]
            width and height (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
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

    def drawPolygon(self, p: list[list[int]], orient: int = 0) -> None:
        """
        Draw a polygon in the ROI image of the current SisypheROI instance. Polygon is drawn in a single slice (all
        points must be within the same slice).

        Parameters
        ----------
        p : list[list[int]]
            - list of 3 list[int]:
                - first list[int],  x coordinates of points
                - second list[int], y coordinates of points
                - third list[int],  z coordinates of points
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        px = p[0]
        py = p[1]
        pz = p[2]
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

    def drawCube(self, p: vectorInt3, extent: int) -> None:
        """
        Draw a cube in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : int
            length of cube sides (in voxels)
        """
        extent = (extent,) * 3
        img = self.getNumpy()
        z, y, x = rectangle(start=(p[2], p[1], p[0]), extent=extent)
        img[z, y, x] = 1

    def drawParallelepiped(self, p: vectorInt3, extent: vectorInt3) -> None:
        """
        Draw a parallelepiped in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : tuple[int, int, int] | list[int, int, int]
            width, height and depth (in voxels)
        """
        img = self.getNumpy()
        z, y, x = rectangle(start=(p[2], p[1], p[0]), extent=(extent[2], extent[1], extent[0]))
        img[z, y, x] = 1

    def drawSphere(self, p: vectorInt3, radius: int) -> None:
        """
        Draw a sphere in the ROI image of the current SisypheROI instance.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center coordinates
        radius : int
            sphere radius (in voxels)
        """
        sph = ellipsoid(radius, radius, radius,
                        spacing=self.getSpacing()).astype('uint8')
        sph = sph[2:-2, 2:-2, 2:-2]
        x, y, z = p
        xmax, ymax, zmax = self.getSize()
        if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
            # noinspection PyUnresolvedReferences
            idx1: cython.int = radius - 1 - x
            # noinspection PyUnresolvedReferences
            idy1: cython.int = radius - 1 - y
            # noinspection PyUnresolvedReferences
            idz1: cython.int = radius - 1 - z
            # noinspection PyUnresolvedReferences
            idx2: cython.int = xmax - x - radius
            # noinspection PyUnresolvedReferences
            idy2: cython.int = ymax - y - radius
            # noinspection PyUnresolvedReferences
            idz2: cython.int = zmax - z - radius
            if idx1 < 0: x, idx1 = -idx1, 0
            else: x = 0
            if idy1 < 0: y, idy1 = -idy1, 0
            else: y = 0
            if idz1 < 0: z, idz1 = -idz1, 0
            else: z = 0
            # noinspection PyUnresolvedReferences
            m: cython.int = 2 * radius - 1
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
        """
        Create a 3D contour of the ROI mask of the current SisypheROI instance (uses vtk.vtkContourFilter).

        Returns
        -------
        vtk.vtkPolyData
            vtkPolydata surface of roi
        """
        filtr = vtkImageCast()
        filtr.SetInputData(self.getVTKImage())
        filtr.SetOutputScalarTypeToFloat()
        # noinspection PyArgumentList
        filtr.Update()
        mask = filtr.GetOutput()
        filtr = vtkContourFilter()
        filtr.SetInputData(mask)
        filtr.ComputeNormalsOn()
        filtr.SetValue(0, 0.5)
        # noinspection PyArgumentList
        filtr.Update()
        return filtr.GetOutput()

    def getVtkMarchingCubeContourPolyData(self) -> vtkPolyData:
        """
        Create a 3D contour of the ROI mask of the current SisypheROI instance (uses vtk.vtkMarchingCubes).

        Returns
        -------
        vtk.vtkPolyData
            vtkPolydata surface of roi
        """
        filtr = vtkImageCast()
        filtr.SetInputData(self.getVTKImage())
        filtr.SetOutputScalarTypeToFloat()
        # noinspection PyArgumentList
        filtr.Update()
        mask = filtr.GetOutput()
        filtr = vtkMarchingCubes()
        filtr.SetInputData(mask)
        filtr.ComputeNormalsOn()
        filtr.SetValue(0, 0.5)
        # noinspection PyArgumentList
        filtr.Update()
        return filtr.GetOutput()

    def getVtkContourActor(self) -> vtkActor:
        """
        Create a 3D contour of the ROI mask of the current SisypheROI instance (uses vtk.vtkContourFilter).

        Returns
        -------
        vtk.vtkActor
            vtkActor surface of roi
        """
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(self.getVtkContourPolyData())
        mapper.ScalarVisibilityOff()
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
        return actor

    def getVtkMarchingCubeContourActor(self) -> vtkActor:
        """
        Create a 3D contour of the ROI mask of the current SisypheROI instance (uses vtk.vtkMarchingCubes).

        Returns
        -------
        vtk.vtkActor
            vtkActor surface of roi
        """
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(self.getVtkMarchingCubeContourPolyData())
        mapper.ScalarVisibilityOff()
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self._color[0], self._color[1], self._color[2])
        return actor

    # IO old version 1.0, deprecated methods

    def createXMLOld(self, doc: minidom.Document) -> None:
        """
        Deprecated, use createXML() method
        """
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
        """
        Deprecated, use parseXML() method
        """
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
        """
        Deprecated, use saveAs() method
        """
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
        """
        Deprecated, use load() method
        """
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

    def save(self, filename: str = '', single: bool = True) -> None:
        """
        Save the current SisypheROI instance to a PySisyphe ROI (.xroi) file. This method uses the file name attribute
        of the current SisypheROI instance.

        Parameters
        ----------
        filename : str
            PySisyphe ROI file name (optional), if filename is empty ('', default), the file name attribute of the
            current SisypheROI instance is used
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xroi file and the binary part in .raw file
        """
        if not self.isEmpty():
            if filename != '': self.saveAs(filename, single)
            elif self.hasFilename(): self.saveAs(self._filename, single)
            else: raise IOError('parameter and filename attribute are empty.')
        else: raise ValueError('Voxel data array is empty.')

    def createXML(self, doc: minidom.Document, single: bool = True) -> None:
        """
        Write the current SisypheROI instance attributes to xml instance. This method is called by save() and saveAs()
        methods, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xroi file and the binary part in .raw file
        """
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
        """
        Save the current SisypheROI instance to PySisyphe ROI (.xroi) file.

        Parameters
        ----------
        filename : str
            PySisypheROI file name
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xroi file and the binary part in .raw file
        """
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

    # noinspection PyTypeChecker
    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheROI instance attributes from xml instance. This method is called by load() method, it
        is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict[str]
        Keys:
        - 'size', list[int], image size in each axis
        - 'spacing', list[float], voxel size in each axis
        - 'array', bytes, array image
        """
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
        """
        Load the current SisypheROI instance from a PySisyphe ROI (.xroi) file.

        Parameters
        ----------
        filename : str
            PySisyphe ROI file name
        """
        # Check extension xroi
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
        if exists(filename):
            # Read XML part
            with open(filename, 'rb') as f:
                ln = ''
                strdoc = ''
                while ln != '</xroi>\n':
                    ln = f.readline().decode()  # Convert binary to utf-8
                    strdoc += ln
                self._filename = filename
                doc = minidom.parseString(strdoc)
                attr = self.parseXML(doc)
                # < Revision 04/04/2025
                self._name = splitext(basename(filename))[0]
                # Revision 04/04/2025 >
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
        """
        Load the current SisypheROI instance from old Sisyphe ROI (.roi) file.

        Parameters
        ----------
        filename : str
            old Sisyphe ROI file name
        index : int
            ROI index in the old Sisyphe ROI file (default 0, first ROI)
        """
        if exists(filename):
            from Sisyphe.core.sisypheConstants import getSisypheROIExt
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
        """
        Load the current SisypheROI instance from BrainVoyager files. BrainVoyager's ROI format can include several
        ROIs, an index parameter is provided to select the ROI to be loaded.

        Parameters
        ----------
        vmr : str
            BrainVoyager image file name (.vmr)
        voi : str
            BrainVoyager ROI file name (.voi)
        index : int
            ROI index in the BrainVoyager ROI file
        """
        if exists(vmr):
            from Sisyphe.core.sisypheConstants import getBrainVoyagerVMRExt
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
            from Sisyphe.core.sisypheConstants import getBrainVoyagerVOIExt
            path, ext = splitext(voi)
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
                    self.setColor(rgb=voi['ColorOfVOI'])
                    self.setName(voi['NameOfVOI'])
                    self.setOrigin()
                    self.setDirections(getRegularDirections())
            else: raise IOError('{} is not a BrainVoyager VOI file extension.'.format(ext))
        else: raise IOError('no such file {}.'.format(vmr))


class SisypheROICollection(object):
    """
    Description
    ~~~~~~~~~~~

    Named list container of SisypheROI instances. Container key to address elements can be an int index, a roi name str
    or a SisypheROI instance (uses name attribute as str key).

    Getter methods of the SisypheROI class are added to the SisypheROICollection class, returning a list of values
    returned by each SisypheROI element in the container.

    Scope of methods:

        - resampling (apply geometric transformation),
        - converting to and from SisypheVolume label,
        - setter and getter methods of sisypheROI instances in the collection,
        - set operators (union, intersection, difference, symmetric difference),
        - flip/shift,
        - morphology operators (dilate, erode, closing, opening),
        - fill holes,
        - IO methods.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheROICollection

    Creation: 08/09/2022
    Last revision: 23/05/2024
    """

    __slots__ = ['_rois', '_index', '_referenceID']

    # Private method

    def _verifyID(self, roi: SisypheROI) -> None:
        if isinstance(roi, SisypheROI):
            if self.isEmpty(): self.setReferenceID(roi.getReferenceID())
            if self.hasReferenceID():
                if roi.getReferenceID() != self._referenceID:
                    # noinspection PyUnresolvedReferences
                    if roi.getSize() == self.rois[0].getSize():
                        roi.setReferenceID(self._referenceID)
                    else:
                        raise ValueError('ROI reference ID ({}) is not '
                                         'compatible with collection reference ID ({}).'.format(roi.getReferenceID(),
                                                                                                self._referenceID))
            else: self.setReferenceID(roi.getReferenceID())
        else: raise TypeError('parameter type {} is not SisypheROI or SisypheROICollection.'.format(type(roi)))

    # Special methods

    """
    Private attributes

    _rois           list[SisypheROI]
    _index          int, index for iterator
    _referenceID    str
    """

    def __init__(self) -> None:
        """
        SisypheROICollection instance constructor.
        """
        super().__init__()
        self._rois: list = list()
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        self._referenceID: str = ''

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheROICollection instance to str
        """
        # noinspection PyUnresolvedReferences
        index: cython.int = 0
        buff: str = 'SisypheROI count #{}\n'.format(len(self._rois))
        for roi in self._rois:
            index += 1
            buff += 'SisypheROI #{}\n'.format(index)
            buff += '{}\n'.format(str(roi))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheROICollection instance representation
        """
        return 'SisypheROICollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, key: int | str | slice | list[str]) -> SisypheROI | SisypheROICollection:
        """
        Special overloaded container getter method. Get SisypheROI element from container. Key which can be int index,
        ROI name, slicing indexes (start:stop:step) or list of ROI names.

        Parameters
        ----------
        key : int | str | slice | list[str]
            index, ROI name, slicing indexes (start:stop:step) or list of ROI names

        Returns
        -------
        SisypheROI | SisypheROICollection
            SisypheROICollection if key is slice or list[str]
        """
        # key is Name str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._rois): return self._rois[key]
            else: raise IndexError('key parameter is out of range.')
        elif isinstance(key, slice):
            rois = SisypheROICollection()
            for i in range(key.start, key.stop, key.step):
                rois.append(self._rois[i])
            return rois
        elif isinstance(key, list):
            rois = SisypheROICollection()
            for i in range(len(self._rois)):
                if self._rois[i].getName() in key:
                    rois.append(self._rois[i])
            return rois
        else: raise TypeError('parameter type {} is not int, str, slice or list[str].'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheROI) -> None:
        """
        Special overloaded container setter method. Set a SisypheROI element in the container.

        Parameters
        ----------
        key : int
            index
        value : SisypheROI
            ROI to be placed at key position
        """
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

    def __delitem__(self, key: int | str | SisypheROI) -> None:
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheROI element in the
        container.

        Parameters
        ----------
        key : int | str | SisypheROI
            index, ROI name or ROI name attribute of the SisypheROI
        """
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
        """
        Special overloaded method called by the built-in len() python function. Returns the number of SisypheROI
        elements in the container.

        Returns
        -------
        int
            number of SisypheROI elements
        """
        return len(self._rois)

    def __contains__(self, value: str | SisypheROI) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a SisypheROI is
        in the container.

        Parameters
        ----------
        value : str | SisypheROI
            ROI name or ROI name attribute of the SisypheMesh

        Returns
        -------
        bool
            True if value is in the container.
        """
        keys = [k.getName() for k in self._rois]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is SisypheROI
        elif isinstance(value, SisypheROI):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or SisypheROI.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> SisypheROI:
        """
        Special overloaded container called by the built-in 'next()' and 'for ... in' python iterator method. Returns
        the next value for the iterable.
        """
        if self._index < len(self._rois):
            n = self._index
            self._index += 1
            return self._rois[n]
        else: raise StopIteration

    def __getattr__(self, name: str):
        """
        When attribute does not exist in the class, try calling the setter or getter method of sisypheROI instances in
        collection. Getter methods return a list of the same size as the collection.

        Parameters
        ----------
        name : str
            attribute name of the SisypheROI class (container element)
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
                    else: raise AttributeError('Not get/set method.')
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

    def setReferenceID(self, ID: SisypheROI | SisypheVolume | str) -> None:
        """
        Set reference ID attribute of the current SisypheROICollection instance. All ROIs in the container are defined
        in the space of a reference SisypheVolume whose ID is the reference ID.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheROI.SisypheROI | Sisyphe.core.sisypheVolume.SisypheVolume
            - str, ID
            - SisypheROI's ID attribute
            - SisypheVolume's ID attribute
        """
        if isinstance(ID, SisypheROI):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, SisypheVolume):
            self._referenceID = ID.getID()
        elif isinstance(ID, str):
            self._referenceID = ID
            if not self.isEmpty():
                for roi in self:
                    roi.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not SisypheROI or str'.format(type(ID)))

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current SisypheROICollection instance. All ROIs in the container are defined
        in the space of a reference SisypheVolume whose ID is the reference ID.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID of the current SisypheROICollection instance is defined (not '').

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID != ''

    def isEmpty(self) -> bool:
        """
        Checks if SisypheROICollection instance container is empty.

        Returns
        -------
        bool
            True if container is empty
        """
        return len(self._rois) == 0

    def count(self) -> int:
        """
        Get the number of SisypheROI elements in the current SisypheROICollection instance container.

        Returns
        -------
        int
            number of SisypheROI elements
        """
        return len(self._rois)

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current SisypheROICollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        return [k.getName() for k in self._rois]

    def remove(self, value: int | str | SisypheROI) -> None:
        """
        Remove a SisypheROI element from the current SisypheROICollection instance container.

        Parameters
        ----------
        value : int | str | SisypheROI
            - int, index of the SisypheROI to remove
            - str, ROI name of the SisypheROI to remove
            - SisypheROI to remove
        """
        # value is SisypheROI
        if isinstance(value, SisypheROI):
            self._rois.remove(value)
        # value is SisypheROI, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or SisypheROI.'.format(type(value)))

    def pop(self, key: int | str | SisypheROI | None = None) -> SisypheROI:
        """
         Remove a SisypheROI element from the current SisypheROICollection instance container and return it. If key is
         None, removes and returns the last element.

        Parameters
        ----------
        key : int | str | SisypheROI | None
            - int, index of the SisypheROI to remove
            - str, ROI name of the SisypheROI to remove
            - SisypheROI to remove
            - None, remove the last element

        Returns
        -------
        SisypheROI
            element removed from the container
        """
        if key is None: return self._rois.pop()
        # key is Name str or SisypheROI
        if isinstance(key, (str, SisypheROI)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._rois.pop(key)
        else: raise TypeError('parameter type {} is not int, str or SisypheROI.'.format(type(key)))

    def index(self, value: str | SisypheROI) -> int:
        """
        Index of a SisypheROI element in the current SisypheROICollection instance container.

        Parameters
        ----------
        value : str | SisypheROI
            ROI name or ROI element

        Returns
        -------
        int
            index
        """
        keys = [k.getName() for k in self._rois]
        # value is SisypheROI
        if isinstance(value, SisypheROI):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheROI.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current SisypheROICollection instance container.
        """
        self._rois.reverse()

    def append(self, value: SisypheROI | SisypheROICollection) -> None:
        """
        Append a SisypheROI element in the current SisypheROICollection instance container.

        Parameters
        ----------
        value : SisypheROI | SisypheROICollection
            ROI(s) to append
        """
        if isinstance(value, SisypheROI):
            self._verifyID(value)
            if value.getName() not in self: self._rois.append(value)
            else: self._rois[self.index(value)] = value
        elif isinstance(value, SisypheROICollection):
            if len(value) > 0:
                for roi in value:
                    self._verifyID(roi)
                    if roi.getName() not in self: self._rois.append(roi)
                    else: self._rois[self.index(roi)] = roi
        else: raise TypeError('parameter type {} is not SisypheROI or SisypheROICollection.'.format(type(value)))

    def insert(self, key: int | str | SisypheROI, value: SisypheROI):
        """
        Insert a SisypheROI element at the position given by the key in the current SisypheROICollection instance
        container.

        Parameters
        ----------
        key : int | str | SisypheROI
            - int, index
            - str, ROI name index
            - SisypheROI, ROI index
        value : SisypheROI
            ROI to insert
        """
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
        """
        Remove all elements from the current SisypheROICollection instance container (empty).
        """
        self._rois.clear()
        self._referenceID = ''

    def sort(self, reverse: bool = False):
        """
        Sort elements of the current SisypheROICollection instance container. Sorting is based on the name attribute of
        the SisypheROI elements, in the ascending order.

        Parameters
        ----------
        reverse : bool
            sorting in reverse order
        """
        def _getName(item):
            return item.getName()

        self._rois.sort(reverse=reverse, key=_getName)

    def copy(self) -> SisypheROICollection:
        """
        Copy the current SisypheROICollection instance container (Shallow copy of elements).

        Returns
        -------
        SisypheROICollection
            shallow copy of the collection
        """
        rois = SisypheROICollection()
        for roi in self._rois:
            rois.append(roi)
        return rois

    def copyToList(self) -> list[SisypheROI]:
        """
        Copy the current SisypheROICollection instance container to a list (Shallow copy of elements).

        Returns
        -------
        list[SisypheROI]
            shallow copy of the collection
        """
        rois = self._rois.copy()
        return rois

    def getList(self) -> list[SisypheROI]:
        """
        Get the list attribute of the current SisypheROICollection instance container (Shallow copy of the elements).

        Returns
        -------
        list[SisypheROI]
            shallow copy of the collection
        """
        return self._rois

    def resample(self,
                 trf: SisypheTransform,
                 save: bool = True,
                 dialog: bool = False,
                 prefix: str | None = None,
                 suffix: str | None = None,
                 wait: DialogWait | None = None):
        """
        Apply an affine geometric transformation to all the SisypheROI elements of the current SisypheROICollection
        instance container.

        Parameters
        ----------
        trf : SisypheTransform
            affine geometric transformation
        save : bool
            save resampled SisypheROI elements (default True)
        dialog : bool
            dialog box to choice file name of each resampled SisypheROI element (default False)
        prefix : str | None
         prefix added to file name of the resampled SisypheROI elements (optional)
        suffix : str | None
            suffix added to file name of the resampled SisypheROI elements (optional)
        wait : DialogWait | None
            progress bar dialog (optional)
        """
        if not self.isEmpty():
            from Sisyphe.core.sisypheTransform import SisypheTransform
            from Sisyphe.core.sisypheTransform import SisypheApplyTransform
            if isinstance(trf, SisypheTransform):
                f = SisypheApplyTransform()
                f.setTransform(trf)
                c = SisypheROICollection()
                for roi in self:
                    f.setMovingROI(roi)
                    c.append(f.resampleROI(save, dialog, prefix, suffix, wait))
                return c
            else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(trf)))
        else: raise ValueError('ROI collection is empty.')

    def toLabelVolume(self) -> SisypheVolume:
        """
        Convert the current SisypheROICollection instance into a SisypheVolume instance of labels. The label value of
        each ROI in the SisypheVolume instance is its int index in the SisypheROICollection container.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            label volume
        """
        if not self.isEmpty():
            self.sort()
            roi = self[0].getSITKImage()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(1, self.count()):
                roi = roi + self[i].getSITKImage() * i
            roi = sitkCast(roi, getLibraryDataType('uint8', 'sitk'))
            rvol = SisypheVolume()
            rvol.setSITKImage(roi)
            rvol.acquisition.setModalityToLB()
            rvol.setID(self[0].getReferenceID())
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(self.count()):
                name = self[i].getName()
                if name == '': name = 'ROI#{}'.format(i + 1)
                rvol.acquisition.setLabel(i+1, name)
            return rvol
        else: raise AttributeError('Image is empty.')

    def fromLabelVolume(self, v: SisypheVolume) -> None:
        """
        Convert a SisypheVolume instance of labels to SisypheROI images added to the current SisypheROICollection
        instance. Each scalar value in the SisypheVolume instance is converted to a SisypheROI image, these scalar
        values are used as int index in the current SisypheROICollection instance.

        Parameters
        ----------
        v : Sisyphe.core.sisypheVolume.SisypheVolume
            label volume
        """
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self.clear()
                img = v.getSITKImage()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, 256):
                    # noinspection PyTypeChecker
                    r: sitkImage = (img == i)
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

    # Set operators

    def union(self) -> SisypheROI:
        """
        Apply union operator between sisypheROI instances in the current SisypheROICollection instance container.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            # noinspection PyUnresolvedReferences
            n: cython.int = self.count()
            roi = self[0]
            if n > 1:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    roi = roi | self[i]
            return roi
        else: raise AttributeError('Collection is empty.')

    def intersection(self) -> SisypheROI:
        """
        Apply intersection operator between sisypheROI instances in the current SisypheROICollection instance container.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            # noinspection PyUnresolvedReferences
            n: cython.int = self.count()
            roi = self[0]
            if n > 1:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    roi = roi & self[i]
            return roi
        else: raise AttributeError('Collection is empty.')

    def difference(self) -> SisypheROI:
        """
        Apply difference operator between sisypheROI instances in the current SisypheROICollection instance container.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            # noinspection PyUnresolvedReferences
            n: cython.int = self.count()
            roi = self[0]
            if n > 1:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    roi = roi - self[i]
            return roi
        else: raise AttributeError('Collection is empty.')

    def symmetricDifference(self) -> SisypheROI:
        """
        Apply symmetric difference operator between sisypheROI instances in the current SisypheROICollection instance container.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            # noinspection PyUnresolvedReferences
            n: cython.int = self.count()
            roi = self[0]
            if n > 1:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    roi = roi ^ self[i]
            return roi
        else: raise AttributeError('Collection is empty.')

    # Processing

    def flip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> None:
        """
        Flip SisypheROI instances axes in the current SisypheROICollection instance container.

        Parameters
        ----------
        fx : bool
            flip x-axis if True (default False)
        fy : bool
            flip y-axis if True (default False)
        fz : bool
            flip z-axis if True (default False)
        """
        if not self.isEmpty():
            for roi in self:
                roi.flip(fx, fy, fz)

    def shift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> None:
        """
        SisypheROI instances shift in the current SisypheROICollection instance container.

        Parameters
        ----------
        sx : int
            shift of sx voxels in x-axis (default 0)
        sy : int
            shift of sy voxels in y-axis (default 0)
        sz : int
            shift of sz voxels in z-axis (default 0)
        """
        if not self.isEmpty():
            for roi in self:
                roi.shift(sx, sy, sz)

    def morphoDilate(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        Morphological dilatation of the SisypheROI instances in the current SisypheROICollection instance container.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        if not self.isEmpty():
            for roi in self:
                roi.morphoDilate(radius, struct)

    def morphoErode(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        Morphological erosion of the SisypheROI instances in the current SisypheROICollection instance container.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        if not self.isEmpty():
            for roi in self:
                roi.morphoErode(radius, struct)

    def morphoOpening(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        Morphological opening of the SisypheROI instances in the current SisypheROICollection instance container.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        if not self.isEmpty():
            for roi in self:
                roi.morphoOpening(radius, struct)

    def morphoClosing(self, radius: int = 1, struct: int = sitkBall) -> None:
        """
        Morphological closing of the SisypheROI instances in the current SisypheROICollection instance container.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)
        """
        if not self.isEmpty():
            for roi in self:
                roi.morphoClosing(radius, struct)

    def fillHoles(self) -> None:
        """
        Fill holes of the SisypheROI instances in the current SisypheROICollection instance container.
        """
        if not self.isEmpty():
            for roi in self:
                roi.fillHoles()

    # < Revision 30/07/2024
    # add removeBlobByDistance method
    def removeBlobByDistance(self, d: float):
        """
        Remove blobs until the remaining ones are spaced more than a given distance from one another. By default,
        smaller objects are removed first.

        Parameters
        ----------
        d : float
            minimal distance between blobs in mm
        """
        if not self.isEmpty():
            for roi in self:
                roi.removeBlobByDistance(d)
    # Revision 30/07/2024 >

    # < Revision 01/08/2024
    # add pruning method
    def pruning(self, blob: int = 0):
        """
        Remove "spurs" of less than a certain length in the current SisypheROI instance.

        Parameters
        ----------
        blob : int
            blob index or 0 (whole image, default)
        """
        if not self.isEmpty():
            for roi in self:
                roi.pruning(blob)
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add clearBorderBlobs method
    def clearBorderBlobs(self):
        """
        Clear blob(s) connected to the border of the current SisypheROI instance.
        """
        if not self.isEmpty():
            for roi in self:
                roi.clearBorderBlobs()
    # Revision 01/08/2024 >

    def getFlip(self, fx: bool = False, fy: bool = False, fz: bool = False) -> SisypheROICollection:
        """
        Flip SisypheROI instances axes in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        fx : bool
            flip x-axis if True (default False)
        fy : bool
            flip y-axis if True (default False)
        fz : bool
            flip z-axis if True (default False)

        Returns
        -------
        SisypheROICollection
            collection of flipped roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getFlip(fx, fy, fz))
        return rois

    def getShift(self, sx: int = 0, sy: int = 0, sz: int = 0) -> SisypheROICollection:
        """
        SisypheROI instances shift in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        sx : int
            shift of sx voxels in x-axis (default 0)
        sy : int
            shift of sy voxels in y-axis (default 0)
        sz : int
            shift of sz voxels in z-axis (default 0)

        Returns
        -------
        SisypheROICollection
            collection of shifted roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getShift(sx, sy, sz))
        return rois

    def getMorphoDilate(self, radius: int = 1, struct: int = sitkBall) -> SisypheROICollection:
        """
        SisypheROI instances morphological dilatation in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROICollection
            collection of dilated roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getMorphoDilate(radius, struct))
        return rois

    def getMorphoErode(self, radius: int = 1, struct: int = sitkBall) -> SisypheROICollection:
        """
        SisypheROI instances morphological erosion in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROICollection
            collection of eroded roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getMorphoErode(radius, struct))
        return rois

    def getMorphoOpening(self, radius: int = 1, struct: int = sitkBall) -> SisypheROICollection:
        """
        SisypheROI instances morphological opening in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROICollection
            collection of morphology opening roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getMorphoOpening(radius, struct))
        return rois

    def getMorphoClosing(self, radius: int = 1, struct: int = sitkBall) -> SisypheROICollection:
        """
        SisypheROI instances morphological closing in a copy of the current SisypheROICollection instance.

        Parameters
        ----------
        radius : int
            structuring element radius (in voxels)
        struct : int
            structuring element shape, SimpleITK code (0 sitkAnnulus, 1 sitkBall, 2 sitkBox, 3 sitkCross)

        Returns
        -------
        SisypheROICollection
            collection of morphology closing roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getMorphoClosing(radius, struct))
        return rois

    def getFillHoles(self) -> SisypheROICollection:
        """
        Fill holes of the SisypheROI instances in a copy of the current SisypheROICollection instance.

        Returns
        -------
        SisypheROICollection
            collection of processed roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getFillHoles())
        return rois

    def getMajorBlob(self) -> SisypheROICollection:
        """
        Clear all blobs (connected components) except the major one (most voxels) of the SisypheROI instances in a copy
        of the current SisypheROICollection instance.

        Returns
        -------
        SisypheROICollection
            collection of processed roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getMajorBlob())
        return rois

    def getBlobLargerThan(self, n: int) -> SisypheROICollection:
        """
        Remove blobs (connected components) with less than n voxels from the SisypheROI instances in a copy of the
        current SisypheROICollection instance.

        Returns
        -------
        SisypheROICollection
            collection of processed roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getBlobLargerThan(n))
        return rois

    def getBlobCount(self) -> list[int]:
        """
        Get the number of blobs (connected components) in the SisypheROI instances in a copy of the current
        SisypheROICollection instance.

        Returns
        -------
        list[int]
            number of blobs in each SisypheROI instance
        """
        r = list()
        if not self.isEmpty():
            for roi in self:
                r.append(roi.getBlobCount())
        return r

    # < Revision 01/08/2024
    # add getSkeletonize method
    def getClearBorderBlobs(self) -> SisypheROICollection:
        """
        Clear blob(s) connected to the border of the current SisypheROI instance.

        Returns
        -------
        SisypheROICollection
            collection of processed roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getClearBorderBlobs())
        return rois
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add getSkeletonize method
    def getSkeletonize(self, blob: int = 0) -> SisypheROICollection:
        """
        Calculate the skeleton of the current SisypheROI instance.

        Parameters
        ----------
        blob : int
            blob index or 0 (whole image, default)

        Returns
        -------
        SisypheROI
            collection of skeleton roi(s)
        """
        rois = SisypheROICollection()
        for roi in self:
            rois.append(roi.getSkeletonize(blob))
        return rois
    # Revision 01/08/2024 >

    # < Revision 30/07/2024
    # add getEulerNumber method
    def getEulerNumber(self, connectivity: int = 26) -> list[int]:
        """
        Calculate the Euler characteristic of the current SisypheROI instance. The Euler number is obtained as the
        number of blobs plus the number of holes, minus the number of tunnels, or loops.

        Parameters
        ----------
        connectivity : int
            6 or 26

        Returns
        -------
        list[int]
            Euler number(s)
        """
        r = list()
        for roi in self:
            r.append(roi.getEulerNumber(connectivity))
        return r
    # Revision 30/07/2024 >

    # < Revision 01/08/2024
    # add roiVotingCombination method
    def roiVotingCombination(self) -> SisypheROI:
        """
        Performs a pixelwise combination of ROIs, where each of them represents a segmentation of the same image. Label
        voting is a simple method of classifier combination applied to image segmentation. Typically, the accuracy of
        the combined segmentation exceeds the accuracy of the input segmentations. Voting is therefore commonly used as
        a way of boosting segmentation performance.

        The use of label voting for combination of multiple segmentations is described in T. Rohlfing and C. R. Maurer,
        Jr., "Multi-classifier framework for atlas-based image segmentation," Pattern Recognition Letters, 2005.

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            lroi = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(self._rois)):
                lroi.append(self._rois[i].getSITKImage())
            f = sitkComposeImageFilter()
            rois = f.Execute(lroi)
            img = sitkLabelVoting(rois)
            r = SisypheROI()
            r.copyFromSITKImage(img)
            r.copyAttributesFrom(self._rois[0])
            r.setDefaultFilename()
            r.setFilenamePrefix('voting')
            return r
        else: raise AttributeError('Collection is empty.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add roiSTAPLECombination method
    def roiSTAPLECombination(self) -> SisypheROI:
        """
        Performs a pixelwise combination of ROIs, where each of them represents a segmentation of the same image. The
        labelings are weighted relative to each other based on their "performance" as estimated by an
        expectation-maximization algorithm. In the process, a ground truth segmentation is estimated, and the estimated
        performances of the individual segmentations are relative to this estimated ground truth.

        The algorithm is based on the binary STAPLE algorithm by Warfield et al. : S. Warfield, K. Zou, W. Wells,
        "Validation of image segmentation and expert quality with an expectation-maximization algorithm" in MICCAI
        2002: Fifth International Conference on Medical Image Computing and Computer-Assisted Intervention,
        Springer-Verlag, Heidelberg, Germany, 2002, pp. 298-306

        Returns
        -------
        SisypheROI
            processed roi
        """
        if not self.isEmpty():
            lroi = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(self._rois)):
                lroi.append(self._rois[i].getSITKImage())
            f = sitkComposeImageFilter()
            rois = f.Execute(lroi)
            img = sitkMultiLabelSTAPLE(rois)
            r = SisypheROI()
            r.copyFromSITKImage(img)
            r.copyAttributesFrom(self._rois[0])
            r.setDefaultFilename()
            r.setFilenamePrefix('staple')
            return r
        else: raise AttributeError('Collection is empty.')
    # Revision 01/08/2024 >

    # IO Public methods

    def load(self, filenames: str | list[str]) -> None:
        """
        Load SisypheROI elements in the current SisypheROICollection instance container from a list of PySisyphe ROI
        (.xroi) file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of PySisyphe ROI (.xroi) file names
        """
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        roi = SisypheROI()
                        roi.load(filename)
                        self._verifyID(roi)
                        if roi.getName() not in self:
                            self.append(roi)
                            if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromSisyphe(self, filenames: str | list[str]) -> None:
        """
        Load SisypheROI elements in the current SisypheROICollection instance container from a list of old Sisyphe ROI
        (.roi) file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of old Sisyphe ROI (.roi) file names
        """
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            from Sisyphe.core.sisypheConstants import getSisypheROIExt
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        path, ext = splitext(filename)
                        ext = ext.lower()
                        if ext == getSisypheROIExt()[0]:
                            imgs, hdr = readFromSisypheROI(filename)
                            # noinspection PyUnresolvedReferences
                            i: cython.int
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
                                    if QApplication.instance() is not None: QApplication.processEvents()
                        else: raise IOError('{} is not a Sisyphe ROI file extension.'.format(ext))
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromBrainVoyagerVOI(self, vmr: str, filenames: str | list[str]) -> None:
        """
        Load SisypheROI elements in the current SisypheROICollection instance container from a list of old Sisyphe ROI
        (.roi) file names.

        Parameters
        ----------
        vmr : str
            BrainVoyager reference volume (.vmr) file name
        filenames : str | list[str]
            list of BrainVoyager ROI (.voi) file names
        """
        if exists(vmr):
            from Sisyphe.core.sisypheConstants import getBrainVoyagerVMRExt
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
            from Sisyphe.core.sisypheConstants import getBrainVoyagerVOIExt
            self.clear()
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        path, ext = splitext(filename)
                        ext = ext.lower()
                        if ext == getBrainVoyagerVOIExt()[0]:
                            voi = read_voi(filename)
                            n = voi[0]['NrOfVOIs']
                            # noinspection PyUnresolvedReferences
                            i: cython.int
                            for i in range(n):
                                voi = voi[1][i]
                                r = voi['Coordinates'][:, 0]
                                c = voi['Coordinates'][:, 1]
                                buff[r, c] = 1
                                img = sitkGetImageFromArray(buff.T)
                                img.SetSpacing((vx, vy, vz))
                                roi = SisypheROI()
                                roi.setSITKImage(img)
                                roi.setColor(rgb=voi['ColorOfVOI'])
                                roi.setName(voi['NameOfVOI'])
                                roi.setOrigin()
                                roi.setDirections(getRegularDirections())
                                if roi.getName() not in self:
                                    self.append(roi)
                                    if QApplication.instance() is not None: QApplication.processEvents()
                        else: raise IOError('{} is not a BrainVoyager VOI file extension.'.format(ext))
                    else: raise IOError('no such file {}.'.format(vmr))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def save(self) -> None:
        """
        Iteratively save SisypheROI elements in the current SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for roi in self:
                if roi.hasFilename(): roi.save()


class SisypheROIDraw(object):
    """
    Description
    ~~~~~~~~~~~

    Processing class for SisypheROI instances with undo/redo management. Set input ROI with setROI method. Set input
    reference valume with SetVolume method.

    Scope of methods:

        - drawing,
        - flip/shift,
        - copy/cut/paste (global or blob),
        - blob selection,
        - morphology operators (global or blob),
        - fill holes,
        - thresholding (global or blob),
        - region growing (global or blob),
        - active contour,
        - slice interpolation,
        - shape statistics,
        - descriptive statistics.

    Most of these methods are available in 2D (slice) and 3D.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheROIDraw

    Creation: 08/09/2022
    Last revision: 24/03/2025
    """

    __slots__ = {'_volume', '_gradient', '_mask', '_brush', '_vbrush', '_roi', '_undo', '_undolifo', '_redolifo',
                 '_radius', '_morphradius', '_thickness', '_brushtype', '_struct', '_thresholdmin', '_thresholdmax',
                 '_ccsigma', '_cciter', '_acradius', '_acrms', '_acsigma', '_accurv', '_acadvec', '_acpropag',
                 '_aciter', '_acalgo', '_acthresholds', '_acfactor', '_clipboard'}

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

    """
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
    _radius         int, brush radius (pixel unit)
    _brushtype      int, brush shape
    _morphradius    int, structuring element radius (pixel unit)
    _struct         int, structuring element shape (ball, box, cross, annulus)
    _thickness      float, default expand/shrink thickness (mm)
    _thresholdmin   float
    _thresholdmax   float
    _ccsigma        float, cluster confidence sigma
    _cciter         int, cluster confidence iterations
    _acradius       float, active contour seed radius in mm (default 2.0)
    _acrms          float, active contour convergnece threshold (default 0.01)
    _acsigma        float, active contour gaussian kernel sigma for gradient magnitude processing (default 1.0)
    _accurv         float, active contour curvature weight (default 1.0)
    _acadvec        float, active contour advection weight (default 1.0)
    _acpropag       float, active contour propagation weight (default 1.0)
    _aciter         int, active contour number of iterations (default 1000)
    _acalgo         str, active contour algorithm ('geodesic', 'shape', 'threshold')
    _acfactor       float, factor used to process thresholds in seed region (mean +/- factor * sigma)
    _acthresholds   tuple[float, float] | None, active contour thresholds inf. and sup.
    _clipboard      sitkImage
    """

    def __init__(self) -> None:
        """
        SisypheROIDraw instance constructor.
        """
        self._volume = None
        self._mask = None
        self._brush = None
        self._vbrush = None
        self._roi = None
        self._undo = False
        self._undolifo = deque(maxlen=self._MAXUNDO)
        self._redolifo = deque(maxlen=self._MAXUNDO)
        # noinspection PyUnresolvedReferences
        self._radius: cython.int = self._DEFAULTRADIUS
        # noinspection PyUnresolvedReferences
        self._brushtype: cython.int = self._BRUSHTYPECODE['solid']
        # noinspection PyUnresolvedReferences
        self._morphradius: cython.int = self._DEFAULTMORPHRADIUS
        # noinspection PyUnresolvedReferences
        self._thickness: cython.double = 0.0
        self._struct = sitkBall
        # noinspection PyUnresolvedReferences
        self._thresholdmin: cython.double = 0.0
        # noinspection PyUnresolvedReferences
        self._thresholdmax: cython.double = 0.0
        # noinspection PyUnresolvedReferences
        self._ccsigma: cython.double = 2.0
        # noinspection PyUnresolvedReferences
        self._cciter: cython.int = 4
        # noinspection PyUnresolvedReferences
        self._acradius: cython.double = 2.0
        # noinspection PyUnresolvedReferences
        self._acrms: cython.double = 0.01
        # noinspection PyUnresolvedReferences
        self._acsigma: cython.double = 1.0
        # noinspection PyUnresolvedReferences
        self._accurv: cython.double = 1.0
        # noinspection PyUnresolvedReferences
        self._acadvec: cython.double = 1.0
        # noinspection PyUnresolvedReferences
        self._acpropag: cython.double = 1.0
        # noinspection PyUnresolvedReferences
        self._aciter: cython.int = 1000
        self._acalgo: str = 'geodesic'
        # noinspection PyUnresolvedReferences
        self._acfactor: cython.double = 2.0
        self._acthresholds: tuple[float, float] | None = None
        self._clipboard = None
        self._calcBrush()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheROIDraw instance to str
        """
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
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheROIDraw instance representation
        """
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
            # noinspection PyUnresolvedReferences
            s: cython.int = self._radius * 2 - 1
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

    # Private methods to update and extract slices from volume

    def _updateRoiFromSITKImage(self, img: sitkImage, replace: bool = True) -> None:
        npimg = sitkGetArrayViewFromImage(img)
        self._updateRoiFromNumpy(npimg, replace)

    def _updateSliceFromSITKImage(self, img: sitkImage, sindex: int, dim: int, replace: bool = True) -> None:
        npimg = sitkGetArrayViewFromImage(img)
        self._updateSliceFromNumpy(npimg, sindex, dim, replace)

    def _updateRoiFromNumpy(self, img: ndarray, replace: bool = True) -> None:
        if not replace: img = self._roi.getNumpy() | img
        self._roi.getNumpy()[:] = img[:]

    def _updateSliceFromNumpy(self, img: ndarray, sindex: int, dim: int, replace: bool = True):
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

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the reference SisypheVolume image attribute to the current SisypheROIDraw instance. Same space as
        SisypheROI attribute (same size and spacing). Many methods require a reference SisypheVolume (including
        segmentation methods).

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self.setFullRangeThreshold()
            if self.hasROI():
                if self._roi.getReferenceID() != self._volume.getID(): self._roi = None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        """
        Get the reference SisypheVolume image attribute from the current SisypheROIDraw instance. Same space as
        SisypheROI attribute (same size and spacing). Many methods require a reference SisypheVolume (including
        segmentation methods).

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        return self._volume

    def hasVolume(self) -> bool:
        """
        Check whether the reference SisypheVolume attribute of the current SisypheROIDraw instance is defined
        (not None).

        Returns
        -------
        bool
            True if reference SisypheVolume attribute is defined
        """
        return self._volume is not None

    def setROI(self, roi: SisypheROI) -> None:
        """
        Set the SisypheROI image attribute to the current SisypheROIDraw instance. This is the ROI image processed in
        the current SisypheROIDraw instance. Same space as reference SisypheVolume attribute (same size and spacing).

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            roi to be processed
        """
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
        """
        Get the SisypheROI image attribute from the current SisypheROIDraw instance. This is the ROI image processed in
        the current SisypheROIDraw instance. Same space as reference SisypheVolume attribute (same size and spacing).

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            roi to be processed
        """
        return self._roi

    def hasROI(self) -> bool:
        """
        Check whether the SisypheROI attribute of the current SisypheROIDraw instance is defined (not None). This is
        the ROI image processed in the current SisypheROIDraw instance.

        Returns
        -------
        bool
            True if SisypheROI attribute is defined
        """
        return self._roi is not None

    def removeROI(self) -> None:
        """
        Remove the SisypheROI attribute to the current SisypheROIDraw instance.
        """
        self._roi = None
        self.clearLIFO()

    def getBrushType(self) -> str:
        """
        Get the brush type, as str name, used to hand-draw in the SisypheROI image.

        Brush types:

            - 'solid' disc-shaped 2D brush
            - 'threshold' voxels of the disc-shaped 2D brush surface with a scalar value over a threshold in the SisypheVolume reference
            - 'solid3' sphere-shaped 3D brush
            - 'threshold3' voxels in sphere-shaped 3D brush volume with a scalar value over a threshold in the SisypheVolume reference

        Returns
        -------
        str
            brush type
        """
        return self._BRUSHTYPENAME[self._brushtype]

    def setBrushType(self, brushtype: int | str) -> None:
        """
        Set the brush type, as str name or int code, used to hand-draw in the SisypheROI image.

        Parameters
        ----------
        brushtype   int | str
            name or int code

                - 0 or 'solid' disc-shaped 2D brush
                - 1 or 'threshold' thresholded voxels of the disc-shaped 2D brush surface
                - 2 or 'solid3' sphere-shaped 3D brush
                - 3 or 'threshold3' thresholded voxels in sphere-shaped 3D brush volume
        """
        # brush type = 'solid', 'threshold', 'solid3', 'threshold3'
        if isinstance(brushtype, str):
            if brushtype in self._BRUSHTYPECODE: self._brushtype = self._BRUSHTYPECODE[brushtype]
            else: self._brushtype = self._BRUSHTYPECODE['solid']
        elif isinstance(brushtype, int):
            if 0 <= brushtype < 3: self._brushtype = brushtype
            else: self._brushtype = self._BRUSHTYPECODE['solid']

    def setBrushRadius(self, radius: int) -> None:
        """
        Set the radius (in voxels) of the brush used to hand-draw in the SisypheROI image.

        Parameters
        ----------
        radius : int
            brush radius in voxels
        """
        if isinstance(radius, int):
            self._radius = radius
            if self._radius < 0: self._radius = 0
            if self._radius > self._MAXRADIUS: self._radius = self._MAXRADIUS
            self._calcBrush()
        else: raise TypeError('parameter type {} is not int.'.format(type(radius)))

    def getBrushRadius(self) -> int:
        """
        Get the radius (in voxels) of the brush used to hand-draw in the SisypheROI image.

        Returns
        -------
        int
            brush radius in voxels
        """
        return self._radius

    def setStructElement(self, struct: str) -> None:
        """
        Set the structuring element shape, as str name, used in morphological methods (erosion, dilatation, opening,
        closing).

        Parameters
        ----------
        struct : str
            structuring element: 'ball', 'box', 'cross' or 'annulus'
        """
        if isinstance(struct, str):
            if struct in ('ball', 'box', 'cross', 'annulus'):
                if struct == 'ball': self._struct = sitkBall
                elif struct == 'box': self._struct = sitkBox
                elif struct == 'cross': self._struct = sitkCross
                else: self._struct = sitkAnnulus
            else: raise ValueError('parameter value {} is not valid.'.format(struct))
        else: raise TypeError('parameter type {} is not str.'.format(type(struct)))

    def getStructElement(self) -> str:
        """
        Get the structuring element shape, as str name, used in morphological methods (erosion, dilatation, opening,
        closing).

        Returns
        -------
        str
            structuring element: 'ball', 'box', 'cross' or 'annulus'
        """
        if self._struct == sitkBall: return 'ball'
        elif self._struct == sitkBox: return 'box'
        elif self._struct == sitkCross: return 'cross'
        else: return 'annulus'

    def setMorphologyRadius(self, radius: float) -> None:
        """
        Set the radius (in voxels) of the structuring element used in morphological methods (erosion, dilatation,
        opening, closing).

        Parameters
        ----------
        radius : int
            structuring element radius in voxels
        """
        if isinstance(radius, (int, float)):
            if radius <= 0.0: radius = 1.0
            if radius > 20.0: radius = 20.0
            self._morphradius = radius
        else: raise TypeError('parameter type {} is not int or float.'.format(type(radius)))

    def getMorphologyRadius(self) -> float:
        """
        Get the radius (in voxels) of the structuring element used in morphological methods (erosion, dilatation,
        opening, closing).

        Returns
        -------
        int
            structuring element radius in voxels
        """
        return self._morphradius

    def getThickness(self) -> float:
        """
        Get the margin (in mm) used in euclidean expanding/shrinking methods (euclideanDilate,
        euclideanErode, 2D and 3D, whole and blob versions).

        Returns
        -------
        float
            margin in mm
        """
        return self._thickness

    def setThickness(self, mm: float) -> None:
        """
        Set the margin (in mm) used in euclidean expanding/shrinking methods (euclideanDilate,
        euclideanErode, 2D and 3D, whole and blob versions).

        Parameters
        ----------
        mm : float
            margin in mm
        """
        if isinstance(mm, float):
            if 0.0 < mm <= 50.0: self._thickness = mm
            else: raise ValueError('parameter value {} is out of range (0.0 to 50.0 mm).'.format(mm))
        else: raise TypeError('parameter type {} is not float.'.format(mm))

    def getThresholdMin(self) -> float:
        """
        Get the minimum value threshold used in some methods.

        Returns
        -------
        float
            minimum value threshold
        """
        return self._thresholdmin

    def getThresholdMax(self) -> float:
        """
        Get the maximum value threshold used in some methods.

        Returns
        -------
        float
            maximum value threshold
        """
        return self._thresholdmax

    def getThresholds(self) -> tuple[float, float]:
        """
        Get the minimum and maximum value thresholds used in some methods.

        Returns
        -------
        tuple[float, float]
            minimum and maximum value thresholds
        """
        return self._thresholdmin, self._thresholdmax

    def setThresholdMin(self, vmin: float) -> None:
        """
        Set the minimum value threshold used in some methods.

        Parameters
        ----------
        vmin : float
            minimum value threshold
        """
        if isinstance(vmin, (int, float)):
            self._thresholdmin = vmin
            if self._thresholdmin > self._thresholdmax:
                self._thresholdmax = self._thresholdmin
            self._calcMask()
        else: raise TypeError('parameter type {} is not int or float.'.format(type(vmin)))

    def setThresholdMax(self, vmax: float) -> None:
        """
        Set the maximum value threshold used in some methods.

        Parameters
        ----------
        vmax : float
            maximum value threshold
        """
        if isinstance(vmax, (int, float)):
            self._thresholdmax = vmax
            if self._thresholdmax < self._thresholdmin:
                self._thresholdmin = self._thresholdmax
            self._calcMask()
        else: raise TypeError('parameter type {} is not int or float.'.format(type(vmax)))

    def setThresholds(self, vmin: float, vmax: float) -> None:
        """
        Set the minimum and maximum value thresholds used in some methods.

        Parameters
        ----------
        vmin : float
            minimum value threshold
        vmax : float
            maximum value threshold
        """
        if isinstance(vmax, (int, float)) and isinstance(vmin, (int, float)):
            if vmin > vmax: vmin, vmax = vmax, vmin
            self._thresholdmin = vmin
            self._thresholdmax = vmax
            self._calcMask()

    def hasThresholds(self) -> bool:
        """
        Check whether threshold attributes of the current SisypheROIDraw instance are defined.

        Returns
        -------
        bool
            True if thresholds are defined
        """
        return self._thresholdmax > 0

    def setFullRangeThreshold(self) -> None:
        """
        Set the minimum and maximum value thresholds to the minimum and maximum scalar values in the reference
        SisypheVolume instance. These thresholds are used in some processing methods.
        """
        self._thresholdmin = self._volume.getDisplay().getRangeMin()
        self._thresholdmax = self._volume.getDisplay().getRangeMax()

    def setOtsuThreshold(self, background: bool = False) -> None:
        """
        Set minimum and maximum value thresholds using Otsu algorithm. These thresholds are used in some processing
        methods.

        Parameters
        ----------
        background : bool
            - True:
                - minimum threshold = minimum scalar value in the reference SisypheVolume instance
                - maximum threshold processed by Otsu algorithm
            - False:
                - minimum threshold processed by Otsu algorithm
                - maximum threshold = maximum scalar value in the reference SisypheVolume instance
        """
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

    def setHuangThreshold(self, background: bool = False) -> None:
        """
        Set minimum and maximum value thresholds using Huang algorithm. These thresholds are used in some processing
        methods.

        Parameters
        ----------
        background : bool
            - True:
                - minimum threshold = minimum scalar value in the reference SisypheVolume instance
                - maximum threshold processed by Huang algorithm
            - False:
                - minimum threshold processed by Huang algorithm
                - maximum threshold = maximum scalar value in the reference SisypheVolume instance
        """
        simg = self._volume.getSITKImage()
        otsu = sitkHuangThresholdImageFilter()
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
        """
        Set minimum and maximum value thresholds using Mean algorithm. These thresholds are used in some processing
        methods.

        Parameters
        ----------
        background : bool
            - True:
                - minimum threshold = minimum scalar value in the reference SisypheVolume instance
                - maximum threshold processed by Mean algorithm
            - False:
                - minimum threshold processed by Mean algorithm
                - maximum threshold = maximum scalar value in the reference SisypheVolume instance
        """
        mean = int(self._volume.getNumpy().mean())
        if background:
            self._thresholdmin = self._volume.getDisplay().getRangeMin()
            self._thresholdmax = mean
        else:
            self._thresholdmin = mean
            self._thresholdmax = self._volume.getDisplay().getRangeMax()
        self._calcMask()

    def getConfidenceConnectedSigma(self) -> float:
        """
        Get the confidence connected sigma attribute of the current SisypheDraw instance.

        Returns
        -------
        float
            confidence connected sigma attribute
        """
        return self._ccsigma

    def getConfidenceConnectedIter(self) -> int:
        """
        Get the confidence connected number of iterations attribute of the current SisypheDraw instance.

        Returns
        -------
        int
            confidence connected number of iterations attribute
        """
        return self._cciter

    def getActiveContourSeedRadius(self) -> float:
        """
        Get the active contour seed radius attribute of the current SisypheDraw instance. This attribute is useb by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        Returns
        -------
        float
            active contour seed radius attribute, seed sphere radius in mm
        """
        return self._acradius

    def getActiveContourCurvatureWeight(self) -> float:
        """
        Get the active contour curvature weight attribute of the current SisypheDraw instance. This attribute is useb
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        The curvature attribute (default 1.0) controls the magnitude of the curvature values which are calculated on
        the evolving  isophote. This is important in controlling the relative effect of curvature in the calculation.
        Default value is 1.0. Higher values relative to the other level set equation terms (propagation and advection)
        will give a smoother result.

        Returns
        -------
        float
            active contour curvature weight attribute
        """
        return self._accurv

    def getActiveContourAdvectionWeight(self) -> float:
        """
        Get the active contour advection weight attribute of the current SisypheDraw instance. This attribute is useb
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        The advection attribute (default 1.0) controls the scaling of the vector advection field term relative to other
        terms in the level set equation.

        Returns
        -------
        float
            active contour advection weight attribute
        """
        return self._acadvec

    def getActiveContourPropagationWeight(self) -> float:
        """
        Get the active contour propagation weight attribute of the current SisypheDraw instance. This attribute is useb
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        The propagation speed attribute (default 1.0) controls the scaling of the scalar propagation (speed) term
        relative to other terms in the level set equation. > 0 propagation outwards, < 0 propagating inwards.

        Returns
        -------
        float
            active contour propagation weight attribute
        """
        return self._acpropag

    def getActiveContourNumberOfIterations(self) -> int:
        """
        Get the active contour number of iterations attribute of the current SisypheDraw instance. This attribute is
        useb by the activeContourSegmentation() method. Active contour is an iterative level set method of
        segmentation, starting from a seed sphere.

        Returns
        -------
        int
            active contour number of iterations attribute
        """
        return self._aciter

    def getActiveContourConvergence(self) -> float:
        """
        Get the active contour convergence attribute of the current SisypheDraw instance. This attribute is useb by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The rms convergence attribute (0.0 < rms < 1.0, default 0.01) is used to determine when the solution has
        converged. A lower value will result in a tighter-fitting solution, but will require more computations. Too low
        a value could put the solver into an infinite loop unless a reasonable number of iterations parameter is set.

        Returns
        -------
        float
            active contour convergence attribute
        """
        return self._acrms

    def getActiveContourAlgorithm(self) -> str:
        """
        Get the active contour algorithm attribute of the current SisypheDraw instance. This attribute is useb by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        Returns
        -------
        str
            active contour algorithm attribute ('geodesic', 'shape' or 'threshold')
        """
        return self._acalgo

    def getActiveContourSigma(self) -> float:
        """
        Get the active contour sigma attribute of the current SisypheDraw instance. This attribute is useb by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The sigma attribute is a gaussian kernel parameter used to compute the magnitude of the gradient. The edge
        potential map of the level set algorithm is computed from the image gradient. Edge potential map is that it has
        values close to zero in regions near the edges and values close to one inside the shape itself. This map is the
        image from which the speed function will be calculated.

        Returns
        -------
        float
            active contour sigma attribute
        """
        return self._acsigma

    def getActiveContourFactor(self) -> float:
        """
        Get the active contour factorfactor attribute of the current SisypheDraw instance. This attribute is useb by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The factor attribute is only used by the threshold version of the active contour algorithms, if threshold
        attributes are not defined. The formula factor x standard deviation of the signal within the seed sphere is
        used to estimate the lower and upper threshold parameters (default 3.0).

        Returns
        -------
        float
            active contour factor attribute
        """
        return self._acfactor

    def getActiveContourThresholds(self) -> tuple[float, float] | None:
        """
        Get the active contour curvature weight attribute of the current SisypheDraw instance. These attributes are
        useb by the activeContourSegmentation() method. Active contour is an iterative level set method of
        segmentation, starting from a seed sphere.

        Lower and upper threshold attributes are only used by the threshold version of the active contour algorithms.

        Returns
        -------
        tuple[float, float]
            active contour threshold attributes
        """
        return self._acthresholds

    def setConfidenceConnectedSigma(self, sigma: float = 2.0) -> None:
        """
        Set the confidence connected sigma attribute of the current SisypheDraw instance.

        Parameters
        ----------
        sigma : float
            confidence connected sigma attribute
        """
        self._ccsigma = sigma

    def setConfidenceConnectedIter(self, iters: int = 4) -> None:
        """
        Set the confidence connected number of iterations attribute of the current SisypheDraw instance.

        Parameters
        ----------
        iters : int
            confidence connected number of iterations attribute
        """
        self._cciter = iters

    def setActiveContourSeedRadius(self, radius: float = 2.0) -> None:
        """
        Set the active contour seed radius attribute of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        Parameters
        ----------
        radius : float
            active contour seed radius attribute, seed sphere radius in mm
        """
        self._acradius = radius

    def setActiveContourCurvatureWeight(self, weight: float = 1.0) -> None:
        """
        Set the active contour curvature weight attribute of the current SisypheDraw instance. This attribute is used
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        The curvature attribute (default 1.0) controls the magnitude of the curvature values which are calculated on
        the evolving  isophote. This is important in controlling the relative effect of curvature in the calculation.
        Default value is 1.0. Higher values relative to the other level set equation terms (propagation and advection)
        will give a smoother result.

        Parameters
        ----------
        weight : float
            active contour curvature weight attribute
        """
        self._accurv = weight

    def setActiveContourAdvectionWeight(self, weight: float = 1.0) -> None:
        """
        Set the active contour advection weight attribute of the current SisypheDraw instance. This attribute is used
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        Advection attribute (default 1.0) controls the scaling of the vector advection field term relative to other
        terms in the level set equation.

        Parameters
        ----------
        weight : float
            active contour advection weight attribute
        """
        self._acadvec = weight

    def setActiveContourPropagationWeight(self, weight: float = 1.0) -> None:
        """
        Set the active contour propagation weight attribute of the current SisypheDraw instance. This attribute is used
        by the activeContourSegmentation() method. Active contour is an iterative level set method of segmentation,
        starting from a seed sphere.

        The propagation speed attribute (default 1.0) controls the scaling of the scalar propagation (speed) term
        relative to other terms in the level set equation. > 0 propagation outwards, < 0 propagating inwards.

        Parameters
        ----------
        weight : float
            active contour propagation weight attribute
        """
        self._acpropag = weight

    def setActiveContourNumberOfIterations(self, niter: int = 1000) -> None:
        """
        Set the active contour number of iterations attribute of the current SisypheDraw instance. This attribute is
        used by the activeContourSegmentation() method. Active contour is an iterative level set method of
        segmentation, starting from a seed sphere.

        Parameters
        ----------
        niter : int
            active contour number of iterations attribute
        """
        self._aciter = niter

    def setActiveContourConvergence(self, rms: float = 0.01) -> None:
        """
        Set the active contour convergence attribute of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The rms convergence attribute (0.0 < rms < 1.0, default 0.01) is used to determine when the solution has
        converged. A lower value will result in a tighter-fitting solution, but will require more computations. Too low
        a value could put the solver into an infinite loop unless a reasonable number of iterations parameter is set.

        Parameters
        ----------
        rms : float
            active contour convergence attribute
        """
        self._acrms = rms

    def setActiveContourAlgorithm(self, algo: str = 'geodesic') -> None:
        """
        Set the active contour algorithm attribute of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        Parameters
        ----------
        algo : str
            active contour algorithm attribute ('geodesic', 'shape' or 'threshold')
        """
        if algo in ('geodesic', 'shape', 'threshold'): self._acalgo = algo
        else: raise ValueError('{} invalid algorithm.'.format(algo))

    def setActiveContourSigma(self, sigma: float = 1.0) -> None:
        """
        Set the active contour sigma attribute of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The sigma attribute is a gaussian kernel parameter used to compute the magnitude of the gradient. The edge
        potential map of the level set algorithm is computed from the image gradient. Edge potential map is that it has
        values close to zero in regions near the edges and values close to one inside the shape itself. This map is the
        image from which the speed function will be calculated.

        Parameters
        ----------
        sigma : float
            active contour sigma attribute
        """
        self._acsigma =  sigma

    def setActiveContourFactor(self, factor: float = 2.0) -> None:
        """
        Set the active contour factor attribute of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        The factor attribute is only used by the threshold version of the active contour algorithms, if threshold
        attributes are not defined. The formula mean +/- factor x standard deviation of the signal within the seed
        sphere is used to estimate the lower and upper threshold parameters (default 3.0).

        Parameters
        ----------
        factor : float
            active contour factor attribute
        """
        self._acfactor =  factor

    def setActiveContourThresholds(self, thresholds: tuple[float, float] | None) -> None:
        """
        Set the active contour threshold attributes of the current SisypheDraw instance. This attribute is used by the
        activeContourSegmentation() method. Active contour is an iterative level set method of segmentation, starting
        from a seed sphere.

        Lower and upper threshold attributes are only used by the threshold version of the active contour algorithms.

        Parameters
        ----------
        thresholds : tuple[float, float]
            Lower and upper thresholds
        """
        self._acthresholds = thresholds

    def clearClipboard(self) -> None:
        """
        Clear the clipboard attribute of the current SisypheROIDraw instance. The clipboard attribute is used as
        temporary buffer by copy/cut/paste methods.
        """
        if self._clipboard is not None:
            del self._clipboard
            self._clipboard = None

    # Undo/redo

    def setUndoOn(self) -> None:
        """
        Enables undo/redo abilities of the current SisypheROIDraw instance. All ROI processing is stored in a LIFO
        stack if this option is enabled.
        """
        self.setUndo(True)

    def setUndoOff(self) -> None:
        """
        Disables undo/redo abilities of the current SisypheROIDraw instance. All ROI processing is stored in a LIFO
        stack if this option is enabled.
        """
        self.setUndo(False)

    def setUndo(self, v: bool) -> None:
        """
        Enables/disables undo/redo abilities of the current SisypheROIDraw instance. All ROI processing is stored in a
        LIFO stack if this option is enabled.

        Parameters
        ----------
        v : boolean
            undo enabled if True
        """
        if isinstance(v, bool):
            self._undo = v
            self.clearLIFO()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getUndo(self) -> bool:
        """
        Check whether undo/redo abilities of the current SisypheROIDraw instance are enabled. All ROI processing is
        stored in a LIFO stack if this option is enabled.

        Returns
        -------
        boolean
            undo enabled if True
        """
        return self._undo

    def appendZSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        """
        Add an axial slice of the SisypheROI attribute in the LIFO undo/redo stack. This method is called by 2D
        processing methods if undo/redo abilities are enabled.

        Parameters
        ----------
        i : int
            z-axis index of the slice
        pile : int
            0 addBundle to LIFO undo stack, 1 addBundle to LIFO redo stack
        """
        if 0 <= i < self._roi.getSize()[2]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[i, :, :].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSZ, i, buff))
            else: self._redolifo.append((self._DSZ, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendYSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        """
        Add a coronal slice of the SisypheROI attribute in the LIFO undo/redo stack. This method is called by 2D
        processing methods if undo/redo abilities are enabled.

        Parameters
        ----------
        i : int
            y-axis index of the slice
        pile : int
            0 addBundle to LIFO undo stack, 1 addBundle to LIFO redo stack
        """
        if 0 <= i < self._roi.getSize()[1]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[:, i, :].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSY, i, buff))
            else: self._redolifo.append((self._DSY, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendXSliceToLIFO(self, i: int, pile: int = _UNDO) -> None:
        """
        Add a sagittal slice of the SisypheROI attribute in the LIFO undo/redo stack. This method is called by 2D
        processing methods if undo/redo abilities are enabled.

        Parameters
        ----------
        i : int
            x-axis index of the slice
        pile : int
            0 addBundle to LIFO undo stack, 1 addBundle to LIFO redo stack
        """
        if 0 <= i < self._roi.getSize()[0]:
            buff = sparse.csr_matrix(self._roi.getNumpy()[:, :, i].copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DSX, i, buff))
            else: self._redolifo.append((self._DSY, i, buff))
        else: raise IndexError('parameter index {} is out of range.'.format(i))

    def appendSliceToLIFO(self, i: int, dim: int, pile: int = _UNDO) -> None:
        """
        Add a slice of the SisypheROI attribute in the LIFO undo/redo stack. This method is called by 2D processing
        methods if undo/redo abilities are enabled.

        Parameters
        ----------
        i : int
            index of the slice
        dim : int
            slice axis code, 0 z-axis, 1 y-axis, 2 x-axis
        pile : int
            0 addBundle to LIFO undo stack, 1 addBundle to LIFO redo stack
        """
        if self._undo:
            if dim == 0: self.appendZSliceToLIFO(i, pile)
            elif dim == 1: self.appendYSliceToLIFO(i, pile)
            else: self.appendXSliceToLIFO(i, pile)

    def appendVolumeToLIFO(self, pile: int = _UNDO) -> None:
        """
        Add the whole volume of the SisypheROI attribute in the LIFO undo/redo stack. This method is called by 3D
        processing methods if undo/redo abilities are enabled.

        Parameters
        ----------
        pile : int
            0 addBundle to LIFO undo stack, 1 addBundle to LIFO redo stack
        """
        if self._undo and self.hasROI():
            buff = sparse.csr_matrix(self._roi.getNumpy().copy().flatten())
            if pile == self._UNDO: self._undolifo.append((self._DV, None, buff))
            else: self._redolifo.append((self._DV, None, buff))

    def popUndoLIFO(self) -> None:
        """
        Copy the last element (slice or whole ROI) of the LIFO undo stack to the SisypheROI attribute. Undo the last
        processing of the SisypheROI attribute.
        """
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
        """
        Copy the last element (slice or whole ROI) of the LIFO redo stack to the SisypheROI attribute. Redo the last
        processing of the SisypheROI attribute.
        """
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
        """
        Clear the LIFO undo/redo stacks.
        """
        self._undolifo.clear()
        self.appendVolumeToLIFO()
        self._redolifo.clear()

    # Brush

    def brush(self, x: int, y: int, z: int, dim: int) -> None:
        """
        Draw a brush-shape at the x, y, z coordinates of the SisypheROI image attribute. Brush-shape is defined with
        setBrushType() method, and size with setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        dim : int
            slice orientation code
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            if self._brushtype == self._BRUSHTYPECODE['solid']: self.solidBrush(x, y, z, 1, dim)
            elif self._brushtype == self._BRUSHTYPECODE['threshold']: self.thresholdBrush(x, y, z, dim)
            elif self._brushtype == self._BRUSHTYPECODE['solid3']: self.solid3DBrush(x, y, z)
            else: self.threshold3DBrush(x, y, z)

    def erase(self, x: int, y: int, z: int, dim: int) -> None:
        """
        Erase a brush-shape at the x, y, z coordinates of the SisypheROI image attribute. Brush-shape is defined with
        setBrushType() method, and size with setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        dim : int
            slice orientation code
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            if self._brushtype < self._BRUSHTYPECODE['solid3']: self.solidBrush(x, y, z, 0, dim)
            else: self.solid3DBrush(x, y, z, 0)

    def solidBrush(self, x: int, y: int, z: int, c: int, dim: int) -> None:
        """
        Draw a disk at the x, y, z coordinates of the SisypheROI image attribute. Disk radius is defined with
        setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        c : int
            0 (erase) or 1 (draw)
        dim : int
            slice orientation code
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self._radius in (0, 1):
            self._roi.getSITKImage()[x, y, z] = c
        else:
            xmax, ymax, zmax = self._roi.getSize()
            if dim == 0:
                if 0 <= x < xmax and 0 <= y < ymax:
                    # noinspection PyUnresolvedReferences
                    idx1: cython.int = self._radius - 1 - x
                    # noinspection PyUnresolvedReferences
                    idy1: cython.int = self._radius - 1 - y
                    # noinspection PyUnresolvedReferences
                    idx2: cython.int = xmax - x - self._radius
                    # noinspection PyUnresolvedReferences
                    idy2: cython.int = ymax - y - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    brush = self._brush[idy1:idy2, idx1:idx2]
                    dy, dx = brush.shape
                    # noinspection PyUnresolvedReferences
                    x2: cython.int = x + dx
                    # noinspection PyUnresolvedReferences
                    y2: cython.int = y + dy
                    back = self._roi.getNumpy()[z, y:y2, x:x2]
                    if c == 1: self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_and(back, invert(brush))
            elif dim == 1:
                if 0 <= x < xmax and 0 <= z < zmax:
                    # noinspection PyUnresolvedReferences
                    idx1: cython.int = self._radius - 1 - x
                    # noinspection PyUnresolvedReferences
                    idz1: cython.int = self._radius - 1 - z
                    # noinspection PyUnresolvedReferences
                    idx2: cython.int = xmax - x - self._radius
                    # noinspection PyUnresolvedReferences
                    idz2: cython.int = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idx1:idx2]
                    dz, dx = brush.shape
                    # noinspection PyUnresolvedReferences
                    x2: cython.int = x + dx
                    # noinspection PyUnresolvedReferences
                    z2: cython.int = z + dz
                    back = self._roi.getNumpy()[z:z2, y, x:x2]
                    if c == 1: self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_and(back, invert(brush))
            else:
                if 0 <= y < ymax and 0 <= z < zmax:
                    # noinspection PyUnresolvedReferences
                    idy1: cython.int = self._radius - 1 - y
                    # noinspection PyUnresolvedReferences
                    idz1: cython.int = self._radius - 1 - z
                    # noinspection PyUnresolvedReferences
                    idy2: cython.int = ymax - y - self._radius
                    # noinspection PyUnresolvedReferences
                    idz2: cython.int = zmax - z - self._radius
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idy1:idy2]
                    dz, dy = brush.shape
                    # noinspection PyUnresolvedReferences
                    y2: cython.int = y + dy
                    # noinspection PyUnresolvedReferences
                    z2: cython.int = z + dz
                    back = self._roi.getNumpy()[z:z2, y:y2, x]
                    if c == 1: self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_or(back, brush)
                    else: self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_and(back, invert(brush))

    def thresholdBrush(self, x: int, y: int, z: int, dim: int) -> None:
        """
        Draw a disk at the x, y, z coordinates of the SisypheROI image attribute. In this thresholded version, only
        voxels with scalar values above a threshold in the SisypheVolume reference are added. Disk radius is defined
        with setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        dim : int
            slice orientation code
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if not self.hasThresholds(): self.solidBrush(x, y, z, 1, dim)
        else:
            if self._radius in (0, 1):
                if self._thresholdmin <= self._volume.getSITKImage()[x, y, z] <= self._thresholdmax:
                    self._roi.getSITKImage()[x, y, z] = 1
            else:
                xmax, ymax, zmax = self._roi.getSize()
                if dim == 0:
                    # noinspection PyUnresolvedReferences
                    idx1: cython.int = self._radius - 1 - x
                    # noinspection PyUnresolvedReferences
                    idy1: cython.int = self._radius - 1 - y
                    # noinspection PyUnresolvedReferences
                    idx2: cython.int = xmax - x - self._radius
                    # noinspection PyUnresolvedReferences
                    idy2: cython.int = ymax - y - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    brush = self._brush[idy1:idy2, idx1:idx2]
                    dy, dx = brush.shape
                    # noinspection PyUnresolvedReferences
                    x2: cython.int = x + dx
                    # noinspection PyUnresolvedReferences
                    y2: cython.int = y + dy
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z, y:y2, x:x2], brush)
                    back = self._roi.getNumpy()[z, y:y2, x:x2]
                    self._roi.getNumpy()[z, y:y2, x:x2] = bitwise_or(back, brush)
                elif dim == 1:
                    # noinspection PyUnresolvedReferences
                    idx1: cython.int = self._radius - 1 - x
                    # noinspection PyUnresolvedReferences
                    idz1: cython.int = self._radius - 1 - z
                    # noinspection PyUnresolvedReferences
                    idx2: cython.int = xmax - x - self._radius
                    # noinspection PyUnresolvedReferences
                    idz2: cython.int = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idx1:idx2]
                    dz, dx = brush.shape
                    # noinspection PyUnresolvedReferences
                    x2: cython.int = x + dx
                    # noinspection PyUnresolvedReferences
                    z2: cython.int = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y, x:x2], brush)
                    back = self._roi.getNumpy()[z:z2, y, x:x2]
                    self._roi.getNumpy()[z:z2, y, x:x2] = bitwise_or(back, brush)
                else:
                    # noinspection PyUnresolvedReferences
                    idy1: cython.int = self._radius - 1 - y
                    # noinspection PyUnresolvedReferences
                    idz1: cython.int = self._radius - 1 - z
                    # noinspection PyUnresolvedReferences
                    idy2: cython.int = ymax - y - self._radius
                    # noinspection PyUnresolvedReferences
                    idz2: cython.int = zmax - z - self._radius
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._brush[idz1:idz2, idy1:idy2]
                    dz, dy = brush.shape
                    # noinspection PyUnresolvedReferences
                    y2: cython.int = y + dy
                    # noinspection PyUnresolvedReferences
                    z2: cython.int = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y:y2, x], brush)
                    back = self._roi.getNumpy()[z:z2, y:y2, x]
                    self._roi.getNumpy()[z:z2, y:y2, x] = bitwise_or(back, brush)

    def solid3DBrush(self, x: int, y: int, z: int, c: int = 1) -> None:
        """
        Draw a sphere at the x, y, z coordinates of the SisypheROI image attribute. Disk radius is defined with
        setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        c : int
            0 (erase) or 1 (draw)
        """
        if self._radius in (0, 1):
            self._roi.getSITKImage()[x, y, z] = c
        else:
            xmax, ymax, zmax = self._roi.getSize()
            if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
                # noinspection PyUnresolvedReferences
                idx1: cython.int = self._radius - 1 - x
                # noinspection PyUnresolvedReferences
                idy1: cython.int = self._radius - 1 - y
                # noinspection PyUnresolvedReferences
                idz1: cython.int = self._radius - 1 - z
                # noinspection PyUnresolvedReferences
                idx2: cython.int = xmax - x - self._radius
                # noinspection PyUnresolvedReferences
                idy2: cython.int = ymax - y - self._radius
                # noinspection PyUnresolvedReferences
                idz2: cython.int = zmax - z - self._radius
                if idx1 < 0: x, idx1 = -idx1, 0
                else: x = 0
                if idy1 < 0: y, idy1 = -idy1, 0
                else: y = 0
                if idz1 < 0: z, idz1 = -idz1, 0
                else: z = 0
                # noinspection PyUnresolvedReferences
                m: cython.int = 2 * self._radius - 1
                if idx2 > -1: idx2 = m
                if idy2 > -1: idy2 = m
                if idz2 > -1: idz2 = m
                brush = self._vbrush[idz1:idz2, idy1:idy2, idx1:idx2]
                dz, dy, dx = brush.shape
                # noinspection PyUnresolvedReferences
                x2: cython.int = x + dx
                # noinspection PyUnresolvedReferences
                y2: cython.int = y + dy
                # noinspection PyUnresolvedReferences
                z2: cython.int = z + dz
                back = self._roi.getNumpy()[z:z2, y:y2, x:x2]
                if c == 1: self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_or(back, brush)
                else: self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_and(back, invert(brush))

    def threshold3DBrush(self, x: int, y: int, z: int) -> None:
        """
        Draw a sphere at the x, y, z coordinates of the SisypheROI image attribute. In this thresholded version, only
        voxels with scalar values above a threshold in the SisypheVolume reference are added. Disk radius is defined
        with setBrushRadius() method.

        Parameters
        ----------
        x : int
            x-axis coordinate
        y : int
            y-axis coordinate
        z : int
            z-axis coordinate
        """
        if not self.hasThresholds(): self.solid3DBrush(x, y, z, 1)
        else:
            if self._radius in (0, 1):
                if self._thresholdmin <= self._volume.getSITKImage()[x, y, z] <= self._thresholdmax:
                    self._roi.getSITKImage()[x, y, z] = 1
            else:
                xmax, ymax, zmax = self._roi.getSize()
                if 0 <= x < xmax and 0 <= y < ymax and 0 <= z < zmax:
                    # noinspection PyUnresolvedReferences
                    idx1: cython.int = self._radius - 1 - x
                    # noinspection PyUnresolvedReferences
                    idy1: cython.int = self._radius - 1 - y
                    # noinspection PyUnresolvedReferences
                    idz1: cython.int = self._radius - 1 - z
                    # noinspection PyUnresolvedReferences
                    idx2: cython.int = xmax - x - self._radius
                    # noinspection PyUnresolvedReferences
                    idy2: cython.int = ymax - y - self._radius
                    # noinspection PyUnresolvedReferences
                    idz2: cython.int = zmax - z - self._radius
                    if idx1 < 0: x, idx1 = -idx1, 0
                    else: x = 0
                    if idy1 < 0: y, idy1 = -idy1, 0
                    else: y = 0
                    if idz1 < 0: z, idz1 = -idz1, 0
                    else: z = 0
                    # noinspection PyUnresolvedReferences
                    m: cython.int = 2 * self._radius - 1
                    if idx2 > -1: idx2 = m
                    if idy2 > -1: idy2 = m
                    if idz2 > -1: idz2 = m
                    brush = self._vbrush[idz1:idz2, idy1:idy2, idx1:idx2]
                    dz, dy, dx = brush.shape
                    # noinspection PyUnresolvedReferences
                    x2: cython.int = x + dx
                    # noinspection PyUnresolvedReferences
                    y2: cython.int = y + dy
                    # noinspection PyUnresolvedReferences
                    z2: cython.int = z + dz
                    if self._mask is not None:
                        brush = bitwise_and(self._mask[z:z2, y:y2, x:x2], brush)
                    back = self._roi.getNumpy()[z:z2, y:y2, x:x2]
                    self._roi.getNumpy()[z:z2, y:y2, x:x2] = bitwise_or(back, brush)

    # Slice processing

    def flipSlice(self, sindex: int, dim: int, flipx: bool, flipy: bool) -> None:
        """
        Flip axes of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        flipx : bool
            flip x-slice-axis if True
        flipy : bool
            flip y-slice-axis if True
        """
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkFlip(img, [flipx, flipy])
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def shiftSlice(self, sindex: int, dim: int, movex: int, movey: int) -> None:
        """
        Image shift of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex :int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        movex : int
            shift in x-slice-axis (in voxels)
        movey : int
            shift in y-slice-axis (in voxels)
        """
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkShift(img, [movex, movey])
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def copySlice(self, sindex: int, dim: int) -> None:
        """
        Copy of a SisypheROI attribute slice to the clipboard.

        Parameters
        ----------
        sindex :int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        self._clipboard = self._extractSITKSlice(sindex, dim)

    def cutSlice(self, sindex: int, dim: int) -> None:
        """
        Cut of a SisypheROI attribute slice to the clipboard.

        Parameters
        ----------
        sindex :int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        self._clipboard = self._extractSITKSlice(sindex, dim)
        self.clearSlice(sindex, dim)
        if self._undo: self.appendSliceToLIFO(sindex, dim)

    def pasteSlice(self, sindex: int, dim: int) -> None:
        """
        Paste a SisypheROI attribute slice from the clipboard.

        Parameters
        ----------
        sindex :int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self._clipboard is not None and self._clipboard.GetDimension() == 2:
            self._updateSliceFromSITKImage(self._clipboard, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def morphoSliceDilate(self,
                          sindex: int,
                          dim: int,
                          radius: int | None = None,
                          struct: int | None = None) -> None:
        """
        Morphological dilatation of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological erosion of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological opening of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological closing of a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological dilatation of a SisypheROI attribute slice. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological erosion of a SisypheROI attribute slice. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological opening of a SisypheROI attribute slice. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological closing of a SisypheROI attribute slice. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
            - 0 z-axis slice (axial),
            - 1 y-axis slice (coronal),
            - 2 x-axis slice (sagittal)
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Fill holes in a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        undo : bool | None
            - if True, adds slice in the LIFO undo/redo stack
            - if None, takes state of the undo attribute of the current SisypheROIDraw instance (see setUndo() method)
        """
        if self.hasROI():
            if undo is None: undo = self._undo
            img = self._extractSITKSlice(sindex, dim)
            img = sitkBinaryFillHole(img)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if undo: self.appendSliceToLIFO(sindex, dim)

    def fillHolesAllSlices(self, dim: int) -> None:
        """
        Fill holes of the SisypheROI attribute. This method executes iteratively in 2D on all slices of the SisypheROI
        attribute.

        Parameters
        ----------
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            dz, dy, dx = self._roi.getNumpy().shape
            if dim == 0: d = dz
            elif dim == 1: d = dy
            else: d = dx
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(0, d):
                self.fillHolesSlice(i, dim, False)
            if self._undo: self.appendVolumeToLIFO()

    def seedFillSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        """
        Fill background voxels (i.e. 0 value) from a seed voxel in a SisypheROI attribute slice. Filling algorithm
        starts from a seed voxel whose x, y and z coordinates are provided.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis seed coordinate
        y : int
            y-axis seed coordinate
        z : int
            z-axis seed coordinate
        """
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
        """
        Fill background voxels (i.e. 0 value) from a seed voxel in the SisypheROI. Filling algorithm starts from a seed
        voxel whose x, y and z coordinates are provided.

        Parameters
        ----------
        x : int
            x-axis seed coordinate
        y : int
            y-axis seed coordinate
        z : int
            z-axis seed coordinate
        """
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
        """
        Clear a SisypheROI attribute slice (i.e. all voxels to 0).

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        img = self._extractSITKSlice(sindex, dim)
        img = sitkImage(img.GetSize(), sitkUInt8)
        self._updateSliceFromSITKImage(img, sindex, dim)
        if self._undo: self.appendSliceToLIFO(sindex, dim)

    def binaryNotSlice(self, sindex: int, dim: int) -> None:
        """
        Apply the binary not operator in a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            img = sitkBinaryNot(self._extractSITKSlice(sindex, dim))
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def objectSegmentSlice(self, sindex: int, dim: int, algo: str = 'huang') -> None:
        """
        Automatic mask segmentation in a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        algo : str
            algorithm used to find the best separation threshold between a mask and the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments' (default 'huang')
        """
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

    def backgroundSegmentSlice(self, sindex: int, dim: int, algo: str = 'huang') -> None:
        """
        Automatic background segmentation in a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        algo : str
            algorithm used to find the best separation threshold between a mask and the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments' (default 'huang')
        """

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
        """
        Remove blobs (connected components) from a SisypheROI attribute slice, according to their extent (number of
        voxels).

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        n : int
            number of voxels threshold
        """
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkConnectedComponent(img)
            img = sitkRelabelComponent(img, minimumObjectSize=n)
            img = (img > 0)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def majorBlobSelectSlice(self, sindex: int, dim: int):
        """
        Remove all blobs (connected components) except for the largest one, from a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = sitkConnectedComponent(img)
            img = sitkRelabelComponent(img, sortByObjectSize=True)
            # noinspection PyTypeChecker
            img: sitkImage = (img == 1)
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    # < Revision 20/10/2024
    # add clearBorderBlobSlice method
    def clearBorderBlobSlice(self, sindex: int, dim: int) -> None:
        """
        Remove all blobs (connected components) connected to image border, from a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
        if self.hasROI():
            img = self._extractSITKSlice(sindex, dim)
            img = clear_border(sitkGetArrayViewFromImage(img))
            self._updateSliceFromSITKImage(img, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)
    # Revision 20/10/2024 >

    def blobSelectSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        """
        Remove all blobs except the one containing the voxel whose coordinates are transmitted, from a SisypheROI
        attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                img = self._extractSITKSlice(sindex, dim)
                cimg = sitkConnectedComponent(img)
                if dim == 0: c = cimg[x, y]
                elif dim == 1: c = cimg[x, z]
                else: c = cimg[y, z]
                if c > 0:
                    img = (cimg == c)
                    # noinspection PyTypeChecker
                    self._updateSliceFromSITKImage(img, sindex, dim)
                    if self._undo: self.appendSliceToLIFO(sindex, dim)

    def blobRemoveSlice(self, sindex: int, dim: int, x: int, y: int, z: int) -> None:
        """
        Remove the blob containing the voxel whose coordinates are transmitted, from a SisypheROI attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Copy the blob containing the voxel whose coordinates are transmitted to clipboard, from a SisypheROI attribute
        slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Cut the blob containing the voxel whose coordinates are transmitted to clipboard, from a SisypheROI attribute
        slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Paste the blob from clipboard at the position of the voxel whose coordinates are transmitted, into a SisypheROI
        attribute slice.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Empty slices are interpolated between two non-empty slices above and below. Non-empty slices are searched for
        above and below a starting slice given as parameter. Cavalieri's interpolation method is used to fill in the
        empty slices of the SisypheROI attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        """
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
        """
        Cavalieri's interpolation method is used to fill in the slices of the SisypheROI attribute between two slices
        sent as parameters (sindex1 and sindex2).

        Parameters
        ----------
        sindex1 : int
            first slice index
        sindex2 : int
            last slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        replace : bool
            - if True, the interpolated slices replace the previous ones
            - if False (default), interpolated slices are combined (or logical) with previous ones
        """
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
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(1, n):
                        img1 = img1 + sitkCast(step * i, sitkFloat32)
                        img = img1 <= 0
                        self._updateSliceFromSITKImage(img, sindex1 + i, dim, replace=replace)
                    if self._undo: self.appendVolumeToLIFO()

    def extractingValueSlice(self,
                             sindex: int,
                             dim: int,
                             value: float,
                             mask: bool = False,
                             replace: bool = False) -> None:
        """
        Calculate a mask in a slice of the SisypheROI attribute of voxels with a given scalar value in the reference
        SisypheVolume attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        value : float
            scalar value in reference SisypheVolume attribute
        mask : bool
            if True, & (and) logic between mask and previous voxels of the slice (default False)
        replace : bool
            - if True, mask replaces previous voxels of the slice
            - if False (default), | (or) logic between mask and previous voxels of the slice
        """
        if self.hasVolume() and self.hasROI():
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            roi = img == value
            if mask: roi = roi & self._extractSITKSlice(sindex, dim)
            if not replace: roi = roi | roi1
            self._updateSliceFromSITKImage(roi, sindex, dim)
            if self._undo: self.appendSliceToLIFO(sindex, dim)

    def extractingValueBlobSlice(self, sindex: int, dim: int, value: float, x: int, y: int, z: int) -> None:
        """
        Calculate a mask limited to the surface of a blob in a slice of the SisypheROI attribute from voxels with a
        given scalar value in the SisypheVolume reference attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        value : float
            scalar value in reference SisypheVolume attribute
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Calculate a mask in a slice of the SisypheROI attribute of voxels whose scalar value is greater than a
        threshold in the reference SisypheVolume attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        mask : bool
            if True, & (and) logic between mask and previous voxels of the slice (default False)
        replace : bool
            - if True, mask replaces previous voxels of the slice
            - if False, | (or) logic between mask and previous voxels of the slice
        """
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
        """
        Calculate a mask limited to the surface of a blob in a slice of the SisypheROI attribute of voxels whose scalar
        value is greater than a threshold in the reference SisypheVolume attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Region growing from a seed voxel in a slice of the SisypheROI attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        mask : bool
            if True, & (and) logic between mask and previous voxels of the slice (default False)
        replace : bool
            - if True, mask replaces previous voxels of the slice
            - if False (default), or logic between mask and previous voxels of the slice
        """
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
        """
        Region growing from a seed voxel limited to the surface of a blob in a slice of the SisypheROI attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        """
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
                                     niter: int | None = None,
                                     multi: float | None = None,
                                     radius: int | None = None,
                                     mask: bool = False,
                                     replace: bool = False) -> None:
        """
        Region growing confidence from a seed voxel in a slice of the SisypheROI attribute.

        SimpleITK ConfidenceConnectedImageFilter doc:
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html

        This filter extracts a connected set of voxels whose voxel intensities are consistent with the voxel statistics
        of a seed point. The mean and variance across a neighborhood (8-connected, 26-connected, ...) are calculated
        for a seed point. Then voxels connected to this seed point whose values are within the confidence interval for
        the seed point are grouped. The width of the confidence interval is controlled by the "multi" parameter (the
        confidence interval is the mean plus or minus the "multi" times the standard deviation). If the intensity
        variations across a segment were gaussian, a "multi" setting of 2.5 would define a confidence interval wide
        enough to capture 99% of samples in the segment.

        After this initial segmentation is calculated, the mean and variance are re-calculated. All the voxels in the
        previous segmentation are used to calculate the mean the standard deviation (as opposed to using the voxels in
        the neighborhood of the seed point). The segmentation is then recalculated using these refined estimates for
        the mean and variance of the voxel values. This process is repeated for the specified number of iterations.
        Setting the number of iterations to zero stops the algorithm after the initial segmentation from the seed point.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        niter : int | None
            number of iteration (default None)
            if niter is None, niter = confidence connected iterations attribute of the current instance
        multi : float | None
            confidence interval = multi * standard deviation (default None)
            if multi is None, multi = confidence connected sigma attribute of the current instance
        radius : int | None
            neighborhood radius (default None)
            if radius is None, raidus = morphology radius attribute of the current instance
        mask : bool
            if True, & (and) logic between mask and previous voxels of the slice (default False)
        replace : bool
            - if True, mask replaces previous voxels of the slice
            - if False (default), or logic between mask and previous voxels of the slice
        """
        if self.hasVolume() and self.hasROI():
            if niter is None: niter = self._cciter
            if multi is None: multi = self._ccsigma
            if radius is None: radius = self._morphradius
            roi1 = self._extractSITKSlice(sindex, dim, roi=True)
            img = self._extractSITKSlice(sindex, dim, roi=False)
            if dim == 0:
                roi = sitkConfidenceConnected(img, [(x, y)],
                                              numberOfIterations=niter, multiplier=multi,
                                              initialNeighborhoodRadius=radius)
            elif dim == 1:
                roi = sitkConfidenceConnected(img, [(x, z)],
                                              numberOfIterations=niter, multiplier=multi,
                                              initialNeighborhoodRadius=radius)
            else:
                roi = sitkConfidenceConnected(img, [(y, z)],
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
                                         niter: int | None = None,
                                         multi: float | None = None,
                                         radius: int | None = None) -> None:
        """
        Region growing confidence from a seed voxel limited to the surface
        of a blob in a slice of the SisypheROI attribute.

        SimpleITK ConfidenceConnectedImageFilter doc:
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html

        This filter extracts a connected set of voxels whose voxel intensities are consistent with the voxel statistics
        of a seed point. The mean and variance across a neighborhood (8-connected, 26-connected, ...) are calculated
        for a seed point. Then voxels connected to this seed point whose values are within the confidence interval for
        the seed point are grouped. The width of the confidence interval is controlled by the "multi" parameter (the
        confidence interval is the mean plus or minus the "multi" times the standard deviation). If the intensity
        variations across a segment were gaussian, a "multi" setting of 2.5 would define a confidence interval wide
        enough to capture 99% of samples in the segment.

        After this initial segmentation is calculated, the mean and variance are re-calculated. All the voxels in the
        previous segmentation are used to calculate the mean the standard deviation (as opposed to using the voxels in
        the neighborhood of the seed point). The segmentation is then recalculated using these refined estimates for
        the mean and variance of the voxel values. This process is repeated for the specified number of iterations.
        Setting the number of iterations to zero stops the algorithm after the initial segmentation from the seed point.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        niter : int | None
            number of iteration (default None)
            if niter is None, niter = confidence connected iterations attribute of the current instance
        multi : float | None
            confidence interval = multi * standard deviation (default None)
            if multi is None, multi = confidence connected sigma attribute of the current instance
        radius : int | None
            neighborhood radius (default None)
            if radius is None, multi = morphology radius attribute of the current instance
        """
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if niter is None: niter = self._cciter
                if multi is None: multi = self._ccsigma
                if radius is None: radius = self._morphradius
                roi1 = self._extractSITKSlice(sindex, dim, roi=True)
                img = self._extractSITKSlice(sindex, dim, roi=False)
                cc = sitkConnectedComponent(roi1)
                if dim == 0:
                    mask = (cc == cc[x, y])
                    roi = sitkConfidenceConnected(img, [(x, y)],
                                                  numberOfIterations=niter, multiplier=multi,
                                                  initialNeighborhoodRadius=radius)
                elif dim == 1:
                    mask = (cc == cc[x, y])
                    roi = sitkConfidenceConnected(img, [(x, z)],
                                                  numberOfIterations=niter, multiplier=multi,
                                                  initialNeighborhoodRadius=radius)
                else:
                    mask = (cc == cc[x, y])
                    roi = sitkConfidenceConnected(img, [(y, z)],
                                                  numberOfIterations=niter, multiplier=multi,
                                                  initialNeighborhoodRadius=radius)
                roi1 = roi1 ^ mask
                roi = (roi & mask) | roi1
                self._updateSliceFromSITKImage(roi, sindex, dim)
                if self._undo: self.appendSliceToLIFO(sindex, dim)

    # Volume processing

    def flip(self, flipx: bool, flipy: bool, flipz: bool) -> None:
        """
        Flip axes of the SisypheROI image attribute.

        Parameters
        ----------
        flipx : bool
            flip x-slice-axis if True
        flipy : bool
            flip y-slice-axis if True
        flipz : bool
            flip z-slice-axis if True
        """
        if self.hasROI():
            img = sitkFlip(self._roi.getSITKImage(), [flipx, flipy, flipz])
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def shift(self, movex: int, movey: int, movez: int) -> None:
        """
        Image shift of the SisypheROI image attribute.

        Parameters
        ----------
        movex : int
            shift in x-slice-axis (in voxels)
        movey : int
            shift in y-slice-axis (in voxels)
        movez : int
            shift in z-slice-axis (in voxels)
        """
        if self.hasROI():
            img = sitkShift(self._roi.getSITKImage(), [movex, movey, movez])
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def euclideanDilate(self, mm: float = 0.0) -> None:
        """
        Expand the SisypheROI image attribute with a constant margin (in mm)

        Parameters
        ----------
        mm : float
            margin thickness in mm
        """
        if self.hasROI():
            if mm == 0.0: mm = self._thickness
            if mm > 0.0:
                dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                img = (dmap <= mm)
                img = sitkCast(img, sitkUInt8)
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def euclideanErode(self, mm: float = 0.0) -> None:
        """
        Shrink the SisypheROI image attribute with a constant margin (in mm)

        Parameters
        ----------
        mm : float
            margin thickness in mm
        """
        if self.hasROI():
            if mm == 0.0: mm = self._thickness
            if mm > 0.0:
                dmap = sitkSignedMaurerDistanceMap(self._roi.getSITKImage(), False, False, True)
                img = (dmap <= -mm)
                img = sitkCast(img, sitkUInt8)
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def morphoDilate(self, radius: int | None = None, struct: int | None = None) -> None:
        """
        Morphological dilatation of the SisypheROI image attribute.

        Parameters
        ----------
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryDilate(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoErode(self, radius: int | None = None, struct: int | None = None) -> None:
        """
        Morphological erosion of the SisypheROI image attribute.

        Parameters
        ----------
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryErode(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoOpening(self, radius: int | None = None, struct: int | None = None) -> None:
        """
        Morphological opening of the SisypheROI image attribute.

        Parameters
        ----------
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryOpening(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def morphoClosing(self, radius: int | None = None, struct: int | None = None) -> None:
        """
        Morphological closing of the SisypheROI image attribute.

        Parameters
        ----------
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
        if self.hasROI():
            if radius is None: radius = self._morphradius
            if struct is None: struct = self._struct
            img = sitkBinaryClosing(self._roi.getSITKImage(), [radius, radius, radius], struct)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def euclideanBlobDilate(self, x: int, y: int, z: int, mm: float = 0.0) -> None:
        """
        Expand a selected blob in the SisypheROI image attribute with a constant margin (in mm).

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        mm : float
            margin thickness in mm
        """
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
        """
        Shrink a selected blob in the SisypheROI image attribute with a constant margin (in mm).

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        mm : float
            margin thickness in mm
        """
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
        """
        Morphological dilatation of the SisypheROI image attribute. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological erosion of the SisypheROI image attribute. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological opening of the SisypheROI image attribute. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Morphological closing of the SisypheROI image attribute. Processing only applies to a blob selected by the
        coordinates of one of its voxels.

        Parameters
        ----------
        x : int
            x-axis coordinate of the voxel used for blob selection
        y : int
            y-axis coordinate of the voxel used for blob selection
        z : int
            z-axis coordinate of the voxel used for blob selection
        radius : int | None
            structuring element radius in voxels (Default is None). If None, get radius from the morphological radius
            attribute of the current SisypheROIDraw instance (see setMorphologyRadius() method)
        struct : int | None
            structuring element shape as SimpleITK int code (Default is None)
                - 0 Annulus
                - 1 disk
                - 2 box
                - 3 cross
                - if None, get structuring element shape from the structuring element attribute of the current SisypheROIDraw instance (see setStructElement() method)
        """
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
        """
        Binary "logic and" between the SisypheROI image attribute and a list of SisypheROI images (or
        SisypheROICollection).

        Parameters
        ----------
        rois : list[SisypheROI] | SisypheROICollection
            rois to be processed
        """
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    temp = temp & rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryOR(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        """
        Binary "logic or" between the SisypheROI image attribute and a list of SisypheROI images (or
        SisypheROICollection).

        Parameters
        ----------
        rois : list[SisypheROI] | SisypheROICollection
            rois to be processed
        """
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    temp = temp | rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryXOR(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        """
        Binary "logic xor" between the SisypheROI image attribute and a list of SisypheROI images (or
        SisypheROICollection).

        Parameters
        ----------
        rois : list[SisypheROI] | SisypheROICollection
            rois to be processed
        """
        if self.hasROI():
            n = len(rois)
            if n > 1:
                temp = rois[0].getNumpy()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(1, n):
                    temp = temp ^ rois[i].getNumpy()
                self._updateRoiFromNumpy(temp)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter has less than two items.')

    def binaryNAND(self, rois: list[SisypheROI] | SisypheROICollection) -> None:
        """
        Binary "logic nand (not and)" between the SisypheROI image attribute and a list of SisypheROI images (or
        SisypheROICollection).

        Parameters
        ----------
        rois : list[SisypheROI] | SisypheROICollection
            rois to be processed
        """
        if self.hasROI():
            n = len(rois)
            if n > 0:
                temp1 = rois[0].getNumpy()
                temp2 = rois[1].getNumpy()
                # noinspection PyUnresolvedReferences
                i: cython.int
                # < Revision 21/03/2025
                # for i in range(2, n): temp2 = temp2 & rois[i].getNumpy()
                for i in range(2, n): temp2 = temp2 | rois[i].getNumpy()
                # Revision 21/03/2025 >
                temp1 = temp1 & logical_not(temp2).astype(uint8)
                self._updateRoiFromNumpy(temp1)
                if self._undo: self.appendVolumeToLIFO()
            else: raise ValueError('list parameter is empty.')

    def binaryNOT(self) -> None:
        """
        Binary "not" of the SisypheROI image attribute.
        """
        if self.hasROI():
            img = sitkBinaryNot(self._roi.getSITKImage())
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def fillHoles(self) -> None:
        """
        Fill holes in the SisypheROI image attribute.
        """
        if self.hasROI():
            img = sitkBinaryFillHole(self._roi.getSITKImage())
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def clear(self) -> None:
        """
        Clear the SisypheROI image attribute (i.e. all voxels to 0).
        """
        img = sitkImage(self._roi.getSITKImage().GetSize(), sitkUInt8)
        self._updateRoiFromSITKImage(img)
        if self._undo: self.appendVolumeToLIFO()

    def objectSegment(self, algo: str = 'huang') -> None:
        """
        Automatic mask segmentation of the SisypheROI image attribute.

        Parameters
        ----------
        algo : str
            algorithm used to find the best threshold for separating a mask from the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments'
        """
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

    def backgroundSegment(self, algo: str = 'huang') -> None:
        """
        Automatic background segmentation of the SisypheROI image attribute.

        Parameters
        ----------
        algo : str
            algorithm used to find the best threshold for separating a mask from the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments'
        """
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
                    algo: str = 'huang',
                    morpho: str = '',
                    niter: int = 1,
                    kernel: int = 0,
                    fill: str = ''):
        """
        Automatic head/brain mask segmentation of the SisypheROI image attribute.

        Parameters
        ----------
        algo : str
            algorithm used to find the best threshold for separating a mask from the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments'
        morpho : str
            binary morphology operator: 'dilate', 'erode', 'open', 'close', '' (default, no morphology)
        niter : int
            number of binary morphology iterations
        kernel : int
            structuring element size
        fill : str
            - '2d', fill holes slice by slice
            - '3d', fill holes in 3D
            - '', no filling
        """
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
            if QApplication.instance() is not None: QApplication.processEvents()
            # mask = not( background )
            img = sitkBinaryNot(img)
            # Morphology operator
            if isinstance(kernel, int):
                if kernel > 0 and morpho in ('dilate', 'erode', 'open', 'close'):
                    morpho = morpho.lower()
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(niter):
                        if morpho == 'dilate': img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        elif morpho == 'erode': img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        elif morpho == 'open':
                            # noinspection PyUnusedLocal
                            img = sitkBinaryOpening(img, [kernel, kernel, kernel])
                            break
                        elif morpho == 'close':
                            # noinspection PyUnusedLocal
                            img = sitkBinaryClosing(img, [kernel, kernel, kernel])
                            break
                        if QApplication.instance() is not None: QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            # Filling
            if fill == '2d':
                f = BinaryFillholeImageFilter()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(img.GetSize()[2]):
                    slc = img[:, :, i]
                    slc = f.Execute(slc)
                    img[:, :, i] = slc
                    if QApplication.instance() is not None: QApplication.processEvents()
            elif fill == '3d':
                img = sitkBinaryFillHole(img)
                if QApplication.instance() is not None: QApplication.processEvents()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def maskSegment2(self,
                     algo: str = 'huang',
                     morphoiter: int = 2,
                     kernel: int = 0):
        """
        Automatic head/brain mask segmentation of the SisypheROI image attribute.

        Parameters
        ----------
        algo : str
            algorithm used to find the best threshold for separating a mask from the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments'
        morphoiter : int
            number of binary morphology iterations
        kernel : int
            structuring element size, 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)
        """
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
            if QApplication.instance() is not None: QApplication.processEvents()
            # Background processing
            if isinstance(kernel, int):
                if kernel == 0:
                    if max(self._volume.getSpacing()) < 1.5: kernel = 2
                    else: kernel = 1
                # Erode
                if morphoiter > 0:
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(morphoiter):
                        img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        if QApplication.instance() is not None: QApplication.processEvents()
                # keep major blob (remove blobs in head/brain)
                blobs = sitkConnectedComponent(img)
                if QApplication.instance() is not None: QApplication.processEvents()
                blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
                if QApplication.instance() is not None: QApplication.processEvents()
                img = blobs == 1
                # Dilate
                if morphoiter > 0:
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(morphoiter):
                        img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        if QApplication.instance() is not None: QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            # Object = not( background )
            img = sitkBinaryNot(img)
            # Object processing
            if isinstance(kernel, int):
                # Erode
                if morphoiter > 0:
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(morphoiter):
                        img = sitkBinaryErode(img, [kernel, kernel, kernel])
                        if QApplication.instance() is not None: QApplication.processEvents()
                # keep major blob (remove blobs in head/brain)
                blobs = sitkConnectedComponent(img)
                if QApplication.instance() is not None: QApplication.processEvents()
                blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
                if QApplication.instance() is not None: QApplication.processEvents()
                img = blobs == 1
                # Dilate
                if morphoiter > 0:
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(morphoiter):
                        img = sitkBinaryDilate(img, [kernel, kernel, kernel])
                        if QApplication.instance() is not None: QApplication.processEvents()
            else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
            # noinspection PyTypeChecker
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def notMaskSegment2(self,
                        algo: str = 'huang',
                        morphoiter: int = 2,
                        kernel: int = 0):
        """
        Automatic background mask segmentation of the SisypheROI image attribute.

        Parameters
        ----------
        algo : str
            algorithm used to find the best threshold for separating a mask from the background. Available algorithm
            names : 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes',
            'maximumentropy', 'kittler', 'isodata', 'moments'
        morphoiter : int
            number of binary morphology iterations
        kernel : int
            structuring element size, 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)
        """
        self.maskSegment2(algo, morphoiter, kernel)
        self.binaryNOT()

    def blobFilterExtent(self, n: int) -> None:
        """
        Remove blobs (connected components) from the SisypheROI image attribute, according to their extent (number of
        voxels).

        Parameters
        ----------
        n : int
            number of voxels threshold
        """
        if self.hasROI():
            img = sitkConnectedComponent(self._roi.getSITKImage())
            img = sitkRelabelComponent(img, minimumObjectSize=n)
            img = (img > 0)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def majorBlobSelect(self) -> None:
        """
        Remove all blobs (connected components) except the largest one, from the SisypheROI image attribute.
        """
        if self.hasROI():
            img = sitkConnectedComponent(self._roi.getSITKImage())
            img = sitkRelabelComponent(img, sortByObjectSize=True)
            # noinspection PyTypeChecker
            img: sitkImage = (img == 1)
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    # < Revision 20/10/2024
    # add clearBorderBlob method
    def clearBorderBlob(self) -> None:
        """
        Remove all blobs (connected components) connected to image border.
        """
        if self.hasROI():
            img = clear_border(self._roi.getNumpy())
            self._updateRoiFromNumpy(img)
            if self._undo: self.appendVolumeToLIFO()
    # Revision 20/10/2024 >

    def blobSelect(self, x: int, y: int, z: int) -> None:
        """
        Remove all blobs except the one containing the voxel whose coordinates are transmitted, from the SisypheROI
        image attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
        if self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                cimg = sitkConnectedComponent(self._roi.getSITKImage())
                c = cimg[x, y, z]
                if c > 0:
                    img = (cimg == c)
                    # noinspection PyTypeChecker
                    self._updateRoiFromSITKImage(img)
                    if self._undo: self.appendVolumeToLIFO()

    def blobRemove(self, x: int, y: int, z: int) -> None:
        """
        Remove the blob containing the voxel whose coordinates are transmitted, from the SisypheROI image attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Copy to clipboard the blob containing the voxel whose coordinates are transmitted, from the SisypheROI image
        attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Cut to clipboard the blob containing the voxel whose coordinates are transmitted, from the SisypheROI image
        attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Paste the blob from clipboard at the position of the voxel whose coordinates are transmitted, into the
        SisypheROI image attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
        if self.hasROI():
            if self._clipboard is not None:
                img = Paste(self._roi.getSITKImage(),
                            self._clipboard,
                            self._clipboard.GetSize(),
                            (0, 0, 0), (x, y, z))
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    def extractingValue(self, value: float, mask: bool = False, replace: bool = False) -> None:
        """
        Calculate a mask of the SisypheROI image attribute of voxels with a given scalar value in the reference
        SisypheVolume image attribute.

        Parameters
        ----------
        value : float
            scalar value in reference SisypheVolume attribute
        mask : bool
            if True, & (and) logic between mask and previous voxels (default False)
        replace : bool
            - if True, mask replaces previous voxels
            - if False (default), | (or) logic between mask and previous voxels
        """
        if self.hasVolume() and self.hasROI():
            img = self._volume.getSITKImage() == value
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def extractingValueBlob(self, value: float, x: int, y: int, z: int) -> None:
        """
        Calculate a mask limited to a blob of the SisypheROI image attribute from voxels with a given scalar value in
        the reference SisypheVolume image
        attribute.

        Parameters
        ----------
        value : float
            scalar value in reference SisypheVolume attribute
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Calculate a mask of the SisypheROI image attribute of voxels whose scalar value is greater than a threshold
        in the reference SisypheVolume image attribute.

        Parameters
        ----------
        mask : bool
            if True, & (and) logic between mask and previous voxels (default False)
        replace : bool
            - if True, mask replaces previous voxels
            - if False (default), | (or) logic between mask and previous voxels
        """
        if self.hasVolume() and self.hasROI():
            img = sitkThreshold(self._volume.getSITKImage(),
                                lowerThreshold=float(self._thresholdmin),
                                upperThreshold=float(self._thresholdmax))
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def thresholdingBlob(self, x: int, y: int, z: int) -> None:
        """
        Calculate a mask limited to a blob of the SisypheROI image attribute of voxels whose scalar value is greater
        than a threshold in the reference image SisypheVolume attribute.

        Parameters
        ----------
        x : int
            x-axis blob selection coordinate
        y : int
            y-axis blob selection coordinate
        z : int
            z-axis blob selection coordinate
        """
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
        """
        Region growing from a seed voxel in the SisypheROI image attribute.

        Parameters
        ----------
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        mask : bool
            if True, & (and) logic between mask and previous voxels (default False)
        replace : bool
            - if True, mask replaces previous voxels
            - if False (default), | (or) logic between mask and previous voxels
        """
        if self.hasVolume() and self.hasROI():
            img = sitkConnectedThreshold(self._volume.getSITKImage(), [(x, y, z)],
                                         lower=self._thresholdmin, upper=self._thresholdmax)
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def regionGrowingBlob(self, x: int, y: int, z: int) -> None:
        """
        Region growing from a seed voxel limited to a blob in the SisypheROI image attribute.

        Parameters
        ----------
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        """
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
                                niter: int | None = None,
                                multi: float | None = None,
                                radius: int | None = None,
                                mask: bool = False,
                                replace: bool = False) -> None:
        """
        Region growing confidence from a seed voxel in the SisypheROI image attribute.

        SimpleITK ConfidenceConnectedImageFilter doc:
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html

        This filter extracts a connected set of voxels whose voxel intensities are consistent with the voxel statistics
        of a seed point. The mean and variance across a neighborhood (8-connected, 26-connected, ...) are calculated
        for a seed point. Then voxels connected to this seed point whose values are within the confidence interval for
        the seed point are grouped. The width of the confidence interval is controlled by the "multi" parameter (the
        confidence interval is the mean plus or minus the "multi" times the standard deviation). If the intensity
        variations across a segment were gaussian, a "multi" setting of 2.5 would define a confidence interval wide
        enough to capture 99% of samples in the segment.

        After this initial segmentation is calculated, the mean and variance are re-calculated. All the voxels in the
        previous segmentation are used to calculate the mean the standard deviation (as opposed to using the voxels in
        the neighborhood of the seed point). The segmentation is then recalculated using these refined estimates for
        the mean and variance of the voxel values. This process is repeated for the specified number of iterations.
        Setting the number of iterations to zero stops the algorithm after the initial segmentation from the seed point.

        Parameters
        ----------
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        niter : int | None
            number of iteration (default None)
            if niter is None, niter = confidence connected iterations attribute of the current instance
        multi : float | None
            confidence interval = multi * standard deviation (default None)
            if multi is None, multi = confidence connected sigma attribute of the current instance
        radius : int | None
            neighborhood radius (default None)
            if radius is None, raidus = morphology radius attribute of the current instance
        mask : bool
            if True, & (and) logic between mask and previous voxels (default False)
        replace : bool
            - if True, mask replaces previous voxels
            - if False, | (or) logic between mask and previous voxels
        """
        if self.hasVolume() and self.hasROI():
            if niter is None: niter = self._cciter
            if multi is None: multi = self._ccsigma
            if radius is None: radius = self._morphradius
            img = sitkConfidenceConnected(self._volume.getSITKImage(), [(x, y, z)],
                                          numberOfIterations=niter, multiplier=multi,
                                          initialNeighborhoodRadius=radius)
            if mask: img = img & self._roi.getSITKImage()
            if not replace: img = img | self._roi.getSITKImage()
            self._updateRoiFromSITKImage(img)
            if self._undo: self.appendVolumeToLIFO()

    def regionGrowingConfidenceBlob(self,
                                    x: int, y: int, z: int,
                                    niter: int | None = None,
                                    multi: float | None= None,
                                    radius: int | None = None) -> None:
        """
        Region growing confidence from a seed voxel limited to a blob in the SisypheROI image attribute.

        See SimpleITK ConfidenceConnectedImageFilter doc:
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html

        This filter extracts a connected set of voxels whose voxel intensities are consistent with the voxel statistics
        of a seed point. The mean and variance across a neighborhood (8-connected, 26-connected, ...) are calculated
        for a seed point. Then voxels connected to this seed point whose values are within the confidence interval for
        the seed point are grouped. The width of the confidence interval is controlled by the "multi" parameter (the
        confidence interval is the mean plus or minus the "multi" times the standard deviation). If the intensity
        variations across a segment were gaussian, a "multi" setting of 2.5 would define a confidence interval wide
        enough to capture 99% of samples in the segment.

        After this initial segmentation is calculated, the mean and variance are re-calculated. All the voxels in the
        previous segmentation are used to calculate the mean the standard deviation (as opposed to using the voxels in
        the neighborhood of the seed point). The segmentation is then recalculated using these refined estimates for
        the mean and variance of the voxel values. This process is repeated for the specified number of iterations.
        Setting the number of iterations to zero stops the algorithm after the initial segmentation from the seed point.

        Parameters
        ----------
        x : int
            x-axis seed voxel coordinate
        y : int
            y-axis seed voxel coordinate
        z : int
            z-axis seed voxel coordinate
        niter : int | None
            number of iteration (default None)
            if niter is None, niter = confidence connected iterations attribute of the current instance
        multi : float
            confidence interval = multi * standard deviation (default None)
            if multi is None, multi = confidence connected sigma attribute of the current instance
        radius : int | None
            neighborhood radius (default None)
            if radius is None, raidus = morphology radius attribute of the current instance
        """
        if self.hasVolume() and self.hasROI():
            if self._roi.getSITKImage()[x, y, z] > 0:
                if niter is None: niter = self._cciter
                if multi is None: multi = self._ccsigma
                if radius is None: radius = self._morphradius
                roi1 = self._roi.getSITKImage()
                cc = sitkConnectedComponent(roi1)
                mask = (cc == cc[x, y, z])
                img = sitkConfidenceConnected(self._volume.getSITKImage(), [(x, y, z)],
                                              numberOfIterations=niter, multiplier=multi,
                                              initialNeighborhoodRadius=radius)
                roi1 = roi1 ^ mask
                img = (img & mask) | roi1
                self._updateRoiFromSITKImage(img)
                if self._undo: self.appendVolumeToLIFO()

    # < Revision 25/03/2025
    def activeContourSegmentation(self, x: int, y: int, z: int) -> None:
        """
        Active contour, level set method of segmentation, in the SisypheROI image attribute. Iterative algorithm
        starting from a seed sphere. This method used active contour attributes of the current SisypheDraw instance as
        parameters (seed radius, sigma, rms, advection weight, curvature weight, propagation weight, number of
        iterations, algorithm).

        Parameters
        ----------
        x : int
            x-axis seed sphere coordinate
        y : int
            y-axis seed sphere coordinate
        z : int
            z-axis seed sphere coordinate
        """
        if self._acalgo in ('geodesic', 'shape'):
            self.activeContour(x, y, z,
                               self._acradius,
                               self._acsigma,
                               self._acrms,
                               self._acadvec,
                               self._accurv,
                               self._acpropag,
                               self._aciter,
                               self._acalgo)
        elif self._acalgo == 'threshold':
            self.activeThresholdContour(x, y, z,
                                        self._acradius,
                                        self._acfactor,
                                        self._acrms,
                                        self._accurv,
                                        self._acpropag,
                                        self._acthresholds,
                                        self._aciter)
        else: raise ValueError('{} invalid active contour algorithm.'.format(self._acalgo))
    # Revision 25/03/2025 >

    def activeContour(self,
                      x: int, y: int, z: int,
                      seedradius: float = 2.0,
                      sigma: float = 1.0,
                      rms: float = 0.01,
                      advec: float = 1.0,
                      curv: float = 1.0,
                      propag: float = 1.0,
                      niter: int = 1000,
                      algo: str = 'default',
                      replace: bool = False) -> None:
        """
        Active contour, level set method of segmentation, in the SisypheROI image attribute. Iterative algorithm
        starting from a seed sphere.

        See SimpleITK GeodesicActiveContourLevelSetImageFilter doc:
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1GeodesicActiveContourLevelSetImageFilter.html

        Parameters
        ----------
        x : int
            x-axis seed sphere coordinate
        y : int
            y-axis seed sphere coordinate
        z : int
            z-axis seed sphere coordinate
        seedradius : float
            radius in mm of the seed sphere centered on x, y, z (default 2.0). If roi[x, y, z] is not background
            (i.e. > 0), use blob as seed rather than sphere, seedradius parameter is then ignored.
        sigma : float
            gaussian kernel parameter used to compute the magnitude of the gradient. The edge potential map of the
            level set algorithm is computed from the image gradient. Edge potential map is that it has values close to
            zero in regions near the edges and values close to one inside the shape itself. This map is the image from
            which the speed function will be calculated.
        rms : float
            convergence threshold (0.0 < rms < 1.0, default 0.01). rms is used to determine when the solution has
            converged. A lower value will result in a tighter-fitting solution, but will require more computations. Too
            low a value could put the solver into an infinite loop unless a reasonable number of iterations parameter
            is set.
        curv : float
            curvature, larger -> smoother resulting contour (default 1.0). Controls the magnitude of the curvature
            values which are calculated on the evolving isophote. This is important in controlling the relative effect
            of curvature in the calculation. Default value is 1.0. Higher values relative to the other level set
            equation terms (propagation and advection) will give a smoother result.
        advec : float
            advection, default 1.0. Controls the scaling of the vector advection field term relative to other terms in
            the level set equation
        propag : float
            propagation speed (default 1.0). > 0 propagation outwards, < 0 propagating inwards controls the scaling of
            the scalar propagation (speed) term relative to other terms in the level set equation
        niter : int
            maximum number of iterations (default 1000). Can be used to halt the solution after a specified number of
            iterations, overriding the rms halting criteria
        algo : str
            algorithm 'default' SimpleITK GeodesicActiveContourLevelSetImageFilter or 'shape' SimpleITK
            ShapeDetectionLevelSetImageFilter
        replace : bool
            - if True, segmented mask replaces previous voxels
            - if False (default), | (or) logic between mask and previous voxels
        """
        seedradius = seedradius * 2 + 1
        img = sitkCast(self._volume.getSITKImage(), sitkFloat32)
        speed = sitkBoundedReciprocal(sitkGradientMagnitude(img, sigma))
        if self._roi[x, y, z] == 0:
            seed = sitkImage(self._volume.getSize()[0],
                             self._volume.getSize()[1],
                             self._volume.getSize()[2],
                             sitkUInt8)
            seed.SetSpacing(self._volume.getSpacing())
            seed.SetOrigin(img.GetOrigin())
            seed[x, y, z] = 1
            seed = sitkSignedMaurerDistanceMap(seed, insideIsPositive=False, useImageSpacing=True)
        else:
            cimg = sitkConnectedComponent(self._roi.getSITKImage())
            c = cimg[x, y, z]
            seed = (cimg == c)
        seed = sitkCast(sitkThreshold(seed, -1000, seedradius), speed.GetPixelID()) * -1 + 0.5
        # < debug
        vol = SisypheVolume()
        vol.copyFromSITKImage(seed)
        vol.saveAs('activecontour_seed.xvol')
        vol2 = SisypheVolume()
        vol2.copyFromSITKImage(speed)
        vol2.saveAs('activecontour_speed.xvol')
        # debug >
        if algo == 'shape': flt = sitkShapeDetectionLevelSetImageFilter()
        else:
            flt = sitkGeodesicActiveContourLevelSetImageFilter()
            flt.SetAdvectionScaling(advec)
        flt.SetMaximumRMSError(rms)
        flt.SetNumberOfIterations(niter)
        flt.SetCurvatureScaling(curv)
        flt.SetPropagationScaling(propag)
        roi = self._roi.copyToSITKImage()
        img = sitkThreshold(flt.Execute(seed, speed), -1000, 0)
        if not replace: img = img | roi
        self._updateRoiFromSITKImage(img)
        if self._undo: self.appendVolumeToLIFO()

    def activeThresholdContour(self,
                               x: int, y: int, z: int,
                               seedradius: float = 2.0,
                               factor: float = 3.0,
                               rms: float = 0.01,
                               curv: float = 1.0,
                               propag: float = 1.0,
                               thresholds: tuple[float, float] | None = None,
                               niter: int = 1000,
                               replace: bool = False) -> None:
        """
        Active contour, level set method of segmentation, in the SisypheROI image attribute. Iterative algorithm
        starting from a seed sphere.

        See SimpleITK ThresholdSegmentationLevelSetImageFilter doc:
        https://simpleitk.org/doxygen/v1_0/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html

        Parameters
        ----------
        x : int
            x-axis seed sphere coordinate
        y : int
            y-axis seed sphere coordinate
        z : int
            z-axis seed sphere coordinate
        seedradius : float
            radius in mm of the seed sphere centered on x, y, z (default 2.0). If roi[x, y, z] is not background
            (i.e. > 0), use blob as seed rather than sphere, seedradius parameter is then ignored.
        factor : float
            factor x standard deviation of signal in seed sphere to estimate lower and upper thresholds used by level
            set algorithm (default 3.0)
        rms : float
            convergence threshold (0.0 < rms < 1.0, default 0.01). rms is used to determine when the solution has
            converged. A lower value will result in a tighter-fitting solution, but will require more computations. Too
            low a value could put the solver into an infinite loop unless a reasonabl number of iterations parameter is
            set.
        curv : float
            curvature, larger -> smoother resulting contour (default 1.0). Controls the magnitude of the curvature
            values which are calculated on the evolving isophote. This is important in controlling the relative effect
            of curvature in the calculation. Default value is 1.0. Higher values relative to the other level set
            equation terms (propagation and advection) will give a smoother result.
        propag : float
            propagation speed (default 1.0). > 0 propagation outwards, < 0 propagating inwards controls the scaling of
            the scalar propagation (speed) term relative to other terms in the level set equation.
        thresholds : tuple[float, float] | None
            Lower and upper thresholds used by level set algorithm. If None, threshold are computed from seed region
            (mean +/- factor * sigma)
        niter : int
            maximum number of iterations (default 1000). Can be used to halt the solution after a specified number of
            iterations, overriding the rms halting criteria
        replace : bool
            - if True, segmented mask replaces previous voxels
            - if False (default), | (or) logic between mask and previous voxels
        """
        seedradius = seedradius * 2 + 1
        img = sitkCast(self._volume.getSITKImage(), sitkFloat32)
        if self._roi[x, y, z] == 0:
            seed = sitkImage(self._volume.getSize()[0],
                             self._volume.getSize()[1],
                             self._volume.getSize()[2],
                             sitkUInt8)
            seed.SetSpacing(self._volume.getSpacing())
            seed.SetOrigin(img.GetOrigin())
            seed[x, y, z] = 1
            seed = sitkSignedMaurerDistanceMap(seed, insideIsPositive=False, useImageSpacing=True)
            seed = sitkThreshold(seed, -1000, seedradius)
        else:
            cimg = sitkConnectedComponent(self._roi.getSITKImage())
            c = cimg[x, y, z]
            seed = (cimg == c)
        if thresholds is None:
            stats = sitkLabelStatisticsImageFilter()
            stats.Execute(img, seed)
            lower_threshold = stats.GetMean(1) - factor * stats.GetSigma(1)
            upper_threshold = stats.GetMean(1) + factor * stats.GetSigma(1)
        else:
            lower_threshold = thresholds[0]
            upper_threshold = thresholds[1]
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

    # Draw methods

    # < Revision 20/10/2024
    # add drawLine method, not yet tested
    def drawLine(self, p0: vectorInt3, p1: vectorInt3, orient: int = 0) -> None:
        """
        Draw a line in the current SisypheROI image attribute. Line is drawn in a single slice (p0 and p1 must be
        within the same slice)

        Parameters
        ----------
        p0 : tuple[int, int, int] | list[int, int, int]
            x, y, z first point coordinates
        p1 : tuple[int, int, int] | list[int, int, int]
            x, y, z second point coordinates
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawLine(p0, p1, orient)
            if orient == 0: sindex = p0[2]
            elif orient == 1: sindex = p0[1]
            else: sindex = p0[0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawDisk method, not yet tested
    def drawDisk(self, p: vectorInt3, radius: int, orient: int = 0) -> None:
        """
        Draw a disk in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center point coordinates
        radius : int
            disk radius (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawDisk(p, radius, orient)
            if orient == 0: sindex = p[2]
            elif orient == 1: sindex = p[1]
            else: sindex = p[0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawEllipse method, not yet tested
    def drawEllipse(self, p: vectorInt3, radius: vectorInt2, rot: float = 0.0, orient: int = 0) -> None:
        """
        Draw an ellipse in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center point coordinates
        radius : tuple[int, int] | list[int, int]
            radius in x and y axes (in voxels)
        rot : float
            set the ellipse rotation in radians (between -pi and pi, default 0.0)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawEllipse(p, radius, rot, orient)
            if orient == 0: sindex = p[2]
            elif orient == 1: sindex = p[1]
            else: sindex = p[0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawSquare method, not yet tested
    def drawSquare(self, p: vectorInt3, extent: int, orient: int = 0) -> None:
        """
        Draw a square in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : int
            length of square sides (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawSquare(p, extent, orient)
            if orient == 0: sindex = p[2]
            elif orient == 1: sindex = p[1]
            else: sindex = p[0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawRectangle method, not yet tested
    def drawRectangle(self, p: vectorInt3, extent: vectorInt2, orient: int = 0) -> None:
        """
        Draw a rectangle in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : tuple[int, int] | list[int, int]
            width and height (in voxels)
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawRectangle(p, extent, orient)
            if orient == 0: sindex = p[2]
            elif orient == 1: sindex = p[1]
            else: sindex = p[0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawPolygon method, not yet tested
    def drawPolygon(self, p: list[list[int]], orient: int = 0) -> None:
        """
        Draw a polygon in the current SisypheROI image attribute.
        Polygon is drawn in a single slice (all points must be within the same slice).

        Parameters
        ----------
        p : list[list[int]]
            list of 3 list[int]:
            - first list[int],  x coordinates of points
            - second list[int], y coordinates of points
            - third list[int],  z coordinates of points
        orient : int
            slice orientation (0 axial, 1 coronal, 2 sagittal)
        """
        if self.hasROI():
            self._roi.drawPolygon(p, orient)
            if orient == 0: sindex = p[0][2]
            elif orient == 1: sindex = p[0][1]
            else: sindex = p[0][0]
            if self._undo: self.appendSliceToLIFO(sindex, orient)
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawCube method, not yet tested
    def drawCube(self, p: vectorInt3, extent: int) -> None:
        """
        Draw a cube in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : int
            length of cube sides (in voxels)
        """
        if self.hasROI():
            self._roi.drawCube(p, extent)
            if self._undo: self.appendVolumeToLIFO()
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawParallelepiped method, not yet tested
    def drawParallelepiped(self, p: vectorInt3, extent: vectorInt3) -> None:
        """
        Draw a parallelepiped in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z origin coordinates
        extent : tuple[int, int, int] | list[int, int, int]
            width, height and depth (in voxels)
        """
        if self.hasROI():
            self._roi.drawParallelepiped(p, extent)
            if self._undo: self.appendVolumeToLIFO()
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add drawSphere method, not yet tested
    def drawSphere(self, p: vectorInt3, radius: int) -> None:
        """
        Draw a sphere in the current SisypheROI image attribute.

        Parameters
        ----------
        p : tuple[int, int, int] | list[int, int, int]
            x, y, z center coordinates
        radius : int
            sphere radius (in voxels)
        """
        if self.hasROI():
            self._roi.drawParallelepiped(p, radius)
            if self._undo: self.appendVolumeToLIFO()
    # Revision 20/10/2024 >

    # Statistics

    def getIntensityStatistics(self) -> dict[str, float]:
        """
        Get the descriptive statistics of scalar values in the reference SisypheVolume image attribute masked by the
        SisypheROI image attribute.

        Returns
        -------
        dict[str, float]
            key (str) / value (float)
                - 'count'       number of voxels
                - 'mean'        mean
                - 'median'      median
                - 'min'         minimum
                - 'max'         maximum
                - 'range'       maximum - minimum
                - 'perc25'      first quartile
                - 'perc75'      third quartile
                - 'var'         variance
                - 'std'         standard deviation
                - 'skewness'    skewness
                - 'kurtosis'    kurtosis
        """
        stats = dict()
        if self.hasVolume() and self.hasROI():
            mask = self._roi.getNumpy().flatten() > 0
            img = self._volume.getNumpy().flatten()[mask]
            r = describe(img)
            # noinspection PyUnresolvedReferences
            stats['count'] = r.nobs
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            stats['median'] = median(img)
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['range'] = r.minmax[1] - r.minmax[0]
            stats['perc25'] = percentile(img, 25)
            stats['perc75'] = percentile(img, 75)
            # noinspection PyUnresolvedReferences
            stats['var'] = r.variance
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
        return stats

    def getSliceIntensityStatistics(self, sindex: int, dim: int) -> dict[str, float]:
        """
        Get the descriptive statistics of scalar values in a slice of the reference SisypheVolume image attribute
        masked by the SisypheROI image attribute.

        Parameters
        ----------
        sindex : int
            slice index
        dim : int
            slice orientation code,
                - 0 z-axis slice (axial),
                - 1 y-axis slice (coronal),
                - 2 x-axis slice (sagittal)

        Returns
        -------
        dict[str, float]
            key (str) / value (float)
                - 'count'       number of voxels
                - 'mean'        mean
                - 'median'      median
                - 'min'         minimum
                - 'max'         maximum
                - 'range'       maximum - minimum
                - 'perc25'      first quartile
                - 'perc75'      third quartile
                - 'var'         variance
                - 'std'         standard deviation
                - 'skewness'    skewness
                - 'kurtosis'    kurtosis
        """
        stats = dict()
        if self.hasVolume() and self.hasROI():
            # noinspection PyTypeChecker
            roi: sitkImage = (self._extractSITKSlice(sindex, dim) > 0)
            slc = self._extractSITKSlice(sindex, dim, roi=False)
            mask = sitkGetArrayViewFromImage(roi).flatten() > 0
            img = sitkGetArrayViewFromImage(slc).flatten()[mask]
            r = describe(img)
            # noinspection PyUnresolvedReferences
            stats['count'] = r.nobs
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            stats['median'] = median(img)
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['range'] = r.minmax[1] - r.minmax[0]
            stats['perc25'] = percentile(img, 25)
            stats['perc75'] = percentile(img, 75)
            # noinspection PyUnresolvedReferences
            stats['var'] = r.variance
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
        return stats

    def getShapeStatistics(self) -> list[dict[str, float]]:
        """
        Get the shape statistics of the SisypheROI image attribute.

        Returns
        -------
        dict[str, float]
            key (str)
                - 'count'
                - 'boundingbox'
                - 'centroid'
                - 'elongation'
                - 'flatness'
                - 'principalaxes'
                - 'principalmoments'
                - 'perimeter'
                - 'physicalsize'
                - 'feretdiameter'
                - 'ellipsoiddiameter'
                - 'sphericalperimeter'
                - 'sphericalradius'
        """
        stats = []
        if self.hasVolume() and self.hasROI():
            filtr = sitkLabelShapeStatisticsImageFilter()
            filtr.SetComputeFeretDiameter(True)
            filtr.SetComputePerimeter(True)
            img = sitkConnectedComponent(self._roi.getSITKImage())
            filtr.Execute(img)
            if filtr.GetNumberOfLabels() > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
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
    Description
    ~~~~~~~~~~~

    Extract features (descriptive statistics, shape, texture) from SisypheROI and SisypheVolume instance(s).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheROIFeatures

    Creation: 08/09/2022
    Last revision: 15/12/2023
    """

    __slots__ = ['_volume', '_rois', '_foTag', '_shTag', '_glcmTag',
                 '_glszmTag', '_glrlmTag', '_ngtdmTag', '_gldmTag', '_df']

    # Special method

    """
    Private attributes

    _volume     SisypheVolume
    _rois       SisypheROICollection
    _foTag      bool
    _shTag      bool
    _glcmTag    bool
    _glszmTag   bool
    _glrlmTag   bool
    _ngtdmTag   bool
    _gldmTag    boll
    _df         pandas.DataFrame    
    """

    def __init__(self,
                 vol: SisypheVolume | None = None,
                 rois: SisypheROICollection | None = None) -> None:
        """
        SisypheROIFeatures instance constructor.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        rois : SisypheROICollection
            ROI(s)
        """
        super().__init__()

        if vol is not None: self.setVolume(vol)
        else: self._volume = None

        if rois is not None: self.setROICollection(rois)
        else: self._rois = None

        self._foTag: bool = False
        self._shTag: bool = False
        self._glcmTag: bool = False
        self._glszmTag: bool = False
        self._glrlmTag: bool = False
        self._ngtdmTag: bool = False
        self._gldmTag: bool = False

        self._df: DataFrame | None = None

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheROIFeatures instance to str
        """
        if self._volume is not None: v = 'SisypheVolume instance at <{}>'.format(id(self._volume))
        else: v = 'None'
        if self._rois is not None: r = 'SisypheROICollection instance at <{}>'.format(id(self._rois))
        else: r = 'None'
        buff: str = 'Volume: {}\n'.format(v)
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
        """
         Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
        SisypheROIFeatures instance representation
        """
        return 'SisypheROIFeatures instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the reference SisypheVolume image attribute to the current SisypheROIFeatures instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            if self.hasROICollection() and len(self._rois) > 0:
                if self._rois[0].getReferenceID() != self._volume.getID(): self._rois = None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        """
        Get the reference SisypheVolume image attribute from the current SisypheROIFeatures instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        return self._volume

    def hasVolume(self) -> bool:
        """
        Check whether the reference SisypheVolume attribute of the current SisypheROIFeatures instance is defined
        (not None).

        Returns
        -------
        bool
            True if reference SisypheVolume attribute is defined
        """
        return self._volume is not None

    def setROICollectionFromLabelVolume(self, v: SisypheVolume) -> None:
        """
        Convert the SisypheVolume instance of labels to SisypheROI images added to a SisypheROICollection instance
        (see fromLabelVolume() docstrings of the SisypheROICollection class) and set it to the current
        SisypheROIFeatures instance.

        Parameters
        ----------
        v : Sisyphe.core.sisypheVolume.SisypheVolume
            label volume
        """
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self._rois = SisypheROICollection()
                self._rois.fromLabelVolume(v)
            else: raise ValueError('volume modality {} is not LB.'.format(v.acquisition.getModality()))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def setROICollection(self, rois: SisypheROICollection) -> None:
        """
        Set the SisypheROICollection attribute to the current SisypheROIFeatures instance. Same space as SisypheVolume
        attribute (same image size and spacing).

        Parameters
        ----------
        rois : SisypheROICollection
            roi collection to be processed
        """
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
        """
        Get the SisypheROICollection attribute from the current SisypheROIFeatures instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Returns
        -------
        SisypheROICollection
            roi collection to be processed
        """
        return self._rois

    def hasROICollection(self) -> bool:
        """
        Check whether the SisypheROICollection attribute of the current SisypheROIFeatures instance is defined
        (not None).

        Returns
        -------
        bool
            True if SisypheROICollection attribute is defined
        """
        return self._rois is not None

    def getDataFrame(self) -> DataFrame:
        """
        Get the pandas.DataFrame instance attribute of the current SisypheROIFeatures instance.

        Returns
        -------
        pandas.DataFrame
            DataFrame, table of features
        """
        return self._df

    def setFirstOrderTag(self, v: bool) -> None:
        """
        Enable/Disable the FirstOrder features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#radiomics.firstorder.RadiomicsFirstOrder

        FirstOrder features : energy, total energy, entropy, 10th percentile, 90th percentile, minimum, maximum, mean,
        median, interquartile range, range, mean absolute deviation, robust mean absolute deviation, root mean squared,
        standard deviation

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._foTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getFirstOrderTag(self) -> bool:
        """
        Get tag state of the FirstOrder features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._foTag

    def setShapeTag(self, v: bool) -> None:
        """
        Enable/Disable the Shape features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.shape

        Shape features : mesh volume, voxel volume, surface area, surface area to volume ratio, sphericity, compactness
        1 and 2, spherical disproportion, maximum 3D diameter, maximum 2D diameter (slice), maximum 2D diameter
        (column), maximum 2D diameter (row), major axis length, minor Axis Length, least axis Length, elongation,
        flatness, mesh Surface, pixel surface, perimeter, perimeter to surface ratio, sphericity, spherical
        disproportion, maximum 2D diameter, major axis length, minor axis length, elongation

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._shTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getShapeTag(self) -> bool:
        """
        Get tag state of the Shape features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._shTag

    def setGrayLevelCooccurrenceMatrixTag(self, v: bool) -> None:
        """
        Enable/Disable the GrayLevelCooccurrenceMatrix (GLCM) features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.glcm

        GLCM features : autocorrelation, joint average, cluster prominence, cluster shade, cluster tendency, contrast,
        correlation, difference average, difference entropy, difference variance, dissimilarity, joint energy, joint
        entropy, homogeneity 1 and 2, informational measure of correlation 1 and 2, inverse difference moment, maximal
        correlation coefficient, inverse difference moment normalized, inverse difference, inverse difference
        normalized, inverse variance, maximum probability, sum average, sum variance, sum entropy, sum of squares

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._glcmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelCooccurrenceMatrixTag(self) -> bool:
        """
        Get tag state of the GrayLevelCooccurrenceMatrix features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._glcmTag

    def setGrayLevelSizeZoneMatrixTag(self, v: bool) -> None:
        """
        Enable/Disable the GrayLevelSizeZoneMatrix (GLSZM) features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.glszm

        GLSZM features : small area emphasis, large area emphasis, gray level non-uniformity, gray level non-uniformity
        normalized, size-Zone non-uniformity, size-zone non-uniformity normalized, zone percentage, gray level
        variance, zone variance, zone entropy, low gray level zone emphasis, high gray level zone emphasis, small area
        low gray level emphasis, small area high gray level emphasis, large area low gray level emphasis, large area
        high gray level emphasis

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._glszmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelSizeZoneMatrixTag(self) -> bool:
        """
        Get tag state of the GrayLevelSizeZoneMatrix features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._glszmTag

    def setGrayLevelRunLengthMatrixTag(self, v: bool) -> None:
        """
        Enable/Disable the GrayLevelRunLengthMatrix (GLRLM) features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.glrlm

        GLRLM features : short run emphasis, long run emphasis, gray level non-uniformity, gray level non-uniformity
        normalized, run length non-uniformity, run length non-uniformity normalized, run percentage, gray level
        variance, run variance, run entropy, low gray level run emphasis, high gray level run emphasis, short run
        low gray level emphasis, short run high gray level emphasis, long run low gray level emphasis, long run high
        gray level emphasis

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._glrlmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelRunLengthMatrixTag(self) -> bool:
        """
        Get tag state of the GrayLevelRunLengthMatrix features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._glrlmTag

    def setNeighbouringGrayToneDifferenceMatrixTag(self, v: bool) -> None:
        """
        Enable/Disable the NeighbouringGrayToneDifferenceMatrix (NGTDM) features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.ngtdm

        NGTDM features : coarseness, contrast, busyness, complexity, strength

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._ngtdmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getNeighbouringGrayToneDifferenceMatrixTag(self) -> bool:
        """
        Get tag state of the NeighbouringGrayToneDifferenceMatrix features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._ngtdmTag

    def setGrayLevelDependenceMatrixTag(self, v: bool) -> None:
        """
        Enable/Disable the GrayLevelDependenceMatrix (GLDM) features.

        See https://pyradiomics.readthedocs.io/en/latest/features.html#module-radiomics.gldm

        GLDM features : small dependence emphasis, large dependence emphasis, gray level non-uniformity, gray level
        non-uniformity normalized, dependence non-uniformity, dependence non-uniformity normalized, gray level
        variance, dependence variance, dependence entropy, low gray level emphasis, high gray level emphasis, small
        dependence low gray level emphasis, small dependence high gray level emphasis, large dependence low gray level
        emphasis, large dependence high gray level emphasis

        Parameters
        ----------
        v : bool
            enabled if True
        """
        if isinstance(v, bool): self._gldmTag = v
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def getGrayLevelDependenceMatrixTag(self) -> bool:
        """
        Get tag state of the GrayLevelDependenceMatrix features.

        Returns
        -------
        bool
            True if enabled
        """
        return self._gldmTag

    def setAllTagsOn(self) -> None:
        """
        Enables all features.
        """
        self._foTag = True
        self._shTag = True
        self._glcmTag = True
        self._glszmTag = True
        self._glrlmTag = True
        self._ngtdmTag = True
        self._gldmTag = True

    # noinspection PyArgumentList
    def execute(self, progress: DialogWait | None = None) -> None:
        """
        Execute features calculation.

        List of calculated features enabled by tag methods :
            - setFirstOrderTag()
            - setGrayLevelCooccurrenceMatrixTag()
            - setGrayLevelSizeZoneMatrixTag()
            - setGrayLevelRunLengthMatrixTag()
            - setNeighbouringGrayToneDifferenceMatrixTag()
            - setGrayLevelDependenceMatrixTag()
            - setShapeTag()

        Feature results are set in the pandas.DataFrame instance attribute of the current SisypheROIFeatures instance.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasVolume() and self.hasROICollection():
            from Sisyphe.gui.dialogWait import DialogWait
            if not isinstance(progress, DialogWait): progress = None
            # noinspection PyUnresolvedReferences
            n: cython.int = len(self._rois)
            if n > 0:
                img = self._volume.getSITKImage()
                rows = self._rois.keys()
                cols = list()
                df = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
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
        """
        Save calculated features to a CSV file (.csv).

        Parameters
        ----------
        filename : str
            csv file name
        """
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.csv'
                self._df.to_csv(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')

    def saveToXLSX(self, filename: str) -> None:
        """
        Save calculated features to an Excel file (.xlsx).

        Parameters
        ----------
        filename : str
            Excel file name
        """
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.xlsx'
                self._df.to_excel(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')


class SisypheROIHistogram(object):
    """
    Description
    ~~~~~~~~~~~

    Extract histograms from SisypheROICollection instance.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheROIHistogram

    Creation: 08/09/2022
    Last revision: 15/12/2023
    """

    __slots__ = ['_volume', '_rois', '_bins', '_df']

    # Special method

    """
    Private attributes

    _volume     SisypheVolume
    _rois       SisypheROICollection
    _bins       int, histogram bins
    _df         pandas.DataFrame
    """

    def __init__(self,
                 vol: SisypheVolume | None = None,
                 rois: SisypheROICollection | None = None) -> None:
        """
        SisypheROIHistogram instance constructor.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        rois : SisypheROICollection
            ROI(s)
        """
        super().__init__()

        if vol is not None: self.setVolume(vol)
        else: self._volume = None

        if rois is not None: self.setROICollection(rois)
        else: self._rois = None

        # noinspection PyUnresolvedReferences
        self._bins: cython.int = 100
        self._df: DataFrame | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheROIHistogram instance to str
        """
        if self._volume is not None: v = 'SisypheVolume instance at <{}>'.format(id(self._volume))
        else: v = 'None'
        if self._rois is not None: r = 'SisypheROICollection instance at <{}>'.format(id(self._rois))
        else: r = 'None'
        buff: str = 'Volume: {}\n'.format(v)
        buff += 'ROICollection: {}\n'.format(r)
        buff += '  Bins: {}\n'.format(self._bins)
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheROIHistogram instance representation
        """
        return 'SisypheROIHistogram instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setVolume(self, volume: SisypheVolume) -> None:
        """
        Set the reference SisypheVolume image attribute to the current SisypheROIHistogram instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            if self.hasROICollection() and len(self._rois) > 0:
                if self._rois[0].getReferenceID() != self._volume.getID(): self._rois = None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self) -> SisypheVolume:
        """
        Get the reference SisypheVolume image attribute from the current SisypheROIHistogram instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        return self._volume

    def hasVolume(self) -> bool:
        """
        Check whether the reference SisypheVolume attribute of the current SisypheROIHistogram instance is defined
        (not None).

        Returns
        -------
        bool
            True if reference SisypheVolume attribute is defined
        """
        return self._volume is not None

    def setROICollectionFromLabelVolume(self, v: SisypheVolume) -> None:
        """
        Convert the SisypheVolume instance of labels to SisypheROI images added to a SisypheROICollection instance
        (see fromLabelVolume() docstrings of the SisypheROICollection class) and set it to the current
        SisypheROIHistogram instance.

        Parameters
        ----------
        v : Sisyphe.core.sisypheVolume.SisypheVolume
            label volume
        """
        if isinstance(v, SisypheVolume):
            if v.acquisition.isLB():
                self._rois = SisypheROICollection()
                self._rois.fromLabelVolume(v)
            else: raise ValueError('volume modality {} is not LB.'.format(v.acquisition.getModality()))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def setROICollection(self, rois: SisypheROICollection) -> None:
        """
        Set the SisypheROICollection attribute to the current SisypheROIHistogram instance. Same space as SisypheVolume
        attribute (same image size and spacing).

        Parameters
        ----------
        rois : SisypheROICollection
            roi collection to be processed
        """
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
        """
        Get the SisypheROICollection attribute from the current SisypheROIHistogram instance. Same space as
        SisypheROICollection attribute (same image size and spacing).

        Returns
        -------
        SisypheROICollection
            roi collection to be processed
        """
        return self._rois

    def hasROICollection(self) -> bool:
        """
        Check whether the SisypheROICollection attribute of the current SisypheROIHistogram instance is defined
        (not None).

        Returns
        -------
        bool
            True if SisypheROICollection attribute is defined
        """
        return self._rois is not None

    def setBins(self, v: int) -> None:
        """
        Set the histogram bins attribute of the current SisypheROIHistogram instance.

        Parameters
        ----------
        v : int
            number of bins in the histogram
        """
        if isinstance(v, int):
            if 2 <= v <= 256: self._bins = v
            else: raise ValueError('parameter value {} is not between 2 and 256.'.format(v))

    def getBins(self) -> int:
        """
        Get the histogram bins attribute of the current SisypheROIHistogram instance.

        Returns
        -------
        int
            number of bins in the histogram
        """
        return self._bins

    def getDataFrame(self) -> DataFrame:
        """
        Get the pandas.DataFrame instance attribute of the current SisypheROIFeatures instance.

        Returns
        -------
        pandas.DataFrame
            DataFrame histogram values
        """
        return self._df

    def getHistograms(self, roi: SisypheROI, norm: bool = False) -> tuple[DataFrame, DataFrame]:
        """
        Calculate the histograms of a SisypheROI instance.

        Parameters
        ----------
        roi : SisypheROI
            roi to be processed
        norm : bool
            histogram normalization if True (default False)

        Returns
        -------
        tuple[pandas.DataFrame, pandas.DataFrame]
            - histogram in the first pandas.DataFrame
            - cumulative histogram in the second pandas.DataFrame
        """
        if isinstance(roi, SisypheROI):
            if roi.getNumpy().sum() > 0:
                mask = roi.getNumpy().flatten() > 0
                img = self._volume.getNumpy().flatten()
                img = img[mask]
                # Histogram
                h, c = histogram(img, bins=self._bins)
                c2 = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
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
        """
        Execute histogram(s) calculation. Histogram results are set in the pandas.DataFrame instance attribute of the
        current SisypheROIFeatures instance.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasVolume() and self.hasROICollection():
            from Sisyphe.gui.dialogWait import DialogWait
            if not isinstance(progress, DialogWait): progress = None
            # noinspection PyUnresolvedReferences
            n: cython.int = len(self._rois)
            if n > 0:
                df = list()
                rows = self._rois.keys()
                img = self._volume.getNumpy().flatten()
                c2 = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(n):
                    name = self._rois[i].getName()
                    if progress is not None: progress.setInformationText('{} histogram.'.format(name))
                    mask = self._rois[i].getNumpy().flatten() > 0
                    roi = img[mask]
                    h, c = histogram(roi, bins=self._bins)
                    if i == 0:
                        for j in range(len(c) - 1):
                            c2.append((c[j] + c[j + 1]) / 2)
                    df.append(h)
                self._df = DataFrame(df, index=rows, columns=c2)
            else: raise AttributeError('ROI collection is empty.')
        else: raise AttributeError('Undefined volume or ROICollection.')

    def saveToCSV(self, filename: str) -> None:
        """
        Save calculated histogram(s) to a CSV file (.csv).

        Parameters
        ----------
        filename : str
            csv file name
        """
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.csv'
                self._df.to_csv(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')

    def saveToXLSX(self, filename: str) -> None:
        """
        Save calculated histogram(s) to an Excel file (.xlsx).

        Parameters
        ----------
        filename : str
            Excel file name
        """
        if self._df is not None:
            if isinstance(filename, str):
                filename = splitext(filename)[0] + '.xlsx'
                self._df.to_excel(filename)
            else: raise TypeError('parameter type {} is not str'.format(type(filename)))
        else: raise AttributeError('Dataframe is empty.')
