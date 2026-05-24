"""
Explainability module for the Tree Prescriber system.
Combines SHAP (Shapley Additive exPlanations) for model-level contributions
with expert ecological rules to output natural language reasons.
"""

import numpy as np
import pandas as pd

# Try to import shap, but support fallback if installation fails
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("Warning: shap package not found. Explainability will use fallback heuristics.")

# Define expert ecological envelopes for tree species in Nepal
ECOLOGICAL_ENVELOPES = {
    "Dalbergia sissoo": {
        "common_name": "Sisau",
        "optimal_elevation": (60, 1000),      # Lowland Terai riverine species
        "preferred_pH": (5.8, 7.8),           # Prefers neutral to slightly alkaline alluvial soil
        "preferred_textures": ["Loam", "Sandy Loam", "Silt Loam", "Sand"], # Thrives in well-drained, sandy/alluvial soil
        "nitrogen_requirement": "moderate_to_high",
        "description": "A nitrogen-fixing deciduous tree that thrives in lowland Terai plains and riverine sandbeds."
    },
    "Pinus roxburghii": {
        "common_name": "Salla / Chir Pine",
        "optimal_elevation": (900, 2400),     # Mid-hill conifer
        "preferred_pH": (4.5, 6.5),           # Tolerant of acidic, nutrient-poor soils
        "preferred_textures": ["Sandy Loam", "Loamy Sand", "Sand", "Sandy Clay Loam"], # Prefers highly drained slopes
        "nitrogen_requirement": "low",
        "description": "A robust, drought-tolerant conifer adapted to dry, acidic, and nutrient-poor slopes of the Middle Hills."
    }
}

def get_ecological_reasons(features: dict, species: str) -> list:
    """
    Generates natural language explanations comparing input features with expert ecological envelopes.
    """
    reasons = []
    envelope = ECOLOGICAL_ENVELOPES.get(species)
    if not envelope:
        return ["Suitable for local environmental conditions."]

    # 1. Elevation check
    elev = features.get("elevation", 0)
    opt_min, opt_max = envelope["optimal_elevation"]
    if opt_min <= elev <= opt_max:
        reasons.append(f"Elevation of {elev:.0f}m is within the optimal range ({opt_min}-{opt_max}m) for {species}.")
    elif elev < opt_min:
        reasons.append(f"Lowland elevation ({elev:.0f}m) fits the warm temperature requirements of {species}.")
    else:
        reasons.append(f"Elevation ({elev:.0f}m) is acceptable, but fits upper altitude tolerance.")

    # 2. pH check
    ph = features.get("pH", 7.0)
    ph_min, ph_max = envelope["preferred_pH"]
    if ph_min <= ph <= ph_max:
        reasons.append(f"Soil pH ({ph:.2f}) is optimal (preferred: {ph_min}-{ph_max}) for this species.")
    elif ph < ph_min:
        reasons.append(f"Soil pH ({ph:.2f}) is highly acidic, which {species} is known to tolerate.")
    else:
        reasons.append(f"Soil pH ({ph:.2f}) is neutral-to-alkaline, matching the preference of {species}.")

    # 3. Soil Texture check
    texture = features.get("soil_texture_class", "Loam")
    if texture in envelope["preferred_textures"]:
        reasons.append(f"Soil texture '{texture}' provides the excellent drainage required by this species.")
    else:
        reasons.append(f"Soil texture '{texture}' offers acceptable physical support and aeration.")

    # 4. Chemical nutrients check
    om = features.get("organic_matter", 1.0)
    if species == "Pinus roxburghii" and om < 2.0:
        reasons.append(f"Organic matter ({om:.2f}%) is low, but this conifer is highly suited for degraded/nutrient-poor land.")
    elif species == "Dalbergia sissoo" and om >= 2.0:
        reasons.append(f"High organic matter ({om:.2f}%) provides the rich nutrient base this broadleaf species prefers.")

    return reasons


def get_model_shap_reasons(pipeline, X_sample: pd.DataFrame, species_idx: int, label_encoder, top_n: int = 3) -> list:
    """
    Computes local SHAP values to identify features that contributed most positively
    to the predicted species class.
    """
    if not SHAP_AVAILABLE:
        return []

    try:
        # Preprocess sample to match the model inputs
        preprocessor = pipeline.named_steps['preprocessor']
        classifier = pipeline.named_steps['classifier']
        
        # Transform the single sample
        X_trans = preprocessor.transform(X_sample)
        
        # Determine feature names in preprocessed space
        # Preprocessor outputs numeric followed by categorical columns
        feature_names = preprocessor.get_feature_names_out()
        
        # Initialize explainer
        # TreeExplainer works directly on RandomForest/XGBoost/LightGBM
        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(X_trans)
        
        # If binary classification (2 species), SHAP returns shape (n_samples, n_features)
        # representing the log-odds of the positive class (class 1).
        # If multiclass (>=3 classes), it returns a list of arrays, one per class.
        if isinstance(shap_values, list):
            # Multiclass case
            local_shap = shap_values[species_idx][0]
        elif len(shap_values.shape) == 3:
            # Alternate shape for multiclass in newer SHAP versions
            local_shap = shap_values[0, :, species_idx]
        else:
            # Binary class case: shap_values is a single array of shape (n_samples, n_features).
            # It represents contributions for class 1.
            # For class 0, contributions are the negative of class 1.
            if species_idx == 1:
                local_shap = shap_values[0]
            else:
                local_shap = -shap_values[0]

        # Get indices of top features with positive contribution
        positive_indices = np.argsort(local_shap)[::-1]
        
        shap_reasons = []
        for idx in positive_indices:
            feat_contrib = local_shap[idx]
            if feat_contrib > 0.01: # Significant positive contribution
                feat_name = feature_names[idx]
                # Clean up feature name (e.g. num__elevation -> elevation)
                feat_clean = feat_name.split("__")[-1]
                # Map back to value if in original dataframe
                orig_val = ""
                if feat_clean in X_sample.columns:
                    val = X_sample[feat_clean].iloc[0]
                    orig_val = f" ({val:.2f})" if isinstance(val, (int, float)) else f" ('{val}')"
                
                shap_reasons.append(f"Feature '{feat_clean}'{orig_val} positively influenced recommendation (SHAP impact: +{feat_contrib:.3f})")
                if len(shap_reasons) >= top_n:
                    break
        
        return shap_reasons

    except Exception as e:
        print(f"Error computing SHAP values: {e}")
        return []


def generate_explanations(pipeline, X_sample: pd.DataFrame, species_name: str, score: float, label_encoder) -> list:
    """
    Coordinates SHAP and ecological rules to construct a rich, complete explanation.
    """
    # 1. Retrieve ecological explanations (general scientific rules)
    features_dict = X_sample.iloc[0].to_dict()
    ecological_reasons = get_ecological_reasons(features_dict, species_name)
    
    # 2. Retrieve SHAP explanations (mathematical model contributions)
    try:
        species_idx = list(label_encoder.classes_).index(species_name)
        shap_reasons = get_model_shap_reasons(pipeline, X_sample, species_idx, label_encoder)
    except Exception:
        shap_reasons = []

    # Combine both lists (limit SHAP reasons to 2 and ecological to 3)
    explanations = []
    explanations.extend(ecological_reasons[:3])
    if shap_reasons:
        explanations.extend(shap_reasons[:2])
        
    return explanations
