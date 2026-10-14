"""Responder SEM IA: acha os trechos que contêm as palavras da pergunta e mostra a fonte."""
from app import config
from app.keyword_store import buscar_trechos
from app.keywords import destacar, melhor_frase, montar_consulta, recorte, termos_achados, termos_da_pergunta


def responder_sem_ia(pergunta, banco, k=None, min_cobertura=None) -> dict:
    """Mesmo formato do rag.responder: {"resposta", "encontrou", "fontes", ...}.

    A "resposta" é a frase do documento que mais combina com a pergunta (citada
    como está no texto, não reescrita). Se nenhum trecho contiver pelo menos
    `min_cobertura` dos termos da pergunta, diz que não encontrou.
    Levanta ValueError se a pergunta for vazia, grande demais ou só tiver palavras comuns.
    """
    k = config.KEYWORD_TOP_K if k is None else k
    minimo = config.MIN_COVERAGE if min_cobertura is None else min_cobertura
    pergunta = (pergunta or "").strip()

    if not pergunta:
        raise ValueError("Digite uma pergunta.")

    if len(pergunta) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"A pergunta passa de {config.MAX_QUESTION_CHARS} caracteres.")

    termos = termos_da_pergunta(pergunta)

    if not termos:
        raise ValueError("Use palavras mais específicas na pergunta (por exemplo: prazo de devolução).")

    candidatos = []

    for t in buscar_trechos(banco, montar_consulta(termos), k):
        achados = termos_achados(t["texto"], termos)
        candidatos.append({**t, "achados": achados, "cobertura": len(achados) / len(termos)})

    # Quem contém mais termos vem primeiro; empate: melhor nota BM25 (menor = melhor)
    relevantes = sorted((c for c in candidatos if c["cobertura"] >= minimo), key=lambda c: (-c["cobertura"], c["nota"]))

    if not relevantes:
        return {
            "resposta": config.NOT_FOUND_MESSAGE,
            "encontrou": False,
            "fontes": [],
            "melhor_distancia": None,
            "modo": "sem_ia",
        }

    melhor = relevantes[0]
    resposta = (
        f"Trecho mais relevante ({melhor['arquivo']}, página {melhor['pagina']}):\n\n"
        f"> {destacar(melhor_frase(melhor['texto'], termos), termos)}"
    )

    if len(relevantes) > 1:
        resposta += f"\n\nHá mais {len(relevantes) - 1} trecho(s) relacionado(s) nas fontes abaixo."

    fontes = [
        {
            "numero": i,
            "arquivo": c["arquivo"],
            "pagina": c["pagina"],
            "distancia": None,
            "detalhe": f"termos encontrados: {len(c['achados'])} de {len(termos)} ({', '.join(c['achados'])})",
            "trecho": destacar(recorte(c["texto"], termos, 700), termos),
        }
        for i, c in enumerate(relevantes, start=1)
    ]

    return {"resposta": resposta, "encontrou": True, "fontes": fontes, "melhor_distancia": None, "modo": "sem_ia"}
