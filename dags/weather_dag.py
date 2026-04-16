import json
import pendulum
import pandas as pd
from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook


def kelvin_to_fahrenheit(temp_in_kelvin):
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return temp_in_fahrenheit


def transform_data(ti):
    data = ti.xcom_pull(task_ids=extract_data)
    city = data["name"]
    longitude = data["coord"]["long"]
    latitude = data["coord"]["lat"]
    weather_description = data["weather"][0]["description"]
    temp_fahr = kelvin_to_fahrenheit(data["main"]["temp"])
    temp_feels_like = kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    normalized_data = {
        "City" : city,
        "Longitude":  longitude,
        "Latitude": latitude,
        "Description": weather_description,
        "Temperature (F)": temp_fahr,
        "FeelsLike (F)": temp_feels_like,
        "MinimunTemp (F)":min_temp_farenheit,
        "MaximumTemp (F)": max_temp_farenheit,
        "Pressure": pressure,
        "Humidty": humidity,
        "WindSpeed": wind_speed,
        "TimeOfRecord": time_of_record,
        "Sunrise(Local Time)":sunrise_time,
        "Sunset(Local Time)": sunset_time                        
        }

    transformed_data = pd.DataFrame([normalized_data])
    return transformed_data.to_csv(index=False)


def upload_to_gcs(ti):
    data = ti.xcom_pull(task_ids="transform_data")
    hook = GCSHook(gcp_conn_id="gcp_conn")
    dt_string = ti.execution_date.strftime("%Y%m%d%H%M%S")
    object_name = f"current_weather_data_london_{dt_string}.csv

    hook.upload(
        bucket_name="weathermap-data",
        object_name=object_name,
        data=data.encode("utf-8"),
        mime_type="text/csv"
    )


with DAG(
    dag_id="weather_dag",
    start_date=pendulum.datetime(2026, 4, 14, tz="UTC"),
    schedule="@daily",
    catchup=False
) as dag:

    check_api = HttpSensor(
        task_id="check_api",
        http_conn_id="weather_api",
        endpoint="data/2.5/weather?q=London&appid=67862819e0a02c166b39b47e3dd7ad19",
        response_check=lambda response: response.status_code == 200,
        poke_interval=60,
        timeout=600
    )

    extract_data = SimpleHttpOperator(
        task_id="extract_data",
        http_conn_id="weather_api",
        endpoint="data/2.5/weather?q=London&appid=67862819e0a02c166b39b47e3dd7ad19",
        method= "GET",
        response_filter= lambda response: json.loads(response.text),
        log_response=True
    )

    transform_data = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data
    )

    upload_to_gcs = PythonOperator(
        task_id="upload_to_gcs",
        python_callable=upload_to_gcs
    )


    check_api >> extract_data >> transform_data >> upload_to_gcs
