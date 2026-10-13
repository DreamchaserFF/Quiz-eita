import json
from domain.entities.document_chunk import DocumentChunk


class RagRepository:
    CHUNK_KEY_PATTERN = "id_drive:*:chunk:*"
    INDEX_BATCH_SIZE = 500
    INDEX_READY_PREFIX = "document_type:index:ready:"

    def __init__(self, redis_client):
        self.redis = redis_client.client

    @staticmethod
    def _chunk_key(id_drive: str, chunk: int) -> str:
        return f"id_drive:{id_drive}:chunk:{chunk}"

    @staticmethod
    def _normalize_document_type(document_type: str | None) -> str:
        return (document_type or "").strip().lower()

    @classmethod
    def _document_type_key(cls, document_type: str) -> str:
        return f"document_type:{cls._normalize_document_type(document_type)}"

    @classmethod
    def _index_ready_key(cls, document_type: str) -> str:
        return (
            f"{cls.INDEX_READY_PREFIX}"
            f"{cls._normalize_document_type(document_type)}"
        )

    @staticmethod
    def _document_type_from_json(raw_chunk: str | None) -> str:
        if raw_chunk is None:
            return ""

        chunk = json.loads(raw_chunk)
        return (chunk.get("document_type") or "").strip().lower()

    async def _load_chunks(self, keys: list[str]) -> list[dict]:
        raw_chunks = await self.redis.mget(keys)
        return [
            json.loads(raw_chunk)
            for raw_chunk in raw_chunks
            if raw_chunk is not None
        ]

    async def _initialize_document_type_index(self, document_type: str) -> None:
        """Cria o índice do tema a partir dos chunks gravados antes desta versão."""
        normalized_type = self._normalize_document_type(document_type)
        index_key = self._document_type_key(normalized_type)
        keys_batch = []

        async def add_matching_keys(keys: list[str]) -> None:
            raw_chunks = await self.redis.mget(keys)
            matching_keys = [
                key
                for key, raw_chunk in zip(keys, raw_chunks)
                if self._document_type_from_json(raw_chunk) == normalized_type
            ]

            if matching_keys:
                await self.redis.sadd(index_key, *matching_keys)

        async for key in self.redis.scan_iter(
            match=self.CHUNK_KEY_PATTERN,
            count=self.INDEX_BATCH_SIZE,
        ):
            keys_batch.append(key)

            if len(keys_batch) >= self.INDEX_BATCH_SIZE:
                await add_matching_keys(keys_batch)
                keys_batch = []

        if keys_batch:
            await add_matching_keys(keys_batch)

        await self.redis.set(self._index_ready_key(normalized_type), "1")

    async def create(
        self,
        document_chunk: DocumentChunk
    ):
        key = self._chunk_key(document_chunk.id_drive, document_chunk.chunk)
        document_type = self._normalize_document_type(document_chunk.document_type)
        previous_chunk = await self.redis.get(key)
        previous_type = self._document_type_from_json(previous_chunk)
        payload = json.dumps({
            "name": document_chunk.name,
            "document_type": document_chunk.document_type,
            "date_modification": document_chunk.date_modification,
            "text": document_chunk.text,
            "embedding": document_chunk.embedding,
        })

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(key, payload)
            if previous_type and previous_type != document_type:
                pipe.srem(self._document_type_key(previous_type), key)
            if document_type:
                pipe.sadd(self._document_type_key(document_type), key)
            await pipe.execute()

    async def get(self, id_drive: str, chunk: int):
        result = await self.redis.get(self._chunk_key(id_drive, chunk))

        if result is None:
            return None

        return json.loads(result)
    
    async def search_context(self, tema: str) -> list[dict]:
        document_type = self._normalize_document_type(tema)
        if not document_type:
            return []

        if not await self.redis.exists(self._index_ready_key(document_type)):
            await self._initialize_document_type_index(document_type)

        context = []
        keys_batch = []

        async for key in self.redis.sscan_iter(
            self._document_type_key(document_type),
            count=self.INDEX_BATCH_SIZE,
        ):
            keys_batch.append(key)

            if len(keys_batch) >= self.INDEX_BATCH_SIZE:
                context.extend(await self._load_chunks(keys_batch))
                keys_batch = []

        if keys_batch:
            context.extend(await self._load_chunks(keys_batch))

        return context
        
    
    async def list_documents(self):
        documents = {}

        async for key in self.redis.scan_iter(match="id_drive:*:chunk:*"):
            data = await self.redis.get(key)

            if data is None:
                continue

            document = json.loads(data)

            id_drive = key.split(":")[1]

            documents[id_drive] = {
                "date_modification": document["date_modification"]
            }

        return documents
    

    async def delete(self, id_drive: str, chunk: int):
        key = self._chunk_key(id_drive, chunk)
        raw_chunk = await self.redis.get(key)

        if raw_chunk is None:
            return

        document_type = self._document_type_from_json(raw_chunk)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(key)
            if document_type:
                pipe.srem(self._document_type_key(document_type), key)
            await pipe.execute()

    async def delete_document(self, id_drive: str):
        keys = [
            key
            async for key in self.redis.scan_iter(
                match=f"id_drive:{id_drive}:chunk:*"
            )
        ]

        if not keys:
            return

        raw_chunks = await self.redis.mget(keys)
        keys_by_document_type = {}
        for key, raw_chunk in zip(keys, raw_chunks):
            document_type = self._document_type_from_json(raw_chunk)
            if document_type:
                keys_by_document_type.setdefault(document_type, []).append(key)

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(*keys)
            for document_type, document_keys in keys_by_document_type.items():
                pipe.srem(
                    self._document_type_key(document_type),
                    *document_keys,
                )
            await pipe.execute()
        
        








