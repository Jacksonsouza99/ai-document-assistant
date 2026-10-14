"""Perguntas pelo terminal (por padrão SEM IA).

    python -m app.ask "Qual é o prazo de devolução?"          busca por palavras-chave, offline
    python -m app.ask "Qual é o prazo?" --ia                  usa o Gemini (precisa de chave e dos pacotes da IA)
    python -m app.ask "Qual é o prazo?" --trechos             mostra também o texto das fontes
"""
import sys

from app import config


def main(argumentos: list[str]) -> int:
    usar_ia = "--ia" in argumentos
    mostrar_trechos = "--trechos" in argumentos
    pergunta = " ".join(a for a in argumentos if a not in ("--ia", "--trechos")).strip()

    if not pergunta:
        pergunta = input("Faça uma pergunta sobre os documentos: ").strip()

    try:
        if usar_ia:
            from app.llm import LLMError
            from app.rag import responder
            from app.vector_store import abrir_colecao

            resultado = responder(pergunta, abrir_colecao())
        else:
            from app.keyword_store import abrir_banco
            from app.offline import responder_sem_ia

            LLMError = ValueError
            resultado = responder_sem_ia(pergunta, abrir_banco())
    except (ValueError, LLMError) as erro:
        print(erro)
        return 1
    except ImportError:
        print("Para usar a IA, instale os pacotes dela: python -m pip install -r requirements-ia.txt")
        return 1

    print("\n" + resultado["resposta"])

    if resultado["fontes"]:
        print("\nFontes:")

    for fonte in resultado["fontes"]:
        print(f"  [{fonte['numero']}] {fonte['arquivo']}, página {fonte['pagina']} ({fonte['detalhe']})")

        if mostrar_trechos:
            print(f"      {fonte['trecho']}")

    if usar_ia and not resultado["encontrou"] and resultado["melhor_distancia"] is not None:
        print(f"\n(melhor distância: {resultado['melhor_distancia']:.2f}; limite: {config.MAX_DISTANCE})")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
