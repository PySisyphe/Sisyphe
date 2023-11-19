"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            http://stnava.github.io/ANTs/                               Image registration
        ITK             https://itk.org/                                            Medical image processing
        Numpy           https://numpy.org/                                          Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os.path import exists
from os.path import join
from os.path import split
from os.path import splitext
from os.path import basename
from os.path import dirname

from xml.dom import minidom

from zlib import compress
from zlib import decompress

from hashlib import md5

from numpy import stack
from numpy import nanmean
from numpy import nanmedian
from numpy import nanpercentile
from numpy import nanstd
from numpy import nanmax
from numpy import nanmin
from numpy import nanargmin
from numpy import nanargmax
from numpy import frombuffer
from numpy import copy as np_copy
from numpy import array as np_array
from numpy import ndarray as np_ndarray

from ants.core import ANTsImage

from itk import Image as itkImage

from SimpleITK import Image as sitkImage
from SimpleITK import Cast as sitkCast
from SimpleITK import ComposeImageFilter as sitkComposeImageFilter
from SimpleITK import VectorIndexSelectionCastImageFilter as sitkVectorIndexSelectionCastImageFilter

from vtk import vtkImageData

import Sisyphe.core as sc
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.core.sisypheTransform import SisypheTransforms
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
from Sisyphe.core.sisypheImageAttributes import SisypheACPC
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheVolume',
           'SisypheVolumeCollection',
           'multiComponentSisypheVolumeFromList']

"""
    Function

        multiComponentSisypheVolumeFromList(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume
    
    Creation: 12/04/2023
    Revisions:
    
        01/09/2023  type hinting
"""


