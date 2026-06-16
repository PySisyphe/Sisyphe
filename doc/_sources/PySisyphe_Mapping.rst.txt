.. _page-mapping:

Mapping menu
============

- Model >
	- :ref:`menu-section-fmri-model`
	- :ref:`menu-section-glm-model`
	- :ref:`menu-section-models`
- :ref:`menu-section-contrast`
- :ref:`menu-section-result`
- :ref:`menu-section-latindex`
- :ref:`menu-section-conjunction`
- :ref:`menu-section-t2zmap`
- :ref:`menu-section-seriespreproc`
- :ref:`menu-section-seriesseed`
- :ref:`menu-section-seriesica`
- :ref:`menu-section-seriescorr`
- :ref:`menu-section-b0map`
- :ref:`menu-section-b1map`
- :ref:`menu-section-t1map`
- :ref:`menu-section-t2map`
- :ref:`menu-section-t2pmap`
- :ref:`menu-section-mtrmap`
- :ref:`menu-section-qsmmap`
- :ref:`menu-section-asl`
- :ref:`menu-section-dsc`

.. _menu-section-fmri-model:

fMRI model definition
---------------------

This menu allows you to define the statistical model that will be used for the voxel-by-voxel fMRI analysis (see `Nilearn introduction to fMRI statistical analysis <https://nilearn.github.io/stable/glm/glm_intro.html>`_).

.. admonition::
	Design matrix & model estimation
	
	The statistical model is described by the **design matrix X**, in which the rows represent the observations and the columns represent the explanatory factors (i.e. effects/covariates).

	The model is estimated using a multiple regression scheme using least squares solver (Moore-Penrose pseudo-inverse).

	beta = pinv(X) Y = (XtX)-1 Xt Y
	residuals i.e. model errors = Y - X beta
	pooled variance = variance(residuals)

	Y, vector of observations, 
	X, design matrix,
	beta, vector of regressor weight values, one value for each factor (effects/covariates)

	`Reference 1 <https://onlinelibrary.wiley.com/doi/10.1002/hbm.460020402>`_: Statistical parametric maps in functional imaging: A general linear approach. KJ Friston, AP Holmes, KJ Worsley, JP Poline, CD Frith, RSJ Frackowiak. Human Brain Mapping 1995;2(4):189-210.

	`Reference 2 <https://www.sciencedirect.com/science/article/abs/pii/S1053811985710075?via%3Dihub>`_: Analysis of fmri time series revisited. KJ Friston, AP Holmes, JB Poline, PJ Grasby, SCR Williams, RSJ Frackowiak, R Turner. Neuroimage 1995 Mar;2(1):45-53.

PySisyphe manages only block-related fMRI design, the following statistical models are available:

- fMRI conditions, one subject with one or more conditions (condition = block-related fMRI time series).
- fMRI subjects/conditions, several subjects with one or more conditions.
- fMRI groups/subjects/conditions, several subjects divided into several groups with one or more conditions.

1) A first **fMRI Model** dialog box is displayed to define fMRI conditions/subjects/groups and condition blocks.

- Define the number of fMRI conditions using the **Condition count** spinbox.
- Define the number of subjects using the **Subject count** spinbox, not displayed for fMRI conditions model.
- Define the number of subject groups using the **Group count** spinbox, not displayed for fMRI conditions and fMRI subjects/conditions models.

A tree widget is located below to configure the condition blocks in the fMRI time series. For each condition, you must set the index of the first block in the column title **First**, the number of images per activation block in the columun titled **Active**, the number of images per rest block in the column titled **Rest**, and finally the inter-scan interval of the time series (TR in s) in the column title **inter-scan**. You can edit the names of conditions by double-clicking on them in the first column titled **conditions**.

Left-click **OK** button to validate the model and display a second **fMRI Model** dialog box.

Left-click **Cancel** button to exit dialog box.

2) A second **fMRI Model** dialog box is displayed to add observations (time-series images) and covariates to the statistical model. 

A tree widget is located at the top with a button bar below.

To add time-series images in the statistical model, follow the steps below:

- Left-click on a condition/subject/group item to select it in the **Observations** tree structure, located in the first column. The second column, titled **Image count/filenames** displays the number of observations (i.e., the number of PySisyphe volumes in the fMRI time series) required for this item.
- Left-click **Add observation(s)** button.
- In the file selection dialog box, select the time series PySisyphe volumes (.xvol).
- The File names are displayed as child items of the current condition in the second column, titled **Image count/filenames**. A tooltip displaying the file's volume attributes pops up when the user puts the mouse pointer over a file name.

There are four types of covariates that can be added to the statistical model. A covariate must contain a number of elements equal to the total number of observations in the statistical model.

- *global covariate*, one column in the design matrix,
- *covariate by condition*, one column by condition in the design matrix,
- *covariate by subjet*, one column by subject in the design matrix,
- *covariate by group*, one column by group in the design matrix.

To add a covariate, follow the steps below:

- Left-click **Add global cov.**, **Add cov. by condition**, **Add cov. by subject** or **Add cov. by group** button.
- In the file selection dialog box, select covariate values from a file in one of the following supported formats: CSV, JSON, LaTeX, text, Excel XLSX, or Python XSHEET.
- The covariate name, which defaults to the file name without the extension, is added as a new child in the covariate tree structure (global covariate, Covariate by condition, Covariate by subject or Covariate by group) in the first column. You can edit the covariate names by double-clicking on them. A tooltip displaying the covariate values pops up when the user puts the mouse pointer over a covariate name.

To remove observations, follow the steps below:

- Left-click on a condition/subject/group item to select it in the **Observations** tree structure.
- Left-click **Remove** button.
- File names of the time series PySisyphe volumes of the current condition in the second column are removed.

To remove a covariate, follow the steps below:

- Left-click on a condition/subject/group item to select it in the global covariate(s), Covariate(s) by condition, Covariate(s) by subject or Covariate(s) by group tree structure.
- Left-click **Remove** button.
- The covariate is removed from the first column's tree structure.

Left-click **Remove all** button to remove all obersvations and covariates from the statistical model.

Left-click **View design** button shows the design matrix chart in a dialog box. This dialog includes two buttons at the bottom: a **Save bitamp** button to save a bitmap of the chart (supported bitmap formats BMP, JPG, PNG, TIFF and SVG), and a **Copy to clipboard** button to copy a bitmap capture of the chart to the clipboard.

Left-click **Save** button to save the current model as a PySisyphe statistical model file (.xmodel). The default folder is the "models" subfolder located in the PySisyphe user folder ($User/.PySisyphe). 

Statistical model parameters are as follows:

- Select the method used for **Signal normalization**:

	- *no*, native signal
	- *mean scaling*, (voxel value / mean volume value in the analysis mask) * 100
	- *median scaling*, (voxel value / median volume value in the analysis mask) * 100
	- *75th percentile scaling*, (voxel value / 75th percentile volume value in the analysis mask) * 100
	- *ROI mean scaling*, (voxel value / mean volume value in ROI mask) * 100
	- *ROI median scaling*, (voxel value / median volume value in ROI mask) * 100
	- *ROI 75th percentile scaling*, (voxel value / 75th percentile volume value in ROI mask) * 100
	- *ANCOVA mean*, add mean volume values in the analysis mask as a covariate to the statistical model
	- *ANCOVA median*, add median volume values in the analysis mask as a covariate to the statistical model
	- *ANCOVA 75th percentile*, add 75th percentile volume values in the analysis mask as a covariate to the statistical model

