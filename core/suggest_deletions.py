import collections
import core.prompts
import core.llm_interaction


def suggest_deletions(df, age_threshold_days: int, size_threshold_kb: int, stream_callback=None):
    duplicates = find_duplicates(df)

    prompt = core.prompts.get_delete_prompt(df, duplicates, age_threshold_days, size_threshold_kb)

    json_response = core.llm_interaction.prompt_llm(
        model=core.llm_interaction.LLM.DEEPSEEK.value,
        prompt=prompt,
        context_length=int(len(prompt) * 1.5),
        stream=True,
        stream_callback=stream_callback
    )

    deletion_suggestions = json_response.get('deletions', {})

    df['LLM-Delete'] = df['Filename'].apply(lambda filename: 'Delete' if filename in deletion_suggestions else 'Keep')

    df['LLM-Delete-Reason'] = df.apply(
        lambda row: deletion_suggestions[row['Filename']] if row['LLM-Delete'] == 'Delete' else '', axis=1)

    return df


def find_duplicates(df):
    potential_duplicates = collections.defaultdict(list)

    for index, row in df.iterrows():
        key = (row['Size (Raw)'], row['Type'])
        potential_duplicates[key].append(row['Filename'])

    duplicates = [files for files in potential_duplicates.values() if len(files) > 1]
    return duplicates
