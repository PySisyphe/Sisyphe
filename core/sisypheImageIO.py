"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            http://stnava.github.io/ANTs/                               Image registration
        ITK             https://itk.org/                                            Medical image processing
        Numpy           https://numpy.org/                                          Scientific computing
        pydicom         https://pydicom.github.io/pydicom/stable/                   DICOM library
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from os.path import isdir
from os.path import exists
from os.path import dirname
from os.path import splitext

from struct import unpack

from numpy import load
from numpy import save
from numpy import frombuffer
from numpy import array as np_array

from pydicom import read_file
from pydicom import dcmread
from pydicom.tag import BaseTag
from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset

from PyQt5.QtWidgets import QApplication

from ants.core import image_read
from ants.core import from_numpy

from itk import imread as itkImageRead
from itk import GetImageFromArray as itkGetImageFromArray

from vtk import vtkImageData
from vtk import vtkImageReader
from vtk import vtkNIFTIImageReader
from vtk import vtkNrrdReader
from vtk import vtkMINCImageReader
from vtk import vtkBMPReader
from vtk import vtkTIFFReader
from vtk import vtkJPEGReader
from vtk import vtkPNGReader
from vtk import vtkJSONImageWriter
from vtkmodules.util.vtkImageExportToArray import vtkImageExportToArray
from vtkmodules.util.numpy_support import numpy_to_vtk

from SimpleITK import ImageFileReader as sitkImageFileReader
from SimpleITK import ImageFileWriter as sitkImageFileWriter
from SimpleITK import ImageSeriesReader as sitkImageSeriesReader
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage
from SimpleITK import GetImageFromArray as sitkGetImageFromArray
from SimpleITK import Flip as sitkFlip
from SimpleITK import PermuteAxes as sitkPermuteAxes
from SimpleITK import Image as sitkImage

from Sisyphe.lib.bv.vmr import read_vmr
from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getJsonExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getNiftiCompressedExt
from Sisyphe.core.sisypheConstants import getImageExt
from Sisyphe.core.sisypheConstants import getSisypheExt
from Sisyphe.core.sisypheConstants import getBrainVoyagerVMRExt
from Sisyphe.core.sisypheConstants import getSisypheROIExt
from Sisyphe.core.sisypheConstants import getBitmapExt
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.core.sisypheConstants import isValidLibraryName
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getSisypheDirections

__all__ = ['isDicom',
           'compareDataElementsBetweenDatasets',
           'extractDataElementValuesFromDatasets',
           'convertVTKtoSITK',
           'convertSITKtoVTK',
           'flipImageToVTKDirectionConvention',
           'convertImageToAxialOrientation',
           'readImage',
           'readFromNIFTI',
           'readFromNRRD',
           'readFromMINC',
           'readFromVTK',
           'readFromBitmap',
           'readFromNumpy',
           'readFromSisyphe',
           'readFromSisypheROI',
           'readFromDicomDirectory',
           'readFromDicomSeries',
           'readFromDicomFilenames',
           'readFromBrainVoyagerVMR',
           'writeToNIFTI',
           'writeToNRRD',
           'writeToMINC',
           'writeToJSON',
           'writeToVTK',
           'writeToNumpy']

