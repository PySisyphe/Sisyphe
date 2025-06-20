"""
External packages/modules
-------------------------

    - DIPY, MR diffusion image processing, https://www.dipy.org/
    - Numpy, scientific computing, https://numpy.org/
    - pandas, data structures and data analysis tools, https://pandas.pydata.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - scipy, scientific computing, https://scipy.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Callable

import os
from os import getcwd
from os.path import abspath
from os.path import dirname
from os.path import basename
from os.path import join
from os.path import exists
from os.path import splitext

import cython

from math import sqrt
from math import cos
from math import radians

from hashlib import md5

from xml.dom import minidom

# noinspection PyProtectedMember
from dipy.data import default_sphere
# noinspection PyProtectedMember
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
from dipy.align.streamlinear import whole_brain_slr
from dipy.io.utils import create_tractogram_header
from dipy.io.stateful_tractogram import Origin
from dipy.io.stateful_tractogram import Space
from dipy.io.stateful_tractogram import StatefulTractogram
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
from dipy.tracking.distances import minimum_closest_distance
from dipy.tracking.distances import bundles_distances_mam
from dipy.tracking.distances import bundles_distances_mdf
# < Revision 07/03/2025
# from dipy.tracking.metrics import set_number_of_points
# Revision 07/03/2025 >
from dipy.tracking.streamlinespeed import compress_streamlines
from dipy.tracking.streamlinespeed import set_number_of_points
from dipy.tracking.streamline import values_from_volume
from dipy.tracking.streamline import unlist_streamlines
from dipy.tracking.streamline import relist_streamlines
from dipy.tracking.streamline import transform_streamlines
from dipy.tracking.streamline import Streamlines
from dipy.tracking.utils import density_map
from dipy.tracking.utils import path_length
from dipy.tracking.utils import connectivity_matrix
from dipy.tracking.utils import streamline_near_roi
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
from dipy.direction import peaks_from_model
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
from dipy.reconst.shm import SphHarmFit
from dipy.reconst.odf import gfa
from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel
from dipy.reconst.csdeconv import auto_response_ssst
from dipy.tracking.utils import seeds_from_mask
from dipy.tracking.tracker import eudx_tracking
from dipy.tracking.tracker import deterministic_tracking
from dipy.tracking.tracker import ptt_tracking
from dipy.tracking.tracker import closestpeak_tracking
from dipy.tracking.tracker import bootstrap_tracking
from dipy.tracking.tracker import probabilistic_tracking
from dipy.tracking.stopping_criterion import ActStoppingCriterion
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion

from Sisyphe.lib.dipy.streamline import cluster_confidence

from numpy import iinfo
from numpy import array
from numpy import finfo
from numpy import any
from numpy import abs
from numpy import sign
from numpy import dot
from numpy import sqrt
from numpy import eye
from numpy import ones
from numpy import diag
from numpy import stack
from numpy import matmul
from numpy import ndarray
from numpy import asarray
from numpy import allclose
from numpy import frombuffer
from numpy import median
from numpy import histogram
from numpy import percentile
from numpy.linalg import norm

from pandas import DataFrame

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from scipy.stats import describe

from vtk import vtkRenderer
from vtk import vtkFloatArray
from vtk import vtkActor
from vtk import vtkPoints
from vtk import vtkPolyLineSource
from vtk import vtkLookupTable
from vtk import vtkPolyData
from vtk import vtkPolyDataMapper
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.numpy_interface.dataset_adapter import numpyTovtkDataArray

from Sisyphe.core.sisypheConstants import getID_ICBM152
from Sisyphe.core.sisypheConstants import getShape_ICBM152
from Sisyphe.core.sisypheDicom import loadBVal
from Sisyphe.core.sisypheDicom import loadBVec
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
# from Sisyphe.lib.dipy.peaks import peaks_from_model
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheTransform import SisypheTransform


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
           'SisypheDSIDModel',
           'SisypheTracking']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheTract
             -> SisypheTractCollection
             -> SisypheBundle
             -> SisypheBundleCollection
             -> SisypheStreamlines
             -> SisypheDiffusionModel
             -> SisypheDiffusionModel -> SisypheDTIModel
             -> SisypheDiffusionModel -> SisypheDKIModel
             -> SisypheDiffusionModel -> SisypheSHCSAModel
             -> SisypheDiffusionModel -> SisypheSHCSDModel
             -> SisypheDiffusionModel -> SisypheDSIModel
             -> SisypheDiffusionModel -> SisypheDSIDModel
             -> SisypheTracking
"""

listint = list[int]
tuple3int = tuple[int, int, int]
listfloat = list[float]
tuple3float = tuple[float, float, float]
tuple4float = tuple[float, float, float, float]
vector3float = list[float] | tuple3float
vector3int = list[int] | tuple3int


class SisypheTract(object):
    """
    Description
    ~~~~~~~~~~~

    Class to manage streamline display (tract).

    This class manages display attributes of tracts:

        - Color representation

            - RGB mode, colors derived from unit vector directed to next point of the tract
            - CMAP mode, colors derived from scalar values associated with points using the look-up table colormap attribute
            - COLOR mode, solid color given by the color attribute

        - Color, used in COLOR mode
        - Look-up table colormap, used in CMAP mode
        - Line width
        - Visibility
        - Opacity

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTract

    Creation: 26/10/2023
    Last revision: 21/02/2025
    """

    __slots__ = ['_polydata', '_mapper', '_actor', '_scalarnames', '_lut']

    # Class constants

    _RGB = 0
    _CMAP = 1
    _COLOR = 2
    _REPTYPE = (_RGB, _CMAP, _COLOR)

    # Special method

    """
    Private attributes

    _lut            SisypheLut, bundle colormap
    _polydata       vtkPolyData
    _mapper         vtkPolyDataMapper
    _actor          vtkActor
    _scalarnames    dict[str, bool]
    """

    def __init__(self) -> None:
        """
        SisypheTract instance constructor.
        """
        super().__init__()

        self._polydata: vtkPolyData | None = None
        self._mapper = vtkPolyDataMapper()
        self._actor = vtkActor()
        self._actor.SetMapper(self._mapper)
        self._actor.SetObjectName('streamline')
        self._scalarnames: dict[str, bool] | None = None
        self._lut: SisypheLut | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheTract instance to str
         """
        if self._polydata is None: n = 0
        else: n = self._polydata.GetNumberOfPoints()
        buff = 'Points count: {}\n'.format(n)
        buff += 'Color representation: {}\n'.format(self.getColorRepresentationAsString())
        buff += 'Color: r {0[0]:.2} g {0[1]:.2} b {0[2]:.2}\n'.format(self.getFloatColor())
        buff += 'Scalars:\n'
        for name in self._scalarnames:
            buff += '\t{}\n'.format(name)
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTract instance representation
        """
        return 'SisypheBundle instance at <{}>\n'.format(str(id(self))) + self.__str__()

    def __del__(self):
        """
        Special overloaded method called by the built-in del() python function.
        """
        if self._polydata is not None: del self._polydata
        if self._mapper is not None: del self._mapper
        if self._actor is not None: del self._actor
        if self._scalarnames is not None: del self._scalarnames
        if self._lut is not None: del self._lut

    # Private method

    def _updatePolydata(self) -> None:
        if self._polydata is not None:
            self._mapper.SetInputData(self._polydata)
            self._mapper.UpdateInformation()
            # noinspection PyArgumentList
            self._mapper.Update()

    # Public methods

    def deepCopy(self) -> SisypheTract:
        """
        Deep copy of the current SisypheTract instance.

        Returns
        -------
            SisypheTract
                deep copy of tract
        """
        r = SisypheTract()
        if self._polydata is not None:
            r._polydata = vtkPolyData()
            r._polydata.DeepCopy(self._polydata)
            r._updatePolydata()
            r._scalarnames = self._scalarnames
            if self._lut is not None:
                r._lut = self._lut.copy()
            r.setColorRepresentation(self.getColorRepresentation())
            r.setFloatColor(self.getFloatColor(), update=False)
            r.setOpacity(self.getOpacity())
            r.setVisibility(self.getVisibility())
        return r

    def clear(self) -> None:
        """
        Clear the current SisypheTract instance.
        """
        self._mapper = vtkPolyDataMapper()
        self._actor = vtkActor()
        self._actor.SetObjectName('streamline')
        self._actor.SetMapper(self._mapper)
        self._polydata = None
        self._scalarnames = None
        self._lut = None

    def isEmpty(self) -> bool:
        """
        Check whether the current SisypheTract instance is empty (no point)

        Returns
        -------
            bool
                True if empty
        """
        return self._polydata is None

    def setPoints(self, sl: ndarray, reg: bool = True) -> None:
        """
        Set the tract points of the current SisypheTract instance.

        Parameters
        ----------
        sl : ndarray
            streamline of n points, shape(n, 3)
        reg : bool
            regular step between points of the streamline
        """
        # Points
        points = vtkPoints()
        points.SetData(numpyTovtkDataArray(sl))
        polyline = vtkPolyLineSource()
        polyline.SetPoints(points)
        polyline.ClosedOff()
        # noinspection PyArgumentList
        polyline.Update()
        self._polydata = polyline.GetOutput()
        if len(sl) > 1:
            # RGB scalars
            s = abs(sl[0:-1] - sl[1:])
            if reg:
                # regular step
                # noinspection PyUnresolvedReferences
                step = sqrt(s[0] ** 2).sum()
                if abs(step - 1.0) > finfo('float32').eps:
                    # step != 1.0 mm
                    s = s / step
            else:
                # non-regular step, compressed streamline
                ss = sqrt((s ** 2).sum(axis=1))
                s = diag(1 / ss) @ s
        else: s = array([1.0, 0.0, 0.0])
        scalars = numpyTovtkDataArray(s)
        scalars.SetName('RGB')
        self._scalarnames = {'RGB': True, 'volume': False}
        self._polydata.GetPointData().SetScalars(scalars)
        self._polydata.GetPointData().SetActiveScalars('RGB')
        self._mapper.SetScalarModeToUsePointData()
        self._mapper.SetColorModeToDirectScalars()
        self._updatePolydata()

    def setScalarsFromVolume(self, vol: SisypheVolume) -> None:
        """
        Set scalar values associated to each point of the current SisypheTract instance from a
        Sisyphe.core.sisypheVolume.SisypheVolume instance. The value associated with a point of the tract is the scalar
        value of the SisypheVolume voxel at the coordinates of that point.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            reference volume
        """
        if self._polydata is not None:
            # Remove previous scalars
            if self._polydata.GetPointData().HasArray('volume'):
                self._polydata.GetPointData().RemoveArray('volume')
            # Add new scalars
            img = vol.getSITKImage()
            n = self._polydata.GetNumberOfPoints()
            points = self._polydata.GetPoints()
            scalars = vtkFloatArray()
            scalars.SetNumberOfComponents(1)
            scalars.SetNumberOfTuples(n)
            scalars.SetName('volume')
            for name in self._scalarnames:
                self._scalarnames[name] = name == 'volume'
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(n):
                p = points.GetPoint(i)
                p2 = vol.getVoxelCoordinatesFromWorldCoordinates(p)
                scalars.SetTuple1(i, float(img[p2[0], p2[1], p2[2]]))
            self._polydata.GetPointData().AddArray(scalars)
            self._polydata.GetPointData().SetActiveScalars('volume')
            self.setLut(vol.display.getLUT())
            self._updatePolydata()

    def setFloatColor(self, c: vector3float, update: bool = False) -> None:
        """
        Set the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[float, float, float] | list[float, float, float]
            color red, green, blue (each component between 0.0 and 1.0)
        update : bool
            update color representation to solid color
        """
        if self._polydata is not None:
            self._actor.GetProperty().SetColor(c[0], c[1], c[2])
            if update:
                self._mapper.ScalarVisibilityOff()
                self._mapper.UpdateInformation()
                # noinspection PyArgumentList
                self._mapper.Update()

    def setIntColor(self, c: vector3int, update: bool = False) -> None:
        """
        Set the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[int, int, int] | list[int, int, int]
            color red, green, blue (each component between 0 and 255)
        update : bool
            update color representation to solid color
        """
        if self._polydata is not None:
            self.setFloatColor([v / 255.0 for v in c], update)

    def setQColor(self, c: QColor, update: bool = False) -> None:
        """
        Set the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            color
        update : bool
            update color representation to solid color
        """
        if self._polydata is not None:
            self.setFloatColor([c.redF(), c.greenF(), c.blueF()], update)

    def getFloatColor(self) -> vector3float:
        """
        Get the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        tuple[float, float, float] | list[float, float, float]
            color red, green, blue (each component between 0.0 and 1.0)
        """
        if self._polydata is not None:
            return self._actor.GetProperty().GetColor()
        else: raise AttributeError('Polydata attribute is None.')

    def getIntColor(self) -> vector3int:
        """
        Get the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        tuple[int, int, int] | list[int, int, int]
            color red, green, blue (each component between 0 and 255)
        """
        if self._polydata is not None:
            color = self._actor.GetProperty().GetColor()
            return [int(c*255) for c in color]
        else: raise AttributeError('Polydata attribute is None.')

    def getQColor(self) -> QColor:
        """
        Get the color attribute of the current SisypheTract instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        PyQt5.QtGui.QColor
            tract color
        """
        if self._polydata is not None:
            color = self._actor.GetProperty().GetColor()
            c = QColor()
            c.setRgbF(color[0], color[1], color[2])
            return c
        else: raise AttributeError('Polydata attribute is None.')

    def setLut(self, lut: str | SisypheVolume | SisypheLut | vtkLookupTable | None = None, update: bool = False) -> None:
        """
        Set the look-up table colormap attribute of the current SisypheTract instance. The look-up table colormap
        attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        lut : str | Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheLUT.SisypheLut | vtk.vtkLookupTable | None
            if None, set a default look-up table colormap (hot)
        update : bool
            update color representation to color map
        """
        if lut is None:
            self._lut = SisypheLut()
            self._lut.setLutToHot()
            lut = self._lut.getvtkLookupTable()
        elif isinstance(lut, SisypheVolume):
            self._lut = lut.display.getLUT()
            lut = self._lut.getvtkLookupTable()
        elif isinstance(lut, SisypheLut):
            self._lut = lut
            lut = lut.getvtkLookupTable()
        elif isinstance(lut, str):
            self._lut = SisypheLut()
            self._lut.setLut(lut)
            lut = self._lut.getvtkLookupTable()
        if isinstance(lut, vtkLookupTable):
            self._mapper.SetLookupTable(lut)
            if update:
                self._mapper.SetScalarModeToUsePointData()
                self._mapper.SetColorModeToMapScalars()
                self._mapper.UseLookupTableScalarRangeOff()
                # noinspection PyArgumentList
                self._mapper.SetScalarRange(lut.GetRange())
                self._mapper.ScalarVisibilityOn()
                self._mapper.UpdateInformation()
                # noinspection PyArgumentList
                self._mapper.Update()
        else: raise TypeError('parameter type {} is not str, vtkLookupTable, SisypheLut or SisypheVolume.'.format(type(lut)))

    def getLut(self) -> SisypheLut:
        """
        Get the look-up table colormap attribute of the current SisypheTract instance. The look-up table colormap
        attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Returns
        -------
        Sisyphe.core.sisypheLUT.SisypheLut
            tract lut
        """
        return self._lut

    def setColorRepresentation(self, r: int) -> None:
        """
        Set the tract representation attribute of the current SisypheTract instance.

        Parameters
        ----------
        r : int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component in
                red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current SisypheTract instance.
                - 2, COLOR mode, solid color given by the color attribute of the current SisypheTract instance.
        """
        if r == self._RGB:
            self._mapper.ScalarVisibilityOn()
            self._mapper.SetScalarModeToUsePointData()
            self._mapper.SetColorModeToDirectScalars()
            self._polydata.GetPointData().SetActiveScalars('RGB')
            for name in self._scalarnames:
                self._scalarnames[name] = (name == 'RGB')
        elif r == self._CMAP:
            for name in self._scalarnames:
                if self._scalarnames[name] is True:
                    if name == 'volume':
                        if not self._polydata.GetPointData().HasArray('volume'): name = 'RGB'
                    if self._lut is None: self.setLut()
                    self._mapper.ScalarVisibilityOn()
                    self._mapper.SetColorModeToMapScalars()
                    self._mapper.SetScalarModeToUsePointData()
                    self._polydata.GetPointData().SetActiveScalars(name)
                    break
        elif r == self._COLOR:
            self._mapper.ScalarVisibilityOff()
        self._mapper.UpdateInformation()
        # noinspection PyArgumentList
        self._mapper.Update()

    # noinspection PyTypeChecker
    def getColorRepresentation(self) -> int:
        """
        Get the tract representation attribute of the current SisypheTract instance.

        Returns
        -------
        int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component in
                red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current SisypheTract instance.
                - 2, COLOR mode, solid color given by the color attribute of the current SisypheTract instance.
        """
        if self._mapper.GetScalarVisibility() > 0:
            for name in self._scalarnames:
                if self._scalarnames[name] is True:
                    if name == 'RGB': return self._RGB
                    else: return self._CMAP
        else: return self._COLOR

    def setColorRepresentationAsString(self, r: str) -> None:
        """
        Set the tract representation attribute of the current SisypheTract instance from a str.

        Parameters
        ----------
        r : str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current SisypheTract instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current SisypheTract instance.
        """
        r = r.lower()
        if r == 'rgb': self.setColorRepresentation(0)
        elif r == 'scalars': self.setColorRepresentation(1)
        elif r == 'color': self.setColorRepresentation(2)

    # noinspection PyTypeChecker
    def getColorRepresentationAsString(self) -> str:
        """
        Get the tract representation attribute of the current SisypheTract instance from a str.

        Returns
        -------
        str
            representation code
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current SisypheTract instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current SisypheTract instance.
        """
        r = self.getColorRepresentation()
        if r == 0: return 'rgb'
        elif r == 1: return 'scalars'
        elif r == 2: return 'color'
        else: raise ValueError('Invalid representation code.')

    def setColorRepresentationToRGB(self) -> None:
        """
        Set the tract representation attribute of the current SisypheTract instance to RGB mode. Colors are derived
        from unit vector directed to next point of the tract (x-axis component in red, y-axis component in green and
        z-axis component in blue).
        """
        self.setColorRepresentation(self._RGB)

    def setColorRepresentationToScalars(self) -> None:
        """
        Set the tract representation attribute of the current SisypheTract instance to SCALARS mode. Colors are derived
        from scalar values associated with points using the look-up table colormap attribute of the current
        SisypheTract instance.
        """
        self.setColorRepresentation(self._CMAP)

    def setColorRepresentationToColor(self) -> None:
        """
        Set the tract representation attribute of the current SisypheTract instance to COLOR mode. The tract has a
        solid color given by the color attribute of the current SisypheTract instance.
        """
        self.setColorRepresentation(self._COLOR)

    def isRGBRepresentation(self) -> bool:
        """
        Check whether the tract representation of the current SisypheTract instance is in RGB mode. Colors are derived
        from unit vector directed to next point of the tract (x-axis component in red, y-axis component in green and
        z-axis component in blue).

        Returns
        -------
            bool
                True if RGB representation
        """
        return self.getColorRepresentation() == self._RGB

    def isScalarsRepresentation(self) -> bool:
        """
        Check whether the tract representation of the current SisypheTract instance is in SCALARS mode. Colors are
        derived from scalar values associated with points using the look-up table colormap attribute of the current
        SisypheTract instance.

        Returns
        -------
            bool
                True if scalrs representation
        """
        return self.getColorRepresentation() == self._CMAP

    def isColorRepresentation(self) -> bool:
        """
        Check whether the tract representation of the current SisypheTract instance is in COLOR mode. The tract has a
        solid color given by the color attribute of the current SisypheTract instance.

        Returns
        -------
            bool
                True if color representation
        """
        return self.getColorRepresentation() == self._COLOR

    def setActiveScalars(self, sc: str) -> None:
        """
        Set the name of the active scalar value associated with points in the current SisypheTract instance.

        Parameters
        ----------
            sc : str
                scalar value name
        """
        if sc in self._scalarnames:
            for name in self._scalarnames:
                self._scalarnames[name] = (name == sc)
                self._polydata.GetPointData().SetActiveScalars(sc)
        else: raise ValueError('Invalid scalar name.')

    # noinspection PyTypeChecker
    def getActiveScalars(self) -> str | None:
        """
        Get the name of the active scalar value associated with points in the current SisypheTract instance.

        Returns
        -------
        str | None
            scalar value name
        """
        for name in self._scalarnames:
            if self._scalarnames[name] is True: return name
        return None

    def getScalarNames(self) -> list[str]:
        """
        Get a list of scalar value names associated with points in the current SisypheTract instance.

        Returns
        -------
        list[str]
            scalar value names
        """
        return list(self._scalarnames.keys())

    def hasScalarNames(self) -> bool:
        """
        Check whether the current SisypheTract instance has associated scalar values.

        Returns
        -------
        bool
            True if scalar values are defined
        """
        return len(self._scalarnames) > 0

    def getPolyData(self) -> vtkPolyData:
        """
        Get the vtk.vtkPolyData attribute of the current SisypheTract instance.

        Returns
        -------
        vtk.vtkPolyData
            vtkPolydata tract
        """
        return self._polydata

    def getActor(self) -> vtkActor:
        """
        Get the vtk.vtkActor attribute of the current SisypheTract instance.

        Returns
        -------
        vtk.vtkActor
            vtkActor tract
        """
        return self._actor

    def getPoints(self) -> ndarray:
        """
        Get the tract points of the current SisypheTract instance.

        Returns
        -------
        ndarray
            shape(n, 3), n points.
        """
        if self._polydata is not None:
            return vtk_to_numpy(self._polydata.GetPoints())
        else: raise AttributeError('Polydata attribute is None.')

    # noinspection PyTypeChecker
    def getVisibility(self) -> bool:
        """
        Get the visibility attribute of the current SisypheTract instance.

        Returns
        -------
        bool
            True if visible
        """
        if self._actor is not None: return self._actor.GetVisibility() > 0
        else: raise AttributeError('_actor attribute is None.')

    def setVisibility(self, v: bool):
        """
        Set the visibility attribute of the current SisypheTract instance.

        Parameters
        ----------
        v : bool
            True if visible
        """
        self._actor.SetVisibility(v)

    def visibilityOn(self) -> None:
        """
        Show the current SisypheTract instance (set the visibility attribute to True).
        """
        # < Revision 21/02/2025
        # self._polydata.VisibilityOn()
        self._actor.SetVisibility(True)
        # Revision 21/02/2025 >

    def visibilityOff(self) -> None:
        """
        Hide the current SisypheTract instance (set the visibility attribute to False).
        """
        # < Revision 21/02/2025
        # self._polydata.VisibilityOn()
        self._actor.SetVisibility(False)
        # Revision 21/02/2025 >

    def getOpacity(self) -> float:
        """
        Get the opacity attribute of the current SisypheTract instance.

        Returns
        -------
        float
            opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        return self._actor.GetProperty().GetOpacity()

    def setOpacity(self, v: float):
        """
        Set the opacity attribute of the current SisypheTract instance.

        Parameters
        ----------
        v : float
            opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        self._actor.GetProperty().SetOpacity(v)

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current SisypheTract instance in mm.

        Returns
        -------
        float
            line width in mm
        """
        return self._actor.GetProperty().GetLineWidth()

    def setLineWidth(self, v: float):
        """
        Set the line width attribute of the current SisypheTract instance in mm.

        Parameters
        ----------
        v : float
            line width in mm
        """
        self._actor.GetProperty().SetLineWidth(v)


class SisypheTractCollection(object):
    """
    Description
    ~~~~~~~~~~~

    Named (bundel name) list container of SisypheTract instances.
    Container Key = tuple[str, int], str bundle name, int index of a SisypheTract in the bundle

    This class manages display attributes of bundles:

        - Color representation

            - RGB mode, colors derived from unit vector directed to next point of the tract
            - CMAP mode, colors derived from scalar values associated with points using the look-up table colormap attribute
            - COLOR mode, solid color given by the color attribute

        - Color, used in COLOR mode
        - Look-up table colormap, used in CMAP mode
        - Line width
        - Visibility
        - Opacity

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTractCollection

    Creation: 26/10/2023
    Last revision: 20/02/2025
    """

    __slots__ = ['_bundles', '_renderer']

    # Special methods

    """
    Private attributes
    
    _bundles    dict[str, list[SisypheTract]]
    _renderer   vtkRenderer
    """

    def __init__(self) -> None:
        """
        SisypheTractCollection instance constructor.
        """
        self._bundles: dict[str, list[SisypheTract]] = dict()
        self._renderer: vtkRenderer | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of SisypheTractCollection instance to str
        """
        buff = 'Bundle count: {}\n'.format(len(self._bundles))
        for bundle in self._bundles:
            buff += 'Bundle {}: {} tracts\n'.format(bundle, len(self._bundles[bundle]))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTractCollection instance representation
        """
        return 'SisypheTractCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __getitem__(self, key: tuple[str, int]) -> SisypheTract:
        """
        Special overloaded container getter method. Get a SisypheTract element from container.

        Parameters
        ----------
        key : tuple[str, int]
            Container key, bundle name str and tract index int

        Returns
        -------
        SisypheTract
            container element
        """
        bundle = key[0]
        index = key[1]
        if isinstance(bundle, str) and isinstance(index, int):
            if bundle in self._bundles:
                if 0 <= index < len(self._bundles[bundle]):
                    return self._bundles[bundle][index]
                else: raise IndexError('tract index key is out of range.')
            else: raise IndexError('invalid bundle name key.')
        else: raise TypeError('key type ({}, {}) is not (str, int).'.format(type(bundle), type(index)))

    def __setitem__(self, key: tuple[str, int], value: SisypheTract) -> None:
        """
        Special overloaded container setter method. Set a SisypheTract element in the container.

        Parameters
        ----------
        key : tuple[str, int]
            Container key, bundle name str and tract index int
        value : SisypheTract
            tract to be placed at key position
        """
        if isinstance(value, SisypheTract):
            bundle = key[0]
            index = key[1]
            if isinstance(bundle, str) and isinstance(index, int):
                if bundle in self._bundles:
                    if 0 <= index < len(self._bundles[bundle]):
                        self._bundles[bundle][index] = value
                    else: raise IndexError('tract index key is out of range.')
                else: raise IndexError('invalid bundle name key.')
            else: raise TypeError('key type ({}, {}) is not (str, int).'.format(type(bundle), type(index)))

    def __delitem__(self, key: tuple[str, int]) -> None:
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheTract element of the
        container.

        Parameters
        ----------
        key : tuple[str, int]
            Container key, bundle name str and tract index int
        """
        bundle = key[0]
        index = key[1]
        if isinstance(bundle, str) and isinstance(index, int):
            if bundle in self._bundles:
                if 0 <= index < len(self._bundles[bundle]):
                    del self._bundles[bundle][index]
                else: raise IndexError('tract index key is out of range.')
            else: raise IndexError('invalid bundle name key.')
        else: raise TypeError('key type ({}, {}) is not (str, int).'.format(type(bundle), type(index)))

    def __len__(self) -> int:
        """
        Special overloaded method called by the built-in len() python function. Returns the number of SisypheTract
        elements in the container.

        Returns
        -------
        int
            Number of SisypheTract elements
        """
        return self.count()

    # Private method

    def _getNewName(self, name: str) -> str:
        while name in self._bundles:
            parts = name.split('#')
            suffix = parts[-1]
            if suffix.isdigit():
                suffix = int(suffix) + 1
                parts[-1] = str(suffix)
            else: parts.append('1')
            name = '#'.join(parts)
        return name

    # Public methods

    def count(self) -> int:
        """
         Get the global number of SisypheTract elements in the current SisypheTractCollection instance container.

        Returns
        -------
        int
            Number of SisypheTract elements
        """
        n = 0
        if len(self._bundles) > 0:
            for bundle in self._bundles:
                n += len(self._bundles[bundle])
        return n

    def bundleCount(self) -> int:
        """
         Get the number of bundles in the current SisypheTractCollection instance container.

        Returns
        -------
        int
            Number of bundles
        """
        return len(self._bundles)

    def tractCount(self, bundle: str = '') -> int:
        """
        Get the number of SisypheTract elements in a bundle of the current SisypheTractCollection instance container.

        Parameters
        ----------
        bundle : str
            Bundle name, if bundle = '', returns the global number of tracts.

        Returns
        -------
        int
            Number of SisypheTract elements in the bundle
        """
        if len(self._bundles) > 0:
            if bundle == '': return self.count()
            elif bundle in self._bundles:
                return len(self._bundles[bundle])
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isEmpty(self) -> bool:
        """
        Check if SisypheTractCollection instance container is empty.

        Returns
        -------
        bool
            True if empty
        """
        return self.count() == 0

    def clear(self) -> None:
        """
        Remove all elements from the current SisypheTractCollection instance container (empty).
        """
        self._bundles = dict()

    def getDict(self) -> dict[str: list[SisypheTract]]:
        """
        Get the current SisypheTractCollection instance container as dict (Shallow copy).

        Returns
        -------
        dict[str: list[SisypheTract]]
            - str dict key, bundle name
            - list[SisypheTract] dict value
        """
        return self._bundles

    def getBundleNames(self) -> list[str]:
        """
        Get the bundle names in the current SisypheTractCollection instance container.

        Returns
        -------
            list[str]
                list of bundle names
        """
        return list(self._bundles.keys())

    def setRenderer(self, r: vtkRenderer | None):
        """
        Define the renderer in which the current SisypheTractCollection is displayed.

        Parameters
        ----------
        r : vtkRenderer | None
            renderer
        """
        self._renderer = r

    def getRenderer(self) -> vtkRenderer | None:
        """
        Get the renderer in which the current SisypheTractCollection is displayed.

        Returns
        -------
        vtkRenderer | None
            renderer
        """
        return self._renderer

    def hasRenderer(self) -> bool:
        """
        Check whether a renderer has been defined to display the current SisypheTractCollection.

        Returns
        -------
        bool
            True if renderer is defined i.e. not None
        """
        return self._renderer is not None

    # Public bundle methods

    def appendBundle(self,
                     sl: SisypheStreamlines,
                     bundle: str,
                     wait: DialogWait | None = None) -> None:
        """
        Append streamlines to the current SisypheTractCollection instance container. These streamlines belong to a
        bundle identified by a bundle name given as parameter.

        Parameters
        ----------
        sl : SisypheStreamlines
        bundle : str
            Bundle name
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            Progress bar dialog
        """
        if bundle in ('', 'all', 'tractogram'):
            bundle = 'bundle#{}'.format(len(self._bundles))
            sl.setName(bundle)
        if bundle not in self._bundles:
            if bundle != sl.getName(): sl = sl.getSisypheStreamlinesFromBundle(bundle)
            rep = sl.getColorRepresentation(bundle)
            lut = sl.getLut(bundle)
            c = sl.getFloatColor(bundle)
            opacity = sl.getOpacity(bundle)
            width = sl.getLineWidth(bundle)
            # noinspection PyUnresolvedReferences
            i: cython.int
            # noinspection PyUnresolvedReferences
            j: cython.int = 0
            n = len(sl)
            self._bundles[bundle] = list()
            if wait is not None: wait.setProgressVisibility(n > 100)
            for i in range(n):
                tract = SisypheTract()
                tract.setPoints(sl[i], reg=sl.hasRegularStep())
                tract.setLut(lut, update=False)
                tract.setFloatColor(c, update=False)
                tract.setColorRepresentation(rep)
                tract.setOpacity(opacity)
                tract.setLineWidth(width)
                self._bundles[bundle].append(tract)
                if self._renderer is not None:
                    self._renderer.AddActor(tract.getActor())
                if wait is not None:
                    j += 1
                    if j == 100:
                        j = 0
                        wait.setCurrentProgressValuePercent(i / n, None)
            if self._renderer is not None:
                self._renderer.GetRenderWindow().Render()
        else: raise ValueError('{} bundle is already in {}'.format(bundle, self.__class__.__name__))

    def duplicateBundle(self,
                        sl: SisypheStreamlines,
                        select: SisypheBundle | None = None) -> SisypheStreamlines:
        """
        Duplicate a selection of streamlines belonging to a bundle of the current SisypheTractCollection instance
        container. The new bundle is called with the name attribute of the select instance (SisypheBundle parameter)

        Parameters
        ----------
        sl : SisypheStreamlines
        select : SisypheBundle | None
            streamlines duplicated in the new bundle. If None (default), no streamline selection (all streamlines are duplicated)

        Returns
        -------
        SisypheStreamlines
            Streamlines of the new bundle
        """
        bundle = sl.getName()
        if bundle in self._bundles:
            if select is None or select.count() == sl.count(): r = SisypheStreamlines(sl=sl.getStreamlines())
            else: r = SisypheStreamlines(sl=sl.getStreamlines()[select.getList()])
            r.copyAttributesFrom(sl)
            r.setName(select.getName())
            tracts = list()
            if select is None:
                select = SisypheBundle()
                select.appendTracts(list(range(sl.count())))
                select.setName(self._getNewName(bundle))
            for idx in select:
                tract = self._bundles[bundle][idx].deepCopy()
                tract.visibilityOn()
                tracts.append(tract)
                if self._renderer is not None:
                    self._renderer.AddActor(tract.getActor())
            self._bundles[select.getName()] = tracts
            if self._renderer is not None:
                self._renderer.GetRenderWindow().Render()
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def updateBundle(self,
                     sl: SisypheStreamlines,
                     select: SisypheBundle) -> SisypheStreamlines:
        """
        Update streamlines belonging to a bundle of the current SisypheTractCollection instance container. The bundle
        updated is the bundle name attribute of the sl instance (SisypheStreamlines parameter)

        Parameters
        ----------
        sl : SisypheStreamlines
            Streamlines of the bundle to update
        select : SisypheBundle
            Streamlines selection of the bundle

        Returns
        -------
        SisypheStreamlines
            Selected streamlines
        """
        bundle = sl.getName()
        if bundle in self._bundles:
            if select.count() < sl.getBundle(0).count():
                # noinspection PyUnresolvedReferences
                i: cython.int
                unselect = sl.getBundle(0) - select
                for i in range(unselect.count()-1, -1, -1):
                    tract = self._bundles[bundle].pop(unselect[i])
                    if self._renderer is not None:
                        self._renderer.RemoveActor(tract.getActor())
                    del tract
                if self._renderer is not None:
                    self._renderer.GetRenderWindow().Render()
                r = SisypheStreamlines(sl=sl.getStreamlines()[select.getList()])
                r.copyAttributesFrom(sl)
                r.setWholeBrainStatus(False)
                return r
            else: return sl
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def unionBundle(self,
                    bundle: str,
                    lsl: list[SisypheStreamlines],
                    wait: DialogWait | None = None) -> SisypheStreamlines:
        """
        Union of bundles of the current SisypheTractCollection instance container. The bundle updated is the bundle
        name attribute of the sl1 instance (SisypheStreamlines parameter)

        Parameters
        ----------
        bundle : str
            union bundle name
        lsl : list[SisypheStreamlines]
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            Progress bar dialog (optional)

        Returns
        -------
        SisypheStreamlines
            Streamlines union
        """
        r = SisypheStreamlines()
        r.copyAttributesFrom(lsl[0])
        r.setName(bundle)
        r.setWholeBrainStatus(False)
        self._bundles[bundle] = list()
        for sl in lsl:
            if sl.getName() in self._bundles:
                if wait is not None:
                    wait.setInformationText('{} bundle union...'.format(sl.getName()))
                r.append(sl.getStreamlines())
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(sl.count()):
                    tract = self._bundles[sl.getName()][i].deepCopy()
                    self._bundles[bundle].append(tract)
                    if self._renderer is not None:
                        self._renderer.AddActor(tract.getActor())
            else: raise ValueError('invalid bundle name, {} not in current collection.'.format(sl.getName()))
            # noinspection PyUnreachableCode
            if self._renderer is not None:
                # < Revision 21/02/2025
                # self._renderer.updateRender()
                self._renderer.GetRenderWindow().Render()
                # Revision 21/02/2025 >
        return r

    def removeBundle(self, bundle: str = '') -> None:
        """
        Remove a bundle from the current SisypheTractCollection instance container. This bundle is identified by a
        bundle name given as parameter.

        Parameters
        ----------
        bundle : str
            Bundle name. if bundle name is empty, removes the first bundle.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    if self._renderer is not None:
                        self._renderer.RemoveActor(tract.getActor())
                    del tract
                del self._bundles[bundle]
                if self._renderer is not None:
                    self._renderer.GetRenderWindow().Render()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def removeAllBundles(self) -> None:
        """
        Remove all bundles from the current SisypheTractCollection instance container.
        """
        if len(self._bundles) > 0:
            for bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    if self._renderer is not None:
                        self._renderer.RemoveActor(tract.getActor())
                    del tract
                if self._renderer is not None:
                    self._renderer.GetRenderWindow().Render()
            self._bundles.clear()

    def renameBundle(self, old: str, new: str) -> None:
        """
        Rename a bundle of the current SisypheTractCollection instance container.

        Parameters
        ----------
        old : str
            Old bundle name
        new : str
            New bundle name
        """
        if old in self._bundles:
            # < Revision 20/02/2025
            # self._bundles[new] = self._bundles[old]
            # del self._bundles[old]
            self._bundles[new] = self._bundles.pop(old)
            # Revision 20/02/2025 >

    # Representation public methods

    def setScalarsFromVolume(self, vol: SisypheVolume, bundle: str, wait: DialogWait | None = None) -> None:
        """
        Set scalar values associated to each point of the tract elements from a Sisyphe.core.sisypheVolume.SisypheVolume
        instance. The value associated with a point of the tract is the scalar value of the SisypheVolume voxel at the
        coordinates of that point.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
        bundle : str
            Bundle name, if bundle name is empty, the first bundle is selected
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            Progress bar dialog (optional)
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                # noinspection PyUnresolvedReferences
                i: cython.int
                # noinspection PyUnresolvedReferences
                j: cython.int = 0
                n = len(self._bundles[bundle])
                if wait is not None:
                    wait.setProgressRange(0, 100)
                    wait.setProgressVisibility(n > 100)
                for i, tract in enumerate(self._bundles[bundle]):
                    tract.setScalarsFromVolume(vol)
                    if wait is not None:
                        j += 1
                        if j == 100:
                            j = 0
                            wait.setCurrentProgressValuePercent(i / n, None)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getScalarNames(self, bundle: str) -> list[str]:
        """
        Get a list of scalar value names associated with tract points in the current SisypheTractCollection instance.

        Parameters
        ----------
        bundle : str
            Bundle name, if bundle name is empty, the first bundle is selected

        Returns
        -------
        list[str]
            scalar value names
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getScalarNames()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setActiveScalars(self, sc: str, bundle: str = '') -> None:
        """
        Set the name of the active scalar value associated with tract points of a bundle in the current
        SisypheTractCollection instance.

        Parameters
        ----------
        sc : str
            scalar value name
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setActiveScalars(sc)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getActiveScalars(self, bundle: str = '') -> str:
        """
        Get the name of the active scalar value associated with tract points of a bundle in the current
        SisypheTractCollection instance.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected

        Returns
        -------
        str
            scalar value name
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getActiveScalars()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def hasScalars(self,  bundle: str = '') -> bool:
        """
        Check whether the bundle in the current SisypheTractCollection instance has associated scalar values.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected

        Returns
        -------
        bool
            True if scalars are defined
        """
        r = False
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                r = self._bundles[bundle][0].hasScalarNames()
        return r

    def setFloatColor(self, c: vector3float, bundle: str = '') -> None:
        """
        Set the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[float, float, float] | list[float, float, float]
            color red, green, blue (each component between 0.0 and 1.0)
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setFloatColor(c, update=True)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setIntColor(self, c: vector3int, bundle: str = '') -> None:
        """
        Set the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
         c : tuple[int, int, int] | list[int, int, int]
            color red, green, blue (each component between 0 and 255)
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setIntColor(c, update=True)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setQColor(self, c: QColor, bundle: str = '') -> None:
        """
        Set the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setQColor(c, update=True)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getFloatColor(self, bundle: str = '') -> vector3float:
        """
        Get the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        tuple[float, float, float] | list[float, float, float]
            color red, green, blue (each component between 0.0 and 1.0)
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getFloatColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getIntColor(self, bundle: str = '') -> vector3int:
        """
        Get the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        tuple[int, int, int] | list[int, int, int]
            color red, green, blue (each component between 0 and 255)
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getIntColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getQColor(self, bundle: str = '') -> QColor:
        """
        Get the color attribute of a bundle in the current SisypheTractCollection instance. The color attribute is only
        used in COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        PyQt5.QtGui.QColor
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getQColor()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setLut(self, lut: SisypheLut, bundle: str = '') -> None:
        """
        Set the look-up table colormap attribute of a bundle in the current SisypheTractCollection instance. The
        look-up table colormap attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        lut : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheLUT.SisypheLut | vtk.vtkLookupTable
            lut
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setLut(lut)
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getLut(self, bundle: str = '') -> SisypheLut:
        """
        Get the look-up table colormap attribute of a bundle in the current SisypheTractCollection instance.
        The look-up table colormap attribute is only used in CMAP mode representation
        (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        Sisyphe.core.sisypheLUT.SisypheLut
            lut
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getLut()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentation(self, v: int, bundle: str = '') -> None:
        """
        Set the color representation attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        v : int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component in
                red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setColorRepresentation(v)
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getColorRepresentation(self, bundle: str = '') -> int:
        """
        Get the color representation attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component
                in red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getColorRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationAsString(self, v: str, bundle: str = '') -> None:
        """
        Set the color representation attribute of a bundle in the current SisypheTractCollection instance from a str.

        Parameters
        ----------
        v : str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setColorRepresentationAsString(v)
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getColorRepresentationAsString(self, bundle: str = '') -> str:
        """
        Get the color representation attribute of a bundle in the current SisypheTractCollection instance from a str.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getColorRepresentationAsString()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationToRGB(self, bundle: str = '') -> None:
        """
        Set the color representation attribute of a bundle in the current SisypheTractCollection instance to RGB mode.
        Colors are derived from unit vector directed to next point of the tract (x-axis component in red, y-axis
        component in green and z-axis component in blue).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setColorRepresentationToRGB()
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationToScalars(self, bundle: str = '') -> None:
        """
        Set the color representation attribute of a bundle in the current SisypheTractCollection instance to SCALARS
        mode. Colors are derived from scalar values associated with points using the look-up table colormap attribute.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setColorRepresentationToScalars()
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setColorRepresentationToColor(self, bundle: str = '') -> None:
        """
        Set the color representation attribute of the current SisypheTractCollection instance to COLOR mode. The tracts
        have a solid color given by the color attribute.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setColorRepresentationToColor()
                    QApplication.processEvents()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isRGBRepresentation(self, bundle: str = '') -> bool:
        """
        Check whether the color representation of a bundle is in RGB mode. Colors are derived from unit vector directed
        to next point of the tract (x-axis component in red, y-axis component in green and z-axis component in blue).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        bool
            True if RGB representation
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].isRGBRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isScalarsRepresentation(self, bundle: str = '') -> bool:
        """
        Check whether the color representation of a bundle is in SCALARS mode. Colors are derived from scalar values
        associated with points using the look-up table colormap attribute.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        bool
            True if scalars representation
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].isScalarsRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def isColorRepresentation(self, bundle: str = '') -> bool:
        """
        Check whether the color representation of a bundle is in COLOR mode. The tracts have a solid color given by the
        color attribute.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        bool
            True if color representation
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].isColorRepresentation()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setOpacity(self, v: float, bundle: str = '') -> None:
        """
        Set the opacity attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        v : float
            opacity, between 0.0 (transparent) and 1.0 (opaque)
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setOpacity(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getOpacity(self, bundle: str = '') -> float:
        """
        Get the opacity attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        float
            opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getOpacity()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setLineWidth(self, v: float, bundle: str = '') -> None:
        """
        Set the line width attribute of a bundle in the current SisypheTractCollection instance in mm.

        Parameters
        ----------
        v : float
            line width in mm
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setLineWidth(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getLineWidth(self, bundle: str = '') -> float:
        """
        Get the line width attribute of a bundle in the current SisypheTractCollection instance in mm.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        float
            line width in mm
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getLineWidth()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def getVisibility(self, bundle: str = '') -> bool:
        """
        Get the visibility attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.

        Returns
        -------
        bool
            True if visible
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                return self._bundles[bundle][0].getVisibility()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def setVisibility(self, v: bool, bundle: str = ''):
        """
        Set the visibility attribute of a bundle in the current SisypheTractCollection instance.

        Parameters
        ----------
        v : bool
            visibility
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.setVisibility(v)
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def visibilityOn(self, bundle: str = '') -> None:
        """
        Show a bundle of the current SisypheTractCollection instance (set the visibility attribute to True).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.visibilityOn()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))

    def visibilityOff(self, bundle: str = '') -> None:
        """
        Hide a bundle of the current SisypheTractCollection instance (set the visibility attribute to False).

        Parameters
        ----------
        bundle : str
            bundle name, if bundle name is empty, the first bundle is selected.
        """
        if len(self._bundles) > 0:
            if bundle == '': bundle = list(self._bundles.keys())[0]
            if bundle in self._bundles:
                for tract in self._bundles[bundle]:
                    tract.visibilityOff()
            else: raise ValueError('{} invalid bundle name.'.format(bundle))
        else: raise AttributeError('{} is empty.'.format(self.__class__.__name__))


