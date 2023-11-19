"""
    External packages/modules

        Name            Link                                                        Usage

        BeautifulSoup   https://www.crummy.com/software/BeautifulSoup/bs4/doc/      HTML parser
        Requests        https://requests.readthedocs.io/en/latest/                  Simple HTTP library
"""

from os.path import join
from os.path import dirname
from os.path import exists
from os.path import abspath

from bs4 import BeautifulSoup as bs

import requests as rq

from xml.dom import minidom

__version__ = "0.1.0"

_VERSIONURL = 'https://www.mediafire.com/file/ytynbn92vnohz2c/versions.xml/file'

"""
    Functions
    
       getMajorVersion() -> int
       getMinorVersion() -> int
       getPatchVersion() -> int
       getVersion() -> str
       getVersionAsList() -> ist[int, int, int]
       getVersionAsDict() -> dict[str: int]
       isOlderThan(version: str | list[int, int, int] | dict[str: int]) -> bool
       isNewerThan(version: str | list[int, int, int] | dict[str: int]) -> bool
       isCurrentVersion(version: str | list[int, int, int] | dict[str: int]) -> bool
       getVersionFromHost(timeout: float = 5.0) -> str
       isUpToDateVersion() -> bool
       getVersionHistoryFromHost() -> dict[str: str]
       getUrlsToUpdate(history: dict[str: str] | None = None) -> list[tuple[str: str]]
       
    Creation: 04/11/2023
"""

def getMajorVersion() -> int:
    return int(__version__.split('.')[0])

def getMinorVersion() -> int:
    return int(__version__.split('.')[1])

def getPatchVersion() -> int:
    return int(__version__.split('.')[2])

def getVersion() -> str:
    return __version__

def getVersionAsList() -> list[int, int, int]:
    return [int(v) for v in __version__.split('.')]

def getVersionAsDict() -> dict[str: int]:
    r = dict()
    v = __version__.split('.')
    r['major'] = int(v[0])
    r['minor'] = int(v[1])
    r['patch'] = int(v[2])
    return r

def isOlderThan(version: str | list[int, int, int] | dict[str: int]) -> bool:
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

def isNewerThan(version: str | list[int, int, int] | dict[str: int]) -> bool:
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

def isCurrentVersion(version: str | list[int, int, int] | dict[str: int]) -> bool:
    if isinstance(version, list): version = '.'.join([str(v) for v in version])
    elif isinstance(version, dict): version = '.'.join([str(version[v]) for v in ('major', 'minor', 'patch')])
    if isinstance(version, str): return version == __version__
    else: raise TypeError('Invalid parameter type {}.'.format(type(version)))

def getVersionFromHost(timeout: float = 5.0) -> str:
    """
        timeout     float, timeout in seconds, default = 5s
    """
    import Sisyphe
    filename = join(dirname(abspath(Sisyphe.__file__)), 'versions.xml')
    url = ''
    # Get html download page from host, search file link
    r = rq.get(_VERSIONURL, timeout=timeout)
    if r.status_code == rq.codes.ok:
        html = r.content
        soup = bs(html, 'html.parser')
        item = soup.find_all('a', class_='input popsok')
        if len(item) > 0:
            item = item[0]
            url = item.attrs['href']
    if url == '': raise IOError('PySisyphe host connection failed.')
    # Download file
    r = rq.get(url, timeout=timeout)
    if r.status_code == rq.codes.ok:
        with open(filename, 'wb') as file:
            file.write(r.content)
    if exists(filename):
        doc = minidom.parse(filename)
        root = doc.documentElement
        if root.nodeName == 'host' and root.getAttribute('version') == '1.0':
            section = doc.getElementsByTagName('version')
            if len(section) > 0:
                section = section[0]
                return section.getAttribute('current')

def isUpToDateVersion() -> bool:
    version = getVersionFromHost()
    return isCurrentVersion(version)

def getVersionHistoryFromHost() -> dict[str: str]:
    import Sisyphe
    filename = join(dirname(abspath(Sisyphe.__file__)), 'versions.xml')
    if not exists(filename): getVersionFromHost()
    else:
        doc = minidom.parse(filename)
        root = doc.documentElement
        if root.nodeName == 'host' and root.getAttribute('version') == '1.0':
            sections = doc.getElementsByTagName('folder')
            r = dict()
            if len(sections) > 0:
                for section in sections:
                    if section.hasAttribute('version') and section.hasAttribute('url'):
                        r[section.getAttribute('version')] = section.getAttribute('url')
            return r

def getUrlsToUpdate(history: dict[str: str] | None = None) -> list[tuple[str: str]]:
    r = list()
    if history is None: history = getVersionHistoryFromHost()
    for version, url in history.items():
        if isNewerThan(version): r.append((version, url))
    return r

