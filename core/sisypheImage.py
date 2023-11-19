"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            http://stnava.github.io/ANTs/                               Image registration
        ITK             https://itk.org/                                            Medical image processing
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        Scipy           https://docs.scipy.org                                      Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os.path import exists

import numpy as np
from numpy import iinfo
from numpy import can_cast
from numpy import array as np_array
from numpy import ndarray as np_ndarray
from numpy import copy as np_copy
from numpy import mean
from numpy import std
from numpy import median
from numpy import percentile
from numpy import transpose

from PyQt5.QtWidgets import QApplication

from scipy.stats import kurtosis
from scipy.stats import skew

from itk import Image as itkImage
from itk import GetImageFromArray as itkGetImageFromArray
from itk import GetImageViewFromArray as itkGetImageViewFromArray
from itk import GetArrayViewFromImage as itkGetArrayViewFromImage
from itk import GetMatrixFromArray as itkGetMatrixFromArray
from itk import GetArrayFromMatrix as itkGetArrayFromMatrix

from SimpleITK import sitkUInt8
from SimpleITK import sitkFloat32
from SimpleITK import Image as sitkImage
from SimpleITK import Cast as sitkCast
from SimpleITK import VectorIndexSelectionCastImageFilter as sitkVectorIndexSelectionCastImageFilter
from SimpleITK import ComposeImageFilter as sitkComposeImageFilter
from SimpleITK import GetImageFromArray as sitkGetImageFromArray
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage
from SimpleITK import BinaryNot as sitkBinaryNot
from SimpleITK import OtsuThreshold as sitkOtsu
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
from SimpleITK import OtsuThresholdImageFilter
from SimpleITK import HuangThresholdImageFilter
from SimpleITK import RenyiEntropyThresholdImageFilter
from SimpleITK import YenThresholdImageFilter
from SimpleITK import LiThresholdImageFilter
from SimpleITK import ShanbhagThresholdImageFilter
from SimpleITK import TriangleThresholdImageFilter
from SimpleITK import IntermodesThresholdImageFilter
from SimpleITK import MaximumEntropyThresholdImageFilter
from SimpleITK import KittlerIllingworthThresholdImageFilter
from SimpleITK import IsoDataThresholdImageFilter
from SimpleITK import MomentsThresholdImageFilter
from SimpleITK import BinaryDilate
from SimpleITK import BinaryErode
from SimpleITK import BinaryMorphologicalOpening
from SimpleITK import BinaryMorphologicalClosing
from SimpleITK import BinaryFillhole
from SimpleITK import BinaryFillholeImageFilter
from SimpleITK import ConnectedComponent as sitkConnectedComponent
from SimpleITK import RelabelComponent as sitkRelabelComponent

from vtk import VTK_UNSIGNED_CHAR
from vtk import vtkImageData
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray
from vtkmodules.util.numpy_support import numpy_to_vtk

from ants.core import ANTsImage
from ants.core import from_numpy as ants_from_numpy

import Sisyphe.core as sc
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.core.sisypheConstants import isValidDatatype
from Sisyphe.core.sisypheConstants import isValidLibraryName
from Sisyphe.core.sisypheConstants import isUint8ITKImage
from Sisyphe.core.sisypheConstants import isITKImageSupportedType
from Sisyphe.core.sisypheConstants import isITKSupportedStdType
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getVTKDirections
from Sisyphe.core.sisypheConstants import getIntStdDatatypes
from Sisyphe.core.sisypheConstants import getFloatStdDatatypes
from Sisyphe.core.sisypheImageIO import convertImageToAxialOrientation
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.core.sisypheImageIO import readImage
from Sisyphe.core.sisypheImageIO import readFromNIFTI
from Sisyphe.core.sisypheImageIO import readFromMINC
from Sisyphe.core.sisypheImageIO import readFromVTK
from Sisyphe.core.sisypheImageIO import readFromNRRD
from Sisyphe.core.sisypheImageIO import readFromNumpy
from Sisyphe.core.sisypheImageIO import readFromSisyphe
from Sisyphe.core.sisypheImageIO import readFromBrainVoyagerVMR
from Sisyphe.core.sisypheImageIO import writeToNIFTI
from Sisyphe.core.sisypheImageIO import writeToNRRD
from Sisyphe.core.sisypheImageIO import writeToMINC
from Sisyphe.core.sisypheImageIO import writeToVTK
from Sisyphe.core.sisypheImageIO import writeToJSON
from Sisyphe.core.sisypheImageIO import writeToNumpy

__all__ = ['numpyToVtkImageData',
           'simpleITKToVTK',
           'SisypheImage',
           'SisypheBinaryImage']

"""
    Functions
    
        numpyToVtkImageData(np: numpy.ndarray) -> vtk.vtkImageData
        simpleITKtoVTK(img: SimpleITK.Image) -> vtk.vtkImageData
        
    Revisions:
    
        31/08/2023  type hinting
        17/11/2023  docstrings
"""


def numpyToVtkImageData(np: np_ndarray) -> vtkImageData:
    """
        numpy ndarray to vtk.vtkImageData conversion

        Parameter

            np      numpy.ndarray

        return  vtk.vtkImageData
    """
    buff = np.view(np_ndarray)
    d = list(buff.shape)
    if len(d) == 2: d.append(1)
    buff.shape = buff.size
    data = numpy_to_vtk(buff)
    img = vtkImageData()
    img.SetDimensions(d[::-1])
    img.AllocateScalars(getLibraryDataType(str(np.dtype), 'vtk'), 1)
    img.GetPointData().SetScalars(data)
    return img

def simpleITKToVTK(img: sitkImage) -> vtkImageData:
    """
        SimpleITK.Image to vtk.vtkImageData conversion

        Parameter

            img     SimpleITK.Image

        return  vtk.vtkImageData
    """
    if isinstance(img, sitkImage):
        np = sitkGetArrayViewFromImage(img)
        vtkimg = numpyToVtkImageData(np)
        vtkimg.SetSpacing(img.GetSpacing())
        # Revision 15/04/2023
        # vtkimg.SetOrigin(img.GetOrigin())
        return vtkimg
    else: raise TypeError('parameter type {} is not SimpleITK image.'.format(type(img)))


"""
    Class hierarchy
    
        object -> SisypheImage -> SisypheBinaryImage   
"""

imageType2 = sitkImage | np_ndarray
imageType4 = imageType2 | vtkImageData | ANTsImage
vectorInt3Type = list[int, int, int] | tuple[int, int, int]
vectorFloat3Type = list[float, float, float] | tuple[float, float, float]

