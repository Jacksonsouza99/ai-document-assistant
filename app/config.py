"""Configurações centrais do projeto.

Os caminhos são calculados a partir da posição deste arquivo, então funcionam
mesmo que você rode o comando de outra pasta.
"""
import os
from pathlib import Path

# Raiz do projeto = a pasta que contém "app"
ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = ROOT / "documents"
CHROMA_DIR = ROOT / "chroma_db"

# Banco do modo SEM IA (um único arquivo SQLite, sem instalar nada)
SQLITE_PATH = ROOT / "data" / "keyword.db"

# Coleção NOVA (com página nos metadados). A antiga, "documents", fica intacta.
COLLECTION_NAME = "documents_v2"

# Mesmo modelo que o projeto já usa (trocar exige reindexar tudo)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Modelo do Gemini (o mesmo que já estava no llm.py)
GEMINI_MODEL = "gemini-3.5-flash-lite"

CHUNK_SIZE = 1000
OVERLAP = 200

# Limite de tamanho para PDFs enviados
MAX_PDF_MB = 20

# --- Busca e respostas ---
# Quantos trechos buscar por pergunta
TOP_K = 4

# Distância máxima para um trecho ser considerado relevante (quanto MENOR a
# distância, mais parecido). 1.3 é um valor inicial; calibre com
# `python -m app.calibrar "sua pergunta"`. Dá para testar outro valor sem editar
# o código:  $env:RAG_MAX_DISTANCE = "1.1"
MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "1.3"))

MAX_QUESTION_CHARS = 500

# Palavra combinada com o modelo para dizer "isso não está nos trechos"
NO_ANSWER_TOKEN = "SEM_RESPOSTA"
NOT_FOUND_MESSAGE = "Não encontrei essa informação nos documentos enviados."

# --- Modo sem IA (busca por palavras-chave) ---
KEYWORD_TOP_K = 5

# Fração mínima dos termos da pergunta que o trecho precisa conter para valer
# como resposta (0.5 = pelo menos metade dos termos).
MIN_COVERAGE = 0.5
