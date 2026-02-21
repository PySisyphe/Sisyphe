"""
External packages/modules
-------------------------
"""

import sys

from os import getcwd
from os import scandir
from os import remove
from os import chdir
from os import mkdir

from os.path import isfile
from os.path import isdir
from os.path import join
from os.path import exists
from os.path import dirname
from os.path import abspath
from os.path import split
from os.path import splitext
from os.path import getmtime
from os.path import expanduser

from pathlib import Path

from importlib import metadata

from glob import glob

from shutil import rmtree
from shutil import copy

from binascii import unhexlify

from tempfile import TemporaryDirectory

from xml.dom import minidom

from zipfile import ZipFile

# from subprocess import check_call
from subprocess import STDOUT
from subprocess import check_output

from tqdm import tqdm

from Sisyphe.version import isOlderThan
from Sisyphe.version import getVersionFromHost
from Sisyphe.lib.mega.mega import Mega
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.core.sisypheSettings import initPySisypheUserPath
from Sisyphe.core.sisypheSettings import setUserSettingsToDefault

__all__ = ['getPackageMetadata',
           'getPackagesToUpdate',
           'getPackageFolder',
           'downloadFromHost',
           'installFromHost',
           'updatePackages',
           'updatePySisyphe']

_V = b'70797369737970686540676d61696c2e636f6d'

"""
Functions
~~~~~~~~~

    - getInstalledPackages
    - getPackagesToUpdate
    - getPackageFolder
    - downloadFromHost
    - installFromHost
    - updatePackages
    - updatePySisyphe

Last revision: 08/02/2026
"""


def getPackageMetadata(packages: str | list[str] | None = None,
                       wait : DialogWait | None = None) -> dict[str, str | list[str]]:
    """
    Extract metadata from packages: version, installation folders, and required packages.
    If no package is provided, all installed packages are processed.

    Parameters
    ----------
    packages : str | list[str] | None
        list of packages for which metadata should be extracted. All installed packages if None.
    wait : DialogWait | None = None
        progress dialog

    Returns
    -------
    dict[str, str | list[str]]
        keys: 'version' = version, 'folders' = installation folder(s), 'requires' = required package(s)
    """

    def getRequires(pname: str):
        try: buffr = metadata.distribution(pname).requires
        except: return
        if buffr is not None and len(buffr) > 0:
            for vr in buffr:
                if 'extra' in vr: continue
                elif 'exceptiongroup' in v: continue
                vr = vr.translate(t).split(' ')[0]
                if vr not in requires:
                    requires.append(vr)
                    getRequires(vr)

    r = dict()
    if packages is None: distrib = list(metadata.distributions())
    else:
        if isinstance(packages, str): packages = [packages]
        distrib = list()
        for v in packages:
            try: distrib.append(metadata.distribution(v))
            except: pass
    n = len(distrib)
    t = {60: 32, 61: 32, 62: 32, 91: 32}
    if n > 0:
        if wait is not None:
            wait.setInformationText('Get installed packages...')
            wait.setProgressRange(0, n)
            # < Revision 17/02/2026
            wait.setCurrentProgressValue(0)
            # Revision 17/02/2026 >
            wait.progressVisibilityOn()
        else: wait2 = tqdm(total=n, colour='white')
        for pkg in distrib:
            n = len(pkg.files[0].parts)
            root = Path(pkg.files[0].locate()).parents[n-1]
            name = pkg.metadata['Name']
            r[name] = dict()
            r[name]['version'] = pkg.version
            previous = ''
            folders = list()
            for f in pkg.files:
                folder = f.parts[0]
                if folder != previous:
                    previous = folder
                    if folder == '..': continue
                    elif folder[:2] == '__': continue
                    elif folder[-4:] == 'info': continue
                    current = join(root, folder)
                    if exists(current) and isdir(current):
                        folders.append(folder)
            r[pkg.metadata['Name']]['folders'] = folders
            if packages is not None:
                requires = list()
                buff = pkg.requires
                if buff is not None and len(buff) > 0:
                    for v in buff:
                        if 'extra' in v: continue
                        elif 'exceptiongroup' in v: continue
                        v = v.translate(t).split(' ')[0]
                        if v not in requires:
                            requires.append(v)
                            getRequires(v)
                r[pkg.metadata['Name']]['requires'] = requires
            if wait is not None: wait.incCurrentProgressValue()
            else:
                # noinspection PyUnboundLocalVariable
                wait2.update()
            # < Revision 17/02/2026
            if wait is not None: wait.progressVisibilityOff()
            # Revision 17/02/2026 >
    return r