""""
    DICOM functions
    
        isDicom(f: str) -> bool
        compareDataElementsBetweenDatasets(ds1: pydicom.dataset.Dataset, 
                                           ds2: pydicom.dataset.Dataset, 
                                           equality: bool = False) -> pydicom.dataset.Dataset
        extractDataElementValuesFromDatasets(dslist: list[pydicom.dataset.FileDataset 
                                                          | pydicom.dataset.Dataset 
                                                          | str], 
                                             taglist: list[pydicom.tag.BaseTag]) -> dict
        convertVTKtoSITK(img: vtk.vtkImageData) -> SimpleITK.Image
        convertSITKtoVTK(img: SimpleITK.Image) -> vtk.vtkImageData
        
    IO functions
    
        flipImageToVTKDirectionConvention(img: SimpleITK.Image) -> SimpleITK.Image
        convertImageToAxialOrientation(img: SimpleITK.Image) -> tuple[SimpleITK.Image, list[int, int, int]]
        readImage(filename: str, lib: str = 'sitk') -> SimpleITK.Image | tuple[SimpleITK.Image, dict]
        readFromNIFTI(filename: str, lib: str = 'sitk') -> SimpleITK.Image
        readFromNRRD(filename: str, lib: str = 'sitk') -> SimpleITK.Image
        readFromMINC(filename: str, lib: str = 'sitk') -> SimpleITK.Image
        readFromVTK(filename: str, lib: str = 'sitk') -> SimpleITK.Image
        readFromBitmap(filename: str, lib: str = 'sitk') -> SimpleITK.Image
        readFromNumpy(filename: str, defaultshape: bool = True, lib: str = 'sitk') -> SimpleITK.Image
        readFromSisyphe(filename: str, lib: str = 'sitk') -> tuple[SimpleITK.Image, dict]
        readFromBrainVoyagerVMR(filename: str, lib: str = 'sitk') -> tuple[SimpleITK.Image, dict]
        readFromSisypheROI(filename: str, lib: str = 'sitk') -> tuple[list[SimpleITK.Image], dict]
        readFromDicomDirectory(directory: str) -> SimpleITK.Image
        readFromDicomSeries(filename: list[str]) -> SimpleITK.Image
        readFromDicomFilenames(filenames: list[str]) -> SimpleITK.Image
        writeToNIFTI(img: SimpleITK.Image, filename: str, compression: bool = False)
        writeToNRRD(img: SimpleITK.Image, filename: str)
        writeToMINC(img: SimpleITK.Image, filename: str)
        writeToVTK(img: SimpleITK.Image, filename: str)
        writeToJSON(img: SimpleITK.Image, filename: str)
        writeToNumpy(img: SimpleITK.Image, filename: str)

    Creation: 01/11/2022        
    Revision:
    
        29/08/2023  type hinting
        19/10/2023  add readFromDicomFilenames() function
        19/11/2023  docstrings
"""


def isDicom(f: str) -> bool:
    """
        Test if a file is in Dicom format

        Parameter

            f   str, filename
    """
    if exists(f):
        file = open(f, 'rb')
        try:
            file.seek(128, 0)
            r = file.read(4)
            return r == b'DICM'
        except IOError:
            return False
        finally:
            file.close()
    else:
        return False


def compareDataElementsBetweenDatasets(ds1: Dataset, ds2: Dataset, equality: bool = False) -> Dataset:
    """
        Create dataset with Dicom fields with same values
        between two tested datasets (ds1, ds2 parameters)

        Parameters

            ds1         pydicom.Dataset
            ds2         pydicom.Dataset
            equality    bool, test equality if True, difference otherwise

        return  pydicom.Dataset
    """
    if isinstance(ds1, str):
        if exists(ds1):
            if isDicom(ds1):
                ds1 = read_file(ds1, stop_before_pixels=True)
    if isinstance(ds2, str):
        if exists(ds2):
            if isDicom(ds2):
                ds2 = read_file(ds2, stop_before_pixels=True)
    if isinstance(ds1, (FileDataset, Dataset)) and isinstance(ds2, (FileDataset, Dataset)):
        ds = Dataset()
        for de in ds1:
            if de.tag in ds2:
                if (de.value == ds2[de.tag].value) == equality:
                    ds.add(de)
        return ds
    else: raise TypeError('parameters are not str, pydicom.Filedataset or pydicom.Dataset.')


