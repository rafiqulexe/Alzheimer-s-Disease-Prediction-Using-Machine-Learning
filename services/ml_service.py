# services/ml_service.py
from pathlib import Path
import logging
import joblib
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"
model_path = MODEL_DIR / "random_forest_model.pkl"
scaler_path = MODEL_DIR / "scaler.pkl"
label_path = MODEL_DIR / "label_encoder.pkl"

model = None
scaler = None
label_encoder = None

def load_ml_components():
    global model, scaler, label_encoder
    if model is not None and scaler is not None and label_encoder is not None:
        return model, scaler, label_encoder

    try:
        if model_path.exists() and scaler_path.exists() and label_path.exists():
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            label_encoder = joblib.load(label_path)
            logger.info("Random Forest model, scaler, and label encoder loaded.")
        else:
            logger.warning("Model files not found. Run train_model.py to generate models.")
    except Exception as e:
        logger.error(f"Error loading model files: {e}")

    return model, scaler, label_encoder

# Preload on import
load_ml_components()

def predict_alzheimers(
    memory_complaints: float,
    behavioral_problems: float,
    adl: float,
    mmse: float,
    functional_assessment: float,
):
    m, s, le = load_ml_components()
    if m is None or s is None or le is None:
        raise RuntimeError("ML model is not loaded. Please run train_model.py first.")

    features = np.array(
        [[memory_complaints, behavioral_problems, adl, mmse, functional_assessment]],
        dtype=float,
    )
    scaled = s.transform(features)

    pred_idx = int(m.predict(scaled)[0])
    class_label = le.inverse_transform([pred_idx])[0]

    if str(class_label) in ["1", "Alzheimer", "Alzheimer's Disease", "AD"]:
        status = "Alzheimer's Detected"
    else:
        status = "No Alzheimer's"

    return pred_idx, str(class_label), status
