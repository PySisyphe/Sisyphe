from numbers import Number

import numpy as np

from dipy.denoise.nlmeans_block import nlmeans_block
from dipy.testing.decorators import warning_for_keywords

from datetime import datetime

# noinspection PyProtectedMember
from multiprocessing.managers import DictProxy

from Sisyphe.gui.dialogWait import DialogWait


@warning_for_keywords()
def non_local_means(
    arr, sigma, *, mask=None, patch_radius=1, block_radius=5, rician=True, wait : DialogWait | DictProxy | None = None
):
    r"""Non-local means for denoising 3D and 4D images, using blockwise
    averaging approach.

    See :footcite:p:`Coupe2008` and :footcite:p:`Coupe2012` for further details
    about the method.

    Parameters
    ----------
    arr : 3D or 4D ndarray
        The array to be denoised
    mask : 3D ndarray
        Mask on data where the non-local means will be applied.
    sigma : float or ndarray
        standard deviation of the noise estimated from the data
    patch_radius : int
        patch size is ``2 x patch_radius + 1``. Default is 1.
    block_radius : int
        block size is ``2 x block_radius + 1``. Default is 5.
    rician : boolean
        If True the noise is estimated as Rician, otherwise Gaussian noise
        is assumed.
    wait : DialogWait | multiprocessing.managers.DictProxy | None
        optional progress dialog or multiprocessing shared dict (DictProxy)

    Returns
    -------
    denoised_arr : ndarray
        the denoised ``arr`` which has the same shape as ``arr``.

    References
    ----------
    .. footbibliography::

    """
    if isinstance(sigma, np.ndarray) and sigma.size == 1:
        sigma = sigma.item()
    if isinstance(sigma, np.ndarray):
        if arr.ndim == 3:
            raise ValueError("sigma should be a scalar for 3D data", sigma)
        if not np.issubdtype(sigma.dtype, np.number):
            raise ValueError("sigma should be an array of floats", sigma)
        if arr.ndim == 4 and sigma.ndim != 1:
            raise ValueError("sigma should be a 1D array for 4D data", sigma)
        if arr.ndim == 4 and sigma.shape[0] != arr.shape[-1]:
            raise ValueError(
                "sigma should have the same length as the last "
                "dimension of arr for 4D data",
                sigma,
            )
    else:
        if not isinstance(sigma, Number):
            raise ValueError("sigma should be a float", sigma)
        # if sigma is a scalar and arr is 4D, we assume the same sigma for all
        if arr.ndim == 4:
            sigma = np.array([sigma] * arr.shape[-1])

    if mask is None and arr.ndim > 2:
        mask = np.ones((arr.shape[0], arr.shape[1], arr.shape[2]), dtype="f8")
    else:
        mask = np.ascontiguousarray(mask, dtype="f8")

    if mask.ndim != 3:
        raise ValueError("mask needs to be a 3D ndarray", mask.shape)

    if arr.ndim == 3:
        return np.array(
            nlmeans_block(
                np.double(arr), mask, patch_radius, block_radius, sigma, int(rician)
            )
        ).astype(arr.dtype)
    elif arr.ndim == 4:
        # < Revision 18/06/2024 from original dipy
        t = datetime.now()
        if wait is not None:
            if isinstance(wait, DialogWait):
                wait.progressVisibilityOn()
                wait.setProgressRange(0, arr.shape[-1])
                wait.setCurrentProgressValue(0)
            elif isinstance(wait, DictProxy): wait['max'] = arr.shape[-1]
        # Revision 18/06/2024 from original dipy >
        denoised_arr = np.zeros_like(arr)
        for i in range(arr.shape[-1]):
            # < Revision 18/06/2024 from original dipy
            if wait is not None and i > 0:
                now = datetime.now()
                delta = now - t
                t = now
                delta *= arr.shape[-1] - i
                m = delta.seconds // 60
                s = delta.seconds - (m * 60)
                if m == 0:
                    if isinstance(wait, DialogWait): wait.addInformationText('Estimated time remaining {} s.'.format(s))
                    elif isinstance(wait, DictProxy): wait['amsg'] = 'Estimated time remaining {} s.'.format(s)
                else:
                    if isinstance(wait, DialogWait): wait.addInformationText('Estimated time remaining {} min {} s.'.format(m, s))
                    elif isinstance(wait, DictProxy): wait['amsg'] = 'Estimated time remaining {} min {} s.'.format(m, s)
            # Revision 18/06/2024 from original dipy >
            denoised_arr[..., i] = np.array(
                nlmeans_block(
                    np.double(arr[..., i]),
                    mask,
                    patch_radius,
                    block_radius,
                    sigma[i],
                    int(rician),
                )
            ).astype(arr.dtype)
            # < Revision 18/06/2024 from original dipy
            if wait is not None:
                if isinstance(wait, DialogWait): wait.setCurrentProgressValue(i + 1)
                elif isinstance(wait, DictProxy): wait['value'] = i + 1
            # Revision 18/06/2024 from original dipy >
        # < Revision 18/06/2024 from original dipy
        if wait is not None:
            if isinstance(wait, DialogWait): wait.progressVisibilityOff()
            elif isinstance(wait, DictProxy): wait['max'] = 0
        # Revision 18/06/2024 from original dipy >
        return denoised_arr

    else:
        raise ValueError("Only 3D or 4D array are supported!", arr.shape)
