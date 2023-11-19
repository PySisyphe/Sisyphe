import sys

if sys.version_info.major == 3 and sys.version_info.minor < 10:
    raise ImportError('PySisyphe needs Python version 3.10 or above.')

from . import version

from .core.sisypheImageAttributes import *
from .core.sisypheConstants import *
from .core.sisypheDatabase import *
from .core.sisypheDicom import *
from .core.sisypheFiducialBox import *
from .core.sisypheImage import *
from .core.sisypheImageIO import *
from .core.sisypheLUT import *
from .core.sisypheMesh import *
from .core.sisypheMeshIO import *
from .core.sisypheRecent import *
from .core.sisypheROI import *
from .core.sisypheSettings import *
from .core.sisypheSheet import *
from .core.sisypheStatistics import *
from .core.sisypheTransform import *
from .core.sisypheVolume import *
from .core.sisypheXml import *

__version__ = version.__version__