class SisypheBundle(object):
    """
    Description
    ~~~~~~~~~~~

    Container of tracts (streamlines) indices in an associated SisypheStreamlines instance belonging to a bundle. The
    SisypheBundle instance is an attribute of the associated SisypheStreamlines instance.

    Scope of methods:

        - set operators between SisypheBundle instances (union, intersection, difference, symmetric difference)
        - logic operators between SisypheBundle instances (and, or, xor)
        - addBundle and sub arithmetic operators between SisypheBundle instances
        - Color representation

            - RGB mode, colors derived from unit vector directed to next point of the tract
            - CMAP mode, colors derived from scalar values associated with points using the look-up table colormap
            attribute
            - COLOR mode, solid color given by the color attribute

        - Color, used in COLOR mode
        - Look-up table colormap, used in CMAP mode
        - Line width
        - Visibility
        - Opacity

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheBundle

    Creation: 26/10/2023
    Last revision: 10/04/2025
    """

    __slots__ = ['_index', '_name', '_color', '_lut', '_rep', '_width', '_opacity', '_list']

    # Class constants

    _RGB = 0
    _CMAP = 1
    _COLOR = 2
    _REPTYPE = (_RGB, _CMAP, _COLOR)

    # Special methods

    """
    Private attributes

    _index      int, bundle index
    _name       str, bundle name
    _rep        int, bundle representation (0: RGB, 1: CMAP, 3: COLOR)
    _color      list[float, float, float], bundle color
    _lut        SisypheLut, bundle colormap
    _list       list[int], bundle list
    """

    def __init__(self, s: int | vector3int | None = None) -> None:
        """
        SisypheBundle instance constructor.

        Parameters
        ----------
        s : int, list[int] | tuples[int, ...] | None
            - int, streamlines belonging in the bundle, all indices between 0 and s
            - list[int] | tuple[int, ...],
                - s[0] index of the first streamline belonging in the bundle,
                - s[1] streamline count in bundles[2],
                - s[2] step (default 1)
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        self._name: str = ''
        self._color: vector3float = [1.0, 1.0, 1.0]
        self._lut = SisypheLut()
        self._lut.setLutToHot()
        self._rep: int = self._RGB
        self._width = 1.0
        self._opacity = 1.0
        if s is not None:
            if isinstance(s, int): self._list = list(range(s))
            elif isinstance(s, (tuple, list)):
                n = len(s)
                if n == 1: self._list = list(range(s[0]))
                elif n == 2: self._list = list(range(s[0], s[1]))
                else: self._list = list(range(s[0], s[1], s[2]))
        else: self._list: list[int] = list()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of SisypheBundle instance to str
        """
        buff = 'Name: {}\n'.format(self._name)
        buff += '\tTracts count: {}\n'.format(len(self._list))
        buff += '\tRepresentation: {}\n'.format(self.getColorRepresentationAsString())
        r = self.getColorRepresentation()
        if r == self._COLOR: buff += '\tColor: {}\n'.format(self.getFloatColor())
        elif r == self._CMAP: buff += '\tColormap: {}\n'.format(self._lut.getName())
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheBundle instance representation
        """
        return 'SisypheBundle instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __contains__(self, item: int) -> bool:
        """
        Check whether the current SisypheBundle instance contains the index of a tract (streamline) in the associated
        SisypheStreamlines instance.

        Parameters
        ----------
        item : int
            index of a tract (streamline) in the associated SisypheStreamlines instance

        Returns
        -------
        bool
            True if index in container
        """
        return item in self._list

    def __len__(self) -> int:
        """
        Get the number of tracts (streamlines) in the current SisypheBundle instance.

        Returns
        -------
        int
            number of tracts (streamlines)
        """
        return len(self._list)

    def __getitem__(self, key: int) -> int:
        """
        Special overloaded container getter method. Get an element (i.e. index of a tract (streamline) in the
        associated SisypheStreamlines instance) from the container.

        Parameters
        ----------
        key : int
            container index

        Returns
        -------
        int
            index of the tract (streamline) in the associated SisypheStreamlines instance
        """
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._list): return self._list[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(key)))

    def __setitem__(self, key: int, value: int) -> None:
        """
        Special overloaded container getter method. Set an element (i.e. index of a tract (streamline) in the
        associated SisypheStreamlines instance) in the container.

        Parameters
        ----------
        key : int
            container index
        value : int
            index of the tract (streamline) in the associated SisypheStreamlines instance
        """
        if isinstance(value, int):
            if isinstance(key, int):
                if 0 <= key < len(self._list): self._list[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('key parameter type {} is not int.'.format(type(key)))
        else: raise TypeError('value parameter type {} is not int.'.format(type(value)))

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        return self

    def __next__(self) -> int:
        """
        Special overloaded container called by the built-in 'next()' python iterator method.

        Returns
        -------
        int
            Next value for the iterable.
        """
        if self._index < len(self._list):
            n = self._index
            self._index += 1
            return self._list[n]
        else: raise StopIteration

    # Special logic operators

    def __and__(self, other: SisypheBundle) -> SisypheBundle:
        """
        Special overloaded logic operator & (and). self & other -> SisypheBundle.

        Parameters
        ----------
        other : SisypheBundle
            second operand of & operator

        Returns
        -------
        SisypheBundle
            result = self & other
        """
        r = set(self._list) & set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        # < Revision 10/04/2025
        if len(buff._list) > 0: buff._list.sort()
        # Revision 10/04/2025 >
        return buff

    def __or__(self, other: SisypheBundle) -> SisypheBundle:
        """
        Special overloaded logic operator | (or). self | other -> SisypheBundle.

        Parameters
        ----------
        other : SisypheBundle
            second operand of | operator

        Returns
        -------
        SisypheBundle
            result = self | other
        """
        r = set(self._list) | set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        # < Revision 10/04/2025
        if len(buff._list) > 0: buff._list.sort()
        # Revision 10/04/2025 >
        return buff

    def __xor__(self, other: SisypheBundle) -> SisypheBundle:
        """
        Special overloaded logic operator ^ (xor). self ^ other -> SisypheBundle.

        Parameters
        ----------
        other : SisypheBundle
            second operand of ^ operator

        Returns
        -------
        SisypheBundle
            result = self ^ other
        """
        r = set(self._list) ^ set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        # < Revision 10/04/2025
        if len(buff._list) > 0: buff._list.sort()
        # Revision 10/04/2025 >
        return buff

    def __sub__(self, other: SisypheBundle) -> SisypheBundle:
        """
        Special overloaded arithmetic operator -. self - other -> SisypheBundle.

        Parameters
        ----------
        other : SisypheBundle
            second operand of subtraction

        Returns
        -------
        SisypheBundle
            result = self - other
        """
        r = set(self._list) - set(other._list)
        buff = SisypheBundle()
        buff._list = list(r)
        # < Revision 10/04/2025
        if len(buff._list) > 0: buff._list.sort()
        # Revision 10/04/2025 >
        return buff

    def __add__(self, other: SisypheBundle) -> SisypheBundle:
        """
        Special overloaded arithmetic operator +. self + other -> SisypheBundle

        Parameters
        ----------
        other : SisypheBundle
            second operand of addition

        Returns
        -------
        SisypheBundle
            result = self + other
        """
        return self.__or__(other)

    # Public methods

    def setName(self, name: str) -> None:
        """
        Set the name attribute of the current SisypheBundle instance.

        Parameters
        ----------
        name : str
            bundle name
        """
        self._name = name

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheBundle instance.

        Returns
        -------
        str
            bundle name
        """
        return self._name

    def hasName(self) -> bool:
        """
        Check whether the name attribute of the current SisypheBundle instance is defined (not empty).

        Returns
        -------
        bool
            True if name attribute is defined
        """
        return self._name != ''

    def sameName(self, name: str | SisypheBundle) -> bool:
        """
        Check whether the current SisypheBundle instance has the same name as the parameter.

        Parameters
        ----------
        name : str | SisypheBundle

        Returns
        -------
        bool
            True if same name
        """
        if isinstance(name, SisypheBundle): name = name.getName()
        if isinstance(name, str): return self._name == name
        else: raise TypeError('parameter value {} is not a str or SisypheBundle.'.format(type(name)))

    def count(self) -> int:
        """
        Get the number of tracts (streamlines) in the current SisypheBundle instance.

        Returns
        -------
        int
            number of tracts (streamlines)
        """
        return len(self._list)

    def isEmpty(self) -> bool:
        """
        Check whether the current SisypheBundle instance is empty (no tract).

        Returns
        -------
        bool
            True if bundle is empty
        """
        return len(self._list) == 0

    def clear(self) -> None:
        """
        Remove all the tract indices from the current SisypheBundle instance.
        """
        self._list = list()

    def copy(self) -> SisypheBundle:
        """
        Copy the current SisypheBundle instance.

        Returns
        -------
        SisypheBundle
            bundle copy
        """
        r = SisypheBundle()
        r._name = self._name
        r._color = self._color
        r._lut = self._lut
        r._rep = self._rep
        r._list = self._list.copy()
        return r

    def copyToList(self) -> list[int]:
        """
        Copy the current SisypheBundle instance to a list.

        Returns
        -------
        list[int]
            list copy of bundle
        """
        return self._list.copy()

    def getList(self) -> list[int]:
        """
        Get the list attribute of the current SisypheBundle instance container.

        Returns
        -------
        list[int]
            list copy of bundle
        """
        return self._list

    def appendTracts(self, tracts: int | list[int] | tuple[int, ]) -> None:
        """
        Append element(s) (i.e. index of a tract (streamline) in the associated SisypheStreamlines instance) to the
        current SisypheBundle instance.

        Parameters
        ----------
        tracts : int | list[int] | tuple[int, ]
            tract indices in the associated SisypheStreamlines instance
        """
        if isinstance(tracts, int): tracts = [tracts]
        self._list = list(set(self._list) | set(tracts))
        # < Revision 10/04/2025
        self._list.sort()
        # Revision 10/04/2025 >

    def removeTracts(self, tracts: int | list[int] | tuple[int, ]) -> None:
        """
        Remove element(s) (i.e. index of a tract (streamline) in the associated SisypheStreamlines instance) to the
        current SisypheBundle instance.

        Parameters
        ----------
        tracts : int | list[int] | tuple[int, ]
            tract indices in the associated SisypheStreamlines instance
        """
        if isinstance(tracts, int): tracts = [tracts]
        self._list = list(set(self._list) - set(tracts))
        # < Revision 10/04/2025
        self._list.sort()
        # Revision 10/04/2025 >

    def setFloatColor(self, c: vector3float) -> None:
        """
        Set the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[float, float, float] | list[float, float, float]
            bundle color red, green, blue (each component between 0.0 and 1.0)
        """
        self._color = c

    def setIntColor(self, c: vector3int) -> None:
        """
        Set the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
         c : tuple[int, int, int] | list[int, int, int]
            bundle color red, green, blue (each component between 0 and 255)
        """
        self.setFloatColor([v / 255.0 for v in c])

    def setQColor(self, c: QColor) -> None:
        """
        Set the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
        """
        self.setFloatColor([c.redF(), c.greenF(), c.blueF()])

    def getFloatColor(self) -> vector3float:
        """
        Get the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        tuple[float, float, float] | list[float, float, float]
            bundle color red, green, blue (each component between 0.0 and 1.0)
        """
        return self._color

    def getIntColor(self,) -> vector3int:
        """
        Get the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        tuple[int, int, int] | list[int, int, int]
            bundle color red, green, blue (each component between 0 and 255)
        """
        return [int(c*255) for c in self._color]

    def getQColor(self) -> QColor:
        """
        Get the color attribute of the current SisypheBundle instance. The color attribute is only used in COLOR mode
        representation (see setColorRepresentation() method).

        Returns
        -------
        PyQt5.QtGui.QColor
            bundle color
        """
        c = QColor()
        c.setRgbF(self._color[0], self._color[1], self._color[2])
        return c

    def setLut(self, lut: str | SisypheLut) -> None:
        """
        Set the look-up table colormap attribute the current SisypheBundle instance. The look-up table colormap
        attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        lut : str | Sisyphe.core.SisypheLUT.SisypheLut
            bundle lut
        """
        if isinstance(lut, str):
            name = lut
            lut = SisypheLut()
            lut.setLut(name)
        if isinstance(lut, SisypheLut):
            self._lut = lut
        else: raise TypeError('parameter type {} is not str or SisypheLut.'.format(type(lut)))

    def getLut(self) -> SisypheLut:
        """
        Get the look-up table colormap attribute of the current SisypheBundle instance. The look-up table colormap
        attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Returns
        -------
        Sisyphe.core.sisypheLUT.SisypheLut
            bundle lut
        """
        return self._lut

    def setColorRepresentation(self, v: int) -> None:
        """
        Set the color representation attribute of the current SisypheBundle instance.

        Parameters
        ----------
        v : int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component in
                red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        """
        if v in self._REPTYPE: self._rep = v
        else: self._rep = self._RGB

    def getColorRepresentation(self) -> int:
        """
        Get the color representation attribute of the current SisypheBundle instance.

        Returns
        -------
        int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the tract (x-axis component in
                red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        """
        return self._rep

    def setColorRepresentationAsString(self, v: str) -> None:
        """
        Set the color representation attribute of the current SisypheBundle instance from a str.

        Parameters
        ----------
        v : str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        """
        v = v.lower()
        if v == 'scalars': self._rep = self._CMAP
        elif v == 'color': self._rep = self._COLOR
        else: self._rep = self._RGB

    # noinspection PyTypeChecker
    def getColorRepresentationAsString(self) -> str:
        """
        Get the color representation attribute of the current SisypheBundle instance from a str.

        Returns
        -------
        str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the tract (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        """
        if self._rep == self._RGB: return 'rgb'
        elif self._rep == self._CMAP: return 'scalars'
        elif self._rep == self._COLOR: return 'color'
        else: raise AttributeError('Invalid _rep attribute value {}.'.format(self._rep))

    def setColorRepresentationToRGB(self) -> None:
        """
        Set the color representation attribute of the current SisypheBundle instance to RGB mode. Colors are derived
        from unit vector directed to next point of the tract (x-axis component in red, y-axis component in green and
        z-axis component in blue).
        """
        self._rep = self._RGB

    def setColorRepresentationToScalars(self) -> None:
        """
        Set the color representation attribute of the current SisypheBundle instance to SCALARS mode. Colors are
        derived from scalar values associated with points using the look-up table colormap attribute.
        """
        self._rep = self._CMAP

    def setColorRepresentationToColor(self) -> None:
        """
        Set the color representation attribute of the current SisypheBundle instance to COLOR mode. The tracts have a
        solid color given by the color attribute.
        """
        self._rep = self._COLOR

    def isRGBRepresentation(self) -> bool:
        """
        Check whether the color representation of the current bundle is in RGB mode. Colors are derived from unit
        vector directed to next point of the tract (x-axis component in red, y-axis component in green and z-axis
        component in blue).

        Returns
        -------
            bool
                True if RGB representation
        """
        return self._rep == self._RGB

    def isScalarsRepresentation(self) -> bool:
        """
        Check whether the color representation of the current bundle is in SCALARS mode. Colors are derived from scalar
        values associated with points using the look-up table colormap attribute.

        Returns
        -------
            bool
                True if scalars representation
        """
        return self._rep == self._CMAP

    def isColorRepresentation(self) -> bool:
        """
        Check whether the color representation of the current bundle is in COLOR mode. The tracts have a solid color
        given by the color attribute.

        Returns
        -------
            bool
                True if color representation
        """
        return self._rep == self._COLOR

    def setOpacity(self, v: float) -> None:
        """
        Set the opacity attribute of the current SisypheBundle instance.

        Parameters
        ----------
        v : float
            bundle opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        self._opacity = v

    def getOpacity(self) -> float:
        """
        Get the opacity attribute of the current SisypheBundle instance.

        Returns
        -------
        float
            bundle opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        return self._opacity

    def setLineWidth(self, v: float) -> None:
        """
        Set the line width attribute of the current SisypheBundle instance in mm.

        Parameters
        ----------
        v : float
            line width in mm
        """
        self._width = v

    def getLineWidth(self) -> float:
        """
        Get the line width attribute of the current SisypheBundle instance in mm.

        Returns
        -------
        float
            line width in mm
        """
        return self._width

    # Public set operators

    def union(self, other: SisypheBundle) -> None:
        """
        Union between the current SisypheBundle instance and a SisypheBundle instance given as parameter. The result
        replaces the current SisypheBundle instance.

        Parameters
        ----------
        other : SisypheBundle
            bundle used for union
        """
        self._list = list(set(self._list) | set(other._list))

    def intersection(self, other: SisypheBundle) -> None:
        """
        Intersection between the current SisypheBundle instance and a SisypheBundle instance given as parameter. The
        result replaces the current SisypheBundle instance.

        Parameters
        ----------
        other : SisypheBundle
            bundle used for intersection
        """

        self._list = list(set(self._list) & set(other._list))

    def difference(self, other: SisypheBundle) -> None:
        """
        Difference between the current SisypheBundle instance and a SisypheBundle instance given as parameter. The
        result replaces the current SisypheBundle instance.

        Parameters
        ----------
        other : SisypheBundle
            second operand bundle for subtraction
        """

        self._list = list(set(self._list) - set(other._list))

    def symDifference(self, other: SisypheBundle) -> None:
        """
        Symmetric difference between the current SisypheBundle instance and a SisypheBundle instance given as parameter.
        The result replaces the current SisypheBundle instance.

        Parameters
        ----------
        other : SisypheBundle
            second operand bundle for Symmetric difference
        """

        self._list = list(set(self._list) ^ set(other._list))


