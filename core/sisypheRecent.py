"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import mkdir
from os.path import join
from os.path import exists
from os.path import basename
from os.path import expanduser
from os.path import splitext

from xml.dom import minidom

from PyQt5.QtWidgets import QMenu

from Sisyphe.core.sisypheVolume import SisypheVolume

__all__ = ['SisypheRecent']

"""
    Class hierarchy

        object -> SisypheRecent

    Description

        Manage recently opened files.
"""


class SisypheRecent(object):
    """
        SisypheRecent

        Description

            Manage recently opened files.

        Inheritance

            object ->   SisypheRecent

        Private attributes

            _files  list of strings
            _max    maximum size of _file

        Public methods

            setMaximumCount(int)
            int = getMaximumCount()
            int = getFileCount()
            list = getFileList()
            append(str)
            clear()
            save()
            load()
            updateQMenu(QMenu)

        Creation: 27/10/2022
        Revisions:

            31/08/2023  type hinting
    """
    __slots__ = ['_max', '_files']

    # Class method

    @classmethod
    def getUserDirectory(cls) -> str:
        userdir = join(expanduser('~'), '.PySisyphe')
        if not exists(userdir): mkdir(userdir)
        return userdir

    # Special method

    def __init__(self, n: int = 10) -> None:
        super().__init__()

        self._max = n
        self._files = list()

    def __str__(self) -> str:
        buff = 'Recent files:\n'
        if len(self._files) > 0:
            for file in self._files:
                buff += '   {}\n'.format(file)
        else: buff += 'Empty'
        return buff

    def __repr__(self) -> str:
        return 'SisypheRecent instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setMaximumCount(self, n: int):
        if isinstance(n, int):
            if n > 0: self._max = n
            else: raise ValueError('parameter value {} must be positive.'.format(n))
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def getMaximumCount(self) -> int:
        return self._max

    def getFileCount(self) -> int:
        return len(self._files)

    def getFileList(self) -> list[str]:
        return self._files

    def append(self, filename: str) -> None:
        if exists(filename):
            ext = splitext(filename)[1]
            if ext == SisypheVolume.getFileExt():
                if filename not in self._files:
                    if len(self._files) >= self._max: del self._files[0]
                    self._files.append(filename)
                else:
                    # if already in list, becomes last element of the list
                    index = self._files.index(filename)
                    self._files.pop(index)
                    self._files.append(filename)
            else: raise IOError('{} is not PySisyphe *{}'.format(filename, SisypheVolume.getFileExt()))

    def clear(self) -> None:
        self._files.clear()

    def save(self) -> None:
        doc = minidom.Document()
        root = doc.createElement('recent')
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        if len(self._files) > 0:
            for file in self._files:
                if exists(file):
                    node = doc.createElement('file')
                    root.appendChild(node)
                    txt = doc.createTextNode(file)
                    node.appendChild(txt)
        xml = doc.toprettyxml()
        filename = join(self.getUserDirectory(), 'recent.xml')
        with open(filename, 'w') as f:
            f.write(xml)

    def load(self) -> None:
        filename = join(self.getUserDirectory(), 'recent.xml')
        if exists(filename):
            self._files.clear()
            doc = minidom.parse(filename)
            nodes = doc.getElementsByTagName('file')
            if nodes.length > 0:
                for node in nodes:
                    if node.hasChildNodes():
                        child = node.firstChild
                        data = child.data
                        if exists(data): self.append(data)
        else: raise IOError('No such file {}'.format(filename))

    def updateQMenu(self, menu: QMenu) -> None:
        if isinstance(menu, QMenu):
            menu.clear()
            if len(self._files) > 0:
                c = False
                for file in reversed(self._files):
                    if exists(file):
                        action = menu.addAction(basename(file))
                        action.setData(file)
                        c = True
                if c:
                    menu.addSeparator()
                    menu.addAction('Clear')
        else: raise TypeError('parameter type {} is not QMenu.'.format(type(menu)))
