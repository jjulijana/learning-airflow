import os
import zipfile
import tempfile
import hashlib
import requests
import ROOT
import pandas as pd
import logging
from datetime import datetime
import configparser
from sqlalchemy import create_engine, inspect
import click

# log_file = 'processing.log'
# logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# def add_separator_to_log():
#     separator = "\n" + "=" * 80 + "\n" + f"New Run: {datetime.now()}" + "\n" + "=" * 80 + "\n"
#     with open(log_file, 'a') as log:
#         log.write(separator)

@click.command()
@click.argument('url')
@click.argument('download_path')
def download_zip(url, download_path):
    response = requests.get(url)
    # logging.info(f"Started downloading zip file from {url}.")
    if response.status_code == 200:
        with open(download_path, 'wb') as f:
            f.write(response.content)
        # logging.info(f"Zip file downloaded.")
    else:
        # logging.error(f"Failed to download zip file from {url}, status code: {response.status_code}.")
        raise Exception(f"Failed to download zip file from {url}.")

@click.command()
@click.argument('zip_file_path')
@click.argument('extracted_path')
def extract_zip(zip_file_path, extracted_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_path)
        # logging.info(f"Extracted zip file to {extracted_path}.")

@click.command()
@click.argument('root_file_path')
@click.argument('csv_output_path')
def process_root_file_to_csv(root_file_path, csv_output_path):
    # logging.info(f"Processing ROOT file {root_file_path}:")
    root_file = ROOT.TFile.Open(root_file_path)
    
    if not root_file or root_file.IsZombie():
        # logging.error(f"Unable to open the ROOT file {os.path.basename(root_file_path)}.")
        return

    for key in root_file.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, ROOT.TTree):
            tree = obj
            tree_name = tree.GetName()
            # logging.info(f"Processing TTree {tree_name} from {os.path.basename(root_file_path)}:")

            output_file = os.path.join(csv_output_path, f"{os.path.basename(root_file_path)}_{tree_name}.csv")
            
            data = {}
            for branch in tree.GetListOfBranches():
                branch_name = branch.GetName()
                data[branch_name] = []

            for entry in tree:
                for branch_name in data.keys():
                    data[branch_name].append(getattr(entry, branch_name))

            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            # logging.info(f"\tCSV file has been created: {output_file}.")


def read_db_config(filename='db_config.ini', section='postgresql'):
    parser = configparser.ConfigParser()
    parser.read(filename)

    db_config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_config[param[0]] = param[1]
        logging.info(f"\tRead credentials for {section} database.")
    else:
        logging.error(f"\tFailed to read credentials for {section} database.")
        raise Exception(f'\tSection {section} not found in the {filename} file.')

    return db_config

def hash_table_name(table_name, max_length=63):
    if len(table_name) > max_length:
        hash_object = hashlib.md5(table_name.encode())
        hash_suffix = hash_object.hexdigest()[:8]
        return f"{table_name[:max_length-9]}_{hash_suffix}"
    return table_name

@click.command()
@click.argument('csv_file')
@click.argument('table_name')
def add_table_to_postgres(csv_file, table_name):
    try:
        db_config = read_db_config()
        db_uri = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(db_uri)
    except Exception as e:
        # logging.error(f"\tError reading database config or creating engine: {e}.")
        raise

    try:
        connection = engine.connect()
        # logging.info("\tDatabase connection established.")
    except Exception as e:
        # logging.error(f"\tError establishing database connection: {e}.")
        raise

    df = pd.read_csv(csv_file)

    inspector = inspect(engine)
    if inspector.has_table(table_name):
        # logging.info(f"\tTable {table_name} already exists. Updating data.")
        df.to_sql(hash_table_name(table_name), engine, if_exists='replace', index=False)
    else:
        # logging.info(f"\tTable {table_name} created.")
        df.to_sql(hash_table_name(table_name), engine, if_exists='append', index=False)
        # logging.info(f"\tData inserted into table {table_name}.")

    connection.close()
    # logging.info("\tDatabase connection closed.")

@click.group()
def cli():
    pass

cli.add_command(download_zip)
cli.add_command(extract_zip)
cli.add_command(process_root_file_to_csv)
cli.add_command(add_table_to_postgres)

if __name__ == '__main__':
    # add_separator_to_log()
    cli()
