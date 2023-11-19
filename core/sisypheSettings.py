"""
    No external package or module
"""

import sys

from os import environ
from os import mkdir

from shutil import copy

from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import basename
from os.path import exists

from glob import glob

from datetime import date
from datetime import datetime

from xml.dom import minidom


__all__ = ['getUsername',
           'getUserPath',
           'getUserPySisyphePath',
           'initPySisypheUserPath',
           'setUserSettingsToDefault',
           'SisypheSettings',
           'SisypheFunctionsSettings',
           'SisypheDialogsSettings']

"""
    Functions
    
        getUsername
        getUserPath
        getUserSettingsPath
        initPySisypheUserPath
        
    Revisions:
    
        31/08/2023  type hinting
"""


def getUsername() -> str:
    """
        Return username of the current session
    """
    system = sys.platform[:3]
    if system == 'dar': return environ['USER']
    elif system == 'win': return environ['USERNAME']
    else: raise OSError('{} system is not supported.'.format(sys.platform))


def getUserPath() -> str:
    """
        Return user path of the current session
    """
    system = sys.platform[:3]
    if system == 'dar': return environ['HOME']
    elif system == 'win': return environ['USERPROFILE']
    else: raise OSError('{} system is not supported.'.format(sys.platform))


def getUserPySisyphePath() -> str:
    """
        Return user PySisyphe path of the current session
    """
    path = join(getUserPath(), '.PySisyphe')
    if not exists(path): initPySisypheUserPath()
    return path


def initPySisypheUserPath() -> None:
    """
        Creates user PySisyphe directory.
        Creates database and models subdirectories.
        Copy default xml files to user PySisyphe directory.
    """
    path = join(getUserPath(), '.PySisyphe')
    if not exists(path): mkdir(path)
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
        Copy default xml files to user PySisyphe directory.
    """
    upath = getUserPySisyphePath()
    import Sisyphe.settings
    dpath = dirname(abspath(Sisyphe.settings.__file__))
    file = join(dpath, 'settings.xml')
    copy(file, upath)
    file = join(dpath, 'functions.xml')
    copy(file, upath)


"""
    Class hierarchy

        object  -> SisypheSettings  -> SisypheFunctionsSettings 
                                    -> SisypheDialogsSettings 
