"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os import remove
from os.path import join
from os.path import splitext
from os.path import exists
from os.path import dirname
from os.path import basename

from xml.dom import minidom

import cython

from numpy import zeros

from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import Image as sitkImage
from SimpleITK import sitkFloat32
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
from SimpleITK import BinaryFillholeImageFilter
from SimpleITK import SmoothingRecursiveGaussian

from vtk import vtkActor
from vtk import vtkPoints
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper
from vtk import vtkTransform
from vtk import vtkTransformPolyDataFilter
from vtk import vtkCenterOfMass
from vtk import vtkOBBTree
from vtk import vtkDistancePolyDataFilter
from vtk import vtkImplicitPolyDataDistance
from vtk import vtkProperty
from vtk import vtkTriangleFilter
from vtk import vtkPolyDataNormals
from vtk import vtkStripper
from vtk import vtkFillHolesFilter
from vtk import vtkDecimatePro
from vtk import vtkSmoothPolyDataFilter
from vtk import vtkWindowedSincPolyDataFilter
from vtk import vtkPolyDataConnectivityFilter
from vtk import vtkTubeFilter
from vtk import vtkContourFilter
from vtk import vtkMarchingCubes
from vtk import vtkFlyingEdges3D
from vtk import vtkLineSource
from vtk import vtkSphereSource
from vtk import vtkCubeSource
from vtk import vtkCleanPolyData
from vtk import vtkAppendPolyData
from vtk import vtkMassProperties
from vtk import vtkImageData
from vtk import vtkImageCast
from vtk import vtkLookupTable
from vtk import vtkPolyDataToImageStencil
from vtk import vtkImageStencilToImage
from vtk import vtkFloatArray
from vtk import VTK_UNSIGNED_CHAR
from vtk import VTK_TRIANGLE
from vtk import vtkVersion

import Sisyphe.core as sc
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheMeshIO import readMeshFromOBJ
from Sisyphe.core.sisypheMeshIO import writeMeshToOBJ
from Sisyphe.core.sisypheMeshIO import readMeshFromSTL
from Sisyphe.core.sisypheMeshIO import writeMeshToSTL
from Sisyphe.core.sisypheMeshIO import readMeshFromVTK
from Sisyphe.core.sisypheMeshIO import writeMeshToVTK
from Sisyphe.core.sisypheMeshIO import readMeshFromXMLVTK
from Sisyphe.core.sisypheMeshIO import writeMeshToXMLVTK
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.core.sisypheTransform import SisypheApplyTransform
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheMesh',
           'SisypheMeshCollection']

"""
    Class hierarchy
    
        object -> SisypheMesh
                  SisypheMeshCollection
"""

vectorFloat3Type = list[float, float, float] | tuple[float, float, float]


