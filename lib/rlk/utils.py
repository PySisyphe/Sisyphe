import os
import torch
import numpy as np
import nibabel as nib
from scipy.ndimage import label, generate_binary_structure

from .data_process import crop_sample


def numpy_convert(img):  
    img = torch.squeeze(img,0)
    img = torch.squeeze(img,0)
    img = img.detach().cpu().numpy()
    return img


def tensor_convert(img):
    img = torch.from_numpy(img).float()
    img  = torch.unsqueeze(img,0)
    img  = torch.unsqueeze(img,0)
    return img


def label_thr(labels, thr):
    labels  = numpy_convert(labels)

    s                       = generate_binary_structure(3,3)
    label_array, label_num  = label(labels, structure=s)
    count                   = []
    for i in range(1, label_num+1):
        target_len          = len(label_array[np.where(label_array==i)])
        count.append(target_len)

    for j in range(0, len(count)):
        if count[j] < thr:
            label_array = np.where(label_array==j+1, 0, label_array)

    labels  = np.where(label_array>=1.0, 1.0, 0.0)
    labels  = labels.astype(np.float32)

    labels  = tensor_convert(labels)
    return labels


def save_prediction(results, row_data, output_path, name):
    # Resolve location where data should be written
    if not os.path.exists(output_path):
        raise IOError("Data path, {}, could not be resolved".format(output_path))

    # load row data
    row_data        = nib.load(row_data)
    # noinspection PyUnresolvedReferences
    row_array       = row_data.get_fdata()
    _, reshape      = crop_sample(row_array)

    # padding
    filled_result   = np.zeros_like(row_array)
    filled_result[reshape[0]:reshape[1], reshape[2]:reshape[3], reshape[4]:reshape[5]]  = results

    # Convert numpy array to NIfTI
    # noinspection PyUnresolvedReferences
    out_nifti       = nib.Nifti1Image(filled_result, row_data.affine)

    # Save segmentation to disk
    file_name       = name.split('.nii')[0] 
    out_file        = file_name + "_BMs.nii.gz"
    print("Save output  :: {}".format(os.path.join(output_path, out_file)))
    nib.save(out_nifti, os.path.join(output_path, out_file))
