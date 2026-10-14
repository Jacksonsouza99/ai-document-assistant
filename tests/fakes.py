"""Bancos e modelos falsos para os testes (rápidos, sem ChromaDB nem IA)."""


def _dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


class ColecaoFalsa:
    """Imita só o que o nosso código usa do ChromaDB."""

    def __init__(self):
        self.dados = {}
        self.upserts = 0

    def get(self, where=None, include=None):
        ids = [
            i for i, d in self.dados.items()
            if all(d["meta"].get(k) == v for k, v in (where or {}).items())
        ]
        return {"ids": ids, "metadatas": [self.dados[i]["meta"] for i in ids]}

    def upsert(self, ids, documents, embeddings, metadatas):
        self.upserts += 1
        for i, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
            self.dados[i] = {"doc": doc, "emb": emb, "meta": meta}

    def delete(self, ids):
        for i in ids:
            del self.dados[i]

    def count(self):
        return len(self.dados)

    def query(self, query_embeddings, n_results, include=None):
        q = query_embeddings[0]
        itens = sorted(self.dados.values(), key=lambda d: _dist(q, d["emb"]))[:n_results]
        return {
            "documents": [[d["doc"] for d in itens]],
            "metadatas": [[d["meta"] for d in itens]],
            "distances": [[_dist(q, d["emb"]) for d in itens]],
        }


class EmbedFalso:
    """Vetores de mentira; conta quantas vezes foi chamado."""

    def __init__(self):
        self.chamadas = 0

    def __call__(self, textos):
        self.chamadas += 1
        return [[float(len(t)), 0.0] for t in textos]


class EmbedMapa:
    """Devolve um vetor combinado para cada texto (para controlar as distâncias)."""

    def __init__(self, mapa, padrao=(9.0, 9.0)):
        self.mapa, self.padrao, self.chamadas = mapa, list(padrao), 0

    def __call__(self, textos):
        self.chamadas += 1
        return [list(self.mapa.get(t, self.padrao)) for t in textos]


def colecao_com(*itens):
    """itens: (id, texto, vetor, arquivo, pagina)"""
    col = ColecaoFalsa()
    for i, texto, vetor, arquivo, pagina in itens:
        col.dados[i] = {"doc": texto, "emb": list(vetor), "meta": {"arquivo": arquivo, "pagina": pagina}}
    return col
