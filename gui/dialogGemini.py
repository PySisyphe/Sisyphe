"""
External packages/modules
-------------------------

    - google-genai, gemini LLM API, https://googleapis.github.io/python-genai/
    - Numpy, Scientific computing, https://numpy.org/
    - Pillow,  image processing, https://pillow.readthedocs.io/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sys import platform

from os import mkdir
from os import getcwd

from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename

# < Revision 14/12/2025
try:
    from google import genai
    from google.genai.errors import APIError
except: pass
# Revision 14/12/2025 >

import json

from numpy import array
from numpy import ndarray

from xml.dom import minidom

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROIDraw
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheTools import HandleWidget
from Sisyphe.core.sisypheTools import ToolWidgetCollection
from Sisyphe.core.sisypheSettings import getUserPySisyphePath
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.widgets.consoleWidget import ConsoleWidget
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.gui.dialogWait import DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection

__all__ = ['DialogGemini']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogGemini
"""

class DialogGemini(QDialog):
    """
    DialogGemini

    Description
    ~~~~~~~~~~~

    GUI dialog window, gemini LLM prompt.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogGemini

    Creation: 10/12/2025
    Last revision: 12/12/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Gemini prompt')
        # noinspection PyTypeChecker,PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        # Attributes

        self._ID: str | None = None
        self._slcindex: int = 0
        self._slcorient: int = 0
        self._roi: SisypheROIDraw | None = None
        self._volume: SisypheVolume | None = None
        self._mask: ndarray | None = None
        self._console: ConsoleWidget | None = None
        self._hprompt: dict[str, str] = dict()
        self._views: IconBarViewWidgetCollection | None = None
        self._hprompt['text'] = ('\nDo not send any segmentation masks.'
                                 '\nThe JSON output must not contain a \"mask\" key.')
        self._hprompt['bbox'] = ('\nThe JSON output must contain a bounding box for the recognized object in the key \"bbox\".'
                                 '\nThe bounding box should be [xmin, ymin, xmax, ymax] normalized to 0-1000.'
                                 '\nDo not include any explanation, comments, or additional text.')
        self._hprompt['contour'] = ('\nSegment the recognized object precisely and extract the coordinates of the points defining its outer boundary (contour).'
                                    '\nReturn the result as an ordered list of 2D points representing the object\'s boundary.'
                                    '\nEach point coordinates should be [x, y] normalized to 0-1000.'
                                    '\nThe points should follow the contour in a consistent direction (clockwise or counterclockwise).'
                                    '\nDo not include any explanation, comments, or additional text.'
                                    '\nOutput only the list of coordinates in JSON format in the key \"contour\"')
        self._hprompt['points'] = ('\nThe point coordinates should be [x, y] normalized to 0-1000.'
                                   '\nDo not include any explanation, comments, or additional text.'
                                   '\nOutput only the list of points in JSON format in the key \"points\"')
        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        label1 = QLabel('Prompt')
        self._prompt = QPlainTextEdit()
        self._response = QPlainTextEdit()
        self._response.setReadOnly(True)
        self._response.setVisible(False)

        lyout1 = QHBoxLayout()
        if platform == 'win32': lyout1.setContentsMargins(10, 10, 10, 10)
        lyout1.setSpacing(10)
        # noinspection PyUnresolvedReferences
        lyout1.setDirection(QHBoxLayout.RightToLeft)
        self._btLoadPrompt = QPushButton('Load')
        self._btSavePrompt = QPushButton('Save')
        self._btClearPrompt = QPushButton('Clear')
        self._btSpacingPrompt = QPushButton('Add spacing')
        self._btSpacingPrompt.setToolTip('Add pixel dimension in mm of the current slice in the prompt.')
        self._btSend = QPushButton('Send')
        lyout1.addWidget(self._btSend)
        lyout1.addStretch()
        lyout1.addWidget(self._btSpacingPrompt)
        lyout1.addWidget(self._btClearPrompt)
        lyout1.addWidget(self._btSavePrompt)
        lyout1.addWidget(self._btLoadPrompt)

        lyout2 = QHBoxLayout()
        if platform == 'win32': lyout1.setContentsMargins(10, 10, 10, 10)
        lyout2.setSpacing(10)
        # noinspection PyUnresolvedReferences
        lyout2.setDirection(QHBoxLayout.RightToLeft)
        self._btText = QRadioButton('Text')
        self._btBox = QRadioButton('Bounding box')
        self._btContour = QRadioButton('Contour')
        self._btPoints = QRadioButton('Points')
        self._btText.setToolTip('Add the following text to the prompt:{}'.format(self._hprompt['text']))
        self._btBox.setToolTip('Add the following text to the prompt:{}'.format(self._hprompt['bbox']))
        self._btContour.setToolTip('Add the following text to the prompt:{}'.format(self._hprompt['contour']))
        self._btPoints.setToolTip('Add the following text to the prompt:{}'.format(self._hprompt['points']))
        self._btText.setChecked(True)
        lyout2.addStretch()
        lyout2.addWidget(self._btPoints)
        lyout2.addWidget(self._btContour)
        lyout2.addWidget(self._btBox)
        lyout2.addWidget(self._btText)
        lyout2.addWidget(QLabel('Response'))
        lyout2.addStretch()

        lyout3 = QHBoxLayout()
        if platform == 'win32': lyout3.setContentsMargins(10, 10, 10, 10)
        lyout3.setSpacing(10)
        # noinspection PyUnresolvedReferences
        lyout3.setDirection(QHBoxLayout.RightToLeft)
        self._btSaveReply = QPushButton('Save')
        self._btConsole = QPushButton('Copy to console')
        self._btSaveReply.setVisible(False)
        self._btConsole.setVisible(False)
        lyout3.addWidget(self._btConsole)
        lyout3.addWidget(self._btSaveReply)
        lyout3.addStretch()

        self._tokens = QLabel()
        self._tokens.setVisible(False)

        self._layout.addWidget(label1)
        self._layout.addWidget(self._prompt)
        self._layout.addLayout(lyout1)
        self._layout.addLayout(lyout2)
        self._layout.addWidget(self._tokens)
        self._layout.addWidget(self._response)
        self._layout.addLayout(lyout3)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('Close')
        self._ok.setFixedWidth(100)
        layout.addWidget(self._ok)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._btLoadPrompt.clicked.connect(lambda _: self.loadPrompt())
        # noinspection PyUnresolvedReferences
        self._btSavePrompt.clicked.connect(lambda _: self.savePrompt())
        # noinspection PyUnresolvedReferences
        self._btClearPrompt.clicked.connect(self.clearPrompt)
        # noinspection PyUnresolvedReferences
        self._btSpacingPrompt.clicked.connect(self.setSpacingToPrompt)
        # noinspection PyUnresolvedReferences
        self._btSend.clicked.connect(self._send)
        # noinspection PyUnresolvedReferences
        self._btSaveReply.clicked.connect(lambda _: self.saveTextReply())
        # noinspection PyUnresolvedReferences
        self._btConsole.clicked.connect(self.copyResponseToConsole)

    # Private method

    def _send(self):
        self.send()

    @classmethod
    def _parsejson(cls, output: str) -> str:
        lines = output.splitlines()
        for i, line in enumerate(lines):
            if line == '```json':
                json_output = '\n'.join(lines[i + 1:])
                output = json_output.split('```')[0]
                break
        return output

    # Public methods

    def loadPrompt(self, filename: str = ''):
        if filename == '' or not exists(filename):
            folder = join(getUserPySisyphePath(), 'prompts')
            if not exists(folder): mkdir(folder)
            filename = QFileDialog.getOpenFileName(self,
                                                   'Select XML request file',
                                                   folder,
                                                   '*.xml')
            QApplication.processEvents()
            filename = filename[0]
        if exists(filename):
            try: doc = minidom.parse(filename)
            except:
                messageBox(self,
                           'Load gemini prompt',
                           text='{} XML file read error.'.format(filename))
                return
            root = doc.documentElement
            if root.nodeName == 'request' and root.getAttribute('version') == '1.0':
                node = root.firstChild
                while node:
                    # prompt
                    if node.nodeName == 'prompt':
                        buff = node.firstChild.data
                        if buff is not None: self._prompt.setPlainText(buff)
                    # output
                    elif node.nodeName == 'output':
                        buff = node.firstChild.data
                        self._btText.setChecked(True)
                        if buff is not None:
                            if buff == 'text': self._btText.setChecked(True)
                            elif buff == 'bbox': self._btBox.setChecked(True)
                            elif buff == 'contour': self._btContour.setChecked(True)
                            elif buff == 'points': self._btPoints.setChecked(True)
                    node = node.nextSibling
            else:
                messageBox(self,
                           'Load gemini prompt',
                           text='{} is not a valid gemini prompt file.'.format(filename))

    def savePrompt(self, filename: str = ''):
        if filename == '':
            folder = join(getUserPySisyphePath(), 'prompts')
            if not exists(folder): mkdir(folder)
            filename = QFileDialog.getSaveFileName(self,
                                                   'Save XML request file',
                                                   folder,
                                                   '*.xml')
            QApplication.processEvents()
            filename = filename[0]
        if filename:
            path, ext = splitext(filename)
            if ext.lower() != '.xml':
                filename = path + '.xml'
            doc = minidom.Document()
            root = doc.createElement('request')
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            # prompt
            node = doc.createElement('prompt')
            root.appendChild(node)
            txt = doc.createTextNode(self._prompt.toPlainText())
            node.appendChild(txt)
            # input
            node = doc.createElement('input')
            root.appendChild(node)
            txt = doc.createTextNode('image')
            node.appendChild(txt)
            # input
            node = doc.createElement('output')
            root.appendChild(node)
            if self._btText.isChecked(): txt = doc.createTextNode('text')
            elif self._btBox.isChecked(): txt = doc.createTextNode('bbox')
            elif self._btContour.isChecked(): txt = doc.createTextNode('contour')
            elif self._btPoints.isChecked(): txt = doc.createTextNode('points')
            else: txt = doc.createTextNode('text')
            node.appendChild(txt)
            # write XML file
            buff = doc.toprettyxml()
            f = open(filename, 'w')
            try: f.write(buff)
            except IOError:
                messageBox(self,
                           'Save gemini prompt',
                           text='{} XML file write error.'.format(basename(filename)))
            finally: f.close()

    def send(self) -> bool:
        prompt = self._prompt.toPlainText()
        if prompt != '':
            self._btSend.setEnabled(False)
            settings = SisypheSettings()
            aikey = settings.getFieldValue('Gemini', 'APIKey')
            aimodel = settings.getFieldValue('Gemini', 'Model')
            if aikey is None or aikey == '':
                messageBox(self,
                           self.windowTitle(),
                           'There is no Gemini API key declared.')
                return False
            if aimodel is None or aimodel == '':
                messageBox(self,
                           self.windowTitle(),
                           'There is no Gemini model declared.')
                return False
            client = genai.Client(api_key=aikey)
            config = genai.types.GenerateContentConfig(response_mime_type='application/json',
                                                       max_output_tokens=65536)
            slc = self._volume.copyToPillowImage(slc=self._slcindex,
                                                 orient=self._slcorient,
                                                 rgb=True)
            if self._btText.isChecked(): prompt += self._hprompt['text']
            elif self._btBox.isChecked():  prompt += self._hprompt['bbox']
            elif self._btContour.isChecked(): prompt += self._hprompt['contour']
            elif self._btPoints.isChecked(): prompt += self._hprompt['points']
            content = [slc, prompt]
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Waiting for gemini response...')
            try:
                r = client.models.generate_content(model=aimodel,
                                                   contents=content,
                                                   config=config)
            except APIError as e:
                wait.close()
                messageBox(self,
                           self.windowTitle(),
                           'Gemini error {}: {}.'.format(e.code, e.message))
                return False
            rdict = r.to_json_dict()
            rtxt = ''
            ptokens = 0
            ttokens = 0
            try:
                if 'candidates' in rdict:
                    if 'content' in rdict['candidates'][0]:
                        if 'parts' in rdict['candidates'][0]['content']:
                            if 'text' in  rdict['candidates'][0]['content']['parts'][0]:
                                rtxt = rdict['candidates'][0]['content']['parts'][0]['text']
            except: pass
            if 'usage_metadata' in rdict:
                if 'prompt_token_count' in rdict['usage_metadata']: ptokens = int(rdict['usage_metadata']['prompt_token_count'])
                if 'total_token_count' in rdict['usage_metadata']: ttokens = int(rdict['usage_metadata']['total_token_count'])
            self._tokens.setText('Prompt tokens {}, total tokens {}'.format(ptokens, ttokens))
            self._tokens.setVisible(True)
            if isinstance(rtxt, str) and rtxt != '':
                self._response.setPlainText(rtxt)
                self._response.setVisible(True)
                self._btSaveReply.setVisible(True)
                self._btConsole.setVisible(True)
                self.adjustSize()
                sx, sy, sz = self._volume.getSize()
                items = json.loads(rtxt)
                if 'bbox' in items:
                    if len(items['bbox']) > 0:
                        pts = array(items['bbox']).reshape([2, 2])
                        if self._slcorient == 0:
                            pts = pts * array([sx / 1000, sy / 1000])
                            pts = pts.flatten()
                            p = (int(pts[0]), int(pts[1]), self._slcindex)
                        elif self._slcorient == 1:
                            pts = pts * array([sx / 1000, sz / 1000])
                            pts = pts.flatten()
                            p = (int(pts[0]), self._slcindex, int(pts[1]))
                        else:
                            pts = pts * array([sy / 1000, sz / 1000])
                            pts = pts.flatten()
                            p = (self._slcindex, int(pts[0]), int(pts[1]))
                        e = (int(pts[2] - pts[0]), int(pts[3] - pts[1]))
                        self._roi.drawRectangle(p, e, self._slcorient)
                        if self._views is not None: self._views.updateROIDisplay()
                    else:
                        messageBox(self,
                                   self.windowTitle(),
                                   'There is no bounding box in the Gemini response.')
                elif 'contour' in items:
                    if len(items['contour']) > 0:
                        if self._slcorient == 0: pts = array(items['contour']) * array([sx/1000, sy/1000])
                        elif self._slcorient == 1: pts = array(items['contour']) * array([sx/1000, sz/1000])
                        else: pts = array(items['contour']) * array([sy/1000, sz/1000])
                        self._roi.drawFilledPolygon(list(pts.astype('uint16')), self._slcorient, self._slcindex)
                        if self._views is not None: self._views.updateROIDisplay()
                    else:
                        messageBox(self,
                                   self.windowTitle(),
                                   'There is no contour in the Gemini response.')
                elif 'points' in items:
                    if len(items['points']) > 0:
                        if self._slcorient == 0: pts = array(items['points']) * array([sx/1000, sy/1000])
                        elif self._slcorient == 1: pts = array(items['points']) * array([sx/1000, sz/1000])
                        else: pts = array(items['points']) * array([sy/1000, sz/1000])
                        tools = ToolWidgetCollection()
                        for i in range(pts.shape[0]):
                            p = pts[i, :]
                            if self._slcorient == 0: p = (p[0], p[1], self._slcindex)
                            elif self._slcorient == 1: p = (p[0], self._slcindex, p[1])
                            else: p = (self._slcindex, p[0], p[1])
                            tool = HandleWidget('#{}'.format(i), '')
                            tool.setPosition(p)
                            tool.setSphereRadius(2.0)
                            tool.setHandleSize(5.0)
                            tool.setTextOffset((10, -10))
                            tool.setLegend('')
                            tool.setFontSize(10)
                            tools.append(tool)
                        buff = self._volume.getFilename()
                        self._volume.setFilenameSuffix('points')
                        tools.setReferenceID(self._volume)
                        tools.setPurpose('gemini')
                        tools.saveAs(self._volume.getFilename())
                        messageBox(self,
                                   self.windowTitle(),
                                   'Points are saved as target tools in {}'.format(tools.getFilename()))
                        self._volume.setFilename(buff)
                    else:
                        messageBox(self,
                                   self.windowTitle(),
                                   'There is no point in the Gemini response.')
                return False
            else:
                wait.close()
                messageBox(self,
                           self.windowTitle(),
                           'Gemini error, no response text.')
                return False
        else:
            messageBox(self,
                       self.windowTitle(),
                       'Gemini prompt is empty.')
            return False

    def saveTextReply(self, filename: str = ''):
        if filename == '':
            filename = QFileDialog.getSaveFileName(self,
                                                   'Save XML request file',
                                                   getcwd(),
                                                   '*.xml (XML request)')
            QApplication.processEvents()
            filename = filename[0]
        if filename:
            path, ext = splitext(filename)
            if ext.lower() != '.txt':
                filename = path + '.txt'
            f = open(filename, 'w')
            try: f.write(self._response.toPlainText())
            except IOError:
                messageBox(self,
                           'Save gemini response',
                           text='{} file write error.'.format(basename(filename)))
            finally: f.close()

    def getTextReply(self) -> str:
        return self._response.toPlainText()

    def hasTextReply(self) -> bool:
        return self._response.toPlainText() != ''

    def setROIDraw(self, roi: SisypheROIDraw,
                   index: int | None = 0,
                   orient: int = 0,
                   views: IconBarViewWidgetCollection | None = None) -> None:
        if index is not None:
            if self._ID is None: self._ID = roi.getROI().getReferenceID()
            if roi.getROI().getReferenceID() == self._ID:
                self._roi = roi
                self._slcindex = index
                self._slcorient = orient
                self._views = views
            else: raise ValueError('{} ID mismatch.'.format(basename(roi.getROI().getFilename())))
        else:
            messageBox(self,
                       self.windowTitle(),
                       'No slice is selected.')

    def getSliceIndex(self) -> int:
        return self._slcindex

    def getSliceOrient(self) -> int:
        return self._slcorient

    def getROIDraw(self) -> SisypheROIDraw:
        return self._roi

    def setReferenceVolume(self, v: SisypheVolume) -> None:
        if self._ID is None: self._ID = v.getID()
        if v.getID() == self._ID: self._volume = v
        else: raise ValueError('{} ID mismatch.'.format(v.getBasename()))

    def getReferenceVolume(self) -> SisypheVolume:
        return self._volume

    def clear(self) -> None:
        self._volume = None
        self._roi = None
        self._ID = None
        self._slcindex = 0
        self._slcorient = 0
        self._prompt.clear()
        self._response.clear()
        self._tokens.setVisible(False)
        self._response.setVisible(False)
        self._btSaveReply.setVisible(False)
        self._btConsole.setVisible(False)
        self._btSend.setEnabled(True)

    def clearPrompt(self) -> None:
        self._prompt.clear()
        self._response.clear()
        self._tokens.setVisible(False)
        self._response.setVisible(False)
        self._btSaveReply.setVisible(False)
        self._btConsole.setVisible(False)
        self._btSend.setEnabled(True)
        self.adjustSize()

    def setConsoleWidget(self, w: ConsoleWidget):
        self._console = w

    def getConsoleWidget(self) -> ConsoleWidget:
        return self._console

    def setSpacingToPrompt(self) -> None:
        if self._volume is not None:
            if self._slcorient == 0:
                self._prompt.textCursor().insertText('\nThe image size is {0[0]} pixels '
                                                     'on the x-axis and {0[1]} pixels on the y-axis.\n'.format(self._volume.getSize()))
                self._prompt.textCursor().insertText('The pixel spacing in the image is {0[0]} mm '
                                                     'on the x-axis and {0[1]} mm on the y-axis.\n'.format(self._volume.getSpacing()))
            elif self._slcorient == 1:
                self._prompt.textCursor().insertText('\nThe image size is {0[0]} pixels '
                                                     'on the x-axis and {0[1]} pixels on the y-axis.\n'.format(self._volume.getSize()))
                self._prompt.textCursor().insertText('The pixel spacing in the image is {0[0]} mm '
                                                     'on the x-axis and {0[2]} on the y-axis.\n'.format(self._volume.getSpacing()))
            else:
                self._prompt.textCursor().insertText('\nThe image size is {0[0]} pixels '
                                                     'on the x-axis and {0[1]} pixels on the y-axis.\n'.format(self._volume.getSize()))
                self._prompt.textCursor().insertText('The pixel spacing in the image is {0[1]} mm '
                                                     'on the x-axis and {0[2]} on the y-axis.\n'.format(self._volume.getSpacing()))

    def copyResponseToConsole(self) -> None:
        if self._console is not None:
            txt = self._response.toPlainText()
            if txt != '':
                try: obj = json.loads(txt)
                except: obj = txt
                self._console.pushVariables({'jsonr': obj})
                self._console.update()
                messageBox(self,
                           self.windowTitle(),
                           'The Gemini response was copied to the console under the variable name \'jsonr\'.')