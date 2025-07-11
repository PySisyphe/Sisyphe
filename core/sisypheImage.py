"""
External packages/modules
-------------------------

    - Cython, static compiler, https://cython.org/
    - ANTs, image registration, http://stnava.github.io/ANTs/
    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - ITK, medical image processing, https://itk.org/
    - NiBabel, nibabel image class access, https://nipy.org/nibabel
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - scikit-image, image processing, https://scikit-image.org/
    - Scipy, scientific computing, https://docs.scipy.org
    - SimpleITK, medical image processing, https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os.path import exists

import cython

from copy import deepcopy

from numpy import iinfo
from numpy import can_cast
from numpy import array
from numpy import nan as npnan
from numpy import min as npmin
from numpy import max as npmax
from numpy import argwhere
from numpy import ndarray
from numpy import asanyarray
from numpy import diag
from numpy import mean
from numpy import std
from numpy import median
from numpy import percentile
from numpy import histogram
from numpy import transpose
from numpy import nanargmin
from numpy import count_nonzero
from numpy import unravel_index
from numpy import flipud
from numpy import round
from numpy import trunc
from numpy import zeros
from numpy import nan_to_num
from numpy.ma import masked_equal
from numpy.ma import mean as ma_mean
from numpy.ma import median as ma_median
from numpy.ma import std as ma_std
from numpy.ma import filled

from scipy.stats import kurtosis
from scipy.stats import skew

# noinspection PyProtectedMember
from skimage.measure._moments import centroid
from skimage.morphology import h_maxima

from dipy.denoise.noise_estimate import estimate_sigma

# noinspection PyUnresolvedReferences
from itk import Image as itkImage
from itk import GetImageFromArray as itkGetImageFromArray
from itk import GetImageViewFromArray as itkGetImageViewFromArray
from itk import GetArrayViewFromImage as itkGetArrayViewFromImage
from itk import GetMatrixFromArray as itkGetMatrixFromArray
from itk import GetArrayFromMatrix as itkGetArrayFromMatrix

from SimpleITK import sitkUInt8
from SimpleITK import sitkFloat32
from SimpleITK import sitkVectorInt8
from SimpleITK import sitkVectorUInt8
from SimpleITK import sitkVectorInt16
from SimpleITK import sitkVectorUInt16
from SimpleITK import sitkVectorInt32
from SimpleITK import sitkVectorUInt32
from SimpleITK import sitkVectorInt64
from SimpleITK import sitkVectorUInt64
from SimpleITK import sitkVectorFloat32
from SimpleITK import sitkVectorFloat64
from SimpleITK import Image as sitkImage
from SimpleITK import Cast as sitkCast
from SimpleITK import Flip as sitkFlip
from SimpleITK import VectorIndexSelectionCastImageFilter as sitkVectorIndexSelectionCastImageFilter
from SimpleITK import ComposeImageFilter as sitkComposeImageFilter
from SimpleITK import GetImageFromArray as sitkGetImageFromArray
from SimpleITK import GetArrayFromImage as sitkGetArrayFromImage
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
from SimpleITK import RescaleIntensityImageFilter
from SimpleITK import NormalizeImageFilter
from SimpleITK import IntensityWindowingImageFilter

from vtk import VTK_CHAR
from vtk import VTK_UNSIGNED_CHAR
from vtk import vtkImageData
from vtk import vtkImageCast
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray
from vtkmodules.util.numpy_support import numpy_to_vtk

from ants.core import from_numpy as ants_from_numpy
# < Revision 19/02/2025
from ants.core.ants_image import ANTsImage
# from Sisyphe.lib.ants.ants_image import ANTsImage
# Revision 19/02/2025 >

from nibabel.nifti1 import Nifti1Image
from nibabel.nifti1 import Nifti1Header

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
from Sisyphe.core.sisypheImageIO import readFromFreeSurferMGH
from Sisyphe.core.sisypheImageIO import writeToNIFTI
from Sisyphe.core.sisypheImageIO import writeToNRRD
from Sisyphe.core.sisypheImageIO import writeToMINC
from Sisyphe.core.sisypheImageIO import writeToVTK
from Sisyphe.core.sisypheImageIO import writeToJSON
from Sisyphe.core.sisypheImageIO import writeToNumpy

# to avoid import error due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheROI import SisypheROI


__all__ = ['numpyToVtkImageData',
           'simpleITKToVTK',
           'SisypheImage',
           'SisypheBinaryImage']

"""
Functions
~~~~~~~~~

numpyToVtkImageData(np: numpy.ndarray) -> vtk.vtkImageData
simpleITKtoVTK(img: SimpleITK.Image) -> vtk.vtkImageData
"""

def numpyToVtkImageData(np: ndarray) -> vtkImageData:
    """
    numpy ndarray to vtk.vtkImageData conversion.

    Parameters
    ----------
    np : numpy.ndarray
        numpy array to convert

    Returns
    -------
    vtk.vtkImageData
        converted vtkImageData
    """
    buff = np.view(ndarray)
    # noinspection PyTypeChecker
    d = list(buff.shape)
    if len(d) == 2: d.append(1)
    buff.shape = buff.size
    data = numpy_to_vtk(buff)
    img = vtkImageData()
    # noinspection PyArgumentList
    img.SetDimensions(d[::-1])
    img.AllocateScalars(getLibraryDataType(str(np.dtype), 'vtk'), 1)
    img.GetPointData().SetScalars(data)
    return img

def simpleITKToVTK(img: sitkImage) -> vtkImageData:
    """
    SimpleITK.Image to vtk.vtkImageData conversion.

    Parameters
    ----------
    img : SimpleITK.Image
        SimpleITK.Image to convert

    Returns
    -------
    vtk.vtkImageData
        converted vtkImageData
    """
    if isinstance(img, sitkImage):
        np = sitkGetArrayViewFromImage(img)
        vtkimg = numpyToVtkImageData(np)
        # noinspection PyArgumentList
        vtkimg.SetSpacing(img.GetSpacing())
        # Revision 15/04/2023
        # vtkimg.SetOrigin(img.GetOrigin())
        return vtkimg
    else: raise TypeError('parameter type {} is not SimpleITK image.'.format(type(img)))


"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - object -> SisypheImage -> SisypheBinaryImage   
"""

listImages = sitkImage | ndarray
listImages2 = listImages | vtkImageData | ANTsImage
tupleInt3 = tuple[int, int, int]
tupleFloat3 = tuple[float, float, float]
vectorInt3 = list[int] | tupleInt3
vectorFloat3 = list[float] | tupleFloat3

