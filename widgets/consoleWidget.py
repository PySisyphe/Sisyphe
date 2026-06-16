"""
External packages/modules
-------------------------

    - google-genai, gemini LLM API, https://googleapis.github.io/python-genai/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - Numpy, Scientific computing, https://numpy.org/
    - Pillow,  image processing, https://pillow.readthedocs.io/
    - SimpleITK, medical image processing, https://simpleitk.org/
    - qtconsole, Python console widget, https://qtconsole.readthedocs.io/en/stable/
    - vtk, visualization engine/3D rendering, https://vtk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any
import sys
from sys import platform

from os.path import join
from os.path import exists
from os.path import abspath
from os.path import dirname
from os.path import splitext
# noinspection PyUnusedImports
from os.path import basename

from pathlib import Path

import types

import pkgutil

import traceback

import json

# < Revision 19/02/2025
from ants.core.ants_image import ANTsImage
# from Sisyphe.lib.ants.ants_image import ANTsImage
# Revision 19/02/2025 >

from numpy import array
from numpy import ndarray
from numpy import issubdtype
from numpy import number
from numpy import argwhere

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton

from PIL.Image import Image as pilImage

from SimpleITK import Image as sitkImage

from vtk import vtkImageData

import darkdetect

from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheDownload import getPackageMetadata
from Sisyphe.core.sisypheImageIO import isDicom
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.gui.dialogFromXml import DialogFromXml
from Sisyphe.gui.dialogWait import DialogWait

if TYPE_CHECKING:
    from PyQt5.QtGui import QKeyEvent
    from Sisyphe.gui.windowSisyphe import WindowSisyphe

__all__ = ['ConsoleWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> ConsoleWidget

"""

