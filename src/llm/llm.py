from openai import AsyncOpenAI

from src.config import OPENAI_API_KEY, LLM_MODEL_NAME

class LLM:
    api_key = OPENAI_API_KEY
    model_name = LLM_MODEL_NAME
    client = AsyncOpenAI(api_key=api_key)
    
    @classmethod
    async def execute(cls, input_query: str) -> str:
        response = await cls.client.responses.create(
            model=cls.model_name,
            input=input_query,
            reasoning={"effort": "low"}
        )
        return response.output_text