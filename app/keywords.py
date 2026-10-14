"""Texto sem IA: transforma a pergunta em palavras-chave e destaca o que foi achado.

Tudo aqui é Python puro. A busca ignora acentos e maiúsculas, tira palavras
comuns ("de", "qual", "o"...) e casa palavras da mesma família pelo começo
(radical): "devolução", "devolver" e "devolvido" casam entre si.
"""
import re
import unicodedata

# Palavras muito comuns, escritas sem acento (a comparação é feita sem acento)
STOPWORDS = set(
    """a o as os um uma uns umas de do da dos das dum duma em no na nos nas num numa por pelo
    pela pelos pelas para pra com sem sob sobre entre ate ao aos e ou mas que qual quais quem
    como quando onde porque se ja nao sim eu tu ele ela eles elas me te lhe meu minha seu sua
    nosso nossa este esta isso isto esse essa aquele aquela ser sao era foi tem tinha ha ter
    fazer pode podem posso deve devo existe existem quanto quantos quantas quanta favor diga
    explique fale""".split()
)


def _base(texto: str) -> str:
    """Minúsculas e sem acento, mantendo EXATAMENTE o mesmo tamanho (letra por letra)."""
    return "".join((unicodedata.normalize("NFD", c)[0].lower() or c)[:1] for c in texto)


def termos_da_pergunta(pergunta: str) -> list[str]:
    """Palavras importantes da pergunta, sem repetição e na ordem em que aparecem."""
    termos = []

    for palavra in re.findall(r"[a-z0-9]+", _base(pergunta)):
        if palavra in STOPWORDS or (len(palavra) < 2 and not palavra.isdigit()):
            continue

        if palavra not in termos:
            termos.append(palavra)

    return termos


def radical(termo: str) -> str:
    """Começo da palavra usado para casar a mesma família (devolu-ção, devol-ver)."""
    if len(termo) > 5:
        return termo[:5]

    if len(termo) == 5:
        return termo[:4]

    return termo


def _casa(palavra: str, termo: str) -> bool:
    return palavra.startswith(radical(termo)) if len(termo) >= 5 else palavra == termo


def montar_consulta(termos: list[str]) -> str:
    """Consulta para o SQLite FTS5: qualquer termo serve, mas quem tem mais termos ganha nota maior."""
    partes = [f'"{radical(t)}"*' if len(t) >= 5 else f'"{t}"' for t in termos]

    return " OR ".join(partes)


def termos_achados(texto: str, termos: list[str]) -> list[str]:
    """Quais termos da pergunta aparecem no texto."""
    palavras = re.findall(r"[a-z0-9]+", _base(texto))

    return [t for t in termos if any(_casa(p, t) for p in palavras)]


def melhor_frase(texto: str, termos: list[str], limite: int = 500) -> str:
    """A frase do trecho que contém mais termos da pergunta."""
    frases = [f for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f]

    if not frases:
        return texto.strip()

    melhor = max(frases, key=lambda f: len(termos_achados(f, termos)))  # empate: a primeira

    return recorte(melhor, termos, limite)


def recorte(texto: str, termos: list[str], tamanho: int = 500) -> str:
    """Se o texto for longo, mostra só a janela em volta da primeira palavra encontrada."""
    if len(texto) <= tamanho:
        return texto

    base = _base(texto)
    inicio_match = next(
        (m.start() for m in re.finditer(r"[a-z0-9]+", base) if any(_casa(m.group(), t) for t in termos)),
        0,
    )

    inicio = max(0, inicio_match - tamanho // 4)
    espaco = texto.rfind(" ", max(0, inicio - 40), inicio)  # começa em palavra inteira
    inicio = espaco + 1 if espaco != -1 else inicio
    fim = inicio + tamanho

    return ("..." if inicio > 0 else "") + texto[inicio:fim].strip() + ("..." if fim < len(texto) else "")


def destacar(texto: str, termos: list[str]) -> str:
    """Coloca **negrito** (markdown) nas palavras encontradas."""
    texto = texto.replace("*", "")
    base = _base(texto)
    saida, ultimo = [], 0

    for m in re.finditer(r"[a-z0-9]+", base):
        if any(_casa(m.group(), t) for t in termos):
            saida.append(texto[ultimo:m.start()])
            saida.append(f"**{texto[m.start():m.end()]}**")
            ultimo = m.end()

    saida.append(texto[ultimo:])

    return "".join(saida)
