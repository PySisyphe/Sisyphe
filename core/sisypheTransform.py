"""
External packages/modules
-------------------------

    - ANTs, image registration, http://stnava.github.io/ANTs/
    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - NiBabel, Euler angle conversions, https://nipy.org/nibabel
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - Scipy, scientific computing, https://docs.scipy.org/doc/scipy/index.html
    - SimpleITK, medical image processing, https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import splitext
from os.path import split
from os.path import join

from math import radians
from math import degrees

from xml.dom import minidom

from numpy import array
from numpy import ndarray
from numpy import identity
from numpy import matmul
from numpy import diag
from numpy import allclose
from numpy.linalg import inv

from nibabel.quaternions import quat2angle_axis
from nibabel.quaternions import angle_axis2quat
from nibabel.quaternions import quat2mat
from nibabel.quaternions import mat2quat

from scipy.linalg import det
from scipy.linalg import cholesky
from scipy.linalg import solve

from vtk import vtkMatrix3x3
from vtk import vtkMatrix4x4
from vtk import vtkTransform
from vtk import vtkMNITransformReader
from vtk import vtkMNITransformWriter

from SimpleITK import Cast
from SimpleITK import sitkVectorFloat32
from SimpleITK import sitkVectorFloat64
from SimpleITK import Image as sitkImage
from SimpleITK import sitkLinear
from SimpleITK import sitkBSpline
from SimpleITK import sitkGaussian
from SimpleITK import sitkHammingWindowedSinc
from SimpleITK import sitkCosineWindowedSinc
from SimpleITK import sitkWelchWindowedSinc
from SimpleITK import sitkLanczosWindowedSinc
from SimpleITK import sitkBlackmanWindowedSinc
from SimpleITK import sitkNearestNeighbor
from SimpleITK import Transform as sitkTransform
from SimpleITK import AffineTransform as sitkAffineTransform
from SimpleITK import VersorTransform as sitkVersorTransform
from SimpleITK import Euler3DTransform as sitkEuler3DTransform
from SimpleITK import DisplacementFieldTransform as sitkDisplacementFieldTransform
from SimpleITK import ReadTransform as sitkReadTransform
from SimpleITK import TransformToDisplacementFieldFilter as sitkTransformToDisplacementFieldFilter
from SimpleITK import ResampleImageFilter as sitkResampleImageFilter

from ants.core.ants_transform import ANTsTransform
from ants.core.ants_transform_io import read_transform
from ants.core.ants_transform_io import write_transform
from ants.core.ants_transform_io import transform_from_displacement_field

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.lib.bv.trf import read_trf
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImage import SisypheBinaryImage
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    pass


__all__ = ['SisypheTransform',
           'SisypheApplyTransform',
           'SisypheTransformCollection',
           'SisypheTransforms']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheTransform
             -> SisypheApplyTransform
             -> SisypheTransformCollection
             -> SisypheTransformCollection -> SisypheTransforms
"""

listFloat = list[float]
tupleFloat3 = tuple[float, float, float]
vectorFloat3 = listFloat | tupleFloat3
tupleFloat4 = tuple[float, float, float, float]
vectorFloat4 = listFloat | tupleFloat4
listInt = list[int]
tupleInt3 = tuple[int, int, int]
vectorInt3 = listInt | tupleInt3


