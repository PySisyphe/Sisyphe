"""
    External packages/modules

        Name            Link                                                        Usage

        matplotlib      https://matplotlib.org/                                     Graph plot library
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        vtk             https://vtk.org/                                            Visualization
"""

from __future__ import annotations

from os import stat

from os.path import abspath
from os.path import exists
from os.path import join
from os.path import dirname
from os.path import basename
from os.path import splitext

from xml.dom import minidom

from numpy import frombuffer
from numpy import interp
from numpy import uint8
from numpy import ndarray
from numpy import array as np_array
from numpy import ndarray as np_ndarray

from matplotlib.cm import get_cmap
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap

from PyQt5.QtGui import QColor
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPainter

from vtk import vtkLookupTable
from vtk import vtkColorTransferFunction
from vtk import vtkPiecewiseFunction

import Sisyphe.core as sc
from Sisyphe.core.sisypheConstants import getLutExt

__all__ = ['lutConversion',
           'saveColormapBitmapPreview',
           'SisypheLut',
           'SisypheColorTransfer']

"""

    Function
    
        lutConversion
        saveColormapBitmapPreview
"""

def lutConversion(filenames: str | list[str], out: str = 'xlut') -> None:
    out = '.{}'.format(out)
    if out in ('.lut', '.xlut', '.olt', '.txt'):
        if isinstance(filenames, str): filenames = [filenames]
        for filename in filenames:
            base, ext = splitext(filename)
            ext = ext.lower()
            if ext != out:
                lut = SisypheLut()
                if ext == '.lut': lut.load(filename)
                elif ext == '.xlut': lut.loadFromXML(filename)
                elif ext == '.olt': lut.loadFromOlt(filename)
                elif ext == '.txt': lut.loadFromTxt(filename)
                else: raise IOError('{} format is not supported.'.format(ext))
                filename = base + out
                if out == '.lut': lut.save(filename)
                elif out == '.xlut': lut.saveToXML(filename)
                elif out == '.olt': lut.saveToOlt(filename)
                elif out == '.txt': lut.saveToTxt(filename)
    else: raise ValueError('format of conversion {} is not supported.'.format(out))

def saveColormapBitmapPreview(filenames: str | list[str], format: str = 'jpg') -> None:
    if format in ('bmp', 'jpg', 'png'):
        if isinstance(filenames, str): filenames = [filenames]
        for filename in filenames:
            lut = SisypheLut()
            ext = splitext(filename)[1].lower()
            if ext == '.lut': lut.load(filename)
            elif ext == '.xlut': lut.loadFromXML(filename)
            elif ext == '.olt': lut.loadFromOlt(filename)
            elif ext == '.txt': lut.loadFromTxt(filename)
            else: raise IOError('{} format is not supported.'.format(ext))
            lut.saveBitmapPreview(256, 32, format)
    else: raise ValueError('{} format is not supported'.format(format))

"""
    Classes
    
        SisypheLut
        SisypheColorTransfer
"""

tupleInt4 = tuple[int, int, int, int]
tupleFloat4 = tuple[float, float, float, float]
listFloat4 = list[float, float, float, float]

