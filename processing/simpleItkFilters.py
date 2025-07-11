"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - SimpleITK, Medical image processing, https://simpleitk.org/
    - scikit-learn, Machine Learning, https://scikit-learn.org/stable/
"""

from math import sqrt, log, ceil

from numpy import mean
from numpy import percentile
from numpy import expand_dims
from numpy import where

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

from SimpleITK import Image as sitkImage
from SimpleITK import Cast as sitkCast
from SimpleITK import sitkFloat32
from SimpleITK import Exp as sitkExp
from SimpleITK import Shrink as sitkShrink
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage
from SimpleITK import SLICImageFilter as sitkSLICImageFilter
from SimpleITK import ScalarImageKmeansImageFilter as sitkKMeansFilter
from SimpleITK import N4BiasFieldCorrectionImageFilter as sitkBiasFieldCorrection
from SimpleITK import DiscreteGaussianImageFilter as sitkDiscreteGaussianImageFilter
from SimpleITK import RecursiveGaussianImageFilter as sitkRecursiveGaussianImageFilter
from SimpleITK import GradientAnisotropicDiffusionImageFilter as sitkGradientAnisotropicDiffusionImageFilter
from SimpleITK import CurvatureAnisotropicDiffusionImageFilter as sitkCurvatureAnisotropicDiffusionImageFilter
from SimpleITK import MinMaxCurvatureFlowImageFilter as sitkMinMaxCurvatureFlowImageFilter
from SimpleITK import CurvatureFlowImageFilter as sitkCurvatureFlowImageFilter
from SimpleITK import HistogramMatchingImageFilter as sitkHistogramMatching
from SimpleITK import MedianImageFilter as sitkMedianImageFilter
from SimpleITK import MeanImageFilter as sitkMeanImageFilter
from SimpleITK import BoxMeanImageFilter as sitkBoxMeanImageFilter
from SimpleITK import GradientMagnitudeImageFilter as sitkGradientMagnitudeImageFilter
from SimpleITK import GradientMagnitudeRecursiveGaussianImageFilter as sitkGradientMagnitudeRecursiveGaussianImageFilter
from SimpleITK import LaplacianImageFilter as sitkLaplacianImageFilter
from SimpleITK import LaplacianRecursiveGaussianImageFilter as sitkLaplacianRecursiveGaussianImageFilter
from SimpleITK import PermuteAxes as sitkPermuteAxes

from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImage import SisypheBinaryImage
from Sisyphe.core.sisypheROI import SisypheROI

__all__ = ['biasFieldCorrection',
           'kmeans',
           'slicFilter',
           'gaussianFilter',
           'recursiveGaussianFilter',
           'gradientAnisotropicDiffusionFilter',
           'curvatureAnisotropicDiffusionFilter',
           'curvatureFlowFilter',
           'minMaxCurvatureFlowFilter',
           'meanFilter',
           'medianFilter',
           'gradientMagnitudeFilter',
           'gradientMagnitudeRecursiveFilter',
           'laplacianFilter',
           'laplacianRecursiveFilter',
           'histogramIntensityMatching',
           'regressionIntensityMatching',
           'CoronalToAxial',
           'SagittalToAxial']

"""
Functions
~~~~~~~~~

    - biasFieldCorrection
    - kmeans
    - slicFilter
    - gaussianFilter
    - recursiveGaussianFilter
    - gradientAnisotropicDiffusionFilter
    - curvatureAnisotropicDiffusionFilter
    - curvatureFlowFilter
    - minMaxCurvatureFlowFilter
    - meanFilter
    - medianFilter
    - gradientMagnitudeFilter
    - gradientMagnitudeRecursiveFilter
    - laplacianFilter
    - laplacianRecursiveFilter
    - histogramIntensityMatching
    - regressionIntensityMatching
    - CoronalToAxial
    - SagittalToAxial
