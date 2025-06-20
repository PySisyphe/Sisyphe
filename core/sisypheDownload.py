"""
External packages/modules
-------------------------
"""

from os import getcwd
from os import remove
from os import chdir
from os import mkdir
from os import rmdir

from shutil import rmtree
from shutil import copy

from glob import glob

from os.path import isfile
from os.path import isdir
from os.path import join
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import split
from os.path import splitext

from tempfile import TemporaryDirectory

from xml.dom import minidom

from zipfile import ZipFile

from PyQt5.QtWidgets import QApplication

from Sisyphe.version import isOlderThan
from Sisyphe.version import getVersionFromHost
from Sisyphe.lib.mega.mega import Mega
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['downloadFromHost',
           'installFromHost',
           'updatePySisyphe']

"""
Functions
~~~~~~~~~

    - downloadFromHost
    - installFromHost
    - updatePySisypheToNewerVersion
"""


def downloadFromHost(urls: str | list[str],
                     dst: str = getcwd(),
                     info: str = '',
                     wait: DialogWait | None = None) -> None:
    """
    Download file from mega.nz url link.

    Parameters
    ----------
    urls : str | list[str]
        list of the mega.nz download links
    dst : str
        destination folder, files are saved in dst folder
    info : str
        installation name displayed in wait dialog
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog (optional)
    """
    if info != '':
        if info[0] != ' ': info = ' ' + info
    if not exists(dst): mkdir(dst)
    if isinstance(urls, str): urls = [urls]
    if wait is not None:
        wait.setInformationText('Connection to host...')
        wait.progressVisibilityOff()
    mega = Mega()
    mega.setProgress(wait)
    mega.login_anonymous()
    for url in urls:
        if wait is not None:
            wait.setInformationText('Download{}...'.format(info))
            wait.progressVisibilityOff()
        if not exists(dst): mkdir(dst)
        try: filename = mega.download_url(url, dest_path=dst)
        except: continue
        if splitext(filename)[1].lower() == '.zip':
            if wait is not None:
                wait.setInformationText('Unzip{}...'.format(info))
                wait.progressVisibilityOff()
            dst = dirname(filename)
            # Unzip filename
            with ZipFile(filename, 'r') as fzip:
                fzip.extractall(dst)
            # Remove filename
            remove(filename)
            path = join(dst, '__MACOSX')
            if exists(path): rmtree(path)


def installFromHost(urls: str | list[str],
                    temp: str = getcwd(),
                    dst: str = '',
                    info: str = '',
                    wait: DialogWait | None = None) -> None:
    """
    Download and install files from mega.nz url links.

    Parameters
    ----------
    urls : str | list[str]
        list of url
    temp : str
        temporary folder, files are saved in temp folder
    dst : str
        destination folder, files are recursively copied from temp to dst
    info : str
        installation name displayed in wait dialog
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog (optional)
    """
    downloadFromHost(urls, temp, wait)
    if dst != '' and exists(dst):
        previous = getcwd()
        chdir(temp)
        files = glob('**', recursive=True)
        if wait is not None:
            if info != '': info = ' {}'.format(info)
            wait.setInformationText('Installing{}...'.format(info))
            wait.setProgressRange(0, len(files))
            wait.setCurrentProgressValue(0)
            wait.progressVisibilityOn()
        folders = list()
        for i, file in enumerate(files):
            if isfile(file):
                base, filename = split(file)
                src = join(temp, file)
                dst = join(dst, base)
                if not exists(dst): mkdir(dst)
                if wait is not None: wait.setInformationText('Copy {}...'.format(basename(src)))
                copy(src, dst)
                remove(src)
            elif isdir(file): folders.append(file)
            if wait is not None: wait.incCurrentProgressValue()
        if len(folders) > 0:
            for folder in folders:
                rmdir(folder)
        chdir(previous)


def updatePySisyphe(wait: DialogWait | None = None) -> None:
    """
    Download and install last version of PySisyphe.

    Parameters
    ----------
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog (Optional)
    """
    import Sisyphe
    dst = dirname(Sisyphe.__file__)
    version = getVersionFromHost()
    if version != '':
        if isOlderThan(version):
            filename = join(dst, 'settings/host.xml')
            if exists(filename):
                url = ''
                doc = minidom.parse(filename)
                root = doc.documentElement
                if root.nodeName == 'host' and root.getAttribute('version') == '1.0':
                    section = doc.getElementsByTagName('source')
                    if len(section) > 0:
                        section = section[0]
                        url = section.getAttribute('url')
                if url is not None and url != '':
                    try:
                        with TemporaryDirectory() as temp:
                            installFromHost(url[1], temp, dst, info='version {}'.format(version), wait=wait)
                    except: raise ConnectionError('PySisyphe update failed.')
    else: raise ConnectionError('Failed to connect to host.')