"""

fieldTypes = int | float | bool | str | list[int] | list[float] | list[bool] | list[str] | None

class SisypheSettings(object):
    """
        SisypheSettings class

        Description

            Management of application settings from XML file (settings.xml by default).

        Inheritance

            object -> SisypheSettings

        Private attributes

            _doc        minidom.Document
            _filename   str, xml filename if custom

        Class methods

            str = getDefaultSettings()
            str = getUserSettings()
            list[str] = getAttributes()
            bool = isValidAttribute(str)
            list[str] = getVartypes()
            bool = isValidVartype(str)

        Public methods

            __getitem__(str, str)
            __setitem__(str, str, int | float | bool | str | list)
            __contain__(str, str)
            int = isEmpty()
            getSectionsList() -> list[str]
            newSection(str)
            hasSection(str) -> bool
            getSectionNode(str) -> minidom.Element | None
            getSectionFieldsList(str) -> list[str]
            newField(str, str, dict)
            hasField(str, str) -> bool
            getFieldNode(str, str) -> minidom.Element | None
            str = getFieldVartype(str, str)
            int | float | bool | str | list = getFieldValue(str, str) -> int | float | bool | str | list
            setFieldValue(str, str, int | float | bool | str | list) -> None
            loadCustomFileSettings(str) -> None
            loadUserFileSettings() -> None
            loadDefaultFileSettings() - > None
            isCustom() -> bool
            isUser() -> bool
            getFilename() -> str
            save() -> None
            saveToDefault() -> None
            saveAs(str, bool=True) -> None

            inherited object methods

        Creation: 08/09/2022
        Revisions:

            22/06/2023  add setting parameter (='user' by default) to constructor method
            22/06/2023  add newSection, newField, getFieldVartype methods
            31/08/2023  type hinting
    """
    __slots__ = ['_doc', '_filename']

    # Class constants

    _VARTYPES = ('str', 'vol', 'roi', 'dir',
                 'vols', 'rois', 'dirs', 'date',
                 'int', 'float', 'percent', 'bool',
                 'visibility', 'lstr', 'lint',
                 'lfloat', 'lbool', 'color')

    _ATTRS = ('label', 'icon', 'vartype', 'varmin', 'varmax')

    # Class methods

    @classmethod
    def getDefaultSettings(cls) -> str:
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'settings.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        path = join(getUserPySisyphePath(), 'settings.xml')
        if not exists(path):
            file = cls.getDefaultSettings()
            copy(file, getUserPySisyphePath())
        return path

    @classmethod
    def getAttributes(cls):
        return cls._ATTRS

    @classmethod
    def isValidAttribute(cls, v: str) -> bool:
        return v.lower() in cls._ATTRS

    @classmethod
    def getVartypes(cls):
        return cls._VARTYPES

    @classmethod
    def isValidVartype(cls, v: str) -> bool:
        return v.lower() in cls._VARTYPES

    # Special methods

    def __init__(self, setting: str = 'user') -> None:
        """
            Parameter

                setting     str,
                            'user', load settings.xml from user path
                            'default', load settings.xml from application ./settings path
                            'xxx', load xxx.xml from user path or creates empty xml if xxx does not exist
        """
        super().__init__()
        self._filename = ''
        filename = join(getUserPySisyphePath(), '{}.xml'.format(setting))
        # Load user settings
        if setting == 'user': self._doc = minidom.parse(self.getUserSettings())
        # Load default settings
        elif setting == 'default': self._doc = minidom.parse(self.getDefaultSettings())
        # Load custom settings
        elif exists(filename):
            self._doc = minidom.parse(filename)
            self._filename = filename
        # Create empty custom settings
        else:
            self._doc = minidom.Document()
            root = self._doc.createElement(setting)
            root.setAttribute('version', '1.0')
            self._doc.appendChild(root)
            self._filename = filename

    def __repr__(self) -> str:
        return '{} class instance at <{}>\n'.format(self.__class__.__name__,
                                                    str(id(self)))

    def __str__(self) -> str:
        sections = self.getSectionsList()
        if self._filename != '': buff = '{}\n'.format(self._filename)
        else: buff = '{}\n'.format(self.getUserSettings())
        for section in sections:
            buff += '{}\n'.format(section)
            fields = self.getSectionFieldsList(section)
            for field in fields:
                buff += '  {}: {}\n'.format(field, self.getFieldValue(section, field))
        return buff

    def __getitem__(self, keyword: tuple[str]) -> fieldTypes:
        if isinstance(keyword, tuple):
            if len(keyword) == 2: return self.getFieldValue(keyword[0], keyword[1])
            else: raise KeyError('key tuple has {} key(s), two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    def __setitem__(self, keyword: tuple[str], v: fieldTypes) -> None:
        if isinstance(keyword, tuple):
            if len(keyword) == 2: self.setFieldValue(keyword[0], keyword[1], v)
            else: raise KeyError('key tuple has {} key(s), two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    def __contains__(self, keyword: tuple[str]) -> bool:
        if isinstance(keyword, tuple):
            if len(keyword) == 2: return self.hasField(keyword[0], keyword[1])
            else: raise IndexError('key tuple has {}, two expected.'.format(len(keyword)))
        else: raise TypeError('key type {} is not tuple.'.format(type(keyword)))

    # Public methods

    def isEmpty(self) -> int:
        return len(self.getSectionsList())

    def getSectionsList(self) -> list[str]:
        r = list()
        node = self._doc.documentElement.firstChild
        while node:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                r.append(node.nodeName)
            node = node.nextSibling
        return r

    def newSection(self, section: str):
        if not self.hasSection(section):
            root = self._doc.documentElement
            root.appendChild(self._doc.createElement(section))

    def hasSection(self, section: str) -> bool:
        sections = self.getSectionsList()
        return section in sections

    def getSectionNode(self, section: str) -> minidom.Element | None:
        node = self._doc.documentElement.firstChild
        while node:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                if node.nodeName == section: return node
            node = node.nextSibling
        return None

    def getSectionFieldsList(self, section: str) -> list[str]:
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
        if not self.hasField(section, field):
            node = self.getSectionNode(section)
            fieldnode = self._doc.createElement(field)
            if len(attrs) > 0:
                for attr in attrs:
                    if attr in ('label', 'icon', 'vartype', 'varmin', 'varmax'):
                        attrnode = self._doc.createAttribute(attr)
                        fieldnode.setAttributeNode(attrnode)
                        fieldnode.setAttribute(attr, attrs[attr])
                    else: raise ValueError('{} incorrect attribute.')
                txtnode = self._doc.createTextNode('')
                fieldnode.appendChild(txtnode)
                node.appendChild(fieldnode)

    def hasField(self, section: str, field: str) -> bool:
        fields = self.getSectionFieldsList(section)
        return field in fields

    def getFieldNode(self, section: str, field: str) -> minidom.Element | None:
        nodes = self._doc.getElementsByTagName(field)
        if nodes.length > 0:
            for node in nodes:
                if node.parentNode.nodeName == section: return node
        return None

    def getFieldVartype(self, section: str, field: str) -> str:
        node = self.getFieldNode(section, field)
        if node is not None: return node.getAttribute('vartype')

    def getFieldValue(self, section: str, field: str) -> fieldTypes:
        node = self.getFieldNode(section, field)
        if node is not None:
            vartype = node.getAttribute('vartype')
            if node.hasChildNodes():
                child = node.firstChild
                data = child.data
                if vartype in ('str', 'dir', 'vol', 'roi', 'date'): return data
                elif vartype == 'int': return int(data)
                elif vartype in ('float', 'percent'): return float(data)
                elif vartype in ('bool', 'visibility'): return bool(data == 'True')
                elif vartype in ('lstr', 'dirs', 'vols', 'rois'): return data.split('|')
                elif vartype == 'lint': return [int(i) for i in data.split()]
                elif vartype in ('lfloat', 'color'): return [float(i) for i in data.split()]
                elif vartype == 'lbool': return [bool(i == 'True') for i in data.split()]
            elif vartype in ('str', 'dir', 'vol', 'roi', 'dirs', 'vols', 'rois', 'date'): return ''
        return None

    def setFieldValue(self, section: str, field: str, v: fieldTypes):
        node = self.getFieldNode(section, field)
        if node is not None:
            vartype = node.getAttribute('vartype')
            if vartype in ('str', 'vol', 'roi', 'dir'): pass
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
            elif vartype in ('lstr', 'dirs', 'vols', 'rois'):
                if isinstance(v, list) and not all([isinstance(i, str) for i in v]):
                    raise TypeError('parameter type {} is not a list of str'.format(type(v)))
                v = '|'.join(v)
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
            else: raise KeyError('Unknown vartype {}.'.format(vartype))
            if node.hasChildNodes(): node.firstChild.data = v
            else:
                child = self._doc.createTextNode(v)
                node.appendChild(child)
        else: raise KeyError('Key ({},{}) is not found.'.format(section, field))

    def loadCustomFileSettings(self, filename: str) -> None:
        if exists(filename):
            try:
                self._doc = minidom.parse(filename)
                self._filename = abspath(filename)
            except:
                self._doc = minidom.parse(self.getUserSettings())
                self._filename = ''
        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))

    def loadUserFileSettings(self) -> None:
        self._doc = minidom.parse(self.getUserSettings())
        self._filename = ''

    def loadDefaultFileSettings(self) -> None:
        self._doc = minidom.parse(self.getDefaultSettings())
        self._filename = ''

    def isCustom(self) -> bool:
        return self._filename != ''

    def isUser(self) -> bool:
        return self._filename == ''

    def getFilename(self) -> str:
        return self._filename

    def save(self) -> None:
        if self.isCustom(): filename = self._filename
        else: filename = self.getUserSettings()
        self.saveAs(filename, current=False)

    def saveToDefault(self) -> None:
        self.saveAs(self.getDefaultSettings(), current=False)

    def saveAs(self, filename: str, current: bool = True) -> None:
        xml = self._doc.toxml()
        # xml = self._doc.toprettyxml()
        with open(filename, 'w') as f:
            f.write(xml)
        if current: self._filename = filename


class SisypheFunctionsSettings(SisypheSettings):
    """
        SisypheFunctionsSettings class

        Description

            Management of application function settings from XML file (functions.xml by default).

        Inheritance

            object -> SisypheSettings -> SisypheFunctionsSettings

        Private attributes

        Public methods

            inherited SisypheSettings methods
            inherited object methods

        Creation: 08/09/2022
        Revisions:

            31/08/2023  type hinting
    """
    # Class method

    @classmethod
    def getDefaultSettings(cls) -> str:
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'functions.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        path = join(getUserPySisyphePath(), 'functions.xml')
        if not exists(path):
            file = cls.getDefaultSettings()
            copy(file, getUserPySisyphePath())
        return path

    # Special methods

    def __init__(self) -> None:
        super().__init__()


class SisypheDialogsSettings(SisypheSettings):
    """
        SisypheDialogsSettings class

        Description

            Dialogs from XML file (dialogs.xml by default).

        Inheritance

            object -> SisypheSettings -> SisypheDialogsSettings

        Private attributes

        Public methods

            inherited SisypheSettings methods
            inherited object methods

        Creation: 08/09/2022
        Revisions:

            31/08/2023  type hinting
    """
    # Class method

    @classmethod
    def getDefaultSettings(cls) -> str:
        import Sisyphe.settings
        return join(dirname(abspath(Sisyphe.settings.__file__)), 'dialogs.xml')

    @classmethod
    def getUserSettings(cls) -> str:
        return cls.getDefaultSettings()

    # Special methods

    def __init__(self) -> None:
        super().__init__()
