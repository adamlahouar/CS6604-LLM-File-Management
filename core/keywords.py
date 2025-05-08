import pandas as pd
import json
import os
import pathlib
import core.prompts
import core.llm_interaction
import PyPDF2
import docx
import csv

TEXT_BASED_FILETYPES = [
    '.doc', '.docx', '.pdf', '.txt', '.md', '.json', '.csv', '.xlsx', '.ppt', '.pptx',
    '.py', '.java', '.cpp', '.c', '.html', '.css', '.js', '.ts', '.sql', '.xml', '.yaml'
]

MAX_CONTENT_LENGTH = 1000
KEYWORDS_CONTEXT_LENGTH = 10_000
MAX_LINES = 20
MAX_PDF_PAGES = 5
NUM_KEYWORDS = 5
MAX_KEYWORDS_LENGTH = 200


def get_keywords(df, progress_callback=None):
    keywords = {}

    total = len(df)
    for i, path in enumerate(df['Path']):
        keywords[path] = _get_keywords(path)

        if progress_callback:
            progress_callback(i + 1, total)

    df['Keywords'] = df['Path'].map(keywords)

    return df


def _get_keywords(path):
    if pathlib.Path(path).suffix not in TEXT_BASED_FILETYPES:
        return 'N/A'

    try:
        file_content = _extract_file_content(path)[:MAX_CONTENT_LENGTH]
    except:
        return 'Unknown'

    filename = os.path.basename(path)

    prompt = core.prompts.get_keywords_prompt(filename, file_content, NUM_KEYWORDS)
    response = core.llm_interaction.prompt_llm(
        model=core.llm_interaction.LLM.PHI.value,
        prompt=prompt,
        context_length=KEYWORDS_CONTEXT_LENGTH,
        stream=False
    )

    return _fix_keywords_response(response)


def _extract_file_content(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    file_ext = path.split('.')[-1].lower()

    if file_ext in {'txt', 'md', 'py', 'java', 'cpp', 'c', 'html', 'css', 'js', 'ts', 'sql', 'xml', 'yaml'}:
        with open(path, 'r', encoding='utf-8') as f:
            return '\n'.join(f.readline().strip() for _ in range(MAX_LINES))

    elif file_ext == 'json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=4)[:1000] + '...' if len(json.dumps(data)) > 1000 else json.dumps(data,
                                                                                                             indent=4)

    elif file_ext == 'csv':
        with open(path, 'r', encoding='utf-8') as f:
            return '\n'.join([','.join(row) for _, row in zip(range(MAX_LINES), csv.reader(f))])

    elif file_ext in {'xlsx'}:
        df = pd.read_excel(path, sheet_name=None)
        return '\n'.join([f"Sheet: {sheet}\n" + df[sheet].head(MAX_LINES).to_csv(index=False) for sheet in df])

    elif file_ext in {'doc', 'docx'}:
        doc = docx.Document(path)
        return '\n'.join([para.text for para in doc.paragraphs[:MAX_LINES]])

    elif file_ext == 'pdf':
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = min(len(reader.pages), MAX_PDF_PAGES)
            return '\n'.join(
                [reader.pages[i].extract_text() for i in range(num_pages) if reader.pages[i].extract_text()])

    else:
        raise ValueError(f"File type not supported yet: {file_ext}")


def _fix_keywords_response(response):
    if response.count(',') == NUM_KEYWORDS - 1 and len(response) <= MAX_KEYWORDS_LENGTH:
        return response

    keywords = response.split(',')
    response = ', '.join(keywords[:NUM_KEYWORDS])

    return response if len(response) <= MAX_KEYWORDS_LENGTH else 'Unknown'
