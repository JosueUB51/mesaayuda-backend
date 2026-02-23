from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def ingest_pdf():
    loader = PyPDFLoader("data/Procesos_Mesa_de_Ayuda.pdf")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL
    )

    db = Chroma.from_documents(chunks, embeddings, persist_directory="db")
    db.persist()

    print("PDF indexado correctamente.")
