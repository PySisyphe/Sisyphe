"""
External packages/modules
-------------------------

    - matplotlib, graph plot library, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

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
from numpy import array

from matplotlib.cm import get_cmap
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap

from PyQt5.QtGui import QColor
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPainter

from vtk import vtkLookupTable
from vtk import vtkColorTransferFunction
from vtk import vtkPiecewiseFunction

from Sisyphe.core.sisypheConstants import getLutExt

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.core.sisypheVolume import SisypheVolume


__all__ = ['lutConversion',
           'saveColormapBitmapPreview',
           'SisypheLut',
           'SisypheColorTransfer']

"""
Functions
~~~~~~~~~

    - lutConversion(filenames: str | list[str], out: str = 'xlut')
    - saveColormapBitmapPreview(filenames: str | list[str], format: str = 'jpg')

Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheLut
             -> SisypheColorTransfer
"""

def lutConversion(filenames: str | list[str], out: str = 'xlut') -> None:
    """
    Batch look-up table colormaps conversion. Supported formats are .lut, .xlut, .olt, .txt

    Parameters
    ----------
    filenames : str | list[str]
        list of look-up table colormaps file names
    out : str
        conversion target format '.lut', '.xlut' (default), '.olt', '.txt'
    """
    out = '.{}'.format(out)
    if out in ('.lut', '.xlut', '.txt'):
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
                elif out == '.txt': lut.saveToTxt(filename)
    else: raise ValueError('format of conversion {} is not supported.'.format(out))


# noinspection PyShadowingBuiltins
def saveColormapBitmapPreview(filenames: str | list[str], format: str = 'jpg') -> None:
    """
    Save a bitmap preview of look-up table colormap files.

    Parameters
    ----------
    filenames : str | list[str]
        list of look-up table colormaps file names
    format : str
        saved bitmap file format 'bmp', 'jpg' (default), 'png'
    """
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


tupleInt4 = tuple[int, int, int, int]
tupleFloat3 = tuple[float, float, float]
tupleFloat4 = tuple[float, float, float, float]


class SisypheLut(object):
    """
    SisypheLut class

    Description
    ~~~~~~~~~~~

    Class to manage look-up table colormaps.

    Scope methods:

        - container-like methods (color elements)
        - copy from/to list, numpy.ndarray, matplotlib
        - bitmap preview
        - IO methods

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheLut

    Creation: 07/11/2022
    Last revision: 25/10/2024
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
        """
        Get SisypheLut file extension.

        Returns
        -------
        str
            '.xlut'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheLut filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Lut (.xlut)'
        """
        return 'PySisyphe Lut (*{})'.format(cls._FILEEXT)

    @classmethod
    def getDefaultLutDirectory(cls) -> str:
        """
        Get default lut directory (~/gui/lut)

        Returns
        -------
        str
            lut directory (~/gui/lut)
        """
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'lut')

    @classmethod
    def getColormapList(cls) -> list[str]:
        """
        Get list of available Look-up table colormaps.

        Returns
        -------
        list[str]
            list of available Look-up table colormaps
        """
        return cls._COLORMAPS

    @classmethod
    def getColormapFromName(cls, name: str) -> str:
        """
        Get public name of a Look-Up table colormap from its internal name.

        Parameters
        ----------
        name : str, internal name

        Returns
        -------
        str
            public name
        """
        return cls. _COLORMAPSNAME[name]

    @classmethod
    def openLut(cls, filename: str) -> SisypheLut | None:
        """
        Create a SisypheLut instance from a Look-Up table colormap file.

        Parameters
        ----------
        filename : str
            lut file name (supported formats 'xlut', '.lut', '.olt', '.txt')

        Returns
        -------
        SisypheLut
            loaded lut.
        """
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
        else: raise IOError('No such file {}.'.format(filename))

    # Special methods

    """
    Private attributes
    
    _name       str, lut name (internal functype) or filename (file functype)
    _typeLUT    int, lut functype (default, internal, file or custom)
    _vtklut     vtkLookupTable
    """

    def __init__(self, name: str | None = None) -> None:
        """
        SisypheLut instance constructor.

        Parameters
        ----------
        name : str | None
            look-up table colormap name to load in the current SisypheLut instance (default None)
        """
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
                    if ext == '.lut': self.load(name)
                    elif ext == '.xlut': self.loadFromXML(name)
                    elif ext == '.txt': self.loadFromTxt(name)
                    self._name = name
                else: self.setDefaultLut()
            else: self.setDefaultLut()
        else: self.setDefaultLut()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheLut instance to str
         """
        buff = '{}\n{}\n'.format(self._name, self.getLUTType(True))
        for i in range(0, 256):
            rgba = self._vtklut.GetTableValue(i)
            rgba = [int(j * 255.0) for j in rgba]
            buff += '{} r: {} g: {} b: {} a: {}\n'.format(i, rgba[0], rgba[1], rgba[2], rgba[3])
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheLut instance representation
        """
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    def __len__(self) -> int:
        """
        Special overloaded method called by the built-in len() python function.

        Returns
        -------
        int
            number of colors in the look-up table colormap (always 255) of the current SisypheLut instance
        """
        return 255

    def __getitem__(self, i: int) -> tupleFloat4:
        """
        Special overloaded container getter method. Get the color associated with index i in the colormap look-up table
        of the current SisypheLut instance.
        syntax: color = instance_name[i]

        Parameters
        ----------
        i : int
            color index in the look-up table colormap

        Returns
        -------
        tuple[float, float, float, float]
            color (red, green, blue, alpha)
        """
        if 0 <= i <= 255: return self._vtklut.GetTableValue(i)
        else: raise KeyError('invalid key index')

    def __setitem__(self, i: int, v: tupleFloat4 | list[float]) -> None:
        """
        Special overloaded container setter method. Set the color associated with index i in the colormap look-up table
        of the current SisypheLut instance.
        syntax: instance_name[i] = color

        Parameters
        ----------
        i : int
            color index in the look-up table colormap
        v : tuple[float, float, float, float]
            color (red, green, blue, alpha)
        """
        if 0 <= i <= 255: self._vtklut.SetTableValue(i, v)
        else: raise KeyError('invalid key index')

    def __contains__(self, v: tupleFloat4 | list[float]) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator. Checks whether v parameter
        (color) is in the look-up table colormap of the current SisypheLut instance.

        Parameters
        ----------
        v : tuple[float, float, float, float]
            color (red, green, blue, alpha)

        Returns
        -------
        bool
            True if v parameter (color) is in the look-up table colormap
        """
        for i in range(0, 256):
            if self.isSameColor(i, v):
                return True
        return False

    def __eq__(self, buff: SisypheLut) -> bool:
        """
        Special overloaded relational operator ==. Look-up table colormap comparison.
        self == other -> bool

        Parameters
        ----------
        buff : SisypheLut
            lut to compare

        Returns
        -------
        bool
            True if same lut
        """
        return self.isEqual(buff)

    # Public methods

    def copy(self) -> SisypheLut:
        """
        Copy of the current SisypheLut instance (deep copy).

        Returns
        -------
        SisypheLut
            lut copy
        """
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
        """
        Copy SisypheLut attributes to the current SisypheLut instance (deep copy).

        Parameters
        ----------
        buff : SisypheLut
            lut to copy
        """
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

    def copyToList(self) -> list[list[float]]:
        """
        Copy look-up table colormap of the current SisypheLut instance to a list.

        Returns
        -------
        list[list[float, float, float, float]]
            list of 255 colors (red, green, blue, alpha)
        """
        clist = []
        for i in range(0, 256):
            v = self._vtklut.GetTableValue(i)
            clist.append(list(v))
        return clist

    def copyFromList(self, clist: list[list[float]]) -> None:
        """
        Copy look-up table colormap sent as list parameter to the current SisypheLut instance.

        Parameters
        ----------
        clist : list[list[float, float, float, float]]
            list of 255 colors (red, green, blue, alpha) to copy.
        """
        if isinstance(clist, list):
            self._name = 'from list'
            self._typeLUT = self._LUTTOCODE['custom']
            for i in range(0, 256):
                v = clist[i]
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter {} type is not list.'.format(type(clist)))

    def copyToNumpy(self) -> ndarray:
        """
        Copy look-up table colormap of the current SisypheLut instance to a numpy array.

        Returns
        -------
        numpy.ndarray
            ndarray of 255 colors (red, green, blue, alpha) copy.
        """
        return array(self.copyToList())

    def copyFromNumpy(self, cnp: ndarray) -> None:
        """
        Copy look-up table colormap sent as numpy.ndarray parameter to the current SisypheLut instance.

        Parameters
        ----------
        cnp : numpy.ndarray
            ndarray of 255 colors (red, green, blue, alpha) to copy.
        """
        if isinstance(cnp, ndarray):
            self._name = 'from numpy'
            self._typeLUT = self._LUTTOCODE['custom']
            for i in range(0, 256):
                v = cnp[i, :]
                # noinspection PyTypeChecker
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter type {} is not a numpy.ndarray.'.format(type(cnp)))

    def copyToMatplotlibColormap(self) -> ListedColormap:
        """
        Copy look-up table colormap of the current SisypheLut instance to a matplotlib.colors.ListedColormap.

        Returns
        -------
        matplotlib.colors.ListedColormap
            lut copy
        """
        cmap = ListedColormap(self.copyToList(), self._name, 256)
        cmap.set_over(cmap(255))
        cmap.set_under(cmap(0))
        return cmap

    def copyFromMatplotlibColormap(self, cmap: ListedColormap | LinearSegmentedColormap) -> None:
        """
        Copy matplotlib look-up table colormap sent as parameter to the current SisypheLut instance.

        Parameters
        ----------
        cmap : matplotlib.colors.ListedColormap, look-up table colormap | matplotlib.colors.LinearSegmentedColormap
            lut to copy
        """
        if isinstance(cmap, (ListedColormap, LinearSegmentedColormap)):
            self._name = cmap.name
            self._typeLUT = self._LUTTOCODE['internal']
            for i in range(0, 256):
                v = cmap(i / 255)
                self._vtklut.SetTableValue(i, v[0], v[1], v[2], 1.0)
        else: raise TypeError('parameter type {} is not a matplotlib colormap.'.format(type(cmap)))

    # < Revision 25/10/2024
    # add reverseLut method
    def reverseLut(self) -> None:
        """
        Reverse the color order in the look-up table colormap of the current SisypheLut instance.
        """
        c = self.copyToList()
        for i in range(0, 256):
            self._vtklut.SetTableValue(i, c[255 - i])
    # Revision 25/10/2024 >

    # < Revision 25/10/2024
    # add getReversedLut method
    def getReversedLut(self) -> SisypheLut:
        """
        Copy of the current SisypheLut instance (deep copy) in reverse color order.

        Returns
        -------
            SisypheLut
                reversed LUT
        """
        lut = self.copy()
        for i in range(0, 256):
            lut._vtklut.SetTableValue(i, self._vtklut.GetTableValue(255 - i))
        return lut
    # Revision 25/10/2024 >

    def isEqual(self, buff: ListedColormap | LinearSegmentedColormap | SisypheLut) -> bool:
        """
        Check whether the look-up table colormap of the current SisypheLut instance is identical to the one sent as
        parameter.

        Parameters
        ----------
        buff : ListedColormap | LinearSegmentedColormap | SisypheLut
            look-up table colormap

        Returns
        -------
        bool
            True if lut are identical
        """
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
        else: raise TypeError('parameter functype is not Matplotlib colormap or SisypheLut.')

    def setDefaultLut(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'gray' (default).
        """
        self._name = 'gray'
        self._typeLUT = self._LUTTOCODE['default']
        for i in range(0, 256):
            v = float(i) / 255.0
            self._vtklut.SetTableValue(i, v, v, v, 1.0)

    def setLut(self, name: str) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance. If the name doesn't appear in the internal lut
        list, try opening a file with the same name from the default lut directory.

        Parameters
        ----------
        name : str
            lut name
        """
        if isinstance(name, str):
            if name == 'gray':
                self.setDefaultLut()
            elif name in self._COLORMAPS: self.setInternalLut(name)
            elif name in self._COLORMAPSNAME.values():
                idx = list(self._COLORMAPSNAME.values()).index(name)
                name = list(self._COLORMAPSNAME.keys())[idx]
                self.setInternalLut(name)
            else:
                # search in lut directory
                name = splitext(name)[0]
                filename = join(self.getDefaultLutDirectory(), name + self.getFileExt())
                if exists(filename): self.loadFromXML(filename)
                else: self.setDefaultLut()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def setInternalLut(self, name: str) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance.

        Parameters
        ----------
        name : str
            lut name
        """
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
            else: raise ValueError('{} is not a predefined Lut.'.format(name))
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def setLutToAutumn(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'autumn'.
        """
        self.setInternalLut(self._COLORMAPS[2])

    def setLutToCool(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'cool'.
        """
        self.setInternalLut(self._COLORMAPS[3])

    def setLutToGNU(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'gnu'.
        """
        self.setInternalLut(self._COLORMAPS[4])

    def setLutToGNU2(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'gnu2'.
        """
        self.setInternalLut(self._COLORMAPS[5])

    def setLutToHeat(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'heat'.
        """
        self.setInternalLut(self._COLORMAPS[6])

    def setLutToHot(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'hot'.
        """
        self.setInternalLut(self._COLORMAPS[8])

    def setLutToJet(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'jet'.
        """
        self.setInternalLut(self._COLORMAPS[10])

    def setLutToSpectral(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'spectral'.
        """
        self.setInternalLut(self._COLORMAPS[11])

    def setLutSpring(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'spring'.
        """
        self.setInternalLut(self._COLORMAPS[12])

    def setLutToSummer(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'summer'.
        """
        self.setInternalLut(self._COLORMAPS[13])

    def setLutToRainbow(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'rainbow'.
        """
        self.setInternalLut(self._COLORMAPS[14])

    def setLutToWinter(self) -> None:
        """
        Set look-up table colormap of the current SisypheLut instance to 'winter'.
        """
        self.setInternalLut(self._COLORMAPS[15])

    def isDefaultLut(self) -> bool:
        """
        Check whether look-up table colormap type of the current SisypheLut instance is 'default' (grayscale).

        Returns
        -------
        bool
            True if look-up table colormap type is 'default'
        """
        return self._typeLUT == self._LUTTOCODE['default']

    def isInternalLut(self) -> bool:
        """
        Check whether look-up table colormap type of the current SisypheLut instance is 'internal'.

        Returns
        -------
        bool
            True if look-up table colormap type is 'internal'
        """
        return self._typeLUT == self._LUTTOCODE['internal']

    def isFileLut(self) -> bool:
        """
        Check whether look-up table colormap type of the current SisypheLut instance is 'file'.

        Returns
        -------
        bool
            True if look-up table colormap type is 'file'
        """
        return self._typeLUT == self._LUTTOCODE['file']

    def isCustomLut(self) -> bool:
        """
        Check whether look-up table colormap type of the current SisypheLut instance is 'custom'.

        Returns
        -------
        bool
            True if look-up table colormap type is 'custom'
        """
        return self._typeLUT == self._LUTTOCODE['custom']

    def getFilename(self) -> str | None:
        """
        Get the look-up table colormap filename of the current SisypheLut instance.

        Returns
        -------
        str | None
            look-up table colormap filename if type is 'file', None otherwise
        """
        if self._typeLUT == self._LUTTOCODE['file'] and exists(self._name): return self._name
        else: return None

    def getLUTType(self, string: bool = True) -> str | int:
        """
        Get the look-up table colormap type of the current SisypheLut instance.

        Parameters
        ----------
        string : bool
            if true returns str code, otherwise int code (0 'default', 1 'internal', 2 'file', 3 'custom')

        Returns
        -------
        str | int
            look-up table colormap type
        """
        if string: return self._CODETOLUT[self._typeLUT]
        else: return self._typeLUT

    def getName(self) -> str:
        """
        Get the name of the look-up table colormap of the current SisypheLut instance.

        Returns
        -------
        str
            lut name
        """
        if self._typeLUT == self._LUTTOCODE['file']: return splitext(basename(self._name))[0]
        else: return self._name

    def setDisplayBelowRangeColorOff(self) -> None:
        """
        Set transparent color (alpha=0) to display values below the minimum window value of the current SisypheLut
        instance.
        """
        self._vtklut.UseBelowRangeColorOff()

    def setDisplayBelowRangeColorOn(self) -> None:
        """
        Set opaque black color (alpha=1.0) to display values below the minimum window value of the current SisypheLut
        instance.
        """
        self._vtklut.SetBelowRangeColor(0.0, 0.0, 0.0, 1.0)
        self._vtklut.UseBelowRangeColorOn()

    def getvtkLookupTable(self) -> vtkLookupTable:
        """
        Get the look-up table colormap attribute of the current SisypheLut instance.

        Returns
        -------
        vtk.vtkLookupTable
            VTK lut
        """
        return self._vtklut

    def setvtkLookupTable(self, vtklut: vtkLookupTable) -> None:
        """
        Set the look-up table colormap attribute of the current SisypheLut instance.

        Parameters
        ----------
        vtklut : vtk.vtkLookupTable
            VTK lut to copy
        """
        if isinstance(vtklut, vtkLookupTable):
            self._vtklut = vtklut
        else: raise TypeError('parameter type {} is not vtkLookupTable.'.format(type(vtklut)))

    def setColor(self, i: int, r: float, g: float, b: float, a: float = 1.0) -> None:
        """
        Set a color (red, green, blue, alpha) to index i in the look-up table colormap of the current SisypheLut
        instance.

        Parameters
        ----------
        i : int
            colormap index
        r : float
            red value (0.0 to 1.0)
        g : float
            green value (0.0 to 1.0)
        b : float
            blue value (0.0 to 1.0)
        a : float,
            alpha value (0.0 to 1.0)
        """
        if 0 <= i <= 255: self._vtklut.SetTableValue(i, r, g, b, a)
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def setQColor(self, i: int, c: QColor) -> None:
        """
        Set a color (Qt color) to index i in the look-up table colormap of the current SisypheLut instance.

        Parameters
        ----------
        i : int
            colormap index
        c : PyQt5.QtGui.QColor
            Qt color
        """
        self.setColor(i, c.redF(), c.greenF(), c.blueF())

    def setIntColor(self, i: int, r: int, g: int, b: int, a: int = 255):
        """
        Set a color (red, green, blue, alpha) to index i in the look-up table colormap of the current SisypheLut
        instance.

        Parameters
        ----------
        i : int
            colormap index
        r : int
            red value (0 to 255)
        g : int
            green value (0 to 255)
        b : int
            blue value (0 to 255)
        a : int
            alpha value (0 to 255)
        """
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0
        a = a / 255.0
        self.setColor(i, r, g, b, a)

    def getColor(self, i: int) -> tupleFloat4:
        """
        Get the color (red, green, blue, alpha) at index i in the look-up table colormap of the current SisypheLut
        instance.

        Parameters
        ----------
        i : int
            colormap index

        Returns
        -------
        tuple[float, float, float, float]
            color (red, green, blue, alpha)
        """
        if 0 <= i <= 255: return self._vtklut.GetTableValue(i)
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def getQColor(self, i: int) -> QColor:
        """
        Get the color (Qt color) at index i in the look-up table colormap of the current SisypheLut instance.

        Parameters
        ----------
        i : int
            colormap index

        Returns
        -------
        PyQt5.QtGui.QColor
            Qt color
        """
        rgba = self._vtklut.GetTableValue(i)
        c = QColor()
        c.setRedF(rgba[0])
        c.setGreenF(rgba[1])
        c.setBlueF(rgba[2])
        return c

    def getIntColor(self, i: int) -> tupleInt4:
        """
        Get the color (red, green, blue, alpha) at index i in the look-up table colormap of the current SisypheLut
        instance.

        Parameters
        ----------
        i : int
            colormap index

        Returns
        -------
        tuple[int, int, int, int]
            color (red, green, blue, alpha)
        """
        if 0 <= i <= 255:
            r, g, b, a = self._vtklut.GetTableValue(i)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            a = int(a * 255)
            return r, g, b, a
        else: raise KeyError('invalid index (0 <= index <= 255)')

    def getWindowRange(self) -> tuple[float, float]:
        """
         Get the windowing range of the look-up table colormap of the current SisypheLut instance.

        Returns
        -------
        tuple[float, float]
            minimum and maximum values of the window
         """
        return self._vtklut.GetTableRange()

    def setWindowRange(self, w1: float, w2: float) -> None:
        """
        Set the windowing range of the look-up table colormap of the current SisypheLut instance.

        Parameters
        ----------
        w1 : float
            minimum value of the window
        w2 : float
            maximum value of the window
        """
        self._vtklut.SetTableRange(w1, w2)

    def isSameColor(self, i: int, c: tupleFloat4 | list[float] | QColor) -> bool:
        """
        Check whether color at the index i in the look-up table colormap of the current SisypheLut instance identical
        to a color c given in parameter.

        Parameters
        ----------
            i : int
                colormap index
            c : tuple[float, float, float, float] | list[float, float, float, float] | QColor
                color

        Returns
        -------
        bool
            True if colors are identical
        """
        if isinstance(c, QColor): c = (c.redF(), c.greenF(), c.blueF(), c.alphaF())
        return self._vtklut.GetTableValue(i) == c

    def getBitmapPreview(self, width: int, height: int) -> QImage:
        """
        Get a look-up table colormap bitmap preview of the current SisypheLut instance.

        Parameters
        ----------
        width : int
            bitmap preview width
        height : int
            bitmap preview height

        Returns
        -------
        PyQt5.QtGui.QImage
            bitmap preview
        """
        img = QImage(256, height, QImage.Format_ARGB32)
        paint = QPainter(img)
        for i in range(256):
            paint.setPen(self.getQColor(i))
            paint.drawLine(i, 0, i, height-1)
        if width != 256: img = img.scaledToWidth(width)
        return img

    # noinspection PyShadowingBuiltins
    def saveBitmapPreview(self, width: int, height: int, format: str = 'jpg') -> None:
        """
        Save a look-up table colormap bitmap preview of the current SisypheLut instance.

        Parameters
        ----------
        width : int
            bitmap preview width
        height : int
            bitmap preview height
        format : str
            bitmap file format ('bmp', 'jpg' default, 'png')
        """
        img = self.getBitmapPreview(width, height)
        if format in ('bmp', 'jpg', 'png'):
            filename = '{}.{}'.format(self.getName(), format)
            img.save(filename)
        else: raise ValueError('{} format is not supported'.format(format))

    def saveToTxt(self, filename: str) -> None:
        """
        Save current SisypheLut instance attributes to text file (.txt).

        Parameters
        ----------
        filename : str
            text file name (.txt)
        """
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
            raise IOError('write error.')
        finally:
            f.close()

    def saveToXML(self, filename: str) -> None:
        """
        Save current SisypheLut instance attributes to xml file (.xlut).

        Parameters
        ----------
        filename : str
            xml file name (.xlut)
        """
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
        """
        Save current SisypheLut instance attributes to lut file (.lut).

        Parameters
        ----------
        filename : str
            lut file name (.lut)
        """
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
        """
        Load current SisypheLut instance attributes from BrainVoyager lut file (.olt).

        Parameters
        ----------
        filename : str
            BrainVoyager lut file name (.olt)
        """
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
            # noinspection PyTypeChecker
            self._vtklut.SetTableValue(i, r256[i], g256[i], b256[i], 1.0)

    def loadFromTxt(self, filename: str) -> None:
        """
        Load current SisypheLut instance attributes from text file (.txt).

        Parameters
        ----------
        filename : str
            text file name (.txt)
        """
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
        """
        Load current SisypheLut instance attributes from xml file (.xlut).

        Parameters
        ----------
        filename : str
            xml file name (.xlut)
        """
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
        """
        Load current SisypheLut instance attributes from lut file (.lut).

        Parameters
        ----------
        filename : str
            lut file name (.lut)
        """
        filename = abspath(filename)
        path, ext = splitext(filename)
        if ext.lower() != '.lut':
            filename = path + '.lut'
            if not exists(filename): raise IOError('No such file {}.'.format(filename))
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
                    # noinspection PyTypeChecker
                    self._vtklut.SetTableValue(i, rv[i] / 255.0, gv[i] / 255.0, bv[i] / 255.0, av[i] / 255.0)
            elif info.st_size == 768:
                rv = f.read(256)
                gv = f.read(256)
                bv = f.read(256)
                rv = frombuffer(rv, dtype=uint8)
                gv = frombuffer(gv, dtype=uint8)
                bv = frombuffer(bv, dtype=uint8)
                for i in range(0, 256):
                    # noinspection PyTypeChecker
                    self._vtklut.SetTableValue(i, rv[i] / 255.0, gv[i] / 255.0, bv[i] / 255.0, 1.0)
            else: raise IOError('{} is not a LUT file.'.format(filename))
            # noinspection PyUnreachableCode
            self._typeLUT = self._LUTTOCODE['file']
            self._name = filename
        except IOError: raise IOError('read error.')
        finally: f.close()


class SisypheColorTransfer(object):
    """
    Description
    ~~~~~~~~~~~

    Class to manage color transfer function used for 3D volume rendering.

    This class has three transfer function attributes:

    - Color transfer function which associates image array values with colors
    - Alpha transfer function which associates image array values with alpha (opacity)
    - Gradient transfer function which associates gradient image array values with alpha (opacity) used to improve the
    rendering of object edges. (i.e. high gradient values in edges are associated with high alpha)

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheColorTransfer

    Creation: 07/11/2022
    Last revision: 13/12/2023
    """
    __slots__ = ['_ID', '_colortransfer', '_alphatransfer', '_gradienttransfer']

    # Class constants

    _FILEEXT = '.xtfer'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheColorTransfer file extension.

        Returns
        -------
        str
            '.xtfer'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get  SisypheColorTransfer filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Color Transfer (.xtfer)'
        """
        return 'PySisyphe Color Transfer (*{})'.format(cls._FILEEXT)

    @classmethod
    def openColorTransfer(cls, filename: str) -> SisypheColorTransfer:
        """
        Create a SisypheColorTransfer instance from a color Transfer file (.xtfer).

        Parameters
        ----------
        filename : str
            color Transfer file name

        Returns
        -------
        SisypheColorTransfer
            loaded color Transfer
        """
        filename = basename(filename) + '.xtfer'
        ct = SisypheColorTransfer()
        ct.loadFromXML(filename)
        return ct

    # Special methods

    """
    Private attributes

    _ID                 str
    _colortransfer      vtkColorTransferFunction
    _alphatransfer      vtkPiecewiseFunction
    _gradienttransfer   vtkPiecewiseFunction
    """

    def __init__(self) -> None:
        """
        SisypheColorTransfer instance constructor.
        """
        self._ID = None
        self._colortransfer = vtkColorTransferFunction()
        self._alphatransfer = vtkPiecewiseFunction()
        self._gradienttransfer = vtkPiecewiseFunction()

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheColorTransfer instance to str
         """
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
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheColorTransfer instance representation
        """
        return '{} class instance at <{}>\n{}'.format(self.__class__.__name__,
                                                      str(id(self)),
                                                      self.__str__())

    def __eq__(self, buff: SisypheColorTransfer) -> bool:
        """
        Special overloaded relational operator ==. Color transfer function comparison.
        self == other -> bool

        Parameters
        ----------
        buff : SisypheColorTransfer
            Color transfer to compare

        Returns
        -------
        bool
            True if identical
        """
        return self.isEqual(buff)

    # Public methods

    def isEmpty(self) -> bool:
        """
        Check whether all three transfer function of the current SisypheColorTransfer instance are empty.

        Returns
        -------
        bool
            True if all three transfer functions are empty
        """
        return self.getColorTransferSize() == 0 and \
               self.getAlphaTransferSize() == 0 and \
               self.getGradientTransferSize() == 0

    def isColorTransferEmpty(self) -> bool:
        """
        Check whether the color transfer function of the current SisypheColorTransfer instance is empty.

        Returns
        -------
        bool
            True if color transfer function is empty
        """
        return self.getColorTransferSize() == 0

    def isAlphaTransferEmpty(self) -> bool:
        """
        Check whether the alpha transfer function of the current SisypheColorTransfer instance is empty.

        Returns
        -------
        bool
            True if alpha transfer function is empty
        """
        return self.getAlphaTransferSize() == 0

    def isGradientTransferEmpty(self) -> bool:
        """
        Check whether the gradient transfer function of the current SisypheColorTransfer instance is empty.

        Returns
        -------
        bool
            True if gradient transfer function is empty
        """
        return self.getGradientTransferSize() == 0

    def setDefault(self, volume: SisypheVolume) -> None:
        """
        Initialize all three transfer functions of the current SisypheColorTransfer instance with default values.
        Black color for the minimum value of the image array. White color for the maximum value of the image array.
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(volume, SisypheVolume):
            self.setDefaultColor(volume)
            self.setDefaultAlpha(volume)
            self.setDefaultGradient(volume)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultColor(self, volume: SisypheVolume) -> None:
        """
        Initialize the color transfer function of the current SisypheColorTransfer instance with default values.

            - Black color for the minimum value of the image array.
            - White color for the maximum value of the image array.
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(volume, SisypheVolume):
            self.setID(volume.getArrayID())
            self.addColorTransferElement(v=volume.display.getRangeMin(), r=0.0, g=0.0, b=0.0)
            self.addColorTransferElement(v=volume.display.getRangeMax(), r=1.0, g=1.0, b=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultAlpha(self, volume: SisypheVolume) -> None:
        """
        Initialize the alpha transfer function of the current SisypheColorTransfer instance with default values.

            - Transparent color (alpha=0) for the minimum value of the image array.
            - Opaque color (alpha=1.0) for the maximum value of the image array.
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(volume, SisypheVolume):
            self.setID(volume.getArrayID())
            self.addAlphaTransferElement(v=volume.display.getRangeMin(), a=0.0)
            self.addAlphaTransferElement(v=volume.display.getRangeMax(), a=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setDefaultGradient(self, volume: SisypheVolume) -> None:
        """
        Initialize the gradient transfer function of the current SisypheColorTransfer instance with default values.

            - Transparent color (alpha=0) for the minimum value of the gradient image array.
            - Opaque color (alpha=1.0) for the maximum value of the gradient image array.
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(volume, SisypheVolume):
            self.setID(volume.getArrayID())
            self.addGradientTransferElement(v=0.0, a=0.0)
            self.addGradientTransferElement(v=volume.display.getRangeMax() - volume.display.getRangeMin(), a=1.0)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def init(self) -> None:
        """
        Initialize all three transfer functions of the current SisypheColorTransfer instance with default values.

            - Black color for the minimum value of the image array.
            - White color for the maximum value of the image array.
            - Default range between 0.0 and 1.0.
        """
        self.addColorTransferElement(v=0, r=0.0, g=0.0, b=0.0)
        self.addColorTransferElement(v=1, r=1.0, g=1.0, b=1.0)
        self.addAlphaTransferElement(v=0, a=0.0)
        self.addAlphaTransferElement(v=1, a=1.0)
        self.addGradientTransferElement(v=0, a=0.0)
        self.addGradientTransferElement(v=1, a=1.0)

    def getID(self) -> str:
        """
        Get ID attribute of the current SisypheColorTransfer instance.

        Returns
        -------
        str
            ID attribute
        """
        return self._ID

    def setID(self, ID: str | SisypheVolume) -> None:
        """
        Set ID attribute of the current SisypheColorTransfer instance.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            ID attribute
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if isinstance(ID, str): self._ID = ID
        elif isinstance(ID, SisypheVolume): self._ID = ID.getArrayID()
        else: raise TypeError('parameter type {} is not str, SisypheImage or SisypheVolume.'.format(type(ID)))

    def hasSameID(self, ID: str | SisypheVolume) -> bool:
        """
        Check whether the ID parameter is identical to that of the current SisypheColorTransfer instance ID.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume
            ID attribute

        Returns
        -------
        bool
            True if IDs are identical
        """
        from Sisyphe.core.sisypheVolume import SisypheVolume
        if self._ID is None: return False
        else:
            if isinstance(ID, SisypheVolume): return self._ID == ID.getArrayID()
            elif isinstance(ID, str): return self._ID == ID
            else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(ID)))

    def hasID(self) -> bool:
        """
        Check whether the ID attribute of the current SisypheColorTransfer is defined (not None).

        Returns
        -------
        bool
            True if ID is not None
        """
        return self._ID is not None

    def getColorTransfer(self) -> vtkColorTransferFunction:
        """
        Get the color transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        vtk.vtkColorTransferFunction
            color transfer function copy
        """
        return self._colortransfer

    def getAlphaTransfer(self) -> vtkPiecewiseFunction:
        """
        Get the alpha transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        vtk.vtkPiecewiseFunction
            alpha transfer function copy
        """
        return self._alphatransfer

    def getGradientTransfer(self) -> vtkPiecewiseFunction:
        """
        Get the gradient transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        vtk.vtkPiecewiseFunction
            gradient transfer function copy
        """
        return self._gradienttransfer

    def setColorTransfer(self, colortransfer: vtkColorTransferFunction) -> None:
        """
        Set the color transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        colortransfer : vtk.vtkColorTransferFunction
            color transfer function to copy
        """
        if isinstance(colortransfer, vtkColorTransferFunction):
            self._colortransfer = colortransfer
        else: raise TypeError('parameter type {} is not vtkColorTransferFunction.'.format(type(colortransfer)))

    def setAlphaTransfer(self, alphatransfer: vtkPiecewiseFunction) -> None:
        """
        Set the alpha transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        alphatransfer : vtk.vtkPiecewiseFunction
            alpha transfer function to copy
        """
        if isinstance(alphatransfer, vtkPiecewiseFunction):
            self._alphatransfer = alphatransfer
        else: raise TypeError('parameter type {} is not vtkPiecewiseFunction.'.format(type(alphatransfer)))

    def setGradientTransfer(self, gradienttransfer: vtkPiecewiseFunction) -> None:
        """
        Set the gradient transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        gradienttransfer : vtk.vtkPiecewiseFunction
            gradient trasnfer function to copy
        """
        if isinstance(gradienttransfer, vtkPiecewiseFunction):
            self._gradienttransfer = gradienttransfer
        else: raise TypeError('parameter type {} is not vtkPiecewiseFunction.'.format(type(gradienttransfer)))

    def addColorTransferElement(self,
                                v: float | None = None,
                                r: float | None = None,
                                g: float | None = None,
                                b: float | None = None,
                                vrgb: tupleFloat4 | list[float] | None = None) -> None:
        """
        Add a color to the color transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float | None
            scalar value of the image array
        r : float | None
            red component of the color
        g : float | None
            green component of the color
        b : float | None
            blue component of the color
        vrgb : tuple[float, float, float, float] | list[float] | None
            scalar value of the image array then red, green blue components
        """
        if vrgb is not None:
            v = vrgb[0]
            r = vrgb[1]
            g = vrgb[2]
            b = vrgb[3]
        self._colortransfer.AddRGBPoint(v, r, g, b)

    def addAlphaTransferElement(self,
                                v: float | None = None,
                                a: float | None = None,
                                va: tuple[float, float] | list[float] | None = None) -> None:
        """
        Add alpha value to the alpha transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float | None
            scalar value of the image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the image array and alpha value
        """
        if va is not None:
            v = va[0]
            a = va[1]
        self._alphatransfer.AddPoint(v, a)

    def addGradientTransferElement(self,
                                   v: float | None = None,
                                   a: float | None = None,
                                   va: tuple[float, float] | list[float] | None = None) -> None:
        """
        Add gradient value to the gradient transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float | None
            scalar value of the gradient image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the gradient image array and alpha value
        """
        if va is not None:
            v = va[0]
            a = va[1]
        self._gradienttransfer.AddPoint(v, a)

    def getColorTransferElement(self, index: int) -> list[float]:
        """
        Get color from index of the color transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index of the color transfer function table

        Returns
        -------
        list[float, float, float, float]
            scalar value of the image array then red, green and blue components
        """
        vrgb = [0.0] * 6
        self._colortransfer.GetNodeValue(index, vrgb)
        return vrgb[:4]  # v, r, g, b, m, separator

    def getAlphaTransferElement(self, index: int) -> list[float]:
        """
        Get alpha from index of the alpha transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index of the alpha transfer function table

        Returns
        -------
        list[float, float]
            scalar value of the image array and alpha value
        """
        va = [0.0] * 4
        self._alphatransfer.GetNodeValue(index, va)
        return va[:2]  # v, a, m, separator

    def getGradientTransferElement(self, index: int) -> list[float]:
        """
        Get alpha from index of the gradient transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index of the gradient transfer function table

        Returns
        -------
        list[float, float]
            scalar value of the gradient image array and alpha value
        """
        va = [0.0] * 4
        self._gradienttransfer.GetNodeValue(index, va)
        return va[:2]  # v, a, m, separator

    def setColorTransferElement(self,
                                index: int | None = None,
                                v: float | None = None,
                                r: float | None = None,
                                g: float | None = None,
                                b: float | None = None,
                                vrgb: list[float] | tupleFloat4 | None = None) -> None:
        """
        Set color in the color transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index in the color transfer function table
        v : float | None
            scalar value of the image array
        r : float | None
            red component of the color
        g  : float | None
            green component of the color
        b  : float | None
            blue component of the color
        vrgb : tuple[float, float, float, float] | list[float, float, float, float] | None
            scalar value of the image array then red, green and blue components
        """
        if vrgb is not None:
            v = vrgb[0]
            r = vrgb[1]
            g = vrgb[2]
            b = vrgb[3]
        if index is None:
            index = self.hasColorTransferValue(v)
        if index is not None and index < self.getColorTransferSize():
            # noinspection PyArgumentList
            self._colortransfer.SetNodeValue(index, v, r, g, b, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def setAlphaTransferElement(self,
                                index: int | None = None,
                                v: float | None = None,
                                a: float | None = None,
                                va: list[float] | tuple[float, float] | None = None) -> None:
        """
        Set alpha value in the alpha transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index in the alpha transfer function table
        v : float | None
            scalar value of the image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the image array and alpha value
        """
        if va is not None:
            v = va[0]
            a = va[1]
        if index is None:
            index = self.hasAlphaTransferValue(v)
        if index is not None and index < self.getAlphaTransferSize():
            # noinspection PyArgumentList
            self._alphatransfer.SetNodeValue(index, v, a, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def setGradientTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None,
                                   a: float | None = None,
                                   va: list[float] | tuple[float, float] | None = None) -> None:
        """
        Set alpha value in the gradient transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        index : int
            index in the gradient transfer function table
        v : float | None
            scalar value of the gradient image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the gradient image array and alpha value
        """
        if va is not None:
            v = va[0]
            a = va[1]
        if index is None:
            index = self.hasGradientTransferValue(v)
        if index is not None and index < self.getGradientTransferSize():
            # noinspection PyArgumentList
            self._gradienttransfer.SetNodeValue(index, v, a, 0.5, 0.0)
        else: raise IndexError('index parameter is out of range.')

    def removeColorTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None) -> None:
        """
        Remove a color in the color transfer function of the current SisypheColorTransfer instance.
        Color is identified by an index in the color transfer function table or by a scalar value of the image array.

        Parameters
        ----------
        index : int | None
            index in the color transfer function table
        v : float | None
            scalar value of the image array
        """
        if v is None:
            if index < self.getColorTransferSize():
                vrgb = self.getColorTransferElement(index)
                v = vrgb[0]
            else: raise IndexError('index parameter is out of range.')
        self._colortransfer.RemovePoint(v)

    def removeAlphaTransferElement(self,
                                   index: int | None = None,
                                   v: float | None = None) -> None:
        """
        Remove an item in the alpha transfer function of the current SisypheColorTransfer instance.
        Item is identified by an index in the alpha transfer function table or by a scalar value of the image array.

        Parameters
        ----------
        index : int | None
            index in the alpha transfer function table
        v : float | None
            scalar value of the image array
        """
        if v is None:
            if index < self.getAlphaTransferSize():
                va = self.getAlphaTransferElement(index)
                v = va[0]
            else: raise IndexError('index parameter is out of range.')
        self._alphatransfer.RemovePoint(v)

    def removeGradientTransferElement(self,
                                      index: int | None = None,
                                      v: float | None = None) -> None:
        """
        Remove an item in the gradient transfer function of the current SisypheColorTransfer instance.
        Item is identified by an index in the gradient transfer function table or by a scalar value of the image array.

        Parameters
        ----------
        index : int | None
            index in the gradient transfer function table
        v : float | None
            scalar value of the gradient image array
        """
        if v is None:
            if index < self.getGradientTransferSize():
                va = self.getGradientTransferElement(index)
                v = va[0]
            else: raise IndexError('index parameter is out of range.')
        self._gradienttransfer.RemovePoint(v)

    def getColorTransferSize(self) -> int:
        """
        Get number of colors in the color transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        int
            number of colors in the color transfer function
        """
        return self._colortransfer.GetSize()

    def getAlphaTransferSize(self) -> int:
        """
        Get number of elements in the alpha transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        int
            number of elements in the alpha transfer function
        """
        return self._alphatransfer.GetSize()

    def getGradientTransferSize(self) -> int:
        """
        Get number of elements in the gradient transfer function of the current SisypheColorTransfer instance.

        Returns
        -------
        int
            number of elements in the gradient transfer function
        """
        return self._gradienttransfer.GetSize()

    def clearColorTransfer(self) -> None:
        """
        Remove all colors of the color transfer function of the current SisypheColorTransfer instance.
        """
        self._colortransfer.RemoveAllPoints()

    def clearAlphaTransfer(self) -> None:
        """
        Remove all elements of the alpha transfer function of the current SisypheColorTransfer instance.
        """
        self._alphatransfer.RemoveAllPoints()

    def clearGradientTransfer(self) -> None:
        """
        Remove all elements of the gradient transfer function of the current SisypheColorTransfer instance.
        """
        self._gradienttransfer.RemoveAllPoints()

    def clear(self) -> None:
        """
        Remove all elements of the three transfer function and clear ID attribute of the current SisypheColorTransfer
        instance.
        """
        self._ID = None
        self._colortransfer.RemoveAllPoints()
        self._alphatransfer.RemoveAllPoints()
        self._gradienttransfer.RemoveAllPoints()

    def copy(self) -> SisypheColorTransfer:
        """
        Copy of the current SisypheColorTransfer instance (deep copy).

        Returns
        -------
        SisypheColorTransfer
            color transfer function copy
        """
        buff = SisypheColorTransfer()
        buff._ID = self._ID
        buff._colortransfer.DeepCopy(self._colortransfer)
        buff._alphatransfer.DeepCopy(self._alphatransfer)
        buff._gradienttransfer.DeepCopy(self._gradienttransfer)
        return buff

    def copyFrom(self, buff: SisypheColorTransfer) -> None:
        """
        Copy SisypheColorTransfer attributes to the current SisypheColorTransfer instance (deep copy).

        Parameters
        ----------
        buff : SisypheColorTransfer
            color transfer functrion to copy
        """
        if isinstance(buff, SisypheColorTransfer):
            self._ID = buff._ID
            self._colortransfer.DeepCopy(buff._colortransfer)
            self._alphatransfer.DeepCopy(buff._alphatransfer)
            self._gradienttransfer.DeepCopy(buff._gradienttransfer)
        else: raise TypeError('parameter functype is not SisypheColorTransfer.')

    def copyToDict(self) -> dict[str, list[list[float]]]:
        """
        Copy all three transfer functions of the current SisypheColorTransfer instance to a dict.

        Returns
        -------
        dict[str, list[list[float, ...]]]
            Keys / Values, transfer functions as lists
                - 'color', color transfer function (list[list[float, float, float, float]])
                - 'alpha', alpha transfer function (list[list[float, float]])
                - 'gradient', gradient transfer function (list[list[float, float]])
        """
        return {'color': self.copyToList('color'),
                'alpha': self.copyToList('alpha'),
                'gradient': self.copyToList('gradient')}

    def copyFromDict(self, cdict: dict[str, list[list[float]]]) -> None:
        """
        Set all three transfer functions of the current SisypheColorTransfer instance from a dict parameter.

        Parameters
        ----------
        cdict : dict[str, list[list[float, ...]]]
            Keys / Values, transfer functions as lists
                - 'color', color transfer function (list[list[float, float, float, float]])
                - 'alpha', alpha transfer function (list[list[float, float]])
                - 'gradient', gradient transfer function (list[list[float, float]])
        """
        if isinstance(cdict, dict):
            self.copyFromList(cdict['color'], 'color')
            self.copyFromList(cdict['alpha'], 'alpha')
            self.copyFromList(cdict['gradient'], 'gradient')
        else: raise TypeError('parameter type {} is not dict.'.format(type(cdict)))

    def copyToList(self, code: str) -> list[list[float]]:
        """
        Copy one of the three transfer functions of the current SisypheColorTransfer instance to a list.

        Parameters
        ----------
        code : str
            code of the transfer function to copy ('color', 'alpha' or 'gradient')

        Returns
        -------
        list[list[float, ...]]
            - if code is 'color', list[list[float, float, float, float]] scalar value, red, green and blue components
            - if code is 'alpha', list[list[float, float]] scalar value and alpha components
            - if code is 'gradient', list[list[float, float]] scalar value and alpha components
        """
        clist = list()
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
        # noinspection PyUnreachableCode
        return clist

    def copyFromList(self, clist: list | ndarray, code: str) -> None:
        """
        Set one of the three transfer functions of the current SisypheColorTransfer instance from a list or a
        numpy.ndarray parameter.

        Parameters
        ----------
        code : str
            code of the transfer function to copy ('color', 'alpha' or 'gradient')
        clist : list[float, ...] | numpy.ndarray
            - if code is 'color', list[list[float, float, float, float]] scalar value, red, green and blue components
            - if code is 'alpha', list[list[float, float]] scalar value and alpha components
            - if code is 'gradient', list[list[float, float]] scalar value and alpha components
        """
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

    def copyToNumpy(self, code: str) -> ndarray:
        """
        Copy a transfer function of the current SisypheColorTransfer instance to a numpy.ndarray.

        Parameters
        ----------
        code : str
            transfer function to copy ('color', 'alpha' or 'gradient')

        Returns
        -------
        numpy.array(list[float, ...])
            - if code is 'color', numpy.array(list[float, float, float, float]) scalar value, red, green and blue components
            - if code is 'alpha', numpy.array(list[list[float, float]]) scalar value and alpha components
            - if code is 'gradient', numpy.array(list[list[float, float]]) scalar value and alpha components
        """
        return array(self.copyToList(code))

    def copyFromNumpy(self, cnp: ndarray, code: str) -> None:
        """
        Set one of the three transfer functions of the current SisypheColorTransfer instance from a list or a
        numpy.ndarray parameter.

        Parameters
        ----------
        code : str
            code of the transfer function to copy ('color', 'alpha' or 'gradient')
        cnp : numpy.array(list[float, ...])
            - if code is 'color', numpy.array(list[float, float, float, float]) scalar value, red, green and blue components
            - if code is 'alpha', numpy.array(list[list[float, float]]) scalar value and alpha components
            - if code is 'gradient', numpy.array(list[list[float, float]]) scalar value and alpha components
        """
        self.copyFromList(cnp, code)

    def isSameColorTransfer(self, buff: SisypheColorTransfer) -> bool:
        """
        Check whether the color transfer function of the parameter is identical to that of the current
        SisypheColorTransfer instance.

        Parameters
        ----------
        buff : SisypheColorTransfer
            color transfer function to compare

        Returns
        -------
        bool
            True if color transfer functions are identical
        """
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._colortransfer.GetSize()):
                vrgb1 = self.getColorTransferElement(i)
                vrgb2 = buff.getColorTransferElement(i)
                if vrgb1 != vrgb2:
                    return False
            return True
        else: return False

    def isSameAlphaTransfer(self, buff: SisypheColorTransfer) -> bool:
        """
        Check whether the alpha transfer function of the parameter is identical to that of the current
        SisypheColorTransfer instance.

        Parameters
        ----------
        buff : SisypheColorTransfer
            alpha transfer function to compare

        Returns
        -------
        bool
            True if alpha transfer functions are identical
        """
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._alphatransfer.GetSize()):
                va1 = self.getAlphaTransferElement(i)
                va2 = buff.getAlphaTransferElement(i)
                if va1 != va2:
                    return False
            return True
        else: return False

    def isSameGradientTransfer(self, buff: SisypheColorTransfer) -> bool:
        """
        Check whether the gradient transfer function of the parameter is identical to that of the current
        SisypheColorTransfer instance.

        Parameters
        ----------
        buff : SisypheColorTransfer
            gradient transfer function to compare

        Returns
        -------
        bool
            True if gradient transfer functions are identical
        """
        if isinstance(buff, SisypheColorTransfer):
            for i in range(0, self._gradienttransfer.GetSize()):
                va1 = self.getGradientTransferElement(i)
                va2 = buff.getGradientTransferElement(i)
                if va1 != va2:
                    return False
            return True
        else: return False

    def hasColorElement(self,
                        v: float | None = None,
                        r: float | None = None,
                        g: float | None = None,
                        b: float | None = None,
                        vrgb: tupleFloat4 | list[float] | None = None) -> int | None:
        """
        Check whether the value/color parameters are is the color transfer function of the current SisypheColorTransfer
        instance.

        Parameters
        ----------
        v : float | None
            scalar value of the image array
        r : float | None
            red component of the color
        g : float | None
            green component of the color
        b : float | None
            blue component of the color
        vrgb : tuple[float, float, float, float] | list[float, float, float, float] | None
            scalar value of the image array then red, green blue components

        Returns
        -------
        int | None
            index of the color item in the color transfer function table, None if not in the table
        """
        if vrgb is None:
            vrgb = [v, r, g, b]
        for i in range(0, self._colortransfer.GetSize()):
            vrgb1 = self.getColorTransferElement(i)
            if vrgb == vrgb1: return i
        return None

    def hasAlphaElement(self,
                        v: float | None = None,
                        a: float | None = None,
                        va: list[float] | tuple[float, float] | None = None) -> int | None:
        """
        Check whether the value/alpha parameters are is the alpha transfer function of the current SisypheColorTransfer
        instance.

        Parameters
        ----------
        v : float | None
            scalar value of the image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the image array and alpha value

        Returns
        -------
        int | None
            index of the item in the alpha transfer function table, None if not in the table.
        """
        if va is None: va = [v, a]
        for i in range(0, self._alphatransfer.GetSize()):
            va1 = self.getAlphaTransferElement(i)
            if va == va1: return i
        return None

    def hasGradientElement(self,
                           v: float | None = None,
                           a: float | None = None,
                           va: list[float] | tuple[float, float] | None = None) -> int | None:
        """
        Check whether the gradient value/alpha parameters are is the gradient transfer function of the current
        SisypheColorTransfer instance.

        Parameters
        ----------
        v : float | None
            scalar value of the gradient image array
        a : float | None
            alpha value
        va : tuple[float, float] | list[float, float] | None
            scalar value of the gradient image array and alpha value

        Returns
        -------
        int | None
            index of the item in the gradient transfer function table, None if not in the table.
        """
        if va is None: va = [v, a]
        for i in range(0, self._gradienttransfer.GetSize()):
            va1 = self.getGradientTransferElement(i)
            if va == va1: return i
        return None

    def hasColorTransferValue(self, v: float) -> int | None:
        """
        Check whether the scalar value v is in the color transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float
            scalar value in the image array

        Returns
        -------
        int | None
            index of the scalar value in the color transfer function table, None if not in the table.
        """
        for i in range(0, self._colortransfer.GetSize()):
            vrgb = self.getColorTransferElement(i)
            if v == vrgb[0]: return i
        return None

    def hasAlphaTransferValue(self, v: float) -> int | None:
        """
        Check whether the scalar value v is in the alpha transfer function of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float
            scalar value in the image array

        Returns
        -------
        int | None
            index of the scalar value in the alpha transfer function table, None if not in the table.
        """
        for i in range(0, self._alphatransfer.GetSize()):
            va = self.getAlphaTransferElement(i)
            if v == va[0]: return i
        return None

    def hasGradientTransferValue(self, v: float) -> int | None:
        """
        Check whether the scalar value v is in the gradient transfer function of the current SisypheColorTransfer
        instance.

        Parameters
        ----------
        v : float
            scalar value in the gradient image array

        Returns
        -------
        int | None
            index of the scalar value in the gradient transfer function table, None if not in the table.
        """
        for i in range(0, self._gradienttransfer.GetSize()):
            va = self.getGradientTransferElement(i)
            if v == va[0]: return i
        return None

    def getValueFromColor(self,
                          r: float | None = None,
                          g: float | None = None,
                          b: float | None = None,
                          rgb: list[float] | tupleFloat3 | None = None) -> float | None:
        """
        Get scalar value from color in the color transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        r : float | None
            red component of the color
        g : float | None
            green component of the color
        b : float | None
            blue component of the color
        rgb : tuple[float, float, float, float] | list[float, float, float, float] | None
            scalar value of the image array then red, green and blue components

        Returns
        -------
        float | None
            scalar value in the color transfer function table, None if not in the table.
        """
        if rgb is None:
            rgb = [r, g, b]
        for i in range(0, self._colortransfer.GetSize()):
            vrgb1 = self.getColorTransferElement(i)
            if vrgb1[1:4] == rgb: return vrgb1[0]  # value
        return None

    def getColorFromValue(self, v: float, interpol: bool = True) -> list[float] | None:
        """
        Get color from scalar value in the color transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float | None
            scalar value in the image array
        interpol : bool
            nearest scalar value in the color transfer function table

        Returns
        -------
        list[float] | None
            color (red, green and blue components) in the color transfer function table, None if not in the table.
        """
        if interpol:
            return list(self._colortransfer.GetColor(v))
        else:
            for i in range(0, self._colortransfer.GetSize()):
                vrgb = self.getColorTransferElement(i)
                if vrgb[0] == v: return vrgb[1:4]  # r, g, b
            return None

    def getValueFromAlpha(self, a: float) -> float | None:
        """
        Get scalar value from alpha in the alpha transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        a : float
            alpha value

        Returns
        -------
        float | None
            scalar value in the alpha transfer function table, None if not in the table.
        """
        for i in range(0, self._alphatransfer.GetSize()):
            va1 = self.getAlphaTransferElement(i)
            if va1[1] == a: return va1[0]  # value
        return None

    def getAlphaFromValue(self, v: float, interpol: bool = True) -> float | None:
        """
        Get alpha from scalar value in the alpha transfer function table of the current SisypheColorTransfer instance.

        Parameters
        ----------
        v : float
            scalar value in the image array
        interpol : bool
            nearest scalar value in the color transfer function table

        Returns
        -------
        float | None
            alpha value in the alpha transfer function table, None if not in the table.
        """
        if interpol:
            return self._alphatransfer.GetValue(v)
        else:
            for i in range(0, self._alphatransfer.GetSize()):
                va = self.getAlphaTransferElement(i)
                if va[0] == v: return va[1]  # a
            return None

    def getGradientValueFromAlpha(self, a: float) -> float | None:
        """
        Get gradient value from alpha in the gradient transfer function table of the current SisypheColorTransfer
        instance.

        Parameters
        ----------
        a : float | None
            alpha value

        Returns
        -------
        float | None
            gradient value in the alpha transfer function table, None if not in the table.
        """
        for i in range(0, self._gradienttransfer.GetSize()):
            va1 = self.getGradientTransferElement(i)
            if va1[1] == a: return va1[0]  # value
        return None

    def getAlphaFromGradientValue(self, v: float, interpol: bool = True) -> float | None:
        """
        Get alpha from gradient value in the gradient transfer function table of the current SisypheColorTransfer
        instance.

        Parameters
        ----------
        v : float | None
            scalar value in the gradient image array
        interpol : bool
            nearest scalar value in the color transfer function table

        Returns
        -------
        float | None
            alpha value in the gradient transfer function table, None if not in the table.
        """
        if interpol:
            return self._gradienttransfer.GetValue(v)
        else:
            for i in range(0, self._gradienttransfer.GetSize()):
                va = self.getGradientTransferElement(i)
                if va[0] == v: return va[1]  # g
            return None

    def isEqual(self, buff: SisypheColorTransfer) -> bool:
        """
        Check whether all three transfer functions of the parameter are identical to those of the current
        SisypheColorTransfer instance.

        Parameters
        ----------
        buff : SisypheColorTransfer
            color transfer function to compare

        Returns
        -------
        bool
            True if all three transfer functions are identical
        """
        if isinstance(buff, SisypheColorTransfer):
            return self.isSameColorTransfer(buff) and \
                   self.isSameAlphaTransfer(buff) and \
                   self.isSameGradientTransfer(buff)
        else: return False

    def getRange(self) -> tuple[float, float]:
        """
        Get scalar values range in the image array.

        Returns
        -------
        tuple[float, float]
            minimum and maximum scalar values in the image array
        """
        return self._colortransfer.GetRange()

    def saveToXML(self, filename: str) -> None:
        """
        Save current SisypheColorTransfer instance attributes to xml file (.xtfer).

        Parameters
        ----------
        filename : str
            xml file name (.xtfer)
        """
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
        """
        Load current SisypheColorTransfer instance attributes from xml file (.xtfer).

        Parameters
        ----------
        filename : str
            xml file name (.xtfer)
        """
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