class SisypheTransform(object):
    """
    Description
    ~~~~~~~~~~~

    PySisyphe geometric centered transformation class.

    Uses forward convention, i.e. transformation of fixed to floating volume coordinates. To resample floating volume,
    apply the inverse i.e. backward transformation. Private attributes ID, spacing and size are those of the fixed
    image (resampling space)

    Fixed and floating volumes are associated with instance attributes:

        - Parent attribute = fixed volume.
        - ID attribute = ID of the floating volume

    Methods to copy to/from ANTs, SimpleITK and VTK geometric transformation classes.
    IO methods for common neuroimaging geometric transformation file formats.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTransform

    Creation: 05/10/2021
    Last revision: 19/03/2025
    """
    __slots__ = ['_parent', '_name', '_ID', '_size', '_spacing', '_transform', '_field', '_fieldname']

    # Class constant

    _FILEEXT = '.xtrf'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheTransform file extension.

        Returns
        -------
        str
            '.xtrf'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheTransform filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Geometric transformation (.xtrf)'
        """
        return 'PySisyphe Geometric transformation (*{})'.format(cls._FILEEXT)

    @classmethod
    def getSITKtoNumpy(cls, trf: sitkAffineTransform | sitkEuler3DTransform) -> ndarray:
        """
        Convert SimpleITK.AffineTransform or SimpleITK.Euler3DTransform o a numpy.ndarray.

        Parameters
        ----------
        trf : SimpleITK.AffineTransform | SimpleITK.Euler3DTransform

        Returns
        -------
        numpy.ndarray
            homogeneous affine matrix
        """
        if isinstance(trf, (sitkAffineTransform, sitkEuler3DTransform)):
            m = list(trf.GetMatrix())
            t = list(trf.GetTranslation())
            m = m[:3] + [t[0]] + m[3:6] + [t[1]] + m[-3:] + [t[2], 0.0, 0.0, 0.0, 1.0]
            return array(m).reshape(4, 4)
        else: raise TypeError('parameter type {} is not sitkAffineTransform or sitkEuler3DTransform.'.format(type(trf)))

    @classmethod
    def getVTKtoNumpy(cls, trf: vtkMatrix4x4) -> ndarray:
        """
        Convert a vtk.vtkMatrix4x4 to a numpy.ndarray.

        Parameters
        ----------
        trf : vtk.vtkMatrix4x4

        Returns
        -------
        numpy.ndarray
            homogeneous affine matrix
        """
        if isinstance(trf, vtkMatrix4x4):
            m = ndarray((4, 4))
            # < Revision 21/07/2024
            # for r in range(3):
            #     for c in range(3):
            # bugfix, replace range(3) by range(4)
            for r in range(4):
                for c in range(4):
                    m[r, c] = trf.GetElement(r, c)
            # Revision 21/07/2024 >
            return m
        else: raise TypeError('parameter type {} is not vtkMatrix4x4.'.format(type(trf)))

    @classmethod
    def openTransform(cls, filename: str) -> SisypheTransform:
        """
        create a SisypheTransform instance from PySisyphe geometric transformation file (.xtrf).

        Parameters
        ----------
        filename : str
            geometric transformation file name

        Returns
        -------
        SisypheTransform
            loaded geometric transform
        """
        filename = basename(filename) + cls.getFileExt()
        trf = SisypheTransform()
        trf.load(filename)
        return trf

    # Special methods

    """
    Private attributes

    _parent     SisypheVolume, reference volume
    _ID         str, ID of floating image,  fixed volume ID
    _name       str
    _size       tuple[int, int, int], fixed volume size
    _spacing    tuple[float, float, float], fixed volume spacing
    _transform  sitkAffineTransform, backward transformation, fixed coordinates to moving coordinates
    _affine     sitkScaleSkewVersor3DTransform
    _field      sitkDisplacementFieldTransform
    _fieldname  str    
    """

    def __init__(self, parent: SisypheVolume | None = None) -> None:
        """
        SisypheTransform instance constructor

        Parameters
        ----------
        parent : Sisyphe.core.sisypheVolume.SisypheVolume | None
            reference volume (default None)
        """
        self._transform = sitkAffineTransform(3)
        self._field = None
        self._fieldname = ''
        if parent and isinstance(parent, SisypheVolume):
            self._ID = parent.getID()
            self._name = parent.getName()
            self._size = parent.getSize()
            self._spacing = parent.getSpacing()
            self._transform.SetCenter(parent.getCenter())
        else:
            self._ID = ''  # moving SisypheVolume ID
            self._name = ''
            self._size = (0, 0, 0)
            self._spacing = (0.0, 0.0, 0.0)
            self.setCenter((0.0, 0.0, 0.0))
        self._parent = parent

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheTransform instance to str
        """
        buff = 'ID: {}\n'.format(self.getID())
        buff += 'Name: {}\n'.format(self.getName())
        buff += 'Size: {}\n'.format(self.getSize())
        p = self.getSpacing()
        buff += 'Spacing: [{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}]\n'.format(p=p)
        p = self.getCenter()
        buff += 'Center: [{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}]\n'.format(p=p)
        if self._field is None:
            r = self.isRigid()
            if r: buff += 'Rigid transform\n'
            else: buff += 'Affine transform\n'
            p = self.getTranslations()
            buff += '  Translations: [{p[0]:.1f} {p[1]:.1f} {p[2]:.1f}]\n'.format(p=p)
            # < Revision 07/09/2024
            if self.hasCenter():
                buff += '  Offsets: [{p[0]:.1f} {p[1]:.1f} {p[2]:.1f}]\n'.format(p=self.getOffsets())
            # Revision 07/09/2024 >
            if r:
                p = self.getRotations()
                buff += '  Rotations: \n'
                buff += '    radians [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]\n'.format(p=p)
                p = [degrees(i) for i in p]
                buff += '    degrees [{p[0]:.1f} {p[1]:.1f} {p[2]:.1f}]\n'.format(p=p)
                p = self.getVersor()
                buff += '    versor [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f} {p[3]:.3f}]\n'.format(p=p)
                a, p = self.getAngleVector()
                buff += '    vector [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}] angle {a:.3f}\n'.format(p=p, a=a)
            else:
                try:
                    p = self.getAffineParametersFromMatrix()
                    pr = p[1]
                    pz = p[2]
                    ps = p[3]
                    buff += '  Rotations: \n'
                    buff += '    radians [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]\n'.format(p=pr)
                    pr = [degrees(i) for i in pr]
                    buff += '    degrees [{p[0]:.1f} {p[1]:.1f} {p[2]:.1f}]\n'.format(p=pr)
                    buff += '  Zooms: [{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}]\n'.format(p=pz)
                    buff += '  Shears: [{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}]\n'.format(p=ps)
                except: buff += 'Non-orthogonal transform\n'
            buff += '  Matrix:\n'
            m = self._transform.GetMatrix()
            p = m[:3]
            buff += '    [{p[0]:7.4f} {p[1]:7.4f} {p[2]:7.4f} ]\n'.format(p=p)
            p = m[3:6]
            buff += '    [{p[0]:7.4f} {p[1]:7.4f} {p[2]:7.4f} ]\n'.format(p=p)
            p = m[-3:]
            buff += '    [{p[0]:7.4f} {p[1]:7.4f} {p[2]:7.4f} ]\n'.format(p=p)
        else:
            buff += 'Displacement Field transform\n'
            if self._fieldname == '': name = 'Not yet saved'
            else: name = self._fieldname
            buff += '  Filename: {}\n'.format(name)
        buff += 'Memory size: {} Bytes\n'.format(self.__sizeof__())
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTransform instance representation
        """
        return 'SisypheTransform instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def hasParent(self) -> bool:
        """
        Check if the parent attribute of the current SisypheTransform instance is defined (not None).

        Returns
        -------
        bool
            True if parent attribute is defined
        """
        return self._parent is not None

    def getParent(self) -> SisypheVolume | None:
        """
        Get the parent attribute of the current SisypheTransform instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            parent
        """
        return self._parent

    def setParent(self, parent: SisypheVolume) -> None:
        """
        Set the parent attribute of the current SisypheTransform instance.

        Parameters
        ----------
        parent : Sisyphe.core.sisypheVolume.SisypheVolume
            parent volume
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if parent and isinstance(parent, SisypheVolume):
            self.setID(parent)
            self._size = parent.getSize()
            self._spacing = parent.getSpacing()
            self._transform.SetCenter(parent.getCenter())

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current SisypheTransform instance.

        Parameters
        ----------
        name : str
            transform name
        """
        self._name = splitext(basename(name))[0]

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheTransform instance.

        Returns
        -------
        str
            transform name
        """
        return self._name

    def hasName(self) -> bool:
        """
        Check if the name attribute of the current SisypheTransform instance is defined (not '').

        Returns
        -------
        bool
            True if name attribute is defined
        """
        return self._name != ''

    def setIdentity(self) -> None:
        """
        Clear the current SisypheTransform instance (set geometric transformation to identity).
        """
        # Copy center
        c = self._transform.GetCenter()
        # SetIdentity clear center
        self._transform.SetIdentity()
        # Set center
        self._transform.SetCenter(c)

    def isIdentity(self) -> bool:
        """
        Check if the current SisypheTransform instance is an identity geometric transformation.

        Returns
        -------
        bool
            True if identity geometric transformation
        """
        if self._field is None:
            return self._transform.GetMatrix() == (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0) and \
                   self._transform.GetTranslation() == (0.0, 0.0, 0.0)
        else: raise TypeError('Displacement field transform.')

    def getInverseTransform(self) -> SisypheTransform:
        """
        Get the inverse geometric transformation of the current SisypheTransform instance.

        Returns
        -------
        SisypheTransform
            inverse geometric transformation
        """
        if self._field is None:
            trf = SisypheTransform()
            trf.setSITKTransform(sitkAffineTransform(self._transform.GetInverse()))
            trf.setID(self.getID())
            trf.setSize(self.getSize())
            trf.setSpacing(self.getSpacing())
            return trf
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setTranslations(self, t: vectorFloat3) -> None:
        """
        Set translation attributes of the current SisypheTransform instance.

        Parameters
        ----------
        t : tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis translations in mm
        """
        if self._field is None: self._transform.SetTranslation(t)
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setRotations(self, r: vectorFloat3, deg: bool = False) -> None:
        """
        Set rotation attributes of the current SisypheTransform instance. The order in which rotations are applied is
        x-axis, then y-axis and finally z-axis.

        Parameters
        ----------
        r : tuple[float, float, float] | list[float]
            rotations around x-axis, y-axis and z-axis
        deg : bool
            rotations in degrees if True, in radians otherwise (default False)
        """
        if self._field is None:
            r = list(r)
            if deg:
                r[0] = radians(r[0])
                r[1] = radians(r[1])
                r[2] = radians(r[2])
            t = sitkEuler3DTransform()
            t.SetRotation(r[0], r[1], r[2])
            self._transform.SetMatrix(t.GetMatrix())
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setVersor(self, v: vectorFloat4) -> None:
        """
        Set rotation attributes of the current SisypheTransform instance from a versor i.e. quaternion in w, x, y, z
        (i.e. real, then unit vector in 3D).

        Parameters
        ----------
        v : tuple[float, float, float, float] | list[float]
            versor
        """
        if self._field is None:
            t = sitkVersorTransform()
            t.SetRotation(v)
            self._transform.SetMatrix(t.GetMatrix())
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setAngleVector(self, a: float, v: vectorFloat3, deg: bool = False) -> None:
        """
        Set rotation attributes of the current SisypheTransform instance from a vector of rotation axis and an angle.
        Rotation matrix is processed from the Rodrigues’ formula.

        Parameters
        ----------
        a : float
            angle of rotation
        v : tuple[float, float, float] | list[float]
            vector of rotation axis
        deg : bool
            angle in radians if False, in degrees otherwise
        """
        if self._field is None:
            if deg: a = radians(a)
            q = angle_axis2quat(a, v)
            R = quat2mat(q)
            self._transform.SetMatrix(R.flatten())
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setAffineParameters(self,
                            t: vectorFloat3 | None = None,
                            r: vectorFloat3 | None = None,
                            z: vectorFloat3 | None = None,
                            s: vectorFloat3 | None = None,
                            deg: bool = False) -> None:
        """
        Set affine parameters i.e. translations, rotations, zooms and shears of the current SisypheTransform instance.

        Parameters
        ----------
        t : tuple[float, float, float] | list[float]
            translations in x-axis, y-axis and z-axis
        r : tuple[float, float, float] | list[float]
            rotations around x-axis, y-axis and z-axis
        z : tuple[float, float, float] | list[float]
            zoom factors applied to x-axis, y-axis and z-axis
        s : tuple[float, float, float] | list[float]
            shear factors for x-y, x-z, y-z axes
        deg : bool
            angle in radians if False, in degrees otherwise
        """
        if self._field is None:
            self.setIdentity()
            if t is not None: self.setTranslations(t)
            if r is not None: self.setRotations(r, deg)
            if s is not None:
                M = identity(3)
                M[0, 1] = s[0]
                M[0, 2] = s[1]
                M[1, 2] = s[2]
                M = matmul(self.getNumpyArray(), M)
                self._transform.SetMatrix(M.flatten())
            if z is not None:
                M = identity(3)
                M[0, 0] = z[0]
                M[1, 1] = z[1]
                M[2, 2] = z[2]
                M = matmul(self.getNumpyArray(), M)
                self._transform.SetMatrix(M.flatten())
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def addTranslations(self, t: vectorFloat3) -> None:
        """
        Add translations to the current SisypheTransform instance.

        Parameters
        ----------
        t : tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis translations in mm
        """
        if self._field is None:
            t2 = list(self.getTranslations())
            t2[0] += t[0]
            t2[1] += t[1]
            t2[2] += t[2]
            self.setTranslations(t2)
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def composeRotations(self, r: vectorFloat3, deg: bool = False) -> None:
        """
        Compose rotations to the current SisypheTransform instance.

        Parameters
        ----------
        r : tuple[float, float, float] | list[float]
            rotations around x-axis, y-axis and z-axis
        deg : bool
            rotations in degrees if True, in radians otherwise (default False)
        """
        if self._field is None:
            trf = SisypheTransform()
            trf.setRotations(r, deg)
            self.preMultiply(trf, homogeneous=True)
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def composeTransform(self, trf: SisypheTransform) -> None:
        """
        Compose a geometric transformation (SisypheTransform) to the current SisypheTransform instance.

        Parameters
        ----------
        trf : SisypheTransform
            geometric transformation to compose
        """
        if self._field is None:
            if isinstance(trf, SisypheTransform):
                self.preMultiply(trf, homogeneous=True)
            else: raise TypeError('parameter type {} is not SisypheTransform'.format(trf))
        else: raise TypeError('Displacement field transform has no affine matrix parameter.')

    def getTranslations(self) -> listFloat:
        """
        Get translation attributes of the current SisypheTransform instance.

        Returns
        -------
        tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis translations in mm
        """
        return list(self._transform.GetTranslation())

    # < Revision 07/09/2024
    # add getOffsets method
    def getOffsets(self) -> listFloat:
        """
        Get offsets of the current SisypheTransform instance. if center of rotation is default (0.0, 0.0, 0.0),
        offsets are equal to translations. However, if center of rotation is not default, offsets are translations
        of an equivalent geometric transformation with a default center of rotation.

        Returns
        -------
        tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis translations in mm
        """
        if self.hasCenter():
            trf = self.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
            return trf.getTranslations()
        else: return self.getTranslations()
    # Revision 07/09/2024 >

    def getRotations(self, deg: bool = False) -> listFloat | None:
        """
        Get rotation attributes of the current SisypheTransform instance.

        Parameters
        ----------
        deg : bool, rotations in degrees if True, in radians otherwise (default False)

        Returns
        -------
        list[float]
            rotations around x-axis, y-axis and z-axis
        """
        if self._field is None:
            t = sitkEuler3DTransform()
            try: t.SetMatrix(self._transform.GetMatrix())
            except: return self.getRotationsFromMatrix(deg)
            if deg: return [degrees(t.GetAngleX()), degrees(t.GetAngleY()), degrees(t.GetAngleZ())]
            else: return [t.GetAngleX(), t.GetAngleY(), t.GetAngleZ()]
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def getRotationsFromMatrix(self, deg: bool = False) -> listFloat:
        """
        Get rotations from the affine matrix attribute of the current SisypheTransform instance.

        Parameters
        ----------
        deg : bool
            rotations in degrees if True, in radians otherwise (default False)

        Returns
        -------
        list[float]
            rotations around x-axis, y-axis and z-axis
        """
        if self._field is None:
            # < Revision 08/09/2024
            # return self.getAffineParametersFromMatrix(deg)[2]
            return self.getAffineParametersFromMatrix(deg)[1]
            # Revision 08/09/2024 >
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def getVersor(self) -> listFloat:
        """
        Get versor i.e. quaternion in w, x, y, z (real, then unit vector in 3D) from the rotation attributes of the
        current SisypheTransform instance.

        Returns
        -------
        tuple[float, float, float, float] | list[float]
            versor
        """
        if self._field is None:
            t = sitkVersorTransform()
            t.SetMatrix(self._transform.GetMatrix())
            return list(t.GetVersor())
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def getAngleVector(self, deg: bool = False) -> tuple[float, listFloat]:
        """
        Get angle and vector of rotation axis from the rotations of the current SisypheTransform instance.

        Parameters
        ----------
        deg : bool
            angle in radians if False, in degrees otherwise

        Returns
        -------
        float, tuple[float, float, float] | list[float]
            angle of rotation and vector of rotation axis
        """
        if self._field is None:
            M = self.getNumpyArray()
            q = mat2quat(M)
            a, v = quat2angle_axis(q)
            if deg: a = degrees(a)
            return a, list(v)
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def getAffineParametersFromMatrix(self, deg: bool = False) -> tuple[listFloat, listFloat, listFloat, listFloat]:
        """
        Get affine parameters from the affine matrix attribute of the current SisypheTransform instance.

        Parameters
        ----------
        deg : bool
            rotations in degrees if True, in radians otherwise (default False)

        Returns
        -------
        tuple[list[float], list[float], list[float], list[float]]
            - translations in x-axis, y-axis and z-axis
            - rotations around x-axis, y-axis and z-axis
            - zoom factors applied to x-axis, y-axis and z-axis
            - shear factors for x-y, x-z, y-z axes
        """
        if self._field is None:
            # retrieve zooms
            r = self.getNumpyArray()
            C = cholesky(r.T @ r)
            z = diag(C)
            if det(r) < 0: z[0] = -z[0]
            Z = diag(z)
            # retrieve shears
            C = solve(diag(diag(C)), C)
            # finally, retrieve rotations
            R0 = Z @ C
            R1 = solve(r.T, R0.T)
            t = sitkEuler3DTransform()
            t.SetMatrix(R1.flatten())
            r1 = t.GetAngleX()
            r2 = t.GetAngleY()
            r3 = t.GetAngleZ()
            if deg:
                r1 = degrees(r1)
                r2 = degrees(r2)
                r3 = degrees(r3)
            return self.getTranslations(), [r1, r2, r3], list(diag(Z)), [C[0, 1], C[0, 2], C[1, 2]]
        else: raise TypeError('Displacement field transform has no affine attribute.')

    def setCenter(self, c: vectorFloat3) -> None:
        """
        Set the center of rotation of the current SisypheTransform instance.

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            center of rotation coordinates
        """
        self._transform.SetCenter(c)

    # < Revision 03/09/2024
    # add removeCenter method
    def removeCenter(self) -> None:
        """
        Set the center of rotation of the current SisypheTransform instance to [0.0, 0.0, 0.0]
        """
        self._transform.SetCenter([0.0, 0.0, 0.0])
    # Revision 03/09/2024 >

    def getEquivalentTransformWithNewCenterOfRotation(self, c: vectorFloat3) -> SisypheTransform:
        """
        Calculate a geometric transformation equivalent to the current SisypheTransform instance, with a new center
        of rotation

        1. Apply forward translation, old center to new center (translation = volume center - old center)
        2. Apply rotation, after forward translation, center of rotation is new center
        3. Apply backward translation, new center to old center

        Parameters
        ----------
        c : tuple[float, float, float] | list[float]
            new center of rotation coordinates

        Returns
        -------
        SisypheTransform
        """
        if self.getCenter() != list(c):
            newc = list(c)
            oldc = self.getCenter()
            newc[0] -= oldc[0]
            newc[1] -= oldc[1]
            newc[2] -= oldc[2]
            """
                t1 = forward translation transformation matrix
                forward translation of the center of rotation from old center to new center
                translation = new center (c) - old center (m)
            """
            t1 = SisypheTransform()
            t1.setTranslations(newc)
            """
                rt2 = roto-translation matrix = backward translation transformation x rotation transformation
                backward translation from new center to old center
                backward translation = - forward translation
                Order of transformations is 1. rotation -> 2. backward translation
            """
            rt2 = SisypheTransform()
            # < Revision 08/09/2024
            # copy matrix instead of rotations
            # rt2.setRotations(self.getRotations())
            rt2.setNumpyArray(self.getNumpyArray())
            # Revision 08/09/2024 >
            oldtrans = list(self.getTranslations())
            # Keep previous translations (oldtrans),
            # integrated in roto-translation matrix (added to backward translation)
            # translation = old translation + backward translation (-newc)
            oldtrans[0] -= newc[0]
            oldtrans[1] -= newc[1]
            oldtrans[2] -= newc[2]
            rt2.setTranslations(oldtrans)
            """
                final transformation = t1 x rt2
                Order of transformations (inverse of the matrix product order) is
                1. forward translation -> 2. rotation -> 3. backward translation
            """
            t1.preMultiply(rt2, homogeneous=True)
            t1.setCenter(c)
            t1.setID(self.getID())
            t1.setSize(self.getSize())
            t1.setSpacing(self.getSpacing())
            t1.setName(self.getName())
            return t1
        else:
            t = self.copy()
            return t

    def setCenterFromSisypheVolume(self, vol: SisypheVolume) -> None:
        """
        Set the center of rotation of the current SisypheTransform instance to the center of a SisypheVolume image.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            center of rotation = volume center
        """
        if isinstance(vol, SisypheVolume): self._transform.SetCenter(vol.getCenter())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def isCenteredToSisypheVolume(self, vol: SisypheVolume) -> bool:
        """
        Check whether the center of rotation of the current SisypheTransform instance is the center of a SisypheVolume
        image.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume center used as center of rotation

        Returns
        -------
        bool
            True if center of rotation = volume center
        """
        if isinstance(vol, SisypheVolume):
            c1 = self.getCenter()
            c2 = list(vol.getCenter())
            return c1 == c2
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setCenterFromParent(self) -> None:
        """
        Set the center of rotation of the current SisypheTransform instance to the center of the SisypheVolume parent
        attribute.
        """
        if self.hasParent():
            self.setCenterFromSisypheVolume(self._parent)

    def isCenteredFromParent(self) -> bool:
        """
        Check whether the center of rotation of the current SisypheTransform instance is the center of the
        SisypheVolume parent attribute.

        Returns
        -------
        bool
            True if center of rotation = parent volume center
        """
        if self.hasParent():
            return self.isCenteredToSisypheVolume(self._parent)
        else: raise AttributeError('SisypheVolume parent attribute is None.')

    def getCenter(self) -> listFloat:
        """
        Get the center of rotation of the current SisypheTransform instance.

        Returns
        -------
        list[float]
            center of rotation coordinates
        """
        return list(self._transform.GetCenter())

    def hasCenter(self) -> bool:
        """
        Check whether the center of rotation of the current SisypheTransform instance is defined (not 0.0, 0.0, 0.0).

        Returns
        -------
        bool
            True if center is defined (not 0.0, 0.0, 0.0)
        """
        return self._transform.GetCenter() != (0.0, 0.0, 0.0)

    def copyFrom(self, t: SisypheTransform) -> None:
        """
        Copy a SisypheTransform instance to the current SisypheTransform instance.

        Parameters
        ----------
        t : SisypheTransform
            geometric transform
        """
        if isinstance(t, SisypheTransform):
            if t.isDisplacementField():
                self._field = sitkDisplacementFieldTransform()
                self._field.SetInterpolator(sitkLinear)
                self._field.SetDisplacementField(t.getSITKDisplacementFieldSITKImage())
            else:
                self.removeDisplacementField()
                self.setID(t.getID())
                self.setName(t.getName())
                self.setSize(t.getSize())
                self.setSpacing(t.getSpacing())
                self.setCenter(t.getCenter())
                self.setIdentity()
                self._transform.SetTranslation(t.getTranslations())
                self._transform.SetMatrix(t.getSITKTransform().GetMatrix())
        else: raise TypeError('parameter type {} is not SisypheTransform or SisypheVolume.'.format(type(t)))

    def copyTo(self, t: SisypheTransform) -> None:
        """
        Copy the current SisypheTransform instance to a SisypheTransform instance.

        Parameters
        ----------
        t : SisypheTransform
            transform copy
        """
        if isinstance(t, SisypheTransform):
            if self._field is None:
                t.removeDisplacementField()
                t.setIdentity()
                t.setID(self.getID())
                t.setName(self.getName())
                t.setSize(self.getSize())
                t.setSpacing(self.getSpacing())
                t.setCenter(self.getCenter())
                t.setTranslations(self._transform.GetTranslation())
                t.getSITKTransform().SetMatrix(self._transform.GetMatrix())
            else:
                f = sitkDisplacementFieldTransform()
                f.SetInterpolator(sitkLinear)
                f.SetDisplacementField(self.getSITKDisplacementFieldSITKImage())
                t.setSITKDisplacementFieldTransform(f)
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(t)))

    def copy(self) -> SisypheTransform:
        """
        Copy the current SisypheTransform instance.

        Returns
        -------
        SisypheTransform
            transform copy
        """
        t = SisypheTransform()
        self.copyTo(t)
        return t

    def setSITKTransform(self, trf):
        """
        Copy a SimpleITK.Transform instance to the current SisypheTransform instance.

        Parameters
        ----------
        trf : SimpleITK.TranslationTransform | SimpleITK.VersorTransform | SimpleITK.ScaleTransform | SimpleITK.VersorRigid3DTransform | SimpleITK.Euler3DTransform | SimpleITK.Similarity3DTransform | SimpleITK.ScaleVersor3DTransform | SimpleITK.ScaleSkewVersor3DTransform | SimpleITK.AffineTransform | SimpleITK.DisplacementFieldTransform
            SimpleITK geometric transform
        """
        name = trf.GetName()
        if name != 'DisplacementFieldTransform':
            self.setIdentity()
            if name == 'TranslationTransform':
                self._transform.SetTranslation(trf.GetOffset())
            elif name == 'VersorTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'VersorRigid3DTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'Euler3DTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'Similarity3DTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleVersor3DTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleSkewVersor3DTransform':
                # < Revision 06/09/2024
                self._transform.SetCenter(trf.GetCenter())
                # Revision 06/09/2024 >
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'AffineTransform':
                self._transform = trf
            else: raise TypeError('transform type {} is not supported.'.format(type(trf)))
        else: self.setSITKDisplacementFieldTransform(trf)

    def getSITKTransform(self) -> sitkAffineTransform | sitkDisplacementFieldTransform:
        """
        Get a SimpleITK.Transform instance from the current SisypheTransform instance.

        Returns
        -------
        SimpleITK.AffineTransform | SimpleITK.DisplacementFieldTransform
            transform copy
        """
        if self._field is None: return self._transform
        else: return self._field

    def getSITKDisplacementFieldTransform(self) -> sitkDisplacementFieldTransform:
        """
        Get a SimpleITK.DisplacementFieldTransform instance from the current SisypheTransform instance.

        Returns
        -------
        SimpleITK.DisplacementFieldTransform
            displacement field transform copy
        """
        if self._field is not None: return self._field
        else: raise ValueError('No displacement field transform.')

    def getSITKDisplacementFieldSITKImage(self) -> sitkImage:
        """
        Get a SimpleITK.Image instance from the displacement field of the current SisypheTransform instance.

        Returns
        -------
        SimpleITK.Image
            displacement field image
        """
        if self._field is not None: return self._field.GetDisplacementField()
        else: raise AttributeError('Displacement field attribute is None.')

    def getDisplacementField(self) -> SisypheVolume:
        """
        Get the displacement field of the current SisypheTransform instance as SisypheVolume.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            displacement field image
        """
        if self._field is not None:
            field = SisypheVolume()
            field.setSITKImage(self._field.GetDisplacementField())
            field.getAcquisition().setSequenceToDisplacementField()
            return field
        else: raise AttributeError('Displacement field attribute is None.')

    def getInverseSITKTransform(self) -> sitkAffineTransform:
        """
        Get inverse of the current SisypheTransform instance as a SimpleITK.Transform instance.

        Returns
        -------
        SimpleITK.AffineTransform
            inverse transform
        """
        if self._field is None: return self._transform.GetInverse()
        else: raise TypeError('No affine transform.')

    def setSITKDisplacementFieldTransform(self, trf: sitkDisplacementFieldTransform) -> None:
        """
        Set a SimpleITK.DisplacementFieldTransform instance to the current SisypheTransform instance.

        Parameters
        ----------
        trf : SimpleITK.DisplacementFieldTransform
            displacement field transform
        """
        if isinstance(trf, sitkDisplacementFieldTransform):
            self._field = trf
            self.setIdentity()
        else: raise TypeError('parameter type {} is not sitkDisplacementFieldTransform.'.format(type(trf)))

    def setSITKDisplacementFieldImage(self, img: SisypheImage | sitkImage) -> None:
        """
        Set a displacement field as SimpleITK.Image or Sisyphe.core.sisypheImage.SisypheImage instance to the current
        SisypheTransform instance.

        Parameters
        ----------
        img : Sisyphe.core.sisypheImage.SisypheImage | SimpleITK.Image
            displacement field image
        """
        if isinstance(img, SisypheImage):
            img = img.getSITKImage()
        if isinstance(img, sitkImage):
            if img.GetNumberOfComponentsPerPixel() == 3 and img.GetPixelIDValue() in (sitkVectorFloat32,
                                                                                      sitkVectorFloat64):
                self.setIdentity()
                self.removeCenter()
                if self._field is not None: del self._field
                # Displacement field img type must be sitkVectorFloat64 (not sitkVectorFloat32)
                self._field = sitkDisplacementFieldTransform(Cast(img, sitkVectorFloat64))
                self.setIdentity()
                self.setSize(img.GetSize())
                self.setSpacing(img.GetSpacing())
            else: raise ValueError('image parameter is not a displacement field.')
        else: raise TypeError('parameter type {} is not sitkImage or SisypheImage.'.format(type(img)))

    def copyFromDisplacementFieldImage(self, img: SisypheImage | sitkImage) -> None:
        """
        Copy a displacement field as SimpleITK.Image or Sisyphe.core.sisypheImage.SisypheImage instance to the current
        SisypheTransform instance.

        Parameters
        ----------
        img : Sisyphe.core.sisypheImage.SisypheImage | SimpleITK.Image
            displacement field image
        """
        if isinstance(img, SisypheImage):
            img = img.copyToSITKImage()
            if img.GetNumberOfComponentsPerPixel() == 3 and img.GetPixelIDValue() in (sitkVectorFloat32,
                                                                                      sitkVectorFloat64):
                self.setIdentity()
                self.removeCenter()
                if self._field is not None: del self._field
                # Displacement field img type must be sitkVectorFloat64 (not sitkVectorFloat32)
                self._field = sitkDisplacementFieldTransform(Cast(img, sitkVectorFloat64))
                self.setIdentity()
                self.setSize(img.GetSize())
                self.setSpacing(img.GetSpacing())
            else: raise ValueError('image parameter is not a displacement field.')
        else: raise TypeError('parameter type {} is not SisypheImage.'.format(type(img)))

    def removeDisplacementField(self) -> None:
        """
        Remove the displacement field of the current SisypheTransform instance.
        """
        if self.isDisplacementField():
            del self._field
            self._field = None
            self._fieldname = ''

    def setVTKTransform(self, trf: vtkTransform, center_reset: bool = False) -> None:
        """
        Copy a vtk.vtkTransform instance to the current SisypheTransform instance.
        The center of rotation of the current SisypheTransform instance is set to default (0.0, 0.0, 0.0).

        Parameters
        ----------
        trf : vtk.vtkTransform
            VTK transform to copy
        center_reset : bool
            set center of rotation to default (0.0, 0.0, 0.0) if True
        """
        if self._field is None:
            if isinstance(trf, vtkTransform):
                mat = trf.GetMatrix()
                self.setVTKMatrix4x4(mat)
                # < Revision 07/09/2024
                if center_reset:
                    self.setCenter([0.0, 0.0, 0.0])
                # Revision 07/09/2024 >
            else: raise TypeError('parameter type {} is not vtkTransform.'.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def getVTKTransform(self, center_correction: bool = False) -> vtkTransform:
        """
        Get a vtk.vtkTransform instance from the current SisypheTransform instance.

        Parameters
        ----------
        center_correction : bool
            if True, replace translations by offset if center of rotation is not default (0.0,0.0,0.0),

        Returns
        -------
        vtk.vtkTransform
            VTK transform copy
        """
        if self._field is None:
            sitkmat = self._transform.GetMatrix()
            # < Revision 07/09/2024
            # center correction management
            if center_correction and self.hasCenter():
                ctrf = self.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                sitktrans = ctrf.getTranslations()
            else: sitktrans = self._transform.GetTranslation()
            # Revision 07/09/2024 >
            # < Revision 19/03/2024
            # to avoid vtk warning, do not edit the vtkMatrix3x3 attribute of a vtkTransform instance
            trf = vtkTransform()
            # vtkmat = trf.GetMatrix()
            vtkmat = vtkMatrix4x4()
            for r in range(3):
                vtkmat.SetElement(r, 3, sitktrans[r])
                for c in range(3):
                    vtkmat.SetElement(r, c, sitkmat[r * 3 + c])
            trf.SetMatrix(vtkmat)
            # Revision 19/03/2024 >
            return trf
        else: raise TypeError('No affine transform.')

    def setVTKMatrix3x3(self, mat: vtkMatrix3x3, center_reset: bool = False) -> None:
        """
        Copy an affine matrix as vtk.vtkMatrix3x3 instance to the current SisypheTransform instance.

        Parameters
        ----------
        mat : vtk.vtkMatrix3x3
            VTK affine matrix to copy
        center_reset : bool
            set center of rotation to default (0.0, 0.0, 0.0) if True
        """
        if self._field is None:
            if isinstance(mat,  vtkMatrix3x3):
                # < Revision 19/03/2025
                # bugfix, error in method name: m = mat.GetGetData()
                m = mat.GetData()
                # Revision 19/03/2025 >
                self._transform.SetMatrix(m)
                # < Revision 07/09/2024
                if center_reset:
                    self.setCenter([0.0, 0.0, 0.0])
                # Revision 07/09/2024 >
            else: raise TypeError('parameter type {} is not vtkMatrix3x3.'.format(type(mat)))
        else: raise TypeError('No affine transform.')

    def setVTKMatrix4x4(self, mat: vtkMatrix4x4, center_reset: bool = False) -> None:
        """
        Copy an affine matrix as vtk.vtkMatrix4x4 instance to the current SisypheTransform instance.
        The center of rotation of the current SisypheTransform instance is set to default (0.0, 0.0, 0.0).

        Parameters
        ----------
        mat : vtk.vtkMatrix4x4
            VTK affine homogeneous affine matrix to copy
        center_reset : bool
            set center of rotation to default (0.0, 0.0, 0.0) if True
        """
        if self._field is None:
            if isinstance(mat,  vtkMatrix4x4):
                self.setIdentity()
                # < Revision 07/09/2024
                if center_reset:
                    self.setCenter([0.0, 0.0, 0.0])
                # Revision 07/09/2024 >
                sitkmat = list()
                sitktrans = list()
                for r in range(3):
                    sitktrans.append(mat.GetElement(r, 3))
                    for c in range(3):
                        sitkmat.append(mat.GetElement(r, c))
                self._transform.SetMatrix(sitkmat)
                self._transform.SetTranslation(sitktrans)
            else: raise TypeError('parameter type {} is not tkMatrix4x4.'.format(type(mat)))
        else: raise TypeError('No affine transform.')

    def getVTKMatrix4x4(self, center_correction: bool = False) -> vtkMatrix4x4:
        """
        Get the affine matrix as vtk.vtkMatrix4x4 instance of the current SisypheTransform instance.

        Parameters
        ----------
        center_correction : bool
            if True, replace translations by offset if center of rotation is not default (0.0,0.0,0.0),

        Returns
        -------
        vtk.vtkMatrix4x4
            VTK homogeneous affine matrix copy
        """
        if self._field is None: return self.getVTKTransform(center_correction).GetMatrix()
        else: raise TypeError('No affine transform.')

    def getVTKMatrix3x3(self) -> vtkMatrix3x3:
        """
        Get the affine matrix as vtk.vtkMatrix3x3 instance
        of the current SisypheTransform instance.

        Returns
        -------
        vtk.vtkMatrix4x4
            VTK affine matrix copy
        """
        if self._field is None:
            m4 = self.getVTKTransform().GetMatrix()
            m3 = vtkMatrix3x3()
            for i in range(3):
                for j in range(3):
                    m3.SetElement(i, j, m4.GetElement(i, j))
            return m3
        else: raise TypeError('No affine transform.')

    def getInverseVTKTransform(self, center_correction: bool = False) -> vtkTransform:
        """
        Get the inverse affine matrix as vtk.vtkMatrix3x3 instance of the current SisypheTransform instance.

        Parameters
        ----------
        center_correction : bool
            if True, take into account center of rotation and replace translations by offset if center of rotation
            is not default (0.0,0.0,0.0),

        Returns
        -------
        vtk.vtkMatrix4x4
            inverse transform as VTK homogeneous affine matrix
        """
        if self._field is None:
            trf = self.getVTKTransform(center_correction)
            # noinspection PyTypeChecker
            return trf.Inverse()
        else: raise TypeError('No affine transform.')

    def getNumpyArray(self, homogeneous: bool = False) -> ndarray:
        """
        Get the affine matrix as numpy.ndarray instance of the current SisypheTransform instance.

        Parameters
        ----------
        homogeneous : boolean
            homogeneous 4x4 affine matrix if True, 3x3 affine matrix otherwise

        Returns
        -------
        numpy.ndarray
            homogeneous affine matrix as numpy ndarray
        """
        if self._field is None:
            if homogeneous:
                np = array(self.getFlattenMatrix(homogeneous))
                return np.reshape(4, 4)
            else:
                np = array(self._transform.GetMatrix())
                return np.reshape(3, 3)
        else: raise TypeError('No affine transform.')

    def setNumpyArray(self, np: ndarray) -> None:
        """
        Copy an affine matrix as numpy.ndarray instance to the current SisypheTransform instance.

        Parameters
        ----------
        np : numpy.ndarray
            homogeneous affine matrix
        """
        if self._field is None:
            if isinstance(np, ndarray):
                if np.shape == (3, 3):
                    self._transform.SetMatrix(np.flatten())
                elif np.shape == (4, 4):
                    self.setIdentity()
                    m = list(np[0:3, 0:3].flatten())
                    t = list(np[0:3, 3])
                    self._transform.SetMatrix(m)
                    self._transform.SetTranslation(t)
                else: raise ValueError('numpy array shape is not supported.')
            else: raise TypeError('parameter type {} is not numpy array.'.format(type(np)))
        else: raise TypeError('No affine transform.')

    def setANTSTransform(self, trf: ANTsTransform) -> None:
        """
        Copy an ants.core.ants_transform.ANTsTransform instance to the current SisypheTransform instance.
        The only ANTsTransform supported type is AffineTransform.

        Parameters
        ----------
        trf : ants.core.ants_transform.ANTsTransform
            ANTs transform to copy
        """
        if self._field is None:
            if isinstance(trf, ANTsTransform):
                if trf.type == 'AffineTransform':
                    self.setIdentity()
                    self._transform.SetMatrix(trf.parameters[0:9])
                    self._transform.SetTranslation(trf.parameters[-3:])
                    # < Revision 07/09/2024
                    # copy ANTsTransform center of rotation
                    self._transform.SetCenter(list(trf.fixed_parameters))
                    # Revision 07/09/2024 >
                else: raise TypeError('ANTsTransform type {} is not AffineTransform.'.format(trf.type))
            else: raise TypeError('parameter type {} is not ANTsTransform.'.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def getANTSTransform(self) -> ANTsTransform:
        """
        Get an ants.core.ants_transform.ANTsTransform instance from the current SisypheTransform instance.

        Returns
        -------
        ants.core.ants_transform.ANTsTransform
            ANTs transform copy
        """
        if self._field is None:
            # Affine transform
            p = self._transform.GetMatrix() + self._transform.GetTranslation()
            trf = ANTsTransform()
            trf.set_parameters(p)
            # < Revision 07/09/2024
            # copy center of rotation to ANTsTransform
            if self.hasCenter():
                trf.set_fixed_parameters(self.getCenter())
            # Revision 07/09/2024 >
        else:
            # Displacement field transform
            # < Revision 26/10/2024
            # adds displacement field conversion
            field = self.getDisplacementField().copyToANTSImage()
            trf = transform_from_displacement_field(field)
            # Revision 26/10/2024 >
        return trf

    def getMatrixColumn(self, c: int) -> vectorFloat3:
        """
        Get a column from the affine matrix of the current SisypheTransform instance.

        Parameters
        ----------
        c : int
            column number (0 <= c < 3)

        Returns
        -------
        list[float]
            column vector of affine matrix
        """
        if self._field is None:
            if isinstance(c, int):
                if 0 <= c < 3:
                    r = self.getFlattenMatrix()
                    return [r[0 + c], r[3 + c], r[6 + c]]
                else: raise ValueError('parameter value {} is out of range (0 to 2).'.format(c))
            else: raise TypeError('parameter type {} isn not int'.format(type(c)))
        else: raise TypeError('No affine transform.')

    def getMatrixDiagonal(self) -> vectorFloat3:
        """
        Get the diagonal of the affine matrix of the current SisypheTransform instance.

        Returns
        -------
        list[float]
            diagonal vector of affine matrix
        """
        r = self.getFlattenMatrix()
        return [r[0], r[4], r[8]]

    def getFlattenMatrix(self, homogeneous: bool = False) -> list[float]:
        """
        Get the affine matrix of the current SisypheTransform instance as a list.

        Parameters
        ----------
        homogeneous : bool
            homogeneous 4x4 affine matrix if True, 3x3 affine matrix otherwise

        Returns
        -------
        list[float]
            16 elements (4x4 matrix) if homogeneous is True, 9 elements (3x3 matrix) otherwise
        """
        if self._field is None:
            if homogeneous:
                m = list(self._transform.GetMatrix())
                t = list(self._transform.GetTranslation())
                m = m[:3] + [t[0]] + m[3:6] + [t[1]] + m[-3:] + [t[2], 0.0, 0.0, 0.0, 1.0]
                return m
            else: return list(self._transform.GetMatrix())
        else: raise TypeError('No affine transform.')

    def setFlattenMatrix(self, m: list[float], bycolumn: bool = False) -> None:
        """
        Set the affine matrix of the current SisypheTransform instance from a list.

        Parameters
        ----------
        m : list[float]
            9 (3x3 affine matrix) or 16 elements (4x4 homogeneous affine matrix)
        bycolumn : bool
            elements in column order if True, row order otherwise
        """
        if self._field is None:
            if len(m) == 9:
                if bycolumn: m = list(array(m).reshape(3, 3).T.flatten())
                self._transform.SetMatrix(m)
            elif len(m) == 16:
                self.setIdentity()
                m = m[:3] + m[4:7] + m[8:11]
                t = [m[3], m[7], m[11]]
                self._transform.SetMatrix(m)
                self._transform.SetTranslation(t)
            else: raise ValueError('List size is not supported.')
        else: raise TypeError('No affine transform.')

    def applyToPoint(self, coor: vectorFloat3) -> vectorFloat3:
        """
        Apply the geometric transformation of the current SisypheTransform instance to a point.

        Parameters
        ----------
        coor : tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis point coordinates

        Returns
        -------
        tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis point coordinates
        """
        if self._field is None:
            return self._transform.TransformPoint(tuple(coor))
        else: return self._field.TransformPoint(coor)

    # noinspection PyTypeChecker
    def applyInverseToPoint(self, coor: vectorFloat3) -> vectorFloat3:
        """
        Apply the inverse geometric transformation of the current SisypheTransform instance to a point.

        Parameters
        ----------
        coor : tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis point coordinates

        Returns
        -------
        tuple[float, float, float] | list[float]
            x-axis, y-axis and z-axis point coordinates
        """
        if self._field is None:
            t: sitkTransform = self._transform.GetInverse()
            return t.TransformPoint(tuple(coor))
        else: raise AttributeError('_field attribute is None.')

    def preMultiply(self,
                    trf: vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkAffineTransform | sitkEuler3DTransform | ndarray,
                    homogeneous: bool = False) -> None:
        """
        Compose a geometric transformation with the geometric transformation of the current SisypheTransform instance.
        Order of transformations 1. current 2. parameter (Pre-multiply current by parameter)

        Parameters
        ----------
        trf : vtk.vtkTransform | vtk.vtkMatrix4x4 | SimpleITK.AffineTransform | SimpleITK.Euler3DTransform | ndarray | SisypheTransform
            affine transform used to pre-multiply
        homogeneous : bool
            used for ndarray trf, 4x4 affine matrix if True, 3x3 affine matrix otherwise
        """
        if self._field is None:
            # Apply new transformation after current
            if isinstance(trf, vtkTransform):
                trf = trf.GetMatrix()
            if isinstance(trf, vtkMatrix4x4):
                trf = self.getVTKtoNumpy(trf)
            elif isinstance(trf, SisypheTransform):
                trf = trf.getNumpyArray(homogeneous)
            elif isinstance(trf, (sitkAffineTransform, sitkEuler3DTransform)):
                trf = self.getSITKtoNumpy(trf)
            if isinstance(trf, ndarray):
                if homogeneous: r = matmul(trf, self.getNumpyArray(homogeneous=True))
                else: r = matmul(trf[:3, :3], self.getNumpyArray())
                self.setNumpyArray(r)
            else: raise TypeError('parameter type {} is not numpy array, vtkTransform '
                                  'vtkMatrix4x4, sitkTransform or SisypheTransform. '.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def postMultiply(self,
                     trf: vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkAffineTransform | sitkEuler3DTransform | ndarray,
                     homogeneous: bool = False) -> None:
        """
        Compose a geometric transformation with the geometric transformation of the current SisypheTransform instance.
        Order of transformations 1. parameter 2. current (Post-multiply current by parameter)

        Parameters
        ----------
        trf : vtk.vtkTransform | vtk.vtkMatrix4x4 | SimpleITK.AffineTransform | SimpleITK.Euler3DTransform | ndarray | SisypheTransform
            affine transform used to post-multiply
        homogeneous : bool
            used for ndarray trf, 4x4 affine matrix if True, 3x3 affine matrix otherwise
        """
        if self._field is None:
            # Apply new transformation before current
            if isinstance(trf, vtkTransform):
                trf = trf.GetMatrix()
            if isinstance(trf, vtkMatrix4x4):
                trf = self.getVTKtoNumpy(trf)
            elif isinstance(trf, SisypheTransform):
                trf = trf.getNumpyArray(homogeneous)
            elif isinstance(trf, (sitkAffineTransform, sitkEuler3DTransform)):
                trf = self.getSITKtoNumpy(trf)
            if isinstance(trf, ndarray):
                if homogeneous: r = matmul(self.getNumpyArray(homogeneous=True), trf)
                else: r = matmul(self.getNumpyArray(), trf[:3, :3])
                self.setNumpyArray(r)
            else:
                raise TypeError('parameter type {} is not numpy array, vtkTransform, '
                                'vtkMatrix4x4, sitkTransform or SisypheTransform. '.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def isDisplacementField(self) -> bool:
        """
        Check whether the current SisypheTransform instance is a displacement field geometric transformation.

        Returns
        -------
        bool
            True if displacement field transform
        """
        return self._field is not None

    def isRigid(self) -> bool:
        """
        Check whether the current SisypheTransform instance is rigid geometric transformation. True if matrix is
        orthogonal i.e. M-1 Mt = I

        Returns
        -------
        bool
            True if rigid transform
        """
        r = False
        if self._field is None:
            m1 = self.getNumpyArray(homogeneous=True).T
            m2 = inv(self.getNumpyArray(homogeneous=True))
            r = allclose(m1, m2)
        return r

    def isAffine(self) -> bool:
        """
        Check whether the current SisypheTransform instance is an affine geometric transformation.

        Returns
        -------
        bool
            True if affine transform
        """
        return self._field is None

    def affineToDisplacementField(self, inverse: bool = True) -> None:
        """
        Convert the affine geometric transformation of the current SisypheTransform instance to a displacement field.

        Parameters
        ----------
        inverse : bool
            inverse affine geometric transformation if True (default)
        """
        if self._field is None:
            if not self.isIdentity():
                f = sitkTransformToDisplacementFieldFilter()
                f.SetSize(self.getSize())
                f.SetOutputSpacing(self.getSpacing())
                f.SetOutputOrigin([0.0, 0.0, 0.0])
                f.SetOutputPixelType(sitkVectorFloat64)
                if self.hasCenter(): trf = self.getEquivalentTransformWithNewCenterOfRotation([0.0, 0.0, 0.0])
                else: trf = self
                if inverse: trf = trf.getInverseTransform()
                field = f.Execute(trf.getSITKTransform())
                self._field = sitkDisplacementFieldTransform(3)
                self._field.SetInterpolator(sitkLinear)
                self._field.SetDisplacementField(field)
                self.setIdentity()
                self.setCenter([0.0, 0.0, 0.0])
        else: raise TypeError('No affine transform.')

    def hasID(self) -> bool:
        """
        Check whether the ID attribute of the current SisypheTransform instance is defined (not '')

        Returns
        -------
        bool
            True if ID is defined
        """
        return self._ID != ''

    def getID(self) -> str:
        """
        Get the ID attribute of the current SisypheTransform instance.

        Returns
        -------
        str
            transform ID
        """
        return self._ID

    def setID(self, ID: str | SisypheVolume) -> None:
        """
        Set the ID attribute of the current SisypheTransform instance.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            transform ID
        """
        if isinstance(ID, str): self._ID = ID
        elif isinstance(ID, SisypheVolume): self._ID = ID.getID()
        else: raise TypeError('parameter is not str, SisypheImage or SisypheVolume.')

    def getSpacing(self) -> vectorFloat3:
        """
        Get the spacing attribute of the current SisypheTransform instance. Voxel size in the x, y and z axes of the
        floating volume in mm.

        Returns
        -------
        list[float]
            Voxel size in the x, y and z axes of the floating volume in mm
        """
        return self._spacing

    def setSpacing(self, spacing: vectorFloat3) -> None:
        """
        Set the spacing attribute of the current SisypheTransform instance. Voxel size in the x, y and z axes of the
        floating volume in mm.

        Parameters
        ----------
        spacing : list[float]
            Voxel size in the x, y and z axes of the floating volume in mm
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(spacing, (SisypheImage, SisypheVolume)): self._spacing = list(spacing.getSpacing())
        else:  self._spacing = list(spacing)

    def hasSpacing(self) -> bool:
        """
        Check whether the spacing attribute of the current SisypheTransform instance is defined (not 0.0, 0.0, 0.0)

        Returns
        -------
        bool
            True if spacing is defined
        """
        return self._spacing != (0.0, 0.0, 0.0)

    def getSize(self) -> vectorInt3:
        """
        Get the size attribute of the current SisypheTransform instance. Image size in the x, y and z axes of the
        floating volume (in voxels).

        Returns
        -------
        list[int]
            image size in the x, y and z axes of the floating volume (in voxels)
        """
        return self._size

    def setSize(self, size: vectorInt3):
        """
        Set the size attribute of the current SisypheTransform instance. Image size in the x, y and z axes of the
        floating volume (in voxels).

        Parameters
        ----------
        size : list[int]
            image size in the x, y and z axes of the floating volume (in voxels)
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(size, (SisypheImage, SisypheVolume)): self._size = list(size.getSize())
        else: self._size = list(size)

    def hasSize(self) -> bool:
        """
        Check whether the size attribute of the current SisypheTransform instance is defined (not 0, 0, 0)

        Returns
        -------
        bool
            True if size is defined
        """
        return self._size != (0, 0, 0)

    def copyAttributesTo(self, t: SisypheTransform) -> None:
        """
        Copy attributes of the current SisypheTransform instance to a SisypheTransform instance.

        Parameters
        ----------
        t : SisypheTransform
            copy attributes to this transform
        """
        t.setSize(self.getSize())
        t.setSpacing(self.getSpacing())
        t.setCenter(self.getCenter())
        t.setID(self.getID())
        t.setName(self.getName())

    def copyAttributesFrom(self, t: SisypheTransform) -> None:
        """
        Copy attributes of a SisypheTransform instance to the current SisypheTransform instance.

        Parameters
        ----------
        t : SisypheTransform
            copy attributes from this transform
        """
        self.setSize(t.getSize())
        self.setSpacing(t.getSpacing())
        self.setCenter(t.getCenter())
        self.setID(t.getID())
        self.setName(t.getName())

    def setAttributesFromFixedVolume(self, vol: SisypheVolume) -> None:
        """
        Set the attributes relating to fixed volume (ID, size, spacing) of the current SisypheTransform instance
        from a SisypheVolume instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            copy ID, size and spacing attributes from this volume
        """
        if isinstance(vol, SisypheVolume):
            self.setID(vol)
            self.setName(vol.getFilename())
            self._size = vol.getSize()
            self._spacing = vol.getSpacing()

    def hasFixedVolumeAttributes(self) -> bool:
        """
        Check whether the attributes relating to fixed volume (size, spacing) of the current SisypheTransform instance
        are defined.

        Returns
        -------
        bool
            True if ID, size and spacing attributes are defined
        """
        return self.hasSize() and self.hasSpacing()

    def hasSameFixedVolumeAttributes(self, vol: SisypheVolume) -> bool:
        """
        Check whether the attributes of the current SisypheTransform instance relating to fixed volume (size, spacing)
        are those of a SisypheVolume instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume attributes to test

        Returns
        -------
        bool
            True if the parameter volume has the same size and spacing attributes
        """
        if isinstance(vol, SisypheVolume):
            return self._size == vol.getSize() and \
                   self._spacing == vol.getSpacing()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def saveDisplacementField(self, filename: str) -> None:
        """
        Save the displacement field of the current SisypheTransform instance as SisypheVolume.
        Adds 'field_' prefix to the filename parameter.

        Parameters
        ----------
        filename : str
            displacement field file name
        """
        if self._field is not None:
            field = SisypheVolume()
            field.setSITKImage(Cast(self._field.GetDisplacementField(), sitkVectorFloat32))
            field.getAcquisition().setSequenceToDisplacementField()
            field.setID(self.getID())
            path = split(filename)
            if path[1][:6] != 'field_': self._fieldname = join(path[0], 'field_' + path[1])
            else: self._fieldname = filename
            field.save(self._fieldname)

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
        Write the current SisypheTransform instance attributes to xml document instance. Use of this method is not
        recommended (called internally by saveAs method).

        Parameters
        ----------
        doc : minidom.Document
            xml document
        currentnode : minidom.Element
            xml root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                transform = doc.createElement('transform')
                currentnode.appendChild(transform)
                # ID
                node = doc.createElement('ID')
                transform.appendChild(node)
                ID = self.getID()
                txt = doc.createTextNode(ID)
                node.appendChild(txt)
                # Name
                node = doc.createElement('name')
                transform.appendChild(node)
                txt = doc.createTextNode(self._name)
                node.appendChild(txt)
                # Size
                node = doc.createElement('size')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join([str(i) for i in self.getSize()]))
                node.appendChild(txt)
                # Spacing
                node = doc.createElement('spacing')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join([str(i) for i in self.getSpacing()]))
                node.appendChild(txt)
                # center
                node = doc.createElement('center')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join([str(i) for i in self.getCenter()]))
                node.appendChild(txt)
                # translations
                node = doc.createElement('translations')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join([str(i) for i in self.getTranslations()]))
                node.appendChild(txt)
                # matrix
                buff = self._transform.GetMatrix()
                node = doc.createElement('matrixrow1')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join(str(buff[i]) for i in range(3)))
                node.appendChild(txt)
                node = doc.createElement('matrixrow2')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join(str(buff[i]) for i in range(3, 6)))
                node.appendChild(txt)
                node = doc.createElement('matrixrow3')
                transform.appendChild(node)
                txt = doc.createTextNode(' '.join(str(buff[i]) for i in range(6, 9)))
                node.appendChild(txt)
                # DisplacementField
                node = doc.createElement('displacementfield')
                transform.appendChild(node)
                if self._field is not None:
                    from Sisyphe.core.sisypheVolume import SisypheVolume
                    field = SisypheVolume()
                    """
                        Displacement field image type is sitkFloat64 in SimpleITK DisplacementFieldTransform class.
                        Convert to sitkFloat32. 
                    """
                    field.setSITKImage(Cast(self._field.GetDisplacementField(), sitkVectorFloat32))
                    field.getAcquisition().setSequenceToDisplacementField()
                    field.save(self._fieldname)
                    txt = doc.createTextNode(field.getBasename())
                    node.appendChild(txt)
                else:
                    txt = doc.createTextNode('')
                    node.appendChild(txt)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXMLNode(self, currentnode: minidom.Element) -> None:
        """
        Read the current SisypheTransform instance attributes from xml document instance. The use of this method is
        not recommended (called internally by parseXML method).

        Parameters
        ----------
        currentnode : minidom.Element
            xml document
        """
        if currentnode.nodeName == 'transform':
            buffmat = [0] * 9
            for node in currentnode.childNodes:
                # ID
                if node.nodeName == 'ID':
                    if node.hasChildNodes(): self._ID = node.firstChild.data
                    else: self._ID = ''
                # Name
                if node.nodeName == 'name':
                    if node.hasChildNodes(): self._name = node.firstChild.data
                    else: self._name = ''
                # Size
                elif node.nodeName == 'size':
                    if node.hasChildNodes():
                        buff = node.firstChild.data
                        buff = buff.split(' ')
                        self.setSize((int(buff[0]), int(buff[1]), int(buff[2])))
                    else: self.setSize([0, 0, 0])
                # Spacing
                elif node.nodeName == 'spacing':
                    if node.hasChildNodes():
                        buff = node.firstChild.data
                        buff = buff.split(' ')
                        self.setSpacing((float(buff[0]), float(buff[1]), float(buff[2])))
                    else: self.setSpacing([0.0, 0.0, 0.0])
                # Center
                elif node.nodeName == 'center':
                    if node.hasChildNodes():
                        buff = node.firstChild.data
                        buff = buff.split(' ')
                        self.setCenter((float(buff[0]), float(buff[1]), float(buff[2])))
                    else: self.setCenter([0.0, 0.0, 0.0])
                # Translations
                elif node.nodeName == 'translations':
                    if node.hasChildNodes():
                        buff = node.firstChild.data
                        buff = buff.split(' ')
                        self.setTranslations((float(buff[0]), float(buff[1]), float(buff[2])))
                    else: self.setTranslations([0.0, 0.0, 0.0])
                # Matrix
                elif node.nodeName == 'matrixrow1':
                    buff = node.firstChild.data
                    buffmat[:3] = buff.split(' ')
                elif node.nodeName == 'matrixrow2':
                    buff = node.firstChild.data
                    buffmat[3:6] = buff.split(' ')
                elif node.nodeName == 'matrixrow3':
                    buff = node.firstChild.data
                    buffmat[-3:] = buff.split(' ')
                elif node.nodeName == 'displacementfield':
                    if node.hasChildNodes():
                        self._fieldname = node.firstChild.data
                    else:
                        self._field = None
                        self._fieldname = ''
            if len(buffmat) == 9:
                self._transform.SetMatrix([float(i) for i in buffmat])
            else: raise IOError('XML file read error.')
        else: raise ValueError('Node name {} is not \'transform\'.'.format(currentnode.nodeName))

    def parseXML(self, doc: minidom.Document) -> None:
        """
        Read the current SisypheTransform instance attributes from xml document instance. The use of this method is
        not recommended (called internally by load method).

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                transform = doc.getElementsByTagName('transform')
                self.parseXMLNode(transform[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a PySisyphe Transform (.xtrf) file.

        Parameters
        ----------
        filename : str
            PySisyphe Transform file name
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if self._field is None: self._fieldname = ''
        else:
            if self._fieldname == '':
                path = split(filename)
                self._fieldname = join(path[0], 'field_' + path[1])
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        """
        
            Save XML transform (*.xtrf)
        
        """
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()

    def load(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from PySisyphe Transform (.xtrf) file.

        Parameters
        ----------
        filename : str
            PySisyphe Transform file name
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
            if self._fieldname != '':
                self._fieldname = join(dirname(filename), self._fieldname)
                if exists(self._fieldname):
                    self._field = sitkDisplacementFieldTransform(3)
                    self._field.SetInterpolator(sitkLinear)
                    from Sisyphe.core.sisypheVolume import SisypheVolume
                    field = SisypheVolume()
                    field.load(self._fieldname)
                    if (field.getNumberOfComponentsPerPixel() == 3 and
                            field.isFloatDatatype() and
                            field.getAcquisition().isDisplacementField()):
                        """
                            Displacement field image type is stored on disk with sitkVectorFloat32 datatype, 
                            but with SimpleITK DisplacementFieldTransform class, datatype must be sitkVectorFloat64.
                            Cast datatype to sitkVectorFloat64.
                        """
                        self._field.SetDisplacementField(Cast(field.getSITKImage(), sitkVectorFloat64))
                        self.setIdentity()
                        self._fieldname = field.getBasename()
                else: raise IOError('no such file : {}'.format(self._fieldname))
        else: raise IOError('no such file : {}'.format(filename))

    # IO public methods

    def saveToXfmTransform(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a XFM (.xfm) file.

        Parameters
        ----------
        filename : str
            XFM file name
        """
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.xfm'
            w = vtkMNITransformWriter()
            w.SetFileName(filename)
            w.SetTransform(self.getVTKTransform())
            w.Write()
        else: raise TypeError('Displacement field transform can not be saved to Xfm format.')

    def saveToTfmTransform(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a TFM (.tfm) file.

        Parameters
        ----------
        filename : str
            TFM file name
        """
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.tfm'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to Tfm format.')

    def saveToMatfileTransform(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a Matlab (.mat) file.

        Parameters
        ----------
        filename : str
            Matlab file name
        """
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.mat'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to Matfile format.')

    def saveToTxtTransform(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a text (.txt) file.

        Parameters
        ----------
        filename : str
            text file name
        """
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.txt'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to txt format.')

    def saveToANTSTransform(self, filename: str) -> None:
        """
        Save the current SisypheTransform instance to a ANTs transform (.mat) file.

        Parameters
        ----------
        filename : str
            ANTs transform file name
        """
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.mat'
            trf = self.getANTSTransform()
            write_transform(trf, filename)
        else: raise TypeError('Displacement field transform can not be saved to ANTs format.')

    def loadFromXfmTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a XFM (.xfm) file.

        Parameters
        ----------
        filename : str
            XFM file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.xfm':
            filename = path + '.xfm'
        if exists(filename):
            if ext.lower() == '.xfm':
                self.setIdentity()
                self.removeDisplacementField()
                r = vtkMNITransformReader()
                r.SetFileName(filename)
                r.Update()
                self.setVTKTransform(r.GetNthTransform(0))
            else: raise IOError('{} is not a XFM file extension.'.format(ext))
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromTfmTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a TFM (.tfm) file.

        Parameters
        ----------
        filename : str
            TFM file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.tfm':
            filename = path + '.tfm'
        if exists(filename):
            if ext.lower() == '.tfm':
                self.setIdentity()
                self.removeDisplacementField()
                self.setSITKTransform(sitkAffineTransform(sitkReadTransform(filename)))
            else: raise IOError('{} is not a TFM file extension.'.format(ext))
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromMatfileTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a Matlab (.mat) file.

        Parameters
        ----------
        filename : str
            Matlab file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.mat':
            filename = path + '.mat'
        if exists(filename):
            if ext.lower() == '.mat':
                self.setIdentity()
                self.removeDisplacementField()
                self.setSITKTransform(sitkAffineTransform(sitkReadTransform(filename)))
            else: raise IOError('{} is not a Matfile file extension.'.format(ext))
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromTxtTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a text (.txt) file.

        Parameters
        ----------
        filename : str
            text file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.txt':
            filename = path + '.txt'
        if exists(filename):
            if ext.lower() == '.txt':
                self.setIdentity()
                self.removeDisplacementField()
                self.setSITKTransform(sitkAffineTransform(sitkReadTransform(filename)))
            else: raise IOError('{} is not a Txt file extension.'.format(ext))
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromANTSTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a ANTs transform (.mat) file.

        Parameters
        ----------
        filename : str
            ANTs transform file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.mat': filename = path + '.mat'
        if exists(filename):
            self.setIdentity()
            self.removeDisplacementField()
            trf = read_transform(filename)
            self.setANTSTransform(trf)
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromBrainVoyagerTransform(self, filename: str) -> None:
        """
        Load the current SisypheTransform instance from a BrainVoyager transform (.trf) file.

        Parameters
        ----------
        filename : str
            BrainVoyager transform file name
        """
        path, ext = splitext(filename)
        if ext.lower() != '.trf': filename = path + '.trf'
        if exists(filename):
            trf = read_trf(filename)
            if trf[0]['DataFormat'] == 'Matrix':
                self.setNumpyArray(trf[1]['Matrix'])
            else: raise ValueError('{} format is not supported.'.format(trf['DataFormat']))
        else: raise FileNotFoundError('No such file {}.'.format(filename))


class SisypheApplyTransform(object):
    """
    Description
    ~~~~~~~~~~~

    SisypheVolume resampling class.

    Applies SisypheTransform geometric transformation to resample a moving image, ROI, mesh or streamlines into
    the space of a fixed image. Affine geometric transformation is in forward convention (apply inverse transformation
    to resample). Displacement field geometric transformation is in backward convention.

    This class automatically updates the SisypheTransforms instances associated to the fixed, moving and
    resliced volumes.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheApplyTransform

    Creation: 05/10/2021
    Last revision: 22/05/2025
    """
    __slots__ = ['_moving', '_roi', '_mesh', '_sl', '_transform', '_resample']

    # Class constants

    _NEAREST, _LIBITK, _LIBSITK, _LIBVTK, _LIBSITKVEC = 0, 1, 2, 3, 4

    _TOCODE = {'nearest': sitkNearestNeighbor,
               'linear': sitkLinear,
               'bspline': sitkBSpline,
               'gaussian': sitkGaussian,
               'hammingsinc': sitkHammingWindowedSinc,
               'cosinesinc': sitkCosineWindowedSinc,
               'welchsinc': sitkWelchWindowedSinc,
               'lanczossinc': sitkLanczosWindowedSinc,
               'blackmansinc': sitkBlackmanWindowedSinc}

    _FROMCODE: dict[int, str] = {sitkNearestNeighbor: 'nearest',
                                 sitkLinear: 'linear',
                                 sitkBSpline: 'bspline',
                                 sitkGaussian: 'gaussian',
                                 sitkHammingWindowedSinc: 'hammingsinc',
                                 sitkCosineWindowedSinc: 'cosinesinc',
                                 sitkWelchWindowedSinc: 'welchsinc',
                                 sitkLanczosWindowedSinc: 'lanczossinc',
                                 sitkBlackmanWindowedSinc: 'blackmansinc'}

    # Class methods

    @classmethod
    def getInterpolatorCodeFromName(cls, name: str) -> int:
        """
        Get SimpleITK’s interpolation int code from a name.

        Parameters
        ----------
        name : str
            interpolation name. Methods of interpolation are: 'nearest', 'linear', 'bspline', 'gaussian',
            'hammingsinc', 'cosinesinc', 'welchsinc', 'lanczossinc', 'blackmansinc'

        Returns
        -------
        int
            SimpleITK’s interpolation int code
        """
        return cls._TOCODE[name]

    @classmethod
    def getInterpolatorNameFromCode(cls, code: int) -> str:
        """
        Get interpolation name from a SimpleITK’s int code.

        Parameters
        ----------
        code : int
            SimpleITK’s interpolation int code

        Returns
        -------
        str
            interpolation name. Methods of interpolation are : 'nearest', 'linear', 'bspline', 'gaussian',
            'hammingsinc', 'cosinesinc', 'welchsinc', 'lanczossinc', 'blackmansinc'
        """
        return cls._FROMCODE[code]

    # Special methods

    """
    Private attributes

    _moving     SisypheVolume to resample
    _roi        SisypheROI to resample
    _mesh       SisypheMesh to resample
    _sl         SisypheStreamlines to resample
    _transform  SisypheTransform, geometric transformation to apply
    _resample   sitkResampleImageFilter    
    """

    def __init__(self) -> None:
        """
        SisypheApplyTransform instance constructor.
        """
        self._moving = None
        self._roi = None
        self._mesh = None
        self._sl = None
        self._transform = None
        self._resample = sitkResampleImageFilter()
        self._resample.SetInterpolator(sitkLinear)

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheApplyTransform instance to str
        """
        buff = '\nTransform:\n{}\n'.format(str(self._transform))
        buff += 'Resample volume:\n{}\n'.format(str(self._moving))
        buff += 'Interpolator: {}\n'.format(self.getInterpolator())
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheApplyTransform instance representation
        """
        return 'SisypheApplyTransform instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setInterpolator(self, v: int | str) -> None:
        """
        Set the interpolator attribute of the current SisypheApplyTransform instance. This attribute defines the method
        of interpolation used to reslice the "moving" volume.

        Parameters
        ----------
        v : int | str
            SimpleITK’s interpolation int code or interpolation name. Methods of interpolation are : 'nearest',
            'linear', 'bspline', 'gaussian','hammingsinc', 'cosinesinc', 'welchsinc', 'lanczossinc', 'blackmansinc'
        """
        if self.hasMoving() and isinstance(self._moving, SisypheBinaryImage): self._resample.SetInterpolator(0)
        elif self.hasMoving() and self._moving.getAcquisition().isLB(): self._resample.SetInterpolator(0)
        else:
            if isinstance(v, str):
                if v in self._TOCODE: self._resample.SetInterpolator(self._TOCODE[v])
                else: raise ValueError('interpolator str {} is not valid'.format(v))
            elif isinstance(v, int):
                if v < 10: self._resample.SetInterpolator(v)
                else: raise ValueError('interpolator int {} is not valid, must be less than 10.'.format(v))
            else: raise TypeError('parameter type {} is not str or int'.format(type(v)))

    def getInterpolator(self) -> str:
        """
        Get the interpolator attribute of the current SisypheApplyTransform instance. This attribute defines the method
        of interpolation used to reslice the "moving" volume.

        Returns
        -------
        str
            interpolation name. Methods of interpolation are : 'nearest', 'linear', 'bspline', 'gaussian',
            'hammingsinc', 'cosinesinc', 'welchsinc', 'lanczossinc', 'blackmansinc'
        """
        return self._FROMCODE[self._resample.GetInterpolator()]

    def getInterpolatorSITKCode(self) -> int:
        """
        Get the interpolator attribute of the current SisypheApplyTransform instance. This attribute defines the method
        of interpolation used to reslice the "moving" volume.

        Returns
        -------
        int
            SimpleITK’s interpolation int code
        """
        return self._resample.GetInterpolator()

    def setTransform(self, trf: SisypheTransform, center: bool = True) -> None:
        # < Revision 03/09/2024
        # setTransform(self, trf: SisypheTransform, center: bool = False) -> None:
        # change center default to True
        # Revision 03/09/2024 >
        """
        Set the transform attribute of the current SisypheApplyTransform instance. This attribute defines the geometric
        transformation used to reslice the "moving" volume.

        Parameters
        ----------
        trf : SisypheTransform
            transform to copy
        center : bool
            set center to 0.0, 0.0, 0.0 if False (default True)
        """
        if isinstance(trf, SisypheTransform):
            if not center: trf.setCenter([0.0, 0.0, 0.0])
            self._transform = trf
            self._resample.SetSize(self._transform.getSize())
            self._resample.SetOutputSpacing(self._transform.getSpacing())
            if trf.isAffine():
                # Affine trf is by default a forward transform
                # inverse trf = backward transform used to resample
                self._resample.SetTransform(trf.getInverseSITKTransform())
            else:
                # Displacement field trf is already backward transform
                self._resample.SetTransform(trf.getSITKTransform())
        else: raise TypeError('parameter type {} is not SisypheTransform'.format(type(trf)))

    def setFromTransforms(self, trfs: SisypheTransforms, ID: str | SisypheVolume) -> None:
        """
        Set the transform attribute of the current SisypheApplyTransform instance  from a SisypheTransforms instance
        and an ID key.

        Parameters
        ----------
        trfs : SisypheTransforms
            trasnform to copy
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            - ID key of the SisypheTransforms container, SisypheTransform = SisypheTransforms[ID] or
            - ID key is the ID attribute of the SisypheVolume
        """
        if isinstance(trfs, SisypheTransforms):
            if ID in trfs: self.setTransform(trfs[ID])
        else: raise TypeError('parameter type {} is not SisypheTransforms'.format(type(trfs)))

    def setFromVolumes(self,
                       fixed: SisypheVolume,
                       moving: SisypheVolume) -> None:
        """
        Set attributes (size, spacing, moving volume and transform) of the current SisypheApplyTransform instance from
        fixed and moving SisypheVolume instances.

        size and spacing: size and spacing attributes of the fixed SisypheVolume instance.
        transform: SisypheTransforms instance associated to the moving volume with ID attribute of the fixed volume as key.

        Parameters
        ----------
        fixed : Sisyphe.core.sisypheVolume.SisypheVolume
            fixed volume
        moving : Sisyphe.core.sisypheVolume.SisypheVolume
            moving volume
        """
        if isinstance(fixed, SisypheVolume) and isinstance(moving, SisypheVolume):
            transform = moving.getTransformFromID(fixed.getID())
            if transform is not None:
                self.setMoving(moving)
                self.setTransform(transform)
                if not transform.hasSize(): transform.setSize(fixed.getSize())
                if not transform.hasSpacing(): transform.setSpacing(fixed.getSpacing())
                if not transform.hasCenter(): transform.setCenter(fixed.getCenter())
            else: raise ValueError('volumes {} and {} are not registered.'.format(fixed.getBasename(),
                                                                                  moving.getBasename()))
        else: raise TypeError('Image parameters type is not SisypheVolume.')

    def getTransform(self) -> SisypheTransform:
        """
        Get the forward transform attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        SisypheTransform
            forward transfrom copy
        """
        return self._transform

    def getResampleTransform(self) -> SisypheTransform:
        """
        Get the backward transform attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        SisypheTransform
            backward transform copy
        """
        return self._transform.getInverseTransform()

    def getSITKTransform(self) -> sitkAffineTransform | sitkDisplacementFieldTransform:
        """
        Get forward transform attribute of the current SisypheApplyTransform instance as SimpleITK.Transform.

        Returns
        -------
        SimpleITK.AffineTransform | SimpleITK.DisplacementFieldTransform
            SimpleITK forward transform copy
        """
        return self._transform.getSITKTransform()

    def getSITKResampleTransform(self) -> sitkTransform:
        """
        Get backward transform attribute of the current SisypheApplyTransform instance as SimpleITK.Transform.

        Returns
        -------
        SimpleITK.Transform
            SimpleITK backward transform copy
        """
        return self._resample.GetTransform()

    def hasTransform(self) -> bool:
        """
        Check whether the transform attribute of the current SisypheApplyTransform instance is defined (not None).

        Returns
        -------
        bool
            True if geometric transform is defined
        """
        return self._transform is not None

    def hasAffineTransform(self) -> bool:
        """
        Check whether the transform attribute of the current SisypheApplyTransform instance is an affine geometric
        transformation.

        Returns
        -------
        bool
            True if geometric transform is defined and is an affine transformation
        """
        return self._transform is not None and self._transform.isAffine()

    def hasDisplacementFieldTransform(self) -> bool:
        """
        Check whether the transform attribute of the current SisypheApplyTransform instance is a displacement field
        transformation.

        Returns
        -------
        bool
            True if geometric transform is defined and is a displacement field transform
        """
        return self._transform is not None and self._transform.isDisplacementField()

    def setMoving(self, img: SisypheVolume) -> None:
        """
        Set the moving volume attribute of the current SisypheApplyTransform instance.

        Parameters
        ----------
        img : Sisyphe.core.sisypheVolume.SisypheVolume
            moving volume
        """
        if isinstance(img, SisypheImage):
            self._moving = img
            if isinstance(self._moving, SisypheBinaryImage):
                # Nearest Neighbor for binary image
                self._resample.SetInterpolator(sitkNearestNeighbor)
            if isinstance(self._moving, SisypheVolume):
                # Nearest Neighbor for label volume
                if self._moving.getAcquisition().isLB(): self._resample.SetInterpolator(sitkNearestNeighbor)
        else: raise TypeError('parameter type {} is not SisypheImage'.format(type(img)))

    def getMoving(self) -> SisypheVolume:
        """
        Get the moving volume attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            moving volume
        """
        return self._moving

    def hasMoving(self) -> bool:
        """
        Check whether the moving volume attribute of the current SisypheApplyTransform instance is defined (not None).

        Returns
        -------
        bool
            True if moving volume is defined
        """
        return self._moving is not None

    def clearMoving(self) -> None:
        """
        Clear the moving volume attribute of the current SisypheApplyTransform instance (set to none)
        """
        self._moving = None

    def setMovingROI(self, roi: SisypheROI) -> None:
        """
        Set the moving ROI attribute of the current SisypheApplyTransform instance.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            moving roi
        """
        if isinstance(roi, SisypheROI): self._roi = roi
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def getMovingROI(self) -> SisypheROI:
        """
        Get the moving ROI attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            moving roi
        """
        return self._roi

    def hasMovingROI(self) -> bool:
        """
        Check whether the moving ROI attribute of the current SisypheApplyTransform instance is defined (not None).

        Returns
        -------
        bool
            True if moving roi is defined
        """
        return self._roi is not None

    def clearMovingROI(self) -> None:
        """
        Clear the moving ROI attribute of the current SisypheApplyTransform instance (set to none)
        """
        self._roi = None

    def setMovingMesh(self, mesh: SisypheMesh) -> None:
        """
        Set the moving mesh attribute of the current SisypheApplyTransform instance.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            moving mesh
        """
        if isinstance(mesh, SisypheMesh): self._mesh = mesh
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def getMovingMesh(self) -> SisypheMesh:
        """
        Get the moving mesh attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        Sisyphe.core.sisypheMesh.SisypheMesh
            moving mesh
        """
        return self._mesh

    def hasMovingMesh(self) -> bool:
        """
        Check whether the moving mesh attribute of the current SisypheApplyTransform instance is defined (not None).

        Returns
        -------
        bool
            True if moving mes his defined
        """
        return self._mesh is not None

    def clearMesh(self) -> None:
        """
        Clear the moving mesh attribute of the current SisypheApplyTransform instance (set to none)
        """
        self._mesh = None

    def setMovingStreamlines(self, sl: SisypheStreamlines) -> None:
        """
        Set the moving streamlines attribute of the current SisypheApplyTransform instance.

        Parameters
        ----------
        sl : Sisyphe.core.sisypheTracts.SisypheStreamlines
            moving streamlines
        """
        if isinstance(sl, SisypheStreamlines): self._sl = sl
        else: raise TypeError('parameter type {} is not SisypheStreamlines.'.format(type(sl)))

    def getMovingStreamlines(self) -> SisypheStreamlines:
        """
        Get the moving streamlines attribute of the current SisypheApplyTransform instance.

        Returns
        -------
        Sisyphe.core.sisypheTracts.SisypheStreamlines
            moving streamlines
        """
        return self._sl

    def hasMovingStreamlines(self) -> bool:
        """
        Check whether the moving streamlines attribute of the current SisypheApplyTransform instance is defined
        (not None).

        Returns
        -------
        bool
            True if moving streamlines are defined
        """
        return self._sl is not None

    def clearMovingStreamlines(self) -> None:
        """
        Clear the moving streamlines attribute of the current SisypheApplyTransform instance (set to none)
        """
        self._sl = None

    def updateVolumeTransformsFromMoving(self, vol: SisypheVolume) -> None:
        """
        Copy the SisypheTransforms instance associated to the SisypheVolume moving volume to another SisypheVolume
        instance with the same ID (same space as moving volume)

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume SisypheTransforms is to be updated.
        """
        if self.hasAffineTransform() and self.hasMoving():
            if not isinstance(vol, SisypheVolume):
                raise TypeError('resampled parameter type {} is not SisypheVolume.'.format(type(vol)))
            # Template fixed volume is not updated
            if not vol.acquisition.isTP():
                if vol.getID() == self._moving.getID():
                    vtrfs = vol.getTransforms()
                    for trf in self._moving.getTransforms():
                        if trf.getID() not in vtrfs:
                            if trf.isAffine():
                                vtrfs.append(trf)
                # Save moving volume SisypheTransforms
                if vol.hasFilename(): vol.saveTransforms()
            else: raise ValueError('Incorrect ID of the parameter volume.')

    def updateTransforms(self,
                         resampled: SisypheVolume,
                         fixed: SisypheVolume | None) -> None:
        """
        Update the SisypheTransforms instance associated to fixed, moving and resliced volumes. Do not call this
        method, called by resampleMoving() method.

        - Add forward transform (moving -> fixed/resampled) to moving volume SisypheTransforms (mtrfs)
        - Add backward transform (resampled -> moving) to resampled volume SisypheTransforms (rtrfs)
        - Add backward transform (fixed -> moving) to fixed volume SisypheTransforms (ftrfs)
        - Update moving volume SisypheTransforms

            - Copy transforms from fixed volume to moving volume (mtrfs)
            - forward transform (moving -> fixed) pre multiplied by each fixed transforms

        - Update fixed volume SisypheTransforms

            - Copy transforms from moving volume to fixed volume (ftrfs)
            - backward transform (fixed -> moving) pre multiplied by each moving transforms

        - Update resampled volume SisypheTransforms

            - Copy transforms from fixed volume to resampled volume (rtrfs)
            - simple copy (fixed and resampled are registered and share same space)

        Parameters
        ----------
        resampled : Sisyphe.core.sisypheVolume.SisypheVolume
            resampled volume
        fixed : Sisyphe.core.sisypheVolume.SisypheVolume | None
            fixed volume (optional)
        """
        if self.hasAffineTransform() and self.hasMoving():
            if not isinstance(resampled, SisypheVolume):
                raise TypeError('resampled parameter type {} is not SisypheVolume.'.format(type(resampled)))
            forwardtrf = self._transform
            # < Revision 03/09/2024
            # add fixed attributes to forward transform
            if fixed is not None: forwardtrf.setAttributesFromFixedVolume(fixed)
            # Revision 03/09/2024 >
            backwardtrf = self._transform.getInverseTransform()
            backwardtrf.setAttributesFromFixedVolume(self._moving)
            """
                Add forward transform (moving -> fixed/resampled) to moving volume SisypheTransforms (mtrfs)
                Add backward transform (resampled -> moving) to resampled volume SisypheTransforms (rtrfs)
                Add backward transform (fixed -> moving) to fixed volume SisypheTransforms (ftrfs)
            """
            # Add forward transform (moving -> fixed/resampled) to moving volume
            mtrfs = self._moving.getTransforms()
            # Template fixed volume is not updated
            if not self._moving.acquisition.isTP():
                mtrfs.append(forwardtrf)
            # Add backward transform (resampled -> moving) to resampled volume
            rtrfs = resampled.getTransforms()
            rtrfs.append(backwardtrf)
            # Add backward transform (fixed -> moving) to fixed volume
            ftrfs = None
            # Template fixed volume is not updated
            if fixed is not None:
                if not fixed.acquisition.isTP():
                    ftrfs = fixed.getTransforms()
                    ftrfs.append(backwardtrf)
            """
                Update moving volume SisypheTransforms:    
                Copy transforms from fixed volume to moving volume (mtrfs)
                forward transform (moving -> fixed) pre multiplied by each fixed transforms
            """
            if ftrfs is not None:
                # Template fixed volume is not updated
                if not self._moving.acquisition.isTP():
                    # Copy transforms from fixed volume to moving volume (mtrfs)
                    if ftrfs.count() > 0:
                        for trf in ftrfs:
                            if trf.getID() != self._moving.getID():
                                if trf.getID() not in mtrfs:
                                    if trf.isAffine():
                                        ftrf = trf.copy()
                                        ftrf.postMultiply(forwardtrf, homogeneous=True)
                                        mtrfs.append(ftrf)
            """ 
                Update fixed volume SisypheTransforms:   
                Copy transforms from moving volume to fixed volume (ftrfs)
                backward transform (fixed -> moving) pre multiplied by each moving transforms
            """
            if ftrfs is not None:
                # Template fixed volume is not updated
                if not fixed.acquisition.isTP():
                    # Copy transforms from moving volume to fixed volume (ftrfs)
                    if mtrfs.count() > 0:
                        for trf in mtrfs:
                            if trf.getID() != fixed.getID():
                                if trf.getID() not in ftrfs:
                                    if trf.isAffine():
                                        mtrf = trf.copy()
                                        mtrf.postMultiply(backwardtrf, homogeneous=True)
                                        ftrfs.append(mtrf)
            """
                Update resampled volume SisypheTransforms:
                Copy transforms from fixed volume to resampled volume (rtrfs)
                simple copy (fixed and resampled are registered and share same space)
            """
            if ftrfs is not None:
                if ftrfs.count() > 0:
                    for trf in ftrfs:
                        if trf.getID() not in rtrfs:
                            if trf.isAffine():
                                rtrfs.append(trf)
            """
                Save moving volume SisypheTransforms
            """
            if self._moving.hasFilename():
                self._moving.saveTransforms()
            # Save fixed volume SisypheTransforms
            if fixed is not None:
                # < Revision 03/09/2024
                # add the TP modality condition below
                if not fixed.acquisition.isTP():
                    if fixed.hasFilename(): fixed.saveTransforms()
                # Revision 03/09/2024 >
        else: raise AttributeError('No SisypheTransform or moving SisypheVolume.')

    def resampleMoving(self,
                       fixed: SisypheVolume | None = None,
                       save: bool = True,
                       dialog: bool = False,
                       prefix: str | None = None,
                       suffix: str | None = None,
                       wait: DialogWait | None = None) -> SisypheVolume | None:
        """
        Reslice the moving volume attribute with the geometric transformation attribute of the current
        SisypheApplyTransform instance.

        Origin is not used during registration, origin must therefore be ignored at the resampling stage

        Origin management:

            - 1. moving volume origin is stored before resampling
            - 2. set moving volume origin to (0.0, 0.0, 0.0)
            - 3. moving volume resampling
            - 4. moving volume origin is restored
            - 5. copy moving volume attributes to resampled volume (identity, display, acquisition, acpc)
            - 6. copy fixed volume ID to resampled volume (same brain space)
            - 7. copy fixed volume origin to resampled volume

        Parameters
        ----------
        fixed : Sisyphe.core.sisypheVolume.SisypheVolume | None
            fixed volume (default None)
        save : bool
            save resliced moving volume if True (default)
        dialog : bool
            - dialog to choice the resliced moving volume file name, if True
            - addBundle suffix/prefix to the moving volume file name, if False (default)
        prefix : str | None
            file name prefix of the resliced moving volume (default None)
        suffix : str | None
            file name suffix of the resliced moving volume (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            resliced moving volume
        """
        if self.hasTransform():
            if self.hasMoving():
                if wait is not None:
                    if not wait.isVisible(): wait.open()
                    wait.setSimpleITKFilter(self._resample)
                    wait.addSimpleITKFilterProcessCommand()
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(self._moving.getBasename()))
                if isinstance(self._moving, SisypheBinaryImage): self._resample.SetInterpolator(sitkNearestNeighbor)
                elif self._moving.getAcquisition().isLB(): self._resample.SetInterpolator(sitkNearestNeighbor)
                resampled = SisypheVolume()
                # 1. Store moving volume origin
                origin = self._moving.getOrigin()
                # 2. Set moving volume origin to (0.0, 0.0, 0.0)
                self._moving.setDefaultOrigin()
                # < Revision 27/09/2024
                # set directions to default
                self._moving.setDefaultDirections()
                # Revision 27/09/2024 >
                # 3. moving volume resampling -> resampled volume
                if self._moving.getNumberOfComponentsPerPixel() == 1:
                    resampled.setSITKImage(self._resample.Execute(self._moving.getSITKImage()))
                else:
                    # < Revision 11/02/2025
                    # multicomponent resampling
                    series = list()
                    for i in range(self._moving.getNumberOfComponentsPerPixel()):
                        if wait is not None:
                            wait.setInformationText('Component {} resampling...'.format(i))
                        moving = self._moving.copyComponent(i)
                        r = SisypheVolume()
                        r.setSITKImage(self._resample.Execute(moving.getSITKImage()))
                        series.append(r)
                    resampled = multiComponentSisypheVolumeFromList(series)
                    # Revision 11/02/2025 >
                # 4. Restore moving volume origin
                self._moving.setOrigin(origin)
                # < Revision 05/09/2024
                if not self._moving.isDefaultOrigin():
                    if self._transform.isAffine():
                        resampled.setOrigin(self._transform.applyToPoint(self._moving.getOrigin()))
                # Revision 05/09/2024 >
                # 5. copy moving volume identity, acquisition, display, slope to resampled volume
                resampled.copyPropertiesFrom(self._moving, acpc=False)
                # if moving is a template, resampled is no longer a template, set its modality to OT
                if self._moving.acquisition.isTP():
                    resampled.acquisition.setModalityToOT()
                if fixed is not None:
                    # 6. copy fixed volume ID to resampled volume
                    resampled.setID(fixed.getID())
                    # 7. Copy fixed volume origin to resampled volume
                    resampled.setOrigin(fixed.getOrigin())
                    # 8. Copy fixed volume ACPC to resampled volume
                    if fixed.getACPC().hasACPC():
                        # copy fixed volume  SisypheACPC image attribute to resampled volume
                        acpc = fixed.getACPC().copy()
                        resampled.acpc = acpc
                """
                    Update geometric transformations of moving, fixed and resampled volumes:

                    1. Copy all transformations of moving volume to resampled volume,
                    2. Copy all transformations of moving volume to fixed volume,
                    updated (Post multiplication) with inverse of current transformation

                    3. Copy all transformations of fixed volume to moving volume
                    updated (Post multiplication) with current transformation
                    4. Copy all transformations of fixed volume to resample volume
                    simple copy (fixed and resampled share same space)
                """
                if self._transform.isAffine():
                    # < Revision 05/09/2024
                    # if fixed is None:
                    #    if not self._transform.hasID():
                    #        self._transform.setID(resampled)
                    # Revision 05/09/2024 >
                    self.updateTransforms(resampled, fixed)
                """
                    Save resampled volume
                """
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    # < Revision 22/05/2025
                    # add always an underscore char after prefix and before suffix
                    if len(prefix) > 0 and prefix[-1] != '_': prefix = prefix + '_'
                    if len(suffix) > 0 and suffix[0] != '_': suffix = '_' + suffix
                    # Revision 22/05/2025 >
                    path = dirname(self._moving.getFilename())
                    base, ext = splitext(self._moving.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled volume', filename,
                                                               filter=resampled.getFilterExt())[0]
                        if QApplication.instance() is not None: QApplication.processEvents()
                    if filename:
                        if wait is not None:
                            wait.progressVisibilityOff()
                            wait.setInformationText('Save {}...'.format(basename(filename)))
                        resampled.saveAs(filename)
                        if wait is not None: wait.hide()
                return resampled
            else: raise AttributeError('No moving SisypheVolume.')
        else: raise AttributeError('No SisypheTransform.')

    def resampleROI(self,
                    save: bool = True,
                    dialog: bool = False,
                    prefix: str | None = None,
                    suffix: str | None = None,
                    wait: DialogWait | None = None) -> SisypheROI | None:
        """
        Reslice the moving ROI attribute with the geometric transformation attribute of the current
        SisypheApplyTransform instance.

        Parameters
        ----------
        save : bool
            save resliced moving ROI if True (default)
        dialog : bool
            - dialog to choice the resliced moving ROI file name, if True
            - addBundle suffix/prefix to the moving ROI file name, if False (default)
        prefix : str | None
            file name prefix of the resliced moving ROI (default None)
        suffix : str | None
            file name suffix of the resliced moving ROI (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            resliced moving ROI
        """
        if self.hasTransform():
            if self.hasMovingROI():
                if wait is not None:
                    if not wait.isVisible(): wait.open()
                    wait.setSimpleITKFilter(self._resample)
                    wait.addSimpleITKFilterProcessCommand()
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(self._roi.getBasename()))
                interpolator = self.getInterpolator()
                self._resample.SetInterpolator(sitkNearestNeighbor)
                resampled = SisypheROI()
                resampled.setSITKImage(self._resample.Execute(self._roi.getSITKImage()))
                resampled.setReferenceID(self._transform.getID())
                resampled.setName(self._roi.getName())
                resampled.setColor(rgb=self._roi.getColor())
                resampled.setAlpha(self._roi.getAlpha())
                self._resample.SetInterpolator(interpolator)
                # Save resampled roi
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    # < Revision 22/05/2025
                    # add always an underscore char after prefix and before suffix
                    if len(prefix) > 0 and prefix[-1] != '_': prefix = prefix + '_'
                    if len(suffix) > 0 and suffix[0] != '_': suffix = '_' + suffix
                    # Revision 22/05/2025 >
                    path = dirname(self._roi.getFilename())
                    base, ext = splitext(self._roi.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled ROI', filename,
                                                               filter=resampled.getFilterExt())[0]
                        if QApplication.instance() is not None: QApplication.processEvents()
                    if filename:
                        if wait is not None:
                            wait.progressVisibilityOff()
                            wait.setInformationText('Save {}...'.format(basename(filename)))
                        resampled.saveAs(filename)
                        if wait is not None: wait.hide()
                return resampled
            else: raise AttributeError('No moving SisypheROI.')
        else: raise AttributeError('No SisypheTransform.')

    def resampleMesh(self,
                     save: bool = True,
                     dialog: bool = False,
                     prefix: str | None = None,
                     suffix: str | None = None,
                     wait: DialogWait | None = None) -> SisypheMesh | None:
        """
        Reslice the moving mesh attribute with the geometric transformation attribute of the current
        SisypheApplyTransform instance.

        Parameters
        ----------
        save : bool
            save resliced moving mesh if True (default)
        dialog : bool
            - dialog to choice the resliced moving mesh file name, if True
            - addBundle suffix/prefix to the moving mesh file name, if False (default)
        prefix : str | None
            file name prefix of the resliced moving mesh (default None)
        suffix : str | None
            file name suffix of the resliced moving mesh (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        Sisyphe.core.sisypheMesh.SisypheMesh
            resliced moving mesh
        """
        if self.hasTransform():
            if self.hasMovingMesh():
                n = self._mesh.getNumberOfPoints()
                if wait is not None:
                    if not wait.isVisible(): wait.open()
                    wait.setProgressRange(0, n)
                    wait.buttonVisibilityOn()
                    wait.setInformationText('Resample {}...'.format(self._mesh.getBasename()))
                resampled = SisypheMesh()
                resampled.copyFrom(self._mesh)
                points = self._mesh.getPoints()
                # Use forward transform to resample mesh vertices
                trf = self._transform.getInverseTransform()
                for i in range(n):
                    p = points.GetPoint(i)
                    points.SetPoint(i, trf.applyToPoint(p))
                    if wait is not None:
                        wait.incCurrentProgressValue()
                        if wait.getStopped(): return None
                self._mesh.setPoints(points)
                resampled.setReferenceID(self._transform.getID())
                resampled.setName(self._mesh.getName())
                resampled.copyPropertiesFromMesh(self._mesh)
                # Save resampled mesh
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    # < Revision 22/05/2025
                    # add always an underscore char after prefix and before suffix
                    if len(prefix) > 0 and prefix[-1] != '_': prefix = prefix + '_'
                    if len(suffix) > 0 and suffix[0] != '_': suffix = '_' + suffix
                    # Revision 22/05/2025 >
                    path = dirname(self._mesh.getFilename())
                    base, ext = splitext(self._mesh.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled Mesh', filename,
                                                               filter=resampled.getFilterExt())[0]
                        if QApplication.instance() is not None: QApplication.processEvents()
                    if filename:
                        if wait is not None:
                            wait.progressVisibilityOff()
                            wait.setInformationText('Save {}...'.format(basename(filename)))
                        resampled.saveAs(filename)
                        if wait is not None: wait.hide()
                return resampled
            else: raise AttributeError('No moving SisypheMesh.')
        else: raise AttributeError('No SisypheTransform.')

    def resampleStreamlines(self,
                            save: bool = True,
                            dialog: bool = False,
                            prefix: str | None = None,
                            suffix: str | None = None,
                            wait: DialogWait | None = None) -> SisypheStreamlines | None:
        """
        Reslice the moving streamlines attribute with the geometric transformation
        attribute of the current SisypheApplyTransform instance.

        Parameters
        ----------
        save : bool
            save resliced moving streamlines if True (default)
        dialog : bool
            - dialog to choice the resliced moving streamlines file name, if True
            - addBundle suffix/prefix to the moving streamlines file name, if False (default)
        prefix : str | None
            file name prefix of the resliced moving streamlines (default None)
        suffix : str | None
            file name suffix of the resliced moving streamlines (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (default None)

        Returns
        -------
        Sisyphe.core.sisypheTracts.SisypheStreamlines
            resliced moving streamlines
        """
        if self.hasTransform():
            if self.hasMovingStreamlines():
                if wait is not None:
                    if not wait.isVisible(): wait.open()
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(basename(self._sl.getFilename())))
                # Use forward transform to resample mesh vertices
                trf = self._transform.getInverseTransform()
                resampled = self._sl.applyTransformToStreamlines(trf, inplace=False)
                # Save resampled mesh
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    # < Revision 22/05/2025
                    # add always an underscore char after prefix and before suffix
                    if len(prefix) > 0 and prefix[-1] != '_': prefix = prefix + '_'
                    if len(suffix) > 0 and suffix[0] != '_': suffix = '_' + suffix
                    # Revision 22/05/2025 >
                    base, ext = splitext(self._sl.getFilename())
                    # noinspection PyTypeChecker
                    filename: str = join(self._sl.getDirname(), prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled streamlines', filename,
                                                               filter=resampled.getFilterExt())[0]
                        if QApplication.instance() is not None: QApplication.processEvents()
                    if filename:
                        if wait is not None:
                            wait.progressVisibilityOff()
                            wait.setInformationText('Save {}...'.format(basename(filename)))
                        resampled.save(bundle='all', filename=filename)
                        if wait is not None: wait.hide()
                return resampled
            else: raise AttributeError('No moving SisypheStreamlines.')
        else: raise AttributeError('No SisypheTransform.')

    def execute(self,
                fixed: SisypheVolume | None = None,
                save: bool = True,
                dialog: bool = False,
                prefix: str | None = None,
                suffix: str | None = None,
                wait: DialogWait | None = None) -> SisypheVolume | SisypheROI | SisypheMesh | SisypheStreamlines | None:
        """
        Reslice the moving volume, ROI, mesh and streamlines attributes ith the geometric transformation attribute of
        the current SisypheApplyTransform instance.

        Parameters
        ----------
        fixed : Sisyphe.core.sisypheVolume.SisypheVolume | None
            fixed volume (default None)
        save : bool
            save resliced moving volume if True (default)
        dialog : bool
            - dialog to choice the resliced moving volume file name, if True
            - addBundle suffix/prefix to the moving volume file name, if False (default)
        prefix : str | None
            file name prefix of the resliced moving volume (default None)
        suffix : str | None
            file name suffix of the resliced moving volume (default None)
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.sisypheROI.SisypheROI | Sisyphe.core.sisypheMesh.SisypheMesh | Sisyphe.core.sisypheTracts.SisypheStreamlines
            resliced moving attributes
        """
        if self.hasTransform():
            if self.hasMoving(): r = self.resampleMoving(fixed, save, dialog, prefix, suffix, wait)
            elif self.hasMovingROI(): r = self.resampleROI(save, dialog, prefix, suffix, wait)
            elif self.hasMovingMesh(): r = self.resampleMesh(save, dialog, prefix, suffix, wait)
            elif self.hasMovingStreamlines(): r = self.resampleStreamlines(save, dialog, prefix, suffix, wait)
            else: raise AttributeError('Nothing to resample.')
            return r
        else: raise AttributeError('No SisypheTransform.')


class SisypheTransformCollection(object):
    """
    Description
    ~~~~~~~~~~~

    Named list container of SisypheTransform instances. Container key to address elements can be an int index, a
    transform ID str, a SisypheTransform instance (its ID attribute is used as str key) or a SisypheVolume instance
    (its ID attribute is used as str key).

    Getter methods of the SisypheTransform class are added to the SisypheTransformCollection class, returning a list
    of values returned by each SisypheTransform element in the container.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTransformCollection

    Creation: 05/10/2021
    Last revision: 18/04/05/2025
    """

    __slots__ = ['_trfs', '_index']

    # Special methods

    """
    Private attributes

    _trfs       list[SisypheTransform]
    _index      int, index for Iterator   
    """

    def __init__(self) -> None:
        """
        SisypheTransformCollection instance constructor.
        """
        self._trfs = list()
        self._index = 0

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion ofSisypheTransformCollection instance to str
        """
        index = 0
        n = len(self._trfs)
        buff = 'Transform count #{}\n'.format(n)
        if n > 0:
            for trf in self._trfs:
                index += 1
                buff += 'Transform #{}:\n'.format(index)
                buff += '{}\n'.format(str(trf))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTransformCollection instance representation
        """
        return 'SisypheTransformCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container Public methods

    def __getitem__(self, key: int | str | SisypheVolume | slice | list[str]) -> SisypheTransform | SisypheTransforms:
        """
        Special overloaded container getter method. Get a SisypheTransform element from container, key which can be int
        index, ID, SisypheVolume (ID attribute), slicing indexes (start:stop:step) or list of ID.

        Parameters
        ----------
        key : int | str | Sisyphe.core.sisypheVolume.SisypheVolume | slice | list[str]
            index, ID, SisypheVolume (ID attribute), slicing indexes (start:stop:step) or list of ID

        Returns
        -------
        SisypheTransform | SisypheTransforms
            SisypheTransforms if key is slice or list[str]
        """
        # key is ID str
        if isinstance(key, (str, SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._trfs): return self._trfs[key]
            else: raise IndexError('key parameter is out of range.')
        elif isinstance(key, slice):
            trfs = SisypheTransforms()
            for i in range(key.start, key.stop, key.step):
                trfs.append(self._trfs[i])
            return trfs
        elif isinstance(key, list):
            trfs = SisypheTransforms()
            for i in range(len(self._trfs)):
                if self._trfs[i].getID() in key:
                    trfs.append(self._trfs[i])
            return trfs
        else: raise TypeError('parameter type {} is not int, str, slice or list[str].'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheTransform):
        """
        Special overloaded container setter method. Set a SisypheTransform element in the container.

        Parameters
        ----------
        key : int
            index
        value : SisypheTransform
            geometric transformation to be placed at key position
        """
        if isinstance(value, SisypheTransform):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._trfs):
                    if value.getID() in self: key = self.index(value)
                    self._trfs[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def __delitem__(self, key: int | str | SisypheTransform | SisypheVolume):
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheTransform element in
        the container.

        Parameters
        ----------
        key : int | str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume
            index, ID, SisypheTransform ID attribute or SisypheVolume ID attribute
        """
        # key is ID str, SisypheVolume or SisypheTransform
        if isinstance(key, (str, SisypheVolume, SisypheTransform)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._trfs):
                del self._trfs[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        """
        Special overloaded method called by the built-in len() python function. Returns the number of SisypheTransform
        elements in the container.

        Returns
        -------
        int
            number of SisypheTransform elements
        """
        return len(self._trfs)

    def __contains__(self, value: str | SisypheTransform | SisypheVolume) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a
        SisypheTransform is in the container.

        Parameters
        ----------
        value : str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume
            ID, SisypheTransform ID attribute or SisypheVolume ID attribute

        Returns
        -------
        bool
            True if value is in the container.
        """
        keys = [k.getID() for k in self._trfs]
        # value is SisypheTransform or SisypheVolume
        if isinstance(value, (SisypheTransform, SisypheVolume)):
            value = value.getID()
        # value is ID str
        if isinstance(value, str):
            return value in keys
        else: raise TypeError('parameter type {} is not str or SisypheTransform.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> SisypheTransform:
        """
        Special overloaded container called by the built-in 'next()' python iterator method. Returns the next value for
        the iterable.
        """
        if self._index < len(self._trfs):
            n = self._index
            self._index += 1
            return self._trfs[n]
        else:
            raise StopIteration

    def __getattr__(self, name: str):
        """
        Special overloaded method called when attribute does not exist in the class.
        Try iteratively calling the setter or getter methods of the sisypheTransform instances in the container.
        Getter methods return a list of the same size as the container.

        Parameters
        ----------
        name : str
            attribute name of the SisypheTransform class (container element)
        """
        prefix = name[:3]
        if prefix in ('set', 'get'):
            def func(*args):
                # SisypheTransform get methods or set methods without argument
                if len(args) == 0:
                    if prefix in ('get', 'set'):
                        if name in SisypheTransform.__dict__:
                            if prefix == 'get': return [trf.__getattribute__(name)() for trf in self]
                            else:
                                for trf in self: trf.__getattribute__(name)()
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                    else: raise AttributeError('Not get/set method')
                # SisypheVolume set methods with argument
                elif prefix == 'set':
                    p = args[0]
                    # SisypheTransform set method argument is list
                    if isinstance(p, (list, tuple)):
                        n = len(p)
                        if n == self.count():
                            if name in SisypheTransform.__dict__:
                                for i in range(n): self[i].__getattribute__(name)(p[i])
                            else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                        else: raise ValueError('Number of items in list ({}) '
                                               'does not match with {} ({}).'.format(p, self.__class__, self.count()))
                    # SisypheTransform set method argument is a single value (int, float, str, bool)
                    else:
                        if name in SisypheTransform.__dict__:
                            for trf in self: trf.__getattribute__(name)(p)
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
            return func
        raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Public methods

    def isEmpty(self) -> bool:
        """
        Checks if SisypheTransformCollection instance container is empty.

        Returns
        -------
        bool
            True if container is empty
        """
        return len(self._trfs) == 0

    def count(self) -> int:
        """
        Get the number of SisypheTransform elements in the current SisypheTransformCollection instance container.

        Returns
        -------
        int
            number of SisypheTransform elements
        """
        return len(self._trfs)

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current SisypheTransformCollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        return [k.getID() for k in self._trfs]

    def remove(self, value: int | str | SisypheTransform | SisypheVolume) -> None:
        """
         Remove a SisypheTransform element from the current SisypheTransformCollection instance container.

        Parameters
        ----------
        value : int | str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume
            index, ID, SisypheTransform ID attribute or SisypheVolume ID attribute
        """
        # value is SisypheTransform
        if isinstance(value, SisypheTransform): self._trfs.remove(value)
        # < Revision 18/04/2025
        # value is SisypheVolume, ID str or int index
        elif isinstance(value, (SisypheVolume, str)): value = self.index(value)
        if isinstance(value, int): self.pop(value)
        # Revision 18/04/2025 >
        else: raise TypeError('parameter type {} is not int, str or SisypheTransform.'.format(type(value)))

    def pop(self, key: int | str | SisypheTransform | SisypheVolume | None = None) -> SisypheTransform:
        """
         Remove a SisypheTransform element from the current SisypheTransformCollection instance container and return it.
         If key is None, removes and returns the last element.

        Parameters
        ----------
        key : int | str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume | None
            - index, ID, SisypheTransform ID attribute or SisypheVolume ID attribute
            - if None, remove the last element

        Returns
        -------
        SisypheTransform
            element removed from the container
        """
        if key is None: return self._trfs.pop()
        # key is ID str, SisypheVolume or SisypheTransform
        if isinstance(key, (str, SisypheTransform, SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._trfs.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def index(self, value: str | SisypheVolume | SisypheTransform) -> int:
        """
        Index of a SisypheTransform element in the current SisypheTransformCollection instance container.

        Parameters
        ----------
        value : str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume
            ID, SisypheTransform ID attribute or SisypheVolume ID attribute

        Returns
        -------
        int
            index
        """
        keys = [k.getID() for k in self._trfs]
        # value is SisypheTransform or SisypheVolume
        if isinstance(value, (SisypheTransform, SisypheVolume)):
            value = value.getID()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheTransform.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current SisypheTransformCollection instance container.
        """
        self._trfs.reverse()

    def append(self, value: SisypheTransform, replace: bool = True) -> None:
        """
        Append a SisypheTransform element in the current SisypheTransformCollection instance container.

        Parameters
        ----------
        value : SisypheTransform
            geometric transformation to append
        replace: bool
            if value is already in the current container, replace it (default True)
        """
        if isinstance(value, SisypheTransform):
            if value.getID() not in self: self._trfs.append(value)
            elif replace: self._trfs[self.index(value)] = value
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def insert(self,
               key: int | str | SisypheTransform | SisypheVolume,
               value: SisypheTransform) -> None:
        """
        Insert a SisypheTransform element at the position given by the key in the current SisypheTransformCollection
        instance container.

        Parameters
        ----------
        key : int | str | SisypheTransform | Sisyphe.core.sisypheVolume.SisypheVolume | None
            index, ID, SisypheTransform ID attribute or SisypheVolume ID attribute
        value : SisypheTransform
            geometric transformation to insert
        """
        if isinstance(value, SisypheTransform):
            # value is ID str, SisypheTransform or SisypheVolume
            if isinstance(key, (str, SisypheTransform, SisypheVolume)):
                key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._trfs):
                    if value.getID() not in self: self._trfs.insert(key, value)
                    else: self._trfs[self.index(value)] = value
                else: IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def clear(self) -> None:
        """
        Remove all elements from the current SisypheTransformCollection instance container (empty).
        """
        self._trfs.clear()

    def sort(self, reverse: bool = False) -> None:
        """
        Sort elements of the current SisypheTransformCollection instance container. Sorting is based on the ID
        attribute of the SisypheTransform elements, in the ascending order.

        Parameters
        ----------
        reverse : bool
            sorting in reverse order
        """
        def _getID(item):
            return item.getID()

        self._trfs.sort(reverse=reverse, key=_getID)

    def copy(self) -> SisypheTransformCollection:
        """
        Copy the current SisypheTransformCollection instance container (Shallow copy of elements).

        Returns
        -------
        SisypheTransformCollection
            Shallow copy of container
        """
        trfs = SisypheTransformCollection()
        for trf in self._trfs:
            trfs.append(trf)
        return trfs

    def copyToList(self) -> list[SisypheTransform]:
        """
        Copy the current SisypheTransformCollection instance container to a list (Shallow copy of elements).

        Returns
        -------
        list[SisypheTransform]
            shallow copy to list of container elements
        """
        trfs = self._trfs.copy()
        return trfs

    def getList(self) -> list[SisypheTransform]:
        """
        Get the list attribute of the current SisypheTransformCollection instance container (Shallow copy)

        Returns
        -------
        list[SisypheTransform]
            shallow copy of container list
        """
        return self._trfs


class SisypheTransforms(SisypheTransformCollection):
    """
    Description
    ~~~~~~~~~~~

    Each SisypheVolume is associated with a SisypheTransforms instance, which stores all the geometric transformations
    calculated from co-registrations with other SisypheVolume instances.

    This class works as a named list (key/value) container of SisypheTransform instances.

    - Key: ID attribute of a SisypheVolume that is co-registered with the reference SisypheVolume.
    - Value: the geometric transformation (SisypheTransform instance) used to co-register the SisypheVolume with the
    reference SisypheVolume.

    Inherits from SisypheTransformCollection class and adds

    - ID attribute of the associated (or reference) SisypheVolume instance,
    - IO methods.

    Geometric transformations are in forward convention (apply inverse transformation to resample)

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTransformCollection -> SisypheTransforms

    Creation: 05/10/2021
    Last revision: 23/05/2024
    """
    __slots__ = ['_referenceID', '_filename', '_parent']

    # Class constant

    _FILEEXT = '.xtrfs'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheTransforms file extension.

        Returns
        -------
        str
            '.xtrfs'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheTransforms filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Geometric transformation collection (.xtrfs)'
        """
        return 'PySisyphe Geometric transformation collection (*{})'.format(cls._FILEEXT)

    @classmethod
    def openTransforms(cls, filename) -> SisypheTransforms:
        """
        create a SisypheTransforms instance from PySisyphe
        geometric transformation collection file (.xtrfs).

        Parameters
        ----------
        filename : str
            geometric transformation collection file name

        Returns
        -------
        SisypheTransforms
            loaded geometric transformation collection
        """
        if exists(filename):
            filename = basename(filename) + cls.getFileExt()
            trfs = SisypheTransforms()
            trfs.load(filename)
            return trfs
        else: raise FileExistsError('No such file {}'.format(filename))

    # Special methods

    """
    Private attributes

    _ID         str, ID of the SisypheVolume parent instance
    _filename   str, filename to save instance    
    """

    def __init__(self, parent: SisypheVolume | None = None) -> None:
        """
        SisypheTransforms instance constructor.

        Parameters
        ----------
        parent : Sisyphe.core.sisypheVolume.SisypheVolume | None
            Associated SisypheVolume instance (default None)
        """
        super().__init__()
        self._referenceID = None  # reference SisypheVolume ID
        self._filename = ''
        if not isinstance(parent, SisypheVolume): parent = None
        if parent is not None: self.setReferenceID(parent)

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheTransforms instance to str
        """
        buff = 'Reference ID: {}\n'.format(self.getReferenceID())
        buff += 'Filename: {}\n'.format(basename(self.getFilename()))
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTransforms instance representation
        """
        return 'SisypheTransforms instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container Public methods

    def __getitem__(self, key: int | str | SisypheVolume | slice | list[str]) -> SisypheTransform | SisypheTransforms:
        """
        Special overloaded container getter method. Get a SisypheTransform element from container, Key which can be int
        index, ID, SisypheVolume (ID attribute), slicing indexes (start:stop:step) or list of ID.

        Parameters
        ----------
        key : int | str | Sisyphe.core.sisypheVolume.SisypheVolume | slice | list[str]
            index, ID, SisypheVolume ID attribute, slicing indexes (start:stop:step) or list of ID

        Returns
        -------
        SisypheTransform | SisypheTransforms
            SisypheTransforms if key is slice or list[str]
        """
        r = super().__getitem__(key)
        if isinstance(r, SisypheTransforms):
            r.setReferenceID(self.getReferenceID())
        return r

    # Public methods

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current SisypheTransforms instance. The reference ID is the ID of the
        associated SisypheVolume.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def setReferenceID(self, ID: str | SisypheVolume) -> None:
        """
        Set the reference ID attribute of the current SisypheTransforms instance. The reference ID is the ID of the
        associated SisypheVolume.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            ID or SisypheVolume's ID attribute
        """
        if isinstance(ID, str):
            self._referenceID = ID
        elif isinstance(ID, SisypheVolume):
            self._referenceID = ID.getID()
            self.setFilenameFromVolume(ID)
        else:
            self._referenceID = None

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID of the current SisypheTransforms instance is defined (not ''). The reference ID is
        the ID of the associated SisypheVolume.

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID is not None

    def hasFilename(self) -> bool:
        """
        Check whether the file name attribute of the current SisypheTransforms instance is defined.

        Returns
        -------
        bool
            True if file name attribute is defined
        """
        if self._filename != '':
            if exists(self._filename): return True
            else: self._filename = ''
        return False

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current SisypheTransforms instance is defined.

        Returns
        -------
        str
            file name attribute
        """
        return self._filename

    def setFilenameFromVolume(self, img: SisypheVolume) -> None:
        """
        Copy the file name attribute of the current SisypheTransforms instance from the file name attribute of a
        SisypheVolume instance.

        Parameters
        ----------
        img : Sisyphe.core.sisypheVolume.SisypheVolume
            volume filename to copy
        """
        if isinstance(img, SisypheVolume):
            if img.hasFilename():
                path, ext = splitext(img.getFilename())
                path += self._FILEEXT
                self._filename = path
            else:
                self._filename = ''
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(img))

    def appendIdentityTransformWithVolume(self, vol: SisypheVolume) -> None:
        """
        Add an identity geometric transformation with a SisypheVolume (parameter) in the current SisypheTransforms
        instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume (volume ID key) to associate with an identity tranform
        """
        if isinstance(vol, SisypheVolume):
            trf = SisypheTransform()
            trf.setIdentity()
            trf.setAttributesFromFixedVolume(vol)
            self.append(trf)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def copy(self) -> SisypheTransforms:
        """
        Copy the current SisypheTransforms instance container (Shallow copy of elements).

        Returns
        -------
        SisypheTransforms
            container shallow copy
        """
        trfs = SisypheTransforms()
        for trf in self._trfs:
            trfs.append(trf)
        return trfs

    # IO public methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheTransforms instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('referenceID')
            root.appendChild(node)
            txt = doc.createTextNode(str(self.getReferenceID()))
            node.appendChild(txt)
            # SisypheTransform nodes
            for trf in self._trfs:
                # Save only affine transformations, not displacement field
                if trf.isAffine():
                    trf.createXML(doc, root)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXML(self, doc: minidom.Document) -> None:
        """
        Read the current SisypheTransforms instance attributes from xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.clear()
                node = root.firstChild
                while node:
                    # ID
                    if node.nodeName == 'referenceID':
                        self.setReferenceID(node.firstChild.data)
                    elif node.nodeName == 'transform':
                        trf = SisypheTransform()
                        trf.parseXMLNode(node)
                        self.append(trf)
                    node = node.nextSibling
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
        """
        Save the current SisypheTransforms instance to a PySisyphe geometric transformation collection file (.xtrfs).

        Parameters
        ----------
        filename : str
            - PySisyphe geometric transformation collection file name
            - The file name attribute of the current SisypheTransforms instance is replaced by this parameter
        """
        if not self.isEmpty():
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT:
                filename = path + self._FILEEXT
            doc = minidom.Document()
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            self.createXML(doc)
            buff = doc.toprettyxml()
            f = open(filename, 'w')
            try: f.write(buff)
            except IOError: raise IOError('{} XML file write error.'.format(basename(filename)))
            finally: f.close()
            self._filename = filename
        else: raise AttributeError('SisypheTransform instance is empty.')

    def save(self, filename: str = '') -> None:
        """
        Save the current SisypheTransforms instance to a PySisyphe geometric
        transformation collection file (.xtrfs).

        Parameters
        ----------
        filename : str
            PySisyphe geometric transformation collection file name (optional)
            if filename is empty ('', default), the file name attribute of the current SisypheTransforms instance is used
        """
        if not self.isEmpty():
            if self.hasFilename():
                filename = self._filename
            if filename != '':
                self.saveAs(filename)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('SisypheTransform instance is empty.')

    def load(self, filename: str = '') -> None:
        """
        Load the current SisypheTransforms instance from a PySisyphe geometric transformation collection file (.xtrfs).

        Parameters
        ----------
        filename : str
            - PySisyphe geometric transformation collection file name (optional)
            - if filename is empty ('', default), the file name attribute of the current SisypheTransforms instance is used
        """
        if self.hasFilename() and exists(self._filename):
            filename = self._filename
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            self.parseXML(doc)
            self._filename = filename
        else: raise FileNotFoundError('no such file : {}'.format(basename(filename)))
