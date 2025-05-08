import json

import os

import PyPDF2
import pandas as pd
import requests
from send2trash import send2trash
from tqdm import tqdm

tqdm.pandas()

DATASET_PATH = 'web_search_dataset.json'
DATASET_FOLDER_PATH = 'web_search_dataset'


def main():
    with open(DATASET_PATH, 'r') as f:
        web_search_dataset = json.load(f)

    df = pd.DataFrame(web_search_dataset).drop('id', axis=1)
    df = df[df['Filename'].str.endswith('.pdf')]

    if not os.path.exists(DATASET_FOLDER_PATH):
        os.mkdir(DATASET_FOLDER_PATH)

    print(f'Downloading {len(df)} files...')
    df.progress_apply(_download_file, axis=1)

    print(f'Checking {len(df)} files...')
    df.progress_apply(_check_corrupted_file, axis=1)


def _download_file(row):
    url = row['URL']
    path = f'{DATASET_FOLDER_PATH}/{row["Filename"]}'

    try:
        response = requests.get(url, stream=True, timeout=20)

        if response.status_code != 200:
            return

        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except Exception:
        return


def _check_corrupted_file(row):
    path = f'{DATASET_FOLDER_PATH}/{row["Filename"]}'

    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            reader.pages
    except Exception:
        send2trash(path)


if __name__ == '__main__':
    main()
