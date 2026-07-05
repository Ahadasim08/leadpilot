from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    embeddings_provider: str = "local"
    agency_name: str = "Acme Digital"

    class Config:
        env_file = ".env"


settings = Settings()
