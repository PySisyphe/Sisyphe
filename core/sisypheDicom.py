"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool,  https://pandas.pydata.org/
    - pydicom, DICOM library, https://pydicom.github.io/pydicom/stable/
    - PyQt5,Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - skimage, image processing, https://scikit-image.org/
"""

from os import getcwd
from os import mkdir
from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import isdir
from os.path import splitext
from os.path import join
from os.path import abspath

from datetime import date
from datetime import datetime

from math import sqrt

from numpy import array
from numpy import ndarray
from numpy import zeros
from numpy import frombuffer

from pandas import concat

from xml.dom import minidom

from pydicom.tag import Tag
from pydicom.dicomio import dcmread
from pydicom import Dataset
from pydicom import Sequence
from pydicom import DataElement
from pydicom.misc import is_dicom
from pydicom.uid import ExplicitVRLittleEndian
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset
from pydicom.datadict import dictionary_VR

from PyQt5.QtWidgets import QApplication

from SimpleITK import Cast
from SimpleITK import sitkLinear
from SimpleITK import Euler3DTransform
from SimpleITK import ResampleImageFilter
from SimpleITK import CenteredTransformInitializerFilter
from SimpleITK import GetArrayViewFromImage
from SimpleITK import GetImageFromArray

from skimage.draw import polygon2mask
from skimage.measure import find_contours

from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.core.sisypheImageIO import convertImageToAxialOrientation
from Sisyphe.core.sisypheImageIO import readFromDicomSeries
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DicomToXmlDicom',
           'XmlDicom',
           'DicomUIDGenerator',
           'ExportToDicom',
           'ImportFromDicom',
           'ImportFromRTDose',
           'ImportFromRTStruct',
           'ExportToRTStruct',
           'getDicomModalities',
           'getDicomImageModalities',
           'getDicomRTModalities',
           'getIdentityFromDicom',
           'getAcquisitionFromDicom',
           'getDiffusionParametersFromDicom',
           'mosaicImageToVolume',
           'saveBVal',
           'saveBVec',
           'loadBVal',
           'loadBVec',
           'removeSuffixNumberFromFilename']

"""
Functions
~~~~~~~~~

    - getDicomModalities
    - getDicomImageModalities
    - getDicomRTModalities
    - getIdentityFromDicom
    - getAcquisitionFromDicom
    - getDiffusionParametersFromDicom
    - mosaicImageToVolume
    - saveBVal
    - saveBVec
    - loadBVal
    - loadBVec
    - removeSuffixNumberFromFilename

Class hierarchy
~~~~~~~~~~~~~~~

    - object -> DicomToXmlDicom
             -> XmlDicom
             -> DicomUIDGenerator
             -> ExportToDicom
             -> ImportFromDicom
             -> ImportFromDicom -> ImportFromRTDose
                                -> ImportFromRTStruct
             -> ExportToRTStruct
