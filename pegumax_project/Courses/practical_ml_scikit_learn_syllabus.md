# Practical Machine Learning with Scikit-Learn

*A hands-on, code-first course for building real predictive models in Python. Skip the heavy calculus—focus on cleaning data, training models, and shipping them into production.*

---

## Module 1: The Practical ML Workflow
**Get the big-picture pipeline so every later technique fits into a clear, repeatable process.**

- The end-to-end workflow: data → features → model → evaluation → deployment
- Supervised vs. unsupervised learning and how to recognize which problem you have
- Setting up your Python environment: NumPy, Pandas, scikit-learn, and Jupyter

---

## Module 2: Data Cleaning with Pandas
**Turn messy raw data into a clean, model-ready dataset—where most real ML time is actually spent.**

- Loading data and inspecting it: types, ranges, duplicates, and summary statistics
- Handling missing values, outliers, and inconsistent or malformed entries
- Filtering, grouping, merging, and reshaping DataFrames into a usable structure

---

## Module 3: Exploratory Data Analysis & Visualization
**Understand your data visually so you make informed modeling choices instead of guessing.**

- Distributions, correlations, and spotting relationships between variables
- Plotting with Matplotlib and Seaborn for quick, revealing visuals
- Detecting leakage, imbalance, and red flags before training anything

---

## Module 4: Feature Engineering & Preprocessing
**Transform raw columns into features that make models dramatically more accurate.**

- Encoding categorical variables and scaling/normalizing numeric features
- Creating, binning, and selecting features that carry real predictive signal
- Building reproducible preprocessing with scikit-learn transformers

---

## Module 5: Supervised Learning—Regression
**Predict continuous values and learn to read whether your model is actually any good.**

- Linear regression and regularized variants (Ridge, Lasso) in scikit-learn
- Tree-based regressors and when they beat linear models
- Regression metrics: MAE, MSE/RMSE, and R² interpreted in plain terms

---

## Module 6: Supervised Learning—Classification
**Predict categories and evaluate classifiers beyond a misleading accuracy score.**

- Logistic regression, decision trees, and k-nearest neighbors for classification
- Confusion matrix, precision, recall, F1, and the ROC/AUC curve
- Handling imbalanced classes with resampling and threshold tuning

---

## Module 7: Ensemble Methods
**Combine many models to squeeze out the accuracy that single algorithms can't reach.**

- Bagging and Random Forests for robust, low-variance predictions
- Boosting with gradient-boosted trees (and XGBoost-style libraries)
- Feature importance and interpreting what an ensemble learned

---

## Module 8: Clustering & Unsupervised Learning
**Find structure in unlabeled data to segment, group, and discover patterns.**

- K-means clustering and choosing the number of clusters
- Hierarchical and density-based (DBSCAN) clustering for non-spherical groups
- Dimensionality reduction with PCA for visualization and noise reduction

---

## Module 9: Model Evaluation & Tuning
**Validate and tune models properly so they perform on new data, not just your training set.**

- Train/test splits, cross-validation, and avoiding overfitting and data leakage
- Hyperparameter tuning with grid and randomized search
- Building leak-proof pipelines that bundle preprocessing and modeling together

---

## Module 10: Saving & Deploying Models for Production
**Persist trained models and serve predictions so your work runs outside the notebook.**

- Serializing models and pipelines with `joblib` and `pickle`
- Loading saved models to make predictions on fresh data reliably
- Wrapping a model in a simple API and versioning models for production use

---
