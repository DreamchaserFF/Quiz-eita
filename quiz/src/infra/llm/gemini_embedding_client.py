import asyncio

from infra.llm.key_manager import KeyManager
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class GeminiEmbeddingClient:
    
    def __init__(self, base_model: str = "gemini-embedding-2"):
        self.key_manager = KeyManager()
        self.base_model = base_model

    async def create_embedding(self, chunk_list: list[str]) -> list[list[float]]:
        if not chunk_list:
            return []

        if not self.key_manager.keys:
            raise ValueError("Nenhuma API Key foi configurada")

        chunks = iter(enumerate(chunk_list))
        results = [[] for _ in chunk_list]

        async def worker(worker_index: int) -> None:
            for chunk_index, chunk in chunks:
                for attempt in range(len(self.key_manager.keys)):
                    lease = await self.key_manager.try_acquire()
                    if lease is None:
                        raise RuntimeError(
                            "Nenhuma API Key está disponível neste momento"
                        )

                    try:
                        llm = self.create_llm(lease.value, self.base_model)
                        results[chunk_index] = await self.make_embedding(llm, chunk)
                        print(f"Worker {worker_index + 1}: chunk {chunk_index} finalizado")
                        break

                    except Exception as error:
                        print(f"Chave falhou: {error}")
                        status_code = getattr(error, "status_code", None)
                        if status_code is None:
                            status_code = getattr(error.__cause__ or error, "code", None)
                        if status_code != 429:
                            raise

                        if attempt == len(self.key_manager.keys) - 1:
                            raise Exception("Todas as API Keys foram utilizadas") from error
                    finally:
                        await lease.release()

        workers = [
            asyncio.create_task(worker(worker_index))
            for worker_index in range(min(10, len(chunk_list)))
        ]
        try:
            await asyncio.gather(*workers)
        finally:
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        return results
    
    
    async def make_embedding(self, llm: GoogleGenerativeAIEmbeddings, chunk: str) -> list[float]:
        try:
            return await llm.aembed_query(chunk)
        except Exception as error:
            print(f"Erro ao gerar embedding: {error}")
            raise

    @staticmethod
    def create_llm(api_key: str , base_model: str) -> GoogleGenerativeAIEmbeddings:
        return GoogleGenerativeAIEmbeddings(
            model=base_model,
            google_api_key=api_key,
        )