"""

_DICOMMODALITIES = ['CT', 'MR', 'NM', 'PT', 'OT', 'RTDOSE', 'RTSTRUCT']


def getDicomModalities() -> list[str]:
    """
    Get list of DICOM modalities.
    DICOM modality format is two-chars str for images.

    Returns
    -------
    list[str]
        ['CT', 'MR', 'NM', 'PT', 'OT', 'RTDOSE', 'RTSTRUCT']
    """
    return _DICOMMODALITIES


def getDicomImageModalities() -> list[str]:
    """
    Get list of DICOM image modalities.
    DICOM modality format is two-chars str for images.

    Returns
    -------
    list[str]
        ['CT', 'MR', 'NM', 'PT', 'OT']
    """
    return _DICOMMODALITIES[:5]


def getDicomRTModalities() -> list[str]:
    """
    Get list of DICOM radiotherapy modalities.

    Returns
    -------
    list[str]
        ['RTDOSE', 'RTSTRUCT']
    """
    return _DICOMMODALITIES[-2:]

# noinspection PyBroadException
def getIdentityFromDicom(filename: str) -> SisypheIdentity:
    """
    Get patient identity information (Sisyphe.core.SisypheImageAttributes.SisypheIdentity) from DICOM file.

    Dicom fields used:

        - PatientName
        - PatientBirthDate
        - PatientSex

    Parameters
    ----------
    filename : str
        Dicom file name

    Returns
    -------
    Sisyphe.core.SisypheImageAttributes.SisypheIdentity
        patient identity
    """
    if isinstance(filename, str):
        if exists(filename):
            if is_dicom(filename):
                identity = SisypheIdentity()
                tags = [Tag(0x0010, 0x0010),
                        Tag(0x0010, 0x0030),
                        Tag(0x0010, 0x0040)]
                # < Revision 07/03/2025
                # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                # Revision 07/03/2025 >
                if QApplication.instance() is not None: QApplication.processEvents()
                # Patient name
                if 'PatientName' in ds:
                    if ds['PatientName'].VM > 0:
                        name = ds['PatientName'].value
                        if '^' in name: last, first = str(name).split('^')
                        elif ' ' in name: last, first = str(name).split(' ')
                        # < Revision 20/09/2024
                        # else: last, first = name, ''
                        else: last, first = str(name), ''
                        # Revision 20/09/2024 >
                        identity.setLastname(last)
                        identity.setFirstname(first)
                # Patient birthdate
                if 'PatientBirthDate' in ds:
                    if ds['PatientBirthDate'].VM > 0:
                        dob = ds['PatientBirthDate'].value
                        try: identity.setDateOfBirthday(dob, f='%Y%m%d')
                        except: identity.setDateOfBirthday()
                # Patient sex
                if 'PatientSex' in ds:
                    if ds['PatientSex'].VM > 0:
                        gender = ds['PatientSex'].value
                        if gender == 'M': identity.setGender('Male')
                        elif gender == 'F': identity.setGender('Female')
                        else: identity.setGender('Unknown')
                return identity
            else: raise ValueError('{} is not a valid Dicom file.'.format(basename(filename)))
        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
    else: raise TypeError('parameter type {} is not str'.format(type(filename)))


def getAcquisitionFromDicom(filename: str, useacqnumber: bool = False) -> SisypheAcquisition:
    """
    Get acquisition attributes (Sisyphe.core.SisypheImageAttributes.SisypheAcquisition) in DICOM file.

    Dicom fields used:

        - 0x0008, 0x0020  Study Date
        - 0x0008, 0x0021  Series Date
        - 0x0008, 0x0022  Acquisition Date
        - 0x0008, 0x0023  Content Date
        - 0x0008, 0x0060  Modality
        - 0x0008, 0x103e  Series Description
        - 0x0018, 0x0010  Contrast/Bolus Agent
        - 0x0018, 0x0023  MR Acquisition Type (2D or 3D)
        - 0x0020, 0x0012  Acquisition Number

    Parameters
    ----------
    filename : str
        Dicom file name
    useacqnumber : bool
        Add acquisition number in the SisypheAcquisition sequence attribute

    Returns
    -------
    Sisyphe.core.SisypheImageAttributes.SisypheIdentity
        patient identity
    """
    if isinstance(filename, str):
        if exists(filename):
            if is_dicom(filename):
                """
                0x0008, 0x0020  Study Date
                0x0008, 0x0021  Series Date
                0x0008, 0x0022  Acquisition Date
                0x0008, 0x0023  Content Date
                0x0008, 0x0060  Modality
                0x0008, 0x103e  Series Description
                0x0018, 0x0010  Contrast/Bolus Agent
                0x0018, 0x0023  MR Acquisition Type (2D or 3D)
                0x0020, 0x0012  Acquisition Number
                0x0028, 0x1054  Rescale Type
                0x0054, 0x1001  Units
                """
                acq = SisypheAcquisition()
                tags = [Tag(0x0008, 0x0020),
                        Tag(0x0008, 0x0021),
                        Tag(0x0008, 0x0022),
                        Tag(0x0008, 0x0023),
                        Tag(0x0008, 0x0060),
                        Tag(0x0008, 0x103e),
                        Tag(0x0018, 0x0010),
                        Tag(0x0018, 0x0023),
                        Tag(0x0020, 0x0012)]
                # < Revision 07/03/2025
                # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                # Revision 07/03/2025 >
                if QApplication.instance() is not None: QApplication.processEvents()
                modality = ds['Modality'].value
                sequence = ''
                unit = acq.NOUNIT
                if 'MRAcquisitionType' in ds:
                    acq.setType(ds['MRAcquisitionType'].value)
                if 'SeriesDescription' in ds:
                    sequence = ds['SeriesDescription'].value
                    sq = sequence.upper()
                    if modality == 'MR':
                        ce = ''
                        if 'ContrastBolusAgent' in ds:
                            if ds['ContrastBolusAgent'].value.upper() == 'YES': ce = '{} '.format(acq.CECT)
                        if 'T1' in sq: sequence = ce + acq.T1
                        elif 'T2' in sq: sequence = ce + acq.T2
                        elif 'FLAIR' in sq: sequence = ce + acq.FLAIR
                        elif 'SWI' in sq: sequence = acq.SWI
                        elif 'TOF' in sq: sequence = ce + acq.TOF
                        elif 'ADC' in sq: modality, sequence, unit = 'OT', acq.ADC, acq.ADC
                        elif 'FA' in sq: modality, sequence, unit = 'OT', acq.FA, acq.RATIO
                        elif ('DTI' or 'DWI' or 'DIFFUSION') in sq: sequence = acq.DWI
                        elif 'B0' in sq: sequence = acq.B0
                        elif ('PD' or 'DP') in sq: sequence = acq.PD
                        else: sequence = ds['SeriesDescription'].value
                        # < Revision 26/09/2024
                        # Add acquisition number
                        if useacqnumber and 'AcquisitionNumber' in ds:
                            sequence += '_{}'.format(ds['AcquisitionNumber'].value)
                        # Revision 26/09/2024 >
                if 'StudyDate' in ds: dos = ds['StudyDate'].value
                elif 'SeriesDate' in ds: dos = ds['SeriesDate'].value
                elif 'AcquisitionDate' in ds: dos = ds['AcquisitionDate'].value
                elif 'ContentDate' in ds: dos = ds['ContentDate'].value
                else: dos = date.today().strftime('%Y%m%d')
                # < Revision 24/10/2024
                # Units for CT, PT and NM modalities
                if modality == 'CT': acq.setUnitToHounsfield()
                elif modality == 'PT':
                    v = None
                    if 'Units' in ds: v = ds['Units'].value
                    elif 'RescaleType' in ds: v = ds['RescaleType'].value
                    if v is not None:
                        if v == 'CNTS': unit = acq.COUNT
                        elif v == 'CPS': unit = acq.BQ
                        elif v == 'BQML': unit = acq.BQML
                elif modality == 'NM': unit = acq.COUNT
                elif modality == 'RTDOSE':
                    # < Revision 21/09/2024
                    # modality = 'OT'
                    modality = acq.getOTModalityTag()
                    # Revision 21/09/2024 >
                    sequence = acq.DOSE
                    unit = acq.GY
                # Revision 24/10/2024 >
                acq.setModality(modality)
                acq.setSequence(sequence)
                acq.setUnit(unit)
                acq.setDateOfScan(dos, f='%Y%m%d')
                return acq
            else: raise ValueError('{} is not a valid Dicom file.'.format(basename(filename)))
        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
    else: raise TypeError('parameter type {} is not str'.format(type(filename)))


def getDiffusionParametersFromDicom(filename: str) -> dict[str: float, str: list[float]]:
    """
    Get diffusion attributes B-value and gradient direction in DICOM file.

    Parameters
    ----------
    filename : str
        Dicom file name

    Returns
    -------
    dict[str: float, str: list[float]]
        Key/Value
            - 'bval': float, B-value
            - 'bvec': list[float], gradient direction vector
    """
    if isinstance(filename, str):
        if exists(filename):
            if is_dicom(filename):
                """
                    Siemens diffusion
                        0x0019, 0x100c FD, B value
                        0x0019, 0x100e FD, Diffusion gradient direction
                    Dicom diffusion
                        0x0018, 0x9087 IS, B value
                        0x0018, 0x9089 FD, Diffusion gradient direction
                """
                tags = [Tag(0x0018, 0x9087),
                        Tag(0x0018, 0x9089),
                        Tag(0x0019, 0x100c),
                        Tag(0x0019, 0x100e)]
                # < Revision 07/03/2025
                # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                # Revision 07/03/2025 >
                if QApplication.instance() is not None: QApplication.processEvents()
                r = dict()
                if Tag(0x0018, 0x9087) in ds: r['bval'] = ds[0x0018, 0x9087].value
                elif Tag(0x0019, 0x100c) in ds:
                    v = ds[0x0019, 0x100c].value
                    if isinstance(v, bytes): v = v.decode()
                    r['bval'] = int(v)
                else: r['bval'] = 0
                if Tag(0x0018, 0x9089) in ds: r['bvec'] = ds[0x0018, 0x9089].value
                elif Tag(0x0019, 0x100e) in ds:
                    v = ds[0x0019, 0x100e].value
                    if isinstance(v, bytes): v = list(frombuffer(v, dtype=float))
                    r['bvec'] = v
                else: r['bvec'] = [0.0, 0.0, 0.0]
                return r
            else: raise IOError('{} is not a valid Dicom file.'.format(basename(filename)))
        else: raise IOError('No such file {}'.format(basename(filename)))
    else: raise TypeError('parameter type {} is not str'.format(type(filename)))


def mosaicImageToVolume(slc: ndarray, n: int) -> ndarray:
    """
    Siemens Mosaic 2D image to 3D volume conversion. Mosaic is a grid of n^2 images (n columns x n rows), all the
    slices of a volume are stored in a single DICOM mosaic file.

    Parameters
    ----------
    slc : numpy.ndarray
        2D mosaic image (ndarray, ndim=2)
    n : int
        columns/rows count

    Returns
    -------
    numpy.ndarray
        3D volume
    """
    d, slcr, slcc = slc.shape
    if d == 1:
        if slcr == slcc:
            rn = int(sqrt(n))
            vn = int(slcr // rn)
            vol = zeros([n, vn, vn])
            for r in range(rn):
                for c in range(rn):
                    vol[r * rn + c, :, :] = slc[0, r * vn:(r + 1) * vn, c * vn:(c + 1) * vn]
            return vol
        else: return slc
    else: raise ValueError('parameter is not a 2D ndarray.')


# noinspection PyShadowingBuiltins
def saveBVal(filename: str,
             bval: dict[str: float],
             format: str = 'txt') -> None:
    """
    Save gradient B-values.

    Parameters
    ----------
    filename : str
        file name (.bval, .xbval or .txt)
    bval : dict[str: float]
        - key str, diffusion weighted image file name (.xvol) or index number
        - value float, B value
    format : str
        - 'xml', xml format <bvalue file=filename>v</bvector>
        - 'txt', txt format, v[0] -> v[1] ... -> v[n]
    """
    if format in ('txtbydim', 'txtbyvec', 'txt'):
        filename = splitext(filename)[0] + '.bval'
        txt = ' '.join([str(v) for v in bval.values()])
        with open(filename, 'w') as f:
            f.write(txt)
    elif format == 'xml':
        filename = splitext(filename)[0] + '.xbval'
        doc = minidom.Document()
        root = doc.createElement('xbval')
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        for k, v in bval.items():
            node = doc.createElement('bvalue')
            node.setAttribute('file', basename(k))
            root.appendChild(node)
            txt = doc.createTextNode(str(v))
            node.appendChild(txt)
        buffxml = doc.toprettyxml().encode()
        with open(filename, 'wb') as f:
            f.write(buffxml)


# noinspection PyShadowingBuiltins
def saveBVec(filename: str,
             bvec: dict[str: [float, float, float]],
             format='txtbydim') -> None:
    """
    Save gradient direction vector.

    Parameters
    ----------
    filename : str
        file name (.bvec, .xbvec or .txt)
    bvec : dict[str: [float, float, float]],
        - key str, diffusion weighted image file name (.xvol) or index number
        - value [float, float, float], gradient direction vector
    format : str
        - 'xml', xml format <bvector file=filename>v0[0] v0[1] v0[2]</bvector>
        - 'txtbyvec', txt format, vector order, v0[0] -> v0[1] -> v0[2] -> ... -> vn[0] -> vn[1] -> vn[2]
        - 'txtbydim', txt format, dimension order, v0[0] -> ... -> vn[0], v0[1] -> ... -> vn[1], v0[2] -> ... -> vn[2]
    """
    if format == 'txtbyvec':
        filename = splitext(filename)[0] + '.bvec'
        txt = ' '.join(['{0[0]} {0[1]} {0[2]}'.format(v) for v in bvec.values()])
        with open(filename, 'w') as f:
            f.write(txt)
    elif format == 'txtbydim':
        filename = splitext(filename)[0] + '.bvec'
        values = list(bvec.values())
        with open(filename, 'w') as f:
            for i in range(3):
                txt = ' '.join([str(v[i]) for v in values]) + '\n'
                f.write(txt)
    elif format == 'xml':
        filename = splitext(filename)[0] + '.xbvec'
        doc = minidom.Document()
        root = doc.createElement('xbvec')
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        for k, v in bvec.items():
            node = doc.createElement('bvector')
            node.setAttribute('file', basename(k))
            root.appendChild(node)
            v = [str(i) for i in v]
            txt = doc.createTextNode(' '.join(v))
            node.appendChild(txt)
        buffxml = doc.toprettyxml().encode()
        with open(filename, 'wb') as f:
            f.write(buffxml)


# noinspection PyShadowingBuiltins
def loadBVal(filename: str,
             format='txt',
             numpy=False) -> dict[str: float] | ndarray:
    """
    Load gradient B-values.

    Parameters
    ----------
    filename : str
        file name (.bval, .xbval or .txt)
    format : str
        - 'xml', xml format <bvalue file=filename>v</bvector>
        - 'txt', txt format, v[0] -> v[1] ... -> v[n]
    numpy : bool
        return type is ndarray (True) or dict (False)

    Returns
    -------
    ndarray | dict[str: float]
        if numpy parameter is False:
            - key str, diffusion weighted image file name (.xvol) or index number
            - value float, B-value
    """
    if format in ('txtbydim', 'txtbyvec', 'txt'):
        with open(filename, 'r') as f:
            v = f.readline()
        v = [float(i) for i in v.split(' ')]
        r = dict()
        for i in range(len(v)): r[str(i)] = v[i]
        if numpy: r = array(list(r.values()))
        return r
    elif format == 'xml':
        r = dict()
        with open(filename, 'rb') as f:
            line = ''
            strdoc = ''
            while line != '</xbval>\n':
                line = f.readline().decode()  # Convert binary to utf-8
                strdoc += line
            doc = minidom.parseString(strdoc)
            root = doc.documentElement
            if root.nodeName == 'xbval' and root.getAttribute('version') <= '1.0':
                node = root.firstChild
                while node:
                    if node.nodeName == 'bvalue':
                        v = node.firstChild.data
                        if v is None: v = 0.0
                        r[node.getAttribute('file')] = float(v)
                    node = node.nextSibling
            if numpy: r = array(list(r.values()))
            return r
    else: raise ValueError('{} is not a valid format parameter (xml, txtbydim, txtbyvec, txt).'.format(format))


# noinspection PyShadowingBuiltins
def loadBVec(filename: str,
             format='txtbydim',
             numpy=False) -> dict[str: [float, float, float]] | ndarray:
    """
    Load gradient direction vector.

    Parameters
    ----------
    filename : str
        file name (.bvec, .xbvec or .txt)
    format : str
        - 'xml', xml format <bvector file=filename>v0[0] v0[1] v0[2]</bvector>
        - 'txtbyvec', txt format, vector order, v0[0] -> v0[1] -> v0[2] -> ... -> vn[0] -> vn[1] -> vn[2]
        - 'txtbydim', txt format, dimension order, v0[0] -> ... -> vn[0], v0[1] -> ... -> vn[1], v0[2] -> ... -> vn[2]
    numpy : bool
        return type is ndarray (True) or dict (False)

    Returns
    -------
    ndarray | dict[str: [float, float, float]]
        if numpy parameter is False:
            - key str, diffusion weighted image file name (.xvol) or index number,
            - value [float, float, float], gradient direction vector
    """
    if format == 'txtbyvec':
        with open(filename, 'r') as f:
            v = f.readline()
        v = [float(i) for i in v.split(' ')]
        if len(v) % 3 == 0:
            r = dict()
            for i in range(0, len(v), 3):
                r[str(i // 3)] = v[i:i + 3]
            if numpy: r = array(list(r.values()))
            return r
        else: raise ValueError('Less than 3 elements in current vector.')
    elif format == 'txtbydim':
        r = list()
        with open(filename, 'r') as f:
            for i in range(3):
                v = f.readline()
                v = [float(i) for i in v.split(' ')]
                r.append(v)
        r = array(r).transpose()
        if numpy: return r
        else:
            d = dict()
            for i in range(r.shape[1]):
                d[i] = r[i, :]
            return d
    elif format == 'xml':
        r = dict()
        with open(filename, 'rb') as f:
            line = ''
            strdoc = ''
            while line != '</xbvec>\n':
                line = f.readline().decode()  # Convert binary to utf-8
                strdoc += line
            doc = minidom.parseString(strdoc)
            root = doc.documentElement
            if root.nodeName == 'xbvec' and root.getAttribute('version') <= '1.0':
                node = root.firstChild
                while node:
                    if node.nodeName == 'bvector':
                        v = node.firstChild.data
                        if v is None: v = [0.0, 0.0, 0.0]
                        r[node.getAttribute('file')] = [float(i) for i in v.split(' ')]
                    node = node.nextSibling
            if numpy: r = array(list(r.values()))
            return r
    else: raise ValueError('{} is not a valid format parameter (xml, txtbydim, txtbyvec, txt).'.format(format))

def removeSuffixNumberFromFilename(filename: str) -> str:
    """
    Remove numerical suffix from a file name.
    ex: '../image_01.xvol' -> '../image.xvol'

    Parameters
    ----------
    filename : str
        file name

    Returns
    -------
    str
        file name
    """
    base, ext = splitext(filename)
    splt1 = base.split(' ')
    splt2 = base.split('_')
    if len(splt1[-1]) < len(splt2[-1]):
        splt = splt1
        s = ' '
    else:
        splt = splt2
        s = '_'
    sfx = splt[-1]
    if sfx[0] == '#': sfx = sfx[1:]
    if sfx.isnumeric(): splt = splt[:-1]
    return s.join(splt).rstrip(' _-#') + ext


class DicomToXmlDicom(object):
    """
    Description
    ~~~~~~~~~~~

    Dicom file to XmlDicom file conversion. XmlDicom file stores DICOM fields in a key/value XML file.

    Inheritance
    ~~~~~~~~~~~

    object -> DicomToXmlDicom

    Creation: 08/09/2022
    Last Revision: 27/03/2025
    """
    __slots__ = ['_uid', '_filenames', '_xmldirectory', '_xmlfilename']

    _FILEEXT = '.xdcm'

    # Class methods

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get XmlDicom file extension.

        Returns
        -------
        str
            '.xdcm'
        """
        return cls._FILEEXT

    @classmethod
    def getDefaultXmlDicomFilename(cls, ds: Dataset) -> str:
        """
        Get default XmlDicom file name from DICOM fields.

        Parameters
        ----------
        ds : pydicom.Dataset
            DICOM fields

        Returns
        -------
        str
            '{lastname}_{firstname}_{birth_date}_{modality}_{acquisition_date}_{series_description}.xdcm'
        """
        last, first = '', ''
        if 'PatientName' in ds:
            if ds['PatientName'].VM > 0:
                name = str(ds['PatientName'].value)
                if '^' in name: last, first = name.split('^')
                elif ' ' in name: last, first = name.split(' ')
                else: last, first = name, ''
        dtbirth = ''
        if 'PatientBirthDate' in ds:
            if ds['PatientBirthDate'].VM > 0:
                dt = str(ds['PatientBirthDate'].value)
                dtbirth = '{}-{}-{}'.format(dt[:4], dt[4:6], dt[6:])
        modality = str(ds['Modality'].value)
        dtscan = ''
        if 'AcquisitionDate' in ds:
            dt = str(ds['AcquisitionDate'].value)
            dtscan = '{}-{}-{}'.format(dt[:4], dt[4:6], dt[6:])
        if 'SeriesDescription' in ds: seq = ds['SeriesDescription'].value
        else: seq = ''
        return '_'.join([last, first, dtbirth, modality, dtscan, seq]) + cls.getFileExt()

    # Special methods

    """
    Private attributes

    _uid            str, series uid
    _filenames      list, list of dicom series filenames
    _xmldirectory   str, xml dicom filepath
    _xmlfilename    str, xml dicom filename
    """

    def __init__(self) -> None:
        """
        DicomToXmlDicom instance constructor.
        """
        super().__init__()

        self._uid = None
        self._filenames = list()
        self._xmldirectory = ''
        self._xmlfilename = ''

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            DicomToXmlDicom instance representation
        """
        return 'DicomToXmlDicom instance at <{}>\n'.format(str(id(self)))

    # Public methods

    def setDicomSeriesFilenames(self, filenames: list[str]) -> None:
        """
        Set the list of DICOM file names to convert in XmlDicom format.

        Parameters
        ----------
        filenames : list[str]
            list of DICOM file names
        """
        if isinstance(filenames, str):
            filenames = [filenames]
        if isinstance(filenames, list):
            self._filenames.clear()
            self._uid = None
            self.addDicomSeriesFilenames(filenames)

    def addDicomSeriesFilenames(self, filenames: list[str]) -> None:
        """
        Add a list of DICOM file names to the list of conversion.

        Parameters
        ----------
        filenames : list[str]
            list of DICOM file names
        """
        if isinstance(filenames, list):
            for filename in filenames:
                if exists(filename):
                    if is_dicom(filename):
                        # < Revision 07/03/2025
                        # ds = read_file(filename, stop_before_pixels=True)
                        ds = dcmread(filename, stop_before_pixels=True)
                        # Revision 07/03/2025 >
                        if not self._uid: self._uid = ds['SeriesInstanceUID'].value
                        if ds['SeriesInstanceUID'].value == self._uid:
                            self._filenames.append(abspath(filename))
                        else: raise ValueError('{} series UID is different from the main.')
                    else: raise IOError('{} is not a valid Dicom file.'.format(basename(filename)))
                else: raise FileNotFoundError('No such file {}.'.format(filename))
        else: raise TypeError('parameter type {} is not list.'.format(filenames))

    def getDicomSeriesFilenames(self) -> list[str]:
        """
        Get the list of DICOM file names to convert.

        Returns
        -------
        list[str]
            list of DICOM file names
        """
        return self._filenames

    def clearDicomSeriesFilenames(self) -> None:
        """
        Clear the list of DICOM file names to convert.
        """
        self._filenames.clear()
        self._uid = None

    def hasDicomSeriesFilenames(self) -> bool:
        """
        Check that the list of DICOM file names is not empty.

        Returns
        -------
        bool
            True if list is not empty
        """
        return len(self._filenames) > 0

    def setBackupXmlDicomDirectory(self, path: str) -> None:
        """
        Set the path of the XmlDicom backup folder.

        Parameters
        ----------
        path : str
            path of the backup folder
        """
        if isinstance(path, str):
            if exists(path):
                if isdir(path):
                    self._xmldirectory = path
                else: raise NotADirectoryError('{} is not a directory.'.format(path))
            else: raise FileNotFoundError('No such directory {}.'.format(path))
        else: raise TypeError('parameter type {} is not str.'.format(type(path)))

    def getBackupXmlDicomDirectory(self) -> str:
        """
        Get path of the XmlDicom backup folder.

        Returns
        -------
        str
            path of the backup folder
        """
        return self._xmldirectory

    def isDefaultBackupXmlDicomDirectory(self) -> bool:
        """
        Checks whether path of the backup folder is defined. In this case, backup folder is the path of the Dicom files.

        Returns
        -------
        bool
            True if backup folder path is not defined
        """
        return self._xmldirectory == ''

    def setXmlDicomFilename(self, filename: str) -> None:
        """
        Set name of converted XmlDicom file.

        Parameters
        ----------
        filename : str
            XmlDicom file name
        """
        if isinstance(filename, str):
            base, ext = splitext(filename)
            if ext != self.getFileExt(): ext = self.getFileExt()
            filename = base + ext
            self._xmlfilename = filename

    def getXmlDicomFilename(self) -> str:
        """
        Get name of converted XmlDicom file.

        Returns
        -------
        str
            XmlDicom file name
        """
        return self._xmlfilename

    def execute(self) -> None:
        """
        Run Dicom to XmlDicom conversion.
        """
        if self.hasDicomSeriesFilenames():
            doc = minidom.Document()
            root = doc.createElement(self.getFileExt()[1:])
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            ds0 = dcmread(self._filenames[0], stop_before_pixels=True)
            if QApplication.instance() is not None: QApplication.processEvents()
            ds0.remove_private_tags()
            multi = list()
            if len(self._filenames) == 1:
                for de in ds0:
                    if de.VR != 'SQ':
                        node = doc.createElement(de.keyword)
                        vr = doc.createAttribute('VR')
                        vr.value = de.VR
                        vm = doc.createAttribute('VM')
                        vm.value = str(de.VM)
                        node.setAttributeNode(vr)
                        node.setAttributeNode(vm)
                        root.appendChild(node)
                        if de.VM == 0:
                            # < Revision 27/03/2025
                            # set a default value if no value in dicom dataset (VM = 0)
                            if vr in ['FL', 'FD', 'DS']:  txt = doc.createTextNode('0.0')
                            elif vr in ['SL', 'SS', 'UL', 'US', 'IS']: txt = doc.createTextNode('0')
                            elif vr == 'PN': txt = doc.createTextNode('None^None')
                            else: txt = doc.createTextNode('None')
                            # Revision 27/03/2025 >
                        elif de.VM == 1:
                            # < Revision 27/03/2025
                            # set a default value if no value in dicom dataset
                            if de.value == '':
                                if vr == 'PN': txt = doc.createTextNode('None^None')
                                else: txt = doc.createTextNode('None')
                            else: txt = doc.createTextNode(str(de.value))
                            # Revision 27/03/2025 >
                        else:
                            # < Revision 27/03/2025
                            # set a default values if no value (or invalid count) in dicom dataset
                            n = len(de.value)
                            if n < de.VM:
                                if vr in ['FL', 'FD', 'DS']:
                                    buff = '|'.join(['0.0'] * de.VM)
                                    if n > 0: buff[:n] = de.value
                                    txt = doc.createTextNode(buff)
                                elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                                    buff = '|'.join(['0'] * de.VM)
                                    if n > 0: buff[:n] = de.value
                                    txt = doc.createTextNode(buff)
                                else:
                                    buff = '|'.join(['None'] * de.VM)
                                    if n > 0: buff[:n] = de.value
                                    txt = doc.createTextNode(buff)
                            else: txt = doc.createTextNode('|'.join([str(v) for v in de.value]))
                            # Revision 27/03/2025 >
                        node.appendChild(txt)
            elif len(self._filenames) > 1:
                ds1 = dcmread(self._filenames[1], stop_before_pixels=True)
                if QApplication.instance() is not None: QApplication.processEvents()
                ds1.remove_private_tags()
                for de in ds0:
                    if de.VR != 'SQ':
                        if de.value != ds1[de.keyword].value:
                            multi.append(de)
                            node = doc.createElement('Node{}'.format(de.keyword))
                            for dec in (ds0[de.keyword], ds1[de.keyword]):
                                child = doc.createElement(de.keyword)
                                vr = doc.createAttribute('VR')
                                vr.value = de.VR
                                vm = doc.createAttribute('VM')
                                vm.value = str(de.VM)
                                child.setAttributeNode(vr)
                                child.setAttributeNode(vm)
                                node.appendChild(child)
                                """
                                if de.VM == 0: txt = doc.createTextNode('')
                                elif de.VM == 1: txt = doc.createTextNode(str(dec.value))
                                else: txt = doc.createTextNode('|'.join([str(v) for v in dec.value]))
                                """
                                if de.VM == 0:
                                    # < Revision 27/03/2025
                                    # set a default value if no value in dicom dataset (VM = 0)
                                    if vr in ['FL', 'FD', 'DS']: txt = doc.createTextNode('0.0')
                                    elif vr in ['SL', 'SS', 'UL', 'US', 'IS']: txt = doc.createTextNode('0')
                                    elif vr == 'PN': txt = doc.createTextNode('None^None')
                                    else: txt = doc.createTextNode('None')
                                    # Revision 27/03/2025 >
                                elif de.VM == 1:
                                    # < Revision 27/03/2025
                                    # set a default value if no value in dicom dataset
                                    if de.value == '':
                                        if vr == 'PN': txt = doc.createTextNode('None^None')
                                        else: txt = doc.createTextNode('None')
                                    else: txt = doc.createTextNode(str(dec.value))
                                    # Revision 27/03/2025 >
                                else:
                                    # < Revision 27/03/2025
                                    # set a default values if no value (or invalid count) in dicom dataset
                                    n = len(dec.value)
                                    if n < de.VM:
                                        if vr in ['FL', 'FD', 'DS']:
                                            buff = '|'.join(['0.0'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                        elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                                            buff = '|'.join(['0'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                        else:
                                            buff = '|'.join(['None'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                    else:
                                        txt = doc.createTextNode('|'.join([str(v) for v in dec.value]))
                                    # Revision 27/03/2025 >
                                child.appendChild(txt)
                            root.appendChild(node)
                        else:
                            node = doc.createElement(de.keyword)
                            vr = doc.createAttribute('VR')
                            vr.value = de.VR
                            vm = doc.createAttribute('VM')
                            vm.value = str(de.VM)
                            node.setAttributeNode(vr)
                            node.setAttributeNode(vm)
                            root.appendChild(node)
                            """
                            if de.VM == 0: txt = doc.createTextNode('')
                            elif de.VM == 1: txt = doc.createTextNode(str(de.value))
                            else: txt = doc.createTextNode('|'.join([str(v) for v in de.value]))
                            """
                            if de.VM == 0:
                                # < Revision 27/03/2025
                                # set a default value if no value in dicom dataset (VM = 0)
                                if vr in ['FL', 'FD', 'DS']: txt = doc.createTextNode('0.0')
                                elif vr in ['SL', 'SS', 'UL', 'US', 'IS']: txt = doc.createTextNode('0')
                                elif vr == 'PN': txt = doc.createTextNode('None^None')
                                else: txt = doc.createTextNode('None')
                                # Revision 27/03/2025 >
                            elif de.VM == 1:
                                # < Revision 27/03/2025
                                # set a default value if no value in dicom dataset
                                if de.value == '':
                                    if vr == 'PN': txt = doc.createTextNode('None^None')
                                    else: txt = doc.createTextNode('None')
                                else: txt = doc.createTextNode(str(de.value))
                                # Revision 27/03/2025 >
                            else:
                                # < Revision 27/03/2025
                                # set a default values if no value (or invalid count) in dicom dataset
                                n = len(de.value)
                                if n < de.VM:
                                    if vr in ['FL', 'FD', 'DS']:
                                        buff = '|'.join(['0.0'] * de.VM)
                                        if n > 0: buff[:n] = de.value
                                        txt = doc.createTextNode(buff)
                                    elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                                        buff = '|'.join(['0'] * de.VM)
                                        if n > 0: buff[:n] = de.value
                                        txt = doc.createTextNode(buff)
                                    else:
                                        buff = '|'.join(['None'] * de.VM)
                                        if n > 0: buff[:n] = de.value
                                        txt = doc.createTextNode(buff)
                                else:
                                    txt = doc.createTextNode('|'.join([str(v) for v in de.value]))
                                # Revision 27/03/2025 >
                            node.appendChild(txt)
            if len(self._filenames) > 2:
                if len(multi) > 0:
                    for filename in self._filenames[2:]:
                        ds = dcmread(filename, stop_before_pixels=True)
                        if QApplication.instance() is not None: QApplication.processEvents()
                        for de in multi:
                            node = doc.getElementsByTagName('Node{}'.format(de.keyword))
                            if node:
                                dec = ds[de.keyword]
                                child = doc.createElement(de.keyword)
                                vr = doc.createAttribute('VR')
                                vr.value = de.VR
                                vm = doc.createAttribute('VM')
                                vm.value = str(de.VM)
                                child.setAttributeNode(vr)
                                child.setAttributeNode(vm)
                                node[0].appendChild(child)
                                """
                                if de.VM == 0: txt = doc.createTextNode('')
                                elif de.VM == 1: txt = doc.createTextNode(str(dec.value))
                                else: txt = doc.createTextNode('|'.join([str(v) for v in dec.value]))
                                """
                                if de.VM == 0:
                                    # < Revision 27/03/2025
                                    # set a default value if no value in dicom dataset (VM = 0)
                                    if vr in ['FL', 'FD', 'DS']: txt = doc.createTextNode('0.0')
                                    elif vr in ['SL', 'SS', 'UL', 'US', 'IS']: txt = doc.createTextNode('0')
                                    elif vr == 'PN': txt = doc.createTextNode('None^None')
                                    else: txt = doc.createTextNode('None')
                                    # Revision 27/03/2025 >
                                elif de.VM == 1:
                                    # < Revision 27/03/2025
                                    # set a default value if no value in dicom dataset
                                    if de.value == '':
                                        if vr == 'PN': txt = doc.createTextNode('None^None')
                                        else: txt = doc.createTextNode('None')
                                    else: txt = doc.createTextNode(str(dec.value))
                                    # Revision 27/03/2025 >
                                else:
                                    # < Revision 27/03/2025
                                    # set a default values if no value (or invalid count) in dicom dataset
                                    n = len(dec.value)
                                    if n < de.VM:
                                        if vr in ['FL', 'FD', 'DS']:
                                            buff = '|'.join(['0.0'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                        elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                                            buff = '|'.join(['0'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                        else:
                                            buff = '|'.join(['None'] * de.VM)
                                            if n > 0: buff[:n] = dec.value
                                            txt = doc.createTextNode(buff)
                                    else:
                                        txt = doc.createTextNode('|'.join([str(v) for v in dec.value]))
                                    # Revision 27/03/2025 >
                                child.appendChild(txt)
            #  write xdcm
            if self._xmlfilename == '': self._xmlfilename = self.getDefaultXmlDicomFilename(ds0)
            if self._xmldirectory == '': self._xmldirectory = dirname(self._filenames[0])
            savename = join(self.getBackupXmlDicomDirectory(), self._xmlfilename)
            xml = doc.toprettyxml()
            with open(savename, 'w') as f:
                f.write(xml)
            self.clear()
        else: raise ValueError('No Dicom filename loaded in DicomToXmlDicom instance.')

    def clear(self) -> None:
        """
        Reset all DicomToXmlDicom attributes.
        """
        self._uid = None
        self._filenames = list()
        self._xmldirectory = getcwd()
        self._xmlfilename = ''


class XmlDicom(object):
    """
    Description
    ~~~~~~~~~~~

    Class to get field values from XmlDicom file. XmlDicom file stores DICOM fields in a key/value XML file.

    Scope of methods:

    - container-like methods for accessing DICOM fields
    - IO methods (Xml, Text, Matfile, CSV, Excel, Latex)

    Inheritance
    ~~~~~~~~~~~

    object -> XmlDicom

    Creation: 08/09/2022
    Last revisions: 11/12/2023
    """
    __slots__ = ['_doc']

    _FILEEXT = '.xdcm'

    # Class method

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get XmlDicom file extension.

        Returns
        -------
        str
            '.xdcm'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get XmlDicom filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe XmlDicom (.xdcm)'
        """
        return 'PySisyphe XmlDicom (*{})'.format(cls._FILEEXT)

    # Special methods

    """
    Private attributes

    _doc    minidom.Document
    """

    def __init__(self) -> None:
        """
        XmlDicom instance constructor.
        """
        super().__init__()
        self._doc = None

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.

        Returns
        -------
        str
            XmlDicom instance representation
        """
        return 'XmlDicom instance at <{}>\n'.format(str(id(self)))

    def __str__(self) -> str:
        """
         Special overloaded method called by the built-in str() python function.

        Returns
        -------
        str
            conversion of XmlDicom instance to str
        """
        buff = ''
        if self._doc is not None:
            keys = self.getKeywords()
            for k in keys:
                data = self.getDataElement(k)
                if not isinstance(data, list): line = '{}\n'.format(data)
                else:
                    line = ''
                    for d in data:
                        line += '\t{}\n'.format(d)
                buff += line
        return buff

    def __getitem__(self, keyword: str):
        """
        Special overloaded container getter method. Get Dicom field (Data element) value from field name as str key.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        int | float | str | list[int] | list[float]
            Dicom field value
        """
        if isinstance(keyword, str): return self.getDataElementValue(keyword)
        else: raise TypeError('parameter type {} is not str.'.format(type(keyword)))

    def __contains__(self, keyword: str) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator.
        Checks whether a Dicom field is in XmlDicom instance.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        bool
            True if field is in XmlDicom instance
        """
        if isinstance(keyword, str): return self.hasKeyword(keyword)
        else: raise TypeError('parameter type {} is not str.'.format(type(keyword)))

    # Public methods

    def loadXmlDicomFilename(self, filename: str) -> None:
        """
        Load XmlDicom file.

        Parameters
        ----------
        filename : str
            XmlDicom file name
        """
        if isinstance(filename, str):
            filename = splitext(filename)
            filename = filename[0] + DicomToXmlDicom.getFileExt()
            if exists(filename): self._doc = minidom.parse(filename)
            else: raise FileNotFoundError('No such file {}.'.format(filename))
        else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    def getSheet(self, keys: list[str]) -> SisypheSheet:
        """
        Copy a list of Dicom fields to a Sisyphe.core.sisypheSheet.SisypheSheet.

        Parameters
        ----------
        keys : list[str]
            list of Dicom fields

        Returns
        -------
        Sisyphe.core.sisypheSheet.SisypheSheet
        """
        s = list()
        for k in keys:
            if k in self:
                v = array(self.getDataElementValue(k))
                if v.ndim == 1:
                    s.append(SisypheSheet({k: v}))
                else:
                    for i in range(v.shape[1]):
                        kb = k + str(i)
                        s.append(SisypheSheet({kb: v[:, i]}))
        return SisypheSheet(concat(s, axis=1))

    def getNumerOfDatasets(self) -> int:
        """
        Get the number of Dicom instances in the current XmlDicom instance.

        Returns
        -------
        int
            Dicom instance count
        """
        k = self.getKeywordsWithValueVariation()
        if len(k) > 0: return len(self.getDataElementValue(k[0]))
        else: return 1

    def getDataset(self, index: int = 0) -> Dataset:
        """
        Copy all Dicom Fields in a pydicom.Dataset.

        Parameters
        ----------
        index : int
            Dicom instance index to copy (default 0)

        Returns
        -------
        pydicom.Dataset
        """
        ds = Dataset()
        if not self.isEmpty():
            keys = self.getKeywords()
            for k in keys:
                de = self.getDataElement(k)
                if isinstance(k, list): ds.add(de[index])
                else: ds.add(de)
        return ds

    def getDataElementValue(self, keyword: str) -> int | float | str | list[int] | list[float] | None:
        """
        Get Dicom field (Data element) value from field name as str key.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        int | float | str | list[int] | list[float]
            Dicom field value
        """
        if self.isEmpty(): return None
        nodes = self._doc.getElementsByTagName(keyword)
        r = None
        if nodes:
            r = list()
            for node in nodes:
                vr = node.getAttribute('VR')
                vm = int(node.getAttribute('VM'))
                child = node.firstChild
                if child and vm > 0:
                    data = child.data
                    if vr in ['FL', 'FD', 'DS']:
                        if vm == 1:  data = float(data)
                        else:
                            data = data.split('|')
                            data = [float(d) for d in data]
                    elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                        if vm == 1: data = int(data)
                        else:
                            data = data.split('|')
                            data = [int(d) for d in data]
                    else:
                        if vm > 1: data = data.split('|')
                else:
                    if vr in ['FL', 'FD', 'DS']:
                        if vm < 2: data = 0.0
                        else: data = [0.0] * vm
                    elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                        if vm < 2: data = 0
                        else: data = [0] * vm
                    elif vr in ['DA', 'TM']: data = ''
                    else:
                        if vm < 2: data = ''
                        else: data = [''] * vm
                r.append(data)
            if len(r) == 1: r = r[0]
        return r

    def getDataElementVR(self, keyword: str) -> str | None:
        """
        Get Dicom field VR attribute (Value representation i.e. Dicom datatype code) from field name as str key. Dicom
        datatype is a two-chars str code.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        str
            VR Dicom datatype code
        """
        if self.isEmpty(): return None
        node = self._doc.getElementsByTagName(keyword)
        if node: return node[0].getAttribute('VR')
        else: return None

    def getDataElementVM(self, keyword: str) -> int | None:
        """
        Get Dicom field VM attribute (Value multiplicity) from field name as str key. Some dicom fields have multiple
        values (vector), VM gives value count of the field.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        str
            VM value count of the DICOM field
        """
        if self.isEmpty(): return None
        node = self._doc.getElementsByTagName(keyword)
        if node: return node[0].getAttribute('VM')
        else: return None

    def getDataElement(self, keyword: str) -> DataElement | list[DataElement] | None:
        """
        Copy a Dicom field in a pydicom.DataElement. Returns a list of pydicom.DataElement if Dicom field value is not
        constant in all Dicom instances of a series. In this case, there is a pydicom.Element for each Dicom instance.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        pydicom.Element | list[pydicom.Element]
        """
        r = None
        if not self.isEmpty():
            nodes = self._doc.getElementsByTagName(keyword)
            if nodes:
                r = list()
                for node in nodes:
                    vr = node.getAttribute('VR')
                    vm = int(node.getAttribute('VM'))
                    child = node.firstChild
                    v = list()
                    if child and vm > 0:
                        data = child.data
                        if vr in ['FL', 'FD', 'DS']:
                            if vm == 1:
                                data = float(data)
                            else:
                                # < Revision 26/03/2025
                                # data = data.split(' ')
                                data = data.split('|')
                                # Revision 26/03/2025 >
                                data = [float(d) for d in data]
                        elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                            if vm == 1:
                                data = int(data)
                            else:
                                # < Revision 26/03/2025
                                # data = data.split(' ')
                                data = data.split('|')
                                # Revision 26/03/2025 >
                                data = [int(d) for d in data]
                        else:
                            # < Revision 26/03/2025
                            # if vm > 1: data = data.split(' ')
                            if vm > 1: data = data.split('|')
                            # Revision 26/03/2025 >
                    else:
                        # < Revision 26/03/2025
                        # return valid value if xml node is empty
                        if vr in ['FL', 'FD', 'DS']:
                            if vm < 2: data = 0.0
                            else: data = [0.0] * vm
                        elif vr in ['SL', 'SS', 'UL', 'US', 'IS']:
                            if vm < 2: data = 0
                            else: data = [0] * vm
                        elif vr in ['DA', 'TM']: data = ''
                        else:
                            if vm < 2: data = ''
                            else: data = [''] * vm
                        # Revision 26/03/2025 >
                    v.append(data)
                    if len(v) == 1: v = v[0]
                    r.append(DataElement(keyword, vr, v))
                if len(r) == 1: r = r[0]
        return r

    def hasKeyword(self, keyword: str) -> bool:
        """
        Checks whether a Dicom field is in XmlDicom instance.

        Parameters
        ----------
        keyword : str
            Dicom field name

        Returns
        -------
        bool
            True if field is in XmlDicom instance
        """
        return len(self._doc.getElementsByTagName(keyword)) > 0

    def getKeywords(self) -> list[str] | None:
        """
        Get list of all Dicom field names in XmlDicom instance.

        Returns
        -------
        list[str]
            list of Dicom field names
        """
        if self.isEmpty(): return None
        else:
            r = list()
            node = self._doc.documentElement.firstChild
            while node:
                if node.nodeType == minidom.Node.ELEMENT_NODE:
                    if node.nodeName[:4] == 'Node': r.append(node.nodeName[4:])
                    else: r.append(node.nodeName)
                node = node.nextSibling
            return r

    def getKeywordsWithConstantValue(self) -> list[str] | None:
        """
        Get list of Dicom fields with constant value (same value in all Dicom instances).

        Returns
        -------
        list[str]
            list of Dicom field names
        """
        if self.isEmpty(): return None
        else:
            r = list()
            node = self._doc.documentElement.firstChild
            while node:
                if node.nodeType == minidom.Node.ELEMENT_NODE:
                    if node.nodeName[:4] != 'Node': r.append(node.nodeName)
                node = node.nextSibling
            return r

    def getKeywordsWithValueVariation(self) -> list[str] | None:
        """
        Get list of Dicom fields having a value variation with Dicom instances (one value for each Dicom instance).

        Returns
        -------
        list[str]
            list of Dicom field names
        """
        if self.isEmpty(): return None
        else:
            r = list()
            node = self._doc.documentElement.firstChild
            while node:
                if node.nodeType == minidom.Node.ELEMENT_NODE:
                    if node.nodeName[:4] == 'Node': r.append(node.nodeName[4:])
                node = node.nextSibling
            return r

    def findKeywords(self, flt: str) -> list[str] | None:
        """
        Search for Dicom fields from a string or substring.

        Parameters
        ----------
        flt : str
            string to search Dicom fields names

        Returns
        -------
        list[str]
            list of Dicom field names
        """
        if self.isEmpty(): return None
        if isinstance(flt, str):
            keywords = self.getKeywords()
            r = list()
            for key in keywords:
                if key.find(flt) > -1:
                    r.append(key)
            if len(r) == 0: return None
            else: return r
        else: raise TypeError('parameter type {} ids not str'.format(type(flt)))

    def isEmpty(self) -> bool:
        """
        Checks if XmlInstance is empty (no Dicom field).

        Returns
        -------
        bool
            True if XmlInstance is empty
        """
        return self._doc is None

    def clear(self) -> None:
        """
        Delete all Dicom fields.
        """
        self._doc = None

    def saveDataElementValuesToXml(self, keys: list[str], filename: str) -> None:
        """
        Save a list of Dicom fields in an XML file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str
            XML file name
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + SisypheSheet.getFileExt()
            sheet = self.getSheet(keys)
            sheet.save(filename)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def saveDataElementValuesToTxt(self, keys: list[str], filename: str, sep: str = '\t') -> None:
        """
        Save a list of Dicom fields in a text file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str
            text file name
        sep : str
            separator char between Dicom fields (default '\t')
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + '.txt'
            sheet = self.getSheet(keys)
            sheet.saveTXT(filename, sep)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def saveDataElementValuesToCSV(self, keys: list[str], filename: str) -> None:
        """
        Save a list of Dicom fields in a CSV file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str
            CSV file name
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + '.csv'
            sheet = self.getSheet(keys)
            sheet.saveCSV(filename)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def saveDataElementValuesToMatfile(self, keys: list[str], filename: str) -> None:
        """
        Save a list of Dicom fields in a Matlab file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str
            Matlab file name
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + '.mat'
            sheet = self.getSheet(keys)
            sheet.saveMATFILE(filename)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def saveDataElementValuesToExcel(self, keys: list[str], filename: str) -> None:
        """
        Save a list of Dicom fields in an Excel file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str
            Excel file name
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + '.xlsx'
            sheet = self.getSheet(keys)
            sheet.saveXLSX(filename)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def saveDataElementValuesToLATEX(self, keys: list[str], filename: str) -> None:
        """
        Save a list of Dicom fields in a LaTeX file.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to save
        filename : str, LaTeX file name
        """
        if not self.isEmpty():
            root, ext = splitext(filename)
            filename = root + '.tex'
            sheet = self.getSheet(keys)
            sheet.saveLATEX(filename)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')

    def copyDataElementValuesToClipboard(self, keys: list[str], sep: str = '\t') -> None:
        """
        Copy a list of Dicom fields to clipboard.

        Parameters
        ----------
        keys : list[str]
            list of Dicom field names to copy
        sep : str
            separator char between Dicom fields (default '\t')
        """
        if not self.isEmpty():
            sheet = self.getSheet(keys)
            sheet.toClipboard(sep=sep)
        else: raise ValueError('Nothing to save, XmlDicom instance is empty.')


class DicomUIDGenerator(object):
    """
    Description
    ~~~~~~~~~~~

    Class to generate Dicom UID (study UID, series UID, instance UID, FrameOfReference UID) and Date/Time for various
    Dicom fields. This UID generator is used by DICOM import/export classes. UID is a Dicom ID code compliant with
    ISO-8824 standard.

    Inheritance
    ~~~~~~~~~~~

    object -> DicomUIDGenerator

    Creation: 08/09/2022
    Last revision: 11/12/2023
    """
    __slots__ = ['_instanceindex', '_seriesindex', '_currentstudy',
                 '_currentseries', '_currentinstance', '_currentframe',
                 '_currentdate', '_currentstudytime',
                 '_currentseriestime', '_currentinstancetime']

    _IMPLEMENTATIONCLASSUID = '1.2.826.0.1.3680043.1.2.100.6.40.0.76'
    _IMPLEMENTATIONVERSIONNAME = 'PySisyphe'
    _OTCLASSUID = '1.2.840.10008.5.1.4.1.1.7'  # Secondary capture Image Storage
    _MRCLASSUID = '1.2.840.10008.5.1.4.1.1.4'
    _CTCLASSUID = '1.2.840.10008.5.1.4.1.1.2'
    _NMCLASSUID = '1.2.840.10008.5.1.4.1.1.20'
    _PTCLASSUID = '1.2.840.10008.5.1.4.1.1.128'
    _RTIMAGESOPCLASSUID = '1.2.840.10008.5.1.4.1.1.481.1'
    _RTDOSESOPCLASSUID = '1.2.840.10008.5.1.4.1.1.481.2'
    _RTSTRUCTCLASSUID = '1.2.840.10008.5.1.4.1.1.481.3'
    _ROOTUID = '1.2.840.12052'

    # Class methods

    @classmethod
    def getImplementationClassUID(cls) -> str:
        """
        Get implementation class UID (i.e. ID of the application/service class user)
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.826.0.1.3680043.1.2.100.6.40.0.76'
        """
        return cls._IMPLEMENTATIONCLASSUID

    @classmethod
    def getImplementationVersionName(cls) -> str:
        """
        Get implementation version name (i.e. name of the application/service class user)

        Returns
        -------
        str
            'PySisyphe'
        """
        return cls._IMPLEMENTATIONVERSIONNAME

    @classmethod
    def getSOPClassUIDFromModality(cls, modality: str) -> str:
        """
        Get modality UID.
        UID = Dicom ID, ISO8824 format.

        Parameters
        ----------
        modality : str
            Dicom modality ('CT', 'MR', 'NM', 'PT', 'OT', 'RTDOSE', 'RTSTRUCT')

        Returns
        -------
        str
            modality UID
        """
        if isinstance(modality, str):
            from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
            if modality in SisypheAcquisition.getModalityToCodeDict():
                if modality == 'OT': return cls._OTCLASSUID
                elif modality == 'MR': return cls._MRCLASSUID
                elif modality == 'CT': return cls._CTCLASSUID
                elif modality == 'PT': return cls._PTCLASSUID
                elif modality == 'RTDOSE': return cls._RTDOSESOPCLASSUID
                elif modality == 'RTSTRUCT': return cls._RTSTRUCTCLASSUID
                else: return cls._NMCLASSUID
            else: raise ValueError('parameter value {} is not a valid modality.'.format(modality))
        else: raise TypeError('parameter type {} is not str.'.format(type(modality)))

    @classmethod
    def getOTSOPClassUID(cls) -> str:
        """
        Get UID of the OT modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.7'
        """
        return cls._OTCLASSUID

    @classmethod
    def getMRSOPClassUID(cls) -> str:
        """
        Get UID of the MR modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.4'
        """
        return cls._MRCLASSUID

    @classmethod
    def getCTSOPClassUID(cls) -> str:
        """
        Get UID of the CT modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.2'
        """
        return cls._CTCLASSUID

    @classmethod
    def getPTSOPClassUID(cls) -> str:
        """
        Get UID of the PT modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.128'
        """
        return cls._PTCLASSUID

    @classmethod
    def getNMSOPClassUID(cls) -> str:
        """
        Get UID of the NM modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.20'
        """
        return cls._NMCLASSUID

    @classmethod
    def getRTImageSOPClassUID(cls) -> str:
        """
        Get UID of the RTIMAGE modality.
        UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.481.1'
        """
        return cls._RTIMAGESOPCLASSUID

    @classmethod
    def getRTDoseSOPClassUID(cls) -> str:
        """
         Get UID of the RTDOSE modality.
         UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.481.2'
        """
        return cls._RTDOSESOPCLASSUID

    @classmethod
    def getRTStructSOPClassUID(cls) -> str:
        """
         Get UID of the RTSTRUCT modality.
         UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            '1.2.840.10008.5.1.4.1.1.481.3'
         """
        return cls._RTSTRUCTCLASSUID

    @classmethod
    def getRootUID(cls) -> str:
        """
         Get root UID, str Prefix used to generate various UID codes.
         UID = Dicom ID, ISO8824 format.

        Returns
        -------
        str
            UID prefix '1.2.840.12052'
         """
        return cls._ROOTUID

    # Special method

    """
    Private attributes

    _instanceindex          int, instance index
    _seriesindex            int, series index
    _currentstudy           str, StudyUID
    _currentseries          str, SeriesUID
    _currentinstance        str, InstanceUID
    _currentframe           str, FrameOfReferenceUID
    _currentdate            str, Study/Series/Instances Date
    _currentstudytime       str, Study time
    _currentseriestime      str, Series time
    _currentinstancetime    str, Instance time
    """

    def __init__(self) -> None:
        """
        DicomUIDGenerator instance constructor.
        """
        super().__init__()

        self._instanceindex = 0
        self._seriesindex = 0
        self._currentstudy = ''
        self._currentseries = ''
        self._currentinstance = ''
        self._currentframe = ''
        self._currentdate = ''
        self._currentstudytime = ''
        self._currentseriestime = ''
        self._currentinstancetime = ''

    # Public methods

    def newStudy(self) -> None:
        """
        Generates current StudyUID.
        """
        self._instanceindex = 0
        self._seriesindex = 0
        self._currentseries = ''
        self._currentinstance = ''
        self._currentframe = ''
        # Root.1.DateTime
        dt = datetime.now()
        self._currentdate = dt.strftime('%Y%m%d')
        self._currentstudytime = dt.strftime('%H%M%S.%f')
        self._currentseriestime = dt.strftime('%H%M%S.%f')
        self._currentinstancetime = dt.strftime('%H%M%S.%f')
        self._currentstudy = '{}.1.{}'.format(self.getRootUID(), dt.strftime('%Y%m%d%H%M%S%f'))

    def newSeries(self) -> None:
        """
        Generates current SeriesUID and FrameOfReferenceUID, increments series index.
        """
        self._instanceindex = 0
        self._seriesindex += 1
        dt = datetime.now()
        self._currentseriestime = dt.strftime('%H%M%S.%f')
        # SeriesUID = Root.2.SeriesIndex.DateTime
        self._currentseries = '{}.2.{}.{}'.format(self.getRootUID(), self._seriesindex, dt.strftime('%Y%m%d%H%M%S%f'))
        # FrameOfReferenceUID = Root.4.SeriesIndex.DateTime
        dt = datetime.now()
        self._currentframe = '{}.4.{}.{}'.format(self.getRootUID(), self._seriesindex, dt.strftime('%Y%m%d%H%M%S%f'))

    def newInstance(self) -> None:
        """
        Generates current InstanceUID and increments instance index.
        """
        self._instanceindex += 1
        dt = datetime.now()
        self._currentinstancetime = dt.strftime('%H%M%S.%f')
        # InstanceUID = Root.3.SeriesIndex.InstanceIndex.DateTime
        self._currentinstance = '{}.3.{}.{}.{}'.format(self.getRootUID(), self._seriesindex,
                                                       self._instanceindex, dt.strftime('%Y%m%d%H%M%S%f'))

    def getCurrentInstanceIndex(self) -> int:
        """
        Get current instance index.

        Returns
        -------
        int
            instance index
        """
        return self._instanceindex

    def getCurrentSeriesIndex(self) -> int:
        """
        Get current series index.

        Returns
        -------
        int
            series index
        """
        return self._seriesindex

    def getCurrentStudyUID(self) -> str:
        """
        Get current StudyUID.

        Returns
        -------
        str
            Study UID
        """
        return self._currentstudy

    def getCurrentSeriesUID(self) -> str:
        """
        Get current SeriesUID.

        Returns
        -------
        str
            Series UID
        """
        return self._currentseries

    def getCurrentInstanceUID(self) -> str:
        """
        Get current InstanceUID.

        Returns
        -------
        str
            Instance UID
        """
        return self._currentinstance

    def getCurrentFrameOfReferenceUID(self) -> str:
        """
        Get current FrameOfReferenceUID.

        Returns
        -------
        str
            FrameOfReference UID
        """
        return self._currentframe

    def getCurrentStudyID(self) -> str:
        """
        Get current StudyID.

        Returns
        -------
        str
            Study ID
        """
        # < Revision 26/03/2025
        # bug fix, SH lenght 16 instead 18
        # return 'A{}'.format(self._currentstudy[-18:])
        return 'A{}{}'.format(self._currentdate, self._currentstudytime)[:16]
        # Revision 26/03/2025 >

    def getStudyDate(self) -> str:
        """
        Get study date.

        Returns
        -------
        str
            study date
        """
        return self._currentdate

    def getStudyTime(self) -> str:
        """
        Get study time.

        Returns
        -------
        str
            study time
        """
        return self._currentstudytime

    def getSeriesTime(self) -> str:
        """
        Get series time.

        Returns
        -------
        str
            series time
        """
        return self._currentseriestime

    def getInstanceTime(self) -> str:
        """
        Get instance time.

        Returns
        -------
        str
            instance time
        """
        return self._currentinstancetime


class ExportToDicom(object):
    """
    Description
    ~~~~~~~~~~~

    Class to convert PySisyphe volume (.xvol) to Dicom format.

    Inheritance
    ~~~~~~~~~~~

    object -> ExportToDicom

    Creation: 08/09/2022
    Last revision: 27/03/2025
    """
    __slots__ = ['_volume', '_xmlref', '_dcmdirectory']

    # Class method

    @classmethod
    def getSettingsDirectory(cls) -> str:
        """
        Get PySisyphe user settings path (~/.PySisyphe/settings.xml in user folder).

        Returns
        -------
        str
            PySisyphe user settings path
        """
        import Sisyphe.settings
        return dirname(abspath(Sisyphe.settings.__file__))

    # Special method

    """
    Private attributes

    _volume         SisypheVolume, volume to convert in dicom format
    _xmlref         XmlDicom, XmlDicom reference
    _dcmdirectory   str, backup directory
    """

    def __init__(self) -> None:
        """
        ExportToDicom instance constructor.
        """
        super().__init__()

        self._volume = None
        self._xmlref = None
        self._dcmdirectory = ''

    # Public methods

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set PySisyphe volume (.xvol) to convert.

        Parameters
        ----------
        vol : Sisyphe.core.sisypheVolume.SisypheVolume
            volume (.xvol) to convert
        """
        if isinstance(vol, SisypheVolume):
            self._volume = vol
            if self._volume.hasFilename():
                filename = splitext(self._volume.getFilename())[0] + DicomToXmlDicom.getFileExt()
                if exists(filename):
                    self._xmlref = XmlDicom()
                    self._xmlref.loadXmlDicomFilename(filename)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def getVolume(self) -> SisypheVolume:
        """
        Get PySisyphe volume (.xvol) to convert.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            volume (.xvol) to convert
        """
        return self._volume

    def hasVolume(self) -> bool:
        """
        Checks whether PySisyphe volume to convert is defined.

        Returns
        -------
        bool
            True if PySisyphe volume to convert is defined
        """
        return self._volume is not None

    def setXmlDicomReference(self, filename: str) -> None:
        """
        Set XmlDicom reference (.xdcm). Dicom fields of the XmlDicom reference are used as a template for writing Dicom
        file.

        Parameters
        ----------
        filename : str
            XmlDicom file name
        """
        if isinstance(filename, str):
            filename = splitext(filename)
            filename = filename[0] + DicomToXmlDicom.getFileExt()
            if exists(filename):
                self._xmlref = XmlDicom()
                self._xmlref.loadXmlDicomFilename(filename)
            else: raise FileNotFoundError('No such file {}.'.format(filename))
        else: raise TypeError('parameter type {} is not str.'.format(type(filename)))

    def getXmlDicomReference(self) -> str:
        """
        Get XmlDicom reference (.xdcm). Dicom fields of the XmlDicom reference are used as a template for writing Dicom
        file.

        Returns
        -------
        str
            XmlDicom file name
        """
        return self._xmlref

    def hasXmlDicomReference(self) -> bool:
        """
        Checks whether XmlDicom reference is defined.

        Returns
        -------
        bool
            True if PySisyphe volume to convert is defined
        """
        return self._xmlref is not None

    def setBackupDicomDirectory(self, path: str) -> None:
        """
        Set the path of the backup folder. Dicom files are saved in this directory.

        Parameters
        ----------
        path : str
            path of the backup folder
        """
        if isinstance(path, str):
            if exists(path):
                if isdir(path):
                    self._dcmdirectory = path
                else: raise NotADirectoryError('{} is not a directory.'.format(path))
            else: raise FileNotFoundError('No such directory {}.'.format(path))
        else: raise TypeError('parameter type {} is not str.'.format(type(path)))

    def getBackupDicomDirectory(self) -> str:
        """
        Get the path of the backup folder. Dicom files are saved in this directory.

        Returns
        -------
        str
            path of the backup folder
        """
        return self._dcmdirectory

    def isDefaultBackupDicomDirectory(self) -> bool:
        """
        Checks whether backup folder is defined. The default backup folder is the path of the PySisyphe volume.

        Returns
        -------
        bool
            True if backup folder is not defined
        """
        return self._dcmdirectory == ''

    def clear(self) -> None:
        """
        Reset all ExportToDicom instance attributes.
        """
        del self._xmlref
        self._volume = None
        self._xmlref = None
        self._dcmdirectory = ''

    # noinspection PyUnboundLocalVariable
    def execute(self, progress: DialogWait | None = None) -> None:
        """
        Run PySisyphe volume (.xvol) to Dicom conversion.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasVolume():
            if progress: progress.setInformationText('{} Dicom conversion...'.
                                                     format(basename(self._volume.getFilename)))
            # Datatype conversion to uint16
            if self._volume.getDatatype() != 'uint16':
                vol = self._volume.cast('uint16')
                img = vol.copyToSITKImage()
            else: img = self._volume.copyToSITKImage()
            if QApplication.instance() is not None: QApplication.processEvents()
            # Spatial convention PySisyphe (VTK) to SITK/DICOM
            img = flipImageToVTKDirectionConvention(img)
            if QApplication.instance() is not None: QApplication.processEvents()
            # XmlDicom
            m = self._volume.getAcquisition().getModality()
            # < Revision 26/03/2025
            # if self.hasXmlDicomReference(): m2 = m
            # else: m2 = 'OT'
            if m not in _DICOMMODALITIES: m = 'OT'
            # filename = join(self.getSettingsDirectory(), m2 + DicomToXmlDicom.getFileExt())
            filename = join(self.getSettingsDirectory(), m + DicomToXmlDicom.getFileExt())
            # Revision 26/03/2025 >
            xmlbase = XmlDicom()
            xmlbase.loadXmlDicomFilename(filename)
            # UID generator
            gen = DicomUIDGenerator()
            gen.newStudy()
            gen.newSeries()
            # Convert to numpy
            np = GetArrayViewFromImage(img)
            try:
                for i in range(self._volume.getDepth()):
                    gen.newInstance()
                    if i == 0:
                        # Create dicom dataset
                        filemeta = FileMetaDataset()
                        filemeta.FileMetaInformationVersion = b'\x00\x01'
                        # noinspection PyTypeChecker
                        filemeta.MediaStorageSOPClassUID = gen.getSOPClassUIDFromModality(m)
                        # noinspection PyTypeChecker
                        filemeta.ImplementationClassUID = gen.getImplementationClassUID()
                        filemeta.ImplementationVersionName = gen.getImplementationVersionName()
                        filemeta.TransferSyntaxUID = ExplicitVRLittleEndian
                        ds = FileDataset('temp', {}, file_meta=filemeta, preamble=b'\0' * 128, is_implicit_VR=False)
                        # Copy data elements
                        if self.hasXmlDicomReference():
                            for keyword in xmlbase.getKeywords():
                                if self._xmlref.hasKeyword(keyword):
                                    de = self._xmlref.getDataElement(keyword)
                                    if de: ds.add(de)
                                else:
                                    de = xmlbase.getDataElement(keyword)
                                    if de: ds.add(de)
                        else:
                            for keyword in xmlbase.getKeywords():
                                de = xmlbase.getDataElement(keyword)
                                if de: ds.add(de)
                            ds['Modality'].value = m
                            ds['SOPClassUID'].value = gen.getSOPClassUIDFromModality(m)
                        # Update constant attributes, edited once
                        # < Revision 27/03/2025
                        # ds['ImageType'].value = 'DERIVED SECONDARY AXIAL'
                        ds['ImageType'].value = ['DERIVED', 'SECONDARY', 'AXIAL']
                        # Revision 27/03/2025v
                        ds['SliceThickness'].value = self._volume.getSpacing()[2]
                        ds['SpacingBetweenSlices'].value = self._volume.getSpacing()[2]
                        ds['Columns'].value = self._volume.getSize()[0]
                        ds['Rows'].value = self._volume.getSize()[1]
                        ds['PixelSpacing'].value = list(self._volume.getSpacing()[:2])
                        ds['ImageOrientationPatient'].value = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
                        ds['SeriesInstanceUID'].value = gen.getCurrentSeriesUID()
                        datescan = self._volume.getAcquisition().getDateOfScan().replace('-', '')
                        ds['SeriesDate'].value = datescan
                        ds['SeriesTime'].value = gen.getSeriesTime()
                        ds['AcquisitionDate'].value = datescan
                        ds['ContentDate'].value = datescan
                        ds['InstanceCreationDate'].value = datescan
                        ds['AcquisitionTime'].value = gen.getInstanceTime()
                        ds['ContentTime'].value = gen.getInstanceTime()
                        ds['InstanceCreationTime'].value = gen.getInstanceTime()
                        ds['ImagesInAcquisition'].value = self._volume.getDepth()
                        ds['FrameOfReferenceUID'].value = gen.getCurrentFrameOfReferenceUID()
                        fov = self._volume.getFieldOfView()
                        p = [-fov[0] / 2, -fov[1] / 2, -fov[2] / 2]
                        if self.hasXmlDicomReference():
                            ds['StudyInstanceUID'].value = self._xmlref['StudyInstanceUID']
                            ds['StudyID'].value = self._xmlref['StudyID']
                            ds['AccessionNumber'].value = self._xmlref['AccessionNumber']
                            ds['SeriesNumber'].value = self._xmlref['SeriesNumber'] + 20
                            ds['StudyDate'].value = self._xmlref['StudyDate']
                            ds['StudyTime'].value = self._xmlref['StudyTime']
                        else:
                            ds['StudyInstanceUID'].value = gen.getCurrentStudyUID()
                            ds['StudyID'].value = gen.getCurrentStudyID()
                            ds['AccessionNumber'].value = gen.getCurrentStudyID()
                            ds['SeriesNumber'].value = gen.getCurrentSeriesIndex()
                            ds['StudyDate'].value = gen.getStudyDate()
                            ds['StudyTime'].value = gen.getStudyTime()
                            ds['SeriesDescription'].value = self._volume.getAcquisition().getSequence()
                            # Patient attributes
                            ds['PatientName'].value = '{}^{}'.format(self._volume.getIdentity().getLastname(),
                                                                     self._volume.getIdentity().getFirstname())
                            ds['PatientBirthDate'].value = \
                                self._volume.getIdentity().getDateOfBirthday().replace('-', '')
                            gender = self._volume.getIdentity().getGender(string=False)
                            if gender == 1: ds['PatientSex'].value = 'M'
                            elif gender == 2: ds['PatientSex'].value = 'F'
                            else: ds['PatientSex'].value = 'O'
                            ds['PatientAge'].value = '00{}Y'.format(self._volume.getIdentity().getAge())[-4:]
                    # Update instance dependent attributes, edited for each instance
                    ds['SOPInstanceUID'].value = gen.getCurrentInstanceUID()
                    ds['InstanceNumber'].value = gen.getCurrentInstanceIndex()
                    p[2] = p[2] - (i * self._volume.getSpacing()[2])
                    ds['ImagePositionPatient'].value = p
                    ds['SliceLocation'].value = p[2]
                    minv = int(np[i, :, :].min())
                    maxv = int(np[i, :, :].max())
                    ds['SmallestImagePixelValue'].value = minv
                    ds['LargestImagePixelValue'].value = maxv
                    ds['WindowCenter'].value = (maxv - minv) // 2
                    ds['WindowWidth'].value = maxv - minv
                    ds['RescaleIntercept'].value = self._volume.getIntercept()
                    ds['RescaleSlope'].value = self._volume.getSlope()
                    # Add pixel array
                    ds.PixelData = np[i, :, :].tobytes()
                    # Save dicom file
                    savename = splitext(self._volume.getFilename())[0] + '_' + '0000{}'.format(i)[-4:] + '.dcm'
                    if self._dcmdirectory == '':
                        self._dcmdirectory = dirname(savename)
                        mkdir(self._dcmdirectory)
                    filename = join(self.getBackupDicomDirectory(), basename(savename))
                    # noinspection PyTypeChecker
                    ds.file_meta.MediaStorageSOPInstanceUID = gen.getCurrentInstanceUID()
                    ds.save_as(filename, write_like_original=False)
                    if QApplication.instance() is not None: QApplication.processEvents()
            except: raise IOError('Dicom write error.')
            finally: self.clear()


class ImportFromDicom(object):
    """
    Description
    ~~~~~~~~~~~

    Class to convert Dicom files to PySisyphe volume (.xvol).

    Inheritance
    ~~~~~~~~~~~

    object -> ImportFromDicom

    Creation: 08/09/2022
    Last revision: 07/03/2025
    """

    __slots__ = ['_refuid', '_seriesuid', '_reflist', '_folder', '_refvol', '_savetag']

    # Special method

    """
    Private attributes

    _reflist        list[(str, str, str)], one item for each filename,
                    instance: str, Dicom SOPInstanceUID value (0x0008, 0x0018)
                    filename: str
                    position: str, Dicom ImagePositionPatient (0x0020, 0x0032)
    _refframeuid    str, frame of reference uid of Dicom series to import
    _seriesuid      str, series uid of Dicom series to import
    _folder         str, save folder
    _refvol         SisypheVolume, converted Dicom
    _savetag        bool, True automatic saving
    """

    def __init__(self) -> None:
        """
        ImportFromDicom instance constructor.
        """
        super().__init__()

        self._reflist = list()
        self._refuid = ''
        self._seriesuid = ''
        self._folder = ''
        self._refvol = None
        self._savetag = False

    # Public methods

    def setSaveTag(self, v: bool) -> None:
        """
        Set save tag value. If tag is True, PySisyphe volume is saved during execute method.

        Parameters
        ----------
        v : bool
            save tag value
        """
        if isinstance(v, bool): self._savetag = v
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSaveTag(self) -> bool:
        """
        Get save tag value. If tag is True, PySisyphe volume is saved during execute method.

        Returns
        -------
        bool
            save tag value
        """
        return self._savetag

    def setDicomFilenames(self, filenames: list[str]) -> None:
        """
        Set Dicom file names to convert. All files must belong to the same Dicom series.
        Dicom fields used to detect Dicom series:

        - (0x0008, 0x0018) SOPInstanceUID
        - (0x0020, 0x000e) SeriesInstanceUID
        - (0x0020, 0x0032) ImagePositionPatient
        - (0x0020, 0x0052) FrameOfReferenceUID

        Parameters
        ----------
        filenames : str
            list of Dicom file names
        """
        self._refuid = ''
        self._seriesuid = ''
        self._reflist = list()
        tags = [Tag(0x0008, 0x0018),
                Tag(0x0020, 0x000e),
                Tag(0x0020, 0x0032),
                Tag(0x0020, 0x0052)]
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str):
                    if exists(filename):
                        if is_dicom(filename):
                            # < Revision 07/03/2025
                            # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                            ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                            # Revision 07/03/2025 >
                            if QApplication.instance() is not None: QApplication.processEvents()
                            frameuid = ds['FrameOfReferenceUID'].value
                            seriesuid = ds['SeriesInstanceUID'].value
                            if 'ImagePositionPatient' in ds: pos = ds['ImagePositionPatient'].value
                            else: pos = [0, 0, 0]
                            if self._refuid == '':
                                self._refuid = frameuid
                                self._seriesuid = seriesuid
                            if seriesuid == self._seriesuid and frameuid == self._refuid:
                                # SOPInstanceUID 0 suffix = key, 1 filename, 2 ImagePositionPatient
                                suffix = int(ds['SOPInstanceUID'].value.split('.')[-1])
                                self._reflist.append([suffix, filename, pos])
                            else: raise IOError('{} is not in the current series.'.format(basename(filename)))
                        else: raise IOError('{} is not a valid Dicom file.'.format(basename(filename)))
                    else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
            if len(self._reflist) > 0: self._reflist.sort(key=lambda v: v[2][2])
        else: raise TypeError('parameter type {} is not list.'.format(type(filenames)))

    def getDicomFilenames(self) -> list[str]:
        """
        Get Dicom file names to convert.

        Returns
        -------
        str
            list of Dicom file names
        """
        filenames = list()
        if not self.isEmpty():
            for item in self._reflist:
                filenames.append(item[1])
        return filenames

    def getDicomImagePositionPatient(self) -> list[float]:
        """
        Get PositionPatient Dicom field values from Dicom Files to convert.

        Returns
        -------
        list[float]
            list of PositionPatient Dicom field values
        """
        positions = list()
        if not self.isEmpty():
            for item in self._reflist:
                positions.append(item[2])
        return positions

    def getReferenceUID(self) -> str:
        """
        Get Dicom files reference UID (i.e. FrameOfReferenceUID)

        Returns
        -------
        str
            Dicom files reference UID
        """
        return self._refuid

    def hasReferenceUID(self) -> bool:
        """
        Checks whether Dicom files reference UID is defined.

        Returns
        -------
        bool
            True if Dicom files reference UID is defined
        """
        return self._refuid != ''

    def getSeriesUID(self) -> str:
        """
        Get Dicom files seriesUID.

        Returns
        -------
        str
            Dicom files seriesUID
        """
        return self._seriesuid

    def setImportFolder(self, folder: str) -> None:
        """
        Set path of the backup folder. PySisyphe volume is saved in this directory.

        Parameters
        ----------
        folder : str
            path of the backup folder
        """
        if isinstance(folder, str):
            if exists(folder):
                self._folder = folder
            else: raise FileNotFoundError('No such folder {}.'.format(folder))
        else: raise TypeError('parameter type {} is not str.'.format(type(folder)))

    def getImportFolder(self) -> str:
        """
        Get path of the backup folder. PySisyphe volume is saved in this directory.

        Returns
        -------
        str
            path of the backup folder
        """
        return self._folder

    def hasImportFolder(self) -> bool:
        """
        Checks whether backup folder is defined. The default backup folder is the path of the Dicom files.

        Returns
        -------
        bool
            True if backup folder is defined
        """
        return self._folder != ''

    def getReferenceVolume(self) -> SisypheVolume:
        """
        Get converted PySisyphe volume.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
        """
        if self._refvol: return self._refvol
        else: raise ValueError('No reference volume converted.')

    def hasReferenceVolume(self) -> bool:
        """
        Checks whether converted PySisyphe volume exists (False before calling execute method).

        Returns
        -------
        bool
            True if PySisyphe volume exists
        """
        return self._refvol is not None

    def saveReferenceVolume(self, progress: DialogWait | None = None) -> None:
        """
        Save converted PySisyphe volume.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait | None
            progress bar dialog (optional)
        """
        if self.hasReferenceVolume():
            identity = self._refvol.getIdentity()
            acq = self._refvol.getAcquisition()
            filenames = self.getDicomFilenames()
            # Sisyphe write
            savename = '_'.join([identity.getLastname(),
                                 identity.getFirstname(),
                                 identity.getDateOfBirthday(),
                                 acq.getModality(),
                                 acq.getDateOfScan(),
                                 acq.getSequence()]) + self._refvol.getFileExt()
            if self._folder != '': savename = join(self._folder, savename)
            else: savename = join(dirname(filenames[0]), savename)
            if progress: progress.setInformationText('Save volume {}.'.format(basename(savename)))
            self._refvol.save(savename)
            if QApplication.instance() is not None: QApplication.processEvents()
            # Write XmlDicom
            xml = DicomToXmlDicom()
            xml.setDicomSeriesFilenames(filenames)
            xml.setXmlDicomFilename(savename)
            if self._folder != '': xml.setBackupXmlDicomDirectory(dirname(savename))
            xml.execute()
            if QApplication.instance() is not None: QApplication.processEvents()
        else: raise ValueError('No reference volume converted.')

    def isEmpty(self) -> bool:
        """
        Checks if ImportFromDicom is empty, Dicom files to convert are not defined.

        Returns
        -------
        bool
            True if Dicom files to convert are not defined
        """
        return len(self._reflist) == 0

    def clear(self) -> None:
        """
        Reset all ImportFromDicom instance attributes.
        """
        self._reflist = list()
        self._refuid = ''
        self._seriesuid = ''
        self._folder = ''

    def execute(self, progress: DialogWait | None = None, getdirs: bool = False) -> SisypheVolume | None:
        """
        Run Dicom to PySisyphe volume (.xvol) conversion.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait
            progress bar dialog (optional)
        getdirs : bool
            if True, copy PySisyphe volume origin and direction attributes from Dicom fields, otherwise set PySisyphe
            volume origin and direction attributes to default

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            converted PySisyphe volume
        """
        if not self.isEmpty():
            filenames = self.getDicomFilenames()
            if filenames:
                if progress: progress.setInformationText('Dicom files conversion...')
                img = readFromDicomSeries(filenames)
                img = flipImageToVTKDirectionConvention(img)
                img = convertImageToAxialOrientation(img)[0]
                if getdirs is False:
                    img.SetOrigin((0, 0, 0))
                    img.SetDirection(getRegularDirections())
                # Attributes
                vol = SisypheVolume()
                vol.identity = getIdentityFromDicom(filenames[0])
                vol.acquisition = getAcquisitionFromDicom(filenames[0])
                vol.setSITKImage(img)
                self._refvol = vol
                if self._savetag: self.saveReferenceVolume(progress)
                return self._refvol
            else: raise ValueError('No Dicom file to convert.')
        else: raise ValueError('No Dicom file to convert.')


class ImportFromRTDose(ImportFromDicom):
    """
    Description
    ~~~~~~~~~~~

    Class to convert Dicom RTDose to PySisyphe volume (.xvol).

    Inheritance
    ~~~~~~~~~~~

    object -> ImportFromDicom -> ImportFromRTDose

    Creation: 08/09/2022
    Last revision: 07/03/2025
    """
    __slots__ = ['_rtdosefile', '_rtdosevol']

    # Special method

    """
    Private attributes

    _rtdosefile     list[str], list of RTDose filenames to convert
    _rtdosevol      SisypheVolumeCollection, converted RTDose
    """

    def __init__(self) -> None:
        """
        ImportFromRTDose instance constructor.
        """
        super().__init__()

        self._rtdosefile = list()
        self._rtdosevol = SisypheVolumeCollection()

    # Public methods

    def addRTDoseFilename(self, filenames: str | list[str]) -> None:
        """
        Add Dicom RTDose file names to convert.
        Dicom fields used:

        - (0x0008, 0x0060) Modality
        - (0x0020, 0x0052) FrameOfReferenceUID

        Parameters
        ----------
        filenames : str | list[str]
            list of Dicom RTDose file names
        """
        # Dicom field used
        #   (0x0008, 0x0060) Modality
        #   (0x0020, 0x0052) FrameOfReferenceUID
        if self.hasReferenceUID():
            tags = [Tag(0x0008, 0x0060),
                    Tag(0x0020, 0x0052)]
            if isinstance(filenames, str): filenames = [filenames]
            if isinstance(filenames, list):
                for filename in filenames:
                    if isinstance(filename, str):
                        if exists(filename):
                            if is_dicom(filename):
                                # < Revision 07/03/2025
                                # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                                ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                                # Revision 07/03/2025 >
                                if QApplication.instance() is not None: QApplication.processEvents()
                                if ds['Modality'].value == 'RTDOSE':
                                    if ds['FrameOfReferenceUID'].value == self._refuid:
                                        self._rtdosefile.append(filename)
                                    else: raise IOError('{} has not valid reference UID.'.format(basename(filename)))
                                else: raise IOError('{} modality is not RTDose.'.format(basename(filename)))
                            else: raise IOError('{} is not a valid Dicom file.'.format(basename(filename)))
                        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                    else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
            else: raise TypeError('parameter type {} is not list.'.format(type(filenames)))
        else: raise ValueError('Reference UID is not defined.')

    def getRTDoseFilename(self) -> list[str]:
        """
        Get Dicom RTDose file names to convert.

        Returns
        -------
        list[str]
            list of Dicom RTDose file names
        """
        return self._rtdosefile

    def hasRTDoseFilename(self) -> bool:
        """
        Checks whether Dicom RTDose files to convert are defined.

        Returns
        -------
        bool
            True if Dicom RTDose files to convert are defined
        """
        return len(self._rtdosefile) > 0

    def getRTDoseVolume(self) -> SisypheVolumeCollection:
        """
        Get converted PySisyphe volumes.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolumeCollection
        """
        if self.hasRTDoseVolume(): return self._rtdosevol
        else: raise ValueError('No RTDose volume converted.')

    def hasRTDoseVolume(self) -> bool:
        """
        Checks whether converted PySisyphe volumes exists (False before calling execute method).

        Returns
        -------
        bool
            True if PySisyphe volume exists
        """
        return len(self._rtdosevol) > 0

    def saveRTDoseVolume(self) -> None:
        """
        Save converted PySisyphe volumes.
        """
        if self.hasRTDoseVolume():
            filenames = self.getRTDoseFilename()
            for vol in self._rtdosevol:
                identity = vol.getIdentity()
                acq = vol.getAcquisition()
                # Sisyphe write
                savename = '_'.join([identity.getLastname(),
                                     identity.getFirstname(),
                                     identity.getDateOfBirthday(),
                                     acq.getModality(),
                                     acq.getDateOfScan(),
                                     acq.getSequence()]) + vol.getFileExt()
                if self._folder != '': savename = join(self._folder, savename)
                else: savename = join(dirname(filenames[0]), savename)
                vol.save(savename)
                if QApplication.instance() is not None: QApplication.processEvents()

    def clear(self) -> None:
        """
        Reset all ImportFromRTDose instance attributes.
        """
        super().clear()
        self._rtdosefile = list()
        self._rtdosevol.clear()

    def execute(self, progress: DialogWait | None = None, getdirs: bool = False) -> SisypheVolumeCollection | None:
        """
        Run Dicom RTDose to PySisyphe volume (.xvol) conversion.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait
            progress bar dialog
        getdirs : bool
            if True, copy PySisyphe volume origin and direction attributes from Dicom fields, otherwise set PySisyphe
            volume origin and direction attributes to default

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolumeCollection
            converted PySisyphe volumes
        """
        if self.hasRTDoseFilename():
            super().execute(progress, getdirs=getdirs)
            self._rtdosevol.clear()
            for filename in self._rtdosefile:
                if progress: progress.setInformationText('{} Dicom RTDose conversion...'.format(basename(filename)))
                img = readFromDicomSeries([filename])
                # VTK orientation conversion
                img = flipImageToVTKDirectionConvention(img)
                img = convertImageToAxialOrientation(img)[0]
                img.SetOrigin((0, 0, 0))
                img.SetDirection(getRegularDirections())
                # Resample to reference volume space
                if img.GetDimension() == 4: img = img[:, :, :, 0]
                if self._refvol.getSize() != img.GetSize() or self._refvol.getSpacing() != img.GetSpacing():
                    # Centered identity transform initializer
                    t = Euler3DTransform()
                    t.SetIdentity()
                    r = CenteredTransformInitializerFilter()
                    r.GeometryOn()
                    refimg = Cast(self._refvol.getSITKImage(), img.GetPixelID())
                    r.Execute(img, refimg, t)
                    # Resample
                    r = ResampleImageFilter()
                    r.SetReferenceImage(self._refvol.getSITKImage())
                    r.SetInterpolator(sitkLinear)
                    r.SetTransform(t)
                    img = r.Execute(img)
                # Attributes
                vol = SisypheVolume()
                vol.identity = getIdentityFromDicom(filename)
                vol.acquisition = getAcquisitionFromDicom(filename)
                vol.setSITKImage(img)
                vol.setOrigin()
                self._rtdosevol.append(vol)
                if self._savetag:
                    # Sisyphe write
                    savename = '_'.join([vol.identity.getLastname(),
                                         vol.identity.getFirstname(),
                                         vol.identity.getDateOfBirthday(),
                                         vol.acquisition.getModality(),
                                         vol.acquisition.getDateOfScan(),
                                         vol.acquisition.getSequence()]) + vol.getFileExt()
                    if self._folder != '': savename = join(self._folder, savename)
                    else: savename = join(dirname(filename), savename)
                    if progress: progress.setInformationText('Save {}.'.format(basename(savename)))
                    vol.save(savename)
                    if QApplication.instance() is not None: QApplication.processEvents()
                    # Write XmlDicom
                    xml = DicomToXmlDicom()
                    xml.setDicomSeriesFilenames(filename)
                    xml.setXmlDicomFilename(savename)
                    if self._folder != '': xml.setBackupXmlDicomDirectory(dirname(savename))
                    xml.execute()
                    if QApplication.instance() is not None: QApplication.processEvents()
                return self._rtdosevol
        else: raise ValueError('No RTDose file to convert.')


class ImportFromRTStruct(ImportFromDicom):
    """
    Description
    ~~~~~~~~~~~

    Class to convert Dicom RTSTRUCT to PySisyphe ROI (.xroi).

    Inheritance
    ~~~~~~~~~~~

    object -> ImportFromDicom -> ImportFromRTStruct

    Creation: 08/09/2022
    Last revision: 07/03/2025
    """
    __slots__ = ['_rtstructfile', '_rtroi']

    # Special method

    """
    Private attributes

    _rtstructfile   list[str], list of RTStruct filenames to convert
    _rtroi          SisypheROICollection, converted RTStruct
    """

    def __init__(self) -> None:
        """
        ImportFromRTStruct instance constructor.
        """
        super().__init__()

        self._rtstructfile = list()
        self._rtroi = SisypheROICollection()

    # Public methods

    def addRTStructFilename(self, filenames: str | list[str]) -> None:
        """
        Add Dicom RTStruct file names to convert.
        Dicom fields used:

        - (0x0008, 0x0060) Modality
        - (0x0020, 0x0052) FrameOfReferenceUID

        Parameters
        ----------
        filenames : str
            list of Dicom RTDose file names
        """
        # Dicom field used
        #   (0x0008, 0x0060) Modality
        #   (0x0020, 0x0052) FrameOfReferenceUID
        if self.hasReferenceUID():
            tags = [Tag(0x0008, 0x0060),
                    Tag(0x3006, 0x0010)]
            if isinstance(filenames, str): filenames = [filenames]
            if isinstance(filenames, list):
                for filename in filenames:
                    if isinstance(filename, str):
                        if exists(filename):
                            if is_dicom(filename):
                                # < Revision 07/03/2025
                                # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                                ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                                # Revision 07/03/2025 >
                                if QApplication.instance() is not None: QApplication.processEvents()
                                if ds['Modality'].value == 'RTSTRUCT':
                                    if tags[1] not in ds:
                                        raise IOError('{} has not ReferencedFrameOfReferenceSequence field.'
                                                      .format(basename(filename)))
                                    if [0x0020, 0x0052] not in ds[tags[1]][0]:
                                        raise IOError('{} has not FrameOfReferenceUID field.'
                                                      .format(basename(filename)))
                                    if ds[tags[1]][0][0x0020, 0x0052].value == self._refuid:
                                        self._rtstructfile.append(filename)
                                    else: raise IOError('{} has not valid reference UID.'.format(basename(filename)))
                                else: raise IOError('{} modality is not RTDose.'.format(basename(filename)))
                            else: raise IOError('{} is not a valid Dicom file.'.format(basename(filename)))
                        else: raise FileNotFoundError('No such file {}.'.format(basename(filename)))
                    else: raise TypeError('parameter type {} is not str.'.format(type(filename)))
            else: raise TypeError('parameter type {} is not list.'.format(type(filenames)))
        else: raise ValueError('Reference UID is not defined.')

    def getRTStructFilename(self) -> list[str]:
        """
        Get Dicom RTStruct file names to convert.

        Returns
        -------
        list[str]
            list of Dicom RTStruct file names
        """
        return self._rtstructfile

    def hasRTStructFilename(self) -> bool:
        """
        Checks whether Dicom RTStruct files to convert are defined.

        Returns
        -------
        bool
            True if Dicom RTStruct files to convert are defined
        """
        return len(self._rtstructfile) > 0

    def getRTStructROI(self) -> SisypheROICollection:
        """
        Get converted PySisyphe ROIs.

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROICollection
        """
        if self.hasRTStructROI(): return self._rtroi
        else: raise ValueError('No RTStruct ROI converted.')

    def hasRTStructROI(self) -> bool:
        """
        Checks whether converted PySisyphe rois exists (False before calling execute method).

        Returns
        -------
        bool
            True if PySisyphe rois exists
        """
        return len(self._rtroi) > 0

    def saveRTStructROI(self) -> None:
        """
        Save converted PySisyphe ROIs.
        """
        if self.hasRTStructROI():
            filenames = self.getRTStructFilename()
            for roi in self._rtroi:
                if self._folder != '': folder = self._folder
                else: folder = dirname(filenames[0])
                savename = join(folder, roi.getName()) + SisypheROI.getFileExt()
                roi.saveAs(savename)
                if QApplication.instance() is not None: QApplication.processEvents()
        else: raise ValueError('No ROI to save.')

    def getRTStructLabel(self) -> SisypheVolume:
        """
        Get converted PySisyphe label volume.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
            label volume
        """
        if self.hasReferenceVolume():
            if self.hasRTStructROI():
                v = self._rtroi.toLabelVolume()
                v.setFilename(self._refvol.getFilename())
                v.setFilenameSuffix('_LABELS')
                return v
            else: raise ValueError('No ROI to save.')
        else: raise ValueError('No reference volume.')

    def saveRTStructLabel(self) -> None:
        """
        Save converted PySisyphe label volume.
        """
        v = self.getRTStructLabel()
        v.save()

    def clear(self) -> None:
        """
        Reset all ImportFromRTStruct instance attributes.
        """
        super().clear()
        self._rtstructfile = list()
        self._rtroi.clear()

    def execute(self, progress: DialogWait | None = None, getdirs: bool = False) -> SisypheROICollection:
        """
        Run Dicom RTStruct to PySisyphe roi (.xroi) conversion.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait
            progress bar dialog (optional)
        getdirs : bool
            if True, copy PySisyphe volume origin and direction attributes from Dicom fields,
            otherwise set PySisyphe volume origin and direction attributes to default

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROICollection
            converted PySisyphe rois
        """
        if not self.isEmpty():
            if self.hasRTStructFilename():
                super().execute(progress, getdirs=getdirs)
                self._rtroi.clear()
                iudlist = [v[0] for v in self._reflist]
                npsize = self._refvol.getSize()[::-1]
                img = zeros(npsize, dtype='uint8')
                tags = [Tag(0x3006, 0x0020),
                        Tag(0x3006, 0x0039)]
                for filename in self._rtstructfile:
                    if progress: progress.setInformationText('{} Dicom RTStruct conversion...'.format(basename(filename)))
                    # < Revision 07/03/2025
                    # ds = read_file(filename, stop_before_pixels=True, specific_tags=tags)
                    ds = dcmread(filename, stop_before_pixels=True, specific_tags=tags)
                    # Revision 07/03/2025 >
                    for i in range(ds['StructureSetROISequence'].VM):
                        img.fill(0)
                        sq = ds['StructureSetROISequence']
                        name = sq[i][0x3006, 0x0026].value
                        sq = ds['ROIContourSequence']
                        color = sq[i][0x3006, 0x002a].value
                        # ROIContourSequence
                        for j in range(sq[i][0x3006, 0x0040].VM):
                            sqc = sq[i][0x3006, 0x0040][j]
                            if sqc[0x3006, 0x0042].value == 'CLOSED_PLANAR':
                                SOPInstanceUID = sqc[0x3006, 0x0016][0][0x0008, 0x1155].value
                                suffix = int(SOPInstanceUID.split('.')[-1])
                                cz = iudlist.index(suffix)
                                c = sqc[0x3006, 0x0050].value
                                cx = list()
                                cy = list()
                                for k in range(len(c) // 3):
                                    idx = k * 3
                                    p = self._refvol.getVoxelCoordinatesFromWorldCoordinates(c[idx:idx+3])
                                    cx.append(p[0])
                                    cy.append(p[1])
                                contour = list(zip(cy, cx))
                                slc = polygon2mask(npsize[-2:], contour)
                                img[cz, :, :] = img[cz, :, :] + slc.astype('uint8')
                            else: raise ValueError('ROI geometry {} is not supported.'.format(sqc[0x3006, 0x0042].value))
                        # Numpy to SimpleITK image
                        sitkimg = GetImageFromArray(img)
                        sitkimg.SetSpacing(self._refvol.getSpacing())
                        sitkimg.SetDirection(self._refvol.getDirections())
                        sitkimg.SetOrigin(self._refvol.getOrigin())
                        # SimpleITK to VTK orientation
                        sitkimg = flipImageToVTKDirectionConvention(sitkimg)
                        sitkimg = convertImageToAxialOrientation(sitkimg)[0]
                        # SimpleITK to SisypheROI
                        roi = SisypheROI(sitkimg)
                        roi.setReferenceID(self._refvol.getID())
                        roi.setName(name)
                        roi.setColor(int(color[0]), int(color[1]), int(color[2]))
                        if getdirs is False:
                            roi.setOrigin()
                            roi.setDirections()
                        # Save SisypheROI
                        if self._savetag:
                            if self._folder != '': folder = self._folder
                            else: folder = dirname(filename)
                            savename = join(folder, name) + SisypheROI.getFileExt()
                            if progress: progress.setInformationText('Save {}.'.format(basename(savename)))
                            # noinspection PyTypeChecker
                            roi.saveAs(savename)
                            if QApplication.instance() is not None: QApplication.processEvents()
                        self._rtroi.append(roi)
                if getdirs is False:
                    self._refvol.setOrigin()
                    self._refvol.setDirections()
                if self._savetag:
                    self._refvol.save()
                    if self._rtroi.count() > 0: self._rtroi.save()
                return self._rtroi
            else: raise ValueError('No Dicom RTStruct file to convert.')
        else: raise ValueError('No Dicom reference file to convert.')


class ExportToRTStruct(object):
    """
    ExportToRTStruct class

    Description
    -----------

    Class to convert PySisyphe ROI (.xroi) to Dicom RTSTRUCT.

    Inheritance
    -----------

    object -> ExportToRTStruct

    Creation: 08/09/2022
    Last revision: 27/03/2025
    """
    __slots__ = ['_rois', '_refvol', '_refframeuid', '_refseriesuid', '_refclassuid', '_folder', '_uid']

    # Class method

    @classmethod
    def getSettingsDirectory(cls) -> str:
        """
        Get PySisyphe user settings folder (~/.PySisyphe/settings.xml in user folder).

        Returns
        -------
        str
            PySisyphe user settings folder
        """
        import Sisyphe.settings
        return dirname(abspath(Sisyphe.settings.__file__))

    # Special method

    """
    Private attributes

    _folder         str, export folder
    _refvol         SisypheVolume, reference volume
    _refframeuid    str, frame uid of refrence volume
    _refseriesuid   str, series uid of refrence volume
    _refclassuid    str, class uid of reference voluem
    _rois           SisypheROICollection, ROI 
    _uid            list[str], instance uids
    """

    def __init__(self) -> None:
        """
        ExportToRTStruct instance constructor.
        """
        super().__init__()

        self._folder: str = ''
        self._refvol: SisypheVolume | None = None
        self._refframeuid: str = ''
        self._refseriesuid: str = ''
        self._refclassuid: str = ''
        self._rois: SisypheROICollection = SisypheROICollection()
        self._uid: list[str] = list()

    # Private methods

    def _hasXmlDicomReference(self) -> bool:
        filename = splitext(self._refvol.getFilename())[0] + XmlDicom().getFileExt()
        return exists(filename)

    # noinspection PyUnboundLocalVariable
    def _convertReference(self, progress: DialogWait | None = None) -> None:
        if self.hasReferenceVolume():
            if progress: progress.setInformationText('{} reference Dicom conversion...'
                                                     .format(basename(self._refvol.getFilename())))
            self._uid = list()
            # Datatype conversion to uint16
            if self._refvol.getDatatype() != 'uint16':
                vol = self._refvol.cast('uint16')
                img = vol.copyToSITKImage()
            else: img = self._refvol.copyToSITKImage()
            if QApplication.instance() is not None: QApplication.processEvents()
            # Spatial convention PySisyphe (VTK) to SITK/DICOM
            img = flipImageToVTKDirectionConvention(img)
            if QApplication.instance() is not None: QApplication.processEvents()
            # XmlDicom
            m = self._refvol.getAcquisition().getModality()
            # < revision 26/03/2025
            # if self._hasXmlDicomReference(): m2 = m
            # else: m2 = 'OT'
            if self._hasXmlDicomReference():
                xmlref = XmlDicom()
                xmlref.loadXmlDicomFilename(splitext(self._refvol.getFilename())[0] + XmlDicom().getFileExt())
            else: xmlref = None
            if m not in _DICOMMODALITIES: m = 'OT'
            filename = join(self.getSettingsDirectory(), m + XmlDicom.getFileExt())
            # revision 26/03/2025 >
            xmlbase = XmlDicom()
            xmlbase.loadXmlDicomFilename(filename)
            # UID generator
            gen = DicomUIDGenerator()
            gen.newStudy()
            gen.newSeries()
            # Convert to numpy
            np = GetArrayViewFromImage(img)
            try:
                for i in range(self._refvol.getDepth()):
                    gen.newInstance()
                    if i == 0:
                        # Create dicom dataset
                        filemeta = FileMetaDataset()
                        filemeta.FileMetaInformationVersion = b'\x00\x01'
                        # noinspection PyTypeChecker
                        filemeta.MediaStorageSOPClassUID = gen.getSOPClassUIDFromModality(m)
                        # noinspection PyTypeChecker
                        filemeta.ImplementationClassUID = gen.getImplementationClassUID()
                        filemeta.ImplementationVersionName = gen.getImplementationVersionName()
                        filemeta.TransferSyntaxUID = ExplicitVRLittleEndian
                        ds = FileDataset('temp', {}, file_meta=filemeta, preamble=b'\0' * 128, is_implicit_VR=False)
                        # Copy data elements
                        if self._hasXmlDicomReference():
                            for keyword in xmlbase.getKeywords():
                                if xmlref.hasKeyword(keyword):
                                    de = xmlref.getDataElement(keyword)
                                    if de: ds.add(de)
                                else:
                                    de = xmlbase.getDataElement(keyword)
                                    if de: ds.add(de)
                        else:
                            for keyword in xmlbase.getKeywords():
                                de = xmlbase.getDataElement(keyword)
                                if de: ds.add(de)
                            ds['Modality'].value = m
                            ds['SOPClassUID'].value = gen.getSOPClassUIDFromModality(m)
                        self._refclassuid = gen.getSOPClassUIDFromModality(m)
                        # Update constant attributes, edited once
                        # < Revision 27/03/2025
                        # ds['ImageType'].value = 'DERIVED SECONDARY AXIAL'
                        ds['ImageType'].value = ['DERIVED', 'SECONDARY', 'AXIAL']
                        # Revision 27/03/2025 >
                        ds['SliceThickness'].value = self._refvol.getSpacing()[2]
                        ds['SpacingBetweenSlices'].value = self._refvol.getSpacing()[2]
                        ds['Columns'].value = self._refvol.getSize()[0]
                        ds['Rows'].value = self._refvol.getSize()[1]
                        ds['PixelSpacing'].value = list(self._refvol.getSpacing()[:2])
                        ds['ImageOrientationPatient'].value = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
                        ds['SeriesInstanceUID'].value = gen.getCurrentSeriesUID()
                        self._refseriesuid = gen.getCurrentSeriesUID()
                        datescan = self._refvol.getAcquisition().getDateOfScan().replace('-', '')
                        ds['SeriesDate'].value = datescan
                        ds['SeriesTime'].value = gen.getSeriesTime()
                        ds['AcquisitionDate'].value = datescan
                        ds['ContentDate'].value = datescan
                        ds['InstanceCreationDate'].value = datescan
                        ds['AcquisitionTime'].value = gen.getInstanceTime()
                        ds['ContentTime'].value = gen.getInstanceTime()
                        ds['InstanceCreationTime'].value = gen.getInstanceTime()
                        ds['ImagesInAcquisition'].value = self._refvol.getDepth()
                        ds['FrameOfReferenceUID'].value = gen.getCurrentFrameOfReferenceUID()
                        self._refframeuid = gen.getCurrentFrameOfReferenceUID()
                        fov = self._refvol.getFieldOfView()
                        p = [-fov[0] / 2, -fov[1] / 2, -fov[2] / 2]
                        if self._hasXmlDicomReference():
                            ds['StudyInstanceUID'].value = xmlref['StudyInstanceUID']
                            ds['StudyID'].value = xmlref['StudyID']
                            ds['AccessionNumber'].value = xmlref['AccessionNumber']
                            ds['SeriesNumber'].value = xmlref['SeriesNumber'] + 20
                            ds['StudyDate'].value = xmlref['StudyDate']
                            ds['StudyTime'].value = xmlref['StudyTime']
                        else:
                            ds['StudyInstanceUID'].value = gen.getCurrentStudyUID()
                            ds['StudyID'].value = gen.getCurrentStudyID()
                            ds['AccessionNumber'].value = gen.getCurrentStudyID()
                            ds['SeriesNumber'].value = gen.getCurrentSeriesIndex()
                            ds['StudyDate'].value = gen.getStudyDate()
                            ds['StudyTime'].value = gen.getStudyTime()
                            ds['SeriesDescription'].value = self._refvol.getAcquisition().getSequence()
                            # Patient attributes
                            ds['PatientName'].value = '{}^{}'.format(self._refvol.getIdentity().getLastname(),
                                                                     self._refvol.getIdentity().getFirstname())
                            ds['PatientBirthDate'].value = \
                                self._refvol.getIdentity().getDateOfBirthday().replace('-', '')
                            gender = self._refvol.getIdentity().getGender(string=False)
                            if gender == 1: ds['PatientSex'].value = 'M'
                            elif gender == 2: ds['PatientSex'].value = 'F'
                            else: ds['PatientSex'].value = 'O'
                            ds['PatientAge'].value = '00{}Y'.format(self._refvol.getIdentity().getAge())[-4:]
                    # Update instance dependent attributes, edited for each instance
                    ds['SOPInstanceUID'].value = gen.getCurrentInstanceUID()
                    self._uid.append(gen.getCurrentInstanceUID())
                    ds['InstanceNumber'].value = gen.getCurrentInstanceIndex()
                    p[2] = p[2] - (i * self._refvol.getSpacing()[2])
                    ds['ImagePositionPatient'].value = p
                    ds['SliceLocation'].value = p[2]
                    minv = int(np[i, :, :].min())
                    maxv = int(np[i, :, :].max())
                    ds['SmallestImagePixelValue'].value = minv
                    ds['LargestImagePixelValue'].value = maxv
                    ds['WindowCenter'].value = (maxv - minv) // 2
                    ds['WindowWidth'].value = maxv - minv
                    ds['RescaleIntercept'].value = self._refvol.getIntercept()
                    ds['RescaleSlope'].value = self._refvol.getSlope()
                    # Add pixel array
                    ds.PixelData = np[i, :, :].tobytes()
                    # Save dicom file
                    savename = splitext(self._refvol.getFilename())[0] + '_' + '0000{}'.format(i)[-4:] + '.dcm'
                    if self._folder == '':
                        self._folder = dirname(savename)
                        mkdir(self._folder)
                    filename = join(self.getExportFolder(), basename(savename))
                    # noinspection PyTypeChecker
                    ds.file_meta.MediaStorageSOPInstanceUID = gen.getCurrentInstanceUID()
                    ds.save_as(filename, write_like_original=False)
                    if QApplication.instance() is not None: QApplication.processEvents()
            except: raise IOError('Dicom write error.')
        else: raise ValueError('No reference volume defined.')

    def _convertROI(self, progress: DialogWait | None = None) -> None:
        if self.hasROI():
            if progress: progress.setInformationText('Convert ROI(s) to Dicom RTStruct....')
            # UID generator
            gen = DicomUIDGenerator()
            gen.newStudy()
            gen.newSeries()
            gen.newInstance()
            # Create dicom dataset
            filemeta = FileMetaDataset()
            filemeta.FileMetaInformationVersion = b'\x00\x01'
            # noinspection PyTypeChecker
            filemeta.MediaStorageSOPClassUID = gen.getRTStructSOPClassUID()
            # noinspection PyTypeChecker
            filemeta.ImplementationClassUID = gen.getImplementationClassUID()
            filemeta.ImplementationVersionName = gen.getImplementationVersionName()
            filemeta.TransferSyntaxUID = ExplicitVRLittleEndian
            ds = FileDataset('temp', {}, file_meta=filemeta, preamble=b'\0' * 128, is_implicit_VR=False)
            # Xml Dicom default RTStruct
            filename = join(self.getSettingsDirectory(), 'RTSTRUCT' + XmlDicom.getFileExt())
            xmlbase = XmlDicom()
            xmlbase.loadXmlDicomFilename(filename)
            # Copy default data elements to dataset
            for keyword in xmlbase.getKeywords():
                de = xmlbase.getDataElement(keyword)
                if de: ds.add(de)
            # Default DataElements
            for key in xmlbase.getKeywords():
                if key == 'InstanceCreationDate': ds[key].value = gen.getStudyDate()
                elif key == 'InstanceCreationTime': ds[key].value = gen.getInstanceTime()
                elif key == 'SOPInstanceUID': ds[key].value = gen.getCurrentInstanceUID()
                elif key == 'StudyDate': ds[key].value = gen.getStudyDate()
                elif key == 'SeriesDate': ds[key].value = gen.getStudyDate()
                elif key == 'StudyTime': ds[key].value = gen.getStudyTime()
                elif key == 'SeriesTime': ds[key].value = gen.getSeriesTime()
                elif key == 'AccessionNumber': ds[key].value = gen.getCurrentStudyID()
                elif key == 'PatientName':
                    ds[key].value = '{}^{}'.format(self._refvol.getIdentity().getLastname(),
                                                   self._refvol.getIdentity().getFirstname())
                elif key == 'PatientBirthDate':
                    ds[key].value = self._refvol.getIdentity().getDateOfBirthday().replace('-', '')
                elif key == 'PatientSex':
                    gender = self._refvol.getIdentity().getGender(string=False)
                    if gender == 1: ds[key].value = 'M'
                    elif gender == 2: ds[key].value = 'F'
                    else: ds[key].value = 'O'
                elif key == 'PatientAge': ds[key].value = '00{}Y'.format(self._refvol.getIdentity().getAge())[-4:]
                elif key == 'StudyInstanceUID': ds[key].value = gen.getCurrentStudyUID()
                elif key == 'SeriesInstanceUID': ds[key].value = gen.getCurrentSeriesUID()
                elif key == 'StudyID': ds[key].value = gen.getCurrentStudyID()
                elif key == 'SeriesNumber': ds[key].value = gen.getCurrentSeriesIndex()
                elif key == 'InstanceNumber': ds[key].value = gen.getCurrentInstanceIndex()
                elif key == 'StructureSetName': pass
                elif key == 'StructureSetDate': ds[key].value = gen.getStudyDate()
                elif key == 'StructureSetTime': ds[key].value = gen.getInstanceTime()
                else: ds[key].value = xmlbase.getDataElementValue(key)
            # Referenced Frame of Reference Sequence
            dsframe = Dataset()
            # dsframe[0x0020, 0x0052].value = self._refframeuid                      # Frame of Reference UID
            dsframe.add_new((0x0020, 0x0052), dictionary_VR((0x0020, 0x0052)), self._refframeuid)
            dsrtstudy = Dataset()
            # dsrtstudy[0x0008, 0x1150].value = '1.2.840.10008.3.1.2.3.1'             # Referenced SOP Class UID
            # dsrtstudy[0x0008, 0x1155].value = gen.getCurrentInstanceUID()           # Referenced SOP Instance UID
            dsrtstudy.add_new((0x0008, 0x1150), dictionary_VR((0x0008, 0x1150)), '1.2.840.10008.3.1.2.3.1' )
            dsrtstudy.add_new((0x0008, 0x1155), dictionary_VR((0x0008, 0x1155)), gen.getCurrentInstanceUID())
            dsrtseries = Dataset()
            # dsrtseries[0x0020, 0x000e].value = self._refseriesuid                   # Series Instance UID
            dsrtseries.add_new((0x0020, 0x000e), dictionary_VR((0x0020, 0x000e)), self._refseriesuid)
            sq = list()
            for i in range(self._refvol.getDepth()):
                dsitem = Dataset()
                # dsitem[0x0008, 0x1150].value = self._refclassuid                    # Referenced SOP Class UID
                # dsitem[0x0008, 0x1155].value = self._uid[i]                         # Referenced SOP Instance UID
                dsitem.add_new((0x0008, 0x1150), dictionary_VR((0x0008, 0x1150)), self._refclassuid)
                dsitem.add_new((0x0008, 0x1155), dictionary_VR((0x0008, 0x1155)), self._uid[i])
                sq.append(dsitem)
            # dsrtseries[0x3006, 0x0016].value = Sequence(sq)                         # Contour Image Sequence
            dsrtseries.add_new((0x3006, 0x0016), dictionary_VR((0x3006, 0x0016)), Sequence(sq))
            # dsrtstudy[0x3006, 0x0014].value = Sequence([dsrtseries])                # RT Referenced Series Sequence
            dsrtstudy.add_new((0x3006, 0x0014), dictionary_VR((0x3006, 0x0014)), Sequence([dsrtseries]))
            # dsframe[0x3006, 0x0012].value = Sequence([dsrtstudy])                   # RT Referenced Study Sequence
            dsframe.add_new((0x3006, 0x0012), dictionary_VR((0x3006, 0x0012)), Sequence([dsrtstudy]))
            # ds['ReferencedFrameOfReferenceSequence'].value = Sequence([dsframe])
            ds.add_new((0x3006, 0x0010), dictionary_VR((0x3006, 0x0010)), Sequence([dsframe]))
            # Structure Set ROI Sequence
            index = 0
            sq = list()
            for roi in self._rois:
                dsitem = Dataset()
                # dsitem[0x3006, 0x0022].value = index                # Roi Number
                # dsitem[0x3006, 0x0024].value = self._refframeuid    # Referenced Frame of Reference UID
                # dsitem[0x3006, 0x0026].value = roi.getName()        # ROI Name
                # dsitem[0x3006, 0x0036].value = 'SEMIAUTOMATIC'      # ROI Generation Algorithm
                dsitem.add_new((0x3006, 0x0022), dictionary_VR((0x3006, 0x0022)), index)
                dsitem.add_new((0x3006, 0x0024), dictionary_VR((0x3006, 0x0024)), self._refframeuid)
                dsitem.add_new((0x3006, 0x0026), dictionary_VR((0x3006, 0x0026)), roi.getName())
                dsitem.add_new((0x3006, 0x0036), dictionary_VR((0x3006, 0x0036)), 'SEMIAUTOMATIC')
                # = MANUAL, SEMIAUTOMATIC, AUTOMATIC
                sq.append(dsitem)
                index += 1
            # ds['StructureSetROISequence'].value = Sequence(sq)
            ds.add_new((0x3006, 0x0020), dictionary_VR((0x3006, 0x0020)), Sequence(sq))
            # ROI Contour Sequence
            index = 0
            sqroi = list()
            for roi in self._rois:
                if progress: progress.setInformationText('Convert ROI {} to Dicom RTStruct.'.format(roi.getName()))
                # Calc contour
                img = roi.copyToSITKImage()
                img = flipImageToVTKDirectionConvention(img)
                npimg = GetArrayViewFromImage(img)
                sqcontour = list()
                sx, sy = self._refvol.getSpacing()[:2]
                fov = self._refvol.getFieldOfView()
                ox, oy = -fov[0] / 2, -fov[1] / 2
                for nslc in range(npimg.shape[0]):
                    slc = npimg[nslc, :, :]
                    if slc.sum() > 0:
                        contours = find_contours(npimg[nslc, :, :].astype('int64'), 0.5)
                        for contour in contours:
                            cy = contour[:, 0] * sy + oy
                            cx = contour[:, 1] * sx + ox
                            # cc = list(zip(cx, cy))
                            cc = list(sum(zip(cx, cy), ()))
                            dsref = Dataset()
                            # dsref[0x0008, 0x1150].value = self._refclassuid     # Referenced SOP Class UID
                            # dsref[0x0008, 0x1155].value = self._uid[nslc]       # Referenced SOP Instance UID
                            dsref.add_new((0x0008, 0x1150), dictionary_VR((0x0008, 0x1150)), self._refclassuid)
                            dsref.add_new((0x0008, 0x1155), dictionary_VR((0x0008, 0x1155)), self._uid[nslc])
                            dsitem = Dataset()
                            # dsitem[0x3006, 0x0016].value = Sequence([dsref])    # Contour Image Sequence
                            # dsitem[0x3006, 0x0042].value = 'CLOSED_PLANAR'      # Contour Geometric Type
                            # dsitem[0x3006, 0x0046].value = len(contour)         # Number of Contour Points
                            # dsitem[0x3006, 0x0050].value = cc                   # Contour Data
                            dsitem.add_new((0x3006, 0x0016), dictionary_VR((0x3006, 0x0016)), Sequence([dsref]))
                            dsitem.add_new((0x3006, 0x0042), dictionary_VR((0x3006, 0x0042)), 'CLOSED_PLANAR')
                            dsitem.add_new((0x3006, 0x0046), dictionary_VR((0x3006, 0x0046)), len(contour))
                            dsitem.add_new((0x3006, 0x0050), dictionary_VR((0x3006, 0x0050)), cc)
                            sqcontour.append(dsitem)
                # Add ROI sequence
                dsroi = Dataset()
                color = roi.getColor()
                color = [int(co * 255) for co in color]
                # dsroi[0x3006, 0x002a].value = color                 # ROI Display Color
                # dsroi[0x3006, 0x0084].value = index                 # Referenced ROI Number
                # dsroi[0x3006, 0x0040].value = Sequence(sqcontour)   # Contour Sequence
                dsroi.add_new((0x3006, 0x002a), dictionary_VR((0x3006, 0x002a)), color)
                dsroi.add_new((0x3006, 0x0084), dictionary_VR((0x3006, 0x0084)), index)
                dsroi.add_new((0x3006, 0x0040), dictionary_VR((0x3006, 0x0040)), Sequence(sqcontour))
                sqroi.append(dsroi)
                index += 1
            # ds['ROIContourSequence'].value = Sequence(sqroi)
            ds.add_new((0x3006, 0x0039), dictionary_VR((0x3006, 0x0039)), Sequence(sqroi))
            # RT ROI Observations Sequence
            sq = list()
            for i in range(len(self._rois)):
                index = i + 1
                dsitem = Dataset()
                # dsitem[0x3006, 0x0082].value = index            # Observation Number
                # dsitem[0x3006, 0x0084].value = index            # Referenced ROI Number
                # dsitem[0x3006, 0x00a4].value = 'ORGAN'          # RT ROI Interpreted Type
                # dsitem[0x3006, 0x00a6].value = ''               # ROI Interpreter
                dsitem.add_new((0x3006, 0x0082), dictionary_VR((0x3006, 0x0082)), index)
                dsitem.add_new((0x3006, 0x0084), dictionary_VR((0x3006, 0x0084)), index)
                dsitem.add_new((0x3006, 0x00a4), dictionary_VR((0x3006, 0x00a4)), 'ORGAN')
                dsitem.add_new((0x3006, 0x00a6), dictionary_VR((0x3006, 0x00a6)), 'None^None')
                sq.append(dsitem)
            # ds['RTROIObservationsSequence'].value = Sequence(sq)
            ds.add_new((0x3006, 0x0080), dictionary_VR((0x3006, 0x0080)), Sequence(sq))
            # Save dicom file
            savename = splitext(self._refvol.getFilename())[0] + '_RTSTRUCT.dcm'
            if self._folder == '':
                self._folder = dirname(savename)
                mkdir(self._folder)
            filename = join(self.getExportFolder(), basename(savename))
            # noinspection PyTypeChecker
            ds.file_meta.MediaStorageSOPInstanceUID = gen.getCurrentInstanceUID()
            ds.save_as(filename, write_like_original=False)
            if QApplication.instance() is not None: QApplication.processEvents()
        else: raise ValueError('No ROI defined.')

    # Public methods

    def setReferenceVolume(self, vol: str | SisypheVolume) -> None:
        """
        Set PySisyphe reference volume (.xvol). Dicom RTSTRUCT is always associated to a reference anatomical volume.
        PySisyphe reference is also converted to Dicom format during conversion. PySisyphe ROI to convert must have
        the same ID as the PySisyphe reference volume.

        Parameters
        ----------
        vol : str | Sisyphe.core.sisypheVolume.SisypheVolume
            PySisyphe reference volume file name (.xvol) or instance
        """
        if isinstance(vol, str):
            filename = vol
            if exists(filename):
                if splitext(filename)[1] == SisypheVolume.getFileExt():
                    vol = SisypheVolume()
                    vol.load(filename)
                else: raise IOError('{} is not SisypheVolume.'.format(basename(filename)))
            else: raise FileNotFoundError('No such file {}'.format(basename(filename)))
        if isinstance(vol, SisypheVolume):
            self._refvol = vol
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(vol)))

    def getReferenceVolume(self) -> SisypheVolume:
        """
        Get PySisyphe reference volume (.xvol). Dicom RTSTRUCT is always associated to a reference anatomical volume.
        PySisyphe reference is also converted to Dicom format during execute method. PySisyphe ROI to convert must have
        the same ID as the PySisyphe reference volume.

        Returns
        -------
        Sisyphe.core.sisypheVolume.SisypheVolume
        """
        return self._refvol

    def hasReferenceVolume(self) -> bool:
        """
        Checks whether PySisyphe reference volume is defined.

        Returns
        -------
        bool
            True if PySisyphe volume is defined
        """
        return self._refvol is not None

    def addROI(self, roi: str | SisypheROI) -> None:
        """
        Add PySisyphe ROI to the list of conversion. PySisyphe ROI must have the same ID as the PySisyphe reference
        volume.

        Parameters
        ----------
        roi : str | Sisyphe.core.sisypheROI.SisypheROI
            PySisyphe ROI file name or instance
        """
        if self.hasReferenceVolume():
            if isinstance(roi, str):
                filename = roi
                if exists(filename):
                    if splitext(filename)[1] == SisypheROI.getFileExt():
                        roi = SisypheROI()
                        roi.load(filename)
                        if roi.getReferenceID() != self._refvol.getID():
                            raise IOError('{} reference ID is not valid.'.format(basename(filename)))
                    else: raise IOError('{} is not SisypheROI.'.format(basename(filename)))
                else: raise FileNotFoundError('No such file {}'.format(basename(filename)))
            if isinstance(roi, SisypheROI):
                self._rois.append(roi)
            else: raise TypeError('parameter type {} is not str or SisypheROI.'.format(type(roi)))
        else: raise ValueError('No reference volume.')

    def getROI(self) -> SisypheROICollection:
        """
        Get PySisyphe ROI(s) to convert.

        Returns
        -------
        Sisyphe.core.sisypheROI.SisypheROICollection
            ROIs list to convert
        """
        return self._rois

    def hasROI(self) -> bool:
        """
        Checks whether PySisyphe ROIs list of conversion is not empty.

        Returns
        -------
        bool
            True if PySisyphe ROIs list of conversion is not empty
        """
        return len(self._rois) > 0

    def setExportFolder(self, folder: str) -> None:
        """
        Set the path of the backup folder. Dicom RTStruct file is saved in this directory.

        Parameters
        ----------
        folder : str
            path of the backup folder
        """
        if isinstance(folder, str):
            if exists(folder):
                self._folder = folder
            else: raise FileNotFoundError('No such folder {}.'.format(folder))
        else: raise TypeError('parameter type {} is not str.'.format(type(folder)))

    def getExportFolder(self) -> str:
        """
        Get the path of the backup folder. Dicom RTSTRUCT file is saved in this directory.

        Returns
        -------
        str
            path of the backup folder
        """
        return self._folder

    def hasExportFolder(self) -> bool:
        """
        Checks whether backup folder is defined.

        Returns
        -------
        bool
            True if backup folder is defined
        """
        return self._folder != ''

    def clear(self) -> None:
        """
        Reset all ExportToRTStruct instance attributes.
        """
        self._folder = ''
        self._refvol = None
        self._refframeuid = ''
        self._refseriesuid = ''
        self._refclassuid = ''
        self._rois.clear()
        self._uid = list()

    def execute(self, progress: DialogWait | None = None) -> None:
        """
        Run PySisyphe ROI (.xroi) to Dicom RTSTRUCT conversion.

        Parameters
        ----------
        progress : Sisyphe.gui.dialogWait.DialogWait
            progress bar dialog (optional)
        """
        if self.hasReferenceVolume():
            if self.hasROI():
                self._convertReference(progress)
                self._convertROI(progress)
            else: raise ValueError('No ROI defined.')
        else: raise ValueError('No reference volume.')
