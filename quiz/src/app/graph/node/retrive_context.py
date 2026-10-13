
import logging
import time

from typing import Any

from app.graph.state import QuizState
from infra.repository.rag_repository import RagRepository
from infra.repository.redis_client import RedisClient


logger = logging.getLogger(__name__)


async def search_context_in_redis(rag_repository: RagRepository, state: QuizState) -> list[str]:
    """Busca no Redis os trechos mais relevantes para o tema atual do quiz."""
    try:
        tema = state.get("tema", "").strip().lower()
        context = await rag_repository.search_context(tema)
        return context
        
    except Exception:
        logger.exception("Falha ao buscar contexto no Redis")
        raise


async def retrive_context(state: QuizState) -> dict[str, Any]:
    """Busca no Redis o contexto para o próximo nó do grafo."""
    started_at = time.perf_counter()
    try:
        redis_client = RedisClient("REDIS_URL_RAG")
        rag_repository = RagRepository(redis_client)
        context = await search_context_in_redis(rag_repository, state)

        return {"context": context}
    except Exception:
        logger.exception("Falha no node retrieve_context")
        raise
    finally:
        logger.info(
            "Node retrieve_context finalizado em %.3f segundos",
            time.perf_counter() - started_at,
        )
