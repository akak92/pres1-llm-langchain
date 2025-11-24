import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    
    # Azure OpenAI
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_KEY", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    azure_openai_version: str = os.getenv("AZURE_OPENAI_VERSION", "2025-01-01-preview")
    
    # MongoDB
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27025/store")
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # LLM Settings
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()