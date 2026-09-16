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

5. Run model (Executes the notebook headlessly to generate forecast.csv)
```bash
jupyter nbconvert --to notebook --execute --inplace work.ipynb
```

6. Run app
```bash
streamlit run app.py # -> http://localhost:8501
```

**The app loads the pre-computed `forecast.csv` and provides a clean, fast dashboard for internal users to search for inventory forecasts.*


## Modeling Approach

### Key Architectural Decisions
1. **Model Selection:** Given the panel structure of the data (thousands of individual `(shop, item)` time series) and the constant introduction of new items without historical data, I chose regression tree-based models, since they have the ability to learn global patterns across thousands of disparate timelines and handle missing history via lag features.
    - The chosen models are: Random Forest, XGBoost, and LightGBM
2. **Feature Engineering:** I engineered temporal features (month) and historical sliding windows (Lag 1, Lag 2, Lag 12) to capture short-term momentum and yearly seasonality.
3. **Data Cleaning & Target Clipping:** Extreme daily anomalies (sales count > 1000 or item price > 100k) were dropped as outliers. Furthermore, to align with standard retail forecasting metrics and prevent the Root Mean Square Error (RMSE) from being exponentially skewed by rare wholesale orders (0.1% outliers), the target variable `item_cnt_month` was clipped to a maximum of 21, based on the quantile analysis showing that 99.9% of all monthly item sales are 21.0 units or fewer.
4. **Time-Series Cross-Validation:** I used months 0 to 32 as the train set, and month 33 as the validation set. Hyperparameters were tuned on the train set and validated using the validation set. After validation, I fit the optimized model on the full original train set (33 blocks) to get the best performance.
5. **Prediction:** Finally, I applied the optimized model to predict the test set and saved the result to `forecast.csv`.
---

## Deployment Patterns & Web App

### Deployment Pattern Analysis

For this project, there are 2 primary deployment pattern that I think off: **Real-Time** and **Batch Prediction**.


**1. Real-Time**
*   *How it works:* The user clicks "Search," the web app sends the `item_id` to an API, the server loads the model into RAM, gathers the real-time lag features from a database, runs `.predict()`, and returns the answer.
*   *Why it is not used here:* Retail forecasts for an upcoming month are static. The answer to "How many items will we sell next month?" does not change by the second or by the day, because stores usually order stock weeks or months in advance (not to mention holiday seasons, where stock has to be ordered even further ahead). Running a heavy XGBoost model in real time for every single user search is computationally expensive, slow, and completely unnecessary, especially when our training dataset (after reconstruction) is near 10 million rows.

**2. Batch Prediction (my implementation)**
*   *How it works:* At the end of the month, a scheduled data pipeline runs the XGBoost model *once* on the entire inventory. It generates the predictions for all items and saves them into a lightweight database or CSV (e.g., `forecast.csv`). The web app simply queries this file.
*   *Why it is the perfect fit here:* It is infinitely cheaper, faster, and more robust. If the ML model crashes during inference, users never notice, because the web app uses data directly from the CSV rather than generating it from the model.