class SisypheBundleCollection(object):
    """
    Description
    ~~~~~~~~~~~

    Named list container of SisypheBundle instances with int index or str name key for addressing container elements.

    Scope of methods:

        - container methods
        - set operator methods between SisypheBundle elements of the container (union, intersection, difference,
        symmetric difference)

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheBundleCollection

    Creation: 26/10/2023
    Last revision: 06/12/2023
    """

    __slots__ = ['_index', '_list']

    # Special methods

    """
    Private attributes

    _index      int, SisypheBundle index
    _list       list[SisypheBundle], SisypheBundle list
    """

    def __init__(self) -> None:
        """
        SisypheBundleCollection instance constructor.
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        self._list: list[SisypheBundle] = list()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of SisypheBundleCollection instance to str
        """
        n = len(self._list)
        buff = 'Bundles count: {}\n'.format(n)
        if n > 0:
            for item in self._list:
                buff += '\t{}\t{} tracts\n'.format(str(item), item.count())
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheBundleCollection instance representation
        """
        return 'SisypheBundleCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container operators

    def __getitem__(self, key: str | int) -> SisypheBundle:
        """
        Special overloaded container getter method. Get a SisypheBundle element from the container.

        Parameters
        ----------
        key : int | str
            index or bundle name

        Returns
        -------
        SisypheBundle
            bundle
        """
        # key is str
        if isinstance(key, str): key = self.index(key)
        # key is int index
        if isinstance(key, int):
            if 0 <= key < len(self._list): return self._list[key]
            else: raise IndexError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def __setitem__(self, key: int | str, value: SisypheBundle) -> None:
        """
        Special overloaded container getter method. Set a SisypheBundle element to the container.

        Parameters
        ----------
        key : int | str
            index or bundle name
        value : SisypheBundle
            bundle
        """
        if isinstance(value, SisypheBundle):
            # key is int index
            if isinstance(key, str): key = self.index(key)
            if isinstance(key, int):
                if 0 <= key < len(self._list): self._list[key] = value
                else: raise IndexError('parameter is out of range.')
            else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))
        else: raise TypeError('parameter type {} is not SisypheBundle.'.format(type(value)))

    def __delitem__(self, key: int | str | SisypheBundle) -> None:
        """
        Special overloaded method called by the built-in del() python function. Delete a SisypheBundle element of the
        container.

        Parameters
        ----------
        key : int | str | SisypheBundle
            index or bundle name or SisypheBundle instance
        """
        if isinstance(key, SisypheBundle): key = key.getName()
        if isinstance(key, str): key = self.index(key)
        if isinstance(key, int): self._list.pop(key)

    def __contains__(self, item: str | SisypheBundle) -> bool:
        """
        Check whether the current SisypheBundleCollection instance contains a SisypheBundle instance given as parameter.

        Parameters
        ----------
        item : str | SisypheBundle
            bundle name or SisypheBundle instance

        Returns
        -------
        bool
            True if bundle in container
        """
        if isinstance(item, SisypheBundle): item = item.getName()
        if isinstance(item, str): return item in self.keys()
        else: raise TypeError('parameter type {} is not str or SisypheBundle.'.format(type(item)))

    def __len__(self) -> int:
        """
        Get the number of SisypheBundle elements in the current SisypheBundleCollection instance.

        Returns
        -------
        int
            number of SisypheBundle elements
        """
        return len(self._list)

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        return self

    def __next__(self) -> SisypheBundle:
        """
        Special overloaded container called by the built-in 'next()' python iterator method.

        Returns
        -------
        SisypheBundle
            Next value for the iterable.
        """
        if self._index < len(self._list):
            n = self._index
            self._index += 1
            return self._list[n]
        else: raise StopIteration

    # Public methods

    def count(self) -> int:
        """
        Get the number of SisypheBundle elements in the current SisypheBundleCollection instance.

        Returns
        -------
        int
            number of SisypheBundle elements
        """
        return len(self._list)

    def isEmpty(self) -> bool:
        """
        Check whether the current SisypheBundleCollection instance is empty (no bundle).

        Returns
        -------
        bool
            True if container is empty
        """
        return len(self._list) == 0

    def clear(self) -> None:
        """
        Remove all the SisypheBundle elements from the current SisypheBundleCollection instance.
        """
        self._list = list()

    def remove(self, value: int | str | SisypheBundle) -> None:
        """
        Remove a SisypheBundle element from the current SisypheBundleCollection instance.

        Parameters
        ----------
        value : int | str | SisypheBundle
            index or bundle name or SisypheBundle instance to remove
        """
        # value is SisypheBundle
        if isinstance(value, SisypheBundle): self._list.remove(value)
        # value is str or int
        elif isinstance(value, (str, int)): self.pop(self.index(value))
        else: raise TypeError('parameter type {} is not int, str or SisypheBundle.'.format(type(value)))

    def pop(self, key: int | str | SisypheBundle | None = None) -> SisypheBundle:
        """
        Remove a SisypheBundle elements from the current SisypheBundleCollection instance and return it. If key is
        None, removes and returns the last element.

        Parameters
        ----------
        key : int | str | SisypheBundle | None
            index or bundle name or SisypheBundle to remove

        Returns
        -------
        SisypheBundle
            bundle removed from the container
        """
        if key is None: return self._list.pop()
        # key is SisypheVolume arrayID str
        if isinstance(key, (str, SisypheBundle)): key = self.index(key)
        # key is int index
        if isinstance(key, int): return self._list.pop(key)
        else: raise TypeError('parameter type {} is not int or str.'.format(type(key)))

    def keys(self) -> list[str]:
        """
        Get the list of keys in the current SisypheBundleCollection instance container.

        Returns
        -------
        list[str]
            list of keys in the container
        """
        return [k.getName() for k in self._list]

    def index(self, value: str | SisypheBundle) -> int:
        """
         Index of a SisypheBundle element in the current SisypheBundleCollection instance container.

        Parameters
        ----------
        value : str | SisypheBundle
            bundle name or SisypheBundle

        Returns
        -------
        int
            index of bundle in the container
        """
        keys = [k.getName() for k in self._list]
        # value is SisypheBundle
        if isinstance(value, SisypheBundle): value = value.getName()
        # value is str
        if isinstance(value, str): return keys.index(value)
        else: raise TypeError('parameter type {} is not str or SisypheBundle.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverses the order of the elements in the current SisypheBundleCollection instance container.
        """
        self._list.reverse()

    def append(self, value: SisypheBundle) -> None:
        """
        Append a SisypheBundle element in the current SisypheBundleCollection instance container.

        Parameters
        ----------
        value :  SisypheBundle
            bundle to append in the container
        """
        if isinstance(value, SisypheBundle):
            if value.getName() not in self: self._list.append(value)
        else: raise TypeError('parameter type {} is not SisypheBundle.'.format(type(value)))

    def insert(self, key: int | str | SisypheBundle, value: SisypheBundle) -> None:
        """
         Insert a SisypheBundle element at the position given by the key in the current SisypheBundleCollection
         instance container.

        Parameters
        ----------
        key : int | str | SisypheBundle | None
            index or bundle name or SisypheBundle
        value : SisypheBundle
            bundle to insert in the container
        """
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

    def copy(self) -> SisypheBundleCollection:
        """
        Copy the current SisypheBundleCollection instance container (Shallow copy of elements).

        Returns
        -------
        SisypheBundleCollection
            shallow copy of bundle
        """
        bundle = SisypheBundleCollection()
        for item in self._list:
            bundle.append(item)
        return bundle

    def copyToList(self) -> list[SisypheBundle]:
        """
        Copy the current SisypheBundleCollection instance container to a list (Shallow copy of elements).

        Returns
        -------
        list[SisypheBundle]
            shallow copy of bundle to list
        """
        return self._list.copy()

    def getList(self) -> list[SisypheBundle]:
        """
        Get the list attribute of the current SisypheBundleCollection instance container (Shallow copy of the elements).

        Returns
        -------
        list[SisypheBundle]
            shallow copy of bundle to list
        """
        return self._list

    def rename(self, old: str, new: str) -> None:
        """
        Rename a bundle of the current SisypheBundleCollection instance container.

        Parameters
        ----------
        old : str
            Old bundle name
        new : str
            New bundle name
        """
        if old in self:
            idx = self.index(old)
            self._list[idx].setName(new)
        else: raise ValueError('{} is not a key of the current SisypheBundleCollection.'.format(old))

    # Public set operators

    def union(self, names: list[str, ], newname: str) -> None:
        """
        Union of SisypheBundle elements of the current SisypheBundleCollection. Bundles are selected by their name
        attributes. The resulting SisypheBundle is appended to the container.

        Parameters
        ----------
        names : list[str, ]
            list of bundle names
        newname :
            name of the new bundle (union result)
        """
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.union(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def intersection(self, names: list[str, ], newname: str) -> None:
        """
        Intersection of SisypheBundle elements of the current SisypheBundleCollection. Bundles are selected by their
        name attributes. The resulting SisyphusBundle is appended to the container.

        Parameters
        ----------
        names : list[str, ]
            list of bundle names
        newname :
            name of the new bundle (intersection result)
        """
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.intersection(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def difference(self, names: list[str, ], newname: str) -> None:
        """
        Difference of SisypheBundle elements of the current SisypheBundleCollection. Bundles are selected by their
        name attributes. The resulting SisyphusBundle is appended to the container.

        Parameters
        ----------
        names : list[str, ]
            list of bundle names
        newname :
            name of the new bundle (difference result)
        """
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.difference(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))

    def symDifference(self, names: list[str, ], newname: str) -> None:
        """
        Symmetric difference of SisypheBundle elements of the current SisypheBundleCollection. Bundles are selected by
        their name attributes. The resulting SisyphusBundle is appended to the container.

        Parameters
        ----------
        names : list[str, ]
            list of bundle names
        newname :
            name of the new bundle (symmetric difference result)
        """
        if newname not in self:
            r = self[names[0]]
            for name in names:
                r.symDifference(self[name])
            r.setName(newname)
            self.append(r)
        else: raise ValueError('parameter {} already exists.'.format(newname))


class SisypheStreamlines(object):
    """
    Description
    ~~~~~~~~~~~

    Class to manage a list of streamlines. A streamline is represented as a numpy ndarray of size (n×3) where each row
    of the array represent a 3D point of the streamline. A set of streamlines is represented with a list of numpy
    ndarray of size (Ni×3) for i=1:M where M is the number of streamlines in the set.

    This class has a SisypheBundleCollection private attribute to classify the streamlines in bundles. It is used by
    all methods that process bundles.

    Attributes:

        - reference ID, space ID of the diffusion weighted images used for the tracking process
        - shape and spacing of the diffusion-weighted images used for the tracking process
        - file name, file name used to save the current instance
        - display attributes (color representation mode, color, look-up table colormap, line width, opacity)

    Scope of methods:

        - container-like methods
        - tract feature methods (length, curvature, center of mass, principal direction, distances...)
        - bundle feature methods
        - bundle selection and clustering methods (virtual dissection)
        - bundle conversion to ROI and Mesh
        - maps processing (density, path length, connectivity)
        - IO methods to and from Tck, Trk, Vtk, Vtp, Fib, Dpy and numpy formats

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheStreamlines

    Creation: 26/10/2023
    Last Revision: 19/06/2025
    """

    __slots__ = ['_index', '_ID', '_shape', '_spacing', '_bundles', '_streamlines',
                 '_regstep', '_dirname', '_trf', '_whole', '_centroid', '_atlas']

    # Class constants

    _DEFAULTNAME = 'tractogram'
    _FILEEXT = '.xtracts'
    TRK, TCK, VTK, VTP, FIB, NPZ, DPY = '.trk', '.tck', '.vtk', '.vtp', '.fib', '.npz', '.dpy'
    _TRACTSEXT = [_FILEEXT, TRK, TCK, VTK, VTP, FIB, NPZ, DPY]
    _ATLASBDL = {'WHOLE': 'Whole Brain Tractogram',
                 'AR_L': 'Acoustic Radiation Left',
                 'AR_R': 'Acoustic Radiation Right',
                 'AC': 'Anterior Commissure',
                 'AF_L': 'Arcuate Fasciculus Left',
                 'AF_R': 'Arcuate Fasciculus Right',
                 'CNVIII_L': 'Auditory Cranial Nerve Left',
                 'CNVIII_R': 'Auditory Cranial Nerve Right',
                 'CTT_L': 'Central Tegmental Tract Left',
                 'CTT_R': 'Central Tegmental Tract Right',
                 'CB_L': 'Cerebellum Left',
                 'CB_R': 'Cerebellum Right',
                 'C_L': 'Cingulum Tract Left',
                 'C_R': 'Cingulum Tract Right',
                 'CC_Mid': 'Corpus Callosum Middle',
                 'CC': 'Corpus Callosum',
                 'CST_L': 'Cortico Spinal Tract Left',
                 'CST_R': 'Cortico Spinal Tract Right',
                 'CS_L': 'Cortico Striatal Tract Left',
                 'CS_R': 'Cortico Striatal Tract Right',
                 'CT_L': 'Cortico Thalamic Tract Left',
                 'CT_R': 'Cortico Thalamic Tract Right',
                 'DLF_L': 'Dorsal Longitudinal Fasciculus Left',
                 'DLF_R': 'Dorsal Longitudinal Fasciculus Right',
                 'EMC_L': 'Extreme Capsule Left',
                 'EMC_R': 'Extreme Capsule Right',
                 'CNVII_L': 'Facial Cranial Nerve left',
                 'CNVII_R': 'Facial Cranial Nerve Right',
                 'CC_FMI': 'Forceps Minor',
                 'CC_FMJ': 'Forceps Major',
                 'F': 'Fornix',
                 'AST_L': 'Frontal Aslant Tract Left',
                 'AST_R': 'Frontal Aslant Tract Right',
                 'FPT_L': 'Frontal Pontine Tract Left',
                 'FPT_R': 'Frontal Pontine Tract Right',
                 'ICP_L': 'Inferior Cerebellar Peduncle Left',
                 'ICP_R': 'Inferior Cerebellar Peduncle Right',
                 'IFOF_L': 'Inferior Fronto Occipital Fasciculus Left',
                 'IFOF_R': 'Inferior Fronto Occipital Fasciculus Right',
                 'ILF_L': 'Inferior Longitudinal Fasciculus Left',
                 'ILF_R': 'Inferior Longitudinal Fasciculus Right',
                 'LL_L': 'Lateral Lemniscus Left',
                 'LL_R': 'Lateral Lemniscus Right',
                 'ML_L': 'Medial Lemniscus Left',
                 'ML_R': 'Medial Lemniscus Right',
                 'MLF_L': 'Medial Longitudinal Fasciculus Left',
                 'MLF_R': 'Medial Longitudinal Fasciculus Right',
                 'MCP': 'Middle Cerebellar Peduncle',
                 'MdLF_L': 'Middle Longitudinal Fasciculus Left',
                 'MdLF_R': 'Middle Longitudinal Fasciculus Right',
                 'OPT_L': 'Occipital Pontine Tract Left',
                 'OPT_R': 'Occipital Pontine Tract Right',
                 'CNIII_L': 'Oculomotor Cranial Nerve Left',
                 'CNIII_R': 'Oculomotor Cranial Nerve Right',
                 'OR_L': 'Optic Radiation Left',
                 'OR_R': 'Optic Radiation Right',
                 'PPT_L': 'Parietal Pontine Tract Left',
                 'PPT_R': 'Parietal Pontine Tract Right',
                 'PC': 'Posterior Commissure',
                 'RST_L': 'Rubro Spinal Tract Left',
                 'RST_R': 'Rubro Spinal Tract Right',
                 'STT_L': 'Spino Thalamic Tract Left',
                 'STT_R': 'Spino Thalamic Tract Right',
                 'SCP': 'Superior Cerebellar Peduncle',
                 'SLF_L': 'Superior Longitudinal Fasciculus Left',
                 'SLF_R': 'Superior Longitudinal Fasciculus Right',
                 'TPT_L': 'Temporal Pontine Tract Left',
                 'TPT_R': 'Temporal Pontine Tract Right',
                 'CNV_L': 'Trigeminal Cranial Nerve Left',
                 'CNV_R': 'Trigeminal Cranial Nerve Right',
                 'CNIV_L': 'Trochlear Cranial Nerve Left',
                 'CNIV_R': 'Trochlear Cranial Nerve Right',
                 'UF_L': 'Uncinate Fasciculus Left',
                 'UF_R': 'Uncinate Fasciculus Right',
                 'V': 'Vermis',
                 'VOF_L': 'Vertical Occipital fasciculus Left',
                 'VOF_R': 'Vertical Occipital fasciculus Right',
                 'CNII_L': 'Visual Cranial Nerve Left',
                 'CNII_R': 'Visual Cranial Nerve Right'}

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheStreamlines file extension.

        Returns
        -------
        str
            '.xtracts'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheStreamlines filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Streamlines (.xtracts)'
        """
        return 'PySisyphe Streamlines (*{})'.format(cls._FILEEXT)

    @classmethod
    def getDefaultName(cls) -> str:
        """
        Get the default name of a SisypheStreamlines instance (name after initialization).

        Returns
        -------
        str
            default name
        """
        return cls._DEFAULTNAME

    @classmethod
    def getAtlasBundleDirectory(cls) -> str:
        """
        Get atlas bundles directory (~/templates/BUNDLES)

        Returns
        -------
        str
            bundle model directory (~/templates/BUNDLES)
        """
        import Sisyphe.templates
        # < Revision 20/02/2025
        # return join(dirname(abspath(Sisyphe.templates.__file__)), 'BUNDLES')
        return join(dirname(abspath(Sisyphe.templates.__file__)), 'ICBM152', 'BUNDLES HCP', 'TRACTS')
        # Revision 20/02/2025 >

    @classmethod
    def getAtlasBundleShortNames(cls, whole: bool = True) -> list[str]:
        """
        Get short names of atlas bundles.

        Parameters
        ----------
        whole : bool
            if False, whole brain tractogram is removed from the list

        Returns
        -------
        str
            short names of atlas bundles
        """
        if whole: return list(cls._ATLASBDL.keys())
        else: return list(cls._ATLASBDL.keys())[1:]

    @classmethod
    def getAtlasBundleNames(cls, whole: bool = True) -> list[str]:
        """
        Get names of atlas bundles.

        Parameters
        ----------
        whole : bool
            if False, whole brain tractogram is removed from the list

        Returns
        -------
        str
            names of atlas bundles
        """
        if whole: return list(cls._ATLASBDL.values())
        else: return list(cls._ATLASBDL.values())[1:]

    @classmethod
    def isAtlasBundleName(cls, name: str) -> bool:
        """
        Check whether name parameter is a valid atlas bundle name.

        Parameters
        ----------
        name : str
            atlas bundle name

        Returns
        -------
        bool
            True if valid atlas bundle name
        """
        # < Revision 20/02/2025
        # capitalize conversion
        name = ' '.join([v.capitalize() for v in name.split(' ')])
        # Revision 20/02/2025 >
        return name in cls._ATLASBDL.values()

    @classmethod
    def isAtlasBundleShortName(cls, short: str) -> bool:
        """
        Check whether short name parameter is a valid atlas bundle short name.

        Parameters
        ----------
        short : str
            atlas bundle short name

        Returns
        -------
        bool
            True if valid atlas bundle short name
        """
        # < Revision 20/02/2025
        # upper case conversion
        short = short.upper()
        # Revision 20/02/2025 >
        return short in cls._ATLASBDL.keys()

    @classmethod
    def getAtlasBundleFilenameFromName(cls, name: str) -> str | None:
        """
        Get atlas bundle filename from its name.

        Parameters
        ----------
        name : str
            atlas bundle long name

        Returns
        -------
        str | None
            bundle filename
        """
        names = list(cls._ATLASBDL.values())
        # < Revision 20/02/2025
        # capitalize conversion
        name = ' '.join([v.capitalize() for v in name.split(' ')])
        # Revision 20/02/2025 >
        if name in names:
            name = name.lower().replace(' ', '_')
            return join(cls.getAtlasBundleDirectory(), name + cls.getFileExt())
        else: raise ValueError('{} is not a valid atlas bundle name.'.format(name))

    @classmethod
    def getAtlasBundleFilenameFromShortName(cls, short: str) -> str | None:
        """
        Get atlas bundle filename from its short name.

        Parameters
        ----------
        short : str
            atlas bundle short name

        Returns
        -------
        str | None
            bundle filename
        """
        # < Revision 20/02/2025
        # upper case conversion
        short = short.upper()
        # Revision 20/02/2025 >
        if short in cls._ATLASBDL.keys():
            # < 20/02/2025
            # return join(cls.getAtlasBundleDirectory(), short + cls.getFileExt())
            name = cls._ATLASBDL[short]
            return cls.getAtlasBundleFilenameFromName(name)
            # 20/02/2025 >
        else: raise ValueError('{} is not a valid atlas bundle short name.'.format(short))

    @classmethod
    def openStreamlines(cls, filename: str) -> SisypheStreamlines:
        """
        Create a SisypheStreamlines instance from a PySisyphe streamlines file (.xtracts).

        Parameters
        ----------
        filename : str
            Diffusion model file name

        Returns
        -------
        SisypheStreamlines
            loaded streamlines
        """
        sl = SisypheStreamlines()
        sl.load(filename)
        return sl

    @classmethod
    def getStepSize(cls, sl: SisypheStreamlines | Streamlines | ndarray) -> tuple[bool, float]:
        """
        Get whether step size of a streamline is regular.

        Parameters
        ----------
        sl : SisypheStreamlines | dipy.tracking.Streamlines | numpy.ndarray
            streamlines to test

        Returns
        -------
        tuple[bool, float]
            True if regular step size, step size in mm (0.0 if non-regular step size)
        """
        if isinstance(sl, SisypheStreamlines): sl = sl.getStreamlines()
        if isinstance(sl, Streamlines): sl = sl[0]
        if isinstance(sl, ndarray):
            s = sl[0:-1] - sl[1:]
            ss = sqrt((s ** 2).sum(axis=1))
            # noinspection PyUnresolvedReferences
            reg = allclose(ss, ss[0])
            if reg:
                # noinspection PyUnresolvedReferences
                rss = ss[0]
                if abs(rss - round(rss)) <= finfo('float32').eps: rss = round(rss)
            else: rss = 0.0
            return reg, rss
        else: raise TypeError('parameter type {} is not SisypheStreamlines, Streamlines or ndarray.'.format(type(sl)))

    @classmethod
    def getReferenceIDfromFile(cls, filename: str) -> str:
        """
        Get the reference ID attribute from xtracts file. This is the space ID of the diffusion weighted images used
        for the tracking process.

        Returns
        -------
        str
            ID
        """
        filename = splitext(filename)[0] + cls.getFileExt()
        if exists(filename):
            with open(filename, 'rb') as f:
                # Read XML part
                line = ''
                strdoc = ''
                while line != '</{}>\n'.format(cls._FILEEXT[1:]):
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                doc = minidom.parseString(strdoc)
                root = doc.documentElement
                if root.nodeName == cls._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
                    node = root.firstChild
                    while node:
                        if node.nodeName == 'id': return node.firstChild.data
                        node = node.nextSibling
            raise ValueError('No id field.')
        else: raise FileNotFoundError('No such file {}'.format(filename))

    # Special methods

    """
    Private attributes

    _index          cython.int
    _ID             str
    _shape          list[int, int, int]
    _spacing        list[float, float, float]
    _affine         ndarray
    _streamlines    Streamlines
    _bundles        SisypheBundleCollection
    _dirname        str
    _regstep        bool, True if step is constant
    _whole          bool, True if whole brain streamlines
    _centroid       bool, True if bundle centroid streamline
    _atlas          bool, True if atlas streamlines
    _trf            ndarray | None, atlas to streamlines space affine transformation
    """

    def __init__(self, sl: Streamlines | ndarray | None = None, compress=False) -> None:
        """
        SisypheStreamlines instance constructor.

        Parameters
        ----------
        sl : dipy.tracking.Streamlines | ndarray
            streamlines to be added to the current SisypheStreamlines instance.
        compress: bool
            By default, streamlines are uncompressed, with a regular distance between points. If compress is True,
            compression is applied to streamlines i.e. a reduction in the number of points with non-uniform distances
            between points. The compression consists in merging consecutive segments that are nearly collinear. The
            merging is achieved by removing the point the two segments have in common. The linearization process
            ensures that every point being removed are within a certain margin of the resulting streamline.
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        self._ID: str = ''
        self._shape: tuple | list = [256, 256, 256]
        self._spacing: tuple | list = [1.0, 1.0, 1.0]
        self._regstep: bool = True
        self._whole: bool = False
        self._centroid: bool = False
        self._atlas: bool = False
        self._trf: ndarray | None = None
        if sl is None or not isinstance(sl, (ndarray, Streamlines)):
            self._streamlines = Streamlines()
            bundle = SisypheBundle()
        else:
            if isinstance(sl, ndarray):
                s = sl
                sl = Streamlines()
                sl.append(s)
            if compress:
                sl = compress_streamlines(sl)
                self._regstep = False
            self._streamlines = sl
            bundle = SisypheBundle((0, len(sl), 1))
        bundle.setName(self._DEFAULTNAME)
        self._bundles = SisypheBundleCollection()
        self._bundles.append(bundle)
        self._dirname = getcwd()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            Conversion of SisypheStreamlines instance to str
        """
        buff = 'Global streamlines count: {}\n'.format(len(self._streamlines))
        buff += 'reference ID: {}\n'.format(str(self._ID))
        buff += 'DWI shape: {}\n'.format(self._shape)
        buff += 'DWI spacing: {}\n'.format(self._spacing)
        buff += 'Regular step: {}\n'.format(str(self._regstep))
        if self._whole: buff += 'Whole brain tractogram\n'
        # < Revision 20/02/2025
        # add centroid attribute
        if self._centroid:
            if len(self._streamlines) == 1: buff += 'Centroid streamline\n'
            else: buff += 'Centroid streamlines\n'
        # Revision 20/02/2025 >
        buff += 'Atlas: {}\n'.format(str(self._atlas))
        if self._trf is not None:
            buff += 'Affine (Atlas to native anatomy):\n'
            buff += '\t{0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {0[3]:.2f}\n'.format(self._trf[0])
            buff += '\t{0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {0[3]:.2f}\n'.format(self._trf[1])
            buff += '\t{0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {0[3]:.2f}\n'.format(self._trf[2])
            buff += '\t{0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {0[3]:.2f}\n'.format(self._trf[3])
        for bundle in self._bundles:
            buff += 'Bundle: {}\n'.format(bundle.getName())
            buff += '\tStreamlines count: {}\n'.format(bundle.count())
            buff += '\tColor: {} mode\n'.format(self.getColorRepresentationAsString(bundle.getName()))
            r = self.getColorRepresentation()
            if r == 1:
                buff += '\tColormap: {}\n'.format(self.getLut(bundle.getName()))
            elif r == 2: buff += '\tColor: {}\n'.format(self.getFloatColor(bundle.getName()))
            buff += '\tOpacity: {}\n'.format(self.getOpacity(bundle.getName()))
            buff += '\tLine width: {}\n'.format(self.getLineWidth(bundle.getName()))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheStreamlines instance representation
        """
        return 'SisypheStreamlines instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Special container methods

    def __getitem__(self, key: int | slice | list[int]) -> ndarray | Streamlines:
        """
        Special overloaded container getter method.
        Get streamline element(s) from the container.
        If int, index of the streamline element (numpy.ndarray) to retrieve.
        If slice, use slicing to retrieve consecutive streamline elements (dipy.tracking.Streamlines).
        If list, indices of non-consecutive elements to retrieve (dipy.tracking.Streamlines).

        Parameters
        ----------
        key : int | slice | list[int]
            index

        Returns
        -------
        numpy.ndarray | dipy.tracking.Streamlines
            streamlines
        """
        return self._streamlines[key]

    def __len__(self) -> int:
        """
        Get the number of streamline elements in the current SisypheStreamlines instance.

        Returns
        -------
        int
            number of streamline elements
        """
        return len(self._streamlines)

    def __iter__(self):
        """
        Special overloaded container called by the built-in 'iter()' python iterator method. This method initializes a
        Python iterator object.
        """
        # noinspection PyUnresolvedReferences
        self._index: cython.int = 0
        return self

    def __next__(self) -> Streamlines:
        """
        Special overloaded container called by the built-in 'next()' python iterator method.

        Returns
        -------
        dipy.tracking.Streamlines
            Next value for the iterable.
        """
        if self._index < len(self._streamlines):
            n = self._index
            self._index += 1
            return self._streamlines[n]
        else: raise StopIteration

    # Private methods

    def _load(self, filename: str, loadfunc: Callable) -> None:
        if splitext(filename)[1] == '.trk': hdr = 'same'
        else:
            hdr = create_tractogram_header(filename,
                                           affine=eye(4, 4),
                                           dimensions=self._shape,
                                           voxel_sizes=self._spacing,
                                           voxel_order=b'RAS')
        tractogram = loadfunc(filename,
                              reference=hdr,
                              to_space=Space.RASMM,
                              to_origin=Origin.TRACKVIS,
                              bbox_valid_check=False,
                              trk_header_check=False)
        self._streamlines = tractogram.streamlines
        bundle = SisypheBundle((0, len(self._streamlines), 1))
        bundle.setName(splitext(basename(filename))[0])
        self._bundles = SisypheBundleCollection()
        self._bundles.append(bundle)
        self._dirname = dirname(filename)
        if self._dirname == '': getcwd()

    def _save(self, bundle: str, savefunc: Callable) -> None:
        if bundle == 'all': bundle = self._bundles[0].getName()
        filename = join(self._dirname, bundle)
        hdr = create_tractogram_header('.trk',
                                       affine=eye(4, 4),
                                       dimensions=self._shape,
                                       voxel_sizes=self._spacing,
                                       voxel_order=b'RAS')
        tractogram = StatefulTractogram(self.getStreamlinesFromBundle(bundle),
                                        reference=hdr,
                                        space=Space.RASMM,
                                        origin=Origin.TRACKVIS)
        savefunc(tractogram, filename)

    # Public methods

    def clearAffineAtlasTransformation(self) -> None:
        """
        Clear affine attribute of the current SisypheStreamlines instance. Affine attribute = affine transformation
        from ICBM152 HCP space to current space.
        """
        self._trf = None

    def getAffineAtlasTransformation(self) -> ndarray | None:
        """
        Get affine attribute of the current SisypheStreamlines instance. Affine attribute = affine transformation from
        ICBM152 HCP space to current space.
        """
        return self._trf

    def getReferenceID(self) -> str:
        """
        Get the reference ID attribute of the current SisypheStreamlines instance. This is the space ID of the
        diffusion weighted images used for the tracking process.

        Returns
        -------
        str
            ID
        """
        return self._ID

    def setReferenceID(self, ID: str | SisypheVolume | SisypheDiffusionModel | SisypheStreamlines) -> None:
        """
        Set the reference ID attribute of the current SisypheStreamlines instance. This is the space ID of the
        diffusion-weighted images used for the tracking process. If the parameter is a SisypheVolume or
        SisypheDiffusionModel instance, this method also copies shape and spacing attributes to the current
        SisypheStreamlines instance.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume | SisypheDiffusionModel | SisypheStreamlines
            reference ID
        """
        if isinstance(ID, SisypheVolume):
            self._dirname = ID.getDirname()
            self._shape = ID.getSize()
            self._spacing = ID.getSpacing()
            ID = ID.getID()
        elif isinstance(ID, SisypheDiffusionModel):
            self._shape = ID.getDWI().shape[:3]
            self._spacing = ID.getSpacing()
            ID = ID.getReferenceID()
        elif isinstance(ID, SisypheStreamlines):
            self._shape = ID.getDWIShape()
            self._spacing = ID.getDWISpacing()
            ID = ID.getReferenceID()
        if isinstance(ID, str): self._ID = ID
        else: raise TypeError('parameter type {} is not str, SisypheVolume, SisypheDiffusionModel or SisypheStreamlines.'.format(type(ID)))

    def hasReferenceID(self) -> bool:
        """
        Check whether the reference ID attribute of the current SisypheStreamlines instance is defined. This is the
        space ID of the diffusion weighted images used for the tracking process.

        Returns
        -------
        bool
            True if ID is defined
        """
        return self._ID != ''

    # < Revision 21/02/2025
    # add hasICBM152ReferenceID method
    def hasICBM152ReferenceID(self) -> bool:
        """
        Check whether the reference ID attribute of the current SisypheStreamlines instance is ICBM152.

        Returns
        -------
        bool
            True if ID is ICBM152
        """
        from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
        return self._ID == SisypheAcquisition.getICBM152TemplateTag()
    # Revision 21/02/2025 >

    # < Revision 21/02/2025
    # add hasSRI24ReferenceID method
    def hasSRI24ReferenceID(self) -> bool:
        """
        Check whether the reference ID attribute of the current SisypheStreamlines instance is SRI24.

        Returns
        -------
        bool
            True if ID is SRI24
        """
        from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
        return self._ID == SisypheAcquisition.getSRI24TemplateTag()
    # Revision 21/02/2025 >

    def setDWIShape(self, v: listint | tuple3int):
        """
        Set the shape attribute of the current SisypheStreamlines instance. This is the shape of the diffusion-weighted
        images used for the tracking process.

        Parameters
        ----------
        v : tuple[int, int, int] | list[int, int, int]
            shape of the diffusion-weighted images used to calculate streamlines
        """
        self._shape = list(v)

    def getDWIShape(self):
        """
        Get the shape attribute of the current SisypheStreamlines instance. This is the shape of the diffusion-weighted
        images used for the tracking process.

        Returns
        -------
        tuple[int, int, int] | list[int, int, int]
            shape of the diffusion-weighted images used to calculate streamlines
        """
        return self._shape

    def setDWISpacing(self, v: listfloat | tuple3float):
        """
        Set the spacing attribute of the current SisypheStreamlines instance. This is the spacing of the
        diffusion-weighted images used for the tracking process.

        Parameters
        ----------
        v : tuple[float, float, float] | list[float, float, float]
            spacing of the diffusion-weighted images used to calculate streamlines
        """
        self._spacing = list(v)

    def getDWISpacing(self):
        """
        Get the spacing attribute of the current SisypheStreamlines instance. This is the spacing of the
        diffusion-weighted images used for the tracking process.

        Returns
        -------
        tuple[float, float, float] | list[float, float, float]
            spacing of the diffusion-weighted images used to calculate streamlines
        """
        return self._spacing

    def getDWIFOV(self, decimals: int | None = None) -> tuple[float, float, float]:
        """
        Get the field of view (FOV) attribute of the current SisypheStreamlines instance. This is the spacing of the
        diffusion-weighted images used for the tracking process.

        Parameters
        ----------
        decimals : int | None
            number of decimals used to round values, if None no round

        Returns
        -------
        tuple[float, float, float]
            field of view of diffusion-weighted images used to calculate streamlines
        """
        if decimals is not None:
            # noinspection PyTypeChecker
            return tuple([round(self._shape[i] * self._spacing[i], decimals) for i in range(3)])
        else:
            # noinspection PyTypeChecker
            return tuple([self._shape[i] * self._spacing[i] for i in range(3)])

    def isWholeBrainTractogram(self) -> bool:
        """
        Check whether streamlines of the current SisypheStreamlines instance have been generated from whole brain seeds.
        Whole brain state is assumed if more than 50% brain mask voxels are used as seeds.

        Returns
        -------
        bool
            True if whole brain seeds
        """
        return self._whole

    def setWholeBrainStatus(self, s: bool):
        """
        Set the whole brain attribute of the current SisypheStreamlines instance are atlas streamlines. Whole brain
        state is assumed if more than 50% brain mask voxels are used as seeds.

        Parameters
        ----------
        s: bool
            Whole brain state
        """
        self._whole = s

    def setWholeBrainStatusFromMasks(self, brainmask: ndarray, seedmask: ndarray) -> float:
        """
        Set the whole brain status of the seeds used to generate streamlines of the current SisypheStreamlines instance.
        Whole brain state is assumed if more than 50% brain mask voxels are used as seeds.

        Parameters
        ----------
        brainmask : numpy.ndarray
            whole brain mask
        seedmask : numpy.ndarray
            seeding voxels mask

        Returns
        -------
        float
            Ratio of brain mask voxels used as seeds
        """
        v = (brainmask.sum() / seedmask.sum())
        self._whole = (v > 0.5)
        return v

    def isAtlas(self) -> bool:
        """
        Check whether streamlines of the current SisypheStreamlines instance are atlas streamlines.

        Returns
        -------
        bool
            True if atlas streamlines
        """
        return self._atlas

    def setAtlasStatus(self, v) -> None:
        """
        Set the atlas attribute of the current SisypheStreamlines instance. True if streamlines are atlas streamlines.

        Parameters
        ----------
        v: bool
            atlas status of streamlines
        """
        self._atlas = v
        if v: self._trf = eye(4, 4)

    def isCentroid(self) -> bool:
        """
        Check whether streamline(s) of the current SisypheStreamlines instance is (are) centroid streamline(s).

        Returns
        -------
        bool
            True if centroid streamline(s)
        """
        return self._centroid

    def setCentroidStatus(self, v) -> None:
        """
        Set the centroid attribute of the current SisypheStreamlines instance. True if streamline(s) is (are) centroid
        streamline(s).

        Parameters
        ----------
        v: bool
            centroid status of streamline(s)
        """
        self._centroid = v

    def isAtlasRegistered(self) -> bool:
        """
        Check whether streamlines of the current SisypheStreamlines instance are coregistered with atlas.

        Returns
        -------
        bool
            True if affine transformation to atlas is not empty
        """
        return self._trf is not None

    def getAtlasTransformation(self) -> ndarray | None:
        """
        Get affine SisypheTransform of atlas coregistration.

        Returns
        -------
        numpy.ndarray | None
            affine geometric transformation
        """
        return self._trf

    def setAtlasTransformation(self, affine: ndarray) -> None:
        """
        Set affine SisypheTransform of atlas coregistration.

        Parameters
        ----------
        affine: ndarray | None
            affine geometric transformation
        """
        self._trf = affine

    def getDirname(self) -> str:
        """
        Get the path part of the file name attribute of the current SisypheStreamlines instance. This file name is the
        default name used by IO methods.

        Returns
        -------
        str
            default path
        """
        return self._dirname

    def getFilename(self, bundle: str = 'all') -> str:
        """
        Get the bundle file name attribute of the current SisypheStreamlines instance. This file name is the default
        name used by IO methods.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        str
            default bundle file name
        """
        if bundle not in self._bundles: bundle = 'all'
        if bundle == 'all': bundle = self._bundles[0].getName()
        return join(self._dirname, bundle + self.getFileExt())

    def setName(self, name: str = _DEFAULTNAME) -> None:
        """
        Set the name attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        name : str
            streamlines name
        """
        self._bundles[0].setName(name)

    def getName(self) -> str:
        """
        Get the name attribute of the current SisypheStreamlines instance.

        Returns
        -------
        str
            streamlines name
        """
        return self._bundles[0].getName()

    def isDefaultName(self) -> bool:
        """
        Check whether the name attribute of the current SisypheStreamlines instance has a default value.

        Returns
        -------
        bool
            True if 'all' or 'tractogram'
        """
        return self._bundles[0].getName() in ('all', self._DEFAULTNAME)

    def isEmpty(self) -> bool:
        """
        Check whether the current SisypheStreamlines instance is empy (no streamline).

        Returns
        -------
        bool
            True if empty
        """
        return len(self._streamlines) == 0 or self._streamlines is None

    def count(self) -> int:
        """
        Get the number of streamline elements in the current SisypheStreamlines instance.

        Returns
        -------
        int
            number of streamline elements
        """
        return len(self._streamlines)

    def hasRegularStep(self):
        """
        Check whether the streamlines of the current SisypheStreamlines instance are compressed.

        By default, streamlines are uncompressed, with a regular step between points. Compression can be applied to
        streamlines i.e. a reduction in the number of points with non-uniform steps between points. The compression
        consists in merging consecutive segments that are nearly collinear. The merging is achieved by removing the
        point the two segments have in common. The linearization process ensures that every point being removed are
        within a certain margin of the resulting streamline.

        Returns
        -------
        bool
            True, if not compressed with regular step between points.
        """
        return self._regstep is True

    def getBundles(self) -> SisypheBundleCollection:
        """
        Get the SisypheBundleCollection attribute of the current SisypheStreamlines instance.

        Returns
        -------
        SisypheBundleCollection
            bundles collection
        """
        return self._bundles

    def getBundle(self, key: int | str) -> SisypheBundle:
        """
        Get a SisypheBundle of the current SisypheStreamlines instance.

        Returns
        -------
        SisypheBundle
            bundle
        """
        return self._bundles[key]

    def renameBundle(self, old: str, new: str) -> None:
        """
        Rename a SisypheBundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        old : str
            Old bundle name
        new : str
            New bundle name
        """
        self._bundles.rename(old, new)

    def append(self, sl: ndarray | Streamlines, bundlename: str = '') -> None:
        """
        Append streamlines to the current SisypheStreamlines instance.

        Parameters
        ----------
        sl :  numpy.ndarray | dipy.tracking.Streamlines
            streamline(s) to append
        bundlename : str
            Create a new bundle with appended streamlines
        """
        n = self._bundles[0].count()
        if isinstance(sl, ndarray):
            if sl.ndim == 2 and sl.shape[1] == 3:
                self._streamlines.append(sl)
                self._bundles[0].appendTracts(n)
        elif isinstance(sl, Streamlines):
            self._streamlines.extend(sl)
            tracts = list(range(n, n + len(sl), 1))
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

    def copyAttributesTo(self, sl: SisypheStreamlines) -> None:
        """
        Copy current SisypheStreamlines instance attributes to SisypheStreamlines parameter.

        Parameters
        ----------
        sl: SisypheStreamlines
            copy streamline attributes to sl
        """
        sl._ID = self._ID
        sl._shape = self._shape
        sl._spacing = self._spacing
        sl._dirname = self._dirname
        sl._regstep = self._regstep
        sl._whole = self._whole
        sl._centroid = self._centroid
        sl._atlas = self._atlas
        sl._trf = self._trf
        sl.setName(self.getName())

    def copyAttributesFrom(self, sl: SisypheStreamlines) -> None:
        """
        Copy attributes from SisypheStreamlines parameter to current SisypheStreamlines instance.

        Parameters
        ----------
        sl: SisypheStreamlines
            copy streamline attributes from sl
        """
        self._ID = sl._ID
        self._shape = sl._shape
        self._spacing = sl._spacing
        self._dirname = sl._dirname
        self._regstep = sl._regstep
        self._whole = sl._whole
        self._centroid = sl._centroid
        self._atlas = sl._atlas
        self._trf = sl._trf
        self.setName(sl.getName())

    # Public representation methods

    def setFloatColor(self, c: vector3float, bundle: str = 'all') -> None:
        """
        Set the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[float, float, float] | list[float, float, float]
            bundle color red, green, blue (each component between 0.0 and 1.0)
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setFloatColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setIntColor(self, c: vector3int, bundle: str = 'all') -> None:
        """
        Set the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : tuple[int, int, int] | list[int, int, int]
            bundle color red, green, blue (each component between 0 and 255)
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setIntColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setQColor(self, c: QColor, bundle: str = 'all') -> None:
        """
        Set the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        c : PyQt5.QtGui.QColor
            bundle color
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setQColor(c)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getFloatColor(self, bundle: str = 'all') -> vector3float:
        """
        Get the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        tuple[float, float, float] | list[float, float, float]
            bundle color red, green, blue (each component between 0.0 and 1.0)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getFloatColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getIntColor(self, bundle: str = 'all') -> vector3int:
        """
        Get the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        c : tuple[int, int, int] | list[int, int, int]
            bundle color red, green, blue (each component between 0 and 255)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getIntColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getQColor(self, bundle: str = 'all') -> QColor:
        """
        Get the bundle color attribute of the current SisypheStreamlines instance. The color attribute is only used in
        COLOR mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        c : PyQt5.QtGui.QColor
            bundle color
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getQColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setLut(self, lut: str | SisypheLut, bundle: str = 'all') -> None:
        """
        Set the bundle look-up table colormap attribute the current SisypheStreamlines instance. The look-up table
        colormap attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        lut : str | Sisyphe.core.SisypheLUT.SisypheLut
            look-up table colormap
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setLut(lut)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getLut(self, bundle: str = 'all') -> SisypheLut:
        """
        Get the bundle look-up table colormap attribute of the current SisypheStreamlines instance. The look-up table
        colormap attribute is only used in CMAP mode representation (see setColorRepresentation() method).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        Sisyphe.core.sisypheLUT.SisypheLut
            bundle lut
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getLut()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentation(self, v: int, bundle: str = 'all') -> None:
        """
        Set the bundle color representation attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        v : int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the streamline (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentation(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getColorRepresentation(self, bundle: str = 'all') -> int:
        """
        Get the bundle color representation attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        int
            representation code:
                - 0, RGB mode, colors derived from unit vector directed to next point of the streamline (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 1, CMAP mode, colors derived from scalar values associated with points using the look-up table
                colormap attribute of the current instance.
                - 2, COLOR mode, solid color given by the color attribute of the current instance.
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getColorRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationAsString(self, v: str, bundle: str = 'all') -> None:
        """
        Set the bundle color representation attribute of the current SisypheStreamlines instance from a str.

        Parameters
        ----------
        v : str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the streamlineb(x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationAsString(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getColorRepresentationAsString(self, bundle: str = 'all') -> str:
        """
        Get the bundle color representation attribute of the current SisypheStreamlines instance from a str.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        str
            representation code:
                - 'rgb', RGB mode, colors derived from unit vector directed to next point of the streamline (x-axis
                component in red, y-axis component in green and z-axis component in blue).
                - 'scalars', CMAP mode, colors derived from scalar values associated with points using the look-up
                table colormap attribute of the current instance.
                - 'color', COLOR mode, solid color given by the color attribute of the current instance.
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getColorRepresentationAsString()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToRGB(self, bundle: str = 'all') -> None:
        """
        Set the bundle color representation attribute of the current SisypheStreamlines instance to RGB mode. Colors
        are derived from unit vector directed to next point of the streamline (x-axis component in red, y-axis
        component in green and z-axis component in blue).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToRGB()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToScalars(self, bundle: str = 'all') -> None:
        """
        Set the bundle color representation attribute of the current SisypheStreamlines instance to SCALARS mode.
        Colors are derived from scalar values associated with points using the look-up table colormap attribute.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToScalars()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setColorRepresentationToColor(self, bundle: str = 'all') -> None:
        """
        Set the bundle color representation attribute of the current SisypheStreamlines instance to COLOR mode. The
        bundle streamlines have a solid color given by the color attribute.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            self._bundles[bundle].setColorRepresentationToColor()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isRGBRepresentation(self, bundle: str = 'all') -> bool:
        """
        Check whether the bundle color representation of the current SisypheStreamlines instance is in RGB mode. Colors
        are derived from unit vector directed to next point of the streamline (x-axis component in red, y-axis
        component in green and z-axis component in blue).

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        bool
            True if RGB representation
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isRGBRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isScalarsRepresentation(self, bundle: str = 'all') -> bool:
        """
        Check whether the bundle color representation of the current SisypheStreamlines instance is in SCALARS mode.
        Colors are derived from scalar values associated with points using the look-up table colormap attribute.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        bool
            True if scalars representation
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isScalarsRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def isColorRepresentation(self, bundle: str = 'all') -> bool:
        """
        Check whether the bundle color representation of the current SisypheStreamlines instance is in COLOR mode.
        The bundle streamlines have a solid color given by the color attribute.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        bool
            True if color representation
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].isColorRepresentation()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setOpacity(self, v: float, bundle: str = 'all') -> None:
        """
        Set the bundle opacity attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        v : float
            bundle opacity, between 0.0 (transparent) and 1.0 (opaque)
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].setOpacity(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getOpacity(self, bundle: str = 'all') -> float:
        """
        Get the bundle opacity attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        float
            bundle opacity, between 0.0 (transparent) and 1.0 (opaque)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getOpacity()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def setLineWidth(self, v: float, bundle: str = 'all') -> None:
        """
        Set the bundle line width attribute of the current SisypheStreamlines instance in mm.

        Parameters
        ----------
        v : float
            bundle line width in mm
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].setLineWidth(v)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getLineWidth(self, bundle: str = 'all') -> float:
        """
        Get the bundle line width attribute of the current SisypheStreamlines instance in mm.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        float
            bundle line width in mm
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            return self._bundles[bundle].getLineWidth()
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # Public streamline (ndarray) processing methods

    def isStreamlineIntersectSphere(self, index: int, p: vector3float, radius: float) -> bool:
        """
        Check whether a streamline of the current SisypheStreamlines instance crosses a sphere.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container
        p : tuple[float, float, float] | list[float, float, float]
            coordinates of sphere center
        radius : float
            sphere radius in mm

        Returns
        -------
        bool
            True if the streamline crosses the sphere
        """
        if 0 <= index < len(self._streamlines):
            if self._regstep: return inside_sphere(self._streamlines[index], p, radius)
            else: return intersect_sphere(self._streamlines[index], p, radius)
        else: raise ValueError('index parameter is out of range.')

    def streamlineLength(self, index: int) -> float:
        """
        Get the length of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        float
            streamline length
        """
        if 0 <= index < len(self._streamlines):
            reg, step = self.getStepSize(self._streamlines[index])
            if reg: return step * len(self._streamlines[index])
            else: return length(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def streamlineMeanCurvature(self, index: int) -> float:
        """
        Get the mean curvature of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        float
            mean curvature of the streamline
        """
        if 0 <= index < len(self._streamlines):
            return mean_curvature(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def streamlineCenterOfMass(self, index: int) -> vector3float:
        """
        Get the center of mass of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        tuple[float, float, float]
            center of mass of the streamline
        """
        if 0 <= index < len(self._streamlines):
            return center_of_mass(self._streamlines[index])
        else: raise ValueError('index parameter is out of range.')

    def streamlinePrincipalDirection(self, index: int) -> vector3float:
        """
        Get the principal direction of a streamline of the current SisypheStreamlines instance. PCA is used to
        calculate the 3 principal directions for a streamline.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        list[float, float, float]
            unit vector of the principal direction
        """
        if 0 <= index < len(self._streamlines):
            va, ve = principal_components(self._streamlines[index])
            return list(ve[va.argmax()])
        else: raise ValueError('index parameter is out of range.')

    def streamlineMidPoint(self, index: int) -> vector3float:
        """
        Get the mid-point of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        tuple[float, float, float]
            mid-point of the streamline
        """
        if 0 <= index < len(self._streamlines):
            return list(midpoint(self._streamlines[index]))
        else: raise ValueError('index parameter is out of range.')

    def streamlineFirstPoint(self, index: int) -> vector3float:
        """
        Get the first point of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        tuple[float, float, float]
            first point of the streamline
        """
        if 0 <= index < len(self._streamlines):
            return self._streamlines[index][0]
        else: raise ValueError('index parameter is out of range.')

    def streamlineLastPoint(self, index: int) -> vector3float:
        """
        Get the last point of a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container

        Returns
        -------
        tuple[float, float, float]
            last point of the streamline
        """
        if 0 <= index < len(self._streamlines):
            return self._streamlines[index][-1]
        else: raise ValueError('index parameter is out of range.')

    def streamlineDistanceToMidPoint(self, index: int, p: vector3float) -> float:
        """
        Get the distance between of a point and the mid-point of a streamline of the current SisypheStreamlines
        instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container
        p : tuple[float, float, float] | list[float, float, float]
            point coordinates

        Returns
        -------
        tuple[float, float, float]
            distance between of the given point and the mid-point of the streamline
        """

        if 0 <= index < len(self._streamlines):
            return midpoint2point(self._streamlines[index], p)
        else: raise ValueError('index parameter is out of range.')

    def streamlinePointIndex(self, index: int, p: vector3float, tol: float = 0.1) -> int | None:
        """
        Get the index a point in a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container
        p : tuple[float, float, float] | list[float, float, float]
            point coordinates
        tol : float
            tolerance (default 0.1)

        Returns
        -------
        int | None
            point index in the streamline of the current SisypheStreamlines instance. If point is not in the
            streamline, returns None
        """
        if 0 <= index < len(self._streamlines):
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(self._streamlines[index])):
                if allclose(self._streamlines[index][i], p, rtol=0.0, atol=tol): return i
        else: return None

    def streamlinePointFromDistance(self, index: int, d: float, percent: bool = False) -> vector3float:
        """
        Get a point at a given distance from the start along a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container
        d : float
            distance from the start, as ratio, or in mm
        percent : bool
            if True, d is expressed as a ratio value, between 0.0 and 1.0. Otherwise, d is expressed as absolute value
            in mm

        Returns
        -------
        tuple[float, float, float]
            point coordinates at distance d from the start along the streamline
        """
        if 0 <= index < len(self._streamlines):
            sl = self._streamlines[index]
            l = length(sl)
            if percent: d *= l
            if d == 0.0: return sl[0]
            elif d == l: return sl[-1]
            else: return arbitrarypoint(sl, d)
        else: raise ValueError('index parameter is out of range.')

    def streamlinePointIndexFromDistance(self, index: int, d: float, percent: bool = False) -> int:
        """
        Get a point at a given distance from the start along a streamline of the current SisypheStreamlines instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamlines instance container
        d : float
            distance from the start, as ratio, or in mm
        percent : bool
            if True, d is expressed as a ratio value, between 0.0 and 1.0. Otherwise, d is expressed as absolute value
            in mm

        Returns
        -------
        int
            point index at distance d from the start along the streamline
        """
        if 0 <= index < len(self._streamlines):
            p = self.streamlinePointFromDistance(index, d, percent)
            return self.streamlinePointIndex(index, p)
        else: raise ValueError('index parameter is out of range.')

    def minimumClosestDistanceBetweenStreamlines(self, index1: int, index2: int) -> float:
        """
        Get the minimum distance between two streamlines of the current SisypheStreamline instance.

        Parameters
        ----------
        index1 : int
            first streamline index in the current SisypheStreamline instance
        index2 : int
            second streamline index in the current SisypheStreamline instance

        Returns
        -------
        float
            minimum distance between the two streamlines in mm
        """
        if index1 >= len(self._streamlines): raise ValueError('index1 parameter is out of range.')
        if index2 >= len(self._streamlines): raise ValueError('index2 parameter is out of range.')
        sl1 = self._streamlines[index1]
        sl2 = self._streamlines[index2]
        return minimum_closest_distance(sl1, sl2)

    def streamlineScalarsFromVolume(self, index: int, vol: SisypheVolume) -> ndarray:
        """
        Get scalar values in a Sisyphe.core.sisypheVolume.SisypheVolume instance along a streamline of the current
        SisypheStreamline instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamline instance
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to get scalar values

        Returns
        -------
        numpy.ndarray
            numpy ndarray of scalar values (same size as the number of points in the streamline)
        """
        if 0 <= index < len(self._streamlines):
            img = vol.getNumpy(defaultshape=False)
            affine = diag(list(vol.getSpacing()) + [1.0])
            return values_from_volume(img, [self._streamlines[index]], affine)
        else: raise ValueError('index parameter is out of range.')

    def streamlineScalarStatisticsFromVolume(self, index: int, vol: SisypheVolume) -> dict[str: float]:
        """
        Get descriptive statistics of scalar values in a Sisyphe.core.sisypheVolume.SisypheVolume instance along a
        streamline of the current SisypheStreamline instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamline instance
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to get scalars

        Returns
        -------
        dict[str: float]
            descriptive statistics dict, keys(str), values (float) :
                - 'min', minimum
                - 'perc5', 5th percentile
                - 'perc25', first quartile
                - 'median', median
                - 'perc75', third quartile
                - 'perc95', 95th percentile
                - 'max', maximum
                - 'std', standard deviation
                - 'mean', mean
                - 'skewness', skewness
                - 'kurtosis', kurtosis
        """
        if 0 <= index < len(self._streamlines):
            data = self.streamlineScalarsFromVolume(index, vol)
            r = describe(data)
            stats = dict()
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = median(data)
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('index parameter is out of range.')

    def streamlineScalarHistogramFromVolume(self, index: int,  vol: SisypheVolume, bins: int = 10) -> ndarray:
        """
        Get histogram of scalar values in a Sisyphe.core.sisypheVolume.SisypheVolume instance along a streamline of the
        current SisypheStreamline instance.

        Parameters
        ----------
        index : int
            streamline index in the current SisypheStreamline instance
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to get scalars
        bins : int
            histogram bins (default 10)

        Returns
        -------
        numpy.ndarray
            histogram
        """
        if 0 <= index < len(self._streamlines):
            data = self.streamlineScalarsFromVolume(index, vol)
            # noinspection PyTypeChecker
            return histogram(data, bins)
        else: raise ValueError('index parameter is out of range.')

    # Public bundle processing methods

    def bundleIntersectSphere(self,
                              p: vector3float,
                              radius: float,
                              include: bool = False,
                              inplace: bool = False,
                              bundle: str = 'all') -> SisypheBundle:
        """
        Create a new bundle from streamlines of a bundle in the current SisypheStreamlines instance that cross a sphere.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float, float, float]
            coordinates of sphere center
        radius : float
            sphere radius in mm
        include : bool
            True for inclusion in sphere, otherwise exclusion from sphere (default False)
        inplace : bool
            if True, the initial bundle of the current SisypheStreamlines instance is replaced (default False)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines that cross the sphere
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            # noinspection PyUnresolvedReferences,PyTypeHints
            r: list[cython.int] = list()
            bundleout = SisypheBundle()
            if include:
                for i in range(self._bundles[bundle].count()):
                    idx = self._bundles[bundle][i]
                    if inside_sphere(self._streamlines[idx], p, radius) > 0:
                        r.append(idx)
            else:
                for i in range(self._bundles[bundle].count()):
                    idx = self._bundles[bundle][i]
                    if inside_sphere(self._streamlines[idx], p, radius) == 0:
                        r.append(idx)
            if len(r) > 0: bundleout.appendTracts(r)
            if inplace:
                bundleout.setName(bundle)
                self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleIntersectPlane(self,
                             p: vector3float,
                             planes: tuple[bool, bool, bool] | list[bool],
                             include: bool = False,
                             inplace: bool = False,
                             bundle: str = 'all') -> SisypheBundle:
        """
        Create a new bundle with streamlines that cross (or not) a plane.
        A streamline is included/excluded if one of its points crosses the x-axis plane.
        A streamline is included/excluded if one of its points crosses the y-axis plane.
        A streamline is included/excluded if one of its points crosses the z-axis plane.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float, float, float]
            coordinates of plane center
        planes : tuple[int, int, int] | list[int, int, int]
            - first bool, x-axis inclusion/exclusion
            - second bool, y-axis inclusion/exclusion
            - third bool, z-axis, inclusion/exclusion
        include : bool
            - True, streamlines that cross plane are included
            - False, streamlines that cross plane are excluded
        inplace : bool
            if True, the initial bundle of the current SisypheStreamlines instance is replaced (default False)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines that cross the sphere
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            # noinspection PyUnresolvedReferences
            j: cython.int
            # noinspection PyUnresolvedReferences
            k: cython.int
            p = array(p)
            planes = array(planes)[:3]
            bundleout = SisypheBundle()
            # noinspection PyUnresolvedReferences,PyTypeHints
            r: list[cython.int] = list()
            for i in range(self._bundles[bundle].count()):
                idx = self._bundles[bundle][i]
                sl = self._streamlines[idx]
                s0 = sign(sl[0] - p)
                flag = not include
                for j in range(len(sl)-1, 0, -1):
                    s = sign(sl[j] - p)
                    cross = s != s0
                    # < Revision 11/04/2025
                    # buf fix, cross = cross and planes
                    cross = cross & planes
                    # Revision 11/04/2025 >
                    if any(cross):
                        flag = include
                        break
                if flag: r.append(idx)
            bundleout.appendTracts(r)
            if inplace:
                bundleout.setName(bundle)
                self._bundles[bundle] = bundleout
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleLengths(self, bundle: str = 'all') -> ndarray:
        """
        Get the lengths of streamlines in a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            streamline lengths
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            r: list[float] = list()
            reg, step = self.getStepSize(self._streamlines[0])
            if reg:
                for i in range(self._bundles[bundle].count()):
                    index = self._bundles[bundle][i]
                    r.append(step * len(self._streamlines[index]))
            else:
                for i in range(self._bundles[bundle].count()):
                    index = self._bundles[bundle][i]
                    r.append(length(self._streamlines[index]))
            return array(r)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleLengthStatistics(self, bundle: str = 'all') -> dict[str: float]:
        """
        Get the descriptive statistics of streamline lengths in a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dict[str: float]
            descriptive statistics of streamline lengths, keys(str), values (float) :
                - 'min', minimum
                - 'perc5', 5th percentile
                - 'perc25', first quartile
                - 'median', median
                - 'perc75', third quartile
                - 'perc95', 95th percentile
                - 'max', maximum
                - 'std', standard deviation
                - 'mean', mean
                - 'skewness', skewness
                - 'kurtosis', kurtosis
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = self.bundleLengths(bundle)
            r = describe(data)
            stats = dict()
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = median(data)
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleMeanCurvatures(self, bundle: str = 'all') -> ndarray:
        """
        Get the mean curvatures of streamlines in a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            streamline mean curvatures
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            r: list[float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                r.append(self.streamlineMeanCurvature(index))
            return array(r)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleMeanCurvatureStatistics(self, bundle: str = 'all') -> dict[str: float]:
        """
        Get the descriptive statistics of streamline mean curvatures in a bundle of the current SisypheStreamlines
        instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dict[str: float]
            descriptive statistics of streamline mean curvatures, keys(str), values (float) :
                - 'min', minimum
                - 'perc5', 5th percentile
                - 'perc25', first quartile
                - 'median', median
                - 'perc75', third quartile
                - 'perc95', 95th percentile
                - 'max', maximum
                - 'std', standard deviation
                - 'mean', mean
                - 'skewness', skewness
                - 'kurtosis', kurtosis
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = array(self.bundleMeanCurvatures(bundle))
            r = describe(data)
            stats = dict()
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = median(data)
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleClusterConfidence(self,
                                mdf: int = 5,
                                power: int = 1,
                                subsample: int = 12,
                                bundle: str = 'all') -> ndarray:
        """
        Computes the cluster confidence index (cci), which is an estimation of the support a set of streamlines gives
        to a particular pathway. The cci provides a voting system where by each streamline (within a set tolerance)
        gets to vote on how much support it lends to. Outlier pathways score relatively low on cci, since they do not
        have many streamlines voting for them. These outliers can be removed by thresholding on the cci metric.

        Parameters
        ----------
        mdf : int
            maximum MDF distance (mm) that will be considered a 'supporting' streamline and included in cci calculation
            (default 5 mm)
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time,
            each streamline is subsampled (default 12 points)
        power : int
            power to which the MDF distance for each streamline will be raised to determine how much it contributes to
            the cci. High values of power make the contribution value degrade much faster. e.g., a streamline with 5 mm
            MDF similarity contributes 1/5 to the cci if power is 1, but only contributes 1/5^2 = 1/25 if power is 2
            (default 1).
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            cci
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            cci = cluster_confidence(sl, max_mdf=mdf, subsample=subsample, power=power)
            return cci
        else: raise ValueError('Invalid bundle name.')

    def bundleClusterConfidenceStatistics(self,
                                          mdf: int = 5,
                                          power: int = 1,
                                          subsample: int = 12,
                                          bundle: str = 'all') -> dict[str: float]:
        """
        Get the descriptive statistics of streamline cluster confidence index in a bundle
        of the current SisypheStreamlines instance.

        Parameters
        ----------
        mdf : int
            maximum MDF distance (mm) that will be considered a 'supporting' streamline and included in cci calculation
            (default 5 mm)
        power : int
            power to which the MDF distance for each streamline will be raised to determine how much it contributes to
            the cci. High values of power make the contribution value degrade much faster. e.g., a streamline with 5 mm
            MDF similarity contributes 1/5 to the cci if power is 1, but only contributes 1/5^2 = 1/25 if power is 2
            (default 1).
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time,
            each streamline is subsampled (default 12 points)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dict[str: float]
            descriptive statistics of streamline mean curvatures, keys(str), values (float) :
                - 'min', minimum
                - 'perc5', 5th percentile
                - 'perc25', first quartile
                - 'median', median
                - 'perc75', third quartile
                - 'perc95', 95th percentile
                - 'max', maximum
                - 'std', standard deviation
                - 'mean', mean
                - 'skewness', skewness
                - 'kurtosis', kurtosis
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = self.bundleClusterConfidence(mdf, power, subsample, bundle)
            r = describe(data)
            stats = dict()
            # noinspection PyUnresolvedReferences
            stats['min'] = r.minmax[0]
            stats['perc5'] = percentile(data, 5)
            stats['perc25'] = percentile(data, 25)
            stats['median'] = median(data)
            stats['perc75'] = percentile(data, 75)
            stats['perc95'] = percentile(data, 95)
            # noinspection PyUnresolvedReferences
            stats['max'] = r.minmax[1]
            # noinspection PyUnresolvedReferences
            stats['std'] = sqrt(r.variance)
            # noinspection PyUnresolvedReferences
            stats['mean'] = r.mean
            # noinspection PyUnresolvedReferences
            stats['skewness'] = r.skewness
            # noinspection PyUnresolvedReferences
            stats['kurtosis'] = r.kurtosis
            return stats
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCentersOfMass(self, bundle: str = 'all') -> list[vector3float]:
        """
        Get the streamlines centers of mass in a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        list[list[float, float, float]
            streamline centers of mass
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            r: list[vector3float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                r.append(self.streamlineCenterOfMass(index))
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCosineDistanceBetweenEndVectors(self, bundle: str = 'all') -> ndarray:
        """
        Get the cosine distance between endpoint vectors of streamlines in a bundle of the current SisypheStreamlines
        instance. The cosine distance between two vector A and B is (A.B) / (||A||.||B||)

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            cosine distance between endpoint vectors of streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            r: list[float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                sl = self._streamlines[index]
                if len(sl) > 3:
                    s1 = sl[0] - sl[1]
                    s2 = sl[-2] - sl[-1]
                    c = dot(s1, s2) / (norm(s1) * norm(s2))
                    r.append(c)
                else: r.append(1.0)
            return array(r)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleEuclideanDistanceBetweenEndPoints(self, bundle: str = 'all') -> ndarray:
        """
        Get the euclidean distance between endpoint of streamlines in a bundle of the current SisypheStreamlines
        instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            euclidean distance between endpoint vectors of streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            # noinspection PyUnresolvedReferences
            i: cython.int
            r: list[float] = list()
            for i in range(self._bundles[bundle].count()):
                index = self._bundles[bundle][i]
                sl = self._streamlines[index]
                if len(sl) > 1:
                    d = sqrt(((sl[0] - sl[-1]) ** 2).sum())
                    r.append(d)
                else: r.append(0.0)
            return array(r)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleScalarsFromVolume(self, vol: SisypheVolume, bundle: str = 'all') -> list[ndarray]:
        """
        Get scalar values in a Sisyphe.core.sisypheVolume.SisypheVolume instance along the streamlines in a bundle of
        the current SisypheStreamline instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        list[numpy.ndarray]
            scalar values
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            img = vol.getNumpy(defaultshape=False)
            affine = diag(list(vol.getSpacing()) + [1.0])
            return values_from_volume(img, sl, affine)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleScalarStatisticsFromVolume(self, vol: SisypheVolume, bundle: str = 'all') -> dict[str: float]:
        """
        Get descriptive statistics of scalar values in a Sisyphe.core.sisypheVolume.SisypheVolume instance along the
        streamlines in a bundle of the current SisypheStreamline instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to get scalars
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dict[str: float]
            descriptive statistics dict, keys(str), values (float) :
                - 'min', minimum
                - 'perc5', 5th percentile
                - 'perc25', first quartile
                - 'median', median
                - 'perc75', third quartile
                - 'perc95', 95th percentile
                - 'max', maximum
                - 'std', standard deviation
                - 'mean', mean
                - 'skewness', skewness
                - 'kurtosis', kurtosis
        """
        data = self.bundleScalarsFromVolume(vol, bundle)
        data = array(data).flatten()
        r = describe(data)
        stats = dict()
        # noinspection PyUnresolvedReferences
        stats['min'] = r.minmax[0]
        stats['perc5'] = percentile(data, 5)
        stats['perc25'] = percentile(data, 25)
        stats['median'] = median(data)
        stats['perc75'] = percentile(data, 75)
        stats['perc95'] = percentile(data, 95)
        # noinspection PyUnresolvedReferences
        stats['max'] = r.minmax[1]
        # noinspection PyUnresolvedReferences
        stats['std'] = sqrt(r.variance)
        # noinspection PyUnresolvedReferences
        stats['mean'] = r.mean
        # noinspection PyUnresolvedReferences
        stats['skewness'] = r.skewness
        # noinspection PyUnresolvedReferences
        stats['kurtosis'] = r.kurtosis
        return stats

    def bundleScalarHistogramFromVolume(self, vol: SisypheVolume, bins: int = 10,  bundle: str = 'all') -> ndarray:
        """
        Get scalar values histogram in a Sisyphe.core.sisypheVolume.SisypheVolume instance along the streamlines in a
        bundle of the current SisypheStreamline instance.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume used to get scalars
        bins : int
            histogram bins (default 10)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        numpy.ndarray
            histogram
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            data = self.bundleScalarsFromVolume(vol, bundle)
            data = array(data).flatten()
            # noinspection PyTypeChecker
            return histogram(data, bins)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getStreamlineIndexesSortedByLength(self, bundle: str = 'all') -> list[int]:
        """
        Get indices of streamlines sorted by length in a bundle of the current SisypheStreamline instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        list[int]
            list of indices of streamlines sorted by length
        """
        sl = self.getStreamlinesFromBundle(bundle)
        # noinspection PyTypeChecker
        return list(longest_track_bundle(sl, sort=True))

    def getLongestStreamlineIndex(self, bundle: str = 'all') -> int:
        """
        Get index of the longest streamline in a bundle of the current SisypheStreamline instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        int
            index of the longest streamline
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            idx = self.getStreamlineIndexesSortedByLength(bundle)[-1]
            return self._bundles[bundle][idx]
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def getShortestStreamlineIndex(self, bundle: str = 'all') -> int:
        """
        Get index of the shortest streamline in a bundle of the current SisypheStreamline instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        int
            index of the shortest streamline
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            idx = self.getStreamlineIndexesSortedByLength(bundle)[0]
            return self._bundles[bundle][idx]
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleStreamlinesLongerThan(self, bundle: str = 'all', l: float = 10.0) -> SisypheBundle:
        """
        Create a new bundle with streamlines whose lengths are longer than a threshold.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        l : float
            streamline length threshold in mm

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines selected by a lengths threshold
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            tracts = list()
            for idx in self._bundles[bundle]:
                if length(self._streamlines[idx]) >= l: tracts.append(idx)
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleStreamlinesShorterThan(self, bundle: str = 'all', l: float = 10.0) -> SisypheBundle:
        """
        Create a new bundle with streamlines whose lengths are shorter than a threshold.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        l : float
            streamline length threshold in mm

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines selected by a lengths threshold
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            tracts = list()
            for idx in self._bundles[bundle]:
                if length(self._streamlines[idx]) <= l: tracts.append(idx)
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleRoiSelection(self,
                           rois: SisypheROICollection,
                           include: list[bool] | None = None,
                           mode: str = 'any',
                           tol: float | None = None,
                           bundle: str = 'all') -> SisypheBundle:
        """
        Create a new bundle with streamlines of a bundle selected by ROI(s).
        These ROI(s) are used to perform virtual dissection.
        A streamline is included if any (or all) streamline point is within tol from inclusion ROI.
        A streamline is excluded if any (or all) streamline point is within tol from exclusion ROI.

        Parameters
        ----------
        rois : Sisyphe.core.sisypheROI.SisypheROICollection
            Container with ROIs (Sisyphe.core.sisypheROI.SisypheROI instances) used to select streamlines
        include : list[bool] | None
            - This list has the same number of elements as the ROI container. if list element is True, the ROI with the
            same index is used as inclusion, otherwise the ROI is used as exclusion
            - if None, all ROIs are used as inclusion
        mode : str
            - 'any' : any streamline point is within tol from ROI (Default)
            - 'all' : all streamline points are within tol from ROI
            - 'end' : either of the end-points is within tol from ROI
        tol : float | None
            - If any coordinate in the streamline is within this distance, in mm, from the center of any voxel in the
            ROI, the filtering criterion is set to True for this streamline, otherwise False.
            - if None (Default) tol is the distance between the center of each voxel and the corner of the voxel
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheBundle
             bundle with indices of streamlines selected by ROI(s)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            if include is None: include = [True] * len(rois)
            if tol is None or tol == 0.0: tol = sqrt((array(self._spacing) ** 2).sum())
            mode = mode.lower()
            if mode not in ('any', 'all', 'end'): mode = 'any'
            elif mode == 'end': mode = 'either_end'
            incl: list = list()
            excl: list = list()
            sp = array(self._spacing)
            sp2 = sp / 2
            for i in range(rois.count()):
                roi = rois[i].toIndexes(numpy=True)
                roi = (roi * sp) + sp2
                if include[i]: incl.append(roi)
                else: excl.append(roi)
            tracts = list()
            bundle = self._bundles[bundle].getList()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(bundle)):
                sl = self._streamlines[bundle[i]]
                tag: bool = True
                if len(excl) > 0:
                    for select in excl:
                        if streamline_near_roi(sl, select, tol, mode):
                            tag = False
                            break
                if tag and len(incl) > 0:
                    for select in incl:
                        if not streamline_near_roi(sl, select, tol, mode):
                            tag = False
                            break
                    if tag: tracts.append(bundle[i])
                # if len(list(select_by_rois([sl], affine, rois2, include, mode=mode, tol=tol))) > 0:
                #    tracts.append(bundle[i])
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleClusterConfidenceFiltering(self,
                                         mdf: int = 5,
                                         subsample: int = 12,
                                         power: int = 1,
                                         ccithreshold: float = 1.0,
                                         bundle: str = 'all') -> tuple[SisypheBundle, ndarray]:
        """
        Create a new bundle with streamlines of a bundle selected by a clustering confidence algorithm. Computes the
        cluster confidence index (cci), which is an estimation of the support a set of streamlines gives to a
        particular pathway. The cci provides a voting system where by each streamline (within a set tolerance) gets to
        vote on how much support it lends to. Outlier pathways score relatively low on cci, since they do not have many
        streamlines voting for them. These outliers can be removed by thresholding on the cci metric.

        Parameters
        ----------
        mdf : int
            maximum MDF distance (mm) that will be considered a 'supporting' streamline and included in cci calculation
            (default 5 mm)
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time,
            each streamline is subsampled (default 12 points)
        power : int
            power to which the MDF distance for each streamline will be raised to determine how much it contributes to
            the cci. High values of power make the contribution value degrade much faster. e.g., a streamline with 5 mm
            MDF similarity contributes 1/5 to the cci if power is 1, but only contributes 1/5^2 = 1/25 if power is 2
            (default 1).
        ccithreshold : float
            cci threshold used to select streamlines
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        tuple[SisypheBundle, ndarray]
            - SisypheBundle, indices of streamlines with cci >= ccithreshold
            - ndarray, cci values
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            cci = cluster_confidence(sl, max_mdf=mdf, subsample=subsample, power=power)
            tracts = list()
            bundle = self._bundles[bundle].getList()
            # noinspection PyUnresolvedReferences
            i: cython.int
            for i in range(len(cci)):
                if cci[i] >= ccithreshold: tracts.append(bundle[i])
            r = SisypheBundle()
            r.appendTracts(tracts)
            return r, cci
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleMajorClusterCentroid(self, threshold: float = 10.0, bundle: str = 'all') -> Streamlines:
        """
        Get the major cluster centroid streamline of a bundle.

        Parameters
        ----------
        threshold : float
            maximum distance from a bundle for a streamline to be still considered as part of it (Default 10 mm).
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dipy.tracking.Streamlines
            centroid streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            # noinspection PyTypeChecker
            cl = cluster_bundle(sl, threshold, rng=None)
            cll = list(map(len, cl))
            i = cll.index(max(cll))
            return cl[i].centroid
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleCentroidDistanceSelection(self,
                                        centroid: ndarray,
                                        subsample: int = 12,
                                        dist: str = 'mam',
                                        threshold: float = 10.0,
                                        bundle: str = 'all') -> SisypheBundle:
        """
        Create a new bundle with streamlines of a bundle selected by a distance to centroid threshold.

        Parameters
        ----------
        centroid : ndarray
            centroid streamline used as reference to select streamlines
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time,
            each streamline is subsampled (default 12 points)
        dist : str
            - 'mam' mean average minimum distance
            - 'mdf' average pointwise euclidean distance
        threshold : float
            dist parameter threshold (default 10.0 mm)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines selected
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            centroid = set_number_of_points(Streamlines(centroid), subsample)
            sl = set_number_of_points(self.getStreamlinesFromBundle(bundle), subsample)
            if dist == 'mam': indices = bundles_distances_mam(centroid, sl)
            else: indices = bundles_distances_mdf(centroid, sl)
            tracts = list()
            for j in range(len(sl)):
                if indices[0, j] < threshold:
                    tracts.append(self._bundles[bundle][j])
            bundleout = SisypheBundle()
            bundleout.appendTracts(tracts)
            return bundleout
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleClustering(self,
                         threshold: float | None = None,
                         nbp: int = 12,
                         metric: str = 'apd',
                         minclustersize: int = 10,
                         bundle: str = 'all') -> tuple[SisypheBundleCollection, list[SisypheStreamlines]]:
        """
        Create a new bundle with streamlines of a bundle selected by a clustering algorithm.

        Parameters
        ----------
        threshold : float
            maximum distance from a bundle for a streamline to be still considered as part of it. (Default 10 mm)
        nbp : int
            streamlines are subsampled, number of points per streamline
        metric : str
            - 'apd' average pointwise euclidean distance (default)
            - 'cmd' center of mass euclidean distance
            - 'mpd' midpoint euclidean distance
            - 'lgh' length
            - 'ang' vector between endpoints
        minclustersize : int
            minimum cluster size (number of streamlines, default 10)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        tuple[SisypheBundleCollection, list[SisypheStreamlines]]
            - SisypheBundleCollection, clusters
            - list[SisypheStreamlines], centroid streamlines of clusters
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            width: float = 10.0
            # Streamline average pointwise euclidean distance
            if metric == 'apd':
                if threshold is None: threshold = 10.0
                feature = ResampleFeature(nb_points=nbp)
                metric = AveragePointwiseEuclideanMetric(feature=feature)
                width = threshold
            # Streamline center of mass euclidean distance
            elif metric == 'cmd':
                if threshold is None: threshold = 5.0
                feature = CenterOfMassFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline midpoint euclidean distance
            elif metric == 'mpd':
                if threshold is None: threshold = 5.0
                feature = MidpointFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline length
            elif metric == 'lgh':
                if threshold is None: threshold = 2.0
                feature = ArcLengthFeature()
                metric = EuclideanMetric(feature=feature)
            # Streamline vector between endpoints
            elif metric == 'ang':
                if threshold is None: threshold = 0.1
                feature = VectorOfEndpointsFeature()
                metric = CosineMetric(feature=feature)
            else: raise ValueError('Invalid metric ({})'.format(metric))
            f = QuickBundles(threshold, metric=metric)
            clusters = f.cluster(sl)
            select = clusters > minclustersize
            centroids = list()
            r = SisypheBundleCollection()
            if select.any():
                # noinspection PyUnresolvedReferences
                c: cython.int = 1
                # noinspection PyUnresolvedReferences
                i: cython.int
                # noinspection PyUnresolvedReferences
                j: cython.int
                for i in range(len(clusters)):
                    if select[i]:
                        tracts = list()
                        indices = clusters[i].indices
                        for j in range(len(indices)):
                            tracts.append(self._bundles[bundle][indices[j]])
                        bundleout = SisypheBundle()
                        bundleout.setName(self.getName() + ' cluster#{}'.format(c))
                        bundleout.appendTracts(tracts)
                        r.append(bundleout)
                        slc = SisypheStreamlines(clusters[i].centroid)
                        slc.setReferenceID(self.getReferenceID())
                        slc.setName(self.getName() + ' cluster#{} centroid'.format(c))
                        slc.setLineWidth(width)
                        slc.changeStreamlinesStepSize(step=1.0, inplace=True)
                        centroids.append(slc)
                        c += 1
            return r, centroids
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleFastClustering(self,
                             threshold: float = 10.0,
                             minclustersize: int = 10,
                             bundle: str = 'all') -> tuple[SisypheBundleCollection, list[SisypheStreamlines]]:
        """
        Create a new bundle with streamlines of a bundle selected by a clustering algorithm (fast version).

        Parameters
        ----------
        threshold : float
            maximum distance from a bundle for a streamline to be still considered as part of it. (Default 10 mm)
        minclustersize : int
            minimum cluster size (number of streamlines, default 10)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        tuple[SisypheBundleCollection, dipy.tracking.Streamlines]
            - SisypheBundleCollection, clusters
            - list[SisypheStreamlines], centroid streamlines of clusters
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            thresholds = [30, 20, 15, threshold]
            clusters = qbx_and_merge(sl, thresholds)
            select = clusters > minclustersize
            centroids = list()
            r = SisypheBundleCollection()
            if select.any():
                # noinspection PyUnresolvedReferences
                c: cython.int = 1
                # noinspection PyUnresolvedReferences
                i: cython.int
                # noinspection PyUnresolvedReferences
                j: cython.int
                for i in range(len(clusters)):
                    if select[i]:
                        tracts = list()
                        indices = clusters[i].indices
                        for j in range(len(indices)):
                            tracts.append(self._bundles[bundle][indices[j]])
                        bundleout = SisypheBundle()
                        bundleout.setName(self.getName() + ' cluster#{}'.format(c))
                        bundleout.appendTracts(tracts)
                        r.append(bundleout)
                        slc = SisypheStreamlines(clusters[i].centroid)
                        slc.setName(self.getName() + ' cluster#{} centroid'.format(c))
                        centroids.append(slc)
                        c += 1
            return r, centroids
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleFromBundleModel(self,
                              model: Streamlines,
                              threshold: float = 15.0,
                              reduction: float = 10.0,
                              pruning: float = 5.0,
                              reductiondist: str = 'mam',
                              pruningdist: str = 'mam',
                              refine: bool = False,
                              minlength: int = 50,
                              bundle: str = 'all') -> SisypheBundle:
        """
        Create a new bundle with streamlines of a bundle selected by a model.

        Parameters
        ----------
        model : dipy.tracking.Streamlines
            streamlines used as model
        threshold : float
            distance threshold in mm for clustering streamlines (default 15.0)
        reduction : float
            distance threshold in mm for bundle reduction (default 10.0)
        pruning : float
            distance threshold in mm for bundle pruning (default 5.0)
        reductiondist : str
            - 'mdf' average pointwise euclidean distance
            - 'mam' mean average minimum distance
        pruningdist : str
            - 'mdf' average pointwise euclidean distance
            - 'mam' mean average minimum distance
        refine : bool
            if True, two stage algorithm (recognize and refine), otherwise only recognize
        minlength : int
            minimum streamline size
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheBundle
            bundle with indices of streamlines selected by model
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            f = RecoBundles(sl, greater_than=minlength)
            slf, indices = f.recognize(model,
                                       model_clust_thr=threshold,
                                       reduction_thr=reduction,
                                       reduction_distance=reductiondist,
                                       pruning_thr=pruning,
                                       pruning_distance=pruningdist)
            if refine:
                slf, indices = f.refine(model, slf,
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
                    threshold: int = 10,
                    perc: bool = False,
                    bundle: str = 'all') -> SisypheROI:
        """
        Convert a bundle of the current SisypheStreamlines instance to a ROI (Sisyphe.core.sisypheROI.SisypheROI
        instance).

        Parameters
        ----------
        threshold : int
            - absolute streamline count per voxel (if perc is False)
            - percentile of streamline count per voxel distribution (if perc is True)
        perc : bool
            absolute (default False) or percentile (True) Threshold
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROI
            bundle roi
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            dmap = self.bundleToDensityMap(bundle)
            if perc:
                if not (0.0 < threshold < 100.0): threshold = 5.0
                s = dmap.getNumpy().flatten().nonzero()
                threshold = int(percentile(s, threshold))
            roi = SisypheROI(dmap > threshold)
            roi.setName(bundle)
            s = self.getDWISpacing()
            roi.setSpacing(s[0], s[1], s[2])
            roi.setReferenceID(self.getReferenceID())
            return roi
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToMesh(self,
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
        Convert a bundle of the current SisypheStreamlines instance to a mesh (Sisyphe.core.sisypheMesh.SisypheMesh
        instance).

        Parameters
        ----------
        threshold : int
            - absolute streamline count per voxel (if perc is False)
            - percentile of streamline count per voxel distribution (if perc is True)
        perc : bool
            absolute (default False) or percentile (True) Threshold
        fill : float
            identify and fill holes in mesh (default 1000.0)
        decimate : float
            mesh points reduction percentage (between 0.0 and 1.0, default 1.0)
        clean : bool
            merge duplicate points, remove unused points and remove degenerate cells
        smooth : str
            smoothing algorithm, 'sinc' or 'laplacian'
        niter : int
            number of iterations of smoothing algorithm (default 20)
        factor : float
            - lower values produce more smoothing (between 0.0 and 1.0)
            - if smooth == 'sinc', passband factor
            - if smooth == 'laplacian', relaxation factor
        algo : str
            isosurface algorithm, 'contour', 'marching' or 'flying' (default)
        largest : bool
            keep only the largest blob (default False)
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        Sisyphe.core.sisypheMesh.SisypheMesh
            bundle mesh
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            roi = self.bundleToRoi(threshold, perc, bundle)
            mesh = SisypheMesh()
            if not roi.isEmptyArray():
                mesh.createFromROI(roi, fill, decimate, clean, smooth, niter, factor, algo, largest)
                mesh.setName(bundle)
                mesh.setReferenceID(self.getReferenceID())
            return mesh
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToDensityMap(self, bundle: str = 'all') -> SisypheVolume:
        """
        Calculate the density map of a bundle in the current SisypheStreamlines instance. The scalar values of this map
        are the number of unique streamlines that pass through each voxel.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            density map
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            affine = diag(list(self.getDWISpacing()) + [1.0])
            img = density_map(sl, affine, self.getDWIShape())
            # img dtype is int64, conversion to int16 or int32
            vmax = img.max()
            if vmax <= iinfo('int16').max: img = img.astype('int16', casting='same_kind')
            else: img = img.astype('int32', casting='same_kind')
            r = SisypheVolume()
            r.copyFromNumpyArray(img,
                                 spacing=self.getDWISpacing(),
                                 defaultshape=False)
            # < Revision 21/02/2025
            # r.setID(self.getReferenceID())
            if self.hasICBM152ReferenceID(): r.setIDtoICBM152()
            elif self.hasSRI24ReferenceID(): r.setIDtoSRI24()
            else: r.setID(self.getReferenceID())
            # Revision 21/02/2025 >
            r.acquisition.setSequenceToDensityMap()
            r.acquisition.setFrameToNo()
            r.display.setLUT('hot')
            r.display.setDefaultWindow()
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToPathLengthMap(self, roi: SisypheROI, bundle: str = 'all') -> SisypheVolume:
        """
        Calculate the path length map of a bundle in the current SisypheStreamlines instance. The scalar values of this
        map are the shortest path, along any streamline, between a reference roi and each voxel.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            reference roi
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            path length map
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = self.getStreamlinesFromBundle(bundle)
            affine = diag(list(roi.getSpacing()) + [1.0])
            img = path_length(sl, affine, roi.getNumpy(defaultshape=False), fill_value=-1)
            # img dtype is int64, conversion to int16 or int32
            # noinspection PyUnresolvedReferences
            vmax = img.max()
            # < Revision 19/06/2025
            # bug fix
            # if vmax <= iinfo('int16')
            print(vmax)
            if vmax <= iinfo('int16').max:
                # img = img.astype('int16', 'same_kind')
                # noinspection PyUnresolvedReferences
                img = img.astype('int16', casting='unsafe')
            elif vmax <= iinfo('int32').max:
                # img = img.astype('int32', 'same_kind')
                # noinspection PyUnresolvedReferences
                img = img.astype('int32', casting='unsafe')
            else:
                # noinspection PyUnresolvedReferences
                img = img.astype('int64', casting='unsafe')
            # Revision 19/06/2025 >
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(img,
                                 spacing=roi.getSpacing(),
                                 defaultshape=False)
            # < Revision 21/02/2025
            # r.setID(self.getReferenceID())
            if self.hasICBM152ReferenceID(): r.setIDtoICBM152()
            elif self.hasSRI24ReferenceID(): r.setIDtoSRI24()
            else: r.setID(self.getReferenceID())
            r.acquisition.setFrameToNo()
            r.display.setLUT('hot')
            # Revision 21/02/2025 >
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('PATH LENGTH MAP')
            return r
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def bundleToConnectivityMatrix(self, vol: SisypheVolume, bundle: str = 'all') -> DataFrame:
        """
        Calculate the connectivity matrix of a bundle in the current SisypheStreamlines instance. The connectivity
        matrix is a square matrix with as many columns (and rows) as there are labels in a label volume. Each element
        corresponds to the number of streamlines that start and end at each pair of labels in the label volume.


        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            label volume, Sisyphe.core.sisypheVolume.SisypheVolume must a label volume
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        pandas.DataFrame
            connectivity matrix
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            if vol.acquisition.isLB():
                affine = diag(list(vol.getSpacing()) + [1.0])
                sl = self.getStreamlinesFromBundle(bundle)
                a = connectivity_matrix(sl, affine=affine, label_volume=vol.getNumpy(defaultshape=False))
                labels = list(vol.acquisition.getLabels().values())
                return DataFrame(a, index=labels, columns=labels)
            else: raise ValueError('{} volume parameter modality {} is not LB.'.format(vol.getBasename(),
                                                                                       vol.acquisition.getModality()))
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def addBundleToSisypheTractCollection(self, tracts: SisypheTractCollection, bundle: str = 'all'):
        """
        Add streamlines of a bundle in the current SisypheStreamlines instance to a SisypheTractCollection instance.

        Parameters
        ----------
        tracts : SisypheTractCollection
            tracts to add to bundle
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            tracts.appendBundle(self.getSisypheStreamlinesFromBundle(bundle), bundle)
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # Public streamlines processing methods

    def getStreamlines(self) -> Streamlines:
        """
        Get dipy.tracking.Streamlines of the current SisypheStreamlines instance.

        Returns
        -------
        dipy.tracking.Streamlines
            streamlines
        """
        return self._streamlines

    def getStreamlinesFromBundle(self, bundle: str = 'all') -> Streamlines:
        """
        Get dipy.tracking.Streamlines from a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        dipy.tracking.Streamlines
            streamlines of the bundle
        """
        if bundle == 'all' or bundle == self._bundles[0].getName(): return self._streamlines
        elif bundle in self._bundles:
            return self._streamlines[self._bundles[bundle].getList()]
        else: raise ValueError('Invalid bundle name.')

    def getSisypheStreamlinesFromBundle(self, bundle: str = 'all') -> SisypheStreamlines:
        """
        Get a new SisypheStreamlines from a bundle of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines

        Returns
        -------
        SisypheStreamlines
            streamlines of the bundle
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            sl = SisypheStreamlines(sl=self.getStreamlinesFromBundle(bundle))
            sl.copyAttributesFrom(self)
            sl.setName(bundle)
            sl.setWholeBrainStatus(bundle != self.getName())
            return sl
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # noinspection PyTypeChecker
    def getSisypheStreamlinesLongerThan(self, bundle: str = 'all', l: float = 10.0) -> SisypheStreamlines | None:
        """
        Get a new SisypheStreamlines from the streamlines of a bundle of the current SisypheStreamlines instance whose
        lengths are longer than a threshold.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        l : float
            streamline length threshold in mm

        Returns
        -------
        SisypheStreamlines | None
            streamlines of a bundle longer than the threshold
        """
        sl = None
        if bundle == 'all' or bundle == self._bundles[0].getName(): sl = self._streamlines
        elif bundle in self._bundles: sl = self._streamlines[self._bundles[bundle].getList()]
        if sl is not None:
            slout = list()
            reg, step = self.getStepSize(sl[0])
            if reg:
                l = int(l / step)
                for sli in sl:
                    if len(sli) >= l: slout.append(sli)
            else:
                for sli in sl:
                    if length(sli) >= l: slout.append(sli)
            if len(slout) > 0:
                sl = SisypheStreamlines(Streamlines(slout))
                sl.copyAttributesFrom(self)
                sl.setName(bundle)
                return sl
            else: return None
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    # noinspection PyTypeChecker
    def getSisypheStreamlinesShorterThan(self, bundle: str = 'all', l: float = 10.0) -> SisypheStreamlines | None:
        """
        Get a new SisypheStreamlines from the streamlines of a bundle of the current SisypheStreamlines instance whose
        lengths are shorter than a threshold.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines
        l : float
            streamline length threshold in mm

        Returns
        -------
        SisypheStreamlines | None
            streamlines of a bundle shorter than the threshold
        """
        sl = None
        if bundle == 'all' or bundle == self._bundles[0].getName(): sl = self._streamlines
        elif bundle in self._bundles: sl = self._streamlines[self._bundles[bundle].getList()]
        if sl is not None:
            slout = list()
            reg, step = self.getStepSize(sl[0])
            if reg:
                l = int(l / step)
                for sli in sl:
                    if len(sli) >= l: slout.append(sli)
            else:
                for sli in sl:
                    if length(sli) <= l: slout.append(sli)
            if len(slout) > 0:
                sl = SisypheStreamlines(Streamlines(slout))
                sl.copyAttributesFrom(self)
                sl.setName(bundle)
                return sl
            else: return None
        else: raise ValueError('{} invalid bundle name.'.format(bundle))

    def compressStreamlines(self, inplace: bool = False) -> SisypheStreamlines | None:
        """
        Compress streamlines of the current SisypheStreamlines instance.

        Parameters
        ----------
        inplace : bool
            if True, replace streamlines of the current SisypheStreamlines instance with compressed ones

        Returns
        -------
        SisypheStreamlines | None
            compressed streamlines
        """
        sl = compress_streamlines(self._streamlines)
        if inplace:
            self._streamlines = sl
            self._regstep = False
            return None
        else:
            sl = SisypheStreamlines(sl)
            sl.copyAttributesFrom(self)
            sl._regstep = False
            return sl

    def changeStreamlinesSampling(self, factor: float, inplace: bool = False) -> SisypheStreamlines | None:
        """
        Subsample streamlines of the current SisypheStreamlines instance. This method apply a reduction in the number
        of points.

        Parameters
        ----------
        factor : float
            reduction factor for the number of points (between 0.0 and 2.0)
        inplace : bool
            if True, replace streamlines of the current SisypheStreamlines instance with compressed ones

        Returns
        -------
        SisypheStreamlines | None
            resampled streamlines
        """
        if self._regstep:
            if 0.0 < factor < 2.0:
                sl = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(len(self._streamlines)):
                    n = int(self._streamlines[i].shape[0] * factor)
                    sl.append(set_number_of_points(self._streamlines[i], n))
                sl = Streamlines(sl)
                if inplace:
                    self._streamlines = sl
                    return None
                else:
                    sl = SisypheStreamlines(sl)
                    sl.copyAttributesFrom(self)
                    return sl
            else: raise ValueError('parameter value {} is out of range [0.0 to 2.0].'.format(factor))
        else: raise AttributeError('It is not possible to change step size if streamlines are compressed.')

    def changeStreamlinesStepSize(self, step: float, inplace: bool = False) -> SisypheStreamlines | None:
        """
        Change streamlines sampling of the current SisypheStreamlines instance. This method change the step size, in
        mm, between points.

        Parameters
        ----------
        step : float
            step size between points in mm
        inplace : bool
            if True, replace streamlines of the current SisypheStreamlines instance with resampled ones

        Returns
        -------
        SisypheStreamlines | None
            resampled streamlines
        """
        if self._regstep:
            if 0.1 <= step <= 5.0:
                sl = list()
                # noinspection PyUnresolvedReferences
                i: cython.int
                for i in range(len(self._streamlines)):
                    l = length(self._streamlines[i])
                    n = int(l / step)
                    sl.append(set_number_of_points(self._streamlines[i], n))
                sl = Streamlines(sl)
                if inplace:
                    self._streamlines = sl
                    return None
                else:
                    sl = SisypheStreamlines(sl)
                    sl.copyAttributesFrom(self)
                    return sl
            else: raise ValueError('parameter value {} is out of range [0.1 to 5.0 mm].'.format(step))
        else: raise AttributeError('It is not possible to change step size for if streamlines are compressed.')

    def applyTransformToStreamlines(self, trf: SisypheTransform, inplace: bool = False) -> SisypheStreamlines | None:
        """
        Apply a geometric transformations to the streamlines of the current SisypheStreamlines instance.

        Parameters
        ----------
        trf : Sisyphe.core.sisypheTransform.SisypheTransform
            geometric transformation
        inplace : bool
            if True, replace streamlines of the current SisypheStreamlines instance with resampled ones

        Returns
        -------
        SisypheStreamlines | None
            resampled streamlines
        """
        affine = trf.getNumpyArray(homogeneous=True)
        sl = transform_streamlines(self._streamlines, affine, in_place=inplace)
        if not inplace:
            sl = SisypheStreamlines(sl)
            sl.copyAttributesFrom(self)
            sl._ID = trf.getID()
            sl._shape = trf.getSize()
            sl._spacing = trf.getSpacing()
            if self.isAtlasRegistered():
                # transformation order: template -> self._trf (1) -> current -> trf (2) -> resampled
                # apply first self_trf and then trf
                # order of matrix product: trf x self._trf
                sl._trf = matmul(trf.getNumpyArray(homogeneous=True), self._trf)
            return sl
        else:
            self._ID = trf.getID()
            self._shape = trf.getSize()
            self._spacing = trf.getSpacing()
            if self.isAtlasRegistered():
                self._trf = matmul(trf.getNumpyArray(homogeneous=True), self._trf)
            return None

    def applyAtlasTransformToStreamlines(self, inplace: bool = False) -> SisypheStreamlines | None:
        """
        Resampling of streamlines from the current SisypheStreamlines instance into atlas space.

        Parameters
        ----------
        inplace : bool
            if True, replace streamlines of the current SisypheStreamlines instance with resampled ones

        Returns
        -------
        SisypheStreamlines | None
            resampled streamlines
        """
        if self.isAtlasRegistered():
            from Sisyphe.core.sisypheTransform import SisypheTransform
            trf = SisypheTransform()
            trf.setNumpyArray(self._trf)
            trf = trf.getInverseTransform()
            trf.setID(getID_ICBM152())
            trf.setSize(getShape_ICBM152())
            trf.setSpacing([1.0, 1.0, 1.0])
            sl = self.applyTransformToStreamlines(trf, inplace)
            if not inplace: return sl
            else: return None
        else: raise AttributeError('Not coregistered to atlas.')

    def resampleAtlasBundle(self, bundle: str) -> SisypheStreamlines | None:
        """
        Resampling of atlas streamlines into the current SisypheStreamlines instance space.

        Parameters
        ----------
        bundle : str
            Atlas bundle name or short name

        Returns
        -------
        SisypheStreamlines | None
            resampled streamlines
        """
        if self.isAtlasRegistered():
            if self.isAtlasBundleName(bundle) or self.isAtlasBundleShortName(bundle):
                atlas = SisypheStreamlines()
                atlas.loadAtlasBundle(bundle)
                sl = transform_streamlines(atlas.getStreamlines(), self._trf)
                atlas2 = SisypheStreamlines(sl)
                atlas2.copyAttributesFrom(self)
                atlas2.setName(atlas.getName())
                return atlas2
            else: raise ValueError('Invalid atlas bundle name.')
        else: raise AttributeError('Not coregistered to atlas.')

    def streamlinesToDensityMap(self) -> SisypheVolume:
        """
        Calculate the density map of the current SisypheStreamlines instance (all streamlines). The scalar values of
        this map are the number of unique streamlines that pass through each voxel.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            density map
        """
        return self.bundleToDensityMap()

    def streamlinesToPathLengthMap(self, roi: SisypheROI) -> SisypheVolume:
        """
        Calculate the path length map of the current SisypheStreamlines instance (all streamlines). The scalar values
        of this map are the shortest path, along any streamline, between a reference roi and each voxel.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            reference roi

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            path length map
        """
        return self.bundleToPathLengthMap(roi)

    def streamlinesToConnectivityMatrix(self, vol: SisypheVolume | None) -> DataFrame:
        """
        Calculate the connectivity matrix of the current SisypheStreamlines instance (all streamlines). The
        connectivity matrix is a square matrix with as many columns (rows) as there are labels in a label volume. Each
        element corresponds to the number of streamlines that start and end at each pair of labels in the label volume.


        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            label volume, Sisyphe.core.sisypheVolume.SisypheVolume must be a label volume

        Returns
        -------
        pandas.DataFrame
            connectivity matrix
        """
        return self.bundleToConnectivityMatrix(vol)

    def streamlinesRoiSelection(self,
                                rois: SisypheROICollection,
                                include: list[bool] | None = None,
                                mode: str = 'any',
                                tol: float | None = None,
                                wait: DialogWait | None = None) -> SisypheStreamlines:
        """
        ROI(s) selection of streamlines in the current SisypheStreamline instance.
        These ROI(s) are used to perform virtual dissection.
        A streamline is included if any (or all) streamline point(s) is(are) within tol from inclusion ROI.
        A streamline is excluded if any (or all) streamline point(s) is(are) within tol from exclusion ROI.

        Parameters
        ----------
        rois : Sisyphe.core.sisypheROI.SisypheROICollection
            ROIs container used to select streamlines
        include : list[bool] | None
            - This list has the same number of elements as the ROI container. if list element is True, the ROI with the
            same index is used as inclusion, otherwise the ROI is used as exclusion
            - if None, all ROIs are used as inclusion
        mode : str
            - 'any' : any streamline point is within tol from ROI (Default)
            - 'all' : all streamline points are within tol from ROI
            - 'end' : either of the end-points is within tol from ROI
        tol : float | None
            - If any coordinate in the streamline is within this distance, in mm, from the center of any voxel in the
            ROI, the filtering criterion is set to True for this streamline, otherwise False.
            - if None (Default) tol is the distance between the center of each voxel and the corner of the voxel
        wait : Sisyphe.gui.dialogWait.DialogWait | None
            progress dialog (optional)

        Returns
        -------
        SisypheStreamlines
             selected streamlines
        """
        if wait is not None:
            wait.progressVisibilityOn()
            wait.setProgressRange(0, self.count() // 100)
        if mode == 'end': mode = 'either_end'
        elif mode not in ('any', 'all', 'end'): mode = 'any'
        if tol is None or tol == 0.0: tol = sqrt((array(self._spacing) ** 2).sum())
        if include is None: include = [True] * len(rois)
        # < Revision 03/04/2025
        incl: list = list()
        excl: list = list()
        sp = array(self._spacing)
        sp2 = sp / 2
        for i in range(rois.count()):
            roi = rois[i].toIndexes(numpy=True)
            roi = (roi * sp) + sp2
            if include[i]: incl.append(roi)
            else: excl.append(roi)
        # noinspection PyUnresolvedReferences
        c: cython.int = 0
        r: list = list()
        for sl in self._streamlines:
            tag: bool = True
            if len(excl) > 0:
                for select in excl:
                    if streamline_near_roi(sl, select, tol, mode=mode):
                        tag = False
                        break
            if tag and len(incl) > 0:
                for select in incl:
                    if not streamline_near_roi(sl, select, tol, mode=mode):
                        tag = False
                        break
            if tag: r.append(sl)
            if c == 100:
                c = 0
                if wait is not None: wait.incCurrentProgressValue()
            else: c += 1
        if wait is not None: wait.setCurrentProgressValue(self.count() // 100)
        sl = SisypheStreamlines(Streamlines(r))
        sl.copyAttributesFrom(self)
        sl.setWholeBrainStatus(False)
        return sl
        # Revision 03/04/2025 >

    def streamlinesSphereSelection(self,
                                   p: vector3float,
                                   radius: float,
                                   include: bool = False) -> SisypheStreamlines:
        """
        Sphere selection of streamlines in the current SisypheStreamline instance.
        A streamline is included if any streamline point(s) is(are) within sphere.
        A streamline is excluded if any streamline point(s) is(are) within sphere.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float, float, float]
            coordinates of sphere center
        radius : float
            sphere radius in mm
        include : bool
            True for inclusion in sphere, otherwise exclusion from sphere (default False)

        Returns
        -------
        SisypheStreamlines
             selected streamlines
        """
        # noinspection PyUnresolvedReferences
        i: cython.int
        slout = list()
        for i in range(self.count()):
            r = inside_sphere(self._streamlines[i], p, radius)
            if r == include: slout.append(self._streamlines[i])
        sl = SisypheStreamlines(Streamlines(slout))
        sl.copyAttributesFrom(self)
        sl.setWholeBrainStatus(False)
        return sl

    def streamlinesPlaneSelection(self,
                                  p: vector3float,
                                  planes: list[bool],
                                  include: bool = False) -> SisypheStreamlines:
        """
        Create a new bundle with streamlines that cross or do not cross a plane.
        A streamline is included/excluded if one of its points crosses the x-axis plane.
        A streamline is included/excluded if one of its points crosses the y-axis plane.
        A streamline is included/excluded if one of its points crosses the z-axis plane.

        Parameters
        ----------
        p : tuple[float, float, float] | list[float, float, float]
            coordinates of sphere center
        planes : tuple[int, int, int] | list[int, int, int]
            - first bool, x-axis inclusion/exclusion
            - second bool, y-axis inclusion/exclusion
            - third bool, z-axis, inclusion/exclusion
        include : bool
            - True, streamlines that cross plane are included
            - False, streamlines that cross plane are excluded

        Returns
        -------
        SisypheStreamlines
             selected streamlines
        """
        # noinspection PyUnresolvedReferences
        i: cython.int
        # noinspection PyUnresolvedReferences
        j: cython.int
        # noinspection PyUnresolvedReferences
        k: cython.int
        slout = list()
        p = array(p)
        planes = array(planes)
        for i in range(self.count()):
            sl = self._streamlines[i]
            s0 = sign(sl[0] - p)
            flag = not include
            for j in range(len(sl) - 1, 0, -1):
                s = sign(sl[j] - p)
                cross = s != s0
                cross = cross and planes
                if any(cross):
                    flag = include
                    break
            if flag: slout.append(sl)
        r = SisypheStreamlines(Streamlines(slout))
        r.copyAttributesFrom(self)
        r.setWholeBrainStatus(False)
        return r

    def streamlinesClusterConfidenceFiltering(self,
                                              mdf: int = 5,
                                              subsample: int = 12,
                                              power: int = 1,
                                              ccithreshold: float = 1.0) -> SisypheStreamlines | None:
        """
        Create a new bundle with streamlines of a bundle selected by a clustering confidence algorithm. Computes the
        cluster confidence index (cci), which is an estimation of the support a set of streamlines gives to a
        particular pathway. The cci provides a voting system where by each streamline (within a set tolerance) gets to
        vote on how much support it lends to. Outlier pathways score relatively low on cci, since they do not have many
        streamlines voting for them. These outliers can be removed by thresholding on the cci metric.

        Parameters
        ----------
        mdf : int
            maximum MDF distance (mm) that will be considered a 'supporting' streamline and included in cci calculation
            (default 5 mm)
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time,
            each streamline is subsampled (default 12 points)
        power : int
            power to which the MDF distance for each streamline will be raised to determine how much it contributes to
            the cci. High values of power make the contribution value degrade much faster. e.g., a streamline with 5 mm
            MDF similarity contributes 1/5 to the cci if power is 1, but only contributes 1/5^2 = 1/25 if power is 2
            (default 1).
        ccithreshold : float
            cci threshold used to select streamlines

        Returns
        -------
        SisypheStreamlines | None
             selected streamlines
        """
        cci = cluster_confidence(self._streamlines,
                                 max_mdf=mdf,
                                 subsample=subsample,
                                 power=power)
        slout = list()
        # noinspection PyUnresolvedReferences
        i: cython.int
        for i in range(len(cci)):
            if cci[i] >= ccithreshold: slout.append(self._streamlines[i])
        if len(slout) > 0:
            sl = SisypheStreamlines(Streamlines(slout))
            sl.copyAttributesFrom(self)
            sl.setWholeBrainStatus(False)
            return sl
        else: return None

    def streamlinesClustering(self,
                              metric: str = 'apd',
                              threshold: float | None = None,
                              subsample: int = 12,
                              minclustersize: int = 10) -> list[SisypheStreamlines]:
        """
        Streamlines clustering with various metric : average pointwise euclidean distance, center of mass distance,
        midpoint distance, length, angle between vector endpoints.

        Parameters
        ----------
        metric: str
            - 'apd': average pointwise euclidean distance (mm), default metric
            - 'cmd': center of mass euclidean distance (mm)
            - 'mpd': midpoint euclidean distance (mm)
            - 'lgh': length (mm)
            - 'ang': angle between vector endpoints (degrees)
        threshold : float | None
            metric value threshold :
                - average pointwise euclidean distance, default 10 mm
                - center of mass euclidean distance, default 5 mm
                - midpoint euclidean distance, default 5 mm
                - length, default 10 mm
                - angle between vector endpoints, default 80°
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time
            (default 12 points)
        minclustersize : int
            minimum cluster size (number of streamlines, default 10)

        Returns
        -------
        list[SisypheStreamlines]
            Streamlines clusters
        """
        if metric == 'apd':
            if threshold is None: threshold = 10.0
            if subsample > 24: subsample = 24
            feature = ResampleFeature(nb_points=subsample)
            mfunc = AveragePointwiseEuclideanMetric(feature=feature)
        elif metric == 'cmd':
            if threshold is None: threshold = 5.0
            feature = CenterOfMassFeature()
            mfunc = EuclideanMetric(feature=feature)
        elif metric == 'mpd':
            if threshold is None: threshold = 5.0
            feature = MidpointFeature()
            mfunc = EuclideanMetric(feature=feature)
        elif metric == 'lgh':
            if threshold is None: threshold = 10.0
            feature = ArcLengthFeature()
            mfunc = EuclideanMetric(feature=feature)
        elif metric == 'ang':
            if threshold is None: threshold = 80.0
            threshold = cos(radians(threshold))
            feature = VectorOfEndpointsFeature()
            mfunc = CosineMetric(feature=feature)
        else: raise ValueError('Invalid metric parameter.')
        f = QuickBundles(threshold, metric=mfunc)
        clusters = f.cluster(self._streamlines)
        r = list()
        for i in range(len(clusters)):
            if len(clusters[i]) > minclustersize:
                indices = clusters[i].indices
                sl = list()
                for j in indices:
                    sl.append(self._streamlines[j])
                sl2 = SisypheStreamlines(Streamlines(sl))
                sl2.copyAttributesFrom(self)
                sl2.setName(self.getName() + ' Cluster#{}'.format(i))
                sl2.setWholeBrainStatus(False)
                r.append(sl2)
        return r

    def streamlinesMajorCentroid(self,
                                 threshold: float | None = None,
                                 subsample: int = 12) -> SisypheStreamlines | None:
        """
        Get the major cluster centroid streamline.

        Parameters
        ----------
        threshold : float | None
            maximum distance from a bundle for a streamline to be still considered as part of it (Default 10 mm).
        subsample : int
            number of points that are considered for each streamline in the calculation. To save on calculation time
            (default 12 points)

        Returns
        -------
        SisypheStreamlines | None
            centroid streamline
        """
        if threshold is None: threshold = 10.0
        if subsample > 24: subsample = 24
        feature = ResampleFeature(nb_points=subsample)
        mfunc = AveragePointwiseEuclideanMetric(feature=feature)
        f = QuickBundles(threshold, metric=mfunc)
        clusters = f.cluster(self._streamlines)
        if len(clusters) > 0:
            n = list(map(len, clusters))
            i = n.index(max(n))
            sl = SisypheStreamlines(clusters[i].centroid)
            sl.copyAttributesFrom(self)
            sl.setName(self.getName() + ' Centroid')
            sl.setLineWidth(threshold)
            sl.setWholeBrainStatus(False)
            sl._centroid = True
            sl.changeStreamlinesStepSize(step=1.0, inplace=True)
            return sl
        else: return None

    def streamlinesFromAtlas(self,
                             atlas: SisypheStreamlines,
                             threshold: float = 0.1,
                             reduction: float = 25.0,
                             pruning: float = 12.0,
                             reductiondist: str = 'mdf',
                             pruningdist: str = 'mdf',
                             refine: bool = False,
                             refinereduction: float = 12.0,
                             refinepruning: float = 6.0,
                             minlength: float = 50.0,
                             wait : DialogWait | None = None) -> SisypheStreamlines:
        """
        Select streamlines from an atlas bundle. This function requires a model bundle (HCP bundle, ICBM152 space) and
        tries to extract similar looking bundle from the tractogram of the current SisypheStreamlines instance.

        Parameters
        ----------
        atlas : SisypheStreamlines
            streamlines used as bundle model
        threshold : float
            mdf distance threshold for model bundle clustering (default 15.0). Get the centroids of the model bundle
            and work with centroids instead of all streamlines. This helps speed up processing.The larger the value of
            the threshold, the fewer centroids will be, and smaller the threshold value, the more centroids will be.
            If you prefer to use all the streamlines of the model bundle, you can set this threshold to 0.1 mm.
        reduction : float
            distance threshold in mm for bundle reduction (default 25.0)
        pruning : float
            distance threshold in mm for bundle pruning (default 12.0)
        reductiondist : str
            - 'mdf' average pointwise euclidean distance (default)
            - 'mam' mean average minimum distance
        pruningdist : str
            - 'mdf' average pointwise euclidean distance (default)
            - 'mam' mean average minimum distance
        refine : bool
            if True, two stage algorithm (recognize and refine), otherwise only recognize
        refinereduction : float
            distance threshold in mm for bundle reduction at refine stage (default 12.0)
        refinepruning : float
            distance threshold in mm for bundle pruning at refine stage (default 6.0)
        minlength : int
            minimum streamline size
        wait : Sisyphe.gui.dialogWait.DialogWait
            progress dialog (optional)

        Returns
        -------
        SisypheStreamlines
            streamlines selected by model
        """
        if not self.isAtlas():
            if not self.isAtlasRegistered():
                if wait is not None: wait.addInformationText('Atlas to tractogram coregistration...')
                self.atlasRegistration()
            if wait is not None: wait.addInformationText('{} resampling...'.format(atlas.getName()))
            atlas2 = transform_streamlines(atlas.getStreamlines(), self._trf)
            # save bundle model
            filename = join(self.getDirname(), 'registered_icbm152_hcp_{}'.format(basename(atlas.getFilename())))
            slatlas = SisypheStreamlines(atlas2)
            slatlas.copyAttributesFrom(atlas)
            slatlas.setReferenceID(self.getReferenceID())
            slatlas.save(filename)
            f = RecoBundles(self._streamlines, greater_than=minlength)
            if wait is not None:
                if refine: wait.addInformationText('Recognize {} bundle...'.format(atlas.getName()))
                else: wait.addInformationText('Stage 1 - Recognize {} bundle...'.format(atlas.getName()))
            sl, _ = f.recognize(model_bundle=atlas2,
                                model_clust_thr=threshold,
                                reduction_thr=reduction,
                                reduction_distance=reductiondist,
                                pruning_thr=pruning,
                                pruning_distance=pruningdist)
            if refine:
                if wait is not None:
                    wait.addInformationText('Stage 2 - Refine {} bundle...'.format(atlas.getName()))
                sl, _ = f.refine(model_bundle=atlas2,
                                 pruned_streamlines=sl,
                                 model_clust_thr=threshold,
                                 reduction_thr=refinereduction,
                                 reduction_distance=reductiondist,
                                 pruning_thr=refinepruning,
                                 pruning_distance=pruningdist)
            sl2 = SisypheStreamlines(sl)
            sl2.copyAttributesFrom(self)
            sl2.setWholeBrainStatus(False)
            sl2.setName(atlas.getName())
            return sl2
        else: raise AttributeError('Current instance is atlas.')

    def atlasRegistration(self):
        """
        Calculate affine transformation between whole-brain atlas tractogram and tractogram of the current instance.
        This transformation is stored in affine attribute (affine transformation from HCP ICBM152 space to current
        space).
        """
        if not self.isAtlas():
            if not self.isAtlasRegistered():
                if self.isWholeBrainTractogram():
                    atlas = SisypheStreamlines()
                    atlas.loadAtlasBundle()
                    # < Revision 14/04/2025
                    # _, self._trf, _, _ = whole_brain_slr(atlas.getStreamlines(), self._streamlines, x0='affine', progressive=True)
                    _, self._trf, _, _ = whole_brain_slr(static=self._streamlines, moving=atlas.getStreamlines(), x0='affine', progressive=True)
                    # Revision 14/04/2025 >
                else: raise AttributeError('Current instance is not a whole brain tractogram.')

    # Public IO methods

    def createXML(self, doc: minidom.Document, bundle: str) -> None:
        """
        Write a bundle of the current SisypheStreamlines instance attributes to xml instance. This method is called by
        save() and saveAs() methods, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        bundle : str
            bundle name or 'all' for all streamlines
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('id')
            root.appendChild(node)
            buff = self.getReferenceID()
            if buff == '': buff = 'None'
            txt = doc.createTextNode(buff)
            node.appendChild(txt)
            # Name
            node = doc.createElement('name')
            root.appendChild(node)
            txt = doc.createTextNode(bundle)
            node.appendChild(txt)
            # Whole brain
            node = doc.createElement('whole')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._whole))
            node.appendChild(txt)
            # Centroid
            node = doc.createElement('centroid')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._centroid))
            node.appendChild(txt)
            # Atlas
            node = doc.createElement('atlas')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._atlas))
            node.appendChild(txt)
            # Atlas affine transformation
            if self._trf is not None:
                node = doc.createElement('affine')
                trf = list(self._trf.flatten())
                root.appendChild(node)
                txt = doc.createTextNode(' '.join([str(v) for v in trf]))
                node.appendChild(txt)
            # Shape
            node = doc.createElement('shape')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(v) for v in self._shape]))
            node.appendChild(txt)
            # Spacing
            node = doc.createElement('spacing')
            root.appendChild(node)
            txt = doc.createTextNode(' '.join([str(v) for v in self._spacing]))
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

    def save(self, filename: str = '', bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a PySisyphe Streamlines (.xtracts) file. If the
        filename parameter is empty, uses the file name attribute of the current SisypheStreamlines instance.

        Parameters
        ----------
        filename : str
            PySisyphe Streamlines file name
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        if len(self._streamlines) > 0:
            if bundle == 'all': bundle = self._bundles[0].getName()
            if bundle in self._bundles:
                if filename == '':
                    filename = join(self.getDirname(), bundle + self._FILEEXT)
                elif splitext(filename)[1] != self._FILEEXT:
                    filename = splitext(filename)[0] + self._FILEEXT
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
                buff = '{} {}'.format(str(len(bdata)), str(len(boffsets)))
                node = doc.createElement('offsets')
                root.appendChild(node)
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                # Datatypes
                buff = '{} {}'.format(str(data.dtype), str(offsets.dtype))
                node = doc.createElement('dtypes')
                root.appendChild(node)
                txt = doc.createTextNode(buff)
                node.appendChild(txt)
                buffxml = doc.toprettyxml().encode()  # Convert utf-8 to binary
                with open(filename, 'wb') as f:
                    # Write XML part
                    f.write(buffxml)
                    # Write Binary arrays
                    f.write(bdata)
                    f.write(boffsets)

    def saveToNumpy(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a numpy (.npz) file. Uses the file name attribute
        of the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        if bundle == 'all': bundle = self._bundles[0].getName()
        if bundle in self._bundles:
            filename = join(self.getDirname(), bundle + self.NPZ)
            self._streamlines.save(filename)

    def saveToTck(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a TCK (.tck) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_tck)

    def saveToTrk(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a TRK (.trk) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_trk)

    def saveToVtk(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a VTK (.vtk) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_vtk)

    def saveToVtp(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a VTP (.vtp) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_vtp)

    def saveToFib(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a FIB (.fib) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_fib)

    def saveToDpy(self, bundle: str = 'all') -> None:
        """
        Save a bundle of the current SisypheStreamlines instance to a dipy (.dpy) file. Uses the file name attribute of
        the current SisypheStreamlines instance.

        Parameters
        ----------
        bundle : str
            bundle name or 'all' for all streamlines (default)
        """
        self._save(bundle, save_dpy)

    # noinspection PyTypeChecker
    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read a bundle of the current SisypheStreamline instance attributes from xml instance. This method is called by
        load() method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'name', str, bundle name
                - 'color', list[float, float, float], red, green, blue color components
                - 'lut', str, lut name
                - 'opacity', float
                - 'width', float, line width in mm
                - 'offsets', tuple[float, float], streamlines data size
                - 'dtypes', streamlines data type
        """
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            r = dict()
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'id':
                    self._ID = node.firstChild.data
                    if self._ID == 'None': self._ID = ''
                # Name
                if node.nodeName == 'name':
                    r['name'] = node.firstChild.data
                # Whole brain
                if node.nodeName == 'whole':
                    self._whole = bool(node.firstChild.data == 'True')
                # Whole brain
                if node.nodeName == 'centroid':
                    self._centroid = bool(node.firstChild.data == 'True')
                # Atlas
                if node.nodeName == 'atlas':
                    self._atlas = bool(node.firstChild.data == 'True')
                # Atlas affine transformation
                if node.nodeName == 'affine':
                    buff = node.firstChild.data
                    affine = [float(v) for v in buff.split(' ')]
                    self._trf = array(affine).reshape(4, 4)
                # Shape
                if node.nodeName == 'shape':
                    buff = node.firstChild.data
                    self._shape = [int(v) for v in buff.split(' ')]
                # Spacing
                if node.nodeName == 'spacing':
                    buff = node.firstChild.data
                    self._spacing = [float(v) for v in buff.split(' ')]
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
                node = node.nextSibling
            return r
        else: raise IOError('Invalid xml file format.')

    def load(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a PySisyphe Streamlines (.xtracts) file.

        Parameters
        ----------
        filename : str
            PySisyphe Streamlines file name
        """
        filename = splitext(filename)[0] + self.getFileExt()
        if exists(filename):
            with open(filename, 'rb') as f:
                # Read XML part
                line = ''
                strdoc = ''
                while line != '</{}>\n'.format(self._FILEEXT[1:]):
                    line = f.readline().decode()  # Convert binary to utf-8
                    strdoc += line
                doc = minidom.parseString(strdoc)
                r = self.parseXML(doc)
                # Read binary part
                bdata = f.read(r['offsets'][0])
                boffsets = f.read(r['offsets'][1])
            data = frombuffer(bdata, dtype=r['dtypes'][0])
            data = data.reshape((len(data) // 3, 3))
            offsets = frombuffer(boffsets, dtype=r['dtypes'][1])
            # noinspection PyTypeChecker
            self._streamlines = Streamlines(relist_streamlines(data, offsets))
            bundle = SisypheBundle((0, len(self._streamlines), 1))
            r['name'] = r['name'].lower()
            if r['name'] in ('all', 'whole', self._DEFAULTNAME): r['name'] = splitext(basename(filename))[0]
            bundle.setName(r['name'])
            self._bundles = SisypheBundleCollection()
            self._bundles.append(bundle)
            self.setFloatColor(r['color'], r['name'])
            self.setLut(r['lut'], r['name'])
            self.setOpacity(r['opacity'], r['name'])
            self.setLineWidth(r['width'], r['name'])
            self._dirname = dirname(filename)
        else: raise IOError('No such file {}'.format(filename))

    def loadAtlasBundle(self, name: str = 'WHOLE'):
        """
        Load an atlas bundle.

        Parameters
        ----------
        name : str
            atlas bundle name or short name
        """
        filename = self.getAtlasBundleFilenameFromShortName(name)
        if filename is None: filename = self.getAtlasBundleFilenameFromName(name)
        if filename is not None and exists(filename): self.load(filename)
        else: raise ValueError('{} is not a valid atlas bundle name or short name.'.format(name))

    def loadFromNumpy(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a numpy (.npz) file.

        Parameters
        ----------
        filename : str
            numpy file name
        """
        filename = splitext(filename)[0] + self.NPZ
        if exists(filename):
            self._streamlines = Streamlines.load(filename)
            bundle = SisypheBundle((0, len(self._streamlines), 1))
            bundle.setName(splitext(basename(filename))[0])
            self._bundles = SisypheBundleCollection()
            self._bundles.append(bundle)
            self._dirname = dirname(filename)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromTck(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a TCK (.tck) file.

        Parameters
        ----------
        filename : str
            TCK file name
        """
        filename = splitext(filename)[0] + self.TCK
        if exists(filename): self._load(filename, load_tck)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromTrk(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a TRK (.trk) file.

        Parameters
        ----------
        filename : str
            TRK file name
        """
        filename = splitext(filename)[0] + self.TRK
        if exists(filename): self._load(filename, load_trk)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromVtk(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a VTK (.vtk) file.

        Parameters
        ----------
        filename : str
            VTK file name
        """
        filename = splitext(filename)[0] + self.VTK
        if exists(filename): self._load(filename, load_vtk)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromVtp(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a VTP (.vtp) file.

        Parameters
        ----------
        filename : str
            VTP file name
        """
        filename = splitext(filename)[0] + self.VTP
        if exists(filename): self._load(filename, load_vtp)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromFib(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a FIB (.fib) file.

        Parameters
        ----------
        filename : str
            FIB file name
        """
        filename = splitext(filename)[0] + self.FIB
        if exists(filename): self._load(filename, load_fib)
        else: raise IOError('No such file {}'.format(filename))

    def loadFromDpy(self, filename: str) -> None:
        """
        Load the current SisypheStreamlines instance from a dipy (.dpy) file.

        Parameters
        ----------
        filename : str
            dipy file name
        """
        filename = splitext(filename)[0] + self.DPY
        if exists(filename): self._load(filename, load_dpy)
        else: raise IOError('No such file {}'.format(filename))


class SisypheDiffusionModel(object):
    """
    Description
    ~~~~~~~~~~~

    Abstract class for diffusion models.

    Scope of methods:

        - gradient values and vectors management
        - diffusion weighted images management
        - IO methods

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel

    Creation: 27/10/2023
    Last revisions: 08/04/2025
    """

    __slots__ = ['_bvals', '_bvecs', '_gtable', '_dwi', '_mask', '_mean', '_b0', '_ID', '_model', '_fmodel', '_spacing']

    # Class constants

    _FILEEXT = '.xdmodel'
    _DTI, _DKI, _SHCSA, _SHCSD, _DSI, _DSID = 'DTI', 'DKI', 'SHCSA', 'SHCSD', 'DSI', 'DSID'
    _MODELS = (_DTI, _DKI, _SHCSA, _SHCSD, _DSI, _DSID)

    # Class methods

    # noinspection PyTypeChecker
    @classmethod
    def _getModelType(cls, filename: str) -> str:
        ext = splitext(filename)[1]
        if ext == cls._FILEEXT:
            if exists(filename):
                with open(filename, 'rb') as f:
                    # Read XML part
                    line = ''
                    strdoc = ''
                    while line != '</{}>\n'.format(cls._FILEEXT[1:]):
                        line = f.readline().decode()  # Convert binary to utf-8
                        strdoc += line
                    doc = minidom.parseString(strdoc)
                    root = doc.documentElement
                    node = root.firstChild
                    # noinspection PyInconsistentReturns
                    while node:
                        # Model type
                        if node.nodeName == 'model':
                            return node.firstChild.data
                        node = node.nextSibling
            else: raise IOError('No such file {}.'.format(basename(filename)))
        else: raise ValueError('Invalid file extension {}, must be {}'.format(ext, cls._FILEEXT))

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheDiffusionModel file extension.

        Returns
        -------
        str
            '.xdmodel'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheDiffusionModel filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Diffusion model (.xdmodel)'
        """
        return 'PySisyphe Diffusion model (*{})'.format(cls._FILEEXT)

    # noinspection PyTypeChecker
    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheDiffusionModel:

        """
        Create a SisypheDiffusionModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheDiffusionModel
            loaded diffusion model
        """
        mt = cls._getModelType(filename)
        if mt in cls._MODELS:
            # noinspection PyInconsistentReturns
            if mt == cls._DTI: return SisypheDTIModel.openModel(filename, fit, binary, wait)
            elif mt == cls._DKI: return SisypheDKIModel.openModel(filename, fit, binary, wait)
            elif mt == cls._SHCSA: return SisypheSHCSAModel.openModel(filename, fit, binary, wait)
            elif mt == cls._SHCSD: return SisypheSHCSDModel.openModel(filename, fit, binary, wait)
            elif mt == cls._DSI: return SisypheDSIModel.openModel(filename, fit, binary, wait)
            elif mt == cls._DSID: return SisypheDSIDModel.openModel(filename, fit, binary, wait)
        else: raise ValueError('Unknown model type {}'.format(mt))

    # Special method

    """
    Private attributes

    _bvals      ndarray, gradient B values
    _bvecs      ndarray, gradient vectors
    _gtable     GradientTable
    _dwi        ndarray, n dwi images [x, y, z, n]
    _mask       ndarray, same shape as dwi images [x, y, z]
    _b0         ndarray, mean B0 image, same shape as dwi images [x, y, z]
    _mean       ndarray, mean dwi image, same shape as dwi images [x, y, z]
    _ID         str, reference ID
    _spacing    tuple[float, float, float], dwi image spacing
    _model      None, initialized by child classes
    _fmodel     None, initialized by child classes
    """

    def __init__(self) -> None:
        """
        SisypheDiffusionModel instance constructor.
        """
        self._bvals: ndarray | None = None
        self._bvecs: ndarray | None = None
        self._gtable: GradientTable | None = None
        self._dwi: ndarray | None = None
        self._mask: ndarray | None = None
        self._b0: ndarray | None = None
        self._mean: ndarray | None = None
        self._model = None
        self._fmodel = None
        self._ID = ''
        self._spacing = [1.0] * 3

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDiffusionModel instance to str
         """
        buff = 'Reference ID: {}\n'.format(self._ID)
        buff += 'DWI spacing: {}\n'.format(self._spacing)
        if self._dwi is None: buff += 'DWI shape: None\n'
        else:  buff += 'DWI shape: {}\n'.format(self._dwi.shape)
        if self._mean is None: buff += 'Mean image shape: None\n'
        else: buff += 'Mean image shape: {}\n'.format(self._mean.shape)
        if self._mask is None: buff += 'Mask image shape: None\n'
        else: buff += 'Mask image shape: {}\n'.format(self._mask.shape)
        if self.hasGradients():
            buff += '{:10}{:30}\n'.format('B values', 'Gradient vectors')
            for i in range(self._bvals.shape[0]):
                buff += '{:10}{:30}\n'.format(str(self._bvals[i]), str(self._bvecs[i]))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDiffusionModel instance representation
        """
        return 'SisypheDiffusionModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Private method

    def _calcID(self):
        # < Revision 08/04/2025
        # replace _mean by _b0
        if self._b0 is not None:
            m = md5()
            # < Revision 10/04/2025
            # bug fix, ndarray is not C-contiguous
            # m.update(self._b0)
            m.update(self._b0.tostring())
            # < Revision 10/04/2025
            self._ID = m.hexdigest()
        # Revision 08/04/2025

    # Public methods

    def getReferenceID(self):
        """
        Get reference ID attribute of the current SisypheDiffusionModel instance. By default, this ID is the array ID
        of the mean B0, which is calculated when diffusion-weighted images are added to the model using the loadDWI()
        or setDWI() method.

        Returns
        -------
        str
            reference ID
        """
        return self._ID

    def hasReferenceID(self):
        """
        Check whether reference ID attribute of the current SisypheDiffusionModel instance is defined (not '').

        Returns
        -------
        bool
            True if reference ID is defined
        """
        return self._ID != ''

    def clear(self) -> None:
        """
        Clear attributes of the current SisypheDiffusionModel instance.
        """
        del self._bvals, self._bvecs, self._gtable
        del self._dwi, self._mask, self._model
        self._bvals = None
        self._bvecs = None
        self._gtable = None
        self._dwi = None
        self._b0 = None
        self._mean = None
        self._mask = None
        self._model = None

    def count(self) -> int:
        """
        Number of diffusion weighted images (diffusion values/vectors) in the current SisypheDiffusionModel instance.

        Returns
        -------
        int
        """
        if self._bvals is not None: return self._bvals.shape[0]
        elif self._dwi is not None: return self._dwi.shape[3]
        else: return 0

    def reorientGradients(self, trf: SisypheTransform) -> None:
        """
        Apply a geometric transformation to gradient attributes of the current SisypheDiffusionModel instance.

        Parameters
        ----------
        trf : Sisyphe.core.sisypheTransform.SisypheTransform
            geometric transformation
        """
        if self._gtable is not None:
            affine = trf.getNumpyArray(homogeneous=True)
            self._gtable = reorient_bvecs(self._gtable, affine)
        else: raise AttributeError('Gradient table is empty.')

    def loadGradients(self,
                      bvalsfile: str,
                      bvecsfile: str,
                      lpstoras: bool = False) -> None:
        """
        Load gradient values/vectors attributes of the current SisypheDiffusionModel instance
        from text or xml files.

        Parameters
        ----------
        bvalsfile : str
            gradients b values file name
        bvecsfile : str
            gradient direction vectors file name
        lpstoras : bool
            gradient reorientation if True, LPS+ (DICOM) to RAS+ conversion (flip x and y)
        """
        if exists(bvalsfile):
            _, ext = splitext(bvalsfile)
            if ext == '.txt': bvals = loadBVal(bvalsfile, format='txt', numpy=True)
            elif ext == '.xbval': bvals = loadBVal(bvalsfile, format='xml', numpy=True)
            else: raise IOError('invalid format {}.'.format(ext))
        else: raise IOError('no such file {}.'.format(basename(bvalsfile)))
        if exists(bvecsfile):
            _, ext = splitext(bvecsfile)
            if ext == '.txt':
                try:
                    # noinspection PyUnusedLocal
                    bvecs = loadBVec(bvecsfile, format='txtbydim', numpy=True)
                except: bvecs = loadBVec(bvecsfile, format='txtbyvec', numpy=True)
            elif ext == '.xbvec':
                bvecs = loadBVec(bvecsfile, format='xml', numpy=False)
                filenames = list(bvecs.keys())
                self.loadDWI(filenames)
                bvecs = array(list(bvecs.values()))
            else: raise IOError('invalid format {}.'.format(ext))
        else: raise IOError('no such file {}.'.format(basename(bvecsfile)))
        # < Revision 08/04/2025
        # LPS+ to RAS+ orientation conversion
        if lpstoras:
            t = diag([-1.0, -1.0, 1.0])
            for i in range(bvecs.shape[0]):
                v = bvecs[i]
                v = t @ v
                bvecs[i] = v
        # Revision 08/04/2025 >
        self.setGradients(bvals, bvecs)

    def setGradients(self,
                     bvals: ndarray,
                     bvecs: ndarray,
                     lpstoras: bool = False) -> None:
        """
        Set gradient values/vectors attributes of the current SisypheDiffusionModel instance
        from numpy.ndarray.

        Parameters
        ----------
        bvals : numpy.ndarray
            gradients b values numpy.ndarray, shape(n, 1)
        bvecs : numpy.ndarray
            gradient direction vectors numpy.ndarray, shape(n, 3)
        lpstoras : bool
            gradient reorientation if True, LPS+ (DICOM) to RAS+ orientation convention (flip x and y)
        """
        if bvecs.ndim != 2 or bvecs.shape[1] != 3:
            raise ValueError('invalid bvecs ndarray parameter shape.')
        if bvals.ndim != 1:
            raise ValueError('invalid bvals ndarray parameter shape.')
        if bvecs.shape[0] != bvals.shape[0]:
            raise ValueError('item count in bvals and bvecs is different.')
        if self._dwi is not None and self._dwi.shape[3] != bvals.shape[0]:
            raise ValueError('item count in bvals/bvecs and DWI image count is different.')
        # < Revision 08/04/2025
        # LPS+ to RAS+ orientation conversion
        if lpstoras:
            t = diag([-1.0, -1.0, 1.0])
            for i in range(bvecs.shape[0]):
                v = bvecs[i]
                v = t @ v
                bvecs[i] = v
        # Revision 08/04/2025 >
        self._bvecs = bvecs
        self._bvals = bvals
        self._gtable = gradient_table(bvals=self._bvals, bvecs=self._bvecs)

    def getGradients(self) -> tuple[ndarray, ndarray]:
        """
        Get gradient values/vectors attributes of the current SisypheDiffusionModel instance.

        Returns
        -------
        tuple[ndarray, ndarray]
            - gradients b values numpy.ndarray, shape(n, 1)
            - gradient direction vectors numpy.ndarray, shape(n, 3)
        """
        return self._bvals, self._bvecs

    def hasGradients(self) -> bool:
        """
        Check whether gradient attributes of the current SisypheDiffusionModel instance are defined (not None).

        Returns
        -------
        bool
            True if gradients are defined
        """
        return self._bvals is not None and self._bvecs is not None

    def loadDWI(self, filenames: list[str]) -> None:
        """
        Load diffusion weighted images (Sisyphe.core.sisypheVolume.SisypheVolume)
        to the current SisypheDiffusionModel instance.

        Parameters
        ----------
        filenames : list[str]
            list of PySisyphe Volumes (.xvol) file names
        """
        vols = SisypheVolumeCollection()
        vols.load(filenames)
        self.setDWI(vols)

    def setDWI(self,
               vols: SisypheVolumeCollection) -> None:
        """
        Set diffusion-weighted images to the current SisypheDiffusionModel instance.

        Parameters
        ----------
        vols : SisypheVolumeCollection
            diffusion weighted images container
        """
        if self._bvals is not None:
            if vols.count() == self._bvals.shape[0]:
                self._dwi = vols.copyToNumpyArray(defaultshape=False)
                # B0 mean
                v = SisypheVolumeCollection()
                for i in range(len(self._bvals)):
                    if self._bvals[i] == 0: v.append(vols[i])
                if v.count() == 1: self._b0 = v[0]
                elif v.count() > 1: self._b0 = v.getMeanVolume().copyToNumpyArray(defaultshape=False)
                # DWI mean
                v = SisypheVolumeCollection()
                for i in range(len(self._bvals)):
                    if self._bvals[i] > 0: v.append(vols[i])
                if v.count() == 1: self._mean = v[0]
                elif v.count() > 1: self._mean = v.getMeanVolume().copyToNumpyArray(defaultshape=False)
                self._calcID()
                self._spacing = vols[0].getSpacing()
            else: raise ValueError('Mismatch between bvals/bvecs element count and DWI image count.')
        else: raise ValueError('Set bvals and bvecs before DWI images.')

    def setDWIFromNumpy(self,
                        dwi: ndarray,
                        spacing: vector3float | None = None) -> None:
        """
        Set diffusion weighted images to the current SisypheDiffusionModel instance.

        Parameters
        ----------
        dwi : numpy.ndarray
            diffusion weighted images container
        spacing : list[float, float, float] | tuple[float, float, float]
            voxel size (mm) in each dimension
        """
        if self._bvals is not None:
            if dwi.shape[-1] != self._bvals.shape[0]:
                self._dwi = dwi
                # B0 mean
                v = list()
                for i in range(len(self._bvals)):
                    if self._bvals[i] == 0: v.append(self._dwi[:,:,:,i])
                if len(v) == 1: self._b0 = v[0]
                elif len(v) > 1:
                    buff = stack(v, axis=3)
                    self._b0 = asarray(buff.mean(axis=3), order='C')
                self._calcID()
                # DWI mean
                v = list()
                for i in range(len(self._bvals)):
                    if self._bvals[i] > 0: v.append(self._dwi[:, :, :, i])
                if len(v) == 1: self._mean = v[0]
                elif len(v) > 1:
                    buff = stack(v, axis=3)
                    self._mean = asarray(buff.mean(axis=3), order='C')
                if spacing is not None: self._spacing = spacing
                else: self._spacing = (1.0, 1.0, 1.0)
            else: raise ValueError('Mismatch between bvals/bvecs element count and DWI image count.')
        else: raise ValueError('Set bvals and bvecs before DWI images.')

    def getDWI(self) -> ndarray:
        """
        Get diffusion weighted images from the current SisypheDiffusionModel instance.

        Returns
        -------
        numpy.ndarray
            diffusion weighted images
        """
        return self._dwi

    def hasDWI(self) -> bool:
        """
        Check whether diffusion-weighted images are defined in the current SisypheDiffusionModel instance.

        Returns
        -------
        bool
            True if diffusion-weighted images are defined
        """
        return self._dwi is not None

    def getShape(self) -> tuple[int, int, int]:
        """
        Get the diffusion weighted image shape of the current SisypheDiffusionModel instance.

        Returns
        -------
        tuple[int, int, int]
            diffusion weighted image shape
        """
        if self._dwi is not None:
            # noinspection PyTypeChecker
            return tuple(self._dwi.shape[:3])
        else: return 0, 0, 0

    def getSpacing(self) -> vector3float:
        """
        Get the diffusion weighted images spacing of the current SisypheDiffusionModel instance.

        Returns
        -------
        tuple[float, float, float]
            diffusion weighted images spacing i.e. voxel size (mm) in each dimension
        """
        return self._spacing

    def getFOV(self, decimals: int | None = None) -> tuple[float, float, float]:
        """
        Get the field of view (FOV) of the current SisypheDiffusionModel instance.

        Parameters
        ----------
        decimals : int | None
            number of decimals used to round values, if None no round

        Returns
        -------
        tuple[float, float, float]
            field of view of diffusion-weighted images (mm)
        """
        shape = self.getShape()
        if decimals is not None:
            # noinspection PyTypeChecker
            return tuple([round(shape[i] * self._spacing[i], decimals) for i in range(3)])
        else:
            # noinspection PyTypeChecker
            return tuple([shape[i] * self._spacing[i] for i in range(3)])

    def getMask(self) -> ndarray:
        """
        Get the brain mask attribute of the current SisypheDiffusionModel instance.

        Returns
        -------
        numpy.ndarray
            brain mask
        """
        return self._mask

    def loadMask(self, filename: str) -> None:
        """
        Load brain mask to the current SisypheDiffusionModel instance.

        Parameters
        ----------
        filename : str
            brain mask file name
        """
        if self.hasDWI():
            if exists(filename):
                ext = splitext(filename)
                if ext == SisypheROI.getFileExt():
                    v = SisypheROI()
                    v.load(filename)
                elif ext == SisypheVolume.getFileExt():
                    v = SisypheVolume()
                    v.load(filename)
                else: raise ValueError('{} format is not supported (must be {} or {}.'.format(ext, SisypheROI.getFileExt(), SisypheVolume.getFileExt()))
                self.setMask(v)
            else: raise FileNotFoundError('no such file {}.'.format(filename))
        else: raise ValueError('No dwi image in the current {} instance.'.format(type(self)))

    def setMask(self, mask: ndarray | SisypheROI | SisypheVolume) -> None:
        """
        Set the brain mask attribute of the current SisypheDiffusionModel instance.

        Parameters
        ----------
        numpy.ndarray | Sisyphe.core.SisypheROI | Sisyphe.core.SisypheVolume
            brain mask
        """
        if self.hasDWI():
            if isinstance(mask, (SisypheROI, SisypheVolume)):
                mask = mask.copyToNumpyArray(defaultshape=False)
            if isinstance(mask, ndarray):
                if mask.shape == self._dwi.shape[:3]:
                    self._mask = (mask > 0).astype('uint8')
                else: raise ValueError('parameter shape {} is not compatible with dwi shape {}'.format(mask.shape, self._dwi.shape[:3]))
            else: raise TypeError('parameter type {} is invalid (must be ndarray or SisypheROI or SisypheVolume.'.format(type(mask)))
        else: raise ValueError('No dwi image in the current {} instance.'.format(type(self)))

    def getDWIMean(self):
        """
        Get diffusion-weighted mean image from the current SisypheDiffusionModel instance.

        Returns
        -------
        numpy.ndarray
            diffusion weighted mean image
        """
        return self._mean

    def calcMask(self,
                 algo: str = 'huang',
                 niter: int = 2,
                 kernel: int = 1):
        """
        Calculate brain mask of the current SisypheDiffusionModel instance.

        Parameters
        ----------
        algo : str
            brain mask parameter, algorithm used to estimate background threshold (default huang): 'mean', 'otsu',
            'huang', 'renyi', 'yen', 'li', 'shanbhag', 'triangle', 'intermodes', 'maximumentropy', 'kittler', 'isodata', 'moments'
        niter : int
            brain mask parameter, number of binary morphology iterations (default 2). No brain mask if 0.
        kernel : int
            brain mask parameter, kernel size of binary morphology operator (default 1). No brain mask if 0.
        """
        if self.hasDWI():
            v = SisypheVolume()
            v.copyFromNumpyArray(self._mean, spacing=self._spacing, defaultshape=False)
            mask = v.getMask2(algo, niter, kernel)
            self._mask = mask.copyToNumpyArray(defaultshape=False)
        else: raise ValueError('No dwi image in the current {} instance.'.format(type(self)))

    def isFitted(self) -> bool:
        """
        Check whether the diffusion of the current SisypheDiffusionModel instance is estimated (fitted)

        Returns
        -------
        bool
            True if diffusion model is estimated
        """
        return self._fmodel is not None

    def computeFitting(self, wait: DialogWait | None = None) -> None:
        """
        Abstract method, must be implemented in the derived classes. Estimating the diffusion model.
        """
        raise NotImplementedError

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dti.TensorModel | dipy.reconst.dki.DiffusionKurtosisModel
        | dipy.reconst.shm.CsaOdfModel | dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel
        | dipy.reconst.dsi.DiffusionSpectrumModel | dipy.reconst.dsi.DiffusionSpectrumDeconvModel
            dipy diffusion model
        """
        return self._model

    def getFittedModel(self):
        """
        Get the estimated model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dti.TensorFit | dipy.reconst.dki.DiffusionKurtosisFit
        | dipy.reconst.shm.SphHarmFit | dipy.reconst.dsiDiffusionSpectrumFit
        | dipy.reconst.dsiDiffusionSpectrumDeconvFit
            dipy estimated diffusion model
        """
        return self._fmodel

    def getGradientTable(self) -> GradientTable:
        """
        Get the gradient table attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.core.gradients.GradientTable
            gradient table
        """
        return self._gtable

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDiffusionModel instance attributes to xml instance. This method is called by save()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # ID
            node = doc.createElement('ID')
            root.appendChild(node)
            txt = doc.createTextNode(self.getReferenceID())
            node.appendChild(txt)
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
        """
        Save the current SisypheDiffusionModel instance to a PySisyphe diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            PySisyphe diffusion model file name
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
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
                    wait.setInformationText('Save {}'.format(basename(filename)))
                    wait.setProgressRange(0, n)
                    wait.progressVisibilityOn()
                    for i in range(n):
                        start = i * block
                        end = start + block
                        f.write(buffdwi[start:end])
                        wait.setCurrentProgressValue(i + 1)
                    if end < total:
                        f.write(buffdwi[end:])
                    wait.progressVisibilityOff()
            filename = splitext(filename)[0] + SisypheVolume.getFileExt()
            # Save DWI mean
            if self._mean is not None:
                v = SisypheVolume(self._mean.T, spacing=self._spacing)
                v.setFilename(filename)
                v.setFilenameSuffix('mean')
                v.acquisition.setSequenceToMeanMap()
                v.setID(self._ID)
                wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()
            # Save B0 mean
            if self._b0 is not None:
                v = SisypheVolume(self._b0.T, spacing=self._spacing)
                v.setFilename(filename)
                v.setFilenameSuffix('B0')
                v.acquisition.setSequenceToB0()
                v.setID(self._ID)
                wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()
            # Save mask
            if self._mask is not None:
                v = SisypheVolume(self._mask.T, spacing=self._spacing)
                v.setFilename(filename)
                v.setFilenameSuffix('mask')
                v.acquisition.setSequenceToMask()
                v.setID(self._ID)
                wait.setInformationText('Save {}'.format(v.getBasename()))
                v.save()

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheDiffusionModel instance attributes from xml instance. This method is called by load()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
        root = doc.documentElement
        if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') <= '1.0':
            bvals = None
            bvecs = None
            attr = dict()
            node = root.firstChild
            while node:
                # ID
                if node.nodeName == 'ID':
                    self._ID = node.firstChild.data
                # bvals
                if node.nodeName == 'bvals':
                    buff = node.firstChild.data
                    bvals = array([float(v) for v in buff.split(' ')])
                # bvecs
                if node.nodeName == 'bvecs':
                    buff = list()
                    vecs = node.firstChild.data.split('|')
                    for vec in vecs:
                        buff.append([float(v) for v in vec.split(' ')])
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
            # noinspection PyTypeChecker
            return attr
        else: raise IOError('XML file format is not supported.')

    def loadModel(self,
                  filename: str,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> None:
        """
        Load the current SisypheDiffusionModel instance from a PySisyphe diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            PySisyphe diffusion model file name
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
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
                if binary:
                    block = 10485760  # 10 MBytes
                    start = f.tell()
                    end = f.seek(0, os.SEEK_END)
                    total = end - start + 1  # Binary part size
                    n = total // block
                    f.seek(start, os.SEEK_SET)
                    if wait is None or n < 2: buffarray = f.read()
                    else:
                        wait.setInformationText('Load {}'.format(basename(filename)))
                        wait.setProgressRange(0, n)
                        wait.progressVisibilityOn()
                        buffarray = bytearray()
                        while f.tell() < end:
                            r = f.read(block)
                            buffarray += r
                            wait.incCurrentProgressValue()
                        wait.progressVisibilityOff()
            doc = minidom.parseString(strdoc)
            attr = self.parseXML(doc)
            if binary:
                dwi = frombuffer(buffarray, dtype=attr['dtype'])
                dwi = dwi.reshape(attr['shape'])
                self._dwi = dwi
                filename = splitext(filename)[0] + SisypheVolume.getFileExt()
                # Open DWI mean
                v = SisypheVolume()
                v.setFilename(filename)
                v.setFilenameSuffix('mean')
                if exists(v.getFilename()):
                    v.load()
                    self._mean = v.copyToNumpyArray(defaultshape=False)
                else:
                    v = list()
                    for i in range(len(self._bvals)):
                        if self._bvals[i] > 0: v.append(self._dwi[:, :, :, i])
                    if len(v) == 1: self._mean = v[0]
                    elif len(v) > 1:
                        buff = stack(v, axis=3)
                        self._mean = asarray(buff.mean(axis=3), order='C')
                # Open mask
                v = SisypheVolume()
                v.setFilename(filename)
                v.setFilenamePrefix('mask')
                if exists(v.getFilename()):
                    v.load()
                    self._mask = v.copyToNumpyArray(defaultshape=False)
                else: self.calcMask()
            else:
                self._dwi = None
                self._mask = None
                self._mean = None
        else: raise IOError('No such file {}.'.format(basename(filename)))


class SisypheDTIModel(SisypheDiffusionModel):
    """
    Description
    ~~~~~~~~~~~

    Class to manage diffusion tensor imaging model.

    Methods to calculate diffusion derived maps (mean diffusivity, fractional anisotropy...).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheDTIModel

    Creation: 27/10/2023
    Last revision: 21/03/2024
    """

    __slots__ = ['_algfit']

    # Class constants

    _WLS, _OLS, _NLLS, _RT = 'WLS', 'OLS', 'NLLS', 'RT'
    _ALG = (_WLS, _OLS, _NLLS, _RT)

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheDTIModel:
        """
        Create a SisypheDTIModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheDiffusionModel
            loaded diffusion model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheDTIModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('DTI model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    """
    Private attribute

    _algfit         str 
    _model          dipy.reconst.dti.TensorModel
    _fmodel         dipy.reconst.dti.TensorFit
    """

    def __init__(self, algfit: str = 'WLS') -> None:
        """
        SisypheDTIModel instance constructor.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'NLLS' non-linear least squares
                - 'RT' restore robust tensor
        """
        super().__init__()

        if algfit in self._ALG: self._algfit = algfit
        else: self._algfit = 'WLS'

        self._model: TensorModel | None = None
        self._fmodel: TensorFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDTIModel instance to str
         """
        buff = 'Diffusion Tensor Imaging (DTI) model\n'
        buff += 'Fitting algorithm: {}\n'.format(self._algfit)
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDTIModel instance representation
        """
        return 'SisypheDTIModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setFitAlgorithm(self, algfit: str = 'WLS') -> None:
        """
        Set the fitting algorithm attribute of the current SisypheDTIModel instance.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'NLLS' non-linear least squares
                - 'RT' restore robust tensor
        """
        if algfit in self._ALG: self._algfit = algfit
        else: ValueError('invalid parameter value {}.'.format(algfit))

    def getFitAlgorithm(self) -> str:
        """
        Get the fitting algorithm attribute of the current SisypheDTIModel instance.

        Returns
        -------
        str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'NLLS' non-linear least squares
                - 'RT' restore robust tensor
        """
        return self._algfit

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dti.TensorModel
            dipy DTI model
        """
        if self.hasGradients():
            if self._model is None:
                self._model = TensorModel(self._gtable, self._algfit)
        return super().getModel()

    def computeFitting(self, algfit: str = '', wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheDTIModel instance.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'NLLS' non-linear least squares
                - 'RT' restore robust tensor
                - if is empty, uses fitting algorithm attribute
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if wait is not None:
                    wait.setInformationText('DTI model fitting...')
                if algfit == '' or algfit not in self._ALG: algfit = self._algfit
                else: self._algfit = algfit
                self._model = TensorModel(gtab=self._gtable, fit_method=algfit)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getFA(self) -> SisypheVolume:
        """
        Calculate Fractional Anisotropy (FA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            FA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getGA(self) -> SisypheVolume:
        """
        Calculate Geodesic Anisotropy (GA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.ga,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('GA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getMD(self) -> SisypheVolume:
        """
        Calculate Mean Diffusivity (MD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            MD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.md,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('MD')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getTrace(self) -> SisypheVolume:
        """
        Calculate Tensor Trace map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            Trace map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.trace,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('TRACE')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getAxialDiffusivity(self) -> SisypheVolume:
        """
        Calculate Axial Diffusivity (AD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            AD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.ad,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('AXIAL DIFFUSIVITY')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getRadialDiffusivity(self) -> SisypheVolume:
        """
        Calculate Radial Diffusivity (RD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            RD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.rd,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('RADIAL DIFFUSIVITY')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getIsotropic(self) -> ndarray:
        """
        Calculate Isotropic Diffusivity.

        Returns
        -------
        numpy.ndarray
            isotropic Diffusivity
        """
        if self._fmodel is not None:
            return isotropic(self._fmodel.quadratic_form)
        else: raise AttributeError('Model attribute is None.')

    def getDeviatropic(self) -> ndarray:
        """
        Calculate Deviatropic Diffusivity.

        Returns
        -------
        numpy.ndarray
            deviatropic Diffusivity
        """
        if self._fmodel is not None:
            return deviatoric(self._fmodel.quadratic_form)
        else: raise AttributeError('Model attribute is None.')

    def getTensor(self) -> ndarray:
        """
        Get tensors.

        Returns
        -------
        numpy.ndarray
            tensors
        """
        if self._fmodel is not None:
            return self._fmodel.quadratic_form
        else: raise AttributeError('Model attribute is None.')

    def getEigenValues(self) -> ndarray:
        """
        Get tensor eigen values.

        Returns
        -------
        numpy.ndarray
            eigen values
        """
        if self._fmodel is not None:
            return self._fmodel.evals
        else: raise AttributeError('Model attribute is None.')

    def getEigenVectors(self) -> ndarray:
        """
        Get tensor eigen vectors.

        Returns
        -------
        numpy.ndarray
            eigen vectors
        """
        if self._fmodel is not None:
            return self._fmodel.evecs
        else: raise AttributeError('Model attribute is None.')

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDTIModel instance attributes to xml instance. This method is called by save() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._DTI)
            node.appendChild(txt)
            # Fitting algorithm
            node = doc.createElement('fitalgo')
            root.appendChild(node)
            txt = doc.createTextNode(self._algfit)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheDTIModel instance attributes from xml instance. This method is called by load() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'DTI'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to manage diffusion kurtosis model.

    Methods to calculate diffusion derived maps (mean diffusivity, fractional anisotropy...).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheDkIDModel

    Creation: 29/10/2023
    Last revision: 21/03/2024
    """

    __slots__ = ['_algfit']

    # Class constants

    _WLS, _OLS, _CLS, _CWLS = 'WLS', 'OLS', 'CLS', 'CWLS'
    _ALG = (_WLS, _OLS, _CLS, _CWLS)

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheDKIModel:
        """
        Create a SisypheDKIModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheDKIModel
            loaded DKI model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheDKIModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('DKI model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    """
    Private attribute

    _algfit     str
    _model     dipy.reconst.dki.DiffusionKurtosisModel
    _fmodel    dipy.reconst.dki.DiffusionKurtosisFit
    """

    def __init__(self, algfit: str = 'WLS') -> None:
        """
        SisypheDKIModel instance constructor.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'CLS' constrained ordinary least squares
                - 'CWLS' constrained weighted least squares
        """
        super().__init__()

        if algfit in self._ALG: self._algfit = algfit
        else: self._algfit = 'WLS'

        self._model: DiffusionKurtosisModel | None = None
        self._fmodel: DiffusionKurtosisFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDKIModel instance to str
         """
        buff = 'Diffusion Kurtosis Imaging (DKI) model\n'
        buff += 'Fitting algorithm: {}\n'.format(self._algfit)
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDKIModel instance representation
        """
        return 'SisypheDKIModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setFitAlgorithm(self, algfit: str = 'WLS') -> None:
        """
        Set the fitting algorithm attribute of the current SisypheDKIModel instance.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'CLS' constrained ordinary least squares
                - 'CWLS' constrained weighted least squares
        """
        if algfit in self._ALG: self._algfit = algfit
        else: ValueError('invalid parameter value {}.'.format(algfit))

    def getFitAlgorithm(self) -> str:
        """
        Get the fitting algorithm attribute of the current SisypheDKIModel instance.

        Returns
        -------
        str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'CLS' constrained ordinary least squares
                - 'CWLS' constrained weighted least squares
        """
        return self._algfit

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dki.DiffusionKurtosisModel
            dipy DKI model
        """
        if self.hasGradients():
            if self._model is None:
                self._model = DiffusionKurtosisModel(self._gtable, fit_method=self._algfit)
        return super().getModel()

    def computeFitting(self, algfit: str = '', wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheDKIModel instance.

        Parameters
        ----------
        algfit : str
            fitting algorithm:
                - 'WLS' weighted least squares
                - 'OLS' ordinary least squares
                - 'CLS' constrained ordinary least squares
                - 'CWLS' constrained weighted least squares
                - if is empty, uses fitting algorithm attribute
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if wait is not None:
                    wait.setInformationText('DKI model fitting...')
                if algfit == '' or algfit not in self._ALG: algfit = self._algfit
                else: self._algfit = algfit
                self._model = DiffusionKurtosisModel(gtab=self._gtable, fit_method=algfit)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getFA(self) -> SisypheVolume:
        """
        Calculate Fractional Anisotropy (FA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            FA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.fa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getGA(self) -> SisypheVolume:
        """
        Calculate Geodesic Anisotropy (GA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.ga,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('GA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getMD(self) -> SisypheVolume:
        """
        Calculate Mean Diffusivity (MD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            MD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.md,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('MD')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getTrace(self) -> SisypheVolume:
        """
        Calculate Tensor Trace map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            trace map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.trace,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('TRACE')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getAxialDiffusivity(self) -> SisypheVolume:
        """
        Calculate Axial Diffusivity (AD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            AD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.ad,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('AXIAL DIFFUSIVITY')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    def getRadialDiffusivity(self) -> SisypheVolume:
        """
        Calculate Radial Diffusivity (RD) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            RD map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.rd,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('RADIAL DIFFUSIVITY')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDKIModel instance attributes to xml instance. This method is called by save() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._DKI)
            node.appendChild(txt)
            # Fitting algorithm
            node = doc.createElement('fitalgo')
            root.appendChild(node)
            txt = doc.createTextNode(self._algfit)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheDKIModel instance attributes from xml instance. This method is called by load() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'DKI'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to manage spherical harmonic model with constant solid angle reconstruction

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheSHCSAModel

    Creation: 29/10/2023
    Last revision: 21/03/2024
    """

    __slots__ = ['_order']

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheSHCSAModel:
        """
        Create a SisypheSHCSAModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheSHCSAModel
            loaded SHCSA model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheSHCSAModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('SHCSA model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    """
    Private attribute

    _order      int
    _model      dipy.reconst.shm.CsaOdfModel
    _fmodel     dipy.reconst.shm.SphHarmFit
    """

    def __init__(self, order: int = 6) -> None:
        """
        SisypheSHCSAModel instance constructor.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        """
        super().__init__()
        self._order: int = order
        self._model: CsaOdfModel | None = None
        self._fmodel: SphHarmFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheSHCSAModel instance to str
         """
        buff = 'Spherical Harmonic with Constant Solid Angle reconstruction (SHCSA) model\n'
        buff += 'Spherical harmonic order: {}\n'.format(self._order)
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheSHCSAModel instance representation
        """
        return 'SisypheSHCSAModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setOrder(self, order: int = 6) -> None:
        """
        Set the spherical harmonic order attribute of the current SisypheSHCSAModel instance.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        """
        self._order = order

    def getOrder(self) -> int:
        """
        Set the spherical harmonic order attribute of the current SisypheSHCSAModel instance.

        Returns
        -------
        int
            spherical harmonic order of the model (default 6)
        """
        return self._order

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.shm.CsaOdfModel
            dipy SHCSA model
        """
        if self.hasGradients():
            if self._model is None:
                self._model = CsaOdfModel(self._gtable, sh_order=self._order)
        return super().getModel()

    def computeFitting(self, order: int = 6, wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheSHCSAModel instance.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasGradients() and self.hasDWI():
            if self._model is None:
                if wait is not None:
                    wait.setInformationText('SHCSA model fitting...')
                if order == 0: order = self._order
                else: self._order = order
                self._model = CsaOdfModel(gtab=self._gtable, sh_order=order)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getGFA(self) -> SisypheVolume:
        """
        Calculate Generalized Fractional Anisotropy (GFA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GFA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.gfa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('GFA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheSHCSAModel instance attributes to xml instance. This method is called by save()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._SHCSA)
            node.appendChild(txt)
            # Spherical harmonic order
            node = doc.createElement('order')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._order))
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheSHCSAModel instance attributes from xml instance. This method is called by load()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'SHCSA'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to manage constrained spherical harmonic deconvolution model

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheSHCSDModel

    Creation: 29/10/2023
    Last revision: 21/03/2024
    """

    __slots__ = ['_order']

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheSHCSDModel:
        """
        Create a SisypheSHCSDModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheSHCSDModel
            loaded SHCSD model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheSHCSDModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('SHCSD model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    """
    Private attribute

    _order      int
    _model      dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel
    _fmodel     dipy.reconst.shm.SphHarmFit
    """

    def __init__(self, order: int = 6) -> None:
        """
        SisypheSHCSDModel instance constructor.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        """
        super().__init__()
        self._order: int = order
        self._model: ConstrainedSphericalDeconvModel | None = None
        self._fmodel: SphHarmFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheSHCSDModel instance to str
         """
        buff = 'Spherical Harmonic Constrained Deconvolution (SHCSD) model\n'
        buff += 'Spherical harmonic order: {}\n'.format(self._order)
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheSHCSDModel instance representation
        """
        return 'SisypheSHCSDModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setOrder(self, order: int = 6) -> None:
        """
        Set the spherical harmonic order attribute of the current SisypheSHCSDModel instance.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        """
        self._order = order

    def getOrder(self) -> int:
        """
        Set the spherical harmonic order attribute of the current SisypheSHCSDModel instance.

        Returns
        -------
        int
            spherical harmonic order of the model (default 6)
        """
        return self._order

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.csdeconv.ConstrainedSphericalDeconvModel
            dipy SHCSD model
        """
        if self.hasGradients():
            if self._model is None:
                response, ratio = auto_response_ssst(self._gtable, self._dwi, roi_radii=10, fa_thr=0.7)
                self._model = ConstrainedSphericalDeconvModel(self._gtable, response, sh_order=self._order)
        return super().getModel()

    def computeFitting(self, order: int = 0, wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheSHCSDModel instance.

        Parameters
        ----------
        order : int
            spherical harmonic order of the model (default 6)
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (default None)
        """
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if wait is not None:
                    wait.setInformationText('SHCSD model fitting...')
                if order == 0: order = self._order
                else: self._order = order
                response, ratio = auto_response_ssst(gtab=self._gtable, data=self._dwi, roi_radii=10, fa_thr=0.7)
                # self._model = ConstrainedSphericalDeconvModel(gtab=self._gtable, response=response, sh_order=order)
                # new parameter name since dipy v1.9 sh_order -> sh_order_max
                self._model = ConstrainedSphericalDeconvModel(gtab=self._gtable, response=response, sh_order_max=order)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getGFA(self) -> SisypheVolume:
        """
        Calculate Generalized Fractional Anisotropy (GFA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GFA map
        """
        if self._fmodel is not None:
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(self._fmodel.gfa,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    getFA = getGFA

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheSHCSDModel instance attributes to xml instance. This method is called by save()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._SHCSD)
            node.appendChild(txt)
            # Spherical harmonic order
            node = doc.createElement('order')
            root.appendChild(node)
            txt = doc.createTextNode(str(self._order))
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheSHCSDModel instance attributes from xml instance. This method is called by load()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'SHCSD'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to manage diffusion spectrum imaging model

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheDSIModel

    Creation: 29/10/2023
    Last revision: 21/03/2024
    """

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheDSIModel:
        """
        Create a SisypheDSIModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheDSIModel
            loaded DSI model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheDSIModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('DSI model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    """
    Private attribute

    _model      dipy.reconst.dsi.DiffusionSpectrumModel
    _fmodel     dipy.reconst.dsi.DiffusionSpectrumFit
    """

    def __init__(self) -> None:
        """
        SisypheDSIModel instance constructor.
        """
        super().__init__()
        self._model: DiffusionSpectrumModel | None = None
        self._fmodel: DiffusionSpectrumFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDSIModel instance to str
         """
        buff = 'Diffusion Spectrum Imaging (DSI) model\n'
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDSIModel instance representation
        """
        return 'SisypheDSIModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public method

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dsi.DiffusionSpectrumModel
            dipy DSI model
        """
        if self.hasGradients():
            if self._model is None:
                self._model = DiffusionSpectrumModel(self._gtable)
        return super().getModel()

    def computeFitting(self, wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheDSIModel instance.

        Parameters
        ----------
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if wait is not None:
                    wait.setInformationText('DSI model fitting...')
                self._model = DiffusionSpectrumModel(gtab=self._gtable)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getGFA(self) -> SisypheVolume:
        """
        Calculate Generalized Fractional Anisotropy (GFA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GFA map
        """
        if self._fmodel is not None:
            gfav = gfa(self._fmodel.odf(default_sphere))
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(gfav,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDSIModel instance attributes to xml instance. This method is called by save() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._DSI)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheDSIModel instance attributes from xml instance. This method is called by load() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'DSI'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to manage diffusion spectrum imaging deconvolution model

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDiffusionModel -> SisypheDSIDModel

    Creation: 29/10/2023
    Last revision: 21/03/2024
    """

    # Class method

    @classmethod
    def openModel(cls,
                  filename: str,
                  fit: bool = False,
                  binary: bool = True,
                  wait: DialogWait | None = None) -> SisypheDSIDModel:
        """
        Create a SisypheDSIDModel instance from a PySisyphe Diffusion model (.xdmodel) file.

        Parameters
        ----------
        filename : str
            Diffusion model file name
        fit : bool
            compute model fitting (default False)
        binary : bool
            - if True, binary part (DWI images, mask image, mean DWI image) is loaded (default True)
            - if False, only xml part is loaded
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheDSIModel
            loaded DSID model
        """
        filename = splitext(filename)[0] + cls._FILEEXT
        if exists(filename):
            r = SisypheDSIDModel()
            r.loadModel(filename, binary, wait)
            if fit and binary:
                if wait is not None: wait.setInformationText('DSID model fitting...')
                r.computeFitting()
            return r
        else: raise IOError('No such file {}.'.format(basename(filename)))

    # Special method

    def __init__(self) -> None:
        """
        SisypheDSIDModel instance constructor.
        """
        super().__init__()
        self._model: DiffusionSpectrumDeconvModel | None = None
        self._fmodel: DiffusionSpectrumDeconvFit | None = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheDSIDModel instance to str
         """
        buff = 'Diffusion Spectrum Imaging Deconvolution (DSID) model\n'
        buff += super().__str__()
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDSIDModel instance representation
        """
        return 'SisypheDSIDModel instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public method

    """
    Private attribute

    _model      dipy.reconst.dsi.DiffusionSpectrumDeconvModel
    _fmodel     dipy.reconst.dsi.DiffusionSpectrumDeconvFit
    """

    def getModel(self):
        """
        Get the model attribute of the current SisypheDiffusion instance.

        Returns
        -------
        dipy.reconst.dsi.DiffusionSpectrumDeconvModel
            dipy DSID model
        """
        if self.hasGradients():
            if self._model is None:
                self._model = DiffusionSpectrumDeconvModel(self._gtable)
        return super().getModel()

    def computeFitting(self, wait: DialogWait | None = None) -> None:
        """
        Estimate the diffusion model of the current SisypheDSIDModel instance.

        Parameters
        ----------
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasGradients() and self.hasDWI():
            if self._fmodel is None:
                if wait is not None:
                    wait.setInformationText('DSID model fitting...')
                self._model = DiffusionSpectrumDeconvModel(gtab=self._gtable)
                self._fmodel = self._model.fit(data=self._dwi, mask=self._mask)

    def getGFA(self) -> SisypheVolume:
        """
        Calculate Generalized Fractional Anisotropy (GFA) map.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            GFA map
        """
        if self._fmodel is not None:
            gfav = gfa(self._fmodel.odf(default_sphere))
            r = SisypheVolume()
            # noinspection PyTypeChecker
            r.copyFromNumpyArray(gfav,
                                 spacing=self._spacing,
                                 defaultshape=False)
            r.acquisition.setModalityToOT()
            r.acquisition.setSequence('FA')
            r.setID(self.getReferenceID())
            return r
        else: raise AttributeError('Model attribute is None.')

    # Public IO methods

    def createXML(self, doc: minidom.Document) -> None:
        """
        Write the current SisypheDSIDModel instance attributes to xml instance. This method is called by save() method,
        it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # Model type
            node = doc.createElement('model')
            root.appendChild(node)
            txt = doc.createTextNode(self._DSID)
            node.appendChild(txt)
            # Common attributes
            super().createXML(doc)

    def parseXML(self, doc: minidom.Document) -> dict:
        """
        Read the current SisypheDSIDModel instance attributes from xml instance. This method is called by load()
        method, it is not recommended for use.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        dict
            keys(str), values:
                - 'model', str, 'DSID'
                - 'dtype', str, diffusion weighted images datatype
                - 'shape', list[int, int, int], diffusion weighted images shape (image size in each dimension)
        """
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
    Description
    ~~~~~~~~~~~

    Class to compute streamlines from diffusion model.

    Attributes:

    - name of the generated bundle (default 'tractogram')
    - tracking algorithm

        - deterministic EuDX Euler integration
        - deterministic fiber orientation distribution
        - deterministic parallel transpor
        - deterministic closest peak direction
        - probabilistic bootstrap direction
        - probabilistic fiber orientation distribution

    - seed voxels from

        - FA threshold
        - ROI

    - seed count per voxel
    - step size between streamline points
    - stopping criterion

        - FA threshold
        - ROI
        - GM/WM/CSF Maps

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheTracking

    Creation: 29/10/2023
    Last revision: 07/04/2025
    """

    __slots__ = ['_model', '_name', '_alg', '_density', '_seeds', '_stepsize', '_npeaks', '_thresholdpeaks',
                 '_anglepeaks', '_minlength', '_stopping']

    # Class constants

    _DEUDX = 0
    _DFOD = 1
    _DPT = 2
    _DCPD = 3
    _PBSD = 4
    _PFOD = 5
    _ALG = {_DEUDX: 'Deterministic EuDX Euler integration',
            _DFOD: 'Deterministic Fiber orientation distribution',
            _DPT: 'Deterministic Parallel transport',
            _DCPD: 'Deterministic Closest peak direction',
            _PBSD: 'Probabilistic Bootstrap direction',
            _PFOD: 'Probabilistic Fiber orientation distribution'}

    # Special method

    """
    Private attribute

    _model : SisypheDiffusionModel
    _name : str
    _alg : str
        tracking algorithm
    _density : int
        seed count per voxel
    _seeds : ndarray
        seed mask
    _stepsize : float
        step size in mm
    _npeaks : int
        maximum  number of peaks
    _thresholdpeaks : float
        relative peak threshold
    _anglepeaks : float
        min separation angle between peaks
    _minlength : float
        streamline minimum length (mm)
    _stopping : ActStoppingCriterion | BinaryStoppingCriterion | ThresholdStoppingCriterion | None
    """

    def __init__(self, model: SisypheDiffusionModel):
        """
        SisypheTracking instance constructor.

        Parameters
        ----------
        model : SisypheDiffusionModel
        """
        self._model = model
        self._name = 'tractogram'
        self._alg: int = 0
        self._density: int = 1
        self._seeds: ndarray | None = None
        self._stepsize: float = 1.0
        self._npeaks: int = 5
        # noinspection PyUnresolvedReferences
        self._thresholdpeaks: cython.double = 0.5
        # noinspection PyUnresolvedReferences
        self._anglepeaks: cython.double = 30
        self._minlength = 0.0
        self._stopping = None

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheTracking instance to str
         """
        buff = 'Bundle name: {}\n'.format(self._name)
        buff += 'Tracking algorithm: {}\n'.format(self.getTrackingAlgorithmAsString())
        buff += 'Seed count per voxel: {}\n'.format(self._density)
        if self._seeds is None: buff += 'Number of seeds: 0\n'
        else: buff += 'Number of seeds: {}\n'.format(self._seeds.sum())
        buff += 'Step size: {} mm\n'.format(self._stepsize)
        if self._stopping is not None:
            if isinstance(self._stopping, ActStoppingCriterion):
                buff += 'gray matter/white matter/cerebro-spinal fluid maps stopping criterion\n'
            elif isinstance(self._stopping, BinaryStoppingCriterion):
                buff += 'ROI stopping criterion\n'
            elif isinstance(self._stopping, ThresholdStoppingCriterion):
                buff += 'FA/GFA stopping criterion\n'
        buff += str(self._model)
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheTracking instance representation
        """
        return 'SisypheTracking instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setBundleName(self, name: str):
        """
        Set the bundle name attribute of the current SisypheTracking instance.

        Parameters
        ----------
        name : str
            name of the generated bundle
        """
        self._name = name

    def getBundleName(self) -> str:
        """
        Get the bundle name attribute of the current SisypheTracking instance.

        Returns
        -------
        str
            name of the generated bundle
        """
        return self._name

    def setTrackingAlgorithm(self, alg: int = 0) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance as int code.

        Parameters
        ----------
        alg : int
            - 0 deterministic Euler integration
            - 1 deterministic particle filtering
            - 2 deterministic closest peak direction
            - 3 deterministic fiber orientation distribution
            - 4 probabilistic bootstrap direction
            - 5 probabilistic fiber orientation distribution
        """
        if alg in self._ALG: self._alg = alg
        else: raise ValueError('Invalid algorithm code.')

    def setTrackingAlgorithmToDeterministicEulerIntegration(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to deterministic Euler integration.
        """
        self._alg = self._DEUDX

    def setTrackingAlgorithmToDeterministicFiberOrientationDistribution(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to deterministic fiber orientation
        distribution.
        """
        self._alg = self._DFOD

    def setTrackingAlgorithmToDeterministicParallelTransport(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to deterministic parallel
        transport.
        """
        self._alg = self._DPT

    def setTrackingAlgorithmToDeterministicClosestPeakDirection(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to deterministic closest peak
        direction.
        """
        self._alg = self._DCPD

    def setTrackingAlgorithmToProbabilisticBootstrapDirection(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to probabilistic bootstrap
        direction.
        """
        self._alg = self._PBSD

    def setTrackingAlgorithmToProbabilisticFiberOrientationDistribution(self) -> None:
        """
        Set the tracking algorithm attribute of the current SisypheTracking instance to probabilistic fiber orientation
        distribution.
        """
        self._alg = self._PFOD

    def getTrackingAlgorithm(self) -> int:
        """
        Get the tracking algorithm attribute of the current SisypheTracking instance as int code.

        Returns
        -------
        int
            - 0 Deterministic EuDX Euler integration
            - 1 Deterministic Fiber orientation distribution
            - 2 Deterministic Parallel transport
            - 3 Deterministic Closest peak direction
            - 4 Probabilistic Bootstrap direction
            - 5 Probabilistic Fiber orientation distribution
        """
        return self._alg

    def getTrackingAlgorithmAsString(self) -> str:
        """
        Get the tracking algorithm attribute of the current SisypheTracking instance.

        Returns
        -------
        str
            - Deterministic EuDX Euler integration
            - Deterministic Fiber orientation distribution
            - Deterministic Parallel transport
            - Deterministic Closest peak direction
            - Probabilistic Bootstrap direction
            - Probabilistic Fiber orientation distribution
        """
        return self._ALG[self._alg]

    def setSeedCountPerVoxel(self, n: int = 1) -> None:
        """
        Set the seed count per voxel attribute of the current SisypheTracking instance. Number of streamlines generated
        per seed voxel.

        Parameters
        ----------
        n : int
             number of streamlines generated per seed voxel
        """
        if 0 < n < 10: self._density = n
        else: raise ValueError('invalid number of seeds per voxel.')

    def getSeedCountPerVoxel(self) -> int:
        """
        Get the seed count per voxel attribute of the current SisypheTracking instance.
        Number of streamlines generated per seed voxel.

        Returns
        -------
        int
            number of streamlines generated per seed voxel
        """
        return self._density

    def setStepSize(self, stepsize: float = 0.5) -> None:
        """
        Set the step size attribute of the current SisypheTracking instance. Step size (mm) between streamline points
        (default 0.5).

        Parameters
        ----------
        stepsize : float
            step size
        """
        if 0.1 <= stepsize <= 2.0: self._stepsize = stepsize
        else: raise ValueError('invalid step size.')

    def getStepSize(self) -> float:
        """
        Get the step size attribute of the current SisypheTracking instance. Step size (mm) between streamline points.

        Returns
        -------
        float
            step size
        """
        return self._stepsize

    def setStoppingCriterionToFAThreshold(self, threshold: float = 0.1) -> None:
        """
        Set the stopping criterion attribute of the current SisypheTracking instance to FA threshold. Streamline
        reconstruction is stopped when the current point is in a voxel whose FA value is below a threshold.

        Parameters
        ----------
        threshold : float
            FA threshold (between 0.0 and 1.0, default 0.1)
        """
        if 0.0 < threshold < 1.0:
            if not self._model.isFitted(): self._model.computeFitting()
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                FA = self._model.getFA().copyToNumpyArray(defaultshape=False)
            else:
                # noinspection PyUnresolvedReferences
                FA = self._model.getGFA().copyToNumpyArray(defaultshape=False)
            self._stopping = ThresholdStoppingCriterion(FA, threshold)
        else: raise ValueError('Invalid threshold.')

    def setStoppingCriterionToROI(self, roi: SisypheROI) -> None:
        """
        Set the stopping criterion attribute of the current SisypheTracking instance to ROI. Streamline reconstruction
        is stopped when the current point is in a voxel belonging to the mask of a ROI.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            stopping criterion roi
        """
        self._stopping = BinaryStoppingCriterion(roi.copyToNumpyArray(defaultshape=False))

    def setStoppingCriterionToMaps(self,
                                   gm: SisypheVolume(),
                                   wm: SisypheVolume(),
                                   csf: SisypheVolume()) -> None:
        """
        Set the stopping criterion attribute of the current SisypheTracking instance to maps. This stopping criterion
        uses gray matter, white matter and cerebro-spinal fluid maps. Streamline reconstruction is stopped when the
        current point is in a voxel belonging to gray matter (> 0.5), cerebro-spinal fluid (> 0.5) or background.

        Parameters
        ----------
        gm : Sisyphe.core.sisypheVolume.SisypheVolume
            gray matter probability map
        wm : Sisyphe.core.sisypheVolume.SisypheVolume
            white matter probability map
        csf : Sisyphe.core.sisypheVolume.SisypheVolume
            cerebro-spinal fluid probability map
        """
        shape = self._model.getMask()
        if gm.acquisition.getSequence() != SisypheAcquisition.GM:
            raise ValueError('{} volume is not gray matter map.'.format(gm.getBasename()))
        if wm.acquisition.getSequence() != SisypheAcquisition.WM:
            raise ValueError('{} volume is not white matter map.'.format(wm.getBasename()))
        if csf.acquisition.getSequence() != SisypheAcquisition.CSF:
            raise ValueError('{} volume is not cerebro-spinal fluid map.'.format(csf.getBasename()))
        if gm.getSize() != shape:
            raise ValueError('invalid {} size.'.format(gm.getBasename()))
        if wm.getSize() != shape:
            raise ValueError('invalid {} size.'.format(wm.getBasename()))
        if csf.getSize() != shape:
            raise ValueError('invalid {} size.'.format(csf.getBasename()))
        include = gm.copyToNumpyArray(defaultshape=False)
        wm = wm.copyToNumpyArray(defaultshape=False)
        exclude = csf.copyToNumpyArray(defaultshape=False)
        back = ones(include.shape)
        back[(include + wm + exclude) > 0] = 0
        include[back > 0] = 1
        self._stopping = ActStoppingCriterion(include, exclude)

    def setSeedsFromRoi(self, roi: SisypheROI) -> None:
        """
        Set seed voxels of the current SisypheTracking instance from a ROI. Streamlines are generated from voxels
        belonging to the mask of a ROI.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            seed roi
        """
        self._seeds = roi.copyToNumpyArray(defaultshape=False)

    def setSeedsFromFAThreshold(self, threshold: float) -> None:
        """
        Set seed voxels of the current SisypheTracking instance from FA threshold. Streamlines are generated from
        voxels whose FA value is above a given threshold.

        Parameters
        ----------
        threshold : float
            FA threshold
        """
        if 0.0 < threshold < 1.0:
            if not self._model.isFitted(): self._model.computeFitting()
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                FA = self._model.getFA().copyToNumpyArray(defaultshape=False)
            else:
                # noinspection PyUnresolvedReferences
                FA = self._model.getGFA().copyToNumpyArray(defaultshape=False)
            self._seeds = (FA > threshold).astype('uint8')
        else: raise ValueError('Invalid threshold.')

    def getSeeds(self) -> ndarray:
        """
        Get array of seeds from the current SisypheTracking instance.

        Returns
        -------
        numpy.ndarray
            array of seeds
        """
        affine = diag(list(self._model.getSpacing()) + [1.0])
        return seeds_from_mask(self._seeds, affine, self._density)

    def setNumberOfPeaks(self, v: int = 5):
        """
        Set the number of peaks attribute of the current SisypheTracking instance. Maximum number of odf peaks used by
        deterministic euler integration tracking algorithm.

        Returns
        -------
        int
            maximum number of peaks (default 5)
        """
        if v < 1: v = 1
        elif v > 10: v = 10
        self._npeaks = v

    def getNumberOfPeaks(self) -> int:
        """
        Get the number of peaks attribute of the current SisypheTracking instance. Maximum number of odf peaks used by
        deterministic euler integration tracking algorithm.

        Returns
        -------
        int
            maximum number of peaks
        """
        return self._npeaks

    def setMinSeparationAngleOfPeaks(self, v: float):
        """
        Set the minimum separation angle attribute of the current SisypheTracking instance. If two odf peaks are too
        close i.e. separation angle below this threshold, only the larger of the two is returned. This parameter is
        only ysed by the deterministic euler integration tracking algorithm.

        Parameters
        ----------
        v : float
            minimum separation angle between peaks in degrees
        """
        if v < 0.0: v = 0.0
        elif v > 90.0: v = 90.0
        self._anglepeaks = v

    def getMinSeparationAngleOfPeaks(self) -> float:
        """
        Get the minimum separation angle attribute of the current SisypheTracking instance. If two odf peaks are too
        close i.e. separation angle below this threshold, only the larger of the two is returned. This parameter is
        only ysed by the deterministic euler integration tracking algorithm.

        Returns
        -------
        float
            minimum separation angle between peaks in degrees
        """
        return self._anglepeaks

    def setRelativeThresholdOfPeaks(self, v: float):
        """
        Set the relative peak threshold attribute of the current SisypheTracking instance. Only return odf peaks
        greater than relative_peak_threshold * m where m is the largest peak. This parameter is only ysed by the
        deterministic euler integration tracking algorithm.

        Parameters
        ----------
        v : float
            relative peak threshold (ratio, 0.0 to 1.0)
        """
        if v < 0.0: v = 0.0
        elif v > 1.0: v = 1.0
        self._thresholdpeaks = v

    def getRelativeThresholdOfPeaks(self) -> float:
        """
        Get the relative peak threshold attribute of the current SisypheTracking instance. Only return odf peaks
        greater than relative_peak_threshold * m where m is the largest peak. This parameter is only ysed by the
        deterministic euler integration tracking algorithm.

        Returns
        -------
        float
            relative peak threshold (ratio, 0.0 to 1.0)
        """
        return self._thresholdpeaks

    def setMinLength(self, l : float = 0.0):
        """
        Set the minimum length attribute of the current SisypheTracking instance. Streamlines with a length below this
        threshold are removed.

        Parameters
        ----------
        l : float
            minimum length in mm
        """
        self._minlength = l

    def getMinLength(self) -> float:
        """
        Get the minimum length attribute of the current SisypheTracking instance. Streamlines with a length below this
        threshold are removed.

        Returns
        -------
        float
            minimum length in mm
        """
        return self._minlength

    # noinspection PyTypeChecker
    def computeTracking(self, wait: DialogWait | None = None) -> SisypheStreamlines:
        """
        Compute the fiber tracking according to the current SisypheTracking instance attributes (bundle name, diffusion
        model, tracking algorithm, seed method, seed count per voxel, step size and stopping criterion).

        Parameters
        ----------
        wait: Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)

        Returns
        -------
        SisypheStreamlines
            streamlines
        """
        sls = None
        affine = diag(list(self._model.getSpacing()) + [1.0])
        seeds = seeds_from_mask(self._seeds, affine, density=self._density)
        l = int(self._minlength / self._stepsize)
        if l < 2: l = 2
        if wait is not None: wait.setInformationText('{} tracking...'.format(self.getTrackingAlgorithmAsString()))
        # Deterministic Euler integration
        if self._alg == self._DEUDX:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                peaks = peaks_from_model(model=self._model.getModel(),
                                         data=self._model.getDWI(),
                                         sphere=small_sphere,
                                         relative_peak_threshold=self._thresholdpeaks,
                                         min_separation_angle=self._anglepeaks,
                                         mask=self._model.getMask(),
                                         sh_order_max=8,
                                         sh_basis_type=None,
                                         npeaks=2)
            elif isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                peaks = peaks_from_model(model=self._model.getModel(),
                                         data=self._model.getDWI(),
                                         sphere=small_sphere,
                                         relative_peak_threshold=self._thresholdpeaks,
                                         min_separation_angle=self._anglepeaks,
                                         mask=self._model.getMask(),
                                         sh_order_max=8,
                                         sh_basis_type=None,
                                         npeaks=self._npeaks)
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                peaks = peaks_from_model(model=self._model.getModel(),
                                         data=self._model.getDWI(),
                                         sphere=default_sphere,
                                         relative_peak_threshold=self._thresholdpeaks,
                                         min_separation_angle=self._anglepeaks,
                                         mask=self._model.getMask(),
                                         sh_order_max=8,
                                         sh_basis_type=None,
                                         npeaks=self._npeaks)
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if peaks is not None:
                sl = Streamlines(eudx_tracking(seeds,
                                               self._stopping,
                                               affine,
                                               min_len=l,
                                               step_size=self._stepsize,
                                               pam=peaks))
                sls = SisypheStreamlines(sl)
        # Deterministic Fiber orientation distribution
        if self._alg == self._DFOD:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                sl = Streamlines(deterministic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sf=self._model.getFittedModel().odf(small_sphere),
                                                        sphere=small_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                sl = Streamlines(deterministic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sf=self._model.getFittedModel().odf(small_sphere),
                                                        sphere=small_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            elif isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                # noinspection PyUnresolvedReferences
                sl = Streamlines(deterministic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sh=self._model.getFittedModel().shm_coeff,
                                                        sphere=default_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if sl is not None: sls = SisypheStreamlines(sl)
        # Deterministic Parallel transport
        if self._alg == self._DPT:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                sl = Streamlines(ptt_tracking(seeds,
                                              self._stopping,
                                              affine,
                                              sf=self._model.getFittedModel().odf(small_sphere),
                                              sphere=small_sphere,
                                              max_angle=30,
                                              min_len=l,
                                              step_size=self._stepsize))
            elif isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                sl = Streamlines(ptt_tracking(seeds,
                                              self._stopping,
                                              affine,
                                              sf=self._model.getFittedModel().odf(small_sphere),
                                              sphere=small_sphere,
                                              max_angle=30,
                                              min_len=l,
                                              step_size=self._stepsize))
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                sl = Streamlines(ptt_tracking(seeds,
                                              self._stopping,
                                              affine,
                                              sf=self._model.getFittedModel().odf(default_sphere),
                                              sphere=default_sphere,
                                              max_angle=30,
                                              min_len=l,
                                              step_size=self._stepsize))
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if sl is not None: sls = SisypheStreamlines(sl)
        # Deterministic Closest peak direction
        if self._alg == self._DCPD:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                sl = Streamlines(closestpeak_tracking(seeds,
                                                      self._stopping,
                                                      affine,
                                                      sf=self._model.getFittedModel().odf(small_sphere).clip(min=0),
                                                      sphere=small_sphere,
                                                      max_angle=30,
                                                      min_len=l,
                                                      step_size=self._stepsize))
            elif isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                # noinspection PyUnresolvedReferences
                sl = Streamlines(closestpeak_tracking(seeds,
                                                      self._stopping,
                                                      affine,
                                                      sh=self._model.getFittedModel().shm_coeff,
                                                      sphere=small_sphere,
                                                      max_angle=30,
                                                      min_len=l,
                                                      step_size=self._stepsize))
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                sl = Streamlines(closestpeak_tracking(seeds,
                                                      self._stopping,
                                                      affine,
                                                      sf=self._model.getFittedModel().odf(default_sphere).clip(min=0),
                                                      sphere=default_sphere,
                                                      max_angle=30,
                                                      step_size=self._stepsize))
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if sl is not None: sls = SisypheStreamlines(sl)
        # Probabilistic Bootstrap direction
        if self._alg == self._PBSD:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel, SisypheSHCSAModel, SisypheSHCSDModel)):
                sl = Streamlines(bootstrap_tracking(seeds,
                                                    self._stopping,
                                                    affine,
                                                    step_size=self._stepsize,
                                                    min_len=l,
                                                    data=self._model.getDWI(),
                                                    model=self._model.getModel(),
                                                    max_angle=30.0,
                                                    sphere=small_sphere))
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                sl = Streamlines(bootstrap_tracking(seeds,
                                                    self._stopping,
                                                    affine,
                                                    step_size=self._stepsize,
                                                    min_len=l,
                                                    data=self._model.getDWI(),
                                                    model=self._model.getModel(),
                                                    max_angle=30.0,
                                                    sphere=default_sphere))
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if sl is not None: sls = SisypheStreamlines(sl)
        # Probabilistic Fiber orientation distribution
        if self._alg == self._PFOD:
            if isinstance(self._model, (SisypheDTIModel, SisypheDKIModel)):
                sl = Streamlines(probabilistic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sf=self._model.getFittedModel().odf(small_sphere),
                                                        sphere=small_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            elif isinstance(self._model, (SisypheSHCSAModel, SisypheSHCSDModel)):
                # noinspection PyUnresolvedReferences
                sl = Streamlines(probabilistic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sh=self._model.getFittedModel().shm_coeff,
                                                        sphere=small_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            elif isinstance(self._model, (SisypheDSIModel, SisypheDSIDModel)):
                sl = Streamlines(probabilistic_tracking(seeds,
                                                        self._stopping,
                                                        affine,
                                                        sf=self._model.getFittedModel().odf(default_sphere),
                                                        sphere=default_sphere,
                                                        max_angle=30,
                                                        min_len=l,
                                                        step_size=self._stepsize))
            else: raise TypeError('Invalid model type ({}).'.format(type(self._model)))
            if sl is not None: sls = SisypheStreamlines(sl)
        if sls is not None:
            sls.getBundle(0).setName(self._name)
            sls.setReferenceID(self._model)
            sls.setWholeBrainStatus(True)
            sls.setDWIShape(self._model.getShape())
            sls.setDWISpacing(self._model.getSpacing())
        return sls
