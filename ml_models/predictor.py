import os
import joblib
import pandas as pd
import numpy as np

class WaitTimePredictor:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'wait_time_rf.joblib')
        self.model = None
        self.le_dept = None
        self.features = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data.get('model')
                self.le_dept = data.get('label_encoder_dept')
                self.features = data.get('features')
            except Exception as e:
                print(f"[!] Error loading model: {e}")
        else:
            print("[!] Model file not found. Please train the model first.")

    def predict_wait_time(self, hour, day_of_week, queue_length, doctor_count, department):
        if not self.model or not self.le_dept:
            return None
        
        try:
            # Handle unknown departments gracefully
            if department in self.le_dept.classes_:
                dept_encoded = self.le_dept.transform([department])[0]
            else:
                dept_encoded = 0 # Default fallback
                
            input_data = pd.DataFrame([{
                'Hour': hour,
                'Day_of_Week': day_of_week,
                'Queue_Length': queue_length,
                'Doctor_Count': doctor_count,
                'Department_Encoded': dept_encoded
            }])
            
            # Predict
            pred = self.model.predict(input_data)[0]
            return max(5, int(round(pred))) # Ensure at least 5 mins
        except Exception as e:
            print(f"[!] Prediction error: {e}")
            return None

# Singleton instance
predictor = WaitTimePredictor()
