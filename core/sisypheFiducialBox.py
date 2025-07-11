"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from os import remove
from os.path import exists
from os.path import splitext

from xml.dom import minidom

from math import sqrt

import numpy as np

from SimpleITK import Image as sitkImage
from SimpleITK import sitkBall
from SimpleITK import OtsuThreshold as sitkOtsuThreshold
from SimpleITK import BinaryDilate as sitkBinaryDilate
from SimpleITK import BinaryErode as sitkBinaryErode
from SimpleITK import BinaryFillhole as sitkBinaryFillhole
from SimpleITK import ConnectedComponent as sitkConnectedComponent
from SimpleITK import LabelShapeStatisticsImageFilter as sitkLabelShapeStatisticsImageFilter

from vtk import vtkPoints
from vtk import vtkLandmarkTransform

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTransform import SisypheTransform

__all__ = ['SisypheFiducialBox']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - PyQt5.QtCore.QObject -> SisypheFiducialBox
"""

class SisypheFiducialBox(QObject):
    """
    Description
    ~~~~~~~~~~~

    This class detects the Elekta Leksell frame's fiducial markers. It computes a rigid transformation to calculate
    coordinates between the geometric Leksell reference and the image coordinates, and vice versa.

    Elekta Leksell frame space, LAI+ convention:

        - right (0.0) to left (+)
        - posterior (0.0) to anterior (+)
        - superior (0.0) to inferior (+)
        - origin right, posterior, superior

    Fiducial coordinates:

        - Fiducial              x       y       z
        - anterior right  ->    5.0     160.0   40.0 cranial to 160.0 caudal
        - anterior left   ->    195.0   160.0   40.0 cranial to 160.0 caudal
        - posterior right ->    5.0     40.0    40.0 cranial to 160.0 caudal
        - posterior left  ->    195.0   40.0    40.0 cranial to 160.0 caudal

    Inheritance
    ~~~~~~~~~~~

    QObject -> SisypheFiducialBox

    Creation: 26/07/2022
    Last revision: 21/05/2025
    """
    # Class constant

    _FILEEXT = '.xfid'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheFiducialBox file extension.

        Returns
        -------
        str
            '.xfid'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheFiducialBox filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Fiducial markers (.xfid)'
        """
        return 'PySisyphe Fiducial markers (*{})'.format(cls._FILEEXT)

    # Custom Qt Signal

    ProgressValueChanged = pyqtSignal(int)
    ProgressRangeChanged = pyqtSignal(int, int)
    ProgressTextChanged = pyqtSignal(str)

    # Special methods

    """
    Private attributes

    _nbfid      int, fiducials count (6 or 9)
    _fidtol     float, distance tolerance of fiducial markers
    _fidlist    dict, fiducial markers coordinates
    _errorlist  dict, fiducial markers errors
    _errorstats dict, fiducial markers errors statistics
    _volume     SisypheVolume
    _trf        SisypheTransform
    """

    def __init__(self) -> None:
        """
        SisypheFiducialBox instance constructor.
        """
        super().__init__()
        self._trf = None
        self._volume = None
        self._nbfid = 0
        self._fidtol = 0
        """
        _fidlist = dict[key1: int, value1: dict[key2: int, value2: list[float, float, float]]]
                        key1 int, slice number
                        key2 int, marker number (see _firstSliceSearch() method for marker code)
                        value2 list(float, float, float), marker coordinates x, y, z
        """
        self._fidlist = dict()
        """
        _errorlist = dict[key1: int, value1: dict[key2: int, value2: float]]
                          key1 int, slice number
                          key2 int, marker number (see _firstSliceSearch() method for marker code)
                          value2 float, error in millimeters
        """
        self._errorlist = dict()
        """
        _errorstats = dict[key: str, value: float]
                           key in ('Mean', 'RMS', 'Median', 'Std', '25th', '75th', 'Min', 'Max')
        """
        self._errorstats = dict()

    # Container Public methods

    def __getitem__(self, index) -> list[float]:
        """
        Special overloaded container getter method. Get a fiducial marker coordinates.

        Parameters
        ----------
        index : tuple[int, int]
            - first int, slice index
            - second int, fiducial marker index

        Returns
        -------
        list[float]
            x, y, z fiducial marker coordinates
        """
        return self.getMarker(index[0], index[1])

    def __setitem__(self, index, value) -> None:
        """
        Special overloaded container setter method. Set a fiducial marker.

        Parameters
        ----------
        index : tuple[int, int]
            - first int, slice index
            - second int, fiducial marker index
        value : tuple[float, float, float]
            x, y, z fiducial marker coordinates
        """
        if isinstance(value, tuple):
            if len(value) == 2:
                if isinstance(value[0], float) and isinstance(value[1], float):
                    self._fidlist[index[0]][index[1]] = value
                    return
        raise TypeError('Wrong value type.')

    def __delitem__(self, index) -> None:
        """
        Special overloaded container delete method called by the built-in del() python function. Remove a fiducial
        marker.

        Parameters
        ----------
        index : tuple[int, int]
            - first int, slice index
            - second int, fiducial marker index
        """
        if index in self._fidlist:
            del self._fidlist[index]

    def __contains__(self, value) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether a slice index
        is valid (i.e. it contains at least 6 or 9 fiducial markers depending on configuration)

        Parameters
        ----------
        value : int
            slice index

        Returns
        -------
        bool
            True if slice index is valid
        """
        return self.hasSlice(value)

    def __len__(self) -> int:
        """
        Special overloaded container method called by the built-in len() python function. Get list of valid slice
        indexes (i.e. slices with at least 6 or 9 fiducial markers depending on configuration).

        Returns
        -------
        list[int]
            list of valid indexes
        """
        return len(self._fidlist)

    # Private methods
    
    def _calcDistBetweenFiducials(self, idx: int, marker1: int, marker2: int) -> float:
        f1 = self._fidlist[idx][marker1]
        f2 = self._fidlist[idx][marker2]
        return sqrt((f1[0] - f2[0]) ** 2 + (f1[1] - f2[1]) ** 2)

    def _sliceSearch(self, img: sitkImage, idx: int, idx0: int) -> int:
        slc = sitkBinaryDilate(img[:, :, idx], [2, 2], sitkBall)
        slc = sitkBinaryFillhole(slc)
        slc = sitkBinaryErode(slc, [2, 2], sitkBall)
        cc = sitkConnectedComponent(slc)
        f = sitkLabelShapeStatisticsImageFilter()
        f.Execute(cc)
        n = f.GetNumberOfLabels()
        if n > 5:
            labels = list(f.GetLabels())
            # Search for major component (head)
            buff = list()
            for i in range(1, n):
                buff.append(f.GetNumberOfPixels(i))
            head = labels[buff.index(max(buff))]
            labels.remove(head)
            coor = list()
            for i in range(len(labels)):
                c = f.GetCentroid(labels[i])
                coor.append(c)
            # Search for marker locations
            tol = self._fidtol * abs(idx - idx0)
            self._fidlist[idx] = dict()
            for i in range(len(coor)):
                c = coor[i]
                for j in range(self._nbfid):
                    fid = self._fidlist[idx0][j]
                    v = sqrt((c[0] - fid[0]) ** 2 + (c[1] - fid[1]) ** 2)
                    if v < tol:
                        self._fidlist[idx][j] = c
                        break
            if len(self._fidlist[idx]) < self._nbfid:
                del self._fidlist[idx]
                return 1
            else: return self._nbfid
        else: return 0

    def _firstSliceSearch(self, img: sitkImage, idx: int) -> None:
        slc = img[:, :, idx]
        slc = sitkBinaryDilate(slc, [2, 2], sitkBall)
        slc = sitkBinaryFillhole(slc)
        cc = sitkConnectedComponent(slc)
        f = sitkLabelShapeStatisticsImageFilter()
        f.ComputePerimeterOff()
        f.ComputeFeretDiameterOff()
        f.ComputeOrientedBoundingBoxOff()
        f.Execute(cc)
        labels = list(f.GetLabels())
        n = f.GetNumberOfLabels()
        # < Revision 21/05/2025
        # Search for major component (head)
        buff = list()
        for i in range(1, n+1):
            buff.append(f.GetNumberOfPixels(i))
        h = labels[buff.index(max(buff))]
        labels.remove(h)
        buff.remove(max(buff))
        # Search and removal non-fiducial components
        n = len(buff)
        if n not in (6, 9) and n > 5:
            m = int(np.median(np.array(buff)))
            minf = m // 2
            msup = m * 2
            for i in range(n - 1, -1, -1):
                if minf < buff[i] or buff[i] > msup:
                    del labels[i]
        # vox = self._volume.getVoxelVolume()
        # buff = list()
        # for i in range(len(labels)):
        #     if vox * f.GetNumberOfPixels(labels[i]) > 100: buff.append(i)
        # if len(buff) > 0:
        #     for i in range(len(buff) - 1, -1, -1): del labels[buff[i]]
        # Revision 21/05/2025 >
        self._nbfid = len(labels)
        if self._nbfid in (6, 9):
            """
            Marker codes
            
                            Ant    
                     6   7           8
                     o - o --------- o
               3 o                       o 2
            R    |                       |       
            i    |                       |    L
            g    |                       |    e
            h  4 o                       o 1  f
            t    |                       |    t
               5 o                       o 0
                            Post
                
            Search for most posterior left and anterior right markers
            markers 0 and 3, if 6 markers box
            markers 0 and 6, if 9 markers box
            """
            coor = list()
            buff = list()
            for i in range(self._nbfid):
                c = f.GetCentroid(labels[i])
                v = c[0] ** 2 + c[1] ** 2
                coor.append(c)
                buff.append(v)
            fid1 = coor[buff.index(min(buff))]
            fid2 = coor[buff.index(max(buff))]
            self._fidlist.clear()
            self._fidlist[idx] = dict()
            # Six fiducial box
            if self._nbfid == 6:
                self._fidlist[idx][0] = fid1
                self._fidlist[idx][3] = fid2
                coor.remove(fid1)
                coor.remove(fid2)
                # Search for 1, 2, 4, 5 markers
                buff1 = list()
                buff2 = list()
                for i in range(len(coor)):
                    v1 = sqrt((coor[i][0] - fid1[0]) ** 2 + (coor[i][1] - fid1[1]) ** 2)
                    v2 = sqrt((coor[i][0] - fid2[0]) ** 2 + (coor[i][1] - fid2[1]) ** 2)
                    # left markers, closest to marker 0
                    if v1 < 170: buff1.append([v1, coor[i]])
                    # right markers, closest to marker 3
                    if v2 < 170: buff2.append([v2, coor[i]])
                if len(buff1) != 2 or len(buff2) != 2: raise ValueError('Wrong fiducial markers geometry.')
                else:
                    if buff1[0][0] > buff1[1][0]:
                        # noinspection PyUnresolvedReferences
                        buff1[0], buff1[1] = buff1[1], buff1[0]
                    if buff2[0][0] > buff2[1][0]:
                        # noinspection PyUnresolvedReferences
                        buff2[0], buff2[1] = buff2[1], buff2[0]
                    # < Revision 21/05/2025
                    # if 119 < buff1[1][0] < 126:  # 120 + 5%
                    if 116 < buff1[1][0] < 126:  # 120 + 5%
                        self._fidlist[idx][1] = buff1[0][1]
                        self._fidlist[idx][2] = buff1[1][1]
                    # Revision 21/05/2025 >
                    else: raise ValueError('Wrong fiducial markers geometry.')
                    # < Revision 21/05/2025
                    # if 119 < buff2[1][0] < 126:  # 120 + 5%
                    if 116 < buff2[1][0] < 126:  # 120 + 5%
                        self._fidlist[idx][4] = buff2[0][1]
                        self._fidlist[idx][5] = buff2[1][1]
                    # Revision 21/05/2025 >
                    else: raise ValueError('Wrong fiducial markers geometry.')
                    d = self._calcDistBetweenFiducials(idx, 0, 5)
                    # < Revision 21/05/2025
                    # if not (189 < d < 200): raise ValueError('Wrong fiducial markers geometry.')
                    if not (186 < d < 200): raise ValueError('Wrong fiducial markers geometry.')
                    # Revision 21/05/2025 >
            # Nine fiducial box
            elif self._nbfid == 9:
                self._fidlist[idx][0] = fid1
                self._fidlist[idx][6] = fid2
                coor.remove(fid1)
                coor.remove(fid2)
                # Search for marker 3
                fid3 = None
                for i in range(len(coor)):
                    v1 = sqrt((coor[i][0] - fid1[0]) ** 2 + (coor[i][1] - fid1[1]) ** 2)
                    v2 = sqrt((coor[i][0] - fid2[0]) ** 2 + (coor[i][1] - fid2[1]) ** 2)
                    # < Revision 21/05/2025
                    # if 223 < v1 < 235 and 64 < v2 < 70:
                    if 220 < v1 < 235 and 61 < v2 < 70:
                        fid3 = coor[i]
                        self._fidlist[idx][3] = fid3
                        coor.remove(fid3)
                        break
                    # Revision 21/05/2025 >
                if fid3 is None: raise ValueError('Wrong fiducial markers geometry.')
                # Search for markers 2, 5, 8
                for i in range(len(coor)):
                    v1 = sqrt((coor[i][0] - fid1[0]) ** 2 + (coor[i][1] - fid1[1]) ** 2)
                    v2 = sqrt((coor[i][0] - fid2[0]) ** 2 + (coor[i][1] - fid2[1]) ** 2)
                    v3 = sqrt((coor[i][0] - fid3[0]) ** 2 + (coor[i][1] - fid3[1]) ** 2)
                    # < Revision 21/05/2025
                    # if 119 < v1 < 126: self._fidlist[idx][2] = coor[i]
                    # elif 119 < v2 < 126: self._fidlist[idx][8] = coor[i]
                    # elif 119 < v3 < 126: self._fidlist[idx][5] = coor[i]
                    if 116 < v1 < 126: self._fidlist[idx][2] = coor[i]
                    elif 116 < v2 < 126: self._fidlist[idx][8] = coor[i]
                    elif 116 < v3 < 126: self._fidlist[idx][5] = coor[i]
                    # Revision 21/05/2025 >
                if 2 in self._fidlist[idx]: coor.remove(self._fidlist[idx][2])
                if 8 in self._fidlist[idx]: coor.remove(self._fidlist[idx][8])
                if 5 in self._fidlist[idx]: coor.remove(self._fidlist[idx][5])
                if len(coor) != 3: raise ValueError('Wrong fiducial markers geometry.')
                # Search for middle markers 1, 4, 7
                buff = list()
                for i in range(len(coor)):
                    buff.clear()
                    buff.append(sqrt((coor[i][0] - fid1[0]) ** 2 + (coor[i][1] - fid1[1]) ** 2))
                    buff.append(sqrt((coor[i][0] - fid2[0]) ** 2 + (coor[i][1] - fid2[1]) ** 2))
                    buff.append(sqrt((coor[i][0] - fid3[0]) ** 2 + (coor[i][1] - fid3[1]) ** 2))
                    v = buff.index(min(buff))
                    if v == 0: self._fidlist[idx][1] = coor[i]
                    elif v == 1: self._fidlist[idx][7] = coor[i]
                    else: self._fidlist[idx][4] = coor[i]

    def _markersSearch(self, slc: int | None = None) -> None:
        # noinspection PyUnresolvedReferences
        self.ProgressTextChanged.emit('Fiducial markers detection...')
        # noinspection PyUnresolvedReferences
        self.ProgressRangeChanged.emit(0, self._volume.getDepth())
        # noinspection PyUnresolvedReferences
        self.ProgressValueChanged.emit(0)
        self._fidtol = self._volume.getSpacing()[2] * 2
        if self._volume.acquisition.isCT():
            t = 300 - self._volume.getIntercept()
            img = self._volume.getSITKImage() > t
        else: img = sitkOtsuThreshold(self._volume.getSITKImage(), 0, 1)
        if slc is not None and 0 <= slc < self._volume.getDepth(): n = slc
        else: n = self._volume.getDepth() // 2
        for i in range(10):
            self._firstSliceSearch(img, n + i)
            if self._nbfid in (6, 9):
                n = n + i
                break
        if self._nbfid not in (6, 9): raise ValueError('No fiducial box or wrong number of fiducial markers, '
                                                       '{} detected, must be 6 or 9.')
        c = 1
        # noinspection PyUnresolvedReferences
        self.ProgressValueChanged.emit(c)
        # Next slices
        idx0 = n
        for i in range(n + 1, self._volume.getDepth()):
            c += 1
            # noinspection PyUnresolvedReferences
            self.ProgressValueChanged.emit(c)
            nb = self._sliceSearch(img, i, idx0)
            if nb == self._nbfid: idx0 = i
            elif nb == 0: break
        c = n
        # noinspection PyUnresolvedReferences
        self.ProgressValueChanged.emit(n)
        # Previous slices
        idx0 = n
        for i in range(n - 1, -1, -1):
            c += 1
            # noinspection PyUnresolvedReferences
            self.ProgressValueChanged.emit(c)
            nb = self._sliceSearch(img, i, idx0)
            if nb == self._nbfid: idx0 = i
            elif nb == 0: break
        # noinspection PyUnresolvedReferences
        self.ProgressValueChanged.emit(self._volume.getDepth())

    # Public methods

    def execute(self, vol: SisypheVolume) -> None:
        """
        Execute Leksell fiducial markers detection to calculate rigid transformation between image and Leksell
        geometric reference.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            PySisyphe volume
        """
        if isinstance(vol, SisypheVolume):
            self.markersSearch(vol)
            self.calcTransform()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def markersSearch(self, vol: SisypheVolume, slc: int | None = None) -> bool:
        """
        Leksell fiducial markers detection in a slice.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            PySisyphe volume
        slc : int
            slice index

        Returns
        -------
        bool
            False if no frame or frame detection failed
        """
        if isinstance(vol, SisypheVolume):
            self._trf = None
            self._volume = vol
            self._fidlist.clear()
            try:
                self._markersSearch(slc)
                self._volume.getAcquisition().setFrameToLeksell()
                return True
            except:
                self._volume.getAcquisition().setFrameToNo()
                return False
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def calcTransform(self) -> None:
        """
        Calculate rigid transformation between image and Leksell geometric reference.
        """
        if not self.isEmpty():
            sz = self._volume.getSpacing()[2]
            f = vtkLandmarkTransform()
            f.SetModeToRigidBody()
            n = self._nbfid // 3
            nb = len(self._fidlist) * n
            ref = vtkPoints()
            ref.SetNumberOfPoints(nb)
            mov = vtkPoints()
            mov.SetNumberOfPoints(nb)
            idx = 0
            for fid in self._fidlist:
                # left middle fiducial
                # Leksell coordinate, 195,0 z z
                c = self._fidlist[fid][1]
                d = self._calcDistBetweenFiducials(fid, 0, 1) + 40
                ref.SetPoint(idx, 195, d, d)
                mov.SetPoint(idx, c[0], c[1], fid * sz)
                idx += 1
                # right middle fiducial
                # Leksell coordinate, 5,0 z z
                c = self._fidlist[fid][4]
                d = self._calcDistBetweenFiducials(fid, 4, 5) + 40
                ref.SetPoint(idx, 5, d, d)
                mov.SetPoint(idx, c[0], c[1], fid * sz)
                idx += 1
                if self._nbfid == 9:
                    # anterior middle fiducial
                    # Leksell coordinate, z 215.0 z
                    c = self._fidlist[fid][7]
                    d = self._calcDistBetweenFiducials(fid, 6, 7) + 40
                    ref.SetPoint(idx, d, 215, d)
                    mov.SetPoint(idx, c[0], c[1], fid * sz)
                    idx += 1
            f.SetSourceLandmarks(mov)
            f.SetTargetLandmarks(ref)
            f.Update()
            self._trf = SisypheTransform()
            self._trf.setID('LEKSELL')
            self._trf.setSpacing([1.0, 1.0, 1.0])
            self._trf.setSize([220, 220, 220])
            self._trf.setVTKMatrix4x4(f.GetMatrix())

    # noinspection PyArgumentList
    def calcErrors(self) -> None:
        """
        Calculate errors i.e. euclidean distances between coordinates of the detected fiducial markers and their
        theoretical coordinates in mm.
        """
        if not self.isEmpty() and self.hasTransform():
            sz = self._volume.getSpacing()[2]
            idx = 0
            err = np.zeros(len(self._fidlist) * self._nbfid)
            self._errorlist.clear()
            for fid in self._fidlist:
                self._errorlist[fid] = dict()
                d = 40 + self._calcDistBetweenFiducials(fid, 0, 1)
                p = list(self._fidlist[fid][0])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 195) ** 2 + (c[1] - 40) ** 2)
                self._errorlist[fid][0] = e
                err[idx] = e
                idx += 1
                p = list(self._fidlist[fid][1])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 195) ** 2 + (c[1] - d) ** 2)
                self._errorlist[fid][1] = e
                err[idx] = e
                idx += 1
                p = list(self._fidlist[fid][2])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 195) ** 2 + (c[1] - 160) ** 2)
                self._errorlist[fid][2] = e
                err[idx] = e
                idx += 1
                d = 40 + self._calcDistBetweenFiducials(fid, 4, 5)
                p = list(self._fidlist[fid][3])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 5) ** 2 + (c[1] - 160) ** 2)
                self._errorlist[fid][3] = e
                err[idx] = e
                idx += 1
                p = list(self._fidlist[fid][4])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 5) ** 2 + (c[1] - d) ** 2)
                self._errorlist[fid][4] = e
                err[idx] = e
                idx += 1
                p = list(self._fidlist[fid][5])
                p.append(fid * sz)
                c = self._trf.applyToPoint(p)
                e = sqrt((c[0] - 5) ** 2 + (c[1] - 40) ** 2)
                self._errorlist[fid][5] = e
                err[idx] = e
                idx += 1
                if self._nbfid == 9:
                    d = 40 + self._calcDistBetweenFiducials(fid, 6, 7)
                    p = list(self._fidlist[fid][6])
                    p.append(fid * sz)
                    c = self._trf.applyToPoint(p)
                    e = sqrt((c[0] - 40) ** 2 + (c[1] - 215) ** 2)
                    self._errorlist[fid][6] = e
                    err[idx] = e
                    idx += 1
                    p = list(self._fidlist[fid][7])
                    p.append(fid * sz)
                    c = self._trf.applyToPoint(p)
                    e = sqrt((c[0] - d) ** 2 + (c[1] - 215) ** 2)
                    self._errorlist[fid][7] = e
                    err[idx] = e
                    idx += 1
                    p = list(self._fidlist[fid][8])
                    p.append(fid * sz)
                    c = self._trf.applyToPoint(p)
                    e = sqrt((c[0] - 160) ** 2 + (c[1] - 215) ** 2)
                    self._errorlist[fid][8] = e
                    err[idx] = e
                    idx += 1
            self._errorstats.clear()
            self._errorstats['Mean'] = float(err.mean())
            self._errorstats['RMS'] = float(sqrt(np.sum(np.square(err)) / len(err)))
            self._errorstats['Median'] = float(np.median(err))
            self._errorstats['Std'] = float(err.std())
            self._errorstats['25th'] = float(np.percentile(err, 25))
            self._errorstats['75th'] = float(np.percentile(err, 75))
            self._errorstats['Min'] = float(err.min())
            self._errorstats['Max'] = float(err.max())

    def getErrors(self) -> dict[int, dict[int, float]] | None:
        """
        Get errors i.e. euclidean distances between coordinates of the detected fiducial markers and their theoretical
        coordinates in mm.

        Marker indexes (axial slice):
            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left

        Returns
        -------
        dict[int, dict[int, float]],
            - key int, slice index
            - value dict[int, float]
                - key int, marker index (6 or 9 markers)
                - value float, euclidean distance error in mm
        """
        if not self.isEmpty() and self.hasTransform():
            if len(self._errorlist) == 0: self.calcErrors()
            return self._errorlist
        else: return None

    def hasErrors(self) -> bool:
        """
        Checks whether errors are calculated.

        Returns
        -------
        bool
            True if errors are calculated
        """
        return len(self._errorlist) > 0

    def getErrorStatistics(self) -> dict[str, float]:
        """
        Get errors statistics.

        Returns
        -------
        dict[str, float]
            str keys, float values
                - 'Mean'      mean error
                - 'RMS'       root-mean-square error
                - 'Median'    median error
                - 'Std'       standard deviation error
                - '25th'      first quantile error
                - '75th'      third quantile error
                - 'Min'       minimum error
                - 'Max'       maximum error
        """
        if not self.isEmpty() and self.hasTransform():
            if len(self._errorlist) == 0: self.calcErrors()
            return self._errorstats
        else: raise AttributeError('Error attribute is empty.')

    def addTransformToVolume(self) -> None:
        """
        Add the calculated geometric transformation to the Sisyphe.core.sisypheTransform.SisypheTransforms attribute
        of the processed volume.
        """
        if self.hasVolume():
            if self.hasTransform():
                trfs = self._volume.getTransforms()
                trfs.append(self._trf)
                self._volume.save()
                self.saveToXML(self._volume.getFilename())
            else: raise ValueError('Geometric transformation attribute is empty.')
        else: raise ValueError('Volume attribute is empty.')

    def removeTransformFromVolume(self) -> None:
        """
        remove the calculated geometric transformation from the Sisyphe.core.sisypheTransform.SisypheTransforms
        attribute of the processed volume.
        """
        if self.hasVolume():
            if self.hasTransform():
                trfs = self._volume.getTransforms()
                if 'LEKSELL' in trfs:
                    trfs.remove('LEKSELL')
                    self._volume.saveTransforms()
                self.removeXML(self._volume.getFilename())

    def hasTransform(self) -> bool:
        """
        Checks whether rigid transformation between image and Leksell geometric reference is calculated.

        Returns
        -------
        bool
            True if rigid transformation is calculated
        """
        return self._trf is not None

    def getTransform(self) -> SisypheTransform:
        """
        Get rigid transformation between image and Leksell geometric reference.

        Returns
        -------
        Sisyphe.core.SisypheTransform.SisypheTransform
            rigid transformation
        """
        if self.hasTransform(): return self._trf
        else: raise ValueError('Geometric transformation is not calculated.')

    def getMarker(self, n: int, m: int) -> list[float]:
        """
        Get coordinates of a fiducial marker.

        Marker indexes (axial slice):
            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left

        Parameters
        ----------
        n : int
            slice index
        m : int
            marker index

        Returns
        -------
        list[float]
            x, y, z fiducial marker coordinates
        """
        if isinstance(n, int) and isinstance(m, int):
            if n in self._fidlist:
                if 0 <= m < self._nbfid: return self._fidlist[n][m]
                else: raise IndexError('Wrong marker number, {} is not between 0 and {}.'.format(m, self._nbfid))
            else: raise IndexError('Wrong slice number, no marker in slice {}.'.format(n))
        else: raise TypeError('parameter type {}/{} is not int.'.format(type(n), type(m)))

    def getSliceMarkers(self, n: int) -> dict[int, list[float]]:
        """
        Get coordinates of fiducial markers in a slice.

        Marker indexes (axial slice):
            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left

        Parameters
        ----------
        n : int
            slice index

        Returns
        -------
        dict[int, list[float]]
            - key int, marker index
            - value list[float], x, y, z fiducial marker coordinates
        """
        if not self.isEmpty():
            if isinstance(n, int):
                if n in self._fidlist: return self._fidlist[n]
                else: raise IndexError('Wrong slice number, no marker in slice {}.'.format(n))
            else: raise TypeError('parameter type {} is not int.'.format(type(n)))
        else: raise AttributeError('Fiduciary marker coordinates are not calculated.')

    def getAllMarkers(self) -> dict[int, dict[int, list[float]]]:
        """
        Get all fiducial markers coordinates.

        Marker indexes (axial slice):
            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left

        Returns
        -------
        dict[int, dict[int, list[float]]
            - key int, slice index
            - value dict[int, float]
                - key int, marker index (6 or 9 markers)
                - value list[float, float, float], list of x, y, z fiducial marker coordinates
        """
        return self._fidlist

    def removeSliceMarkers(self, n: int) -> None:
        """
        Removes all fiduciary markers from a slice.

        Parameters
        ----------
        n : int
            slice index
        """
        if n in self._fidlist:
            del self._fidlist[n]

    def removeFrontPlateMarkers(self) -> None:
        """
        Remove front fiducial markers. Six markers configuration, 3 on the left and 3 on the right.

        Marker indexes (axial slice):
            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left
        """
        if self._nbfid == 9:
            for z in self._fidlist:
                del self._fidlist[z][6]
                del self._fidlist[z][7]
                del self._fidlist[z][8]
            self._nbfid = 6

    def getSliceNumbers(self) -> list[int]:
        """
        Get list of valid slice indexes (i.e. slices with at least 6 or 9 fiducial markers depending on configuration).

        Returns
        -------
        list[int]
            list of valid indexes
        """
        return list(self._fidlist.keys())

    def getMarkersCount(self) -> int:
        """
        Get fiducial markers count.

        Two possible configurations:

            - 6: 3 to the left and 3 to the right
            - 9: 3 to the left, 3 to the right, 3 to the front (front markers are optional)

        Marker indexes (axial slice):

            - Left markers: 0 posterior, 1 middle, 2 anterior
            - right markers: 3 anterior, 4 middle, 5 posterior
            - anterior markers: 6 right, 7 middle, 8 left

        Returns
        -------
        bool
            True if slice index is valid (i.e. less than slice count)
        """
        return self._nbfid

    def hasSlice(self, n: int) -> bool:
        """
        Check whether slice index is valid (i.e. it contains at least 6 or 9 fiducial markers depending on
        configuration).

        Returns
        -------
        bool
            True if slice index is valid
        """
        if isinstance(n, int): return n in self._fidlist
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def isEmpty(self) -> bool:
        """
        Check that fiduciary marker coordinates are calculated.

        Returns
        -------
        bool
            True if fiduciary marker coordinates are calculated
        """
        return len(self._fidlist) == 0

    def hasVolume(self) -> bool:
        """
        Check whether PySisyphe volume to process is available.

        Returns
        -------
        bool
            True if PySisyphe volume is defined
        """
        return self._volume is not None

    def setVolume(self, v: SisypheVolume) -> None:
        """
        Set PySisyphe volume to process.

        Parameters
        ----------
        v : Sisyphe.core.sisypheVolume.SisypheVolume
            volume to process
        """
        if isinstance(v, SisypheVolume): self._volume = v
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))

    def getVolume(self) -> SisypheVolume:
        """
        Get PySisyphe volume

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            volume to process
        """
        return self._volume

    def saveToXML(self, filename: str) -> None:
        """
        Save fiducial markers coordinates file (.xfid).

        Parameters
        ----------
        filename : str
            file name (.xfid)
        """
        if not self.isEmpty():
            if isinstance(filename, str):
                path, ext = splitext(filename)
                if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
                doc = minidom.Document()
                root = doc.createElement(self._FILEEXT[1:])
                root.setAttribute('version', '1.0')
                doc.appendChild(root)
                item = doc.createElement('markerscount')
                root.appendChild(item)
                v = doc.createTextNode(str(self._nbfid))
                item.appendChild(v)
                for k1 in self._fidlist:
                    item = doc.createElement('slice')
                    item.setAttribute('index', str(k1))
                    root.appendChild(item)
                    for k2 in self._fidlist[k1]:
                        subitem = doc.createElement('marker')
                        subitem.setAttribute('location', str(k2))
                        item.appendChild(subitem)
                        v = doc.createTextNode(' '.join([str(i) for i in self._fidlist[k1][k2]]))
                        subitem.appendChild(v)
                buff = doc.toprettyxml()
                f = open(filename, 'w')
                try: f.write(buff)
                except IOError: raise IOError('XML file write error.')
                finally: f.close()
            else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    def loadFromXML(self, filename: str) -> None:
        """
        Load fiducial markers coordinates file (.xfid).

        Parameters
        ----------
        filename : str
            file name (.xfid)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != self._FILEEXT: filename = path + self._FILEEXT
            if exists(filename):
                doc = minidom.parse(filename)
                root = doc.documentElement
                if root.nodeName == self._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                    self._fidlist.clear()
                    node = root.getElementsByTagName('markerscount')[0]
                    self._nbfid = int(node.firstChild.data)
                    for node1 in root.getElementsByTagName('slice'):
                        k1 = int(node1.getAttribute('index'))
                        self._fidlist[k1] = dict()
                        for node2 in node1.getElementsByTagName('marker'):
                            k2 = int(node2.getAttribute('location'))
                            buff = node2.firstChild.data
                            buff = buff.split(' ')
                            self._fidlist[k1][k2] = (float(buff[0]), float(buff[1]))
                else: raise IOError('XML file format is not supported.')
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    def hasXML(self, filename: str) -> bool:
        """
        Check that fiducial markers coordinates file (.xfid) exists.

        Parameters
        ----------
        filename : str
            file name, file extension is replaced by .xfid if necessary

        Returns
        -------
        bool
            True if file name exists
        """
        path, ext = splitext(filename)
        return exists(path + self._FILEEXT)

    def removeXML(self, filename: str) -> None:
        """
        Remove fiducial markers coordinates file (.xfid).

        Parameters
        ----------
        filename : str
            file name, file extension is replaced by .xfid if necessary
        """
        path, ext = splitext(filename)
        filename = path + self._FILEEXT
        if exists(filename): remove(filename)
