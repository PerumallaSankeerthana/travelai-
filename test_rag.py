from backend.core.database import SessionLocal, init_db

from ai.rag.memory import store_memory
from ai.rag.retriever import retrieve_memories


init_db()

db = SessionLocal()

try:
    user_id = 1

    store_memory(
        db,
        user_id,
        "I prefer hotels near beaches.",
    )

    store_memory(
        db,
        user_id,
        "I enjoy local food and authentic restaurants.",
    )

    store_memory(
        db,
        user_id,
        "I prefer budget-friendly accommodation.",
    )

    results = retrieve_memories(
        db,
        user_id,
        "Find me accommodation close to the beach.",
    )

    print("\n--- RAG Results ---")

    for result in results:
        print(result)

finally:
    db.close()