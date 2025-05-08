import os
import pathlib
import pandas as pd
import datetime


def get_files_metadata(folder_path: str):
    files = os.listdir(folder_path)

    file_paths = [os.path.join(folder_path, f) for f in files if
                  os.path.isfile(os.path.join(folder_path, f))]

    file_names = [pathlib.Path(f).name for f in file_paths]
    file_types = [pathlib.Path(f).suffix for f in file_paths]
    file_sizes = [os.path.getsize(f) for f in file_paths]
    last_modified_dates = [os.path.getmtime(f) for f in file_paths]
    last_modified_dates_str = [datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d') for date in
                               last_modified_dates]

    file_sizes_kb = [f'{size / 1024:,.2f} KB' for size in file_sizes]
    days_since_last_modified = [(datetime.datetime.now() - datetime.datetime.fromtimestamp(date)).days for date in
                                last_modified_dates]

    df = pd.DataFrame(
        data={
            'Path': file_paths,
            'Filename': file_names,
            'Type': file_types,
            'Size': file_sizes_kb,
            'Size (Raw)': file_sizes,
            'Last Modified': last_modified_dates_str,
            'Days Since Last Modified': days_since_last_modified,
        }
    )

    return df
