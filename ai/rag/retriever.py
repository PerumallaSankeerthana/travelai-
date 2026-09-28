from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.rag.embeddings import create_embedding
from database.memory_model import TravelMemory


def retrieve_memories(
    db: Session,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[dict]:

    query_embedding = create_embedding(query)

    distance = TravelMemory.embedding.cosine_distance(
        query_embedding
    )

    statement = (
        select(
            TravelMemory,
            distance.label("distance"),
        )
        .where(
            TravelMemory.user_id == user_id
        )
        .order_by(distance)
        .limit(limit)
    )

    results = db.execute(statement).all()

    return [
        {
            "memory": memory.memory,
            "distance": float(distance_value),
        }
        for memory, distance_value in results
    ]