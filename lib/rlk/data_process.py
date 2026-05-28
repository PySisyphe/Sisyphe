# import os
import numpy as np
# import nibabel as nib
import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

### IMAGE PRE-PROCESSING 

def crop_sample(volume, thr=8):
    # crop x-axial                                      
    v_min, v_max    = 0, 0                                        
    for i in range(np.shape(volume)[0]):
        x_axis          = volume[i,:,:]
        x_num_nonzero   = len(np.where(x_axis>0)[0])
        if x_num_nonzero > 0 and v_min == 0:
            v_min   = i
        elif x_num_nonzero > 0 and v_min > 0:
            v_max   = i           
    if v_min%thr != 0:
        v_min       = v_min-(v_min%thr)
    if v_max%thr != 0:
        v_max       = v_max+(thr-(v_max%thr))   
    x_min, x_max    = v_min, v_max

    # crop y-axial
    v_min, v_max    = 0, 0
    for j in range(np.shape(volume)[1]):
        y_axis      = volume[:,j,:]
        num_nonzero = len(np.where(y_axis>0)[0])
        if num_nonzero > 0 and v_min == 0:
            v_min   = j
        elif num_nonzero > 0 and v_min > 0:
            v_max   = j
    if v_min%thr != 0:
        v_min       = v_min-(v_min%thr)
    if v_max%thr != 0:
        v_max       = v_max+(thr-(v_max%thr))
    y_min, y_max    = v_min, v_max

    # crop z-axial
    v_min, v_max    = 0, 0
    for k in range(np.shape(volume)[2]):
        z_axis      = volume[:,:,k]
        num_nonzero = len(np.where(z_axis>0)[0])
        if num_nonzero > 0 and v_min == 0:
            v_min   = k
        elif num_nonzero > 0 and v_min > 0:
            v_max   = k
    if v_min%thr != 0:
        v_min       = v_min-(v_min%thr)
    if v_max%thr != 0:
        v_max       = v_max+(thr-(v_max%thr))

    if v_max > np.shape(volume)[2]:
        pad         = v_max-np.shape(volume)[2]
        v_max       = v_max - pad
        v_min       = v_min - pad
    if v_min < 0:
        v_min   = 6
    z_min, z_max    = v_min, v_max

    reshape         = x_min, x_max, y_min, y_max, z_min, z_max
    return volume[x_min:x_max,y_min:y_max,z_min:z_max], reshape

def normalize_volume(volume):
    nonzero_volume  = volume[volume > 0]
    mean            = nonzero_volume.mean()
    std             = nonzero_volume.std()
    volume          = (volume - mean) / std
    return volume

class BrainSegmentationDataset(Dataset):

    def __init__(self, image_data):
        images      = []

        # read images
        # row_image   = nib.load(image_data).get_fdata()
        # print("\nNIfTI file   :: {}".format(os.path.abspath(image_data)))
        # print("Image shape  :: {}".format(np.shape(row_image)))
        # print("Pre-processing ...\n")
        # cropping
        # proc_image,_= crop_sample(row_image)
        # < Revision 22/05/2026
        # proc_image, _ = crop_sample(image_data)
        proc_image, self._bbox = crop_sample(image_data)
        # Revision 22/05/2026 >
        # normalize
        proc_image  = normalize_volume(proc_image)
        #stack
        images.append(proc_image)
        self.images = images

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image       = self.images[idx]
        image       = torch.from_numpy(image)
        image       = torch.unsqueeze(image,0)
        return image

    # < Revision 22/05/2026
    # add getBBox method
    def getBBox(self):
        return self._bbox
    # Revision 22/05/2026 >

def data_loaders(img_data):
    dataset_test    = datasets(img_data)
    loader_test     = DataLoader(
                                dataset_test,
                                batch_size=1,
                                shuffle=False,
                                drop_last=False
                                )
    return loader_test

def datasets(images):
    test            = BrainSegmentationDataset(image_data=images)
    return test