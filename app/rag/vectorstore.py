from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def get_vectorstore():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL
    )

    db = Chroma(
        persist_directory="db",
        embedding_function=embeddings
    )

    return db