- Use the **ROI signal normalization** :ref:`widgets-section-single-file` widget, to select the PySisyphe ROI(s) (.xroi) that will be used for signal normalization (see above).
- Select the **Mask** of analysis. A brain mask is computed and statistical analysis is restricted to the voxels within this mask.  When the **Auto** option is selected, the brain mask is the analysis mask. When the **Auto + ROI** option is selected, the mask of analysis is the intersection (i.e. logical AND) between the brain mask and a ROI.
- Use the **Mask ROI** :ref:`widgets-section-single-file` widget, to select the PySisyphe ROI(s) (.xroi) that will be used to compute the mask of analysis (see above).
- An **Age covariate** can be added automatically to the model as a global covariate, Covariate by condition, Covariate by subject or Covariate by group. Age values are extracted from PySisyphe volume attributes (birth date and acquisition date).

Left-click **Estimate** button to compute the model estimation. Once this calculation has been completed, it is proposed to save the statistical model and then move on to the next step of defining a :ref:`menu-section-contrast`. Five files are saved: PySisyphe statistical model file (.xmodel), PySisyphe volume of beta (.xvol) suffixed with "beta", PySisyphe volume of pooled variance (.xvol) suffixed with "sig2", PySisyphe multi-component volume of observations (.xvol) suffixed with "obs", PySisyphe mean volume of observations (.xvol) suffixed with "mean" and PySisyphe analysis mask (.xvol) suffixed with "mask".

Left-click **Close** button to exit dialog box.

.. _menu-section-glm-model:

General linear model definition
-------------------------------

This menu allows you to define the statistical model that will be used for the voxel-by-voxel general linear model analysis (GLM).

The following statistical models are available:

- *One sample t-test*, one group of n images,
- *Two sample t-test*, two groups of n1 and n2 images,
- *Paired t-test*, ns subjects with two conditions of n(1) and n(2) images,
- *ANCOVA*, at least one covariate of interest
- *GLM subjects/conditions*, ns subjects with nc conditions of n(1) ... n(nc) images,
- *GLM groups/subjects/conditions*, ng groups of ns(1) ... ns(ng) subjects with nc conditions of n(1) ... n(nc) images
- *GLM groups*, ng groups with n(1) and n(ng) images,
- *GLM groups/subjects*, ng groups of ns(1) ... ns(ng) subjects with n(ns(1)) ... n(ns(ng)) images

1) A first **GLM Model** dialog box is displayed to define the number conditions/subjects/groups and set the number of images for each.

- Define the number of conditions using the **Condition count** spinbox.
- Define the number of subjects using the **Subject count** spinbox.
- Define the number of subject groups using the **Group count** spinbox.

Left-click **OK** button to validate the model and display a second **GLM Model** dialog box.

Left-click **Cancel** button to exit dialog box.

2) A second **GLM Model** dialog box is displayed to add observations (images) and covariates to the statistical model. 

A tree widget is located at the top with a button bar below.

To add time-series images in the statistical model, follow the steps below:

- Left-click on a condition/subject/group item to select it in the **Observations** tree structure, located in the first column. The number of obervations (i.e. number of PySisyphe volumes) required for this item is displayed in the second column titled **Image count/filenames**.
- Left-click **Add observation(s)** button.
- In the file selection dialog box, select PySisyphe volumes (.xvol).
- The File names are displayed as child items of the current condition in the second column, titled **Image count/filenames**. A tooltip displaying the file's volume attributes pops up when the user puts the mouse pointer over a file name.

There are four types of covariates that can be added to the statistical model. A covariate must contain a number of elements equal to the total number of observations in the statistical model.

- *global covariate*, one column in the design matrix,
- *covariate by condition*, one column by condition in the design matrix,
- *covariate by subjet*, one column by subject in the design matrix,
- *covariate by group*, one column by group in the design matrix.

To add a covariate, follow the steps below:

- Left-click **Add global cov.**, **Add cov. by condition**, **Add cov. by subject** or **Add cov. by group** button.
- In the file selection dialog box, select covariate values from a file in one of the following supported formats: CSV, JSON, LaTeX, text, Excel XLSX, or Python XSHEET.
- The covariate name, which defaults to the file name without the extension, is added as a new child in the covariate tree structure (global covariate, Covariate by condition, Covariate by subject or Covariate by group) in the first column. You can edit the covariate names by double-clicking on them. A tooltip displaying the covariate values pops up when the user puts the mouse pointer over a covariate name.

To remove observations, follow the steps below:

- Left-click on a condition/subject/group item to select it in the **Observations** tree structure.
- Left-click **Remove** button.
- PySisyphe file names of the current item are removed.

To remove a covariate, follow the steps below:

- Left-click on a condition/subject/group item to select it in the global covariate(s), Covariate(s) by condition, Covariate(s) by subject or Covariate(s) by group tree structure.
- Left-click **Remove** button.
- The covariate is removed from the first column's tree structure.

Left-click **Remove all** button to remove all obersvations and covariates from the statistical model.

Left-click **View design** button shows the design matrix chart in a dialog box. This dialog includes two buttons at the bottom: a **Save bitamp** button to save a bitmap of the chart (supported bitmap formats BMP, JPG, PNG, TIFF and SVG), and a **Copy to clipboard** button to copy a bitmap capture of the chart to the clipboard.

Left-click **Save** button to save the current model as a PySisyphe statistical model file (.xmodel). The default folder is the "models" subfolder located in the PySisyphe user folder ($User/.PySisyphe). 

Statistical model parameters are as follows:

- Select the method used for **Signal normalization**: 

	- *no*, native signal
	- *mean scaling*, (voxel value / mean volume value in the analysis mask) * 100
	- *median scaling*, (voxel value / median volume value in the analysis mask) * 100
	- *75th percentile scaling*, (voxel value / 75th percentile volume value in the analysis mask) * 100
	- *ROI mean scaling*, (voxel value / mean volume value in ROI mask) * 100
	- *ROI median scaling*, (voxel value / median volume value in ROI mask) * 100
	- *ROI 75th percentile scaling*, (voxel value / 75th percentile volume value in ROI mask) * 100
	- *ANCOVA mean*, add mean volume values in the analysis mask as a covariate to the statistical model
	- *ANCOVA median*, add median volume values in the analysis mask as a covariate to the statistical model
	- *ANCOVA 75th percentile*, add 75th percentile volume values in the analysis mask as a covariate to the statistical model

- Use the **ROI signal normalization** :ref:`widgets-section-single-file` widget, to select the PySisyphe ROI(s) (.xroi) that wil be used for signal normalization (see above).
- Select the **Mask** of analysis. A brain mask is computed and statistical analysis is restricted to the voxels within this mask.  When the **Auto** option is selected, the brain mask is the analysis mask. When the **Auto + ROI** option is selected, the mask of analysis is the intersection (i.e. logical AND) between the brain mask and a ROI.
- Use the **Mask ROI** :ref:`widgets-section-single-file` widget, to select the PySisyphe ROI(s) (.xroi) that wil be used to compute the mask of analysis (see above).
- An **Age covariate** can be added automatically to the model as a global covariate, Covariate by condition, Covariate by subject or Covariate by group. Age values are extracted from PySisyphe volume attributes (birth date and acquisition date).

Left-click **Estimate** button to compute the model estimation. Once this calculation has been completed, it is proposed to save the statistical model and then move on to the next step of defining a :ref:`menu-section-contrast`.

Left-click **Close** button to exit dialog box.

.. _menu-section-models:

Models
------

This menu displays PySisyphe statistical model files (.xmodel) in the "models" subfolder in the PySisyphe user folder (~/.PySisyphe).

Select a model item to open it in the :ref:`menu-section-fmri-model` or :ref:`menu-section-glm-model` dialog box.

