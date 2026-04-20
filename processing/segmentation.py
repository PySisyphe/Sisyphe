"""
External packages/modules
-------------------------

    - Numpy, scientific computing, https://numpy.org/
    - scikit-learn, machine learning library, https://scikit-learn.org/stable/
    - SimpleITK, https://simpleitk.org/, Medical image processing
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from os.path import join
from os.path import dirname
from os.path import abspath

from numpy import clip
from numpy import min
from numpy import max
from numpy import array
from numpy import repeat
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

from skimage import transform

import torch

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.lib.sam import sam_model_registry
from Sisyphe.gui.dialogWait import  DialogWait

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from numpy import ndarray
    from torch import Tensor
    from Sisyphe.core.sisypheROI import  SisypheROI

__all__ = ['brainMaskFromProbabilityTissueMaps',
           'probabilityTissueMapsToLabelMap',
           'nearestNeighborTransformLabelCorrection',
           'SegmentAnything']

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

Class
-----

    - SegmentAnything

Creation: 29/07/2024
Last revision: 26/02/2026
"""

# noinspection PyTypeChecker
def brainMaskFromProbabilityTissueMaps(vols: list[SisypheVolume] | SisypheVolumeCollection,
                                       radius: int = 2) -> SisypheVolume:
    """
    Process a brain mask from probability maps.

    Parameters
    ----------
    vols : list[SisypheVolume] | SisypheVolumeCollection
        tissue maps, should contain gray and white matter maps
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
        # noinspection PyInconsistentReturns
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
    Structure label is corrected with a tissue label map (gray matter, white matter and cerebro-spinal fluid).

    Adapted from: Sdika M., Combining atlas based segmentation and intensity classification with nearest neighbor transform
    and accuracy weighted vote,  Med Image Anal. 2010 Apr;14(2):219-26
    https://doi.org/10.1016/j.media.2009.12.004

    Parameters
    ----------
    tmplLabels : SisypheVolume
        template tissue label map (gray matter, white matter and cerebro-spinal fluid) registered to subject
    subjLabels : SisypheVolume
        subject tissue label map (gray matter, white matter and cerebro-spinal fluid)
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


class SegmentAnything(object):
    """
    SegmentAnything class

    Description
    ~~~~~~~~~~~

    Perform segmentation using a Segment Anything Pre-trained Model (MedSAM).

    Reference
    https://github.com/bowang-lab/MedSAM

    Inheritance
    ~~~~~~~~~~~

    object -> SegmentAnything

    Creation: 24/02/2026
    Last revision: 26/02/2026
    """
    __slots__ = ['_model', '_image_embed', '_sizex', '_sizey', '_slc', '_orient', '_roi']

    # Special method

    def __init__(self) -> None:
        """
        SegmentAnything instance constructor.
        """
        import Sisyphe.lib.sam
        path = abspath(join(dirname(Sisyphe.lib.sam.__file__), 'model', 'medsam_vit_b.pth'))
        self._model = sam_model_registry['vit_b'](checkpoint=path)
        self._model.to('cuda:0' if torch.cuda.is_available() else 'cpu')
        self._model.eval()
        self._image_embed: Tensor | None = None
        self._sizex: int = 0
        self._sizey: int = 0
        self._slc: int = 0
        self._orient: int = 0
        self._roi: SisypheROI | None = None

    """
    Private attributes
            
    _image          ndarray, slice image
    _sizex          int, slice width
    _sizey          int, slice height
    _slc            int, slice index
    _orient         int, slice orientation 0: axial, 1: coronal, 2: sagittal
    _roi            SisypheROI
    """

    # Private method

    @torch.no_grad()
    def _preprocess(self, img):
        if len(img.shape) == 2:
            img = repeat(img[:, :, None], 3, axis=-1)
        # img.shape (sizey, sizex, 3)
        img_resize = transform.resize(img, (1024, 1024), order=3, preserve_range=True, anti_aliasing=True).astype('uint8')
        img_resize = (img_resize - img_resize.min()) / clip(img_resize.max() - img_resize.min(), a_min=1e-8, a_max=None)
        # img_resize.shape (1024, 1024, 3)
        img_tensor = torch.tensor(img_resize).float().permute(2, 0, 1).unsqueeze(0).to(self._model.device)
        # img_tensor.shape (1, 3, 1024, 1024)
        with torch.no_grad():
            self._image_embed = self._model.image_encoder(img_tensor)
        # self._image_embed.shape (1, 256, 64, 64)

    # Public method

    def setROI(self, roi: SisypheROI) -> None:
        """
        Set SisypheROI attribute in which to copy the segmentation result.

        Parameters
        ----------
        roi : SisypheROI
            ROI in which to copy the segmentation result
        """
        self._roi = roi

    def getROI(self) -> SisypheROI:
        """
        Get SisypheROI attribute in which to copy the segmentation result.

        Results
        -------
        SisypheROI
            ROI in which to copy the segmentation result
        """
        return self._roi

    def setSlice(self, vol: SisypheVolume, slc: int, orient: int) -> None:
        """
        Set slice of the SisypheVolume to segment.

        Parameters
        ----------
        vol : SisypheVolume
            volume to segment
        slc : int
            slice index
        orient: int
            slice orientation, 0: axial, 1: coronal, 2: sagittal
        """
        if vol.hasSameSize(self._roi):
            if orient == 0: img = vol.getNumpy()[slc, :, :]  # axial
            elif orient == 1: img = vol.getNumpy()[:, slc, :]  # coronal
            else: img = vol.getNumpy()[:, :, slc]  # sagittal
            self._slc = slc
            self._orient = orient
            self._sizey, self._sizex = img.shape
            self._preprocess(img)
        else: raise ValueError('Size mismatch between volume parameter and ROI.')

    @torch.no_grad()
    def segment(self, bbox: list[int] | ndarray) -> None:
        """
        Use the Segment Anything Pre-trained Model (MedSAM) to perform segmentation of the SisypheVolume attribute in a bounding box.
        The result is drawn in the SisypheROI attribute.

        Parameters
        ----------
        bbox: list[int] | ndarray
            bounding box (point1 x, point1 y, point2 x, point2 z)
        """
        if self._image_embed is not None:
            if isinstance(bbox, list): bbox = array([bbox])
            if len(bbox.shape) == 1: bbox = bbox.reshape((1, bbox.shape[0]))
            bbox1024 = bbox / array([self._sizex, self._sizey, self._sizex, self._sizey]) * 1024
            bbox_torch = torch.as_tensor(bbox1024,
                                         dtype=torch.float,
                                         device=self._image_embed.device)
            if len(bbox_torch.shape) == 2: bbox_torch = bbox_torch[:, None, :]
            sparse_embed, dense_embed = self._model.prompt_encoder(points=None,
                                                                   boxes=bbox_torch,
                                                                   masks=None)
            low_res_logits, _ = self._model.mask_decoder(image_embeddings=self._image_embed,
                                                         image_pe=self._model.prompt_encoder.get_dense_pe(),
                                                         sparse_prompt_embeddings=sparse_embed,
                                                         dense_prompt_embeddings=dense_embed,
                                                         multimask_output=False)
            low_res_pred = torch.sigmoid(low_res_logits)
            low_res_pred = torch.nn.functional.interpolate(low_res_pred,
                                                           size=(self._sizey, self._sizex),
                                                           mode='bilinear',
                                                           align_corners=False)
            low_res_pred = low_res_pred.squeeze().cpu().numpy()
            if self._orient == 0:  # axial
                mask = (self._roi.getNumpy()[self._slc, :, :] + (low_res_pred > 0.5)) > 0
                self._roi.getNumpy()[self._slc, :, :] = mask.astype('uint8')
            elif self._orient == 1:  # coronal
                mask = (self._roi.getNumpy()[:, self._slc, :] + (low_res_pred > 0.5)) > 0
                self._roi.getNumpy()[:, self._slc, :] = mask.astype('uint8')
            else:  # sagittal
                mask = (self._roi.getNumpy()[:, :, self._slc] + (low_res_pred > 0.5)) > 0
                self._roi.getNumpy()[:, :, self._slc] = mask.astype('uint8')
        else: raise AttributeError('No slice')
