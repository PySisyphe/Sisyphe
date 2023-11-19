"""
    External packages/modules

        Name            Link                                                        Usage

        Matplotlib      https://matplotlib.org/                                     Plotting library
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import exists
from os.path import splitext
from os.path import basename

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import zeros

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheStatistics import getDOF
from Sisyphe.core.sisypheStatistics import tmapContrastEstimate
from Sisyphe.core.sisypheStatistics import zmapContrastEstimate
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogContrast']

"""
    Class hierarchy

        QDialog -> DialogContrast
"""

class DialogContrast(QDialog):
    """
        DialogContrast class

        Inheritance

            QDialog -> DialogContrast

        Private attributes

            _factors    dict, key = factor name, value list of design matrix column indexes

        Public methods

            estimate()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, design, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('Statistical model definition')

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init non-GUI attributes

        if isinstance(design, str) and exists(design):
            path, ext = splitext(design)
            if ext == SisypheDesign.geModelExt():
                self._design = SisypheDesign()
                self._design.load(design)
            else: raise IOError('File format {} is not statistical model.'.format(basename(design)))
        elif isinstance(design, SisypheDesign):
            self._design = design
        else: raise TypeError('parameter type {} is not SisypheDesign.'.format(type(design)))

        # Init widgets

        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.pcolormesh(self._design.getDesign())
        cdesign = design.getBetaInformations()
        lbl = list()
        for i in range(len(cdesign)):
            lbl.append(cdesign[i][0])
        ax.set_xlabel(lbl)

        self._cfactors = LabeledComboBox()
        self._tradio = QRadioButton('t map')
        self._zradio = QRadioButton('z map')
        self._tradio.setChecked(True)
        lyout = QHBoxLayout()
        lyout.addLayout(self._cfactors)
        lyout.addLayout(self._tradio)
        lyout.addLayout(self._zradio)
        
        self._factors = dict()
        for i in range(len(cdesign)):
            if cdesign[i][1] == 2:  # Main effect
                if 'Main' in self._factors:
                    self._factors['Main'].append(i)
                    self._cfactors.addItem('Main effect')
                else: self._factors['Main'] = [i]
            elif cdesign[i][1] == 1:  # Estimable
                name = cdesign[i][0].split(' ')[0]
                if name in self._factors:
                    self._factors[name].append(i)
                    self._cfactors.addItem(name)
                else: self._factors[name] = [i]
        self._flayout = QHBoxLayout()
        self._cfactors.currentIndexChanged.connect(self._factorsComboBoxChanged)
        self._cfactors.setCurrentIndex(0)

        self._layout.addWidget(canvas)
        self._layout.addLayout(lyout)
        self._layout.addLayout(self._flayout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        self._ok = QPushButton('Estimate')
        self._ok.setFixedSize(QSize(100, 32))
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()

        self._ok.pressed.connect(self.estimate)
        cancel.pressed.connect(self.reject)

        self._layout.addLayout(layout)
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setSizeGripEnabled(False)
        
    # Private method
    
    def _factorsComboBoxChanged(self, index):
        cdesign = self._design.getBetaInformations()
        # Clear widgets from factors layout
        while self._flayout.count():
            self._flayout.takeAt(0)
        # Add widgets to factor layout
        if self._cfactors.currentIndex() == 0: k = 'Main'
        else: k = self._cfactors.currentText()
        for i in range(len(self._factors[k])):
            w = LabeledDoubleSpinBox(parent=self)
            w.setTitle(cdesign[self._factors[k][i]])
            w.setRange(-1.0, 1.0)
            self._flayout.addWidget(w)

    # Public methods

    def estimate(self):
        title = 'Statistical map estimation'
        if self._design.isEstimated():
            design = self._design.getDesign()
            # Contrast vector initialization
            cdesign = self._design.getBetaInformations()
            n = len(cdesign)
            contrast = zeros(n)
            if self._cfactors.currentIndex() == 0: k = 'Main'
            else: k = self._cfactors.currentText()
            f = self._factors[k]
            for idx in f:
                w = self._flayout.itemAt(idx).widget()
                if w is not None and isinstance(w, LabeledComboBox):
                    contrast[idx] = w.value()
            # Get degrees of freedom
            from Sisyphe.core.sisypheVolume import SisypheVolume
            img = SisypheVolume()
            df = getDOF(design)
            img.acquisition.setDegreesOfFreedom(df)
            # Statistical map
            wait = DialogWait(title=title, parent=self)
            beta = self._design.getBeta()
            variance = self._design.getPooledVariance()
            img.acquisition.setAutoCorrelations(variance.acquisition.getAutoCorrelations())
            r = None
            filename = ''
            try:
                if self._tradio.isChecked():
                    r = tmapContrastEstimate(contrast, design, beta, variance, df, wait=wait)
                    img.acquisition.setSequenceToTMap()
                    prefix = 'tmap'
                else:
                    r = zmapContrastEstimate(contrast, beta, variance, df, wait=wait)
                    img.acquisition.setSequenceToZMap()
                    prefix = 'zmap'
                if variance.hasFilename(): filename = variance.getFilename().replace('sig2', prefix)
            except Exception as err:
                QMessageBox.warning(self, title, '{}'.format(err))
            if r is not None:
                wait.setInformationText('Save statistical map.')
                img.copyFromNumpyArray(r, spacing=variance.getSpacing())
                filename = QFileDialog.getSaveFileName(self, 'Save statistical map', filename,
                                                       filter='PySisyphe volume ({})'.format(img.getFileExt()))[0]
                QApplication.processEvents()
                if filename:
                    img.saveAs(filename)
            wait.close()
        else:
            QMessageBox.warning(self, title, 'Statistical model is not estimated.')

"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    dlg = DialogContrast(parent=None)
    dlg.exec()
