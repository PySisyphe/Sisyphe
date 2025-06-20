"""
External packages/modules
-------------------------

    - darkdetect, OS dark Mode detection, https://github.com/albertosottile/darkdetect
    - psutil, Process and system utilities, https://github.com/giampaolo/psutil
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

import sys

from os import environ
from os.path import join
from os.path import dirname
from os.path import abspath

import platform

from psutil import cpu_freq
from psutil import cpu_count
from psutil import virtual_memory
from psutil import disk_partitions
from psutil import disk_usage

import itk
import vtk
from numpy.version import version as vnumpy
from matplotlib import __version__ as vmplt
from pydicom import __version__ as vpdcm
from SimpleITK import __version__ as vsitk
from ants import __version__ as vants
from dipy import __version__ as vdipy
from radiomics import __version__ as vradiomics
from pandas import __version__ as vpandas
from skimage import __version__ as vski
from scipy import __version__ as vscipy
# noinspection PyProtectedMember
from docx import __version__ as vdocx
from qtconsole import __version__ as vcons

from PyQt5.QtCore import Qt
from PyQt5.QtCore import PYQT_VERSION_STR
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QApplication

from Sisyphe.version import __version__ as versionSisyphe

__all__ = ['DialogSplash']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QDialog -> DialogSplash
"""


