"""
Feature Extraction Module for Radiomics
Matches the EXACT notebook preprocessing for consistent predictions
"""

import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from skimage import filters, morphology, exposure, measure, segmentation
from scipy import ndimage
import SimpleITK as sitk
from radiomics import featureextractor
import pandas as pd


class RadiomicsFeatureExtractor:
    """Extract radiomics features from brain scan images"""
    
    def __init__(self):
        """Initialize the radiomics feature extractor"""
        # PyRadiomics parameters - MUST include shape for the 6 key features
        params = {
            'imageType': {'Original': {}},
            'featureClass': {
                'shape': {},  # CRITICAL for Elongation, MajorAxisLength, MinorAxisLength
                'firstorder': {},
                'glcm': {},
                'glrlm': {},
                'glszm': {},
                'gldm': {}
            },
            'setting': {'binWidth': 25, 'normalize': True}
        }
        self.extractor = featureextractor.RadiomicsFeatureExtractor(**params)
        self.TARGET_SHAPE = (256, 256)
    
    def preprocess_image(self, image_path_or_array, label='unknown'):
        """
        Preprocess image using WATERSHED segmentation matching the notebook.
        The mask should capture the BRIGHT tumor regions, not the whole brain.
        Returns: (normalized_image, mask, name)
        """
        try:
            # Load image
            if isinstance(image_path_or_array, (str, Path)):
                img = Image.open(image_path_or_array).convert('L')
                arr = np.array(img, dtype=np.float32)
                name = Path(image_path_or_array).stem
            else:
                arr = np.array(image_path_or_array, dtype=np.float32)
                if len(arr.shape) == 3:
                    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
                name = 'uploaded_image'
            
            # Resize to target shape
            if arr.shape != self.TARGET_SHAPE:
                arr = cv2.resize(arr, self.TARGET_SHAPE, interpolation=cv2.INTER_LINEAR)
            
            # Normalize image (matching notebook)
            m, s = arr.mean(), arr.std()
            if s < 1e-6:
                s = 1.0
            imgn = (arr - m) / s
            
            # Convert to uint8 for processing
            im_uint8 = exposure.rescale_intensity(imgn, out_range=(0, 255)).astype(np.uint8)
            
            # Step 1: Create brain mask using Otsu threshold
            thr = filters.threshold_otsu(im_uint8)
            brain = im_uint8 > thr
            brain = morphology.binary_closing(brain, morphology.disk(3))
            brain = morphology.remove_small_objects(brain, min_size=500)
            
            # Step 2: WATERSHED segmentation for tumor detection (matching notebook)
            # Apply brain mask to image
            masked = im_uint8 * brain
            
            # Create markers for watershed
            markers = np.zeros_like(masked, dtype=np.int32)
            
            # Background markers: low intensity areas within brain
            if np.any(brain):
                p30 = np.percentile(masked[brain], 30)
                p85 = np.percentile(masked[brain], 85)
                
                # Mark background (darker regions)
                markers[masked < p30] = 1
                
                # Mark foreground (bright regions - potential tumor)
                markers[masked > p85] = 2
            
            # Apply watershed
            mask = segmentation.watershed(masked, markers, mask=brain)
            
            # The tumor/ROI is label 2 (bright regions)
            mask = (mask == 2).astype(np.uint8)
            
            # Clean up the mask
            mask = morphology.binary_opening(mask, morphology.disk(2)).astype(np.uint8)
            mask = morphology.binary_closing(mask, morphology.disk(3)).astype(np.uint8)
            mask = morphology.remove_small_objects(mask.astype(bool), min_size=20).astype(np.uint8)
            
            # If mask is too small or empty, fall back to brain mask
            # (this happens for "notumor" cases where there's no bright tumor region)
            if mask.sum() < 100:
                mask = brain.astype(np.uint8)
            
            return imgn.astype(np.float32), mask, name
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_mask_visualization(self, image_path_or_array, label='unknown'):
        """
        Get the original image with mask overlay for visualization
        Returns: (original_image, mask, overlay_image) as numpy arrays
        """
        try:
            # Load original image for display
            if isinstance(image_path_or_array, (str, Path)):
                img = Image.open(image_path_or_array)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                original = np.array(img)
            else:
                original = np.array(image_path_or_array)
                if len(original.shape) == 2:
                    original = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
            
            # Resize original to target shape
            original_resized = cv2.resize(original, self.TARGET_SHAPE)
            
            # Get mask from preprocessing
            result = self.preprocess_image(image_path_or_array, label)
            if result is None:
                return original_resized, None, original_resized
            
            imgn, mask, name = result
            
            # Create overlay visualization (RED for mask, matching notebook style)
            overlay = original_resized.copy()
            
            # Apply red color to mask region
            if mask.sum() > 0:
                # Create red overlay
                red_overlay = np.zeros_like(overlay)
                red_overlay[:, :, 0] = 255  # Red channel
                
                # Apply mask
                mask_3d = np.stack([mask, mask, mask], axis=-1).astype(bool)
                overlay = np.where(mask_3d, 
                                   (overlay * 0.5 + red_overlay * 0.5).astype(np.uint8),
                                   overlay)
                
                # Draw yellow contour
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(overlay, contours, -1, (255, 255, 0), 2)
            
            return original_resized, mask, overlay.astype(np.uint8)
            
        except Exception as e:
            print(f"Error creating mask visualization: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
    
    def extract_features(self, image_path_or_array, label='unknown'):
        """
        Extract radiomics features from an image
        Returns: Dictionary of features
        """
        try:
            # Preprocess image
            result = self.preprocess_image(image_path_or_array, label)
            if result is None:
                return None
            
            imgn, mask, name = result
            
            # Ensure mask has at least some pixels for feature extraction
            if mask.sum() < 10:
                print(f"Warning: Mask too small ({mask.sum()} pixels)")
                mask = np.ones_like(mask, dtype=np.uint8)
            
            print(f"Mask size: {mask.sum()} pixels")
            
            # Convert to SimpleITK format (3D with single slice)
            img_uint8 = exposure.rescale_intensity(imgn, out_range=(0, 255)).astype(np.uint8)
            sitk_img = sitk.GetImageFromArray(img_uint8[np.newaxis, :, :])
            sitk_mask = sitk.GetImageFromArray(mask[np.newaxis, :, :])
            
            # Extract features
            feats = self.extractor.execute(sitk_img, sitk_mask)
            
            # Build feature dictionary - include ALL features
            row = {}
            
            for k, v in feats.items():
                if isinstance(v, (int, float, np.number)):
                    row[k] = float(v)
                elif isinstance(v, np.ndarray) and v.size == 1:
                    row[k] = float(v.flat[0])
                elif isinstance(v, (list, tuple)) and len(v) > 0:
                    try:
                        row[k] = float(np.mean([float(x) for x in v if isinstance(x, (int, float, np.number))]))
                    except:
                        row[k] = 0.0
                else:
                    row[k] = 0.0
            
            row['image_name'] = name
            row['label'] = label
            
            # Debug: print key features
            key_features = [
                'diagnostics_Image-original_Mean',
                'diagnostics_Mask-original_VoxelNum',
                'diagnostics_Mask-original_VolumeNum',
                'original_shape_Elongation',
                'original_shape_MajorAxisLength',
                'original_shape_MinorAxisLength'
            ]
            print(f"\nKey features for {name}:")
            for f in key_features:
                val = row.get(f, 'NOT FOUND')
                print(f"  {f}: {val}")
            
            return row
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_features_batch(self, image_paths_or_arrays, labels=None):
        """
        Extract features from multiple images
        Returns: DataFrame with features
        """
        if labels is None:
            labels = ['unknown'] * len(image_paths_or_arrays)
        
        feature_rows = []
        for img, label in zip(image_paths_or_arrays, labels):
            row = self.extract_features(img, label)
            if row:
                feature_rows.append(row)
        
        if feature_rows:
            return pd.DataFrame(feature_rows)
        return pd.DataFrame()
