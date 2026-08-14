import os
from pathlib import Path

import faiss
import joblib
import numpy as np
import pandas as pd
import requests
from scipy.sparse import hstack
from sentence_transformers import SentenceTransformer


# ============================================================
# PROJECT PATHS
# ============================================================
# This file is intended to live at:
# project_root/src/pipeline.py
#
# Using __file__ makes all model/data paths independent of the
# directory from which the script is executed.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "dataset" / "processed"


# ============================================================
# MODEL / DATA PATHS
# ============================================================
CATEGORY_MODEL_PATH = MODELS_DIR / "category_svm.pkl"
CATEGORY_TFIDF_PATH = MODELS_DIR / "category_tfidf.pkl"

PRIORITY_MODEL_PATH = MODELS_DIR / "priority" / "priority_model.pkl"
PRIORITY_TFIDF_PATH = MODELS_DIR / "priority" / "tfidf_vectorizer.pkl"
CATEGORY_ENCODER_PATH = MODELS_DIR / "priority" / "category_encoder.pkl"

QUEUE_MODEL_PATH = MODELS_DIR / "queue" / "queue_model.pkl"
QUEUE_TFIDF_PATH = MODELS_DIR / "queue" / "tfidf_vectorizer.pkl"

FAISS_INDEX_PATH = MODELS_DIR / "embeddings" / "ticket_index.faiss"
TICKET_EMBEDDINGS_PATH = MODELS_DIR / "embeddings" / "ticket_embeddings.npy"

TICKETS_PATH = DATA_DIR / "cleaned_tickets.csv"


# ============================================================
# OLLAMA SETTINGS
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# LOAD MODELS AND DATA
# ============================================================
print("Loading AI ticket analysis components...")

category_model = joblib.load(CATEGORY_MODEL_PATH)
category_tfidf = joblib.load(CATEGORY_TFIDF_PATH)

priority_model = joblib.load(PRIORITY_MODEL_PATH)
priority_tfidf = joblib.load(PRIORITY_TFIDF_PATH)
category_encoder = joblib.load(CATEGORY_ENCODER_PATH)

queue_model = joblib.load(QUEUE_MODEL_PATH)
queue_tfidf = joblib.load(QUEUE_TFIDF_PATH)

index = faiss.read_index(str(FAISS_INDEX_PATH))
ticket_embeddings = np.load(TICKET_EMBEDDINGS_PATH)

retrieval_df = pd.read_csv(TICKETS_PATH)

# Same embedding model used to create the saved FAISS embeddings.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

print("All models and files loaded successfully!")
print(f"FAISS vectors: {index.ntotal}")
print(f"Ticket embeddings shape: {ticket_embeddings.shape}")
print(f"Retrieval dataset shape: {retrieval_df.shape}")


# ============================================================
# HELPERS
# ============================================================
def _encode_priority_metadata(predicted_queue, predicted_type):
    """
    Encode queue + type for the priority model.

    The encoder was fitted with feature names, so use a DataFrame
    when possible. This avoids the sklearn warning:
    'X does not have valid feature names...'
    """
    feature_names = getattr(category_encoder, "feature_names_in_", None)

    if feature_names is not None:
        feature_names = list(feature_names)

        # The training pipeline uses queue and type metadata.
        metadata_values = {
            "queue": predicted_queue,
            "type": predicted_type,
        }

        # Build columns in the exact order used during fitting.
        try:
            metadata_df = pd.DataFrame(
                [[metadata_values[name] for name in feature_names]],
                columns=feature_names,
            )
            return category_encoder.transform(metadata_df)
        except KeyError:
            # Fallback for an encoder with unexpected feature names.
            pass

    # Backward-compatible fallback.
    return category_encoder.transform(
        [[predicted_queue, predicted_type]]
    )


def _build_retrieved_context(retrieved_incidents):
    """Convert retrieved incidents into grounded LLM context."""
    context_parts = []

    for incident in retrieved_incidents:
        context_parts.append(
            f"""
Historical Incident {incident['rank']}:
Type: {incident['type']}
Queue: {incident['queue']}
Priority: {incident['priority']}
Resolution: {incident['answer']}
""".strip()
        )

    return "\n\n".join(context_parts)


def _generate_resolution(ticket, predicted_type, predicted_queue,
                         predicted_priority, retrieved_context):
    """Generate a grounded resolution using local Ollama."""
    prompt = f"""
You are an IT helpdesk assistant.

Ticket:
{ticket}

Predicted Type: {predicted_type}
Predicted Queue: {predicted_queue}
Predicted Priority: {predicted_priority}

Historical Evidence:
{retrieved_context}

Give ONLY:
1. Likely issue
2. 2-3 troubleshooting steps
3. When to escalate

Use the historical evidence.
Do not invent unsupported facts.
If the evidence is insufficient, clearly say so.
Keep the answer under 100 words.
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 100,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
    )
    response.raise_for_status()

    response_json = response.json()

    if "response" not in response_json:
        raise RuntimeError(
            f"Ollama response did not contain 'response': {response_json}"
        )

    return response_json["response"].strip()


def check_ollama():
    """
    Check whether the local Ollama server is reachable.

    Returns True if reachable, otherwise False.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


