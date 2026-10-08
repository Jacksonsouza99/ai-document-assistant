import chromadb
from sentence_transformers import SentenceTransformer


# Modelo de embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")


# Conectar ao banco vetorial existente
client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection(
    name="documents"
)


# Pergunta do usuário
pergunta = input("Faça uma pergunta sobre o documento: ")


# Transformar a pergunta em vetor
pergunta_embedding = model.encode(
    [pergunta]
).tolist()


# Buscar os chunks mais relevantes
resultados = collection.query(
    query_embeddings=pergunta_embedding,
    n_results=3
)


print("\n" + "=" * 70)
print("TRECHOS MAIS RELEVANTES")
print("=" * 70)


for i, documento in enumerate(resultados["documents"][0], start=1):
    print(f"\n--- RESULTADO {i} ---")
    print(documento)