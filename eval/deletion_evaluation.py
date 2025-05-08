import random

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm

from core import metadata, suggest_deletions

matplotlib.rcParams['figure.dpi'] = 300

NUM_RUNS = 30


def _get_thresholds(df):
    min_size, max_size = df['Size (Raw)'].min(), df['Size (Raw)'].max()
    min_age, max_age = df['Days Since Last Modified'].min(), df['Days Since Last Modified'].max()

    size_threshold = random.randint(min_size // (1024 ** 2), max_size // (1024 ** 2)) * (1024 ** 2)
    age_threshold = random.randint(min_age, max_age)

    return size_threshold, age_threshold


def _find_duplicate_filenames(duplicates_tuples):
    duplicates = []
    for group in duplicates_tuples:
        for file in group:
            if ').' in file:
                duplicates.append(file)
    return duplicates


def _apply_labeling(df, duplicates, age_threshold, size_threshold):
    def _mark_for_deletion(row):
        if row['Filename'] in duplicates \
                or row['Days Since Last Modified'] > age_threshold \
                or row['Size (Raw)'] > size_threshold \
                or row['Type'] == '.exe':
            return 'Delete'
        return 'Keep'

    return df.apply(_mark_for_deletion, axis=1)


def _run_single_iteration():
    df = metadata.get_files_metadata('downloads_folder_dataset')
    size_threshold, age_threshold = _get_thresholds(df)

    duplicates_tuples = suggest_deletions.find_duplicates(df)
    duplicates = _find_duplicate_filenames(duplicates_tuples)

    df['Labeled Deletion'] = _apply_labeling(df, duplicates, age_threshold, size_threshold)

    df = suggest_deletions.suggest_deletions(df=df,
                                             age_threshold_days=age_threshold,
                                             size_threshold_kb=(size_threshold // 1024),
                                             stream_callback=print)

    return df['Labeled Deletion'], df['LLM-Delete']


def _evaluate_predictions(true_labels, predictions):
    accuracy = accuracy_score(true_labels, predictions)
    precision = precision_score(true_labels, predictions, average='weighted', zero_division=0)
    recall = recall_score(true_labels, predictions, average='weighted', zero_division=0)
    f1 = f1_score(true_labels, predictions, average='weighted')

    print(f'Accuracy: {accuracy:.4f}')
    print(f'Precision: {precision:.4f}')
    print(f'Recall: {recall:.4f}')
    print(f'F1: {f1:.4f}')

    cm = pd.crosstab(true_labels, predictions, rownames=['Actual'], colnames=['Predicted'])
    plt.figure(figsize=(3, 3))
    sns.heatmap(cm, annot=True, fmt='g', cmap='Blues', cbar=False)
    plt.title('Confusion Matrix for Deletion')
    plt.xlabel('Predicted Deletion')
    plt.ylabel('Actual Deletion')
    plt.tight_layout()
    plt.show()


def main():
    labeled_deletions = []
    llm_deletions = []

    for _ in tqdm(range(NUM_RUNS)):
        labeled, predicted = _run_single_iteration()
        labeled_deletions.append(labeled)
        llm_deletions.append(predicted)

    labeled_deletions = pd.concat(labeled_deletions, axis=0, ignore_index=True)
    llm_deletions = pd.concat(llm_deletions, axis=0, ignore_index=True)

    _evaluate_predictions(labeled_deletions, llm_deletions)


if __name__ == '__main__':
    main()
