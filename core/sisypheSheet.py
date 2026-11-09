"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - pandas, data analysis and manipulation tool, https://pandas.pydata.org/
    - SciPy, fundamental algorithms for scientific computing, https://scipy.org/
"""

from __future__ import annotations
from os.path import exists
from os.path import splitext

from xml.dom import minidom

from numpy import load as npload
from numpy import save as npsave
from numpy import savez as npsavez

from pandas import DataFrame
from pandas import read_csv
from pandas import read_json
from pandas import read_excel
from pandas import read_table
from pandas import read_xml
from pandas import read_spss
from pandas import read_sas
from pandas import read_stata

from scipy.io import savemat

__all__ = ['SisypheSheet']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - pandas.DataFrame -> SisypheDataFrame
"""

class SisypheSheet(DataFrame):
    """
    Description
    ~~~~~~~~~~~

    Class derived from pandas DataFrame class. Adds IO methods (xml, matfile) to pandas DataFrame class.

    Inheritance
    ~~~~~~~~~~~

    DataFrame -> SisypheSheet

    Creation: 10/04/2023
    Last revision: 28/10/2026
    """

    # Class constants

    _FILEEXT: str = '.xsheet'

    @classmethod
    def getFileExt(cls) -> str:
        """
        Get SisypheSheet file extension.

        Returns
        -------
        str
            '.xsheet'
        """
        return cls._FILEEXT

    @classmethod
    def getFilterExt(cls) -> str:
        """
        Get SisypheSheet filter used by QFileDialog.getOpenFileName() and QFileDialog.getSaveFileName().

        Returns
        -------
        str
            'PySisyphe Sheet (.xsheet)'
        """
        return 'PySisyphe Sheet (*.{})'.format(cls._FILEEXT)

    # noinspection unresolved-references
    @classmethod
    def parseXMLNode(cls, currentnode: minidom.Element) -> SisypheSheet:
        """
        Create a SisypheSheet instance from XML node.

        Parameters
        ----------
        currentnode : minidom.Element
            XML node

        Returns
        -------
        SisypheSheet
            new sheet
        """
        def isFloat(txt):
            try: float(txt)
            except: return False
            return True

        if currentnode.nodeName == cls.getFileExt()[1:]:
            node = currentnode.firstChild
            r = dict()
            r['data'] = list()
            while node:
                # Column names
                if node.nodeName == 'columnlabels':
                    # noinspection PyUnresolvedReferences
                    data = node.firstChild.data
                    r['columns'] = data.split('|')
                # Row names
                if node.nodeName == 'rowlabels':
                    # noinspection PyUnresolvedReferences
                    data = node.firstChild.data
                    r['index'] = data.split('|')
                # Row values
                if node.nodeName == 'row':
                    # noinspection PyUnresolvedReferences
                    data = node.firstChild.data
                    data = data.split('|')
                    if isFloat(data[0]): data = [float(v) for v in data]
                    r['data'].append(data)
                node = node.nextSibling
            r['index_names'] = [None]
            r['column_names'] = [None]
            return SisypheSheet(DataFrame.from_dict(r, orient='tight'))
        else: raise ValueError('Current node {} is not \'sheet\'.'.format(currentnode.nodeName))

    @classmethod
    def parseXML(cls, doc: minidom.Document) -> SisypheSheet:
        """
        Create a SisypheSheet instance from XML document.

        Parameters
        ----------
        doc : minidom.Document
            XML document

        Returns
        -------
        SisypheSheet
            new sheet
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
            # noinspection unresolved-references
            if root.nodeName == cls._FILEEXT[1:] and root.getAttribute('version') == '1.0':
                sheet = doc.getElementsByTagName(cls.getFileExt()[1:])[0]
                return cls.parseXMLNode(sheet)
            else: raise IOError('XML file format is not supported.')
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    @classmethod
    def load(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from a PySisyphe Sheet file (.xsheet).

        Parameters
        ----------
        filename : str
            PySisyphe Sheet file name (.xsheet)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        path, ext = splitext(filename)
        if ext.lower() != cls._FILEEXT:
            filename = path + cls._FILEEXT
        if exists(filename):
            doc = minidom.parse(filename)
            return cls.parseXML(doc)
        else: raise IOError('no such file : {}'.format(filename))

    @classmethod
    def loadCSV(cls, filename: str, sep: str = ',') -> SisypheSheet:
        """
        Create a SisypheSheet instance from a CSV file (.csv).

        Parameters
        ----------
        filename : str
            CSV file name (.csv)
        sep : str (optional)
            separator (default ",")
        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.csv':
                filename = path + '.csv'
            if exists(filename):
                # < Revision 28/10/2026
                # d = read_csv(filename, sep=sep, index_col=0).to_dict(orient='tight')
                # return SisypheSheet(DataFrame.from_dict(d, orient='tight'))
                return SisypheSheet(read_csv(filename, sep=sep))
                # Revision 28/10/2026 >
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    @classmethod
    def loadTXT(cls, filename: str, sep: str = '|') -> SisypheSheet:
        """
        Create a SisypheSheet instance from a text file (.txt).

        Parameters
        ----------
        filename : str
            text file name (.txt)
        sep : str
            optional (default '|'), char separator between values

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.txt':
                filename = path + '.txt'
            if exists(filename):
                # < Revision 28/10/2026
                # d = read_table(filename, sep=sep).to_dict(orient='tight')
                # return SisypheSheet(DataFrame.from_dict(d, orient='tight').set_index('Series'))
                return SisypheSheet(read_table(filename, sep=sep))
                # Revision 28/10/2026 >
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    @classmethod
    def loadXLSX(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from an Excel file (.xlsx).

        Parameters
        ----------
        filename : str
            Excel file name (.xlsx)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.xlsx':
                filename = path + '.xlsx'
            if exists(filename):
                # < Revision 28/10/2026
                # d = read_excel(filename).to_dict(orient='tight')
                # return SisypheSheet(DataFrame.from_dict(d, orient='tight').set_index('Unnamed: 0'))
                return SisypheSheet(read_excel(filename))
                # Revision 28/10/2026 >
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    @classmethod
    def loadJSON(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from a JSON file (.json).

        Parameters
        ----------
        filename : str
            JSON file name (.json)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.json':
                filename = path + '.json'
            if exists(filename):
                # < Revision 28/10/2026
                # d = read_json(filename).to_dict(orient='tight')
                # return SisypheSheet(DataFrame.from_dict(d, orient='tight'))
                return SisypheSheet(read_json(filename))
                # Revision 28/10/2026 >
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    # < Revision 28/10/2026
    @classmethod
    def loadXML(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from an XML file (.xml).

        Parameters
        ----------
        filename : str
            XML file name (.xml)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.xml':
                filename = path + '.xml'
            if exists(filename):
                return SisypheSheet(read_xml(filename))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # < Revision 28/10/2026
    @classmethod
    def loadNPY(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from a Numpy file (.npy).

        Parameters
        ----------
        filename : str
            Numpy file name (.npy)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.npy':
                filename = path + '.npy'
            if exists(filename):
                d = npload(filename,  allow_pickle=True)
                return SisypheSheet(DataFrame(d))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # < Revision 28/10/2026
    @classmethod
    def loadNPZ(cls, filename: str, index: int = 0) -> SisypheSheet:
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.npz':
                filename = path + '.npz'
            if exists(filename):
                d = npload(filename, allow_pickle=True)
                return SisypheSheet(DataFrame(d[tuple(d.keys())[index]]))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # < Revision 28/10/2026
    @classmethod
    def loadSAS(cls, filename: str) -> SisypheSheet:
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.sas7bdat':
                filename = path + '.sas7bdat'
            if exists(filename):
                return SisypheSheet(read_sas(filename, index=False))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # < Revision 28/10/2026
    @classmethod
    def loadSPSS(cls, filename: str) -> SisypheSheet:
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.sav':
                filename = path + '.sav'
            if exists(filename):
                return SisypheSheet(read_spss(filename))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # < Revision 28/10/2026
    @classmethod
    def loadSTATA(cls, filename: str) -> SisypheSheet:
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.dta':
                filename = path + '.dta'
            if exists(filename):
                return SisypheSheet(read_stata(filename))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 28/10/2026 >

    # Special methods

    def __init__(self, *args, **kwargs):
        """
        SisypheSheet instance constructor.

        Parameters
        ----------
        *args
            inherited DataFrame constructor parameters
        **kwargs
            inherited DataFrame constructor parameters
        """
        super().__init__(*args, **kwargs)

    # Public methods

    def createXML(self, doc: minidom.Document, currentnode: minidom.Element) -> None:
        """
        Write the current SisypheSheet instance attributes to XML document instance.

        Parameters
        ----------
        doc : minidom.Document
            XML document
        currentnode : minidom.Element
            XML root node
        """
        if isinstance(doc, minidom.Document):
            if isinstance(currentnode, minidom.Element):
                # Column names
                node = doc.createElement('columnlabels')
                currentnode.appendChild(node)
                h = [str(c) for c in self.columns]
                txt = doc.createTextNode('|'.join(h))
                node.appendChild(txt)
                # Row names
                node = doc.createElement('rowlabels')
                currentnode.appendChild(node)
                h = [str(i) for i in self.index]
                txt = doc.createTextNode('|'.join(h))
                node.appendChild(txt)
                # Row values
                for r in list(self.index):
                    node = doc.createElement('row')
                    currentnode.appendChild(node)
                    buff = [str(v) for v in list(self.loc[r])]
                    txt = doc.createTextNode('|'.join(buff))
                    node.appendChild(txt)
        else: raise TypeError('parameter type {} is not xml.dom.minidom.Document.'.format(type(doc)))

    def save(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to a PySisyphe Sheet file (.xsheet).

        Parameters
        ----------
        filename : str
            PySisyphe Sheet file name (.xsheet)
        """
        path, ext = splitext(filename)
        if ext.lower() != self._FILEEXT:
            filename = path + self._FILEEXT
        doc = minidom.Document()
        root = doc.createElement(self._FILEEXT[1:])
        root.setAttribute('version', '1.0')
        doc.appendChild(root)
        self.createXML(doc, root)
        buff = doc.toprettyxml()
        """

            Save XML (*.xsheet)

        """
        f = open(filename, 'w')
        try: f.write(buff)
        except IOError: raise IOError('XML file write error.')
        finally: f.close()

    def saveCSV(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to a CSV file (.csv).

        Parameters
        ----------
        filename : str
            CSV file name (.csv)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.csv': filename = path + '.csv'
            # < Revision 28/10/2026
            # self.to_csv(filename, index_label='Series')
            self.to_csv(filename, index=False)
            # Revision 28/10/2026 >
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    def saveTXT(self, filename: str, sep: str = '|') -> None:
        """
        Save the current SisypheSheet instance to a text file (.txt).

        Parameters
        ----------
        filename : str
            text file name (.txt)
        sep : str
            optional (default '|'), char separator between values
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.txt': filename = path + '.txt'
            # < Revision 28/10/2026
            # self.to_csv(filename, index_label='Series', sep=sep)
            self.to_csv(filename, index=False, sep=sep)
            # Revision 28/10/2026 >
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    def saveMATFILE(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to a Matlab file (.mat).

        Parameters
        ----------
        filename : str
            Matlab file name (.mat)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.mat': filename = path + '.mat'
            # < Revision 28/10/2026
            # d = self.to_dict()
            d = self.to_dict(index=False)
            # Revision 28/10/2026 >
            savemat(filename, d)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    # < Revision 13/12/2024
    def saveNPY(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to a Numpy binary file (.npy).

        Parameters
        ----------
        filename : str
            Numpy binary file name (.npy)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.npy': filename = path + '.npy'
            np = self.values
            npsave(filename, np)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 13/12/2024 >

    # < Revision 13/12/2024
    def saveNPZ(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to a Numpy binary compressed file (.npz).

        Parameters
        ----------
        filename : str
            Numpy binary compressed file name (.npz)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.npz': filename = path + '.npz'
            np = self.values
            npsavez(filename, np)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 13/12/2024 >

    # < Revision 28/10/2026
    def saveXML(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to XML file (.xml).

        Parameters
        ----------
        filename : str
            XML file name (.xml)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.xml': filename = path + '.xml'
            xml = self.to_xml(index=False)
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(xml)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # evision 28/10/2026 >

    # < Revision 28/10/2026
    def saveLATEX(self, filename: str) -> None:
        """
        Save the current SisypheSheet instance to XML file (.xml).

        Parameters
        ----------
        filename : str
            XML file name (.xml)
        """
        if isinstance(filename, str):
            path, ext = splitext(filename)
            if ext.lower() != '.tex': filename = path + '.tex'
            latex = self.to_latex(index=False)
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(latex)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # evision 28/10/2026 >

    # Aliases

    saveXLSX = DataFrame.to_excel
    saveJSON = DataFrame.to_json
    saveSTATA = DataFrame.to_stata
    saveHTML = DataFrame.to_html
    toClipboard = DataFrame.to_clipboard
