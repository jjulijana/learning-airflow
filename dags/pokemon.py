from airflow.decorators import dag, task
from airflow import DAG

from datetime import datetime, timedelta
import requests
import random

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

@dag(
    dag_id="pokemon",
    start_date=datetime(2024, 4, 6),
    schedule="@daily",
    catchup=False,
    default_args={"owner": "admin", "retries": 5, "retry_delay": timedelta(minutes=5)},  # Using timedelta for retry_delay
    tags=["pokeapi"],
    doc_md=__doc__,
    render_template_as_native_obj=True,
    params={"n": 5}
)
def poke_dag():

    @task
    def get_all_pokemons() -> list:
        session = create_session_with_retries()
        count = session.get("https://pokeapi.co/api/v2/pokemon").json()["count"]

        response = session.get(f'https://pokeapi.co/api/v2/pokemon?limit={count}')
        results = response.json()["results"]

        print(f"Total number of pokemons: {count}")
        print("List of pokemons:")
        for result in results:
            print(result['name'])

        return [result['name'] for result in results]


    @task
    def get_pokemon_sample(pokemons: list[str], n: int = 5) -> list[str]:
        return random.sample(pokemons, n)
    
    @task
    def get_poke_info(name: str) -> dict:
        poke = {}
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{name}').json()

        poke['name'] = name
        poke['id'] = response['id']
        abilities_data = response['abilities']
        abilities = [ability_info['ability']['name'] for ability_info in abilities_data]
        poke['abilities'] = abilities
        types_data = response['types']
        types = [type['type']['name'] for type in types_data]
        poke['types'] = types
        poke['xp'] = response['base_experience']
        stats_data = response['stats']
        stats = {stat['stat']['name']: stat['base_stat'] for stat in stats_data}
        poke['stats'] = stats

        print(f"Information for Pokémon {name}:")
        print(poke)

        return poke


    pokemons = get_all_pokemons()
    pokemon_sample = get_pokemon_sample(pokemons, "{{ params.n }}")
    poke_info = get_poke_info.expand(name=pokemon_sample)

poke_dag = poke_dag()

    # get_pokemons_task = PythonOperator(
    #     task_id="get_all_pokemons",
    #     python_callable=get_all_pokemons
    # )

    # with TaskGroup("parallel_pokemon_tasks") as parallel_pokemon_tasks:
    #     for i in range(5):
    #         random_pokemon_task_id = f"get_random_pokemon_{i+1}"
    #         get_random_pokemon_task = PythonOperator(
    #             task_id=random_pokemon_task_id,
    #             python_callable=lambda: random.choice(get_all_pokemons())
    #         )
        
    #         get_pokemon_info_task_id = f"get_pokemon_info_{i+1}"
    #         get_pokemon_info_task = PythonOperator(
    #             task_id=get_pokemon_info_task_id,
    #             python_callable=get_poke_info,
    #             op_kwargs={'name': "{{ task_instance.xcom_pull(task_ids='" + random_pokemon_task_id + "') }}"},
    #             provide_context=True,
    #         )
            
    #         get_random_pokemon_task >> get_pokemon_info_task

    # get_pokemons_task >> parallel_pokemon_tasks 