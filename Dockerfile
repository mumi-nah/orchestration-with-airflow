FROM apache/airflow:slim-3.2.0-python3.13

USER airflow

COPY requirements.txt /requirements.txt

EXPOSE 8080

RUN pip install --no-cache-dir -r /requirements.txt