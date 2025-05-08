import ollama
import json
from enum import Enum


class LLM(Enum):
    DEEPSEEK = 'deepseek-r1:14b'
    PHI = 'phi3:3.8b-mini-128k-instruct-q4_K_M'


def prompt_llm(model: str, prompt: str, context_length: int, stream: bool = False, stream_callback=None):
    if not stream:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0, 'num_ctx': context_length}
        )
        return response['message']['content']

    stream_response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0, 'num_ctx': context_length},
        stream=True
    )

    full_response = ''
    for chunk in stream_response:
        text = chunk['message']['content']
        full_response += text
        if stream_callback:
            if stream_callback == print:
                print(text, end='', flush=True)
            else:
                stream_callback(full_response)

    if model != LLM.DEEPSEEK.value:
        return full_response

    try:
        json_part = full_response.split('</think>')[1].replace('```json', '').replace('```', '')
        return json.loads(json_part)
    except json.JSONDecodeError:
        return None
