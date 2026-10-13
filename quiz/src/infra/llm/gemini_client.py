import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from infra.llm.key_manager import KeyManager


logger = logging.getLogger(__name__)


class GeminiClient:
    
    def __init__(self):
        self.key_manager = KeyManager()
        self.base_model = "gemini-3.5-flash-lite"

    async def invoke(self, prompt, structured_output=None):
        """Invoca o Gemini usando uma locação exclusiva de API key.

        A aquisição não bloqueia: quando todas as chaves estão ocupadas ou
        em cooldown, a operação falha imediatamente. Em caso de 429, a
        locação é liberada e a próxima chave disponível é tentada.
        """
        max_attempts = len(self.key_manager.keys)
        if not max_attempts:
            raise ValueError("Nenhuma API Key foi configurada")

        received_rate_limit = False
        for _ in range(max_attempts):
            lease = await self.key_manager.try_acquire()
            if lease is None:
                if received_rate_limit:
                    raise Exception("Todas as API Keys foram utilizadas")
                raise RuntimeError("Nenhuma API Key está disponível neste momento")

            try:
                llm = self.create_llm(lease.value, self.base_model)
                if structured_output:
                    llm = llm.with_structured_output(structured_output)

                return await llm.ainvoke(prompt)

            except Exception as error:
                status_code = getattr(error, "status_code", None)
                if status_code is None:
                    status_code = getattr(error, "code", None)
                if status_code is None:
                    cause = getattr(error, "__cause__", None)
                    status_code = getattr(cause, "code", None)

                if status_code == 429:
                    received_rate_limit = True
                    logger.warning("Gemini recusou a chave por limite de uso (429)")
                    continue
                raise
            finally:
                await lease.release()

        raise Exception("Todas as API Keys foram utilizadas")


    @staticmethod
    def create_llm(api_key: str , base_model: str):
        return ChatGoogleGenerativeAI(
            model=base_model,
            google_api_key=api_key,
        )

