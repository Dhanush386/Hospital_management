import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import json

def train_model():
    data_path = os.path.join(os.path.dirname(__file__), 'historical_data.csv')
    df = pd.read_csv(data_path)

    # Preprocessing
    le_dept = LabelEncoder()
    df['Department_Encoded'] = le_dept.fit_transform(df['Department'])
    
    # Features & Target
    features = ['Hour', 'Day_of_Week', 'Queue_Length', 'Doctor_Count', 'Department_Encoded']
    X = df[features]
    y = df['Wait_Time']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model Training
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, y_pred)
    print(f"[OK] Model trained. RMSE: {rmse:.2f} minutes")

    # Feature Importance
    importances = model.feature_importances_
    feature_importance_dict = {
        feature: round(float(importance) * 100, 2)
        for feature, importance in zip(features, importances)
    }
    
    # Sort by importance
    feature_importance_dict = dict(sorted(feature_importance_dict.items(), key=lambda item: item[1], reverse=True))
    
    print("[OK] Feature Importances:")
    for k, v in feature_importance_dict.items():
        print(f"  - {k}: {v}%")

    # Save Model & Artifacts
    model_path = os.path.join(os.path.dirname(__file__), 'wait_time_rf.joblib')
    artifacts_path = os.path.join(os.path.dirname(__file__), 'model_artifacts.json')
    
    joblib.dump({
        'model': model,
        'label_encoder_dept': le_dept,
        'features': features
    }, model_path)
    
    with open(artifacts_path, 'w') as f:
        json.dump({
            'rmse': rmse,
            'feature_importances': feature_importance_dict
        }, f, indent=4)
        
    print(f"[OK] Model saved -> {model_path}")

if __name__ == '__main__':
    train_model()
