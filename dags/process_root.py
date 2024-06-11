from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    'docker_sample_dag',
    default_args=default_args,
    description='A simple DockerOperator DAG',
    schedule_interval='@daily',
    start_date=days_ago(1),
    tags=['example'],
) as dag:

    t1 = DockerOperator(
        task_id='run_docker_container',
        image='ubuntu:latest',
        api_version='auto',
        auto_remove=True,
        command='/bin/sleep 30',
        docker_url='unix://var/run/docker.sock',
        network_mode='bridge',
    )

    t1
