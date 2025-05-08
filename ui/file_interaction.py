import os
import shutil

from send2trash import send2trash

DOWNLOADS_FOLDER = os.path.expanduser("~/Downloads")


def move_to_category_folders(df):
    for category in df['LLM-Categorized'].unique():
        category_path = os.path.join(DOWNLOADS_FOLDER, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)

    def move_file(row):
        file_path = row['Path']
        file_category = row['LLM-Categorized']
        category_path = os.path.join(DOWNLOADS_FOLDER, file_category)
        new_path = os.path.join(category_path, os.path.basename(file_path))
        try:
            shutil.move(file_path, new_path)
        except Exception as e:
            print(f'Failed to move {file_path} to {new_path}: {e}')

    df.apply(move_file, axis=1)


def delete_suggested_files(paths: list[str]):
    for path in paths:
        try:
            send2trash(path)
        except OSError as e:
            print(f'Failed to delete {path}: {e}')
