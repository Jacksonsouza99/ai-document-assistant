import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém a chave da API
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY não encontrada no arquivo .env."
    )

# Cria o cliente do Gemini
client = genai.Client(
    api_key=api_key
)


def gerar_resposta(pergunta: str, contexto: str):
    prompt = f"""
Você é um assistente que responde perguntas com base no conteúdo
fornecido pelo usuário.

Use o contexto abaixo para responder à pergunta.

Se a resposta não estiver no contexto, diga claramente que
a informação não foi encontrada no documento.

CONTEXTO:
{contexto}

PERGUNTA:
{pergunta}
"""

    try:
        resposta = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return resposta.text

    except errors.ServerError as erro:
        print("\nO serviço do Gemini está temporariamente indisponível.")
        print("Tente novamente em alguns instantes.")
        print(f"Detalhes técnicos: {erro}")

        return "Não foi possível gerar a resposta porque o serviço de IA está temporariamente indisponível."

    except Exception as erro:
        print("\nOcorreu um erro ao gerar a resposta.")
        print(f"Detalhes técnicos: {erro}")

        return "Não foi possível gerar a resposta devido a um erro inesperado."


if __name__ == "__main__":
    pergunta = "O que é RAG?"

    contexto = """
RAG é uma técnica que permite que um modelo de inteligência artificial
consulte informações externas antes de gerar uma resposta.
"""

    resposta = gerar_resposta(pergunta, contexto)

    print("\nRESPOSTA DO GEMINI:")
    print(resposta)