class SisypheImage(object):
    """
    Description
    ~~~~~~~~~~~

    PySisyphe image class.

    This class provides access to internal SimpleITK, ITK, VTK and numpy image classes, which share the same image
    buffer.

    Overloaded operators which work with int, float, SisypheVolume, SisypheImage, SimpleITK Image, and numpy array:

        - Arithmetic  +, -, /, //, *
        - Logic       & (and), | (or), ^ (xor), ~ (not)
        - Relational  >, >=, <, <=, ==, !=

    Getter and Setter access to scalar values with slicing ability.
    Getter: v = instance_name[x, y, z]
    Setter: instance_name[x, y, z] = v
    x, y, z are int or slice object (syntax first:last:step)

    Scope of methods:

        - copy to/from SimpleITK, ITK, VTK, ANTs, NiBabel and numpy image instances
        - various image attributes getter methods
        - descriptive statistics (minimum, maximum, median, mean, standard-deviation, percentile...)
        - IO methods for common neuroimaging file formats (BrainVoyager, Nifti, Nrrd, Minc, VTK)

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheImage

    Creation: 12/01/2021
    Last revision: 13/06/2025
    """
    __slots__ = ['_sitk_image', '_itk_image', '_vtk_image', '_numpy_array', '_attr']

    # Special methods

    """
    Private attributes

    _sitk_image     sitkImage
    _vtk_image      vtkImageData
    _itk_image      itkImage
    _numpy_array    ndarray
    """

    def __init__(self,
                 image: str | listImages2 | SisypheImage | None = None,
                 **kargs) -> None:
        """
        SisypheImage instance constructor.

        Parameters
        ----------
        image : SisypheImage | SimpleITK.Image | vkt.vtkImageData | ants.core.ANTSImage | numpy.ndarray | str
            image to copy (optional)
        **kargs :
            - size, tuple[float, float, float] | list[float, float, float]
            - datatype, str
            - spacing, tuple[float, float, float] | list[float, float, float]
            - direction, tuple[float, ...] | list[float, ...] (9 elements)
        """

        # Init attributes (default, constructor without parameter)

        self._sitk_image = None
        self._itk_image = None
        self._vtk_image = None
        self._numpy_array = None
        # < Revision 17/11/2024
        self._attr = dict()
        # Revision 17/11/2024 >

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
            elif isinstance(image, ndarray):
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
                if 'size' in kargs.keys(): matrix = kargs['size']
                else: matrix = (128, 128, 128)
                if 'datatype' in kargs.keys(): datatype = getLibraryDataType(kargs['datatype'], 'sitk')
                else: datatype = getLibraryDataType('uint16', 'sitk')
                if 'spacing' in kargs.keys(): spacing = kargs['spacing']
                else: spacing = (1.0, 1.0, 1.0)
                if 'origin' in kargs.keys(): origin = kargs['origin']
                else: origin = (0.0, 0.0, 0.0)
                if 'direction' in kargs.keys(): direction = kargs['direction']
                else: direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
                self._sitk_image = sitkImage(matrix, datatype)
                self._sitk_image.SetSpacing(spacing)
                self._sitk_image.SetOrigin(origin)
                self._sitk_image.SetDirection(direction)
                self._updateImages()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheImage instance to str
        """
        buff = 'Image attributes:\n' \
               '\tDatatype: {0}\n' \
               '\tSize: {1[0]} x {1[1]} x {1[2]} x {2}\n' \
               '\tSpacing: {3[0]:.2f} {3[1]:.2f} {3[2]:.2f}\n' \
               '\tFOV: {4[0]:.1f} {4[1]:.1f} {4[2]:.1f}\n' \
               '\tOrigin: {5[0]:.1f} {5[1]:.1f} {5[2]:.1f}\n' \
               '\tDirections:\n' \
               '\t{6[0]:.1f} {6[1]:.1f} {6[2]:.1f}\n' \
               '\t{6[3]:.1f} {6[4]:.1f} {6[5]:.1f}\n' \
               '\t{6[6]:.1f} {6[7]:.1f} {6[8]:.1f}\n'.format(self.getDatatype(),
                                                             self.getSize(),
                                                             self.getNumberOfComponentsPerPixel(),
                                                             self.getSpacing(),
                                                             self.getFieldOfView(),
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

        Returns
        -------
        str
            SisypheImage instance representation
        """
        return 'SisypheImage instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Arithmetic operators

    def __add__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator +. self + other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of addition

        Returns
        -------
        SisypheImage
            image = self + other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__add__(other))

    def __sub__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator -. self - other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of subtraction

        Returns
        -------
        SisypheImage
            image = self - other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__sub__(other))

    def __mul__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator *. self * other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of multiplication

        Returns
        -------
        SisypheImage
            image = self * other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__mul__(other))

    def __div__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator /. self / other -> SisypheImage

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | int | float

        Returns
        -------
        SisypheImage
            image = self / other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__div__(other))

    def __floordiv__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator //. self // other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of floordiv operator

        Returns
        -------
        SisypheImage
            image = self // other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__floordiv__(other))

    def __truediv__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator /. self / other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of division

        Returns
        -------
        SisypheImage
            image = self / other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__truediv__(other))

    def __radd__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator +. other + self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of addition

        Returns
        -------
        SisypheImage
            image = other + self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__radd__(other))

    def __rsub__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator -. other - self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of subtraction

        Returns
        -------
        SisypheImage
            image = other - self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rsub__(other))

    def __rmul__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator *. other * self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of multiplication

        Returns
        -------
        SisypheImage
            image = other * self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rmul__(other))

    def __rdiv__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator /. other / self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of division

        Returns
        -------
        SisypheImage
            image = other / self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rdiv__(other))

    def __rfloordiv__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator //. other // self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of floordiv operator

        Returns
        -------
        SisypheImage
            image = other // self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rfloordiv__(other))

    def __rtruediv__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded arithmetic operator /. other / self -> SisypheImage

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            first operand of division

        Returns
        -------
        SisypheImage
            image = other / self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rtruediv__(other))

    def __neg__(self) -> SisypheImage:
        """
        Special overloaded arithmetic unary operator -. - self -> SisypheImage

        Returns
        -------
        SisypheImage
            image = - self
        """
        return SisypheImage(self._sitk_image.__neg__())

    def __pos__(self) -> SisypheImage:
        """
        Special overloaded arithmetic unary operator +. + self -> SisypheImage

        Returns
        -------
        SisypheImage
            image = + self
        """
        return self

    # Logic operators

    def __and__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator & (and). self & other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            second operand of & operator

        Returns
        -------
        SisypheImage
            image = self & other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__and__(other))

    def __rand__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator & (and). other & self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            first operand of & operator

        Returns
        -------
        SisypheImage
            image = other & self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rand__(other))

    def __or__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator | (or). self | other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            second operand of | operator

        Returns
        -------
        SisypheImage
            image = self | other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__or__(other))

    def __ror__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator | (or). other | self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            first operand of | operator

        Returns
        -------
        SisypheImage
            image = other | self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ror__(other))

    def __xor__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator ^ (xor). self ^ other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            second operand of ^ operator

        Returns
        -------
        SisypheImage
            image = self ^ other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__xor__(other))

    def __rxor__(self, other: listImages | SisypheImage) -> SisypheImage:
        """
        Special overloaded logic operator ^ (xor). other ^ self -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage
            first operand of ^ operator

        Returns
        -------
        SisypheImage
            image = other ^ self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__rxor__(other))

    def __invert__(self) -> SisypheImage:
        """
        Special overloaded logic unary operator ~ (not). ~self -> SisypheImage.

        Returns
        -------
        SisypheImage
            image = ~self
        """
        return SisypheImage(self._sitk_image.__invert__())

    # Relational operators

    def __lt__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded relational operator <. self < other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of < operator

        Returns
        -------
        SisypheImage
            image = self < other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__lt__(other))

    def __le__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded relational operator <=. self <= other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of <= operator

        Returns
        -------
        SisypheImage
            image = self <= other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__le__(other))

    def __eq__(self, other: listImages | SisypheImage | int | float) -> bool | SisypheImage:
        """
        Special overloaded relational operator ==. self == other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of == operator

        Returns
        -------
        bool | SisypheImage
            result = self == other
        """
        if isinstance(other, SisypheImage): return id(self) == id(other)
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__eq__(other))

    def __ne__(self, other: listImages | SisypheImage | int | float) -> bool | SisypheImage:
        """
        Special overloaded relational operator !=. self != other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of != operator

        Returns
        -------
        bool | SisypheImage
            result = self != other
        """
        if isinstance(other, SisypheImage): return id(self) != id(other)
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ne__(other))

    def __gt__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded relational operator >. self > other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of > operator

        Returns
        -------
        SisypheImage
            image = self > other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__gt__(other))

    def __ge__(self, other: listImages | SisypheImage | int | float) -> SisypheImage:
        """
        Special overloaded relational operator >=. self >= other -> SisypheImage.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | SisypheImage | int | float
            second operand of >= operator

        Returns
        -------
        SisypheImage
            image = self >= other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        return SisypheImage(self._sitk_image.__ge__(other))

    # set/get pixel methods

    def __getitem__(self, idx):
        """
        Special overloaded container getter method. Get scalar value(s) with slicing ability.
        ex: v = instance_name[x, y, z]

        Parameters
        ----------
        idx : list[int, int, int], tuple[int, int, int] | slice
            x, y, z int indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)

        Returns
        -------
        int | float | tuple | SisypheImage
            scalar value or SisypheImage if slicing
        """
        r = self._sitk_image.__getitem__(idx)
        if isinstance(r, sitkImage): r = SisypheImage(r)
        return r

    def __setitem__(self, idx, rvalue):
        """
        Special overloaded container setter method. Set scalar value(s) with slicing ability.
        ex: instance_name[x, y, z] = rvalue

        Parameters
        ----------
        idx : list[int, int, int], tuple[int, int, int] | slice
            x, y, z int indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)
        rvalue : int | float | SisypheImage
            scalar value or SisypheImage if slicing
        """
        if isinstance(rvalue, SisypheImage): rvalue = rvalue.getSITKImage()
        else: rvalue = self._toSimpleITK(rvalue)
        self._sitk_image.__setitem__(idx, rvalue)

    # Private methods

    def _toSimpleITK(self, img: ANTsImage | ndarray | int | float) -> sitkImage | int | float:
        if isinstance(img, ANTsImage): img = img.view().T
        if isinstance(img, ndarray):
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
        # noinspection PyPropertyAccess
        self._numpy_array.data = buff.data
        self._numpy_array = self._numpy_array.T  # default shape (z, y, x)

    def _updateVTKImageFromNumpy(self) -> None:
        # default numpy array shape (z, y, x)
        buff = self._numpy_array.view(ndarray)
        buff.shape = buff.size
        data = numpy_to_vtk(buff)
        self._vtk_image = vtkImageData()
        sz = self._sitk_image.GetSize()
        sp = self._sitk_image.GetSpacing()
        if len(sz) == 2:
            sz = (sz[0], sz[1], 1)
            sp = (sp[0], sp[1], 1.0)
        # noinspection PyArgumentList
        self._vtk_image.SetDimensions(sz)
        # noinspection PyArgumentList
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
            d = array(self._sitk_image.GetDirection())
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

        Returns
        -------
        bool
            True if itk.Image attribute is available (not None)
        """
        return self._itk_image is not None

    def allocate(self, matrix: vectorInt3, datatype: str) -> None:
        """
        Initialize image buffer.

        Parameters
        ----------
        matrix : list[float, float, float] | tuple[float, float, float]
            image size in x, y, z dimensions
        datatype : str
            numpy datatype
        """
        if isinstance(matrix, (list, tuple)) and len(matrix) == 3:
            if isValidDatatype(datatype):
                self._sitk_image = sitkImage(matrix, getLibraryDataType(datatype, 'sitk'))
                self._updateImages()
            else: raise ValueError('string parameter is not a correct datatype.')
        else: raise TypeError('matrix parameter is not a list of 3 int.')

    def copyFromSITKImage(self, img: sitkImage) -> None:
        """
        Copy a SimpleITK image buffer to the current SisypheImage instance. Image buffer is not shared between
        SimpleITK image and SisypheImage instances (deep copy).

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        if isinstance(img, sitkImage):
            # < Revision 13/06/2025
            # self._sitk_image = sitkImage(img)
            self._sitk_image = deepcopy(img)
            # Revision 13/06/2025 >
            self._updateImages()
        else: raise TypeError('parameter type {} is not SimpleITK.'.format(type(img)))

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        """
        Copy a VTKImageData buffer to the current SisypheImage instance. Image buffer is not shared between
        VTKImageData image and SisypheImage instances.

        Parameters
        ----------
        img : vtk.vtkImageData
            image to copy
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
        Copy an ITKImage buffer to the current SisypheImage instance. Image buffer is not shared between ITKImage
        image and SisypheImage instances.

        Parameters
        ----------
        img : itk.Image
            image to copy
        """
        if isITKImageSupportedType(img):
            # GetArrayViewFromImage() return default numpy array shape (z, y, x)
            buff = itkGetArrayViewFromImage(img)
            d = tuple(itkGetArrayFromMatrix(img.GetDirection()).flatten())
            # noinspection PyTypeChecker
            self.copyFromNumpyArray(buff, tuple(img.GetSpacing()), tuple(img.GetOrigin()), d)
            self._updateImages()
        else: raise TypeError('parameter type {} is not itkImage class or itktype is not supported.'.format(type(img)))

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        """
        Copy an ANTsImage buffer to the current SisypheImage instance. Image buffer is not shared between ANTsImage
        image and SisypheImage instances.

        Parameters
        ----------
        img : ants.core.ANTsImage
            image to copy
        """
        if isinstance(img, ANTsImage):
            # ANTsImage.view() return numpy array with image shape (x, y, z)
            # transpose to get default numpy array shape (z, y, z)
            buff = img.view().T
            # noinspection PyUnresolvedReferences
            d = list(img.direction.flatten())
            # noinspection PyTypeChecker
            self.copyFromNumpyArray(buff, img.spacing, img.origin, d)
            self.setDirections()
        else: raise TypeError('parameter type {} is not ANTsImage class.'.format(type(img)))

    def copyFromNumpyArray(self,
                           img: ndarray,
                           spacing: vectorFloat3 = (1.0, 1.0, 1.0),
                           origin: vectorFloat3 = (0.0, 0.0, 0.0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True) -> None:
        """
        Copy a Numpy array buffer to the current SisypheImage instance. Image buffer is not shared between numpy array
        and SisypheImage instances.

        Parameters
        ----------
        img : numpy.ndarray
            image to copy
        spacing : list[float, float, float] | tuple[float, float, float],
            voxel sizes in mm (default 1.0, 1.0, 1.0)
        origin : list[float, float, float] | tuple[float, float, float],
            origin coordinates (default 0.0, 0.0, 0.0)
        direction : list[float]
            axes directions
        defaultshape : bool
            - 3D: if True, numpy array (z, y, x) shape, otherwise (x, y, z) shape
            - 4D: if True, numpy array (n, z, y, x) shape, otherwise (x, y, z, n) shape
        """
        if isinstance(img, ndarray):
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

    def copyFromNibabelImage(self, img: Nifti1Image):
        """
        Copy a Nifti1Image to the current SisypheImage instance.
        Image buffer is not shared between Nifti1Image and SisypheImage instances (deep copy).

        Parameters
        ----------
        img : nibabel.nifti1.Nifti1Image
        """
        hdr = Nifti1Header(img.header)
        # noinspection PyTypeChecker
        self.copyFromNumpyArray(img=asanyarray(img.dataobj),
                                spacing=hdr.get_zooms(),
                                defaultshape=False)

    def copyToSITKImage(self) -> sitkImage:
        """
        SimpleITK image copy of the current SisypheImage instance. Image buffer is not shared between SimpleITK image
        and SisypheImage instances (deep copy).

        Returns
        -------
        SimpleITK.Image
            image copy
        """
        if not self.isEmpty():
            # < Revision 13/06/2025
            # return sitkImage(self._sitk_image)
            return deepcopy(self._sitk_image)
            # Revision 13/06/2025 >
        else: raise ValueError('SisypheImage array is empty.')

    def copyToVTKImage(self) -> vtkImageData:
        """
        VTKImageData copy of the current SisypheImage instance. Image buffer is not shared between VTKImageData and
        SisypheImage instances.

        Returns
        -------
        vtk.vtkImageData
            image copy
        """
        if not self.isEmpty():
            buff = vtkImageData()
            buff.DeepCopy(self._vtk_image)
            return buff
        else: raise ValueError('SisypheImage array is empty.')

    def copyToITKImage(self) -> itkImage:
        """
        ITKImage copy of the current SisypheImage instance. Image buffer is not shared between ITKImage and
        SisypheImage instances.

        Returns
        -------
        itk.Image
            image copy
        """
        if not self.isEmpty():
            # GetImageFromArray() array parameter must have default shape (z, y, x)
            buff = itkGetImageFromArray(self._numpy_array)
            buff.SetOrigin(self._sitk_image.GetOrigin())
            buff.SetSpacing(self._sitk_image.GetSpacing())
            d = itkGetMatrixFromArray(array(self._sitk_image.GetDirection()).reshape(3, 3))
            buff.SetDirection(d)
            return buff
        else: raise ValueError('SisypheImage array is empty.')

    def copyToANTSImage(self, dtype: str = '', direction: bool = False) -> ANTsImage:
        """
        ANTsImage copy of the current SisypheImage instance. Image buffer is not shared between ANTsImage and
        SisypheImage instances.

        Parameters
        ----------
        dtype : str
            datatype conversion (default no conversion)
        direction : bool
            set direction to LPI+ if True (default False)

        Returns
        -------
        ants.core.ANTSImage
            image copy
        """
        if not self.isEmpty():
            # ants_from_numpy() array parameter must have image shape (x, y, z)
            # < Revision 26/102/2024
            # bugfix if multicomponent image
            # data = self._numpy_array.T
            data = self.getNumpy(defaultshape=False)
            # Revision 26/102/20 >
            t = ('unit8', 'uint32', 'float32', 'float64')
            if self.getDatatype() not in t or dtype != '':
                if dtype in t: data = data.astype(dtype)
                else: data = data.astype('float32')
            d = array(self._sitk_image.GetDirection()).reshape((3, 3))
            # < Revision 26/10/2024
            # bugfix if multicomponent image
            # img = ants_from_numpy(data, self._sitk_image.GetOrigin(), self._sitk_image.GetSpacing(), d)
            img = ants_from_numpy(data,
                                  self._sitk_image.GetOrigin(),
                                  self._sitk_image.GetSpacing(),
                                  d, has_components=self.getNumberOfComponentsPerPixel() > 1)
            # Revision 26/10/2024
            # set direction to LPI
            if direction:
                d = img.direction
                d[0, 0] = -1
                d[1, 1] = -1
                img.set_direction(d)
            return img
        else: raise ValueError('SisypheImage array is empty.')

    def copyToNumpyArray(self, defaultshape: bool = True) -> ndarray:
        """
        Numpy array copy of the current SisypheImage instance. Image buffer is not shared between numpy array and
        SisypheImage instances.

        Parameters
        ----------
        defaultshape : bool
            - 3D: if True returns (z, y, x) shape, otherwise returns shape (x, y, z)
            - 4D: if True returns (n, z, y, x) shape, otherwise returns shape (x, y, z, n)

        Returns
        -------
        numpy.ndarray
            image copy
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
                if defaultshape: return self._numpy_array.copy()
                else: return self._numpy_array.copy().T
            elif self._numpy_array.ndim == 4:
                """
                    4D multicomponent volume, n components
                    native shape = (z, y, x, n)
                    defaultshape = True  -> return shape (n, z, y, x)
                                 = False -> return shape (x, y, z, n)   
                """
                if defaultshape: return transpose(self._numpy_array, axes=(3, 0, 1, 2)).copy()
                else: return transpose(self._numpy_array, axes=(2, 1, 0, 3)).copy()
            else: raise AttributeError('Invalid number of dimensions.')
        else: raise ValueError('SisypheImage array is empty.')

    def copyToNibabelImage(self) -> Nifti1Image:
        """
        Nibabel Nifti1Image copy of the current SisypheImage instance. Image buffer is not shared between Nifti1Image
        and SisypheImage instances (deep copy).

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            image copy
        """
        img = self.copyToNumpyArray(defaultshape=False)
        affine = diag(list(self.getSpacing()) + [1.0])
        # noinspection PyTypeChecker
        return Nifti1Image(img, affine)

    def cast(self, datatype: str) -> tuple[SisypheImage, float, float]:  # recode with SimpleITK Clamp
        """
        SisypheImage copy of the current SisypheImage instance with a new datatype.

        Parameters
        ----------
        datatype : str
            numpy datatype

        Returns
        -------
        tuple[SisypheImage, float, float]
            - first float, slope
            - second float, intercept
            - linear transform: cast value = slope * original value + intercept, linear transform is applied if direct cast is not possible (overflow error)
        """
        if not self.isEmpty():
            if datatype == str(self._numpy_array.dtype):
                return SisypheImage(self._sitk_image), 1.0, 0.0
            else:
                if can_cast(str(self._numpy_array.dtype), datatype, 'same_kind'):
                    # < Revision 12/09/2024
                    # take into account vector datatypes
                    if self.getNumberOfComponentsPerPixel() > 1:
                        if datatype == 'int8': dtype = sitkVectorInt8
                        elif datatype == 'uint8': dtype = sitkVectorUInt8
                        elif datatype == 'int16': dtype = sitkVectorInt16
                        elif datatype == 'uint16': dtype = sitkVectorUInt16
                        elif datatype == 'int32': dtype = sitkVectorInt32
                        elif datatype == 'uint32': dtype = sitkVectorUInt32
                        elif datatype == 'int64': dtype = sitkVectorInt64
                        elif datatype == 'uint64': dtype = sitkVectorUInt64
                        elif datatype == 'float32': dtype = sitkVectorFloat32
                        elif datatype == 'float64': dtype = sitkVectorFloat64
                        else: raise ValueError('Vector datatype {} is not supported.'.format(datatype))
                    else: dtype = getLibraryDataType(datatype, 'sitk')
                    # Revision 12/09/2024 >
                    img = sitkCast(self._sitk_image, dtype)
                    return SisypheImage(image=img), 1.0, 0.0
                else:
                    slope = 1.0
                    tmax = iinfo(datatype).max
                    vmax = self._numpy_array.max()
                    vmin = self._numpy_array.min()
                    if vmax - vmin < tmax:
                        buff = sitkCast(self._sitk_image, sitkFloat32) - vmin
                    else:
                        islope = tmax / (vmax - vmin)
                        buff = (sitkCast(self._sitk_image, sitkFloat32) - vmin) * islope
                        slope = 1.0 / islope
                    buff = sitkCast(buff, getLibraryDataType(datatype, 'sitk'))
                    img = SisypheImage(image=buff)
                    return img, slope, vmin
        else: raise ValueError('SisypheImage array is empty.')

    def copy(self) -> SisypheImage:
        """
        SisypheImage copy of the current SisypheImage instance.

        Returns
        -------
        SisypheImage
            image copy
        """
        if not self.isEmpty(): return SisypheImage(self._sitk_image)
        else: raise ValueError('SisypheImage array is empty.')

    def copyComponent(self, c: int = 0) -> SisypheImage:
        """
        Extract single-component SisypheImage from the current multi-component SisypheImage instance.

        Parameters
        ----------
        c : int
            component index (default 0)

        Returns
        -------
        SisypheImage
            extracted single-component image
        """
        if not self.isEmpty():
            n = self.getNumberOfComponentsPerPixel()
            if n > 1:
                if isinstance(c, int):
                    f = sitkVectorIndexSelectionCastImageFilter()
                    f.SetIndex(c)
                    return SisypheImage(f.Execute(self.getSITKImage()))
                else: raise TypeError('parameter type {} is not int.'.format(type(c)))
            else: raise ValueError('Image has only one component.')
        else: raise AttributeError('Image is empty.')

    def getSITKImage(self) -> sitkImage:
        """
        SimpleITK view (pointer) of the current SisypheImage instance. Image buffer is shared between SimpleITK image
        and current SisypheImage instances.

        Returns
        -------
        SimpleITK.Image
            shallow copy of image
        """
        if not self.isEmpty(): return self._sitk_image
        else: raise ValueError('SisypheImage array is empty.')

    def setSITKImage(self, img: sitkImage) -> None:
        """
        Shallow copy of a SimpleITK Image to the current SisypheImage instance. Image buffer is shared between
        SimpleITK image and current SisypheImage instances.

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        if isinstance(img, sitkImage):
            self._sitk_image = img
            self._updateImages()
        else: raise TypeError('parameter type {} is not sitkImage.'.format(type(img)))

    def getVTKImage(self) -> vtkImageData:
        """
        VTKImageData view (pointer) of the current SisypheImage. Image buffer is shared between VTKImageData and
        current SisypheImage instances.

        Returns
        -------
        vtk.vtkImageData
            shallow copy of image
        """
        if not self.isEmpty(): return self._vtk_image
        else: raise ValueError('SisypheImage array is empty.')

    def getITKImage(self) -> itkImage:
        """
        ITKImage view (pointer) of the current SisypheImage. Image buffer is shared between ITKImage and current
        SisypheImage instances.

        Returns
        -------
        itk.Image
            shallow copy of image
        """
        if not self.isEmpty(): return self._itk_image
        else: raise ValueError('SisypheImage array is empty.')

    def getNumpy(self, defaultshape: bool = True) -> ndarray:
        """
        Numpy array view (pointer) of the current SisypheImage instance. Image buffer is shared between numpy array
        and current SisypheImage instances.

        Parameters
        ----------
        defaultshape : bool
            - 3D: if True returns (z, y, x) shape, otherwise returns shape (x, y, z)
            - 4D: if True returns (n, z, y, x) shape, otherwise returns shape (x, y, z, n)

        Returns
        -------
        numpy.ndarray
            shallow copy of image
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
                    defaultshape = True  -> return shape (n, z, y, x)
                                 = False -> return shape (x, y, z, n)   
                """
                if defaultshape: return transpose(self._numpy_array, axes=(3, 0, 1, 2))
                else: return transpose(self._numpy_array, axes=(2, 1, 0, 3))
            else: raise AttributeError('Invalid number of dimensions.')
        else: raise ValueError('SisypheImage array is empty.')

    def getSize(self) -> vectorInt3:
        """
        Get image size, i.e. voxel count in each dimension.

        Returns
        -------
        tuple[int, int, int]
            image size in x, y, z dimensions
        """
        if not self.isEmpty(): r = self._sitk_image.GetSize()
        else:
            if 'size' in self._attr: r = self._attr['size']
            else: return 0, 0, 0
        if len(r) == 2: r = (r[0], r[1], 1)
        return r

    def hasSameSize(self, img: SisypheImage | vtkImageData | ANTsImage | sitkImage | ndarray | vectorInt3):
        """
        Compare size between the current SisypheImage instance and other image.

        Parameters
        ----------
        img : SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage | numpy.ndarray | tuple[int, int, int] | list[int, int, int]
            image to compare

        Returns
        -------
        bool
            True if same size
        """
        s = None
        if isinstance(img, SisypheImage): s = tuple(img.getSize())
        elif isinstance(img, sitkImage): s = tuple(img.GetSize())
        elif isinstance(img, vtkImageData): s = tuple(img.GetDimensions())
        elif isinstance(img, ANTsImage): s = tuple(img.shape)
        elif isinstance(img, ndarray): s = img.shape
        elif isinstance(img, list | tuple): s = tuple(img)
        return s == self.getSize()

    def getWidth(self) -> int:
        """
        Get image size in x.

        Returns
        -------
        int
            x-axis image size
        """
        if not self.isEmpty(): return self.getSITKImage().GetWidth()
        else:
            if 'size' in self._attr: return self._attr['size'][0]
            else: return 0

    def getHeight(self) -> int:
        """
        Get image size in y.

        Returns
        -------
        int
            y-axis image size
        """
        if not self.isEmpty(): return self.getSITKImage().GetHeight()
        else:
            if 'size' in self._attr: return self._attr['size'][1]
            else: return 0

    def getDepth(self) -> int:
        """
        Get image size in z.

        Returns
        -------
        int
            z-axis image size
        """
        if not self.isEmpty(): r = self.getSITKImage().GetDepth()
        else:
            if 'size' in self._attr: r = self._attr['size'][2]
            else: return 0
        if r == 0: r = 1
        return r

    def getSpacing(self) -> vectorFloat3:
        """
        Get voxel size (mm) in each dimension.

        Returns
        -------
        tuple[float, float, float]
            voxel spacing in x, y, z
        """
        if not self.isEmpty(): r = self._sitk_image.GetSpacing()
        else:
            if 'spacing' in self._attr: r = self._attr['spacing']
            else: return 0.0, 0.0, 0.0
        if len(r) == 2: r = (r[0], r[1], 1.0)
        elif len(r) == 4: r = r[:3]
        return r

    def hasSameSpacing(self, img: SisypheImage | listImages | vectorFloat3, decimals: int = 2):
        """
        Compare spacing between the current SisypheImage instance and other image.

        Parameters
        ----------
        img : SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage | tuple[float, float, float] | list[float, float, float]
            get spacing from image attribute (SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage)
            or directly from a tuple or a list of three values
        decimals : int
            Number of decimal to round to (default 2)

        Returns
        -------
        bool
            True if same spacing
        """
        s = None
        if isinstance(img, SisypheImage): s = tuple(img.getSpacing())
        elif isinstance(img, sitkImage): s = tuple(img.GetSpacing())
        elif isinstance(img, vtkImageData): s = tuple(img.GetSpacing())
        elif isinstance(img, ANTsImage): s = tuple(img.spacing)
        elif isinstance(img, list | tuple): s = img
        s1 = round(array(s), decimals)
        s2 = round(array(self.getSpacing()), decimals)
        # noinspection PyTypeChecker
        return all(s1 == s2)

    def setSpacing(self, sx: float, sy: float, sz: float) -> None:
        """
        Set voxel size (mm) in each dimension.

        Parameters
        ----------
        sx : float
            voxel spacing in x
        sy : float
            voxel spacing in y
        sz : float
            voxel spacing in x
        """
        self._sitk_image.SetSpacing((sx, sy, sz))
        self._vtk_image.SetSpacing(sx, sy, sz)
        if self.hasITKImage():
            self._itk_image.SetSpacing((sx, sy, sz))

    def getVoxelVolume(self) -> float:
        """
        Get voxel volume in mm3.

        Returns
        -------
        float
            voxel volume in mm3
        """
        sx, sy, sz = self.getSpacing()
        return sx * sy * sz

    def getNumberOfVoxels(self) -> int:
        """
        Get voxel count in the array.

        Returns
        -------
        int
            voxel count
        """
        s = self.getSize()
        return s[0] * s[1] * s[2]

    def getNumberOfVoxelsInXYPlane(self) -> int:
        """
        Get voxel count in axial slice.

        Returns
        -------
        int
            voxel count in XY plane
        """
        s = self.getSize()
        return s[0] * s[1]

    def getNumberOfVoxelsInXZPlane(self) -> int:
        """
        Get voxel count in coronal slice.

        Returns
        -------
        int
            voxel count in XZ plane
        """
        s = self.getSize()
        return s[0] * s[2]

    def getNumberOfVoxelsInYZPlane(self) -> int:
        """
        Get voxel count in sagittal slice.

        Returns
        -------
        int
            voxel count in YZ plane
        """
        s = self.getSize()
        return s[1] * s[2]

    def isIsotropic(self, tol: float = 2.0) -> bool:
        """
        Check whether voxel is isotropic, i.e. same spacing in each dimension.
        A tolerance is applied:  max(spacing) / min(spacing) <= tol

        Parameters
        ----------
        tol : float
            tolerance (default 2.0)

        Returns
        -------
        bool
            True if max(spacing) / min(spacing) < tol
        """
        if isinstance(tol, float):
            s = list(self.getSpacing())
            s.sort()
            # < Revision 9/10/2024
            # return (s[2] / s[0]) < tol
            return (s[2] / s[0]) <= tol
            # Revision 9/10/2024 >
        else: raise TypeError('parameter type {} is not float.'.format(type(tol)))

    def isAnisotropic(self, tol: float = 2.0) -> bool:
        """
        Check whether voxel is anisotropic, i.e. not same spacing in each dimension
        A tolerance is applied: max(spacing) / min(spacing) > tol

        Parameters
        ----------
        tol : float
            tolerance (default 2.0)

        Returns
        -------
        bool
            True if max(spacing) / min(spacing) > tol
        """
        return not self.isIsotropic(tol)

    def isThickAnisotropic(self, tol: float = 2.0, thickness: float = 3.0) -> bool:
        """
        Check if the voxel is anisotropic and thicker than a given slice thickness in mm.
        A tolerance is applied for anisotropy: max(spacing) / min(spacing) > tol.

        Parameters
        ----------
        tol : float
            tolerance (default 2.0)
        thickness : float
            slice thickness threshold (default 3.0 mm)

        Returns
        -------
        bool
            True if max(spacing) / min(spacing) > tol and max(spacing) >= thickness
        """
        s = list(self.getSpacing())
        s.sort()
        # < Revision 20/02/2025
        # return (s[2] / s[0]) > tol or s[2] >= thickness
        return (s[2] / s[0]) > tol and s[2] >= thickness
        # Revision 20/02/2025 >

    def getNative2DOrientation(self) -> int:
        """
        Get code of the native orientation (0 3D, 1 axial, 2 coronal, 3 sagittal).

        Returns
        -------
        int
            code of the native orientation
        """
        if self.isAnisotropic():
            s = self.getSpacing()
            return 3 - s.index(max(s))
        else: return 0  # Unspecified or 3D

    def getNative2DOrientationAsString(self) -> tuple[str, str | None]:
        """
        Get the native orientation as str.

        Returns
        -------
        tuple[str, str]
            - first str, mode '2D' or '3D'
            - second str, orientation 'Axial', 'Coronal' or 'Sagittal'
        """
        r = self.getNative2DOrientation()
        if r == 0: return '3D', None
        elif r == 1: return '2D', 'Axial'
        elif r == 2: return '2D', 'Coronal'
        else: return '2D', 'Sagittal'

    def getCenter(self) -> vectorFloat3:
        """
        Get center of the volume as world coordinates.

        Returns
        -------
        tuple[float, float, float]
            center of the volume
        """
        d = self.getSize()
        s = self.getSpacing()
        return ((d[0] - 1) * s[0] * 0.5,
                (d[1] - 1) * s[1] * 0.5,
                (d[2] - 1) * s[2] * 0.5)
        # return tuple([(d[i] - 1) * s[i] * 0.5 for i in range(3)])

    def getFieldOfView(self, decimals: int | None = None) -> tupleFloat3:
        """
        Get field of view of the volume.

        Parameters
        ----------
        decimals : int | None
            number of decimals used to round values, if None no round

        Returns
        -------
        tuple[float, float, float]
            field of view
        """
        matrix = self.getSize()
        spacing = self.getSpacing()
        # < Revision 08/04/2025
        # rounding management
        if decimals is not None:
            return (round(matrix[0] * spacing[0], decimals),
                    round(matrix[1] * spacing[1], decimals),
                    round(matrix[2] * spacing[2], decimals))
        # Revision 08/04/2025 >
        else:
            return (matrix[0] * spacing[0],
                    matrix[1] * spacing[1],
                    matrix[2] * spacing[2])

    def hasSameFieldOfView(self, img: SisypheImage | vtkImageData | ANTsImage | sitkImage | vectorFloat3, decimals: int = 2) -> bool:
        """
        Compare field of view between current SisypheImage instance and other image.

        Parameters
        ----------
        img : SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage | tuple[float, float, float] | list[float, float, float]
            get FOV value from image attributes (SisypheImage | SimpleITK.Image | itk.Image | vtk.vtkImageData | ants.core.ANTsImage)
            or directly from a tuple or a list of three values
        decimals : int
            Number of decimal places to round to (default 2)

        Returns
        -------
        bool
            True if same field of view
        """
        s, m = 0, 0
        if isinstance(img, SisypheImage):
            s = array(img.getSpacing())
            m = array(img.getSize())
        elif isinstance(img, sitkImage):
            s = array(img.GetSpacing())
            m = array(img.GetSize())
        elif isinstance(img, vtkImageData):
            s = array(img.GetSpacing())
            m = array(img.GetDimensions())
        elif isinstance(img, ANTsImage):
            s = array(img.spacing)
            m = array(img.shape)
        elif isinstance(img, (tuple, list)):
            s = array(img)
            m = array([1.0, 1.0, 1.0])
        # < Revision 19/09/2024
        # space = s * m
        # return all(space == self.getFieldOfView())
        space1 = round(s * m, decimals)
        space2 = round(array(self.getFieldOfView()), decimals)
        # noinspection PyTypeChecker
        return all(space1 == space2)
        # Revision 19/09/2024 >

    def getDatatype(self) -> str:
        """
        Get image datatype as numpy datatype (i.e. 'uint8', 'int8', 'uint16', 'int16', 'int32', 'uint32', 'int64',
        'uint64', 'float32', 'float62').

        Returns
        -------
        str
            numpy datatype
        """
        if not self.isEmpty(): return str(self._numpy_array.dtype)
        else:
            if 'datatype' in self._attr: return self._attr['datatype']
            else: return 'None'

    def isIntegerDatatype(self) -> bool:
        """
        Check whether datatype is integer ('uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64' or 'int64').

        Returns
        -------
        bool
            True if integer datatype
        """
        return self.getDatatype() in getIntStdDatatypes()

    def isUInt8Datatype(self) -> bool:
        """
        Check whether datatype is uint8.

        Returns
        -------
        bool
            True if uint8 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[0]

    def isInt8Datatype(self) -> bool:
        """
        Check whether datatype is int8.

        Returns
        -------
        bool
            True if int8 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[1]

    def isUInt16Datatype(self) -> bool:
        """
        Check whether datatype is uint16.

        Returns
        -------
        bool
            True if uint16 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[2]

    def isInt16Datatype(self) -> bool:
        """
        Check whether datatype is int16.

        Returns
        -------
        bool
            True if int16 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[3]

    def isUInt32Datatype(self) -> bool:
        """
        Check whether datatype is uint32.

        Returns
        -------
        bool
            True if uint32 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[4]

    def isInt32Datatype(self) -> bool:
        """
        Check whether datatype is int32.

        Returns
        -------
        bool
            True if int32 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[5]

    def isUInt64Datatype(self) -> bool:
        """
        Check whether datatype is uint64.

        Returns
        -------
        bool
            True if uint64 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[6]

    def isInt64Datatype(self) -> bool:
        """
        Check whether datatype is int64.

        Returns
        -------
        bool
            True if int64 datatype
        """
        return self.getDatatype() == getIntStdDatatypes()[7]

    def isFloatDatatype(self) -> bool:
        """
        Check whether datatype is float ('float32' or 'float64').

        Returns
        -------
        bool
            True if float datatype
        """
        return self.getDatatype() in getFloatStdDatatypes()

    def isFloat32Datatype(self) -> bool:
        """
        Check whether datatype is float32.

        Returns
        -------
        bool
            True if float32 datatype
        """
        return self.getDatatype() == getFloatStdDatatypes()[0]

    def isFloat64Datatype(self) -> bool:
        """
        Check whether datatype is float64.

        Returns
        -------
        bool
            True if float64 datatype
        """
        return self.getDatatype() == getFloatStdDatatypes()[1]

    def getDatatypeAs(self, lib: str = 'sitk') -> str | int | None:
        """
        Get datatype with the library format of ANTs, SimpleITK, ITK or VTK.

        Parameters
        ----------
        lib : str | int
            - library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
            - library code (i.e. ants=0, itk=1, sitk=2, vtk=3)

        Returns
        -------
        str | int
            datatype (str or int code)
        """
        if isValidLibraryName(lib):
            # < Revision 17/11/2024
            # if not self.isEmpty(): return getLibraryDataType(str(self._numpy_array.dtype), lib)
            # else: return None
            dtype = self.getDatatype()
            if dtype is not None: return getLibraryDataType(dtype, lib)
            else: return None
            # Revision 17/11/2024 >
        else: raise ValueError('parameter {} is not a valid library name.'.format(lib))

    def getNumberOfComponentsPerPixel(self) -> int:
        """
        Get number of components. Array element of single component image is a scalar, array element of multi-component
        image is a vector. The number of components is the vector element count.

        Returns
        -------
        int
            number of components
        """
        if not self.isEmpty(): return self._sitk_image.GetNumberOfComponentsPerPixel()
        else:
            if 'components' in self._attr: return self._attr['components']
            else: return 0

    def isMulticomponent(self) -> bool:
        """
        Check whether image is multicomponent (array element is a vector and not a scalar value).

        Returns
        -------
        bool
            True if multicomponent image
        """
        return self._sitk_image.GetNumberOfComponentsPerPixel() > 1

    def getNumberOfDimensions(self) -> int:
        """
        Get number of dimensions.

        Returns
        -------
        int
            number of dimensions
        """
        if not self.isEmpty(): return self._sitk_image.GetDimension()
        else:
            if 'size' in self._attr:
                size = self._attr['size']
                if size[2] == 1: return 2
                else: return 3
            else: return 0

    def getDirections(self) -> tuple[float, ...]:
        """
        Get vectors of image axes in RAS+ coordinates system.

        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats:

            - First vector, x-axis image direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y-axis image direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, z-axis image direction, [0.0, 0.0, 1.0] (RAS+ default)

        Returns
        -------
        tuple[float, ...]
            vectors of image axes
        """
        if not self.isEmpty(): r = self._sitk_image.GetDirection()
        else:
            if 'directions' in self._attr: r = self._attr['directions']
            else: return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        if len(r) == 4: r = (r[0], r[1], 0.0, r[2], r[3], 0.0, 0.0, 0.0, 1.0)
        return r

    def getFirstVectorDirection(self) -> vectorFloat3:
        """
        Get first direction vector, x image axis in RAS+ coordinates system.

        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats:

            - First vector, x-axis image direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y-axis image direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, z-axis image direction, [0.0, 0.0, 1.0] (RAS+ default)

        Returns
        -------
        tuple[float, float, float]
            vector of the x-axis image
        """
        if not self.isEmpty():
            return self._sitk_image.GetDirection()[0:3]
        else:
            if 'directions' in self._attr: return self._attr['directions'][0:3]
            else: return 0.0, 0.0, 0.0

    def getSecondVectorDirection(self) -> vectorFloat3:
        """
        Get second direction vector, y image axis in RAS+ coordinates system.

        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats:

            - First vector, x-axis image direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y-axis image direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, z-axis image direction, [0.0, 0.0, 1.0] (RAS+ default)

        Returns
        -------
        tuple[float, float, float]
            vector of the y-axis image
        """
        if not self.isEmpty(): return self._sitk_image.GetDirection()[3:6]
        else:
            if 'directions' in self._attr: return self._attr['directions'][3:6]
            else: return 0.0, 0.0, 0.0

    def getThirdVectorDirection(self) -> vectorFloat3:
        """
        Get third direction vector, z image axis in RAS+ coordinates system.

        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats:

            - First vector, x-axis image direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y-axis image direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, z-axis image direction, [0.0, 0.0, 1.0] (RAS+ default)

        Returns
        -------
        tuple[float, float, float]
            vector of the z-axis image
        """
        if not self.isEmpty(): return self._sitk_image.GetDirection()[6:]
        else:
            if 'directions' in self._attr: return self._attr['directions'][6:]
            else: return 0.0, 0.0, 0.0

    def setDirections(self, direction: list | tuple = tuple(getRegularDirections())) -> None:
        """
        Set vectors of image axes in RAS+ coordinates system. PySisyphe uses RAS+ world coordinates system convention
        (as MNI, Nibabel, Dipy...) with origin to corner of the voxel.

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats

            - First vector, x image axis direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y image axis direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, y image axis direction, [0.0, 0.0, 1.0] (RAS+ default)

        Parameters
        ----------
        direction  tuple[float, ...]
            9 elements, vectors of image axes
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(direction)
            if self.hasITKImage():
                d = array(self._sitk_image.GetDirection())
                if d.size == 4: d = d.reshape(2, 2)
                elif d.size == 9: d = d.reshape(3, 3)
                buff = itkGetMatrixFromArray(d)
                self._itk_image.SetDirection(buff)

    def getMemorySize(self, rep: str = 'B') -> int | float:
        """
        Get the memory size of the current SisypheImage instance.

        Parameters
        ----------
        rep : str
            memory unit: 'B' Bytes, 'KB' Kilobytes or 'MB' Megabytes

        Returns
        -------
        int | float,
            - int if rep == 'B'
            - float if rep in ('KB', 'MB')
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
            else: raise ValueError('invalid rep parameter.')
        else: return 0.0

    def setDefaultOrigin(self) -> None:
        """
        Set geometrical reference origin coordinates to (0.0, 0.0, 0.0).
        """
        self.setOrigin()

    def setOrigin(self, origin: vectorFloat3 = (0.0, 0.0, 0.0)) -> None:
        """
        Set geometrical reference origin coordinates.

        Parameters
        ----------
        origin : list[float, float, float] | tuple[float, float, float]
            image origin in world coordinates
        """
        if not self.isEmpty():
            if self._sitk_image.GetDepth() == 2: origin = origin[:2]
            self._sitk_image.SetOrigin(origin)
            # < Revision 15/04/2023
            # self._vtk_image.SetOrigin(origin)
            if self.hasITKImage():
                self._itk_image.SetOrigin(origin)
            # Revision 15/04/2023 >

    def setOriginToCenter(self) -> None:
        """
        Set geometrical reference origin coordinates to image center.
        """
        self.setOrigin(self.getCenter())

    def getOrigin(self) -> vectorFloat3:
        """
        Get geometrical reference origin coordinates.

        Returns
        -------
        tuple[float, float, float]
            image origin in world coordinates
        """
        if not self.isEmpty(): r = self._sitk_image.GetOrigin()
        else:
            if 'origin' in self._attr: r = self._attr['origin']
            else: return 0.0, 0.0, 0.0
        if len(r) == 2: r = (r[0], r[1], 0.0)
        return r

    def isDefaultOrigin(self) -> bool:
        """
        Check whether geometrical reference origin is (0.0, 0.0, 0.0).

        Returns
        -------
        bool
            True if world coordinates origin is (0.0, 0.0, 0.0)
        """
        return self.getOrigin() == (0.0, 0.0, 0.0)

    #  < Revision 21/02/2025
    # add hasSameOrigin method
    def hasSameOrigin(self, origin: vectorFloat3 | SisypheImage | vtkImageData | ANTsImage | sitkImage | str) -> bool:
        """
        Compare origin between the current SisypheImage instance and other image.

        Parameters
        ----------
        origin : SisypheImage | SimpleITK.Image | vtk.vtkImageData | ants.core.ANTsImage | tuple[float, float, float] | list[float, float, float] | ndarray | str
            - get origin from image attribute (SisypheImage, SimpleITK.Image, itk.Image, vtk.vtkImageData, ants.core.ANTsImage),
            - or from a tuple, a list, a numpy.ndarray of three values,
            - or from template tags 'ICBM152', 'ICBM452', 'ATROPOS', 'SRI24'

        Returns
        -------
        bool
            True if same origin
        """
        r = False
        if isinstance(origin, str):
            from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
            if origin == SisypheAcquisition.getICBM152TemplateTag(): origin = (98.0, 134.0, 72.0)
            elif origin == SisypheAcquisition.getICBM452TemplateTag(): origin = (0.0, 0.0, 0.0)
            elif origin == SisypheAcquisition.getATROPOSTemplateTag(): origin = (0.0, 0.0, 0.0)
            elif origin == SisypheAcquisition.getSRI24TemplateTag(): origin = (120.0, 127.0, 68.0)
            else: raise ValueError('{} invalid origin parameter'.format(origin))
        elif isinstance(origin, SisypheImage): origin = origin.getOrigin()
        elif isinstance(origin, sitkImage): origin = origin.GetOrigin()
        elif isinstance(origin, vtkImageData): origin = origin.GetOrigin()
        elif isinstance(origin, ANTsImage): origin = origin.origin
        elif isinstance(origin, ndarray): origin = list(origin)[:3]
        if isinstance(origin, (list, tuple)):
            o = self.getOrigin()
            r = (o[0] == origin[0] and o[1] == origin[1] and o[2] == origin[2])
        return r
    #  Revision 21/02/2025 >

    def getWorldCoordinatesFromVoxelCoordinates(self, p: vectorFloat3) -> vectorFloat3:
        """
        Convert voxel grid coordinates to world coordinates.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            voxel coordinates (image reference)

        Returns
        -------
        tuple[float, float, float]
            world coordinates
        """
        return self._sitk_image.TransformIndexToPhysicalPoint(p)

    def getVoxelCoordinatesFromWorldCoordinates(self, p: vectorFloat3) -> vectorFloat3:
        """
        Convert world coordinates to voxel grid coordinates.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            world coordinates

        Returns
        -------
        tuple[float, float, float]
            voxel coordinates (image reference)
        """
        return self._sitk_image.TransformPhysicalPointToIndex(p)

    # < Revision 26/10/2024
    # add fillWith method
    def fillWith(self, v: float = 0.0) -> None:
        """
        Fill the entire image with a given value.

        Parameters
        ----------
        v : float
            value to fill the image with (default 0.0)
        """
        if self.isIntegerDatatype(): v = int(v)
        self.getNumpy().fill(v)
    # Revision 26/10/2024

    def isEmpty(self) -> bool:
        """
        Check whether image buffer is allocated.

        Returns
        -------
        bool
            True if image buffer is allocated
        """
        return self._sitk_image is None

    def isEmptyArray(self) -> bool:
        """
        Check whether image is empty i.e. all scalar values in the image array are 0.0.

        Returns
        -------
        bool
            True if image is empty
        """
        return self.isEmpty() or self.getNumpy().sum() == 0

    # < Revision 02/01/2025
    # add list[int] and tuple[int, ...] to index type hinting
    def sliceIsEmpty(self, index: int | list[int] | tuple[int, ...], orient: int) -> bool:
        """
        Check whether slices are empty i.e. all scalar values in slices are 0.0.

        Parameters
        ----------
        index : int | list[int] | tuple[int, ...]
            slice indices
        orient : int
            slice orientation code (0 axial, 1 coronal, 2 sagittal)

        Returns
        -------
        bool
            True if slices are empty
        """
        if isinstance(index, int): index = [index]
        # Axial
        if orient == 0:
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in index:
                if self.getNumpy()[i, :, :].sum() != 0: return False
            return True
        # Coronal
        elif orient == 1:
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in index:
                if self.getNumpy()[:, i, :].sum() != 0: return False
            return True
        # Sagittal
        else:
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in index:
                if self.getNumpy()[:, :, i].sum() != 0: return False
            return True
    # Revision 02/01/2025 >

    def getMask(self,
                algo: str = 'huang',
                morpho: str = '',
                niter: int = 1,
                kernel: int = 0,
                fill: str = '2d',
                c: int | None = 0) -> SisypheImage:
        """
        Calc SisypheImage mask of the head.

        Processing stages :
        1. automatic thresholding of background
        2. binary not of background = object
        2. optional stage, iterative binary morphology
        3. keep major blob
        4. optional stage, fill holes ('2d', '3d' or '')

        Parameters
        ----------
        algo : str
            Automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen',
            'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
        morpho : str
            binary morphology operator, 'dilate', 'erode', 'open', 'close' or '' (default, no morphology)
        niter : int
            number of binary morphology iterations (default 1)
        kernel : int
            structuring element size, 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)
        fill : str
            - '2d', fill holes slice by slice
            - '3d', fill holes in 3D
            - '', no filling (default)
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        SisypheImage
            mask
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        # Segment background
        algo = algo.lower()
        # < Revision 16/12/2024
        # multi-component management
        # try:
        #    if algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        #    elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        #    elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        #    elif algo == 'yen': img = sitkYen(self.getSITKImage())
        #    elif algo == 'li': img = sitkLi(self.getSITKImage())
        #    elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        #    elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        #    elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        #    elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        #    elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        #    elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        #    elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        #    else:
        #        # mean threshold
        #        v = self.getNumpy().mean()
        #        img = (self.getSITKImage() <= v)
        # except:
        #    # mean threshold
        #    v = self.getNumpy().mean()
        #    img = (self.getSITKImage() <= v)
        # Revision 16/12/2024 >
        try:
            if algo == 'otsu': img = sitkOtsu(vol.getSITKImage())
            elif algo == 'huang': img = sitkHuang(vol.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(vol.getSITKImage())
            elif algo == 'yen': img = sitkYen(vol.getSITKImage())
            elif algo == 'li': img = sitkLi(vol.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(vol.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(vol.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(vol.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(vol.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(vol.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(vol.getSITKImage())
            elif algo == 'moments': img = sitkMoments(vol.getSITKImage())
            else:
                # mean threshold
                v = vol.getNumpy().mean()
                img = (vol.getSITKImage() <= v)
        except:
            # mean threshold
            v = vol.getNumpy().mean()
            img = (vol.getSITKImage() <= v)
        # mask = not( background )
        img = sitkBinaryNot(img)
        # Morphology operator
        if isinstance(kernel, int):
            # < Revision 06/06/2025
            if kernel == 0:
                if max(vol.getSpacing()) < 1.5: kernel = 2
                else: kernel = 1
            # Revision 06/06/2025 >
            morpho = morpho.lower()
            if morpho in ('dilate', 'erode', 'open', 'close'):
                if morpho in ('dilate', 'erode'):
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(niter):
                        if morpho == 'dilate': img = BinaryDilate(img, [kernel, kernel, kernel])
                        elif morpho == 'erode': img = BinaryErode(img, [kernel, kernel, kernel])
                elif morpho == 'open': img = BinaryMorphologicalOpening(img, [kernel, kernel, kernel])
                else: img = BinaryMorphologicalClosing(img, [kernel, kernel, kernel])
            else: raise ValueError('Invalid morphology operator ({})'.format(morpho))
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        # < Revision 19/12/2024
        # keep major blob (remove blobs in head/brain)
        blobs = sitkConnectedComponent(img)
        blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
        img = blobs == 1
        # Revision 19/12/2024 >
        # Filling
        if fill == '2d':
            f = BinaryFillholeImageFilter()
            # noinspection PyUnresolvedReferences
            i: cython.int
            # noinspection PyUnresolvedReferences
            for i in range(img.GetSize()[2]):
                slc = img[:, :, i]
                slc = f.Execute(slc)
                img[:, :, i] = slc
        elif fill == '3d':
            img = BinaryFillhole(img)
        return SisypheImage(img)

    # < Revision 23/10/2024
    # add getROI method
    def getROI(self,
               threshold: float = 0.5,
               op: str = '>',
               c: int | None = 0) -> SisypheROI:
        """
        Converting current SisypheImage instance to Sisyphe.core.sisypheROI.SisypheROI using a threshold.

        Parameters
        ----------
        threshold  : float
            threshold for binarization (default 0.5)
        op : str
            comparison operator: '>' (default), '>=', '<', '<=', '==', '!=', '0<' (0 < x < threshold), '0<='
            (0 < x <= threshold)
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        from Sisyphe.core.sisypheROI import SisypheROI
        roi = SisypheROI()
        # < Revision 16/12/2024
        # multi-component management
        # roi.setSITKImage(self.getSITKImage() > threshold)
        # < Revision 20/12/2024
        # add comparison operator
        # roi.setSITKImage(vol.getSITKImage() > threshold)
        if op == '>':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() > threshold)
        elif op == '>=':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() >= threshold)
        elif op == '<':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() < threshold)
        elif op == '0<':
            # noinspection PyTypeChecker
            roi.setSITKImage((vol.getSITKImage() > 0) * (vol.getSITKImage() < threshold))
        elif op == '<=':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() <= threshold)
        elif op == '0<=':
            # noinspection PyTypeChecker
            roi.setSITKImage((vol.getSITKImage() > 0) * (vol.getSITKImage() <= threshold))
        elif op == '==':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() == threshold)
        elif op == '!=':
            # noinspection PyTypeChecker
            roi.setSITKImage(vol.getSITKImage() != threshold)
        else: raise ValueError('invalid comparison operator {}'.format(op))
        # Revision 20/12/2024 >
        # Revision 16/12/2024 >
        return roi
    # Revision 23/10/2024>

    def getMask2(self,
                 algo: str = 'huang',
                 morphoiter: int = 2,
                 kernel: int = 0,
                 c: int | None = 0) -> SisypheImage:
        """
        Calc SisypheImage mask of the head.

        Processing stages :
        1. automatic thresholding of background
        2. erode background
        3. keep major blob (i.e.remove blobs in head/object)
        4. dilate background
        5. binary not of background = object
        6. erode object
        7. keep major blob (i.e.remove background blobs in head/object)
        8. dilate object

        Parameters
        ----------
        algo : str
            Automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen',
            'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
        morphoiter : int
            number of binary morphology iterations (default 2)
        kernel : int
            structuring element size, 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        SisypheImage
            mask
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        # Segment background
        algo = algo.lower()
        # < Revision 16/12/2024
        # multi-component management
        # try:
        #    if algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        #    elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        #    elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        #    elif algo == 'yen': img = sitkYen(self.getSITKImage())
        #    elif algo == 'li': img = sitkLi(self.getSITKImage())
        #    elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        #    elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        #    elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        #    elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        #    elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        #    elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        #    elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        #    else:
        #        # mean threshold
        #        v = self.getNumpy().mean()
        #        img = (self.getSITKImage() <= v)
        # except:
        #    # mean threshold
        #    v = self.getNumpy().mean()
        #    img = (self.getSITKImage() <= v)
        try:
            if algo == 'otsu': img = sitkOtsu(vol.getSITKImage())
            elif algo == 'huang': img = sitkHuang(vol.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(vol.getSITKImage())
            elif algo == 'yen': img = sitkYen(vol.getSITKImage())
            elif algo == 'li': img = sitkLi(vol.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(vol.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(vol.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(vol.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(vol.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(vol.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(vol.getSITKImage())
            elif algo == 'moments': img = sitkMoments(vol.getSITKImage())
            else:
                # mean threshold
                v = vol.getNumpy().mean()
                img = (vol.getSITKImage() <= v)
        except:
            # mean threshold
            v = vol.getNumpy().mean()
            img = (vol.getSITKImage() <= v)
        # Revision 16/12/2024 >
        # Background processing
        if isinstance(kernel, int):
            if kernel == 0:
                if max(vol.getSpacing()) < 1.5: kernel = 2
                else: kernel = 1
            # Erode
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
            # keep major blob (remove blobs in head/brain)
            blobs = sitkConnectedComponent(img)
            blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
            img = blobs == 1
            # Dilate
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryDilate(img, [kernel, kernel, kernel])
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
                    img = BinaryErode(img, [kernel, kernel, kernel])
            # keep major blob (remove blobs in head/brain)
            blobs = sitkConnectedComponent(img)
            blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
            img = blobs == 1
            # Dilate
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryDilate(img, [kernel, kernel, kernel])
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        return SisypheImage(img)

    def getMaskROI(self,
                   algo: str = 'huang',
                   morpho: str = '',
                   niter: int = 1,
                   kernel: int = 0,
                   fill: str = '2d',
                   c: int | None = 0) -> SisypheROI:
        """
        Calc Sisyphe.core.sisypheROI.SisypheROI mask of the head.

        Parameters
        ----------
        algo : str
            Automatic thresholding algorithm used for background segmentation:  'mean', 'otsu', 'huang', 'renyi', 'yen',
            'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
        morpho : str
            binary morphology operator, 'dilate', 'erode', 'open', 'close' or '' (default, no morphology)
        niter : int
            number of binary morphology iterations (default 1)
        kernel : int
            structuring element size (default 0, no morphology)
        fill : str
            - '2d', fill holes slice by slice
            - '3d', fill holes in 3D
            - '', no filling
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            mask
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        from Sisyphe.core.sisypheROI import SisypheROI
        # Segment background
        algo = algo.lower()
        fill = fill.lower()
        # < Revision 16/12/2024
        # multi-component management
        # try:
        #    if algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        #    elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        #    elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        #    elif algo == 'yen': img = sitkYen(self.getSITKImage())
        #    elif algo == 'li': img = sitkLi(self.getSITKImage())
        #    elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        #    elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        #    elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        #    elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        #    elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        #    elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        #    elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        #    else:
        #        # mean threshold
        #        v = self.getNumpy().mean()
        #        img = (self.getSITKImage() <= v)
        # except:
        #    # mean threshold
        #    v = self.getNumpy().mean()
        #    img = (self.getSITKImage() <= v)
        try:
            if algo == 'otsu': img = sitkOtsu(vol.getSITKImage())
            elif algo == 'huang': img = sitkHuang(vol.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(vol.getSITKImage())
            elif algo == 'yen': img = sitkYen(vol.getSITKImage())
            elif algo == 'li': img = sitkLi(vol.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(vol.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(vol.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(vol.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(vol.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(vol.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(vol.getSITKImage())
            elif algo == 'moments': img = sitkMoments(vol.getSITKImage())
            else:
                # mean threshold
                v = vol.getNumpy().mean()
                img = (vol.getSITKImage() <= v)
        except:
            # mean threshold
            v = vol.getNumpy().mean()
            img = (vol.getSITKImage() <= v)
        # Revision 16/12/2024 >
        # mask = not( background )
        img = sitkBinaryNot(img)
        # Morphology operator
        if isinstance(kernel, int):
            if kernel > 0 and morpho in ('dilate', 'erode', 'open', 'close'):
                morpho = morpho.lower()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(niter):
                    if morpho == 'dilate': img = BinaryDilate(img, [kernel, kernel, kernel])
                    elif morpho == 'erode': img = BinaryErode(img, [kernel, kernel, kernel])
                    elif morpho == 'open':
                        # noinspection PyUnusedLocal
                        img = BinaryMorphologicalOpening(img, [kernel, kernel, kernel])
                        break
                    elif morpho == 'close':
                        # noinspection PyUnusedLocal
                        img = BinaryMorphologicalClosing(img, [kernel, kernel, kernel])
                        break
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
        elif fill == '3d':
            img = BinaryFillhole(img)
        return SisypheROI(img)

    def getMaskROI2(self,
                    algo: str = 'huang',
                    morphoiter: int = 2,
                    kernel: int = 0,
                    c: int | None = 0) -> SisypheROI:
        """
        Calc Sisyphe.core.sisypheROI.SisypheROI mask of the head.

        Parameters
        ----------
        algo : str
            Automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen',
            'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
        morphoiter : int
            number of binary morphology iterations
        kernel : int
            structuring element size, 0 automatic value (kernel=2 if spacing < 1.5 mm, kernel=1 otherwise)
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            mask
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        from Sisyphe.core.sisypheROI import SisypheROI
        # Segment background
        algo = algo.lower()
        # < Revision 16/12/2024
        # multi-component management
        # try:
        #    if algo == 'otsu': img = sitkOtsu(self.getSITKImage())
        #    elif algo == 'huang': img = sitkHuang(self.getSITKImage())
        #    elif algo == 'renyi': img = sitkRenyi(self.getSITKImage())
        #    elif algo == 'yen': img = sitkYen(self.getSITKImage())
        #    elif algo == 'li': img = sitkLi(self.getSITKImage())
        #    elif algo == 'shanbhag': img = sitkShanbhag(self.getSITKImage())
        #    elif algo == 'triangle': img = sitkTriangle(self.getSITKImage())
        #    elif algo == 'intermodes': img = sitkIntermodes(self.getSITKImage())
        #    elif algo == 'maximumentropy': img = sitkMaximumEntropy(self.getSITKImage())
        #    elif algo == 'kittler': img = sitkKittler(self.getSITKImage())
        #    elif algo == 'isodata': img = sitkIsoData(self.getSITKImage())
        #    elif algo == 'moments': img = sitkMoments(self.getSITKImage())
        #    else:
        #        # mean threshold
        #        v = self.getNumpy().mean()
        #        img = (self.getSITKImage() <= v)
        # except:
        #    # mean threshold
        #    v = self.getNumpy().mean()
        #    img = (self.getSITKImage() <= v)
        try:
            if algo == 'otsu': img = sitkOtsu(vol.getSITKImage())
            elif algo == 'huang': img = sitkHuang(vol.getSITKImage())
            elif algo == 'renyi': img = sitkRenyi(vol.getSITKImage())
            elif algo == 'yen': img = sitkYen(vol.getSITKImage())
            elif algo == 'li': img = sitkLi(vol.getSITKImage())
            elif algo == 'shanbhag': img = sitkShanbhag(vol.getSITKImage())
            elif algo == 'triangle': img = sitkTriangle(vol.getSITKImage())
            elif algo == 'intermodes': img = sitkIntermodes(vol.getSITKImage())
            elif algo == 'maximumentropy': img = sitkMaximumEntropy(vol.getSITKImage())
            elif algo == 'kittler': img = sitkKittler(vol.getSITKImage())
            elif algo == 'isodata': img = sitkIsoData(vol.getSITKImage())
            elif algo == 'moments': img = sitkMoments(vol.getSITKImage())
            else:
                # mean threshold
                v = vol.getNumpy().mean()
                img = (vol.getSITKImage() <= v)
        except:
            # mean threshold
            v = vol.getNumpy().mean()
            img = (vol.getSITKImage() <= v)
        # Revision 16/12/2024 >
        # Background processing
        if isinstance(kernel, int):
            if kernel == 0:
                if max(vol.getSpacing()) < 1.5: kernel = 2
                else: kernel = 1
            # Erode
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryErode(img, [kernel, kernel, kernel])
            # keep major blob (remove blobs in head/brain)
            blobs = sitkConnectedComponent(img)
            blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
            img = blobs == 1
            # Dilate
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryDilate(img, [kernel, kernel, kernel])
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
                    img = BinaryErode(img, [kernel, kernel, kernel])
            # keep major blob (remove blobs in head/brain)
            blobs = sitkConnectedComponent(img)
            blobs = sitkRelabelComponent(blobs, sortByObjectSize=True)
            img = blobs == 1
            # Dilate
            if morphoiter > 0:
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(morphoiter):
                    img = BinaryDilate(img, [kernel, kernel, kernel])
        else: raise TypeError('kernel parameter type {} is not int.'.format(type(kernel)))
        return SisypheROI(img)

    # < Revision 14/01/2025
    # add replaceNanInfValues method
    def replaceNanInfValues(self, nan: float = 0.0, posinf: float = 0.0, neginf: float = 0.0) -> None:
        """
        Replace NaN and Inf values with a given values.

        Parameters
        ----------
        nan : float, optional
            value to replace NaN (default 0.0)
        posinf : float, optional
            value to replace positive infinity (default 0.0)
        neginf : float, optional
            value to replace negative infinity (default 0.0)
        """
        origin = self.getOrigin()
        spacing = self.getSpacing()
        direction = self.getDirections()
        v = nan_to_num(self.getNumpy(), nan=nan, posinf=posinf, neginf=neginf)
        self.copyFromNumpyArray(v, spacing=spacing, origin=origin, direction=direction)
    # Revision 14/01/2025 >

    # < Revision 03/06/2025
    def getRelabeled(self, cross: dict[int, int]) -> SisypheImage:
        """
        Get a relabeled SisypheImage of the current SisypheImage instance.

        Parameters
        ----------
        cross : dict[int, int]
            - label value mapping table between current image and relabeled image
            - key: label value in the current image
            - value: new label value in the relabeled image

        Returns
        -------
        SisypheImage
            relabeled image
        """
        img1 = self.getNumpy(defaultshape=True)
        img2 = zeros(shape=img1.shape, dtype=img1.dtype)
        for v1 in cross:
            v2 = cross[v1]
            img2[img1 == v1] = v2
        r = SisypheImage()
        r.copyFromNumpyArray(img2, spacing=self.getSpacing(), origin=self.getOrigin(),
                             direction=self.getDirections(), defaultshape=True)
        return r
    # Revision 03/06/2025 >

    # < Revision 19/11/2024
    # add getNonZeroMask method
    def getNonZeroMask(self, c: int | None = 0) -> SisypheImage:
        """
        Calc SisypheImage mask of non-zero voxels of the current SisypheImage instance.

        Parameters
        ----------
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        SisypheImage
            mask
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        r = SisypheImage()
        # < Revision 27/11/2024
        # r.setSITKImage(self.getSITKImage() > 0.0)
        # noinspection PyTypeChecker
        r.setSITKImage(vol.getSITKImage() != 0.0)
        # Revision 27/11/2024 >
        return r
    # Revision 19/11/2024 >

    # < Revision 17/10/2024
    # add getCentroid method
    def getCentroid(self, binary: bool = False, ref: str = 'world', c: int | None = 0) -> tuple[float, ...]:
        """
        Get centroid of the image as world coordinates.

        Parameters
        ----------
        binary : bool
            Processing on a binary mask if True, or greyscale image (as weights) if False
        ref : str
            reference of returned coordinates
                - 'world' world coordinates
                - 'array' array coordinates
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        tuple[float, ...]
            centroid coordinates
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        # Revision 16/12/2024 >
        if binary: img = vol.getMask().getNumpy(defaultshape=False)
        else: img = vol.getNumpy(defaultshape=False)
        # noinspection PyTypeChecker
        p = centroid(img, spacing=vol.getSpacing())
        # < Revision 13/06/2025
        if ref == 'array': p = trunc(p / vol.getSpacing())
        # Revision 13/06/2025 >
        return tuple(p.tolist())
    # Revision 17/10/2024 >

    def getBackgroundThreshold(self, algo: str = 'mean', c: int | None = 0) -> float:
        """
        Calc threshold to segment background.

        Parameters
        ----------
        algo : str
            Automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen',
            'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        float
            threshold to segment background
        """
        # < Revision 16/12/2024
        # multi-component management
        n = self.getNumberOfComponentsPerPixel()
        if n == 1: vol = self
        else:
            if c is None: vol = self.getComponentMean()
            else: vol = self.copyComponent(c)
        algo = algo.lower()
        if algo == 'otsu': f = OtsuThresholdImageFilter()
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
        # else: return self.getNumpy().mean()
        else: return vol.getNumpy().mean()
        if f is not None:
            try:
                # f.Execute(self.getSITKImage())
                f.Execute(vol.getSITKImage())
                return f.GetThreshold()
            # except: return self.getNumpy().mean()
            except: return vol.getNumpy().mean()
        else: raise ValueError('Invalid algo parameter.')
        # Revision 16/12/2024 >

    # < Revision 29/07/2024
    # add getCrop method
    # noinspection PyTypeChecker
    def getCrop(self, c: tuple | list | ndarray, ) -> SisypheImage:
        """
        Get a cropped image of the current SisypheVolume instance.

        Parameters
        ----------
        c : tuple | list
            xmin, xmax, ymin, ymax, zmin, zmax

        Returns
        -------
        SisypheImage
            cropped image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            xmin = c[0]
            xmax = c[1]
            ymin = c[2]
            ymax = c[3]
            zmin = c[4]
            zmax = c[5]
            if xmin < 0: xmin = 0
            if ymin < 0: ymin = 0
            if zmin < 0: zmin = 0
            s = self.getSize()
            if xmax > s[0]: xmax = s[0]
            if ymax > s[1]: ymax = s[1]
            if zmax > s[2]: zmax = s[2]
            r = self[xmin:xmax, ymin:ymax, zmin:zmax]
            # < Revision 25/10/2024
            # spacing factor
            # origin[0] += xmin
            # origin[1] += ymin
            # origin[2] += zmin
            s = self.getSpacing()
            origin = self.getOrigin()
            # Revision 16/12/2024 >
            origin[0] -= xmin * s[0]
            origin[1] -= ymin * s[1]
            origin[2] -= zmin * s[2]
            r.setOrigin(origin)
            return r
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 29/07/2024 >

    # < Revision 29/07/2024
    # add getBoundingBox method
    # noinspection PyTypeChecker
    def getBoundingBox(self, threshold: float = 0.0, margin: int = 0, blobs: bool = False) -> ndarray:
        """
        Get the bounding box a thresholded image of the current SisypheVolume instance.

        Parameters
        ----------
        threshold : float
            threshold applied to scalar image (default 0.0)
        margin : int
            isotropic margin added to the bounding box (in voxels, default 0 i.e. no margin)
        blobs : bool
            bounding box of the whole image if False, of each image blob if True

        Returns
        -------
        ndarray
            - if blobs is False, 6 elements ndarray: xmin, xmax, ymin, ymax, zmin, zmax
            - if blobs is True, 6 elements ndarray for each blob of the thresholded image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img = self.getSITKImage() > threshold
            if blobs: img = sitkConnectedComponent(self.getSITKImage() > threshold)
            np = sitkGetArrayFromImage(img).T
            n = np.flatten().max()
            bb = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(1, n+1):
                # < Revision 25/10/2024
                # bugfix
                # np = (np == blobs)
                np = (np == i)
                # Revision 25/10/2024 >
                c = argwhere(np)
                cmin = npmin(c, axis=0)
                cmax = npmax(c, axis=0)
                xmin = cmin[0] - margin
                ymin = cmin[1] - margin
                zmin = cmin[2] - margin
                xmax = cmax[0] + margin + 1
                ymax = cmax[1] + margin + 1
                zmax = cmax[2] + margin + 1
                if xmin < 0: xmin = 0
                if ymin < 0: ymin = 0
                if zmin < 0: zmin = 0
                # noinspection PyUnresolvedReferences
                s = np.shape
                if xmax > s[0]: xmax = s[0]
                if ymax > s[1]: ymax = s[1]
                if zmax > s[2]: zmax = s[2]
                r = array([xmin, xmax, ymin, ymax, zmin, zmax])
                bb.append(r)
            if len(bb) == 1: return bb[0]
            else: return array(bb)
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 29/07/2024 >

    # < Revision 29/07/2024
    # add getLocalMaxima method
    # noinspection PyTypeChecker
    def getLocalMaxima(self, threshold: float) -> ndarray:
        """
        Get the local maxima of the current SisypheVolume instance.

        Determine all maxima of the image with height >= threshold. The local maxima are defined as connected sets
        of voxels with equal scalar value strictly greater than the scalar value of all voxels in direct neighborhood
        of the set. A local maximum M of height threshold is a local maximum for which there is at least one path
        joining M with an equal or higher local maximum on which the minimal value is f(M) - h (i.e. the values along
        the path are not decreasing by more than h with respect to the maximum’s value) and no path to an equal or
        higher local maximum for which the minimal value is greater.

        Parameters
        ----------
        threshold : float
            local maxima threshold

        Returns
        -------
        ndarray
            coordinates of the local maxima
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img = self.getNumpy(defaultshape=False)
            return argwhere(h_maxima(img, threshold))
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 29/07/2024 >

    # < Revision 01/08/2024
    # add getProjection method
    def getProjection(self,
                      d: str = 'left',
                      thickness: float = 0.0,
                      func: str = 'max',
                      output: str = 'native',
                      emask: SisypheImage | None = None) -> sitkImage | ndarray | SisypheImage:
        """
        Get a 2D projection of the current SisypheImage instance.
        The projection is processed to a depth expressed in mm from the head surface (default 0.0, whole brain,
        no thickness). Operators applied to voxels on a projection line: maximum, mean, median, standard deviation, sum.

        Parameters
        ----------
        d : str
            direction of the projection: 'left', 'right', 'ant', 'post', 'top', 'bottom'
        thickness: float
            projection by a given thickness in mm (default 0.0, whole brain, no thickness)
        func : str
            'max', 'mean', 'median', 'std', 'sum', 'label'
        output : str
            output format: 'numpy' numpy.ndarray, 'sitk' SimpleITK.Image, 'native' SisypheImage
        emask : SisypheImage
            if mask is None (default), mask is processed from the current SisypheImage instance (automatic thresholding
            with Huang algorithm for grayscale images, or non-zero voxels for label images). if an explicit mask is
            given, array size must match the current SisypheImage instance.

        Returns
        -------
        SimpleITK.Image | numpy.ndarray | SisypheImage
            - SimpleITK.Image if func = 'sitk',
            - numpy.ndarray if func = 'numpy',
            - SisypheImage if func = 'native'
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            s = self.getSpacing()
            # < Revision 21/11/2024
            # add explicit mask parameter
            if emask is None:
                # < Revision 08/11/2024
                # bugfix, threshold to 0 for label image
                if func == 'label':
                    # noinspection PyTypeChecker
                    mask = sitkGetArrayFromImage(self.getSITKImage() > 0).T
                    func = 'max'
                # Revision 08/11/2024 >
                else:
                    # Mask, automatic thresholding with Huang algorithm
                    try:
                        # noinspection PyUnusedLocal
                        mask = sitkGetArrayFromImage(sitkHuang(self.getSITKImage(), 0, 1)).T
                    # < Revision 06/12/2024
                    except:
                        v = self.getNumpy().mean()
                        # noinspection PyTypeChecker
                        mask = sitkGetArrayFromImage(self.getSITKImage() > v).T
                    # Revision 06/12/2024 >
            else: mask = sitkGetArrayFromImage(emask.getSITKImage() > 0).T
            # Revision 21/11/2024 >
            if d == 'left':
                ax = 0
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            elif d == 'right':
                ax = 0
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[::-1, :, :]  # flip x
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[::-1, :, :]  # flip x
            elif d == 'ant':
                ax = 1
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[:, ::-1, :]  # flip y
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[:, ::-1, :]  # flip y
            elif d == 'post':
                ax = 1
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            elif d == 'top':
                ax = 2
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[:, :, ::-1]  # flip z
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[:, :, ::-1]  # flip z
            elif d == 'bottom':
                ax = 2
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            else: raise ValueError('Invalid direction parameter ({})'.format(d))
            img = (self.getNumpy(defaultshape=False) * mask).astype('float32')
            if func == 'max':
                r = npmax(img, axis=ax)
            elif func == 'mean':
                # < Revision 13/10/2024
                # img[img == 0.0] = npnan
                # r = nanmean(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_mean(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'median':
                # img[img == 0.0] = npnan
                # r = nanmedian(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_median(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'std':
                # img[img == 0.0] = npnan
                # r = nanstd(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_std(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'sum':
                r = img.sum(axis=ax)
            else: raise ValueError('Invalid function parameter ({})'.format(func))
            # Flip left/right for right, top and post projections
            if d in ('right', 'top', 'post'): r = flipud(r)
            if output == 'numpy': return r.T
            elif output == 'sitk':
                r = sitkGetImageFromArray(r.T)
                if ax == 0: r.SetSpacing([s[1], s[2]])
                elif ax == 1: r.SetSpacing([s[0], s[2]])
                else: r.SetSpacing([s[0], s[1]])
                return r
            elif output == 'native':
                sh = r.shape
                # < Revision 12/10/2024
                # r = r.reshape(shape=(sh[0], sh[1], 1))
                r = r.reshape((sh[0], sh[1], 1))
                # Revision 12/10/2024 >
                img = SisypheImage()
                img.copyFromNumpyArray(r, defaultshape=False)
                if ax == 0: img.setSpacing(s[1], s[2], 1.0)
                elif ax == 1: img.setSpacing(s[0], s[2], 1.0)
                else: img.setSpacing(s[0], s[1], 1.0)
                return img
            else: raise ValueError('Invalid output parameter ({})'.format(func))
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 01/08/2024 >

    # < Revision 30/08/2024
    # add getCroppedProjection method
    def getCroppedProjection(self,
                             slc: int,
                             d: str = 'left',
                             thickness: float = 0.0,
                             func: str = 'max',
                             output: str = 'native',
                             emask: SisypheImage | None = None) -> sitkImage | ndarray | SisypheImage:
        """
        Get a 2D projection of the current SisypheVolume instance.
        The projection is processed to a depth expressed in mm from the head surface (default 0.0, whole brain, no
        thickness). Operators applied to voxels on a projection line: maximum, mean, median, standard deviation, sum.
        The volume can be cut out to a specified depth (slice index) in the direction of projection.

        Parameters
        ----------
        slc : int
            cutting plan (orientation is given by d parameter, see below)
        d : str
            direction of the projection: 'left', 'right', 'ant', 'post', 'top', 'bottom'
        thickness: float
            projection by a given thickness in mm (default 0.0, whole brain, no thickness)
        func : str
            'max', 'mean', 'median', 'std', 'sum'
        output : str
            output format: 'numpy' numpy.ndarray, 'sitk' SimpleITK.Image, 'native' SisypheImage
        emask : SisypheImage
            if mask is None (default), mask is processed from the current SisypheImage instance (automatic thresholding
            with Huang algorithm for grayscale images, or non-zero voxels for label images). if an explicit mask is
            given, array size must match the current SisypheImage instance.

        Returns
        -------
        SimpleITK.Image | numpy.ndarray | SisypheImage
            - SimpleITK.Image if func = 'sitk',
            - numpy.ndarray if func = 'numpy',
            - SisypheImage if func = 'native'
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            s = self.getSpacing()
            # < Revision 21/11/2024
            # add explicit mask parameter
            if emask is None:
                # < Revision 08/11/2024
                # bugfix, threshold to 0 for label image
                if func == 'label':
                    # noinspection PyTypeChecker
                    mask = sitkGetArrayFromImage(self.getSITKImage() > 0).T
                    func = 'max'
                # Revision 08/11/2024 >
                else:
                    # Mask, automatic thresholding with Huang algorithm
                    try:
                        # noinspection PyUnusedLocal
                        mask = sitkGetArrayFromImage(sitkHuang(self.getSITKImage(), 0, 1)).T
                    # < Revision 06/12/2024
                    except:
                        v = self.getNumpy().mean()
                        # noinspection PyTypeChecker
                        mask = sitkGetArrayFromImage(self.getSITKImage() > v).T
                    # Revision 06/12/2024 >
            else: mask = sitkGetArrayFromImage(emask.getSITKImage() > 0).T
            # Revision 21/11/2024 >
            if d == 'left':
                mask[:slc, :, :] = 0
                ax = 0
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            elif d == 'right':
                mask[slc:-1, :, :] = 0
                ax = 0
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[::-1, :, :]  # flip x
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[::-1, :, :]  # flip x
            elif d == 'ant':
                mask[:, slc:-1, :] = 1
                ax = 1
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[:, ::-1, :]  # flip y
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[:, ::-1, :]  # flip y
            elif d == 'post':
                mask[:, :slc, :] = 1
                ax = 1
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            elif d == 'top':
                mask[:, :, slc:-1] = 1
                ax = 2
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    mask = mask[:, :, ::-1]  # flip z
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
                    mask = mask[:, :, ::-1]  # flip z
            elif d == 'bottom':
                mask[:, :, slc] = 1
                ax = 2
                if thickness > 0.0:
                    thickness = (thickness // s[ax]) + 1
                    csum = mask.cumsum(axis=ax) > 0
                    csum = csum.cumsum(axis=ax)
                    mask = mask * (csum <= thickness)
            else:
                raise ValueError('Invalid direction parameter ({})'.format(d))
            img = (self.getNumpy(defaultshape=False) * mask).astype('float32')
            if func == 'max':
                r = npmax(img, axis=ax)
            elif func == 'mean':
                # < Revision 13/10/2024
                # img[img == 0.0] = npnan
                # r = nanmean(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_mean(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'median':
                # img[img == 0.0] = npnan
                # r = nanmedian(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_median(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'std':
                # img[img == 0.0] = npnan
                # r = nanstd(img, axis=ax)
                # using numpy masked array
                img = masked_equal(img, 0.0)
                r = ma_std(img, axis=ax)
                r = filled(r, 0.0)
                # Revision 13/10/2024 >
            elif func == 'sum':
                r = img.sum(axis=ax)
            else:
                raise ValueError('Invalid function parameter ({})'.format(func))
            # Flip left/right for right, top and post projections
            if d in ('right', 'top', 'post'): r = flipud(r)
            if output == 'numpy':
                return r.T
            elif output == 'sitk':
                r = sitkGetImageFromArray(r.T)
                if ax == 0: r.SetSpacing([s[1], s[2]])
                elif ax == 1: r.SetSpacing([s[0], s[2]])
                else: r.SetSpacing([s[0], s[1]])
                return r
            elif output == 'native':
                sh = r.shape
                # < Revision 12/10/2024
                # r = r.reshape(shape=(sh[0], sh[1], 1))
                r = r.reshape((sh[0], sh[1], 1))
                # Revision 12/10/2024 >
                img = SisypheImage()
                img.copyFromNumpyArray(r, defaultshape=False)
                if ax == 0: img.setSpacing(s[1], s[2], 1.0)
                elif ax == 1: img.setSpacing(s[0], s[2], 1.0)
                else: img.setSpacing(s[0], s[1], 1.0)
                return img
            else: raise ValueError('Invalid output parameter ({})'.format(func))
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 30/08/2024 >

    # < Revision 04/09/2024
    # add headSurface method
    # noinspection PyTypeChecker
    def sliceHeadSurface(self, orient: str = 'e') -> dict[str, list]:
        """
        Get head surface (number of pixels) in each slice of the current SisypheImage instance.

        Parameters
        ----------
        orient : str
            slice orientation ('a' axial, 'c' coronal, 's' sagittal, 'e' every orientation default)

        Returns
        -------
        dict[str, list]
            - keys: 'a' axial results, 'c' coronal results, 's' sagittal results
            - dict value is list with four elements
            - first element = int, index of the slice with the maximum head surface
            - second element = int, index of the first slice with non-zero head surface
            - third element = int, index of the last slice with non-zero head surface
            - fourth element = numpy.ndarray, head surface (number of pixels) of each slice
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            r = dict()
            orient = orient[0].lower()
            mask = sitkGetArrayFromImage(sitkHuang(self.getSITKImage(), 0, 1)).T
            if orient in ('a', 'e'):
                s = mask.sum(axis=0).sum(axis=0)
                r['a'] = list()
                r['a'].append(int(s.argmax()))
                v = argwhere(s > 0)
                r['a'].append(int(v[0][0]))
                r['a'].append(int(v[-1][0]))
                r['a'].append(s)
            if orient in ('c', 'e'):
                s = mask.sum(axis=0).sum(axis=1)
                r['c'] = list()
                r['c'].append(int(s.argmax()))
                v = argwhere(s > 0)
                r['c'].append(int(v[0][0]))
                r['c'].append(int(v[-1][0]))
                r['c'].append(s)
            if orient in ('s', 'e'):
                s = mask.sum(axis=1).sum(axis=1)
                r['s'] = list()
                r['s'].append(int(s.argmax()))
                v = argwhere(s > 0)
                r['s'].append(int(v[0][0]))
                r['s'].append(int(v[-1][0]))
                r['s'].append(s)
            if len(r) == 0:
                raise ValueError('Invalid orientation \'{}\' (\'a\', \'c\', \'s\' or \'e\')'.format(orient))
            return r
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 04/09/2024 >

    # < Revision 04/10/2024
    # add removeNeckSlices method
    # noinspection PyTypeChecker
    def removeNeckSlices(self, f: float = 1.8) -> SisypheImage:
        """
        Get a new SisypheImage instance, cropped in z. Most sagittal MRI scans have extensive and useless inferior
        coverage. This function crop MR volume in z direction, removing empty slices and lower slices of neck below
        foramen magnum.

        Parameters
        ----------
        f : float
            multiplicative factor to adjust the neck slice. Lower values remove more slices, higher values keep more
            slices (between 1.5 and 2.0, default 1.8 close to the foramen magnum for most MR images)

        Returns
        -------
        SisypheImage
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            if f > 2.0: f = 2.0
            elif f < 1.5: f = 1.5
            r = self.sliceHeadSurface('a')
            sup = r['a'][2]
            n = sup - r['a'][0]
            inf = sup - int(f * n)
            if inf < r['a'][1]: inf = r['a'][1]
            return self[:, :, inf:sup+1]
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 04/10/2024 >

    # Descriptive statistics public methods

    # < Revision 08/09/2024
    #  add noiseEstimate method
    def noiseEstimate(self) -> float:
        """
        Estimator of the (Gaussian) noise standard deviation.

        Returns
        -------
        float
            noise standard deviation
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            return float(estimate_sigma(self.getNumpy(defaultshape=False)))
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 08/09/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getMean(self,
                mask: str | SisypheImage | SisypheBinaryImage | None = None,
                c: int | None = 0) -> float | list[float]:
        """
        Get mean of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process
            - None, all components processed. In this case, the method returns a list of mean values of each component
            of the multi-component image

        Returns
        -------
        float | list[float]
            - mean value for single-component image
            - mean value for multi-component image, if component index c is int (default 0)
            - list of mean values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        # Mean processing
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            return float(mean(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(mean(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getMedian(self,
                  mask: str | SisypheImage | SisypheBinaryImage | None = None,
                  c: int | None = 0) -> float | list[float]:
        """
        Get median of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process
            - None, all components processed. In this case, the method returns a list of median values of each component
            of the multi-component image

        Returns
        -------
        float | list[float]
            - median value for single-component image
            - median value for multi-component image, if component index c is int (default 0)
            - list of median values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Median processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            return float(median(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(median(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getStd(self,
               mask: str | SisypheImage | SisypheBinaryImage | None = None,
               c: int | None = 0) -> float | list[float]:
        """
        Get standard deviation of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process
            - None, all components processed. In this case, the method returns a list of standard deviation values of
            each component of the multi-component image

        Returns
        -------
        float | list[float]
            - standard deviation value for single-component image
            - standard deviation value for multi-component image, if component index c is int (default 0)
            - list of standard deviation values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Median processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            return float(std(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(std(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getMin(self,
               nonzero: bool = False,
               c: int | None = 0) -> float | list[float]:
        """
        Get min of image. Processing can be performed on non-zero values.

        Parameters
        ----------
        nonzero : bool
            exclude zero values if True
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process
            - None, all components processed. In this case, the method returns a list of min values of each component
            of the multi-component image

        Returns
        -------
        float | list[float]
            - min value for single-component image
            - min value for multi-component image, if component index c is int (default 0)
            - list of min values of each component of a multi-component image, if component index c is None
        """
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        if n == 1:
            img = self.getNumpy().flatten()
            if nonzero: img = img[img > 0]
            return float(std(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if nonzero: img = img[img > 0]
                r.append(float(std(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getMax(self,
               mask: str | SisypheImage | SisypheBinaryImage | None = None,
               c: int | None = 0) -> float | list[float]:
        """
        Get max of image. Calculation can only be performed on non-zero values.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process
            - None, all components processed. In this case, the method returns a list of max values of each component
            of the multi-component image

        Returns
        -------
        float | list[float]
            - max value for single-component image
            - max value for multi-component image, if component index c is int (default 0)
            - list of max values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Max processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            # noinspection PyArgumentList
            return float(img.max())
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(img.max()))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    def getArgmax(self,
                  mask: str | SisypheImage | SisypheBinaryImage | None = None) -> tuple[int, ...] | list[tuple[int, ...]]:
        """
        Get the coordinates of the highest scalar value.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image

        Returns
        -------
        tuple[int, int, int] | list[tuple[int, int, int]]
            x, y, z or list[(x, y, z)] for multicomponent image
        """
        img = self.getNumpy()
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask).getNumpy()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                # < Revision 04/03/2025
                # m = m.astype('uint8').flatten()
                m = m.astype('uint8')
                # Revision 04/03/2025 >
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            # < Revision 04/03/2025
            # img = img * m
            # Revision 04/03/2025 >
        c = 0
        r = list()
        n = self.getNumberOfComponentsPerPixel()
        while c < n:
            if n == 1:
                np = img
                if np.ndim == 2:
                    s = np.shape
                    # noinspection PyArgumentList
                    np = np.reshape(shape=(1, s[0], s[1]))
                c = n
            else:
                # n > 1, multicomponent image
                # < Revision 04/03/2025
                # np = img.getNumpy()[c, :, :, :]
                np = self.getNumpy()[c, :, :, :]
                # Revision 04/03/2025 >
                c += 1
            # < Revision 04/03/2025
            # apply mask
            if m is not None: np = np * m
            # Revision 04/03/2025 >
            idx = np.argmax()
            cc = unravel_index(idx, np.shape)[::-1]
            cc = tuple([int(i) for i in cc])
            r.append(cc)
        if len(r) == 1: r = r[0]
        return r

    # < Revision 16/12/2024
    #  multi-component management
    def getRange(self,
                 mask: str | SisypheImage | SisypheBinaryImage | None = None,
                 c: int | None = 0) -> tuple[float, float] | list[tuple[float, float]]:
        """
        Get range (min, max) of image.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process
            - None, all components processed. In this case, the method returns a list of range values of each component
            of the multi-component image

        Returns
        -------
        tuple[float, float] | list[tuple[float, float]]
            - (min, max) values for single-component image
            - (min, max) values for multi-component image, if component index c is int (default 0)
            - list of max values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Range processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            # noinspection PyArgumentList
            return float(img.min()), float(img.max())
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append((float(img.min()), float(img.max())))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getPercentile(self,
                      perc: int = 25, mask: str | SisypheImage | SisypheBinaryImage | None = None,
                      c: int | None = 0) -> float | list[float]:
        """
        Get percentile of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        perc : int
            percentile (default 25, first quartile)
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process
            - None, all components processed. In this case, the method returns a list of percentile values of each
            component of the multi-component image

        Returns
        -------
        float | list[float]
            - percentile value for single-component image
            - percentile value for multi-component image, if component index c is int (default 0)
            - list of percentile values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Percentile processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            return float(percentile(img, perc))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(percentile(img, perc)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getKurtosis(self,
                    mask: str | SisypheImage | SisypheBinaryImage | None = None,
                    c: int | None = 0) -> float | list[float]:
        """
        Get kurtosis of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process
            - None, all components processed. In this case, the method returns a list of kurtosis values of each
            component of the multi-component image

        Returns
        -------
        float | list[float]
            - kurtosis value for single-component image
            - kurtosis value for multi-component image, if component index c is int (default 0)
            - list of kurtosis values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Kurtosis processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            return float(kurtosis(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                r.append(float(kurtosis(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # < Revision 16/12/2024
    #  multi-component management
    def getSkewness(self,
                    mask: str | SisypheImage | SisypheBinaryImage | None = None,
                    c: int | None = 0) -> float | list[float]:
        """
        Get skewness of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int | None
            - parameter only used for multi-component image
            - int, index of the component to process
            - None, all components processed. In this case, the method returns a list of skewness values of each
            component of the multi-component image

        Returns
        -------
        float | list[float]
            - skewness value for single-component image
            - skewness value for multi-component image, if component index c is int (default 0)
            - list of kurtosis values of each component of a multi-component image, if component index c is None
        """
        # mask processing
        m = None
        if mask is not None:
            if isinstance(mask, str):
                m = self.getMask(algo=mask, c=c).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        # Skewness processing
        if n == 1:
            img = self.getNumpy().flatten()
            if m is not None: img = img[m > 0]
            # noinspection PyTypeChecker
            return float(skew(img))
        else:
            if c is None: first, last = 0, n
            else: first, last = c, c + 1
            r = list()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(first, last):
                img = self.getNumpy()[i, :, :, :].flatten()
                if m is not None: img = img[m > 0]
                # noinspection PyTypeChecker
                r.append(float(skew(img)))
            if len(r) == 1: return r[0]
            else: return r
    # Revision 16/12/2024 >

    # noinspection PyShadowingBuiltins
    def getHistogram(self,
                     mask: str | SisypheImage | SisypheBinaryImage | None = None,
                     bins: int = 100,
                     range: tuple[float, float] | None = None,
                     density: bool = False,
                     c: int = 0) -> ndarray:
        """
        Get histogram of image. Calculation is performed on the entire image (mask parameter = None) or in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        bins : int
            defines the number of equal-width bins in the given range.
        range : tuple[float, float] | None
            lower and upper range of the bins. If not provided (default None), range is simply (a.min(), a.max()),
            values outside the range are ignored.
        density : bool
            if False (default), the result will contain the number of samples in each bin. If True, the result is the
            value of the probability density function at the bin, normalized such that the integral over the range is 1.
        c : int
            component index

        Returns
        -------
        ndarray
            histogram
        """
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        if n > 1: img = self.getNumpy()[c, :, :, :].flatten()
        else: img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str) and mask != '':
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        # < Revision 04/03/2025
        # return histogram(img, bins, range, density)[0]
        return histogram(img, bins, range, density=density)[0]
        # Revision 04/03/2025 >

    def getStatistics(self, mask: str | SisypheImage | SisypheBinaryImage | None = None, c: int = 0) -> dict[str, float]:
        """
        Get descriptive statistics of image. Calculation is performed on the entire image (mask parameter = None) or
        in a mask.

        Parameters
        ----------
        mask : str | SisypheImage | SisypheBinaryImage | None
            - str, automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata' or 'moments'
            - SisypheBinaryImage, binary mask image
            - None, no mask, calculation is performed on the entire image
        c : int
            component index

        Returns
        -------
        dict[str, float]
            key/value:
                - 'mean': mean
                - 'std': standard deviation
                - 'min': minimum
                - 'p25': first quartile
                - 'median': median
                - 'p75': third quartile
                - 'max': maximum
                - 'kurtosis': kurtosis
                - 'skewness': skewness
        """
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        if n > 1: img = self.getNumpy()[c, :, :, :].flatten()
        else: img = self.getNumpy().flatten()
        if mask is not None:
            if isinstance(mask, str) and mask != '':
                m = self.getMask(algo=mask).getNumpy().flatten()
            elif isinstance(mask, SisypheBinaryImage):
                m = mask.getNumpy().flatten()
            # < Revision 12/12/2024
            elif isinstance(mask, SisypheImage):
                m = mask.getNumpy() > 0
                m = m.astype('uint8').flatten()
            # Revision 12/12/2024 >
            else: raise TypeError('parameter type {} is not str or SisypheBinaryImage.'.format(type(mask)))
            img = img[m > 0]
        r = dict()
        r['mean'] = mean(img)
        r['std'] = std(img)
        # noinspection PyArgumentList
        r['min'] = img.min()
        r['p25'] = percentile(img, 25)
        r['median'] = median(img)
        r['p75'] = percentile(img, 75)
        # noinspection PyArgumentList
        r['max'] = img.max()
        r['kurtosis'] = kurtosis(img)
        r['skewness'] = skew(img)
        return r

    def getNumberOfNonZero(self, c: int = 0) -> int:
        """
        Get number of non-zero in image.

        Parameters
        ----------
        c : int
            component index

        Returns
        -------
        int
            number of non-zero scalar values
        """
        n = self._sitk_image.GetNumberOfComponentsPerPixel()
        if n > 1: img = self.getNumpy()[c, :, :, :].flatten()
        else: img = self.getNumpy().flatten()
        # < Revision 27/11/2024
        # bugfix, return len(img[img > 0])
        return len(img[img != 0])
        # Revision 27/11/2024 >

    def getComponentMean(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get mean of each vector in a multicomponent image. Process all components or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = mean(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentStd(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get standard deviation of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = std(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentMin(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get minimum of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            # noinspection PyArgumentList
            r = img.min(axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentMax(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get maximum of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            # noinspection PyArgumentList
            r = img.max(axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    # < Revision 17/12/2024
    # add getComponentRange method
    def getComponentRange(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get range (max - min) of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            # noinspection PyArgumentList
            rmin = img.min(axis=0)
            # noinspection PyArgumentList
            rmax = img.max(axis=0)
            r = rmax - rmin
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')
    # Revision 17/12/2024 >

    def getComponentMedian(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get median of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = median(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentPercentile(self, perc: int = 25, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get percentile of each vector in a multicomponent image.

        Parameters
        ----------
        perc : int
            percentile (default 25, first quartile)
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = percentile(img, perc, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentKurtosis(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get kurtosis of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = kurtosis(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentSkewness(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get skewness of each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = skew(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentArgmax(self) -> SisypheImage:
        """
        Get the component index of the highest scalar value of each vector in a multicomponent image.

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            img = self.getNumpy()
            r = img.argmax(axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentArgmin(self, nonzero: bool = False) -> SisypheImage:
        """
        Get the component index of the lowest scalar value of each vector in a multicomponent image.

        Parameters
        ----------
        nonzero : bool
           exclude zero values if True

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            img = self.getNumpy()
            if nonzero:
                img = img.astype('double')
                img[img == 0.0] = npnan
                try:
                    # noinspection PyUnusedLocal
                    r = nanargmin(img, axis=0)
                except: r = 0.0
            else: r = img.argmin(axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentNumberOfNonZero(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get the number of non-zero values for each vector in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None: img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice): img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            r = count_nonzero(img, axis=0)
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('single component image.')

    def getComponentAllZero(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheImage:
        """
        Get vectors whose values are all zero in a multicomponent image.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed (default)

        Returns
        -------
        SisypheImage
            single-component image
        """
        if self._sitk_image.GetNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # add component indices management
            # img = self.getNumpy()
            if c is None:
                img = self.getNumpy()
            elif isinstance(c, (list, tuple)):
                l = list()
                for ci in c:
                    l.append(self.getNumpy()[ci, :, :, :])
                img = array(l)
            elif isinstance(c, slice):
                img = self.getNumpy()[c.start:c.stop:c.step, :, :, :]
            else:
                raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
            # Revision 19/12/2024 >
            # noinspection PyUnresolvedReferences
            r = (img.sum(axis=0) == 0.0).astype('uint8')
            return SisypheImage(r, spacing=self.getSpacing())
        else: raise AttributeError('Non-multicomponent image.')

    # < Revision 15/09/2024
    # add flip method
    def flip(self, axis: list[bool]) -> None:
        """
        Flip the current SisypheImage instance.

        Parameters
        ----------
        axis : list[bool]
            flip axis if True, axis order x, y, z.
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img = sitkFlip(self.getSITKImage(), axis)
            self.setSITKImage(img)
        else: ValueError('Not implemented for multi-component images.')
    # Revision 15/09/2024 >

    # < Revision 15/09/2024
    # add flip method
    # noinspection PyTypeChecker
    def getFlip(self, axis: list[bool]) -> SisypheImage:
        """
        Get a flipped copy of the current SisypheImage instance.

        Parameters
        ----------
        axis : list[bool]
            flip axis if True, axis order x, y, z.

        Returns
        -------
        SisypheImage
            flipped image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img: sitkImage = sitkFlip(self.getSITKImage(), axis)
            return SisypheImage(img)
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 15/09/2024 >

    # < Revision 20/10/2024
    # add standardizeIntensity method, not yet tested
    def standardizeIntensity(self, method: str = 'norm') -> None:
        """
        Intensity normalization of the current SisypheImage instance.

        Parameters
        ----------
        method : str
            - 'norm', standardize the intensity as zscore (i.e. zero mean, [-std, +std] mapped to [0, 1]
            - 'rescale', standardize the intensity values to the range [0, 1]
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            if method == 'norm':
                f = NormalizeImageFilter()
                img = f.Execute(self.getSITKImage())
            elif method == 'rescale':
                img = self.cast('float32')
                f = RescaleIntensityImageFilter()
                f.SetOutputMinimum(0.0)
                f.SetOutputMaximum(1.0)
                # noinspection PyUnresolvedReferences
                img = f.Execute(img.getSITKImage())
            else: raise ValueError('Invalid method {} (must be \'norm\' or \'rescale\''.format(method))
            self.setSITKImage(img)
        else: ValueError('Not implemented for multi-component images.')
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add getStandardizeIntensity method, not yet tested
    # noinspection PyTypeChecker
    def getStandardizeIntensity(self, method: str = 'norm') -> SisypheImage:
        """
        Get an intensity normalized copy of the current SisypheImage instance.

        Parameters
        ----------
        method : str
            - 'norm', standardize the intensity as zscore (i.e. zero mean, [-std, +std] mapped to [-1, 1]
            - 'rescale', standardize the intensity values to the range [0, 1]

        Returns
        -------
            SisypheImage
                standardized image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            if method == 'norm':
                f = NormalizeImageFilter()
                img = f.Execute(self.getSITKImage())
            elif method == 'rescale':
                img = self.cast('float32')
                f = RescaleIntensityImageFilter()
                f.SetOutputMaximum(1.0)
                f.SetOutputMinimum(0.0)
                # noinspection PyUnresolvedReferences
                img = f.Execute(img.getSITKImage())
            else: raise ValueError('Invalid method {} (must be \'norm\' or \'rescale\''.format(method))
            return SisypheImage(img)
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add truncateIntensity method, not yet tested
    def truncateIntensity(self,
                          centile: int = 1,
                          outputrange: tuple[float, float] | None = None):
        """
        Truncate intensity of the current SisypheImage instance. Truncate threshold is expressed in percentile
        (min threshold = centile, max threshold = 100 - centile). The max and min values of the output image are given
        in the output range parameter. If output range is None, max and min values of the output image are the max and
        min truncate thresholds.

        Parameters
        ----------
        centile : int
            truncate threshold expressed in percentile
        outputrange : tuple[float, float] | None
            max and min values of the output image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img = self.getNumpy().flatten()
            wmin = percentile(img, centile)
            wmax = percentile(img, 100 - centile)
            f = IntensityWindowingImageFilter()
            f.SetWindowMinimum(wmin)
            f.SetWindowMaximum(wmax)
            if outputrange is None:
                f.SetOutputMinimum(wmin)
                f.SetOutputMaximum(wmax)
            else:
                f.SetOutputMinimum(outputrange[0])
                f.SetOutputMaximum(outputrange[1])
            img = f.Execute(self.getSITKImage())
            self.setSITKImage(img)
        else: ValueError('Not implemented for multi-component images.')
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add getTruncateIntensity method, not yet tested
    # noinspection PyTypeChecker
    def getTruncateIntensity(self,
                             centile: int = 1,
                             outputrange: tuple[float, float] | None = None) -> SisypheImage:
        """
        Get intensity truncated copy of the current SisypheImage instance.
        Truncate threshold is expressed in percentile (min threshold = centile, max threshold = 100 - centile).
        The max and min values of the output image are given in the output range parameter.
        If output range is None, max and min values of the output image are the max and min truncate thresholds.

        Parameters
        ----------
        centile : int
            truncate threshold expressed in percentile
        outputrange : tuple[float, float] | None
            max and min values of the output image

        Returns
        -------
            SisypheImage
                truncated intensity image
        """
        if self.getNumberOfComponentsPerPixel() == 1:
            img = self.getNumpy().flatten()
            wmin = percentile(img, centile)
            wmax = percentile(img, 100 - centile)
            f = IntensityWindowingImageFilter()
            f.SetWindowMinimum(wmin)
            f.SetWindowMaximum(wmax)
            if outputrange is None:
                f.SetOutputMinimum(wmin)
                f.SetOutputMaximum(wmax)
            else:
                f.SetOutputMinimum(outputrange[0])
                f.SetOutputMaximum(outputrange[1])
            img = f.Execute(self.getSITKImage())
            return SisypheImage(img)
        else: raise ValueError('Not implemented for multi-component images.')
    # Revision 20/10/2024 >

    # IO public methods

    def saveToNIFTI(self, filename: str, compress: bool = False) -> None:
        """
        Save the current SisypheImage instance to a Nifti (.nii) file.

        Parameters
        ----------
        filename : str
            Nifti file name
        compress : bool
            gzip compression if True (default False)
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToNIFTI(self._sitk_image, filename, compress)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToNRRD(self, filename: str) -> None:
        """
        Save the current SisypheImage instance to a Nrrd (.nrrd) file.

        Parameters
        ----------
        filename : str
            Nrrd file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToNRRD(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToMINC(self, filename: str) -> None:
        """
        Save the current SisypheImage instance to a Minc (.minc) file.

        Parameters
        ----------
        filename : str
            Minc file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToMINC(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToVTK(self, filename: str) -> None:
        """
        Save the current SisypheImage instance to a vtk (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        if not self.isEmpty():
            self._sitk_image.SetDirection(getVTKDirections())
            writeToVTK(self._sitk_image, filename)
            self._sitk_image.SetDirection(getRegularDirections())
        else: raise ValueError('SisypheImage array is empty.')

    def saveToJSON(self, filename: str) -> None:
        """
        Save the current SisypheImage instance to a Json (.json) file.

        Parameters
        ----------
        filename : str
            Json file name
        """
        if not self.isEmpty():
            writeToJSON(self._sitk_image, filename)
        else: raise ValueError('SisypheImage array is empty.')

    def saveToNumpy(self, filename: str) -> None:
        """
        Save the current SisypheImage instance to a numpy (.npy) file.

        Parameters
        ----------
        filename : str
            numpy file name
        """
        if not self.isEmpty():
            writeToNumpy(self._sitk_image, filename)
        else: raise ValueError('SisypheImage array is empty.')

    def loadFromSisyphe(self, filename: str) -> dict:
        """
        Load the current SisypheImage instance from an old Sisyphe (.vol) file.

        Parameters
        ----------
        filename : str
            old Sisyphe binary file name

        Returns
        -------
        dict
            Old Sisyphe header (see Sisyphe.sisypheImageIO.loadFromSisyphe docstring for keys and values documentation)
        """
        img, hdr = readFromSisyphe(filename)
        img = flipImageToVTKDirectionConvention(img)
        img = convertImageToAxialOrientation(img)[0]
        img.SetDirection(getRegularDirections())
        # < Revision 31/07/2024
        if hdr['scale'] != 1.0 or hdr['intercept'] != 0.0:
            img = sitkCast(img, sitkFloat32) * hdr['scale'] + hdr['intercept']
            hdr['scale'] = 1.0
            hdr['intercept'] = 0.0
        # Revision 31/07/2024 >
        self.setSITKImage(img)
        self.setOrigin()
        return hdr

    def loadFromBrainVoyagerVMR(self, filename: str) -> dict:
        """
        Load the current SisypheImage instance from a BrainVoyager (.vmr) file.

        Parameters
        ----------
        filename : str
            BrainVoyager file name
        """
        img, hdr = readFromBrainVoyagerVMR(filename)
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)
        self.setOrigin()
        return hdr

    def loadFromFreeSurferMGH(self, filename: str) -> None:
        """
        Load the current SisypheImage instance from a FreeSurfer MGH (.mgh, .mgz) file.

        Parameters
        ----------
        filename : str
            FreeSurfer file name
        """
        img = readFromFreeSurferMGH(filename)
        self.setSITKImage(img)

    def loadFromNIFTI(self, filename: str, reorient: bool = True) -> None:
        """
        Load the current SisypheImage instance from a Nifti (.nii) file.

        Parameters
        ----------
        filename : str
            Nifti file name
        reorient : bool
            conversion to RAS+ world coordinates convention if True (default True)
        """
        img = readFromNIFTI(filename)
        imgs = list()
        s = img.GetSize()
        # Multicomponent sitk image ?
        # Copy each component to a single component sitk image
        d = len(s)
        if d == 3: imgs.append(img)
        elif d == 4 and s[3] > 1:
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(s[3]):
                imgs.append(img[:, :, :, i])
        # Reorientation of each sitk single component image
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(imgs)):
            if reorient:
                # <Revision 18/07/2024
                # imgs[i] = flipImageToVTKDirectionConvention(imgs[i])
                # imgs[i], _ = convertImageToAxialOrientation(imgs[i])
                # reverse function call order
                imgs[i], _ = convertImageToAxialOrientation(imgs[i])  # Update directions, not origin (always [x, y, z], independent of image orientation)
                imgs[i] = flipImageToVTKDirectionConvention(imgs[i])  # Update directions and origin
                # Revision 18/07/2024>
            imgs[i].SetDirection(getRegularDirections())
        # Rebuild multicomponent sitk image
        if len(imgs) == 1: img = imgs[0]
        else:
            f = sitkComposeImageFilter()
            img = f.Execute(imgs)
        # Set multicomponent sitk image to self SisypheVolume instance
        self.setSITKImage(img)
        # <Revision 15/04/2023
        # self.setOrigin()
        # Revision 15/04/2023>
        # <Revision 17/07/2024
        # origin = [abs(i) for i in img.GetOrigin()]
        origin = list(img.GetOrigin())
        s = img.GetSize()
        sp = img.GetSpacing()
        # if origin is negative in x-axis or y-axis, origin is corrected (FOV - origin)
        if origin[0] < 0.0: origin[0] = s[0] * sp[0] - origin[0]
        if origin[1] < 0.0: origin[1] = s[1] * sp[1] - origin[1]
        if origin[2] > 0.0: origin[2] = s[2] * sp[2] + origin[2]
        else: origin[2] = -origin[2]
        # Revision 17/07/2024>
        self.setOrigin(origin)

    def loadFromNRRD(self, filename: str) -> None:
        """
        Load the current SisypheImage instance from a Nrrd (.nrrd) file.

        Parameters
        ----------
        filename : str
            Nrrd file name
        """
        img = readFromNRRD(filename)
        # < Revision 18/07/2024
        # img = flipImageToVTKDirectionConvention(img)
        # img = convertImageToAxialOrientation(img)[0]
        # reverse function call order
        img = convertImageToAxialOrientation(img)[0]
        img = flipImageToVTKDirectionConvention(img)
        origin = list(img.GetOrigin())
        s = img.GetSize()
        sp = img.GetSpacing()
        # if origin is negative in x-axis or y-axis, origin is corrected (FOV - origin)
        if origin[0] < 0.0: origin[0] = s[0] * sp[0] - origin[0]
        if origin[1] < 0.0: origin[1] = s[1] * sp[1] - origin[1]
        if origin[2] > 0.0: origin[2] = s[2] * sp[2] + origin[2]
        else: origin[2] = -origin[2]
        # Revision 18/07/2024 >
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)

    def loadFromMINC(self, filename: str) -> None:
        """
        Load the current SisypheImage instance from a Minc (.minc) file.

        Parameters
        ----------
        filename : str
            Minc file name
        """
        img = readFromMINC(filename)
        # < Revision 18/07/2024
        # img = flipImageToVTKDirectionConvention(img)
        # img = convertImageToAxialOrientation(img)[0]
        # reverse function call order
        img = convertImageToAxialOrientation(img)[0]
        img = flipImageToVTKDirectionConvention(img)
        origin = list(img.GetOrigin())
        s = img.GetSize()
        sp = img.GetSpacing()
        # if origin is negative in x-axis or y-axis, origin is corrected (FOV - origin)
        if origin[0] < 0.0: origin[0] = s[0] * sp[0] - origin[0]
        if origin[1] < 0.0: origin[1] = s[1] * sp[1] - origin[1]
        if origin[2] > 0.0: origin[2] = s[2] * sp[2] + origin[2]
        else: origin[2] = -origin[2]
        # Revision 18/07/2024 >
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)

    def loadFromVTK(self, filename: str) -> None:
        """
        Load the current SisypheImage instance from a VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        img = readFromVTK(filename)
        # < Revision 18/07/2024
        # img = flipImageToVTKDirectionConvention(img)
        # img = convertImageToAxialOrientation(img)[0]
        # reverse function call order
        img = convertImageToAxialOrientation(img)[0]
        img = flipImageToVTKDirectionConvention(img)
        origin = list(img.GetOrigin())
        s = img.GetSize()
        sp = img.GetSpacing()
        # if origin is negative in x-axis or y-axis, origin is corrected (FOV - origin)
        if origin[0] < 0.0: origin[0] = s[0] * sp[0] - origin[0]
        if origin[1] < 0.0: origin[1] = s[1] * sp[1] - origin[1]
        if origin[2] > 0.0: origin[2] = s[2] * sp[2] + origin[2]
        else: origin[2] = -origin[2]
        # Revision 18/07/2024 >
        img.SetDirection(getRegularDirections())
        self.setSITKImage(img)

    def loadFromNumpy(self, filename: str) -> None:
        """
        Load the current SisypheImage instance from a numpy (.npy) file.

        Parameters
        ----------
        filename : str
            numpy file name
        """
        self.setSITKImage(readFromNumpy(filename))
        self.setOrigin()


class SisypheBinaryImage(SisypheImage):
    """
    Description
    ~~~~~~~~~~~

    Specialized SisypheImage class with unsigned short datatype.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheImage -> SisypheBinaryImage

    Creation: 12/01/2021
    Last revision: 22/06/2024
    """
    __slots__ = []

    # Special methods

    def __init__(self,
                 image: str | listImages2 | SisypheImage | None = None,
                 copy: bool = True,
                 **kargs) -> None:
        """
        SisypheBinaryImage instance constructor

        Parameters
        ----------
        image : SisypheImage | SimpleITK.Image | vkt.vtkImageData | ants.core.ANTSImage | numpy.ndarray
            image to copy
        copy : bool
            - if True, copy image to SisypheBinaryImage if datatype is unit8
            - if False, create only a new SisypheBinaryImage with the same image geometry (size, spacing, origin, orientation)
        **kargs :
            - size, tuple[float, float, float] | list[float, float, float]
            - datatype, str
            - spacing, tuple[float, float, float] | list[float, float, float]
            - direction, tuple[float, ...] | list[float, ...] (9 elements)
        """
        if image is None:
            kargs['datatype'] = 'uint8'
        else:
            # SisypheImage / SisypheVolume
            if isinstance(image, SisypheImage):
                # Revision 22/06/2024
                if copy:
                    if not image.isUInt8Datatype():
                        image = (image > 0).cast('uint8')
                else:
                    kargs['size'] = image.getSize()
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.getSpacing()
                    kargs['origin'] = image.getOrigin()
                    kargs['direction'] = image.getDirections()
                    image = None
            # sitkImage
            elif isinstance(image, sitkImage):
                # Revision 22/06/2024
                if copy:
                    if not image.GetPixelID() == sitkUInt8:
                        image = sitkCast(image > 0, sitkUInt8)
                else:
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.GetSpacing()
                    kargs['origin'] = image.GetOrigin()
                    kargs['direction'] = image.GetDirection()
                    image = None
            # vtkImageData
            elif isinstance(image, vtkImageData):
                # Revision 22/06/2024
                if copy:
                    # noinspection PyArgumentList
                    if image.GetScalarType() != VTK_CHAR:
                        f = vtkImageCast()
                        f.SetOutputScalarTypeToChar()
                        f.ClampOverflowOn()
                        f.SetInputData(image)
                        # noinspection PyArgumentList
                        f.Update()
                        image = f.GetOutput()
                else:
                    kargs['size'] = image.GetDimensions()
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.GetSpacing()
                    image = None
            # ANTsImage
            elif isinstance(image, ANTsImage):
                # Revision 22/06/2024
                if copy:
                    if image.pixeltype != 'unsigned char':
                        # noinspection PyUnresolvedReferences
                        image = (image > 0).astype('uint8')
                else:
                    kargs['size'] = image.shape
                    kargs['datatype'] = 'uint8'
                    kargs['spacing'] = image.spacing
                    kargs['direction'] = tuple(list(array(image.direction).flatten()))
                    image = None
            # Numpy
            elif isinstance(image, ndarray):
                # Revision 22/06/2024
                if copy:
                    if image.dtype != 'uint8':
                        image = (image > 0).astype('uint8')
                else:
                    image = None

        super().__init__(image, **kargs)

        if self.getDatatype() != 'uint8':
            raise TypeError('image parameter type {} is not uint8.'.format(self.getDatatype()))

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheBinaryImage instance to str
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

        Returns
        -------
        str
            SisypheBinaryImage instance representation
        """
        return 'SisypheBinaryImage instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def copyFromSITKImage(self, img: sitkImage) -> None:
        """
        Copy SimpleITK image buffer to current instance.

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        if isinstance(img, sitkImage):
            if img.GetPixelID() == sitkUInt8:
                super().copyFromSITKImage(img)
            else: raise TypeError('SimpleITK image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not SimpleITK image class.')

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        """
        Copy VTK image buffer to current instance.

        Parameters
        ----------
        img : vtk.vtkImageData
            image to copy
        """
        if isinstance(img, vtkImageData):
            # noinspection PyArgumentList
            if img.GetScalarType() == VTK_UNSIGNED_CHAR:
                super().copyFromVTKImage(img)
            else: raise TypeError('VTK image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not VTK image class.')

    def copyFromITKImage(self, img: itkImage) -> None:
        """
        Copy ITK image buffer to current instance.

        Parameters
        ----------
        img : itk.Image
            image to copy
        """
        if isUint8ITKImage(img):
            super().copyFromITKImage(img)
        else: raise TypeError('image parameter datatype is not uint8 ITK image class.')

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        """
        Copy ANTs image buffer to current instance.

        Parameters
        ----------
        img : ants.core.ANTsImage
            image to copy
        """
        if isinstance(img, ANTsImage):
            if img.pixeltype != 'unsigned char':
                super().copyFromANTSImage(img)
            else: raise TypeError('ANTs image parameter datatype is not uint8.')
        else: raise TypeError('image parameter is not ANTs Image class.')

    def copyFromNumpyArray(self,
                           img: ndarray,
                           spacing: vectorFloat3 = (1.0, 1.0, 1.0),
                           origin: vectorFloat3 = (0.0, 0.0, 0.0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True):
        """
        Copy Numpy array buffer to current instance.

        Parameters
        ----------
        img : numpy.ndarray
            image to copy
        spacing : tuple[float, float, float] | list[float, float, float]
            voxel sizes in mm (default 1.0, 1.0, 1.0)
        origin : tuple[float, float, float] | list[float, float, float]
            origin coordinates (default 0.0, 0.0, 0.0)
        direction : tuple[float, ...] | list[float]
            axes directions
        defaultshape : bool
            if True, numpy shape order is reversed (i.e. z, y, x)
        """
        if isinstance(img, ndarray):
            if img.dtype == 'uint8':
                super().copyFromNumpyArray(img, spacing, origin, direction, defaultshape)
            else: raise TypeError('image parameter datatype is not uint8.')
        else: raise TypeError('parameter is not ndarray class.')

    def setSITKImage(self, img: sitkImage) -> None:
        """
        Shallow copy of a SimpleITK Image to the SimpleITK Image attribute of the current SisypheImage instance.

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        if isinstance(img, sitkImage):
            if img.GetPixelID() == sitkUInt8:
                self._sitk_image = img
                self._updateImages()
            else: raise TypeError('image parameter datatype is not uint8.')
        else: raise TypeError('image parameter type {} is not sitkImage class.'.format(type(img)))
