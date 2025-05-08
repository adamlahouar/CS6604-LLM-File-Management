import math

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import StratifiedKFold

from core import categorize, metadata

matplotlib.rcParams['figure.dpi'] = 300

MAX_CHUNK_SIZE = 300


def main():
    print("\n--- Evaluating Downloads folder dataset ---")
    _evaluate_dataset(
        metadata_folder='downloads_folder_dataset',
        labels_file='DOWNLOADS_FOLDER_DATASET_MANUALLY_LABELED.csv',
        label="Downloads"
    )

    print("\n--- Evaluating web_search_dataset folder ---")
    _evaluate_dataset(
        metadata_folder='web_search_dataset',
        labels_file='WEB_SEARCH_DATASET_MANUALLY_LABELED.csv',
        label="Web_Search"
    )


def _evaluate_dataset(metadata_folder, labels_file, label):
    manually_labelled_df = pd.read_csv(labels_file)

    df = metadata.get_files_metadata(metadata_folder)

    user_categories = manually_labelled_df['Labeled Category'].unique().tolist()

    results = {
        "Without Keywords": _run_categorization(df, manually_labelled_df, user_categories, use_keywords=False),
        "With Keywords": _run_categorization(df, manually_labelled_df, user_categories, use_keywords=True),
    }

    for sublabel, categorized_df in results.items():
        metrics = _compute_metrics(categorized_df)
        _display_results(categorized_df, f"{label}_{sublabel.replace(' ', '_')}", metrics)


def _run_categorization(df, manually_labelled_df, user_categories, use_keywords):
    merged_df = df.merge(manually_labelled_df[['Filename', 'Labeled Category']], on='Filename')
    y = merged_df['Labeled Category'].values
    df = merged_df

    total_rows = len(df)

    if total_rows > MAX_CHUNK_SIZE:
        n_splits = math.ceil(total_rows / MAX_CHUNK_SIZE)
        print(f"Splitting dataset of {total_rows} rows into {n_splits} stratified chunks...")

        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        categorized_dfs = []

        for i, (_, split_index) in enumerate(skf.split(df, y)):
            split_df = df.iloc[split_index].copy()
            split_user_categories = split_df['Labeled Category'].unique().tolist()

            print(f"Categorizing split {i + 1}/{n_splits} (size: {len(split_df)})...")
            categorized_split = categorize.categorize(
                split_df,
                use_keywords=use_keywords,
                user_categories=split_user_categories,
                only_use_user_categories=True,
                stream_callback=print
            )
            categorized_dfs.append(categorized_split)

        categorized_df = pd.concat(categorized_dfs, ignore_index=True)
    else:
        print(f"Categorizing full dataset of {total_rows} rows without splitting.")
        categorized_df = categorize.categorize(
            df,
            use_keywords=use_keywords,
            user_categories=user_categories,
            only_use_user_categories=True,
            stream_callback=print
        )

    return categorized_df


def _compute_metrics(categorized_df):
    return {
        "accuracy": accuracy_score(categorized_df['Labeled Category'], categorized_df['LLM-Categorized']),
        "precision": precision_score(categorized_df['Labeled Category'], categorized_df['LLM-Categorized'],
                                     average='weighted', zero_division=0),
        "recall": recall_score(categorized_df['Labeled Category'], categorized_df['LLM-Categorized'],
                               average='weighted', zero_division=0),
        "f1": f1_score(categorized_df['Labeled Category'], categorized_df['LLM-Categorized'], average='weighted')
    }


def _display_results(categorized_df, label, metrics):
    print(f'\nEvaluation metrics for {label.replace("_", " ")}:')
    for metric_name, metric_value in metrics.items():
        print(f'{metric_name.capitalize()}: {metric_value:.4f}')

    cm = pd.crosstab(categorized_df['Labeled Category'], categorized_df['LLM-Categorized'],
                     rownames=['Actual'], colnames=['Predicted'])

    rows = [cat for cat in cm.index if cat != 'Other'] + (['Other'] if 'Other' in cm.index else [])
    cols = [cat for cat in cm.columns if cat != 'Other'] + (['Other'] if 'Other' in cm.columns else [])

    cm = cm.loc[rows, cols]

    plt.figure(figsize=(16, 16))
    sns.heatmap(cm, annot=True, fmt='g', cmap='Blues', cbar=False)
    plt.title(f'Confusion Matrix for {label.replace("_", " ")}')
    plt.xlabel('Predicted Category')
    plt.ylabel('Actual Category')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
