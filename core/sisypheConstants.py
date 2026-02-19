"""
External packages/modules
-------------------------

    - ITK, medical image processing, https://itk.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import basename
from os.path import splitext

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
# noinspection PyUnresolvedReferences
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

"""
Functions
~~~~~~~~~

    - listToStr
    - getIntStdDatatypes
    - getFloatStdDatatypes
    - getDatatypes
    - isValidDatatype
    - isValidLibraryName
    - getLibraryDataType
    - getSupportedITKDatatypes
    - getSupportedITKStdDatatypes
    - isITKSupportedType
    - isITKSupportedStdType
    - isUint8ITKImage
    - isITKImageSupportedType
    - getNiftiExt
    - getNiftiCompressedExt
    - getNrrdExt
    - getMincExt
    - getVtkExt
    - getJsonExt
    - getNumpyExt
    - getSisypheExt
    - getSisypheROIExt
    - getFreeSurferExt
    - getBrainVoyagerVMRExt
    - getBrainVoyagerVOIExt
    - getSisypheROIExt
    - getDicomExt
    - getBitmapExt
    - getImageExt
    - getLutExt
    - getTractsExt
    - getRegularDirections
    - getVTKDirections
    - getSisypheDirections
    - getTemplatesID
    - addPrefixToFilename
    - addSuffixToFilename
    - addPrefixSuffixToFilename
    - replaceDirname
    - getID_ATROPOS
    - getID_ICBM152
    - getID_ICBM452
    - getID_NAC
    - getID_SPL
    - getID_SRI24
    - getID_DISTAL
    - isTemplateID
    - isATROPOS
    - isDISTAL
    - isICBM152
    - isICBM452
    - isNAC
    - isSPL
    - isSRI24
    - getShape_ICBM152
    - getOrigin_ICBM152
    - getTemplatePath
    - getATROPOSPath
    - getICBM152Path
    - getICBM452Path
    - getDISTALPath
    - getNACPath
    - getSPLPath
    - getSRI24Path

