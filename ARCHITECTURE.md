# Project Architecture: Real-Time Sentiment Analysis Platform

## 1. System Overview
This platform is designed to ingest, analyze, and visualize social media sentiment in real-time using a microservices-based architecture.

## 2. Data Flow
The system follows a pipeline architecture to ensure scalability and real-time responsiveness:

1.  **Ingestion Layer**: The `Ingester` service simulates or fetches raw social media data and publishes it to a **Redis** message queue.
2.  **Processing Layer**: The `Worker` service subscribes to Redis, pulls raw posts, and uses an **LLM** (Gemini/HuggingFace) to perform sentiment analysis.
3.  **Storage Layer**: Analyzed results are stored in a **PostgreSQL** database for historical tracking.
4.  **API Layer**: The **FastAPI** backend serves the data via REST endpoints and pushes live updates to the frontend using **WebSockets**.
5.  **Visualization Layer**: The **React/Vite** dashboard displays real-time charts (Pie and Line) and a live feed.



## 3. Database Schema
The core of the data storage is the `posts` table in PostgreSQL:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID/Serial | Unique identifier for each post. |
| `text` | TEXT | The raw content of the social media post. |
| `sentiment` | VARCHAR | The analyzed sentiment: positive, negative, or neutral. |
| `score` | FLOAT | The confidence score from the LLM. |
| `created_at` | TIMESTAMP | The time the post was analyzed and stored. |

## 4. Component Interaction
* **Redis**: Acts as the asynchronous bridge between the Ingester and the Worker.
* **WebSockets**: Enables the "Live Feed" feature without requiring page refreshes.
* **Tailwind CSS**: Used for the dark-themed, responsive dashboard layout.