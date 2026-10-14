"""O fluxo completo: pergunta -> busca -> resposta com fontes (ou "não encontrei")."""
import re

from app import config
from app.llm import gerar_resposta
from app.search import buscar, similaridade

_CITACAO = re.compile(r"\[(\d+)\]")


def montar_contexto(trechos: list[dict]) -> str:
    """Numera os trechos e diz de onde vieram, para o modelo poder citar [1], [2]..."""
    blocos = []

    for i, trecho in enumerate(trechos, start=1):
        pagina = trecho["pagina"] if trecho["pagina"] is not None else "?"
        blocos.append(f"[{i}] ({trecho['arquivo']}, página {pagina})\n{trecho['texto']}")

    return "\n\n".join(blocos)


def _sem_resposta(candidatos: list[dict]) -> dict:
    melhor = min((c["distancia"] for c in candidatos), default=None)

    return {
        "resposta": config.NOT_FOUND_MESSAGE,
        "encontrou": False,
        "fontes": [],
        "melhor_distancia": melhor,
        "modo": "ia",
    }


def responder(pergunta, colecao, embed=None, gerador=None, k=None, max_distancia=None) -> dict:
    """Responde a pergunta usando só o que está nos documentos.

    Devolve: {"resposta", "encontrou", "fontes", "melhor_distancia"}.
    Se nenhum trecho for parecido o bastante, NEM chama o modelo: devolve
    "não encontrei". Levanta ValueError (pergunta inválida) ou LLMError.
    """
    pergunta = (pergunta or "").strip()

    if not pergunta:
        raise ValueError("Digite uma pergunta.")

    if len(pergunta) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"A pergunta passa de {config.MAX_QUESTION_CHARS} caracteres.")

    candidatos = buscar(pergunta, colecao, embed, k, max_distancia)
    relevantes = [c for c in candidatos if c["relevante"]]

    if not relevantes:
        return _sem_resposta(candidatos)

    texto = gerar_resposta(pergunta, montar_contexto(relevantes), gerador)

    if texto.upper().startswith(config.NO_ANSWER_TOKEN):
        return _sem_resposta(candidatos)

    # Mostra só as fontes que o modelo citou; se não citou nenhuma, mostra todas as usadas
    citados = sorted({int(n) for n in _CITACAO.findall(texto) if 1 <= int(n) <= len(relevantes)})
    usados = citados or list(range(1, len(relevantes) + 1))

    fontes = [
        {
            "numero": n,
            "arquivo": relevantes[n - 1]["arquivo"],
            "pagina": relevantes[n - 1]["pagina"],
            "distancia": relevantes[n - 1]["distancia"],
            "trecho": relevantes[n - 1]["texto"],
            "detalhe": f"similaridade ~{similaridade(relevantes[n - 1]['distancia']):.0%}",
        }
        for n in usados
    ]

    return {
        "resposta": texto,
        "encontrou": True,
        "fontes": fontes,
        "melhor_distancia": min(c["distancia"] for c in candidatos),
        "modo": "ia",
    }
