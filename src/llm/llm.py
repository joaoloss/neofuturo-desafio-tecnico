from openai import AsyncOpenAI

from src.config.settings import Settings

class LLM:
    api_key = Settings.openai_api_key
    model_name = Settings.llm_model_name
    client = AsyncOpenAI(api_key=api_key)
    
    @classmethod
    async def execute(cls, input_query: str) -> str:
        response = await cls.client.responses.create(
            model=cls.model_name,
            input=input_query,
            reasoning={"effort": "low"}
        )
        return response.output_text