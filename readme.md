![logo](https://github.com/PySisyphe/Sisyphe/blob/main/logo.png)

Overview
========

**PySisyphe** is a general purpose neuroimaging visualization and post-processing software.
Versions for MS Windows and MacOS platforms are available.

It supports advanced 2D and 3D visualization modes and a comprehensive collection of post-processing functions: filtering, texture analysis, co-registration, segmentation, fMRI analysis, time series analysis, perfusion and diffusion/tractography processing.

Visualization functions are based on the [VTK](https://docs.vtk.org/en/latest/) library. Reference libraries provide post-processing: [ITK](https://itk.org/), [SimpleITK](https://simpleitk.org/) (filtering, Region-Of-Interest tools), [pyradiomics](https://pyradiomics.readthedocs.io/en/latest/) (texture analysis),[ANTspyx](https://github.com/ANTsX/ANTsPy) (co-registration, prior-based registration, cortical thickness), [ANTspynet](https://github.com/antsx/antspy) (deep learning segmentation), [nilearn](https://nilearn.github.io/stable/index.html) (time-series analysis), [dipy](https://dipy.org/index.html) (diffusion/tracking analysis).

Five viewing widgets are integrated:

- **Slice view**: grid of adjacent slices with axial, coronal or sagittal orientation.
- **Orthogonal view**: three synchronized orthogonal slices and a 3D surface/texture renderer.
- **Synchronized view**: grid of slices from multiple synchronized volumes.
- **Projection view**: grid of fixed (non-interactive) 3D projections in left, right, mid-left, mid-right, cranial, caudal, anterior and posterior orientations.
- **Multi-component view**: grid of slices from adjacent volumes of a time series multi-component volume.

Common tools of viewing widgets: look-up table management, overlay(s) management, isovalue display, ROI display, mesh display, target/trajectory tools, measurement tools (distance, orthogonal distances, angle), screenshots.

ROI tools: various 2D/3D brushes, cut/copy/paste, flip, translations in any direction, interpolating empty slices, automatic or interactive hole filling, mathematical morphology operators, set operators (union/intersection/difference/symmetric difference), thresholding, region-growing segmentation, confidence connected segmentation, active contour (snake) segmentation. Most of these tools can be applied to 2D slices, whole 3D volume or to blob(s) derived from connected component labeling. Any ROI processing can be cancelled with unlimited number of undo/redo.

The interface also includes a patient database manager, a file manager, a screenshots manager and a fully functional IPython console.

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
- Quantitative MR: B0 map, B1 map, T1 map, T2/T2* map, T2' map, MTR map, QSM
- ASL DSC map
- Dynamic susceptibility contrast MR perfusion maps
- Diffusion/tracking visualization and analysis tools (DTI, FWDTI, DKI, RUMBA, SHCSA, SHCSD, DSI, DSID models)

The most common neuroimaging formats are imported/exported: DICOM (including RTSTRUCT and RTDOSE), Nifti, Nrrd, Minc, Brainvoyager, FreeSurfer, Vtk, Numpy.

All native PySisyphe files are in XML format (.xvol volume, .xroi ROI, .xmesh mesh, .xtracts tracking streamlines, .xtrf/.xtrfs geometric transformation, .xlut look-up table...).

A large collection of atlases and templates (volumes, ROI, meshes, streamlines) is already included in the package: sym and asym ICBM152, ICBM452, Atropos, Distal, Nac, SPL, SRI24.

PySisyphe is plug-in extensible and provides a fully documented API that gives access to all of the software's advanced features and widgets for fast plug-in development. API classes are available in the PySisyphe's IPython console.

[PySisyphe Website documentation](https://pysisyphe.github.io/Sisyphe/home.html)

[PySisyphe NITRC website](https://www.nitrc.org/projects/pysisyphe/)

Download
========

[Download source](https://mega.nz/folder/G18X2IRQ#BRpA7_fcyHBIK66aZNyntA)

[Download folder](https://mega.nz/folder/Kt8hzbSa#AUkLH1WH0zoawYolT8Ep0w)

Direct link to binary archives:
- Windows binary [PySisyphe 0.96.24 python 3.10 build 20-06-2026](https://mega.nz/file/a9EBnaCJ#NWedDmGWiuBBICxK0SkN6UZUxGh4ldNr3Vf-0v1n0LA)
- Windows binary [PySisyphe 0.96.24 python 3.12 build 20-06-2026](https://mega.nz/file/j50xXT6Y#BBGUC2zSYHsBprDbgOo15dyhKNLQa5gsvlXvc4JXRD4)
- MacOS 11+ intel binary [PySisyphe 0.96.24 python 3.10 build 30-06-2026](https://mega.nz/file/K5lWUB5T#PShqFfPlkWVTzVOZNRS4tJ6TRxkh1FKK_zRGVTaBjcE)
- MacOS 11+ intel binary [PySisyphe 0.96.24 python 3.12 build 30-06-2026](https://mega.nz/file/7sE1jT4a#s8AX7yJWMMcN9FUMDGoxYoAjhB4gjMF2l5X2cwJU2B8)

Unzip the downloaded archive into the directory of your choice. The PySisyphe folder can be placed anywhere; it does not have to be in the Program Files directory on Windows or the Applications directory on MacOS. **We recommend copying it to the user directory**. To launch the software, double-click on PySisyphe.exe on Windows or PySisyphe.app on MacOS. PySisyphe may take more than a minute to start up when running for the first time. Subsequent starts take less than 30 seconds.

**PySisyphe may trigger false alerts from antivirus software, particularly on the Windows platform (e.g., Avast One). If this happens, be sure to add PySisyphe.exe to the list of trusted software.**

On the Windows 11 platform, the terminal (i.e. console) remains visible in the taskbar. If you would prefer it to be hidden, simply change the default terminal application.

	- click the Start button,
	- open Windows Terminal application,
	- click the dropdown arrow (▾) in the tab bar,
	- select Settings,
	- under Startup, locate Default terminal application,
	- set it to Windows Console Host,
	- save changes.

The PySisyphe graphical user interface has been optimized for dark mode, so we recommend using this mode for the best user experience.

Enabling dark mode on the Windows 11 platform:

	- click the Start button,
	- select Settings (or press Windows + I),
	- click Personalization in the left menu,
	- select Colors,
	- in the Choose your mode line, select the Dark option to enable Windows 11 dark mode.

Enabling dark mode on the MacOS platform:

	- click the Apple menu in the top-left corner of your screen,
	- select System Settings,
	- click Appearance in the sidebar,
	- choose Dark.

Additional content, such as templates, atlases, samples, plugins, and various modality scans from volunteer groups, can be retrieved directly from the download manager integrated into the PySisyphe interface. To access the download manager, select **File > Download Manager**.