# ============================================================
# MAIN END-TO-END PIPELINE
# ============================================================
def analyze_ticket(ticket, top_k=5):
    """
    Run one support ticket through the complete AI pipeline.

    Workflow:
        Ticket
        -> Category prediction
        -> Queue prediction
        -> Priority prediction
        -> Sentence Transformer embedding
        -> FAISS similarity search
        -> RAG context
        -> Ollama grounded resolution

    Parameters
    ----------
    ticket : str
        Support ticket text.
    top_k : int, default=5
        Number of similar historical incidents to retrieve.

    Returns
    -------
    dict
        Complete ticket analysis.
    """
    if not isinstance(ticket, str) or not ticket.strip():
        raise ValueError("ticket must be a non-empty string")

    ticket = ticket.strip()

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    # Never ask FAISS for more rows than the available index.
    top_k = min(top_k, index.ntotal)

    # ========================================================
    # 1. CATEGORY / TYPE
    # ========================================================
    category_vector = category_tfidf.transform([ticket])
    predicted_type = category_model.predict(category_vector)[0]

    # ========================================================
    # 2. QUEUE
    # ========================================================
    queue_vector = queue_tfidf.transform([ticket])
    predicted_queue = queue_model.predict(queue_vector)[0]

    # ========================================================
    # 3. PRIORITY
    # ========================================================
    priority_vector = priority_tfidf.transform([ticket])

    priority_metadata = _encode_priority_metadata(
        predicted_queue,
        predicted_type,
    )

    priority_input = hstack([
        priority_vector,
        priority_metadata,
    ]).tocsr()

    predicted_priority = priority_model.predict(
        priority_input
    )[0]

    # ========================================================
    # 4. SEMANTIC EMBEDDING + FAISS RETRIEVAL
    # ========================================================
    ticket_embedding = embedding_model.encode(
        [ticket],
        normalize_embeddings=True,
    ).astype("float32")

    distances, indices = index.search(
        ticket_embedding,
        top_k,
    )

    # ========================================================
    # 5. BUILD RAG CONTEXT
    # ========================================================
    retrieved_incidents = []

    for rank, idx in enumerate(indices[0], start=1):
        idx = int(idx)

        # Protect against invalid FAISS indices.
        if idx < 0 or idx >= len(retrieval_df):
            continue

        row = retrieval_df.iloc[idx]

        retrieved_incidents.append({
            "rank": rank,
            "index": idx,
            "similarity": float(distances[0][rank - 1]),
            "type": row["type"],
            "queue": row["queue"],
            "priority": row["priority"],
            "answer": row["answer"],
        })

    retrieved_context = _build_retrieved_context(
        retrieved_incidents
    )

    # ========================================================
    # 6. OLLAMA / RAG RESOLUTION
    # ========================================================
    resolution = _generate_resolution(
        ticket=ticket,
        predicted_type=predicted_type,
        predicted_queue=predicted_queue,
        predicted_priority=predicted_priority,
        retrieved_context=retrieved_context,
    )

    # ========================================================
    # 7. FINAL RESULT
    # ========================================================
    return {
        "ticket": ticket,
        "category": predicted_type,
        "queue": predicted_queue,
        "priority": predicted_priority,
        "retrieved_incidents": retrieved_incidents,
        "retrieved_context": retrieved_context,
        "resolution": resolution,
    }


# ============================================================
# COMMAND-LINE DEMO
# ============================================================
# This block runs ONLY when:
#     python src/pipeline.py
#
# It does NOT run when another file imports analyze_ticket().
if __name__ == "__main__":
    test_ticket = (
        "My laptop cannot connect to the office Wi-Fi. "
        "I have restarted it but the problem still exists."
    )

    result = analyze_ticket(test_ticket)

    print("\n================================")
    print("       AI TICKET ANALYSIS")
    print("================================")

    print("\nCategory:", result["category"])
    print("Queue:", result["queue"])
    print("Priority:", result["priority"])

    print("\nSimilar Incidents:")

    for incident in result["retrieved_incidents"]:
        print(
            f"#{incident['rank']} "
            f"| Similarity: {incident['similarity']:.3f} "
            f"| Queue: {incident['queue']} "
            f"| Priority: {incident['priority']}"
        )

    print("\nResolution:")
    print(result["resolution"])