class SisypheLut(object):
    """
        SisypheLut Class

        Inheritance

            object -> SisypheLut

        Private attributes

            _name       str, lut name (internal functype) or filename (file functype)
            _typeLUT    int, lut functype (default, internal, file or custom)
            _vtklut     vtkLookupTable

        Class methods

            str = getFileExt()
            str = getFilterExt()
            list of str = getColormapList()
            list of str = getColormapName(str)

        Public methods

            SisypheLut = copy()
            copyFrom(SisypheLut)
            list = copyToList()
            copyFromList(list)
            ndarray = copyToNumpy()
            copyFromNumpy(ndarray)
            ListedColormap = copyToMatplotlibColormap()
            copyFromMatplotlibColormap(ListedColormap)
            bool = isEqual()
            setDefaultLut()
            setInternalLut()
            setLutToAutumn()
            setLutToCool()
            setLutToGNU()
            setLutToGNU2()
            setLutToHeat()
            setLutToHot()
            setLutToJet()
            setLutToSpectral()
            setLutSpring()
            setLutToSummer()
            setLutToRainbow()
            setLutToWinter()
            bool = isDefaultLut()
            bool = isInternalLut()
            bool = isFileLut()
            bool = isCustomLut()
            str = getFilename()
            int = getLUTType()
            str = getName()
            setDisplayBelowRangeColorOff()
            setDisplayBelowRangeColorOn()
            vtkLookupTable = getvtkLookupTable()
            setvtkLookupTable(vtkLookupTable)
            setColor(int, float, float, float, float)
            setQColor(int, QColor)
            setIntColor(int, int, int, int)
            float, float, float, float = getColor(int)
            QColor = getQColor(int)
            int, int, int, int = getIntColor(int)
            bool = isSameColor()
            QImage = getBitmapPreview(width: int, height: int)
            saveBitmapPreview(width: int, height: int, format: str = 'jpg')
            float, float = getWindowRange()
            setWindowRange(float, float)
            saveToTxt(str)
            saveToXML(str)
            save(str)
            loadFromTxt(str)
            loadFromOlt(str)    BrainVoyager lut format
            loadFromXML(str)
            load(str)

        Creation: 07/11/2022
        Revisions:

            20/07/2023  added new IO loadFromOlt method, loading brainvoyager lut (*.olt)
            24/08/2023  copyFrom() method, parameter type extension to SisypheVolume and SisypheDisplay
            24/08/2023  copyFrom() and copy() methods, copy of windowing range attributes
            29/08/2023  type hinting
            31/10/2023  add openLut() class method
                        add openColorTransfer() class method
            03/11/2023  loadFromOlt() method bugfix, remove multiple spaces between numeric chars
                        add getBitmapPreview() method
                        add saveBitmapPreview() method
    """
    __slots__ = ['_vtklut', '_name', '_typeLUT']

    # Class constants

    _COLORMAPS = ['gray', 'gray_r', 'autumn', 'cool', 'gnuplot', 'gnuplot2', 'gist_heat', 'gist_ncar',
                  'hot', 'hsv', 'jet', 'nipy_spectral', 'spring', 'summer', 'rainbow', 'winter', 'Wistia']

    _COLORMAPSNAME = {'gray': 'gray', 'gray_r': 'grayinv',
                      'autumn': 'autumn', 'cool': 'cool',
                      'gnuplot': 'gnu1', 'gnuplot2': 'gnu2',
                      'gist_heat': 'heat', 'gist_ncar': 'ncar',
                      'hot': 'hot', 'hsv': 'hsv',
                      'jet': 'jet', 'nipy_spectral': 'spectral',
                      'spring': 'spring', 'summer': 'summer',
                      'rainbow': 'rainbow', 'winter': 'winter',
                      'Wistia': 'wistia'}

    _LUTTOCODE = {'default': 0, 'internal': 1, 'file': 2, 'custom': 3}
    _CODETOLUT = {0: 'default', 1: 'internal', 2: 'file', 3: 'custom'}
    _FILEEXT = '.xlut'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe LUT (*{})'.format(cls._FILEEXT)

    @classmethod
    def getDefaultLutDirectory(cls) -> str:
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'lut')

    @classmethod
    def getColormapList(cls) -> list[str]:
        return cls._COLORMAPS

    @classmethod
    def getColormapFromName(cls, name: str) -> str:
        return cls. _COLORMAPSNAME[name]

    @classmethod
    def openLut(cls, filename: str) -> SisypheLut:
        if exists(filename):
            _, ext = splitext(filename)
            lut = SisypheLut()
            ext = ext.lower()
            if ext == cls.getFileExt(): lut.loadFromXML(filename)
            elif ext == '.lut': lut.load(filename)
            elif ext == '.txt': lut.loadFromTxt(filename)
            elif ext == '.olt': lut.loadFromOlt(filename)
            else: raise IOError('{} format is not supported.'.format(ext))
            return lut

    # Special methods

    def __init__(self, name: str | None = None) -> None:
        self._vtklut = vtkLookupTable()
        self._vtklut.SetNumberOfTableValues(256)
        self._vtklut.SetNanColor(0.0, 0.0, 0.0, 0.0)
        self._vtklut.SetBelowRangeColor(0.0, 0.0, 0.0, 0.0)
        self._vtklut.UseBelowRangeColorOn()
        if name is not None and isinstance(name, str):
            if name in self._COLORMAPS:
                self._name = name
                self._typeLUT = self._LUTTOCODE['internal']
                self.setInternalLut(name)
            elif exists(name):
                path, ext = splitext(name)
                if ext in getLutExt() + ['.txt']:
                    if ext == '.lut':
                        self.load(name)
                    elif ext == '.xlut':
                        self.loadFromXML(name)
                    elif ext == '.txt':
                        self.loadFromTxt(name)
                    self._name = name
                else:
                    self.setDefaultLut()
            else:
                self.setDefaultLut()
        else:
            self.setDefaultLut()

    def __str__(self) -> str:
        buff = '{}\n{}\n'.format(self._name, self.getLUTType(True))
        for i in range(0, 256):
            rgba = self._vtklut.GetTableValue(i)
            rgba = [int(j * 255.0) for j in rgba]
            buff += '{} r: {} g: {} b: {} a: {}\n'.format(i, rgba[0], rgba[1], rgba[2], rgba[3])
        return buff

    def __repr__(self) -> str:
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    def __len__(self) -> int:
        return 255

    def __getitem__(self, i: int) -> tupleFloat4:
        if 0 <= i <= 255: return self._vtklut.GetTableValue(i)
        else: raise KeyError('invalid key index')

    def __setitem__(self, i: int, v: tupleFloat4 | listFloat4) -> None:
        if 0 <= i <= 255: self._vtklut.SetTableValue(i, v)
        else: raise KeyError('invalid key index')

    def __contains__(self, v: tupleFloat4 | listFloat4) -> bool:
        for i in range(0, 256):
            if self.isSameColor(i, v):
                return True
        return False

    def __eq__(self, buff: SisypheLut) -> bool:
        return self.isEqual(buff)

    # Public methods

    def copy(self) -> SisypheLut:
        buff = SisypheLut()
        buff._name = self._name
        buff._typeLUT = self._typeLUT
        for i in range(0, 256):
            buff._vtklut.SetTableValue(i, self._vtklut.GetTableValue(i))
        buff._vtklut.SetUseBelowRangeColor(self._vtklut.GetUseBelowRangeColor())
        w1, w2 = self.getWindowRange()
        buff.setWindowRange(w1, w2)
        return buff

    def copyFrom(self, buff: SisypheLut) -> None:
        from Sisyphe.core.sisypheVolume import SisypheVolume
        from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
        if isinstance(buff, SisypheVolume): buff = buff.display.getLUT()
        elif isinstance(buff, SisypheDisplay): buff = buff.getLUT()
        if isinstance(buff, SisypheLut):
            self._name = buff._name
            self._typeLUT = buff._typeLUT
            for i in range(0, 256):
                self._vtklut.SetTableValue(i, buff._vtklut.GetTableValue(i))
            self._vtklut.SetUseBelowRangeColor(buff._vtklut.GetUseBelowRangeColor())
            w1, w2 = buff.getWindowRange()
            self.setWindowRange(w1, w2)
        else: raise TypeError('parameter functype is not {}.'.format(self.__class__.__name__))

    def copyToList(self) -> list[listFloat4]:
        clist = []
        for i in range(0, 256):
            v = self._vtklut.GetTableValue(i)
            clist.append(list(v))
        return clist

    def copyFromList(self, clist: list[listFloat4]) -> None:
        if isinstance(clist, list):
            self._name = 'from list'
            self._typeLUT = self._LUTTOCODE['custom']
            for i in range(0, 256):
                v = clist[i]
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter {} type is not list.'.format(type(clist)))

    def copyToNumpy(self) -> np_ndarray:
        return np_array(self.copyToList())

    def copyFromNumpy(self, cnp: np_ndarray) -> None:
        if isinstance(cnp, np_ndarray):
            self._name = 'from numpy'
            self._typeLUT = self._LUTTOCODE['custom']
            for i in range(0, 256):
                v = cnp[i, :]
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter type {} is not a numpy.ndarray.'.format(type(cnp)))

    def copyToMatplotlibColormap(self) -> ListedColormap:
        cmap = ListedColormap(self.copyToList(), self._name, 256)
        cmap.set_over(cmap(255))
        cmap.set_under(cmap(0))
        return cmap

    def copyFromMatplotlibColormap(self, cmap: ListedColormap | LinearSegmentedColormap) -> None:
        if isinstance(cmap, (ListedColormap, LinearSegmentedColormap)):
            self._name = cmap.name
            self._typeLUT = self._LUTTOCODE['internal']
            for i in range(0, 256):
                v = cmap(i / 255)
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter type {} is not a matplotlib colormap.'.format(type(cmap)))

    def isEqual(self, buff: ListedColormap | LinearSegmentedColormap | SisypheLut) -> bool:
        if isinstance(buff, SisypheLut):
            for i in range(0, 256):
                if buff[i] != self.__getitem__(i):
                    return False
            return True
        elif isinstance(buff, (ListedColormap, LinearSegmentedColormap)):
            for i in range(0, 256):
                if buff(i) != self.__getitem__(i):
                    return False
            return True
        else:
            raise TypeError('parameter functype is not Matplotlib colormap or SisypheLut.')

    def setDefaultLut(self) -> None:
        self._name = 'gray'
        self._typeLUT = self._LUTTOCODE['default']
        for i in range(0, 256):
            v = float(i) / 255.0
            self._vtklut.SetTableValue(i, v, v, v, 1.0)

    def setInternalLut(self, name: str) -> None:
        if isinstance(name, str):
            if name == 'gray':
                self.setDefaultLut()
            elif name in self._COLORMAPS:
                cmap = get_cmap(name, 256)
                self._name = name
                self._typeLUT = self._LUTTOCODE['internal']
                for i in range(0, 256):
                    v = cmap(i / 255)
                    self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
            else:
                raise ValueError('{} is not a predefined Lut.'.format(name))
        else:
            raise TypeError('parameter functype is not str.')

    def setLutToAutumn(self) -> None:
        self.setInternalLut(self._COLORMAPS[2])

    def setLutToCool(self) -> None:
        self.setInternalLut(self._COLORMAPS[3])

    def setLutToGNU(self) -> None:
        self.setInternalLut(self._COLORMAPS[4])

    def setLutToGNU2(self) -> None:
        self.setInternalLut(self._COLORMAPS[5])

    def setLutToHeat(self) -> None:
        self.setInternalLut(self._COLORMAPS[6])

    def setLutToHot(self) -> None:
        self.setInternalLut(self._COLORMAPS[8])

    def setLutToJet(self) -> None:
        self.setInternalLut(self._COLORMAPS[10])

    def setLutToSpectral(self) -> None:
        self.setInternalLut(self._COLORMAPS[11])

    def setLutSpring(self) -> None:
        self.setInternalLut(self._COLORMAPS[12])

    def setLutToSummer(self) -> None:
        self.setInternalLut(self._COLORMAPS[13])

    def setLutToRainbow(self) -> None:
        self.setInternalLut(self._COLORMAPS[14])

    def setLutToWinter(self) -> None:
        self.setInternalLut(self._COLORMAPS[15])

    def isDefaultLut(self) -> bool:
        return self._typeLUT == self._LUTTOCODE['default']

    def isInternalLut(self) -> bool:
        return self._typeLUT == self._LUTTOCODE['internal']

    def isFileLut(self) -> bool:
        return self._typeLUT == self._LUTTOCODE['file']

    def isCustomLut(self) -> bool:
        return self._typeLUT == self._LUTTOCODE['custom']

    def getFilename(self) -> str | None:
        if self._typeLUT == self._LUTTOCODE['file'] and exists(self._name): return self._name
        else: return None

    def getLUTType(self, string: bool = True) -> str | int:
        if string: return self._CODETOLUT[self._typeLUT]
        else: return self._typeLUT

    def getName(self) -> str:
        if self._typeLUT == self._LUTTOCODE['file']: return splitext(basename(self._name))[0]
        else: return self._name

    def setDisplayBelowRangeColorOff(self) -> None:
        self._vtklut.UseBelowRangeColorOff()

    def setDisplayBelowRangeColorOn(self) -> None:
        self._vtklut.SetBelowRangeColor(0.0, 0.0, 0.0, 0.0)
        self._vtklut.UseBelowRangeColorOn()

    def getvtkLookupTable(self) -> vtkLookupTable:
        return self._vtklut

    def setvtkLookupTable(self, vtklut: vtkLookupTable) -> None:
        if isinstance(vtklut, vtkLookupTable):
            self._vtklut = vtklut
        else: raise TypeError('parameter type {} is not vtkLookupTable.'.format(type(vtklut)))

    def setColor(self, i: int, r: float, g: float, b: float, a: float = 1.0) -> None:
        if 0 <= i <= 255: self._vtklut.SetTableValue(i, r, g, b, a)
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def setQColor(self, i: int, c: QColor) -> None:
        self.setColor(i, c.redF(), c.greenF(), c.blueF())

    def setIntColor(self, i: int, r: int, g: int, b: int, a: int = 255):
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0
        a = a / 255.0
        self.setColor(i, r, g, b,a)

    def getColor(self, i: int) -> tupleFloat4:
        if 0 <= i <= 255: return self._vtklut.GetTableValue(i)
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def getQColor(self, i: int) -> QColor:
        rgba = self._vtklut.GetTableValue(i)
        c = QColor()
        c.setRedF(rgba[0])
        c.setGreenF(rgba[1])
        c.setBlueF(rgba[2])
        return c

    def getIntColor(self, i: int) -> tupleInt4:
        if 0 <= i <= 255:
            r, g, b, a = self._vtklut.GetTableValue(i)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            a = int(a * 255)
            return r, g, b, a
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def getWindowRange(self) -> tuple[float, float]:
        return self._vtklut.GetTableRange()

    def setWindowRange(self, w1: float, w2: float) -> None:
        self._vtklut.SetTableRange(w1, w2)

    def isSameColor(self, i: int, c: tupleFloat4 | listFloat4 | QColor) -> bool:
        if isinstance(c, QColor): c = (c.redF(), c.greenF(), c.blueF(), c.alphaF())
        return self._vtklut.GetTableValue(i) == c

    def getBitmapPreview(self, width: int, height: int) -> QImage:
        img = QImage(256, height, QImage.Format_ARGB32)
        paint = QPainter(img)
        for i in range(256):
            paint.setPen(self.getQColor(i))
            paint.drawLine(i, 0, i, height-1)
        if width != 256: img = img.scaledToWidth(width)
        return img

    def saveBitmapPreview(self, width: int, height: int, format: str = 'jpg') -> None:
        img = self.getBitmapPreview(width, height)
        if format in ('bmp', 'jpg', 'png'):
            filename = '{}.{}'.format(self.getName(), format)
            img.save(filename)
        else: raise ValueError('{} format is not supported'.format(format))

    def saveToTxt(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != '.txt':
            filename = path + '.txt'
        f = open(filename, 'w')
        try:
            for i in range(0, 256):
                rgba = self._vtklut.GetTableValue(i)
                rgba = [str(int(j * 255.0)) for j in rgba]
                rgba = ' '.join(rgba) + '\n'
                f.write(rgba)
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            print('write error.')
        finally:
            f.close()

    def saveToXML(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != SisypheLut._FILEEXT:
            filename = path + SisypheLut._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(SisypheLut._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        for i in range(0, 256):
            rgba = self._vtklut.GetTableValue(i)
            rgba = [str(int(j * 255.0)) for j in rgba]
            rgba = ' '.join(rgba)
            node = doc.createElement('color')
            node.setAttribute('index', str(i))
            root.appendChild(node)
            txt = doc.createTextNode(rgba)
            node.appendChild(txt)
        doc.appendChild(root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try:
            f.write(buff)
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('XML write error.')
        finally:
            f.close()

    def save(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != '.lut':
            filename = path + '.lut'
        f = open(filename, 'wb')
        try:
            rgba = self.copyToNumpy() * 255
            rv = rgba[:, 0].astype(uint8).tobytes()
            gv = rgba[:, 1].astype(uint8).tobytes()
            bv = rgba[:, 2].astype(uint8).tobytes()
            f.write(rv)  # red, vector of 256 values
            f.write(gv)  # green, vector of 256 values
            f.write(bv)  # blue, vector of 256 values
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('write error.')
        finally:
            f.close()

    def loadFromOlt(self, filename: str) -> None:
        filename = abspath(filename)
        path, ext = splitext(filename)
        if ext.lower() != '.olt':
            filename = path + '.olt'
            if not exists(filename):
                raise IOError('No such file {}.'.format(filename))
        f = open(filename, 'r')
        try:
            r20 = list()
            g20 = list()
            b20 = list()
            xp = list()
            n = 20
            step = 1 / (n - 1)
            for i in range(0, 20):
                buff = f.readline()
                v = buff.split(' ')
                v = [i for i in v if i != '']
                r20.append(float(v[1]) / 255.0)
                g20.append(float(v[2]) / 255.0)
                b20.append(float(v[3]) / 255.0)
                xp.append(i * step)
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('read error.')
        finally:
            f.close()
        x = [i / 255 for i in range(256)]
        r256 = interp(x, xp, r20)
        g256 = interp(x, xp, g20)
        b256 = interp(x, xp, b20)
        for i in range(256):
            self._vtklut.SetTableValue(i, r256[i], g256[i], b256[i], 1.0)

    def loadFromTxt(self, filename: str) -> None:
        filename = abspath(filename)
        path, ext = splitext(filename)
        if ext.lower() != '.txt':
            filename = path + '.txt'
            if not exists(filename):
                raise IOError('No such file {}.'.format(filename))
        f = open(filename, 'r')
        try:
            for i in range(0, 256):
                buff = f.readline()
                rgba = buff.split(' ')
                rgba = [(float(j) / 255.0) for j in rgba]
                self._vtklut.SetTableValue(i, rgba[0], rgba[1], rgba[2], rgba[3])
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('read error.')
        finally:
            f.close()

    def loadFromXML(self, filename: str) -> None:
        filename = abspath(filename)
        path, ext = splitext(filename)
        if ext.lower() != SisypheLut._FILEEXT:
            filename = path + SisypheLut._FILEEXT
            if not exists(filename):
                raise IOError('No such file {}.'.format(filename))
        try:
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == SisypheLut._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                node = root.firstChild
                while node:
                    # Alternation of TEXT_NODE and ELEMENT_NODE
                    if node.nodeType == 1:  # ELEMENT_NODE
                        if node.nodeName == 'color':
                            idx = int(node.getAttribute('index'))
                            buff = node.firstChild.data
                            rgba = buff.split(' ')
                            rgba = [(float(j) / 255.0) for j in rgba]
                            self._vtklut.SetTableValue(idx, rgba[0], rgba[1], rgba[2], rgba[3])
                    node = node.nextSibling
            else: raise IOError('XML format is not supported.')
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('XML read error.')

    def load(self, filename: str) -> None:
        filename = abspath(filename)
        path, ext = splitext(filename)
        if ext.lower() != '.lut':
            filename = path + '.lut'
            if not exists(filename):
                raise IOError('No such file {}.'.format(filename))
        f = open(filename, 'rb')
        try:
            info = stat(filename)
            if info.st_size == 1024:
                rv = f.read(256)
                gv = f.read(256)
                bv = f.read(256)
                av = f.read(256)
                rv = frombuffer(rv, dtype=uint8)
                gv = frombuffer(gv, dtype=uint8)
                bv = frombuffer(bv, dtype=uint8)
                av = frombuffer(av, dtype=uint8)
                for i in range(0, 256):
                    self._vtklut.SetTableValue(i, rv[i] / 255.0, gv[i] / 255.0, bv[i] / 255.0, av[i] / 255.0)
            elif info.st_size == 768:
                rv = f.read(256)
                gv = f.read(256)
                bv = f.read(256)
                rv = frombuffer(rv, dtype=uint8)
                gv = frombuffer(gv, dtype=uint8)
                bv = frombuffer(bv, dtype=uint8)
                for i in range(0, 256):
                    self._vtklut.SetTableValue(i, rv[i] / 255.0, gv[i] / 255.0, bv[i] / 255.0, 1.0)
            else:
                raise IOError('{} is not a LUT file.'.format(filename))
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError:
            raise IOError('read error.')
        finally:
            f.close()


class SisypheColorTransfer(object):
    """
        SisypheColorTransfer class

        Inheritance

            object -> SisypheColorTransfer

        Private attributes

            _ID                 str
            _colortransfer      vtkColorTransferFunction
            _alphatransfer      vtkPiecewiseFunction
            _gradienttransfer   vtkPiecewiseFunction

        Public methods

            str = getID()
            setID(str)
            bool = hasSameID()
            bool = hasID()
            bool = isEmpty()
            bool = isColorTransferEmpty()
            bool= isAlphaTransferEmpty()
            bool= isGradientTransferEmpty()
            setDefault()
            setDefaultColor()
            setDefaultAlpha()
            setDefaultGradient()
            init()
            vtkColorTransferFunction = getColorTransfer()
            vtkPiecewiseFunction = getAlphaTransfer()
            vtkPiecewiseFunction = getGradientTransfer()
            setColorTransfer(vtkColorTransferFunction)
            setAlphaTransfer(vtkPiecewiseFunction)
            setGradientTransfer(vtkPiecewiseFunction)
            addColorTransferElement(v= float, r=float, g=float, b=float or vrgb=list(float, float, float, float))
            addAlphaTransferElement(v= float, a=float or va=list(float, float))
            addGradientTransferElement(v= float, a=float or va=list(float, float))
            list = getColorTransferElement(int)
            list = getAlphaTransferElement(int)
            list = getGradientTransferElement(int)
            setColorTransferElement(index=int, r=float, g=float, b=float or vrgb=list(float, float, float))
            setAlphaTransferElement(index=int, v=float, a=float)
            setGradientTransferElement(index=int, v=float, a=float)
            removeColorTransferElement(index=int or v=list(float, float, float))
            removeAlphaTransferElement(index=int or v=float)
            removeGradientTransferElement(index=int or v=float)
            int = getColorTransferSize()
            int = getAlphaTransferSize()
            int = getGradientTransferSize()
            clear()
            clearColorTransfer()
            clearAlphaTransfer()
            clearGradientTransfer()
            SisypheColorTransfer = copy()
            copyFrom(SisypheColorTransfer)
            dict = copyToDict()
            copyFromDict(dict)
            list = copyToList()
            copyFromList(list)
            numpy array = copyToNumpy()
            copyFromNumpy(numpy array)
            bool = isSameColorTransfer()
            bool = isSameAlphaTransfer()
            bool = isSameGradientTransfer()
            bool = hasColorElement()
            bool = hasAlphaElement()
            bool = hasGradientElement()
            bool = hasColorTransferValue()
            bool = hasAlphaTransferValue()
            bool = hasGradientTransferValue()
            getValueFromColor(r, g, b or rgb=list(float ,float, float))
            list(r, g, b) = getColorFromValue()
            float = getValueFromAlpha(float)
            float = getAlphaFromValue(float)
            float = getValueFromGradient(float)
            float = getGradientFromValue(float)
            bool = isEqual()
            float, float = getRange()
            saveToXML()
            loadFromXML()

        Creation: 07/11/2022
        Revision:

            29/08/2023  type hinting
    """
    __slots__ = ['_ID', '_colortransfer', '_alphatransfer', '_gradienttransfer']

    # Class constants

    _FILEEXT = '.xtfer'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        return 'PySisyphe Color Transfer (*{})'.format(cls._FILEEXT)

    @classmethod
    def openColorTransfer(cls, filename: str) -> SisypheColorTransfer:
        filename = basename(filename) + '.xtfer'
        ct = SisypheColorTransfer()
        ct.loadFromXML(filename)
        return ct

    # Special methods

    def __init__(self) -> None:
        self._ID = None
        self._colortransfer = vtkColorTransferFunction()
        self._alphatransfer = vtkPiecewiseFunction()
        self._gradienttransfer = vtkPiecewiseFunction()

    def __str__(self) -> str:
        if self.isEmpty():
            return 'Empty'
        else:
            buff = 'ID: {}\n'.format(self._ID)
            # color transfer
            buff += 'Color transfer:\n'
            if self._colortransfer.GetSize() > 0:
                for i in range(0, self._colortransfer.GetSize()):
                    rgb = self.getColorTransferElement(i)
                    v = rgb[0]
                    rgb = rgb[1:4]
                    rgb = [int(j * 255.0) for j in rgb]
                    buff += '{} v: {} r: {} g: {} b: {}\n'.format(i, v, rgb[0], rgb[1], rgb[2])
            else:
                buff += 'Empty\n'
            # alpha transfer
            buff += 'Alpha transfer:\n'
            if self._alphatransfer.GetSize() > 0:
                for i in range(0, self._alphatransfer.GetSize()):
                    va = self.getAlphaTransferElement(i)
                    buff += '{} v: {} a: {}\n'.format(i, va[0], int(va[1] * 255))
            else:
                buff += 'Empty\n'
            # gradient transfer
            buff += 'Gradient transfer:\n'
            if self._gradienttransfer.GetSize() > 0:
                for i in range(0, self._gradienttransfer.GetSize()):
                    va = self.getGradientTransferElement(i)
                    buff += '{} v: {} g: {}\n'.format(i, va[0], int(va[1] * 255))
            else:
                buff += 'Empty\n'
            return buff

    def __repr__(self) -> str:
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    def __eq__(self, buff) -> bool:
        return self.isEqual(buff)

    # Public methods

    def isEmpty(self) -> bool:
        return self.getColorTransferSize() == 0 and \
               self.getAlphaTransferSize() == 0 and \
               self.getGradientTransferSize() == 0

    def isColorTransferEmpty(self) -> bool:
        return self.getColorTransferSize() == 0

    def isAlphaTransferEmpty(self) -> bool:
        return self.getAlphaTransferSize() == 0

    def isGradientTransferEmpty(self) -> bool:
        return self.getGradientTransferSize() == 0

    def setDefault(self, volume: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(volume, sc.sisypheVolume.SisypheVolume):
            self.setDefaultColor(volume)
            self.setDefaultAlpha(volume)
            self.setDefaultGradient(volume)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultColor(self, volume: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(volume, sc.sisypheVolume.SisypheVolume):
            self.setID(volume.getArrayID())
            self.addColorTransferElement(v=volume.display.getRangeMin(), r=0.0, g=0.0, b=0.0)
            self.addColorTransferElement(v=volume.display.getRangeMax(), r=1.0, g=1.0, b=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultAlpha(self, volume: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(volume, sc.sisypheVolume.SisypheVolume):
            self.setID(volume.getArrayID())
            self.addAlphaTransferElement(v=volume.display.getRangeMin(), a=0.0)
            self.addAlphaTransferElement(v=volume.display.getRangeMax(), a=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultGradient(self, volume: sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(volume, sc.sisypheVolume.SisypheVolume):
            self.setID(volume.getArrayID())
            self.addGradientTransferElement(v=0.0, a=0.0)
            self.addGradientTransferElement(v=volume.display.getRangeMax() - volume.display.getRangeMin(), a=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def init(self) -> None:
        self.addColorTransferElement(v=0, r=0.0, g=0.0, b=0.0)
        self.addColorTransferElement(v=1, r=1.0, g=1.0, b=1.0)
        self.addAlphaTransferElement(v=0, a=0.0)
        self.addAlphaTransferElement(v=1, a=1.0)
        self.addGradientTransferElement(v=0, a=0.0)
        self.addGradientTransferElement(v=1, a=1.0)

    def getID(self) -> str:
        return self._ID

    def setID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> None:
        if isinstance(ID, str): self._ID = ID
        elif isinstance(ID, sc.sisypheVolume.SisypheVolume): self._ID = ID.getArrayID()
        else: raise TypeError('parameter type {} is not str, SisypheImage or SisypheVolume.'.format(type(ID)))

    def hasSameID(self, ID: str | sc.sisypheVolume.SisypheVolume) -> bool:
        if self._ID is None: return False
        else:
            if isinstance(ID, sc.sisypheVolume.SisypheVolume): return self._ID == ID.getArrayID()
            elif isinstance(ID, str): return self._ID == ID

    def hasID(self) -> bool:
        return self._ID is not None

    def getColorTransfer(self) -> vtkColorTransferFunction:
        return self._colortransfer

    def getAlphaTransfer(self) -> vtkPiecewiseFunction:
        return self._alphatransfer

    def getGradientTransfer(self) -> vtkPiecewiseFunction:
        return self._gradienttransfer

    def setColorTransfer(self, colortransfer: vtkColorTransferFunction) -> None:
        if isinstance(colortransfer, vtkColorTransferFunction):
            self._colortransfer = colortransfer
        else: raise TypeError('parameter type {} is not vtkColorTransferFunction.'.format(type(colortransfer)))

    def setAlphaTransfer(self, alphatransfer: vtkPiecewiseFunction) -> None:
        if isinstance(alphatransfer, vtkPiecewiseFunction):
            self._alphatransfer = alphatransfer
        else: raise TypeError('parameter type {} is not vtkPiecewiseFunction.'.format(type(alphatransfer)))

    def setGradientTransfer(self, gradienttransfer: vtkPiecewiseFunction) -> None:
        if isinstance(gradienttransfer, vtkPiecewiseFunction):
            self._gradienttransfer = gradienttransfer
        else: raise TypeError('parameter type {} is not vtkPiecewiseFunction.'.format(type(gradienttransfer)))

    def addColorTransferElement(self,
                                v: float | None = None,
                                r: float | None = None,
                                g: float | None = None,
                                b: float | None = None,
                                vrgb: tupleFloat4 | listFloat4 | None = None) -> None:
        if vrgb is not None:
            v = vrgb[0]
            r = vrgb[1]
            g = vrgb[2]
            b = vrgb[3]
        self._colortransfer.AddRGBPoint(v, r, g, b)

    def addAlphaTransferElement(self,
                                v: float | None = None,
                                a: float | None = None,
                                va: tuple[float, float] | list[float, float] | None = None) -> None:
        if va is not None:
            v = va[0]
            a = va[1]
        self._alphatransfer.AddPoint(v, a)

    def addGradientTransferElement(self,
                                   v: float | None = None,
                                   a: float | None = None,
                                   va: tuple[float, float] | list[float, float] | None = None) -> None:
        if va is not None:
            v = va[0]
            a = va[1]
        self._gradienttransfer.AddPoint(v, a)

    def getColorTransferElement(self, index: int) -> listFloat4:
        vrgb = [0.0] * 6
        self._colortransfer.GetNodeValue(index, vrgb)
        return vrgb[:4]  # v, r, g, b, m, separator

    def getAlphaTransferElement(self, index: int) -> list[float, float]:
        va = [0.0] * 4
        self._alphatransfer.GetNodeValue(index, va)
        return va[:2]  # v, a, m, separator

    def getGradientTransferElement(self, index: int) -> list[float, float]:
        va = [0.0] * 4
        self._gradienttransfer.GetNodeValue(index, va)
        return va[:2]  # v, a, m, separator

    def setColorTransferElement(self,
                                index: int | None = None,
                                v: float | None = None,
                                r: float | None = None,
                                g: float | None = None,
                                b: float | None = None,
                                vrgb: listFloat4 | tupleFloat4 | None = None) -> None:
        if vrgb is not None:
            v = vrgb[0]
            r = vrgb[1]
            g = vrgb[2]
            b = vrgb[3]
        if index is None:
            index = self.hasColorTransferValue(v)
        if index is not None and index < self.getColorTransferSize():
            self._colortransfer.SetNodeValue(index, v, r, g, b, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def setAlphaTransferElement(self,
                                index: int | None = None,
                                v: float | None = None,
                                a: float | None = None,
                                va: list[float, float] | tuple[float, float] | None = None) -> None:
        if va is not None:
            v = va[0]
            a = va[1]
        if index is None:
            index = self.hasAlphaTransferValue(v)
        if index is not None and index < self.getAlphaTransferSize():
            self._alphatransfer.SetNodeValue(index, v, a, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def setGradientTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None,
                                   a: float | None = None,
                                   va: list[float, float] | tuple[float, float] | None = None) -> None:
        if va is not None:
            v = va[0]
            a = va[1]
        if index is None:
            index = self.hasGradientTransferValue(v)
        if index is not None and index < self.getGradientTransferSize():
            self._gradienttransfer.SetNodeValue(index, v, a, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def removeColorTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None) -> None:
        if v is None:
            if index < self.getColorTransferSize():
                vrgb = self.getColorTransferElement(index)
                v = vrgb[0]
            else: raise IndexError('index parameter is out of range.')
        self._colortransfer.RemovePoint(v)

    def removeAlphaTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None) -> None:
        if v is None:
            if index < self.getAlphaTransferSize():
                va = self.getAlphaTransferElement(index)
                v = va[0]
            else: raise IndexError('index parameter is out of range.')
        self._alphatransfer.RemovePoint(v)

    def removeGradientTransferElement(self,
                                      index: int | None = None,
                                      v=None) -> None:
        if v is None:
            if index < self.getGradientTransferSize():
                va = self.getGradientTransferElement(index)
                v = va[0]
            else: raise IndexError('index parameter is out of range.')
        self._gradienttransfer.RemovePoint(v)

    def getColorTransferSize(self) -> int:
        return self._colortransfer.GetSize()

    def getAlphaTransferSize(self) -> int:
        return self._alphatransfer.GetSize()

    def getGradientTransferSize(self) -> int:
        return self._gradienttransfer.GetSize()

    def clearColorTransfer(self) -> None:
        self._colortransfer.RemoveAllPoints()

    def clearAlphaTransfer(self) -> None:
        self._alphatransfer.RemoveAllPoints()

    def clearGradientTransfer(self) -> None:
        self._gradienttransfer.RemoveAllPoints()

    def clear(self) -> None:
        self._ID = None
        self._colortransfer.RemoveAllPoints()
        self._alphatransfer.RemoveAllPoints()
        self._gradienttransfer.RemoveAllPoints()

    def copy(self) -> SisypheColorTransfer:
        buff = SisypheColorTransfer()
        buff._ID = self._ID
        buff._colortransfer.DeepCopy(self._colortransfer)
        buff._alphatransfer.DeepCopy(self._alphatransfer)
        buff._gradienttransfer.DeepCopy(self._gradienttransfer)
        return buff

    def copyFrom(self, buff: SisypheColorTransfer) -> None:
        if isinstance(buff, SisypheColorTransfer):
            self._ID = buff._ID
            self._colortransfer.DeepCopy(buff._colortransfer)
            self._alphatransfer.DeepCopy(buff._alphatransfer)
            self._gradienttransfer.DeepCopy(buff._gradienttransfer)
        else:
            raise TypeError('parameter functype is not SisypheColorTransfer.')

    def copyToDict(self) -> dict:
        return {'color': self.copyToList('color'),
                'alpha': self.copyToList('alpha'),
                'gradient': self.copyToList('gradient')}

    def copyFromDict(self, cdict: dict) -> None:
        if isinstance(cdict, dict):
            self.copyFromList(cdict['color'], 'color')
            self.copyFromList(cdict['alpha'], 'alpha')
            self.copyFromList(cdict['gradient'], 'gradient')
        else: raise TypeError('parameter type {} is not dict.'.format(type(cdict)))

    def copyToList(self, code: str) -> list:
        clist = []
        if code == 'color':
            for i in range(0, self._colortransfer.GetSize()):
                clist.append(self.getColorTransferElement(i))
        elif code == 'alpha':
            for i in range(0, self._alphatransfer.GetSize()):
                clist.append(self.getAlphaTransferElement(i))
        elif code == 'gradient':
            for i in range(0, self._gradienttransfer.GetSize()):
                clist.append(self.getGradientTransferElement(i))
        else: raise ValueError('{} invalid parameter value.'.format(code))
        return clist

    def copyFromList(self, clist: list | np_ndarray, code: str) -> None:
        if isinstance(clist, (list, ndarray)):
            if code == 'color':
                self._colortransfer.RemoveAllPoints()
                for i in range(0, len(clist)):
                    self.addColorTransferElement(vrgb=clist[i])
            elif code == 'alpha':
                self._alphatransfer.RemoveAllPoints()
                for i in range(0, len(clist)):
                    self.addAlphaTransferElement(va=clist[i])
            elif code == 'gradient':
                self._gradienttransfer.RemoveAllPoints()
                for i in range(0, len(clist)):
                    self.addGradientTransferElement(va=clist[i])
            else: raise ValueError('{} invalid parameter value.'.format(code))
        else: raise TypeError('parameter type {} is not list.'.format(type(clist)))

    def copyToNumpy(self, code: str) -> np_ndarray:
        return np_array(self.copyToList(code))

    def copyFromNumpy(self, cnp: np_ndarray, code: str) -> None:
        self.copyFromList(cnp, code)

    def isSameColorTransfer(self, buff: SisypheColorTransfer) -> bool:
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._colortransfer.GetSize()):
                vrgb1 = self.getColorTransferElement(i)
                vrgb2 = buff.getColorTransferElement(i)
                if vrgb1 != vrgb2:
                    return False
            return True
        else:
            return False

    def isSameAlphaTransfer(self, buff: SisypheColorTransfer) -> bool:
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._alphatransfer.GetSize()):
                va1 = self.getAlphaTransferElement(i)
                va2 = buff.getAlphaTransferElement(i)
                if va1 != va2:
                    return False
            return True
        else:
            return False

    def isSameGradientTransfer(self, buff: SisypheColorTransfer) -> bool:
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._gradienttransfer.GetSize()):
                va1 = self.getGradientTransferElement(i)
                va2 = buff.getGradientTransferElement(i)
                if va1 != va2:
                    return False
            return True
        else:
            return False

    def hasColorElement(self,
                        v: float | None = None,
                        r: float | None = None,
                        g: float | None = None,
                        b: float | None = None,
                        vrgb: list[float, float, float] | None = None) -> int | None:
        if vrgb is None:
            vrgb = [v, r, g, b]
        for i in range(0, self._colortransfer.GetSize()):
            vrgb1 = self.getColorTransferElement(i)
            if vrgb == vrgb1: return i
        return None

    def hasAlphaElement(self,
                        v: float | None = None,
                        a: float | None = None,
                        va: list[float, float] | None = None) -> int | None:
        if va is None: va = [v, a]
        for i in range(0, self._alphatransfer.GetSize()):
            va1 = self.getAlphaTransferElement(i)
            if va == va1: return i
        return None

    def hasGradientElement(self,
                           v: float | None = None,
                           a: float | None = None,
                           va: list[float, float] | None = None) -> int | None:
        if va is None: va = [v, a]
        for i in range(0, self._gradienttransfer.GetSize()):
            va1 = self.getGradientTransferElement(i)
            if va == va1: return i
        return None

    def hasColorTransferValue(self, v: float) -> int | None:
        for i in range(0, self._colortransfer.GetSize()):
            vrgb = self.getColorTransferElement(i)
            if v == vrgb[0]: return i
        return None

    def hasAlphaTransferValue(self, v: float) -> int | None:
        for i in range(0, self._alphatransfer.GetSize()):
            va = self.getAlphaTransferElement(i)
            if v == va[0]: return i
        return None

    def hasGradientTransferValue(self, v: float) -> int | None:
        for i in range(0, self._gradienttransfer.GetSize()):
            va = self.getGradientTransferElement(i)
            if v == va[0]: return i
        return None

    def getValueFromColor(self,
                          r: float | None = None,
                          g: float | None = None,
                          b: float | None = None,
                          rgb: list[float, float, float] | None = None) -> float | None:
        if rgb is None:
            rgb = [r, g, b]
        for i in range(0, self._colortransfer.GetSize()):
            vrgb1 = self.getColorTransferElement(i)
            if vrgb1[1:4] == rgb: return vrgb1[0]  # value
        return None

    def getColorFromValue(self, v: float, interpol: bool = True) -> list[float, float, float] | None:
        if interpol:
            return self._colortransfer.GetColor(v)
        else:
            for i in range(0, self._colortransfer.GetSize()):
                vrgb = self.getColorTransferElement(i)
                if vrgb[0] == v: return vrgb[1:4]  # r, g, b
            return None

    def getValueFromAlpha(self, a: float) -> float | None:
        for i in range(0, self._alphatransfer.GetSize()):
            va1 = self.getAlphaTransferElement(i)
            if va1[1] == a: return va1[0]  # value
        return None

    def getAlphaFromValue(self, v: float, interpol: bool = True) -> float | None:
        if interpol:
            return self._alphatransfer.GetValue(v)
        else:
            for i in range(0, self._alphatransfer.GetSize()):
                va = self.getAlphaTransferElement(i)
                if va[0] == v: return va[1]  # a
            return None

    def getValueFromGradient(self, a: float) -> float | None:
        for i in range(0, self._gradienttransfer.GetSize()):
            va1 = self.getGradientTransferElement(i)
            if va1[1] == a: return va1[0]  # value
        return None

    def getGradientFromValue(self, v: float, interpol: bool = True) -> float | None:
        if interpol:
            return self._gradienttransfer.GetValue(v)
        else:
            for i in range(0, self._gradienttransfer.GetSize()):
                va = self.getGradientTransferElement(i)
                if va[0] == v: return va[1]  # g
            return None

    def isEqual(self, buff: SisypheColorTransfer) -> bool:
        if isinstance(buff, SisypheColorTransfer):
            return self.isSameColorTransfer(buff) and \
                   self.isSameAlphaTransfer(buff) and \
                   self.isSameGradientTransfer(buff)
        else: return False

    def getRange(self) -> tuple[float, float]:
        return self._colortransfer.GetRange()

    def saveToXML(self, filename: str) -> None:
        path, ext = splitext(filename)
        if ext.lower() != SisypheColorTransfer._FILEEXT:
            filename = path + SisypheColorTransfer._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(SisypheColorTransfer._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        # ID
        node = doc.createElement('ID')
        item = doc.createTextNode(str(self._ID))
        node.appendChild(item)
        root.appendChild(node)
        # color transfer
        if self._colortransfer.GetSize() > 0:
            color = doc.createElement('colortransfer')
            for i in range(0, self._colortransfer.GetSize()):
                rgb = self.getColorTransferElement(i)
                v = rgb[0]
                rgb = rgb[1:4]
                rgb = [str(int(j * 255.0)) for j in rgb]
                rgb = ' '.join(rgb)
                node = doc.createElement('rgb')
                node.setAttribute('value', str(v))
                color.appendChild(node)
                item = doc.createTextNode(rgb)
                node.appendChild(item)
            root.appendChild(color)
        # alpha transfer
        if self._alphatransfer.GetSize() > 0:
            alpha = doc.createElement('alphatransfer')
            for i in range(0, self._alphatransfer.GetSize()):
                va = self.getAlphaTransferElement(i)
                node = doc.createElement('alpha')
                node.setAttribute('value', str(va[0]))
                alpha.appendChild(node)
                item = doc.createTextNode(str(int(va[1] * 255)))
                node.appendChild(item)
            root.appendChild(alpha)
        # gradient transfer
        if self._gradienttransfer.GetSize() > 0:
            gradient = doc.createElement('gradienttransfer')
            for i in range(0, self._gradienttransfer.GetSize()):
                va = self.getGradientTransferElement(i)
                node = doc.createElement('gradient')
                node.setAttribute('value', str(va[0]))
                gradient.appendChild(node)
                item = doc.createTextNode(str(int(va[1] * 255)))
                node.appendChild(item)
            root.appendChild(gradient)
        doc.appendChild(root)
        buff = doc.toprettyxml()
        f = open(filename, 'w')
        try:
            f.write(buff)
        except IOError:
            raise IOError('XML write error.')
        finally:
            f.close()

    def loadFromXML(self, filename: str) -> None:
        path, ext = splitext(filename)
        if exists(filename) and ext.lower() != SisypheColorTransfer._FILEEXT:
            filename = path + SisypheColorTransfer._FILEEXT
        try:
            doc = minidom.parse(filename)
            root = doc.documentElement
            if root.nodeName == SisypheColorTransfer._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                self.clear()
                node = root.firstChild
                while node:
                    # get ID
                    if node.nodeName == 'ID':
                        self._ID = node.firstChild.data
                    # get color transfer points
                    elif node.nodeName == 'colortransfer':
                        childnode = node.firstChild
                        while childnode:
                            # Alternation of TEXT_NODE and ELEMENT_NODE
                            if childnode.nodeType == 1:  # ELEMENT_NODE
                                if childnode.nodeName == 'rgb':
                                    value = float(childnode.getAttribute('value'))
                                    buff = childnode.firstChild.data
                                    rgb = buff.split(' ')
                                    rgb = [(float(j) / 255.0) for j in rgb]
                                    self._colortransfer.AddRGBPoint(value, rgb[0], rgb[1], rgb[2])
                            childnode = childnode.nextSibling
                    # get alpha transfer points
                    elif node.nodeName == 'alphatransfer':
                        childnode = node.firstChild
                        while childnode:
                            # Alternation of TEXT_NODE and ELEMENT_NODE
                            if childnode.nodeType == 1:  # ELEMENT_NODE
                                if childnode.nodeName == 'alpha':
                                    value = float(childnode.getAttribute('value'))
                                    a = float(childnode.firstChild.data) / 255
                                    self._alphatransfer.AddPoint(value, a)
                            childnode = childnode.nextSibling
                    # gradient transfer points
                    elif node.nodeName == 'gradienttransfer':
                        childnode = node.firstChild
                        while childnode:
                            # Alternation of TEXT_NODE and ELEMENT_NODE
                            if childnode.nodeType == 1:  # ELEMENT_NODE
                                if childnode.nodeName == 'gradient':
                                    value = float(childnode.getAttribute('value'))
                                    a = float(childnode.firstChild.data) / 255
                                    self._gradienttransfer.AddPoint(value, a)
                            childnode = childnode.nextSibling
                    node = node.nextSibling
            else:
                raise IOError('XML format is not supported.')
        except IOError:
            raise IOError('XML read error.')
