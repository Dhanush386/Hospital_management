# Smart Hospital: AI-Integrated Patient Flow System

An industrial-grade, AI-driven hospital workflow optimization platform built for real-time patient management and clinical intelligence.

## 🌟 Key Features

### 1. Predictive Analytics
- **ML-Based Wait Times**: Real-time waiting time predictions using a Random Forest model.
- **Accuracy Monitoring**: Self-monitoring system that tracks predicted vs actual wait times.
- **Model Interpretability**: Visualized feature importance (Queue length vs Doctor load).

### 2. Intelligent Queue Management
- **Real-Time WebSockets**: Instant updates across all hospital roles.
- **Risk Assessment**: 🟢 Low, 🟡 Medium, 🔴 High congestion detection.
- **Adaptive Recommendations**: Suggests alternative doctors/departments to reduce congestion.

### 3. AI clinical Documentation
- **NLP SOAP Generator**: Uses Google Gemini to structure raw consultation transcripts into professional clinical notes.
- **Integrated Workflow**: Seamless link between consultation, prescriptions, and lab orders.

### 4. Advanced Analytics Dashboard
- **Performance Metrics**: Doctor efficiency scores and department footfall analysis.
- **Peak Hour Analysis**: Predicted peak hours based on historical data.

## 🛠️ Technology Stack
- **Backend**: Django, Django Channels (WebSockets), Redis.
- **Database**: SQLite (Development) / PostgreSQL (Production).
- **ML/DS**: Scikit-Learn, Pandas, NumPy, Joblib.
- **Generative AI**: Google Gemini Pro (LLM).
- **Frontend**: Bootstrap 5, Chart.js, HTML5/JS.

## 🚀 Setup Instructions
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure `.env` with your `GEMINI_API_KEY`.
4. Run migrations: `python manage.py migrate`.
5. Start the server: `python manage.py runserver`.
