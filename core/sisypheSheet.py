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

from numpy import save as npsave
from numpy import savez as npsavez

from pandas import DataFrame
from pandas import read_csv
from pandas import read_json
from pandas import read_excel
from pandas import read_table

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
    Last revision: 13/12/2024
    """

    # Class constants

    _FILEEXT = '.xsheet'

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

    @classmethod
    def parseXMLNode(cls, currentnode: minidom.Element) -> SisypheSheet:
        """
        Create a SisypheSheet instance from xml node.

        Parameters
        ----------
        currentnode : minidom.Element
            xml node

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
        Create a SisypheSheet instance from xml document.

        Parameters
        ----------
        doc : minidom.Document
            xml document

        Returns
        -------
        SisypheSheet
            new sheet
        """
        if isinstance(doc, minidom.Document):
            root = doc.documentElement
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
    def loadCSV(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from a CSV file (.csv).

        Parameters
        ----------
        filename : str
            CSV file name (.csv)

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
                d = read_csv(filename, index_col=0).to_dict(orient='tight')
                return SisypheSheet(DataFrame.from_dict(d, orient='tight'))
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
            if exists(filename):
                d = read_table(filename, sep=sep).to_dict(orient='tight')
                return SisypheSheet(DataFrame.from_dict(d, orient='tight').set_index('Series'))
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
            if exists(filename):
                d = read_excel(filename).to_dict(orient='tight')
                return SisypheSheet(DataFrame.from_dict(d, orient='tight').set_index('Unnamed: 0'))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    @classmethod
    def loadJSON(cls, filename: str) -> SisypheSheet:
        """
        Create a SisypheSheet instance from a Json file (.json).

        Parameters
        ----------
        filename : str
            Json file name (.json)

        Returns
        -------
        SisypheSheet
            loaded sheet
        """
        if isinstance(filename, str):
            if exists(filename):
                d = read_json(filename).to_dict(orient='tight')
                return SisypheSheet(DataFrame.from_dict(d, orient='tight'))
            else: raise IOError('No such file : {}'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

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
        Write the current SisypheSheet instance attributes to xml document instance.

        Parameters
        ----------
        doc : minidom.Document
            xml document
        currentnode : minidom.Element
            xml root node
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
            self.to_csv(filename, index_label='Series')
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
            self.to_csv(filename, index_label='Series', sep=sep)
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
            d = self.to_dict()
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
            if ext.lower() != '.mat': filename = path + '.npy'
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
            if ext.lower() != '.mat': filename = path + '.npz'
            np = self.values
            npsavez(filename, np)
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))
    # Revision 13/12/2024 >

    # Aliases

    saveXLSX = DataFrame.to_excel
    saveJSON = DataFrame.to_json
    saveLATEX = DataFrame.to_latex
    toClipboard = DataFrame.to_clipboard
