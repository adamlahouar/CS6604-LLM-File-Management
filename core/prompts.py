def get_keywords_prompt(filename: str, contents: str, num_keywords: int) -> str:
    prompt = f"""Please provide {num_keywords} keywords in a comma-separated list that describe the contents of this file ({filename}).
    If it's not possible, just reply with "Unknown". The file content is: {contents}"""

    return prompt


def get_categorize_prompt(df, use_keywords: bool = True, user_categories: list | None = None,
                          only_use_user_categories: bool = False) -> str:
    if use_keywords:
        filenames_str = '\n'.join(
            [f"{filename}: {keywords}" for filename, keywords in zip(df['Filename'], df['Keywords'])])
    else:
        filenames_str = '\n'.join(df['Filename'])

    prompt = f"""
    You are an AI that categorizes files in a user's Downloads folder based on filenames {'file types, and provided keywords.' if use_keywords else 'and file types.'}
    Your task is to generate a **valid JSON object** with the following structure:

    ```json
    {{
        "categories": ["Category 1", "Category 2", ...],
        "assignments": {{
            "filename1.ext": "Category 1",
            "filename2.ext": "Category 2",
            ...
        }}
    }}
    ```

    ### **Categorization Rules:**
    {'- **Use keywords to infer meaning** – If keywords are provided, prioritize them for categorization.' if use_keywords else ''}
    - **Consider file extensions** – Group similar file types together (e.g., `.png`, `.jpg` → "Images").
    - **Identify common patterns** – Installers, documents, spreadsheets, compressed files, etc.
    - **Be as specific as possible** – If a filename suggests a unique category, create one even if only a few files fit.
    - **Handle ambiguity properly** – If a filename lacks enough context, assign it to `"Other"`.
    """

    if user_categories:
        user_categories_str = '\n'.join(user_categories)

        if only_use_user_categories:
            prompt += """
                ### **IMPORTANT: Exclusively Use User Categories**
                The user has provided a set of categories. You must **only** assign files to these categories and **cannot** create new ones.
                Even if a file doesn't fit perfectly into any of the user-provided categories, you must still assign it to the best-fitting category.
                The file **should never be left unassigned**, even if it's ambiguous.
                User categories:
                """
        else:
            prompt += f"""
            ### **User Categories:**
            The user has provided the following categories for reference. These may be broad, specific, or only partially useful.
            Use them when they clearly apply, but do not force assignments if the fit isn't appropriate.
            You are encouraged to create new, more suitable categories if needed.
            Some user-provided categories may go unused — this is acceptable.
            User categories:
            """

        prompt += f'\n{user_categories_str}'

    prompt += f"""

    ### **Filenames to categorize:**
    {filenames_str}

    Return only the JSON output.
    """

    return prompt


def get_delete_prompt(df, duplicates, age_threshold_days, size_threshold_kb) -> str:
    filenames_str = '\n'.join(
        [f'{filename}: Size: {size}, Age: {age} days' for filename, size, age in
         zip(df['Filename'], df['Size'], df['Days Since Last Modified'])]
    )

    duplicates_str = '\n'.join([', '.join(group) for group in duplicates])

    prompt = f"""
    Based on the file metadata provided below, identify files that are candidates for deletion.
    Consider each file's size, age, and potential duplication status.

    If a file meets any of the following criteria, it should be considered for deletion:
    - More than {age_threshold_days} days old
    - Over {size_threshold_kb} KB
    - Is potentially a single-use installer ('wiztree_4_23_setup.exe' for example, because it contains 'setup' and is an exe file)
    - Is a duplicate of another file. For duplicates, only delete the "secondary" file, usually indicated by parenthesis (on Windows OS).

    Return a JSON object with the following structure:
    ```json
    {{
    "deletions": {{
        "filename1.ext": "reason1",
        "filename2.ext": "reason2",
        ...
        }}
    }}
    ```

    File metadata:
    {filenames_str}

    Duplicate groups:
    {duplicates_str}

    Return only the JSON output.
    """

    return prompt


def get_search_prompt(df, query: str, max_results: int) -> str:
    filenames_str = '\n'.join(
        [f'{filename}: {keywords}: {category}: {last_modified}' for filename, keywords, category, last_modified in
         zip(df['Filename'], df['Keywords'], df['LLM-Categorized'], df['Last Modified'])]
    )

    prompt = f"""
    Please find up to {max_results} files in the user's Downloads folder that best match the query "{query}".

    The files will be provided as a list in the format:
    `filename: keywords: category: last_modified`

    Notes:
    - Some files might not have keywords.
    - Categories are AI-generated and may not be perfect.
    - You may return **fewer than {max_results}** if only a few files are relevant.
    - Only include files that are genuinely related to the query.

    The files will be given to you as a list with the following format: filename: keywords: category: last_modified.
    Return a JSON object with the following structure:

    ```json
    {{
        "results": ["filename1.ext", "filename2.ext", ...]
    }}
    ```

    Files:
    {filenames_str}

    Return only the JSON output.
    """

    return prompt
