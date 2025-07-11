"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
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
~~~~~~~~~~~~~~~

    - object -> SisypheRecent
"""

class SisypheRecent(object):
    """
    SisypheRecent class

    Description
    ~~~~~~~~~~~

    Manage a persistent list of recently opened files. It includes methods for adding, removing, and retrieving files
    from the list, as well as saving and loading the list to/from an XML file.

    Inheritance
    ~~~~~~~~~~~

    object ->   SisypheRecent

    Creation: 27/10/2022
    Last revision: 14/12/2023
    """
    __slots__ = ['_max', '_files']

    # Class method

    @classmethod
    def getUserDirectory(cls) -> str:
        """
        Get user directory (~/.PySisyphe)

        Returns
        -------
        str
            '~/.PySisyphe'
        """
        userdir = join(expanduser('~'), '.PySisyphe')
        if not exists(userdir): mkdir(userdir)
        return userdir

    # Special method

    """
    Private attributes

    _files  list of strings
    _max    maximum size of _file
    """

    def __init__(self, n: int = 10) -> None:
        """
        SisypheRecent instance constructor.

        Parameters
        ----------
        n : int
            number of files in the recent list
        """
        super().__init__()

        self._max = n
        self._files = list()

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of SisypheRecent instance to str
         """
        buff = 'Recent files:\n'
        if len(self._files) > 0:
            for file in self._files:
                buff += '   {}\n'.format(file)
        else: buff += 'Empty'
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheRecent instance representation
        """
        return 'SisypheRecent instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Public methods

    def setMaximumCount(self, n: int) -> None:
        """
        Set the maximum number of files in the recent list of the current SisypheRecent instance.

        Parameters
        ----------
        n : int
            maximum number of files in the recent list
        """
        if isinstance(n, int):
            if n > 0: self._max = n
            else: raise ValueError('parameter value {} must be positive.'.format(n))
        else: raise TypeError('parameter type {} is not int.'.format(type(n)))

    def getMaximumCount(self) -> int:
        """
        Get the maximum number of files in the recent list of the current SisypheRecent instance.

        Returns
        -------
        int
            maximum number of files in the recent list
        """
        return self._max

    def getFileCount(self) -> int:
        """
        Get the number of files in the recent list of the current SisypheRecent instance.

        Returns
        -------
        int
            number of files in the recent list
        """
        return len(self._files)

    def getFileList(self) -> list[str]:
        """
        Get the list of files in the recent list of the current SisypheRecent instance.

        Returns
        -------
        list[str]
            list of recent files
        """
        return self._files

    def append(self, filename: str) -> None:
        """
        Add a file name in the recent list of the current SisypheRecent instance.

        Parameters
        ----------
        filename : str
            file name
        """
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
        """
        Clear the recent list of the current SisypheRecent instance.
        """
        self._files.clear()

    def save(self) -> None:
        """
        Save the recent list of the current SisypheRecent instance in the recent.xml file in the user directory
        (~/.PySisyphe).
        """
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
        """
        Load the recent list of the current SisypheRecent instance from the recent.xml file in the user directory
        (~/.PySisyphe).
        """
        filename = join(self.getUserDirectory(), 'recent.xml')
        if exists(filename):
            self._files.clear()
            doc = minidom.parse(filename)
            nodes = doc.getElementsByTagName('file')
            if nodes.length > 0:
                for node in nodes:
                    if node.hasChildNodes():
                        child = node.firstChild
                        # noinspection PyUnresolvedReferences
                        data = child.data
                        if exists(data): self.append(data)
        # < Revision 07/03/2025
        # else: raise IOError('No such file {}'.format(filename))
        # Revision 07/03/2025 >

    def updateQMenu(self, menu: QMenu) -> None:
        """
        Update QMenu parameter items with files from the recent list of the current SisypheRecent instance.

        Parameters
        ----------
        menu : PyQt5.QtWidgets.QMenu
            menu to update with the recent list elements
        """
        if isinstance(menu, QMenu):
            menu.clear()
            if len(self._files) > 0:
                c = False
                for file in reversed(self._files):
                    if exists(file):
                        action = menu.addAction(basename(file))
                        # noinspection PyUnresolvedReferences
                        action.setData(file)
                        c = True
                if c:
                    menu.addSeparator()
                    menu.addAction('Clear')
        else: raise TypeError('parameter type {} is not QMenu.'.format(type(menu)))
