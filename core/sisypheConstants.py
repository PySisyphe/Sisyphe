"""
    External packages/modules

        Name            Link                                                        Usage

        ITK             https://itk.org/                                            Medical image processing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from itk import itkCType
from itk import UC as itkUC
from itk import SC as itkSC
from itk import US as itkUS
from itk import SS as itkSS
from itk import UI as itkUI
from itk import SI as itkSI
from itk import UL as itkUL
from itk import SL as itkSL
from itk import F as itkF
from itk import D as itkD
from itk import Image as itkImage

from vtk import VTK_UNSIGNED_CHAR
from vtk import VTK_CHAR
from vtk import VTK_UNSIGNED_SHORT
from vtk import VTK_SHORT
from vtk import VTK_UNSIGNED_INT
from vtk import VTK_INT
from vtk import VTK_UNSIGNED_LONG
from vtk import VTK_LONG
from vtk import VTK_FLOAT
from vtk import VTK_DOUBLE

from SimpleITK import sitkUInt8, sitkInt8, sitkUInt16, sitkInt16, sitkUInt32
from SimpleITK import sitkInt32, sitkUInt64, sitkInt64, sitkFloat32, sitkFloat64
from SimpleITK import sitkVectorUInt8, sitkVectorInt8, sitkVectorUInt16, sitkVectorInt16, sitkVectorUInt32
from SimpleITK import sitkVectorInt32, sitkVectorUInt64, sitkVectorInt64, sitkVectorFloat32, sitkVectorFloat64

from PyQt5.QtGui import QImageReader

import Sisyphe.core as sc

__all__ = ['listToStr',
           'getIntStdDatatypes',
           'getFloatStdDatatypes',
           'getDatatypes',
           'isValidDatatype',
           'isValidLibraryName',
           'getLibraryDataType',
           'getSupportedITKDatatypes',
           'getSupportedITKStdDatatypes',
           'isITKSupportedType',
           'isITKSupportedStdType',
           'isUint8ITKImage',
           'isITKImageSupportedType',
           'getNiftiExt',
           'getNiftiCompressedExt',
           'getNrrdExt',
           'getMincExt',
           'getVtkExt',
           'getJsonExt',
           'getNumpyExt',
           'getSisypheExt',
           'getSisypheROIExt',
           'getBrainVoyagerVMRExt',
           'getBrainVoyagerVOIExt',
           'getDicomExt',
           'getBitmapExt',
           'getImageExt',
           'getLutExt',
           'getRegularDirections',
           'getVTKDirections',
           'getSisypheDirections']

"""
    Constants
