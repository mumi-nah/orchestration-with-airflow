# Weather Data Pipeline with Apache Airflow

This project is a data pipeline built on **Docker** using **Apache Airflow**. It connects to the OpenWeatherMap API, extracts weather data, transforms it into a clean format, and uploads the results into **Google Cloud Storage (GCS)** as CSV files. The pipeline is designed to run daily and can be extended to feed into other systems like BigQuery for analysis.

---

## What the pipeline does

1. **Check API health**  
   Uses an Airflow `HttpSensor` to make sure the weather API is online and returning status 200 before continuing.

2. **Extract data**  
   Calls the OpenWeatherMap API with a `SimpleHttpOperator` to fetch current weather data for London (this can be changed to any city).

3. **Transform data**  
   A `PythonOperator` processes the raw JSON response:
   - Converts temperature from Kelvin to Fahrenheit.
   - Normalizes fields like city, coordinates, weather description, humidity, wind speed, sunrise/sunset times.
   - Saves the transformed data into a CSV string.

4. **Upload to GCS**  
   Another `PythonOperator` uses the `GCSHook` to upload the CSV into a GCS bucket.  
   The file name includes a timestamp to avoid overwriting and to keep a history of runs (idempotency).

---

## Requirements

- **Apache Airflow** (with LocalExecutor or CeleryExecutor)
- **Airflow Google Provider**:  
  Add this to `requirements.txt`:
`apache-airflow-providers-google`

- **Pandas** for data transformation
- **OpenWeatherMap API key** (free signup at openweathermap.org)
- **Google Cloud service account JSON key** with permissions to write to your GCS bucket

---

## Setup

1. **Clone the repo**  
 ```bash
 git clone https://github.com/mumi-nah/orchestration-with-airflow.git
 cd orchestration-with-airflow

2. **Install dependencies** 
Add the required packages to your Airflow image or environment.

3. **Add Requirements**
In the requirements.txt file, enter:
```
apache-airflow-providers-http
apache-airflow-providers-google```

4. Configure Airflow connections

    In the Airflow UI, go to Admin → Connections.

    Create a connection for the weather API:

    Conn Id: weather_api

    Conn Type: HTTP

    Host: https://api.openweathermap.org

Create a connection for GCP:

    Conn Id: gcp_conn

    Conn Type: Google Cloud

    Upload your service account JSON key.

5. Place the DAG file  
Copy weather_dag.py into your Airflow dags/ folder.

6. Run Airflow  
 Start the scheduler and webserver. Trigger the DAG manually or let it run daily.

 ## How to test locally
airflow tasks test weather_dag check_api 2026-04-15
airflow tasks test weather_dag extract_data 2026-04-15
airflow tasks test weather_dag transform_data 2026-04-15
airflow tasks test weather_dag upload_to_gcs 2026-04-15

## Example output
The pipeline produces CSV files in your GCS bucket with names like:
current_weather_data_london_20260415181900.csv

## Future improvements
Add more cities or make the city configurable.

Load data directly into BigQuery for analysis.

Add error handling and retries for API calls.

Schedule more frequently (e.g., hourly) for near‑real‑time monitoring.