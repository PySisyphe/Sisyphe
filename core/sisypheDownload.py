"""
    External packages/modules

        Name            Link                                                        Usage

        BeautifulSoup   https://www.crummy.com/software/BeautifulSoup/bs4/doc/      HTML parser
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        Requests        https://requests.readthedocs.io/en/latest/                  Simple HTTP library
"""

from os import getcwd
from os import remove
from os import chdir
from os import mkdir
from os import rmdir

from glob import glob

from os.path import isfile
from os.path import isdir
from os.path import join
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import split
from os.path import splitext

from shutil import copy

from tempfile import TemporaryDirectory

from zipfile import ZipFile

from xml.dom import minidom

from bs4 import BeautifulSoup as bs

from PyQt5.QtWidgets import QMessageBox

import requests as rq

from Sisyphe.version import getUrlsToUpdate
from Sisyphe.version import getVersionHistoryFromHost
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['getHostName',
           'getFilenameFromMediaFireLink',
           'downloadFromMediaFireHost',
           'downloadFromHost',
           'installFromHost',
           'updatePySisypheToNewerVersion']

"""
    Functions
    
        getHostName(url: str) -> str
        
        getFilenameFromMediaFireLink(url: str) -> str
        
        downloadFromMediaFireHost(url: str | list[str],
                              dst: str = getcwd(),
                              wait: DialogWait | None = None) -> str
        
        downloadFromHost(urls: str | list[str], 
                         dst: str = getcwd(), 
                         wait: DialogWait | None = None)
        
        installFromHost(urls: str | list[str], 
                        temp: str = getcwd(), 
                        dst: str = '',
                        info: str = '',
                        wait: DialogWait | None = None)
                        
        updatePySisypheToNewerVersion(wait: DialogWait | None = None)
    
    Creation: 04/11/2023 
    Revisions:
    
        16/11/2023  docstrings
"""

def getHostName(url: str) -> str:
    """
        Get host name

        Parameter

            url     str, url

        return str, host name
    """
    return url.split('/')[2]

def getFilenameFromMediaFireLink(url: str) -> str:
    """
        Get downloaded file name form mediafire link

        Parameter

            url     str, url

        return  str, file name
    """
    r = url.split('/')
    if r[0] == 'https:' and r[2] == 'www.mediafire.com' and r[-1] == 'file': return r[-2]
    else: return ''

def downloadFromMediaFireHost(url: str,
                              dst: str = getcwd(),
                              wait: DialogWait | None = None) -> str:
    """
        Download file from mediafire link

        Parameters

            url     str, url of the mediafire download link
            dst     str, destination folder, files are saved in dst folder
            wait    Sisyphe.gui.dialogWait.DialogWait, progress bar dialog

        return  str, name of the download file
    """
    if not exists(dst): mkdir(dst)
    filename = join(dst, getFilenameFromMediaFireLink(url))
    if filename == '':
        if wait is not None: wait.hide()
        QMessageBox.warning(self, 'Downloading',
                            '{} is not a valid link'.format(url))
        if wait is not None: wait.show()
        return ''
    if wait is not None: wait.setInformationText('Connection to hosts for {}...'.format(basename(filename)))
    else: print('Connection to hosts for {}...'.format(basebame(filename)))
    durl = ''
    try:
        r = rq.get(url)
        if r.status_code == rq.codes.ok:
            html = r.content
            soup = bs(html, 'html.parser')
            item = soup.find_all('a', class_='input popsok')
            if len(item) > 0:
                item = item[0]
                durl = item.attrs['href']
    except: durl = ''
    if durl == '':
        if wait is not None: wait.hide()
        QMessageBox.warning(self, 'Downloading',
                            'Host connection failed.')
        if wait is not None: wait.show()
        return ''
    try:
        r = rq.get(durl, stream=True)
        total = int(r.headers.get('content-length', 0))
        if wait is not None:
            wait.setInformationText('{} downloading...'.format(basename(filename)))
            wait.setProgressRange(0, total)
            wait.setCurrentProgressValue(0)
            wait.setProgressVisibility(total > 1024)
        else: print('{} downloading...'.format(basename(filename)))
        with open(filename, 'wb') as file:
            for data in r.iter_content(chunk_size=1024):
                file.write(data)
                if wait is not None: wait.setCurrentProgressValue(file.tell())
    except:
        if wait is not None: wait.hide()
        QMessageBox.warning(self, 'Downloading',
                            'Host connection failed.')
        if wait is not None: wait.show()
        return ''
    return filename

def downloadFromHost(urls: str | list[str],
                     dst: str = getcwd(),
                     wait: DialogWait | None = None) -> None:
    """
        Download file from mediafire link

        Parameters

            urls    str | list[str], list of the mediafire download links
            dst     str, destination folder, files are saved in dst folder
            wait    Sisyphe.gui.dialogWait.DialogWait, progress bar dialog
    """
    if not exists(dst): mkdir(dst)
    if isinstance(urls, str): urls = [urls]
    if wait is not None:
        wait.setInformationText('Connection to host...')
        wait.progressVisibilityOff()
    else: print('Connection to host...')
    for url in urls:
        hostname = getHostName(url)
        if hostname == 'www.mediafire.com': filename = downloadFromMediaFireHost(url, dst, wait)
        else:
            if wait is not None: wait.hide()
            QMessageBox.warning(self, 'Downloading',
                                '{} Host is not supported.'.format(hostname))
            if wait is not None: wait.show()
            continue
        if filename == '': continue
        if splitext(filename)[1].lower() == '.zip':
            if wait is not None:
                wait.setInformationText('Unzip {}...'.format(basename(filename)))
                wait.progressVisibilityOff()
            else: print('Unzip {}...'.format(filename))
            dst = dirname(filename)
            # Unzip filename
            with ZipFile(filename, 'r') as fzip:
                fzip.extractall(dst)
            # Remove filename
            remove(filename)

def installFromHost(urls: str | list[str],
                    temp: str = getcwd(),
                    dst: str = '',
                    info: str = '',
                    wait: DialogWait | None = None) -> None:
    """
        Install files downloaded from url links

        Parameters

            urls    str | list[str], list of the mediafire download links
            temp    str, temporary folder, files are saved in temp folder
            dst     str, destination folder, files are recursively copied from temp to dst
            info    str, installation name displayed in wait dialog
            wait    Sisyphe.gui.dialogWait.DialogWait, progress bar dialog
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

def updatePySisypheToNewerVersion(wait: DialogWait | None = None) -> None:
    """
        Download and install last version of PySisyphe.

        Parameter

            wait    Sisyphe.gui.dialogWait.DialogWait, progress bar dialog
    """
    history = getVersionHistoryFromHost()
    urls = getUrlsToUpdate(history)
    if len(urls) > 0:
        import Sisyphe
        dst = dirname(Sisyphe.__file__)
        try:
            with TemporaryDirectory() as temp:
                for url in urls:
                    if url != '':
                        installFromHost(url[1], temp, dst, info='version {}'.format(url[0]), wait=wait)
        except:
            if wait is not None: wait.hide()
            QMessageBox.warning(self, 'Version update', 'PySisyphe update failed.')