"""

# Library codes

_LIBANTS, _LIBITK, _LIBSITK, _LIBVTK, _LIBSITKVEC = 0, 1, 2, 3, 4
_NAMETOLIB = {'ants': _LIBANTS, 'itk': _LIBITK, 'sitk': _LIBSITK, 'vtk': _LIBVTK}
_LIBTONAME = {_LIBANTS: 'ants', _LIBITK: 'itk', _LIBSITK: 'sitk', _LIBVTK: 'vtk'}

# Datatype conversion between SITK, ITK, VTK and Numpy libraries
# key = ndarray.dtype.name, value = datatype (ANTs, ITK, SITK, VTK, SITKVECTOR)

_DATATYPES = {'uint8': ('unsigned char', itkUC, sitkUInt8, VTK_UNSIGNED_CHAR, sitkVectorUInt8),
              'int8': ('char', itkSC, sitkInt8, VTK_CHAR, sitkVectorInt8),
              'uint16': ('unsigned short', itkUS, sitkUInt16, VTK_UNSIGNED_SHORT, sitkVectorUInt16),
              'int16': ('short', itkSS, sitkInt16, VTK_SHORT, sitkVectorInt16),
              'uint32': ('unsigned int', itkUI, sitkUInt32, VTK_UNSIGNED_INT, sitkVectorUInt32),
              'int32': ('int', itkSI, sitkInt32, VTK_INT, sitkVectorInt32),
              'uint64': ('unsigned long', itkUL, sitkUInt64, VTK_UNSIGNED_LONG, sitkVectorUInt64),
              'int64': ('long', itkSL, sitkInt64, VTK_LONG, sitkVectorInt64),
              'float32': ('float', itkF, sitkFloat32, VTK_FLOAT, sitkVectorFloat32),
              'float64': ('double', itkD, sitkFloat64, VTK_DOUBLE, sitkVectorFloat64)}

_INTDATATYPES = ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64']
_FLOATDATATYPES = ['float32', 'float64']

# List of datatypes supported in ITK

_ITKDATATYPES = [itkUC, itkUS, itkSS, itkUL, itkF, itkD]
_EQITKDATATYPES = ['uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64']

# List of itkImage types

_ITKIMAGETYPES = [itkImage[i, 3] for i in _ITKDATATYPES]

# File extensions

_NIFTIEXT = ['.nii', '.hdr', '.img', '.nia', '.nii.gz', '.img.gz']
_NRRDEXT = ['.nrrd', '.nhdr']
_MINCEXT = ['.mnc']
_VTKEXT = ['.vtk', '.vti']
_JSONEXT = ['.json']
_BITMAPEXT = ['.' + f.data().decode() for f in QImageReader.supportedImageFormats()]
_NUMPYEXT = ['.npy']
_SISYPHEEXT = ['.vol']
_BVVMREXT = ['.vmr']
_BVVOIEXT = ['.voi']
_SISYPHEROIEXT = ['.roi']
_LUTEXT = ['.lut', '.xlut']
_DICOMEXT = ['.dcm', '.dicom', '.ima', '.nema']
_TRACTSEXT = [sc.sisypheTracts.SisypheStreamlines.getFileExt(), '.npz', '.tck', '.trk', '.vtk', '.vtp', '.fib', '.dpy']
_IMGEXT = _NIFTIEXT + _NRRDEXT + _MINCEXT + _VTKEXT + _JSONEXT + _NUMPYEXT + _SISYPHEEXT + _BITMAPEXT

# Axis direction conventions

_REGULARDIR = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
_VTKDIR = [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]
_SISDIR = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0]

"""
    Functions
    
        listToStr(l: list) -> str
        getIntStdDatatypes() -> list[str]
        getFloatStdDatatypes() -> list[str]
        getDatatypes() -> list[str]
        isValidDatatype(datatype: str) -> bool
        isValidLibraryName(libname) -> bool
        getLibraryDataType(datatype: str = 'uint8', lib: str | int = _LIBSITK) -> str | int
        getSupportedITKDatatypes() -> list[itkCType]
        getSupportedITKStdDatatypes() -> list[str]
        isITKSupportedType(itkdatatype: itkCType) -> bool
        isITKSupportedStdType(datatype: str) -> bool
        isUint8ITKImage(itkimage: itkImage) -> bool
        isITKImageSupportedType(itkimage: itkImage) -> bool
        getNiftiExt() -> list[str]
        getNiftiCompressedExt() -> list[str]
        getNrrdExt() -> list[str]
        getMincExt() -> list[str]
        getVtkExt() -> list[str]
        getJsonExt() -> list[str]
        getNumpyExt() -> list[str]
        getSisypheExt() -> list[str]
        getBrainVoyagerVMRExt() -> list[str]
        getBrainVoyagerVOIExt() -> list[str]
        getSisypheROIExt() -> list[str]
        getDicomExt() -> list[str]
        getBitmapExt() -> list[str]
        getImageExt() -> list[str]
        getLutExt() -> list[str]
        getRegularDirections() -> list[float]
        getVTKDirections() -> list[float]
        getSisypheDirections() -> list[float]
        
    Creation: 08/09/2022
    Revisions:
    
        31/08/2023  type hinting
        14/11/2023  docstrings