"""


def biasFieldCorrection(img, shrink=1, bins=200, biasfwhm=0.15, convergence=0.001, levels=4,
                        splineorder=3, filternoise=0.01, points=4, niter=50, auto=True, wait=None):
    """
        N4BiasFieldCorrectionImageFilter default parameter values
        Shrink factor 1
        Bias Field FWHM 0.15
        Spline Order 3
        Wiener filter noise 0.01
        Convergence Threshold 0.001
        Number of histogram bins 200
        Number of control points (4, 4, 4)
        Maximum number of iterations (50, 50, 50, 50)
    """
    filtr = sitkBiasFieldCorrection()
    filtr.SetNumberOfHistogramBins(bins)
    filtr.SetBiasFieldFullWidthAtHalfMaximum(biasfwhm)
    filtr.SetConvergenceThreshold(convergence)
    nbiters = [niter] * levels
    filtr.SetMaximumNumberOfIterations(nbiters)
    points = [points] * 3
    filtr.SetNumberOfControlPoints(points)
    filtr.SetSplineOrder(splineorder)
    filtr.SetWienerFilterNoise(filternoise)
    filtr.SetUseMaskLabel(False)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterIterationCommand(niter)
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    if isinstance(img, (SisypheImage, SisypheVolume)): refimg = img.getSITKImage()
    else: refimg = img

    if isinstance(refimg, sitkImage):
        pid = refimg.GetPixelID()
        refimg = sitkCast(refimg, sitkFloat32)
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    mask = None
    if auto:
        if wait is not None:
            if wait.getStopped(): return None, None
            wait.addInformationText('Preprocessing - Calc mask...')
        m = mean(sitkGetArrayViewFromImage(refimg))
        mask = refimg >= m
        filtr.SetUseMaskLabel(False)

    if shrink > 1:
        if wait is not None:
            if wait.getStopped(): return None, None
            wait.addInformationText('Preprocessing - Shrink...')
        s = refimg.GetSpacing()
        shrinkz = ceil(s[0] * shrink / s[2])
        buffimg = sitkShrink(refimg, [shrink, shrink, shrinkz])
        if mask is not None: mask = sitkShrink(mask, [shrink, shrink, shrinkz])
    else: buffimg = refimg

    if wait is not None:
        if wait.getStopped(): return None, None
        wait.addInformationText('')

    if mask is not None: simg = filtr.Execute(buffimg, mask)
    else: simg = filtr.Execute(buffimg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        bimg = filtr.GetLogBiasFieldAsImage(refimg)
        if shrink > 1: simg = refimg / sitkExp(bimg)
        simg = sitkCast(simg, pid)

        if isinstance(img, sitkImage):
            return simg, bimg
        elif isinstance(img, SisypheVolume):
            result = SisypheVolume()
            result.setSITKImage(simg)
            result.copyAttributesFrom(img, display=False)
            bias = SisypheVolume()
            bias.setSITKImage(bimg)
            bias.copyAttributesFrom(img, display=False)
            bias.acquisition.setSequenceToBiasFieldMap()
            return result, bias
        elif isinstance(img, SisypheImage):
            result = SisypheImage()
            result.setSITKImage(simg)
            bias = SisypheImage()
            bias.setSITKImage(bimg)
            return result, bias
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None, None


def kmeans(img, mask=None, nclass=3, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    if mask is not None:
        if isinstance(mask, (SisypheBinaryImage, SisypheROI)): mask = mask.getSITKImage()
        if not isinstance(mask, sitkImage):
            raise TypeError('mask parameter type {} is not sitkImage, '
                            'SisypheBinaryImage or SisypheROI.'.format(type(mask)))
        simg = simg * mask

    filtr = sitkKMeansFilter()

    # Init means for each class
    m = list()
    step = 100.0 / nclass
    v = sitkGetArrayViewFromImage(simg).flatten()
    for i in range(nclass):
        perc = int(step * (i + 0.5))
        m.append(percentile(v, perc))

    filtr.SetClassWithInitialMean(m)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def slicFilter(img, connect=True, perturb=True, niter=5, weight=10.0, gridsize=(3, 50), wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)):
        simg = img.getSITKImage()
    elif isinstance(img, sitkImage):
        simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkSLICImageFilter()
    filtr.SetMaximumNumberOfIterations(niter)
    filtr.SetEnforceConnectivity(connect)
    filtr.SetInitializationPerturbation(perturb)
    filtr.SetSpatialProximityWeight(weight)
    filtr.SetSuperGridSize(gridsize)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()

    if not stop:
        if isinstance(img, sitkImage):
            return filtr.Execute(simg)
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(filtr.Execute(simg))
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(filtr.Execute(simg))
            return fimg
    else: return None


def gaussianFilter(img, fwhm, wait=None):
    """
        Gaussian filter, convolve version
        fwhm = 2 * sqrt(2 * log(2)) * sigma
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    c = 2 * sqrt(2 * log(2))
    s = fwhm / c    # sigma form fwhm
    v = s * s       # variance
    filtr = sitkDiscreteGaussianImageFilter()
    filtr.SetVariance(v)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def recursiveGaussianFilter(img, fwhm, wait=None):
    """
        Gaussian filter, recursive version
        fwhm = 2 * sqrt(2 * log(2)) * sigma
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    c = 2 * sqrt(2 * log(2))
    s = fwhm / c
    filtr = sitkRecursiveGaussianImageFilter()
    filtr.SetSigma(s)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def gradientAnisotropicDiffusionFilter(img, step=0.0625, conductance=2.0, niter=5, wait=None):
    """
        niter       number of iteration, default 5 (larger , smoother)
        step        default 0.0625 (< spacing / 2 ^(n+1))
        conductance lower preserve image features (edge), 1.0 to 2.0
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkGradientAnisotropicDiffusionImageFilter()
    filtr.SetTimeStep(step)
    filtr.SetNumberOfIterations(niter)
    filtr.SetConductanceParameter(conductance)
    filtr.SetConductanceScalingUpdateInterval(1)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def curvatureAnisotropicDiffusionFilter(img, step=0.0625, conductance=3.0, niter=5, wait=None):
    """
        niter       number of iteration, default 5 (larger , smoother)
        step        default 0.0625 (< spacing / 2 ^(n+1))
        conductance lower preserve image features (edge), default 3.0
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkCurvatureAnisotropicDiffusionImageFilter()
    filtr.SetTimeStep(step)
    filtr.SetNumberOfIterations(niter)
    filtr.SetConductanceParameter(conductance)
    filtr.SetConductanceScalingUpdateInterval(1)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def curvatureFlowFilter(img, step=0.0625, niter=5, wait=None):
    """
        niter       int, number of iteration, default 5 (larger , smoother), typical 10
        step        float, default 0.0625 (< spacing / 2 ^(n+1)), typical 0.25 or 0.5
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkCurvatureFlowImageFilter()
    filtr.SetTimeStep(step)
    filtr.SetNumberOfIterations(niter)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def minMaxCurvatureFlowFilter(img, step=0.05, radius=2, niter=5, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkMinMaxCurvatureFlowImageFilter()
    filtr.SetTimeStep(step)
    filtr.SetStencilRadius(radius)
    filtr.SetNumberOfIterations(niter)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


def meanFilter(img, radius=3, fast=False, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    if fast: filtr = sitkBoxMeanImageFilter()
    else: filtr = sitkMeanImageFilter()
    filtr.SetRadius(radius)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def medianFilter(img, radius=3, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkMedianImageFilter()
    filtr.SetRadius(radius)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def gradientMagnitudeFilter(img, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkGradientMagnitudeImageFilter()

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def gradientMagnitudeRecursiveFilter(img, sigma=1.0, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkGradientMagnitudeRecursiveGaussianImageFilter()
    filtr.SetSigma(sigma)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def laplacianFilter(img, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkLaplacianImageFilter()

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def laplacianRecursiveFilter(img, sigma=1.0, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    # < Revision 28/09/2024
    # Cast to sitkFloat32
    pid = simg.GetPixelID()
    if pid != sitkFloat32: simg = sitkCast(simg, sitkFloat32)
    # Revision 28/09/2024 >

    filtr = sitkLaplacianRecursiveGaussianImageFilter()
    filtr.SetSigma(sigma)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg)
    # < Revision 28/09/2024
    # Cast to native datatype
    if pid != sitkFloat32: simg = sitkCast(simg, pid)
    # Revision 28/09/2024 >

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None


def histogramIntensityMatching(img, rimg, bins=128, match=2, threshold=True, wait=None):
    """
    img     source img to be matched
    rimg    reference img
    """
    # Convert source image to sitkImage
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('reference image parameter type {}'
                          ' is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    # Convert reference image to sitkImage
    if isinstance(rimg, (SisypheImage, SisypheVolume)): rimg = rimg.getSITKImage()
    elif not isinstance(rimg, sitkImage):
        raise TypeError('source image parameter type {}'
                        ' is not sitkImage, SisypheImage or SisypheVolume.'.format(type(rimg)))

    # Cast to reference image datatype
    if simg.GetPixelID() != rimg.GetPixelID():
        simg = sitkCast(simg, rimg.GetPixelID())

    filtr = sitkHistogramMatching()
    filtr.SetNumberOfHistogramLevels(bins)
    filtr.SetNumberOfMatchPoints(match)
    filtr.SetThresholdAtMeanIntensity(threshold)

    if wait is not None:
        wait.setSimpleITKFilter(filtr)
        wait.addSimpleITKFilterProcessCommand()
        wait.progressVisibilityOn()
        wait.buttonVisibilityOn()

    simg = filtr.Execute(simg, rimg)

    stop = False
    if wait is not None:
        stop = wait.getStopped()
        wait.buttonVisibilityOff()

    if not stop:
        if isinstance(img, sitkImage):
            return simg
        elif isinstance(img, SisypheVolume):
            fimg = SisypheVolume()
            fimg.setSITKImage(simg)
            img.copyAttributesTo(fimg)
            return fimg
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
        else: raise TypeError('image parameter type {} is not not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))
    else: return None


# < Revision 21/10/2024
# add regressionIntensityMatching function
def regressionIntensityMatching(img: SisypheVolume,
                                rimg: SisypheVolume,
                                mask: SisypheVolume | SisypheROI | None = None,
                                order: int = 1,
                                truncate: bool = True):
    """
    img     source img to be matched
    rimg    reference img
    """
    if img.hasSameSize(rimg):
        if mask is None:
            src = expand_dims(img.getNumpy().flatten(), axis=1)
            ref = expand_dims(rimg.getNumpy().flatten(), axis=1)
        else:
            mask = mask.getNumpy().flatten()
            src = expand_dims(img.getNumpy().flatten()[where(mask != 0)], axis=1)
            ref = expand_dims(rimg.getNumpy().flatten()[where(mask != 0)], axis=1)
        poly = PolynomialFeatures(degree=order)
        srcpoly = poly.fit_transform(src)
        model = LinearRegression()
        model.fit(srcpoly, ref)
        if mask is not None:
            srcpoly = poly.fit_transform(expand_dims(img.getNumpy().flatten().flatten(), axis=1))
        matched = model.predict(srcpoly)
        if truncate:
            # noinspection PyArgumentList
            rmin = ref.min()
            # noinspection PyArgumentList
            rmax = ref.max()
            matched[matched < rmin] = rmin
            matched[matched > rmax] = rmax
        # < Revision 29/11/2024
        # bug fix, reshape vector image
        matched = matched.reshape(img.getNumpy().shape)
        # Revision 29/11/2024 >
        r = SisypheVolume()
        r.copyFromNumpyArray(matched, spacing=img.getSpacing())
        r.copyPropertiesFrom(img, slope=False)
        return r
    else: raise ValueError('Source and reference images have not the same size.')
# Revision 21/10/2024 >


def CoronalToAxial(img):
    if isinstance(img, (SisypheImage, SisypheVolume)):
        simg = img.getSITKImage()
    elif isinstance(img, sitkImage):
        simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    if isinstance(img, sitkImage):
        return sitkPermuteAxes(simg, [0, 2, 1])
    elif isinstance(img, SisypheVolume):
        fimg = SisypheVolume()
        fimg.setSITKImage(sitkPermuteAxes(simg, [0, 2, 1]))
        fimg.setOrientationToAxial()
        img.copyAttributesTo(fimg)
        return fimg
    else:
        fimg = SisypheImage()
        fimg.setSITKImage(sitkPermuteAxes(simg, [0, 2, 1]))
        return fimg


def SagittalToAxial(img):
    if isinstance(img, (SisypheImage, SisypheVolume)):
        simg = img.getSITKImage()
    elif isinstance(img, sitkImage):
        simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    if isinstance(img, sitkImage):
        return sitkPermuteAxes(simg, [1, 2, 0])
    elif isinstance(img, SisypheVolume):
        fimg = SisypheVolume()
        fimg.setSITKImage(sitkPermuteAxes(simg, [1, 2, 0]))
        fimg.setOrientationToAxial()
        img.copyAttributesTo(fimg)
        return fimg
    else:
        fimg = SisypheImage()
        fimg.setSITKImage(sitkPermuteAxes(simg, [1, 2, 0]))
        return fimg
