"""
Kelly Kapowski algorithm with computing cortical thickness
"""

__all__ = ['kelly_kapowski']

from os import getcwd
from os.path import join

from ants.core import ants_image as iio
from ants import utils


def kelly_kapowski(s, g, w, its=45, r=0.025, m=1.5, **kwargs):
    """
    Compute cortical thickness using the DiReCT algorithm.

    Diffeomorphic registration-based cortical thickness based on probabilistic
    segmentation of an image.  This is an optimization algorithm.


    Arguments
    ---------
    s : ANTsimage
        segmentation image

    g : ANTsImage
        gray matter probability image

    w : ANTsImage
        white matter probability image

    its : integer
        convergence params - controls iterations

    r : scalar
        gradient descent update parameter

    m : scalar
        gradient field smoothing parameter

    kwargs : keyword arguments
        anything else, see KellyKapowski help in ANTs

    Returns
    -------
    ANTsImage
    """
    if isinstance(s, iio.ANTsImage):
        s = s.clone('unsigned int')

    d = s.dimension
    outimg = g.clone()
    kellargs = {'d': d,
                's': s,
                'g': g,
                'w': w,
                'c': "[{},0.0,10]".format(its),
                'r': r,
                'm': m,
                'o': outimg}
    for k, v in kwargs.items():
        kellargs[k] = v

    processed_kellargs = utils._int_antsProcessArguments(kellargs)

    libfn = utils.get_lib_fn('KellyKapowski')
    libfn(processed_kellargs)

    filename = join(getcwd(), 'temp.nii')
    outimg.to_filename(filename)
    return filename



