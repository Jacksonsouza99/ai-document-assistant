"""Busca semântica: transforma a pergunta em vetor e acha os trechos mais parecidos."""
from app import config
from app.vector_store import gerar_embeddings


def similaridade(distancia: float) -> float:
    """Converte a distância em uma nota de 0 a 1, só para exibir na tela.

    Vale como aproximação quando os vetores são normalizados (é o caso do
    all-MiniLM-L6-v2) e a distância é L2 ao quadrado (padrão do ChromaDB):
    nesse caso distância = 2 - 2 * cosseno.
    """
    return max(0.0, min(1.0, 1 - distancia / 2))


def buscar(pergunta, colecao, embed=None, k=None, max_distancia=None) -> list[dict]:
    """Devolve os trechos mais parecidos com a pergunta, do mais para o menos parecido.

    Cada item: {"texto", "arquivo", "pagina", "distancia", "relevante"}.
    "relevante" diz se a distância está dentro do limite configurado.
    """
    k = config.TOP_K if k is None else k
    limite = config.MAX_DISTANCE if max_distancia is None else max_distancia

    total = colecao.count()

    if total == 0:
        return []

    vetor = (embed or gerar_embeddings)([pergunta])

    resultado = colecao.query(
        query_embeddings=vetor,
        n_results=min(k, total),
        include=["documents", "metadatas", "distances"],
    )

    trechos = []

    for texto, meta, distancia in zip(
        resultado["documents"][0], resultado["metadatas"][0], resultado["distances"][0]
    ):
        meta = meta or {}
        trechos.append(
            {
                "texto": texto,
                "arquivo": meta.get("arquivo", "?"),
                "pagina": meta.get("pagina"),
                "distancia": float(distancia),
                "relevante": float(distancia) <= limite,
            }
        )

    return trechos
