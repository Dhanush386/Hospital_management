# Smart Hospital - Project Architecture

This document outlines the high-level architecture and data flow of the Smart Hospital Patient Flow Management System.

## System Overview
The system is built as a monolithic Django application with real-time capabilities powered by Django Channels and Redis. It integrates Machine Learning models for predictive analytics and Generative AI for clinical documentation.

## Core Components

### 1. Web Layer (Django)
- **Authentication**: Custom role-based access control (RBAC) for Patients, Doctors, Lab Technicians, Pharmacists, and Admins.
- **Queue Management**: Real-time tracking of patient flow using WebSockets.
- **Consultation Workflow**: Integrated prescription and lab ordering system.

### 2. Real-Time Layer (Django Channels)
- **WebSockets**: Used for broadcasting queue updates, doctor status changes, and notifications.
- **Redis**: Acts as the channel layer backbone for asynchronous communication.

### 3. AI & Data Science Layer
- **Wait Time Predictor (Random Forest)**: Predicts patient waiting times based on historical patterns and real-time congestion.
- **Queue Optimizer**: Assesses risk levels and provides adaptive recommendations for overloaded departments.
- **Clinical AI (Gemini)**: Converts raw consultation transcripts into structured SOAP notes.

### 4. Analytics Layer
- **Admin Dashboard**: Visualizes hospital performance metrics using Chart.js.
- **Efficiency Scoring**: Calculates doctor performance based on patient throughput and consultation time.

## Data Flow
1. **Patient Registration**: Patient joins a queue -> Token generated -> Wait time predicted.
2. **Real-Time Update**: New slot broadcasted via WebSockets to all dashboards.
3. **Consultation**: Doctor accepts patient -> Status changes to IN_PROGRESS.
4. **AI Generation**: Doctor records notes -> AI structures them into SOAP format.
5. **Completion**: Patient discharged -> Wait time error logged -> Model accuracy tracked.
