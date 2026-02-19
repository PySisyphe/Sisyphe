![logo](https://github.com/PySisyphe/Sisyphe/blob/main/logo.png)

Overview
========

**PySisyphe** is a general purpose neuroimaging visualization and post-processing software.
Versions for MS Windows and MacOS platforms are available.

It supports advanced 2D and 3D visualization modes and a comprehensive collection of post-processing functions: filtering, texture analysis, co-registration, segmentation, fMRI analysis, time series analysis, perfusion and diffusion/tractography processing.

Visualization functions are based on the [VTK](https://docs.vtk.org/en/latest/) library. Reference libraries provide post-processing: [ITK](https://itk.org/), [SimpleITK](https://simpleitk.org/) (filetring, Region-Of-Interest tools), [pyradiomics](https://pyradiomics.readthedocs.io/en/latest/) (texture analysis),[ANTspyx](https://github.com/ANTsX/ANTsPy) (co-registration, prior-based registration, cortical thickness), [ANTspynet](https://github.com/antsx/antspy) (deep learning segmentation), [nilearn](https://nilearn.github.io/stable/index.html) (time-series analysis), [dipy](https://dipy.org/index.html) (diffusion/tracking analysis).

Five viewing widgets are integrated:

- **Slice view**: grid of adjacent slices with axial, coronal or sagittal orientation.
- **Orthogonal view**: three synchronized orthogonal slices and a 3D surface/texture renderer.
- **Synchronized view**: grid of slices from multiple synchronized volumes.
- **Projection view**: grid of fixed (non-interactive) 3D projections in left, right, mid-left, mid-right, cranial, caudal, anterior and posterior orientations.
- **Multi-component view**: grid of slices from adjacent volumes of a time series multi-component volume.

Common tools of viewing widgets: look-up table management, overlay(s) management, isovalue display, ROI display, mesh display, target/trajectory tools, measurement tools (distance, orthogonal distances, angle), screenshots.

ROI tools: various 2D/3D brushes, cut/copy/paste, flip, translations in any direction, interpolating empty slices, automatic or interactive hole filling, mathematical morphology operators, set operators (union/intersection/difference/symmetric difference), thresholding, region-growing segmentation, confidence connected segmentation, active contour (snake) segmentation. Most of these tools can be applied to 2D slices, whole 3D volume or to blob(s) derived from connected component labeling. Any ROI processing can be cancelled with unlimited number of undo/redo.

The interface also includes a patient database manager, a screenshots manager and a fully functional IPython console.

List of available post-processings:

- Flip/reorientation
- Datatype conversion
- Image attributes conversion
- Voxel by voxel algebra (mean, median, std, min, max, any numpy expression)
- Automatic removal of caudal slices (neck slices, usually as part of a 3D sagittal acquisition)
- Filtering/denoising: median, mean, gaussian, anistropic diffusion, non-local means, gradient magnitude, laplacian
- Intensity matching between volumes: histogram matching, regression matching
- Intensity normalization (0-1, z-score...)
- Texture analysis (first order, 2D and 3D Shape-based, gray level co-occurrence matrix, gray level run length matrix, gray level size zone matrix, neighbouring gray tone difference matrix, gray level dependence matrix)
- Biais field correction
- Fiducial markers detection of Leksell stereotaxic frame
- Co-registration (manual, frame-based, rigid, affine, displacement field, ICBM spatial normalization, batch)
- Time series realignment
- Eddy current correction
- Asymmetry analysis
- Resampling
- KMeans segmentation
- Prior-based tissue segmentation (gray matter, white matter, cerebro-spinal fluid)
- Registration-based segmentation
- Cortical thickness map
- Deep learning segmentation (skull striping, hippocampus, medial temporal lobe, tumor, T1 hypo-intensity lesions, white matter hyper-intensities)
- fMRI analysis (model, contrast, conjunction...)
- Time series analysis (ICA)
- Dynamic susceptibility contrast MR perfusion maps
- Diffusion/tracking visualization and analysis tools (DTI, DKI, SHCSA, SHCSD, DSI, DSID models)

The most common neuroimaging formats are imported/exported: DICOM (including RTSTRUCT and RTDOSE), Nifti, Nrrd, Minc, Brainvoyager, FreeSurfer, Vtk, Numpy.

All native PySisyphe files are in XML format (.xvol volume, .xroi ROI, .xmesh mesh, .xtracts tracking streamlines, .xtrf/.xtrfs geometric transformation, .xlut look-up table...).

A large collection of atlases and templates (volumes, ROI, meshes, streamlines) is already included in the package: sym and asym ICBM152, ICBM452, Atropos, Distal, Nac, SPL, SRI24.

PySisyphe is plug-in extensible and provides a fully documented API that gives access to all of the software's advanced features and widgets for fast plug-in development. API classes are available in the PySisyphe's IPython console.

[PySisyphe Website documentation](https://pysisyphe.github.io/Sisyphe/home.html)

[PySisyphe NITRC website](https://www.nitrc.org/projects/pysisyphe/)

Download Binary archive
=======================

[Download folder](https://mega.nz/folder/hKEBzRTR#MUodQFh4N8LeukE2hbkzNA)

Direct link to binary archives:
- Windows binary [PySisyphe 0.78.08 python 3.10 build 01-02-2026](https://mega.nz/file/wbkUUQ4D#OWSRX2pfy9qsHc9EfdafAQWe9riSPfvQm8GCfg6r0c4)
- Windows binary [PySisyphe 0.80.14 python 3.12 build 20-02-2026](https://mega.nz/file/BHVkSaoa#v4uTusBTiD4s9oDgfBXqXHpS2Du_2Mpwu4hIzBN7q-0)
- MacOS 11+ intel binary [PySisyphe 0.78.08 python 3.10 build 01-02-2026](https://mega.nz/file/FWNkFYwZ#YKEI5hmbCahXrEwy60r71yUR60CuXtwi2P7oNMweqSo)

Unzip the downloaded archive into the directory of your choice. The PySisyphe folder can be placed anywhere; it does not have to be in the Program Files directory on Windows or the Applications directory on MacOS. **We recommend copying it to the user directory**. To launch the software, double-click on PySisyphe.exe on Windows or PySisyphe.app on MacOS. PySisyphe may take more than a minute to start up when running for the first time.

**PySisyphe may trigger false alerts from antivirus software, particularly on the Windows platform (e.g., Avast One). If this happens, be sure to add PySisyphe.exe to the list of trusted software.**
