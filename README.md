# AI Document Assistant

Assistente de perguntas e respostas sobre documentos PDF, desenvolvido com Python e técnicas de Retrieval-Augmented Generation (RAG).

O projeto extrai o texto de documentos, divide o conteúdo em trechos, gera embeddings, armazena os vetores no ChromaDB e recupera os trechos mais relevantes para fornecer contexto ao modelo Gemini.

## Funcionalidades

- Extração de texto de arquivos PDF.
- Divisão do texto em chunks com sobreposição.
- Geração de embeddings com Sentence Transformers.
- Armazenamento vetorial persistente com ChromaDB.
- Busca semântica de trechos relevantes.
- Geração de respostas com o Gemini usando o contexto recuperado.
- Configuração da chave de API por variável de ambiente.

## Tecnologias

- Python
- ChromaDB
- Sentence Transformers
- Google Gen AI SDK
- PyPDF
- python-dotenv
- scikit-learn

## Como funciona

1. O documento PDF é lido e seu texto é extraído.
2. O texto é dividido em chunks.
3. Os chunks são convertidos em embeddings.
4. Os embeddings e textos são armazenados no ChromaDB.
5. A pergunta do usuário é convertida em embedding.
6. O sistema recupera os trechos semanticamente relevantes.
7. O Gemini gera uma resposta com base no contexto recuperado.

## Requisitos

- Python instalado.
- Uma chave de API do Gemini.
- Um documento PDF que possa ser processado pelo projeto.

## Instalação

Clone o repositório e entre na pasta do projeto.

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
GEMINI_API_KEY=sua_chave_aqui
```

Substitua `sua_chave_aqui` pela sua chave real. Nunca publique esse arquivo.

## Adicionar um documento

Coloque um PDF na pasta `documents`.

A pasta do banco vetorial será criada localmente durante a ingestão.

## Executar

A ingestão do documento é feita pelo script `app/vector_store.py`:

```powershell
python -m app.vector_store
```

Depois, faça uma pergunta:

```powershell
python -m app.ask
```

Os comandos acima pressupõem que os módulos estejam organizados para execução a partir da raiz do projeto. Caso a execução atual ainda dependa de imports sem o prefixo `app`, ajuste os imports antes de considerar estas instruções validadas.

## Segurança

Os arquivos `.env`, `.venv`, `chroma_db` e os PDFs locais não devem ser enviados ao GitHub.

## Status

Projeto de estudo em desenvolvimento, criado para praticar Python, busca semântica, bancos vetoriais e integração com modelos de linguagem.
