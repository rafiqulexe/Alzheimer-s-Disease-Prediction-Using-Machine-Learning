# 🧠 Alzheimer's Disease Prediction & Clinical Assistant

A full-stack, machine-learning-powered clinical decision-support web application for the early detection and management of Alzheimer's disease. The system integrates predictive modeling, patient record keeping, an AI-driven clinical literature assistant (RAG), and a comprehensive administrative monitoring suite.

---

## 🌟 Key Features

* **Clinical Prediction Engine:** Predicts Alzheimer's disease risk using an optimized Random Forest classifier trained on cognitive, behavioral, and functional patient indicators (`MMSE`, `ADL`, `MemoryComplaints`, `BehavioralProblems`, `FunctionalAssessment`).
* **Patient Management:** Track patient history, update demographic details, generate automated patient IDs, and monitor longitudinal prediction trajectories.
* **AI Clinical Assistant (RAG):** Context-aware medical assistant powered by LangChain, Ollama (`llama3.2`), and FAISS vector retrieval on clinical reference documents (`mybuild_.pdf`).
* **Interactive Analytics Dashboards:**
  * **User Dashboard:** 14-day patient trend lines and overall diagnosis distribution (Chart.js).
  * **Admin Console:** Global patient registry, user status management (enable/disable, role elevation), prediction audit logs, and 30-day analytics.
* **Reports & Data Export:** One-click CSV exports of patient rosters and historical predictions.
* **Authentication & Role-Based Access Control:** Secure JWT cookie-based authentication with bcrypt password hashing and admin auto-assignment.

---

## 🏗️ Architecture & Technology Stack

* **Backend:** FastAPI, Uvicorn, Jinja2 Templates, Python-Jose (JWT), Passlib (Bcrypt).
* **Database:** MongoDB Atlas (via PyMongo).
* **Machine Learning:** Scikit-learn (RandomForestClassifier, StandardScaler), Joblib.
* **Retrieval-Augmented Generation (RAG):** LangChain, LangChain-Ollama, FAISS vector stores, PyPDF2.
* **Frontend:** Modern Vanilla CSS (responsive CSS Grid/Flexbox), Chart.js.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10+ (Python 3.11 or 3.12 recommended)
* MongoDB Atlas account or local MongoDB instance
* (Optional for Chatbot) [Ollama](https://ollama.com/) installed and running locally

### 2. Installation & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/rafiqulislam35/Alzheimer-s-Disease-Prediction-Using-Machine-Learning.git
cd Alzheimer-s-Disease-Prediction-Using-Machine-Learning

# Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and fill in your connection details:

```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=AlzheimerCluster
MONGODB_DB_NAME=alzheimers_app
JWT_SECRET=generate_a_secure_random_key_here
ADMIN_EMAILS=your_email@example.com
```

### 4. Train the Machine Learning Model

Run the training pipeline to generate the scaler, label encoder, and Random Forest model:

```bash
python train_model.py
```
*Output will be saved to the `model/` folder.*

### 5. (Optional) Setup the AI Assistant with Ollama

To enable local LLM and vector embeddings:

```bash
# Pull the required models
ollama pull llama3.2
ollama pull mxbai-embed-large

# Start the Ollama server
ollama serve
```

### 6. Start the Web Server

Run using the entrypoint script:

```bash
python main.py
```

Or directly via Uvicorn:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Access the application in your browser at `http://127.0.0.1:8000`.

---

## 📂 Project Structure

```
├── .env.example              # Sample environment template
├── .gitignore                # Security & repository ignore rules
├── app.py                    # Main FastAPI application and API routes
├── main.py                   # Server startup entrypoint
├── db.py                     # MongoDB database client configuration
├── train_model.py            # Model training, scaling, and evaluation script
├── vector.py                 # Lazy-loaded FAISS vector store & RAG pipeline
├── requirements.txt          # Python dependencies
├── data/
│   └── alzheimer_disease_data.csv  # Clinical dataset
├── model/
│   ├── label_encoder.pkl     # Fitted label encoder
│   ├── random_forest_model.pkl # Trained Random Forest classifier
│   └── scaler.pkl            # Fitted StandardScaler
├── faiss_index/              # Persisted vector embeddings
├── static/
│   └── styles.css            # Core UI design tokens and component styling
└── templates/                # Server-rendered Jinja2 templates
    ├── dashboard.html        # User analytics dashboard
    ├── prediction.html       # Diagnostic prediction form
    ├── patients.html         # User patient registry
    ├── add_patient.html      # Manual patient registration
    ├── edit_patient.html     # Patient profile edit modal
    ├── assistant.html        # AI clinical assistant chat
    ├── reports.html          # Reports and CSV downloads
    ├── settings.html         # User profile and password settings
    ├── login.html            # Authentication login
    ├── register.html         # User registration
    ├── forgot_password.html  # Password reset placeholder
    ├── admin_dashboard.html  # Admin control center
    ├── admin_users.html      # Admin user management
    ├── admin_patients.html   # Global patient records
    └── admin_predictions.html# Global prediction audit trail
```

---

## ⚕️ Medical Disclaimer

This software application is developed for **academic and research demonstration purposes only**. It is not a certified medical device and is not intended to replace professional clinical judgement, official diagnostic testing, or doctor-patient consultations. Always consult a qualified physician or neurologist for medical concerns.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