def getPackagesToUpdate(packages: str | dict[str, str],
                        wait : DialogWait | None = None) -> dict[str, str]:
    """
    List of packages to check for installation or update.

    Parameters
    ----------
    packages : str | dict[str, str]

        - if str, path to a text file (line 'name version')
        - if dict[str, str], key = package name, value = package version

    wait : DialogWait | None = None
        progress dialog

    Returns
    -------
    dict[str, str]
        Packages that need to be updated, keys: package name, values: package version
    """
    r = dict()
    if isinstance(packages, str):
        if exists(packages):
            with open(packages, 'r') as f:
                buff = f.readlines()
            packages = dict()
            for line in buff:
                k, v = line.split(' ')
                v = v.replace('\n', '')
                packages[k] = v
    if isinstance(packages, dict):
        ipkg = getPackageMetadata(wait=wait)
        for k in packages:
            if k in ipkg:
                # noinspection PyTypeChecker
                if packages[k] != ipkg[k]['version']: r[k] = packages[k]
            else: r[k] = packages[k]
    return r


def getPackageFolder() -> str:
    """
    Get the package folder of the current Python environment:

        - venv execution: ./.venv/Lib/site-packages
        - frozen execution: ./_internal

    Returns
    -------
    str
        package folder
    """
    pkg = metadata.distribution('decorator')
    n = len(pkg.files[0].parts)
    return str(Path(pkg.files[0].locate()).parents[n-1])


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
    Download and install files from mega.nz url link(s).

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
    import logging
    logger = logging.getLogger(__name__)
    downloadFromHost(urls, temp, wait=wait)
    if dst != '' and exists(dst):
        previous = getcwd()
        d = [join(temp, f) for f in scandir(temp) if f.is_dir()]
        if len(d) > 0: temp = d[0]
        chdir(temp)
        files = glob('**', recursive=True)
        if wait is not None:
            if info != '': info = ' {}'.format(info)
            wait.setInformationText('Installing{}...'.format(info))
            wait.setProgressRange(0, len(files))
            wait.setCurrentProgressValue(0)
            wait.progressVisibilityOn()
        v = 'cp{}{}'.format(sys.version_info.major, sys.version_info.minor)
        for i, file in enumerate(files):
            if isfile(file):
                base, filename = split(file)
                src = join(temp, file)
                dst2 = join(dst, base)
                if not exists(dst2):
                    try:
                        mkdir(dst2)
                        if logger is not None:
                            logger.info('mkdir {}'.format(dst2))
                    except:
                        if logger is not None:
                            logger.info('error: mkdir {}'.format(dst2))
                ext = splitext(src)[1]
                if sys.platform == 'win32':
                    if ext == '.so': continue
                    elif ext == 'dylib': continue
                    elif ext == '.pyd':
                        if v not in src: continue
                elif sys.platform == 'darwin':
                    if ext == '.pyd': continue
                    elif ext =='.dll': continue
                    elif ext == '.so':
                        if v not in src: continue
                dstfile = join(dst2, filename)
                if exists(dstfile):
                    if getmtime(src) > getmtime(dstfile):
                        if wait is not None:
                            wait.addInformationText('Update {}'.format(filename))
                        try:
                            copy(src, dst2)
                            if logger is not None:
                                logger.info('update {}'.format(dstfile))
                        except:
                            if logger is not None:
                                logger.info('error: update {}'.format(dstfile))
                # else: copy(src, dst)
                else:
                    if wait is not None:
                        wait.addInformationText('Copy {}'.format(filename))
                    try:
                        copy(src, dst2)
                        if logger is not None:
                            logger.info('copy {}'.format(dstfile))
                    except:
                        if logger is not None:
                            logger.info('error: copy {}'.format(dstfile))
            # < Revision 15/10/2025
            # elif isdir(file): folders.append(file)
            # Revision 15/10/2025 >
            elif isdir(file):
                dst2 = join(dst, file)
                if not exists(dst2):
                    try:
                        mkdir(dst2)
                        if logger is not None:
                            logger.info('mkdir {}'.format(dst2))
                    except:
                        if logger is not None:
                            logger.info('error: mkdir {}'.format(dst2))
            # < Revision 06/11/2025
            # Revision 06/11/2025 >
            if wait is not None:
                wait.incCurrentProgressValue()
        chdir(previous)


