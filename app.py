"""Chat with uploaded PDFs using Ollama embeddings and Chroma retrieval."""

import hashlib
import io
import uuid

import chromadb
import ollama
import streamlit as st
from pypdf import PdfReader


DEFAULT_CHAT_MODEL = "llama3.2"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_HOST = "http://localhost:11434"
CHUNK_OVERLAP = 180
EMBED_BATCH_SIZE = 32


def uploaded_files_signature(files):
    """Return a stable fingerprint so stale indexes are not used by mistake."""
    digest = hashlib.sha256()
    for uploaded_file in files:
        digest.update(uploaded_file.name.encode("utf-8"))
        digest.update(uploaded_file.getvalue())
    return digest.hexdigest()


def split_text(text, chunk_size):
    """Split page text into overlapping chunks, preferring word boundaries."""
    text = " ".join(text.split())
    chunks = []
    start = 0
    overlap = min(CHUNK_OVERLAP, chunk_size // 4)

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)

    return chunks


def extract_pdf_chunks(uploaded_files, chunk_size):
    """Extract page text and retain filename/page metadata for citations."""
    documents = []
    metadatas = []
    ids = []

    for file_number, uploaded_file in enumerate(uploaded_files):
        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            for chunk_number, chunk in enumerate(split_text(page_text, chunk_size)):
                documents.append(chunk)
                metadatas.append(
                    {
                        "source": uploaded_file.name,
                        "page": page_number,
                        "chunk": chunk_number,
                    }
                )
                ids.append(f"file-{file_number}-page-{page_number}-chunk-{chunk_number}")

    return documents, metadatas, ids


def build_vector_index(client, embedding_model, documents, metadatas, ids):
    """Embed document chunks with Ollama and store vectors in an in-memory Chroma collection."""
    vector_client = chromadb.Client()
    collection = vector_client.create_collection(
        name=f"pdf-rag-{uuid.uuid4().hex}",
        metadata={"hnsw:space": "cosine"},
    )

    for start in range(0, len(documents), EMBED_BATCH_SIZE):
        stop = start + EMBED_BATCH_SIZE
        batch_documents = documents[start:stop]
        response = client.embed(model=embedding_model, input=batch_documents)
        collection.add(
            ids=ids[start:stop],
            documents=batch_documents,
            metadatas=metadatas[start:stop],
            embeddings=response.embeddings,
        )

    return vector_client, collection


