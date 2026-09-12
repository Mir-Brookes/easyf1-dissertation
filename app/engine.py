
#Core logic of EasyF1
import os
import json
import requests
import chromadb
from dotenv import load_dotenv
from fastembed import TextEmbedding
from google import genai

# ---- Paths & keys ----
BASE = os.path.expanduser('~/easyf1')
load_dotenv(dotenv_path=os.path.join(BASE, '.env'))
GEMINI_KEY     = os.getenv("GEMINI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

# ---- Lazy-loaded singletons (built once, reused) ----
_embedding_model = None
_collection = None
_gemini_client = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir=os.path.join(BASE, "model_cache")
        )
    return _embedding_model

def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=os.path.join(BASE, 'chromadb'))
        _collection = client.get_collection("easyf1_all_seasons")
    return _collection

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_KEY)
    return _gemini_client


# ---- Core functions ----
def embed_text(text):
    model = get_embedding_model()
    return list(model.embed([text]))[0].tolist()


def list_circuits():
    """Pull the unique circuit list from the knowledge base."""
    coll = get_collection()
    all_data = coll.get(include=['metadatas'])
    circuits = set()
    for meta in all_data['metadatas']:
        if meta.get('circuit'):
            circuits.add(meta['circuit'])
    return sorted(circuits)


def retrieve_context(scenario, circuit=None, n=6, pool=20):
    """
    Venue-weighted retrieval: pull a semantic candidate pool,
    then gently boost chunks from the selected circuit.
    """
    q_emb = embed_text(scenario)
    coll = get_collection()

    # Pull a larger candidate pool ranked by pure semantic relevance
    results = coll.query(
        query_embeddings=[q_emb],
        n_results=pool,
        include=['documents', 'metadatas']
    )
    docs  = results['documents'][0]
    metas = results['metadatas'][0]

    # Soft boost: bring selected-circuit chunks to the front,
    # keep the rest in relevance order behind them
    if circuit:
        same = [(d, m) for d, m in zip(docs, metas) if m.get('circuit') == circuit]
        other = [(d, m) for d, m in zip(docs, metas) if m.get('circuit') != circuit]
        ordered = same + other
    else:
        ordered = list(zip(docs, metas))

    top = ordered[:n]
    return [d for d, m in top]


def build_prompt(scenario, context_chunks):
    """Build the identical prompt used by both models."""
    context_text = "\n".join(f"- {c}" for c in context_chunks)
    return f"""You are an expert F1 race strategist. Using ONLY the historical context provided, give a strategy recommendation.

HISTORICAL CONTEXT FROM PAST RACES:
{context_text}

SCENARIO:
{scenario}

Provide your recommendation in this exact format:
VERDICT: (one clear recommendation in a sentence)
CONFIDENCE: (High / Medium / Low)
REASONING: (2-3 sentences grounded in the historical context above)
RISK: (the main risk of this recommendation)"""


def ask_gemini(prompt, retries=3):
    """Send prompt to Gemini, retrying on transient 503/overload errors."""
    import time
    from google.genai import errors
    client = get_gemini_client()
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return response.text
        except errors.ServerError as e:
            # 503 / overload — transient, wait and retry
            if attempt < retries:
                time.sleep(5)
                continue
            return f"[Gemini unavailable after {retries} retries — Google servers busy. Try again in a moment.]"
        except Exception as e:
            return f"[Gemini error: {str(e)[:120]}]"


def ask_nemotron(prompt, retries=2):
    import time
    for attempt in range(retries + 1):
        resp = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}",
                     "Content-Type": "application/json"},
            data=json.dumps({"model": OPENROUTER_MODEL,
                             "messages": [{"role": "user", "content": prompt}]})
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('choices'):
                return data['choices'][0]['message']['content']
            if attempt < retries:
                time.sleep(5); continue
            return "[No response from Nemotron after retries]"
        elif resp.status_code == 429 and attempt < retries:
            time.sleep(15); continue
        else:
            return f"[Error {resp.status_code}]"
    return "[Failed after retries]"


def compare(scenario, circuit=None):
    """Run one scenario through both models with identical context."""
    chunks = retrieve_context(scenario, circuit=circuit)
    prompt = build_prompt(scenario, chunks)
    return {
        'scenario': scenario,
        'context': chunks,
        'gemini': ask_gemini(prompt),
        'nemotron': ask_nemotron(prompt),
    }

def parse_recommendation(text):
    """
    Split a model's response into VERDICT / CONFIDENCE / REASONING / RISK.
    Returns a dict; any field not found is left blank.
    """
    fields = {'VERDICT': '', 'CONFIDENCE': '', 'REASONING': '', 'RISK': ''}
    labels = list(fields.keys())

    # Find where each label starts in the text
    positions = []
    upper = text.upper()
    for label in labels:
        idx = upper.find(label)
        if idx != -1:
            positions.append((idx, label))
    positions.sort()

    # Slice the text between consecutive labels
    for i, (start, label) in enumerate(positions):
        # content starts after "LABEL:" 
        content_start = text.find(':', start)
        content_start = content_start + 1 if content_start != -1 else start + len(label)
        # content ends where the next label begins
        content_end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        fields[label] = text[content_start:content_end].strip()

    return fields