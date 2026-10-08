import chromadb
from sentence_transformers import SentenceTransformer

from app.reader import extract_text
from app.chunker import split_text

from pathlib import Path


# Modelo responsável pelos embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")


# Banco vetorial local
client = chromadb.PersistentClient(path="chroma_db")


# Coleção onde vamos guardar nossos documentos
collection = client.get_or_create_collection(
    name="documents"
)


# Encontrar o primeiro PDF
pdfs = list(Path("documents").glob("*.pdf"))

if not pdfs:
    print("Nenhum PDF encontrado.")
    raise SystemExit(1)


pdf = pdfs[0]

print(f"Processando: {pdf.name}")


# 1. Extrair texto
text = extract_text(str(pdf))


# 2. Dividir em chunks
chunks = split_text(text)


print(f"Chunks encontrados: {len(chunks)}")


# 3. Criar embeddings
embeddings = model.encode(chunks).tolist()


# 4. Criar IDs
ids = [
    f"{pdf.stem}_chunk_{i}"
    for i in range(len(chunks))
]


# 5. Guardar no banco vetorial
collection.upsert(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=[
        {
            "arquivo": pdf.name
        }
        for _ in chunks
    ]
)


print("Documento armazenado no ChromaDB.")
print(f"Total de registros: {collection.count()}")
