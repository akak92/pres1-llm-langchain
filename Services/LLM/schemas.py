from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProductQuery(BaseModel):
    """Esquema para consultas de productos"""
    query: str = Field(..., description="Consulta del usuario para buscar productos")
    max_products: int = Field(default=5, ge=1, le=20, description="Número máximo de productos a retornar")


class ChatRequest(BaseModel):
    """Esquema para solicitudes de chat"""
    message: str = Field(..., description="Mensaje del usuario")
    context: str = Field(default="", description="Contexto adicional para la conversación")


class ProductRecommendation(BaseModel):
    """Esquema para respuestas de recomendaciones de productos"""
    products: List[Dict[str, Any]] = Field(..., description="Lista de productos recomendados")
    recommendation: str = Field(..., description="Texto de recomendación generado por IA")


class Product(BaseModel):
    """Esquema para un producto"""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Nombre del producto")
    unit_price: float = Field(..., ge=0, description="Precio unitario del producto")
    stock: int = Field(..., ge=0, description="Cantidad en stock")
    
    class Config:
        allow_population_by_field_name = True


class ProductsResponse(BaseModel):
    """Esquema para respuestas de listado de productos"""
    products: List[Product]
    count: int = Field(..., description="Número total de productos retornados")


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