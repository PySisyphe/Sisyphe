"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, <https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os import remove
from os import getcwd
from os.path import join
from os.path import splitext
from os.path import exists
from os.path import dirname
from os.path import basename

from xml.dom import minidom

import cython

from re import sub

import numpy as np
from numpy import zeros
from numpy import array
from numpy import ndarray
from numpy import median

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import Image as sitkImage
from SimpleITK import sitkFloat32
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
from vtk import VTK_TRIANGLE
from vtk import vtkVersion

from Sisyphe.core.sisypheMeshIO import readMeshFromOBJ
from Sisyphe.core.sisypheMeshIO import writeMeshToOBJ
from Sisyphe.core.sisypheMeshIO import readMeshFromSTL
from Sisyphe.core.sisypheMeshIO import writeMeshToSTL
from Sisyphe.core.sisypheMeshIO import readMeshFromVTK
from Sisyphe.core.sisypheMeshIO import writeMeshToVTK
from Sisyphe.core.sisypheMeshIO import readMeshFromXMLVTK
from Sisyphe.core.sisypheMeshIO import writeMeshToXMLVTK
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheTransform import SisypheTransform
    from Sisyphe.core.sisypheTransform import SisypheApplyTransform


__all__ = ['SisypheMesh',
           'SisypheMeshCollection']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheMesh
             -> SisypheMeshCollection