class DialogSplash(QDialog):
    """
    DialogSplash

    Description
    ~~~~~~~~~~~

    Splash screen displayed before main window.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogSplash

    Last revision: 07/03/2025
    """

    # Class method

    @classmethod
    def getModuleClassDirectory(cls):
        import Sisyphe.gui
        return dirname(abspath(Sisyphe.gui.__file__))

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init QWidgets
        """
        How to get version ?
        
        Python      sys.version_info.major, sys.version_info.minor, sys.version_info.micro
        Qt          PyQt5.QtCore.PYQT_VERSION_STR
        Numpy       numpy.version.version
        Matplotlib  matplotlib.__version__
        Pydicom     pydicom.__version__
        SimpleITK   SimpleITK.__version__
        ITK         itk.Version.GetITKVersion()
        VTK         vtk.vtkVersion.GetVTKVersion()
        ANTs        ants.__version__
        Dipy        dipy.__version__
        pyradiomics radiomics.__version__
        
        OS              platform.uname().system
        OS version      platform.uname().release
        CPU type        platform.uname().machine
        CPU core        os.cpu_count()
        Mac OS
            Username    os.environ['USER'] or os.environ['LOGNAME']
            Home        os.environ['HOME']
        Windows
            Username    os.environ['USERNAME']    
            Home        os.environ['USERPROFILE']
        Physical cores  psutil.cpu_count(False)
        Logical cores   psutil.cpu_count(True)
        Frequency       psutil.cpu_freq().max, psutil.cpu_freq().min, psutil.cpu_freq().current
        Memory          psutil.virtual_memory().total, 
                        psutil.virtual_memory().available,
                        psutil.virtual_memory().used,
                        psutil.virtual_memory().percent
        """
        system = sys.platform[:3]
        if system == 'dar':
            vuser = environ['USER']
            vhome = environ['HOME']
            vsysname = 'Mac OS'
            vrelease = platform.mac_ver()[0]
            vmachine = platform.uname().machine
        elif system == 'win':
            vuser = environ['USERNAME']
            vhome = environ['USERPROFILE']
            vsysname = 'Windows'
            vrelease = platform.uname().version
            vmachine = platform.uname().machine
        else:
            vuser = ''
            vhome = ''
            vsysname = ''
            vrelease = ''
            vmachine = ''

        vpython = '{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
        # noinspection PyUnresolvedReferences
        vitk = itk.Version.GetITKVersion()
        # noinspection PyArgumentList
        vvtk = vtk.vtkVersion.GetVTKVersion()
        screen = QApplication.primaryScreen()

        diskpart = disk_partitions()
        diskusage = disk_usage('/')

        icndir = 'logos'

        self._pixmap = QLabel(parent=self)
        self._pixmap.setPixmap(QPixmap(join(self.getModuleClassDirectory(), icndir, 'Logo Original.png')))
        self._pixmap.setScaledContents(True)
        self._pixmap.setFixedSize(1000, 320)
        self._info = QLabel()
        self._info.setFixedWidth(1000)
        self._info.setWordWrap(True)
        self._info.setText('PySisyphe {} (2021), developed by Jean-Albert Lotterie, contact: pysisyphe@gmail.com\n\n'
                           'Python {}, Qt {}, Numpy {}, Pandas {}, Matplotlib {}, Pydicom {}, '
                           'SimpleITK {}, ITK {}, VTK {}, ANTs {}, Dipy {}, pyradiomics {}, '
                           'Scikit-image {}, SciPy {}, python-docx {}, qtconsole {}\n\n'
                           'User: {}, Home path: {}\n'
                           'Platform: {}, version {}\n'
                           'CPU {} {:.1f} GHz, {} cores {} threads\n'
                           'Memory {:.1f} GB\n'
                           'Screen size {}x{}, scaling factor {:.1f}, {:.1f} DPI\n'
                           'Primary disk {}, {} file system, {:.1f} '
                           'GBytes, {:.1f}% free'.format(versionSisyphe,
                                                         vpython, PYQT_VERSION_STR, vnumpy,
                                                         vpandas, vmplt, vpdcm,
                                                         vsitk, vitk, vvtk, vants, vdipy, vradiomics[1:],
                                                         vski, vscipy, vdocx, vcons,
                                                         vuser, vhome, vsysname,
                                                         vrelease, vmachine,
                                                         cpu_freq().max / 1000, cpu_count(False),
                                                         cpu_count(True),
                                                         virtual_memory().total / (1024*1024),
                                                         screen.size().width(),
                                                         screen.size().height(),
                                                         screen.devicePixelRatio(),
                                                         screen.logicalDotsPerInch(),
                                                         diskpart[0][0], diskpart[0][2],
                                                         diskusage[0] / (1024 ** 3),
                                                         100 - diskusage[3]))
        self._message = QLabel(parent=self)
        self._message.setAlignment(Qt.AlignCenter)
        self._message.setFixedWidth(1000)
        self._message.setText('Starting PySisyphe...')
        self._progress = QProgressBar(parent=self)
        self._progress.setMinimum(0)
        self._progress.setMaximum(10)
        self._progress.setValue(0)
        self._progress.setAlignment(Qt.AlignCenter)
        self._exit = QPushButton('Close', parent=self)
        self._exit.setFixedWidth(100)
        self._exit.setAutoDefault(True)
        self._exit.setDefault(True)
        # noinspection PyUnresolvedReferences
        self._exit.clicked.connect(self._close)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._pixmap)
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)

        dpi = QApplication.primaryScreen().logicalDotsPerInch()
        if dpi > 100: size = int(32 * dpi / 800) * 8
        else: size = 32

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoANTs.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('ANTs {}'.format(vants))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoDipy.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r * 0.6), int(size * 0.6))
        label.setToolTip('Dipy {}'.format(vdipy))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoITK.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('ITK {}'.format(vitk))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoMatplotlib.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('Matplotlib {}'.format(vmplt))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoNumpy.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r * 1.5), int(size * 1.5))
        label.setToolTip('Numpy {}'.format(vnumpy))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoPandas.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r * 1.5), int(size * 1.5))
        label.setToolTip('Pandas {}'.format(vpandas))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoPydicom.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('Pydicom {}'.format(vpdcm))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoQt.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r * 1.5), int(size * 1.5))
        label.setToolTip('Qt {}'.format(PYQT_VERSION_STR))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'Logoscipy.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('SciPy {}'.format(vski))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoSimpleITK.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('SimpleITK {}'.format(vsitk))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'Logoskimage.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('Scikit-image {}'.format(vscipy))
        layout.addWidget(label)

        label = QLabel(parent=self)
        pixmap = QPixmap(join(self.getModuleClassDirectory(), icndir, 'LogoVTK.png'))
        r = pixmap.width() / pixmap.height()
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(int(size * r), size)
        label.setToolTip('VTK {}'.format(vvtk))
        layout.addWidget(label)

        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._info)
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._message)
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.setContentsMargins(60, 0, 60, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._progress)
        self._layout.addLayout(layout)

        layout = QHBoxLayout()
        if sys.platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        elif sys.platform == 'darwin': layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self._exit)
        self._layout.addLayout(layout)

        # Window

        if sys.platform == 'win32':
            # noinspection PyTypeChecker
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        elif sys.platform == 'darwin':
            # noinspection PyTypeChecker
            self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        # noinspection PyTypeChecker
        self.setWindowModality(Qt.WindowModal)

    # Private method

    def _close(self):
        self.accept()

    # Public methods

    def setButtonVisibility(self, v):
        if isinstance(v, bool):
            self._exit.setVisible(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def buttonVisibilityOn(self):
        self.setButtonVisibility(True)

    def buttonVisibilityOff(self):
        self.setButtonVisibility(False)

    def getButtonVisibility(self):
        return self._exit.isVisible()

    def setProgressBarVisibility(self, v):
        if isinstance(v, bool):
            self._message.setVisible(v)
            self._progress.setVisible(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def progressBarVisibilityOn(self):
        self._message.setVisible(True)
        self.setProgressBarVisibility(True)

    def progressBarVisibilityOff(self):
        self._message.setVisible(False)
        self.setProgressBarVisibility(False)

    def getProgressBarVisibility(self):
        return self._progress.isVisible()

    def setMessage(self, msg: str):
        self.activateWindow()
        self._message.setText(msg)
        QApplication.processEvents()

    def getProgressBar(self) -> QProgressBar:
        return self._progress
