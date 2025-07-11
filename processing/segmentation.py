"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - scikit-learn, machine learning library, https://scikit-learn.org/stable/
    - SimpleITK, https://simpleitk.org/, Medical image processing
"""

from numpy import min
from numpy import max
from numpy import zeros
from numpy import argwhere

from SimpleITK import Cast
from SimpleITK import sitkUInt8
from SimpleITK import BinaryErode as sitkBinaryErode
from SimpleITK import BinaryDilate as sitkBinaryDilate
from SimpleITK import BinaryDilate as sitkBinaryFillhole
from SimpleITK import RelabelComponent as sitkRelabelComponent
from SimpleITK import ConnectedComponentImageFilter

from sklearn.neighbors import BallTree

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.gui.dialogWait import  DialogWait

__all__ = ['brainMaskFromProbabilityTissueMaps',
           'probabilityTissueMapsToLabelMap',
           'nearestNeighborTransformLabelCorrection']

"""
Functions
---------

    - brainMaskFromProbabilityTissueMaps(vols: list[SisypheVolume] | SisypheVolumeCollection, radius: int = 2) -> SisypheVolume
    - probabilityTissueMapsToLabelMap(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume
    - nearestNeighborTransformLabelCorrection(tmplLabels: SisypheVolume,
                                              subjLabels: SisypheVolume,
                                              vstruct: SisypheVolume,
                                              margin: int = 2,
                                              wait: DialogWait | None = None) -> SisypheVolume

Creation: 29/07/2024
Last revision:
"""

# noinspection PyTypeChecker
def brainMaskFromProbabilityTissueMaps(vols: list[SisypheVolume] | SisypheVolumeCollection,
                                       radius: int = 2) -> SisypheVolume:
    """
    Process a brain mask from probability maps.

    Parameters
    ----------
    vols : list[SisypheVolume] | SisypheVolumeCollection
        tissue maps, should contain grey and white matter maps
    radius : int
        kernel radius

    Returns
    -------
    SisypheVolume
        mask
    """
    gm = None
    wm = None
    scgm = None
    for v in vols:
        if v.acquisition.isGreyMatterMap(): gm = v
        elif v.acquisition.isWhiteMatterMap(): wm = v
        elif v.acquisition.isSubCorticalGreyMatterMap(): scgm = v
    if gm is not None and wm is not None:
        radius = [radius] * 3
        if scgm is None: mask = gm + wm
        else: mask = gm + wm + scgm
        # Erode
        img = Cast(mask.getSITKImage() >= 0.5, sitkUInt8)
        img = sitkBinaryErode(img, kernelRadius=radius)
        # Keep major connected component
        f = ConnectedComponentImageFilter()
        f.FullyConnectedOn()
        img = f.Execute(img)
        img = sitkRelabelComponent(img)
        img = (img == 1)
        # Dilate
        img = sitkBinaryDilate(img, kernelRadius=radius)
        # Fill holes
        img = sitkBinaryFillhole(img)
        mask.copyFromSITKImage(img)
        mask.copyAttributesFrom(gm)
        mask.acquisition.setModalityToOT()
        mask.acquisition.setSequence(SisypheAcquisition.MASK)
        return mask
    else:
        if gm is None and wm is None:
            raise ValueError('missing grey and white matter maps.')
        elif gm is None:
            raise ValueError('missing grey matter map.')
        elif wm is None:
            raise ValueError('missing white matter map.')


def probabilityTissueMapsToLabelMap(vols: list[SisypheVolume] | SisypheVolumeCollection) -> SisypheVolume:
    """
    Create a multilabel SisypheVolume from a list of single-component SisypheVolume or
    a SisypheVolumeCollection of probability maps.

    Parameters
    ----------
    vols : list[SisypheVolume] | SisypheVolumeCollection

    Returns
    -------
    SisypheVolume
    """
    multi = multiComponentSisypheVolumeFromList(vols)
    np = multi.getNumpy()
    mask = np.sum(axis=0) > 0.0
    labels = np.argmax(axis=0) + 1
    labels = (labels * mask).astype('uint8')
    r = SisypheVolume()
    r.copyFromNumpyArray(labels, spacing=multi.getSpacing(), origin=multi.getOrigin())
    r.copyAttributesFrom(multi)
    r.acquisition.setModalityToLB()
    r.acquisition.setSequenceToLabels()
    r.acquisition.setLabel(0, 'Background')
    for i in range(len(vols)):
        r.acquisition.setLabel(i + 1, vols[i].acquisition.getSequence())
    return r


def nearestNeighborTransformLabelCorrection(tmplLabels: SisypheVolume,
                                            subjLabels: SisypheVolume,
                                            vstruct: SisypheVolume,
                                            margin: int = 2,
                                            wait: DialogWait | None = None) -> SisypheVolume:
    """
    Correct a structure label resulting from a registration-based segmentation with a nearest neighbor transform algorithm.
    Structure label is corrected with a tissue label map (grey matter, white matter and cerebro-spinal fluid).

    Adapted from: Sdika M., Combining atlas based segmentation and intensity classification with nearest neighbor transform
    and accuracy weighted vote,  Med Image Anal. 2010 Apr;14(2):219-26
    https://doi.org/10.1016/j.media.2009.12.004

    Parameters
    ----------
    tmplLabels : SisypheVolume
        template tissue label map (grey matter, white matter and cerebro-spinal fluid) registered to subject
    subjLabels : SisypheVolume
        subject tissue label map (grey matter, white matter and cerebro-spinal fluid)
    vstruct : SisypheVolume
        subject structure label to be corrected
    margin : int
        bounding box margin around structure (number of voxels)
    wait : Sisyphe.gui.dialogWait.DialogWait | None
        progress gui dialog (default None)

    Returns
    -------
    SisypheVolume
        corrected structure label
    """
    # crop image of structure / template tissue labels / subject tissue Labels
    if wait is not None: wait.setInformationText('Crop {}...'.format(vstruct.getName()))
    np = vstruct.getNumpy(defaultshape=False)
    if margin > 0:
        c = argwhere(np)
        cmin = min(c, axis=0)
        cmax = max(c, axis=0)
        xmin = cmin[0] - margin
        ymin = cmin[1] - margin
        zmin = cmin[2] - margin
        xmax = cmax[0] + margin + 1
        ymax = cmax[1] + margin + 1
        zmax = cmax[2] + margin + 1
        if xmin < 0: xmin = 0
        if ymin < 0: ymin = 0
        if zmin < 0: zmin = 0
        s = np.shape
        if xmax > s[0]: xmax = s[0]
        if ymax > s[1]: ymax = s[1]
        if zmax > s[2]: zmax = s[2]
        struct = np[xmin:xmax, ymin:ymax, zmin:zmax]
        tmpl = tmplLabels.getNumpy(defaultshape=False)[xmin:xmax, ymin:ymax, zmin:zmax]
        subj = subjLabels.getNumpy(defaultshape=False)[xmin:xmax, ymin:ymax, zmin:zmax]
    else:
        struct = np
        tmpl = tmplLabels
        subj = subjLabels
        xmin, ymin, zmin = 0, 0, 0
        xmax, ymax, zmax = 0, 0, 0
    # nearest neighbor transform
    if wait is not None: wait.setInformationText('Nearest neighbor transform {}...'.format(vstruct.getName()))
    gm = argwhere(tmpl == 1)
    wm = argwhere(tmpl == 2)
    csf = argwhere(tmpl == 3)
    treegm = BallTree(gm, leaf_size=2)
    treewm = BallTree(wm, leaf_size=2)
    treecsf = BallTree(csf, leaf_size=2)
    _, nngm = treegm.query(argwhere(struct > -1), k=1)
    _, nnwm = treewm.query(argwhere(struct > -1), k=1)
    _, nncsf = treecsf.query(argwhere(struct > -1), k=1)
    # struct correction
    if wait is not None: wait.setInformationText('{} correction...'.format(vstruct.getName()))
    rstruct = zeros(struct.size)
    subj = subj.flatten()
    for i in range(struct.size):
        c = subj[i]
        if c == 1: rstruct[i] = struct[nngm[i]]
        elif c == 2: rstruct[i] = struct[nnwm[i]]
        elif c == 3: rstruct[i] = struct[nncsf[i]]
        else: rstruct[i] = 0
    # noinspection PyArgumentList
    rstruct.reshape(shape=struct.shape)
    cnp = np.copy()
    if margin > 0:
        cnp[xmin:xmax,
            ymin:ymax,
            zmin:zmax] = rstruct
    else: cnp = rstruct
    r = SisypheVolume()
    r.copyAttributesFrom(vstruct)
    r.copyFromNumpyArray(cnp,
                         spacing=vstruct.getSpacing(),
                         origin=vstruct.getOrigin(),
                         direction=vstruct.getDirections(),
                         defaultshape=False)
    return r
