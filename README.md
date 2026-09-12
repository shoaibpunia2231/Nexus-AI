# Nexus AI — Dengue Screening & Risk Assessment

An end-to-end clinical machine learning application designed to assist in dengue screening and decision support using patient laboratory parameters.

## Overview

The system takes patient information such as age, sex, haemoglobin, platelet count, and PDW and uses machine learning to estimate the likelihood of dengue.

The project combines a machine learning pipeline, FastAPI backend, and React frontend into a complete prediction application.

### Key Features

* 🧠 ML-based dengue prediction
* 📊 Clinical and laboratory feature analysis
* 🔍 Feature importance and model interpretability
* ⚡ FastAPI prediction backend
* 💻 Interactive React frontend
* 📈 Model performance and prediction dashboard
* 🧪 Feature-selection experiments to investigate data leakage and feature dominance

---

## Machine Learning Approach

Several classification models were evaluated, including:

* Logistic Regression
* Random Forest
* Gradient Boosting

The dataset was processed using missing-value handling, categorical encoding, feature scaling, and stratified train/test splitting.

### Why Were Some Features Removed?

During model evaluation, the initial feature set produced extremely high performance. Instead of treating this as automatically valid, the individual features were investigated to determine whether the model was relying on potentially problematic predictors.

**WBC Count** was found to have an unusually strong influence on the predictions and was therefore excluded from the production feature set.

Other features that provided little useful variation or were unsuitable for the final clinical-oriented feature set were also removed.

This resulted in a more conservative feature set based on:

* Age
* Sex
* Haemoglobin
* Platelet Count
* PDW

The goal was to reduce the possibility of the model simply exploiting a dominant feature and to produce a more interpretable and clinically oriented prediction pipeline.

---

## Model Performance

After feature selection, the final model achieved:

| Metric           |           Result |
| ---------------- | ---------------: |
| Test Accuracy    |        **98.9%** |
| Cross-Validation | **98.6% ± 1.4%** |
| Train–Test Gap   |         **0.1%** |

The small train–test gap indicates that the model's performance was relatively consistent between training and unseen test data.

Cross-validation was also used to evaluate whether the performance remained stable across different data splits rather than relying only on a single train/test split.

> **Important:** High accuracy on this dataset does not imply clinical-grade diagnostic accuracy. The model has not been clinically validated and should not be used as a substitute for laboratory testing or professional medical diagnosis.

---

## Architecture

```text
Patient Information
        ↓
Data Preprocessing
        ↓
Feature Selection
        ↓
ML Model
        ↓
Dengue Risk Prediction
        ↓
Feature Importance
        ↓
FastAPI Backend
        ↓
React Dashboard
```

---

## Tech Stack

**Machine Learning**

Python • Pandas • NumPy • Scikit-learn

**Backend**

FastAPI • Python • REST API

**Frontend**

React • JavaScript

**Deployment**

Render • Vercel

---

## Project Structure

```text
dengue-v4/
├── ml/
│   ├── data/
│   ├── models/
│   ├── data_cleaning.py
│   ├── preprocess.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── eda_analysis.py
│   ├── predict.py
│   └── root_cause_analysis.py
│
├── backend/
│   └── main.py
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── App.jsx
│       └── main.jsx
│
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Running Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Train the Model

```bash
cd ml
python train_model.py
# Nexus AI — Dengue Screening & Risk Assessment

An end-to-end clinical machine learning application designed to assist in dengue screening and decision support using patient laboratory parameters.

## Overview

The system takes patient information such as age, sex, haemoglobin, platelet count, and PDW and uses machine learning to estimate the likelihood of dengue.

The project combines a machine learning pipeline, FastAPI backend, and React frontend into a complete prediction application.

### Key Features

* 🧠 ML-based dengue prediction
* 📊 Clinical and laboratory feature analysis
* 🔍 Feature importance and model interpretability
* ⚡ FastAPI prediction backend
* 💻 Interactive React frontend
* 📈 Model performance and prediction dashboard
* 🧪 Feature-selection experiments to investigate data leakage and feature dominance

---

## Machine Learning Approach

Several classification models were evaluated, including:

* Logistic Regression
* Random Forest
* Gradient Boosting

The dataset was processed using missing-value handling, categorical encoding, feature scaling, and stratified train/test splitting.

### Why Were Some Features Removed?

During model evaluation, the initial feature set produced extremely high performance. Instead of treating this as automatically valid, the individual features were investigated to determine whether the model was relying on potentially problematic predictors.

**WBC Count** was found to have an unusually strong influence on the predictions and was therefore excluded from the production feature set.

Other features that provided little useful variation or were unsuitable for the final clinical-oriented feature set were also removed.

This resulted in a more conservative feature set based on:

* Age
* Sex
* Haemoglobin
* Platelet Count
* PDW

The goal was to reduce the possibility of the model simply exploiting a dominant feature and to produce a more interpretable and clinically oriented prediction pipeline.

---

## Model Performance

After feature selection, the final model achieved:

| Metric           |           Result |
| ---------------- | ---------------: |
| Test Accuracy    |        **98.9%** |
| Cross-Validation | **98.6% ± 1.4%** |
| Train–Test Gap   |         **0.1%** |

The small train–test gap indicates that the model's performance was relatively consistent between training and unseen test data.

Cross-validation was also used to evaluate whether the performance remained stable across different data splits rather than relying only on a single train/test split.

> **Important:** High accuracy on this dataset does not imply clinical-grade diagnostic accuracy. The model has not been clinically validated and should not be used as a substitute for laboratory testing or professional medical diagnosis.

---

## Architecture

```text
Patient Information
        ↓
Data Preprocessing
        ↓
Feature Selection
        ↓
ML Model
        ↓
Dengue Risk Prediction
        ↓
Feature Importance
        ↓
FastAPI Backend
        ↓
React Dashboard
```

---

## Tech Stack

**Machine Learning**

Python • Pandas • NumPy • Scikit-learn

**Backend**

FastAPI • Python • REST API

**Frontend**

React • JavaScript

**Deployment**

Render • Vercel

---

## Project Structure

```text
dengue-v4/
├── ml/
│   ├── data/
│   ├── models/
│   ├── data_cleaning.py
│   ├── preprocess.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── eda_analysis.py
│   ├── predict.py
│   └── root_cause_analysis.py
│
├── backend/
│   └── main.py
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── App.jsx
│       └── main.jsx
│
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Running Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Train the Model

```bash
cd ml
python train_model.py
```

---

## Disclaimer

This project is intended for **educational and research purposes** as an AI-assisted screening and decision-support system.

It is **not a clinically validated diagnostic tool** and should not replace professional medical evaluation, laboratory confirmation, or medical advice.#   N e x u s - A I  
 