def extractDataElementValuesFromDatasets(dslist: list[FileDataset | Dataset | str], taglist: list[BaseTag]) -> dict:
    """
        Extract all the values of multiples dicom Tag (taglist parameter) in multiple datasets (dslist parameter)

        Parameters

            dslist  list[pydicom.Dataset]
            taglist list[pydicom.BaseTag]

        return  dict, key=pydicom.BaseTag, value=list of values of each pydicom.Dataset in dslist
    """
    if all([isinstance(i, (FileDataset, Dataset, str)) for i in dslist]):
        if all([isinstance(i, BaseTag) for i in dslist]):
            r = {}
            for tag in taglist:
                r[tag] = []
            for ds in dslist:
                if isinstance(ds, str):
                    if exists(ds):
                        if isDicom(ds):
                            ds = read_file(ds, stop_before_pixels=True)
                if isinstance(ds, (FileDataset, Dataset)):
                    for tag in taglist:
                        r[tag].append(ds[tag].value)
                return r
        else: raise TypeError('second parameter is not a list of pydicom.BaseTag.')
    else: raise TypeError('first parameter is not a list of pydicom.Filedataset, pydicom.Dataset or str.')


def convertVTKtoSITK(img: vtkImageData) -> sitkImage:
    """
        VTK image to SimpleITK image conversion

        Parameter

            img     vtk.vtkImageData

        return SimpleITK.Image
    """
    if isinstance(img, vtkImageData):
        r = vtkImageExportToArray()
        r.SetInputData(img)
        buff = r.GetArray()
        sitkimg = sitkGetImageFromArray(buff)
        sitkimg.SetSpacing(img.GetSpacing())
        sitkimg.SetOrigin(img.GetOrigin())
        sitkimg.SetDirection(getRegularDirections())
        return sitkimg
    else: raise TypeError('image parameter type {} is not vtkImageData image class.'.format(type(img)))


def convertSITKtoVTK(img: sitkImage) -> vtkImageData:
    """
        SimpleITK image to VTK image conversion

        Parameter

            img     SimpleITK.Image

        return  vtk.vtkImageData
    """
    if isinstance(img, sitkImage):
        buff = sitkGetArrayViewFromImage(img)
        buff.shape = buff.size
        data = numpy_to_vtk(buff)
        vtkimg = vtkImageData()
        vtkimg.SetDimensions(img.GetSize())
        vtkimg.SetSpacing(img.GetSpacing())
        vtkimg.SetOrigin(img.GetOrigin())
        vtkimg.AllocateScalars(getLibraryDataType(str(buff.dtype), 'vtk'), img.GetNumberOfComponentsPerPixel())
        vtkimg.GetPointData().SetScalars(data)
        return vtkimg
    else: raise TypeError('image parameter type {} is not sitkImage image class.'.format(type(img)))


# SisypheImage IO functions


def flipImageToVTKDirectionConvention(img: sitkImage) -> sitkImage:
    """
        Flip sitkImage to VTK orientation convention

        Sisyphe
            x Right to Left -> Flip X
            y Ant to Post   -> Flip Y
            z Top to Bottom -> Flip Z

        SimpleITK, ITK, DICOM
            x Right to Left     if direction (1 0 0)  -> Flip X
            y Ant to Post       if direction (0 1 0)  -> Flip Y
            z Bottom to Top     if direction (0 0 -1) -> Flip Z

        VTK, NIFTI
            x Left to Right
            y Post to Ant
            z Bottom to Top

        Parameter

            img     SimpleITK.Image

        return  SimpleITK.Image
    """
    if isinstance(img, sitkImage):
        f = [False, False, False]
        d = np_array(img.GetDirection()).reshape(3, 3).round()
        m = abs(d).argmax(axis=1)
        for i in range(3):
            # x dimension
            if m[i] == 0:
                if d[i, 0] == 1.0:
                    f[i] = True
            # y dimension
            elif m[i] == 1:
                if d[i, 1] == 1.0:
                    f[i] = True
            # z dimension
            else:
                if d[i, 2] == -1.0:
                    f[i] = True
        if any(f):
            img = sitkFlip(img, f)
        QApplication.processEvents()
        return img
    else: raise TypeError('image parameter type {} is not SimpleITK image class.'.format(type(img)))


