"""
    External packages/modules

        Name            Link                                                        Usage

        DIPY            https://www.dipy.org/                                       MR diffusion image processing
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        scipy           https://scipy.org/                                          Scientific computing
        vtk             https://vtk.org/                                            Visualization engine
"""

from __future__ import annotations
from typing import Callable

import os
from os import getcwd
from os.path import dirname
from os.path import basename
from os.path import join
from os.path import splitext

import cython

from math import sqrt

from xml.dom import minidom

from dipy.data import default_sphere
from dipy.data import small_sphere
from dipy.io.streamline import load_tck
from dipy.io.streamline import load_trk
from dipy.io.streamline import load_vtk
from dipy.io.streamline import load_vtp
from dipy.io.streamline import load_fib
from dipy.io.streamline import load_dpy
from dipy.io.streamline import save_tck
from dipy.io.streamline import save_trk
from dipy.io.streamline import save_vtk
from dipy.io.streamline import save_vtp
from dipy.io.streamline import save_fib
from dipy.io.streamline import save_dpy
from dipy.io.utils import create_tractogram_header
from dipy.io.stateful_tractogram import Origin
from dipy.io.stateful_tractogram import Space
from dipy.io.stateful_tractogram import StatefulTractogram
from dipy.tracking import Streamlines
from dipy.tracking.metrics import inside_sphere
from dipy.tracking.metrics import intersect_sphere
from dipy.tracking.metrics import length
from dipy.tracking.metrics import mean_curvature
from dipy.tracking.metrics import midpoint
from dipy.tracking.metrics import midpoint2point
from dipy.tracking.metrics import center_of_mass
from dipy.tracking.metrics import longest_track_bundle
from dipy.tracking.metrics import arbitrarypoint
from dipy.tracking.metrics import principal_components
from dipy.tracking.metrics import set_number_of_points
from dipy.tracking.distances import minimum_closest_distance
from dipy.tracking.distances import bundles_distances_mam
from dipy.tracking.distances import bundles_distances_mdf
from dipy.tracking.streamlinespeed import compress_streamlines
from dipy.tracking.streamline import values_from_volume
from dipy.tracking.streamline import cluster_confidence
from dipy.tracking.streamline import select_by_rois
from dipy.tracking.streamline import unlist_streamlines
from dipy.tracking.streamline import relist_streamlines
from dipy.tracking.streamline import transform_streamlines
from dipy.tracking.utils import density_map
from dipy.tracking.utils import path_length
from dipy.tracking.utils import connectivity_matrix
from dipy.segment.bundles import qbx_and_merge
from dipy.segment.bundles import cluster_bundle
from dipy.segment.bundles import RecoBundles
from dipy.segment.clustering import QuickBundles
from dipy.segment.featurespeed import ResampleFeature
from dipy.segment.featurespeed import CenterOfMassFeature
from dipy.segment.featurespeed import MidpointFeature
from dipy.segment.featurespeed import ArcLengthFeature
from dipy.segment.featurespeed import VectorOfEndpointsFeature
from dipy.segment.metric import EuclideanMetric
from dipy.segment.metric import CosineMetric
from dipy.segment.metric import AveragePointwiseEuclideanMetric
from dipy.core.gradients import gradient_table
from dipy.core.gradients import GradientTable
from dipy.core.gradients import reorient_bvecs
from dipy.direction import BootDirectionGetter
from dipy.direction import ClosestPeakDirectionGetter
from dipy.direction import DeterministicMaximumDirectionGetter
from dipy.direction import ProbabilisticDirectionGetter
from dipy.reconst.dti import TensorModel
from dipy.reconst.dti import TensorFit
from dipy.reconst.dti import isotropic
from dipy.reconst.dti import deviatoric
from dipy.reconst.dki import DiffusionKurtosisModel
from dipy.reconst.dki import DiffusionKurtosisFit
from dipy.reconst.dsi import DiffusionSpectrumModel
from dipy.reconst.dsi import DiffusionSpectrumFit
from dipy.reconst.dsi import DiffusionSpectrumDeconvModel
from dipy.reconst.dsi import DiffusionSpectrumDeconvFit
from dipy.reconst.shm import CsaOdfModel
from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel
from dipy.reconst.csdeconv import auto_response_ssst
from dipy.direction import peaks_from_model
from dipy.tracking.utils import seeds_from_mask
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import ActStoppingCriterion
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion

from numpy import array
from numpy import eye
from numpy import ones
from numpy import diag
from numpy import ndarray
from numpy import all as npall
from numpy import absolute
from numpy import frombuffer
from numpy import histogram
from numpy import percentile

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from scipy.stats import describe

from vtk import vtkActor
from vtk import vtkPoints
from vtk import vtkPolyLineSource
from vtk import vtkLookupTable
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper

from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheTransform import SisypheTransform
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheTract',
           'SisypheTractCollection',
           'SisypheBundle',
           'SisypheBundleCollection',
           'SisypheStreamlines',
           'SisypheDiffusionModel',
           'SisypheDTIModel',
           'SisypheDKIModel',
           'SisypheSHCSAModel',
           'SisypheSHCSDModel',
           'SisypheDSIModel',
           'SisypheDSIDModel']

"""
    Class hierarchy

        object  -> SisypheTract
                -> SisypheTractCollection
                -> SisypheBundle
                -> SisypheBundleCollection
                -> SisypheStreamlines
                -> SisypheDiffusionModel -> SisypheDTIModel 
                                         -> SisypheDKIModel 
                                         -> SisypheSHCSAModel
                                         -> SisypheSHCSDModel
                                         -> SisypheDSIModel
                                         -> SisypheDSIDModel
"""

vector3float = list[float, float, float] | tuple[float, float, float]
vector3int = list[int, int, int] | tuple[int, int, int]


class SisypheTract(object):
    """
        SisypheTract Class

        Inheritance

            object -> SisypheTract

        Private attributes

            _lut            SisypheLut, bundle colormap
            _polyline       vtkPolylineSource
            _polydata       vtkPolyData
            _mapper         vtkPolyDataMapper
            _actor          vtkActor
            _scalarnames    dict[str: bool]

        Public methods

            isEmpty() -> bool
            setPoints(sl: ndarray)
            setScalarsFromVolume(vol: SisypheVolume)
            setFloatColor(c: vector3float)
            setIntColor(c: vector3int)
            setQColor(c: QColor)
            getFloatColor() -> vector3float
            getIntColor() -> vector3int
            getQColor() -> QColor
            setLut(lut: SisypheVolume | SisypheLut | vtkLookupTable)
            getLut() -> SisypheLut
            setColorRepresentation(r: int)
            getColorRepresentation() -> int
            setColorRepresentationAsString(r: str)
            getColorRepresentationAsString() -> str
            setColorRepresentationToRGB()
            setColorRepresentationToScalars()
            setColorRepresentationToColor()
            isRGBRepresentation() -> bool
            isScalarsRepresentation() -> bool
            isColorRepresentation() -> bool
            setActiveScalars(sc: str)
            getActiveScalars() -> str
            getScalarNames() -> list[str]
            getPolyData() -> vtkPolyData
            getActor() -> vtkActor
            getPoints() -> ndarray
            getVisibility() -> bool
            setVisibility(v: bool)
            visibilityOn()
            visibilityOff()
            getOpacity() -> float
            setOpacity(v: float)
            getLineWidth() -> float
            setLineWidth(v: float)

        Creation: 26/10/2023
        Revisions:
    """

    __slots__ = ['_array', '_polyline', '_polydata', '_mapper', '_actor', '_scalarnames', '_lut']

    # Class constants

    _RGB = 0
    _CMAP = 1
    _COLOR = 2
    _REPTYPE = (_RGB, _CMAP, _COLOR)

    # Special method

    def __init__(self) -> None:
        super().__init__()

        self._array: ndarray | None = None
        self._polyline = vtkPolylineSource()
        self._polydata: vtkPolyData | None = None
        self._mapper = vtkPolyDataMapper()
        self._actor = vtkActor()
        self._scalarnames: dict[str: bool] = dict()
        self._lut = SisypheLut()
        self._lut.setLutToHot()

    def __str__(self) -> str:
        if self._polydata is None: n = 0
        else: n = self._polydata.GetNumberOfPoints()
        buff = 'Points count: {}\n'.format(n)
        buff += 'Color representation: {}\n'.format(self.getColorRepresentationAsString())
        buff += 'Color: r {0[0]:.2} g {0[1]:.2} b {0[2]:.2}\n'.format(self.getFloarColor())
        buff += 'Scalars:\n'
        for name in self._scalarnames:
            buff += '\t{}\n'.format(name)
        return buff

    def __repr__(self) -> str:
        return 'SisypheBundle instance at <{}>\n'.format(str(id(self))) + self.__str__()

    def __del__(self):
        if self._array is not None:
            del self._array
            del self._polyline
            del self._polydata
            del self._mapper
            del self._actor
            del self._scalarnames
            del self._lut

    # Private method

    def _updatePolydata(self) -> None:
        if self._polydata is not None:
            self._mapper.SetInputData(self._polydata)
            self._mapper.UpdateInformation()
            self._mapper.Update()
            self._actor.SetMapper(self._mapper)

    # Public methods

    def isEmpty(self) -> bool:
        return self._array is None

    def setPoints(self, sl: ndarray) -> None:
        points = vtkPoints()
        points.SetNumberOfPoints(sl.total_nb_rows)
        scalars = vtkCharArray()
        scalars.SetNumberOfComponents(3)
        scalars.SetNumberOfTuples(sl.total_nb_rows)
        scalars.SetName('RGB')
        self._scalarnames = dict()
        self._scalarnames['RGB'] = True
        i: cython.int
        for i in range(sl.total_nb_rows-1):
            cp = sl[i, :]
            np = sl[i+1, :]
            nm = absolute(cp - np)
            nm2 = nm ** 2
            r = (nm / sqrt(nm2.sum())) * 255
            r = r.astype('uint8')
            points.SetPoint(i, tuple(cp))
            scalar.setTuple(i, tuple(r))
        i = sl.total_nb_rows-1
        points.SetPoint(i, tuple(sl[i, :]))
        scalars.SetTuple(i, scalars.GetTuple(i-1))
        self._polyline.SetPoints(points)
        self._polyline.Update()
        self._polydata = self._polyline.GetOutput()
        r = self._polydata.GetProperty()
        r.RenderLinesAsTubesOn()
        r.SetInterpolationToPhong()
        self._polydata.GetPointData().SetScalars(scalars)
        self._polydata.GetPointData().SetActiveScalars('RGB')
        self._mapper.ScalarVisibilityOn()
        self._mapper.SetScalarModeToUsePointData()
        self._mapper.SetColorModeToDirectScalars()
        self._updatePolydata()
        self._array = sl

    def setScalarsFromVolume(self, vol: SisypheVolume) -> None:
        if self._polydata is not None:
            if vol.getName() not in self._scalarnames:
                img = vol.getSITKImage()
                n = self._polydata.GetNumberOfPoints()
                scalars = vtkFloatArray()
                scalars.SetNumberOfComponents(1)
                scalars.SetNumberOfTuples(n)
                scalars.SetName(vol.getBasename())
                for name in self._scalarnames:
                    self._scalarnames[name] = False
                self._scalarnames[vol.getBasename()] = True
                i: cython.int
                for i in range(n):
                    p = points.GetPoint(i)
                    p2 = vol.getVoxelCoordinatesFromWorldCoordinates(p)
                    scalars.SetTuple1(i, float(img[p2[0], p2[1], p2[2]]))
                self._polydata.GetPointData().SetScalars(scalars)
                self._polydata.GetPointData().SetActiveScalars(vol.getBasename())
                self.setLUT(vol.display.getLUT())
                self._updatePolydata()

    def setFloatColor(self, c: vector3float) -> None:
        if self._polydata is not None:
            self._mapper.ScalarVisibilityOff()
            self._mapper.UpdateInformation()
            self._mapper.Update()
            self._actor.GetProperty().SetColor(c[0], c[1], c[2])

    def setIntColor(self, c: vector3int) -> None:
        if self._polydata is not None:
            self.setFloatColor([v / 255.0 for v in c])

    def setQColor(self, c: QColor) -> None:
        if self._polydata is not None:
            self.setFloatColor([c.redF(), c.greenF(), c.blueF()])

    def getFloatColor(self) -> vector3float:
        if self._polydata is not None:
            return self._actor.GetProperty().GetColor()

    def getIntColor(self) -> vector3int:
        if self._polydata is not None:
            color = self._actor.GetProperty().GetColor()
            return [int(c*255) for c in color]

    def getQColor(self) -> QColor:
        if self._polydata is not None:
            color = self._actor.GetProperty().GetColor()
            c = QColor()
            c.setRgbF(color[0], color[1], color[2])
            return c

    def setLut(self, lut: SisypheVolume | SisypheLut | vtkLookupTable) -> None:
        if isinstance(lut, SisypheVolume): lut = lut.display.getVTKLUT()
        if isinstance(lut, SisypheLut): lut = lut.getvtkLookupTable()
        if isinstance(lut, vtkLookupTable):
            self._mapper.SetScalarModeToUsePointData()
            self._mapper.SetColorModeToMapScalars()
            self._mapper.SetLookupTable(lut)
            self._mapper.UseLookupTableScalarRangeOff()
            self._mapper.SetScalarRange(lut.GetRange())
            self._mapper.ScalarVisibilityOn()
            self._mapper.UpdateInformation()
            self._mapper.Update()
        else: raise TypeError('parameter type {} is not vtkLookupTable, SisypheLut or SisypheVolume.'.format(type(lut)))

    def getLut(self) -> SisypheLut:
        return self._lut

    def setColorRepresentation(self, r: int) -> None:
        if r == self._RGB:
            self._mapper.ScalarVisibilityOn()
            self._mapper.SetColorModeToDirectScalars()
            self._mapper.SetScalarModeToUsePointData()
            self._polydata.GetPointData().SetActiveScalars('RGB')
            for name in self._scalarnames:
                self._scalarnames[name] = (name == 'RGB')
        elif r == self._CMAP:
            for name in self._scalarnames:
                if self._scalarnames[name] is True:
                    self._mapper.ScalarVisibilityOn()
                    self._mapper.SetColorModeToMapScalars()
                    self._mapper.SetScalarModeToUsePointData()
                    self._polydata.GetPointData().SetActiveScalars(name)
                    break
        elif r == self._COLOR: self._mapper.ScalarVisibilityOff()
        self._mapper.UpdateInformation()
        self._mapper.Update()

    def getColorRepresentation(self) -> int:
        if self._mapper.GetScalarVisibility() > 0:
            for name in self._scalarnames:
                if self._scalarnames[name] is True:
                    if name == 'RGB': return self._RGB
                    else: return self._CMAP
        else: return self._COLOR

    def setColorRepresentationAsString(self, r: str) -> None:
        r = r.lower()
        if r == 'rgb': self.setColorRepresentation(0)
        elif r == 'scalars': self.setColorRepresentation(1)
        elif r == 'color': self.setColorRepresentation(2)

    def getColorRepresentationAsString(self) -> str:
        r = self.getColorRepresentation()
        if r == 0: return 'rgb'
        elif r == 1: return 'scalars'
        elif r == 2: return 'color'

    def setColorRepresentationToRGB(self) -> None:
        self.setColorRepresentation(self._RGB)

    def setColorRepresentationToScalars(self) -> None:
        self.setColorRepresentation(self._CMAP)

    def setColorRepresentationToColor(self) -> None:
        self.setColorRepresentation(self._COLOR)

    def isRGBRepresentation(self) -> bool:
        return self.getColorRepresentation() == self._RGB

    def isScalarsRepresentation(self) -> bool:
        return self.getColorRepresentation() == self._CMAP

    def isColorRepresentation(self) -> bool:
        return self.getColorRepresentation() == self._COLOR

    def setActiveScalars(self, sc: str) -> None:
        if sc in self.activeScalars:
            for name in self.activeScalars:
                self.activeScalars[name] = (name == sc)
                self._polydata.GetPointData().SetActiveScalars(sc)
        else: raise ValueError('Invalid scalar name.')

    def getActiveScalars(self) -> str:
        for name in self.activeScalars:
            if self.activeScalars[name] is True: return name

    def getScalarNames(self) -> list[str]:
        return list(self._scalarnames.keys())

    def getPolyData(self) -> vtkPolyData:
        return self._polydata

    def getActor(self) -> vtkActor:
        return self._actor

    def getPoints(self) -> ndarray:
        return self._array

    def getVisibility(self) -> bool:
        if self._polydata is not None:
            return self._polydata.GetVisibility() > 0

    def setVisibility(self, v: bool):
        self._polydata.SetVisibility(v)

    def visibilityOn(self) -> None:
        self._polydata.VisibilityOn()

    def visibilityOff(self) -> None:
        self._polydata.VisibilityOff()

    def getOpacity(self) -> float:
        return self._actor.GetProperty().GetOpacity()

    def setOpacity(self, v: float):
        self._actor.GetProperty().SetOpacity(v)

    def getLineWidth(self) -> float:
        return self._actor.GetProperty().GetLineWidth()

    def setLineWidth(self, v: float):
        self._actor.GetProperty().SetLineWidth(v)