Creation: 08/09/2022
Last revision: 22/07/2024
"""

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
           'getFreeSurferExt',
           'getSisypheExt',
           'getSisypheROIExt',
           'getBrainVoyagerVMRExt',
           'getBrainVoyagerVOIExt',
           'getDicomExt',
           'getBitmapExt',
           'getImageExt',
           'getLutExt',
           'getTractsExt',
           'getRegularDirections',
           'getVTKDirections',
           'getSisypheDirections',
           'getTemplatesID',
           'addPrefixToFilename',
           'addSuffixToFilename',
           'addPrefixSuffixToFilename',
           'removeSuffixNumberFromFilename',
           'removeAllPrefixesFromFilename',
           'removeAllSuffixesFromFilename',
           'replaceDirname',
           'getID_ATROPOS',
           'getID_ICBM152',
           'getID_ICBM452',
           'getID_NAC',
           'getID_SPL',
           'getID_SRI24',
           'getID_DISTAL',
           'isTemplateID',
           'isATROPOS',
           'isICBM152',
           'isICBM452',
           'isNAC',
           'isSPL',
           'isSRI24',
           'isDISTAL',
           'getShape_ICBM152',
           'getOrigin_ICBM152',
           'getTemplatePath',
           'getATROPOSPath',
           'getICBM152Path',
           'getICBM452Path',
           'getDISTALPath',
           'getNACPath',
           'getSPLPath',
           'getSRI24Path']

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
_FREESURFEREXT = ['.mgh', '.mgz']
_SISYPHEROIEXT = ['.roi']
_LUTEXT = ['.lut', '.xlut']
_DICOMEXT = ['.dcm', '.dicom', '.ima', '.nema']
_TRACTSEXT = ['.xtracts', '.npz', '.tck', '.trk', '.vtk', '.vtp', '.fib', '.dpy']
_IMGEXT = _NIFTIEXT + _NRRDEXT + _MINCEXT + _VTKEXT + _JSONEXT + _NUMPYEXT + _SISYPHEEXT + _BVVMREXT + _FREESURFEREXT

# Templates

_ATROPOSID = 'ATROPOS'
_DISTALID = 'DISTAL'
_ICBM152ID = 'ICBM152'
_ICBM452ID = 'ICBM452'
_NACID = 'NAC'
_SPLID = 'SPL'
_SRI24ID = 'SRI24'
_TEMPLATEID = [_ATROPOSID, _DISTALID, _ICBM152ID, _ICBM452ID, _NACID, _SPLID, _SRI24ID]
_ICBM152SHAPE = [197, 233, 189]
_ICBM452SHAPE = [149, 188, 148]
_ICBM152ORIGIN = [98.0, 134.0, 72.0]

# Axis direction conventions

_REGULARDIR = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
_VTKDIR = [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0]
_SISDIR = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0]

def listToStr(l: list) -> str:
    """
    List to str conversion. Each item of the list is converted to str and concatenated in a new str with a space char
    as separator.

    Parameters
    ----------
    l : list
        list elements must be convertible to str

    Returns
    -------
    str
        converted list
    """
    return ' '.join([str(x) for x in l])

# Datatype conversion between SITK, ITK, VTK and Numpy libraries

def getIntStdDatatypes() -> list[str]:
    """
    Get list of numpy int datatypes in str format.

    Returns
    -------
    list[str]
        ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64']
    """
    return _INTDATATYPES

def getFloatStdDatatypes() -> list[str]:
    """
    Get list of numpy float datatypes in str format.

    Returns
    -------
    list[str]
        ['float32', 'float64']
    """
    return _FLOATDATATYPES

def getDatatypes() -> list[str]:
    """
    Get list of numpy datatypes in str format.

    Returns
    -------
    list[str]
        ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'float32', 'float64']
    """
    return _INTDATATYPES + _FLOATDATATYPES

def isValidDatatype(datatype: str) -> bool:
    """
    Checks whether the str parameter is a valid numpy datatype.

    Parameters
    ----------
    datatype : str
        numpy datatype in str format

    Returns
    -------
    bool
        True if datatype parameter is a valid numpy datatype
    """
    return datatype in _DATATYPES.keys()

def isValidLibraryName(libname) -> bool:
    """
    Checks whether the str parameter is a valid library name.

    Parameters
    ----------
    libname : str
        library name ('ants', 'itk', 'sitk', 'vtk')

    Returns
    -------
    bool
        True if parameter is a valid library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
    """
    return libname in _NAMETOLIB.keys()

def getLibraryDataType(datatype: str = 'uint8', lib: str | int = _LIBSITK) -> str | int | None:
    """
    Get native library datatype from numpy datatype in str format.

    Parameters
    ----------
    datatype : str
        numpy datatype in str format (default 'uint8')
    lib : str | int
        - library name (i.e. 'ants', 'itk', 'sitk', 'vtk')
        - library code (i.e. ants=0, itk=1, sitk=2, vtk=3)

    Returns
    -------
    str | int
        native library datatype
    """
    if datatype == 'None': return None
    else:
        if isinstance(datatype, str):
            if datatype in _DATATYPES.keys():
                if isinstance(lib, int): return _DATATYPES[datatype][lib]
                elif isinstance(lib, str): return _DATATYPES[datatype][_NAMETOLIB[lib]]
                else: raise ValueError('invalid lib parameter.')
            else: raise ValueError('invalid datatype parameter.')
        else: raise TypeError('{} parameter type is not str.'.format(str(type(datatype))))

def getSupportedITKDatatypes() -> list[itkCType]:
    """
    Get supported itk datatypes (wrapped in itk python package).

    Returns
    -------
    list[itk.itkCType]
        list of native itk datatype codes
    """
    return _ITKDATATYPES

def getSupportedITKStdDatatypes() -> list[str]:
    """
    Get supported itk datatypes (wrapped in itk python package) in numpy str format.

    Returns
    -------
    list[str]
        list of datatypes in numpy str format (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
    """
    return _EQITKDATATYPES

def isITKSupportedType(itkdatatype: itkCType) -> bool:
    """
    Checks whether the parameter is a supported itk datatype (wrapped in itk python package).

    Parameters
    ----------
    itkdatatype : itk.itkCType
        native itk datatype code

    Returns
    -------
    bool
        True if parameter is a supported itk datatype
    """
    return itkdatatype in _ITKDATATYPES

def isITKSupportedStdType(datatype: str) -> bool:
    """
    Checks whether the parameter, in numpy str format, is a supported itk datatype (wrapped in python itk package).

    Parameters
    ----------
    datatype : str
        numpy datatype in str format

    Returns
    -------
    bool
        True if parameter is a supported itk datatype (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
"""
    return datatype in _EQITKDATATYPES

def isUint8ITKImage(itkimage: itkImage) -> bool:
    """
    Checks whether itk image datatype is 'uint8' (wrapped in itk python package).

    Parameters
    ----------
    itkimage : itk.Image
        itk image instance

    Returns
    -------
    bool
        True if itk image datatype is 'unit8'
    """
    return type(itkimage) is _ITKIMAGETYPES[0]

def isITKImageSupportedType(itkimage: itkImage) -> bool:
    """
    Checks whether itk image datatype is supported.

    Parameters
    ----------
    itkimage : itk.Image
        itk image instance

    Returns
    -------
    bool
        True if itk image datatype is supported (i.e. 'uint8', 'uint16', 'int16', 'uint64', 'float32', 'float64')
    """
    return type(itkimage) in _ITKIMAGETYPES

# File extensions

def getNiftiExt() -> list[str]:
    """
    Get list of nifti file extensions.

    Returns
    -------
    list[str]
        ['.nii', '.hdr', '.img', '.nia', '.nii.gz', '.img.gz']
    """
    return _NIFTIEXT

def getNiftiCompressedExt() -> list[str]:
    """
    Get list of nifti compressed file extensions.

    Returns
    -------
    list[str]
        ['.nii.gz', '.img.gz']
    """
    return _NIFTIEXT[-2:]

def getNrrdExt() -> list[str]:
    """
    Get list of Nrrd file extensions.

    Returns
    -------
    list[str]
        ['.nrrd', '.nhdr']
    """
    return _NRRDEXT

def getMincExt() -> list[str]:
    """
    Get list of Minc file extension.

    Returns
    -------
    list[str]
        ['.mnc']
    """
    return _MINCEXT

def getVtkExt() -> list[str]:
    """
    Get list of VTK file extensions.

    Returns
    -------
    list[str]
        ['.vtk', '.vti']
    """
    return _VTKEXT

def getJsonExt() -> list[str]:
    """
    Get list of JSON file extension.

    Returns
    -------
    list[str]
        ['.json']
    """
    return _JSONEXT

def getNumpyExt() -> list[str]:
    """
    Get list of Numpy file extension.

    Returns
    -------
    list[str]
        ['.npy']
    """
    return _NUMPYEXT

def getSisypheExt() -> list[str]:
    """
    Get list of Sisyphe image file extension.

    Returns
    -------
    list[str]
        ['.vol']
    """
    return _SISYPHEEXT

def getSisypheROIExt() -> list[str]:
    """
    Get list of Sisyphe ROI file extension.

    Returns
    -------
    list[str]
        ['.roi']
    """
    return _SISYPHEROIEXT

def getBrainVoyagerVMRExt() -> list[str]:
    """
    Get list of BrainVoyager image file extension.

    Returns
    -------
    list[str]
        ['.vmr']
    """
    return _BVVMREXT

def getBrainVoyagerVOIExt() -> list[str]:
    """
    Get list of BrainVoyager ROI file extension.

    Returns
    -------
    list[str]
        ['.voi']
    """
    return _BVVOIEXT

def getFreeSurferExt() -> list[str]:
    """
    Get list of FreeSurfer volume file extension.

    Returns
    -------
    list[str]
      ['.mgh', '.mgz']
    """
    return _FREESURFEREXT

def getDicomExt() -> list[str]:
    """
    Get list of DICOM file extensions.

    Returns
    -------
    list[str]
        ['.dcm', '.dicom', '.ima', '.nema']
    """
    return _DICOMEXT

def getBitmapExt() -> list[str]:
    """
    Get list of bitmap image file extensions.

    Returns
    -------
    list[str]
        ['.bmp', '.jpg', '.jpeg','.png','.pbm','.pgm', '.ppm', '.xpm','.svg']
    """
    return _BITMAPEXT

def getImageExt() -> list[str]:
    """
    Get list of image file extensions supported by PySisyphe.

    Returns
    -------
    list[str]
        list of image file extensions
    """
    return _IMGEXT

def getLutExt() -> list[str]:
    """
    Get list of look-up table (LUT colormap) file extensions supported by PySisyphe.

    Returns
    -------
    list[str]
        ['.lut', '.xlut']
    """
    return _LUTEXT

def getTractsExt() -> list[str]:
    """
    Get list of tractogram file extensions supported by PySisyphe.

    Returns
    -------
    list[str]
        list of tractogram file extensions
    """
    return _TRACTSEXT

def addPrefixToFilename(filename: str, prefix: str, sep: str = '_') -> str:
    """
    Add a prefix to a file name.

    Parameters
    ----------
    filename : str
        filename to be prefixed
    prefix : str
        prefix to add
    sep : str
        separator between prefix and file name (default '_')

    Returns
    -------
    str
        file name with prefix
    """
    if filename != '':
        if isinstance(prefix, str):
            if prefix != '':
                if prefix[-1] == sep: prefix = prefix[:-1]
                return join(dirname(filename), '{}{}{}'.format(prefix, sep, basename(filename)))
            else: return filename
        else: raise TypeError('prefix parameter type {} is not str.'.format(prefix))
    else: raise ValueError('Filename parameter is empty.')

def addSuffixToFilename(filename: str, suffix: str, sep: str = '_') -> str:
    """
    Add a suffix to a file name.

    Parameters
    ----------
    filename : str
        filename to be suffixed
    suffix : str
        suffix to add
    sep : str
        separator between file name and suffix (default '_')

    Returns
    -------
    str
        file name with suffix
    """
    if filename != '':
        if isinstance(suffix, str):
            if suffix != '':
                if suffix[0] == sep: suffix = suffix[1:]
                root, ext = splitext(basename(filename))
                return join(dirname(filename), '{}{}{}{}'.format(root, sep, suffix, ext))
            else: return filename
        else: raise TypeError('suffix parameter type {} is not str.'.format(suffix))
    else: raise ValueError('Filename attribute is empty.')

def addPrefixSuffixToFilename(filename: str, prefix: str, suffix: str, sep: str = '_') -> str:
    """
    Add prefix and suffix to a file name.

    Parameters
    ----------
    filename : str
        filename to be prefixed and suffixed
    prefix : str
        prefix to add
    suffix : str
        suffix to add
    sep : str
        separator between prefix/suffix and file name (default '_')

    Returns
    -------
    str
        file name with prefix and suffix
    """
    if filename != '':
        if isinstance(suffix, str) and isinstance(prefix, str):
            if suffix != '':
                if suffix[0] == sep: suffix = suffix[1:]
            if prefix != '':
                if prefix[-1] == sep: prefix = prefix[:-1]
            root, ext = splitext(basename(filename))
            if suffix != '': sep2 = sep
            else: sep2 = ''
            if prefix != '': sep1 = sep
            else: sep1 = ''
            return join(dirname(filename), '{}{}{}{}{}{}'.format(prefix, sep1, root, sep2, suffix, ext))
        else: raise TypeError('suffix and/or prefix parameter type is not str.'.format(suffix))
    else: raise ValueError('Filename attribute is empty.')

def removeSuffixNumberFromFilename(filename: str, sep: str = '_') -> str:
    """
    Remove a suffix number (if any) from a file name.

    Parameters
    ----------
    filename : str
        file name with suffix to be removed
    sep : str
        char between prefix(es) (default '_')

    Returns
    -------
    str
        file name without suffix number
    """
    base, ext = splitext(filename)
    splt = base.split(sep)
    sfx = splt[-1]
    if sfx[0] == '#': sfx = sfx[1:]
    if sfx.isnumeric(): splt = splt[:-1]
    filename = sep.join(splt).rstrip(' _-#') + ext
    return filename

def removeAllPrefixesFromFilename(filename: str, sep: str = '_') -> str:
    """
    Remove all prefixes from a file name.

    Parameters
    ----------
    filename : str
        file name with prefix to be removed
    sep : str
        char between prefix(es) (default '_')

    Returns
    -------
    str
        file name without prefix
    """
    splt = filename.split(sep)
    if len(splt) > 1:
        path = dirname(filename)
        filename = join(path, splt[-1])
    return filename

def removeAllSuffixesFromFilename(filename: str, sep: str = '_') -> str:
    """
    Remove all suffixes from a file name.

    Parameters
    ----------
    filename : str
        file name with suffix to be removed
    sep : str
        char between prefix(es) (default '_')

    Returns
    -------
    str
        file name without suffix
    """
    splt = filename.split(sep)
    if len(splt) > 1:
        ext = splitext(filename)[1]
        filename = splt[0] + ext
    return filename

def replaceDirname(filename: str, newdir: str) -> str:
    """
    Replace the dirname of a file name.

    Parameters
    ----------
    filename : str
        path that dirname will be replaced
    newdir : str
        new dirname

    Returns
    -------
    str
        new file name
    """
    if newdir != '': return join(newdir, basename(filename))
    else: return filename

# Template ID and path

def getTemplatesID() -> list[str]:
    """
    Get list of template ID used by PySisyphe.

    Returns
    -------
    list[str]
        list of template ID
    """
    return _TEMPLATEID

def getID_ATROPOS() -> str:
    """
    Get ATROPOS template ID used by PySisyphe.

    Returns
    -------
    str
        ATROPOS template ID
    """
    return _ATROPOSID

def getID_DISTAL() -> str:
    """
    Get DISTAL template ID used by PySisyphe.

    Returns
    -------
    str
        DISTAL template ID
    """
    return _DISTALID

def getID_ICBM152() -> str:
    """
    Get ICBM152 template ID used by PySisyphe.

    Returns
    -------
    str
        ICBM152 template ID
    """
    return _ICBM152ID

def getID_ICBM452() -> str:
    """
    Get ICBM452 template ID used by PySisyphe.

    Returns
    -------
    str
        ICBM452 template ID
    """
    return _ICBM452ID

def getID_NAC() -> str:
    """
    Get NAC template ID used by PySisyphe.

    Returns
    -------
    str
        NAC template ID
    """
    return _NACID

def getID_SPL() -> str:
    """
    Get SPL template ID used by PySisyphe.

    Returns
    -------
    str
        SPL template ID
    """
    return _SPLID

def getID_SRI24() -> str:
    """
    Get SRI24 template ID used by PySisyphe.

    Returns
    -------
    str
        SRI24 template ID
    """
    return _SRI24ID

def isTemplateID(ID: str) -> bool:
    """
    Check whether ID parameter is a valid template ID used by PySisyphe.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if template ID
    """
    return ID in _TEMPLATEID

def isATROPOS(ID: str) -> bool:
    """
    Check whether ID parameter is an ATROPOS template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if ATROPOS template ID
    """
    return ID == _ATROPOSID

def isDISTAL(ID: str) -> bool:
    """
    Check whether ID parameter is a DISTAL template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if DISTAL template ID
    """
    return ID == _DISTALID

def isICBM152(ID: str) -> bool:
    """
    Check whether ID parameter is an ICBM152 template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if ICBM152 template ID
    """
    return ID == _ICBM152ID

def isICBM452(ID: str) -> bool:
    """
    Check whether ID parameter is an ICBM452 template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if ICBM452 template ID
    """
    return ID == _ICBM452ID

def isNAC(ID: str) -> bool:
    """
    Check whether ID parameter is a NAC template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if NAC template ID
    """
    return ID == _NACID

def isSPL(ID: str) -> bool:
    """
    Check whether ID parameter is an SPL template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if SPL template ID
    """
    return ID == _SPLID

def isSRI24(ID: str) -> bool:
    """
    Check whether ID parameter is an SRI24 template ID.

    Parameters
    ----------
    ID : str
        ID to test

    Returns
    -------
    bool
        True if SRI24 template ID
    """
    return ID == _SRI24ID

def getShape_ICBM152() -> list[int]:
    """
    Get shape (i.e. number of voxels in x, y and z axes) of ICBM152 templates.

    Returns
    -------
    list[int, int, int]
        ICBM152 templates shape
    """
    return _ICBM152SHAPE

def getOrigin_ICBM152() -> list[float]:
    """
    Get origin (i.e. world coordinates in mm) of ICBM152 templates.

    Returns
    -------
    list[float, float, float]
        ICBM152 templates origin
    """
    return _ICBM152ORIGIN

def getTemplatePath() -> str:
    """
    Get template path.

    Returns
    -------
    str
        PySisyphe template path
    """
    import Sisyphe
    return join(dirname(abspath(Sisyphe.__file__)), 'templates')

def getATROPOSPath() -> str:
    """
    Get Atropos template path.

    Returns
    -------
    str
        PySisyphe Atropos template path
    """
    return join(getTemplatePath(), _ATROPOSID)

def getDISTALPath() -> str:
    """
    Get Distal template path.

    Returns
    -------
    str
        PySisyphe Distal template path
    """
    return join(getTemplatePath(), _DISTALID)

def getICBM152Path() -> str:
    """
    Get ICBM152 template path.

    Returns
    -------
    str
        PySisyphe ICBM152 template path
    """
    return join(getTemplatePath(), _ICBM152ID)

def getICBM452Path() -> str:
    """
    Get ICBM452 template path.

    Returns
    -------
    str
        PySisyphe ICBM452 template path
    """
    return join(getTemplatePath(), _ICBM452ID)

def getNACPath() -> str:
    """
    Get NAC template path.

    Returns
    -------
    str
        PySisyphe NAC template path
    """
    return join(getTemplatePath(), _NACID)

def getSPLPath() -> str:
    """
    Get SPL template path.

    Returns
    -------
    str
        PySisyphe SPL template path
    """
    return join(getTemplatePath(), _SPLID)

def getSRI24Path() -> str:
    """
    Get SRI24 template path.

    Returns
    -------
    str
        PySisyphe SRI24 template path
    """
    return join(getTemplatePath(), _SRI24ID)

# Axis direction conventions

def getRegularDirections() -> list[float]:
    """
    Get default direction vectors of SisypheVolume image axes in RAS+ coordinates system.

    PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

        - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
        - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
        - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

    Directions is a list of 9 float, 3 vectors of 3 floats:

        - First vector, x-axis image direction, [1.0, 0.0, 0.0]
        - Second vector, y-axis image direction, [0.0, 1.0, 0.0]
        - Third vector, z-axis image direction, [0.0, 0.0, 1.0]

    Returns
    -------
    list[float]
        default direction vectors
    """
    return _REGULARDIR

def getVTKDirections() -> list[float]:
    """
    Get direction vectors of VTK image axes in RAS+ coordinates system.

    PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

        - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
        - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
        - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

    Directions is a list of 9 float, 3 vectors of 3 floats:

        - First vector, x-axis image direction, [-1.0, 0.0, 0.0]
        - Second vector, y-axis image direction, [0.0, -1.0, 0.0]
        - Third vector, z-axis image direction, [0.0, 0.0, 1.0]

    Returns
    -------
    list[float]
        VTK direction vectors
    """
    return _VTKDIR

def getSisypheDirections() -> list[float]:
    """
    Get direction vectors of old Sisyphe image axes in RAS+ coordinates system.

    PySisyphe uses RAS+ world coordinates system convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel:

        - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
        - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
        - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

    Directions is a list of 9 float, 3 vectors of 3 floats:

        - First vector, x-axis image direction, [1.0, 0.0, 0.0]
        - Second vector, y-axis image direction, [0.0, 1.0, 0.0]
        - Third vector, z-axis image direction, [0.0, 0.0, -1.0]

    Returns
    -------
    list[float]
        Sisyphe direction vectors
    """
    return _SISDIR