def convertImageToAxialOrientation(img: sitkImage) -> tuple[sitkImage, list[int, int, int]]:
    """
        SimpleITK image reorientation to axial
        ex. coronal to axial  -> order = 0, 2, 1 (x, z, y)
        ex. sagittal to axial -> order = 1, 2, 0 (y, z, x)

        Parameter

            img     SimpleITK.Image

        return  SimpleITK.Image,
                list[int, int, int], order of dimensions
    """
    if isinstance(img, sitkImage):
        d = np_array(img.GetDirection()).reshape(3, 3).round()
        m = abs(d).argmax(axis=1)
        m = [int(i) for i in list(m)]
        if m != [0, 1, 2]: img = sitkPermuteAxes(img, m)
        QApplication.processEvents()
        return img, m
    else: raise TypeError('image parameter type {} is not SimpleITK image class.'.format(type(img)))


def readImage(filename: str, lib: str = 'sitk') -> sitkImage | tuple[sitkImage, dict]:
    """
        Read image from Nifti, Nrrd, Minc, VTK, Numpy, old Sisyphe, or Bitmap format.
        Format detection from filename extension.
        Instance returned can be SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getImageExt():
            if ext in getNiftiExt(): return readFromNIFTI(filename, lib)
            elif ext in getNrrdExt(): return readFromNRRD(filename, lib)
            elif ext in getMincExt(): return readFromMINC(filename, lib)
            elif ext in getVtkExt(): return readFromVTK(filename, lib)
            elif ext in getNumpyExt(): return readFromNumpy(filename, lib=lib)
            elif ext in getSisypheExt(): return readFromSisyphe(filename, lib)
            elif ext in getBitmapExt(): return readFromBitmap(filename, lib)
            else: raise ValueError('{} is not a valid extension'.format(lib))
        else: raise IOError('{} image format is not supported.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromNIFTI(filename: str, lib: str = 'sitk') -> sitkImage:
    """
        Read Nifti file (.nii, .hdr, .img, .nia, .nii.gz, .img.gz)

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == '.gz': path, ext = splitext(path)
        if ext in getNiftiExt():
            if isValidLibraryName(lib):
                if lib == 'sitk':
                    r = sitkImageFileReader()
                    r.SetImageIO('NiftiImageIO')
                    r.SetFileName(filename)
                    return r.Execute()
                if lib == 'vtk':
                    r = vtkNIFTIImageReader()
                    r.SetFileName(filename)
                    r.Update()
                    return r.GetOutput()
                elif lib == 'itk':
                    return itkImageRead(filename)
                else:  # lib == 'ants':
                    return image_read(filename)
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a NIFTI file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromNRRD(filename: str, lib: str = 'sitk') -> sitkImage:
    """
        Read NRRD file (.nrrd, .nhdr)

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getNrrdExt():
            if isValidLibraryName(lib):
                if lib == 'sitk':
                    r = sitkImageFileReader()
                    r.SetImageIO('NrrdImageIO')
                    r.SetFileName(filename)
                    return r.Execute()
                elif lib == 'vtk':
                    r = vtkNrrdReader()
                    r.SetFileName(filename)
                    r.Update()
                    return r.GetOutput()
                elif lib == 'itk':
                    return itkImageRead(filename)
                else:  # lib == 'ants':
                    return image_read(filename)
            else: raise ValueError('{} is not a valid library')
        else: raise IOError('{} is not a NRRD file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromMINC(filename: str, lib: str = 'sitk') -> sitkImage:
    """
        Read MINC file (.mnc)

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getMincExt():
            if isValidLibraryName(lib):
                if lib == 'sitk':
                    r = sitkImageFileReader()
                    r.SetImageIO('MINCImageIO')
                    r.SetFileName(filename)
                    return r.Execute()
                elif lib == 'vtk':
                    r = vtkMINCImageReader()
                    r.SetFileName(filename)
                    r.Update()
                    return r.GetOutput()
                elif lib == 'itk':
                    return itkImageRead(filename)
                else:  # lib == 'ants':
                    return image_read(filename)
            else: raise ValueError('{} is not a valid library')
        else: raise IOError('{} is not a MINC file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromVTK(filename: str, lib: str = 'sitk') -> sitkImage:
    """
        Read VTK file (.vtk, .vti)

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getVtkExt():
            if isValidLibraryName(lib):
                if lib == 'sitk':
                    r = sitkImageFileReader()
                    r.SetImageIO('VTKImageIO')
                    r.SetFileName(filename)
                    return r.Execute()
                elif lib == 'vtk':
                    r = vtkImageReader()
                    r.SetFileName(filename)
                    r.Update()
                    return r.GetOutput()
                elif lib == 'itk':
                    return itkImageRead(filename)
                else:  # lib == 'ants':
                    return image_read(filename)
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a VTK file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromBitmap(filename: str, lib: str = 'sitk') -> sitkImage:
    """
        Read Bitmap file (.bmp, .jpg, .jpeg, .png, .tiff)

        Parameter

            filename    str
            lib         str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getBitmapExt():
            if isValidLibraryName(lib):
                if lib == 'sitk':
                    if ext == '.bmp':
                        ioformat = 'BMPImageIO'
                    elif ext == '.jpg' or ext == '.jpeg':
                        ioformat = 'JPEGImageIO'
                    elif ext == '.png':
                        ioformat = 'PNGImageIO'
                    else:  # ext == '.tiff'
                        ioformat = 'TIFFImageIO'
                    r = sitkImageFileReader()
                    r.SetImageIO(ioformat)
                    r.SetFileName(filename)
                    return r.Execute()
                elif lib == 'vtk':
                    if ext == '.bmp':
                        r = vtkBMPReader()
                    elif ext == '.jpg' or ext == '.jpeg':
                        r = vtkJPEGReader()
                    elif ext == '.png':
                        r = vtkPNGReader()
                    else:  # ext == '.tiff'
                        r = vtkTIFFReader()
                    r.SetFileName(filename)
                    r.Update()
                    return r.GetOutput()
                elif lib == 'itk':
                    return itkImageRead(filename)
                else:  # lib == 'ants':
                    return image_read(filename)
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a Bitmap file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromNumpy(filename: str, defaultshape: bool = True, lib: str = 'sitk') -> sitkImage:
    """
        Read Numpy file (.npy)

        Parameter

            filename        str
            defaultshape    bool, shape (z, y, x) if True, (x, y, z) if False
            lib             str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
    """
    # defaultshape = True if default numpy shape (z, y, x)
    #              = False if image shape (x, y, z)
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext in getNumpyExt():
            if isValidLibraryName(lib):
                img = load(filename)
                if not defaultshape:
                    img = img.T
                if lib == 'sitk':
                    return sitkGetImageFromArray(img)
                elif lib == 'vtk':
                    vtkdata = numpy_to_vtk(img)
                    vtkimg = vtkImageData()
                    d = list(img.shape)
                    d.reverse()
                    vtkimg.SetDimensions(d)
                    vtkimg.AllocateScalars(getLibraryDataType(str(img.dtype), 'vtk'), img.ndim-2)
                    vtkimg.GetPointData().SetScalars(vtkdata)
                    return vtkimg
                elif lib == 'itk':
                    return itkGetImageFromArray(img)
                else:  # lib == 'ants':
                    return from_numpy(img.T)
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a Numpy file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromSisyphe(filename: str, lib: str = 'sitk') -> tuple[sitkImage, dict]:
    """
        Read Sisyphe file (.vol)

        Parameter

            filename        str
            lib             str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
                dict, header of Sisyphe image format
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == getSisypheExt()[0]:
            if isValidLibraryName(lib):
                f = open(filename, 'rb')
                try:
                    buff = f.read(1672)
                    if len(buff) == 1672:
                        buff = unpack('@I101p101p11p11p21p255p5d3H3dh?2B4d2?3d1024B', buff)
                        fields = ['id', 'lastname', 'firstname', 'dateofbirth', 'dateofscan', 'modality',
                                  'sequence', 'dummy1', 'TR', 'TE', 'scale', 'intercept', 'dimx', 'dimy', 'dimz',
                                  'vx', 'vy', 'vz', 'depth', 'isotropic', 'orient', 'codage', 'max', 'min',
                                  'windowmax', 'windowmin', 'template', 'smooth', 'fwhmx', 'fwhmy', 'fwhmz', 'palette']
                        hdr = dict(zip(fields, buff))
                        x, y, z = hdr['dimx'], hdr['dimy'], hdr['dimz']
                        vx, vy, vz = hdr['vx'], hdr['vy'], hdr['vz']
                        s = x * y * z
                        c = hdr['codage']
                        if c == 1:
                            s *= 2
                            buff = f.read(s)
                            # default array shape (z, y, z)
                            buff = frombuffer(buff, 'int16').reshape((z, y, x))
                        elif c == 2:
                            s *= 8
                            buff = f.read(s)
                            # default array shape (z, y, z)
                            buff = frombuffer(buff, 'float64').reshape((z, y, x))
                        elif c == 3:
                            raise IOError('rgb datatype is not supported.')
                        else:
                            raise IOError('datatype error.')
                        if hdr['orient'] == 0:
                            # axial
                            c = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0)
                        elif hdr['orient'] == 1:
                            # coronal
                            c = (1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0)
                        else:
                            # sagittal
                            c = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0)
                        # SisypheImage constructor array parameter must have default shape (z, y, x)
                        if lib == 'sitk':
                            img = sitkGetImageFromArray(buff)
                            img.SetSpacing((vx, vy, vz))
                            img.SetDirection(c)
                            img.SetOrigin((0, 0, 0))
                        elif lib == 'vtk':
                            vtkdata = numpy_to_vtk(buff)
                            img = vtkImageData()
                            d = list(buff.shape)
                            d.reverse()
                            img.SetDimensions(d)
                            img.SetSpacing(vx, vy, vz)
                            img.SetOrigin(0, 0, 0)
                            img.AllocateScalars(getLibraryDataType(str(buff.dtype), 'vtk'), buff.ndim - 2)
                            img.GetPointData().SetScalars(vtkdata)
                        elif lib == 'itk':
                            img = itkGetImageFromArray(buff)
                        else:  # lib == 'ants':
                            img = from_numpy(buff.T)
                        return img, hdr
                    else: raise IOError('{} is not a Sisyphe volume file.'.format(filename))
                except IOError: raise IOError('{} is not a Sisyphe volume file.'.format(filename))
                finally:
                    f.close()
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a Sisyphe file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromBrainVoyagerVMR(filename: str, lib: str = 'sitk') -> tuple[sitkImage, dict]:
    """
        Read BrainVoyager VMR file (.vmr)

        Parameter

            filename        str
            lib             str, format of returned image 'itk', 'vtk', 'ants' or by default 'sitk'

        return  SimpleITK.Image | itk.Image | vtk.ImageData | ants.core.ANTsImage
                dict, header of BrainVoyager VMR image format
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == getBrainVoyagerVMRExt()[0]:
            if isValidLibraryName(lib):
                hdr, buff = read_vmr(filename)
                vx = hdr['VoxelSizeY']
                vy = hdr['VoxelSizeX']
                vz = hdr['VoxelSizeZ']
                if lib == 'sitk':
                    img = sitkGetImageFromArray(buff.T)
                    img.SetSpacing((vx, vy, vz))
                    img.SetOrigin((0, 0, 0))
                elif lib == 'vtk':
                    vtkdata = numpy_to_vtk(buff.T)
                    img = vtkImageData()
                    d = list(buff.shape)
                    d.reverse()
                    img.SetDimensions(d)
                    img.SetSpacing(vx, vy, vz)
                    img.SetOrigin(0, 0, 0)
                    img.AllocateScalars(getLibraryDataType(str(buff.dtype), 'vtk'), buff.ndim - 2)
                    img.GetPointData().SetScalars(vtkdata)
                elif lib == 'itk':
                    img = itkGetImageFromArray(buff.T)
                else:  # lib == 'ants':
                    img = from_numpy(buff)
                return img, hdr
            else: raise ValueError('{} is not a valid library'.format(lib))
        else: raise IOError('{} is not a BrainVoyager VMR file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromSisypheROI(filename: str, lib: str = 'sitk') -> tuple[list[sitkImage], dict]:
    """
        Read sitkImage

        Parameter

            filename    str
            lib         str, format of returned image 'numpy' or by default 'sitk'

        return      SimpleITK.Image
                    dict, header of Sisyphe ROI image format, key = string of field, value of field
    """
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == getSisypheROIExt()[0]:
            f = open(filename, 'rb')
            try:
                buff = f.read(16)
                if len(buff) != 16:
                    raise IOError('{} is not a Sisyphe ROI.'.format(filename))
                buff = unpack('<3H6B4x', buff)
                fields = ['Dimx', 'Dimy', 'Dimz', 'Depth', 'Dummy', 'Blue', 'Green', 'Red', 'Alpha']
                hdr = dict(zip(fields, buff))
                x, y, z, d = hdr['Dimx'], hdr['Dimy'], hdr['Dimz'], hdr['Depth']
                s = x * y * z * d
                buff = f.read(s)
                buff = frombuffer(buff, 'uint8')
                if d == 1: buff = buff.reshape((z, y, x))
                else: buff = buff.reshape((d, z, y, x))
                if lib == 'numpy':
                    return buff, hdr
                else:
                    r = list()
                    if d == 1:
                        img = sitkGetImageFromArray(buff)
                        img.SetDirection(getSisypheDirections())
                        r.append(img)
                    else:
                        for i in range(d):
                            img = sitkGetImageFromArray(buff[i, :, :, :])
                            img.SetDirection(getSisypheDirections())
                            r.append(img)
                    QApplication.processEvents()
                    return r, hdr
            except IOError: raise IOError('{} is not a Sisyphe ROI file.'.format(filename))
            finally:
                f.close()
        else: raise IOError('{} is not a Sisyphe ROI file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readFromDicomDirectory(directory: str) -> sitkImage:
    """
        Read DICOM files in a directory

        Parameter

            directory   str, directory of the dicom files to convert

        return SimpleITK.Image
    """
    if isdir(directory):
        if exists(directory):
            r = sitkImageSeriesReader()
            ids = r.GetGDCMSeriesIDs(directory)
            if len(ids) == 1:
                filenames = r.GetGDCMSeriesFileNames(directory, ids[0])
                r.SetFileNames(filenames)
                img = r.Execute()
                s = img.GetSize()
                if img.GetDimension() == 4:
                    if s[3] == 1: img = img[:, :, :, 0]
                    else: raise ValueError('4D SimpleITK images are not supported.')
                QApplication.processEvents()
                return img
            else: raise IOError('multiple series in {}.'.format(directory))
        else: raise IOError('no such file {}.'.format(directory))
    else: raise IOError('{} is not a directory.'.format(directory))


def readFromDicomSeries(filename: list[str]) -> sitkImage:
    """
        Read a list of DICOM files

        Parameter

            filename    str, one dicom filename of the series to convert

        return SimpleITK.Image
    """
    if isinstance(filename, list):
        filename = filename[0]
    if isinstance(filename, str):
        if exists(filename):
            ds = dcmread(filename)
            uid = ds['SeriesInstanceUID'].value
            r = sitkImageSeriesReader()
            filenames = r.GetGDCMSeriesFileNames(dirname(filename), uid)
            r.SetFileNames(filenames)
            img = r.Execute()
            s = img.GetSize()
            if img.GetDimension() == 4:
                if s[3] == 1: img = img[:, :, :, 0]
                else: raise ValueError('4D SimpleITK images are not supported.')
            QApplication.processEvents()
            return img
        else: raise ValueError('No such file {}.'.format(filename))
    else: raise TypeError('parameter type {} is not list of str or str.'.format(type(filename)))


def readFromDicomFilenames(filenames: list[str]) -> sitkImage:
    """
        Read a list of DICOM files

        Parameter

            filenames   list[str], dicom filenames to convert

        return SimpleITK.Image
    """
    if isinstance(filenames, list):
        r = sitkImageSeriesReader()
        r.SetFileNames(filenames)
        img = r.Execute()
        s = img.GetSize()
        if img.GetDimension() == 4:
            if s[3] == 1: img = img[:, :, :, 0]
            else: raise ValueError('4D SimpleITK images are not supported.')
        QApplication.processEvents()
        return img
    else: raise TypeError('parameter type {} is not list of str'.format(type(filenames)))


def writeToNIFTI(img: sitkImage, filename: str, compression: bool = False) -> None:
    """
        Write SimpleITK image to disk with NIFTI format (.nii, .hdr, .img, .nia, .nii.gz, .img.gz)

        Parameters

            img             SimpleITK.Image
            filename        str
            compression     bool, write compressed format nii.gz if True, default is False
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        if compression: filename += getNiftiCompressedExt()[0]
        else: filename += getNiftiExt()[0]
        w = sitkImageFileWriter()
        w.SetUseCompression(compression)
        w.SetImageIO('NiftiImageIO')
        w.SetFileName(filename)
        w.Execute(img)
        QApplication.processEvents()
    else: raise TypeError('parameter image type {} is not sitkImage.'.format(type(img)))


def writeToNRRD(img: sitkImage, filename: str) -> None:
    """
        Write SimpleITK image to disk with NRRD format (.nrrd, .nhdr)

        Parameters

            img         SimpleITK.Image
            filename    str
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        filename += getNrrdExt()[0]
        w = sitkImageFileWriter()
        w.SetImageIO('NrrdImageIO')
        w.SetFileName(filename)
        w.Execute(img)
        QApplication.processEvents()
    else: raise IOError('parameter image type {} is not sitkImage.'.format(type(img)))


def writeToMINC(img: sitkImage, filename: str) -> None:
    """
        Write SimpleITK image to disk with MINC format (.mnc)

        Parameters

            img         SimpleITK.Image
            filename    str
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        filename += getMincExt()[0]
        w = sitkImageFileWriter()
        w.SetImageIO('MINCImageIO')
        w.SetFileName(filename)
        w.Execute(img)
        QApplication.processEvents()
    else: raise IOError('parameter image type {} is not sitkImage.'.format(type(img)))


def writeToJSON(img: sitkImage, filename: str) -> None:
    """
        Write SimpleITK image to disk with JSON format (.json)

        Parameters

            img         SimpleITK.Image
            filename    str
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        filename += getJsonExt()[0]
        vtkimg = convertSITKtoVTK(img)
        w = vtkJSONImageWriter()
        w.SetInputData(vtkimg)
        w.SetFileName(filename)
        w.Write()
        QApplication.processEvents()
    else: raise IOError('parameter image type {} is not sitkImage.'.format(type(img)))


def writeToVTK(img: sitkImage, filename: str) -> None:
    """
        Write SimpleITK image to disk with VTK format (.vtk)

        Parameters

            img         SimpleITK.Image
            filename    str
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        filename += getVtkExt()[0]
        w = sitkImageFileWriter()
        w.SetImageIO('VTKImageIO')
        w.SetFileName(filename)
        w.Execute(img)
        QApplication.processEvents()
    else: raise IOError('parameter image type {} is not sitkImage.'.format(type(img)))


def writeToNumpy(img: sitkImage, filename: str) -> None:
    """
        Write SimpleITK image to disk with Numpy format (.npy)

        Parameters

            img         SimpleITK.Image
            filename    str
    """
    if isinstance(img, sitkImage):
        filename, ext = splitext(filename.lower())
        filename += getNumpyExt()[0]
        # GetArrayViewFromImage return array with default shape (z, y, x)
        save(filename, sitkGetArrayViewFromImage(img))
    else: raise IOError('parameter image type {} is not sitkImage.'.format(type(img)))
