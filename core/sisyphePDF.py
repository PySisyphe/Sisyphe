"""
External packages/modules
-------------------------

    - easyocr, OCR, https://github.com/JaidedAI/EasyOCR
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - pymupdf, PDF processing, https://pymupdf.readthedocs.io/
"""

from os.path import exists
from os.path import basename
from os.path import splitext

from xml.dom import minidom

try: import easyocr
except: pass

import pymupdf

from pandas import DataFrame

from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['SisypheParsePdf']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - object -> SisypheParsePdf
"""

class SisypheParsePdf(object):
    """
    Description
    ~~~~~~~~~~~

    This class performs OCR processing on PDF files.

    - OCR processing to extract all strings from the PDF,
    - search table fields (table column header),
    - extract table field values.

    Inheritance
    ~~~~~~~~~~~

    object -> SisypheParsePdf

    Creation: 15/12/2025
    Last revision: 10/01/2026
    """

    __slots__ = ['_fields', '_exclude', '_types']

    # class method

    @classmethod
    def detect(cls, filename: str) -> list[tuple[list[list[float]], str, float]]:
        """
        Extract all strings from a PDF.

        Parameters
        ----------
        filename : str
            PDF filename

        Returns
        -------
        list[tuple[list[list[float]], str, float]]
            One tuple for each string extracted from the PDF:

                - list[list[float]], four corners of the detected string's bounding box.
                - str, dtected string.
                - float, confidence level in percent of OCR.
        """
        if splitext(filename)[1].lower() == '.pdf':
            if exists(filename):
                reader = easyocr.Reader(['en'])
                pdf = pymupdf.open(filename)
                r2 = list()
                for i in range(pdf.page_count):
                    png = splitext(filename)[0] + '{}.png'.format(i)
                    if not exists(png):
                        pixmap = pdf[i].get_pixmap(dpi=300)
                        img = pixmap.pil_image()
                        img.save(png)
                    r = reader.readtext(png)
                    if isinstance(r, list): r2 += r
                return r2
            else: raise IOError('No such file {}.'.format(filename))
        else: raise ValueError('{} is not a PDF file.'.format(basename(filename)))

    @classmethod
    def hasField(cls,
                 extracted: list[tuple[list[list[float]], str, float]],
                 fieldname: str) -> bool:
        """
        Check if a string was extracted from a PDF.

        Parameters
        ----------
        extracted : list[tuple[list[list[float]], str, float]]
            list of extracted strings from the PDF, processed with the detect() method.
        fieldname : str
            string to search in the PDF.

        Returns
        -------
        bool
            True if the string was extracted from the PDF.
        """
        for field in extracted:
            if fieldname in field[1]: return True
        return False

    @classmethod
    def hasFields(cls,
                  extracted: list[tuple[list[list[float]], str, float]],
                  fieldnames: list[str]) -> dict[str, tuple[bool, list[int]]]:
        """
        Check if a list of strings was extracted from a PDF.

        Parameters
        ----------
        extracted : list[tuple[list[list[float]], str, float]]
            list of extracted strings from the PDF, processed with the detect() method.
        fieldnames : list[str]
            list of strings to search in the PDF.

        Returns
        -------
        dict[str, tuple[bool, list[int]]]

            - keys are strings to search
            - items are tuples of a bool, True if the current key string is extracted from the PDF; an index list
            of the current key string within the extracted list.
        """
        r = dict()
        for k in fieldnames:
            r[k] = (False, list())
        for field in extracted:
            for i, sub in enumerate(fieldnames):
                # < Revision 10/01/2026
                tag = False
                idx = list()
                if sub in field[1]:
                    # if r[sub][0] is False: r[sub][0] = True
                    # r[sub][1].append(i)
                    if not tag: tag = True
                    idx.append(i)
                if tag: r[sub] = (tag, idx)
                # Revision 10/01/2026 >
        return r

    # Special methods

    def __init__(self) -> None:
        """
        SisypheParsePdf instance constructor.
        """
        self._fields: list[str] | None = None
        self._types: list[str] | None = None
        self._exclude: list[str] | None = None

    # Public methods

    def parse(self, filename: str, wait: DialogWait | None = None) -> tuple[DataFrame, list]:
        """
        PDF parsing:

        - OCR processing to extract all strings from the PDF
        - search table fields (table column header)
        - extract table field values

        Parameters
        ----------
        filename : str
            PDF file to parse.
        wait : DialogWait
            progress dialog.

        Returns
        -------
        Tuple[DataFrame, list]

            - Dataframe of extracted table values
            - list of all strings extracted from the PDF
        """

        # < Revision 15/12/2025
        def inFields(v: str) -> str:
            for field in self._fields:
                if field in v: return field
            return ''
        # Revision 15/12/2025 >

        # < Revision 15/12/2025
        def inExclude(v: str) -> bool:
            for field in self._exclude:
                if field in v: return True
            return False
        # Revision 15/12/2025 >

        if splitext(filename)[1].lower() == '.pdf':
            if exists(filename):
                r2 = list()
                nf = len(self._fields)
                df = DataFrame(columns=self._fields)
                reader = easyocr.Reader(['en'])
                pdf = pymupdf.open(filename)
                for i in range(pdf.page_count):
                    if wait is not None:
                        wait.addInformationText('Page {} - Bitamp conversion...'.format(i+1))
                    png = splitext(filename)[0] + '_{}.png'.format(i)
                    if not exists(png):
                        pixmap = pdf[i].get_pixmap(dpi=300)
                        img = pixmap.pil_image()
                        img.save(png)
                    if wait is not None:
                        wait.addInformationText('Page {} - OCR processing...'.format(i + 1))
                    r = reader.readtext(png)
                    r2 += r
                    if isinstance(r, list):
                        n = len(r)
                        if n > 0:
                            # search fields to extract
                            idx = 0
                            fields = dict()
                            for j in range(n):
                                # < Revision 15/12/2025
                                # if r[j][1] in self._fields:
                                f = inFields(r[j][1])
                                if f != '':
                                    # < Revision 16/12/2025
                                    # fields[r[j][1]] = (idx, r[j][0][0][0], r[j][0][1][0])
                                    fields[f] = (idx, r[j][0][0][0], r[j][0][1][0])
                                    # Revision 16/12/2025 >
                                    idx += 1
                                    if wait is not None:
                                        wait.addInformationText('Page {} - {}/{} fields found...'.format(i + 1, idx, nf))
                                    if len(fields) == len(self._fields): break
                                # Revision 15/12/2025 >
                            # search field values to extract
                            key = 0
                            rows = dict()
                            py = None
                            for j in range(len(r)):
                                # < Revision 15/12/2025
                                # if r[j][1] in self._exclude: continue
                                if inExclude(r[j][1]): continue
                                # Revision 15/12/2025 >
                                y = r[j][0][0][1]
                                if py is None: py = y
                                # noinspection PyUnboundLocalVariable
                                if py > y: c = y / py
                                else: c = py / y
                                py = y
                                x = r[j][0][0][0]
                                for k in range(len(self._fields)):
                                    idx, x1, x2 = fields[self._fields[k]]
                                    if x1 < x < x2:
                                        if c < 0.95: key += 1
                                        if wait is not None: wait.addInformationText(
                                            'Page {} - row {}, field {}...'.format(i + 1, key, self._fields[k]))
                                        if key not in rows: rows[key] = [''] * len(self._fields)
                                        rows[key][idx] = r[j][1]
                            # append DataFrame
                            if len(rows) > 0:
                                ndf = len(df)
                                for key in rows:
                                    # < Revision 08/01/2026
                                    # if all([v != '' for v in rows[key]]) is True:
                                    if all([v != '' for v in rows[key]]):
                                        df.loc[ndf + key] = rows[key]
                                    # Revision 08/01/2026 >
                return df, r2
            else: raise IOError('No such file {}.'.format(filename))
        else: raise ValueError('{} is not a PDF file.'.format(basename(filename)))

    def setFieldNamesToExclude(self, fields: list[str]) -> None:
        """
        Set the list of strings to exclude from the OCR detection.

        Parameters
        ----------
        fields : str | list[str]
            list of strings to exclude.
        """
        self._exclude = fields

    def getFieldNamesToExclude(self) -> list[str]:
        """
        Get the list of strings to exclude from the OCR detection.

        Returns
        -------
        list[str]
            list of strings to exclude.
        """
        return self._exclude

    def appendFieldNamesToExclude(self, fields: str | list[str]):
        """
        Add strings to the list of strings to exclude from the OCR detection.

        Parameters
        ----------
        fields : str | list[str]
            list of strings to exclude.
        """
        if isinstance(fields, str): fields = [fields]
        self._exclude += fields

    def hasFieldNamesToExclude(self) -> bool:
        """
        Check if the list of strings to exclude from the OCR detection is not empty.

        Returns
        -------
        bool
            True if the list of strings to exclude is not empty.
        """
        if self._exclude is None or len(self._exclude) == 0: return False
        else: return True

    def setFieldNamesToExtract(self, fields: list[str]) -> None:
        """
        Set the list of table fields (header column) to be searched in the PDF.

        Parameters
        ----------
        fields : str | list[str]
            list of fields to be searched in the PDF.
        """
        self._fields = fields

    def appendFieldNamesToExtract(self, fields: str | list[str]):
        """
        Add fields to the list of table fields (header column) to search for in the PDF.

        Parameters
        ----------
        fields : str | list[str]
            list of fields to be searched in the PDF.
        """
        if isinstance(fields, str): fields = [fields]
        self._fields += fields

    def getFieldNamesToExtract(self) -> list[str]:
        """
        Get the list of table fields to be searched in the PDF.

        Returns
        -------
        list[str]
            list of fields (header column) to be searched in the PDF.
        """
        return self._fields

    def hasFieldNamesToExtract(self) -> bool:
        """
        Check if the list of table fields (header column) to be searched in the PDF is not empty.

        Returns
        -------
        bool
            True if the list of table fields to be searched in the PDF is not empty.
        """
        if self._fields is None or len(self._fields) == 0: return False
        else: return True

    def clearFieldNames(self) -> None:
        """
        Clear the list of table fields to be searched in the PDF.
        """
        self._fields = None
        self._exclude = None

    def saveFieldNames(self, filename: str) -> None:
        """
        Save the XML file that stores the table fields to be searched in the PDF.

        Parameters
        ----------
        filename : str
        """
        if filename != '' and len(self._fields) > 0:
            path, ext = splitext(filename)
            if ext.lower() != '.xml': filename = path + '.xml'
            doc = minidom.Document()
            root = doc.createElement('SEEGReport')
            root.setAttribute('version', '1.0')
            doc.appendChild(root)
            for i in range(len(self._fields)):
                field = self._fields[i]
                node = doc.createElement('field')
                root.appendChild(node)
                txt = doc.createTextNode(field)
                node.appendChild(txt)
            for i in range(len(self._exclude)):
                field = self._exclude[i]
                node = doc.createElement('exclude')
                root.appendChild(node)
                txt = doc.createTextNode(field)
                node.appendChild(txt)
            xml = doc.toprettyxml()
            with open(filename, 'w') as f:
                f.write(xml)

    def loadFieldNames(self, filename: str) -> None:
        """
        Load the XML file that stores the table fields to be searched in the PDF.

        Parameters
        ----------
        filename : str
        """
        if filename != '':
            path, ext = splitext(filename)
            if ext.lower() != '.xml': filename = path + '.xml'
            if exists(filename):
                self.clearFieldNames()
                doc = minidom.parse(filename)
                root = doc.documentElement
                if root.nodeName == 'SEEGReport' and root.getAttribute('version') == '1.0':
                    node = root.firstChild
                    while node:
                        if node.nodeName == 'field':
                            data = node.firstChild.data
                            if data is not None and data != '':
                                self._fields.append(data)
                        if node.nodeName == 'exclude':
                            data = node.firstChild.data
                            if data is not None and data != '':
                                self._exclude.append(data)
            else: raise IOError('No such file : {}'.format(basename(filename)))
