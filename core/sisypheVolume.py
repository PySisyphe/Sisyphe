"""
External packages/modules
-------------------------

    - Cython, static compiler, https://cython.org/
    - ANTs, image registration, http://stnava.github.io/ANTs/
    - ITK, medical image processing, https://itk.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os import remove

from os.path import exists
from os.path import join
from os.path import split
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath

import cython

from xml.dom import minidom

from zlib import compress
from zlib import decompress

from hashlib import md5

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

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
from numpy import array
from numpy import ndarray
from numpy import fliplr

from PyQt5.QtGui import QImage

# < Revision 19/02/2025
from ants.core.ants_image import ANTsImage
# from Sisyphe.lib.ants.ants_image import ANTsImage
# Revision 19/02/2025 >

# noinspection PyUnresolvedReferences
from itk import Image as itkImage

from SimpleITK import Image as sitkImage
from SimpleITK import Cast as sitkCast
from SimpleITK import LabelVoting as sitkLabelVoting
from SimpleITK import ComposeImageFilter as sitkComposeImageFilter
from SimpleITK import VectorIndexSelectionCastImageFilter as sitkVectorIndexSelectionCastImageFilter

from vtk import vtkImageData

from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheConstants import getLibraryDataType
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
from Sisyphe.core.sisypheImageAttributes import SisypheACPC

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheXml import XmlVolume
    from Sisyphe.core.sisypheROI import SisypheROI
    from Sisyphe.core.sisypheMesh import SisypheMesh
    from Sisyphe.core.sisypheTransform import SisypheTransform
    from Sisyphe.core.sisypheTransform import SisypheTransforms
    from Sisyphe.core.sisypheTransform import SisypheApplyTransform
    from Sisyphe.core.sisypheDicom import XmlDicom
    from Sisyphe.gui.dialogWait import DialogWait


__all__ = ['SisypheVolume',
           'SisypheVolumeCollection',
           'multiComponentSisypheVolumeFromList']

"""
Function
~~~~~~~~

    - multiComponentSisypheVolumeFromList(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume

Class hierarchy
~~~~~~~~~~~~~~~

    - object -> Sisyphe.core.sisypheImage.SisypheImage -> SisypheVolume
             -> SisypheVolumeCollection
"""

def multiComponentSisypheVolumeFromList(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Create a multicomponent SisypheVolume from a list of single-component SisypheVolume or a SisypheVolumeCollection.

    Parameters
    ----------
    vols : list[SisypheVolume] | SisypheVolumeCollection
        list of single-component volumes

    Returns
    -------
    SisypheVolume
        multi-component volume
    """
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


listImages = sitkImage | ndarray | SisypheImage
listImages2 = sitkImage | ndarray | vtkImageData | ANTsImage
listFloat = list[float]
tupleFloat3 = tuple[float, float, float]
vectorFloat3 = listFloat | tupleFloat3


# noinspection PyShadowingBuiltins
class SisypheVolume(SisypheImage):
    """
    Description
    ~~~~~~~~~~~

    PySisyphe volume class.

    SisypheVolume is in RAS+ world coordinates convention (as MNI, Nibabel, NIFTI...) with origin to corner of the
    voxel

        - x, direction[1.0, 0.0, 0.0]: left(-) to right(+)
        - y, direction[0.0, 1.0, 0.0]: posterior(-) to anterior(+)
        - z: direction[0.0, 0.0, 1.0]: inferior(-) to superior(+)

    SimpleITK, ITK, DICOM is in LPS+ world coordinates convention

        - x: right(-) to left(+)          -> apply flipx for RAS+ conversion
        - y: anterior(-) to posterior(+)  -> apply flipy for RAS+ conversion
        - z: inferior(-) to superior(+)

    This class provides access to internal SimpleITK, ITK, VTK and numpy image classes, which share the same image
    buffer (behaviour inherited from the ancestor class SisypheImage).

    Supported properties:

        - Array ID: ID number calculated from scalar values (md5 algorithm)
        - ID: space ID, can be shared between several volumes (i.e. image of the same subject with same field of view)
        - identity: lastname, firstname, birthdate, gender
        - acquisition: modality, sequence, date of scan, stereotactic frame, signal unit, labels for label map modality,
        degrees of freedom and autocorrelations for statistical maps
        - display: look-up table colormap, range and window values, slope/intercept
        - acpc: AC coordinates, PC coordinates, geometric transformation to geometric reference with axes aligned on
        the AC-PC line with origin to the AC coordinates
        - transforms: list of geometric transformations to all co-registered volumes
        - dicom: access to Dicom fields of the related XmlDicom file (created during Dicom conversion)

    Overloaded operators which work with int, float, SisypheVolume, SisypheImage, SimpleITK Image, and numpy array
    instances.

        - Arithmetic  +, -, /, //, *
        - Logic       & (and), | (or), ^ (xor), ~ (not)
        - Relational  >, >=, <, <=, ==, !=

    Getter and Setter access to scalar values with slicing ability.

        - Getter: v = instance_name[x, y, z]
        - Setter: instance_name[x, y, z] = v
        - x, y, z are int or pythonic slicing (i.e. python slice object, syntax first:last:step)

    Deep copy methods to and from SimpleITK, ITK, VTK, ANTs, NiBabel and numpy image instances.
    IO methods for the most common neuroimaging file formats (BrainVoyager, FreeSurfer, Nifti, Nrrd, Minc, VTK).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheImage -> SisypheVolume

    Creation: 04/02/2021
    Last revisions: 07/06/2025
    """
    __slots__ = ['_ID', '_arrayID', '_filename', '_compression', '_identity', '_acquisition',
                 '_display', '_acpc', '_transforms', '_xdcm', '_slope', '_intercept', '_orientation']

    # Class constants

    _FILEEXT = '.xvol'
    _UNSPECIFIED, _AXIAL, _CORONAL, _SAGITTAL, = 0, 1, 2, 3

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheVolume file extension.

        Returns
        -------
        str
            '.xvol'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheVolume filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Volume (.xvol)'
        """
        return 'PySisyphe volume (*{})'.format(cls._FILEEXT)

    @classmethod
    def openVolume(cls, filename: str) -> SisypheVolume | None:
        """
        create a SisypheVolume instance from PySisyphe Volume file (.xvol).

        Parameters
        ----------
        filename : str
            volume file name

        Returns
        -------
        SisypheVolume
            loaded volume
        """
        if exists(filename):
            # < Revision 24/10/2024
            # bug fix
            # base, ext = splitext(filename)[1]
            base, ext = splitext(filename)
            # Revision 24/10/2024 >
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
        else: raise IOError('No such file {}.'.format(filename))

    # < Revision 03/10/2024
    # add class method getVolumeAttribute
    @classmethod
    def getVolumeAttribute(cls, filename: str, attr: str) -> str | int | float | tuple | list:
        """
        Get an attribute of a PySisyphe Volume file (.xvol).

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name
        attr : str
            attribute name: ID, size, spacing, FOV, number of componentes, datatype, origin, directions, orientation,
            modality, sequence, date of scan, stereotactic frame, scalar unit, range, window, slope, intercept,
            lastname, firstname, gender, date of birthday

        Returns
        -------
        str | int | float | tuple | list
            attribute value
        """
        from Sisyphe.core.sisypheXml import XmlVolume
        v = XmlVolume(filename)
        attr = attr.lower()
        if attr == 'id': return v.getID()
        # < Revision 29/11/2024
        # list -> tuple for size, spacing, fov, directions
        elif attr == 'size': return tuple(v.getSize())
        elif attr == 'spacing': return tuple(v.getSpacing())
        elif attr == 'fov': return tuple(v.getFOV())
        elif attr == 'components': return v.getComponents()
        elif attr == 'datatype': return v.getDatatype()
        elif attr == 'origin': return v.getOrigin()
        elif attr == 'directions': return tuple(v.getDirections())
        # Revision 29/11/2024 >
        elif attr == 'orientation': return v.getOrientation()
        elif attr == 'modality': return v.getModality()
        elif attr == 'sequence': return v.getSequence()
        elif attr == 'dateofscan': return v.getDateOfScanAsString()
        elif attr == 'frame': return v.getFrame()
        elif attr == 'unit': return v.getUnit()
        elif attr == 'range': return v.getRange()
        elif attr == 'window': return v.getWindow()
        elif attr == 'slope': return v.getSlope()
        elif attr == 'intercept': return v.getIntercept()
        elif attr == 'lastname': return v.getLastname()
        elif attr == 'firstname': return v.getFirstname()
        elif attr == 'gender': return v.getGender()
        elif attr == 'dateofbirthday': return v.getDateOfBirthdayAsString()
        else: raise ValueError('Invalid attribute {}.'.format(attr))
    # Revision 03/10/2024 >

    # < Revision 03/10/2024
    # add class method getVolumeAttributes
    @classmethod
    def getVolumeAttributes(cls, filename: str) -> dict:
        """
        Get attributes of a PySisyphe Volume file (.xvol).

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name

        Returns
        -------
        dict
            attribute keys: ID, size, spacing, FOV, number of componentes, datatype, origin, directions, orientation,
            modality, sequence, date of scan, stereotactic frame, scalar unit, range, window, slope, intercept,
            lastname, firstname, gender, date of birthday
        """
        from Sisyphe.core.sisypheXml import XmlVolume
        v = XmlVolume(filename)
        r = dict()
        r['id'] = v.getID()
        r['size'] = v.getSize()
        r['spacing'] = v.getSpacing()
        r['fov'] = v.getFOV()
        r['components'] = v.getComponents()
        r['datatype'] = v.getDatatype()
        r['origin'] = v.getOrigin()
        r['directions'] = v.getDirections()
        r['orientation'] = v.getOrientation()
        r['modality'] = v.getModality()
        r['sequence'] = v.getSequence()
        r['dateofscan'] = v.getDateOfScanAsString()
        r['frame'] = v.getFrame()
        r['unit'] = v.getUnit()
        r['range'] = v.getRange()
        r['window'] = v.getWindow()
        r['slope'] = v.getSlope()
        r['intercept'] = v.getIntercept()
        r['lastname'] = v.getLastname()
        r['firstname'] = v.getFirstname()
        r['gender'] = v.getGender()
        r['dateofbirthday'] = v.getDateOfBirthdayAsString()
        return r
    # Revision 03/10/2024 >

    # < Revision 09/11/2024
    # add class method getXmlVolume
    @classmethod
    def getXmlVolume(cls, filename: str) -> XmlVolume:
        """
        Get a XmlVolume instance of a PySisyphe Volume file (.xvol).

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name

        Returns
        -------
        Sisyphe.core.sisypheXml.XmlVolume
            XmlVolume
        """
        from Sisyphe.core.sisypheXml import XmlVolume
        return XmlVolume(filename)
    # Revision 09/11/2024 >

    # Special methods

    """
    Private attributes

    _filename       str
    _compression    bool
    _patients       SisypheIdentity
    _acquisition    SisypheAcquisition
    _display        SisypheDisplay
    _transforms     SisypheTransforms
    _acpc           SisypheACPC
    _slope          float
    _intercept      float
    _orient         int
    _ID             str, space ID (used by geometric transformations), editable, saved
    _arrayID        str, array ID, not editable, not saved, generated from array (md5, creation and loading)
    """

    def __init__(self, image: str | listImages2 | SisypheVolume | None = None, **kargs) -> None:
        """
        SisypheVolume instance constructor.

        Parameters
        ----------
        image : SisypheImage | SimpleITK.Image | vkt.vtkImageData | ants.core.ANTSImage | numpy.ndarray | str
            file name if str
        **kargs :
            - size, tuple[float, float, float] | list[float, float, float]
            - datatype, str
            - spacing, tuple[float, float, float] | list[float, float, float]
            - direction, tuple[float, ...] | list[float, ...] (9 elements)
        """
        from Sisyphe.core.sisypheTransform import SisypheTransforms
        self._ID: str | None = None
        self._arrayID: str | None = None
        self._filename: str = ''
        # noinspection PyUnresolvedReferences
        self._orientation: cython.int = self._UNSPECIFIED
        self._compression: bool = False
        # noinspection PyUnresolvedReferences
        self._slope: cython.double = 1.0
        # noinspection PyUnresolvedReferences
        self._intercept: cython.double = 0.0
        self._xdcm = None
        self._identity: SisypheIdentity = SisypheIdentity(parent=self)
        self._acquisition: SisypheAcquisition = SisypheAcquisition(parent=self)
        self._display: SisypheDisplay = SisypheDisplay(parent=self)
        self._acpc: SisypheACPC = SisypheACPC(parent=self)
        self._transforms: SisypheTransforms = SisypheTransforms()
        if isinstance(image, SisypheVolume):
            self._arrayID = image._arrayID
            self._filename = image._filename
            # < Revision 01/04/2025
            # self.copyAttributesFrom(image)
            # image = image.copyToSITKImage()
            # super().__init__(image, **kargs)
            # < Revision 07/06/2025
            # img = image.copyToSITKImage()
            super().__init__(image.getSITKImage(), **kargs)
            # Revision 07/06/2025 >
            self.copyAttributesFrom(image)
            # Revision 01/04/2025 >
        else: super().__init__(image, **kargs)

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheVolume instance to str
         """
        buff: str = 'Array ID: {}\n'.format(self.getArrayID())
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
        return buff[:-1]

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheVolume instance representation
        """
        return 'SisypheVolume instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Arithmetic operators

    def __add__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator +. self + other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of addition

        Returns
        -------
        SisypheVolume
            image = self + other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__add__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __sub__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator -. self - other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of subtraction

        Returns
        -------
        SisypheVolume
            image = self - other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__sub__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __mul__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator *. self * other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of multiplication

        Returns
        -------
        SisypheVolume
            image = self * other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__mul__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __div__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator /. self / other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float

        Returns
        -------
        SisypheVolume
            image = self / other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__div__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __floordiv__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator //. self // other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of floordiv operator

        Returns
        -------
        SisypheVolume
            image = self // other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__floordiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __truediv__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator /. self / other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of division

        Returns
        -------
        SisypheVolume
            image = self / other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__truediv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __radd__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator +. other + self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of addition

        Returns
        -------
        SisypheVolume
            image = other + self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__radd__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rsub__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator -. other - self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of subtraction

        Returns
        -------
        SisypheVolume
            image = other - self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rsub__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rmul__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator *. other * self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of multiplication

        Returns
        -------
        SisypheVolume
            image = other * self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rmul__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rdiv__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator /. other / self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of division

        Returns
        -------
        SisypheVolume
            image = other / self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rdiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rfloordiv__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator //. other // self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of floordiv operator

        Returns
        -------
        SisypheVolume
            image = other // self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rfloordiv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rtruediv__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded arithmetic operator /. other / self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            first operand of division

        Returns
        -------
        SisypheVolume
            image = other / self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rtruediv__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __neg__(self) -> SisypheVolume:
        """
        Special overloaded arithmetic unary operator -. - self -> SisypheVolume.

        Returns
        -------
        SisypheVolume
            image = - self
        """
        r = SisypheVolume(self._sitk_image.__neg__())
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __pos__(self) -> SisypheVolume:
        """
        Special overloaded arithmetic unary operator +. + self -> SisypheVolume.

        Returns
        -------
        SisypheVolume
            image = + self
        """
        return self

    # Logic operators

    def __and__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator & (and). self & other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            second operand of & operator

        Returns
        -------
        SisypheVolume
            image = self & other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__and__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rand__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator & (and). other & self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            first operand of & operator

        Returns
        -------
        SisypheVolume
            image = other & self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rand__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __or__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator | (or). self | other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            second operand of | operator

        Returns
        -------
        SisypheVolume
            image = self | other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__or__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __ror__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator | (or). other | self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            first operand of | operator

        Returns
        -------
        SisypheVolume
            image = other | self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__ror__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __xor__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator ^ (xor). self ^ other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            second operand of ^ operator

        Returns
        -------
        SisypheVolume
            image = self ^ other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__xor__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __rxor__(self, other: listImages) -> SisypheVolume:
        """
        Special overloaded logic operator ^ (xor). other ^ self -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume
            first operand of ^ operator

        Returns
        -------
        SisypheVolume
            image = other ^ self
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__rxor__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __invert__(self) -> SisypheVolume:
        """
        Special overloaded logic unary operator ~ (not). ~self -> SisypheVolume.

        Returns
        -------
        SisypheVolume
            image = ~self
        """
        r = SisypheVolume(self._sitk_image.__invert__())
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    # Relational operators

    def __lt__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded relational operator <. self < other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of < operator

        Returns
        -------
        SisypheVolume
            image = self < other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__lt__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __le__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded relational operator <=. self <= other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of <= operator

        Returns
        -------
        SisypheVolume
            image = self <= other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__le__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __eq__(self, other: listImages | int | float) -> bool | SisypheVolume:
        """
        Special overloaded relational operator ==. self == other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of == operator

        Returns
        -------
        bool | SisypheVolume
            result = self == other
        """
        if isinstance(other, SisypheVolume): return id(self) == id(other)
        elif isinstance(other, (int, float)):
            r = SisypheVolume(self._sitk_image.__eq__(other))
            r.copyAttributesFrom(self, display=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequenceToAlgebraMap()
            return r
        else:
            raise TypeError('parameter type {} is not SimpleTIK.Image, '
                            'ndarray, SisypheImage, SisypheVolume, int or float'.format(type(other)))

    def __ne__(self, other: listImages | int | float) -> bool | SisypheVolume:
        """
        Special overloaded relational operator !=. self != other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of != operator

        Returns
        -------
        bool | SisypheVolume
            result = self != other
        """
        if isinstance(other, SisypheVolume): return id(self) != id(other)
        elif isinstance(other, (int, float)):
            r = SisypheVolume(self._sitk_image.__ne__(other))
            r.copyAttributesFrom(self, display=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequenceToAlgebraMap()
            return r
        else:
            raise TypeError('parameter type {} is not SimpleTIK.Image, '
                            'ndarray, SisypheImage, SisypheVolume, int or float'.format(type(other)))

    def __gt__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded relational operator >. self > other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of > operator

        Returns
        -------
        SisypheVolume
            image = self > other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__gt__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    def __ge__(self, other: listImages | int | float) -> SisypheVolume:
        """
        Special overloaded relational operator >=. self >= other -> SisypheVolume.

        Parameters
        ----------
        other : SimpleTIK.Image | numpy.ndarray | Sisyphe.core.sisypheImage.SisypheImage | SisypheVolume | int | float
            second operand of >= operator

        Returns
        -------
        SisypheVolume
            image = self >= other
        """
        if isinstance(other, SisypheImage): other = other.getSITKImage()
        else: other = self._toSimpleITK(other)
        r = SisypheVolume(self._sitk_image.__ge__(other))
        r.copyAttributesFrom(self, display=False)
        r.acquisition.setModalityToOT()
        r.acquisition.setSequenceToAlgebraMap()
        return r

    # get pixel methods

    def __getitem__(self, idx):
        """
        Special overloaded container getter method. Get scalar value(s) with slicing ability.
        syntax: v = instance_name[x, y, z]

        Parameters
        ----------
        idx : list[float, float, float] | tuple[float, float, float] | slice
            x, y, z int indices, pythonic slicing (i.e. python slice object, used the syntax first:last:step)

        Returns
        -------
        int | float | tuple | SisypheVolume
            scalar value or SisypheVolume if slicing
        """
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
        if self.getSITKImage().GetDimension() == 3:
            i1 = abs(array(self.getFirstVectorDirection())).argmax()
            i2 = abs(array(self.getSecondVectorDirection())).argmax()
            i3 = abs(array(self.getThirdVectorDirection())).argmax()
            if i1 == 0 and i2 == 1 and i3 == 2: self._orientation = self._AXIAL
            elif i1 == 0 and i2 == 2 and i3 == 1: self._orientation = self._CORONAL
            elif i1 == 1 and i2 == 2 and i3 == 0: self._orientation = self._SAGITTAL

    def _updateRange(self) -> None:
        # bugfix, conversion numpy.float32 to float
        # noinspection PyArgumentList
        vmin = float(str(self.getNumpy().min()))
        # noinspection PyArgumentList
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
        # < Revision 0/10/2024
        if self.isThickAnisotropic(): self.acquisition.set2D()
        else: self.acquisition.set3D()
        # Revision 9/10/2024 >
        k = self._sitk_image.GetMetaDataKeys()
        if 'scl_inter' in k: self._intercept = self._sitk_image.GetMetaData('scl_inter')
        else: self._intercept = 0.0
        if 'scl_slope' in k: self._slope = self._sitk_image.GetMetaData('scl_slope')
        else: self._slope = 1.0

    # Public methods

    def copyFromSITKImage(self, img: sitkImage) -> None:
        """
        Copy a SimpleITK image buffer to the current SisypheVolume instance. Image buffer is not shared between
        SimpleITK image and SisypheVolume instances.

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        super().copyFromSITKImage(img)
        self._updateRange()

    def copyFromVTKImage(self, img: vtkImageData) -> None:
        """
        Copy a VTKImageData buffer to the current SisypheVolume instance. Image buffer is not shared between
        VTKImageData and SisypheVolume instances.

        Parameters
        ----------
        img : vtk.vtkImageData
            image to copy
        """
        super().copyFromVTKImage(img)
        self._updateRange()

    def copyFromITKImage(self, img: itkImage) -> None:
        """
        Copy an ITKImage buffer to the current SisypheVolume instance. Image buffer is not shared between ITKImage
        and SisypheVolume instances.

        Parameters
        ----------
        img : itk.Image
            image to copy
        """
        super().copyFromITKImage(img)
        self._updateRange()

    def copyFromANTSImage(self, img: ANTsImage) -> None:
        """
        Copy an ANTsImage buffer to the current SisypheVolume instance. Image buffer is not shared between ANTsImage
        and SisypheVolume instances.

        Parameters
        ----------
        img : ants.core.ANTsImage
            image to copy
        """
        super().copyFromANTSImage(img)
        self._updateRange()

    def copyFromNumpyArray(self,
                           img: ndarray,
                           spacing: vectorFloat3 = (1.0, 1.0, 1.0),
                           origin: vectorFloat3 = (0, 0, 0),
                           direction: tuple | list = tuple(getRegularDirections()),
                           defaultshape: bool = True) -> None:
        """
        Copy a Numpy array buffer to the current SisypheVolume instance. Image buffer is not shared between numpy array
        and SisypheVolume instances.

        Parameters
        ----------
         img : numpy.ndarray
            image to copy
         spacing : list[float, float, float] | tuple[float, float, float]
            voxel sizes in mm (default 1.0, 1.0, 1.0)
         origin : list[float, float, float] | tuple[float, float, float]
            origin coordinates (default 0.0, 0.0, 0.0)
         direction : list[float]
            axes directions
         defaultshape : bool
            if True (default), numpy shape order is reversed (i.e. z, y, x)
        """
        super().copyFromNumpyArray(img, spacing, origin, direction, defaultshape)
        self._updateRange()

    def setSITKImage(self, img: sitkImage) -> None:
        """
        Shallow copy of a SimpleITK Image to the SimpleITK Image attribute of the current SisypheVolume instance. Image
        buffer is shared between SimpleITK image and current SisypheVolume instances.

        Parameters
        ----------
        img : SimpleITK.Image
            image to copy
        """
        super().setSITKImage(img)
        self._updateRange()

    def getID(self) -> str:
        """
        Get the ID attribute of the current SisypheVolume instance.

        There are two types of identifier (i.e. ID):

            - Array ID: unique, calculated from scalar values (md5 algorithm). This cannot be edited.
            - ID: this is a space ID, it is not unique, all volumes sharing a common space have the same ID. This
            attribute is used as key in the Sisyphe.core.sisypheTransform.SisypheTransforms instances.

        Returns
        -------
        str
            ID
        """
        if self._ID is None: return 'None'
        else: return self._ID

    def setID(self, ID: str | SisypheVolume) -> None:
        """
        Set the ID attribute of the current SisypheVolume instance.

        There are two ID types:

        - ID is a space ID, it is not unique, all volumes sharing a common space have the same ID. This attribute is
        used as key in the Sisyphe.core.sisypheTransform.SisypheTransforms instances
        - Array ID, unique, calculated from scalar values (md5 algorithm). This cannot be edited.

        Parameters
        ----------
        ID : str | SisypheVolume
            ID or SisypheVolume ID attribute
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            self._ID = ID
            self._transforms.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    # < Revision 21/02/2025
    # add setICBM152ID method
    def setIDtoICBM152(self) -> None:
        """
        Set the ID attribute of the current SisypheVolume instance to ICBM152.
        """
        if self.hasSameSize((197, 233, 189)):
            self._ID = SisypheAcquisition.getICBM152TemplateTag()
            self.setDefaultDirections()
            self.setOrigin((98.0, 134.0, 72.0))
        else: raise ValueError('Incompatible size {} with ICBM152 space.'.format(self.getSize()))

    # < Revision 21/02/2025
    # add setICBM452ID method
    def setIDtoICBM452(self) -> None:
        """
        Set the ID attribute of the current SisypheVolume instance to ICBM452.
        """
        if self.hasSameSize((149, 188, 148)):
            self._ID = SisypheAcquisition.getICBM452TemplateTag()
            self.setDefaultDirections()
            self.setDefaultOrigin()
        else: raise ValueError('Incompatible size {} with ICBM452 space.'.format(self.getSize()))
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add setATROPOSID method
    def setIDtoATROPOS(self) -> None:
        """
        Set the ID attribute of the current SisypheVolume instance to ATROPOS.
        """
        if self.hasSameSize((216, 291, 256)):
            self._ID = SisypheAcquisition.getATROPOSTemplateTag()
            self.setDefaultDirections()
            self.setDefaultOrigin()
        else: raise ValueError('Incompatible size {} with ATROPOS space.'.format(self.getSize()))
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add setSRI24ID method
    def setIDtoSRI24(self) -> None:
        """
        Set the ID attribute of the current SisypheVolume instance to SRI24.
        """
        if self.hasSameSize((240, 240, 155)):
            self._ID = SisypheAcquisition.getSRI24TemplateTag()
            self.setDefaultDirections()
            self.setOrigin((120.0, 127.0, 68.0))
        else: raise ValueError('Incompatible size {} with SRI24 space.'.format(self.getSize()))
    # Revision 21/02/2025 >

    def hasSameID(self, ID: str | SisypheVolume | SisypheROI | SisypheMesh) -> bool:
        """
        Check if an ID is identical to the ID of the current SisypheVolume instance.

        Parameters
        ----------
        ID : str | SisypheVolume | Sisyphe.core.sisypheROI.SisypheROI | Sisyphe.core.sisypheMesh.SisypheMesh
            ID, SisypheVolume ID attribute, SisypheROI ID attribute or SisypheMesh ID attribute

        Returns
        -------
        bool
        """
        from Sisyphe.core.sisypheROI import SisypheROI
        from Sisyphe.core.sisypheMesh import SisypheMesh
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        elif isinstance(ID, SisypheROI): ID = ID.getReferenceID()
        elif isinstance(ID, SisypheMesh): ID = ID.getReferenceID()
        if isinstance(ID, str): return self._ID == ID
        else: raise TypeError('parameter type {} is not str, SisypheVolume, SisypheROI or SisypheMesh.'.format(type(ID)))

    def getArrayID(self) -> str:
        """
        Get the Array ID attribute of the current SisypheVolume instance.

        There are two types of identifier (i.e. ID):

            - Array ID: unique, calculated from scalar values (md5 algorithm). This cannot be edited.
            - ID: this is a space ID, it is not unique, all volumes sharing a common space have the same ID. This
            attribute is used as key in the Sisyphe.core.sisypheTransform.SisypheTransforms instances.

        Returns
        -------
        str
            Array ID
        """
        return self._arrayID

    def updateArrayID(self) -> None:
        """
        Re-calculate the array ID attribute from the scalar values of the current SisypheVolume instance.
        """
        self._calcArrayID()

    def setIdentity(self, identity: SisypheIdentity) -> None:
        """
        Set the identity instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheIdentity attributes are: lastname, firstname, gender, birthdate

        Parameters
        ----------
        identity : Sisyphe.core.sisypheImageAttributes.SisypheIdentity
            identity attribute
        """
        if isinstance(identity, SisypheIdentity):
            self._identity = identity
            self._identity.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))

    def getIdentity(self) -> SisypheIdentity:
        """
        Get the identity instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheIdentity attributes are: lastname, firstname, gender, birthdate

        Returns
        -------
        Sisyphe.core.sisypheImageAttributes.SisypheIdentity
            identity attribute
        """
        return self._identity

    def setAcquisition(self, acquisition: SisypheAcquisition) -> None:
        """
        Set the acquisition instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheAcquisition attributes are: modality, sequence, date of scan, frame,
        units of scalar values, labels for LB modality, degrees of freedom and autocorrelation for statistical map
        sequences.

        Parameters
        ----------
        acquisition : Sisyphe.core.sisypheImageAttributes.SisypheAcquisition
            acquisition attribute
        """
        if isinstance(acquisition, SisypheAcquisition):
            self._acquisition = acquisition
            self._acquisition.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheAcquisition.'.format(type(acquisition)))

    def getAcquisition(self) -> SisypheAcquisition:
        """
        Get the acquisition instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheAcquisition attributes are: modality, sequence, date of scan, frame,
        units of scalar values, labels for LB modality, degrees of freedom and autocorrelation for statistical map
        sequences.

        Returns
        -------
        Sisyphe.core.sisypheImageAttributes.SisypheAcquisition
            acquisition attribute
        """
        return self._acquisition

    def setDisplay(self, display: SisypheDisplay) -> None:
        """
        Set the display instance of the current SisypheVolume instance.

        Parameters
        ----------
        display : Sisyphe.core.sisypheImageAttributes.SisypheDisplay
            display attribute
        """
        if isinstance(display, SisypheDisplay):
            self._display = display
            self._display.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheDisplay.'.format(type(display)))

    def removeDisplay(self) -> None:
        """
        Clear the display attribute of the current SisypheVolume instance. Default display values: gray level colormap,
        no windowing.
        """
        self._display = None

    def getDisplay(self) -> SisypheDisplay:
        """
        Get the display instance of the current SisypheVolume instance.

        Returns
        -------
        Sisyphe.core.sisypheImageAttributes.SisypheDisplay
            display attribute
        """
        return self._display

    def setACPC(self, acpc: SisypheACPC) -> None:
        """
        Set the acp instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheACPC attributes are: (AC) and posterior (PC) commissure coordinates,
        rigid geometric transformation i.e. geometric transformation to reference with axes aligned on the AC-PC line,
        with midACPC point as center of rotation.

        Parameters
        ----------
        acpc : Sisyphe.core.sisypheImageAttributes.SisypheACPC
            acpc attribute
        """
        if isinstance(acpc, SisypheACPC):
            self._acpc = acpc
            self._acpc.setParent(self)
        else: raise TypeError('parameter type {} is not SisypheACPC.'.format(type(acpc)))

    def getACPC(self) -> SisypheACPC:
        """
        Set the acp instance of the current SisypheVolume instance.
        Sisyphe.core.sisypheImageAttributes.SisypheACPC attributes are: (AC) and posterior (PC) commissure coordinates,
        rigid geometric transformation i.e. geometric transformation to reference with axes aligned on the AC-PC line,
        with midACPC point as center of rotation.

        Returns
        -------
        Sisyphe.core.sisypheImageAttributes.SisypheACPC
            acpc attribute
        """
        return self._acpc

    def copy(self) -> SisypheVolume:
        """
        SisypheVolume copy of the current SisypheVolume instance (deep copy).

        Returns
        -------
        SisypheVolume
            image copy
        """
        if not self.isEmpty():
            img = SisypheVolume(self)
            return img
        else: raise TypeError('SisypheImage is empty.')

    def copyComponent(self, c: int = 0) -> SisypheVolume:
        """
        Copy a component of the current SisypheVolume instance.

        Parameters
        ----------
        c : int
            component index (default 0)

        Returns
        -------
        SisypheVolume
            single-component volume
        """
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
        """
        SisypheVolume copy of the current SisypheVolume instance with a new datatype.

        Parameters
        ----------
        datatype : str
            numpy datatype

        Returns
        -------
        SisypheVolume
            cast volume
        """
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
        """
        Copy the properties of the current SisypheVolume instance to a SisypheVolume instance.

        Parameters
        ----------
        img : SisypheVolume
            copy to this instance
        identity : bool
            copy identity property if True (default)
        acquisition : bool
            copy acquisition property if True (default)
        display : bool
            copy display property if True (default)
        acpc : bool
            copy acpc property if True (default)
        slope : bool
            copy slope/intercept attributes if True (default)
        """
        if isinstance(img, SisypheVolume):
            # < Revision 21/02/2025
            img.setOrigin(self.getOrigin())
            img.setDirections(self.getDirections())
            # Revision 21/02/2025 >
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
        """
        Copy the properties of a SisypheVolume instance to the current SisypheVolume instance.

        Parameters
        ----------
        img : SisypheVolume
            copy from this instance
        identity : bool
            copy identity property if True (default)
        acquisition : bool
            copy acquisition property if True (default)
        display : bool
            copy display property if True (default)
        acpc : bool
            copy acpc property if True (default)
        slope : bool
            copy slope/intercept attributes if True (default)
        """
        if isinstance(img, SisypheVolume):
            # < Revision 21/02/2025
            self.setOrigin(img.getOrigin())
            self.setDirections(img.getDirections())
            # Revision 21/02/2025 >
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
        """
        Copy the properties and attributes of the current SisypheVolume instance to a SisypheVolume instance.

        Parameters
        ----------
        img : SisypheVolume
            copy to this instance
        id : bool
            copy ID attribute if True (default)
        identity : bool
            copy identity property if True (default)
        acquisition : bool
            copy acquisition property if True (default)
        display : bool
            copy display property if True (default)
        acpc : bool
            copy acpc property if True (default)
        transform : bool
            copy  transform property if True (default)
        slope : bool
            copy slope/intercept attributes if True (default)
        """
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
        """
        Copy the properties and attributes of a SisypheVolume instance to the current SisypheVolume instance.

        Parameters
        ----------
        img : SisypheVolume
            copy from this instance
        id : bool
            copy ID attribute if True (default)
        identity : bool
            copy identity property if True (default)
        acquisition : bool
            copy acquisition property if True (default)
        display : bool
            copy display property if True (default)
        acpc : bool
            copy acpc property if True (default)
        transform : bool
            copy  transform property if True (default)
        slope : bool
            copy slope/intercept attributes if True (default)
        """
        if isinstance(img, SisypheVolume):
            self.copyPropertiesFrom(img,  identity, acquisition, display, acpc, slope)
            if id: self.setID(img.getID())
            if transform:
                self._transforms = img._transforms.copy()
                self._transforms.setReferenceID(self.getID())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def setSlope(self, slope: float = 1.0) -> None:
        """
        Set the slope attribute of the current SisypheVolume instance. The slope and intercept attributes are used to
        apply a linear transformation of the scalar values: value = slope * scalar value + intercept.

        Parameters
        ----------
        slope : float
            slope value
        """
        self._slope = slope

    def setIntercept(self, intercept: float = 0.0) -> None:
        """
        Set the intercept attribute of the current SisypheVolume instance. The slope and intercept attributes are used
        to apply a linear transformation of the scalar values: value = slope * scalar value + intercept.

        Parameters
        ----------
        intercept : float
            intercept value
        """
        self._intercept = intercept

    def getSlope(self) -> float:
        """
        Get the slope attribute of the current SisypheVolume instance. The slope and intercept attributes are used to
        apply a linear transformation of the scalar values: value = slope * scalar value + intercept.

        Returns
        -------
        float
            slope value
        """
        if self._slope is None or not isinstance(self._slope, float): self._slope = 1.0
        return self._slope

    def getIntercept(self) -> float:
        """
        Set the intercept attribute of the current SisypheVolume instance. The slope and intercept attributes are used
        to apply a linear transformation of the scalar values: value = slope * scalar value + intercept.

        Returns
        -------
        float
            intercept value
        """
        if self._intercept is None or not isinstance(self._intercept, float): self._intercept = 0.0
        return self._intercept

    def setDirections(self, direction: tuple = tuple(getRegularDirections())) -> None:
        """
        Set vectors of image axes in RAS+ coordinates system. PySisyphe uses RAS+ world coordinates system convention
        (as MNI, Nibabel, Dipy...) with origin to corner of the voxel.

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats

            - First vector, x image axis direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y image axis direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, y image axis direction, [0.0, 0.0, 1.0] (RAS+ default)

        Parameters
        ----------
        direction : list[float]
            vectors of image axes
        """
        super().setDirections(direction)
        self._updateOrientation()

    def setDefaultDirections(self) -> None:
        """
        Set vectors of image axes to default in RAS+ coordinates system. PySisyphe uses RAS+ world coordinates system
        convention (as MNI, Nibabel, Dipy...) with origin to corner of the voxel

            - x, direction [1.0, 0.0, 0.0]: left(-) to right(+)
            - y, direction [0.0, 1.0, 0.0]: posterior(-) to anterior(+)
            - z, direction [0.0, 0.0, 1.0]: inferior(-) to superior(+)

        Directions is a list of 9 float, 3 vectors of 3 floats

            - First vector, x image axis direction, [1.0, 0.0, 0.0] (RAS+ default)
            - Second vector, y image axis direction, [0.0, 1.0, 0.0] (RAS+ default)
            - Third vector, y image axis direction, [0.0, 0.0, 1.0] (RAS+ default)
        """
        self.setDirections()

    def setOrientation(self, orient: str = 'axial') -> None:
        """
        Set the orientation attribute of the current SisypheVolume instance.

        Parameters
        ----------
        orient : str
            'axial', 'coronal', 'sagittal' or 'unspecified'
        """
        if orient == 'axial': self._orientation = self._AXIAL
        elif orient == 'coronal': self._orientation = self._CORONAL
        elif orient == 'sagittal': self._orientation = self._SAGITTAL
        else: self._orientation = self._UNSPECIFIED

    def setOrientationToAxial(self) -> None:
        """
        Set the orientation attribute of the current SisypheVolume instance to axial.
        """
        self._orientation = self._AXIAL

    def setOrientationToCoronal(self) -> None:
        """
        Set the orientation attribute of the current SisypheVolume instance to coronal.
        """
        self._orientation = self._CORONAL

    def setOrientationToSagittal(self) -> None:
        """
        Set the orientation attribute of the current SisypheVolume instance to sagittal.
        """
        self._orientation = self._SAGITTAL

    def getOrientationAsString(self) -> str:
        """
        Get the orientation attribute of the current SisypheVolume instance as str.

        Returns
        -------
        str
            'axial', 'coronal', 'sagittal' or 'unspecified'
        """
        if self._orientation == self._AXIAL: return 'axial'
        elif self._orientation == self._CORONAL: return 'coronal'
        elif self._orientation == self._SAGITTAL: return 'sagittal'
        else: return 'unspecified'

    def getOrientation(self) -> int:
        """
        Get the orientation attribute of the current SisypheVolume instance as int code.

        Returns
        -------
        int
            1 'axial', 2 'coronal', 3 'sagittal' or 0 'unspecified'
        """
        return self._orientation

    def isAxial(self) -> bool:
        """
        Check whether the orientation attribute of the current SisypheVolume instance is axial.

        Returns
        -------
        bool
            True if axial orientation
        """
        return self._orientation == self._AXIAL

    def isCoronal(self) -> bool:
        """
        Check whether the orientation attribute of the current SisypheVolume instance is coronal.

        Returns
        -------
        bool
            True if coronal orientation
        """
        return self._orientation == self._CORONAL

    def isSagittal(self) -> bool:
        """
        Check whether the orientation attribute of the current SisypheVolume instance is sagittal.

        Returns
        -------
        bool
            True if sagittal orientation
        """
        return self._orientation == self._SAGITTAL

    def hasFilename(self) -> bool:
        """
        Check whether the filename attribute of the current SisypheVolume instance is defined (i.e. not '')

        Returns
        -------
        bool
            True if filename attribute is defined
        """
        return self._filename != ''

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current SisypheVolume instance. The file name attribute is used to save the
        current SisypheVolume instance.

        Returns
        -------
        str
            file name
        """
        return self._filename

    def getDirname(self) -> str:
        """
        Get the path name attribute of the current SisypheVolume instance. The file name attribute is used to save the
        current SisypheVolume instance.

        Returns
        -------
        str
            path name (path part of the file name)
        """
        return dirname(self._filename)

    def getBasename(self) -> str:
        """
        Get the base name attribute of the current SisypheVolume instance. The file name attribute is used to save the
        current SisypheVolume instance.

        Returns
        -------
        str
            base name (base part of the file name)
        """
        return basename(self._filename)

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheVolume instance. This is the base part of the file name, without
        extension.

        Returns
        -------
        str
            name (base part of the file name, without extension)
        """
        return splitext(basename(self._filename))[0]

    def copyFilenameTo(self, vol: SisypheVolume) -> None:
        """
        Copy the file name attribute of the current SisypheVolume instance to a SisypheVolume instance.

        Parameters
        ----------
        vol : SisypheVolume
            copy to this volume
        """
        if isinstance(vol, SisypheVolume):
            vol._filename = self._filename
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def copyFilenameFrom(self, vol: SisypheVolume) -> None:
        """
        Copy the file name attribute of a SisypheVolume instance to the current SisypheVolume instance

        Parameters
        ----------
        vol : SisypheVolume
            copy from this volume
        """
        if isinstance(vol, SisypheVolume):
            self._filename = vol.getFilename()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setFilename(self, filename: str) -> None:
        """
        Set the file name attribute of the current SisypheVolume instance. The file name attribute is used to save the
        current SisypheVolume instance.

        Parameters
        ----------
        filename : str
            file name
        """
        if filename == '':
            filename = '{}_{}_{}_{}_{}_{}{}'.format(self._identity.getLastname(),
                                                    self._identity.getFirstname(),
                                                    self._identity.getDateOfBirthday(),
                                                    self.acquisition.getModality(),
                                                    self.acquisition.getDateOfScan(),
                                                    self.acquisition.getSequence(),
                                                    self._FILEEXT)
        else:
            filename = abspath(filename)
            path, ext = splitext(filename)
            # <Revision 18/07/2024
            # take into account '.nii.gz' double extension
            if ext.lower() == '.gz':
                path, ext = splitext(path)
            # Revision 18/07/2024>
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
        self._filename = filename
        self._transforms.setFilenameFromVolume(self)

    def setDirname(self, path: str) -> None:
        """
        Set the path name attribute of the current SisypheVolume instance. The file name attribute is used to save the
        current SisypheVolume instance.

        Parameters
        ----------
        path : str
            path name (path part of the file name)
        """
        if exists(path):
            path = abspath(path)
            if self._filename != '': self._filename = join(path, basename(self._filename))
            else: raise ValueError('Filename attribute is empty.')

    def setFilenamePrefix(self, prefix: str, sep: str = '_') -> None:
        """
        Set a prefix to the file name attribute of the current SisypheVolume instance. The file name attribute is used
        to save the current SisypheVolume instance.

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

    def getFilenamePrefix(self, sep: str = '_') -> str:
        """
        Get prefix (if any) from the file name attribute of the current SisypheVolume instance. The file name attribute
        is used to save the current SisypheVolume instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            prefix
        """
        r = self.getName().split(sep)
        if len(r) > 0: return r[0]
        else: return ''

    def setFilenameSuffix(self, suffix: str, sep: str = '_') -> None:
        """
        Set a suffix to the file name attribute of the current SisypheVolume instance. The file name attribute is used
        to save the current SisypheVolume instance.

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

    def getFilenameSuffix(self, sep: str = '_') -> str:
        """
        Get suffix (if any) from the file name attribute of the current SisypheVolume instance. The file name attribute
        is used to save the current SisypheVolume instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            suffix
        """
        r = self.getName().split(sep)
        if len(r) > 0: return r[-1]
        else: return ''

    def removeSuffixNumber(self) -> None:
        """
        Remove a suffix number (if any) from the file name attribute of the current SisypheVolume instance.
        """
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

    # < 05/11/2024
    # add removeAllPrefixes method
    def removeAllPrefixes(self, sep: str = '_') -> None:
        """
        Remove all prefixes from the file name attribute of the current SisypheVolume instance.

        Parameters
        ----------
        sep : str
            char between prefix(es) (default '_')
        """
        splt = self._filename.split(sep)
        if len(splt) > 1:
            # < Revision 07/11/2024
            # self._filename = splt[-1]
            path = dirname(self._filename)
            self._filename = join(path, splt[-1])
            # Revision 07/11/2024 >
    # 05/11/2024 >

    # < 05/11/2024
    # add removeAllSuffixes method
    def removeAllSuffixes(self, sep: str = '_') -> None:
        """
        Remove all prefixes from the file name attribute of the current SisypheVolume instance.

        Parameters
        ----------
        sep : str
            char between prefix(es) (default '_')
        """
        splt = self._filename.split(sep)
        if len(splt) > 1: self._filename = splt[0] + self.getFileExt()
    # 05/11/2024 >

    def setCompression(self, v: bool) -> None:
        """
        Set the compression attribute of the current SisypheVolume instance. ySisyphe volume format (.xvol) can be
        optionally gzipped.

        Parameters
        ----------
        v : bool
            compression is enabled if True
        """
        if isinstance(v, bool): self._compression = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCompressionOn(self) -> None:
        """
        Enables gzip file compression of the current SisypheVolume instance. PySisyphe volume format (.xroi) can be
        optionally gzipped.
        """
        self._compression = True

    def setCompressionOff(self) -> None:
        """
        Disables gzip file compression of the current SisypheVolume instance. PySisyphe volume format (.xroi) can be
        optionally gzipped.
        """
        self._compression = False

    def getCompression(self) -> bool:
        """
        Get the compression attribute of the current SisypheVolume instance. PySisyphe volume format (.xvol) can be
        optionally gzipped.

        Returns
        -------
        bool
            True, if compression is enabled
        """
        return self._compression

    # < Revision 23/10/2024
    # add getROI method
    def getROI(self,
               threshold: float = 0.5,
               op: str = '>',
               c: int | None = 0) -> SisypheROI:
        """
        Converting current SisypheVolume instance to Sisyphe.core.sisypheROI.SisypheROI.

        Parameters
        ----------
        threshold  : float
            threshold for binarization (default 0.5)
        op : str
            comparison operator: '>' (default), '>=', '<', '<=', '==', '!='
        c : int | None
            parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
        """
        # < Revision 20/12/2024
        # add comparison operator
        # roi = super().getROI(threshold, c)
        roi = super().getROI(threshold, op, c)
        # Revision 20/12/2024 >
        roi.setReferenceID(self)
        roi.setName(self.getName())
        return roi
    # Revision 23/10/2024>

    # < Revision 24/10/2024
    # add labelToROI method
    def labelToROI(self, label: int = 0) -> SisypheROI:
        """
        Converting a label of the current SisypheVolume instance to Sisyphe.core.sisypheROI.SisypheROI. The modality of
        the current SisypheVolume instance must be LB (Label).

        Parameters
        ----------
        label  : int
            label index (default 0)

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            roi converted from label volume
        """
        if self.acquisition.isLB():
            if label <= self.getMax():
                from Sisyphe.core.sisypheROI import SisypheROI
                roi = SisypheROI()
                # noinspection PyTypeChecker
                roi.setSITKImage(self.getSITKImage() == label)
                roi.setReferenceID(self)
                roi.setName(self.acquisition.getLabel(label))
                roi.setFilename(self.getFilename())
                roi.setFilenamePrefix(self.acquisition.getLabel(label))
                return roi
            else: raise ValueError('Label {} is out of range.'.format(label))
        else: raise ValueError('Modality is not LB.')
    # Revision 24/10/2024>

    # < Revision 04/06/2025
    def getRelabeled(self, cross: dict[int, int]) -> SisypheVolume:
        """
        Get a relabeled SisypheVolume of the current SisypheVolume instance.

        Parameters
        ----------
        cross : dict[int, int]
            - label value mapping table between current image and relabeled image
            - key: label value in the current image
            - value: new label value in the relabeled image

        Returns
        -------
        SisypheVolume
            relabeled image
        """
        vol = SisypheVolume(super().getRelabeled(cross))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('relabel')
        return vol
    # Revision 04/06/2025

    def getMask(self,
                algo: str = 'huang',
                morpho: str = '',
                niter: int = 1,
                kernel: int = 0,
                fill: str = '',
                c: int | None = 0) -> SisypheVolume:
        """
        Calc SisypheVolume mask of the head.

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
            structuring element size (default 0, no morphology)
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
        SisypheVolume
            mask
        """
        vol = SisypheVolume(super().getMask(algo, morpho, niter, kernel, fill, c))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('mask')
        vol.acquisition.setModalityToOT()
        vol.acquisition.setSequenceToMask()
        return vol

    def getMaskROI(self,
                   name: str = 'Mask',
                   algo: str = 'huang',
                   morpho: str = '',
                   niter: int = 1,
                   kernel: int = 0,
                   fill: str = '',
                   c: int | None = 0) -> SisypheROI:
        """
        Calc Sisyphe.core.sisypheROI.SisypheROI mask of the head.

        Parameters
        ----------
        name  : str
            roi name
        algo : str
            Automatic thresholding algorithm used for background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen',
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
            - '', no filling (default)
        c : int | None
            - parameter only used for multi-component image
            - int index of the component to process (default 0, first component)
            - None, processing is performed on the mean image

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            mask roi
        """
        roi = super().getMaskROI(algo, morpho, niter, kernel, fill, c)
        roi.setReferenceID(self.getID())
        roi.setName(name)
        return roi

    def getMask2(self,
                 algo: str = 'huang',
                 morphoiter: int = 1,
                 kernel: int = 0,
                 c: int | None = 0) -> SisypheVolume:
        """
        Calc SisypheVolume mask of the head.

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
        SisypheVolume
            mask
        """
        vol = SisypheVolume(super().getMask2(algo, morphoiter, kernel, c))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('mask')
        vol.acquisition.setModalityToOT()
        vol.acquisition.setSequenceToMask()
        return vol

    def getMaskROI2(self,
                    name: str = 'Mask',
                    algo: str = 'huang',
                    morphoiter: int = 1,
                    kernel: int = 0,
                    c: int | None = 0) -> SisypheROI:
        """
        Calc Sisyphe.core.sisypheROI.SisypheROI mask of the head.

        Parameters
        ----------
        name : str
            roi name
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
        Sisyphe.core.sisypheROI.SisypheROI
            mask roi
        """
        roi = super().getMaskROI2(algo, morphoiter, kernel, c)
        roi.setReferenceID(self.getID())
        roi.setName(name)
        return roi

    # < Revision 19/11/2024
    # add getNonZeroMask method
    def getNonZeroMask(self, c: int | None = 0) -> SisypheVolume:
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
        SisypheVolume
            non-zero mask
        """
        vol = SisypheVolume(super().getNonZeroMask(c))
        vol.copyAttributesFrom(self, display=False, acquisition=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('mask')
        vol.acquisition.setModalityToOT()
        vol.acquisition.setSequenceToMask()
        return vol
    # Revision 19/11/2024 >

    # < Revision 08/10/2024
    # add removeNeckSlices method
    def removeNeckSlices(self, f: float = 1.8) -> SisypheVolume:
        """
        Get a new SisypheVolume instance, cropped in z. Most sagittal MRI scans have extensive and useless inferior
        coverage. This function crop MR volume in z direction, removing empty slices and lower slices of neck below
        foramen magnum.

        Parameters
        ----------
        f : float
            multiplicative factor to adjust the neck slice. Lower values remove more slices, higher values keep more
            slices (between 1.5 and 2.0, default 1.8 close to the foramen magnum for most MR images)

        Returns
        -------
        SisypheVolume
            cropped volume
        """
        vol = SisypheVolume(super().removeNeckSlices(f))
        vol.copyAttributesFrom(self, acpc=False, transform=False)
        vol.setFilename(self._filename)
        vol.setFilenamePrefix('crop')
        return vol
    # Revision 08/10/2024 >

    def getComponentMean(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Get mean of each vector in a multicomponent image. Process all components or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            component indices
                - list[int]: list of component indices
                - tuple[int, ...]: tuple of component indices
                - slice: slice of component indices (start:end:step)
                - None: no selection, all components are processed

        Returns
        -------
        SisypheVolume
            component mean volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentMean())
            vol = SisypheVolume(super().getComponentMean(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('mean')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentStd(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component std volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentStd())
            vol = SisypheVolume(super().getComponentStd(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('std')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentMin(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component min volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentMin())
            vol = SisypheVolume(super().getComponentMin(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('min')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentMax(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component max volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentMax())
            vol = SisypheVolume(super().getComponentMax(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('max')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    # < Revision 17/12/2024
    # add getComponentRange method
    def getComponentRange(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component range volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentRange())
            vol = SisypheVolume(super().getComponentRange(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('range')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')
    # Revision 17/12/2024 >

    def getComponentMedian(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component median volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentMedian())
            vol = SisypheVolume(super().getComponentMedian(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('median')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentPercentile(self, perc: int = 25, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component percentile volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentPercentile(perc))
            vol = SisypheVolume(super().getComponentPercentile(perc, c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('perc{}'.format(perc))
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentKurtosis(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component kurtosis volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentKurtosis())
            vol = SisypheVolume(super().getComponentKurtosis(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('kurtosis')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentSkewness(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            component skewness volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentSkewness())
            vol = SisypheVolume(super().getComponentSkewness(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('skew')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentArgmax(self) -> SisypheVolume:
        """
        Get the index of the highest scalar value of each vector in a multicomponent image.

        Returns
        -------
        SisypheVolume
            single-component volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            vol = SisypheVolume(super().getComponentArgmax())
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('argmax')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentArgmin(self, nonzero: bool = False) -> SisypheVolume:
        """
        Get the index of the lowest scalar value of each vector in a multicomponent image.

        Parameters
        ----------
        nonzero : bool
            exclude zero values if True

        Returns
        -------
        SisypheVolume
            single-component volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            vol = SisypheVolume(super().getComponentArgmin(nonzero))
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('argmin')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentNumberOfNonZero(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            single-component volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentNumberOfNonZero())
            vol = SisypheVolume(super().getComponentNumberOfNonZero(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('nonzero')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    def getComponentAllZero(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
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
        SisypheVolume
            single-component volume
        """
        if self.getNumberOfComponentsPerPixel() > 1:
            # < Revision 19/12/2024
            # vol = SisypheVolume(super().getComponentAllZero())
            vol = SisypheVolume(super().getComponentAllZero(c))
            # Revision 19/12/2024 >
            vol.copyAttributesFrom(self, display=False, acquisition=False)
            vol.setFilename(self._filename)
            vol.setFilenamePrefix('allzero')
            vol.acquisition.setModalityToOT()
            return vol
        else: raise AttributeError('single component image.')

    # < Revision 04/12/2024
    # add componentsToSisypheVolumeCollection method
    def componentsToSisypheVolumeCollection(self) -> SisypheVolumeCollection:
        """
        Copy each component of the current SisypheVolume instance to a SisypheVolumeCollection.

        Returns
        -------
        SisypheVolumeCollection
            collection of components
        """
        r = SisypheVolumeCollection()
        n = self.getNumberOfComponentsPerPixel()
        if n > 1:
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(n):
                v = self.copyComponent(i)
                r.append(v)
        else: r.append(self)
        return r
    # Revision 04/12/2024 >

    # < Revision 29/07/2024
    # add getCrop method
    def getCrop(self, c: tuple | list | ndarray) -> SisypheVolume:
        """
        Get a cropped volume of the current SisypheVolume instance.

        Parameters
        ----------
        c : tuple | list
            xmin, xmax, ymin, ymax, zmin, zmax

        Returns
        -------
        SisypheVolume
            cropped volume
        """
        r = super().getCrop(c)
        r = SisypheVolume(r)
        r.copyPropertiesFrom(self, acpc=False)
        return r
    # Revision 29/07/2024 >

    # < Revision 01/08/2024
    # add getProjection method
    def getProjection(self,
                      d: str = 'left',
                      thickness: float = 0.0,
                      func: str = 'max',
                      output: str = 'native',
                      emask: SisypheVolume | None = None) -> sitkImage | ndarray | QImage | SisypheVolume:
        """
        Get a 2D projection of the current SisypheVolume instance. The projection is processed to a depth expressed in
        mm from the head surface (default 0.0, whole brain, no thickness). Operators applied to voxels on a projection
        line: maximum, mean, median, standard deviation, sum.

        Parameters
        ----------
        d : str
            direction of the projection: 'left', 'right', 'ant', 'post', 'top', 'bottom'
        thickness: float
            projection by a given thickness in mm (default 0.0, whole brain, no thickness)
        func : str
            - 'max', 'mean', 'median', 'std', 'sum', 'label'
            - if 'label': threshold > 0 instead of automatic to process mask, and then uses 'max' operator
        output : str
            output format: 'numpy' numpy.ndarray, 'sitk' SimpleITK.Image, 'qimage' PyQt5.gui.QImage, 'native' SisypheVolume
        emask : SisypheVolume
            if mask is None (default), mask is processed from the current SisypheImage instance (automatic
            thresholding with Huang algorithm for grayscale images, or non-zero voxels for label images). If an
            explicit mask is given, array size must match the current SisypheImage instance.

        Returns
        -------
        SimpleITK.Image | numpy.ndarray | PyQt5.QtGui.QPixmap | SisypheVolume
            - SimpleITK.Image if output = 'sitk',
            - numpy.ndarray if output = 'numpy',
            - PyQt5.QtGui.QImage if output = 'qimage',
            - SisypheVolume if output = 'native'
        """
        # < Revision 08/11/2024
        # avoid automatic thresholding for mask processing when image has the label modality
        if self.acquisition.isLB(): func = 'label'
        # Revision 08/11/2024 >
        # < Revision 29/08/2024
        # add qimage return
        if output == 'qimage': r = super().getProjection(d, thickness, func, 'numpy', emask)
        # Revision 29/08/2024 >
        else: r = super().getProjection(d, thickness, func, output, emask)
        if isinstance(r, SisypheImage):
            r = SisypheVolume(r)
            r.copyPropertiesFrom(self, acpc=False, slope=False)
            r.acquisition.setModalityToPJ()
            # < Revision 19/03/2025
            # projection images must have a default origin to avoid discrepancies with pre-calculated background
            # projections that have default origins.
            r.setDefaultOrigin()
            # Revision 19/03/2025 >
        # < Revision 29/08/2024
        # add qimage return
        if output == 'qimage' and isinstance(r, ndarray):
            fig = Figure()
            fig.set_facecolor('black')
            canvas = FigureCanvasAgg(fig)
            # noinspection PyTypeChecker
            axe = fig.add_axes([0, 0, 1, 1], frame_on=False, xmargin=0)
            axe.get_xaxis().set_visible(False)
            axe.get_yaxis().set_visible(False)
            axe.imshow(fliplr(r),
                       origin='lower',
                       cmap=self.display.getLUT().copyToMatplotlibColormap(),
                       vmin=self.display.getWindowMin(),
                       vmax=self.display.getWindowMax(),
                       interpolation='bilinear')
            s = canvas.get_width_height()
            canvas.draw()
            # noinspection PyUnresolvedReferences
            r = QImage(canvas.buffer_rgba(), s[0], s[1], QImage.Format_ARGB32)
            r = r.rgbSwapped()
        # Revision 29/08/2024 >
        return r
    # Revision 01/08/2024 >

    # < Revision 30/08/2024
    # add getProjection method
    def getCroppedProjection(self,
                             slc: int,
                             d: str = 'left',
                             thickness: float = 0.0,
                             func: str = 'max',
                             output: str = 'native',
                             emask: SisypheVolume | None = None) -> sitkImage | ndarray | QImage | SisypheVolume:
        """
        Get a 2D projection of the current SisypheVolume instance. The projection is processed to a depth expressed in
        mm from the head surface (default 0.0, whole brain, no thickness). Operators applied to voxels on a projection
        line: maximum, mean, median, standard deviation, sum. The volume can be cut out to a specified depth (slice
        index) in the direction of projection.

        Parameters
        ----------
        slc : int
            cutting plan (orientation is given by d parameter, see below)
        d : str
            direction of the projection: 'left', 'right', 'ant', 'post', 'top', 'bottom'
        thickness: float
            projection by a given thickness in mm (default 0.0, whole brain, no thickness)
        func : str
            - 'max', 'mean', 'median', 'std', 'sum', 'label'
            - if 'label': threshold > 0 instead of automatic to process mask, and then uses 'max' operator
        output : str
            output format: 'numpy' numpy.ndarray, 'sitk' SimpleITK.Image, 'qimage' PyQt5.gui.QImage, 'native' SisypheVolume
        emask : SisypheVolume
            if mask is None (default), mask is processed from the current SisypheImage instance (automatic
            thresholding with Huang algorithm for grayscale images, or non-zero voxels for label images). If an
            explicit mask is given, array size must match the current SisypheImage instance.

        Returns
        -------
        SimpleITK.Image | numpy.ndarray | PyQt5.QtGui.QPixmap | SisypheVolume
            - SimpleITK.Image if output = 'sitk',
            - numpy.ndarray if output = 'numpy',
            - PyQt5.QtGui.QImage if output = 'qimage',
            - SisypheVolume if output = 'native'
        """
        # < Revision 08/11/2024
        # avoid automatic thresholding for mask processing when image has the label modality
        if self.acquisition.isLB(): func = 'label'
        # Revision 08/11/2024 >
        # < Revision 29/08/2024
        # add qimage return
        if output == 'qimage': r = super().getCroppedProjection(slc, d, thickness, func, 'numpy', emask)
        # Revision 29/08/2024 >
        else: r = super().getCroppedProjection(slc, d, thickness, func, output, emask)
        if isinstance(r, SisypheImage):
            r = SisypheVolume(r)
            r.copyPropertiesFrom(self, acpc=False, slope=False)
            r.acquisition.setModalityToPJ()
            # < Revision 19/03/2025
            # projection images must have a default origin to avoid discrepancies with pre-calculated background
            # projections that have default origins.
            r.setDefaultOrigin()
            # Revision 19/03/2025 >
        # < Revision 29/08/2024
        # add qimage return
        if output == 'qimage' and isinstance(r, ndarray):
            fig = Figure()
            fig.set_facecolor('black')
            canvas = FigureCanvasAgg(fig)
            # noinspection PyTypeChecker
            axe = fig.add_axes([0, 0, 1, 1], frame_on=False, xmargin=0)
            axe.get_xaxis().set_visible(False)
            axe.get_yaxis().set_visible(False)
            axe.imshow(fliplr(r),
                       origin='lower',
                       cmap=self.display.getLUT().copyToMatplotlibColormap(),
                       vmin=self.display.getWindowMin(),
                       vmax=self.display.getWindowMax(),
                       interpolation='bilinear')
            s = canvas.get_width_height()
            canvas.draw()
            # noinspection PyUnresolvedReferences
            r = QImage(canvas.buffer_rgba(), s[0], s[1], QImage.Format_ARGB32)
            r = r.rgbSwapped()
        # Revision 29/08/2024 >
        return r
    # Revision 30/08/2024 >

    # < Revision 15/09/2024
    # add getFlip method
    def getFlip(self, axis: list[bool]) -> SisypheVolume:
        """
        Get a flipped copy of the current SisypheVolume instance.

        Parameters
        ----------
        axis : list[bool, bool, bool]
            flip axis if True, axis order x, y, z.

        Returns
        -------
        SisypheVolume
            flipped volume
        """
        v = self.copy()
        v.flip(axis)
        prefix = 'flip'
        if axis[0]: prefix += 'x'
        if axis[1]: prefix += 'y'
        if axis[2]: prefix += 'z'
        if v.hasFilename(): v.setFilenamePrefix(prefix)
        return v
    # Revision 15/09/2024 >

    # < Revision 20/10/2024
    # add getStandardizeIntensity method, not yet tested
    def getStandardizeIntensity(self, method: str = 'norm') -> SisypheVolume:
        """
        Get an intensity normalized copy of the current SisypheImage instance.

        Parameters
        ----------
        method : str
            - 'norm', standardize the intensity as zscore (i.e. zero mean, [-std, +std] mapped to [0, 1]
            - 'rescale', standardize the intensity values to the range [0, 1]

        Returns
        -------
            SisypheVolume
                standardized volume
        """
        r = super().getStandardizeIntensity(method)
        r = SisypheVolume(r)
        r.copyPropertiesFrom(self, slope=False)
        r.setFilename(self.getFilename())
        return r
    # Revision 20/10/2024 >

    # < Revision 20/10/2024
    # add getTruncateIntensity method, not yet tested
    def getTruncateIntensity(self,
                             centile: int = 1,
                             outputrange: tuple[float, float] | None = None) -> SisypheVolume:
        """
        Get intensity truncated copy of the current SisypheImage instance. Truncate threshold is expressed in
        percentile (min threshold = centile, max threshold = 100 - centile). The max and min values of the output image
        are given in the output range parameter. If output range is None, max and min values of the output image are
        the max and min truncate thresholds.

        Parameters
        ----------
        centile : int
            truncate threshold expressed in percentile
        outputrange : tuple[float, float] | None
            max and min values of the output image

        Returns
        -------
            SisypheVolume
                truncated volume
        """
        r = super().getTruncateIntensity(centile, outputrange)
        r = SisypheVolume(r)
        r.copyPropertiesFrom(self, slope=False)
        r.setFilename(self.getFilename())
        return r
    # Revision 20/10/2024 >

    # Geometric transformation methods

    def setTransforms(self, transforms: SisypheTransforms, force: bool = False) -> None:
        """
        Set the transforms attribute of the current SisypheVolume attribute. Each SisypheVolume is associated with a
        SisypheTransforms instance which stores all the geometric transformations calculated from co-registrations with
        other SisypheVolume instances. This transforms attribute is saved the same file name with .xtrfs extension.

        Parameters
        ----------
        transforms : SisypheTransforms
            geometric transform collection to copy
        force : bool
            if True, ignores reference ID (default False)
        """
        from Sisyphe.core.sisypheTransform import SisypheTransforms
        if isinstance(transforms, SisypheTransforms):
            if force:
                self._transforms = transforms
                self._transforms.setReferenceID(self.getID())
            elif transforms.getReferenceID() == self.getID():
                self._transforms = transforms
            else: raise ValueError('SisypheTransforms parameter and SisypheVolume do not have the same ID.')
        else: raise TypeError('parameter type {} is not SisypheTransforms.'.format(type(transforms)))

    def getTransforms(self) -> SisypheTransforms:
        """
        Set the transforms attribute of the current SisypheVolume attribute. Each SisypheVolume is associated with a
        SisypheTransforms instance, which stores all the geometric transformations calculated from co-registrations
        with other SisypheVolume instances. This transforms attribute is saved the same file name with .xtrfs extension.

        Returns
        -------
        SisypheTransforms
            geometric transform collection
        """
        return self._transforms

    def hasTransform(self, ID: str | SisypheVolume) -> bool:
        """
        Check whether the transforms attribute of the current SisypheVolume attribute contains a given ID.

        Parameters
        ----------
        ID : str | SisypheVolume
            ID or SisypheVolume ID attribute

        Returns
        -------
        bool
            True if geometric transform is in collection
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str): return ID in self.getTransforms()
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def isIdentityTransform(self, ID: str | SisypheVolume) -> bool:
        """
        Check whether the geometric transformation corresponding to a given ID in the transforms attribute of the
        current SisypheVolume instance, is an identity transformation.

        Parameters
        ----------
        ID : str | SisypheVolume
            ID or SisypheVolume ID attribute

        Returns
        -------
        bool
            True if identity geometric transform
        """
        r = False
        trf = self.getTransformFromID(ID)
        if trf is not None: r = trf.isIdentity()
        return r

    def getTransformFromID(self, ID: str | SisypheVolume) -> SisypheTransform | None:
        """
        Get the geometric transformation corresponding to a given ID in the transforms attribute of the current
        SisypheVolume instance.

        Parameters
        ----------
        ID : str | SisypheVolume
            ID or SisypheVolume ID attribute

        Returns
        -------
        Sisyphe.core.sisypheTransform.SisypheTransform | None
            geometric transform
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            if self.hasTransform(ID): return self.getTransforms()[ID]
            else: return None
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def getTransformFromIndex(self, index: int) -> SisypheTransform:
        """
        Get the geometric transformation corresponding to a given index in the transforms attribute of the current
        SisypheVolume instance.

        Parameters
        ----------
        index : int
            index in geometric transform collection

        Returns
        -------
        Sisyphe.core.sisypheTransform.SisypheTransform
            geometric transform
        """
        if isinstance(index, int):
            if 0 <= index < self.getTransforms().count():
                return self.getTransforms()[index]
            else: raise IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(index)))

    def loadTransforms(self) -> None:
        """
        Load the transforms attribute of the current SisypheVolume instance. Each SisypheVolume is associated with a
        SisypheTransforms instance, which stores all the geometric transformations calculated from co-registrations
        with other SisypheVolume instances.
        """
        filename = splitext(self._filename)[0] + self._transforms.getFileExt()
        if exists(filename): self._transforms.load(filename)
        else:  # init transforms
            self._transforms.clear()
            self._transforms.setReferenceID(self)

    def saveTransforms(self) -> None:
        """
        Save the transforms attribute of the current SisypheVolume instance. Each SisypheVolume is associated with a
        SisypheTransforms instance, which stores all the geometric transformations calculated from co-registrations
        with other SisypheVolume instances.
        """
        if self.hasFilename():
            path, ext = splitext(self._filename)
            filename = path + self._transforms.getFileExt()
            if len(self._transforms) > 0:
                self._transforms.save(filename)
            # < Revision 18/04/2025
            else:
                if exists(filename): remove(filename)
            # Revision 18/04/2025 >

    def hasICBMTransform(self) -> bool:
        """
        Check whether the transforms attribute of the current SisypheVolume instance contains a geometric
        transformation to the ICBM152 template space (contains ID == 'ICBM152').

        Returns
        -------
        bool
            True if an ICBM152 transform is in collection
        """
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        return self.hasTransform(icbmid)

    def getICBMTransform(self) -> SisypheTransform | None:
        """
        Get the geometric transformation to the ICBM152 template space (if any) in the transforms attribute of the
        current SisypheVolume instance.

        Returns
        -------
        Sisyphe.core.sisypheTransform.SisypheTransform | None
            geometric transform to ICBM152 template space
        """
        from Sisyphe.core.sisypheTransform import SisypheTransform
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        if self.hasICBMTransform(): return self._transforms[icbmid]
        elif self.acquisition.isICBM152():
            trf = SisypheTransform()
            trf.setIdentity()
            trf.setID(icbmid)
            return trf
        else: return None

    def getICBMfromWorld(self, p: vectorFloat3) -> vectorFloat3 | None:
        """
        Convert world coordinates to ICBM coordinates. Returns None if the transforms attribute of the current
        SisypheVolume instance does not contain the 'ICBM152' ID.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            World coordinates

        Returns
        -------
        tuple[float, float, float] | None
            ICBM coordinates
        """
        icbmid = SisypheAcquisition.getTemplatesList()[0]  # ICBM152
        if self.hasICBMTransform(): return self._transforms[icbmid].applyToPoint(p)
        elif self.acquisition.isICBM152(): return p
        else: return None

    def getWorldfromICBM(self, p: vectorFloat3) -> vectorFloat3 | None:
        """
        Convert ICBM coordinates to world coordinates Returns None if the transforms attribute of the current
        SisypheVolume instance does not contain the 'ICBM152' ID.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            ICBM coordinates

        Returns
        -------
        tuple[float, float, float] | None
            world coordinates
        """
        if self.hasICBMTransform(): return self._transforms['ICBM'].applyInverseToPoint(p)
        else: return None

    def hasLEKSELLTransform(self) -> bool:
        """
        Check whether the transforms attribute of the current SisypheVolume instance contains a geometric
        transformation to the LEKSELL space (contains ID == 'LEKSELL').

        Returns
        -------
        bool
            True if a LEKSELL transform is in collection
        """
        return self.hasTransform('LEKSELL')

    def getLEKSELLTransform(self) -> SisypheTransform | None:
        """
        Get the geometric transformation to the LEKSELL space (if any) in the transforms attribute of the current
        SisypheVolume instance.

        Returns
        -------
        Sisyphe.core.sisypheTransform.SisypheTransform
            geometric transform to LEKSELL space
        """
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL']
        else: return None

    def getLEKSELLfromWorld(self, p: vectorFloat3) -> vectorFloat3 | None:
        """
        Convert world coordinates to LEKSELL coordinates Returns None if the transforms attribute of the current
        SisypheVolume instance does not contain the 'LEKSELL' ID.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            World coordinates

        Returns
        -------
        tuple[float, float, float] | None
            LEKSELL coordinates
        """
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL'].applyToPoint(p)
        else: return None

    def getWorldfromLEKSELL(self, p: vectorFloat3) -> vectorFloat3 | None:
        """
        Convert LEKSELL coordinates to world coordinates Returns None if the transforms attribute of the current
        SisypheVolume instance does not contain the 'LEKSELL' ID.

        Parameters
        ----------
        p : list[float, float, float] | tuple[float, float, float]
            LEKSELL coordinates

        Returns
        -------
        tuple[float, float, float] | None
            world coordinates
        """
        if self.hasLEKSELLTransform(): return self._transforms['LEKSELL'].applyInverseToPoint(p)
        else: return None

    def getWorldfromTransform(self, ID: str | SisypheVolume, p: vectorFloat3) -> vectorFloat3:
        """
        Extract the geometric transformation corresponding to an ID key from the SisypheTransforms attribute of the
        current SisypheVolume instance. Then apply this geometric transformation to a given point.

        Parameters
        ----------
        ID : str | SisypheVolume
            ID or SisypheVolume ID attribute
        p : list[float, float, float] | tuple[float, float, float]
            point coordinates

        Returns
        -------
        tuple[float, float, float]
            point coordinates, returns the same point coordinates if the ID is not in the SisypheTransforms attribute
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, str):
            if self.hasTransform(ID):
                return self._transforms[ID].applyToPoint(p)
            else: return p
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    # XmlDicom methods

    def hasXmlDicom(self) -> bool:
        """
        Check whether the XmlDicom instance of the current SisypheVolume instance is defined (not None). XmlDicom file
        stores DICOM fields in a key/value XML file. Each SisypheVolume converted from Dicom files is associated with
        an XmlDicom file (same file name with .xdcm extension).

        Returns
        -------
        Sisyphe.core.sisypheDicom.XmlDicom
            XmlDicom attribute
        """
        if self.hasFilename():
            from Sisyphe.core.sisypheDicom import XmlDicom
            filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
            return exists(filename)
        else: return False

    def getXmlDicom(self) -> XmlDicom | None:
        """
        Get the XmlDicom instance of the current SisypheVolume instance. XmlDicom file stores DICOM fields in a
        key/value XML file. Each SisypheVolume converted from Dicom files is associated with an XmlDicom file (same
        file name with .xdcm extension).

        Returns
        -------
        Sisyphe.core.sisypheDicom.XmlDicom
            XmlDicom attribute
        """
        from Sisyphe.core.sisypheDicom import XmlDicom
        if self._xdcm is not None: return self._xdcm
        else:
            filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
            # noinspection PyInconsistentReturns
            if exists(filename):
                self.loadXmlDicom()
                return self._xdcm

    def loadXmlDicom(self) -> None:
        """
        Load the XmlDicom instance associated to the current SisypheVolume instance. XmlDicom file stores DICOM fields
        in a key/value XML file. Each SisypheVolume converted from Dicom files is associated with an XmlDicom file
        (same file name with .xdcm extension).
        """
        from Sisyphe.core.sisypheDicom import XmlDicom
        if self.hasFilename():
            filename = splitext(self.getFilename())[0] + XmlDicom.getFileExt()
            if exists(filename):
                self._xdcm = XmlDicom()
                self._xdcm.loadXmlDicomFilename(filename)

    def clearXmlDicom(self) -> None:
        """
        Clear the XmlDicom instance of the current SisypheVolume instance (set to None).
        """
        self._xdcm = None

    # Capture methods

    # < Revision 29/08/2024
    # add getBitmapCapture method
    def getBitmapCapture(self, index: int, zoom: float = 1.0, orient: str = 'a') -> QImage:
        """
        Get a bitmap capture of the current SisypheVolume instance.

        Parameters
        ----------
        index : int
            slice index
        zoom : float
            zoom factor (default 1.0, no zoom)
        orient : int
            slice orientation ('a' axial, 'c' coronal or 's' sagittal)

        Returns
        -------
        PyQt5.QtGui.QImage
            Bitmap Qt image
        """
        img = self.getNumpy()
        orient = orient[0]
        fov = self.getFieldOfView()
        zoom = zoom / 100.0
        fig = Figure()
        if orient == 'a':
            img = img[index, :, :]
            fig.set_size_inches(fov[0] * zoom, fov[1] * zoom)
        elif orient == 'c':
            img = img[:, index, :]
            fig.set_size_inches(fov[0] * zoom, fov[2] * zoom)
        elif orient == 's':
            img = img[:, :, index]
            fig.set_size_inches(fov[1] * zoom, fov[2] * zoom)
        else: raise ValueError('\'{}\' is not a valid orientation parameter (\'a\', \'c\' or \'s\').'.format(orient))
        fig.set_facecolor('black')
        canvas = FigureCanvasAgg(fig)
        # noinspection PyTypeChecker
        axe = fig.add_axes([0, 0, 1, 1], frame_on=False, xmargin=0)
        axe.get_xaxis().set_visible(False)
        axe.get_yaxis().set_visible(False)
        axe.imshow(fliplr(img),
                   origin='lower',
                   cmap=self.display.getLUT().copyToMatplotlibColormap(),
                   vmin=self.display.getWindowMin(),
                   vmax=self.display.getWindowMax(),
                   interpolation='bilinear')
        s = canvas.get_width_height()
        canvas.draw()
        # noinspection PyUnresolvedReferences
        qimg = QImage(canvas.buffer_rgba(), s[0], s[1], QImage.Format_ARGB32)
        return qimg.rgbSwapped()
    # Revision 29/08/2024 >

    # < Revision 29/08/2024
    # add saveBitmapCapture method
    def saveBitmapCapture(self, filename: str, index: int, zoom: float = 1.0, orient: str = 'a') -> None:
        """
        Save a bitmap capture of the current SisypheVolume instance.

        Parameters
        ----------
        filename : str
        index : int
            slice index
        zoom : float
            zoom factor (default 1.0, no zoom)
        orient : int
            slice orientation ('a' axial, 'c' coronal or 's' sagittal)

        Returns
        -------
        PyQt5.QtGui.QPixmap
            Bitmap Qt pixmap
        """
        ext = splitext(filename)[1].lower()
        if ext in ('.bmp', '.gif', '.jpg', '.jpeg', '.png', 'xpm'):
            img = self.getBitmapCapture(index, zoom, orient)
            img.save(filename)
        else: raise ValueError('{} format is not supported (bmp, gif, jpg, jpeg, png or xpm).'.format(ext))
    # Revision 29/08/2024 >

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
            # Display nodes
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

    def save(self, filename: str = '', single: bool = True) -> None:
        """
        Save the current SisypheVolume instance to a PySisyphe Volume (.xvol) file.

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name (optional). if filename is empty ('', default), the file name attribute of the
            current SisypheVolume instance is used
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xvol file and the binary part in .raw file
        """
        if not self.isEmpty():
            if filename != '': self.setFilename(filename)
            if self.hasFilename(): self.saveAs(self._filename, single)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('Data array is empty.')

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheVolume instance attributes from xml instance. This method is called by load() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict[str]
            Key / Value
                - 'size': list[int, int, int], image size in each axis
                - 'components': int, number of components
                - 'spacing': list[float, float, float], voxel size in each axis
                - 'origin': list[float, float, float], origin coordinates
                - 'datatype': str, numpy datatype
                - 'directions': list[float], direction vectors
                - 'array': bytes, array image
        """
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
                            # < Revision 17/11/2024
                            # list to tuple conversion
                            # attr['size'] = [int(i) for i in buff]
                            attr['size'] = tuple([int(i) for i in buff])
                            # Revision 17/11/2024 >
                        elif childnode.nodeName == 'components':
                            attr['components'] = int(childnode.firstChild.data)
                        elif childnode.nodeName == 'spacing':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            # < Revision 17/11/2024
                            # list to tuple conversion
                            # attr['spacing'] = [float(i) for i in buff]
                            attr['spacing'] = tuple([float(i) for i in buff])
                            # Revision 17/11/2024 >
                        elif childnode.nodeName == 'origin':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            # < Revision 17/11/2024
                            # list to tuple conversion
                            # attr['origin'] = [float(i) for i in buff]
                            attr['origin'] = tuple([float(i) for i in buff])
                            # Revision 17/11/2024 >
                        elif childnode.nodeName == 'orientation':
                            self.setOrientation(childnode.firstChild.data)
                        elif childnode.nodeName == 'datatype':
                            attr['datatype'] = childnode.firstChild.data
                        elif childnode.nodeName == 'directions':
                            buff = childnode.firstChild.data
                            buff = buff.split(' ')
                            # < Revision 17/11/2024
                            # list to tuple conversion
                            # attr['directions'] = [float(i) for i in buff]
                            attr['directions'] = tuple([float(i) for i in buff])
                            # Revision 17/11/2024 >
                        elif childnode.nodeName == 'slope':
                            try: self._slope = float(childnode.firstChild.data)
                            except: self._slope = 1.0
                        elif childnode.nodeName == 'intercept':
                            try: self._intercept = float(childnode.firstChild.data)
                            except: self._intercept = 0.0
                        childnode = childnode.nextSibling
                elif node.nodeName == 'array':
                    attr['array'] = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')

    def load(self, filename: str = '', binary: bool = True) -> None:
        """
        Load the current SisypheVolume instance from a PySisyphe Volume (.xvol) file.

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name (optional). If filename is empty ('', default), the file name attribute of the
            current SisypheVolume instance is used
        binary : bool
            if False, load only xml part (attributes), not binary part (array), default is True (load xml and binary
            parts)
        """
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
                # attr = self.parseXML(doc)
                self._attr = self.parseXML(doc)
                # Read binary array part
                if binary:
                    buff = None
                    # rawname = attr['array']
                    rawname = self._attr['array']
                    if rawname == 'self':
                        buff = f.read()
                    else:
                        rawname = join(dirname(filename), basename(rawname))
                        rawname = '{}.raw'.format(splitext(rawname)[0])
                        if exists(rawname):
                            with open(rawname, 'rb') as fa:
                                buff = fa.read()
                    if buff is not None:
                        # < Revision 17/11/2024
                        # replace attr by self._attr
                        if self._compression: buff = decompress(buff)
                        # img = frombuffer(buff, dtype=attr['datatype'])
                        img = frombuffer(buff, dtype=self._attr['datatype'])
                        # size = attr['size']
                        size = self._attr['size']
                        # if attr['components'] == 1: img = img.reshape((size[2], size[1], size[0]))
                        if self._attr['components'] == 1: img = img.reshape((size[2], size[1], size[0]))
                        # <revision 16/07/2024
                        # bug multicomponent loading, reshape to default order (n, z, y, x) and not native order (z, y, x, n)
                        # else: img = img.reshape((size[2], size[1], size[0], attr['components']))
                        # else: img = img.reshape((attr['components'], size[2], size[1], size[0]))
                        else: img = img.reshape((self._attr['components'], size[2], size[1], size[0]))
                        # revision 16/07/2024>
                        # self.copyFromNumpyArray(img,
                        #                         spacing=attr['spacing'],
                        #                         origin=attr['origin'],
                        #                         direction=attr['directions'],
                        #                         defaultshape=True)
                        self.copyFromNumpyArray(img,
                                                spacing=self._attr['spacing'],
                                                origin=self._attr['origin'],
                                                direction=self._attr['directions'],
                                                defaultshape=True)
                        # Revision 17/11/2024 >
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
        """
        Write the current SisypheVolume instance attributes to xml instance. This method is called by save() and
        saveAs() methods, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xvol file and the binary part in .raw file
        """
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
            # Display nodes
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
        """
        Save the current SisypheVolume instance to a PySisyphe Volume (.xvol) file.

        Parameters
        ----------
        filename : str
            PySisyphe Volume file name
        single : bool
            - if True, saved in a single file (xml part + binary part)
            - if False, The xml part is saved in .xvol file and the binary part in .raw file
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
            buffxml = doc.toprettyxml().encode()   # Convert utf-8 to binary
            buffarray = self.getNumpy().tobytes()  # Default shape (n, z, y, x) if multicomponent
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
        """
        Load the current SisypheVolume instance from an old Sisyphe Volume (.vol) file.

        Parameters
        ----------
        filename : str
            old Sisyphe Volume file name
        """
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
        elif modality == 'CAR':
            if sequence == 'E T':
                # < Revision 31/07/2024
                self._acquisition.setSequenceToTMap()
                self._acquisition.setAutoCorrelations((hdr['fwhmx'], hdr['fwhmy'], hdr['fwhmz']))
                self._acquisition.setDegreesOfFreedom(int(hdr['TR']))
                # Revision 31/07/2024 >
            elif sequence == 'E Z':
                # < Revision 31/07/2024
                self._acquisition.setSequenceToZMap()
                self._acquisition.setAutoCorrelations((hdr['fwhmx'], hdr['fwhmy'], hdr['fwhmz']))
                self._acquisition.setDegreesOfFreedom(int(hdr['TR']))
                # Revision 31/07/2024 >
        else:
            self._acquisition.setModality('OT')
            if sequence == ' SG': self._acquisition.setSequenceToGreyMatterMap()
            elif sequence == ' SB': self._acquisition.setSequenceToWhiteMatterMap()
            elif sequence == 'LCR': self._acquisition.setSequenceToCerebroSpinalFluidMap()
            elif sequence == 'DSC': self._acquisition.setSequenceToCerebralBloodFlowMap()
            elif sequence == 'VSC': self._acquisition.setSequenceToCerebralBloodVolumeMap()
            elif sequence == 'TTM': self._acquisition.setSequenceToMeanTransitTimeMap()
            elif sequence == ' FA': self._acquisition.setSequenceToFractionalAnisotropyMap()
            elif sequence == 'ADC': self._acquisition.setSequenceToApparentDiffusionMap()
            elif sequence == 'ROI': self._acquisition.setSequenceToMask()
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
        """
        Load the current SisypheVolume instance from a BrainVoyager (.vmr) file.

        Parameters
        ----------
        filename : str
            BrainVoyager file name
        """
        super().loadFromBrainVoyagerVMR(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def loadFromFreeSurferMGH(self, filename: str) -> None:
        """
        Load the current SisypheVolume instance from a FreeSurfer (.mgh, .mgz) file.

        Parameters
        ----------
        filename : str
            FreeSurfer file name
        """
        super().loadFromFreeSurferMGH(filename)
        self._calcID()
        self._updateRange()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def loadFromNIFTI(self, filename: str, reorient: bool = True) -> None:
        """
        Load the current SisypheVolume instance from a Nifti (.nii) file.

        Parameters
        ----------
        filename : str
            Nifti file name
        reorient : bool
            conversion to RAS+ world coordinates convention if True (default)
        """
        super().loadFromNIFTI(filename, reorient)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    # noinspection PyShadowingNames
    def saveToNIFTI(self, filename: str = '', compress: bool = False) -> None:
        """
        Save the current SisypheVolume instance to a Nifti (.nii) file.

        Parameters
        ----------
        filename : str
            Nifti file name, if filename is empty ('', default), the file name attribute of
            the current SisypheVolume instance is used
        compress : bool
            gzip compression if True (default False)
        """
        if filename == '': filename = splitext(self.getFilename())[0] + getNiftiExt()[0]
        super().saveToNIFTI(filename, compress)

    def loadFromNRRD(self, filename: str) -> None:
        """
        Load the current SisypheVolume instance from a Nrrd (.nrrd) file.

        Parameters
        ----------
        filename : str
            Nrrd file name
        """
        super().loadFromNRRD(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToNRRD(self, filename: str = '') -> None:
        """
        Save the current SisypheVolume instance to a Nrrd (.nrrd) file.

        Parameters
        ----------
        filename : str
            Nrrd file name, if filename is empty ('', default), the file name attribute of the current SisypheVolume
            instance is used
        """
        if filename == '': filename = splitext(self.getFilename())[0] + getNrrdExt()[0]
        super().saveToNRRD(filename)

    def loadFromMINC(self, filename: str) -> None:
        """
        Load the current SisypheVolume instance from a Minc (.minc) file.

        Parameters
        ----------
        filename : str
            Minc file name
        """
        super().loadFromMINC(filename)
        self._calcID()
        self._updateRange()
        self._updateOrientation()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToMINC(self, filename: str = '') -> None:
        """
        Save the current SisypheVolume instance to a Minc (.minc) file.

        Parameters
        ----------
        filename : str
            Minc file name, if filename is empty ('', default), the file name attribute of the current SisypheVolume
            instance is used
        """
        if filename == '': filename = splitext(self.getFilename())[0] + getMincExt()[0]
        super().saveToMINC(filename)

    def loadFromVTK(self, filename: str) -> None:
        """
        Load the current SisypheVolume instance from a VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        super().loadFromVTK(filename)
        self._calcID()
        self._updateRange()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToVTK(self, filename: str = '') -> None:
        """
        Save the current SisypheVolume instance to a VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name, if filename is empty ('', default), the file name attribute of the current SisypheVolume
            instance is used
        """
        if filename == '': filename = splitext(self.getFilename())[0] + getVtkExt()[1]
        super().saveToVTK(filename)

    def loadFromNumpy(self, filename: str) -> None:
        """
        Load the current SisypheVolume instance from a numpy (.npy) file.

        Parameters
        ----------
        filename : str
            numpy file name
        """
        super().loadFromNumpy(filename)
        self._calcID()
        self._updateRange()
        self.setFilename(filename)
        # Init transforms
        self._transforms.clear()
        self._transforms.setReferenceID(self)

    def saveToNumpy(self, filename: str = '') -> None:
        """
        Save the current SisypheVolume instance to a numpy (.npy) file.

        Parameters
        ----------
        filename : str
            numpy file name, if filename is empty ('', default), the file name attribute of the current SisypheVolume
            instance is used
        """
        if filename == '': filename = splitext(self.getFilename())[0] + getNumpyExt()[0]
        super().saveToNumpy(filename)

    # Properties

    # noinspection PyTypeChecker
    identity = property(getIdentity, setIdentity)
    # noinspection PyTypeChecker
    acquisition = property(getAcquisition, setAcquisition)
    # noinspection PyTypeChecker
    display = property(getDisplay, setDisplay)
    # noinspection PyTypeChecker
    transforms = property(getTransforms, setTransforms)
    # noinspection PyTypeChecker
    acpc = property(getACPC, setACPC)
    # noinspection PyTypeChecker
    dicom = property(getXmlDicom)


