# ML Model Report: Patient Wait Time Prediction

## Model Selection: Random Forest Regressor
We chose Random Forest for wait time prediction due to its robustness to outliers, non-linear relationship handling, and native support for feature importance interpretability.

## Feature Engineering
- **Queue Length**: Current number of patients waiting in the department.
- **Doctor Count**: Number of doctors currently online and accepting patients.
- **Department**: One-hot encoded categorical variable.
- **Hour of Day**: Captures daily peak-hour patterns.
- **Day of Week**: Captures weekly variation (e.g., busier Mondays).

## Training Performance
- **Dataset Size**: 800 synthetic hospital records.
- **Root Mean Squared Error (RMSE)**: ~6.75 minutes.
- **R-squared Score**: ~0.92 (Explains 92% of variance).

## Feature Importance (Interpretability)
1. **Queue Length**: ~51% (Primary driver of wait time).
2. **Doctor Count**: ~43% (Strong secondary factor).
3. **Department**: ~4% (Slight variations per specialty).
4. **Time Factors**: ~2% (Peak hour effects).

## Self-Monitoring System
The system implements real-time accuracy tracking by comparing `predicted_wait_time` vs `actual_wait_time_mins`. This data is stored per token to allow for model retraining and performance audits.