The last submenu **Open model** shows a file selection dialog box to open a PySisyphe statistical model file (.xmodel) in the :ref:`menu-section-fmri-model` or :ref:`menu-section-glm-model` dialog box.

.. _menu-section-contrast:

Contrast
--------

This menu is used to define a contrast from a statistical model.

In the file selection dialog box, select a PySisyphe statistical model file (.xmodel).

A **Statistical contrast** dialog box is displayed showing design matrix chart at the top and parameters below:

- Select the factor to analyze, main factor is selected by default.
- Check the type of statistics to perform, *t-test* (t-map) or *z-score* (z-map)
- Define the contrast as weight values for each design matrix column associated with the selected factor. The sum of the weights must be equal to +1.0, 0.0 (If there is more than one weight), or -1.0.

Left-click **Estimate** button to compute the contrast estimation. Once this calculation has been completed, it is proposed to save the statistical map. 

Left-click **Close** button to exit dialog box.

.. _menu-section-result:

Result
------

This menu is used to navigate a statistical map that was generated from the :ref:`menu-section-contrast` menu.

In the file selection dialog box, select a PySisyphe statistical map (.xvol).

A **Statistical result** dialog box is displayed. It consists of five areas.

1) The first part consists of a tabbed widget with five tabs:

	- **Slices** tab shows the statistical map in an :ref:`page-orthogonalview` with a cross-shaped cursor. The background volume is the T1 symmetric ICBM152 template if the statistical map is normalized in the ICBM152 space; otherwise, the mean volume of observations is used. Left-clicking on the slice view moves the cursor to the current position of the mouse.
	- **Projections** tab shows the statistical map in an :ref:`page-projectionview`. The background volume is the T1 symmetric ICBM152 template if the statistical map is normalized in the ICBM152 space; otherwise, the mean volume of obervations is used.
	- **Beta chart** tab shows a box plot chart of beta values at the current position of the cross-shaped cursor. Beta is a regressor weight assigned to each factor in the statistical model. It is an estimate of the factor's contribution to the signal resulting from multiple regression analysis used to solve the general linear model. This tab includes three buttons at the bottom: a **Save bitamp** button to save a bitmap of the chart (supported bitmap formats BMP, JPG, PNG, TIFF and SVG), a **Copy to clipboard** button to copy a bitmap capture of the chart to the clipboard, and a **Copy to screenshots** button to copy a bitmap capture of the chart to the :ref:`page-screenshots`.
	- **Time series chart** tab shows a line plot chart of the time series signal (blue) and the adjusted model (orange) at the current position of the cross-shaped cursor. This tab is only visible for fMRI models. It has the same three buttons as the previous tab.
	- **Regression chart** tab shows a scatter plot chart between the modelled signal of the first factor on the x-axis and the osbserved signal on the y-axis. The regression line is plotted and the title reports the Pearson's correlation coefficient. This tab has the same three buttons as the previous one.

2) The second part consists of widgets to set **statistical thresholds**. These thresholds affect the statistical map, which is updated after each change.

	- Voxels with statistical significance below the **Voxel threshold** are removed from the statistical map. There are six types of thresholds available: *t-value*, *z-value*, *uncorrected p-value* (i.e. uncorrected for multiple comparisons), *Bonferroni corrected p-value* (Bonferroni correction for multiple comparisons, p-value / number of repeated tests i.e. voxel count in the analysis mask), *Gaussian field corrected p-value*, and *q FDR* (False Discovry Rate). There is a problem with multiple comparisons because the number of statistical tests performed is equal to the number of voxels in the analysis mask. The Bonferroni correction is too conservative because it does not take into account the spatial autocorrelations occurring in the images used in neuroimaging (MR, PET, SPECT modality). The other two methods, Gaussian field (see A unified statistical approach for determining significant signals in images of cerebral activation KJ Worsley, S Marrett, P Neelin, AC Vandal, KJ Friston, AC Evans. Hum Brain Mapp. 1996;4(1):58-73) and false discovry rate (see Controlling the false discovery rate: a practical and powerful approach to multiple testing. Benjamini Y, Hochberg Y. Journal of the Royal Statistical Society, Series B. 1995;57(1):289–300.) are more effective in this context. 
	- Significant voxels are spatially grouped into clusters. Any clusters below the **Cluster extent threshold** are removed from the statistical map. There are five extent thresholds available: *number of voxels*, *number of resels*, *volume* in mm3, *uncorrected p-value*, *Gaussian field corrected p-value*. Spatial autocorrelations are evaluated as a Gaussian field, whose extent is expressed as a Gaussian kernel described by a full width at half maximum (FWHM) in mm, in each dimension. A resel, which represents a volume of spatial autocorrelations, is the product of the FWHM on the three axes.

3) The third part shows global statistical results, which are organized by themes:

	- *t-map results*: degrees of freedom of the GLM model, autocorrelations FWHM in mm, Resel volume in mm3, volume of the analysis mask expressed in mm3, number of voxels, number of resels.
	- *Expected results* taking into account the number of comparisons and autocorrelations: number of significant voxels, number of clusters, number of voxels per cluster.
	- *Observed results* for the current voxel threshold: number of significant voxels, number of clusters, number of voxels per cluster.
	- *Voxel threshold*, current voxel threshold expressed as t-value, z-value, uncorrected p-value, Bonferroni corrected p-value and Gaussian field corrected p-value.
	- *Cluster extent threshold*, current cluster extent expressed as number of voxels, number of resels, volume, uncorrected p-value, Gaussian field corrected p-value.
	- *Cursor position*, voxel coordinates, t-value, z-value, uncorrected p-value, Bonferroni corrected p-value and Gaussian field corrected p-value at the cross-shaped cursor position.

4) The fourth part displays a tab providing statistical results for each cluster at the current significance and extent thresholds. Left-click on a table header to sort the rows according to the values in that column. The items provided for a cluster are as follows:

	- *x, y, z*, coordinates of the local maximum in the cluster, expressed as voxel indices along each axis.
	- *world x, y, z*, coordinates of the local maximum in the cluster, expressed in mm along each axis (i.e. world coordinates).
	- *t-value*, *z-value*, *Bonferroni corrected p-value* and *Gaussian field corrected p-value* at the local maximum in the cluster.
	- Cluster extent expressed as *number of voxels*, *number of resels*, *volume*, cluster *uncorrected p-value*, cluster *Gaussian field corrected p-value*.

5) A button bar is included in the last part.

	- Left-click **Save report** button to save a summary report of the statistical analysis results in a PDF file.
	- Left-click **Save table** button to save the cluster table in various formats: csv, Excel (.xlsx), PySisyphe XML sheet (.xsheet), or numpy (.npy).
	- Left-click **Save map** button to save the statistical map with the current voxel and extent thresholds as a PySisphe volume (.xvol).
	- Left-click **Close** button to exit dialog box.

.. _menu-section-latindex:

Laterality index
----------------

This menu is used to calculate laterality indexes (LI) of a statistical map that was generated from the :ref:`menu-section-contrast` menu.

Hemispheric or regional dominance in cognitive functions, particularly language, can be quantified using laterality indexes (LI). The LI indicates the prevalence of activation in an fMRI statistical map on one side of the brain compared to the other. Its values range from +1.0 (left dominant) to -1.0 (right dominant).