"""

tupleFloat3 = tuple[float, float, float]
vectorFloat3Type = list[float] | tupleFloat3


class SisypheMesh(object):
    """
    Description
    ~~~~~~~~~~~

    PySisyphe mesh class.

    This class provides access to internal vtk classes: vtkPolyData, vtkPolyDataMapper and vtkActor.

    Getter and Setter access to mesh points with slicing ability.
    Getter: v = instance_name[idx]
    Setter: instance_name[idx] = [x, y, z]
    idx is int index, or list/tuple of indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)

    Scope of available methods:

        - creating mesh from simple shapes (line, tube, sphere, cube),
        - creating brain/head outer surface mesh,
        - creating mesh from discrete region-of-interest (ROI),
        - creating isosurface mesh from volume,
        - mesh properties management,
        - filtering (decimate, clean, smoothing, fill holes),
        - boolean operators (union, intersection, difference),
        - expanding/shrinking,
        - geometric transformation,
        - binary image discretization,
        - feature extraction (surface, volume, center-of-mass, bounds, principal axes, distances...),
        - IO methods for common mesh file formats (OBJ, STL, VTK, VTP).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheMesh

    Creation: 22/03/2023
    Last revision: 22/03/2025
    """
    __slots__ = ['_name', '_filename', '_referenceID', '_polydata', '_mapper', '_actor']
    _counter: int = 0

    _FILEEXT = '.xmesh'

    # Class methods

    # < Revision 21/02/2025
    @classmethod
    def getInstancesCount(cls) -> int:
        """
        Get the SisypheMesh instance count.

        Returns
        -------
        int
            instance count
        """
        return cls._counter
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    @classmethod
    def addInstance(cls) -> None:
        """
        Increment the SisypheMesh instance count. This class method is called by the constructor.
        """
        cls._counter += 1
    # Revision 21/02/2025 >

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheMesh file extension.

        Returns
        -------
        str
            '.xmesh'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheMesh filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Mesh (.xmesh)'
        """
        return 'PySisyphe Mesh (*{})'.format(cls._FILEEXT)

    @classmethod
    def openMesh(cls, filename: str) -> SisypheMesh:
        """
        Create a SisypheMesh instance from various mesh file formats.

        Parameters
        ----------
        filename : str
            mesh file name (supported formats 'obj', 'stl', 'vtk', 'vtp')

        Returns
        -------
        SisypheMesh
            loaded mesh
        """
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
        else: raise FileNotFoundError('no such file {}'.format(filename))

    # Special methods

    """
    Private attributes

    _name           str, mesh name
    _filename       str, file name
    _referenceID    str, reference SisypheVolume ID
    _polydata       vtkPolyData
    _mapper         vtkPolyDataMapper
    _actor          vtkActor
    """

    def __init__(self) -> None:
        """
        SisypheMesh instance constructor.
        """
        # < Revision 21/02/2025
        self.addInstance()
        # Revision 21/02/2025 >
        self._name: str = 'Mesh'
        self._filename: str = ''
        self._referenceID = ''  # reference SisypheVolume ID
        self._polydata = None
        self._mapper = vtkPolyDataMapper()
        self._actor = vtkActor()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheMesh instance to str
        """
        if self._polydata is not None:
            buff = 'Name: {}\n'.format(self.getName())
            buff += 'ID: {}\n'.format(self.getReferenceID())
            buff += 'Origin: {}\n'.format(self._numericToStr(self.getOrigin(), d=1))
            buff += 'Position: {}\n'.format(self._numericToStr(self.getPosition(), d=1))
            buff += 'Orientation: {}\n'.format(self._numericToStr(self.getRotation(), d=1))
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
            if mem <= 1024: buff += 'Memory Size: {:.1f} KB\n'.format(mem)
            else: buff += 'Memory Size: {:.1f} MB\n'.format(mem/1024)
        else: buff = 'Empty mesh instance'
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheMesh instance representation
        """
        return 'SisypheMesh instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # set/get mesh point methods

    def __getitem__(self, idx: int | list[int] | tuple[int, ...] | slice) -> ndarray:
        """
        Special overloaded container getter method. Get mesh point with slicing ability.
        syntax: v = instance_name[idx]

        Parameters
        ----------
        idx : int | list[int] | tuple[int, ...] | slice
            int index, or list/tuple of indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)

        Returns
        -------
        numpy.ndarray
            mesh point(s)
        """
        if isinstance(idx, int):
            return array(self._polydata.GetPoint(idx))
        elif isinstance(idx, (tuple, list)):
            r = list()
            for i in idx:
                r.append(self._polydata.GetPoint(i))
            return array(r)
        elif isinstance(idx, slice):
            r = list()
            start, stop, step = idx.start, idx.stop, idx.step
            if start is None: start = 0
            if step is None: step = 1
            for i in range(start, stop, step):
                r.append(self._polydata.GetPoint(i))
            return array(r)
        else: raise TypeError('parameter type is not int, list[int], tuple[int, ...] or slice')

    def __setitem__(self, idx: int | list[int] | tuple[int, ...] | slice, value: ndarray) -> None:
        """
        Special overloaded container setter method. Set mesh point with slicing ability.
        syntax: instance_name[idx] = value

        Parameters
        ----------
        idx : int, list[int], tuple[int, ...] | slice
            x, y, z int indices or pythonic slicing (i.e. python slice object, used the syntax first:last:step)
        value : list[float, float, float] | ndarray
            mesh point(s)
        """
        if isinstance(idx, int):
            if isinstance(value, list): self._polydata.GetPoints().SetPoint(idx, value[:3])
            elif isinstance(value, ndarray): self._polydata.GetPoints().SetPoint(idx, value[:3])
        elif isinstance(idx, (tuple, list)):
            for ii, i in enumerate(idx):
                self._polydata.GetPoints().SetPoint(i, value[ii, :])
        elif isinstance(idx, slice):
            start, stop, step = idx.start, idx.stop, idx.step
            if start is None: start = 0
            if step is None: step = 1
            for ii, i in enumerate(range(start, stop, step)):
                self._polydata.GetPoints().SetPoint(i, value[ii, :])

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
        # noinspection PyTypeChecker
        return r

    def _updatePolydata(self) -> None:
        if self._polydata is not None:
            self._mapper.SetInputData(self._polydata)
            self._mapper.UpdateInformation()
            # noinspection PyArgumentList
            self._mapper.Update()
            self._actor.SetMapper(self._mapper)

    def _updateNormals(self) -> None:
        if self._actor is not None:
            flt = vtkPolyDataNormals()
            flt.SetInputData(self._polydata)
            flt.SetFeatureAngle(60.0)
            flt.ComputePointNormalsOn()
            flt.ComputeCellNormalsOn()
            flt.SplittingOn()
            flt.ConsistencyOn()
            flt.AutoOrientNormalsOn()
            # noinspection PyArgumentList
            flt.Update()
            self._polydata = flt.GetOutput()
            self._updatePolydata()

    # Public methods

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current SisypheMesh instance. A mesh is defined in the space of a reference
        SisypheVolume whose ID is the reference ID.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def setReferenceID(self, ID: str | SisypheVolume) -> None:
        """
        Set the reference ID attribute of the current SisypheMesh instance. A mesh is defined in the space of a
        reference SisypheVolume whose ID is the reference ID.

        Parameters
        ----------
        ID : str | SisypheVolume
            if SisypheVolume, get ID attribute
        """
        if isinstance(ID, str): self._referenceID = ID
        elif isinstance(ID, SisypheVolume): self._referenceID = ID.getID()
        else: self._referenceID = None

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID of the current SisypheMesh instance is defined (not '').

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID != ''

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current SisypheMesh instance.

        Parameters
        ----------
        name : str
            mesh name
        """
        if isinstance(name, str):
            if name != '':
                # < Revision 21/09/2024
                # re = QRegExp(self._REGEXP)
                # if re.exactMatch(name):
                #     self._name = name
                r = '[^A-Za-z0-9#\-\_\s,]'
                name = sub(r, '', name)
                if name != '':
                    self._name = name
                    # < Revision 23/03/2025
                    if self._filename is not None:
                        self._filename = join(dirname(self._filename), self._name + self._FILEEXT)
                    # Revision 23/03/2025 >
                # Revision 21/09/2024 >
                else: raise ValueError('Invalid char in name parameter.')
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheMesh instance.

        Returns
        -------
        str
            mesh name
        """
        return self._name

    def setDefaultName(self) -> None:
        """
        Set default name attribute of the current SisypheMesh instance. default name = 'MESH' + instance count.
        """
        idx = '00{}'.format(self.getInstancesCount())[-3:]
        self.setName('MESH{}'.format(idx))

    def setNameFromFilename(self, filename: str) -> None:
        """
        Set the name attribute of the current SisypheMesh instance from a file name.

        Parameters
        ----------
        filename : str
            file name
        """
        if isinstance(filename, str): self._name = splitext(basename(filename))[0]
        else: raise TypeError('parameter type {} is not str.'.format(filename))

    def setFilename(self, filename: str) -> None:
        """
        Set the file name attribute of the current SisypheMesh instance. This file name is used by save() method.

        Parameters
        ----------
        filename : str
            file name
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        self._filename = filename
        if self._name == '': self.setNameFromFilename(filename)

    def getFilename(self) -> str:
        """
        Get the file name attribute of the current SisypheMesh instance. This file name is used by save() method.

        Returns
        -------
        str
            file name
        """
        return self._filename

    # < Revision 21/02/2025
    # add setFilenamePrefix method
    def setFilenamePrefix(self, prefix: str, sep: str = '_') -> None:
        """
        Set a prefix to the file name attribute of the current SisypheMesh instance.

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
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add getFilenamePrefix method
    def getFilenamePrefix(self, sep: str = '_') -> str:
        """
        Get prefix (if any) from the file name attribute of the current SisypheMesh instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            prefix
        """
        r = self.getFilename().split(sep)
        if len(r) > 0: return r[0]
        else: return ''
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add setFilenameSuffix method
    def setFilenameSuffix(self, suffix: str, sep: str = '_') -> None:
        """
        Set a suffix to the file name attribute of the current SisypheMesh instance.

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
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add getFilenameSuffix method
    def getFilenameSuffix(self, sep: str = '_') -> str:
        """
        Get suffix (if any) from the file name attribute of the current SisypheMesh instance.

        Parameters
        ----------
        sep : str
            char between prefix and base name (default '_')

        Returns
        -------
        str
            suffix
        """
        r = self.getFilename().split(sep)
        if len(r) > 0: return r[-1]
        else: return ''
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    def setDefaultFilename(self) -> None:
        """
        Set default file name attribute of the current SisypheMesh instance. This file name is used by save() method.
        Default file name = name attribute + mesh file extension ('.xmesh')
         """
        if self._name == '': self.setDefaultName()
        self._filename = join(getcwd(), '{}{}'.format(self._name, self._FILEEXT))
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    def setPathFromVolume(self, volume: SisypheVolume) -> None:
        """
        Set path part of the file name attribute of the current SisypheMesh instance from the path part (dirname) of
        the file name attribute of a SisypheVolume parameter.

        Parameters
        ----------
        volume : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to replace dirname
        """
        if isinstance(volume, SisypheVolume):
            path = dirname(volume.getFilename())
            if path != '': self._filename = join(path, basename(self._filename))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))
    # Revision 21/02/2025 >

    def getDirname(self) -> str:
        """
        Get the path of the file name attribute of the current SisypheMesh instance.

        Returns
        -------
        str
            file name
        """
        return dirname(self._filename)

    def setDirname(self, filename: str) -> None:
        """
        Set the path of the file name attribute of the current SisypheMesh instance.

        Returns
        -------
        str
            file name
        """
        self._filename = join(dirname(filename), basename(self._filename))

    def hasFilename(self) -> bool:
        """
        Check that the file name attribute of the SisypheMesh instance is set (not None).

        Returns
        -------
        bool
            True if file name si defined
        """
        return self._filename != ''

    def isEmpty(self) -> bool:
        """
        Check whether the current SisypheMesh instance is empty.

        Returns
        -------
        bool
            True if empty
        """
        return self._polydata is None

    def setActor(self, actor: vtkActor) -> None:
        """
        Set the vtkActor attribute of the current SisypheMesh instance.

        Parameters
        ----------
        actor : vtkActor
        """
        if isinstance(actor, vtkActor):
            self._actor = actor
            self._mapper = actor.GetMapper()
            self._polydata = self._mapper.GetInput()
        else: raise TypeError('parameter type {} is not vtkActor.'.format(type(actor)))

    def setPolyData(self, data: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> None:
        """
        Set the vtkPolydata attribute of the current SisypheMesh instance from SisypheMesh, vtkActor, vtkPolyDataMapper
        or vtkPolyData instance (shallow copy).

        Parameters
        ----------
        data : SisypheMesh | vtkActor | vtkPolyDataMapper | vtkPolyData
            vtkPolydata to copy
        """
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
        """
        Set the vtkPolydata attribute of the current SisypheMesh instance from SisypheMesh, vtkActor, vtkPolyDataMapper
        or vtkPolyData instance (deep copy).

        Parameters
        ----------
        data : SisypheMesh | vtkActor | vtkPolyDataMapper | vtkPolyData
            vtkPolyData to copy
        """
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
        """
        Clear the current SisypheMesh instance (empty).
        """
        del self._polydata
        self._polydata = None

    def getPolyData(self) -> vtkPolyData:
        """
        Get the vtkPolyData attribute of the current SisypheMesh instance.

        Returns
        -------
        vtkPolydata
            vtkPolydata shallow copy
        """
        return self._polydata

    def getPolyDataMapper(self) -> vtkPolyDataMapper:
        """
        Get the vtkPolyDataMapper attribute of the current SisypheMesh instance.

        Returns
        -------
        vtkPolydataMapper
            vtkPolydataMapper shallow copy
        """
        return self._mapper

    def getActor(self) -> vtkActor:
        """
        Get the vtkActor attribute of the current SisypheMesh instance.

        Returns
        -------
        vtkActor
            vtkActor shallow copy
        """
        return self._actor

    def getMemorySize(self) -> int:
        """
        Get the memory size of the current SisypheMesh instance.

        Returns
        -------
        int
            memory size in KBytes
        """
        if self._polydata is not None:
            return self._polydata.GetActualMemorySize()
        else: raise AttributeError('Polydata attribute is None.')

    def getNumberOfPoints(self) -> int:
        """
        Get the number of points of the vtkPolyData attribute of the current SisypheMesh instance.

        Returns
        -------
        int
            number of points
        """
        return self._polydata.GetNumberOfPoints()

    def getPoints(self) -> vtkPoints:
        """
        Get the vtKPoints (vtk container of points) of the vtkPolyData attribute of the current SisypheMesh instance.

        Returns
        -------
        vtkPoints
            vtkPoints shallow copy
        """
        return self._polydata.GetPoints()

    def setPoints(self, p: vtkPoints) -> None:
        """
        Set the vtKPoints (vtk container of points) of the vtkPolyData attribute of the current SisypheMesh instance.

        Parameters
        ----------
        p : vtkPoints
            vtkPoints to copy
        """
        if isinstance(p, vtkPoints):
            if p.GetNumberOfPoints() == self._polydata.GetNumberOfPoints():
                self._polydata.SetPoints(p)
                self._updatePolydata()
            else: raise ValueError('incorrect number of points in vtkPoints parameter.')
        else: raise TypeError('parameter type {} is not vtkPoints.'.format(type(p)))

    def getPoint(self, idx: int = 0) -> tupleFloat3:
        """
        Get a point of the vtkPolyData.

        Parameters
        ----------
        idx : int
            point index in the vtkPolyData

        Returns
        -------
        tuple[float, float, float]
            point coordinates
        """
        return self._polydata.GetPoint(idx)

    def setPoint(self, idx: int, p: vectorFloat3Type) -> None:
        """
        Get a point of the vtkPolyData.

        Parameters
        ----------
        idx : int
            point index in the vtkPolyData
        p : tuple[float, float, float] | list[float, float, float]
            point coordinates
        """
        self._polydata.GetPoints().SetPoint(idx, p)

    def setPosition(self, x: float, y: float, z: float) -> None:
        """
        Set the mesh position (mm), in world coordinates, of the current SisypheMesh instance.

        Parameters
        ----------
        x : float
            x-axis coordinate
        y : float
            y-axis coordinate
        z : float
            z-axis coordinate
        """
        self._actor.SetPosition(x, y, z)

    def getPosition(self) -> tupleFloat3:
        """
        Get the mesh position (mm), in world coordinates, of the current SisypheMesh instance.

        Returns
        -------
        Tuple[float, float, float]
            x, y, z world coordinates
        """
        return self._actor.GetPosition()

    def setRotation(self, x: float, y: float, z: float) -> None:
        """
        Set the mesh rotation (°), in world coordinates, of the current SisypheMesh instance.

        Parameters
        ----------
        x : float
            x-axis coordinate
        y : float
            y-axis coordinate
        z : float
            z-axis coordinate
        """
        self._actor.SetOrientation(x, y, z)

    def getRotation(self) -> tupleFloat3:
        """
        Get the mesh rotation (°), in world coordinates, of the current SisypheMesh instance.

        Returns
        -------
        Tuple[float, float, float]
            x, y, z world coordinates
        """
        return self._actor.GetOrientation()

    def isDefaultPosition(self) -> bool:
        """
        Check whether the mesh position of the current SisypheMesh instance is (0.0, 0.0 ,0.0).

        Returns
        -------
        bool
            True if mesh position is (0.0, 0.0 ,0.0)
        """
        return self._actor.GetPosition() == (0.0, 0.0, 0.0)

    def isDefaultRotation(self) -> bool:
        """
        Check whether the mesh rotation of the current SisypheMesh instance is (0.0, 0.0 ,0.0).

        Returns
        -------
        bool
            True if mesh rotation is (0.0, 0.0 ,0.0)
        """
        return self._actor.GetOrientation() == (0.0, 0.0, 0.0)

    def getOrigin(self) -> vectorFloat3Type:
        """
        Get the vtkPolydata attribute origin, in world coordinates, of the current SisypheMesh instance. All rotations
        take place around this point.

        Returns
        -------
        tuple[float, float, float]
            origin coordinates
        """
        return self._actor.GetOrigin()

    def setOrigin(self, x: float, y: float, z: float) -> None:
        """
        Set the vtkPolydata attribute origin, in world coordinates, of the current SisypheMesh instance. All rotations
        take place around this point.

        Parameters
        ----------
        x : float
            x-axis coordinate
        y : float
            y-axis coordinate
        z : float
            z-axis coordinate
        """
        self._actor.SetOrigin(x, y, z)

    def isDefaultOrigin(self) -> bool:
        """
        Check whether the mesh origin of the current SisypheMesh instance is (0.0, 0.0 ,0.0).

        Returns
        -------
        bool
            True if origin is (0.0, 0.0 ,0.0).
        """
        return self._actor.GetOrigin() == (0.0, 0.0, 0.0)

    def setOriginToCenter(self) -> None:
        """
        Set the vtkPolydata attribute origin to the bounding box center, in world coordinates, of the current
        SisypheMesh instance. All rotations take place around this point.
        """
        c = self.getCenter()
        self.setOrigin(c[0], c[1], c[2])

    def setDefaultOrigin(self) -> None:
        """
        Set the vtkPolydata attribute origin to (0.0, 0.0, 0.0), in world coordinates, of the current SisypheMesh
        instance. All rotations take place around this point.
        """
        self.setOrigin(0.0, 0.0, 0.0)

    def getCenter(self) -> vectorFloat3Type:
        """
        Get the vtkPolydata attribute bounding box center, in world coordinates, of the current SisypheMesh instance.
        All rotations take place around this point.

        Returns
        -------
        tuple[float, float, float]
            center coordinates
        """
        return self._actor.GetCenter()

    def setOriginFromReferenceVolume(self, v: SisypheVolume) -> None:
        """
        Set the vtkPolydata attribute origin, in world coordinates, of the current SisypheMesh instance to the center
        of a SisypheVolume.

        Parameters
        ----------
        v : SisypheVolume
            origin is placed at the center of this volume
        """
        if isinstance(v, SisypheVolume):
            c = v.getCenter()
            self._actor.SetOrigin(c[0], c[1], c[2])
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def setScale(self, sx: float, sy: float, sz: float) -> None:
        """
        Set a scale factor (zoom) to the vtkPolyData attribute of the current SisypheMesh instance.

        Parameters
        ----------
        sx : float
            x-axis scale
        sy : float
            y-axis scale
        sz : float
            z-axis scale
        """
        self._actor.SetScale(sx, sy, sz)

    def getScale(self) -> vectorFloat3Type:
        """
        Get a scale factor (zoom) which is applied to the vtkPolyData attribute of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, float, float]
            scales in x, y, z axes
        """
        return self._actor.GetScale()

    def getBounds(self) -> tuple[float, ...]:
        """
        Get the vtkPolyData attribute bounds of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, ...]
            - x minimum, x maximum,
            - y minimum, y maximum,
            - z minimum, z maximum
        """
        return self._polydata.GetBounds()

    def setTransform(self, trf: SisypheTransform | vtkTransform) -> None:
        """
        Apply a rigid geometric transformation to the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        trf : SisypheTransform | vtkTransform
            rigid geometric transformation
        """
        from Sisyphe.core.sisypheTransform import SisypheTransform
        if isinstance(trf, SisypheTransform): trf = trf.getVTKTransform()
        if isinstance(trf, vtkTransform): self._actor.SetUserMatrix(trf)

    def getTransform(self) -> SisypheTransform:
        """
        Get the rigid geometric transformation applied to the mesh of the current SisypheMesh instance.

        Returns
        -------
        SisypheTransform
            rigid geometric transformation
        """
        from Sisyphe.core.sisypheTransform import SisypheTransform
        trf = SisypheTransform()
        trf.setVTKMatrix4x4(self._actor.GetUserMatrix())
        return trf

    def applyTransform(self, trf: SisypheTransform | vtkTransform):
        """
        Apply an affine geometric transformation to the mesh of the current SisypheMesh instance. The center of
        rotation is the origin. This method performs a resampling of the vtkPolyData points.

        Parameters
        ----------
        trf : SisypheTransform | vtkTransform
            affine geometric transformation
        """
        from Sisyphe.core.sisypheTransform import SisypheTransform
        if isinstance(trf, SisypheTransform):
            trf = trf.getVTKTransform()
        if isinstance(trf, vtkTransform):
            # < Revision 21/07/2024
            # change center of rotation, if origin is not (0.0, 0.0, 0.0)
            origin = self.getOrigin()
            if origin != (0.0, 0.0, 0.0):
                # 1) -origin translations, center of rotation = origin
                # 2) roto-translation (1 pre-multiply 2)
                # 3) +origin translations (2 pre-multiply 3)
                o3 = SisypheTransform()
                o3.setTranslations(origin)
                o1 = o3.getInverseTransform()
                o1.preMultiply(trf, homogeneous=True)
                o1.preMultiply(o3, homogeneous=True)
                trf = o1.getVTKTransform()
            # Revision 21/07/2024 >
            f = vtkTransformPolyDataFilter()
            f.SetTransform(trf)
            f.SetInputData(self._polydata)
            f.Update()
            self.setPolyData(f.GetOutput())
            self.setOriginToCenter()

    # Rendering property methods

    def getVtkProperty(self) -> vtkProperty:
        """
        Get the vtkActor attribute properties (surface rendering properties) of the current SisypheMesh instance.

        Returns
        -------
        vtkProperty
            vtkProperty shallow copy
        """
        return self._actor.GetProperty()

    def setVtkProperty(self, v: vtkProperty) -> None:
        """
        Set the vtkActor attribute properties (surface rendering properties)
        of the current SisypheMesh instance (shallow copy).

        Parameters
        ----------
        v : vtkProperty
            vtkProperty to copy
        """
        if isinstance(v, vtkProperty):
            self._actor.SetProperty(v)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(v)))

    def copyPropertiesFromVtkProperty(self, v: vtkProperty) -> None:
        """
        Set the vtkActor attribute properties (surface rendering properties) of the current SisypheMesh instance
        (deep copy).

        Parameters
        ----------
        v : vtkProperty
            vtkProperty to copy
        """
        if isinstance(v, vtkProperty):
            c = vtkProperty()
            c.DeepCopy(v)
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not vtkProperty.'.format(type(v)))

    def copyPropertiesFromVtkActor(self, v: vtkActor) -> None:
        """
        Set the vtkActor attribute properties (surface rendering properties) of the current SisypheMesh instance from a
        vtkActor parameter (deep copy).

        Parameters
        ----------
        v : vtkActor
            vtkActor to copy
        """
        if isinstance(v, vtkActor):
            c = vtkProperty()
            c.DeepCopy(v.GetProperty())
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not vtkActor.'.format(type(v)))

    def copyPropertiesFromMesh(self, mesh: SisypheMesh) -> None:
        """
        Set the vtkActor attribute properties (surface rendering properties) of the current SisypheMesh instance from a
        SisypheMesh parameter (deep copy).

        Parameters
        ----------
        mesh : SisypheMesh
            mesh to copy
        """
        if isinstance(mesh, SisypheMesh):
            c = vtkProperty()
            c.DeepCopy(mesh.getActor().GetProperty())
            self._actor.SetProperty(c)
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(mesh)))

    def copyColorFromROI(self, roi: SisypheROI) -> None:
        """
        Set the mesh color of the current SisypheMesh instance from a SisypheROI parameter.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            roi color to copy
        """
        if isinstance(roi, SisypheROI):
            c = roi.getColor()
            self.setColor(c[0], c[1], c[2])
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    def setOpacity(self, alpha: float) -> None:
        """
        Set the mesh opacity of the current SisypheMesh instance.

        Parameters
        ----------
        alpha : float
            opacity, between 0.0 and 1.0
        """
        if self._polydata is not None:
            if isinstance(alpha, float):
                if 0.0 <= alpha <= 1.0:
                    self._actor.GetProperty().SetOpacity(alpha)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(alpha))
            else: raise TypeError('parameter type {} is not float.'.format(type(alpha)))

    def getOpacity(self) -> float:
        """
        Get the mesh opacity of the current SisypheMesh instance.

        Returns
        -------
        float
            opacity, between 0.0 and 1.0
         """
        if self._polydata is not None:
            return self._actor.GetProperty().GetOpacity()
        else: raise AttributeError('Polydata attribute is None.')

    def setVisibility(self, v: bool) -> None:
        """
        Set the mesh visibility of the current SisypheMesh instance.

        Parameters
        ----------
        v : bool
            visible if True
        """
        if self._polydata is not None:
            if isinstance(v, bool) and self._actor is not None:
                self._actor.SetVisibility(v)
            else: raise TypeError('parameter functype is not bool or int.')

    def setVisibilityOn(self) -> None:
        """
        Show the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        """
        Hide the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self.setVisibility(False)

    def getVisibility(self) -> bool:
        """
        Get the mesh visibility of the current SisypheMesh instance.

        Returns
        -------
        bool
            True if visible
        """
        if self._polydata is not None:
            return self._actor.GetVisibility() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def setColor(self, r: float, g: float, b: float) -> None:
        """
        Set the mesh color of the current SisypheMesh instance. This color is not used if the scalar color visibility
        mode is on.

        Parameters
        ----------
        r : float
            mesh color, 0.0 <= red component <= 1.0
        g : float
            mesh color, 0.0 <= green component <= 1.0
        b : float
            mesh color, 0.0 <= blue component <= 1.0
        """
        if self._polydata is not None:
            self._mapper.ScalarVisibilityOff()
            self._actor.GetProperty().SetColor(r, g, b)

    def setQColor(self, c: QColor, opacity: bool = False) -> None:
        """
        Set the mesh color of the current SisypheMesh instance from a QColor. This color is not used if the scalar
        color visibility mode is on.

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            mesh color
        opacity : bool
            sets mesh opacity from QColor alpha component if True
        """
        self.setColor(c.redF(), c.greenF(), c.blueF())
        if opacity: self.setOpacity(c.alphaF())

    # noinspection PyTypeChecker
    def getColor(self) -> vectorFloat3Type:
        """
        Get the mesh color of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, float, float]
            mesh color, red, green, blue (0.0 <= value <= 1.0)
        """
        if self._polydata is not None: return self._actor.GetProperty().GetColor()
        else: raise ValueError('Polydata attribute is None.')

    def getQColor(self, opacity: bool = False) -> QColor:
        """
        Get the mesh color (as QColor) of the current SisypheMesh instance.

        Parameters
        ----------
        opacity : bool
            copies the mesh opacity to alpha QColor component if true

        Returns
        -------
        PyQt5.QtGui.QColor
            mesh color
        """
        r, g, b = self.getColor()
        c = QColor()
        if opacity: c.setRgbF(r, g, b, self.getOpacity())
        else: c.setRgbF(r, g, b, 1.0)
        return c

    def getScalarColorVisibility(self) -> bool:
        """
        Check whether the scalar color visibility mode of the current SisypheMesh instance is on. In this mode, the
        color of each point in the mesh is calculated from the scalar value, displayed with a look-up table colormap,
        at the point's coordinates in the reference SisypheVolume image array.

        Returns
        -------
        bool
            True if scalar color visibility mode is on
        """
        return self._mapper.GetScalarVisibility() > 0

    def setScalarColorVisibilityOn(self) -> None:
        """
        Set the scalar color visibility mode of the current SisypheMesh instance to on. In this mode, the color of each
        point in the mesh is calculated from the scalar value, displayed with a look-up table colormap, at the point's
        coordinates in the reference SisypheVolume image array.
        """
        self._mapper.ScalarVisibilityOn()

    def setScalarColorVisibilityOff(self) -> None:
        """
        Set the scalar color visibility mode of the current SisypheMesh instance to off. In this mode, the mesh is
        painted with even color fixed by the setColor (or setQColor) method.
        """
        self._mapper.ScalarVisibilityOff()

    def setScalarColorVisibility(self, v: bool) -> None:
        """
        Set the scalar color visibility mode of the current SisypheMesh instance. If scalar color visibility mode is
        on, the color of each mesh point  is calculated from the scalar value, displayed with a look-up table colormap,
        at the point's coordinates in the reference SisypheVolume image array. Otherwise, the mesh is painted with even
        color fixed by the setColor (or setQColor) method.

        Parameters
        ----------
        v : bool
            scalar visibility
        """
        if isinstance(v, bool): self._mapper.SetScalarVisibility(v)
        else: raise TypeError('parameter type {} is not bool'.format(type(v)))

    # noinspection PyArgumentList
    def setLUT(self, lut: SisypheVolume | SisypheLut | vtkLookupTable) -> None:
        """
        Set the mesh look-up table colormap of the current SisypheMesh instance. Set the scalar color visibility mode
        of the current SisypheMesh instance to on. In this mode, the color of each mesh point is calculated from the
        scalar value, displayed with a look-up table colormap, at the point's coordinates in the reference
        SisypheVolume image array.

        Parameters
        ----------
        lut : SisypheVolume | SisypheLut | vtkLookupTable
            lut to copy
        """
        if isinstance(lut, SisypheVolume): lut = lut.display.getVTKLUT()
        if isinstance(lut, SisypheLut): lut = lut.getvtkLookupTable()
        if isinstance(lut, vtkLookupTable):
            self._mapper.SetScalarModeToUsePointData()
            self._mapper.SetColorModeToMapScalars()
            self._mapper.SetLookupTable(lut)
            self._mapper.UseLookupTableScalarRangeOff()
            # self._mapper.UseLookupTableScalarRangeOn()
            # noinspection PyArgumentList
            self._mapper.SetScalarRange(lut.GetRange())
            self._mapper.ScalarVisibilityOn()
            self._mapper.UpdateInformation()
            self._mapper.Update()
        else: raise TypeError('parameter type {} is not vtkLookupTable, SisypheLut or SisypheVolume.'.format(type(lut)))

    def getLUT(self) -> vtkLookupTable:
        """
        Get the mesh look-up table colormap (as vtkLookupTable) of the current SisypheMesh instance.

        Returns
        -------
        vtkLookupTable
            lut copy
        """
        return self._mapper.GetLookupTable()

    def setLUTScalarRange(self, vmin: float, vmax: float) -> None:
        """
        Set the scalar range of the look-up table colormap of the current SisypheMesh instance.

        Parameters
        ----------
        vmin: float
            minimum scalar value
        vmax : float
            maximum scalar value
        """
        if self._mapper.GetScalarVisibility() > 0:
            self._mapper.SetScalarRange(vmin, vmax)
            self._mapper.UpdateInformation()
            # noinspection PyArgumentList
            self._mapper.Update()

    # noinspection PyArgumentList,PyUnresolvedReferences
    def setPointScalarColorFromVolume(self,
                                      vol: SisypheVolume,
                                      depth: cython.int = 0,
                                      feature: str = 'mean',
                                      wait: DialogWait | None = None) -> None:
        """
        Calculate scalar values associated to each vtkPolydata point from scalars values in the reference SisypheVolume
        image array.

        Several scalar values are accumulated for each vtkPolydata point, the first being the scalar value in the
        reference SisypheVolume image array to the point's coordinates, the next for points spaced by a constant step
        of 1 mm in the direction of the normal vector over a depth set in parameter. The value associated to each
        vtkPolydata point can be the mean, median, minimum, maximum or sum of the accumulated values.

        Parameters
        ----------
        vol : SisypheVolume
            reference volume
        depth : cython.int
            depth in mm, in the normal vector direction.
            if depth is 0.0, no accumulation (scalar value to the point's coordinates, default)
        feature : str
            'mean', 'median', 'min', 'max', 'sum'
        wait : DialogWait | None
            progress bar dialog (optional)
        """
        if self._polydata is not None:
            if isinstance(vol, SisypheVolume):
                origin = vol.getOrigin()
                vol.setDefaultOrigin()
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
                    vp: cython.double
                    p1: cython.double[3]
                    p2: cython.double[3]
                    if depth == 0:
                        for i in range(n):
                            p1 = points.GetPoint(i)
                            p2 = vol.getVoxelCoordinatesFromWorldCoordinates(p1)
                            vp = float(img[p2[0], p2[1], p2[2]])
                            scalars.SetTuple1(i, vp)
                            c += 1
                            if wait is not None and c == 100:
                                c = 0
                                wait.incCurrentProgressValue()
                    else:
                        f: cython.int
                        c: cython.int = 0
                        if feature == 'mean': f = 0
                        elif feature == 'median': f = 1
                        elif feature == 'min': f = 2
                        elif feature == 'max': f = 3
                        elif feature == 'sum': f = 4
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
                            elif f == 1:
                                # noinspection PyTypeChecker
                                scalars.SetTuple1(i, median(v))
                            elif f == 2: scalars.SetTuple1(i, v.min())
                            elif f == 3: scalars.SetTuple1(i, v.max())
                            elif f == 4: scalars.SetTuple1(i, v.sum())
                            c += 1
                            if wait is not None and c == 100:
                                c = 0
                                wait.incCurrentProgressValue()
                    self._polydata.GetPointData().SetScalars(scalars)
                    self._polydata.GetPointData().SetActiveScalars(vol.getName())
                    self.setLUT(vol.display.getLUT())
                    self._actor = vtkActor()
                    self._actor.SetMapper(self._mapper)
                    vol.setOrigin(origin)
                    if wait is not None: wait.setProgressVisibility(False)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def setAmbient(self, v: float) -> None:
        """
        Set mesh ambient lighting coefficient of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetAmbient(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getAmbient(self) -> float:
        """
        Get mesh ambient lighting coefficient of the current SisypheMesh instance.

        Returns
        -------
        float
            ambient lighting coefficient
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetAmbient()
        else: raise AttributeError('Polydata attribute is None.')

    def setDiffuse(self, v: float) -> None:
        """
        Set mesh diffuse lighting coefficient of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            diffuse lighting coefficient (between 0.0 and 1.0)
        """
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetDiffuse(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getDiffuse(self) -> float:
        """
        Get mesh diffuse lighting coefficient of the current SisypheMesh instance.

        Returns
        -------
        float
            diffuse lighting coefficient
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetDiffuse()
        else: raise AttributeError('Polydata attribute is None.')

    def setSpecular(self, v: float) -> None:
        """
        Set mesh specular lighting coefficient of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            specular lighting coefficient (between 0.0 and 1.0)
        """
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetSpecular(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecular(self) -> float:
        """
        Get mesh specular lighting coefficient of the current SisypheMesh instance.

        Returns
        -------
        float
            specular lighting coefficient
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetSpecular()
        else: raise AttributeError('Polydata attribute is None.')

    def setSpecularPower(self, v: float) -> None:
        """
        Set mesh specular power of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            specular power (between 0.0 and 50.0)
        """
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.0 <= v <= 50.0:
                    self._actor.GetProperty().SetSpecularPower(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 50.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getSpecularPower(self) -> float:
        """
        Get mesh specular power of the current SisypheMesh instance.

        Returns
        -------
        float
            specular power
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetSpecularPower()
        else: raise AttributeError('Polydata attribute is None.')

    def setMetallic(self, v: float) -> None:
        """
        Set mesh metallic coefficient of the current SisypheMesh instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Parameters
        ----------
        v : float
            metallic coefficient
        """
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetMetallic(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getMetallic(self) -> float:
        """
        Get mesh metallic coefficient of the current SisypheMesh instance. Usually this value is either 0.0 or 1.0 for
        real material but any value in between is valid. This parameter is only used by PBR Interpolation (Default is
        0.0).

        Returns
        -------
        float
            metallic coefficient
        """
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            return self._actor.GetProperty().GetMetallic()
        else: raise AttributeError('Polydata attribute is None.')

    def setRoughness(self, v: float) -> None:
        """
        Set mesh roughness coefficient of the current SisypheMesh instance. This value has to be between 0.0 (glossy)
        and 1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Parameters
        ----------
        v : float
            roughness coefficient, between 0.0 (glossy) and 1.0 (rough)
        """
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            if isinstance(v, float):
                if 0.0 <= v <= 1.0:
                    self._actor.GetProperty().SetRoughness(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def getRoughness(self) -> float:
        """
        Get mesh roughness coefficient of the current SisypheMesh instance. This value has to be between 0.0 (glossy)
        and 1.0 (rough). A glossy material has reflections and a high specular part. This parameter is only used by PBR
        Interpolation (Default 0.5)

        Returns
        -------
        float
            roughness coefficient, between 0.0 (glossy) and 1.0 (rough)
        """
        if self._polydata is not None:
            # Only used by PBR rendering algorithm
            return self._actor.GetProperty().GetRoughness()
        else: raise AttributeError('Polydata attribute is None.')

    def setFlatRendering(self) -> None:
        """
        Set "Flat" shading interpolation method to render the mesh of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToFlat()

    def setGouraudRendering(self) -> None:
        """
        Set "Gouraud" shading interpolation method to render the mesh of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToGouraud()

    def setPhongRendering(self) -> None:
        """
        Set "Phong" shading interpolation method to render the mesh of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToPhong()

    def setPBRRendering(self) -> None:
        """
        Set "PBR" shading interpolation method to render the mesh of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetInterpolationToPBR()

    def setRenderingAlgorithm(self, r: int) -> None:
        """
        Set the shading interpolation method, as int code, used to render the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        r : int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
        self._actor.GetProperty().SetInterpolation(r)

    def getRenderingAlgorithmAsString(self) -> str:
        """
        Get the shading interpolation method (as string) used to render the mesh of the current SisypheMesh instance.

        Returns
        -------
        str
            'Flat', 'Gouraud', 'Phong', 'PBR'
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetInterpolationAsString()
        else: raise AttributeError('Polydata attribute is None.')

    def getRenderingAlgorithm(self) -> int:
        """
        Get the shading interpolation method (as int code) used to render the mesh of the current SisypheMesh instance.

        Returns
        -------
        int
            shading interpolation code (0 'Flat', 1 'Gouraud', 2 'Phong', 3 'PBR')
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetInterpolation()
        else: raise AttributeError('Polydata attribute is None.')

    def setRenderPointsAsSpheresOn(self) -> None:
        """
        Render mesh points of the current SisypheMesh instance as spheres.
        """
        if self._polydata is not None:
            self._actor.GetProperty().RenderPointsAsSpheresOn()

    def setRenderPointsAsSpheresOff(self) -> None:
        """
        Stop rendering mesh points of the current SisypheMesh instance as spheres.
        """
        if self._polydata is not None:
            self._actor.GetProperty().RenderPointsAsSpheresOff()

    def getRenderPointsAsSpheres(self) -> bool:
        """
        Checks whether mesh points in the current SisyphusMesh instance are rendered as spheres.

        Returns
        -------
        bool
            True if mesh points are rendered as spheres
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetRenderPointsAsSpheres() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def setRenderLinesAsTubesOn(self) -> None:
        """
        Render mesh lines of the current SisypheMesh instance as tubes.
        """
        if self._polydata is not None:
            self._actor.GetProperty().RenderLinesAsTubesOn()

    def setRenderLinesAsTubesOff(self) -> None:
        """
        Stop rendering mesh lines of the current SisypheMesh instance as tubes.
        """
        if self._polydata is not None:
            self._actor.GetProperty().RenderLinesAsTubesOff()

    def getRenderLinesAsTubes(self) -> bool:
        """
        Checks whether mesh lines in the current SisyphusMesh instance are rendered as tubes

        Returns
        -------
        bool
            True if mesh lines are rendered as tubes
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetRenderLinesAsTubes() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def setVertexVisibilityOn(self) -> None:
        """
        Show mesh vertex of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().VertexVisibilityOn()

    def setVertexVisibilityOff(self) -> None:
        """
        Hide mesh vertex of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().VertexVisibilityOff()

    def getVertexVisibility(self) -> bool:
        """
        Get mesh vertex visibility of the current SisypheMesh instance.

        Returns
        -------
        bool
            True if vertices are visible
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetVertexVisibility() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def setVertexColor(self, r: float, g: float, b: float) -> None:
        """
        Set the mesh vertex color of the current SisypheMesh instance.

        Parameters
        ----------
        r : float
            vertex color, 0.0 <= red component <= 1.0
        g : float
            vertex color, 0.0 <= green component <= 1.0
        b : float
            vertex color, 0.0 <= blue component <= 1.0
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetVertexColor(r, g, b)

    # noinspection PyTypeChecker
    def getVertexColor(self) -> vectorFloat3Type:
        """
        Get the mesh vertex color of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, float, float]
            vertex color, red, green, blue (0.0 <= value <= 1.0)
        """
        if self._polydata is not None: return self._actor.GetProperty().GetVertexColor()
        else: raise ValueError('Polydata attribute is None.')

    def setVertexQColor(self, c: QColor) -> None:
        """
        Set the mesh vertex color of the current SisypheMesh instance from a QColor.

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            vertex color
        """
        self.setVertexColor(c.redF(), c.greenF(), c.blueF())

    def getVertexQColor(self) -> QColor:
        """
        Get the mesh vertex color (as QColor) of the current SisypheMesh instance

        Returns
        -------
        PyQt5.QtGui.QColor
            vertex color
        """
        r, g, b = self.getVertexColor()
        c = QColor()
        c.setRgbF(r, g, b, 1.0)
        return c

    def setEdgeVisibilityOn(self) -> None:
        """
        Show mesh edges of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().EdgeVisibilityOn()

    def setEdgeVisibilityOff(self) -> None:
        """
        Hide mesh edges of the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().EdgeVisibilityOff()

    def getEdgeVisibility(self) -> bool:
        """
        Get mesh edges visibility of the current SisypheMesh instance.

        Returns
        -------
        bool
            True if edges are visbile
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetEdgeVisibility() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def setEdgeColor(self, r: float, g: float, b: float) -> None:
        """
        Set the mesh edges color of the current SisypheMesh instance.

        Parameters
        ----------
        r : float
            edges color, 0.0 <= red component <= 1.0
        g : float
            edges color, 0.0 <= green component <= 1.0
        b : float
            edges color, 0.0 <= blue component <= 1.0
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetEdgeColor(r, g, b)

    # noinspection PyTypeChecker
    def getEdgeColor(self) -> vectorFloat3Type:
        """
        Get the mesh edges color of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, float, float]
            edges color, red, green, blue (0.0 <= value <= 1.0)
        """
        if self._polydata is not None: return self._actor.GetProperty().GetEdgeColor()
        else: raise ValueError('Polydata attribute is None.')

    def setEdgeQColor(self, c: QColor) -> None:
        """
        Set the mesh edges color of the current SisypheMesh instance from a QColor.

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            edges color
        """
        self.setEdgeColor(c.redF(), c.greenF(), c.blueF())

    def getEdgeQColor(self) -> QColor:
        """
        Get the mesh edges color (as QColor) of the current SisypheMesh instance

        Returns
        -------
        PyQt5.QtGui.QColor
            edges color
        """
        r, g, b = self.getEdgeColor()
        c = QColor()
        c.setRgbF(r, g, b, 1.0)
        return c

    def setLineWidth(self, v: float) -> None:
        """
        Set line width size (mm) of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            line width in mm
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetLineWidth(v)

    def getLineWidth(self) -> float:
        """
        Get mesh line width (mm) of the current SisypheMesh instance.

        Returns
        -------
        float
            line width in mm
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetLineWidth()
        else: raise AttributeError('Polydata attribute is None.')

    def setPointSize(self, v: float) -> None:
        """
        Set mesh point size (mm) of the current SisypheMesh instance.

        Parameters
        ----------
        v : float
            point size in mm
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetPointSize(v)

    def getPointSize(self) -> float:
        """
        Get mesh point size (mm) of the current SisypheMesh instance.

        Returns
        -------
        float
            point size in mm
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetPointSize()
        else: raise AttributeError('Polydata attribute is None.')

    def getShading(self) -> bool:
        """
        Get the mesh shading mode of the current SisypheMesh instance.

        Returns
        -------
        bool
            True if shading id on
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetShading() > 0
        else: raise AttributeError('Polydata attribute is None.')

    def shadingOn(self) -> None:
        """
        Enables mesh shading mode for the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().ShadingOn()

    def shadingOff(self) -> None:
        """
        Disables mesh shading mode for the current SisypheMesh instance.
        """
        if self._polydata is not None:
            self._actor.GetProperty().ShadingOff()

    # Mesh sources

    def createLine(self, p1: vectorFloat3Type, p2: vectorFloat3Type, d: float) -> None:
        """
        Create a line-shaped SisypheMesh instance.

        Parameters
        ----------
        p1 : list[float, float, float]
            first point coordinates
        p2 : list[float, float, float]
            second point coordinates
        d : float
            line width (mm)
        """
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        # noinspection PyArgumentList
        line.Update()
        self.setPolyData(line.GetOutput())
        self.setLineWidth(d)
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Line#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createTube(self, p1: vectorFloat3Type, p2: vectorFloat3Type, r: float, sides: int) -> None:
        """
        Create a tube-shaped SisypheMesh instance.

        Parameters
        ----------
        p1 : list[float, float, float]
            first point coordinates
        p2 : list[float, float, float]
            second point coordinates
        r : float
            tube radius (mm)
        sides : int
            number of sides
        """
        line = vtkLineSource()
        line.SetPoint1(p1[0], p1[1], p1[2])
        line.SetPoint2(p2[0], p2[1], p2[2])
        # noinspection PyArgumentList
        line.Update()
        tube = vtkTubeFilter()
        # noinspection PyArgumentList
        tube.SetInputConnection(line.GetOutputPort())
        tube.SetRadius(r)
        tube.SetNumberOfSides(sides)
        # noinspection PyArgumentList
        tube.Update()
        self.setPolyData(tube.GetOutput())
        self.setColor(1.0, 0.0, 0.0)
        self._name = 'Tube#{}'.format(id(self))
        self._filename = join(self._name + self.getFileExt())

    def createSphere(self, r: float, p: vectorFloat3Type = (0.0, 0.0, 0.0), res: int = 64) -> None:
        """
        Create a sphere-shaped SisypheMesh instance.

        Parameters
        ----------
        r : float
            sphere radius (mm)
        p : list[float, float, float]
            center coordinates
        res : int
            set the number of points in the latitude and longitude directions (default 64)
        """
        sphere = vtkSphereSource()
        sphere.SetThetaResolution(res)
        sphere.SetPhiResolution(res)
        sphere.SetRadius(r)
        # noinspection PyArgumentList
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
        Create a cube-shaped SisypheMesh instance.

        Parameters
        ----------
        dx : float
            length of the cube in the x-direction (mm)
        dy : float
            length of the cube in the y-direction (mm)
        dz : float
            length of the cube in the z-direction (mm)
        p : list[float, float, float]
            position coordinates
        """
        cube = vtkCubeSource()
        cube.SetXLength(dx)
        cube.SetYLength(dy)
        cube.SetZLength(dz)
        # noinspection PyArgumentList
        cube.Update()
        polydata = cube.GetOutput()
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
                           img: SisypheVolume,
                           seg: str = 'huang',
                           fill: float = 1000.0,
                           decimate: float = 1.0,
                           clean: bool = False,
                           smooth: str = 'sinc',
                           niter: int = 10,
                           factor: float = 0.1,
                           algo: str = 'flying',
                           largest: bool = True) -> None:
        """
        Create brain/head outer surface SisypheMesh instance.

        Parameters
        ----------
        img : SisypheVolume
            reference image used to process outer surface
        seg : str
            algorithm used for automatic object/background segmentation: 'mean', 'otsu', 'huang', 'renyi', 'yen', 'li',
            'shanbhag', 'triangle', 'intermodes','maximumentropy', 'kittler', 'isodata', 'moments'
        fill : float
            identify and fill holes in mesh (See docstring for the fillHoles method)
        decimate : float
            mesh points reduction percentage (between 0.0 and 1.0, See docstring for the decimate method)
        clean : bool
            merge duplicate points, remove unused points and remove degenerate cells (See docstring for the clean method)
        smooth : str
            'sinc', 'laplacian', smoothing algorithm (See docstrings for the sincSmooth and laplacianSmooth methods)
        niter : int
            number of iterations (default 20)
        factor : float
            - lower values produce more smoothing (between 0.0 and 1.0)
            - if smooth == 'sinc', passband factor
            - if smooth == 'laplacian', relaxation factor
        algo : str
            'contour', 'marching', 'flying', algorithm used to generate isosurface
        largest : bool
            keep only the largest isosurface (default False)
        """
        if isinstance(img, SisypheVolume):
            seg = seg.lower()
            roi = img.getMaskROI2(algo=seg, kernel=0)
            self.createFromROI(roi, fill, decimate, clean, smooth, niter, factor, algo, largest)
            self._name = 'Outer surface'
            self._filename = join(img.getDirname(), self._name + self.getFileExt())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def createIsosurface(self,
                         img: SisypheVolume,
                         isovalue: float,
                         fill: float = 1000.0,
                         decimate: float = 1.0,
                         clean: bool = False,
                         smooth: str = 'sinc',
                         niter: int = 10,
                         factor: float = 0.1,
                         algo: str = 'flying',
                         largest: bool = False) -> None:
        """
        Create isosurface SisypheMesh instance.

        Parameters
        ----------
        img : Sisyphe.core.sisypheVolume.SisypheVol
            reference image used to process isosurface
        isovalue : float
            threshold used as isovalue to generate isosurface
        fill : float
            identify and fill holes in mesh (See docstring for the fillHoles method)
        decimate : float
            mesh points reduction percentage (between 0.0 and 1.0, See docstring for the decimate method)
        clean : bool
            merge duplicate points, remove unused points and remove degenerate cells (See docstring for the clean method)
        smooth : str
            'sinc', 'laplacian', smoothing algorithm (See docstrings for the sincSmooth and laplacianSmooth methods)
        niter : int
            number of iterations (default 20)
        factor : float
            lower values produce more smoothing (between 0.0 and 1.0)
            - if smooth == 'sinc', passband factor
            - if smooth == 'laplacian', relaxation factor
        algo : str
            'contour', 'marching', 'flying', algorithm used to generate isosurface
        largest : bool
            keep only the largest isosurface (default False)
        """
        if isinstance(img, SisypheVolume):
            inf, sup = img.getDisplay().getRange()
            if inf <= isovalue <= sup:
                # Convert image datatype to float if not
                if img.isFloatDatatype(): vtkimg = img.getVTKImage()
                else:
                    f = vtkImageCast()
                    f.SetInputData(img.getVTKImage())
                    f.SetOutputScalarTypeToFloat()
                    # noinspection PyArgumentList
                    f.Update()
                    vtkimg = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Generate isosurface
                algo = algo.lower()
                if algo == 'contour': f = vtkContourFilter()
                elif algo == 'marching': f = vtkMarchingCubes()
                elif algo == 'flying': f = vtkFlyingEdges3D()
                else: raise ValueError('parameter algorithm {} is not implemented.'.format(algo))
                f.SetInputData(vtkimg)
                f.ComputeNormalsOff()
                f.SetValue(0, isovalue)
                # noinspection PyArgumentList
                f.Update()
                result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Largest isosurface
                if isinstance(largest, bool):
                    if largest:
                        f = vtkPolyDataConnectivityFilter()
                        f.SetInputData(result)
                        f.SetExtractionModeToLargestRegion()
                        f.ScalarConnectivityOff()
                        # noinspection PyArgumentList
                        f.Update()
                        result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Decimate
                if isinstance(decimate, float):
                    if 0.1 <= decimate < 1.0:
                        if result.GetCellType(0) != VTK_TRIANGLE:
                            f = vtkTriangleFilter()
                            f.SetInputData(result)
                            # noinspection PyArgumentList
                            f.Update()
                            result = f.GetOutput()
                        f = vtkDecimatePro()
                        f.SetInputData(result)
                        f.PreserveTopologyOn()
                        f.SetTargetReduction(decimate)
                        # noinspection PyArgumentList
                        f.Update()
                        result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Fill holes
                if isinstance(fill, float):
                    if fill > 0.0:
                        f = vtkFillHolesFilter()
                        f.SetInputData(result)
                        f.SetHoleSize(fill)
                        f.Update()
                        result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Clean
                if isinstance(clean, bool):
                    if clean:
                        f = vtkCleanPolyData()
                        f.SetInputData(result)
                        # noinspection PyArgumentList
                        f.Update()
                        result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
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
                        # noinspection PyArgumentList
                        f.Update()
                        result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Create triangle strips
                f = vtkStripper()
                f.SetInputData(result)
                # noinspection PyArgumentList
                f.Update()
                result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                # Calc normals
                f = vtkPolyDataNormals()
                f.SetInputData(result)
                f.SetFeatureAngle(60.0)
                f.ComputePointNormalsOn()
                f.ComputeCellNormalsOn()
                f.AutoOrientNormalsOn()
                f.ConsistencyOn()
                f.SplittingOn()
                # noinspection PyArgumentList
                f.Update()
                result = f.GetOutput()
                if QApplication.instance() is not None: QApplication.processEvents()
                self.setPolyData(result)
                self.setColor(1.0, 0.0, 0.0)
                self._name = 'isosurface#{}'.format(isovalue)
                self._filename = join(img.getDirname(), self._name + self.getFileExt())
                self.setReferenceID(img)
            else: raise ValueError('parameter isovalue {} is not between {} and {}.'.format(isovalue, inf, sup))
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(img)))

    def createFromROI(self,
                      roi: SisypheROI,
                      fill: float = 1000.0,
                      decimate: float = 1.0,
                      clean: bool = False,
                      smooth: str = 'sinc',
                      niter: int = 10,
                      factor: float = 0.1,
                      algo: str = 'flying',
                      largest: bool = False) -> None:
        """
        Create SisypheMesh instance from SisypheROI.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            image used to process isosurface
        fill : float
            identify and fill holes in mesh (See docstring for the fillHoles method)
        decimate : float
            mesh points reduction percentage (between 0.0 and 1.0, See docstring for the decimate method)
        clean : bool
            merge duplicate points, remove unused points and remove degenerate cells (See docstring for the clean method)
        smooth : str
            'sinc', 'laplacian', smoothing algorithm (See docstrings for the sincSmooth and laplacianSmooth methods)
        niter : int
            number of iterations (default 20)
        factor : float
            lower values produce more smoothing (between 0.0 and 1.0)
            - if smooth == 'sinc', passband factor
            - if smooth == 'laplacian', relaxation factor
        algo : str
            'contour', 'marching', 'flying', algorithm used to generate isosurface
        largest : bool
            keep only the largest isosurface (default False)
        """
        if isinstance(roi, SisypheROI):
            mask = roi.getSITKImage()
            # Fill mask in each 2D axial slice
            if fill > 0.0:
                f = BinaryFillholeImageFilter()
                for i in range(mask.GetSize()[2]):
                    slc = mask[:, :, i]
                    slc = f.Execute(slc)
                    mask[:, :, i] = slc
                    if QApplication.instance() is not None: QApplication.processEvents()
            # Convert to float
            mask = Cast(mask, sitkFloat32)
            if QApplication.instance() is not None: QApplication.processEvents()
            # Smoothing
            mask *= 100
            mask = SmoothingRecursiveGaussian(mask, [1.0, 1.0, 1.0])
            if QApplication.instance() is not None: QApplication.processEvents()
            img = SisypheVolume(mask)
            self.createIsosurface(img, 50, fill, decimate, clean, smooth, niter, factor, algo, largest)
            self._name = roi.getName()
            c = roi.getColor()
            self.setColor(c[0], c[1], c[2])
            self.setReferenceID(roi.getReferenceID())
            self.setDefaultFilename()
            if roi.hasFilename(): self.setDirname(roi.getDirname())
        else: raise TypeError('parameter type {} is not SisypheROI.'.format(type(roi)))

    # Processing methods

    def decimate(self, v: float, updatenormals: bool = True) -> None:
        """
        Reduce the number of triangles in the mesh of the SisypheMesh instance.

        Parameters
        ----------
        v : float
            reduction ratio (between 0.0 and 1.0), ex. 0.2, -20% of triangles
        updatenormals : bool
            recalculate normals after reduction
        """
        if self._polydata is not None:
            if isinstance(v, float):
                if 0.1 <= v < 1.0:
                    # Convert to triangle mesh if not
                    if self._polydata.GetCellType(0) != VTK_TRIANGLE:
                        f = vtkTriangleFilter()
                        f.SetInputData(self._polydata)
                        # noinspection PyArgumentList
                        f.Update()
                        self._polydata = f.GetOutput()
                    f = vtkDecimatePro()
                    f.SetInputData(self._polydata)
                    f.PreserveTopologyOn()
                    f.SetTargetReduction(v)
                    # noinspection PyArgumentList
                    f.Update()
                    self.setPolyData(f.GetOutput())
                    if updatenormals: self._updateNormals()
                else: raise ValueError('parameter value {} is not between 0.1 and 1.0.'.format(v))
            else: raise TypeError('parameter type {} is not float.'.format(type(v)))
        else: raise ValueError('vtkPolyData is empty.')

    def clean(self, updatenormals: bool = True) -> None:
        """
        Merge duplicate points, remove unused points and remove degenerate cells in the mesh of the current SisypheMesh
        instance.

        Parameters
        ----------
        updatenormals : bool
            recalculate normals after reduction
        """
        if self._polydata is not None:
            f = vtkCleanPolyData()
            f.SetInputData(self._polydata)
            # noinspection PyArgumentList
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
        Adjust mesh point positions using a windowed sinc function interpolation kernel of the current SisypheMesh
        instance. The effect is to "smooth" the mesh, making the cells better shaped and the vertices more evenly
        distributed.

        Parameters
        ----------
        niter : int
            determines the maximum number of smoothing iterations (between 10 and 20, default 10)
        passband : float
            pass band factor, lower values produce more smoothing (between 0.0 and 2.0, default 0.1)
        edge : bool
            enables/disables customized smoothing of the interior vertices. Interior vertices are classified as either
            "simple", "interior edge", or "fixed", and smoothed differently. A feature edge occurs when the angle
            between the two surface normals of a polygon sharing an edge s greater than a feature angle (45°). Then,
            vertices used by no feature edges are classified "simple", vertices used by exactly two feature edges are
            classified "interior edge", and all others are "fixed" vertices. "fixed" vertices are not smoothed at all.
            "simple" vertices are smoothed as before. "interior edge" vertices are smoothed only along their two
            connected edges, and only if the angle between the edges is less than an edge angle (15°).
        boundary : bool
            enables/disables the smoothing operation on vertices that are on the "boundary" of the mesh. A boundary
            vertex is one that is surrounded by a semi-cycle of polygons (or used by a single line)
        updatenormals : bool
            recalculate normals after reduction
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
            # noinspection PyArgumentList
            f.Update()
            self.setPolyData(f.GetOutput())
            if updatenormals: self._updateNormals()
        else: raise ValueError('vtkPolyData is empty.')

    # noinspection PyArgumentList
    def laplacianSmooth(self,
                        niter: int = 20,
                        relax: float = 0.1,
                        edge: bool = True,
                        boundary: bool = True,
                        updatenormals: bool = True) -> None:
        """
        Adjust mesh point positions using a Laplacian smoothing of the current SisypheMesh instance. The effect is to
        "smooth" the mesh, making the cells better shaped and the vertices more evenly distributed.

        Parameters
        ----------
        niter : int
            determines the maximum number of smoothing iterations (between 10 and 100, default 20)
        relax : float
            relaxation factor, lower values produce more smoothing. Small relaxation factors and large numbers of
            iterations are more stable than larger relaxation factors and smaller numbers of iterations (between 0.0
            and 1.0, default 0.1)
        edge : bool
            enables/disables customized smoothing of the interior vertices. Interior vertices are classified as either
            "simple", "interior edge", or "fixed", and smoothed differently. A feature edge occurs when the angle
            between the two surface normals of a polygon sharing an edge is greater than a feature angle (45°). Then,
            vertices used by no feature edges are classified "simple", vertices used by exactly two feature edges are
            classified "interior edge", and all others are "fixed" vertices. "fixed" vertices are not smoothed at all.
            "simple" vertices are smoothed as before. "interior edge" vertices are smoothed only along their two
            connected edges, and only if the angle between the edges is less than an edge angle (15°).
        boundary : bool
            enables/disables the smoothing operation on vertices that are on the "boundary" of the mesh. A boundary
            vertex is one that is surrounded by a semi-cycle of polygons (or used by a single line)
        updatenormals : bool
            recalculate normals after reduction
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
        """
        Identify and fill mesh holes of the current SisypheMesh instance.

        Parameters
        ----------
        size : float
            size threshold of the hole that can be filled, radius to the bounding circumsphere containing the hole
            (default 1000.0).
        updatenormals : bool
            recalculate normals after reduction
        """
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
               decimate: float = 0.5,
               clean: bool = False,
               smooth: str = 'sinc',
               niter: int = 20,
               factor: float = 0.1) -> None:
        """
        Mesh filtering of the current SisypheMesh instance. rocessing order: decimate, fill holes, clean and finally
        smooth.

        Parameters
        ----------
        fill : float
            identify and fill holes in mesh (See docstring for the fillHoles method)
        decimate : float
            mesh points reduction percentage (between 0.0 and 1.0, See docstring for the decimate method)
        clean : bool
            merge duplicate points, remove unused points and remove degenerate cells (See docstring for the clean method)
        smooth : str
            'sinc', 'laplacian', smoothing algorithm (See docstrings for the sincSmooth and laplacianSmooth methods)
        niter : int
            number of iterations (default 20)
        factor : float
            - lower values produce more smoothing (between 0.0 and 1.0)
            - if smooth == 'sinc', passband factor
            - if smooth == 'laplacian', relaxation factor
        """
        if self._polydata is not None:
            result = self._polydata
            # Decimate
            if isinstance(decimate, float):
                if 0.1 <= decimate < 1.0:
                    if result.GetCellType(0) != VTK_TRIANGLE:
                        f = vtkTriangleFilter()
                        f.SetInputData(result)
                        # noinspection PyArgumentList
                        f.Update()
                        result = f.GetOutput()
                    f = vtkDecimatePro()
                    f.SetInputData(result)
                    f.PreserveTopologyOn()
                    f.SetTargetReduction(decimate)
                    # noinspection PyArgumentList
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
                    # noinspection PyArgumentList
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
                    # noinspection PyArgumentList
                    f.Update()
                    result = f.GetOutput()
            # Create triangle strips
            f = vtkStripper()
            f.SetInputData(result)
            # noinspection PyArgumentList
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
            # noinspection PyArgumentList
            f.Update()
            result = f.GetOutput()
            # Result
            self._name = 'filter {}'.format(self._name)
            self.setPolyData(result)
        else: raise ValueError('vtkPolyData is empty.')

    def combinePolyData(self, data: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> None:
        """
        Combine a mesh to the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        data : vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh
            mesh to append
        """
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
                # noinspection PyArgumentList
                fcombine.Update()
                fclean = vtkCleanPolyData()
                # noinspection PyArgumentList
                fclean.SetInputConnection(fcombine.GetOutputPort())
                # noinspection PyArgumentList
                fclean.Update()
                self.setPolyData(fclean.GetOutput())
                self._name = 'Combine {}'.format(self._name)
                if name != '': self._name = self._name + ' {}'.format(name)
            else: raise TypeError('parameter functype is not SisypheMesh, vtkActor, vtkPolyDataMapper or vtkPolydata.')
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def union(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        """
        Union of meshes with the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        datas : SisypheMesh | list[SisypheMesh]
            mesh(es) used for union
        """
        if self._polydata is not None:
            roi = self.convertToSisypheROI(refimg=None)
            if self._name[:5] != 'Union': name = 'Union {}'.format(self._name)
            else: name = self._name
            if not isinstance(datas, list): datas = [datas]
            for data in datas:
                if isinstance(data, SisypheMesh):
                    roi = roi | data.convertToSisypheROI(refimg=None)
                    if QApplication.instance() is not None: QApplication.processEvents()
                    if data._name != '': name += ' {}'.format(data._name)
                else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(data)))
            roi.setName(name)
            roi.setReferenceID(self.getReferenceID())
            if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
            else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def intersection(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        """
        Intersection of meshes with the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        datas : SisypheMesh | list[SisypheMesh]
            mesh(es) used for intersection
        """
        if self._polydata is not None:
            roi = self.convertToSisypheROI(refimg=None)
            if self._name[:12] != 'Intersection': name = 'Intersection {}'.format(self._name)
            else: name = self._name
            if not isinstance(datas, list): datas = [datas]
            for data in datas:
                if isinstance(data, SisypheMesh):
                    roi2 = data.convertToSisypheROI(refimg=None)
                    roi = roi & roi2
                    if QApplication.instance() is not None: QApplication.processEvents()
                    if data._name != '': name += ' {}'.format(data._name)
                else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(data)))
            roi.setName(name)
            roi.setReferenceID(self.getReferenceID())
            if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
            else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def difference(self, datas: SisypheMesh | list[SisypheMesh]) -> None:
        """
        Difference between mesh of the current SisypheMesh instance and meshes union.

        Parameters
        ----------
        datas : SisypheMesh | list[SisypheMesh]
            mesh(es) used for difference
        """
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
                            if QApplication.instance() is not None: QApplication.processEvents()
                            if datas[i].getName() != '': name += ' {}'.format(datas[i].getName())
                        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(datas)))
                roi = roi - roi2
                if QApplication.instance() is not None: QApplication.processEvents()
                roi.setName(name)
                roi.setReferenceID(self.getReferenceID())
                if roi.getNumberOfNonZero() > 0: self.createFromROI(roi)
                else: self.clear()
        else: raise ValueError('Mesh vtkPolyData is empty.')

    def dilate(self, mm: float) -> None:
        """
        Expand mesh of the current SisypheMesh instance with an isotropic margin in mm.

        Parameters
        ----------
        mm : float
            isotropic margin in mm
        """
        if isinstance(mm, (float, int)):
            if self._polydata is not None:
                # < Revision 22/03/2025
                roi = self.convertToSisypheROI(refimg=None)
                dmap = roi.getDistanceMap()
                roi = dmap.getROI(mm, '<=')
                if roi.getNumberOfNonZero() > 0: self.createIsosurface(dmap, mm)
                else: self.clear()
                self._name = 'Expand#{} {}'.format(mm, self._name)
                # Revision 22/03/2025 >
            else: raise ValueError('Mesh vtkPolyData is empty.')
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def erode(self, mm: float) -> None:
        """
        Shrink mesh of the current SisypheMesh instance with an isotropic margin in mm.

        Parameters
        ----------
        mm : float
            isotropic margin in mm
        """
        if isinstance(mm, (float, int)):
            if self._polydata is not None:
                # < Revision 22/03/2025
                roi = self.convertToSisypheROI(refimg=None)
                dmap = roi.getDistanceMap()
                roi = dmap.getROI(-mm, '<=')
                if roi.getNumberOfNonZero() > 0: self.createIsosurface(dmap, -mm)
                else: self.clear()
                self._name = 'Shrink#{} {}'.format(mm, self._name)
                # Revision 22/03/2025 >
            else: raise ValueError('Mesh vtkPolyData is empty.')
        else: raise TypeError('parameter type {} is not float.'.format(type(mm)))

    def update(self) -> None:
        """
        Update mesh rendering of the current SisypheMesh instance.
        """
        self._mapper.UpdateInformation()
        # noinspection PyArgumentList
        self._mapper.Update()

    # Polydata features

    def getMeshVolume(self) -> float:
        """
        Get mesh volume (mm3) of the current SisypheMesh instance.

        Returns
        -------
        float
            mesh volume (mm3)
        """
        if self._polydata is not None:
            f = vtkMassProperties()
            f.SetInputData(self._polydata)
            return f.GetVolume()
        else: raise AttributeError('Polydata attribute is None.')

    def getMeshSurface(self) -> float:
        """
        Get mesh surface (mm2) of the current SisypheMesh instance.

        Returns
        -------
        float
            mesh surface (mm2)
        """
        if self._polydata is not None:
            f = vtkMassProperties()
            f.SetInputData(self._polydata)
            return f.GetSurfaceArea()
        else: raise AttributeError('Polydata attribute is None.')

    # noinspection PyTypeChecker
    def getCenterOfMass(self) -> vectorFloat3Type:
        """
        Get mesh center-of-mass coordinates of the current SisypheMesh instance.

        Returns
        -------
        tuple[float, float, float]
            center-of-mass coordinates
        """
        if self._polydata is not None:
            f = vtkCenterOfMass()
            f.SetInputData(self._polydata)
            f.SetUseScalarsAsWeights(False)
            # noinspection PyArgumentList
            f.Update()
            return f.GetCenter()
        else: raise ValueError('Polydata attribute is None.')

    # noinspection PyTypeChecker
    def getPrincipalAxis(self) -> tuple[vectorFloat3Type, vectorFloat3Type, vectorFloat3Type, vectorFloat3Type, vectorFloat3Type]:
        """
        Get mesh PCA axes of the current SisypheMesh instance.

        Returns
        -------
        tuple[tuple[float, float, float], ...]
            - first tuple[float, float, float], center-of-mass coordinates
            - second tuple[float, float, float], PCA major axis
            - third tuple[float, float, float], PCA intermediate axis
            - fourth tuple[float, float, float], PCA minor axis
            - fifth tuple[float, float, float], length of major, intermediate and minor axes
        """
        if self._polydata is not None:
            f = vtkOBBTree()
            center = [0.0, 0.0, 0.0]
            vmax = [0.0, 0.0, 0.0]
            vmid = [0.0, 0.0, 0.0]
            vmin = [0.0, 0.0, 0.0]
            size = [0.0, 0.0, 0.0]
            f.ComputeOBB(self._polydata, center, vmax, vmid, vmin, size)
            return center, vmax, vmid, vmin, size
        else: raise ValueError('Polydata attribute is None.')

    # noinspection PyTypeChecker
    def getDistanceFromSurfaceToPoint(self, p: vectorFloat3Type) -> tuple[float, vectorFloat3Type]:
        """
        Get distance between a point and the mesh surface of the current SisypheMesh instance.

        Parameters
        ----------
        p : tuple[float, float, float]
            point coordinates

        Returns
        -------
        tuple[float, list[float, float, float]]
            - float, distance between p and surface of the mesh
            - list[float, float, float], coordinates of the closest surface point of the mesh
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
        else: raise ValueError('Polydata attribute is None.')

    # noinspection PyTypeChecker
    def getDistanceFromSurfaceToSurface(self,
                                        mesh: vtkActor | vtkPolyDataMapper | vtkPolyData | SisypheMesh) -> tuple[float, float]:
        """
        Get distance between surfaces of a mesh and the mesh of the current SisypheMesh instance.

        Parameters
        ----------
        mesh : vtkPolyData | vtkPolyDataMapper | vtkActor | SisypheMesh

        Returns
        -------
        tuple[float, float]
            minimum and maximum distances between meshes
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
            else: raise TypeError('parameter type {} is not vtkPolyData, vtkActor or SisypheMesh.'.format(type(mesh)))
        else: raise AttributeError('Polydata attribute is None.')

    def isPointInside(self, p: vectorFloat3Type) -> bool:
        """
        Check whether a point is inside mesh of the current SisypheMesh instance.

        Parameters
        ----------
        p : tuple[float, float, float]
            point coordinates

        Returns
        -------
        bool
            True if point is inside mesh
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
        else: raise AttributeError('Polydata attribute is None.')

    def isPointOutside(self, p: vectorFloat3Type) -> bool:
        """
        Check whether a point is outside mesh of the current SisypheMesh instance.

        Parameters
        ----------
        p : tuple[float, float, float]
            point coordinates

        Returns
        -------
        bool
            True if point is outside mesh
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
        else: raise AttributeError('Polydata attribute is None.')

    # Image conversion methods

    def convertToVTKImage(self, refimg: SisypheVolume | None, tol: float = 0.0) -> vtkImageData:
        """
        Binary discretization of the current SisypheMesh instance mesh.

        Parameters
        ----------
        refimg : Sisyphe.core.sisypheVolume.SisypheVolume | None
            reference volume, mesh is discretized in this reference space
        tol : float
            The tolerance for including a voxel inside the mask. This is in fractions of a voxel, and must be between
            0.0 and 1.0 (default 0.0, no tolerance, all the voxel volume must be inside mesh to become part of the mask)

        Returns
        -------
        vtk.vtkImageData
            binary volume
        """
        if self._polydata is not None:
            if refimg is None:
                spacing = (1.0, 1.0, 1.0)
                origin = (0.0, 0.0, 0.0)
                size = (256, 256, 256)
            elif isinstance(refimg, SisypheVolume):
                spacing = refimg.getSpacing()
                # < Revision 23/03/2025
                # origin = refimg.getOrigin()
                origin = (0.0, 0.0, 0.0)
                # Revision 23/03/2025 >
                size = refimg.getSize()
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))
            # vtkPolyData to vtkImageStencil
            stencil = vtkPolyDataToImageStencil()
            stencil.SetTolerance(tol)
            stencil.SetInputData(self._polydata)
            # noinspection PyArgumentList
            stencil.SetOutputOrigin(origin)
            # noinspection PyArgumentList
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
        else: raise AttributeError('Polydata is None.')

    def convertToSisypheROI(self,
                            refimg: SisypheVolume | None,
                            tol: float = 0.0) -> SisypheROI:
        """
        Binary discretization of the current SisypheMesh instance mesh.

        Parameters
        ----------
        refimg : Sisyphe.core.sisypheVolume.SisypheVolume | None
            reference volume, mesh is discretized in this reference space
        tol : float
            The tolerance for including a voxel inside the mask. This is in fractions of a voxel, and must be between
            0.0 and 1.0 (default 0.0, no tolerance, all the voxel volume must be inside mesh to become part of the mask)

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            ROI
        """
        if self._polydata is not None:
            if refimg is None or isinstance(refimg, SisypheVolume):
                img = self.convertToVTKImage(refimg, tol)
                roi = SisypheROI()
                roi.copyFromVTKImage(img)
                if refimg is not None: roi.setOrigin(refimg.getOrigin())
                roi.setName(self.getName())
                roi.setColor(rgb=self.getColor())
                roi.setReferenceID(self.getReferenceID())
                roi.setDefaultFilename()
                if self.hasFilename(): roi.setDirname(self.getDirname())
                elif refimg is not None: roi.setDirname(refimg.getDirname())
                return roi
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))
        else: raise AttributeError('Polydata attribute is None.')

    def convertToSisypheVolume(self,
                               refimg: SisypheVolume,
                               tol: float = 0.0) -> SisypheVolume:
        """
        Binary discretization of the current SisypheMesh instance mesh.

        Parameters
        ----------
        refimg : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume, mesh is discretized in this reference space
        tol : float
            The tolerance for including a voxel inside the mask. This is in fractions of a voxel, and must be between
            0.0 and 1.0 (default 0.0, no tolerance, all the voxel volume must be inside mesh to become part of the mask)

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            binary volume
        """
        if self._polydata is not None:
            if refimg is None or isinstance(refimg, SisypheVolume):
                img = self.convertToVTKImage(refimg, tol)
                vol = SisypheVolume()
                vol.copyFromVTKImage(img)
                return vol
            else: raise TypeError('image parameter type {} is not SisypheVolume.'.format(type(refimg)))
        else: raise AttributeError('Polydata attribute is None.')

    # IO Public methods

    def loadFromOBJ(self, filename: str) -> None:
        """
        Load mesh of the current SisypheMesh instance from OBJ (.obj) file.

        Parameters
        ----------
        filename : str
            OBJ file name
        """
        self._actor = readMeshFromOBJ(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromSTL(self, filename: str) -> None:
        """
        Load mesh of the current SisypheMesh instance from STL (.stl) file.

        Parameters
        ----------
        filename : str
            STL file name
        """
        self._actor = readMeshFromSTL(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromVTK(self, filename: str) -> None:
        """
        Load mesh of the current SisypheMesh instance from VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        self._actor = readMeshFromVTK(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def loadFromXMLVTK(self, filename: str) -> None:
        """
        Load mesh of the current SisypheMesh instance from XMLVTK (.vtp) file.

        Parameters
        ----------
        filename : str
            XMLVTK Mesh file name
        """
        self._actor = readMeshFromXMLVTK(filename)
        self._mapper = self._actor.GetMapper()
        self._polydata = self._mapper.GetInput()
        self._updateNormals()
        self.setNameFromFilename(filename)
        path, ext = splitext(filename)
        self._filename = path + self._FILEEXT

    def ParseXML(self, doc: minidom.Document) -> None:
        """
        Read the current SisypheMesh instance attributes
        from xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
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
        """
        Load mesh of the current SisypheMesh instance from a PySisyphe Mesh (.xmesh) file.

        Parameters
        ----------
        filename : str
            PySisyphe Mesh file name
        """
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
        """
        Save the current SisypheMesh instance mesh to an OBJ (.obj) file.

        Parameters
        ----------
        filename : str
            OBJ file name
        """
        # noinspection PyArgumentList
        v = vtkVersion.GetVTKMajorVersion()
        if v >= 9:
            if self._polydata is not None:
                writeMeshToOBJ(self._polydata, filename)
                self.setNameFromFilename(filename)
        else: raise TypeError('VTK version {} (< 9) does not support saving of Obj format.'.format(v))

    def saveToSTL(self, filename: str) -> None:
        """
        Save the current SisypheMesh instance mesh to a STL (.stl) file.

        Parameters
        ----------
        filename : str
            STL file name
        """
        if self._polydata is not None:
            writeMeshToSTL(self._polydata, filename)
            self.setNameFromFilename(filename)

    def saveToVTK(self, filename: str) -> None:
        """
        Save the current SisypheMesh instance mesh to a VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        if self._polydata is not None:
            writeMeshToVTK(self._polydata, filename)
            self.setNameFromFilename(filename)

    def saveToXMLVTK(self, filename: str) -> None:
        """
        Save the current SisypheMesh instance mesh to XMLVTK (.vtp) file.

        Parameters
        ----------
        filename : str
            XMLVTK file name
        """
        if self._polydata is not None:
            writeMeshToXMLVTK(self._polydata, filename)
            self.setNameFromFilename(filename)

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
        Write the current SisypheMesh instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        currentnode : minidom.Element
            xml root node
        """
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
        """
        Save the current SisypheMesh instance mesh to a PySisyphe Mesh (.xmesh) file. This method uses the file name
        attribute of the current SisypheMesh instance.
        """
        if self.hasFilename(): self.saveAs(self._filename)
        else: raise AttributeError('Filename attribute is empty.')

    def saveAs(self, filename: str) -> None:
        """
        Save the current SisypheMesh instance mesh to a PySisyphe Mesh (.xmesh) file.

        Parameters
        ----------
        filename : str
            PySisyphe Mesh file name
        """
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
    Description
    ~~~~~~~~~~~

    Named list container of SisypheMesh instances. Container key to address elements can be an int index, a mesh name
    str or a SisypheMesh instance (uses name attribute as str key).

    Getter methods of the SisypheMesh class are added to the SisypheMeshCollection class, returning a list of values
    returned by each SisypheMesh element in the container.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheMeshCollection

    Creation: 22/03/2023
    Last revision: 23/05/2024
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

    """
    Private attributes

    _meshes         list[SisypheMesh]
    _referenceID    str, SisypheVolume ID
    _index          int, index used by iterator methods
    """

    def __init__(self) -> None:
        """
        SisypheMeshCollection instance constructor.
        """
        self._meshes: list[SisypheMesh] = list()
        self._index = 0
        self._referenceID = ''

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheMeshCollection instance to str
        """
        index = 0
        buff = 'SisypheMesh count #{}\n'.format(len(self._meshes))
        for mesh in self._meshes:
            index += 1
            buff += 'SisypheMesh #{}\n'.format(index)
            buff += '{}\n'.format(str(mesh))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheMeshCollection instance representation
        """
        return 'SisypheMeshCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, key: int | str | slice | list[str]) -> SisypheMesh | SisypheMeshCollection:
        """
        Special overloaded container getter method. Get SisypheMesh element from container. Key which can be int index,
        mesh name, slicing indexes (start:stop:step) or list of mesh names.

        Parameters
        ----------
        key : int | str | slice | list[str]
            index, mesh name, slicing indexes (start:stop:step) or list of mesh names

        Returns
        -------
        SisypheMesh | SisypheMeshCollection
            SisypheMeshCollection if key is slice or list[str]
        """
        # key is Name str
        if isinstance(key, str):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._meshes): return self._meshes[key]
            else: raise IndexError('key parameter is out of range.')
        elif isinstance(key, slice):
            meshes = SisypheMeshCollection()
            for i in range(key.start, key.stop, key.step):
                meshes.append(self._meshes[i])
            return meshes
        elif isinstance(key, list):
            meshes = SisypheMeshCollection()
            for i in range(len(self._meshes)):
                if self._meshes[i].getName() in key:
                    meshes.append(self._meshes[i])
            return meshes
        else: raise TypeError('parameter type {} is not int, str, slice or list[str].'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheMesh) -> None:
        """
        Special overloaded container setter method. Set a SisypheMesh element in the container.

        Parameters
        ----------
        key : int
            index
        value : SisypheMesh
            mesh to be placed at key position
        """
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
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheMesh element in the
        container.

        Parameters
        ----------
        key : int | str | SisypheMesh,
            - int, index
            - str, mesh name
            - SisypheMesh, mesh name attribute of the SisypheMesh
        """
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
        """
        Special overloaded method called by the built-in len() python function. Returns the number of SisypheMesh
        elements in the container.

        Returns
        -------
        int
            number of SisypheMesh elements
        """
        return len(self._meshes)

    def __contains__(self, value: str | SisypheMesh) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a SisypheMesh
        is in the container.

        Parameters
        ----------
        value : str | SisypheMesh
            - str, mesh name
            - SisypheMesh, mesh name attribute of the SisypheMesh

        Returns
        -------
        bool
            True if value is in the container.
        """
        keys = [k.getName() for k in self._meshes]
        # value is Name str
        if isinstance(value, str):
            return value in keys
        # value is SisypheMesh
        elif isinstance(value, SisypheMesh):
            return value.getName() in keys
        else: raise TypeError('parameter type {} is not str or SisypheMesh.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> SisypheMesh:
        """
        Special overloaded container called by the built-in 'next()' python iterator method. Returns the next value for
        the iterable.
        """
        if self._index < len(self._meshes):
            n = self._index
            self._index += 1
            return self._meshes[n]
        else:
            raise StopIteration

    def __getattr__(self, name: str):
        """
        Special overloaded method called when attribute does not exist in the class.

        Try iteratively calling the setter or getter methods of the sisypheMesh instances in the container. Getter
        methods return a list of the same size as the container.

        Parameters
        ----------
        name : str
            attribute name of the SisypheMesh class (container element)
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
                    else: raise AttributeError('Not get/set method.'.format(self.__class__, name))
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
        """
        Checks if SisypheMeshCollection instance container is empty.

        Returns
        -------
        bool
            True if empty
        """
        return len(self._meshes) == 0

    def setReferenceID(self, ID: str | SisypheMesh | SisypheVolume) -> None:
        """
        Set reference ID attribute of the current SisypheMeshCollection instance. All meshes in the container are
        defined in the space of a reference SisypheVolume whose ID is the reference ID.

        Parameters
        ----------
        ID : str | SisypheMesh | Sisyphe.core.sisypheVolume.SisypheVolume
            - str, ID
            - SisypheMesh, ID attribute of the SisypheMesh
            - Sisyphe.core.sisypheVolume.SisypheVolume, ID attribute of the SisypheVolume
        """
        if isinstance(ID, SisypheMesh):
            self._referenceID = ID.getReferenceID()
        elif isinstance(ID, SisypheVolume):
            self._referenceID = ID.getID()
        elif isinstance(ID, str):
            self._referenceID = ID
            if not self.isEmpty():
                for mesh in self:
                    mesh.setReferenceID(ID)
        else: raise TypeError('parameter type {} is not SisypheMesh or str'.format(type(ID)))

    def getReferenceID(self) -> str:
        """
        Get reference ID attribute of the current SisypheMeshCollection instance. All meshes in the container are
        defined in the space of a reference SisypheVolume whose ID is the reference ID.

        Returns
        -------
        str
            reference ID
        """
        return self._referenceID

    def hasReferenceID(self) -> bool:
        """
        Check if the reference ID of the current SisypheMeshCollection instance is defined (not empty str).

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._referenceID != ''

    def count(self) -> int:
        """
        Get the number of SisypheMesh elements in the current SisypheMeshCollection instance container.

        Returns
        -------
        int
            number of SisypheMesh elements
        """
        return len(self._meshes)

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current SisypheMeshCollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        return [k.getName() for k in self._meshes]

    def remove(self, value: int | str | SisypheMesh) -> None:
        """
        Remove a SisypheMesh element from the current SisypheMeshCollection instance container.

        Parameters
        ----------
        value : int | str | SisypheMesh
            - int, index of the SisypheMesh to remove
            - str, mesh name of the SisypheMesh to remove
            - SisypheMesh to remove
        """
        # value is SisypheMesh
        if isinstance(value, SisypheMesh):
            self._meshes.remove(value)
        # value is SisypheMesh, Name str or int index
        elif isinstance(value, (str, int)):
            self.pop(value)
        else: raise TypeError('parameter type {} is not int, str or SisypheMesh.'.format(type(value)))

    def pop(self, key: int | str | SisypheMesh | None = None) -> SisypheMesh:
        """
        Remove a SisypheMesh element from the current SisypheMeshCollection instance container and return it. If key is
        None, removes and returns the last element.

        Parameters
        ----------
        key : int | str | SisypheMesh | None
            - int, index of the SisypheMesh to remove
            - str, mesh name of the SisypheMesh to remove
            - SisypheMesh to remove
            - None, remove the last element

        Returns
        -------
        SisypheMesh
            element removed from the container
        """
        if key is None: return self._meshes.pop()
        # key is Name str or SisypheMesh
        if isinstance(key, (str, SisypheMesh)):
            key = self.index(key)
        # key is int index
        if isinstance(key, int):
            return self._meshes.pop(key)
        else: raise TypeError('parameter type {} is not int, str or SisypheMesh.'.format(type(key)))

    def index(self, value: str | SisypheMesh) -> int:
        """
        Index of a SisypheMesh element in the current SisypheMeshCollection instance container.

        Parameters
        ----------
        value : str | SisypheMesh
            mesh name or SisypheMesh

        Returns
        -------
        int
            index
        """
        keys = [k.getName() for k in self._meshes]
        # value is SisypheMesh
        if isinstance(value, SisypheMesh):
            value = value.getName()
        # value is ID str
        if isinstance(value, str):
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheMesh.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current SisypheMeshCollection instance container.
        """
        self._meshes.reverse()

    def append(self, value: SisypheMesh) -> None:
        """
        Append a SisypheMesh element in the current SisypheMeshCollection instance container.

        Parameters
        ----------
        value : SisypheMesh
            mesh to append
        """
        if isinstance(value, SisypheMesh):
            self._verifyID(value)
            if value.getName() not in self: self._meshes.append(value)
            else: self._meshes[self.index(value)] = value
        else: raise TypeError('parameter type {} is not SisypheMesh.'.format(type(value)))

    def insert(self, key: int | str | SisypheMesh, value: SisypheMesh) -> None:
        """
        Insert a SisypheMesh element at the position given by the key in the current SisypheMeshCollection instance
        container.

        Parameters
        ----------
        key : int | str | SisypheMesh
            - int, index
            - str, mesh name index
            - SisypheMesh, mesh index
        value : SisypheMesh
            mesh to insert
        """
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
        """
        Remove all elements from the current SisypheMeshCollection instance container (empty).
        """
        self._meshes.clear()

    def sort(self, reverse: bool = False) -> None:
        """
        Sort elements of the current SisypheMeshCollection instance container. Sorting is based on the name attribute
        of the SisypheMesh elements, in the ascending order.

        Parameters
        ----------
        reverse : bool
            sorting in reverse order
        """
        def _getName(item):
            return item.getName()

        self._meshes.sort(reverse=reverse, key=_getName)

    def copy(self) -> SisypheMeshCollection:
        """
        Copy the current SisypheMeshCollection instance container (Shallow copy of elements).

        Returns
        -------
        SisypheMeshCollection
            SisypheMeshCollection shallow copy
        """
        meshes = SisypheMeshCollection()
        for mesh in self._meshes:
            meshes.append(mesh)
        return meshes

    def copyToList(self) -> list[SisypheMesh]:
        """
        Copy the current SisypheMeshCollection instance container to a list (Shallow copy of elements).

        Returns
        -------
        list[SisypheMesh]
            SisypheMeshCollection shallow copy
        """
        meshes = self._meshes.copy()
        return meshes

    def getList(self) -> list[SisypheMesh]:
        """
        Get the list attribute of the current SisypheMeshCollection instance container (Shallow copy of the elements).

        Returns
        -------
        list[SisypheMesh]
            SisypheMeshCollection shallow copy
        """
        return self._meshes

    # Mesh Public methods

    def setOpacity(self, alpha: float) -> None:
        """
        Set opacity attribute of all the SisypheMesh elements of the current SisypheMeshCollection instance container.

        Parameters
        ----------
        alpha : float
            opacity (between 0.0 and 1.0)
        """
        if isinstance(alpha, float):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setOpacity(alpha)
        else: raise TypeError('parameter type {} is not float.'.format(type(alpha)))

    def setVisibility(self, v: bool) -> None:
        """
        Set visibility attribute of all the SisypheMesh elements  of the current SisypheMeshCollection instance container.

        Parameters
        ----------
        v : bool
            visible if True
        """
        if isinstance(v, bool):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setVisibility(v)
        else: raise TypeError('parameter type is not bool.'.format(type(v)))

    def setVisibilityOn(self) -> None:
        """
        Show all the SisypheMesh elements of the current SisypheMeshCollection instance container.
        """
        self.setVisibility(True)

    def setVisibilityOff(self) -> None:
        """
        Hide all the SisypheMesh elements of the current SisypheMeshCollection instance container.
        """
        self.setVisibility(False)

    def setAmbient(self, v: float) -> None:
        """
        Set ambient lighting coefficient attribute of all the SisypheMesh elements of the current SisypheMeshCollection
        instance container.

        Parameters
        ----------
        v : float
            ambient lighting coefficient (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setAmbient(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setDiffuse(self, v: float) -> None:
        """
        Set diffuse lighting coefficient attribute of all the SisypheMesh elements of the current SisypheMeshCollection
        instance container.

        Parameters
        ----------
        v : float
            diffuse lighting coefficient (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setDiffuse(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecular(self, v: float) -> None:
        """
        Set specular lighting coefficient attribute of all the SisypheMesh elements of the current
        SisypheMeshCollection instance container.

        Parameters
        ----------
        v : float
            specular lighting coefficient (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setSpecular(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setSpecularPower(self, v: float) -> None:
        """
        Set specular power attribute of all the SisypheMesh elements of the current SisypheMeshCollection instance
        container.

        Parameters
        ----------
        v : float
            specular power (between 0.0 and 50.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 50.0:
                    for mesh in self._meshes:
                        mesh.setSpecularPower(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 50.0.'.format(v))
        else: raise TypeError('parameter type is not float.'.format(type(v)))

    def setMetallic(self, v: float) -> None:
        """
        Set metallic attribute of all the SisypheMesh elements of the current SisypheMeshCollection instance container.

        Parameters
        ----------
        v : float
            metallic (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setMetallic(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setRoughness(self, v: float) -> None:
        """
        Set roughness attribute of all the SisypheMesh elements of the current SisypheMeshCollection instance container.

        Parameters
        ----------
        v : float
            roughness (between 0.0 and 1.0)
        """
        if isinstance(v, float):
            if not self.isEmpty():
                if 0.0 <= v <= 1.0:
                    for mesh in self._meshes:
                        mesh.setRoughness(v)
                else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        else: raise TypeError('parameter type is not float.'.format(type(v)))

    def setFlatRendering(self) -> None:
        """
        Set "Flat" shading interpolation method to render all the SisypheMesh elements of the current
        SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setFlatRendering()

    def setGouraudRendering(self) -> None:
        """
        Set "Gouraud" shading interpolation method to render all the SisypheMesh elements of the current
        SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setGouraudRendering()

    def setPhongRendering(self) -> None:
        """
        Set "Phong" shading interpolation method to render all the SisypheMesh elements of the current
        SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setPhongRendering()

    def setPBRRendering(self) -> None:
        """
        Set "PBR" shading interpolation method to render all the SisypheMesh elements of the current
        SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setPBRRendering()

    def setRenderPointsAsSpheresOn(self) -> None:
        """
        Render mesh points of all the SisypheMesh elements of the current SisypheMeshCollection instance container
        as spheres.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderPointsAsSpheresOn()

    def setRenderPointsAsSpheresOff(self) -> None:
        """
        Stop rendering mesh points of all the SisypheMesh elements of the current SisypheMeshCollection instance
        container as spheres.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderPointsAsSpheresOff()

    def setRenderLinesAsTubesOn(self) -> None:
        """
        Render mesh lines of all the SisypheMesh elements of the current SisypheMeshCollection instance container
        as tubes.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderLinesAsTubesOn()

    def setRenderLinesAsTubesOff(self) -> None:
        """
        Stop rendering mesh lines of all the SisypheMesh elements of the current SisypheMeshCollection instance
        container as tubes.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setRenderLinesAsTubesOff()

    def setEdgeVisibilityOn(self) -> None:
        """
        Show mesh vertex of all the SisypheMesh elements of the current SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setEdgeVisibilityOn()

    def setEdgeVisibilityOff(self) -> None:
        """
        Hide mesh vertex of all the SisypheMesh elements of the current SisypheMeshCollection instance container.
        """
        if not self.isEmpty():
            for mesh in self._meshes:
                mesh.setEdgeVisibilityOff()

    def setLineWidth(self, v: float) -> None:
        """
        Set line width size (mm) of all the SisypheMesh elements of the current SisypheMeshCollection instance
        container.

        Parameters
        ----------
        v : float
            line width in mm
        """
        if isinstance(v, float):
            if not self.isEmpty():
                for mesh in self._meshes:
                    mesh.setLineWidth(v)
        else: raise TypeError('parameter type {} is not float.'.format(type(v)))

    def setPointSize(self, v: float) -> None:
        """
        Set point size (mm) of all the SisypheMesh elements of the current SisypheMeshCollection instance container.

        Parameters
        ----------
        v : float
            point size in mm
        """
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
        """
        Apply an affine geometric transformation to all the SisypheMesh elements of the current SisypheMeshCollection
        instance container. This method performs a resampling of the vtkPolyData points.

        Parameters
        ----------
        trf : SisypheTransform | vtkTransform
            affine geometric transformation
        save : bool
            save resampled SisypheMesh elements (default True)
        dialog : bool
            dialog box to choice file name of each resampled SisypheMesh element (default False)
        prefix : str | None
            prefix added to file name of the resampled SisypheMesh elements (default None)
        suffix : str | None
            suffix added to file name of the resampled SisypheMesh elements (default None)
        wait : DialogWait | None
            progress bar dialog (optional)
        """
        if not self.isEmpty():
            from Sisyphe.core.sisypheTransform import SisypheTransform
            from Sisyphe.core.sisypheTransform import SisypheApplyTransform
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
        """
        Load SisypheMesh elements in the current SisypheMeshCollection instance container from a list of PySisyphe
        Mesh (.xmesh) file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of PySisyphe Mesh (.xmesh) file names
        """
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
        """
        Load SisypheMesh elements in the current SisypheMeshCollection instance container from a list of OBJ (.obj)
        file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of OBJ (.obj) file names
        """
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
        """
        Load SisypheMesh elements in the current SisypheMeshCollection instance container from a list of STL (.stl)
        file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of STL (.stl) file names
        """
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
        """
        Load SisypheMesh elements in the current SisypheMeshCollection instance container from a list of VTK (.vtk)
        file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of VTK (.vtk) file names
        """
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
        """
        Load SisypheMesh elements in the current SisypheMeshCollection instance container from a list of XMLVTK (.vtp)
        file names.

        Parameters
        ----------
        filenames : str | list[str]
            list of XMLVTK (.vtp) file names
        """
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

    def save(self, wait: DialogWait | None = None):
        """
        Iteratively save SisypheMesh elements in the current SisypheMeshCollection instance container.
        """
        n = len(self._meshes)
        if n != 0:
            if wait is not None:
                wait.setProgressRange(0, n)
                wait.progressVisibilityOn()
            for mesh in self._meshes:
                if mesh.hasFilename():
                    if wait is not None:
                        wait.setInformationText('Save {}...'.format(basename(mesh.getFilename())))
                    mesh.save()
