# Real-Time Sentiment Analysis Platform

A full-stack, microservices-based application that ingests social media data, performs sentiment analysis using LLMs, and visualizes trends on a real-time dashboard.

## 🚀 Key Features
* **Automated Ingestion**: Simulates real-time data flow from social media sources.
* **AI-Powered Analysis**: Uses Gemini or HuggingFace models to classify text into Positive, Negative, or Neutral sentiments.
* **Real-Time Dashboard**: A responsive React/Vite frontend featuring live charts and data feeds.
* **Persistent Storage**: Historical sentiment data is stored in PostgreSQL for trend analysis.
* **Live Updates**: Utilizes WebSockets for instant data visualization without refreshing.

## 🛠 Prerequisites
* **Docker** and **Docker Compose** installed on your system.
* At least 4GB of RAM allocated to Docker.
* **Ports**: Ensure ports `3000` (Frontend) and `8000` (Backend) are available.

## ⚡ Quick Start
Follow these steps to get the platform running locally:

1. **Clone the repository** and navigate to the project root.
2. **Start the platform**:
   ```bash
   docker-compose up -d --build