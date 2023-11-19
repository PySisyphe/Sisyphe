"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PYFAB           https://pypi.org/project/pyfab/                             Bayesian model-fitting framework
                        https://pyfab.readthedocs.io/en/latest/tutorial.html
                        https://fabber-dsc.readthedocs.io/en/latest/
"""

import os
from os.path import join

import fabber
from fabber import Fabber

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList

os.environ['FABBERDIR'] = join(fabber.__path__[0], 'fabber')

__all__ = ['dynamicSusceptibilityContrast']

"""
    Functions

        dynamicSusceptibilityContrast
"""

def dynamicSusceptibilityContrast(vols, aifroi, te, delt, mask='mean', wait=None):
    """
        vols        list[SisypheVolume] | SisypheVolumeCollection
        aifroi      SisypheROI, aif voxels
        te          float, echo time in s
        delt 	    float, time separation between volumes in s
        mask        str, brain mask algorithm (default='mean',
        wait        DialogWait
    """
    if wait is not None:
        wait.setInformationText('DSC initialization...')
        wait.setProgressRange(0, 100)
        wait.progressVisibilityOff()
        wait.buttonVisibilityOff()
        wait.open()
    # mask calculation
    mask = vols[0].getMask(algo=mask)
    mask = mask.getNumpy()
    # numpy conversion of volumes
    if isinstance(vols, (list, SisypheVolumeCollection)):
        n = len(vols)
        if n > 1:
            vols = multiComponentSisypheVolumeFromList(vols)
            data = vols.getNumpy()
        else: raise ValueError('invalid number of volumes.')
    else: raise TypeError('vols parameter type {} is not list or SisypheVolumeCollection.'.format(type(vols)))
    # arterial input function extraction
    if isinstance(aifroi, SisypheROI):
        if aifroi.getSize() == vols[0].getSize():
            aif = vols.getValuesInsideMask(aifroi, asnumpy=True)
        else: raise ValueError('invalid aifroi parameter size {}.'.format(aifroi.getSize()))
    else: raise TypeError('aifroi parameter type {} is not SisypheROI.'.format(type(aifroi)))
    """
        Fabber options:
        
        data        4D Numpy array
        mask        3D Numpy array
        aif 	    Numpy array, ASCII matrix containing the arterial signal
        aifsig 	    Indicate that the AIF is a signal curve
        aifconc     Indicate that the AIF is a concentration curve
        te          echo time in s
        delt 	    Time separation between volumes in minutes
        disp 	    Apply dispersion to AIF
        inferdelay  The model will incorporate a voxelwise delay in the arrival of the bolus,
                    the AIF for a voxel will be the specified curve time shifted by the delay. 
                    The delay value will be estimated within the Bayesian framework in the same
                    way as the other model parameters.
        inferart 	Infer arterial component
        inferret 	Infer tracer retention parameter. This is the proportion of the tracer
                    which remains in the tissue and is not removed by the residue function
    """
    fab = Fabber()
    options = fab.get_options(model='dsc')
    options['te'] = te
    options['delt'] = delt / 60.0
    options['aif'] = aif
    options['aifsig'] = True
    options['aifconc'] = False
    options['inferdelay'] = True
    options['disp'] = True
    options['inferart'] = False
    options['infermtt'] = False
    options['usecbv'] = True
    options['inferlambda'] = True
    options['inferret'] = True
    options['convmtx'] = 'simple'
    options['model'] = 'dsc'
    options['method'] = 'vb'
    options['noise'] = 'white'
    options['data'] = data
    options['mask'] = mask
    # Model processing (Fabber dsc model: https://fabber-dsc.readthedocs.io/en/latest/)
    if wait is None: result = fab.run(options)
    else:
        wait.setInformationText('DSC maps processing...')
        wait.progressVisibilityOn()
        result = fab.run(options, progress_cb=wait.setCurrentProgressValuePercent)
    # Save results
    if wait is not None:
        wait.setInformationText('Save DSC maps...')
        wait.progressVisibilityOff()
    r = dict()
    for name, data in result.data.items():
        v = SisypheVolume()
        v.copyFromNumpyArray(data, spacing=vols[0].getSpacing())
        v.copyAttributesFrom(vols[0])
        v.setFilename(vols[0].getFilename())
        v.setFilenamePrefix(name + '_')
        v.save()
        r[data] = v
    return r


