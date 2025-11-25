from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field



class ChatRequest(BaseModel):
    """Esquema para solicitudes de chat"""
    message: str = Field(..., description="Mensaje del usuario")


class ChatResponse(BaseModel):
    """Esquema para respuestas de chat"""
    response: str = Field(..., description="Respuesta generada por IA")
    model: str = Field(..., description="Modelo utilizado para generar la respuesta")


class HealthResponse(BaseModel):
    """Esquema para respuesta de health check"""
    status: str = Field(..., description="Estado general del servicio")
    services: Dict[str, str] = Field(..., description="Estado de cada servicio individual")


class BaseResponse(BaseModel):
    """Esquema base para respuestas de la API"""
    message: str = Field(..., description="Mensaje de respuesta")
    timestamp: Optional[str] = Field(None, description="Timestamp de la respuesta")