# STANDALONE: pull circuit list 
import os
import chromadb

BASE = os.path.expanduser('~/easyf1')

# Connect to the knowledge base (script does its own setup)
chroma_client = chromadb.PersistentClient(path=os.path.join(BASE, 'chromadb'))
collection = chroma_client.get_collection("easyf1_all_seasons")

# Pull unique circuits
all_data = collection.get(include=['metadatas'])
circuits = set()
for meta in all_data['metadatas']:
    if 'circuit' in meta and meta['circuit']:
        circuits.add(meta['circuit'])

circuits = sorted(circuits)
print(f"Found {len(circuits)} unique circuits:\n")
for c in circuits:
    print(f"  {c}")