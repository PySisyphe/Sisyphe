"""
External packages/modules
-------------------------
"""

import sys

from os import getcwd
from os import remove
from os import chdir
from os import mkdir
from os import rmdir

from os.path import getmtime
from os.path import expanduser

from shutil import rmtree
from shutil import copy

from binascii import unhexlify

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

from Sisyphe.version import isOlderThan
from Sisyphe.version import getVersionFromHost
from Sisyphe.lib.mega.mega import Mega
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.core.sisypheSettings import initPySisypheUserPath

__all__ = ['downloadFromHost',
           'installFromHost',
           'updatePySisyphe']

_V = b'70797369737970686540676d61696c2e636f6d'

"""
Functions
~~~~~~~~~

    - downloadFromHost
    - installFromHost
    - updatePySisypheToNewerVersion
    
Last revision: 15/10/2025
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
    # < Revision 11/07/2025
    # mega.login_anonymous()
    v1 = unhexlify(_V).decode()
    v2 = unhexlify(_V[:18]).decode()
    mega.login(v1, v2)
    # Revision 11/07/2025 >
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
                # < Revision 24/07/2024
                # Copy src only if the file is more recent
                # copy(src, dst)
                ext = splitext(src)[1]
                if sys.platform == 'win32' and ext == '.so':
                    remove(src)
                    continue
                elif sys.platform == 'darwin' and ext == '.pyd':
                    remove(src)
                    continue
                if exists(dst):
                    if getmtime(src) > getmtime(dst): copy(src, dst)
                else: copy(src, dst)
                # < Revision 15/10/2025
                # copy new functions.xml and settings.xml to ~/.PySisyphe
                if filename == 'functions.xml':
                    userdir = join(expanduser('~'), '.PySisyphe')
                    if not exists(userdir): initPySisypheUserPath()
                    copy(src, userdir)
                elif filename == 'settings.xml':
                    userdir = join(expanduser('~'), '.PySisyphe')
                    if not exists(userdir): initPySisypheUserPath()
                    copy(src, userdir)
                # Revision 15/10/2025 >
                # Revision 24/07/2024 >
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
                    if hasattr(sys, '_MEIPASS'):
                        # < Revision 15/10/2025
                        # if sys.platform == 'win32': updatesec = 'updatepyc'
                        updatesec = 'updatepyc'
                        # Revision 15/10/2025 >
                    else: updatesec = 'updatepy'
                    section = doc.getElementsByTagName(updatesec)
                    if len(section) > 0:
                        section = section[0]
                        url = section.getAttribute('url')
                if url is not None and url != '':
                    try:
                        with TemporaryDirectory() as temp:
                            # < Revision 24/07/2025
                            # installFromHost(url[1], temp, dst, info='version {}'.format(version), wait=wait)
                            installFromHost(url, temp, dst, info='version {}'.format(version), wait=wait)
                            # Revision 24/07/2025 >
                    except: raise ConnectionError('PySisyphe update failed.')
    else: raise ConnectionError('Failed to connect to host.')
