## CS6604-LLM-File-Management

### Setup Instructions:

1. Clone the repository
2. Download and install Ollama: https://ollama.com/download
3. Pull the DeepSeek model: `ollama run deepseek-r1:14b`

> **Note:**
> If the `deepseek-r1:14b` model is too large for your system, try using a smaller
> one: https://ollama.com/library/deepseek-r1
> Additionally, you'll need to edit the `DEEPSEEK` model name in `core/llm_interaction.py` to match the version you
> chose.

4. Pull the Phi-3 model: `ollama run phi3:3.8b-mini-128k-instruct-q4_K_M`
5. Install Python dependencies: `pip install -r requirements.txt`
6. (Optional) If you want to run the categorization evaluation, you'll need to download the 'Web Search' dataset:
   `python eval/get_web_search_dataset.py`

> **Note:**
> The categorization evaluation can only be run on the 'Web Search' dataset, as the 'Downloads Folder' dataset is not
> provided due to privacy concerns. You can still run the evaluation on the 'Web Search' dataset to test the
> categorization feature's functionality.

### Usage:

> ⚠️ **Warning:**
> Before running anything, make a backup of your Downloads folder and move it to another location just in case.

- To run the UI: `streamlit run ui/ui.py`
- To run the categorization evaluation: `python eval/categorization_evaluation.py`

### Contact:

If you run into any issues, please let me know at [adamlahouar@vt.edu](mailto:adamlahouar@vt.edu)