# noinspection PyShadowingBuiltins
class SisypheVolumeCollection(object):
    """
    Description
    ~~~~~~~~~~~

    Named list container of SisypheVolume instances. Container key to address elements can be int index, ID str or
    SisypheVolume (uses ID attribute as str key).

    Getter methods of the SisypheVolume class are added to the SisypheVolumeCollection class, returning a list
    of values sent by each SisypheVolume element in the container.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheVolumeCollection

    Creation: 04/02/2021
    Last revision: 06/06/2025
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

    """
    Private attributes

    _volumes        list[SisypheVolume]
    _index          int, index for Iterator
    _homogeneous    bool, all volumes have the same data type and field of view (True) or not (False)    
    """

    def __init__(self) -> None:
        """
        SisypheVolumeCollection instance constructor.
        """
        self._volumes = list()
        self._index = 0
        self._homogeneous = False

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheVolumeCollection instance to str
        """
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
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheVolumeCollection instance representation
        """
        return 'SisypheVolumeCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container Public methods

    def __getitem__(self, key: int | str | slice | list[str]) -> SisypheVolume | SisypheVolumeCollection:
        """
        Special overloaded container getter method. Get a SisypheVolume element from container, key which can be int
        index, ID, slicing indexes (start:stop:step) or list of ID.

        Parameters
        ----------
        key : int| str | slice | list[str]
            index, ID, slicing indexes (start:stop:step) or list of ID

        Returns
        -------
        SisypheVolume | SisypheVolumeCollection
            SisypheVolumeCollection if key is slice or list[str]
        """
        # key is SisypheVolume arrayID str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._volumes): return self._volumes[key]
            else: raise IndexError('key parameter is out of range.')
        elif isinstance(key, slice):
            vols = SisypheVolumeCollection()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(key.start, key.stop, key.step):
                vols.append(self._volumes[i])
            return vols
        elif isinstance(key, list):
            vols = SisypheVolumeCollection()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(self._volumes)):
                if self._volumes[i].getID() in key:
                    vols.append(self._volumes[i])
            return vols
        else: raise TypeError('parameter type {} is not int, str, slice or list[str].'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheVolume) -> None:
        """
        Special overloaded container setter method. Set a SisypheVolume element in the container.

        Parameters
        ----------
        key : int
            index
        value : SisypheVolume
            volume to be placed at key position
        """
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

    def __delitem__(self, key: int | str | SisypheVolume) -> None:
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheVolume element in the
        container.

        Parameters
        ----------
        key : int | str | SisypheVolume
            index, ID, SisypheVolume ID attribute
        """
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
        """
        Special overloaded method called by the built-in len() python function. Returns the number of SisypheVolume
        elements in the container.

        Returns
        -------
        int
            number of SisypheVolume elements
        """
        return len(self._volumes)

    def __contains__(self, value: str | SisypheVolume) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a SisypheVolume
        is in the container.

        Parameters
        ----------
        value : str | SisypheVolume
            ID, SisypheVolume ID attribute

        Returns
        -------
        bool
            True if value is in the container.
        """
        keys = [k.getArrayID() for k in self._volumes]
        # value is SisypheVolume arrayID str
        if isinstance(value, str):
            return value in keys
        # value is SisypheVolume
        elif isinstance(value, SisypheVolume):
            return value.getArrayID() in keys
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> SisypheVolume:
        """
        Special overloaded container called by the built-in 'next()' python iterator method. Returns the next value for
        the iterable.
        """
        if self._index < len(self._volumes):
            n = self._index
            self._index += 1
            return self._volumes[n]
        else: raise StopIteration

    def __getattr__(self, name: str):
        """
        Special overloaded method called when attribute does not exist in the class. Try iteratively calling the setter
        or getter methods of the sisypheVolume instances in the container. Getter methods return a list of the same
        size as the container.

        Parameters
        ----------
        name : str
            attribute name of the SisypheVolume class (container element)
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
                            if prefix == 'get':
                                return [vol.identity.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.identity.__getattribute__(name)()
                        elif name in SisypheAcquisition.__dict__:
                            if prefix == 'get':
                                return [vol.acquisition.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.acquisition.__getattribute__(name)()
                        elif name in SisypheDisplay.__dict__:
                            if prefix == 'get':
                                return [vol.display.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.display.__getattribute__(name)()
                        elif name in SisypheACPC.__dict__:
                            if prefix == 'get':
                                return [vol.acpc.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.acpc.__getattribute__(name)()
                        elif flag:
                            if prefix == 'get':
                                return [vol.__getattribute__(name)() for vol in self]
                            else:
                                for vol in self: vol.__getattribute__(name)()
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                    else: raise AttributeError('Not get/set method.')
                # SisypheVolume set methods with argument
                # < Revision 04/12/2024
                # elif prefix == 'set':
                # Revision 04/12/2024 >
                elif len(args) == 1:
                    p = args[0]
                    # SisypheVolume set method argument is list
                    if isinstance(p, (list, tuple)):
                        n = len(p)
                        if n == self.count():
                            if name in SisypheIdentity.__dict__:
                                # noinspection PyUnresolvedReferences
                                i: cython.int
                                for i in range(n): self[i].identity.__getattribute__(name)(p[i])
                            elif name in SisypheAcquisition.__dict__:
                                # noinspection PyUnresolvedReferences
                                i: cython.int
                                for i in range(n): self[i].acquisition.__getattribute__(name)(p[i])
                            elif name in SisypheDisplay.__dict__:
                                # noinspection PyUnresolvedReferences
                                i: cython.int
                                for i in range(n): self[i].display.__getattribute__(name)(p[i])
                            elif name in SisypheACPC.__dict__:
                                # noinspection PyUnresolvedReferences
                                i: cython.int
                                for i in range(n): self[i].acpc.__getattribute__(name)(p[i])
                            elif flag:
                                # noinspection PyUnresolvedReferences
                                i: cython.int
                                for i in range(n): self[i].__getattribute__(name)(p[i])
                            else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                        else: raise ValueError('Number of items in list ({}) '
                                               'does not match with {} ({}).'.format(p, self.__class__, self.count()))
                    # SisypheVolume set method argument is a single value (int, float, str, bool)
                    else:
                        if name in SisypheIdentity.__dict__:
                            if prefix == 'get':
                                return [vol.identity.__getattribute__(name)(p) for vol in self]
                            else:
                                for vol in self: vol.identity.__getattribute__(name)(p)
                        elif name in SisypheAcquisition.__dict__:
                            if prefix == 'get':
                                return [vol.acquisition.__getattribute__(name)(p) for vol in self]
                            else:
                                for vol in self: vol.acquisition.__getattribute__(name)(p)
                        elif name in SisypheDisplay.__dict__:
                            if prefix == 'get':
                                return [vol.display.__getattribute__(name)(p) for vol in self]
                            else:
                                for vol in self: vol.display.__getattribute__(name)(p)
                        elif name in SisypheACPC.__dict__:
                            if prefix == 'get':
                                return [vol.acpc.__getattribute__(name)(p) for vol in self]
                            else:
                                for vol in self: vol.acpc.__getattribute__(name)(p)
                        elif flag:
                            if prefix == 'get':
                                return [vol.__getattribute__(name)(p) for vol in self]
                            else:
                                for vol in self: vol.__getattribute__(name)(p)
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
            return func
        raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Public methods

    def isEmpty(self) -> bool:
        """
        Check if SisypheVolumeCollection instance container is empty.

        Returns
        -------
        bool
            True if container is empty
        """
        return len(self._volumes) == 0

    def isHomogeneous(self) -> bool:
        """
        Check whether SisypheVolume instances is the current SisypheVolumeCollection are homogeneous (i.e. same field
        of view and datatype)

        Returns
        -------
        bool
            True if container is homogeneous
        """
        return self._homogeneous

    def count(self) -> int:
        """
        Get the number of SisypheVolume elements in the current SisypheVolumeCollection instance container.

        Returns
        -------
        int
            number of SisypheVolume elements
        """
        return len(self._volumes)

    def remove(self, value: int | str | SisypheVolume) -> None:
        """
        Remove a SisypheVolume element from the current SisypheVolumeCollection instance container.

        Parameters
        ----------
        value : int | str | SisypheVolume
            index, ID, SisypheVolume ID attribute
        """
        # value is SisypheVolume
        if isinstance(value, SisypheVolume):
            self._volumes.remove(value)
        # value is SisypheVolume arrayID str or int
        elif isinstance(value, (str, int)):
            self.pop(self.index(value))
        else: raise TypeError('parameter type {} is not int, str or SisypheVolume.'.format(type(value)))
        if self.isEmpty(): self._homogeneous = False

    def pop(self, key: int | str | SisypheVolume | None = None) -> SisypheVolume:
        """
        Remove a SisypheVolume element from the current SisypheVolumeCollection instance container and return it. If
        key is None, removes and returns the last element.

        Parameters
        ----------
        key : int | str | SisypheVolume
            - index, ID, SisypheVolume ID attribute
            - if None, remove the last element

        Returns
        -------
        SisypheVolume
            element removed from the container
        """
        if key is None: return self._volumes.pop()
        # key is SisypheVolume arrayID str
        if isinstance(key, (str, SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._volumes.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current SisypheVolumeCollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        return [k.getArrayID() for k in self._volumes]

    def index(self, value: str | SisypheVolume) -> int:
        """
        Index of a SisypheVolume element in the current SisypheVolumeCollection instance container.

        Parameters
        ----------
        value : str | SisypheVolume
            ID, SisypheVolume ID attribute

        Returns
        -------
        int
            index
        """
        keys = [k.getArrayID() for k in self._volumes]
        # value is SisypheVolume
        if isinstance(value, SisypheVolume):
            value = value.getArrayID()
        # value is SisypheVolume arrayID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current SisypheVolumeCollection instance container.
        """
        self._volumes.reverse()

    def append(self, value: SisypheVolume) -> None:
        """
        Append a SisypheVolume element in the current SisypheVolumeCollection instance container.

        Parameters
        ----------
        value : SisypheVolume
            volume to append
        """
        if isinstance(value, SisypheVolume):
            if value.getArrayID() not in self:
                self._volumes.append(value)
                self._verifyHomogeneous(value)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(value)))

    def insert(self, key: int | str | SisypheVolume, value: SisypheVolume) -> None:
        """
         Insert a SisypheVolume element at the position given by the key in the current SisypheVolumeCollection
         instance container.

        Parameters
        ----------
        key : int | str | SisypheVolume
            index, ID, SisypheVolume ID attribute
        value : SisypheVolume
            volume to insert
        """
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
        """
        Remove all elements from the current SisypheVolumeCollection instance container (empty).
        """
        self._volumes.clear()
        self._homogeneous = False

    def sort(self, reverse: bool = False) -> None:
        """
        Sort elements of the current SisypheVolumeCollection instance container. Sorting is based on the name attribute
        of the SisypheVolume elements, in the ascending order.

        Parameters
        ----------
        reverse : bool
            sorting in reverse order
        """
        def _getID(item):
            return item.getArrayID()

        self._volumes.sort(reverse=reverse, key=_getID)

    def copy(self) -> SisypheVolumeCollection:
        """
        Copy the current SisypheVolumeCollection instance container (Shallow copy of elements).

        Returns
        -------
        SisypheVolumeCollection
            Shallow copy of collection elements
        """
        volumes = SisypheVolumeCollection()
        volumes._homogeneous = self._homogeneous
        for vol in self._volumes:
            volumes.append(vol)
        return volumes

    def copyToList(self) -> list[SisypheVolume]:
        """
        Copy the current SisypheVolumeCollection instance container to a list.
        (Shallow copy of elements)

        Returns
        -------
        list[SisypheVolume]
            shallow copy of collection elements
        """
        volumes = self._volumes.copy()
        return volumes

    def copyFromList(self, vols: list[SisypheVolume]) -> None:
        """
        Copy a list of SisypheVolume to the current SisypheVolumeCollection instance container (Shallow copy of image
        array)

        Parameters
        ----------
        vols : list[SisypheVolume]
            list of volumes to copy in collection
        """
        if len(vols) > 0:
            self._volumes = list()
            self._index = 0
            for vol in vols:
                self._volumes.append(vol)
                # < Revision 06/06/2025
                # update homoegeneous attribute
                self._verifyHomogeneous(vol)
                # Revision 06/06/2025 >
        else: raise ValueError('parameter list is empty.')

    # < Revision 22/09/2024
    # add setList method
    def getList(self) -> list[SisypheVolume]:
        """
        Get the list attribute of the current SisypheVolumeCollection instance container (Shallow copy of the elements).

        Returns
        -------
        list[SisypheVolume]
            shallow copy of collection
        """
        return self._volumes
    # Revision 22/09/2024 >

    # < Revision 22/09/2024
    # add setList method
    def setList(self, vols: list[SisypheVolume]):
        """
        Copy a list of SisypheVolume to the current SisypheVolumeCollection instance container (Shallow copy of list).

        Parameters
        ----------
        vols : list[SisypheVolume]
            list of volumes to copy in collection
        """
        self._volumes = vols
        self._index = 0
        # < Revision 06/06/2025
        # update homoegeneous attribute
        n = len(self._volumes)
        if n > 1:
            for i in range(1, n):
                self._verifyHomogeneous(self._volumes[i])
        elif n == 1: self._homogeneous = True
        # Revision 06/06/2025 >
    # Revision 22/09/2024 >

    def copyToMultiComponentSisypheVolume(self) -> SisypheVolume:
        """
        Copy the current SisypheVolumeCollection instance to a multi-component SisypheVolume instance

        Returns
        -------
        SisypheVolume
            multi-component volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                return multiComponentSisypheVolumeFromList(self)
            else: raise ValueError('Collection is not homogeneous for field of view or datatype.')
        else: raise ValueError('Image is empty.')

    def copyToNumpyArray(self, defaultshape: bool = True) -> ndarray:
        """
        Copy the current SisypheVolumeCollection instance to a numpy.ndarray.

        Returns
        -------
        numpy.ndarray
            multi-component numpy array
        """
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

    def resample(self, trf: SisypheTransform,
                 save: bool = True,
                 dialog: bool = False,
                 prefix: str | None = None,
                 suffix: str | None = None,
                 wait: DialogWait | None = None) -> SisypheVolumeCollection:
        """
        Resample all the SisypheVolume images in the current SisypheVolumeCollection instance. The current
        SisypheVolumeCollection instance must be homogeneous (see isHomogeneous() method)

        Parameters
        ----------
        trf : Sisyphe.core.sisypheTransform.SisypheTransform
            geometric transformation to apply
        save : bool
            save resampled images if True (default)
        dialog : bool
            - dialog to choice the resampled image file names, if True
            - addBundle suffix/prefix to the image file names, if False (default)
        prefix : str | None
            file name prefix of the resampled images (default None)
        suffix : str | None
            file name suffix of the resampled images (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheVolumeCollection
            resampled images
        """
        if not self.isEmpty():
            from Sisyphe.core.sisypheTransform import SisypheTransform
            from Sisyphe.core.sisypheTransform import SisypheApplyTransform
            if isinstance(trf, SisypheTransform):
                if self.isHomogeneous():
                    f = SisypheApplyTransform()
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

    def getMeanVolume(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate mean image of the SisypheVolume images in the current SisypheVolumeCollection instance. Process all
        volumes or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            mean volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanmean(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getStdVolume(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate standard deviation image of the SisypheVolume images in the current SisypheVolumeCollection instance.
        Process all volumes or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            std volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanstd(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMedianVolume(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate median image of the SisypheVolume images in the current SisypheVolumeCollection instance. Process all
        volumes or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            median volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanmedian(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getPercentileVolume(self, perc: int = 25, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate percentile image of the SisypheVolume images in the current SisypheVolumeCollection instance. Process
        all volumes or a subset selected by indices.

        Parameters
        ----------
        perc : int
            percentile value (default 25, first quartile)
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            percentile volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanpercentile(stack(l), perc, axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMaxVolume(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate maximum image of the SisypheVolume images in the current SisypheVolumeCollection instance. Process
        all volumes or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            max volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanmax(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getMinVolume(self, c: list[int] | tuple[int, ...] | slice | None = None) -> SisypheVolume:
        """
        Calculate minimum image of the SisypheVolume images in the current SisypheVolumeCollection instance. Process
        all volumes or a subset selected by indices.

        Parameters
        ----------
        c : int | list[int] | tuple[int, ...] | slice | None
            volume indices
                - list[int]: list of indices
                - tuple[int, ...]: tuple of indices
                - slice: slice of indices (start:end:step)
                - None: no selection, all volumes are processed

        Returns
        -------
        SisypheVolume
            min volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # < Revision 20/12/2024
                # add subset selected by indices
                # for v in self:
                #    l.append(v.getNumpy())
                if c is None: idx = list(range(self.count()))
                elif isinstance(c, (list, tuple)): idx = c
                elif isinstance(c, slice): idx = list(range(c.start, c.stop, c.step))
                else: raise TypeError('invalid parameter type {}, must be list[int], slice or None.')
                for i in idx:
                    l.append(self._volumes[i].getNumpy())
                # Revision 20/12/2024 >
                img = nanmin(stack(l), axis=0)
                vol = SisypheVolume(img, spacing=self[0].getSpacing())
                vol.copyAttributesFrom(self[0])
                return vol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    def getArgminVolume(self) -> SisypheVolume:
        """
        Calculate argmin image of the SisypheVolume images in the current SisypheVolumeCollection instance. argmin
        returns the image index of the minimum value in the SisypheVolumeCollection instance.

        Returns
        -------
        SisypheVolume
            argmin volume
        """
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
        """
        Calculate argmax image of the SisypheVolume images in the current SisypheVolumeCollection instance. argmax
        returns the image index of the minimum value in the SisypheVolumeCollection instance.

        Returns
        -------
        SisypheVolume
            argmax volume
        """
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
        """
        Copy the current SisypheVolumeCollection instance to a SisypheVolume label instance. Each image of the current
        SisypheVolumeCollection instance is thresholded to get a binary image, this image is multiplied by its index in
        the container to get a label image.

        Parameters
        ----------
        threshold : float
            threshold applied to each image of the current SisypheVolumeCollection instance to get a binary image
            (default 0.5)

        Returns
        -------
        SisypheVolume
            label volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                for v in self:
                    if not v.display.hasZeroOneRange():
                        raise ValueError('Not all volumes have a range between 0.0 and 1.0.')
                r = self[0].getSITKImage() > threshold
                if self.count() > 1:
                    # noinspection PyUnresolvedReferences
                    i: cython.int
                    for i in range(1, self.count()):
                        v = (self[i].getSITKImage() > threshold) * i
                        r = r + v
                r = sitkCast(r, getLibraryDataType('uint8', 'sitk'))
                rvol = SisypheVolume(image=r)
                rvol.copyAttributesFrom(self[0], acquisition=False, display=False, slope=False)
                rvol.acquisition.setModalityToLB()
                rvol.setID(self[0].getID())
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(self.count()):
                    name = self[i].getName()
                    if name == '': name = 'ROI#{}'.format(i + 1)
                    rvol.acquisition.setLabel(i+1, name)
                return rvol
            else: raise ValueError('Collection is not homogeneous.')
        else: raise ValueError('Collection is empty.')

    # < Revision 01/08/2024
    # add labelVotingCombination method
    def labelVotingCombination(self) -> SisypheVolume:
        """
        Performs a pixelwise combination of Labels, where each of them represents a segmentation of the same image.
        Label voting is a simple method of classifier combination applied to image segmentation. Typically, the
        accuracy of the combined segmentation exceeds the accuracy of the input segmentations. Voting is therefore
        commonly used as a way of boosting segmentation performance.

        The use of label voting for combination of multiple segmentations is described in
        T. Rohlfing and C. R. Maurer, Jr., "Multi-classifier framework for atlas-based image segmentation,"
        Pattern Recognition Letters, 2005.

        Returns
        -------
        SisypheVolume
            combined volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(len(self._volumes)):
                    if self._volumes[i].acquisition.isLB(): l.append(self._volumes[i].getSITKImage())
                    else: raise ValueError('{} is not a label image.'.format(self._volumes[i].getBasename()))
                f = sitkComposeImageFilter()
                labels = f.Execute(l)
                img = sitkLabelVoting(labels)
                r = SisypheVolume()
                r.copyFromSITKImage(img)
                r.copyAttributesFrom(self._volumes[0])
                r.copyFilenameFrom(self._volumes[0])
                r.setFilenamePrefix('voting')
                return r
            else: raise AttributeError('Collection is not homogeneous.')
        else: raise AttributeError('Collection is empty.')
    # Revision 01/08/2024 >

    # < Revision 01/08/2024
    # add labelSTAPLECombination method
    def labelSTAPLECombination(self) -> SisypheVolume:
        """
        Performs a pixelwise combination of Labels, where each of them represents a segmentation of the same image.
        The labelings are weighted relative to each other based on their "performance" as estimated by an
        expectation-maximization algorithm. In the process, a ground truth segmentation is estimated,
        and the estimated performances of the individual segmentations are relative to this estimated ground truth.

        The algorithm is based on the binary STAPLE algorithm by Warfield et al. :
        S. Warfield, K. Zou, W. Wells, "Validation of image segmentation and expert quality with an
        expectation-maximization algorithm" in MICCAI 2002: Fifth International Conference on Medical Image Computing
        and Computer-Assisted Intervention, Springer-Verlag, Heidelberg, Germany, 2002, pp. 298-306

        Returns
        -------
        SisypheVolume
            combined volume
        """
        if not self.isEmpty():
            if self.isHomogeneous():
                l = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(len(self._volumes)):
                    if self._volumes[i].acquisition.isLB(): l.append(self._volumes[i].getSITKImage())
                    else: raise ValueError('{} is not a label image.'.format(self._volumes[i].getBasename()))
                f = sitkComposeImageFilter()
                labels = f.Execute(l)
                img = sitkLabelVoting(labels)
                r = SisypheVolume()
                r.copyFromSITKImage(img)
                r.copyAttributesFrom(self._volumes[0])
                r.copyFilenameFrom(self._volumes[0])
                r.setFilenamePrefix('staple')
                return r
            else: raise AttributeError('Collection is not homogeneous.')
        else: raise AttributeError('Collection is empty.')
    # Revision 01/08/2024 >

    # Descriptive statistics public methods

    def getValuesInsideMask(self, mask: SisypheImage) -> list[ndarray]:
        """
        Get scalar values inside a mask of the SisypheVolume images in the current SisypheVolumeCollection instance.
        The current SisypheVolumeCollection instance must be homogeneous (see isHomogeneous() method)

        Parameters
        ----------
        mask : Sisyphe.core.sisypheImage.SisypheImage

        Returns
        -------
        numpy.ndarray | list[float]
            values inside mask
        """
        if not self.isEmpty():
            if isinstance(mask, SisypheImage):
                r = list()
                m = mask.getNumpy() > 0.0
                for v in self:
                    img = v.getNumpy()
                    # noinspection PyUnresolvedReferences
                    img = img[m]
                    r.append(img)
                return r
            else: raise TypeError('parameter type {} is not SisypheImage.'.format(type(mask)))
        else: raise TypeError('image is empty.')

    def getValuesAt(self, x: int, y: int, z: int, asnumpy: bool = False) -> list[float] | ndarray:
        """
        Get scalar values in a voxel of the SisypheVolume images in the current SisypheVolumeCollection instance. The
        current SisypheVolumeCollection instance must be homogeneous (see isHomogeneous() method)

        Parameters
        ----------
        x : int
            x-axis voxel coordinate
        y : int
            y-axis voxel coordinate
        z : int
            z-axis voxel coordinate
        asnumpy : bool
            returns numpy.ndarray if True, list[float] otherwise (default False)

        Returns
        -------
        numpy.ndarray | list[float]
            volues at voxel (x, y, z)
        """
        if not self.isEmpty():
            r = [v[x, y, z] for v in self]
            if asnumpy: r = array(r)
            return r
        else: raise TypeError('image is empty.')

    getVector = getValuesAt

    # IO Public methods

    def load(self, filenames: str | list[str]) -> None:
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of PySisyphe
        volume (.xvol) file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of PySisyphe Volume (.xvol) file names
        """
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
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of old
        Sisyphe volume (.vol) file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of old Sisyphe Volume (.vol) file names
        """
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
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of Nifti file
        names.

        Parameters
        ----------
        filenames : str | list[str]
            list of Nifti file names
        """
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
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of Nrrd file
        names.

        Parameters
        ----------
        filenames : str | list[str]
            list of Nrrd file names
        """
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
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of Minc file
        names.

        Parameters
        ----------
        filenames : str | list[str]
            list of Minc file names
        """
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
        """
        Load SisypheVolume elements in the current SisypheVolumeCollection instance container from a list of VTK file
        names.

        Parameters
        ----------
        filenames : str | list[str]
            list of VTK file names
        """
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
        """
        Iteratively save SisypheVolume elements in the current SisypheVolumeCollection instance container.
        """
        if not self.isEmpty():
            for vol in self:
                if vol.hasFilename(): vol.save()

    def saveToMulticomponentVolume(self, filename: str, copyattr: bool | dict[str: bool] = False) -> None:
        """
        Save SisypheVolume elements of the current SisypheVolumeCollection instance container to a multi-component
        SisypheVolume.

        Parameters
        ----------
        filename : str
            file name
        copyattr : bool | dict[str: bool]
            - bool: copy all attributes if True (default False)
            - or dict, keys
                - 'ID': bool, copy ID attribute if True
                - 'identity': bool, copy identity attribute if True
                - 'acquisition': bool, copy acquisition attribute if True
                - 'display': bool, copy display attribute if True
                - 'acpc': bool, copy acpc attribute if True
                - 'transform': bool, copy transform attribute if True
                - 'slope': bool, copy slope/intercept attributes if True
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
