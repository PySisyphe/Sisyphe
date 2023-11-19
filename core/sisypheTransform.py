"""
    External packages/modules

        Name            Link                                                        Usage

        ANTs            http://stnava.github.io/ANTs/                               Image registration
        DIPY            https://www.dipy.org/                                       MR diffusion image processing
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        Scipy           https://docs.scipy.org/doc/scipy/index.html                 Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import splitext
from os.path import split
from os.path import join

from math import radians
from math import degrees
from math import cos
from math import asin
from math import atan2
from math import pi

from xml.dom import minidom

from dipy.align.streamlinear import decompose_matrix44

from numpy import array as nparray
from numpy import ndarray as npndarray
from numpy import matmul
from numpy import diag
from numpy import degrees as npdegrees

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
from SimpleITK import Euler3DTransform as sitkEuler3DTransform
from SimpleITK import VersorTransform as sitkVersorTransform
from SimpleITK import ScaleSkewVersor3DTransform as sitkScaleSkewVersor3DTransform
from SimpleITK import DisplacementFieldTransform as sitkDisplacementFieldTransform
from SimpleITK import ReadTransform as sitkReadTransform
from SimpleITK import TransformToDisplacementFieldFilter as sitkTransformToDisplacementFieldFilter
from SimpleITK import ResampleImageFilter as sitkResampleImageFilter

from ants.core.ants_transform import ANTsTransform
from ants.core.ants_transform_io import read_transform
from ants.core.ants_transform_io import write_transform

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

import Sisyphe.core as sc
from Sisyphe.lib.bv.trf import read_trf
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheImage import SisypheBinaryImage
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheTransform',
           'SisypheApplyTransform',
           'SisypheTransformCollection',
           'SisypheTransforms',
           'getVersorFromRotations',
           'getRotationsFromVersor']

vectorFloat3 = list[float, float, float] | tuple[float, float, float]
vectorFloat4 = list[float, float, float, float] | tuple[float, float, float, float]
vectorInt3 = list[int, int, int] | tuple[int, int, int]

"""
    Functions
    
        getVersorFromRotations
        getRotationsFromVersor
        
    Revisions:
    
        01/09/2023  type hinting
"""


def getVersorFromRotations(r: vectorFloat3) -> vectorFloat4:
    # return vector x, y, z and rotation
    euler = sitkEuler3DTransform()
    versor = sitkVersorTransform()
    euler.SetRotation(r[0], r[1], r[2])
    versor.SetMatrix(euler.GetMatrix())
    return versor.GetVersor()

def getRotationsFromVersor(v: vectorFloat4) -> vectorFloat3:
    # parameter v: vector x, y, z and rotation
    euler = sitkEuler3DTransform()
    versor = sitkVersorTransform(v)
    euler.SetMatrix(versor.GetMatrix())
    return euler.GetAngleX(), euler.GetAngleY(), euler.GetAngleZ()


"""
    Class hierarchy

        object -> SisypheTransform
               -> SisypheApplyTransform
               -> SisypheTransformCollection -> SisypheTransforms
