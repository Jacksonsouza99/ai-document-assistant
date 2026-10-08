import chromadb


client = chromadb.PersistentClient(path="chroma_db")

print("Coleções antes da limpeza:")

for collection in client.list_collections():
    print("-", collection.name)


try:
    client.delete_collection(name="documents")
    print("\nColeção 'documents' removida.")
except Exception:
    print("\nA coleção 'documents' não existia.")


print("\nLimpeza concluída.")