.. admonition::
	Laterality index methodology

	LI = (NLt - NRt) / (NLt + NRt)

	- NLt Number of voxels activated in the left hemisphere (or left mask) at statistical threshold t.
	- NRt Number of voxels activated in the right hemisphere (or right mask) at statistical threshold t.

	**Area Under Curve (AUC) LI**

	- CHL cumulative histograms of the number of activated voxels vs statistical threshold t in the left hemisphere (or left mask), CHL(t) = NLt
	- CHR cumulative histograms of the number of activated voxels vs statistical threshold t in the left hemisphere (or right mask), CHR(t) = NRt

	AUC CHL = ∑ NLt (∑ between t=tmin to t=tmax)
			   
	AUC LI = (AUC CHL - AUC CHR) / (AUC CHL + AUC CHR)

	**Average LI**

	Average LI = ∑ (NLt - NRt) / (NLt + NRt) / Nt (∑ between t=tmin to t=tmax)

	Nt number of t intervals

	LI indexes are calculated in a subset of voxels located within symmetric masks in each hemisphere (e.g. language areas).

	`Reference <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0230129>`_: Implementation of clinically relevant and robust fMRI-based language lateralization: Choosing the laterality index calculation method. I Brumer, E De Vita, J Ashmore, J Jarosz, M Borri. PLoS One. 2020 Mar 12;15(3):e0230129.

The **Laterality index** dialog box is displayed, which is provides five :ref:`widgets-section-single-file` widgets:

- Select a **Statistical map** PySisyphe volume (.xvol, t-map or z-map sequence attribute).
- Select one of the PySisyphe volumes (.xvol) of the fMRI time-series used to calculate the statistical map, or the mean volume of the fMRI time-series with the **fMRI volume** widget. This volume is used for the spatial normalization stage used to resample the statistical map in the ICBM152 space. This widget will not be displayed if the statistical map is already normalized in the ICBM152 space (i.e. space/transform ID is *ICBM152*).
- Select the PySisyphe ICBM152 **Template** volume. This volume is used for the spatial normalization stage. This widget will not be displayed if the statistical map is already normalized in the ICBM152 space (i.e. space/transform ID is *ICBM152*).
- Select the PySisyphe **Left mask**, left hemisphere mask in the ICBM152 space (i.e. space/transform ID is *ICBM152*). LI indexes are calculated in the subset of voxels located in this mask. It can be either a PySisyphe volume (.xvol) with a *mask* sequence attribute or a PySisyphe ROI (.xroi). The mask file type is defined by the **mask type** parameter (see **Laterality index...** parameters below).
- Select the PySisyphe **Right mask**, right hemisphere mask in the ICBM152 space (i.e. space/transform ID is *ICBM152*). LI indexes are calculated in the subset of voxels located in this mask. It can be either a PySisyphe volume (.xvol) with a mask sequence attribute or a PySisyphe ROI (.xroi). The mask file type is defined by the **mask type** parameter (see **Laterality index...** parameters below).

Toggle **Laterality index...** button to show/hide parameters:

- Select the **Mask type** option: *volume* (.xvol) with a *mask* sequence attribute or *ROI* (.xroi)
- Set the number of **Histogram bins**, number of statistical threshold intervals used for cumulative his￾tograms processing (default 100).
- Use the **Template** :ref:`widgets-section-single-file` widget to set the default ICBM152 template.
- Use the **Left mask** :ref:`widgets-section-single-file` widget to set the default ICBM152 left hemisphere mask.
- Use the **Right mask** :ref:`widgets-section-single-file` widget to set the default ICBM152 right hemisphere mask.

Left-click **OK** button to calculate the laterality index (LI). If the statistical map is not in the ICBM152 space (i.e. space/transform ID is not *ICBM152*), a spatial normalization stage is processed first.

The results are displayed in a dialog box that has a chart at the top, and a tab below. The chart shows the cumulative histograms, i.e. number of activated voxels versus statistical threshold, in the left and right hemisphere masks, respectively, in red and blue. The table shows various criteria values: 

	- *AUC left mask*, area under the cumulative histogram curve in the left hemisphere mask.
	- *AUC right mask*, area under the cumulative histogram curve in the right hemisphere mask.
	- *LI p=0.05*, laterality index at the p-value=0.05 statistical threshold.
	- *LI p=0.01*, laterality index at the p-value=0.01 statistical threshold.
	- *LI p=0.001*, laterality index at the p-value=0.001 statistical threshold.
	- *Average LI* (See Laterality index methodology above)
	- *AUC LI* (See Laterality index methodology above)

This dialog box includes four buttons at the bottom: a **Save bitamp** button to save a bitmap of the chart (supported bitmap formats BMP, JPG, PNG, TIFF and SVG), a **Copy to clipboard** button to copy a bitmap capture of the chart to the clipboard, and a **Copy to screenshots** button to copy a bitmap capture of the chart to the :ref:`Screenshots manager <page-screenshots>`, and a **Save Dataset**, which shows a dialog box to save the table in various formats (CSV, JSON, LATEX, TXT, Excel XLSX, Pysisyphe XSHEET).

Left-click **Close** button to exit dialog box.

.. _menu-section-conjunction:

Conjunction
-----------

This menu is used to perform statitical map conjunction. A Conjunction allow you to determine whether a voxel or group of voxels passes a statistical threshold for two or more statistical maps. The t-maps are converted into z-maps so that conjunctions can be performed using either t or z-maps.

.. admonition:: Reference

	`Article <https://www.sciencedirect.com/science/article/abs/pii/S1053811902911079?via%3Dihub>`_: Combining brains: a survey of methods for statistical pooling of information. NA Lazar, B Luna, JA Sweeney, WF Eddy. Neuroimage 2002 Jun;16(2):538-50.

Use the :ref:`widgets-section-multi-file` widget at the top, to select **Statistical maps** PySisyphe volume (.xvol).

Toggle **Settings...** button to show/hide parameters:

- Select the conjunction **Method**: *Fisher*, *Mudholkar*, *Stouffer*, *Tippett* or *Worsley*.
- Edit the **Default file name**. This name is used to save the conjunction as a PySisyphe volume (.xvol) in the folder of the first statistical map.

Left-click **Execute** button to compute the conjunction of statistical maps.

Left-click **Close** button to exit dialog box.

.. _menu-section-t2zmap:

t to z-map conversion
---------------------

This menu is used to convert t-map volume(s) to z-map volulme(s).

.. admonition::
	t to z-map processing

	p = 1.0 - student cdf(t, df)
	z = norm ppf(1.0 - p)
	 
	df, degrees of freedom
	t, t-value
	p, p-value
	z, z-value
	student cdf, Student cumulative distribution function
	norm ppf, Normal inverse cumulative distribution function (i.e. percent point function)

Use the :ref:`widgets-section-multi-file` widget at the top, to select **t maps** PySisyphe volume (.xvol).

Left-click **Execute** button to compute z-maps. z-map volume(s) is(are) saved with the original file name, which is suffixed with "zmap".

Left-click **Close** button to exit dialog box.

.. _menu-section-seriespreproc:

Time series preprocessing
-------------------------

This menu is used to compute preprocessing on a time series volume: spatial filtering (gaussian smoothing), detrend, standardize signal (z-scored), standardize confounds (z-scored), high variance confounds, low pass filtering and high pass filtering. PySisyphe uses the `Nilearn <https://nilearn.github.io/stable/index.html>`_ library implemenentation.

Use the :ref:`widgets-section-single-file` widget at the top, to select a **Time series** PySisyphe multi-component volume (.xvol).

Use the **Confound variable(s)** :ref:`widgets-section-multi-file` widget, under the previous, to select a confounding variable file. This file is filled with a list of values whose number must be equal to the components count in the time series volume. It can have various formats: csv, Excel (.xlsx), PySisyphe XML sheet (.xsheet), or numpy (.npy).

The preprocessing parameters are as follows:

- Check the **Tissue confounds** parameter if you want to add tissue-based signal confounds: mean signal in cerebro-spinal fluid, mean signal in gray matter, mean signal in white matter, mean global signal (cerebro-spinal fluid + gray matter + white matter). Tissue masks are extracted from a tissue label volume (see next).
- Use the **Tissue label map** :ref:`widgets-section-multi-file` widget to select a tissue label volume used to calculate tissue signal confounding variables. The label volume must be in the same space/transform ID as the time series multi-component volume. It is generated from either the :ref:`menu-section-atropos` or :ref:`menu-section-tissue` menu.
- Set the **Gaussian smoothing FWHM** in millimeters to apply to the time series. No smoothing if 0.0 (default).
- Check the **Detrend** parameter to detrend the time series.
- Check the **Standardize** parameter to standardize the time series signal. Timeseries are z-scored, i.e. shifted to zero mean and scaled to unit variance (default False).
- Check the  **Standardize confounders** parameter to standadize confounding variables. Each variable is z-scored, mean is shifted to zero and scaled to unit variance in the time dimension (default True).
- Check the **High variance confounds** parameter to compute high variance confounds on provided image and regressed out (default False).
- Set the **Low pass filter cutoff**, frequence in Hertz. If specified, signals above this frequency will be filtered out. Usual value of 0.1. If 0.0, no low-pass filtering will be performed (default).
- Set the  **High pass filter cutoff**, frequence in Hertz. If specified, signals below this frequency will be filtered out. Usual value of 0.01. If 0.0, no high-pass filtering will be performed (default).
- Use the  **Get TR from Dicom file** :ref:`widgets-section-single-file` widget to get the time series Repetition Time value (TR, in ms) from a dicom file.
- Set the **TR** parameter, time series Repetition Time value (TR, in ms). This value can be extracted from a Dicom file (see above).
- The preprocessed volume is saved with the original file name, which is prefixed and/or suffixed by the strings edited in the **Prefix** and **Suffix** parameters.

Left-click **Execute** button to perform preprocessing.

Left-click **Close** button to exit dialog box.

.. _menu-section-seriesseed:

Seed-to-voxel time series correlation
-------------------------------------

This menu is used to compute seed-to-voxel correlation map from a time series (i.e. fMRI resting-state) multi-component volume. This map shows the temporal correlation between a seed region and the rest of the brain. PySisyphe uses the  `Nilearn <https://nilearn.github.io/stable/auto_examples/03_connectivity/plot_seed_to_voxel_correlation.html>`_ library implemenentation.

Use the :ref:`widgets-section-single-file` widget at the top, to select a **Time series** PySisyphe multi-component volume (.xvol).

The seed-to-voxel time series correlation parameters are as follows:

- Check the **preprocessing** option to compute :ref:`menu-section-seriespreproc` before correlation. This triggers the display of the :ref:`menu-section-seriespreproc` parameters.
- Use the **Seed ROI** :ref:`widgets-section-single-file` widget to select a PySisyphe ROI (.xroi), which will be used as the seed region to compute the correlation with the rest of the brain.

Left-click **Execute** button to perform a time series correlation. A cross-correlation map is saved with the original file name, which is suffixed with "seed_cmap". A z-map is also saved with the original file name, which is suffixed with "seed_zmap".

Left-click **Close** button to exit dialog box.

.. _menu-section-seriesica:

Single subject time series ICA
------------------------------

This menu is used to compute a time series (i.e. fMRI resting state) Independent Component Analysis (ICA). ICA separates a multivariate signal into additive subcomponents that are maximally independent. PySisyphe uses the `scikit learn library FastICA <https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html and https://nilearn.github.io/dev/auto_examples/07_advanced/plot_ica_resting_state.html>`_ implemenentation.

Use the :ref:`widgets-section-single-file` widget at the top, to select a **Time series** PySisyphe multi-component volume (.xvol).

The Single subject time series ICA parameters are as follows:

- Check the **preprocessing** option to compute :ref:`menu-section-seriespreproc` before correlation. This triggers the display of the :ref:`menu-section-seriespreproc` parameters.
- Set the **Number of components** to extract.
- Set the **Component variance threshold**, ratio used to remove components that are likened to noise and have a low weight in the signal variance.

Left-click **Execute** button to perform ICA. An ICA multi-component volume is saved with the original file name, which is suffixed with "ica".

Left-click **Close** button to exit dialog box.

.. _menu-section-seriescorr:

Time series correlation matrix
------------------------------

This menu is used to extract time series signals (i.e. fMRI resting state) from a brain parcellation and compute a correlation matrix. PySisyphe uses the `Nilearn <https://nilearn.github.io/dev/auto_examples/03_connectivity/plot_signal_extraction.html#sphx-glr-auto-examples-03-connectivity-plot-signal-extraction-py>`_ library implemenentation.

Use the :ref:`widgets-section-single-file` widget at the top, to select a **Time series** PySisyphe multi-component volume (.xvol).

The Time series correlation matrix parameters are as follows:

- Check the **preprocessing** option to compute :ref:`menu-section-seriespreproc` before correlation. This triggers the display of the :ref:`menu-section-seriespreproc` parameters.
- Use the **Label volume** :ref:`widgets-section-single-file` widget to select a PySisyphe label volume (.xvol), which will be used for brain parcellation.

Left-click **Execute** button to compute the correlation matrix.

The result is displayed in a dialog box with two tabs. The first tab, titled **Connectivity matrix**, shows the connectivity matrix as a chart. This tab includes three buttons at the bottom: a **Save bitamp** button to save a bitmap of the chart (supported bitmap formats BMP, JPG, PNG, TIFF and SVG), a **Copy to clipboard** button to copy a bitmap capture of the chart to the clipboard, and a **Copy to screenshots** button to copy a bitmap capture of the chart to the :ref:`Screenshots manager <page-screenshots>`. The second tab, titled **Connectivity table**, shows the connectivity matrix values in table format. This tab includes the button **Save Dataset**, which shows a dialog box to save the table in various formats (CSV, JSON, LATEX, TXT, Excel XLSX, Pysisyphe XSHEET).

Left-click **Close** button to exit dialog box.

.. _menu-section-b0map:

B0 map
------

This menu is used to process the static magnetic field map B0 (in Hz) based on the phase difference between two echoes in a gradient echo sequence.
The PySisyphe code was adapted from the `erwin package <https://github.com/lamyj/erwin>`_.
See https://qmrlab.org/mooc/b0-mapping/ for theory.

.. admonition:: Reference

	`Article <https://pmc.ncbi.nlm.nih.gov/articles/PMC2896433/>`_: An in vivo automated shimming method taking into account shim current constraints. Wen H. & Jaffer F.A. Magn Reson Med. 1995 34(6),pp.898-904.

Use the **Two phase volumes** :ref:`widgets-section-multi-file` widget to select two PySisyphe volumes acquired with two echo times (.xvol, with *PHASE* sequence attribute). Echo times can be extracted automatically if DICOM conversion files are associated with PySisyphe volumes (same filename with .xdcm extension). If this is not the case, edit the echo time values for each volume using the spin boxes located in the column to the right of the file names. You can also load echo times from a file (supported formats .txt, .csv or numpy .npy) by clicking the **Load parameter** button and then selecting the **EchoTime** menu. Echo times are saved by clicking the **Save parameter** and then selecting the **EchoTime** menu.

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). B0 map is not processed in background voxels of the mask. This field is optional and may be left blank.

Toggle **B0 map...** button to show/hide parameters:

- Check the box **Rescale phase signal** to rescale the phase volume signal. This option ensures that the scalar range of the phase images lies between -π and +π.
- The B0 map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute B0 map.

Left-click **Close** button to exit dialog box.

Sample volumes can be downloaded from the :ref:`menu-section-download` to test this processing.

.. _menu-section-b1map:

B1 map
------

