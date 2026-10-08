import chromadb
from sentence_transformers import SentenceTransformer
from app.llm import gerar_resposta


# ============================================================
# 1. MODELO DE EMBEDDINGS
# ============================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# 2. BANCO VETORIAL
# ============================================================

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    name="documents"
)


# ============================================================
# 3. BUSCA SEMÂNTICA
# ============================================================

def buscar_documentos(pergunta: str, quantidade: int = 3):

    pergunta_embedding = model.encode(
        [pergunta]
    ).tolist()

    resultados = collection.query(
        query_embeddings=pergunta_embedding,
        n_results=quantidade
    )

    return resultados["documents"][0]


# ============================================================
# 4. MONTAR O CONTEXTO
# ============================================================

def montar_contexto(documentos):

    contexto = ""

    for i, documento in enumerate(documentos, start=1):

        contexto += f"""
--- TRECHO {i} ---

{documento}

"""

    return contexto


# ============================================================
# 5. TESTE
# ============================================================

if __name__ == "__main__":

    pergunta = input(
        "Faça uma pergunta sobre o documento: "
    )

    documentos = buscar_documentos(pergunta)

    contexto = montar_contexto(documentos)      
    
    resposta = gerar_resposta(
        pergunta,
        contexto
    )        


    print("\n")
    print("=" * 70)
    print("CONTEXTO ENCONTRADO PELO RAG")
    print("=" * 70)

    print(contexto)
    
    print("\n")
    print("=" * 70)
    print("RESPOSTA DO GEMINI")
    print("=" * 70)
    
    print(resposta)
    