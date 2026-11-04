# PDF RAG Chatbot with Ollama

Upload one or more PDFs, index their text into a local Chroma vector database, and ask questions in Streamlit. Ollama creates embeddings and generates answers on your computer. Each answer includes the source PDF and page number for the passages it used.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- VS Code with the Python extension
- Ollama: [ollama.com/download](https://ollama.com/download)

## 1. Install Ollama models

The app uses one model to write answers and a separate model to create searchable vectors. In a VS Code terminal, download both:

```powershell
ollama pull llama3.2
ollama pull nomic-embed-text
```

Check that both models appear in the local model list:

```powershell
ollama list
```

Ollama normally starts in the background. If the app cannot connect, start its server in a separate terminal and leave it running:

```powershell
ollama serve
```

The default server address is `http://localhost:11434`.

## 2. Install Python dependencies

Open this folder in VS Code. In the integrated PowerShell terminal, create and activate a virtual environment:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the environment's Python directly:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This workspace also has an `env1` environment. To use it, select `env1\Scripts\python.exe` with **Python: Select Interpreter** in VS Code, then install the requirements:

```powershell
.\env1\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Start the app

In VS Code, open **Terminal > New Terminal** and run:

```powershell
streamlit run app.py
```

Open the displayed local address, usually `http://localhost:8501`.

## 4. Upload and ask

1. In the app sidebar, upload one or more text-based PDF files. Each file can be up to 40 MB.
2. Select **Index PDFs** and wait for the passages to be embedded.
3. Ask a question in the chat. The app searches for the closest passages and gives them to Llama 3.2 as context.
4. Open **Sources** under an answer to see the PDF name, page, and text used for retrieval.

You can change the chat model, embedding model, Ollama address, chunk size, and number of retrieved passages in the sidebar. If you change or remove uploaded files, select **Index PDFs** again before chatting so the vector index matches the current uploads.

## How it works

The app extracts text page by page with `pypdf`, splits it into overlapping chunks, and asks Ollama's `nomic-embed-text` model to convert each chunk into a vector. Chroma stores those vectors in memory for the active Streamlit session. For each question, the app embeds the question, retrieves the closest chunks, and sends those passages with the conversation to `llama3.2`. The assistant is instructed to answer from the uploaded documents and cite its sources.

Uploaded PDFs and the vector index are not saved to disk; they need to be uploaded and indexed again after the app session ends. Scanned/image-only PDFs require OCR before upload because they do not contain selectable text.

## Troubleshooting

- **Could not reach Ollama:** Start Ollama and verify the host in the sidebar is `http://localhost:11434`.
- **Model not found:** Run `ollama pull llama3.2` or `ollama pull nomic-embed-text`, depending on which model the error names.
- **No selectable text found:** The PDF is probably scanned. Run OCR on it first, then upload the searchable PDF.
- **Changed PDFs:** Select **Index PDFs** again after adding or removing files.
- **PowerShell blocks activation:** Use the direct `env1\Scripts\python.exe` or `.venv\Scripts\python.exe` commands; activation is optional.