"""

def listToStr(l: list) -> str:
    """
        List to str conversion.
        Each item of the list is converted to str and concatenated
        in a new str with a space character as separator.

        Parameter

            l   list, item type must be convertible to str

        return  str
    """
    return ' '.join([str(x) for x in l])

# Datatype conversion between SITK, ITK, VTK and Numpy libraries

def getIntStdDatatypes() -> list[str]:
    """
        Get list of numpy int datatypes in str format.

        return  ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64']
    """
    return _INTDATATYPES

def getFloatStdDatatypes() -> list[str]:
    """
        Get list of numpy float datatypes in str format.

        return  ['float32', 'float64']
    """
    return _FLOATDATATYPES

def getDatatypes() -> list[str]:
    """
        Get list of numpy datatypes in str format.

        return  ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'float32', 'float64']
    """
    return _INTDATATYPES + _FLOATDATATYPES

def isValidDatatype(datatype: str) -> bool:
    """
        Checks whether the str parameter is a valid numpy datatype.

        Parameter

            datatype    str, numpy datatype in str format

        return  bool, True if datatype parameter is a valid numpy datatype
    """
    return datatype in _DATATYPES.keys()

def isValidLibraryName(libname) -> bool:
    """
        Checks whether the str parameter is a valid library name.

        Parameter

            libname    str, library name

        return  bool, True if parameter is a valid library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
    """
    return libname in _NAMETOLIB.keys()

def getLibraryDataType(datatype: str = 'uint8', lib: str | int = _LIBSITK) -> str | int | None:
    """
        Get native library datatype from numpy datatype in str format.

        Parameters

            datatype    str, numpy datatype in str format (default 'uint8')
            lib         str | int, library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
                                   library code (i.e. ants=0, itk=1, sitk=2, vtk=3)

        return  str | int, native library datatype
    """
    if datatype == 'None':
        return None
    else:
        if isinstance(datatype, str):
            if datatype in _DATATYPES.keys():
                if isinstance(lib, int):
                    return _DATATYPES[datatype][lib]
                elif isinstance(lib, str):
                    return _DATATYPES[datatype][_NAMETOLIB[lib]]
            else: raise ValueError('datatype parameter is not correct.')
        else: raise TypeError('{} type of the datatype parameter is not a string.'.format(str(type(datatype))))

def getSupportedITKDatatypes() -> list[itkCType]:
    """
        Get supported itk datatypes (wrapped in python itk package).

        return  list[itkCType], list of native itk datatype codes
    """
    return _ITKDATATYPES

def getSupportedITKStdDatatypes() -> list[str]:
    """
        Get supported itk datatypes (wrapped in python itk package) in numpy str format.

        return  list[str], list of datatypes in numpy str format
                           (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
    """
    return _EQITKDATATYPES

def isITKSupportedType(itkdatatype: itkCType) -> bool:
    """
        Checks whether the parameter is a supported itk datatype (wrapped in python itk package).

        Parameter

            itkdatatype     itkCType, native itk datatype code

        return  bool, True if parameter is a supported itk datatype
    """
    return itkdatatype in _ITKDATATYPES

def isITKSupportedStdType(datatype: str) -> bool:
    """
        Checks whether the parameter, in numpy str format,
        is a supported itk datatype (wrapped in python itk package).

        Parameter

            itkdatatype     str, numpy datatype in str format

        return  bool, True if parameter is a supported itk datatype
                      (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
    """
    return datatype in _EQITKDATATYPES

def isUint8ITKImage(itkimage: itkImage) -> bool:
    """
        Checks whether itk image datatype is 'uint8' (wrapped in python itk package).

        Parameter

            itkimage    itkImage, instance of itk image class

        return  bool, True if itk image datatype is 'unit8'
    """
    return type(itkimage) == _ITKIMAGETYPES[0]

def isITKImageSupportedType(itkimage: itkImage) -> bool:
    """
        Checks whether itk image datatype is supported.

        Parameter

            itkimage    itkImage, instance of itk image class

        return  bool, True if itk image datatype is supported
                      (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
    """
    return type(itkimage) in _ITKIMAGETYPES

# File extensions

def getNiftiExt() -> list[str]:
    """
        Get list of nifti file extensions.

        return  ['.nii', '.hdr', '.img', '.nia', '.nii.gz', '.img.gz']
    """
    return _NIFTIEXT

def getNiftiCompressedExt() -> list[str]:
    """
        Get list of nifti compressed file extensions.

        return  ['.nii.gz', '.img.gz']
    """
    return _NIFTIEXT[-2:]

def getNrrdExt() -> list[str]:
    """
        Get list of Nrrd file extensions.

        return  ['.nrrd', '.nhdr']
    """
    return _NRRDEXT

def getMincExt() -> list[str]:
    """
        Get list of Minc file extension.

        return  ['.mnc']
    """
    return _MINCEXT

def getVtkExt() -> list[str]:
    """
        Get list of VTK file extensions.

        return  ['.vtk', '.vti']
    """
    return _VTKEXT

def getJsonExt() -> list[str]:
    """
        Get list of JSON file extension.

        return  ['.json']
    """
    return _JSONEXT

def getNumpyExt() -> list[str]:
    """
        Get list of Numpy file extension.

        return  ['.npy']
    """
    return _NUMPYEXT

def getSisypheExt() -> list[str]:
    """
        Get list of Sisyphe image file extension.

        return  ['.vol']
    """
    return _SISYPHEEXT

def getSisypheROIExt() -> list[str]:
    """
        Get list of Sisyphe ROI file extension.

        return  ['.roi']
    """
    return _SISYPHEROIEXT

def getBrainVoyagerVMRExt() -> list[str]:
    """
        Get list of BrainVoyager image file extension.

        return  ['.vmr']
    """
    return _BVVMREXT

def getBrainVoyagerVOIExt() -> list[str]:
    """
        Get list of BrainVoyager ROI file extension.

        return  ['.voi']
    """
    return _BVVOIEXT

def getDicomExt() -> list[str]:
    """
        Get list of DICOM file extensions.

        return  ['.dcm', '.dicom', '.ima', '.nema']
    """
    return _DICOMEXT

def getBitmapExt() -> list[str]:
    """
        Get list of bitmap image file extensions.

        return  list[str]
    """
    return _BITMAPEXT

def getImageExt() -> list[str]:
    """
        Get list of image file extensions supported by PySisyphe.

        return  list[str]
    """
    return _IMGEXT

def getLutExt() -> list[str]:
    """
        Get list of look-up table (LUT colormap) file extensions supported by PySisyphe.

        return  ['.lut', '.xlut']
    """
    return _LUTEXT

def getTractsExt() -> list[str]:
    """
        Get list of tractogram file extensions supported by PySisyphe.

        return  list[str]
    """
    return self._TRACTSEXT

# Axis direction conventions

def getRegularDirections() -> list[float]:
    """
        Get default vectors of SisypheVolume image axes in RAS+ coordinates system.
        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
        with origin to corner of the voxel
            x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
        Directions is a list of 9 float, 3 vectors of 3 floats
        First vector, x image axis direction, [1.0, 0.0, 0.0]
        Second vector, y image axis direction, [0.0, 1.0, 0.0]
        Third vector, y image axis direction, [0.0, 0.0, 1.0]

        return     list[float]
    """
    return _REGULARDIR

def getVTKDirections() -> list[float]:
    """
        Get vectors of VTK image axes in RAS+ coordinates system.
        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
        with origin to corner of the voxel
            x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
        Directions is a list of 9 float, 3 vectors of 3 floats
        First vector, x image axis direction, [-1.0, 0.0, 0.0]
        Second vector, y image axis direction, [0.0, -1.0, 0.0]
        Third vector, y image axis direction, [0.0, 0.0, 1.0]

        return     list[float]
    """
    return _VTKDIR

def getSisypheDirections() -> list[float]:
    """
        Get vectors of old Sisyphe image axes in RAS+ coordinates system.
        PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...)
        with origin to corner of the voxel
            x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            z: direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)
        Directions is a list of 9 float, 3 vectors of 3 floats
        First vector, x image axis direction, [1.0, 0.0, 0.0]
        Second vector, y image axis direction, [0.0, 1.0, 0.0]
        Third vector, y image axis direction, [0.0, 0.0, -1.0]

        return     list[float]
    """
    return _SISDIR