def multiComponentSisypheVolumeFromList(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    if isinstance(vols, (list, SisypheVolumeCollection)):
        lsitk = list()
        fov = vols[0].getFieldOfView()
        dtype = vols[0].getDatatype()
        for vol in vols:
            if isinstance(vol, SisypheVolume):
                if vol.getFieldOfView() == fov and vol.getDatatype() == dtype: lsitk.append(vol.getSITKImage())
                else: raise ValueError('SisypheVolume with incompatible field of view or data type.')
            else: raise TypeError('list element type {} is not SisypheVolume.'.format(type(vol)))
        f = sitkComposeImageFilter()
        r = f.Execute(lsitk)
        vol = SisypheVolume()
        vol.setSITKImage(r)
        # copy attributes of the first SisypheVolume in the list
        vol.copyAttributesFrom(vols[0])
        return vol
    else: raise TypeError('parameter type {} is not list.'.format(type(vols)))


"""
    Class hierarchy
    
        object -> SisypheImage -> SisypheVolume
               -> SisypheVolumeCollection
"""

imageType = sitkImage | np_ndarray | SisypheImage
imageType4 = sitkImage | np_ndarray | vtkImageData | ANTsImage
vectorFloat3 = list[float, float, float] | tuple[float, float, float]


class SisypheVolume(SisypheImage):
    """
        SisypheVolume class

        Description

            PySisyphe image class.

            SisypheVolume is in RAS+ world coordinates convention (as MNI, Nibabel, Dipy...)
            with origin to corner of the voxel
                x, direction[1.0, 0.0, 0.0]: left(-) to right(+)
                y, direction[0.0, 1.0, 0.0]: posterior(-) to anterior(+)
                z: direction[0.0, 0.0, 1.0]: inferior(-) to superior(+)

            SimpleITK, ITK, NIFTI, DICOM are in LPS+ world coordinates convention
                x: right(-) to left(+)          -> apply flipx for RAS+ conversion
                y: anterior(-) to posterior(+)  -> apply flipy for RAS+ conversion
                z: inferior(-) to superior(+)

            This class provides access to internal SimpleITK, ITK, VTK and numpy image classes,
            which share the same image buffer.

            Supported attributes:

                ID          ID number calculated from scalar values (md5 algorithm)
                identity    lastname, firstname, birthdate, gender
                acquisition modality, sequence, date of scan, stereotactic frame, signal unit
                            labels for label map modality, degrees of freedom and autocorrelations for statistical maps
                display     Look-up table, range and widow values, slope/intercept
                acpc        AC coordinates, PC coordinates, geometric transformation to geometric reference with axes
                            aligned on the AC-PC line with origin to the AC coordinates
                transforms  list of geometric transformations to all coregistered volumes
                dicom       access to Dicom fields of the associated XmlDicom file

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

            object -> SisypheImage -> SisypheVolume

        Private attributes

            _filename       str
            _compression    bool
            _patients       SisypheIdentity instance
            _acquisition    SisypheAcquisition instance
            _dislpay        SisypheDisplay instance
            _transforms     SisypheTransforms instance
            _acpc           SisypheACPC instance
            _slope          float
            _intercept      float
            _orient         int
            _ID             str, space ID (used by geometric transformations), editable, saved
            _arrayID        str, array ID, not editable, not saved, generated at creation and loading

        Properties

            identity        property(getIdentity, setIdentity)
            acquisition     property(getAcquisition, setAcquisition)
            display         property(getDisplay, setDisplay)
            transform       property(getTransforms, setTransforms)
            acpc            property(getACPC, setACPC)
            dicom           property(getXmlDicom)

        Class method

            getFileExt() -> str
            getFilterExt() -> str

        Public methods

            Arithmetic, logical and relational operators with
            int, float, SisypheVolume, SitkImage, ANTSImage and numpy array

            __str__()
            __repr__()
            updateArrayID()
            str = getID()
            setID(str | SisypheVolume)
            bool = hasSameID(ID=str | SisypheVolume | SisypheROI | SisypheMesh)
            str = getArray(ID)
            setIdentity(SisypheIdentity)
            SisypheIdentity = getIdentity()
            setAcquisition(SisypheAcquisition)
            SisypheAcquisition = getAcquisition()
            setDisplay(SisypheDisplay)
            SisypheDisplay = getDisplay()
            setTransforms(SisypheTransforms, bool)
            SisypheTransforms = getTransforms()
            bool = hasTransform()
            SisypheTransform = getTransformFromID(str)
            SisypheTransform = getTransformFromIndex(int)
            loadTransforms()
            saveTransforms()
            SisypheVolume = copy()                  override SisypheImage class
            SisypheVolume = copyComponent(int)      override SisypheImage class
            SisypheVolume, float, float = cast()    override SisypheImage class
            copyAttributesTo(SisypheVolume)
            copyAttributesFrom(SisypheVolume)
            copyPropertiesTo(SisypheVolume)
            CopyPropertiesFrom(SisypheVolume)
            setSlope(float)
            setIntercept(float)
            setDirections(list)                     override SisypheImage class
            setDefaultDirections()
            setOrientation(str)
            setOrientationToAxial()
            setOrientationToCoronal()
            setOrientationToSagittal()
            str = getOrientationAsString()
            int = getOrientation()
            bool = isAxial()
            bool = isCoronal()
            bool = isSagittal()
            float = getSlope()
            float = getIntercept()
            bool = hasFilename()
            setFilename(str)
            setFilenamePrefix(str)
            str = getFilenamePrefix()
            setFilenameSuffix(str)
            str = getFilenameSuffix()
            removeSuffixNumber()
            copyFilenameTo(SisypheVolume)
            copyFilenameFrom(SisypheVolume)
            str = getFilename()
            str = getBasename()
            str = getDirname()
            str = getName()
            setCompression(bool)
            setCompressionToOn()
            setCompressionToOff()
            bool = getCompression()
            SisypheVolume = getMask(algo: str = 'mean', dilate: int = 0, fill: bool = False)
            setTransforms(SisypheTransforms)
            SisypheTransform = getTransforms()
            bool = hasTransform(str)                    str is image ID (md5)
            SisypheTransform = getTransformFromID(str)  str is image ID (md5)
            SisypheTransform = getTransformFromIndex(int)
            bool = isICBM()
            bool = hasICBMTransform()
            SisypheTransform = getICBMTransform()
            [float, float, float] = getICBMfromWorld( [float, float, float])
            [float, float, float] = getWorldfromICBM( [float, float, float])
            bool = hasLEKSELLTransform()
            SisypheTransform = getLEKSELLTransform()
            [float, float, float] = getLEKSELLfromWorld([float, float, float])
            [float, float, float] = getWorldfromLEKSELL([float, float, float])
            [float, float, float] = getWorldfromTransform(str, [float, float, float])
            bool = hasXmlDicom()
            XmlDicom = getXmlDicom()
            loadXmlDicom()
            clearXmlDicom()
            parseXML(minidom.Document)
            createXML(minidom.Document, minidom.Document.documentElement)
            save(str)
            saveAs(str)
            load(str)
            loadFromSisyphe(str)
            loadFromNIFTI(str, bool)                override SisypheImage class
            loadFromNRRD(str)                       override SisypheImage class
            loadFromMINC(str)                       override SisypheImage class
            loadFromVTK(str)                        override SisypheImage class
            loadFromNumpy(str)                      override SisypheImage class
            saveFromNIFTI(str)                      override SisypheImage class
            saveFromNRRD(str)                       override SisypheImage class
            saveFromMINC(str)                       override SisypheImage class
            saveFromVTK(str)                        override SisypheImage class
            saveFromNumpy(str)                      override SisypheImage class
            loadTransforms()
            saveTransforms()

            inherited SisypheImage class

        Creation: 04/02/2021
        Revisions:

            08/05/2022  new IO methods for single file *.xvol format
            09/06/2023  addition of arithmetic, logic and relational operator overloading
            20/07/2023  add IO method loadFromBrainVoyagerVMR(), to open brainvoyager VMR file
            25/07/2023  add methods setFilenamePrefix(), setFilenameSuffix()
            25/07/2023  add methods getFilenamePrefix(), getFilenameSuffix()
            27/07/2023  add methods for accessing to XmlDicom file associated with PySisyphe volume instance
                        add hasXmlDicom() method
                        add getXmlDicom() method
                        add loadXmlDicom() method
                        add clearXmlDicom() method
                        add dicom property (alias to getXmlDicom() getter method)
            25/08/2023  add hasSameID() method
            02/09/2023  type hinting
            19/10/2023  _updateImages() method, set acquisition type attribute to '3D' if isotropic
            30/10/2023  add openVolume() class method
            07/11/2023  add removeSuffixNumber() method
    """
    __slots__ = ['_ID', '_arrayID', '_filename', '_compression', '_identity', '_acquisition',
                 '_display', '_acpc', '_transforms', '_xdcm', '_slope', '_intercept', '_orientation']

    # Class constants

    _FILEEXT = '.xvol'
    _UNSPECIFIED, _AXIAL, _CORONAL, _SAGITTAL, = 0, 1, 2, 3

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe volume (*{})'.format(cls._FILEEXT)

    @classmethod
    def openVolume(cls, filename: str) -> SisypheVolume:
        if exists(filename):
            base, ext = splitext(filename)[1]
            if ext == '.gz':
                base, ext2 = splitext(base)
                ext = ext2 + ext
            r = SisypheVolume()
            from Sisyphe.core.sisypheConstants import getNiftiExt
            from Sisyphe.core.sisypheConstants import getMincExt
            from Sisyphe.core.sisypheConstants import getNrrdExt
            from Sisyphe.core.sisypheConstants import getVtkExt
            from Sisyphe.core.sisypheConstants import getSisypheExt
            from Sisyphe.core.sisypheConstants import getBrainVoyagerVMRExt
            ext = ext.lower()
            if ext == cls.getFileExt(): r.load(filename)
            elif ext in getBrainVoyagerVMRExt(): r.loadFromBrainVoyagerVMR(filename)
            elif ext in getNiftiExt(): r.loadFromNIFTI(filename)
            elif ext in getMincExt(): r.loadFromMINC(filename)
            elif ext in getNrrdExt(): r.loadFromNRRD(filename)
            elif ext in getVtkExt(): r.loadFromVTK(filename)
            elif ext in getSisypheExt(): r.loadFromSisyphe(filename)
            else: raise IOError('{} format is not supported.'.format(ext))
            return r

    # Special methods

    def __init__(self, image: str | imageType4 | SisypheVolume | None = None, **kargs) -> None:
        """
            image   SisypheVolume, SisypheImage, sitkImage, vtkImageData, ANTSImage, Numpy instance

            copy    bool, True copy image to SisypheBinaryImage if datatype is unit8
                    False create a new SisypheBinaryImage with the same geometry
                    (matrix, spacing, origin, orientation) as the image
            image   SisypheImage, sitkImage, vtkImageData, ANTSImage or Numpy instance

            kargs :
                size        (int, int, int)
                datatype    (str)
                spacing     (float float float)
                direction   (float float float float float float float float float)
        """
        if isinstance(image, SisypheVolume):
            self._arrayID = image._arrayID
            self._filename = image._filename
            self.copyAttributesFrom(image)
            image = image.getSITKImage()
        else:
            self._ID = None
            self._arrayID = None
            self._filename = ''
            self._orientation = self._UNSPECIFIED
            self._compression = False
            self._identity = SisypheIdentity(parent=self)
            self._acquisition = SisypheAcquisition(parent=self)
            self._display = SisypheDisplay(parent=self)
            self._acpc = SisypheACPC(parent=self)
            self._transforms = SisypheTransforms()
            self._slope = 1.0
            self._intercept = 0.0
            self._xdcm = None
        super().__init__(image, **kargs)

    def __str__(self) -> str:
        buff = 'Array ID: {}\n'.format(self.getArrayID())
        buff += 'Transform ID: {}\n'.format(self.getID())
        buff += 'Filename: {}\n'.format(basename(self._filename))
        buff += super().__str__()
        buff += '\tOrientation: {}\n' \
                '\tSlope: {}\n' \
                '\tIntercept: {}\n'.format(self.getOrientationAsString(),
                                           str(self._slope), str(self._intercept))
        buff += str(self._identity)
        buff += str(self._acquisition)
        buff += str(self._display)
        buff += str(self._acpc)
        return buff

    def __repr__(self) -> str:
        return 'SisypheVolume instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Arithmetic operators

    def __add__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__add__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __sub__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__sub__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __mul__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__mul__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __div__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__div__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __floordiv__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__floordiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __truediv__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__truediv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __radd__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__radd__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rsub__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rsub__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rmul__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rmul__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rdiv__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rdiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rfloordiv__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rfloordiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rtruediv__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rtruediv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __neg__(self) -> SisypheVolume:
        r = SisypheVolume(self._sitk_image.__neg__())
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __pos__(self) -> SisypheVolume:
        return self

    # Logic operators

    def __and__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__and__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rand__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rand__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __or__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__or__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __ror__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__ror__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __xor__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__xor__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rxor__(self, other: imageType) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rxor__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __invert__(self) -> SisypheVolume:
        r = SisypheVolume(self._sitk_image.__invert__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    # Relational operators

    def __lt__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__lt__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __le__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__le__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __eq__(self, other: imageType | int | float) -> bool | SisypheVolume:
        if isinstance(other, SisypheVolume): return id(self) == id(other)
        elif isinstance(other, (int, float)):
            r = SisypheVolume(self._sitk_image.__eq__(other))
            r.copyAttributesFrom(self, display=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequenceToAlgebraMap()
            return r

    def __ne__(self, other: imageType | int | float) -> bool | SisypheVolume:
        if isinstance(other, SisypheVolume): return id(self) != id(other)
        elif isinstance(other, (int, float)):
            r = SisypheVolume(self._sitk_image.__ne__(other))
            r.copyAttributesFrom(self, display=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequenceToAlgebraMap()
            return r

    def __gt__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__gt__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __ge__(self, other: imageType | int | float) -> SisypheVolume:
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__ge__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    # get pixel methods

    def __getitem__(self, idx):
        r = self._sitk_image.__getitem__(idx)
        if isinstance(r, sitkImage):
            r = SisypheVolume(r)
            r.copyAttributesFrom(self, id=False, display=False, acpc=False, transform=False)
        return r

    # Private method

    def _calcArrayID(self) -> None:
        if not self.isEmpty():
            m = md5()
            m.update(self._numpy_array.tostring())
            self._arrayID = m.hexdigest()

    def _calcID(self) -> None:
        if not self.isEmpty():
            self._calcArrayID()
            if self._ID is None: self._ID = self._arrayID
            self._transforms.setReferenceID(self._ID)

    def _updateOrientation(self) -> None:
        self._orientation = self._UNSPECIFIED
        if self.getSITKImage().GetDepth() == 3:
            i1 = abs(np_array(self.getFirstVectorDirection())).argmax()
            i2 = abs(np_array(self.getSecondVectorDirection())).argmax()
            i3 = abs(np_array(self.getThirdVectorDirection())).argmax()
            if i1 == 0 and i2 == 1 and i3 == 2: self._orientation = self._AXIAL
            elif i1 == 0 and i2 == 2 and i3 == 1: self._orientation = self._CORONAL
            elif i1 == 1 and i2 == 2 and i3 == 0: self._orientation = self._SAGITTAL

    def _updateRange(self) -> None:
        # bugfix, conversion numpy.float32 to float
        vmin = float(str(self.getNumpy().min()))
        vmax = float(str(self.getNumpy().max()))
        if vmin != self._display.getRangeMin() or vmax != self._display.getRangeMax():
            self._display.setRange(vmin, vmax)
            self._display.setDefaultWindow()
        else: self.display.updateVTKLUT()

    def _updateImages(self) -> None:
        super()._updateImages()
        self._updateOrientation()
        self._updateRange()
        self._calcID()
        if self.isIsotropic(tol=0.0) and self.getSpacing()[0] <= 1.0: self.acquisition.set3D()
        k = self._sitk_image.GetMetaDataKeys()
        if 'scl_inter' in k: self._intercept = self._sitk_image.GetMetaData('scl_inter')
        else: self._intercept = 0.0
        if 'scl_slope' in k: self._slope = self._sitk_image.GetMetaData('scl_slope')
        else: self._slope = 1.0

    # Public methods

    def copyFromSITKImage(self, img: sitkImage) -> None:
        super().copyFromSITKImage(img)
        self._updateRange()

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        super().copyFromVTKImage(img)
        self._updateRange()

    def copyFromITKImage(self, img: itkImage) -> None:
        super().copyFromITKImage(img)
        self._updateRange()

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        super().copyFromANTSImage(img)
        self._updateRange()

    def copyFromNumpyArray(self,
                           img: np_ndarray,
                           spacing: vectorFloat3 = (1.0, 1.0, 1.0),
                           origin: vectorFloat3 = (0, 0, 0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True) -> None:
        super().copyFromNumpyArray(img, spacing, origin, direction, defaultshape)
        self._updateRange()

    def setSITKImage(self, img: sitkImage) -> None:
        super().setSITKImage(img)
        self._updateRange()

    def getID(self) -> str:
        if self._ID is None: return 'None'
        else: return self._ID

    def setID(self, ID: str | SisypheVolume) -> None:
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            self._ID = ID
            self._transforms.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def hasSameID(self, ID: str | SisypheVolume | sc.sisypheROI.SisypheROI | sc.sisypheMesh.SisypheMesh) -> str:
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        elif isinstance(ID, sc.sisypheROI.SisypheROI): ID = ID.getReferenceID()
        elif isinstance(ID, sc.sisypheMesh.SisypheMesh): ID = ID.getReferenceID()
        if isinstance(ID, str):
            return self._ID == ID

    def getArrayID(self) -> str:
        return self._arrayID

    def updateArrayID(self) -> None:
        self._calcArrayID()

    def setIdentity(self, identity: SisypheIdentity) -> None:
        if isinstance(identity, SisypheIdentity):
            self._identity = identity
            self._identity.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))

    def getIdentity(self) -> SisypheIdentity:
        return self._identity

    def setAcquisition(self, acquisition: SisypheAcquisition) -> None:
        if isinstance(acquisition, SisypheAcquisition):
            self._acquisition = acquisition
            self._acquisition.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheAcquisition.'.format(type(acquisition)))

    def getAcquisition(self) -> SisypheAcquisition:
        return self._acquisition

    def setDisplay(self, display: SisypheDisplay) -> None:
        if isinstance(display, SisypheDisplay):
            self._display = display
            self._display.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheDislpay.'.format(type(display)))

    def removeDisplay(self) -> None:
        self._display = None

    def getDisplay(self) -> SisypheDisplay:
        return self._display

    def setACPC(self, acpc: SisypheACPC) -> None:
        if isinstance(acpc, SisypheACPC):
            self._acpc = acpc
            self._acpc.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheACPC.'.format(type(acpc)))

    def getACPC(self) -> SisypheACPC:
        return self._acpc

    def copy(self) -> SisypheVolume:
        if not self.isEmpty():
            img = SisypheVolume(self)
            self.copyAttributesTo(img)
            img._filename = self._filename
            img._ID = self._ID
            return img
        else: raise TypeError('SisypheImage is empty.')

    def copyComponent(self, c: int) -> SisypheVolume:
        n = self.getNumberOfComponentsPerPixel()
        if n > 1:
            if isinstance(c, int):
                if c < n:
                    f = sitkVectorIndexSelectionCastImageFilter()
                    f.SetIndex(c)
                    img = SisypheVolume(f.Execute(self.getSITKImage()))
                    self.copyAttributesTo(img)
                    return img
                else: raise IndexError('parameter value {} is out of range.'.format(c))
            else: raise TypeError('parameter type {} is not int.'.format(type(c)))
        else: raise ValueError('Image has only one component.')

    def cast(self, datatype: str) -> SisypheVolume:
        img, slope, inter = super().cast(datatype)
        img = SisypheVolume(img)
        self.copyAttributesTo(img)
        img._slope = slope
        img._intercept = inter
        img._updateRange()
        img._calcArrayID()
        return img

    def copyPropertiesTo(self,
                         img: SisypheVolume,
                         identity: bool = True,
                         acquisition: bool = True,
                         display: bool = True,
                         acpc: bool = True,
                         slope: bool = True) -> None:
        if isinstance(img, SisypheVolume):
            if identity: img._identity.copyFrom(self._identity)
            if acquisition: img._acquisition.copyFrom(self._acquisition)
            if display: img._display.copyFrom(self._display)
            if acpc: img._acpc.copyFrom(self._acpc)
            img._compression = self._compression
            img._orientation = self._orientation
            if slope:
                img._slope = self._slope
                img._intercept = self._intercept
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def copyPropertiesFrom(self,
                           img: SisypheVolume,
                           identity: bool = True,
                           acquisition: bool = True,
                           display: bool = True,
                           acpc: bool = True,
                           slope: bool = True) -> None:
        if isinstance(img, SisypheVolume):
            if identity: self._identity.copyFrom(img._identity)
            if acquisition: self._acquisition.copyFrom(img._acquisition)
            if display: self._display.copyFrom(img._display)
            if acpc: self._acpc.copyFrom(img._acpc)
            self._compression = img._compression
            self._orientation = img._orientation
            if slope:
                self._slope = img._slope
                self._intercept = img._intercept
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def copyAttributesTo(self,
                         img: SisypheVolume,
                         id: bool = True,
                         identity: bool = True,
                         acquisition: bool = True,
                         display: bool = True,
                         acpc: bool = True,
                         transform: bool = True,
                         slope: bool = True) -> None:
        if isinstance(img, SisypheVolume):
            self.copyPropertiesTo(img, identity, acquisition, display, acpc, slope)
            if id: img.setID(self.getID())
            if transform:
                img._transforms = self._transforms.copy()
                img._transforms.setReferenceID(img.getID())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def copyAttributesFrom(self,
                           img: SisypheVolume,
                           id: bool = True,
                           identity: bool = True,
                           acquisition: bool = True,
                           display: bool = True,
                           acpc: bool = True,
                           transform: bool = True,
                           slope: bool = True) -> None:
        if isinstance(img, SisypheVolume):
            self.copyPropertiesFrom(img,  identity, acquisition, display, acpc, slope)
            if id: self.setID(img.getID())
            if transform:
                self._transforms = img._transforms.copy()
                self._transforms.setReferenceID(self.getID())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def setSlope(self, slope: float = 1.0) -> None:
        self._slope = slope

    def setIntercept(self, intercept: float = 0.0) -> None:
        self._intercept = intercept

    def setDirections(self, direction: tuple = tuple(getRegularDirections())) -> None:
        super().setDirections(direction)
        self._updateOrientation()

    def setDefaultDirections(self) -> None:
        self.setDirections()

    def setOrientation(self, orient: str = 'axial') -> None:
        if orient == 'axial':
            self._orientation = self._AXIAL
        elif orient == 'coronal':
            self._orientation = self._CORONAL
        elif orient == 'sagittal':
            self._orientation = self._SAGITTAL
        else:
            self._orientation = self._UNSPECIFIED

    def setOrientationToAxial(self) -> None:
        self._orientation = self._AXIAL

    def setOrientationToCoronal(self) -> None:
        self._orientation = self._CORONAL

    def setOrientationToSagittal(self) -> None:
        self._orientation = self._SAGITTAL

    def getOrientationAsString(self) -> str:
        if self._orientation == self._AXIAL:
            return 'axial'
        elif self._orientation == self._CORONAL:
            return 'coronal'
        elif self._orientation == self._SAGITTAL:
            return 'sagittal'
        else:
            return 'unspecified'

    def getOrientation(self) -> int:
        return self._orientation

    def isAxial(self) -> bool:
        return self._orientation == self._AXIAL

    def isCoronal(self) -> bool:
        return self._orientation == self._CORONAL

    def isSagittal(self) -> bool:
        return self._orientation == self._SAGITTAL

    def getSlope(self) -> float:
        return self._slope

    def getIntercept(self) -> float:
        return self._intercept

    def hasFilename(self) -> bool:
        return self._filename != ''

    def getFilename(self) -> str:
        return self._filename

    def getDirname(self) -> str:
        return dirname(self._filename)

    def getBasename(self) -> str:
        return basename(self._filename)

    def getName(self) -> str:
        return splitext(basename(self._filename))[0]

    def copyFilenameTo(self, vol: SisypheVolume) -> None:
        if isinstance(vol, SisypheVolume):
            vol._filename = self._filename
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def copyFilenameFrom(self, vol: SisypheVolume) -> None:
        if isinstance(vol, SisypheVolume):
            self._filename = vol.getFilename()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setFilename(self, filename: str) -> None:
        if filename == '':
            filename = '{}_{}_{}_{}_{}_{}{}'.format(self._identity.getLastname(),
                                                    self._identity.getFirstname(),
                                                    self._identity.getDateOfBirthday(),
                                                    self.acquisition.getModality(),
                                                    self.acquisition.getDateOfScan(),
                                                    self.acquisition.getSequence(),
                                                    self._FILEEXT)
        else:
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
        self._filename = filename
        self._transforms.setFilenameFromVolume(self)

    def setFilenamePrefix(self, prefix: str, sep: str = '_') -> None:
        if isinstance(prefix, str):
            if prefix[-1] == sep: prefix = prefix[:-1]
            self._filename = join(dirname(self._filename), '{}{}{}'.format(prefix, sep, basename(self._filename)))
        else: raise TypeError('parameter type {} is not str.'.format(prefix))

    def getFilenamePrefix(self, sep: str = '_') -> str:
        r = self.getName().split(sep)
        if len(r) > 0: return r[0]
        else: return ''

    def setFilenameSuffix(self, suffix: str, sep: str = '_') -> None:
        if isinstance(suffix, str):
            if suffix[0] == sep: suffix = suffix[1:]
            root, ext = splitext(basename(self._filename))
            self._filename = join(dirname(self._filename), '{}{}{}{}'.format(root, sep, suffix, ext))
        else: raise TypeError('parameter type {} is not str.'.format(suffix))

    def getFilenameSuffix(self, sep: str = '_') -> str:
        r = self.getName().split(sep)
        if len(r) > 0: return r[-1]
        else: return ''

    def removeSuffixNumber(self) -> None:
        base, ext = splitext(self._filename)
        splt1 = base.split(' ')
        splt2 = base.split('_')
        if len(splt1[-1]) < len(splt2[-1]):
            splt = splt1
            s = ' '
        else:
            splt = splt2
            s = '_'
        sfx = splt[-1]
        if sfx[0] == '#': sfx = sfx[1:]
        if sfx.isnumeric(): splt = splt[:-1]
        self._filename = s.join(splt).rstrip(' _-#') + ext

    def setCompression(self, v: bool) -> None:
        if isinstance(v, bool): self._compression = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCompressionOn(self) -> None:
        self._compression = True

    def setCompressionOff(self) -> None:
        self._compression = False

    def getCompression(self) -> bool:
        return self._compression

    def getMask(self,
                algo: str = 'mean',
                morpho: str = '',
                niter: int = 1,
                kernel: int = 0,
                fill: str = '') -> SisypheVolume:
        vol = SisypheVolume(super().getMask(algo, morpho, niter, kernel, fill))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('mask')
        vol.acquisition.setModalityToOT()
        vol.acquisition.setSequenceToMask()
        return vol

    def getMaskROI(self,
                   name: str = 'Mask',
                   algo: str = 'mean',
                   morpho: str = '',
                   niter: int = 1,
                   kernel: int = 0,
                   fill: str = '') -> sc.sisypheROI.SisypheROI:
        roi = super().getMaskROI(algo, morpho, niter, kernel, fill)
        roi.setReferenceID(self.getID())
        roi.getName(name)
        return roi

    def getMask2(self,
                 algo: str = 'mean',
                 morphoiter: int = 1,
                 kernel: int = 0) -> SisypheVolume:
        vol = SisypheVolume(super().getMask2(algo, morphoiter, kernel))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('mask')
        vol.acquisition.setModalityToOT()
        vol.acquisition.setSequenceToMask()
        return vol

    def getMaskROI2(self,
                    name: str = 'Mask',
                    algo: str = 'mean',
                    morphoiter: int = 1,
                    kernel: int = 0) -> sc.sisypheROI.SisypheROI:
        roi = super().getMaskROI2(algo, morphoiter, kernel)
        roi.setReferenceID(self.getID())
        roi.getName(name)
        return roi

    # Geometric transformation methods

    def setTransforms(self, transform: sc.sisypheTransform.SisypheTransform, force: bool = False) -> None:
        if isinstance(transform, SisypheTransforms):
            if force:
                self._transforms = transform
                self._transforms.setReferenceID(self.getID())
            elif transform.getReferenceID() == self.getID():
                self._transforms = transform
            else: raise ValueError('SisypheTransforms parameter and SisypheVolume do not have the same ID.')
        else: raise TypeError('parameter type {} is not SisypheTransforms.'.format(type(transform)))

    def getTransforms(self) -> SisypheTransforms:
        return self._transforms

    def hasTransform(self, ID: str | SisypheVolume) -> bool:
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            return ID in self.getTransforms()
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def hasIdentityTransform(self, ID: str | SisypheVolume) -> bool:
        r = False
        trf = self.getTransformFromID(ID)
        if trf is not None: r = trf.isIdentity()
        return r

    def getTransformFromID(self, ID: str | SisypheVolume) -> sc.sisypheTransform.SisypheTransform | None:
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            if self.hasTransform(ID): return self.getTransforms()[ID]
            else: return None
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def getTransformFromIndex(self, index: int) -> sc.sisypheTransform.SisypheTransform:
        if isinstance(index, int):
            if 0 <= index < self.getTransforms().count():
                return self.getTransforms()[index]
            else: raise IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(index)))

    def loadTransforms(self) -> None:
        filename = splitext(self._filename)[0] + self._transforms.getFileExt()
        if exists(filename): self._transforms.load(filename)
        else:  # init transforms
            self._transforms.clear()
            self._transforms.setReferenceID(self)

    def saveTransforms(self) -> None:
        if len(self._transforms) > 0 and self.hasFilename():
            path, ext = splitext(self._filename)
            filename = path + self._transforms.getFileExt()
            self._transforms.save(filename)

    def hasICBMTransform(self) -> bool:
        from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        return self.hasTransform(icbmid)

    def getICBMTransform(self) -> sc.sisypheTransform.SisypheTransform | None:
        from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        if self.hasICBMTransform(): return self._transforms[icbmid]
        elif self.acquisition.isICBM152():
            from Sisyphe.core.sisypheTransform import SisypheTransform
            trf = SisypheTransform()
            trf.setIdentity()
            trf.setID(icbmid)
        else: return None

    def getICBMfromWorld(self, p: vectorFloat3) -> vectorFloat3 | None:
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        if self.hasICBMTransform(): return self._transforms[icbmid].applyToPoint(p)
        elif self.acquisition.isICBM152(): return p
        else: return None

    def getWorldfromICBM(self, p: vectorFloat3) -> vectorFloat3 | None:
        if self.hasICBMTransform(): return self._transforms['ICBM'].applyInverseToPoint(p)
        else: return None

    def hasLEKSELLTransform(self) -> bool:
        return self.hasTransform('LEKSELL')

    def getLEKSELLTransform(self) -> sc.sisypheTransform.SisypheTransform | None:
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL']
        else: return None

    def getLEKSELLfromWorld(self, p: vectorFloat3) -> vectorFloat3 | None:
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL'].applyToPoint(p)
        else: return None

    def getWorldfromLEKSELL(self, p: vectorFloat3) -> vectorFloat3 | None:
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL'].applyInverseToPoint(p)
        else: return None

    def getWorldfromTransform(self, ID: str | SisypheVolume, p: vectorFloat3) -> vectorFloat3:
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            if self.hasTransform(ID):
                return self._transforms[ID].applyToPoint(p)
            else: return p

    # XmlDicom methods

    def hasXmlDicom(self) -> bool:
        if self.hasFilename():
            from Sisyphe.core.sisypheDicom import XmlDicom
            filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
            return exists(filename)

    def getXmlDicom(self) -> sc.sisypheDicom.XmlDicom:
        if self._xdcm is not None: return self._xdcm
        else:
            from Sisyphe.core.sisypheDicom import XmlDicom
            filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
            if exists(filename):
                self.loadXmlDicom()
                return self._xdcm

    def loadXmlDicom(self) -> None:
        filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
        if exists(filename):
            self._xdcm = sc.sisypheDicom.XmlDicom()
            self._xdcm.loadXmlDicomFilename(filename)

    def clearXmlDicom(self) -> None:
        self._xdcm = None

    # IO public methods, old format v1.0, two files (*.raw and *.xvol)
    # Deprecated methods

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
            # Save XML and raw files
            self.createXMLOld(doc)
            buff = doc.toprettyxml()
            with open(filename, 'w') as f:
                f.write(buff)
            # Save Transforms
            self.saveTransforms()
        else: raise AttributeError('Array image is empty.')

    def createXMLOld(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('ID')
            root.appendChild(node)
            txt = doc.createTextNode(self.getID())
            node.appendChild(txt)
            # Compressed
            node = doc.createElement('compressed')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._compression))
            node.appendChild(txt)
            # Image attributes nodes
            volume = doc.createElement('attributes')
            root.appendChild(volume)
            # Size
            node = doc.createElement('size')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSize())]))
            node.appendChild(txt)
            # Components
            node = doc.createElement('components')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self.getNumberOfComponentsPerPixel()))
            node.appendChild(txt)
            # Spacing
            node = doc.createElement('spacing')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSpacing())]))
            node.appendChild(txt)
            # Origin
            node = doc.createElement('origin')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getOrigin())]))
            node.appendChild(txt)
            # Orientation
            node = doc.createElement('orientation')
            volume.appendChild(node)
            txt = doc.createTextNode(self.getOrientationAsString())
            node.appendChild(txt)
            # Datatype
            node = doc.createElement('datatype')
            volume.appendChild(node)
            txt = doc.createTextNode(self.getDatatype())
            node.appendChild(txt)
            # Directions
            node = doc.createElement('directions')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getDirections())]))
            node.appendChild(txt)
            # Slope
            node = doc.createElement('slope')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self._slope))
            node.appendChild(txt)
            # Intercept
            node = doc.createElement('intercept')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self._intercept))
            node.appendChild(txt)
            # Identity nodes
            self._identity.createXML(doc, root)
            # Acquisition nodes
            self._acquisition.createXML(doc, root)
            # Dislpay nodes
            self._display.createXML(doc, root)
            # Array
            node = doc.createElement('array')
            root.appendChild(node)
            path, ext = splitext(self._filename)
            filename = path + '.raw'
            txt = doc.createTextNode(split(filename)[1])
            node.appendChild(txt)
            # Save raw data
            buff = self.getNumpy().tobytes()
            if self._compression: buff = compress(buff)
            with open(filename, 'wb') as f:
                f.write(buff)
        else: raise TypeError('parameter functype is not xml.dom.minidom.Document.')

    def parseXMLOld(self, doc: minidom.Document) -> None:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
            size = None
            spacing = None
            origin = None
            directions = None
            datatype = None
            components = 1  # Default
            # Identity nodes
            self._identity.parseXML(doc)
            # Acquisition nodes
            self._acquisition.parseXML(doc)
            # Display nodes
            self._display.parseXML(doc)
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'ID':
                    self._ID = node.firstChild.data
                    if self._ID == 'None': self._ID = None
                # Compressed
                elif node.nodeName == 'compressed':
                    self._compression = node.firstChild.data == 'True'
                # Image attributes nodes
                elif node.nodeName == 'attributes':
                    childnode = node.firstChild
                    while childnode:
                        if childnode.nodeName == 'size':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            size = [int(i) for i in buff]
                        elif childnode.nodeName == 'components':
                            components = int(childnode.firstChild.data)
                        elif childnode.nodeName == 'spacing':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            spacing = [float(i) for i in buff]
                        elif childnode.nodeName == 'origin':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            origin = [float(i) for i in buff]
                        elif childnode.nodeName == 'orientation':
                            self.setOrientation(childnode.firstChild.data)
                        elif childnode.nodeName == 'datatype':
                            datatype = childnode.firstChild.data
                        elif childnode.nodeName == 'directions':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            directions = [float(i) for i in buff]
                        elif childnode.nodeName == 'slope':
                            self._slope = float(childnode.firstChild.data)
                        elif childnode.nodeName == 'intercept':
                            self._intercept = float(childnode.firstChild.data)
                        childnode = childnode.nextSibling
                elif node.nodeName == 'array':
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
                    img = frombuffer(buff, dtype=datatype)
                    if components == 1: img = img.reshape((size[2], size[1], size[0]))
                    else: img = img.reshape((size[2], size[1], size[0], components))
                    self.copyFromNumpyArray(img, spacing=spacing, origin=origin,
                                            direction=directions, defaultshape=True)
                node = node.nextSibling
        else: raise IOError('XML file format is not supported.')

    def loadOld(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            # XML part
            self._filename = filename
            self.parseXMLOld(doc)
            self.loadTransforms()
        else: raise IOError('no such file : {}'.format(filename))

    # IO public methods, new format v1.1, single file *.xvol

    def save(self, filename: str = '') -> None:
        if not self.isEmpty():
            if filename != '': self.setFilename(filename)
            if self.hasFilename(): self.saveAs(self._filename)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('Data array is empty.')

    def parseXML(self, doc: minidom.Document) -> dict:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.1':
            attr = dict()
            # Identity nodes
            self._identity.parseXML(doc)
            # Acquisition nodes
            self._acquisition.parseXML(doc)
            # Display nodes
            self._display.parseXML(doc)
            # ACPC nodes
            self._acpc.parseXML(doc)
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'ID':
                    self._ID = node.firstChild.data
                    if self._ID == 'None': self._ID = None
                # Compressed
                elif node.nodeName == 'compressed':
                    self._compression = node.firstChild.data == 'True'
                # Image attributes nodes
                elif node.nodeName == 'attributes':
                    childnode = node.firstChild
                    while childnode:
                        if childnode.nodeName == 'size':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            attr['size'] = [int(i) for i in buff]
                        elif childnode.nodeName == 'components':
                            attr['components'] = int(childnode.firstChild.data)
                        elif childnode.nodeName == 'spacing':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            attr['spacing'] = [float(i) for i in buff]
                        elif childnode.nodeName == 'origin':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            attr['origin'] = [float(i) for i in buff]
                        elif childnode.nodeName == 'orientation':
                            self.setOrientation(childnode.firstChild.data)
                        elif childnode.nodeName == 'datatype':
                            attr['datatype'] = childnode.firstChild.data
                        elif childnode.nodeName == 'directions':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            attr['directions'] = [float(i) for i in buff]
                        elif childnode.nodeName == 'slope':
                            self._slope = float(childnode.firstChild.data)
                        elif childnode.nodeName == 'intercept':
                            self._intercept = float(childnode.firstChild.data)
                        childnode = childnode.nextSibling
                elif node.nodeName == 'array':
                    attr['array'] = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')

    def load(self, filename: str = '') -> None:
        if filename == '' and self.hasFilename(): filename = self._filename
        # Check extension xvol
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
        if exists(filename):
            # Read XML part
            with open(filename, 'rb') as f:
                line = ''
                strdoc = ''
                while line != '</xvol>\n':
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
                img = frombuffer(buff, dtype=attr['datatype'])
                size = attr['size']
                if attr['components'] == 1: img = img.reshape((size[2], size[1], size[0]))
                else: img = img.reshape((size[2], size[1], size[0], attr['components']))
                self.copyFromNumpyArray(img,
                                        spacing=attr['spacing'],
                                        origin=attr['origin'],
                                        direction=attr['directions'],
                                        defaultshape=True)
                if self.isIntegerDatatype(): self.display.convertRangeWindowToInt()
            else: raise IOError('no such file : {}.'.format(rawname))
            # Generate arrayID
            self._calcArrayID()
            # Read transforms *.trfs if exists
            self.loadTransforms()
            # Read labels *.labels if LB modality and exists
            self.getAcquisition().loadLabels()
        else: raise IOError('no such file : {}.'.format(filename))

    def createXML(self, doc: minidom.Document, single: bool = True) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('ID')
            root.appendChild(node)
            txt = doc.createTextNode(self.getID())
            node.appendChild(txt)
            # Compressed
            node = doc.createElement('compressed')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._compression))
            node.appendChild(txt)
            # Image attributes nodes
            volume = doc.createElement('attributes')
            root.appendChild(volume)
            # Size
            node = doc.createElement('size')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSize())]))
            node.appendChild(txt)
            # Components
            node = doc.createElement('components')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self.getNumberOfComponentsPerPixel()))
            node.appendChild(txt)
            # Spacing
            node = doc.createElement('spacing')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getSpacing())]))
            node.appendChild(txt)
            # Origin
            node = doc.createElement('origin')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getOrigin())]))
            node.appendChild(txt)
            # Orientation
            node = doc.createElement('orientation')
            volume.appendChild(node)
            txt = doc.createTextNode(self.getOrientationAsString())
            node.appendChild(txt)
            # Datatype
            node = doc.createElement('datatype')
            volume.appendChild(node)
            txt = doc.createTextNode(self.getDatatype())
            node.appendChild(txt)
            # Directions
            node = doc.createElement('directions')
            volume.appendChild(node)
            txt = doc.createTextNode(' '.join([str(i) for i in list(self.getDirections())]))
            node.appendChild(txt)
            # Slope
            node = doc.createElement('slope')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self._slope))
            node.appendChild(txt)
            # Intercept
            node = doc.createElement('intercept')
            volume.appendChild(node)
            txt = doc.createTextNode(str(self._intercept))
            node.appendChild(txt)
            # Identity nodes
            self._identity.createXML(doc, root)
            # Acquisition nodes
            self._acquisition.createXML(doc, root)
            # Dislpay nodes
            self._display.createXML(doc, root)
            # ACPC nodes
            self._acpc.createXML(doc, root)
            # Array
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
            # Save Transforms
            self.saveTransforms()
            # Save labels *.labels if LB modality
            self.acquisition.saveLabels()
        else: raise AttributeError('Data Array is empty.')

    # Public IO methods, other formats
    # Sisyphe, Nifti, Nrrd, Minc, Vtk, Numpy

    def loadFromSisyphe(self, filename: str) -> None:
        hdr = super().loadFromSisyphe(filename)
        # Identity fields
        self._identity.setLastname(hdr['lastname'].decode('latin-1'))
        self._identity.setFirstname(hdr['firstname'].decode('latin-1'))
        try:
            d, m, y = hdr['dateofbirth'].decode('latin-1').split('/')
            self._identity.setDateOfBirthday('-'.join([y, m, d]))
        except: pass
        self._identity.setGenderToUnknown()
        # Acquisition fields
        modality = hdr['modality'].decode('latin-1')[:3]
        sequence = hdr['modality'].decode('latin-1')[-3:]
        if modality == 'IRM':
            self._acquisition.setModality('MR')
            if sequence == ' T1': self._acquisition.setSequence(self._acquisition.getMRSequences()[1])
            elif sequence == ' T2': self._acquisition.setSequence(self._acquisition.getMRSequences()[2])
            elif sequence == ' DP': self._acquisition.setSequence(self._acquisition.getMRSequences()[4])
            elif sequence == 'EPI': self._acquisition.setSequence(self._acquisition.getMRSequences()[9])
            elif sequence == 'AIR': self._acquisition.setSequence(self._acquisition.getMRSequences()[5])
            elif sequence == 'DWI': self._acquisition.setSequence(self._acquisition.getMRSequences()[10])
            elif sequence == 'PWI': self._acquisition.setSequence(self._acquisition.getMRSequences()[11])
        elif modality == 'TDM': self._acquisition.setModality('CT')
        elif modality == 'TEP':
            self._acquisition.setModality('PT')
            if sequence == 'FDG':
                self._acquisition.setUnit(self._acquisition.getUnitList()[4])
                self._acquisition.setSequence(self._acquisition.getPTSequences()[1])
        elif modality == 'SPE':
            self._acquisition.setModality('NM')
            self._acquisition.setUnit(self._acquisition.getUnitList()[4])
            if sequence == 'PAO': self._acquisition.setSequence(self._acquisition.getNMSequences()[1])
            elif sequence == 'ECD': self._acquisition.setSequence(self._acquisition.getNMSequences()[2])
            elif sequence == 'CAN': self._acquisition.setSequence(self._acquisition.getNMSequences()[3])
        else:
            self._acquisition.setModality('OT')
            if sequence == 'E T':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[1])
                self._acquisition.setUnit(self._acquisition.getUnitList()[9])
            elif sequence == ' SG':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[3])
                self._acquisition.setUnit(self._acquisition.getUnitList()[1])
            elif sequence == ' SB':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[4])
                self._acquisition.setUnit(self._acquisition.getUnitList()[1])
            elif sequence == 'LCR':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[5])
                self._acquisition.setUnit(self._acquisition.getUnitList()[1])
            elif sequence == 'DSC': self._acquisition.setSequence(self._acquisition.getOTSequences()[7])
            elif sequence == 'VSC': self._acquisition.setSequence(self._acquisition.getOTSequences()[8])
            elif sequence == 'TTM':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[9])
                self._acquisition.setUnit(self._acquisition.getUnitList()[2])
            elif sequence == ' FA':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[12])
                self._acquisition.setUnit(self._acquisition.getUnitList()[1])
            elif sequence == 'ADC':
                self._acquisition.setSequence(self._acquisition.getOTSequences()[13])
                self._acquisition.setUnit(self._acquisition.getUnitList()[6])
            elif sequence == 'ROI': self._acquisition.setSequence(self._acquisition.getOTSequences()[17])
        if self._acquisition.getSequence() == '':
            self._acquisition.setSequence(hdr['sequence'].decode('latin-1'))
        try:
            d, m, y = hdr['dateofscan'].decode('latin-1').split('/')
            self._acquisition.setDateOfScan('-'.join([y, m, d]))
        except: pass
        # Attribute fields
        self._slope = hdr['scale']
        self._intercept = hdr['intercept']
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def loadFromBrainVoyagerVMR(self, filename: str) -> None:
        super().loadFromBrainVoyagerVMR(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def loadFromNIFTI(self, filename: str, reorient: bool = True) -> None:
        super().loadFromNIFTI(filename, reorient)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToNIFTI(self, filename: str = '', compress: bool = False) -> None:
        if filename == '': filename = splitext(self.getFilename())[0] + getNiftiExt()[0]
        super().saveToNIFTI(filename, compress)

    def loadFromNRRD(self, filename: str) -> None:
        super().loadFromNRRD(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToNRRD(self, filename: str = '') -> None:
        if filename == '': filename = splitext(self.getFilename())[0] + getNrrdExt()[0]
        super().saveToNRRD(filename)

    def loadFromMINC(self, filename: str) -> None:
        super().loadFromMINC(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToMINC(self, filename: str = '') -> None:
        if filename == '': filename = splitext(self.getFilename())[0] + getMincExt()[0]
        super().saveToMINC(filename)

    def loadFromVTK(self, filename: str) -> None:
        super().loadFromVTK(filename)
        self._calcID()
        self._updateRange()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToVTK(self, filename: str = '') -> None:
        if filename == '': filename = splitext(self.getFilename())[0] + getVtkExt()[1]
        super().saveToVTK(filename)

    def loadFromNumpy(self, filename: str) -> None:
        super().loadFromNumpy(filename)
        self._calcID()
        self._updateRange()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToNumpy(self, filename: str = '') -> None:
        if filename == '': filename = splitext(self.getFilename())[0] + getNumpyExt()[0]
        super().saveToNumpy(filename)

    # Properties

    identity = property(getIdentity, setIdentity)
    acquisition = property(getAcquisition, setAcquisition)
    display = property(getDisplay, setDisplay)
    transforms = property(getTransforms, setTransforms)
    acpc = property(getACPC, setACPC)
    dicom = property(getXmlDicom)


class SisypheVolumeCollection(object):
    """
        SisypheVolumeCollection

        Description

            Container of SisypheVolume instances.
            List-like methods with int index.
            Dict-like access with str (SisypheVolume arrayID) as key, no duplication.
            Setter and getter methods of SisypheVolume, to get or set attributes of all SisypheVolume.
            Getter methods returns a list.
            Setter methods parameter is a single attribute value or a list of the same size as the container.

        Inheritance

            object -> SisypheVolumeCollection

        Private attributes

            _volumes        list of SisypheVolume
            _index          index for Iterator
            _homogeneous    all volumes have the same data type and field of view (True) or not (False)

        Public methods

            __getitem__(int | str)
            __setitem__(int, SisypheVolume)
            __delitem__(int | str | SisypheVolume)
            __len__()
            __contains__(str | SisypheVolume)
            __iter__()
            __next__()
            __str__()
            __repr__()
            clear()
            bool = isEmpty()
            bool = isHomogeneous()
            int = count()
            remove(int | str | SisypheVolume)
            SisypheVolume = pop(int | str)
            int = index(str | SisypheVolume)
            reverse()
            append(SisypheVolume)
            insert(int | str | SisypheVolume, SisypheVolume)
            clear()
            sort()
            SisypheVolumeCollection = copy()
            list = copyToList()
            list = getList()
            SisypheVolume = copyToMultiComponentSisypheVolume()
            ndarray = copyToNumpyArray(defaultshape=bool)
            SisypheVolume = getMeanVolume()
            SisypheVolume = getStdVolume()
            SisypheVolume = getMedianVolume()
            SisypheVolume = getPercentileVolume(float)
            SisypheVolume = getMinVolume()
            SisypheVolume = getMaxVolume()
            SisypheVolume = getArgminVolume()
            SisypheVolume = getArgmaxVolume()
            float = getMean(mask=str)
            float = getStd(mask=str)
            float = getMin()
            float = getMax()
            float = getMedian(mask=str)
            float = getPercentile(mask=str)
            float = getKurtosis(mask=str)
            float = getSkewness(mask=str)
            dict = getStatistics(mask=str)
            list[float] = getValuesInsideMask(SisypheImage)
            list[float] = getValuesAt(x=int, y=int, z=int)
            load(str | list[str])               load PySisyphe volume(s) and append in the container
            loadFromSisyphe(str | list[str])    load Sisyphe volume(s) and append in the container
            loadFromNIFTI(str | list[str])      load Nifti volume(s) and append in the container
            loadFromNRRD(str | list[str])       load Nrrd volume(s) and append in the container
            loadFromMINC(str | list[str])       load Minc volume(s) and append in the container
            loadFromVTK(str | list[str])        load VTK volume(s) and append in the container
            save()
            saveToMulitcomponentVolume(str)

            inherited SisypheVolume getter methods, getXXX() -> list
            inherited SisypheVolume setter methods, setXXX(v) or setXXX(list | tuple)

        Creation: 04/02/2021
        Revisions:

            15/03/2023  change items type in _volumes list, tuple(Str ID, SisypheVolume) replaced by SisypheVolume
            16/03/2023  add pop method, removes SisypheVolume from list and returns it
            16/03/2023  add method __getattr__, gives access to setter and getter methods of SisypheVolume
            09/05/2023  add descriptive statistical methods
            15/06/2023  add method toLabelVolume() label volume conversion
            02/09/2023  type hinting
            08/11/2023  add saveToMulticomponentVolume() method
            10/11/2023  copyToNumpyArray(), reimplementation
                        add getVector() method
    """

    __slots__ = ['_volumes', '_index', '_homogeneous']

    # Private method

    def _verifyHomogeneous(self, v: SisypheVolume | None = None) -> None:
        if isinstance(v, SisypheVolume):
            if self.count() > 1:
                self._homogeneous = (self[0].getFieldOfView() == v.getFieldOfView() and
                                     self[0].getDatatype() == v.getDatatype())
            else: self._homogeneous = True
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    # Special methods

    def __init__(self) -> None:
        self._volumes = list()
        self._index = 0
        self._homogeneous = False

    def __str__(self) -> str:
        index = 0
        buff = 'SisypheVolume count #{}\n'.format(len(self._volumes))
        buff += 'Homogeneous: {}\n'.format(self._homogeneous)
        if self._homogeneous and not self.isEmpty():
            buff += 'Field of view: {}\n'.format(self[0].getFieldOfView())
            buff += 'Data type: {}\n'.format(self[0].getDatatype())
        for volume in self._volumes:
            index += 1
            buff += 'SisypheVolume #{}\n'.format(index)
            buff += '{}\n'.format(str(volume))
        return buff

    def __repr__(self) -> str:
        return 'SisypheVolumeCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container Public methods

    def __getitem__(self, key: str | int) -> SisypheVolume:
        # key is SisypheVolume arrayID str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._volumes):
                return self._volumes[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheVolume) -> None:
        if isinstance(value, SisypheVolume):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._volumes):
                    if value.getArrayID() not in self:
                        self._volumes[key] = value
                        self._verifyHomogeneous(value)
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(value)))

    def __delitem__(self, key: str | int | SisypheVolume) -> None:
        # key is SisypheVolume ID str
        if isinstance(key, (str, SisypheVolume)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._volumes):
                del self._volumes[key]
                if self.isEmpty(): self._homogeneous = False
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        return len(self._volumes)

    def __contains__(self, value: str | SisypheVolume) -> bool:
        keys = [k.getArrayID() for k in self._volumes]
        # value is SisypheVolume arrayID str
        if isinstance(value, str):
            return value in keys
        # value is SisypheVolume
        elif isinstance(value, SisypheVolume):
            return value.getArrayID() in keys
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> SisypheVolume:
        if self._index < len(self._volumes):
            n = self._index
            self._index += 1
            return self._volumes[n]
        else: raise StopIteration

    def __getattr__(self, name: str):
        """
            When attribute does not exist in the class,
            try calling the setter or getter method of sisypheVolume instances in collection.
            Getter methods return a list of the same size as the collection.
        """
        prefix = name[:3]
        if prefix in ('set', 'get'):
            def func(*args):
                flag = name in SisypheVolume.__dict__
                flag = flag or name in SisypheImage.__dict__
                # SisypheVolume get methods or set methods without argument
                if len(args) == 0:
                    if prefix in ('get', 'set'):
                        if name in SisypheIdentity.__dict__:
                            if prefix == 'get': return [vol.identity.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.identity.__getattribute__(name)()
                        elif name in SisypheAcquisition.__dict__:
                            if prefix == 'get': return [vol.acquisition.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.acquisition.__getattribute__(name)()
                        elif name in SisypheDisplay.__dict__:
                            if prefix == 'get': return [vol.display.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.display.__getattribute__(name)()
                        elif name in SisypheACPC.__dict__:
                            if prefix == 'get': return [vol.acpc.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.acpc.__getattribute__(name)()
                        elif flag:
                            if prefix == 'get': return [vol.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.__getattribute__(name)()
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                # SisypheVolume set methods with argument
                elif prefix == 'set':
                    p = args[0]
                    # SisypheVolume set method argument is list
                    if isinstance(p, (list, tuple)):
                        n = len(p)
                        if n == self.count():
                            if name in SisypheIdentity.__dict__:
                                for i in range(n): self[i].identity.__getattribute__(name)(p[i])
                            elif name in SisypheAcquisition.__dict__:
                                for i in range(n): self[i].acquisition.__getattribute__(name)(p[i])
                            elif name in SisypheDisplay.__dict__:
                                for i in range(n): self[i].display.__getattribute__(name)(p[i])
                            elif name in SisypheACPC.__dict__:
                                for i in range(n): self[i].acpc.__getattribute__(name)(p[i])
                            elif flag:
                                for i in range(n): self[i].__getattribute__(name)(p[i])
                            else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                        else: raise ValueError('Number of items in list ({}) '
                                               'does not match with {} ({}).'.format(p, self.__class__, self.count()))
                    # SisypheVolume set method argument is a single value (int, float, str, bool)
                    else:
                        if name in SisypheIdentity.__dict__:
                            for vol in self: vol.identity.__getattribute__(name)(p)
                        elif name in SisypheAcquisition.__dict__:
                            for vol in self: vol.acquisition.__getattribute__(name)(p)
                        elif name in SisypheDisplay.__dict__:
                            for vol in self: vol.display.__getattribute__(name)(p)
                        elif name in SisypheACPC.__dict__:
                            for vol in self: vol.acpc.__getattribute__(name)(p)
                        elif flag:
                            for vol in self: vol.__getattribute__(name)(p)
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
            return func
        raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Public methods

    def isEmpty(self) -> bool:
        return len(self._volumes) == 0

    def isHomogeneous(self) -> bool:
        return self._homogeneous

    def count(self) -> int:
        return len(self._volumes)

    def getVector(self, x, y, z, numpy=False) -> list | np_ndarray:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self._volumes:
                    l.append(v[x, y, z])
                if numpy: return np_array(l)
                else: return l
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def remove(self, value: str | int | SisypheVolume) -> None:
        # value is SisypheVolume
        if isinstance(value, SisypheVolume):
            self._volumes.remove(value)
        # value is SisypheVolume arrayID str or int
        elif isinstance(value, (str, int)):
            self.pop(self.index(value))
        else: raise TypeError('parameter type {} is not int, str or SisypheVolume.'.format(type(value)))
        if self.isEmpty(): self._homogeneous = False

    def pop(self, key: str | int | SisypheVolume | None = None) -> SisypheVolume:
        if key is None: return self._volumes.pop()
        # key is SisypheVolume arrayID str
        if isinstance(key, (str, SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._volumes.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def keys(self) -> list[str]:
        return [k.getArrayID() for k in self._volumes]

    def index(self, value: str | SisypheVolume) -> int:
        keys = [k.getArrayID() for k in self._volumes]
        # value is SisypheVolume
        if isinstance(value, SisypheVolume):
            value = value.getArrayID()
        # value is SisypheVolume arrayID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(value)))

    def reverse(self) -> None:
        self._volumes.reverse()

    def append(self, value: SisypheVolume) -> None:
        if isinstance(value, SisypheVolume):
            if value.getArrayID() not in self:
                self._volumes.append(value)
                self._verifyHomogeneous(value)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(value)))

    def insert(self, key: int | str | SisypheVolume, value: SisypheVolume) -> None:
        if isinstance(value, SisypheVolume):
            # value is SisypheVolume
            if isinstance(key, SisypheVolume):
                key = key.getArrayID()
            # value is SisypheVolume arrayID str
            if isinstance(key, str):
                key = self.index(key)
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._volumes):
                    if value.getArrayID() not in self._volumes:
                        self._volumes.insert(key, value)
                        self._verifyHomogeneous(value)
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int, str or SisypheVolume.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(value)))

    def clear(self) -> None:
        self._volumes.clear()
        self._homogeneous = False

    def sort(self, reverse: bool = False) -> None:
        def _getID(item):
            return item.getArrayID()

        self._volumes.sort(reverse=reverse, key=_getID)

    def copy(self) -> SisypheVolumeCollection:
        volumes = SisypheVolumeCollection()
        volumes._homogeneous = self._homogeneous
        for vol in self._volumes:
            volumes.append(vol)
        return volumes

    def copyToList(self) -> list[SisypheVolume]:
        volumes = self._volumes.copy()
        return volumes

    def getList(self) -> list[SisypheVolume]:
        return self._volumes

    def copyToMultiComponentSisypheVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                return multiComponentSisypheVolumeFromList(self)
            else: raise ValueError('Collection is not homogeneous for field of view or datatype.')

    def copyToNumpyArray(self, defaultshape: bool = True) -> np_ndarray:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                ar = stack(l)
                if defaultshape: return ar
                else: return ar.T
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def resample(self, trf: sc.sisypheTransform.SisypheTransform,
                 save: bool = True,
                 dialog: bool = False,
                 prefix: str | None = None,
                 suffix: str | None = None,
                 wait: DialogWait | None = None):
        if not self.isEmpty():
            if isinstance(trf, sc.sisypheTransform.SisypheTransform):
                if self.isHomogeneous():
                    f = sc.sisypheTransform.SisypheApplyTransform()
                    f.setTransform(trf)
                    c = SisypheVolumeCollection()
                    for vol in self:
                        f.setMoving(vol)
                        c.append(f.resampleMoving(fixed=None, save=save, dialog=dialog,
                                                  prefix=prefix, suffix=suffix, wait=wait))
                    return c
                else: raise ValueError('Volume collection is not homogeneous (same field of view and datatype).')
            else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(trf)))
        else: raise ValueError('Volume collection is empty.')

    # Algebraic public methods

    def getMeanVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanmean(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getStdVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanstd(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMedianVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanmedian(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getPercentileVolume(self, perc: int = 25) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanpercentile(stack(l), perc, axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMaxVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanmax(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMinVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanmin(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getArgminVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanargmin(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getArgmaxVolume(self) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                for v in self:
                    l.append(v.getNumpy())
                img = nanargmax(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def toLabelVolume(self, threshold: float = 0.5) -> SisypheVolume:
        if not self.isEmpty():
            if self.isHomogeneous():
                for v in self:
                    print(v.display.getRange())
                    if not v.display.hasZeroOneRange():
                        raise ValueError('Not all volumes have a range between 0.0 and 1.0.')
                r = self[0].getSITKImage() > threshold
                if self.count() > 1:
                    for i in range(1, self.count()):
                        v = (self[i].getSITKImage() > threshold) * i
                        r = r + v
                r = sitkCast(r, getLibraryDataType('uint8', 'sitk'))
                rvol = SisypheVolume(image=r)
                rvol.copyAttributesFrom(self[0], acquisition=False, display=False, slope=False)
                rvol.acquisition.setModalityToLB()
                rvol.setID(self[0].getID())
                for i in range(self.count()):
                    name = self[i].getName()
                    if name == '': name = 'ROI#{}'.format(i + 1)
                    rvol.acquisition.setLabel(i+1, name)
                return rvol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    # Descriptive statistics public methods

    def getMean(self, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getMean(mask) for v in self]

    def getStd(self, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getStd(mask) for v in self]

    def getMin(self) -> list[float]:
        if not self.isEmpty():
            return [v.getMin() for v in self]

    def getMax(self) -> list[float]:
        if not self.isEmpty():
            return [v.getMax() for v in self]

    def getMedian(self, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getMedian(mask) for v in self]

    def getPercentile(self, perc: int = 25, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getPercentile(perc, mask) for v in self]

    def getKurtosis(self, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getKurtosis(mask) for v in self]

    def getSkewness(self, mask: str = '') -> list[float]:
        if not self.isEmpty():
            return [v.getSkewness(mask) for v in self]

    def getStatistics(self, mask: str = '') -> dict[str, list[float]]:
        if not self.isEmpty():
            r = dict()
            r['mean'] = list()
            r['std'] = list()
            r['min'] = list()
            r['p25'] = list()
            r['median'] = list()
            r['p75'] = list()
            r['max'] = list()
            r['kurtosis'] = list()
            r['skewness'] = list()
            for v in self:
                rv = v.getStatistics(mask)
                r['mean'].append(rv['mean'])
                r['std'].append(rv['std'])
                r['min'].append(rv['min'])
                r['p25'].append(rv['p25'])
                r['median'].append(rv['median'])
                r['p75'].append(rv['p75'])
                r['max'].append(rv['max'])
                r['kurtosis'].append(rv['kurtosis'])
                r['skewness'].append(rv['skewness'])
            return r

    def getValuesInsideMask(self, mask: SisypheImage, asnumpy: bool = False) -> list[float] | np_ndarray:
        if not self.isEmpty():
            if isinstance(mask, SisypheImage):
                r = list()
                m = mask.getNumpy() > 0.0
                for v in self:
                    img = v.getNumpy()
                    img = img[m]
                    r.append(nanmean(img))
                if asnumpy: r = np_array(r)
                return r
            else: raise TypeError('parameter type {} is not SisypheImage.'.format(type(mask)))

    def getValuesAt(self, x: int, y: int, z: int, asnumpy: bool = False) -> list[float] | np_ndarray:
        if not self.isEmpty():
            r = [v[x, y, z] for v in self]
            if asnumpy: r = np_array(r)
            return r

    # IO Public methods

    def load(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.load(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromSisyphe(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.loadFromSisyphe(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromNIFTI(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.loadFromNIFTI(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromNRRD(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.loadFromNRRD(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromMINC(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.loadFromMINC(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromVTK(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        vol = SisypheVolume()
                        vol.loadFromVTK(filename)
                        self.append(vol)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def save(self) -> None:
        if not self.isEmpty():
            for vol in self:
                if vol.hasFilename(): vol.save()

    def saveToMulticomponentVolume(self, filename: str, copyattr: bool | dict[str: bool] = False) -> None:
        """
            copyattr    bool | dict[str: bool],
                        if type is bool, all dict values are set with copyattr value
                        dict[str: bool] = {'ID': True,
                                           'identity': True,
                                           'acquisition': True,
                                           'display': True,
                                           'acpc': True,
                                           'transform': True,
                                           'slope': True}
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                v = self.copyToMultiComponentSisypheVolume()
                if isinstance(copyattr, bool):
                    if copyattr is True: copyattr = {'ID': True,
                                                     'identity': True,
                                                     'acquisition': True,
                                                     'display': True,
                                                     'acpc': True,
                                                     'transform': True,
                                                     'slope': True}
                if isinstance(copyattr, dict):
                    if any(list(copyattr.values())):
                        if 'ID' in copyattr: id = copyattr['ID']
                        else: id = False
                        if 'identity' in copyattr: identity = copyattr['identity']
                        else: identity = False
                        if 'acquisition' in copyattr: acquisition = copyattr['acquisition']
                        else: acquisition = False
                        if 'display' in copyattr: display = copyattr['display']
                        else: display = False
                        if 'acpc' in copyattr: acpc = copyattr['acpc']
                        else: acpc = False
                        if 'transform' in copyattr: transform = copyattr['transform']
                        else: transform = False
                        if 'slope' in copyattr: slope = copyattr['slope']
                        else: slope = False
                        v.copyAttributesFrom(self[0], id, identity, acquisition, display, acpc, transform, slope)
                v.saveAs(filename)
            else: raise ValueError('Collection is not homogeneous for field of view or datatype.')