class SisypheMesh(object):
    """
        SisypheMesh class

        Inheritance

            object -> SisypheMesh

        Private attributes

            _name           str
            _filename       str
            _referenceID    str
            _polydata       vtkPolyData
            _mapper         vtkPolyDataMapper
            _actor          vtkActor

        Public methods

            str = getReferenceID()
            setReferenceID(str or SisypheVolume)
            bool = hasReferenceID()
            bool = isEmpty()
            setName(str)
            setNameFromFilename(str)
            str = getName()
            setFilename(str)
            str = getFilename()
            str = getDirname()
            bool = hasFilename()
            setPolyData(vtkPolyData or vtkPolyDataMapper or vtkActor or sisypheMesh)
            copyFrom(vtkPolyData or vtkPolyDataMapper or vtkActor or sisypheMesh)
            clear()
            vtkPolyData = getPolyData()
            vtkPolyDataMapper = getPolyDataMapper()
            vtkActor = getActor()
            int = getMemorySize()
            int = getNumberOfPoints()
            vtkPoints = getPoints()
            setPoints(vtkPoints)
            setPosition(float, float, float)
            list = getPosition()
            bool = isDefaultPosition()
            vtkProperty = getVtkProperty()
            setVtkProperty(vtkProperty)
            copyPropertiesFromVtkProperty(vtkProperty)
            copyPropertiesFromVtkActor(vtkActor)
            copyColorFromROI(SisypheROI)
            copyAttributesFromMesh(SisypheMesh)
            setOpacity(float)
            float = getOpacity()
            setScale(float, float, float)
            list = getScale()
            setOrigin(float, float, float)
            setOriginFromReferenceVolume(SisypheVolume)
            list = getOrigin()
            bool = isDefaultOrigin()
            setTransform(SisypheTransform)
            SisypheTransform = getTransform()
            setVisibilityOn()
            setVisibilityOff()
            bool = getVisibility()
            setColor(r, g, ,b)
            list = getColor()
            bool = getScalarColorVisibility()
            setScalarColorVisibilityOn()
            setScalarColorVisibilityOff()
            setScalarColorVisibility(bool)
            setLUT(vtkLookupTable or SisypheLUT or SisypheVolume)
            vtkLookupTable = getLUT()
            setPointScalarColorFromVolume(SisypheVolume)
            setAmbiant(float)
            float = getAmbient()
            setDiffuse(float)
            float = getDiffuse()
            setSpecular(float)
            float = getSpecular()
            setSpecularPower(float)
            float = getSpecularPower()
            setMetallic(bool)
            bool = getMetallic()
            setRoughness(float)
            float = getRoughness()
            setFlatRendering()
            setGouraudRendering()
            setPhongRendering()
            setPBRRendering()
            str = getRenderingAlgorithmAsString()
            int = getRenderingAlgorithm()
            setRenderingAlgorithm(int)
            setRenderPointsAsSpheresOn()
            setRenderPointsAsSpheresOff()
            bool = getRenderPointsAsSpheres()
            setRenderLinesAsTubesOn()
            setRenderLinesAsTubesOff()
            bool = getRenderLinesAsTubes()
            setVertexVisibilityOn()
            setVertexVisibilityOff()
            bool = getVertexVisibility()
            setVertexColor(float, float, float)
            list = getVertexColor()
            setEdgeVisibilityOn()
            setEdgeVisibilityOff()
            bool = getEdgeVisibility()
            setEdgeColor(float, float, float)
            list = getEdgeColor()
            setLineWidth(float)
            float = getLineWidth()
            setPointSize(float)
            float = getPointSize()
            bool = getShading()
            shadingOn()
            shadingOff()
            createLine(list, list, float)
            createTube(list, list, float, float)
            createSphere(float, float)
            createCube(float, float, float)
            createOuterSurface(SisypheVolume, fill=bool, decimate=float, clean=bool, smooth=str, niter=int, algo=str)
            createIsosurface(SisypheVolume, int, fill=bool, decimate=float, clean=bool, smooth=str, niter=int, algo=str)
            createFromROI(SisypheROI, fill=bool, decimate=float, clean=bool, smooth=str, niter=int, algo=str)
            decimate(float)
            clean()
            sincSmooth(int, float, bool, bool)
            laplacianSmooth(int, float, bool, bool)
            fillHoles(int)
            combinePolyData(SisypheMesh or vtkActor or vtkPolyDataMapper or vtkPolyData)
            union(datas=list[SisypheMesh])
            intersection(datas=list[SisypheMesh])
            difference(datas=list[SisypheMesh])
            float = getMeshVolume()
            float = getMeshSurface()
            [float, float, float] = getCenterOfMass()
            float = getDistanceFromSurfaceToPoint([float, float, float])
            (float, float) = getDistanceFromSurfaceToSurface(vtkPolyData | vtkPolyDataMapper | vtkActor | SisypheMesh)
            bool = isPointInside([float, float, float])
            bool = isPointOutside([float, float, float])
            vtkImageData = convertToVTKImage()
            sisypheROI = convertToSisypheROI()
            load(str)
            loadFromOBJ(str)
            loadFromSTL(str)
            loadFromVTK(str)
            loadFromXMLVTK(str)
            loadFromXML(str)
            saveToObj(str)          vtk version > 9
            saveToSTL(str)
            saveToVTK(str)
            saveToXMLVTK(str)
            save(str)
            saveAs(str)

        Creation: 22/03/2023
        Revisions:

            29/07/2023  getDistanceFromSurfaceToSurface() bugfix, SetInputConnection replaced by SetInputData
            02/08/2023  ParseXML() bugfix, convert str to boolean attributes
            02/08/2023  dilate() and erode() bugfix, tuple assignment
            02/08/2023  copyFrom() and setPolyData(), reference ID and vtkProperty copy added
            02/08/2023  createCube() and createSphere() bugfix
            05/08/2023  add applyTransform() method to resample mesh vertices
            07/08/2023  union(), intersection(), difference() bugfix
            08/08/2023  convertToVTKImage() bugfix
            01/09/2023  type hinting
            31/10/2023  add depth and feature parameters to setPointScalarColorFromVolume() method
                        cythonise setPointScalarColorFromVolume() method
            31/10/2023  add updatenormals parameter to decimate(), clean(), sincSmooth,
                        laplacianSmooth() and fillHoles() methods
            31/10/2023  add openMesh() class method
    """
    __slots__ = ['_name', '_filename', '_referenceID', '_polydata', '_mapper', '_actor']

    _FILEEXT = '.xmesh'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Mesh (*{})'.format(cls._FILEEXT)

    @classmethod
    def openMesh(cls, filename: str) -> SisypheMesh:
        if exists(filename):
            _, ext = splitext(filename)
            mesh = SisypheMesh()
            ext = ext.lower()
            if ext == cls.getFileExt(): mesh.load(filename)
            elif ext == '.obj': mesh.loadFromOBJ(filename)
            elif ext == '.stl': mesh.loadFromSTL(filename)
            elif ext == '.vtk': mesh.loadFromVTK(filename)
            elif ext == '.vtp': mesh.loadFromXMLVTK(filename)
            else: raise IOError('{} format is not supported.'.format(ext))
            return mesh

    # Special methods

    def __init__(self) -> None:
        self._name = 'Mesh'
        self._filename = ''
        self._referenceID = ''  # reference SisypheVolume ID
        self._polydata = None
        self._mapper = vtkPolyDataMapper()
        self._actor = vtkActor()

    def __str__(self) -> str:
        if self._polydata is not None:
            buff = 'Name: {}\n'.format(self.getName())
            buff += 'ID: {}\n'.format(self.getReferenceID())
            buff += 'Origin: {}\n'.format(self._numericToStr(self.getOrigin(), d=1))
            buff += 'Position: {}\n'.format(self._numericToStr(self.getPosition(), d=1))
            buff += 'Center: {}\n'.format(self._numericToStr(self.getCenter(), d=1))
            buff += 'Bounds: {}\n'.format(self._numericToStr(self.getBounds(), d=1))
            buff += 'Scale: {}\n'.format(self._numericToStr(self.getScale()))
            buff += 'Color: {}\n'.format(self._numericToStr(self.getColor()))
            buff += 'Opacity: {:.2f}\n'.format(self.getOpacity())
            buff += 'Ambient: {:.2f}\n'.format(self.getAmbient())
            buff += 'Diffuse: {:.2f}\n'.format(self.getDiffuse())
            buff += 'Specular: {:.2f}\n'.format(self.getSpecular())
            buff += 'Specular Power: {:.2f}\n'.format(self.getSpecularPower())
            buff += 'Metallic: {:.2f}\n'.format(self.getMetallic())
            buff += 'Roughness: {:.2f}\n'.format(self.getRoughness())
            buff += 'Render points as spheres: {}\n'.format(self.getRenderPointsAsSpheres())
            buff += 'Render lines as tubes: {}\n'.format(self.getRenderLinesAsTubes())
            buff += 'Point size: {:.1f}\n'.format(self.getPointSize())
            buff += 'Line width: {:.1f}\n'.format(self.getLineWidth())
            buff += 'Vertex visibility: {}\n'.format(self.getVertexVisibility())
            buff += 'Vertex color: {}\n'.format(self._numericToStr(self.getVertexColor()))
            buff += 'Edge visibility: {}\n'.format(self.getEdgeVisibility())
            buff += 'Edge color: {}\n'.format(self._numericToStr(self.getEdgeColor()))
            buff += 'Rendering algorithm: {}\n'.format(self.getRenderingAlgorithmAsString())
            buff += 'Point count: {}\n'.format(self.getNumberOfPoints())
            if self._mapper.GetScalarVisibility() > 0:
                buff += 'Scalar visibility On\n'
                buff += 'Color mode: {}\n'.format(self._mapper.GetColorModeAsString())
                buff += 'Scalar mode: {}\n'.format(self._mapper.GetScalarModeAsString())
            else: buff += 'Scalar visibility Off\n'
            mem = self.getMemorySize()
            if mem <= 1024: buff += 'Memory Size: {:.2f} KB\n'.format(mem)
            else: buff += 'Memory Size: {:.2f} MB\n'.format(mem/1024)
        else: buff = 'Empty mesh instance'
        return buff

    def __repr__(self) -> str:
        return 'SisypheMesh instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Private methods

    @staticmethod
    def _numericToStr(v: bool | int | float | list | tuple, d: int = 2) -> str:
        f = '{:.' + str(d) + 'f}'
        if isinstance(v, (int, bool)): r = str(v)
        elif isinstance(v, float): r = f.format(v)
        elif isinstance(v, (list, tuple)):
            r = list()
            for vi in v:
                if isinstance(vi, (int, bool)): r.append(str(vi))
                elif isinstance(vi, float): r.append(f.format(vi))
            r = ' '.join(r)
        else: r = v
        return r

    def _updatePolydata(self) -> None:
        if self._polydata is not None:
            self._mapper.SetInputData(self._polydata)
            self._mapper.UpdateInformation()
            self._mapper.Update()
            self._actor.SetMapper(self._mapper)

    def _updateNormals(self) -> None:
        if self._actor is not None:
            flt = vtkPolyDataNormals()
            flt.SetInputData(self._polydata)
            flt.SetFeatureAngle(60.0)
            flt.ComputePointNormalsOn()
            flt.ComputeCellNormalsOn()
            flt.AutoOrientNormalsOn()
            flt.ConsistencyOn()
            flt.SplittingOn()
            flt.Update()
            self._polydata = flt.GetOutput()
            self._updatePolydata()

    # Public methods

    def getReferenceID(self) -> str:
        return self._referenceID

    def setReferenceID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(ID, str): self._referenceID = ID
        elif isinstance(ID, sc.sisypheVolume.SisypheVolume): self._referenceID = ID.getID()
        else: self._referenceID = None

    def hasReferenceID(self) -> bool:
        return self._referenceID is not None

    def setName(self, name: str) -> None:
        if isinstance(name, str):
            self._name = name
        else: raise TypeError('parameter type {} is not str.'.format(name))

    def setNameFromFilename(self, filename: str) -> None:
        if isinstance(filename, str): self._name = splitext(basename(filename))[0]
        else: raise TypeError('parameter type {} is not str.'.format(filename))

    def setFilename(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        self._filename = filename
        if self._name == '': self.setNameFromFilename(filename)

    def getFilename(self) -> str:
        return self._filename

    def getDirname(self) -> str:
        return dirname(self._filename)

    def hasFilename(self) -> bool:
        return self._filename != ''

    def getName(self) -> str:
        return self._name

    def isEmpty(self) -> bool:
        return self._polydata is None

    def setActor(self, actor: vtkActor) -> None:
        if isinstance(actor, vtkActor):
            self._actor = actor
            self._mapper = actor.GetMapper()
            self._polydata = self._mapper.GetInput()
        else: raise TypeError('parameter type {} is not vtkActor.'.format(type(actor)))

    def setPolyData(self, data: vtkActor | vtkPolyDataMapper| vtkPolyData) -> None:
        prop = None
        if isinstance(data, vtkActor):
            prop = data.GetProperty()
            data = data.GetMapper().GetInput()
        elif isinstance(data, vtkPolyDataMapper):
            data = data.GetInput()
        elif isinstance(data, SisypheMesh):
            self._referenceID = data.getReferenceID()
            prop = data.getActor().GetProperty()
            data = data._polydata
        if isinstance(data, vtkPolyData):
            self._polydata = data
            self._updatePolydata()
            self._mapper.ScalarVisibilityOff()
            if prop is not None: self.copyPropertiesFromVtkProperty(prop)
        else: raise TypeError('parameter type {} is not vtkActor, vtkPolyDataMapper or vtkPolyData.'.format(type(data)))

    def copyFrom(self, data: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> None:
        prop = None
        if isinstance(data, vtkActor):
            prop = data.GetProperty()
            data = data.GetMapper().GetInput()
        elif isinstance(data, vtkPolyDataMapper):
            data = data.GetInput()
        elif isinstance(data, SisypheMesh):
            self._referenceID = data.getReferenceID()
            self._name = data._name
            prop = data.getActor().GetProperty()
            data = data._polydata
        if isinstance(data, vtkPolyData):
            if self._polydata is not None:
                del self._polydata
            self._polydata = vtkPolyData()
            self._polydata.DeepCopy(data)
            self._updatePolydata()
            self._mapper.ScalarVisibilityOff()
            if prop is not None: self.copyPropertiesFromVtkProperty(prop)
        else: raise TypeError('parameter type {} is not vtkActor, vtkPolyDataMapper or vtkPolyData.'.format(type(data)))

    def clear(self) -> None:
        del self._polydata
        self._polydata = None

    def getPolyData(self) -> vtkPolyData:
        return self._polydata

    def getPolyDataMapper(self) -> vtkPolyDataMapper:
        return self._mapper

    def getActor(self) -> vtkActor:
        return self._actor

    def getMemorySize(self) -> int:
        if self._polydata is not None:
            return self._polydata.GetActualMemorySize()

    def getNumberOfPoints(self) -> int:
        return self._polydata.GetNumberOfPoints()

    def getPoints(self) -> vtkPoints:
        return self._polydata.GetPoints()

    def setPoints(self, p: vtkPoints) -> None:
        if isinstance(p, vtkPoints):
            if p.GetNumberOfPoints() == self._polydata.GetNumberOfPoints():
                self._polydata.SetPoints(p)
                self._updatePolydata()
            else: raise ValueError('incorrect number of points in vtkPoints parameter.')
        else: raise TypeError('parameter type {} is not vtkPoints.'.format(type(p)))

    def setPosition(self, x: float, y: float, z: float) -> None:
        self._actor.SetPosition(x, y, z)

    def getPosition(self) -> vectorFloat3Type:
        return self._actor.GetPosition()

    def isDefaultPosition(self) -> bool:
        return self._actor.GetPosition() == (0.0, 0.0, 0.0)

    def getOrigin(self) -> vectorFloat3Type:
        return self._actor.GetOrigin()

    def setOrigin(self, x: float, y: float, z: float) -> None:
        self._actor.SetOrigin(x, y, z)

    def isDefaultOrigin(self) -> bool:
        return self._actor.GetOrigin() == (0.0, 0.0, 0.0)

    def getCenter(self) -> vectorFloat3Type:
        return self._actor.GetCenter()

    def setOriginFromReferenceVolume(self, v: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(v, sc.sisypheVolume.SisypheVolume):
            c = v.getCenter()
            self._actor.setOrigin(c[0], c[1], c[2])
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def setScale(self, sx: float, sy: float, sz: float) -> None:
        self._actor.SetScale(sx, sy, sz)

    def getScale(self) -> vectorFloat3Type:
        return self._actor.GetScale()

    def getBounds(self) -> tuple:
        return self._polydata.GetBounds()

    def setTransform(self, trf: SisypheTransform | vtkTransform) -> None:
        if isinstance(trf, sc.sisypheTransform.SisypheTransform): trf = trf.getVTKTransform()
        if isinstance(trf, vtkTransform): self._actor.SetUserMatrix(trf)

    def getTransform(self) -> SisypheTransform:
        trf = SisypheTransform()
        trf.setVTKMatrix4x4(self._actor.GetUserMatrix())
        return trf

    def applyTransform(self, trf: SisypheTransform | vtkTransform):
        if isinstance(trf, SisypheTransform): trf = trf.getVTKTransform()
        if isinstance(trf, vtkTransform):
            f = vtkTransformPolyDataFilter()
            f.SetTransform(trf)
            f.SetInputData(self._polydata)
            f.Update()
            self.setPolyData(f.GetOutput())

    # Rendering property methods

    def getVtkProperty(self) -> vtkProperty:
        return self._actor.GetProperty()

    def setVtkProperty(self, v: vtkProperty) -> None:
        if isinstance(v, vtkProperty):
            self._actor.SetProperty(v)
        else:
            raise TypeError('parameter type {} is not vtkProperty.'.format(type(v)))

    def copyPropertiesFromVtkProperty(self, v: vtkProperty) -> None:
        if isinstance(v, vtkProperty):
            c = vtkProperty()
            c.DeepCopy(v)
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(v)))

    def copyPropertiesFromVtkActor(self, v: vtkActor) -> None:
        if isinstance(v, vtkActor):
            c = vtkProperty()
            c.DeepCopy(v.GetProperty())
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not vtkActor.'.format(type(v)))

    def copyPropertiesFromMesh(self, mesh: SisypheMesh) -> None:
        if isinstance(mesh, SisypheMesh):
            c = vtkProperty()
            c.DeepCopy(mesh.getActor().GetProperty())
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def copyColorFromROI(self, roi: sc.sisypheROISisypheROI) -> None:
        if isinstance(roi, sc.sisypheROISisypheROI):
            c = roi.getColor()
            self.setColor(c[0], c[1], c[2])
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def setOpacity(self, alpha: float) -> None:
        if self._polydata is not None:
            if isinstance(alpha, float):
                if 0.0 <= alpha <= 1.0:
                    self._actor.GetProperty().SetOpacity(alpha)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(alpha))
            else: raise TypeError('parameter type {} is not float.'.format(type(alpha)))

    def getOpacity(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetOpacity()

    def setVisibility(self, v: bool) -> None:
        if self._polydata is not None:
            if isinstance(v, bool) and self._actor is not None:
                self._actor.SetVisibility(v)
            else: raise TypeError('parameter functype is not bool or int.')

    def setVisibilityOn(self) -> None:
        if self._polydata is not None:
            self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        if self._polydata is not None:
            self.setVisibility(False)

    def getVisibility(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetVisibility() > 0

    def setColor(self, r: float, g: float, b: float) -> None:
        """
            r   float, 0.0 <= red <= 1.0
            g   float, 0.0 <= green <= 1.0
            b   float, 0.0 <= blue <= 1.0
        """
        if self._polydata is not None:
            self._mapper.ScalarVisibilityOff()
            self._actor.GetProperty().SetColor(r, g, b)

    def getColor(self) -> vectorFloat3Type:
        """
            return (float, float, float), red, green, blue (0.0 <= value <= 1.0)
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetColor()

    def getScalarColorVisibility(self) -> bool:
        return self._mapper.GetScalarVisibility()

    def setScalarColorVisibilityOn(self) -> None:
        self._mapper.ScalarVisibilityOn()

    def setScalarColorVisibilityOff(self) -> None:
        self._mapper.ScalarVisibilityOff()

    def setScalarColorVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._mapper.SetScalarVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    def setLUT(self, lut: sc.sisypheVolume.SisypheVolume | SisypheLut | vtkLookupTable) -> None:
        if isinstance(lut, sc.sisypheVolume.SisypheVolume): lut = lut.display.getVTKLUT()
        if isinstance(lut, SisypheLut): lut = lut.getvtkLookupTable()
        if isinstance(lut, vtkLookupTable):
            self._mapper.SetScalarModeToUsePointData()
            self._mapper.SetColorModeToMapScalars()
            self._mapper.SetLookupTable(lut)
            self._mapper.UseLookupTableScalarRangeOff()
            # self._mapper.UseLookupTableScalarRangeOn()
            self._mapper.SetScalarRange(lut.GetRange())
            self._mapper.ScalarVisibilityOn()
        else: raise TypeError('parameter type {} is not vtkLookupTable, SisypheLut or SisypheVolume.'.format(type(lut)))

    def getLUT(self) -> vtkLookupTable:
        return self._mapper.GetLookupTable()

    def setPointScalarColorFromVolume(self,
                                      vol: sc.sisypheVolume.SisypheVolume,
                                      depth: cython.int = 0,
                                      feature: str = 'mean',
                                      wait: DialogWait | None = None) -> None:
        """
            vol     SisypheVolume
            depth   cython.int, signal depth in mm
            feature str, 'mean', 'min', 'max', 'sum'
        """
        if self._polydata is not None:
            if isinstance(vol, sc.sisypheVolume.SisypheVolume):
                img: sitkImage = vol.getSITKImage()
                n: cython.int = self._polydata.GetNumberOfPoints()
                if n > 0:
                    nw: int = n // 100
                    if wait is not None:
                        wait.setProgressRange(0, nw)
                        wait.setCurrentProgressValue(0)
                        wait.setProgressVisibility(nw > 0)
                    points: vtkPoints = self._polydata.GetPoints()
                    scalars: vtkFloatArray = vtkFloatArray()
                    scalars.SetNumberOfComponents(1)
                    scalars.SetNumberOfTuples(n)
                    scalars.SetName(vol.getName())
                    normals = self._polydata.GetPointData().GetNormals()
                    i: cython.int
                    c: cython.int = 0
                    v: cython.double
                    p1: cython.double[3]
                    p2: cython.double[3]
                    if depth == 0:
                        for i in range(n):
                            p1 = points.GetPoint(i)
                            p2 = vol.getVoxelCoordinatesFromWorldCoordinates(p1)
                            v = float(img[p2[0], p2[1], p2[2]])
                            scalars.SetTuple1(i, v)
                            c += 1
                            if wait is not None and c == 100:
                                c = 0
                                wait.incCurrentProgressValue()
                    else:
                        f: cython.int
                        c: cython.int = 0
                        if feature == 'mean': f = 0
                        elif feature == 'min': f = 1
                        elif feature == 'max': f = 2
                        elif feature == 'sum': f = 3
                        else: f = 0
                        v1: cython.double[3]
                        v: ndarray = zeros(10, dtype=np.double)
                        for i in range(n):
                            for j in range(depth):
                                p1 = points.GetPoint(i)
                                v1 = normals.GetPoint(i)
                                p1[0] -= v1[0]
                                p1[1] -= v1[1]
                                p1[2] -= v1[2]
                                p2 = vol.getVoxelCoordinatesFromWorldCoordinates(p1)
                                v[j] = img[p2[0], p2[1], p2[2]]
                            if f == 0: scalars.SetTuple1(i, v.mean())
                            elif f == 1: scalars.SetTuple(i, v.min())
                            elif f == 2: scalars.SetTuple(i, v.max())
                            elif f == 3: scalars.SetTuple(i, v.sum())
                            c += 1
                            if wait is not None and c == 100:
                                c = 0
                                wait.incCurrentProgressValue()
                    self._polydata.GetPointData().SetScalars(scalars)
                    self._polydata.GetPointData().SetActiveScalars(vol.getName())
                    self.setLUT(vol.display.getLUT())
                    self._mapper.UpdateInformation()
                    self._mapper.Update()
                    self._actor = vtkActor()
                    self._actor.SetMapper(self._mapper)
                    if wait is not None: wait.setProgressVisibility(False)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setAmbient(self, v: float) -> None:
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetAmbient(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getAmbient(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetAmbient()

    def setDiffuse(self, v: float) -> None:
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetDiffuse(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getDiffuse(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetDiffuse()

    def setSpecular(self, v: float) -> None:
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetSpecular(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecular(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetSpecular()

    def setSpecularPower(self, v: float) -> None:
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 50.0:
                    self._actor.GetProperty().SetSpecularPower(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 50.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecularPower(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetSpecularPower()

    def setMetallic(self, v: float) -> None:
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetMetallic(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getMetallic(self) -> float:
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            return self._actor.GetProperty().GetMetallic()

    def setRoughness(self, v: float) -> None:
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetRoughness(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getRoughness(self) -> float:
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            return self._actor.GetProperty().GetRoughness()

    def setFlatRendering(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToFlat()

    def setGouraudRendering(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToGouraud()

    def setPhongRendering(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToPhong()

    def setPBRRendering(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToPBR()

    def setRenderingAlgorithm(self, r: int) -> None:
        self._actor.GetProperty().SetInterpolation(r)

    def getRenderingAlgorithmAsString(self) -> str:
        if self._polydata is not None:
            return self._actor.GetProperty().GetInterpolationAsString()

    def getRenderingAlgorithm(self) -> int:
        if self._polydata is not None:
            return self._actor.GetProperty().GetInterpolation()

    def setRenderPointsAsSpheresOn(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().RenderPointsAsSpheresOn()

    def setRenderPointsAsSpheresOff(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().RenderPointsAsSpheresOff()

    def getRenderPointsAsSpheres(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetProperty().GetRenderPointsAsSpheres() > 0

    def setRenderLinesAsTubesOn(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().RenderLinesAsTubesOn()

    def setRenderLinesAsTubesOff(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().RenderLinesAsTubesOff()

    def getRenderLinesAsTubes(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetProperty().GetRenderLinesAsTubes() > 0

    def setVertexVisibilityOn(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().VertexVisibilityOn()

    def setVertexVisibilityOff(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().VertexVisibilityOff()

    def getVertexVisibility(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetProperty().GetVertexVisibility() > 0

    def setVertexColor(self, r: float, g: float, b: float) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetVertexColor(r, g, b)

    def getVertexColor(self) -> vectorFloat3Type:
        if self._polydata is not None:
            return self._actor.GetProperty().GetVertexColor()

    def setEdgeVisibilityOn(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().EdgeVisibilityOn()

    def setEdgeVisibilityOff(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().EdgeVisibilityOff()

    def getEdgeVisibility(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetProperty().GetEdgeVisibility() > 0

    def setEdgeColor(self, r: float, g: float, b: float) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetEdgeColor(r, g, b)

    def getEdgeColor(self) -> vectorFloat3Type:
        if self._polydata is not None:
            return self._actor.GetProperty().GetEdgeColor()

    def setLineWidth(self, v: float) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetLineWidth(v)

    def getLineWidth(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetLineWidth()

    def setPointSize(self, v: float) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().SetPointSize(v)

    def getPointSize(self) -> float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetPointSize()

    def getShading(self) -> bool:
        if self._polydata is not None:
            return self._actor.GetProperty().GetShading() > 0

    def shadingOn(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().ShadingOn()

    def shadingOff(self) -> None:
        if self._polydata is not None:
            self._actor.GetProperty().ShadingOff()

    # Mesh sources

    def createLine(self, p1: vectorFloat3Type, p2: vectorFloat3Type, d) -> None:
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        line.Update()
        self.setPolyData(line.GetOutput())
        self.setLineWidth(d)
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Line#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createTube(self, p1: vectorFloat3Type, p2: vectorFloat3Type, r, sides: int) -> None:
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        line.Update()
        tube = vtkTubeFilter()
        tube.SetInputConnection(line.GetOutputPort())
        tube.SetRadius(r)
        tube.SetNumberOfSides(sides)
        tube.Update()
        self.setPolyData(tube.GetOutput())
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Tube#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createSphere(self, r: float, p: vectorFloat3Type = (0.0, 0.0, 0.0), res: int = 64) -> None:
        """
            r   float, sphere radius (mm)
            p   [float]*3, center coordinates
            res int, set the number of points in the latitude and longitude directions
                default=64
        """
        sphere = vtkSphereSource()
        sphere.SetThetaResolution(res)
        sphere.SetPhiResolution(res)
        sphere.SetRadius(r)
        sphere.Update()
        polydata = sphere.GetOutput()
        if p != (0.0, 0.0, 0.0):
            trf = vtkTransform()
            trf.Translate(p)
            f = vtkTransformPolyDataFilter()
            f.SetTransform(trf)
            f.SetInputData(polydata)
            f.Update()
            polydata = f.GetOutput()
        self.setPolyData(polydata)
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Sphere#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createCube(self, dx: float, dy: float, dz: float, p: vectorFloat3Type = (0.0, 0.0, 0.0)) -> None:
        """
            dx  float, length of the cube in the x-direction (mm)
            dy  float, length of the cube in the y-direction (mm)
            dz  float, length of the cube in the z-direction (mm)
            p   [float]*3, position coordinates
        """
        cube = vtkCubeSource()
        cube.SetXLength(dx)
        cube.SetYLength(dy)
        cube.SetZLength(dz)
        cube.Update()
        polydata = sphere.GetOutput()
        if p != (0.0, 0.0, 0.0):
            trf = vtkTransform()
            trf.Translate(p)
            f = vtkTransformPolyDataFilter()
            f.SetTransform(trf)
            f.SetInputData(polydata)
            f.Update()
            polydata = f.GetOutput()
        self.setPolyData(polydata)
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Cube#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createOuterSurface(self,
                           img: sc.sisypheVolume.SisypheVolume,
                           seg: str = 'otsu',
                           fill: float = 1000.0,
                           decimate: float = 1.0,
                           clean: bool = False,
                           smooth: str = 'sinc',
                           niter: int = 10,
                           factor: float = 0.1,
                           algo: str = 'flying',
                           largest: bool = True) -> None:
        """
            img         SisypheVol
            seg         str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                                'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                        algorithm used for automatic object/background segmentation
            fill        float, identify and fill holes in mesh
            decimate    0.0 <= float <= 1.0, mesh points reduction percentage
            clean       bool, merge duplicate points, and/or remove unused points and/or remove degenerate cells
            smooth      str in ['sinc', 'laplacian'], smoothing algorithm
            niter       int, number of iterations, default value 20
            factor      0.0 <= float <= 1.0, lower values produce more smoothing
                        if smooth='sinc', passband factor
                        if smooth='laplacian', relaxation factor
            algo        str in ['contour', 'marching', 'flying'], algorithm used to generate isosurface
        """

        if isinstance(img, sc.sisypheVolume.SisypheVolume):
            seg = seg.lower()
            # v = img.getBackgroundThreshold(algo=seg)
            # self.createIsosurface(img, v, fill, decimate, clean, smooth, niter, factor, algo, largest)
            roi = img.getMaskROI(algo=seg, morpho='', kernel=0, fill='2d')
            self.createFromROI(roi, fill, decimate, clean, smooth, niter, factor, algo, largest)
            self._name = 'Outer surface'
            self._filename = join(img.getDirname(), self._name + self.getFileExt())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def createIsosurface(self,
                         img: sc.sisypheVolume.SisypheVolume,
                         value: float,
                         fill: float = 1000.0,
                         decimate: float = 1.0,
                         clean: bool = False,
                         smooth: str = 'sinc',
                         niter: int = 10,
                         factor: float = 0.1,
                         algo: str = 'flying',
                         largest: bool = False) -> None:
        """
            img         SisypheVol
            value       float, threshold used as isovalue to generate isosurface
            fill        float, identify and fill holes in mesh
            decimate    0.0 <= float <= 1.0, mesh points reduction percentage
            clean       bool, merge duplicate points, and/or remove unused points and/or remove degenerate cells
            smooth      str in ['sinc', 'laplacian'], smoothing algorithm
            niter       int, number of iterations, default value 20
            factor      0.0 <= float <= 1.0, lower values produce more smoothing
                        if smooth='sinc', passband factor
                        if smooth='laplacian', relaxation factor
            algo        str in ['contour', 'marching', 'flying'], algorithm used to generate isosurface
        """
        if isinstance(img, sc.sisypheVolume.SisypheVolume):
            inf, sup = img.getDisplay().getRange()
            if inf <= value <= sup:
                # Convert image datatype to float if not
                if img.isFloatDatatype(): vtkimg = img.getVTKImage()
                else:
                    f = vtkImageCast()
                    f.SetInputData(img.getVTKImage())
                    f.SetOutputScalarTypeToFloat()
                    f.Update()
                    vtkimg = f.GetOutput()
                QApplication.processEvents()
                # Generate isosurface
                algo = algo.lower()
                if algo == 'contour': f = vtkContourFilter()
                elif algo == 'marching': f = vtkMarchingCubes()
                elif algo == 'flying': f = vtkFlyingEdges3D()
                else: raise ValueError('parameter algorithm {} is not implemented.'.format(algo))
                f.SetInputData(vtkimg)
                f.ComputeNormalsOff()
                f.SetValue(0, value)
                f.Update()
                result = f.GetOutput()
                QApplication.processEvents()
                # Largest isosurface
                if isinstance(largest, bool):
                    if largest:
                        f = vtkPolyDataConnectivityFilter()
                        f.SetInputData(result)
                        f.SetExtractionModeToLargestRegion()
                        f.ScalarConnectivityOff()
                        f.Update()
                        result = f.GetOutput()
                QApplication.processEvents()
                # Decimate
                if isinstance(decimate, float):
                    if 0.1 <= decimate < 1.0:
                        if result.GetCellType(0) != VTK_TRIANGLE:
                            f = vtkTriangleFilter()
                            f.SetInputData(result)
                            f.Update()
                            result = f.GetOutput()
                        f = vtkDecimatePro()
                        f.SetInputData(result)
                        f.PreserveTopologyOn()
                        f.SetTargetReduction(decimate)
                        f.Update()
                        result = f.GetOutput()
                QApplication.processEvents()
                # Fill holes
                if isinstance(fill, float):
                    if fill > 0.0:
                        f = vtkFillHolesFilter()
                        f.SetInputData(result)
                        f.SetHoleSize(fill)
                        f.Update()
                        result = f.GetOutput()
                QApplication.processEvents()
                # Clean
                if isinstance(clean, bool):
                    if clean:
                        f = vtkCleanPolyData()
                        f.SetInputData(result)
                        f.Update()
                        result = f.GetOutput()
                QApplication.processEvents()
                # Smooth
                if isinstance(smooth, str):
                    smooth = smooth.lower()
                    f = None
                    if smooth == 'sinc':
                        f = vtkWindowedSincPolyDataFilter()
                        f.SetInputData(result)
                        f.SetNumberOfIterations(niter)
                        f.SetFeatureEdgeSmoothing(True)
                        f.SetBoundarySmoothing(True)
                        f.SetPassBand(factor)
                        f.NormalizeCoordinatesOn()
                        f.NonManifoldSmoothingOn()
                    elif smooth == 'laplacian':
                        f = vtkSmoothPolyDataFilter()
                        f.SetInputData(result)
                        f.SetNumberOfIterations(niter)
                        f.SetFeatureEdgeSmoothing(True)
                        f.SetBoundarySmoothing(True)
                        f.SetRelaxationFactor(factor)
                    if f is not None:
                        f.Update()
                        result = f.GetOutput()
                QApplication.processEvents()
                # Create triangle strips
                f = vtkStripper()
                f.SetInputData(result)
                f.Update()
                result = f.GetOutput()
                QApplication.processEvents()
                # Calc normals
                f = vtkPolyDataNormals()
                f.SetInputData(result)
                f.SetFeatureAngle(60.0)
                f.ComputePointNormalsOn()
                f.ComputeCellNormalsOn()
                f.AutoOrientNormalsOn()
                f.ConsistencyOn()
                f.SplittingOn()
                f.Update()
                result = f.GetOutput()
                QApplication.processEvents()
                self.setPolyData(result)
                self.setColor(1.0, 0.0, 0.0)
                self._name = 'isosurface#{}'.format(value)
                self._filename = join(img.getDirname(), self._name + self.getFileExt())
                self.setReferenceID(img)
            else: raise ValueError('parameter value {} is not between {} and {}.'.format(value, inf, sup))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def createFromROI(self,
                      roi: sc.sisypheROI.SisypheROI,
                      fill: float = 1000.0,
                      decimate: float = 1.0,
                      clean: bool = False,
                      smooth: str = 'sinc',
                      niter: int = 10,
                      factor: float = 0.1,
                      algo: str = 'flying',
                      largest: bool = False) -> None:
        """
            roi         SisypheROI
            fill        float, identify and fill holes in mesh
            decimate    0.0 <= float <= 1.0, mesh points reduction percentage
            clean       bool, merge duplicate points, and/or remove unused points and/or remove degenerate cells
            smooth      str in ['sinc', 'laplacian'], smoothing algorithm
            niter       int, number of iterations, default value 20
            factor      0.0 <= float <= 1.0, lower values produce more smoothing
                        if smooth='sinc', passband factor
                        if smooth='laplacian', relaxation factor
            algo        str in ['contour', 'marching', 'flying'], algorithm used to generate isosurface
        """
        if isinstance(roi, sc.sisypheROI.SisypheROI):
            mask = roi.getSITKImage()
            # Fill mask in each 2D axial slice
            if fill > 0.0:
                f = BinaryFillholeImageFilter()
                for i in range(mask.GetSize()[2]):
                    slc = mask[:, :, i]
                    slc = f.Execute(slc)
                    mask[:, :, i] = slc
                    QApplication.processEvents()
            # Convert to float
            mask = Cast(mask, sitkFloat32)
            QApplication.processEvents()
            # Smoothing
            mask *= 100
            mask = SmoothingRecursiveGaussian(mask, [1.0, 1.0, 1.0])
            QApplication.processEvents()
            img = sc.sisypheVolume.SisypheVolume(mask)
            self.createIsosurface(img, 50, fill, decimate, clean, smooth, niter, factor, algo, largest)
            self._name = roi.getName()
            self._filename = join(roi.getDirname(), self._name + self.getFileExt())
            c = roi.getColor()
            self.setColor(c[0], c[1], c[2])
            self.setReferenceID(roi.getReferenceID())
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    # Processing methods

    def decimate(self, v: float, updatenormals: bool = True) -> None:
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.1 <= v < 1.0:
                    # Convert to triangle mesh if not
                    if self._polydata.GetCellType(0) != VTK_TRIANGLE:
                        f = vtkTriangleFilter()
                        f.SetInputData(self._polydata)
                        f.Update()
                        self._polydata = f.GetOutput()
                    f = vtkDecimatePro()
                    f.SetInputData(self._polydata)
                    f.PreserveTopologyOn()
                    f.SetTargetReduction(v)
                    f.Update()
                    self.setPolyData(f.GetOutput())
                    if updatenormals: self._updateNormals()
                else: raise ValueError('parameter value {} is not between 0.1 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))
        else: raise ValueError('vtkPolyData is empty.')

    def clean(self, updatenormals: bool = True) -> None:
        if self._polydata is not None:
            f = vtkCleanPolyData()
            f.SetInputData(self._polydata)
            f.Update()
            self.setPolyData(f.GetOutput())
            if updatenormals: self._updateNormals()
        else: raise ValueError('vtkPolyData is empty.')

    def sincSmooth(self,
                   niter: int = 10,
                   passband: float = 0.1,
                   edge: bool = True,
                   boundary: bool = True,
                   updatenormals: bool = True) -> None:
        """
            10 < niter < 20
            0.0 < passband < 2.0, default 0.1
        """
        if self._polydata is not None:
            f = vtkWindowedSincPolyDataFilter()
            f.SetInputData(self._polydata)
            f.SetNumberOfIterations(niter)
            f.SetFeatureEdgeSmoothing(edge)
            f.SetBoundarySmoothing(boundary)
            f.SetPassBand(passband)
            f.NormalizeCoordinatesOn()
            f.NonManifoldSmoothingOn()
            f.Update()
            self.setPolyData(f.GetOutput())
            if updatenormals: self._updateNormals()
        else: raise ValueError('vtkPolyData is empty.')

    def laplacianSmooth(self,
                        niter: int = 20,
                        relax: float = 0.1,
                        edge: bool = True,
                        boundary: bool = True,
                        updatenormals: bool = True) -> None:
        """
            10 < niter < 100
            0.0 < passband < 1.0, default 0.1
        """
        if self._polydata is not None:
            f = vtkSmoothPolyDataFilter()
            f.SetInputData(self._polydata)
            f.SetNumberOfIterations(niter)
            f.SetRelaxationFactor(relax)
            f.SetFeatureEdgeSmoothing(edge)
            f.SetBoundarySmoothing(boundary)
            f.Update()
            self.setPolyData(f.GetOutput())
            if updatenormals: self._updateNormals()
        else: raise ValueError('vtkPolyData is empty.')

    def fillHoles(self, size: float = 1000.0, updatenormals: bool = True) -> None:
        if self._polydata is not None:
            f = vtkFillHolesFilter()
            f.SetInputData(self._polydata)
            f.SetHoleSize(size)
            f.Update()
            self.setPolyData(f.GetOutput())
            if updatenormals: self._updateNormals()
        else: raise ValueError('vtkPolyData is empty.')

    def filter(self,
               fill: float = 1000.0,
               decimate: float = 1.0,
               clean: bool = False,
               smooth: str = 'sinc',
               niter: int = 10,
               factor: float = 0.1) -> None:
        """
            fill        float, fill holes in mesh
            decimate    0.0 <= float <= 1.0, mesh points reduction percentage
            clean       bool, merge duplicate points, and/or remove unused points and/or remove degenerate cells
            smooth      str in ['sinc', 'laplacian'], smoothing algorithm
            niter       int, number of iterations, default value 20
            factor      0.0 <= float <= 1.0, lower values produce more smoothing
                        if smooth='sinc', passband factor
                        if smooth='laplacian', relaxation factor
        """
        if self._polydata is not None:
            result = self._polydata
            # Decimate
            if isinstance(decimate, float):
                if 0.1 <= decimate < 1.0:
                    if result.GetCellType(0) != VTK_TRIANGLE:
                        f = vtkTriangleFilter()
                        f.SetInputData(result)
                        f.Update()
                        result = f.GetOutput()
                    f = vtkDecimatePro()
                    f.SetInputData(result)
                    f.PreserveTopologyOn()
                    f.SetTargetReduction(decimate)
                    f.Update()
                    result = f.GetOutput()
            # Fill holes
            if isinstance(fill, float):
                if fill > 0.0:
                    f = vtkFillHolesFilter()
                    f.SetInputData(result)
                    f.SetHoleSize(fill)
                    f.Update()
                    result = f.GetOutput()
            # Clean
            if isinstance(clean, bool):
                if clean:
                    f = vtkCleanPolyData()
                    f.SetInputData(result)
                    f.Update()
                    result = f.GetOutput()
            # Smooth
            if isinstance(smooth, str):
                smooth = smooth.lower()
                f = None
                if smooth == 'sinc':
                    f = vtkWindowedSincPolyDataFilter()
                    f.SetInputData(result)
                    f.SetNumberOfIterations(niter)
                    f.SetFeatureEdgeSmoothing(True)
                    f.SetBoundarySmoothing(True)
                    f.SetPassBand(factor)
                    f.NormalizeCoordinatesOn()
                    f.NonManifoldSmoothingOn()
                elif smooth == 'laplacian':
                    f = vtkSmoothPolyDataFilter()
                    f.SetInputData(result)
                    f.SetNumberOfIterations(niter)
                    f.SetFeatureEdgeSmoothing(True)
                    f.SetBoundarySmoothing(True)
                    f.SetRelaxationFactor(factor)
                if f is not None:
                    f.Update()
                    result = f.GetOutput()
            # Create triangle strips
            f = vtkStripper()
            f.SetInputData(result)
            f.Update()
            result = f.GetOutput()
            # Calc normals
            f = vtkPolyDataNormals()
            f.SetInputData(result)
            f.SetFeatureAngle(60.0)
            f.ComputePointNormalsOn()
            f.ComputeCellNormalsOn()
            f.AutoOrientNormalsOn()
            f.ConsistencyOn()
            f.SplittingOn()
            f.Update()
            result = f.GetOutput()
            # Result
            self._name = 'filter {}'.format(self._name)
            self.setPolyData(result)
        else: raise ValueError('vtkPolyData is empty.')

    def combinePolyData(self, data: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> None:
        if self._polydata is not None:
            name = ''
            if isinstance(data, vtkActor):
                data = data.GetMapper().GetInput()
            elif isinstance(data, vtkPolyDataMapper):
                data = data.GetInput()
            elif isinstance(data, SisypheMesh):
                name = data._name
                data = data._polydata
            if isinstance(data, vtkPolyData):
                fcombine = vtkAppendPolyData()
                fcombine.AddInputData(self._polydata)
                fcombine.AddInputData(data)
                fcombine.Update()
                fclean = vtkCleanPolyData()
                fclean.SetInputConnection(fcombine.GetOutputPort())
                fclean.Update()
                self.setPolyData(fclean.GetOutput())
                self._name = 'Combine {}'.format(self._name)
                if name != '': self._name = self._name + ' {}'.format(name)
            else: raise TypeError('parameter functype is not SisypheMesh, vtkActor, vtkPolyDataMapper or vtkPolydata.')
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def union(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        if self._polydata is not None:
            roi = self.convertToSisypheROI(refimg=None)
            if self._name[:5] != 'Union': name = 'Union {}'.format(self._name)
            else: name = self._name
            if not isinstance(datas, list): datas = [datas]
            for data in datas:
                if isinstance(data, SisypheMesh):
                    roi = roi | data.convertToSisypheROI(refimg=None)
                    QApplication.processEvents()
                    if data._name != '': name += ' {}'.format(data._name)
                else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(data)))
            roi.setName(name)
            roi.setReferenceID(self.getReferenceID())
            if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
            else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def intersection(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        if self._polydata is not None:
            roi = self.convertToSisypheROI(refimg=None)
            if self._name[:12] != 'Intersection': name = 'Intersection {}'.format(self._name)
            else: name = self._name
            if not isinstance(datas, list): datas = [datas]
            for data in datas:
                if isinstance(data, SisypheMesh):
                    roi2 = data.convertToSisypheROI(refimg=None)
                    roi = roi & roi2
                    QApplication.processEvents()
                    if data._name != '': name += ' {}'.format(data._name)
                else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(data)))
            roi.setName(name)
            roi.setReferenceID(self.getReferenceID())
            if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
            else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def difference(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        if self._polydata is not None:
            roi = self.convertToSisypheROI(refimg=None)
            if self._name[:10] != 'Difference': name = 'Difference {}'.format(self._name)
            else: name = self._name
            if not isinstance(datas, list): datas = [datas]
            if isinstance(datas[0], SisypheMesh):
                roi2 = datas[0].convertToSisypheROI(refimg=None)
                if len(datas) > 1:
                    for i in range(1, len(datas)):
                        if isinstance(datas[i], SisypheMesh):
                            roi3 = datas[i].convertToSisypheROI(refimg=None)
                            roi2 = roi2 | roi3
                            QApplication.processEvents()
                            if datas[i].getName() != '': name += ' {}'.format(datas[i].getName())
                        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(data)))
                roi = roi - roi2
                QApplication.processEvents()
                roi.setName(name)
                roi.setReferenceID(self.getReferenceID())
                if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
                else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def dilate(self, mm: float) -> None:
        if isinstance(mm, (float, int)):
            if self._polydata is not None:
                normals = self._polydata.GetPointData().GetNormals()
                points = self._polydata.GetPoints()
                for i in range(self._polydata.GetNumberOfPoints()):
                    p = list(points.GetPoint(i))
                    n = normals.GetTuple(i)
                    p[0] += n[0] * mm
                    p[1] += n[1] * mm
                    p[2] += n[2] * mm
                    points.SetPoint(i, p)
                self._updatePolydata()
                self._name = 'Dilate#{} {}'.format(mm, self._name)
            else: raise ValueError('Mesh vtkPolyData is empty.')
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def erode(self, mm: float) -> None:
        if isinstance(mm, (float, int)):
            if self._polydata is not None:
                normals = self._polydata.GetPointData().GetNormals()
                points = self._polydata.GetPoints()
                for i in range(self._polydata.GetNumberOfPoints()):
                    p = list(points.GetPoint(i))
                    n = normals.GetTuple(i)
                    p[0] -= n[0] * mm
                    p[1] -= n[1] * mm
                    p[2] -= n[2] * mm
                    points.SetPoint(i, p)
                self._updatePolydata()
                self._name = 'Erode#{} {}'.format(mm, self._name)
            else: raise ValueError('Mesh vtkPolyData is empty.')
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def update(self) -> None:
        self._mapper.UpdateInformation()
        self._mapper.Update()

    # Polydata features

    def getMeshVolume(self) -> float:
        if self._polydata is not None:
            f = vtkMassProperties()
            f.SetInputData(self._polydata)
            return f.GetVolume()

    def getMeshSurface(self) -> float:
        if self._polydata is not None:
            f = vtkMassProperties()
            f.SetInputData(self._polydata)
            return f.GetSurfaceArea()

    def getCenterOfMass(self) -> vectorFloat3Type:
        if self._polydata is not None:
            f = vtkCenterOfMass()
            f.SetInputData(self._polydata)
            f.SetUseScalarsAsWeights(False)
            f.Update()
            return f.GetCenter()

    def getPrincipalAxis(self) -> tuple[vectorFloat3Type, vectorFloat3Type, vectorFloat3Type, vectorFloat3Type, vectorFloat3Type]:
        if self._polydata is not None:
            f = vtkOBBTree()
            center = [0.0, 0.0, 0.0]
            vmax = [0.0, 0.0, 0.0]
            vmid = [0.0, 0.0, 0.0]
            vmin = [0.0, 0.0, 0.0]
            size = [0.0, 0.0, 0.0]
            f.ComputeOBB(self._polydata, center, vmax, vmid, vmin, size)
            return center, vmax, vmid, vmin, size

    def getDistanceFromSurfaceToPoint(self, p: vectorFloat3Type) -> tuple[float, vectorFloat3Type]:
        """
            p  [float, float, float], point coordinates
            return  float, distance between p and surface of the mesh
                    (float, list[float, float, float]), distance and closest surface point of the mesh
        """
        if self._polydata is not None:
            if isinstance(p, (list, tuple)):
                if len(p) == 3 and all([isinstance(i, float) for i in p]):
                    f = vtkImplicitPolyDataDistance()
                    f.SetInput(self._polydata)
                    cp = [0.0, 0.0, 0.0]
                    d = f.EvaluateFunctionAndGetClosestPoint(p, cp)
                    return d, cp
                else: raise TypeError('invalid list/tuple item count or item type is not float.')
            else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def getDistanceFromSurfaceToSurface(self,
                                        mesh: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> tuple[float, float]:
        """
            mesh    vtkPolyData | vtkPolyDataMapper | vtkActor | SisypheMesh
            return  (float, float), minimum and maximum distances
        """
        if self._polydata is not None:
            if isinstance(mesh, vtkActor):
                mesh = mesh.GetMapper().GetInput()
            elif isinstance(mesh, vtkPolyDataMapper):
                mesh = mesh.GetInput()
            elif isinstance(mesh, SisypheMesh):
                mesh = mesh._polydata
            if isinstance(mesh, vtkPolyData):
                f = vtkDistancePolyDataFilter()
                f.SignedDistanceOff()
                f.SetInputData(0, self._polydata)
                f.SetInputData(1, mesh)
                f.Update()
                vmin, vmax = f.GetSecondDistanceOutput().GetPointData().GetScalars().GetRange()
                return vmin, vmax

    def isPointInside(self, p: vectorFloat3Type) -> bool:
        """
            p  [float, float, float], point coordinates
            return  bool
        """
        if self._polydata is not None:
            if isinstance(p, (list, tuple)):
                if len(p) == 3 and all([isinstance(i, float) for i in p]):
                    f = vtkOBBTree()
                    f.SetDataSet(self._polydata)
                    f.BuildLocator()
                    return f.InsideOrOutside(p) < 0.0
                else: raise TypeError('invalid list/tuple item count or item type is not float.')
            else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    def isPointOutside(self, p: vectorFloat3Type) -> bool:
        """
            p  list[float, float, float], point coordinates
            return  bool
        """
        if self._polydata is not None:
            if isinstance(p, (list, tuple)):
                if len(p) == 3 and all([isinstance(i, float) for i in p]):
                    f = vtkOBBTree()
                    f.SetDataSet(self._polydata)
                    f.BuildLocator()
                    return f.InsideOrOutside(p) > 0.0
                else: raise TypeError('invalid list/tuple item count or item type is not float.')
            else: raise TypeError('parameter type {} is not list or tuple.'.format(type(p)))

    # Image conversion methods

    def convertToVTKImage(self, refimg: sc.sisypheVolume.SisypheVolume, tol: float = 0.0) -> vtkImageData:
        if self._polydata is not None:
            if refimg is None:
                spacing = (1.0, 1.0, 1.0)
                origin = (0.0, 0.0, 0.0)
                size = (256, 256, 256)
            elif isinstance(refimg, sc.sisypheVolume.SisypheVolume):
                spacing = refimg.getSpacing()
                origin = refimg.getOrigin()
                size = refimg.getSize()
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))
            # vtkPolyData to vtkImageStencil
            stencil = vtkPolyDataToImageStencil()
            stencil.SetTolerance(tol)
            stencil.SetInputData(self._polydata)
            stencil.SetOutputOrigin(origin)
            stencil.SetOutputSpacing(spacing)
            stencil.SetOutputWholeExtent(0, size[0]-1, 0, size[1]-1, 0, size[2]-1)
            stencil.Update()
            # vtkImageStencil to vtkImageData
            stencil2img = vtkImageStencilToImage()
            stencil2img.SetInputData(stencil.GetOutput())
            stencil2img.SetOutsideValue(0)
            stencil2img.SetInsideValue(1)
            stencil2img.Update()
            img = stencil2img.GetOutput()
            return img

    def convertToSisypheROI(self,
                            refimg: sc.sisypheVolume.SisypheVolume,
                            tol: float = 0.0) -> sc.sisypheROI.SisypheROI:
        if self._polydata is not None:
            if refimg is None or isinstance(refimg, sc.sisypheVolume.SisypheVolume):
                img = self.convertToVTKImage(refimg, tol)
                roi = sc.sisypheROI.SisypheROI()
                roi.copyFromVTKImage(img)
                roi.setName(self.getName())
                roi.setColor(rgb=self.getColor())
                if refimg is None: roi.setReferenceID(self.getReferenceID())
                else: roi.setReferenceID(refimg.getID())
                return roi
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))

    def convertToSisypheVolume(self,
                               refimg: sc.sisypheVolume.SisypheVolume,
                               tol: float = 0.0) -> sc.sisypheVolume.SisypheVolume:
        if self._polydata is not None:
            if refimg is None or isinstance(refimg, sc.sisypheVolume.SisypheVolume):
                img = self.convertToVTKImage(refimg, tol)
                vol = sc.sisypheVolume.SisypheVolume()
                vol.copyFromVTKImage(img)
                return vol
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))

    # IO Public methods

    def loadFromOBJ(self, filename: str) -> None:
        self._actor = readMeshFromOBJ(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromSTL(self, filename: str) -> None:
        self._actor = readMeshFromSTL(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromVTK(self, filename: str) -> None:
        self._actor = readMeshFromVTK(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromXMLVTK(self, filename: str) -> None:
        self._actor = readMeshFromXMLVTK(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def ParseXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            item = doc.getElementsByTagName('XMESH')
            if len(item) > 0:
                for node in item[0].childNodes:
                    if node.nodeName == 'ReferenceID':
                        if node.hasChildNodes(): self.setReferenceID(node.firstChild.data)
                        else: self.setReferenceID('')
                    elif node.nodeName == 'Name': self.setName(node.firstChild.data)
                    elif node.nodeName == 'Color':
                        r = node.firstChild.data.split(' ')
                        self.setColor(float(r[0]), float(r[1]), float(r[2]))
                    elif node.nodeName == 'Opacity': self.setOpacity(float(node.firstChild.data))
                    elif node.nodeName == 'Ambient': self.setAmbient(float(node.firstChild.data))
                    elif node.nodeName == 'Diffuse': self.setDiffuse(float(node.firstChild.data))
                    elif node.nodeName == 'Specular': self.setSpecular(float(node.firstChild.data))
                    elif node.nodeName == 'SpecularPower': self.setSpecularPower(float(node.firstChild.data))
                    elif node.nodeName == 'Metallic': self.setMetallic(float(node.firstChild.data))
                    elif node.nodeName == 'Roughness': self.setRoughness(float(node.firstChild.data))
                    elif node.nodeName == 'RenderingAlgorithm':
                        r = node.firstChild.data
                        if r == 'Flat': self.setFlatRendering()
                        elif r == 'Gouraud': self.setGouraudRendering()
                        elif r == 'PBR': self.setPBRRendering()
                        elif r == 'Phong': self.setPhongRendering()
                        else: self.setGouraudRendering()
                    elif node.nodeName == 'RenderPointsAsSpheres':
                        r = node.firstChild.data == 'True'
                        if r: self.setRenderPointsAsSpheresOn()
                        else: self.setRenderPointsAsSpheresOff()
                    elif node.nodeName == 'RenderLinesAsTubes':
                        r = node.firstChild.data == 'True'
                        if r: self.setRenderLinesAsTubesOn()
                        else: self.setRenderLinesAsTubesOff()
                    elif node.nodeName == 'VertexVisibility':
                        r = node.firstChild.data == 'True'
                        if r: self.setVertexVisibilityOn()
                        else: self.setVertexVisibilityOff()
                    elif node.nodeName == 'VertexColor':
                        r = node.firstChild.data.split(' ')
                        self.setVertexColor(float(r[0]), float(r[1]), float(r[2]))
                    elif node.nodeName == 'EdgeVisibility':
                        r = node.firstChild.data == 'True'
                        if r: self.setEdgeVisibilityOn()
                        else: self.setEdgeVisibilityOff()
                    elif node.nodeName == 'EdgeColor':
                        r = node.firstChild.data.split(' ')
                        self.setEdgeColor(float(r[0]), float(r[1]), float(r[2]))
                    elif node.nodeName == 'LineWidth': self.setLineWidth(float(node.firstChild.data))
                    elif node.nodeName == 'PointSize': self.setPointSize(float(node.firstChild.data))
                    elif node.nodeName == 'Shading':
                        r = node.firstChild.data == 'True'
                        if r: self.shadingOn()
                        else: self.shadingOff()
            else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def load(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
        if exists(filename):
            self._actor = readMeshFromXMLVTK(filename)
            self._mapper = self._actor.GetMapper()
            self._polydata = self._mapper.GetInput()
            self._updateNormals()
            self.setNameFromFilename(filename)
            # Read XML
            doc = minidom.parse(filename)
            self.ParseXML(doc)
            self._filename = filename
        else: raise TypeError('No such file {}'.format(filename))

    def saveToOBJ(self, filename: str) -> None:
        v = vtkVersion.GetVTKVersion().GetVTKMajorVersion()
        if v >= 9:
            if self._polydata is not None:
                writeMeshToOBJ(self._polydata, filename)
                self.setNameFromFilename(filename)
        else: raise TypeError('VTK version {} (< 9) does not support saving of Obj format.'.format(v))

    def saveToSTL(self, filename: str) -> None:
        if self._polydata is not None:
            writeMeshToSTL(self._polydata, filename)
            self.setNameFromFilename(filename)

    def saveToVTK(self, filename: str) -> None:
        if self._polydata is not None:
            writeMeshToVTK(self._polydata, filename)
            self.setNameFromFilename(filename)

    def saveToXMLVTK(self, filename: str) -> None:
        if self._polydata is not None:
            writeMeshToXMLVTK(self._polydata, filename)
            self.setNameFromFilename(filename)

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                item = doc.createElement('XMESH')
                currentnode.appendChild(item)
                # ReferenceID
                node = doc.createElement('ReferenceID')
                item.appendChild(node)
                txt = doc.createTextNode(self.getReferenceID())
                node.appendChild(txt)
                # Name
                node = doc.createElement('Name')
                item.appendChild(node)
                txt = doc.createTextNode(self.getName())
                node.appendChild(txt)
                # Color
                buff = ' '.join([str(c) for c in self.getColor()])
                node = doc.createElement('Color')
                item.appendChild(node)
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # Opacity
                node = doc.createElement('Opacity')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getOpacity()))
                node.appendChild(txt)
                # Ambient
                node = doc.createElement('Ambient')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getAmbient()))
                node.appendChild(txt)
                # Diffuse
                node = doc.createElement('Diffuse')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getDiffuse()))
                node.appendChild(txt)
                # Specular
                node = doc.createElement('Specular')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getSpecular()))
                node.appendChild(txt)
                # SpecularPower
                node = doc.createElement('SpecularPower')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getSpecularPower()))
                node.appendChild(txt)
                # Metallic
                node = doc.createElement('Metallic')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getMetallic()))
                node.appendChild(txt)
                # Roughness
                node = doc.createElement('Roughness')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getRoughness()))
                node.appendChild(txt)
                # RenderingAlgorithm
                node = doc.createElement('RenderingAlgorithm')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getRenderingAlgorithmAsString()))
                node.appendChild(txt)
                # RenderPointsAsSpheres
                node = doc.createElement('RenderPointsAsSpheres')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getRenderPointsAsSpheres()))
                node.appendChild(txt)
                # RenderLinesAsTubes
                node = doc.createElement('RenderLinesAsTubes')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getRenderLinesAsTubes()))
                node.appendChild(txt)
                # VertexVisibility
                node = doc.createElement('VertexVisibility')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getVertexVisibility()))
                node.appendChild(txt)
                # VertexColor
                buff = ' '.join([str(c) for c in self.getVertexColor()])
                node = doc.createElement('VertexColor')
                item.appendChild(node)
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # EdgeVisibility
                node = doc.createElement('EdgeVisibility')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getEdgeVisibility()))
                node.appendChild(txt)
                # EdgeColor
                buff = ' '.join([str(c) for c in self.getEdgeColor()])
                node = doc.createElement('EdgeColor')
                item.appendChild(node)
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # LineWidth
                node = doc.createElement('LineWidth')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getLineWidth()))
                node.appendChild(txt)
                # PointSize
                node = doc.createElement('PointSize')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getPointSize()))
                node.appendChild(txt)
                # Shading
                node = doc.createElement('Shading')
                item.appendChild(node)
                txt = doc.createTextNode(str(self.getShading()))
                node.appendChild(txt)

    def save(self) -> None:
        if self.hasFilename(): self.saveAs(self._filename)
        else: raise AttributeError('Filename attribute is empty.')

    def saveAs(self, filename: str) -> None:
        if not self.isEmpty():
            path, ext = splitext(filename)
            filename = path + '.vtp'
            # Save xmlvtk part
            writeMeshToXMLVTK(self._polydata, filename)
            # Read xmlvtk
            doc = minidom.parse(filename)
            root = doc.documentElement
            # Add PySisyphe mesh attributes part
            self.createXML(doc, root)
            buff = doc.toprettyxml()
            # Save xmesh file
            remove(filename)
            filename = path + self._FILEEXT
            with open(filename, 'w') as f:
                f.write(buff)
            self._filename = filename


class SisypheMeshCollection(object):
    """
        SisypheMeshCollection

        Inheritance

            object -> SisypheMeshCollection

        Private attributes

            _meshes     list of SisypheMesh
            _index      index for Iterator

        Public methods

            __getitem__(str | int)
            __setitem__(int, SisypheMesh)
            __delitem__(SisypheMesh | str | int)
            __len__()
            __contains__(str | SisypheMesh)
            __iter__()
            __next__()
            __str__()
            __repr__()
            bool = isEmpty()
            int = count()
            remove(SisypheMesh | str | int)
            SisypheTransform = pop(SisypheMesh | str | int)
            list = keys()
            int = index(SisypheMesh | str)
            reverse()
            append(SisypheMesh)
            insert(SisypheMesh | str | int, SisypheMesh)
            clear()
            sort()
            SisypheMeshCollection = copy()
            list = copyToList()
            list = getList()
            setOpacity(float)
            setOverlayEdgeVisibility(bool)
            setVisibilityOn()
            setVisibilityOff()
            setAmbiant(float)
            setDiffuse(float)
            setSpecular(float)
            setSpecularPower(float)
            setMetallic(float)
            setRoughness(float)
            setFlatRendering()
            setGouraudRendering()
            setPhongRendering()
            setPBRRendering()
            setRenderPointsAsSpheresOn()
            setRenderPointsAsSpheresOff()
            setRenderLinesAsTubesOn()
            setRenderLinesAsTubesOff()
            setLineWidth(float)
            setPointSize(float)
            load(list of str)
            loadFromOBJ(list of str)
            loadFromSTL(list of str)
            loadFromVTK(list of str)
            loadFromXMLVTK(list of str)

        Creation: 22/03/2023
        Revisions:

            16/03/2023  change items type in _meshes list, tuple(Str Name, SisypheMesh) replaced by SisypheMesh
            16/03/2023  add pop method, removes SisypheMesh from list and returns it
            16/03/2023  add __getattr__ method, gives access to setter and getter methods of SisypheMesh
            15/04/2023  add item ID control
            01/09/2023  type hinting
    """
    __slots__ = ['_meshes', '_referenceID', '_index']

    # Private method

    def _verifyID(self, mesh: SisypheMesh) -> None:
        if isinstance(mesh, SisypheMesh):
            if self.isEmpty(): self.setReferenceID(mesh.getReferenceID())
            if self.hasReferenceID():
                if mesh.getReferenceID() != self._referenceID:
                    raise ValueError('Mesh reference ID ({}) is not '
                                     'compatible with collection reference ID ({}).'.format(mesh.getReferenceID(),
                                                                                            self._referenceID))
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    # Special methods

    def __init__(self) -> None:
        self._meshes = list()
        self._index = 0
        self._referenceID = ''

    def __str__(self) -> str:
        index = 0
        buff = 'SisypheMesh count #{}\n'.format(len(self._meshes))
        for mesh in self._meshes:
            index += 1
            buff += 'SisypheMesh #{}\n'.format(index)
            buff += '{}\n'.format(str(mesh))
        return buff

    def __repr__(self) -> str:
        return 'SisypheMeshCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, key: int | str) -> SisypheMesh:
        # key is Name str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._meshes):
                return self._meshes[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheMesh) -> None:
        if isinstance(value, SisypheMesh):
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._meshes):
                    self._verifyID(value)
                    if value.getName() in self: key = self.index(value)
                    self._meshes[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(value)))

    def __delitem__(self, key: int | str | SisypheMesh) -> None:
        # key is Name str or SisypheMesh
        if isinstance(key, (str, SisypheMesh)):
            key = self.index(key)
        # int index
        if isinstance(key, int):
            if 0 <= key < len(self._meshes):
                del self._meshes[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __len__(self) -> int:
        return len(self._meshes)

    def __contains__(self, value: str | SisypheMesh) -> bool:
        keys = [k.getName() for k in self._meshes]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is SisypheMesh
        elif isinstance(value, SisypheMesh):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or SisypheMesh.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> SisypheMesh:
        if self._index < len(self._meshes):
            n = self._index
            self._index += 1
            return self._meshes[n]
        else:
            raise StopIteration

    def __getattr__(self, name: str):
        """
            When attribute does not exist in the class,
            try calling the setter or getter method of sisypheMesh instances in collection.
            Getter methods return a list of the same size as the collection.
        """
        prefix = name[:3]
        if prefix in ('set', 'get'):
            def func(*args):
                # SisypheMesh get methods or set methods without argument
                if len(args) == 0:
                    if prefix in ('get', 'set'):
                        if name in SisypheMesh.__dict__:
                            if prefix == 'get': return [mesh.__getattribute__(name)() for mesh in self]
                            else:
                                for mesh in self: mesh.__getattribute__(name)()
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                # SisypheMesh set methods with argument
                elif prefix == 'set':
                    p = args[0]
                    # SisypheMesh set method argument is list
                    if isinstance(p, (list, tuple)):
                        n = len(p)
                        if n == self.count():
                            if name in SisypheMesh.__dict__:
                                for i in range(n): self[i].__getattribute__(name)(p[i])
                            else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                        else: raise ValueError('Number of items in list ({}) '
                                               'does not match with {} ({}).'.format(p, self.__class__, self.count()))
                    # SisypheMesh set method argument is a single value (int, float, str, bool)
                    else:
                        if name in SisypheMesh.__dict__:
                            for mesh in self: mesh.__getattribute__(name)(p)
                        else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
                else: raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))
            return func
        raise AttributeError('{} object has no attribute {}.'.format(self.__class__, name))

    # Public methods

    def isEmpty(self) -> bool:
        return len(self._meshes) == 0

    def setReferenceID(self, ID: str | SisypheMesh) -> None:
        if isinstance(ID, SisypheMesh):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, str):
            self._referenceID = ID
            if not self.isEmpty():
                for mesh in self:
                    mesh.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not SisypheMesh or str'.format(type(ID)))

    def getReferenceID(self) -> str:
        return self._referenceID

    def hasReferenceID(self) -> bool:
        return self._referenceID != ''

    def count(self) -> int:
        return len(self._meshes)

    def keys(self) -> list[str]:
        return [k.getName() for k in self._meshes]

    def remove(self, value: int | str | SisypheMesh) -> None:
        # value is SisypheMesh
        if isinstance(value, SisypheMesh):
            self._meshes.remove(value)
        # value is SisypheMesh, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or SisypheMesh.'.format(type(value)))

    def pop(self, key: int | str | SisypheMesh | None = None) -> SisypheMesh:
        if key is None: return self._meshes.pop()
        # key is Name str or SisypheMesh
        if isinstance(key, (str, SisypheMesh)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._meshes.pop(key)
        else: raise TypeError('parameter type {} is not int, str or SisypheMesh.'.format(type(key)))

    def index(self, value: str | SisypheMesh) -> int:
        keys = [k.getName() for k in self._meshes]
        # value is SisypheMesh
        if isinstance(value, SisypheMesh):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheMesh.'.format(type(value)))

    def reverse(self) -> None:
        self._meshes.reverse()

    def append(self, value: SisypheMesh) -> None:
        if isinstance(value, SisypheMesh):
            self._verifyID(value)
            if value.getName() not in self: self._meshes.append(value)
            else: self._meshes[self.index(value)] = value
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(value)))

    def insert(self, key: int | str | SisypheMesh, value: SisypheMesh) -> None:
        if isinstance(value, SisypheMesh):
            # value is Name str or SisypheMesh
            if isinstance(key, (str, SisypheMesh)):
                key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._meshes):
                    self._verifyID(value)
                    if value.getName() not in self: self._meshes.insert(key, value)
                    else: self._meshes[self.index(value)] = value
                else: IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(value)))

    def clear(self) -> None:
        self._meshes.clear()

    def sort(self, reverse: bool = False) -> None:
        def _getName(item):
            return item.getName()

        self._meshes.sort(reverse=reverse, key=_getName)

    def copy(self) -> SisypheMeshCollection:
        meshes = SisypheMeshCollection()
        for mesh in self._meshes:
            meshes.append(mesh)
        return meshes

    def copyToList(self) -> list[SisypheMesh]:
        meshes = self._meshes.copy()
        return meshes

    def getList(self) -> list[SisypheMesh]:
        return self._meshes

    # Mesh Public methods

    def setOpacity(self, alpha: float) -> None:
        if isinstance(alpha, float):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setOpacity(alpha)
        else: raise TypeError('parameter type {} is not float.'.format(type(alpha)))

    def setVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setOverlayEdgeVisibility(v)
        else: raise TypeError('parameter type is not bool.'.format(type(v)))

    def setVisibilityOn(self) -> None:
        self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        self.setVisibility(False)

    def setAmbient(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setAmbient(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setDiffuse(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setDiffuse(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecular(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setSpecular(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecularPower(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 50.0:
                    for mesh in self._meshes:
                        mesh.setSpecularPower(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 50.0.'.format(v))
        else: raise TypeError('parameter type is not float.'.format(type(v)))

    def setMetallic(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setMetallic(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setRoughness(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setRoughness(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type is not float.'.format(type(v)))

    def setFlatRendering(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setFlatRendering(True)

    def setGouraudRendering(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setGouraudRendering(True)

    def setPhongRendering(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setPhongRendering(True)

    def setPBRRendering(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setPBRRendering(True)

    def setRenderPointsAsSpheresOn(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderPointsAsSpheresOn()

    def setRenderPointsAsSpheresOff(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderPointsAsSpheresOff()

    def setRenderLinesAsTubesOn(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderLinesAsTubesOn()

    def setRenderLinesAsTubesOff(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderLinesAsTubesOff()

    def setEdgeVisibilityOn(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setEdgeVisibilityOn()

    def setEdgeVisibilityOff(self) -> None:
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setEdgeVisibilityOff()

    def setLineWidth(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setPointSize(self, v: float) -> None:
        if isinstance(v, float):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setPointSize(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def resample(self,
                 trf: SisypheTransform,
                 save: bool = True,
                 dialog: bool = False,
                 prefix: str | None = None,
                 suffix: str | None = None,
                 wait: DialogWait | None = None):
        if not self.isEmpty():
            if isinstance(trf, SisypheTransform):
                f = SisypheApplyTransform()
                f.setTransform(trf)
                c = SisypheMeshCollection()
                for mesh in self:
                    f.setMovingMesh(mesh)
                    c.append(f.resampleMesh(save, dialog, prefix, suffix, wait))
                return c
            else: raise TypeError('parameter type {} is not SisypheTransform.'.format(type(trf)))
        else: raise ValueError('Mesh collection is empty.')

    # IO Public methods

    def load(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        mesh = SisypheMesh()
                        mesh.load(filename)
                        self.append(mesh)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromOBJ(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        mesh = SisypheMesh()
                        mesh.loadFromOBJ(filename)
                        self.append(mesh)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromSTL(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        mesh = SisypheMesh()
                        mesh.loadFromSTL(filename)
                        self.append(mesh)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromVTK(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        mesh = SisypheMesh()
                        mesh.loadFromVTK(filename)
                        self.append(mesh)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))

    def loadFromXMLVTK(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        mesh = SisypheMesh()
                        mesh.loadFromXMLVTK(filename)
                        self.append(mesh)
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not filepath str'.format(type(filename)))
        else: raise TypeError('parameter type {} is not list of filepath str.'.format(type(filenames)))
