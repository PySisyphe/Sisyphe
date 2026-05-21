from operator import add

from numpy import pad
from numpy import where
from numpy import stack
from numpy import array
from numpy import ndarray
from numpy import nonzero

def get_mask_voxels(mask: ndarray) -> list[tuple[int, int, int]]:
    """
    Compute x,y,z coordinates of a binary mask

    Parameters
    ----------
    mask : numpy.ndarray*
        binary mask

    Returns
    -------
    list[tuple[float, float, float]]
    """
    idx = array(where(mask == 1)).T
    return list([tuple(v) for v in idx])

def get_patches(mask: ndarray,
                centers: list[tuple[int, int, int]],
                patchsize: tuple[int, int, int] = (16, 16, 16)) -> list[tuple[int, int, int]]:
    """
    Get image patches of specified size based on a set of centers.

    Parameters
    ----------
    mask : ndarray
        binary mask
    centers: list[tuple[int, int, int]]
        list of tuples corresponding voxel coordinates (x,y,z) of selected patches
    patchsize : tuple[int, int, int]
        patch size 3D (p1, p2, p3)

    Returns
    -------
    list[tuple[int, int, int]]
    """
    patches = list()
    list_of_tuples = all([isinstance(center, tuple) for center in centers])
    sizes_match = [len(center) == len(patchsize) for center in centers]
    if list_of_tuples and sizes_match:
        patch_half = tuple([idx // 2 for idx in patchsize])
        new_centers = [map(add, center, patch_half) for center in centers]
        padding = tuple((idx, size - idx) for idx, size in zip(patch_half, patchsize))
        new_image = pad(mask, padding, mode='constant', constant_values=0)
        slices = [[slice(c_idx - p_idx, c_idx + (s_idx - p_idx))
                   for (c_idx, p_idx, s_idx) in zip(center, patch_half, patchsize)]
                  for center in new_centers]
        patches = [new_image[tuple(idx)] for idx in slices]
    return patches

def normalize(imgs: tuple[ndarray]) -> tuple[ndarray]:
    images = list()
    # z-score signal normalization
    for img in imgs:
        nz = nonzero(img)
        images.append((img.astype('float32') - img[nz].mean()) / img[nz].std())
    return images

def load_patches(imgs: tuple[ndarray],
                 mask: ndarray,
                 patchsize: tuple[int, int, int],
                 batchsize: int):
    """
    Load test patches with size equal to patchsize, given a list of selected voxels patches are returned in batches.

    Parameters
    ----------
    imgs : tuple[numpy.ndarray]
        T1, FLAIR
    mask : numpy.ndarray | None
        mask of analysis
    patchsize : tuple[int, int, int]
        patch size 3D (p1, p2, p3)
    batchsize : int
    """
    voxels = get_mask_voxels(mask)
    # yield data with size equal to batch_size
    for i in range(0, len(voxels), batchsize):
        centers = voxels[i : i + batchsize]
        X = list()
        for image_modality in imgs:
            X.append(get_patches(image_modality, centers, patchsize))
        yield stack(X, axis=1), centers