This menu is used to process B1 radiofrequency (RF) coil map from two gradient echo images using the double angle method (actual flip angle imaging AFI).
The PySisyphe code was adapted from the `MyRelax package <https://github.com/fragrussu/MyRelax>`_.
See https://qmrlab.org/mooc/b1-mapping/ for theory.

.. admonition:: Reference

	`Article <https://www.sciencedirect.com/science/article/abs/pii/S1064185883711332>`_: Mapping of the radiofrequency field. Insko E.K. & Bolinger L. J Magn Reson Imaging. 1993 Series A, 103:82-85.

Use the **Two spoiled gradient echo** :ref:`widgets-section-multi-file` widget to select two PySisyphe volumes (.xvol, with *MAGNITUDE* sequence attribute). Echo times and reptition times can be extracted automatically if DICOM conversion files are associated with PySisyphe volumes (same filename with .xdcm extension). If this is not the case, edit the echo time and repetition time values for each volume using the spin boxes located in the column to the right of the file names. You can also load echo and repetition times from a file (supported formats .txt, .csv or numpy .npy) by clicking the **Load parameter** button and then selecting the **EchoTime**/**RepetitionTime** menu. Echo and repetition times are saved by clicking the **Save parameter** and then selecting the **EchoTime**/**RepetitionTime** menu.

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). B1 map is not processed in background voxels of the mask. This field is optional and may be left blank.

Toggle **B1 map...** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe magnitude volumes (default *No*, no automatic mask). This field is ignored if an **Analysis mask** is provided. The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- Set the **flip angle** (in degrees) of the gradient echo images.
- The B1 map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields. 

Left-click **Execute** button to compute B1 map.

Left-click **Close** button to exit dialog box.

.. _menu-section-t1map:

T1 map
------

This menu is used to process voxel-wise mono-exponential T1 fitting for variable flip angle (VFA) gradient echo images.
The PySisyphe code was adapted from the `MyRelax package <https://github.com/fragrussu/MyRelax>`_.
See https://qmrlab.org/mooc/t1-mapping/ for theory.

.. admonition:: Reference

	`Book <http://qmri.org/>`_: Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

Use the **Volumes with variable TR (VTR) or variable flip angles (VFA)** :ref:`widgets-section-multi-file` widget to select PySisyphe volumes (.xvol, with *MAGNITUDE* sequence attribute). Echo time/reptition time/flip angle values can be extracted automatically if DICOM conversion files are associated with PySisyphe volumes (same filename with .xdcm extension). If this is not the case, edit the echo time/repetition time/flip angle values for each volume using the spin boxes located in the column to the right of the file names. You can also load echo time/repetition time/flip angle from a file (supported formats .txt, .csv or numpy .npy) by clicking the **Load parameter** button and then selecting the **EchoTime**/**RepetitionTime**/**FlipAngle** menu. Echo time/repetition time/flip angle are saved by clicking the **Save parameter** and then selecting the **EchoTime**/**RepetitionTime**/**FlipAngle** menu.

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). T1 map is not processed in background voxels of the mask. This field is optional and may be left blank.

Use the **B1 map** :ref:`widgets-section-multi-file` widget to select a B1 map PySisyphe volume (.xvol, with *B1 MAP* sequence attribute). This field is optional and may be left blank.

Toggle **T1 map...** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe magnitude volumes (default *No*, no automatic mask). This field is ignored if an **Analysis mask** is provided. The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- Select the **Fitting method**: *linear* (default), *non linear*
- The T1 map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute T1 map.

Left-click **Close** button to exit dialog box.

Sample volumes can be downloaded from the :ref:`menu-section-download` to test this processing.

.. _menu-section-t2map:

T2 map
------

This menu is used to process voxel-wise mono-exponential or bi-exponential T2/T2* fitting on gradient echo images at variable echo times.
The PySisyphe code was adapted from the `MyRelax package <https://github.com/fragrussu/MyRelax>`_.
See https://qmrlab.org/mooc/t2-mapping/ for theory.

.. admonition:: Reference

	Mono-exponential signal model  = S0 * exp(-TE/T2)
	
	Bi-exponential signal model    = S0 * f * exp(-TE/T2l) + S0 * (1 - f) * exp(-TE/T2s)

	- TE, echo time
	- S0, signal for zero TE
	- T2/T2* tissue
	- T2l, T2/T2* of the slowly-decaying water
	- T2s (T2s <= T2l), T2/T2* of the fast-decaying water
	- f signal fraction of the slowly-decaying water

	Usual brain values:

	- T2* gray matter   48.5 +/- 12.1 ms
	- T2* white matter  67.6 +/- 11.0 ms
	- T2 gray matter    96.1 +/- 9.1 ms
	- T2 white matter   109.8 +/- 11.4 ms

	`Book <http://qmri.org/>`_: Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

Use the **Volumes at variable echo times** :ref:`widgets-section-multi-file` widget to select PySisyphe volumes acquired with multiple echo times (.xvol, with *MAGNITUDE* sequence attribute). Echo times can be extracted automatically if DICOM conversion files are associated with PySisyphe volumes (same filename with .xdcm extension). If this is not the case, edit the echo time values for each volume using the spin boxes located in the column to the right of the file names. You can also load echo times from a file (supported formats .txt, .csv or numpy .npy) by clicking the **Load parameter** button and then selecting the **EchoTime** menu. Echo times are saved by clicking the **Save parameter** and then selecting the **EchoTime** menu.

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). T2 map is not processed in background voxels of the mask. This field is optional and may be left blank.

Toggle **T2 map...** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe magnitude volumes (default *No*, no automatic mask). This field is ignored if an **Analysis mask** is provided. The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- Select the **Fitting model**, mono or bi-exponential.
- Select the **Fitting method**: *linear* (default), *non linear*. This field is only used for the mono-exponential fitting. The bi-exponential fitting algorithm is always non-linear and uses the Limited-memory Broyden-Fletcher-Goldfarb-Shanno L-BFGS optimization algorithm.
- The T2 map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute T2 map.

Left-click **Close** button to exit dialog box.

Sample volumes can be downloaded from the :ref:`menu-section-download` to test this processing.

.. _menu-section-t2pmap:

T2' map
-------

This menu is used to process T2' from quantitative T2 and T2* maps.
The PySisyphe code was adapted from the `MyRelax package <https://github.com/fragrussu/MyRelax>`_.

.. admonition:: Reference

	`Article <https://pmc.ncbi.nlm.nih.gov/articles/PMC8128565/>`_: Age-dependent normal values of T2* and T2' in brain parenchyma. Siemonsen  S., Finsterbusch J., Matschke J., Lorenzen A., Ding X.-Q., Fiehler J. AJNR Am J Neuroradiol. 2008 May;29(5):950-955.

Use the **T2 map(s)** :ref:`widgets-section-multi-file` widget to select T2 map PySisyphe volume(s) (.xvol, with *T2 MAP* sequence attribute).

Use the **T2star map(s)** :ref:`widgets-section-multi-file` widget to select T2* map PySisyphe volume(s) (.xvol, with *T2star MAP* sequence attribute).

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). T2' map is not processed in background voxels of the mask. This field is optional and may be left blank.

The PySisyphe volumes located at the same row number in the three previous widgets must have the same field of view, the same space/transform ID, and be acquired from the same patient.

Toggle **T2' map...** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe T2/T2* map volumes (default *No*, no automatic mask). This field is ignored if an **Analysis mask** is provided. The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- The T2' map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute T2' map(s).

Left-click **Close** button to exit dialog box.

.. _menu-section-mtrmap:

MTR map
-------