def updatePackages(temp: str = getcwd(),
                   dst: str = '',
                   wait: DialogWait | None = None) -> None:
    """
    Install or update package(s).

    Parameters
    ----------
        temp : str
            temporary folder with the packages to be installed
        dst : str
            destination folder, files are recursively copied from temp to dst
        wait : Sisyphe.gui.dialogWait.DialogWait
            progress bar dialog (optional)
    """
    import logging
    logger = logging.getLogger(__name__)
    temp = join(temp, '.packages', 'packages.txt')
    if exists(temp):
        # < Revision 17/02/2026
        # pkg = getPackagesToUpdate(temp)
        pkg = getPackagesToUpdate(temp, wait=wait)
        # Revision 17/02/2026 >
        if len(pkg) > 0:
            if hasattr(sys, '_MEIPASS'):
                """
                Update of packages, frozen execution
                """
                if len(pkg) > 0:
                    dst = Path(dst).parents[0]
                    v = 'cp{}{}'.format(sys.version_info.major, sys.version_info.minor)
                    for k in pkg:
                        if wait is not None:
                            wait.setInformationText('Update {} package...'.format(k))
                            # noinspection PyTypeChecker
                            for folder in pkg[k]['folders']:
                                path = join(temp, '.packages', folder)
                                if exists(path):
                                    files2 = glob(join(path, '**'), recursive=True)
                                    if len(files2) > 0:
                                        for i, file in enumerate(files2):
                                            if isdir(file):
                                                try:
                                                    mkdir(file)
                                                    if logger is not None:
                                                        logger.info('mkdir {}'.format(file))
                                                except:
                                                    if logger is not None:
                                                        logger.info('error: mkdir {}'.format(file))
                                            elif isfile(file):
                                                base, filename = split(file)
                                                src = join(temp, file)
                                                dst2 = join(dst, base)
                                                ext = splitext(src)[1]
                                                if sys.platform == 'win32':
                                                    if ext == '.so': continue
                                                    elif ext == '.dylib': continue
                                                    elif ext == '.pyd':
                                                        if v not in src: continue
                                                elif sys.platform == 'darwin':
                                                    if ext == '.pyd': continue
                                                    elif ext == '.dll': continue
                                                    elif ext == '.so':
                                                        if v not in src: continue
                                                dstfile = join(dst2, filename)
                                                if wait is not None:
                                                    wait.addInformationText('Copy {}'.format(filename))
                                                try:
                                                    copy(src, dst2)
                                                    if logger is not None:
                                                        logger.info('copy {}'.format(dstfile))
                                                except:
                                                    if logger is not None:
                                                        logger.info('error: copy {}'.format(dstfile))
                                            if wait is not None:
                                                wait.incCurrentProgressValue()
            else:
                """
                Update of packages, venv execution
                """
                for k in pkg:
                    if wait is not None:
                        wait.addInformationText('Installing {} package...'.format(k))
                    try:
                        # < Revision 08/02/2026
                        # check_call([sys.executable, '-m', 'pip', 'install', '=='.join([k, pkg[k]])])
                        output = check_output([sys.executable, '-m', 'pip', 'install', '=='.join([k, pkg[k]])],
                                              stderr=STDOUT)
                        if logger is not None:
                            logger.info(output)
                        # Revision 08/02/2026 >
                    except:
                        if logger is not None:
                            logger.info('error: failed to install {} package.'.format(k))


def updatePySisyphe(wait: DialogWait | None = None) -> None:
    """
    Download and install last version of PySisyphe.

    Parameters
    ----------
    wait : Sisyphe.gui.dialogWait.DialogWait
        progress bar dialog (Optional)
    """
    import logging
    logger = logging.getLogger(__name__)
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
                        # < Revision 28/01/2026
                        vpython = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
                        if vpython == '3.10':
                            # < Revision 15/10/2025
                            # if sys.platform == 'win32': updatesec = 'updatepyc'
                            updatesec = 'updatepyc'
                            # Revision 15/10/2025 >
                        elif vpython == '3.12': updatesec = 'updatepyc312'
                        elif vpython == '3.14': updatesec = 'updatepyc314'
                        else: raise ValueError('Python {} is not supported.'.format(vpython))
                        # Revision 28/01/2026 >
                    else: updatesec = 'updatepy'
                    section = doc.getElementsByTagName(updatesec)
                    if len(section) > 0:
                        section = section[0]
                        url = section.getAttribute('url')
                if url is not None and url != '':
                    try:
                        with TemporaryDirectory() as temp:
                            installFromHost(url, temp, dst, info='version {}'.format(version), wait=wait)
                            updatePackages(temp, dst, wait=wait)
                    except:
                        if logger is not None:
                            logger.info('error: failed to update PySisyphe.')
                        raise ConnectionError('PySisyphe update failed.')
                    """
                    Reset PySisyphe settings to default
                    """
                    # < Revision 19/01/2026
                    if wait is not None:
                        wait.setInformationText('Reset PySisyphe settings to default...')
                    userdir = abspath(join(expanduser('~'), '.PySisyphe'))
                    if not exists(userdir):
                        initPySisypheUserPath()
                        if logger is not None:
                            logger.info('Create {}'.format(userdir))
                            logger.info('Copy default settings to {}'.format(userdir))
                    else:
                        setUserSettingsToDefault()
                        if logger is not None:
                            logger.info('Copy default settings to {}'.format(userdir))
                    # Revision 19/01/2026 >
    else:
        if logger is not None:
            logger.info('error: failed to connect to host.')
        raise ConnectionError('Failed to connect to host.')