class SisypheTractCollection(object):
    """
        SisypheTractCollection Class

        Inheritance

            object -> SisypheTractCollection

        Private attributes

            _index          int
            _list           list[SisypheTract]
            _bundles        SisypheBundleCollection()

        Public methods

            count() -> int
            isEmpty(self) -> bool
            clear()
            copy() -> SisypheTractCollection
            getLists() -> tuple[list[SisypheTract], dict[str: list[int, int]]]
            appendBundle(sl: SisypheStreamlines, bundle: str)
            removeBundle(bundle: str = '')
            setScalarsFromVolume(vol: SisypheVolume)
            getScalarNames() -> list[str]
            setActiveScalars(sc: str, bundle: str = '')
            getActiveScalars(bundle: str = '') -> str
            setFloatColor(c: vector3float, bundle: str = '')
            setIntColor(c: vector3int, bundle: str = '')
            setQColor(c: QColor, bundle: str = '')
            getFloatColor(bundle: str = '') -> vector3float
            getIntColor(bundle: str = '') -> vector3int
            getQColor(bundle: str = '') -> QColor
            setLut(lut: SisypheLut, bundle: str = '')
            getLut(bundle: str = '') -> SisypheLut
            setColorRepresentation(v: int, bundle: str = '')
            getColorRepresentation(bundle: str = '') -> int
            setColorRepresentationAsString(v: str, bundle: str = '')
            getColorRepresentationAsString(bundle: str = '') -> str
            setColorRepresentationToRGB(bundle: str = '')
            setColorRepresentationToScalars(bundle: str = '')
            setColorRepresentationToColor(bundle: str = '')
            isRGBRepresentation(bundle: str = '') -> bool
            isScalarsRepresentation(bundle: str = '') -> bool
            isColorRepresentation(bundle: str = '') -> bool
            setOpacity(v: float, bundle: str = '')
            getOpacity(bundle: str = '') -> float
            setLineWidth(v: float, bundle: str = '')
            getLineWidth(bundle: str = '') -> float
            getVisibility(bundle: str = '')
            setVisibility(v: bool, bundle: str = '')
            visibilityOn(bundle: str = '')
            visibilityOff(bundle: str = '')

        Creation: 26/10/2023
        Revisions:
    """

    __slots__ = ['_index', '_list', '_bundles']

    # Private methods

    def _updateBundles(self, bundle: str):
        if len(self._bundles) > 0:
            if bundle in self._bundles:
                n = self._bundles[bundle][1]
                i0 = self._bundles[bundle][0] + n
                for k in self._bundles:
                    if self._bundles[k][0] > i0:
                        self._bundles[k][0] -= n
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # Special methods

    def __init__(self) -> None:
        self._index: cython.int = 0
        self._list: list[SisypheTract] = list()
        self._bundles: dict[str: list[int, int]] = dict()

    def __str__(self) -> str:
        return 'Tracts count: {}\n'.format(len(self._list))

    def __repr__(self) -> str:
        return 'SisypheTractCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __getitem__(self, key: int) -> SisypheTract:
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._list): return self._list[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(key)))

    def __setitem__(self, key: int, value: SisypheTract) -> None:
        if isinstance(value, SisypheTract):
            if isinstance(key, int):
                if 0 <= key < len(self._list): self._list[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheTract.'.format(type(value)))

    def __delitem__(self, key: int) -> None:
        if 0 <= key < len(self._list): self._list.pop(key)
        else: raise IndexError('parameter is out of range.')

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self):
        self._index: cython.int = 0
        return self

    def __next__(self) -> SisypheTract:
        if self._index < len(self._list):
            n = self._index
            self._index += 1
            return self._list[n]
        else: raise StopIteration

    # Public methods

    def count(self) -> int:
        return len(self._list)

    def isEmpty(self) -> bool:
        return len(self._list) == 0

    def clear(self) -> None:
        self._list = list()
        self._bundles = dict()

    def copy(self) -> SisypheTractCollection:
        r = SisypheTractCollection()
        r._list = self._list.copy()
        r._bundles = self._bundles.copy()
        return r

    def getLists(self) -> tuple[list[SisypheTract], dict[str: list[int, int]]]:
        return self._list, self._bundles

    def appendBundle(self, sl: SisypheStreamlines, bundle: str):
        if bundle not in self._bundles:
            sl = sl.getStreamlinesFromBundle(bundle)
            self._bundles[bundle][0] = len(self._list)
            self._bundles[bundle][1] = sl.total_nb_rows
            c = sl.getFloatColor(bundle)
            lut = sl.getLut(bundle)
            rep = sl.getColorRepresentation(bundle)
            opacity = sl.getopacity(bundle)
            width = sl.getLineWidth(bundle)
            i: cython.int
            for i in range(sl.total_nb_rows):
                tract = SisypheTract()
                tract.setPoints(sl[i])
                tract.setFloatColor(c)
                tract.setLut(lut)
                tract.setColorRepresentation(rep)
                tract.setOpacity(opacity)
                tract.setLineWidth(width)
                self._list.append(tract)
        else: raise ValueError('bundle parameter {} is already in {}'.format(bundle, self.__class__.__name__))

    def removeBundle(self, bundle: str = ''):
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                n = self._bundles[bundle][1]
                i0 = self._bundles[bundle][0] + n - 1
                i1 = i0 - n
                for i in range(i0, i1, -1): del self._list[i]
                self._updateBundles(bundle)
                del self._bundles[bundle]
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    # Representation public methods

    def setScalarsFromVolume(self, vol: SisypheVolume) -> None:
        if len(self._list) > 0:
            i: cython.int
            for i in range(self.count()): self._list[i].setScalarsFromVolume(vol)
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getScalarNames(self) -> list[str]:
        if len(self._list) > 0:
            return self._list[0].getScalarNames()
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setActiveScalars(self, sc: str, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setActiveScalars(sc)
            else: raise ValueError('Invalid scalar name.')
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getActiveScalars(self, bundle: str = '') -> str:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getActiveScalars()
            else: raise ValueError('Invalid scalar name.')
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setFloatColor(self, c: vector3float, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setFloatColor(c)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setIntColor(self, c: vector3int, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setIntColor(c)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setQColor(self, c: QColor, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setQColor(c)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getFloatColor(self, bundle: str = '') -> vector3float:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getFloatColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getIntColor(self, bundle: str = '') -> vector3int:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getIntColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getQColor(self, bundle: str = '') -> QColor:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getQColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setLut(self, lut: SisypheLut, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setLut(lut)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getLut(self, bundle: str = '') -> SisypheLut:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getLut()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentation(self, v: int, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setColorRepresentation(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getColorRepresentation(self, bundle: str = '') -> int:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getColorRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationAsString(self, v: str, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setColorRepresentationAsString(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getColorRepresentationAsString(self, bundle: str = '') -> str:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getColorRepresentationAsString()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationToRGB(self, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setColorRepresentationToRGB()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationToScalars(self, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setColorRepresentationToScalars()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToColor(self, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setColorRepresentationToColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isRGBRepresentation(self, bundle: str = '') -> bool:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].isRGBRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isScalarsRepresentation(self, bundle: str = '') -> bool:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].isScalarsRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isColorRepresentation(self, bundle: str = '') -> bool:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].isColorRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setOpacity(self, v: float, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setOpacity(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getOpacity(self, bundle: str = '') -> float:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getOpacity()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setLineWidth(self, v: float, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setLineWidth(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getLineWidth(self, bundle: str = '') -> float:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getLineWidth()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getVisibility(self, bundle: str = '') -> bool:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i = self._bundles[bundle][0]
                return self._list[i].getVisibility()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setVisibility(self, v: bool, bundle: str = ''):
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].setVisibility(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def visibilityOn(self, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].visibilityOn()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def visibilityOff(self, bundle: str = '') -> None:
        if len(self._list) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                i: cython.int
                i0 = self._bundles[bundle][0]
                i1 = i0 + self._bundles[bundle][1]
                for i in range(i0, i1): self._list[i].visibilityOff()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))


class SisypheBundle(object):
    """
        SisypheBundle Class

        Inheritance

            object -> SisypheBundle

        Private attributes

            _index      int, bundle index
            _name       str, bundle name
            _rep        int, bundle representation (0: RGB, 1: CMAP, 3: COLOR)
            _color      list[float, float, float], bundle color
            _lut        SisypheLut, bundle colormap
            _list       list[int, ], bundle list

        Public methods

            setName(str)
            getName() -> str
            hasName(str) -> bool
            sameName(str | SisypheBundle) -> bool
            count() -> int
            isEmpty() -> bool
            clear() -> bool
            copy() -> SisypheBundle
            copyToList() -> list[int]
            getList() -> list[int]
            addTract(int | list[int, ] | tuple[int, ])
            removeTract(int | list[int, ] | tuple[int, ])
            setFloatColor(c: vector3float)
            setIntColor(c: vector3int)
            setQColor(c: QColor)
            getFloatColor() -> vector3float
            getIntColor() -> vector3int
            getQColor() -> QColor
            setLut(lut: SisypheLut)
            getLut() -> SisypheLut
            setColorRepresentation(v: int)
            getColorRepresentation() -> int
            setColorRepresentationAsString(v: str)
            getColorRepresentationAsString() -> str
            setColorRepresentationToRGB()
            setColorRepresentationToScalars()
            setColorRepresentationToColor()
            isRGBRepresentation() -> bool
            isScalarsRepresentation() -> bool
            isColorRepresentation() -> bool
            setOpacity(v: float)
            getOpacity() -> float
            setLineWidth(v: float)
            getLineWidth() -> float
            union(other: SisypheBundle)
            intersection(other: SisypheBundle)
            difference(other: SisypheBundle)
            symDifference(other: SisypheBundle)

        Creation: 26/10/2023
        Revisions:
    """

    __slots__ = ['_index', '_name', '_color', '_lut', '_rep', '_width', '_opacity', '_list']

    # Class constants

    _RGB = 0
    _CMAP = 1
    _COLOR = 2
    _REPTYPE = (_RGB, _CMAP, _COLOR)

    # Special methods

    def __init__(self, s: vector3int | None = None) -> None:
        """
            s[0], first streamline index
            s[1], streamline count in bundle
            s[2], step (default 1)
        """
        self._index: cython.int = 0
        self._name: str = ''
        self._color: vector3float = [1.0, 1.0, 1.0]
        self._lut = SisypheLut()
        self._lut.setLutToHot()
        self._rep: int = _RGB
        self._width = 1.0
        self._opacity = 1.0
        if s is not None and isinstance(s, vector3int): self._list = list(range(s[0], s[1], s[2]))
        else: self._list: list[int] = list()

    def __str__(self) -> str:
        buff = 'Name: {}\n'.format(self._name)
        buff += '\tTracts count: {}\n'.format(len(self._list))
        buff += '\tRepresentation: {}\n'.format(self.getColorRepresentationAsString())
        r = self.getColorRepresentation()
        if r == _COLOR: buff += '\tColor: {}\n'.format(self.getFloatColor())
        elif r == _CMAP: buff += '\tColormap: {}\n'.format(self._lut.getName())
        return buff

    def __repr__(self) -> str:
        return 'SisypheBundle instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __contains__(self, item: int) -> bool:
        return item in self._list

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self):
        self._index: cython.int = 0
        return self

    def __next__(self) -> int:
        if self._index < len(self._list):
            n = self._index
            self._index += 1
            return self._list[n]
        else: raise StopIteration

    # Special logic operators

    def __and__(self, other: SisypheBundle) -> SisypheBundle:
        r = set(self._list) & set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        return buff

    def __or__(self, other: SisypheBundle) -> SisypheBundle:
        r = set(self._list) | set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        return buff

    def __xor__(self, other: SisypheBundle) -> SisypheBundle:
        r = set(self._list) ^ set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        return buff

    def __sub__(self, other: SisypheBundle) -> SisypheBundle:
        r = set(self._list) - set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        return buff

    def __add__(self, other: SisypheBundle) -> SisypheBundle:
        return self.__or__(other)

    # Public methods

    def setName(self, name: str) -> None:
        self._name = name

    def getName(self) -> str:
        return self._name

    def hasName(self) -> bool:
        return self._name != ''

    def sameName(self, name: str | SisypheBundle) -> bool:
        if isinstance(name, SisypheBundle): name = name.getName()
        if isinstance(name, str): return self._name == name
        else: raise TypeError('parameter value {} is not a str or SisypheBundle.'.format(type(name)))

    def count(self) -> int:
        return len(self._list)

    def isEmpty(self) -> bool:
        return len(self._list) == 0

    def clear(self) -> None:
        self._list = list()

    def copy(self) -> SisypheBundle:
        r = SisypheBundle()
        r._name = self._name
        r._color = self._color
        r._lut = self._lut
        r._rep = self._rep
        r._list = self._list.copy()
        return r

    def copyToList(self) -> list[int]:
        return self._list.copy()

    def getList(self) -> list[int]:
        return self._list

    def appendTracts(self, tract: int | list[int] | tuple[int, ]) -> None:
        if isinstance(tract, int): tract = [tract]
        self._list = list(set(self._list) | set(tract))

    def removeTracts(self, tracts: int | list[int] | tuple[int, ]) -> None:
        if isinstance(tracts, int): tracts = [tracts]
        self._list = list(set(self._list) - set(tracts))

    def setFloatColor(self, c: vector3float) -> None:
        self._color = c

    def setIntColor(self, c: vector3int) -> None:
        self.setFloatColor([v / 255.0 for v in c])

    def setQColor(self, c: QColor) -> None:
        self.setFloatColor([c.redF(), c.greenF(), c.blueF()])

    def getFloatColor(self) -> vector3float:
        return self._color

    def getIntColor(self,) -> vector3int:
        return [int(c*255) for c in self._color]

    def getQColor(self) -> QColor:
        c = QColor()
        c.setRgbF(self._color[0], self._color[1], self._color[2])
        return c

    def setLut(self, lut: SisypheLut) -> None:
        self._lut = lut

    def getLut(self) -> SisypheLut:
        return self._lut

    def setColorRepresentation(self, v: int) -> None:
        if v in self._REPTYPE: self._rep = v
        else: self._rep = self._RGB

    def getColorRepresentation(self) -> int:
        return self._rep

    def setColorRepresentationAsString(self, v: str) -> None:
        v = v.lower()
        if v == 'scalars': self._rep = self._CMAP
        elif v == 'color': self._rep = self._COLOR
        else: self._rep = self._RGB

    def getColorRepresentationAsString(self) -> str:
        if self._rep == self._RGB: return 'rgb'
        elif self._rep == self._CMAP: return 'scalars'
        elif self._rep == self._COLOR: return 'color'

    def setColorRepresentationToRGB(self) -> None:
        self._rep = self._RGB

    def setColorRepresentationToScalars(self) -> None:
        self._rep = self._CMAP

    def setColorRepresentationToColor(self) -> None:
        self._rep = self._COLOR

    def isRGBRepresentation(self) -> bool:
        return self._rep == self._RGB

    def isScalarsRepresentation(self) -> bool:
        return self._rep == self._CMAP

    def isColorRepresentation(self) -> bool:
        return self._rep == self._COLOR

    def setOpacity(self, v: float) -> None:
        self._opacity = v

    def getOpacity(self) -> float:
        return self._opacity

    def setLineWidth(self, v: float) -> None:
        self._width = v

    def getLineWidth(self) -> float:
        return self._width

    # Public set operators

    def union(self, other: SisypheBundle) -> None:
        self._list = list(set(self._list) | set(other._list))

    def intersection(self, other: SisypheBundle) -> None:
        self._list = list(set(self._list) & set(other._list))

    def difference(self, other: SisypheBundle) -> None:
        self._list = list(set(self._list) - set(other._list))

    def symDifference(self, other: SisypheBundle) -> None:
        self._list = list(set(self._list) ^ set(other._list))


class SisypheBundleCollection(object):
    """
        SisypheBundle Class

        Inheritance

            object -> SisypheBundle

        Private attributes

            _index      int, SisypheBundle index
            _list       list[SisypheBundle, ], SisypheBundle list

        Public methods

            count() -> int
            isEmpty() -> bool
            clear()
            remove(value: str | int | SisypheBundle)
            pop(key: str | int | SisypheBundle | None = None)
            keys() -> list[str]
            index(value: str | SisypheBundle) -> int
            reverse()
            append(value: SisypheBundle)
            insert(key: int | str | SisypheBundle, value: SisypheBundle)
            sort(reverse: bool = False)
            copy() -> SisypheBundleCollection
            copyToList() -> list[SisypheBundle, ]
            getList() -> list[SisypheBundle, ]
            union(names: list[str, ], newname: str)
            intersection(names: list[str, ], newname: str)
            difference(names: list[str, ], newname: str)
            symDifference(names: list[str, ], newname: str)

        Creation: 26/10/2023
        Revisions:
    """

    __slots__ = ['_index', '_list']

    # Special methods

    def __init__(self) -> None:
        self._index: cython.int = 0
        self._list: list[SisypheBundle] = list()

    def __str__(self) -> str:
        n = len(self._list)
        buff = 'Bundles count: {}\n'.format(n)
        if n > 0:
            for item in self._list:
                buff += '\t{}\t{} tracts\n'.format(str(item), item.count())
        return buff

    def __repr__(self) -> str:
        return 'SisypheBundleCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container operators

    def __getitem__(self, key: str | int) -> SisypheBundle:
        # key is str
        if isinstance(key, str): key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._list): return self._list[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: str | int, value: SisypheBundle) -> None:
        if isinstance(value, SisypheBundle):
            # key is int index
            if isinstance(key, str): key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._list): self._list[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheBundle.'.format(type(value)))

    def __delitem__(self, key: str | int | SisypheBundle) -> None:
        if isinstance(key, SisypheBundle): key = key.getName()
        if isinstance(key, str): key = self.index(key)
        if isinstance(key, int): self._list.pop(key)

    def __contains__(self, item: SisypheBundle | str) -> bool:
        if isinstance(item, SisypheBundle): item = item.getName()
        if isinstance(item, str): return item in self.keys()

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self):
        self._index: cython.int = 0
        return self

    def __next__(self) -> SisypheBundle:
        if self._index < len(self._list):
            n = self._index
            self._index += 1
            return self._list[n]
        else: raise StopIteration

    # Public methods

    def count(self) -> int:
        return len(self._list)

    def isEmpty(self) -> bool:
        return len(self._list) == 0

    def clear(self) -> None:
        self._list = list()

    def remove(self, value: str | int | SisypheBundle) -> None:
        # value is SisypheBundle
        if isinstance(value, SisypheBundle): self._list.remove(value)
        # value is str or int
        elif isinstance(value, (str, int)): self.pop(self.index(value))
        else: raise TypeError('parameter type {} is not int, str or SisypheBundle.'.format(type(value)))

    def pop(self, key: str | int | SisypheBundle | None = None) -> SisypheBundle:
        if key is None: return self._list.pop()
        # key is SisypheVolume arrayID str
        if isinstance(key, (str, SisypheBundle)): key = self.index(key)
        # key is int index
        if isinstance(key, int): return self._list.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def keys(self) -> list[str]:
        return [k.getName() for k in self._list]

    def index(self, value: str | SisypheBundle) -> int:
        keys = [k.getName() for k in self._list]
        # value is SisypheBundle
        if isinstance(value, SisypheBundle): value = value.getName()
        # value is str
        if isinstance(value, str): return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheBundle.'.format(type(value)))

    def reverse(self) -> None:
        self._list.reverse()

    def append(self, value: SisypheBundle) -> None:
        if isinstance(value, SisypheBundle):
            if value.getName() not in self: self._list.append(value)
        else: raise TypeError('parameter type {} is not SisypheBundle.'.format(type(value)))

    def insert(self, key: int | str | SisypheBundle, value: SisypheBundle) -> None:
        if isinstance(value, SisypheBundle):
            # value is SisypheBundle
            if isinstance(key, SisypheBundle): key = key.getName()
            # value is str
            if isinstance(key, str): key = self.index(key)
            # key is int index
            if isinstance(key, int):
                if 0 <= key < len(self._list):
                    if value.getName() not in self._list: self._list.insert(key, value)
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int, str or SisypheBundle.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheBundle.'.format(type(value)))

    def sort(self, reverse: bool = False) -> None:
        def _getName(item):
            return item.getName()

        self._volumes.sort(reverse=reverse, key=_getName)

    def copy(self) -> SisypheBundleCollection:
        bundle = SisypheBundleCollection()
        for item in self._list:
            bundle.append(item)
        return bundle

    def copyToList(self) -> list[SisypheBundle]:
        return self._list.copy()

    def getList(self) -> list[SisypheBundle]:
        return self._list

    # Public set operators

    def union(self, names: list[str, ], newname: str) -> None:
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.union(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def intersection(self, names: list[str, ], newname: str) -> None:
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.intersection(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def difference(self, names: list[str, ], newname: str) -> None:
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.difference(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def symDifference(self, names: list[str, ], newname: str) -> None:
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.symDifference(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))


class SisypheStreamlines(object):
    """
        SisypheTracts Class

        Inheritance

            object -> SisypheTracts

        Private attributes

            _streamlines    Streamlines
            _bundles        SisypheBundleCollection
            _ID             str
            _dirname        str
            _regstep        bool, True if step is constant

        Public methods

            getReferenceID() -> str
            setReferenceID(ID: str | SisypheVolume)
            hasReferenceID() -> bool
            getDirname() -> str
            getFilename(bundle: str = 'all') -> str
            isEmpty() -> bool
            count()
            hasRegularStep() -> bool
            append(self, sl: ndarray | Streamlines, bundlename: str = '')
            setFloatColor(c: vector3float, bundle: str = 'all')
            setIntColor(c: vector3int, bundle: str = 'all')
            setQColor(c: QColor, bundle: str = 'all')
            getFloatColor(bundle: str = 'all') -> vector3float
            getIntColor(bundle: str = 'all') -> vector3int
            getQColor(bundle: str = 'all') -> QColor
            setLut(lut: SisypheLut, bundle: str = 'all')
            getLut(bundle: str = 'all') -> SisypheLut
            setColorRepresentation(v: int, bundle: str = 'all')
            getColorRepresentation(bundle: str = 'all') -> int
            setColorRepresentationAsString(v: str, bundle: str = 'all')
            getColorRepresentationAsString(bundle: str = 'all') -> str
            setColorRepresentationToRGB(bundle: str = 'all')
            setColorRepresentationToScalars(bundle: str = 'all')
            setColorRepresentationToColor(bundle: str = 'all')
            isRGBRepresentation(bundle: str = 'all') -> bool
            isScalarsRepresentation(bundle: str = 'all') -> bool
            isColorRepresentation(bundle: str = 'all') -> bool
            setOpacity(v: float, bundle: str = 'all')
            getOpacity(bundle: str = 'all') -> float
            setLineWidth(v: float, bundle: str = 'all')
            getLineWidth(bundle: str = 'all')
            getStreamlinesFromBundle(bundle: str = 'all') -> Streamlines
            getSisypheStreamlinesFromBundle(bundle: str) -> SisypheStreamlines
            isTractInsideSphere(index: int, p: vector3float, radius: float) -> bool
            isTractIntersectSphere(index: int, p: vector3float, radius: float) -> bool
            tractLength(index: int) -> float
            tractMeanCurvature(index: int) -> float
            tractCenterOfMass(index: int) -> vector3float
            tractPrincipalDirection(index: int) -> vector3float
            tractMidPoint(index: int) -> vector3float
            tractFirstPoint(index: int) -> vector3float
            tractLastPoint(index: int) -> vector3float
            tractDistanceToMidPoint(index: int, p: vector3float) -> float
            tractPointIndex(index: int, p: vector3float) -> int
            tractPointFromDistance(index: int, d: float, percent: bool = False) -> vector3float
            tractPointIndexFromDistance(index: int, d: float, percent: bool = False) -> int
            minimumClosestDistanceBetweenTracts(index1: int, index2: int) -> float
            tractScalarsFromVolume(index: int, vol: SisypheVolume) -> ndarray
            tractScalarStatisticsFromVolume(index: int, vol: SisypheVolume) -> dict[str: float]
            tractScalarHistogramFromVolume(index: int,  vol: SisypheVolume, bins: int = 10) -> ndarray
            tractsInsideSphere(p: vector3float, radius: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle
            tractsIntersectSphere(p: vector3float, radius: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle
            bundleLengths(bundle: str = 'all') -> list[float]
            bundleLengthStatistics(bundle: str = 'all') -> dict[str: float]
            bundleMeanCurvatures(bundle: str = 'all') -> list[float]
            bundleMeanCurvatureStatistics(bundle: str = 'all') -> dict[str: float]
            bundleCentersOfMass(bundle: str = 'all') -> list[vector3float]
            bundleScalarStatisticsFromVolume(vol: SisypheVolume, bundle: str = 'all') -> dict[str: float]
            bundleScalarHistogramFromVolume(vol: SisypheVolume, bins: int = 10,  bundle: str = 'all') -> ndarray
            getTractsSortedByLength(bundle: str = 'all') -> list[int]
            getLongestTractIndex(bundle: str = 'all') -> int
            getShortestTractIndex(bundle: str = 'all') -> int
            removeTractsShorterThan(l: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle
            removeTractsLongerThan(l: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle
            bundleRoiSelection(rois: SisypheROICollection,
                               include: list[bool] | None = None,
                               mode: str = 'any',
                               bundle: str = 'all') -> SisypheBundle
            bundleClusterConfidence(mdf: int = 5,
                                    subsample: int = 12,
                                    power: int = 1,
                                    ccithreshold: float = 1.0,
                                    bundle: str = 'all') -> tuple[SisypheBundle, ndarray]
            bundleCentroidClustering(threshold: float = 10.0, bundle: str = 'all') -> Streamlines
            bundleCentroidDistanceSelection(centroid: ndarray,
                                            dist: str = 'mam',
                                            threshold: float = 10.0,
                                            bundle: str = 'all') -> SisypheBundle
            bundleClustering(threshold: float | None = None,
                             nbp: int = 12,
                             metric: str = 'mdf',
                             minclustersize: int = 10,
                             bundle: str = 'all') -> tuple[SisypheBundleCollection, Streamlines]
            bundleFastClustering(threshold: float = 10.0,
                                 minsize: int = 10,
                                 bundle: str = 'all') -> tuple[SisypheBundleCollection, Streamlines]
            bundleFromBundleModel(slmodel: Streamlines,
                                  threshold: float = 15.0,
                                  reduction: float = 10.0,
                                  pruning: float = 5.0,
                                  reductiondist: str = 'mam',
                                  pruningdist: str = 'mam',
                                  refine: bool = False,
                                  minlength: int = 50,
                                  bundle: str = 'all') -> SisypheBundle
            bundleToRoi(vol: SisypheVolume,
                        threshold: int = 10,
                        perc: bool = False,
                        bundle: str = 'all') -> SisypheROI
            bundleToMesh(vol: SisypheVolume,
                         threshold: int,
                         perc: bool = False,
                         fill: float = 1000.0,
                         decimate: float = 1.0,
                         clean: bool = False,
                         smooth: str = 'sinc',
                         niter: int = 10,
                         factor: float = 0.1,
                         algo: str = 'flying',
                         largest: bool = False,
                         bundle: str = 'all') -> SisypheMesh
            bundleToDensityMap(vol: SisypheVolume, bundle: str = 'all') -> SisypheVolume
            bundleToPathLengthMap(vol: SisypheVolume, roi: SisypheROI, bundle: str = 'all') -> SisypheVolume
            bundleToConnectivityMatrix(vol: SisypheVolume, bundle: str = 'all') -> ndarray
            addBundleToSisypheTractCollection(tracts: SisypheTractCollection | None = None, bundle: str = 'all')
            compressStreamlines(maxlength: float = 10, inplace: bool = False) -> Streamlines
            changeStreamlinesSampling(factor: float, inplace: bool = False) -> Streamlines
            changeStreamlinesStepSize(step: float, inplace: bool = False) -> Streamlines
            applyTransformToStreamlines(trf: SisypheTransform, inplace: bool = False) -> Streamlines
            streamlinesToDensityMap(vol: SisypheVolume) -> SisypheVolume
            streamlinesToPathLengthMap(vol: SisypheVolume, roi: SisypheROI) -> SisypheVolume
            streamlinesToConnectivityMatrix(vol: SisypheVolume) -> ndarray
            streamlinesRoiSelection(rois: SisypheROICollection,
                                    include: list[bool] | None = None,
                                    mode: str = 'any') -> SisypheStreamlines
            save(bundle: str)
            saveToNumpy(bundle: str)
            saveToTck(bundle: str)
            saveToTrk(bundle: str)
            saveToVtk(bundle: str)
            saveToVtp(bundle: str)
            saveToFib(bundle: str)
            saveToDpy(bundle: str)
            load(bundle: str)
            loadToNumpy(bundle: str)
            loadToTck(bundle: str)
            loadToTrk(bundle: str)
            loadToVtk(bundle: str)
            loadToVtp(bundle: str)
            loadToFib(bundle: str)
            loadToDpy(bundle: str)

        Creation: 26/10/2023
        Revisions:
    """

    __slots__ = ['_index', '_ID', '_bundles', '_streamlines', '_regstep', '_dirname']

    # Class constants

    _FILEEXT = '.xtracts'
    TRK, TCK, VTK, VTP, FIB, NPZ, DPY = '.trk', '.tck', '.vtk', '.vtp', '.fib', '.npz', '.dpy'
    _TRACTSEXT = [_FILEEXT, TRK, TCK, VTK, VTP, FIB, NPZ, DPY]

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Tractogram (*{})'.format(cls._FILEEXT)

    # Special methods

    def __init__(self, sl: Streamlines | None = None, compress=False) -> None:
        self._index: cython.int = 0
        self._ID = None
        self._regstep = True
        if sl is not None and isinstance(sl, Streamlines):
            if compress:
                sl = compress_streamlines(sl)
                self._regstep = False
            self._streamlines = sl
            bundle = SisypheBundle((0, sl.total_nb_rows, 1))
        else:
            self._streamlines = Streamlines()
            bundle = SisypheBundle()
        bundle.setName('all')
        self._bundles = SisypheBundleCollection()
        self._bundles.append(bundle)
        self._dirname = getcwd()

    def __str__(self) -> str:
        buff = 'Global tract count: {}\n'.format(self._streamlines.total_nb_rows)
        buff += 'reference ID: {}\n'.format(str(self._ID))
        buff += 'Regular step: {}\n'.format(str(self._regstep))
        for bundle in self._bundles:
            buff = 'Bundle: {}\n'.format(bundle.getName())
            buff += '\tTract count: {}\n'.format(bundle.count())
            buff += '\tRepresentation: {}\n'.format(self.getColorRepresentationAsString(bundle.getName()))
            r = self.getColorRepresentation()
            if r == 1:
                buff += '\tColormap: {}\n'.format(self._lut.getName(bundle.getName()))
            elif r == 2: buff += '\tColor: {}\n'.format(self.getFloatColor(bundle.getName()))
            buff += '\tOpacity: {}\n'.format(self.getOpacity(bundle.getName()))
            buff += '\tLine width: {}\n'.format(self.getLineWidth(bundle.getName()))
        return buff

    def __repr__(self) -> str:
        return 'SisypheStreamlines instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __len__(self) -> int:
        return self._streamlines.total_nb_rows

    def __iter__(self):
        self._index: cython.int = 0
        return self

    def __next__(self) -> Streamlines:
        if self._index < self._streamlines.total_nb_rows:
            n = self._index
            self._index += 1
            return self._streamlines[n]
        else: raise StopIteration

    # Private methods

    def _load(self, filename: str, loadfunc: Callable) -> None:
        hdr = create_tractogram_header('.trk',
                                       affine=eye(4, 4),
                                       dimensions=(256, 256, 256),
                                       voxel_sizes=(1.0, 1.0, 1.0),
                                       voxel_order=b'RAS')
        tractogram = loadfunc(filename,
                              reference=hdr,
                              to_space=Space.RASMM,
                              to_origin=Origin.TRACKVIS)
        self._streamlines = tractogram.streamlines()
        bundle = SisypheBundle((0, self._streamlines.total_nb_rows, 1))
        bundle.setName(splitext(basename(filename))[0])
        self._bundles = SisypheBundleCollection()
        self._bundles.append(bundle)
        self._dirname = dirname(filename)

    def _save(self, bundle: str, savefunc: Callable) -> None:
        hdr = create_tractogram_header('.trk',
                                       affine=eye(4, 4),
                                       dimensions=(256, 256, 256),
                                       voxel_sizes=(1.0, 1.0, 1.0),
                                       voxel_order=b'RAS')
        tractogram = StatefulTractogram(self.getStreamlinesFromBundle(bundle),
                                        reference=hdr,
                                        space=Space.RASMM,
                                        origin=Origin.TRACKVIS)
        filename = join(self._dirname, bundle)
        savefunc(tractogram, filename)

    # Public methods

    def getReferenceID(self) -> str:
        return self._ID

    def setReferenceID(self, ID: str | SisypheVolume) -> None:
        if isinstance(ID, SisypheVolume):
            self._dirname = ID.getDirname()
            ID = ID.getID()
        if isinstance(ID, str): self._ID = ID
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def hasReferenceID(self) -> bool:
        return self._ID is not None

    def getDirname(self) -> str:
        return self._dirname

    def getFilename(self, bundle: str = 'all') -> str:
        if bundle not in self._bundles: bundle = 'all'
        if bundle == 'all': bundle = self._bundles[0].getName()
        return join(self._dirname, bundle + self.getFilterExt())

    def isEmpty(self) -> bool:
        return self._streamlines.total_nb_rows == 0

    def count(self) -> int:
        return self._streamlines.total_nb_rows

    def hasRegularStep(self):
        return self._regstep is True

    def append(self, sl: ndarray | Streamlines, bundlename: str = '') -> None:
        n = self._bundles[0].count()
        if isinstance(sl, ndarray):
            if sl.ndim == 2 and sl.shape[1] == 3:
                self._streamlines.append(sl)
                self._bundles[0].appendTracts(n)
        elif isinstance(sl, Streamlines):
            self._streamlines.extend(sl)
            tracts = list(range(n, n + sl.total_nb_rows, 1))
            self._bundles[0].appendTracts(tracts)
            if bundlename != '':
                if bundlename in self._bundles:
                    buff = bundlename.split(' ')
                    suffix = buff[-1]
                    if suffix[0] == '#' and suffix[1:].isnumeric():
                        suffix = '#{}'.format(int(suffix[1:])+1)
                        buff = buff[:-1] + [suffix]
                        bundlename = ' '.join(buff)
                    else: bundlename += ' #1'
                bundle = SisypheBundle(tracts)
                bundle.setName(bundlename)
                self._bundles.append(bundle)
        else: raise TypeError('parameter type {} is not ndarray or Streamlines.'.format(type(sl)))

    def setFloatColor(self, c: vector3float, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setFloatColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setIntColor(self, c: vector3int, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setIntColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setQColor(self, c: QColor, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setQColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getFloatColor(self, bundle: str = 'all') -> vector3float:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getFloatColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getIntColor(self, bundle: str = 'all') -> vector3int:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getIntColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getQColor(self, bundle: str = 'all') -> QColor:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getQColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setLut(self, lut: SisypheLut, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setLut(lut)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getLut(self, bundle: str = 'all') -> SisypheLut:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getLut()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentation(self, v: int, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentation(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getColorRepresentation(self, bundle: str = 'all') -> int:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getColorRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationAsString(self, v: str, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationAsString(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getColorRepresentationAsString(self, bundle: str = 'all') -> str:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getColorRepresentationAsString()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToRGB(self, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToRGB()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToScalars(self, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToScalars()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToColor(self, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isRGBRepresentation(self, bundle: str = 'all') -> bool:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isRGBRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isScalarsRepresentation(self, bundle: str = 'all') -> bool:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isScalarsRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isColorRepresentation(self, bundle: str = 'all') -> bool:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isColorRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setOpacity(self, v: float, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].setOpacity(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getOpacity(self, bundle: str = 'all') -> float:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getOpacity()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setLineWidth(self, v: float, bundle: str = 'all') -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].setLineWidth(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getLineWidth(self, bundle: str = 'all') -> float:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getLineWidth()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getStreamlinesFromBundle(self, bundle: str = 'all') -> Streamlines:
        if bundle == 'all': return self._streamlines
        elif bundle in self._bundles:
            return self._streamlines[self._bundles[bundle].getList()]

    def getSisypheStreamlinesFromBundle(self, bundle: str) -> SisypheStreamlines:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            return SisypheStreamlines(sl=sl)

    # Public tract ndarray processing methods

    def isTractInsideSphere(self, index: int, p: vector3float, radius: float) -> bool:
        if 0 <= index < self._streamlines.total_nb_rows:
            if self._regstep: return inside_sphere(self._streamlines[index], p, radius)
            else: return intersect_sphere(self._streamlines[index], p, radius)
        else: raise ValueError('index parameter is out of range.')

    def isTractIntersectSphere(self, index: int, p: vector3float, radius: float) -> bool:
        if 0 <= index < self._streamlines.total_nb_rows:
            return intersect_sphere(self._streamlines[index], p, radius)
        else: raise ValueError('index parameter is out of range.')

    def tractLength(self, index: int) -> float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return length(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def tractMeanCurvature(self, index: int) -> float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return mean_curvature(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def tractCenterOfMass(self, index: int) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return center_of_mass(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def tractPrincipalDirection(self, index: int) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            va, ve = principal_components(self._streamlines[index])
            return list(ve[va.argmax()])
        else: raise ValueError('index parameter is out of range.')

    def tractMidPoint(self, index: int) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return list(midpoint(self._streamlines[index]))
        else: raise ValueError('index parameter is out of range.')

    def tractFirstPoint(self, index: int) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return self._streamlines[index][0]
        else: raise ValueError('index parameter is out of range.')

    def tractLastPoint(self, index: int) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return self._streamlines[index][-1]
        else: raise ValueError('index parameter is out of range.')

    def tractDistanceToMidPoint(self, index: int, p: vector3float) -> float:
        if 0 <= index < self._streamlines.total_nb_rows:
            return midpoint2point(self._streamlines[index], p)
        else: raise ValueError('index parameter is out of range.')

    def tractPointIndex(self, index: int, p: vector3float) -> int:
        if 0 <= index < self._streamlines.total_nb_rows:
            i: cython.int
            for i in range(self._streamlines.total_nb_rows):
                if npall(self._streamlines[i] == p): return i
        else: raise ValueError('index parameter is out of range.')

    def tractPointFromDistance(self, index: int, d: float, percent: bool = False) -> vector3float:
        if 0 <= index < self._streamlines.total_nb_rows:
            sl = self._streamlines[index]
            l = length(sl)
            if percent: d *= l
            return arbitrarypoint(sl, d)
        else: raise ValueError('index parameter is out of range.')

    def tractPointIndexFromDistance(self, index: int, d: float, percent: bool = False) -> int:
        if 0 <= index < self._streamlines.total_nb_rows:
            p = self.tractPointFromDistance(index, d, percent)
            return self.tractPointIndex(index, p)
        else: raise ValueError('index parameter is out of range.')

    def minimumClosestDistanceBetweenTracts(self, index1: int, index2: int) -> float:
        if index1 >= self._streamlines.total_nb_rows: raise ValueError('index1 parameter is out of range.')
        if index2 >= self._streamlines.total_nb_rows: raise ValueError('index2 parameter is out of range.')
        sl1 = self._streamlines[index1]
        sl2 = self._streamlines[index2]
        return minimum_closest_distance(sl1, sl2)

    def tractScalarsFromVolume(self, index: int, vol: SisypheVolume) -> ndarray:
        if 0 <= index < self._streamlines.total_nb_rows:
            img = vol.getNumpy(defaultshape=False)
            affine = diag(list(vol.getSpacing()) + [1.0])
            return values_from_volume(img, self._streamlines[index], affine)
        else: raise ValueError('index parameter is out of range.')

    def tractScalarStatisticsFromVolume(self, index: int, vol: SisypheVolume) -> dict[str: float]:
        if 0 <= index < self._streamlines.total_nb_rows:
            data = self.tractScalarsFromVolume(index, vol)
            r = describe(data)
            stats = dict()
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = data.median()
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            stats['max'] = r.minmax[1]
            stats['std'] = sqrt(r.variance)
            stats['mean'] = r.mean
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('index parameter is out of range.')

    def tractScalarHistogramFromVolume(self, index: int,  vol: SisypheVolume, bins: int = 10) -> ndarray:
        if 0 <= index < self._streamlines.total_nb_rows:
            data = self.tractScalarsFromVolume(index, vol)
            return data.histogram(data, bins)
        else: raise ValueError('index parameter is out of range.')

    # Public bundle processing methods

    def tractsInsideSphere(self, p: vector3float, radius: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            i: cython.int
            r: list[cython.int] = list()
            bundleout = SisypheBundle()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                if self.isTractInsideSphere(index, p, radius): r.append(index)
            if len(r) > 0: bundleout.appendTracts(r)
            if inplace:
                bundleout.setName(bundle.getName())
                self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def tractsIntersectSphere(self, p: vector3float, radius: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            i: cython.int
            r: list[cython.int] = list()
            bundleout = SisypheBundle()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                if self.isTractIntersectSphere(index, p, radius): r.append(index)
            if len(r) > 0: bundleout.appendTracts(r)
            if inplace:
                bundleout.setName(bundle.getName())
                self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleLengths(self, bundle: str = 'all') -> list[float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            i: cython.int
            r: list[float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                r.append(self.tractLength(index))
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleLengthStatistics(self, bundle: str = 'all') -> dict[str: float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = array(self.bundleLengths(bundle))
            r = describe(data)
            stats = dict()
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = data.median()
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            stats['max'] = r.minmax[1]
            stats['std'] = sqrt(r.variance)
            stats['mean'] = r.mean
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleMeanCurvatures(self, bundle: str = 'all') -> list[float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            i: cython.int
            r: list[float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                r.append(self.tractMeanCurvature(index))
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleMeanCurvatureStatistics(self, bundle: str = 'all') -> dict[str: float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = array(self.bundleMeanCurvatures(bundle))
            r = describe(data)
            stats = dict()
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = data.median()
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            stats['max'] = r.minmax[1]
            stats['std'] = sqrt(r.variance)
            stats['mean'] = r.mean
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCentersOfMass(self, bundle: str = 'all') -> list[vector3float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            i: cython.int
            r: list[vector3float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                r.append(self.tractCenterOfMass(index))
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleScalarStatisticsFromVolume(self, vol: SisypheVolume, bundle: str = 'all') -> dict[str: float]:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            img = vol.getNumpy(defaultshape=False)
            affine = diag(list(vol.getSpacing()) + [1.0])
            data = values_from_volume(img, sl, affine)
            data = array(data).flatten()
            r = describe(data)
            stats = dict()
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = data.median()
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            stats['max'] = r.minmax[1]
            stats['std'] = sqrt(r.variance)
            stats['mean'] = r.mean
            stats['skewness'] = r.skewness
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleScalarHistogramFromVolume(self, vol: SisypheVolume, bins: int = 10,  bundle: str = 'all') -> ndarray:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            img = vol.getNumpy(defaultshape=False)
            affine = diag(list(vol.getSpacing()) + [1.0])
            data = values_from_volume(img, sl, affine)
            data = array(data).flatten()
            return data.histogram(data, bins)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getTractsSortedByLength(self, bundle: str = 'all') -> list[int]:
        sl = self.getStreamlinesFromBundle(bundle)
        return list(longest_track_bundle(sl, sort=True)[:])

    def getLongestTractIndex(self, bundle: str = 'all') -> int:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self.getTractsSortedByLength(bundle)[-1]
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getShortestTractIndex(self, bundle: str = 'all') -> int:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self.getTractsSortedByLength(bundle)[0]
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def removeTractsShorterThan(self, l: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            bundleout = self._bundles[bundle].copy()
            sortedidx = self.getTractsSortedByLength(bundle)
            removeidx = list()
            for idx in sortedidx:
                if l > length(self._streamlines[idx]): removeidx.append(idx)
                else: break
            if len(removeidx) > 0: bundleout.removeTracts(removeidx)
            if inplace: self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def removeTractsLongerThan(self, l: float, bundle: str = 'all', inplace: bool = False) -> SisypheBundle:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            bundleout = self._bundles[bundle].copy()
            sortedidx = self.getTractsSortedByLength(bundle)
            removeidx = list()
            for idx in sortedidx:
                if l < length(self._streamlines[idx]): removeidx.append(idx)
                else: break
            if len(removeidx) > 0: bundleout.removeTracts(removeidx)
            if inplace: self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleRoiSelection(self,
                           rois: SisypheROICollection,
                           include: list[bool] | None = None,
                           mode: str = 'any',
                           bundle: str = 'all') -> SisypheBundle:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            rois2 = list()
            for roi in rois:
                rois2.append(roi.getNumpy(defaultshape=False))
            if include is None: include = [True] * len(rois)
            affine = diag(list(rois[0].getSpacing()) + [1.0])
            if mode not in ('any', 'end'): mode = 'any'
            tracts = list()
            bundle = self._bundles[bundle].getList()
            i: cython.int
            for i in range(len(bundle)):
                sl = self._streamlines[bundle[i]]
                if len(list(select_by_rois([sl], affine, rois2, include, mode=mode))) > 0: tracts.append(bundle[i])
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleClusterConfidence(self,
                                mdf: int = 5,
                                subsample: int = 12,
                                power: int = 1,
                                ccithreshold: float = 1.0,
                                bundle: str = 'all') -> tuple[SisypheBundle, ndarray]:
        """
            mdf         int, maximum MDF distance (mm) that will be considered a 'supporting' streamline
                             and included in cci calculation (default 5 mm)
            subsample   int, number of points that are considered for each streamline in the calculation.
                             To save on calculation time, each streamline is subsampled.
                             (default 12 points)
            power       int, power to which the MDF distance for each streamline will be raised to determine
                             how much it contributes to the cci. High values of power make the contribution
                             value degrade much faster. E.g., a streamline with 5 mm MDF similarity contributes
                             1/5 to the cci if power is 1, but only contributes 1/5^2 = 1/25 if power is 2.
                             (default 1)
            return      SisypheBundle, streamline with cci >= ccithreshold
                        ndarray, cluster confidence index (CCI)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            cci = cluster_confidence(sl, mdf, subsample, power)
            tracts = list()
            bundle = self._bundles[bundle].getList()
            i: cython.int
            for i in range(len(cci)):
                if cci[i] >= ccithreshold: tracts.append(bundle[i])
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r, cci
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCentroidClustering(self, threshold: float = 10.0, bundle: str = 'all') -> Streamlines:
        """
            threshold   float, maximum distance from a bundle for a streamline to be
                               still considered as part of it. (Default 10 mm)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            return cluster_bundle(sl, threshold, rng=None)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCentroidDistanceSelection(self,
                                        centroid: ndarray,
                                        dist: str = 'mam',
                                        threshold: float = 10.0,
                                        bundle: str = 'all') -> SisypheBundle:
        """
            centroid    ndarray, centroid streamline
            dist        str, 'mam' mean average minimum distance
            threshold   float, dist parameter threshold, (default 10.0 mm)

            return  SisypheBundle
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            n = centroid.shape[0]
            centroid = Streamlines(centroid)
            sl = set_number_of_points(self.getStreamlinesFromBundle(bundle), n)
            if dist == 'mam': indices = bundles_distances_mam(centroid, sl)
            else: indices = bundles_distances_mdf(centroid, sl)
            tracts = list()
            for j in range(sl.total_nb_rows):
                if indices[0, j] < threshold:
                    tracts.append(self._bundles[bundle][j])
            bundleout = SisypheBundle()
            bundleout.appendTracts(tracts)
            return bundleout

    def bundleClustering(self,
                         threshold: float | None = None,
                         nbp: int = 12,
                         metric: str = 'mdf',
                         minclustersize: int = 10,
                         bundle: str = 'all') -> tuple[SisypheBundleCollection, Streamlines]:
        """
            threshold       float, maximum distance from a bundle for a streamline to be
                                   still considered as part of it. (Default 10 mm)
            nbp             int, number of points per streamline
            metric          str, 'mdf' average pointwise euclidean distance
                                 'com' center of mass euclidean distance
                                 'mid' midpoint euclidean distance
                                 'lgh' length
                                 'vbe' vector between endpoints
            minclustersize  int, minimum cluster size

            return          SisypheBundleCollection, clusters
                            Streamlines, cluster centroids
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            # Streamline average pointwise euclidean distance
            if metric == 'mdf':
                if threshold is None: threshold = 10.0
                feature = ResampleFeature(nb_points=nbp)
                AveragePointwiseEuclideanMetric(feature=feature)
            # Streamline center of mass euclidean distance
            elif metric == 'com':
                if threshold is None: threshold = 5.0
                feature = CenterOfMassFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline midpoint euclidean distance
            elif metric == 'mid':
                if threshold is None: threshold = 5.0
                feature = MidpointFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline length
            elif metric == 'lgh':
                if threshold is None: threshold = 2.0
                feature = ArcLengthFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline vector between endpoints
            elif metric == 'vbe':
                if threshold is None: threshold = 0.1
                feature = VectorOfEndpointsFeature()
                metric = CosineMetric(feature=feature)
            f = QuickBundles(threshold, metric=metric)
            clusters = f.cluster(sl)
            select = cluster < minclustersize
            centroids = list()
            r = SisypheBundleCollection()
            i: cython.int
            j: cython.int
            for i in range(len(clusters)):
                if select[i]:
                    tracts = list()
                    indices = clusters[i].indices
                    for j in range(len(indices)):
                        tracts.append(self._bundles[bundle][indices[j]])
                    bundleout = SisypheBundle()
                    bundleout.appendTracts(tracts)
                    r.append(bundleout)
                    centroids.append(clusters[i].centroid)
            return r, Streamlines(centroids)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleFastClustering(self,
                             threshold: float = 10.0,
                             minsize: int = 10,
                             bundle: str = 'all') -> tuple[SisypheBundleCollection, Streamlines]:
        """
            threshold   float, maximum distance from a bundle for a streamline to be
                               still considered as part of it. (Default 10 mm)
            minsize     int, minimum cluster size

            return      SisypheBundleCollection, clusters
                        Streamlines, cluster centroids
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            thresholds = [30, 20, 15, threshold]
            clusters = qbx_and_merge(sl, thresholds)
            select = cluster < minsize
            centroids = list()
            r = SisypheBundleCollection()
            i: cython.int
            j: cython.int
            for i in range(len(clusters)):
                if select[i]:
                    tracts = list()
                    indices = clusters[i].indices
                    for j in range(len(indices)):
                        tracts.append(self._bundles[bundle][indices[j]])
                    bundleout = SisypheBundle()
                    bundleout.appendTracts(tracts)
                    r.append(bundleout)
                    centroids.append(clusters[i].centroid)
            return r, Streamlines(centroids)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleFromBundleModel(self,
                              slmodel: Streamlines,
                              threshold: float = 15.0,
                              reduction: float = 10.0,
                              pruning: float = 5.0,
                              reductiondist: str = 'mam',
                              pruningdist: str = 'mam',
                              refine: bool = False,
                              minlength: int = 50,
                              bundle: str = 'all') -> SisypheBundle:
        """
            threshold       float, distance threshold in mm for clustering streamlines. (default 15.0)
            reduction       float, distance threshold in mm for bundle reduction. (default 10.0)
            pruning         float, distance threshold in mm for bundle pruning. (default 5.0)
            reductiondist   str, 'mdf' or 'mam'
            pruningdist     str, 'mdf' or 'mam'
            refine          bool
            minlength       int, minimum streamline size

            return          SisypheBundle
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            f = RecoBundles(sl, greater_than=minlength)
            slf, indices = f.recognize(slmodel,
                                       model_clust_thr=threshold,
                                       reduction_thr=reduction,
                                       reduction_distance=reductiondist,
                                       pruning_thr=pruning,
                                       pruning_distance=pruningdist)
            if refine:
                slf, indices = f.refine(slmodel, slf,
                                        model_clust_thr=threshold,
                                        reduction_thr=reduction,
                                        reduction_distance=reductiondist,
                                        pruning_thr=pruning,
                                        pruning_distance=pruningdist)
            tracts = list()
            for i in range(len(indices)):
                tracts.append(self._bundles[bundle][indices[i]])
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToRoi(self,
                    vol: SisypheVolume,
                    threshold: int = 10,
                    perc: bool = False,
                    bundle: str = 'all') -> SisypheROI:
        """
            threshold   int, if perc is False: absolute streamline count per voxel
                             if perc is True: percentile of streamline count per voxel distribution
            perc        bool, (default False)

            return      SisypheROI
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            map = self.bundleDensityMap(vol, bundle)
            roi = SisypheROI()
            roi.setName(bundle)
            if perc:
                if not (0.0 < threshold < 100.0): threshold = 95.0
                s = map.getNumpy().flatten().nonzero()
                threshold = int(percentile(s, threshold))
            roi = SisypheROI(map > threshold)
            roi.setName(bundle)
            return roi
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToMesh(self,
                     vol: SisypheVolume,
                     threshold: int,
                     perc: bool = False,
                     fill: float = 1000.0,
                     decimate: float = 1.0,
                     clean: bool = False,
                     smooth: str = 'sinc',
                     niter: int = 10,
                     factor: float = 0.1,
                     algo: str = 'flying',
                     largest: bool = False,
                     bundle: str = 'all') -> SisypheMesh:
        """
            threshold   int, if perc is False: absolute streamline count per voxel
                             if perc is True: percentile of streamline count per voxel distribution
            perc        bool, (default False)

            return      SisypheMesh
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            roi = self.bundleRoi(vol, threshold, perc, bundle)
            mesh = SisypheMesh()
            mesh.createFromROI(roi, fill, decimate, clean, smooth, niter, factor, algo, largest)
            mesh.setName(bundle)
            return mesh
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToDensityMap(self, vol: SisypheVolume, bundle: str = 'all') -> SisypheVolume:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            affine = diag(list(vol.getSpacing()) + [1.0])
            img = density_map(sl, affine, vol.getSize())
            r = SisypheVolume()
            r.copyFromNumpyArray(img,
                                 spacing=vol.getSpacing(),
                                 origin=vol.getOrigin(),
                                 defaultshape=False)
            r.copyAttributesFrom(vol)
            r.acquisition.setSequenceToDensityMap()
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToPathLengthMap(self, vol: SisypheVolume, roi: SisypheROI, bundle: str = 'all') -> SisypheVolume:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            affine = diag(list(roi.getSpacing()) + [1.0])
            img = path_length(sl, affine, roi.getNumpy(defaultshape=False), fill_value=-1)
            r = SisypheVolume()
            r.copyFromNumpyArray(img,
                                 spacing=vol.getSpacing(),
                                 origin=vol.getOrigin(),
                                 defaultshape=False)
            r.copyAttributesFrom(vol)
            r.acquisition.setSequence('PATH LENGTH MAP')
            return r

    def bundleToConnectivityMatrix(self, vol: SisypheVolume, bundle: str = 'all') -> ndarray:
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            if vol.acquisition.isLB():
                affine = diag(list(vol.getSpacing()) + [1.0])
                sl = self.getStreamlinesFromBundle(bundle)
                return connectivity_matrix(sl, affine, vol.getNumpy(defaultshape=False))
            else: raise ValueError('{} volume parameter modality {} is not LB.'.format(vol.getBasename(),
                                                                                       vol.acquisition.getModality()))
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def addBundleToSisypheTractCollection(self, tracts: SisypheTractCollection | None = None, bundle: str = 'all'):
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            if tracts is None: tracts = SisypheTractCollection()
            tracts.appendBundle(self, bundle)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # Public streamlines processing methods

    def compressStreamlines(self, maxlength: float = 10, inplace: bool = False) -> Streamlines:
        sl = compress_streamlines(self._streamlines, max_segment_length=maxlength)
        if inplace: self._streamlines = sl
        return sl

    def changeStreamlinesSampling(self, factor: float, inplace: bool = False) -> Streamlines:
        if 0.0 < factor < 2.0:
            sl = list()
            i: cython.int
            for i in range(self._streamlines.total_nb_rows):
                n = int(self._streamlines[i].shape[0] * factor)
                sl.append(set_number_of_points(self._streamlines[i], n))
            sl = Streamlines(sl)
            if inplace: self._streamlines = sl
            return sl
        else: raise ValueError('parameter value {} is out of range [0.0 to 2.0].'.format(factor))

    def changeStreamlinesStepSize(self, step: float, inplace: bool = False) -> Streamlines:
        if 0.1 <= step <= 5.0:
            sl = list()
            i: cython.int
            for i in range(self._streamlines.total_nb_rows):
                l = length(self._streamlines[i])
                n = int(l / step)
                sl.append(set_number_of_points(self._streamlines[i], n))
            sl = Streamlines(sl)
            if inplace: self._streamlines = sl
            return sl
        else: raise ValueError('parameter value {} is out of range [0.1 to 5.0 mm].'.format(step))

    def applyTransformToStreamlines(self, trf: SisypheTransform, inplace: bool = False) -> Streamlines:
        affine = trf.getNumpyArray(homogeneous=True)
        return transform_streamlines(self._streamlines, affine, in_place=inplace)

    def streamlinesToDensityMap(self, vol: SisypheVolume) -> SisypheVolume:
        return self.bundleDensityMap(vol)

    def streamlinesToPathLengthMap(self, vol: SisypheVolume, roi: SisypheROI) -> SisypheVolume:
        return self.bundlePathLengthMap(vol, roi)

    def streamlinesToConnectivityMatrix(self, vol: SisypheVolume) -> ndarray:
        return self.bundleConnectivityMatrix(vol)

    def streamlinesRoiSelection(self,
                                rois: SisypheROICollection,
                                include: list[bool] | None = None,
                                mode: str = 'any') -> SisypheStreamlines:
        rois2 = list()
        for roi in rois:
            rois2.append(roi.getNumpy(defaultshape=False))
        if include is None: include = [True] * len(rois)
        affine = diag(list(rois[0].getSpacing()) + [1.0])
        if mode not in ('any', 'end'): mode = 'any'
        r = list(select_by_rois(list(self._streamlines), affine, rois2, include, mode=mode))
        sl = SisypheStreamlines(Streamlines(r))
        sl.setFloatColor(sl.getFloatColor())
        sl.setLut(sl.getLut())
        sl.setColorRepresentation(sl.getColorRepresentation())
        sl.setOpacity(sl.getOpacity())
        sl.setLineWidth(sl.getLineWidth())
        return sl

    # Public IO methods

    def createXML(self, doc: minidom.Document, bundle: str) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('id')
            root.appendChild(node)
            txt = doc.createTextNode(self.getReferenceID())
            node.appendChild(txt)
            # Name
            node = doc.createElement('name')
            root.appendChild(node)
            txt = doc.createTextNode(bundle)
            node.appendChild(txt)
            # Regular step
            node = doc.createElement('regularstep')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._regstep))
            node.appendChild(txt)
            # Color
            node = doc.createElement('color')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(v) for v in self.getFloatColor(bundle)]))
            node.appendChild(txt)
            # Lut
            node = doc.createElement('lut')
            root.appendChild(node)
            txt = doc.createTextNode(self.getLut(bundle).getName())
            node.appendChild(txt)
            # Opacity
            node = doc.createElement('opacity')
            root.appendChild(node)
            txt = doc.createTextNode(str(self.getOpacity(bundle)))
            node.appendChild(txt)
            # Line width
            node = doc.createElement('linewidth')
            root.appendChild(node)
            txt = doc.createTextNode(str(self.getLineWidth(bundle)))
            node.appendChild(txt)

    def save(self, bundle: str, filename: str = '') -> None:
        if self._streamlines.total_nb_rows > 0:
            if bundle in self._bundles:
                if filename == '':
                    filename = join(self.getDirname(), bundle + self._FILEEXT)
                doc = minidom.Document()
                root = doc.createElement(self._FILEEXT[1:])
                root.setAttribute('version', '1.0')
                doc.appendChild(root)
                self.createXML(doc, bundle)
                sl = self.getStreamlinesFromBundle(bundle)
                data, offsets = unlist_streamlines(sl)
                bdata = data.tobytes()
                boffsets = offsets.tobytes()
                # Offsets
                offsets = '{} {}'.format(str(len(bdata)), str(len(boffsets)))
                node = doc.createElement('offsets')
                root.appendChild(node)
                txt = doc.createTextNode(offsets)
                node.appendChild(txt)
                # Datatypes
                dtypes = '{} {}'.format(str(data.dtype), str(offsets.dtype))
                node = doc.createElement('dtypes')
                root.appendChild(node)
                txt = doc.createTextNode(dtypes)
                node.appendChild(txt)
                buffxml = doc.toprettyxml().encode()  # Convert utf-8 to binary
                with open(filename, 'wb') as f:
                    # Write XML part
                    f.write(buffxml)
                    # Write Binary arrays
                    f.write(bdata)
                    f.write(boffsets)

    def saveToNumpy(self, bundle: str) -> None:
        if bundle in self._bundles:
            filename = join(self.getDirname(), bundle + self._FILEEXT)
            self._streamlines.save(filename)

    def saveToTck(self, bundle: str) -> None:
        self._save(bundle, save_tck)

    def saveToTrk(self, bundle: str) -> None:
        self._save(bundle, save_trk)

    def saveToVtk(self, bundle: str) -> None:
        self._save(bundle, save_vtk)

    def saveToVtp(self, bundle: str) -> None:
        self._save(bundle, save_vtp)

    def saveToFib(self, bundle: str) -> None:
        self._save(bundle, save_fib)

    def saveToDpy(self, bundle: str) -> None:
        self._save(bundle, save_dpy)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            r = dict()
            while node:
                # ID
                if node.nodeName == 'id':
                    self._ID = node.firstChild.data
                    if self._ID == 'None': self._ID = None
                # Name
                if node.nodeName == 'name':
                    r['name'] = node.firstChild.data
                # # Regular step
                if node.nodeName == 'regularstep':
                    self._regstep = (node.firstChild.data == 'True')
                # Color
                if node.nodeName == 'color':
                    buff = node.firstChild.data
                    r['color'] = [float(v) for v in buff.split(' ')]
                # Lut
                if node.nodeName == 'lut':
                    r['lut'] = node.firstChild.data
                # Opacity
                if node.nodeName == 'opacity':
                    r['opacity'] = float(node.firstChild.data)
                # Line width
                if node.nodeName == 'linewidth':
                    r['width'] = float(node.firstChild.data)
                # Offsets
                if node.nodeName == 'offsets':
                    buff = node.firstChild.data
                    r['offsets'] = [int(v) for v in buff.split(' ')]
                # Datatypes
                if node.nodeName == 'dtypes':
                    buff = node.firstChild.data
                    r['dtypes'] = buff.split(' ')
            return r

    def load(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.getFileExt()
        if exists(filename):
            with open(filename, 'rb') as f:
                # Read XML part
                line = ''
                strdoc = ''
                while line != '</xvol>\n':
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                doc = minidom.parseString(strdoc)
                r = self.parseXML(doc)
                # Read binary part
                bdata = f.read(r['offsets'][0])
                boffsets = f.read(r['offsets'][1])
            data = frombuffer(bdata, dtype=r['dtypes'][0])
            offsets = frombuffer(boffsets, dtype=r['dtypes'][1])
            self._streamlines = relist_streamlines(data, offsets)
            bundle = SisypheBundle((0, self._streamlines.total_nb_rows, 1))
            bundle.setName(r['name'])
            self._bundles = SisypheBundleCollection()
            self._bundles.append(bundle)
            self._initTracts()
            self.setFloatColor(r['color'], r['name'])
            self.setLut(r['lut'], r['name'])
            self.setOpacity(r['opacity'], r['name'])
            self.setLineWidth(r['width'], r['name'])
            self._dirname = dirname(filename)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromNumpy(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.NPZ
        if exists(filename):
            self._streamlines.load(filename)
            bundle = SisypheBundle((0, self._streamlines.total_nb_rows, 1))
            bundle.setName(splitext(basename(filename))[0])
            self._bundles = SisypheBundleCollection()
            self._bundles.append(bundle)
            self._initTracts()
            self._dirname = dirname(filename)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromTck(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.TCK
        if exists(filename): self._load(filename, load_tck)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromTrk(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.TRK
        if exists(filename): self._load(filename, load_trk)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromVtk(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.VTK
        if exists(filename): self._load(filename, load_vtk)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromVtp(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.VTP
        if exists(filename): self._load(filename, load_vtp)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromFib(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.FIB
        if exists(filename): self._load(filename, load_fib)
        else: raise IOError('No such file {}}'.format(filename))

    def loadFromDpy(self, filename: str) -> None:
        filename = splitext(filename)[0] + self.DPY
        if exists(filename): self._load(filename, load_dpy)
        else: raise IOError('No such file {}}'.format(filename))


class SisypheDiffusionModel(object):
    """
        SisypheDiffusionModel Class

        Description

            Abstract class for diffusion model

        Inheritance

            object -> SisypheDiffusionModel

        Private attributes

            _bvals      ndarray, gradient B values
            _bvecs      ndarray, gradient vectors
            _gtable     GradientTable
            _dwi        ndarray, n dwi images [x, y, z, n]
            _mean       SisypheVolume

        Public methods

            clear()
            count() -> int
            reorientGradients(trf: SisypheTransform)
            loadGradients(bvalsfile: str, bvecsfile: str)
            setGradients(bvals: ndarray, bvecs: ndarray) -> None
            getGradients() -> tuple[ndarray, ndarray]
            hasGradients() -> bool
            loadDWI(filenames: list[str])
            setDWI(vols: SisypheVolumeCollection) -> ndarray
            setDWIFromNumpy(self, dwi: ndarray,
                        spacing: vector3float | None = None,
                        radius: int = 4,
                        numpass: int = 4)
            getDWI() -> ndarray
            hasDWI() -> bool
            getSpacing() -> vector3float
            getMask() -> ndarray
            isFitted() -> bool
            computeFitting()
            getModel() -> SisypheDiffusionModel
            getFittedModel()
            getGradientTable() -> GradientTable
            saveModel(filename)
            loadModel(filename)

        Creation: 27/10/2023
        Revisions:

            10/11/2023  setGradients() method bugfix, ndim (=1) and shape of bvals parameter
                        setDWI() method bugfix
            11/11/2023  add binary block write with progress bar support to saveModel() method
                        add binary block read with progress bar support to loadModel() method
    """

    __slots__ = ['_bvals', '_bvecs', '_gtable', '_dwi', '_mask', '_model', '_fmodel', '_spacing']

    # Class constants

    _FILEEXT = '.xdmodel'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Diffusion model (*{})'.format(cls._FILEEXT)

    @classmethod
    def openModel(cls, filename: str) -> SisypheDiffusionModel:
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            with open(filename, 'rb') as f:
                # Read XML part
                line = ''
                strdoc = ''
                while line != '</{}>\n'.format(self._FILEEXT[1:]):
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                # Read binary part
                buffarray = f.read()
            doc = minidom.parseString(strdoc)
            attr = self.parseXML(doc)
            if attr['model'] == 'DTI': r = SisypheDTIModel()
            elif attr['model'] == 'DKI': r = SisypheDKIModel()
            elif attr['model'] == 'SHCSA': r = SisypheSHCSAModel()
            elif attr['model'] == 'SHCSD': r = SisypheSHCSDModel()
            elif attr['model'] == 'DSI': r = SisypheDSIModel()
            elif attr['model'] == 'DSID': r = SisypheDSIDModel()
            else: r = SisypheDTIModel()
            dwi = frombuffer(buffarray, dtype=attr['dtype'])
            dwi = dwi.reshape(attr['shape'])
            r.setDWIFromNumpy(dwi, spacing=attr['spacing'])
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    def __init__(self) -> None:
        self._bvals: ndarray | None = None
        self._bvecs: ndarray | None = None
        self._gtable: GradientTable | None = None
        self._dwi: ndarray | None = None
        self._mask: ndarray | None = None
        self._model = None
        self._fmodel = None
        self._spacing = [1.0] * 3

    # Public methods

    def clear(self) -> None:
        del self._bvals, self._bvecs, self._gtable
        del self._dwi, self._mask, self._model
        self._bvals = None
        self._bvecs = None
        self._gtable = None
        self._dwi = None
        self._mask = None
        self._model = None

    def count(self) -> int:
        if self._bvals is not None: return self._bvals.shape[0]
        elif self._dwi is not None: return self._dwi.shape[3]
        else: return 0

    def reorientGradients(self, trf: SisypheTransform) -> None:
        if self._gtable is not None:
            affine = trf.getNumpyArray(homogeneous=True)
            self._gtable = reorient_bvecs(self._gtable, affine)
        else: raise AttributeError('Gradient table is empty.')

    def loadGradients(self, bvalsfile: str, bvecsfile: str) -> None:
        if exists(bvalsfile):
            _, ext = splitext(bvalsfile)
            if ext == '.txt': bvals = loadBVal(bvalsfile, format='txt', numpy=True)
            elif ext == '.xbval': bvals = loadBVal(bvalsfile, format='xml', numpy=True)
            else: raise IOError('invalid format {}.'.format(ext))
        else: raise IOError('no such file {}.'.format(basename(bvalsfile)))
        if exists(bvecsfile):
            _, ext = splitext(bvecsfile)
            if ext == '.txt':
                try: bvecs = loadBVec(bvecsfile, format='txtbydim', numpy=True)
                except: bvecs = loadBVec(bvecsfile, format='txtbyvec', numpy=True)
            elif ext == '.xbvec':
                bvecs = loadBVec(bvecsfile, format='xml', numpy=False)
                filenames = list(bvecs.keys())
                self.loadDWI(filenames)
                bvecs = array(list(bvecs.values()))
            else: raise IOError('invalid format {}.'.format(ext))
        else: raise IOError('no such file {}.'.format(basename(bvecsfile)))
        self.setGradients(bvals, bvecs)

    def setGradients(self, bvals: ndarray, bvecs: ndarray) -> None:
        if bvecs.ndim != 2 or bvecs.shape[1] != 3:
            raise ValueError('invalid bvecs ndarray parameter shape.')
        if bvals.ndim != 1:
            raise ValueError('invalid bvals ndarray parameter shape.')
        if bvecs.shape[0] != bvals.shape[0]:
            raise ValueError('item count in bvals and bvecs is different.')
        if self._dwi is not None and self._dwi.shape[3] != bvals.shape[0]:
            raise ValueError('item count in bvals/bvecs and DWI image count is different.')
        self._bvecs = bvecs
        self._bvals = bvals
        self._gtable = gradient_table(self._bvals, self._bvecs)

    def getGradients(self) -> tuple[ndarray, ndarray]:
        return self._bvals, self._bvecs

    def hasGradients(self) -> bool:
        return self._bvals is not None and self._bvecs is not None

    def loadDWI(self, filenames: list[str]) -> None:
        vols = SisypheVolumeCollection()
        vols.load(filenames)
        self.setDWI(vols)

    def setDWI(self,
               vols: SisypheVolumeCollection,
               algo: str = 'otsu',
               niter: int = 2,
               kernel: int = 0) -> None:
        """
            algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                            'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                            algorithm used for automatic object/background segmentation (default otsu)
            kernel  int, kernel size of binary morphology operator (default 1)
            niter   int, number of binary morphology iterations (default 1)
        """
        if self._bvals is not None and vols.count() != self._bvals.shape[0]:
            raise ValueError('item count in bvals/bvecs and DWI image count is different.')
        self._dwi = vols.copyToNumpyArray(defaultshape=False)
        self._spacing = vols[0].getSpacing()
        vol = SisypheVolume(self._dwi.mean(axis=3), spacing=self._spacing())
        self._mask = vol.getMask2(algo, niter, kernel).getNumpy(defaultshape=False)

    def setDWIFromNumpy(self, dwi: ndarray,
                        spacing: vector3float | None = None,
                        algo: str = 'otsu',
                        niter: int = 2,
                        kernel: int = 0) -> None:
        """
            algo    str in ['mean', 'otsu', 'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle',
                            'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments']
                            algorithm used for automatic object/background segmentation (default otsu)
            kernel  int, kernel size of binary morphology operator (default 1)
            niter   int, number of binary morphology iterations (default 1)
        """
        if self._bvals is not None and dwi.shape[-1] != bvals.shape[0]:
            raise ValueError('item count in bvals/bvecs and DWI image count is different.')
        self._dwi = dwi
        if spacing is not None: self._spacing = spacing
        vol = SisypheVolume(self._dwi.mean(axis=3), spacing=spacing)
        self._mask = vol.getMask2(algo, niter, kernel).getNumpy(defaultshape=False)

    def getDWI(self) -> ndarray:
        return self._dwi

    def hasDWI(self) -> bool:
        return self._dwi is not None

    def getSpacing(self) -> vector3float:
        return self._spacing

    def getMask(self) -> ndarray:
        return self._mask

    def isFitted(self) -> bool:
        return self._fmodel is not None

    def computeFitting(self) -> None:
        raise NotImplementedError

    def getModel(self):
        return self._model

    def getFittedModel(self):
        return self._fmodel

    def getGradientTable(self) -> GradientTable:
        return self._gtable

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # bvals
            node = doc.createElement('bvals')
            root.appendChild(node)
            buff = ' '.join([str(v) for v in self._bvals])
            txt = doc.createTextNode(buff)
            node.appendChild(txt)
            # bvecs
            node = doc.createElement('bvecs')
            root.appendChild(node)
            buff = list()
            for i in range(self._bvecs.shape[0]):
                buff.append(' '.join([str(v) for v in list(self._bvecs[i])]))
            txt = doc.createTextNode('|'.join(buff))
            node.appendChild(txt)
            # DWI dtype
            node = doc.createElement('dtype')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._dwi.dtype))
            node.appendChild(txt)
            # DWI shape
            node = doc.createElement('shape')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(v) for v in self._dwi.shape]))
            node.appendChild(txt)
            # DWI spacing
            node = doc.createElement('spacing')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(v) for v in self._spacing]))
            node.appendChild(txt)

    def saveModel(self,
                  filename: str,
                  wait: DialogWait | None = None) -> None:
        if self._dwi is not None and self._gtable is not None:
            filename = splitext(filename)[0] + self._FILEEXT
            doc = minidom.Document()
            root = doc.createElement(self._FILEEXT[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            self.createXML(doc)
            buffxml = doc.toprettyxml().encode()  # Convert utf-8 to binary
            # Binary ndarray attribute
            buffdwi = self._dwi.tobytes()
            with open(filename, 'wb') as f:
                # Save XML part
                f.write(buffxml)
                # Binary array part
                block = 10485760  # 10 MBytes
                total = len(buffdwi)
                n = total // block
                if wait is None or n < 2: f.write(buffdwi)
                else:
                    wait.setInformationText('Save {} model'.format(basename(filename)))
                    wait.setProgressRange(0, n)
                    wait.progressVisibilityOn()
                    for i in range(n):
                        start = i * block
                        end = start + block - 1
                        f.write(buffdwi[start:end])
                        wait.setCurrentProgressValue(i + 1)
                    if end < total: f.write(buffdwi[end + 1:])
                    wait.progressVisibilityOff()

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            bvals = None
            bvecs = None
            attr = dict()
            node = root.firstChild
            while node:
                # bvals
                if node.nodeName == 'bvals':
                    buff = node.firstChild.data
                    bvals = array([float(v) for v in buff.split(' ')])
                # bvecs
                if node.nodeName == 'bvecs':
                    buff = list()
                    vecs = node.firstChild.data.split('|')
                    for vec in vecs: buff.append([float(v) for v in vec])
                    bvecs = array(buff)
                # DWI dtype
                if node.nodeName == 'dtype':
                    attr['dtype'] = node.firstChild.data
                # DWI shape
                if node.nodeName == 'shape':
                    buff = node.firstChild.data
                    attr['shape'] = [int(v) for v in buff.split(' ')]
                # DWI spacing
                if node.nodeName == 'spacing':
                    buff = node.firstChild.data
                    self._spacing = [float(v) for v in buff.split(' ')]
                node = node.nextSibling
            if bvals is not None and bvecs is not None: self.setGradients(bvals, bvecs)
            return attr
        else: raise IOError('XML file format is not supported.')

    def loadModel(self,
                  filename: str,
                  wait: DialogWait | None = None) -> None:
        filename = splitext(filename)[0] + self._FILEEXT
        if exists(filename):
            with open(filename, 'rb') as f:
                # Read XML part
                line = ''
                strdoc = ''
                while line != '</{}>\n'.format(self._FILEEXT[1:]):
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                # Read binary part
                block = 10485760  # 10 MBytes
                start = f.tell()
                end = f.seek(0, os.SEEK_END)
                total = end - start + 1  # Binary part size
                n = total // block
                f.seek(start, os.SEEK_SET)
                if wait is None or n > 2: buffarray = f.read()
                else:
                    wait.setInformationText('Load {} model'.format(basename(filename)))
                    wait.setProgressRange(0, n)
                    wait.progressVisibilityOn()
                    buffarray = bytes()
                    while f.tell() < end:
                        r = f.read(block)
                        buffarray += r
                        wait.incCurrentProgressValue()
                    wait.progressVisibilityOff()
            doc = minidom.parseString(strdoc)
            attr = self.parseXML(doc)
            dwi = frombuffer(buffarray, dtype=attr['dtype'])
            dwi = dwi.reshape(attr['shape'])
            self.setDWIFromNumpy(dwi, spacing=None)
        else: raise IOError('No such file {}.'.format(basename(filename)))


class SisypheDTIModel(SisypheDiffusionModel):
    """
        SisypheDTIModel Class

        Description

            Class to manage diffusion tensor imaging model

        Inheritance

            object -> SisypheDiffusionModel -> SisypheDTIModel

        Private attribute

            _algfit         str, 'WLS'  weighted least squares
                                 'OLS'  ordinary least squares
                                 'NLLS' non-linear least squares
                                 'RT'   restore robust tensor
            _model          TensorModel class (dipy.reconst.dti.TensorModel)
            _fmodel         TensorFit class (dipy.reconst.dti.TensorFit)

        Public methods

            setFitAlgorithm(algfit: str = 'WLS')
            getFitAlgorithm() -> str
            getFA() -> SisypheVolume
            getGA() -> SisypheVolume
            getMD() -> SisypheVolume
            getLinearity() -> SisypheVolume
            getPlanarity() -> SisypheVolume
            getSphericity() -> SisypheVolume
            getTrace() -> SisypheVolume
            getAxialDiffusivity() -> SisypheVolume
            getRadialDiffusivity() -> SisypheVolume
            getIsotropic() -> SisypheVolume
            getDeviatropic() -> SisypheVolume
            getTensor() -> ndarray
            getEigenValues() -> ndarray
            getEigenVectors() -> ndarray

            inherited SisypheDiffusionModel methods

        Creation: 27/10/2023
        Revisions:
    """

    __slots__ = ['_algfit']

    # Class constants

    _WLS, _OLS, _NLLS, _RT = 'WLS', 'OLS', 'NLLS', 'RT'
    _ALG = (_WLS, _OLS, _NLLS, _RT)

    # Special method

    def __init__(self, algfit: str = 'WLS') -> None:
        super().__init__()

        if algfit in self._ALG: self._algfit = algfit
        else: self._algfit = 'WLS'

        self._model: TensorModel | None = None
        self._fmodel: TensorFit | None = None

    # Public methods

    def setFitAlgorithm(self, algfit: str = 'WLS') -> None:
        if algfit in self._ALG: self._algfit = algfit
        else: ValueError('invalid parameter value {}.'.format(algfit))

    def getFitAlgorithm(self) -> str:
        return self._algfit

    def computeFitting(self, algfit: str = '') -> None:
        if self.hasGradients() and self.hasDWI():
            if self._model is None:
                if algfit == '' or algfit not in _ALG: algfit = self._algfit
                else: self._algfit = algfit
                self._model = TensorModel(self._gtable, algfit)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    def getFA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            return r

    def getGA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.ga,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('GA')
            return r

    def getMD(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.md,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('MD')
            return r

    def getLinearity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.linearity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('LINEARITY')
            return r

    def getPlanarity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.planarity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('PLANARITY')
            return r

    def getSphericity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.sphericity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('SPHERICITY')
            return r

    def getTrace(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.trace,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('TRACE')
            return r

    def getAxialDiffusivity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.ad,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('AXIAL DIFFUSIVITY')
            return r

    def getRadialDiffusivity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.rd,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('RADIAL DIFFUSIVITY')
            return r

    def getIsotropic(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(isotropic(self._fmodel.quadratic_form),
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('ISOTROPIC TENSOR')
            return r

    def getDeviatropic(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(deviatoric(self._fmodel.quadratic_form),
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('ANISOTROPIC TENSOR')
            return r

    def getTensor(self) -> ndarray:
        if self._fmodel is not None:
            return self._fmodel.quadratic_form

    def getEigenValues(self) -> ndarray:
        if self._fmodel is not None:
            return self._fmodel.evals

    def getEigenVectors(self) -> ndarray:
        if self._fmodel is not None:
            return self._fmodel.evecs

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('DTI')
            node.appendChild(txt)
            # Fitting algorithm
            node = doc.createElement('fitalgo')
            root.appendChild(node)
            txt = doc.createTextNode(self._algfit)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                # Fitting algorithm
                if node.nodeName == 'fitalgo': self._algfit = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheDKIModel(SisypheDiffusionModel):
    """
         SisypheDkIDModel

         Description

             Class to manage diffusion kurtosis model

         Inheritance

             object -> SisypheDiffusionModel -> SisypheDkIDModel

         Private attribute

            _algfit     str, 'WLS' weighted least squares
                             'OLS' ordinary least squares
                             'CLS' constrained ordinary least squares
                             'CWLS' constrained weighted least squares
             _model     DiffusionKurtosisModel class (dipy.reconst.dki.DiffusionKurtosisModel)
             _fmodel    DiffusionKurtosisFit class (dipy.reconst.dki.DiffusionKurtosisFit)

         Public methods

            setFitAlgorithm(algfit: str = 'WLS')
            getFitAlgorithm() -> str
            getKFA() -> SisypheVolume
            getFA() -> SisypheVolume
            getGA() -> SisypheVolume
            getMD() -> SisypheVolume
            getLinearity() -> SisypheVolume
            getPlanarity() -> SisypheVolume
            getSphericity() -> SisypheVolume
            getTrace() -> SisypheVolume
            getAxialDiffusivity() -> SisypheVolume
            getRadialDiffusivity() -> SisypheVolume

            inherited SisypheDiffusionModel methods

         Creation: 29/10/2023
         Revisions:
     """

    __slots__ = ['_algfit']

    # Class constants

    _WLS, _OLS, _CLS, _CWLS = 'WLS', 'OLS', 'CLS', 'CWLS'
    _ALG = (_WLS, _OLS, _CLS, _CWLS)

    # Special method

    def __init__(self) -> None:
        super().__init__()

        if algfit in self._ALG: self._algfit = algfit
        else: self._algfit = 'WLS'

        self._model: DiffusionKurtosisModel | None = None
        self._fmodel: DiffusionKurtosisFit | None = None

    # Public methods

    def setFitAlgorithm(self, algfit: str = 'WLS') -> None:
        if algfit in self._ALG: self._algfit = algfit
        else: ValueError('invalid parameter value {}.'.format(algfit))

    def getFitAlgorithm(self) -> str:
        return self._algfit

    def computeFitting(self, algfit: str = '') -> None:
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if algfit == '' or algfit not in _ALG: algfit = self._algfit
                else: self._algfit = algfit
                self._model = DiffusionKurtosisModel(gtab, fit_method=algfit)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    def getKFA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.kfa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('KFA')
            return r

    def getFA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            return r

    def getGA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.ga,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('GA')
            return r

    def getMD(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.md,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('MD')
            return r

    def getLinearity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.linearity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('LINEARITY')
            return r

    def getPlanarity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.planarity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('PLANARITY')
            return r

    def getSphericity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.sphericity,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('SPHERICITY')
            return r

    def getTrace(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.trace,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('TRACE')
            return r

    def getAxialDiffusivity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.ad,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('AXIAL DIFFUSIVITY')
            return r

    def getRadialDiffusivity(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.rd,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('RADIAL DIFFUSIVITY')
            return r

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('DKI')
            node.appendChild(txt)
            # Fitting algorithm
            node = doc.createElement('fitalgo')
            root.appendChild(node)
            txt = doc.createTextNode(self._algfit)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                # Fitting algorithm
                if node.nodeName == 'fitalgo': self._algfit = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheSHCSAModel(SisypheDiffusionModel):
    """
        SisypheSHCSAModel

        Description

            Class to manage spherical harmonic model with constant solid angle reconstruction

        Inheritance

            object -> SisypheDiffusionModel -> SisypheSHCSAModel

        Private attribute

            _order      int, spherical harmonic order of the model
            _model      CsaOdfModel class (dipy.reconst.shm.CsaOdfModel)
            _fmodel     SphHarmFit class (dipy.reconst.shm.SphHarmFit)

        Public methods

            setOrder(order: int = 6)
            getOrder() -> int
            getGFA() -> SisypheVolume

            inherited SisypheDiffusionModel methods

        Creation: 29/10/2023
        Revisions:
    """

    __slots__ = ['_order']

    # Special method

    def __init__(self, order: int = 6) -> None:
        super().__init__()
        self._order: int = order
        self._model: CsaOdfModel | None = None
        self._fmodel: SphHarmFit | None = None

    # Public methods

    def setOrder(self, order: int = 6) -> None:
        self._order = order

    def getOrder(self) -> int:
        return self._order

    def computeFitting(self, order: int = 0) -> None:
        if self.hasGradients() and self.hasDWI():
            if self._model is None:
                if order == 0: order = self._order
                else: self._order = order
                self._model = CsaOdfModel(self._gtable, sh_order=order)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    def getGFA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            return r

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('SHCSA')
            node.appendChild(txt)
            # Spherical harmonic order
            node = doc.createElement('order')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._order))
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                # Spherical harmonic order
                if node.nodeName == 'order': self._order = int(node.firstChild.data)
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheSHCSDModel(SisypheDiffusionModel):
    """
        SisypheCSDModel

        Description

            Class to manage constrained spherical harmonic deconvolution model

        Inheritance

            object -> SisypheDiffusionModel -> SisypheCSDModel

        Private attribute

            _order      int, spherical harmonic order of the model
            _model      ConstrainedSphericalDeconvModel class (dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel)
            _fmodel     SphHarmFit class (dipy.reconst.shm.SphHarmFit)

        Public methods

            setOrder(order: int = 6)
            getOrder() -> int
            getGFA() -> SisypheVolume

            inherited SisypheDiffusionModel methods

        Creation: 29/10/2023
        Revisions:
    """

    __slots__ = ['_order']

    # Special method

    def __init__(self, order: int = 6) -> None:
        super().__init__()
        self._order: int = order
        self._model: ConstrainedSphericalDeconvModel | None = None
        self._fmodel: SphHarmFit | None = None

    # Public methods

    def setOrder(self, order: int = 6) -> None:
        self._order = order

    def getOrder(self) -> int:
        return self._order

    def computeFitting(self, order: int = 0) -> None:
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if order == 0: order = self._order
                else: self._order = order
                response, ratio = auto_response_ssst(self._gtable, self._dwi, roi_radii=10, fa_thr=0.7)
                self._model = ConstrainedSphericalDeconvModel(gtab, response, sh_order=order)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    def getGFA(self) -> SisypheVolume:
        if self._fmodel is not None:
            r = SisypheVolume()
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            return r

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('SHCSD')
            node.appendChild(txt)
            # Spherical harmonic order
            node = doc.createElement('order')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._order))
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                # Spherical harmonic order
                if node.nodeName == 'order': self._order = int(node.firstChild.data)
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheDSIModel(SisypheDiffusionModel):
    """
        SisypheDSIModel

        Description

            Class to manage diffusion spectrum imaging model

        Inheritance

            object -> SisypheDiffusionModel -> SisypheDSIModel

        Private attribute

            _model      DiffusionSpectrumModel class (dipy.reconst.dsi.DiffusionSpectrumModel)
            _fmodel     DiffusionSpectrumFit class (dipy.reconst.dsi.DiffusionSpectrumFit)

        Public methods

            inherited SisypheDiffusionModel methods

        Creation: 29/10/2023
        Revisions:
    """

    # Special method

    def __init__(self) -> None:
        super().__init__()
        self._model: DiffusionSpectrumModel | None = None
        self._fmodel: DiffusionSpectrumFit | None = None

    # Public method

    def computeFitting(self) -> None:
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                self._model = DiffusionSpectrumModel(gtab)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('DSI')
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheDSIDModel(SisypheDiffusionModel):
    """
         SisypheDSIDModel

         Description

             Class to manage diffusion spectrum imaging deconvolution model

         Inheritance

             object -> SisypheDiffusionModel -> SisypheDSIDModel

         Private attribute

             _model      DiffusionSpectrumDeconvModel class (dipy.reconst.dsi.DiffusionSpectrumDeconvModel)
             _fmodel     DiffusionSpectrumDeconvFit class (dipy.reconst.dsi.DiffusionSpectrumDeconvFit)

         Public methods

            inherited SisypheDiffusionModel methods

         Creation: 29/10/2023
         Revisions:
     """

    # Special method

    def __init__(self) -> None:
        super().__init__()
        self._model: DiffusionSpectrumDeconvModel | None = None
        self._fmodel: DiffusionSpectrumDeconvFit | None = None

    # Public method

    def computeFitting(self) -> None:
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                self._model = DiffusionSpectrumDeconvModel(gtab)
                self._fmodel = self._model.fit(self._dwi, self._mask)

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode('DSID')
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict[str]:
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            attr = super().parseXML(doc)
            node = root.firstChild
            while node:
                # Model type
                if node.nodeName == 'model': attr['model'] = node.firstChild.data
                node = node.nextSibling
            return attr
        else: raise IOError('XML file format is not supported.')


class SisypheTracking(object):
    """
        SisypheTracking Class

        Description

            Tracking class

        Inheritance

            object -> SisypheTracking

        Private attribute

            _model      SisypheDiffusionModel
            _alg        str, tracking algorithm
            _density    int, seed count per voxel
            _seeds      ndarray, seed mask
            _stepsize   float, step size in mm
            _stopping   ActStoppingCriterion | BinaryStoppingCriterion | ThresholdStoppingCriterion

        Public methods

            setTrackingAlgorithm(alg: int)
            setTrackingAlgorithmToDeterministicEulerIntegration()
            setTrackingAlgorithmToDeterministicParticleFiltering()
            setTrackingAlgorithmToDeterministicClosestPeakDirection()
            setTrackingAlgorithmToDeterministicFiberOrientationDistribution()
            setTrackingAlgorithmToProbabilisticBootstrapDirection()
            setTrackingAlgorithmToProbabilisticFiberOrientationDistribution()
            getTrackingAlgorithm() -> int
            getTrackingAlgorithmAsString() -> str
            setSeedCountPerVoxel(n: int = 1)
            getSeedCountPerVoxel() -> int
            setStepSize(stepsize: float = 1.0)
            getStepSize() -> float
            setStoppingCriterionFAThreshold(threshold: float = 0.1)
            setStoppingCriterionGFAThreshold(threshold: float = 0.1)
            setStoppingCriterionRoi(roi: SisypheROI)
            setStoppingCriterionAnatomical(gm: SisypheVolume(), wm: SisypheVolume(), csf: SisypheVolume())
            setSeedsFromRoi(roi: SisypheROI)
            setSeedsFromFAThreshold(threshold: float)
            setSeedsFromGFAThreshold(threshold: float)
            computeTracking() -> SisypheStreamlines

        Creation: 29/10/2023
        Revisions:
    """

    __slots__ = ['_model', '_alg', '_density', '_seeds', '_stepsize', '_stopping']

    # Class constants

    _DEUDX = 0
    _DPARTICLE = 1
    _DCPD = 2
    _DFOD = 3
    _PBSD = 4
    _PFOD = 5
    _ALG = {_DEUDX: 'Deterministic Euler integration',
            _DPARTICLE: 'Deterministic particle filtering',
            _DCPD: 'Deterministic closest peak direction',
            _DFOD: 'Deterministic fiber orientation distribution',
            _PBSD: 'Probabilistic bootstrap direction',
            _PFOD: 'Probabilistic fiber orientation distribution'}

    # Special method

    def __init__(self, model: SisypheDiffusionModel):
        self._model = model
        self._alg: int = 0
        self._density: int = 1
        self._seeds: ndarray | None = None
        self._stepsize: float = 1.0
        self._stopping = None

    # Public methods

    def setTrackingAlgorithm(self, alg: int) -> None:
        if alg in self._ALG: self._alg = alg
        else: raise ValueError('Invalid algorithm code.')

    def setTrackingAlgorithmToDeterministicEulerIntegration(self) -> None:
        self._alg = self._DEUDX

    def setTrackingAlgorithmToDeterministicParticleFiltering(self) -> None:
        self._alg = self._DPARTICLE

    def setTrackingAlgorithmToDeterministicClosestPeakDirection(self) -> None:
        self._alg = self._DCPD

    def setTrackingAlgorithmToDeterministicFiberOrientationDistribution(self) -> None:
        self._alg = self._DFOD

    def setTrackingAlgorithmToProbabilisticBootstrapDirection(self) -> None:
        self._alg = self._PBSD

    def setTrackingAlgorithmToProbabilisticFiberOrientationDistribution(self) -> None:
        self._alg = self._PFOD

    def getTrackingAlgorithm(self) -> int:
        return self._alg

    def getTrackingAlgorithmAsString(self) -> str:
        return self._ALG[self._ald]

    def setSeedCountPerVoxel(self, n: int = 1) -> None:
        if 0 < n < 10: self._density = n
        else: raise ValueError('invalid number of seeds per voxel.')

    def getSeedCountPerVoxel(self) -> int:
        return self._density

    def setStepSize(self, stepsize: float = 1.0) -> None:
        if 0.1 <= stepsize <= 2.0: self._stepsize = stepsize
        else: raise ValueError('invalid step size.')

    def getStepSize(self) -> float:
        return self._stepsize

    def setStoppingCriterionFAThreshold(self, threshold: float = 0.1) -> None:
        if 0.0 < threshod < 1.0:
            if isinstance(self._model, SisypheDTIModel): FA = self._model.getFA()
            else:
                model = TensorModel(self._model.getGradientTable(), 'WLS')
                fit = model.fit(self._model.getDWI(), self._model.getMask())
                FA = fit.fa
            self._stopping = ThresholdStoppingCriterion(FA, threshold)
        else: raise ValueError('Invalid threshold.')

    def setStoppingCriterionGFAThreshold(self, threshold: float = 0.1) -> None:
        if 0.0 < threshod < 1.0:
            if isinstance(self._model, SisypheSHCSAModel): GFA = self._model.getGFA()
            else:
                model = CsaOdfModel(self._gtable, sh_order=6)
                fit = model.fit(self._model.getDWI(), self._model.getMask())
                GFA = fit.gfa
            self._stopping = ThresholdStoppingCriterion(GFA, threshold)
        else: raise ValueError('Invalid threshold.')

    def setStoppingCriterionRoi(self, roi: SisypheROI) -> None:
        self._stopping = BinaryStoppingCriterion(roi.getNumpy(defaultshape=False))

    def setStoppingCriterionAnatomical(self,
                                       gm: SisypheVolume(),
                                       wm: SisypheVolume(),
                                       csf: SisypheVolume()) -> None:
        if gm.acquisition.getSequence() != SisypheAcquisition.GM:
            raise ValueError('{} volume is not gray matter map.'.format(gm.getBasename()))
        if wm.acquisition.getSequence() != SisypheAcquisition.WM:
            raise ValueError('{} volume is not white matter map.'.format(wm.getBasename()))
        if csf.acquisition.getSequence() != SisypheAcquisition.CSF:
            raise ValueError('{} volume is not cerebro-spinal fluid map.'.format(csf.getBasename()))
        if gm.getSize() != self._mask.shape:
            raise ValueError('invalid {} size.'.format(gm.getBasename()))
        if wm.getSize() !=  self._mask.shape:
            raise ValueError('invalid {} size.'.format(wm.getBasename()))
        if csf.getSize() !=  self._mask.shape:
            raise ValueError('invalid {} size.'.format(csf.getBasename()))
        include = gm.getNumpy(defaultshape=False)
        wm = wm.getNumpy(defaultshape=False)
        exclude = csf.getNumpy(defaultshape=False)
        back = np.ones(include.shape)
        back[(include + wm + exclude) > 0] = 0
        include[back > 0] = 1
        self._stopping = ActStoppingCriterion(include, exclude)

    def setSeedsFromRoi(self, roi: SisypheROI) -> None:
        self._seeds = roi.getNumpy(defaultshape=False)

    def setSeedsFromFAThreshold(self, threshold: float) -> None:
        if 0.0 < threshod < 1.0:
            if isinstance(self._model, SisypheDTIModel): FA = self._model.getFA()
            else:
                model = TensorModel(self._model.getGradientTable(), 'WLS')
                fit = model.fit(self._model.getDWI(), self._model.getMask())
                FA = fit.fa
            self._seeds = FA > threshold
        else: raise ValueError('Invalid threshold.')

    def setSeedsFromGFAThreshold(self, threshold: float) -> None:
        if 0.0 < threshod < 1.0:
            if isinstance(self._model, SisypheSHCSAModel): GFA = self._model.getGFA()
            else:
                model = CsaOdfModel(self._model.getGradientTable(), sh_order=6)
                fit = model.fit(self._model.getDWI(), self._model.getMask())
                GFA = fit.gfa
            self._seeds = GFA > threshold
        else: raise ValueError('Invalid threshold.')

    def computeTracking(self) -> SisypheStreamlines:
        affine = diag(list(self._model.getSpacing()) + [1.0])
        seeds = seeds_from_mask(self._seeds, affine, self._density)
        # Deterministic Euler integration
        if self._alg == _DEUDX:
            if not self._model.isFitted(): self._model.computeFitting()
            peaks = peaks_from_model(model=self._model.getFittedModel(),
                                     data=self._model.getDWI(),
                                     sphere=default_sphere,
                                     relative_peak_threshold=0.8,
                                     min_separation_angle=45,
                                     mask=self._mask)
            sl = Streamlines(LocalTracking(direction_getter=peaks,
                                           stopping_criterion=self._stopping,
                                           seeds=seeds,
                                           affine=affine,
                                           step_size=self._stepsize))
            return SisypheStreamlines(sl)
        # Deterministic particle filtering
        elif self._alg == _DPARTICLE:
            if not self._model.isFitted(): self._model.computeFitting()
            peaks = peaks_from_model(model=self._model.getFittedModel(),
                                     data=self._model.getDWI(),
                                     sphere=default_sphere,
                                     relative_peak_threshold=0.8,
                                     min_separation_angle=45,
                                     mask=self._mask)
            sl = Streamlines(ParticleFilteringTracking(direction_getter=peaks,
                                                       stopping_criterion=self._stopping,
                                                       seeds=seeds,
                                                       affine=affine,
                                                       step_size=self._stepsize))
            return SisypheStreamlines(sl)
        # Deterministic Closest peak direction
        elif self._alg == _DCPD:
            if not self._model.isFitted(): self._model.computeFitting()
            pmf = self._model.getFittedModel().odf(small_sphere).clip(min=0)
            peaks = ClosestPeakDirectionGetter.from_pmf(pmf,
                                                        max_angle=30.0,
                                                        sphere=small_sphere)
            sl = Streamlines(LocalTracking(direction_getter=peaks,
                                           stopping_criterion=self._stopping,
                                           seeds=seeds,
                                           affine=affine,
                                           step_size=self._stepsize))
            return SisypheStreamlines(sl)
        # Deterministic fiber orientation distribution
        elif self._alg == _DFOD:
            if not self._model.isFitted(): self._model.computeFitting()
            if isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                peaks = DeterministicMaximumDirectionGetter.from_shcoeff(self._model.getFittedModel().shm_coeff,
                                                                         max_angle=30.0,
                                                                         sphere=default_sphere)
            else:
                pmf = self._model.getFittedModel().odf(small_sphere).clip(min=0)
                peaks = DeterministicMaximumDirectionGetter.from_pmf(pmf,
                                                                     max_angle=30.0,
                                                                     sphere=small_sphere)
            sl = Streamlines(LocalTracking(direction_getter=peaks,
                                           stopping_criterion=self._stopping,
                                           seeds=seeds,
                                           affine=affine,
                                           step_size=self._stepsize))
            return SisypheStreamlines(sl)
        # Probabilistic Bootstrap direction
        elif self._alg == _PBSD:
            peaks = BootDirectionGetter.from_data(self._model.getDWI(),
                                                  self._model.getModel(),
                                                  max_angle=30.0,
                                                  sphere=small_sphere)
            sl = Streamlines(LocalTracking(direction_getter=peaks,
                                           stopping_criterion=self._stopping,
                                           seeds=seeds,
                                           affine=affine,
                                           step_size=self._stepsize))
            return SisypheStreamlines(sl)
        # Probabilistic fiber orientation distribution
        elif self._alg == _PFOD:
            if not self._model.isFitted(): self._model.computeFitting()
            pmf = self._model.getFittedModel().odf(small_sphere).clip(min=0)
            peaks = ProbabilisticDirectionGetter.from_pmf(pmf,
                                                          max_angle=30.0,
                                                          sphere=small_sphere)
            sl = Streamlines(LocalTracking(direction_getter=peaks,
                                           stopping_criterion=self._stopping,
                                           seeds=seeds,
                                           affine=affine,
                                           step_size=self._stepsize))
            return SisypheStreamlines(sl)
