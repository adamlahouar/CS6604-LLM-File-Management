from core import categorize, prompts, llm_interaction


def search(df, query: str, max_results: int, stream_callback=None):
    if 'LLM-Categorized' not in df.columns:
        df = categorize.categorize(df)

    prompt = prompts.get_search_prompt(df, query, max_results)

    json_response = llm_interaction.prompt_llm(
        model=llm_interaction.LLM.DEEPSEEK.value,
        prompt=prompt,
        context_length=int(len(prompt) * 1.5),
        stream=True,
        stream_callback=stream_callback
    )

    return json_response.get('results', [])
