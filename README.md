# Retail Sales Forecasting & Internal Deployment

This repository contains a full end-to-end Machine Learning pipeline for predicting future retail sales, developed for the Datanest Data Scientist / Machine Learning Engineer take-home assessment.

## Guide on how to run the app

> **Note on Data:** Due to GitHub's 100MB file size limit, the raw training datasets (`train.csv`) are not included in this repository. 
> - To run the **Streamlit Web App** (Step 6), you do not need the training data! The required `forecast.csv` is already included.
> - To run the **Jupyter Notebook** (Step 5), please download the original dataset from this [Google Drive](https://drive.google.com/drive/folders/1UO1sUyfTa17fLDNUCuXp-2Ocuk7PB0Dz?usp=drive_link) and place it in the `data/` folder in the root directory before running.

1. Clone down the repo

```bash
git clone git@github.com:nguyen6uyen/Nguyen_Datanest_DS_MLE_takehome_test.git
```
2. Cd into the repo on terminal

```bash
cd Nguyen_Datanest_DS_MLE_takehome_test
```
3. Create conda environment
```bash
conda env create -f environment.yml
```
4. Activate environment
```bash
conda activate datanest
```

5. Run model
```bash
jupyter notebook work.ipynb
```

6. Run app
```bash
streamlit run app.py # -> http://localhost:8501
```

**The app loads the pre-computed `forecast.csv` and provides a clean, fast dashboard for internal users to search for inventory forecasts.*


## Modeling Approach

The goal of Task 1 is to predict the total amount of products sold in every shop for the upcoming month (November 2015).

### Key Architectural Decisions
1. **Model Selection:** Given the panel structure of the data (thousands of individual `(shop, item)` time series) and the constant introduction of new items without historical data, I choose Regression Tree Based model. Since they have the ability to learn global patterns across thousands of disparate timelines and handle missing history via lag features.
    - The chosen models are: RandomForest, XGBoost, and LightGBM
2. **Feature Engineering:** I engineered temporal features (month) and historical sliding windows (Lag 1, Lag 2, Lag 12) to capture short-term momentum and yearly seasonality.
3. **Data Cleaning & Target Clipping:** Extreme daily anomalies (sales count > 1000 or item's price > 100k) were dropped as outliers. Furthermore, to align with standard retail forecasting metrics and prevent the Root Mean Square Error (RMSE) from being exponentially skewed by rare wholesale orders (0.1% outliers), the target variable `item_cnt_month` was clipped to a maximum of 21 according to the quantiles analysis (that 99.9% of all monthly item sales are 21.0 units or less)
4. **Time-Series Cross Validation:** I use month 0 to 32 as a train set, and month 33 a a validation set. Hyperparameters were tuned based on the train set and validated through the validation set.

---

## Deployment Patterns & Web App

The goal of Task 2 is to deploy this model to an internal web page where non-technical stakeholders (e.g., Supply Chain Managers) can input an `item_id` and receive the November 2015 forecast.

### Deployment Pattern Analysis
When deploying a machine learning model to a web application, there are two primary architectures: **Real-Time Inference** and **Batch Prediction**.

**1. Real-Time Inference (Not Recommended Here)**
*   *How it works:* The user clicks "Search", the web app sends the `item_id` to an API, the server loads the heavy XGBoost model into RAM, gathers the real-time lag features from a database, runs `.predict()`, and returns the answer.
*   *Why it's bad for this use-case:* Retail forecasts for an upcoming month are static. The answer for "How many items will we sell next month?" does not change by the second. Running a heavy XGBoost model in real-time for every single user search is computationally expensive, slow, and completely unnecessary.

**2. Batch Prediction (The Chosen Implementation)**
*   *How it works:* At the end of the month, a scheduled data pipeline (e.g., Apache Airflow) runs the XGBoost model *once* on the entire inventory. It generates the predictions for all items and saves them into a lightweight database or CSV (`forecast.csv`). The web app simply queries this file.
*   *Why it's the perfect fit:* It is infinitely cheaper, faster, and more robust. If the ML model crashes during inference, the users never notice because the web app is decoupled from the ML pipeline.
