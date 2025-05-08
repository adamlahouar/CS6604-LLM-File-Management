import core.keywords
import core.prompts
import core.llm_interaction


def categorize(df, use_keywords: bool = True, user_categories: list | None = None,
               only_use_user_categories: bool = False, stream_callback=None, progress_callback=None):
    if use_keywords and 'Keywords' not in df.columns:
        df = core.keywords.get_keywords(df, progress_callback=progress_callback)

    prompt = core.prompts.get_categorize_prompt(df, use_keywords, user_categories, only_use_user_categories)

    json_response = core.llm_interaction.prompt_llm(model=core.llm_interaction.LLM.DEEPSEEK.value,
                                                    prompt=prompt,
                                                    context_length=int(len(prompt) * 1.5),
                                                    stream=True,
                                                    stream_callback=stream_callback)

    assignments = json_response.get('assignments', {})

    cleaned_assignments = {
        filename: category.replace('/', '-').replace('\\', '-') for filename, category in assignments.items()
    }

    df['LLM-Categorized'] = df['Filename'].map(lambda filename: cleaned_assignments.get(filename, 'Other'))

    return df
