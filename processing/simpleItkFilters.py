"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from math import sqrt, log, ceil

from numpy import mean

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
           'meanFilter',
           'medianFilter',
           'gradientMagnitudeFilter',
           'gradientMagnitudeRecursiveFilter',
           'laplacianFilter',
           'laplacianRecursiveFilter',
           'histogramMatching',
           'CoronalToAxial',
           'SagittalToAxial']

"""
    Functions
    
        biasFieldCorrection
        kmeans
        slicFilter
        gaussianFilter
        recursiveGaussianFilter
        gradientAnisotropicDiffusionFilter
        curvatureAnisotropicDiffusionFilter
        curvatureFlowFilter
        nonLocalMeansFilter
        patchBasedDenoisingImageFilter
        meanFilter
        medianFilter
        gradientMagnitudeFilter
        gradientMagnitudeRecursiveFilter
        laplacianFilter
        laplacianRecursiveFilter
        histogramMatching
        CoronalToAxial
        SagittalToAxial
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
        if wait is not None: wait.addInformationText('Preprocessing - cast to float32...')
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
        wait.addInformationText('Filter processing...')

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
    else: return None, None

def kmeans(img, mask=None, wait=None):
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
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None

def slicFilter(img, connect=True, perturb=True, niter=5, weight=10.0, gridsize=(3, 50)):
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
    else: return None

def gradientAnisotropicDiffusionFilter(img, step=0.0625, conductance=2, niter=5, wait=None):
    """
        niter       number of iteration, default 5 (larger , smoother)
        step        default 0.0625 (< spacing / 2 ^(n+1))
        conductance lower preserve image features (edge), 1 to 2
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

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
    else: return None

def curvatureAnisotropicDiffusionFilter(img, step=0.0625, conductance=3, niter=5, wait=None):
    """
        niter       number of iteration, default 5 (larger , smoother)
        step        default 0.0625 (< spacing / 2 ^(n+1))
        conductance lower preserve image features (edge), default 3
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

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
    else: return None

def curvatureFlowFilter(img, step=0.0625, niter=5, wait=None):
    """
        niter       int, number of iteration, default 5 (larger , smoother), typical 10
        step        float, default 0.0625 (< spacing / 2 ^(n+1)), typical 0.25 or 0.5
    """
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkCurvatureFlowImageFilter()
    filtr.SetTimeStep(step)
    filtr.SetNumberOfIterations(niter)

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
        elif isinstance(img, SisypheImage):
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
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

    filtr = sitkLaplacianImageFilter()

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

def laplacianRecursiveFilter(img, sigma=1.0, wait=None):
    if isinstance(img, (SisypheImage, SisypheVolume)): simg = img.getSITKImage()
    elif isinstance(img, sitkImage): simg = img
    else: raise TypeError('image parameter type {} is not sitkImage, SisypheImage or SisypheVolume.'.format(type(img)))

    filtr = sitkLaplacianRecursiveGaussianImageFilter()
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

def histogramMatching(img, rimg, bins=128, match=2, threshold=True, wait=None):
    """
        rimg    reference img
        simg    source img to be normalized
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
        else:
            fimg = SisypheImage()
            fimg.setSITKImage(simg)
            return fimg
    else: return None

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