def retrieve_chunks(client, collection, embedding_model, question, result_count):
    """Embed the current question and retrieve its closest document chunks."""
    response = client.embed(model=embedding_model, input=question)
    results = collection.query(
        query_embeddings=[response.embeddings[0]],
        n_results=min(result_count, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    return [
        {"text": text, "source": metadata["source"], "page": metadata["page"]}
        for text, metadata in zip(documents, metadatas)
    ]


def stream_reply(client, model, messages, errors):
    """Yield response text while recording any Ollama error for the UI."""
    try:
        response = client.chat(model=model, messages=messages, stream=True)
        for chunk in response:
            text = chunk.message.content or ""
            if text:
                yield text
    except Exception as error:
        errors.append(error)


def show_ollama_error(error, model_name):
    """Show actionable guidance for model, connection, and other Ollama errors."""
    details = str(error)
    if getattr(error, "status_code", None) == 404 or "model not found" in details.lower():
        st.error(f"Model not found. Download it with `ollama pull {model_name}`.")
    elif any(
        phrase in details.lower()
        for phrase in ("connection refused", "failed to connect", "connecterror")
    ):
        st.error("Could not reach Ollama. Start Ollama and check its host address in the sidebar.")
    else:
        st.error(f"Ollama returned an error: {details}")


st.set_page_config(page_title="Chat with your PDFs", page_icon=":material/menu_book:")
st.title("Chat with your PDFs")
st.caption("Upload documents, index their contents locally, then ask questions grounded in those pages.")
st.subheader("1. Upload your PDFs")

uploaded_files = st.file_uploader(
    "Choose one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    max_upload_size=40,
    key="pdf_uploads",
    help="Text-based PDFs up to 40 MB each. Scanned image-only PDFs need OCR first.",
)
uploaded_files = uploaded_files or []
current_signature = uploaded_files_signature(uploaded_files)

index_clicked = st.button(
    "Index PDFs",
    type="primary",
    width="stretch",
    disabled=not uploaded_files,
    icon=":material/search:",
)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("vector_client", None)
st.session_state.setdefault("collection", None)
st.session_state.setdefault("indexed_signature", None)
st.session_state.setdefault("indexed_files", [])
st.session_state.setdefault("indexed_chunk_count", 0)

with st.sidebar:
    st.subheader("Ollama settings")
    ollama_host = st.text_input("Ollama host", value=DEFAULT_HOST).strip()
    chat_model = st.text_input("Chat model", value=DEFAULT_CHAT_MODEL).strip()
    embedding_model = st.text_input("Embedding model", value=DEFAULT_EMBED_MODEL).strip()
    chunk_size = st.slider("Chunk size", min_value=500, max_value=2500, value=1200, step=100)
    result_count = st.slider("Retrieved passages", min_value=1, max_value=8, value=4)

    if st.session_state.collection is not None:
        st.caption(
            f"Indexed {st.session_state.indexed_chunk_count} passages from "
            f"{len(st.session_state.indexed_files)} PDF(s)."
        )
    if st.button("Clear conversation", width="stretch", icon=":material/delete:"):
        st.session_state.messages = []
        st.rerun()

if index_clicked:
    try:
        client = ollama.Client(host=ollama_host)
        with st.status("Reading PDFs and creating the vector index", expanded=True) as status:
            documents, metadatas, ids = extract_pdf_chunks(uploaded_files, chunk_size)
            if not documents:
                raise ValueError(
                    "No selectable text was found. This may be a scanned PDF; run OCR on it first."
                )
            status.write(f"Extracted {len(documents)} text passages. Creating embeddings...")
            vector_client, collection = build_vector_index(
                client, embedding_model, documents, metadatas, ids
            )
            st.session_state.vector_client = vector_client
            st.session_state.collection = collection
            st.session_state.indexed_signature = current_signature
            st.session_state.indexed_files = [file.name for file in uploaded_files]
            st.session_state.indexed_chunk_count = len(documents)
            st.session_state.messages = []
            status.update(label="PDFs indexed", state="complete", expanded=False)
    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        show_ollama_error(error, embedding_model)

index_is_current = (
    st.session_state.collection is not None
    and st.session_state.indexed_signature == current_signature
)
if uploaded_files and st.session_state.collection is None:
    st.info("Upload your PDFs, then select **Index PDFs** to make them searchable.")
elif st.session_state.collection is not None and not index_is_current:
    st.warning("The uploaded PDFs changed. Select **Index PDFs** before asking another question.")
elif index_is_current:
    st.success(
        f"Ready to chat about {len(st.session_state.indexed_files)} PDF(s) "
        f"and {st.session_state.indexed_chunk_count} passages."
    )
else:
    st.info("Choose one or more PDF files above, then select **Index PDFs** to make them searchable.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(f"**{source['source']}**, page {source['page']}")
                    st.caption(source["text"])

prompt = st.chat_input("Ask a question about your indexed PDFs...")
if prompt:
    if not ollama_host or not chat_model or not embedding_model:
        st.warning("Enter an Ollama host, chat model, and embedding model in the sidebar.")
    elif not index_is_current:
        st.warning("Upload and index your PDFs before asking a question.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = ollama.Client(host=ollama_host)
        errors = []
        with st.chat_message("assistant"):
            try:
                sources = retrieve_chunks(
                    client,
                    st.session_state.collection,
                    embedding_model,
                    prompt,
                    result_count,
                )
                context = "\n\n".join(
                    f"[Source: {source['source']}, page {source['page']}]\n{source['text']}"
                    for source in sources
                )
                system_message = (
                    "Answer using only the source passages below. If the passages do not "
                    "contain the answer, say that the uploaded documents do not provide it. "
                    "Cite supporting sources by filename and page.\n\n"
                    f"SOURCE PASSAGES:\n{context}"
                )
                chat_messages = [{"role": "system", "content": system_message}]
                chat_messages.extend(
                    {"role": message["role"], "content": message["content"]}
                    for message in st.session_state.messages
                )
                reply = st.write_stream(stream_reply(client, chat_model, chat_messages, errors))
                if errors:
                    show_ollama_error(errors[0], chat_model)
                elif reply:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"**{source['source']}**, page {source['page']}")
                            st.caption(source["text"])
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply, "sources": sources}
                    )
            except Exception as error:
                show_ollama_error(error, embedding_model)