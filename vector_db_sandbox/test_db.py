import chromadb
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "chroma_db")

client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(name="test_docs")

collection.add(
    documents=[
        "Otevírací doba: Pondělí-Pátek 9:00-17:00",
        "Kontakt: info@firma.cz, tel: 123456789",
        "Ceny: Základní 299 Kč, Premium 999 Kč"
    ],
    ids=["doc1", "doc2", "doc3"]
)

results = collection.query(
    query_texts=["Kdy máte otevřeno?"],
    n_results=2
)

print("Nalezené dokumenty:")
for i, doc in enumerate(results['documents'][0]):
    print(f"{i+1}. {doc}")