"""


class SisypheTransform(object):
    """
        SisypheTransform class

        Description

            Geometric centered transformation class.
            Uses forward convention, transformation of fixed to floating volume coordinates.
            To resample floating volume, apply the inverse i.e. backward transformation.
            Privates attributes ID, spacing and size were those of the fixed image (resampling space)

        Inheritance

            object -> SisypheTransform

        Private attributes

            _ID         str, ID of floating image,  fixed volume ID
            _name       str
            _size       [int, int, int],            fixed volume size
            _spacing    [float, float, float],      fixed volume spacing
            _transform  sitkAffineTransform         backward transformation, fixed coordinates to moving coordinates
            _field      sitkDisplacementFieldTransform
            _fieldname  str

        Class methods

            str = getFileExt()
            str = getFilterExt()
            numpy array = getSITKtoNumpy(sitkAffineTransform or sitkEuler3DTransform)
            numpy array = getVTKtoNumpy(sitkAffineTransform or sitkEuler3DTransform)

        Public methods

            __str__()
            __repr__()
            setIdentity()
            bool = isIdentity(self)
            SisypheTransform = getInverseTransform()
            setTranslations([float, float, float])
            addTranslations([float, float, float])
            setRotations([float, float, float], deg=bool)
            setVersor([float, float, float], float)
            setScales([float, float, float])
            setSkews([float, float, float float float float])
            [float, float, float] = getRotations(deb=bool)
            setCenter([float, float, float])
            SisypheTransform = getEquivalentTransformWithNewCenterOfRotation([float, float, float])
            setCenterFromSisypheVolume(SisypheVolume)
            [float, float, float] = getCenter()
            bool = hasCenter()
            SisypheTransform = copy()
            SisypheTransform = copyEquivalentVolumeCenteredTransform()
            copyTo(SisypheTransform)
            SisypheTransform = copy()
            setSITKTransform(sitkTransform)
            sitkTransform = getSITKTransform(self)
            sitkDisplacementFieldTransform = getSITKDisplacementFieldTransform(self)
            sitkImage = getSITKDisplacementFieldSITKImage(self)
            sitkTransform = getInverseSITKTransform()
            setSITKDisplacementFieldTransform(sitkDisplacementFieldTransform)
            setSITKDisplacementFieldImage(SisypheVolume | SisypheImage | sitkImage)
            removeDisplacementField()
            setVTKTransform(VTKTransform)
            VTKTransform = getVTKTransform()
            setVTKMatrix3x3(VTKMatrix3x3)
            setVTKMatrix4x4(VTKMatrix4x4)
            VTKMatrix4x4 = getVTKMatrix4x4()
            VTKMatrix3x3 = getVTKMatrix3x3()
            VTKTransform = getInverseVTKTransform()
            NDArray = getNumpyArray(homogeneous=bool)
            setNumpyArray(NDArray)
            setANTSTransform(ANTSTranform)
            ANTSTranform = getANTSTransform()
            list of float = getMatrixColumn()
            list of float = getFlattenMatrix(self, homogeneous=False)
            setFlattenMatrix(list of float)
            applyToPoint([float, float, float])
            preMultiply(vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkEuler3DTransform or NDArray, homogeneous=bool)
            postMultiply(vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkEuler3DTransform or NDArray, homogeneous=bool)
            bool = isDisplacementFieldTransform()
            bool = isAffineTransform()
            AffineToDisplacementField()
            bool = hasID()
            str = getID()
            setID(str)
            [float, float, float] = getSpacing()
            setSpacing([float, float, float])
            bool = hasSpacing()
            [int, int, int] = getSize(self)
            setSize([int, int, int])
            bool = hasSize()
            setAttributesFromFixedVolume(SisypheVolume)
            copyAttributesTo(SisypheTransform)
            copyAttributesFrom(SisypheTransform)
            bool = hasFixedVolumeAttributes()
            bool = hasSameFixedVolumeAttributes(SisypheVolume)
            saveAs(str)
            load(str)
            saveToXfmTransform(str)
            saveToTfmTransform(str)
            saveToMatfileTransform(str)
            saveToTxtTransform(str)
            saveToANTSTransform(str)
            loadFromXfmTransform(str)
            loadFromTfmTransform(str)
            loadFromMatfileTransform(str)
            loadFromTxtTransform(str)
            loadFromANTSTransform(str)
            loadFromBrainVoyagerTransform(str)

        Creation: 05/10/2021
        Revision:

            24/04/2023  displacement field IO methods debugged (sitkVectorFloat32 and sitkVectorFloat64 conversion)
            20/07/2023  added loadFromBrainVoyagerTransform IO method, open brainvoyager *.trf transform
            01/09/2023  type hinting
            31/10/2023  add openTransform() class method
    """
    __slots__ = ['_parent', '_name', '_ID', '_size', '_spacing', '_transform', '_affine', '_field', '_fieldname']

    # Class constant

    _FILEEXT = '.xtrf'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Geometric transformation (*{})'.format(cls._FILEEXT)

    @classmethod
    def getSITKtoNumpy(cls, trf: sitkAffineTransform | sitkEuler3DTransform) -> npndarray:
        if isinstance(trf, (sitkAffineTransform, sitkEuler3DTransform)):
            m = list(trf.GetMatrix())
            t = list(trf.GetTranslation())
            m = m[:3] + [t[0]] + m[3:6] + [t[1]] + m[-3:] + [t[2], 0.0, 0.0, 0.0, 1.0]
            return nparray(m).reshape(4, 4)
        else: raise TypeError('parameter type {} is not sitkAffineTransform or sitkEuler3DTransform.'.format(type(trf)))

    @classmethod
    def getVTKtoNumpy(cls, trf: vtkMatrix4x4) -> npndarray:
        if isinstance(trf, vtkMatrix4x4):
            m = npndarray((4, 4))
            for r in range(3):
                for c in range(3):
                    m[r, c] = trf.GetElement(r, c)
            return m
        else: raise TypeError('parameter type {} is not vtkMatrix4x4.'.format(type(trf)))

    @classmethod
    def openTransform(cls, filename: str) -> SisypheTransform:
        filename = basename(filename) + cls.getFileExt()
        trf = SisypheTransform()
        trf.load(filename)
        return trf

    # Special methods

    def __init__(self, parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        self._transform = sitkAffineTransform(3)
        self._affine = sitkScaleSkewVersor3DTransform()
        self._field = None
        self._fieldname = ''
        if parent and isinstance(parent, sc.sisypheVolume.SisypheVolume):
            self._ID = parent.getID()
            self._name = parent.getName()
            self._size = parent.getSize()
            self._spacing = parent.getSpacing()
            self._transform.SetCenter(parent.getCenter())
        else:
            self._ID = ''  # floating SisypheVolume ID
            self._name = ''
            self._size = (0, 0, 0)
            self._spacing = (0.0, 0.0, 0.0)
            self.setCenter((0.0, 0.0, 0.0))
        self._parent = parent

    def __str__(self) -> str:
        buff = 'ID: {}\n'.format(self.getID())
        buff += 'Name: {}\n'.format(self.getName())
        buff += 'Size: {}\n'.format(self.getSize())
        p = self.getSpacing()
        buff += 'Spacing: [{[0]:.2f} {[1]:.2f} {[2]:.2f}]\n'.format(p, p, p)
        p = self.getCenter()
        buff += 'Center: [{[0]:.2f} {[1]:.2f} {[2]:.2f}]\n'.format(p, p, p)
        if self._field is None:
            buff += 'Affine transform\n'
            p = self.getTranslations()
            buff += '  Translations: [{[0]:.1f} {[1]:.1f} {[2]:.1f}]\n'.format(p, p, p)
            p = self.getRotations(deg=True)
            if p is not None:
                buff += '  Rotations: \n'
                buff += '    degrees [{[0]:.1f} {[1]:.1f} {[2]:.1f}]\n'.format(p, p, p)
                p = self.getRotations(deg=False)
                buff += '    radians [{[0]:.3f} {[1]:.3f} {[2]:.3f}]\n'.format(p, p, p)
                p = self.getVersor()
                buff += '    versor [{[0]:.3f} {[1]:.3f} {[2]:.3f} {[3]:.3f}]\n'.format(p, p, p, p)
            else: buff += '  Rotations: Non-orthogonal affine matrix\n'
            buff += '  Matrix:\n'
            m = self._transform.GetMatrix()
            p = m[:3]
            buff += '    [{[0]:7.4f} {[1]:7.4f} {[2]:7.4f} ]\n'.format(p, p, p)
            p = m[3:6]
            buff += '    [{[0]:7.4f} {[1]:7.4f} {[2]:7.4f} ]\n'.format(p, p, p)
            p = m[-3:]
            buff += '    [{[0]:7.4f} {[1]:7.4f} {[2]:7.4f} ]\n'.format(p, p, p)
        else:
            buff += 'Displacement Field transform\n'
            if self._fieldname == '': name = 'Not yet saved'
            else: name = self._fieldname
            buff += '  Filename: {}\n'.format(name)
        buff += 'Memory size: {} Bytes\n'.format(self.__sizeof__())
        return buff

    def __repr__(self) -> str:
        return 'SisypheTransform instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def hasParent(self) -> bool:
        return self._parent is not None

    def getParent(self) -> sc.sisypheVolume.SisypheVolume | None:
        return self._parent

    def setParent(self, parent: sc.sisypheVolume.SisypheVolume) -> None:
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if parent and isinstance(parent, SisypheVolume):
            self.setID(parent)
            self._size = parent.getSize()
            self._spacing = parent.getSpacing()
            self._transform.SetCenter(parent.getCenter())

    def setName(self, name: str) -> None:
        self._name = splitext(basename(name))[0]

    def getName(self) -> str:
        return self._name

    def hasName(self) -> bool:
        return self._name != ''

    def setIdentity(self) -> None:
        # Copy center
        c = self._transform.GetCenter()
        # SetIdentity clear center
        self._affine.SetIdentity()
        self._transform.SetIdentity()
        # Set center
        self._transform.SetCenter(c)

    def isIdentity(self) -> bool:
        if self._field is None:
            return self._transform.GetMatrix() == (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0) and \
                   self._transform.GetTranslation() == (0.0, 0.0, 0.0)
        else: raise TypeError('Displacement field transform.')

    def getInverseTransform(self) -> SisypheTransform:
        if self._field is None:
            trf = SisypheTransform()
            trf.setSITKTransform(sitkAffineTransform(self._transform.GetInverse()))
            trf.setID(self.getID())
            trf.setSize(self.getSize())
            trf.setSpacing(self.getSpacing())
            return trf
        else: raise TypeError('Displacement field transform.')

    def setTranslations(self, t: vectorFloat3) -> None:
        if self._field is None: self._transform.SetTranslation(t)
        else: raise TypeError('Displacement field transform has no translation parameter.')

    def setRotations(self, r: vectorFloat3, deg: bool = False) -> None:
        if self._field is None:
            r = list(r)
            if deg:
                r[0] = radians(r[0])
                r[1] = radians(r[1])
                r[2] = radians(r[2])
            self._affine.SetRotation(getVersorFromRotations(r))
            self._transform.SetMatrix(self._affine.GetMatrix())
        else: raise TypeError('Displacement field transform has no rotation parameter.')

    def addTranslations(self, t: vectorFloat3) -> None:
        if self._field is None:
            t2 = list(self.getTranslations())
            t2[0] += t[0]
            t2[1] += t[1]
            t2[2] += t[2]
            self.setTranslations(t2)
        else: raise TypeError('Displacement field transform has no translation parameter.')

    def composeRotations(self, r: vectorFloat3, deg: bool = False) -> None:
        if self._field is None:
            trf = SisypheTransform()
            trf.setRotations(r, deg)
            self.preMultiply(trf, homogeneous=True)
        else: raise TypeError('Displacement field transform has no rotation parameter.')

    def composeTransform(self, trf: SisypheTransform) -> None:
        if self._field is None:
            if isinstance(trf, SisypheTransform):
                self.preMultiply(trf, homogeneous=True)
            else: raise TypeError('parameter type {} is not SisypheTransform'.format(trf))
        else: raise TypeError('Displacement field transform has no affine matrix parameter.')

    def setVersor(self, v: vectorFloat4) -> None:
        if self._field is None:
            self._affine.SetRotation(v)
            self._transform.SetMatrix(self._affine.GetMatrix())
        else: raise TypeError('Displacement field transform has no versor parameter.')

    def setScales(self, sc: vectorFloat3) -> None:
        if self._field is None:
            self._affine.SetScale(sc)
            self._transform.SetMatrix(self._affine.GetMatrix())
        else: raise TypeError('Displacement field transform has no scale parameter.')

    def setSkews(self, sk: vectorFloat3) -> None:
        if self._field is None:
            self._affine.SetSkew(sk)
            self._transform.SetMatrix(self._affine.GetMatrix())
        else: raise TypeError('Displacement field transform has no skew parameter.')

    def getTranslations(self) -> vectorFloat3:
        return tuple(self._transform.GetTranslation())

    def getRotations(self, deg: bool = False) -> vectorFloat3 | None:
        t = sitkEuler3DTransform()
        try: t.SetMatrix(self._transform.GetMatrix())
        except: return None
        if deg: return degrees(t.GetAngleX()), degrees(t.GetAngleY()), degrees(t.GetAngleZ())
        else: return t.GetAngleX(), t.GetAngleY(), t.GetAngleZ()

    def getRotationsFromMatrix(self, deg: bool = False, algo: str = 'dipy') -> vectorFloat3:
        if algo == 'dipy':
            r = decompose_matrix44(self.getNumpyArray(homogeneous=True), size=12)
            if deg: r = npdegrees(r[3:6])
            else: r = r[3:6]
            return tuple(r)
        else:
            def rang(v):
                return min(max(v, -1), 1)
            """
                from matlab code spm_imatrix, John Ashburner & Stefan Kiebel
            """
            # retrieve zooms
            r = self.getNumpyArray()
            C = cholesky(r.T @ r)
            z = diag(C)  # zooms
            if det(r) < 0: z[0] = -z[0]
            Z = diag(z)
            # retrieve shears
            C = solve(diag(diag(C)), C)
            s = [C[1, 0], C[2, 0], C[2, 1]]  # shears
            S = nparray([[1, C[1, 0], C[2, 0]],
                         [0, 1,       C[2, 1]],
                         [0, 0,       1]])
            # finally, retrieve rotations
            R0 = Z @ S
            R1 = solve(r.T, R0.T)
            R1 = R1.T
            r2 = -asin(rang(R1[0, 2]))
            if (abs(r2) - pi/2) ** 2 < 1e-9:
                r1 = 0
                r3 = atan2(-rang(R1[1, 0]), rang(-R1[2, 0] / R1[0, 2]))
            else:
                c = cos(r2)
                r1 = atan2(rang(R1[1, 2] / c), rang(R1[2, 2] / c))
                r3 = atan2(rang(R1[0, 1] / c), rang(R1[0, 0] / c))
            if deg:
                r1 = degrees(r1)
                r2 = degrees(r2)
                r3 = degrees(r3)
            return r1, r2, r3

    def getVersor(self) -> vectorFloat4:
        r = self.getRotations()
        return list(getVersorFromRotations(r))

    def setCenter(self, c: vectorFloat3) -> None:
        self._transform.SetCenter(c)

    def getEquivalentTransformWithNewCenterOfRotation(self, c: vectorFloat3) -> SisypheTransform:
        """
            1. Apply forward translation, mid CA-CP to volume center (translation = volume center - mid CA-CP)
            2. Apply rotation, after forward translation, center of rotation is volume center
            3. Apply backward translation, volume center to mid CA-CP
        """
        if self.hasCenter():
            newc = list(c)
            oldc = self.getCenter()
            newc[0] -= oldc[0]
            newc[1] -= oldc[1]
            newc[2] -= oldc[2]
            """
                t1 = forward translation transformation matrix
                forward translation of the center of rotation from mid CA-CP to volume center
                translation = volume center (c) - mid CA-CP (m)
            """
            t1 = SisypheTransform()
            t1.setTranslations(newc)
            """
                rt2 = roto-translation matrix = backward translation transformation x rotation transformation
                backward translation from volume center to mid CA-CP
                backward translation = - forward translation
                Order of transformations is 1. rotation -> 2. backward translation
            """
            rt2 = SisypheTransform()
            rt2.setRotations(self.getRotations())
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
            return t1
        else:
            t = self.copy()
            t.setCenter(c)
            return t

    def setCenterFromSisypheVolume(self, vol: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(vol, sc.sisypheVolume.SisypheVolume): self._transform.SetCenter(vol.getCenter())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def isCenteredToSisypheVolume(self, vol: sc.sisypheVolume.SisypheVolume) -> bool:
        if isinstance(vol, sc.sisypheVolume.SisypheVolume):
            c1 = self.getCenter()
            c2 = list(vol.getCenter())
            return c1 == c2
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setCenterFromParent(self) -> None:
        if self.hasParent():
            self.setCenterFromSisypheVolume(self._parent)

    def isCenteredFromParent(self) -> bool:
        if self.hasParent():
            return self.isCenteredToSisypheVolume(self._parent)

    def getCenter(self) -> vectorFloat3:
        return list(self._transform.GetCenter())

    def hasCenter(self) -> bool:
        return self._transform.GetCenter() != (0.0, 0.0, 0.0)

    def copyFrom(self, t: sc.sisypheVolume.SisypheVolume | SisypheTransform) -> None:
        if isinstance(t, sc.sisypheVolume.SisypheVolume):
            t = t.getTransforms()
        if isinstance(t, SisypheTransform):
            if t.isDisplacementFieldTransform():
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
        t = SisypheTransform()
        self.copyTo(t)
        return t

    def setSITKTransform(self, trf):
        name = trf.GetName()
        if name != 'DisplacementFieldTransform':
            self.setIdentity()
            if name == 'TranslationTransform':
                self._transform.SetTranslation(trf.GetOffset())
            elif name == 'VersorTransform':
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleTransform':
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'VersorRigid3DTransform':
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'Euler3DTransform':
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'Similarity3DTransform':
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleVersor3DTransform':
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'ScaleSkewVersor3DTransform':
                self._transform.SetTranslation(trf.GetTranslation())
                self._transform.SetMatrix(trf.GetMatrix())
            elif name == 'AffineTransform':
                self._transform = trf
            else: raise TypeError('transform type {} is not supported.'.format(type(trf)))
        else: self.setSITKDisplacementFieldTransform(trf)

    def getSITKTransform(self) -> sitkAffineTransform | sitkDisplacementFieldTransform:
        if self._field is None: return self._transform
        else: return self._field

    def getSITKDisplacementFieldTransform(self) -> sitkDisplacementFieldTransform:
        if self._field is not None: return self._field
        else: raise ValueError('No displacement field transform.')

    def getSITKDisplacementFieldSITKImage(self) -> sitkImage:
        if self._field is not None: return self._field.GetDisplacementField()

    def getInverseSITKTransform(self) -> sitkAffineTransform:
        if self._field is None: return self._transform.GetInverse()
        else: raise TypeError('No affine transform.')

    def setSITKDisplacementFieldTransform(self, trf: sitkDisplacementFieldTransform) -> None:
        if isinstance(trf, sitkDisplacementFieldTransform):
            self._field = trf
            self.setIdentity()
        else: raise TypeError('parameter type {} is not sitkDisplacementFieldTransform.'.format(type(trf)))

    def setSITKDisplacementFieldImage(self, img: SisypheImage | sitkImage) -> None:
        if isinstance(img, SisypheImage):
            img = img.getSITKImage()
        if isinstance(img, sitkImage):
            if img.GetNumberOfComponentsPerPixel() == 3 and img.GetPixelIDValue() in (sitkVectorFloat32,
                                                                                      sitkVectorFloat64):
                if self._field is not None: del self._field
                # Displacement field img type must be sitkVectorFloat64 (not sitkVectorFloat32)
                self._field = sitkDisplacementFieldTransform(Cast(img, sitkVectorFloat64))
                self.setIdentity()
                self.setSize(img.GetSize())
                self.setSpacing(img.GetSpacing())
            else: raise ValueError('image parameter is not a displacement field.')
        else: raise TypeError('parameter type {} is not sitkImage or SisypheImage.'.format(type(img)))

    def removeDisplacementField(self) -> None:
        if self.isDisplacementFieldTransform():
            del self._field
            self._field = None
            self._fieldname = ''

    def setVTKTransform(self, trf: vtkTransform) -> None:
        if self._field is None:
            if isinstance(trf, vtkTransform):
                mat = trf.GetMatrix()
                self.setVTKMatrix4x4(mat)
            else: raise TypeError('parameter type {} is not vtkTransform.'.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def getVTKTransform(self) -> vtkTransform:
        if self._field is None:
            trf = vtkTransform()
            vtkmat = trf.GetMatrix()
            sitkmat = self._transform.GetMatrix()
            sitktrans = self._transform.GetTranslation()
            for r in range(3):
                vtkmat.SetElement(r, 3, sitktrans[r])
                for c in range(3):
                    vtkmat.SetElement(r, c, sitkmat[r * 3 + c])
            return trf
        else: raise TypeError('No affine transform.')

    def setVTKMatrix3x3(self, mat: vtkMatrix3x3) -> None:
        if self._field is None:
            if isinstance(mat,  vtkMatrix3x3):
                m = mat.GetGetData()
                self._affine.SetIdentity()
                self._transform.SetMatrix(m)
            else: raise TypeError('parameter type {} is not vtkMatrix3x3.'.format(type(mat)))
        else: raise TypeError('No affine transform.')

    def setVTKMatrix4x4(self, mat: vtkMatrix4x4) -> None:
        if self._field is None:
            if isinstance(mat,  vtkMatrix4x4):
                self.setIdentity()
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

    def getVTKMatrix4x4(self) -> vtkMatrix4x4:
        if self._field is None: return self.getVTKTransform().GetMatrix()
        else: raise TypeError('No affine transform.')

    def getVTKMatrix3x3(self) -> vtkMatrix3x3:
        if self._field is None:
            m4 = self.getVTKTransform().GetMatrix()
            m3 = vtkMatrix3x3()
            for i in range(3):
                for j in range(3):
                    m3.SetElement(i, j, m4.GetElement(i, j))
            return m3
        else: raise TypeError('No affine transform.')

    def getInverseVTKTransform(self) -> vtkTransform:
        if self._field is None:
            trf = self.getVTKTransform()
            return trf.Inverse()
        else: raise TypeError('No affine transform.')

    def getNumpyArray(self, homogeneous: bool = False) -> npndarray:
        if self._field is None:
            if homogeneous:
                np = nparray(self.getFlattenMatrix(homogeneous))
                return np.reshape(4, 4)
            else:
                np = nparray(self._transform.GetMatrix())
                return np.reshape(3, 3)
        else: raise TypeError('No affine transform.')

    def setNumpyArray(self, np: npndarray) -> None:
        if self._field is None:
            if isinstance(np, npndarray):
                if np.shape == (3, 3):
                    self._affine.SetIdentity()
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
        if self._field is None:
            if isinstance(trf, ANTsTransform):
                if trf.type == 'AffineTransform':
                    self.setIdentity()
                    self._transform.SetMatrix(trf.parameters[0:9])
                    self._transform.SetTranslation(trf.parameters[-3:])
                else: raise TypeError('ANTsTransform type {} is not AffineTransform.'.format(trf.type))
            else: raise TypeError('parameter type {} is not ANTsTransform.'.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def getANTSTransform(self) -> ANTsTransform:
        if self._field is None:
            p = self._transform.GetMatrix() + self._transform.GetTranslation()
            trf = ANTsTransform()
            trf.set_parameters(p)
            return trf
        else: raise TypeError('No affine transform.')

    def getMatrixColumn(self, c: int) -> vectorFloat3:
        if self._field is None:
            if isinstance(c, int):
                if 0 <= c < 3:
                    r = self.getFlattenMatrix()
                    return [r[0 + c], r[3 + c], r[6 + c]]
                else: raise ValueError('parameter value {} is out of range (0 to 2).'.format(c))
            else: raise TypeError('parameter type {} isn not int'.format(type(c)))
        else: raise TypeError('No affine transform.')

    def getMatrixDiagonal(self) -> vectorFloat3:
        r = self.getFlattenMatrix()
        return [r[0], r[4], r[8]]

    def getFlattenMatrix(self, homogeneous: bool = False) -> list[float]:
        if self._field is None:
            if homogeneous:
                m = list(self._transform.GetMatrix())
                t = list(self._transform.GetTranslation())
                m = m[:3] + [t[0]] + m[3:6] + [t[1]] + m[-3:] + [t[2], 0.0, 0.0, 0.0, 1.0]
                return m
            else: return list(self._transform.GetMatrix())
        else: raise TypeError('No affine transform.')

    def setFlattenMatrix(self, m: list[float], bycolumn: bool = False) -> None:
        if self._field is None:
            if len(m) == 9:
                if bycolumn: m = list(nparray(m).reshape(3, 3).T.flatten())
                self._affine.SetIdentity()
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
        if self._field is None:
            return self._transform.TransformPoint(tuple(coor))
        else: return self._field.TransformPoint(coor)

    def applyInverseToPoint(self, coor: vectorFloat3) -> vectorFloat3:
        if self._field is None:
            t = self._transform.GetInverse()
            return t.TransformPoint(tuple(coor))

    def preMultiply(self,
                    trf: vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkAffineTransform | sitkEuler3DTransform | npndarray,
                    homogeneous: bool = False) -> None:
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
            if isinstance(trf, npndarray):
                self._affine.SetIdentity()
                if homogeneous: r = matmul(trf, self.getNumpyArray(homogeneous=True))
                else: r = matmul(trf[:3, :3], self.getNumpyArray())
                self.setNumpyArray(r)
            else: raise TypeError('parameter type {} is not numpy array, vtkTransform '
                                  'vtkMatrix4x4, sitkTransform or SisypheTransform. '.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def postMultiply(self,
                     trf: vtkTransform | vtkMatrix4x4 | SisypheTransform | sitkAffineTransform | sitkEuler3DTransform | npndarray,
                     homogeneous: bool = False) -> None:
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
            if isinstance(trf, npndarray):
                self._affine.SetIdentity()
                if homogeneous: r = matmul(self.getNumpyArray(homogeneous=True), trf)
                else: r = matmul(self.getNumpyArray(), trf[:3, :3])
                self.setNumpyArray(r)
            else:
                raise TypeError('parameter type {} is not numpy array, vtkTransform, '
                                'vtkMatrix4x4, sitkTransform or SisypheTransform. '.format(type(trf)))
        else: raise TypeError('No affine transform.')

    def isDisplacementFieldTransform(self) -> bool:
        return self._field is not None

    def isAffineTransform(self) -> bool:
        return self._field is None

    def AffineToDisplacementField(self, inverse: bool = False) -> None:
        if self._field is None:
            if not self.isIdentity():
                f = sitkTransformToDisplacementFieldFilter()
                f.SetSize(self.getSize())
                f.SetOutputSpacing(self.getSpacing())
                f.SetOutputOrigin([0.0, 0.0, 0.0])
                f.SetOutputPixelType(sitkVectorFloat64)
                self._transform.SetCenter([0.0, 0.0, 0.0])
                if inverse: field = f.Execute(self._transform.GetInverse())
                else: field = f.Execute(self._transform)
                self._field = sitkDisplacementFieldTransform(3)
                self._field.SetInterpolator(sitkLinear)
                self._field.SetDisplacementField(field)
                self.setIdentity()
        else: raise TypeError('No affine transform.')

    def hasID(self) -> bool:
        return self._ID != ''

    def getID(self) -> str:
        return self._ID

    def setID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(ID, str): self._ID = ID
        elif isinstance(ID, sc.sisypheVolume.SisypheVolume): self._ID = ID.getID()
        else: raise TypeError('parameter is not str, SisypheImage or SisypheVolume.')

    def getSpacing(self) -> vectorFloat3:
        return self._spacing

    def setSpacing(self, spacing: vectorFloat3) -> None:
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(spacing, (SisypheImage, SisypheVolume)): self._spacing = list(spacing.getSpacing())
        else:  self._spacing = list(spacing)

    def hasSpacing(self) -> bool:
        return self._spacing != (0.0, 0.0, 0.0)

    def getSize(self) -> vectorInt3:
        return self._size

    def setSize(self, size: vectorInt3):
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(size, (SisypheImage, SisypheVolume)): self._size = list(size.getSize())
        else: self._size = list(size)

    def hasSize(self) -> bool:
        return self._size != (0, 0, 0)

    def copyAttributesTo(self, t: SisypheTransform) -> None:
        t.setSize(self.getSize())
        t.setSpacing(self.getSpacing())
        t.setCenter(self.getCenter())
        t.setID(self.getID())
        t.setName(self.getName())

    def copyAttributesFrom(self, t: SisypheTransform) -> None:
        self.setSize(t.getSize())
        self.setSpacing(t.getSpacing())
        self.setCenter(t.getCenter())
        self.setID(t.getID())
        self.setName(t.getName())

    def setAttributesFromFixedVolume(self, vol: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(vol, sc.sisypheVolume.SisypheVolume):
            self.setID(vol)
            self.setName(vol.getFilename())
            self._size = vol.getSize()
            self._spacing = vol.getSpacing()
            self._transform.SetCenter(vol.getCenter())

    def hasFixedVolumeAttributes(self) -> bool:
        return self.hasSize() and self.hasSpacing() and self.hasCenter()

    def hasSameFixedVolumeAttributes(self, vol: sc.sisypheVolume.SisypheVolume) -> bool:
        if isinstance(vol, sc.sisypheVolume.SisypheVolume):
            return self._size == vol.getSize() and \
                   self._spacing == vol.getSpacing()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
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
                        Displacement field image type is sitkFloat64 
                        in SimpleITK DisplacementFieldTransform class.
                        Space saving conversion to sitkFloat32. 
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
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                transform = doc.getElementsByTagName('transform')
                self.parseXMLNode(transform[0])
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def saveAs(self, filename: str) -> None:
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
                        but in SimpleITK DisplacementFieldTransform class, datatype must be sitkVectorFloat64.
                        Cast datatype to sitkVectorFloat64.
                    """
                    self._field.SetDisplacementField(Cast(field.getSITKImage(), sitkVectorFloat64))
                    self.setIdentity()
                    self._fieldname = field.getBasename()
        else: raise IOError('no such file : {}'.format(filename))

    # IO public methods

    def saveToXfmTransform(self, filename: str) -> None:
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.xfm'
            w = vtkMNITransformWriter()
            w.SetFileName(filename)
            w.SetTransform(self.getVTKTransform())
            w.Write()
        else: raise TypeError('Displacement field transform can not be saved to Xfm format.')

    def saveToTfmTransform(self, filename: str) -> None:
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.tfm'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to Tfm format.')

    def saveToMatfileTransform(self, filename: str) -> None:
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.mat'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to Matfile format.')

    def saveToTxtTransform(self, filename: str) -> None:
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.txt'
            self._transform.WriteTransform(filename)
        else: raise TypeError('Displacement field transform can not be saved to txt format.')

    def saveToANTSTransform(self, filename: str) -> None:
        if self._field is None:
            path, ext = splitext(filename)
            filename = path + '.mat'
            trf = self.getANTSTransform()
            write_transform(trf, filename)
        else: raise TypeError('Displacement field transform can not be saved to ANTs format.')

    def loadFromXfmTransform(self, filename: str) -> None:
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
        path, ext = splitext(filename)
        if ext.lower() != '.mat': filename = path + '.mat'
        if exists(filename):
            self.setIdentity()
            self.removeDisplacementField()
            trf = read_transform(filename)
            self.setANTSTransform(trf)
        else: raise FileNotFoundError('No such file {}.'.format(filename))

    def loadFromBrainVoyagerTransform(self, filename: str) -> None:
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
        SisypheApplyTransform class

        Description

            SisypheVolume resampling class.
            Applies SisypheTransform geometric transformation
            to resample a moving image, roi, mesh or streamlines
            into the space of a fixed image.

        Inheritance

            object -> SisypheApplyTransform

        Private attributes

            _moving     SisypheVolume to resample
            _transform  SisypheTransform to apply
            _resample   sitkResampleImageFilter

        Class methods

            int = getInterpolatorCodeFromName(str)
            str = getInterpolatorNameFromCode(int)

        Public methods

            __str__()
            __repr__()
            setInterpolator(str | int)
            str = getInterpolator()
            int = getInterpolatorSITKCode()
            setTransform(SisypheTransform)                      forward transform moving -> fixed
            setFromTransforms(SisypheTransforms, str)
            setFromVolumes(SisypheVolume, SisypheVolume)
            SisypheTransform = getTransform()                   return forward transform, moving -> fixed
            SisypheTransform = getResampleTransform()           return backward tranform, fixed -> moving
            setFromTransforms(SisypheTransform | str | int)     int = index or str = ID key
            sitkTransform = getSITKTransform()                  return forward transform moving -> fixed
            sitkTransform = getSITKResampleTransform()          return backward tranform, fixed -> moving
            bool = hasTransform()
            bool = hasAffineTransform()
            bool = hasDisplacementFieldTransform()
            updateTransforms(SisypheVolume, SisypheVolume)      SisypheVolumes = resampled and fixed volumes
            updateVolumeTransformsFromMoving(SisypheVolume)
            setMoving(SisypheVolume)
            SisypheVolume = getMoving()
            bool = hasMoving()
            setMovingROI(SisypheROI)
            SisypheROI = getMovingROI()
            bool = hasMovingROI()
            setMovingMesh(SisypheMesh)
            SisypheMesh = getMovingMesh()
            bool = hasMovingMesh()
            setMovingStreamlines(SisypheStreamlines)
            SisypheStreamlines = getMovingStreamlines()
            bool = hasMovingStreamlines()
            resampleMoving()
            resampleROI()
            resampleMesh()
            resampleStreamlines()
            execute()

        Creation: 05/10/2021
        Revisions:

            15/04/2023  add ROI and mesh resampling
            21/04/2023  updateTransforms() method bugfix
            01/09/2023  type hinting
            13/11/2023  add streamlines resampling
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
        return cls._TOCODE[name]

    @classmethod
    def getInterpolatorNameFromCode(cls, code: int) -> str:
        return cls._FROMCODE[code]

    # Special methods

    def __init__(self) -> None:
        self._moving = None
        self._roi = None
        self._mesh = None
        self._sl = None
        self._transform = None
        self._resample = sitkResampleImageFilter()
        self._resample.SetInterpolator(sitkLinear)

    def __str__(self) -> str:
        buff = '\nTransform:\n{}\n'.format(str(self._transform))
        buff += 'Resample volume:\n{}\n'.format(str(self._moving))
        buff += 'Interpolator: {}\n'.format(self.getInterpolator())
        return buff

    def __repr__(self) -> str:
        return 'SisypheApplyTransform instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setInterpolator(self, v: str | int) -> None:
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
        return self._FROMCODE[self._resample.GetInterpolator()]

    def getInterpolatorSITKCode(self) -> int:
        return self._resample.GetInterpolator()

    def setTransform(self, trf: SisypheTransform, center: bool = False) -> None:
        if isinstance(trf, SisypheTransform):
            if not center: trf.setCenter([0.0, 0.0, 0.0])
            self._transform = trf
            self._resample.SetSize(self._transform.getSize())
            self._resample.SetOutputSpacing(self._transform.getSpacing())
            if trf.isAffineTransform():
                # Affine trf is forward transform
                # inverse trf = backward transform to resample
                self._resample.SetTransform(trf.getInverseSITKTransform())
            else:
                # Displacement field trf is backward transform
                self._resample.SetTransform(trf.getSITKTransform())
        else: raise TypeError('parameter type {} is not SisypheTransform'.format(type(trf)))

    def setFromTransforms(self, trfs: SisypheTransforms, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(trfs, SisypheTransforms):
            if ID in trfs: self.setTransform(trfs[ID])
        else: raise TypeError('parameter type {} is not SisypheTransforms'.format(type(trfs)))

    def setFromVolumes(self,
                       fixed: sc.sisypheVolume.SisypheVolume,
                       moving: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(fixed, sc.sisypheVolume.SisypheVolume) and isinstance(moving, sc.sisypheVolume.SisypheVolume):
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
        return self._transform

    def getResampleTransform(self) -> SisypheTransform:
        return self._transform.getInverseTransform()

    def getSITKTransform(self) -> sitkAffineTransform | sitkDisplacementFieldTransform:
        return self._transform.getSITKTransform()

    def getSITKResampleTransform(self) -> sitkTransform:
        return self._resample.GetTransform()

    def hasTransform(self) -> bool:
        return self._transform is not None

    def hasAffineTransform(self) -> bool:
        return self._transform is not None and self._transform.isAffineTransform()

    def hasDisplacementFieldTransform(self) -> bool:
        return self._transform is not None and self._transform.isDisplacementFieldTransform()

    def setMoving(self, img: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(img, SisypheImage):
            self._moving = img
            if isinstance(self._moving, SisypheBinaryImage):
                # Nearest Neighbor for binary image
                self._resample.SetInterpolator(sitkNearestNeighbor)
            if isinstance(self._moving, sc.sisypheVolume.SisypheVolume):
                # Nearest Neighbor for label volume
                if self._moving.getAcquisition().isLB(): self._resample.SetInterpolator(sitkNearestNeighbor)
        else: raise TypeError('parameter type {} is not SisypheImage'.format(type(img)))

    def getMoving(self) -> sc.sisypheVolume.SisypheVolume:
        return self._moving

    def hasMoving(self) -> bool:
        return self._moving is not None

    def clearMoving(self) -> None:
        self._moving = None

    def setMovingROI(self, roi: sc.sisypheROI.SisypheROI) -> None:
        if isinstance(roi, sc.sisypheROI.SisypheROI): self._roi = roi
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def getMovingROI(self) -> sc.sisypheROI.SisypheROI:
        return self._roi

    def hasMovingROI(self) -> bool:
        return self._roi is not None

    def clearMovingROI(self) -> None:
        self._roi = None

    def setMovingMesh(self, mesh: sc.sisypheMesh.SisypheMesh) -> None:
        if isinstance(mesh, sc.sisypheMesh.SisypheMesh): self._mesh = mesh
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def getMovingMesh(self) -> sc.sisypheMesh.SisypheMesh:
        return self._mesh

    def hasMovingMesh(self) -> bool:
        return self._mesh is not None

    def clearMesh(self) -> None:
        self._mesh = None

    def setMovingStreamlines(self, sl: sc.sisypheTracts.SisypheStreamlines) -> None:
        if isinstance(sl, sc.sisypheTracts.SisypheStreamlines): self._sl = sl
        else: raise TypeError('parameter type {} is not SisypheStreamlines.'.format(type(sl)))

    def getMovingStreamlines(self) -> sc.sisypheTracts.SisypheStreamlines:
        return self._sl

    def hasMovingStreamlines(self) -> bool:
        return self._sl is not None

    def clearStreamlines(self) -> None:
        self._sl = None

    def updateVolumeTransformsFromMoving(self, vol: sc.sisypheVolume.SisypheVolume) -> None:
        if self.hasAffineTransform() and self.hasMoving():
            if not isinstance(vol, sc.sisypheVolume.SisypheVolume):
                raise TypeError('resampled parameter type {} is not SisypheVolume.'.format(type(vol)))
            # Template fixed volume is not updated
            if not vol.acquisition.isTP():
                if vol.getID() == self._moving.getID():
                    vtrfs = vol.getTransforms()
                    for trf in self._moving.getTransforms():
                        if trf.getID() not in vtrfs:
                            if trf.isAffineTransform():
                                vtrfs.append(trf)
                # Save moving volume SisypheTransforms
                if vol.hasFilename():
                    vol.saveTransforms()
            else: raise ValueError('Incorrect ID of the parameter volume.')

    def updateTransforms(self,
                         resampled: sc.sisypheVolume.SisypheVolume,
                         fixed: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        if self.hasAffineTransform() and self.hasMoving():
            if not isinstance(resampled, sc.sisypheVolume.SisypheVolume):
                raise TypeError('resampled parameter type {} is not SisypheVolume.'.format(type(resampled)))
            forwardtrf = self._transform
            forwardtrf.setAttributesFromFixedVolume(fixed)
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
            if fixed is not None:
                # Template fixed volume is not updated
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
                                    if trf.isAffineTransform():
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
                                    if trf.isAffineTransform():
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
                            if trf.isAffineTransform():
                                rtrfs.append(trf)
            """
                Save moving volume SisypheTransforms
            """
            if self._moving.hasFilename():
                self._moving.saveTransforms()
            # Save fixed volume SisypheTransforms
            if fixed is not None:
                if fixed.hasFilename(): fixed.saveTransforms()
        else: raise AttributeError('No SisypheTransform or moving SisypheVolume.')

    def resampleMoving(self,
                       fixed: sc.sisypheVolume.SisypheVolume | None = None,
                       save: bool = True,
                       dialog: bool = False,
                       prefix: str | None = None,
                       suffix: str | None = None,
                       wait: DialogWait | None = None) -> sc.sisypheVolume.SisypheVolume:
        """
            Origin management in resampling function:
            Origin is not used during registration, origin must therefore be ignored at the resampling stage
                1. moving volume origin is stored before resampling
                2. set moving volume origin to (0.0, 0.0, 0.0)
                3. moving volume resampling
                4. moving volume origin is restored
                5. copy moving volume attributes to resampled volume (identity, display, acquisition, acpc)
                6. copy fixed volume ID to resampled volume (same brain space)
                7. copy fixed volume origin to resampled volume
        """
        if self.hasTransform():
            if self.hasMoving():
                if wait is not None:
                    wait.setSimpleITKFilter(self._resample)
                    wait.addSimpleITKFilterProcessCommand()
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(self._moving.getBasename()))
                    wait.open()
                if isinstance(self._moving, SisypheBinaryImage): self._resample.SetInterpolator(sitkNearestNeighbor)
                elif self._moving.getAcquisition().isLB(): self._resample.SetInterpolator(sitkNearestNeighbor)
                resampled = sc.sisypheVolume.SisypheVolume()
                # 1. Store moving volume origin
                origin = self._moving.getOrigin()
                # 2. Set moving volume origin tp (0.0, 0.0, 0.0)
                self._moving.setDefaultOrigin()
                # 3. moving volume resampling -> resampled volume
                resampled.setSITKImage(self._resample.Execute(self._moving.getSITKImage()))
                # 4. Restore moving volume origin
                self._moving.setOrigin(origin)
                # 5. copy moving volume attributes to resampled volume
                resampled.copyPropertiesFrom(self._moving, acpc=False)
                # if moving is a template, resampled is no longer a template, set its modality to OT
                if self._moving.acquisition.isTP(): resampled.acquisition.setModalityToOT()
                if fixed is not None:
                    # 6. copy fixed volume ID to resampled volume
                    resampled.setID(fixed.getID())
                    # 7. Copy fixed volume origin to resampled volume
                    resampled.setOrigin(fixed.getOrigin())
                    if fixed.getACPC().hasACPC():
                        # copy fixed volume  SisypheACPC image attribute to resampled volume
                        acpc = fixed.getACPC().copy()
                        resampled.setACPC(acpc)
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
                if self._transform.isAffineTransform():
                    self.updateTransforms(resampled, fixed)
                """
                    Save resampled volume
                """
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    path = dirname(self._moving.getFilename())
                    base, ext = splitext(self._moving.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled volume', filename,
                                                               filter=resampled.getFilterExt())[0]
                        QApplication.processEvents()
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
                    wait: DialogWait | None = None) -> sc.sisypheROI.SisypheROI:
        if self.hasTransform():
            if self.hasMovingROI():
                if wait is not None:
                    wait.setSimpleITKFilter(self._resample)
                    wait.addSimpleITKFilterProcessCommand()
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(self._roi.getBasename()))
                    wait.open()
                interpolator = self.getInterpolator()
                self._resample.SetInterpolator(sitkNearestNeighbor)
                resampled = sc.sisypheROI.SisypheROI()
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
                    path = dirname(self._roi.getFilename())
                    base, ext = splitext(self._roi.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled ROI', filename,
                                                               filter=resampled.getFilterExt())[0]
                        QApplication.processEvents()
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
                     wait: DialogWait | None = None) -> sc.sisypheMesh.SisypheMesh:
        if self.hasTransform():
            if self.hasMovingMesh():
                n = self._mesh.getNumberOfPoints()
                if wait is not None:
                    wait.setProgressRange(0, n)
                    wait.buttonVisibilityOn()
                    wait.setInformationText('Resample {}...'.format(self._mesh.getBasename()))
                    wait.open()
                resampled = sc.sisypheMesh.SisypheMesh()
                resampled.copyFrom(self._mesh)
                points = self._mesh.getPoints()
                # Use forward transform to resample mesh vertices
                trf = self._transform.getInverseTransform()
                for i in range(n):
                    p = points.GetPoint(i)
                    points.SetPoint(i, trf.applyToPoint(p))
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): return None
                self._mesh.setPoints(points)
                resampled.setReferenceID(self._transform.getID())
                resampled.setName(self._roi.getName())
                resampled.copyPropertiesFromMesh(self._mesh)
                # Save resampled mesh
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    path = dirname(self._mesh.getFilename())
                    base, ext = splitext(self._mesh.getFilename())
                    filename = join(path, prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled Mesh', filename,
                                                               filter=resampled.getFilterExt())[0]
                        QApplication.processEvents()
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
                            wait: DialogWait | None = None) -> sc.sisypheTracts.SisypheStreamlines:
        if self.hasTransform():
            if self.hasMovingStreamlines():
                if wait is not None:
                    wait.buttonVisibilityOff()
                    wait.setInformationText('Resample {}...'.format(basename(self._sl.getFilename())))
                    wait.open()
                # Use forward transform to resample mesh vertices
                trf = self._transform.getInverseTransform()
                resampled = self._sl.applyTransformToStreamlines(trf, inplace=False)
                # Save resampled mesh
                if save:
                    settings = SisypheFunctionsSettings()
                    if prefix is None: prefix = settings.getFieldValue('Resample', 'Prefix')
                    if suffix is None: suffix = settings.getFieldValue('Resample', 'Suffix')
                    base, ext = splitext(self._sl.getFilename())
                    filename = join(self._sl.getDirname(), prefix + basename(base) + suffix + ext)
                    if dialog:
                        filename = QFileDialog.getSaveFileName(None, 'Save resampled streamlines', filename,
                                                               filter=resampled.getFilterExt())[0]
                        QApplication.processEvents()
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
                fixed: sc.sisypheVolume.SisypheVolume | None = None,
                save: bool = True,
                dialog: bool = False,
                prefix: str | None = None,
                suffix: str | None = None,
                wait: DialogWait | None = None) \
            -> sc.sisypheVolume.SisypheVolume | sc.sisypheROI.SisypheROI | \
               sc.sisypheMesh.SisypheMesh | sc.sisypheTracts.SisypheStreamlines:
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
        SisypheTransformCollection

        Description

            Container of SisypheTransform instances.
            List-like methods and access with int indexes.
            Dict-like access with str (SisypheVolume ID) as key, no duplication.
            Setter and getter methods of SisypheTransform, to get or set attributes of all SisypheTransform.
            Getter methods returns a list.
            Setter methods parameter is a single attribute value or a list of the same size as the container.

        Inheritance

            object -> SisypheTransformCollection

        Private attributes

            _trfs       list of SisypheTransform
            _index      index for Iterator

        Public methods

            __getitem__(str | int)
            __setitem__(int, SisypheTransform)
            __delitem__(SisypheVolume | SisypheTransform | str | int)
            __len__()
            __contains__(str | SisypheTransform | SisypheVolume)
            __iter__()
            __next__()
            __str__()
            __repr__()
            bool = isEmpty()
            int = count()
            remove(SisypheVolume | SisypheTransform | str | int)
            SisypheTransform = pop(SisypheVolume | SisypheTransform | str | int)
            list = keys()
            int = index(SisypheVolume | SisypheTransform | str)
            reverse()
            append(SisypheTransform)
            insert(SisypheVolume | SisypheTransform | str | int, SisypheTransform)
            clear()
            sort()
            SisypheTransformCollection = copy()
            list = copyToList()
            list = getList()

        Creation: 05/10/2021
        Revisions

            16/03/2023  change items type in _trfs list, tuple(Str ID, SisypheTransform) replaced by SisypheTransform
            16/03/2023  add pop method, removes SisypheTransform from list and returns it
            16/03/2023  add __getattr__ method, gives access to setter and getter methods of SisypheTransform
            01/09/2023  type hinting
    """

    __slots__ = ['_trfs', '_index']

    # Special methods

    def __init__(self) -> None:
        self._trfs = list()
        self._index = 0

    def __str__(self) -> str:
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
        return 'SisypheTransformCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container Public methods

    def __getitem__(self, key: int | str | sc.sisypheVolume.SisypheVolume):
        # key is ID str
        if isinstance(key, (str, sc.sisypheVolume.SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._trfs):
                return self._trfs[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheTransform):
        if isinstance(value, SisypheTransform):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._trfs):
                    if value.getID() in self: key = self.index(value)
                    self._trfs[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def __delitem__(self, key: int | str | SisypheTransform | sc.sisypheVolume.SisypheVolume):
        # key is ID str, SisypheVolume or SisypheTransform
        if isinstance(key, (str, sc.sisypheVolume.SisypheVolume, SisypheTransform)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._trfs):
                del self._trfs[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        return len(self._trfs)

    def __contains__(self, value: SisypheTransform | sc.sisypheVolume.SisypheVolume | str) -> bool:
        keys = [k.getID() for k in self._trfs]
        # value is SisypheTransform or SisypheVolume
        if isinstance(value, (SisypheTransform, sc.sisypheVolume.SisypheVolume)):
            value = value.getID()
        # value is ID str
        if isinstance(value, str):
            return value in keys
        else: raise TypeError('parameter type {} is not str or SisypheTransform.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> SisypheTransform:
        if self._index < len(self._trfs):
            n = self._index
            self._index += 1
            return self._trfs[n]
        else:
            raise StopIteration

    def __getattr__(self, name: str):
        """
            When attribute does not exist in the class,
            try calling the setter or getter method of sisypheTransform instances in collection.
            Getter methods return a list of the same size as the collection.
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
        return len(self._trfs) == 0

    def count(self) -> int:
        return len(self._trfs)

    def keys(self) -> list[str]:
        return [k.getID() for k in self._trfs]

    def remove(self, value: SisypheTransform | int | str | sc.sisypheVolume.SisypheVolume) -> None:
        # value is SisypheTransform
        if isinstance(value, SisypheTransform):
            self._trfs.remove(value)
        # value is SisypheVolume, ID str or int index
        elif isinstance(value, (sc.sisypheVolume.SisypheVolume, str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or SisypheTransform.'.format(type(value)))

    def pop(self,
            key: str | int | SisypheTransform | sc.sisypheVolume.SisypheVolume | None = None) -> SisypheTransform:
        if key is None: return self._trfs.pop()
        # key is ID str, SisypheVolume or SisypheTransform
        if isinstance(key, (str, SisypheTransform, sc.sisypheVolume.SisypheVolume)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._trfs.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def index(self, value: str | sc.sisypheVolume.SisypheVolume | SisypheTransform) -> int:
        keys = [k.getID() for k in self._trfs]
        # value is SisypheTransform or SisypheVolume
        if isinstance(value, (SisypheTransform, sc.sisypheVolume.SisypheVolume)):
            value = value.getID()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheTransform.'.format(type(value)))

    def reverse(self) -> None:
        self._trfs.reverse()

    def append(self, value: SisypheTransform, replace: bool = True) -> None:
        if isinstance(value, SisypheTransform):
            if value.getID() not in self: self._trfs.append(value)
            elif replace: self._trfs[self.index(value)] = value
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def insert(self,
               key: str | int | SisypheTransform | sc.sisypheVolume.SisypheVolume,
               value: SisypheTransform) -> None:
        if isinstance(value, SisypheTransform):
            # value is ID str, SisypheTransform or SisypheVolume
            if isinstance(key, (str, SisypheTransform, sc.sisypheVolume.SisypheVolume)):
                key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._trfs):
                    if value.getID() not in self: self._trfs.insert(key, value)
                    else: self._trfs[self.index(value)] = value
                else: IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(value)))

    def clear(self) -> None:
        self._trfs.clear()

    def sort(self, reverse: bool = False) -> None:
        def _getID(item):
            return item.getID()

        self._trfs.sort(reverse=reverse, key=_getID)

    def copy(self) -> SisypheTransformCollection:
        trfs = SisypheTransformCollection()
        for trf in self._trfs:
            trfs.append(trf)
        return trfs

    def copyToList(self) -> list[SisypheTransform]:
        trfs = self._trfs.copy()
        return trfs

    def getList(self) -> list[SisypheTransform]:
        return self._trfs


