from sqlalchemy.orm import Session

from ai.rag.embeddings import create_embedding
from database.memory_model import TravelMemory


def store_memory(
    db: Session,
    user_id: int,
    memory: str,
) -> TravelMemory:

    embedding = create_embedding(memory)

    travel_memory = TravelMemory(
        user_id=user_id,
        memory=memory,
        embedding=embedding,
    )

    db.add(travel_memory)
    db.commit()
    db.refresh(travel_memory)

    return travel_memory