class SisypheImage(object):
    """
        SisypheImage class

        Description

            This class provides access to internal SimpleITK, ITK, VTK and numpy image classes,
            which share the same image buffer.

            Overloaded operators which work with int, float, SisypheVolume, SisypheImage, SimpleITK Image,
            and numpy array.

                Arithmetic  +, -, /, //, *
                Logic       & (and), | (or), ^ (xor), ~ (not)
                Relational  >, >=, <, <=, ==, !=

            Getter and Setter access to scalar values with slicing ability.

                Getter: v = instance_name[x, y, z]
                Setter: instance_name[x, y, z] = v
                x, y, z are int or pythonic slicing (i.e. python slice object, used the syntax first:last:step)

        Inheritance

            object -> SisypheImage

        Private attributes

            _sitk_image     sitkImage instance
            _vtk_image      vtkImageData instance
            _itk_image      itkImage instance
            _numpy_array    numpy instance

        Public methods

            __init__(image: str
                            | SimpleITK.Image
                            | vkt.vtkImageData
                            | ants.core.ANTSImage
                            | numpy.ndarray
                            | SisypheImage
                            | None = None,
                            **kargs)
            __str__() -> str
            __repr__() -> str
            __add__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __sub__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __mul__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __floordiv__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __truediv__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __radd__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __rsub__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __rmul__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __rfloordiv__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __rtruediv__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __neg__() -> SisypheImage
            __pos__() -> SisypheImage
            __and__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __rand__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __or__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __ror__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __xor__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __rxor__(other: SimpleITK.Image | numpy.ndarray | SisypheImage) -> SisypheImage
            __invert__() -> SisypheImage
            __lt__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __le__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __eq__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> bool | SisypheImage
            __ne__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> bool | SisypheImage
            __gt__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __ge__(other: SimpleITK.Image | numpy.ndarray | SisypheImage | int | float) -> SisypheImage
            __getitem__(idx)
            _setitem__(idx, value)
            hasITKImage() -> bool
            allocate(self, matrix: vectorInt3Type, datatype: str)
            copyFromSITKImage(img: SimpleITK.Image)
            copyFromVTKImage(img: vtk.vtkImageData)
            copyFromITKImage(img: itk.Image)
            copyFromANTSImage(img: ants.core.ANTsImage)
            copyFromNumpyArray(img: numpy.ndarray,
                               spacing: vectorFloat3Type = (1.0, 1.0, 1.0),
                               origin: vectorFloat3Type = (0.0, 0.0, 0.0),
                               direction: tuple | list = tuple(getRegularDirections()),
                               defaultshape: bool = True)
            copyToSITKImage() -> SimpleITK.Image
            copyToVTKImage() -> vtk.vtkImageData
            copyToITKImage() -> itk.Image
            copyToANTSImage(dtype: str = '', direction: bool = False) -> ants.core.ANTsImage
            copyToNumpyArray(defaultshape: bool = True) -> numpy.ndarray
            cast(datatype: str) -> tuple[SisypheImage, float, float]
            copy() -> SisypheImage
            copyComponent(c: int) -> SisypheImage
            getSITKImage() -> SimpleITK.Image
            setSITKImage(img: SimpleITK.Image)
            getITKImage() -> itk.Image
            getVTKImage() -> vtk.vtkImageData
            getNumpy(defaultshape: bool = True) -> numpy.ndarray
            getSize() -> vectorInt3Type
            getWidth() -> int
            getHeight() -> int
            getDepth() -> int
            (float, float, float) = getOrigin()
            setOrigin(tuple or list)
            setDefaultOrigin()
            setOriginToCenter()
            getSpacing() -> vectorFloat3Type
            setSpacing(sx: float, sy: float, sz: float)
            getVoxelVolume() -> float
            getNumberOfVoxels() -> int
            getNumberOfVoxelsInXYPlane() -> int
            getNumberOfVoxelsInXZPlane() -> int
            getNumberOfVoxelsInYZPlane() -> int
            isIsotropic(tol: float = 2.0) -> bool
            isAnisotropic(tol: float = 2.0) -> bool
            isThickAnisotropic(tol: float = 3.0) -> bool
            getNative2DOrientation() -> int
            getNative2DOrientationAsString() -> tuple[str, str | None]
            getCenter() -> vectorFloat3Type
            getFieldOfView() -> vectorFloat3Type
            hasSameFieldOfView(SisypheImage | SimpleITK.Image | vtk.vtkImageData | ants.core.ANTsImage) -> bool
            getDatatype() -> str
            getDatatypeAs(lib: str = 'sitk') -> str | int | None
            isIntegerDatatype() -> bool
            isUInt8Datatype() -> bool
            isInt8Datatype() -> bool
            isUInt16Datatype() -> bool
            isInt16Datatype()  -> bool
            isUInt32Datatype() -> bool
            isInt32Datatype() -> bool
            isUInt64Datatype() -> bool
            isInt64Datatype() -> bool
            isFloatDatatype() -> bool
            isFloat32Datatype() -> bool
            isFloat64Datatype() -> bool
            getNumberOfComponentsPerPixel() -> int
            getDirections() -> tuple
            setDirections(direction: list | tuple = tuple(getRegularDirections()))
            getFirstVectorDirection() -> vectorFloat3Type
            getSecondVectorDirection() -> vectorFloat3Type
            getThirdVectorDirection() -> vectorFloat3Type
            getMemorySize(rep: str = 'B') -> int | float
            setDefaultOrigin()
            SetOrigin(origin: vectorFloat3Type = (0.0, 0.0, 0.0))
            setOriginToCenter()
            getOrigin() -> vectorFloat3Type
            isDefaultOrigin() -> bool
            getWorldCoordinatesFromVoxelCoordinates(p: vectorFloat3Type) -> vectorFloat3Type
            getVoxelCoordinatesFromWorldCoordinates(p: vectorFloat3Type) -> vectorFloat3Type
            isEmpty() -> bool
            isEmptyArray() -> bool
            sliceIsEmpty(index: int, orient: int) -> bool
            getMask(algo: str = 'mean',
                    morpho: str = '',
                    niter: int = 1,
                    kernel: int = 0,
                    fill: str = '2d') -> SisypheImage
            getMask2(algo: str = 'mean',
                     morphoiter: int = 1,
                     kernel: int = 0) -> SisypheImage
            getMaskROI(algo: str = 'mean',
                       morpho: str = '',
                       niter: int = 1,
                       kernel: int = 0,
                       fill: str = '2d') -> SisypheImage
            getMaskROI2(algo: str = 'mean',
                        morphoiter: int = 1,
                        kernel: int = 0) -> SisypheImage
            getBackgroundThreshold(algo: str = 'mean') -> float
            getMean(mask: str | SisypheBinaryImage | None = None) -> float
            getStd(mask: str | SisypheBinaryImage | None = None) -> float
            getMin(nonzero: bool = False) -> float
            getMax() -> float
            getRange() -> tuple[float, float]
            getMedian(mask: str | SisypheBinaryImage | None = None) -> float
            getPercentile(perc: int = 25, mask: str | SisypheBinaryImage | None = None) -> float
            float = getKurtosis(mask: str | SisypheBinaryImage | None = None) -> float
            float = getSkewness(mask: str | SisypheBinaryImage | None = None) -> float
            getStatistics(mask: str | SisypheBinaryImage | None = None) -> dict[str, float]
            getNumberOfNonZero() -> int
            saveToNIFTI(filename: str = '', compress: bool = False)
            saveToNRRD(filename: str = '')
            saveToMINC(filename: str = '')
            saveToVTK(filename: str = '')
            saveToNumpy(filename: str = '')
            loafFromSisyphe(filename: str)
            loadFromBrainVoyagerVMR(filename: str)
            loadFromNIFTI(filename: str, reorient: bool = True)
            loadFromNRRD(filename: str)
            loadFromMINC(filename: str)
            loadFromVTK(filename: str)
            loadFromNumpy(filename: str)

        Creation: 12/01/2021
        Revisions:

            12/04/2023  add multicomponent nifi image support
            15/04/2023  origin attribute is no more copied in _vtk_image vtkImageData instance
                        (methods _updateVTKImageFromNumpy and setOrigin)
                        origin attribute is set after nifti, nrrd, minc, vtk load
                        origin is used to display world coordinates in viewport labels
            09/05/2023  add descriptive statistical methods
            09/06/2023  add arithmetic, logic and relational operators
            20/07/2023  add loadFromBrainVoyagerVMR IO method, open brainvoyager VMR file
            20/07/2023  descriptive statistics public methods, mask bugfix
            20/07/2023  add getNumberOfNonZero method
            25/07/2023  add getWorldCoordinatesFromVoxelCoordinates
                        add getVoxelCoordinatesFromWorldCoordinates
                        to convert world and voxel coordinates relative to origin and direction matrix
            07/08/2023  add getMaskROI() method
                        getMask(), changing fill parameter type to str ('2d', '3d' or '')
            11/08/2023  add sliceIsEmpty() method
            31/08/2023  type hinting
            10/11/2023  getNumpy(), copyToNumpyArray() and copyFromNumpyArray() methods
                        bugfix for 4D multicomponent volumes
            17/11/2023  docstrings
    """
    __slots__ = ['_sitk_image', '_itk_image', '_vtk_image', '_numpy_array']

    # Special methods

    def __init__(self, image: str | imageType4 | SisypheImage | None = None, **kargs) -> None:
        """
            SisypheImage instance constructor

            Parameters

                image   SisypheImage, SimpleITK.Image, vkt.vtkImageData,
                        ants.core.ANTSImage or numpy.ndarray instance

                kargs :
                    size        vectorFloat3Type
                    datatype    str
                    spacing     vectorFloat3Type
                    direction   vectorFloat9Type
        """

        # Init attributes (default, constructor without parameter)

        self._sitk_image = None
        self._itk_image = None
        self._vtk_image = None
        self._numpy_array = None

        # Init from image (filename, sitkImage, vtkImage, ANTSImage, numpy)

        if image is not None:
            # Init from SisypheImage
            if isinstance(image, (SisypheImage, SisypheBinaryImage)):
                image = image._sitk_image
            # Init from filename
            if isinstance(image, str):
                if exists(image): image = readImage(image)
                else: raise IOError('No such file {}.'.format(image))
            # Init from sitkImage
            if isinstance(image, sitkImage):
                self.copyFromSITKImage(image)
            # Init from vtkImage
            elif isinstance(image, vtkImageData):
                self.copyFromVTKImage(image)
            # Init from ANTSImage
            elif isinstance(image, ANTsImage):
                self.copyFromANTSImage(image)
            # Init from numpy
            elif isinstance(image, np_ndarray):
                self.copyFromNumpyArray(image)  # default numpy array shape (z, y, x)
                if 'spacing' in kargs.keys():
                    spacing = kargs['spacing']
                    self.setSpacing(spacing[0], spacing[1], spacing[2])
                if 'direction' in kargs.keys():
                    self.setDirections(kargs['direction'])
            else: raise TypeError('constructor image parameter type {} not supported.'.format(type(image)))

        # Init new image from kargs dict parameters

        else:
            if len(kargs) > 0:
                if 'size' in kargs.keys():
                    matrix = kargs['size']
                else: matrix = (128, 128, 128)
                if 'datatype' in kargs.keys():
                    datatype = getLibraryDataType(kargs['datatype'], 'sitk')
                else:
                    datatype = getLibraryDataType('uint16', 'sitk')
                if 'spacing' in kargs.keys():
                    spacing = kargs['spacing']
                else: spacing = (1.0, 1.0, 1.0)
                if 'origin' in kargs.keys():
                    origin = kargs['origin']
                else: origin = (0.0, 0.0, 0.0)
                if 'direction' in kargs.keys():
                    direction = kargs['direction']
                else: direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
                self._sitk_image = sitkImage(matrix, datatype)
                self._sitk_image.SetSpacing(spacing)
                self._sitk_image.SetOrigin(origin)
                self._sitk_image.SetDirection(direction)
                self._updateImages()

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheImage instance to str
         """
        buff = 'Image attributes:\n' \
               '\tSize: {0[0]} x {0[1]} x {0[2]} x {1}\n' \
               '\tDatatype: {2}\n' \
               '\tSpacing: {3[0]:.2f} {3[1]:.2f} {3[2]:.2f}\n' \
               '\tOrigin: {4[0]:.1f} {4[1]:.1f} {4[2]:.1f}\n' \
               '\tDirections:\n' \
               '\t{5[0]:.1f} {5[1]:.1f} {5[2]:.1f}\n' \
               '\t{5[3]:.1f} {5[4]:.1f} {5[5]:.1f}\n' \
               '\t{5[6]:.1f} {5[7]:.1f} {5[8]:.1f}\n'.format(self.getSize(),
                                                             self.getNumberOfComponentsPerPixel(),
                                                             self.getDatatype(),
                                                             self.getSpacing(),
                                                             self.getOrigin(),
                                                             self.getDirections())
        m = self.getMemorySize('B')
        mb = 1024 * 1024
        if m < 1024: buff += '\tMemory Size: {} B\n'.format(m)
        elif m < mb: buff += '\tMemory Size: {:.2f} KB\n'.format(m / 1024)
        else: buff += '\tMemory Size: {:.2f} MB\n'.format(m / mb)
        return buff

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheImage instance representation
        """
        return 'SisypheImage instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Arithmetic operators

    def __add__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator +.
            self + other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__add__(other))

    def __sub__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator -.
            self - other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__sub__(other))

    def __mul__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator *.
            self * other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__mul__(other))

    def __div__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__div__(other))

    def __floordiv__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator //.
            self // other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__floordiv__(other))

    def __truediv__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator /.
            self / other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__truediv__(other))

    def __radd__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator +.
            other + self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__radd__(other))

    def __rsub__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator -.
            other - self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rsub__(other))

    def __rmul__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator *.
            other * self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rmul__(other))

    def __rdiv__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator /.
            other / self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rdiv__(other))

    def __rfloordiv__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator //.
            other // self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rfloordiv__(other))

    def __rtruediv__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded arithmetic operator /.
            other / self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rtruediv__(other))

    def __neg__(self) -> SisypheImage:
        """
            Special overloaded arithmetic unary operator -.
            - self -> SisypheImage

            return  SisypheImage
        """
        return SisypheImage(self._sitk_image.__neg__())

    def __pos__(self) -> SisypheImage:
        """
            Special overloaded arithmetic unary operator +.
            + self -> SisypheImage

            return  SisypheImage
        """
        return self

    # Logic operators

    def __and__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator & (and).
            self & other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__and__(other))

    def __rand__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator & (and).
            other & self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rand__(other))

    def __or__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator | (or).
            self | other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__or__(other))

    def __ror__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator | (or).
            other | self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ror__(other))

    def __xor__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator ^ (xor).
            self ^ other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__xor__(other))

    def __rxor__(self, other: imageType2 | SisypheImage) -> SisypheImage:
        """
            Special overloaded logic operator ^ (xor).
            other ^ self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rxor__(other))

    def __invert__(self) -> SisypheImage:
        """
            Special overloaded logic unary operator ~ (not).
            ~self -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage

            return  SisypheImage
        """
        return SisypheImage(self._sitk_image.__invert__())

    # Relational operators

    def __lt__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded relational operator <.
            self < other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__lt__(other))

    def __le__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded relational operator <=.
            self <= other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__le__(other))

    def __eq__(self, other: imageType2 | SisypheImage | int | float) -> bool | SisypheImage:
        """
            Special overloaded relational operator ==.
            self == other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): return id(self) == id(other)
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__eq__(other))

    def __ne__(self, other: imageType2 | SisypheImage | int | float) -> bool | SisypheImage:
        """
            Special overloaded relational operator !=.
            self != other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): return id(self) != id(other)
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ne__(other))

    def __gt__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded relational operator >.
            self > other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__gt__(other))

    def __ge__(self, other: imageType2 | SisypheImage | int | float) -> SisypheImage:
        """
            Special overloaded relational operator >=.
            self >= other -> SisypheImage

            Parameter

                other   SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float

            return  SisypheImage
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ge__(other))

    # set/get pixel methods

    def __getitem__(self, idx):
        """
            Special overloaded container getter method.
            Get scalar value(s) with slicing ability.
            syntax: v = instance_name[x, y, z]

            Parameter

                idx     vectorInt3Type,     x, y, z int indexes
                        | slice,            pythonic slicing (i.e. python slice object,
                                            used the syntax first:last:step)

            return  int | float | SisypheImage
        """
        r = self._sitk_image.__getitem__(idx)
        if isinstance(r, sitkImage): r = SisypheImage(r)
        return r

    def __setitem__(self, idx, rvalue):
        """
            Special overloaded container setter method.
            Set scalar value(s) with slicing ability.
            syntax: instance_name[x, y, z] = rvalue

            Parameter

                idx     vectorInt3Type,     x, y, z int indexes
                        | slice,            pythonic slicing (i.e. python slice object,
                                            used the syntax first:last:step)

                rvalue  int | float | SisypheImage
        """
        if isinstance(rvalue, SisypheImage): rvalue = rvalue.getSITKImage()
        else: rvalue = self._toSimpleITK(rvalue)
        self._sitk_image.__setitem__(idx, rvalue)

    # Private methods

    def _toSimpleITK(self, img: ANTsImage | np_ndarray | int | float) -> sitkImage | int | float:
        if isinstance(img, ANTsImage): img = img.view().T
        if isinstance(img, np_ndarray):
            img = sitkGetImageFromArray(img)
            img.SetSpacing(self.getSpacing())
        return img

    def _updateImages(self) -> None:
        self._updateNumpyFromSITKImage()
        self._updateITKImageFromNumpy()
        self._updateVTKImageFromNumpy()

    def _updateNumpyFromSITKImage(self) -> None:
        # GetArrayViewFromImage() return default numpy array shape (z, y, x)
        buff = sitkGetArrayViewFromImage(self._sitk_image)
        self._numpy_array = buff.copy().T  # image shape (x, y, z)
        self._numpy_array.data = buff.data
        self._numpy_array = self._numpy_array.T  # default shape (z, y, x)

    def _updateVTKImageFromNumpy(self) -> None:
        # default numpy array shape (z, y, x)
        buff = self._numpy_array.view(np_ndarray)
        buff.shape = buff.size
        data = numpy_to_vtk(buff)
        self._vtk_image = vtkImageData()
        sz = self._sitk_image.GetSize()
        sp = self._sitk_image.GetSpacing()
        if len(sz) == 2:
            sz = (sz[0], sz[1], 1)
            sp = (sp[0], sp[1], 1.0)
        self._vtk_image.SetDimensions(sz)
        self._vtk_image.SetSpacing(sp)
        # Revision 15/04/2023
        # self._vtk_image.SetOrigin(self._sitk_image.GetOrigin())
        self._vtk_image.AllocateScalars(getLibraryDataType(str(self._numpy_array.dtype), 'vtk'),
                                        self._sitk_image.GetNumberOfComponentsPerPixel())
        self._vtk_image.GetPointData().SetScalars(data)

    def _updateITKImageFromNumpy(self) -> None:
        if isITKSupportedStdType(self.getDatatype()) and self.getNumberOfComponentsPerPixel() == 1:
            # GetImageViewFromArray() array parameter must have default shape (z, y, x)
            self._itk_image = itkGetImageViewFromArray(self._numpy_array)
            self._itk_image.SetOrigin(self._sitk_image.GetOrigin())
            self._itk_image.SetSpacing(self._sitk_image.GetSpacing())
            d = np_array(self._sitk_image.GetDirection())
            if d.size == 4: d = d.reshape(2, 2)
            elif d.size == 9: d = d.reshape(3, 3)
            buff = itkGetMatrixFromArray(d)
            self._itk_image.SetDirection(buff)
        else:
            self._itk_image = None

    # Public methods

    def hasITKImage(self) -> bool:
        """
            Checks whether itk.Image attribute is available.

            return  bool, True if itk.Image attribute is available (not None)
        """
        return self._itk_image is not None

    def allocate(self, matrix: vectorInt3Type, datatype: str) -> None:
        """
            Initialize image buffer.

            Parameters

                matrix      vectorInt3Type, array size in x, y, z dimensions
                datatype    str, numpy datatype
        """
        if isinstance(matrix, (list, tuple)) and len(matrix) == 3:
            if isValidDatatype(datatype):
                self._sitk_image = sitkImage(matrix, getLibraryDataType(datatype, 'sitk'))
                self._updateImages()
            else: raise ValueError('string parameter is not a correct datatype.')
        else: raise TypeError('matrix parameter is not a list of 3 int.')

    def copyFromSITKImage(self, img: sitkImage) -> None:
        """
            Copy SimpleITK image buffer to current instance.

            Parameter

                img     SimpleITK.Image
        """
        if isinstance(img, sitkImage):
            self._sitk_image = sitkImage(img)
            self._updateImages()
        else: raise TypeError('parameter type {} is not SimpleITK.'.format(type(img)))

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        """
            Copy VTK image buffer to current instance.

            Parameter

                img     vtk.vtkImageData
        """
        if isinstance(img, vtkImageData):
            r = vtkImageExportToArray()
            r.SetInputData(img)
            buff = r.GetArray()
            # default numpy array shape (z, y, x)
            self.copyFromNumpyArray(buff, img.GetSpacing(), img.GetOrigin(), getRegularDirections())
            self._updateImages()
        else: raise TypeError('parameter type {} is not vtkImageData class.'.format(type(img)))

    def copyFromITKImage(self, img: itkImage) -> None:
        """
            Copy ITK image buffer to current instance.

            Parameter

                img     itk.Image
        """
        if isITKImageSupportedType(img):
            # GetArrayViewFromImage() return default numpy array shape (z, y, x)
            buff = itkGetArrayViewFromImage(img)
            d = tuple(itkGetArrayFromMatrix(img.GetDirection()).flatten())
            self.copyFromNumpyArray(buff, tuple(img.GetSpacing()), tuple(img.GetOrigin()), d)
            self._updateImages()
        else: raise TypeError('parameter type {} is not itkImage class or itktype is not supported.'.format(type(img)))

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        """
            Copy ANTs image buffer to current instance.

            Parameter

                img     ants.core.ANTsImage
        """
        if isinstance(img, ANTsImage):
            # ANTsImage.view() return numpy array with image shape (x, y, z)
            # transpose to get default numpy array shape (z, y, z)
            buff = img.view().T
            d = list(img.direction.flatten())
            self.copyFromNumpyArray(buff, img.spacing, img.origin, d)
            self.setDirections()
        else: raise TypeError('parameter type {} is not ANTsImage class.'.format(type(img)))

    def copyFromNumpyArray(self,
                           img: np_ndarray,
                           spacing: vectorFloat3Type = (1.0, 1.0, 1.0),
                           origin: vectorFloat3Type = (0.0, 0.0, 0.0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True) -> None:
        """
             Copy Numpy array buffer to current instance.

             Parameter

                 img             numpy.ndarray
                 spacing         vectorFloat3Type, voxel sizes in mm (default 1.0, 1.0, 1.0)
                 origin          vectorFloat3Type, origin coordinates (default 0.0, 0.0, 0.0)
                 direction       vectorFloat9Type, axes directions
                 defaultshape    bool, if True, numpy shape order is reversed (i.e. z, y, x)
        """
        if isinstance(img, np_ndarray):
            if img.ndim == 3:
                """
                    native shape = (z, y, x)
                    defaultshape = True  if numpy shape is (z, y, x)
                                 = False if numpy shape is (x, y, z)
                """
                if defaultshape: self._sitk_image = sitkGetImageFromArray(img)
                else: self._sitk_image = sitkGetImageFromArray(img.T)
            elif img.ndim == 4:
                """
                    native shape = (z, y, x, n)
                    defaultshape = True  if numpy shape is (n, z, y, x)
                                 = False if numpy shape is (x, y, z, n)
                """
                if defaultshape: self._sitk_image = sitkGetImageFromArray(transpose(img, axes=(1, 2, 3, 0)))
                else: self._sitk_image = sitkGetImageFromArray(transpose(img, axes=(2, 1, 0, 3)))
            else: raise ValueError('{}D ndarray is not supported.'.format(img.ndim))
            self._sitk_image.SetSpacing(spacing)
            self._sitk_image.SetDirection(direction)
            self._sitk_image.SetOrigin(origin)
            self._updateImages()
        else: raise TypeError('parameter type {} is not numpy ndarray.'.format(type(img)))

    def copyToSITKImage(self) -> sitkImage:
        """
            SimpleITK image copy of the current SisypheImage instance.

            return SimpleITK.Image
        """
        if not self.isEmpty():
            return sitkImage(self._sitk_image)
        else: raise ValueError('SisypheImage array is empty.')

    def copyToVTKImage(self) -> vtkImageData:
        """
            VTK image copy of the current SisypheImage instance.

            return vtk.vtkImageData
        """
        if not self.isEmpty():
            buff = vtkImageData()
            buff.DeepCopy(self._vtk_image)
            return buff
        else: raise ValueError('SisypheImage array is empty.')

    def copyToITKImage(self) -> itkImage:
        """
            ITK image copy of the current SisypheImage instance.

            return itk.Image
        """
        if not self.isEmpty():
            # GetImageFromArray() array parameter must have default shape (z, y, x)
            buff = itkGetImageFromArray(self._numpy_array)
            buff.SetOrigin(self._sitk_image.GetOrigin())
            buff.SetSpacing(self._sitk_image.GetSpacing())
            d = itkGetMatrixFromArray(np_array(self._sitk_image.GetDirection()).reshape(3, 3))
            buff.SetDirection(d)
            return buff
        else: raise ValueError('SisypheImage array is empty.')

    def copyToANTSImage(self, dtype: str = '', direction: bool = False) -> ANTsImage:
        """
            ANTs image copy of the current SisypheImage instance.

            return ants.core.ANTSImage
        """
        if not self.isEmpty():
            data = self._numpy_array.T
            t = ('unit8', 'uint32', 'float32', 'float64')
            if self.getDatatype() not in t or dtype != '':
                if dtype in t: data = data.astype(dtype)
                else: data = data.astype('float32')
            # ants_from_numpy() array parameter must have image shape (x, y, z)
            # transpose to get default numpy array shape (z, y, z)
            d = np_array(self._sitk_image.GetDirection()).reshape((3, 3))
            img = ants_from_numpy(data, self._sitk_image.GetOrigin(), self._sitk_image.GetSpacing(), d)
            # set direction to LPI
            if direction:
                d = img.direction
                d[0, 0] = -1
                d[1, 1] = -1
                img.set_direction(d)
            return img
        else: raise ValueError('SisypheImage array is empty.')

    def copyToNumpyArray(self, defaultshape: bool = True) -> np_ndarray:
        """
            Numpy array copy of the current SisypheImage instance.

            return numpy.ndarray
        """
        # Numpy array deep copy
        if not self.isEmpty():
            if self._numpy_array.ndim == 3:
                """
                    3D volume
                    native shape = (z, y, x)
                    defaultshape = True  -> return shape (z, y, x)
                                 = False -> return shape (x, y, z)   
                """
                if defaultshape: return np_copy(self._numpy_array)
                else: return self._numpy_array.T
            elif self._numpy_array.ndim == 4:
                """
                    4D multicomponent volume, n components
                    native shape = (z, y, x, n)
                    defaultshape = True  -> return shape (n, z, y, x)
                                 = False -> return shape (x, y, z, n)   
                """
                if defaultshape: return transpose(self._numpy_array, axes=(3, 0, 1, 2))
                else: return transpose(self._numpy_array, axes=(2, 1, 0, 3))
        else: raise ValueError('SisypheImage array is empty.')

    def cast(self, datatype: str) -> tuple[SisypheImage, float, float]:  # recode with SimpleITK Clamp
        """
            SisypheImage copy of the current SisypheImage instance with a new datatype.

            Parameter

                datatype    str, numpy datatype

            return  tuple[SisypheImage, slope: float, intercept: float]
                    linear transform: casted value = slope * original value + intercept
                    linear transform is applied if direct cast is not possible (overflow error)
        """
        if not self.isEmpty():
            if datatype == str(self._numpy_array.dtype):
                return SisypheImage(self._sitk_image), 1.0, 0.0
            else:
                if can_cast(str(self._numpy_array.dtype), datatype, 'same_kind'):
                    img = sitkCast(self._sitk_image, getLibraryDataType(datatype, 'sitk'))
                    return SisypheImage(image=img), 1.0, 0.0
                else:
                    slope = 1
                    tmax = iinfo(datatype).max
                    vmax = self._numpy_array.max()
                    vmin = self._numpy_array.min()
                    if vmax - vmin < tmax:
                        buff = sitkCast(self._sitk_image, sitkFloat32) - vmin
                    else:
                        islope = tmax / (vmax - vmin)
                        buff = (sitkCast(self._sitk_image, sitkFloat32) - vmin) * islope
                        slope = 1 / islope
                    buff = sitkCast(buff, getLibraryDataType(datatype, 'sitk'))
                    img = SisypheImage(image=buff)
                    return img, slope, vmin
        else: raise ValueError('SisypheImage array is empty.')

    def copy(self) -> SisypheImage:
        """
            SisypheImage copy of the current SisypheImage instance.

            return SisypheImage
        """
        if not self.isEmpty(): return SisypheImage(self._sitk_image)
        else: raise ValueError('SisypheImage array is empty.')

    def copyComponent(self, c: int) -> SisypheImage:
        """
            Extract single-component SisypheImage from the
            current multi-component SisypheImage instance.

            return SisypheImage
        """
        n = self.getNumberOfComponentsPerPixel()
        if n > 1:
            if isinstance(c, int):
                f = sitkVectorIndexSelectionCastImageFilter()
                f.SetIndex(c)
                return SisypheImage(f.Execute(self.getSITKImage()))
            else: raise TypeError('parameter type {} is not int.'.format(type(c)))
        else: raise ValueError('Image has only one component.')

    def getSITKImage(self) -> sitkImage:
        """
            Shallow copy of the current SisypheImage instance SimpleITK attribute.

            return SimpleITK.Image
        """
        if not self.isEmpty(): return self._sitk_image
        else: raise ValueError('SisypheImage array is empty.')

    def setSITKImage(self, img: sitkImage) -> None:
        """
            Shallow copy of a SimpleITK Image to the SimpleITK Image
            attribute of the current SisypheImage instance.

            Parameter

                img     SimpleITK.Image
        """
        if isinstance(img, sitkImage):
            self._sitk_image = img
            self._updateImages()
        else: raise TypeError('parameter type {} is not sitkImage.'.format(type(img)))

    def getVTKImage(self) -> vtkImageData:
        """
            Shallow copy of the current SisypheImage instance VTK Image attribute.

            return vtk.vtkImageData
        """
        if not self.isEmpty(): return self._vtk_image
        else: raise ValueError('SisypheImage array is empty.')

    def getITKImage(self: vtkImageData):
        """
            Shallow copy of the current SisypheImage instance ITK Image attribute.

            return itk.Image
        """
        if not self.isEmpty(): return self._itk_image
        else: raise ValueError('SisypheImage array is empty.')

    def getNumpy(self, defaultshape: bool = True) -> np_ndarray:
        """
            Shallow copy of the current SisypheImage instance numpy array attribute.

            return numpy.ndarray
        """
        # Numpy array shallow copy
        if not self.isEmpty():
            if self._numpy_array.ndim == 3:
                """
                    3D volume
                    defaultshape = True  -> return shape (z, y, x)
                                 = False -> return shape (x, y, z)
                """
                if defaultshape: return self._numpy_array
                else: return self._numpy_array.T
            elif self._numpy_array.ndim == 4:
                """
                    4D multicomponent volume, n components
                    native shape = (z, y, x, n)
                    defaultshape = True  -> return shape (n, z, y, x)
                                 = False -> return shape (x, y, z, n)   
                """
                if defaultshape: return transpose(self._numpy_array, axes=(3, 0, 1, 2))
                else: return transpose(self._numpy_array, axes=(2, 1, 0, 3))
        else: raise ValueError('SisypheImage array is empty.')

    def getSize(self) -> vectorInt3Type:
        """
            Get array size, i.e. voxel count in each dimension.

            return  vectorInt3Type, array size in x, y, z dimensions
        """
        if not self.isEmpty():
            r = self._sitk_image.GetSize()
            if len(r) == 2: r = (r[0], r[1], 1)
            return r
        else: return 0, 0, 0

    def getWidth(self) -> int:
        """
            Get array size in x.

            return  int, voxel count in x
        """
        return self.getSITKImage().GetWidth()

    def getHeight(self) -> int:
        """
            Get array size in y.

            return  int, voxel count in y
        """
        return self.getSITKImage().GetHeight()

    def getDepth(self) -> int:
        """
            Get array size in z.

            return  int, voxel count in z
        """
        r = self.getSITKImage().GetDepth()
        if r == 0: r = 1
        return r

    def getSpacing(self) -> vectorFloat3Type:
        """
            Get voxel size (mm) in each dimension.

            return  vectorFloat3Type, voxel spacing in x, y, z
        """
        if not self.isEmpty():
            r = self._sitk_image.GetSpacing()
            if len(r) == 2: r = (r[0], r[1], 1.0)
            return r
        else: return 0.0, 0.0, 0.0

    def setSpacing(self, sx: float, sy: float, sz: float) -> None:
        """
            Set voxel size (mm) in each dimension.

            Parameters

                sx  float, voxel spacing in x
                sy  float, voxel spacing in y
                sz  float, voxel spacing in x
        """
        self._sitk_image.SetSpacing((sx, sy, sz))
        self._vtk_image.SetSpacing(sx, sy, sz)
        if self.hasITKImage():
            self._itk_image.SetSpacing((sx, sy, sz))

    def getVoxelVolume(self) -> float:
        """
            Get voxel volume in mm3

            return  float, voxel volume in mm3
        """
        sx, sy, sz = self.getSpacing()
        return sx * sy * sz

    def getNumberOfVoxels(self) -> int:
        """
            Get voxel count in the array.

            return  int, voxel count
        """
        s = self.getSize()
        return s[0] * s[1] * s[2]

    def getNumberOfVoxelsInXYPlane(self) -> int:
        """
            Get voxel count in axial slice.

            return  int, voxel count
        """
        s = self.getSize()
        return s[0] * s[1]

    def getNumberOfVoxelsInXZPlane(self) -> int:
        """
            Get voxel count in coronal slice.

            return  int, voxel count
        """
        s = self.getSize()
        return s[0] * s[2]

    def getNumberOfVoxelsInYZPlane(self) -> int:
        """
            Get voxel count in sagittal slice.

            return  int, voxel count
        """
        s = self.getSize()
        return s[1] * s[2]

    def isIsotropic(self, tol: float = 2.0) -> bool:
        """
            Check whether voxel is isotropic, i.e. same spacing in each dimension
            A tolerance is applied: max(spacing) / min(spacing) < tol

            Parameter

                tol float, tolerance (default 2.0)

            return  bool, True if max(spacing) / min(spacing) < tol
        """
        if isinstance(tol, float):
            s = list(self.getSpacing())
            s.sort()
            return (s[2] / s[0]) < tol
        else: raise TypeError('parameter type {} is not float.'.format(type(tol)))

    def isAnisotropic(self, tol: float = 2.0) -> bool:
        """
            Check whether voxel is anisotropic, i.e. not same spacing in each dimension
            A tolerance is applied: max(spacing) / min(spacing) > tol

            Parameter

                tol float, tolerance (default 2.0)

            return  bool, True if max(spacing) / min(spacing) > tol
        """
        return not self.isIsotropic(tol)

    def isThickAnisotropic(self, tol: float = 3.0) -> bool:
        """
            Check whether voxel is anisotropic or thickness > tol
            Tolerance applied for anisotropy: max(spacing) / min(spacing) > tol

            Parameter

                tol float, tolerance (default 2.0)

            return  bool, True if max(spacing) / min(spacing) > tol or max(spacing) > tol
        """
        s = list(self.getSpacing())
        s.sort()
        return (s[2] / s[0]) >= tol or s[2] >= tol

    def getNative2DOrientation(self) -> int:
        """
            Get code of the native orientation
            (0 3D, 1 axial, 2 coronal, 3 sagittal).

            return  int, code of the native orientation
        """
        if self.isAnisotropic():
            s = self.getSpacing()
            return 3 - s.index(max(s))
        else: return 0  # Unspecified or 3D

    def getNative2DOrientationAsString(self) -> tuple[str, str | None]:
        """
            Get the native orientation as str

            return  tuple[mode, orient]
                    mode    str, '2D' or '3D'
                    orient  str, 'Axial', 'Coronal' or 'Sagittal'
        """
        r = self.getNative2DOrientation()
        if r == 0: return '3D', None
        elif r == 1: return '2D', 'Axial'
        elif r == 2: return '2D', 'Coronal'
        else: return '2D', 'Sagittal'

    def getCenter(self) -> vectorFloat3Type:
        """
            Get center of the volume as world coordinates

            return vectorFloat3Type, center of the volume
        """
        d = self.getSize()
        s = self.getSpacing()
        return ((d[0] - 1) * s[0] * 0.5,
                (d[1] - 1) * s[1] * 0.5,
                (d[2] - 1) * s[2] * 0.5)
        # return tuple([(d[i] - 1) * s[i] * 0.5 for i in range(3)])

    def getFieldOfView(self) -> vectorFloat3Type:
        """
            Get field of view of the volume.

            return vectorFloat3Type, field of view
        """
        if not self.isEmpty():
            matrix = self._sitk_image.GetSize()
            spacing = self._sitk_image.GetSpacing()
            return (matrix[0] * spacing[0],
                    matrix[1] * spacing[1],
                    matrix[2] * spacing[2])
        else: return 0.0, 0.0, 0.0

    def hasSameFieldOfView(self, img: SisypheImage | imageType) -> bool:
        """
            Compare field of view between current SisypheImage instance and other image.

            Parameter

                img     SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage

            return bool, True if same field of view
        """
        s, m = 0, 0
        if isinstance(img, SisypheImage):
            s = np_array(img.getSpacing())
            m = np_array(img.getSize())
        elif isinstance(img, sitkImage):
            s = np_array(img.GetSpacing())
            m = np_array(img.GetSize())
        elif isinstance(img, vtkImageData):
            s = np_array(img.GetSpacing())
            m = np_array(img.GetDimensions())
        elif isinstance(img, ANTsImage):
            s = np_array(img.spacing)
            m = np_array(img.shape)
        space = s * m
        return all(space == self.getFieldOfView())

    def getDatatype(self) -> str:
        """
            Get datatype (numpy format)

            return  str, datatype (numpy format)
        """
        if not self.isEmpty(): return str(self._numpy_array.dtype)
        else: return 'None'

    def isIntegerDatatype(self) -> bool:
        """
            Check whether datatype is integer
            ('uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64' or 'int64')

            return  bool, True if integer datatype
        """
        return self.getDatatype() in getIntStdDatatypes()

    def isUInt8Datatype(self) -> bool:
        """
            Check whether datatype is uint8

            return  bool, True if uint8 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[0]

    def isInt8Datatype(self) -> bool:
        """
            Check whether datatype is int8

            return  bool, True if int8 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[1]

    def isUInt16Datatype(self) -> bool:
        """
            Check whether datatype is uint16

            return  bool, True if uint16 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[2]

    def isInt16Datatype(self) -> bool:
        """
            Check whether datatype is int16

            return  bool, True if int16 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[3]

    def isUInt32Datatype(self) -> bool:
        """
            Check whether datatype is uint32

            return  bool, True if uint32 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[4]

    def isInt32Datatype(self) -> bool:
        """
            Check whether datatype is int32

            return  bool, True if int32 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[5]

    def isUInt64Datatype(self) -> bool:
        """
            Check whether datatype is uint64

            return  bool, True if uint64 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[6]

    def isInt64Datatype(self) -> bool:
        """
            Check whether datatype is int64

            return  bool, True if int64 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[7]

    def isFloatDatatype(self) -> bool:
        """
            Check whether datatype is float ('float32' or 'float64')

            return  bool, True if float datatype
        """
        return self.getDatatype() in getFloatStdDatatypes()

    def isFloat32Datatype(self) -> bool:
        """
            Check whether datatype is float32

            return  bool, True if float32 datatype
        """
        return self.getDatatype() == getFloatStdDatatypes()[0]

    def isFloat64Datatype(self) -> bool:
        """
            Check whether datatype is float64

            return  bool, True if float64 datatype
        """
        return self.getDatatype() == getFloatStdDatatypes()[1]

    def getDatatypeAs(self, lib: str = 'sitk') -> str | int | None:
        """
            Get datatype with the library format of ANTs, SimpleITK, ITK or VTK.

            Parameters

                lib         str | int, library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
                                       library code (i.e. ants=0, itk=1, sitk=2, vtk=3)

            return  str | int, datatype
        """
        if isValidLibraryName(lib):
            if not self.isEmpty(): return getLibraryDataType(str(self._numpy_array.dtype), lib)
            else: return None
        else: raise ValueError('parameter {} is not a valid library name.'.format(lib))

    def getNumberOfComponentsPerPixel(self) -> int:
        """
            Get number of components.
            Scalar image has a single component.
            Array element of multi-component image is a vector,
            the number of components is the vector element count.

            return  int, number of components
        """
        if not self.isEmpty(): return self._sitk_image.GetNumberOfComponentsPerPixel()
        else: return 0

    def getDirections(self) -> tuple:
        """
            Get vectors of image axes in RAS+ coordinates system.
            PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
            Directions is a list of 9 float, 3 vectors of 3 floats
            First vector, x image axis direction, [1.0, 0.0, 0.0]
            Second vector, y image axis direction, [0.0, 1.0, 0.0]
            Third vector, y image axis direction, [0.0, 0.0, 1.0]

            return  vectorFloat9Type, vectors of image axes
        """
        if not self.isEmpty():
            r = self._sitk_image.GetDirection()
            if len(r) == 4: r = (r[0], r[1], 0.0, r[2], r[3], 0.0, 0.0, 0.0, 1.0)
            return r
        else: return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    def getFirstVectorDirection(self) -> vectorFloat3Type:
        """
            Get first direction vector, x image axis in RAS+ coordinates system.
            PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
            Directions is a list of 9 float, 3 vectors of 3 floats
            First vector, x image axis direction, [1.0, 0.0, 0.0]
            Second vector, y image axis direction, [0.0, 1.0, 0.0]
            Third vector, y image axis direction, [0.0, 0.0, 1.0]

            return  vectorFloat3Type, vector of the x image axis
        """
        if not self.isEmpty(): return self._sitk_image.GetDirection()[0:3]
        else: return 0.0, 0.0, 0.0

    def getSecondVectorDirection(self) -> vectorFloat3Type:
        """
            Get second direction vector, y image axis in RAS+ coordinates system.
            PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
            Directions is a list of 9 float, 3 vectors of 3 floats
            First vector, x image axis direction, [1.0, 0.0, 0.0]
            Second vector, y image axis direction, [0.0, 1.0, 0.0]
            Third vector, y image axis direction, [0.0, 0.0, 1.0]

            return  vectorFloat3Type, vector of the y image axis
        """
        if not self.isEmpty(): return self._sitk_image.GetDirection()[3:6]
        else: return 0.0, 0.0, 0.0

    def getThirdVectorDirection(self) -> vectorFloat3Type:
        """
            Get second direction vector, z image axis in RAS+ coordinates system.
            PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
            Directions is a list of 9 float, 3 vectors of 3 floats
            First vector, x image axis direction, [1.0, 0.0, 0.0]
            Second vector, y image axis direction, [0.0, 1.0, 0.0]
            Third vector, y image axis direction, [0.0, 0.0, 1.0]

            return  vectorFloat3Type, vector of the z image axis
        """
        if not self.isEmpty(): return self._sitk_image.GetDirection()[6:]
        else: return 0.0, 0.0, 0.0

    def setDirections(self, direction: list | tuple = tuple(getRegularDirections())) -> None:
        """
            Set vectors of image axes in RAS+ coordinates system.
            PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
            Directions is a list of 9 float, 3 vectors of 3 floats
            First vector, x image axis direction, [1.0, 0.0, 0.0]
            Second vector, y image axis direction, [0.0, 1.0, 0.0]
            Third vector, y image axis direction, [0.0, 0.0, 1.0]

            Parameter

                direction  vectorFloat9Type, vectors of image axes
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(direction)
            if self.hasITKImage():
                d = np_array(self._sitk_image.GetDirection())
                if d.size == 4: d = d.reshape(2, 2)
                elif d.size == 9: d = d.reshape(3, 3)
                buff = itkGetMatrixFromArray(d)
                self._itk_image.SetDirection(buff)

    def getMemorySize(self, rep: str = 'B') -> int | float:
        """
            Get the memory size of the current SisypheImage instance.

            Parameter

                rep     str, memory unit
                             'B' Bytes
                             'KB' Kilobytes
                             'MB' Megabytes

            return  int,        if rep == 'B'
                    | float,    if rep in ('KB', 'MB')
        """
        if not self.isEmpty():
            m = self._numpy_array.size * self._numpy_array.dtype.itemsize
            if rep == 'B':
                # Bytes
                return m
            elif rep == 'KB':
                # Kilo Bytes
                return m / 1024
            elif rep == 'MB':
                # Mega Bytes
                return m / (1024 * 1024)
        else:
            return 0.0

    def setDefaultOrigin(self) -> None:
        """
            Set geometrical reference origin coordinates to (0.0, 0.0, 0.0)
        """
        self.setOrigin()

    def setOrigin(self, origin: vectorFloat3Type = (0.0, 0.0, 0.0)) -> None:
        """
            Set geometrical reference origin coordinates.

            Parameter

                origin  vectorFloat3Type, world coordinates origin
        """
        if not self.isEmpty():
            if self._sitk_image.GetDepth() == 2: origin = origin[:2]
            self._sitk_image.SetOrigin(origin)
            # Revision 15/04/2023
            # self._vtk_image.SetOrigin(origin)
            if self.hasITKImage():
                self._itk_image.SetOrigin(origin)

    def setOriginToCenter(self) -> None:
        """
            Set geometrical reference origin coordinates to image center.
        """
        self.setOrigin(self.getCenter())

    def getOrigin(self) -> vectorFloat3Type:
        """
            Get geometrical reference origin coordinates.

            return  vectorFloat3Type, world coordinates origin
        """
        if not self.isEmpty():
            r = self._sitk_image.GetOrigin()
            if len(r) == 2: r = (r[0], r[1], 0.0)
            return r
        else: return 0.0, 0.0, 0.0

    def isDefaultOrigin(self) -> bool:
        """
            Check whether geometrical reference origin coordinates is (0.0, 0.0, 0.0).

            return  bool, True if world coordinates origin is (0.0, 0.0, 0.0)
        """
        return self.getOrigin() == (0.0, 0.0, 0.0)

    def getWorldCoordinatesFromVoxelCoordinates(self, p: vectorFloat3Type) -> vectorFloat3Type:
        """
            Convert voxel grid coordinates to world coordinates

            Parameter

                p   vectorFloat3Type, voxel grid coordinates

            return  vectorFloat3Type, world coordinates
        """
        return self._sitk_image.TransformIndexToPhysicalPoint(p)

    def getVoxelCoordinatesFromWorldCoordinates(self, p: vectorFloat3Type) -> vectorFloat3Type:
        """
            Convert world coordinates to voxel grid coordinates

            Parameter

                p   vectorFloat3Type, world coordinates

            return  vectorFloat3Type, voxel grid coordinates
        """
        return self._sitk_image.TransformPhysicalPointToIndex(p)

    def isEmpty(self) -> bool:
        """
            Check whether image buffer is allocated.

            return  bool, True if image buffer is allocated
        """
        return self._sitk_image is None

    def isEmptyArray(self) -> bool:
        """
            Check whether image is empty i.e. all scalar values in the image array are 0.0.

            return  bool, True if image is empty
        """
        return self.isEmpty() or self.getNumpy().sum() == 0

    def sliceIsEmpty(self, index: int, orient: int) -> bool:
        """
            Check whether a slice is empty i.e. all scalar values in the slice array are 0.0.

            Parameter

                index   int, slice index
                orient  int, orientation code (0 axial, 1 coronal, 2 sagittal)

            return  bool, True if slice is empty
        """
        if isinstance(index, int): index = [index]
        # Axial
        if orient == 0:
            for i in index:
                if self.getNumpy()[i, :, :].sum() != 0: return False
            return True
        # Coronal
        elif orient == 1:
            for i in index:
                if self.getNumpy()[:, i, :].sum() != 0: return False
            return True
        # Sagittal
        else:
            for i in index:
                if self.getNumpy()[:, :, i].sum() != 0: return False
            return True

    def getMask(self,
                algo: str = 'mean',
                morpho: str = '',
                niter: int = 1,
                kernel: int = 0,
                fill: str = '2d') -> SisypheImage:
        """
            Calc SisypheImage mask of the head.

            parameters

                algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        Automatic thresholding algorithm used for background segmentation.
                morpho  str in ['dilate', 'erode', 'open', 'close', ''], binary morphology operator
                niter   int, number of binary morphology iterations
                kernel  int, structuring element size
                fill    str in ['2d', '3d', '']
                        '2d', fill holes slice by slice
                        '3d', fill holes in 3D
                        '', no filling

            return  SisypheImage, mask
        """
        # Segment background
        algo = algo.lower()
        if algo == 'mean':
            v = self.getNumpy().mean()
            img = (self.getSITKImage() <= v)
        elif algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        elif algo == 'yen': img = sitkYen(self.getSITKImage())
        elif algo == 'li': img = sitkLi(self.getSITKImage())
        elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
        QApplication.processEvents()
        # mask = not( background )
        img = sitkBinaryNot(img)
        # Morphology operator
        if isinstance(kernel, int):
            if kernel > 0 and morpho in ('dilate', 'erode', 'open', 'close'):
                morpho = morpho.lower()
                for i in range(niter):
                    if morpho == 'dilate': img = BinaryDilate(img, [kernel, kernel, kernel])
                    elif morpho == 'erode': img = BinaryErode(img, [kernel, kernel, kernel])
                    elif morpho == 'open':
                        img = BinaryMorphologicalOpening(img, [kernel, kernel, kernel])
                        break
                    elif morpho == 'close':
                        img = BinaryMorphologicalClosing(img, [kernel, kernel, kernel])
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
            img = BinaryFillhole(img)
            QApplication.processEvents()
        return SisypheImage(img)

    def getMask2(self,
                 algo: str = 'huang',
                 morphoiter: int = 2,
                 kernel: int = 0) -> SisypheImage:
        """
            Calc SisypheImage mask of the head.

            parameters

                algo        str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                    'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                            Automatic thresholding algorithm used for background segmentation.
                morphoiter  int, number of binary morphology iterations
                kernel      int, structuring element size
                            0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)

            return  SisypheImage
        """
        # Segment background
        algo = algo.lower()
        if algo == 'mean':
            v = self.getNumpy().mean()
            img = (self.getSITKImage() <= v)
        elif algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        elif algo == 'yen': img = sitkYen(self.getSITKImage())
        elif algo == 'li': img = sitkLi(self.getSITKImage())
        elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
        QApplication.processEvents()
        # Background processing
        if isinstance(kernel, int):
            if kernel == 0:
                if max(self.getSpacing()) < 1.5: kernel = 2
                else: kernel = 1
            # Erode
            if morphoiter > 0:
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
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
                    img = BinaryDilate(img, [kernel, kernel, kernel])
                    QApplication.processEvents()
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        # Object = not( background )
        img = sitkBinaryNot(img)
        # Object processing
        if isinstance(kernel, int):
            # Erode
            if morphoiter > 0:
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
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
                    img = BinaryDilate(img, [kernel, kernel, kernel])
                    QApplication.processEvents()
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        return SisypheImage(img)

    def getMaskROI(self,
                   algo: str = 'mean',
                   morpho: str = '',
                   niter: int = 1,
                   kernel: int = 0,
                   fill: str = '2d') -> sc.sisypheROI.SisypheROI:
        """
            Calc Sisyphe.sisypheROI.SisypheROI mask of the head.

            parameters

                algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        Automatic thresholding algorithm used for background segmentation.
                morpho  str in ['dilate', 'erode', 'open', 'close', ''], binary morphology operator
                niter   int, number of binary morphology iterations
                kernel  int, structuring element size
                fill    str in ['2d', '3d', '']
                        '2d', fill holes slice by slice
                        '3d', fill holes in 3D
                        '', no filling

            return  Sisyphe.sisypheROI.SisypheROI
        """
        # Segment background
        algo = algo.lower()
        fill = fill.lower()
        if algo == 'mean':
            v = self.getNumpy().mean()
            img = (self.getSITKImage() <= v)
        elif algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        elif algo == 'yen': img = sitkYen(self.getSITKImage())
        elif algo == 'li': img = sitkLi(self.getSITKImage())
        elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
        QApplication.processEvents()
        # mask = not( background )
        img = sitkBinaryNot(img)
        # Morphology operator
        if isinstance(kernel, int):
            if kernel > 0 and morpho in ('dilate', 'erode', 'open', 'close'):
                morpho = morpho.lower()
                for i in range(niter):
                    if morpho == 'dilate': img = BinaryDilate(img, [kernel, kernel, kernel])
                    elif morpho == 'erode': img = BinaryErode(img, [kernel, kernel, kernel])
                    elif morpho == 'open':
                        img = BinaryMorphologicalOpening(img, [kernel, kernel, kernel])
                        break
                    elif morpho == 'close':
                        img = BinaryMorphologicalClosing(img, [kernel, kernel, kernel])
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
            img = BinaryFillhole(img)
            QApplication.processEvents()
        return sc.sisypheROI.SisypheROI(img)

    def getMaskROI2(self,
                    algo: str = 'huang',
                    morphoiter: int = 2,
                    kernel: int = 0) -> sc.sisypheROI.SisypheROI:
        """
            Calc Sisyphe.sisypheROI.SisypheROI mask of the head.

            parameters

                algo        str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                    'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                            Automatic thresholding algorithm used for background segmentation.
                morphoiter  int, number of binary morphology iterations
                kernel      int, structuring element size
                                 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)

            return  Sisyphe.sisypheROI.SisypheROI
        """
        # Segment background
        algo = algo.lower()
        if algo == 'mean':
            v = self.getNumpy().mean()
            img = (self.getSITKImage() <= v)
        elif algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        elif algo == 'yen': img = sitkYen(self.getSITKImage())
        elif algo == 'li': img = sitkLi(self.getSITKImage())
        elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
        QApplication.processEvents()
        # Background processing
        if isinstance(kernel, int):
            if kernel == 0:
                if max(self.getSpacing()) < 1.5: kernel = 2
                else: kernel = 1
            # Erode
            if morphoiter > 0:
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
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
                    img = BinaryDilate(img, [kernel, kernel, kernel])
                    QApplication.processEvents()
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        # Object = not( background )
        img = sitkBinaryNot(img)
        # Object processing
        if isinstance(kernel, int):
            # Erode
            if morphoiter > 0:
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
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
                    img = BinaryDilate(img, [kernel, kernel, kernel])
                    QApplication.processEvents()
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))

        return sc.sisypheROI.SisypheROI(img)

    def getBackgroundThreshold(self, algo: str = 'mean') -> float:
        """
            Calc threshold to segment background.

            parameters

                algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        Automatic thresholding algorithm

            return  float, threshold to segment background
        """
        algo = algo.lower()
        if algo == 'mean': return self.getNumpy().mean()
        elif algo == 'otsu': f = OtsuThresholdImageFilter()
        elif algo == 'huang': f = HuangThresholdImageFilter()
        elif algo == 'renyi': f = RenyiEntropyThresholdImageFilter()
        elif algo == 'yen': f = YenThresholdImageFilter()
        elif algo == 'li': f = LiThresholdImageFilter()
        elif algo == 'shanbhag': f = ShanbhagThresholdImageFilter()
        elif algo == 'triangle': f = TriangleThresholdImageFilter()
        elif algo == 'intermodes': f = IntermodesThresholdImageFilter()
        elif algo == 'maximumentropy': f = MaximumEntropyThresholdImageFilter()
        elif algo == 'kittler': f = KittlerIllingworthThresholdImageFilter()
        elif algo == 'isodata': f = IsoDataThresholdImageFilter()
        elif algo == 'moments': f = MomentsThresholdImageFilter()
        else: raise ValueError('{} unknown algorithm parameter.'.format(algo))
        if f is not None:
            try:
                f.Execute(self.getSITKImage())
                return f.GetThreshold()
            except: return self.getNumpy().mean()

    # Descriptive statistics public methods

    def getMean(self, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get mean of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, mean value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return mean(img)

    def getStd(self, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get standard deviation of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, standard deviation value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return std(img)

    def getMin(self, nonzero: bool = False) -> float:
        """
            Get min of the image scalars values.
            Calculation can only be performed on non-zero values.

            Parameter

                nonzero     bool, exclude non-zero values if True

            return      float, min value
        """
        img = self.getNumpy().flatten()
        if nonzero: img = img[img > 0]
        return img.min()

    def getMax(self) -> float:
        """
            Get max of the image scalars values.
            Calculation can only be performed on non-zero values.

            return      float, max value
        """
        return self.getNumpy().flatten().max()

    def getRange(self) -> tuple[float, float]:
        """
            Get range (min, max) of the image scalars values.

            Parameter

                nonzero     bool, exclude non-zero values if True

            return      tuple[float, float], (min, max) values
        """
        img = self.getNumpy().flatten()
        return img.min(), img.max()

    def getMedian(self, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get median of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, median value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return median(img)

    def getPercentile(self, perc: int = 25, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get percentile of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                perc    int, percentile value (default is 25, first quartile)
                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, percentile value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return percentile(img, perc)

    def getKurtosis(self, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get kurtosis of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, kurtosis value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str) and mask != '':
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return kurtosis(img)

    def getSkewness(self, mask: str | SisypheBinaryImage | None = None) -> float:
        """
            Get skewness of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      float, skewness value
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str) and mask != '':
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        return skew(img)

    def getStatistics(self, mask: str | SisypheBinaryImage | None = None) -> dict[str, float]:
        """
            Get descriptive statistics of the image scalars values.
            Calculation is performed on the entire image (mask parameter = None) or in a mask.

            Parameter

                mask    str, automatic thresholding algorithm used for background segmentation
                             str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                     'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        | SisypheBinaryImage, binary mask image
                        | None, no mask, calculation is performed on the entire image

            return      dict[key, value]
                        key, str        value, float
                        'mean'      value, mean
                        'std'       value, standard deviation
                        'min'       value, minimum
                        'p25'       value, first quartile
                        'median'    value, median
                        'p75'       value, third quartile
                        'max'       value, maximum
                        'kurtosis'  value, kurtosis
                        'skewness'  value, skewness
        """
        img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str) and mask != '':
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        r = dict()
        r['mean'] = mean(img)
        r['std'] = std(img)
        r['min'] = img.min()
        r['p25'] = percentile(img, 25)
        r['median'] = median(img)
        r['p75'] = percentile(img, 75)
        r['max'] = img.max()
        r['kurtosis'] = kurtosis(img)
        r['skewness'] = skew(img)
        return r

    def getNumberOfNonZero(self) -> int:
        """
            Get number of non-zero scalar values in image.

            return  int, number of non-zero scalar values
        """
        img = self.getNumpy().flatten()
        return len(img[img > 0])

    # IO public methods

    def saveToNIFTI(self, filename: str = '', compress: bool = False) -> None:
        """
            Save current SisypheImage instance to a file in Nifti format.

            Parameter

                filename    str, Nifti file name
                compress    bool, gzip compression if True
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToNIFTI(self._sitk_image, filename, compress)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToNRRD(self, filename: str = '') -> None:
        """
            Save current SisypheImage instance to a file in Nrrd format.

            Parameter

                filename    str, Nrrd file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToNRRD(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToMINC(self, filename: str = '') -> None:
        """
            Save current SisypheImage instance to a file in Minc format.

            Parameter

                filename    str, Minc file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToMINC(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else:
            raise ValueError('SisypheImage array is empty.')

    def saveToVTK(self, filename: str = '') -> None:
        """
            Save current SisypheImage instance to a file in VTK format.

            Parameter

                filename    str, VTK file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToVTK(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else:
            raise ValueError('SisypheImage array is empty.')

    def saveToJSON(self, filename: str = '') -> None:
        """
            Save current SisypheImage instance to a file in Json format.

            Parameter

                filename    str, Json file name
        """
        if not self.isEmpty():
            writeToJSON(self._sitk_image, filename)
        else: raise ValueError('SisypheImage array is empty.')

    def saveToNumpy(self, filename: str = '') -> None:
        """
            Save current SisypheImage instance to a file in numpy format.

            Parameter

                filename    str, numpy file name
        """
        if not self.isEmpty():
            writeToNumpy(self._sitk_image, filename)
        else:
            raise ValueError('SisypheImage array is empty.')

    def loadFromSisyphe(self, filename: str) -> dict:
        """
            Load image in current SisypheImage instance from old Sisyphe binary file.

            Parameter

                filename    str, old Sisyphe binary file name

            return dict, Old Sisyphe header
                        (see Sisyphe.sisypheImageIO.loadFromSisyphe
                        docstring for keys and values documentation)
        """
        img, hdr = readFromSisyphe(filename)
        img = flipImageToVTKDirectionConvention(img)
        img = convertImageToAxialOrientation(img)[0]
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        self.setOrigin()
        return hdr

    def loadFromBrainVoyagerVMR(self, filename: str) -> dict:
        """
            Load image in current SisypheImage instance from BrainVoyager file.

            Parameter

                filename    str, BrainVoyager file name
        """
        img, hdr = readFromBrainVoyagerVMR(filename)
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        self.setOrigin()
        return hdr

    def loadFromNIFTI(self, filename: str, reorient: bool = True) -> None:
        """
            Load image in current SisypheImage instance from Nifti file.

            Parameter

                filename    str, BrainVoyager file name
                reorient    bool, conversion to RAS+ world coordinates convention if True
        """
        img = readFromNIFTI(filename)
        imgs = list()
        s = img.GetSize()
        origin = [abs(i) for i in img.GetOrigin()]
        # Multicomponent sitk image ?
        # Copy each component to a single component sitk image
        if len(s) == 3: imgs.append(img)
        elif len(s) == 4 and s[3] > 1:
            for i in range(s[3]):
                imgs.append(img[:, :, :, i])
        # Reorientation of each sitk single component image
        p = None
        for i in range(len(imgs)):
            if reorient:
                imgs[i] = flipImageToVTKDirectionConvention(imgs[i])
                imgs[i], p = convertImageToAxialOrientation(imgs[i])
            imgs[i].SetDirection(getRegularDirections())
        # Rebuild multicomponent sitk image
        if len(imgs) == 1: img = imgs[0]
        else:
            f = sitkComposeImageFilter()
            img = f.Execute(imgs)
        # Set multicomponent sitk image to self SisypheVolume instance
        self.setSITKImage(img)
        # Revision 15/04/2023
        # self.setOrigin()
        if p is not None: origin = [origin[i] for i in p]
        self.setOrigin(origin)

    def loadFromNRRD(self, filename: str) -> None:
        """
            Load image in current SisypheImage instance from Nrrd file.

            Parameter

                filename    str, Nrrd file name
        """
        img = readFromNRRD(filename)
        img = flipImageToVTKDirectionConvention(img)
        img = convertImageToAxialOrientation(img)[0]
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        # Revision 15/04/2023
        # self.setOrigin()
        self.setOrigin(img.GetOrigin())

    def loadFromMINC(self, filename: str) -> None:
        """
            Load image in current SisypheImage instance from Minc file.

            Parameter

                filename    str, Minc file name
        """
        img = readFromMINC(filename)
        img = flipImageToVTKDirectionConvention(img)
        img = convertImageToAxialOrientation(img)[0]
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        # Revision 15/04/2023
        # self.setOrigin()
        self.setOrigin(img.GetOrigin())

    def loadFromVTK(self, filename: str) -> None:
        """
            Load image in current SisypheImage instance from VTK file.

            Parameter

                filename    str, VTK file name
        """
        img = readFromVTK(filename)
        img = flipImageToVTKDirectionConvention(img)
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        # Revision 15/04/2023
        # self.setOrigin()
        self.setOrigin(img.GetOrigin())

    def loadFromNumpy(self, filename: str) -> None:
        """
            Load image in current SisypheImage instance from numpy file.

            Parameter

                filename    str, numpy file name
        """
        self.setSITKImage(readFromNumpy(filename))
        self.setOrigin()


class SisypheBinaryImage(SisypheImage):
    """
        SisypheBinaryImage class

        Description

            Specialized SisypheImage class with unsigned short datatype.

        Inheritance

            object -> SisypheImage -> SisypheBinaryImage

        Public methods

            __init__(image: str
                            | SimpleITK.Image
                            | vkt.vtkImageData
                            | ants.core.ANTSImage
                            | numpy.ndarray
                            | SisypheImage
                            | None = None,
                     copy: bool = True,
                     **kargs)
            copyFromSITKImage(img: SimpleITK.Image)
            copyFromVTKImage(img: vtk.vtkImageData)
            copyFromITKImage(img: itk.Image)
            copyFromANTSImage(img: ants.core.ANTsImage)
            copyFromNumpyArray(img: numpy.ndarray,
                               spacing: vectorFloat3Type = (1.0, 1.0, 1.0),
                               origin: vectorFloat3Type = (0.0, 0.0, 0.0),
                               direction: tuple | list = tuple(getRegularDirections()),
                               defaultshape: bool = True)
            setSITKImage(img: SimpleITK.Image)

            inherited SisypheImage class

        Creation: 12/01/2021
        Revision:

            03/08/2023  copyFromVTKImage() bugfix, replace scalar type VTK_CHAR with VTK_UNSIGNED_CHAR
            31/08/2023  type hinting
            16/11/2°23  docstrings
    """
    __slots__ = []

    # Special methods

    def __init__(self, image: str | imageType4 | SisypheImage | None = None, copy: bool = True, **kargs) -> None:
        """
            SisypheBinaryImage instance constructor

            Parameters

                image   SisypheImage, SimpleITK.Image, vkt.vtkImageData,
                        ants.core.ANTSImage or numpy.ndarray instance

                copy    bool, True copy image to SisypheBinaryImage if datatype is unit8
                              False create only a new SisypheBinaryImage with the same image geometry
                              (size, spacing, origin, orientation)

                kargs :
                    size        vectorFloat3Type
                    datatype    str
                    spacing     vectorFloat3Type
                    direction   vectorFloat9Type
        """
        if image is None:
            kargs['datatype'] = 'uint8'
        else:
            # SisypheImage / SisypheVolume
            if isinstance(image, SisypheImage):
                kargs['size'] = image.getSize()
                kargs['datatype'] = 'uint8'
                kargs['spacing'] = image.getSpacing()
                kargs['origin'] = image.getOrigin()
                kargs['direction'] = image.getDirections()
                image = None
            # sitkImage
            elif isinstance(image, sitkImage):
                if image.GetPixelID() != sitkUInt8 or not copy:
                    kargs['size'] = image.GetSize()
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.GetSpacing()
                    kargs['origin'] = image.GetOrigin()
                    kargs['direction'] = image.GetDirection()
                    image = None
            # vtkImageData
            elif isinstance(image, vtkImageData):
                if image.GetScalarType() != VTK_CHAR or not copy:
                    kargs['size'] = image.GetDimensions()
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.GetSpacing()
                    image = None
            # ANTsImage
            elif isinstance(image, ANTsImage):
                if image.pixeltype != 'unsigned char':
                    kargs['size'] = image.shape
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.spacing
                    kargs['direction'] = tuple(list(np_array(image.direction).flatten()))
                    image = None
            # ITKImage
            elif not isUint8ITKImage(image):
                kargs['size'] = tuple(image.GetLargestPossibleRegion().GetSize())
                kargs['datatype'] = 'uint8'
                kargs['spacing'] = image.GetSpacing()
                kargs['direction'] = tuple(itkGetArrayFromMatrix(image.GetDirection()).flatten())
                image = None
            # Numpy
            elif isinstance(image, np_ndarray):
                if image.dtype != 'uint8' or not copy:
                    image = None

        super().__init__(image, **kargs)

        if self.getDatatype() != 'uint8':
            raise TypeError('image parameter type {} is not uint8.'.format(self.getDatatype()))

    def __str__(self) -> str:
        """
             Special overloaded method called by the built-in str() python function.

             return  str, conversion of SisypheBinaryImage instance to str
         """
        buff = 'Size: {0[0]} x {0[1]} x {0[2]}\n' \
               'Spacing: {1[0]:.2f} {1[1]:.2f} {1[2]:.2f}\n' \
               'Origin: {2[0]:.1f} {2[1]:.1f} {2[2]:.1f}\n' \
               'Directions:\n' \
               '{3[0]:.1f} {3[1]:.1f} {3[2]:.1f}\n' \
               '{3[3]:.1f} {3[4]:.1f} {3[5]:.1f}\n ' \
               '{3[6]:.1f} {3[7]:.1f} {3[8]:.1f}\n'.format(self.getSize(),
                                                           self.getSpacing(),
                                                           self.getOrigin(),
                                                           self.getDirections())
        m = self.getMemorySize('B')
        mb = 1024 * 1024
        if m < 1024: buff += 'Memory Size: {} B\n'.format(m)
        elif m < mb: buff += 'Memory Size: {:.2f} KB\n'.format(m / 1024)
        else: buff += 'Memory Size: {:.2f} MB\n'.format(m / mb)
        return buff

    def __repr__(self) -> str:
        """
            Special overloaded method called by the built-in repr() python function.

            return  str, SisypheBinaryImage instance representation
        """
        return 'SisypheBinaryImage instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def copyFromSITKImage(self, img: sitkImage) -> None:
        """
            Copy SimpleITK image buffer to current instance.

            Parameter

                img     SimpleITK.Image
        """
        if isinstance(img, sitkImage):
            if img.GetPixelID() == sitkUInt8:
                super().copyFromSITKImage(img)
            else: raise TypeError('SimpleITK image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not SimpleITK image class.')

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        """
            Copy VTK image buffer to current instance.

            Parameter

                img     vtk.vtkImageData
        """
        if isinstance(img, vtkImageData):
            if img.GetScalarType() == VTK_UNSIGNED_CHAR:
                super().copyFromVTKImage(img)
            else: raise TypeError('VTK image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not VTK image class.')

    def copyFromITKImage(self, img: itkImage) -> None:
        """
            Copy ITK image buffer to current instance.

            Parameter

                img     itk.Image
        """
        if isUint8ITKImage(img):
            super().copyFromITKImage(img)
        else: raise TypeError('image parameter datatype is not uint8 ITK image class.')

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        """
            Copy ANTs image buffer to current instance.

            Parameter

                img     ants.core.ANTsImage
        """
        if isinstance(img, ANTsImage):
            if img.pixeltype != 'unsigned char':
                super().copyFromANTSImage(img)
            else: raise TypeError('ANTs image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not ANTs Image class.')

    def copyFromNumpyArray(self,
                           img: np_ndarray,
                           spacing: vectorFloat3Type = (1.0, 1.0, 1.0),
                           origin: vectorFloat3Type = (0.0, 0.0, 0.0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True):
        """
            Copy Numpy array buffer to current instance.

            Parameter

                img             numpy.ndarray
                spacing         vectorFloat3Type, voxel sizes in mm (default 1.0, 1.0, 1.0)
                origin          vectorFloat3Type, origin coordinates (default 0.0, 0.0, 0.0)
                direction       vectorFloat9Type, axes directions
                defaultshape    bool, if True, numpy shape order is reversed (i.e. z, y, x)
            """
        if isinstance(img, np_ndarray):
            if img.dtype == 'uint8':
                super().copyFromNumpyArray(img, spacing, origin, direction, defaultshape)
            else: raise TypeError('image parameter datatype is not uint8.')
        else: raise TypeError('parameter is not ndarray class.')

    def setSITKImage(self, img: sitkImage) -> None:
        """
            Shallow copy of a SimpleITK Image to the SimpleITK Image
            attribute of the current SisypheImage instance.

            Parameter

                img     SimpleITK.Image
        """
        if isinstance(img, sitkImage):
            if img.GetPixelID() == sitkUInt8:
                self._sitk_image = img
                self._updateImages()
            else: raise TypeError('image parameter datatype is not uint8.')
        else: raise TypeError('image parameter type {} is not sitkImage class.'.format(type(img)))