class SisypheTransforms(SisypheTransformCollection):
    """
        SisypheTransformDict class

        Description

            SisypheTransformCollection wih :
            - XML format IO methods to SisypheTransformCollection ancestor.
            - ID attribute of the reference SisypheVolume instance.
            Geometric transformations are in forward convention
            (apply inverse transformation to resample)

        Inheritance

            object -> SisypheTransformCollection -> SisypheTransforms

        Private attributes

            _ID         str, ID of the SisypheVolume parent instance
            _filename   str, filename to save instance

        Class method

            str = getFileExt()
            str = getFilterExt()

        Public methods

            __str__()
            __repr__()
            str = getReferenceID()
            setReferenceID(str | SisypheVolume)
            bool = hasReferenceID()
            bool = hasFilename()
            str = getFilename()
            setFilenameFromVolume(SisypheVolume)
            appendIdentityTransformWithVolume(SisypheVolume)
            createXML(minidom.Document)
            parseXML(minidom.Document)
            saveAs()
            save()
            load()

        Creation: 05/10/2021
        Revisions:

            01/09/2023  type hinting
            31/10/2023  add openTransforms() class method
    """
    __slots__ = ['_referenceID', '_filename', '_parent']

    # Class constant

    _FILEEXT = '.xtrfs'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Geometric transformation collection (*{})'.format(cls._FILEEXT)

    @classmethod
    def openTransforms(cls, filename) -> SisypheTransforms:
        if exists(filename):
            filename = basename(filename) + cls.getFileExt()
            trfs = SisypheTransforms()
            trfs.load(filename)
            return trfs

    # Special methods

    def __init__(self, parent: sc.sisypheVolume.SisypheVolume | None = None) -> None:
        super().__init__()
        self._referenceID = None  # reference SisypheVolume ID
        self._filename = ''
        if not isinstance(parent, sc.sisypheVolume.SisypheVolume): parent = None
        if parent is not None: self.setReferenceID(parent)

    def __str__(self) -> str:
        buff = 'Reference ID: {}\n'.format(self.getReferenceID())
        buff += 'Filename: {}\n'.format(basename(self.getFilename()))
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        return 'SisypheTransforms instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def getReferenceID(self) -> str:
        return self._referenceID

    def setReferenceID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(ID, str):
            self._referenceID = ID
        elif isinstance(ID, sc.sisypheVolume.SisypheVolume):
            self._referenceID = ID.getID()
        else:
            self._referenceID = None

    def hasReferenceID(self) -> bool:
        return self._referenceID is not None

    def hasFilename(self) -> bool:
        if self._filename != '':
            if exists(self._filename):
                return True
            else:
                self._filename = ''
        return False

    def getFilename(self) -> str:
        return self._filename

    def setFilenameFromVolume(self, img: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(img, sc.sisypheVolume.SisypheVolume):
            if img.hasFilename():
                path, ext = splitext(img.getFilename())
                path += self._FILEEXT
                self._filename = path
            else:
                self._filename = ''
        else: raise TypeError('parameter type {} is not SisypheVolume'.format(img))

    def appendIdentityTransformWithVolume(self, vol: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(vol, sc.sisypheVolume.SisypheVolume):
            trf = SisypheTransform()
            trf.setIdentity()
            trf.setAttributesFromFixedVolume(vol)
            self.append(trf)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def copy(self) -> SisypheTransforms:
        trfs = SisypheTransforms()
        for trf in self._trfs:
            trfs.append(trf)
        return trfs

    # IO public methods

    def createXML(self, doc: minidom.Document) -> None:
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
                if trf.isAffineTransform():
                    trf.createXML(doc, root)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def parseXML(self, doc: minidom.Document) -> None:
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
        if not self.isEmpty():
            if self.hasFilename():
                filename = self._filename
            if filename != '':
                self.saveAs(filename)
            else: raise AttributeError('filename attribute is empty.')
        else: raise AttributeError('SisypheTransform instance is empty.')

    def load(self, filename: str = '') -> None:
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
