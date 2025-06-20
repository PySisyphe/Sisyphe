"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

import sys

from os import environ
from os import mkdir

from shutil import copy

from os.path import join
from os.path import split
from os.path import abspath
from os.path import dirname
from os.path import basename
from os.path import exists
from os.path import isfile

from glob import glob

from datetime import date
from datetime import datetime

from xml.dom import minidom

from PyQt5.QtGui import QFont
from PyQt5.QtGui import QFontDatabase


__all__ = ['getUsername',
           'getUserPath',
           'getUserPySisyphePath',
           'initPySisypheUserPath',
           'setUserSettingsToDefault',
           'SisypheSettings',
           'SisypheFunctionsSettings',
           'SisypheDialogsSettings',
           'SisypheTooltips']

"""
Functions
~~~~~~~~~

    - getUsername() -> str
    - getUserPath() -> str
    - getUserPySisyphePath() -> str
    - initPySisypheUserPath()
    - setUserSettingsToDefault()

Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheSettings -> SisypheFunctionsSettings
                                -> SisypheDialogsSettings
                                -> SisypheTooltips
"""

def getUsername() -> str:
    """
    Get username of the current session.

    Returns
    -------
    str
        username of the current session
    """
    system = sys.platform[:3]
    if system == 'dar': return environ['USER']
    elif system == 'win': return environ['USERNAME']
    else: raise OSError('{} system is not supported.'.format(sys.platform))


def getUserPath() -> str:
    """
    Get user path of the current session.

    Returns
    -------
    str
        user path of the current session
    """
    system = sys.platform[:3]
    if system == 'dar': return environ['HOME']
    elif system == 'win': return environ['USERPROFILE']
    else: raise OSError('{} system is not supported.'.format(sys.platform))


def getUserPySisyphePath() -> str:
    """
    Get PySisyphe user path of the current session.

    Returns
    -------
    str
        user PySisyphe path of the current session
    """
    path = join(getUserPath(), '.PySisyphe')
    if not exists(path): initPySisypheUserPath()
    return path


def initPySisypheUserPath() -> None:
    """
    Creates user PySisyphe directory. Creates database, models and segmentation subdirectories. Copy default xml files
    (settings.xml and functions.xml) to PySisyphe user directory.
    """
    path = join(getUserPath(), '.PySisyphe')
    if not exists(path): mkdir(path)
    # Controls directory
    # < Revision 30/10/2024
    # add controls directory
    path2 = join(path, 'controls')
    if not exists(path2): mkdir(path2)
    # Revision 30/10/2024 >
    # Database directory
    path2 = join(path, 'database')
    if not exists(path2): mkdir(path2)
    # Models directory
    path2 = join(path, 'models')
    if not exists(path2): mkdir(path2)
    xmls = glob(join(path2, '*.xml'))
    if len(xmls) > 0:
        for xml in xmls: copy(xml, path2)
    # Segmentation directory
    path2 = join(path, 'segmentation')
    if not exists(path2): mkdir(path2)
    xmls = glob(join(path2, '*.xml'))
    if len(xmls) > 0:
        for xml in xmls: copy(xml, path2)
    # Root
    import Sisyphe.settings
    path2 = dirname(abspath(Sisyphe.settings.__file__))
    file = join(path, 'settings.xml')
    if not exists(file):
        default = join(path2, 'settings.xml')
        copy(default, path)
    file = join(path, 'functions.xml')
    if not exists(file):
        default = join(path2, 'functions.xml')
        copy(default, path)


def setUserSettingsToDefault() -> None:
    """
    Copy default xml files (settings.xml and functions.xml) to PySisyphe user directory.
    """
    upath = getUserPySisyphePath()
    import Sisyphe.settings
    dpath = dirname(abspath(Sisyphe.settings.__file__))
    file = join(dpath, 'settings.xml')
    copy(file, upath)
    file = join(dpath, 'functions.xml')
    copy(file, upath)


fieldTypes = int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | QFont | None