This menu is used to process Magnetization Transfer Ratio (MTR) from MT "on" and MT "off" acquisitions.
The PySisyphe code was adapted from the `MyRelax package <https://github.com/fragrussu/MyRelax>`_.
See https://qmrlab.org/mooc/magnetization-transfer-imaging/ for theory.

.. admonition:: Reference

	MTR = 100.0 * (MToff - MTon) / MToff

	`Article <https://onlinelibrary.wiley.com/doi/10.1002/mrm.20605>`_: T1, T2 relaxation and magnetization transfer in tissue at 3T. Stanisz G.J. Magn Reson Med. 2005 54:507-512.

Use the **Magnetization transfer Off volume(s)** :ref:`widgets-section-multi-file` widget to select PySisyphe volume(s) (.xvol, with *MTR* sequence attribute).

Use the **Magnetization transfer On volume(s)** :ref:`widgets-section-multi-file` widget to select PySisyphe volume(s) (.xvol,  with *MTR* sequence attribute).

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). MTR map is not processed in background voxels of the mask. This field is optional and may be left blank.

The PySisyphe volumes located at the same row number in the three previous widgets must have the same field of view, the same space/transform ID, and be acquired from the same patient.

Toggle **MTR map...** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe MTR volumes (default *No*, no automatic mask). This field is ignored if an **Analysis mask** is provided. The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- The MTR map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute MTR map(s).

Left-click **Close** button to exit dialog box.

.. _menu-section-qsmmap:

QSM map
-------

This menu is used to process Quantitative Susceptibility Mapping (QSM).
The PySisyphe code was adapted from the `TGVQSM package <https://www.neuroimaging.at/pages/qsm.php>`_.

.. admonition:: Reference

	`Article <https://www.sciencedirect.com/science/article/abs/pii/S1053811915001421?via%3Dihub>`_: Fast Quantitative Susceptibility Mapping using 3D EPI and Total Generalized Variation. Langkammer C., Bredies K., Poser B.A., Barth M., Reishofer G. Fan A.P., Bilgic B., Fazekas F., Mainero C., Ropele S. Neuroimage. 2015 May 1;111:622-30

Use the **Phase volume(s)** :ref:`widgets-section-multi-file` widget to select gradient echo PySisyphe volume(s) (.xvol, with *PHASE* sequence attribute). Echo time/Magnetic field strength values can be extracted automatically if DICOM conversion files are associated with PySisyphe volumes (same filename with .xdcm extension). If this is not the case, edit the echo time/Magnetic field strength values for each volume using the spin boxes located in the column to the right of the file names. You can also load echo time/Magnetic field strength values from a file (supported formats .txt, .csv or numpy .npy) by clicking the **Load parameter** button and then selecting the **EchoTime**/**MagneticFieldStrength** menu. Echo time/Magnetic field strength values are saved by clicking the **Save parameter** and then selecting the **EchoTime**/**MagneticFieldStrength** menu.

Use the **Analysis mask** :ref:`widgets-section-multi-file` widget to select a PySisyphe volume used as mask (.xvol, with *MASK* sequence attribute). QSM map is not processed in background voxels of the mask. This field is optional and may be left blank.

The PySisyphe volumes located at the same row number in the two previous widgets must have the same field of view, the same space/transform ID, and be acquired from the same patient.

Toggle **QSM map...** button to show/hide parameters:

- Set the **Number of iterations** of the Total Generalized Variation (TGV) algorithm (default 1000).
- Check the box **Rescale phase signal** to rescale the phase volume signal. This option ensures that the scalar range of the phase images lies between -π and +π.
- The QSM map is saved with the original file name prefixed and/or suffixed with the strings edited in the **prefix** and **suffix** fields.

Left-click **Execute** button to compute QSM map(s).

Left-click **Close** button to exit dialog box.

Sample volumes can be downloaded from the :ref:`menu-section-download` to test this processing.

.. _menu-section-asl:

ASL perfusion
-------------

This menu is used to process Cerebral Blood Flow (CBF) processing from Arterial Spin Labeling (ASL) series.
The PySisyphe code was adapted from the `ASL_processing package <https://github.com/SaraDupont/ASL_processing>`_ and `erwin package <https://github.com/lamyj/erwin>`_.
See https://radiologykey.com/arterial-spin-labeled-mr-perfusion-imaging-techniques/ for theory.

.. admonition:: Reference

	`Article <https://onlinelibrary.wiley.com/doi/10.1002/mrm.10211>`_: Comparison of quantitative perfusion imaging using arterial spin labeling at 1.5 and 4.0 Tesla. Wang J, Alsop DC, Li L, Listerud J., Gonzalez-At J.B., Schnall M.D., Detre J.A. Magn Reson Med. 2002 Aug;48(2):242-54.

	`Article <https://onlinelibrary.wiley.com/doi/10.1002/jmri.22678>`_: Correcting for the echo-time effect after measuring the cerebral blood flow by arterial spin labeling. Foucher J.R., Roquet D., Marrer C., Pham B.T., Gounot D. J Magn Reson Imaging. 2011 Oct;34(4):785-90.

	`Article <https://pmc.ncbi.nlm.nih.gov/articles/PMC10365107/>`_: A Beginner's Guide to Arterial Spin Labeling (ASL) Image Processing. Clement P., Petr J., Dijsselhof M.B.J., Padrela B., Pasternak M., Dolui S., Jarutyte L., Pinter N., Hernandez-Garcia L., Jahn A., Kuijer J.P.A., Barkhof F., Mutsaerts H.J.M., Keil V.C. Front Radiol. 2022 Jun 14:2:929533.

	`Article <https://onlinelibrary.wiley.com/doi/10.1002/mrm.24550>`_: In vivo blood T1 measurements at 1.5 T, 3 T, and 7 T. Zhang X., Petersen E.T., Ghariq E., De Vis J.B., Webb A.G., Teeuwisse W.M., Hendrikse J. van Osch M.J.P. Magn Reson Med. 2013 70:1082–1086.

Use the **ASL multi-component volume(s)** :ref:`widgets-section-multi-file` widget to select multicomponent PySisyphe ASL series volume(s) (.xvol, with *ASL* sequence attribute). ASL sequences typically include a volume acquired without saturation pulses, referred to as M0, and several volumes acquired after applying saturation pulses. All of these volumes must be combined into a multi-component volume (See :ref:`menu-section-join`).

Toggle **ASL** button to show/hide parameters:

- Select an algorithm from the **Automatic masking** combobox to process a mask from the PySisyphe ASL volumes (default *No*, no masking). The following algorithms are available: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_.
- Set the **Gaussian smoothing FWHM** (mm), full width at hall maximum of the gaussian kernel in mm used to smooth ASL images before CBF processing (default 0.0, no smoothing)
- Set the type of ASL **Sequence**: pulsed ASL or pseudo-continuous ASL
- Set the **M0 index**, index of the M0 volume, acquired without saturation pulses, in the multi-component ASL volume (default 0, first component)
- Set the **Label duration** in ms of the labeling sequence (default 1800). Typically 700-900 ms in pulsed ASL and 1800-2000 ms in pseudo-continuous ASL.
- Set the **Post labeling delay** in ms of the labeling sequence (default 1800). Typically 1600-2000 ms in pulsed ASL and 1800-2000 ms in pseudo-continuous ASL.
- Set the **TE**, echo time in ms of the ASL series. It is used for magnetization correction. This value can be taken from a DICOM file of the perfusion time series using the widget **Get TR/TE from dicom file** above.
- Set the **TR**, repetition time in ms of the ASL series. It is used to correct intensity of proton density weighted M0 volume if the repetition time is too short. This value can be taken from a DICOM file of the perfusion time series using the widget **Get TR/TE from dicom file** above.
- Set the **Blood brain partition coefficient** value in mL/g eq. L/Kg (default 0.9). Estimated to 0.9 mL/g in the global brain parenchyma (`Wang J et al <https://onlinelibrary.wiley.com/doi/10.1002/mrm.10211>`_ and `Foucher JR et al <https://onlinelibrary.wiley.com/doi/10.1002/jmri.22678>`_, 0.98 mL/g in gray matter (`Foucher JR et al <https://onlinelibrary.wiley.com/doi/10.1002/jmri.22678>`_), 0.81 mL/g in white matter (`Foucher JR et al <https://onlinelibrary.wiley.com/doi/10.1002/jmri.22678>`_).
- Set the **Labeling efficiency** value (default 0.98). Estimated to 0.95 in `Wang J et al <https://onlinelibrary.wiley.com/doi/10.1002/mrm.10211>`_ and `Foucher JR et al <https://onlinelibrary.wileyhttps://onlinelibrary.wiley.com/doi/10.1002/mrm.10211.com/doi/10.1002/jmri.22678>`_
- Set the **T1 relaxation time of blood** value in ms (default 1650). Estimated to ~1200–1350 ms 1.5T, ~1600–1700 ms 3.0T, ~2100–2300 ms 7.0T (`Zhang et al <https://onlinelibrary.wiley.com/doi/10.1002/mrm.24550>`_).

Left-click **Execute** button to compute ASL map(s).

Left-click **Close** button to exit dialog box.

.. _menu-section-dsc:

Dynamic susceptibility contrast
-------------------------------

This menu is used to compute dynamic susceptibility contrast MR perfusion analysis.

The following maps are produced: **cerebral blood flow** (CBF in ml/min/100g), **cerebral blood volume** (CBV in ml/100g), **mean transit time** (MTT in s), *leakage volume* (LKV in ml/100g), **time to pic** (TTP in s), **time to bolus arrival** (TMAX in s), **signal recovery** (SR) and **percentage signal recovery** (PSR).

The DSC maps are processed using PyPeT (Python Perfusion Tool) for which the code is openly available on GitHub https://github.com/Marijn311/CT-and-MR-Perfusion-Tool. This package was validated through a visual and quantitative comparison with reference perfusion maps generated by FDA-approved, commercial softwares (Iconbrain CVA, iSchemaView Rapid, UniToBrain and Olea Sphere 3.0).

.. admonition::
	References
	
	`Reference1 <https://arxiv.org/pdf/2511.13310>`_: PyPeT: A python perfusion tool for automated quantitative brain CT and MR perfusion. Borghouts M. & Su R. arXiv:2511.13310

	`Reference2 <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0168174>`_: Alterations of the blood-brain barrier and regional perfusion in tumor development: MRI insights from a rat C6 glioma model. Monika Huhndorf M., Moussavi A., Kramann N., Will O., Hattermann K., Stadelmann C., Jansen O., Boretius S. PLoS One 2016 Dec 22;11(12):e0168174. 

Use the :ref:`widgets-section-single-file` widget at the top, to select a PySisyphe **DSC-MR multi-component volume(s)** (.xvol).

The Dynamic susceptibility contrast parameters are as follows:

- Set the **TR** parameter, repetition time of the dynamic susceptibility contrast MR perfusion images, in milliseconds. This value can be taken from a DICOM file of the perfusion time series using the widget **Get TR/TE from dicom file** above.
- Set the **TE** parameter, echo time of the dynamic susceptibility contrast MR perfusion images, in milliseconds.
- Select the thresholding algorithm used for mask processing from the **Masking algorithm** combobox. PySisyphe provides the following algorithms from the SimpleITK library: `Huang <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1HuangThresholdImageFilter.html>`_, Mean, `Otsu <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1OtsuThresholdImageFilter.html>`_, `Renyi <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1RenyiEntropyThresholdImageFilter.html>`_, `Yen <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1YenThresholdImageFilter.html>`_, `Li <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LiThresholdImageFilter.html>`_, `Shanbhag <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ShanbhagThresholdImageFilter.html>`_, `Triangle <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1TriangleThresholdImageFilter.html>`_, `Intermodes <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IntermodesThresholdImageFilter.html>`_, `Maximumentropy <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MaximumEntropyThresholdImageFilter.html>`_, `Kittler <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1KittlerIllingworthThresholdImageFilter.html>`_, `Isodata <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1IsoDataThresholdImageFilter.html>`_, `Moments <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1MomentsThresholdImageFilter.html>`_ (default Huang)
- Set the **Baseline indices (first, last)** parameters. This is the range (start and end) of volume indices used as baseline signal to calculate contrast concentration curves.
- Set the **Number of AIF voxels** parameter, number of voxels used to calculate arterial input function (mean curve of these voxels)
- Check **AIF dialog** to determine whether or not to display a dialog box for selecting voxels that will be used to compute the arterial input function.
- Check **Smoothing** to determine whether or not to smooth contrast concentration curves.
- Check **Signal recovery maps processing** to determine whether or not to calculate signal recovery (SR) and percentage signal recovery (PSR) maps.
- Check **DSC maps processing** to determine whether or not to calculate cerebral blood flow (CBF), cerebral blood volume (CBV), mean transit time (MTT), time to pic (TTP), time to bolus arrival (TMAX)
- Check **Leakage** to determine whether or not to calculate leakage volume (LKV).

Left-click **Execute** button to compute perfusion maps. 

If the AIF dialog parameter is checked, an **arterial input function** dialog box will be displayed first:

- The left side shows a mean image from the time series of perfusion-weighted images in a :ref:`page-sliceview` with a cross-shaped cursor. Left-clicking on the slice view moves the cursor to the current position of the mouse.
- The voxels considered for calculating the AIF curve are selected based on three criteria: shortest time to pic, highest peak amplitude, and minimal curve width. 
- The right side shows a chart of the time series signal curves. The mean brain curve is shown in blue, the curve of the voxel at the current cursor position is shown in green, the current AIF curve is shown in red, and the curves of each AIF voxel are shown in gray. A gray curve can be selected by left-clicking, the cursor is centered on the voxel associated with this curve, which is then drawn in green.
- A button bar is displayed below the chart:

	- Left-click **Add** button to add the current voxel, under the cross-shaped cursor, to the AIF calculation. The AIF curve is then updated.
	- Left-click **Remove** button to remove the current voxel, under the cross-shaped cursor, from the AIF calculation. The AIF curve is then updated.
	- Left-click **Clear** button to remove all voxels selected for AIF calculation. The mean AIF curve and the AIF voxel curves are then removed from the chart.
	- Left-click **Save bitmap** button to save the chart as a bitmap file (supported bitmap formats BMP, JPG, PNG, TIFF and SVG)
	- Left-click **Clipboard** button to copy the chart to the clipboard.
	- Left-click **Screenshots** button to copy the chart to the :ref:`page-screenshots`.
	- Left-click **Save ROI** button to save the selected voxels for the AIF calculation as a PySisyphe ROI (.xroi).
	- Left-click **Save Dataset** button to save all the curves displayed in the chart as table (supported formats CSV, JSON, LATEX, TXT, Excel XLSX, Pysisyphe XSHEET).
	
- Left-click **OK** button to calculate perfusion maps. This is a computationally intensive process that may take more than 30 minutes depending on the selected parameters.
- Left-click **Cancel** button to exit dialog box without calculating the perfusion maps.

Perfusion maps are saved with the original file name, which is suffixed with the map acronym (i.e. cbf, cbv, mtt, ttp, tmax, lkv, sr, psr).
 
Left-click **Close** button to exit dialog box.

Sample volumes can be downloaded from the :ref:`menu-section-download` to test this processing.