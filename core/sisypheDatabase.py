"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from os import mkdir
from os import remove

from os.path import exists
from os.path import join
from os.path import basename
from os.path import dirname
from os.path import abspath
from os.path import splitext
from os.path import getctime
from os.path import getmtime
from os.path import isdir
from os.path import expanduser

from shutil import copy
from shutil import rmtree

from time import ctime
from time import strptime
from time import strftime

from glob import glob

from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheMesh import SisypheMeshCollection
from Sisyphe.core.sisypheTransform import SisypheTransforms
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheXml import XmlVolume
from Sisyphe.core.sisypheXml import XmlROI
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheDatabase']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheDatabase
"""

class SisypheDatabase(object):
    """
    Description
    ~~~~~~~~~~~

    Class used to manage a patient database.

    Scope of methods:

    - container-like methods to access to patient folder
    - Get/set/remove volumes/ROIs/meshes to patient folder
    - search volume/ROI/mesh in database
    - database backup

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheDatabaseItem

    Creation: 27/09/2022
    Last revision: 10/12/2023
    """
    __slots__ = ['_dbpath']

    # Class methods

    @classmethod
    def getIdentityFromFolder(cls, folder: str) -> SisypheIdentity:
        """
        Get patient identity (Sisyphe.core.sisypheImageAttributes.SisypheIdentity) from folder name.

        Parameters
        ----------
        folder : str
            folder name

        Returns
        -------
        Sisyphe.core.sisypheImageAttributes.SisypheIdentity
        """
        if isinstance(folder, str):
            if exists(folder):
                last, first, dob = basename(folder).split('_')
                identity = SisypheIdentity()
                identity.setLastname(last)
                identity.setFirstname(first)
                identity.setDateOfBirthday(dob)
                return identity
            else: raise FileNotFoundError('no such directory {}.'.format(folder))
        else: raise TypeError('parameter type {} is not str.'.format(type(folder)))

    @classmethod
    def getFolderFromIdentity(cls, identity: SisypheIdentity) -> str:
        """
        Get patient folder name from identity (Sisyphe.core.sisypheImageAttributes.SisypheIdentity).

        Parameters
        ----------
        identity : Sisyphe.core.sisypheImageAttributes.SisypheIdentity

        Returns
        -------
        str
            folder name
        """
        if isinstance(identity, SisypheVolume):
            identity = identity.getIdentity()
        if isinstance(identity, SisypheIdentity):
            return '_'.join([identity.getLastname(), identity.getFirstname(), identity.getDateOfBirthday()])
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))

    @classmethod
    def getCreationDateCode(cls, filename: str) -> float | None:
        """
        Get file creation date as operating system float code.

        Parameters
        ----------
        filename : str
            file name

        Returns
        -------
        float | None
            float code of the date
        """
        if exists(filename): return getctime(filename)
        else: return None

    @classmethod
    def getCreationDate(cls, filename: str, f: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        Get file creation date as str.

        Parameters
        ----------
        filename : str
            file name
        f : str
            date format (default '%Y-%m-%d %H:%M:%S')

        Returns
        -------
        str
            date
        """
        r = ''
        if exists(filename):
            code = cls.getCreationDateCode(filename)
            if code:
                code = strptime(ctime(code))
                r = strftime(f, code)
        return r

    @classmethod
    def getLastModifiedDateCode(cls, filename: str) -> float | None:
        """
        Get file last modified date as operating system float code.

        Parameters
        ----------
        filename : str
            file name

        Returns
        -------
        float
            float code of the last modified date
        """
        if exists(filename): return getmtime(filename)
        else: return None

    @classmethod
    def getLastModifiedDate(cls, filename: str, f: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        Get file last modified date as str.

        Parameters
        ----------
        filename : str
            file name
        f : str
            date format (default '%Y-%m-%d %H:%M:%S')

        Returns
        -------
        str
            last modified date
        """
        r = ''
        if exists(filename):
            code = cls.getLastModifiedDateCode(filename)
            if code:
                code = strptime(ctime(code))
                r = strftime(f, code)
        return r

    @classmethod
    def getFilesLastModifiedDate(cls, folder: str) -> dict[str, float]:
        """
        Get last modified date of files in a folder as list of operating system float code.

        Parameters
        ----------
        folder : str
            folder name

        Returns
        -------
        dict[str, float]
            keys are file names, values are float codes of last modified dates
        """
        r = dict()
        if exists(folder):
            filt = join(folder, '*')
            filenames = glob(filt)
            if len(filenames) > 0:
                for filename in filenames:
                    r[filename] = getmtime(filename)
        return r

    # Special methods

    """
    Private attributes
    
    _dbpath : str
    """

    def __init__(self) -> None:
        """
        SisypheDatabase instance constructor.
        """
        super().__init__()
        self._dbpath = ''

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            SisypheDatabase instance representation
        """
        return 'SisypheDatabase instance at <{}>\n'.format(str(id(self)))

    def __getitem__(self, key: SisypheVolume | SisypheIdentity) -> str:
        """
        Special overloaded container getter method.
        Get patient folder name.

        Parameters
        ----------
        key : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            Patient identity

        Returns
        -------
        str
            patient folder name
        """
        if isinstance(key, SisypheVolume):
            key = key.getIdentity()
        if isinstance(key, SisypheIdentity):
            return self.getAbsFolderFromIdentity(key)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(key)))

    def __delitem__(self, key: SisypheVolume | SisypheIdentity) -> None:
        """
        Special overloaded container delete method called by the built-in del() python function.
        Remove patient folder.

        Parameters
        ----------
        key : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            Patient identity
        """
        self.removePatient(key)

    def __len__(self) -> int:
        """
        Special overloaded container method called by the built-in len() python function.
        Patient count in the current SisypheDatabase instance.

        Returns
        -------
        int
            Patient count
        """
        return self.getPatientCount()

    def __contains__(self, key: SisypheVolume | SisypheIdentity) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator.
        Checks whether a patient is in the current SisypheDatabase instance.

        Parameters
        ----------
        key : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            Patient identity

        Returns
        -------
        bool
            True if patient is in the current SisypheDatabase instance
        """
        if isinstance(key, SisypheVolume):
            key = key.getIdentity()
        if isinstance(key, SisypheIdentity):
            return self.hasPatient(key)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(key)))

    # Public methods

    def getAbsFolderFromIdentity(self, identity: SisypheVolume | SisypheIdentity) -> str:
        """
        Get patient folder name from identity.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        str
            folder name
        """
        if isinstance(identity, SisypheVolume):
            identity = identity.getIdentity()
        if isinstance(identity, SisypheIdentity):
            folder = self.getFolderFromIdentity(identity)
            return join(self.getDatabasePath(), folder)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))

    def setDatabasePath(self, path: str) -> None:
        """
        Set the PySisyphe patient database folder (root folder).

        Parameters
        ----------
        path : str
            folder name
        """
        path = abspath(path)
        if exists(path): self._dbpath = path
        else: mkdir(path)

    def setDatabasePathFromSettings(self) -> None:
        """
        Set the default PySisyphe patient database folder from PySisyphe settings file (~/.PySisyphe/settings.xml in
        user folder).
        """
        settings = SisypheSettings()
        path = settings.getFieldValue('Database', 'CurrentPath')
        if path and exists(path): self.setDatabasePath(path)
        else: self.setDefaultDatabasePath()

    def setDefaultDatabasePath(self) -> None:
        """
        Set the PySisyphe patient database folder to ~/.PySisyphe/Database (in user folder).
        """
        path = join(expanduser('~'), '.PySisyphe', 'database')
        self.setDatabasePath(path)

    def getDatabasePath(self) -> str:
        """
        Get the PySisyphe patient database folder (root folder).

        Returns
        -------
        str
            PySisyphe patient database folder
        """
        return self._dbpath

    def hasDatabasePath(self) -> bool:
        """
        Checks whether PySisyphe database folder exists.

        Returns
        -------
        bool
            True if the PySisyphe database folder exists
        """
        return self._dbpath != '' and exists(self._dbpath)

    def getPatientCount(self) -> int:
        """
        Get patient count in PySisyphe database.

        Returns
        -------
        int
            patient count
        """
        if self.hasDatabasePath():
            return len(self.getPatientList())
        else: raise AttributeError('Database folder is not defined or is empty.')

    def getPatientList(self, flt: str = '*_*_*') -> list[str]:
        """
        Get a list of patient folder names from a search filter string.

        Parameters
        ----------
        flt : str
            filter format is '{lastname}_{firstname}_{birthdate}', lastname, firstname, birthdate could be
            replaced by '*' wildcard char. default is '*_*_*' to get all patient folder names

        Returns
        -------
        list[str]
            patient folder names
        """
        r = []
        if self.hasDatabasePath():
            filt = join(self._dbpath, flt)
            folders = glob(filt)
            if len(folders) > 0:
                for folder in folders:
                    if not isdir(folder): del folder
                r = folders
        return r

    def searchPatients(self, fltlastname: str = '*', fltfirstname: str = '*', fltdate: str = '*') -> list[str]:
        """
        Get a list of patient folder names from a search filter based on identity.

        Parameters
        ----------
        fltlastname : str
            lastname filter, default is '*' wildcard char
        fltfirstname : str
            firstname filter, default is '*' wildcard char.
        fltdate : str
            date filter, default is '*' wildcard char.

        Returns
        -------
        list[str]
            patient folder names
        """
        r = []
        if self.hasDatabasePath():
            if fltlastname == '': fltlastname = '*'
            if fltfirstname == '': fltfirstname = '*'
            if fltdate == '': fltdate = '*'
            if fltlastname != '*':
                fltlastname = ' '.join([ch[0].title() + ch[1:] for ch in fltlastname.split(' ')])
                fltlastname = '{}*'.format(fltlastname)
            if fltfirstname != '*':
                fltfirstname = ' '.join([ch[0].title() + ch[1:] for ch in fltfirstname.split(' ')])
                fltfirstname = '{}*'.format(fltfirstname)
            flt = join(self._dbpath, '_'.join([fltlastname, fltfirstname, fltdate]))
            folders = glob(flt)
            for folder in folders:
                if not isdir(folder): del folder
            r = folders
        return r

    def hasPatient(self, identity: SisypheVolume | SisypheIdentity) -> bool:
        """
        Checks whether a patient is in SisypheDatabase instance.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        bool
            True if patient is in database
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                return exists(folder)
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def getPatientVolumes(self, identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Get the list of Sisyphe.core.sisypheVolume.SisypheVolume file names (.xvol) in a patient folder.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            Sisyphe.core.sisypheVolume.SisypheVolume file names
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                if exists(folder):
                    flt = join(folder, '*{}'.format(SisypheVolume.getFileExt()))
                    return glob(flt)
                return []
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def getPatientROIs(self, identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Get the list of Sisyphe.core.sisypheROI.SisypheROI file names (.xroi) in a patient folder.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            Sisyphe.core.sisypheROI.SisypheROI file names
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                if exists(folder):
                    flt = join(folder, '*{}'.format(SisypheROI.getFileExt()))
                    return glob(flt)
                else: return []
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def getPatientMeshes(self, identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Get the list of Sisyphe.core.sisypheMesh.SisypheMesh file names (.xmesh) in a patient folder.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            Sisyphe.core.sisypheMesh.SisypheMesh file names
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                if exists(folder):
                    flt = join(folder, '*{}'.format(SisypheMesh.getFileExt()))
                    return glob(flt)
                else: return []
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def getPatientTools(self, identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Get the list of Sisyphe.widget.toolWidgets.ToolWidgetCollection file names (.xtools) in a patient folder.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            Sisyphe.widget.toolWidgets.ToolWidgetCollection file names
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                if exists(folder):
                    flt = join(folder, '*{}'.format(ToolWidgetCollection.getFileExt()))
                    return glob(flt)
                else: return []
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def createPatient(self, identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Add a patient in the database, creates patient sub-folder in the database directory.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                if self.hasDatabasePath():
                    folder = self.getAbsFolderFromIdentity(identity)
                    if not exists(folder): mkdir(folder)
                    if QApplication.instance() is not None: QApplication.processEvents()
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database folder is not defined or is empty.')

    def createPatients(self, identities: list[SisypheVolume] | list[SisypheIdentity]) -> None:
        """
        Add a list of patients in the database, creates patient sub-folders in the database directory.

        Parameters
        ----------
        identities : list[Sisyphe.core.sisypheVolume.SisypheVolume] | list[Sisyphe.core.SisypheImageAttributes.SisypheIdentity]
            patient identities
        """
        if self.hasDatabasePath():
            if isinstance(identities, list):
                for identity in identities:
                    self.createPatient(identity)
                    if QApplication.instance() is not None: QApplication.processEvents()
        else: raise ValueError('Database is not defined or is empty.')

    def removePatient(self, identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Remove a patient from the database, delete patient sub-folder of the database directory.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(identity, SisypheVolume):
                identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                folder = self.getAbsFolderFromIdentity(identity)
                if exists(folder): rmtree(folder, ignore_errors=True)
                if QApplication.instance() is not None: QApplication.processEvents()
            else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
        else: raise ValueError('Database is not defined or is empty.')

    def removePatients(self, identities: list[SisypheVolume] | list[SisypheIdentity]) -> None:
        """
        Removes a list of patients from the database, deletes patient sub-folders of the database directory.

        Parameters
        ----------
        identities : list[Sisyphe.core.sisypheVolume.SisypheVolume] | list[Sisyphe.core.SisypheImageAttributes.SisypheIdentity]
            patient identities
        """
        if self.hasDatabasePath():
            if isinstance(identities, list):
                for identity in identities:
                    self.removePatient(identity)
        else: raise ValueError('Database is not defined or is empty.')

    def clearDatabase(self) -> None:
        """
        Clear the patient database, deletes all sub-folders of the database directory.
        """
        if self.hasDatabasePath():
            folders = self.getPatientList()
            for folder in folders:
                rmtree(folder, ignore_errors=True)
                if QApplication.instance() is not None: QApplication.processEvents()

    def copyFileToPatient(self, filename: str, identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Copy a file to a patient folder.

        Parameters
        ----------
        filename : str
            file name to copy
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(filename, str) and exists(filename):
                if isinstance(identity, SisypheVolume):
                    identity = identity.getIdentity()
                if isinstance(identity, SisypheIdentity):
                    folder = self.getAbsFolderFromIdentity(identity)
                    if not exists(folder): self.createPatient(identity)
                    dbname = join(folder, basename(filename))
                    copy(filename, dbname)
                    if QApplication.instance() is not None: QApplication.processEvents()
                else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
            else: raise FileNotFoundError('no such file {}.'.format(basename(filename)))
        else: raise ValueError('Database is not defined or is empty.')

    def copyFilesToPatient(self, filenames: list[str], identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Copy a list of files to a patient folder.

        Parameters
        ----------
        filenames : list[str]
            list of file names to copy
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(filenames, list):
                for filename in filenames:
                    self.copyFileToPatient(filename, identity)
        else: raise ValueError('Database is not defined or is empty.')

    def deleteFileFromPatient(self, filename: str, identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Remove a file from a patient folder.

        Parameters
        ----------
        filename : str
            file name to remove
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(filename, str) and exists(filename):
                if isinstance(identity, SisypheVolume):
                    identity = identity.getIdentity()
                if isinstance(identity, SisypheIdentity):
                    folder = self.getAbsFolderFromIdentity(identity)
                    if exists(folder):
                        if dirname(filename) != folder: filename = join(folder, basename(filename))
                        if exists(filename):
                            remove(filename)
                            if splitext(filename)[1] == SisypheVolume.getFileExt():
                                # remove raw
                                filename = splitext(filename)[0] + '.raw'
                                if exists(filename): remove(filename)
                                # remove xtrfs
                                filename = splitext(filename)[0] + SisypheTransforms.getFileExt()
                                if exists(filename): remove(filename)
                                # remove xdcm
                                filename = splitext(filename)[0] + XmlDicom.getFileExt()
                                if exists(filename): remove(filename)
                                # remove xtools
                                filename = splitext(filename)[0] + ToolWidgetCollection.getFileExt()
                                if exists(filename): remove(filename)
                            if splitext(filename)[1] == SisypheROI.getFileExt():
                                # remove raw
                                filename = splitext(filename)[0] + '.raw'
                                if exists(filename): remove(filename)
                    if QApplication.instance() is not None: QApplication.processEvents()
                else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(type(identity)))
            else: raise FileNotFoundError('no such file {}.'.format(basename(filename)))
        else: raise ValueError('Database is empty or is empty.')

    def deleteFilesFromPatient(self, filenames: list[str], identity: SisypheVolume | SisypheIdentity) -> None:
        """
        Remove a list of files from patient folder.

        Parameters
        ----------
        filenames : list[str]
            list of file names to remove
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(filenames, list):
                for filename in filenames:
                    self.deleteFileFromPatient(filename, identity)
        else: raise ValueError('Database is not defined or is empty.')

    def saveSisypheVolumeToDatabase(self, vol: SisypheVolume, filename: str) -> None:
        """
        Save a Sisyphe.core.sisypheVolume.SisypheVolume file (.xvol) in its patient folder.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume to save
        filename : str
            Sisyphe.core.sisypheVolume.SisypheVolume file name
        """
        if self.hasDatabasePath():
            if isinstance(vol, SisypheVolume):
                if isinstance(filename, str):
                    identity = vol.getIdentity()
                    if not self.hasPatient(identity): self.createPatient(identity)
                    filename = basename(splitext(filename)[0]) + SisypheVolume.getFileExt()
                    filename = join(self.getAbsFolderFromIdentity(identity), filename)
                    vol.saveAs(filename)
                    if QApplication.instance() is not None: QApplication.processEvents()
                else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
            else: raise TypeError('parameter type {} is not SisypheVolume'.format(type(vol)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheVolume(self, vol: SisypheVolume) -> None:
        """
        Copy a Sisyphe.core.sisypheVolume.SisypheVolume file (.xvol) in its patient folder.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume is saved in the patient folder with its file name attribute
        """
        if self.hasDatabasePath():
            if isinstance(vol, SisypheVolume):
                if vol.hasFilename():
                    filename = vol.getFilename()
                    # xvol
                    if exists(filename): self.copyFileToPatient(filename, vol.getIdentity())
                    # raw
                    filename = splitext(filename)[0] + '.raw'
                    if exists(filename): self.copyFileToPatient(filename, vol.getIdentity())
                    # xtrfs
                    filename = splitext(filename)[0] + vol.getTransforms().getFileExt()
                    if exists(filename): self.copyFileToPatient(filename, vol.getIdentity())
                    # xdcm
                    filename = splitext(filename)[0] + XmlDicom.getFileExt()
                    if exists(filename): self.copyFileToPatient(filename, vol.getIdentity())
                    # xtools
                    filename = splitext(filename)[0] + ToolWidgetCollection.getFileExt()
                    if exists(filename): self.copyFileToPatient(filename, vol.getIdentity())
                    if QApplication.instance() is not None: QApplication.processEvents()
                else: raise ValueError('SisypheVolume parameter does not have filename.')
            else: raise TypeError('parameter type {} is not a SisypheVolume.'.format(type(vol)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheVolumes(self, vols: list[SisypheVolume] | SisypheVolumeCollection) -> None:
        """
        Copy a list of Sisyphe.core.sisypheVolume.SisypheVolume file (.xvol) in the database.

        Parameters
        ----------
        vols : list[Sisyphe.core.sisypheVolume.SisypheVolume] | Sisyphe.core.sisypheVolume.SisypheVolumeCollection
            volumes are saved in the patient folders with their file name attributes
        """
        if self.hasDatabasePath():
            if isinstance(vols, list):
                for vol in vols:
                    self.copySisypheVolume(vol)
        else: raise ValueError('Database is not defined.')

    def saveSisypheROItoDatabase(self, roi: SisypheROI, identity: SisypheIdentity, filename: str) -> None:
        """
        Save a Sisyphe.core.sisypheROI.SisypheROI file (.xroi) in its patient folder.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            ROI to save
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        filename : str
            Sisyphe.core.sisypheROI.SisypheROI file name
        """
        if self.hasDatabasePath():
            if isinstance(roi, SisypheROI):
                if isinstance(identity, SisypheIdentity):
                    if isinstance(filename, str):
                        if not self.hasPatient(identity): self.createPatient(identity)
                        filename = basename(splitext(filename)[0]) + SisypheROI.getFileExt()
                        filename = join(self.getAbsFolderFromIdentity(identity), filename)
                        roi.saveAs(filename)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
                else: raise TypeError('parameter type {} is not SisypheIdentity'.format(type(identity)))
            else: raise TypeError('parameter type {} is not SisypheROI'.format(type(roi)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheROI(self, roi: SisypheROI, identity: SisypheIdentity) -> None:
        """
        Copy a Sisyphe.core.sisypheROI.SisypheROI file (.xroi) in its patient folder.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            ROI to copy
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(roi, SisypheROI):
                if isinstance(identity, SisypheIdentity):
                    if roi.hasFilename():
                        # xroi
                        filename = roi.getFilename()
                        if exists(filename): self.copyFileToPatient(filename, identity)
                        # raw
                        filename = splitext(filename)[0] + '.raw'
                        if exists(filename): self.copyFileToPatient(filename, identity)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise ValueError('SisypheROI parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheROI.'.format(type(roi)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheROIs(self, rois: list[SisypheROI] | SisypheROICollection, identity: SisypheIdentity) -> None:
        """
        Copy a list of Sisyphe.core.sisypheROI.SisypheROI files (.xroi) in the database.

        Parameters
        ----------
        rois : list[Sisyphe.core.sisypheROI.SisypheROI] | Sisyphe.core.sisypheROI.SisypheROICollection
            ROIs to copy
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(rois, list):
                for roi in rois:
                    self.copySisypheROI(roi, identity)
        else: raise ValueError('Database is not defined or is empty.')

    def saveSisypheMeshtoDatabase(self, mesh: SisypheMesh, identity: SisypheIdentity, filename: str) -> None:
        """
        Save a Sisyphe.core.sisypheMesh.SisypheMesh file (.xmesh) in its patient folder.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to save
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        filename : str
            Sisyphe.core.sisypheMesh.SisypheMesh file name
        """
        if self.hasDatabasePath():
            if isinstance(mesh, SisypheMesh):
                if isinstance(identity, SisypheIdentity):
                    if isinstance(filename, str):
                        if not self.hasPatient(identity): self.createPatient(identity)
                        filename = basename(splitext(filename)[0]) + SisypheMesh.getFileExt()
                        filename = join(self.getAbsFolderFromIdentity(identity), filename)
                        mesh.saveAs(filename)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
                else: raise TypeError('parameter type {} is not SisypheIdentity'.format(type(identity)))
            else: raise TypeError('parameter type {} is not SisypheROI'.format(type(mesh)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheMesh(self, mesh: SisypheMesh, identity: SisypheIdentity) -> None:
        """
        Copy a Sisyphe.core.sisypheROI.SisypheROI file (.xmesh) in its patient folder.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to copy
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(mesh, SisypheMesh):
                if isinstance(identity, SisypheIdentity):
                    if mesh.hasFilename():
                        filename = mesh.getFilename()
                        if exists(filename): self.copyFileToPatient(filename, identity)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise ValueError('SisypheMesh parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheMesh.'.format(type(mesh)))
        else: raise ValueError('Database is not defined or is empty.')

    def copySisypheMeshes(self, meshes: list[SisypheMesh] | SisypheMeshCollection, identity: SisypheIdentity) -> None:
        """
        Save a list of Sisyphe.core.sisypheMesh.SisypheMesh files (.xmesh) in the database.

        Parameters
        ----------
        meshes : list[Sisyphe.core.sisypheMesh.SisypheMesh] | Sisyphe.core.sisypheMesh.SisypheMeshCollection
            meshes to save
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(meshes, list):
                for mesh in meshes:
                    self.copySisypheMesh(mesh, identity)
        else: raise ValueError('Database is not defined or is empty.')

    def hasSisypheVolume(self, vol: SisypheVolume) -> bool:
        """
        Checks whether Sisyphe.core.sisypheVolume.SisypheVolume is in the database.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume to search in database

        Returns
        -------
        bool
            True if vol is in database
        """
        if self.hasDatabasePath():
            if isinstance(vol, SisypheVolume):
                if vol.hasFilename():
                    folder = self.getAbsFolderFromIdentity(vol.getIdentity())
                    filename = join(folder, basename(vol.getFilename()))
                    return exists(filename)
                else: raise ValueError('SisypheVolume parameter does not have filename.')
            else: raise TypeError('parameter type {} is not a SisypheVolume.'.format(type(vol)))
        else: raise ValueError('Database is not defined or is empty.')

    def hasSisypheROI(self, roi: SisypheROI, identity: SisypheIdentity) -> bool:
        """
        Checks whether Sisyphe.core.sisypheROI.SisypheROI is in the database.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            ROI to search in database
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        bool
            True if roi is in database
        """
        if self.hasDatabasePath():
            if isinstance(roi, SisypheROI):
                if isinstance(identity, SisypheIdentity):
                    if roi.hasFilename():
                        folder = self.getAbsFolderFromIdentity(identity)
                        filename = join(folder, basename(roi.getFilename()))
                        return exists(filename)
                    else: raise ValueError('SisypheROI parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheROI.'.format(type(roi)))
        else: raise ValueError('Database is not defined.')

    def hasSisypheMesh(self, mesh: SisypheMesh, identity: SisypheIdentity) -> bool:
        """
        Checks whether Sisyphe.core.sisypheMesh.SisypheMesh is in the database.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to search in database
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        bool
            True if mesh is in database
        """
        if self.hasDatabasePath():
            if isinstance(mesh, SisypheMesh):
                if isinstance(identity, SisypheIdentity):
                    if mesh.hasFilename():
                        folder = self.getAbsFolderFromIdentity(identity)
                        filename = join(folder, basename(mesh.getFilename()))
                        return exists(filename)
                    else: raise ValueError('SisypheMesh parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheMesh.'.format(type(mesh)))
        else: raise ValueError('Database is not defined.')

    def removeSisypheVolume(self, vol: SisypheVolume) -> None:
        """
        Remove Sisyphe.core.sisypheVolume.SisypheVolume from the database.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume to remove
        """
        if self.hasDatabasePath():
            if isinstance(vol, SisypheVolume):
                if vol.hasFilename():
                    folder = self.getAbsFolderFromIdentity(vol.getIdentity())
                    filename = join(folder, basename(vol.getFilename()))
                    # remove xvol
                    if exists(filename): remove(filename)
                    # remove raw
                    filename = splitext(filename)[0] + '.raw'
                    if exists(filename): remove(filename)
                    # remove xtrfs
                    filename = splitext(filename)[0] + vol.getTransforms().getFileExt()
                    if exists(filename): remove(filename)
                    # remove xdcm
                    filename = splitext(filename)[0] + XmlDicom.getFileExt()
                    if exists(filename): remove(filename)
                    # remove xtools
                    filename = splitext(filename)[0] + ToolWidgetCollection.getFileExt()
                    if exists(filename): remove(filename)
                    if QApplication.instance() is not None: QApplication.processEvents()
                else: raise ValueError('SisypheVolume parameter does not have filename.')
            else: raise TypeError('parameter type {} is not a SisypheVolume.'.format(type(vol)))
        else: raise ValueError('Database is not defined or is empty.')

    def removeSisypheROI(self, roi: SisypheROI, identity: SisypheIdentity) -> None:
        """
        Remove Sisyphe.core.sisypheROI.SisypheROI from the database.

        Parameters
        ----------
        roi : Sisyphe.core.sisypheROI.SisypheROI
            ROI to remove
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(roi, SisypheROI):
                if isinstance(identity, SisypheIdentity):
                    if roi.hasFilename():
                        folder = self.getAbsFolderFromIdentity(identity)
                        # remove xroi
                        filename = join(folder, basename(roi.getFilename()))
                        if exists(filename): remove(filename)
                        # remove raw
                        filename = splitext(filename)[0] + '.raw'
                        if exists(filename): remove(filename)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise ValueError('SisypheROI parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheROI.'.format(type(roi)))
        else: raise ValueError('Database is not defined or is empty.')

    def removeSisypheMesh(self, mesh: SisypheMesh, identity: SisypheIdentity) -> None:
        """
        Remove Sisyphe.core.sisypheMesh.SisypheMesh from the database.

        Parameters
        ----------
        mesh : Sisyphe.core.sisypheMesh.SisypheMesh
            mesh to remove
        identity : Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        """
        if self.hasDatabasePath():
            if isinstance(mesh, SisypheMesh):
                if isinstance(identity, SisypheIdentity):
                    if mesh.hasFilename():
                        folder = self.getAbsFolderFromIdentity(identity)
                        filename = join(folder, basename(mesh.getFilename()))
                        if exists(filename): remove(filename)
                        if QApplication.instance() is not None: QApplication.processEvents()
                    else: raise ValueError('SisypheMesh parameter does not have filename.')
                else: raise TypeError('parameter type {} is not SisypheIdentity.'.format(type(identity)))
            else: raise TypeError('parameter type {} is not a SisypheMesh.'.format(type(mesh)))
        else: raise ValueError('Database is empty or is empty.')

    def isEmpty(self) -> bool:
        """
        Checks whether patient database is empty.

        Returns
        -------
        bool
            True if patient database is empty
        """
        if self.hasDatabasePath():
            return self.getPatientCount() == 0
        else: return True

    def backupIdentity(self, identity: SisypheVolume | SisypheIdentity, backuppath: str) -> None:
        """
        Copy a patient folder to a backup directory.

        Parameters
        ----------
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity
        backuppath : str
            backup folder name
        """
        if isinstance(identity, SisypheVolume):
            identity = identity.getIdentity()
        if isinstance(identity, SisypheIdentity):
            folder = self.getFolderFromIdentity(identity)
            self.backupPatient(folder, backuppath)
        else: raise TypeError('parameter type {} is not SisypheVolume or SisypheIdentity.'.format(identity))

    def backupPatient(self, patient: str, backuppath: str) -> None:
        """
        Copy a patient folder to a backup directory.

        Parameters
        ----------
        patient : str
            patient folder name
        backuppath : str
            backup folder name
        """
        if self.hasDatabasePath():
            if isinstance(patient, str):
                if exists(patient):
                    filelist = self.getFilesLastModifiedDate(patient)
                    backuppath = join(backuppath, basename(patient))
                    if not exists(backuppath): mkdir(backuppath)
                    for f in filelist:
                        backupfile = join(backuppath, basename(f))
                        if exists(backupfile):
                            if filelist[f] > getmtime(backupfile):
                                copy(f, backupfile)
                        else:
                            copy(f, backuppath)
                        if QApplication.instance() is not None: QApplication.processEvents()
                else: raise FileExistsError('folder {} does not exist.'.format(patient))
            else: raise TypeError('parameter type {} is not str.'.format(type(patient)))
        else: raise ValueError('Database is not defined or is empty.')

    def backupDatabase(self, backuppath: str, wait: DialogWait | None = None) -> None:
        """
        Copy database to a backup directory.

        Parameters
        ----------
        backuppath : str
            backup folder name
        wait : Sisyphe.core.dialogWait.DialogWait
            progress bar dialog
        """
        if self.hasDatabasePath():
            if not isinstance(wait, DialogWait): wait = None
            if isinstance(backuppath, str):
                if not exists(backuppath): mkdir(backuppath)
                patients = self.getPatientList()
                n = len(patients)
                if n > 0:
                    if wait:
                        wait.open()
                        wait.setProgressRange(0, n)
                        wait.setCurrentProgressValue(0)
                        wait.setProgressVisibility(n > 1)
                        wait.buttonVisibilityOn()
                        wait.progressTextVisibilityOn()
                        wait.setInformationText('Database backup...')
                    for patient in patients:
                        if wait: wait.setInformationText('Backup {}'.format(basename(patient)))
                        self.backupPatient(patient, backuppath)
                        if wait: wait.incCurrentProgressValue()
                        if wait.getStopped(): break
            else: raise TypeError('parameter type {} is not str.'.format(type(backuppath)))
        else: raise ValueError('Database is not defined or is empty.')

    def searchSisypheVolumeFromID(self,
                                  ID: SisypheROI | SisypheMesh | SisypheTransforms | ToolWidgetCollection | str,
                                  identity: SisypheVolume | SisypheIdentity) -> str | None:
        """
        Search Sisyphe.core.sisypheVolume.SisypheVolume from ID (str or ID attributes) in patient folder.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheROI.SisypheROI | Sisyphe.core.sisypheMesh.SisypheMesh
        | Sisyphe.core.sisypheTransform.SisypheTransforms | Sisyphe.widget.toolWidgets.ToolWidgetCollection
            ID to search
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        str
            volume file name
        """
        if isinstance(ID, SisypheROI): ID = ID.getReferenceID()
        if isinstance(ID, SisypheMesh): ID = ID.getReferenceID()
        if isinstance(ID, SisypheTransforms): ID = ID.getReferenceID()
        if isinstance(ID, ToolWidgetCollection): ID = ID.getReferenceID()
        if isinstance(ID, str):
            if isinstance(identity, SisypheVolume): identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                if self.hasDatabasePath():
                    r = None
                    filenames = self.getPatientVolumes(identity)
                    if len(filenames) > 0:
                        for filename in filenames:
                            xml = XmlVolume(filename)
                            if xml.getID() == ID:
                                r = filename
                                break
                            if QApplication.instance() is not None: QApplication.processEvents()
                    return r
                else: raise ValueError('Database is not defined or is empty.')
            else: raise TypeError('parameter identity type {} is not SisypheIdentity or SisypheVolume.'.format(identity))
        else: raise TypeError('parameter ID type {} is not str, SisypheROI, SisypheMesh, '
                              'SisypheTransforms or ToolWidgetCollection'.format(type(id)))

    def searchSisypheROIFromID(self,
                               ID: SisypheVolume | SisypheMesh | SisypheTransforms | ToolWidgetCollection | str,
                               identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Search Sisyphe.core.sisypheROI.SisypheROI from ID (str or ID attributes) in patient folder.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.sisypheMesh.SisypheMesh
        | Sisyphe.core.sisypheTransform.SisypheTransforms | Sisyphe.widget.toolWidgets.ToolWidgetCollection
            ID to search
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            list of ROI file names
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, SisypheMesh): ID = ID.getReferenceID()
        if isinstance(ID, SisypheTransforms): ID = ID.getReferenceID()
        if isinstance(ID, ToolWidgetCollection): ID = ID.getReferenceID()
        if isinstance(ID, str):
            if isinstance(identity, SisypheVolume): identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                if self.hasDatabasePath():
                    r = list()
                    filenames = self.getPatientROIs(identity)
                    if len(filenames) > 0:
                        for filename in filenames:
                            xml = XmlROI(filename)
                            if xml.getID() == ID:
                                r.append(filename)
                            if QApplication.instance() is not None: QApplication.processEvents()
                    return r
                else: raise ValueError('Database is not defined or is empty.')
            else: raise TypeError('parameter identity type {} is not SisypheIdentity or SisypheVolume.'.format(identity))
        else: raise TypeError('parameter ID type {} is not str, SisypheVolume, SisypheMesh, '
                              'SisypheTransforms or ToolWidgetCollection'.format(type(id)))

    def searchSisypheMeshFromID(self,
                                ID: SisypheVolume | SisypheROI | SisypheTransforms | ToolWidgetCollection | str,
                                identity: SisypheVolume | SisypheIdentity) -> list[str]:
        """
        Search Sisyphe.core.sisypheMesh.SisypheMesh from ID (str or ID attributes) in patient folder.

        Parameters
        ----------
        ID : str | Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.sisypheROI.SisypheROI
        | Sisyphe.core.sisypheTransform.SisypheTransforms | Sisyphe.widget.toolWidgets.ToolWidgetCollection
            ID to search
        identity : Sisyphe.core.sisypheVolume.SisypheVolume | Sisyphe.core.SisypheImageAttributes.SisypheIdentity
            patient identity

        Returns
        -------
        list[str]
            list of mesh file names
        """
        if isinstance(ID, SisypheVolume): ID = ID.getID()
        if isinstance(ID, SisypheROI): ID = ID.getReferenceID()
        if isinstance(ID, SisypheTransforms): ID = ID.getReferenceID()
        if isinstance(ID, ToolWidgetCollection): ID = ID.getReferenceID()
        if isinstance(ID, str):
            if isinstance(identity, SisypheVolume): identity = identity.getIdentity()
            if isinstance(identity, SisypheIdentity):
                if self.hasDatabasePath():
                    r = list()
                    filenames = self.getPatientMeshes(identity)
                    if len(filenames) > 0:
                        mesh = SisypheMesh()
                        for filename in filenames:
                            mesh.load(filename)
                            if mesh.getReferenceID() == ID:
                                r.append(filename)
                            if QApplication.instance() is not None: QApplication.processEvents()
                    return r
                else: raise ValueError('Database is not defined or is empty.')
            else: raise TypeError('parameter identity type {} is not SisypheIdentity or SisypheVolume.'.format(identity))
        else: raise TypeError('parameter ID type {} is not str, SisypheVolume, SisypheROI '
                              'SisypheTransforms or ToolWidgetCollection'.format(type(id)))
