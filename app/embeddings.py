from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer("all-MiniLM-L6-v2")


textos = [
    "O prazo para devolução do produto é de 7 dias.",
    "O cliente pode devolver a mercadoria em até uma semana.",
    "O escritório funciona de segunda a sexta-feira."
]


embeddings = model.encode(textos)


print("Dimensão dos vetores:")
print(embeddings.shape)

print("\nSimilaridade entre os textos:\n")

for i in range(len(textos)):
    for j in range(i + 1, len(textos)):
        similarity = cosine_similarity(
            [embeddings[i]],
            [embeddings[j]]
        )[0][0]

        print(f"Texto {i + 1} x Texto {j + 1}: {similarity:.4f}")