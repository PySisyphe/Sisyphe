"""
    External packages/modules

        Name            Homepage link                                               Usage

        vtk             https://vtk.org/                                            Visualization
"""

from os.path import exists
from os.path import join
from os.path import split
from os.path import splitext

from vtk import vtkOBJReader
from vtk import vtkOBJWriter
from vtk import vtkSTLReader
from vtk import vtkSTLWriter
from vtk import vtkPolyDataReader
from vtk import vtkPolyDataWriter
from vtk import vtkXMLPolyDataReader
from vtk import vtkXMLPolyDataWriter
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper
from vtk import vtkActor

__all__ = ['readMeshFromOBJ',
           'writeMeshToOBJ',
           'readMeshFromSTL',
           'readMeshFromVTK',
           'readMeshFromXMLVTK',
           'writeMeshToSTL',
           'writeMeshToXMLVTK',
           'writeMeshToVTK']

"""
    Functions
    
        readMeshFromOBJ
        readMeshFromSTL
        readMeshFromVTK
        readMeshFromXMLVTK
        readMeshFromJSON
        writeMeshToOBJ
        writeMeshToSTL
        writeMeshToXMLVTK
        writeMeshToVTK

    Creation: 02/11/2022      
    Revisions:
    
        01/09/2023  type hinting
"""


def readMeshFromOBJ(filename: str) -> vtkActor:
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == '.obj':
            r = vtkOBJReader()
            r.SetFileName(filename)
            r.Update()
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(r.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            return actor
        else: raise IOError('{} is not a OBJ file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readMeshFromSTL(filename: str) -> vtkActor:
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == '.stl':
            r = vtkSTLReader()
            r.SetFileName(filename)
            r.Update()
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(r.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            mapper.ScalarVisibilityOff()
            return actor
        else: raise IOError('{} is not a STL file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readMeshFromVTK(filename: str) -> vtkActor:
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == '.vtk':
            r = vtkPolyDataReader()
            r.SetFileName(filename)
            r.Update()
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(r.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            mapper.ScalarVisibilityOff()
            return actor
        else: raise IOError('{} is not a VTK file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def readMeshFromXMLVTK(filename: str) -> vtkActor:
    if exists(filename):
        path, ext = splitext(filename)
        ext = ext.lower()
        if ext == '.vtp' or ext == '.xmesh':
            r = vtkXMLPolyDataReader()
            r.SetFileName(filename)
            r.Update()
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(r.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            mapper.ScalarVisibilityOff()
            return actor
        else: raise IOError('{} is not a VTK file extension.'.format(ext))
    else: raise IOError('no such file {}.'.format(filename))


def writeMeshToOBJ(data: vtkPolyData | vtkPolyDataMapper | vtkActor, filename: str) -> None:
    if isinstance(data, vtkActor):
        data = data.GetMapper().GetInput()
    elif isinstance(data, vtkPolyDataMapper):
        data = data.GetInput()
    if isinstance(data, vtkPolyData):
        path, name = split(filename)
        if exists(path):
            name = name.lower()
            name, ext = splitext(name)
            name += '.obj'
            filename = join(path, name)
            w = vtkOBJWriter()
            w.SetInputData(data)
            w.SetFileName(filename)
            w.Write()
        else: raise IOError('No such directory {}.'.format(path))
    else: raise TypeError('parameter functype is not vtkActor, vtkPolyDataMapper or vtkPolyData.')


def writeMeshToSTL(data: vtkPolyData | vtkPolyDataMapper | vtkActor, filename: str) -> None:
    if isinstance(data, vtkActor):
        data = data.GetMapper().GetInput()
    elif isinstance(data, vtkPolyDataMapper):
        data = data.GetInput()
    if isinstance(data, vtkPolyData):
        path, name = split(filename)
        name = name.lower()
        name, ext = splitext(name)
        name += '.stl'
        filename = join(path, name)
        w = vtkSTLWriter()
        w.SetInputData(data)
        w.SetFileName(filename)
        w.Write()
    else: raise TypeError('parameter type {} is not vtkActor, vtkPolyDataMapper or vtkPolyData.'.format(type(data)))


def writeMeshToXMLVTK(data: vtkPolyData | vtkPolyDataMapper | vtkActor, filename: str) -> None:
    if isinstance(data, vtkActor):
        data = data.GetMapper().GetInput()
    elif isinstance(data, vtkPolyDataMapper):
        data = data.GetInput()
    if isinstance(data, vtkPolyData):
        path, name = split(filename)
        name = name.lower()
        name, ext = splitext(name)
        name += '.vtp'
        filename = join(path, name)
        w = vtkXMLPolyDataWriter()
        w.SetInputData(data)
        w.SetFileName(filename)
        w.Write()
    else: raise TypeError('parameter type {} is not vtkActor, vtkPolyDataMapper or vtkPolyData.'.format(type(data)))


def writeMeshToVTK(data: vtkPolyData | vtkPolyDataMapper | vtkActor, filename: str) -> None:
    if isinstance(data, vtkActor):
        data = data.GetMapper().GetInput()
    elif isinstance(data, vtkPolyDataMapper):
        data = data.GetInput()
    if isinstance(data, vtkPolyData):
        path, name = split(filename)
        name = name.lower()
        name, ext = splitext(name)
        name += '.vtk'
        filename = join(path, name)
        w = vtkPolyDataWriter()
        w.SetInputData(data)
        w.SetFileName(filename)
        w.Write()
    else: raise TypeError('parameter type {} is not vtkActor, vtkPolyDataMapper or vtkPolyData.'.format(type(data)))
