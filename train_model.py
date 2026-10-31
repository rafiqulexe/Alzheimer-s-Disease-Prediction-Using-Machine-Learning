# train_model.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# -----------------------------
# Paths
# -----------------------------
DATA_PATH = Path("data") / "alzheimer_disease_data.csv"   # your actual file
MODEL_DIR = Path("model")
MODEL_DIR.mkdir(exist_ok=True)

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv(DATA_PATH)

print("Columns in CSV:", list(df.columns))

# -----------------------------
# Features & target
# (these columns DO exist in your CSV)
# -----------------------------
feature_cols = [
    "MemoryComplaints",
    "BehavioralProblems",
    "ADL",
    "MMSE",
    "FunctionalAssessment",
]

# Target column is 'Diagnosis' (text labels)
target_col = "Diagnosis"

X = df[feature_cols].values

# Encode text diagnosis labels to numbers
diagnosis_values = df[target_col].astype(str)
print("Unique Diagnosis values:", diagnosis_values.unique())

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(diagnosis_values)

# -----------------------------
# Train/test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -----------------------------
# Scale features
# -----------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# -----------------------------
# Train model
# -----------------------------
clf = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)
clf.fit(X_train_scaled, y_train)

# -----------------------------
# Evaluate
# -----------------------------
y_pred = clf.predict(X_test_scaled)
y_proba = clf.predict_proba(X_test_scaled)[:, 1] if len(label_encoder.classes_) == 2 else None

print("\n--- Model Evaluation ---")
print("Accuracy:", accuracy_score(y_test, y_pred))
if y_proba is not None:
    from sklearn.metrics import roc_auc_score
    print("ROC-AUC Score:", roc_auc_score(y_test, y_proba))
from sklearn.metrics import confusion_matrix
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# -----------------------------
# Save model + scaler + label encoder
# -----------------------------
joblib.dump(clf, MODEL_DIR / "random_forest_model.pkl")
joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
joblib.dump(label_encoder, MODEL_DIR / "label_encoder.pkl")

print("[OK] Saved model, scaler, and label encoder to:", MODEL_DIR)
print("Classes:", label_encoder.classes_)
