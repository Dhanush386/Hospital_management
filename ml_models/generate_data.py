import pandas as pd
import numpy as np
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

DEPARTMENTS = ['GENERAL', 'CARDIOLOGY', 'ORTHOPEDICS', 'PEDIATRICS',
               'DERMATOLOGY', 'ENT', 'OPHTHALMOLOGY', 'NEUROLOGY']

DEPT_BASE_WAIT = {
    'GENERAL': 10, 'CARDIOLOGY': 25, 'ORTHOPEDICS': 20,
    'PEDIATRICS': 15, 'DERMATOLOGY': 12, 'ENT': 15,
    'OPHTHALMOLOGY': 15, 'NEUROLOGY': 30
}


def generate_hospital_data(n_samples=800):
    data = []

    for i in range(n_samples):
        dept = random.choice(DEPARTMENTS)
        hour = random.randint(8, 20)        # Hospital hours: 8 AM – 8 PM
        day_of_week = random.randint(0, 6)  # 0 = Monday

        # ---- Simulate realistic congestion patterns ----
        is_peak_hour = 1 if (10 <= hour <= 13 or 17 <= hour <= 19) else 0
        is_busy_day  = 1 if day_of_week in [0, 4] else 0   # Mon & Fri busier

        avg_queue = 5 + (is_peak_hour * 10) + (is_busy_day * 5)
        queue_length = max(1, int(np.random.normal(avg_queue, 3)))

        # Doctors online (peak hours get extra staff)
        doctor_count = random.randint(2, 5) if is_peak_hour else random.randint(1, 3)

        # ---- Target: actual_wait_time (minutes) ----
        # Derived from domain logic + Gaussian noise
        noise = np.random.normal(0, 4)
        raw_wait = (DEPT_BASE_WAIT[dept]
                    + (queue_length / doctor_count) * 12
                    + noise)
        actual_wait_time = max(5, int(round(raw_wait)))

        consultation_duration = max(5, int(np.random.normal(DEPT_BASE_WAIT[dept] * 0.8, 3)))
        status = random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'NO_SHOW'])
        doctor_id = f'D{random.randint(1, doctor_count):03d}'
        appointment_time = f"{hour:02d}:{random.randint(0, 59):02d}"

        data.append({
            'Patient_ID': f'P{i+1:05d}',
            'Department': dept,
            'Doctor_ID': doctor_id,
            'Appointment_Time': appointment_time,
            'Hour': hour,
            'Day_of_Week': day_of_week,
            'Queue_Length': queue_length,
            'Doctor_Count': doctor_count,
            'Is_Peak_Hour': is_peak_hour,
            'Consultation_Duration': consultation_duration,
            'Wait_Time': actual_wait_time,
            'Status': status
        })

    df = pd.DataFrame(data)
    import os
    out_path = os.path.join(os.path.dirname(__file__), 'historical_data.csv')
    df.to_csv(out_path, index=False)
    print(f"[OK] Generated {n_samples} records -> {out_path}")
    print(df[['Department', 'Queue_Length', 'Wait_Time']].describe())
    return df


if __name__ == '__main__':
    generate_hospital_data()
