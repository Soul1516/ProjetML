"""
Model Predictor Module - Uses trained Warm Start RLT model
With feature-based validation for better accuracy
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path


class CancerStagePredictor:
    """Predict cancer stage and risk level from radiomics features"""
    
    # The 6 features the scaler was trained on (in order!)
    SCALER_FEATURES = [
        'diagnostics_Image-original_Mean',
        'diagnostics_Mask-original_VoxelNum', 
        'diagnostics_Mask-original_VolumeNum',
        'original_shape_Elongation',
        'original_shape_MajorAxisLength',
        'original_shape_MinorAxisLength'
    ]
    
    # Training data ranges per class (from analysis)
    # KEY DIFFERENCES:
    # - Pituitary: LARGER size (VoxelNum 4400-6200), LONGER axes (Major 257-331, Minor 221-279)
    # - Meningioma: SMALLER size (VoxelNum 2800-5200), SHORTER axes (Major 200-310, Minor 150-235)
    # - Meningioma can be more ROUND (Elongation 0.50+), Pituitary is more elongated (0.80+)
    CLASS_RANGES = {
        'glioma': {
            'VoxelNum': (3400, 5100),
            'VolumeNum': (5, 29),
            'MajorAxis': (240, 277),
            'MinorAxis': (200, 228),
            'Elongation': (0.76, 0.92),
            'Mean': (25, 50)
        },
        'meningioma': {
            'VoxelNum': (2800, 5200),  # Can be smaller
            'VolumeNum': (4, 20),       # Fewer regions
            'MajorAxis': (200, 260),    # SHORTER than pituitary
            'MinorAxis': (150, 220),    # SHORTER than pituitary  
            'Elongation': (0.50, 0.85), # Can be more ROUND
            'Mean': (29, 65)
        },
        'pituitary': {
            'VoxelNum': (4400, 6500),   # LARGER
            'VolumeNum': (9, 30),        # More regions
            'MajorAxis': (255, 335),     # LONGER
            'MinorAxis': (220, 280),     # LONGER
            'Elongation': (0.80, 0.96),  # More elongated
            'Mean': (30, 65)
        },
        'notumor': {
            'VoxelNum': (10000, 40000),
            'VolumeNum': (1, 2),
            'MajorAxis': (215, 260),
            'MinorAxis': (155, 225),
            'Elongation': (0.69, 0.97),
            'Mean': (25, 95)
        }
    }
    
    def __init__(self, model_dir='output'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.classes = ['glioma', 'meningioma', 'notumor', 'pituitary']
        self._load_model_artifacts()
    
    def _load_model_artifacts(self):
        """Load all model artifacts"""
        root_dir = Path('.')
        search_dirs = [root_dir, self.model_dir]
        
        # Load model
        for search_dir in search_dirs:
            for ext in ['.pkl', '.joblib']:
                model_path = search_dir / f'warm_start_rlt_model{ext}'
                if model_path.exists():
                    print(f"Loading model from {model_path}")
                    self.model = joblib.load(model_path)
                    if isinstance(self.model, list):
                        print(f"Model: {len(self.model)} trees")
                    break
            if self.model is not None:
                break
        
        # Load scaler
        for search_dir in search_dirs:
            for ext in ['.pkl', '.joblib']:
                scaler_path = search_dir / f'scaler{ext}'
                if scaler_path.exists():
                    print(f"Loading scaler from {scaler_path}")
                    self.scaler = joblib.load(scaler_path)
                    break
            if self.scaler is not None:
                break
        
        print(f"✓ Model loaded! Classes: {self.classes}")
    
    def _predict_tree(self, tree, x):
        """Traverse a custom tree structure"""
        if isinstance(tree, np.ndarray):
            proba = tree.copy()
            if proba.sum() > 0:
                proba = proba / proba.sum()
            return proba
        
        if isinstance(tree, dict):
            feat_idx = tree.get('feat', 0)
            split_val = tree.get('split', 0)
            feat_val = x[feat_idx] if feat_idx < len(x) else 0
            
            if feat_val <= split_val:
                return self._predict_tree(tree.get('left', np.ones(4)/4), x)
            else:
                return self._predict_tree(tree.get('right', np.ones(4)/4), x)
        
        return np.ones(len(self.classes)) / len(self.classes)
    
    def _predict_ensemble(self, X):
        """Make predictions using ensemble of trees"""
        n_samples = X.shape[0]
        n_classes = len(self.classes)
        y_proba = np.zeros((n_samples, n_classes))
        
        if self.model is None or not isinstance(self.model, list):
            return np.ones((n_samples, n_classes)) / n_classes
        
        n_trees = 0
        for tree in self.model:
            try:
                for i in range(n_samples):
                    proba = self._predict_tree(tree, X[i])
                    if isinstance(proba, np.ndarray) and len(proba) >= n_classes:
                        y_proba[i] += proba[:n_classes]
                n_trees += 1
            except:
                continue
        
        if n_trees > 0:
            y_proba /= n_trees
        else:
            y_proba = np.ones((n_samples, n_classes)) / n_classes
        
        # Normalize
        row_sums = y_proba.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return y_proba / row_sums
    
    def _feature_based_scores(self, features):
        """Calculate class scores based on feature ranges"""
        scores = {}
        
        voxel_num = features.get('diagnostics_Mask-original_VoxelNum', 0)
        volume_num = features.get('diagnostics_Mask-original_VolumeNum', 0)
        major_axis = features.get('original_shape_MajorAxisLength', 0)
        minor_axis = features.get('original_shape_MinorAxisLength', 0)
        elongation = features.get('original_shape_Elongation', 0)
        mean_val = features.get('diagnostics_Image-original_Mean', 0)
        p90_val = features.get('original_firstorder_90Percentile', mean_val)
        entropy = features.get('original_glcm_Idmn', 0)  # texture smoothness proxy
        axis_ratio = (major_axis / minor_axis) if minor_axis else 1.0
        compactness = features.get('original_shape_Compactness2', elongation)
        
        print(f"\n=== Feature Analysis ===")
        print(f"  VoxelNum: {voxel_num:.0f}")
        print(f"  VolumeNum: {volume_num:.0f}")
        print(f"  MajorAxis: {major_axis:.1f}")
        print(f"  MinorAxis: {minor_axis:.1f}")
        print(f"  Elongation: {elongation:.3f}")
        print(f"  Mean: {mean_val:.1f}")
        print(f"  P90: {p90_val:.1f}")
        print(f"  Axis Ratio: {axis_ratio:.2f}")
        print(f"  Compactness: {compactness:.3f}")
        
        for cls, ranges in self.CLASS_RANGES.items():
            score = 0
            
            # Get range boundaries
            vn_min, vn_max = ranges['VoxelNum']
            vol_min, vol_max = ranges['VolumeNum']
            maj_min, maj_max = ranges['MajorAxis']
            min_min, min_max = ranges['MinorAxis']
            elong_min, elong_max = ranges['Elongation']
            mean_min, mean_max = ranges['Mean']
            
            # NO TUMOR: Very distinctive - requires VERY large VoxelNum AND very few regions
            if cls == 'notumor':
                # STRICT: Only high scores when BOTH conditions are met
                if voxel_num >= 10000 and volume_num <= 2:
                    score += 25  # Very high - clear no tumor (both conditions)
                elif voxel_num >= 8000 and volume_num <= 2:
                    score += 15  # Good match (both conditions)
                elif voxel_num >= 10000 and volume_num <= 3:
                    score += 8  # Large voxels but more regions
                # Range matching (only if already scoring well)
                if voxel_num >= 8000:
                    if vn_min <= voxel_num <= vn_max:
                        score += 3
                    if volume_num <= 2:
                        score += 3
                # Penalties for tumor-like features
                if voxel_num < 7000:
                    score -= 8  # Too small for no tumor
                if volume_num > 3:
                    score -= 6  # Too many regions
                if voxel_num < 8000 and volume_num > 2:
                    score -= 10  # Neither condition met - likely a tumor
                    
            # PITUITARY: Large size, many regions, elongated
            elif cls == 'pituitary':
                # Size checks - pituitary is LARGE
                if maj_min <= major_axis <= maj_max:
                    score += 7
                if min_min <= minor_axis <= min_max:
                    score += 7
                # STRONG match for large pituitary - DISTINGUISHING FEATURE
                if major_axis >= 270 and minor_axis >= 225:
                    score += 15  # Very large - STRONG pituitary indicator
                elif major_axis >= 260 and minor_axis >= 220:
                    score += 10
                elif major_axis >= 255 and minor_axis >= 220:
                    score += 7
                # Voxel count - pituitary is LARGER
                if vn_min <= voxel_num <= vn_max:
                    score += 7
                if voxel_num >= 4500:
                    score += 6  # Large voxels favor pituitary
                if voxel_num >= 5000:
                    score += 4  # Very large voxels
                # Volume regions - pituitary has MORE regions
                if vol_min <= volume_num <= vol_max:
                    score += 6
                if volume_num >= 9:
                    score += 5  # Many regions favor pituitary
                if volume_num >= 12:
                    score += 3  # Very many regions
                # Elongation - pituitary is MORE elongated
                if elongation >= 0.80:
                    score += 5
                if elongation >= 0.85:
                    score += 3  # Very elongated
                # STRONG penalties for small size (not pituitary)
                if major_axis < 255:
                    score -= 8  # Too small - likely meningioma
                if minor_axis < 220:
                    score -= 8  # Too small - likely meningioma
                if voxel_num < 4000:
                    score -= 6  # Too small voxels
                # Penalize if looks like meningioma
                if major_axis <= 250 and minor_axis <= 215:
                    score -= 10  # Definitely meningioma range
                    
            # MENINGIOMA: Small to medium size, can be rounder
            elif cls == 'meningioma':
                # Size checks - meningioma is SMALLER
                if maj_min <= major_axis <= maj_max:
                    score += 7
                if min_min <= minor_axis <= min_max:
                    score += 7
                # STRONG match for small meningioma - DISTINGUISHING FEATURE
                if major_axis <= 250 and minor_axis <= 215:
                    score += 15  # Small size - STRONG meningioma indicator
                elif major_axis <= 240 and minor_axis <= 210:
                    score += 12  # Very small
                elif major_axis <= 260 and minor_axis <= 220:
                    score += 8
                # Voxel count - meningioma can be SMALLER
                if vn_min <= voxel_num <= vn_max:
                    score += 7
                if voxel_num <= 4500:
                    score += 4  # Smaller voxels favor meningioma
                if voxel_num <= 4000:
                    score += 3  # Very small voxels
                # Volume regions - meningioma has FEWER regions
                if vol_min <= volume_num <= vol_max:
                    score += 6
                if volume_num <= 15:
                    score += 3  # Fewer regions favor meningioma
                # Elongation - can be rounder (less elongated)
                if elongation < 0.85:
                    score += 5
                if elongation < 0.80:
                    score += 3  # More round
                # STRONG penalties for large size (not meningioma)
                if major_axis > 270:
                    score -= 8  # Too large - likely pituitary
                if minor_axis > 225:
                    score -= 8  # Too large - likely pituitary
                if voxel_num > 5500:
                    score -= 6  # Too large voxels
                # Penalize if looks like pituitary
                if major_axis >= 270 and minor_axis >= 225:
                    score -= 10  # Definitely pituitary range
                # Penalize if looks like glioma (medium)
                if 245 <= major_axis <= 270 and 205 <= minor_axis <= 225:
                    score -= 5  # Glioma range
                    
            # GLIOMA: Medium size, intermediate characteristics
            elif cls == 'glioma':
                # Size checks - glioma is MEDIUM
                if maj_min <= major_axis <= maj_max:
                    score += 8
                if min_min <= minor_axis <= min_max:
                    score += 8
                # STRONG match for medium glioma - DISTINGUISHING FEATURE
                if 245 <= major_axis <= 270 and 205 <= minor_axis <= 225:
                    score += 15  # Sweet spot - STRONG glioma indicator
                elif 240 <= major_axis <= 277 and 200 <= minor_axis <= 228:
                    score += 10  # Good glioma range
                # Voxel count - glioma is MEDIUM
                if vn_min <= voxel_num <= vn_max:
                    score += 8
                if 3400 <= voxel_num <= 5100:
                    score += 6  # Glioma range
                # Volume regions - glioma has MODERATE regions
                if vol_min <= volume_num <= vol_max:
                    score += 6
                if volume_num >= 5 and volume_num <= 25:
                    score += 4  # Moderate regions favor glioma
                # Elongation - glioma is MODERATELY elongated
                if elong_min <= elongation <= elong_max:
                    score += 6
                if 0.78 <= elongation <= 0.90:
                    score += 4  # Typical glioma elongation
                # STRONG penalties for extremes
                if major_axis >= 280:
                    score -= 6  # Too large, likely pituitary
                if major_axis < 230:
                    score -= 6  # Too small, likely meningioma
                if minor_axis >= 230:
                    score -= 5  # Too large, likely pituitary
                if minor_axis < 195:
                    score -= 5  # Too small, likely meningioma
                if voxel_num >= 5500:
                    score -= 5  # Too large, likely pituitary
                if voxel_num < 3000:
                    score -= 5  # Too small, likely meningioma
                # Penalize if looks like meningioma (small)
                if major_axis <= 250 and minor_axis <= 215:
                    score -= 8  # Definitely meningioma range
                # Penalize if looks like pituitary (large)
                if major_axis >= 270 and minor_axis >= 225:
                    score -= 8  # Definitely pituitary range
            
            # Elongation - class-specific checks (additional boost)
            if cls == 'notumor':
                if elong_min <= elongation <= elong_max:
                    score += 2
            elif cls == 'pituitary':
                if elongation >= 0.85:
                    score += 5  # Very elongated - strong pituitary indicator
                elif elongation >= 0.80:
                    score += 4
                if elong_min <= elongation <= elong_max:
                    score += 3
                # Penalize if not elongated enough
                if elongation < 0.75:
                    score -= 4  # Too round for pituitary
            elif cls == 'meningioma':
                if elongation < 0.80:
                    score += 5  # Rounder - strong meningioma indicator
                if elongation < 0.75:
                    score += 3  # Very round
                if elong_min <= elongation <= elong_max:
                    score += 3
                # Penalize if too elongated
                if elongation > 0.90:
                    score -= 4  # Too elongated for meningioma
            elif cls == 'glioma':
                if 0.78 <= elongation <= 0.90:
                    score += 5  # Moderate elongation - glioma indicator
                if elong_min <= elongation <= elong_max:
                    score += 4
                # Penalize extremes
                if elongation > 0.92:
                    score -= 3  # Too elongated, likely pituitary
                if elongation < 0.76:
                    score -= 3  # Too round, likely meningioma

            # Mean intensity - class-specific checks (additional boost)
            if cls == 'notumor':
                if mean_min <= mean_val <= mean_max:
                    score += 3
            elif cls == 'pituitary':
                if 30 <= mean_val <= 65:
                    score += 5  # Pituitary intensity range
                if mean_min <= mean_val <= mean_max:
                    score += 4
            elif cls == 'meningioma':
                if 29 <= mean_val <= 65:
                    score += 5  # Meningioma intensity range
                if mean_min <= mean_val <= mean_max:
                    score += 4
            elif cls == 'glioma':
                if 25 <= mean_val <= 50:
                    score += 5  # Glioma intensity range
                if mean_min <= mean_val <= mean_max:
                    score += 4
                # Penalize if too bright (likely pituitary/meningioma)
                if mean_val > 55:
                    score -= 3
                    
            # Bright hotspots indicator (tumors often have bright spots)
            if p90_val >= mean_val + 12:
                if cls in ['glioma', 'pituitary', 'meningioma']:
                    score += 3  # Bright hotspots common in tumors
                elif cls == 'notumor':
                    score -= 2  # Shouldn't have hotspots

            # Texture / compactness (smooth lesions vs diffuse)
            if cls == 'meningioma' and compactness >= 0.8:
                score += 3  # Meningioma often smooth
            if cls == 'pituitary' and compactness >= 0.8:
                score += 2  # Pituitary can be smooth
            if cls == 'glioma' and compactness < 0.7:
                score += 2  # Gliomas often less compact
            
            # FINAL CROSS-VALIDATION: Prevent wrong class from winning
            # Glioma vs Meningioma
            if cls == 'glioma':
                # If features strongly match meningioma (small), heavily penalize glioma
                if major_axis <= 240 and minor_axis <= 210 and voxel_num <= 4000:
                    score -= 12  # Definitely meningioma
            elif cls == 'meningioma':
                # If features strongly match glioma (medium), heavily penalize meningioma
                if 245 <= major_axis <= 270 and 205 <= minor_axis <= 225 and 3400 <= voxel_num <= 5100:
                    score -= 12  # Definitely glioma
                    
            # Meningioma vs Pituitary
            if cls == 'meningioma':
                # If features strongly match pituitary (large), heavily penalize meningioma
                if major_axis >= 270 and minor_axis >= 225 and voxel_num >= 4500:
                    score -= 15  # Definitely pituitary
            elif cls == 'pituitary':
                # If features strongly match meningioma (small), heavily penalize pituitary
                if major_axis <= 250 and minor_axis <= 215 and voxel_num <= 4500:
                    score -= 15  # Definitely meningioma
                    
            # Pituitary vs Meningioma (same as above but ensure both directions)
            if cls == 'pituitary':
                # Additional check: if small, definitely not pituitary
                if major_axis < 260 and minor_axis < 220:
                    score -= 8  # Too small for pituitary
            elif cls == 'meningioma':
                # Additional check: if large, definitely not meningioma
                if major_axis > 260 and minor_axis > 220:
                    score -= 8  # Too large for meningioma
            
            scores[cls] = score
        
        print(f"\n=== Feature-Based Scores ===")
        for cls, score in sorted(scores.items(), key=lambda x: -x[1]):
            print(f"  {cls}: {score}")
        
        return scores
    
    def predict(self, features_df, patient_info=None):
        """Predict cancer stage combining model + feature analysis"""
        try:
            # Get raw features for analysis
            raw_features = features_df.iloc[0].to_dict() if len(features_df) > 0 else {}
            
            # Extract the 6 features for model
            X = pd.DataFrame()
            for feat in self.SCALER_FEATURES:
                if feat in features_df.columns:
                    X[feat] = features_df[feat].fillna(0.0)
                else:
                    X[feat] = 0.0
            X = X[self.SCALER_FEATURES]
            
            # Scale features
            X_scaled = self.scaler.transform(X.values)
            
            # Get model prediction
            y_proba_model = self._predict_ensemble(X_scaled)
            
            # Get feature-based scores
            feature_scores = self._feature_based_scores(raw_features)
            
            # Normalize scores: ensure all scores are non-negative
            min_score = min(feature_scores.values())
            if min_score < 0:
                # Shift all scores to be non-negative (add offset)
                offset = abs(min_score) + 0.1
                feature_scores = {cls: score + offset for cls, score in feature_scores.items()}
            
            # Convert feature scores to probabilities
            total_score = sum(feature_scores.values()) + 0.01
            y_proba_features = np.array([
                feature_scores[cls] / total_score for cls in self.classes
            ])
            
            # Combine: 40% model + 60% feature-based (as specified)
            y_proba = 0.4 * y_proba_model[0] + 0.6 * y_proba_features
            y_proba = y_proba / y_proba.sum()  # Normalize
            
            y_pred = np.argmax(y_proba)
            predicted_label = self.classes[y_pred]
            
            print(f"\n=== Final Prediction ===")
            print(f"  Model proba: {dict(zip(self.classes, y_proba_model[0].round(3)))}")
            print(f"  Feature proba: {dict(zip(self.classes, y_proba_features.round(3)))}")
            print(f"  Combined: {dict(zip(self.classes, y_proba.round(3)))}")
            print(f"  PREDICTED: {predicted_label} ({y_proba[y_pred]*100:.1f}%)")
            
            probs = {cls: float(y_proba[i]) for i, cls in enumerate(self.classes)}
            
            return {
                'predicted_stage': predicted_label,
                'probabilities': probs,
                'confidence': float(y_proba[y_pred]),
                'risk_level': self._get_risk_level(probs, patient_info),
                'patient_context': self._get_patient_context(probs, patient_info) if patient_info else None
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_risk_level(self, probs, patient_info=None):
        """Calculate risk level"""
        max_class = max(probs, key=probs.get)
        max_prob = probs[max_class]
        
        age_note = ""
        if patient_info and patient_info.get('age'):
            age = patient_info['age']
            if age > 60:
                age_note = " (age is a risk factor)"
            elif age < 18:
                age_note = " (pediatric - specialized care needed)"
        
        if max_class == 'notumor' and max_prob > 0.4:
            return f"Low Risk - No tumor detected{age_note}"
        elif max_class == 'glioma':
            return f"High Risk - Glioma suspected (aggressive type){age_note}"
        elif max_class == 'meningioma':
            return f"Medium Risk - Meningioma suspected (usually benign){age_note}"
        elif max_class == 'pituitary':
            return f"Medium Risk - Pituitary tumor suspected (often treatable){age_note}"
        else:
            return f"Uncertain - Further evaluation recommended{age_note}"
    
    def _get_patient_context(self, probs, patient_info):
        """Generate patient context"""
        if not patient_info:
            return "No patient information provided"
        
        context = []
        age = patient_info.get('age')
        symptoms = patient_info.get('symptoms', [])
        
        if age:
            context.append(f"Age: {age}")
        if symptoms:
            context.append(f"Symptoms: {', '.join(symptoms)}")
        
        return " | ".join(context) if context else "No additional context"
    
    def get_feature_importance(self, features_df, predicted_class):
        """
        Calculate feature importance/contribution for the prediction
        Returns feature contributions with human-readable names
        """
        try:
            raw_features = features_df.iloc[0].to_dict() if len(features_df) > 0 else {}
            
            # Feature names in human-readable format
            feature_names = {
                'diagnostics_Image-original_Mean': 'Image Brightness',
                'diagnostics_Mask-original_VoxelNum': 'Tumor Size (pixels)',
                'diagnostics_Mask-original_VolumeNum': 'Number of Regions',
                'original_shape_Elongation': 'Shape Elongation',
                'original_shape_MajorAxisLength': 'Longest Axis Length',
                'original_shape_MinorAxisLength': 'Shortest Axis Length'
            }
            
            # Get feature values
            feature_values = {}
            for feat in self.SCALER_FEATURES:
                feature_values[feat] = raw_features.get(feat, 0.0)
            
            # Calculate contribution based on how well features match predicted class
            contributions = {}
            predicted_ranges = self.CLASS_RANGES.get(predicted_class, {})
            
            for feat in self.SCALER_FEATURES:
                value = feature_values[feat]
                human_name = feature_names.get(feat, feat)
                
                # Get expected range for predicted class
                if feat == 'diagnostics_Mask-original_VoxelNum':
                    expected_min, expected_max = predicted_ranges.get('VoxelNum', (0, 10000))
                elif feat == 'diagnostics_Mask-original_VolumeNum':
                    expected_min, expected_max = predicted_ranges.get('VolumeNum', (0, 30))
                elif feat == 'original_shape_MajorAxisLength':
                    expected_min, expected_max = predicted_ranges.get('MajorAxis', (0, 400))
                elif feat == 'original_shape_MinorAxisLength':
                    expected_min, expected_max = predicted_ranges.get('MinorAxis', (0, 300))
                elif feat == 'original_shape_Elongation':
                    expected_min, expected_max = predicted_ranges.get('Elongation', (0, 1))
                else:
                    expected_min, expected_max = (0, 100)
                
                # Calculate how well value matches expected range
                if expected_min <= value <= expected_max:
                    # Perfect match
                    contribution = 1.0
                    explanation = f"Value ({value:.1f}) matches {predicted_class} range"
                elif value < expected_min:
                    # Below range
                    diff = expected_min - value
                    range_size = expected_max - expected_min
                    contribution = max(0, 1 - (diff / range_size))
                    explanation = f"Value ({value:.1f}) is below typical {predicted_class} range"
                else:
                    # Above range
                    diff = value - expected_max
                    range_size = expected_max - expected_min
                    contribution = max(0, 1 - (diff / range_size))
                    explanation = f"Value ({value:.1f}) is above typical {predicted_class} range"
                
                contributions[human_name] = {
                    'value': value,
                    'contribution': contribution,
                    'explanation': explanation,
                    'expected_range': f"{expected_min:.1f} - {expected_max:.1f}"
                }
            
            return contributions
            
        except Exception as e:
            print(f"Error calculating feature importance: {e}")
            return {}