class SisypheSettings(object):
    """
    SisypheSettings class

    Description
    ~~~~~~~~~~~

    Management of application settings from XML file (settings.xml by default).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheSettings

    Creation: 08/09/2022
    Last revisions: 15/03/2025
    """
    __slots__ = ['_doc', '_filename']

    # Class constants

    # < Revision 23/12/2024
    # add 'dcm' and 'dcms' var types
    _VARTYPES = ('str', 'vol', 'roi', 'dir', 'dcm',
                 'vols', 'rois', 'dcms', 'dirs', 'date',
                 'int', 'float', 'percent', 'bool',
                 'visibility', 'lstr', 'lint',
                 'lfloat', 'lbool', 'lut', 'color')
    # < Revision 23/12/2024

    _ATTRS = ('label', 'icon', 'vartype', 'varmin', 'varmax')

    # Class methods

    @classmethod
    def getDefaultSettings(cls) -> str:
        """
        Get default settings xml file name (./Sisyphe/settings/settings.xml).

        Returns
        -------
        str
            default settings xml file name
        """
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'settings.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        """
        Get user settings xml file name (~/.PySisyphe/settings/settings.xml). if user settings xml file does not exist,
        create it from a copy of the default xml file.

        Returns
        -------
        str
            user settings xml file name
        """
        path = join(getUserPySisyphePath(), 'settings.xml')
        if not exists(path):
            file = cls.getDefaultSettings()
            copy(file, getUserPySisyphePath())
        return path

    @classmethod
    def getAttributes(cls) -> tuple[str, ...]:
        """
        Get node attribute names of the xml settings file format.

        Returns
        -------
        tuple[str, ...]
            node attribute names
        """
        return cls._ATTRS

    @classmethod
    def isValidAttribute(cls, v: str) -> bool:
        """
        Check whether a str is a valid node attribute name of the xml settings file format.

        Parameters
        ----------
        v : str
            node attribute name to check

        Returns
        -------
        bool
            True if v is a valid node attribute name
        """
        return v.lower() in cls._ATTRS

    @classmethod
    def getVartypes(cls):
        """
        Get vartype names of the xml settings file format.

        Returns
        -------
        tuple[str, ...]
            vartype names
        """
        return cls._VARTYPES

    @classmethod
    def isValidVartype(cls, v: str) -> bool:
        """
        Check whether a str is a valid vartype name of the xml settings file format.

        Parameters
        ----------
        v : str
            vartype name to check

        Returns
        -------
        bool
            True if v is a valid vartype name
        """
        return v.lower() in cls._VARTYPES

    # Special methods

    """
    Private attributes

    _doc        minidom.Document
    _filename   str, xml filename if custom
    """

    def __init__(self, setting: str = 'user') -> None:
        """
        SisypheSettings instance constructor.

        Parameters
        ----------
        setting : str
            - 'user', load settings.xml from user path
            - 'default', load settings.xml from application ./settings path
            - 'xxx', load /user path/xxx.xml, xxx is a basename without extension
            - 'xxx', load xxx, xxx is a file name with absolute path and extension
            - creates empty xml if xxx does not exist
        """
        super().__init__()
        self._filename = ''
        # Load user settings
        if setting == 'user': self._doc = minidom.parse(self.getUserSettings())
        # Load default settings
        elif setting == 'default': self._doc = minidom.parse(self.getDefaultSettings())
        else:
            filename = join(getUserPySisyphePath(), '{}.xml'.format(setting))
            # Load custom settings in user path
            if exists(filename):
                self._doc = minidom.parse(filename)
                self._filename = filename
            # < revision 10/10/2024
            # Load custom settings
            elif exists(setting):
                self._doc = minidom.parse(setting)
                self._filename = setting
            # revision 10/10/2024 >
            # Create empty custom settings
            else:
                if setting == '': setting = 'settings'
                self._doc = minidom.Document()
                root = self._doc.createElement(setting)
                root.setAttribute('version', '1.0')
                self._doc.appendChild(root)
                self._filename = filename

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheSettings instance representation
        """
        return '{} class instance at <{}>\n'.format(self.__class__.__name__,
                                                    str(id(self)))

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheSettings instance to str
        """
        sections = self.getSectionsList()
        if self._filename != '': buff = '{}\n'.format(self._filename)
        else: buff = '{}\n'.format(self.getUserSettings())
        for section in sections:
            buff += '{}\n'.format(section)
            fields = self.getSectionFieldsList(section)
            for field in fields:
                buff += '  {}: {}\n'.format(field, self.getFieldValue(section, field))
        return buff

    def __getitem__(self, keyword: tuple[str, str]) -> fieldTypes:
        """
        Get the field value of the current SisypheSettings instance.

        Parameters
        ----------
        keyword : tuple[str, str]
            section and field names

        Returns
        -------
        int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | None
            vartype / return type, return type depends on the vartype of the field

                - 'str', str
                - 'vol', str
                - 'roi', str
                - 'dcm', str
                - 'dir', str
                - 'vols', list[str]
                - 'rois', list[str]
                - 'dcms', list[str]
                - 'dirs', list[str]
                - 'date', str
                - 'int', int
                - 'float', float
                - 'percent', float
                - 'bool', bool
                - 'visibility', bool
                - 'lstr', list[str]
                - 'lint', list[int]
                - 'lfloat', list[float]
                - 'lbool', list[bool]
                - 'color', list[float, float, float]
        """
        if isinstance(keyword, tuple):
            if len(keyword) == 2: return self.getFieldValue(keyword[0], keyword[1])
            else: raise KeyError('key tuple has {} key(s), two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    def __setitem__(self, keyword: tuple[str, str], v: fieldTypes) -> None:
        """
        Set the field value of the current SisypheSettings instance.

        Parameters
        ----------
        keyword : tuple[str, str]
            section and field names
        v : int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | None
            vartype / return type, type depends on the vartype of the field

                - 'str', str
                - 'vol', str
                - 'roi', str
                - 'dcm', str
                - 'dir', str
                - 'vols', list[str]
                - 'rois', list[str]
                - 'dcms', list[str]
                - 'dirs', list[str]
                - 'date', str
                - 'int', int
                - 'float', float
                - 'percent', float
                - 'bool', bool
                - 'visibility', bool
                - 'lstr', list[str]
                - 'lint', list[int]
                - 'lfloat', list[float]
                - 'lbool', list[bool]
                - 'color', list[float, float, float]
        """
        if isinstance(keyword, tuple):
            if len(keyword) == 2: self.setFieldValue(keyword[0], keyword[1], v)
            else: raise KeyError('key tuple has {} key(s), two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    def __contains__(self, keyword: tuple[str, str]) -> bool:
        """
        Check whether the current SisypheSettings instance contains a section/field key.

        Parameters
        ----------
        keyword : tuple[str, str]
            section and field names

        Returns
        -------
        bool
            True if section and field names are in the current SisypheSettings instance
        """
        if isinstance(keyword, tuple):
            if len(keyword) == 2: return self.hasField(keyword[0], keyword[1])
            else: raise IndexError('key tuple has {}, two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    # Public methods

    def isEmpty(self) -> int:
        """
        Check whether the current SisypheSettings instance is empty (No section and no field).

        Returns
        -------
        bool
            True is empty
        """
        return len(self.getSectionsList())

    def getSectionsList(self) -> list[str]:
        """
        Get the section list of the current SisypheSettings instance.

        Returns
        -------
        list[str]
            list of sections
        """
        r = list()
        node = self._doc.documentElement.firstChild
        while node:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                r.append(node.nodeName)
            node = node.nextSibling
        return r

    def newSection(self, section: str):
        """
        Create a new section in the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        """
        if not self.hasSection(section):
            root = self._doc.documentElement
            root.appendChild(self._doc.createElement(section))

    def hasSection(self, section: str) -> bool:
        """
        Check whether the current SisypheSettings instance contains a section.

        Parameters
        ----------
        section : str
            section name

        Returns
        -------
        bool
            True if section is defined
        """
        sections = self.getSectionsList()
        return section in sections

    def getSectionNode(self, section: str) -> minidom.Element | None:
        """
        Get a section node (minidom.Element) from the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name

        Returns
        -------
        minidom.Element | None
            section node
        """
        node = self._doc.documentElement.firstChild
        while node:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                if node.nodeName == section: return node
            node = node.nextSibling
        return None

    def getSectionFieldsList(self, section: str) -> list[str]:
        """
        Get the list of fields in a section of the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name

        Returns
        -------
        list[str]
            list of fields in a section
        """
        r = list()
        node = self.getSectionNode(section)
        if node:
            child = node.firstChild
            while child:
                if child.nodeType == minidom.Node.ELEMENT_NODE:
                    r.append(child.nodeName)
                child = child.nextSibling
        return r

    def newField(self, section: str, field: str, attrs: dict):
        """
        Create a new field in a section of the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name
        attrs : dict
            dict keys are field attributes

                - 'label', str, optional label displayed in the gui widget
                - 'icon', str, required for 'visibility' vartype, bitmap file name (.png) in ./Sisyphe/gui/darkicons or ./Sisyphe/gui/lighticons folder
                - 'vartype', str, always required, field vartypes are 'str', 'vol', 'roi', 'dir', 'vols', 'rois', 'dirs', 'date', 'int', 'float', 'percent', 'bool', 'visibility', 'lstr', 'lint', 'lfloat', 'lbool', 'color'
                - 'varmin', int | float, optional, minimum field value (for 'int' or 'float' vartype)
                - 'varmax', int | float, optional, maximum field value (for 'int' or 'float' vartype)
                - 'step', int, optional, step of the associated QSpinbox widget
        """
        if not self.hasField(section, field):
            node = self.getSectionNode(section)
            fieldnode = self._doc.createElement(field)
            if len(attrs) > 0:
                for attr in attrs:
                    if attr in ('label', 'icon', 'vartype', 'varmin', 'varmax', 'step'):
                        attrnode = self._doc.createAttribute(attr)
                        fieldnode.setAttributeNode(attrnode)
                        fieldnode.setAttribute(attr, attrs[attr])
                    else: raise ValueError('{} incorrect attribute.')
                txtnode = self._doc.createTextNode('')
                fieldnode.appendChild(txtnode)
                node.appendChild(fieldnode)

    def hasField(self, section: str, field: str) -> bool:
        """
        Check whether the current SisypheSettings instance contains a section/field key.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name

        Returns
        -------
        bool
            True if section/field are defined
        """
        fields = self.getSectionFieldsList(section)
        return field in fields

    def getFieldNode(self, section: str, field: str) -> minidom.Element | None:
        """
        Get a field node (minidom.Element) from the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name

        Returns
        -------
        minidom.Element | None
            section node
        """
        nodes = self._doc.getElementsByTagName(field)
        if nodes.length > 0:
            for node in nodes:
                if node.parentNode.nodeName == section: return node
        return None

    def getFieldVartype(self, section: str, field: str) -> str:
        """
        Get the vartype of a field in the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name

        Returns
        -------
        str
            field vartype, vartypes are :

            - 'str': str
            - 'vol': str, PySisyphe volume filename
            - 'roi': str, PySisyphe ROI filename
            - 'dcm': str, DICOM filename
            - 'dir': str, path name
            - 'vols': list[str], list of PySisyphe volume filenames
            - 'rois': list[str], list of PySisyphe ROI filenames
            - 'dcms': list[str], list of DICOM filenames
            - 'dirs': list[str], list of path names
            - 'date': str, format 'DDMMYYYY'
            - 'int': int
            - 'float': float
            - 'percent': float, percent value between 0.0 and 100.0
            - 'bool': bool
            - 'visibility': bool
            - 'lstr': list[str]
            - 'lint': list[int]
            - 'lfloat': list[float]
            - 'lbool': list[bool]
            - 'lut': str, lut name
            - 'color': list[float, float, float], each float between 0.0 and 1.0
            - 'font': str, font name
            - 'txt', str text file name (in ./Sisyphe/doc folder if path attribute is not defined)
        """
        node = self.getFieldNode(section, field)
        if node is not None: return node.getAttribute('vartype')
        else: raise ValueError('Invalid node.')

    def getFieldValue(self, section: str, field: str) -> fieldTypes:
        """
        Get the value of a field in the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name

        Returns
        -------
        int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | None
            vartype / return type, return type depends on the field vartype

                - 'str', str
                - 'vol', str
                - 'roi', str
                - 'dcm', str
                - 'dir', str
                - 'vols', list[str]
                - 'rois', list[str]
                - 'dcms', list[str]
                - 'dirs', list[str]
                - 'date', str
                - 'int', int
                - 'float', float
                - 'percent', float
                - 'bool', bool
                - 'visibility', bool
                - 'lstr', list[str]
                - 'lint', list[int]
                - 'lfloat', list[float]
                - 'lbool', list[bool]
                - 'lut', str
                - 'color', list[float, float, float]
                - 'font', str
                - 'txt', str text file name (in ./Sisyphe/doc folder if path attribute is not defined)
        """
        node = self.getFieldNode(section, field)
        if node is not None:
            vartype = node.getAttribute('vartype')
            if node.hasChildNodes():
                child = node.firstChild
                # noinspection PyUnresolvedReferences
                data = child.data
                # < Revision 23/12/2024
                # add 'dcm' var type
                # add 'font' var type
                # if vartype in ('str', 'dir', 'vol', 'roi', 'date', 'lut'): return data
                if vartype in ('str', 'dir', 'vol', 'roi', 'dcm', 'date', 'lut', 'font'): return data
                # Revision 23/12/2024 >
                elif vartype == 'int': return int(data)
                elif vartype in ('float', 'percent'): return float(data)
                elif vartype in ('bool', 'visibility'): return bool(data == 'True')
                # < Revision 23/12/2024
                # add 'dcms' var type
                # elif vartype in ('lstr', 'dirs', 'vols', 'rois'): return data.split('|')
                elif vartype in ('lstr', 'dirs', 'vols', 'dcms', 'rois'): return data.split('|')
                # Revision 23/12/2024 >
                elif vartype == 'lint': return [int(i) for i in data.split()]
                elif vartype in ('lfloat', 'color'): return [float(i) for i in data.split()]
                elif vartype == 'lbool': return [bool(i == 'True') for i in data.split()]
                # < Revision 6/10/2024
                elif vartype == 'txt':
                    path = node.getAttribute('path')
                    if path is None:
                        import Sisyphe.gui
                        path = join(dirname(abspath(Sisyphe.gui.__file__)), 'doc')
                    filename = join(path, data)
                    r = ''
                    if exists(filename) and isfile(filename):
                        f = open(filename, 'r')
                        try: r = f.readlines()
                        except:
                            f.close()
                    return r
                # Revision 6/10/2024 >
                else: return data
            elif vartype in ('str', 'dir', 'vol', 'roi', 'dcm', 'dirs', 'vols', 'rois', 'dcms', 'date'): return ''
            elif vartype == 'font': return 'Arial'
        return None

    def setFieldValue(self, section: str, field: str, v: fieldTypes) -> None:
        """
        Set the field value of the current SisypheSettings instance.

        Parameters
        ----------
        section : str
            section name
        field : str
            field name
        v : int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | None
            field value, type depends on the vartype of the field

                - 'str', str
                - 'vol', str
                - 'roi', str
                - 'dcm', str
                - 'dir', str
                - 'vols', list[str]
                - 'rois', list[str]
                - 'dcms', list[str]
                - 'dirs', list[str]
                - 'date', str
                - 'int', int
                - 'float', float
                - 'percent', float
                - 'bool', bool
                - 'visibility', bool
                - 'lstr', list[str]
                - 'lint', list[int]
                - 'lfloat', list[float]
                - 'lbool', list[bool]
                - 'lut', str
                - 'color', list[float, float, float]
                - 'font', str | QFont
                - 'txt', str, text file name (in ./Sisyphe/doc folder if path attribute is not defined)
        """
        node = self.getFieldNode(section, field)
        if node is not None:
            vartype = node.getAttribute('vartype')
            # < Revision 23/12/2024
            # add 'dcm' var type
            # if vartype in ('str', 'vol', 'roi', 'dir', 'lut'):
            if vartype in ('str', 'vol', 'roi', 'dcm', 'dir', 'lut'):
                if v is None: v = ''
            # < Revision 15/03/2025
            # add font type
            elif vartype == 'font':
                # < Revision 16/03/2025
                if isinstance(v, QFont): v = v.family()
                # Revision 16/03/2025 >
                if v is None: v = 'Arial'
                else:
                    database = QFontDatabase()
                    if v not in database.families():
                        raise ValueError('{} invalid font family.'.format(v))
            # Revision 15/03/2025 >
            # Revision 23/12/2024 >
            elif vartype == 'date':
                if isinstance(v, datetime): v = v.date()
                if isinstance(v, date): v = v.strftime('%Y-%m-%d')
                if isinstance(v, str):
                    try: _ = datetime.strptime(v, '%Y-%m-%d')
                    except: TypeError('parameter type {} is not date, datetime or str formatted date.'.format(type(v)))
            elif vartype == 'int':
                if not isinstance(v, int):
                    raise TypeError('parameter type {} is not int'.format(v))
                v = str(v)
            elif vartype == 'float':
                if not isinstance(v, float): raise TypeError('parameter type {} is not float'.format(type(v)))
                v = str(v)
            elif vartype == 'percent':
                if not isinstance(v, float): raise TypeError('parameter type {} is not float'.format(type(v)))
                if v < 0.0 or v > 1.0: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
                v = str(v)
            elif vartype in ('bool', 'visibility'):
                if not isinstance(v, bool): raise TypeError('parameter type {} is not bool'.format(type(v)))
                v = str(v)
            # < Revision 23/12/2024
            # add 'dcms' var type
            # elif vartype in ('lstr', 'dirs', 'vols', 'rois'):
            elif vartype in ('lstr', 'dirs', 'vols', 'dcms', 'rois'):
                if isinstance(v, list) and not all([isinstance(i, str) for i in v]):
                    raise TypeError('parameter type {} is not a list of str'.format(type(v)))
                if v is None: v = ''
                else: v = '|'.join(v)
            # Revision 23/12/2024 >
            elif vartype == 'lint':
                if isinstance(v, list) and not all([isinstance(i, int) for i in v]):
                    raise TypeError('parameter type {} is not a list of int'.format(type(v)))
                v = ' '.join([str(i) for i in v])
            elif vartype in ('lfloat', 'color'):
                if isinstance(v, list) and not all([isinstance(i, float) for i in v]):
                    raise TypeError('{} parameter type {} is not a list of float'.format(v, type(v)))
                if vartype == 'color' and len(v) != 3:
                    raise ValueError('incorrect items count ({}) for color.'.format(len(v)))
                v = ' '.join([str(i) for i in v])
            # < Revision 15/03/2025
            elif vartype == 'txt':
                path = split(v)
                if path[0] == '':
                    import Sisyphe.gui
                    doc = join(dirname(abspath(Sisyphe.gui.__file__)), 'doc')
                    v = join(doc, v)
                if exists(v) and isfile(v):
                    if path[0] != '': node.setAttribute('path', path[0])
                    v = path[1]
                else: raise ValueError('No such file {}'.format(v))
            # Revision 15/03/2025 >
            else: raise KeyError('Unknown vartype {}.'.format(vartype))
            if node.hasChildNodes(): node.firstChild.data = v
            else:
                child = self._doc.createTextNode(v)
                node.appendChild(child)
        else: raise KeyError('Key ({},{}) is not found.'.format(section, field))

    # < Revision 13/02/2025
    # add fieldsToDict method
    def fieldsToDict(self, section: str) -> dict[str, fieldTypes]:
        """
        Copy section fields of the current SisypheSettings instance into a dict.

        Returns
        -------
        dict
            dict keys are field names, and dict values are field values
        """
        keys = self.getSectionFieldsList(section)
        d = dict()
        for k in keys:
            d[k] = self.getFieldValue(section, k)
        return d
    # Revision 13/02/2025 >

    # < Revision 13/02/2025
    # add fieldsFromDict method
    def fieldsFromDict(self, section: str, fields: dict[str, fieldTypes]):
        """
        Copy section field values of the current SisypheSettings instance from a dict.

        Parameters
        ----------
        section : str
            section name
        fields : dict
            dict keys are field names, and dict values are field values
        """
        keys = list(fields.keys())
        for k in keys:
            if self.hasField(section, k):
                self.setFieldValue(section, k, fields[k])
    # Revision 13/02/2025 >

    def loadCustomFileSettings(self, filename: str) -> None:
        """
        Load the current SisypheSettings from a custom xml settings file.

        Parameters
        ----------
        filename : str
            custom xml settings file name, filename becomes the current save name used by save() method and the
            instance becomes custom
        """
        if exists(filename):
            try:
                self._doc = minidom.parse(filename)
                self._filename = abspath(filename)
            except:
                self._doc = minidom.parse(self.getUserSettings())
                self._filename = ''
        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))

    def loadUserFileSettings(self) -> None:
        """
        Load the current SisypheSettings from the user settings file (~/.PySisyphe/settings/settings.xml).
        """
        self._doc = minidom.parse(self.getUserSettings())
        self._filename = ''

    def loadDefaultFileSettings(self) -> None:
        """
        Load the current SisypheSettings from the default settings file (./Sisyphe/settings/settings.xml).
        """
        self._doc = minidom.parse(self.getDefaultSettings())
        self._filename = ''

    def isCustom(self) -> bool:
        """
        Check whether the current SisypheSettings is a custom settings instance. In this case, the associated xml
        settings file is defined in a custom save name attribute.

        Returns
        -------
        bool
            True if custom save name attribute is defined
        """
        return self._filename != ''

    def isUser(self) -> bool:
        """
        Check whether the current SisypheSettings is a user settings instance. In this case, the associated xml
        settings file is ~/.PySisyphe/settings/settings.xml and the custom save name attribute is empty ('').

        Returns
        -------
        bool
            True if custom save name attribute is empty
        """
        return self._filename == ''

    def getFilename(self) -> str:
        """
        Get the custom save name of the current SisypheSettings instance. Save name is only defined in a custom
        instance. Save name is empty in a user instance.

        Returns
        -------
        str
            xml file name
        """
        return self._filename

    def save(self) -> None:
        """
        Save the current SisypheSettings instance. In case of custom instance, saved with the custom save name
        attribute. In case of user instance, saved in ~/.PySisyphe/settings/settings.xml.
        """
        if self.isCustom(): filename = self._filename
        else: filename = self.getUserSettings()
        self.saveAs(filename, current=False)

    def saveToDefault(self) -> None:
        """
        Save the current SisypheSettings instance to the default settings file. It is not recommended, because the
        original settings are lost and the file may be corrupted (./Sisyphe/settings/settings.xml).
        """
        self.saveAs(self.getDefaultSettings(), current=False)

    def saveAs(self, filename: str, current: bool = True, pretty: bool = False) -> None:
        """
        Save the current SisypheSettings instance to a xml file.

        Parameters
        ----------
        filename : str
            xml file name
        current : bool
            if True, filename becomes the current save name used by save() method and the instance becomes custom
        pretty : bool
            if True, pretty xml formatting
        """
        if pretty: xml = self._doc.toprettyxml()
        else: xml = self._doc.toxml()
        with open(filename, 'w') as f:
            f.write(xml)
        if current: self._filename = filename


class SisypheFunctionsSettings(SisypheSettings):
    """
    SisypheFunctionsSettings class

    Description
    ~~~~~~~~~~~

    Management of application function settings from XML file (functions.xml by default).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheSettings -> SisypheFunctionsSettings

    Creation: 08/09/2022
    Last revision: 15/12/2023
    """
    # Class method

    @classmethod
    def getDefaultSettings(cls) -> str:
        """
        Get default function settings xml file name (./Sisyphe/settings/functions.xml).

        Returns
        -------
        str
            default function settings xml file name
        """
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'functions.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        """
        Get user function settings xml file name (~/.PySisyphe/settings/functions.xml). If user function settings xml
        file does not exist, create it from a copy of the default xml file.

        Returns
        -------
        str
            user function settings xml file name
        """
        path = join(getUserPySisyphePath(), 'functions.xml')
        if not exists(path):
            file = cls.getDefaultSettings()
            copy(file, getUserPySisyphePath())
        return path

    # Special methods

    def __init__(self) -> None:
        """
        SisypheFunctionsSettings instance constructor.
        """
        super().__init__()


class SisypheDialogsSettings(SisypheSettings):
    """
    SisypheDialogsSettings class

    Description
    ~~~~~~~~~~~

    Management of application dialogs from XML file (dialogs.xml by default).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheSettings -> SisypheDialogsSettings

    Creation: 08/09/2022
    Last Revision: 15/12/2023
    """
    # Class method

    @classmethod
    def getDefaultSettings(cls) -> str:
        """
        Get default dialog settings xml file name (./Sisyphe/settings/dialogs.xml').

        Returns
        -------
        str
            default dialog settings xml file name
        """
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'dialogs.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        """
        Get user dialog settings xml file name (~/.PySisyphe/settings/dialogs.xml').

        Returns
        -------
        str
            user dialog settings xml file name
        """
        return cls.getDefaultSettings()

    # Special methods

    def __init__(self) -> None:
        """
        SisypheDialogsSettings instance constructor.
        """
        super().__init__()


class SisypheTooltips(SisypheSettings):
    """
    SisypheTooltips class

    Description
    ~~~~~~~~~~~

    Management of function tooltips from XML file (tooltips.xml by default).

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheSettings -> SisypheTooltips

    Creation: 05/10/2024
    """
    # Class method

    @classmethod
    def getDefaultSettings(cls) -> str:
        """
        Get tooltips xml file name (./Sisyphe/settings/tooltips.xml).

        Returns
        -------
        str
            tooltips xml file name
        """
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'tooltips.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        """
        Get user dialog settings xml file name (~/.PySisyphe/settings/dialogs.xml').

        Returns
        -------
        str
            user dialog settings xml file name
        """
        return cls.getDefaultSettings()

    # Special methods

    def __init__(self) -> None:
        """
        SisypheTooltips instance constructor.
        """
        super().__init__()
