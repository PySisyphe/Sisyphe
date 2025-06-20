"""
External packages/modules
-------------------------
"""

from os.path import dirname
from os.path import exists
from os.path import abspath

from binascii import unhexlify

from Sisyphe.lib.mega.mega import Mega

from xml.dom import minidom

__version__ = "0.9.1"

_V = b'70797369737970686540676d61696c2e636f6d'

"""
Functions
~~~~~~~~~

   - getMajorVersion
   - getMinorVersion
   - getPatchVersion
   - getVersion
   - getVersionAsList
   - getVersionAsDict
   - isOlderThan
   - isNewerThan
   - isCurrentVersion
   - getVersionFromHost
   - isUpToDateVersion
   - getVersionHistoryFromHost
   - getUrlsToUpdate
       
Creation: 04/11/2023
Last revision: 30/10/2024
"""


def getMajorVersion() -> int:
    return int(__version__.split('.')[0])


def getMinorVersion() -> int:
    return int(__version__.split('.')[1])


def getPatchVersion() -> int:
    return int(__version__.split('.')[2])


def getVersion() -> str:
    return __version__


def getVersionAsList() -> list[int]:
    return [int(v) for v in __version__.split('.')]


def getVersionAsDict() -> dict[str: int]:
    r = dict()
    v = __version__.split('.')
    # noinspection PyUnresolvedReferences
    r['major'] = int(v[0])
    r['minor'] = int(v[1])
    r['patch'] = int(v[2])
    return r


def isOlderThan(version: str | list[int] | dict[str, int]) -> bool:
    if isinstance(version, str): version = [int(v) for v in version.split('.')]
    elif isinstance(version, dict): version = [version['major'], version['minor'], version['patch']]
    if isinstance(version, list):
        current = getVersionAsList()
        if current[0] < version[0]: return True
        elif current[0] == version[0]:
            if current[1] < version[1]: return True
            elif current[1] == version[1]:
                if current[2] < version[2]: return True
        return False
    else: raise TypeError('Invalid parameter type {}.'.format(type(version)))


def isNewerThan(version: str | list[int] | dict[str: int]) -> bool:
    if isinstance(version, str): version = [int(v) for v in version.split('.')]
    elif isinstance(version, dict): version = [version['major'], version['minor'], version['patch']]
    if isinstance(version, list):
        current = getVersionAsList()
        if current[0] > version[0]: return True
        elif current[0] == version[0]:
            if current[1] > version[1]: return True
            elif current[1] == version[1]:
                if current[2] < version[2]: return True
        return False
    else: raise TypeError('Invalid parameter type {}.'.format(type(version)))


def isCurrentVersion(version: str | list[int] | dict[str, int]) -> bool:
    if isinstance(version, list): version = '.'.join([str(v) for v in version])
    elif isinstance(version, dict): version = '.'.join([str(version[v]) for v in ('major', 'minor', 'patch')])
    if isinstance(version, str): return version == __version__
    else: raise TypeError('Invalid parameter type {}.'.format(type(version)))


def getVersionFromHost() -> str:
    # Connect to host as anonymous & Download host.xml
    mega = Mega()
    import Sisyphe.settings
    try:
        v1 = unhexlify(_V).decode()
        v2 = unhexlify(_V[:18]).decode()
        path = dirname(abspath(Sisyphe.settings.__file__))
        mega.login(v1, v2)
        h = mega.find('host.xml')
        filename = str(mega.download(h, dest_path=path))
    except: filename = ''
    version = ''
    if exists(filename):
        doc = minidom.parse(filename)
        root = doc.documentElement
        if root.nodeName == 'host' and root.getAttribute('version') == '1.0':
            section = doc.getElementsByTagName('version')
            if len(section) > 0:
                section = section[0]
                version = section.getAttribute('current')
    return version


def isUpToDateVersion() -> bool:
    version = getVersionFromHost()
    return isCurrentVersion(version)
