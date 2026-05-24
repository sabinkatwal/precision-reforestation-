"""
Model training and evaluation pipeline for the Tree Prescriber system.
Loads the training dataset, applies spatial clustering splits,
compares Random Forest, XGBoost, and LightGBM, and saves the best model.
"""

import pandas as pd
import numpy as np
import joblib
import sys
from pathlib import Path

# Add parent directory to sys.path to allow running from any folder
sys.path.append(str(Path(__file__).resolve().parent))

from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

# Import custom configurations and feature engineering
from config import (
    TRAINING_DATA_PATH, MODEL_PATH, ENCODERS_PATH,
    NUMERIC_FEATURES, CATEGORICAL_FEATURES,
    ENGINEERED_NUMERIC, ENGINEERED_CATEGORICAL,
    MODEL_FEATURES
)
from feature_engineering import TreePrescriberFeatureEngineer

# Graceful imports for XGBoost and LightGBM
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("Warning: xgboost package not found. Will fall back to Random Forest if needed.")

try:
    from lightgbm import LGBMClassifier
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False
    print("Warning: lightgbm package not found. Will fall back to Random Forest if needed.")


def top_k_accuracy(y_true, y_probs, k=2):
    """
    Computes top-k accuracy.
    """
    # Sort probabilities descending and take top k indices
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    # Check if true class is in top k predictions
    correct = [y_true[i] in top_k_preds[i] for i in range(len(y_true))]
    return np.mean(correct)


def train_and_evaluate():
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found at {TRAINING_DATA_PATH}. Please run build_dataset.py first.")

    print("=== LOADING TRAINING DATASET ===")
    df = pd.read_csv(TRAINING_DATA_PATH)
    print(f"Loaded dataset shape: {df.shape}")

    # Separating features (X) and target (y)
    X = df.drop(columns=["species"])
    y = df["species"]

    # Encode Target Labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)
    print(f"Unique target species classes: {list(label_encoder.classes_)}")

    # Initialize and fit our Feature Engineer
    print("\n=== STEP 1: FITTING FEATURE ENGINEER ===")
    # Using 5 clusters for spatial grouping of coordinates
    feature_engineer = TreePrescriberFeatureEngineer(n_clusters=5, random_state=42)
    X_engineered = feature_engineer.fit_transform(X)

    # Save spatial cluster assignments for geographic splitting
    # The feature engineer outputs a column "spatial_cluster" which represents KMeans clusters.
    groups = X_engineered["spatial_cluster"].values
    
    print(f"Spatial clusters distribution: {pd.Series(groups).value_counts().to_dict()}")

    # Define categorical features encoding pipeline
    categorical_features_to_encode = CATEGORICAL_FEATURES + ENGINEERED_CATEGORICAL
    numeric_features_to_use = NUMERIC_FEATURES + ENGINEERED_NUMERIC
    
    # We use OrdinalEncoder for tree-based models (efficient and handles unseen categories gracefully)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features_to_use),
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), categorical_features_to_encode)
        ]
    )

    # Define models to evaluate
    models_dict = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    }
    
    if XGB_AVAILABLE:
        models_dict["XGBoost"] = XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            eval_metric="mlogloss"
        )
    if LGBM_AVAILABLE:
        models_dict["LightGBM"] = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            verbose=-1,
            class_weight='balanced'
        )

    # Spatial Cross-Validation: GroupKFold splits the data geographically by spatial cluster
    # This guarantees that the model is tested on coordinates it hasn't seen during training,
    # preventing spatial autocorrelation bias.
    gkf = GroupKFold(n_splits=5)
    
    best_overall_f1 = 0.0
    best_model_name = None
    best_pipeline = None

    print("\n=== STEP 2: SPATIAL CROSS-VALIDATION ===")
    for model_name, clf in models_dict.items():
        print(f"\nEvaluating Model: {model_name}...")
        
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', clf)
        ])

        fold_accuracies = []
        fold_f1_scores = []
        fold_top2_accuracies = []

        # Iterate through the GroupKFold splits
        for fold, (train_idx, val_idx) in enumerate(gkf.split(X_engineered, y_encoded, groups)):
            X_tr, X_val = X_engineered.iloc[train_idx], X_engineered.iloc[val_idx]
            y_tr, y_val = y_encoded[train_idx], y_encoded[val_idx]

            # Fit the pipeline
            pipeline.fit(X_tr, y_tr)
            
            # Predict
            preds = pipeline.predict(X_val)
            probs = pipeline.predict_proba(X_val)

            # Evaluate
            acc = accuracy_score(y_val, preds)
            f1 = f1_score(y_val, preds, average='macro')
            top2 = top_k_accuracy(y_val, probs, k=min(2, num_classes))

            fold_accuracies.append(acc)
            fold_f1_scores.append(f1)
            fold_top2_accuracies.append(top2)

        mean_acc = np.mean(fold_accuracies)
        mean_f1 = np.mean(fold_f1_scores)
        mean_top2 = np.mean(fold_top2_accuracies)

        print(f"  Mean Accuracy: {mean_acc:.4f}")
        print(f"  Mean Macro F1-Score: {mean_f1:.4f}")
        print(f"  Mean Top-2 Accuracy: {mean_top2:.4f}")

        # Choose the best model based on macro F1
        if mean_f1 > best_overall_f1:
            best_overall_f1 = mean_f1
            best_model_name = model_name
            # Retrain on the entire dataset for final export
            best_pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', clf)
            ])
            best_pipeline.fit(X_engineered, y_encoded)

    print(f"\nBest Model Selected: {best_model_name} (Macro F1: {best_overall_f1:.4f})")

    # Evaluate final model on the whole dataset to show classification details
    final_preds = best_pipeline.predict(X_engineered)
    final_probs = best_pipeline.predict_proba(X_engineered)
    
    print("\n=== FINAL CHOSEN MODEL METRICS (On Full Dataset) ===")
    print("Accuracy Score:", accuracy_score(y_encoded, final_preds))
    print("Macro F1-Score:", f1_score(y_encoded, final_preds, average='macro'))
    print("Top-2 Accuracy:", top_k_accuracy(y_encoded, final_probs, k=min(2, num_classes)))
    
    print("\nDetailed Classification Report:")
    print(classification_report(y_encoded, final_preds, target_names=label_encoder.classes_))
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_encoded, final_preds))

    # Save artifacts
    print("\n=== STEP 3: EXPORTING PIPELINES ===")
    
    # Save the trained model pipeline (Preprocessor + Classifier)
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"Saved trained classifier pipeline to: {MODEL_PATH}")

    # Save other encoders (FeatureEngineer and Target LabelEncoder)
    encoders = {
        "feature_engineer": feature_engineer,
        "label_encoder": label_encoder,
        "feature_names_in": X_engineered.columns.tolist(),
        "numeric_features": numeric_features_to_use,
        "categorical_features": categorical_features_to_encode
    }
    joblib.dump(encoders, ENCODERS_PATH)
    print(f"Saved encoders mapping to: {ENCODERS_PATH}")

if __name__ == "__main__":
    train_and_evaluate()