class RichJupyterWidget2(RichJupyterWidget):
    """
    Last revision: 14/12/2025
    """

    # < Revision 09/12/2025
    # override __init__() method
    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        settings = SisypheSettings()
        self._aikey = settings.getFieldValue('Gemini', 'APIKey')
        self._aimodel = settings.getFieldValue('Gemini', 'Model')
        if self._aimodel is None or self._aimodel == '':
            self._aimodel = 'gemini-2.5-flash'
        self._client = None
        self._update = None
    # Revision 09/12/2025 >

    def _event_filter_console_keypress(self, event) -> bool:
        # noinspection PyProtectedMember
        r = super()._event_filter_console_keypress(event)
        k = event.text()
        if k == '.':
            self._control.insertPlainText('.')
            self._complete()
            r = True
        elif k == '(':
            self._control.insertPlainText('()')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '[':
            self._control.insertPlainText('[]')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '{':
            self._control.insertPlainText('{}')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '\'':
            self._control.insertPlainText('\'\'')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '\"':
            self._control.insertPlainText('\"\"')
            self._control.moveCursor(9, 0)
            r = True
        return r

    # < Revision 08/02/2026
    def _gemini(self) -> None:
        # history
        history = self.input_buffer
        history = history.rstrip()
        if history and (not self._history or self._history[-1] != history):
            self._history.append(history)
        # noinspection PyAttributeOutsideInit
        self._history_index = len(self._history)
        # parse args
        nb = self._previous_prompt_obj.number + 1
        buff = self.input_buffer.split(' \'')
        buff2 = list()
        for i in range(len(buff)):
            sbuff = buff[i].split('\'')
            if len(sbuff) == 1:
                sbuff2 = sbuff[0].split(' ')
                for j in range(len(sbuff2)):
                    buff2.append(sbuff2[j])
            else:
                buff2.append(sbuff[0])
                sbuff2 = sbuff[1].split(' ')
                for j in range(len(sbuff2)):
                    buff2.append(sbuff2[j])
        buff = array(buff2[1:])
        buff = buff[buff != '']
        if self._aikey is not None and self._aikey != '':
            # < Revision 08/02/2026
            try: from google import genai
            except:
                if hasattr(sys, '_MEIPASS'):
                    self._append_plain_text('\ngoogle-genai module is not installed.\n'
                                            'Please perform a complete reinstallation of the latest version '
                                            'of PySisyphe, which can be downloaded from '
                                            'https://github.com/PySisyphe/Sisyphe.')
                else:
                    self._append_plain_text('\ngoogle-genai module is not installed.\n'
                                            'Please install it using "pip install google-genai==1.55.0" from your venv console.')
                self._show_interpreter_prompt(nb)
                return
            # Revision 08/02/2026 >
            tag = True
            jsontag = False
            content = list()
            config = None
            if self._client is None:
                # < Revision 14/12/2025
                try:
                    self._client = genai.Client(api_key=self._aikey)
                except:
                    self._append_plain_text('\ngoogle module error.')
                    self._show_interpreter_prompt(nb)
                    return
                # Revision 14/12/2025 >
            g = self.kernel_manager.kernel.shell.user_ns
            # help arg
            if '?' in buff or '-help' in buff:
                self._append_plain_text('\n%gemini args:\n'
                                        '  -p prompt, str\n'
                                        '  -i image input, PIL.Image\n'
                                        '  -pdf input, str or pathlib.Path\n'
                                        '  -json, reply format json\n'
                                        '  -model, print ai model\n'
                                        '  -key, print api key\n',
                                        before_prompt=False)
                self._show_interpreter_prompt(nb)
                return
            # model arg
            if '-model' in buff:
                tag = False
                self._append_plain_text('\n%gemini model: {}'.format(self._aimodel))
            # key arg
            if '-key' in buff:
                tag = False
                if self._aikey in (None, ''):
                    self._append_plain_text('\n%gemini api key: no api key')
                else:
                    self._append_plain_text('\n%gemini api key: {}'.format(self._aikey))
            # json flag arg
            if '-json' in buff:
                jsontag = True
                config = genai.types.GenerateContentConfig(response_mime_type='application/json')
            # segmentation flag arg
            # if '-seg' in buff:
            #     config = genai.types.GenerateContentConfig(response_mime_type='application/json',
            #                                                thinking_config=genai.types.ThinkingConfig(thinking_budget=0))
            # prompt arg
            if '-p' in buff:
                i = argwhere(buff == '-p')[0][0]
                if i < len(buff) - 1 and buff[i + 1] != '-':
                    buffp = buff[i + 1]
                    # noinspection PyUnresolvedReferences
                    if len(buffp.split(' ')) > 1:
                        content.append(buffp[1:-1])
                    else:
                        if buffp in g.keys():
                            v = g[buffp]
                            if isinstance(v, str):
                                content.append(v)
                            else:
                                self._append_plain_text('\n%gemini prompt error:\n'
                                                        '{} type is not str.'.format(buffp),
                                                        before_prompt=False)
                                self._show_interpreter_prompt(nb)
                                return
                        else:
                            self._append_plain_text('\n%gemini prompt error:\n'
                                                    '{} not exists.'.format(buffp),
                                                    before_prompt=False)
                            self._show_interpreter_prompt(nb)
                            return
                else:
                    self._append_plain_text('\n%gemini prompt error:\n'
                                            'no prompt specified.',
                                            before_prompt=False)
                    self._show_interpreter_prompt(nb)
                    return
            else:
                if tag:
                    self._append_plain_text('\n%gemini prompt error:\n'
                                            'no prompt specified.',
                                            before_prompt=False)
                self._show_interpreter_prompt(nb)
                return
            # image arg
            if '-i' in buff:
                i = argwhere(buff == '-i')[0][0]
                if i < len(buff) - 1 and buff[i + 1] != '-':
                    buffp = buff[i + 1]
                    if buffp in g.keys():
                        v = g[buffp]
                        if isinstance(v, pilImage):
                            content.append(v)
                        else:
                            self._append_plain_text('\n%gemini image error:\n'
                                                    '{} is not a Pillow image.'.format(buffp),
                                                    before_prompt=False)
                            self._show_interpreter_prompt(nb)
                            return
                    else:
                        self._append_plain_text('\n%gemini error:\n'
                                                '{} not exists.'.format(buffp),
                                                before_prompt=False)
                        self._show_interpreter_prompt(nb)
                        return
                else:
                    self._append_plain_text('\n%gemini error:\n'
                                            'no image specified.',
                                            before_prompt=False)
                    self._show_interpreter_prompt(nb)
                    return
            # pdf arg
            if '-pdf' in buff:
                i = argwhere(buff == '-i')[0][0]
                if i < len(buff) - 1 and buff[i + 1] != '-':
                    v = None
                    buffp = buff[i + 1]
                    # noinspection PyTypeChecker
                    if exists(buffp):
                        # noinspection PyTypeChecker
                        v = Path(buffp)
                    if buffp in g.keys():
                        v = g[buffp]
                        if isinstance(v, str):
                            if exists(v): v = Path(v)
                    if isinstance(v, Path):
                        if v.exists():
                            content.append(genai.types.Part.from_bytes(data=v.read_bytes(),
                                                                       mime_type='application/pdf'))
                        else:
                            self._append_plain_text('\n%gemini error:\n'
                                                    'no such file {}.'.format(v),
                                                    before_prompt=False)
                            self._show_interpreter_prompt(nb)
                            return
                    else:
                        self._append_plain_text('\n%gemini error:\n'
                                                'invalid pdf {}.'.format(v),
                                                before_prompt=False)
                        self._show_interpreter_prompt(nb)
                        return
            # execute request
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Waiting for gemini reponse...')
            try:
                r = self._client.models.generate_content(model=self._aimodel,
                                                         contents=content,
                                                         config=config)
                r = r.text
                if isinstance(r, str):
                    self.kernel_manager.kernel.shell.push({'r': r})
                    if jsontag:
                        self.execute('import json', hidden=True)
                        self.execute('r = json.loads(r)', hidden=True)
                        r = json.loads(r)
                    self._append_plain_text('\n{}'.format(r))
                    if self._update is not None: self._update()
            except:
                self._append_plain_text('\n%gemini client error:\n{}'.format(traceback.format_exc()),
                                        before_prompt=False)
            finally:
                wait.close()
        else:
            self._append_plain_text('\n%gemini API key error:\n'
                                    'No API key.\nGo to PySisyphe settings (General/Gemini) to edit your API Key.\n'
                                    'Get your API key from Google AI Studio https://aistudio.google.com/api-keys',
                                    before_prompt=False)
        self._show_interpreter_prompt(nb)
    # Revision 08/02/2026 >

    # < Revision 08/02/2026
    def _packages(self) -> None:
        # history
        history = self.input_buffer
        history = history.rstrip()
        if history and (not self._history or self._history[-1] != history):
            self._history.append(history)
        # noinspection PyAttributeOutsideInit
        self._history_index = len(self._history)
        # parse args
        nb = self._previous_prompt_obj.number + 1
        buff = self.input_buffer.split(' ')
        if len(buff) > 1: buff = buff[1:]
        else: buff = None
        # help arg
        if '?' in buff or '-help' in buff:
            self._append_plain_text('\n%packages args:\n'
                                    '  no arg or package names separated by spaces',
                                    before_prompt=False)
            self._show_interpreter_prompt(nb)
            return
        # execute command
        wait = DialogWait()
        wait.open()
        try: r = getPackageMetadata(packages=buff, wait=wait)
        except:
            self._show_interpreter_prompt(nb)
            return
        wait.close()
        self.kernel_manager.kernel.shell.push({'r': r})
        self._append_plain_text('\n{}'.format(r))
        if self._update is not None: self._update()
        self._show_interpreter_prompt(nb)
    # Revision 08/02/2026 >

    # < Revision 08/02/2026
    def _open(self) -> None:
        # history
        history = self.input_buffer
        history = history.rstrip()
        if history and (not self._history or self._history[-1] != history):
            self._history.append(history)
        # noinspection PyAttributeOutsideInit
        self._history_index = len(self._history)
        # parse args
        nb = self._previous_prompt_obj.number + 1
        buff = self.input_buffer.split(' ')
        if len(buff) > 1: buff = buff[1]
        else:
            self._append_plain_text('\nfilename argument is missing.')
            self._show_interpreter_prompt(nb)
            return
        # help arg
        if '?' in buff or '-help' in buff:
            self._append_plain_text('\n%open args: filename\n'
                                    'Supported extensions are:\n'
                                    '  .xvol: PySisyphe volume\n'
                                    '  .nii, .hdr, .img, .nia, .nii.gz, .img.gz: Nifti volume\n'
                                    '  .nrrd, .nhdr: Nrrd volume\n'
                                    '  .mnc, .minc: Minc volume\n'
                                    '  .mgh, mgz: FreeSurfer volume\n'
                                    '  .vol: Sisyphe volume\n'
                                    '  .vmr: BrainVoyager volume\n'
                                    '  .vtk, .vti: VTK volume\n'
                                    '  .xroi: PySisyphe ROI\n'
                                    '  .roi: Sisyphe ROI\n'
                                    '  .xlut: PySisyphe LUT\n'
                                    '  .lut: Sisyphe/MRIcron LUT\n'
                                    '  .olt: BrainVoyager LUT\n'
                                    '  .xfid: PySisyphe stereotactic frame markers\n'
                                    '  .xtrf: PySisyphe geometric transformation\n'
                                    '  .xtrfs: collection of PySisyphe geometric transformations\n'
                                    '  .xfm: XFM geometric transformation\n'
                                    '  .tfm: TFM geometric transformation\n'
                                    '  .trf: BrainVoyager geometric transformation\n'
                                    '  .mat: ANTs geometric transformation\n'
                                    '  .xmesh: PySisyphe Mesh\n'
                                    '  .obj: OBJ wavefront Mesh\n'
                                    '  .stl: STL 3D Systems Mesh\n'
                                    '  .vtp: VTK Mesh\n'
                                    '  .xtools: collection of PySisyphe tools\n'
                                    '  .xline: PySisyphe trajectory tool\n'
                                    '  .xpoint: PySisyphe target tool\n'
                                    '  .xtract: PySisyphe Streamlines\n'
                                    '  .tck: TCK Streamlines\n'
                                    '  .trk: TRK Streamlines\n'
                                    '  .trk: TRK Streamlines\n'
                                    '  .fib: FIB Streamlines\n'
                                    '  .dpy: Dipy Streamlines\n'
                                    '  .xidentity: PySisyphe identity attributes\n'
                                    '  .xacq: PySisyphe acquisition attributes\n'
                                    '  .xdisplay: PySisyphe display attributes\n'
                                    '  .xacpc: PySisyphe AC-PC attributes\n'
                                    '  .xdcm: PySisyphe XML Dicom\n'
                                    '  .dcm, .dicom, .ima, .nema: DICOM image\n'
                                    '  .json: JSON format\n'
                                    '  .npy, .npz: Numpy vector/array format\n'
                                    '  .csv: CSV table format\n'
                                    '  .xlsx: Excel table format\n'
                                    '  .xsheet: PySisyphe table format\n'
                                    '  .sav: SPSS table format\n'
                                    '  .dta: Stata table format\n'
                                    '  .sas7bdat: SAS table format\n'
                                    '  .pdf: PDF format\n'
                                    '  .xml: XML format\n'
                                    '  .txt: Text format\n',
                                    before_prompt=False)
            self._show_interpreter_prompt(nb)
            return
        # execute command
        if exists(buff):
            ext = splitext(buff)[1].lower()
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Open {}...'.format(buff))
            import pydicom as pd
            try:
                if ext == '.xvol':
                    r = SisypheVolume()
                    r.load(buff)
                elif ext in ('.nii', '.hdr', '.img', '.nia', '.nii.gz', '.img.gz'):
                    r = SisypheVolume()
                    r.loadFromNIFTI(buff)
                elif ext in ('.nrrd', '.nhdr'):
                    r = SisypheVolume()
                    r.loadFromNRRD(buff)
                elif ext in ('.mnc', '.minc'):
                    r = SisypheVolume()
                    r.loadFromMINC(buff)
                elif ext in ('.mgh', '.mgz'):
                    r = SisypheVolume()
                    r.loadFromFreeSurferMGH(buff)
                elif ext == '.vol':
                    r = SisypheVolume()
                    r.loadFromSisyphe(buff)
                elif ext == '.vmr':
                    r = SisypheVolume()
                    r.loadFromBrainVoyagerVMR(buff)
                elif ext in ('.vtk', '.vti'):
                    r = SisypheVolume()
                    r.loadFromVTK(buff)
                elif ext == '.xroi':
                    r = SisypheROI()
                    r.load(buff)
                elif ext == '.roi':
                    r = SisypheROI()
                    r.loadFromSisyphe(buff)
                elif ext == '.lut':
                    r = SisypheLut()
                    r.load(buff)
                elif ext == '.xlut':
                    r = SisypheLut()
                    r.loadFromXML(buff)
                elif ext == '.olt':
                    r = SisypheLut()
                    r.loadFromOlt(buff)
                elif ext == '.xfid':
                    from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
                    r = SisypheFiducialBox()
                    r.loadFromXML(buff)
                elif ext == '.xtrf':
                    from Sisyphe.core.sisypheTransform import SisypheTransform
                    r = SisypheTransform()
                    r.load(buff)
                elif ext == '.xtrfs':
                    from Sisyphe.core.sisypheTransform import SisypheTransformCollection
                    r = SisypheTransformCollection()
                    r.load(buff)
                elif ext == '.xfm':
                    from Sisyphe.core.sisypheTransform import SisypheTransform
                    r = SisypheTransform()
                    r.loadFromXfmTransform(buff)
                elif ext == '.tfm':
                    from Sisyphe.core.sisypheTransform import SisypheTransform
                    r = SisypheTransform()
                    r.loadFromTfmTransform(buff)
                elif ext == '.trf':
                    from Sisyphe.core.sisypheTransform import SisypheTransform
                    r = SisypheTransform()
                    r.loadFromBrainVoyagerTransform(buff)
                elif ext == '.mat':
                    from Sisyphe.core.sisypheTransform import SisypheTransform
                    r = SisypheTransform()
                    try: r.loadFromANTSTransform(buff)
                    except:
                        from scipy.io import loadmat
                        # noinspection PyUnusedLocal
                        r = loadmat(buff)
                elif ext == '.xmesh':
                    from Sisyphe.core.sisypheMesh import SisypheMesh
                    r = SisypheMesh()
                    r.load(buff)
                elif ext == '.obj':
                    from Sisyphe.core.sisypheMesh import SisypheMesh
                    r = SisypheMesh()
                    r.loadFromOBJ(buff)
                elif ext == '.stl':
                    from Sisyphe.core.sisypheMesh import SisypheMesh
                    r = SisypheMesh()
                    r.loadFromSTL(buff)
                elif ext == '.vtp':
                    from Sisyphe.core.sisypheMesh import SisypheMesh
                    r = SisypheMesh()
                    r.loadFromXMLVTK(buff)
                elif ext == '.xtools':
                    from Sisyphe.core.sisypheTools import ToolWidgetCollection
                    r = ToolWidgetCollection()
                    r.load(buff)
                elif ext == '.xline':
                    from Sisyphe.core.sisypheTools import LineWidget
                    r = LineWidget('line')
                    r.load(buff)
                elif ext == '.xpoint':
                    from Sisyphe.core.sisypheTools import HandleWidget
                    r = HandleWidget('point')
                    r.load(buff)
                elif ext == '.xtract':
                    from Sisyphe.core.sisypheTracts import SisypheStreamlines
                    r = SisypheStreamlines()
                    r.load(buff)
                elif ext == '.tck':
                    from Sisyphe.core.sisypheTracts import SisypheStreamlines
                    r = SisypheStreamlines()
                    r.loadFromTck(buff)
                elif ext == '.trk':
                    from Sisyphe.core.sisypheTracts import SisypheStreamlines
                    r = SisypheStreamlines()
                    r.loadFromTrk(buff)
                elif ext == '.fib':
                    from Sisyphe.core.sisypheTracts import SisypheStreamlines
                    r = SisypheStreamlines()
                    r.loadFromFib(buff)
                elif ext == '.dpy':
                    from Sisyphe.core.sisypheTracts import SisypheStreamlines
                    r = SisypheStreamlines()
                    r.loadFromDpy(buff)
                elif ext == '.xidentity':
                    from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
                    r = SisypheIdentity()
                    r.loadFromXML(buff)
                elif ext == '.xacq':
                    from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
                    r = SisypheAcquisition()
                    r.loadFromXML(buff)
                elif ext == '.xdisplay':
                    from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
                    r = SisypheDisplay()
                    r.loadFromXML(buff)
                elif ext == '.xacpc':
                    from Sisyphe.core.sisypheImageAttributes import SisypheACPC
                    r = SisypheACPC()
                    r.loadFromXML(buff)
                elif ext == '.xdcm':
                    from Sisyphe.core.sisypheDicom import XmlDicom
                    r = XmlDicom()
                    r.loadXmlDicomFilename(buff)
                elif ext in ('.dcm', '.dicom', '.ima', '.nema'):
                    # noinspection PyUnusedLocal
                    r = pd.dcmread(buff)
                elif ext == '.json':
                    # noinspection PyUnusedLocal
                    r = json.loads(buff)
                elif ext in ('.npy', '.npz'):
                    import numpy as np
                    # noinspection PyUnusedLocal
                    r = np.load(buff)
                elif ext == '.csv':
                    import pandas as pd
                    # noinspection PyUnusedLocal
                    r = pd.read_csv(buff)
                elif ext == '.xlsx':
                    import pandas as pd
                    # noinspection PyUnusedLocal
                    try: r = pd.read_excel(buff)
                    except:
                        # < Revision 19/02/2026
                        try:
                            wait.close()
                            import openpyxl
                        except:
                            if hasattr(sys, '_MEIPASS'):
                                messageBox(self,
                                           'XLSX IO',
                                           'OpenPyXL module is not installed.\n'
                                           'Please perform a complete reinstallation of the latest version '
                                           'of PySisyphe, which can be downloaded from '
                                           'https://github.com/PySisyphe/Sisyphe.')
                            else:
                                messageBox(self,
                                           'XLSX IO',
                                           'OpenPyXL module is not installed.\n'
                                           'Please install it using "pip install openpyxl==3.1.5" from your venv console.')
                        self._append_plain_text('\nOpen {} error.'.format(basename(buff)),
                                                before_prompt=False)
                        self._show_interpreter_prompt(nb)
                        return
                        # Revision 19/02/2026 >
                elif ext == '.xsheet':
                    from Sisyphe.core.sisypheSheet import SisypheSheet
                    r = SisypheSheet()
                    r.load(buff)
                elif ext == '.sav':   # SPSS format
                    import pandas as pd
                    # noinspection PyUnusedLocal
                    r = pd.read_spss(buff)
                elif ext == '.dta':  # Stata format
                    import pandas as pd
                    # noinspection PyUnusedLocal
                    r = pd.read_stata(buff)
                elif ext == '.sas7bdat':  # SAS format
                    import pandas as pd
                    # noinspection PyUnusedLocal
                    r = pd.read_sas(buff)
                elif ext == '.pdf':
                    try: import pymupdf
                    except:
                        # < Revision 19/02/2026
                        if hasattr(sys, '_MEIPASS'):
                            messageBox(self,
                                       'PDF IO',
                                       'PyMuPDF module is not installed.\n'
                                       'Please perform a complete reinstallation of the latest version '
                                       'of PySisyphe, which can be downloaded from '
                                       'https://github.com/PySisyphe/Sisyphe.')
                        else:
                            messageBox(self,
                                       'PDF IO',
                                       'PyMuPDF module is not installed.\n'
                                       'Please install it using "pip install PyMuPDF==1.26.7" from your venv console.')
                        self._append_plain_text('\nOpen {} error.'.format(basename(buff)),
                                                before_prompt=False)
                        self._show_interpreter_prompt(nb)
                        return
                        # Revision 19/02/2026 >
                    # noinspection PyUnusedLocal
                    r = pymupdf.open(buff)
                elif ext in ('.xml', '.txt'):
                    with open(buff, 'r') as f:
                        # noinspection PyUnusedLocal
                        r = f.readlines()
                elif isDicom(buff):
                    # noinspection PyUnusedLocal
                    r = pd.dcmread(buff)
                else:
                    wait.close()
                    self._append_plain_text('\n{} file extension is not supported.'.format(ext),
                                            before_prompt=False)
                    self._show_interpreter_prompt(nb)
                    return
                self.kernel_manager.kernel.shell.push({'v': r})
                self._append_plain_text('\n{} file is loaded into v variable.'.format(buff))
                if self._update is not None: self._update()
                self._show_interpreter_prompt(nb)
            except:
                self._append_plain_text('\nIO error, unable to load {}.'.format(buff))
                self._show_interpreter_prompt(nb)
            wait.close()
        else:
            self._append_plain_text('\nno such file {}.'.format(buff))
            self._show_interpreter_prompt(nb)
            return
        # Revision 08/02/2026 >

    # < Revision 09/12/2025
    # override execute method
    # noinspection PyProtectedMember
    def execute(self,
                source: str | None = None,
                hidden: bool = False,
                interactive: bool = False):
        if source is None:
            if self.input_buffer[:7] == '%gemini':
                self._gemini()
                return
            elif self.input_buffer[:9] == '%packages':
                self._packages()
                return
            elif self.input_buffer[:5] == '%open':
                self._open()
                return
        super().execute(source, hidden, interactive)
    # Revision 09/12/2025 >


class ConsoleWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    Embedded IPython Qt console.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ConsoleWidget

    Last revision: 27/04/2026
    """

    @classmethod
    def isDarkMode(cls) -> bool:
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        return darkdetect.isLight()

    @classmethod
    def getDocDirectory(cls) -> str:
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'doc')
    
    # Special method

    """
    Private attribute

    _mainwindow     WindowSisyphe, PySisyphe main window
    _variables      dict
    _console        RichJupyterWidget
    _modules        QTreeWidget
    _globals        QTreeWidget
    _action         dict[QAction]
    _popup          QMenu
    """

    def __init__(self,
                 variables: dict[str, Any] | None = None,
                 parent: QWidget | None = None):
        super().__init__(parent)

        self._vol = None

        # Console

        self._mainwindow = None
        self._variables = variables
        # < Revision 08/03/2025
        # add font family and point size (QApplication font)
        # < Revision 01/12/2025
        # self._console = RichJupyterWidget(gui_completion='droplist',
        #                                   font_family=self.font().family(),
        #                                   font_size=self.font().pointSize())
        self._console = RichJupyterWidget2(gui_completion='droplist',
                                           font_family=self.font().family(),
                                           font_size=self.font().pointSize())
        # < Revision 09/12/2025
        self._console._update = self.update
        # Revision 09/12/2025 >
        # Revision 01/12/2025 >
        # Revision 08/03/2025 >
        if self.isDarkMode(): self._console.set_default_style('linux')
        else: self._console.set_default_style('lightbg')
        self._console.paging = 'none'
        self._console.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=False)
        kernel_manager.kernel.gui = 'qt'
        self._console.kernel_client = kernel_client = self._console.kernel_manager.client()
        kernel_client.start_channels()
        self.pushVariables(variables)

        # < Revision 27/04/2026
        # inline setup
        try:
            # workaround for the exception raised by %matplotlib inline during a frozen execution
            # this bug is related to upgrading Matplotlib to version 3.10.8.
            if hasattr(sys, '_MEIPASS'):
                self._console.execute("import matplotlib; matplotlib.use('QtAgg')", hidden=True)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, self._enable_inline)
                # self._console.execute(setup_inline, hidden=True)
            else: self._console.execute('%matplotlib inline', hidden=True)
        except: pass
        # Revision 27/04/2026 >

        if platform == 'win32':
            # bug fix of windows console encodings (code page 850 vs code page 1252)
            self._console.execute('import os', hidden=True)
            # < Revision 22/12/2025
            # self._console.execute('os.system("chcp 65001")', hidden=True)
            self._console.execute('os.system("chcp 65001 > NUL")', hidden=True)
            # Revision 22/12/2025 >

        path = join(self.getDocDirectory(), 'ipython.txt')
        if exists(path):
            with open(path, 'r') as f:
                buff = f.readlines()
            self.setToolTip(''.join(buff))

        # Modules and variables listwidgets

        self._modules = QTreeWidget()
        self._modules.setHeaderLabel('Module(s) / Type(s) / Function(s)')
        self._modules.setToolTip('Module(s) / Type(s) / Function(s)')
        self._modules.setAlternatingRowColors(True)
        # noinspection PyUnresolvedReferences
        self._modules.itemDoubleClicked.connect(self._modulesDblClicked)

        self._globals = QTreeWidget()
        self._globals.setHeaderLabel('Variables')
        self._globals.setToolTip('Variables')
        self._globals.setAlternatingRowColors(True)
        # < Revision 01/12/2025
        # noinspection PyUnresolvedReferences
        self._globals.setContextMenuPolicy(Qt.CustomContextMenu)
        # noinspection PyUnresolvedReferences
        self._globals.customContextMenuRequested.connect(self._popupGlobals)
        # Revision 01/12/2025 >
        # noinspection PyUnresolvedReferences
        self._globals.itemDoubleClicked.connect(self._globalsDblClicked)
        # noinspection PyUnresolvedReferences
        self._globals.itemClicked.connect(self._globalsClicked)

        splt = QSplitter()
        splt.addWidget(self._modules)
        splt.addWidget(self._globals)
        # noinspection PyUnresolvedReferences
        splt.setOrientation(Qt.Vertical)

        splitter = QSplitter()
        splitter.addWidget(self._console)
        splitter.addWidget(splt)
        # noinspection PyUnresolvedReferences
        splitter.setOrientation(Qt.Horizontal)

        # Buttons

        btnlyout = QHBoxLayout()
        btnlyout.setContentsMargins(0, 0, 0, 0)
        btnlyout.setSpacing(5)
        self._save = QPushButton('Save as HTML/XML...', parent=self)
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.save)
        self._save.setToolTip('Save console to HTML/XML file')
        # < Revision 25/04/2025
        # self._copy = QPushButton('Copy', parent=self)
        # self._copy.setToolTip('Copy selection to clipboard')
        # noinspection PyUnresolvedReferences
        # self._copy.clicked.connect(self.copy)
        # Revision 25/04/2025 >
        self._clear = QPushButton('Clear', parent=self)
        self._clear.setToolTip('Clear console display')
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(self.clear)
        self._restart = QPushButton('Restart', parent=self)
        self._restart.setToolTip('Restart console')
        # noinspection PyUnresolvedReferences
        self._restart.clicked.connect(self.restart)
        self._import = QPushButton('Import', parent=self)
        self._import.setToolTip('Import PySisyphe modules')

        btnlyout.addStretch()
        btnlyout.addWidget(self._import)
        btnlyout.addWidget(self._clear)
        # < Revision 25/04/2025
        # btnlyout.addWidget(self._copy)
        # Revision 25/04/2025 >
        btnlyout.addWidget(self._restart)
        btnlyout.addWidget(self._save)

        # Popup menu

        self._action = dict()
        self._action['copy'] = QAction('Copy', self)
        self._action['clear'] = QAction('Clear', self)
        self._action['restart'] = QAction('Restart', self)
        self._action['save'] = QAction('Save as HTML/XML...', self)
        self._action['mod'] = QAction('View modules', self)
        self._action['glob'] = QAction('View Globals', self)
        self._action['mod'].setCheckable(True)
        self._action['glob'].setCheckable(True)
        self._action['mod'].setChecked(True)
        self._action['glob'].setChecked(True)
        self._action['main'] = QAction('PySisyphe main window as \"main\"', self)
        # noinspection PyUnresolvedReferences
        self._action['copy'].triggered.connect(self.copy)
        # noinspection PyUnresolvedReferences
        self._action['clear'].triggered.connect(self.clear)
        # noinspection PyUnresolvedReferences
        self._action['restart'].triggered.connect(self.restart)
        # noinspection PyUnresolvedReferences
        self._action['save'].triggered.connect(self.save)
        # noinspection PyUnresolvedReferences
        self._action['mod'].toggled.connect(self.setModuleVisibility)
        # noinspection PyUnresolvedReferences
        self._action['glob'].toggled.connect(self.setGlobalsVisibility)
        # noinspection PyUnresolvedReferences
        self._action['main'].triggered.connect(self.importMain)

        self._popup = QMenu()
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._popup.addAction(self._action['copy'])
        self._popup.addAction(self._action['clear'])
        self._popup.addAction(self._action['restart'])
        self._popup.addAction(self._action['save'])
        self._popup.addSeparator()
        self._popup.addAction(self._action['mod'])
        self._popup.addAction(self._action['glob'])
        self._popup.addSeparator()
        self._menuImport = self._popup.addMenu('Import')
        self._menuImport.addAction(self._action['main'])
        self._menuImport.addSeparator()
        import Sisyphe
        for pkg in pkgutil.iter_modules([join(Sisyphe.__path__[0], 'core')]):
            if not pkg.ispkg and pkg.name != 'PySisyphe':
                cmd = 'from Sisyphe.core.{} import *'.format(pkg.name)
                action = QAction(pkg.name, self)
                # noinspection PyUnresolvedReferences
                action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
                self._menuImport.addAction(action)
        self._menuImport.addSeparator()
        # ANTs
        cmd = 'import ants'
        action = QAction('ANTs', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Matplotlib
        cmd = 'from matplotlib import pyplot as plt'
        action = QAction('Matplotlib', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # NiBabel
        cmd = 'import nibabel as nib'
        action = QAction('NiBabel', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Nilearn
        cmd = 'import nilearn as nil'
        action = QAction('Nilearn', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Numpy
        cmd = 'import numpy as np'
        action = QAction('Numpy', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Pandas
        cmd = 'import pandas as pd'
        action = QAction('Pandas', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Pillow
        cmd = 'import PIL as pil'
        action = QAction('Pillow', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # PyDicom
        cmd = 'import pydicom as dcm'
        action = QAction('PyDicom', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Scikit-image
        cmd = 'import skimage as ski'
        action = QAction('Scikit-image', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # SciPy
        cmd = 'import scipy as scp'
        action = QAction('SciPy', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # SimpleITK
        cmd = 'import SimpleITK as sitk'
        action = QAction('SimpleITK', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        self._popup.addMenu(self._menuImport)
        self._import.setMenu(self._menuImport)

        # Init layout

        lyout = QVBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(0)
        lyout.addWidget(splitter)
        lyout.addLayout(btnlyout)
        self.setLayout(lyout)
        self.update()
        self._console.executed.connect(self.update)

    # Private methods

    # < Revision 27/04/2026
    # add _enable_inline method
    def _enable_inline(self) -> None:
        # workaround for the exception raised by %matplotlib inline during a frozen execution
        # this bug is related to upgrading Matplotlib to version 3.10.8
        if sys.version_info.minor == 10:
            self._console.execute("import matplotlib\n"
                                  "import matplotlib.rcsetup as rcsetup\n"
                                  "\n"
                                  "def _no_validate_backend(s):\n"
                                  "    return s\n"
                                  "\n"
                                  "matplotlib.rcParams.validate['backend'] = _no_validate_backend\n"
                                  "import matplotlib_inline.backend_inline\n"
                                  "from IPython import get_ipython\n"
                                  "ip = get_ipython()\n"
                                  "if ip:\n"
                                  "    ip.run_line_magic('matplotlib', 'inline')\n", hidden=True)
        elif sys.version_info.minor == 12:
            # hook for inline display without inline backend
            self._console.execute("import matplotlib.pyplot as plt\n"
                                  "from IPython.display import display\n"
                                  "\n"
                                  "try:\n"
                                  "    from matplotlib_inline.backend_inline import configure_inline_support\n"
                                  "    from IPython import get_ipython\n"
                                  "    ip = get_ipython()\n"
                                  "    if ip:\n"
                                  "        configure_inline_support(ip, 'inline')\n"
                                  "except: pass\n"
                                  "\n"
                                  "def _inline_show(*args, **kwargs):\n"
                                  "    display(plt.gcf())\n"
                                  "\n"
                                  "plt.show = _inline_show\n", hidden=True)
    # Revision 27/04/2026 >

    # noinspection PyUnusedLocal
    def _globalsDblClicked(self, item: QTreeWidgetItem, c: int) -> None:
        if self.hasMainWindow():
            # noinspection PyUnresolvedReferences
            v = item.data(0, Qt.UserRole)
            if v != '':
                g = self._console.kernel_manager.kernel.shell.user_ns
                try:
                    if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                        if isinstance(g[v], SisypheVolume):
                            if not g[v].isEmpty():
                                self._vol = g[v].copy()
                                self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], sitkImage):
                            self._vol = SisypheVolume()
                            self._vol.copyFromSITKImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], ANTsImage):
                            self._vol = SisypheVolume()
                            self._vol.copyFromANTSImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], vtkImageData):
                            self._vol = SisypheVolume()
                            self._vol.copyFromVTKImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], ndarray):
                            if g[v].ndim == 3:
                                self._vol = SisypheVolume()
                                self._vol.copyFromNumpyArray(g[v])
                                self._mainwindow.addVolume(self._vol)
                except: return

    # noinspection PyUnusedLocal
    def _globalsClicked(self, item: QTreeWidgetItem, c: int) -> None:
        # noinspection PyUnresolvedReferences
        v = item.data(0, Qt.UserRole)
        if v != '':
            g = self._console.kernel_manager.kernel.shell.user_ns
            try:
                if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                    info = '{}:\n{}'.format('Double-click to open in PSisyphe', str(g[v]))
                    item.setToolTip(0, info)
                else:
                    info = str(g[v])
                    item.setToolTip(0, info)
            except: return

    # noinspection PyUnusedLocal
    def _modulesDblClicked(self, item: QTreeWidgetItem, c: int) -> None:
        if self.hasMainWindow():
            # noinspection PyUnresolvedReferences
            v = item.data(0, Qt.UserRole)
            if v != '':
                g = self._console.kernel_manager.kernel.shell.user_ns
                try:
                    module = g[v].__module__
                    if module[:12] == 'Sisyphe.core':
                        self._mainwindow.getDock().setCurrentIndex(5)
                        self._mainwindow.getHelp().setSearch(v)
                except: return

    # < Revision 01/12/2025
    # add _popupGlobals method
    # noinspection PyTypeChecker
    def _popupGlobals(self, p: QPoint) -> None:
        item = self._globals.itemAt(p)
        if item is not None:
            g = self._console.kernel_manager.kernel.shell.user_ns
            try:
                # noinspection PyUnresolvedReferences
                v = g[item.data(0, Qt.UserRole)]
                popup = QMenu()
                # noinspection PyUnresolvedReferences
                popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                popup.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                popup.setAttribute(Qt.WA_TranslucentBackground, True)
                actions = dict()
                actions['plot'] = QAction('Line plot')
                actions['bar'] = QAction('Bar plot')
                actions['stairs'] = QAction('Stairs plot')
                actions['box'] = QAction('Box-and-Whisker plot')
                actions['violin'] = QAction('Violin plot')
                actions['hist'] = QAction('Histogram plot')
                actions['scatter'] = QAction('Scatter plot')
                actions['mat'] = QAction('Matrix plot')
                actions['image'] = QAction('Image plot')
                actions['plot'].triggered.connect(lambda _: self._plot(0, item))
                actions['bar'].triggered.connect(lambda _: self._plot(1, item))
                actions['stairs'].triggered.connect(lambda _: self._plot(2, item))
                actions['box'].triggered.connect(lambda _: self._plot(3, item))
                actions['violin'].triggered.connect(lambda _: self._plot(4, item))
                actions['hist'].triggered.connect(lambda _: self._plot(5, item))
                actions['scatter'].triggered.connect(lambda _: self._plot(6, item))
                actions['mat'].triggered.connect(lambda _: self._plot(7, item))
                actions['image'].triggered.connect(lambda _: self._plot(8, item))
                # Revision 01/12/2025 >
                if isinstance(v, list):
                    v = array(v)
                    # < Revision 05/12/2025
                    if not issubdtype(v.dtype, number): return
                    # Revision 05/12/2025 >
                if isinstance(v, ndarray):
                    # < Revision 05/12/2025
                    if issubdtype(v.dtype, number):
                        # Revision 05/12/2025 >
                        if v.ndim < 3:
                            if v.ndim == 1:
                                popup.addAction(actions['plot'])
                                popup.addAction(actions['bar'])
                                popup.addAction(actions['stairs'])
                                popup.addAction(actions['box'])
                                popup.addAction(actions['violin'])
                                popup.addAction(actions['hist'])
                            elif v.ndim == 2:
                                if 2 in v.shape:
                                    popup.addAction(actions['plot'])
                                    popup.addAction(actions['bar'])
                                    popup.addAction(actions['stairs'])
                                    popup.addAction(actions['box'])
                                    popup.addAction(actions['violin'])
                                    popup.addAction(actions['hist'])
                                    popup.addAction(actions['scatter'])
                                else:
                                    popup.addAction(actions['plot'])
                                    popup.addAction(actions['bar'])
                                    popup.addAction(actions['stairs'])
                                    popup.addAction(actions['box'])
                                    popup.addAction(actions['violin'])
                                    popup.addAction(actions['hist'])
                                    popup.addAction(actions['mat'])
                                    popup.addAction(actions['image'])
                            popup.exec(self._globals.mapToGlobal(p))
                elif isinstance(v, sitkImage):
                    if v.GetDimension() == 2:
                        popup.addAction(actions['image'])
                        popup.exec(self._globals.mapToGlobal(p))
                # < Revision 09/12/2025
                elif isinstance(v, pilImage):
                    popup.addAction(actions['image'])
                    popup.exec(self._globals.mapToGlobal(p))
                # Revision 09/12/2025 >
            except: pass
    # Revision 01/12/2025 >

    # < Revision 01/12/2025
    # add _plot method
    def _plot(self, chart: int, item: QTreeWidgetItem) -> None:
        g = self._console.kernel_manager.kernel.shell.user_ns
        try:
            # noinspection PyUnresolvedReferences
            vstr = item.data(0, Qt.UserRole)
            v = g[vstr]
            if isinstance(v, (list, ndarray, sitkImage, pilImage)):
                if isinstance(v, list): ndim = 1
                elif isinstance(v, ndarray): ndim = v.ndim
                elif isinstance(v, sitkImage): ndim = v.GetDimension()
                elif isinstance(v, pilImage): ndim = 2
                else: ndim = 1
                if ndim in (1, 2):
                    self._console.execute('import numpy as np', hidden=True)
                    self._console.execute('import matplotlib.pyplot as plt', hidden=True)
                    #
                    # Line plot
                    #
                    if chart == 0:
                        dialog = DialogFromXml('Line plot settings', 'LinePlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            mk = settings['marker'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if ndim == 1: buff = 'r = ax.plot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.plot(np.array({}).T, '.format(vstr)
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={}, '.format(float(settings['linewidth']))
                            buff += 'marker=\'{}\', '.format(mk)
                            buff += 'ms={})'.format(float(settings['markersize']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['raxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Bar plot
                    #
                    elif chart == 1:
                        dialog = DialogFromXml('Bar plot settings', 'BarPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if ndim == 1: buff = 'r = plt.bar(range(len({0})), np.array({0}), '.format(vstr)
                            else: buff = 'r = plt.bar(range({0}.shape[1]), np.array({0}).T, '.format(vstr)
                            buff += 'width={}, '.format(float(settings['barwidth']))
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={})'.format(float(settings['linewidth']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Stairs plot
                    #
                    elif chart == 2:
                        dialog = DialogFromXml('Stairs plot settings', 'StairsPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if ndim == 1: buff = 'r = plt.stairs(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.stairs(np.array({}).T, '.format(vstr)
                            buff += 'fill={}, '.format(str(settings['fill']))
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={})'.format(float(settings['linewidth']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Box-and-Whisker plot
                    #
                    elif chart == 3:
                        dialog = DialogFromXml('Box & Whisker plot settings', 'WhiskerPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            sym = settings['symbol'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if ndim == 1: buff = 'r = plt.boxplot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.boxplot(np.array({}).T, '.format(vstr)
                            buff += 'notch={}, '.format(str(settings['notch']))
                            buff += 'sym=\'{}\', '.format(sym)
                            buff += 'widths={}, '.format(float(settings['boxwidth']))
                            buff += 'showcaps={}, '.format(str(settings['showcaps']))
                            buff += 'showbox={}, '.format(str(settings['showbox']))
                            buff += 'showfliers={}, '.format(str(settings['showfliers']))
                            buff += 'showmeans={})'.format(str(settings['showmeans']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Violin plot
                    #
                    elif chart == 4:
                        dialog = DialogFromXml('Violin plot settings', 'ViolinPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if ndim == 1: buff = 'r = plt.violinplot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.violinplot(np.array({}).T, '.format(vstr)
                            buff += 'widths={}, '.format(float(settings['boxwidth']))
                            buff += 'showmeans={}, '.format(str(settings['showmeans']))
                            buff += 'showextrema={}, '.format(str(settings['showextrema']))
                            buff += 'showmedians={})'.format(str(settings['showmedians']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Histogram plot
                    #
                    elif chart == 5:
                        dialog = DialogFromXml('Histogram plot settings', 'HistPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if ndim == 1: buff = 'r = plt.hist(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.hist(np.array({}).T, '.format(vstr)
                            buff += 'cumulative={}, '.format(str(settings['cumulative']))
                            buff += 'histtype=\'{}\')'.format(settings['histtype'][0])
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Scatter plot
                    #
                    elif chart == 6:
                        dialog = DialogFromXml('Scatter plot settings', 'ScatterPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            mk = settings['marker'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if v.shape[0] == 2: self._console.execute('buff = np.array({})'.format(vstr), hidden=True)
                            elif v.shape[1] == 2: self._console.execute('buff = np.array({}).T'.format(vstr), hidden=True)
                            else: return
                            buff = 'r = ax.scatter(buff[0], buff[1], '
                            buff += 'marker=\'{}\')'.format(mk)
                            # buff += 'ms={})'.format(float(settings['markersize']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('del buff', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Matrix plot
                    #
                    elif chart == 7:
                        dialog = DialogFromXml('Matrix plot settings', 'MatrixPlot')
                        dialog.getFieldsWidget().getParameterWidget('cmap').removeFilesLut()
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            cmap = SisypheLut.getInternalColormapFromName(settings['cmap'])
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            buff = 'r = ax.matshow(np.array({}), '.format(vstr)
                            buff += 'cmap=\'{}\')'.format(cmap)
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            if settings['colorbar']:
                                self._console.execute('from mpl_toolkits.axes_grid1 import make_axes_locatable', hidden=True)
                                self._console.execute('d = make_axes_locatable(ax)', hidden=True)
                                self._console.execute('cax = d.append_axes(\'right\', size=\'5%\', pad=0.05)', hidden=True)
                                self._console.execute('fig.colorbar(r, cax=cax, orientation=\'vertical\')', hidden=True)
                                self._console.execute('del d', hidden=True)
                                self._console.execute('del cax', hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Image plot
                    #
                    elif chart == 8:
                        dialog = DialogFromXml('Image plot settings', 'ImagePlot')
                        dialog.getFieldsWidget().getParameterWidget('cmap').removeFilesLut()
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            cmap = SisypheLut.getInternalColormapFromName(settings['cmap'])
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            if isinstance(v, sitkImage):
                                self._console.execute('from SimpleITK import GetArrayFromImage', hidden=True)
                                self._console.execute('buff = GetArrayFromImage({})'.format(vstr), hidden=True)
                            elif isinstance(v, pilImage):
                                self._console.execute('from PIL.Image import Transpose', hidden=True)
                                self._console.execute('buff = {}.convert(\'L\')'.format(vstr), hidden=True)
                                self._console.execute('buff = np.array(buff.transpose(Transpose.ROTATE_180))', hidden=True)
                                self._console.execute('del Transpose', hidden=True)
                            elif isinstance(v, list):
                                self._console.execute('buff = np.array({}), '.format(vstr), hidden=True)
                            if isinstance(v, ndarray): buff = 'r = ax.imshow(np.fliplr({}.T), origin=\'lower\', '.format(vstr)
                            else: buff = 'r = ax.imshow(np.fliplr(buff), origin=\'lower\', '
                            buff += 'cmap=\'{}\')'.format(cmap)
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible(False)', hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible(False)', hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            if settings['colorbar']:
                                self._console.execute('from mpl_toolkits.axes_grid1 import make_axes_locatable', hidden=True)
                                self._console.execute('d = make_axes_locatable(ax)', hidden=True)
                                self._console.execute('cax = d.append_axes(\'right\', size=\'5%\', pad=0.05)', hidden=True)
                                self._console.execute('fig.colorbar(r, cax=cax, orientation=\'vertical\')', hidden=True)
                                self._console.execute('del d', hidden=True)
                                self._console.execute('del cax', hidden=True)
                            if not isinstance(v, ndarray):
                                self._console.execute('del buff', hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
        except: pass
    # Revision 01/12/2025 >

    def update(self) -> None:
        self._modules.clear()
        self._globals.clear()
        g = self._console.kernel_manager.kernel.shell.user_ns
        k = g.keys()
        for v in k:
            if v[0] == '_': continue
            elif v in ['In', 'Out', 'get_ipython', 'exit', 'quit']: continue
            elif type(g[v]) == type:
                rep = str(g[v])
                item = QTreeWidgetItem()
                item.setText(0, rep)
                info = '{}:\n{}'.format(v, g[v].__doc__)
                item.setToolTip(0, info)
                # noinspection PyUnresolvedReferences
                item.setData(0, Qt.UserRole, v)
                self._modules.addTopLevelItem(item)
            elif isinstance(g[v], (types.ModuleType, types.FunctionType)):
                rep = str(g[v])
                item = QTreeWidgetItem()
                item.setText(0, rep)
                info = '{}:\n{}'.format(v, g[v].__doc__)
                item.setToolTip(0, info)
                self._modules.addTopLevelItem(item)
            else:
                item = QTreeWidgetItem()
                item.setText(0, '{} ({})'.format(v, type(g[v])))
                if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                    # noinspection PyUnresolvedReferences
                    item.setData(0, Qt.UserRole, v)
                    rep = '{}:\n{}'.format('Double-click to open in PSisyphe', str(g[v]))
                else:
                    # noinspection PyUnresolvedReferences
                    item.setData(0, Qt.UserRole, v)
                    rep = str(g[v])
                item.setToolTip(0, rep)
                self._globals.addTopLevelItem(item)
        
    # Public methods

    def setModuleVisibility(self, v: bool = True) -> None:
        self._modules.setVisible(v)

    def getModuleVisibility(self) -> bool:
        return self._modules.isVisible()

    def setGlobalsVisibility(self, v: bool = True) -> None:
        self._globals.setVisible(v)

    def getGlobalsVisibility(self) -> bool:
        return self._globals.isVisible()

    def getPopup(self) -> QMenu:
        return self._popup

    def pushVariables(self, v: dict[str, Any]) -> None:
        if v is not None:
            if isinstance(v, dict):
                self._console.kernel_manager.kernel.shell.push(v)
            else: raise TypeError('parameter type {} is not dict.'.format(type(v)))

    # < Revision 29/11/2025
    # add hasVariable method
    def hasVariable(self, v: str) -> bool:
        """
        Check if a variable exists in the console.

        Parameters
        ----------
        v : str
            variable name to check.

        Returns
        -------
        bool
            True if the variable exists in the console, False otherwise.
        """
        g = self._console.kernel_manager.kernel.shell.user_ns
        k = g.keys()
        return v in k
    # Revision 29/11/2025 >

    def clear(self) -> None:
        self._console.clear()

    def copy(self) -> None:
        self._console.copy()

    def restart(self) -> None:
        self._console.reset(clear=True)
        self.pushVariables(self._variables)

        # < Revision 27/04/2026
        # workaround for the exception raised by %matplotlib inline during a frozen execution
        # this bug is related to upgrading Matplotlib to version 3.10.8
        try:
            if hasattr(sys, '_MEIPASS'):
                self._console.execute("import matplotlib; matplotlib.use('QtAgg')", hidden=True)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, self._enable_inline)
            else: self._console.execute('%matplotlib inline', hidden=True)
        except: pass
        # Revision 27/04/2026 >

        self.update()

    def save(self) -> None:
        try: self._console.export_html()
        except Exception as err: messageBox(self,
                                            'Save console display to HTML/XML.',
                                            text='error : {}'.format(err))

    def importMain(self) -> None:
        if self._mainwindow is not None:
            v = {'main': self._mainwindow}
            self.pushVariables(v)
            self.update()

    def setFont(self, font: QFont) -> None:
        # noinspection PyProtectedMember
        self._console._set_font(font)

    def setMainWindow(self, w: WindowSisyphe) -> None:
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): self._mainwindow = w
        else: raise TypeError('parameter type {} is not WindowSisyphe.'.format(type(w)))

    def getMainWindow(self) -> WindowSisyphe:
        return self._mainwindow

    def hasMainWindow(self) -> bool:
        return self._mainwindow is not None

    # Qt event

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.Copy): self.copy()
